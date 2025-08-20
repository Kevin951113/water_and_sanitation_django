
# ParkSpero - Melbourne Parking App

**Live Website:** https://www.mel-borntowinta12.me/

> This notebook contains an overview and setup guide. Run the cells if you'd like to execute commands locally (adjust paths as needed).


## Project Overview
ParkSpero is a Django-based web application that provides **live parking availability**, **historical analytics**, and **demand prediction** for Melbourne streets.

**Purpose**  
Help drivers **quickly find available parking**, **plan ahead based on predicted availability**, and **reduce time spent circling the city** — making parking in Melbourne more efficient and less stressful. By leveraging real-time data and historical trends, ParkSpero supports both **individual convenience** and **overall traffic flow improvement**.


## 📂 Project Structure
```
 └── parkingapp-django/
     ├── config/                # Django project configuration
     ├── main/                  # Main application
     │   ├── services/          # Business logic and API services
     │   ├── static/            # Static files (CSS, JS, images)
     │   ├── templates/         # HTML templates
     │   └── views/             # Django views
     ├── venv/                  # Virtual environment
     ├── manage.py              # Django management script
     ├── requirements.txt       # Python dependencies
     └── db.sqlite3             # SQLite database (for dev)
```

## 🚀 Setup Instructions
### 1️⃣ Clone the repository
# Use this cell to clone the repo (edit the path as you need)
!git clone https://github.com/Kevin951113/ParkSpero-Melbourne.git
%cd ParkSpero-Melbourne

### 2️⃣ Create a Virtual Environment
#### Windows (PowerShell)
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate

#### Mac/Linux
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

### 3️⃣ Install dependencies
pip install -r requirements.txt
### 4️⃣ Run the Django server
python manage.py runserver

## Access the App
- Local dev: `http://127.0.0.1:8000`
- Production: https://www.mel-borntowinta12.me/


## Notes
- Static files are located in `main/static/`.
- HTML templates are located in `main/templates/`.
- Business logic for analytics, predictions, and live parking updates is inside `main/services/`.
