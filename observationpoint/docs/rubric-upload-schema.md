# Rubric Upload — Schema & Backend Spec

Status: **stub** — backend schema and API contract documented; UI not yet built.

## Goal

Tenant admins upload their own observation rubrics (teacher, leader, prek,
or custom) without engineering involvement. Uploaded rubrics live alongside
file-based rubrics in `config/tenants/<id>/rubrics/`, but with a managed
upload pipeline so admins can add/version/retire them through the app.

## Two storage paths

1. **Filesystem (current, default)** — Rubrics live in
   `config/tenants/<id>/rubrics/*.json`. Loaded by `tenant_loader.get_rubric()`.
   Suited for tenant onboarding and version-controlled changes.
2. **Database (new, opt-in for tenant admins)** — Rubrics uploaded through
   the app are stored in the `rubrics` table below. `tenant_loader` is
   updated to check DB first, then fall back to filesystem.

DB-backed rubrics are tenant-editable in the UI; filesystem rubrics are not.
A tenant can mix both: ship filesystem defaults, let admins override.

## Database schema

```sql
CREATE TABLE rubrics (
    id              SERIAL PRIMARY KEY,
    tenant_id       VARCHAR(64) NOT NULL,
    rubric_key      VARCHAR(64) NOT NULL,        -- 'teacher' | 'leader' | 'prek' | <custom>
    rubric_id       VARCHAR(128) NOT NULL,       -- internal id from JSON ('fls_teacher_v1')
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    json_content    JSONB NOT NULL,              -- full rubric JSON
    version         INT NOT NULL DEFAULT 1,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    uploaded_by     VARCHAR(255) NOT NULL,       -- email of admin who uploaded
    uploaded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes           TEXT,                        -- admin notes (e.g., "v2: clarified T3")

    -- Only one active rubric per (tenant, rubric_key) at a time.
    -- Older versions stay in the table for audit / observation history.
    UNIQUE (tenant_id, rubric_key, version)
);

CREATE INDEX idx_rubrics_tenant_active
    ON rubrics (tenant_id, rubric_key)
    WHERE is_active;

CREATE INDEX idx_rubrics_rubric_id
    ON rubrics (rubric_id);
```

Note: existing `scores_v2.rubric_id` (from `setup_bigquery.py`) already
references rubric IDs — DB-backed rubrics keep the same ID convention so
historical scores remain interpretable when a rubric is retired.

## Upload flow

1. Admin opens `/app/admin/rubrics`
2. Picks a rubric key (`teacher` | `leader` | `prek` | new custom slug)
3. Drag-and-drop a JSON file (validated client-side against schema)
4. Optional: paste/edit JSON in a code editor before submit
5. Submits → server validates, increments version, marks new row active,
   marks old row inactive (history preserved)
6. Cache is invalidated; next observation form picks up the new rubric

## Validation

Server rejects upload if:

- Not valid JSON
- Missing required keys: `id`, `name`, `scale`, `dimensions`
- `scale.min` / `scale.max` not integers, or `min >= max`
- `dimensions[]` empty, or any dimension missing `id`, `name`, `question`
- Duplicate dimension `id` within the rubric
- `rubric_id` already used by a different tenant (collision check)

## API endpoints (planned)

```
GET    /api/admin/rubrics                  list all rubrics for active tenant
GET    /api/admin/rubrics/<key>            full rubric JSON for the active version
GET    /api/admin/rubrics/<key>/history    all versions for this key
POST   /api/admin/rubrics/<key>            upload new version (becomes active)
POST   /api/admin/rubrics/<key>/rollback   set a prior version active
DELETE /api/admin/rubrics/<key>/<version>  hide a specific version (audit retained)

GET    /api/admin/rubrics/library          published rubric framework starters
                                           (TNTP, Danielson, Marzano, Marshall, CLASS)
                                           returns JSON suitable for direct upload
```

All endpoints require admin tier (per permissions.schema.yaml `view_permissions_admin`).

## Library: starter rubrics

`/api/admin/rubrics/library` returns a curated list of public-domain or
licensable observation frameworks that admins can clone-and-customize:

```json
{
  "library": [
    {
      "framework": "tntp_core",
      "name": "TNTP Core Teaching Rubric",
      "description": "Five-domain teacher rubric used by many TNTP partners",
      "license": "CC-BY-NC (TNTP)",
      "rubric_keys": ["teacher"],
      "starter_json_url": "/api/admin/rubrics/library/tntp_core/teacher.json"
    },
    {
      "framework": "danielson",
      "name": "Charlotte Danielson — Framework for Teaching",
      "description": "Four-domain teacher framework, widely used in eval systems",
      "license": "All rights reserved (Danielson Group); use within license",
      "rubric_keys": ["teacher"],
      "starter_json_url": "/api/admin/rubrics/library/danielson/teacher.json"
    }
  ]
}
```

See `research/rubric-frameworks.md` for full source/license notes.

## Why JSONB + DB, not just filesystem?

- Tenant admins shouldn't need git or a deploy to update rubrics
- Version history lives next to the data (audit-friendly)
- Score data references rubric_id — keeping rubrics in DB keeps everything
  in one place when a rubric is updated
- Filesystem path stays as the default / starter — tenants who haven't
  customized run on shipped rubrics
