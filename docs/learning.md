# SoulSync — Learning Log

*One section per completed milestone. Concepts, sources, and real issues hit along the way.*

---

## Milestone 0 — Environment Setup

### What we built
A working FastAPI backend, a Supabase (Postgres + pgvector) database connection, and a React frontend — all successfully talking to each other locally.

### Core concepts learned

**Virtual environments (Python)**
- Isolate a project's dependencies from the global Python install and from other projects
- Created once (`python -m venv venv`), but must be **re-activated every new terminal session** — activation ≠ installation
- 📖 https://docs.python.org/3/library/venv.html

**FastAPI basics**
- `FastAPI()` creates the application instance everything attaches to
- `@app.get("/")`-style decorators define routes
- Auto-generates interactive API docs at `/docs` for free
- 📖 https://fastapi.tiangolo.com/tutorial/first-steps/

**Uvicorn**
- FastAPI is a framework; Uvicorn is the actual server that runs it — separate concerns in Python
- `--reload` auto-restarts the server on code changes (development only)

**Environment variables & secrets**
- `.env` holds real secrets (API keys), never committed to git
- `python-dotenv` + `load_dotenv()` reads `.env` into `os.getenv(...)` — not automatic in Python
- `.gitignore` must explicitly exclude `.env` (but keep `.env.example` as a template)

