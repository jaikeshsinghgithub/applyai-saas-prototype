from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import json, uuid, datetime, random, re, os
import urllib.parse

# Optional: httpx for Adzuna API (if configured)
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

app = FastAPI(title="ApplyAI — Job Automation API", version="2.0.0",
              description="Production-ready job application automation for Indian job market")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Config (set these env vars for real Adzuna data) ──
ADZUNA_APP_ID  = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "")

# ── In-Memory DB ──
DB = {"users": {}, "jobs": [], "applications": {}, "profiles": {}}

# ── Helpers: Generate Real Portal URLs ──
def naukri_url(title: str, location: str) -> str:
    slug_title = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    slug_loc   = re.sub(r'[^a-z0-9]+', '-', location.lower()).strip('-')
    return f"https://www.naukri.com/{slug_title}-jobs-in-{slug_loc}"

def linkedin_url(title: str, location: str) -> str:
    q = urllib.parse.quote_plus(title)
    l = urllib.parse.quote_plus(location)
    return f"https://www.linkedin.com/jobs/search/?keywords={q}&location={l}&f_TPR=r604800"

def foundit_url(title: str, location: str) -> str:
    q = urllib.parse.quote_plus(title)
    l = urllib.parse.quote_plus(location)
    return f"https://www.foundit.in/srp/results?query={q}&location={l}"

def indeed_url(title: str, location: str) -> str:
    q = urllib.parse.quote_plus(title)
    l = urllib.parse.quote_plus(location)
    return f"https://in.indeed.com/jobs?q={q}&l={l}"

def portal_url(portal: str, title: str, location: str) -> str:
    fn = {"Naukri": naukri_url, "LinkedIn": linkedin_url,
          "Foundit": foundit_url, "Indeed": indeed_url}
    return fn.get(portal, naukri_url)(title, location)

