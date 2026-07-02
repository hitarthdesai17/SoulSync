# AI Companion Platform — Architecture Decisions

*This document is built incrementally as each design phase is finalized. Each section below is locked once we agree on it in conversation — treat this as the source of truth going forward, more reliable than scrolling back through chat history.*

---

## 1. Personality Architecture

**Status: Locked**

### Core Concept
An AI model has no persistent personality on its own — the same base model is used for every conversation. "Personality" is therefore an engineering problem: *what information do we feed the model, every time, so it consistently behaves like a specific character?*

### Structure: Personality Profile
A dedicated, per-companion section — separate from chat — where all personality data lives and gets edited.

**Two layers:**

1. **Core Identity**
   - Traits, backstory, speaking style, relationship type
   - Authored explicitly by the user
   - The anchor — does not drift on its own
   - Only changes via explicit user edit

2. **Adaptive Layer**
   - Mood, tone, small stylistic quirks
   - Emerges naturally through real conversation over time
   - Visible to the user, clearly labeled as "developed through your conversations" (distinct from core, for transparency)
   - Editable by the user
   - **Constraint: can never override or contradict the Core layer.** Evolution happens *within* the boundaries the user set, not against them.

### Seeding Flow
1. User provides a freeform description of the companion (traits, style, backstory, etc.)
2. System parses this into structured fields (trait values, speaking style parameters, etc.)
3. System reflects its interpretation back to the user for confirmation ("here's what I understood — is this right?") before finalizing

### Editing Flow
- All edits happen in the Personality Profile section, never inferred from mid-chat conversation (avoids ambiguity between roleplay and real instruction)
- **MVP: edits apply instantly**
- Gradual "settling in" behavior after edits — deferred to Nice-to-Have (adds meaningful complexity; sequencing decision to ship a working simple version first)

### Open / Deferred Items
- Gradual settling behavior (post-MVP)
- Exact mechanism for how the Adaptive Layer's evolution is triggered/weighted by conversation (to be defined in Memory Architecture phase)

---

## 2. Memory Architecture

**Status: Locked**

### Core Concept
An AI model has no memory between messages — each message requires the system to re-send all relevant context. "Memory" is therefore a retrieval and storage problem: what does the system store, and what does it decide to pull back in for each message?

### Memory Tiers
1. **Short-term (working) memory** — the current session, sent in full, complete detail
2. **Long-term memory** — everything older, not sent in full; only relevant pieces retrieved per message

### Long-term Memory: Two Categories
1. **Episodic memory** — things that happened, conversations, facts shared
   - Each memory has a **strength score**
   - Strength starts high when first mentioned, **decays** over time if unreferenced
   - Strength is **reinforced** (increases) if the topic is mentioned again later
   - Low-strength memories are not deleted — they become "fuzzy" (retrievable but uncertain)
2. **Glossary/reference memory** — personal slang, romanized regional language terms, abbreviations (e.g. "kn" = "kai nai" = nothing)
   - Near-permanent strength — does not decay like episodic memory
   - Checked against every incoming message, not just contextually relevant retrieval
   - Once a term is explained (by user, or during upload/setup), it should not need to be asked again

### Uncertainty Handling (anti-hallucination rule)
Memory strength directly controls response confidence:
- High strength → respond confidently ("Yeah, we used to do that all the time")
- Low strength → hedge honestly, ask for a reminder ("I think we did something like that — remind me?")
- No match found → ask, never guess or invent

### Retrieval Mechanism
- Text is converted into **embeddings** (numerical representations of meaning, not exact words)
- New messages are embedded and compared against stored memory embeddings via **vector search** to find relevant matches
- Only relevant matches are pulled into context — not the full memory history

### Connection to Personality (Adaptive Layer)
The Adaptive Layer (see Section 1) does not update on every message. Periodically (e.g. after N conversations or at session end), the system reviews recent high-strength memories and evaluates whether they suggest a tone/mood/style shift. This keeps evolution deliberate rather than noisy or unstable.

### Handling Romanized Regional Language / Code-Switching
- Modern LLMs handle common romanized Hindi/Gujarati and code-switched text reasonably well natively
- Gap is in **personal/hyper-local slang** — handled via Glossary memory above
- System should only ask for clarification when a term is genuinely unrecognized **and** materially changes meaning — not for unusual spelling or typos it can still infer
- Clarification should be batched during initial upload/setup where possible, not constantly interrupt live conversation

---

## 3. Emotion Model

**Status: Locked**

### Core Concept
Distinct from the Personality Adaptive Layer. The Adaptive Layer is about who the companion is *becoming* over time (slow). The Emotion Model is about reading what the user needs *right now, in this message* (fast) and shaping the response accordingly.

### Two Steps
1. **Detect** — infer the user's emotional state from the current message and recent context (intensity, valence, whether they seem to want space or engagement)
2. **Respond appropriately** — response strategy is persona/companion-type specific. Same detected emotion, different appropriate response depending on companion type (e.g. mentor vs. grief-companion)

