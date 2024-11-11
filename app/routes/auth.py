# app/routes/auth.py

from flask import Blueprint, request, jsonify
from app.models.user import User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import logging

bp = Blueprint('auth', __name__, url_prefix='/auth')

logger = logging.getLogger(__name__)

@bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email and password are required.'}), 400

    if User.objects(email=email).first():
        return jsonify({'message': 'User already exists.'}), 409

    try:
        new_user = User(email=email)
        new_user.set_password(password)
        new_user.save()
        logger.info(f"New user created: {email}")
    except Exception as e:
        logger.error(f"Error creating user {email}: {e}")
        return jsonify({'message': 'Error creating user.'}), 500

    return jsonify({'message': 'User created successfully.'}), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email and password are required.'}), 400

    user = User.objects(email=email).first()

    if user and user.check_password(password):
        access_token = create_access_token(identity=str(user.id))
        logger.info(f"User logged in: {email}")
        return jsonify({'access_token': access_token}), 200

    return jsonify({'message': 'Invalid credentials.'}), 401

@bp.route('/profile', methods=['GET', 'PUT'])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()

    if not user:
        return jsonify({'message': 'User not found.'}), 404

    if request.method == 'GET':
        return jsonify({
            'id': str(user.id),
            'email': user.email,
            'projects': [str(project.id) for project in user.projects],
            'is_admin': user.is_admin
        }), 200

    elif request.method == 'PUT':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if email:
            if User.objects(email=email).exclude(id=user_id).first():
                return jsonify({'message': 'Email already in use.'}), 409
            user.email = email

        if password:
            user.set_password(password)

        try:
            user.save()
            logger.info(f"User profile updated: {email if email else user.email}")
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return jsonify({'message': 'Error updating profile.'}), 500

        return jsonify({'message': 'Profile updated successfully.'}), 200
