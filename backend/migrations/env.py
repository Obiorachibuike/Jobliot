import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__),".."))
from alembic import context
from app.db import Base, DB_PATH
from app import models  # noqa
config=context.config
config.set_main_option("sqlalchemy.url", f"sqlite:///{DB_PATH}")
target_metadata=Base.metadata
def run_migrations_online():
    from sqlalchemy import engine_from_config, pool
    connectable=engine_from_config(config.get_section(config.config_ini_section),prefix="sqlalchemy.",poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection,target_metadata=target_metadata,render_as_batch=True)
        with context.begin_transaction(): context.run_migrations()
run_migrations_online()
