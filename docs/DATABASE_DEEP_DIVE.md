# Database Deep Dive

เอกสารนี้ใช้ตอบคำถาม database แบบลึก ตั้งแต่เหตุผลการแยกตารางจนถึง constraint สำคัญ

## 1. Database philosophy

ฐานข้อมูลของโปรเจกต์นี้ออกแบบให้เป็น relational schema ที่ลดข้อมูลซ้ำและสะท้อนธุรกรรมจริงของระบบ

หลักคิดคือ:

- ค่ามาตรฐานที่ใช้ซ้ำควรอยู่ใน lookup tables
- ข้อมูลหลักควรแยกจากเหตุการณ์ธุรกรรม
- many-to-many ต้องมี junction table
- business rules สำคัญควร enforce ที่ database ด้วย ไม่ใช่แค่ใน UI

## 2. ตารางทั้งหมดในระบบ

จาก [sql/schema.sql](/abs/path/C:/Users/saifa/Desktop/cn230/sql/schema.sql:1)

Lookup tables:
- `roles`
- `lab_types`
- `equipment_categories`

Core tables:
- `users`
- `labs`
- `equipments`

Transaction tables:
- `lab_reservations`
- `reservation_participants`
- `equipment_borrowings`
- `maintenance_records`

Support tables:
- `penalties`
- `notifications`
- `audit_logs`

## 3. เหตุผลของแต่ละกลุ่มตาราง

### Lookup tables

เหตุผลที่ต้องแยก:

- ป้องกันการพิมพ์ข้อความซ้ำผิดกัน
- ใช้ foreign key เชื่อมได้
- เปลี่ยนค่ากลางได้ง่าย

ตัวอย่าง:
- role ไม่ควรพิมพ์เป็น string ลอยทุกแถวใน `users`
- ประเภทห้องและหมวดอุปกรณ์ควรจัดมาตรฐานไว้

### Core tables

`users`, `labs`, `equipments` เป็นข้อมูลหลักที่ transaction อื่นมาอ้างอิง

ถ้าไม่มีสามตารางนี้ ระบบจะไม่รู้ว่า:

- ใครเป็นผู้ใช้
- ห้องมีอะไรบ้าง
- อุปกรณ์อยู่ที่ไหน

### Transaction tables

เป็นหัวใจของระบบงานจริง

- `lab_reservations` เก็บการจองห้อง
- `equipment_borrowings` เก็บการยืมคืน
- `maintenance_records` เก็บประวัติซ่อม
- `reservation_participants` แก้ปัญหา many-to-many

### Support tables

- `penalties` รองรับกติกาคืนช้า
- `notifications` รองรับการแจ้งเตือน
- `audit_logs` รองรับการตรวจสอบย้อนหลัง

## 4. ความสัมพันธ์หลักที่ควรอธิบาย

### `roles` 1:N `users`

ผู้ใช้แต่ละคนมี role เดียว แต่ role หนึ่งมีผู้ใช้หลายคน

### `lab_types` 1:N `labs`

ช่วยจัดประเภทห้องแล็บ

### `labs` 1:N `equipments`

อุปกรณ์สังกัดห้องได้ ทำให้รายงานตามห้องได้

### `users` 1:N `lab_reservations`

ผู้ใช้หนึ่งคนจองได้หลายครั้ง

### `lab_reservations` M:N `users` ผ่าน `reservation_participants`

นี่เป็นจุดที่ตอบเรื่อง many-to-many ได้ชัดที่สุด

เหตุผล:
- ผู้จองหลักมีได้ 1 คน
- แต่ผู้เข้าร่วมจริงอาจมีหลายคน
- ผู้ใช้คนหนึ่งก็เข้าร่วมได้หลาย reservation

### `users` 1:N `equipment_borrowings`

ผู้ใช้หนึ่งคนยืมอุปกรณ์ได้หลายครั้ง

### `equipments` 1:N `equipment_borrowings`

อุปกรณ์หนึ่งชิ้นมีประวัติการยืมหลายครั้งตามเวลา

### `equipments` 1:N `maintenance_records`

อุปกรณ์หนึ่งชิ้นเสียและซ่อมได้หลายครั้ง

### `equipment_borrowings` 1:N `penalties`

ในเชิงโครงสร้างเปิดให้รองรับหลาย penalty ได้ แม้ flow ปัจจุบันจะสร้างได้อย่างมากหนึ่งรายการต่อการคืนช้าแต่ละครั้ง

### `users` 1:N `notifications`

ผู้ใช้คนหนึ่งมีการแจ้งเตือนหลายรายการได้

### `users` 1:N `audit_logs`

เก็บว่าใครทำ action อะไรกับ entity ไหน

## 5. เหตุผลที่ไม่รวมทุกอย่างไว้ตารางเดียว

ถ้ารวมข้อมูลห้อง, อุปกรณ์, การยืม, การซ่อม, ค่าปรับ ไว้ตารางเดียว จะเกิดปัญหา:

- ข้อมูลซ้ำมาก
- update anomaly
- delete anomaly
- query ยาก
- ขยายระบบลำบาก

