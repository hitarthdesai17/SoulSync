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