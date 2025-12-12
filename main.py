
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from jose import JWTError, jwt
from pymongo import MongoClient
from bson import ObjectId
import bcrypt
import uuid
import os

# =========================
# CONFIG
# =========================

# Change this to your MongoDB URI (Atlas or local)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MASTER_DB_NAME = os.getenv("MASTER_DB_NAME", "org_master_db")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "SUPER_SECRET_KEY_CHANGE_ME")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# =========================
# DB SETUP
# =========================

mongo_client = MongoClient(MONGO_URI)
master_db = mongo_client[MASTER_DB_NAME]
orgs_coll = master_db["organizations"]
admins_coll = master_db["admins"]

# =========================
# UTILS
# =========================

def slugify(name: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in name).strip("_")

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def org_doc_to_response(org_doc: Dict[str, Any], admin_email: str) -> Dict[str, Any]:
    return {
        "id": str(org_doc["_id"]),
        "organization_name": org_doc["name"],
        "collection_name": org_doc["collection_name"],
        "admin_email": admin_email,
    }

# =========================
# SCHEMAS
# =========================

class OrgCreate(BaseModel):
    organization_name: str
    email: EmailStr
    password: str

class OrgUpdate(BaseModel):
    organization_name: str
    new_organization_name: str
    email: EmailStr
    password: str

class OrgDelete(BaseModel):
    organization_name: str

class OrgResponse(BaseModel):
    id: str
    organization_name: str
    collection_name: str
    admin_email: EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str

# =========================
# AUTH HELPERS
# =========================

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/login")

def get_admin_by_email(email: str) -> Optional[Dict[str, Any]]:
    return admins_coll.find_one({"email": email.lower()})

def get_org_by_name(name: str) -> Optional[Dict[str, Any]]:
    return orgs_coll.find_one({"name": name})

def get_org_by_id(org_id: str) -> Optional[Dict[str, Any]]:
    try:
        return orgs_coll.find_one({"_id": ObjectId(org_id)})
    except:
        return None

def get_admin_by_id(admin_id: str) -> Optional[Dict[str, Any]]:
    try:
        return admins_coll.find_one({"_id": ObjectId(admin_id)})
    except:
        return None

def get_current_admin(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        admin_id: str = payload.get("sub")
        org_id: str = payload.get("org_id")
        if admin_id is None or org_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    admin = get_admin_by_id(admin_id)
    org = get_org_by_id(org_id)
    if admin is None or org is None:
        raise credentials_exception
    return {"admin": admin, "org": org}

# =========================
# APP
# =========================

app = FastAPI(title="Organization Management Service (MongoDB)")

@app.get("/")
def root():
    return {"message": "Organization Management Service running"}

# -------- Create Organization --------
@app.post("/org/create", response_model=OrgResponse)
def create_organization(payload: OrgCreate):
    if get_org_by_name(payload.organization_name):
        raise HTTPException(status_code=400, detail="Organization already exists")

    # Create admin
    admin_doc = {
        "email": payload.email.lower(),
        "password_hash": hash_password(payload.password),
        "org_id": None,
        "created_at": datetime.utcnow(),
    }
    admin_insert_result = admins_coll.insert_one(admin_doc)
    admin_id = admin_insert_result.inserted_id

    # Create org + dynamic collection
    slug = slugify(payload.organization_name)
    collection_name = f"org_{slug}"
    org_doc = {
        "name": payload.organization_name,
        "collection_name": collection_name,
        "admin_id": admin_id,
        "connection_uri": MONGO_URI,  # for assignment: master + same conn
        "created_at": datetime.utcnow(),
    }
    org_insert_result = orgs_coll.insert_one(org_doc)
    org_id = org_insert_result.inserted_id

    # Back-ref org_id to admin
    admins_coll.update_one({"_id": admin_id}, {"$set": {"org_id": org_id}})

    # Create the dynamic collection (empty)
    org_collection = master_db[collection_name]
    org_collection.insert_one({"_seed": True})
    org_collection.delete_one({"_seed": True})

    org_doc = orgs_coll.find_one({"_id": org_id})
    return org_doc_to_response(org_doc, payload.email.lower())

# -------- Get Organization --------
@app.get("/org/get", response_model=OrgResponse)
def get_organization(organization_name: str):
    org = get_org_by_name(organization_name)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    admin = admins_coll.find_one({"_id": org["admin_id"]})
    admin_email = admin["email"] if admin else "unknown@example.com"
    return org_doc_to_response(org, admin_email)

# -------- Update Organization --------
@app.put("/org/update", response_model=OrgResponse)
def update_organization(payload: OrgUpdate):
    org = get_org_by_name(payload.organization_name)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    admin = admins_coll.find_one({"_id": org["admin_id"]})
    if (
        not admin
        or admin["email"] != payload.email.lower()
        or not verify_password(payload.password, admin["password_hash"])
    ):
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    if (
        payload.new_organization_name != payload.organization_name
        and get_org_by_name(payload.new_organization_name)
    ):
        raise HTTPException(status_code=400, detail="New organization name already exists")

    old_collection_name = org["collection_name"]
    new_slug = slugify(payload.new_organization_name)
    new_collection_name = f"org_{new_slug}"

    old_collection = master_db[old_collection_name]
    new_collection = master_db[new_collection_name]

    # Copy data to new collection
    docs = list(old_collection.find({}))
    if docs:
        for d in docs:
            d.pop("_id", None)
        new_collection.insert_many(docs)

    # Drop old collection
    master_db.drop_collection(old_collection_name)

    # Update org metadata
    orgs_coll.update_one(
        {"_id": org["_id"]},
        {"$set": {"name": payload.new_organization_name, "collection_name": new_collection_name}},
    )
    updated_org = orgs_coll.find_one({"_id": org["_id"]})
    return org_doc_to_response(updated_org, admin["email"])

# -------- Delete Organization --------
@app.delete("/org/delete")
def delete_organization(payload: OrgDelete, current=Depends(get_current_admin)):
    org = current["org"]

    if payload.organization_name != org["name"]:
        raise HTTPException(status_code=403, detail="Cannot delete another organization")

    collection_name = org["collection_name"]

    # Drop tenant collection
    master_db.drop_collection(collection_name)

    # Delete admins for this org
    admins_coll.delete_many({"org_id": org["_id"]})

    # Delete org document
    orgs_coll.delete_one({"_id": org["_id"]})

    return {"detail": "Organization deleted successfully"}

# -------- Admin Login --------
@app.post("/admin/login", response_model=Token)
def admin_login(form_data: OAuth2PasswordRequestForm = Depends()):
    admin = get_admin_by_email(form_data.username.lower())
    if not admin or not verify_password(form_data.password, admin["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not admin.get("org_id"):
        raise HTTPException(status_code=400, detail="Admin not associated with any organization")

    access_token = create_access_token(
        data={"sub": str(admin["_id"]), "org_id": str(admin["org_id"])},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=access_token, token_type="bearer")
