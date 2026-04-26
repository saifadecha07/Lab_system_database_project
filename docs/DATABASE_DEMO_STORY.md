# Database Demo Story

เอกสารนี้ทำไว้สำหรับใช้เล่า demo ระบบแบบเน้น database เป็นแกนหลัก ตั้งแต่ schema, constraint, transaction flow, ไปจนถึง SQL reports โดยเรียงลำดับให้พูดตามได้ง่าย

## 1. Opening สั้น ๆ

ประโยคเปิดที่ใช้ได้ทันที:

> ระบบของผมคือ Smart Lab Management System สำหรับจัดการห้องปฏิบัติการและอุปกรณ์ครับ จุดเด่นคือไม่ได้ทำแค่ CRUD แต่เอา database มาเป็นแกนของ business rules จริง เช่น การจองห้องห้ามเวลาซ้อน, การยืมคืนต้องติดตามสถานะ, คืนช้าเกิดค่าปรับ, งานซ่อมมีประวัติย้อนหลัง, และทุกอย่างถูกสรุปออกมาเป็น SQL reports ได้จาก relational schema เดียว

ถ้าต้องการเปิดแบบสั้นกว่า:

> โปรเจกต์นี้ออกแบบฐานข้อมูล PostgreSQL ให้รองรับทั้ง master data, transaction data, audit trail, notification, penalty และ advanced reporting ในระบบเดียวครับ

## 2. ภาพรวม database architecture

โครงสร้างฐานข้อมูลแบ่งเป็น 4 กลุ่มหลัก:

1. Lookup tables
   - `roles`
   - `lab_types`
   - `equipment_categories`

2. Core entities
   - `users`
   - `labs`
   - `equipments`

3. Transaction tables
   - `lab_reservations`
   - `reservation_participants`
   - `equipment_borrowings`
   - `maintenance_records`

4. Supporting / control tables
   - `penalties`
   - `notifications`
   - `audit_logs`

ประโยคอธิบาย:

> ผมแยก schema เป็นข้อมูลอ้างอิง, ข้อมูลหลัก, ข้อมูลธุรกรรม และข้อมูลสนับสนุน เพื่อให้ลดข้อมูลซ้ำและทำให้แต่ละตารางมีหน้าที่ชัดเจน เวลา query หรือขยายระบบจะ maintain ง่ายกว่าเก็บทุกอย่างไว้ในตารางเดียว

## 3. Schema walkthrough แบบเล่าทีละชั้น

### 3.1 Lookup tables

`roles`
- เก็บบทบาทของผู้ใช้ เช่น Student, Staff, Technician, Admin
- ทำให้ user ไม่ต้องเก็บชื่อ role ซ้ำทุกแถว
- ถ้ามี role ใหม่ในอนาคตก็เพิ่มข้อมูลได้โดยไม่ต้อง redesign ตาราง users

`lab_types`
- แยกประเภทห้อง เช่น Computer Lab, Science Lab
- ช่วยให้ query รายงานการใช้งานตามประเภทห้องได้ง่าย

`equipment_categories`
- แยกหมวดอุปกรณ์ เช่น Computer, Microscope, Electronics
- ใช้ทั้งในหน้าแสดงผลและ report ด้านการซ่อม/การยืม

ประโยคอธิบาย:

> สามตารางนี้เป็น lookup tables ที่ช่วย normalization ครับ เพราะค่าที่ถูกใช้ซ้ำบ่อย ๆ ไม่ควร hard-code ไว้ในตารางหลัก

### 3.2 Core entities

`users`
- PK: `user_id`
- FK: `role_id -> roles.role_id`
- จุดสำคัญ:
  - `email` เป็น `UNIQUE`
  - มี `is_active`
  - มี `created_at`, `updated_at`

ประโยคอธิบาย:

> users เป็นศูนย์กลางของหลาย transaction เพราะทั้งการจอง, การยืม, การแจ้งซ่อม, notification และ audit ต่างอ้างถึงผู้ใช้

`labs`
- PK: `lab_id`
- FK: `lab_type_id -> lab_types.lab_type_id`
- จุดสำคัญ:
  - `room_name` เป็น `UNIQUE`
  - `capacity > 0`
  - `status` จำกัดค่าเป็น `Available`, `Reserved`, `Maintenance`, `Closed`

ประโยคอธิบาย:

> labs ไม่ได้เก็บแค่ชื่อห้อง แต่เก็บ capacity และ status เพื่อให้ฐานข้อมูลสะท้อนสภาพการใช้งานจริงของห้อง

