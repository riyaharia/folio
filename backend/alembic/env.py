from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context
from app.config import settings
from app.database.base import Base
import app.database.models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

OWN_TABLES = {
    "users",
    "source_documents",
    "document_chunks",
    "chat_threads",
    "chat_messages",
    "message_citations",
}

# Added in migrations, not SQLAlchemy models.
MANAGED_COLUMNS = {"search_vector"}
MANAGED_INDEXES = {
    "ix_document_chunks_search_vector",
    "ix_document_chunks_embedding_hnsw",
    "ix_document_chunks_chunk_metadata",
}


def sqlalchemy_url() -> str:
    url = settings.database_url
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql://")
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url.removeprefix("postgres://")
    return url


def include_object(object_, name, type_, reflected, compare_to) -> bool:
    if type_ == "table":
        return name in OWN_TABLES
    if type_ == "column" and name in MANAGED_COLUMNS:
        return False
    if type_ == "index" and name in MANAGED_INDEXES:
        return False
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=sqlalchemy_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(sqlalchemy_url(), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
