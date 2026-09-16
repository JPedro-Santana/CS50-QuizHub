"""
init_db.py — Cria as tabelas no PostgreSQL.
Executado automaticamente pelo Render no buildCommand.
"""

import os
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set.")

# Render fornece URLs com prefixo 'postgres://', psycopg2 precisa de 'postgresql://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS quiz (
        id          SERIAL PRIMARY KEY,
        title       TEXT    NOT NULL,
        category    TEXT    NOT NULL,
        description TEXT,
        image       TEXT,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id            SERIAL PRIMARY KEY,
        quiz_id       INTEGER NOT NULL REFERENCES quiz(id) ON DELETE CASCADE,
        question_text TEXT    NOT NULL,
        question_type TEXT    NOT NULL
    );
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS options (
        id           SERIAL  PRIMARY KEY,
        question_id  INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
        options_text TEXT    NOT NULL,
        is_correct   BOOLEAN NOT NULL DEFAULT FALSE
    );
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS open_answers (
        id             SERIAL  PRIMARY KEY,
        question_id    INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
        correct_answer TEXT    NOT NULL
    );
""")

conn.commit()
cur.close()
conn.close()

print(" Database tables created successfully.")
