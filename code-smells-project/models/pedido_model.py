from database.connection import get_db
from utils.exceptions import ValidationError

_SELECT_PEDIDOS = """
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
"""


def _agrupar_pedidos(rows):
    pedidos = {}
    for row in rows:
        pedido = pedidos.setdefault(
            row["id"],
            {
                "id": row["id"],
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": [],
            },
        )
        if row["produto_id"] is not None:
            pedido["itens"].append(
                {
                    "produto_id": row["produto_id"],
                    "produto_nome": row["produto_nome"] or "Desconhecido",
                    "quantidade": row["quantidade"],
                    "preco_unitario": row["preco_unitario"],
                }
            )
    return list(pedidos.values())


def listar_todos():
    rows = get_db().execute(_SELECT_PEDIDOS + " ORDER BY p.id, i.id").fetchall()
    return _agrupar_pedidos(rows)


def listar_por_usuario(usuario_id):
    rows = get_db().execute(
        _SELECT_PEDIDOS + " WHERE p.usuario_id = ? ORDER BY p.id, i.id", (usuario_id,)
    ).fetchall()
    return _agrupar_pedidos(rows)


def buscar_por_id(pedido_id):
    row = get_db().execute("SELECT id, status FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    return dict(row) if row else None


def criar(usuario_id, itens, total):
    """Cria pedido, itens e baixa de estoque em uma única transação.

    `itens`: lista de dicts com produto_id, quantidade e preco_unitario.
    """
    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
            (usuario_id, total),
        )
        pedido_id = cursor.lastrowid
        for item in itens:
            baixa = db.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                (item["quantidade"], item["produto_id"], item["quantidade"]),
            )
            if baixa.rowcount == 0:
                raise ValidationError(f"Estoque insuficiente para o produto {item['produto_id']}")
            db.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                (pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"]),
            )
        db.commit()
        return pedido_id
    except Exception:
        db.rollback()
        raise


def atualizar_status(pedido_id, novo_status, devolver_estoque=False):
    db = get_db()
    try:
        if devolver_estoque:
            db.execute(
                """
                UPDATE produtos SET estoque = estoque + (
                    SELECT COALESCE(SUM(i.quantidade), 0) FROM itens_pedido i
                    WHERE i.pedido_id = ? AND i.produto_id = produtos.id
                )
                WHERE id IN (SELECT produto_id FROM itens_pedido WHERE pedido_id = ?)
                """,
                (pedido_id, pedido_id),
            )
        db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
        db.commit()
    except Exception:
        db.rollback()
        raise

