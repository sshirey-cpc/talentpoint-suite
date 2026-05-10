"""
ObservationPoint — Authentication & Authorization
Google OAuth + email-based org hierarchy.

Tier classification is delegated to tenant_loader.classify_tier() which
reads config/tenants/<TENANT_ID>/titles.yaml. The legacy is_cteam /
is_admin_title / is_content_lead / is_school_leader helpers are now thin
wrappers that delegate to tenant_loader.
"""
import os
import logging
import functools
import psycopg2
from flask import session, redirect, request, jsonify

from config import (
    DEV_MODE, ALLOWED_DOMAINS,
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
)
from tenant_loader import (
    classify_tier as _classify_tier,
    get_titles_config,
)

log = logging.getLogger(__name__)

# OAuth setup
from authlib.integrations.flask_client import OAuth
oauth = OAuth()


def init_oauth(app):
    oauth.init_app(app)
    oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )


def is_allowed_email(email: str) -> bool:
    """Check if an email's domain is in the tenant's allowed_domains list."""
    if not email or '@' not in email:
        return False
    domain = email.split('@', 1)[1].lower()
    return domain in [d.lower() for d in ALLOWED_DOMAINS]


def get_current_user():
    """
    The EFFECTIVE current user. If an admin is impersonating another staff
    member, this returns that impersonated user (with is_admin forced False
    so they don't accidentally wield admin powers). Otherwise returns the
    real signed-in user.
    """
    real_user = session.get('user')
    if not real_user:
        return None
    imp = session.get('impersonating_as')
    if imp and real_user.get('is_admin'):
        return {
            'email': imp['email'],
            'name': imp.get('name', ''),
            'job_title': imp.get('job_title', ''),
            'school': imp.get('school', ''),
            'job_function': imp.get('job_function', ''),
            'is_admin': False,           # impersonated users never have admin powers
            'accessible_emails': imp.get('accessible_emails', []),
            '_impersonating': True,
            '_real_user_email': real_user.get('email'),
        }
    return real_user


def get_real_user():
    """The real signed-in user, regardless of impersonation. Use for audit."""
    return session.get('user')


def is_impersonating():
    return bool(session.get('impersonating_as'))


def require_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if DEV_MODE:
            return f(*args, **kwargs)
        user = get_current_user()
        if not user:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Not authenticated'}), 401
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    """Only the real signed-in user's is_admin flag counts — impersonated
    users are never admins."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        real = get_real_user()
        if not real or not real.get('is_admin'):
            return jsonify({'error': 'Admin required'}), 403
        return f(*args, **kwargs)
    return decorated


def require_no_impersonation(f):
    """Block the endpoint while impersonating. Use on write endpoints —
    admins in view-as mode shouldn't be able to create/modify data as the
    impersonated user."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if is_impersonating():
            return jsonify({
                'error': 'Cannot modify data while viewing as another user. Exit view-as mode first.',
                'code': 'impersonating',
            }), 403
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────────────────────────────────────
# Tier classification — delegates to tenant_loader (per-tenant titles.yaml)
# ─────────────────────────────────────────────────────────────────────────────

def _tier_for(job_title, has_reports=False):
    """Single source of truth: tenant_loader.classify_tier()."""
    return _classify_tier(job_title or '', has_direct_reports=has_reports, is_active=True)


def is_admin_title(job_title):
    """True if title maps to admin tier in the active tenant's titles.yaml."""
    return _tier_for(job_title) == 'admin'


def is_cteam(job_title):
    """Backward-compat: was 'C-team title (Chief / ExDir keyword)'.
    Now equivalent to is_admin_title since admin tier carries the keyword
    list. Kept for callers that still import it; prefer is_admin_title."""
    return is_admin_title(job_title)


def is_content_lead(job_title):
    return _tier_for(job_title) == 'content_lead'


def is_school_leader(job_title):
    return _tier_for(job_title) == 'school_leader'


def is_admin_user(user):
    if not user:
        return False
    return user.get('is_admin', False)


def get_user_scope(user):
    """Return the user's permission tier + (for school_leader) their school.

    Returns one of:
      {'tier': 'admin'}
      {'tier': 'content_lead'}
      {'tier': 'school_leader', 'school': '<school name>'}
      {'tier': 'supervisor'}
      {'tier': 'self_only'}
      {'tier': None}  # not authenticated
    """
    if not user:
        return {'tier': None}
    job_title = user.get('job_title') or ''
    school = user.get('school') or ''
    has_reports = is_supervisor(user)

    tier = _classify_tier(job_title, has_direct_reports=has_reports, is_active=True)

    if tier == 'school_leader' and school:
        return {'tier': 'school_leader', 'school': school}
    return {'tier': tier}


# ─────────────────────────────────────────────────────────────────────────────
# Org hierarchy (email-based recursive CTE)
# ─────────────────────────────────────────────────────────────────────────────

def get_accessible_emails(conn, email, job_title):
    """
    Get all staff emails the user can access. Used by check_access() for
    per-record authorization on staff profiles, action steps, touchpoints.

    Tier behavior (mirrors permissions.schema.yaml):
      - admin / content_lead: all active staff (Content Leads coach across
        all schools; their PMAP exclusion is enforced at the capability
        layer, not by trimming this list)
      - school_leader: own downline + ALL active staff at their school
        (so when they click into any teacher at their school the profile
        loads, not just their direct reports)
      - other supervisors: own + recursive downline
      - everyone else: self only
    """
    # All-staff tiers: admin and content_lead.
    if is_content_lead(job_title) or is_admin_title(job_title):
        cur = conn.cursor()
        cur.execute("SELECT email FROM staff WHERE is_active")
        return [r[0] for r in cur.fetchall()]

    # Always include self
    own = (email or '').lower()
    accessible = {own} if own else set()

    # Add recursive downline for supervisors
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM staff WHERE supervisor_email = %s AND is_active", (email,))
    if cur.fetchone()[0] > 0:
        cur.execute("""
            WITH RECURSIVE downline AS (
                SELECT email FROM staff
                WHERE supervisor_email = %s AND is_active

                UNION ALL

                SELECT s.email FROM staff s
                INNER JOIN downline d ON s.supervisor_email = d.email
                WHERE s.is_active
            )
            SELECT DISTINCT email FROM downline
        """, (email,))
        for r in cur.fetchall():
            accessible.add(r[0])

    # School leaders: also include all active staff at their school.
    if is_school_leader(job_title):
        cur.execute("SELECT school FROM staff WHERE LOWER(email) = LOWER(%s)", (email,))
        row = cur.fetchone()
        leader_school = row[0] if row else None
        if leader_school:
            cur.execute(
                "SELECT email FROM staff WHERE is_active AND school = %s",
                (leader_school,),
            )
            for r in cur.fetchall():
                if r[0]:
                    accessible.add(r[0])

    return list(accessible)


def check_access(user, target_email):
    """Check if user can view a specific staff member.
    Self is always allowed — every staff member can view their own profile."""
    if not user:
        return False
    if user.get('is_admin'):
        return True
    if user.get('email', '').lower() == (target_email or '').lower():
        return True
    accessible = user.get('accessible_emails', [])
    return target_email.lower() in accessible


def is_supervisor(user):
    """Check if user has any direct reports (accessible emails beyond their own)."""
    if not user:
        return False
    if user.get('is_admin', False):
        return True
    own = (user.get('email') or '').lower()
    accessible = user.get('accessible_emails', [])
    return any((e or '').lower() != own for e in accessible)
