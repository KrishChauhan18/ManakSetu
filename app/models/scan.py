from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

JSONB_TYPE = JSONB().with_variant(JSON(), "sqlite")

class Scan(Base):
    __tablename__ = "scans"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # allows anonymous/guest inspection if needed
    image_path = Column(String, nullable=False)
    category = Column(String, nullable=False)
    status = Column(String, default="processing")  # processing|done|failed|needs_review
    label_record = Column(JSONB_TYPE, nullable=True)     # <-- OCR output lands here, see §2.3
    compliance_pct = Column(Float, nullable=True)
    gps_lat = Column(Float, nullable=True)
    gps_lng = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="scans", foreign_keys=[user_id])
    violations = relationship("Violation", back_populates="scan", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="scan", cascade="all, delete-orphan")
