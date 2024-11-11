# app/routes/uniquefaces.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from app.models.project import Project
from app.models.face import Face
from app.models.user import User
from app.utils.ml_model import get_unique_faces_for_project

bp = Blueprint('uniquefaces', __name__, url_prefix='/uniquefaces')

logger = logging.getLogger(__name__)

@bp.route('/<string:project_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
def handle_unique_faces(project_id):
    """
    Retrieves, updates, or deletes unique faces within a specific project.
    """
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()

    if not user:
        return jsonify({'message': 'User not found.'}), 404

    project = Project.objects(id=project_id, user=user).first()
    if not project:
        return jsonify({'message': 'Project not found or not owned by user.'}), 404

    if request.method == 'GET':
        try:
            unique_faces_list = get_unique_faces_for_project(project_id)
            if not unique_faces_list:
                return jsonify({'message': 'No unique faces found in the project.'}), 404
        except Exception as e:
            logger.error(f"Error retrieving unique faces for project {project_id}: {e}")
            return jsonify({'message': 'Error retrieving unique faces.', 'error': str(e)}), 500

        return jsonify({
            'unique_faces': unique_faces_list
        }), 200

    elif request.method == 'PUT':
        data = request.get_json()
        face_id = data.get('face_id')
        cluster_label = data.get('cluster_label')

        if not face_id or not cluster_label:
            return jsonify({'message': 'face_id and cluster_label are required.'}), 400

        face = Face.objects(id=face_id, project=project).first()
        if not face:
            return jsonify({'message': 'Face not found.'}), 404

        face.cluster_label = cluster_label
        try:
            face.save()
            logger.info(f"Face {face_id} updated with new cluster label {cluster_label}.")
        except Exception as e:
            logger.error(f"Error updating face {face_id}: {e}")
            return jsonify({'message': 'Error updating unique face.'}), 500

        return jsonify({'message': 'Unique face updated successfully.'}), 200

    elif request.method == 'DELETE':
        data = request.get_json()
        face_id = data.get('face_id')

        if not face_id:
            return jsonify({'message': 'face_id is required.'}), 400

        face = Face.objects(id=face_id, project=project).first()
        if not face:
            return jsonify({'message': 'Face not found.'}), 404

        try:
            face.delete()
            logger.info(f"Face {face_id} deleted from project {project_id}.")
            return jsonify({'message': 'Unique face deleted successfully.'}), 200
        except Exception as e:
            logger.error(f"Error deleting face {face_id}: {e}")
            return jsonify({'message': 'Error deleting unique face.'}), 500
