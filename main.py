import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import School, Order, PayoutRequest

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "School Portal Backend Running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected & Working"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response

# ---------------------------
# Auth & Schools
# ---------------------------
class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    school_id: str
    name: str
    email: str

@app.post("/api/auth/signup", response_model=LoginResponse)
def signup(school: School):
    # Basic check for existing email
    existing = db["school"].find_one({"email": school.email}) if db else None
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    inserted_id = create_document("school", school)
    return LoginResponse(school_id=inserted_id, name=school.name, email=school.email)

@app.post("/api/auth/login", response_model=LoginResponse)
def login(req: LoginRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    doc = db["school"].find_one({"email": req.email, "password": req.password})
    if not doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return LoginResponse(school_id=str(doc.get("_id")), name=doc.get("name"), email=doc.get("email"))

# ---------------------------
# Orders & Revenue
# ---------------------------
class RevenueSummary(BaseModel):
    total_orders: int
    total_revenue: float
    pending_payout: float

@app.get("/api/orders", response_model=List[Order])
def list_orders(school_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    docs = get_documents("order", {"school_id": school_id})
    # Convert ObjectId fields
    return [Order(**{**{k: v for k, v in d.items() if k != "_id"}}) for d in docs]

@app.post("/api/orders")
def create_order(order: Order):
    inserted_id = create_document("order", order)
    return {"id": inserted_id}

@app.get("/api/revenue", response_model=RevenueSummary)
def revenue(school_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    orders = list(db["order"].find({"school_id": school_id, "status": "paid"}))
    total_revenue = float(sum([o.get("amount", 0) for o in orders]))
    total_orders = len(orders)
    # Pending payout = total revenue - sum of approved/paid payouts for this school
    payouts = list(db["payoutrequest"].find({"school_id": school_id, "status": {"$in": ["approved", "paid"]}}))
    paid_out = float(sum([p.get("amount", 0) for p in payouts]))
    pending = max(total_revenue - paid_out, 0.0)
    return RevenueSummary(total_orders=total_orders, total_revenue=total_revenue, pending_payout=pending)

# ---------------------------
# Payouts
# ---------------------------
class PayoutCreateResponse(BaseModel):
    request_id: str
    status: str

@app.get("/api/payouts", response_model=List[PayoutRequest])
def list_payouts(school_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    docs = get_documents("payoutrequest", {"school_id": school_id})
    return [PayoutRequest(**{**{k: v for k, v in d.items() if k != "_id"}}) for d in docs]

@app.post("/api/payouts", response_model=PayoutCreateResponse)
def create_payout(req: PayoutRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    # Ensure school exists
    school = db["school"].find_one({"_id": ObjectId(req.school_id)}) if ObjectId.is_valid(req.school_id) else None
    if not school:
        # Fallback: also allow if there's at least an email match (looser for demo)
        school = db["school"].find_one({"_id": req.school_id})
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    request_id = create_document("payoutrequest", req)
    return PayoutCreateResponse(request_id=request_id, status="pending")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
