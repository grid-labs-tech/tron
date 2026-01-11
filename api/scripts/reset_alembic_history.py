#!/usr/bin/env python3
"""
Script to reset Alembic history and mark the initial migration as applied.
This script should be executed after deleting old migrations and creating a new initial migration.
"""

import os
import sys
from pathlib import Path

# Add root directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.shared.database.database import SessionLocal
import os

def reset_alembic_history():
    """Reset Alembic history in the database."""
    # Get database URL from environment variables
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'tron')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'tron')
    DB_NAME = os.getenv('DB_NAME', 'api')
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

    engine = create_engine(DATABASE_URL)

    with engine.connect() as connection:
        # Delete all entries from alembic_version table
        connection.execute(text("DELETE FROM alembic_version"))
        connection.commit()

        # Insert the new initial migration
        connection.execute(text("INSERT INTO alembic_version (version_num) VALUES ('initial_schema')"))
        connection.commit()

        print("✓ Alembic history reset successfully!")
        print("✓ Migration 'initial_schema' marked as applied")

if __name__ == "__main__":
    try:
        reset_alembic_history()
    except Exception as e:
        print(f"❌ Error resetting Alembic history: {e}")
        sys.exit(1)

