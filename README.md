# Word Forensics System

An academic-integrity platform: a Microsoft Word add-in that records
document-writing activity during an assignment, a Django backend that
stores and analyzes it, and a lecturer dashboard for reviewing how a
submission developed over time.

**Read this first:** see `docs/forensic-methodology.md` for what is (and
isn't) recorded, and why the system never outputs an accusation like
"student cheated" — only descriptive evidence for a lecturer to review.

## What's implemented in this build

- ✅ Django backend: full auth (JWT, roles), assignments, submissions,
  writing sessions, snapshots, forensic events, the diff/reconstruction
  engine, timeline/analytics/replay endpoints, an idempotent batched sync
  endpoint, ML anomaly detection (Isolation Forest over each submission's
  own baseline), JSON/CSV reporting, and an audit log.
- ✅ React lecturer dashboard: assignment list, assignment detail with a
  submissions table, and the core three-column forensic view (timeline /
  document viewer with event highlighting / event details), plus a word
  count trajectory chart and ML indicator panel.
- ✅ Word Office.js add-in: login, assignment selection, consent screen,
  real one-second document polling via `Word.run`, an IndexedDB offline
  queue, and periodic idempotent synchronization.
- ✅ A `seed_demo_data` command that recreates the spec's acceptance-test
  scenario (normal writing → 632-word large insertion → editing → 5-minute
  idle period → submission) so the whole flow can be exercised immediately.

## What's intentionally out of scope for this build (documented, not faked)

- PDF report export (JSON/CSV are fully functional; a PDF template can be
  layered on `ReportService.build()` without touching the underlying data).
- The full replay *scrubber UI* (the backend's `/replay/` endpoint and
  `DocumentReconstructionService.generate_replay_sequence()` are real and
  working; the dashboard doesn't yet wire up play/pause/speed controls).
- Celery/Redis background processing — the spec explicitly says not to
  introduce this for the SQLite version; `process_forensic_analysis` is a
  management command instead, exactly as instructed.
- Docker files (see below) are provided but not required for local dev.
- Automated test suites are stubbed with the structure described in
  `docs/` rather than fully written out, given the size of the spec.

None of the above is faked in code — each is either a genuine, working
subset of the feature or clearly absent.

---

## Backend setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env

python manage.py makemigrations
python manage.py migrate
python manage.py seed_demo_data
python manage.py process_forensic_analysis   # populates ML indicators
python manage.py createsuperuser             # optional, for /admin/
python manage.py runserver
```

Backend runs at `http://localhost:8000`. API root: `http://localhost:8000/api/v1/`.

Demo accounts created by `seed_demo_data` (password `password123` for all):
`lecturer1`, `student1`, `student2`, `student3`.

## Lecturer dashboard setup

```bash
cd lecturer-dashboard
npm install
cp .env.example .env
npm run dev
```

Runs at `http://localhost:5173`. Log in as `lecturer1` / `password123`.

## Word add-in setup

```bash
cd word-addin
npm install
cp .env.example .env
npm run dev
```

Runs at `http://localhost:3000`. To actually side-load it into Word, you
need Office's dev certificates and a real HTTPS localhost origin (Word
Add-ins require HTTPS). The quickest path:

```bash
npm install -g office-addin-dev-certs
npx office-addin-dev-certs install
```

Then update `vite.config.ts` to use the generated cert, re-run `npm run
dev`, and in Word: **Insert → My Add-ins → Upload My Add-in** and select
`manifest.xml`. Log in with `student1` / `password123`.

Without side-loading, you can still develop the taskpane UI in a normal
browser at `localhost:3000` — `DocumentMonitor` detects the absence of
`Office`/`Word` globals and no-ops instead of crashing.

## Running the whole flow

1. Start the backend, run `seed_demo_data`.
2. Start the lecturer dashboard, log in as `lecturer1`, open "Database
   Systems Research Assignment", click into John Doe's submission — you'll
   see the full recorded scenario including the large insertion and the
   idle period.
3. Optionally side-load the add-in and log in as `student1` to record a
   *new* live submission from scratch.

## Configuration

All forensic thresholds live in `backend/.env` (see `.env.example`) and
are read once via `settings.FORENSIC_CONFIG` — nothing is hard-coded into
detection logic.

## Database migration path (SQLite → PostgreSQL)

Models use only the Django ORM (no raw SQL, no SQLite-specific fields).
To move to PostgreSQL later: install `psycopg2-binary`, change the
`DATABASES` dict in `config/settings/base.py`, and re-run `migrate`
against the new database.

## Docker

`docker-compose.yml` and `Dockerfile`s are provided for the backend and
dashboard, but local development does not require Docker.

## Project structure

```
word-forensics/
├── backend/            Django REST API + ML engine
├── lecturer-dashboard/ React + Vite + Tailwind dashboard
├── word-addin/         Office.js Word task pane add-in
├── docs/               Architecture, methodology, API notes
├── docker-compose.yml
└── README.md
```
