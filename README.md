# ApplyAI — Job Application Automation SaaS (Prototype)

![ApplyAI Dashboard](screenshot_dashboard_auth.png)

### 🔍 Find Jobs View
![ApplyAI Find Jobs](screenshot_find_jobs.png)

### 🗂️ Landing Page View
![ApplyAI Landing Page](screenshot_landing.png)

ApplyAI is a full-stack job application automation prototype designed for the Indian job market. It includes a FastAPI backend, a responsive frontend dashboard, and a companion Chrome Extension to streamline the job search and application process.

## 🚀 Features

### 🟢 Fully Functional
*   **Adzuna API Integration:** Connects to the real-world Adzuna Job API to fetch live job listings.
*   **Smart Deep Links:** Dynamically generates accurate, pre-filtered search URLs for LinkedIn, Naukri, Indeed, and Foundit.
*   **Automated Cover Letters:** Generates personalized cover letters based on user skills, experience, and the specific job title.
*   **Chrome Extension UI:** A fully functional extension popup and content script architecture ready to be injected into job portals.
*   **Responsive Dashboard:** A polished, modern web interface.

### 🟡 Mocked for Demo Purposes
*To keep this repository lightweight and easy to run locally, the following features are simulated:*
*   **Database:** Uses an in-memory datastore (clears on restart) instead of a heavy PostgreSQL/MongoDB setup.
*   **Auto-Apply:** Simulates the application pipeline and status updates (Viewed, Shortlisted) without requiring actual bot logins/automation via Playwright.
*   **Resume Parsing:** Simulates skill extraction rather than using heavy OCR libraries.

## 💻 Tech Stack
*   **Backend:** Python, FastAPI, Uvicorn
*   **Frontend:** Vanilla JavaScript, HTML5, CSS3, Tailwind (or custom CSS)
*   **Browser Extension:** Chrome Manifest V3, JavaScript

## 🛠️ How to Run Locally

### 1. Start the Backend
Make sure you have Python installed, then run:

```bash
# Install required packages
pip install fastapi uvicorn pydantic httpx python-multipart

# Start the server
cd backend
python main.py
```
*The server will start on `http://localhost:8000`*

### 2. Load the Chrome Extension
1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** in the top right corner.
3. Click **Load unpacked**.
4. Select the `extension/` folder from this repository.

### 3. (Optional) Enable Live Data
To fetch real jobs instead of the demo dataset, set your Adzuna API credentials in your environment variables before starting the backend:
```bash
export ADZUNA_APP_ID="your_app_id"
export ADZUNA_APP_KEY="your_app_key"
```

## 🤝 Contributing
This is an open-source prototype. Feel free to fork the repository, integrate a real database, or build out the Playwright/Selenium automation scripts for the `auto-apply` feature!

## 📜 License
[MIT License](LICENSE)
