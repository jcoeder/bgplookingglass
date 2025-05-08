# Source: app.py
# Published: 5/9/2025, 10:00:00 AM (new file)

from flask import Flask
from routes import bp  # Import the Blueprint

def create_app():
    app = Flask(__name__)
    
    # Register the Blueprint
    app.register_blueprint(bp, url_prefix='/')  # Routes are available under the root path
    
    # Optional: Add configurations here (e.g., for logging, secrets, or extensions)
    app.config['SECRET_KEY'] = 'your_secret_key_here'  # Replace with a secure string
    
    return app

# For testing locally, you can run this file directly
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

