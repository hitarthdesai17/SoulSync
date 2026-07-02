# AI Companion Platform — Product Requirements Document

*Status: Draft v1 — Phase 2 complete*

---

## Mission

To help people reconnect with who they were, say what went unsaid, and become who they wanted to be — through AI companions shaped by the relationships that mattered to them, without ever pretending to replace the people themselves. Purely fantastical or entertainment companions are supported too, but clearly framed as roleplay, not as identity or relationship work.

## Vision

A world where no one has to lose access to their own growth just because they lost access to the person who inspired it.

---

## User Personas

1. **The Unfinished Griever** — lost someone (to death or distance) and needs a space to say things left unsaid. Uses the platform in short, emotionally intense bursts, not daily chatting. Success looks like eventually needing the platform *less*.
2. **The Self-Reconnector** — hasn't necessarily lost someone to death, but lost a version of themselves tied to a relationship that faded. Wants a companion that helps recover that thread. Ongoing, lower-intensity use.
3. **The Growth-Seeker** — wants a mentor/coach-type companion, forward-facing. Leans on world knowledge. Lowest emotional stakes.
4. **The Escapist** — wants a fictional character or fantasy/roleplay companion, explicitly for entertainment. No identity-reconnection framing needed. Fewest guardrails.

**Cross-cutting safety principle (not a persona):** Any user, regardless of companion type, must be recognized by the platform if they show signs of acute distress, and gently redirected toward real human support.

---

## User Stories

**The Unfinished Griever**
- As someone who never got to say goodbye, I want a space to say the unsaid thing to a companion styled after that person, so I can feel some closure without pretending they're really there.
- As this user, I want the companion to notice if I'm circling the same unresolved pain without progress, and gently name that, so I'm not left stuck in that mode indefinitely — without the app ever abruptly cutting me off.

**The Self-Reconnector**
- As someone who drifted from a friendship, I want a companion that remembers who I was becoming during that friendship, so I can reconnect with that version of myself.
- As this user, I want the companion to notice and reflect my growth over time, so the relationship feels alive, not like a static journal.

**The Growth-Seeker**
- As someone chasing a goal, I want a mentor companion that can pull in real-world knowledge, so its advice is actually useful.
- As this user, I want the mentor to hold me accountable over time, not just deliver one-off pep talks.

**The Escapist**
- As someone who wants pure entertainment, I want a fictional-character companion with no identity-reconnection framing, so it doesn't feel heavier than I want it to be.

**Cross-cutting (safety)**
- As any user, if I express acute distress, I want the platform to recognize it and gently point me to real human support, regardless of which companion I'm talking to.

---

## Core Features (MVP)

**Companion Creation & Customization**
1. Personality builder — traits, speaking style, background story, likes/dislikes, humor, communication style, relationship type
2. Realism/intimacy dial, gated by a reflective check-in before max realism
3. Persistent, non-removable "I am AI" disclosure in every companion's UI

**Personalization & Memory**
4. Personal data ingestion — chats, diaries, letters, notes (text only for MVP)
5. Two-tier memory — short-term (session) and long-term (persistent), user-set retention/forgetting policy per companion
6. Companion evolution engine — personality/behavior shifts gradually based on accumulated interaction history

**Conversation Intelligence**
7. Emotional-context adaptivity — companion reads what the conversation needs (comfort / play / challenge)
8. World-knowledge grounding (retrieval) — available for growth-seeker-type companions; deliberately excluded for grief/reconnection-type companions
9. "Unsaid Things" mode — dedicated flow with progress-vs-repetition detection and gentle closure nudge

**Multi-Companion Management**
10. Multiple companions per user, siloed by default
11. Cross-companion awareness only on explicit user mention, never automatic

**Safety (applies to ALL companion types)**
12. Crisis/acute-distress detection with redirection to real human support
13. Dignified companion retirement flow — a real "ending," not just a delete button

## Nice-to-Have (post-MVP)
- Voice cloning (own dedicated consent flow, deferred)
- Companion-to-companion interaction (opt-in only)
- Growth visualization over time

## Future / Explicitly Out of Scope
- Multi-tenant scale, billing, growth/marketing features
- Mobile app
- Advertising or monetization tied to a specific real person's likeness — **permanently** out of scope, not just deferred

---

## Non-Goals
- Not a replacement for professional grief counseling or therapy
- Not trying to convince users a companion *is* the real person
- Not a general-purpose chatbot / ChatGPT competitor
- Not optimizing for engagement/time-spent as a success metric

## Success Metrics
- Personal understanding: can you explain every architectural decision to someone else?
- At least one companion type feels genuinely useful/meaningful in real use, not just technically functional
- "Unsaid Things" mode produces something that feels honest, not hollow, in real testing
- Zero instances, in testing, of a companion claiming to literally *be* the real person

## Risks
- Emotional risk to the builder (you), given you're both engineer and first user of emotionally loaded features
- Scope creep — this is an ambitious system for a solo learning project
- AI "hallucinating" a real person's likely words/reactions in ways that feel false
- Technical debt from learning-as-you-go (expected, not a failure)

## Ethical Principles
- **Transparency:** persistent, non-removable AI disclosure
- **Non-deception:** never claims to literally be the real person
- **User agency within hard limits:** realism check-ins, no autonomous outreach, no likeness-based ads, age-gating, crisis redirection — none of these are user-configurable
- **Dignity in retirement:** companions get a real ending, not a silent delete
