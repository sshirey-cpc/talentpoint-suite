"""
ObservationPoint — Process-level Configuration

Holds environment-driven values that DON'T vary per tenant: secrets, DB
connection, OAuth client credentials. Tenant-specific values (allowed
email domains, school year, branding, titles) live in
config/tenants/<TENANT_ID>/ and are loaded by tenant_loader.py.
"""
import os
import secrets

from tenant_loader import (
    get_tenant_id,
    get_allowed_domains,
    get_school_year,
    get_school_years,
    classify_tier,
    is_admin_title,
)

# ── Flask ──────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# ── Tenant ─────────────────────────────────────────────────────────────
TENANT_ID = get_tenant_id()

# ── OAuth ──────────────────────────────────────────────────────────────
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')

# Domains that may sign in. Driven by tenant config; first domain is treated
# as the canonical one (used in dev-mode email defaults, etc.).
ALLOWED_DOMAINS = get_allowed_domains()
ALLOWED_DOMAIN = ALLOWED_DOMAINS[0] if ALLOWED_DOMAINS else ''  # backward-compat

# ── Dev mode ───────────────────────────────────────────────────────────
DEV_MODE = os.environ.get('DEV_MODE', 'false').lower() == 'true'
DEV_USER_EMAIL = os.environ.get(
    'DEV_USER_EMAIL',
    f'dev@{ALLOWED_DOMAIN}' if ALLOWED_DOMAIN else 'dev@example.org',
)

# ── Database ───────────────────────────────────────────────────────────
DB_HOST = os.environ.get('DB_HOST', '')
DB_NAME = os.environ.get('DB_NAME') or f'observationpoint_{TENANT_ID.replace("-", "_")}'
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASS', '')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_SOCKET = os.environ.get('DB_SOCKET', '')

# ── GCP ────────────────────────────────────────────────────────────────
PROJECT_ID = os.environ.get('GCP_PROJECT', '')

# ── School year (driven by tenant.yaml) ────────────────────────────────
CURRENT_SCHOOL_YEAR = get_school_year()
SCHOOL_YEARS = get_school_years()

# ── Build version for cache busting ────────────────────────────────────
BUILD_VERSION = os.environ.get('BUILD_VERSION', '1')

# ── Backward-compatibility shims ───────────────────────────────────────
# auth.py imports CPO_TITLE / C_TEAM_KEYWORDS / HR_TEAM_TITLES. These are
# being phased out in favor of tenant_loader.classify_tier(). Re-exported
# here as empty / unused so existing imports don't break during the
# transition. Code that calls is_cteam() / is_admin_title() should migrate
# to tenant_loader.classify_tier() / is_admin_title() instead.
CPO_TITLE = ''  # deprecated; classify_tier handles tier assignment
C_TEAM_KEYWORDS = []  # deprecated; see tenant titles.yaml
HR_TEAM_TITLES = []  # deprecated; see tenant titles.yaml
