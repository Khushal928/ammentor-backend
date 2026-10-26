import csv
import io
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Response
from sqlalchemy.orm import Session
from app.db.db import get_db
from app.db import models
from app.crud.auth import get_current_user

router = APIRouter()


@router.get("/reports/export")
def export_claims_csv(
    group_id: Optional[int] = Query(None, description="Filter by MITHRA vertical"),
    event_level: Optional[models.EventLevel] = Query(None, description="Filter by event level"),
    status: Optional[models.ClaimStatus] = Query(None, description="Filter by claim status"),
    start_date: Optional[date] = Query(None, description="Filter claims submitted on or after this date"),
    end_date: Optional[date] = Query(None, description="Filter claims submitted on or before this date"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Export claims report as CSV per Section 10 of briefing document.
    Authorized for Program Admin and Super Admin only.
    """
    if current_user.role not in (models.UserRole.PROGRAM_ADMIN, models.UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Only Program Admins can export reporting data.")

    query = db.query(models.Claim)

    if group_id:
        query = query.filter(models.Claim.group_id == group_id)
    if event_level:
        query = query.filter(models.Claim.event_level == event_level)
    if status:
        query = query.filter(models.Claim.status == status)
    if start_date:
        query = query.filter(models.Claim.event_start_date >= start_date)
    if end_date:
        query = query.filter(models.Claim.event_end_date <= end_date)

    claims = query.order_by(models.Claim.submitted_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Claim ID",
        "Student Roll No",
        "Student Name",
        "Department",
        "Student Email",
        "MITHRA Vertical",
        "Event Name",
        "Event Level",
        "Participation Category",
        "Event Start Date",
        "Event End Date",
        "Organising Body",
        "Status",
        "Points Awarded",
        "Evaluated By",
        "Submitted At",
        "Approved At",
        "Rejection Reason",
        "Supporting Link",
    ])

    for c in claims:
        writer.writerow([
            c.id,
            c.submitter.roll_number if c.submitter else "",
            c.submitter.name if c.submitter else "",
            c.submitter.department if c.submitter else "",
            c.submitter.email if c.submitter else "",
            c.group.title if c.group else "",
            c.event_name,
            c.event_level.value if c.event_level else "",
            c.participation_category.value if c.participation_category else "",
            c.event_start_date.isoformat() if c.event_start_date else "",
            c.event_end_date.isoformat() if c.event_end_date else "",
            c.organising_body,
            c.status.value if c.status else "",
            c.points or 0,
            c.evaluated_by_mentor.name if c.evaluated_by_mentor else "",
            c.submitted_at.isoformat() if c.submitted_at else "",
            c.approved_at.isoformat() if c.approved_at else "",
            c.rejection_reason or "",
            c.supporting_link or "",
        ])

    csv_data = output.getvalue()
    filename = f"mithra_claims_report_{date.today().isoformat()}.csv"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
