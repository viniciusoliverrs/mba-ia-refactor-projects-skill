from database.connection import get_db


def contagens():
    """Verifica a conexão e devolve a contagem das principais tabelas."""
    db = get_db()
    db.execute("SELECT 1")
    return {
        tabela: db.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
        for tabela in ("produtos", "usuarios", "pedidos")
    }


def resetar():
    db = get_db()
    for tabela in ("itens_pedido", "pedidos", "produtos", "usuarios"):
        db.execute(f"DELETE FROM {tabela}")
    db.commit()

