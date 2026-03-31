from fastapi import APIRouter, Depends, Form, Request, Query, HTTPException, BackgroundTasks
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional, List
from models import Leave
from schemas import LeaveRequest, LeaveResponse
from database import get_db, get_current_user, log_action

router = APIRouter()


@router.get("/leaves/{leave_id}/approve")
def approve_get(leave_id: int, token: str = Query(...), db: Session = Depends(get_db)):
    get_current_user(token)
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if leave:
        leave.status = "approved"
        db.commit()
        log_action(f"Leave {leave.id} approved for {leave.employee_name}")
    return RedirectResponse(url=f"/manager-page?token={token}", status_code=303)


@router.get("/leaves/{leave_id}/reject")
def reject_get(leave_id: int, token: str = Query(...), db: Session = Depends(get_db)):
    get_current_user(token)
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if leave:
        leave.status = "rejected"
        db.commit()
        log_action(f"Leave {leave.id} rejected for {leave.employee_name}")
    return RedirectResponse(url=f"/manager-page?token={token}", status_code=303)


@router.post("/apply-leave")
def apply_leave_form(
    request:       Request,
    employee_name: str = Form(...),
    leave_type:    str = Form(...),
    start_date:    str = Form(...),
    end_date:      str = Form(...),
    reason:        str = Form(...),
    token:         str = Form(...),
    db: Session = Depends(get_db)
):
    get_current_user(token)
    new_leave = Leave(
        employee_name=employee_name,
        leave_type=leave_type,
        start_date=date.fromisoformat(start_date),
        end_date=date.fromisoformat(end_date),
        reason=reason
    )
    db.add(new_leave)
    db.commit()
    return RedirectResponse(url=f"/employee-page?token={token}", status_code=303)


@router.post("/leaves/", response_model=LeaveResponse)
def apply_leave(
    leave: LeaveRequest,
    db: Session = Depends(get_db),
    token: str  = Query(...)
):
    user = get_current_user(token)
    if user["role"] != "employee":
        raise HTTPException(status_code=403, detail="Only employees can apply")
    new_leave = Leave(**leave.dict())
    db.add(new_leave)
    db.commit()
    db.refresh(new_leave)
    return new_leave


@router.get("/leaves/", response_model=List[LeaveResponse])
def get_leaves(
    db: Session                  = Depends(get_db),
    token: str                   = Query(...),
    page: int                    = 1,
    limit: int                   = 100,
    status: Optional[str]        = None,
    employee_name: Optional[str] = None,
    start_date: Optional[date]   = None,
    end_date: Optional[date]     = None
):
    user = get_current_user(token)
    if user["role"] not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    query = db.query(Leave)
    if status:
        query = query.filter(Leave.status == status)
    if employee_name:
        query = query.filter(Leave.employee_name == employee_name)
    if start_date:
        query = query.filter(Leave.start_date >= start_date)
    if end_date:
        query = query.filter(Leave.end_date <= end_date)
    skip = (page - 1) * limit
    return query.offset(skip).limit(limit).all()


@router.put("/leaves/{leave_id}/approve")
def approve_leave(
    leave_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    token: str  = Query(...)
):
    user = get_current_user(token)
    if user["role"] != "manager":
        raise HTTPException(status_code=403, detail="Only managers allowed")
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")
    leave.status = "approved"
    db.commit()
    background_tasks.add_task(log_action, f"Leave {leave.id} approved for {leave.employee_name}")
    return {"message": "Leave approved"}


@router.put("/leaves/{leave_id}/reject")
def reject_leave(
    leave_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    token: str  = Query(...)
):
    user = get_current_user(token)
    if user["role"] != "manager":
        raise HTTPException(status_code=403, detail="Only managers allowed")
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")
    leave.status = "rejected"
    db.commit()
    background_tasks.add_task(log_action, f"Leave {leave.id} rejected for {leave.employee_name}")
    return {"message": "Leave rejected"}