# Quizine — agent working memory

## What this project is
Quizine is an AI-powered certification study app. Users select a certification from a curated
catalogue (e.g. "Databricks Machine Learning Associate") or enter a custom one. The app
generates flashcards and MCQ exam questions tailored to that cert's official topic domains and
weightings, then runs spaced repetition study sessions and timed exams.

Tagline: *"Knowledge, served fresh."*
Single-user. No auth in v1.

---

## Repo layout

```
quizine/
├── claude.md                  ← you are here
├── decisions.md               ← architecture decisions — read before changing anything
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── app/
│   │   ├── main.py            ← FastAPI app, CORS from env
│   │   ├── core/
│   │   │   └── config.py      ← pydantic-settings, reads .env
│   │   ├── api/
│   │   │   ├── generate.py    ← /generate/mcq
│   │   │   ├── ingest.py
│   │   │   ├── certifications.py  ← /certifications CRUD + seeding
│   │   │   ├── decks.py
│   │   │   ├── study.py
│   │   │   └── exam.py
│   │   ├── models/            ← SQLAlchemy ORM models
│   │   ├── schemas/           ← Pydantic request/response models
│   │   └── services/
│   │       ├── sm2.py         ← SM-2 algorithm (pure function, no DB)
│   │       ├── generation.py  ← Claude API calls
│   │       ├── chunking.py    ← text/PDF/URL → chunks
│   │       └── exam.py        ← exam session logic
│   ├── alembic/
│   ├── seed/
│   │   └── certifications.json  ← verified cert catalogue seed data
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── api/               ← typed fetch wrappers (one file per resource)
    │   ├── components/
    │   ├── hooks/
    │   └── pages/
    └── vite.config.ts         ← proxies /api → localhost:8000
```

---

## Certification data model — read carefully

This is the most important structural concept in the app.

### Two modes for every deck
A deck links to one of:
1. **Verified certification** — `cert_id` set, `custom_cert_name` null. The cert exists in the
   `certifications` table with official topic domains and weightings. The AI prompt is enriched
   with `prompt_context` from the cert record.
2. **Custom certification** — `cert_id` null, `custom_cert_name` set (free text). No domain
   taxonomy available. AI auto-detects topic tags from source text. Heatmaps and weighted exam
   selection are unavailable.

### Key tables
```
certifications   id, slug, display_name, provider, level, pass_score_pct,
                 verified (bool), prompt_context (injected into AI system prompt)

cert_domains     id, cert_id → certifications, name, slug, weight_pct, description
                 (e.g. "Delta Lake Operations", slug "delta-lake-ops", weight 22)

decks            id, cert_id (nullable FK → certifications),
                 custom_cert_name (nullable text), title, created_at

card_tags        card_id → cards, domain_id → cert_domains
                 (replaces free-text topic_tags — domains ARE the tags for verified certs)
```

### prompt_context format (stored per certification)
```
Databricks Certified Data Engineer Associate. Topics by weight:
- Databricks Lakehouse Platform (24%): Delta Lake, Unity Catalog, architecture
- ELT with Spark and Delta Lake (29%): transformations, higher-order functions
- Incremental Data Processing (22%): Auto Loader, Structured Streaming
- Production Pipelines (16%): Databricks Workflows, job orchestration
- Data Governance (9%): Unity Catalog permissions, lineage
Pass mark: 70%. Question style: scenario-based, practitioner level.
```

### Seed data
`backend/seed/certifications.json` contains the initial verified cert catalogue.
Launch set:
- Databricks Machine Learning Associate
- Databricks Machine Learning Professional

Each entry includes `slug`, `display_name`, `provider`, `level`, `pass_score_pct`,
`prompt_context`, and a `domains` array with `name`, `slug`, `weight_pct`, `description`.

A startup script (`seed_certifications.py`) reads this file and upserts into the DB on
`alembic upgrade head` — safe to re-run (upsert by slug).

---

## Post-task browser verification — mandatory
After completing any task that produces a visible UI change or a new API endpoint,
you MUST verify it using Claude in Chrome before marking the task complete.

