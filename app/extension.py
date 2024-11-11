# app/extensions.py

from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pymongo import MongoClient
import gridfs
from mongoengine import connection
import logging

# Initialize Extensions
jwt = JWTManager()
limiter = Limiter(
    key_func=get_remote_address,
    # You can set default_limits here if needed
)

def init_db(app):
    """
    Initialize MongoDB connection and GridFS.
    """
    try:
        # Connect to MongoDB using MongoEngine
        connection.connect(host=app.config.get('MONGODB_URI'))
        app.logger.info("Connected to MongoDB successfully.")
    except Exception as e:
        app.logger.error(f"Failed to connect to MongoDB: {e}")
        raise
    
    try:
        # Access the underlying PyMongo client
        mongo_client = connection.get_connection()
        app.logger.debug("Retrieved PyMongo client from MongoEngine.")
    
        # Access the default database
        db = connection.get_db()
        app.logger.debug("Accessed default MongoDB database.")
    
        # Initialize GridFS and store it in app's extensions
        grid_fs = gridfs.GridFS(db)
        app.extensions['grid_fs'] = grid_fs
        app.extensions['mongo_db'] = db  # Optionally store the db if needed
    
        # Register the client if other parts of the app need it
        app.extensions['mongo_client'] = mongo_client
    
        app.logger.info("GridFS initialized and attached to Flask extensions successfully.")
    except Exception as e:
        app.logger.error(f"Failed to initialize GridFS: {e}")
        raise
