"""
╔══════════════════════════════════════════════════════════════════════╗
║   MedAnon Pro  — Secure Medical Image Anonymization System          ║
║   © Vedaste NYANDWI · University of Rwanda · CBE · ACE-DS · DM     ║
╚══════════════════════════════════════════════════════════════════════╝

Run:
    pip install -r requirements.txt
    streamlit run app.py
"""

import streamlit as st
import io, os, shutil, zipfile, logging
from pathlib import Path
from datetime import datetime
from PIL import Image

# ── Optional DICOM ──────────────────────────────────────────────────
DICOM_AVAILABLE = False
try:
    import pydicom
    from pydicom.uid import generate_uid
    DICOM_AVAILABLE = True
except ImportError:
    pass

# ═══════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════
st.set_page_config(page_title="MedAnon Pro", page_icon="🛡",
                   layout="wide", initial_sidebar_state="expanded")

# ═══════════════════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');
:root{
  --bg:#eef2f7;--surface:#fff;--surface2:#f8fafc;
  --border:#e2e8f0;--border2:#cbd5e1;
  --deep:#0f172a;--muted:#64748b;--dim:#94a3b8;
  --teal:#0d9488;--teal-lt:#ccfbf1;
  --red:#e11d48;--red-lt:#ffe4e6;
  --amber:#d97706;--amber-lt:#fef3c7;
  --blue:#2563eb;--blue-lt:#dbeafe;
  --purple:#7c3aed;--purple-lt:#ede9fe;
  --radius:10px;
  --shadow:0 1px 3px rgba(15,23,42,.05),0 4px 16px rgba(15,23,42,.06);
}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif!important;background:var(--bg)!important;color:var(--deep)!important;}
/* Sidebar */
section[data-testid="stSidebar"]{background:var(--deep)!important;}
section[data-testid="stSidebar"] *{color:#e2e8f0!important;}
section[data-testid="stSidebar"] label{color:#94a3b8!important;font-size:.78rem!important;}
section[data-testid="stSidebar"] .stSelectbox>div>div,
section[data-testid="stSidebar"] .stTextInput>div>div{background:#1e293b!important;border:1px solid #334155!important;border-radius:8px!important;}
section[data-testid="stSidebar"] .stFileUploader>div{background:#1e293b!important;border:1px dashed #334155!important;border-radius:8px!important;}
section[data-testid="stSidebar"] .stRadio>div>label{background:#1e293b;border:1px solid #334155;border-radius:8px;padding:.45rem .7rem;margin:.2rem 0;cursor:pointer;transition:background .15s;}
section[data-testid="stSidebar"] .stRadio>div>label:hover{background:#263548;}
/* Main */
.main .block-container{background:var(--bg)!important;padding:2rem 2.5rem 3rem;max-width:1100px;}
/* Header */
.app-header{display:flex;align-items:flex-start;gap:1.2rem;background:var(--surface);border:1px solid var(--border);border-top:4px solid var(--teal);border-radius:var(--radius);padding:1.8rem 2rem;margin-bottom:1.5rem;box-shadow:var(--shadow);}
.hdr-icon{font-size:2.4rem;line-height:1;margin-top:.15rem;}
.hdr-title{font-family:'Syne',sans-serif;font-size:1.75rem;font-weight:800;color:var(--deep)!important;letter-spacing:-.5px;line-height:1.1;margin:0 0 .3rem;}
.hdr-sub{font-size:.88rem;color:var(--muted)!important;}
.hdr-badges{display:flex;gap:.45rem;margin-top:.65rem;flex-wrap:wrap;}
.badge{font-family:'DM Mono',monospace;font-size:.63rem;letter-spacing:.5px;padding:3px 10px;border-radius:100px;font-weight:500;}
.b-teal  {background:var(--teal-lt);  color:var(--teal)  !important;}
.b-slate {background:#f1f5f9;color:#1e293b!important;border:1px solid var(--border);}
.b-red   {background:var(--red-lt);   color:var(--red)   !important;}
.b-purple{background:var(--purple-lt);color:var(--purple)!important;}
/* Section heading */
.sec-h{font-family:'Syne',sans-serif;font-size:.68rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--muted)!important;margin:1.8rem 0 .75rem;display:flex;align-items:center;gap:.5rem;}
.sec-h::after{content:"";flex:1;height:1px;background:var(--border);}
/* Upload mode cards */
.umode-card{background:var(--surface);border:2px solid var(--border);border-radius:var(--radius);padding:1rem;text-align:center;box-shadow:var(--shadow);}
.umode-card.active{border-color:var(--teal);background:#f0fdfb;box-shadow:0 0 0 3px var(--teal-lt);}
.umode-icon{font-size:1.6rem;margin-bottom:.35rem;}
.umode-label{font-family:'Syne',sans-serif;font-size:.78rem;font-weight:700;color:var(--deep)!important;}
.umode-hint{font-size:.68rem;color:var(--muted)!important;margin-top:.15rem;}
/* Config pills */
.cfg-strip{display:flex;gap:.7rem;flex-wrap:wrap;margin-bottom:1rem;}
.cfg-pill{display:flex;align-items:center;gap:.6rem;background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:.55rem 1rem;box-shadow:var(--shadow);flex:1;min-width:160px;}
.cfg-icon{font-size:1.1rem;}
.cfg-lbl{font-size:.68rem;color:var(--dim)!important;margin-bottom:.05rem;}
.cfg-val{font-family:'DM Mono',monospace;font-size:.85rem;font-weight:500;color:var(--deep)!important;}
/* Alerts */
.alert{display:flex;align-items:flex-start;gap:.8rem;border-radius:var(--radius);padding:1rem 1.2rem;margin:.8rem 0;font-size:.84rem;}
.alert-warn  {background:#fff7ed;border:1px solid #fed7aa;border-left:4px solid var(--amber);color:#92400e!important;}
.alert-ok    {background:#f0fdf4;border:1px solid #bbf7d0;border-left:4px solid #16a34a;  color:#14532d!important;}
.alert-info  {background:#eff6ff;border:1px solid #bfdbfe;border-left:4px solid var(--blue); color:#1e40af!important;}
.alert-danger{background:var(--red-lt);border:1px solid #fecdd3;border-left:4px solid var(--red);color:#9f1239!important;}
/* Stats */
.stat-row{display:flex;gap:.7rem;flex-wrap:wrap;margin-bottom:.8rem;}
.stat-card{flex:1;min-width:90px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:1rem 1.2rem;box-shadow:var(--shadow);text-align:center;}
.stat-n{font-family:'Syne',sans-serif;font-size:2rem;font-weight:800;line-height:1;}
.stat-lbl{font-size:.7rem;color:var(--muted)!important;margin-top:.2rem;}
.c-teal{color:var(--teal)!important;}.c-red{color:var(--red)!important;}
.c-amber{color:var(--amber)!important;}.c-slate{color:#1e293b!important;}
/* File table */
.ftable{border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow);}
.ftable-head{display:grid;grid-template-columns:2fr 2.2fr 88px;background:var(--deep);padding:.6rem 1rem;font-family:'DM Mono',monospace;font-size:.64rem;letter-spacing:1.2px;text-transform:uppercase;color:#475569!important;}
.frow{display:grid;grid-template-columns:2fr 2.2fr 88px;padding:.65rem 1rem;background:var(--surface);border-top:1px solid var(--border);align-items:center;transition:background .15s;}
.frow:hover{background:var(--surface2);}
.f-orig{font-size:.79rem;color:var(--muted)!important;font-family:'DM Mono',monospace;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.f-new{font-family:'DM Mono',monospace;font-size:.82rem;font-weight:500;color:var(--teal)!important;}
.fbadge{font-family:'DM Mono',monospace;font-size:.63rem;padding:3px 8px;border-radius:100px;justify-self:start;}
.fbok{background:var(--teal-lt);color:var(--teal)!important;}
.fberr{background:var(--red-lt);color:var(--red)!important;}
.fbskip{background:var(--amber-lt);color:var(--amber)!important;}
/* Download box */
.dl-box{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:1.2rem 1.4rem;box-shadow:var(--shadow);}
.dl-name{font-family:'DM Mono',monospace;font-size:.88rem;font-weight:500;color:var(--deep)!important;}
.dl-meta{font-size:.78rem;color:var(--muted)!important;margin-top:.3rem;}
/* Log */
.logbox{background:var(--deep);color:#4ade80!important;font-family:'DM Mono',monospace;font-size:.74rem;border-radius:var(--radius);padding:1rem 1.2rem;max-height:240px;overflow-y:auto;line-height:1.75;border:1px solid #1e293b;}
/* Sidebar labels */
.sb-brand{margin-bottom:1.5rem;padding-bottom:1rem;border-bottom:1px solid #1e293b;}
.sb-title{font-family:'Syne',sans-serif;font-size:1.05rem;font-weight:800;color:#f1f5f9!important;}
.sb-sub{font-size:.7rem;color:#475569!important;margin-top:.15rem;}
.sb-sec{font-size:.65rem;letter-spacing:1.5px;text-transform:uppercase;color:#475569!important;margin:1.2rem 0 .4rem;}
/* Buttons */
.stButton>button{font-family:'Syne',sans-serif!important;font-weight:700!important;border-radius:8px!important;border:none!important;padding:.6rem 1.8rem!important;transition:all .18s!important;}
.stButton>button[kind="primary"]{background:var(--teal)!important;color:white!important;}
.stButton>button:hover{opacity:.85!important;transform:translateY(-1px)!important;}
.stProgress>div>div>div{background:var(--teal)!important;}
hr{border-color:var(--border)!important;}
::-webkit-scrollbar{width:5px;height:5px;}
::-webkit-scrollbar-thumb{background:var(--border2);border-radius:10px;}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════
HOSPITALS = {
    "CHUK — University Teaching Hospital of Kigali": "H01",
    "KFH Rwanda — King Faisal Hospital":             "H02",
    "Hôpital La Croix du Sud":                       "H03",
    "CHUB — University Teaching Hospital of Butare": "H04",
}
PROGRAMS  = {"University of Rwanda · CBE · ACE-DS · Data Mining": "ACE-DS_DM"}
SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".dcm", ".dicom"}

MODE_FILES  = "🖼  Individual files"
MODE_ZIP    = "🗜  Zipped folder"
MODE_FOLDER = "📂  Local folder path"
UPLOAD_MODES = [MODE_FILES, MODE_ZIP, MODE_FOLDER]


# ═══════════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════════
_DEFAULTS = dict(
    results=None, zip_bytes=None, zip_filename=None,
    log_lines=[], run_complete=False,
    custom_hospitals={},
    upload_mode=MODE_FILES,
    save_path=str(Path.home() / "Downloads"),
    dataset_folder="",       # original data path — for deletion
    saved_path="",           # where ZIP was saved to disk
    dataset_deleted=False,   # True once disk folder wiped
)
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ═══════════════════════════════════════════════════════════════════
# LOGGER
# ═══════════════════════════════════════════════════════════════════
def _make_logger():
    log = logging.getLogger("MedAnonPro")
    if not log.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s",
                                          datefmt="%H:%M:%S"))
        log.addHandler(h)
    log.setLevel(logging.DEBUG)
    return log
logger = _make_logger()


# ═══════════════════════════════════════════════════════════════════
# ANONYMIZATION CORE
# ═══════════════════════════════════════════════════════════════════

def _wipe(ba: bytearray):
    for i in range(len(ba)): ba[i] = 0

def strip_image(raw: bytes, ext: str) -> bytes:
    """Rebuild from pixels — drops all EXIF/metadata."""
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
    """Wipe 27 sensitive DICOM tags and regenerate UIDs."""
    if not DICOM_AVAILABLE:
        raise RuntimeError("pydicom not installed — run: pip install pydicom")
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
            except Exception: pass
    ds.StudyInstanceUID = generate_uid()
    ds.SeriesInstanceUID = generate_uid()
    ds.SOPInstanceUID = generate_uid()
    buf = io.BytesIO(); ds.save_as(buf); return buf.getvalue()

def make_filename(h, p, t, pid, ext):
    return f"{h}_{p}_{t}_{str(pid).zfill(5)}{ext.lower()}"


# ═══════════════════════════════════════════════════════════════════
# FILE COLLECTION — one function per upload mode
# ═══════════════════════════════════════════════════════════════════

def collect_from_files(uploaded) -> list:
    return [{"name": f.name, "raw": f.read(), "ext": Path(f.name).suffix.lower()}
            for f in uploaded if Path(f.name).suffix.lower() in SUPPORTED_EXT]

def collect_from_zip(zf_obj) -> list:
    entries = []
    with zipfile.ZipFile(io.BytesIO(zf_obj.read())) as zf:
        for info in zf.infolist():
            if info.is_dir() or "__MACOSX" in info.filename: continue
            fname = Path(info.filename)
            if fname.name.startswith("."): continue
            ext = fname.suffix.lower()
            if ext in SUPPORTED_EXT:
                entries.append({"name": fname.name,
                                 "raw":  zf.read(info.filename), "ext": ext})
    return entries

def collect_from_folder(folder: str) -> list:
    root = Path(folder).expanduser().resolve()
    return [{"name": p.name, "raw": p.read_bytes(), "ext": p.suffix.lower()}
            for p in sorted(root.rglob("*"))
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXT]


# ═══════════════════════════════════════════════════════════════════
# PIPELINE
# ═══════════════════════════════════════════════════════════════════

def run_pipeline(entries, h, p, t, bar, status_el):
    results, log = [], [
        "─"*60,
        f"  MedAnon Pro  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"  Hospital:{h}  Program:{p}  Type:{t}  Files:{len(entries)}",
        "─"*60,
    ]
    pid = 1
    for i, e in enumerate(entries):
        bar.progress(int(i / len(entries) * 100))
        status_el.markdown(
            f'<span style="font-family:\'DM Mono\',monospace;font-size:.79rem;color:#64748b;">'
            f'[{i+1}/{len(entries)}] {e["name"]}</span>', unsafe_allow_html=True)
        try:
            clean = strip_dicom(e["raw"]) if e["ext"] in (".dcm",".dicom") \
                    else strip_image(e["raw"], e["ext"])
            nn = make_filename(h, p, t, pid, e["ext"])
            log.append(f"  ✓  {e['name']:<46} → {nn}")
            results.append(dict(original=e["name"], new_name=nn,
                                clean_bytes=clean, ext=e["ext"],
                                status="ok", msg="Anonymized"))
            pid += 1
        except Exception as ex:
            log.append(f"  ✗  {e['name']:<46} {ex}")
            results.append(dict(original=e["name"], new_name="—",
                                clean_bytes=None, ext=e["ext"],
                                status="error", msg=str(ex)))
    bar.progress(100); status_el.empty()
    ok = sum(1 for r in results if r["status"] == "ok")
    log += ["─"*60, f"  OK:{ok}  ERR:{len(results)-ok}", "─"*60]
    return results, log

def pack_zip(results) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for r in results:
            if r["status"] == "ok" and r.get("clean_bytes"):
                zf.writestr(r["new_name"], r["clean_bytes"])
    return buf.getvalue()

def purge(results) -> list:
    """Zero all image buffers in RAM."""
    out = []
    for r in results:
        if r.get("clean_bytes"):
            ba = bytearray(r["clean_bytes"]); _wipe(ba)
        out.append({**r, "clean_bytes": None})
    return out


# ═══════════════════════════════════════════════════════════════════
# DELETION
# ═══════════════════════════════════════════════════════════════════

def delete_on_disk(path: str) -> tuple:
    """Delete a file or folder from disk. Returns (ok, message)."""
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return False, f"Not found: {p}"
    shutil.rmtree(p) if p.is_dir() else p.unlink()
    return True, str(p)

def clear_session():
    """Wipe all run-related session state (in-memory purge)."""
    for k in ["results","zip_bytes","zip_filename","log_lines",
               "run_complete","saved_path"]:
        st.session_state.pop(k, None)
    for _k, _v in _DEFAULTS.items():
        if _k not in st.session_state:
            st.session_state[_k] = _v


# ═══════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div class="sb-brand">
      <div class="sb-title">🛡 MedAnon Pro</div>
      <div class="sb-sub">by Vedaste NYANDWI &nbsp;·&nbsp; Secure · Private</div>
    </div>""", unsafe_allow_html=True)

    # Hospital
    all_hospitals = {**HOSPITALS, **st.session_state["custom_hospitals"]}
    st.markdown('<div class="sb-sec">🏥 Hospital</div>', unsafe_allow_html=True)
    sel_hospital = st.selectbox("Hospital", list(all_hospitals.keys()),
                                 label_visibility="collapsed")
    h_code = all_hospitals[sel_hospital]

    with st.expander("➕  Add a hospital"):
        nn = st.text_input("Name", placeholder="e.g. Rwanda Military Hospital", key="nh_name")
        nc = st.text_input("Code", value=f"H{str(len(all_hospitals)+1).zfill(2)}",
                            max_chars=6, key="nh_code")
        if st.button("Add hospital", use_container_width=True):
            nn2, nc2 = nn.strip(), nc.strip().upper()
            if not nn2: st.error("Enter a name.")
            elif nc2 in set(all_hospitals.values()): st.error(f"Code '{nc2}' already used.")
            elif nn2 in all_hospitals: st.warning("Already exists.")
            else:
                st.session_state["custom_hospitals"][nn2] = nc2; st.rerun()
        for hname, hcode in list(st.session_state["custom_hospitals"].items()):
            c1, c2 = st.columns([4,1])
            c1.markdown(f'<span style="font-family:\'DM Mono\',monospace;font-size:.72rem;color:#e2e8f0;">{hcode}</span> <span style="font-size:.7rem;color:#64748b;">{hname}</span>', unsafe_allow_html=True)
            if c2.button("✕", key=f"rm_{hcode}"):
                del st.session_state["custom_hospitals"][hname]; st.rerun()

    # Program
    st.markdown('<div class="sb-sec">🎓 Program</div>', unsafe_allow_html=True)
    p_code = PROGRAMS[st.selectbox("Program", list(PROGRAMS.keys()), label_visibility="collapsed")]

    # Image type
    st.markdown('<div class="sb-sec">🩻 Image Type</div>', unsafe_allow_html=True)
    img_type = st.radio("Type", ["🫁  Chest X-ray","🔬  Other medical images"],
                         label_visibility="collapsed")
    img_code = "CXR" if "Chest" in img_type else "IMG"

    # Upload mode
    st.markdown('<div class="sb-sec">📥 Upload Mode</div>', unsafe_allow_html=True)
    upload_mode = st.radio("Upload mode", UPLOAD_MODES,
                            index=UPLOAD_MODES.index(st.session_state["upload_mode"]),
                            label_visibility="collapsed")
    st.session_state["upload_mode"] = upload_mode

    # Data input — changes per mode
    st.markdown('<div class="sb-sec">📁 Data</div>', unsafe_allow_html=True)
    uploaded_files = uploaded_zip = None
    folder_path    = ""

    if upload_mode == MODE_FILES:
        uploaded_files = st.file_uploader("Files", type=["jpg","jpeg","png","dcm"],
                                           accept_multiple_files=True,
                                           label_visibility="collapsed")
        if uploaded_files:
            dcm = sum(1 for f in uploaded_files
                      if Path(f.name).suffix.lower() in (".dcm",".dicom"))
            st.markdown(f'<div style="margin-top:.5rem;background:#1e293b;border-radius:8px;padding:.6rem 1rem;font-size:.77rem;color:#94a3b8;"><b style="color:#e2e8f0;">{len(uploaded_files)}</b> file(s) &ensp;·&ensp; DICOM: <b style="color:#a78bfa;">{dcm}</b></div>', unsafe_allow_html=True)

    elif upload_mode == MODE_ZIP:
        uploaded_zip = st.file_uploader("ZIP", type=["zip"], label_visibility="collapsed")
        if uploaded_zip:
            st.markdown(f'<div style="margin-top:.5rem;background:#1e293b;border-radius:8px;padding:.6rem 1rem;font-size:.77rem;color:#94a3b8;">📦 {uploaded_zip.name} &ensp; {uploaded_zip.size/1024:.1f} KB</div>', unsafe_allow_html=True)

    else:  # MODE_FOLDER
        folder_path = st.text_input("Folder path", key="fp_input",
                                     value=st.session_state.get("fp_input",""),
                                     placeholder="e.g. D:\\Hospital\\Radiology\\2024",
                                     label_visibility="collapsed").strip()
        if folder_path:
            fp = Path(folder_path).expanduser()
            if fp.is_dir():
                n_img = sum(1 for p in fp.rglob("*") if p.suffix.lower() in SUPPORTED_EXT)
                st.markdown(f'<div style="margin-top:.4rem;font-size:.7rem;color:#4ade80;font-family:\'DM Mono\',monospace;">✓ {n_img} image(s) found</div>', unsafe_allow_html=True)
                if not st.session_state["dataset_folder"]:
                    st.session_state["dataset_folder"] = folder_path
            else:
                st.markdown('<div style="margin-top:.4rem;font-size:.7rem;color:#f87171;">✗ Folder not found</div>', unsafe_allow_html=True)

    # Save destination
    st.markdown('<div class="sb-sec">💾 Save ZIP To</div>', unsafe_allow_html=True)
    save_path = st.text_input("Save path", value=st.session_state["save_path"],
                               placeholder="e.g. D:\\Research\\Anonymized",
                               label_visibility="collapsed").strip()
    st.session_state["save_path"] = save_path
    if save_path:
        sp = Path(save_path).expanduser()
        if sp.exists():
            st.markdown(f'<div style="font-size:.7rem;color:#4ade80;font-family:\'DM Mono\',monospace;">✓ {sp}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="font-size:.7rem;color:#f59e0b;">⚠ Will be created</div>', unsafe_allow_html=True)

    # Original dataset path
    st.markdown('<div class="sb-sec">🗑 Original Dataset Path</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:.7rem;color:#64748b;margin-bottom:.35rem;">Used to delete originals after anonymization.</div>', unsafe_allow_html=True)
    df_input = st.text_input("Dataset path", value=st.session_state["dataset_folder"],
                              placeholder="e.g. D:\\Hospital\\Radiology\\2024",
                              label_visibility="collapsed",
                              key="dataset_folder_widget").strip()
    st.session_state["dataset_folder"] = df_input
    if df_input:
        dfp = Path(df_input).expanduser()
        col = "#4ade80" if dfp.exists() else "#f87171"
        lbl = f"✓ Exists" if dfp.exists() else "✗ Not found"
        st.markdown(f'<div style="font-size:.7rem;color:{col};font-family:\'DM Mono\',monospace;">{lbl} — {dfp}</div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-top:1.8rem;padding-top:1rem;border-top:1px solid #1e293b;font-size:.68rem;color:#334155;line-height:1.8;">
      <b style="color:#475569;">Output naming</b><br>
      <span style="color:#0d9488;font-family:'DM Mono',monospace;">HXX_ACE-DS_DM_CXR_NNNNN.ext</span>
    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# MAIN PANEL
# ═══════════════════════════════════════════════════════════════════

st.markdown("""
<div class="app-header">
  <div class="hdr-icon">🛡</div>
  <div>
    <div class="hdr-title">Medical Image Anonymization</div>
    <div class="hdr-sub">Strip metadata · Rename with structured IDs · Purge from session &amp; disk after export</div>
    <div class="hdr-badges">
      <span class="badge b-teal">EXIF STRIPPED</span>
      <span class="badge b-teal">DICOM ANONYMIZED</span>
      <span class="badge b-red">MEMORY PURGED</span>
      <span class="badge b-red">DISK DELETED</span>
      <span class="badge b-slate">LOCAL ONLY</span>
      <span class="badge b-purple">3 UPLOAD MODES</span>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

# Config pills
example = f"{h_code}_{p_code}_{img_code}_00001.jpg"
st.markdown(f"""
<div class="cfg-strip">
  <div class="cfg-pill"><span class="cfg-icon">🏥</span><div><div class="cfg-lbl">HOSPITAL</div><div class="cfg-val">{h_code}</div></div></div>
  <div class="cfg-pill"><span class="cfg-icon">🎓</span><div><div class="cfg-lbl">PROGRAM</div><div class="cfg-val">{p_code}</div></div></div>
  <div class="cfg-pill"><span class="cfg-icon">🩻</span><div><div class="cfg-lbl">TYPE</div><div class="cfg-val">{img_code}</div></div></div>
  <div class="cfg-pill"><span class="cfg-icon">🏷</span><div><div class="cfg-lbl">EXAMPLE OUTPUT</div><div class="cfg-val">{example}</div></div></div>
</div>""", unsafe_allow_html=True)

# Upload mode indicator
m1, m2, m3 = st.columns(3)
for col, mode, icon, label, hint in [
    (m1, MODE_FILES,  "🖼", "Individual Files",  "JPG · PNG · DICOM"),
    (m2, MODE_ZIP,    "🗜", "Zipped Folder",      "Auto-extracted during run"),
    (m3, MODE_FOLDER, "📂", "Local Folder Path",  "Scanned recursively"),
]:
    col.markdown(f"""
    <div class="umode-card {'active' if upload_mode == mode else ''}">
      <div class="umode-icon">{icon}</div>
      <div class="umode-label">{label}</div>
      <div class="umode-hint">{hint}</div>
    </div>""", unsafe_allow_html=True)

# Has input?
has_input = (
    (upload_mode == MODE_FILES  and bool(uploaded_files)) or
    (upload_mode == MODE_ZIP    and bool(uploaded_zip))   or
    (upload_mode == MODE_FOLDER and bool(folder_path)
                                and Path(folder_path).expanduser().is_dir())
)

# ─────────────────────────────────────────────────────────────────
# EMPTY STATE
# ─────────────────────────────────────────────────────────────────
if not has_input and not st.session_state["run_complete"]:
    hints = {
        MODE_FILES:  ("🖼", "Select image files using the uploader in the sidebar"),
        MODE_ZIP:    ("🗜", "Upload a .zip file containing your image folder in the sidebar"),
        MODE_FOLDER: ("📂", "Paste your dataset folder path in the sidebar"),
    }
    ico, msg = hints[upload_mode]
    st.markdown(f"""
    <div style="text-align:center;padding:4rem 2rem;background:white;
                border:2px dashed #e2e8f0;border-radius:12px;margin-top:1rem;">
      <div style="font-size:3.5rem;margin-bottom:1rem;">{ico}</div>
      <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;
                  color:#0f172a;margin-bottom:.4rem;">No images loaded yet</div>
      <div style="color:#64748b;font-size:.88rem;">{msg}</div>
    </div>""", unsafe_allow_html=True)

else:
    # ─────────────────────────────────────────────────────────────
    # RUN BUTTON
    # ─────────────────────────────────────────────────────────────
    if not st.session_state["run_complete"]:
        col_btn, _ = st.columns([1, 3])
        with col_btn:
            run = st.button("🛡  Run Anonymization", type="primary",
                             use_container_width=True)
        if run:
            bar    = st.progress(0)
            status = st.empty()

            # Collect entries per mode
            if upload_mode == MODE_FILES:
                entries = collect_from_files(uploaded_files)
                src_lbl = f"{len(uploaded_files)} file(s)"
            elif upload_mode == MODE_ZIP:
                status.markdown('<span style="font-size:.79rem;color:#7c3aed;">🗜 Extracting ZIP…</span>', unsafe_allow_html=True)
                try:
                    entries = collect_from_zip(uploaded_zip)
                    src_lbl = f"ZIP: {uploaded_zip.name}"
                except Exception as e:
                    st.error(f"ZIP extraction failed: {e}"); st.stop()
            else:
                status.markdown('<span style="font-size:.79rem;color:#64748b;">📂 Scanning folder…</span>', unsafe_allow_html=True)
                entries = collect_from_folder(folder_path)
                src_lbl = f"Folder: {folder_path}"
                if not st.session_state["dataset_folder"]:
                    st.session_state["dataset_folder"] = folder_path

            if not entries:
                st.warning("No supported image files found."); st.stop()

            results, log_lines = run_pipeline(
                entries, h_code, p_code, img_code, bar, status)

            zip_bytes = pack_zip(results)
            zip_fname = f"anonymized_{h_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

            results = purge(results)
            log_lines.append("  🗑  Memory purge complete — all buffers zeroed")
            log_lines.append(f"  📦  Source: {src_lbl}")
            logger.info("Memory purge done. %d files.", len(results))

            st.session_state.update(dict(
                results=results, zip_bytes=zip_bytes,
                zip_filename=zip_fname, log_lines=log_lines,
                run_complete=True))
            st.rerun()

    # ─────────────────────────────────────────────────────────────
    # RESULTS PANEL
    # ─────────────────────────────────────────────────────────────
    if st.session_state["run_complete"] and st.session_state.get("results"):
        results = st.session_state["results"]
        ok_n  = sum(1 for r in results if r["status"] == "ok")
        err_n = sum(1 for r in results if r["status"] == "error")
        sk_n  = sum(1 for r in results if r["status"] == "skip")

        # Summary stats
        st.markdown('<div class="sec-h">📊 Summary</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="stat-row">
          <div class="stat-card"><div class="stat-n c-slate">{len(results)}</div><div class="stat-lbl">Total</div></div>
          <div class="stat-card"><div class="stat-n c-teal">{ok_n}</div><div class="stat-lbl">Anonymized</div></div>
          <div class="stat-card"><div class="stat-n c-amber">{sk_n}</div><div class="stat-lbl">Skipped</div></div>
          <div class="stat-card"><div class="stat-n c-red">{err_n}</div><div class="stat-lbl">Errors</div></div>
        </div>""", unsafe_allow_html=True)

        st.markdown("""
        <div class="alert alert-ok">
          <span>✅</span>
          <div><b>Memory purge complete.</b> All original image buffers zeroed. Only the anonymized ZIP remains.</div>
        </div>""", unsafe_allow_html=True)

        # Renamed file list
        st.markdown('<div class="sec-h">📄 Anonymized File List</div>', unsafe_allow_html=True)
        st.markdown('<div class="ftable"><div class="ftable-head"><span>Original filename</span><span>Anonymized filename</span><span>Status</span></div>', unsafe_allow_html=True)
        for r in results:
            icon = "🩻" if r["ext"] in (".dcm",".dicom") else "🖼️"
            bc, bt = {"ok":("fbok","✓ OK"),"error":("fberr","✗ Err"),"skip":("fbskip","⚠ Skip")}[r["status"]]
            st.markdown(f'<div class="frow"><span class="f-orig">{icon} {r["original"]}</span><span class="f-new">{r["new_name"]}</span><span class="fbadge {bc}">{bt}</span></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ── Export ──────────────────────────────────────────────
        if ok_n > 0 and st.session_state.get("zip_bytes"):
            st.markdown('<div class="sec-h">⬇ Export ZIP</div>', unsafe_allow_html=True)
            zip_b  = st.session_state["zip_bytes"]
            zip_fn = st.session_state["zip_filename"]
            save_dir = st.session_state["save_path"].strip()

            col_dl, col_save = st.columns(2)
            with col_dl:
                st.markdown('<div style="font-size:.72rem;color:#64748b;margin-bottom:.4rem;">🌐 Browser download</div>', unsafe_allow_html=True)
                st.download_button(f"⬇  Download ZIP  ({ok_n} files)",
                    data=zip_b, file_name=zip_fn, mime="application/zip",
                    use_container_width=True, type="primary")
                st.markdown('<div style="font-size:.7rem;color:#94a3b8;margin-top:.3rem;">Saves to your browser default folder</div>', unsafe_allow_html=True)

            with col_save:
                st.markdown('<div style="font-size:.72rem;color:#64748b;margin-bottom:.4rem;">📁 Save to specific folder</div>', unsafe_allow_html=True)
                if not save_dir:
                    st.markdown('<div style="font-size:.82rem;color:#d97706;">⚠ Set "Save ZIP To" path in sidebar first.</div>', unsafe_allow_html=True)
                else:
                    if st.button("💾  Save ZIP to folder", use_container_width=True):
                        try:
                            dest = Path(save_dir).expanduser()
                            dest.mkdir(parents=True, exist_ok=True)
                            out_path = dest / zip_fn
                            out_path.write_bytes(zip_b)
                            st.session_state["saved_path"] = str(out_path)
                            logger.info("ZIP saved: %s", out_path)
                        except Exception as e:
                            st.error(f"Save failed: {e}")
                    if st.session_state.get("saved_path"):
                        st.markdown(f'<div style="font-size:.7rem;color:#4ade80;font-family:\'DM Mono\',monospace;margin-top:.3rem;word-break:break-all;">✓ {st.session_state["saved_path"]}</div>', unsafe_allow_html=True)

            st.markdown(f"""
            <div class="dl-box" style="margin-top:.75rem;">
              <div class="dl-name">📦 {zip_fn}</div>
              <div class="dl-meta">{len(zip_b)/1024:.1f} KB &ensp;·&ensp; {ok_n} file(s) &ensp;·&ensp; In-memory buffers zeroed</div>
            </div>""", unsafe_allow_html=True)

        # ── Delete Original Dataset ─────────────────────────────
        # Single unified deletion: session (in-memory) + disk (folder)
        st.markdown('<div class="sec-h">🗑 Delete Original Dataset</div>', unsafe_allow_html=True)
        dataset_folder = st.session_state.get("dataset_folder","").strip()

        if st.session_state.get("dataset_deleted"):
            # ── Proof of deletion ──────────────────────────────
            st.markdown("""
            <div class="alert alert-ok">
              <span style="font-size:1.3rem;">🗑</span>
              <div>
                <b>Original dataset permanently deleted.</b><br>
                ✓ Uploaded data cleared from this browser session<br>
                ✓ Original folder removed from the computer's hard drive<br><br>
                No copy of the original patient images remains on this machine.
                This can be shown to the radiology department as confirmation.
              </div>
            </div>""", unsafe_allow_html=True)

        elif not dataset_folder:
            st.markdown("""
            <div class="alert alert-info">
              <span>ℹ️</span>
              <div style="font-size:.83rem;">
                Set the <b>Original Dataset Path</b> in the sidebar to enable deletion.
                When using folder mode it is filled automatically.
              </div>
            </div>""", unsafe_allow_html=True)

        else:
            df_path     = Path(dataset_folder).expanduser()
            disk_exists = df_path.exists()

            st.markdown(f"""
            <div class="alert alert-danger">
              <span style="font-size:1.2rem;">⚠️</span>
              <div>
                <b>One button — two deletions:</b>
                <ol style="margin:.4rem 0 0 1rem;padding:0;font-size:.83rem;">
                  <li>Clear all uploaded data from this browser session (in-memory)</li>
                  <li>Permanently delete the folder from your computer's hard drive</li>
                </ol>
                <div style="font-family:'DM Mono',monospace;font-size:.78rem;margin-top:.5rem;word-break:break-all;">
                  📂 {df_path}
                </div>
                <div style="font-size:.78rem;margin-top:.3rem;">
                  {"<b style='color:#e11d48;'>⚠ Folder not found — only session will be cleared</b>"
                   if not disk_exists else
                   "<span style='color:#9f1239;font-weight:600;'>Folder confirmed on disk — will be permanently removed</span>"}
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

            confirmed = st.checkbox(
                "✅  I have saved the anonymized ZIP. Delete the original dataset from session AND disk.",
                key="delete_confirm")

            del_col, _ = st.columns([1, 3])
            with del_col:
                del_btn = st.button("🗑  Delete Now",
                                     disabled=not confirmed,
                                     use_container_width=True)

            if del_btn and confirmed:
                ts  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log = []

                # Step 1 — clear session memory
                clear_session()
                log.append(f"  🗑  SESSION CLEARED  [{ts}]")

                # Step 2 — delete from disk
                if disk_exists:
                    ok_del, msg_del = delete_on_disk(dataset_folder)
                    log.append(
                        f"  🗑  DISK DELETED  {dataset_folder}  [{ts}]"
                        if ok_del else
                        f"  ✗  DISK DELETE FAILED  {msg_del}  [{ts}]")
                    if ok_del:
                        logger.warning("Disk deletion: %s", msg_del)
                    else:
                        st.error(f"Disk deletion failed: {msg_del}")

                # Persist evidence
                st.session_state["dataset_deleted"] = True
                st.session_state["run_complete"]    = True
                st.session_state.setdefault("log_lines", []).extend(log)
                st.rerun()

        # ── Anonymization Log ───────────────────────────────────
        with st.expander("🗒  Anonymization Log", expanded=False):
            log_txt = "\n".join(st.session_state.get("log_lines", []))
            st.markdown(f'<div class="logbox"><pre>{log_txt}</pre></div>', unsafe_allow_html=True)
            st.download_button("⬇  Download log (.txt)", data=log_txt.encode(),
                file_name=f"anon_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain")

        # ── New session ─────────────────────────────────────────
        st.markdown("---")
        col_r, _ = st.columns([1, 4])
        with col_r:
            if st.button("🔄  New session", use_container_width=True):
                for k in ["results","zip_bytes","zip_filename","log_lines","run_complete",
                           "saved_path","dataset_deleted","delete_confirm","dataset_folder"]:
                    st.session_state.pop(k, None)
                for _k, _v in _DEFAULTS.items():
                    if _k not in st.session_state: st.session_state[_k] = _v
                st.rerun()


# ═══════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("""
<div style="display:flex;justify-content:space-between;align-items:center;
            flex-wrap:wrap;gap:.5rem;padding:.3rem 0 .8rem;">
  <div style="font-family:'DM Mono',monospace;font-size:.7rem;color:#64748b;">
    © <b style="color:#0f172a;">Vedaste NYANDWI</b> &ensp;·&ensp; MedAnon Pro
    &ensp;·&ensp; All processing local — patient data never transmitted
  </div>
  <div style="font-family:'DM Mono',monospace;font-size:.68rem;color:#94a3b8;">
    University of Rwanda · CBE · ACE-DS · Data Mining
  </div>
</div>""", unsafe_allow_html=True)
