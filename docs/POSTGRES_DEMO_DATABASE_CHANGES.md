# PostgreSQL Demo: แต่ละระบบทำให้ Database เปลี่ยนยังไง

เอกสารนี้ใช้สำหรับเล่าตอนเปิด PostgreSQL หรือ pgAdmin แล้วโชว์ว่าแต่ละฟีเจอร์ของระบบทำให้ข้อมูลใน database เปลี่ยนอย่างไรแบบเป็นรูปธรรม

แนวคิดของเอกสารนี้คือ:

- ก่อนทำ action ให้โชว์ข้อมูลก่อน
- ทำ action ผ่านระบบ
- กลับมาดูใน PostgreSQL ว่า row ไหนถูก `INSERT`, `UPDATE` หรือเชื่อมโยงเพิ่ม
- อธิบายว่าการเปลี่ยนนั้นสะท้อน business logic ของระบบอย่างไร

## 1. Opening

ประโยคเปิดที่ใช้ได้ทันที:

> ผมจะไม่โชว์แค่หน้าเว็บนะครับ แต่จะโชว์ใน PostgreSQL ด้วยว่าแต่ละ action ของผู้ใช้ทำให้ตารางไหนเปลี่ยน คอลัมน์ไหนเปลี่ยน และความสัมพันธ์ของข้อมูลเชื่อมกันอย่างไร เพื่อยืนยันว่า database เป็นแกนของระบบจริง

## 2. ตารางหลักที่ควรรู้ก่อนเดโม

ก่อนเข้าแต่ละ case ให้ชี้กลุ่มตารางหลักก่อน

Master / lookup:

- `roles`
- `lab_types`
- `equipment_categories`

Core:

- `users`
- `labs`
- `equipments`

Transactions:

- `lab_reservations`
- `reservation_participants`
- `equipment_borrowings`
- `maintenance_records`

Supporting:

- `penalties`
- `notifications`
- `audit_logs`

ประโยคอธิบาย:

> เวลา user ทำ action หนึ่งครั้ง มักไม่ได้กระทบแค่ตารางเดียว แต่จะมี transaction table เป็นตัวหลัก แล้ว supporting tables อย่าง notification, penalty หรือ audit logs ถูกอัปเดตตาม business rule ด้วย

## 3. SQL เบื้องต้นที่ควรเปิดไว้ก่อนเดโม

ถ้าใช้ `psql`:

```sql
\dt
SELECT current_database();
SELECT NOW();
```

ถ้าต้องการดูข้อมูลสั้น ๆ:

```sql
SELECT * FROM users ORDER BY user_id;
SELECT * FROM labs ORDER BY lab_id;
SELECT * FROM equipments ORDER BY equipment_id;
```

## 4. Case 1: สมัครสมาชิก

### ก่อนทำรายการ

ดูจำนวน user ก่อน:

```sql
SELECT user_id, role_id, email, first_name, last_name, is_active, created_at
FROM users
ORDER BY user_id;
```

### ตอนทำรายการ

ผู้ใช้สมัครผ่าน `POST /auth/register`

### หลังทำรายการ database เปลี่ยนยังไง

ตารางที่เปลี่ยน:

- `users`

สิ่งที่เกิดขึ้น:

- มี `INSERT` row ใหม่ใน `users`
- `role_id` จะถูกตั้งเป็น role ของ `Student` อัตโนมัติ
- `password_hash` ถูกเก็บเป็น hash ไม่ใช่ plain text
- `is_active` เป็น `true`

SQL ที่ใช้โชว์:

```sql
SELECT user_id, role_id, email, first_name, last_name, is_active, password_hash, created_at
FROM users
WHERE email = 'student_new@lab.demo';
```

ประโยคอธิบาย:

> ตอนสมัคร ระบบไม่ได้เขียนแค่ email กับชื่อ แต่ใส่ default role เป็น Student และเก็บ password_hash ลง database ทันที แปลว่า authentication ผูกกับข้อมูลใน users table โดยตรง

## 5. Case 2: Login

### ก่อนทำรายการ

ชี้ให้เห็นก่อนว่า login ไม่ได้สร้าง row ใหม่ใน business tables

### หลังทำรายการ database เปลี่ยนไหม

ใน implementation ตอนนี้ login ใช้ session middleware และ session cookie

ดังนั้น:

- database หลักของระบบ **ไม่เปลี่ยน**
- ไม่มี `INSERT` ใน `users`
- ไม่มี `UPDATE` ใน `audit_logs` จาก login flow ปัจจุบัน

