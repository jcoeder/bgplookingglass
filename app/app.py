from flask import Flask
from app.routes import bp
from app_config import AppConfig

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = AppConfig.SECRET_KEY
    app.register_blueprint(bp, url_prefix='/')
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=AppConfig.DEBUG, host='127.0.0.1', port=5000)
