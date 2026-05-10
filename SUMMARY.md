# Overnight Summary — TalentPoint Suite

**Date:** May 9 → May 10, 2026
**Repo:** `github.com/sshirey-cpc/talentpoint-suite`

Read this in the morning. Everything you need to review is linked below.

---

## What you decided last night (locked in)

1. **Brand stack:** Confluence Point Consulting → TalentPoint (suite) → PeoplePoint (dashboard) + ObservationPoint (action) + future Points.
2. **Tech stack:** React 19 + Vite + Tailwind 4 + Flask + Postgres + BigQuery — matching what you actually built in ObservationPoint, not the old Next.js plan.
3. **Repo:** `sshirey-cpc/talentpoint-suite` monorepo — both apps + shared + mocks + docs + research.
4. **Two products that feel like one** (Google Workspace pattern). Suite top bar with cross-app switching.
5. **Multi-tenant strategy:** single-tenant per deployment to start. Migrate at ~20–50 customers.
6. **Backport policy:** FirstLine version and product version are fully separate after fork. You manually decide what crosses.

---

## What I did overnight

### A. Backend genericization (productized fork of FirstLine ObservationPoint)

- **New module** [`observationpoint/tenant_loader.py`](observationpoint/tenant_loader.py) — loads per-tenant config, classifies tier, resolves rubrics. Active tenant set via `TENANT_ID` env var.
- **All FLS-specifics moved out of code into config.** Commitments, vision, rubrics (teacher/leader/PreK), action-steps guide → all now live under [`observationpoint/config/tenants/firstline-schools/`](observationpoint/config/tenants/firstline-schools/). The CLASS PreK descriptors (a public framework) moved to [`config/observation_frameworks/`](observationpoint/config/observation_frameworks/).
- **Permissions split** into shared schema + per-tenant titles. `permissions.yaml` deleted. Now [`config/permissions.schema.yaml`](observationpoint/config/permissions.schema.yaml) is shared, [`config/tenants/<id>/titles.yaml`](observationpoint/config/tenants/firstline-schools/titles.yaml) is per-tenant.
- **`config.py` and `auth.py`** refactored to use `tenant_loader.classify_tier()` instead of hardcoded title lists. `ALLOWED_DOMAIN` (single string) → `ALLOWED_DOMAINS` (list per tenant).
- **`_example` tenant template** at [`config/tenants/_example/`](observationpoint/config/tenants/_example/) — copy this folder to onboard a new customer. README walks through it.
- **`tools/gen_permissions_md.py`** rewritten to read schema + tenant titles. Run with `TENANT_ID=<slug>`.

### B. Specs documented (so the next pass is clear)

- [**`observationpoint/docs/rubric-upload-schema.md`**](observationpoint/docs/rubric-upload-schema.md) — DB schema, API endpoints, validation for the planned admin rubric-upload UI.
- [**`docs/peoplepoint-observationpoint-api.md`**](docs/peoplepoint-observationpoint-api.md) — full API surface between the two apps, what-lives-where matrix, single-sign-on across the suite.
- [**`docs/MIGRATION.md`**](docs/MIGRATION.md) — running log of every change and every TODO that came up. **Open this first.**

### C. Research

