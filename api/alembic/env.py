import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from app.database import Base

# Import all models to ensure they're registered with SQLAlchemy for autogenerate
# These imports are required even though they appear unused
from app.applications.infra.application_model import Application  # noqa: F401
from app.instances.infra.instance_model import Instance  # noqa: F401
from app.environments.infra.environment_model import Environment  # noqa: F401
from app.clusters.infra.cluster_model import Cluster  # noqa: F401
from app.templates.infra.template_model import Template  # noqa: F401
from app.templates.infra.component_template_config_model import (  # noqa: F401
    ComponentTemplateConfig,
)
from app.settings.infra.settings_model import Settings  # noqa: F401
from app.users.infra.user_model import User  # noqa: F401
from app.auth.infra.token_model import Token  # noqa: F401
from app.webapps.infra.application_component_model import (  # noqa: F401
    ApplicationComponent,
)
from app.shared.infra.cluster_instance_model import ClusterInstance  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata


def get_database_url():
    """Get database URL from environment variables or fallback to config."""
    db_host = os.getenv("DB_HOST")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")

    if all([db_host, db_user, db_password, db_name]):
        return f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}"

    # Fallback to alembic.ini (for local development)
    return None


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Use environment variables if available, otherwise fall back to alembic.ini
    url = get_database_url() or config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Use environment variables if available, otherwise fall back to alembic.ini
    database_url = get_database_url()
    configuration = config.get_section(config.config_ini_section, {})

    if database_url:
        configuration["sqlalchemy.url"] = database_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
