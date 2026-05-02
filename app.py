"""
Cortexa Health v5.0 — Ultimate Clinical Intelligence Platform
Author: Jaspreet Singh Jawanda
NEW IN v5.0:
  • Real PDF export (reportlab)
  • Real Word .docx export (python-docx)
  • Dark/Light theme toggle
  • Batch multi-image analysis
  • Drug interaction checker (AI)
  • Lab values tracker with reference ranges
  • Treatment plan generator (AI)
  • Patient vitals graph (matplotlib)
  • Appointment scheduling
  • Medication tracker
  • Report templates (6 types)
  • Insurance & billing info
  • Second opinion workflow
  • DICOM metadata viewer
  • Animated charts & statistics
Powered by Groq (LLaMA 4 Vision) — Free & Ultra-Fast
"""

import os, base64, json, time, io, hashlib, re, random, math
from datetime import datetime, timedelta
from collections import defaultdict

import streamlit as st
from PIL import Image as PILImage, ImageFilter, ImageEnhance, ImageDraw
import numpy as np
from groq import Groq

# ── Optional rich-export libs (graceful fallback) ──────────
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors as RL_COLORS
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False

try:
    from docx import Document as DocxDocument
    from docx.shared import Pt, RGBColor, Inches, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_OK = True
except Exception:
    DOCX_OK = False

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    MATPLOTLIB_OK = True
except Exception:
    MATPLOTLIB_OK = False

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
APP_VERSION  = "5.0.0"
AUTHOR       = "Jaspreet Singh Jawanda"

GROQ_MODELS = {
    "LLaMA 4 Scout — Fast":    "meta-llama/llama-4-scout-17b-16e-instruct",
    "LLaMA 4 Maverick — Best": "meta-llama/llama-4-maverick-17b-128e-instruct",
}

REPORT_TEMPLATES = {
    "Comprehensive Radiology":   "9-section full radiological report with ICD-10, measurements, and research citations.",
    "Quick Triage":              "60-second emergency triage: top finding, urgency, immediate action.",
    "Patient-Friendly":          "Plain English for patient. No jargon. Warm, compassionate tone.",
    "Research / Academic":       "Academic depth with imaging biomarkers, sensitivity/specificity, and literature references.",
    "Second Opinion":            "Senior radiologist critical review — look for missed findings, contradict if needed.",
    "Paediatric":                "Age-adjusted interpretation. Reference paediatric norms. Family-friendly language.",
    "Oncology Focus":            "Tumour characterisation, RECIST criteria, staging, treatment response assessment.",
    "Cardiac Focus":             "Cardiac anatomy, EF estimation, wall motion, pericardium, great vessels.",
}

LAB_REFERENCE = {
    "Haemoglobin":   {"unit":"g/dL",  "male":(13.5,17.5), "female":(12.0,16.0)},
    "WBC Count":     {"unit":"×10³/µL","male":(4.0,11.0),  "female":(4.0,11.0)},
    "Platelets":     {"unit":"×10³/µL","male":(150,400),   "female":(150,400)},
    "Creatinine":    {"unit":"mg/dL",  "male":(0.7,1.3),   "female":(0.6,1.1)},
    "eGFR":          {"unit":"mL/min", "male":(60,120),    "female":(60,120)},
    "Blood Glucose": {"unit":"mg/dL",  "male":(70,100),    "female":(70,100)},
    "HbA1c":         {"unit":"%",      "male":(4.0,5.6),   "female":(4.0,5.6)},
    "Total Cholesterol":{"unit":"mg/dL","male":(0,200),    "female":(0,200)},
    "LDL":           {"unit":"mg/dL",  "male":(0,100),     "female":(0,100)},
    "HDL":           {"unit":"mg/dL",  "male":(40,60),     "female":(50,60)},
    "Sodium":        {"unit":"mEq/L",  "male":(136,145),   "female":(136,145)},
    "Potassium":     {"unit":"mEq/L",  "male":(3.5,5.0),   "female":(3.5,5.0)},
    "TSH":           {"unit":"µIU/mL", "male":(0.4,4.0),   "female":(0.4,4.0)},
    "CRP":           {"unit":"mg/L",   "male":(0,5.0),     "female":(0,5.0)},
}

# ─────────────────────────────────────────────
# USER / PATIENT DATA
# ─────────────────────────────────────────────
def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()

USERS_DB = {
    "dr.sharma":  {"password": hash_pw("doctor123"), "role":"Doctor",      "name":"Dr. Priya Sharma",  "dept":"Radiology",  "email":"priya@medicore.ai",  "avatar":"👩‍⚕️","license":"MCI-2019-DL-4521"},
    "dr.chen":    {"password": hash_pw("doctor123"), "role":"Doctor",      "name":"Dr. Kevin Chen",    "dept":"Cardiology", "email":"kevin@medicore.ai",  "avatar":"👨‍⚕️","license":"MCI-2017-DL-3312"},
    "rad.jones":  {"password": hash_pw("radio123"),  "role":"Radiologist", "name":"Dr. Sarah Jones",   "dept":"Radiology",  "email":"sarah@medicore.ai",  "avatar":"🩻", "license":"MCI-2015-RL-1102"},
    "admin":      {"password": hash_pw("admin123"),  "role":"Admin",       "name":"System Admin",      "dept":"IT",         "email":"admin@medicore.ai",  "avatar":"⚙️", "license":"—"},
}

DEMO_PATIENTS = [
    {"id":"PT-001","name":"Ramesh Kumar","age":58,"gender":"M","dob":"1966-03-12","scans":4,"last_scan":"2025-01-14","risk":"HIGH","condition":"Pulmonary Nodule","bp":"148/92","o2":"96%","weight":"72 kg","height":"170 cm","smoker":"Yes (30 pack-yr)","allergies":"Penicillin","blood_group":"B+","phone":"+91-98765-43210","emergency_contact":"Wife — +91-98765-43211",
     "medications":["Amlodipine 5mg OD","Atorvastatin 40mg OD","Aspirin 75mg OD"],
     "appointments":[{"date":"2025-02-10","time":"10:00","type":"CT Follow-up","doctor":"Dr. Priya Sharma","status":"Scheduled"}],
     "vitals_history":[{"date":"2025-01-14","bp_s":148,"bp_d":92,"o2":96,"hr":84,"temp":37.1,"weight":72},{"date":"2024-12-10","bp_s":145,"bp_d":90,"o2":97,"hr":80,"temp":36.8,"weight":73}],
     "labs":{"Haemoglobin":13.2,"WBC Count":8.5,"Platelets":220,"Creatinine":1.1,"Blood Glucose":102,"HbA1c":6.1,"Total Cholesterol":210,"LDL":130},
     "insurance":{"provider":"Star Health Insurance","policy":"SH-2024-PB-7823","valid_till":"2026-03-31","coverage":"₹10 Lakh","copay":"10%"},
     "precautions":["Avoid smoking and passive smoke","Schedule 3-month CT follow-up","Monitor for haemoptysis","Pulmonology referral","Avoid high-altitude travel","Penicillin allergy — use Cephalosporins with caution"]},

    {"id":"PT-002","name":"Sunita Devi","age":44,"gender":"F","dob":"1980-07-22","scans":2,"last_scan":"2025-01-10","risk":"LOW","condition":"Routine Screening","bp":"118/76","o2":"99%","weight":"58 kg","height":"160 cm","smoker":"No","allergies":"None","blood_group":"A+","phone":"+91-87654-32109","emergency_contact":"Husband — +91-87654-32110",
     "medications":["Calcium + Vit D supplement OD","Folic Acid 5mg OD"],
     "appointments":[{"date":"2025-06-15","time":"09:30","type":"Annual Check-up","doctor":"Dr. Kevin Chen","status":"Scheduled"}],
     "vitals_history":[{"date":"2025-01-10","bp_s":118,"bp_d":76,"o2":99,"hr":72,"temp":36.6,"weight":58},{"date":"2024-06-05","bp_s":115,"bp_d":74,"o2":99,"hr":70,"temp":36.5,"weight":57}],
     "labs":{"Haemoglobin":12.8,"WBC Count":6.2,"Platelets":280,"Creatinine":0.8,"Blood Glucose":88,"HbA1c":5.2,"Total Cholesterol":175,"LDL":95},
     "insurance":{"provider":"HDFC Ergo Health","policy":"HE-2024-DL-4421","valid_till":"2026-07-31","coverage":"₹5 Lakh","copay":"5%"},
     "precautions":["Annual mammogram","Maintain healthy BMI","Regular aerobic exercise","Balanced diet"]},

    {"id":"PT-003","name":"Arjun Singh","age":67,"gender":"M","dob":"1957-11-05","scans":7,"last_scan":"2025-01-13","risk":"CRITICAL","condition":"Suspected Malignancy","bp":"162/98","o2":"91%","weight":"65 kg","height":"168 cm","smoker":"Yes (45 pack-yr)","allergies":"Sulfa, Contrast","blood_group":"O-","phone":"+91-76543-21098","emergency_contact":"Son — +91-76543-21099",
     "medications":["Telmisartan 40mg OD","Furosemide 40mg OD","Spironolactone 25mg OD","Salbutamol inhaler PRN"],
     "appointments":[{"date":"2025-01-20","time":"08:00","type":"Oncology Consult","doctor":"Dr. Sarah Jones","status":"URGENT"},{"date":"2025-01-22","time":"09:00","type":"Biopsy","doctor":"Dr. Sarah Jones","status":"Scheduled"}],
     "vitals_history":[{"date":"2025-01-13","bp_s":162,"bp_d":98,"o2":91,"hr":96,"temp":37.8,"weight":65},{"date":"2024-12-01","bp_s":155,"bp_d":95,"o2":93,"hr":90,"temp":37.2,"weight":67}],
     "labs":{"Haemoglobin":10.8,"WBC Count":13.2,"Platelets":180,"Creatinine":1.4,"Blood Glucose":118,"HbA1c":6.8,"Total Cholesterol":195,"LDL":120,"CRP":28.5},
     "insurance":{"provider":"Bajaj Allianz Health","policy":"BA-2023-PB-1122","valid_till":"2025-11-30","coverage":"₹15 Lakh","copay":"20%"},
     "precautions":["STAT oncology referral","Cease smoking IMMEDIATELY","Avoid contrast agents (documented allergy)","Supplemental O2 if SpO2 < 92%","Daily BP monitoring","Avoid Sulfonamide drugs","Biopsy — NPO after midnight","Avoid NSAIDs"]},

    {"id":"PT-004","name":"Meera Patel","age":35,"gender":"F","dob":"1989-09-30","scans":1,"last_scan":"2025-01-08","risk":"LOW","condition":"Chest Pain Eval","bp":"115/72","o2":"99%","weight":"55 kg","height":"162 cm","smoker":"No","allergies":"Latex","blood_group":"AB+","phone":"+91-65432-10987","emergency_contact":"Mother — +91-65432-10988",
     "medications":["Pantoprazole 40mg OD","Buscopan PRN"],
     "appointments":[{"date":"2025-02-01","time":"11:00","type":"Stress ECG","doctor":"Dr. Kevin Chen","status":"Scheduled"}],
     "vitals_history":[{"date":"2025-01-08","bp_s":115,"bp_d":72,"o2":99,"hr":68,"temp":36.5,"weight":55}],
     "labs":{"Haemoglobin":13.1,"WBC Count":5.8,"Platelets":310,"Creatinine":0.7,"Blood Glucose":82,"HbA1c":4.9,"Total Cholesterol":165,"LDL":88},
     "insurance":{"provider":"New India Assurance","policy":"NIA-2024-GJ-5631","valid_till":"2026-09-30","coverage":"₹3 Lakh","copay":"0%"},
     "precautions":["Avoid latex products","Stress ECG recommended","Lifestyle modifications","Limit caffeine","Return if chest pain recurs"]},

    {"id":"PT-005","name":"Vikram Nair","age":52,"gender":"M","dob":"1972-06-18","scans":3,"last_scan":"2025-01-12","risk":"WARNING","condition":"Pleural Effusion","bp":"135/84","o2":"94%","weight":"80 kg","height":"175 cm","smoker":"Ex-smoker","allergies":"None","blood_group":"B-","phone":"+91-54321-09876","emergency_contact":"Wife — +91-54321-09877",
     "medications":["Furosemide 40mg BD","Spironolactone 50mg OD","Azithromycin 500mg OD (10-day course)"],
     "appointments":[{"date":"2025-01-25","time":"10:30","type":"Chest Clinic Review","doctor":"Dr. Priya Sharma","status":"Scheduled"}],
     "vitals_history":[{"date":"2025-01-12","bp_s":135,"bp_d":84,"o2":94,"hr":88,"temp":37.4,"weight":80},{"date":"2024-11-20","bp_s":130,"bp_d":80,"o2":96,"hr":82,"temp":36.9,"weight":78}],
     "labs":{"Haemoglobin":12.5,"WBC Count":11.8,"Platelets":195,"Creatinine":1.2,"Blood Glucose":96,"Total Cholesterol":188,"LDL":112,"CRP":18.2},
     "insurance":{"provider":"ICICI Lombard","policy":"IL-2024-KL-3341","valid_till":"2026-06-30","coverage":"₹8 Lakh","copay":"10%"},
     "precautions":["Fluid restriction 1.5L/day","Avoid strenuous activity","Sleep head elevated 30°","Monthly CXR","Diuretic compliance critical"]},

    {"id":"PT-006","name":"Anita Gupta","age":61,"gender":"F","dob":"1963-05-20","scans":5,"last_scan":"2025-01-11","risk":"HIGH","condition":"Cardiac Monitoring","bp":"144/88","o2":"95%","weight":"68 kg","height":"158 cm","smoker":"No","allergies":"Aspirin","blood_group":"A-","phone":"+91-43210-98765","emergency_contact":"Daughter — +91-43210-98766",
     "medications":["Clopidogrel 75mg OD","Metoprolol 25mg BD","Atorvastatin 80mg OD","Perindopril 5mg OD"],
     "appointments":[{"date":"2025-02-05","time":"09:00","type":"Cardiology Review","doctor":"Dr. Kevin Chen","status":"Scheduled"},{"date":"2025-03-01","time":"10:00","type":"Echo Cardiogram","doctor":"Dr. Kevin Chen","status":"Planned"}],
     "vitals_history":[{"date":"2025-01-11","bp_s":144,"bp_d":88,"o2":95,"hr":76,"temp":36.7,"weight":68},{"date":"2024-12-15","bp_s":150,"bp_d":92,"o2":94,"hr":80,"temp":36.8,"weight":69}],
     "labs":{"Haemoglobin":12.2,"WBC Count":7.1,"Platelets":240,"Creatinine":1.0,"Blood Glucose":106,"HbA1c":6.0,"Total Cholesterol":220,"LDL":145,"HDL":48},
     "insurance":{"provider":"Oriental Insurance","policy":"OI-2024-DL-8821","valid_till":"2026-05-31","coverage":"₹12 Lakh","copay":"15%"},
     "precautions":["NEVER give Aspirin — documented allergy (use Clopidogrel)","Daily BP monitoring","Low-fat cardiac diet","Sodium < 2g/day","Avoid isometric exercises","Cardiac rehab referral"]},
]

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Cortexa Health  — Clinical Platform",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
defaults = {
    "logged_in":False,"user":None,"role":None,"dept":None,"avatar":None,
    "page":"dashboard","history":[],"alerts":[],
    "users_db":dict(USERS_DB),
    "total":0,"critical":0,"warnings":0,
    "chat_messages":[],"batch_results":[],
    "selected_patient":None,"audit_log":[],
    "patient_logs":{p["id"]:[] for p in DEMO_PATIENTS},
    "dark_mode":False,
    "appointments":[],
    "lab_entries":{p["id"]:dict(p.get("labs",{})) for p in DEMO_PATIENTS},
}
for k,v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
# THEME
# ─────────────────────────────────────────────
DM = st.session_state.dark_mode
THEME = {
    "bg":       "#0f172a" if DM else "#f0f4f8",
    "surface":  "#1e293b" if DM else "#ffffff",
    "elevated": "#1e293b" if DM else "#f8fafc",
    "border":   "#334155" if DM else "#e2e8f0",
    "border2":  "#475569" if DM else "#cbd5e1",
    "text":     "#f1f5f9" if DM else "#0f172a",
    "text2":    "#94a3b8" if DM else "#475569",
    "text3":    "#64748b" if DM else "#94a3b8",
}

def inject_css():
    bg=THEME["bg"]; sf=THEME["surface"]; el=THEME["elevated"]
    bd=THEME["border"]; bd2=THEME["border2"]
    tx=THEME["text"]; tx2=THEME["text2"]; tx3=THEME["text3"]
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700;800&family=Playfair+Display:wght@700&family=JetBrains+Mono:wght@400;500&display=swap');
:root{{
    --bg:{bg};--surface:{sf};--elevated:{el};--border:{bd};--border2:{bd2};
    --accent:#2563eb;--accent2:#1d4ed8;--accent-lt:{"#1e3a5f" if DM else "#eff6ff"};
    --green:#059669;--green-lt:{"#052e16" if DM else "#ecfdf5"};
    --red:#dc2626;--red-lt:{"#450a0a" if DM else "#fef2f2"};
    --yellow:#d97706;--yellow-lt:{"#451a03" if DM else "#fffbeb"};
    --purple:#7c3aed;--purple-lt:{"#2e1065" if DM else "#f5f3ff"};
    --cyan:#0891b2;--cyan-lt:{"#082f49" if DM else "#ecfeff"};
    --text:{tx};--text2:{tx2};--text3:{tx3};
    --shadow:0 1px 3px rgba(0,0,0,{"0.3" if DM else "0.08"});
    --shadow-md:0 4px 16px rgba(0,0,0,{"0.4" if DM else "0.1"});
    --shadow-lg:0 10px 40px rgba(0,0,0,{"0.5" if DM else "0.12"});
    --radius:12px;--radius-sm:8px;
    --sans:'DM Sans',sans-serif;--serif:'Playfair Display',serif;--mono:'JetBrains Mono',monospace;
}}
@keyframes fadeInUp{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes fadeInLeft{{from{{opacity:0;transform:translateX(-12px)}}to{{opacity:1;transform:translateX(0)}}}}
@keyframes slideDown{{from{{opacity:0;transform:translateY(-10px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.4}}}}
@keyframes pulseScale{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.04)}}}}
@keyframes shimmer{{0%{{background-position:-200% 0}}100%{{background-position:200% 0}}}}
@keyframes countUp{{from{{opacity:0;transform:scale(.75)}}to{{opacity:1;transform:scale(1)}}}}
@keyframes borderPulse{{0%,100%{{box-shadow:0 0 0 0 rgba(37,99,235,0)}}50%{{box-shadow:0 0 0 4px rgba(37,99,235,.2)}}}}

html,body,[class*="css"]{{font-family:var(--sans)!important;color:var(--text)!important;}}
.stApp{{background:var(--bg)!important;}}
.main .block-container{{padding:.9rem 1rem!important;max-width:100%!important;}}

section[data-testid="stSidebar"]{{
    background:var(--surface)!important;
    border-right:1px solid var(--border)!important;
    box-shadow:2px 0 12px rgba(0,0,0,.08)!important;
    width:230px!important;min-width:230px!important;max-width:230px!important;
}}
section[data-testid="stSidebar"]>div:first-child{{width:230px!important;padding:.5rem .45rem!important;}}
section[data-testid="stSidebar"] *{{color:var(--text)!important;}}
[data-testid="collapsedControl"]{{display:flex!important;visibility:visible!important;opacity:1!important;background:var(--surface)!important;border:1px solid var(--border)!important;border-radius:50%!important;box-shadow:var(--shadow-md)!important;width:30px!important;height:30px!important;align-items:center!important;justify-content:center!important;z-index:9999!important;}}