ประโยคอธิบาย:

> login เป็นการตรวจข้อมูลจาก users table แล้วสร้าง session ฝั่งแอป ไม่ได้เพิ่ม row ใหม่ใน PostgreSQL ของระบบงาน ดังนั้นนี่เป็นตัวอย่างว่าบาง action อ่านจาก database แต่ไม่ได้เขียนกลับ

## 6. Case 3: จองห้อง

### ก่อนทำรายการ

ดูห้องและ reservation เดิมก่อน:

```sql
SELECT lab_id, room_name, capacity, status
FROM labs
ORDER BY lab_id;

SELECT reservation_id, lab_id, reserved_by, start_time, end_time, status
FROM lab_reservations
ORDER BY reservation_id;
```

ถ้าจะโชว์เฉพาะห้องหนึ่ง เช่น `CS-101`:

```sql
SELECT l.room_name, lr.reservation_id, lr.reserved_by, lr.start_time, lr.end_time, lr.status
FROM lab_reservations lr
JOIN labs l ON l.lab_id = lr.lab_id
WHERE l.room_name = 'CS-101'
ORDER BY lr.start_time;
```

### ตอนทำรายการ

Student สร้าง reservation ใหม่ผ่าน `POST /reservations`

### หลังทำรายการ database เปลี่ยนยังไง

ตารางที่เปลี่ยน:

- `lab_reservations`

สิ่งที่เกิดขึ้น:

- มี `INSERT` row ใหม่ใน `lab_reservations`
- `lab_id` ชี้ไปยังห้องที่จอง
- `reserved_by` ชี้ไปยัง user ที่จอง
- `start_time`, `end_time` ถูกบันทึก
- `status` ถูกตั้งเป็น `Approved` จาก service ปัจจุบัน

SQL ที่ใช้โชว์:

```sql
SELECT reservation_id, lab_id, reserved_by, start_time, end_time, status, created_at
FROM lab_reservations
ORDER BY reservation_id DESC
LIMIT 5;
```

ประโยคอธิบาย:

> การจองห้องคือ transaction ใหม่ของระบบ ดังนั้นจะเกิด row ใหม่ใน `lab_reservations` หนึ่งแถว ซึ่งผูกทั้ง user และห้องผ่าน foreign key ชัดเจน

## 7. Case 4: ยกเลิกการจอง

### ก่อนทำรายการ

```sql
SELECT reservation_id, lab_id, reserved_by, start_time, end_time, status
FROM lab_reservations
WHERE reservation_id = 1;
```

### ตอนทำรายการ

เจ้าของ reservation กดยกเลิกผ่าน `POST /reservations/{reservation_id}/cancel`

### หลังทำรายการ database เปลี่ยนยังไง

ตารางที่เปลี่ยน:

- `lab_reservations`

สิ่งที่เกิดขึ้น:

- ไม่มีการลบ row
- มี `UPDATE` ที่คอลัมน์ `status`
- ค่าเปลี่ยนจาก `Pending` หรือ `Approved` เป็น `Cancelled`

SQL ที่ใช้โชว์:

```sql
SELECT reservation_id, status, updated_at
FROM lab_reservations
WHERE reservation_id = 1;
```

ประโยคอธิบาย:

> ระบบเลือกเก็บประวัติ reservation ไว้ ไม่ลบทิ้ง ทำให้เรายังย้อนดู transaction เดิมได้และใช้ต่อใน report ได้

## 8. Case 5: กันการจองเวลาซ้อน

### ก่อนทำรายการ

โชว์ booking เดิมของห้อง:

```sql
SELECT reservation_id, lab_id, start_time, end_time, status
FROM lab_reservations
WHERE lab_id = 1
  AND status IN ('Pending', 'Approved')
ORDER BY start_time;
```

### ตอนทำรายการ

ลองจองเวลาใหม่ที่ overlap กับรายการเดิม

### หลังทำรายการ database เปลี่ยนไหม

- **ไม่เปลี่ยน**
- ไม่มี row ใหม่ใน `lab_reservations`

เหตุผล:

- service layer เช็ก overlap ก่อน
- ถ้าหลุดมาถึง database PostgreSQL exclusion constraint ก็กันซ้ำอีกชั้น

ประโยคอธิบาย:

> จุดนี้เดโมง่ายมาก เพราะเราจะเห็นว่าผู้ใช้ทำ action แต่ database ไม่ยอมเปลี่ยน เนื่องจาก business rule ถูก enforce ทั้งใน application และใน PostgreSQL