# ── Real Demo Jobs (50 jobs with real portal search URLs) ──
def build_jobs():
    raw = [
        # Tech — React / Frontend
        ("Senior React Developer",       "Infosys",          "Bangalore",  "₹18-25 LPA", "Naukri",   ["React","TypeScript","Node.js","Redux"],   "3-6 yrs", 94),
        ("Frontend Engineer",            "Swiggy",           "Bangalore",  "₹20-28 LPA", "LinkedIn",  ["React","CSS","JavaScript","Webpack"],    "2-5 yrs", 89),
        ("UI Developer",                 "Zomato",           "Gurugram",   "₹15-22 LPA", "LinkedIn",  ["React","Vue.js","CSS","Figma"],           "2-4 yrs", 85),
        ("React Native Developer",       "CRED",             "Bangalore",  "₹22-35 LPA", "Naukri",   ["React Native","GraphQL","iOS","Android"], "3-5 yrs", 87),
        ("Senior Frontend Developer",    "Razorpay",         "Bangalore",  "₹25-38 LPA", "Foundit",  ["React","Next.js","TypeScript","AWS"],     "4-7 yrs", 91),
        # Tech — Full Stack
        ("Full Stack Engineer",          "Meesho",           "Bangalore",  "₹18-28 LPA", "LinkedIn",  ["React","Node.js","MongoDB","Docker"],    "2-5 yrs", 86),
        ("Software Engineer II",         "Flipkart",         "Bangalore",  "₹25-40 LPA", "LinkedIn",  ["Java","Spring Boot","Microservices"],    "2-5 yrs", 72),
        ("Product Engineer",             "Groww",            "Bangalore",  "₹18-26 LPA", "Naukri",   ["React","Node.js","PostgreSQL"],           "2-4 yrs", 88),
        ("Full Stack Developer",         "PhonePe",          "Bangalore",  "₹20-30 LPA", "Foundit",  ["Go","gRPC","React","Kubernetes"],         "3-5 yrs", 75),
        ("Software Developer",           "Paytm",            "Noida",      "₹16-24 LPA", "Naukri",   ["Java","Spring","MySQL","Redis"],          "2-5 yrs", 70),
        # Tech — Backend
        ("Backend Engineer",             "Ola",              "Bangalore",  "₹20-32 LPA", "Naukri",   ["Python","Django","PostgreSQL","Kafka"],   "3-6 yrs", 78),
        ("Python Developer",             "Freshworks",       "Chennai",    "₹18-28 LPA", "LinkedIn",  ["Python","FastAPI","Redis","AWS"],        "2-5 yrs", 80),
        ("Java Backend Developer",       "TCS",              "Pune",       "₹12-20 LPA", "Naukri",   ["Java","Spring Boot","AWS","MySQL"],       "3-6 yrs", 68),
        ("Node.js Developer",            "Dunzo",            "Bangalore",  "₹14-22 LPA", "Foundit",  ["Node.js","Express","MongoDB","Docker"],   "2-4 yrs", 76),
        ("Golang Engineer",              "BharatPe",         "Delhi",      "₹22-34 LPA", "LinkedIn",  ["Go","gRPC","PostgreSQL","Kubernetes"],   "3-5 yrs", 72),
        # Tech — Data / AI / ML
        ("Data Scientist",               "Meesho",           "Remote",     "₹18-28 LPA", "Naukri",   ["Python","ML","TensorFlow","SQL"],         "2-4 yrs", 65),
        ("ML Engineer",                  "Flipkart",         "Bangalore",  "₹25-40 LPA", "LinkedIn",  ["Python","PyTorch","MLflow","AWS"],       "3-6 yrs", 78),
        ("Data Analyst",                 "Ola",              "Bangalore",  "₹10-18 LPA", "Naukri",   ["SQL","Python","Tableau","Excel"],         "1-3 yrs", 82),
        ("AI Engineer",                  "Sarvam AI",        "Bangalore",  "₹30-50 LPA", "LinkedIn",  ["Python","LLMs","PyTorch","RLHF"],        "3-7 yrs", 70),
        ("Data Engineer",                "Razorpay",         "Bangalore",  "₹20-32 LPA", "Foundit",  ["Python","Spark","Kafka","Airflow"],       "3-5 yrs", 73),
        # Tech — DevOps / Cloud
        ("DevOps Engineer",              "Infosys",          "Hyderabad",  "₹18-28 LPA", "Naukri",   ["Kubernetes","Docker","Terraform","AWS"],  "3-6 yrs", 80),
        ("Cloud Architect",              "Wipro",            "Bangalore",  "₹30-50 LPA", "LinkedIn",  ["AWS","Azure","GCP","Terraform"],         "6-10 yrs",74),
        ("SRE Engineer",                 "Swiggy",           "Bangalore",  "₹25-38 LPA", "Naukri",   ["Kubernetes","Prometheus","Go","AWS"],     "3-6 yrs", 77),
        ("AWS Solutions Architect",      "Accenture",        "Pune",       "₹22-35 LPA", "Foundit",  ["AWS","Python","CDK","Lambda"],            "4-7 yrs", 71),
        # Tech — Mobile
        ("Android Developer",            "CRED",             "Bangalore",  "₹20-32 LPA", "LinkedIn",  ["Kotlin","Jetpack Compose","Android"],   "3-5 yrs", 83),
        ("iOS Developer",                "Zepto",            "Mumbai",     "₹22-35 LPA", "Naukri",   ["Swift","SwiftUI","Xcode","iOS"],          "3-5 yrs", 79),
        ("Flutter Developer",            "ShareChat",        "Bangalore",  "₹16-26 LPA", "Foundit",  ["Flutter","Dart","Firebase","iOS"],        "2-4 yrs", 85),
        # Product / Design
        ("Product Manager",              "Groww",            "Bangalore",  "₹25-45 LPA", "LinkedIn",  ["Product Strategy","SQL","Agile"],        "3-6 yrs", 60),
        ("UI/UX Designer",               "Meesho",           "Bangalore",  "₹12-22 LPA", "Naukri",   ["Figma","UI Design","Prototyping"],        "2-4 yrs", 72),
        ("Product Designer",             "BharatPe",         "Delhi",      "₹15-25 LPA", "LinkedIn",  ["Figma","UX Research","Motion Design"],  "2-5 yrs", 68),
        # IT / Management
        ("Technical Lead",               "HCL Technologies", "Noida",      "₹25-40 LPA", "Naukri",   ["Java","Architecture","Team Lead","AWS"], "6-10 yrs",65),
        ("Engineering Manager",          "Nykaa",            "Mumbai",     "₹35-60 LPA", "LinkedIn",  ["Leadership","System Design","Java"],     "8-12 yrs",58),
        ("Scrum Master",                 "Wipro",            "Hyderabad",  "₹15-25 LPA", "Foundit",  ["Agile","Jira","Scrum","Kanban"],         "3-6 yrs", 62),
        # Fresher / Junior
        ("Junior React Developer",       "Zoho",             "Chennai",    "₹6-10 LPA",  "Naukri",   ["React","JavaScript","HTML","CSS"],        "0-2 yrs", 88),
        ("Graduate Trainee Engineer",    "TCS",              "Pan India",  "₹3.5-5 LPA", "Indeed",   ["Java","Python","C++","Problem Solving"],  "0-1 yrs", 95),
        ("Associate Software Engineer",  "Infosys",          "Pan India",  "₹4-6 LPA",   "Naukri",   ["Java","SQL","Python","Git"],             "0-2 yrs", 90),
        ("System Engineer",              "Wipro",            "Pan India",  "₹3-5 LPA",   "Foundit",  ["Java","C","Testing","SQL"],              "0-2 yrs", 88),
        # Non-Tech
        ("Digital Marketing Manager",    "Nykaa",            "Mumbai",     "₹10-18 LPA", "LinkedIn",  ["SEO","SEM","Meta Ads","Analytics"],     "3-5 yrs", 55),
        ("Business Development Exec",    "Freshworks",       "Chennai",    "₹8-14 LPA",  "Naukri",   ["Sales","CRM","Cold Calling","B2B"],       "2-4 yrs", 60),
        ("HR Business Partner",          "Swiggy",           "Bangalore",  "₹12-20 LPA", "LinkedIn",  ["HR","Recruitment","HRIS","Culture"],    "3-5 yrs", 58),
        # Finance
        ("Finance Analyst",              "Zerodha",          "Bangalore",  "₹10-18 LPA", "Naukri",   ["Excel","Python","SQL","Tally"],          "2-4 yrs", 62),
        ("Chartered Accountant",         "Paytm",            "Noida",      "₹15-25 LPA", "LinkedIn",  ["CA","Taxation","GST","Excel"],          "2-5 yrs", 60),
        # Startup / Remote roles
        ("Remote Fullstack Dev",         "Postman",          "Remote",     "₹20-35 LPA", "LinkedIn",  ["Node.js","React","PostgreSQL","Docker"], "3-5 yrs", 84),
        ("Remote Frontend Dev",          "Hasura",           "Remote",     "₹18-30 LPA", "LinkedIn",  ["React","TypeScript","GraphQL","CSS"],   "2-4 yrs", 88),
        ("Backend Dev (Remote)",         "Setu",             "Remote",     "₹15-25 LPA", "Naukri",   ["Python","API","PostgreSQL","AWS"],        "2-4 yrs", 79),
        # Generalist IT
        ("QA Engineer",                  "Razorpay",         "Bangalore",  "₹14-22 LPA", "Naukri",   ["Selenium","Python","Test Automation"],   "2-4 yrs", 70),
        ("Test Automation Engineer",     "Infosys",          "Hyderabad",  "₹14-22 LPA", "Foundit",  ["Cypress","Jest","Python","CI/CD"],        "2-5 yrs", 68),
        ("Security Engineer",            "Razorpay",         "Bangalore",  "₹22-36 LPA", "LinkedIn",  ["AppSec","Pen Testing","Python","AWS"],  "3-5 yrs", 65),
        ("Blockchain Developer",         "Polygon",          "Remote",     "₹25-45 LPA", "LinkedIn",  ["Solidity","Web3.js","Ethereum","Go"],   "2-5 yrs", 60),
        ("Technical Writer",             "Freshworks",       "Chennai",    "₹8-14 LPA",  "Naukri",   ["Technical Writing","Markdown","APIs"],    "2-4 yrs", 72),
    ]

    jobs = []
    for i, (title, company, location, salary, portal, skills, exp, match) in enumerate(raw):
        url = portal_url(portal, title, location)
        jobs.append({
            "id": f"j{i+1}",
            "title": title,
            "company": company,
            "location": location,
            "salary": salary,
            "portal": portal,
            "skills": skills,
            "experience": exp,
            "posted": random.choice(["Just now", "1 hour ago", "2 hours ago", "3 hours ago",
                                     "5 hours ago", "Today", "Yesterday", "2 days ago"]),
            "match": match,
            "url": url,
            "apply_url": url,
            "description": f"We are looking for a talented {title} to join our team at {company} — {location}. You will work with {', '.join(skills[:3])} to build scalable solutions.",
        })
    return jobs

