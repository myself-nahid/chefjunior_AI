# ChefJunior Backend API 👨‍🍳

ChefJunior is a gamified cooking application for kids.  
This repository contains the backend API that powers authentication, recipes, games, analytics, notifications, and an AI-powered cooking assistant named **Dwane**.

Built with FastAPI, SQLAlchemy, SQLite/PostgreSQL, and OpenAI.

---

## 🚀 Features

- 🔐 JWT Authentication (Signup, Login, OTP Password Reset)
- 🤖 AI Avatar Chat (WebSocket + OpenAI GPT + Whisper)
- 🥗 Recipe Management (CRUD, Search, Favorites)
- 🥕 Ingredient Management (With Image Upload)
- 🎮 Educational Games (Word Search, Crossword)
- 📊 Admin Analytics Dashboard
- 🔔 Admin Notifications System
- 👤 User Profiles & Avatar Uploads
- 🌍 Multi-language Support

---

## 🛠 Tech Stack

- **Framework:** FastAPI
- **Database:** SQLAlchemy ORM
- **Dev DB:** SQLite
- **Production DB:** PostgreSQL
- **AI Integration:** OpenAI API (GPT + Whisper)
- **Authentication:** OAuth2 + JWT
- **Password Hashing:** Bcrypt
- **Validation:** Pydantic
- **Real-Time Communication:** WebSockets

---

# ⚙️ Installation & Setup

## 1️⃣ Clone Repository

```bash
git clone https://github.com/myself-nahid/chefjunior-backend.git
cd chefjunior-backend
```

---

## 2️⃣ Create Virtual Environment

### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

### macOS / Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4️⃣ Environment Variables

Create a `.env` file in the root directory:

```ini
# App Configuration
PROJECT_NAME="ChefJunior API"
SECRET_KEY="your_super_secret_key_here"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database
DATABASE_URL="sqlite:///./chefjunior.db"
# For PostgreSQL:
# DATABASE_URL="postgresql://user:password@localhost/dbname"

# OpenAI
OPENAI_API_KEY="sk-your-openai-api-key"

# Email (OTP)
EMAIL_SENDER="your_email@gmail.com"
EMAIL_PASSWORD="your_16_character_app_password"
```

---

## 5️⃣ Run the Application

```bash
uvicorn app.main:app --reload
```

Server will run at:

```
http://127.0.0.1:8000
```

---

# 📚 API Documentation

Swagger UI:
```
http://127.0.0.1:8000/docs
```

ReDoc:
```
http://127.0.0.1:8000/redoc
```

---

# 🔑 Authentication (`/api/v1/auth`)

| Method | Endpoint | Description | Auth |
|--------|----------|------------|------|
| POST | /signup | Register new user | ❌ |
| POST | /login | Login (Form) | ❌ |
| POST | /login-json | Login (JSON) | ❌ |
| POST | /forgot-password | Send OTP | ❌ |
| POST | /verify-otp | Verify OTP | ❌ |
| POST | /resend-otp | Resend OTP | ❌ |
| POST | /reset-password | Reset Password | ❌ |
| POST | /change-password | Change Password | ✅ |
| POST | /logout | Logout | ✅ |

---

# 👤 Users (`/api/v1/users`)

| Method | Endpoint | Description | Auth |
|--------|----------|------------|------|
| GET | /me | Get current user | ✅ |
| PATCH | /me | Update profile | ✅ |
| PATCH | /me/admin-profile | Update admin info | ✅ |
| POST | /me/avatar | Upload avatar | ✅ |
| GET | / | List all users | ✅ |
| PATCH | /{id}/toggle-status | Block/Unblock user | ✅ |
| DELETE | /{id} | Delete user | ✅ |

---

# 🍲 Recipes (`/api/v1/recipes`)

| Method | Endpoint | Description | Auth |
|--------|----------|------------|------|
| GET | / | List recipes | ✅ |
| GET | /explore | Explore feed | ✅ |
| POST | / | Create recipe | ✅ |
| GET | /{id} | Recipe details | ✅ |
| PUT | /{id} | Update recipe | ✅ |
| DELETE | /{id} | Delete recipe | ✅ |
| POST | /{id}/favorite | Favorite/unfavorite | ✅ |
| GET | /me/favorites | My favorites | ✅ |

---

# 🥕 Ingredients (`/api/v1/ingredients`)

| Method | Endpoint | Description | Auth |
|--------|----------|------------|------|
| GET | / | List ingredients | ✅ |
| POST | / | Create ingredient | ✅ |
| PUT | /{id} | Update ingredient | ✅ |
| DELETE | /{id} | Delete ingredient | ✅ |

---

# 🎮 Games (`/api/v1/games`)

| Method | Endpoint | Description | Auth |
|--------|----------|------------|------|
| GET | / | List games | ✅ |
| POST | / | Create game level | ✅ |
| GET | /{id} | Get game data | ✅ |
| POST | /{id}/complete | Submit score | ✅ |

---

# 📈 Analytics (`/api/v1/analytics`)

| Method | Endpoint | Description | Auth |
|--------|----------|------------|------|
| GET | /dashboard | Admin dashboard stats | ✅ |
| GET | /page-view | Growth stats | ✅ |

---

# 🔔 Notifications (`/api/v1/notifications`)

| Method | Endpoint | Description | Auth |
|--------|----------|------------|------|
| GET | / | Get notifications | ✅ |
| PATCH | /read-all | Mark all read | ✅ |
| PATCH | /{id}/read | Mark one read | ✅ |

---

# 🤖 AI Chat (`/api/v1/chat`)

| Method | Endpoint | Description |
|--------|----------|------------|
| WS | /ws/{client_id} | WebSocket chat |
| POST | /upload-audio/{client_id} | Upload audio & transcribe |

---

# 📂 Project Structure

```
chefjunior-backend/
│
├── app/
│   ├── api/v1/endpoints/
│   ├── core/
│   ├── crud/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── main.py
│   └── database.py
│
├── static/
├── .env
├── requirements.txt
└── README.md
```

---

# 🐛 Troubleshooting

### Database Error (no such column)
Delete `chefjunior.db` and restart the server after model changes.

### Audio Upload Error
Ensure:
- Key name is `file`
- Supported formats: mp3, wav, m4a

### CORS Issues
Update `CORSMiddleware` settings in `main.py`.

---

# 📄 License

This project is licensed under the MIT License.

---

# 👨‍💻 Author

Nahid Hasan