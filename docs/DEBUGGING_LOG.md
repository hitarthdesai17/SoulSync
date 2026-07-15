# SoulSync — Debugging Log
*Every real bug hit so far: symptom, root cause, fix, lesson. Chronological.*

| # | Symptom | Root Cause | Fix | Lesson |
|---|---|---|---|---|
| 1 | `uvicorn : not recognized` | venv not activated in *that specific terminal* (new terminal ≠ old terminal's state) | `cd backend` → `venv\Scripts\Activate.ps1` before every command | Venv activation is per-terminal-session, not project-wide or persistent |
| 2 | VS Code shows red squiggly under `import supabase` | Editor's Pylance language server pointed at wrong Python interpreter — cosmetic only, not a real crash | `Ctrl+Shift+P` → "Python: Select Interpreter" → pick venv's `python.exe` | Editor warnings ≠ runtime errors; check if the server actually crashed before trusting an underline |
| 3 | React showed `"Unexpected token '<'... not valid JSON"` | Multi-layered: (a) initially a genuine stale-process/cache red herring, (b) real cause was a typo — `http;//` instead of `http://` in `fetch()`, silently routed to Vite's own fallback HTML | Diagnosed via DevTools Network tab → checked actual **Request URL**, not just the error text or response body | Trust the browser's actual request/response details over an error message's surface wording; a symptom can hide a completely different real cause underneath |
| 4 | Orphaned process stuck on port 8000, serving stale content | An old uvicorn instance never properly stopped, kept the port bound | `netstat -ano | findstr :8000` → `tasklist /FI "PID eq X"` → `taskkill /PID X /F` | Real, reusable skill: finding and killing stuck processes by port on Windows |
| 5 | `Failed to fetch` (after typo above was fixed) | Genuine CORS block — browser refusing cross-origin read between `localhost:5173` and `127.0.0.1:8000` | Added `CORSMiddleware` to FastAPI with explicit `allow_origins` | Browsers enforce same-origin policy by default; the server must explicitly opt in to being read cross-origin |
| 6 | `TypeError: Could not resolve authentication method` (Anthropic) | `load_dotenv()` was called in `config.py` but never in `conversation_engine.py` — env vars aren't globally shared just because one file loaded them | Added `load_dotenv()` directly in the file that needed `os.getenv(...)` | `load_dotenv()` must run in whatever file actually reads the variable — it doesn't propagate across files automatically |
| 7 | `anthropic.BadRequestError: credit balance too low` | Anthropic API has no free tier; account had $0 usable credit | Switched to Google Gemini API (genuinely free tier) as a swap-in provider | Proved the model-agnostic Conversation Engine design in practice — swapped providers with minimal code change |
| 8 | `postgrest.exceptions.APIError: new row violates row-level security policy` | Supabase enables RLS by default on new tables — blocks all reads/writes until explicit policies exist | `alter table ... disable row level security;` (documented as intentional solo-MVP tech debt) | RLS is a deliberate secure-by-default behavior, not a bug; must be revisited before multi-user/deployment |
| 9 | Prompt showed literal `Backstory: None` | `.get("backstory", "Not specified")` only falls back on a *missing* key, not a key present with value `None` | Changed to `companion.get("backstory") or "Not specified"` | `.get(key, default)` ≠ "handle empty/None" — `or` catches both missing and falsy values |
| 10 | `IndentationError: unexpected indent` in REPL | Multi-line code pasted directly into the interactive REPL — REPL's line editor mishandled the paste | Wrote a real throwaway script file (`test_x.py`) and ran it directly instead | REPL is great for one-liners; anything multi-line is more reliable as an actual script file |
| 11 | `ModuleNotFoundError: No module named 'app'` | Code was run from VS Code's Python Interactive Window (different working context), not the terminal REPL from inside `backend/` | Ran `python` from the actual terminal, `cd`'d into `backend/` first | Where code is "run from" affects what imports can resolve — terminal location matters, not just venv activation |
| 12 | Duplicate near-identical rows in `memories` table | Re-ran the same test script/data multiple times during debugging | Manually deleted duplicate rows in Supabase Table Editor | Repeated test runs accumulate real data — worth cleaning up before judging retrieval quality |
| 13 | `TypeError: fromisoformat: argument must be str` | `match_memories` Postgres function's `RETURNS TABLE` never included `last_reinforced_at`/`created_at`, so Python received `None` for both | Updated the SQL function to return both columns (migration 006) | A function's declared return columns and its actual `SELECT` list must match exactly — silently missing columns show up as `None` downstream, not a SQL error |
| 14 (open) | `strength` shows `1` after reinforcement; unclear if `store_memory` is firing for every message | Likely expected (`min(1.0, 1.0+0.3)` stays capped at 1.0) — but `store_memory` actually firing is unconfirmed | In progress: checking `last_reinforced_at` timestamp directly, and verifying `send_message()`'s actual current code calls `store_memory` | Don't conclude "broken" from a capped value alone — check the *other* signal (timestamp) designed to reveal real change |

## Cross-cutting lessons (apply going forward)
- **Always check the actual traceback/terminal output before guessing** — nearly every real bug here was correctly diagnosed only once the real error text was read, not before.
- **A working response doesn't guarantee every side-effect fired** — `/message` can return 200 while a secondary step (like `store_memory`) silently fails or was never called; verify each piece independently (database rows, not just the reply text).
- **Every "fix" here was verified in the actual database/browser, not just assumed from code review** — Table Editor and DevTools were the real sources of truth throughout, not confidence in the code alone.

# SoulSync — Milestone 4 / 4.5 Debugging Session Summary

*A chronological record of every real problem hit while finishing Milestone 4 (memory decay/reinforcement) and Milestone 4.5 (prompt tuning + frontend design), how each was diagnosed, and what it taught us.*

---

## 1. Postgres: `cannot change return type of existing function`

**Symptom:** Running the migration to add `last_reinforced_at`/`created_at` to `match_memories`'s return columns failed with:
```
ERROR: 42P13: cannot change return type of existing function
DETAIL: Row type defined by OUT parameters is different.
```

**Root cause:** `CREATE OR REPLACE FUNCTION` can update a function's *body* freely, but Postgres refuses to change its declared `RETURNS TABLE(...)` shape — it won't guess how to reconcile the old and new row types.

**Fix:** Added an explicit `DROP FUNCTION IF EXISTS match_memories(vector, uuid, double precision, integer);` (matching the exact argument types from the error) before the `CREATE OR REPLACE FUNCTION`.

**Lesson:** Adding columns to a Postgres function's return signature isn't a pure "replace" — it requires an explicit drop first. Safe to do when nothing else depends on the function's exact shape (no views built on top of it, in this case).

---

## 2. Memory `strength` "not increasing" after reinforcement

**Symptom:** After a successful chat exchange that should have retrieved and reinforced a memory, its `strength` value in Supabase still read `1`.

**Root cause:** `reinforce_memory()` was actually firing correctly — but the memory was already at its ceiling (`strength` capped at `1.0`), so there was no visible headroom left to show the increase.

**Debug approach:** Manually lowered the memory's `strength` to `0.5` in Supabase, resent the same test message, and confirmed it moved to `0.8` (0.5 + 0.3) with `last_reinforced_at` updating — proving the logic worked all along.

**Lesson:** A capped/clamped value can silently mask whether logic is actually running. To test something with a ceiling, deliberately move the value away from that ceiling first.

---

## 3. `null value in column "content"` — crash storing the AI's reply

**Symptom:**
```
postgrest.exceptions.APIError: null value in column "content" of relation "messages" violates not-null constraint
```

**Root cause:** `get_ai_response()` returned `None` in some cases, and that `None` was passed straight to `store_message()`, which hit a `NOT NULL` constraint on the `messages` table.

**Fix:** Added a fallback in `conversation_engine.py`: `return response.text or "Sorry, I got a bit lost there — could you say that again?"` — ensuring the function can never return `None` to its caller.

**Lesson:** Any function whose output gets persisted to a `NOT NULL` column needs a guaranteed non-null return value — an external API returning something unexpected shouldn't be able to crash the request pipeline.

---

## 4. Gemini returning genuinely empty responses (`finish_reason: STOP`, no text)

**Symptom:** Innocuous messages ("How are you doing?", "What's your favorite color?") kept triggering the fallback message, with no crash and no obvious error.

**Debug approach:** Added temporary `print(response.candidates[0].finish_reason)` and `print(response.candidates[0])` to inspect the raw response. Found `finish_reason: STOP` (not `MAX_TOKENS`, not a safety block) alongside a `Content(role='model')` object with **no `parts` at all** — genuinely empty output.

**Root cause:** `gemini-2.5-flash` has "thinking" enabled by default. Without a thinking-token budget explicitly set, the model can spend its output budget on internal reasoning and finish successfully having never produced visible text.

**Fix:** Set `thinking_config=types.ThinkingConfig(thinking_budget=0)` in `GenerateContentConfig`, telling the model to skip internal reasoning and go straight to a visible reply.

**Lesson:** `finish_reason: STOP` does not guarantee non-empty output. When debugging "empty response" issues, inspect the full candidate object (including `parts`), not just `response.text`.

---

## 5. `429 RESOURCE_EXHAUSTED` — Gemini free-tier quota

**Symptom:** After extensive testing, requests started failing with:
```
google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED... limit: 20, model: gemini-2.5-flash
```

**Root cause:** Gemini's free tier caps `gemini-2.5-flash` at 20 requests/day. This had been silently approaching its ceiling for a while — and its *symptoms* (empty/fallback replies before the hard 429) looked identical to the thinking-budget bug above, causing real confusion about which bug was actually being observed.

**Fix (short-term):** Waited for quota reset / attempted a second API key.

**Lesson:** Two entirely different root causes (a model config quirk and a rate limit) can produce indistinguishable symptoms. When a "fixed" bug seems to resurface, verify you're not actually looking at a *different* problem with the same visible signature — check the actual error/response object, don't assume.

---

## 6. Second API key still hit the same quota

**Symptom:** Generated a second Gemini API key (same Google account) hoping for a fresh quota — still got `429`.

**Root cause:** Free-tier quota in Google AI Studio is scoped per **Google Cloud project**, not per API key. A new key created under the same account, without explicitly selecting a distinct new project, lands in the same "Default Gemini Project" and shares the same exhausted quota pool.

**Fix:** Switched to a genuinely different Google account to get an independent project/quota.

**Lesson:** "Generate a new key" ≠ "get a new quota." The quota boundary is the project, not the credential.

---

## 7. `gemini-2.5-flash` and then `gemini-2.5-flash-lite` — model shutdowns (`404 NOT_FOUND`)

**Symptom:**
```
404 NOT_FOUND. This model models/gemini-2.5-flash is no longer available.
```
...and then the same error for `gemini-2.5-flash-lite` shortly after switching to it.

**Root cause:** Google has been rapidly deprecating and fully shutting down Gemini model generations throughout 2026 (2.0 Flash retired June 1, 2.5 Flash retired around the same period) — not a soft deprecation, a hard 404 once shut down.

**Fix (attempted):** Tried `gemini-3.5-flash` next, which hit a separate `503 UNAVAILABLE` (server-side high demand) — ultimately leading to the decision to leave the Gemini ecosystem entirely for this project.

**Lesson:** Hardcoding a specific model ID is a real, ongoing maintenance liability, not a one-time setup decision — some providers churn model availability on a timescale of months. Worth designing for (config-driven model names, awareness of provider deprecation pages) in any longer-lived project.

---

## 8. Conversation history returning the *oldest* messages, not the most recent

**Symptom:** A companion described as "closest friend" responded to a normal message as if the user were a stranger who'd vanished for a long time — despite an active, ongoing conversation.

**Debug approach:** Initially suspected model hallucination (a known behavior pattern from Milestone 3). Traced the actual code path instead of assuming, and read `get_conversation_history()` directly:
```python
.order("created_at").limit(limit)
```

**Root cause:** `.order("created_at")` defaults to **ascending** order. Combined with `.limit(20)`, this returned the **oldest 20 messages ever exchanged** with that companion (once it had more than 20 total messages) — not the most recent 20. The model was reasoning correctly from genuinely stale data; it wasn't hallucinating at all.

**Fix:**
```python
.order("created_at", desc=True).limit(limit)
```
then `reversed(result.data)` in Python, since Gemini/Groq both expect chronological (oldest-to-newest) order in the `contents`/`messages` list.

**Lesson:** A model producing an oddly-confident wrong answer should first be checked against *what data it was actually given* — not assumed to be an inherent LLM limitation. This bug had been silently active since the very first time any companion crossed 20 stored messages, well before it was ever noticed.

---

## 9. Provider migration: Gemini → (briefly considered Claude) → Groq

**Context:** After repeated quota exhaustion and model deprecation churn, decided to leave Gemini. Considered Claude (best conversational quality, but no free tier — real cost). Ultimately chose **Groq** (free tier, no credit card, OpenAI-compatible API, high throughput).

**What changed:** Only `conversation_engine.py`'s internals — confirmed by grep across the entire backend that no other file imported `google.genai` anywhere.

**Real adapter detail:** Groq (like Claude before it) uses `"assistant"` for AI-turn roles, while the app's database stores them as `"model"` (a leftover from the original Gemini integration) — required the same small role-mapping logic (`"assistant" if msg["role"] == "model" else "user"`) seen at the very first provider swap in Milestone 1.

**Lesson:** The provider-agnostic design decision from Milestone 1 held up under real pressure a second time — proof that the original architecture choice was sound, not just theoretical.

---

## 10. Minor: duplicate import in `messages.py`

**Symptom:** None (harmless) — just noticed on code review.

**Detail:**
```python
from app.services.memory import store_message, get_conversation_history, store_memory, get_relevant_memories
...
from app.services.memory import store_message, get_conversation_history, store_memory, get_relevant_memories, reinforce_memory
```
The second line re-imports everything the first line already did, plus `reinforce_memory`.

**Lesson:** Small repo-hygiene items are worth flagging even when they don't cause bugs — cheap to fix, and they accumulate in a growing codebase.

---

## Overall theme

Most of this session's real time went into **infrastructure and external-service issues** (Postgres function semantics, Gemini's thinking-token behavior, free-tier quota scoping, and rapid model deprecation) rather than the actual memory-decay logic, which itself was correct on the first real test. Several of these problems shared near-identical symptoms (empty/fallback AI replies) with entirely different root causes — a good reminder that a recurring symptom doesn't imply a recurring cause, and that tracing the actual code path or raw API response is more reliable than pattern-matching to "this looks like the bug from before."

