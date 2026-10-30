import hmac
import logging

from config.settings import Settings
from models import sistema_model
from utils.exceptions import ForbiddenError

logger = logging.getLogger(__name__)


def health():
    """Estado da aplicação. Nunca expõe segredos nem configuração interna."""
    return {
        "status": "ok",
        "database": "connected",
        "counts": sistema_model.contagens(),
        "versao": Settings.VERSAO,
    }


def resetar_banco(token):
    if not Settings.ADMIN_TOKEN or not hmac.compare_digest(token or "", Settings.ADMIN_TOKEN):
        raise ForbiddenError("Acesso negado")
    sistema_model.resetar()
    logger.warning("Banco de dados resetado via rota administrativa")

