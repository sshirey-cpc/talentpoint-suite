# Tenant Rubrics

Place rubric JSON files here. The default ObservationPoint app expects:

- `teacher.json` — classroom teacher observation rubric
- `leader.json` — school leader / principal evaluation rubric
- `prek.json` — early childhood (PreK) observation rubric

Tenants may also drop in custom rubrics (e.g., `instructional_coach.json`)
and reference them from `tenant.yaml`.

## Format

Each rubric file is JSON with the following shape:

```json
{
  "id": "tenant_<role>_v<version>",
  "name": "Display name",
  "description": "Short description shown in form picker",
  "scale": {
    "min": 1,
    "max": 5,
    "labels": { "1": "Beginning", "2": "Emerging", "3": "Proficient", "4": "Advanced", "5": "Exemplary" },
    "colors": { "1": "#ef4444", "2": "#f97316", "3": "#eab308", "4": "#22c55e", "5": "#0ea5e9" }
  },
  "dimensions": [
    {
      "id": "dim_id",
      "code": "T1",
      "name": "Dimension name",
      "question": "Observation question shown in the form",
      "required": true,
      "note_on_1": true
    }
  ]
}
```

## Seeding from public frameworks

ObservationPoint ships with starter rubrics derived from public frameworks
(see `config/observation_frameworks/`). Copy and customize as needed.

Public frameworks supported as starting points:
- **TNTP Core Teaching Rubric** — used as a base by many TNTP partners
- **Charlotte Danielson — Framework for Teaching** — widely adopted, 4-domain structure
- **Marzano Teacher Evaluation Model** — instructional design + classroom strategies
- **Kim Marshall — Marshall Memo Rubric** — concise, plain-language
- **CLASS PreK** (Hamre/La Paro/Pianta) — emotional support / classroom organization / instructional support

See `config/observation_frameworks/README.md` for source links and licensing notes.
