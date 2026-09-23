from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from app.db.session import Base

JSONB_TYPE = JSONB().with_variant(JSON(), "sqlite")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)       # edit|override|delete|rule_change|role_change
    target_type = Column(String, nullable=False)  # scan|rule|user
    target_id = Column(Integer, nullable=False)
    old_value = Column(JSONB_TYPE, nullable=True)
    new_value = Column(JSONB_TYPE, nullable=True)
    reason = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
