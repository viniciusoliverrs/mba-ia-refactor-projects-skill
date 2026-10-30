from flask import Blueprint, jsonify, request

from controllers import usuario_controller

usuario_bp = Blueprint("usuarios", __name__)


@usuario_bp.get("/usuarios")
def listar_usuarios():
    return jsonify({"dados": usuario_controller.listar(), "sucesso": True}), 200


@usuario_bp.get("/usuarios/<int:usuario_id>")
def buscar_usuario(usuario_id):
    return jsonify({"dados": usuario_controller.buscar(usuario_id), "sucesso": True}), 200


@usuario_bp.post("/usuarios")
def criar_usuario():
    dados = usuario_controller.criar(request.get_json(silent=True))
    return jsonify({"dados": dados, "sucesso": True}), 201


@usuario_bp.post("/login")
def login():
    usuario = usuario_controller.login(request.get_json(silent=True))
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200

