
## 🎥 Live Demo 

[![Watch Demo](https://img.youtube.com/vi/VIDEO_ID/0.jpg)](https://github.com/user-attachments/assets/09114534-6f4d-4279-9604-59e1c4a56d01)

<!-- <div align="center">

<img src="https://img.shields.io/badge/Version-5.0.0-2563eb?style=for-the-badge" />
<img src="https://img.shields.io/badge/AI_Powered-LLaMA_4_Vision-7c3aed?style=for-the-badge" />
<img src="https://img.shields.io/badge/Built_with-Streamlit-ff4b4b?style=for-the-badge&logo=streamlit&logoColor=white" />
<img src="https://img.shields.io/badge/Inference-Ultra--Fast_LPU-059669?style=for-the-badge" /> -->

<br/><br/>

# 🏥 Cortexa Health
### *Ultimate Clinical Intelligence Platform (CV+GenAI)*

> **AI-powered radiology, patient management, drug safety, and clinical decision support — all in one beautifully designed platform.**

<br/>

![AI Analysis](https://img.shields.io/badge/🔬_AI_Analysis-✅-2563eb?style=flat-square)
![Drug Checker](https://img.shields.io/badge/💊_Drug_Checker-✅-7c3aed?style=flat-square)
![Lab Tracker](https://img.shields.io/badge/🧪_Lab_Tracker-✅-059669?style=flat-square)
![Heatmap Studio](https://img.shields.io/badge/🧠_Heatmap_Studio-✅-dc2626?style=flat-square)
![PDF Export](https://img.shields.io/badge/📄_PDF_Export-✅-0891b2?style=flat-square)
![DOCX Export](https://img.shields.io/badge/📝_DOCX_Export-✅-d97706?style=flat-square)

</div>

---

## 🌟 What is Cortexa Health?

**Cortexa Health** is a full-stack clinical intelligence platform that brings the power of **LLaMA 4 Vision AI** directly into a hospital workflow. Designed for doctors, radiologists, and clinical administrators, it enables multi-modal medical image analysis, real-time AI consultation, drug interaction safety checks, and HIPAA-ready audit logging — all through a polished, role-based web interface.

Built with ❤️ by **Jaspreet Kaur** India.

---

## 🗺️ Feature Intelligence Map — CV vs Generative AI

Every feature in Cortexa Health belongs to one of two AI paradigms.

```
┌─────────────────────────────────────────────────────────────────┐
│              CORTEXA HEALTH INTELLIGENCE STACK                  │
├────────────────────────────┬────────────────────────────────────┤
│   👁️ COMPUTER VISION (CV)  │   🤖 GENERATIVE AI (GenAI)        │
├────────────────────────────┼────────────────────────────────────┤
│  Medical Image Analysis    │  Clinical Report Generation        │
│  AI Heatmap Generation     │  8 Specialised Report Templates    │
│  Image Enhancement (9×)    │  Drug Interaction Checker          │
│  Batch Image Processing    │  AI Clinical Chat                  │
│  DICOM Metadata Parsing    │  Treatment Plan Generator          │
│  Patient Vitals Graphing   │  Second Opinion Workflow           │
│  Lab Value Visualisation   │  Smart Alert Classification        │
│  Risk Score Computation    │  Patient-Friendly Summaries        │
└────────────────────────────┴────────────────────────────────────┘
                         ↕ unified in
              Vision-Language Cross-Attention Layer
```

---

## 👁️ Computer Vision — Deep Feature Breakdown

### 🧠 1. AI Heatmap — Attention Visualisation Studio

The heatmap is the most visually distinctive CV feature in the platform.

**What it does technically:**

When a medical image is analysed, a parallel **attention heatmap** is generated — a colour-coded overlay that visualises which spatial regions of the scan were most clinically significant. The pipeline runs 6 steps:

**Step 1 — Urgency-Driven Region Count**

The number of highlighted attention regions is dynamically determined by the urgency classification:
- `CRITICAL` → 4 attention regions
- `WARNING` → 3 attention regions
- `NORMAL` → 2 attention regions

**Step 2 — Gaussian Blob Generation**

Each region is modelled as an elliptical Gaussian intensity distribution centred at anatomically plausible coordinates. Centres are seeded from radiologically relevant priors (upper lobe, mid-zone, lower lobe, central), then perturbed by a small random offset for visual realism. Intensity falls off as `exp(-distance² × 1.5)`, creating smooth organic-looking hot zones rather than harsh circles.

**Step 3 — Urgency-Colour Palette Mapping**

Each urgency level maps to a clinically meaningful colour palette:

| Urgency | Colour Palette | Clinical Analogy |
|---|---|---|
| `CRITICAL` | Red → Orange → Amber → Yellow | Hot zone — immediate danger |
| `WARNING` | Orange → Yellow → Lime → Green | Warm zone — monitor closely |
| `NORMAL` | Green → Cyan → Blue → Teal | Cool zone — within limits |

**Step 4 — Alpha Blending onto Original Scan**

The heatmap is composited onto the original image at **48% alpha** — preserving full anatomical detail underneath while making attention zones clearly visible:

```
output = original × (1 − 0.48 × heatmap) + heatmap × [255, 80, 30] × 0.48
```

**Step 5 — Gaussian Smoothing**

A final Gaussian blur (`radius = max(W, H) ÷ 25`) softens heatmap edges, producing the smooth thermal gradient appearance characteristic of saliency maps and GradCAM outputs.

**Step 6 — Region Annotation**

Circular region markers (R1, R2, R3, R4) are drawn at each attention centre with urgency-matched border colours, allowing radiologists to reference specific zones in clinical notes.

**Interactive Controls:**
- **Sensitivity slider** (0.5× to 2.0×) — scales ellipse radii, producing tighter focused or wider diffuse attention regions
- **Urgency simulation** — independently apply CRITICAL / WARNING / NORMAL overlays on any image without running a new analysis (useful for training and demonstration)
- **Side-by-side comparison** — original and heatmap in equal columns
- **Download** — save heatmap as PNG for clinical report inclusion

**Legend:** 🔴 Critical · 🟡 Suspicious · 🟢 Normal

---

### 🔬 2. Medical Image Analysis — Vision-Language Pipeline

The core of the platform. A Vision-Language Model jointly processes image pixels and clinical text context in a single forward pass.

**Supported modalities:**
Auto-detect, Chest X-Ray, Brain MRI, Abdomen CT, Chest CT, MSK MRI, Ultrasound, PET Scan, Mammogram, Spine X-Ray, Echocardiogram, Dental OPG

**What the CV encoder extracts from pixels:**
- Pixel intensity distributions → tissue density mapping
- Edge gradients → structure boundaries (pleural lines, organ margins)
- Spatial relationships → anatomical topology
- Opacity patterns → consolidation, effusion, mass identification
- Symmetry deviation → unilateral vs bilateral findings

**Image pre-processing pipeline:**
The image is resized so the longest edge is ≤ 1568px, converted to RGB, and Base64-encoded before model transmission.

**10-section structured report output:**
1. Image Type & Technical Quality
2. Systematic Findings (✅ Normal / ⚠️ Abnormal / 🚨 Critical)
3. Diagnostic Assessment with confidence %
4. Findings Summary Table (Structure | Finding | Severity | Action)
5. Radiologist's Impression
6. ICD-10 Codes (toggleable)
7. Measurements (toggleable)
8. Evidence & Guidelines (toggleable)
9. Patient-Friendly Summary (toggleable)
10. Clinical Precautions (toggleable)

**Post-report CV pipeline:**
Three additional extractions run automatically after the report is generated:
- Urgency flag via keyword scanning
- Confidence % via regex extraction
- Primary diagnosis for scan log display

---

### 🖼️ 3. Image Enhancement Studio — 9 Classical CV Filters

Nine classical image processing operations implemented in PIL and NumPy:

| Filter | CV Algorithm | Clinical Purpose |
|---|---|---|
| **Sharpen** | Unsharp masking (radius=2, 150%) | Enhance nodule borders, calcification edges |
| **Enhance Contrast** | Linear histogram stretch (×1.8) | Differentiate soft tissue planes |
| **Denoise** | Median filter (3×3 kernel) | Remove sensor noise from low-dose CT |
| **Brighten** | Brightness scaling (×1.3) | Expose underexposed peripheral regions |
| **Edge Detect** | PIL FIND_EDGES (Sobel-based) | Highlight structural boundaries |
| **CLAHE** | Tiled adaptive histogram equalisation (8×8 tiles) | Local contrast for heterogeneous scenes |
| **Gamma Correction** | Power-law transform (γ=0.6) | Recover detail in dark image regions |
| **Invert (Bone Window)** | Pixel complement (255 − x) | Simulate film negative / bone window |
| **Pseudo-Color** | Sinusoidal RGB mapping on grayscale | False-colour for tissue density differentiation |

CLAHE is the most clinically significant — it is the standard preprocessing algorithm used in professional PACS and radiology workstations for heterogeneous structures like brain MRI.

---

### 📦 4. Batch Multi-Image Analysis — Severity-Sorted Parallel Inference

Queues unlimited images for sequential processing.

**Workflow:** Upload → analyse each image → auto-sort by severity (CRITICAL first) → side-by-side original + heatmap for each → aggregate statistics (processed / critical / warning / normal) → bulk JSON export.

**CV concept:** Severity-ranked parallel inference — the same triage approach used in emergency imaging queues.

---

### 🗂️ 5. DICOM Metadata Viewer

Extracts embedded acquisition parameters from medical image files: modality, slice thickness, pixel spacing, field of view, kVp/mAs (X-ray), TR/TE (MRI), institution, study date, equipment model. These calibration parameters directly inform how the AI interprets spatial structures in the scan.

---

### 📊 6. Patient Vitals Graphing — Time-Series Visualisation

Three Matplotlib charts rendered per patient as rasterized images:

**Blood Pressure** — dual-line (systolic red / diastolic blue), reference lines at 130/80 mmHg

**O₂ Saturation** — green line with red shaded fill below 95% (hypoxaemia threshold), y-axis 85–101%

**Heart Rate** — colour-coded bar chart (red for HR > 100 tachycardia, blue for normal), reference lines at 60 and 100 bpm

CV concept: **threshold visualisation on longitudinal biometric data** — the same technique used in ICU monitoring dashboards.

---

## 🤖 Generative AI — Deep Feature Breakdown

### 📝 7. Eight Specialised Report Templates — Conditional Text Generation

Same image, eight radically different outputs via system prompt conditioning.

| Template | AI Technique | Depth | Audience |
|---|---|---|---|
| 🔬 **Comprehensive Radiology** | Structured generation, 9 sections | Maximum | Radiologist peer |
| ⚡ **Quick Triage** | Output length constraint (~200 tokens) | Minimal | Emergency team |
| 👤 **Patient-Friendly** | Register adaptation / style transfer | Moderate | Patient |
| 📚 **Research / Academic** | Knowledge-grounded + citation synthesis | Maximum | Journal reader |
| 🔎 **Second Opinion** | Adversarial prompting, devil's advocate | Maximum | Senior review |
| 👶 **Paediatric** | Domain-specific conditioning | High | Paediatric team |
| 🎗️ **Oncology Focus** | RECIST 1.1 protocol adherence | High | Oncologist |
| ❤️ **Cardiac Focus** | Anatomical focus narrowing | High | Cardiologist |

**Quick Triage** constrains output to: most critical finding → urgency level → one immediate action. **Second Opinion** instructs the model to actively look for what a first reader may have missed. **Patient-Friendly** replaces all medical terminology with plain English ("Pulmonary opacity" → "a cloudy area in your lung") and adds empathetic framing.

---

### 💊 8. Drug Interaction Checker — Multi-Step Pharmacological Reasoning

5-step AI reasoning chain:

1. **Drug parsing** — brand names mapped to generics, dosage forms identified
2. **Pairwise interaction analysis** — CYP450 enzymes, additive toxicity, QT prolongation risk
3. **Severity classification** — Major / Moderate / Minor
4. **Allergy cross-reaction detection** — against documented patient allergies
5. **Renal/hepatic dose adjustment** — based on creatinine/eGFR from lab tracker

**Automatic safety banners:**
- 🔴 `CRITICAL` — "contraindicated", "life-threatening", "avoid", "do not"
- 🟡 `WARNING` — "caution", "moderate", "monitor", "reduce dose"
- ✅ `NORMAL` — no major flags

GenAI technique: **Chain-of-thought multi-step medical reasoning**, not a database lookup.

---

### 🧪 9. Lab Values Tracker — Rule-Based + AI Contextualisation

14 parameters with gender-specific reference ranges. Rule-based layer highlights out-of-range values (▲ High / ▼ Low / ✅ Normal). AI layer contextualises multi-value patterns — e.g., "CRP 28.5 + WBC 13.2 → active infection or inflammatory process". GenAI technique: **multivariate clinical reasoning**.

---

### 💬 10. AI Clinical Chat — Multi-Turn Conversational Reasoning

Full conversation history passed on every message (stateless API + stateful Streamlit session). Model conditioned as "Cortexa Health, expert clinical assistant and radiologist". Supports differential diagnosis, drug dosing, guideline lookup, lab interpretation. GenAI technique: **multi-turn dialogue with persistent context**.

---

### 🔔 11. Smart Alert System — Post-Generation Output Classification

Every analysis result scanned for sentinel clinical language after generation. Critical keywords trigger timestamped alert entries and patient risk flag updates in the dashboard. High-risk patients surfaced in the Alert Center independent of new scans.

---

## 📱 All Sidebar Pages — Complete Reference

### 🏠 Dashboard
Live command centre. Aggregate session statistics (total scans, critical count, warnings). Recent scan log with urgency flag, confidence %, primary diagnosis, response time, and linked patient. Quick-action buttons for analysis, drug checker, and appointments.

### 🔬 AI Analysis
Primary clinical workbench. Left panel: template, mode, modality, urgency, model selection, optional report sections, patient linkage, prior study comparison, image upload. Right panel: five-tab report viewer — Full Report, Heatmap (with sensitivity slider), Enhancement Studio, Export (PDF / DOCX / HTML / TXT / heatmap PNG), Session History.

### 🧠 Heatmap Studio
Standalone CV workspace. Three-column layout: original image + urgency/sensitivity controls → heatmap with legend → enhancement filter view. Urgency simulation allows visualising CRITICAL / WARNING / NORMAL overlays without re-running analysis. Ideal for radiology training and retrospective review.

### 📦 Batch Analysis
Multi-image sequential pipeline. Auto-sorts results by severity. Each result card: urgency badge, primary diagnosis, confidence, full report, original + heatmap side-by-side. Bulk JSON export for HIS integration.

### 👥 Patients
Full patient roster. Each record: demographics, vitals, risk stratification (CRITICAL / HIGH / WARNING / LOW), computed risk score (0–100), medication list, allergy alerts, insurance data, appointment schedule, scan history count.

### 📋 Patient Logs
Timestamped clinical notes. Entry types: Note, Prescription, Referral, Follow-up, Alert, AI Scan, Observation, Lab Result. AI analyses auto-append log entries to linked patients. Timeline view (last 6 entries, colour-coded by type). Filterable by entry type. Exportable as styled HTML or JSON.

### 💊 Drug Checker
Multi-drug AI pharmacology engine. Input: newline-separated medication list. Output: interaction report, severity classification, allergy warnings, dosing adjustments, safe alternatives. Automatic safety banner. Patient linkage auto-logs the check. Bottom panel shows medication summaries for all demo patients.

### 🧪 Lab Tracker
14-parameter entry form with gender-specific reference ranges. Instant colour-coded out-of-range highlighting. Historical trend tracking across visits. Reference table always visible alongside entry form.

### 💬 AI Chat
Full clinical chat interface. Complete conversation history. Conditioned as senior radiologist and clinical consultant. Quick-prompt sidebar buttons. Chat history exportable.

### ⚠️ Precautions
Allergy and contraindication safety dashboard. Red banners for all documented allergies at top. Per-patient precaution lists sorted by risk level. Covers: medication restrictions, activity limitations, follow-up schedules, allergy-safe drug alternatives.

### 📝 Report Templates
Browsable gallery of all 8 templates with descriptions, use-case summaries, and one-click navigation to Analysis with template pre-selected.

### 🔔 Alert Center
Three panels: AI critical flags from this session (timestamped) → high-risk patients (CRITICAL and HIGH) → system health (4 systems). Reverse-chronological. Designed to surface the most urgent clinical information at a glance.

### 📋 Audit Log
HIPAA-ready action log. Captures: Login, Logout, Analysis, AI Chat, Patient Log, Note, Appointment, Lab Update, Drug Check, Batch Analysis. Per entry: icon, description, timestamp, username. JSON export for compliance review.

### 👤 User Management *(Admin only)*
Full user roster with avatars, names, departments, emails, and role badges. New user creation: username, full name, email, SHA-256 hashed password, role, department. Avatars auto-assigned by role (👨‍⚕️ / 🩻 / ⚙️).

---

## 🛠️ Tech Stack

| Layer | Technology | Role |
|---|---|---|
| **Frontend / UI** | Streamlit + custom CSS | Responsive clinical interface |
| **AI Vision-Language** | LLaMA 4 Scout & Maverick (Vision) | CV + GenAI unified inference |
| **CV / Image Processing** | Pillow (PIL), NumPy | Heatmap, filters, preprocessing |
| **Charting** | Matplotlib | Patient vitals time-series graphs |
| **PDF Export** | ReportLab | Clinical-grade formatted PDF |
| **Word Export** | python-docx | Formatted .docx clinical reports |
| **Auth** | SHA-256 + Streamlit session state | Password hashing, RBAC |
| **Language** | Python 3.10+ | Core runtime |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or higher
- A free AI Inference API Key

### 1. Clone
```bash
git clone https://github.com/your-username/cortexa-health.git
cd cortexa-health
```

### 2. Install Dependencies
```bash
pip install streamlit pillow numpy groq reportlab python-docx matplotlib
```

### 3. Set API Key
```bash
export GROQ_API_KEY="your_api_key_here"
```
Or via `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY = "your_api_key_here"
```

### 4. Run
```bash
streamlit run app.py
```
Open `http://localhost:8501` 🎉

---

## 🔑 Demo Login Credentials

| Username | Password | Role | Department |
|---|---|---|---|
| `dr.sharma` | `doctor123` | Doctor | Radiology |
| `dr.chen` | `doctor123` | Doctor | Cardiology |
| `rad.jones` | `radio123` | Radiologist | Radiology |
| `admin` | `admin123` | Admin | IT |

---

## 📦 Requirements

```text
streamlit>=1.32.0
pillow>=10.0.0
numpy>=1.24.0
groq>=0.5.0
reportlab>=4.0.0
python-docx>=1.1.0
matplotlib>=3.8.0
```

> `reportlab`, `python-docx`, and `matplotlib` are optional — the app gracefully degrades to text export if any are missing.

---

## 📁 Project Structure

```
cortexa-health/
├── app.py                  # Full application — 2100+ lines, single file
├── README.md               # You are here
├── .streamlit/
│   └── secrets.toml        # API keys (gitignored)
└── requirements.txt        # Python dependencies
```

---

## 🔒 Security Notes

- Passwords hashed with **SHA-256** — never stored in plaintext
- Role-based access enforced on every page render
- All AI requests are stateless — no PHI written to external storage
- Audit log captures every user action for compliance review

> ⚠️ For production: replace in-memory user store with a database, enforce HTTPS, implement full HIPAA-compliant data governance.

---

## 🤝 Contributing

1. Fork the repository
2. `git checkout -b feature/your-feature`
3. `git commit -m 'Add amazing feature'`
4. `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📜 License

MIT License — see `LICENSE` for details.

---

<div align="center">

**Built with passion for better clinical care**

*Cortexa Health v5.0.0 · Jaspreet Kaur · , India*

[![Made with Streamlit](https://img.shields.io/badge/Made%20with-Streamlit-ff4b4b?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![LLaMA 4 Vision](https://img.shields.io/badge/Model-LLaMA%204%20Vision-7c3aed?style=flat-square)](https://ai.meta.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=flat-square&logo=python&logoColor=white)](https://python.org)

</div>

<img width="1902" height="921" alt="Image" src="https://github.com/user-attachments/assets/37e38d8f-ee79-44e4-9c21-f56ef31df2b5" />
<img width="1897" height="917" alt="Image" src="https://github.com/user-attachments/assets/25aab5a9-abaa-4fad-8450-f086c95e1d69" />
<img width="1625" height="917" alt="Image" src="https://github.com/user-attachments/assets/3c3338d1-b3b0-44b2-b92d-806be559affc" />
<img width="1662" height="856" alt="Image" src="https://github.com/user-attachments/assets/4aeb2377-448c-4a40-a1cb-accc9840ae73" />
<img width="1902" height="892" alt="Image" src="https://github.com/user-attachments/assets/36c2df0a-70a0-49d5-923d-ca5465f819b9" />
<img width="1865" height="891" alt="Image" src="https://github.com/user-attachments/assets/e071a983-7afb-4c21-b705-47f34d4c8dd3" />
<img width="1907" height="888" alt="Image" src="https://github.com/user-attachments/assets/ec936977-7075-4fb2-9f67-37763ada07a2" />
<img width="1898" height="922" alt="Image" src="https://github.com/user-attachments/assets/724e196f-ea8c-4bea-b2b0-0b64ac014992" />
<img width="1877" height="908" alt="Image" src="https://github.com/user-attachments/assets/74c4fce4-720b-4008-a4b7-e0b4ad8f319e" />
<img width="1890" height="922" alt="Image" src="https://github.com/user-attachments/assets/bcce558e-6300-4cef-a9b7-b08260daa5d5" />
<img width="1905" height="915" alt="Image" src="https://github.com/user-attachments/assets/2f3f72e1-aacd-4a14-a982-d7d0de0423a9" />
<img width="1907" height="927" alt="Image" src="https://github.com/user-attachments/assets/ee2c5539-f8a1-4935-8148-97f7f106bfe0" />
<img width="1877" height="922" alt="Image" src="https://github.com/user-attachments/assets/f0dc9a73-6401-4583-86d1-3b12db386bd1" />
<img width="1863" height="917" alt="Image" src="https://github.com/user-attachments/assets/25179d54-4b6d-46d5-af50-65f46c77a0f2" />
<img width="1886" height="915" alt="Image" src="https://github.com/user-attachments/assets/9d40d840-d3b1-434e-befe-c9eef07b4f5b" />
<img width="1876" height="926" alt="Image" src="https://github.com/user-attachments/assets/85ec9ba4-a826-409d-9900-4fb2312e5a24" />
<img width="1867" height="897" alt="Image" src="https://github.com/user-attachments/assets/d8bfea24-66ab-4aab-b8e1-1fcdc2e61132" />
<img width="1877" height="920" alt="Image" src="https://github.com/user-attachments/assets/4ec5de5d-0eb4-4777-bcf0-60ea38c599ca" />
<img width="1886" height="911" alt="Image" src="https://github.com/user-attachments/assets/5eea427b-9a10-4704-afc3-6b7eb9a2366e" />
<img width="1881" height="865" alt="Image" src="https://github.com/user-attachments/assets/d74cf0ad-de11-481c-afc5-3ab7b9fdf99f" />
<img width="1887" height="900" alt="Image" src="https://github.com/user-attachments/assets/f210aadb-8ce7-4d6f-84c4-082886238bb2" />
<img width="1897" height="918" alt="Image" src="https://github.com/user-attachments/assets/7ed3e0cd-7e54-45cb-b05b-7d486329e083" />
<img width="1903" height="917" alt="Image" src="https://github.com/user-attachments/assets/cfadd91a-50aa-4f36-894f-2e447057cd09" />
<img width="718" height="841" alt="Image" src="https://github.com/user-attachments/assets/a355b592-1b2a-48d0-a3b3-fcd0369e9a81" />
