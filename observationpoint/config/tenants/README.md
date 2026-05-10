# Tenants

Each customer of ObservationPoint has a folder under `config/tenants/<slug>/`.
The active tenant is selected at deployment time via the `TENANT_ID`
environment variable.

## Layout

```
tenants/
  ├─ _example/              Template — copy this when onboarding a new tenant
  ├─ firstline-schools/     FirstLine Schools (worked example, the original deployment)
  └─ <new-tenant-slug>/     One folder per customer
```

## Files

Inside each tenant folder:

- `tenant.yaml` — tenant metadata: name, allowed email domains, school year,
  branding, default rubric filenames.
- `titles.yaml` — maps the tenant's job titles to ObservationPoint permission
  tiers (admin / content_lead / school_leader / supervisor / self_only).
- `commitments.json` — *optional* — community values / commitments shown in
  Celebrate flows.
- `vision.json` — *optional* — vision of excellent instruction shown in
  Fundamentals + observation summaries.
- `action_steps_file` — *optional* — coaching playbook (e.g., Get Better Faster).
- `rubrics/` — observation/eval rubrics. App looks here first for any rubric
  referenced in `tenant.yaml`.

## Onboarding a new tenant

1. Copy `_example/` to `<new-slug>/`.
2. Edit `tenant.yaml` (name, domains, school year, branding).
3. Edit `titles.yaml` (map their actual titles to tier IDs).
4. Drop their rubric JSON files into `rubrics/` (or seed from
   `config/observation_frameworks/` and customize).
5. Set `TENANT_ID=<new-slug>` in the deployment environment.

## Why per-tenant folders, not a database table?

Single-tenant runtime to start (one deployment per customer). Files in version
control = easy diffing, reviewable changes, no DB migration to ship a new
tenant. When customer count outgrows this pattern (~20–50+), migrate to
DB-driven config. See `docs/multi-tenant-roadmap.md`.
