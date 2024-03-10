from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from extensions import db
from uuid import uuid4
import json

class ChatORM(db.Model):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), default=lambda: str(uuid4()), unique=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    preset_id = Column(Integer, ForeignKey("presets.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    task_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    def to_dict(self):
        content_obj = json.loads(self.content)
        return {
            "id": self.id,
            "uuid": self.uuid,
            "owner_id": self.owner_id,
            "preset_id": self.preset_id,
            "title": self.title,
            "content": content_obj,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    def get_content(self):
        return json.loads(self.content)
    
    def add_message(self, message):
        content_obj = json.loads(self.content)
        content_obj.append(message)
        self.content = json.dumps(content_obj)
        db.session.commit()

