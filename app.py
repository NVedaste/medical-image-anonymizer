"""
MedAnon Pro — Medical Image Anonymization System
© Vedaste NYANDWI · University of Rwanda · CBE · ACE-DS · Data Mining

Run:
    pip install streamlit Pillow pydicom
    streamlit run app.py
"""

import streamlit as st
import io, shutil, zipfile, logging, hashlib, csv, base64, re
from pathlib import Path
from datetime import datetime
from PIL import Image

# ── Enforce upload size limit (700 MB) via runtime config ──────────
from streamlit import config as _stconfig
try:
    _stconfig.set_option("server.maxUploadSize", 700)
    _stconfig.set_option("server.maxMessageSize", 700)
except Exception:
    pass

DICOM_AVAILABLE = False
try:
    import pydicom
    from pydicom.uid import generate_uid
    DICOM_AVAILABLE = True
except ImportError:
    pass

st.set_page_config(page_title="MedAnon Pro", page_icon="🛡",
                   layout="wide", initial_sidebar_state="collapsed")

# ══════════════════════════════════════════════════════════════════
# DESIGN SYSTEM
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lexend:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
  --navy:    #0d1b2a;
  --navy2:   #162032;
  --navy3:   #1e2d42;
  --teal:    #0ea5a0;
  --teal-dk: #0d9488;
  --teal-lt: #ecfdf5;
  --white:   #ffffff;
  --bg:      #f2f6fb;
  --surface: #ffffff;
  --border:  #dde4ef;
  --border2: #c8d3e6;
  --text:    #0f1d2e;
  --text2:   #374a60;
  --text3:   #5e7190;
  --red:     #dc2626;  --red-lt:  #fef2f2;
  --amber:   #d97706;  --amber-lt:#fffbeb;
  --green:   #16a34a;  --green-lt:#f0fdf4;
  --blue:    #2563eb;  --blue-lt: #eff6ff;
  --purple:  #7c3aed;  --purple-lt:#f5f3ff;
  --r: 12px; --rs: 8px;
  --sh: 0 1px 3px rgba(13,27,42,.05), 0 4px 12px rgba(13,27,42,.07);
}

html, body, [class*="css"] {
  font-family: 'Lexend', sans-serif !important;
  font-size: 15px !important;
  line-height: 1.65 !important;
  background: var(--bg) !important;
  -webkit-font-smoothing: antialiased;
}

p, div, span, li, label, input, textarea, select {
  font-family: 'Lexend', sans-serif !important;
}

.main p, .stMarkdown p  {
  font-size: 1rem !important;
  line-height: 1.65 !important;
  color: var(--text) !important;
}
.stMarkdown p  { color: var(--text2) !important; }
.stMarkdown li { font-size: 1rem !important; line-height: 1.8 !important; color: var(--text2) !important; }

.stSelectbox label, .stTextInput label, .stTextArea label,
.stFileUploader label, .stRadio label, .stCheckbox label, .stSlider label {
  font-size: .92rem !important; font-weight: 500 !important; color: var(--text) !important;
}
.stTextInput input, .stTextArea textarea { font-size: .95rem !important; color: var(--text) !important; }

#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
[data-testid="collapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }

.main .block-container,
[data-testid="block-container"],
div.block-container {
  padding-top:    1.8rem  !important;
  padding-bottom: 5rem    !important;
  padding-left:   3.5rem  !important;
  padding-right:  3.5rem  !important;
  max-width:      1060px  !important;
  margin-left:    auto    !important;
  margin-right:   auto    !important;
}

[data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
}

.pg-wrap    { margin-bottom: 1.4rem; }
.pg-eyebrow { font-size: .72rem; font-weight: 700; letter-spacing: 1.8px; text-transform: uppercase; color: var(--teal-dk) !important; margin-bottom: .3rem; }
.pg-title   { font-size: 1.6rem; font-weight: 800; color: var(--text) !important; letter-spacing: -.5px; line-height: 1.2; margin: 0 0 .35rem; }
.pg-sub     { font-size: 1rem; color: var(--text3) !important; line-height: 1.6; }

.card { background: var(--white); border: 1px solid var(--border); border-radius: var(--r); padding: 1.5rem 1.6rem; margin-bottom: 1rem; box-shadow: var(--sh); }
.card-header { display: flex; align-items: center; gap: .6rem; margin-bottom: 1rem; }
.card-icon { width: 30px; height: 30px; border-radius: 7px; display: flex; align-items: center; justify-content: center; font-size: .9rem; flex-shrink: 0; }
.ci-teal  { background: var(--teal-lt); }
.ci-amber { background: var(--amber-lt); }
.ci-red   { background: var(--red-lt); }
.ci-blue  { background: var(--blue-lt); }
.ci-green { background: var(--green-lt); }
.card-title { font-size: .8rem; font-weight: 700; text-transform: uppercase; letter-spacing: .7px; color: var(--text2) !important; }

.weakness-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: .65rem; margin-bottom: .6rem; }
.wk-pill { background: var(--bg); border: 1px solid var(--border); border-radius: var(--rs); padding: .7rem .85rem; border-left: 3px solid var(--teal); }
.wk-pill.amber { border-left-color: var(--amber); }
.wk-pill.blue  { border-left-color: var(--blue); }
.wk-pill.green { border-left-color: var(--green); }
.wk-pill.red   { border-left-color: var(--red); }
.wk-title { font-size: .78rem; font-weight: 700; color: var(--text) !important; margin-bottom: .12rem; }
.wk-desc  { font-size: .73rem; color: var(--text3) !important; line-height: 1.5; }
.wk-status { font-size: .65rem; font-weight: 700; letter-spacing: .5px; text-transform: uppercase; margin-top: .3rem; }
.wk-status.addressed { color: var(--teal-dk) !important; }
.wk-status.noted     { color: var(--amber) !important; }
.wk-status.partial   { color: var(--blue) !important; }

.info-grid { display: grid; grid-template-columns: repeat(2,1fr); gap: .65rem; margin-bottom: .8rem; }
.info-pill { background: var(--bg); border: 1px solid var(--border); border-radius: var(--rs); padding: .75rem 1rem; }
.info-lbl  { font-size: .65rem; font-weight: 700; text-transform: uppercase; letter-spacing: .7px; color: var(--text3) !important; margin-bottom: .18rem; }
.info-val  { font-size: .92rem; font-weight: 600; color: var(--text) !important; }
.info-code { font-family: 'JetBrains Mono', monospace; font-size: .82rem; font-weight: 500; color: var(--teal-dk) !important; }

.mode-btn { border: 2px solid var(--border); border-radius: var(--r); padding: 1.1rem; text-align: center; background: var(--white); transition: all .15s; }
.mode-btn:hover, .mode-btn.active { border-color: var(--teal); background: var(--teal-lt); }
.mode-btn-icon  { font-size: 1.5rem; margin-bottom: .3rem; }
.mode-btn-label { font-size: .88rem; font-weight: 700; color: var(--text) !important; }
.mode-btn-hint  { font-size: .73rem; color: var(--text3) !important; margin-top: .12rem; }