# SoulSync — Milestone 4 / 4.5 Debugging Session Summary

*A chronological record of every real problem hit while finishing Milestone 4 (memory decay/reinforcement) and Milestone 4.5 (prompt tuning + frontend design), how each was diagnosed, and what it taught us.*

---

## 1. Postgres: `cannot change return type of existing function`

**Symptom:** Running the migration to add `last_reinforced_at`/`created_at` to `match_memories`'s return columns failed with:
```
ERROR: 42P13: cannot change return type of existing function
DETAIL: Row type defined by OUT parameters is different.
```

**Root cause:** `CREATE OR REPLACE FUNCTION` can update a function's *body* freely, but Postgres refuses to change its declared `RETURNS TABLE(...)` shape — it won't guess how to reconcile the old and new row types.

**Fix:** Added an explicit `DROP FUNCTION IF EXISTS match_memories(vector, uuid, double precision, integer);` (matching the exact argument types from the error) before the `CREATE OR REPLACE FUNCTION`.

**Lesson:** Adding columns to a Postgres function's return signature isn't a pure "replace" — it requires an explicit drop first. Safe to do when nothing else depends on the function's exact shape (no views built on top of it, in this case).

---

## 2. Memory `strength` "not increasing" after reinforcement

**Symptom:** After a successful chat exchange that should have retrieved and reinforced a memory, its `strength` value in Supabase still read `1`.

