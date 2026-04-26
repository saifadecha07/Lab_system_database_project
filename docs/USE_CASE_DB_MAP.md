# USE_CASE_DB_MAP — CN230 Lab Management System

> Generated: 2026-04-26  
> Reviewer: Staff-engineer code review pass  
> Covers every router + service file; five-axis review applied (correctness, readability, architecture, security, performance).

---

## 1. Summary Table

| Method | Path | Role Required | Tables Touched | Operations |
|--------|------|---------------|----------------|------------|
| POST | `/auth/register` | Public | `users`, `roles` | SELECT roles, SELECT users (email check), INSERT users |
| POST | `/auth/login` | Public (rate-limited) | `users`, `roles` | SELECT users JOIN roles |
| POST | `/auth/logout` | Public (session optional) | — | Session clear only |
| GET | `/auth/me` | Any authenticated | `users`, `roles` | SELECT users JOIN roles |
| GET | `/users/me` | Any authenticated | `users`, `roles` | SELECT users JOIN roles |
| GET | `/labs` | Public | `labs` | SELECT labs WHERE status='Available' |
| GET | `/equipments` | Public | `equipments` | SELECT equipments WHERE status='Available' |
| GET | `/reservations/my` | Any authenticated | `lab_reservations` | SELECT WHERE reserved_by=me |
| GET | `/reservations` | Staff, Admin | `lab_reservations` | SELECT all ORDER BY start_time |
| GET | `/reservations/availability` | Any authenticated | `labs`, `lab_reservations` | SELECT all labs + SELECT all Pending/Approved reservations |
| POST | `/reservations` | Any authenticated | `labs`, `lab_reservations` | SELECT lab, SELECT overlap check, INSERT reservation |
| POST | `/reservations/{id}/cancel` | Any authenticated (owner only) | `lab_reservations` | SELECT, UPDATE status='Cancelled' |
| PATCH | `/reservations/{id}` | Admin | `lab_reservations` | SELECT, UPDATE status |
| DELETE | `/reservations/{id}` | Admin | `lab_reservations` | SELECT, DELETE |
| GET | `/borrowings/my` | Any authenticated | `equipment_borrowings` | SELECT WHERE user_id=me |
| GET | `/borrowings` | Staff, Admin | `equipment_borrowings` | SELECT (optional status filter), ORDER BY borrow_time |
| POST | `/borrowings` | Staff, Admin | `users`, `equipments`, `equipment_borrowings`, `audit_logs` | SELECT user, SELECT+LOCK equipment, SELECT active borrow check, SELECT maintenance check, INSERT borrowing, UPDATE equipment.status, INSERT audit_log |
| PATCH | `/borrowings/{id}/return` | Staff, Admin | `equipment_borrowings`, `equipments`, `penalties`, `notifications`, `audit_logs` | SELECT borrowing, SELECT+LOCK equipment, UPDATE borrowing, UPDATE equipment.status, INSERT penalty (cond.), INSERT notification (cond.), INSERT audit_log |
| GET | `/maintenance/queue` | Technician, Admin | `maintenance_records` | SELECT all |
| POST | `/maintenance` | Any authenticated | `equipments`, `maintenance_records`, `audit_logs` | SELECT+LOCK equipment, INSERT record, UPDATE equipment.status, INSERT audit_log |
| PATCH | `/maintenance/{id}` | Technician, Admin | `maintenance_records`, `equipments`, `notifications`, `audit_logs` | SELECT record, SELECT+LOCK equipment, UPDATE record, UPDATE equipment.status, INSERT notification (cond.), INSERT audit_log |
| GET | `/penalties/my` | Any authenticated | `penalties` | SELECT WHERE user_id=me |
| GET | `/notifications/my` | Any authenticated | `notifications` | SELECT WHERE user_id=me |
| PATCH | `/notifications/{id}` | Any authenticated (owner only) | `notifications` | SELECT (owner-filtered), UPDATE is_read |
| GET | `/staff/users` | Staff, Admin | `users`, `roles` | SELECT users JOIN roles |
| GET | `/staff/reports/summary` | Staff, Admin | `users`, `labs`, `equipments`, `equipment_borrowings`, `maintenance_records` | 5x COUNT queries |
| GET | `/admin/users` | Admin | `users`, `roles` | SELECT users JOIN roles |
| GET | `/admin/roles` | Admin | `roles` | SELECT all |
| GET | `/admin/labs` | Admin | `labs` | SELECT all |
| POST | `/admin/labs` | Admin | `labs`, `audit_logs` | INSERT lab, INSERT audit_log |
| PATCH | `/admin/labs/{id}` | Admin | `labs`, `audit_logs` | SELECT, UPDATE lab (full replace), INSERT audit_log |
| DELETE | `/admin/labs/{id}` | Admin | `labs`, `audit_logs` | SELECT, lazy-load check reservations+equipments, INSERT audit_log, DELETE lab |
| GET | `/admin/equipments` | Admin | `equipments` | SELECT all |
| POST | `/admin/equipments` | Admin | `labs`, `equipment_categories`, `equipments`, `audit_logs` | SELECT lab (cond.), SELECT category (cond.), INSERT equipment, INSERT audit_log |
| PATCH | `/admin/equipments/{id}` | Admin | `equipments`, `labs`, `equipment_categories`, `audit_logs` | SELECT equipment, SELECT lab (cond.), SELECT category (cond.), UPDATE equipment (full replace), INSERT audit_log |
| DELETE | `/admin/equipments/{id}` | Admin | `equipments`, `audit_logs` | SELECT, lazy-load check borrowings, INSERT audit_log, DELETE equipment |
| PATCH | `/admin/users/{id}/role` | Admin | `users`, `roles`, `audit_logs` | SELECT user JOIN role, SELECT role, UPDATE user.role_id, INSERT audit_log |
| PATCH | `/admin/users/{id}/status` | Admin | `users`, `audit_logs` | SELECT user JOIN role, UPDATE user.is_active, INSERT audit_log |
| GET | `/admin/audit-logs` | Admin | `audit_logs` | SELECT ORDER BY created_at DESC LIMIT (1–500) |
| GET | `/reports/late-borrowings` | Staff, Admin | `equipment_borrowings`, `users`, `equipments`, `labs`, `penalties` | Raw SQL: 5-table JOIN, WHERE late condition |
| GET | `/reports/top-borrowers` | Staff, Admin | `users`, `roles`, `equipment_borrowings`, `penalties` | Raw SQL: GROUP BY + HAVING + SUM |
| GET | `/reports/lab-utilization` | Staff, Admin | `labs`, `lab_types`, `lab_reservations`, `equipments` | Raw SQL: GROUP BY + conditional COUNT |
| GET | `/reports/equipment-repairs` | Staff, Admin | `equipments`, `equipment_categories`, `labs`, `maintenance_records` | Raw SQL: GROUP BY + MAX + conditional COUNT |
| GET | `/reports/reservation-summary` | Staff, Admin | `lab_reservations`, `labs`, `users`, `reservation_participants` | Raw SQL: GROUP BY + COUNT + EXTRACT |

