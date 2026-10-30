from database.connection import get_db

COLUNAS_PUBLICAS = "id, nome, email, tipo, criado_em"


def listar_todos():
    """Lista usuários sem expor o hash da senha."""
    rows = get_db().execute(f"SELECT {COLUNAS_PUBLICAS} FROM usuarios").fetchall()
    return [dict(row) for row in rows]


def buscar_por_id(usuario_id):
    row = get_db().execute(f"SELECT {COLUNAS_PUBLICAS} FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return dict(row) if row else None


def buscar_credenciais_por_email(email):
    """Uso interno de autenticação: inclui o hash da senha (nunca devolver ao cliente)."""
    row = get_db().execute(
        "SELECT id, nome, email, senha, tipo FROM usuarios WHERE email = ?", (email,)
    ).fetchone()
    return dict(row) if row else None


def criar(nome, email, senha_hash, tipo="cliente"):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    db.commit()
    return cursor.lastrowid


def atualizar_senha(usuario_id, senha_hash):
    db = get_db()
    db.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (senha_hash, usuario_id))
    db.commit()

