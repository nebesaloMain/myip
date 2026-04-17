CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users(
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fio VARCHAR,
    username VARCHAR UNIQUE,
    email VARCHAR UNIQUE,
    job VARCHAR,
    passhash VARCHAR,
    verify_code VARCHAR,
    is_verified BOOLEAN DEFAULT FALSE,
    is_admin BOOLEAN DEFAULT FALSE
);

CREATE TABLE bids(
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content VARCHAR,
    add_content VARCHAR,
    name VARCHAR,
    files VARCHAR[] DEFAULT '{}', 
    timestamp TIMESTAMP DEFAULT now(),
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    owner_username VARCHAR,
    owner_fio VARCHAR,
    owner_job VARCHAR,
    status VARCHAR DEFAULT 'new'
);