`equipments`
- PK: `equipment_id`
- FK:
  - `category_id -> equipment_categories.category_id`
  - `lab_id -> labs.lab_id`
- จุดสำคัญ:
  - อุปกรณ์แต่ละชิ้นผูกกับห้องได้
  - `status` จำกัดค่าเป็น `Available`, `Borrowed`, `In_Repair`

ประโยคอธิบาย:

> การแยก equipments ออกจาก labs ทำให้รองรับความสัมพันธ์แบบหนึ่งห้องมีหลายอุปกรณ์ และยัง track วงจรชีวิตของอุปกรณ์แต่ละชิ้นได้ละเอียด

### 3.3 Transaction tables

`lab_reservations`
- ใช้เก็บธุรกรรมการจองห้อง
- FK:
  - `lab_id -> labs.lab_id`
  - `reserved_by -> users.user_id`
- จุดสำคัญ:
  - `start_time`, `end_time`
  - check constraint `end_time > start_time`
  - status จำกัดค่า `Pending`, `Approved`, `Cancelled`

`reservation_participants`
- เป็น junction table แบบ many-to-many
- PK แบบ composite: `(reservation_id, user_id)`
- ใช้เก็บผู้เข้าร่วมหลายคนในหนึ่ง reservation

ประโยคอธิบาย:

> ผมไม่เก็บ participant เป็น text list ใน reservation เพราะจะ query ยากและผิดหลัก relational database จึงแยกเป็น junction table เพื่อรองรับ many-to-many อย่างถูกต้อง

`equipment_borrowings`
- ใช้เก็บประวัติการยืมคืนอุปกรณ์
- FK:
  - `user_id -> users.user_id`
  - `equipment_id -> equipments.equipment_id`
- จุดสำคัญ:
  - `borrow_time`
  - `expected_return`
  - `actual_return`
  - status `Borrowed` หรือ `Returned`

`maintenance_records`
- ใช้เก็บงานแจ้งซ่อมและงานซ่อมจริง
- FK:
  - `equipment_id -> equipments.equipment_id`
  - `reported_by -> users.user_id`
  - `technician_id -> users.user_id`
- จุดสำคัญ:
  - `issue_detail`
  - `report_date`
  - `resolved_date`
  - status `Reported`, `In Progress`, `Fixed`

### 3.4 Supporting tables

`penalties`
- แยกจาก borrowing เพราะไม่ได้เกิดทุกครั้ง
- FK:
  - `user_id -> users.user_id`
  - `borrow_id -> equipment_borrowings.borrow_id`
- จุดสำคัญ:
  - `fine_amount > 0`
  - `is_resolved`

ประโยคอธิบาย:

> ถ้าเอาค่าปรับไปรวมใน borrowing จะทำให้มี nullable fields เยอะและความหมายปนกัน ผมจึงแยก penalties ออกมาเป็นตารางเฉพาะของ business event อีกชั้น

`notifications`
- เก็บข้อความแจ้งเตือนของผู้ใช้
- FK: `user_id -> users.user_id`
- ใช้กับเคสค่าปรับและสถานะซ่อม

`audit_logs`
- เก็บประวัติ action สำคัญในระบบ
- FK: `actor_user_id -> users.user_id`
- มี `action`, `target_type`, `target_id`, `details JSONB`

ประโยคอธิบาย:

> audit_logs ทำให้ระบบ trace ย้อนหลังได้ว่าใครทำอะไรกับ entity ไหน ซึ่งสำคัญมากเวลาอธิบายเรื่อง accountability ของระบบงานจริง

## 4. ความสัมพันธ์สำคัญที่ควรชี้ใน ER diagram

จุดที่ควรชี้ตอนเปิด diagram:

1. `roles 1:M users`
2. `lab_types 1:M labs`
3. `equipment_categories 1:M equipments`
4. `labs 1:M equipments`
5. `users 1:M lab_reservations`
6. `labs 1:M lab_reservations`
7. `lab_reservations M:N users` ผ่าน `reservation_participants`
8. `users 1:M equipment_borrowings`
9. `equipments 1:M equipment_borrowings`
10. `equipments 1:M maintenance_records`
11. `users 1:M penalties`
12. `equipment_borrowings 1:M penalties` ในเชิง schema ตอนนี้อ้างจาก penalty ไปยัง borrowing โดยตรง
13. `users 1:M notifications`
14. `users 1:M audit_logs`

ประโยคอธิบาย:

