# Smart Lab Management System Walkthrough

เอกสารนี้เขียนเพื่อใช้ตอบอาจารย์เกี่ยวกับระบบทั้งหมดของโปรเจกต์นี้แบบอธิบายได้เป็นส่วน ๆ ว่าโค้ดแต่ละชั้นทำอะไร ข้อมูลไหลอย่างไร ตารางฐานข้อมูลสัมพันธ์กันอย่างไร และหน้า UI คุยกับ backend แบบไหน

## 1. ภาพรวมระบบ

โปรเจกต์นี้เป็นระบบจัดการห้องปฏิบัติการและทรัพยากรภายในแลป โดยมีฟีเจอร์หลักดังนี้

- สมัครสมาชิกและล็อกอิน
- แยกสิทธิ์ตาม role
- จองห้องแลป
- ยืมอุปกรณ์
- แจ้งซ่อมอุปกรณ์
- คำนวณค่าปรับเมื่อคืนอุปกรณ์ช้า
- แจ้งเตือนผู้ใช้
- เก็บ audit log สำหรับเหตุการณ์สำคัญ
- แสดงรายงาน SQL หลายตารางสำหรับวิชา Database Systems

เทคโนโลยีหลักที่ใช้

- FastAPI เป็น web framework
- SQLAlchemy ORM เป็นชั้นเชื่อมฐานข้อมูล
- Pydantic เป็นชั้น validate request/response
- Starlette SessionMiddleware สำหรับ session login
- SlowAPI สำหรับ rate limit
- Jinja2 + HTML/CSS/JavaScript สำหรับหน้าเว็บ
- Alembic สำหรับ migration ฐานข้อมูล

## 2. โครงสร้างระบบระดับสูง

ระบบแบ่งเป็น 7 ชั้นหลัก

1. `app/main.py`
   จุดเริ่มต้นของแอป สร้าง FastAPI app, ผูก middleware, mount static files, include routers, และเปิด endpoint หลัก

2. `app/config.py`
   รวมค่าตั้งค่าทั้งหมดจาก environment variables เช่น `DATABASE_URL`, `SECRET_KEY`, cookie config, CORS, allowed hosts, rate limit และค่าปรับต่อชั่วโมง

3. `app/db/`
   จัดการฐานข้อมูล ประกอบด้วย base class, engine/session และ ORM models

4. `app/schemas/`
   นิยามรูปแบบข้อมูล request และ response เพื่อให้ backend รับและคืนข้อมูลอย่างถูกชนิด

5. `app/api/routers/`
   เป็นชั้น HTTP endpoint รับ request จาก frontend หรือผู้ใช้ API แล้วส่งงานต่อไปที่ service

6. `app/services/`
   เป็น business logic หลัก เช่น login, create reservation, return equipment, สร้าง penalty, สร้าง notification, บันทึก audit log

7. `app/security/`
   เป็นชั้น security เช่น password hashing, rate limit, RBAC, CSRF, session helper

## 3. Request Flow ของระบบ

เวลามี request เข้ามา flow หลักจะเป็นแบบนี้

1. Browser ส่ง request มาที่ endpoint
2. Router ใน `app/api/routers/` รับ request
3. Pydantic schema ตรวจว่าข้อมูลถูก format หรือไม่
4. Dependency `get_current_user` เช็ก session ว่าผู้ใช้ล็อกอินอยู่ไหม
5. ถ้า endpoint ต้องจำกัดสิทธิ์ จะเรียก `require_roles(...)`
6. Router ส่งข้อมูลต่อไปที่ service layer
7. Service layer คุยกับ SQLAlchemy ORM และ commit ลงฐานข้อมูล
8. Router ส่ง response กลับตาม response model
9. Frontend JavaScript เอาข้อมูลมา render ลงหน้าเว็บ

## 4. Entry Point และ Middleware

ไฟล์หลักคือ `app/main.py`

หน้าที่ของไฟล์นี้

- สร้าง FastAPI app
- สร้าง `templates = Jinja2Templates(directory="app/templates")`
- mount static file ที่ `/static`
- include router ทุกตัว
- เพิ่ม middleware ด้าน security
- เปิดหน้า `/`, `/healthz`, `/readyz`

middleware ที่สำคัญ

- `TrustedHostMiddleware`
  ป้องกัน request จาก host ที่ไม่อยู่ใน `ALLOWED_HOSTS`