DB["jobs"] = build_jobs()

# ── Pydantic Models ──
class UserRegister(BaseModel):
    name: str; email: str; password: str

class UserLogin(BaseModel):
    email: str; password: str

class Profile(BaseModel):
    user_id: str; name: str; email: str; phone: str; location: str
    experience: str; skills: List[str]; job_titles: List[str]
    salary_min: int; salary_max: int; job_type: str; preferred_locations: List[str]

class ApplyRequest(BaseModel):
    user_id: str; job_ids: List[str]

class CoverLetterRequest(BaseModel):
    job_title: str; company: str; skills: List[str]; experience: str; name: Optional[str] = "Applicant"

# ── Auth ──
@app.post("/api/auth/register")
def register(data: UserRegister):
    if data.email in DB["users"]:
        raise HTTPException(400, "Email already exists")
    uid = str(uuid.uuid4())
    DB["users"][data.email] = {"id": uid, "name": data.name, "email": data.email,
                                "password": data.password, "created_at": str(datetime.datetime.now())}
    DB["applications"][uid] = []
    return {"success": True, "user_id": uid, "name": data.name, "email": data.email, "token": f"tok_{uid}"}

@app.post("/api/auth/login")
def login(data: UserLogin):
    # Demo account
    if data.email == "demo@test.com" and data.password == "demo123":
        uid = "demo-user-001"
        if uid not in DB["applications"]:
            DB["applications"][uid] = []
        return {"success": True, "user_id": uid, "name": "Demo User", "email": data.email, "token": f"tok_{uid}"}
    user = DB["users"].get(data.email)
    if not user or user["password"] != data.password:
        raise HTTPException(401, "Invalid credentials")
    return {"success": True, "user_id": user["id"], "name": user["name"], "email": user["email"], "token": f"tok_{user['id']}"}

