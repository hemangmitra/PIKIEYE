# app/models/user.py

from mongoengine import Document, StringField, ListField, ReferenceField
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId

class User(Document):
    """
    Represents a user of the application.
    """
    email = StringField(required=True, unique=True)
    password_hash = StringField(required=True)
    projects = ListField(ReferenceField('Project'))
    is_admin = StringField(default='false')  # 'true' or 'false'
    
    meta = {
        'collection': 'users',
        'indexes': [
            'email',
        ]
    }
    
    def set_password(self, password):
        """
        Hashes and sets the user's password.
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """
        Checks if the provided password matches the stored hash.
        
        Args:
            password (str): The plaintext password to verify.
        
        Returns:
            bool: True if the password matches, False otherwise.
        """
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """
        Serializes the user object to a dictionary.
        """
        return {
            'id': str(self.id),
            'email': self.email,
            'projects': [str(project.id) for project in self.projects],
            'is_admin': self.is_admin
        }
