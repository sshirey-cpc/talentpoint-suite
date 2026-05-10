# MIGRATION.md — FirstLine ObservationPoint → Productized ObservationPoint

This is the running log of changes made when forking the FirstLine
ObservationPoint into the productized version under `talentpoint-suite/`.
Read top-to-bottom in the morning to see exactly what was changed and what
still needs work.

**Forked from:** `github.com/sshirey-cpc/firstline-schools/observationpoint`
**On:** 2026-05-09 → 2026-05-10
**By:** Claude (overnight productization pass), under Scott's approved scope.

---

## Decisions locked before the fork (May 9, 2026)

- **Brand stack:** Confluence Point Consulting → TalentPoint (suite) → PeoplePoint (dashboard) + ObservationPoint (eval) + future Points.
- **Tech stack:** React 19 + Vite + Tailwind 4 frontend; Flask + Postgres + BigQuery backend.
- **Repo:** `sshirey-cpc/talentpoint-suite` monorepo with `peoplepoint/`, `observationpoint/`, `shared/`, `mocks/`, `docs/`, `research/`.
- **Two products that feel like one** (Google Workspace pattern). Sold separately or bundled.
- **Multi-tenant:** Single-tenant runtime to start (one deployment per customer). Migrate to shared multi-tenant when customer count is painful (~20–50+).
- **Backport policy:** Fully separate after fork. Scott manually decides what crosses between FirstLine and productized versions.

---

## Done overnight (2026-05-10)

### 1. Repo structure

Created `sshirey-cpc/talentpoint-suite` with:

```
talentpoint-suite/
  ├─ README.md                          brand stack and layout
  ├─ .gitignore
  ├─ peoplepoint/                       (placeholder — dashboard not built yet)
  ├─ observationpoint/                  forked from FirstLine, genericized
  ├─ shared/                            (placeholder — for cross-app code)
  ├─ mocks/                             HTML mockups (this overnight pass)
  ├─ research/                          rubric frameworks, multi-tenant patterns
  └─ docs/                              architecture and product docs
```

### 2. Tenant config layer

New module: `observationpoint/tenant_loader.py`. Loads per-tenant config
from `config/tenants/<TENANT_ID>/`. Active tenant set via `TENANT_ID`
env var (defaults to `firstline-schools` for backward compat).

Provides:

- `get_tenant_id()`, `get_tenant_config()` — tenant.yaml metadata
- `get_titles_config()` — title-to-tier mapping
- `get_permissions_schema()` — shared permissions schema
- `get_allowed_domains()` — list of email domains for OAuth
- `get_brand()`, `get_school_year()`, `get_school_years()`
- `get_commitments()`, `get_vision()`, `get_action_steps_guide()` — optional tenant docs
- `get_rubric(rubric_key)`, `get_rubric_by_id(rubric_id)` — load rubrics
- `classify_tier(job_title, has_direct_reports, is_active)` — single source of truth for tier classification
- `is_admin_title(job_title)` — backward-compat helper

All loads cached via `functools.lru_cache` (immutable per process).

### 3. File moves (FLS-specific into firstline-schools tenant folder)

```
forms/fls_commitments.json           → config/tenants/firstline-schools/commitments.json
forms/fls_vision.json                → config/tenants/firstline-schools/vision.json
forms/rubric_teacher.json            → config/tenants/firstline-schools/rubrics/teacher.json
forms/rubric_leader.json             → config/tenants/firstline-schools/rubrics/leader.json
forms/rubric_prek.json               → config/tenants/firstline-schools/rubrics/prek.json
forms/action_steps_guide.json        → config/tenants/firstline-schools/action_steps_guide.json
forms/class_prek_descriptors.json    → config/observation_frameworks/  (public CLASS framework, not tenant-specific)
```

`forms/` is now empty in the productized version.

### 4. Permissions split

- `permissions.yaml` deleted.
- `config/permissions.schema.yaml` is the **shared** capability matrix and
  tier definitions. Identical for all tenants.
- `config/tenants/<id>/titles.yaml` holds **per-tenant** title-to-tier
  mappings (e.g., "Chief Executive Officer" → admin).
- `/api/permissions` endpoint merges the two for the admin viewer.
- `tools/gen_permissions_md.py` rewritten to read both and generate
  `PERMISSIONS.md` per-tenant. Run with `TENANT_ID=<slug>` env var.

### 5. config.py refactor

- `ALLOWED_DOMAIN` (single hardcoded string) replaced by `ALLOWED_DOMAINS` (list, from tenant.yaml).
- `ALLOWED_DOMAIN` kept as a backward-compat alias (first item in the list).
- `HR_TEAM_TITLES`, `C_TEAM_KEYWORDS`, `CPO_TITLE` deprecated as empty stubs. Tier classification now goes through `tenant_loader.classify_tier()`.
- `TENANT_ID` exposed; `DB_NAME` defaults per-tenant (`observationpoint_<tenant_slug>`).
- Hardcoded `DB_HOST` / `PROJECT_ID` removed (env-var-only now).

### 6. auth.py refactor

- `is_cteam`, `is_admin_title`, `is_content_lead`, `is_school_leader` are now thin wrappers around `tenant_loader.classify_tier()`.
- Hardcoded `CONTENT_LEAD_TITLES_EXACT` and `SCHOOL_LEADER_TITLE_KEYWORDS` lists **removed** — both are now per-tenant in `titles.yaml`.
- New `is_allowed_email(email)` helper for OAuth callback domain check (handles multi-domain tenants).
- `get_user_scope()` now delegates entirely to `classify_tier`.

