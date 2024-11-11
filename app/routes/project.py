# app/routes/project.py
from app.models.face import Face
from flask import Blueprint, request, jsonify
from app.models.project import Project
from app.models.user import User
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

bp = Blueprint('project', __name__, url_prefix='/project')

logger = logging.getLogger(__name__)

@bp.route('/create', methods=['POST'])
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

@bp.route('/user', methods=['GET'])
@jwt_required()
def get_user_projects():
    """
    Retrieves all projects associated with the authenticated user.
    """
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()

    if not user:
        return jsonify({'message': 'User not found.'}), 404

    projects = Project.objects(user=user)
    projects_data = [{
        'id': str(project.id),
        'p_name': project.p_name,
        'description': project.description,
        'user': str(project.user.id),
        # Add other project fields as needed
    } for project in projects]

    return jsonify(projects_data), 200

@bp.route('/getall', methods=['GET'])
@jwt_required()
def get_all_projects():
    """
    Retrieves all projects in the system.
    """
    projects = Project.objects()
    projects_data = [{
        'id': str(project.id),
        'p_name': project.p_name,
        'description': project.description,
        'user': str(project.user.id),
        # Add other project fields as needed
    } for project in projects]

    return jsonify(projects_data), 200

@bp.route('/<string:project_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
def manage_project(project_id):
    """
    Retrieves, updates, or deletes a specific project by its ID.
    """
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()

    if not user:
        return jsonify({'message': 'User not found.'}), 404

    project = Project.objects(id=project_id, user=user).first()

    if not project:
        return jsonify({'message': 'Project not found.'}), 404

    if request.method == 'GET':
        # Retrieve all faces associated with this project
        faces = Face.objects(project=project)

        # Compile face data with face_id and gridfs_id
        gridfs_ids = [str(face.gridfs_id) for face in faces]

        # Return project details along with associated faces and their gridfs_ids
        return jsonify({
            'id': str(project.id),
            'p_name': project.p_name,
            'description': project.description,
            'user': str(project.user.id),
            'grdifs_ids': gridfs_ids
        }), 200

    elif request.method == 'PUT':
        data = request.get_json()
        p_name = data.get('p_name')
        description = data.get('description')

        updated = False

        if p_name:
            # Check if another project with the same name exists for the user
            if Project.objects(p_name=p_name, user=user).exclude(id=project_id).first():
                return jsonify({'message': 'Project name already in use.'}), 409
            project.p_name = p_name
            updated = True

        if description is not None:
            project.description = description
            updated = True

        if not updated:
            return jsonify({'message': 'No valid fields to update.'}), 400

        try:
            project.save()
            logger.info(f"Project {project_id} updated by user {user.email}")
        except Exception as e:
            logger.error(f"Error updating project {project_id}: {e}")
            return jsonify({'message': 'Error updating project.'}), 500

        return jsonify({'message': 'Project updated successfully.'}), 200

    elif request.method == 'DELETE':
        try:
            project.delete()
            logger.info(f"Project {project_id} deleted by user {user.email}")
            return jsonify({'message': 'Project deleted successfully.'}), 200
        except Exception as e:
            logger.error(f"Error deleting project {project_id}: {e}")
            return jsonify({'message': 'Error deleting project.'}), 500
