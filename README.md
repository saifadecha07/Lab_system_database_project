# Smart Lab Management System

โปรเจกต์นี้เป็นระบบบริหารจัดการห้องปฏิบัติการและอุปกรณ์สำหรับรายวิชา CN230 โดยพัฒนาเป็นเว็บแอปด้วย FastAPI, SQLAlchemy, PostgreSQL และหน้าเว็บแบบ server-rendered + JavaScript frontend เพื่อให้ผู้ใช้แต่ละบทบาทสามารถจองห้อง ยืมอุปกรณ์ ติดตามงานซ่อม ดูค่าปรับ รับการแจ้งเตือน และดูรายงานจากฐานข้อมูลจริงได้

## ขอบเขตระบบ

ระบบรองรับผู้ใช้ 4 บทบาท

- `Student`
- `Staff`
- `Technician`
- `Admin`

ความสามารถหลักของระบบ

- สมัครสมาชิกและเข้าสู่ระบบแบบ session-based authentication
- ควบคุมสิทธิ์ด้วย role-based access control
- จองห้องปฏิบัติการแบบ fixed time slots
- ยืมและคืนอุปกรณ์
- แจ้งซ่อมและติดตามสถานะงานซ่อม
- คำนวณค่าปรับจากการคืนอุปกรณ์ล่าช้า
- แจ้งเตือนผู้ใช้
- เก็บ audit logs สำหรับ action สำคัญ
- แสดงรายงาน SQL เชิงวิเคราะห์ 5 รายการ

## Fixed Time Slots สำหรับการจองห้อง

ระบบจองห้องถูกปรับให้จองได้เฉพาะ 3 รอบเวลาเพื่อให้ใช้งานง่ายและตรง requirement ที่ใช้งานจริง

- `08:00-12:00`
- `12:00-16:00`
- `16:00-20:00`

หน้า UI แสดงทั้งปุ่มเลือกรอบเวลาและตาราง availability รายวันเพื่อดูว่าห้องไหนว่างหรือถูกจองแล้ว

## โครงสร้างโปรเจกต์

```text
app/
  api/routers/        เส้นทาง API ของแต่ละโมดูล
  db/models/          ORM models ของฐานข้อมูล
  schemas/            Pydantic schemas สำหรับ request/response
  security/           session, CSRF, hashing, RBAC, rate limiting
  services/           business logic ของระบบ
  static/             JavaScript และ CSS ของหน้าเว็บ
  templates/          HTML templates
docs/                 เอกสารสรุประบบและเอกสารประกอบส่งงาน
  reference/          ไฟล์โจทย์งาน, แบบฐานข้อมูล, และไฟล์อ้างอิงต้นฉบับ
sql/                  schema SQL หลักของฐานข้อมูล
scripts/              helper scripts สำหรับ seed data และ setup ฐานข้อมูล
tests/                automated tests
```

## ฐานข้อมูล

ตารางหลักของระบบ

- `roles`
- `users`
- `lab_types`
- `labs`
- `equipment_categories`
- `equipments`
- `lab_reservations`
- `reservation_participants`
- `equipment_borrowings`
- `maintenance_records`
- `penalties`
- `notifications`
- `audit_logs`

อ้างอิง schema หลักจาก [sql/schema.sql](/abs/path/C:/Users/saifa/Desktop/cn230/sql/schema.sql:1)

## Advanced Reports

ระบบมีรายงานเชิงวิเคราะห์อย่างน้อย 5 รายการจากฐานข้อมูลจริง

- Late Borrowings
- Top Borrowers
- Lab Utilization
- Equipment Repairs
- Reservation Summary

## เทคโนโลยีที่ใช้

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Jinja2
- Vanilla JavaScript
- CSS

## การติดตั้งและรันในเครื่อง

1. ติดตั้ง Python 3.11 หรือใหม่กว่า
2. สร้าง virtual environment
3. ติดตั้ง dependencies

```powershell
pip install -r requirements.txt
```

4. สร้างไฟล์ `.env` จาก `.env.example`
5. กำหนดค่า `DATABASE_URL` ให้ชี้ไปยัง PostgreSQL
6. สร้าง schema ด้วยวิธีใดวิธีหนึ่ง

แบบ Alembic

```powershell
alembic upgrade head
```

หรือใช้ helper script

```powershell
python scripts/create_tables.py
```

7. รันแอป

```powershell
uvicorn app.main:app --reload
```

8. เปิดใช้งานที่

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/healthz`
- `http://127.0.0.1:8000/readyz`

## ความปลอดภัยและการควบคุมสิทธิ์

ระบบมีองค์ประกอบที่เกิน requirement พื้นฐานของวิชาและใช้ตอบอาจารย์ได้

- session authentication
- CSRF protection สำหรับ browser requests ที่แก้ไขข้อมูล
- password hashing
- rate limiting สำหรับ login
- RBAC ตามบทบาทผู้ใช้
- audit logging สำหรับ action สำคัญ
- reservation overlap protection ทั้งระดับ service และ database

## เอกสารสำคัญในโปรเจกต์

- [docs/SPEC_COMPLIANCE_AUDIT.md](/abs/path/C:/Users/saifa/Desktop/cn230/docs/SPEC_COMPLIANCE_AUDIT.md:1)
- [docs/SPEC_ALIGNMENT_CHANGES.md](/abs/path/C:/Users/saifa/Desktop/cn230/docs/SPEC_ALIGNMENT_CHANGES.md:1)
- [docs/PROJECT_SPEC_MAPPING.md](/abs/path/C:/Users/saifa/Desktop/cn230/docs/PROJECT_SPEC_MAPPING.md:1)
- [docs/DATABASE_DESIGN_FINAL.md](/abs/path/C:/Users/saifa/Desktop/cn230/docs/DATABASE_DESIGN_FINAL.md:1)
- [docs/SYSTEM_WALKTHROUGH.md](/abs/path/C:/Users/saifa/Desktop/cn230/docs/SYSTEM_WALKTHROUGH.md:1)
- [docs/PRESENTATION_SCRIPT.md](/abs/path/C:/Users/saifa/Desktop/cn230/docs/PRESENTATION_SCRIPT.md:1)

## สถานะความพร้อมสำหรับส่งงาน

จุดที่ระบบผ่านชัดเจน

- เชื่อมฐานข้อมูลจริง
- มีหลายบทบาทผู้ใช้
- มี relational schema พร้อม PK/FK/constraints
- มี DDL และ sample/demo data
- มี advanced SQL reports อย่างน้อย 5 รายการ
- มี web interface เชื่อมฐานข้อมูลจริง
- มี CRUD สำหรับข้อมูลหลักในระดับใช้งานจริงมากขึ้น

หมายเหตุ

- README นี้อัปเดตจาก implementation ปัจจุบัน ไม่ใช่ scaffold เริ่มต้น
- ถ้าจะส่ง final package ควรใส่รายชื่อสมาชิกและลิงก์วิดีโอเดโมเพิ่มในส่วนท้ายของ README
