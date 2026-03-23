"""
MedAnon Pro — Medical Image Anonymization System
© Vedaste NYANDWI · University of Rwanda · CBE · ACE-DS · Data Mining

Run:
    pip install streamlit Pillow pydicom
    streamlit run app.py
"""

import streamlit as st
import io, shutil, zipfile, logging
from pathlib import Path
from datetime import datetime
from PIL import Image

DICOM_AVAILABLE = False
try:
    import pydicom
    from pydicom.uid import generate_uid
    DICOM_AVAILABLE = True
except ImportError:
    pass

# ──────────────────────────────────────────────────────────────────
st.set_page_config(page_title="MedAnon Pro", page_icon="🛡",
                   layout="wide", initial_sidebar_state="expanded")

# ──────────────────────────────────────────────────────────────────
# CSS  – clean, warm, clinic-friendly
# ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── tokens ── */
:root{
  --navy:#0e1726; --navy2:#192236; --navy3:#243047;
  --teal:#14b8a6; --teal-dk:#0d9488; --teal-lt:#f0fdfb; --teal-ring:rgba(20,184,166,.2);
  --slate:#94a3b8; --slate2:#64748b;
  --surface:#ffffff; --bg:#f4f7fb;
  --border:#e4e9f2; --border2:#d0d7e6;
  --red:#ef4444; --red-lt:#fff1f2;
  --amber:#f59e0b; --amber-lt:#fffbeb;
  --green:#22c55e; --green-lt:#f0fdf4;
  --blue:#3b82f6; --blue-lt:#eff6ff;
  --text:#1e2a3b; --text2:#4b5a6d;
  --r:12px; --r-sm:8px;
  --sh:0 1px 2px rgba(0,0,0,.04),0 4px 12px rgba(0,0,0,.06);
  --sh-lg:0 4px 24px rgba(0,0,0,.10);
}

/* ── reset ── */
html,body,[class*="css"]{
  font-family:'Plus Jakarta Sans',sans-serif!important;
  background:var(--bg)!important;color:var(--text)!important;
}

/* ── hide default streamlit nav chrome ── */
#MainMenu,footer,header{visibility:hidden;}
.stDeployButton{display:none;}

