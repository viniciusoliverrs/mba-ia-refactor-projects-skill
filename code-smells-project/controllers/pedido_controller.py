from config.constants import STATUS_PEDIDO
from models import pedido_model, produto_model
from services import notification_service
from utils.exceptions import NotFoundError, ValidationError


def _validar_itens(itens):
    if not isinstance(itens, list) or not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    for item in itens:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("produto_id"), int)
            or not isinstance(item.get("quantidade"), int)
            or item["quantidade"] <= 0
        ):
            raise ValidationError("Item inválido: informe produto_id e quantidade positiva")


def criar(dados):
    if not isinstance(dados, dict) or not dados:
        raise ValidationError("Dados inválidos")
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    _validar_itens(itens)

    total = 0
    itens_precificados = []
    for item in itens:
        produto = produto_model.buscar_por_id(item["produto_id"])
        if produto is None:
            raise ValidationError(f"Produto {item['produto_id']} não encontrado")
        if produto["estoque"] < item["quantidade"]:
            raise ValidationError(f"Estoque insuficiente para {produto['nome']}")
        total += produto["preco"] * item["quantidade"]
        itens_precificados.append({**item, "preco_unitario": produto["preco"]})

    pedido_id = pedido_model.criar(usuario_id, itens_precificados, total)
    notification_service.pedido_criado(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": total}


def listar_todos():
    return pedido_model.listar_todos()


def listar_por_usuario(usuario_id):
    return pedido_model.listar_por_usuario(usuario_id)


def atualizar_status(pedido_id, dados):
    novo_status = dados.get("status", "") if isinstance(dados, dict) else ""
    if novo_status not in STATUS_PEDIDO:
        raise ValidationError("Status inválido")

    pedido = pedido_model.buscar_por_id(pedido_id)
    if not pedido:
        raise NotFoundError("Pedido não encontrado")

    devolver_estoque = novo_status == "cancelado" and pedido["status"] != "cancelado"
    pedido_model.atualizar_status(pedido_id, novo_status, devolver_estoque=devolver_estoque)
    notification_service.status_alterado(pedido_id, novo_status)

