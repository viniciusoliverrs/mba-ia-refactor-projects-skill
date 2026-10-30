import os


class Settings:
    """Configuração da aplicação, lida de variáveis de ambiente (com defaults seguros de desenvolvimento)."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    DEBUG = os.environ.get("APP_DEBUG", "false").lower() == "true"
    DB_PATH = os.environ.get("DB_PATH", "loja.db")
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    # Token exigido (header X-Admin-Token) para rotas administrativas; vazio = rotas desabilitadas
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
    VERSAO = "1.0.0"
