CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT,
    job_url TEXT UNIQUE,
    description TEXT,
    location TEXT,
    is_remote BOOLEAN DEFAULT FALSE,
    score INTEGER DEFAULT 0,
    recommendations TEXT,
    curated BOOLEAN DEFAULT FALSE
);