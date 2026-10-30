from database.connection import get_db

COLUNAS = "id, nome, descricao, preco, estoque, categoria, ativo, criado_em"


def listar_todos():
    rows = get_db().execute(f"SELECT {COLUNAS} FROM produtos").fetchall()
    return [dict(row) for row in rows]


def buscar_por_id(produto_id):
    row = get_db().execute(f"SELECT {COLUNAS} FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    return dict(row) if row else None


def criar(nome, descricao, preco, estoque, categoria):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    db.commit()
    return cursor.lastrowid


def atualizar(produto_id, nome, descricao, preco, estoque, categoria):
    db = get_db()
    db.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )
    db.commit()


def deletar(produto_id):
    db = get_db()
    db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    db.commit()


def pesquisar(termo=None, categoria=None, preco_min=None, preco_max=None):
    condicoes = []
    params = []
    if termo:
        condicoes.append("(nome LIKE ? OR descricao LIKE ?)")
        params.extend([f"%{termo}%", f"%{termo}%"])
    if categoria:
        condicoes.append("categoria = ?")
        params.append(categoria)
    if preco_min is not None:
        condicoes.append("preco >= ?")
        params.append(preco_min)
    if preco_max is not None:
        condicoes.append("preco <= ?")
        params.append(preco_max)

    where = " AND ".join(condicoes) if condicoes else "1=1"
    rows = get_db().execute(f"SELECT {COLUNAS} FROM produtos WHERE {where}", params).fetchall()
    return [dict(row) for row in rows]

