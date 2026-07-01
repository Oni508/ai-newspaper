from sqlite3 import Connection

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS articles (
    url TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    source_name TEXT NOT NULL,
    category TEXT NOT NULL,
    published_at TEXT,
    summary TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_articles_category
    ON articles(category);

CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    importance TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, category)
);

CREATE INDEX IF NOT EXISTS idx_topics_category
    ON topics(category);

CREATE TABLE IF NOT EXISTS topic_articles (
    topic_id INTEGER NOT NULL,
    article_url TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(topic_id, article_url),
    FOREIGN KEY(topic_id) REFERENCES topics(id) ON DELETE CASCADE,
    FOREIGN KEY(article_url) REFERENCES articles(url) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_topic_articles_article_url
    ON topic_articles(article_url);

CREATE TABLE IF NOT EXISTS analyses (
    article_url TEXT PRIMARY KEY,
    summary TEXT NOT NULL,
    background TEXT NOT NULL,
    business_explainer TEXT NOT NULL,
    conditional_scenarios_json TEXT NOT NULL,
    uncertainty TEXT NOT NULL,
    next_checks_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(article_url) REFERENCES articles(url) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS digests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    generated_at TEXT NOT NULL,
    label TEXT NOT NULL,
    article_urls_json TEXT NOT NULL,
    analysis_article_urls_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(generated_at, label)
);

CREATE INDEX IF NOT EXISTS idx_digests_generated_at
    ON digests(generated_at);
"""


def initialize_database(connection: Connection) -> None:
    """Create the initial SQLite schema if it does not already exist."""
    connection.executescript(SCHEMA_SQL)
    connection.commit()
