# Backend-Intern-Assignment---Organization-Management-Service




# Organization Management Service

FastAPI + MongoDB multi-tenant backend with JWT authentication, bcrypt password hashing, and dynamic per-organization collections.

## Quick Start

### Prerequisites
- Python 3.8+
- MongoDB Community Server

### 1. Start MongoDB
Run Command Prompt as Administrator
net start MongoDB

text

### 2. Install Dependencies
pip install fastapi "uvicorn[standard]" pymongo "python-jose[cryptography]" bcrypt "pydantic[email]" python-multipart

text

### 3. Run Server
uvicorn main:app --reload

text

### 4. Open API Docs
http://127.0.0.1:8000/docs

text

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/org/create` | Create org + admin + collection | No |
| `GET` | `/org/get` | Get org details | No |
| `POST` | `/admin/login` | Get JWT token | No |
| `PUT` | `/org/update` | Rename org + migrate data | Yes |
| `DELETE` | `/org/delete` | Delete org + collection | Yes |

## Testing Workflow

### 1. Create Organization
{
"organization_name": "AcmeCorp",
"email": "admin@acme.com",
"password": "StrongPass123"
}

text

### 2. Get Organization
Query: `organization_name=AcmeCorp`

### 3. Login (Copy `access_token`)
username: admin@acme.com
password: StrongPass123

text

### 4. Authorize (Top-right green button)
Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

text

### 5. Update Organization
{
"organization_name": "AcmeCorp",
"new_organization_name": "AcmeGlobal",
"email": "admin@acme.com",
"password": "StrongPass123"
}

text

### 6. Delete Organization
{
"organization_name": "AcmeGlobal"
}

text

## Troubleshooting

| Error | Fix |
|-------|-----|
| `500 ServerSelectionTimeoutError` | `net start MongoDB` (as admin) |
| `401 Not authenticated` | Login → Copy token → Authorize |
| `403 Cannot delete` | Use exact current `organization_name` |
| `400 Organization already exists` | Use unique `organization_name` |

## Architecture

org_master_db (single DB)
├── organizations (org metadata)
├── admins (credentials)
└── org_acmecorp (tenant data)
├── org_acmeglobal (tenant data)
└── org_* (dynamic per org)

text

**Features:**
- ✅ JWT + bcrypt security
- ✅ Dynamic collection creation
- ✅ Data migration on rename
- ✅ Admin scoped to single org
- ✅ Full Swagger UI docs

## Stop Server
`Ctrl + C`

---

**Ready for production deployment on Railway/Render/Heroku**
