# saas_main.py
from datetime import datetime
import json
from typing import Optional, List

from fastapi import (
    FastAPI,
    Request,
    Depends,
    Form,
    status,
    UploadFile,
    File,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from database import Base, engine, get_db
from saas_models import User, Subscription, AlertHistory

# If you prefer direct function import later you can refactor like:
# from backend.normalizer import normalizealert
# from backend.enricher import enrichalert
# from backend.feature_engine import buildfeatures
# from backend.scoring_service import scorealert

import httpx

APIBINDHOST = "127.0.0.1"
APIBINDPORT = 8000
BACKEND_URL = f"http://{APIBINDHOST}:{APIBINDPORT}/api/v1/debug/upload_json"

pwd_context = CryptContext(schemes=["argon2", "pbkdf2_sha256"], deprecated="auto")

app = FastAPI(title="ARIA SaaS")

app.add_middleware(SessionMiddleware, secret_key="change-me-in-prod")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


def login_required(user: User = Depends(get_current_user)):
    if not user:
        raise RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return user


def admin_required(user: User = Depends(get_current_user)):
    if not user or not user.is_admin:
        raise RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return user

def hash_password(password: str) -> str:
    """Safe password hashing - argon2 handles any length"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Password verification"""
    return pwd_context.verify(plain_password, hashed_password)

# ------------- Home page -------------


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "user": user},
    )


# ------------- Auth (Register / Login / Logout) -------------


@app.get("/register", response_class=HTMLResponse)
async def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register")# In saas_main.py, replace your existing register_post block with this:

@app.post("/register")
async def register_post(
    request: Request,
    name: str = Form(...),
    mobile: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    # Validate passwords match
    if password != confirm_password:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Passwords do not match"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Check for existing user
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "User already exists"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Create user with new fields
    user = User(
        name=name, 
        mobile=mobile, 
        email=email, 
        hashed_password=hash_password(password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Default Free subscription
    sub = Subscription(user_id=user.id, tier="Free")
    db.add(sub)
    db.commit()

    request.session["user_id"] = user.id
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid credentials"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    request.session["user_id"] = user.id
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


# ------------- Dashboard (User Module) -------------


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: User = Depends(login_required),
    db: Session = Depends(get_db),
):
    # Previous alert history (last few entries)
    history: List[AlertHistory] = (
        db.query(AlertHistory)
        .filter(AlertHistory.user_id == user.id)
        .order_by(AlertHistory.created_at.desc())
        .limit(5)
        .all()
    )

    subscription = user.subscription
    days_remaining = None
    warn_expiring = False
    if subscription and subscription.end_date:
        delta = subscription.end_date - datetime.utcnow()
        days_remaining = max(delta.days, 0)
        warn_expiring = days_remaining < 3

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "history": history,
            "subscription": subscription,
            "days_remaining": days_remaining,
            "warn_expiring": warn_expiring,
        },
    )


# ------------- Upload Alerts (Run Alert System) -------------


@app.get("/upload-alerts", response_class=HTMLResponse)
async def upload_alerts_get(
    request: Request,
    user: User = Depends(login_required),
):
    return templates.TemplateResponse(
        "upload.html",
        {
            "request": request,
            "user": user,
        },
    )