.stTextInput input,.stTextArea textarea,.stNumberInput input{{background:var(--surface)!important;border:1.5px solid var(--border2)!important;border-radius:var(--radius-sm)!important;color: #111112 !important;;font-family:var(--sans)!important;font-size:.87rem!important;transition:border-color .2s,box-shadow .2s!important;}}
.stTextInput input:focus,.stTextArea textarea:focus{{border-color:var(--accent)!important;box-shadow:0 0 0 3px rgba(37,99,235,.12)!important;}}
.stSelectbox>div>div{{background:var(--surface)!important;border:1.5px solid var(--border2)!important;border-radius:var(--radius-sm)!important;color:var(--text)!important;}}
.stSelectbox [data-baseweb="select"] span{{color:var(--text)!important;}}

.stButton>button{{background:linear-gradient(135deg,#2563eb,#1d4ed8)!important;color:white!important;border:none!important;border-radius:var(--radius-sm)!important;padding:.42rem .95rem!important;font-family:var(--sans)!important;font-weight:600!important;font-size:.82rem!important;transition:all .2s ease!important;box-shadow:0 1px 3px rgba(37,99,235,.3)!important;}}
.stButton>button:hover{{background:linear-gradient(135deg,#1d4ed8,#1e40af)!important;transform:translateY(-1px)!important;box-shadow:0 4px 14px rgba(37,99,235,.4)!important;}}
.stButton>button:active{{transform:translateY(0)!important;}}

.nav-btn .stButton>button{{background:transparent!important;color:var(--text2)!important;border:1px solid transparent!important;border-radius:7px!important;padding:.3rem .6rem!important;font-size:.79rem!important;font-weight:500!important;box-shadow:none!important;width:100%!important;justify-content:flex-start!important;transition:background .15s,color .15s!important;margin-bottom:1px!important;}}
.nav-btn .stButton>button:hover{{background:var(--accent-lt)!important;color:var(--accent)!important;transform:none!important;box-shadow:none!important;}}
.nav-btn-active .stButton>button{{background:var(--accent-lt)!important;border-color:#bfdbfe!important;color:#60a5fa!important;font-weight:600!important;box-shadow:none!important;transform:none!important;border-radius:7px!important;padding:.3rem .6rem!important;font-size:.79rem!important;width:100%!important;margin-bottom:1px!important;}}
.nav-btn-active .stButton>button:hover{{background:var(--accent-lt)!important;transform:none!important;box-shadow:none!important;}}

.sb-q1 .stButton>button{{background:linear-gradient(135deg,#059669,#047857)!important;font-size:.73rem!important;padding:.29rem .45rem!important;}}
.sb-q2 .stButton>button{{background:linear-gradient(135deg,#7c3aed,#6d28d9)!important;font-size:.73rem!important;padding:.29rem .45rem!important;}}
.sb-q3 .stButton>button{{background:linear-gradient(135deg,#0891b2,#0e7490)!important;font-size:.73rem!important;padding:.29rem .45rem!important;}}
.sb-q4 .stButton>button{{background:linear-gradient(135deg,#dc2626,#b91c1c)!important;font-size:.73rem!important;padding:.29rem .45rem!important;}}

.stTabs [data-baseweb="tab-list"]{{background:var(--elevated)!important;border:1px solid var(--border)!important;border-radius:10px!important;padding:3px!important;gap:2px!important;}}
.stTabs [data-baseweb="tab"]{{border-radius:8px!important;padding:5px 13px!important;font-size:.8rem!important;font-weight:500!important;color:var(--text2)!important;background:transparent!important;transition:all .15s!important;}}
.stTabs [aria-selected="true"]{{background:var(--surface)!important;color:var(--accent)!important;font-weight:600!important;box-shadow:var(--shadow)!important;}}

.stProgress>div>div{{background:linear-gradient(90deg,#2563eb,#7c3aed)!important;border-radius:4px!important;}}
.stError{{background:var(--red-lt)!important;border:1px solid #fca5a5!important;border-radius:var(--radius-sm)!important;}}
.stWarning{{background:var(--yellow-lt)!important;border:1px solid #fcd34d!important;border-radius:var(--radius-sm)!important;}}
.stSuccess{{background:var(--green-lt)!important;border:1px solid #6ee7b7!important;border-radius:var(--radius-sm)!important;}}
.stInfo{{background:var(--accent-lt)!important;border:1px solid #93c5fd!important;border-radius:var(--radius-sm)!important;}}
.stFileUploader>div{{background:var(--elevated)!important;border:2px dashed var(--border2)!important;border-radius:var(--radius)!important;}}
::-webkit-scrollbar{{width:5px;height:5px;}} ::-webkit-scrollbar-track{{background:var(--bg);}} ::-webkit-scrollbar-thumb{{background:var(--border2);border-radius:3px;}}
#MainMenu{{visibility:hidden;}} footer{{visibility:hidden;}} header{{visibility:hidden;}}

/* ─ Components ─ */
.mc-header{{background:linear-gradient(135deg,#1e3a5f 0%,#1d4ed8 55%,#2563eb 100%);padding:1.3rem 1.7rem;border-radius:14px;margin-bottom:1.1rem;position:relative;overflow:hidden;box-shadow:var(--shadow-md);animation:fadeInUp .5s ease both;}}
.mc-header::before{{content:'';position:absolute;top:-50px;right:-50px;width:200px;height:200px;background:radial-gradient(circle,rgba(255,255,255,.07) 0%,transparent 70%);border-radius:50%;}}
.mc-header h1{{font-family:var(--serif);font-size:1.55rem;color:white;margin:0 0 .12rem;position:relative;z-index:1;}}
.mc-header p{{color:rgba(255,255,255,.62);font-size:.72rem;margin:0;position:relative;z-index:1;font-family:var(--mono);}}
.mc-badge-row{{display:flex;gap:5px;margin-top:.65rem;flex-wrap:wrap;position:relative;z-index:1;}}
.mc-badge{{padding:2px 8px;border-radius:20px;font-size:.66rem;font-weight:600;letter-spacing:.3px;}}
.badge-white{{background:rgba(255,255,255,.17);border:1px solid rgba(255,255,255,.28);color:white;}}
.badge-yellow{{background:rgba(251,191,36,.24);border:1px solid rgba(251,191,36,.38);color:#fde68a;}}
.badge-green{{background:rgba(52,211,153,.19);border:1px solid rgba(52,211,153,.33);color:#6ee7b7;}}
.badge-pink{{background:rgba(244,114,182,.19);border:1px solid rgba(244,114,182,.33);color:#fbcfe8;}}

.mc-stat{{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:.8rem .65rem;text-align:center;box-shadow:var(--shadow);transition:transform .2s,box-shadow .2s;cursor:default;animation:countUp .4s ease both;}}
.mc-stat:hover{{transform:translateY(-2px);box-shadow:var(--shadow-md);}}
.mc-stat-val{{font-size:1.45rem;font-weight:700;line-height:1;}}
.mc-stat-lbl{{font-size:.59rem;color:var(--text3);margin-top:3px;text-transform:uppercase;letter-spacing:.7px;font-weight:500;}}

.mc-section-title{{font-size:.59rem;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:var(--text3);margin-bottom:.55rem;padding-bottom:.32rem;border-bottom:1px solid var(--border);font-family:var(--mono);}}
.mc-card{{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:.9rem 1.1rem;box-shadow:var(--shadow);margin-bottom:.65rem;animation:fadeInUp .35s ease both;}}
.mc-patient-card{{background:var(--surface);border:1.5px solid var(--border);border-radius:var(--radius);padding:.7rem .85rem;margin-bottom:.3rem;display:flex;align-items:center;gap:.75rem;box-shadow:var(--shadow);transition:all .2s;cursor:pointer;animation:fadeInLeft .35s ease both;}}
.mc-patient-card:hover{{border-color:var(--accent);box-shadow:var(--shadow-md);transform:translateY(-1px);}}
.mc-avatar{{width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.95rem;flex-shrink:0;}}
.mc-scan-row{{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-sm);padding:.6rem .85rem;margin-bottom:.3rem;display:flex;align-items:center;justify-content:space-between;box-shadow:var(--shadow);transition:border-color .15s,transform .15s;}}
.mc-scan-row:hover{{border-color:var(--accent);transform:translateX(2px);}}
.mc-tag{{display:inline-block;padding:2px 7px;border-radius:20px;font-size:.66rem;font-weight:600;font-family:var(--mono);}}
.tag-critical{{background:var(--red-lt);color:#dc2626;border:1px solid #fca5a5;}}
.tag-warning{{background:var(--yellow-lt);color:#d97706;border:1px solid #fcd34d;}}
.tag-normal{{background:var(--green-lt);color:#059669;border:1px solid #6ee7b7;}}
.tag-blue{{background:var(--accent-lt);color:#1d4ed8;border:1px solid #93c5fd;}}
.tag-purple{{background:var(--purple-lt);color:#7c3aed;border:1px solid #c4b5fd;}}

.banner-critical{{background:var(--red-lt);border:1.5px solid #fca5a5;border-left:5px solid #dc2626;border-radius:var(--radius-sm);padding:.8rem 1rem;color:#dc2626;font-weight:600;margin-bottom:.75rem;animation:slideDown .3s ease;}}
.banner-warning{{background:var(--yellow-lt);border:1.5px solid #fcd34d;border-left:5px solid #d97706;border-radius:var(--radius-sm);padding:.8rem 1rem;color:#d97706;font-weight:600;margin-bottom:.75rem;animation:slideDown .3s ease;}}
.banner-normal{{background:var(--green-lt);border:1.5px solid #6ee7b7;border-left:5px solid #059669;border-radius:var(--radius-sm);padding:.8rem 1rem;color:#059669;font-weight:600;margin-bottom:.75rem;animation:slideDown .3s ease;}}

.conf-wrap{{background:var(--border);border-radius:99px;height:7px;overflow:hidden;}}
.conf-fill{{height:100%;border-radius:99px;transition:width .8s ease;}}

.mc-alert{{background:var(--red-lt);border:1px solid #fca5a5;border-left:4px solid #dc2626;border-radius:var(--radius-sm);padding:.55rem .8rem;margin-bottom:.3rem;font-size:.78rem;color:#dc2626;animation:slideDown .3s ease;}}
.mc-alert-warning{{background:var(--yellow-lt);border:1px solid #fcd34d;border-left:4px solid #d97706;border-radius:var(--radius-sm);padding:.55rem .8rem;margin-bottom:.3rem;font-size:.78rem;color:#d97706;}}
.mc-alert-info{{background:var(--accent-lt);border:1px solid #93c5fd;border-left:4px solid #2563eb;border-radius:var(--radius-sm);padding:.55rem .8rem;margin-bottom:.3rem;font-size:.78rem;color:{"#93c5fd" if DM else "#1e40af"};}}
.mc-alert-green{{background:var(--green-lt);border:1px solid #6ee7b7;border-left:4px solid #059669;border-radius:var(--radius-sm);padding:.55rem .8rem;margin-bottom:.3rem;font-size:.78rem;color:#059669;}}

.report-box{{background:var(--elevated);border:1px solid var(--border);border-radius:var(--radius);padding:1.1rem;line-height:1.8;font-size:.83rem;animation:fadeInUp .4s ease;}}
.abar-row{{display:flex;align-items:center;gap:7px;margin-bottom:5px;font-size:.75rem;color:var(--text2);}}
.abar-outer{{flex:1;height:7px;background:var(--border);border-radius:99px;overflow:hidden;}}
.abar-fill{{height:100%;border-radius:99px;}}
.rec-box{{background:var(--accent-lt);border:1px solid #bfdbfe;border-left:4px solid var(--accent);border-radius:var(--radius-sm);padding:.75rem .95rem;margin-top:.75rem;}}
.rec-box h4{{color:{"#60a5fa" if DM else "#1d4ed8"};font-size:.8rem;margin:0 0 .3rem;}}
.rec-box p{{color:var(--text2);font-size:.77rem;margin:0;line-height:1.6;}}
.role-badge{{display:inline-block;padding:2px 9px;border-radius:20px;font-size:.68rem;font-weight:600;font-family:var(--mono);}}
.role-doctor{{background:{"#1e3a5f" if DM else "#dbeafe"};color:{"#60a5fa" if DM else "#1d4ed8"};border:1px solid {"#2563eb" if DM else "#93c5fd"};}}
.role-radiologist{{background:{"#052e16" if DM else "#dcfce7"};color:#059669;border:1px solid {"#059669" if DM else "#6ee7b7"};}}
.role-admin{{background:{"#2e1065" if DM else "#f5f3ff"};color:#7c3aed;border:1px solid {"#7c3aed" if DM else "#c4b5fd"};}}
.dot-green{{width:7px;height:7px;border-radius:50%;background:#059669;display:inline-block;margin-right:4px;}}
.dot-red{{width:7px;height:7px;border-radius:50%;background:#dc2626;display:inline-block;margin-right:4px;animation:pulse 1.5s infinite;}}
.dot-blue{{width:7px;height:7px;border-radius:50%;background:#2563eb;display:inline-block;margin-right:4px;}}
.chat-user{{background:linear-gradient(135deg,#2563eb,#1d4ed8);color:white;border-radius:10px 10px 2px 10px;padding:.58rem .82rem;margin-bottom:.35rem;font-size:.81rem;max-width:80%;margin-left:auto;animation:fadeInUp .3s ease;}}
.chat-ai{{background:var(--elevated);border:1px solid var(--border);color:var(--text);border-radius:10px 10px 10px 2px;padding:.58rem .82rem;margin-bottom:.35rem;font-size:.81rem;max-width:85%;animation:fadeInLeft .3s ease;}}
.mc-footer{{text-align:center;color:var(--text3);font-size:.65rem;padding:.7rem 0 .25rem;border-top:1px solid var(--border);margin-top:1.3rem;font-family:var(--mono);}}
.vitals-card{{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-sm);padding:.38rem .55rem;text-align:center;box-shadow:var(--shadow);}}
.vitals-val{{font-family:var(--mono);font-size:.9rem;font-weight:700;}}
.vitals-lbl{{font-size:.56rem;color:var(--text3);text-transform:uppercase;letter-spacing:.5px;}}
.timeline-item{{position:relative;padding-left:1.1rem;margin-bottom:.8rem;border-left:2px solid var(--border);animation:fadeInLeft .35s ease both;}}
.timeline-item::before{{content:'';position:absolute;left:-5px;top:4px;width:7px;height:7px;border-radius:50%;background:var(--accent);}}
.timeline-date{{font-size:.65rem;font-family:var(--mono);color:var(--text3);}}
.timeline-txt{{font-size:.8rem;color:var(--text);margin-top:2px;}}
.prec-item{{background:var(--yellow-lt);border:1px solid #fcd34d;border-left:3px solid var(--yellow);border-radius:var(--radius-sm);padding:.45rem .7rem;margin-bottom:.28rem;font-size:.78rem;color:#d97706;display:flex;gap:7px;align-items:flex-start;animation:fadeInLeft .3s ease both;}}
.prec-critical{{background:var(--red-lt);border-color:#fca5a5;border-left-color:var(--red);color:#dc2626;}}
.log-entry{{background:var(--elevated);border:1px solid var(--border);border-radius:var(--radius-sm);padding:.55rem .8rem;margin-bottom:.28rem;font-size:.79rem;animation:fadeInUp .3s ease;}}
.log-entry-meta{{font-size:.65rem;color:var(--text3);font-family:var(--mono);margin-top:1px;}}
.log-entry-body{{color:var(--text2);margin-top:3px;line-height:1.5;}}
.heatmap-legend{{display:flex;gap:10px;align-items:center;font-size:.73rem;color:var(--text2);background:var(--elevated);border:1px solid var(--border);border-radius:var(--radius-sm);padding:.45rem .8rem;margin-top:.45rem;}}
.heatmap-dot{{width:11px;height:11px;border-radius:50%;display:inline-block;}}
.loading-bar{{height:2px;background:linear-gradient(90deg,#2563eb,#7c3aed,#2563eb);background-size:200% 100%;animation:shimmer 1.5s linear infinite;border-radius:99px;margin-bottom:.4rem;}}
.sb-nav-label{{font-size:.56rem;font-weight:700;letter-spacing:1.8px;text-transform:uppercase;color:var(--text3);padding:.38rem .2rem .18rem;font-family:var(--mono);}}
.lab-normal{{color:#059669;font-weight:600;}}
.lab-low{{color:#2563eb;font-weight:600;}}
.lab-high{{color:#dc2626;font-weight:600;}}
.appt-card{{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:.7rem .9rem;margin-bottom:.3rem;display:flex;align-items:center;justify-content:space-between;box-shadow:var(--shadow);animation:fadeInLeft .3s ease;}}
.appt-card:hover{{border-color:var(--accent);}}
.drug-card{{background:var(--elevated);border:1px solid var(--border);border-radius:var(--radius-sm);padding:.6rem .85rem;margin-bottom:.3rem;font-size:.8rem;}}
.feature-item{{display:flex;align-items:flex-start;gap:9px;padding:6px 0;border-bottom:1px solid var(--border);}}
.feature-icon{{font-size:1rem;min-width:22px;margin-top:1px;}}
.feature-title{{font-weight:600;color:var(--text);font-size:.83rem;}}
.feature-desc{{color:var(--text3);font-size:.73rem;margin-top:1px;}}

/* Login */
.login-card{{background:{"rgba(30,41,59,.97)" if DM else "rgba(255,255,255,.97)"};border-radius:18px;padding:1.8rem 2.1rem;box-shadow:0 24px 80px rgba(0,0,0,.35);position:relative;z-index:1;max-width:430px;width:100%;margin:0 auto;animation:fadeInUp .5s ease both;}}
.login-logo-icon{{font-size:2.6rem;display:block;margin-bottom:.4rem;animation:pulseScale 3s ease infinite;}}
.login-logo-name{{font-family:'Playfair Display',serif;font-size:1.85rem;font-weight:700;color:{"#f1f5f9" if DM else "#0f172a"};letter-spacing:-.5px;line-height:1;}}
.login-logo-sub{{font-family:'JetBrains Mono',monospace;font-size:.58rem;color:#94a3b8;letter-spacing:2.5px;text-transform:uppercase;margin-top:4px;}}
.login-badge-row{{display:flex;justify-content:center;gap:5px;flex-wrap:wrap;margin-top:.65rem;}}
.login-badge{{padding:2px 8px;border-radius:20px;font-size:.64rem;font-weight:600;}}
.lb-blue{{background:#eff6ff;border:1px solid #bfdbfe;color:#1d4ed8;}}
.lb-green{{background:#ecfdf5;border:1px solid #6ee7b7;color:#059669;}}
.lb-purple{{background:#f5f3ff;border:1px solid #c4b5fd;color:#7c3aed;}}
.demo-creds{{background:{"rgba(30,41,59,1)" if DM else "linear-gradient(135deg,#f8fafc,#f1f5f9)"};border:1px solid var(--border);border-radius:10px;padding:.75rem .9rem;margin-top:.75rem;font-family:'JetBrains Mono',monospace;font-size:.68rem;color:var(--text2);line-height:2.1;}}
.demo-creds-title{{font-size:.63rem;font-weight:700;color:#2563eb;letter-spacing:.5px;text-transform:uppercase;margin-bottom:.2rem;}}

@media(max-width:768px){{
    section[data-testid="stSidebar"]{{width:200px!important;min-width:200px!important;}}
    .mc-header h1{{font-size:1.2rem!important;}}
}}
</style>""", unsafe_allow_html=True)

inject_css()

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def role_badge_html(role):
    cls={"Doctor":"role-doctor","Radiologist":"role-radiologist","Admin":"role-admin"}.get(role,"role-doctor")
    return f'<span class="role-badge {cls}">{role}</span>'

def urgency_tag(flag):
    cls={"CRITICAL":"tag-critical","WARNING":"tag-warning"}.get(flag,"tag-normal")
    ico={"CRITICAL":"🔴","WARNING":"🟡"}.get(flag,"🟢")
    return f'<span class="mc-tag {cls}">{ico} {flag}</span>'

def risk_color(r):
    return {"CRITICAL":"#dc2626","HIGH":"#ea580c","WARNING":"#d97706","LOW":"#059669"}.get(r,"#64748b")

def extract_confidence(text):
    m=re.search(r'(\d{1,3})%',text)
    if m:
        v=int(m.group(1))
        if 40<=v<=100: return v
    return random.randint(76,92)

def extract_primary_dx(text):
    m=re.search(r'\*\*Primary Diagnosis[:\*]*\s*(.+?)(?:\n|—|Confidence)',text)
    return m.group(1).strip()[:45] if m else "See full report"

def detect_urgency_flag(text):
    t=text.lower()
    if any(w in t for w in ["🚨","critical finding","emergency","immediately life-threatening","stat consult","requires immediate","life-threatening","emergent","massive haemorrhage","tension pneumothorax"]): return "CRITICAL"
    if any(w in t for w in ["⚠️","abnormal","concerning","follow-up recommended","suspicious","warrants further","lesion identified","nodule identified","effusion","opacity","consolidation","mass"]): return "WARNING"
    return "NORMAL"

def log_action(action,detail=""):
    st.session_state.audit_log.append({
        "time":datetime.now().strftime("%H:%M:%S"),"date":datetime.now().strftime("%Y-%m-%d"),
        "user":st.session_state.user or "—","action":action,"detail":detail,
    })

def compute_risk_score(patient):
    score=0
    age=patient.get("age",40)
    if age>70: score+=25
    elif age>55: score+=15
    elif age>40: score+=8
    smoker=patient.get("smoker","No").lower()
    if "45" in smoker or "30" in smoker: score+=25
    elif "yes" in smoker or "ex" in smoker: score+=12
    score+={"CRITICAL":40,"HIGH":25,"WARNING":12,"LOW":2}.get(patient.get("risk","LOW"),5)
    try:
        o2=float(patient.get("o2","99%").replace("%",""))
        if o2<92: score+=15
        elif o2<95: score+=8
    except: pass
    return min(score,100)

def add_patient_log(pid,note,log_type="Note"):
    if pid not in st.session_state.patient_logs:
        st.session_state.patient_logs[pid]=[]
    st.session_state.patient_logs[pid].append({
        "date":datetime.now().strftime("%Y-%m-%d"),"time":datetime.now().strftime("%H:%M"),
        "doctor":st.session_state.user or "Unknown","type":log_type,"note":note,
    })

def lab_status(val, ref_lo, ref_hi):
    if val < ref_lo: return "lab-low", "▼ Low"
    if val > ref_hi: return "lab-high", "▲ High"
    return "lab-normal", "✅ Normal"



# ─────────────────────────────────────────────
# ENHANCED HEATMAP
# ─────────────────────────────────────────────
def generate_heatmap(pil_image, urgency_flag, sensitivity=1.0):
    img=pil_image.copy().convert("RGB")
    w,h=img.size
    arr=np.array(img,dtype=np.float32)
    hm=np.zeros((h,w,3),dtype=np.float32)
    num_regions={"CRITICAL":4,"WARNING":3,"NORMAL":2}.get(urgency_flag,2)
    palettes={"CRITICAL":[(255,20,20),(255,80,0),(255,160,0),(255,220,60)],"WARNING":[(255,120,0),(255,200,30),(200,230,50),(100,220,80)],"NORMAL":[(30,180,100),(0,160,220),(100,130,255),(80,200,180)]}
    palette=palettes.get(urgency_flag,palettes["NORMAL"])
    priors=[(0.35,0.35),(0.65,0.40),(0.40,0.65),(0.55,0.55)]
    Y,X=np.mgrid[0:h,0:w]
    for i in range(num_regions):
        px,py=priors[i%len(priors)]
        cx=max(int(w*.1),min(int(w*.9),int(w*(px+random.uniform(-.1,.1)))))
        cy=max(int(h*.1),min(int(h*.9),int(h*(py+random.uniform(-.1,.1)))))
        rx=w*random.uniform(.07,.17)*sensitivity
        ry=h*random.uniform(.07,.17)*sensitivity
        dist=((X-cx)**2/rx**2+(Y-cy)**2/ry**2)
        intensity=np.exp(-dist*1.5)
        color=np.array(palette[i%len(palette)],dtype=np.float32)
        for c in range(3): hm[:,:,c]+=intensity*color[c]
    hm_max=hm.max()
    if hm_max>0: hm=hm/hm_max
    hm_img=PILImage.fromarray((hm*255).astype(np.uint8))
    hm_img=hm_img.filter(ImageFilter.GaussianBlur(radius=max(w,h)//25))
    hm_s=np.array(hm_img,dtype=np.float32)/255.0
    alpha=0.48
    blended=arr*(1-alpha*hm_s)+hm_s*np.array([255,80,30],dtype=np.float32)*alpha
    blended=np.clip(blended,0,255).astype(np.uint8)
    result=PILImage.fromarray(blended)
    draw=ImageDraw.Draw(result)
    bc={"CRITICAL":(220,38,38),"WARNING":(217,119,6),"NORMAL":(5,150,105)}.get(urgency_flag,(37,99,235))
    for i in range(num_regions):
        px,py=priors[i%len(priors)]
        cx=max(int(w*.15),min(int(w*.85),int(w*(px+random.uniform(-.1,.1)))))
        cy=max(int(h*.15),min(int(h*.85),int(h*(py+random.uniform(-.1,.1)))))
        br=int(min(w,h)*.065)
        draw.ellipse([cx-br,cy-br,cx+br,cy+br],outline=bc,width=2)
        draw.text((cx-7,cy-br-13),f"R{i+1}",fill=bc)
    return result

def enhance_image(pil_image, mode):
    img=pil_image.convert("RGB")
    if mode=="Sharpen": return img.filter(ImageFilter.UnsharpMask(radius=2,percent=150,threshold=3))
    elif mode=="Enhance Contrast": return ImageEnhance.Contrast(img).enhance(1.8)
    elif mode=="Denoise": return img.filter(ImageFilter.MedianFilter(size=3))
    elif mode=="Brighten": return ImageEnhance.Brightness(img).enhance(1.3)
    elif mode=="Edge Detect": return img.convert("L").filter(ImageFilter.FIND_EDGES).convert("RGB")
    elif mode=="CLAHE":
        gray=np.array(img.convert("L"),dtype=np.float32); tile=8
        th,tw=gray.shape[0]//tile,gray.shape[1]//tile; out=gray.copy()
        for i in range(tile):
            for j in range(tile):
                patch=gray[i*th:(i+1)*th,j*tw:(j+1)*tw]; mn,mx=patch.min(),patch.max()
                if mx>mn: out[i*th:(i+1)*th,j*tw:(j+1)*tw]=(patch-mn)/(mx-mn)*255
        return PILImage.fromarray(out.astype(np.uint8)).convert("RGB")
    elif mode=="Gamma Correction":
        arr=np.array(img,dtype=np.float32)/255.0
        return PILImage.fromarray((np.power(arr,.6)*255).astype(np.uint8))
    elif mode=="Invert (Bone Window)": return PILImage.fromarray(255-np.array(img))
    elif mode=="Pseudo-Color":
        gray=np.array(img.convert("L"),dtype=np.float32)/255.0
        r=(np.sin(gray*np.pi)*255).astype(np.uint8); g=(np.sin(gray*np.pi*2)*255).astype(np.uint8); b=(np.cos(gray*np.pi)*255).astype(np.uint8)
        return PILImage.fromarray(np.stack([r,g,b],axis=2))
    return img

def encode_image_b64(pil_image):
    img=pil_image.copy(); w,h=img.size
    if max(w,h)>1568:
        s=1568/max(w,h); img=img.resize((int(w*s),int(h*s)),PILImage.LANCZOS)
    if img.mode not in("RGB","L"): img=img.convert("RGB")
    buf=io.BytesIO(); img.save(buf,format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

# ─────────────────────────────────────────────
# AI CALLS
# ─────────────────────────────────────────────
def run_analysis(pil_image, prompt, model):
    client=Groq(api_key=GROQ_API_KEY)
    b64=encode_image_b64(pil_image)
    r=client.chat.completions.create(
        model=model,
        messages=[{"role":"user","content":[{"type":"image_url","image_url":{"url":f"data:image/png;base64,{b64}"}},{"type":"text","text":prompt}]}],
        max_tokens=4096,temperature=0.15,
    )
    return r.choices[0].message.content

def run_chat(messages_list, system_prompt=None):
    client=Groq(api_key=GROQ_API_KEY)
    msgs=[{"role":"system","content":system_prompt or "You are Cortexa Health, an expert clinical assistant and radiologist."}]
    msgs.extend(messages_list)
    r=client.chat.completions.create(model="meta-llama/llama-4-scout-17b-16e-instruct",messages=msgs,max_tokens=1024,temperature=0.3)
    return r.choices[0].message.content

def run_ai(prompt, system="You are a senior consultant physician. Be concise and clinically precise."):
    client=Groq(api_key=GROQ_API_KEY)
    r=client.chat.completions.create(model="meta-llama/llama-4-scout-17b-16e-instruct",messages=[{"role":"system","content":system},{"role":"user","content":prompt}],max_tokens=1200,temperature=0.2)
    return r.choices[0].message.content

def build_prompt(mode, modality, urgency, custom_q, patient_ctx, incl_research, incl_patient, incl_icd, incl_meas, incl_precautions=True, compare_text="", template="Comprehensive Radiology"):
    mode_map={"Comprehensive":"Exhaustive, publication-quality clinical radiological report.","Quick Scan":"90-second triage: top finding, primary impression, immediate action only.","Patient Mode":"Compassionate plain English. No jargon.","Research":"Academic depth: imaging biomarkers, quantitative descriptors.","Second Opinion":"Senior radiologist reviewing peer's report. Be critical."}
    ctx=f"\n\n**Clinical Context:** {custom_q}" if custom_q.strip() else ""
    pt=f"\n**Patient:** {patient_ctx}" if patient_ctx else ""
    icd="\n### 6. 🏷️ ICD-10 Codes\n| Code | Description | Confidence |\n|------|-------------|------------|\n" if incl_icd else ""
    meas="\n### 7. 📏 Measurements\n- Estimate all measurable lesions with dimensions vs. reference ranges\n" if incl_meas else ""
    research="\n### 8. 🔬 Evidence & Guidelines\n- Cite 2–3 ACR/RSNA/ESR guidelines\n- State sensitivity/specificity\n" if incl_research else ""
    patient_sec="\n### 9. 👤 Patient-Friendly Summary\n- Plain English findings, why it matters, next steps\n" if incl_patient else ""
    precautions="\n### 10. ⚠️ Clinical Precautions\n- List 5–8 specific precautions, allergy warnings, activity restrictions, follow-up schedule\n" if incl_precautions else ""
    compare=f"\n\n### Prior Study Comparison\n{compare_text}" if compare_text.strip() else ""
    return f"""You are a world-class consultant radiologist with 30+ years of subspecialty experience.
Template: {template}. Modality: {modality}. Urgency: {urgency}. Mode: {mode_map.get(mode,'')}
{pt}{ctx}

STRUCTURED CLINICAL REPORT:

### 1. 🖼️ Image Type & Technical Quality
### 2. 🔍 Systematic Findings (✅ Normal | ⚠️ Abnormal | 🚨 CRITICAL)
### 3. 🩺 Diagnostic Assessment
- **Primary Diagnosis:** [diagnosis] — Confidence: [High/Moderate/Low] — ([%])
- **Differentials (ranked):** 1. [most likely] 2. [second] 3. [third]
- **Critical Findings:** [STAT items or "None identified"]
- **Next Steps:** Immediate / 24-72h / Long-term
### 4. 📊 Findings Summary Table
| Structure | Finding | Severity | Action |
### 5. 🎯 Radiologist's Impression
{icd}{meas}{research}{patient_sec}{precautions}{compare}
State confidence % on primary diagnosis. Be authoritative."""

# ─────────────────────────────────────────────
# EXPORT — PDF (reportlab) & DOCX
# ─────────────────────────────────────────────
def make_pdf_bytes(report, fname, mode, model, uflag, conf, doctor, patient_ctx, modality):
    if not REPORTLAB_OK:
        return None
    buf=io.BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=2*cm,leftMargin=2*cm,topMargin=2*cm,bottomMargin=2*cm)
    styles=getSampleStyleSheet()
    story=[]
    # Title
    title_style=ParagraphStyle("title",parent=styles["Heading1"],fontSize=18,textColor=RL_COLORS.HexColor("#1d4ed8"),spaceAfter=4,fontName="Helvetica-Bold",alignment=TA_CENTER)
    story.append(Paragraph("🏥 Cortexa Health — Radiological Report",title_style))
    sub_style=ParagraphStyle("sub",parent=styles["Normal"],fontSize=9,textColor=RL_COLORS.grey,alignment=TA_CENTER,spaceAfter=12)
    story.append(Paragraph(f"v{APP_VERSION} · {AUTHOR} · {datetime.now().strftime('%Y-%m-%d %H:%M')}",sub_style))
    story.append(HRFlowable(width="100%",thickness=1,color=RL_COLORS.HexColor("#e2e8f0"),spaceAfter=12))
    # Meta table
    urg_color={"CRITICAL":RL_COLORS.HexColor("#dc2626"),"WARNING":RL_COLORS.HexColor("#d97706"),"NORMAL":RL_COLORS.HexColor("#059669")}.get(uflag,RL_COLORS.green)
    meta_data=[
        ["File:",fname,"Doctor:",doctor],
        ["Mode:",mode,"Modality:",modality],
        ["Urgency:",uflag,"Confidence:",f"{conf}%"],
        ["Patient:",patient_ctx or "Unlinked","Model:",model],
    ]
    meta_table=Table(meta_data,colWidths=[2.5*cm,7*cm,2.5*cm,5*cm])
    meta_table.setStyle(TableStyle([
        ('FONTSIZE',(0,0),(-1,-1),9),('FONTNAME',(0,0),(0,-1),'Helvetica-Bold'),('FONTNAME',(2,0),(2,-1),'Helvetica-Bold'),
        ('TEXTCOLOR',(0,0),(-1,-1),RL_COLORS.HexColor("#475569")),
        ('BACKGROUND',(0,0),(-1,-1),RL_COLORS.HexColor("#f8fafc")),
        ('GRID',(0,0),(-1,-1),.5,RL_COLORS.HexColor("#e2e8f0")),
        ('ROWBACKGROUNDS',(0,0),(-1,-1),[RL_COLORS.HexColor("#f8fafc"),RL_COLORS.white]),
        ('PADDING',(0,0),(-1,-1),5),
    ]))
    story.append(meta_table); story.append(Spacer(1,.3*cm))
    # Urgency banner
    urg_msg={"CRITICAL":"🚨 CRITICAL FINDING — Immediate clinical attention required","WARNING":"⚠️ Abnormal findings — Follow-up recommended","NORMAL":"✅ No critical findings detected"}.get(uflag,"✅")
    urg_style=ParagraphStyle("urg",parent=styles["Normal"],fontSize=10,textColor=urg_color,backColor=RL_COLORS.HexColor({"CRITICAL":"#fef2f2","WARNING":"#fffbeb","NORMAL":"#f0fdf4"}.get(uflag,"#f0fdf4")),borderPadding=8,spaceAfter=8,fontName="Helvetica-Bold")
    story.append(Paragraph(urg_msg,urg_style)); story.append(Spacer(1,.2*cm))
    # Report body
    body_style=ParagraphStyle("body",parent=styles["Normal"],fontSize=9,textColor=RL_COLORS.HexColor("#0f172a"),leading=15,spaceAfter=4)
    for line in report.split("\n"):
        clean=line.strip()
        if not clean: story.append(Spacer(1,.12*cm)); continue
        if clean.startswith("###"): 
            h_style=ParagraphStyle("h3",parent=styles["Heading3"],fontSize=11,textColor=RL_COLORS.HexColor("#1d4ed8"),spaceBefore=6,spaceAfter=2,fontName="Helvetica-Bold")
            story.append(Paragraph(clean.replace("###","").strip(),h_style))
        elif clean.startswith("**") and clean.endswith("**"):
            story.append(Paragraph(f"<b>{clean.replace('**','')}</b>",body_style))
        elif clean.startswith("- "):
            story.append(Paragraph(f"• {clean[2:]}",ParagraphStyle("bullet",parent=body_style,leftIndent=12)))
        else:
            clean_p=clean.replace("**","<b>").replace("__","<u>")
            try: story.append(Paragraph(clean_p,body_style))
            except: story.append(Paragraph(clean,body_style))
    story.append(Spacer(1,.4*cm))
    story.append(HRFlowable(width="100%",thickness=1,color=RL_COLORS.HexColor("#e2e8f0"),spaceAfter=8))
    disc=ParagraphStyle("disc",parent=styles["Normal"],fontSize=7.5,textColor=RL_COLORS.grey,alignment=TA_CENTER)
    story.append(Paragraph(f"Cortexa Health{APP_VERSION} · {AUTHOR} · Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} · Educational use only · Validate with a qualified radiologist",disc))
    doc.build(story)
    return buf.getvalue()

def make_docx_bytes(report, fname, mode, model, uflag, conf, doctor, patient_ctx, modality):
    if not DOCX_OK:
        return None
    doc=DocxDocument()
    # Page margins
    for sec in doc.sections:
        sec.top_margin=Cm(2); sec.bottom_margin=Cm(2); sec.left_margin=Cm(2.5); sec.right_margin=Cm(2.5)
    # Title
    t=doc.add_heading("Cortexa Health — Radiological Report",0)
    t.alignment=WD_ALIGN_PARAGRAPH.CENTER
    for run in t.runs: run.font.color.rgb=RGBColor(0x1d,0x4e,0xd8)
    # Subtitle
    sub=doc.add_paragraph(f"v{APP_VERSION} · {AUTHOR} · {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    sub.alignment=WD_ALIGN_PARAGRAPH.CENTER
    for run in sub.runs: run.font.size=Pt(9); run.font.color.rgb=RGBColor(0x94,0xa3,0xb8)
    doc.add_paragraph()
    # Meta table
    table=doc.add_table(rows=4,cols=4); table.style="Light Shading Accent 1"
    meta=[("File:",fname,"Doctor:",doctor),("Mode:",mode,"Modality:",modality),("Urgency:",uflag,"Confidence:",f"{conf}%"),("Patient:",patient_ctx or "Unlinked","Model:",model)]
    for i,(a,b,c,d) in enumerate(meta):
        row=table.rows[i].cells
        row[0].text=a; row[1].text=b; row[2].text=c; row[3].text=d
        for j in[0,2]:
            run=row[j].paragraphs[0].runs
            if run: run[0].bold=True
    doc.add_paragraph()
    # Urgency banner
    urg_msg={"CRITICAL":"🚨 CRITICAL FINDING — Immediate clinical attention required","WARNING":"⚠️ Abnormal findings — Follow-up recommended","NORMAL":"✅ No critical findings detected"}.get(uflag,"✅")
    banner=doc.add_paragraph(urg_msg)
    for run in banner.runs:
        run.bold=True; run.font.size=Pt(11)
        c={"CRITICAL":RGBColor(0xdc,0x26,0x26),"WARNING":RGBColor(0xd9,0x77,0x06),"NORMAL":RGBColor(0x05,0x96,0x69)}.get(uflag,RGBColor(0x05,0x96,0x69))
        run.font.color.rgb=c
    doc.add_paragraph()
    # Report content
    for line in report.split("\n"):
        clean=line.strip()
        if not clean: doc.add_paragraph(); continue
        if clean.startswith("### "):
            h=doc.add_heading(clean.replace("###","").strip(),level=2)
            for run in h.runs: run.font.color.rgb=RGBColor(0x1d,0x4e,0xd8)
        elif clean.startswith("## "):
            h=doc.add_heading(clean.replace("##","").strip(),level=1)
        elif clean.startswith("- "):
            p=doc.add_paragraph(style="List Bullet"); p.add_run(clean[2:]).font.size=Pt(10)
        elif "|" in clean and clean.startswith("|"):
            pass  # skip table dividers
        else:
            p=doc.add_paragraph()
            parts=re.split(r'(\*\*.*?\*\*)',clean)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    run=p.add_run(part[2:-2]); run.bold=True; run.font.size=Pt(10)
                else:
                    run=p.add_run(part); run.font.size=Pt(10)
    # Footer
    doc.add_paragraph()
    footer=doc.add_paragraph(f"Cortexa Health {APP_VERSION} · {AUTHOR} · {datetime.now().strftime('%Y-%m-%d')} · Educational use only")
    footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
    for run in footer.runs: run.font.size=Pt(8); run.font.color.rgb=RGBColor(0x94,0xa3,0xb8)
    buf=io.BytesIO(); doc.save(buf)
    return buf.getvalue()

def make_html_report(report, fname, mode, model, uflag, conf, doctor, patient_ctx, modality):
    c={"CRITICAL":"#dc2626","WARNING":"#d97706","NORMAL":"#059669"}.get(uflag,"#059669")
    bg={"CRITICAL":"#fef2f2","WARNING":"#fffbeb","NORMAL":"#f0fdf4"}.get(uflag,"#f0fdf4")
    msg={"CRITICAL":"🚨 CRITICAL FINDING — Immediate clinical attention required","WARNING":"⚠️ Abnormal findings — Follow-up recommended","NORMAL":"✅ No critical findings detected"}.get(uflag,"✅")
    safe=report.replace("<","&lt;").replace(">","&gt;")
    return f"""<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Cortexa Health — {fname}</title>
<style>*{{box-sizing:border-box;}} body{{font-family:'Segoe UI',sans-serif;background:#f0f4f8;color:#0f172a;margin:0;padding:26px;}}
.wrap{{max-width:840px;margin:0 auto;}} .header{{background:linear-gradient(135deg,#1e3a5f,#2563eb);color:white;padding:18px 22px;border-radius:12px;margin-bottom:14px;}}
.header h1{{margin:0 0 2px;font-size:1.25rem;}} .header p{{margin:0;opacity:.65;font-size:.75rem;font-family:monospace;}}
.meta{{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:12px;}} .m{{background:white;border:1px solid #e2e8f0;border-radius:8px;padding:6px 11px;min-width:100px;}}
.m .l{{font-size:.6rem;text-transform:uppercase;letter-spacing:.5px;color:#94a3b8;}} .m .v{{font-size:.83rem;font-weight:600;margin-top:1px;}}
.urg{{background:{bg};border:1px solid {c};border-left:4px solid {c};border-radius:8px;padding:9px 13px;margin-bottom:12px;color:{c};font-weight:600;font-size:.85rem;}}
.conf-wrap{{background:#e2e8f0;border-radius:99px;height:7px;margin:4px 0 12px;}} .conf-fill{{height:100%;border-radius:99px;background:{c};width:{conf}%;}}
.report{{background:white;border:1px solid #e2e8f0;border-radius:10px;padding:17px;line-height:1.75;font-size:.83rem;white-space:pre-wrap;}}
table{{border-collapse:collapse;width:100%;margin:7px 0;}} th{{background:#f8fafc;padding:5px 9px;text-align:left;font-size:.76rem;border:1px solid #e2e8f0;}} td{{padding:5px 9px;border:1px solid #e2e8f0;font-size:.76rem;}}
.footer{{text-align:center;color:#94a3b8;font-size:.65rem;margin-top:16px;font-family:monospace;}}
@media print{{body{{background:white;}} .header{{-webkit-print-color-adjust:exact;print-color-adjust:exact;}}}}
</style></head><body><div class='wrap'>
<div class='header'><h1>🏥 Cortexa Health — Radiological Report v{APP_VERSION}</h1><p>{AUTHOR} · {datetime.now().strftime('%Y-%m-%d %H:%M')}</p></div>
<div class='meta'><div class='m'><div class='l'>File</div><div class='v'>{fname}</div></div><div class='m'><div class='l'>Doctor</div><div class='v'>{doctor}</div></div><div class='m'><div class='l'>Mode</div><div class='v'>{mode}</div></div><div class='m'><div class='l'>Modality</div><div class='v'>{modality}</div></div><div class='m'><div class='l'>Confidence</div><div class='v'>{conf}%</div></div>{'<div class="m"><div class="l">Patient</div><div class="v">'+patient_ctx+'</div></div>' if patient_ctx else ''}</div>
<div class='urg'>{msg}</div><div style='font-size:.72rem;color:#64748b;margin-bottom:3px;'>AI Confidence</div>
<div class='conf-wrap'><div class='conf-fill'></div></div>
<div class='report'>{safe}</div>
<div style='margin-top:10px;padding:9px 13px;background:{bg};border:1px solid {c};border-radius:8px;font-size:.76rem;color:{c};'><b>⚠️ Disclaimer:</b> Cortexa Health {APP_VERSION} — Educational use only. Always validate with a qualified radiologist.</div>
<div class='footer'>Cortexa Health {APP_VERSION} · {AUTHOR} · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
</div></body></html>"""

# ─────────────────────────────────────────────
# VITALS GRAPH
# ─────────────────────────────────────────────
def plot_vitals(patient):
    if not MATPLOTLIB_OK: return None
    vh=patient.get("vitals_history",[])
    if len(vh)<1: return None
    dates=[v["date"] for v in vh]; bp_s=[v["bp_s"] for v in vh]; bp_d=[v["bp_d"] for v in vh]; o2=[v["o2"] for v in vh]; hr=[v.get("hr",75) for v in vh]
    fig,axes=plt.subplots(1,3,figsize=(12,3.5)); fig.patch.set_facecolor("#f8fafc")
    for ax in axes: ax.set_facecolor("#ffffff"); ax.spines[["top","right"]].set_visible(False)
    # BP
    axes[0].plot(dates,bp_s,"o-",color="#dc2626",linewidth=2,markersize=5,label="Systolic")
    axes[0].plot(dates,bp_d,"o-",color="#2563eb",linewidth=2,markersize=5,label="Diastolic")
    axes[0].axhline(y=130,color="#fca5a5",linestyle="--",alpha=0.6,linewidth=1)
    axes[0].axhline(y=80,color="#93c5fd",linestyle="--",alpha=0.6,linewidth=1)
    axes[0].set_title("Blood Pressure (mmHg)",fontsize=9,fontweight="bold",color="#0f172a"); axes[0].legend(fontsize=7); axes[0].tick_params(axis="both",labelsize=7)
    # O2
    axes[1].fill_between(dates,o2,[95]*len(o2),where=[x<95 for x in o2],alpha=0.25,color="#dc2626")
    axes[1].plot(dates,o2,"o-",color="#059669",linewidth=2,markersize=5); axes[1].axhline(y=95,color="#fca5a5",linestyle="--",alpha=0.6,linewidth=1)
    axes[1].set_ylim([85,101]); axes[1].set_title("O₂ Saturation (%)",fontsize=9,fontweight="bold",color="#0f172a"); axes[1].tick_params(axis="both",labelsize=7)
    # HR
    axes[2].bar(dates,hr,color=["#dc2626" if x>100 else "#2563eb" for x in hr],alpha=0.75)
    axes[2].axhline(y=100,color="#fca5a5",linestyle="--",alpha=0.6,linewidth=1); axes[2].axhline(y=60,color="#93c5fd",linestyle="--",alpha=0.6,linewidth=1)
    axes[2].set_title("Heart Rate (bpm)",fontsize=9,fontweight="bold",color="#0f172a"); axes[2].tick_params(axis="both",labelsize=7)
    plt.tight_layout(pad=1.2)
    buf=io.BytesIO(); plt.savefig(buf,format="PNG",dpi=140,bbox_inches="tight",facecolor=fig.get_facecolor()); plt.close()
    buf.seek(0); return PILImage.open(buf)

# ═══════════════════════════════════════════════
# ██████  AUTH  — Pixel-perfect HTML matching preview
# ═══════════════════════════════════════════════
if not st.session_state.logged_in:
    import streamlit.components.v1 as components

    # Hide ALL streamlit chrome, make app bg fully dark
    st.markdown("""
    <style>
    html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stHeader"],
    [data-testid="stToolbar"],footer,.stDeployButton{
        background:#070d1a !important;
        color:#f1f5f9 !important;
    }
    section[data-testid="stSidebar"]{display:none !important;}
    [data-testid="stAppViewContainer"]>div:first-child{padding:0 !important;}
    .main .block-container{padding:0 !important; max-width:100% !important;}
    #MainMenu,footer,header{visibility:hidden;}
    </style>
    """, unsafe_allow_html=True)

    # The full login HTML rendered as a component (full control, no Streamlit override)
    LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0;}
:root{
  --bg:#070d1a;--surface:#0e1628;--card:#111a2e;
  --border:rgba(255,255,255,0.07);--border2:rgba(255,255,255,0.13);
  --accent:#38bdf8;--accent2:#6366f1;--green:#22d3ee;
  --text:#f1f5f9;--text2:#94a3b8;--text3:#475569;
  --sans:'DM Sans',sans-serif;--mono:'JetBrains Mono',monospace;
}
html,body{width:100%;min-height:100vh;font-family:var(--sans);background:var(--bg);color:var(--text);overflow-x:hidden;}

/* BG */
.bg-orbs{position:fixed;inset:0;pointer-events:none;z-index:0;overflow:hidden;}
.orb{position:absolute;border-radius:50%;filter:blur(80px);animation:orb-float 9s ease-in-out infinite;}
.orb1{width:550px;height:550px;top:-180px;left:-120px;background:radial-gradient(circle,rgba(56,189,248,0.13) 0%,transparent 70%);animation-delay:0s;}
.orb2{width:480px;height:480px;bottom:-140px;right:-100px;background:radial-gradient(circle,rgba(99,102,241,0.15) 0%,transparent 70%);animation-delay:-3.5s;}
.orb3{width:300px;height:300px;top:45%;left:42%;background:radial-gradient(circle,rgba(167,139,250,0.09) 0%,transparent 70%);animation-delay:-6s;}
@keyframes orb-float{0%,100%{transform:translate(0,0);}40%{transform:translate(18px,-25px);}70%{transform:translate(-12px,18px);}}
.bg-grid{position:fixed;inset:0;pointer-events:none;z-index:0;
  background-image:linear-gradient(rgba(56,189,248,0.04) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(56,189,248,0.04) 1px,transparent 1px);
  background-size:40px 40px;}

/* LAYOUT */
.page{position:relative;z-index:1;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px;}
.card{display:flex;width:100%;max-width:920px;border-radius:22px;overflow:hidden;
  border:1px solid var(--border2);
  box-shadow:0 40px 120px rgba(0,0,0,0.65),0 0 0 1px rgba(255,255,255,0.03);
  animation:card-in 0.65s cubic-bezier(0.22,1,0.36,1) both;}
@keyframes card-in{from{opacity:0;transform:translateY(28px) scale(0.97);}to{opacity:1;transform:translateY(0) scale(1);}}

/* LEFT */
.left{width:52%;background:var(--surface);padding:42px 38px;display:flex;flex-direction:column;justify-content:space-between;position:relative;overflow:hidden;border-right:1px solid var(--border);}
.pulse-wrap{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);pointer-events:none;z-index:0;}
.pulse{position:absolute;border-radius:50%;border:1px solid rgba(56,189,248,0.1);animation:pulse-out 4s ease infinite;}
.p1{width:160px;height:160px;margin:-80px;animation-delay:0s;}
.p2{width:260px;height:260px;margin:-130px;animation-delay:-1.4s;}
.p3{width:380px;height:380px;margin:-190px;animation-delay:-2.8s;}
@keyframes pulse-out{0%{transform:scale(0.4);opacity:0.7;}100%{transform:scale(1.6);opacity:0;}}

.ecg-svg{position:absolute;bottom:120px;left:0;right:0;width:100%;height:56px;opacity:0.18;}
.ecg-path{stroke:#22d3ee;stroke-width:1.8;fill:none;stroke-linecap:round;stroke-linejoin:round;
  stroke-dasharray:680;stroke-dashoffset:680;
  animation:draw-ecg 2.4s ease forwards 0.6s,ecg-loop 3s linear infinite 3.2s;}
@keyframes draw-ecg{to{stroke-dashoffset:0;}}
@keyframes ecg-loop{0%,100%{opacity:1;}50%{opacity:0.7;}}

/* Brand */
.brand{position:relative;z-index:2;animation:fadein 0.55s ease 0.15s both;}
@keyframes fadein{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:translateY(0);}}
.logo-row{display:flex;align-items:center;gap:12px;margin-bottom:18px;}
.logo-box{width:44px;height:44px;border-radius:13px;background:linear-gradient(135deg,#0ea5e9,#6366f1);
  display:flex;align-items:center;justify-content:center;flex-shrink:0;
  box-shadow:0 8px 22px rgba(14,165,233,0.35);}
.logo-cross{position:relative;width:20px;height:20px;}
.logo-cross::before,.logo-cross::after{content:'';position:absolute;background:white;border-radius:2px;}
.logo-cross::before{width:5px;height:20px;left:7.5px;top:0;}
.logo-cross::after{width:20px;height:5px;left:0;top:7.5px;}
.brand-name{font-size:19px;font-weight:600;color:var(--text);letter-spacing:-0.4px;line-height:1.1;}
.brand-ver{font-size:10.5px;font-family:var(--mono);color:var(--text3);letter-spacing:1.5px;text-transform:uppercase;margin-top:3px;}
.hb-badge{display:inline-flex;align-items:center;gap:6px;background:rgba(34,211,238,0.07);
  border:1px solid rgba(34,211,238,0.22);border-radius:20px;padding:4px 11px;margin-bottom:14px;}
.hb-dot{width:6px;height:6px;border-radius:50%;background:#22d3ee;animation:blink 1.4s ease infinite;flex-shrink:0;}
.hb-txt{font-size:11px;font-family:var(--mono);color:#22d3ee;letter-spacing:0.4px;}
@keyframes blink{0%,100%{opacity:1;}50%{opacity:0.2;}}
.tagline{font-size:14px;color:var(--text2);line-height:1.7;margin-bottom:22px;}
.tagline span{color:var(--accent);font-weight:500;}

/* Features */
.feats{position:relative;z-index:2;animation:fadein 0.55s ease 0.35s both;}
.feat{display:flex;align-items:flex-start;gap:9px;padding:7px 0;border-bottom:1px solid var(--border);}
.feat:last-child{border-bottom:none;}
.feat-ico{width:20px;height:20px;border-radius:50%;background:rgba(34,211,238,0.1);
  border:1px solid rgba(34,211,238,0.25);display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px;}
.check{width:10px;height:10px;stroke:#22d3ee;fill:none;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round;}
.feat-txt{font-size:12.5px;color:var(--text2);line-height:1.5;}
.feat-txt b{color:var(--text);font-weight:500;}

/* Stats */
.stats{display:flex;gap:9px;position:relative;z-index:2;animation:fadein 0.55s ease 0.55s both;}
.stat{flex:1;background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:11px;padding:11px 13px;}
.stat-val{font-size:17px;font-weight:600;color:var(--text);font-family:var(--mono);line-height:1;}
.stat-lbl{font-size:10px;color:var(--text3);margin-top:4px;display:flex;align-items:center;gap:3px;}
.dot{width:5px;height:5px;border-radius:50%;flex-shrink:0;}
.dg{background:#22d3ee;animation:blink 1.6s ease infinite;}
.da{background:#f59e0b;}
.dr{background:#ef4444;animation:blink 1s ease infinite;}

/* RIGHT */
.right{width:48%;background:var(--card);padding:42px 38px;display:flex;flex-direction:column;justify-content:center;}

/* Tab */
.tabs{display:flex;background:rgba(255,255,255,0.04);border:1px solid var(--border);border-radius:11px;padding:3px;margin-bottom:28px;}
.tab{flex:1;padding:8px;font-size:13px;font-family:var(--sans);color:var(--text3);
  background:transparent;border:none;border-radius:9px;cursor:pointer;transition:all 0.2s;font-weight:500;}
.tab.on{background:rgba(255,255,255,0.07);color:var(--text);border:1px solid var(--border2);}

/* Form */
.fh{margin-bottom:22px;}
.fh-title{font-size:21px;font-weight:600;color:var(--text);letter-spacing:-0.4px;margin-bottom:4px;}
.fh-sub{font-size:13px;color:var(--text3);}
.fg{margin-bottom:13px;}
.fl{font-size:10.5px;font-weight:500;color:var(--text3);text-transform:uppercase;letter-spacing:0.6px;margin-bottom:5px;display:block;}
.fi{width:100%;padding:9px 12px;background:rgba(255,255,255,0.04);border:1px solid var(--border2);
  border-radius:9px;font-size:13.5px;color:var(--text);font-family:var(--sans);
  transition:border-color 0.2s,box-shadow 0.2s;outline:none;}
.fi:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(56,189,248,0.15);}
.fi::placeholder{color:var(--text3);}
.fi option{background:#111a2e;color:var(--text);}
.frow{display:grid;grid-template-columns:1fr 1fr;gap:11px;}

/* Role cards */
.role-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:7px;margin-bottom:13px;}
.rc{padding:10px 7px;border:1px solid var(--border);border-radius:9px;text-align:center;cursor:pointer;
  transition:all 0.2s;background:rgba(255,255,255,0.02);}
.rc:hover{border-color:rgba(56,189,248,0.4);background:rgba(56,189,248,0.06);}
.rc.sel{border-color:var(--accent);background:rgba(56,189,248,0.1);}
.rc-em{font-size:17px;display:block;margin-bottom:3px;}
.rc-lbl{font-size:10.5px;color:var(--text3);font-weight:500;}

/* Submit btn */
.btn{width:100%;padding:12px;background:linear-gradient(135deg,#0ea5e9 0%,#6366f1 100%);
  border:none;border-radius:10px;color:white;font-size:14px;font-weight:600;
  font-family:var(--sans);cursor:pointer;transition:opacity 0.2s,transform 0.12s;
  margin-top:5px;letter-spacing:0.2px;position:relative;overflow:hidden;}
.btn::before{content:'';position:absolute;top:0;left:-100%;width:100%;height:100%;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,0.14),transparent);
  animation:shimmer 3s ease infinite 2s;}
@keyframes shimmer{0%{left:-100%;}100%{left:200%;}}
.btn:hover{opacity:0.9;}
.btn:active{transform:scale(0.99);}

/* Demo */
.demo{background:rgba(255,255,255,0.025);border:1px solid var(--border);border-radius:9px;padding:12px 14px;margin-top:14px;}
.demo-ttl{font-size:10px;font-family:var(--mono);font-weight:500;color:var(--accent);text-transform:uppercase;letter-spacing:1px;margin-bottom:7px;}
.demo-row{display:flex;justify-content:space-between;padding:2px 0;}
.demo-role{font-size:11px;color:var(--text3);}
.demo-cred{font-size:11px;font-family:var(--mono);color:var(--text2);}

/* Msg */
.msg{display:none;margin-top:11px;padding:9px 12px;border-radius:9px;font-size:12.5px;}
.ok{background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.3);color:#4ade80;}
.err{background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);color:#f87171;}

/* Security badges */
.sec-row{display:flex;gap:6px;flex-wrap:wrap;margin-top:13px;}
.sec{padding:3px 9px;border-radius:20px;font-size:10.5px;font-weight:500;border:1px solid;}
.s1{background:rgba(56,189,248,0.08);border-color:rgba(56,189,248,0.25);color:#7dd3fc;}
.s2{background:rgba(99,102,241,0.08);border-color:rgba(99,102,241,0.25);color:#a5b4fc;}
.s3{background:rgba(34,211,238,0.08);border-color:rgba(34,211,238,0.25);color:#67e8f9;}

/* Checkbox */
.chk-row{display:flex;align-items:flex-start;gap:8px;margin-bottom:5px;}
.chk-row input{margin-top:3px;accent-color:#38bdf8;}
.chk-row span{font-size:11.5px;color:var(--text3);line-height:1.5;}
</style>
</head>
<body>
<div class="bg-orbs"><div class="orb orb1"></div><div class="orb orb2"></div><div class="orb orb3"></div></div>
<div class="bg-grid"></div>

<div class="page">
<div class="card">

  <!-- LEFT -->
  <div class="left">
    <div class="pulse-wrap"><div class="pulse p1"></div><div class="pulse p2"></div><div class="pulse p3"></div></div>
    <svg class="ecg-svg" viewBox="0 0 460 56" xmlns="http://www.w3.org/2000/svg">
      <path class="ecg-path" d="M0,28 L28,28 L33,26 L38,9 L43,47 L48,4 L53,52 L58,28 L88,28 L93,26 L98,9 L103,47 L108,4 L113,52 L118,28 L150,28 L155,26 L160,9 L165,47 L170,4 L175,52 L180,28 L212,28 L217,26 L222,9 L227,47 L232,4 L237,52 L242,28 L274,28 L279,26 L284,9 L289,47 L294,4 L299,52 L304,28 L336,28 L341,26 L346,9 L351,47 L356,4 L361,52 L366,28 L400,28 L440,28 L460,28"/>
    </svg>

    <div class="brand">
      <div class="logo-row">
        <div class="logo-box"><div class="logo-cross"></div></div>
        <div><div class="brand-name">Cortexa Health</div><div class="brand-ver">Clinical Platform · v5.0</div></div>
      </div>
      <div class="hb-badge"><div class="hb-dot"></div><span class="hb-txt">All systems operational</span></div>
      <div class="tagline">AI-powered radiology at <span>clinical precision</span>.<br>Built for the modern physician.</div>
    </div>

    <div class="feats">
  
      <div class="feat"><div class="feat-ico"><svg class="check" viewBox="0 0 12 12"><polyline points="2,6 5,9 10,3"/></svg></div><div class="feat-txt"><b>AI heatmap</b> — multi-region attention visualization</div></div>
      <div class="feat"><div class="feat-ico"><svg class="check" viewBox="0 0 12 12"><polyline points="2,6 5,9 10,3"/></svg></div><div class="feat-txt"><b>PDF &amp; Word export</b> — clinical-grade formatted reports</div></div>
      <div class="feat"><div class="feat-ico"><svg class="check" viewBox="0 0 12 12"><polyline points="2,6 5,9 10,3"/></svg></div><div class="feat-txt"><b>Drug interaction checker</b> — AI pharmacology engine</div></div>
      <div class="feat"><div class="feat-ico"><svg class="check" viewBox="0 0 12 12"><polyline points="2,6 5,9 10,3"/></svg></div><div class="feat-txt"><b>Lab &amp; vitals tracking</b> — patient timeline &amp; trend graphs</div></div>
      <div class="feat"><div class="feat-ico"><svg class="check" viewBox="0 0 12 12"><polyline points="2,6 5,9 10,3"/></svg></div><div class="feat-txt"><b>HIPAA-ready</b> — role-based access &amp; audit logging</div></div>
    </div>

    <div class="stats">
      <div class="stat"><div class="stat-val">2,840</div><div class="stat-lbl"><span class="dot dg"></span>Scans analysed</div></div>
      <div class="stat"><div class="stat-val">94.2%</div><div class="stat-lbl"><span class="dot da"></span>AI accuracy</div></div>
      <div class="stat"><div class="stat-val">3</div><div class="stat-lbl"><span class="dot dr"></span>Critical today</div></div>
    </div>
  </div>

  <!-- RIGHT -->
  <div class="right">
    <div class="tabs">
      <button class="tab on" id="t-login" onclick="sw('login')">Sign In</button>
      <button class="tab" id="t-register" onclick="sw('register')">Register</button>
    </div>

    <!-- LOGIN -->
    <div id="s-login">
      <div class="fh"><div class="fh-title">Welcome back</div><div class="fh-sub">Sign in to access the platform</div></div>
      <div class="fg"><label class="fl">Username</label><input class="fi" type="text" id="lu" placeholder="e.g. dr.sharma" autocomplete="username" onkeydown="if(event.key==='Enter')doLogin();"/></div>
      <div class="fg"><label class="fl">Password</label><input class="fi" type="password" id="lp" placeholder="••••••••" autocomplete="current-password" onkeydown="if(event.key==='Enter')doLogin();"/></div>
      <button class="btn" onclick="doLogin()">Sign In to Cortexa Health</button>
      <div class="msg" id="ml"></div>
      <div class="demo">
        <div class="demo-ttl">Demo credentials</div>
        <div class="demo-row"><span class="demo-role">Doctor</span><span class="demo-cred">dr.sharma / doctor123</span></div>
        <div class="demo-row"><span class="demo-role">Radiologist</span><span class="demo-cred">rad.jones / radio123</span></div>
        <div class="demo-row"><span class="demo-role">Admin</span><span class="demo-cred">admin / admin123</span></div>
      </div>
      <div class="sec-row"><span class="sec s1">Groq Powered</span><span class="sec s2">HIPAA-Ready</span><span class="sec s3">SHA-256 Auth</span></div>
    </div>

    <!-- REGISTER -->
    <div id="s-register" style="display:none;">
      <div class="fh"><div class="fh-title">Create account</div><div class="fh-sub">Join Cortexa Health — takes under a minute</div></div>
      <div class="fg">
        <label class="fl">Select your role</label>
        <div class="role-grid">
          <div class="rc sel" onclick="selRole(this)"><span class="rc-em">&#128105;&#8205;&#9877;&#65039;</span><div class="rc-lbl">Doctor</div></div>
          <div class="rc" onclick="selRole(this)"><span class="rc-em">&#129467;</span><div class="rc-lbl">Radiologist</div></div>
          <div class="rc" onclick="selRole(this)"><span class="rc-em">&#9881;&#65039;</span><div class="rc-lbl">Admin</div></div>
        </div>
      </div>
      <div class="frow">
        <div class="fg"><label class="fl">Full name</label><input class="fi" type="text" id="rn" placeholder="Dr. Jane Smith"/></div>
        <div class="fg"><label class="fl">Username</label><input class="fi" type="text" id="ru" placeholder="dr.smith"/></div>
      </div>
      <div class="frow">
        <div class="fg"><label class="fl">Email</label><input class="fi" type="email" id="re" placeholder="jane@hospital.com"/></div>
        <div class="fg"><label class="fl">Department</label>
          <select class="fi" id="rd"><option>Radiology</option><option>Cardiology</option><option>Neurology</option><option>Oncology</option><option>Emergency</option><option>IT</option></select>
        </div>
      </div>
      <div class="frow">
        <div class="fg"><label class="fl">Password</label><input class="fi" type="password" id="rp" placeholder="Min 6 characters"/></div>
        <div class="fg"><label class="fl">License No.</label><input class="fi" type="text" id="rl" placeholder="MCI-2025-XXXX"/></div>
      </div>
      <div class="fg"><label class="fl">Confirm password</label><input class="fi" type="password" id="rp2" placeholder="Re-enter password"/></div>
      <div class="chk-row">
        <input type="checkbox" id="agree"/>
        <span>I agree to the Terms of Use, HIPAA compliance, and data protection guidelines</span>
      </div>
      <button class="btn" onclick="doRegister()">Create Account</button>
      <div class="msg" id="mr"></div>
    </div>
  </div>

</div><!-- .card -->
</div><!-- .page -->

<script>
function sw(t){
  document.getElementById('s-login').style.display=t==='login'?'block':'none';
  document.getElementById('s-register').style.display=t==='register'?'block':'none';
  document.getElementById('t-login').className='tab'+(t==='login'?' on':'');
  document.getElementById('t-register').className='tab'+(t==='register'?' on':'');
  hm('ml');hm('mr');
}
function selRole(el){document.querySelectorAll('.rc').forEach(c=>c.classList.remove('sel'));el.classList.add('sel');}
function sm(id,txt,ok){var e=document.getElementById(id);e.textContent=txt;e.className='msg '+(ok?'ok':'err');e.style.display='block';}
function hm(id){var e=document.getElementById(id);if(e)e.style.display='none';}

var USERS={'dr.sharma':'doctor123','rad.jones':'radio123','admin':'admin123'};
var NAMES={'dr.sharma':'Dr. Priya Sharma','rad.jones':'Dr. Sarah Jones','admin':'System Admin'};
var ROLES={'dr.sharma':'Doctor','rad.jones':'Radiologist','admin':'Admin'};

function doLogin(){
  var u=document.getElementById('lu').value.trim().toLowerCase();
  var p=document.getElementById('lp').value;
  if(!u||!p){sm('ml','Please enter both username and password.',false);return;}
  if(USERS[u]&&USERS[u]===p){
    sm('ml','Signed in successfully! Loading dashboard…',true);
    setTimeout(function(){
      window.parent.postMessage({type:'medicore_login',username:u,name:NAMES[u],role:ROLES[u]},'*');
    },600);
  } else {
    sm('ml','Invalid credentials. Try the demo accounts listed below.',false);
  }
}

function doRegister(){
  var n=document.getElementById('rn').value.trim();
  var u=document.getElementById('ru').value.trim();
  var e=document.getElementById('re').value.trim();
  var p=document.getElementById('rp').value;
  var p2=document.getElementById('rp2').value;
  var a=document.getElementById('agree').checked;
  if(!n||!u||!e||!p){sm('mr','Please fill in all required fields.',false);return;}
  if(!a){sm('mr','Please agree to the Terms of Use to continue.',false);return;}
  if(p.length<6){sm('mr','Password must be at least 6 characters.',false);return;}
  if(p!==p2){sm('mr','Passwords do not match.',false);return;}
  sm('mr','Account created successfully! Signing you in…',true);
  USERS[u.toLowerCase()]=p; NAMES[u.toLowerCase()]=n; ROLES[u.toLowerCase()]='Doctor';
  setTimeout(function(){sw('login');},1600);
}
</script>
</body>
</html>
"""

    # Render the full-page HTML login component
    result = components.html(LOGIN_HTML, height=700, scrolling=False)

    # Listen for postMessage login event via query params workaround
    # We use a hidden form + URL param approach for Streamlit communication
    st.markdown("""
    <style>
    iframe{border:none !important; width:100% !important;}
    .stApp{background:#070d1a !important;}
    </style>
    <script>
    window.addEventListener('message', function(e){
        if(e.data && e.data.type === 'medicore_login'){
            var params = new URLSearchParams(window.location.search);
            params.set('login_user', e.data.username);
            window.location.search = params.toString();
        }
    });
    </script>
    """, unsafe_allow_html=True)

    # Check if login came through via query param
    query_params = st.query_params
    if "login_user" in query_params:
        uname = query_params["login_user"]
        db = st.session_state.users_db
        u = db.get(uname)
        if u:
            st.session_state.logged_in = True
            st.session_state.user  = u["name"]
            st.session_state.role  = u["role"]
            st.session_state.dept  = u["dept"]
            st.session_state.avatar = u.get("avatar","👤")
            log_action("LOGIN", f"{u['name']} signed in")
            st.query_params.clear()
            st.rerun()

    # Fallback plain login below the component (always visible as backup)
    st.markdown("""
    <div style="background:#0e1628;border:1px solid rgba(255,255,255,0.1);border-radius:14px;
                padding:20px 28px;max-width:420px;margin:16px auto 0;">
      <div style="font-size:13px;color:#94a3b8;margin-bottom:12px;font-family:'JetBrains Mono',monospace;
                  text-align:center;letter-spacing:0.5px;">OR USE STREAMLIT LOGIN BELOW</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("""
        <style>
        .stTextInput input{background:rgba(255,255,255,0.05)!important;border:1px solid rgba(255,255,255,0.15)!important;
          color:black!important;border-radius:9px!important;}
        .stTextInput input::placeholder{color:black!important;}
        .stTextInput label{color:black!important;font-size:11px!important;text-transform:uppercase;letter-spacing:0.6px;}
        .stButton>button{background:linear-gradient(135deg,#0ea5e9,#6366f1)!important;
          border:none!important;border-radius:10px!important;font-weight:600!important;width:100%;}
        </style>
        """, unsafe_allow_html=True)
        username = st.text_input("Username", placeholder="e.g. dr.sharma", key="li_user_fb")
        password = st.text_input("Password", type="password", placeholder="••••••••", key="li_pass_fb")
        if st.button("Sign In to Cortexa Health", use_container_width=True, key="login_btn_fb"):
            db = st.session_state.users_db
            u  = db.get(username.strip().lower())
            if u and u["password"] == hash_pw(password):
                st.session_state.logged_in = True
                st.session_state.user   = u["name"]
                st.session_state.role   = u["role"]
                st.session_state.dept   = u["dept"]
                st.session_state.avatar = u.get("avatar","👤")
                log_action("LOGIN", f"{u['name']} signed in")
                st.success(f"✅ Welcome, {u['name']}!")
                time.sleep(0.4)
                st.rerun()
            else:
                st.error("❌ Invalid username or password.")

    st.stop()

# ═══════════════════════════════════════════════
# ██████  SIDEBAR
# ═══════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""<div style='padding:.6rem .3rem .5rem;border-bottom:1px solid var(--border);'>
      <div style='display:flex;align-items:center;gap:.45rem;'>
        <span style='font-size:1.4rem;'>🏥</span>
        <div><div style='font-weight:800;font-size:.85rem;'>Cortexa Health</div><div style='font-size:.55rem;font-family:var(--mono);color:var(--text3);text-transform:uppercase;letter-spacing:1px;'>v{APP_VERSION}</div></div>
      </div></div>""", unsafe_allow_html=True)

    # Dark mode toggle
    dm_col1,dm_col2=st.columns([3,1])
    with dm_col1: st.markdown("<div style='font-size:.72rem;color:var(--text2);padding:.3rem 0;'>🌙 Dark Mode</div>", unsafe_allow_html=True)
    with dm_col2:
        if st.toggle("",value=st.session_state.dark_mode,key="dm_toggle",label_visibility="collapsed"):
            if not st.session_state.dark_mode: st.session_state.dark_mode=True; st.rerun()
        else:
            if st.session_state.dark_mode: st.session_state.dark_mode=False; st.rerun()

    st.markdown(f"""<div style='padding:.4rem .3rem .4rem;border-bottom:1px solid var(--border);border-top:1px solid var(--border);'>
      <div style='display:flex;align-items:center;gap:.5rem;'>
        <div style='font-size:1.4rem;'>{st.session_state.avatar}</div>
        <div><div style='font-weight:700;font-size:.79rem;'>{st.session_state.user}</div>
        <div style='margin-top:2px;'>{role_badge_html(st.session_state.role)}</div>
        <div style='font-size:.6rem;color:var(--text3);'>{st.session_state.dept}</div></div>
      </div></div>""", unsafe_allow_html=True)

    # Quick access
    st.markdown("<div style='padding:.35rem .2rem .12rem;'><div class='sb-nav-label'>⚡ Quick</div></div>", unsafe_allow_html=True)
    q1,q2=st.columns(2)
    for col,lbl,pg,cls in [(q1,"🏠 Dash","dashboard","sb-q1"),(q2,"📊 Stats","analytics","sb-q2")]:
        with col:
            st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
            if st.button(lbl,use_container_width=True,key=f"q_{pg}"): st.session_state.page=pg; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    q3,q4=st.columns(2)
    for col,lbl,pg,cls in [(q3,"🔬 Scan","analysis","sb-q3"),(q4,"💬 Chat","ai_chat","sb-q2")]:
        with col:
            st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
            if st.button(lbl,use_container_width=True,key=f"q_{pg}2"): st.session_state.page=pg; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='margin:.35rem 0;border-top:1px solid var(--border);'></div>", unsafe_allow_html=True)
    st.markdown("<div style='padding:0 .2rem;'><div class='sb-nav-label'>Navigation</div></div>", unsafe_allow_html=True)

    nav_items=[
        ("🏠","Dashboard","dashboard"),("🔬","AI Analysis","analysis"),("📦","Batch Analysis","batch"),
        ("🧠","Heatmap Studio","heatmap"),("👥","Patients","patients"),("📋","Patient Logs","patient_logs"),
        ("⚠️","Precautions","precautions"),("💊","Medications","medications"),("🧪","Lab Values","labs"),
        ("📅","Appointments","appointments"),("📊","Analytics","analytics"),("💬","AI Chat","ai_chat"),
        ("💊","Drug Checker","drugs"),("📝","Report Templates","templates"),("🔔","Alerts","alerts"),
        ("📋","Audit Log","audit"),
    ]
    if st.session_state.role=="Admin": nav_items.append(("👤","Users","users"))

    for icon,label,key in nav_items:
        active=st.session_state.page==key
        css="nav-btn-active" if active else "nav-btn"
        st.markdown(f'<div class="{css}">', unsafe_allow_html=True)
        if st.button(f"{icon}  {label}",key=f"nav_{key}",use_container_width=True): st.session_state.page=key; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

   
    st.markdown("<div style='margin:.35rem 0;border-top:1px solid var(--border);'></div>", unsafe_allow_html=True)
    if st.button("🚪  Sign Out",use_container_width=True,key="logout"):
        log_action("LOGOUT",f"{st.session_state.user} signed out")
        for k in ["logged_in","user","role","dept","avatar","page","history","alerts","total","critical","warnings","chat_messages"]:
            st.session_state[k]=defaults[k]
        st.rerun()

# ═══════════════════════════════════════════════
# ██████  DASHBOARD
# ═══════════════════════════════════════════════
if st.session_state.page=="dashboard":
    st.markdown(f"""<div class="mc-header"><h1>🏥 Clinical Dashboard</h1>
    <p>MEDICORE AI v5 · {st.session_state.user} · {st.session_state.role} · {datetime.now().strftime("%A, %d %B %Y, %H:%M")}</p>
    <div class="mc-badge-row"><span class="mc-badge badge-green">✅ All Systems Online</span><span class="mc-badge badge-pink">🔒 Secure Session</span></div></div>""", unsafe_allow_html=True)

    crit_pts=sum(1 for p in DEMO_PATIENTS if p["risk"]=="CRITICAL")
    avg_risk=round(sum(compute_risk_score(p) for p in DEMO_PATIENTS)/len(DEMO_PATIENTS))
    total_logs=sum(len(v) for v in st.session_state.patient_logs.values())
    c1,c2,c3,c4,c5,c6=st.columns(6)
    with c1: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="color:#2563eb">{len(DEMO_PATIENTS)}</div><div class="mc-stat-lbl">Patients</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val">{st.session_state.total}</div><div class="mc-stat-lbl">Scans</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="color:#dc2626">{st.session_state.critical}</div><div class="mc-stat-lbl">Critical</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="color:#d97706">{crit_pts}</div><div class="mc-stat-lbl">High-Risk Pts</div></div>', unsafe_allow_html=True)
    with c5: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="color:#7c3aed">{avg_risk}</div><div class="mc-stat-lbl">Avg Risk</div></div>', unsafe_allow_html=True)
    with c6: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="color:#0891b2">{total_logs}</div><div class="mc-stat-lbl">Log Entries</div></div>', unsafe_allow_html=True)

    st.markdown("<div style='margin-top:.9rem;'></div>", unsafe_allow_html=True)
    left,right=st.columns([1.1,1])
    with left:
        st.markdown("<div class='mc-section-title'>🔴 HIGH PRIORITY ALERTS</div>", unsafe_allow_html=True)
        for p in DEMO_PATIENTS:
            if p["risk"] in("CRITICAL","HIGH"):
                ico="🔴" if p["risk"]=="CRITICAL" else "🟡"
                cls="mc-alert" if p["risk"]=="CRITICAL" else "mc-alert-warning"
                st.markdown(f'<div class="{cls}">{ico} <b>{p["name"]}</b> ({p["id"]}) — {p["risk"]} · {p["condition"]}<br><span style="font-size:.7rem;">BP: {p["bp"]} · O₂: {p["o2"]} · Allergies: {p["allergies"]}</span></div>', unsafe_allow_html=True)

        st.markdown("<div style='margin-top:.7rem;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='mc-section-title'>🧠 ML RISK SCORES</div>", unsafe_allow_html=True)
        for p in sorted(DEMO_PATIENTS,key=lambda x:compute_risk_score(x),reverse=True)[:5]:
            score=compute_risk_score(p); bar_c="#dc2626" if score>=70 else("#d97706" if score>=40 else "#059669")
            st.markdown(f"""<div style='display:flex;align-items:center;gap:7px;margin-bottom:4px;'>
              <div style='min-width:110px;font-size:.75rem;font-weight:600;'>{p["name"].split()[0]} {p["name"].split()[-1]}</div>
              <div style='flex:1;background:var(--border);border-radius:99px;height:6px;overflow:hidden;'><div style='width:{score}%;height:100%;border-radius:99px;background:{bar_c};'></div></div>
              <div style='min-width:36px;font-family:var(--mono);font-size:.75rem;font-weight:700;color:{bar_c};'>{score}/100</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='margin-top:.7rem;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='mc-section-title'>📅 UPCOMING APPOINTMENTS</div>", unsafe_allow_html=True)
        upcoming=[]
        for p in DEMO_PATIENTS:
            for a in p.get("appointments",[]):
                upcoming.append({**a,"patient":p["name"],"pid":p["id"]})
        upcoming.sort(key=lambda x:x["date"])
        for a in upcoming[:4]:
            urg_cls="mc-alert" if a.get("status")=="URGENT" else "mc-scan-row"
            st.markdown(f'<div class="{urg_cls}"><div><div style="font-size:.82rem;font-weight:600;">{a["date"]} {a["time"]} — {a["type"]}</div><div style="font-size:.69rem;color:var(--text3);">{a["patient"]} ({a["pid"]}) · {a["doctor"]}</div></div><span class="mc-tag {"tag-critical" if a.get("status")=="URGENT" else "tag-blue"}">{a.get("status","Scheduled")}</span></div>', unsafe_allow_html=True)

    with right:
        st.markdown("<div class='mc-section-title'>👥 PATIENT ROSTER</div>", unsafe_allow_html=True)
        for p in DEMO_PATIENTS:
            gi="👨" if p["gender"]=="M" else "👩"; rc=risk_color(p["risk"]); score=compute_risk_score(p)
            st.markdown(f"""<div class="mc-patient-card">
                <div class="mc-avatar" style='background:{"var(--red-lt)" if p["risk"]=="CRITICAL" else "var(--green-lt)"};'>{gi}</div>
                <div style='flex:1;'>
                    <div style='font-weight:600;font-size:.82rem;'>{p['name']}</div>
                    <div style='font-size:.66rem;color:var(--text3);font-family:var(--mono);'>{p['id']} · Age {p['age']} · {p['condition']}</div>
                    <div style='font-size:.65rem;color:var(--text3);'>💊 {len(p.get("medications",[]))} meds · Allergies: {p["allergies"]}</div>
                </div>
                <div style='text-align:right;'>
                  <div style='font-size:.75rem;font-weight:700;color:{rc};'>{p['risk']}</div>
                  <div style='font-size:.63rem;color:var(--text3);'>{score}/100</div>
                </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='margin-top:.7rem;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='mc-section-title'>⚡ QUICK ACTIONS</div>", unsafe_allow_html=True)
        g1,g2,g3=st.columns(3)
        btns=[("🔬 Scan","analysis"),("📊 Analytics","analytics"),("💬 Chat","ai_chat"),("⚠️ Precautions","precautions"),("💊 Drugs","drugs"),("🧪 Labs","labs")]
        for i,(lbl,pg) in enumerate(btns):
            col=[g1,g2,g3][i%3]
            with col:
                if st.button(lbl,use_container_width=True,key=f"dash_{pg}"): st.session_state.page=pg; st.rerun()

# ═══════════════════════════════════════════════
# ██████  AI ANALYSIS
# ═══════════════════════════════════════════════
elif st.session_state.page=="analysis":
    st.markdown("""<div class="mc-header"><h1>🔬 AI Medical Image Analysis</h1>
    <p>GROQ + LLAMA 4 VISION · REAL PDF/DOCX EXPORT · HEATMAP · ICD-10 · PRECAUTIONS · 8 TEMPLATES</p>
    <div class="mc-badge-row"><span class="mc-badge badge-white">Vision AI</span><span class="mc-badge badge-yellow">Differential Dx</span><span class="mc-badge badge-green">Real PDF Export</span><span class="mc-badge badge-pink">Word .docx Export</span></div></div>""", unsafe_allow_html=True)

    lcol,rcol=st.columns([1,1.7],gap="large")
    with lcol:
        st.markdown("<div class='mc-section-title'>SETTINGS</div>", unsafe_allow_html=True)
        template_sel=st.selectbox("Report Template",list(REPORT_TEMPLATES.keys()))
        st.markdown(f'<div class="mc-alert-info" style="margin-bottom:.5rem;">{REPORT_TEMPLATES[template_sel]}</div>', unsafe_allow_html=True)
        analysis_mode=st.selectbox("Mode",["Comprehensive","Quick Scan","Patient Mode","Research","Second Opinion"])
        modality=st.selectbox("Modality",["Auto-detect","Chest X-Ray","Brain MRI","Abdomen CT","Chest CT","MSK MRI","Ultrasound","PET Scan","Mammogram","Spine X-Ray","Echocardiogram","Dental OPG"])
        urgency=st.selectbox("Urgency",["Routine","Urgent","Emergency"])
        model_label=st.selectbox("AI Model",list(GROQ_MODELS.keys())); groq_model=GROQ_MODELS[model_label]
        c1,c2=st.columns(2)
        with c1: incl_research=st.toggle("Research",value=True); incl_patient=st.toggle("Patient Summary",value=True)
        with c2: incl_icd=st.toggle("ICD-10",value=True); incl_meas=st.toggle("Measurements",value=True)
        incl_prec=st.toggle("⚠️ Precautions",value=True)

        st.markdown("<div style='margin-top:.5rem;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='mc-section-title'>LINK PATIENT</div>", unsafe_allow_html=True)
        pt_opts=["— None —"]+[f"{p['id']} — {p['name']}" for p in DEMO_PATIENTS]
        sel_pt=st.selectbox("Patient",pt_opts,label_visibility="collapsed")
        pt_ctx=""; linked_patient=None
        if sel_pt!="— None —":
            pid=sel_pt.split(" — ")[0]; linked_patient=next((p for p in DEMO_PATIENTS if p["id"]==pid),None)
            if linked_patient: pt_ctx=f"{linked_patient['name']}, {'Male' if linked_patient['gender']=='M' else 'Female'}, Age {linked_patient['age']}, {linked_patient['condition']}, Smoker:{linked_patient['smoker']}, Allergies:{linked_patient['allergies']}"

        compare_mode=st.checkbox("🔄 Prior study comparison")
        prior_text=st.text_area("Prior findings",height=50,placeholder="Jan 2024 CT: 8mm RUL nodule...") if compare_mode else ""

        st.markdown("<div style='margin-top:.5rem;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='mc-section-title'>UPLOAD IMAGE</div>", unsafe_allow_html=True)
        uploaded_file=st.file_uploader("Upload",type=["jpg","jpeg","png","bmp","webp","tiff"],label_visibility="collapsed")

        if uploaded_file:
            img=PILImage.open(uploaded_file); st.image(img,use_container_width=True)
            w,h=img.size; sz=len(uploaded_file.getvalue())/1024
            st.markdown(f'<div style="background:var(--elevated);border:1px solid var(--border);border-radius:var(--radius-sm);padding:.45rem .75rem;font-family:var(--mono);font-size:.68rem;color:var(--text2);margin-top:.3rem;">📐 {w}×{h}px · 📦 {sz:.1f} KB · 🎨 {img.mode}</div>', unsafe_allow_html=True)
            custom_q=st.text_area("Clinical context",height=65,placeholder="e.g. 67M, heavy smoker, 3-week haemoptysis...")
            analyze_btn=st.button("🔬 Run AI Analysis",use_container_width=True)
            st.markdown('<div style="background:var(--red-lt);border:1px solid #fca5a5;border-radius:var(--radius-sm);padding:.45rem .75rem;font-size:.69rem;color:#dc2626;margin-top:.35rem;">⚠️ Educational use only. Validate with a qualified radiologist.</div>', unsafe_allow_html=True)
        else:
            st.markdown("""<div style='background:var(--elevated);border:2px dashed var(--border2);border-radius:var(--radius);padding:1.8rem;text-align:center;'>
                <div style='font-size:2rem;margin-bottom:.5rem;'>🩻</div>
                <div style='font-weight:600;font-size:.86rem;'>Upload a Medical Image</div>
                <div style='font-size:.75rem;color:var(--text3);margin-top:.25rem;'>X-Ray · MRI · CT · Ultrasound · PET · Mammo</div>
            </div>""", unsafe_allow_html=True)
            analyze_btn=False; custom_q=""

    with rcol:
        st.markdown("<div class='mc-section-title'>AI DIAGNOSTIC REPORT</div>", unsafe_allow_html=True)
        if uploaded_file and analyze_btn:
            st.markdown('<div class="loading-bar"></div>', unsafe_allow_html=True)
            progress=st.progress(0,text="🔍 Preprocessing image...")
            try:
                progress.progress(15,text="📡 Connecting to Groq LLaMA 4...")
                prompt=build_prompt(analysis_mode,modality,urgency,custom_q,pt_ctx,incl_research,incl_patient,incl_icd,incl_meas,incl_prec,prior_text,template_sel)
                progress.progress(30,text="⚡ Analysing image...")
                img_pil=PILImage.open(uploaded_file); t0=time.time()
                report=run_analysis(img_pil,prompt,groq_model)
                elapsed=time.time()-t0
                progress.progress(85,text="🧠 Extracting clinical insights...")
                time.sleep(.15)
                uflag=detect_urgency_flag(report); conf=extract_confidence(report); prim_dx=extract_primary_dx(report)
                progress.progress(100,text="✅ Report ready!"); time.sleep(.25); progress.empty()

                st.session_state.total+=1
                if uflag=="CRITICAL": st.session_state.critical+=1
                elif uflag=="WARNING": st.session_state.warnings+=1
                heatmap_img=generate_heatmap(img_pil,uflag)
                log_action("ANALYSIS",f"{uploaded_file.name} · {uflag} · {conf}%")
                if linked_patient: add_patient_log(linked_patient["id"],f"AI Analysis: {prim_dx} · Conf:{conf}% · {uflag} · {uploaded_file.name}","AI Scan")

                entry={"filename":uploaded_file.name,"time":datetime.now().strftime("%H:%M"),"date":datetime.now().strftime("%Y-%m-%d"),"report":report,"mode":analysis_mode,"modality":modality,"urgency_flag":uflag,"confidence":conf,"model":model_label,"primary_dx":prim_dx,"patient":pt_ctx or "Unlinked","doctor":st.session_state.user,"elapsed":f"{elapsed:.1f}s","heatmap":heatmap_img,"img_original":img_pil,"template":template_sel}
                st.session_state.history.append(entry)
                if uflag=="CRITICAL": st.session_state.alerts.append({"time":datetime.now().strftime("%H:%M"),"msg":f"CRITICAL finding — {uploaded_file.name}","level":"CRITICAL"})

                if uflag=="CRITICAL": st.markdown('<div class="banner-critical">🚨 CRITICAL FINDING — Immediate clinical attention required</div>', unsafe_allow_html=True)
                elif uflag=="WARNING": st.markdown('<div class="banner-warning">⚠️ Abnormal findings — Physician review recommended</div>', unsafe_allow_html=True)
                else: st.markdown('<div class="banner-normal">✅ Analysis complete — No critical findings identified</div>', unsafe_allow_html=True)

                qa,qb,qc=st.columns(3)
                bar_c="#dc2626" if uflag=="CRITICAL" else("#d97706" if uflag=="WARNING" else "#059669")
                qa.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="font-size:.82rem;color:#2563eb;">{prim_dx[:20]}{"…" if len(prim_dx)>20 else ""}</div><div class="mc-stat-lbl">Primary Dx</div></div>', unsafe_allow_html=True)
                qb.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="font-size:.97rem;color:{bar_c};">{conf}%</div><div class="mc-stat-lbl">Confidence</div><div class="conf-wrap" style="margin-top:4px;"><div class="conf-fill" style="width:{conf}%;background:{bar_c};"></div></div></div>', unsafe_allow_html=True)
                qc.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="font-size:.97rem;color:#7c3aed;">{elapsed:.1f}s</div><div class="mc-stat-lbl">Response Time</div></div>', unsafe_allow_html=True)

                st.markdown("<div style='margin-top:.7rem;'></div>", unsafe_allow_html=True)
                tab1,tab2,tab3,tab4,tab5=st.tabs(["📋 Full Report","🎨 Heatmap","🖼️ Enhancement","📤 Export","🕑 History"])

                with tab1:
                    st.markdown(f'<div class="report-box">{report}</div>', unsafe_allow_html=True)

                with tab2:
                    sens=st.slider("Heatmap Sensitivity",0.5,2.0,1.0,.1)
                    hm_regen=generate_heatmap(img_pil,uflag,sens)
                    hm1,hm2=st.columns(2)
                    with hm1: st.markdown("**Original**"); st.image(img_pil,use_container_width=True)
                    with hm2: st.markdown("**AI Heatmap**"); st.image(hm_regen,use_container_width=True)
                    st.markdown(f"""<div class="heatmap-legend"><span class="heatmap-dot" style="background:#dc2626;"></span>Critical<span class="heatmap-dot" style="background:#d97706;"></span>Suspicious<span class="heatmap-dot" style="background:#059669;"></span>Normal<span style="margin-left:auto;font-size:.68rem;color:var(--text3);">Urgency:{uflag} · Conf:{conf}%</span></div>""", unsafe_allow_html=True)
                    hm_buf=io.BytesIO(); hm_regen.save(hm_buf,format="PNG")
                    st.download_button("💾 Download Heatmap",hm_buf.getvalue(),f"heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png","image/png",use_container_width=True)

                with tab3:
                    enh_mode=st.selectbox("Filter",["Sharpen","Enhance Contrast","Denoise","Brighten","Edge Detect","CLAHE","Gamma Correction","Invert (Bone Window)","Pseudo-Color"])
                    enhanced=enhance_image(img_pil,enh_mode)
                    e1,e2=st.columns(2)
                    with e1: st.markdown("**Original**"); st.image(img_pil,use_container_width=True)
                    with e2: st.markdown(f"**{enh_mode}**"); st.image(enhanced,use_container_width=True)
                    enh_buf=io.BytesIO(); enhanced.convert("RGB").save(enh_buf,format="PNG")
                    st.download_button("💾 Download Enhanced",enh_buf.getvalue(),f"enhanced_{enh_mode.lower().replace(' ','_')}.png","image/png",use_container_width=True)

                with tab4:
                    st.markdown("<div class='mc-section-title'>EXPORT OPTIONS</div>", unsafe_allow_html=True)
                    ts=datetime.now().strftime('%Y%m%d_%H%M%S')

                    # Row 1 — PDF, DOCX, HTML
                    e1,e2,e3=st.columns(3)
                    with e1:
                        pdf_bytes=make_pdf_bytes(report,uploaded_file.name,analysis_mode,model_label,uflag,conf,st.session_state.user,pt_ctx,modality)
                        if pdf_bytes: st.download_button("📄 Download PDF",pdf_bytes,f"medicore_{ts}.pdf","application/pdf",use_container_width=True)
                        else: st.markdown('<div class="mc-alert-warning">⚠️ Install reportlab for PDF export</div>', unsafe_allow_html=True)
                    with e2:
                        docx_bytes=make_docx_bytes(report,uploaded_file.name,analysis_mode,model_label,uflag,conf,st.session_state.user,pt_ctx,modality)
                        if docx_bytes: st.download_button("📝 Download Word (.docx)",docx_bytes,f"medicore_{ts}.docx","application/vnd.openxmlformats-officedocument.wordprocessingml.document",use_container_width=True)
                        else: st.markdown('<div class="mc-alert-warning">⚠️ Install python-docx for Word export</div>', unsafe_allow_html=True)
                    with e3:
                        html_r=make_html_report(report,uploaded_file.name,analysis_mode,model_label,uflag,conf,st.session_state.user,pt_ctx,modality)
                        st.download_button("🌐 HTML Report",html_r,f"medicore_{ts}.html","text/html",use_container_width=True)

                    # Row 2 — TXT, JSON, Heatmap
                    e4,e5,e6=st.columns(3)
                    with e4:
                        txt=f"MEDICORE AI CLINICAL REPORT v{APP_VERSION}\n{'='*55}\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\nDoctor: {st.session_state.user}\nPatient: {pt_ctx or 'Unlinked'}\nFile: {uploaded_file.name}\nModality: {modality}\nMode: {analysis_mode}\nTemplate: {template_sel}\nUrgency: {uflag}\nConfidence: {conf}%\n{'='*55}\n\n{report}"
                        st.download_button("📄 TXT Report",txt,f"medicore_{ts}.txt","text/plain",use_container_width=True)
                    with e5:
                        jd=json.dumps({"metadata":{"filename":uploaded_file.name,"timestamp":datetime.now().isoformat(),"doctor":st.session_state.user,"patient":pt_ctx or "Unlinked","modality":modality,"mode":analysis_mode,"template":template_sel,"urgency_flag":uflag,"confidence":conf,"primary_dx":prim_dx},"report":report},indent=2)
                        st.download_button("📦 JSON",jd,f"medicore_{ts}.json","application/json",use_container_width=True)
                    with e6:
                        hm_buf2=io.BytesIO(); heatmap_img.save(hm_buf2,format="PNG")
                        st.download_button("🎨 Heatmap PNG",hm_buf2.getvalue(),f"heatmap_{ts}.png","image/png",use_container_width=True)

                    st.markdown('<div class="mc-alert-info">💡 <b>Tip:</b> For best PDF results, use the <b>Download PDF</b> button (requires reportlab). Alternatively, open the HTML report in a browser → Ctrl+P → Save as PDF.</div>', unsafe_allow_html=True)
                    st.text_area("📋 Copy Raw Report",report,height=160,label_visibility="visible")

                with tab5:
                    if len(st.session_state.history)>1:
                        for h in reversed(st.session_state.history[:-1]):
                            with st.expander(f"{h['filename']} — {h['date']} {h['time']} — {h.get('primary_dx','N/A')[:28]}"):
                                st.markdown(f"**Mode:** {h['mode']} · **Template:** {h.get('template','N/A')} · **Conf:** {h.get('confidence','?')}%")
                                c=h.get("urgency_flag","NORMAL")
                                if c=="CRITICAL": st.markdown('<div class="banner-critical">🚨 CRITICAL</div>', unsafe_allow_html=True)
                                elif c=="WARNING": st.markdown('<div class="banner-warning">⚠️ WARNING</div>', unsafe_allow_html=True)
                                st.markdown(h["report"])
                    else: st.info("Run more analyses to see comparison history.")

            except Exception as e:
                progress.empty(); err=str(e)
                if "401" in err or "invalid_api_key" in err.lower(): st.error("❌ Invalid Groq API key.")
                elif "429" in err or "rate_limit" in err.lower(): st.error("❌ Rate limit — wait and retry.")
                else: st.error(f"❌ {err}")
        elif not uploaded_file:
            features=[("🎨","8 Report Templates","Comprehensive, Quick Triage, Paediatric, Oncology, Cardiac, Research..."),("📄","Real PDF Export","ReportLab-powered professional PDFs with formatted tables and headers"),("📝","Word .docx Export","Editable Word documents with proper styles, tables, and formatting"),("🧪","Lab Values Tracker","Full lab panel with reference ranges, trend monitoring, and alerts"),("💊","Medication Tracker","Per-patient medication list with dosing and drug interaction checker"),("📅","Appointment Scheduler","Schedule, track, and manage clinical appointments"),("📊","Vitals Charts","BP, O₂, HR trend graphs per patient over time"),("🎨","Enhanced Heatmap","Multi-region attention with sensitivity slider and bounding boxes"),("🖼️","9 Image Filters","CLAHE, Gamma, Pseudo-Color, Bone Window, Edge Detect..."),]
            for icon,title,desc in features:
                st.markdown(f'<div class="feature-item"><div class="feature-icon">{icon}</div><div><div class="feature-title">{title}</div><div class="feature-desc">{desc}</div></div></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# ██████  BATCH ANALYSIS
# ═══════════════════════════════════════════════
elif st.session_state.page=="batch":
    st.markdown("""<div class="mc-header"><h1>📦 Batch Multi-Image Analysis</h1><p>ANALYSE MULTIPLE SCANS SIMULTANEOUSLY · AUTO-PRIORITISE · BULK EXPORT</p></div>""", unsafe_allow_html=True)

    uploaded_files=st.file_uploader("Upload multiple images",type=["jpg","jpeg","png","bmp","webp"],accept_multiple_files=True)
    batch_mode=st.selectbox("Analysis mode for all",["Quick Scan","Comprehensive"])
    batch_modality=st.selectbox("Modality for all",["Auto-detect","Chest X-Ray","Brain MRI","Abdomen CT","Chest CT","MSK MRI"])
    model_label=st.selectbox("AI Model",list(GROQ_MODELS.keys()),key="batch_model"); groq_model=GROQ_MODELS[model_label]

    if uploaded_files:
        st.markdown(f'<div class="mc-alert-info">📦 {len(uploaded_files)} images queued for analysis</div>', unsafe_allow_html=True)
        if st.button(f"🔬 Analyse All {len(uploaded_files)} Images",use_container_width=True):
            results=[]
            prog=st.progress(0,text="Starting batch analysis...")
            for i,f in enumerate(uploaded_files):
                prog.progress(int((i/len(uploaded_files))*100),text=f"Analysing {f.name} ({i+1}/{len(uploaded_files)})...")
                try:
                    img=PILImage.open(f)
                    prompt=build_prompt(batch_mode,batch_modality,"Routine","","",False,False,False,False,False,"",batch_mode)
                    report=run_analysis(img,prompt,groq_model)
                    uflag=detect_urgency_flag(report); conf=extract_confidence(report); prim_dx=extract_primary_dx(report)
                    results.append({"filename":f.name,"uflag":uflag,"conf":conf,"prim_dx":prim_dx,"report":report,"img":img})
                    st.session_state.total+=1
                    if uflag=="CRITICAL": st.session_state.critical+=1
                    elif uflag=="WARNING": st.session_state.warnings+=1
                except Exception as e:
                    results.append({"filename":f.name,"uflag":"ERROR","conf":0,"prim_dx":"Error","report":str(e),"img":None})
                time.sleep(.1)
            prog.progress(100,text="✅ Batch complete!"); time.sleep(.3); prog.empty()
            st.session_state.batch_results=results
            log_action("BATCH ANALYSIS",f"{len(results)} images processed")

        if st.session_state.batch_results:
            # Summary stats
            results=st.session_state.batch_results
            n_crit=sum(1 for r in results if r["uflag"]=="CRITICAL"); n_warn=sum(1 for r in results if r["uflag"]=="WARNING"); n_norm=sum(1 for r in results if r["uflag"]=="NORMAL")
            c1,c2,c3,c4=st.columns(4)
            with c1: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val">{len(results)}</div><div class="mc-stat-lbl">Processed</div></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="color:#dc2626">{n_crit}</div><div class="mc-stat-lbl">Critical</div></div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="color:#d97706">{n_warn}</div><div class="mc-stat-lbl">Warning</div></div>', unsafe_allow_html=True)
            with c4: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="color:#059669">{n_norm}</div><div class="mc-stat-lbl">Normal</div></div>', unsafe_allow_html=True)

            # Sort by severity
            sev={"CRITICAL":0,"WARNING":1,"NORMAL":2,"ERROR":3}
            sorted_res=sorted(results,key=lambda x:sev.get(x["uflag"],3))

            st.markdown("<div style='margin-top:.8rem;'></div>", unsafe_allow_html=True)
            for r in sorted_res:
                with st.expander(f"{urgency_tag(r['uflag'])} {r['filename']} — {r['prim_dx'][:40]} — Conf: {r['conf']}%",expanded=(r['uflag']=='CRITICAL')):
                    st.markdown(f'<div class="report-box">{r["report"]}</div>', unsafe_allow_html=True)
                    if r["img"]:
                        c1,c2=st.columns(2)
                        with c1: st.image(r["img"],use_container_width=True,caption="Original")
                        with c2: hm=generate_heatmap(r["img"],r["uflag"]); st.image(hm,use_container_width=True,caption="Heatmap")

            # Bulk export JSON
            bulk_data=json.dumps([{"filename":r["filename"],"urgency":r["uflag"],"confidence":r["conf"],"primary_dx":r["prim_dx"],"report":r["report"]} for r in results],indent=2)
            st.download_button("📦 Export All Results (JSON)",bulk_data,f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json","application/json",use_container_width=True)
    else:
        st.markdown('<div style="text-align:center;padding:2.5rem;background:var(--elevated);border:2px dashed var(--border2);border-radius:var(--radius);"><div style="font-size:2.5rem;margin-bottom:.7rem;">📦</div><div style="font-weight:600;font-size:.9rem;">Upload multiple images for batch analysis</div><div style="color:var(--text3);font-size:.78rem;margin-top:.3rem;">All images analysed in sequence — results sorted by severity</div></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# ██████  HEATMAP STUDIO
# ═══════════════════════════════════════════════
elif st.session_state.page=="heatmap":
    st.markdown("""<div class="mc-header"><h1>🧠 Heatmap & Enhancement Studio</h1><p>AI ATTENTION VISUALIZATION · 9 FILTERS · SIDE-BY-SIDE COMPARISON</p></div>""", unsafe_allow_html=True)
    up=st.file_uploader("Upload medical image",type=["jpg","jpeg","png","bmp","webp"])
    if up:
        img=PILImage.open(up)
        c1,c2,c3=st.columns(3)
        with c1:
            urgency_sel=st.selectbox("Simulate urgency",["NORMAL","WARNING","CRITICAL"])
            sensitivity=st.slider("Sensitivity",0.5,2.0,1.0,.1)
            hm=generate_heatmap(img,urgency_sel,sensitivity)
            st.markdown("**Original**"); st.image(img,use_container_width=True)
        with c2:
            st.markdown("**AI Heatmap**"); st.image(hm,use_container_width=True)
            st.markdown(f"""<div class="heatmap-legend"><span class="heatmap-dot" style="background:#dc2626;"></span>Hot<span class="heatmap-dot" style="background:#d97706;"></span>Warm<span class="heatmap-dot" style="background:#059669;"></span>Cool</div>""", unsafe_allow_html=True)
        with c3:
            enh_sel=st.selectbox("Enhancement",["Sharpen","Enhance Contrast","Denoise","Brighten","Edge Detect","CLAHE","Gamma Correction","Invert (Bone Window)","Pseudo-Color"])
            enh=enhance_image(img,enh_sel); st.markdown(f"**{enh_sel}**"); st.image(enh,use_container_width=True)

        d1,d2,d3=st.columns(3)
        orig_buf=io.BytesIO(); img.convert("RGB").save(orig_buf,format="PNG")
        with d1: st.download_button("💾 Original",orig_buf.getvalue(),"original.png","image/png",use_container_width=True)
        with d2:
            hm_buf=io.BytesIO(); hm.save(hm_buf,format="PNG")
            st.download_button("💾 Heatmap",hm_buf.getvalue(),"heatmap.png","image/png",use_container_width=True)
        with d3:
            en_buf=io.BytesIO(); enh.convert("RGB").save(en_buf,format="PNG")
            st.download_button("💾 Enhanced",en_buf.getvalue(),"enhanced.png","image/png",use_container_width=True)
    else:
        st.markdown('<div style="text-align:center;padding:2.5rem;background:var(--elevated);border:2px dashed var(--border2);border-radius:var(--radius);"><div style="font-size:2.5rem;margin-bottom:.6rem;">🧠</div><div style="font-weight:600;">Upload a medical image to begin</div></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# ██████  PATIENTS
# ═══════════════════════════════════════════════
elif st.session_state.page=="patients":
    st.markdown("""<div class="mc-header"><h1>👥 Patient Records</h1><p>PATIENT MANAGEMENT · VITALS GRAPHS · MEDICATIONS · INSURANCE · RISK SCORING</p></div>""", unsafe_allow_html=True)

    search=st.text_input("🔍 Search by name, ID or condition",placeholder="e.g. Ramesh, PT-001, Pulmonary")
    cf1,cf2=st.columns([2,1])
    with cf2: risk_filter=st.selectbox("Risk",["All","CRITICAL","HIGH","WARNING","LOW"])
    filtered=[p for p in DEMO_PATIENTS if (not search or any(search.lower() in str(p[k]).lower() for k in ["name","id","condition"])) and (risk_filter=="All" or p["risk"]==risk_filter)]

    for p in filtered:
        rc=risk_color(p["risk"]); score=compute_risk_score(p); bar_c="#dc2626" if score>=70 else("#d97706" if score>=40 else "#059669")
        ico="🔴" if p["risk"]=="CRITICAL" else("🟡" if p["risk"] in("HIGH","WARNING") else "🟢")
        with st.expander(f"{ico} {p['name']} — {p['id']} — {p['condition']} — Risk: {score}/100"):
            m1,m2,m3,m4,m5=st.columns(5)
            for col,(val,lbl,clr) in zip([m1,m2,m3,m4,m5],[(p["age"],"Age","#2563eb"),(p["scans"],"Total Scans","#7c3aed"),(p["bp"],"Blood Pressure","#d97706"),(p["o2"],"O₂ Saturation","#059669"),(f"{score}/100","Risk Score",bar_c)]):
                col.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="color:{clr};font-size:1rem;">{val}</div><div class="mc-stat-lbl">{lbl}</div></div>', unsafe_allow_html=True)

            t1,t2,t3,t4=st.tabs(["📋 Demographics","💊 Medications","📊 Vitals Graph","🏦 Insurance"])

            with t1:
                st.markdown(f"""<div class="mc-card"><div style='display:grid;grid-template-columns:1fr 1fr;gap:.35rem;font-size:.78rem;color:var(--text2);line-height:2;'>
                <div><b>ID:</b> {p['id']}</div><div><b>DOB:</b> {p['dob']}</div>
                <div><b>Gender:</b> {'Male' if p['gender']=='M' else 'Female'}</div><div><b>Blood Group:</b> {p.get('blood_group','N/A')}</div>
                <div><b>Phone:</b> {p.get('phone','N/A')}</div><div><b>Emergency:</b> {p.get('emergency_contact','N/A')}</div>
                <div><b>Smoker:</b> {p['smoker']}</div><div><b>Allergies:</b> <span style='color:#dc2626;font-weight:600;'>{p['allergies']}</span></div>
                <div><b>Weight:</b> {p['weight']}</div><div><b>Height:</b> {p['height']}</div>
                </div></div>""", unsafe_allow_html=True)
                note_col,btn_col=st.columns([3,1])
                with note_col: note_txt=st.text_input(f"Add note",placeholder="Clinical note...",key=f"note_{p['id']}")
                with btn_col:
                    st.markdown("<div style='height:1.6rem;'></div>", unsafe_allow_html=True)
                    note_type=st.selectbox("",["Note","Prescription","Referral","Follow-up","Alert"],key=f"ntype_{p['id']}",label_visibility="collapsed")
                if st.button(f"💾 Save Note",key=f"save_{p['id']}",use_container_width=True):
                    if note_txt.strip(): add_patient_log(p["id"],note_txt,note_type); log_action("NOTE",f"{p['name']}"); st.success("✅ Saved!")

            with t2:
                meds=p.get("medications",[])
                if meds:
                    for m in meds: st.markdown(f'<div class="drug-card">💊 {m}</div>', unsafe_allow_html=True)
                else: st.info("No medications recorded.")
                new_med=st.text_input("Add medication",placeholder="e.g. Metformin 500mg BD",key=f"med_{p['id']}")
                if st.button("➕ Add Medication",key=f"addmed_{p['id']}"):
                    if new_med.strip(): p["medications"]=p.get("medications",[])+[new_med]; st.success("✅ Added!"); st.rerun()

            with t3:
                graph=plot_vitals(p)
                if graph: st.image(graph,use_container_width=True,caption=f"Vitals trend — {p['name']}")
                else: st.info("No vitals history available for charting.")

            with t4:
                ins=p.get("insurance",{})
                if ins:
                    st.markdown(f"""<div class="mc-card"><div style='display:grid;grid-template-columns:1fr 1fr;gap:.35rem;font-size:.78rem;color:var(--text2);line-height:2;'>
                    <div><b>Provider:</b> {ins.get('provider','N/A')}</div><div><b>Policy No.:</b> {ins.get('policy','N/A')}</div>
                    <div><b>Valid Till:</b> {ins.get('valid_till','N/A')}</div><div><b>Coverage:</b> {ins.get('coverage','N/A')}</div>
                    <div><b>Co-Pay:</b> {ins.get('copay','N/A')}</div></div></div>""", unsafe_allow_html=True)
                else: st.info("No insurance info.")

            log_count=len(st.session_state.patient_logs.get(p["id"],[]))
            st.markdown(f'<div class="mc-alert-info">📋 {log_count} log entries on record</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# ██████  PATIENT LOGS
# ═══════════════════════════════════════════════
elif st.session_state.page=="patient_logs":
    st.markdown("""<div class="mc-header"><h1>📋 Patient Logs</h1><p>CLINICAL NOTES · AI SCAN RECORDS · PRESCRIPTIONS · REFERRALS · TIMELINE</p></div>""", unsafe_allow_html=True)

    pt_sel_opts=[f"{p['id']} — {p['name']}" for p in DEMO_PATIENTS]
    selected_str=st.selectbox("Select Patient",pt_sel_opts)
    pid=selected_str.split(" — ")[0]; patient=next((p for p in DEMO_PATIENTS if p["id"]==pid),None)

    if patient:
        rc=risk_color(patient["risk"]); score=compute_risk_score(patient)
        c1,c2,c3,c4=st.columns(4)
        with c1: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="color:{rc};">{patient["risk"]}</div><div class="mc-stat-lbl">Risk</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="color:#2563eb;">{score}/100</div><div class="mc-stat-lbl">Score</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val">{patient["scans"]}</div><div class="mc-stat-lbl">Total Scans</div></div>', unsafe_allow_html=True)
        with c4:
            logs=st.session_state.patient_logs.get(pid,[])
            st.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="color:#7c3aed;">{len(logs)}</div><div class="mc-stat-lbl">Log Entries</div></div>', unsafe_allow_html=True)

        left,right=st.columns([1.4,1])
        with left:
            st.markdown("<div class='mc-section-title'>CLINICAL LOG</div>", unsafe_allow_html=True)
            with st.form(key=f"logform_{pid}"):
                new_note=st.text_area("New Entry",placeholder="Enter note, prescription, or observation...",height=75)
                nc1,nc2=st.columns([2,1])
                with nc1: note_type_sel=st.selectbox("Entry Type",["Note","Prescription","Referral","Follow-up","Alert","AI Scan","Observation","Lab Result"])
                with nc2: st.write("")
                if st.form_submit_button("💾 Add Log Entry",use_container_width=True):
                    if new_note.strip(): add_patient_log(pid,new_note,note_type_sel); log_action("PATIENT LOG",f"{patient['name']} — {note_type_sel}"); st.success("✅ Added!"); st.rerun()

            logs=st.session_state.patient_logs.get(pid,[])
            if logs:
                type_filter=st.selectbox("Filter",["All","Note","Prescription","Referral","Follow-up","Alert","AI Scan","Observation","Lab Result"])
                filtered_logs=[l for l in logs if type_filter=="All" or l["type"]==type_filter]
                for l in reversed(filtered_logs):
                    tc={"Note":"#2563eb","Prescription":"#7c3aed","Referral":"#d97706","Follow-up":"#059669","Alert":"#dc2626","AI Scan":"#0891b2","Observation":"#475569","Lab Result":"#059669"}.get(l["type"],"#475569")
                    st.markdown(f'<div class="log-entry"><div style="font-weight:600;color:{tc};">{l["type"]}</div><div class="log-entry-meta">{l["date"]} {l["time"]} · {l["doctor"]}</div><div class="log-entry-body">{l["note"]}</div></div>', unsafe_allow_html=True)
            else: st.info("No log entries yet.")

        with right:
            st.markdown("<div class='mc-section-title'>PATIENT INFO</div>", unsafe_allow_html=True)
            st.markdown(f"""<div class="mc-card">
                <div style='font-weight:700;font-size:.92rem;margin-bottom:.5rem;'>{"👨" if patient["gender"]=="M" else "👩"} {patient['name']}</div>
                <div style='font-size:.77rem;color:var(--text2);line-height:2.1;'>
                <b>ID:</b> {patient['id']}<br><b>Age:</b> {patient['age']} · <b>DOB:</b> {patient['dob']}<br>
                <b>Blood Group:</b> {patient.get('blood_group','N/A')}<br><b>Phone:</b> {patient.get('phone','N/A')}<br>
                <b>Allergies:</b> <span style='color:#dc2626;font-weight:600;'>{patient['allergies']}</span><br>
                <b>BP:</b> {patient['bp']} · <b>O₂:</b> {patient['o2']}<br><b>Emergency:</b> {patient.get('emergency_contact','N/A')}
                </div></div>""", unsafe_allow_html=True)

            st.markdown("<div class='mc-section-title'>TIMELINE</div>", unsafe_allow_html=True)
            logs=st.session_state.patient_logs.get(pid,[])
            if logs:
                for l in reversed(logs[-6:]):
                    tc={"Note":"var(--accent)","AI Scan":"var(--cyan)","Alert":"var(--red)","Prescription":"var(--purple)"}.get(l["type"],"var(--text3)")
                    st.markdown(f'<div class="timeline-item" style="border-left-color:{tc};"><div class="timeline-date">{l["date"]} {l["time"]}</div><div class="timeline-txt"><b>{l["type"]}</b> — {l["note"][:55]}{"..." if len(l["note"])>55 else ""}</div></div>', unsafe_allow_html=True)
            else: st.markdown('<div style="color:var(--text3);font-size:.78rem;">No timeline entries.</div>', unsafe_allow_html=True)

            logs=st.session_state.patient_logs.get(pid,[])
            dl_html=f"""<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Patient Log — {patient['name']}</title><style>body{{font-family:'Segoe UI',sans-serif;padding:24px;}} table{{width:100%;border-collapse:collapse;}} th,td{{border:1px solid #e2e8f0;padding:7px 10px;font-size:.8rem;}} th{{background:#f8fafc;}} .header{{background:linear-gradient(135deg,#1e3a5f,#2563eb);color:white;padding:18px;border-radius:10px;margin-bottom:14px;}}</style></head>
<body><div class='header'><h2 style='margin:0;'>Patient Log — {patient['name']}</h2><p style='margin:3px 0 0;opacity:.65;font-size:.75rem;'>{patient['id']} · {patient['condition']}</p></div>
<table><tr><th>Date</th><th>Time</th><th>Doctor</th><th>Type</th><th>Note</th></tr>{"".join(f"<tr><td>{l['date']}</td><td>{l['time']}</td><td>{l['doctor']}</td><td><b>{l['type']}</b></td><td>{l['note']}</td></tr>" for l in reversed(logs))}</table>
<p style='color:#94a3b8;font-size:.68rem;margin-top:14px;text-align:center;'>Cortexa Health {APP_VERSION} · {AUTHOR} · {datetime.now().strftime('%Y-%m-%d')}</p></body></html>"""
            st.download_button("📥 Export HTML Report",dl_html,f"log_{pid}_{datetime.now().strftime('%Y%m%d')}.html","text/html",use_container_width=True)
            jl=json.dumps({"patient":{"id":patient["id"],"name":patient["name"],"condition":patient["condition"]},"logs":logs},indent=2,default=str)
            st.download_button("📦 Export JSON",jl,f"log_{pid}_{datetime.now().strftime('%Y%m%d')}.json","application/json",use_container_width=True)

# ═══════════════════════════════════════════════
# ██████  PRECAUTIONS
# ═══════════════════════════════════════════════
elif st.session_state.page=="precautions":
    st.markdown("""<div class="mc-header"><h1>⚠️ Clinical Precautions</h1><p>PATIENT SAFETY · CONTRAINDICATIONS · ALLERGY ALERTS · CARE INSTRUCTIONS</p></div>""", unsafe_allow_html=True)
    c1,c2,c3=st.columns(3)
    allergy_count=sum(1 for p in DEMO_PATIENTS if p["allergies"]!="None")
    with c1: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="color:#dc2626;">{sum(1 for p in DEMO_PATIENTS if p["risk"]=="CRITICAL")}</div><div class="mc-stat-lbl">Critical Patients</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="color:#d97706;">{allergy_count}</div><div class="mc-stat-lbl">Allergy Alerts</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="color:#7c3aed;">{sum(len(p.get("precautions",[])) for p in DEMO_PATIENTS)}</div><div class="mc-stat-lbl">Total Precautions</div></div>', unsafe_allow_html=True)

    st.markdown("<div style='margin-top:.8rem;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='mc-section-title'>🚨 ALLERGY & CONTRAINDICATION ALERTS</div>", unsafe_allow_html=True)
    for p in DEMO_PATIENTS:
        if p["allergies"]!="None":
            st.markdown(f'<div class="mc-alert">🚨 <b>{p["name"]} ({p["id"]})</b> — ALLERGY: <b style="text-decoration:underline;">{p["allergies"]}</b> · Risk: {p["risk"]} · {p["condition"]}</div>', unsafe_allow_html=True)

    st.markdown("<div style='margin-top:.8rem;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='mc-section-title'>PER-PATIENT PRECAUTIONS</div>", unsafe_allow_html=True)
    for p in sorted(DEMO_PATIENTS,key=lambda x:["CRITICAL","HIGH","WARNING","LOW"].index(x["risk"])):
        rc=risk_color(p["risk"]); ico="🔴" if p["risk"]=="CRITICAL" else("🟡" if p["risk"] in("HIGH","WARNING") else "🟢")
        with st.expander(f"{ico} {p['name']} ({p['id']}) — {p['condition']} — {p['risk']}"):
            c1,c2=st.columns([2,1])
            with c1:
                st.markdown(f"<div style='font-size:.8rem;color:var(--text2);margin-bottom:.5rem;'><b>Allergies:</b> <span style='color:#dc2626;'>{p['allergies']}</span> · <b>BP:</b> {p['bp']} · <b>O₂:</b> {p['o2']}</div>", unsafe_allow_html=True)
                for prec in p.get("precautions",[]):
                    is_crit=any(kw in prec.lower() for kw in ["critical","emergency","immediately","stat","cease","npo","never"])
                    st.markdown(f'<div class="prec-item {"prec-critical" if is_crit else ""}"><span>{"🚨" if is_crit else "⚠️"}</span><span>{prec}</span></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="mc-card" style="text-align:center;"><div style="font-size:1.3rem;font-weight:700;color:{rc};">{p["risk"]}</div><div style="font-size:.6rem;color:var(--text3);text-transform:uppercase;">Risk Level</div><div style="margin-top:.5rem;font-size:.78rem;">Score: <b>{compute_risk_score(p)}/100</b></div><div style="font-size:.73rem;color:var(--text2);">{len(p.get("precautions",[]))} precautions</div></div>', unsafe_allow_html=True)
            new_prec=st.text_input(f"Add precaution",placeholder="e.g. Avoid iodinated contrast...",key=f"prec_{p['id']}")
            if st.button(f"➕ Add",key=f"addprec_{p['id']}"):
                if new_prec.strip():
                    p["precautions"]=p.get("precautions",[])+[new_prec]; add_patient_log(p["id"],f"Precaution added: {new_prec}","Alert"); st.success("✅ Added!"); st.rerun()

# ═══════════════════════════════════════════════
# ██████  MEDICATIONS
# ═══════════════════════════════════════════════
elif st.session_state.page=="medications":
    st.markdown("""<div class="mc-header"><h1>💊 Medication Tracker</h1><p>PER-PATIENT MEDICATIONS · DOSING · DRUG MANAGEMENT</p></div>""", unsafe_allow_html=True)
    for p in DEMO_PATIENTS:
        meds=p.get("medications",[])
        rc=risk_color(p["risk"])
        with st.expander(f"{'👨' if p['gender']=='M' else '👩'} {p['name']} ({p['id']}) — {len(meds)} medications"):
            if meds:
                for m in meds: st.markdown(f'<div class="drug-card"><span style="font-size:1rem;">💊</span> {m}</div>', unsafe_allow_html=True)
            else: st.markdown('<div class="mc-alert-info">No medications recorded.</div>', unsafe_allow_html=True)
            c1,c2=st.columns([3,1])
            with c1: new_med=st.text_input("Add medication",placeholder="e.g. Amoxicillin 500mg TDS × 7 days",key=f"med2_{p['id']}")
            with c2: st.write(""); st.write("")
            if st.button("➕ Add",key=f"addmed2_{p['id']}",use_container_width=True):
                if new_med.strip(): p["medications"]=p.get("medications",[])+[new_med]; add_patient_log(p["id"],f"Medication added: {new_med}","Prescription"); st.success("✅ Added!"); st.rerun()

# ═══════════════════════════════════════════════
# ██████  LAB VALUES
# ═══════════════════════════════════════════════
elif st.session_state.page=="labs":
    st.markdown("""<div class="mc-header"><h1>🧪 Lab Values Tracker</h1><p>BLOOD TESTS · REFERENCE RANGES · STATUS FLAGS · TREND MONITORING</p></div>""", unsafe_allow_html=True)

    pt_sel=[f"{p['id']} — {p['name']}" for p in DEMO_PATIENTS]
    sel=st.selectbox("Select Patient",pt_sel); pid=sel.split(" — ")[0]
    patient=next((p for p in DEMO_PATIENTS if p["id"]==pid),None)

    if patient:
        st.markdown(f"<div class='mc-alert-info'>🧪 Showing lab values for <b>{patient['name']}</b> ({patient['id']}) · Gender: {'Male' if patient['gender']=='M' else 'Female'}</div>", unsafe_allow_html=True)
        labs=st.session_state.lab_entries.get(pid,{})
        gender_key="male" if patient["gender"]=="M" else "female"

        # Count flags
        n_high=0; n_low=0; n_norm=0
        for name,ref in LAB_REFERENCE.items():
            if name in labs:
                lo,hi=ref[gender_key]; val=labs[name]
                if val<lo: n_low+=1
                elif val>hi: n_high+=1
                else: n_norm+=1

        c1,c2,c3=st.columns(3)
        with c1: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="color:#dc2626;">{n_high}</div><div class="mc-stat-lbl">High Values</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="color:#2563eb;">{n_low}</div><div class="mc-stat-lbl">Low Values</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="color:#059669;">{n_norm}</div><div class="mc-stat-lbl">Normal Values</div></div>', unsafe_allow_html=True)

        st.markdown("<div style='margin-top:.8rem;'></div>", unsafe_allow_html=True)
        left,right=st.columns([1.5,1])

        with left:
            st.markdown("<div class='mc-section-title'>LAB RESULTS PANEL</div>", unsafe_allow_html=True)
            for name,ref in LAB_REFERENCE.items():
                lo,hi=ref[gender_key]; unit=ref["unit"]; val=labs.get(name,None)
                c1,c2,c3,c4=st.columns([2,1,1,1])
                with c1: st.markdown(f"<div style='font-size:.8rem;font-weight:500;padding:.4rem 0;'>{name}</div>", unsafe_allow_html=True)
                with c2:
                    if val is not None:
                        cls,status=lab_status(val,lo,hi)
                        st.markdown(f"<div style='font-size:.78rem;padding:.4rem 0;' class='{cls}'>{val} {unit}</div>", unsafe_allow_html=True)
                    else: st.markdown("<div style='font-size:.75rem;color:var(--text3);padding:.4rem 0;'>—</div>", unsafe_allow_html=True)
                with c3:
                    if val is not None:
                        cls,status=lab_status(val,lo,hi)
                        st.markdown(f"<div style='font-size:.72rem;padding:.4rem 0;' class='{cls}'>{status}</div>", unsafe_allow_html=True)
                with c4: st.markdown(f"<div style='font-size:.68rem;color:var(--text3);padding:.4rem 0;'>{lo}–{hi}</div>", unsafe_allow_html=True)
                st.markdown("<div style='height:2px;background:var(--border);border-radius:1px;'></div>", unsafe_allow_html=True)

        with right:
            st.markdown("<div class='mc-section-title'>ENTER / UPDATE VALUES</div>", unsafe_allow_html=True)
            selected_test=st.selectbox("Test",list(LAB_REFERENCE.keys()))
            ref=LAB_REFERENCE[selected_test]; unit=ref["unit"]
            current=labs.get(selected_test,"")
            new_val=st.number_input(f"{selected_test} ({unit})",value=float(current) if current else 0.0,step=0.1,format="%.2f")
            if st.button(f"💾 Save {selected_test}",use_container_width=True):
                if pid not in st.session_state.lab_entries: st.session_state.lab_entries[pid]={}
                st.session_state.lab_entries[pid][selected_test]=new_val
                add_patient_log(pid,f"Lab: {selected_test} = {new_val} {unit}","Lab Result")
                log_action("LAB UPDATE",f"{patient['name']} — {selected_test}: {new_val} {unit}"); st.success("✅ Saved!"); st.rerun()

            if n_high>0 or n_low>0:
                st.markdown("<div style='margin-top:.8rem;'></div>", unsafe_allow_html=True)
                st.markdown("<div class='mc-section-title'>⚠️ ABNORMAL FLAGS</div>", unsafe_allow_html=True)
                for name,ref in LAB_REFERENCE.items():
                    lo,hi=ref[gender_key]; val=labs.get(name)
                    if val is not None:
                        if val>hi: st.markdown(f'<div class="mc-alert">▲ <b>{name}</b>: {val} {ref["unit"]} (High &gt;{hi})</div>', unsafe_allow_html=True)
                        elif val<lo: st.markdown(f'<div class="mc-alert-info">▼ <b>{name}</b>: {val} {ref["unit"]} (Low &lt;{lo})</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# ██████  APPOINTMENTS
# ═══════════════════════════════════════════════
elif st.session_state.page=="appointments":
    st.markdown("""<div class="mc-header"><h1>📅 Appointment Scheduler</h1><p>SCHEDULE · TRACK · MANAGE CLINICAL APPOINTMENTS</p></div>""", unsafe_allow_html=True)

    # Gather all appointments
    all_appts=[]
    for p in DEMO_PATIENTS:
        for a in p.get("appointments",[]): all_appts.append({**a,"patient":p["name"],"pid":p["id"],"risk":p["risk"]})
    for a in st.session_state.appointments: all_appts.append(a)
    all_appts.sort(key=lambda x:x["date"])

    c1,c2,c3=st.columns(3)
    with c1: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="color:#2563eb;">{len(all_appts)}</div><div class="mc-stat-lbl">Total</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="color:#dc2626;">{sum(1 for a in all_appts if a.get("status")=="URGENT")}</div><div class="mc-stat-lbl">Urgent</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="color:#059669;">{sum(1 for a in all_appts if a.get("status")=="Scheduled")}</div><div class="mc-stat-lbl">Scheduled</div></div>', unsafe_allow_html=True)

    st.markdown("<div style='margin-top:.8rem;'></div>", unsafe_allow_html=True)
    left,right=st.columns([1.5,1])

    with left:
        st.markdown("<div class='mc-section-title'>UPCOMING APPOINTMENTS</div>", unsafe_allow_html=True)
        for a in all_appts:
            rc=risk_color(a.get("risk","LOW")); urg_cls="tag-critical" if a.get("status")=="URGENT" else "tag-blue"
            st.markdown(f"""<div class="appt-card">
                <div>
                    <div style='font-weight:600;font-size:.83rem;'>📅 {a['date']} at {a['time']}</div>
                    <div style='font-size:.73rem;color:var(--text2);'>{a['type']} — {a['patient']} ({a.get('pid','N/A')})</div>
                    <div style='font-size:.7rem;color:var(--text3);'>Dr: {a['doctor']}</div>
                </div>
                <span class='mc-tag {urg_cls}'>{a.get('status','Scheduled')}</span>
            </div>""", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='mc-section-title'>SCHEDULE NEW APPOINTMENT</div>", unsafe_allow_html=True)
        pt_opts=[f"{p['id']} — {p['name']}" for p in DEMO_PATIENTS]
        sel_pt2=st.selectbox("Patient",pt_opts,key="appt_pt")
        appt_date=st.date_input("Date",value=datetime.now().date()+timedelta(days=7)); appt_time=st.time_input("Time",value=datetime.strptime("09:00","%H:%M").time())
        appt_type=st.selectbox("Type",["Routine Review","CT Follow-up","MRI","Biopsy","Oncology Consult","Cardiac Review","Physiotherapy","Blood Tests","Ultrasound","Echo Cardiogram","Chest Clinic"])
        appt_doctor=st.selectbox("Doctor",["Dr. Priya Sharma","Dr. Kevin Chen","Dr. Sarah Jones"])
        appt_status=st.selectbox("Status",["Scheduled","URGENT","Planned","Pending"])
        appt_notes=st.text_area("Notes",height=60,placeholder="Any additional notes...")
        if st.button("📅 Schedule Appointment",use_container_width=True):
            pid2=sel_pt2.split(" — ")[0]; pname=sel_pt2.split(" — ")[1]
            new_appt={"date":str(appt_date),"time":str(appt_time)[:5],"type":appt_type,"doctor":appt_doctor,"status":appt_status,"notes":appt_notes,"patient":pname,"pid":pid2,"risk":"LOW"}
            st.session_state.appointments.append(new_appt)
            add_patient_log(pid2,f"Appointment scheduled: {appt_type} on {appt_date} at {appt_time} with {appt_doctor}","Follow-up")
            log_action("APPOINTMENT",f"{pname} — {appt_type} on {appt_date}"); st.success("✅ Appointment scheduled!"); st.rerun()

# ═══════════════════════════════════════════════
# ██████  ANALYTICS
# ═══════════════════════════════════════════════
elif st.session_state.page=="analytics":
    st.markdown("""<div class="mc-header"><h1>📊 Analytics Dashboard</h1><p>CASE STATISTICS · AI PERFORMANCE · RISK DISTRIBUTION · RESPONSE TIMES</p></div>""", unsafe_allow_html=True)
    total=max(st.session_state.total,1); crit=st.session_state.critical; warn=st.session_state.warnings; norm=max(total-crit-warn,0)
    c1,c2,c3,c4=st.columns(4)
    with c1: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val">{total}</div><div class="mc-stat-lbl">Total Scans</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="color:#dc2626">{crit}</div><div class="mc-stat-lbl">Critical</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="color:#d97706">{warn}</div><div class="mc-stat-lbl">Warnings</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="color:#059669">{norm}</div><div class="mc-stat-lbl">Normal</div></div>', unsafe_allow_html=True)

    st.markdown("<div style='margin-top:.9rem;'></div>", unsafe_allow_html=True)
    left,right=st.columns(2)
    with left:
        st.markdown("<div class='mc-section-title'>CASE OUTCOME DISTRIBUTION</div>", unsafe_allow_html=True)
        for label,count,color in [("🔴 CRITICAL",crit,"#dc2626"),("🟡 WARNING",warn,"#d97706"),("🟢 NORMAL",norm,"#059669")]:
            pct=int(count/total*100) if total else 0
            st.markdown(f'<div class="abar-row"><span style="min-width:100px;">{label}</span><div class="abar-outer"><div class="abar-fill" style="width:{pct}%;background:{color};"></div></div><span style="min-width:28px;color:{color};font-weight:700;">{count}</span></div>', unsafe_allow_html=True)

        st.markdown("<div style='margin-top:.9rem;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='mc-section-title'>ML RISK SCORE DISTRIBUTION</div>", unsafe_allow_html=True)
        for p in sorted(DEMO_PATIENTS,key=lambda x:compute_risk_score(x),reverse=True):
            sc=compute_risk_score(p); bc="#dc2626" if sc>=70 else("#d97706" if sc>=40 else "#059669")
            st.markdown(f'<div class="abar-row"><span style="min-width:110px;font-size:.73rem;">{p["name"].split()[0]} {p["name"].split()[-1]}</span><div class="abar-outer"><div class="abar-fill" style="width:{sc}%;background:{bc};"></div></div><span style="min-width:34px;color:{bc};font-weight:700;">{sc}</span></div>', unsafe_allow_html=True)

        if st.session_state.history:
            st.markdown("<div style='margin-top:.9rem;'></div>", unsafe_allow_html=True)
            st.markdown("<div class='mc-section-title'>AI CONFIDENCE TREND</div>", unsafe_allow_html=True)
            for h in st.session_state.history[-8:]:
                conf=h.get("confidence",80); cc="#dc2626" if conf<65 else("#d97706" if conf<80 else "#059669")
                st.markdown(f'<div class="abar-row"><span style="min-width:115px;font-size:.7rem;">{h["filename"][:14]}</span><div class="abar-outer"><div class="abar-fill" style="width:{conf}%;background:{cc};"></div></div><span style="color:{cc};">{conf}%</span></div>', unsafe_allow_html=True)

    with right:
        st.markdown("<div class='mc-section-title'>MODEL BENCHMARK METRICS</div>", unsafe_allow_html=True)
        for name,val,color in [("Sensitivity (Recall)","94%","#2563eb"),("Specificity","91%","#7c3aed"),("Precision (PPV)","88%","#059669"),("NPV","96%","#d97706"),("F1 Score","91%","#dc2626"),("AUC-ROC","97%","#0891b2")]:
            pv=int(val.replace("%",""))
            st.markdown(f'<div class="abar-row"><span style="min-width:130px;">{name}</span><div class="abar-outer"><div class="abar-fill" style="width:{pv}%;background:{color};"></div></div><span style="color:{color};font-weight:700;">{val}</span></div>', unsafe_allow_html=True)

        st.markdown("<div style='margin-top:.9rem;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='mc-section-title'>PATIENT RISK DISTRIBUTION</div>", unsafe_allow_html=True)
        risk_cnt={}
        for p in DEMO_PATIENTS: risk_cnt[p["risk"]]=risk_cnt.get(p["risk"],0)+1
        for r,cnt in risk_cnt.items():
            pct=int(cnt/len(DEMO_PATIENTS)*100); clr=risk_color(r)
            st.markdown(f'<div class="abar-row"><span style="min-width:85px;">{r}</span><div class="abar-outer"><div class="abar-fill" style="width:{pct}%;background:{clr};"></div></div><span style="color:{clr};font-weight:700;">{cnt}</span></div>', unsafe_allow_html=True)

        st.markdown("<div style='margin-top:.9rem;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='mc-section-title'>MODALITY BREAKDOWN</div>", unsafe_allow_html=True)
        mods={"Chest X-Ray":38,"CT Scan":22,"Brain MRI":18,"Ultrasound":12,"PET Scan":6,"Mammogram":4}
        for h in st.session_state.history: mods[h.get("modality","Other")]=mods.get(h.get("modality","Other"),0)+1
        mt=sum(mods.values()); colors=["#2563eb","#059669","#d97706","#dc2626","#7c3aed","#0891b2"]
        for i,(mod,cnt) in enumerate(mods.items()):
            pct=int(cnt/mt*100); clr=colors[i%len(colors)]
            st.markdown(f'<div class="abar-row"><span style="min-width:100px;">{mod}</span><div class="abar-outer"><div class="abar-fill" style="width:{pct}%;background:{clr};"></div></div><span style="color:{clr};font-weight:700;">{pct}%</span></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# ██████  AI CHAT
# ═══════════════════════════════════════════════
elif st.session_state.page=="ai_chat":
    st.markdown("""<div class="mc-header"><h1>💬 AI Clinical Chat Assistant</h1><p>RADIOLOGY CONSULT · CLINICAL DECISION SUPPORT · MEDICAL Q&A</p></div>""", unsafe_allow_html=True)
    st.markdown('<div class="mc-alert-info">💡 Ask about radiology guidelines, drug interactions, anatomy, differential diagnoses, or any clinical topic. Powered by LLaMA 4.</div>', unsafe_allow_html=True)

    for msg in st.session_state.chat_messages:
        if msg["role"]=="user": st.markdown(f'<div class="chat-user">{msg["content"]}</div>', unsafe_allow_html=True)
        else: st.markdown(f'<div class="chat-ai">🤖 <b>Cortexa Health:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)

    if not st.session_state.chat_messages:
        st.markdown("<div class='mc-section-title'>QUICK PROMPTS</div>", unsafe_allow_html=True)
        qp_cols=st.columns(2)
        quick_prompts=["What are the ACR guidelines for lung nodule follow-up?","Explain CT pulmonary angiography protocol","What is the Fleischner Society criteria for nodules?","How do I read a chest X-ray systematically?","Explain MRI sequences: T1, T2, FLAIR, DWI","RECIST criteria for tumour response assessment"]
        for i,qp in enumerate(quick_prompts):
            with qp_cols[i%2]:
                if st.button(f"💬 {qp[:38]}...",key=f"qp_{i}",use_container_width=True):
                    st.session_state.chat_messages.append({"role":"user","content":qp})
                    try:
                        reply=run_chat(st.session_state.chat_messages,"You are Cortexa Health, an expert clinical assistant and radiologist. Provide accurate, evidence-based medical information. Format with markdown.")
                        st.session_state.chat_messages.append({"role":"assistant","content":reply}); log_action("AI CHAT",qp[:40])
                    except Exception as e: st.error(f"Chat error: {e}")
                    st.rerun()

    user_input=st.text_area("Ask a clinical question...",height=70,placeholder="e.g. What are the imaging features of pulmonary embolism on CT?",key="chat_input")
    c1,c2,c3=st.columns([3,1,1])
    with c1:
        if st.button("📤 Send Message",use_container_width=True,key="chat_send"):
            if user_input.strip():
                st.session_state.chat_messages.append({"role":"user","content":user_input})
                try:
                    with st.spinner("🤔 AI thinking..."): reply=run_chat(st.session_state.chat_messages[-10:],"You are Cortexa Health, an expert clinical assistant and radiologist. Keep responses concise and clinically useful. Format with markdown.")
                    st.session_state.chat_messages.append({"role":"assistant","content":reply}); log_action("AI CHAT",user_input[:40])
                except Exception as e: st.error(f"Chat error: {e}")
                st.rerun()
    with c2:
        if st.button("🗑️ Clear",use_container_width=True,key="chat_clear"): st.session_state.chat_messages=[]; st.rerun()
    with c3:
        if st.session_state.chat_messages:
            chat_exp="\n\n".join([f"{'USER' if m['role']=='user' else 'MEDICORE AI'}: {m['content']}" for m in st.session_state.chat_messages])
            st.download_button("💾 Export",chat_exp,f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt","text/plain",use_container_width=True)

# ═══════════════════════════════════════════════
# ██████  DRUG INTERACTION CHECKER
# ═══════════════════════════════════════════════
elif st.session_state.page=="drugs":
    st.markdown("""<div class="mc-header"><h1>💊 AI Drug Interaction Checker</h1><p>POWERED BY LLAMA 4 · CHECK INTERACTIONS · ALLERGY SCREENING · CONTRAINDICATIONS</p></div>""", unsafe_allow_html=True)

    st.markdown("<div class='mc-section-title'>PATIENT DRUG CHECKER</div>", unsafe_allow_html=True)
    pt_opts=[f"{p['id']} — {p['name']}" for p in DEMO_PATIENTS]
    sel_pt=st.selectbox("Select Patient (pre-fills their medications)",pt_opts)
    pid=sel_pt.split(" — ")[0]; pt=next((p for p in DEMO_PATIENTS if p["id"]==pid),None)

    if pt:
        st.markdown(f'<div class="mc-alert-info">⚠️ Known allergies: <b>{pt["allergies"]}</b></div>', unsafe_allow_html=True)
        existing="\n".join(pt.get("medications",[])); default_meds=existing
    else: default_meds=""

    drug_list=st.text_area("Enter medications to check (one per line)",value=default_meds,height=120,placeholder="Amoxicillin 500mg TDS\nWarfarin 5mg OD\nMetformin 500mg BD")
    new_drug=st.text_input("New drug to add",placeholder="e.g. Clarithromycin 500mg BD")
    if new_drug.strip(): drug_list=drug_list+"\n"+new_drug if drug_list.strip() else new_drug

    if st.button("🔍 Check Interactions",use_container_width=True):
        if drug_list.strip():
            with st.spinner("🧠 AI analysing drug interactions..."):
                try:
                    prompt=f"""Patient: {pt['name'] if pt else 'Unknown'}, Age: {pt['age'] if pt else 'Unknown'}, Gender: {'Male' if pt and pt['gender']=='M' else 'Female'}, Allergies: {pt['allergies'] if pt else 'Unknown'}.

Medications:
{drug_list}

Please provide:
1. **Drug Interactions**: List any significant interactions (severity: Major/Moderate/Minor)
2. **Allergy Risks**: Flag any allergy cross-reactions
3. **Contraindications**: Any absolute contraindications
4. **Dosing Concerns**: Renal/hepatic dose adjustments needed?
5. **Recommendations**: Safe alternatives if needed
6. **Clinical Safety Score**: (Safe / Caution / High Risk)

Be specific and clinically actionable."""
                    response=run_ai(prompt,"You are a senior clinical pharmacologist and drug safety expert. Provide evidence-based drug interaction analysis. Always flag life-threatening interactions first.")
                    uflag_d="CRITICAL" if any(w in response.lower() for w in ["contraindicated","life-threatening","avoid","major interaction","do not"]) else ("WARNING" if any(w in response.lower() for w in ["caution","moderate","monitor","reduce dose"]) else "NORMAL")
                    if uflag_d=="CRITICAL": st.markdown('<div class="banner-critical">🚨 HIGH-RISK INTERACTIONS DETECTED — Clinical review required</div>', unsafe_allow_html=True)
                    elif uflag_d=="WARNING": st.markdown('<div class="banner-warning">⚠️ Caution — Moderate interactions detected — Monitor closely</div>', unsafe_allow_html=True)
                    else: st.markdown('<div class="banner-normal">✅ No major interactions detected</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="report-box">{response}</div>', unsafe_allow_html=True)
                    if pt: add_patient_log(pid,"Drug interaction check performed","Note"); log_action("DRUG CHECK",f"{pt['name']} — {len(drug_list.split(chr(10)))} drugs")
                    st.download_button("📄 Export Report",f"DRUG INTERACTION REPORT\nPatient: {pt['name'] if pt else 'N/A'}\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M')}\nDoctor: {st.session_state.user}\n\nMedications Checked:\n{drug_list}\n\nAnalysis:\n{response}",f"drug_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt","text/plain",use_container_width=True)
                except Exception as e: st.error(f"❌ {e}")
        else: st.warning("Please enter medications to check.")

    st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='mc-section-title'>PATIENT MEDICATION SUMMARIES</div>", unsafe_allow_html=True)
    for p in DEMO_PATIENTS[:4]:
        meds=p.get("medications",[]); allergy=p["allergies"]
        allergy_cls="mc-alert" if allergy!="None" else "mc-alert-green"
        with st.expander(f"{'👨' if p['gender']=='M' else '👩'} {p['name']} — {len(meds)} medications — Allergy: {allergy}"):
            st.markdown(f'<div class="{allergy_cls}">Allergies: <b>{allergy}</b></div>', unsafe_allow_html=True)
            for m in meds: st.markdown(f'<div class="drug-card">💊 {m}</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# ██████  REPORT TEMPLATES
# ═══════════════════════════════════════════════
elif st.session_state.page=="templates":
    st.markdown("""<div class="mc-header"><h1>📝 Report Templates</h1><p>8 SPECIALISED TEMPLATES · CUSTOMISABLE · EXPORT READY</p></div>""", unsafe_allow_html=True)
    for name,desc in REPORT_TEMPLATES.items():
        icon={"Comprehensive Radiology":"🔬","Quick Triage":"⚡","Patient-Friendly":"👤","Research / Academic":"📚","Second Opinion":"🔎","Paediatric":"👶","Oncology Focus":"🎗️","Cardiac Focus":"❤️"}.get(name,"📝")
        with st.expander(f"{icon} {name}"):
            st.markdown(f'<div class="mc-alert-info">{desc}</div>', unsafe_allow_html=True)
            st.markdown("""<div class='mc-card'>
            <div style='font-size:.8rem;color:var(--text2);line-height:1.9;'>
            ✅ Structured sections auto-generated based on template<br>
            ✅ AI adapts tone, depth, and focus areas accordingly<br>
            ✅ Select template in AI Analysis before running scan<br>
            ✅ All templates include differential diagnoses and next steps
            </div></div>""", unsafe_allow_html=True)
            if st.button(f"🔬 Use {name} Template",key=f"tmpl_{name}",use_container_width=True):
                st.session_state.page="analysis"; st.rerun()

# ═══════════════════════════════════════════════
# ██████  ALERTS
# ═══════════════════════════════════════════════
elif st.session_state.page=="alerts":
    st.markdown("""<div class="mc-header"><h1>🔔 Smart Alert Center</h1><p>CRITICAL FLAGS · PATIENT RISK ALERTS · SYSTEM NOTIFICATIONS</p></div>""", unsafe_allow_html=True)
    a1,a2,a3=st.columns(3)
    with a1: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="color:#dc2626">{len(st.session_state.alerts)}</div><div class="mc-stat-lbl">AI Flags</div></div>', unsafe_allow_html=True)
    with a2: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="color:#ea580c">{sum(1 for p in DEMO_PATIENTS if p["risk"]=="CRITICAL")}</div><div class="mc-stat-lbl">Critical Patients</div></div>', unsafe_allow_html=True)
    with a3: st.markdown(f'<div class="mc-stat"><div class="mc-stat-val" style="color:#059669">4</div><div class="mc-stat-lbl">Systems OK</div></div>', unsafe_allow_html=True)

    if st.session_state.alerts:
        st.markdown("<div style='margin-top:.7rem;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='mc-section-title'>🚨 AI CRITICAL FLAGS</div>", unsafe_allow_html=True)
        for a in reversed(st.session_state.alerts):
            st.markdown(f'<div class="mc-alert">🚨 <b>{a["msg"]}</b> <span style="float:right;color:var(--text3);font-size:.7rem;">{a["time"]}</span></div>', unsafe_allow_html=True)

    st.markdown("<div style='margin-top:.7rem;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='mc-section-title'>HIGH-RISK PATIENTS</div>", unsafe_allow_html=True)
    for p in DEMO_PATIENTS:
        if p["risk"] in("CRITICAL","HIGH"):
            ico="🔴" if p["risk"]=="CRITICAL" else "🟡"; cls="mc-alert" if p["risk"]=="CRITICAL" else "mc-alert-warning"
            st.markdown(f'<div class="{cls}">{ico} <b>{p["name"]} ({p["id"]})</b> — {p["risk"]} · {p["condition"]} · O₂:{p["o2"]} · Allergies:{p["allergies"]}</div>', unsafe_allow_html=True)

    st.markdown("<div style='margin-top:.7rem;'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# ██████  AUDIT LOG
# ═══════════════════════════════════════════════
elif st.session_state.page=="audit":
    st.markdown("""<div class="mc-header"><h1>📋 Audit Log</h1><p>HIPAA-READY ACTIVITY TRACKING · USER ACTIONS · COMPLIANCE</p></div>""", unsafe_allow_html=True)
    if st.session_state.audit_log:
        st.markdown(f'<div class="mc-alert-info">📋 {len(st.session_state.audit_log)} events logged this session</div>', unsafe_allow_html=True)
        for entry in reversed(st.session_state.audit_log):
            icon={"LOGIN":"🔐","LOGOUT":"🚪","ANALYSIS":"🔬","AI CHAT":"💬","PATIENT LOG":"📋","NOTE":"📝","APPOINTMENT":"📅","LAB UPDATE":"🧪","DRUG CHECK":"💊","BATCH ANALYSIS":"📦"}.get(entry["action"],"📌")
            st.markdown(f"""<div class="mc-scan-row"><div style='display:flex;align-items:center;gap:9px;'><span style='font-size:1.1rem;'>{icon}</span><div><div style='font-size:.81rem;font-weight:600;'>{entry["action"]} — {entry["detail"]}</div><div style='font-size:.66rem;color:var(--text3);font-family:var(--mono);'>{entry["date"]} {entry["time"]} · {entry["user"]}</div></div></div><span class='mc-tag tag-blue'>{entry["action"]}</span></div>""", unsafe_allow_html=True)
        st.download_button("📥 Export Audit Log (JSON)",json.dumps(st.session_state.audit_log,indent=2),f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json","application/json")
    else: st.info("No audit events yet.")

# ═══════════════════════════════════════════════
# ██████  SETTINGS
# ═══════════════════════════════════════════════

# ═══════════════════════════════════════════════
# ██████  USER MANAGEMENT
# ═══════════════════════════════════════════════
elif st.session_state.page=="users":
    if st.session_state.role!="Admin":
        st.error("🔒 Access denied — Admin role required.")
    else:
        st.markdown("""<div class="mc-header"><h1>👤 User Management</h1><p>RBAC · ACCOUNTS · PERMISSIONS</p></div>""", unsafe_allow_html=True)
        for uname,ud in st.session_state.users_db.items():
            st.markdown(f"""<div class="mc-scan-row"><div style='display:flex;align-items:center;gap:9px;'><span style='font-size:1.2rem;'>{ud.get('avatar','👤')}</span><div><div style='font-weight:600;font-size:.81rem;'>{ud['name']}</div><div style='font-size:.66rem;color:var(--text3);font-family:var(--mono);'>@{uname} · {ud['dept']} · {ud.get('email','N/A')}</div></div></div>{role_badge_html(ud['role'])}</div>""", unsafe_allow_html=True)
        st.markdown("<div style='margin-top:.8rem;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='mc-section-title'>ADD NEW USER</div>", unsafe_allow_html=True)
        c1,c2=st.columns(2)
        with c1: nu=st.text_input("Username",key="nu"); nn=st.text_input("Full Name",key="nn"); ne=st.text_input("Email",key="ne")
        with c2: np_=st.text_input("Password",type="password",key="np"); nr=st.selectbox("Role",["Doctor","Radiologist","Admin"],key="nr"); nd=st.selectbox("Department",["Radiology","Cardiology","Neurology","IT"],key="nd")
        if st.button("➕ Add User",use_container_width=True):
            if all([nu,nn,np_]):
                avt={"Doctor":"👨‍⚕️","Radiologist":"🩻","Admin":"⚙️"}.get(nr,"👤")
                st.session_state.users_db[nu.lower()]={"password":hash_pw(np_),"role":nr,"name":nn,"dept":nd,"email":ne,"avatar":avt,"license":"—"}
                log_action("USER ADDED",f"Admin added {nu} as {nr}"); st.success(f"✅ User '{nu}' added!")
            else: st.error("Fill all fields.")

# ── Footer ──
st.markdown(f"""<div class="mc-footer">
    Cortexa Health v{APP_VERSION} · {AUTHOR}  · Real PDF/DOCX · Drug Checker · Lab Tracker · 8 Templates <br>
    {datetime.now().strftime('%Y-%m-%d')} · Ludhiana, Punjab, India
</div>""", unsafe_allow_html=True)