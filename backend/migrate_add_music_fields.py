"""
One-time migration script: adds background_music_path and music_volume
columns to the clips table. Safe to run multiple times.
"""

from sqlalchemy import text
from database.session import engine

with engine.connect() as conn:
    conn.execute(text("""
        ALTER TABLE clips
        ADD COLUMN IF NOT EXISTS background_music_path VARCHAR;
    """))
    conn.execute(text("""
        ALTER TABLE clips
        ADD COLUMN IF NOT EXISTS music_volume FLOAT NOT NULL DEFAULT 0.15;
    """))
    conn.commit()

print("Migration complete: background_music_path and music_volume added to clips table.")