> schema นี้มีทั้ง one-to-many และ many-to-many ครบ ทำให้เหมาะกับวิชา database systems เพราะไม่ได้มีแค่ตารางเดี่ยว ๆ แต่มีความสัมพันธ์เชิงธุรกรรมจริง

## 5. Constraint และ integrity ที่เป็นจุดเด่น

### 5.1 ระดับ table constraint

มีการบังคับความถูกต้องใน database เช่น:

- `users.email` ห้ามซ้ำ
- `labs.room_name` ห้ามซ้ำ
- `labs.capacity > 0`
- `lab_reservations.end_time > start_time`
- `penalties.fine_amount > 0`
- status หลายตารางถูกจำกัดค่าไว้ชัดเจน

ประโยคอธิบาย:

> ผมไม่ได้ปล่อยให้ validation อยู่แค่หน้าเว็บหรือ service layer แต่ให้ database enforce ด้วย เพื่อกันข้อมูลเสียตั้งแต่ต้นทาง

### 5.2 Foreign key behavior

ตัวอย่างที่ควรพูด:

- บางตารางใช้ `ON DELETE RESTRICT` เพราะไม่ควรลบข้อมูลต้นทางถ้ายังมี transaction ผูกอยู่
- บางจุดใช้ `SET NULL` เช่น `technician_id` หรือ `lab_type_id` เพื่อรักษาประวัติเดิมแม้ reference บางตัวเปลี่ยน
- `reservation_participants` ใช้ `ON DELETE CASCADE` เพราะถ้าลบ reservation ก็ต้องลบสมาชิกของ reservation นั้นตาม

### 5.3 Index

มี index ใน field ที่ใช้ query บ่อย เช่น:

- email
- role_id
- lab status
- equipment status
- reservation time
- borrowing status
- maintenance status
- audit created_at

ประโยคอธิบาย:

> index พวกนี้ช่วยรองรับทั้ง transaction query และ report query เพราะระบบไม่ได้มีแค่ insert/update แต่มีการค้นหาและสรุปผลจากหลายตารางตลอด

## 6. จุดขายที่สุดของ database: กันการจองซ้อนเวลา

ระบบนี้กัน reservation overlap สองชั้น

ชั้นที่ 1: service layer
- ใน `reservation_service.py` มีการ query หา reservation ที่ช่วงเวลา overlap ก่อนสร้างรายการใหม่
- ทำให้ตอบ error กลับผู้ใช้ได้เร็วและข้อความชัด

ชั้นที่ 2: PostgreSQL exclusion constraint
- migration `20260409_0002` เพิ่ม constraint:
  - `lab_id WITH =`
  - `tsrange(start_time, end_time, '[)') WITH &&`
  - ใช้กับ status `Pending` และ `Approved`

ประโยคอธิบายหลัก:

> จุดนี้เป็น feature ที่ผมตั้งใจใช้ PostgreSQL ให้คุ้มครับ เพราะถ้าเช็กแค่ใน application อาจกัน race condition ไม่ครบ แต่ exclusion constraint ช่วยรับประกันที่ระดับฐานข้อมูลว่า lab เดียวกันจะไม่ถูกจองเวลาซ้อนกัน

ประโยคสั้นสำหรับกรรมการ:

> ระบบนี้ไม่ได้แค่ตรวจ booking overlap ในโค้ด แต่ enforce ใน PostgreSQL จริงด้วย

## 7. Demo flow แบบเล่าเป็นระบบ

แนะนำให้เดโมตามลำดับนี้

### 7.1 Case 1: เริ่มจาก master data

สิ่งที่พูด:

> ก่อนเกิด transaction ใด ๆ ระบบต้องมี master data ก่อน ได้แก่ roles, lab types, equipment categories, users, labs และ equipments ซึ่งเป็นฐานให้ transaction อื่นอ้างอิงผ่าน foreign keys

สิ่งที่ควรชี้:

- role ของผู้ใช้กำหนดสิทธิ์ระบบ
- ห้องมีประเภทและความจุ
- อุปกรณ์มีหมวดหมู่และสังกัดห้อง

### 7.2 Case 2: การจองห้อง

flow ที่พูด:

1. ผู้ใช้เลือกห้องและช่วงเวลา
2. ระบบเช็กว่าห้องยัง `Available`
3. ระบบเช็ก reservation overlap ใน service layer
4. ถ้าผ่านจึง insert ลง `lab_reservations`
5. ถ้ามีผู้เข้าร่วมหลายคน จะ insert เพิ่มใน `reservation_participants`

