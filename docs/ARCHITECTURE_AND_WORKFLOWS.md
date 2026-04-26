# Architecture And Workflows

เอกสารนี้อธิบายสถาปัตยกรรมของระบบและ workflow หลักจากโค้ดจริง

## 1. ภาพรวมสถาปัตยกรรม

ระบบนี้เป็น web application แบบ monolith ที่แยกชั้นการทำงานชัดเจน

- `app/main.py` เป็นจุดเริ่มต้นของ FastAPI application
- `app/api/routers/` แยก endpoints ตามโมดูล
- `app/services/` เก็บ business logic
- `app/db/models/` เก็บ ORM models
- `app/schemas/` เก็บ request/response schemas
- `app/security/` เก็บ middleware และ security helpers
- `app/templates/` และ `app/static/` เป็น frontend

แนวคิดคือ router รับ request, service จัดการ logic, model คุยกับฐานข้อมูล, แล้ว schema จัดรูปข้อมูลที่รับและส่งกลับ

## 2. Request lifecycle แบบสั้น

1. Browser เปิดหน้า `/`
2. FastAPI render `index.html`
3. JavaScript ใน `app/static/app.js` เรียก API ต่างๆ
4. Request ผ่าน middleware เช่น session, CSRF, trusted hosts, rate limit
5. Router ตรวจ role หรือ current user
6. Service layer ทำ business logic
7. SQLAlchemy อ่านหรือเขียน PostgreSQL
8. Response กลับไป render บนหน้าเว็บ

## 3. Middleware และ infrastructure

จาก [app/main.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/main.py:1)

ระบบมี middleware หลักดังนี้

- `TrustedHostMiddleware`
- `CSRFMiddleware`
- `SessionMiddleware`
- `CORSMiddleware`
- `SlowAPIMiddleware`

ยังมี health endpoints:

- `/healthz` สำหรับ liveness
- `/readyz` สำหรับ readiness โดยเช็กว่าตารางฐานข้อมูลพร้อมจริง

## 4. Authentication workflow

จาก [app/api/routers/auth.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/api/routers/auth.py:1) และ [app/services/auth_service.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/services/auth_service.py:1)

### Register

1. ผู้ใช้ส่งข้อมูลไป `/auth/register`
2. ระบบเช็กว่า email ซ้ำหรือไม่
3. ระบบดึง role `Student`
4. hash รหัสผ่าน
5. บันทึก user ใหม่

### Login

1. ผู้ใช้ส่ง email/password ไป `/auth/login`
2. ระบบตรวจรหัสผ่าน
3. ถ้าถูกต้องจะเริ่ม session
4. session เก็บ `user_id` และ `csrf_token`
5. ระบบคืน header CSRF ให้ client ใช้กับ request ที่แก้ไขข้อมูล

### Logout

1. ล้าง session
2. ลบ cookie

## 5. Role-based access workflow

จาก [app/security/rbac.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/security/rbac.py:1)

router ที่สำคัญจะใช้ `require_roles(...)`

ตัวอย่าง:

- `Staff`, `Admin` เข้าถึง reports ได้
- `Technician`, `Admin` เข้าถึง maintenance queue ได้
- `Admin` จัดการ labs, equipments, users, audit logs ได้

จุดสำคัญคือ role ถูก enforce ฝั่ง backend ไม่ใช่ซ่อนแค่ปุ่มใน frontend

## 6. Reservation workflow

จาก [app/services/reservation_service.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/services/reservation_service.py:1) และ [app/schemas/reservations.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/schemas/reservations.py:1)

### Availability

1. ผู้ใช้เลือกวันที่
2. frontend เรียก `/reservations/availability`
3. backend ดึงห้องทั้งหมดและรายการจองที่ active
4. ระบบคำนวณ availability ตาม fixed slots
5. ส่งกลับเป็นรายห้องและราย slot

### Create reservation

1. ผู้ใช้เลือกห้องและ slot
2. frontend แปลง slot เป็น `start_time` และ `end_time`
3. Pydantic ตรวจว่าตรงกับ fixed slot ที่กำหนด
4. service เช็กว่าห้องยัง available
5. service เช็ก overlap
6. บันทึก reservation
7. database ยังมี exclusion constraint กันซ้ำอีกชั้น

### Cancel reservation

1. ผู้ใช้ยกเลิกได้เฉพาะ reservation ของตัวเอง
2. เปลี่ยน status เป็น `Cancelled`

## 7. Borrowing workflow

จาก [app/services/borrowing_service.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/services/borrowing_service.py:1)

### Create borrowing

