# Contract Management — Purchaser Status

ระบบบันทึกสถานะสัญญาสำหรับฝ่ายจัดซื้อ ช่วยให้ผู้ใช้สามารถระบุสถานะของแต่ละ Purchasing Document ได้ว่า ต่อสัญญา / ไม่ต่อสัญญา / ยกเลิกสัญญาก่อนกำหนด พร้อมเพิ่มหมายเหตุและเลขสัญญาใหม่ได้

ข้อมูลถูกดึงจาก Microsoft Fabric Lakehouse (Delta Lake) และบันทึกกลับแบบ Real-time

## Features
- เลือก Purchasing Doc No แล้วกรอก Purchaser Status ได้ทันที
- เพิ่ม Comment และเลขสัญญาใหม่
- แสดงรายการที่บันทึกแล้วพร้อม Contract Name และเวลาอัปเดต (Asia/Bangkok)
- เชื่อมต่อ Microsoft Fabric OneLake ผ่าน Azure AD

## Tech Stack
- Python / Streamlit
- Delta Lake (deltalake)
- Microsoft Fabric Lakehouse / OneLake
- Azure AD (Client Credentials)

## Demo
https://uuxzr59zpuxokqkqtrq763.streamlit.app/

## Source Code
https://github.com/tanasedw/contract-management