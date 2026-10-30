import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from utils.exceptions import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        return jsonify({"erro": error.message, "sucesso": False}), error.status

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return jsonify({"erro": error.description, "sucesso": False}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.exception("Erro inesperado: %s", error)
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
