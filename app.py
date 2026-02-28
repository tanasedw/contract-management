import streamlit as st
import pandas as pd
import requests
import pytz
from deltalake import DeltaTable, write_deltalake
from datetime import datetime

# ───────────────────────────────────────────
# CONFIG
# ───────────────────────────────────────────
TENANT_ID     = st.secrets["TENANT_ID"]
CLIENT_ID     = st.secrets["CLIENT_ID"]
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]
WORKSPACE_ID  = "69a84913-d8e5-4ca9-970e-85e3ddc68f14"
LAKEHOUSE_ID  = "961d3727-8929-45b1-835d-95568f2ebe59"

ONELAKE_BASE = (
    f"abfss://{WORKSPACE_ID}@onelake.dfs.fabric.microsoft.com"
    f"/{LAKEHOUSE_ID}/Tables"
)

# ───────────────────────────────────────────
# STYLE
# ───────────────────────────────────────────
def apply_style():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

    /* ── Global ── */
    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }
    .stApp {
        background-color: #0b1628;
        color: #e2e8f0;
    }

    /* ── Hide default header/footer ── */
    #MainMenu, footer, header { visibility: hidden; }

    /* ── Title ── */
    h1 {
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1.6rem !important;
        color: #f0f6ff !important;
        letter-spacing: -0.02em !important;
        padding-bottom: 0.25rem !important;
        border-bottom: 1px solid #1e3a5f !important;
        margin-bottom: 0.25rem !important;
    }

    /* ── Caption ── */
    .stApp p[data-testid="stCaptionContainer"] {
        color: #4a6fa5 !important;
        font-size: 0.78rem !important;
    }

    /* ── Subheader ── */
    h3 {
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        color: #4a6fa5 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
        margin-bottom: 1rem !important;
    }

    /* ── Label ── */
    label, .stRadio label, .stSelectbox label {
        color: #94a3b8 !important;
        font-size: 0.78rem !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
    }

    /* ── Selectbox ── */
    .stSelectbox > div > div {
        background-color: #0f2040 !important;
        border: 1px solid #1e3a5f !important;
        border-radius: 8px !important;
        color: #e2e8f0 !important;
        font-family: 'DM Mono', monospace !important;
        font-size: 0.88rem !important;
    }
    .stSelectbox > div > div:focus-within {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 2px rgba(59,130,246,0.15) !important;
    }

    /* ── Radio ── */
    .stRadio > div {
        gap: 0.5rem !important;
    }
    .stRadio > div > label {
        background-color: #0f2040 !important;
        border: 1px solid #1e3a5f !important;
        border-radius: 8px !important;
        padding: 0.4rem 1rem !important;
        color: #94a3b8 !important;
        font-size: 0.82rem !important;
        text-transform: none !important;
        letter-spacing: 0 !important;
        cursor: pointer !important;
        transition: all 0.15s !important;
    }
    .stRadio > div > label:has(input:checked) {
        background-color: #1e3a5f !important;
        border-color: #3b82f6 !important;
        color: #93c5fd !important;
    }

    /* ── Button Save ── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1d4ed8, #1e40af) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.88rem !important;
        letter-spacing: 0.02em !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.2s !important;
        box-shadow: 0 4px 12px rgba(29,78,216,0.3) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
        box-shadow: 0 6px 16px rgba(29,78,216,0.4) !important;
        transform: translateY(-1px) !important;
    }

    /* ── Button Refresh ── */
    .stButton > button[kind="secondary"] {
        background-color: transparent !important;
        color: #4a6fa5 !important;
        border: 1px solid #1e3a5f !important;
        border-radius: 8px !important;
        font-size: 0.82rem !important;
        transition: all 0.15s !important;
    }
    .stButton > button[kind="secondary"]:hover {
        border-color: #3b82f6 !important;
        color: #93c5fd !important;
    }

    /* ── Dataframe ── */
    .stDataFrame {
        border: 1px solid #1e3a5f !important;
        border-radius: 10px !important;
        overflow: hidden !important;
    }
    .stDataFrame thead tr th {
        background-color: #0f2040 !important;
        color: #4a6fa5 !important;
        font-size: 0.72rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        font-weight: 500 !important;
        border-bottom: 1px solid #1e3a5f !important;
    }
    .stDataFrame tbody tr td {
        background-color: #0b1628 !important;
        color: #cbd5e1 !important;
        font-family: 'DM Mono', monospace !important;
        font-size: 0.82rem !important;
        border-bottom: 1px solid #0f2040 !important;
    }
    .stDataFrame tbody tr:hover td {
        background-color: #0f2040 !important;
    }

    /* ── Spinner ── */
    .stSpinner > div {
        border-top-color: #3b82f6 !important;
    }

    /* ── Warning / Info ── */
    .stAlert {
        background-color: #0f2040 !important;
        border: 1px solid #1e3a5f !important;
        border-radius: 8px !important;
        color: #94a3b8 !important;
    }

    /* ── Divider ── */
    hr {
        border-color: #1e3a5f !important;
    }

    /* ── Caption bottom ── */
    small {
        color: #334e6b !important;
        font-size: 0.72rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ───────────────────────────────────────────
# AUTH
# ───────────────────────────────────────────
@st.cache_data(ttl=3000)
def get_token():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    res = requests.post(url, data={
        "grant_type":    "client_credentials",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope":         "https://storage.azure.com/.default",
    })
    res.raise_for_status()
    return res.json()["access_token"]

def storage_options():
    return {
        "bearer_token":        get_token(),
        "use_fabric_endpoint": "true",
    }

# ───────────────────────────────────────────
# DATA
# ───────────────────────────────────────────
@st.cache_data(ttl=600)
def load_all_docs():
    opts = storage_options()
    df = (
        DeltaTable(f"{ONELAKE_BASE}/gold_contract_management", storage_options=opts)
        .to_pandas()[["purchasing_doc_no"]]
        .drop_duplicates()
        .sort_values("purchasing_doc_no")
    )
    return df

@st.cache_data(ttl=600)
def load_saved():
    opts = storage_options()
    try:
        df = (
            DeltaTable(f"{ONELAKE_BASE}/gold_manual_contract_status", storage_options=opts)
            .to_pandas()
            .sort_values("updated_timestamp", ascending=False)
        )
        df["updated_timestamp"] = (
            pd.to_datetime(df["updated_timestamp"], utc=True)
            .dt.tz_convert("Asia/Bangkok")
            .dt.tz_localize(None)
        )
        return df
    except Exception:
        return pd.DataFrame(columns=["purchasing_doc_no", "user_status", "purchaser_status", "updated_timestamp"])

def save_status(doc_no: str, user_status: str, purchaser_status: str):
    opts = storage_options()
    new_row = pd.DataFrame([{
        "purchasing_doc_no": doc_no,
        "user_status":       user_status,
        "purchaser_status":  purchaser_status,
        "updated_timestamp": datetime.now(pytz.timezone("Asia/Bangkok")),
    }])
    try:
        existing = DeltaTable(
            f"{ONELAKE_BASE}/gold_manual_contract_status",
            storage_options=opts
        ).to_pandas()
        existing = existing[existing["purchasing_doc_no"] != doc_no]
        merged = pd.concat([existing, new_row], ignore_index=True)
        write_deltalake(
            f"{ONELAKE_BASE}/gold_manual_contract_status",
            merged,
            mode="overwrite",
            storage_options=opts,
        )
    except Exception:
        write_deltalake(
            f"{ONELAKE_BASE}/gold_manual_contract_status",
            new_row,
            mode="append",
            storage_options=opts,
        )

# ───────────────────────────────────────────
# SESSION STATE
# ───────────────────────────────────────────
if "saved_data" not in st.session_state:
    st.session_state.saved_data = None
if st.session_state.saved_data is None:
    st.session_state.saved_data = load_saved()

# ───────────────────────────────────────────
# UI
# ───────────────────────────────────────────
st.set_page_config(page_title="Contract Status", page_icon="📋", layout="wide")
apply_style()

st.title("Contract Status Management")
st.caption("กรอก User Status และ Purchaser Status สำหรับแต่ละ Purchasing Doc")

st.markdown("<br>", unsafe_allow_html=True)

col_form, col_gap, col_table = st.columns([1, 0.08, 2])

# ── LEFT: Form ──────────────────────────────
with col_form:
    st.subheader("เพิ่ม / แก้ไข Status")

    df_docs = load_all_docs()

    doc_no = st.selectbox(
        "Purchasing Doc No",
        df_docs["purchasing_doc_no"].tolist(),
        placeholder="ค้นหา Doc No...",
    )

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    user_status = st.radio(
        "User Status",
        ["confirmed", ""],
        format_func=lambda x: "✅  confirmed" if x == "confirmed" else "⬜  (ว่าง)",
        horizontal=True,
    )

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    purchaser_status = st.radio(
        "Purchaser Status",
        ["confirmed", ""],
        format_func=lambda x: "✅  confirmed" if x == "confirmed" else "⬜  (ว่าง)",
        horizontal=True,
    )

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    if st.button("Save", type="primary", use_container_width=True):
        with st.spinner("กำลังบันทึก..."):
            try:
                save_status(doc_no, user_status, purchaser_status)
                new_entry = pd.DataFrame([{
                    "purchasing_doc_no": doc_no,
                    "user_status":       user_status,
                    "purchaser_status":  purchaser_status,
                    "updated_timestamp": datetime.now(pytz.timezone("Asia/Bangkok")).replace(tzinfo=None),
                }])
                df = st.session_state.saved_data
                df = df[df["purchasing_doc_no"] != doc_no]
                df = pd.concat([new_entry, df], ignore_index=True)
                st.session_state.saved_data = df
                st.toast(f"Saved — {doc_no}", icon="✅")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# ── RIGHT: Table ─────────────────────────────
with col_table:
    st.subheader("รายการที่บันทึกแล้ว")

    df_saved = st.session_state.saved_data

    if df_saved.empty:
        st.warning("ยังไม่มีข้อมูล")
    else:
        st.dataframe(
            df_saved,
            use_container_width=True,
            hide_index=True,
            column_config={
                "purchasing_doc_no":  st.column_config.TextColumn("Doc No"),
                "user_status":        st.column_config.TextColumn("User Status"),
                "purchaser_status":   st.column_config.TextColumn("Purchaser Status"),
                "updated_timestamp":  st.column_config.DatetimeColumn("Updated At", format="YYYY-MM-DD HH:mm:ss"),
            },
        )
        st.caption(f"{len(df_saved)} รายการ")

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    if st.button("↺  Refresh", use_container_width=True):
        load_all_docs.clear()
        st.session_state.saved_data = None
        st.rerun()