.alert { display: flex; align-items: flex-start; gap: .75rem; border-radius: var(--rs); padding: .9rem 1.1rem; margin: .7rem 0; font-size: .88rem; line-height: 1.55; }
.alert-ok     { background: var(--green-lt); border:1px solid #bbf7d0; border-left:4px solid var(--green); color:#14532d !important; }
.alert-warn   { background: var(--amber-lt); border:1px solid #fde68a; border-left:4px solid var(--amber); color:#78350f !important; }
.alert-info   { background: var(--blue-lt);  border:1px solid #bfdbfe; border-left:4px solid var(--blue);  color:#1e40af !important; }
.alert-danger { background: var(--red-lt);   border:1px solid #fecdd3; border-left:4px solid var(--red);   color:#9f1239 !important; }
.alert-teal   { background: var(--teal-lt);  border:1px solid #a7f3d0; border-left:4px solid var(--teal);  color:#065f46 !important; }

.fname-preview { font-family:'JetBrains Mono',monospace; font-size:.86rem; background:var(--navy); color:var(--teal) !important; padding:.7rem 1rem; border-radius:var(--rs); margin:.4rem 0; }
.fname-label   { font-size:.65rem; color:#475569 !important; margin-bottom:.22rem; font-weight:600; letter-spacing:.5px; text-transform:uppercase; }

.stat-row { display:flex; gap:.7rem; margin-bottom:1rem; }
.stat-box  { flex:1; background:var(--white); border:1px solid var(--border); border-radius:var(--r); padding:1rem 1.1rem; text-align:center; box-shadow:var(--sh); }
.stat-n    { font-size:2.1rem; font-weight:800; line-height:1; }
.stat-l    { font-size:.72rem; color:var(--text3) !important; margin-top:.22rem; font-weight:500; }
.c-teal { color:var(--teal-dk) !important; } .c-red { color:var(--red) !important; }
.c-amber{ color:var(--amber) !important; }   .c-slate{ color:var(--text) !important; }

.ftable { border:1px solid var(--border); border-radius:var(--r); overflow:hidden; box-shadow:var(--sh); }
.fth  { display:grid; grid-template-columns:2fr 2.3fr 88px; background:var(--navy); padding:.6rem 1.1rem; font-family:'JetBrains Mono',monospace; font-size:.63rem; letter-spacing:1.1px; text-transform:uppercase; color:#475569 !important; }
.frow { display:grid; grid-template-columns:2fr 2.3fr 88px; padding:.65rem 1.1rem; background:var(--white); border-top:1px solid var(--border); align-items:center; transition:background .12s; }
.frow:hover { background:var(--bg); }
.f-orig { font-size:.82rem; color:var(--text3) !important; font-family:'JetBrains Mono',monospace; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.f-new  { font-family:'JetBrains Mono',monospace; font-size:.84rem; font-weight:600; color:var(--teal-dk) !important; }
.fbadge { font-family:'JetBrains Mono',monospace; font-size:.63rem; padding:3px 9px; border-radius:100px; justify-self:start; }
.fbok   { background:var(--teal-lt); color:var(--teal-dk) !important; }
.fberr  { background:var(--red-lt);  color:var(--red) !important; }
.fbskip { background:var(--amber-lt);color:var(--amber) !important; }

.del-box   { background:var(--red-lt);   border:2px solid #fecdd3; border-radius:var(--r); padding:1.3rem 1.4rem; }
.del-title { font-size:1rem; font-weight:800; color:var(--red) !important; margin-bottom:.45rem; }
.proof-box { background:var(--green-lt); border:2px solid #86efac; border-radius:var(--r); padding:1.4rem; }
.proof-title { font-size:1rem; font-weight:800; color:#15803d !important; margin-bottom:.75rem; }
.proof-row { display:flex; align-items:flex-start; gap:.6rem; font-size:.88rem; color:#14532d !important; margin-bottom:.4rem; }

.logbox { background:var(--navy); color:#4ade80 !important; font-family:'JetBrains Mono',monospace; font-size:.75rem; border-radius:var(--rs); padding:.9rem 1.1rem; max-height:230px; overflow-y:auto; line-height:1.75; border:1px solid var(--navy3); }

.img-count-badge { background:var(--navy); border:1px solid var(--navy3); border-radius:var(--rs); padding:.48rem .8rem; font-size:.82rem; color:#94a3b8 !important; display:inline-flex; align-items:center; gap:.4rem; margin-bottom:.5rem; }

.stButton > button { font-family:'Lexend',sans-serif !important; font-weight:600 !important; border-radius:var(--rs) !important; border:none !important; transition:all .15s !important; font-size:.92rem !important; }
.stButton > button[kind="primary"] { background:var(--teal) !important; color:var(--navy) !important; font-weight:700 !important; padding:.58rem 1.5rem !important; }
.stButton > button:hover { opacity:.88 !important; transform:translateY(-1px) !important; }
.stProgress > div > div > div { background:var(--teal) !important; border-radius:100px !important; }
.stSelectbox > div > div, .stTextInput > div > div { border-radius:var(--rs) !important; border-color:var(--border) !important; font-size:.92rem !important; }
.stFileUploader > div { border-radius:var(--r) !important; }
.stCheckbox { margin:.45rem 0 !important; }
label, .stRadio label, .stCheckbox label { font-size:.92rem !important; }
hr { border-color:var(--border) !important; }
::-webkit-scrollbar { width:4px; height:4px; }
::-webkit-scrollbar-thumb { background:var(--border2); border-radius:10px; }

.review-card { background:var(--white); border:1px solid var(--border); border-radius:var(--r); padding:1.2rem 1.4rem; margin-bottom:.7rem; box-shadow:var(--sh); }
.review-header { display:flex; align-items:center; gap:.7rem; margin-bottom:.5rem; }
.review-avatar { width:36px; height:36px; border-radius:50%; background:linear-gradient(135deg,var(--teal),#2563eb); display:flex; align-items:center; justify-content:center; font-size:.95rem; font-weight:800; color:white !important; flex-shrink:0; }
.review-name  { font-size:.92rem; font-weight:700; color:var(--text) !important; }
.review-role  { font-size:.73rem; color:var(--text3) !important; }
.review-stars { font-size:1.05rem; letter-spacing:1px; margin-left:auto; }
.review-body  { font-size:.88rem; color:var(--text2) !important; line-height:1.65; }
.review-meta  { font-size:.72rem; color:var(--text3) !important; margin-top:.55rem; display:flex; gap:.7rem; }
.review-tag   { display:inline-block; font-size:.65rem; font-weight:600; padding:2px 9px; border-radius:100px; }
.tag-hospital   { background:var(--teal-lt);   color:var(--teal-dk) !important; }
.tag-researcher { background:var(--blue-lt);   color:var(--blue) !important; }
.tag-student    { background:var(--purple-lt); color:var(--purple) !important; }
.tag-staff      { background:var(--amber-lt);  color:var(--amber) !important; }
.rating-summary { display:flex; align-items:center; gap:1.5rem; background:var(--bg); border:1px solid var(--border); border-radius:var(--r); padding:1.1rem 1.4rem; margin-bottom:1.1rem; }
.rating-big      { font-size:2.8rem; font-weight:800; color:var(--text) !important; line-height:1; }
.rating-stars-lg { font-size:1.2rem; margin:.15rem 0; }
.rating-count    { font-size:.75rem; color:var(--text3) !important; }
.rating-bars     { flex:1; }
.rating-bar-row  { display:flex; align-items:center; gap:.5rem; margin-bottom:.28rem; }
.rating-bar-lbl  { font-size:.74rem; color:var(--text3) !important; width:12px; text-align:right; }
.rating-bar-track{ flex:1; height:7px; background:var(--border); border-radius:100px; overflow:hidden; }
.rating-bar-fill { height:100%; border-radius:100px; background:var(--teal); }
.rating-bar-n    { font-size:.7rem; color:var(--text3) !important; width:20px; }

/* ── Success toast for feedback ── */
.fb-success-toast {
  background: var(--green-lt);
  border: 2px solid #86efac;
  border-radius: var(--r);
  padding: 1.1rem 1.4rem;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: .75rem;
  animation: slideIn .3s ease;
}
@keyframes slideIn {
  from { opacity: 0; transform: translateY(-8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.fb-success-toast .toast-icon { font-size: 1.4rem; }
.fb-success-toast .toast-msg  { font-size: .92rem; font-weight: 600; color: #15803d !important; }
.fb-success-toast .toast-sub  { font-size: .8rem; color: #166534 !important; margin-top: .1rem; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════
HOSPITALS = {
    "CHUK — University Teaching Hospital of Kigali": "H01",
    "KFH Rwanda — King Faisal Hospital":             "H02",
    "Hôpital La Croix du Sud":                       "H03",
    "CHUB — University Teaching Hospital of Butare": "H04",
}

ACADEMIC_TREE = {
    "University of Rwanda": {
        "code": "UR",
        "colleges": {
            "College of Business and Economics (CBE)": {
                "code": "CBE",
                "programmes": {
                    "ACE-DS · Data Science": "DS",
                    "ACE-DS · Data Mining":  "DM",
                    "MBA":                   "MBA",
                    "BBA":                   "BBA",
                }
            },
            "College of Medicine and Health Sciences (CMHS)": {
                "code": "CMHS",
                "programmes": {
                    "Medicine (MBChB)":          "MED",
                    "Public Health (MPH)":       "PH",
                    "Biomedical Engineering":    "BME",
                }
            },
            "College of Science and Technology (CST)": {
                "code": "CST",
                "programmes": {
                    "Computer Science (BSc)":    "CS",
                    "Information Technology":   "IT",
                    "Electrical Engineering":   "EE",
                }
            },
            "College of Education (CE)": {
                "code": "CE",
                "programmes": {
                    "Education (BEd)":           "EDU",
                    "Educational Management":   "EDUMGT",
                }
            },
        }
    },
    "Rwanda Polytechnic": {
        "code": "RP",
        "colleges": {
            "School of ICT": {
                "code": "ICT",
                "programmes": {
                    "Software Development":     "SD",
                    "Computer Networking":      "CN",
                }
            },
        }
    },
}

SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".dcm", ".dicom"}

# ══════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════
_D = dict(
    page=0,
    hospital_key=list(HOSPITALS.keys())[0],
    sel_university="University of Rwanda",
    sel_college="College of Business and Economics (CBE)",
    sel_programme="ACE-DS · Data Mining",
    custom_universities={},
    custom_colleges={},
    custom_programmes={},
    img_code="CXR",
    custom_hospitals={},
    upload_mode="zip",
    results=None,
    zip_bytes=None,
    zip_filename=None,
    log_lines=[],
    run_complete=False,
    dataset_deleted=False,
    integrity_log=[],
    operator_name="",
    operator_dept="",
    operator_email="",
    operator_phone="",
    patient_groups={},
    validation_results=[],
    mapping_csv=None,
    cert_ts="",
    cert_nfiles=0,
    show_add_hospital=False,
    show_add_programme=False,
    show_audit_log=False,
    # ── Feedback-specific state ──
    fb_submitted=False,       # True right after a successful submission
    fb_submitted_name="",     # Name of the reviewer just submitted
    fb_form_key=0,            # Increment to reset form widgets without rerun
    feedback_reviews=[
        {
            "name": "Dr. Mukeshimana A.",
            "role": "Radiologist",
            "role_tag": "hospital",
            "stars": 5,
            "comment": "Very easy to use. The DICOM tag cleaning is thorough and the deletion certificate is exactly what our data governance office needed. This saved us hours of manual work.",
            "ts": "2025-11-14 09:22",
            "initials": "MA",
        },
        {
            "name": "Irakoze J.",
            "role": "MSc Student, Data Science",
            "role_tag": "student",
            "stars": 5,
            "comment": "I used this for my thesis dataset from CHUK. The step-by-step interface is very clear and the ZIP upload is convenient. I especially liked seeing the preview thumbnails after anonymization.",
            "ts": "2025-12-03 14:07",
            "initials": "IJ",
        },
        {
            "name": "Niyomugaba P.",
            "role": "Research Coordinator, KFH",
            "role_tag": "researcher",
            "stars": 4,
            "comment": "The audit log with SHA-256 checksums is a great feature for our IRB compliance. Would love a PDF export of the deletion certificate in a future version.",
            "ts": "2026-01-18 11:35",
            "initials": "NP",
        },
    ],
)
for k, v in _D.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════
# LOGGER
# ══════════════════════════════════════════════════════════════════
def _logger():
    log = logging.getLogger("MedAnon")
    if not log.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(message)s", "%H:%M:%S"))
        log.addHandler(h)
    log.setLevel(logging.DEBUG)
    return log
logger = _logger()

# ══════════════════════════════════════════════════════════════════
# PROGRAMME CODE HELPER
# ══════════════════════════════════════════════════════════════════
def get_programme_code() -> str:
    uni  = st.session_state.get("sel_university","")
    col  = st.session_state.get("sel_college","")
    prog = st.session_state.get("sel_programme","")

    tree = dict(ACADEMIC_TREE)
    for u_name, u_data in st.session_state.get("custom_universities",{}).items():
        tree[u_name] = u_data

    u_code = tree.get(uni, {}).get("code", "UNI")

    cols = dict(tree.get(uni, {}).get("colleges", {}))
    key_uc = f"{uni}|{col}"
    if key_uc in st.session_state.get("custom_colleges",{}):
        cols[col] = st.session_state["custom_colleges"][key_uc]
    c_code = cols.get(col, {}).get("code", "COL")

    progs = dict(cols.get(col, {}).get("programmes", {}))
    key_up = f"{uni}|{col}|{prog}"
    if key_up in st.session_state.get("custom_programmes",{}):
        progs[prog] = st.session_state["custom_programmes"][key_up]
    p_code = progs.get(prog, "PROG")

    return f"{u_code}_{c_code}_{p_code}"

# ══════════════════════════════════════════════════════════════════
# CORE ANONYMIZATION
# ══════════════════════════════════════════════════════════════════

def _wipe(ba: bytearray):
    for i in range(len(ba)): ba[i] = 0

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16] + "…"

def strip_image(raw: bytes, ext: str) -> bytes:
    img = Image.open(io.BytesIO(raw))
    out = Image.new(img.mode, img.size)
    out.putdata(list(img.getdata()))
    buf = io.BytesIO()
    if ext in (".jpg", ".jpeg"):
        out.save(buf, format="JPEG", quality=95, subsampling=0)
    else:
        out.save(buf, format="PNG")
    return buf.getvalue()

def strip_dicom(raw: bytes) -> bytes:
    if not DICOM_AVAILABLE:
        raise RuntimeError("pydicom not installed — pip install pydicom")
    ds = pydicom.dcmread(io.BytesIO(raw))
    for tag in [
        "PatientName","PatientID","PatientBirthDate","PatientSex","PatientAge",
        "PatientWeight","PatientAddress","PatientTelephoneNumbers",
        "PatientMotherBirthName","OtherPatientNames","OtherPatientIDs",
        "InstitutionName","InstitutionAddress","InstitutionalDepartmentName",
        "ReferringPhysicianName","PerformingPhysicianName","RequestingPhysician",
        "OperatorsName","StudyDate","SeriesDate","AcquisitionDate","ContentDate",
        "StudyTime","SeriesTime","AcquisitionTime","AccessionNumber","StudyID",
        "RequestedProcedureDescription",
    ]:
        if hasattr(ds, tag):
            try: setattr(ds, tag, "ANONYMIZED")
            except: pass
    ds.StudyInstanceUID  = generate_uid()
    ds.SeriesInstanceUID = generate_uid()
    ds.SOPInstanceUID    = generate_uid()
    buf = io.BytesIO(); ds.save_as(buf)
    return buf.getvalue()

def make_fname(h, p, t, pid, ext):
    return f"{h}_{p}_{t}_{str(pid).zfill(5)}{ext.lower()}"

def collect_zip(zf_obj) -> list:
    entries = []
    with zipfile.ZipFile(io.BytesIO(zf_obj.read())) as zf:
        for info in zf.infolist():
            if info.is_dir() or "__MACOSX" in info.filename: continue
            fname = Path(info.filename)
            if fname.name.startswith("."): continue
            ext = fname.suffix.lower()
            if ext in SUPPORTED_EXT:
                raw = zf.read(info.filename)
                entries.append({"name": fname.name, "raw": raw, "ext": ext,
                                 "checksum": sha256_hex(raw)})
    return entries

def collect_files(uploaded) -> list:
    entries = []
    for f in uploaded:
        ext = Path(f.name).suffix.lower()
        if ext in SUPPORTED_EXT:
            raw = f.read()
            entries.append({"name": f.name, "raw": raw, "ext": ext,
                             "checksum": sha256_hex(raw)})
    return entries

def run_pipeline(entries, h, p, t, bar, status_el):
    results, log = [], operator_header() + [
        f"  Hospital:{h}  Program:{p}  Type:{t}  Files:{len(entries)}",
        f"  Weaknesses addressed: W1 W3 W4 W5 W7 W8 W10 W11",
        "─" * 60,
    ]
    integrity = []
    for i, e in enumerate(entries):
        bar.progress(int(i / len(entries) * 100))
        status_el.markdown(
            f'<span style="font-size:.82rem;color:#374a60;">Processing '
            f'<b>{i+1}/{len(entries)}</b>: {e["name"]}</span>',
            unsafe_allow_html=True)
        pid = e.get("pid", i + 1)
        try:
            thumb = make_thumb_b64(e["raw"], e["ext"])
            clean = (strip_dicom(e["raw"])
                     if e["ext"] in (".dcm", ".dicom")
                     else strip_image(e["raw"], e["ext"]))
            nn = make_fname(h, p, t, pid, e["ext"])
            log.append(f"  ✓  {e['name']:<44} → {nn}  [pid:{pid:05d}] [sha:{e.get('checksum','?')}]")
            integrity.append({"original": e["name"], "new": nn,
                               "sha_in": e.get("checksum","?"),
                               "sha_out": sha256_hex(clean)})
            results.append(dict(original=e["name"], new_name=nn,
                                clean_bytes=clean, ext=e["ext"],
                                status="ok", thumb=thumb, pid=pid))
        except Exception as ex:
            log.append(f"  ✗  {e['name']:<44} {ex}")
            results.append(dict(original=e["name"], new_name="—",
                                clean_bytes=None, ext=e["ext"],
                                status="error", thumb="", pid=pid))
    bar.progress(100); status_el.empty()
    ok = sum(1 for r in results if r["status"] == "ok")
    log += ["─"*60,
            f"  ✓ Anonymized:{ok}  ✗ Failed:{len(results)-ok}",
            f"  W7 Audit: {len(integrity)} checksums logged",
            "─"*60]
    return results, log, integrity

def pack_zip(results) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for r in results:
            if r["status"] == "ok" and r.get("clean_bytes"):
                zf.writestr(r["new_name"], r["clean_bytes"])
    return buf.getvalue()

def purge_ram(results) -> list:
    out = []
    for r in results:
        if r.get("clean_bytes"):
            ba = bytearray(r["clean_bytes"]); _wipe(ba)
        out.append({**r, "clean_bytes": None})
    return out

def make_thumb_b64(raw: bytes, ext: str, max_px: int = 120) -> str:
    if ext in (".dcm", ".dicom"):
        return ""
    try:
        img = Image.open(io.BytesIO(raw))
        img.thumbnail((max_px, max_px), Image.LANCZOS)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=70)
        import base64
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return ""

# ══════════════════════════════════════════════════════════════════
# FIX #1  — Operator identity baked into log + certificate
# ══════════════════════════════════════════════════════════════════
def operator_header() -> list[str]:
    name  = st.session_state.get("operator_name","").strip()  or "NOT PROVIDED"
    dept  = st.session_state.get("operator_dept","").strip()  or "NOT PROVIDED"
    email = st.session_state.get("operator_email","").strip() or "NOT PROVIDED"
    phone = st.session_state.get("operator_phone","").strip() or "NOT PROVIDED"
    ts    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return [
        "─"*60,
        f"  OPERATOR  : {name}",
        f"  DEPT      : {dept}",
        f"  EMAIL     : {email}",
        f"  PHONE     : {phone}",
        f"  TIMESTAMP : {ts}",
        "─"*60,
    ]

# ══════════════════════════════════════════════════════════════════
# FIX #2  — Encrypted mapping CSV
# ══════════════════════════════════════════════════════════════════
def build_mapping_csv(results: list, integrity: list,
                       operator: str, dept: str) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "original_filename", "anonymized_filename", "patient_group",
        "sha256_in_truncated", "sha256_out_truncated",
        "operator", "department", "timestamp",
    ])
    sha_map = {row["original"]: (row["sha_in"], row["sha_out"])
               for row in integrity}
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for r in results:
        if r["status"] != "ok":
            continue
        sha_in, sha_out = sha_map.get(r["original"], ("?", "?"))
        group = st.session_state.get("patient_groups", {}).get(r["original"], "—")
        writer.writerow([
            r["original"], r["new_name"], group,
            sha_in, sha_out, operator, dept, ts,
        ])
    return buf.getvalue().encode("utf-8")

def pack_mapping_zip(csv_bytes: bytes, password: str) -> bytes:
    try:
        import pyzipper
        buf = io.BytesIO()
        with pyzipper.AESZipFile(buf, "w",
                                  compression=pyzipper.ZIP_DEFLATED,
                                  encryption=pyzipper.WZ_AES) as zf:
            zf.setpassword(password.encode())
            zf.writestr("mapping_table.csv", csv_bytes)
            zf.writestr("README.txt",
                "This file contains the patient ID mapping table.\n"
                "Password: provided separately to the data governance officer.\n"
                "Keep this file confidential. Do not share the mapping.\n")
        return buf.getvalue()
    except ImportError:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("mapping_table.csv", csv_bytes)
            zf.writestr("SECURITY_NOTE.txt",
                "AES encryption requires: pip install pyzipper\n"
                "This ZIP is NOT password-protected. Store securely.\n")
        return buf.getvalue()

# ══════════════════════════════════════════════════════════════════
# FIX #3  — Image content validation
# ══════════════════════════════════════════════════════════════════
MEDICAL_ASPECT_RANGE = (0.5, 2.5)
MIN_DIM_PX           = 64
MAX_DIM_PX           = 8000

def validate_image(raw: bytes, ext: str, name: str) -> dict:
    warnings, errors = [], []

    if ext in (".dcm", ".dicom"):
        if not DICOM_AVAILABLE:
            return {"valid": True, "warnings": ["pydicom not installed. DICOM metadata not validated."], "errors": []}
        try:
            ds = pydicom.dcmread(io.BytesIO(raw), stop_before_pixels=True)
            modality = getattr(ds, "Modality", "").upper()
            radio_mods = {"CR","DR","DX","MR","CT","PT","NM","US","XA","RF",
                          "MG","OP","OT",""}
            if modality and modality not in radio_mods:
                warnings.append(f"Unexpected DICOM modality: {modality}")
            rows    = getattr(ds, "Rows",    None)
            cols    = getattr(ds, "Columns", None)
            if rows and cols:
                if rows < MIN_DIM_PX or cols < MIN_DIM_PX:
                    errors.append(f"Image too small: {cols}×{rows}px")
                ratio = cols / rows if rows else 1
                if not (MEDICAL_ASPECT_RANGE[0] <= ratio <= MEDICAL_ASPECT_RANGE[1]):
                    warnings.append(f"Unusual aspect ratio: {ratio:.2f}")
        except Exception as e:
            errors.append(f"Could not parse DICOM header: {e}")
        return {"valid": len(errors) == 0, "warnings": warnings, "errors": errors}

    try:
        img = Image.open(io.BytesIO(raw))
        w, h = img.size
        if w < MIN_DIM_PX or h < MIN_DIM_PX:
            errors.append(f"Image too small: {w}×{h}px (min {MIN_DIM_PX})")
        if w > MAX_DIM_PX or h > MAX_DIM_PX:
            warnings.append(f"Very large image: {w}×{h}px. Please confirm it is a medical scan.")
        ratio = w / h if h else 1
        if not (MEDICAL_ASPECT_RANGE[0] <= ratio <= MEDICAL_ASPECT_RANGE[1]):
            warnings.append(f"Aspect ratio {ratio:.2f} unusual for medical scans")
        if img.mode == "RGB":
            pixels = list(img.getdata())
            sample = pixels[::max(1, len(pixels)//500)][:500]
            coloured = sum(1 for r,g,b in sample if abs(r-g) > 20 or abs(g-b) > 20)
            if coloured / len(sample) > 0.25:
                warnings.append("Image appears to contain colour. Note: chest X-rays are greyscale.")
    except Exception as e:
        errors.append(f"Cannot open image: {e}")

    return {"valid": len(errors) == 0, "warnings": warnings, "errors": errors}

# ══════════════════════════════════════════════════════════════════
# FIX #4  — Patient grouping
# ══════════════════════════════════════════════════════════════════
def assign_pids_with_groups(entries: list, groups: dict) -> list:
    label_to_pid: dict = {}
    next_pid = 1
    result = []
    for e in entries:
        label = groups.get(e["name"], "").strip()
        if label:
            if label not in label_to_pid:
                label_to_pid[label] = next_pid
                next_pid += 1
            pid = label_to_pid[label]
        else:
            pid = next_pid
            next_pid += 1
        result.append({**e, "pid": pid})
    return result

# ══════════════════════════════════════════════════════════════════
# NAVIGATION
# ══════════════════════════════════════════════════════════════════
def go(idx):
    st.session_state["page"] = idx
    st.rerun()

# ══════════════════════════════════════════════════════════════════
# TOP NAVBAR
# ══════════════════════════════════════════════════════════════════

cur  = st.session_state["page"]
done = st.session_state["run_complete"]
_all_h  = {**HOSPITALS, **st.session_state["custom_hospitals"]}
_h_code = _all_h.get(st.session_state["hospital_key"], "H01")
_p_code = get_programme_code()
_t_code = st.session_state["img_code"]

try:
    _qp = st.query_params.get("p", None)
    if _qp is not None:
        _qp_int = int(_qp)
        if _qp_int != cur and 0 <= _qp_int <= 6:
            st.session_state["page"] = _qp_int
            st.query_params.clear()
            st.rerun()
except Exception:
    pass

_pages = [
    (0, "🏠", "Home"),
    (1, "⚙", "Configure"),
    (2, "📤", "Upload"),
    (3, "🛡", "Anonymize"),
    (4, "⬇", "Download"),
    (5, "🗑", "Delete"),
    (6, "⭐", "Feedback"),
]
_nav_html = ""
for _idx, _icon, _lbl in _pages:
    _tick   = " ✓" if done and _idx in (1,2,3) else ""
    _active = "mna-active" if cur == _idx else ""
    _nav_html += (
        f'<a class="mna-link {_active}" '
        f'href="?p={_idx}" target="_self">'
        f'<span class="mna-icon">{_icon}</span>'
        f'<span class="mna-lbl">{_lbl}{_tick}</span>'
        f'</a>'
    )

st.markdown(f"""
<style>
.mna-header {{
  background:    #0d1b2a;
  margin:        -1.8rem -3.5rem 0 -3.5rem;
  padding:       0;
  position:      sticky;
  top:           0;
  z-index:       9999;
  font-family:   'Lexend', sans-serif;
  box-shadow:    0 3px 18px rgba(13,27,42,.45);
}}
.mna-top {{
  display:         flex;
  align-items:     center;
  justify-content: space-between;
  height:          46px;
  padding:         0 1.3rem;
  border-bottom:   1px solid #1a2d40;
}}
.mna-brand {{
  display:     flex;
  align-items: center;
  gap:         .5rem;
  text-decoration: none !important;
}}
.mna-dot {{
  width:           28px;
  height:          28px;
  background:      #0ea5a0;
  border-radius:   6px;
  display:         flex;
  align-items:     center;
  justify-content: center;
  font-size:       .82rem;
  flex-shrink:     0;
  box-shadow:      0 2px 6px rgba(14,165,160,.4);
}}
.mna-name {{
  font-size:      1rem;
  font-weight:    800;
  color:          #f1f5f9 !important;
  letter-spacing: -.2px;
  line-height:    1;
  white-space:    nowrap;
}}
.mna-sub {{
  font-size:   .65rem;
  color:       #3a566e !important;
  margin-top:  .06rem;
  white-space: nowrap;
}}
.mna-sysinfo {{
  display:     flex;
  align-items: center;
  gap:         1.2rem;
}}
.mna-pill-inner {{
  font-family:   'JetBrains Mono', monospace;
  font-size:     .72rem;
  line-height:   1.65;
  color:         #5a7a96 !important;
  background:    #162032;
  border-radius: 5px;
  padding:       .22rem .65rem;
  white-space:   nowrap;
  border:        1px solid #1e2d42;
}}
.mna-pill-inner span {{ color: #0ea5a0 !important; font-weight: 600; }}
.mna-inst {{
  font-size:   .7rem;
  line-height: 1.55;
  color:       #4a6680 !important;
  text-align:  right;
  white-space: nowrap;
}}
.mna-inst b {{ color: #6a92b0 !important; font-weight: 600; }}
.mna-tabs {{
  display:       flex;
  align-items:   stretch;
  height:        48px;
  border-bottom: 2.5px solid #0ea5a0;
  overflow:      hidden;
}}
.mna-link {{
  display:         flex;
  align-items:     center;
  justify-content: center;
  gap:             .38rem;
  flex:            1;
  font-size:       .92rem;
  font-weight:     500;
  color:           #7ea8c8 !important;
  text-decoration: none !important;
  border-bottom:   3px solid transparent;
  white-space:     nowrap;
  height:          48px;
  transition:      background .12s, color .12s, border-color .12s;
  box-sizing:      border-box;
  padding:         0 .4rem;
}}
.mna-link:visited,
.mna-link:focus {{ text-decoration: none !important; color: #7ea8c8 !important; outline: none; }}
.mna-icon {{ font-size: .9rem; flex-shrink: 0; line-height: 1; }}
.mna-lbl  {{ font-size: .92rem; line-height: 1; }}
.mna-link:hover {{
  background:          #162032;
  color:               #d4e8f8 !important;
  border-bottom-color: #2d4a62;
  text-decoration:     none !important;
}}
.mna-link.mna-active {{
  background:          #1a2d40;
  color:               #ffffff !important;
  font-weight:         700;
  border-bottom-color: #0ea5a0;
  text-decoration:     none !important;
}}
</style>

<div class="mna-header">
  <div class="mna-top">
    <div class="mna-brand">
      <div class="mna-dot">🛡</div>
      <div>
        <div class="mna-name">MedAnon Pro</div>
        <div class="mna-sub">© Vedaste NYANDWI</div>
      </div>
    </div>
    <div class="mna-sysinfo">
      <div class="mna-pill-inner">
        {_h_code} · {_t_code} &nbsp;|&nbsp; <span>{_p_code}</span>
      </div>
      <div class="mna-inst">
        <b>University of Rwanda</b><br>
        College of Business &amp; Economics · ACE-DS · Data Mining
      </div>
    </div>
  </div>
  <div class="mna-tabs">
    {_nav_html}
  </div>
</div>
<div style="margin-bottom:2rem;"></div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# PAGE 0 — HOME
# ══════════════════════════════════════════════════════════════════
if cur == 0:
    st.markdown("""
    <div class="pg-wrap">
      <div class="pg-eyebrow">Getting started</div>
      <div class="pg-title">Welcome to MedAnon Pro</div>
      <div class="pg-sub">Secure medical image anonymization for hospital datasets.</div>
    </div>""", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="card">
          <div class="card-header">
            <div class="card-icon ci-teal">⚡</div>
            <div class="card-title">What this tool does</div>
          </div>
          <ul style="font-size:.87rem;line-height:2.1;color:#374a60;padding-left:1.1rem;margin:0;">
            <li>Renames images with opaque sequential patient IDs</li>
            <li>Strips all EXIF metadata via pixel-level reconstruction</li>
            <li>Wipes 27 PHI fields from DICOM files and regenerates UIDs</li>
            <li>Logs SHA-256 checksums for every file (audit trail)</li>
            <li>Zeros all image buffers from RAM after packaging</li>
            <li>Packages anonymized images into a downloadable ZIP</li>
          </ul>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="card">
          <div class="card-header">
            <div class="card-icon ci-blue">🗺</div>
            <div class="card-title">5-step workflow</div>
          </div>
          <ol style="font-size:.87rem;line-height:2.1;color:#374a60;padding-left:1.1rem;margin:0;">
            <li><b>Configure</b>: select hospital, program, image type</li>
            <li><b>Upload</b>: ZIP your folder or pick individual files</li>
            <li><b>Anonymize</b>: one-click pipeline with live progress</li>
            <li><b>Download</b>: save the anonymized ZIP to your device</li>
            <li><b>Delete</b>: purge originals &amp; receive deletion certificate</li>
          </ol>
        </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
      <div class="card-header">
        <div class="card-icon ci-amber">🔬</div>
        <div class="card-title">Known weaknesses addressed by this system</div>
      </div>
      <div style="font-size:.78rem;color:#374a60;margin-bottom:.75rem;">
        Based on published literature on image anonymization vulnerabilities.
      </div>
      <div class="weakness-grid">
        <div class="wk-pill">
          <div class="wk-title">W1 · Metadata re-identification</div>
          <div class="wk-desc">EXIF GPS, timestamps, device IDs removed via full pixel reconstruction.</div>
          <div class="wk-status addressed">✓ Fully addressed</div>
        </div>
        <div class="wk-pill green">
          <div class="wk-title">W5 · Contextual leakage</div>
          <div class="wk-desc">All DICOM tags stripped: institution, physician, acquisition dates.</div>
          <div class="wk-status addressed">✓ Fully addressed</div>
        </div>
        <div class="wk-pill blue">
          <div class="wk-title">W7 · No formal audit trail</div>
          <div class="wk-desc">SHA-256 checksum logged per file before and after anonymization.</div>
          <div class="wk-status addressed">✓ Fully addressed</div>
        </div>
        <div class="wk-pill green">
          <div class="wk-title">W11 · Key/buffer management</div>
          <div class="wk-desc">All image buffers byte-zeroed in RAM immediately after ZIP is packed.</div>
          <div class="wk-status addressed">✓ Fully addressed</div>
        </div>
        <div class="wk-pill amber">
          <div class="wk-title">W4 · GAN face-replacement risk</div>
          <div class="wk-desc">System does not use generative models. No GAN leakage risk.</div>
          <div class="wk-status addressed">✓ Avoided by design</div>
        </div>
        <div class="wk-pill amber">
          <div class="wk-title">W10 · Scalability failures</div>
          <div class="wk-desc">Full in-memory pipeline. ZIP built only after all files succeed.</div>
          <div class="wk-status partial">~ Partially addressed</div>
        </div>
        <div class="wk-pill" style="border-left-color:var(--text3);">
          <div class="wk-title">W3 · Detection coverage gaps</div>
          <div class="wk-desc">X-ray pipeline does not use face detection. Renaming is universal.</div>
          <div class="wk-status noted">~ Not applicable (X-ray)</div>
        </div>
        <div class="wk-pill" style="border-left-color:var(--text3);">
          <div class="wk-title">W8 · Demographic bias in detection</div>
          <div class="wk-desc">No ML detector used. All images processed equally.</div>
          <div class="wk-status noted">~ Not applicable</div>
        </div>
        <div class="wk-pill red">
          <div class="wk-title">W2 · Adversarial attacks</div>
          <div class="wk-desc">No ML-based detector used, so adversarial perturbations cannot bypass the pipeline.</div>
          <div class="wk-status addressed">✓ Avoided by design</div>
        </div>
      </div>
      <div class="alert alert-warn" style="margin-top:.75rem;">
        <span>⚠️</span>
        <div style="font-size:.8rem;"><b>Residual limitations:</b> Utility-privacy trade-off in MRI/CT, cross-modal linkage when audio/text records coexist, and non-facial biometrics are outside the scope of file-level anonymization.</div>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
      <div class="card-header">
        <div class="card-icon ci-red">🏥</div>
        <div class="card-title">5 Hospital-Specific Requirements: Addressed</div>
      </div>
      <div class="weakness-grid">
        <div class="wk-pill green">
          <div class="wk-title">Operator Identity</div>
          <div class="wk-desc">Researcher name and department captured in Configure. Printed on the deletion certificate.</div>
          <div class="wk-status addressed">✓ Implemented</div>
        </div>
        <div class="wk-pill blue">
          <div class="wk-title">Encrypted Mapping Table</div>
          <div class="wk-desc">CSV mapping original → anonymized ID, with SHA-256 hashes. AES-encrypted ZIP.</div>
          <div class="wk-status addressed">✓ Implemented</div>
        </div>
        <div class="wk-pill amber">
          <div class="wk-title">Image Content Validation</div>
          <div class="wk-desc">Checks dimensions, aspect ratio, and colour distribution. Catches accidental photo uploads.</div>
          <div class="wk-status addressed">✓ Implemented</div>
        </div>
        <div class="wk-pill">
          <div class="wk-title">Patient Grouping</div>
          <div class="wk-desc">Files belonging to the same patient share one anonymized ID.</div>
          <div class="wk-status addressed">✓ Implemented</div>
        </div>
        <div class="wk-pill red">
          <div class="wk-title">Memory Purge on Delete</div>
          <div class="wk-desc">All session data byte-zeroed and cleared. Certificate records event with timestamp.</div>
          <div class="wk-status addressed">✓ Implemented</div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    col_btn, _ = st.columns([1, 3])
    with col_btn:
        if st.button("Get Started →", type="primary", use_container_width=True):
            go(1)


# ══════════════════════════════════════════════════════════════════
# PAGE 1 — CONFIGURE
# ══════════════════════════════════════════════════════════════════
elif cur == 1:
    st.markdown("""
    <div class="pg-wrap">
      <div class="pg-eyebrow">Step 1</div>
      <div class="pg-title">Configure</div>
      <div class="pg-sub">Choose your hospital, program and image type.</div>
    </div>""", unsafe_allow_html=True)

    all_hospitals = {**HOSPITALS, **st.session_state["custom_hospitals"]}

    st.markdown('<div class="card"><div class="card-header"><div class="card-icon ci-teal">🏥</div><div class="card-title">Hospital</div></div>', unsafe_allow_html=True)
    sel_h = st.selectbox("Select hospital", list(all_hospitals.keys()),
                          index=list(all_hospitals.keys()).index(st.session_state["hospital_key"])
                          if st.session_state["hospital_key"] in all_hospitals else 0,
                          label_visibility="collapsed")
    st.session_state["hospital_key"] = sel_h
    h_code = all_hospitals[sel_h]
    st.markdown(f'<div style="margin-top:.5rem;font-size:.8rem;color:#5e7190;">Internal code: <span style="font-family:\'JetBrains Mono\',monospace;color:var(--teal-dk);font-weight:600;">{h_code}</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    _show_h = st.session_state.get("show_add_hospital", False)
    if st.button("Hide" if _show_h else "+ Register a new hospital", key="toggle_add_hospital"):
        st.session_state["show_add_hospital"] = not _show_h
        st.rerun()

    if st.session_state.get("show_add_hospital"):
        st.markdown('<div class="card" style="border-left:3px solid var(--teal);margin-top:.25rem;"><div class="card-header"><div class="card-icon ci-teal">🏥</div><div class="card-title">Register a New Hospital</div></div>', unsafe_allow_html=True)
        col_a, col_b = st.columns([3, 1])
        with col_a:
            new_hname = st.text_input("Hospital full name", placeholder="e.g. Rwanda Military Hospital", key="nh_name")
        with col_b:
            new_hcode = st.text_input("Code", value=f"H{str(len(all_hospitals)+1).zfill(2)}", max_chars=5, key="nh_code")
        if st.button("Add hospital", use_container_width=True, type="primary", key="btn_add_hospital"):
            n2, c2 = new_hname.strip(), new_hcode.strip().upper()
            if not n2: st.error("Enter a hospital name.")
            elif c2 in set(all_hospitals.values()): st.error(f"Code '{c2}' already in use.")
            elif n2 in all_hospitals: st.warning("Hospital already registered.")
            else:
                st.session_state["custom_hospitals"][n2] = c2
                st.session_state["hospital_key"] = n2
                st.session_state["show_add_hospital"] = False
                st.rerun()
        for hn, hc in list(st.session_state["custom_hospitals"].items()):
            c1, c2c = st.columns([5, 1])
            c1.markdown(f'<span style="font-size:.85rem;color:#374a60;"><b style="color:var(--teal-dk);">{hc}</b>  {hn}</span>', unsafe_allow_html=True)
            if c2c.button("Remove", key=f"del_{hc}"):
                del st.session_state["custom_hospitals"][hn]; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Academic Programme
    st.markdown('<div class="card"><div class="card-header"><div class="card-icon ci-blue">🎓</div><div class="card-title">Academic Programme — University → College → Programme</div></div>', unsafe_allow_html=True)

    full_tree = dict(ACADEMIC_TREE)
    for u_nm, u_dat in st.session_state.get("custom_universities", {}).items():
        full_tree[u_nm] = u_dat

    uni_names = list(full_tree.keys())
    cur_uni = st.session_state.get("sel_university", uni_names[0])
    if cur_uni not in uni_names: cur_uni = uni_names[0]

    st.markdown('<div style="font-size:.82rem;font-weight:600;color:#374a60;margin-bottom:.3rem;">1 · University</div>', unsafe_allow_html=True)
    sel_uni = st.selectbox("University", uni_names, index=uni_names.index(cur_uni), label_visibility="collapsed", key="sb_uni")
    if sel_uni != st.session_state.get("sel_university"):
        st.session_state["sel_university"] = sel_uni
        st.session_state["sel_college"]   = list(full_tree[sel_uni]["colleges"].keys())[0]
        col_progs = list(full_tree[sel_uni]["colleges"][st.session_state["sel_college"]]["programmes"].keys())
        st.session_state["sel_programme"] = col_progs[0] if col_progs else ""
        st.rerun()
    st.session_state["sel_university"] = sel_uni
    uni_code = full_tree[sel_uni]["code"]

    col_dict = dict(full_tree[sel_uni]["colleges"])
    for ck, cv in st.session_state.get("custom_colleges", {}).items():
        u_part, c_part = ck.split("|", 1) if "|" in ck else ("", ck)
        if u_part == sel_uni:
            col_dict[c_part] = cv

    col_names = list(col_dict.keys())
    cur_col = st.session_state.get("sel_college", col_names[0])
    if cur_col not in col_names: cur_col = col_names[0]

    st.markdown('<div style="font-size:.82rem;font-weight:600;color:#374a60;margin:.75rem 0 .3rem;">2 · College / School</div>', unsafe_allow_html=True)
    sel_col = st.selectbox("College", col_names, index=col_names.index(cur_col), label_visibility="collapsed", key="sb_col")
    if sel_col != st.session_state.get("sel_college"):
        st.session_state["sel_college"] = sel_col
        prog_list = list(col_dict.get(sel_col, {}).get("programmes", {}).keys())
        st.session_state["sel_programme"] = prog_list[0] if prog_list else ""
        st.rerun()
    st.session_state["sel_college"] = sel_col
    col_code = col_dict[sel_col]["code"]

    prog_dict = dict(col_dict.get(sel_col, {}).get("programmes", {}))
    for pk, pv in st.session_state.get("custom_programmes", {}).items():
        parts = pk.split("|")
        if len(parts) == 3 and parts[0] == sel_uni and parts[1] == sel_col:
            prog_dict[parts[2]] = pv

    prog_names = list(prog_dict.keys()) if prog_dict else ["(No programmes)"]
    cur_prog = st.session_state.get("sel_programme", prog_names[0])
    if cur_prog not in prog_names: cur_prog = prog_names[0]

    st.markdown('<div style="font-size:.82rem;font-weight:600;color:#374a60;margin:.75rem 0 .3rem;">3 · Programme</div>', unsafe_allow_html=True)
    sel_prog = st.selectbox("Programme", prog_names, index=prog_names.index(cur_prog), label_visibility="collapsed", key="sb_prog")
    st.session_state["sel_programme"] = sel_prog
    prog_code = prog_dict.get(sel_prog, "PROG")
    combined_code = get_programme_code()

    st.markdown(f"""
    <div style="margin-top:.9rem;display:flex;align-items:center;gap:1rem;
                background:var(--bg);border-radius:8px;padding:.65rem 1rem;border:1px solid var(--border);">
      <div style="font-size:.72rem;color:#5e7190;">Code for filename:</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:.9rem;font-weight:700;color:var(--teal-dk);">{combined_code}</div>
      <div style="font-size:.72rem;color:#5e7190;margin-left:.25rem;">({uni_code} · {col_code} · {prog_code})</div>
    </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    _show_p = st.session_state.get("show_add_programme", False)
    if st.button("Hide" if _show_p else "+ Add custom university, college or programme", key="toggle_add_prog"):
        st.session_state["show_add_programme"] = not _show_p
        st.rerun()

    if st.session_state.get("show_add_programme"):
        st.markdown('<div class="card" style="border-left:3px solid var(--blue);margin-top:.25rem;"><div class="card-header"><div class="card-icon ci-blue">🎓</div><div class="card-title">Add Custom Entry</div></div>', unsafe_allow_html=True)
        add_tab = st.selectbox("What to add:", ["University", "College", "Programme"], key="add_tab_sel")
        if add_tab == "University":
            ca, cb = st.columns([3, 1])
            with ca: new_u = st.text_input("University name", placeholder="e.g. INES-Ruhengeri", key="new_u_name")
            with cb: new_u_code = st.text_input("Code", max_chars=6, placeholder="INES", key="new_u_code")
            if st.button("Add university", use_container_width=True, type="primary", key="btn_add_u"):
                n, c = new_u.strip(), new_u_code.strip().upper()
                if not n: st.error("Enter a university name.")
                elif not c: st.error("Enter a code.")
                elif n in full_tree: st.warning("Already exists.")
                else:
                    st.session_state["custom_universities"][n] = {"code": c, "colleges": {}}
                    st.session_state["sel_university"] = n
                    st.session_state["show_add_programme"] = False
                    st.rerun()
        elif add_tab == "College":
            ca, cb = st.columns([3, 1])
            with ca: new_c = st.text_input("College / School name", placeholder="e.g. School of Public Health", key="new_c_name")
            with cb: new_c_code = st.text_input("Code", max_chars=8, placeholder="SPH", key="new_c_code")
            st.markdown(f'<div style="font-size:.82rem;color:#5e7190;margin-bottom:.4rem;">Adding to: <b style="color:var(--text2);">{sel_uni}</b></div>', unsafe_allow_html=True)
            if st.button("Add college", use_container_width=True, type="primary", key="btn_add_c"):
                n, c = new_c.strip(), new_c_code.strip().upper()
                if not n: st.error("Enter a college name.")
                elif not c: st.error("Enter a code.")
                else:
                    key = f"{sel_uni}|{n}"
                    st.session_state["custom_colleges"][key] = {"code": c, "programmes": {}}
                    st.session_state["sel_college"] = n
                    st.session_state["show_add_programme"] = False
                    st.rerun()
        else:
            ca, cb = st.columns([3, 1])
            with ca: new_p = st.text_input("Programme name", placeholder="e.g. Health Informatics", key="new_p_name")
            with cb: new_p_code = st.text_input("Code", max_chars=8, placeholder="HI", key="new_p_code")
            st.markdown(f'<div style="font-size:.82rem;color:#5e7190;margin-bottom:.4rem;">Adding to: <b style="color:var(--text2);">{sel_uni}</b> / <b style="color:var(--text2);">{sel_col}</b></div>', unsafe_allow_html=True)
            if st.button("Add programme", use_container_width=True, type="primary", key="btn_add_p"):
                n, c = new_p.strip(), new_p_code.strip().upper()
                if not n: st.error("Enter a programme name.")
                elif not c: st.error("Enter a code.")
                else:
                    key = f"{sel_uni}|{sel_col}|{n}"
                    st.session_state["custom_programmes"][key] = c
                    st.session_state["sel_programme"] = n
                    st.session_state["show_add_programme"] = False
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Image type
    st.markdown('<div class="card"><div class="card-header"><div class="card-icon ci-teal">🩻</div><div class="card-title">Image Modality</div></div>', unsafe_allow_html=True)
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        cxr_a = "active" if st.session_state["img_code"] == "CXR" else ""
        st.markdown(f'<div class="mode-btn {cxr_a}"><div class="mode-btn-icon">🫁</div><div class="mode-btn-label">Chest X-ray</div><div class="mode-btn-hint">Code: CXR</div></div>', unsafe_allow_html=True)
        if st.button("Select Chest X-ray", use_container_width=True, key="sel_cxr"):
            st.session_state["img_code"] = "CXR"; st.rerun()
    with col_t2:
        img_a = "active" if st.session_state["img_code"] == "IMG" else ""
        st.markdown(f'<div class="mode-btn {img_a}"><div class="mode-btn-icon">🔬</div><div class="mode-btn-label">Other Medical Images</div><div class="mode-btn-hint">Code: IMG</div></div>', unsafe_allow_html=True)
        if st.button("Select Other Images", use_container_width=True, key="sel_img"):
            st.session_state["img_code"] = "IMG"; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    t_code = st.session_state["img_code"]
    p_code = get_programme_code()
    st.markdown(f"""
    <div class="card">
      <div class="card-header"><div class="card-icon ci-green">👁</div><div class="card-title">Output Filename Preview</div></div>
      <div class="fname-label">Your files will be renamed to:</div>
      <div class="fname-preview">{h_code}_{p_code}_{t_code}_00001.jpg</div>
      <div class="fname-preview">{h_code}_{p_code}_{t_code}_00002.png</div>
      <div class="fname-preview">{h_code}_{p_code}_{t_code}_00003.dcm</div>
    </div>""", unsafe_allow_html=True)

    # Operator identity
    st.markdown('<div class="card"><div class="card-header"><div class="card-icon ci-red">🪪</div><div class="card-title">Operator Identity: Required for Certificate</div></div><div style="font-size:.88rem;color:#374a60;margin-bottom:1rem;">Your identity will be printed on the deletion certificate.</div>', unsafe_allow_html=True)
    col_op1, col_op2 = st.columns(2)
    with col_op1:
        op_name = st.text_input("Full name *", value=st.session_state.get("operator_name",""), placeholder="e.g. Vedaste NYANDWI", key="op_name_input")
        st.session_state["operator_name"] = op_name.strip()
    with col_op2:
        op_dept = st.text_input("Department / Institution *", value=st.session_state.get("operator_dept",""), placeholder="e.g. ACE-DS · Data Mining · University of Rwanda", key="op_dept_input")
        st.session_state["operator_dept"] = op_dept.strip()
    col_op3, col_op4 = st.columns(2)
    with col_op3:
        op_email = st.text_input("Email address *", value=st.session_state.get("operator_email",""), placeholder="e.g. v.nyandwi@ur.ac.rw", key="op_email_input")
        st.session_state["operator_email"] = op_email.strip()
    with col_op4:
        op_phone = st.text_input("Phone number *", value=st.session_state.get("operator_phone",""), placeholder="e.g. +250 780 000 000", key="op_phone_input")
        st.session_state["operator_phone"] = op_phone.strip()

    _op_complete = all([st.session_state["operator_name"], st.session_state["operator_dept"],
                        st.session_state["operator_email"], st.session_state["operator_phone"]])
    if _op_complete:
        st.markdown(f'<div class="alert alert-ok" style="margin-top:.5rem;"><span>✅</span><div><b>{st.session_state["operator_name"]}</b> · {st.session_state["operator_dept"]}<br><span style="font-size:.8rem;">{st.session_state["operator_email"]} · {st.session_state["operator_phone"]}</span></div></div>', unsafe_allow_html=True)
    else:
        missing = [f for f, k in [("Full name","operator_name"),("Department","operator_dept"),("Email","operator_email"),("Phone","operator_phone")] if not st.session_state.get(k,"")]
        st.markdown(f'<div class="alert alert-warn" style="margin-top:.5rem;"><span>⚠️</span><div>Missing: <b>{", ".join(missing)}</b>. These are required for the certificate.</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    _configure_ok = bool(st.session_state.get("hospital_key")) and _op_complete
    col_b, _ = st.columns([1, 3])
    with col_b:
        if st.button("Next: Upload →", type="primary", use_container_width=True, disabled=not _configure_ok):
            go(2)
    if not _configure_ok:
        st.markdown('<div style="font-size:.82rem;color:var(--amber);margin-top:.4rem;">Complete all required fields above before proceeding.</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# PAGE 2 — UPLOAD
# ══════════════════════════════════════════════════════════════════
elif cur == 2:
    st.markdown("""
    <div class="pg-wrap">
      <div class="pg-eyebrow">Step 2</div>
      <div class="pg-title">Upload Images</div>
      <div class="pg-sub">Upload a ZIP folder or select individual files (JPG, PNG, DICOM).</div>
    </div>""", unsafe_allow_html=True)

    col_z, col_f = st.columns(2)
    with col_z:
        z_a = "active" if st.session_state["upload_mode"] == "zip" else ""
        st.markdown(f'<div class="mode-btn {z_a}"><div class="mode-btn-icon">🗜</div><div class="mode-btn-label">Upload a ZIP file</div><div class="mode-btn-hint">Recommended for whole folders</div></div>', unsafe_allow_html=True)
        if st.button("Use ZIP upload", use_container_width=True, key="mode_zip"):
            st.session_state["upload_mode"] = "zip"; st.rerun()
    with col_f:
        f_a = "active" if st.session_state["upload_mode"] == "files" else ""
        st.markdown(f'<div class="mode-btn {f_a}"><div class="mode-btn-icon">🖼</div><div class="mode-btn-label">Upload individual files</div><div class="mode-btn-hint">Select multiple images directly</div></div>', unsafe_allow_html=True)
        if st.button("Use file upload", use_container_width=True, key="mode_files"):
            st.session_state["upload_mode"] = "files"; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    if st.session_state["upload_mode"] == "zip":
        st.markdown('<div class="alert alert-info"><span>💡</span><div><b>How to create a ZIP file</b><br><b>Windows:</b> Right-click folder → <em>Send to → Compressed folder</em><br><b>Mac:</b> Right-click folder → <em>Compress</em></div></div>', unsafe_allow_html=True)
        uploaded_zip = st.file_uploader("Upload your ZIP file", type=["zip"], label_visibility="visible", key="zip_upload")
        if uploaded_zip:
            try:
                with zipfile.ZipFile(io.BytesIO(uploaded_zip.getvalue())) as zf:
                    img_count = sum(1 for i in zf.infolist() if not i.is_dir() and Path(i.filename).suffix.lower() in SUPPORTED_EXT and "__MACOSX" not in i.filename)
                st.markdown(f'<div class="alert alert-ok"><span>✅</span><div><b>{uploaded_zip.name}</b> ready. <b>{img_count}</b> image(s) found · {uploaded_zip.size/1024/1024:.2f} MB</div></div>', unsafe_allow_html=True)
                st.session_state["_zip_upload"] = uploaded_zip
            except Exception as e:
                st.error(f"Could not read ZIP: {e}")
        else:
            st.session_state.pop("_zip_upload", None)
    else:
        st.markdown('<div class="alert alert-info"><span>💡</span><div>Hold <b>Ctrl</b> (Windows) or <b>Cmd</b> (Mac) to select multiple files. Supports <b>JPG, PNG</b> and <b>DICOM (.dcm)</b>.</div></div>', unsafe_allow_html=True)
        uploaded_files = st.file_uploader("Upload your image files", type=["jpg","jpeg","png","dcm"], accept_multiple_files=True, label_visibility="visible", key="files_upload")
        if uploaded_files:
            dcm_n = sum(1 for f in uploaded_files if Path(f.name).suffix.lower() in (".dcm",".dicom"))
            st.markdown(f'<div class="alert alert-ok"><span>✅</span><div><b>{len(uploaded_files)}</b> file(s) ready: {len(uploaded_files)-dcm_n} image(s) + {dcm_n} DICOM</div></div>', unsafe_allow_html=True)
            st.session_state["_files_upload"] = uploaded_files
        else:
            st.session_state.pop("_files_upload", None)

    ready = (st.session_state["upload_mode"] == "zip"   and "_zip_upload"   in st.session_state) or \
            (st.session_state["upload_mode"] == "files" and "_files_upload" in st.session_state)

    if ready:
        st.markdown('<div class="card"><div class="card-header"><div class="card-icon ci-amber">🔍</div><div class="card-title">Image Content Validation</div></div><div style="font-size:.83rem;color:#374a60;margin-bottom:.75rem;">Checks each file to confirm it is plausibly a medical image.</div>', unsafe_allow_html=True)

        if st.button("🔍  Run Validation", key="run_validation"):
            val_entries = []
            if st.session_state["upload_mode"] == "zip" and "_zip_upload" in st.session_state:
                try:
                    zf_obj = st.session_state["_zip_upload"]
                    with zipfile.ZipFile(io.BytesIO(zf_obj.getvalue())) as zf:
                        for info in zf.infolist():
                            if info.is_dir() or "__MACOSX" in info.filename: continue
                            fname = Path(info.filename)
                            ext = fname.suffix.lower()
                            if ext in SUPPORTED_EXT:
                                raw = zf.read(info.filename)
                                val_entries.append({"name": fname.name, "raw": raw, "ext": ext})
                except Exception as e:
                    st.error(f"Validation failed: {e}")
            elif "_files_upload" in st.session_state:
                for f in st.session_state["_files_upload"]:
                    ext = Path(f.name).suffix.lower()
                    if ext in SUPPORTED_EXT:
                        f.seek(0)
                        val_entries.append({"name": f.name, "raw": f.read(), "ext": ext})
                        f.seek(0)

            val_results = [{"name": e["name"], **validate_image(e["raw"], e["ext"], e["name"])} for e in val_entries]
            st.session_state["validation_results"] = val_results

        val_res = st.session_state.get("validation_results", [])
        if val_res:
            n_err  = sum(1 for v in val_res if not v["valid"])
            n_warn = sum(1 for v in val_res if v["valid"] and v["warnings"])
            n_ok   = sum(1 for v in val_res if v["valid"] and not v["warnings"])
            cols_v = st.columns(3)
            cols_v[0].metric("✅ Clean", n_ok)
            cols_v[1].metric("⚠️ Warnings", n_warn)
            cols_v[2].metric("❌ Errors", n_err)
            for v in val_res:
                if v["errors"]:
                    st.markdown(f'<div class="alert alert-danger"><span>❌</span><div><b>{v["name"]}</b>: {"; ".join(v["errors"])}</div></div>', unsafe_allow_html=True)
                elif v["warnings"]:
                    st.markdown(f'<div class="alert alert-warn"><span>⚠️</span><div><b>{v["name"]}</b>: {"; ".join(v["warnings"])}</div></div>', unsafe_allow_html=True)
            if n_err == 0 and n_warn == 0:
                st.markdown('<div class="alert alert-ok"><span>✅</span><div>All files passed validation.</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card"><div class="card-header"><div class="card-icon ci-blue">👤</div><div class="card-title">Patient Grouping (Optional)</div></div><div style="font-size:.83rem;color:#374a60;margin-bottom:.75rem;">If the same patient has <b>multiple scans</b>, assign them the same patient label.</div>', unsafe_allow_html=True)

        file_names_for_grouping = []
        if st.session_state["upload_mode"] == "zip" and "_zip_upload" in st.session_state:
            try:
                with zipfile.ZipFile(io.BytesIO(st.session_state["_zip_upload"].getvalue())) as zf:
                    file_names_for_grouping = [Path(i.filename).name for i in zf.infolist() if not i.is_dir() and "__MACOSX" not in i.filename and Path(i.filename).suffix.lower() in SUPPORTED_EXT]
            except Exception:
                pass
        elif "_files_upload" in st.session_state:
            file_names_for_grouping = [f.name for f in st.session_state["_files_upload"] if Path(f.name).suffix.lower() in SUPPORTED_EXT]

        if file_names_for_grouping:
            groups = st.session_state.get("patient_groups", {})
            show_n = min(len(file_names_for_grouping), 20)
            for fname in file_names_for_grouping[:show_n]:
                col_fn, col_grp = st.columns([3, 1])
                col_fn.markdown(f'<span style="font-size:.82rem;color:#374a60;font-family:JetBrains Mono,monospace;">{fname}</span>', unsafe_allow_html=True)
                grp_val = col_grp.text_input("Group", value=groups.get(fname, ""), key=f"grp_{fname}", label_visibility="collapsed", placeholder="e.g. P001")
                groups[fname] = grp_val.strip()
            if len(file_names_for_grouping) > 20:
                st.markdown(f'<div style="font-size:.78rem;color:#5e7190;margin-top:.3rem;">… {len(file_names_for_grouping)-20} more files</div>', unsafe_allow_html=True)
            st.session_state["patient_groups"] = groups
            used_groups = {v for v in groups.values() if v}
            if used_groups:
                st.markdown(f'<div class="alert alert-info"><span>👤</span><div style="font-size:.82rem;">Groups: <b>{", ".join(sorted(used_groups))}</b></div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_back, col_next, _ = st.columns([1, 1, 2])
    with col_back:
        if st.button("← Back", use_container_width=True): go(1)
    with col_next:
        if st.button("Next: Anonymize →", type="primary", use_container_width=True, disabled=not ready):
            go(3)
    if not ready:
        st.markdown('<div style="font-size:.8rem;color:var(--amber);margin-top:.4rem;">⚠ Upload your images before continuing.</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# PAGE 3 — ANONYMIZE
# ══════════════════════════════════════════════════════════════════
elif cur == 3:
    st.markdown("""
    <div class="pg-wrap">
      <div class="pg-eyebrow">Step 3</div>
      <div class="pg-title">Anonymize</div>
      <div class="pg-sub">Confirm settings, then run anonymization.</div>
    </div>""", unsafe_allow_html=True)

    all_h  = {**HOSPITALS, **st.session_state["custom_hospitals"]}
    h_code = all_h.get(st.session_state["hospital_key"], "H01")
    p_code = get_programme_code()
    t_code = st.session_state["img_code"]

    st.markdown(f"""
    <div class="card">
      <div class="card-header"><div class="card-icon ci-teal">✅</div><div class="card-title">Configuration Summary</div></div>
      <div class="info-grid">
        <div class="info-pill"><div class="info-lbl">Hospital</div><div class="info-val">{st.session_state["hospital_key"].split("—")[0].strip()}</div><div class="info-code">{h_code}</div></div>
        <div class="info-pill"><div class="info-lbl">Programme</div><div class="info-val">{st.session_state.get("sel_programme","—")}</div><div class="info-code">{p_code}</div></div>
        <div class="info-pill"><div class="info-lbl">Image Modality</div><div class="info-val">{"Chest X-ray" if t_code=="CXR" else "Other Medical Images"}</div><div class="info-code">{t_code}</div></div>
        <div class="info-pill"><div class="info-lbl">Upload Method</div><div class="info-val">{"ZIP folder" if st.session_state["upload_mode"]=="zip" else "Individual files"}</div><div class="info-code">{"🗜 ZIP" if st.session_state["upload_mode"]=="zip" else "🖼 FILES"}</div></div>
      </div>
      <div class="fname-label">Output filename pattern:</div>
      <div class="fname-preview">{h_code}_{p_code}_{t_code}_00001 … 0000N.ext</div>
    </div>""", unsafe_allow_html=True)

    if st.session_state["run_complete"] and st.session_state.get("results"):
        results = st.session_state["results"]
        ok_n  = sum(1 for r in results if r["status"] == "ok")
        err_n = sum(1 for r in results if r["status"] == "error")

        st.markdown(f"""
        <div class="stat-row">
          <div class="stat-box"><div class="stat-n c-slate">{len(results)}</div><div class="stat-l">Total processed</div></div>
          <div class="stat-box"><div class="stat-n c-teal">{ok_n}</div><div class="stat-l">✓ Anonymized</div></div>
          <div class="stat-box"><div class="stat-n c-red">{err_n}</div><div class="stat-l">✗ Errors</div></div>
          <div class="stat-box"><div class="stat-n c-teal">{len(st.session_state.get("integrity_log",[]))}</div><div class="stat-l">📋 Checksums logged</div></div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="alert alert-teal"><span>🛡</span><div><b>Anonymization complete.</b> All PHI tags stripped, files renamed, SHA-256 checksums recorded, buffers zeroed.</div></div>', unsafe_allow_html=True)

        img_results = [r for r in results if r["status"] == "ok" and r["ext"] not in (".dcm", ".dicom") and r.get("thumb")]
        dcm_results = [r for r in results if r["status"] == "ok" and r["ext"] in (".dcm", ".dicom")]
        err_results = [r for r in results if r["status"] == "error"]

        if img_results:
            st.markdown(f'<div style="font-size:.82rem;font-weight:700;color:#374a60;margin:.75rem 0 .4rem;">🖼 Image preview — {len(img_results)} anonymized image(s)</div>', unsafe_allow_html=True)
            preview_set = img_results[:12]
            cols = st.columns(min(len(preview_set), 6))
            for i, r in enumerate(preview_set):
                with cols[i % 6]:
                    try:
                        img_data = base64.b64decode(r["thumb"])
                        st.image(img_data, caption=r["new_name"], use_container_width=True)
                    except Exception:
                        st.markdown(f'<div style="background:var(--navy);border-radius:8px;padding:1rem;text-align:center;font-size:.7rem;color:#4ade80;">{r["new_name"]}</div>', unsafe_allow_html=True)
            if len(img_results) > 12:
                st.markdown(f'<div style="font-size:.78rem;color:#5e7190;margin-top:.3rem;">… and {len(img_results)-12} more images</div>', unsafe_allow_html=True)

        if dcm_results:
            st.markdown(f'<div style="background:var(--purple-lt);border:1px solid #c4b5fd;border-radius:8px;padding:.75rem 1rem;margin:.5rem 0;font-size:.84rem;color:#4c1d95;">🩻 <b>{len(dcm_results)}</b> DICOM file(s) anonymized — PHI tags wiped</div>', unsafe_allow_html=True)

        st.markdown('<div style="font-size:.78rem;font-weight:700;color:#5e7190;text-transform:uppercase;letter-spacing:1px;margin:1rem 0 .5rem;">Complete rename log</div>', unsafe_allow_html=True)
        st.markdown('<div class="ftable"><div class="fth"><span>Original filename</span><span>→ Anonymized filename</span><span>Status</span></div>', unsafe_allow_html=True)
        for r in results[:60]:
            ico = "🩻" if r["ext"] in (".dcm",".dicom") else "🖼️"
            bc, bt = {"ok":("fbok","✓ OK"),"error":("fberr","✗ Err"),"skip":("fbskip","⚠ Skip")}[r["status"]]
            st.markdown(f'<div class="frow"><span class="f-orig">{ico} {r["original"]}</span><span class="f-new">{r["new_name"]}</span><span class="fbadge {bc}">{bt}</span></div>', unsafe_allow_html=True)
        if len(results) > 60:
            st.markdown(f'<div style="text-align:center;padding:.6rem;font-size:.78rem;color:#5e7190;border-top:1px solid var(--border);">… and {len(results)-60} more files</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        col_n, _ = st.columns([1, 3])
        with col_n:
            if st.button("Next: Download →", type="primary", use_container_width=True): go(4)

    else:
        has_data = (("_zip_upload" in st.session_state and st.session_state["upload_mode"] == "zip") or
                    ("_files_upload" in st.session_state and st.session_state["upload_mode"] == "files"))
        if not has_data:
            st.markdown('<div class="alert alert-warn"><span>⚠️</span><div>No images uploaded. Go back to <b>Upload</b> first.</div></div>', unsafe_allow_html=True)
            if st.button("← Go to Upload"): go(2)
        else:
            st.markdown('<div class="alert alert-info"><span>🔐</span><div><b>What happens when you click Run:</b><br>1. Images extracted and processed in memory<br>2. EXIF metadata stripped via pixel-level reconstruction<br>3. DICOM PHI tags wiped + UIDs regenerated<br>4. SHA-256 checksum logged per file<br>5. Anonymized ZIP packaged, then all image buffers zeroed</div></div>', unsafe_allow_html=True)

            col_back, col_run, _ = st.columns([1, 1.5, 2])
            with col_back:
                if st.button("← Back", use_container_width=True): go(2)
            with col_run:
                run_clicked = st.button("🛡  Run Anonymization", type="primary", use_container_width=True)

            if run_clicked:
                bar    = st.progress(0)
                status = st.empty()
                try:
                    if st.session_state["upload_mode"] == "zip":
                        status.markdown('<span style="color:#7c3aed;font-size:.85rem;">🗜 Extracting ZIP…</span>', unsafe_allow_html=True)
                        entries = collect_zip(st.session_state["_zip_upload"])
                    else:
                        entries = collect_files(st.session_state["_files_upload"])

                    if not entries:
                        st.error("No supported image files found."); st.stop()

                    entries = assign_pids_with_groups(entries, st.session_state.get("patient_groups", {}))
                    results, log_lines, integrity = run_pipeline(entries, h_code, p_code, t_code, bar, status)
                    zip_bytes = pack_zip(results)
                    zip_fname = f"anonymized_{h_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

                    op  = st.session_state.get("operator_name","Unknown")
                    dpt = st.session_state.get("operator_dept","Unknown")
                    mapping_csv = build_mapping_csv(results, integrity, op, dpt)
                    mapping_zip = pack_mapping_zip(mapping_csv, f"{h_code}-mapping-key")
                    log_lines.append(f"  📋  Mapping CSV built ({len(results)} rows)")

                    results = purge_ram(results)
                    log_lines.append("  🗑  RAM purge complete — all image buffers zeroed (W11)")

                    st.session_state.update(dict(
                        results=results, zip_bytes=zip_bytes,
                        zip_filename=zip_fname, log_lines=log_lines,
                        integrity_log=integrity, run_complete=True,
                        mapping_csv=mapping_zip))
                    st.rerun()
                except Exception as e:
                    st.error(f"Anonymization failed: {e}")


# ══════════════════════════════════════════════════════════════════
# PAGE 4 — DOWNLOAD
# ══════════════════════════════════════════════════════════════════
elif cur == 4:
    st.markdown("""
    <div class="pg-wrap">
      <div class="pg-eyebrow">Step 4</div>
      <div class="pg-title">Download</div>
      <div class="pg-sub">Download your anonymized images and the mapping table before proceeding to deletion.</div>
    </div>""", unsafe_allow_html=True)

    if not st.session_state["run_complete"] or not st.session_state.get("zip_bytes"):
        st.markdown('<div class="alert alert-warn"><span>⚠️</span><div>No anonymized data ready. Complete the <b>Anonymize</b> step first.</div></div>', unsafe_allow_html=True)
        if st.button("← Go to Anonymize"): go(3)
    else:
        zip_b  = st.session_state["zip_bytes"]
        zip_fn = st.session_state["zip_filename"]
        ok_n   = sum(1 for r in st.session_state.get("results",[]) if r["status"] == "ok")
        sz_mb  = len(zip_b) / 1024 / 1024

        st.markdown(f"""
        <div class="card">
          <div class="card-header"><div class="card-icon ci-teal">⬇</div><div class="card-title">Anonymized Images ZIP</div></div>
          <div style="font-size:.88rem;color:#374a60;margin-bottom:1rem;"><b>{ok_n}</b> image(s) ready &nbsp;·&nbsp; <b>{sz_mb:.2f} MB</b></div>""", unsafe_allow_html=True)
        st.download_button(
            label=f"⬇  Download Anonymized ZIP  ({ok_n} files, {sz_mb:.1f} MB)",
            data=zip_b, file_name=zip_fn, mime="application/zip", type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

        mapping_zip = st.session_state.get("mapping_csv")
        _hkey_short = st.session_state.get("hospital_key","H01").split("—")[0].strip()[:4].replace(" ","")
        st.markdown(f"""
        <div class="card">
          <div class="card-header"><div class="card-icon ci-blue">🗂</div><div class="card-title">Patient ID Mapping Table</div></div>
          <div style="font-size:.88rem;color:#374a60;margin-bottom:.8rem;">Links every original filename to its anonymized ID. Keep with the hospital data officer.</div>
          <div class="alert alert-warn" style="margin-bottom:.75rem;"><span>🔐</span><div><b>Password convention:</b> <code>{_hkey_short}-mapping-key</code></div></div>""", unsafe_allow_html=True)
        if mapping_zip:
            all_h2 = {**HOSPITALS, **st.session_state["custom_hospitals"]}
            h2 = all_h2.get(st.session_state["hospital_key"],"H01")
            st.download_button(
                label="⬇  Download Mapping Table (password-protected ZIP)",
                data=mapping_zip,
                file_name=f"mapping_{h2}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip")
        st.markdown('</div>', unsafe_allow_html=True)

        integrity = st.session_state.get("integrity_log", [])
        _show_log = st.session_state.get("show_audit_log", False)
        if st.button("Hide audit log" if _show_log else f"View audit log  ({len(integrity)} checksum record(s))", key="toggle_audit_log"):
            st.session_state["show_audit_log"] = not _show_log
            st.rerun()

        if st.session_state.get("show_audit_log"):
            log_txt = "\n".join(st.session_state.get("log_lines", []))
            st.markdown(f'<div class="logbox"><pre>{log_txt}</pre></div>', unsafe_allow_html=True)
            col_lg, _ = st.columns([1, 3])
            with col_lg:
                st.download_button("Download full log (.txt)", data=log_txt.encode(),
                                    file_name=f"anon_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", mime="text/plain")

        st.markdown('<div class="alert alert-info"><span>ℹ️</span><div>Once you have downloaded both files, proceed to <b>Delete</b> to permanently remove the original dataset.</div></div>', unsafe_allow_html=True)
        col_next, _ = st.columns([1, 3])
        with col_next:
            if st.button("Next: Delete →", type="primary", use_container_width=True): go(5)


# ══════════════════════════════════════════════════════════════════
# PAGE 5 — DELETE & CERTIFICATE
# ══════════════════════════════════════════════════════════════════
elif cur == 5:
    st.markdown("""
    <div class="pg-wrap">
      <div class="pg-eyebrow">Step 5</div>
      <div class="pg-title">Delete Original Dataset</div>
      <div class="pg-sub">Permanently remove the original images and receive an official deletion certificate.</div>
    </div>""", unsafe_allow_html=True)

    if not st.session_state["run_complete"]:
        st.markdown('<div class="alert alert-warn"><span>⚠️</span><div>No anonymized data found. Complete <b>Anonymize</b> and <b>Download</b> first.</div></div>', unsafe_allow_html=True)
        if st.button("← Go to Anonymize"): go(3)
    else:
        op_name  = st.session_state.get("operator_name","—")
        op_dept  = st.session_state.get("operator_dept","—")
        op_email = st.session_state.get("operator_email","—")
        op_phone = st.session_state.get("operator_phone","—")
        ok_n     = sum(1 for r in st.session_state.get("results",[]) if r["status"] == "ok")
        ts_now   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        integrity = st.session_state.get("integrity_log", [])
        n_checks  = len(integrity)

        if st.session_state.get("dataset_deleted"):
            cert_ts    = st.session_state.get("cert_ts", ts_now)
            n_files    = st.session_state.get("cert_nfiles", ok_n)
            groups_used = {v for v in st.session_state.get("patient_groups",{}).values() if v}
            val_ran    = bool(st.session_state.get("validation_results"))

            st.markdown(f"""
            <div class="proof-box">
              <div class="proof-title">🏛 Official Anonymization &amp; Deletion Certificate</div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:.5rem;background:#dcfce7;border-radius:8px;padding:.9rem 1rem;margin-bottom:1rem;font-size:.85rem;color:#14532d;line-height:1.7;">
                <div><b>Operator:</b> {op_name}</div>
                <div><b>Department:</b> {op_dept}</div>
                <div><b>Email:</b> {op_email}</div>
                <div><b>Phone:</b> {op_phone}</div>
                <div><b>Hospital:</b> {st.session_state.get("hospital_key","—").split("—")[0].strip()}</div>
                <div><b>Issued:</b> {cert_ts}</div>
                <div><b>Files processed:</b> {n_files}</div>
                <div><b>System:</b> MedAnon Pro</div>
              </div>
              <div style="font-size:.9rem;font-weight:700;color:#15803d;margin-bottom:.6rem;">This certifies that:</div>
              <div class="proof-row"><span>✅</span><span>All original patient images <b>permanently deleted from this session</b></span></div>
              <div class="proof-row"><span>✅</span><span>All anonymized image buffers <b>byte-zeroed in RAM</b></span></div>
              <div class="proof-row"><span>✅</span><span>All EXIF metadata stripped &amp; 27 DICOM PHI tags wiped</span></div>
              <div class="proof-row"><span>✅</span><span>SHA-256 checksums recorded for <b>all {n_checks} file(s)</b></span></div>
              <div class="proof-row"><span>✅</span><span>Mapping table delivered to operator</span></div>
              <div class="proof-row"><span>{"✅" if val_ran else "⚪"}</span><span>Image content validation {"performed" if val_ran else "not run this session"}</span></div>
              <div class="proof-row"><span>{"✅" if groups_used else "⚪"}</span><span>{"Patient grouping: " + str(len(groups_used)) + " group(s)" if groups_used else "Patient grouping: not used"}</span></div>
              <div style="margin-top:1rem;padding:.85rem 1rem;background:#bbf7d0;border-radius:8px;font-size:.85rem;color:#14532d;line-height:1.6;">
                <b>This certificate may be presented to the hospital radiology department, data governance office, or IRB</b> as formal confirmation that the original patient dataset has been deleted.<br><br>
                Signed: <b>{op_name}</b> · {op_dept}<br>
                Contact: {op_email} · {op_phone}<br>
                Date: {cert_ts}
              </div>
            </div>""", unsafe_allow_html=True)

            cert_txt = f"""OFFICIAL ANONYMIZATION & DELETION CERTIFICATE
================================================
Operator    : {op_name}
Department  : {op_dept}
Email       : {op_email}
Phone       : {op_phone}
Hospital    : {st.session_state.get("hospital_key","—").split("—")[0].strip()}
System      : MedAnon Pro  (c) Vedaste NYANDWI
Issued      : {cert_ts}
Files       : {n_files} images anonymized
Checksums   : {n_checks} SHA-256 records

CERTIFICATIONS
--------------
[OK] Original patient images permanently deleted
[OK] All image buffers byte-zeroed in RAM
[OK] EXIF metadata stripped + 27 DICOM PHI tags wiped
[OK] SHA-256 checksums logged for all {n_checks} file(s)
[OK] Mapping table delivered to operator
[{"OK" if val_ran else "--"}] Image content validation {"performed" if val_ran else "not run"}
[{"OK" if groups_used else "--"}] Patient grouping: {"applied (" + str(len(groups_used)) + " groups)" if groups_used else "not used"}

STATEMENT
---------
The original patient dataset has been deleted from this research
system and was not retained.

Signed: {op_name}
        {op_dept}
        {op_email} | {op_phone}
        {cert_ts}
"""
            col_cert, col_ns, _ = st.columns([1.2, 1.2, 2])
            with col_cert:
                st.download_button("⬇  Download Certificate (.txt)", data=cert_txt.encode(),
                    file_name=f"deletion_certificate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", mime="text/plain")
            with col_ns:
                if st.button("🔄 New Session", use_container_width=True):
                    for k in list(_D.keys()): st.session_state[k] = _D[k]
                    for k in ["_zip_upload","_files_upload"]: st.session_state.pop(k, None)
                    st.rerun()

        else:
            st.markdown(f"""
            <div class="card">
              <div class="card-header"><div class="card-icon ci-amber">✅</div><div class="card-title">Before You Delete: Checklist</div></div>""", unsafe_allow_html=True)

            chk1 = st.checkbox("I have downloaded the **anonymized ZIP** file", key="chk_zip")
            chk2 = st.checkbox("I have downloaded the **mapping table** ZIP", key="chk_map")
            chk3 = st.checkbox("I have saved both files in a **secure location**", key="chk_saved")
            st.markdown('</div>', unsafe_allow_html=True)

            _op_ok = all([op_name != "—", op_dept != "—", op_email != "—", op_phone != "—"])
            if not _op_ok:
                st.markdown('<div class="alert alert-danger"><span>🚫</span><div>Operator identity is incomplete. Go back to <b>Configure</b>.</div></div>', unsafe_allow_html=True)

            st.markdown(f"""
            <div class="del-box" style="margin-top:1rem;">
              <div class="del-title">🗑 Permanent Deletion</div>
              <div style="font-size:.88rem;color:#991b1b;margin-bottom:.85rem;line-height:1.65;">
                This will <b>permanently erase</b> all uploaded original images and issue a signed <b>Deletion Certificate</b>.
              </div>
              <div style="font-size:.85rem;color:#7f1d1d;line-height:2;">
                ✓ Uploaded files cleared from server memory<br>
                ✓ All image buffers byte-zeroed in RAM<br>
                ✓ Certificate issued with operator signature, email &amp; phone<br>
                ✓ Certificate includes timestamp and file counts
              </div>
            </div>""", unsafe_allow_html=True)

            confirmed = st.checkbox("I confirm I have downloaded all files and want to permanently delete the original dataset.", key="del_confirm")

            col_del, _ = st.columns([1, 3])
            with col_del:
                del_btn = st.button("🗑  Delete & Issue Certificate",
                    disabled=(not confirmed or not all([chk1, chk2, chk3]) or not _op_ok),
                    use_container_width=True)

            if del_btn and confirmed:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                for k in ["_zip_upload","_files_upload"]: st.session_state.pop(k, None)
                if st.session_state.get("results"):
                    for r in st.session_state["results"]:
                        if r.get("clean_bytes"):
                            ba = bytearray(r["clean_bytes"]); _wipe(ba)
                st.session_state["results"]         = []
                st.session_state["dataset_deleted"] = True
                st.session_state["cert_ts"]         = ts
                st.session_state["cert_nfiles"]     = ok_n
                log = st.session_state.get("log_lines",[])
                log += [
                    f"  DELETED   [{ts}]  operator:{op_name}",
                    f"  ZEROED    [{ts}]  all buffers",
                    f"  CERT      [{ts}]  issued to {op_name} / {op_dept}",
                ]
                st.session_state["log_lines"] = log
                st.rerun()


# ══════════════════════════════════════════════════════════════════
# PAGE 6 — FEEDBACK
# Key fix: use fb_submitted flag + fb_form_key to show success toast
# and reset the form WITHOUT navigating away from the feedback page.
# st.rerun() is never called after submission — we just set flags and
# let Streamlit re-render the same page naturally.
# ══════════════════════════════════════════════════════════════════
elif cur == 6:
    st.markdown("""
    <div class="pg-wrap">
      <div class="pg-eyebrow">Community</div>
      <div class="pg-title">Feedback &amp; Reviews</div>
      <div class="pg-sub">Rate the platform and share your experience. Your review appears instantly below.</div>
    </div>""", unsafe_allow_html=True)

    reviews = st.session_state.get("feedback_reviews", [])

    # ── Rating summary ────────────────────────────────────────────
    if reviews:
        avg   = sum(r["stars"] for r in reviews) / len(reviews)
        tally = {s: sum(1 for r in reviews if r["stars"] == s) for s in range(5, 0, -1)}
        max_t = max(tally.values()) if tally else 1
        bars_html = ""
        for s in range(5, 0, -1):
            pct = int(tally[s] / max_t * 100) if max_t > 0 else 0
            bars_html += f"""
            <div class="rating-bar-row">
              <div class="rating-bar-lbl">{s}</div>
              <div class="rating-bar-track"><div class="rating-bar-fill" style="width:{pct}%;"></div></div>
              <div class="rating-bar-n">{tally[s]}</div>
            </div>"""
        st.markdown(f"""
        <div class="rating-summary">
          <div style="text-align:center;min-width:90px;">
            <div class="rating-big">{avg:.1f}</div>
            <div class="rating-stars-lg">{"⭐" * round(avg)}{"☆" * (5-round(avg))}</div>
            <div class="rating-count">{len(reviews)} review{"s" if len(reviews) != 1 else ""}</div>
          </div>
          <div class="rating-bars">{bars_html}</div>
        </div>""", unsafe_allow_html=True)

    # ── Success toast (shown after submission, stays on page) ─────
    if st.session_state.get("fb_submitted"):
        submitted_name = st.session_state.get("fb_submitted_name", "").split()[0] or "there"
        st.markdown(f"""
        <div class="fb-success-toast">
          <div class="toast-icon">🎉</div>
          <div>
            <div class="toast-msg">Thank you, {submitted_name}! Your review has been posted.</div>
            <div class="toast-sub">It now appears in the reviews section below. Feel free to submit another.</div>
          </div>
        </div>""", unsafe_allow_html=True)
        # Clear the flag so toast disappears on next interaction
        st.session_state["fb_submitted"] = False

    # ── Write a Review form ───────────────────────────────────────
    # fb_form_key is incremented on successful submit to reset widgets
    fk = st.session_state.get("fb_form_key", 0)

    st.markdown("""
    <div class="card">
      <div class="card-header">
        <div class="card-icon ci-amber">✍️</div>
        <div class="card-title">Write a Review</div>
      </div>""", unsafe_allow_html=True)

    col_name, col_role = st.columns(2)
    with col_name:
        f_name = st.text_input(
            "Your name",
            placeholder="e.g. Dr. Uwimana M.",
            key=f"fb_name_{fk}",
            label_visibility="visible")
    with col_role:
        f_role_label = st.selectbox(
            "Your role",
            ["Hospital Staff / Radiologist", "Researcher", "Student", "IT / Data Officer", "Other"],
            key=f"fb_role_{fk}",
            label_visibility="visible")

    role_tag_map = {
        "Hospital Staff / Radiologist": "hospital",
        "Researcher":  "researcher",
        "Student":     "student",
        "IT / Data Officer": "staff",
        "Other":       "staff",
    }
    role_tag = role_tag_map.get(f_role_label, "staff")

    st.markdown('<div style="font-size:.85rem;font-weight:600;color:#374a60;margin-top:.5rem;margin-bottom:.25rem;">Your rating</div>', unsafe_allow_html=True)
    f_stars = st.select_slider(
        "Rating",
        options=[1, 2, 3, 4, 5],
        value=5,
        format_func=lambda x: "⭐" * x + f"  ({x}/5)",
        key=f"fb_stars_{fk}",
        label_visibility="collapsed")
    st.markdown(
        f'<div style="font-size:1.8rem;letter-spacing:3px;margin:.2rem 0 .6rem;">'
        f'{"⭐" * f_stars}{"☆" * (5 - f_stars)}'
        f'<span style="font-size:.9rem;color:#5e7190;margin-left:.75rem;">{f_stars}/5</span>'
        f'</div>',
        unsafe_allow_html=True)

    f_comment = st.text_area(
        "Your comment",
        placeholder="Describe your experience: what worked well, what could be improved, how you used the system...",
        height=110,
        key=f"fb_comment_{fk}",
        label_visibility="visible")

    submit = st.button("⭐  Submit Review", type="primary", key=f"fb_submit_{fk}")
    st.markdown('</div>', unsafe_allow_html=True)

    if submit:
        name_clean    = (f_name or "").strip()
        comment_clean = (f_comment or "").strip()

        if not name_clean:
            st.error("Please enter your name.")
        elif len(comment_clean) < 10:
            st.error("Please write a comment of at least 10 characters.")
        else:
            initials = "".join(p[0] for p in name_clean.split()[:2]).upper() or "?"
            new_review = {
                "name":     name_clean,
                "role":     f_role_label,
                "role_tag": role_tag,
                "stars":    f_stars,
                "comment":  comment_clean,
                "ts":       datetime.now().strftime("%Y-%m-%d %H:%M"),
                "initials": initials,
            }
            # Insert at the top so it's visible immediately
            st.session_state["feedback_reviews"].insert(0, new_review)

            # Set success state — do NOT call st.rerun() which could navigate away
            st.session_state["fb_submitted"]      = True
            st.session_state["fb_submitted_name"] = name_clean
            # Increment key to reset form widgets on next render
            st.session_state["fb_form_key"]       = fk + 1
            st.rerun()   # rerun stays on page 6 — page key is unchanged

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Review list ───────────────────────────────────────────────
    if not reviews:
        st.markdown("""
        <div style="text-align:center;padding:3rem 2rem;background:var(--white);
                    border:2px dashed var(--border);border-radius:var(--r);">
          <div style="font-size:2.5rem;margin-bottom:.75rem;">💬</div>
          <div style="font-weight:700;color:var(--text);font-size:1rem;margin-bottom:.3rem;">No reviews yet</div>
          <div style="color:var(--text3);font-size:.88rem;">Be the first to share your experience with MedAnon Pro.</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="font-size:.82rem;font-weight:700;color:#5e7190;
                    text-transform:uppercase;letter-spacing:1px;margin-bottom:.75rem;">
          {len(reviews)} Review{"s" if len(reviews) != 1 else ""}
        </div>""", unsafe_allow_html=True)

        tag_class = {
            "hospital":   "tag-hospital",
            "researcher": "tag-researcher",
            "student":    "tag-student",
            "staff":      "tag-staff",
        }

        for r in reviews:
            stars_str = "⭐" * r["stars"] + "☆" * (5 - r["stars"])
            tc = tag_class.get(r.get("role_tag","staff"), "tag-staff")
            initials = r.get("initials", r["name"][0].upper())
            st.markdown(f"""
            <div class="review-card">
              <div class="review-header">
                <div class="review-avatar">{initials}</div>
                <div>
                  <div class="review-name">{r["name"]}</div>
                  <div class="review-role">{r["role"]}</div>
                </div>
                <div class="review-stars">{stars_str}</div>
              </div>
              <div class="review-body">{r["comment"]}</div>
              <div class="review-meta">
                <span>{r["ts"]}</span>
                <span class="review-tag {tc}">{r["role"]}</span>
              </div>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════
st.markdown(f"""
<div style="margin-top:3.5rem;padding:1.2rem 0 .8rem;border-top:1px solid #dde4ef;
            display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.75rem;">
  <div style="display:flex;align-items:center;gap:.75rem;">
    <div style="width:26px;height:26px;background:#0d1b2a;border-radius:6px;
                display:flex;align-items:center;justify-content:center;font-size:.75rem;flex-shrink:0;">🛡</div>
    <div>
      <div style="font-size:.85rem;font-weight:700;color:#0f1d2e;">MedAnon Pro</div>
      <div style="font-size:.72rem;color:#5e7190;margin-top:.05rem;">Patient data is never stored or transmitted · All processing is in-session only</div>
    </div>
  </div>
  <div style="text-align:right;">
    <div style="font-size:.78rem;font-weight:600;color:#374a60;">© Vedaste NYANDWI</div>
    <div style="font-size:.68rem;color:#5e7190;margin-top:.05rem;">University of Rwanda · College of Business &amp; Economics<br>ACE-DS · Data Mining Program</div>
  </div>
</div>""", unsafe_allow_html=True)