สิ่งที่ต้องเน้น:

- reservation เป็น transaction ของห้อง
- participants ทำให้ reservation รองรับกลุ่มได้
- ถ้าจะยกเลิก ใช้การเปลี่ยน status เป็น `Cancelled` ไม่ใช่ลบทิ้ง

ประโยคอธิบาย:

> ผมใช้สถานะแทนการลบ เพราะต้องการเก็บประวัติธุรกรรมไว้สำหรับตรวจสอบย้อนหลังและทำ report ได้

### 7.3 Case 3: การกันเวลาซ้อน

flow ที่พูด:

1. ลองจองห้องเดิมในช่วงเวลาที่ทับกัน
2. service จะ reject ก่อน
3. ถึงแม้มี request ชนกันพร้อมกัน database ก็ยังกันด้วย exclusion constraint

ประโยคอธิบาย:

> นี่คือจุดที่ database ไม่ได้เป็นแค่ storage แต่เป็นตัว enforce business rule สำคัญโดยตรง

### 7.4 Case 4: การยืมอุปกรณ์

flow ที่พูด:

1. Staff เลือกผู้ยืมและอุปกรณ์
2. ระบบเช็กว่าผู้ใช้ active
3. lock row อุปกรณ์ด้วย `with_for_update()`
4. เช็กว่าอุปกรณ์สถานะเป็น `Available`
5. เช็กว่าไม่มี active borrowing และไม่มี open maintenance
6. insert ลง `equipment_borrowings`
7. update สถานะอุปกรณ์ตาม `resolve_equipment_status`
8. เขียน `audit_logs`

ประโยคอธิบาย:

> ฝั่ง borrowing ผมตั้งใจออกแบบให้มีการตรวจทั้งจากตาราง borrowing และ maintenance เพราะอุปกรณ์หนึ่งชิ้นไม่ควรถูกยืมได้ถ้ายังถูกยืมอยู่หรือกำลังซ่อมอยู่

### 7.5 Case 5: การคืนอุปกรณ์

flow ที่พูด:

1. เมื่อคืนของ ระบบ update `actual_return`
2. เปลี่ยน status ใน `equipment_borrowings` เป็น `Returned`
3. ประเมินว่าคืนช้าหรือไม่
4. update สถานะอุปกรณ์กลับตามสภาพจริง
5. เขียน audit log

ถ้าคืนตรงเวลา:

> จะจบที่ update borrowing และปรับสถานะอุปกรณ์กลับเป็น Available

ถ้าคืนช้า:

> ระบบจะสร้าง record ใหม่ใน `penalties` เพิ่มอีกหนึ่ง transaction และส่ง notification ให้ผู้ใช้

### 7.6 Case 6: ค่าปรับ

flow ที่พูด:

1. อ่านจาก `expected_return` เทียบกับ `actual_return`
2. ถ้าคืนช้า คำนวณ fine ตามชั่วโมง
3. insert ลง `penalties`
4. ตั้ง `is_resolved = false`
5. สร้าง `notifications`

สิ่งที่ควรเน้น:

- penalty ไม่ได้อยู่ใน borrowing โดยตรง
- penalty เป็นผลลัพธ์เชิงธุรกิจที่เกิดภายหลังจาก borrowing

ประโยคอธิบาย:

> โครงสร้างแบบนี้ทำให้ผม query ได้ชัดว่ามีการยืมกี่ครั้ง แต่เกิดค่าปรับกี่ครั้ง และรวมยอดค่าปรับต่อคนได้ตรง ๆ

### 7.7 Case 7: การแจ้งซ่อม

flow ที่พูด:

1. ผู้ใช้แจ้งปัญหาอุปกรณ์
2. ระบบสร้าง record ใน `maintenance_records`
3. เปลี่ยนสถานะอุปกรณ์เป็น `In_Repair` ถ้ายังมีงานซ่อมเปิดอยู่
4. เขียน audit log

สิ่งที่ควรเน้น:

- maintenance เป็นอีก transaction stream หนึ่ง แยกจาก borrowing
- แต่ทั้งสอง stream ส่งผลต่อสถานะเดียวกันของ equipment

ประโยคอธิบาย:

> อุปกรณ์เป็น entity กลางที่ได้รับผลจากหลาย transaction คือทั้งการยืมและการซ่อม ดังนั้นผมแยก transaction ออก แต่มี service กลางช่วย resolve status ให้สอดคล้องกัน

### 7.8 Case 8: ช่างอัปเดตสถานะซ่อม

flow ที่พูด:

