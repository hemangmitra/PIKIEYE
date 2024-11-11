# app/utils/ml_model.py

import os
import cv2
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import normalize
import insightface
from insightface.app import FaceAnalysis
import logging
import io
from bson import ObjectId
from app.models.project import Project
from app.models.face import Face
import torch
import json
from flask import current_app

# Configure logging
logger = logging.getLogger(__name__)

# Initialize the InsightFace application as a singleton
class InsightFaceSingleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InsightFaceSingleton, cls).__new__(cls)
            try:
                if torch.cuda.is_available():
                    ctx_id = 0
                    logger.info("GPU is available. Using GPU for face analysis.")
                else:
                    ctx_id = -1
                    logger.info("GPU is not available. Using CPU for face analysis.")
                
                cls._instance.app_insight = FaceAnalysis()
                cls._instance.app_insight.prepare(ctx_id=ctx_id, det_size=(640, 640))
                logger.info("InsightFace model initialized successfully.")
            except Exception as e:
                logger.error(f"Error initializing InsightFace: {e}")
                cls._instance = None
        return cls._instance

app_insight_singleton = InsightFaceSingleton()
if app_insight_singleton.app_insight is None:
    logger.error("Failed to initialize InsightFace model.")

def preprocess_image(image_bytes):
    try:
        img_array = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is None:
            logger.error("Failed to decode image bytes.")
            return None
        return img
    except Exception as e:
        logger.error(f"Error in image preprocessing: {e}")
        return None

def extract_features(image_bytes):
    img = preprocess_image(image_bytes)
    if img is None:
        logger.error("Image preprocessing returned None.")
        return []
    
    if app_insight_singleton.app_insight is None:
        logger.error("InsightFace model is not initialized.")
        return []
    
    try:
        faces = app_insight_singleton.app_insight.get(img)
        logger.info(f"Detected {len(faces)} faces in the image.")
        face_embeddings = [face.embedding for face in faces if hasattr(face, 'embedding')]
        return face_embeddings
    except Exception as e:
        logger.error(f"Error during feature extraction: {e}")
        return []

def process_new_images(image_data_list, project_id, eps=0.5, min_samples=1):
    logger.info(f"Starting processing of {len(image_data_list)} images for project {project_id}.")

    embeddings = []
    face_ids = []
    for image_data in image_data_list:
        gridfs_id = image_data['gridfs_id']
        try:
            grid_fs = current_app.extensions['grid_fs']
            image_bytes = grid_fs.get(ObjectId(gridfs_id)).read()
        except Exception as e:
            logger.error(f"Error retrieving image {gridfs_id} from GridFS: {e}")
            continue  # Skip this image
        
        image_embeddings = extract_features(image_bytes)
        if not image_embeddings:
            logger.warning(f"No faces detected in image {gridfs_id}.")
            continue  # Skip images with no faces
        
        for embedding in image_embeddings:
            embeddings.append(embedding)
            face_ids.append(image_data['gridfs_id'])

    if not embeddings:
        logger.warning("No valid embeddings extracted from the uploaded images.")
        return

    embeddings = np.array(embeddings)
    embeddings_normalized = normalize(embeddings)

    try:
        clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine').fit(embeddings_normalized)
        labels = clustering.labels_
        logger.info(f"DBSCAN clustering completed with {len(set(labels))} clusters.")
    except Exception as e:
        logger.error(f"Error during DBSCAN clustering: {e}")
        raise

    for face_id, label, embedding in zip(face_ids, labels, embeddings):
        try:
            face = Face.objects(gridfs_id=face_id, project=project_id).first()
            if face:
                face.cluster_label = str(label)
                face.set_encoding(embedding)
                face.save()
                logger.debug(f"Updated Face {face.id} with cluster_label={label}.")
            else:
                logger.warning(f"Face document with gridfs_id={face_id} not found.")
        except Exception as e:
            logger.error(f"Error updating Face document {face_id}: {e}")

# app/utils/ml_model.py

