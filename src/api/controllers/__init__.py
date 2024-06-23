# controllers/__init__.py
from .user import user_bp
from .auth import auth_bp
from .movie import movie_bp
from .serie import serie_bp

def register_blueprints(app):
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(movie_bp, url_prefix='/api')
    app.register_blueprint(serie_bp, url_prefix='/api')