## 9. Case 6: ยืมอุปกรณ์

### ก่อนทำรายการ

ดูสถานะอุปกรณ์ก่อน:

```sql
SELECT equipment_id, equipment_name, lab_id, status
FROM equipments
WHERE equipment_name = 'Projector-A';
```

ดู borrowing เดิม:

```sql
SELECT borrow_id, user_id, equipment_id, borrow_time, expected_return, actual_return, status
FROM equipment_borrowings
WHERE equipment_id = 4
ORDER BY borrow_id;
```

### ตอนทำรายการ

Staff สร้าง borrowing ผ่าน `POST /borrowings`

### หลังทำรายการ database เปลี่ยนยังไง

ตารางที่เปลี่ยน:

- `equipment_borrowings`
- `equipments`
- `audit_logs`

สิ่งที่เกิดขึ้น:

1. `equipment_borrowings`
   - มี `INSERT` row ใหม่
   - เก็บ `user_id`, `equipment_id`, `expected_return`, `status='Borrowed'`

2. `equipments`
   - มี `UPDATE` คอลัมน์ `status`
   - จาก `Available` เป็น `Borrowed`

3. `audit_logs`
   - มี `INSERT` row ใหม่
   - action เป็น `equipment.borrowed`

SQL ที่ใช้โชว์:

```sql
SELECT borrow_id, user_id, equipment_id, borrow_time, expected_return, actual_return, status
FROM equipment_borrowings
ORDER BY borrow_id DESC
LIMIT 5;

SELECT equipment_id, equipment_name, status
FROM equipments
WHERE equipment_name = 'Projector-A';

SELECT audit_log_id, actor_user_id, action, target_type, target_id, created_at
FROM audit_logs
WHERE action = 'equipment.borrowed'
ORDER BY audit_log_id DESC
LIMIT 5;
```

ประโยคอธิบาย:

> การยืมหนึ่งครั้งกระทบสามตารางพร้อมกัน คือ transaction หลักอยู่ที่ `equipment_borrowings`, state ของ resource อยู่ที่ `equipments`, และ traceability อยู่ที่ `audit_logs`

## 10. Case 7: คืนอุปกรณ์ตรงเวลา

### ก่อนทำรายการ

```sql
SELECT borrow_id, equipment_id, expected_return, actual_return, status
FROM equipment_borrowings
WHERE borrow_id = 4;

SELECT equipment_id, equipment_name, status
FROM equipments
WHERE equipment_id = 8;
```

### ตอนทำรายการ

Staff กดรับคืนผ่าน `PATCH /borrowings/{borrow_id}/return`

### หลังทำรายการ database เปลี่ยนยังไง

ตารางที่เปลี่ยน:

- `equipment_borrowings`
- `equipments`
- `audit_logs`

สิ่งที่เกิดขึ้น:

1. `equipment_borrowings`
   - `actual_return` ถูกเติมเวลา
   - `status` เปลี่ยนเป็น `Returned`

2. `equipments`
   - `status` ถูกคำนวณใหม่
   - ถ้าไม่มี active borrowing หรือ open maintenance จะกลับเป็น `Available`

3. `audit_logs`
   - เพิ่ม action `equipment.returned`

4. `penalties`
   - **ไม่เปลี่ยน** ถ้าคืนตรงเวลา

5. `notifications`
   - **ไม่เปลี่ยน** ถ้าไม่มีค่าปรับ

SQL ที่ใช้โชว์:

```sql
SELECT borrow_id, expected_return, actual_return, status
FROM equipment_borrowings
WHERE borrow_id = 4;

SELECT equipment_id, equipment_name, status
FROM equipments
WHERE equipment_id = 8;
```

ประโยคอธิบาย:

> ถ้าคืนตรงเวลา database จะอัปเดตแค่ transaction การยืมกับสถานะอุปกรณ์ และบันทึก audit log แต่จะยังไม่แตะ penalty หรือ notification

## 11. Case 8: คืนอุปกรณ์ช้า

### ก่อนทำรายการ

```sql
SELECT borrow_id, user_id, equipment_id, expected_return, actual_return, status
FROM equipment_borrowings
WHERE borrow_id = 3;

SELECT * FROM penalties WHERE borrow_id = 3;
SELECT * FROM notifications WHERE user_id = 6 ORDER BY notification_id DESC;
```

### ตอนทำรายการ

Staff รับคืนรายการที่ overdue