- [`research/rubric-frameworks.md`](research/rubric-frameworks.md) — TNTP, Danielson, Marzano, Marshall, CLASS. License notes, comparisons, recommendation: ship Marshall as the only included starter (it's the only fully-free comprehensive one); link out and provide empty scaffolds for the others.
- [`research/multi-tenant-flask.md`](research/multi-tenant-flask.md) — three patterns (DB-per-tenant, schema-per-tenant, shared schema with RLS) with tradeoffs and a recommended migration path: stay single-tenant now → schema-per-tenant at ~20 customers → shared schema with RLS at hundreds.

### D. Mocks (HTML, sharing one design system)

[**Open `mocks/index.html` in your browser**](mocks/index.html) — that's the front door for everything below.

| Group | Mocks |
|---|---|
| Suite-level | Design system · Sign-in |
| PeoplePoint | Today (home) · People list · Person detail · Network |
| ObservationPoint | Home · Observe form · PMAP / Eval cycle · Staff profile · Self-reflection |

All share [`mocks/shared/suite.css`](mocks/shared/suite.css) — the design system in code form. Aesthetic: calm river palette, deep navy hero, teal for PeoplePoint, slate-blue for ObservationPoint, status colors muted (no alarmist red). Sidekick voice throughout.

Schools are fictional (Horizon Middle Academy, Cedar Grove Elementary, Pinecrest PreK Center) — your demo-not-FirstLine rule enforced.

---

## What I did NOT do (per your hard rules)

- **Did not redesign UI of the existing FirstLine app.** Mocks define the target; refactoring the React frontend will happen after you approve the mocks.
- **Did not touch your existing `~/confluence-point-consulting/talentpoint/` prototype folder.** Untouched.
- **Did not touch the FirstLine repo.** Read-only clone in `/tmp` was the source. Productized version is its own thing.
- **Did not delete or rewrite working code without approval.** Refactors preserve the existing public API of `auth.py`/`config.py`; old function signatures still work.

---

## Open questions for you (in MIGRATION.md too)

1. **Network-team school name** — At FLS it's "FirstLine Network". Productized default? "Network" / "Central Office" / "Home Office"? (Per-tenant configurable either way.)
2. **Email "from" address pattern** — Should ObservationPoint default to `notifications@<tenant-domain>` for outgoing emails, or let each tenant set their own?
3. **Rubric library licensing** — Plan: ship **Marshall** as the only fully-bundled starter (free, comprehensive). For TNTP/Danielson/Marzano/CLASS, ship the structural scaffold (empty domain shells) so admins paste their own descriptors per their license. Sound right?
4. **Default DB host** — Stay strict env-var-only or set a sensible Cloud SQL default?

---

## Suggested order of review

1. [`SUMMARY.md`](SUMMARY.md) — this file (you're here)
2. [`docs/MIGRATION.md`](docs/MIGRATION.md) — every change and every still-TODO
3. **[`mocks/index.html`](mocks/index.html) — the visual deliverable.** Spend most time here.
4. [`docs/peoplepoint-observationpoint-api.md`](docs/peoplepoint-observationpoint-api.md) — how the two apps talk
5. [`observationpoint/config/tenants/README.md`](observationpoint/config/tenants/README.md) — tenant onboarding pattern
6. [`research/rubric-frameworks.md`](research/rubric-frameworks.md) — license notes, decision needed on libraries
7. [`research/multi-tenant-flask.md`](research/multi-tenant-flask.md) — when we cross the ~20 customer line

---

## Git history

Three commits overnight:

```
3d7a911  Add mocks: design system + suite login + PeoplePoint trio + ObservationPoint home & observe
325a4ea  Genericize ObservationPoint: tenant config layer + permissions schema split
7039741  Initialize talentpoint-suite repo with FirstLine ObservationPoint as starting point
```

(Plus this final commit with PMAP/StaffProfile/Self-Reflection/Network mocks and SUMMARY.md.)

Each commit has a thorough body. `git log --oneline` to see the sequence.

---

## Where to take it next (your call when you're ready)

After mocks approval:

1. Continue genericizing the parts I documented as TODO in MIGRATION.md (email templates, db.py FLS strings, login page placeholder).
2. Build the rubric upload backend (DB migration → API → admin UI).
3. Scaffold PeoplePoint as a real Vite+Flask app under `peoplepoint/`. Use the patterns ObservationPoint already established.
4. Wire up shared SSO across the two apps.
5. Onboard a second test tenant (KIPP Delta? a dummy "Lakeside Schools"?) end-to-end to validate the tenant-loader pattern actually works at the deployment level.

I'll keep memory updated and pick this up cleanly when you're back.

— C
