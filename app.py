import streamlit as st
import pandas as pd
import requests
from deltalake import DeltaTable, write_deltalake
from datetime import datetime
import pytz

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
        # แปลง UTC → Bangkok
        df["updated_timestamp"] = (
            pd.to_datetime(df["updated_timestamp"], utc=True)
            .dt.tz_convert("Asia/Bangkok")
            .dt.tz_localize(None)  # ซ่อน timezone label ออก
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
        # โหลดข้อมูลเดิม ลบแถวเดิมออก แล้ว overwrite
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
        # ถ้า table ยังไม่มี → สร้างใหม่
        write_deltalake(
            f"{ONELAKE_BASE}/gold_manual_contract_status",
            new_row,
            mode="append",
            storage_options=opts,
        )

# ───────────────────────────────────────────
# UI
# ───────────────────────────────────────────
st.set_page_config(page_title="Contract Status", page_icon="📋", layout="wide")
st.title("📋 Contract Status Management")
st.caption("กรอก User Status และ Purchaser Status สำหรับแต่ละ Purchasing Doc")

col_form, col_table = st.columns([1, 2], gap="large")

# ── LEFT: Form ──────────────────────────────
with col_form:
    st.subheader("➕ เพิ่ม / แก้ไข Status")

    df_docs = load_all_docs()

    doc_no = st.selectbox(
        "Purchasing Doc No",
        df_docs["purchasing_doc_no"].tolist(),
        placeholder="พิมพ์เพื่อค้นหา Doc No...",
    )

    user_status = st.radio(
        "User Status",
        ["confirmed", ""],
        format_func=lambda x: "✅ confirmed" if x == "confirmed" else "⬜ (ว่าง)",
        horizontal=True,
    )

    purchaser_status = st.radio(
        "Purchaser Status",
        ["confirmed", ""],
        format_func=lambda x: "✅ confirmed" if x == "confirmed" else "⬜ (ว่าง)",
        horizontal=True,
    )

    if st.button("💾 Save", type="primary", use_container_width=True):
        with st.spinner("กำลังบันทึก..."):
            try:
                save_status(doc_no, user_status, purchaser_status)
                load_saved.clear()
                st.toast(f"✅ Saved: {doc_no}", icon="✅")
                st.rerun()
            except Exception as e:
                st.error(f"❌ เกิดข้อผิดพลาด: {e}")

# ── RIGHT: Table ─────────────────────────────
with col_table:
    st.subheader("📊 รายการที่บันทึกแล้ว")

    df_saved = load_saved()

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
        st.caption(f"ทั้งหมด {len(df_saved)} รายการ")

    if st.button("🔄 Refresh", use_container_width=True):
        load_all_docs.clear()
        load_saved.clear()
        st.rerun()
