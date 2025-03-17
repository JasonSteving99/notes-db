-- Setup Vector Search Extension.
INSTALL vss;
LOAD vss;
SET hnsw_enable_experimental_persistence=true; -- See: https://duckdb.org/docs/stable/extensions/vss.html#persistence still experimental feature.

-- Create sequences for auto-incrementing IDs
CREATE SEQUENCE IF NOT EXISTS notes_id_seq;
CREATE SEQUENCE IF NOT EXISTS tags_id_seq;

-- Main notes table
CREATE TABLE IF NOT EXISTS notes (
    note_id INTEGER PRIMARY KEY DEFAULT nextval('notes_id_seq'),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding FLOAT[3072] NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS notes_hnsw_index ON notes USING HNSW (embedding) WITH (metric = 'cosine');

-- Tags/categories table
CREATE TABLE IF NOT EXISTS tags (
    tag_id INTEGER PRIMARY KEY DEFAULT nextval('tags_id_seq'),
    name TEXT UNIQUE NOT NULL
);

-- Junction table for notes-tags many-to-many relationship
CREATE TABLE IF NOT EXISTS note_tags (
    note_id INTEGER REFERENCES notes(note_id),
    tag_id INTEGER REFERENCES tags(tag_id),
    PRIMARY KEY (note_id, tag_id)
);

