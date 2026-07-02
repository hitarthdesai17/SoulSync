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