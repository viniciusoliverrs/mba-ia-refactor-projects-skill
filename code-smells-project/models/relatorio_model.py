from database.connection import get_db


def obter_totais():
    """Agregados de vendas em uma única consulta."""
    row = get_db().execute(
        """
        SELECT COUNT(*) AS total_pedidos,
               COALESCE(SUM(total), 0) AS faturamento,
               COALESCE(SUM(status = 'pendente'), 0) AS pendentes,
               COALESCE(SUM(status = 'aprovado'), 0) AS aprovados,
               COALESCE(SUM(status = 'cancelado'), 0) AS cancelados
        FROM pedidos
        """
    ).fetchone()
    return dict(row)
