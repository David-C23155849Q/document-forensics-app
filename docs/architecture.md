# Architecture

```
Student (Microsoft Word)
        │  Office.js
        ▼
Word Forensics Add-in (React + TS)
  - DocumentMonitor (1s polling)
  - LocalQueueManager (IndexedDB, offline-safe)
  - SyncService (batched, idempotent)
        │  HTTPS REST
        ▼
Django REST API  (apps/*)
  - accounts, assignments, submissions, sessions
  - snapshots (SnapshotManager)
  - events (ForensicEvent)
  - forensic (DiffEngine, ForensicEventDetector,
              DocumentReconstructionService,
              TimelineService, AnalyticsService, sync endpoint)
  - ml_analysis (feature_engineering + IsolationForestAnalyzer)
  - reports, audit
        │
        ▼
SQLite3 (portable Django ORM models; swap to PostgreSQL by changing
         DATABASES in config/settings/base.py — no app rewrite required)
        │
        ▼
Lecturer Dashboard (React + TS + Vite + Tailwind + Recharts)
  - Assignments / Assignment detail / Submission forensic view
    (Timeline | Document viewer | Event details)
  - Word count trajectory chart
  - ML indicators panel
```

## Backend app boundaries

Each Django app owns one concern and its own models/serializers/views:

| App           | Responsibility                                            |
|---------------|------------------------------------------------------------|
| accounts      | Users, roles, profiles, JWT login                          |
| assignments   | Assignment CRUD, lecturer ownership                         |
| submissions   | Submission lifecycle (start/submit), ownership enforcement  |
| sessions      | WritingSession start/end                                    |
| snapshots     | DocumentSnapshot model + SnapshotManager (dedup, hashing)    |
| events        | ForensicEvent model + listing/filtering API                 |
| forensic      | DiffEngine, ForensicEventDetector, DocumentReconstructionService, TimelineService, AnalyticsService, the /sync/ endpoint |
| ml_analysis   | MLAnalysis model; ml/ package has the actual analysis code   |
| reports       | ReportService + JSON/CSV export                             |
| audit         | Append-only AuditLog + middleware                            |

Business logic lives in `services.py` / `services/` modules, never in
views — views only translate HTTP <-> service calls.

## Data flow for a single writing tick

1. Add-in reads `document.body.text` via `Word.run`.
2. `DocumentMonitor` compares it to the previous tick's text.
3. It writes a lightweight heartbeat (or full) snapshot and, if the word
   count changed, an event, into IndexedDB via `LocalQueueManager`.
4. `SyncService` flushes the queue to `POST /api/v1/sync/` every N
   seconds (configurable), using client-generated IDs for idempotency.
5. The backend's `SnapshotManager` stores the snapshot (deduping
   identical full-content hashes) and `ForensicEventDetector` compares
   consecutive full snapshots to emit authoritative events server-side
   too — the add-in's own event guesses are stored as "client_reported"
   and the diff-based ones as "document_state_diff", so lecturers can see
   which layer produced which event.
6. The lecturer dashboard reads `/timeline/`, `/document/state/`,
   `/analytics/`, and `/ml-analysis/` to render the forensic view.
