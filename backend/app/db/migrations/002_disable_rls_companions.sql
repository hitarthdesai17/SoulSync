-- Temporarily disabled for solo MVP development (no auth/user accounts yet).
   -- MUST be reconsidered once multi-user support or real auth is added (Milestone 10 / real Supabase Auth integration) —
   -- otherwise any client with the anon key could read/write any companion's data.
   alter table companions disable row level security;