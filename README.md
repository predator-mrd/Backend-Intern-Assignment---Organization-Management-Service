# Backend-Intern-Assignment---Organization-Management-Service




## Setup & Run Instructions

### Before You Start
- Python 3.8+
- MongoDB Community Server installed

### 1. Start MongoDB (Windows)
```bash
# Run Command Prompt as Administrator
net start MongoDB
```

### 2. Go to Project Folder
Open Command Prompt in your project directory

### 3. Install Dependencies
```bash
pip install fastapi "uvicorn[standard]" pymongo "python-jose[cryptography]" bcrypt "pydantic[email]" python-multipart
```

### 4. Run Server
```bash
uvicorn main:app --reload
```

Expected output:
```
Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
Application startup complete.
```

### 5. Open API Docs
Browser → `http://127.0.0.1:8000/docs`

---

## Testing Workflow (Swagger UI)

### 1. Create Organization
POST /org/create
```json
{
  "organization_name": "AcmeCorp",
  "email": "admin@acme.com",
  "password": "StrongPass123"
}
```
Response: `200 OK` with org metadata

### 2. Get Organization
GET /org/get?organization_name=AcmeCorp
Response: `200 OK` org details

### 3. Login & Get Token
POST /admin/login
- username: admin@acme.com
- password: StrongPass123
Response: `200 OK` with `access_token`

### 4. Authorize (Top-right green button)
Set Bearer token:
```
Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 5. Update Organization
PUT /org/update (with authorization)
```json
{
  "organization_name": "AcmeCorp",
  "new_organization_name": "AcmeGlobal",
  "email": "admin@acme.com",
  "password": "StrongPass123"
}
```
Response: `200 OK` updated org

### 6. Delete Organization
DELETE /org/delete (with authorization)
```json
{
  "organization_name": "AcmeGlobal"
}
```
Response: `200 OK` success message

---

## Database Schema

```
org_master_db
├── organizations     {_id, name, collection_name, admin_id, created_at}
├── admins            {_id, email, password_hash, org_id, created_at}
├── org_acmecorp      (Tenant data - isolated)
├── org_acmeglobal    (Tenant data - isolated)
└── org_companyxyz    (Tenant data - isolated)
```

---

## API Endpoints Summary

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | /org/create | No | Create org + admin |
| GET | /org/get | No | Fetch org details |
| POST | /admin/login | No | Get JWT token |
| PUT | /org/update | Yes | Rename org + migrate |
| DELETE | /org/delete | Yes | Delete org + cleanup |

---

## Key Features

✅ **Multi-tenant**: Each org isolated in own MongoDB collection
✅ **JWT Authentication**: Secure token-based auth with bcrypt
✅ **Class-Based Design**: Modular, testable, maintainable
✅ **Data Migration**: Automatic data migration on org rename
✅ **Full API Docs**: Swagger UI at /docs
✅ **Error Handling**: Comprehensive HTTP status codes
✅ **Production-Ready**: Scalable, secure, deployable

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| 500 ServerSelectionTimeoutError | Start MongoDB: `net start MongoDB` (admin) |
| ModuleNotFoundError | Reinstall deps: `pip install -r requirements.txt` |
| 401 Not authenticated | Login first, copy token, set Bearer header |
| 403 Cannot delete | Use exact current organization name |
| 400 Already exists | Use unique organization name |

---

## Stop Server
Press `Ctrl + C` in terminal

---
## Stop Server
`Ctrl + C`

---

**Ready for production deployment on Railway/Render/Heroku**