### หลังทำรายการ database เปลี่ยนยังไง

ตารางที่เปลี่ยน:

- `equipment_borrowings`
- `equipments`
- `penalties`
- `notifications`
- `audit_logs`

สิ่งที่เกิดขึ้น:

1. `equipment_borrowings`
   - `actual_return` ถูกเติมค่า
   - `status` เปลี่ยนเป็น `Returned`

2. `equipments`
   - ปรับสถานะใหม่ตามสภาพปัจจุบัน

3. `penalties`
   - มี `INSERT` row ใหม่
   - เก็บ `user_id`, `borrow_id`, `fine_amount`, `is_resolved=false`

4. `notifications`
   - มี `INSERT` row ใหม่ แจ้งผู้ใช้ว่ามีค่าปรับ

5. `audit_logs`
   - มี `INSERT` action `equipment.returned`

SQL ที่ใช้โชว์:

```sql
SELECT penalty_id, user_id, borrow_id, fine_amount, is_resolved, created_at
FROM penalties
ORDER BY penalty_id DESC
LIMIT 5;

SELECT notification_id, user_id, message, is_read, created_at
FROM notifications
ORDER BY notification_id DESC
LIMIT 5;
```

ประโยคอธิบาย:

> เคสคืนช้าจะเห็นชัดว่าหนึ่ง action ทำให้เกิด business consequence เพิ่ม คือไม่ใช่แค่ปิด borrowing แต่สร้าง penalty และ notification ใหม่ตามกติกาของระบบ

## 12. Case 9: แจ้งซ่อมอุปกรณ์

### ก่อนทำรายการ

```sql
SELECT equipment_id, equipment_name, status
FROM equipments
WHERE equipment_name = 'Oscilloscope-02';

SELECT repair_id, equipment_id, reported_by, technician_id, report_date, resolved_date, status
FROM maintenance_records
WHERE equipment_id = 6
ORDER BY repair_id;
```

### ตอนทำรายการ

ผู้ใช้แจ้งซ่อมผ่าน `POST /maintenance`

### หลังทำรายการ database เปลี่ยนยังไง

ตารางที่เปลี่ยน:

- `maintenance_records`
- `equipments`
- `audit_logs`

สิ่งที่เกิดขึ้น:

1. `maintenance_records`
   - มี `INSERT` row ใหม่
   - `reported_by` เป็น user ที่แจ้ง
   - `status` เริ่มต้นเป็น `Reported`

2. `equipments`
   - `status` ถูก resolve ใหม่
   - ถ้ามีงานซ่อมเปิดอยู่ จะกลายเป็น `In_Repair`

3. `audit_logs`
   - เพิ่ม action `maintenance.reported`

SQL ที่ใช้โชว์:

```sql
SELECT repair_id, equipment_id, reported_by, technician_id, report_date, resolved_date, status, issue_detail
FROM maintenance_records
ORDER BY repair_id DESC
LIMIT 5;

SELECT equipment_id, equipment_name, status
FROM equipments
WHERE equipment_name = 'Oscilloscope-02';
```

ประโยคอธิบาย:

> ฝั่ง maintenance จะเห็นว่าตาราง transaction คือ `maintenance_records` ส่วนตาราง resource state คือ `equipments` ซึ่งเปลี่ยนตามว่ามี open repair อยู่หรือไม่

## 13. Case 10: Technician อัปเดตสถานะซ่อม

### ก่อนทำรายการ

```sql
SELECT repair_id, equipment_id, reported_by, technician_id, report_date, resolved_date, status
FROM maintenance_records
WHERE repair_id = 2;

SELECT equipment_id, equipment_name, status
FROM equipments
WHERE equipment_id = 8;
```

### ตอนทำรายการ

Technician ใช้ `PATCH /maintenance/{repair_id}` เปลี่ยน status เป็น `In Progress` หรือ `Fixed`

### หลังทำรายการ database เปลี่ยนยังไง

ตารางที่เปลี่ยน:

- `maintenance_records`
- `equipments`
- `notifications`
- `audit_logs`

สิ่งที่เกิดขึ้น:

1. `maintenance_records`
   - `technician_id` ถูกกำหนด
   - `status` ถูกอัปเดต
   - ถ้า status เป็น `Fixed` จะเติม `resolved_date`

2. `equipments`
   - `status` ถูกคำนวณใหม่
   - ถ้าไม่มี open repair แล้ว อาจกลับเป็น `Available`

