import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from config import Config
from backend.routes import register_routes

def create_app():
    app = Flask(
        __name__,
        template_folder='../frontend/templates',
        static_folder='../frontend/static'
    )

    app.config.from_object(Config)
    Config.validate()

    register_routes(app)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)