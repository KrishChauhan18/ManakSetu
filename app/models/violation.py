from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.db.session import Base

JSONB_TYPE = JSONB().with_variant(JSON(), "sqlite")

class Violation(Base):
    __tablename__ = "violations"
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False)
    rule_id = Column(String, nullable=False)
    legal_rule_ref = Column(String, nullable=True)
    source_law = Column(String, nullable=True)
    field = Column(String, nullable=False)
    severity = Column(String, nullable=False)   # critical|high|medium|low
    status = Column(String, nullable=False)     # fail|needs_review
    detected_value = Column(String, nullable=True)
    expected = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    bbox = Column(JSONB_TYPE, nullable=True)
    reason = Column(String, nullable=True)
    message = Column(String, nullable=True)
    recommendation = Column(String, nullable=True)

    scan = relationship("Scan", back_populates="violations")
