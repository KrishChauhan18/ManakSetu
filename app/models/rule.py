from sqlalchemy import Column, Integer, String, Boolean, JSON
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from app.db.session import Base

JSONB_TYPE = JSONB().with_variant(JSON(), "sqlite")
ARRAY_TYPE = ARRAY(String).with_variant(JSON(), "sqlite")

class Rule(Base):
    __tablename__ = "rules"
    id = Column(Integer, primary_key=True, index=True)
    rule_id_str = Column(String, unique=True, nullable=False)
    legal_rule_ref = Column(String, nullable=True)
    source_law = Column(String, nullable=True)
    field = Column(String, nullable=False)
    check_type = Column(String, nullable=False)
    pattern = Column(JSONB_TYPE, nullable=True)
    severity = Column(String, nullable=False)
    category = Column(ARRAY_TYPE, nullable=False)
    version = Column(String, nullable=False)
    enabled = Column(Boolean, default=True)
