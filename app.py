"""
╔══════════════════════════════════════════════════════════════════════╗
║   MedAnon Pro  — Secure Medical Image Anonymization System          ║
║   University of Rwanda · CBE · ACE-DS · Data Mining                ║
╚══════════════════════════════════════════════════════════════════════╝

Run:
    pip install -r requirements.txt
    streamlit run app.py
"""

import streamlit as st
import io
import os
import shutil
import zipfile
import logging
from pathlib import Path
from datetime import datetime
from PIL import Image

# ── Optional DICOM support ──────────────────────────────────────────
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
st.set_page_config(
    page_title="MedAnon Pro",
    page_icon="🛡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════
# CSS — Sterile-White Lab aesthetic
# Syne (display) + DM Mono (data) · White surface · Deep slate bg
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');

:root {
  --bg:         #eef2f7;
  --surface:    #ffffff;
  --surface2:   #f8fafc;
  --border:     #e2e8f0;
  --border2:    #cbd5e1;
  --deep:       #0f172a;
  --slate:      #1e293b;
  --muted:      #64748b;
  --dim:        #94a3b8;
  --teal:       #0d9488;
  --teal-lt:    #ccfbf1;
  --teal-glow:  rgba(13,148,136,.12);
  --red:        #e11d48;
  --red-lt:     #ffe4e6;
  --amber:      #d97706;
  --amber-lt:   #fef3c7;
  --blue:       #2563eb;
  --blue-lt:    #dbeafe;
  --radius:     10px;
  --shadow:     0 1px 3px rgba(15,23,42,.05), 0 4px 16px rgba(15,23,42,.06);
  --shadow-lg:  0 4px 24px rgba(15,23,42,.12);
}

html, body, [class*="css"] {
  font-family: 'DM Sans', sans-serif !important;
  background-color: var(--bg) !important;
  color: var(--deep) !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
  background: var(--deep) !important;
}
section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
section[data-testid="stSidebar"] label {
  color: #94a3b8 !important;
  font-size: .78rem !important;
  letter-spacing: .3px;
}
section[data-testid="stSidebar"] .stSelectbox > div > div,
section[data-testid="stSidebar"] .stTextInput > div > div {
  background: #1e293b !important;
  border: 1px solid #334155 !important;
  border-radius: 8px !important;
}
section[data-testid="stSidebar"] .stFileUploader > div {
  background: #1e293b !important;
  border: 1px dashed #334155 !important;
  border-radius: 8px !important;
}

/* Main area */
.main .block-container {
  background: var(--bg) !important;
  padding: 2rem 2.5rem 3rem;
  max-width: 1100px;
}

/* ─ Header ─ */
.app-header {
  display: flex;
  align-items: flex-start;
  gap: 1.2rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-top: 4px solid var(--teal);
  border-radius: var(--radius);
  padding: 1.8rem 2rem;
  margin-bottom: 1.5rem;
  box-shadow: var(--shadow);
}
.hdr-icon { font-size: 2.4rem; line-height: 1; margin-top: .15rem; }
.hdr-title {
  font-family: 'Syne', sans-serif;
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--deep) !important;
  letter-spacing: -.5px;
  line-height: 1.1;
  margin: 0 0 .3rem;
}
.hdr-sub { font-size: .88rem; color: var(--muted) !important; }
.hdr-badges { display: flex; gap: .45rem; margin-top: .65rem; flex-wrap: wrap; }
.badge {
  font-family: 'DM Mono', monospace;
  font-size: .63rem;
  letter-spacing: .5px;
  padding: 3px 10px;
  border-radius: 100px;
  font-weight: 500;
}
.b-teal  { background: var(--teal-lt);  color: var(--teal)  !important; }
.b-slate { background: #f1f5f9; color: var(--slate) !important;
           border: 1px solid var(--border); }
.b-red   { background: var(--red-lt);   color: var(--red)   !important; }

/* ─ Section heading ─ */
.sec-h {
  font-family: 'Syne', sans-serif;
  font-size: .68rem;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--muted) !important;
  margin: 1.8rem 0 .75rem;
  display: flex;
  align-items: center;
  gap: .5rem;
}
.sec-h::after { content:""; flex:1; height:1px; background:var(--border); }

/* ─ Config strip ─ */
.cfg-strip { display:flex; gap:.7rem; flex-wrap:wrap; margin-bottom:1rem; }
.cfg-pill {
  display:flex; align-items:center; gap:.6rem;
  background:var(--surface); border:1px solid var(--border);
  border-radius:8px; padding:.55rem 1rem;
  box-shadow:var(--shadow); flex:1; min-width:170px;
}
.cfg-icon { font-size:1.1rem; }
.cfg-lbl  { font-size:.68rem; color:var(--dim) !important; margin-bottom:.05rem; }
.cfg-val  { font-family:'DM Mono',monospace; font-size:.85rem;
            font-weight:500; color:var(--deep) !important; }