- `CSRFMiddleware`
  ตรวจ `X-CSRF-Token` สำหรับ request ที่แก้ข้อมูล เช่น POST/PATCH

- `SessionMiddleware`
  เก็บ session แบบ cookie-backed

- `CORSMiddleware`
  อนุญาต origin ตามค่าที่กำหนดใน config

- `SlowAPIMiddleware`
  ใช้ร่วมกับ limiter เพื่อ rate limit login

endpoint สำคัญใน `main.py`

- `/`
  render หน้า `index.html`

- `/healthz`
  ใช้เช็กว่า process ของแอปยังทำงานอยู่

- `/readyz`
  เช็กความพร้อมของ schema ฐานข้อมูลผ่าน `check_database_state()`

หมายเหตุ

- หน้า home ส่ง `static_version` เข้า template เพื่อ cache-busting ทำให้ browser โหลด `app.js` และ `style.css` เวอร์ชันล่าสุด

## 5. Configuration

ไฟล์ `app/config.py` ใช้ `BaseSettings` ของ Pydantic

ค่าหลักที่ระบบใช้

- `app_env`
- `app_name`
- `debug`
- `secret_key`
- `database_url`
- `session_cookie_name`
- `session_max_age`
- `session_same_site`
- `session_https_only`
- `password_hash_scheme`
- `rate_limit_login`
- `allowed_hosts`
- `cors_origins`
- `csrf_header_name`
- `csrf_exempt_paths`
- `penalty_rate_per_hour`

logic สำคัญในไฟล์นี้

- `_split_csv()`
  แปลงค่า env ที่เป็น string แบบคั่น comma ให้เป็น list

- `normalize_database_url()`
  แปลง `postgres://` หรือ `postgresql://` ให้เป็น `postgresql+psycopg://`

- `include_platform_hosts()`
  รวม Railway healthcheck host เข้าไปใน allowed hosts โดยอัตโนมัติ

- `validate_same_site()`
  บังคับว่า `session_same_site` ต้องเป็น `lax`, `strict` หรือ `none`

## 6. Database Layer

### 6.1 `app/db/base.py`

ใช้เป็น declarative base สำหรับ SQLAlchemy models ทั้งหมด

### 6.2 `app/db/session.py`

หน้าที่หลัก

- อ่าน `database_url`
- สร้าง SQLAlchemy engine
- สร้าง `SessionLocal`
- เปิด generator `get_db()` สำหรับ dependency injection

logic สำคัญ

- ถ้าเป็น SQLite จะใช้ `check_same_thread=False`
- ถ้าเป็น in-memory SQLite จะใช้ `StaticPool`
- ถ้าเป็น PostgreSQL จะตั้งค่า pool เช่น `pool_pre_ping`, `pool_recycle`, `pool_size`, `max_overflow`

## 7. ORM Models และความสัมพันธ์ของตาราง

### 7.1 `roles`

ไฟล์ `app/db/models/role.py`

เก็บชื่อ role เช่น

- Student
- Staff
- Technician
- Admin

relationship

- 1 role มีผู้ใช้หลายคน

### 7.2 `users`

ไฟล์ `app/db/models/user.py`

ฟิลด์สำคัญ

- `user_id`
- `role_id`
- `email`
- `first_name`
- `last_name`
- `password_hash`
- `is_active`

relationship

- user มี role เดียว
- user มี reservation ได้หลายรายการ
- user มี borrowing ได้หลายรายการ
- user มี notification ได้หลายรายการ

### 7.3 `labs`

ไฟล์ `app/db/models/lab.py`

ฟิลด์สำคัญ

- `lab_id`
- `lab_type_id`
- `room_name`
- `capacity`
- `status`

constraint สำคัญ

- `capacity > 0`

relationship

- ห้องหนึ่งมี reservation ได้หลายรายการ
- ห้องหนึ่งมีอุปกรณ์หลายชิ้น

### 7.4 `equipments`

ไฟล์ `app/db/models/equipment.py`

ฟิลด์สำคัญ

- `equipment_id`
- `category_id`
- `lab_id`
- `equipment_name`
- `status`

relationship

- อุปกรณ์อยู่ในห้องได้ 0 หรือ 1 ห้อง
- อุปกรณ์มี borrowing history ได้หลายรายการ

### 7.5 `lab_reservations`

ไฟล์ `app/db/models/reservation.py`

ฟิลด์สำคัญ