@app.post("/upload-alerts", response_class=HTMLResponse)
async def upload_alerts_post(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(login_required),
    db: Session = Depends(get_db),
):
    # Call existing backend debug_upload_json
    backend_url = BACKEND_URL  # adjust path to match your router[file:5]
    contents = await file.read()

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            backend_url,
            files={"file": (file.filename, contents, file.content_type)},
            headers={},  # add auth header if backend protected
        )

    if resp.status_code != 200:
        return templates.TemplateResponse(
            "upload.html",
            {
                "request": request,
                "user": user,
                "error": f"Backend error: {resp.status_code} {resp.text}",
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    data = resp.json()
    # Expect something like: {"inserted": [...], "count": n, "autoplaybook": {...}} or similar[file:5]
    # For MVP, just store raw JSON blobs
    incidents = json.dumps(data.get("incidents", []))
    scored_alerts = json.dumps(data.get("scored_alerts", []))

    history = AlertHistory(
        user_id=user.id,
        incidents_json=incidents,
        scored_alerts_json=scored_alerts,
    )
    db.add(history)
    db.commit()
    db.refresh(history)

    return templates.TemplateResponse(
        "upload.html",
        {
            "request": request,
            "user": user,
            "processed": True,
            "incidents": json.loads(incidents),
            "scored_alerts": json.loads(scored_alerts),
        },
    )


# ------------- Admin Module -------------


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    admin: User = Depends(admin_required),
    db: Session = Depends(get_db),
):
    users = db.query(User).all()
    subs = db.query(Subscription).all()

    # Dummy subscription stats for Chart.js
    daily_data = [3, 5, 2, 7, 4, 6, 8]   # last 7 days
    monthly_data = [10, 15, 12, 18, 20, 25]  # last 6 months

    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "admin": admin,
            "users": users,
            "subs": subs,
            "daily_data": daily_data,
            "monthly_data": monthly_data,
        },
    )


# ------------- Subscription / Pricing -------------


@app.get("/pricing", response_class=HTMLResponse)
async def pricing(
    request: Request,
    user: User = Depends(get_current_user),
):
    # If not logged in -> show pricing but CTA to login/register
    return templates.TemplateResponse(
        "pricing.html",
        {"request": request, "user": user},
    )

# saas_main.py additions/modifications

@app.post("/pricing/subscribe")
async def subscribe_post(
    request: Request,
    tier: str = Form(...),
    payment_method: str = Form(...),
    user: User = Depends(login_required),
    db: Session = Depends(get_db),
):
    # Requirement 2: Enterprise redirect
    if tier == "Enterprise":
        return RedirectResponse(url="/contact-us", status_code=status.HTTP_303_SEE_OTHER)

    # Requirement 3: Check if already subscribed to this tier
    if user.subscription and user.subscription.tier == tier and user.subscription.end_date > datetime.utcnow():
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    # Requirement 1: Redirect to Payment Gateway
    # In a real app, you'd generate a Stripe Checkout URL here.
    return RedirectResponse(
        url=f"/payment-gateway?tier={tier}&method={payment_method}", 
        status_code=status.HTTP_303_SEE_OTHER
    )

@app.get("/payment-gateway", response_class=HTMLResponse)
async def payment_gateway(request: Request, tier: str, method: str, user: User = Depends(login_required)):
    return templates.TemplateResponse("payment_mock.html", {
        "request": request, 
        "tier": tier, 
        "method": method
    })

@app.post("/payment/success")
async def payment_success(
    request: Request,
    tier: str = Form(...),
    user: User = Depends(login_required),
    db: Session = Depends(get_db)
):
    sub = user.subscription
    if not sub:
        sub = Subscription(user_id=user.id, tier=tier)
        db.add(sub)
    else:
        sub.tier = tier
        sub.start_date = datetime.utcnow()
        sub.end_date = datetime.utcnow() + timedelta(days=30)
    
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    @app.get("/contact-us", response_class=HTMLResponse)
async def contact_get(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("contact.html", {"request": request, "user": user})

@app.post("/contact-us")
async def contact_post(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    volume: str = Form(...),
    message: str = Form(...),
    user: User = Depends(get_current_user)
):
    # Professional SaaS Tip: In production, send this to your CRM (HubSpot/Salesforce) 
    # or email your sales team here.
    print(f"Enterprise Inquiry: {name} ({email}) - Volume: {volume}")
    
    return templates.TemplateResponse("contact.html", {
        "request": request, 
        "user": user,
        "success": "Your request has been sent! Our sales team will contact you within 24 hours."
    })