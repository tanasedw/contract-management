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
# STYLE — Claude Dark / Modern
# ───────────────────────────────────────────
def apply_style():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --bg:         #0e0e10;
        --surface:    #17171a;
        --surface2:   #1f1f24;
        --border:     rgba(255,255,255,0.07);
        --border-hi:  rgba(209,149,100,0.45);
        --accent:     #d19564;
        --accent-dim: rgba(209,149,100,0.12);
        --accent-glow:rgba(209,149,100,0.08);
        --text:       #e8e2d9;
        --text-dim:   #7a7570;
        --text-mid:   #b0a89e;
        --red:        #e06060;
        --green:      #6ab890;
        --radius:     10px;
    }

    html, body, [class*="css"] {
        font-family: 'Syne', sans-serif !important;
        background-color: var(--bg) !important;
        color: var(--text) !important;
    }

    /* ── Hide Streamlit chrome ── */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container {
        padding: 2.5rem 2rem 4rem !important;
        max-width: 1300px !important;
    }

    /* ── Page title ── */
    h1 {
        font-family: 'Syne', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1.55rem !important;
        color: var(--text) !important;
        letter-spacing: -0.03em !important;
        margin-bottom: 0.1rem !important;
        background: linear-gradient(90deg, #e8e2d9 0%, #d19564 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    /* ── Caption ── */
    .element-container p small,
    [data-testid="stCaptionContainer"] p {
        color: var(--text-dim) !important;
        font-size: 0.78rem !important;
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* ── Section subheader ── */
    h3 {
        font-family: 'Syne', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.7rem !important;
        color: var(--text-dim) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.18em !important;
        margin-bottom: 1.4rem !important;
    }

    /* ── Thin divider line after title ── */
    h1 + div {
        border-top: 1px solid var(--border);
        margin-top: 0.4rem;
    }

    /* ── Labels ── */
    label, .stRadio label {
        font-family: 'Syne', sans-serif !important;
        color: var(--text-mid) !important;
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.12em !important;
    }

    /* ── Selectbox ── */
    .stSelectbox > div > div {
        background-color: var(--surface2) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        color: var(--text) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.87rem !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }
    .stSelectbox > div > div:hover {
        border-color: var(--border-hi) !important;
    }
    .stSelectbox > div > div:focus-within {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px var(--accent-dim) !important;
    }
    [data-baseweb="popover"],
    [data-baseweb="menu"] {
        background-color: var(--surface2) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
    }
    [data-baseweb="menu"] li {
        color: var(--text) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.84rem !important;
    }
    [data-baseweb="menu"] li:hover {
        background-color: var(--accent-dim) !important;
    }
    .stSelectbox [data-baseweb="select"] input {
        color: var(--text) !important;
    }

    /* ── Radio buttons as pills ── */
    .stRadio > div {
        gap: 0.5rem !important;
        flex-direction: row !important;
        flex-wrap: wrap !important;
    }
    .stRadio > div > label {
        background-color: var(--surface2) !important;
        border: 1px solid var(--border) !important;
        border-radius: 100px !important;
        padding: 0.35rem 1rem !important;
        color: var(--text-dim) !important;
        font-size: 0.8rem !important;
        text-transform: none !important;
        letter-spacing: 0.02em !important;
        cursor: pointer !important;
        transition: all 0.15s !important;
        font-weight: 500 !important;
    }
    .stRadio > div > label:hover {
        border-color: var(--border-hi) !important;
        color: var(--text) !important;
    }
    .stRadio > div > label:has(input:checked) {
        background-color: var(--accent-dim) !important;
        border-color: var(--accent) !important;
        color: var(--accent) !important;
        font-weight: 600 !important;
        box-shadow: 0 0 12px var(--accent-glow) !important;
    }
    /* hide the actual radio dot */
    .stRadio > div > label > div:first-child { display: none !important; }

    /* ── Text input ── */
    .stTextInput > div > div > input {
        background-color: var(--surface2) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        color: var(--text) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.87rem !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px var(--accent-dim) !important;
    }
    .stTextInput > div > div > input::placeholder {
        color: var(--text-dim) !important;
    }

    /* ── Textarea ── */
    .stTextArea > div > div > textarea {
        background-color: var(--surface2) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        color: var(--text) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.84rem !important;
        resize: vertical !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
        line-height: 1.6 !important;
    }
    .stTextArea > div > div > textarea:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px var(--accent-dim) !important;
    }
    .stTextArea > div > div > textarea::placeholder {
        color: var(--text-dim) !important;
    }

    /* ── Primary button — Save ── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #d19564 0%, #c07c4a 100%) !important;
        color: #0e0e10 !important;
        border: none !important;
        border-radius: var(--radius) !important;
        font-family: 'Syne', sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.05em !important;
        padding: 0.55rem 1.2rem !important;
        transition: all 0.2s !important;
        box-shadow: 0 4px 20px rgba(209,149,100,0.3) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #e0a875 0%, #d19564 100%) !important;
        box-shadow: 0 6px 28px rgba(209,149,100,0.45) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button[kind="primary"]:active {
        transform: translateY(0) !important;
        box-shadow: 0 2px 10px rgba(209,149,100,0.25) !important;
    }

    /* ── Secondary button — Refresh ── */
    .stButton > button[kind="secondary"] {
        background-color: var(--surface2) !important;
        color: #ffffff !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        font-family: 'Syne', sans-serif !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.03em !important;
        transition: all 0.2s !important;
    }
    .stButton > button[kind="secondary"]:hover {
        border-color: var(--border-hi) !important;
        color: var(--text) !important;
        background-color: var(--accent-dim) !important;
    }

    /* ── Dataframe / table ── */
    .stDataFrame {
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        overflow: hidden !important;
        background-color: var(--surface) !important;
    }
    [data-testid="stDataFrameResizable"] {
        background-color: var(--surface) !important;
    }
    [data-testid="stDataFrame"] th {
        background-color: var(--surface2) !important;
        color: var(--text-dim) !important;
        font-family: 'Syne', sans-serif !important;
        font-size: 0.7rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
    }
    [data-testid="stDataFrame"] td {
        color: var(--text) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.82rem !important;
    }

    /* ── Alert / warning ── */
    .stAlert {
        background-color: var(--surface2) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        color: var(--text-mid) !important;
    }

    /* ── Spinner ── */
    .stSpinner > div {
        border-top-color: var(--accent) !important;
    }

    /* ── Toast ── */
    [data-testid="stToast"] {
        background-color: var(--surface2) !important;
        border: 1px solid var(--border-hi) !important;
        color: var(--text) !important;
        border-radius: var(--radius) !important;
    }

    /* ── Subtle card wrapper around form column ── */
    [data-testid="column"]:first-child > div > div {
        background-color: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 14px !important;
        padding: 1.5rem !important;
    }

    /* ── Vertical divider column ── */
    [data-testid="column"]:nth-child(2) {
        border-left: 1px solid var(--border) !important;
        margin: 0 0.5rem !important;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 4px; height: 4px; }
    ::-webkit-scrollbar-track { background: var(--bg); }
    ::-webkit-scrollbar-thumb {
        background: var(--surface2);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-dim);
    }

    /* ── Glow dot decoration on title ── */
    .title-dot {
        display: inline-block;
        width: 8px; height: 8px;
        background: var(--accent);
        border-radius: 50%;
        box-shadow: 0 0 12px var(--accent);
        margin-right: 0.6rem;
        vertical-align: middle;
    }

    /* ── Count badge ── */
    .count-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: var(--accent-dim);
        border: 1px solid var(--border-hi);
        border-radius: 100px;
        padding: 0.2rem 0.75rem;
        color: var(--accent);
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        font-family: 'JetBrains Mono', monospace;
    }

    /* ── Section header row ── */
    .section-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.2rem;
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
    """Load purchasing_doc_no + contract_name from gold_contract_management."""
    opts = storage_options()
    df = (
        DeltaTable(f"{ONELAKE_BASE}/gold_contract_management", storage_options=opts)
        .to_pandas()[["purchasing_doc_no", "contract_name"]]
        .drop_duplicates(subset=["purchasing_doc_no"])
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
        df["updated_timestamp"] = pd.to_datetime(
            df["updated_timestamp"].astype(str).str[:19]
        )
        for col in ["comment", "new_contract_doc_no"]:
            if col not in df.columns:
                df[col] = ""
        df = df.drop(columns=["user_status"], errors="ignore")
        return df
    except Exception:
        return pd.DataFrame(columns=[
            "purchasing_doc_no", "purchaser_status",
            "comment", "new_contract_doc_no", "updated_timestamp",
        ])

def save_status(merged_df: pd.DataFrame):
    """Write merged dataframe to Delta table — one round-trip only."""
    opts = storage_options()
    df = merged_df.copy()
    df["updated_timestamp"] = pd.to_datetime(
        df["updated_timestamp"]
    ).dt.tz_localize(None).astype("datetime64[us]")
    write_deltalake(
        f"{ONELAKE_BASE}/gold_manual_contract_status",
        df,
        mode="overwrite",
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

# ── Header ──
st.markdown('<span class="title-dot"></span>', unsafe_allow_html=True)
st.title("Contract Status")
st.caption("กรอก Purchaser Status สำหรับแต่ละ Purchasing Doc")

st.markdown("<br>", unsafe_allow_html=True)

col_form, col_gap, col_table = st.columns([1, 0.05, 2.2])

with col_form:
    st.subheader("เพิ่ม / แก้ไข")

    df_docs = load_all_docs()

    doc_no = st.selectbox(
        "Purchasing Doc No",
        df_docs["purchasing_doc_no"].tolist(),
        placeholder="ค้นหา Doc No...",
    )

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    purchaser_status = st.selectbox(
        "Purchaser Status",
        ["", "ต่อสัญญา", "ไม่ต่อสัญญา", "ยกเลิกสัญญาก่อนกำหนด"],
        format_func=lambda x: "○  ว่าง" if x == "" else x,
    )

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    # ── pre-fill comment & new doc ──
    existing_comment = ""
    existing_new_doc = ""
    if doc_no and not st.session_state.saved_data.empty:
        match = st.session_state.saved_data[
            st.session_state.saved_data["purchasing_doc_no"] == doc_no
        ]
        if not match.empty:
            existing_comment = str(match.iloc[0].get("comment", "") or "")
            existing_new_doc = str(match.iloc[0].get("new_contract_doc_no", "") or "")

    comment = st.text_area(
        "Comment",
        value=existing_comment,
        placeholder="หมายเหตุ / รายละเอียดเพิ่มเติม...",
        height=110,
    )

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    # ── new contract doc no ──
    new_contract_doc_no_raw = st.text_input(
        "เลขสัญญาใหม่ (Purchasing Doc No ใหม่)",
        value=existing_new_doc,
        placeholder="ตัวเลขเท่านั้น เช่น 4500012345",
        max_chars=20,
    )

    new_contract_doc_no = "".join(filter(str.isdigit, new_contract_doc_no_raw))
    if new_contract_doc_no_raw and new_contract_doc_no != new_contract_doc_no_raw:
        st.warning("กรุณากรอกตัวเลขเท่านั้น")

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

    if st.button("Save", type="primary", use_container_width=True):
        with st.spinner("กำลังบันทึก..."):
            try:
                new_entry = pd.DataFrame([{
                    "purchasing_doc_no":    doc_no,
                    "purchaser_status":     purchaser_status,
                    "comment":              comment,
                    "new_contract_doc_no":  new_contract_doc_no,
                    "updated_timestamp":    datetime.now(
                        pytz.timezone("Asia/Bangkok")
                    ).replace(tzinfo=None),
                }])
                df = st.session_state.saved_data
                df = df[df["purchasing_doc_no"] != doc_no]
                df = pd.concat([new_entry, df], ignore_index=True)
                save_status(df)
                st.session_state.saved_data = df
                st.toast(f"Saved — {doc_no}", icon="✅")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

with col_table:
    df_saved = st.session_state.saved_data
    count = len(df_saved)

    # ── join contract_name from df_docs ──
    df_display = df_saved.merge(
        df_docs[["purchasing_doc_no", "contract_name"]],
        on="purchasing_doc_no",
        how="left",
    )

    # ── section header with count badge ──
    st.markdown(
        f"""
        <div class="section-header">
            <span style="font-size:0.7rem;font-weight:600;color:#7a7570;
                         text-transform:uppercase;letter-spacing:0.18em;">
                รายการที่บันทึกแล้ว
            </span>
            <span class="count-badge">{count} รายการ</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df_display.empty:
        st.warning("ยังไม่มีข้อมูล")
    else:
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "purchasing_doc_no":   st.column_config.TextColumn("Doc No"),
                "contract_name":       st.column_config.TextColumn("Contract Name", width="medium"),
                "purchaser_status":    st.column_config.TextColumn("Purchaser Status"),
                "comment":             st.column_config.TextColumn("Comment", width="medium"),
                "new_contract_doc_no": st.column_config.TextColumn("เลขสัญญาใหม่"),
                "updated_timestamp":   st.column_config.DatetimeColumn(
                    "Updated At (BKK)", format="DD MMM YYYY hh:mm A"
                ),
            },
            column_order=[
                "purchasing_doc_no", "contract_name", "purchaser_status",
                "comment", "new_contract_doc_no", "updated_timestamp",
            ],
        )

    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

    if st.button("↺  Refresh data", use_container_width=True):
        load_all_docs.clear()
        load_saved.clear()
        st.session_state.saved_data = None
        st.rerun()
