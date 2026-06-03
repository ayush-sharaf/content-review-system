from app.route.movies import movies_bp


def register_routes(app):
    app.register_blueprint(movies_bp)
