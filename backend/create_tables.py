"""
One-time script: creates all tables in Postgres based on our SQLAlchemy models.
Run this manually with: docker compose exec backend python create_tables.py
Later, once Alembic is set up, this script gets replaced by proper migrations.
"""

from database.session import Base, engine
import database  # triggers the imports in database/__init__.py, registering all models

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done. Tables created:", list(Base.metadata.tables.keys()))