---

## 2. Per-Endpoint Detail

---

### Router: auth (`/auth`)

#### `POST /auth/register`
ผู้ใช้ใหม่สมัครบัญชี ได้รับ role "Student" อัตโนมัติ

**DB Operations:**
1. `SELECT roles WHERE role_name='Student'` — ดึง Student role
2. `SELECT users WHERE email=?` — เช็ค email ซ้ำ
3. `INSERT INTO users (role_id, email, first_name, last_name, password_hash, is_active)` — สร้าง user
4. `db.commit()` + `db.refresh(user)`

**Side effects:** ไม่มี notification / audit log

**Bugs:**
- **[Warning]** ไม่มี audit log สำหรับการสมัครสมาชิก — ไม่มีหลักฐานว่าใครสมัครเมื่อไหร่
- **[Nit]** `register` endpoint ใน `auth.py` hardcode `role_name="Student"` ใน response แทนที่จะอ่านจาก `user.role.role_name` จริง — ถ้า `get_or_create_default_student_role` เปลี่ยน role object ไป response ยังส่งคำว่า "Student" อยู่ดี (ปัจจุบันไม่เป็นปัญหา แต่เป็น inconsistency กับ endpoint อื่น)

---

#### `POST /auth/login`
ผู้ใช้ log in ด้วย email + password; ตั้ง server-side session

**DB Operations:**
1. `SELECT users JOIN roles WHERE email=?` — `joinedload(User.role)` — ดึง user พร้อม role
2. ตรวจ password hash
3. ถ้าผ่าน: `start_user_session` เขียน `user_id` + `csrf_token` ลง session (ไม่มี DB write)

**Side effects:** Rate-limited ด้วย `settings.rate_limit_login`

**Bugs:**
- **[Warning]** `authenticate_user` ไม่กรอง `is_active=True` ตอน query — query ดึง user มาก่อน แล้วเช็ค `is_active` ทีหลัง ถ้า attacker รู้ email อาจได้ message "Inactive account" (HTTP 403) แทน "Invalid email or password" (HTTP 401) ซึ่ง **leak ข้อมูลว่าบัญชีนั้นมีอยู่จริง** (user enumeration via status code)
- **[Nit]** CSRF token ถูกสร้างตอน login แต่ไม่มีการ validate token นี้ใน mutating endpoint อื่น ๆ เลย — CSRF protection ไม่ถูกใช้จริง

---

#### `POST /auth/logout`
ลบ session และ cookie

**DB Operations:** ไม่มี — `request.session.clear()` + `response.delete_cookie()`

**Bugs:**
- **[Nit]** Endpoint ไม่ต้อง authenticate — ถ้า session ไม่มีอยู่ก็ return 200 ปกติ (acceptable UX)

---

#### `GET /auth/me`
ดูข้อมูล profile ของตัวเอง

**DB Operations:**
1. `get_current_user` → `SELECT users JOIN roles WHERE user_id=? AND is_active=True` (joinedload role)

**Bugs:**
- **[Nit]** `/auth/me` และ `/users/me` ทำสิ่งเดียวกันทุกประการ — เป็น **duplicate endpoint** ควรลบออกอันใดอันหนึ่ง

---

### Router: users (`/users`)

#### `GET /users/me`
เหมือน `/auth/me` ทุกประการ — duplicate (ดู bug ข้างบน)

---

### Router: labs (`/labs`)

#### `GET /labs`
ดูรายการ lab ที่สถานะ Available (public, ไม่ต้อง login)

**DB Operations:**
1. `SELECT labs WHERE status='Available'`

**Bugs:**
- **[Warning]** ไม่มี pagination — ถ้า labs มีจำนวนมากจะ return ทั้งหมด
- **[Warning]** Public endpoint ไม่ต้อง authentication — ข้อมูล lab name, capacity เป็น public ซึ่งอาจ acceptable แต่ควรมีการ document การตัดสินใจนี้ชัดเจน
- **[Nit]** ไม่มี ordering — ผลลัพธ์อาจไม่ deterministic