3. `notifications`
   - ถ้าซ่อมเสร็จ จะเพิ่ม notification ไปยังคนที่แจ้ง

4. `audit_logs`
   - เพิ่ม action `maintenance.updated`

SQL ที่ใช้โชว์:

```sql
SELECT repair_id, technician_id, status, resolved_date
FROM maintenance_records
WHERE repair_id = 2;

SELECT notification_id, user_id, message, created_at
FROM notifications
ORDER BY notification_id DESC
LIMIT 5;

SELECT audit_log_id, actor_user_id, action, target_type, target_id, created_at
FROM audit_logs
WHERE action = 'maintenance.updated'
ORDER BY audit_log_id DESC
LIMIT 5;
```

ประโยคอธิบาย:

> พอ technician เปลี่ยนสถานะซ่อม เราจะเห็น lifecycle ครบใน database คือมีทั้งคนรับงาน, สถานะงาน, วันปิดงาน, การแจ้งกลับ และประวัติใน audit log

## 14. Case 11: อ่าน notification

### ก่อนทำรายการ

```sql
SELECT notification_id, user_id, message, is_read, created_at
FROM notifications
WHERE user_id = 5
ORDER BY notification_id DESC;
```

### ตอนทำรายการ

ผู้ใช้กด mark ว่าอ่านแล้วผ่าน `PATCH /notifications/{notification_id}`

### หลังทำรายการ database เปลี่ยนยังไง

ตารางที่เปลี่ยน:

- `notifications`

สิ่งที่เกิดขึ้น:

- `is_read` เปลี่ยนจาก `false` เป็น `true`

SQL ที่ใช้โชว์:

```sql
SELECT notification_id, is_read, updated_at
FROM notifications
WHERE notification_id = 1;
```

ประโยคอธิบาย:

> เคสนี้เป็นตัวอย่างของ state transition แบบง่าย ๆ ใน supporting table ว่าการโต้ตอบของผู้ใช้กับระบบก็ถูกเก็บใน database เช่นกัน

## 15. Case 12: Admin เปลี่ยน role ของ user

### ก่อนทำรายการ

```sql
SELECT u.user_id, u.email, r.role_name
FROM users u
JOIN roles r ON r.role_id = u.role_id
WHERE u.email = 'alice@lab.demo';
```

### ตอนทำรายการ

Admin เรียก `PATCH /admin/users/{user_id}/role`

### หลังทำรายการ database เปลี่ยนยังไง

ตารางที่เปลี่ยน:

- `users`
- `audit_logs`

สิ่งที่เกิดขึ้น:

1. `users`
   - `role_id` เปลี่ยนไปอ้าง role ใหม่

2. `audit_logs`
   - เพิ่ม action `user.role_changed`

SQL ที่ใช้โชว์:

```sql
SELECT u.user_id, u.email, u.role_id, r.role_name
FROM users u
JOIN roles r ON r.role_id = u.role_id
WHERE u.email = 'alice@lab.demo';

SELECT audit_log_id, actor_user_id, action, details, created_at
FROM audit_logs
WHERE action = 'user.role_changed'
ORDER BY audit_log_id DESC
LIMIT 5;
```

## 16. Case 13: Admin ปิด/เปิดบัญชีผู้ใช้

### ก่อนทำรายการ

```sql
SELECT user_id, email, is_active
FROM users
WHERE email = 'bob@lab.demo';
```

### ตอนทำรายการ

Admin เรียก `PATCH /admin/users/{user_id}/status`

### หลังทำรายการ database เปลี่ยนยังไง

ตารางที่เปลี่ยน:

- `users`
- `audit_logs`

สิ่งที่เกิดขึ้น:

1. `users`
   - `is_active` เปลี่ยนค่า

2. `audit_logs`
   - เพิ่ม action `user.status_changed`

ประโยคอธิบาย:

> ตรงนี้ดีสำหรับโชว์ governance ของระบบ เพราะ admin ไม่จำเป็นต้องลบ user แต่ปิดการใช้งานได้ และมี audit trail เก็บไว้ว่าใครเป็นคนเปลี่ยน

## 17. Case 14: CRUD ห้องและอุปกรณ์

### สร้างห้อง

ตารางที่เปลี่ยน:

- `labs`
- `audit_logs`

สิ่งที่เกิดขึ้น:

- `INSERT` ใหม่ใน `labs`
- `INSERT` ใหม่ใน `audit_logs` เป็น `lab.created`

### แก้ไขห้อง

ตารางที่เปลี่ยน:

- `labs`
- `audit_logs`

สิ่งที่เกิดขึ้น:

- `UPDATE` ที่ `room_name`, `capacity`, `status`
- `audit_logs.details` เก็บทั้ง before และ after

### ลบห้อง

ตารางที่เปลี่ยน:

- `labs`
- `audit_logs`

สิ่งที่เกิดขึ้น:

- ถ้ามี reservation หรือ equipment ผูกอยู่ จะ **ลบไม่ได้**
- ถ้าลบได้จะ `DELETE` จาก `labs` และเพิ่ม `audit_logs`

### สร้าง/แก้ไข/ลบอุปกรณ์

ตารางที่เปลี่ยน:

- `equipments`
- `audit_logs`

สิ่งที่เกิดขึ้น:

- create: `INSERT` `equipments` + `audit_logs`
- update: `UPDATE` `equipments` + `audit_logs`
- delete: `DELETE` `equipments` ถ้าไม่มี borrowing history

ประโยคอธิบาย:

> ฝั่ง admin ทำให้เห็นว่าฐานข้อมูลไม่ได้เก็บแค่ transaction ของผู้ใช้ปลายทาง แต่ยังเก็บ master data lifecycle และ audit trail ของงานบริหารระบบด้วย

## 18. ตารางสรุปว่าฟีเจอร์ไหนกระทบตารางอะไร

| Action | ตารางที่เปลี่ยน |
|---|---|
| Register | `users` |
| Login | ไม่มีการเปลี่ยน business tables |
| Create reservation | `lab_reservations` |
| Cancel reservation | `lab_reservations` |
| Overlap reservation attempt | ไม่มีการเปลี่ยน |
| Create borrowing | `equipment_borrowings`, `equipments`, `audit_logs` |
| Return on time | `equipment_borrowings`, `equipments`, `audit_logs` |
| Return late | `equipment_borrowings`, `equipments`, `penalties`, `notifications`, `audit_logs` |
| Report maintenance | `maintenance_records`, `equipments`, `audit_logs` |
| Update maintenance | `maintenance_records`, `equipments`, `notifications`, `audit_logs` |
| Mark notification read | `notifications` |
| Change user role | `users`, `audit_logs` |
| Change user active status | `users`, `audit_logs` |
| Admin create/update/delete lab | `labs`, `audit_logs` |
| Admin create/update/delete equipment | `equipments`, `audit_logs` |

## 19. ลำดับเดโมที่แนะนำ

ถ้ามีเวลา 5-7 นาที ให้ไล่ตามนี้:

1. เปิด `users`, `labs`, `equipments` เพื่อให้เห็น master data
2. ทำ reservation แล้วกลับมา query `lab_reservations`
3. ลองทำ overlapping reservation แล้วชี้ว่า database ไม่เปลี่ยน
4. ทำ borrowing แล้วโชว์ `equipment_borrowings` กับ `equipments`
5. ทำ return late แล้วโชว์ `penalties` กับ `notifications`
6. ทำ maintenance report แล้วโชว์ `maintenance_records`
7. ให้ technician ปิดงาน แล้วโชว์ `resolved_date`, `notifications`, `audit_logs`
8. ปิดท้ายด้วย `audit_logs` เพื่อสรุปว่า database เก็บ trace ย้อนหลังได้

## 20. Closing

ประโยคปิดที่ใช้ได้ทันที:

> สิ่งที่ผมอยากโชว์คือทุก action ของระบบไม่ได้จบแค่หน้าเว็บ แต่สะท้อนลงใน PostgreSQL อย่างเป็นระบบครับ บางเคสเป็นการเพิ่ม transaction ใหม่ บางเคสเป็นการเปลี่ยน state ของ resource และบางเคสสร้างผลลัพธ์ต่อเนื่องอย่าง penalty, notification และ audit log ทำให้ database ของระบบนี้เป็นทั้งที่เก็บข้อมูลและตัวสะท้อน business workflow จริง

## 21. ไฟล์อ้างอิงในโปรเจกต์

- [sql/schema.sql](/abs/path/C:/Users/saifa/Desktop/cn230/sql/schema.sql:1)
- [scripts/seed_demo.py](/abs/path/C:/Users/saifa/Desktop/cn230/scripts/seed_demo.py:1)
- [app/services/reservation_service.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/services/reservation_service.py:1)
- [app/services/borrowing_service.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/services/borrowing_service.py:1)
- [app/services/maintenance_service.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/services/maintenance_service.py:1)