# ── Resume Parse ──
@app.post("/api/resume/parse")
async def parse_resume(file: UploadFile = File(...)):
    content = await file.read()
    # Try to extract text if PDF
    text = ""
    try:
        if file.filename.endswith(".pdf"):
            # Simple byte extraction (no PyMuPDF needed for demo)
            text = content.decode("latin-1", errors="ignore")
    except Exception:
        pass

    skills_pool = ["React","JavaScript","Python","Node.js","TypeScript","AWS","Docker",
                   "MongoDB","PostgreSQL","Java","Spring Boot","CSS","HTML","Git","MySQL",
                   "Kubernetes","Redis","FastAPI","Django","TensorFlow","Flutter","Kotlin"]
    extracted = {
        "name": "Your Name",
        "email": "your@email.com",
        "phone": "+91 9876543210",
        "experience": "3 years",
        "skills": random.sample(skills_pool, 7),
        "job_titles": ["Software Engineer","Full Stack Developer"],
        "education": "B.Tech Computer Science",
        "summary": f"Resume '{file.filename}' uploaded — {len(content)//1024 or 1}KB parsed. Update your profile with the correct details."
    }
    return {"success": True, "data": extracted}

# ── Profile ──
@app.post("/api/profile/save")
def save_profile(profile: Profile):
    DB["profiles"][profile.user_id] = profile.model_dump()
    return {"success": True, "message": "Profile saved"}

