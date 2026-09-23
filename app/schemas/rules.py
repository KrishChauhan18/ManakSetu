from typing import Optional, Union, List, Any
from pydantic import BaseModel

class RuleBase(BaseModel):
    rule_id_str: str
    legal_rule_ref: Optional[str] = "Rule 6"
    source_law: Optional[str] = "Legal Metrology 2011"
    field: Union[str, List[str]]
    check_type: str
    pattern: Optional[Any] = None
    severity: str
    category: List[str] = ["all"]
    version: str = "2011"
    enabled: bool = True

class RuleCreate(RuleBase):
    pass

class RuleUpdate(BaseModel):
    legal_rule_ref: Optional[str] = None
    source_law: Optional[str] = None
    field: Optional[Union[str, List[str]]] = None
    check_type: Optional[str] = None
    pattern: Optional[Any] = None
    severity: Optional[str] = None
    category: Optional[List[str]] = None
    version: Optional[str] = None
    enabled: Optional[bool] = None

class RuleResponse(RuleBase):
    id: int

    class Config:
        from_attributes = True
