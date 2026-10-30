from routes.pedido_routes import pedido_bp
from routes.produto_routes import produto_bp
from routes.sistema_routes import sistema_bp
from routes.usuario_routes import usuario_bp


def register_routes(app):
    for blueprint in (produto_bp, usuario_bp, pedido_bp, sistema_bp):
        app.register_blueprint(blueprint)