def find_matching_faces(query_embeddings, project_id, tolerance=0.6):
    """
    Find and return all images in the project that have faces matching the query embeddings.

    Args:
        query_embeddings (List[np.ndarray]): List of facial embeddings from the query image.
        project_id (str): ID of the project to search within.
        tolerance (float, optional): Threshold for face matching. Defaults to 0.6.

    Returns:
        List[str]: List of GridFS IDs of images with matching faces.

    Raises:
        ValueError: If the project is not found or no faces are detected in the project.
    """
    logger.debug(f"Starting face matching for project_id={project_id} with tolerance={tolerance}")
    project = Project.objects(id=project_id).first()
    if not project:
        logger.error(f"Project with ID {project_id} not found.")
        raise ValueError("Project not found.")

    faces = project.faces
    logger.debug(f"Found {len(faces)} faces in the project.")
    if not faces:
        logger.info("No faces found in the project.")
        return []

    # Convert QuerySet to list to ensure it's indexable
    project_faces = list(Face.objects(id__in=[face.id for face in faces if face.encoding]))
    logger.debug(f"Found {len(project_faces)} project faces with valid encodings.")
    if not project_faces:
        logger.info("No valid face encodings found in the project.")
        return []

    project_embeddings = []
    for face in project_faces:
        try:
            encoding = face.get_encoding()
            project_embeddings.append(encoding)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decoding error for Face ID {face.id}: {e}")
            continue  # Skip this face
        except Exception as e:
            logger.error(f"Unexpected error decoding encoding for Face ID {face.id}: {e}")
            continue  # Skip this face

    if not project_embeddings:
        logger.error("No valid embeddings found after decoding.")
        raise Exception("No valid embeddings available for matching.")

    logger.debug(f"Collected {len(project_embeddings)} embeddings for matching.")
    project_embeddings = np.array(project_embeddings)
    project_embeddings_normalized = normalize(project_embeddings)
    logger.debug("Normalized project embeddings.")

    related_image_ids = set()

    for query_idx, query_embedding in enumerate(query_embeddings):
        try:
            query_embedding_normalized = normalize([query_embedding])[0]
            similarities = np.dot(project_embeddings_normalized, query_embedding_normalized)
            matches = np.where(similarities > tolerance)[0].tolist()  # Convert to list of integers
            logger.debug(f"Query Embedding {query_idx + 1}: Found {len(matches)} matches with tolerance {tolerance}.")

            for idx in matches:
                # Ensure idx is a standard Python int
                matching_face = project_faces[int(idx)]
                related_image_ids.add(matching_face.gridfs_id)
                logger.debug(f"Match Found: Query Embedding {query_idx + 1} matches with Image ID {matching_face.gridfs_id} (Similarity: {similarities[idx]:.2f})")
        except Exception as e:
            logger.error(f"Error processing query embedding {query_idx + 1}: {e}")
            continue  # Skip this query embedding

    logger.debug(f"Total matching images: {len(related_image_ids)}")

    return list(related_image_ids)



def get_unique_faces_for_project(project_id):
    project = Project.objects(id=project_id).first()
    if not project:
        logger.error(f"Project with ID {project_id} not found.")
        return []

    faces = Face.objects(project=project_id).exclude(cluster_label="-1").order_by('cluster_label')

    if not faces:
        logger.info("No faces found in the project.")
        return []

    unique_faces = {}
    for face in faces:
        label = face.cluster_label
        if label not in unique_faces:
            unique_faces[label] = face

    unique_faces_list = []
    for label, face in unique_faces.items():
        unique_faces_list.append({
            'cluster_label': label,
            'face_id': str(face.id),
            'gridfs_id': face.gridfs_id,
            'image_url': f"{current_app.config.get('BASE_URL')}/api/gridfs/{face.gridfs_id}"  # Ensure BASE_URL is set
        })

    logger.info(f"Retrieved {len(unique_faces_list)} unique faces for project {project_id}.")

    return unique_faces_list
