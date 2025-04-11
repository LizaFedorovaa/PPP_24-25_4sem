from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Подключаем ваши модели и базу данных
from app.models.user import User  # Импортируем модель User
from app.db import Base  # Импортируем Base из db.py

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Указываем метаданные моделей для автогенерации
target_metadata = Base.metadata

def run_alembic_offline() -> None:
    """Run alembic in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_alembic()

def run_alembic_online() -> None:
    """Run alembic in 'online' mode."""
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
            context.run_alembic()

if context.is_offline_mode():
    run_alembic_offline()
else:
    run_alembic_online()