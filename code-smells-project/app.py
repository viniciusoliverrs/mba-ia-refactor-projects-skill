import logging

from flask import Flask
from flask_cors import CORS

from config.settings import Settings
from database import connection
from database.schema import init_db
from middlewares.error_handler import register_error_handlers
from routes import register_routes


def create_app():
    """Composition root: monta configuração, banco, middlewares e rotas.

    Factory pura: não abre conexão nem cria o schema, então importar este módulo não toca `loja.db`.
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app = Flask(__name__)
    app.config.from_object(Settings)
    CORS(app, origins=Settings.CORS_ORIGINS)

    connection.init_app(app)
    register_error_handlers(app)
    register_routes(app)
    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        init_db()  # schema + seed: ação explícita do entry point
    app.run(host=Settings.HOST, port=Settings.PORT, debug=Settings.DEBUG)