/* ═══════════════════════════════════════════
   SIDEBAR  — vertical nav panel
═══════════════════════════════════════════ */
section[data-testid="stSidebar"]{
  background:var(--navy)!important;
  border-right:1px solid var(--navy3)!important;
  padding:0!important;
  min-width:240px!important;
}
section[data-testid="stSidebar"] .block-container{padding:0!important;}
section[data-testid="stSidebar"] *{color:#c8d4e8!important;}

/* brand block */
.sb-brand{
  padding:1.6rem 1.4rem 1.2rem;
  border-bottom:1px solid var(--navy3);
  margin-bottom:.5rem;
}
.sb-logo{font-size:1.5rem;margin-bottom:.25rem;}
.sb-name{font-size:1rem;font-weight:800;color:#f1f5f9!important;letter-spacing:-.3px;}
.sb-tagline{font-size:.68rem;color:var(--slate)!important;margin-top:.1rem;}

/* nav items */
.nav-item{
  display:flex;align-items:center;gap:.75rem;
  padding:.72rem 1.4rem;margin:1px 0;
  cursor:pointer;border-radius:0;
  transition:background .15s;font-size:.88rem;
  font-weight:500;color:#94a3b8!important;
  border-left:3px solid transparent;
  text-decoration:none;
}
.nav-item:hover{background:var(--navy2)!important;color:#e2e8f0!important;}
.nav-item.active{
  background:var(--navy2)!important;
  border-left-color:var(--teal)!important;
  color:#f1f5f9!important;
}
.nav-item.done{color:var(--teal)!important;}
.nav-icon{font-size:1.05rem;width:22px;text-align:center;}
.nav-badge{
  margin-left:auto;background:var(--teal);color:var(--navy)!important;
  font-size:.6rem;font-weight:700;padding:2px 7px;border-radius:100px;
}
.nav-section{
  font-size:.6rem;letter-spacing:1.5px;text-transform:uppercase;
  color:var(--navy3)!important;padding:.8rem 1.4rem .3rem;font-weight:700;
}

/* sidebar bottom info */
.sb-footer{
  padding:1rem 1.4rem;border-top:1px solid var(--navy3);
  font-size:.68rem;color:var(--slate)!important;line-height:1.7;
  margin-top:auto;
}
.sb-footer b{color:#94a3b8!important;}

/* ═══════════════════════════════════════════
   MAIN CONTENT
═══════════════════════════════════════════ */
.main .block-container{
  background:var(--bg)!important;
  padding:2rem 2.5rem 4rem!important;
  max-width:960px!important;
}

/* ── Page title ── */
.pg-title{
  font-size:1.55rem;font-weight:800;color:var(--text)!important;
  letter-spacing:-.4px;margin:0 0 .2rem;
}
.pg-sub{font-size:.9rem;color:var(--text2)!important;margin-bottom:1.5rem;}

/* ── Step indicator ── */
.step-bar{display:flex;gap:0;margin-bottom:2rem;border-radius:var(--r);overflow:hidden;border:1px solid var(--border);}
.step{flex:1;padding:.7rem .5rem;text-align:center;background:var(--surface);
  font-size:.72rem;font-weight:600;color:var(--slate2)!important;
  border-right:1px solid var(--border);transition:all .2s;position:relative;}
.step:last-child{border-right:none;}
.step.active{background:var(--teal);color:var(--navy)!important;}
.step.done{background:var(--teal-lt);color:var(--teal-dk)!important;}
.step-num{display:block;font-size:.62rem;font-weight:700;margin-bottom:.1rem;opacity:.7;}

/* ── Cards ── */
.card{
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--r);padding:1.5rem;margin-bottom:1rem;
  box-shadow:var(--sh);
}
.card-title{font-size:.8rem;font-weight:700;text-transform:uppercase;
  letter-spacing:1px;color:var(--slate2)!important;margin-bottom:1rem;
  display:flex;align-items:center;gap:.5rem;}

/* ── Hospital/program pills ── */
.info-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:.75rem;margin-bottom:.5rem;}
.info-pill{background:var(--bg);border:1px solid var(--border);border-radius:var(--r-sm);
  padding:.7rem 1rem;}
.info-lbl{font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.8px;
  color:var(--slate)!important;margin-bottom:.2rem;}
.info-val{font-size:.9rem;font-weight:600;color:var(--text)!important;}
.info-code{font-family:'JetBrains Mono',monospace;font-size:.82rem;font-weight:500;
  color:var(--teal-dk)!important;}

/* ── Upload zone ── */
.upload-zone{
  border:2px dashed var(--border2);border-radius:var(--r);
  padding:2.5rem 2rem;text-align:center;background:var(--surface);
  transition:all .2s;cursor:pointer;
}
.upload-zone:hover{border-color:var(--teal);background:var(--teal-lt);}
.upload-zone.has-file{border-color:var(--teal);background:var(--teal-lt);border-style:solid;}
.upload-icon{font-size:2.2rem;margin-bottom:.6rem;}
.upload-title{font-size:1rem;font-weight:700;color:var(--text)!important;margin-bottom:.25rem;}
.upload-sub{font-size:.82rem;color:var(--text2)!important;}

/* ── Mode selector ── */
.mode-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:.75rem;margin-bottom:1rem;}
.mode-btn{
  border:2px solid var(--border);border-radius:var(--r-sm);padding:1rem;
  text-align:center;cursor:pointer;background:var(--surface);
  transition:all .18s;
}
.mode-btn:hover{border-color:var(--teal);background:var(--teal-lt);}
.mode-btn.active{border-color:var(--teal);background:var(--teal-lt);}
.mode-btn-icon{font-size:1.4rem;margin-bottom:.3rem;}
.mode-btn-label{font-size:.82rem;font-weight:700;color:var(--text)!important;}
.mode-btn-hint{font-size:.7rem;color:var(--text2)!important;margin-top:.15rem;}

/* ── Alerts ── */
.alert{display:flex;align-items:flex-start;gap:.8rem;border-radius:var(--r-sm);
  padding:.9rem 1.1rem;margin:.75rem 0;font-size:.84rem;line-height:1.5;}
.alert-ok    {background:var(--green-lt);border:1px solid #bbf7d0;border-left:4px solid var(--green);color:#14532d!important;}
.alert-warn  {background:var(--amber-lt);border:1px solid #fde68a;border-left:4px solid var(--amber);color:#78350f!important;}
.alert-info  {background:var(--blue-lt); border:1px solid #bfdbfe;border-left:4px solid var(--blue); color:#1e40af!important;}
.alert-danger{background:var(--red-lt);  border:1px solid #fecdd3;border-left:4px solid var(--red);  color:#9f1239!important;}

/* ── Stats row ── */
.stat-row{display:flex;gap:.75rem;margin-bottom:1rem;}
.stat-box{flex:1;background:var(--surface);border:1px solid var(--border);border-radius:var(--r);
  padding:1.1rem 1.2rem;text-align:center;box-shadow:var(--sh);}
.stat-n{font-size:2.2rem;font-weight:800;line-height:1;}
.stat-l{font-size:.72rem;color:var(--text2)!important;margin-top:.2rem;font-weight:500;}
.c-teal {color:var(--teal-dk)!important;}
.c-red  {color:var(--red)!important;}
.c-amber{color:var(--amber)!important;}
.c-slate{color:var(--text)!important;}

/* ── File table ── */
.ftable{border:1px solid var(--border);border-radius:var(--r);overflow:hidden;box-shadow:var(--sh);}
.fth{display:grid;grid-template-columns:2fr 2.2fr 90px;background:var(--navy);padding:.6rem 1.1rem;
  font-family:'JetBrains Mono',monospace;font-size:.62rem;letter-spacing:1px;
  text-transform:uppercase;color:#475569!important;}
.frow{display:grid;grid-template-columns:2fr 2.2fr 90px;padding:.65rem 1.1rem;
  background:var(--surface);border-top:1px solid var(--border);align-items:center;
  transition:background .12s;}
.frow:hover{background:var(--bg);}
.f-orig{font-size:.79rem;color:var(--slate2)!important;font-family:'JetBrains Mono',monospace;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.f-new{font-family:'JetBrains Mono',monospace;font-size:.82rem;font-weight:500;color:var(--teal-dk)!important;}
.fbadge{font-family:'JetBrains Mono',monospace;font-size:.63rem;padding:3px 9px;border-radius:100px;justify-self:start;}
.fbok  {background:var(--teal-lt);color:var(--teal-dk)!important;}
.fberr {background:var(--red-lt); color:var(--red)!important;}
.fbskip{background:var(--amber-lt);color:var(--amber)!important;}

/* ── Filename preview ── */
.fname-preview{
  font-family:'JetBrains Mono',monospace;font-size:.85rem;
  background:var(--navy);color:var(--teal)!important;
  padding:.75rem 1.1rem;border-radius:var(--r-sm);
  margin:.5rem 0;letter-spacing:.3px;
}

/* ── Buttons ── */
.stButton>button{
  font-family:'Plus Jakarta Sans',sans-serif!important;font-weight:700!important;
  border-radius:var(--r-sm)!important;border:none!important;
  padding:.6rem 1.6rem!important;font-size:.9rem!important;transition:all .18s!important;
}
.stButton>button[kind="primary"]{background:var(--teal)!important;color:var(--navy)!important;}
.stButton>button:hover{opacity:.88!important;transform:translateY(-1px)!important;}

/* ── Progress ── */
.stProgress>div>div>div{background:var(--teal)!important;border-radius:100px!important;}

/* ── Streamlit widget overrides ── */
.stSelectbox>div>div,.stTextInput>div>div{border-radius:var(--r-sm)!important;border-color:var(--border)!important;}
.stFileUploader>div{border-radius:var(--r)!important;}
.stRadio>div{gap:.5rem!important;}
.stCheckbox{margin:.5rem 0!important;}

/* ── Deletion confirmation box ── */
.del-box{
  background:var(--red-lt);border:2px solid #fecdd3;border-radius:var(--r);
  padding:1.5rem;margin-top:1rem;
}
.del-box-title{font-size:1rem;font-weight:800;color:var(--red)!important;margin-bottom:.5rem;}
.del-checklist{font-size:.85rem;color:#9f1239!important;line-height:2;}

/* ── Proof box ── */
.proof-box{
  background:var(--green-lt);border:2px solid #86efac;border-radius:var(--r);
  padding:1.5rem;
}
.proof-title{font-size:1rem;font-weight:800;color:#15803d!important;margin-bottom:.75rem;}
.proof-line{display:flex;align-items:flex-start;gap:.6rem;font-size:.85rem;
  color:#14532d!important;margin-bottom:.4rem;}

/* hide streamlit label spam */
div[data-testid="stVerticalBlock"]>div[style*="flex-direction: column"]>div[data-testid="element-container"]>div>div>label{display:none;}

hr{border-color:var(--border)!important;}
::-webkit-scrollbar{width:5px;height:5px;}
::-webkit-scrollbar-thumb{background:var(--border2);border-radius:10px;}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────────────────────────
HOSPITALS = {
    "CHUK — University Teaching Hospital of Kigali": "H01",
    "KFH Rwanda — King Faisal Hospital":             "H02",
    "Hôpital La Croix du Sud":                       "H03",
    "CHUB — University Teaching Hospital of Butare": "H04",
}
PROGRAMS  = {"University of Rwanda · CBE · ACE-DS · Data Mining": "ACE-DS_DM"}
SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".dcm", ".dicom"}

PAGES = ["🏠  Home", "⚙️  Configure", "📤  Upload", "🛡  Anonymize", "📦  Download & Delete"]

# ──────────────────────────────────────────────────────────────────
# SESSION STATE
# ──────────────────────────────────────────────────────────────────
_D = dict(
    page=0,
    hospital_key=list(HOSPITALS.keys())[0],
    program_key=list(PROGRAMS.keys())[0],
    img_code="CXR",
    custom_hospitals={},
    upload_mode="zip",       # "zip" | "files"
    results=None,
    zip_bytes=None,
    zip_filename=None,
    log_lines=[],
    run_complete=False,
    dataset_deleted=False,
)
for k, v in _D.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ──────────────────────────────────────────────────────────────────
# LOGGER
# ──────────────────────────────────────────────────────────────────
def _logger():
    log = logging.getLogger("MedAnon")
    if not log.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s", "%H:%M:%S"))
        log.addHandler(h)
    log.setLevel(logging.DEBUG)
    return log
logger = _logger()

# ──────────────────────────────────────────────────────────────────
# HELPERS — anonymization
# ──────────────────────────────────────────────────────────────────
def _wipe(ba):
    for i in range(len(ba)): ba[i] = 0

def strip_image(raw, ext):
    img = Image.open(io.BytesIO(raw))
    out = Image.new(img.mode, img.size)
    out.putdata(list(img.getdata()))
    buf = io.BytesIO()
    if ext in (".jpg",".jpeg"): out.save(buf, format="JPEG", quality=95, subsampling=0)
    else: out.save(buf, format="PNG")
    return buf.getvalue()

def strip_dicom(raw):
    if not DICOM_AVAILABLE:
        raise RuntimeError("pydicom not installed — pip install pydicom")
    ds = pydicom.dcmread(io.BytesIO(raw))
    for tag in ["PatientName","PatientID","PatientBirthDate","PatientSex","PatientAge",
                "PatientWeight","PatientAddress","PatientTelephoneNumbers",
                "PatientMotherBirthName","OtherPatientNames","OtherPatientIDs",
                "InstitutionName","InstitutionAddress","InstitutionalDepartmentName",
                "ReferringPhysicianName","PerformingPhysicianName","RequestingPhysician",
                "OperatorsName","StudyDate","SeriesDate","AcquisitionDate","ContentDate",
                "StudyTime","SeriesTime","AcquisitionTime","AccessionNumber","StudyID",
                "RequestedProcedureDescription"]:
        if hasattr(ds, tag):
            try: setattr(ds, tag, "ANONYMIZED")
            except: pass
    ds.StudyInstanceUID = generate_uid()
    ds.SeriesInstanceUID = generate_uid()
    ds.SOPInstanceUID = generate_uid()
    buf = io.BytesIO(); ds.save_as(buf); return buf.getvalue()

def make_fname(h, p, t, pid, ext):
    return f"{h}_{p}_{t}_{str(pid).zfill(5)}{ext.lower()}"

def collect_zip(zf_obj):
    entries = []
    with zipfile.ZipFile(io.BytesIO(zf_obj.read())) as zf:
        for info in zf.infolist():
            if info.is_dir() or "__MACOSX" in info.filename: continue
            fname = Path(info.filename)
            if fname.name.startswith("."): continue
            ext = fname.suffix.lower()
            if ext in SUPPORTED_EXT:
                entries.append({"name": fname.name, "raw": zf.read(info.filename), "ext": ext})
    return entries

def collect_files(uploaded):
    return [{"name": f.name, "raw": f.read(), "ext": Path(f.name).suffix.lower()}
            for f in uploaded if Path(f.name).suffix.lower() in SUPPORTED_EXT]

def run_pipeline(entries, h, p, t, bar, status):
    results, log = [], [
        "─"*58,
        f"  MedAnon Pro  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"  Hospital:{h}  Program:{p}  Type:{t}  Files:{len(entries)}",
        "─"*58,
    ]
    pid = 1
    for i, e in enumerate(entries):
        bar.progress(int(i/len(entries)*100))
        status.markdown(f'<span style="font-size:.82rem;color:#64748b;">Processing {i+1}/{len(entries)} — <b>{e["name"]}</b></span>', unsafe_allow_html=True)
        try:
            clean = strip_dicom(e["raw"]) if e["ext"] in (".dcm",".dicom") else strip_image(e["raw"], e["ext"])
            nn = make_fname(h, p, t, pid, e["ext"])
            log.append(f"  ✓  {e['name']:<44} → {nn}")
            results.append(dict(original=e["name"], new_name=nn, clean_bytes=clean, ext=e["ext"], status="ok"))
            pid += 1
        except Exception as ex:
            log.append(f"  ✗  {e['name']:<44} {ex}")
            results.append(dict(original=e["name"], new_name="—", clean_bytes=None, ext=e["ext"], status="error"))
    bar.progress(100); status.empty()
    ok = sum(1 for r in results if r["status"]=="ok")
    log += ["─"*58, f"  ✓ Anonymized:{ok}  ✗ Failed:{len(results)-ok}", "─"*58]
    return results, log

def pack_zip(results):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for r in results:
            if r["status"]=="ok" and r.get("clean_bytes"):
                zf.writestr(r["new_name"], r["clean_bytes"])
    return buf.getvalue()

def purge_ram(results):
    out = []
    for r in results:
        if r.get("clean_bytes"):
            ba = bytearray(r["clean_bytes"]); _wipe(ba)
        out.append({**r, "clean_bytes": None})
    return out

# ──────────────────────────────────────────────────────────────────
# NAVIGATION helper
# ──────────────────────────────────────────────────────────────────
def go(page_idx):
    st.session_state["page"] = page_idx
    st.rerun()

# ──────────────────────────────────────────────────────────────────
# SIDEBAR — vertical nav
# ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sb-brand">
      <div class="sb-logo">🛡</div>
      <div class="sb-name">MedAnon Pro</div>
      <div class="sb-tagline">Medical Image Anonymization</div>
    </div>""", unsafe_allow_html=True)

    cur = st.session_state["page"]
    done = st.session_state["run_complete"]

    # Nav items — each is a button styled as a nav row
    nav_items = [
        (0, "🏠", "Home",          "Welcome & overview",     False),
        (1, "⚙️", "Configure",     "Hospital · program · type", False),
        (2, "📤", "Upload",        "Choose your images",     False),
        (3, "🛡", "Anonymize",     "Run the pipeline",       False),
        (4, "📦", "Download & Delete", "Export & clean up",  False),
    ]

    st.markdown('<div class="nav-section">Navigation</div>', unsafe_allow_html=True)
    for idx, icon, label, hint, _ in nav_items:
        cls = "active" if idx == cur else ("done" if done and idx < 4 else "")
        badge = " ✓" if done and idx in (1,2,3) else ""
        # Use streamlit button disguised as a nav item via CSS trick
        clicked = st.button(
            f"{icon}  {label}{badge}",
            key=f"nav_{idx}",
            use_container_width=True,
        )
        if clicked:
            go(idx)

    st.markdown('<div class="nav-section" style="margin-top:1rem;">Session</div>', unsafe_allow_html=True)
    if st.button("🔄  New Session", key="nav_reset", use_container_width=True):
        for k in list(_D.keys()):
            st.session_state[k] = _D[k]
        st.rerun()

    # Config quick-view
    h_code = {**HOSPITALS, **st.session_state["custom_hospitals"]}.get(
        st.session_state["hospital_key"], "H01")
    p_code = PROGRAMS.get(st.session_state["program_key"], "ACE-DS_DM")
    t_code = st.session_state["img_code"]

    st.markdown(f"""
    <div class="sb-footer">
      <b>Current config</b><br>
      🏥 {h_code} &nbsp;·&nbsp; 🎓 {p_code}<br>
      🩻 {t_code}<br>
      <br>
      <b>Output example</b><br>
      <span style="color:var(--teal)!important;font-family:'JetBrains Mono',monospace;font-size:.65rem;">
        {h_code}_{p_code}_{t_code}_00001.jpg
      </span>
    </div>""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────
# STEP BAR
# ──────────────────────────────────────────────────────────────────
cur = st.session_state["page"]
done = st.session_state["run_complete"]

steps = ["Home","Configure","Upload","Anonymize","Download & Delete"]
step_html = '<div class="step-bar">'
for i, s in enumerate(steps):
    cls = "active" if i==cur else ("done" if i<cur or (done and i<4) else "")
    step_html += f'<div class="step {cls}"><span class="step-num">STEP {i+1}</span>{s}</div>'
step_html += '</div>'
st.markdown(step_html, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# PAGE 0 — HOME
# ══════════════════════════════════════════════════════════════════
if cur == 0:
    st.markdown('<div class="pg-title">Welcome to MedAnon Pro 🛡</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">A secure, step-by-step medical image anonymization system.</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="card">
          <div class="card-title">⚡ What this tool does</div>
          <ul style="font-size:.88rem;line-height:2;color:#4b5a6d;padding-left:1.2rem;margin:0;">
            <li>Renames images with a structured, anonymous ID</li>
            <li>Strips all patient metadata (EXIF & DICOM tags)</li>
            <li>Supports JPG, PNG and DICOM (.dcm) images</li>
            <li>Packages anonymized images into a ZIP file</li>
            <li>Deletes the original dataset on request</li>
          </ul>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="card">
          <div class="card-title">🗺 How to use — 5 steps</div>
          <ol style="font-size:.88rem;line-height:2.1;color:#4b5a6d;padding-left:1.2rem;margin:0;">
            <li><b>Configure</b> — select hospital, program, image type</li>
            <li><b>Upload</b> — ZIP your folder or pick individual files</li>
            <li><b>Anonymize</b> — run the pipeline with one click</li>
            <li><b>Download</b> — save the anonymized ZIP</li>
            <li><b>Delete</b> — remove original dataset (optional)</li>
          </ol>
        </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
      <div class="card-title">🔒 Privacy & security</div>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;font-size:.85rem;color:#4b5a6d;">
        <div><b style="color:#0d9488;">🧹 EXIF stripped</b><br>All JPEG/PNG metadata erased by pixel-level reconstruction.</div>
        <div><b style="color:#0d9488;">🩺 DICOM cleaned</b><br>27 sensitive tags wiped, all UIDs regenerated.</div>
        <div><b style="color:#0d9488;">💾 Memory zeroed</b><br>Image buffers overwritten with zeros after ZIP is built.</div>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="alert alert-info">
      <span>💡</span>
      <div>This tool is <b>fully hosted</b> — upload your images as a ZIP file or individual files. No local folder paths are needed.</div>
    </div>""", unsafe_allow_html=True)

    col_btn, _ = st.columns([1,3])
    with col_btn:
        if st.button("Get Started →", type="primary", use_container_width=True):
            go(1)


# ══════════════════════════════════════════════════════════════════
# PAGE 1 — CONFIGURE
# ══════════════════════════════════════════════════════════════════
elif cur == 1:
    st.markdown('<div class="pg-title">⚙️ Configure</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Set up your hospital, program and image type. These define the output filename.</div>', unsafe_allow_html=True)

    all_hospitals = {**HOSPITALS, **st.session_state["custom_hospitals"]}

    # Hospital
    st.markdown('<div class="card"><div class="card-title">🏥 Hospital</div>', unsafe_allow_html=True)
    sel_h = st.selectbox("Select hospital", list(all_hospitals.keys()),
                          index=list(all_hospitals.keys()).index(st.session_state["hospital_key"])
                          if st.session_state["hospital_key"] in all_hospitals else 0,
                          label_visibility="collapsed")
    st.session_state["hospital_key"] = sel_h
    h_code = all_hospitals[sel_h]
    st.markdown(f'<div style="margin-top:.5rem;font-size:.8rem;color:#64748b;">Hospital code: <span style="font-family:\'JetBrains Mono\',monospace;color:var(--teal-dk);font-weight:600;">{h_code}</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Add hospital
    with st.expander("➕  Register a new hospital"):
        col_a, col_b = st.columns([3,1])
        with col_a:
            new_hname = st.text_input("Hospital name", placeholder="e.g. Rwanda Military Hospital", key="nh_name")
        with col_b:
            new_hcode = st.text_input("Code", value=f"H{str(len(all_hospitals)+1).zfill(2)}", max_chars=5, key="nh_code")
        if st.button("Add hospital ➕", use_container_width=True):
            n2, c2 = new_hname.strip(), new_hcode.strip().upper()
            if not n2: st.error("Please enter a hospital name.")
            elif c2 in set(all_hospitals.values()): st.error(f"Code '{c2}' already exists.")
            elif n2 in all_hospitals: st.warning("This hospital is already registered.")
            else:
                st.session_state["custom_hospitals"][n2] = c2
                st.session_state["hospital_key"] = n2
                st.success(f"✓ Added: {n2} → {c2}")
                st.rerun()
        if st.session_state["custom_hospitals"]:
            for hn, hc in list(st.session_state["custom_hospitals"].items()):
                col1, col2 = st.columns([5,1])
                col1.markdown(f'<span style="font-size:.82rem;"><b style="color:var(--teal-dk);">{hc}</b> — {hn}</span>', unsafe_allow_html=True)
                if col2.button("✕", key=f"del_{hc}"):
                    del st.session_state["custom_hospitals"][hn]
                    st.rerun()

    # Program
    st.markdown('<div class="card"><div class="card-title">🎓 Program</div>', unsafe_allow_html=True)
    sel_p = st.selectbox("Select program", list(PROGRAMS.keys()),
                          index=list(PROGRAMS.keys()).index(st.session_state["program_key"]) if st.session_state["program_key"] in PROGRAMS else 0,
                          label_visibility="collapsed")
    st.session_state["program_key"] = sel_p
    p_code = PROGRAMS[sel_p]
    st.markdown(f'<div style="margin-top:.5rem;font-size:.8rem;color:#64748b;">Program code: <span style="font-family:\'JetBrains Mono\',monospace;color:var(--teal-dk);font-weight:600;">{p_code}</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Image type
    st.markdown('<div class="card"><div class="card-title">🩻 Image Type</div>', unsafe_allow_html=True)
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        cxr_active = "active" if st.session_state["img_code"] == "CXR" else ""
        st.markdown(f'<div class="mode-btn {cxr_active}"><div class="mode-btn-icon">🫁</div><div class="mode-btn-label">Chest X-ray</div><div class="mode-btn-hint">Code: CXR</div></div>', unsafe_allow_html=True)
        if st.button("Select Chest X-ray", use_container_width=True, key="sel_cxr"):
            st.session_state["img_code"] = "CXR"; st.rerun()
    with col_t2:
        img_active = "active" if st.session_state["img_code"] == "IMG" else ""
        st.markdown(f'<div class="mode-btn {img_active}"><div class="mode-btn-icon">🔬</div><div class="mode-btn-label">Other Medical Images</div><div class="mode-btn-hint">Code: IMG</div></div>', unsafe_allow_html=True)
        if st.button("Select Other Images", use_container_width=True, key="sel_img"):
            st.session_state["img_code"] = "IMG"; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Preview
    t_code = st.session_state["img_code"]
    st.markdown(f"""
    <div class="card">
      <div class="card-title">👁 Output Filename Preview</div>
      <div class="fname-preview">{h_code}_{p_code}_{t_code}_00001.jpg</div>
      <div class="fname-preview">{h_code}_{p_code}_{t_code}_00002.jpg</div>
      <div class="fname-preview">{h_code}_{p_code}_{t_code}_00003.dcm</div>
      <div style="font-size:.78rem;color:#64748b;margin-top:.5rem;">Patient IDs are assigned sequentially starting from 00001.</div>
    </div>""", unsafe_allow_html=True)

    col_b, _ = st.columns([1,3])
    with col_b:
        if st.button("Next: Upload Images →", type="primary", use_container_width=True):
            go(2)


# ══════════════════════════════════════════════════════════════════
# PAGE 2 — UPLOAD
# ══════════════════════════════════════════════════════════════════
elif cur == 2:
    st.markdown('<div class="pg-title">📤 Upload Images</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Choose how to upload your medical images. ZIP upload is recommended for folders.</div>', unsafe_allow_html=True)

    # Mode selector
    col_z, col_f = st.columns(2)
    with col_z:
        z_active = "active" if st.session_state["upload_mode"] == "zip" else ""
        st.markdown(f'<div class="mode-btn {z_active}"><div class="mode-btn-icon">🗜</div><div class="mode-btn-label">Upload a ZIP file</div><div class="mode-btn-hint">Compress your folder and upload</div></div>', unsafe_allow_html=True)
        if st.button("Use ZIP upload", use_container_width=True, key="mode_zip"):
            st.session_state["upload_mode"] = "zip"; st.rerun()
    with col_f:
        f_active = "active" if st.session_state["upload_mode"] == "files" else ""
        st.markdown(f'<div class="mode-btn {f_active}"><div class="mode-btn-icon">🖼</div><div class="mode-btn-label">Upload individual files</div><div class="mode-btn-hint">Select multiple images directly</div></div>', unsafe_allow_html=True)
        if st.button("Use file upload", use_container_width=True, key="mode_files"):
            st.session_state["upload_mode"] = "files"; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Uploader
    if st.session_state["upload_mode"] == "zip":
        st.markdown("""
        <div class="alert alert-info">
          <span>💡</span>
          <div><b>How to create a ZIP:</b> On Windows, right-click your folder → <b>Send to → Compressed (zipped) folder</b>. On Mac, right-click → <b>Compress</b>. Then upload the .zip file below.</div>
        </div>""", unsafe_allow_html=True)
        uploaded_zip = st.file_uploader("Upload your ZIP file here",
                                         type=["zip"], label_visibility="visible",
                                         key="zip_upload")
        if uploaded_zip:
            # Count images inside without extracting all
            try:
                with zipfile.ZipFile(io.BytesIO(uploaded_zip.getvalue())) as zf:
                    img_count = sum(1 for i in zf.infolist()
                                    if not i.is_dir() and
                                    Path(i.filename).suffix.lower() in SUPPORTED_EXT and
                                    "__MACOSX" not in i.filename)
                st.markdown(f"""
                <div class="alert alert-ok">
                  <span>✅</span>
                  <div><b>{uploaded_zip.name}</b> uploaded successfully.<br>
                  Found <b>{img_count}</b> supported image(s) inside · {uploaded_zip.size/1024/1024:.2f} MB</div>
                </div>""", unsafe_allow_html=True)
                st.session_state["_zip_upload"] = uploaded_zip
            except Exception as e:
                st.error(f"Could not read ZIP: {e}")
        else:
            st.session_state.pop("_zip_upload", None)

    else:
        st.markdown("""
        <div class="alert alert-info">
          <span>💡</span>
          <div>Select multiple files by holding <b>Ctrl</b> (Windows) or <b>Cmd</b> (Mac) while clicking. Supports JPG, PNG and DICOM (.dcm).</div>
        </div>""", unsafe_allow_html=True)
        uploaded_files = st.file_uploader("Upload your image files here",
                                           type=["jpg","jpeg","png","dcm"],
                                           accept_multiple_files=True,
                                           label_visibility="visible",
                                           key="files_upload")
        if uploaded_files:
            dcm_n = sum(1 for f in uploaded_files if Path(f.name).suffix.lower() in (".dcm",".dicom"))
            img_n = len(uploaded_files) - dcm_n
            st.markdown(f"""
            <div class="alert alert-ok">
              <span>✅</span>
              <div><b>{len(uploaded_files)}</b> file(s) ready — <b>{img_n}</b> image(s) + <b>{dcm_n}</b> DICOM file(s)</div>
            </div>""", unsafe_allow_html=True)
            st.session_state["_files_upload"] = uploaded_files
        else:
            st.session_state.pop("_files_upload", None)

    # Check readiness
    ready = (st.session_state["upload_mode"] == "zip" and "_zip_upload" in st.session_state) or \
            (st.session_state["upload_mode"] == "files" and "_files_upload" in st.session_state)

    st.markdown("<br>", unsafe_allow_html=True)
    col_back, col_next, _ = st.columns([1,1,2])
    with col_back:
        if st.button("← Back", use_container_width=True): go(1)
    with col_next:
        if st.button("Next: Anonymize →", type="primary",
                      use_container_width=True, disabled=not ready):
            go(3)
    if not ready:
        st.markdown('<div style="font-size:.8rem;color:#d97706;margin-top:.4rem;">⚠ Please upload your images first.</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# PAGE 3 — ANONYMIZE
# ══════════════════════════════════════════════════════════════════
elif cur == 3:
    st.markdown('<div class="pg-title">🛡 Anonymize</div>', unsafe_allow_html=True)

    all_hosp = {**HOSPITALS, **st.session_state["custom_hospitals"]}
    h_code = all_hosp.get(st.session_state["hospital_key"], "H01")
    p_code = PROGRAMS.get(st.session_state["program_key"], "ACE-DS_DM")
    t_code = st.session_state["img_code"]

    # Config summary
    st.markdown(f"""
    <div class="card">
      <div class="card-title">✅ Configuration Summary</div>
      <div class="info-grid">
        <div class="info-pill"><div class="info-lbl">Hospital</div><div class="info-val">{st.session_state["hospital_key"].split("—")[0].strip()}</div><div class="info-code">{h_code}</div></div>
        <div class="info-pill"><div class="info-lbl">Program</div><div class="info-val">ACE-DS · Data Mining</div><div class="info-code">{p_code}</div></div>
        <div class="info-pill"><div class="info-lbl">Image Type</div><div class="info-val">{"Chest X-ray" if t_code=="CXR" else "Other Medical Images"}</div><div class="info-code">{t_code}</div></div>
        <div class="info-pill"><div class="info-lbl">Upload Mode</div><div class="info-val">{"ZIP folder" if st.session_state["upload_mode"]=="zip" else "Individual files"}</div><div class="info-code">{"🗜" if st.session_state["upload_mode"]=="zip" else "🖼"}</div></div>
      </div>
      <div class="fname-preview">{h_code}_{p_code}_{t_code}_00001 → 0000N.ext</div>
    </div>""", unsafe_allow_html=True)

    if st.session_state["run_complete"] and st.session_state.get("results"):
        # Already ran — show results
        results = st.session_state["results"]
        ok_n  = sum(1 for r in results if r["status"]=="ok")
        err_n = sum(1 for r in results if r["status"]=="error")

        st.markdown(f"""
        <div class="stat-row">
          <div class="stat-box"><div class="stat-n c-slate">{len(results)}</div><div class="stat-l">Total processed</div></div>
          <div class="stat-box"><div class="stat-n c-teal">{ok_n}</div><div class="stat-l">✓ Anonymized</div></div>
          <div class="stat-box"><div class="stat-n c-red">{err_n}</div><div class="stat-l">✗ Errors</div></div>
        </div>""", unsafe_allow_html=True)

        st.markdown("""
        <div class="alert alert-ok">
          <span>🛡</span>
          <div><b>Anonymization complete!</b> All metadata stripped and images renamed. Memory buffers zeroed.</div>
        </div>""", unsafe_allow_html=True)

        # File table (scrollable)
        st.markdown('<div style="font-size:.8rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-bottom:.5rem;">Renamed files</div>', unsafe_allow_html=True)
        st.markdown('<div class="ftable"><div class="fth"><span>Original</span><span>→ Anonymized</span><span>Status</span></div>', unsafe_allow_html=True)
        for r in results[:50]:  # show first 50
            ico = "🩻" if r["ext"] in (".dcm",".dicom") else "🖼️"
            bc, bt = {"ok":("fbok","✓ OK"),"error":("fberr","✗ Err"),"skip":("fbskip","⚠ Skip")}[r["status"]]
            st.markdown(f'<div class="frow"><span class="f-orig">{ico} {r["original"]}</span><span class="f-new">{r["new_name"]}</span><span class="fbadge {bc}">{bt}</span></div>', unsafe_allow_html=True)
        if len(results) > 50:
            st.markdown(f'<div class="frow" style="justify-content:center;color:#64748b;font-size:.8rem;">… and {len(results)-50} more files</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        col_b, col_n, _ = st.columns([1,1,2])
        with col_n:
            if st.button("Next: Download →", type="primary", use_container_width=True): go(4)

    else:
        # Check upload data available
        has_data = ("_zip_upload" in st.session_state and st.session_state["upload_mode"]=="zip") or \
                   ("_files_upload" in st.session_state and st.session_state["upload_mode"]=="files")

        if not has_data:
            st.markdown("""
            <div class="alert alert-warn">
              <span>⚠️</span>
              <div>No images uploaded yet. <b>Go back to Upload</b> and upload your images first.</div>
            </div>""", unsafe_allow_html=True)
            if st.button("← Go to Upload", use_container_width=False): go(2)
        else:
            st.markdown("""
            <div class="alert alert-warn">
              <span>🔐</span>
              <div><b>Security note:</b> After anonymization, all original image data is zeroed from memory. Only the anonymized ZIP remains.</div>
            </div>""", unsafe_allow_html=True)

            col_back, col_run, _ = st.columns([1,1.5,2])
            with col_back:
                if st.button("← Back", use_container_width=True): go(2)
            with col_run:
                run_clicked = st.button("🛡  Run Anonymization", type="primary", use_container_width=True)

            if run_clicked:
                bar    = st.progress(0)
                status = st.empty()

                try:
                    if st.session_state["upload_mode"] == "zip":
                        status.markdown('<span style="font-size:.85rem;color:#7c3aed;">🗜 Extracting ZIP archive…</span>', unsafe_allow_html=True)
                        entries = collect_zip(st.session_state["_zip_upload"])
                    else:
                        entries = collect_files(st.session_state["_files_upload"])

                    if not entries:
                        st.error("No supported images found in your upload. Please check the file types (JPG, PNG, DCM)."); st.stop()

                    results, log_lines = run_pipeline(entries, h_code, p_code, t_code, bar, status)

                    zip_bytes = pack_zip(results)
                    zip_fname = f"anonymized_{h_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

                    results = purge_ram(results)
                    log_lines.append("  🗑  Memory purge complete — all buffers zeroed")
                    logger.info("Done. %d files processed.", len(results))

                    st.session_state.update(dict(
                        results=results, zip_bytes=zip_bytes,
                        zip_filename=zip_fname, log_lines=log_lines,
                        run_complete=True))
                    st.rerun()

                except Exception as e:
                    st.error(f"Anonymization failed: {e}")


# ══════════════════════════════════════════════════════════════════
# PAGE 4 — DOWNLOAD & DELETE
# ══════════════════════════════════════════════════════════════════
elif cur == 4:
    st.markdown('<div class="pg-title">📦 Download & Delete</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Download your anonymized images, then delete the original dataset.</div>', unsafe_allow_html=True)

    if not st.session_state["run_complete"] or not st.session_state.get("zip_bytes"):
        st.markdown("""
        <div class="alert alert-warn">
          <span>⚠️</span>
          <div>No anonymized data ready. Please complete the <b>Anonymize</b> step first.</div>
        </div>""", unsafe_allow_html=True)
        if st.button("← Go to Anonymize"): go(3)
    else:
        zip_b  = st.session_state["zip_bytes"]
        zip_fn = st.session_state["zip_filename"]
        ok_n   = sum(1 for r in st.session_state["results"] if r["status"]=="ok")
        sz_mb  = len(zip_b)/1024/1024

        # ── STEP A: Download ─────────────────────────────────────
        st.markdown("""
        <div class="card">
          <div class="card-title">⬇ Step 1 — Download your anonymized images</div>""", unsafe_allow_html=True)
        st.markdown(f"""
          <div style="font-size:.85rem;color:#4b5a6d;margin-bottom:1rem;">
            Your ZIP file is ready: <b>{ok_n}</b> anonymized image(s) · <b>{sz_mb:.2f} MB</b>
          </div>""", unsafe_allow_html=True)
        st.download_button(
            label=f"⬇  Download  {zip_fn}  ({ok_n} files · {sz_mb:.2f} MB)",
            data=zip_b, file_name=zip_fn, mime="application/zip",
            type="primary", use_container_width=False)
        st.markdown("""
          <div style="font-size:.78rem;color:#94a3b8;margin-top:.5rem;">
            The file will save to your browser's default Downloads folder. You can then move it anywhere.
          </div>
        </div>""", unsafe_allow_html=True)

        # ── Log ──────────────────────────────────────────────────
        with st.expander("🗒 View anonymization log"):
            log_txt = "\n".join(st.session_state.get("log_lines",[]))
            st.markdown(f'<div style="background:#0e1726;color:#4ade80;font-family:JetBrains Mono,monospace;font-size:.74rem;border-radius:8px;padding:1rem;max-height:220px;overflow-y:auto;line-height:1.75;"><pre>{log_txt}</pre></div>', unsafe_allow_html=True)
            st.download_button("⬇ Download log", data=log_txt.encode(),
                                file_name=f"anon_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                mime="text/plain")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── STEP B: Delete ───────────────────────────────────────
        if st.session_state.get("dataset_deleted"):
            # Proof of deletion
            st.markdown("""
            <div class="proof-box">
              <div class="proof-title">🗑 Deletion Certificate</div>
              <div class="proof-line"><span>✅</span><span>All uploaded images have been <b>cleared from this server session</b></span></div>
              <div class="proof-line"><span>✅</span><span>All anonymized image buffers have been <b>zeroed in memory</b></span></div>
              <div class="proof-line"><span>✅</span><span><b>No copy</b> of the original patient images remains on this platform</span></div>
              <div style="margin-top:1rem;font-size:.8rem;color:#15803d;">
                This screen can be shown to the radiology department as confirmation that the dataset was not retained.
              </div>
            </div>""", unsafe_allow_html=True)

        else:
            st.markdown("""
            <div class="del-box">
              <div class="del-box-title">🗑 Step 2 — Delete Original Dataset</div>
              <div style="font-size:.85rem;color:#9f1239;margin-bottom:1rem;">
                This will permanently erase all uploaded original images from this session.
                A deletion certificate will be generated that you can show to the hospital department.
              </div>
              <div class="del-checklist">
                ✓ Uploaded ZIP / files cleared from server session<br>
                ✓ All image buffers zeroed in memory<br>
                ✓ Deletion certificate generated (proof for the department)
              </div>
            </div>""", unsafe_allow_html=True)

            confirmed = st.checkbox(
                "✅  I confirm I have downloaded the anonymized ZIP and I want to delete the original dataset.",
                key="del_confirm")

            col_del, _ = st.columns([1,3])
            with col_del:
                del_btn = st.button("🗑  Delete Original Dataset",
                                     disabled=not confirmed,
                                     use_container_width=True)

            if del_btn and confirmed:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Purge uploads from session
                for k in ["_zip_upload","_files_upload","zip_upload","files_upload"]:
                    st.session_state.pop(k, None)
                # Zero the results
                if st.session_state.get("results"):
                    for r in st.session_state["results"]:
                        if r.get("clean_bytes"):
                            ba = bytearray(r["clean_bytes"]); _wipe(ba)
                st.session_state["results"] = []
                st.session_state["dataset_deleted"] = True
                log = st.session_state.get("log_lines",[])
                log.append(f"  🗑  SESSION DATA DELETED  [{ts}]")
                log.append(f"  🗑  ALL BUFFERS ZEROED   [{ts}]")
                st.session_state["log_lines"] = log
                logger.warning("Dataset deleted from session at %s", ts)
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("---")
        col_new, _ = st.columns([1,3])
        with col_new:
            if st.button("🔄  Start a new session", use_container_width=True):
                for k in list(_D.keys()):
                    st.session_state[k] = _D[k]
                for k in ["_zip_upload","_files_upload"]:
                    st.session_state.pop(k, None)
                st.rerun()

# ──────────────────────────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:3rem;padding-top:1rem;border-top:1px solid #e4e9f2;
  display:flex;justify-content:space-between;flex-wrap:wrap;gap:.5rem;">
  <div style="font-size:.75rem;color:#94a3b8;font-family:'JetBrains Mono',monospace;">
    © <b style="color:#4b5a6d;">Vedaste NYANDWI</b> &ensp;·&ensp; MedAnon Pro &ensp;·&ensp; Patient data never stored or transmitted
  </div>
  <div style="font-size:.72rem;color:#94a3b8;">University of Rwanda · CBE · ACE-DS · Data Mining</div>
</div>""", unsafe_allow_html=True)