### 7. app.py changes

- OAuth callback uses `is_allowed_email()` and shows the tenant's display name in the 403 message instead of "FirstLine Schools".
- `/api/forms/<form_id>` now resolves through tenant config first (tenant rubrics → tenant root files like commitments/vision → legacy `forms/` fallback).

### 8. _example tenant template

`config/tenants/_example/` is the onboarding starting point. Copy this folder to a new tenant slug, edit the placeholders, set `TENANT_ID=<slug>`. README in `config/tenants/README.md` walks through it.

### 9. Stub specs documented

- `observationpoint/docs/rubric-upload-schema.md` — DB schema, API endpoints, validation rules for the planned admin rubric-upload UI.
- `docs/peoplepoint-observationpoint-api.md` — full API surface between the two apps, tenant-config shape for connected eval tools, what-lives-where matrix.

---

## Still TODO — needs follow-up passes

### Code: residual FLS-specific strings

These are in code, not config — refactoring is more involved. None of them
break the productization for new tenants today (just look like FLS), but
should be tackled before sales:

- **db.py:** Multiple SQL queries filter `school != 'FirstLine Network'` to exclude the FLS network-team virtual school. Pattern is generic (a "non-school" bucket for HQ staff); name is FLS-specific. → Add `network_school_name` to tenant.yaml; substitute in queries.
- **app.py email templates:** Hardcoded `talent@firstlineschools.org`, `hr@firstlineschools.org`, "FirstLine Schools — Education For Life" tagline, FLS navy color. → Read from `tenant.yaml.brand` + `tenant.yaml.support_email`.
- **app.py WIG seed data:** "FLS measures", "FLS network priorities" in `wig_seeds` table-create. → Make seed data tenant-driven (or remove from seeds and let admins configure).
- **app.py login template:** Placeholder text "someone@firstlineschools.org". → Render `someone@{ALLOWED_DOMAINS[0]}` dynamically.
- **frontend/src/lib/rubric-descriptors.js:** Has FLS-specific rubric descriptors hardcoded for tooltips. → Should source from the active rubric JSON instead.
- **frontend/src/pages/Celebrate.jsx:** Comments reference `fls_commitments.json` directly. Behavior unchanged but needs review when productizing tooltips/titles.

### Hardcoded rubric IDs in templates/app.html and prototypes/forms.js

`templates/app.html` lists rubrics by id (`fls_teacher_v1`, `fls_prek_class_v1`, `fls_leader_v1`) for a form picker. Should be driven by `tenant_loader.get_tenant_config().default_rubrics` instead.

### setup_postgres.py / setup_bigquery.py

These set up the schema for one deployment. Should be invokable per-tenant
(`TENANT_ID=<slug> python setup_postgres.py`) and use tenant-scoped DB
names. Mostly works today since DB_NAME is now per-tenant — verify on
next manual run.

### Rubric upload feature (specced, not built)

`observationpoint/docs/rubric-upload-schema.md` has the full plan. Next
passes:

1. Create the `rubrics` table migration.
2. Add `tenant_loader.get_rubric_by_db()` with filesystem fallback.
3. Build `/api/admin/rubrics/...` endpoints.
4. Build the admin UI (drag-drop JSON, version history, library starters).
5. Publish the starter library (TNTP, Danielson, Marzano, Marshall, CLASS).

### PeoplePoint dashboard

Doesn't exist yet as a real app. Mocks in `mocks/peoplepoint/` show the
intended UX. Next pass: scaffold a Vite+Flask app under `peoplepoint/`
using the same patterns ObservationPoint established.

### Multi-tenant migration

Currently single-tenant per deployment. `research/multi-tenant-flask.md`
has the migration plan when customer count outgrows the pattern.

---

## Files to review in the morning

Read these in this order:

1. `README.md` — brand stack and layout
2. `docs/peoplepoint-observationpoint-api.md` — how the two products talk
3. `observationpoint/docs/rubric-upload-schema.md` — admin rubric upload plan
4. `observationpoint/config/tenants/README.md` — tenant onboarding pattern
5. `observationpoint/config/tenants/_example/` — the template
6. `observationpoint/config/tenants/firstline-schools/` — worked example
7. `observationpoint/tenant_loader.py` — the loader module
8. `mocks/` — visual mockups
9. `research/` — rubric frameworks + multi-tenant patterns
10. `docs/MIGRATION.md` — this file (you're reading it)

---

## Commits (overnight)

Run `git log --oneline` in `talentpoint-suite/` to see the full sequence.
Each commit is scoped to a single concern with a detailed body.

---

## Open questions for Scott

1. **Network-team school name** — At FirstLine you call it "FirstLine Network". For the productized version, what should the default be? "Network", "Central Office", "Home Office"? (Configurable per tenant either way, but default matters.)
2. **Email "from" address** — Tenants will need to configure their own SMTP. FirstLine uses `sshirey@firstlineschools.org`. Should we standardize on `notifications@<tenant-domain>` or let each tenant pick?
3. **Rubric library licensing** — TNTP and CLASS are licensed (CC-BY-NC and proprietary respectively). Danielson and Marzano are subscription. Marshall is free. Plan: ship Marshall as the only "starter" rubric included, link out to the others with notes on how to obtain. Sound right?
4. **Default DB host** — Currently env-var-only. Should there be a sensible Cloud SQL default per tenant, or stay strict env-var?
