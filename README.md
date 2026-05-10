# TalentPoint Suite

The talent operations platform for K-12 schools, by [Confluence Point Consulting](https://confluencepointconsulting.com).

## Brand Stack

```
Confluence Point Consulting (company)
  └─ TalentPoint (platform / suite of tools)
       ├─ PeoplePoint — see your people (dashboard)
       ├─ ObservationPoint — observe and develop them
       └─ Future: RetentionPoint, RecruitPoint, etc.
```

## Repository Layout

- `peoplepoint/` — dashboard app (Vite + React, Flask backend)
- `observationpoint/` — observation/eval app (Vite + React, Flask backend)
- `shared/` — shared code (auth, design system, BigQuery clients)
- `mocks/` — design mockups (HTML)
- `docs/` — architecture and product docs
- `research/` — rubric frameworks, multi-tenant patterns, market notes

## Status (May 10, 2026)

ObservationPoint code copied in from FirstLine deployment, genericization pass in progress. PeoplePoint dashboard pending. See `docs/MIGRATION.md` for what's been changed.
