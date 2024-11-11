# app/models/project.py

from mongoengine import Document, StringField, ReferenceField, ListField
from bson import ObjectId

class Project(Document):
    """
    Represents a project created by a user.
    """
    p_name = StringField(required=True)
    description = StringField()
    user = ReferenceField('User', required=True)
    faces = ListField(ReferenceField('Face'))
    
    meta = {
        'collection': 'projects',
        'indexes': [
            'p_name',
            'user'
        ]
    }
    
    def to_dict(self):
        """
        Serializes the project object to a dictionary.
        """
        return {
            'id': str(self.id),
            'p_name': self.p_name,
            'description': self.description,
            'user_id': str(self.user.id),
            'faces': [str(face.id) for face in self.faces]
        }
    
    def add_face(self, face):
        """
        Adds a Face document to the project's faces list.
        """
        if face not in self.faces:
            self.faces.append(face)
            self.save()
