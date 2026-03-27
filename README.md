# Contract Management — Email Button

ระบบปุ่มกดในอีเมล alert สำหรับฝ่ายจัดซื้อ เมื่อได้รับอีเมลแจ้งเตือนสัญญา ผู้ใช้สามารถกดปุ่มในอีเมลเพื่อระบุสถานะได้ทันที โดยไม่ต้องเข้าระบบใด ๆ

ข้อมูลจะถูกบันทึกลง Microsoft Fabric Lakehouse (Delta Lake) แบบ Real-time และแสดงผลบน Streamlit Dashboard

## How it works

1. ระบบส่งอีเมล alert พร้อมปุ่ม **ต่อสัญญา** / **ไม่ต่อสัญญา**
2. แต่ละปุ่มคือ URL ที่ฝัง `doc_no`, `action`, และ `sig` (HMAC signature)
3. เมื่อกดปุ่ม Azure Function จะตรวจสอบ signature แล้วบันทึกสถานะลงคอลัมน์ `user_status` ใน Delta Table `gold_manual_contract_status`
4. แสดงหน้ายืนยันให้ผู้ใช้ทราบว่าบันทึกเรียบร้อย
5. `user_status` ถูกใช้เป็นเงื่อนไขป้องกันการส่งเมลซ้ำ (join real-time จาก `gold_manual_contract_status`)
6. ข้อมูลแสดงผลบน Streamlit Dashboard ผ่าน pipeline ที่ join เข้า `gold_contract_management`

## Delta Table Schema — `gold_manual_contract_status`

| Column | Type | Description |
|--------|------|-------------|
| `purchasing_doc_no` | String | เลขที่สัญญา |
| `user_status` | String | สถานะจากปุ่มในอีเมล (ต่อสัญญา / ไม่ต่อสัญญา) |
| `purchaser_status` | String | สถานะจากฝ่ายจัดซื้อ (กรอกบน Streamlit) |
| `comment` | String | หมายเหตุ |
| `new_purchasing_doc_no` | String | เลขสัญญาใหม่ (กรณีต่อสัญญา) |
| `update_at` | Timestamp | เวลาที่อัปเดตล่าสุด (Asia/Bangkok) |

## Tech Stack

- Python / Azure Functions
- Delta Lake (deltalake)
- Microsoft Fabric Lakehouse / OneLake
- Azure AD (Client Credentials)
- HMAC SHA-256 (ป้องกัน request ปลอม)

## Related Project

- Streamlit Dashboard: https://github.com/tanasedw/contract-management