**Supabase / Postgres / pgvector**
- Supabase bundles Postgres, pgvector (vector search extension), Auth, and Storage in one free-tier account
- pgvector must be manually enabled per-project (Database → Extensions)
- Use the `anon public` key for app code — never a Personal Access Token (that's account-level, far more powerful than the app needs)
- 📖 https://supabase.com/docs/guides/getting-started
- 📖 https://supabase.com/docs/guides/database/extensions/pgvector

**Node.js, npm, Vite, React**
- `npm` is Python's `pip` equivalent for JavaScript
- `node_modules/` is regenerable and gitignored, same role as `venv/`
- Vite is the current standard tool for scaffolding React projects
- 📖 https://vite.dev/guide/

**React fundamentals (first exposure)**
- `useState` — stores data that can change and triggers re-render on update
- `useEffect(() => {...}, [])` — runs code once when a component first mounts; the right place for network calls
- `fetch()` — browser API for making HTTP requests from JavaScript

**CORS (Cross-Origin Resource Sharing)**
- Browsers block JavaScript on one origin (`localhost:5173`) from reading responses from a different origin (`127.0.0.1:8000`) by default — a real security mechanism, not a bug
- Fixed via FastAPI's `CORSMiddleware`, explicitly allowlisting the frontend's origin
- 📖 https://fastapi.tiangolo.com/tutorial/cors/

**Real debugging skills practiced**
- Diagnosing "module not found" vs "editor can't resolve import" as genuinely different problems (runtime vs. editor language server)
- Using `netstat -ano | findstr :PORT` and `tasklist /FI "PID eq ..."` to find and kill stuck/orphaned processes on Windows
- Using browser DevTools Network tab — checking actual Request URL, Response body, and Response Headers instead of trusting a surface-level error message
- Found and fixed a real, subtle typo (`http;//` instead of `http://`) that was masked by what initially looked like a caching or CORS issue — a good lesson in verifying the actual request before assuming the cause

### Honest note
The CORS error was genuinely anticipated (common at this exact integration step), but it was hidden underneath an unrelated typo for most of the debugging session. Real lesson: always verify the *actual* request/response via DevTools before assuming which known issue you're hitting.

---

## Milestone 1 — Bare-bones Chat Loop

### What we built
A real, working chat loop: type a message in React → FastAPI receives it → calls an AI model → reply shown on screen. First genuinely functional piece of SoulSync.

### Core concepts learned

**The Messages API is stateless**
- The AI provider remembers nothing between calls — every relevant piece of conversation must be resent each time
- This is *why* Phase 3's Memory Architecture exists at all — memory is something the app builds, not something the model provides
- 📖 https://docs.claude.com/en/api/messages

**Environment variables must be loaded per-file**
- `load_dotenv()` doesn't apply globally just because it ran somewhere else in the project — it must run in whatever file actually calls `os.getenv()`
- Real bug hit: `conversation_engine.py` tried to read `ANTHROPIC_API_KEY` without ever calling `load_dotenv()` itself, causing a silent `None` and an auth error several layers deep

**API billing is separate from having an account**
- Anthropic's Claude API has no permanent free tier — real credit purchase required
- Found and used a genuinely free alternative (Google Gemini API via Google AI Studio, `google-genai` SDK) as a stand-in during learning
- 📖 https://ai.google.dev/gemini-api/docs/quickstart

**Model-agnostic architecture, proven in practice**
- Swapped the entire AI provider (Claude → Gemini) by only changing the inside of `get_ai_response()` — zero changes needed anywhere else in the app
- Confirms the Phase 3/4 design decision to keep the Conversation Engine provider-independent was correct, not just theoretical

**Pydantic request validation**
- `BaseModel` classes (e.g. `MessageRequest`) define the exact shape of incoming data
- FastAPI validates automatically before your code runs — malformed requests are rejected for free, no manual checking needed

**APIRouter — modular routes**
- Routes split into separate files (`api/messages.py`, etc.) using `APIRouter`, then connected to the main app via `app.include_router(...)`
- Keeps `main.py` from becoming one giant file as the project grows

**React state patterns (new this milestone)**
- Arrays in state are updated immutably: `setMessages(prev => [...prev, newMsg])`, never mutated directly (no `.push()`)
- Controlled components: input `value` bound to state, updated via `onChange` — React state is the single source of truth for form inputs
- `async`/`await` inside event handlers (not just `useEffect`) for on-demand requests, e.g. triggered by a button click
- Two-step UI update pattern: show the user's message immediately, then update again once the AI reply arrives — deliberate responsiveness, not just correctness

### Honest note
Companion display name was changed to "HitMan" in the UI at this stage — currently cosmetic only, not yet wired into an actual personality system. That connection begins in Milestone 2.

---

## Milestone 2 — Companion & Personality Core

### What we built
A real `companions` database table, backend logic to create/fetch companions, a `build_system_prompt` function that turns structured data into an actual AI instruction, a companion-creation UI in React, and a working proof that a defined personality genuinely shapes the AI's tone and behavior in conversation.

### Core concepts learned

**Relational vs. document databases — and why "tabular" doesn't mean "no free text"**
- A column can hold long free text just fine; what defines "relational" is that every row shares the same defined structure, not that field contents are short/simple
- `jsonb` columns (like `core_traits`) give NoSQL-style flexibility *within* a relational table, for the one field that genuinely varies per-record — a deliberate hybrid, not a workaround

**Context windows are a real limit — but retrieval is the actual fix, not the backstory field**
- Every AI model has a hard token cap per request; naively sending all accumulated data would eventually break
- A single companion's Core Identity (name, backstory, style) is small and safely sent in full every time — the real risk was always long-term accumulated memory, which Milestone 4's retrieval design already accounts for

**Prompting/RAG vs. fine-tuning an LLM — genuinely different things**
- What we're building never touches a model's internal weights — we just control what text gets sent before each response (system prompt + retrieved context)
- Fine-tuning means retraining internal parameters on a custom dataset — real compute cost, real ML engineering, a different undertaking entirely
- Prompting + retrieval alone is sufficient for a genuinely good MVP; fine-tuning is a legitimate *future* optimization, not a requirement

**Database schema design**
- `uuid` primary keys (safer than sequential integer IDs for anything potentially public-facing)
- `not null` constraints match what's actually required at the application layer (Pydantic schema mirrors the DB's requirements)
- 📖 https://www.postgresql.org/docs/current/datatype.html

**Migrations as a concept**
- SQL run directly in Supabase's dashboard doesn't automatically exist anywhere else — `.sql` files saved in the repo are a *record* of what was run, not something that executes on its own
- Numbered migration files (`001_...`, `002_...`) are the standard way real projects track database schema history alongside code

