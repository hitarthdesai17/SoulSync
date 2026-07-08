# AI Companion Platform — Milestones

*Status: Locked. Bottom-up ordering — each milestone builds on a working previous one, never skipping ahead of its dependencies.*

---

### Milestone 0 — Environment Setup
- **Goal:** Every Phase 4 tool running and talking to each other
- **Files:** `.env`, `main.py` (hello-world endpoint), basic React shell
- **Concepts:** Environment/secrets management, FastAPI↔Supabase connection, dev servers
- **Difficulty:** Low, but tedious (account setup)
- **Dependencies:** None
- **Outcome:** One API endpoint reachable from the React app

### Milestone 1 — Bare-bones Chat Loop
- **Goal:** Message → Claude API (no personality/memory) → reply → shown in UI
- **Files:** `api/messages.py`, minimal `conversation_engine.py`, basic chat UI
- **Concepts:** LLM API calls, request/response cycle, async functions
- **Difficulty:** Medium
- **Dependencies:** M0
- **Outcome:** First real chat through your own app

### Milestone 2 — Companion & Personality Core
- **Goal:** Create companion with Core Identity fields, stored in DB, injected into prompt
- **Files:** `models/companion.py`, `services/personality.py`, `api/companions.py`, Personality Profile UI
- **Concepts:** DB models/ORMs, prompt assembly, structured data design
- **Difficulty:** Medium
- **Dependencies:** M1
- **Outcome:** Companion behaves consistently like what was described

### Milestone 3 — Short-Term Memory
- **Goal:** Remember earlier messages within a session
- **Files:** `services/memory.py` (short-term)
- **Concepts:** Context window management, message history
- **Difficulty:** Low-Medium
- **Dependencies:** M2
- **Outcome:** No "goldfish" behavior within a single chat

### Milestone 4 — Long-Term Memory (Episodic + Embeddings)
- **Goal:** Strength/decay/reinforcement, embeddings, vector search retrieval
- **Files:** `services/memory.py` (full), `models/memory.py`, pgvector setup
- **Concepts:** Embeddings, vector search, uncertainty-handling rule
- **Difficulty:** High — hardest milestone technically
- **Dependencies:** M3
- **Outcome:** Cross-session memory with realistic confidence/fuzziness

### Milestone 4.5 — Frontend Design Pass (checkpoint, not a feature)
- **Goal:** Give the UI a real design pass — layout, typography, spacing, visual hierarchy, message alignment/formatting — once core functionality is stable enough that we're not still restructuring components every milestone
- **Files:** touches existing frontend components (no new backend logic)
- **Concepts:** Real frontend/UI design principles, not just "add CSS" — proper use of the frontend-design approach for this environment
- **Difficulty:** Medium (design decisions, not technical complexity)
- **Dependencies:** M4 (chat + personality + memory all functional, so styling reflects real, near-final structure rather than being redone repeatedly)
- **Outcome:** SoulSync actually looks like a real product, not a functional prototype — genuinely portfolio/demo-ready
- **Note:** Deliberately deferred until now rather than done incrementally alongside every milestone, to avoid re-styling the same components repeatedly as functionality changes underneath them
- **Additional tracked task (found during M4 testing):** `build_system_prompt` currently causes over-repetition of nicknames/affectionate phrasing (e.g. companion using the same pet name in nearly every message) — the model over-anchors on vivid personality details without guidance on natural variation. Fix: add an explicit instruction to `build_system_prompt` telling the model to vary phrasing naturally rather than repeating the same nickname/phrase every message. Bundled into this milestone since it's prompt/tone tuning, same category as the rest of this pass.

### Milestone 5 — Glossary Memory
- **Goal:** Personal slang / romanized regional language terms stored and reused
- **Files:** extends `services/memory.py`
- **Concepts:** Special-case retrieval, near-permanent memory strength
- **Difficulty:** Low-Medium
- **Dependencies:** M4
- **Outcome:** Terms explained once, never need re-explaining

### Milestone 6 — Emotion Model
- **Goal:** Detect emotional tone, adapt response, handle instruction-vs-emotion conflicts
- **Files:** `services/emotion.py`
- **Concepts:** Sentiment/emotion inference, conditional prompt strategy
- **Difficulty:** Medium-High (sarcasm handling genuinely hard — expect imperfection)
- **Dependencies:** M4 (needs relationship history)
- **Outcome:** Responses match the moment, not just the words

### Milestone 7 — Adaptive Personality Layer
- **Goal:** Personality evolves periodically from memory, constrained by Core
- **Files:** extends `services/personality.py`, periodic review job
- **Concepts:** Background/scheduled jobs, constrained state updates
- **Difficulty:** High
- **Dependencies:** M4, M6
- **Outcome:** Companion genuinely feels different after weeks of use

### Milestone 8 — Full Conversation Engine (Parallelized Pipeline)
- **Goal:** Wire everything into the parallel pipeline, replacing the simple sequential version
- **Files:** `services/conversation_engine.py` (final)
- **Concepts:** Async/concurrent execution in Python
- **Difficulty:** Medium (mostly refactoring)
- **Dependencies:** M5, M6, M7
- **Outcome:** Fast, properly orchestrated responses

### Milestone 9 — Safety & Ethical Guardrails
- **Goal:** Crisis detection/redirection, AI disclosure UI, dignified retirement, Unsaid Things mode
- **Files:** new safety service, retirement flow, Unsaid Things UI/logic
- **Concepts:** Content classification, sensitive-flow UX
- **Difficulty:** Medium-High
- **Dependencies:** M8
- **Outcome:** PRD's non-negotiable guardrails actually enforced in code

### Milestone 10 — Multi-Companion Management
- **Goal:** Multiple companions, siloed by default, cross-awareness only on explicit mention
- **Files:** extends companion/memory models
- **Difficulty:** Medium
- **Dependencies:** M9
- **Outcome:** Full MVP scope from the PRD realized