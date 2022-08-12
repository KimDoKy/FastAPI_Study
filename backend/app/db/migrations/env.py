import pathlib
import sys
import alembic
from sqlalchemy import engine_from_config, pool

from logging.config import fileConfig
import logging

# config를 쉽게 가져오기 위해 앱디렉터리를 추가
sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))

from app.core.config import DATABASE_URL

# ini 파일의 값에 대한 액세스를 제공하는 Alembic Config 객체
config = alembic.context.config
# 로깅을 위한 설정 파일
fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")

def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode
    """
    connectable = config.attributes.get("connection", None)
    config.set_main_option("sqlalchemy.url", str(DATABASE_URL))

    if connectable is None:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

    with connectable.connect() as connection:
        alembic.context.configure(
            connection=connection,
            target_metadata=None
        )
        with alembic.context.begin_transaction():
            alembic.context.run_migrations()

def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode
    """
    alembic.context.configure(url=str(DATABASE_URL))
    with alembic.context.begin_transaction():
        alembic.context.run_migrations()

if alembic.context.is_offline_mode():
    logger.info("Running migrations offline")
    run_migrations_offline()
else:
    logger.info("Running migrations online")
    run_migrations_online()

