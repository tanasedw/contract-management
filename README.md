# Contract Management — Email Button

ระบบปุ่มกดในอีเมล alert สำหรับฝ่ายจัดซื้อ เมื่อได้รับอีเมลแจ้งเตือนสัญญา ผู้ใช้สามารถกดปุ่มในอีเมลเพื่อระบุสถานะได้ทันที โดยไม่ต้องเข้าระบบใด ๆ

ข้อมูลจะถูกบันทึกลง Microsoft Fabric Lakehouse (Delta Lake) แบบ Real-time

## How it works
1. ระบบส่งอีเมล alert พร้อมปุ่ม เช่น "ต่อสัญญา / ไม่ต่อสัญญา / ยกเลิกสัญญาก่อนกำหนด"
2. แต่ละปุ่มคือ URL ที่ฝัง `doc_no`, `action`, และ `sig` (HMAC signature)
3. เมื่อกดปุ่ม Azure Function จะตรวจสอบ signature แล้วบันทึกสถานะลง Fabric Lakehouse
4. แสดงหน้ายืนยันให้ผู้ใช้ทราบว่าบันทึกเรียบร้อย

## Tech Stack
- Python / Azure Functions
- Delta Lake (deltalake)
- Microsoft Fabric Lakehouse / OneLake
- Azure AD (Client Credentials)
- HMAC SHA-256 (ป้องกัน request ปลอม)

## Source Code
https://github.com/tanasedw/contract-management