---

### Router: equipments (`/equipments`)

#### `GET /equipments`
ดูรายการ equipment ที่สถานะ Available (public, ไม่ต้อง login)

**DB Operations:**
1. `SELECT equipments WHERE status='Available'`

**Bugs:**
- **[Warning]** Public endpoint เหมือน labs — ไม่ต้อง auth
- **[Warning]** ไม่มี pagination
- **[Nit]** ไม่มี ordering

---

### Router: reservations (`/reservations`)

#### `GET /reservations/my`
ดูการจอง lab ของตัวเอง

**DB Operations:**
1. `SELECT lab_reservations WHERE reserved_by=current_user.user_id`

**Bugs:**
- **[Warning]** ไม่มี pagination — user ที่จองมาก อาจได้ข้อมูลเยอะมาก
- **[Nit]** ไม่มี ordering

---

#### `GET /reservations`
Staff/Admin ดูการจองทั้งหมด

**DB Operations:**
1. `SELECT lab_reservations ORDER BY start_time DESC`

**Bugs:**
- **[Warning]** ไม่มี pagination — table ใหญ่ขึ้นเรื่อย ๆ

---

#### `GET /reservations/availability`
ดูช่องว่างการจองของทุก lab ในวันที่กำหนด

**DB Operations:**
1. `SELECT labs ORDER BY room_name` — ดึง lab ทั้งหมด (ไม่กรอง status)
2. `SELECT lab_reservations WHERE status IN ('Pending','Approved')` — ดึง **ทุก reservation ที่ยังไม่ยกเลิก** (ไม่กรองวันที่ใน query)
3. Python in-memory grouping + slot matching

**Bugs:**
- **[Critical]** `get_reservation_availability` ดึง **ทุก reservation** ออกมาก่อนแล้วกรองใน Python — ถ้า reservation table มีแสนแถว จะโหลดทั้งหมดเข้า memory ทุกครั้ง **N+1 ระดับ table scan** ควรเพิ่ม `WHERE date(start_time) = :booking_date` ใน query
- **[Warning]** Fetches ALL labs รวมถึงที่ status ไม่ใช่ Available — slot แสดงว่า available จากตรรกะ `lab.status == "Available"` แต่ lab ที่ status อื่นยังโชว์ใน response พร้อม slots ทั้งหมด ซึ่งอาจ confuse frontend

---

#### `POST /reservations`
สร้างการจอง lab

**DB Operations:**
1. `SELECT labs WHERE lab_id=? AND status='Available'` — ตรวจ lab
2. `SELECT lab_reservations WHERE lab_id=? AND status IN ('Pending','Approved') AND overlap` — ตรวจ conflict
3. `INSERT INTO lab_reservations` — สร้าง reservation (status='Approved' ทันที)
4. `db.commit()` พร้อม `IntegrityError` catch

**Side effects:** ไม่มี notification/audit log

**Bugs:**
- **[Critical]** **Race condition** — overlap check (query 2) และ INSERT (query 3) ไม่ได้ใช้ `SELECT ... FOR UPDATE` หรือ DB-level unique constraint — ในสภาพ concurrent สูง user 2 คนอาจจองเวลาเดียวกันพร้อมกันได้ `IntegrityError` catch จะช่วยได้ก็ต่อเมื่อมี unique constraint จริงใน DB ซึ่งไม่เห็นใน model definition
- **[Warning]** ทุก reservation ถูก set status='Approved' ทันที — ไม่มี workflow "Pending → Approved" แม้ว่า schema รองรับ status นั้น (ซ้ำใน PATCH endpoint ที่ Admin เปลี่ยน status ได้) ทำให้ workflow ไม่ชัดเจน
- **[Warning]** ไม่มี audit log และไม่มี notification ให้เจ้าของ reservation — ต่างจาก borrowing/maintenance ที่มี
- **[Warning]** ไม่ validate ว่า `end_time > start_time` — reservation ที่ end <= start จะผ่านเข้า DB ได้
- **[Nit]** `cancel_reservation` ไม่กรองว่า reservation ต้องไม่ Cancelled อยู่แล้ว — สามารถ cancel ซ้ำได้ (idempotent แต่ไม่ explicit)

---

#### `POST /reservations/{id}/cancel`
ยกเลิกการจอง (เจ้าของเท่านั้น)

**DB Operations:**
1. `SELECT lab_reservations WHERE reservation_id=?`
2. ตรวจว่า `reserved_by == current_user.user_id`
3. `UPDATE lab_reservations SET status='Cancelled'`

**Bugs:**
- **[Warning]** ไม่มี audit log
- **[Nit]** ไม่เช็คว่า reservation อยู่ในสถานะที่ cancel ได้ (เช่น ไม่ควร cancel ถ้า Cancelled ไปแล้ว)

---

#### `PATCH /reservations/{id}`
Admin เปลี่ยน status reservation

**DB Operations:**
1. `SELECT lab_reservations WHERE reservation_id=?`
2. `UPDATE lab_reservations SET status=?`

**Bugs:**
- **[Warning]** ไม่ validate ว่า status value ที่ส่งมาถูกต้อง (ควรเป็น enum เช่น Pending/Approved/Cancelled) — ถ้า schema ไม่ enforce อาจใส่ค่า arbitrary ได้
- **[Warning]** ไม่มี audit log

---

#### `DELETE /reservations/{id}`
Admin ลบ reservation

**DB Operations:**
1. `SELECT lab_reservations WHERE reservation_id=?`
2. `DELETE FROM lab_reservations`

