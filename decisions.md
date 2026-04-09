# Architecture Decision Records

Read this before changing any structural part of the codebase.
These decisions were made deliberately — if you think one should change, flag it
rather than reversing it silently.

---

## ADR-001: No auth in v1

**Decision:** No user accounts, sessions, or `user_id` columns in v1.

**Why:** Auth adds significant complexity (session management, password reset, OAuth flows)
that delays shipping a working study tool. Single-user on a personal deployment.

**Consequence:** No `user_id` FK on any table. When auth is added, a single migration
adds `user_id` to `decks` — everything else cascades from there.

**Do not add:** Any middleware, session checks, or `current_user` dependencies.

---

## ADR-002: Local file storage for uploads in v1

**Decision:** PDFs stored in local `UPLOADS_DIR`, not Cloudflare R2 or S3.

**Why:** External object storage adds credentials, SDK config, and network latency for no
benefit at single-user scale. `UPLOADS_DIR` is env-configurable so the storage backend
is swappable without changing application code.

**Migration path:** Replace the file write in `ingest.py` with R2/S3 when going multi-user.
The rest of the app stores only the file path/key in DB — one-function change.

**Do not add:** boto3, Cloudflare, or S3 dependencies in v1.

---

## ADR-003: card_schedule is separate from card_reviews

**Decision:** Current SM-2 state (`interval`, `ease_factor`, `due_date`) lives in
`card_schedule`. Each review event is appended to `card_reviews`.

**Why:** Different concerns. `card_schedule` is mutable state updated on every review.
`card_reviews` is an append-only log, never updated. Mixing them requires either mutating
history or a `MAX(reviewed_at)` table scan to get current schedule.

**Do not:** Store `interval` or `ease_factor` in `card_reviews`, or derive current
schedule from review history.

---

## ADR-004: MCQ options stored with position, not shuffled at query time

**Decision:** `mcq_options.position` (0–3) stores display order, set once at generation.
Options returned in position order.

**Why:** Shuffling at query time makes the correct answer jump between sessions, which is
confusing during wrong-answer review. Stable positions make exam reports consistent.

**Do not:** Apply `ORDER BY RANDOM()` to options at query time.

---

## ADR-005: Two-tier certification model — verified catalogue + custom free-text

**Decision:** The app ships with a curated `certifications` table (seeded from
`backend/seed/certifications.json`). Each verified cert has official topic domains
and exam weightings in a `cert_domains` child table, plus a `prompt_context` field
injected into the AI generation prompt.

Users can also enter any free-text certification name. In this case `decks.cert_id`
is null and `decks.custom_cert_name` is set. Custom certs get no domain taxonomy,
no topic heatmap, and no weighted exam generation — the AI auto-detects tags from
source text instead.

**Why:** A pure free-text approach (original design) produces unstructured output —
no consistent topic tags, no pass/fail benchmarks, no coverage heatmap. But hardcoding
a fixed enum of certs excludes users on other certifications. The two-tier model gives
structure where we have it and graceful degradation where we don't.

**Consequence — feature availability by deck type:**

| Feature | Verified cert deck | Custom cert deck |
|---|---|---|
| AI prompt enrichment | ✅ via `prompt_context` | ✅ cert name only |
| Topic domain tags on cards | ✅ `cert_domains` FK | ⚠️ AI free-text tags |
| Topic coverage heatmap | ✅ | ❌ not shown |
| Weighted exam generation | ✅ proportional to `weight_pct` | ❌ uniform |
| Pass/fail benchmark | ✅ `pass_score_pct` | ❌ not shown |

**Do not:** Add a `CertificationEnum` in Python — the catalogue lives in the DB, not code.
**Do not:** Require a verified cert to create a deck — the custom path must always work.
**Do not:** Show heatmap or weighted exam UI for custom cert decks — those features
require domain weightings that simply don't exist for custom certs.

---

## ADR-006: cert_domains replaces free-text topic_tags for verified cert decks

**Decision:** The old design had a `topic_tags` table with free-text slugs and a
`card_tags` join table. For verified cert decks, `cert_domains` rows ARE the tags —
`card_tags` now joins `cards` to `cert_domains` directly, not to a separate tags table.

**Why:** Free-text tags produced inconsistent grouping ("delta-lake" vs "delta-lake-ops"
vs "delta-lake-fundamentals" across different generation runs). Binding cards to official
`cert_domains` rows makes topic coverage reporting accurate and consistent.

**For custom cert decks:** The AI still generates free-text `topic_tag` strings on each
card (stored in `cards.custom_topic_tag`), but these are display-only and not used for
weighted exam selection or heatmaps.

**Do not:** Create a separate `topic_tags` table. Use `cert_domains` for verified certs
and `cards.custom_topic_tag` for custom certs.

---

## ADR-007: prompt_context is stored in the DB, not in code

**Decision:** The AI system prompt enrichment for each verified certification is stored
in `certifications.prompt_context` (a text field), not in Python constants or prompt
template files.

**Why:** Cert exam guides change. Topic weightings get updated between versions.
Storing context in the DB means updating a cert's prompt requires a DB update (or a
seed file update + migration), not a code deployment. It also means the generation
service doesn't need to know anything about specific certifications — it just reads
`prompt_context` from whatever cert is linked to the deck.

**Format:** Plain prose, ~100–200 words. Topics listed with percentages. Pass mark.
Question style guidance. See `claude.md` for the canonical example.

**Do not:** Hardcode cert-specific context in `generation.py` or any service file.

---

## ADR-008: services contain business logic, routes are thin

**Decision:** `app/api/*.py` routes validate input, call a service, and return the result.
All business logic lives in `app/services/*.py`.

**Why:** Services are independently testable without spinning up HTTP.

**Pattern:**
```python
# api/study.py — thin
@router.post("/study/review")
async def review_card(req: ReviewRequest, db: Session = Depends(get_db)):
    return study_service.record_review(db, req.card_id, req.grade)

# services/study.py — logic here
def record_review(db: Session, card_id: int, grade: int) -> ReviewResult:
    schedule = db.get(CardSchedule, card_id)
    new_interval, new_ease = sm2_update(schedule.interval, schedule.ease_factor, grade)
    ...
```

**Do not:** Put SM-2 updates, chunking logic, or Claude API calls in route handlers.

---

## ADR-009: Seed data is JSON-driven and upserted on startup

**Decision:** The verified certification catalogue lives in
`backend/seed/certifications.json`. A startup script upserts this data on
`alembic upgrade head` using slug as the idempotency key.

**Why:** The catalogue needs to be version-controlled (reviewable in PRs),
editable without writing SQL, and safe to re-run (upsert, not insert).
Keeping it in JSON rather than a migration means cert content can be updated
independently of schema changes.

**Do not:** Hard-code cert data in a migration file. Migrations are for schema,
seed scripts are for reference data.

---

## ADR-010: App name is Quizine

**Decision:** The product is named **Quizine**. All user-facing strings, the
Python package name, Docker image tag, npm package name, and repo name use `quizine`.

**Why:** Selected after domain/npm availability checks. `quizine.com` and `quizine.app`
are available. No active competing products. The cuisine pun (quiz + cuisine) supports
a coherent brand metaphor — decks are menus, the AI is the chef, study sessions are
sittings.

**Tagline:** *"Knowledge, served fresh."*

**Do not:** Use `certprep`, `CertPrep`, or any prior working title in user-facing strings,
comments, or documentation. Internal code references (variable names, etc.) that
predate this decision can be renamed opportunistically.
