from flask import Flask
from .auth import auth_bp

def register_routes(app: Flask):
    app.register_blueprint(auth_bp)