- `reservation_id`
- `lab_id`
- `reserved_by`
- `start_time`
- `end_time`
- `status`

relationship

- reservation เป็นของห้องหนึ่งห้อง
- reservation เป็นของ user คนที่จอง
- reservation มี participant หลายคนได้ผ่านตาราง `reservation_participants`

### 7.6 `reservation_participants`

เป็นตาราง many-to-many ระหว่าง reservation กับ user

ใช้กรณีต้องการเก็บว่ามีสมาชิกคนไหนเข้าร่วมการจองนั้นบ้าง

### 7.7 `equipment_borrowings`

ไฟล์ `app/db/models/borrowing.py`

ฟิลด์สำคัญ

- `borrow_id`
- `user_id`
- `equipment_id`
- `borrow_time`
- `expected_return`
- `actual_return`
- `status`

ใช้เก็บประวัติการยืมอุปกรณ์

### 7.8 `maintenance_records`

ไฟล์ `app/db/models/maintenance.py`

ฟิลด์สำคัญ

- `repair_id`
- `equipment_id`
- `reported_by`
- `technician_id`
- `report_date`
- `resolved_date`
- `issue_detail`
- `status`

ใช้เก็บข้อมูลแจ้งซ่อมและสถานะการซ่อม

### 7.9 `penalties`

ไฟล์ `app/db/models/penalty.py`

ฟิลด์สำคัญ

- `penalty_id`
- `user_id`
- `borrow_id`
- `fine_amount`
- `is_resolved`

ใช้ผูกค่าปรับกับ borrowing ที่คืนช้า

### 7.10 `notifications`

ไฟล์ `app/db/models/notification.py`

ฟิลด์สำคัญ

- `notification_id`
- `user_id`
- `message`
- `is_read`

ใช้ส่งข้อความแจ้งเตือนให้ผู้ใช้

### 7.11 `audit_logs`

ไฟล์ `app/db/models/audit_log.py`

ฟิลด์สำคัญ

- `audit_log_id`
- `actor_user_id`
- `action`
- `target_type`
- `target_id`
- `details`
- `created_at`

ใช้เก็บประวัติการกระทำสำคัญ เช่น สร้างห้อง เปลี่ยน role คืนอุปกรณ์ อัปเดตงานซ่อม

### 7.12 `TimestampMixin`

ไฟล์ `app/db/models/mixins.py`

ให้ field ร่วมกับหลายตาราง

- `created_at`
- `updated_at`

## 8. SQL Schema และ Migration

มี 2 ส่วน

- `sql/schema.sql`
  เป็น DDL ฉบับ PostgreSQL แบบเต็ม เหมาะใช้ดูภาพรวม schema ทั้งระบบ

- `migrations/versions/*.py`
  เป็น Alembic migration สำหรับใช้สร้าง schema จริงในแอป

### Migration 0001

ไฟล์ `migrations/versions/20260409_0001_initial_schema.py`

ทำหน้าที่

- สร้างตารางหลักทั้งหมด
- สร้าง index หลายตัว
- seed role เริ่มต้น 4 role

### Migration 0002

ไฟล์ `migrations/versions/20260409_0002_reservation_exclusion_constraint.py`

ทำหน้าที่

- เปิด extension `btree_gist`
- เพิ่ม exclusion constraint เพื่อกัน reservation time overlap ใน PostgreSQL

แนวคิดสำคัญ

- app-level เช็ก overlap ใน service layer
- db-level กัน overlap ซ้ำอีกชั้นใน PostgreSQL

นี่คือการป้องกัน race condition ที่ดี เพราะไม่พึ่ง frontend อย่างเดียว

## 9. Security Layer

### 9.1 Password Hashing

ไฟล์ `app/security/hashing.py`

ใช้ `pwdlib.PasswordHash.recommended()`

มี 2 ฟังก์ชัน

- `hash_password(password)`
- `verify_password(password, hashed_password)`

แนวคิด

- ไม่เก็บ plain text password
- เก็บเฉพาะ hash

### 9.2 Session Helper

ไฟล์ `app/security/session.py`

ฟังก์ชันหลัก

- `start_user_session()`
  เคลียร์ session เดิมแล้วเก็บ `user_id` กับ `csrf_token`

- `clear_user_session()`
  ล้าง session และลบ cookie

- `get_csrf_token()`
  ดึง CSRF token ออกจาก session

