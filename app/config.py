import os
import logging

# Load environment variables
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')

# Set up logging based on debug level
if DEBUG:
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
else:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Other app configurations
SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key_here')  # Replace with a secure string
