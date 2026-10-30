import logging

logger = logging.getLogger(__name__)


def pedido_criado(pedido_id, usuario_id):
    logger.info("Notificação (e-mail/SMS/push): pedido %s criado para o usuário %s", pedido_id, usuario_id)


def status_alterado(pedido_id, novo_status):
    if novo_status == "aprovado":
        logger.info("Notificação: pedido %s aprovado, preparar envio", pedido_id)
    elif novo_status == "cancelado":
        logger.info("Notificação: pedido %s cancelado, estoque devolvido", pedido_id)