### 9.3 CSRF Middleware

ไฟล์ `app/security/csrf.py`

หน้าที่

- บังคับให้ request ที่แก้ข้อมูลและมี session ต้องส่ง `X-CSRF-Token`
- ตรวจ token ใน session กับ token ใน header ว่าตรงกันหรือไม่
- ถ้าผ่าน จะส่ง token กลับใน response header เพื่อให้ frontend ใช้ต่อ

safe methods ที่ไม่ต้องตรวจ

- GET
- HEAD
- OPTIONS

### 9.4 RBAC

ไฟล์ `app/security/rbac.py`

ฟังก์ชันหลักคือ `require_roles(*role_names)`

ทำงานโดย

- อ่าน role จาก `current_user`
- ถ้า role ไม่อยู่ในรายการที่อนุญาต จะ raise `403 Insufficient permissions`

### 9.5 Rate Limit

ไฟล์ `app/security/rate_limit.py`

สร้าง `Limiter` โดยใช้ IP ของ client เป็น key

ในระบบนี้ route login ใช้ `@limiter.limit("5/minute")`

## 10. Authentication และ User Flow

### 10.1 `app/api/deps.py`

มี `get_current_user()`

ทำงานดังนี้

- อ่าน `user_id` จาก `request.session`
- ถ้าไม่มี session -> 401
- query user จากฐานข้อมูลพร้อมโหลด role
- ถ้า user ไม่มีหรือ inactive -> 401

### 10.2 Auth Router

ไฟล์ `app/api/routers/auth.py`

endpoint

- `POST /auth/register`
  สมัครสมาชิกใหม่

- `POST /auth/login`
  ล็อกอิน

- `POST /auth/logout`
  ออกจากระบบ

- `GET /auth/me`
  ดึงข้อมูล user ที่ล็อกอินอยู่

### 10.3 Auth Service

ไฟล์ `app/services/auth_service.py`

ฟังก์ชันสำคัญ

- `get_or_create_default_student_role()`
  คาดหวังว่าต้องมี role ชื่อ Student อยู่ในระบบ

- `register_user()`
  ตรวจอีเมลซ้ำ
  assign role Student
  hash password
  บันทึกผู้ใช้ใหม่

- `authenticate_user()`
  query user ตาม email
  verify password
  เช็กว่า account ยัง active

## 11. API Routers ทั้งหมด

### 11.1 `users.py`

- `GET /users/me`
  ดึง profile ของผู้ใช้ที่ล็อกอิน

### 11.2 `labs.py`

- `GET /labs`
  คืนเฉพาะห้องที่ `status == "Available"`

### 11.3 `equipments.py`

- `GET /equipments`
  คืนเฉพาะอุปกรณ์ที่ `status == "Available"`

### 11.4 `reservations.py`

- `GET /reservations/my`
  ดูการจองของตัวเอง

- `GET /reservations/availability?booking_date=YYYY-MM-DD`
  ดูตารางรอบเวลาวันนั้นว่าห้องไหนว่างหรือไม่

- `POST /reservations`
  สร้างการจองใหม่

- `POST /reservations/{reservation_id}/cancel`
  ยกเลิกการจองของตัวเอง

### 11.5 `maintenance.py`

- `GET /maintenance/queue`
  สำหรับ Technician/Admin ดูคิวแจ้งซ่อมทั้งหมด

- `POST /maintenance`
  ผู้ใช้แจ้งซ่อมอุปกรณ์

- `PATCH /maintenance/{repair_id}`
  Technician/Admin อัปเดตสถานะงานซ่อม

### 11.6 `borrowings.py`

- `GET /borrowings/my`
  ผู้ใช้ดูรายการยืมของตัวเอง

- `GET /borrowings?status_filter=...`
  Staff/Admin ดู borrowing ทั้งหมดหรือ filter ตาม status

- `POST /borrowings`
  Staff/Admin ออกอุปกรณ์ให้ผู้ใช้ยืม

- `PATCH /borrowings/{borrow_id}/return`
  Staff/Admin ทำรายการคืนอุปกรณ์

### 11.7 `penalties.py`

- `GET /penalties/my`
  ผู้ใช้ดูค่าปรับของตัวเอง

### 11.8 `notifications.py`

- `GET /notifications/my`
  ผู้ใช้ดูการแจ้งเตือนของตัวเอง

### 11.9 `staff.py`

