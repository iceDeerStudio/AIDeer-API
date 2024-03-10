from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship, column_property
from sqlalchemy.sql import func, select
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from orm_models.usage import UsageORM


class UserORM(db.Model):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    nickname = Column(String(64))
    password_hash = Column(String(192), nullable=False)
    permission_level = Column(Integer, default=1)
    wechat_openid = Column(String(64), unique=True, nullable=True)
    wechat_session_key = Column(String(64), nullable=True)
    owned_chats = relationship("ChatORM")
    owned_presets = relationship("PresetORM")
    avatar = Column(String(64), nullable=True)
    is_deleted = Column(Boolean, default=False)
    total_credits = Column(Integer, default=0)
    total_usage = column_property(
        select(func.sum(UsageORM.token_used))
        .where(UsageORM.user_id == id)
        .correlate_except(UsageORM)
        .scalar_subquery()
    )
    credits_left = column_property(total_credits - total_usage)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "nickname": self.nickname,
            "permission_level": self.permission_level,
            "total_credits": self.total_credits,
            "total_usage": self.total_usage,
            "credits_left": self.credits_left,
            "avatar": f"/users/{self.id}/avatar",
        }


class TokenBlocklistORM(db.Model):
    __tablename__ = "token_blocklist"
    id = Column(Integer, primary_key=True)
    jti = Column(String(36), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
