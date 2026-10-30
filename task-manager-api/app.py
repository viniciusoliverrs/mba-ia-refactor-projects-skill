import logging

from flask import Flask
from flask_cors import CORS

from config.settings import Settings
from database import db
from middlewares.error_handler import register_error_handlers
from routes import register_routes
from utils.helpers import format_date, utcnow


def create_app():
    """Composition root: monta configuração, ORM, middlewares e rotas."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    flask_app = Flask(__name__)
    flask_app.config.from_object(Settings)

    CORS(flask_app, origins=Settings.CORS_ORIGINS)
    db.init_app(flask_app)

    register_error_handlers(flask_app)
    register_routes(flask_app)

    @flask_app.route("/health")
    def health():
        return {"status": "ok", "timestamp": format_date(utcnow())}

    @flask_app.route("/")
    def index():
        return {"message": "Task Manager API", "version": "1.0"}

    with flask_app.app_context():
        db.create_all()

    return flask_app


app = create_app()

if __name__ == "__main__":
    app.run(debug=Settings.DEBUG, host=Settings.HOST, port=Settings.PORT)