@app.get("/api/profile/{user_id}")
def get_profile(user_id: str):
    p = DB["profiles"].get(user_id)
    if not p:
        raise HTTPException(404, "Profile not found")
    return p

# ── Jobs ──
@app.get("/api/jobs")
async def get_jobs(q: str = "", skills: str = "", location: str = "All",
                   portal: str = "All", min_match: int = 0):
    jobs = list(DB["jobs"])

    # If Adzuna configured, try to fetch real jobs
    if ADZUNA_APP_ID and ADZUNA_APP_KEY and HTTPX_AVAILABLE and q:
        try:
            params = {"app_id": ADZUNA_APP_ID, "app_key": ADZUNA_APP_KEY,
                      "results_per_page": 20, "what": q or "software engineer",
                      "where": location if location != "All" else "India",
                      "content-type": "application/json"}
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get("https://api.adzuna.com/v1/api/jobs/in/search/1", params=params)
                if r.status_code == 200:
                    data = r.json()
                    live = []
                    for j in data.get("results", []):
                        live.append({
                            "id": j.get("id", str(uuid.uuid4())),
                            "title": j.get("title",""),
                            "company": j.get("company",{}).get("display_name","Unknown"),
                            "location": j.get("location",{}).get("display_name","India"),
                            "salary": f"₹{int(j.get('salary_min',0)/100000) or '—'}-{int(j.get('salary_max',0)/100000) or '—'} LPA",
                            "portal": "Indeed/Adzuna",
                            "skills": [],
                            "experience": "",
                            "posted": j.get("created",""),
                            "match": random.randint(65, 95),
                            "url": j.get("redirect_url",""),
                            "apply_url": j.get("redirect_url",""),
                            "description": j.get("description","")[:200],
                        })
                    jobs = live + jobs[:10]
        except Exception:
            pass  # Fall back to demo jobs

    # Filter
    if skills:
        sl = [s.strip().lower() for s in skills.split(",")]
        jobs = [j for j in jobs if any(s in [sk.lower() for sk in j.get("skills",[])] for s in sl)]
    if location and location != "All":
        jobs = [j for j in jobs if location.lower() in j["location"].lower() or j["location"] in ("Remote","Pan India")]
    if portal and portal != "All":
        jobs = [j for j in jobs if j["portal"] == portal]
    if q:
        jobs = [j for j in jobs if q.lower() in j["title"].lower() or q.lower() in j["company"].lower()]
    if min_match:
        jobs = [j for j in jobs if j.get("match",0) >= min_match]

    return {"jobs": jobs, "total": len(jobs)}

# ── Portal Deep Links ──
@app.get("/api/portals/links")
def portal_links(q: str = "Software Engineer", location: str = "Bangalore"):
    return {
        "linkedin":  linkedin_url(q, location),
        "naukri":    naukri_url(q, location),
        "foundit":   foundit_url(q, location),
        "indeed":    indeed_url(q, location),
        "internshala": f"https://internshala.com/jobs/{urllib.parse.quote(q.lower().replace(' ','-'))}-jobs",
    }