**Root cause:** `reinforce_memory()` was actually firing correctly — but the memory was already at its ceiling (`strength` capped at `1.0`), so there was no visible headroom left to show the increase.

**Debug approach:** Manually lowered the memory's `strength` to `0.5` in Supabase, resent the same test message, and confirmed it moved to `0.8` (0.5 + 0.3) with `last_reinforced_at` updating — proving the logic worked all along.

**Lesson:** A capped/clamped value can silently mask whether logic is actually running. To test something with a ceiling, deliberately move the value away from that ceiling first.

---

## 3. `null value in column "content"` — crash storing the AI's reply

**Symptom:**
```
postgrest.exceptions.APIError: null value in column "content" of relation "messages" violates not-null constraint
```

**Root cause:** `get_ai_response()` returned `None` in some cases, and that `None` was passed straight to `store_message()`, which hit a `NOT NULL` constraint on the `messages` table.

**Fix:** Added a fallback in `conversation_engine.py`: `return response.text or "Sorry, I got a bit lost there — could you say that again?"` — ensuring the function can never return `None` to its caller.

**Lesson:** Any function whose output gets persisted to a `NOT NULL` column needs a guaranteed non-null return value — an external API returning something unexpected shouldn't be able to crash the request pipeline.

---

## 4. Gemini returning genuinely empty responses (`finish_reason: STOP`, no text)

