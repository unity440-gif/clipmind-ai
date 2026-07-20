"""
Importing all models here ensures SQLAlchemy's Base knows about every table
before we try to create them. Any new model file must be imported here too.
"""

from models.user import User
from models.project import Project
from models.video import Video
from models.clip import Clip
