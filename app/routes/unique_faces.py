# app/routes/unique_faces.py

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from app.models.project import Project
from app.models.user import User
from app.utils.ml_model import get_unique_faces_for_project

bp = Blueprint('unique_faces', __name__, url_prefix='/api/projects')

logger = logging.getLogger(__name__)

@bp.route('/<project_id>/unique_faces', methods=['GET'])
@jwt_required()
def unique_faces(project_id):
    """
    Retrieves unique faces (clusters) within a specific project.
    """
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()

    if not user:
        return jsonify({'message': 'User not found.'}), 404

    project = Project.objects(id=project_id, user=user).first()
    if not project:
        return jsonify({'message': 'Project not found or not owned by user.'}), 404

    try:
        unique_faces_list = get_unique_faces_for_project(project_id)
        if not unique_faces_list:
            return jsonify({'message': 'No unique faces found in the project.'}), 404
    except Exception as e:
        logger.error(f"Error retrieving unique faces for project {project_id}: {e}")
        return jsonify({'message': 'Error retrieving unique faces.', 'error': str(e)}), 500

    return jsonify({
        'message': 'Unique faces retrieved successfully.',
        'unique_faces': unique_faces_list
    }), 200
