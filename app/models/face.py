# app/models/face.py

from mongoengine import Document, StringField, ReferenceField
from bson import ObjectId
import json
import numpy as np

class Face(Document):
    """
    Represents a face (image) associated with a project.
    """
    hash = StringField(required=True)
    project = ReferenceField('Project', required=True)
    gridfs_id = StringField(required=True)
    cluster_label = StringField()  # Changed from IntField to StringField
    encoding = StringField()  # Store serialized facial embeddings
    
    meta = {
        'collection': 'faces',
        'indexes': [
            'hash',
            'project'
        ]
    }
    
    def to_dict(self):
        """
        Serializes the face object to a dictionary.
        """
        return {
            'id': str(self.id),
            'hash': self.hash,
            'project_id': str(self.project.id),
            'gridfs_id': self.gridfs_id,
            'cluster_label': self.cluster_label,
            'encoding': self.encoding
        }
    
    def set_encoding(self, encoding_array):
        """
        Serializes and sets the facial embedding.

        Args:
            encoding_array (np.ndarray): Facial embedding array.
        """
        self.encoding = json.dumps(encoding_array.tolist())

    def get_encoding(self):
        """
        Deserializes and retrieves the facial embedding.

        Returns:
            np.ndarray: Facial embedding array.
        """
        return np.array(json.loads(self.encoding))