**Row Level Security (RLS) — a real, live gotcha**
- Supabase enables RLS by default on new tables: no read/write is allowed until explicit policies are set, even with valid credentials
- Hit a real `postgrest.exceptions.APIError: new row violates row-level security policy` error, diagnosed via the actual traceback rather than guesswork
- Temporarily disabled for solo MVP development — explicitly documented as a decision that must be revisited before multi-user/deployment
- 📖 https://supabase.com/docs/guides/database/postgres/row-level-security

**Supabase Python client (real usage, not just theory)**
- `.table(...).insert({...}).execute()` and `.table(...).select("*").eq(...).single().execute()` — real CRUD operations without writing raw SQL from the backend
- 📖 https://supabase.com/docs/reference/python/insert

**Pydantic: `.get()` vs. direct key access, and truthy/falsy defaults**
- `.get(key, default)` only falls back on a *missing* key — not on a key that exists but holds `None` — a real bug caught by tracing through code manually
- Fixed using `x or default`, which catches both missing and empty/`None` values — a genuinely reusable pattern
- Practiced tracing code by hand (manual substitution) and using Python's interactive REPL to verify behavior directly, rather than guessing

**System prompts, for real this time**
- Gemini's `types.GenerateContentConfig(system_instruction=...)` is the actual mechanism connecting a structured personality to real model behavior
- Confirmed working: a defined personality (name, relationship, backstory, speaking style, traits) produced consistent, in-character tone across multiple real messages — including natural, unscripted stylistic choices (e.g. code-mixed phrasing) fitting the described character
- 📖 https://ai.google.dev/gemini-api/docs/generate-content/get-started

**New React patterns**
- Conditional rendering: `if (!companion) { return (...) }` — same component, different screens, based on state
- Object state updates via spread: `setForm({ ...form, name: value })` — update one field, preserve the rest
- Connecting two flows via shared state: the ID returned from creating a companion becomes the identifier used in every subsequent chat request

### Honest note
Conversation currently *feels* coherent turn-to-turn, but this is mostly the model inferring flow from a consistent personality — the backend isn't yet structurally passing prior conversation turns into each request. That's genuinely Milestone 3's job (Short-Term Memory), not something this milestone actually solved yet, despite how it looks in testing.

Also decided to defer frontend visual design (layout, typography, formatting) to a dedicated checkpoint (Milestone 4.5) rather than polishing incrementally — avoids re-styling the same components repeatedly as functionality changes underneath them.

---

## Milestone 3 — Short-Term Memory

### What we built
A real `messages` table storing every turn of every conversation, backend logic to persist and retrieve it, and a reshaped AI call that actually sends real conversation history — not just a single message — to the model each time.

### Core concepts learned

**Foreign keys — real relational structure**
- `companion_id uuid references companions(id)` links the `messages` table to `companions`, and Postgres enforces that every message's companion_id must correspond to an actual existing companion
- This is the concrete answer to "why use a relational database" from earlier — separate tables, linked by reference, instead of duplicating companion data into every message row

**Deliberate history limits, tied to context window awareness**
- `get_conversation_history` caps at the most recent 20 messages for now — a conscious, temporary simplification, not the final answer
- Full-history retrieval via embeddings/relevance (not just recency) is Milestone 4's actual job

**Reshaping data for a specific API's expected format**
- Gemini's `contents` parameter expects a list of `{"role": ..., "parts": [{"text": ...}]}` objects — a real structural requirement, different from the single-string version used in Milestones 1-2
- Learned Gemini's role naming differs from Claude's (`model` vs `assistant`) — a good reminder that provider-agnostic design still requires small adapter logic per provider, even if the core function signature stays the same

**Order of operations matters, and was deliberate**
- Store user message → fetch history (now including that message) → call AI → store AI's reply
- This ordering is what makes the *next* request's history genuinely complete, not delayed by one turn