**Symptom:** Innocuous messages ("How are you doing?", "What's your favorite color?") kept triggering the fallback message, with no crash and no obvious error.

**Debug approach:** Added temporary `print(response.candidates[0].finish_reason)` and `print(response.candidates[0])` to inspect the raw response. Found `finish_reason: STOP` (not `MAX_TOKENS`, not a safety block) alongside a `Content(role='model')` object with **no `parts` at all** — genuinely empty output.

**Root cause:** `gemini-2.5-flash` has "thinking" enabled by default. Without a thinking-token budget explicitly set, the model can spend its output budget on internal reasoning and finish successfully having never produced visible text.

**Fix:** Set `thinking_config=types.ThinkingConfig(thinking_budget=0)` in `GenerateContentConfig`, telling the model to skip internal reasoning and go straight to a visible reply.

**Lesson:** `finish_reason: STOP` does not guarantee non-empty output. When debugging "empty response" issues, inspect the full candidate object (including `parts`), not just `response.text`.

---

## 5. `429 RESOURCE_EXHAUSTED` — Gemini free-tier quota

**Symptom:** After extensive testing, requests started failing with:
```
google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED... limit: 20, model: gemini-2.5-flash
```

**Root cause:** Gemini's free tier caps `gemini-2.5-flash` at 20 requests/day. This had been silently approaching its ceiling for a while — and its *symptoms* (empty/fallback replies before the hard 429) looked identical to the thinking-budget bug above, causing real confusion about which bug was actually being observed.

