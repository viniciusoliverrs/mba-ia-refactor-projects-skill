from flask import Blueprint, jsonify, request

from controllers import sistema_controller

sistema_bp = Blueprint("sistema", __name__)


@sistema_bp.get("/")
def index():
    return jsonify(
        {
            "mensagem": "Bem-vindo à API da Loja",
            "versao": "1.0.0",
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        }
    )


@sistema_bp.get("/health")
def health_check():
    return jsonify(sistema_controller.health()), 200


@sistema_bp.post("/admin/reset-db")
def reset_database():
    sistema_controller.resetar_banco(request.headers.get("X-Admin-Token"))
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200
