-- пользователи, роли

-- департаменты
create table departments (
    id          bigserial primary key,
    code        text unique not null,
    name        text not null
);

-- роли и права (для /admin/roles)
create table roles (
    id          bigserial primary key,
    code        text unique not null,   -- 'admin','expert','viewer'
    name        text not null,          -- человекочитаемое
    description text
);

create table permissions (
    code        text primary key,       -- 'documents.read', 'documents.write', ...
    description text
);

create table role_permissions (
    role_id         bigint references roles(id) on delete cascade,
    permission_code text   references permissions(code) on delete cascade,
    primary key (role_id, permission_code)
);

-- пользователи
create table users (
    id              uuid primary key default gen_random_uuid(),
    username        text unique not null,
    password_hash   text not null,
    first_name      text,
    last_name       text,
    middle_name     text,
    email           text,
    phone           text,
    department_id   bigint references departments(id),
    role_id         bigint references roles(id),
    access_levels   text[] not null default '{}',
    is_active       boolean not null default true,
    created_at      timestamptz not null default now(),
    last_login_at   timestamptz
);

-- опционально: refresh-токены для /auth/refresh
create table refresh_tokens (
    id          uuid primary key default gen_random_uuid(),
    user_id     uuid not null references users(id) on delete cascade,
    token_jti   text not null unique,
    expires_at  timestamptz not null,
    created_at  timestamptz not null default now(),
    revoked     boolean not null default false
);

-- документы

create type document_status as enum ('active', 'archived', 'draft');

create table documents (
    id              uuid primary key default gen_random_uuid(),

    title           text not null,
    description     text,
    category        text,

    department_id   bigint references departments(id),
    access_levels    text[] not null default '{}',     -- 'internal','secret'...
    tags            text[] not null default '{}',

    uploaded_by_id  uuid references users(id),
    author          text,

    status          document_status not null default 'draft',
    is_valid        boolean not null default true,    -- действует / утратил силу

    current_version int,

    metadata        jsonb,                            -- {pages, language, keywords}
    upload_date     timestamptz not null default now(),
    last_modified   timestamptz
);

create type doc_version_status as enum (
    'draft',
    'on_approval',
    'approved',
    'registered',
    'invalidated'
);

create table document_versions (
    id              uuid primary key default gen_random_uuid(),
    document_id     uuid not null references documents(id) on delete cascade,
    version         int  not null,

    file_name       text not null,
    file_type       text not null,
    file_size       bigint not null,
    storage_key     text not null,

    upload_date     timestamptz not null default now(),
    uploaded_by_id  uuid references users(id),

    status          doc_version_status not null default 'draft',
    valid_from      date,
    valid_to        date,
    change_notes    text,
    metadata        jsonb,

    is_current      boolean not null default false,

    unique (document_id, version)
);

create unique index ux_document_versions_current
    on document_versions(document_id)
    where is_current;

create table document_metadata_versions (

    document_version_id uuid primary key
        references document_versions(id) on delete cascade,

    changed_at      timestamptz not null default now(),
    changed_by_id   uuid references users(id),

    title           text not null,
    description     text,
    category        text,
    department_id   bigint references departments(id),
    access_levels   text[] not null,
    tags            text[] not null,
    is_valid        boolean not null,
    metadata        jsonb
);


-- заметки

create table workspace_queries (
    id          uuid primary key default gen_random_uuid(),
    user_id     uuid not null references users(id) on delete cascade,

    question    text not null,         -- поле "Введите запрос"
    filters     jsonb,                 -- {date_from, date_to, department_ids, only_active, ...}

    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now()
);

create table workspace_collections (
    id          uuid primary key default gen_random_uuid(),
    user_id     uuid not null references users(id) on delete cascade,
    name        text not null,
    created_at  timestamptz not null default now()
);

create table workspace_collection_items (
    id            uuid primary key default gen_random_uuid(),

    collection_id uuid not null
        references workspace_collections(id) on delete cascade,

    document_id   uuid not null
        references documents(id) on delete cascade,

    created_at    timestamptz not null default now()
);

create unique index ux_workspace_collection_items_unique
    on workspace_collection_items (collection_id, document_id);

-- аудит

create type audit_action as enum (
    'view',
    'search',
    'cite',
    'download',
    'login',
    'logout',
    'create_document',
    'update_document',
    'create_draft',
    'create_collection'
);

create table audit_events (
    id          bigserial primary key,
    user_id     uuid references users(id),
    action      audit_action not null,
    entity_type text not null,      -- 'document','document_version','case','search'
    entity_id   text,
    meta        jsonb,
    created_at  timestamptz not null default now()
);