**Bugs:**
- **[Warning]** ไม่มี audit log — การลบ reservation ควรมีหลักฐาน
- **[Warning]** ไม่เช็ค cascading effect — ถ้ามี `reservation_participants` FK ไปยัง reservation นี้ จะเกิด FK violation หรือ cascade delete โดยไม่ตั้งใจ (ขึ้นอยู่กับ DB cascade setting ที่ไม่เห็นใน model)

---

### Router: borrowings (`/borrowings`)

#### `GET /borrowings/my`
ดูรายการยืมของตัวเอง

**DB Operations:**
1. `SELECT equipment_borrowings WHERE user_id=current_user.user_id`

**Bugs:**
- **[Warning]** ไม่มี pagination
- **[Nit]** ไม่มี ordering

---

#### `GET /borrowings`
Staff/Admin ดูรายการยืมทั้งหมด (กรอง status ได้)

**DB Operations:**
1. `SELECT equipment_borrowings [WHERE status=?] ORDER BY borrow_time DESC`

**Bugs:**
- **[Warning]** ไม่มี pagination — อาจ return แถวจำนวนมาก
- **[Warning]** `status_filter` เป็น free-text string ไม่มีการ validate ว่าต้องเป็น enum ที่รู้จัก — query จะ return empty list โดยเงียบถ้าพิมพ์ผิด

---

#### `POST /borrowings`
Staff/Admin สร้างรายการยืม equipment

**DB Operations (ใน `create_borrowing`):**
1. `SELECT users WHERE user_id=? AND is_active=True` — ตรวจ borrower
2. `SELECT equipments WHERE equipment_id=? FOR UPDATE` — lock equipment row
3. `SELECT equipment_borrowings WHERE equipment_id=? AND status='Borrowed'` — `has_active_borrowing`
4. `SELECT maintenance_records WHERE equipment_id=? AND status!='Fixed'` — `has_open_maintenance`
5. `INSERT INTO equipment_borrowings` + `db.flush()`
6. `resolve_equipment_status` → queries 3+4 อีกครั้ง (ดู bug)
7. `UPDATE equipments SET status=?`
8. `INSERT INTO audit_logs` + `db.flush()`
9. `db.commit()`

**Side effects:** INSERT audit_log

**Bugs:**
- **[Critical]** **Double query / redundant check** — `has_active_borrowing` และ `has_open_maintenance` ถูกเรียกในขั้นตอน validation (query 3+4) แล้วถูกเรียกอีกครั้งใน `resolve_equipment_status` (query 6) ซึ่งเรียก `has_active_borrowing` + `has_open_maintenance` อีกรอบ รวมเป็น 4 query เพิ่มเติมที่ซ้ำซ้อน ระหว่าง flush และ resolve, borrowing row ยังไม่ commit จึง `has_active_borrowing` ใน resolve อาจไม่เห็น row ใหม่ในบาง isolation level — status อาจถูกตั้งเป็น "Available" แทน "Borrowed" (**logic bug**)
- **[Warning]** Actor (`actor_user_id`) คือ staff ที่กดยืม ไม่ใช่ borrower — ซึ่งถูกต้อง แต่ควร document ใน code comment

---

#### `PATCH /borrowings/{id}/return`
Staff/Admin บันทึกการคืน equipment

**DB Operations (ใน `mark_equipment_returned`):**
1. `SELECT equipment_borrowings WHERE borrow_id=?`
2. `SELECT equipments WHERE equipment_id=? FOR UPDATE`
3. `UPDATE equipment_borrowings SET actual_return=NOW(), status='Returned'`
4. `resolve_equipment_status` → `has_active_borrowing` + `has_open_maintenance` (2 queries)
5. `UPDATE equipments SET status=?`
6. `build_penalty` — คำนวณค่าปรับ (pure Python)
7. ถ้ามีค่าปรับ: `INSERT INTO penalties` + `db.flush()`
8. ถ้ามีค่าปรับ: `INSERT INTO notifications` + `db.flush()`
9. `INSERT INTO audit_logs` + `db.flush()`
10. `db.commit()`

**Side effects:** INSERT penalty (conditional), INSERT notification (conditional), INSERT audit_log

**Bugs:**
- **[Warning]** `resolve_equipment_status` เรียก `has_active_borrowing` หลังจาก set `borrowing.status='Returned'` แล้ว แต่ยังไม่ commit — เนื่องจาก SQLAlchemy flush-before-query อาจทำให้เห็น updated state ใน session เดียวกัน แต่พฤติกรรมนี้ขึ้นอยู่กับ `autoflush` setting — ควร explicit และไม่ควรพึ่ง implicit flush behavior
- **[Nit]** `calculate_penalty_amount` ใช้ ceiling แบบ manual `(late_seconds + 3599) // 3600` — ควรใช้ `math.ceil` เพื่อ readability

---

### Router: maintenance (`/maintenance`)

#### `GET /maintenance/queue`
Technician/Admin ดูรายการซ่อมทั้งหมด

**DB Operations:**
1. `SELECT maintenance_records` — ดึงทั้งหมดไม่มีกรอง

**Bugs:**
- **[Warning]** ดึง **ทุก record** รวมถึงที่ Fixed ไปแล้ว — ชื่อ endpoint คือ "queue" ซึ่ง imply งานที่ยังค้างอยู่ แต่ return ทุก status ควรกรอง `WHERE status != 'Fixed'` หรือรองรับ filter parameter
- **[Warning]** ไม่มี pagination

---

