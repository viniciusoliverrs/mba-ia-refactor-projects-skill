import hmac
import logging

from werkzeug.security import check_password_hash, generate_password_hash

from models import usuario_model
from utils.exceptions import AuthError, NotFoundError, ValidationError

logger = logging.getLogger(__name__)

PREFIXOS_HASH = ("scrypt:", "pbkdf2:")


def listar():
    return usuario_model.listar_todos()


def buscar(usuario_id):
    usuario = usuario_model.buscar_por_id(usuario_id)
    if not usuario:
        raise NotFoundError("Usuário não encontrado")
    return usuario


def criar(dados):
    if not isinstance(dados, dict) or not dados:
        raise ValidationError("Dados inválidos")
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not all(isinstance(v, str) and v for v in (nome, email, senha)):
        raise ValidationError("Nome, email e senha são obrigatórios")

    usuario_id = usuario_model.criar(nome, email, generate_password_hash(senha))
    logger.info("Usuário criado: %s", usuario_id)
    return {"id": usuario_id}


def _senha_confere(armazenada, informada):
    """Retorna (confere, precisa_rehash). Aceita hashes legados em texto puro e migra no login."""
    if armazenada.startswith(PREFIXOS_HASH):
        return check_password_hash(armazenada, informada), False
    return hmac.compare_digest(armazenada, informada), True


def login(dados):
    if not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not email or not senha or not isinstance(email, str) or not isinstance(senha, str):
        raise ValidationError("Email e senha são obrigatórios")

    usuario = usuario_model.buscar_credenciais_por_email(email)
    if usuario:
        confere, rehash = _senha_confere(usuario["senha"], senha)
        if confere:
            if rehash:
                usuario_model.atualizar_senha(usuario["id"], generate_password_hash(senha))
            logger.info("Login bem-sucedido: usuário %s", usuario["id"])
            return {
                "id": usuario["id"],
                "nome": usuario["nome"],
                "email": usuario["email"],
                "tipo": usuario["tipo"],
            }
    logger.warning("Login falhou para o email informado")
    raise AuthError("Email ou senha inválidos")

