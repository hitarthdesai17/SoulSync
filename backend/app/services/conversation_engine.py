"""
Conversation Engine (see docs/ARCHITECTURE.md, Section 4).
Orchestrates the full pipeline for a single message:
1. Glossary check + emotion detection + memory retrieval + personality fetch (parallel)
2. Final emotion read (using retrieved memory)
3. Assemble prompt
4. Call the AI model
5. Log the message for future memory/personality updates
"""