**Hallucination, seen directly, not just as a design principle**
- The AI invented specific unstated details ("Mrs. Sharma," a specific paper-plane incident) despite genuine short-term memory correctly recalling the user's actual name across turns
- This is expected default LLM behavior (filling vague recollection with vivid, plausible specifics) — not a bug in the memory system just built
- Directly confirms *why* Phase 3's anti-hallucination rule ("no match found → ask, never guess or invent") exists as a real design requirement, not an abstract concern — Milestone 4's strength/confidence system is what will structurally address this
- Flagged as a genuine trust/safety consideration specific to companions modeled on real people — invented "memories" of someone real could feel hurtful, not just charming

### Honest note
Short-term memory is genuinely real and working now. Hallucinated specificity is a known, expected limitation at this stage, not a regression — it's the concrete, lived reason Milestone 4 (confidence-aware long-term memory) matters as a safety feature, not only a functionality one.

---

## Milestone 4 — Long-Term Memory: Decay & Reinforcement

### What we built
A real `memories` table with vector embeddings, a Postgres similarity-search function (`match_memories`), and backend logic that retrieves relevant past memories, injects them into the system prompt with a confidence score, and strengthens memories that actually get used — while letting unused ones fade over time.

### Core concepts learned

**`CREATE OR REPLACE FUNCTION` has a real limit**
- Postgres allows replacing a function's body freely, but not changing its declared return shape (`RETURNS TABLE(...)`) — it refuses rather than silently guess how to reconcile old and new row types
- Real error hit: `42P13: cannot change return type of existing function`, fixed by adding an explicit `DROP FUNCTION IF EXISTS ...` (matching the exact old argument types) before the `CREATE OR REPLACE`
- Safe here because the function was pure logic with no dependents (no views built on top of it) — dropping and recreating is not always this risk-free in a bigger system

**pgvector cosine similarity, `match_threshold`, and confidence in practice**
- `match_memories` uses the `<=>` operator (cosine distance) to rank stored memory embeddings against a live query embedding
- `match_threshold=0.3` and `match_count=5` are tunable filters — not hard requirements, and worth revisiting once real usage patterns exist

**Exponential decay, not linear**
- `strength * exp(-decay_rate * days_elapsed)` — memories fade smoothly and continuously rather than dropping off a cliff at a fixed day count
- `reinforce_memory()` resets the decay clock by updating `last_reinforced_at` and nudging `strength` up (capped at 1.0) — decay and reinforcement are two independent, composable mechanisms, not one combined formula

**A capped value can hide whether logic is actually running**
- Spent real debugging time confused about why `strength` "wasn't increasing" after reinforcement — the true cause was that the memory was already at the `1.0` ceiling, so reinforcement was firing correctly but had no visible headroom
- Real lesson: to test a capped/clamped value meaningfully, deliberately move it away from the boundary first

**Gemini's "thinking" tokens can silently eat the whole response**
- `gemini-2.5-flash` has model-internal "thinking" enabled by default; without a token/thinking budget set, it can spend its entire output allowance on internal reasoning and return `finish_reason: STOP` with genuinely empty visible text — not a truncation, not a safety block, just nothing
- Diagnosed by directly inspecting `response.candidates[0]` rather than guessing from `response.text` alone
- Fixed (temporarily) with `thinking_config=types.ThinkingConfig(thinking_budget=0)`, and hardened the call site with `response.text or <fallback string>` so a `None`/empty reply can never again crash `store_message()` on a `NOT NULL` constraint

**`.env` values only load once per process, not per `--reload`**
- Uvicorn's `--reload` restarts your *code*, but `load_dotenv()` doesn't get a fresh run just because files changed — a full stop/restart of the process is required to pick up a changed `.env` value (learned the hard way while rotating API keys)

**Free-tier quotas are real, and look identical to a code bug from the outside**
- A `429 RESOURCE_EXHAUSTED` (daily request quota) produced the *exact same symptom* — empty/fallback replies — as the thinking-budget bug above, which cost real debugging time chasing the wrong cause
- Also learned free-tier quotas are scoped per Google Cloud *project*, not per API key — generating a second key under the same account/default project shares the same exhausted quota

