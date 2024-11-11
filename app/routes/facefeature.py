# app/routes/facefeature.py

import io
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import hashlib
import logging

from app.models.project import Project
from app.models.face import Face
from app.models.user import User
from app.utils.image_processing import allowed_file, is_image_file
from app.utils.ml_model import extract_features, process_new_images, find_matching_faces

bp = Blueprint('facefeature', __name__, url_prefix='/facefeature')

logger = logging.getLogger(__name__)

@bp.route('/imagesupload/<string:project_id>', methods=['POST'])
@jwt_required()
def upload_images_to_project(project_id):
    """
    Uploads multiple images to a specific project and processes them to detect faces.
    """
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()
    
    if not user:
        return jsonify({'message': 'User not found.'}), 404

    # Fetch the project and validate ownership
    project = Project.objects(id=project_id, user=user).first()
    if not project:
        return jsonify({'message': 'Project not found or not owned by user.'}), 404

    # Check if any files were uploaded
    if 'images' not in request.files:
        return jsonify({'message': 'No images part in the request.'}), 400

    files = request.files.getlist('images')
    image_data_list = []
    saved_faces = []

    grid_fs = current_app.extensions['grid_fs']  # Access GridFS via Flask app extensions

    for file in files:
        # Validate the file type by extension
        if file and allowed_file(file.filename):
            original_filename = secure_filename(file.filename)
            
            # Read image bytes without saving to disk
            image_bytes = file.read()

            # Validate MIME type by checking the file content
            if not is_image_file(io.BytesIO(image_bytes)):
                return jsonify({'message': f'Uploaded file {original_filename} is not a valid image.'}), 400

            # Generate a hash for the image to prevent duplicates
            hash_object = hashlib.sha256(image_bytes)
            image_hash = hash_object.hexdigest()

            # Check for existing Face with the same hash and project to prevent duplicates
            existing_face = Face.objects(hash=image_hash, project=project).first()
            if existing_face:
                saved_faces.append({
                    'face_id': str(existing_face.id),
                    'gridfs_id':str(existing_face.gridfs_id),
                    'message': 'Duplicate image detected.'
                })
                continue  # Skip processing this duplicate image

            # Store image in GridFS
            try:
                gridfs_id = grid_fs.put(image_bytes, filename=original_filename)
                logger.info(f"Stored image {original_filename} in GridFS with ID {gridfs_id}.")
            except Exception as e:
                logger.error(f"Error storing image {original_filename} in GridFS: {e}")
                return jsonify({'message': f'Error storing image {original_filename}.'}), 500

            # Create Face document
            try:
                new_face = Face(
                    gridfs_id=str(gridfs_id),
                    project=project,
                    hash=image_hash,
                    cluster_label=None,  # To be set after processing
                    encoding=None         # To be set after processing
                )
                new_face.save()
                # Verify that the document was saved
                if not Face.objects(id=new_face.id).first():
                    logger.error(f"Face document for image {original_filename} was not saved.")
                    raise Exception("Failed to save Face document.")
                logger.info(f"Created new Face document for image {original_filename} with ID {new_face.id}.")

                # **Link Face to Project**
                project.add_face(new_face)

            except Exception as e:
                logger.error(f"Error creating Face document for image {original_filename}: {e}")
                # Optionally, delete the image from GridFS if DB entry fails
                try:
                    grid_fs.delete(gridfs_id)
                    logger.info(f"Deleted image {original_filename} from GridFS due to DB error.")
                except Exception as del_e:
                    logger.error(f"Error deleting image {original_filename} from GridFS: {del_e}")
                return jsonify({'message': f'Error processing image {original_filename}.'}), 500

            # Collect image data for processing
            image_data = {
                'gridfs_id': str(gridfs_id),
                'original_filename': original_filename,
                'hash': image_hash  # Include hash to avoid recomputing
            }
            image_data_list.append(image_data)
        else:
            return jsonify({'message': f'File type not allowed for file {file.filename}.'}), 400

    if not image_data_list:
        return jsonify({'message': 'No new images to process.'}), 200

    # Process all uploaded images (feature extraction and clustering)
    try:
        process_new_images(image_data_list, project_id=project_id)
    except Exception as e:
        logger.error(f"Error processing images for project {project_id}: {e}")
        return jsonify({'message': 'Error processing images.', 'error': str(e)}), 500

    # After processing, retrieve the newly added faces to report
    for image_data in image_data_list:
        gridfs_id = image_data['gridfs_id']
        image_hash = image_data['hash']  # Use precomputed hash

        face = Face.objects(hash=image_hash, project=project).first()
        if face:
            saved_faces.append({
                'face_id': str(face.id),
                'gridfs_id':str(face.gridfs_id),
                'message': 'Image uploaded and processed successfully.'
            })
        else:
            logger.error(f"Face document with hash {image_hash} for project {project_id} not found after processing.")

    return jsonify({'saved_faces': saved_faces}), 201

@bp.route('/find_faces/<string:project_id>', methods=['POST'])
@jwt_required()
def find_matching_faces_route(project_id):
    """
    Uploads a query image to find matching faces within a specific project.
    """
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()
    
    if not user:
        return jsonify({'message': 'User not found.'}), 404

    project = Project.objects(id=project_id, user=user).first()
    if not project:
        return jsonify({'message': 'Project not found or not owned by user.'}), 404

    if 'image' not in request.files:
        return jsonify({'message': 'No image part in the request.'}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'message': 'No selected file.'}), 400
    
    # Validate file extension
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'})
    if '.' not in file.filename or \
       file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return jsonify({'message': 'Invalid file extension.'}), 400
    
    # Secure the filename
    filename = secure_filename(file.filename)

    # Read file bytes
    image_bytes = file.read()

    # Validate MIME type by checking the file content
    if not is_image_file(io.BytesIO(image_bytes)):
        return jsonify({'message': f'Uploaded file {filename} is not a valid image.'}), 400

    try:
        # Extract facial embeddings from the uploaded image
        query_embeddings = extract_features(image_bytes)
        if not query_embeddings:
            return jsonify({'message': 'No faces detected in the uploaded image.'}), 400
        logger.info(f"Extracted {len(query_embeddings)} face embeddings from the uploaded image.")
    except Exception as e:
        logger.error(f"Error extracting features from uploaded image {filename}: {e}")
        return jsonify({'message': 'Error processing the uploaded image.'}), 500

    try:
        # Find matching faces in the project based on embeddings
        related_image_ids = find_matching_faces(query_embeddings, project_id)
        logger.info(f"Found {len(related_image_ids)} related images for uploaded image {filename}.")
    except ValueError as ve:
        logger.error(f"ValueError during face matching: {ve}")
        return jsonify({'message': str(ve)}), 404
    except Exception as e:
        logger.error(f"Unexpected error during face matching: {e}")
        return jsonify({'message': 'An error occurred while matching faces.'}), 500

    if not related_image_ids:
        return jsonify({'message': 'No related images found.'}), 200

    return jsonify({
        'message': 'Image processed successfully.',
        'matching_images': related_image_ids
    }), 200
