import sqlite3

from flask import g

from config.settings import Settings


def get_db():
    """Conexão SQLite por requisição (sem estado global mutável)."""
    if "db" not in g:
        g.db = sqlite3.connect(Settings.DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    """Apenas registra o teardown da conexão. A criação do schema é explícita (`database.schema.init_db`)."""
    app.teardown_appcontext(close_db)

