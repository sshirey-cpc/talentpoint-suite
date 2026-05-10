"""
ObservationPoint — Tenant Loader

Loads per-tenant configuration from config/tenants/<TENANT_ID>/.
The active tenant is selected at process startup via the TENANT_ID env var.
All loads are cached after the first call (config is immutable per process).

Usage:
    from tenant_loader import (
        get_tenant_id, get_tenant_config, get_allowed_domains,
        get_titles_config, get_rubric, get_commitments, get_vision,
        get_action_steps_guide, classify_tier,
    )

    tenant = get_tenant_config()
    if email_domain not in get_allowed_domains():
        return reject()
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

import yaml


CONFIG_ROOT = Path(__file__).parent / 'config'
TENANTS_ROOT = CONFIG_ROOT / 'tenants'


def get_tenant_id() -> str:
    """Active tenant slug. Defaults to 'firstline-schools' for backward compat."""
    return os.environ.get('TENANT_ID', 'firstline-schools')


def _tenant_dir() -> Path:
    tid = get_tenant_id()
    path = TENANTS_ROOT / tid
    if not path.is_dir():
        raise FileNotFoundError(
            f"Tenant '{tid}' not found at {path}. "
            f"Set TENANT_ID env var or create config/tenants/{tid}/."
        )
    return path


@lru_cache(maxsize=1)
def get_tenant_config() -> dict[str, Any]:
    """tenant.yaml — metadata, branding, school years, rubric filenames."""
    with open(_tenant_dir() / 'tenant.yaml') as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def get_titles_config() -> dict[str, Any]:
    """titles.yaml — title-to-tier mapping for this tenant."""
    with open(_tenant_dir() / 'titles.yaml') as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def get_permissions_schema() -> dict[str, Any]:
    """Shared permissions schema (tier-neutral, capability matrix)."""
    with open(CONFIG_ROOT / 'permissions.schema.yaml') as f:
        return yaml.safe_load(f)


def get_allowed_domains() -> list[str]:
    """Email domains allowed to sign in for this tenant."""
    return list(get_tenant_config().get('allowed_domains', []))


def get_school_year() -> str:
    return get_tenant_config().get('current_school_year', '2025-2026')


def get_school_years() -> list[str]:
    return list(get_tenant_config().get('school_years', []))


def get_brand() -> dict[str, Any]:
    return dict(get_tenant_config().get('brand', {}))


def _load_optional_json(filename: Optional[str]) -> Optional[dict]:
    if not filename:
        return None
    path = _tenant_dir() / filename
    if not path.is_file():
        return None
    with open(path) as f:
        return json.load(f)


@lru_cache(maxsize=1)
def get_commitments() -> Optional[dict]:
    return _load_optional_json(get_tenant_config().get('commitments_file'))


@lru_cache(maxsize=1)
def get_vision() -> Optional[dict]:
    return _load_optional_json(get_tenant_config().get('vision_file'))


@lru_cache(maxsize=1)
def get_action_steps_guide() -> Optional[dict]:
    return _load_optional_json(get_tenant_config().get('action_steps_file'))


def get_rubric(rubric_key: str) -> Optional[dict]:
    """Load a rubric by key (e.g., 'teacher', 'leader', 'prek').

    Looks up the filename in tenant.yaml's default_rubrics, then loads from
    config/tenants/<slug>/rubrics/. Returns None if not configured.
    """
    rubrics = get_tenant_config().get('default_rubrics', {})
    filename = rubrics.get(rubric_key)
    if not filename:
        return None
    path = _tenant_dir() / 'rubrics' / filename
    if not path.is_file():
        return None
    with open(path) as f:
        return json.load(f)


def get_rubric_by_id(rubric_id: str) -> Optional[dict]:
    """Load any rubric by its internal id, scanning the tenant's rubrics dir.

    Used by the legacy /api/forms/<form_id> endpoint while we transition
    callers to use rubric keys.
    """
    rubrics_dir = _tenant_dir() / 'rubrics'
    if not rubrics_dir.is_dir():
        return None
    for path in rubrics_dir.glob('*.json'):
        with open(path) as f:
            data = json.load(f)
        if data.get('id') == rubric_id:
            return data
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Tier classification
# ─────────────────────────────────────────────────────────────────────────────

def classify_tier(job_title: str, has_direct_reports: bool, is_active: bool = True) -> str:
    """Classify a user into a permission tier based on their title.

    Walks tenant titles.yaml top-down (admin → content_lead → school_leader),
    falls through to supervisor (rule-based) and self_only.

    Returns: 'admin' | 'content_lead' | 'school_leader' | 'supervisor' | 'self_only'
    """
    if not is_active:
        return 'self_only'

    title = (job_title or '').strip()
    title_lower = title.lower()

    titles_cfg = get_titles_config().get('tiers', [])

    for tier_cfg in titles_cfg:
        tier_id = tier_cfg.get('id')
        if tier_id not in ('admin', 'content_lead', 'school_leader'):
            continue

        # Exact match (case-sensitive)
        for exact in tier_cfg.get('titles_exact', []) or []:
            if title == exact:
                return tier_id

        # Keyword match (case-insensitive substring)
        for kw in tier_cfg.get('titles_keyword', []) or []:
            if kw.lower() in title_lower:
                return tier_id

    if has_direct_reports:
        return 'supervisor'

    return 'self_only'


def is_admin_title(job_title: str) -> bool:
    """Backward-compat helper for code that wants a quick admin check."""
    return classify_tier(job_title, has_direct_reports=False, is_active=True) == 'admin'
