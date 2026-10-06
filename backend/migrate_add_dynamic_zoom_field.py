"""
One-time migration script: adds enable_dynamic_zoom column to clips table.
Safe to run multiple times.
"""

from sqlalchemy import text
from database.session import engine

with engine.connect() as conn:
    conn.execute(text("""
        ALTER TABLE clips
        ADD COLUMN IF NOT EXISTS enable_dynamic_zoom BOOLEAN NOT NULL DEFAULT FALSE;
    """))
    conn.commit()

print("Migration complete: enable_dynamic_zoom added to clips table.")