### Sarcasm & Ambiguity Handling
Sarcasm detection is a genuinely unsolved problem in NLP generally — this system will not be perfect, and should not be designed as if it can be.
- **Lean on relationship history**, not just the single message — the system should factor in a specific user's typical tone (from memory/personality data) rather than reading each message in isolation
- **When uncertain, avoid committing hard to one interpretation** — respond in a way that works reasonably either way, or gently reflect back rather than confidently misreading
- **Design for graceful recovery, not perfection** — if misread, the user should be able to correct in one message and have the companion adapt immediately without friction or argument

### Conflict Rule: Explicit Instruction vs. Detected Emotion
When a user's explicit request conflicts with detected emotional state (e.g. "just distract me" while clearly upset): the companion acknowledges what it's noticing once, briefly and non-pushy, then honors the user's actual request. Check in first, then follow the ask — don't interrogate or override.

---

## 4. Conversation Engine

**Status: Locked**

### Core Concept
The orchestration pipeline that ties Personality, Memory, and Emotion together into a single assembled prompt for each user message.

### Pipeline
1. User sends message
2. **Run in parallel** (none depend on each other's output):
   - Glossary check (unfamiliar terms needing clarification?)
   - First-pass emotion detection (raw message read)
   - Long-term memory retrieval (embedding + vector search)
   - Personality Profile fetch (core + adaptive layers)
3. Final emotion read — incorporates retrieved memory context (relationship history) to improve accuracy, especially for sarcasm/ambiguity (see Emotion Model)
4. Assemble all outputs into a single prompt → send to AI model
5. Response generated → returned to user
6. Log message into short-term memory; flag for long-term storage and periodic personality-evolution review (see Memory Architecture, Section 1 Adaptive Layer connection)

### Parallelization Principle
Two steps can run in parallel only if neither depends on the other's output. Prompt assembly (step 4) is the sync point — it cannot start until all parallel steps in step 2 (and the refined read in step 3) have returned.

---

## Comparative Note: Character.AI (for context, not a target to match)

Researched for calibration, not benchmarking. Key differences from this architecture:
- Character.AI uses a session-level buffer (~10-15 turns) plus summary embeddings; long-term memory is not graded/persistent between sessions — this platform's strength/decay/reinforcement model is architecturally more deliberate on this specific point
- Character.AI's persona is largely static once defined; this platform's Core/Adaptive split allows evolution without personality drift, which is a documented gap in Character.AI's system
- Character.AI lacks built-in crisis-redirection and non-deception guardrails as core architecture; research has associated high-disclosure use with emotional distress and dependency in some users — this platform's ethical guardrails (Section 0, PRD) are designed to address this from the start, not patched in afterward

---

# Phase 4: Software Architecture / Tech Stack

**Status: Locked**

*Calibrated to: Python-comfortable, some Flask exposure without deep understanding, basic HTML/CSS, fast cross-language learner. $0 budget. MVP is solo-use, not multi-tenant.*

| Layer | Choice | Reasoning |
|---|---|---|
| Backend framework | **FastAPI** | Type-hint driven (forces explicit data-shape understanding, unlike Flask's looser style), async-native (matters for AI model calls), current industry standard for AI-backed apps |
| Frontend | **React** | Chosen knowingly over plain HTML/CSS/JS despite steeper learning curve, for industry-standard skill value |
| Database | **Postgres via Supabase (free tier)** | Relational data (accounts, personality, glossary) + pgvector extension for memory embedding search — one tool covers both jobs |
| Auth | **Supabase Auth (bundled)** | Authentication is a solved, security-sensitive problem — not worth hand-rolling for this project's actual learning goals (memory/personality/emotion architecture is the differentiator, not password hashing) |
| File Storage | **Supabase Storage (bundled)** | Same reasoning as Auth — comes free with the same account |
| Embeddings | **sentence-transformers (local, open-source)** | Zero cost, runs on-device, real hands-on learning value vs. a hidden API call |
| AI Model | **Anthropic (Claude) API** | Default choice; Conversation Engine design (Section 4) is model-agnostic by design, so this is swappable without architecture changes |
| Deployment | **None for MVP — run locally** | No multi-user need yet; revisit with free-tier hosting (Render/Railway) once local version is working end-to-end |

### Cost Summary
Supabase free tier: $0. sentence-transformers: $0 (local compute only). Claude API: pay-per-token, fractions of a cent per message at solo-testing volume, likely covered by initial free trial credit. Total realistic cost during MVP build: effectively $0.

### Key Principle Carried Forward
The Conversation Engine (Phase 3, Section 4) was deliberately designed so the AI model is just one swappable component in the pipeline — not hard-wired into the architecture. This tech stack choice reflects that: nothing here should require redesigning Phases 1-3 if a specific tool is swapped later.