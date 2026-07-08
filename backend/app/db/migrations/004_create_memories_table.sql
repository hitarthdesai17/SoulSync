create extension if not exists vector;

create table memories (
    id uuid primary key default gen_random_uuid(),
    companion_id uuid references companions(id) not null,
    content text not null,
    embedding vector(384),
    strength float not null default 1.0,
    memory_type text not null default 'episodic',
    created_at timestamp with time zone default now(),
    last_reinforced_at timestamp with time zone default now()
);

alter table memories disable row level security;