#### `POST /maintenance`
ทุกคน (ต้อง login) รายงานปัญหา equipment

**DB Operations (ใน `create_maintenance_report`):**
1. `SELECT equipments WHERE equipment_id=? FOR UPDATE` — lock equipment
2. `INSERT INTO maintenance_records` + `db.flush()`
3. `resolve_equipment_status` → `has_active_borrowing` + `has_open_maintenance` (2 queries)
4. `UPDATE equipments SET status=?`
5. `INSERT INTO audit_logs` + `db.flush()`
6. `db.commit()`

**Side effects:** UPDATE equipment.status, INSERT audit_log

**Bugs:**
- **[Warning]** ไม่ตรวจว่า equipment อยู่ในสถานะที่ report ได้ — สามารถ report equipment ที่ status='Borrowed' หรือ 'In Repair' ได้อีก ทำให้ maintenance queue บวม
- **[Warning]** `resolve_equipment_status` เรียกหลัง flush แต่ก่อน commit — ดูปัญหาเดียวกับ create_borrowing ข้างบน

---

#### `PATCH /maintenance/{id}`
Technician/Admin อัปเดตสถานะการซ่อม

**DB Operations (ใน `update_maintenance_status`):**
1. `SELECT maintenance_records WHERE repair_id=?`
2. `SELECT equipments WHERE equipment_id=? FOR UPDATE`
3. `UPDATE maintenance_records SET technician_id=?, status=?, resolved_date=?`
4. ถ้า status='Fixed': `INSERT INTO notifications` + `db.flush()`
5. `resolve_equipment_status` → 2 queries
6. `UPDATE equipments SET status=?`
7. `INSERT INTO audit_logs` + `db.flush()`
8. `db.commit()`

**Side effects:** UPDATE equipment.status, INSERT notification (if Fixed), INSERT audit_log

**Bugs:**
- **[Warning]** ไม่ validate ว่า `new_status` เป็น enum ที่รู้จัก — ถ้า schema ไม่ enforce อาจใส่ค่า arbitrary ได้
- **[Warning]** ทุก PATCH จะ overwrite `technician_id` ด้วย caller — ถ้า Admin แก้ status จะกลายเป็น technician ด้วย ซึ่งอาจไม่ตรงตาม business logic

---

### Router: penalties (`/penalties`)

#### `GET /penalties/my`
ดูค่าปรับของตัวเอง

**DB Operations:**
1. `SELECT penalties WHERE user_id=current_user.user_id`

**Bugs:**
- **[Nit]** ไม่มี ordering — ควร `ORDER BY created_at DESC`
- **[Nit]** ไม่มี endpoint สำหรับ Staff/Admin ดูค่าปรับทั้งหมด — มีแค่ใน reports

---

### Router: notifications (`/notifications`)

#### `GET /notifications/my`
ดู notification ของตัวเอง

**DB Operations:**
1. `SELECT notifications WHERE user_id=current_user.user_id`

**Bugs:**
- **[Warning]** ไม่มี pagination — notification สะสมได้เรื่อย ๆ
- **[Nit]** ไม่มี ordering — ควร `ORDER BY created_at DESC`

---

#### `PATCH /notifications/{id}`
Mark notification ว่าอ่านแล้ว (เจ้าของเท่านั้น)

**DB Operations:**
1. `SELECT notifications WHERE notification_id=? AND user_id=current_user.user_id`
2. `UPDATE notifications SET is_read=?`

**Bugs:**
- **[Nit]** `payload.is_read` ถูก set ตรง ๆ — user อาจ mark notification ว่า unread ได้ด้วย (ไม่แน่ใจว่าต้องการหรือเปล่า)

---

### Router: staff (`/staff`)

#### `GET /staff/users`
Staff/Admin ดูรายชื่อ user ทั้งหมด

**DB Operations:**
1. `SELECT users JOIN roles (joinedload) ORDER BY created_at DESC`

**Bugs:**
- **[Warning]** ไม่มี pagination — อาจ return user ทั้งหมดในระบบ
- **[Warning]** ส่ง `email`, `is_active`, `role_name` ของทุก user — ข้อมูล PII ทั้งหมดถูก expose แก่ทุก Staff (ไม่ใช่แค่ Admin)

---

#### `GET /staff/reports/summary`
ดู dashboard summary

**DB Operations:**
1. `SELECT COUNT(*) FROM users`
2. `SELECT COUNT(*) FROM labs`
3. `SELECT COUNT(*) FROM equipments`
4. `SELECT COUNT(*) FROM equipment_borrowings WHERE status='Borrowed'`
5. `SELECT COUNT(*) FROM maintenance_records WHERE status!='Fixed'`

**Bugs:**
- **[Warning]** 5 query แยกกัน — สามารถรวมเป็น single query ด้วย subquery ได้ (minor performance concern ถ้า traffic ต่ำ)

---

### Router: admin (`/admin`)

#### `GET /admin/users`
เหมือน `/staff/users` แต่จำกัด Admin เท่านั้น

**DB Operations:** เหมือน `GET /staff/users`

**Bugs:**
- **[Warning]** **Duplicate endpoint** กับ `/staff/users` — logic เหมือนกันทุกประการ ควร refactor เป็น shared function

---

#### `GET /admin/roles`
ดูรายการ role ทั้งหมด

**DB Operations:**
1. `SELECT roles ORDER BY role_name`

**Bugs:** ไม่มี

---

#### `GET /admin/labs`
Admin ดูรายการ lab ทั้งหมด (ไม่กรอง status)