/* ─ Alert banners ─ */
.alert {
  display:flex; align-items:flex-start; gap:.8rem;
  border-radius:var(--radius); padding:1rem 1.2rem;
  margin:.8rem 0; font-size:.84rem;
}
.alert-warn {
  background:#fff7ed; border:1px solid #fed7aa;
  border-left:4px solid var(--amber); color:#92400e !important;
}
.alert-ok {
  background:#f0fdf4; border:1px solid #bbf7d0;
  border-left:4px solid #16a34a; color:#14532d !important;
}
.alert-info {
  background:#eff6ff; border:1px solid #bfdbfe;
  border-left:4px solid var(--blue); color:#1e40af !important;
}
.alert-danger {
  background:var(--red-lt); border:1px solid #fecdd3;
  border-left:4px solid var(--red); color:#9f1239 !important;
}

/* ─ Stat row ─ */
.stat-row { display:flex; gap:.7rem; flex-wrap:wrap; margin-bottom:.8rem; }
.stat-card {
  flex:1; min-width:90px;
  background:var(--surface); border:1px solid var(--border);
  border-radius:var(--radius); padding:1rem 1.2rem;
  box-shadow:var(--shadow); text-align:center;
}
.stat-n {
  font-family:'Syne',sans-serif; font-size:2rem;
  font-weight:800; line-height:1;
}
.stat-lbl { font-size:.7rem; color:var(--muted) !important; margin-top:.2rem; }
.c-teal  { color:var(--teal)  !important; }
.c-red   { color:var(--red)   !important; }
.c-amber { color:var(--amber) !important; }
.c-slate { color:var(--slate) !important; }

/* ─ File table ─ */
.ftable { border:1px solid var(--border); border-radius:var(--radius);
          overflow:hidden; box-shadow:var(--shadow); }
.ftable-head {
  display:grid; grid-template-columns:2fr 2.2fr 88px;
  background:var(--deep); padding:.6rem 1rem;
  font-family:'DM Mono',monospace; font-size:.64rem;
  letter-spacing:1.2px; text-transform:uppercase;
  color:#475569 !important;
}
.frow {
  display:grid; grid-template-columns:2fr 2.2fr 88px;
  padding:.65rem 1rem; background:var(--surface);
  border-top:1px solid var(--border); align-items:center;
  transition:background .15s;
}
.frow:hover { background:var(--surface2); }
.f-orig { font-size:.79rem; color:var(--muted) !important;
          font-family:'DM Mono',monospace; overflow:hidden;
          text-overflow:ellipsis; white-space:nowrap; }
.f-new  { font-family:'DM Mono',monospace; font-size:.82rem;
          font-weight:500; color:var(--teal) !important; }
.fbadge {
  font-family:'DM Mono',monospace; font-size:.63rem;
  padding:3px 8px; border-radius:100px; text-align:center;
  justify-self:start;
}
.fbok   { background:var(--teal-lt); color:var(--teal)  !important; }
.fberr  { background:var(--red-lt);  color:var(--red)   !important; }
.fbskip { background:var(--amber-lt);color:var(--amber) !important; }

/* ─ Download box ─ */
.dl-box {
  background:var(--surface); border:1px solid var(--border);
  border-radius:var(--radius); padding:1.2rem 1.4rem;
  box-shadow:var(--shadow);
}
.dl-name { font-family:'DM Mono',monospace; font-size:.88rem;
           font-weight:500; color:var(--deep) !important; }
.dl-meta { font-size:.78rem; color:var(--muted) !important; margin-top:.3rem; }

/* ─ Log box ─ */
.logbox {
  background:var(--deep); color:#4ade80 !important;
  font-family:'DM Mono',monospace; font-size:.74rem;
  border-radius:var(--radius); padding:1rem 1.2rem;
  max-height:240px; overflow-y:auto; line-height:1.75;
  border:1px solid #1e293b;
}

