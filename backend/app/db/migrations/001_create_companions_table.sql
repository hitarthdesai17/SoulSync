create table companions (
       id uuid primary key default gen_random_uuid(),
       name text not null,
       relationship_type text not null,
       backstory text,
       speaking_style text,
       core_traits jsonb default '{}',
       adaptive_state jsonb default '{}',
       created_at timestamp with time zone default now()
   );