1. Technician รับงาน
2. update `technician_id` และ `status`
3. ถ้าซ่อมเสร็จ set `resolved_date`
4. ส่ง notification กลับไปยังคนที่แจ้ง
5. อัปเดตสถานะอุปกรณ์ใหม่
6. เขียน audit log

ประโยคอธิบาย:

> ตรงนี้เห็นได้ชัดว่าฐานข้อมูลรองรับ lifecycle ของงานซ่อมครบตั้งแต่แจ้ง, รับงาน, ดำเนินการ, ไปจนถึงปิดงาน

### 7.9 Case 9: Notification และ Audit

สิ่งที่พูด:

> ตาราง notifications ใช้สื่อสารกับผู้ใช้ เช่น มีค่าปรับหรือซ่อมเสร็จ ส่วน audit_logs ใช้เก็บว่าใครทำ action อะไรกับข้อมูลใด ทำให้ระบบตรวจสอบย้อนหลังได้

เคสที่ยกตัวอย่างได้:

- ยืมอุปกรณ์
- คืนอุปกรณ์
- แจ้งซ่อม
- อัปเดตงานซ่อม

## 8. SQL reports ที่ควรเล่าให้ครบ

ระบบมี advanced SQL reports 5 รายการ ซึ่งเหมาะมากสำหรับอธิบายว่า relational schema นี้ไม่ใช่แค่เก็บข้อมูล แต่ดึง insight ได้จริง

### 8.1 Late Borrowings

ตารางที่ใช้:
- `equipment_borrowings`
- `users`
- `equipments`
- `labs`
- `penalties`

สิ่งที่โชว์:
- ใครคืนช้า
- ยืมอุปกรณ์อะไร
- อยู่ห้องไหน
- ค้างกี่ชั่วโมง
- มีค่าปรับเท่าไร

SQL concept:
- JOIN
- LEFT JOIN
- WHERE แบบมี OR
- คำนวณเวลา lateness

### 8.2 Top Borrowers

ตารางที่ใช้:
- `users`
- `roles`
- `equipment_borrowings`
- `penalties`

สิ่งที่โชว์:
- คนที่ยืมบ่อยที่สุด
- จำนวนครั้งที่ยืม
- จำนวน penalty
- ยอดค่าปรับรวม

SQL concept:
- GROUP BY
- HAVING
- COUNT DISTINCT
- SUM

### 8.3 Lab Utilization

ตารางที่ใช้:
- `labs`
- `lab_types`
- `lab_reservations`
- `equipments`

สิ่งที่โชว์:
- ห้องไหนถูกใช้บ่อย
- ประเภทห้อง
- จำนวนการจองทั้งหมด
- จำนวน approved reservation
- จำนวนอุปกรณ์ในห้อง

SQL concept:
- GROUP BY
- conditional COUNT
- aggregation ข้ามหลายตาราง

### 8.4 Equipment Repairs

ตารางที่ใช้:
- `equipments`
- `equipment_categories`
- `labs`
- `maintenance_records`

สิ่งที่โชว์:
- อุปกรณ์ไหนซ่อมบ่อย
- อยู่หมวดอะไร
- อยู่ห้องไหน
- มี open repairs กี่งาน
- ล่าสุดแจ้งเมื่อไร

SQL concept:
- GROUP BY
- COUNT
- MAX
- conditional COUNT

### 8.5 Reservation Summary

ตารางที่ใช้:
- `lab_reservations`
- `labs`
- `users`
- `reservation_participants`

สิ่งที่โชว์:
- รายละเอียดการจองแต่ละรายการ
- คนจองคือใคร
- ห้องไหน
- มีผู้เข้าร่วมกี่คน
- ใช้เวลานานกี่ชั่วโมง

SQL concept:
- GROUP BY
- COUNT
- computed column จากเวลาต่างกัน

ประโยคสรุปส่วน reports:

> รายงานทั้ง 5 ตัวนี้สะท้อนว่าฐานข้อมูลถูกออกแบบให้ query เชิงวิเคราะห์ได้จริง เพราะมี foreign key และการแยกตารางที่ถูกต้องตั้งแต่แรก

## 9. เหตุผลที่เลือก PostgreSQL

ประโยคที่ตอบได้เลย:

> ผมเลือก PostgreSQL เพราะรองรับ relational constraints ได้แข็งแรง, มี type และ feature ที่เหมาะกับ transaction system และที่สำคัญคือรองรับ exclusion constraint ซึ่งผมใช้กันการจองห้องเวลาซ้อนกันโดยตรงในฐานข้อมูล

