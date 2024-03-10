from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from extensions import db
from uuid import uuid4
import json

class PresetORM(db.Model):
    __tablename__ = "presets"
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), default=lambda: str(uuid4()), unique=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(64), nullable=False)
    description = Column(String(255), nullable=True)
    avatar = Column(String(64), nullable=True)
    content = Column(Text, nullable=False)
    type = Column(String(64), nullable=False)
    visibility = Column(String(16), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    def to_dict(self):
        content_obj = json.loads(self.content)
        return {
            "id": self.id,
            "uuid": self.uuid,
            "owner_id": self.owner_id,
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "avatar": self.avatar,
            "content": content_obj,
            "visibility": self.visibility,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    def get_content(self):
        return json.loads(self.content)

