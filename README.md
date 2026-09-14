# 🎟️ Smart Queue Manager

[![Python Version](https://img.shields.io/badge/Python-3.11%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Flask-3.1.x-black.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-SQLAlchemy%20%7C%20PostgreSQL%20%7C%20SQLite-4479A1.svg?logo=postgresql&logoColor=white)](https://www.sqlalchemy.org/)
[![SMS Alerts](https://img.shields.io/badge/SMS-Twilio-F22F46.svg?logo=twilio&logoColor=white)](https://www.twilio.com/)
[![Deployment](https://img.shields.io/badge/Deploy-Vercel%20Ready-000000.svg?logo=vercel&logoColor=white)](https://vercel.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A modern, full-stack **virtual queue and customer flow management system** built with Flask, SQLAlchemy, and Twilio. Smart Queue Manager eliminates physical waiting lines, allowing customers to join queues remotely, monitor their live wait times, and receive automatic SMS notifications when their turn arrives.

---

## 📑 Table of Contents

- [Key Features](#-key-features)
- [Architecture & Tech Stack](#-architecture--tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start & Local Setup](#-quick-start--local-setup)
- [Configuration & Environment Variables](#-configuration--environment-variables)
- [Admin Access & Demo Accounts](#-admin-access--demo-accounts)
- [REST API Endpoints](#-rest-api-endpoints)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Key Features

### 👤 Customer Experience
- **Virtual Check-in:** Browse participating businesses (clinics, salons, retail, government offices, cafes) and join waiting lists from any device.
- **Live Position Tracking:** Check real-time queue position, estimated wait times, and queue status via unique ticket IDs.
- **Customer Accounts & Dashboard:** Register, view active and past queues, or cancel waitlist reservations on demand.
- **SMS Notifications:** Receive automated SMS updates (queue confirmation, position updates, and "You're next!" alerts).

### 🏢 Business & Admin Management
- **Multi-Business Support:** Manage different branch locations or independent service queues under one unified platform.
- **Interactive Admin Control Panel:** Call next customer, complete visits, reorder queues, prioritize urgent tickets, or remove entries in real-time.
- **Queue Analytics & Reports:** Live statistics tracking average wait times, peak traffic hours, total served customers, and historical trends.
- **Reset & Archiving:** Reset or archive daily queues with automated history recording.

---

## 🛠️ Architecture & Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend** | [Python 3.11+](https://www.python.org/), [Flask 3.1](https://flask.palletsprojects.com/), [Werkzeug](https://werkzeug.palletsprojects.com/) |
| **Database & ORM** | [SQLAlchemy 2.0](https://www.sqlalchemy.org/), [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/), PostgreSQL (Production), SQLite (Local zero-config fallback) |
| **Frontend** | Jinja2 Templates, HTML5, CSS3, JavaScript (Fetch API), FontAwesome |
| **Notifications** | [Twilio REST API](https://www.twilio.com/) (SMS alerts & status updates) |
| **Authentication** | Secure password hashing (`werkzeug.security`), Session management, [Flask-Login](https://flask-login.readthedocs.io/) |
| **Production WSGI** | [Gunicorn](https://gunicorn.org/), Vercel Serverless WSGI Handler |

---

## 📂 Project Structure

```text
Smart-Queue-Manager/
├── app.py                     # Main Flask application, routes & business logic
├── main.py                    # Application entrypoint (WSGI server & local runner)
├── models.py                  # SQLAlchemy models (User, Business, QueueItem, QueueStatistics, QueueHistory)
├── queue_manager.py           # Core queue operations and data management helper
├── notifications.py           # Twilio SMS notification service
├── replit_db.py               # Local JSON / Replit DB storage compatibility layer
├── vercel_requirements.txt    # Production Python dependencies
├── vercel.json                # Vercel deployment configuration
├── pyproject.toml             # Project build configuration & metadata
│
├── static/                    # Static assets
│   ├── css/
│   │   └── style.css          # Application styles
│   └── js/                    # Client-side JavaScript scripts
│
└── templates/                 # Jinja2 HTML templates
    ├── base.html              # Base layout with navigation and footer
    ├── businesses.html        # Public directory of businesses
    ├── business_queue.html    # Business queue details & join form
    ├── check_position.html    # Real-time ticket position checker
    ├── user_dashboard.html    # Customer queue dashboard
    ├── user_login.html        # Customer login page
    ├── user_register.html     # Customer registration page
    ├── admin_panel.html       # Business queue operator panel
    ├── admin_login.html       # Admin login page
    ├── statistics.html        # Queue analytics and metrics
    └── error.html             # Error view
```

---

## 🚀 Quick Start & Local Setup

### 1. Prerequisites
- **Python 3.11+** installed on your system ([Download Python](https://www.python.org/downloads/))
- **Git** installed ([Download Git](https://git-scm.com/))

### 2. Clone the Repository
```bash
git clone https://github.com/krishnakant09/Smart-Queue-Manager.git
cd Smart-Queue-Manager
```

### 3. Create & Activate Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(If you see an execution policy error on PowerShell, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first)*

**On Windows (Command Prompt):**
```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r vercel_requirements.txt
```

### 5. Run the Server
```bash
python main.py
```
*Or run directly with the virtual environment executable:*
```powershell
.\.venv\Scripts\python.exe main.py
```

The application will start on **`http://localhost:5000`** (or `http://127.0.0.1:5000`).

---

## ⚙️ Configuration & Environment Variables

The project runs out-of-the-box in local development using **SQLite** (`queue_manager.db`). For production or SMS integration, create a `.env` file or export the following variables:

| Variable | Required | Default | Description |
| :--- | :---: | :--- | :--- |
| `DATABASE_URL` | No | `sqlite:///queue_manager.db` | PostgreSQL or SQLite connection string (e.g., `postgresql://user:pass@host:5432/dbname`) |
| `SESSION_SECRET` | No | `default-secret-key...` | Cryptographic secret key for signing session cookies |
| `ADMIN_USERNAME` | No | `admin` | Default administrator username |
| `ADMIN_PASSWORD` | No | `admin123` | Default administrator password |
| `TWILIO_ACCOUNT_SID` | Optional | `None` | Twilio Account SID for SMS alerts |
| `TWILIO_AUTH_TOKEN` | Optional | `None` | Twilio Auth Token |
| `TWILIO_PHONE_NUMBER` | Optional | `None` | Twilio sender phone number (E.164 format, e.g. `+1234567890`) |

---

## 🔐 Admin Access & Demo Accounts

Default administrator credentials for managing queues:

- **Admin Login URL:** `http://localhost:5000/login` or `http://localhost:5000/admin`
- **Username:** `admin`
- **Password:** `admin123`

> ⚠️ **Important:** Change default credentials in production environments by configuring the `ADMIN_USERNAME` and `ADMIN_PASSWORD` environment variables.

---

## 📡 REST API Endpoints

The application exposes a clean RESTful API for queue operations and third-party integrations:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/queue?business_id=<id>` | Retrieve all current queue items for a business |
| `POST` | `/api/queue` | Add a new customer to a queue (`name`, `phone`, `business_id`, `priority`) |
| `PUT` | `/api/queue/<item_id>` | Update customer details or priority |
| `DELETE` | `/api/queue/<item_id>` | Remove a customer from the queue |
| `POST` | `/api/queue/<item_id>/complete` | Mark a customer as served and update analytics |
| `GET` | `/api/queue/statistics?business_id=<id>` | Fetch real-time queue length, average wait, and peak load |
| `POST` | `/api/queue/reset` | Archive and reset the current business queue |

---

## 🌐 Deployment

### Deploying to Vercel (Recommended)

1. Push your repository to **GitHub**.
2. Visit [Vercel](https://vercel.com/) and click **Add New Project** → Import your GitHub repository.
3. In project settings, configure the **Environment Variables**:
   - `DATABASE_URL`: Connection string for PostgreSQL (e.g., Neon, Supabase, Vercel Postgres).
   - `SESSION_SECRET`: A secure random string.
   - `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`: (Optional, for SMS).
4. Click **Deploy**. Vercel will automatically configure the build using [vercel.json](vercel.json).

### Running with Production WSGI (Linux/Docker)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

---

## 🤝 Contributing

Contributions are welcome! If you'd like to improve the Smart Queue Manager:

1. **Fork** the repository
2. Create a feature branch: `git checkout -b feature/AmazingFeature`
3. Commit your changes: `git commit -m "Add AmazingFeature"`
4. Push to the branch: `git push origin feature/AmazingFeature`
5. Open a **Pull Request**

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).