**Model deprecation is an active, ongoing risk, not a one-time setup concern**
- `gemini-2.5-flash` and then `gemini-2.5-flash-lite` were both fully shut down (`404 NOT_FOUND`, not just deprecated) mid-project, requiring a real migration under time pressure
- Real lesson: hardcoding a specific model string is a genuine maintenance liability — worth knowing this is an active, industry-wide pattern (multiple providers churn model names on a matter of months), not specific to this project

**Switched providers again: Gemini → Groq**
- Given repeated quota exhaustion and model churn, migrated `conversation_engine.py` to Groq (OpenAI-compatible chat API, free tier, no credit card)
- Confirmed the provider-agnostic design (first proven in Milestone 1) held up a second time — only `conversation_engine.py`'s internals changed; `messages.py`, `memory.py`, and every other file were untouched
- Real adapter difference: Groq's role naming (`assistant`, not `model`) required the same kind of small role-mapping logic as the original Claude→Gemini swap — confirms this is a *pattern* to expect at every provider boundary, not a one-off quirk

**A real, separate bug hiding behind all of the above: `.order("created_at")` defaults ascending**
- `get_conversation_history()` was silently returning the *oldest* 20 messages ever exchanged with a companion, not the most recent 20, once a companion passed 20 total messages
- Symptom looked like model hallucination (companion said "stranger," "haven't seen you in a while" to an active companion) — but tracing the actual code showed the model was correctly reasoning from genuinely stale data it had been handed, not inventing anything
- Fixed with `.order("created_at", desc=True)` + `.limit(limit)` + `reversed(...)` in Python — real reminder that "the model is hallucinating" should be checked against "what data did the model actually receive" before assuming it's a prompting problem

### Honest note
This milestone took far longer than the actual memory-decay logic warranted, because of a stack of unrelated infrastructure issues (SQL function replacement, Gemini's thinking-token quirk, free-tier quota exhaustion, and Gemini's model deprecations) that surfaced one after another. Real lesson: when the same symptom (empty/fallback AI replies) kept recurring, it had at least three genuinely different root causes over the course of this milestone — worth remembering that recurring symptoms don't always share a recurring cause.

---

## Milestone 4.5 — Prompt Tuning & Frontend Design Pass

### What we built
A fix for the model's tendency to over-repeat nicknames/pet-names every turn, and a first real visual identity for the app — moving off unstyled HTML for the first time since Milestone 0.

### Core concepts learned

**Over-anchoring is a prompting gap, not a logic bug**
- The model had no instruction on *how often* to use a nickname once it appeared in memory-injected context — LLMs left without an explicit frequency/variation instruction tend to over-signal "I remember this about you" on every turn
- Fixed by adding an explicit instruction to `build_system_prompt()` ("vary phrasing, don't repeat nicknames every message") rather than touching any retrieval or memory logic — confirms that not every behavioral quirk needs a code fix

**Design tokens before code**
- Worked through a real design-token system (named colors, paired typefaces, one deliberate "signature" element) before writing any CSS — grounded in the app's actual subject (memory, presence, companionship) instead of a generic template look
- Chose a dusk-indigo/warm-amber palette specifically to avoid the common AI-generated-design defaults (cream+terracotta serif, near-black+neon accent)

**CSS custom properties (`:root { --var: ... }`)**
- Centralizing colors as CSS variables means the whole palette can be adjusted from one place later, rather than hunting through every component

**`prefers-reduced-motion` as a real accessibility baseline**
- The companion avatar's ambient "breathing" glow animation is wrapped in a `@media (prefers-reduced-motion: reduce)` override — a small, easy-to-forget detail that matters for real users, not just a nice-to-have

### Honest note
The visual design pass is intentionally a first pass, not a final one — deliberately kept restrained (one signature animation, no more) rather than over-decorated. Real follow-up ideas (surfacing memory-confidence visually, typing/loading states, empty-state design) were captured for a later revisit rather than attempted all at once, to avoid scope creep on what was meant to be a focused milestone.