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
    from database.schema import init_db

    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()