- `GET /staff/users`
  Staff/Admin ดูรายชื่อ user

- `GET /staff/reports/summary`
  Staff/Admin ดู summary dashboard

### 11.10 `admin.py`

- `GET /admin/users`
  Admin ดูผู้ใช้ทั้งหมด

- `GET /admin/roles`
  Admin ดู role ทั้งหมด

- `POST /admin/labs`
  Admin สร้างห้องใหม่

- `POST /admin/equipments`
  Admin สร้างอุปกรณ์ใหม่

- `PATCH /admin/users/{user_id}/role`
  Admin เปลี่ยน role ผู้ใช้

- `GET /admin/audit-logs`
  Admin ดู audit log

### 11.11 `reports.py`

เป็น endpoint รายงาน SQL ขั้นสูงสำหรับโจทย์วิชา CN230

- `GET /reports/late-borrowings`
- `GET /reports/top-borrowers`
- `GET /reports/lab-utilization`
- `GET /reports/equipment-repairs`
- `GET /reports/reservation-summary`

ทุก endpoint นี้ต้องเป็น Staff หรือ Admin

## 12. Reservation Logic แบบละเอียด

ไฟล์หลักคือ `app/services/reservation_service.py`

### 12.1 `create_reservation()`

ขั้นตอนทำงาน

1. query ห้องตาม `lab_id`
2. บังคับว่าห้องต้อง `Available`
3. query หา reservation ที่ time overlap และ status ยัง active
4. ถ้าชน -> 409 conflict
5. ถ้าไม่ชน -> สร้าง reservation ใหม่ status `Pending`
6. commit
7. ถ้า database โยน `IntegrityError` จาก exclusion constraint -> rollback แล้วคืน 409

### 12.2 fixed slots

ไฟล์ `app/schemas/reservations.py` กำหนดรอบเวลา fix ไว้ 3 รอบ

- `08:00-12:00`
- `12:00-16:00`
- `16:00-20:00`

แนวคิด

- frontend ไม่ให้กรอกเวลาอิสระ
- backend ก็ validate ซ้ำอีกชั้น

ฟังก์ชันสำคัญ

- `to_booking_timezone()`
  แปลงเวลาไปที่ `Asia/Bangkok`

- `resolve_fixed_slot()`
  เช็กว่า `start_time` กับ `end_time` ตรงกับรอบใดรอบหนึ่งหรือไม่

### 12.3 availability

`get_reservation_availability()` จะ

1. รับ `booking_date`
2. query ห้องทั้งหมด
3. query reservation ที่ยัง active
4. วนทุกห้องและทุก slot
5. ตัดสินว่า slot นี้ available หรือไม่
6. ส่ง response ที่ frontend นำไป render เป็นตารางจอง

## 13. Borrowing Logic แบบละเอียด

ไฟล์ `app/services/borrowing_service.py`

### 13.1 `create_borrowing()`

ขั้นตอน

1. เช็ก borrower ว่ามีจริงและ active
2. เช็ก equipment ว่ามีจริง
3. เช็กว่าอุปกรณ์ต้อง `Available`
4. สร้าง borrowing status `Borrowed`
5. เปลี่ยน status ของ equipment เป็น `Borrowed`
6. สร้าง audit log
7. commit

### 13.2 `mark_equipment_returned()`

ขั้นตอน

1. หา borrowing ตาม `borrow_id`
2. ต้องมี status `Borrowed`
3. หา equipment ที่เกี่ยวข้อง
4. ตั้ง `actual_return = now()`
5. เปลี่ยน borrowing status เป็น `Returned`
6. เปลี่ยน equipment status เป็น `Available`
7. เรียก `build_penalty()` เพื่อคิดค่าปรับ
8. ถ้ามี penalty -> บันทึก penalty และสร้าง notification
9. สร้าง audit log
10. commit

## 14. Penalty Logic

ไฟล์ `app/services/penalty_service.py`

แนวคิด

- ถ้าคืนของตรงเวลา -> ไม่มี penalty
- ถ้าคืนช้า -> คิดตามชั่วโมง
- คิดอย่างน้อย 1 ชั่วโมง

ฟังก์ชันสำคัญ

- `calculate_penalty_amount(expected_return, actual_return)`
  แปลงเวลาเป็น UTC
  คำนวณชั่วโมงที่เกิน
  คูณด้วย `settings.penalty_rate_per_hour`

