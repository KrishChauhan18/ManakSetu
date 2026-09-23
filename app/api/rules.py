import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.domain import Rule, User
from app.schemas.rules import RuleCreate, RuleUpdate, RuleResponse
from app.api.auth import require_role
from app.core.audit import log_audit
from app.core.envelope import success_response, error_response

router = APIRouter(prefix="/rules", tags=["Rules"])

def _format_rule(r: Rule) -> dict:
    return {
        "id": r.id,
        "rule_id_str": r.rule_id_str,
        "legal_rule_ref": r.legal_rule_ref,
        "source_law": r.source_law or "Legal Metrology 2011",
        "field": r.field,
        "check_type": r.check_type,
        "pattern": r.pattern,
        "severity": r.severity,
        "category": r.category,
        "version": r.version,
        "enabled": r.enabled
    }

@router.get("/")
def list_rules(
    category: Optional[str] = None,
    enabled: Optional[bool] = None,
    version: Optional[str] = None,
    page: Optional[int] = Query(None, ge=1),
    page_size: Optional[int] = Query(None, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(Rule)
    if enabled is not None:
        query = query.filter(Rule.enabled == enabled)
    if version:
        query = query.filter(Rule.version == version)

    rules = query.all()
    if category and category != "all":
        rules = [r for r in rules if "all" in (r.category or []) or category in (r.category or [])]

    # If pagination parameters supplied
    if page is not None and page_size is not None:
        total = len(rules)
        total_pages = max(1, math.ceil(total / page_size))
        offset = (page - 1) * page_size
        paginated_rules = rules[offset:offset + page_size]
        return success_response({
            "items": [_format_rule(r) for r in paginated_rules],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages
            }
        })

    return success_response([_format_rule(r) for r in rules])

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_rule(
    rule_in: RuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    existing = db.query(Rule).filter(Rule.rule_id_str == rule_in.rule_id_str).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Rule ID '{rule_in.rule_id_str}' already exists.")

    rule = Rule(
        rule_id_str=rule_in.rule_id_str,
        legal_rule_ref=rule_in.legal_rule_ref if hasattr(rule_in, "legal_rule_ref") and rule_in.legal_rule_ref else "Rule 6",
        source_law=getattr(rule_in, "source_law", "Legal Metrology 2011") or "Legal Metrology 2011",
        field=rule_in.field,
        check_type=rule_in.check_type,
        pattern=rule_in.pattern,
        severity=rule_in.severity,
        category=rule_in.category,
        version=rule_in.version,
        enabled=rule_in.enabled
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    log_audit(
        db=db,
        user_id=current_user.id,
        action="rule_create",
        target_type="rule",
        target_id=rule.rule_id_str,
        old_value=None,
        new_value={"rule_id_str": rule.rule_id_str, "check_type": rule.check_type, "severity": rule.severity},
        reason="Rule created by Admin"
    )
    db.commit()

    return success_response(_format_rule(rule))

@router.put("/{rule_id_str}")
def update_rule(
    rule_id_str: str,
    rule_in: RuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    rule = db.query(Rule).filter(Rule.rule_id_str == rule_id_str).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    old_val = {
        "check_type": rule.check_type,
        "severity": rule.severity,
        "enabled": rule.enabled,
        "pattern": rule.pattern
    }

    update_data = rule_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)

    new_val = {
        "check_type": rule.check_type,
        "severity": rule.severity,
        "enabled": rule.enabled,
        "pattern": rule.pattern
    }

    log_audit(
        db=db,
        user_id=current_user.id,
        action="rule_change",
        target_type="rule",
        target_id=rule_id_str,
        old_value=old_val,
        new_value=new_val,
        reason="Rule updated by Admin"
    )

    db.commit()
    db.refresh(rule)
    return success_response(_format_rule(rule))

@router.delete("/{rule_id_str}")
def delete_rule(
    rule_id_str: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    rule = db.query(Rule).filter(Rule.rule_id_str == rule_id_str).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    old_val = {"rule_id_str": rule.rule_id_str, "severity": rule.severity}
    db.delete(rule)

    log_audit(
        db=db,
        user_id=current_user.id,
        action="rule_delete",
        target_type="rule",
        target_id=rule_id_str,
        old_value=old_val,
        new_value=None,
        reason="Rule deleted by Admin"
    )

    db.commit()
    return success_response({"message": f"Rule '{rule_id_str}' deleted successfully."})
