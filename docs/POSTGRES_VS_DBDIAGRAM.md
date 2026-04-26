# PostgreSQL Vs `dbdiagram.io`

ไฟล์นี้ใช้ตอบคำถามว่า diagram ที่วาดใน `dbdiagram.io` ตรงกับฐานข้อมูล PostgreSQL จริงแค่ไหน

## คำตอบสั้นมาก

`dbdiagram.io` ตรงกับ PostgreSQL จริงในระดับโครงสร้างหลักของฐานข้อมูล แต่ไม่ใช่ DDL จริงแบบ 100%

ตรงแน่ๆ คือ:
- ชื่อตาราง
- ชื่อคอลัมน์
- Primary Key
- Foreign Key
- ความสัมพันธ์ระหว่างตาราง
- ชนิดข้อมูลหลัก

สิ่งที่ PostgreSQL มีจริง แต่ใน diagram มักแสดงไม่ครบคือ:
- `CHECK CONSTRAINT`
- `UNIQUE`
- `DEFAULT`
- `INDEX`
- `ON DELETE` / `ON UPDATE`
- PostgreSQL-specific constraint เช่น `EXCLUDE USING gist`

## ถ้าจะตอบอาจารย์แบบสั้น

"Diagram ใน `dbdiagram.io` ของผมถอดมาจาก schema PostgreSQL จริงครับ ดังนั้นโครงสร้างตารางและความสัมพันธ์ตรงกัน แต่ diagram เป็นเวอร์ชันสื่อสารภาพรวม จึงไม่ได้แสดงรายละเอียดเชิงเทคนิคทุกอย่าง เช่น index, check constraint, on delete behavior และ exclusion constraint ของ PostgreSQL"

## เทียบเป็นหัวข้อ

### 1) สิ่งที่ตรงกับฐานข้อมูล PostgreSQL จริง

จาก schema จริงใน [sql/schema.sql](/abs/path/C:/Users/saifa/Desktop/cn230/sql/schema.sql:1)

- ตารางทั้งหมด 13 ตารางตรงกัน
- key หลักของแต่ละตารางตรงกัน
- foreign key ตรงกัน
- ความสัมพันธ์ `one-to-many` และ `many-to-many` ตรงกัน
- ตารางเชื่อม `reservation_participants` ตรงกับของจริง

ตัวอย่าง:
- `users.role_id -> roles.role_id`
- `equipments.lab_id -> labs.lab_id`
- `lab_reservations.reserved_by -> users.user_id`
- `penalties.borrow_id -> equipment_borrowings.borrow_id`

## 2) สิ่งที่ PostgreSQL จริงมีเพิ่มจาก diagram

### Check constraints

ใน PostgreSQL มีการบังคับกติกาของข้อมูล เช่น

- `labs.capacity > 0`
- `lab_reservations.end_time > start_time`
- `penalties.fine_amount > 0`

และมีการจำกัดค่า `status` หลายตาราง เช่น

- `labs.status` ต้องเป็น `Available`, `Reserved`, `Maintenance`, `Closed`
- `equipments.status` ต้องเป็น `Available`, `Borrowed`, `In_Repair`
- `equipment_borrowings.status` ต้องเป็น `Borrowed`, `Returned`
- `maintenance_records.status` ต้องเป็น `Reported`, `In Progress`, `Fixed`

### Unique constraints

ตัวอย่างที่ PostgreSQL บังคับจริง:

- `users.email` ต้องไม่ซ้ำ
- `labs.room_name` ต้องไม่ซ้ำ
- `roles.role_name` ต้องไม่ซ้ำ
- `lab_types.type_name` ต้องไม่ซ้ำ
- `equipment_categories.category_name` ต้องไม่ซ้ำ

### Default values

ตัวอย่าง:

- timestamp หลายตารางใช้ `NOW()`
- `users.is_active` default เป็น `TRUE`
- `penalties.is_resolved` default เป็น `FALSE`
- status หลายตารางมีค่า default