### For frontend tasks (any Txx touching `frontend/`):
- Confirm the Vite dev server is running on localhost:5173
- Open the relevant page in Chrome
- Interact with the new feature (click buttons, submit forms, trigger the happy path)
- Check the browser console for errors — report any found
- Check the network tab — confirm API calls return expected status codes
- Only mark the task complete if no console errors and the feature behaves as specified

### For backend tasks (any Txx touching `backend/`):
- Confirm the Docker stack is running on localhost:8000
- Open localhost:8000/docs in Chrome
- Find the new or modified endpoint in Swagger UI
- Execute it with realistic test input
- Confirm the response shape matches the schema defined in CLAUDE.md
- Only mark the task complete if the response is correct

### For full-stack tasks:
Run both checks above in sequence.

If Chrome integration is not connected: run `/chrome` in the VS Code panel to reconnect before starting verification. Do not skip verification — flag it explicitly if Chrome is unavailable.

Report format after each verification:
```
Browser check ✅
- Opened: localhost:5173/[page]
- Tested: [what was clicked/submitted]
- Console: clean / [list any errors]
- Network: [endpoint] returned [status]
- Result: pass / fail + detail if fail
```

---

## Conventions — follow these exactly

### Python
- Python 3.12
- Type-annotate every function signature
- Pydantic v2 (`model_dump()` not `.dict()`)
- SQLAlchemy 2.0 style (`select()` not `session.query()`)
- One router per resource in `app/api/`
- Services contain business logic — routes are thin
- Tests in `backend/tests/`, use `pytest` + `httpx.AsyncClient`
- Never hardcode secrets — always use `settings` from `core/config.py`

### SQL / Alembic
- Every migration reversible (`upgrade` + `downgrade`)
- Never modify an existing migration — create a new one
- Table names plural snake_case

### Frontend
- TypeScript strict mode
- One file per resource in `src/api/`
- All API calls through typed wrappers — no raw `fetch` in components
- Tailwind only

### Git
- One branch per phase: `feat/phase-N`
- Commit format: `feat(scope): description (Txx)`

---

## Environment variables

All config in `.env`. See `.env.example`. Read via `app/core/config.py` pydantic-settings.
Never use `os.environ` directly — always use the `settings` singleton.

---

## Running locally

```bash
cp .env.example .env          # fill in ANTHROPIC_API_KEY
docker compose up --build     # API :8000, Postgres :5432
cd frontend && npm install && npm run dev   # UI :5173
```

API docs: http://localhost:8000/docs

---

## Current task queue

Work through in order. Tick and note when done. Do not skip ahead.

### Phase 1 — bootstrap

- [x] **T01** — Create `backend/app/core/config.py` with pydantic-settings. ✅ 2026-04-08
      Fields: `ANTHROPIC_API_KEY`, `DATABASE_URL`, `UPLOADS_DIR`, `CORS_ORIGINS`.
      Export a `settings` singleton.

- [x] **T02** — Fix `backend/app/main.py`: import `settings`, replace hardcoded CORS origin ✅ 2026-04-08
      with `settings.CORS_ORIGINS.split(",")`. Update app title to "Quizine".

- [x] **T03** — Add `POST /generate/flashcards` to `backend/app/api/generate.py`. ✅ 2026-04-08
      Same SSE streaming pattern as `/generate/mcq`.
      Output: `[{"front": "...", "back": "...", "topic_tag": "..."}]`.
      Request: `{text, certification, n_cards, topic_tags[], stream}`.

- [x] **T04** — Write `backend/tests/test_generate.py`. Mock Anthropic client. ✅ 2026-04-08
      Assert: correct response shape, exactly 1 correct MCQ answer, exactly 4 options.

- [x] **T05** — Create `backend/seed/certifications.json` with the 5 launch certs. ✅ 2026-04-08
      Each entry: `slug`, `display_name`, `provider`, `level`, `pass_score_pct`,
      `prompt_context`, `domains[]` (`name`, `slug`, `weight_pct`, `description`).

- [x] **T06** — Create `backend/app/api/certifications.py`. ✅ 2026-04-08
      `GET /certifications` — list all verified certs (for UI picker).
      `GET /certifications/{slug}` — detail with domains.
      `GET /certifications/{slug}/domains` — domain list with weights.