**Fix (short-term):** Waited for quota reset / attempted a second API key.

**Lesson:** Two entirely different root causes (a model config quirk and a rate limit) can produce indistinguishable symptoms. When a "fixed" bug seems to resurface, verify you're not actually looking at a *different* problem with the same visible signature — check the actual error/response object, don't assume.

---

## 6. Second API key still hit the same quota

**Symptom:** Generated a second Gemini API key (same Google account) hoping for a fresh quota — still got `429`.

**Root cause:** Free-tier quota in Google AI Studio is scoped per **Google Cloud project**, not per API key. A new key created under the same account, without explicitly selecting a distinct new project, lands in the same "Default Gemini Project" and shares the same exhausted quota pool.

**Fix:** Switched to a genuinely different Google account to get an independent project/quota.

**Lesson:** "Generate a new key" ≠ "get a new quota." The quota boundary is the project, not the credential.

---

## 7. `gemini-2.5-flash` and then `gemini-2.5-flash-lite` — model shutdowns (`404 NOT_FOUND`)

**Symptom:**
```
404 NOT_FOUND. This model models/gemini-2.5-flash is no longer available.
```
...and then the same error for `gemini-2.5-flash-lite` shortly after switching to it.

**Root cause:** Google has been rapidly deprecating and fully shutting down Gemini model generations throughout 2026 (2.0 Flash retired June 1, 2.5 Flash retired around the same period) — not a soft deprecation, a hard 404 once shut down.