ถ้าถูกถามว่าทำไมไม่ใช้แค่ diagram:

> diagram ใช้สื่อสารโครงสร้าง แต่ของจริงที่ระบบรันคือ PostgreSQL schema และ migration ซึ่งมีรายละเอียดบังคับใช้มากกว่า เช่น check constraints, indexes, on delete behavior และ exclusion constraint

## 10. เหตุผลเชิงออกแบบที่กรรมการมักถาม

### ทำไมต้องแยก `penalties`

> เพราะค่าปรับไม่ได้เกิดทุกการยืม และมี attribute ของตัวเอง เช่น fine amount และ resolved status ถ้าไปรวมกับ borrowing จะทำให้ schema ปนกันและขยายยาก

### ทำไมต้องมี `reservation_participants`

> เพราะ reservation หนึ่งรายการมีผู้เข้าร่วมได้หลายคน และผู้ใช้คนหนึ่งก็เข้าหลาย reservation ได้ จึงเป็น many-to-many ที่ควรแยก junction table

### ทำไมไม่ลบ record ที่ยกเลิกหรือเสร็จแล้ว

> เพราะระบบนี้เป็น transaction system ต้องเก็บประวัติไว้ใช้ตรวจสอบย้อนหลังและทำรายงาน

### ทำไมเช็ก overlap ทั้ง service และ database

> service ให้ error message ที่เป็นมิตรและตอบเร็ว ส่วน database ช่วยรับประกันความถูกต้องจริงในกรณี concurrent requests

### ทำไม equipment status ไม่คงที่จากตารางเดียว

> เพราะสถานะอุปกรณ์ได้รับผลจากหลาย transaction ทั้ง borrowing และ maintenance จึงต้องมี service คอย resolve ตามสภาวะปัจจุบันของข้อมูล

## 11. ลำดับการเดโมที่แนะนำจริง

ถ้ามีเวลาประมาณ 5-7 นาที ให้เล่าตามนี้:

1. เปิด ER diagram หรือ schema overview
2. ชี้ 4 กลุ่มตาราง: lookup, core, transaction, supporting
3. อธิบาย relation หลัก 5-6 จุด
4. โฟกัส reservation และโชว์จุดกันเวลา overlap
5. ต่อด้วย borrowing -> return -> penalty -> notification
6. ต่อด้วย maintenance -> technician update -> equipment status
7. ปิดท้ายด้วย advanced SQL reports 5 ตัว
8. สรุปว่าฐานข้อมูลเป็นตัว enforce business rules จริง

ถ้ามีเวลาสั้นมาก 2-3 นาที:

1. ระบบนี้มี master data + transaction data + supporting data ครบ
2. จุดเด่นคือ reservation overlap ถูกกันทั้งใน service และ PostgreSQL exclusion constraint
3. borrowing เชื่อมต่อไปถึง penalty, notification และ audit log
4. maintenance มี lifecycle ครบและกระทบ equipment status
5. มี SQL reports จากหลายตารางจริง ไม่ใช่ query จากตารางเดียว

## 12. Closing statement

ประโยคปิดที่ใช้ได้ทันที:

> สรุปคือฐานข้อมูลของระบบนี้ไม่ได้ถูกออกแบบมาเพื่อเก็บข้อมูลเฉย ๆ แต่ถูกออกแบบให้รองรับ workflow จริงของระบบงาน โดยใช้ relational schema, foreign keys, constraints, many-to-many relation, audit trail, และ SQL reporting ร่วมกัน ทำให้ database เป็นแกนกลางของทั้งความถูกต้องของข้อมูลและการวิเคราะห์ข้อมูลครับ

## 13. ไฟล์อ้างอิงในโปรเจกต์

- [sql/schema.sql](/abs/path/C:/Users/saifa/Desktop/cn230/sql/schema.sql:1)
- [migrations/versions/20260409_0002_reservation_exclusion_constraint.py](/abs/path/C:/Users/saifa/Desktop/cn230/migrations/versions/20260409_0002_reservation_exclusion_constraint.py:1)
- [app/services/reservation_service.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/services/reservation_service.py:1)
- [app/services/borrowing_service.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/services/borrowing_service.py:1)
- [app/services/maintenance_service.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/services/maintenance_service.py:1)
- [app/api/routers/reports.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/api/routers/reports.py:1)
- [scripts/seed_demo.py](/abs/path/C:/Users/saifa/Desktop/cn230/scripts/seed_demo.py:1)
