"""
Alembic Configuration and Initialization

This file contains instructions and helper code for setting up Alembic
database migrations for the Diabetes Risk Prediction System.

Run these commands in order:

1. If Alembic is not initialized:
   alembic init alembic

2. Create initial migration:
   alembic revision --autogenerate -m "initial_schema"

3. Apply migration:
   alembic upgrade head

4. To create new migrations after model changes:
   alembic revision --autogenerate -m "description"
   alembic upgrade head

"""

# The following should be in alembic/env.py after initialization:

"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import logging.config

# This is the Alembic Config object
config = context.config

# Import settings and models
from app.core.config import get_settings
from app.database import Base

settings = get_settings()

# Configure database URL
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Set up logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# target_metadata is used by 'autogenerate'
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    '''Run migrations in 'offline' mode.'''
    url = config.get_section(config.config_ini_section)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    '''Run migrations in 'online' mode.'''
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
"""

# Migration commands:
# alembic upgrade head           # Apply all pending migrations
# alembic downgrade -1           # Rollback last migration
# alembic downgrade base         # Rollback all (dev only!)
# alembic history                # Show migration history
# alembic current                # Show current revision

print("Alembic setup instructions saved. Follow the steps above.")
