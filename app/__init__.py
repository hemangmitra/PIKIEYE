# app/__init__.py
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from .routes import auth, facefeature, project, unique_faces, health, gridfs
from .extension import jwt, limiter, init_db

# Load environment variables from .env file
load_dotenv()

def create_app():
    app = Flask(__name__)
    env = os.getenv('FLASK_ENV', 'development')
    
    # Load configuration based on the environment
    if env == 'production':
        app.config.from_object('config.ProductionConfig')
    elif env == 'testing':
        app.config.from_object('config.TestingConfig')
    else:
        app.config.from_object('config.DevelopmentConfig')
    
    # Configure Logging
    if not app.debug and not app.testing:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Setup Rotating File Handler
        file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Application startup')
    else:
        # In development, log DEBUG messages to console
        logging.basicConfig(level=logging.DEBUG)

    # **Suppress Pymongo Debug Logs**
    pymongo_logger = logging.getLogger('pymongo')
    pymongo_logger.setLevel(logging.WARNING)
    
    # Initialize MongoDB and GridFS
    try:
        init_db(app)
    except Exception as e:
        app.logger.error(f"Database initialization failed: {e}")
        # Depending on the application needs, you might want to exit or continue

    # Initialize Extensions with the Flask app
    try:
        jwt.init_app(app)
        limiter.init_app(app)
    except Exception as e:
        app.logger.error(f"Extension initialization failed: {e}")
        # Depending on the application needs, you might want to exit or continue

    # Set maximum file size (e.g., 64 MB)
    app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024

    # Register Blueprints
    app.register_blueprint(auth.bp)
    app.register_blueprint(project.bp)
    app.register_blueprint(facefeature.bp)
    app.register_blueprint(unique_faces.bp)
    app.register_blueprint(health.bp)
    app.register_blueprint(gridfs.bp)  # Register GridFS blueprint
    
    # Enable CORS
    CORS(app,
         resources={r"/*": {"origins": app.config.get('CORS_ORIGINS', [])}},
         supports_credentials=True,
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials", "X-Requested-With"])
    
    return app