1. Staff/Admin ส่ง request สร้างรายการยืม
2. ระบบเช็กว่าผู้ยืมมีอยู่จริงและ active
3. ล็อก row ของ equipment ด้วย `with_for_update()`
4. เช็กว่าอุปกรณ์ available
5. เช็กว่าไม่มี active borrowing
6. เช็กว่าไม่มี open maintenance
7. เช็กว่าเวลาคืนต้องอยู่ในอนาคต
8. สร้าง borrowing
9. อัปเดต equipment status
10. บันทึก audit log

### Return borrowing

1. ค้นหารายการยืม
2. เช็กว่ายัง active อยู่
3. ล็อก row ของ equipment
4. ตั้ง `actual_return`
5. เปลี่ยน borrowing เป็น `Returned`
6. คำนวณ penalty ถ้าคืนช้า
7. ถ้ามี penalty ให้สร้าง notification
8. บันทึก audit log
9. อัปเดต equipment status ตาม state จริง

## 8. Maintenance workflow

จาก [app/services/maintenance_service.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/services/maintenance_service.py:1)

### Report maintenance

1. ผู้ใช้ส่งคำขอแจ้งซ่อม
2. ระบบล็อก equipment
3. สร้าง maintenance record
4. อัปเดต equipment status
5. บันทึก audit log

### Update maintenance

1. Technician/Admin เปลี่ยนสถานะ
2. ระบบบันทึก technician_id
3. ถ้าสถานะเป็น `Fixed` จะตั้ง resolved_date
4. ส่ง notification ให้ผู้แจ้ง
5. อัปเดต equipment status
6. บันทึก audit log

## 9. Equipment state resolution

จาก [app/services/equipment_state_service.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/services/equipment_state_service.py:1)

ระบบไม่ได้พึ่ง status ที่ผู้ใช้กรอกอย่างเดียว แต่มีฟังก์ชัน derive state

- ถ้ามี borrowing ที่ active => `Borrowed`
- ถ้ามี maintenance ที่ยังไม่ fixed => `In_Repair`
- ไม่เข้าเงื่อนไขข้างบน => `Available`

นี่เป็นจุดสำคัญมาก เพราะช่วยให้ state สอดคล้องกับความจริงของ transaction

## 10. Reporting workflow

จาก [app/api/routers/reports.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/api/routers/reports.py:1)

รายงาน advanced SQL มี 5 รายการ

- late borrowings
- top borrowers / penalty summary
- lab utilization
- equipment repairs
- reservation summary

ข้อดีคือเป็น query จริงจากหลายตาราง เหมาะกับการตอบอาจารย์ว่าระบบนี้ไม่ได้มีแต่ CRUD แต่มี analytical queries ด้วย

## 11. Frontend workflow

จาก [app/static/app.js](/abs/path/C:/Users/saifa/Desktop/cn230/app/static/app.js:1)

frontend ทำงานแบบ dashboard เดียว แล้วเปิด panel ตาม role

- load current user
- ดึงข้อมูล common เช่น labs, reservations, borrowings, penalties, notifications
- ถ้าเป็น staff/admin จะดึงข้อมูลเพิ่ม
- submit form ผ่าน fetch ไปยัง API
- render รายการและ report tables กลับบนหน้าเดียว

ข้อดีของวิธีนี้คือ demo ง่าย เพราะแสดง flow หลักของระบบครบในหน้าเดียว

## 12. ภาพรวม endpoint สำคัญ

จาก route ที่ประกาศจริงในโค้ด

- auth: register, login, logout, me
- reservations: my, list, availability, create, cancel, update, delete
- borrowings: my, list, create, return
- maintenance: queue, create, update
- notifications: my, mark read
- penalties: my
- admin: users, roles, labs CRUD, equipments CRUD, change role/status, audit logs
- reports: 5 advanced SQL reports

## 13. ประโยคสรุปสำหรับพรีเซนต์

"ระบบนี้ออกแบบเป็น monolithic web application ที่แยกชั้นชัดเจนระหว่าง router, service, model, schema และ security ทำให้ business logic สำคัญอย่างการจองห้อง, ยืมคืน, แจ้งซ่อม และคิดค่าปรับ ถูกควบคุมได้เป็นระบบและตรวจสอบย้อนกลับได้"

## แหล่งอ้างอิง

- [app/main.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/main.py:1)
- [app/services/reservation_service.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/services/reservation_service.py:1)
- [app/services/borrowing_service.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/services/borrowing_service.py:1)
- [app/services/maintenance_service.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/services/maintenance_service.py:1)
- [app/static/app.js](/abs/path/C:/Users/saifa/Desktop/cn230/app/static/app.js:1)