- `build_penalty(...)`
  ถ้าค่าปรับ <= 0 จะคืน `None`
  ถ้ามีค่าปรับจึงสร้าง `Penalty` object

ตัวอย่าง

- ถ้าค่าปรับต่อชั่วโมง = 25
- คืนช้า 2 ชั่วโมง
- fine = 50

## 15. Maintenance Logic

ไฟล์ `app/services/maintenance_service.py`

### 15.1 `create_maintenance_report()`

ขั้นตอน

1. เช็กว่าอุปกรณ์มีจริง
2. เปลี่ยน equipment status เป็น `In_Repair`
3. สร้าง maintenance record status `Reported`
4. สร้าง audit log
5. commit

### 15.2 `update_maintenance_status()`

ขั้นตอน

1. หา maintenance record
2. หา equipment
3. บันทึก `technician_id`
4. เปลี่ยน status ตาม request
5. ถ้า status ใหม่เป็น `Fixed`
   เปลี่ยน equipment status กลับเป็น `Available`
   ตั้ง `resolved_date`
   ส่ง notification ไปหาคนที่แจ้งซ่อม
6. สร้าง audit log
7. commit

## 16. Notification และ Audit Log

### 16.1 Notification

ไฟล์ `app/services/notification_service.py`

มีหน้าที่ง่ายมาก คือสร้าง row ในตาราง notifications

ใช้ในกรณีเช่น

- คืนของช้าแล้วเกิด penalty
- งานซ่อมถูกปิดแล้ว

### 16.2 Audit Log

ไฟล์ `app/services/audit_service.py`

เป็น helper สำหรับสร้าง audit log แบบ reusable

เหตุการณ์ที่บันทึก เช่น

- `lab.created`
- `equipment.created`
- `user.role_changed`
- `equipment.borrowed`
- `equipment.returned`
- `maintenance.reported`
- `maintenance.updated`

## 17. Report Logic สำหรับวิชา Database

ไฟล์ `app/api/routers/reports.py`

จุดเด่นของไฟล์นี้คือใช้ raw SQL ผ่าน `sqlalchemy.text()` เพื่อแสดงความสามารถด้าน query หลายตาราง

### Q1 Late Borrowings

ตารางที่ใช้

- equipment_borrowings
- users
- equipments
- labs
- penalties

แนวคิด

- ดึงรายการยืมที่คืนช้า หรือยังไม่คืนและเลยกำหนดแล้ว
- JOIN ข้อมูลผู้ยืม อุปกรณ์ ห้อง และค่าปรับ

### Q2 Top Borrowers

ตารางที่ใช้

- users
- roles
- equipment_borrowings
- penalties

แนวคิด

- จัดอันดับผู้ใช้ตามจำนวนการยืมและค่าปรับรวม
- ใช้ `GROUP BY`, `HAVING`, `SUM`, `COUNT`

### Q3 Lab Utilization

ตารางที่ใช้

- labs
- lab_types
- lab_reservations
- equipments

แนวคิด

- ดูว่าห้องไหนถูกใช้งานมากแค่ไหน
- นับจำนวน reservation และจำนวนอุปกรณ์ในห้อง

### Q4 Equipment Repairs

ตารางที่ใช้

- equipments
- equipment_categories
- labs
- maintenance_records

แนวคิด

- ดูอุปกรณ์ที่เสียบ่อย
- นับ repair count และ open repairs

### Q5 Reservation Summary

ตารางที่ใช้

- lab_reservations
- labs
- users
- reservation_participants

แนวคิด

- สรุปรายการจองพร้อมจำนวนผู้เข้าร่วม
- คำนวณ duration_hours จากเวลาจริง

## 18. Frontend Architecture

frontend หลักมี 3 ไฟล์

- `app/templates/index.html`
- `app/static/style.css`
- `app/static/app.js`

### 18.1 `index.html`

เป็นหน้าเดียวแบบ dashboard

มี section หลัก

- auth panel
- overview
- resources
- student workflows
- operator panel
- technician panel
- admin panel

การซ่อน/แสดง panel ใช้ `hidden` และให้ JavaScript ตัดสินจาก role ของผู้ใช้

### 18.2 `style.css`

รับผิดชอบ

- layout ทั้งหน้า
- card / panel / button style
- ตารางรายงาน
- ตาราง reservation schedule
- slot buttons สำหรับรอบเวลา

### 18.3 `app.js`

