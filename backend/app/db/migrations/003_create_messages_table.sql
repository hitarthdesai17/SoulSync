create table messages (
    id uuid primary key default gen_random_uuid(),
    companion_id uuid references companions(id) not null,
    role text not null,
    content text not null,
    created_at timestamp with time zone default now()
);

alter table messages disable row level security;