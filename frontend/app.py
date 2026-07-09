import streamlit as st
import requests
import json

st.set_page_config(
    page_title="Excel Consolidator",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
    /* Main background — teal */
    .stApp {
        background-color: #008080 !important;
    }

    section[data-testid="stMain"] > div {
        background-color: #008080 !important;
    }

    /* Top header bar — teal */
    header[data-testid="stHeader"] {
        background-color: #008080 !important;
        border-bottom: none !important;
    }

    /* Deploy button */
    .stDeployButton {
        color: white !important;
    }

    /* Title */
    .header-title {
        font-size: 32px;
        font-weight: 700;
        color: white;
        letter-spacing: -0.5px;
    }
    .header-sub {
        color: #e0f5f5;
        font-size: 15px;
        margin-top: -8px;
    }

    /* Step headers */
    h3 {
        color: white !important;
        font-weight: 600 !important;
    }

    /* Success box */
    .success-box {
        background: #e6fafa;
        border-left: 4px solid #004d4d;
        padding: 10px 16px;
        border-radius: 6px;
        margin: 6px 0;
        color: #004d4d;
        font-size: 13px;
    }

    /* Mapping box */
    .mapping-box {
        background: white;
        border-left: 4px solid #004d4d;
        padding: 10px 16px;
        border-radius: 6px;
        margin: 6px 0;
        font-size: 13px;
        color: #2d3748;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    /* Primary buttons */
    .stButton > button[kind="primary"] {
        background-color: white !important;
        color: #008080 !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #e0f5f5 !important;
    }

    /* Secondary buttons */
    .stButton > button:not([kind="primary"]) {
        border: 1.5px solid white !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        background: transparent !important;
    }

    /* Divider */
    hr {
        border-color: #006666 !important;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        color: white !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #e0f5f5 !important;
    }

    /* File uploader outer border */
    [data-testid="stFileUploader"] {
        border-radius: 10px !important;
    }

    /* File uploader dropzone — white */
    [data-testid="stFileUploaderDropzone"] {
        background-color: white !important;
        border: 2px dashed #008080 !important;
        border-radius: 10px !important;
    }

    /* Upload button inside dropzone */
    [data-testid="stFileUploaderDropzone"] button {
        background-color: #008080 !important;
        color: white !important;
    }

    /* Upload instruction text */
    [data-testid="stFileUploaderDropzoneInstructions"] p {
        color: #008080 !important;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] span {
        color: #666 !important;
    }

    /* Alerts */
    [data-testid="stAlert"] {
        border-radius: 8px !important;
    }

    /* Download button */
    .stDownloadButton > button {
        background-color: white !important;
        color: #008080 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

BACKEND_URL = "http://127.0.0.1:8000"

if "uploaded" not in st.session_state:
    st.session_state.uploaded = False
if "mappings" not in st.session_state:
    st.session_state.mappings = None
if "consolidated" not in st.session_state:
    st.session_state.consolidated = False

st.markdown('<p class="header-title">📊 Excel Consolidator</p>', unsafe_allow_html=True)
st.markdown('<p class="header-sub">Upload multiple Excel or CSV files — AI cleans, maps and consolidates them into one file</p>', unsafe_allow_html=True)
st.markdown("---")

# Step 1 — Upload
st.markdown("### Step 1 — Upload your files")
uploaded_files = st.file_uploader(
    "Upload Excel or CSV files",
    type=["xlsx", "xls", "csv"],
    accept_multiple_files=True,
    label_visibility="collapsed"
)

if uploaded_files and not st.session_state.uploaded:
    if st.button("📤 Upload & Analyse", type="primary"):
        with st.spinner("Uploading files..."):
            files = [("files", (f.name, f.getvalue(),
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))
                     for f in uploaded_files]
            response = requests.post(f"{BACKEND_URL}/upload-files", files=files)

            if response.status_code == 200:
                data = response.json()
                st.session_state.uploaded = True
                st.success(f"✅ {len(data['uploaded'])} files uploaded successfully!")
                for f in data["uploaded"]:
                    st.markdown(f'<div class="success-box">📄 <b>{f["filename"]}</b> — {f["rows"]} rows, {len(f["columns"])} columns</div>', unsafe_allow_html=True)
                st.rerun()
            else:
                st.error("Upload failed. Make sure the backend is running.")

# Step 2 — Column Mapping
if st.session_state.uploaded:
    st.markdown("### Step 2 — AI Column Mapping")

    if st.session_state.mappings is None:
        if st.button("🤖 Run AI Column Mapping", type="primary"):
            with st.spinner("Claude is analysing your column names..."):
                response = requests.get(f"{BACKEND_URL}/map-columns")
                if response.status_code == 200:
                    st.session_state.mappings = response.json()
                    st.rerun()
                else:
                    st.error("Mapping failed.")

    if st.session_state.mappings:
        st.success(f"✅ Claude identified {len(st.session_state.mappings['mappings'])} column mappings!")
        for mapping in st.session_state.mappings["mappings"]:
            matches_str = " | ".join([f"{file}: <b>{col}</b>" for file, col in mapping["matches"].items()])
            st.markdown(f'<div class="mapping-box">🔗 <b>{mapping["standard_name"]}</b> — {matches_str}</div>', unsafe_allow_html=True)

# Step 3 — Clean & Consolidate
if st.session_state.mappings:
    st.markdown("### Step 3 — Clean & Consolidate")

    if not st.session_state.consolidated:
        if st.button("⚙️ Clean & Consolidate Data", type="primary"):
            with st.spinner("Cleaning and consolidating your data..."):
                response = requests.post(f"{BACKEND_URL}/clean-and-consolidate")
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.consolidated = True
                    st.success(f"✅ {data['message']}")
                    col1, col2 = st.columns(2)
                    col1.metric("Total Rows", data["total_rows"])
                    col2.metric("Unique Products", data["unique_products"])
                    st.rerun()
                else:
                    st.error("Consolidation failed.")

# Step 4 — Download
if st.session_state.consolidated:
    st.markdown("### Step 4 — Download your files")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📥 Download Excel", type="primary", use_container_width=True):
            response = requests.get(f"{BACKEND_URL}/download-excel")
            if response.status_code == 200:
                st.download_button(
                    "💾 Save Excel File",
                    data=response.content,
                    file_name="consolidated_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

    with col2:
        if st.button("📄 Download PDF Report", type="primary", use_container_width=True):
            response = requests.get(f"{BACKEND_URL}/download-report")
            if response.status_code == 200:
                st.download_button(
                    "💾 Save PDF Report",
                    data=response.content,
                    file_name="audit_report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

    with col3:
        if st.button("🔄 Start Over", use_container_width=True):
            requests.get(f"{BACKEND_URL}/reset")
            st.session_state.uploaded = False
            st.session_state.mappings = None
            st.session_state.consolidated = False
            st.rerun()