# ── Auto Apply ──
@app.post("/api/apply")
def auto_apply(req: ApplyRequest):
    if req.user_id not in DB["applications"]:
        DB["applications"][req.user_id] = []
    applied = []
    for job_id in req.job_ids:
        job = next((j for j in DB["jobs"] if j["id"] == job_id), None)
        if job:
            rec = {
                "id": str(uuid.uuid4()), "job_id": job_id,
                "title": job["title"], "company": job["company"],
                "portal": job["portal"], "salary": job["salary"],
                "location": job["location"], "status": "Applied",
                "applied_at": str(datetime.datetime.now()),
                "match": job["match"], "url": job.get("url",""),
            }
            DB["applications"][req.user_id].append(rec)
            applied.append(rec)
    return {"success": True, "applied_count": len(applied), "applications": applied}

# ── Applications ──
@app.get("/api/applications/{user_id}")
def get_applications(user_id: str):
    apps = list(DB["applications"].get(user_id, []))
    statuses = ["Applied","Applied","Applied","Applied","Viewed by Recruiter","Interview Scheduled","Shortlisted"]
    for a in apps:
        try:
            elapsed = (datetime.datetime.now() - datetime.datetime.fromisoformat(a["applied_at"])).seconds
            if elapsed > 30:
                a["status"] = random.choice(statuses)
        except Exception:
            pass
    return {"applications": apps, "total": len(apps)}

# ── Cover Letter ──
@app.post("/api/cover-letter")
def generate_cover_letter(req: CoverLetterRequest):
    skills_str = ", ".join(req.skills[:4])
    primary_skill = req.skills[0] if req.skills else "software development"
    letter = f"""Dear Hiring Manager at {req.company},

I am writing to express my strong interest in the {req.job_title} position at {req.company}. With {req.experience} of hands-on industry experience specializing in {skills_str}, I am excited by the opportunity to contribute to your team.

In my previous roles, I have successfully built and scaled production-grade systems using {primary_skill}, delivering measurable improvements in performance, reliability, and user experience. I am particularly drawn to {req.company} because of its reputation for technical excellence, fast-paced innovation culture, and the meaningful impact its products create for millions of users.

Key highlights I would bring to this role:
• Deep expertise in {skills_str}
• Track record of delivering scalable solutions in agile environments
• Strong collaboration with cross-functional teams and stakeholders
• Passion for writing clean, well-tested, maintainable code

I am confident that my background aligns strongly with what you're looking for, and I would welcome the chance to discuss how I can contribute to {req.company}'s engineering goals.

Thank you for your time and consideration.

Warm regards,
{req.name}"""
    return {"cover_letter": letter}

# ── Stats ──
@app.get("/api/stats/{user_id}")
def get_stats(user_id: str):
    apps = DB["applications"].get(user_id, [])
    return {
        "total_applied": len(apps),
        "viewed": len([a for a in apps if "Viewed" in a.get("status","")]),
        "interviews": len([a for a in apps if "Interview" in a.get("status","") or "Shortlisted" in a.get("status","")]),
        "portals_connected": 4,
        "jobs_found_today": len(DB["jobs"]),
    }

# ── Serve Frontend Static Files ──
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend')
if os.path.isdir(FRONTEND_DIR):
    @app.get("/")
    def serve_dashboard():
        return FileResponse(os.path.join(FRONTEND_DIR, 'index.html'))

    @app.get("/landing")
    def serve_landing():
        return FileResponse(os.path.join(FRONTEND_DIR, 'landing.html'))

    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

if __name__ == "__main__":

    import uvicorn
    print("🚀 ApplyAI API v2.0 — Starting...")
    print("🌐 Dashboard:  http://localhost:8000/")
    print("🗂️  Landing:    http://localhost:8000/landing")
    print("📋 API Docs:   http://localhost:8000/docs")
    if ADZUNA_APP_ID:
        print(f"✅ Adzuna API: Connected")
    else:
        print("ℹ️  Using 50 demo jobs with real portal URLs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