### Indexes

ฐานข้อมูลจริงมี index เพื่อช่วย query ให้เร็วขึ้น เช่น

- `idx_users_email`
- `idx_labs_status`
- `idx_equipments_lab_id`
- `idx_borrowings_user_id`
- `idx_penalties_borrow_id`
- `idx_audit_created`

diagram ปกติจะไม่เน้นเรื่องนี้

### Foreign key behavior

PostgreSQL จริงกำหนดพฤติกรรมตอน update/delete เพิ่ม เช่น

- `ON DELETE RESTRICT`
- `ON DELETE SET NULL`
- `ON DELETE CASCADE`
- `ON UPDATE CASCADE`

ตัวอย่าง:
- ลบ user แล้ว `notifications` จะลบตามเพราะเป็น `CASCADE`
- ลบ user แล้ว `audit_logs.actor_user_id` จะเป็น `NULL`
- ลบ lab ที่ถูกใช้งานใน reservation จะถูก `RESTRICT`

## 3) จุดที่สำคัญมากในเวอร์ชันล่าสุด

PostgreSQL จริงของโปรเจกต์นี้มี constraint เพิ่มจาก migration ล่าสุด:

- [migrations/versions/20260409_0002_reservation_exclusion_constraint.py](/abs/path/C:/Users/saifa/Desktop/cn230/migrations/versions/20260409_0002_reservation_exclusion_constraint.py:1)

constraint นี้คือ:

- ห้องเดียวกัน
- เวลาเริ่มและเวลาจบซ้อนกัน
- และสถานะเป็น `Pending` หรือ `Approved`

จะบันทึกซ้ำไม่ได้

นี่คือ business rule สำคัญที่ `dbdiagram.io` มักไม่แสดงได้ครบ เพราะเป็น PostgreSQL-specific feature แบบ `EXCLUDE USING gist`

## 4) สรุปให้พูดหน้าห้อง

"ใน PostgreSQL จริง ระบบนี้ไม่ได้มีแค่ตารางสัมพันธ์กันเฉยๆ แต่ยังมีการบังคับกฎธุรกิจในฐานข้อมูลด้วย เช่น email ห้ามซ้ำ, ห้องต้องมีความจุมากกว่า 0, เวลาจองต้องจบหลังเวลาเริ่ม, ค่าปรับต้องมากกว่า 0 และมี exclusion constraint เพื่อกันการจองห้องเวลา overlap

ดังนั้น diagram ที่ผมวาดใน `dbdiagram.io` คือภาพรวมของ schema จริง แต่ของจริงใน PostgreSQL มีรายละเอียดเชิงบังคับใช้มากกว่านั้น"

## 5) ถ้าอาจารย์ถามว่า “แล้วทำไมไม่โชว์ทุกอย่างใน diagram?”

ตอบได้ว่า:

"เพราะ diagram มีเป้าหมายเพื่อสื่อสารโครงสร้างและความสัมพันธ์ให้เข้าใจเร็วครับ ส่วนรายละเอียดเชิง implementation เช่น index, check constraint หรือ PostgreSQL-specific constraint ผมเก็บไว้ใน schema SQL และ migration ซึ่งเป็นแหล่งอ้างอิงของระบบจริง"

## แหล่งอ้างอิง

- [sql/schema.sql](/abs/path/C:/Users/saifa/Desktop/cn230/sql/schema.sql:1)
- [migrations/versions/20260409_0001_initial_schema.py](/abs/path/C:/Users/saifa/Desktop/cn230/migrations/versions/20260409_0001_initial_schema.py:1)
- [migrations/versions/20260409_0002_reservation_exclusion_constraint.py](/abs/path/C:/Users/saifa/Desktop/cn230/migrations/versions/20260409_0002_reservation_exclusion_constraint.py:1)
