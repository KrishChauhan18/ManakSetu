from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, JSON
from app.db.database import Base

class ScanRecord(Base):
    """
    SQLAlchemy ORM model for storing audit scan records in SQLite.
    """
    __tablename__ = "scan_records"

    scan_id = Column(String(64), primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    image_path = Column(String(512), nullable=False)
    pdf_report_path = Column(String(512), nullable=True)
    is_compliant = Column(Boolean, nullable=False, default=False)
    compliance_score = Column(Float, nullable=False, default=0.0)
    extracted_fields = Column(JSON, nullable=True)
    violations = Column(JSON, nullable=True)
    mean_confidence = Column(Float, nullable=True, default=0.0)
