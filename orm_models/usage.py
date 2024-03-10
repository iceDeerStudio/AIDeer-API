from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from extensions import db

class UsageORM(db.Model):
    __tablename__ = "usages"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token_used = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())