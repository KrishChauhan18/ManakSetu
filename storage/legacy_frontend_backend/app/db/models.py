from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.sql import func

from app.db.database import Base


class Officer(Base):
    __tablename__ = "officers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)

    # Human-readable inspection ID
    scan_id = Column(String(50), unique=True, nullable=False, index=True)

    # Officer who created the inspection
    inspector_id = Column(
        Integer,
        ForeignKey("officers.id"),
        nullable=False,
        index=True
    )

    # Product information
    product = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)
    manufacturer = Column(String(255), nullable=True)

    # Inspection result
    result = Column(String(30), nullable=True)
    score = Column(Integer, nullable=True)

    # Location information
    region = Column(String(100), nullable=True)
    location = Column(Text, nullable=True)

    # Uploaded image
    image_url = Column(Text, nullable=False)
    image_public_id = Column(String(255), nullable=True)

    # OCR extracted fields
    # Will be populated after your ML teammate's OCR API is ready
    extracted = Column(JSON, nullable=True)

    # Rule/compliance results
    # Will be populated when compliance checking is connected
    rules = Column(JSON, nullable=True)

    # Current processing state
    status = Column(String(30), default="uploaded", nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )