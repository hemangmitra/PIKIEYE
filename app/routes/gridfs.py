# app/routes/gridfs.py

from flask import Blueprint, Response, current_app
from bson import ObjectId
import gridfs
import logging

bp = Blueprint('gridfs', __name__, url_prefix='/api/gridfs')

logger = logging.getLogger(__name__)

@bp.route('/<gridfs_id>', methods=['GET'])
def get_image(gridfs_id):
    """
    Serves an image stored in GridFS based on its ID.
    """
    try:
        fs = current_app.extensions['grid_fs']
        file = fs.get(ObjectId(gridfs_id))
        return Response(file.read(), mimetype=file.content_type or 'image/jpeg')
    except gridfs.errors.NoFile:
        logger.error(f"No file found with GridFS ID {gridfs_id}.")
        return Response(status=404)
    except Exception as e:
        logger.error(f"Error retrieving image with GridFS ID {gridfs_id}: {e}")
        return Response(status=500)
