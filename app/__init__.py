# Source: app/__init__.py
# Published: 5/9/2025, 10:00:00 PM (updated)

from flask import Flask
from .routes import bp  # Import the Blueprint

def create_app():
    app = Flask(__name__)
    
    # Register the Blueprint
    app.register_blueprint(bp, url_prefix='/')
    
    # Optional configurations (no Flasgger here)
    app.config['SECRET_KEY'] = 'your_secret_key_here'  # Replace with a secure string
    
    return app

# For local testing
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