ดังนั้นการแยกตารางทำให้ schema maintainable และตอบหลัก normalization ได้ดีกว่า

## 6. Constraints สำคัญ

### Primary keys

ทุกตารางหลักมี primary key ของตัวเอง เช่น

- `user_id`
- `lab_id`
- `equipment_id`
- `reservation_id`
- `borrow_id`
- `repair_id`

ส่วน `reservation_participants` ใช้ composite primary key คือ

- `reservation_id`
- `user_id`

### Foreign keys

foreign key ทำให้ referential integrity แข็งแรง เช่น:

- reservation ต้องอ้างถึง lab ที่มีอยู่จริง
- borrowing ต้องอ้างถึง user และ equipment จริง
- penalty ต้องอ้างถึง borrowing จริง

### Unique constraints

จุดที่สำคัญ:

- `users.email`
- `labs.room_name`
- `roles.role_name`
- `lab_types.type_name`
- `equipment_categories.category_name`

### Check constraints

จุดสำคัญ:

- `capacity > 0`
- `end_time > start_time`
- `fine_amount > 0`
- จำกัดค่า status หลายตาราง

## 7. ทำไม fixed slots สำคัญ

จาก [app/schemas/reservations.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/schemas/reservations.py:1)

ระบบไม่ได้เปิดให้จองเวลาตามใจ แต่บังคับให้จองเฉพาะ:

- `08:00-12:00`
- `12:00-16:00`
- `16:00-20:00`

ข้อดี:

- ใช้งานง่าย
- demo ง่าย
- availability คำนวณง่าย
- ลดความซับซ้อนของการจัดตาราง
- สอดคล้องกับการใช้งานแบบห้องเรียนหรือแล็บในมหาวิทยาลัย

## 8. การกัน reservation overlap

นี่เป็นจุดเด่นสำคัญของ schema

ชั้นที่ 1:
- service layer เช็ก overlap ก่อนบันทึก

ชั้นที่ 2:
- PostgreSQL มี exclusion constraint เพิ่มจาก migration ล่าสุด

จาก [migrations/versions/20260409_0002_reservation_exclusion_constraint.py](/abs/path/C:/Users/saifa/Desktop/cn230/migrations/versions/20260409_0002_reservation_exclusion_constraint.py:1)

แนวคิดคือ:

- ห้องเดียวกัน
- เวลาซ้อนกัน
- status ยัง active (`Pending`, `Approved`)

จะไม่สามารถบันทึกได้

ข้อดีคือช่วยกัน race condition ได้ดีกว่าการเช็กเฉพาะในโค้ด

## 9. การคิดค่าปรับ

จาก [app/services/penalty_service.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/services/penalty_service.py:1)

หลักการ:

- ถ้าคืนตรงเวลาหรือก่อนเวลา => ไม่มีค่าปรับ
- ถ้าคืนช้า => คิดตามจำนวนชั่วโมง
- ปัดขึ้นอย่างน้อย 1 ชั่วโมง
- อัตราปรับต่อชั่วโมงมาจาก config

ตอนนี้ค่า default คือ `25` บาทต่อชั่วโมง

## 10. การเก็บ audit log

`audit_logs` เป็นตารางที่ช่วยตอบอาจารย์ในมุม governance และ traceability

ตัวอย่าง action ที่ถูก log:

- `equipment.borrowed`
- `equipment.returned`
- `maintenance.reported`
- `maintenance.updated`
- `lab.created`
- `user.role_changed`

ทำให้ระบบตรวจสอบย้อนหลังได้ว่าใครทำอะไร เมื่อไร

## 11. Database design ที่ตอบโจทย์วิชา

ระบบนี้มีองค์ประกอบสำคัญของวิชา database ครบหลายด้าน

- relational schema
- PK/FK
- constraints
- many-to-many relation
- transaction tables
- migration
- real SQL reports
- PostgreSQL-specific feature

## 12. ประโยคสรุปสำหรับตอบอาจารย์

"ฐานข้อมูลนี้ออกแบบโดยแยกข้อมูลอ้างอิง, ข้อมูลหลัก, ธุรกรรม และข้อมูลสนับสนุนออกจากกันอย่างชัดเจน เพื่อให้ลดข้อมูลซ้ำและรองรับ business rules จริงของระบบ เช่น การจองห้องห้ามเวลาซ้อน, การยืมคืนมีค่าปรับ, และการซ่อมมีประวัติย้อนหลัง พร้อมทั้งมี advanced SQL reports ที่ดึงค่าจากหลายตารางจริง"

## แหล่งอ้างอิง

- [sql/schema.sql](/abs/path/C:/Users/saifa/Desktop/cn230/sql/schema.sql:1)
- [app/schemas/reservations.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/schemas/reservations.py:1)
- [app/services/penalty_service.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/services/penalty_service.py:1)
- [migrations/versions/20260409_0002_reservation_exclusion_constraint.py](/abs/path/C:/Users/saifa/Desktop/cn230/migrations/versions/20260409_0002_reservation_exclusion_constraint.py:1)
