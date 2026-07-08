create or replace function match_memories (
    query_embedding vector(384),
    match_companion_id uuid,
    match_threshold float default 0.3,
    match_count int default 5
)
returns table (
    id uuid,
    content text,
    strength float,
    similarity float
)
language sql stable
as $$
    select
        memories.id,
        memories.content,
        memories.strength,
        1 - (memories.embedding <=> query_embedding) as similarity
    from memories
    where memories.companion_id = match_companion_id
        and 1 - (memories.embedding <=> query_embedding) > match_threshold
    order by memories.embedding <=> query_embedding
    limit match_count;
$$;