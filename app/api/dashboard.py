from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import Optional

from app.db.session import get_db
from app.models.domain import Scan, Violation, Rule
from app.pipeline.risk_model import risk_scorer
from app.core.envelope import success_response

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats")
def get_dashboard_stats(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Scan)
    if category and category != "all":
        query = query.filter(Scan.category == category)

    total_scans = query.count()
    if total_scans == 0:
        return success_response({
            "total_scans": 0,
            "overall_compliance_pct": 100.0,
            "severity_breakdown": {"critical": 0, "high": 0, "medium": 0, "low": 0, "manual_review": 0}
        })

    avg_compliance = query.with_entities(func.avg(Scan.compliance_pct)).scalar() or 100.0
    
    # Severity breakdown
    v_query = db.query(Violation.severity, func.count(Violation.id)).join(Scan, Violation.scan_id == Scan.id)
    if category and category != "all":
        v_query = v_query.filter(Scan.category == category)

    severity_counts = v_query.group_by(Violation.severity).all()

    breakdown = {"critical": 0, "high": 0, "medium": 0, "low": 0, "manual_review": 0}
    for sev, count in severity_counts:
        if sev in breakdown:
            breakdown[sev] = count

    return success_response({
        "total_scans": total_scans,
        "overall_compliance_pct": round(float(avg_compliance), 2),
        "severity_breakdown": breakdown
    })

@router.get("/trend")
def get_compliance_trend(
    days: int = Query(30, ge=1, le=365),
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    start_date = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(
        func.date(Scan.created_at).label("scan_date"),
        func.avg(Scan.compliance_pct).label("avg_pct"),
        func.count(Scan.id).label("count")
    ).filter(Scan.created_at >= start_date)

    if category and category != "all":
        query = query.filter(Scan.category == category)

    scans = query.group_by(func.date(Scan.created_at)).order_by(func.date(Scan.created_at)).all()

    trend = [
        {
            "date": str(s.scan_date),
            "avg_compliance_pct": round(float(s.avg_pct), 2),
            "scan_count": s.count
        } for s in scans
    ]

    return success_response({"days": days, "trend": trend})

@router.get("/top-violations")
def get_top_violations(
    limit: int = Query(5, ge=1, le=20),
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(
        Violation.rule_id,
        Violation.field,
        Violation.severity,
        func.count(Violation.id).label("violation_count")
    ).join(Scan, Violation.scan_id == Scan.id)

    if category and category != "all":
        query = query.filter(Scan.category == category)

    top = query.group_by(Violation.rule_id, Violation.field, Violation.severity)\
               .order_by(desc("violation_count"))\
               .limit(limit).all()

    return success_response([
        {
            "rule_id": t.rule_id,
            "field": t.field,
            "severity": t.severity,
            "count": t.violation_count
        } for t in top
    ])

@router.get("/manufacturer-ranking")
def get_manufacturer_ranking(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Scan).filter(Scan.label_record.isnot(None))
    if category and category != "all":
        query = query.filter(Scan.category == category)

    scans = query.all()
    
    mfr_stats = {}
    for s in scans:
        rec = s.label_record or {}
        mfr_name = "Unknown Manufacturer"
        if rec.get("manufacturer") and rec["manufacturer"].get("value"):
            mfr_name = rec["manufacturer"]["value"]
        elif rec.get("manufacturer_name") and rec["manufacturer_name"].get("value"):
            mfr_name = rec["manufacturer_name"]["value"]

        if mfr_name not in mfr_stats:
            mfr_stats[mfr_name] = {"scans": 0, "total_pct": 0.0, "violations": 0}

        mfr_stats[mfr_name]["scans"] += 1
        mfr_stats[mfr_name]["total_pct"] += s.compliance_pct

    ranking = []
    for mfr, data in mfr_stats.items():
        avg_pct = round(data["total_pct"] / data["scans"], 2)
        ranking.append({
            "manufacturer_name": mfr,
            "total_scans": data["scans"],
            "avg_compliance_pct": avg_pct
        })

    ranking.sort(key=lambda x: x["avg_compliance_pct"])
    return success_response(ranking)

@router.get("/risk-priority")
def get_risk_priority(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Scan)
    if category and category != "all":
        query = query.filter(Scan.category == category)

    scans = query.all()
    
    mfr_data = {}
    for s in scans:
        rec = s.label_record or {}
        mfr_name = "Unknown Manufacturer"
        if rec.get("manufacturer") and rec["manufacturer"].get("value"):
            mfr_name = rec["manufacturer"]["value"]
        elif rec.get("manufacturer_name") and rec["manufacturer_name"].get("value"):
            mfr_name = rec["manufacturer_name"]["value"]

        if mfr_name not in mfr_data:
            mfr_data[mfr_name] = {
                "scans": 0, "violations": 0, "crit_violations": 0,
                "confs": [], "last_date": s.created_at
            }
        
        mfr_data[mfr_name]["scans"] += 1
        if s.compliance_pct < 100:
            mfr_data[mfr_name]["violations"] += 1
        
        for fkey, fval in rec.items():
            if isinstance(fval, dict) and "confidence" in fval:
                mfr_data[mfr_name]["confs"].append(fval["confidence"])

    priorities = []
    for mfr, d in mfr_data.items():
        hist_rate = d["violations"] / d["scans"] if d["scans"] > 0 else 0.0
        avg_conf = float(sum(d["confs"]) / len(d["confs"])) if d["confs"] else 0.85
        days_since = (datetime.utcnow() - d["last_date"]).days if d["last_date"] else 0
        
        score = risk_scorer.calculate_priority(
            hist_rate=hist_rate,
            crit_count=d["crit_violations"],
            avg_conf=avg_conf,
            days_since=days_since
        )

        priorities.append({
            "manufacturer_name": mfr,
            "total_scans": d["scans"],
            "violation_rate": round(hist_rate, 2),
            "priority_risk_score": score,
            "recommendation": "High Priority Audit" if score > 0.60 else ("Medium Audit Priority" if score > 0.35 else "Low Priority")
        })

    priorities.sort(key=lambda x: x["priority_risk_score"], reverse=True)
    return success_response(priorities)