**Fix (attempted):** Tried `gemini-3.5-flash` next, which hit a separate `503 UNAVAILABLE` (server-side high demand) — ultimately leading to the decision to leave the Gemini ecosystem entirely for this project.

**Lesson:** Hardcoding a specific model ID is a real, ongoing maintenance liability, not a one-time setup decision — some providers churn model availability on a timescale of months. Worth designing for (config-driven model names, awareness of provider deprecation pages) in any longer-lived project.

---

## 8. Conversation history returning the *oldest* messages, not the most recent

**Symptom:** A companion described as "closest friend" responded to a normal message as if the user were a stranger who'd vanished for a long time — despite an active, ongoing conversation.

**Debug approach:** Initially suspected model hallucination (a known behavior pattern from Milestone 3). Traced the actual code path instead of assuming, and read `get_conversation_history()` directly:
```python
.order("created_at").limit(limit)
```

**Root cause:** `.order("created_at")` defaults to **ascending** order. Combined with `.limit(20)`, this returned the **oldest 20 messages ever exchanged** with that companion (once it had more than 20 total messages) — not the most recent 20. The model was reasoning correctly from genuinely stale data; it wasn't hallucinating at all.

**Fix:**
```python
.order("created_at", desc=True).limit(limit)
```
then `reversed(result.data)` in Python, since Gemini/Groq both expect chronological (oldest-to-newest) order in the `contents`/`messages` list.

**Lesson:** A model producing an oddly-confident wrong answer should first be checked against *what data it was actually given* — not assumed to be an inherent LLM limitation. This bug had been silently active since the very first time any companion crossed 20 stored messages, well before it was ever noticed.

---

## 9. Provider migration: Gemini → (briefly considered Claude) → Groq

**Context:** After repeated quota exhaustion and model deprecation churn, decided to leave Gemini. Considered Claude (best conversational quality, but no free tier — real cost). Ultimately chose **Groq** (free tier, no credit card, OpenAI-compatible API, high throughput).

**What changed:** Only `conversation_engine.py`'s internals — confirmed by grep across the entire backend that no other file imported `google.genai` anywhere.

**Real adapter detail:** Groq (like Claude before it) uses `"assistant"` for AI-turn roles, while the app's database stores them as `"model"` (a leftover from the original Gemini integration) — required the same small role-mapping logic (`"assistant" if msg["role"] == "model" else "user"`) seen at the very first provider swap in Milestone 1.

**Lesson:** The provider-agnostic design decision from Milestone 1 held up under real pressure a second time — proof that the original architecture choice was sound, not just theoretical.

---

## 10. Minor: duplicate import in `messages.py`

**Symptom:** None (harmless) — just noticed on code review.

**Detail:**
```python
from app.services.memory import store_message, get_conversation_history, store_memory, get_relevant_memories
...
from app.services.memory import store_message, get_conversation_history, store_memory, get_relevant_memories, reinforce_memory
```
The second line re-imports everything the first line already did, plus `reinforce_memory`.

**Lesson:** Small repo-hygiene items are worth flagging even when they don't cause bugs — cheap to fix, and they accumulate in a growing codebase.

---

## Overall theme

Most of this session's real time went into **infrastructure and external-service issues** (Postgres function semantics, Gemini's thinking-token behavior, free-tier quota scoping, and rapid model deprecation) rather than the actual memory-decay logic, which itself was correct on the first real test. Several of these problems shared near-identical symptoms (empty/fallback AI replies) with entirely different root causes — a good reminder that a recurring symptom doesn't imply a recurring cause, and that tracing the actual code path or raw API response is more reliable than pattern-matching to "this looks like the bug from before."

---

## Milestone 5 — Glossary Memory (Auto-Detection)

### 11. `match_memories` missing `memory_type` column (recurrence of issue #1's pattern)

**Symptom:** Decay-immunity logic for glossary entries had no way to distinguish glossary memories from episodic ones — `memory_type` was never coming back from the retrieval function.

