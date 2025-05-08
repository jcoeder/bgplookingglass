import logging

# Application-wide configuration
class AppConfig:
    DEBUG = True
    LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    SECRET_KEY = 'your_secret_key_here'  # Replace with secure string