**DB Operations:**
1. `SELECT labs ORDER BY room_name`

**Bugs:** ไม่มี

---

#### `POST /admin/labs`
Admin สร้าง lab ใหม่

**DB Operations:**
1. `INSERT INTO labs` + `db.flush()`
2. `INSERT INTO audit_logs` + `db.flush()`
3. `db.commit()`

**Bugs:**
- **[Warning]** `lab_type_id` ไม่ถูกรับจาก payload — Lab model มี `lab_type_id` แต่ `LabCreateRequest` ไม่ส่งค่านี้ไป ทุก lab ที่สร้างผ่าน API จะมี `lab_type_id=NULL`

---

#### `PATCH /admin/labs/{id}`
Admin แก้ไข lab

**DB Operations:**
1. `SELECT labs WHERE lab_id=?`
2. `UPDATE labs SET room_name=?, capacity=?, status=?`
3. `INSERT INTO audit_logs`

**Bugs:**
- **[Warning]** **Full replace** — PATCH ควรเป็น partial update แต่นี่ overwrite ทุก field แม้ payload ไม่ได้ส่งมา ถ้า `LabUpdateRequest` ไม่ใช้ `Optional` fields จะบังคับให้ส่งทุก field
- **[Warning]** `lab_type_id` ไม่ถูก update เช่นเดียวกับ POST

---

#### `DELETE /admin/labs/{id}`
Admin ลบ lab

**DB Operations:**
1. `SELECT labs WHERE lab_id=?`
2. Access `lab.reservations` และ `lab.equipments` — **lazy load** 2 queries (N+1 risk ถ้า called in loop)
3. `INSERT INTO audit_logs` + `db.flush()`
4. `DELETE FROM labs`
5. `db.commit()`

**Bugs:**
- **[Warning]** Lazy load `lab.reservations` และ `lab.equipments` ทำให้เกิด 2 extra query — ควรใช้ joinedload หรือ subquery count แทน

---

#### `POST /admin/equipments`
Admin สร้าง equipment

**DB Operations:**
1. `SELECT labs WHERE lab_id=?` (ถ้า lab_id ระบุ)
2. `SELECT equipment_categories WHERE category_id=?` (ถ้า category_id ระบุ)
3. `INSERT INTO equipments` + `db.flush()`
4. `INSERT INTO audit_logs` + `db.flush()`
5. `db.commit()`

**Bugs:**
- **[Nit]** ไม่มีการ validate ว่า lab status='Available' ก่อนนำ equipment ไปวางใน lab

---

#### `PATCH /admin/equipments/{id}`
Admin แก้ไข equipment

**DB Operations:**
1. `SELECT equipments WHERE equipment_id=?`
2. `SELECT labs WHERE lab_id=?` (ถ้า lab_id ระบุ)
3. `SELECT equipment_categories WHERE category_id=?` (ถ้า category_id ระบุ)
4. `UPDATE equipments` (full replace)
5. `INSERT INTO audit_logs`

**Bugs:**
- **[Critical]** Admin สามารถ force-set `equipment.status` เป็นค่าใดก็ได้ผ่าน `payload.status` — ถ้า equipment กำลัง borrowed อยู่และ Admin เปลี่ยน status เป็น 'Available' จะทำให้ `equipment_state_service` และ state จริงใน DB ไม่ sync กัน — ควรใช้ `resolve_equipment_status` หรือห้าม override status โดยตรง
- **[Warning]** Full replace ทุก field เหมือน PATCH labs

---

#### `DELETE /admin/equipments/{id}`
Admin ลบ equipment

**DB Operations:**
1. `SELECT equipments WHERE equipment_id=?`
2. Access `equipment.borrowings` — **lazy load** 1 query
3. `INSERT INTO audit_logs` + `db.flush()`
4. `DELETE FROM equipments`
5. `db.commit()`

**Bugs:**
- **[Warning]** ตรวจแค่ `borrowings` แต่ไม่ตรวจ `maintenance_records` — ลบ equipment ที่มี maintenance history ได้ (FK จะ fail ถ้า constraint มี แต่ถ้าไม่มีจะ orphan records)

---

#### `PATCH /admin/users/{id}/role`
Admin เปลี่ยน role ของ user

**DB Operations:**
1. `SELECT users JOIN roles WHERE user_id=?`
2. `SELECT roles WHERE role_name=?`
3. `UPDATE users SET role_id=?`
4. `INSERT INTO audit_logs`

**Bugs:**
- **[Warning]** Admin สามารถเปลี่ยน role ตัวเองได้ — ไม่มีการป้องกัน self-demotion หรือ self-promotion

---

#### `PATCH /admin/users/{id}/status`
Admin เปิด/ปิดบัญชี user

**DB Operations:**
1. `SELECT users JOIN roles WHERE user_id=?`
2. `UPDATE users SET is_active=?`
3. `INSERT INTO audit_logs`

**Bugs:**
- **[Warning]** Admin สามารถปิดบัญชีตัวเองได้ — ไม่มีการป้องกัน
- **[Warning]** ปิดบัญชี user แต่ session ที่ active อยู่ของ user นั้นยังใช้งานได้ — `get_current_user` กรอง `is_active=True` จริง แต่ session ที่มีอยู่จะไม่ถูก invalidate ทันที (acceptable ถ้า session TTL สั้น)

---

#### `GET /admin/audit-logs`
Admin ดู audit log

**DB Operations:**
1. `SELECT audit_logs ORDER BY created_at DESC LIMIT :limit`

