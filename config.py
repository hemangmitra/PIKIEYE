# config.py

import os
from datetime import timedelta

class Config:
    """
    Base configuration class with common settings.
    """
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("No SECRET_KEY set for Flask application.")
    
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    if not JWT_SECRET_KEY:
        raise ValueError("No JWT_SECRET_KEY set for Flask application.")
    
    MONGODB_URI = os.getenv('MONGODB_URI')
    if not MONGODB_URI:
        raise ValueError("No MONGODB_URI set for Flask application.")
    
    # Allowed file extensions for uploads
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
    
    # JWT expiration settings
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Maximum allowed payload to prevent DOS attacks (e.g., 64 MB)
    MAX_CONTENT_LENGTH = 64 * 1024 * 1024

    # CORS settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')
    
    # **Define BASE_URL**
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:8080')
class Config:
    """
    Base configuration class with common settings.
    """
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("No SECRET_KEY set for Flask application.")
    
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    if not JWT_SECRET_KEY:
        raise ValueError("No JWT_SECRET_KEY set for Flask application.")
    
    MONGODB_URI = os.getenv('MONGODB_URI')
    if not MONGODB_URI:
        raise ValueError("No MONGODB_URI set for Flask application.")
    
    # Allowed file extensions for uploads
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
    
    # JWT expiration settings
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Maximum allowed payload to prevent DOS attacks (e.g., 64 MB)
    MAX_CONTENT_LENGTH = 64 * 1024 * 1024

    # CORS settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')

class DevelopmentConfig(Config):
    """
    Development configuration with debug mode enabled.
    """
    DEBUG = True
    ENV = 'development'
    # Development-specific configurations

class TestingConfig(Config):
    """
    Testing configuration with testing mode enabled.
    """
    TESTING = True
    ENV = 'testing'
    # Testing-specific configurations

class ProductionConfig(Config):
    """
    Production configuration with debug mode disabled.
    """
    DEBUG = False
    ENV = 'production'
    # Production-specific configurations