/* ─ Sidebar brand ─ */
.sb-brand { margin-bottom:1.5rem; padding-bottom:1rem; border-bottom:1px solid #1e293b; }
.sb-title { font-family:'Syne',sans-serif; font-size:1.05rem;
            font-weight:800; color:#f1f5f9 !important; letter-spacing:-.3px; }
.sb-sub   { font-size:.7rem; color:#475569 !important; margin-top:.15rem; }
.sb-sec   { font-size:.65rem; letter-spacing:1.5px; text-transform:uppercase;
            color:#475569 !important; margin:1.2rem 0 .4rem; }

/* ─ Buttons ─ */
.stButton > button {
  font-family:'Syne',sans-serif !important; font-weight:700 !important;
  border-radius:8px !important; border:none !important;
  letter-spacing:.3px !important; padding:.6rem 1.8rem !important;
  transition:all .18s !important;
}
.stButton > button[kind="primary"] {
  background:var(--teal) !important; color:white !important;
}
.stButton > button:hover { opacity:.85 !important; transform:translateY(-1px) !important; }

/* Progress */
.stProgress > div > div > div { background:var(--teal) !important; }
hr { border-color:var(--border) !important; }

::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:var(--border2); border-radius:10px; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════

HOSPITALS = {
    "CHUK — University Teaching Hospital of Kigali":  "H01",
    "KFH Rwanda — King Faisal Hospital":              "H02",
    "Hôpital La Croix du Sud":                        "H03",
    "CHUB — University Teaching Hospital of Butare":  "H04",
}

PROGRAMS = {
    "University of Rwanda · CBE · ACE-DS · Data Mining": "ACE-DS_DM",
}

SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".dcm", ".dicom"}


# ═══════════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════════
_DEFAULTS = dict(
    results=None, zip_bytes=None, zip_filename=None,
    log_lines=[], purged=False, run_complete=False,
    custom_hospitals={},   # name → code, user-added hospitals
    save_path="",          # user-chosen download folder
    dataset_deleted=False, # True once original dataset folder is wiped
)
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ═══════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════
def get_logger():
    log = logging.getLogger("MedAnonPro")
    log.setLevel(logging.DEBUG)
    if not log.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter(
            "%(asctime)s  %(levelname)-8s  %(message)s", datefmt="%H:%M:%S"))
        log.addHandler(h)
    return log

logger = get_logger()


# ═══════════════════════════════════════════════════════════════════
# ANONYMIZATION UTILITIES
# ═══════════════════════════════════════════════════════════════════

def secure_wipe(ba: bytearray) -> None:
    """Overwrite every byte with zero before releasing."""
    for i in range(len(ba)):
        ba[i] = 0


def strip_image_metadata(raw: bytes, ext: str) -> bytes:
    """
    Reconstruct image from raw pixel data (drops ALL metadata/EXIF).
    Saves at maximum quality.
    """
    img   = Image.open(io.BytesIO(raw))
    clean = Image.new(img.mode, img.size)
    clean.putdata(list(img.getdata()))
    buf = io.BytesIO()
    if ext in (".jpg", ".jpeg"):
        clean.save(buf, format="JPEG", quality=95, subsampling=0)
    else:
        clean.save(buf, format="PNG")
    return buf.getvalue()


def anonymize_dicom_file(raw: bytes) -> bytes:
    """
    Wipe 25+ sensitive DICOM tags and regenerate all UIDs.
    Requires pydicom.
    """
    if not DICOM_AVAILABLE:
        raise RuntimeError(
            "pydicom not installed — run: pip install pydicom")
    ds = pydicom.dcmread(io.BytesIO(raw))
    wipe_tags = [
        "PatientName", "PatientID", "PatientBirthDate", "PatientSex",
        "PatientAge", "PatientWeight", "PatientAddress",
        "PatientTelephoneNumbers", "PatientMotherBirthName",
        "OtherPatientNames", "OtherPatientIDs",
        "InstitutionName", "InstitutionAddress",
        "InstitutionalDepartmentName",
        "ReferringPhysicianName", "PerformingPhysicianName",
        "RequestingPhysician", "OperatorsName",
        "StudyDate", "SeriesDate", "AcquisitionDate", "ContentDate",
        "StudyTime", "SeriesTime", "AcquisitionTime",
        "AccessionNumber", "StudyID",
        "RequestedProcedureDescription",
    ]
    for tag in wipe_tags:
        if hasattr(ds, tag):
            try:
                setattr(ds, tag, "ANONYMIZED")
            except Exception:
                pass
    ds.StudyInstanceUID  = generate_uid()
    ds.SeriesInstanceUID = generate_uid()
    ds.SOPInstanceUID    = generate_uid()
    buf = io.BytesIO()
    ds.save_as(buf)
    return buf.getvalue()


def make_filename(h_code: str, p_code: str, img_code: str,
                  pid: int, ext: str) -> str:
    """
    Build structured anonymized filename.
    Format: <HospitalCode>_<ProgramCode>_<ImageTypeCode>_<PatientID>.<ext>
    Example: H02_ACE-DS_DM_CXR_00001.jpg
    """
    return f"{h_code}_{p_code}_{img_code}_{str(pid).zfill(5)}{ext.lower()}"


def build_zip(results: list) -> bytes:
    """Zip all successfully anonymized files."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for r in results:
            if r["status"] == "ok" and r.get("clean_bytes"):
                zf.writestr(r["new_name"], r["clean_bytes"])
    return buf.getvalue()


def purge_buffers(results: list) -> list:
    """
    Zero-out every clean_bytes buffer and return a sanitised copy.
    This is the core privacy guarantee — no image data lingers in RAM.
    """
    cleaned = []
    for r in results:
        if r.get("clean_bytes"):
            ba = bytearray(r["clean_bytes"])
            secure_wipe(ba)
        cleaned.append({**r, "clean_bytes": None})
    return cleaned


def save_zip_to_folder(zip_bytes: bytes, folder: str, filename: str) -> str:
    """
    Save the ZIP archive to a user-specified folder on disk.
    Returns the full path of the saved file, or raises on error.
    """
    dest_dir = Path(folder).expanduser().resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filename
    dest_path.write_bytes(zip_bytes)
    return str(dest_path)


def delete_dataset_folder(folder: str) -> tuple[bool, str]:
    """
    Permanently delete a folder and all its contents from disk.
    Returns (success: bool, message: str).
    This gives the hospital radiology department visible proof that
    the original dataset has been removed from this machine.
    """
    p = Path(folder).expanduser().resolve()
    if not p.exists():
        return False, f"Path not found: {p}"
    if not p.is_dir():
        # It's a file — delete it directly
        p.unlink()
        return True, f"File deleted: {p}"
    shutil.rmtree(p)
    return True, f"Folder deleted: {p}"


# ═══════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════
with st.sidebar:

    st.markdown("""
    <div class="sb-brand">
      <div class="sb-title">🛡 MedAnon Pro</div>
      <div class="sb-sub">by Vedaste NYANDWI &nbsp;·&nbsp; Secure · Private</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Merge built-in + user-added hospitals ──────────────────────
    all_hospitals = {**HOSPITALS, **st.session_state["custom_hospitals"]}

    st.markdown('<div class="sb-sec">🏥 Hospital</div>', unsafe_allow_html=True)
    sel_hospital = st.selectbox(
        "Hospital", list(all_hospitals.keys()), label_visibility="collapsed")
    h_code = all_hospitals[sel_hospital]

    # ── Add Hospital expander ──────────────────────────────────────
    with st.expander("➕  Add a hospital", expanded=False):
        st.markdown(
            '<div style="font-size:.75rem;color:#94a3b8;margin-bottom:.5rem;">'
            'Register a new hospital and assign it a code.</div>',
            unsafe_allow_html=True,
        )
        new_h_name = st.text_input(
            "Hospital name",
            placeholder="e.g. Rwanda Military Hospital",
            key="new_h_name",
        )
        # Auto-suggest next code, user can override
        next_num   = len(all_hospitals) + 1
        suggested  = f"H{str(next_num).zfill(2)}"
        new_h_code = st.text_input(
            "Hospital code",
            value=suggested,
            max_chars=6,
            key="new_h_code",
            help="Short uppercase code, e.g. H05. Must be unique.",
        )
        add_col, _ = st.columns([1, 1])
        with add_col:
            if st.button("Add hospital", use_container_width=True):
                name_clean = new_h_name.strip()
                code_clean = new_h_code.strip().upper()
                existing_codes = set(all_hospitals.values())

                if not name_clean:
                    st.error("Enter a hospital name.")
                elif not code_clean:
                    st.error("Enter a hospital code.")
                elif name_clean in all_hospitals:
                    st.warning("This hospital already exists.")
                elif code_clean in existing_codes:
                    st.error(f"Code '{code_clean}' is already used.")
                else:
                    st.session_state["custom_hospitals"][name_clean] = code_clean
                    st.success(f"Added: {name_clean} → {code_clean}")
                    st.rerun()

        # Show custom hospitals with remove option
        if st.session_state["custom_hospitals"]:
            st.markdown(
                '<div style="font-size:.72rem;color:#475569;margin-top:.6rem;'
                'margin-bottom:.3rem;">Custom hospitals:</div>',
                unsafe_allow_html=True,
            )
            for hname, hcode in list(st.session_state["custom_hospitals"].items()):
                c1, c2 = st.columns([3, 1])
                c1.markdown(
                    f'<span style="font-family:\'DM Mono\',monospace;font-size:.73rem;'
                    f'color:#e2e8f0;">{hcode}</span>'
                    f'<span style="font-size:.72rem;color:#64748b;"> {hname}</span>',
                    unsafe_allow_html=True,
                )
                if c2.button("✕", key=f"rm_{hcode}"):
                    del st.session_state["custom_hospitals"][hname]
                    st.rerun()

    st.markdown('<div class="sb-sec">🎓 Program</div>', unsafe_allow_html=True)
    sel_program = st.selectbox(
        "Program", list(PROGRAMS.keys()), label_visibility="collapsed")
    p_code = PROGRAMS[sel_program]

    st.markdown('<div class="sb-sec">🩻 Image Type</div>', unsafe_allow_html=True)
    img_type = st.radio(
        "Type",
        ["🫁  Chest X-ray", "🔬  Other medical images"],
        label_visibility="collapsed",
    )
    # Map image type to short code used in filename
    img_code = "CXR" if "Chest" in img_type else "IMG"

    st.markdown('<div class="sb-sec">📁 Upload Images</div>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Upload",
        type=["jpg", "jpeg", "png", "dcm"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        help="JPG · PNG · DICOM (.dcm)",
    )

    if uploaded_files:
        n   = len(uploaded_files)
        dcm = sum(1 for f in uploaded_files
                  if Path(f.name).suffix.lower() in (".dcm", ".dicom"))
        st.markdown(f"""
        <div style="margin-top:.8rem;background:#1e293b;border-radius:8px;
                    padding:.8rem 1rem;font-size:.78rem;color:#94a3b8;">
          Files ready: <b style="color:#e2e8f0;font-family:'DM Mono',monospace;">{n}</b>
          &ensp;·&ensp;
          DICOM: <b style="color:#a78bfa;font-family:'DM Mono',monospace;">{dcm}</b>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="margin-top:2rem;padding-top:1rem;border-top:1px solid #1e293b;
                font-size:.7rem;color:#334155;line-height:1.8;">
      <b style="color:#475569;">Privacy model</b><br>
      All processing runs locally.<br>
      Image buffers zeroed after ZIP.<br>
      Original files never touch disk.<br><br>
      <b style="color:#475569;">Naming format</b><br>
      <span style="color:#0d9488;font-family:'DM Mono',monospace;font-size:.68rem;">
        HXX_ACE-DS_DM_CXR_NNNNN.ext</span><br>
      <span style="color:#334155;font-size:.66rem;">
        Hospital · Program · ImageType · PatientID</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Save location ──────────────────────────────────────────────
    st.markdown('<div class="sb-sec">💾 Download Folder</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:.72rem;color:#64748b;margin-bottom:.4rem;">'
        'Where should the ZIP be saved on this computer?</div>',
        unsafe_allow_html=True,
    )
    save_path_input = st.text_input(
        "Save folder",
        value=st.session_state["save_path"] or str(Path.home() / "Downloads"),
        placeholder="e.g. C:\\Users\\you\\Desktop",
        label_visibility="collapsed",
        key="save_path_widget",
    )
    st.session_state["save_path"] = save_path_input.strip()

    # Validate path and show status
    _sp = Path(st.session_state["save_path"]).expanduser()
    if _sp.exists():
        st.markdown(
            f'<div style="font-size:.7rem;color:#4ade80;font-family:\'DM Mono\',monospace;">'
            f'✓ {_sp}</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div style="font-size:.7rem;color:#f59e0b;font-family:\'DM Mono\',monospace;">'
            f'⚠ Folder does not exist yet — will be created</div>',
            unsafe_allow_html=True)

    # ── Original dataset folder (for deletion) ─────────────────────
    st.markdown('<div class="sb-sec">🗑 Original Dataset Folder</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:.72rem;color:#64748b;margin-bottom:.4rem;">'
        'Paste the folder path you uploaded from. Used for the<br>'
        '"Delete Dataset" button after anonymization.</div>',
        unsafe_allow_html=True,
    )
    dataset_folder_input = st.text_input(
        "Dataset folder",
        value=st.session_state.get("dataset_folder", ""),
        placeholder="e.g. D:\\Hospital\\Radiology\\2024",
        label_visibility="collapsed",
        key="dataset_folder_widget",
    )
    if "dataset_folder" not in st.session_state:
        st.session_state["dataset_folder"] = ""
    st.session_state["dataset_folder"] = dataset_folder_input.strip()

    _df = Path(st.session_state["dataset_folder"]).expanduser() \
          if st.session_state["dataset_folder"] else None
    if _df and _df.exists():
        st.markdown(
            f'<div style="font-size:.7rem;color:#f87171;font-family:\'DM Mono\',monospace;">'
            f'📂 {_df}</div>', unsafe_allow_html=True)
    elif _df:
        st.markdown(
            '<div style="font-size:.7rem;color:#475569;">Path not found on disk</div>',
            unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# MAIN PANEL
# ═══════════════════════════════════════════════════════════════════

# Header
st.markdown("""
<div class="app-header">
  <div class="hdr-icon">🛡</div>
  <div>
    <div class="hdr-title">Medical Image Anonymization</div>
    <div class="hdr-sub">
      Strip patient metadata · Rename with structured IDs ·
      Secure memory purge after export
    </div>
    <div class="hdr-badges">
      <span class="badge b-teal">EXIF STRIPPED</span>
      <span class="badge b-teal">DICOM ANONYMIZED</span>
      <span class="badge b-red">ORIGINALS PURGED</span>
      <span class="badge b-slate">LOCAL ONLY</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# Config pills
example_name = f"{h_code}_{p_code}_{img_code}_00001.jpg"
st.markdown(f"""
<div class="cfg-strip">
  <div class="cfg-pill">
    <span class="cfg-icon">🏥</span>
    <div>
      <div class="cfg-lbl">HOSPITAL CODE</div>
      <div class="cfg-val">{h_code}</div>
    </div>
  </div>
  <div class="cfg-pill">
    <span class="cfg-icon">🎓</span>
    <div>
      <div class="cfg-lbl">PROGRAM CODE</div>
      <div class="cfg-val">{p_code}</div>
    </div>
  </div>
  <div class="cfg-pill">
    <span class="cfg-icon">🩻</span>
    <div>
      <div class="cfg-lbl">IMAGE TYPE CODE</div>
      <div class="cfg-val">{img_code}</div>
    </div>
  </div>
  <div class="cfg-pill">
    <span class="cfg-icon">🏷</span>
    <div>
      <div class="cfg-lbl">EXAMPLE OUTPUT</div>
      <div class="cfg-val">{example_name}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# Security policy banner
st.markdown("""
<div class="alert alert-warn">
  <span style="font-size:1.2rem;">🔐</span>
  <div>
    <b>Secure Purge Policy —</b>
    All uploaded image data and anonymized buffers are <b>zeroed in memory</b>
    immediately after the ZIP is built. Original files are never written to
    disk. Refresh the page after downloading to clear all session data.
  </div>
</div>
""", unsafe_allow_html=True)

# ── Empty state ────────────────────────────────────────────────────
if not uploaded_files:
    st.markdown("""
    <div style="text-align:center;padding:4rem 2rem;background:white;
                border:2px dashed #e2e8f0;border-radius:12px;margin-top:1rem;">
      <div style="font-size:3.5rem;margin-bottom:1rem;">📂</div>
      <div style="font-family:'Syne',sans-serif;font-size:1.1rem;
                  font-weight:700;color:#0f172a;margin-bottom:.4rem;">
        No images uploaded yet
      </div>
      <div style="color:#64748b;font-size:.88rem;">
        Upload JPG · PNG · DICOM files from the sidebar to begin
      </div>
    </div>
    """, unsafe_allow_html=True)

else:
    # ── RUN button (only shown before pipeline runs) ───────────────
    if not st.session_state["run_complete"]:
        col_btn, _ = st.columns([1, 3])
        with col_btn:
            if st.button("🛡  Run Anonymization", type="primary",
                          use_container_width=True):

                st.markdown('<div class="sec-h">⚙ Processing</div>',
                             unsafe_allow_html=True)
                bar    = st.progress(0)
                status = st.empty()
                total  = len(uploaded_files)

                results   = []
                log_lines = [
                    "─" * 62,
                    f"  MedAnon Pro  —  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    f"  Hospital : {h_code}    Program : {p_code}    Type : {img_code}",
                    f"  Files submitted : {total}",
                    "─" * 62,
                ]
                pid = 1  # patient ID counter (ok files only)

                for i, uf in enumerate(uploaded_files):
                    bar.progress(int(i / total * 100))
                    status.markdown(
                        f'<span style="font-family:\'DM Mono\',monospace;'
                        f'font-size:.79rem;color:#64748b;">'
                        f'[{i+1}/{total}] {uf.name}</span>',
                        unsafe_allow_html=True,
                    )
                    name = uf.name
                    ext  = Path(name).suffix.lower()

                    if ext not in SUPPORTED_EXT:
                        log_lines.append(
                            f"  ⚠  SKIP  {name:<48} unsupported: {ext}")
                        results.append(dict(
                            original=name, new_name="—", clean_bytes=None,
                            ext=ext, status="skip",
                            msg=f"Unsupported: {ext}"))
                        continue

                    try:
                        raw = uf.read()
                        clean = (anonymize_dicom_file(raw)
                                 if ext in (".dcm", ".dicom")
                                 else strip_image_metadata(raw, ext))
                        new_name = make_filename(h_code, p_code, img_code, pid, ext)
                        log_lines.append(
                            f"  ✓  OK    {name:<48} → {new_name}")
                        results.append(dict(
                            original=name, new_name=new_name,
                            clean_bytes=clean, ext=ext,
                            status="ok", msg="Anonymized"))
                        pid += 1

                    except Exception as exc:
                        log_lines.append(
                            f"  ✗  ERR   {name:<48} {exc}")
                        results.append(dict(
                            original=name, new_name="—", clean_bytes=None,
                            ext=ext, status="error", msg=str(exc)))

                bar.progress(100)
                status.empty()

                ok   = sum(1 for r in results if r["status"] == "ok")
                err  = sum(1 for r in results if r["status"] == "error")
                skip = sum(1 for r in results if r["status"] == "skip")
                log_lines += [
                    "─" * 62,
                    f"  Result  ✓ OK: {ok}   ✗ Err: {err}   ⚠ Skip: {skip}",
                ]

                # Build ZIP while buffers still exist
                zip_bytes = build_zip(results)
                ts        = datetime.now().strftime("%Y%m%d_%H%M%S")
                zip_fname = f"anonymized_{h_code}_{ts}.zip"

                # ── SECURE PURGE ─────────────────────────────────
                results = purge_buffers(results)
                log_lines.append(
                    "  🗑  Secure purge complete — all buffers zeroed in memory")
                log_lines.append("─" * 62)
                logger.info("Secure purge complete. %d files processed.", len(results))

                st.session_state.update(dict(
                    results=results, zip_bytes=zip_bytes,
                    zip_filename=zip_fname, log_lines=log_lines,
                    purged=True, run_complete=True,
                ))
                st.rerun()

    # ── RESULTS ───────────────────────────────────────────────────
    if st.session_state["run_complete"] and st.session_state["results"]:
        results   = st.session_state["results"]
        ok_count  = sum(1 for r in results if r["status"] == "ok")
        err_count = sum(1 for r in results if r["status"] == "error")
        sk_count  = sum(1 for r in results if r["status"] == "skip")

        # ── Stats ──
        st.markdown('<div class="sec-h">📊 Summary</div>',
                     unsafe_allow_html=True)
        st.markdown(f"""
        <div class="stat-row">
          <div class="stat-card">
            <div class="stat-n c-slate">{len(results)}</div>
            <div class="stat-lbl">Total files</div>
          </div>
          <div class="stat-card">
            <div class="stat-n c-teal">{ok_count}</div>
            <div class="stat-lbl">Anonymized</div>
          </div>
          <div class="stat-card">
            <div class="stat-n c-amber">{sk_count}</div>
            <div class="stat-lbl">Skipped</div>
          </div>
          <div class="stat-card">
            <div class="stat-n c-red">{err_count}</div>
            <div class="stat-lbl">Errors</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Purge confirmation
        st.markdown("""
        <div class="alert alert-ok">
          <span style="font-size:1.1rem;">✅</span>
          <div>
            <b>Secure purge complete.</b>
            All original image buffers have been zeroed in memory.
            Only the anonymized ZIP archive remains, ready for download.
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── File table ──
        st.markdown('<div class="sec-h">📄 Anonymized File List</div>',
                     unsafe_allow_html=True)
        st.markdown("""
        <div class="ftable">
          <div class="ftable-head">
            <span>Original filename</span>
            <span>Anonymized filename</span>
            <span>Status</span>
          </div>
        """, unsafe_allow_html=True)

        for r in results:
            icon = "🩻" if r["ext"] in (".dcm", ".dicom") else "🖼️"
            bmap = {"ok": ("fbok","✓ OK"),
                    "error": ("fberr","✗ Err"),
                    "skip": ("fbskip","⚠ Skip")}
            bc, bt = bmap[r["status"]]
            st.markdown(f"""
            <div class="frow">
              <span class="f-orig">{icon} {r["original"]}</span>
              <span class="f-new">{r["new_name"]}</span>
              <span class="fbadge {bc}">{bt}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # ── Export & Delete ──
        if ok_count > 0 and st.session_state["zip_bytes"]:
            st.markdown('<div class="sec-h">⬇ Export & 🗑 Data Deletion</div>',
                         unsafe_allow_html=True)
            zip_b  = st.session_state["zip_bytes"]
            zip_fn = st.session_state["zip_filename"]
            sz_kb  = len(zip_b) / 1024
            save_dir = st.session_state.get("save_path", "").strip()

            # ── Row 1: browser download + save to disk ──
            col_dl, col_save = st.columns(2)

            with col_dl:
                st.markdown(
                    '<div style="font-size:.72rem;color:#64748b;margin-bottom:.3rem;">'
                    '🌐 Browser download</div>', unsafe_allow_html=True)
                st.download_button(
                    label=f"⬇  Save ZIP via browser  ({ok_count} files)",
                    data=zip_b,
                    file_name=zip_fn,
                    mime="application/zip",
                    use_container_width=True,
                    type="primary",
                )
                st.markdown(
                    '<div style="font-size:.7rem;color:#94a3b8;margin-top:.3rem;">'
                    'Downloads to your browser\'s default folder</div>',
                    unsafe_allow_html=True)

            with col_save:
                st.markdown(
                    '<div style="font-size:.72rem;color:#64748b;margin-bottom:.3rem;">'
                    '📁 Save directly to folder</div>', unsafe_allow_html=True)

                if not save_dir:
                    st.markdown(
                        '<div class="alert alert-warn" style="margin:0;padding:.7rem 1rem;">'
                        '<span>⚠️</span>'
                        '<div style="font-size:.8rem;">Set a Download Folder in the sidebar first.</div>'
                        '</div>', unsafe_allow_html=True)
                else:
                    if st.button("💾  Save ZIP to folder", use_container_width=True):
                        try:
                            saved_path = save_zip_to_folder(zip_b, save_dir, zip_fn)
                            st.session_state["saved_path"] = saved_path
                            st.success(f"✅ Saved to: {saved_path}")
                            logger.info("ZIP saved to disk: %s", saved_path)
                        except Exception as e:
                            st.error(f"Save failed: {e}")

                    # Show last saved path if available
                    if st.session_state.get("saved_path"):
                        sp = st.session_state["saved_path"]
                        st.markdown(
                            f'<div style="font-size:.7rem;color:#4ade80;'
                            f'font-family:\'DM Mono\',monospace;margin-top:.3rem;'
                            f'word-break:break-all;">✓ {sp}</div>',
                            unsafe_allow_html=True)

            # ── ZIP info strip ──
            st.markdown(f"""
            <div class="dl-box" style="margin-top:.75rem;">
              <div class="dl-name">📦 {zip_fn}</div>
              <div class="dl-meta">
                {sz_kb:.1f} KB &ensp;·&ensp;
                {ok_count} anonymized image(s) &ensp;·&ensp;
                In-memory buffers already zeroed
              </div>
            </div>
            """, unsafe_allow_html=True)

            # ── Row 2: Delete original dataset ──────────────────────
            st.markdown('<div class="sec-h">🗑 Delete Original Dataset</div>',
                         unsafe_allow_html=True)

            dataset_folder = st.session_state.get("dataset_folder", "").strip()

            if st.session_state.get("dataset_deleted"):
                st.markdown("""
                <div class="alert alert-ok">
                  <span style="font-size:1.2rem;">🗑</span>
                  <div>
                    <b>Original dataset permanently deleted.</b>
                    The source folder has been removed from this machine.
                    This confirms to the department that no copy of the
                    original images remains here.
                  </div>
                </div>
                """, unsafe_allow_html=True)

            elif not dataset_folder:
                st.markdown("""
                <div class="alert alert-info">
                  <span>ℹ️</span>
                  <div style="font-size:.83rem;">
                    To enable dataset deletion, paste the <b>original dataset folder path</b>
                    into the "Original Dataset Folder" field in the sidebar.
                  </div>
                </div>
                """, unsafe_allow_html=True)

            else:
                _df_path = Path(dataset_folder).expanduser()
                folder_exists = _df_path.exists()

                st.markdown(f"""
                <div class="alert alert-danger">
                  <span style="font-size:1.2rem;">⚠️</span>
                  <div>
                    <b>Irreversible action —</b>
                    This will <b>permanently delete</b> the folder and all its contents
                    from your hard drive. There is no undo.<br>
                    <span style="font-family:'DM Mono',monospace;font-size:.8rem;">
                      📂 {_df_path}
                    </span><br>
                    {"<b style='color:#e11d48;'>⚠ Folder not found on disk</b>"
                     if not folder_exists else
                     "<span style='color:#9f1239;'>Folder confirmed present — ready to delete</span>"}
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # Two-step confirmation: checkbox must be ticked first
                confirmed = st.checkbox(
                    "✅  I confirm anonymized ZIP is saved and I want to delete the original dataset",
                    key="delete_confirm",
                )

                del_col, _ = st.columns([1, 3])
                with del_col:
                    del_btn = st.button(
                        "🗑  Delete Original Dataset",
                        disabled=(not confirmed or not folder_exists),
                        use_container_width=True,
                    )

                if del_btn and confirmed and folder_exists:
                    ok_del, msg_del = delete_dataset_folder(dataset_folder)
                    if ok_del:
                        ts_del = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        st.session_state["dataset_deleted"] = True
                        st.session_state["log_lines"].append(
                            f"  🗑  DATASET DELETED  {dataset_folder}  [{ts_del}]")
                        logger.warning("Dataset folder deleted: %s", dataset_folder)
                        st.rerun()
                    else:
                        st.error(f"Deletion failed: {msg_del}")

        # ── Anonymization log ──
        with st.expander("🗒  Anonymization Log", expanded=False):
            log_txt = "\n".join(st.session_state["log_lines"])
            st.markdown(f'<div class="logbox"><pre>{log_txt}</pre></div>',
                         unsafe_allow_html=True)
            st.download_button(
                "⬇  Download log (.txt)",
                data=log_txt.encode(),
                file_name=(f"anon_log_"
                            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"),
                mime="text/plain",
            )

        # ── Reset session ──
        st.markdown("---")
        col_r, _ = st.columns([1, 4])
        with col_r:
            if st.button("🔄  New session", use_container_width=True):
                for k in ["results","zip_bytes","zip_filename","log_lines",
                           "purged","run_complete","saved_path",
                           "dataset_deleted","delete_confirm"]:
                    if k in st.session_state:
                        del st.session_state[k]
                # Re-init defaults (keeps custom_hospitals, save_path, dataset_folder)
                for _k, _v in _DEFAULTS.items():
                    if _k not in st.session_state:
                        st.session_state[_k] = _v
                st.rerun()


# ═══════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("""
<div style="display:flex;justify-content:space-between;align-items:center;
            flex-wrap:wrap;gap:.5rem;padding:.4rem 0 .9rem;">
  <div style="font-family:'DM Mono',monospace;font-size:.7rem;color:#64748b;">
    © <b style="color:#0f172a;">Vedaste NYANDWI</b>
    &ensp;·&ensp; MedAnon Pro
    &ensp;·&ensp; All processing local — patient data never transmitted
  </div>
  <div style="font-family:'DM Mono',monospace;font-size:.68rem;color:#94a3b8;">
    University of Rwanda · CBE · ACE-DS · Data Mining
  </div>
</div>
""", unsafe_allow_html=True)