**Bugs:**
- **[Nit]** Default limit=100, max=500 — ดี แต่ไม่มี offset/cursor pagination ทำให้ดูเฉพาะ 500 รายการล่าสุดได้เท่านั้น

---

### Router: reports (`/reports`)

> ทุก endpoint ใน router นี้ใช้ raw SQL (`text(...)`) ผ่าน SQLAlchemy

#### `GET /reports/late-borrowings`
รายงาน Q1: การยืมที่เลยกำหนดคืน

**DB Operations (raw SQL):**
```sql
SELECT ... FROM equipment_borrowings eb
JOIN users u ON u.user_id = eb.user_id
JOIN equipments e ON e.equipment_id = eb.equipment_id
LEFT JOIN labs l ON l.lab_id = e.lab_id
LEFT JOIN penalties p ON p.borrow_id = eb.borrow_id
WHERE eb.actual_return > eb.expected_return
   OR (eb.actual_return IS NULL AND eb.expected_return < NOW())
ORDER BY eb.expected_return ASC
```

**Bugs:**
- **[Warning]** ไม่มี pagination — ถ้ามี borrowing ที่ late จำนวนมากจะ return ทั้งหมด

---

#### `GET /reports/top-borrowers`
รายงาน Q2: user ที่ยืมมากที่สุดและค่าปรับรวม

**DB Operations (raw SQL):**
4-table JOIN + GROUP BY + HAVING COUNT > 0 + SUM(fine_amount)

**Bugs:**
- **[Warning]** ไม่มี pagination
- **[Nit]** `HAVING COUNT(DISTINCT eb.borrow_id) > 0` ทำให้ user ที่ไม่เคยยืมถูกกรองออก — แต่ `LEFT JOIN equipment_borrowings` ทำให้ `COUNT(DISTINCT eb.borrow_id)` อาจเป็น 0 ซึ่งถูกต้อง

---

#### `GET /reports/lab-utilization`
รายงาน Q3: การใช้งาน lab

**DB Operations (raw SQL):**
4-table JOIN + GROUP BY + conditional COUNT

**Bugs:**
- **[Warning]** ไม่มี pagination

---

#### `GET /reports/equipment-repairs`
รายงาน Q4: ความถี่ในการซ่อม equipment

**DB Operations (raw SQL):**
4-table JOIN + GROUP BY + MAX + conditional COUNT

**Bugs:**
- **[Warning]** ไม่มี pagination

---

#### `GET /reports/reservation-summary`
รายงาน Q5: รายละเอียด reservation พร้อมจำนวน participant

**DB Operations (raw SQL):**
4-table JOIN + GROUP BY + EXTRACT(EPOCH)

**Bugs:**
- **[Warning]** ไม่มี pagination

---

## 3. Bug Summary (Sorted by Severity)

### Critical

| # | Location | Description |
|---|----------|-------------|
| C1 | `reservation_service.py:create_reservation` | **Race condition**: overlap check และ INSERT ไม่มี row-level lock (`SELECT FOR UPDATE`) และไม่มี DB unique constraint — concurrent request อาจจองเวลาเดียวกันได้ |
| C2 | `admin.py:update_equipment` | Admin สามารถ force-set `equipment.status` เป็นค่าใดก็ได้ ทำให้ state desync กับ `equipment_state_service` — equipment ที่ถูกยืมอยู่อาจถูก mark เป็น Available |
| C3 | `borrowing_service.py:create_borrowing` | `resolve_equipment_status` หลัง flush อาจ return ผิดใน isolation level บางค่า เพราะ `has_active_borrowing` ยังไม่เห็น row ที่เพิ่ง insert แต่ยังไม่ commit — equipment status อาจถูกตั้งเป็น 'Available' แทน 'Borrowed' |

### Warning

| # | Location | Description |
|---|----------|-------------|
| W1 | `auth_service.py:authenticate_user` | User enumeration: inactive account return HTTP 403, invalid credential return HTTP 401 — attacker รู้ว่าบัญชีนั้นมีอยู่จริง |
| W2 | `reservation_service.py:get_reservation_availability` | Full table scan: ดึง reservation ทั้งหมดโดยไม่กรองวันที่ใน SQL — memory และ query time scale กับขนาด table |
| W3 | `reservations.py:create` | ไม่ validate `end_time > start_time` — reservation ที่ invalid เข้า DB ได้ |
| W4 | `reservations.py:update_reservation` | ไม่ validate status enum — arbitrary string ถูก save ลง DB ได้ |
| W5 | `reservations.py:delete_reservation` | ไม่ตรวจ cascade `reservation_participants` — อาจเกิด orphan records หรือ FK violation |
| W6 | `reservations.py` (POST, cancel, PATCH, DELETE) | ไม่มี audit log สำหรับ reservation lifecycle ทั้งหมด |
| W7 | `maintenance.py:create` | ไม่ตรวจ equipment status ก่อน report — สามารถ report equipment ที่อยู่ระหว่าง repair อีกครั้งได้ |
| W8 | `maintenance.py:update_status` | `new_status` ไม่มี enum validation — arbitrary string ถูก save ลง DB ได้ |
| W9 | `maintenance.py:update_status` | PATCH ทับ `technician_id` ด้วย caller เสมอ — Admin แก้ status กลายเป็น technician โดยไม่ตั้งใจ |
| W10 | `maintenance.py:list_queue` | Return ทุก record รวมถึงที่ Fixed — ชื่อ "queue" แต่ไม่กรอง status |
| W11 | `borrowings.py:list_borrowings` | `status_filter` เป็น free-text ไม่มี validation — typo ทำให้ return empty list โดยเงียบ |
| W12 | `admin.py:create_lab` + `update_lab` | `lab_type_id` ไม่ถูก handle ใน API — ทุก lab ที่สร้างผ่าน API มี `lab_type_id=NULL` |
| W13 | `admin.py:delete_equipment` | ไม่ตรวจ `maintenance_records` FK — ลบ equipment ที่มี maintenance history ได้ |
| W14 | `admin.py:change_user_role` + `change_user_status` | Admin สามารถเปลี่ยน role/status ตัวเองได้ ทำให้ Admin lock ตัวเองออกจากระบบได้ |
| W15 | `staff.py:list_users` + `admin.py:list_users` | **Duplicate endpoint** — logic ซ้ำกันทั้งหมด ควร refactor |
| W16 | ทุก list endpoint | ไม่มี pagination ทุก endpoint ที่ return list ไม่มี `limit`/`offset` หรือ cursor-based pagination |
| W17 | `labs.py`, `equipments.py` | Public endpoints (ไม่ต้อง auth) ที่ expose ข้อมูล inventory — อาจ acceptable แต่ไม่มี documentation การตัดสินใจ |

