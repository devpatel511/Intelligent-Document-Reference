-- Placeholder schema. Implement tables: files, chunks, embeddings, jobs, settings.
CREATE TABLE IF NOT EXISTS monitor_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    recursive BOOLEAN DEFAULT 1,
    excluded_files TEXT, -- JSON list of exact file paths to exclude
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);