เป็นหัวใจ frontend

state สำคัญ

- `csrfToken`
- `currentUser`
- `roles`
- `reservationAvailability`

ฟังก์ชันสำคัญ

- `api()`
  wrapper ของ fetch
  แนบ `X-CSRF-Token` ให้อัตโนมัติเมื่อจำเป็น

- `loadCurrentUser()`
  โหลด user ปัจจุบันจาก `/auth/me`

- `refreshDashboard()`
  โหลดข้อมูลทั้งหมดของ dashboard

- `renderCommon()`
  render ส่วนข้อมูลทั่วไป เช่น labs, equipments, my reservations

- `renderStaff()`
  render ส่วน staff

- `renderMaintenance()`
  render queue งานซ่อม

- `renderAdmin()`
  render รายชื่อ user, audit log, role update

- `loadReservationAvailability()`
  เรียก `/reservations/availability`

- `renderReservationSlotOptions()`
  render ปุ่มรอบเวลา 3 ปุ่มในฟอร์ม

- `renderReservationSchedule()`
  render ตารางสถานะการจองทุกห้อง

## 19. Reservation UI แบบใหม่

ระบบจองห้องถูกออกแบบใหม่ให้ใช้ง่ายกว่าเดิม

จากเดิม

- ให้ผู้ใช้กรอก `datetime-local` เอง

ปัญหา

- ใช้งานยาก
- กรอกเวลาผิดได้ง่าย
- ไม่เห็นภาพว่าห้องไหนว่าง

จึงเปลี่ยนเป็น

1. เลือกวันที่
2. เลือกห้อง
3. เลือกรอบเวลา fixed 3 รอบ
4. หรือเลือกจากตาราง schedule โดยตรง

รอบเวลาที่ระบบรองรับ

- 08:00-12:00
- 12:00-16:00
- 16:00-20:00

backend validate ซ้ำอีกชั้น เพื่อไม่ให้ใครยิง API มาด้วยช่วงเวลามั่ว ๆ

## 20. Pydantic Schemas

schema มีหน้าที่สำคัญมาก เพราะเป็นด่านแรกที่บอกว่า input ถูกหรือไม่

ตัวอย่าง

- `RegisterRequest`
  บังคับ email เป็น `EmailStr`
  password ขั้นต่ำ 12 ตัวอักษร

- `LabCreateRequest`
  บังคับ capacity > 0

- `MaintenanceCreateRequest`
  บังคับ `issue_detail` อย่างน้อย 5 ตัวอักษร

- `ReservationCreateRequest`
  บังคับว่าต้องอยู่ใน fixed slot ที่กำหนด

response model มีไว้เพื่อ

- ไม่ให้ field ที่ไม่ควรออก เช่น `password_hash` หลุดออกไป
- คุมรูปแบบข้อมูลให้ frontend ใช้งานง่าย

## 21. Tests และสิ่งที่ test ครอบคลุม

### 21.1 `tests/conftest.py`

เป็นชุด fixture กลาง

หน้าที่

- ตั้งค่า environment สำหรับ test
- สร้าง SQLite test database
- create tables
- seed roles
- สร้าง helper เช่น `create_user()`, `login()`, `create_borrowing_graph()`

### 21.2 `tests/test_app.py`

test หลักของระบบ เช่น

- หน้า root โหลดได้
- register แล้วได้ role Student
- login แล้วได้ CSRF token
- Student ห้ามเข้า route ของ admin
- admin route ต้องมี CSRF
- reservation overlap ถูก reject
- reservation ที่ไม่ตรง fixed slot ถูก reject
- availability endpoint ส่ง slot ถูกต้อง
- คืนของช้าแล้วเกิด penalty และ audit log
- staff สร้าง borrowing ได้
- admin ดู users และ roles ได้
- healthz / readyz ทำงานตามที่ควร
- favicon route คืน 204
- allowed hosts ยังรวม Railway healthcheck host

### 21.3 `tests/test_railway_startup.py`

เช็กว่า startup ของแอปไม่ไปบังคับ readiness check ตั้งแต่เริ่ม process

แนวคิดคือ

- `/healthz` ควรตอบได้แม้ schema ยังไม่พร้อม
- readiness ควรแยกไปเช็กที่ `/readyz`

## 22. จุดที่อาจารย์น่าถาม และวิธีตอบ

### ทำไมต้องมี service layer

