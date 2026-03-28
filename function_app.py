import azure.functions as func
import pandas as pd
import requests
import pytz
from deltalake import write_deltalake, DeltaTable
from datetime import datetime
import hashlib, hmac, os, traceback

app = func.FunctionApp()

TENANT_ID     = os.environ["tenant_id"]
CLIENT_ID     = os.environ["client_id"]
CLIENT_SECRET = os.environ["client_secret"]
SECRET_KEY    = os.environ["secret_key_email_button"]
WORKSPACE_ID  = "69a84913-d8e5-4ca9-970e-85e3ddc68f14"
LAKEHOUSE_ID  = "961d3727-8929-45b1-835d-95568f2ebe59"
ONELAKE_BASE  = (
    f"abfss://{WORKSPACE_ID}@onelake.dfs.fabric.microsoft.com"
    f"/{LAKEHOUSE_ID}/Tables"
)

def get_token():
    res = requests.post(
        f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token",
        data={
            "grant_type":    "client_credentials",
            "client_id":     CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope":         "https://storage.azure.com/.default",
        }
    )
    return res.json()["access_token"]

def storage_options():
    return {
        "bearer_token":        get_token(),
        "use_fabric_endpoint": "true",
    }

def verify_sig(doc_no: str, action: str, sig: str) -> bool:
    expected = hmac.new(
        SECRET_KEY.encode(),
        f"{doc_no}:{action}".encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, sig)

@app.route(route="confirm", auth_level=func.AuthLevel.ANONYMOUS)
def confirm(req: func.HttpRequest) -> func.HttpResponse:
    doc_no = req.params.get("doc_no", "")
    action = req.params.get("action", "")
    sig    = req.params.get("sig", "")

    VALID_ACTIONS = ["ต่อสัญญา", "ไม่ต่อสัญญา"]

    if not doc_no or action not in VALID_ACTIONS:
        return func.HttpResponse("Invalid request", status_code=400)

    if not verify_sig(doc_no, action, sig):
        return func.HttpResponse("Unauthorized", status_code=401)

    try:
        opts = storage_options()
        existing = DeltaTable(
            f"{ONELAKE_BASE}/gold_manual_contract_status",
            storage_options=opts
        ).to_pandas()

        new_entry = pd.DataFrame([{
            "purchasing_doc_no":     doc_no,
            "user_status":           action,
            "purchaser_status":      "",
            "comment":               "",
            "new_purchasing_doc_no": "",
            "update_at":             datetime.now(pytz.timezone("Asia/Bangkok")),
        }])

        existing = existing.rename(columns={
            "updated_timestamp":  "update_at",
            "new_contract_doc_no": "new_purchasing_doc_no",
        })
        for col in ["purchaser_status", "update_at", "new_purchasing_doc_no"]:
            if col not in existing.columns:
                existing[col] = None
        existing["update_at"] = pd.to_datetime(existing["update_at"], errors="coerce")
        merged = pd.concat(
            [existing[existing["purchasing_doc_no"] != doc_no], new_entry],
            ignore_index=True
        )

        write_deltalake(
            f"{ONELAKE_BASE}/gold_manual_contract_status",
            merged,
            mode="overwrite",
            schema_mode="overwrite",
            storage_options=opts,
        )

        html = f"""
        <html><body style="font-family:Segoe UI,sans-serif;text-align:center;padding:60px;color:#333">
            <div style="font-size:48px">✅</div>
            <h2>บันทึกเรียบร้อย</h2>
            <p>สัญญา <strong>{doc_no}</strong> อัพเดทสถานะเป็น <strong>{action}</strong> แล้วครับ</p>
            <p style="color:#999;font-size:13px">ท่านสามารถปิดหน้านี้ได้เลย</p>
        </body></html>
        """
        return func.HttpResponse(html, mimetype="text/html", status_code=200)

    except Exception as e:
        return func.HttpResponse(
            f"<pre>Error: {e}\n\n{traceback.format_exc()}</pre>",
            mimetype="text/html",
            status_code=500
        )