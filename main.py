from fastapi import FastAPI, HTTPException, Query, Depends, BackgroundTasks
from pydantic import BaseModel, validator
from datetime import date, datetime, timedelta
from typing import List, Optional
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import logging
import os
from dotenv import load_dotenv
from fastapi.responses import HTMLResponse

#ENV 
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Leave Management</title>
        <style>
            body { font-family: Arial; padding: 40px; background: #f5f5f5; }
            h1 { color: #333; }
            .box { background: white; padding: 20px; border-radius: 10px; margin-top: 20px; }
            button { padding: 10px; margin: 5px; cursor: pointer; }
            input { padding: 8px; margin: 5px; }
            pre { background: #eee; padding: 10px; }
        </style>
    </head>
    <body>
        <h1>Leave Management System</h1>

        <!-- SIGNUP -->
        <div class="box">
            <h3>Signup</h3>
            <input id="su_user" placeholder="username">
            <input id="su_pass" placeholder="password">
            <input id="su_role" placeholder="role (employee/manager/admin)">
            <button onclick="signup()">Signup</button>
        </div>
        <pre id="signup_result"></pre>

        <!-- LOGIN -->
        <div class="box">
            <h3>Login</h3>
            <input id="li_user" placeholder="username">
            <input id="li_pass" placeholder="password">
            <input id="li_role" placeholder="role">
            <button onclick="login()">Login</button>
        </div>
        <pre id="login_result"></pre>

        <!-- APPLY LEAVE -->
        <div class="box">
            <h3>Apply Leave</h3>
            <input id="emp_name" placeholder="employee name">
            <input id="leave_type" placeholder="leave type">
            <input id="start" placeholder="start date (YYYY-MM-DD)">
            <input id="end" placeholder="end date (YYYY-MM-DD)">
            <input id="reason" placeholder="reason">
            <input id="emp_token" placeholder="employee token">
            <button onclick="applyLeave()">Apply</button>
        </div>
        <pre id="apply_result"></pre>

        <!-- VIEW LEAVES -->
        <div class="box">
            <h3>View Leaves</h3>
            <input id="view_token" placeholder="manager/admin token">
            <button onclick="getLeaves()">Get Leaves</button>
        </div>
        <pre id="view_result"></pre>

        <!-- APPROVE/REJECT -->
        <div class="box">
            <h3>Approve / Reject</h3>
            <input id="leaveId" placeholder="leave id">
            <input id="mgr_token" placeholder="manager token">
            <button onclick="approveLeave()">Approve</button>
            <button onclick="rejectLeave()">Reject</button>
        </div>
        <pre id="action_result"></pre>

        <script>
            async function signup() {
                const res = await fetch("/signup", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({ 
                        username: su_user.value,
                        password: su_pass.value,
                        role: su_role.value 
                    })
                });
                show(res, "signup_result");
            }

            async function login() {
                const res = await fetch("/login", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({ 
                        username: li_user.value,
                        password: li_pass.value,
                        role: li_role.value 
                    })
                });
                show(res, "login_result");
            }

            async function applyLeave() {
                const res = await fetch(`/leaves/?token=${emp_token.value}`, {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({ 
                        employee_name: emp_name.value,
                        leave_type: leave_type.value,
                        start_date: start.value,
                        end_date: end.value,
                        reason: reason.value 
                    })
                });
                show(res, "apply_result");
            }

            async function getLeaves() {
                const res = await fetch(`/leaves/?token=${view_token.value}`);
                show(res, "view_result");
            }

            async function approveLeave() {
                const res = await fetch(`/leaves/${leaveId.value}/approve?token=${mgr_token.value}`, { method: "PUT" });
                show(res, "action_result");
            }

            async function rejectLeave() {
                const res = await fetch(`/leaves/${leaveId.value}/reject?token=${mgr_token.value}`, { method: "PUT" });
                show(res, "action_result");
            }

            async function show(res, elementId) {
                const data = await res.json();
                document.getElementById(elementId).innerText = JSON.stringify(data, null, 2);
            }
        </script>
    </body>
    </html>
    """

logging.basicConfig(level=logging.INFO)
DATABASE_URL = "sqlite:///./leave.db"
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
pwd_context = CryptContext(schemes=["pbkdf2_sha256"])


# models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String)

class Leave(Base):
    __tablename__ = "leaves"
    id = Column(Integer, primary_key=True)
    employee_name = Column(String)
    leave_type = Column(String)
    start_date = Column(Date)
    end_date = Column(Date)
    reason = Column(String)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# schemas
class UserCreate(BaseModel):
    username: str
    password: str
    role: str

class LeaveRequest(BaseModel):
    employee_name: str
    leave_type: str
    start_date: date
    end_date: date
    reason: str

    @validator("end_date")
    def validate_dates(cls, v, values):
        if "start_date" in values and v < values["start_date"]:
            raise ValueError("End date must be >= start date")
        return v

class LeaveResponse(BaseModel):
    id: int
    employee_name: str
    leave_type: str
    start_date: date
    end_date: date
    reason: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# dependency 
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Auth 
def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def create_token(data: dict):
    data["exp"] = datetime.utcnow() + timedelta(hours=2)
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

# Background
def log_action(message: str):
    logging.info(message)

# ROUTES 
@app.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    new_user = User(
        username=user.username,
        password=hash_password(user.password),
        role=user.role
    )
    db.add(new_user)
    db.commit()
    return {"message": "User created"}

@app.post("/login")
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token({
        "username": db_user.username,
        "role": db_user.role
    })
    return {"token": token}

@app.post("/leaves/", response_model=LeaveResponse)
def apply_leave(
    leave: LeaveRequest,
    db: Session = Depends(get_db),
    token: str = Query(...)
):
    user = get_current_user(token)
    if user["role"] != "employee":
        raise HTTPException(status_code=403, detail="Only employees can apply")
    new_leave = Leave(**leave.dict())
    db.add(new_leave)
    db.commit()
    db.refresh(new_leave)
    logging.info(f"Leave applied by {leave.employee_name}")
    return new_leave

@app.get("/leaves/", response_model=List[LeaveResponse])
def get_leaves(
    db: Session = Depends(get_db),
    token: str = Query(...),
    page: int = 1,
    limit: int = 100,
    status: Optional[str] = None,
    employee_name: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
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

@app.put("/leaves/{leave_id}/approve")
def approve_leave(
    leave_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    token: str = Query(...)
):
    user = get_current_user(token)
    if user["role"] != "manager":
        raise HTTPException(status_code=403, detail="Only managers allowed")
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")
    leave.status = "approved"
    db.commit()
    background_tasks.add_task(
        log_action, f"Leave {leave.id} approved for {leave.employee_name}"
    )
    return {"message": "Leave approved"}

@app.put("/leaves/{leave_id}/reject")
def reject_leave(
    leave_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    token: str = Query(...)
):
    user = get_current_user(token)
    if user["role"] != "manager":
        raise HTTPException(status_code=403, detail="Only managers allowed")
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")
    leave.status = "rejected"
    db.commit()
    background_tasks.add_task(
        log_action, f"Leave {leave.id} rejected for {leave.employee_name}"
    )
    return {"message": "Leave rejected"}