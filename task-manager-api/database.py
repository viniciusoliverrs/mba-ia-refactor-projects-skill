from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """Cria o schema. Ação explícita: chamada apenas pelo entry point (`__main__`) ou pelo seed."""
    import models  # noqa: F401  (registra os models no metadata antes do create_all)

    with app.app_context():
        db.create_all()
