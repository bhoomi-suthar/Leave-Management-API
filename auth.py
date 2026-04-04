from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from models import User, Leave
from database import get_db, pwd_context, create_token, get_current_user
import hashlib

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.post("/signup")
def signup(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        return templates.TemplateResponse(
            request=request, name="signup.html",
            context={"error": "Username already exists"}
        )
    hashed = hashlib.sha256(password.encode('utf-8')).hexdigest()
    new_user = User(username=username, password=hashed, role=role)
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/login-page", status_code=303)


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user or db_user.password != password:  
        return templates.TemplateResponse(
            request=request, name="login.html",
            context={"error": "Invalid credentials"}
        )
    
    token = create_token({"username": db_user.username, "role": db_user.role})
    return templates.TemplateResponse(
        request=request, name="token.html",
        context={"token": token, "role": db_user.role, "username": db_user.username}
    )

@router.post("/enter-token")
def enter_token(request: Request, token: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(token)
    role = user["role"]
    if role == "admin":
        leaves = db.query(Leave).all()
        return templates.TemplateResponse(request=request, name="admin.html", context={"user": user, "token": token, "leaves": leaves})
    elif role == "manager":
        leaves = db.query(Leave).all()
        return templates.TemplateResponse(request=request, name="manager.html", context={"user": user, "token": token, "leaves": leaves})
    else:
        leaves = db.query(Leave).filter(Leave.employee_name == user["username"]).all()
        return templates.TemplateResponse(request=request, name="employee.html", context={"user": user, "token": token, "leaves": leaves})
