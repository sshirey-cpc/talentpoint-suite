# PeoplePoint ↔ ObservationPoint API Surface

Two-app architecture (Google Workspace pattern): PeoplePoint is the dashboard
(see your people), ObservationPoint is the action tool (observe, evaluate,
write-up, develop). They share a database and an auth domain, but run as
separate services so customers can buy them separately or bundled.

This doc defines how PeoplePoint *talks to* ObservationPoint when a user
needs to act on a person they're viewing.

## Principles

1. **PeoplePoint never owns observation data.** It reads from the shared
   warehouse (BigQuery) and links out to ObservationPoint when a leader
   wants to write something.
2. **PeoplePoint doesn't know which eval tool the customer uses.** It calls
   a generic "open the connected tool to act on person X" hook. If the
   tenant has ObservationPoint, that hook resolves to ObservationPoint.
   If they have LevelData/Whetstone/Frontline, it resolves to those.
3. **All cross-app calls go through the suite-level config.** The tenant
   config names which eval tool is connected and how to deep-link to it.

## Tenant config — connected tools

In `config/tenants/<id>/tenant.yaml`:

```yaml
connected_tools:
  observation:
    provider: "observationpoint"            # or 'leveldata', 'whetstone', 'frontline', 'none'
    base_url: "https://obs.firstlineschools.org"
    sso: shared                              # 'shared' | 'separate'
    deep_links:
      observe:        "{base}/app/observe?email={email}"
      pmap:           "{base}/app/pmap?email={email}&cycle={cycle}"
      profile:        "{base}/app/staff/{email}"
      write_up:       "{base}/app/write-up?email={email}"
      self_reflect:   "{base}/app/self-reflection"
```

Each `{token}` is substituted at link-render time.

## API endpoints (PeoplePoint side)

```
GET  /api/people                          list people scoped to current user's hierarchy
GET  /api/people/<email>                  one person + the seven data points
GET  /api/people/<email>/last-connection  most recent OP/eval-tool touchpoint summary
GET  /api/people/<email>/eval-status      current eval cycle status (where in PMAP)
GET  /api/people/<email>/itr-status       seasonal ITR status (only if season active)
GET  /api/connected-tool/links/<email>    dictionary of deep-link URLs for active tools
```

Response shape for `/api/people/<email>`:

```json
{
  "email": "maria.lopez@horizon.edu",
  "name": "Maria Lopez",
  "school": "Horizon Middle Academy",
  "job_title": "Math Teacher (Grade 7)",
  "supervisor_email": "p.collins@horizon.edu",

  "data_points": {
    "status":          { "filled": true, "since": "2024-08-12" },
    "tenure":          { "hire_date": "2024-08-12", "years": 1.7 },
    "last_connection": { "kind": "observation", "at": "2026-04-22", "by": "Patrick Collins" },
    "eval_cycle":      { "stage": "mid_year_observation_done", "next": "self_reflection_due" },
    "itr":             { "completed": true, "intent": "yes", "completed_at": "2026-01-18" },
    "pto_balance":     { "days": 7.5 },
    "birthday":        { "month": 11, "day": 14, "today": false }
  },

  "leader_flag": null,

  "connected_tool_links": {
    "observe":      "https://obs.horizon.edu/app/observe?email=maria.lopez@horizon.edu",
    "profile":      "https://obs.horizon.edu/app/staff/maria.lopez@horizon.edu",
    "write_up":     "https://obs.horizon.edu/app/write-up?email=maria.lopez@horizon.edu"
  }
}
```

## API endpoints (ObservationPoint side)

ObservationPoint already exposes the BigQuery-backed reads PeoplePoint
needs. PeoplePoint reads them directly via the shared BigQuery dataset,
NOT via cross-app HTTP calls (cheaper, no auth roundtrip, no rate limits).

What ObservationPoint exposes for PeoplePoint:

```
GET /api/staff/<email>                       (existing) staff profile
GET /api/staff/<email>/touchpoint-history    (existing) last N observations + meetings
GET /api/staff/<email>/eval-summary          NEW — current PMAP cycle stage
GET /api/itr/status                          NEW — list of ITR responses, gated by season
```

The new endpoints are the productization work; the existing ones already
serve the FirstLine deployment.

## Single sign-on across the suite

Both apps run under the same Google OAuth client and share session cookies
on a shared parent domain (e.g., `*.firstlineschools.app`). Login on either
app gives you a session for both. No bouncing.

For tenants that prefer separate SSO (rare), `tenant.yaml.connected_tools.observation.sso = "separate"`
makes PeoplePoint open ObservationPoint in a new tab and let it handle its
own login.

## Data flow summary

```
HRIS (UKG / Namely / Frontline / etc.)
       │
       ▼
   BigQuery (one dataset per tenant)
       │
   ┌───┴───┐
   ▼       ▼
PeoplePoint   ObservationPoint
(reads)        (reads + writes)
   │            │
   └─────┬──────┘
         ▼
   Postgres (shared, transactional)
   - touchpoints, observations, action_steps
   - pmap, self_reflection, pip, write_up
   - rubrics, permissions, impersonation_log
```

PeoplePoint is read-only against Postgres in v1 (only the leader_flag is a
PeoplePoint write — and even that lives in a peoplepoint_flags table to
keep the boundaries clean).

## What lives where

| Concern                         | PeoplePoint | ObservationPoint |
|---------------------------------|:-----------:|:----------------:|
| HRIS-derived staff data         |     ✅      |        ✅        |
| Hierarchy / supervisor chain    |     ✅      |        ✅        |
| Seven data points               |     ✅      |        —         |
| Seasonal toggles (ITR, etc.)    |     ✅      |        —         |
| Birthday surfacing              |     ✅      |        —         |
| Leader flag                     |     ✅      |        —         |
| Observation form + scoring      |      —      |        ✅        |
| PMAP / evaluations              |      —      |        ✅        |
| Self-Reflection                 |      —      |        ✅        |
| Write-Up + Acknowledge          |      —      |        ✅        |
| PIP                             |      —      |        ✅        |
| Solicit Feedback / Response     |      —      |        ✅        |
| Action steps + coaching         |      —      |        ✅        |
| Rubrics                         |      —      |        ✅        |
| Touchpoint history              |     read    |     own + write  |
| Permissions schema              |    shared   |      shared      |
| Impersonation                   |    shared   |      shared      |
