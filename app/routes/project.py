# app/routes/project.py

from flask import Blueprint, request, jsonify
from app.models.project import Project
from app.models.user import User
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

bp = Blueprint('project', __name__, url_prefix='/api/projects')

logger = logging.getLogger(__name__)

@bp.route('', methods=['POST'])
@jwt_required()
def create_project():
    """
    Creates a new project for the authenticated user.
    """
    data = request.get_json()
    p_name = data.get('p_name')
    description = data.get('description', '')

    if not p_name:
        return jsonify({'message': 'Project name is required.'}), 400

    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()

    if not user:
        return jsonify({'message': 'User not found.'}), 404

    # Check if project with the same name exists for the user
    if Project.objects(p_name=p_name, user=user).first():
        return jsonify({'message': 'Project with this name already exists.'}), 409

    try:
        new_project = Project(p_name=p_name, description=description, user=user)
        new_project.save()
        logger.info(f"New project created: {p_name} by user {user.email}")
    except Exception as e:
        logger.error(f"Error creating project {p_name}: {e}")
        return jsonify({'message': 'Error creating project.'}), 500

    return jsonify({'message': 'Project created successfully.', 'project_id': str(new_project.id)}), 201

@bp.route('/<string:project_id>', methods=['GET', 'PUT'])
@jwt_required()
def profile(project_id):
    """
    Retrieves or updates a specific project by its ID.
    """
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()

    if not user:
        return jsonify({'message': 'User not found.'}), 404

    project = Project.objects(id=project_id, user=user).first()

    if not project:
        return jsonify({'message': 'Project not found.'}), 404

    if request.method == 'GET':
        return jsonify({
            'id': str(project.id),
            'p_name': project.p_name,
            'description': project.description,
            'faces': [str(face.id) for face in project.faces]
        }), 200

    elif request.method == 'PUT':
        data = request.get_json()
        p_name = data.get('p_name')
        description = data.get('description')

        if p_name:
            if Project.objects(p_name=p_name, user=user).exclude(id=project_id).first():
                return jsonify({'message': 'Project name already in use.'}), 409
            project.p_name = p_name

        if description is not None:
            project.description = description

        try:
            project.save()
            logger.info(f"Project {project_id} updated by user {user.email}")
        except Exception as e:
            logger.error(f"Error updating project {project_id}: {e}")
            return jsonify({'message': 'Error updating project.'}), 500

        return jsonify({'message': 'Project updated successfully.'}), 200