### Nit

| # | Location | Description |
|---|----------|-------------|
| N1 | `auth.py:register` | Hardcode `role_name="Student"` ใน response แทนอ่านจาก object จริง |
| N2 | `auth.py:me` + `users.py:me` | Duplicate endpoint — ควรลบออกอันหนึ่ง |
| N3 | `session.py` | CSRF token ถูกสร้างแต่ไม่มีการ validate ใน mutating endpoint ใด ๆ |
| N4 | `reservations.py:cancel` | ไม่เช็คว่า reservation ไม่ใช่ Cancelled อยู่แล้ว |
| N5 | `penalty_service.py` | `calculate_penalty_amount` ใช้ manual ceiling แทน `math.ceil` |
| N6 | `notifications.py`, `penalties.py`, `borrowings.py/my`, `reservations.py/my` | ไม่มี `ORDER BY` — ผลลัพธ์ไม่ deterministic |
| N7 | `admin.py:list_audit_logs` | ไม่มี offset/cursor — ดูได้เฉพาะ 500 รายการล่าสุด |
| N8 | `borrowing_service.py` | `create_borrowing` และ `mark_equipment_returned` เรียก `has_active_borrowing` + `has_open_maintenance` ซ้ำซ้อนใน validation และ resolve phases |

---

## 4. Schema Reference

| Model | Table | Key Columns |
|-------|-------|-------------|
| `Role` | `roles` | `role_id`, `role_name` |
| `User` | `users` | `user_id`, `role_id` (FK), `email`, `password_hash`, `is_active` |
| `LabType` | `lab_types` | `lab_type_id`, `type_name` |
| `Lab` | `labs` | `lab_id`, `lab_type_id` (FK, nullable), `room_name`, `capacity`, `status` |
| `EquipmentCategory` | `equipment_categories` | `category_id`, `category_name` |
| `Equipment` | `equipments` | `equipment_id`, `lab_id` (FK, nullable), `category_id` (FK, nullable), `equipment_name`, `status` |
| `LabReservation` | `lab_reservations` | `reservation_id`, `lab_id` (FK), `reserved_by` (FK→users), `start_time`, `end_time`, `status` |
| `ReservationParticipant` | `reservation_participants` | `reservation_id` (FK, PK), `user_id` (FK, PK) |
| `EquipmentBorrowing` | `equipment_borrowings` | `borrow_id`, `user_id` (FK), `equipment_id` (FK), `borrow_time`, `expected_return`, `actual_return`, `status` |
| `MaintenanceRecord` | `maintenance_records` | `repair_id`, `equipment_id` (FK), `reported_by` (FK→users), `technician_id` (FK→users, nullable), `report_date`, `resolved_date`, `issue_detail`, `status` |
| `Penalty` | `penalties` | `penalty_id`, `user_id` (FK), `borrow_id` (FK), `fine_amount`, `is_resolved` |
| `Notification` | `notifications` | `notification_id`, `user_id` (FK), `message`, `is_read` |
| `AuditLog` | `audit_logs` | `audit_log_id`, `actor_user_id` (FK, nullable), `action`, `target_type`, `target_id`, `details` (JSON), `created_at` |

---

## 5. Equipment Status State Machine

```
Available
   │
   ├─ POST /borrowings ──────────────→ Borrowed
   │                                      │
   │                                      └─ PATCH /borrowings/{id}/return ──→ Available (or In_Repair if open maintenance)
   │
   └─ POST /maintenance ─────────────→ In_Repair
                                          │
                                          └─ PATCH /maintenance/{id} (status=Fixed) ──→ Available (or Borrowed if active borrow)
```

`resolve_equipment_status` บังคับ priority: Borrowed > In_Repair > Available

---

## 6. Audit Log Coverage

| Action | Logged? |
|--------|---------|
| user.register | No |
| user.login | No |
| user.logout | No |
| user.role_changed | Yes |
| user.status_changed | Yes |
| lab.created | Yes |
| lab.updated | Yes |
| lab.deleted | Yes |
| equipment.created | Yes |
| equipment.updated | Yes |
| equipment.deleted | Yes |
| equipment.borrowed | Yes |
| equipment.returned | Yes |
| maintenance.reported | Yes |
| maintenance.updated | Yes |
| reservation.created | No |
| reservation.cancelled | No |
| reservation.updated | No |
| reservation.deleted | No |
