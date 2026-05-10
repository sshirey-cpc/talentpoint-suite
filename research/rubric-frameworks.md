# Public / Licensable Observation Rubric Frameworks

Reference for the ObservationPoint rubric library. Each framework is a
well-established structure used by K-12 networks. ObservationPoint can ship
clean-room versions or links + clone-and-customize starters depending on
licensing.

## TNTP Core Teaching Rubric

- **Source:** TNTP (The New Teacher Project)
- **License:** CC-BY-NC for the rubric document; many TNTP partners use it as the basis of their own rubrics
- **Domains/Standards (5):** Essential Content · Academic Ownership · Demonstration of Learning · Culture of Learning · Differentiation (depending on version)
- **Scale:** 4 levels typically (1–4)
- **Suited for:** Charter networks, especially TNTP partners and replication organizations
- **K-12 reach:** Wide — used by KIPP, Achievement First, IDEA, FirstLine (FLS rubric is a TNTP derivative)
- **URL:** tntp.org

**Status for ObservationPoint library:** Cite as foundational reference.
FLS's rubric (now in `config/tenants/firstline-schools/rubrics/teacher.json`) is one customization. We can include a clean version as a starter under "TNTP-derived" tag, but should be clear we're not redistributing the proprietary version.

## Charlotte Danielson — Framework for Teaching (FFT)

- **Source:** The Danielson Group (Charlotte Danielson, founder)
- **License:** Subscription / institutional license. NOT open.
- **Domains (4):** Planning and Preparation · Classroom Environment · Instruction · Professional Responsibilities
- **Components:** 22 across 4 domains
- **Scale:** 4 levels (Unsatisfactory · Basic · Proficient · Distinguished)
- **Suited for:** Districts (very common in state eval systems — NY, IL, others)
- **K-12 reach:** The single most adopted framework in US public schools
- **URL:** danielsongroup.org

**Status for ObservationPoint library:** Reference and link out, but **do not redistribute**. Provide a "Danielson-aligned starter" structure (4 domains, 22-component scaffold) with placeholder language admins fill in to comply with their own license.

## Marzano Teacher Evaluation Model

- **Source:** Marzano Resources (Robert Marzano)
- **License:** Subscription / consultant model. NOT open.
- **Domains (4):** Classroom Strategies & Behaviors · Planning & Preparing · Reflecting on Teaching · Collegiality & Professionalism
- **Elements:** 60 in the full model
- **Scale:** 5 levels (Not Using · Beginning · Developing · Applying · Innovating)
- **Suited for:** Networks that want a fine-grained, research-back instructional strategies focus
- **K-12 reach:** Common in Florida, Texas, several CMOs
- **URL:** marzanoresources.com

**Status for ObservationPoint library:** Same as Danielson — reference, link out, scaffold-only starter.

## Kim Marshall Teacher Evaluation Rubric

- **Source:** Kim Marshall (long-running Marshall Memo)
- **License:** Free for educator use
- **Domains (6):** Planning and Preparation · Classroom Management · Delivery of Instruction · Monitoring, Assessment, and Follow-Up · Family and Community Outreach · Professional Responsibilities
- **Items:** ~60 individual indicators
- **Scale:** 4 levels
- **Suited for:** Schools that want a plain-language, comprehensive rubric without the licensing weight
- **K-12 reach:** Independent and charter schools especially
- **URL:** marshallmemo.com (rubric available freely as PDF)

**Status for ObservationPoint library:** **Ship as a default starter rubric.** Free, clear, comprehensive, plain-language. Best fit for "pick something that works out of the box."

## CLASS — Classroom Assessment Scoring System

- **Source:** Hamre, La Paro, Pianta — University of Virginia / Teachstone
- **License:** Proprietary; certification required for valid scoring
- **Versions:** PreK · K-3 · Upper Elementary · Secondary
- **Domains (3):** Emotional Support · Classroom Organization · Instructional Support
- **Dimensions:** 8–10 depending on version
- **Scale:** 7-point (1=low, 7=high)
- **Suited for:** Early childhood (where it's near-universal), Head Start, Title I PreK programs
- **K-12 reach:** PreK ubiquitous; K-12 less common
- **URL:** teachstone.com

**Status for ObservationPoint library:** PreK programs need this. Already shipping `config/observation_frameworks/class_prek_descriptors.json` (Hamre/La Paro/Pianta dimensions and indicators). FLS uses this for PreK. Don't redistribute scoring guides — those require Teachstone certification — but the *structure* (dimensions + indicators) is published.

## Comparison summary

| Framework | License | Cost | Best For | Ship in OP? |
|---|---|---|---|---|
| **TNTP Core** | CC-BY-NC | Free document, license per use | Charter networks, replication CMOs | Reference + scaffold starter |
| **Danielson FFT** | Proprietary | Subscription | Districts, state eval systems | Reference + scaffold only |
| **Marzano** | Proprietary | Subscription | Strategy-focused CMOs | Reference + scaffold only |
| **Marshall** | Free | Free | Independent + charter schools | **Ship as default starter** |
| **CLASS PreK** | Proprietary | Certification + license | PreK / Head Start | Structure shipped (already in repo); scoring requires cert |

## Recommendations for the OP rubric library

Tier 1 — ship clean starters:
- **Marshall** — free, comprehensive, plain-language. Default "pick this if you don't have one."
- **CLASS PreK structure** (already in `config/observation_frameworks/`).
- **TNTP-derived scaffold** — empty 5-domain structure aligned to TNTP names without copying their proprietary descriptors. Customers fill in.

Tier 2 — link out and scaffold:
- **Danielson** — provide an empty 4-domain / 22-component structure. Customer pastes their licensed descriptors.
- **Marzano** — same pattern.

Tier 3 — admin uploads custom:
- Bring-your-own JSON, validated against the rubric schema.

Implementation: see `observationpoint/docs/rubric-upload-schema.md`.