### Phase 2 — vertical slice (frontend)

- [x] **T07** — Scaffold frontend: `npm create vite@latest frontend -- --template react-ts`. ✅ 2026-04-08
      Add Tailwind. Vite proxy: `/api` → `http://localhost:8000`.

- [x] **T08** — `frontend/src/api/generate.ts` — typed SSE wrappers for both generate endpoints. ✅ 2026-04-08

- [x] **T09** — `frontend/src/api/certifications.ts` — typed wrapper for cert list + detail. ✅ 2026-04-08

- [x] **T10** — Generation page (`src/pages/Generate.tsx`): ✅ 2026-04-08
      cert picker (dropdown of verified certs + "custom" option with free-text fallback),
      text area, mode toggle (flashcard / MCQ), Generate button.
      Stream cards into view as SSE deltas arrive.

### Phase 3 — persistence

- [x] **T11** — SQLAlchemy models: `certifications`, `cert_domains`, `decks`, ✅ 2026-04-08
      `source_chunks`, `cards`, `mcq_options`, `card_schedule`, `card_reviews`,
      `exam_sessions`, `exam_answers`, `card_tags`.

- [x] **T12** — Alembic init + first migration. Verify `alembic upgrade head` runs in Docker. ✅ 2026-04-08

- [x] **T13** — Seed script: `backend/seed_certifications.py` — upserts from
      `certifications.json` on startup. Hook into `main.py` lifespan. ✅ 2026-04-08

- [x] **T14** — `POST /decks`, `GET /decks`, `GET /decks/{id}`. ✅ 2026-04-08
      Deck creation accepts either `cert_id` (verified) or `custom_cert_name` (custom).
      Wire generation to persist chunks + cards post-generation.

- [x] **T15** — `PATCH /cards/{id}`, `DELETE /cards/{id}`, `POST /cards/{id}/approve`. ✅ 2026-04-08

- [x] **T16** — Frontend: deck list, deck detail, inline card editor. ✅ 2026-04-08

### Phase 4 — ingestion

- [ ] **T17** — `backend/app/services/chunking.py`: paragraph-aware, ~400 token target.
      Unit test: 2000-word input → all chunks under 500 tokens, no mid-sentence splits.

- [ ] **T18** — `POST /ingest/text`, `POST /ingest/pdf`, `POST /ingest/url`.
      All write to `source_chunks`, trigger background generation.
      For verified certs, pass domain list to generation prompt for tagging.

- [ ] **T19** — `GET /decks/{id}/status` — `{chunks_total, chunks_processed, cards_generated}`.

- [ ] **T20** — Frontend: PDF upload, URL input, progress polling.

### Phase 5 — study mode

- [ ] **T21** — `backend/app/services/sm2.py`: `sm2_update(interval, ease, grade)`.
      Tests: grade < 3 resets interval; ease never below 1.3; progression 1 → 6 → ~15.

- [ ] **T22** — `GET /study/session?deck_id=`, `POST /study/review`.

- [ ] **T23** — `GET /decks/{id}/stats` — due today, streak, total reviewed.
      For verified cert decks: per-domain coverage stats.

- [ ] **T24** — Frontend: flip card, grade buttons, session summary, streak widget.

### Phase 6 — exam mode

- [ ] **T25** — `POST /exam/generate` — generate MCQ pool for a deck.
      For verified certs: generate proportionally across domains per `weight_pct`.
      For custom certs: generate uniformly, tag by AI-detected topic.

- [ ] **T26** — `POST /exam/start`, `POST /exam/answer`, `GET /exam/{id}/report`.
      Report includes per-domain breakdown for verified cert decks.

- [ ] **T27** — Frontend: exam UI (timer, no going back), score report.
      Topic heatmap only shown for verified cert decks (domain weights known).

### Phase 7 — export + deploy

- [ ] **T28** — `GET /decks/{id}/export/anki` via `genanki`.

- [ ] **T29** — `docker-compose.prod.yml`, GitHub Actions CI, Railway + Vercel deploy.
