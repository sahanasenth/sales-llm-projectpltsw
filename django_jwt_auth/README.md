# 🔐 Django JWT Authentication Backend

A production-ready JWT authentication system built with **Django REST Framework** and **SimpleJWT**.

## 📁 Project Structure

```
django_jwt_auth/
│
├── manage.py                        # Django CLI entry point
├── requirements.txt                 # All Python dependencies
├── .env                             # 🔒 Environment variables (DO NOT commit)
├── .gitignore                       # Excludes .env, __pycache__, db.sqlite3
│
├── core/                            # Django project settings package
│   ├── __init__.py
│   ├── settings.py                  # ⚙️  All configuration (JWT, DRF, DB)
│   ├── urls.py                      # 🌐 Root URL router
│   ├── wsgi.py                      # Production WSGI server entry
│   └── asgi.py                      # Async server entry
│
└── authentication/                  # Auth application
    ├── __init__.py
    ├── apps.py                      # App configuration
    ├── models.py                    # (Uses Django default User model)
    ├── serializers.py               # ✅ Input validation + output formatting
    ├── views.py                     # 🎯 API logic (CBVs)
    ├── urls.py                      # 🗺️  Endpoint routing
    ├── admin.py                     # Django Admin customization
    └── migrations/
        └── __init__.py
```

## 🌐 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/register/` | ❌ | Create new account |
| POST | `/api/token/` | ❌ | Login → get JWT tokens |
| POST | `/api/token/refresh/` | ❌ | Refresh access token |
| POST | `/api/token/verify/` | ❌ | Verify token validity |
| POST | `/api/logout/` | ✅ | Blacklist refresh token |
| GET | `/api/profile/` | ✅ | View user profile |
| PATCH | `/api/profile/` | ✅ | Update user profile |
| GET | `/admin/` | ✅ | Django admin panel |

## ⚡ Quick Start

### 1. Create & Activate Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Apply Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser (Admin)
```bash
python manage.py createsuperuser
```

### 5. Run Development Server
```bash
python manage.py runserver
```

Server runs at: **http://127.0.0.1:8000**

## 🔑 JWT Token Lifetime

| Token | Lifetime | Purpose |
|-------|----------|---------|
| Access Token | 15 minutes | Sent in Authorization header |
| Refresh Token | 1 day | Used to get new access tokens |

## 🛡️ How Authorization Works

Send the access token in every protected request:
```
Authorization: Bearer <your_access_token>
```