เพราะถ้าใส่ logic ทุกอย่างใน router จะยุ่งและดูแลยาก service layer ทำให้

- router บาง
- logic reuse ได้
- test ได้ง่าย
- แยก concern ชัดเจน

### ทำไมต้องใช้ Pydantic schema

เพื่อ validate input และคุม output ให้ปลอดภัยและชัดเจน

### ทำไมต้องมีทั้ง app-level check และ db-level constraint ใน reservation

เพราะ app-level check ช่วยตอบผู้ใช้ได้เร็วและอ่านง่าย แต่ db-level constraint ป้องกัน race condition ได้จริงเวลามี request ชนกันพร้อมกัน

### ทำไมใช้ session-based auth แทน JWT

เพราะระบบนี้เป็น web app ที่หน้า frontend อยู่กับ backend เดียวกัน การใช้ session + CSRF token จัดการง่ายและเหมาะกับ browser flow

### ทำไมต้องมี audit log

เพื่อ trace ว่าใครทำอะไรกับข้อมูลสำคัญ เช่น เปลี่ยน role, สร้างห้อง, คืนอุปกรณ์, อัปเดตงานซ่อม

### ทำไม route บางตัวคืนเฉพาะ Available

เช่น `/labs` และ `/equipments` ตั้งใจใช้สำหรับหน้า self-service ของผู้ใช้ทั่วไป จึงคืนเฉพาะ resource ที่พร้อมใช้งาน

## 23. จุดแข็งของโปรเจกต์นี้

- โครงสร้างแยกชั้นชัดเจน
- มี session auth + CSRF + RBAC
- มี audit log
- มี test ครอบคลุม flow สำคัญหลายจุด
- มี readiness/liveness endpoint แยกกัน
- มี advanced SQL reports ตามโจทย์รายวิชา
- มี UI dashboard ที่เชื่อม backend จริง
- มี fixed-slot reservation ที่ใช้งานง่ายกว่าเดิม

## 24. จุดที่ยังพัฒนาต่อได้

- เพิ่ม endpoint อ่าน notification แล้ว mark as read
- เพิ่ม approval flow สำหรับ reservation
- เพิ่ม CRUD ของ lab types และ equipment categories
- เพิ่ม search/filter ใน UI
- เพิ่ม integration test บน PostgreSQL จริง
- เพิ่ม deployment automation และ CI
- เพิ่ม structured logging และ monitoring

## 25. สรุปสั้นที่สุดสำหรับใช้พูดหน้าห้อง

ระบบนี้เป็น Smart Lab Management System ที่พัฒนาด้วย FastAPI โดยแยกชั้น `router -> service -> model` ชัดเจน ใช้ session-based authentication ร่วมกับ CSRF และ RBAC เพื่อควบคุมความปลอดภัย มีโมดูลหลักคือ user, lab, equipment, reservation, borrowing, maintenance, penalty, notification, audit log และมีรายงาน SQL ขั้นสูงสำหรับโจทย์ฐานข้อมูล ส่วน frontend เป็น dashboard หน้าเดียวที่ดึงข้อมูลจาก API จริงและล่าสุดผมปรับระบบจองห้องให้เป็น fixed time slots 3 รอบเพื่อให้ใช้งานง่ายขึ้นและลดความผิดพลาดจากการกรอกเวลาเอง

## 26. ไฟล์ที่ควรเปิดเวลาถูกถามลึก

- ภาพรวมระบบ: `app/main.py`
- ค่าตั้งค่า: `app/config.py`
- session และ auth: `app/api/deps.py`, `app/api/routers/auth.py`, `app/services/auth_service.py`
- security: `app/security/csrf.py`, `app/security/rbac.py`, `app/security/session.py`, `app/security/hashing.py`
- business logic จองห้อง: `app/services/reservation_service.py`, `app/schemas/reservations.py`
- business logic ยืมอุปกรณ์: `app/services/borrowing_service.py`
- business logic แจ้งซ่อม: `app/services/maintenance_service.py`
- ค่าปรับ: `app/services/penalty_service.py`
- audit log: `app/services/audit_service.py`
- โครงสร้างฐานข้อมูล: `sql/schema.sql`, `migrations/versions/20260409_0001_initial_schema.py`
- frontend: `app/templates/index.html`, `app/static/app.js`, `app/static/style.css`
- tests: `tests/conftest.py`, `tests/test_app.py`
