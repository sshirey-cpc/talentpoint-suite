# Multi-Tenant Patterns for Flask + Postgres

Reference for the ObservationPoint productization. We're starting
single-tenant (one deployment per customer). When customer count makes
that ops-painful (~20–50+), migrate to one of these patterns.

## Three patterns — pick by how isolated tenants need to be

### 1. Database-per-tenant (highest isolation)

Each tenant has their own Postgres database. The Flask app is one codebase
but routes each request to the right database based on tenant ID.

**Pros:**
- Strong physical data isolation (impossible to leak across tenants)
- Easy to back up, restore, or delete a single tenant
- Schema migrations can be staged per-tenant
- Compliance-friendly (clear tenant boundary)

**Cons:**
- Connection pool sprawl — one pool per tenant
- Cross-tenant queries (analytics) require federation
- Harder to bulk-update all tenants

**Best for:** Compliance-sensitive (HIPAA-like, FERPA-strict), or when
tenants insist on single-tenant for legal reasons. Or as a stepping stone
from single-deployment-per-tenant before going fully shared.

**Implementation sketch:**

```python
from flask import g, request

def get_tenant_db(tenant_id):
    """Return a connection to the right tenant's DB. Cached per-process."""
    pool = _pools.get(tenant_id)
    if pool is None:
        cfg = load_tenant_db_config(tenant_id)  # from tenant.yaml or env
        pool = psycopg2.pool.ThreadedConnectionPool(2, 10, **cfg)
        _pools[tenant_id] = pool
    return pool

@app.before_request
def resolve_tenant():
    g.tenant_id = identify_tenant_from_request()  # subdomain / JWT / header
    g.db = get_tenant_db(g.tenant_id)
```

### 2. Shared DB, schema-per-tenant

One Postgres instance, one database, one schema per tenant. The Flask app
sets `SET search_path TO tenant_<id>, public;` on each request.

**Pros:**
- Single connection pool
- Cross-tenant analytics easy (`UNION ALL` across schemas)
- Schema migrations parallelizable but per-schema

**Cons:**
- Postgres has a soft limit on schema count (~thousands work, but ergonomics suffer past a few hundred)
- Must remember to set search_path on every connection
- Permissions are per-schema (more grants)

**Best for:** Mid-sized SaaS with 50–500 tenants and limited cross-tenant analytics needs. Sweet spot for most B2B SaaS.

**Implementation sketch:**

```python
@app.before_request
def set_search_path():
    tenant_id = identify_tenant_from_request()
    g.tenant_id = tenant_id
    schema = f'tenant_{tenant_id.replace("-", "_")}'
    cur = db.get_conn().cursor()
    cur.execute(f"SET search_path TO {schema}, public;")
```

### 3. Shared schema, tenant_id column (most economical)

One Postgres instance, one database, one schema. Every table has a
`tenant_id` column. Every query has `WHERE tenant_id = :current_tenant`.

**Pros:**
- Lowest infrastructure cost
- One pool, one schema, one set of indexes
- Easiest to scale to thousands of tenants
- Simplest migration story

**Cons:**
- Data isolation is by code discipline only. One missing `WHERE` clause = cross-tenant leak.
- Queries must always filter — easy to forget
- Backups per-tenant require row-level filtering
- Largest tenants can degrade query performance for small tenants without partitioning

**Best for:** SaaS at thousands of tenants where compliance is satisfied
by audited code. The pattern most modern multi-tenant SaaS uses.

**Implementation sketch:** Use Postgres Row-Level Security to enforce
isolation at the DB layer, not just the app:

```sql
ALTER TABLE staff ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON staff
    USING (tenant_id = current_setting('app.tenant_id')::text);
```

```python
@app.before_request
def set_tenant_for_rls():
    tenant_id = identify_tenant_from_request()
    g.tenant_id = tenant_id
    cur = db.get_conn().cursor()
    cur.execute("SET app.tenant_id = %s", (tenant_id,))
```

With RLS in place, even a missing `WHERE tenant_id = ...` in app code will
return only the current tenant's rows. Belt and suspenders.

## Recommendation for ObservationPoint

**Now (single-tenant per deployment):** No code changes needed beyond what's already done — `TENANT_ID` env var, per-tenant config folder, per-tenant DB name.

**At ~20 customers — migrate to schema-per-tenant.** Why:

- ObservationPoint already separates concerns by tenant config files; schemas mirror that structure
- BigQuery analytics already use one dataset per tenant — same pattern in Postgres reduces cognitive load
- Migration is simpler than going straight to shared-schema-with-tenant_id (each tenant becomes a schema; tables stay the same)
- If we later need to go to shared schema, we can — schemas-per-tenant is a stable plateau

**At ~hundreds of customers — consider shared schema with RLS.** Postgres
RLS makes the safety net automatic. SAAS at this scale (Stripe, Notion,
Linear, Vercel) all settled here.

## Tenant identification

Three ways to know which tenant a request is for:

1. **Subdomain:** `firstline.observationpoint.com` → tenant `firstline`. Best UX, requires DNS + SSL setup per tenant.
2. **JWT claim:** Tenant baked into the auth token at login. Best for API-first apps; requires SSO/JWT setup.
3. **Path prefix:** `observationpoint.com/firstline/...` → tenant `firstline`. Easiest setup; messier URLs.

For ObservationPoint when we go multi-tenant: **subdomain**. Schools love
seeing their network's name in the URL, and it pairs nicely with the
"single-tenant feel" we want.

## Migration checklist (when we cross the line)

1. Audit every SQL query in `db.py` and `app.py`. Flag any that lack a tenant filter.
2. Add a `tenant_id` (or `schema_name`) resolver in `before_request`.
3. Migrate Postgres: backfill `tenant_id` column on all tables, or create per-tenant schemas and copy rows in.
4. Enable RLS or schema-routing.
5. Update connection management — single pool, but tenant context per request.
6. Test with 2 tenants on the same instance before turning down the per-tenant deployments.
7. Per-tenant rollback plan in case of cross-tenant leak.

## References

- Postgres RLS: https://www.postgresql.org/docs/current/ddl-rowsecurity.html
- Schema-per-tenant patterns: https://www.citusdata.com/blog/2018/02/13/three-approaches-to-postgresql-multitenancy/
- Stripe's tenant model: https://stripe.com/blog/online-migrations
- Notion's database scaling: https://www.notion.so/blog/sharding-postgres-at-notion