**Debug approach:** Ran `SELECT pg_get_functiondef(oid) FROM pg_proc WHERE proname = 'match_memories';` to see the function's actual live definition rather than assuming it matched expectations — confirmed `memory_type` was absent from both `RETURNS TABLE(...)` and the `SELECT` list.

**Fix:** Same `DROP FUNCTION` + `CREATE OR REPLACE FUNCTION` pattern as issue #1, this time adding `memory_type text` to both places.

**Lesson:** Verifying a database function's actual current definition directly is faster and more reliable than assuming it already has a column just because a related column was added recently.

---

### 12. Dictionary-style explanations instead of natural reactions

**Symptom:** When the companion recognized or was told the meaning of a slang/regional term, it explained it in a textbook style ("X means Y, which is [language] for Z") rather than reacting like a real person would.

**Root cause:** The prompt instruction said "ask naturally" but never specified what tone to *avoid* — leaving the model to default toward an explainer voice when handling unfamiliar vocabulary.

**Fix:** Added an explicit negative example to the prompt (the exact phrasing pattern to avoid), rather than relying on a vague positive instruction alone.

**Lesson:** Telling a model what *not* to do, concretely, is often more effective than a general positive instruction — this was also true for the Milestone 4.5 pet-name fix, and held true again here.

---

### 13. Repeating the definition back after learning a term

**Symptom:** After the user explained an unfamiliar term, the companion correctly stopped asking about it going forward — but still restated the definition back once, in a confirming tone ("X means Y, right?").

**Fix:** Added an explicit instruction not to repeat or confirm the definition back — just absorb it and use it naturally afterward.

**Lesson:** A model can partially fix a behavior (stop over-explaining) while still exhibiting a subtler version of the same underlying tic (confirming instead of just moving on) — worth testing the full loop again after each fix rather than assuming one pass resolved everything.

---

### 14. Confident hallucination on an unfamiliar term ("Panchat kehvay")

**Symptom:** Given a genuinely unfamiliar Gujarati phrase, the companion did not ask what it meant — instead it broke the phrase into familiar-sounding fragments and confidently produced a plausible but entirely incorrect translation.

**Root cause:** The existing "ask when you don't understand" instruction only fires when the model recognizes its own uncertainty — but partial pattern-matching (recognizing pieces of the phrase) can make a model feel falsely confident, bypassing that safeguard entirely. This is the same hallucination pattern documented in Milestone 3 (inventing specific unstated details about the user), recurring here in language understanding instead of memory recall.

**Fix:** Added an explicit anti-guessing rule: do not decompose or reconstruct meaning from familiar-looking fragments unless genuinely certain; when in doubt, ask, the same as with any other unfamiliar term.

**Lesson:** A model correctly handling one test case (e.g., guessing "SKC" correctly earlier) is not proof the underlying guessing behavior is fixed — it may simply mean that particular guess happened to land right. Confident-but-wrong outputs are a recurring LLM failure mode that shows up in new domains, not something solved once and done.

---

### 15. Consolidating iterative prompt patches into one structured block

**Context:** After several rounds of small, targeted prompt fixes (pet-name variation in M4.5, then glossary tone, definition-repeat-back, and anti-guessing in M5), merged everything into one comprehensive, well-organized system-prompt section rather than letting incremental patches accumulate side-by-side.

**Lesson:** Multiple overlapping instructions competing for a model's attention can dilute or subtly conflict with each other. A single, coherent, well-structured prompt section is more reliable than a growing pile of one-line patches added over time — worth doing this consolidation pass periodically rather than only at the very end.

---

## Overall theme (updated)

Milestone 5 shifted the *type* of debugging from infrastructure/API issues (Milestone 4's dominant theme) to **prompt behavior tuning** — getting a language model to consistently notice, ask about, and remember something in a natural voice took several real iterations, each surfacing a genuinely distinct failure mode (over-explaining, then confirming back, then confidently guessing wrong) rather than one bug resurfacing repeatedly. The recurring hallucination pattern from Milestone 3 showing up again here, in a new domain, is a good reminder that LLM confidence is not a reliable signal of LLM correctness — and that fixes need to be tested across multiple real scenarios, not just the first one that happens to work.