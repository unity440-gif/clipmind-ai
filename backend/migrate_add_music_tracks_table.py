"""
One-time migration script: creates the music_tracks table.
Safe to run multiple times.
"""

from sqlalchemy import text
from database.session import engine

with engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS music_tracks (
            id UUID PRIMARY KEY,
            title VARCHAR NOT NULL,
            storage_path VARCHAR NOT NULL,
            mood VARCHAR NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """))
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_music_tracks_mood ON music_tracks (mood);
    """))
    conn.commit()

print("Migration complete: music_tracks table created.")
