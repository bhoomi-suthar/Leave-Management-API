from fastapi import FastAPI, Query, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from models import Base, Leave
from database import get_db, get_current_user, engine
from schemas import LeaveRequest, LeaveResponse
from auth import router as auth_router
from leaves import router as leaves_router
import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO)
templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(leaves_router)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(request=request, name="signup.html")

@app.get("/login-page", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.get("/admin-page", response_class=HTMLResponse)
async def admin_page(request: Request, token: str = Query(...), db: Session = Depends(get_db)):
    user   = get_current_user(token)
    leaves = db.query(Leave).all()
    return templates.TemplateResponse(request=request, name="admin.html", context={"user": user, "token": token, "leaves": leaves})

@app.get("/manager-page", response_class=HTMLResponse)
async def manager_page(request: Request, token: str = Query(...), db: Session = Depends(get_db)):
    user   = get_current_user(token)
    leaves = db.query(Leave).all()
    return templates.TemplateResponse(request=request, name="manager.html", context={"user": user, "token": token, "leaves": leaves})

@app.get("/employee-page", response_class=HTMLResponse)
async def employee_page(request: Request, token: str = Query(...), db: Session = Depends(get_db)):
    user   = get_current_user(token)
    leaves = db.query(Leave).filter(Leave.employee_name == user["username"]).all()
    return templates.TemplateResponse(request=request, name="employee.html", context={"user": user, "token": token, "leaves": leaves})


@app.get("/health")
def health():
    return {"status": "ok"}
