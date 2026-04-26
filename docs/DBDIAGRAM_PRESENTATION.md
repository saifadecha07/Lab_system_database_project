# Database Diagram For `dbdiagram.io`

คัดลอกบล็อกด้านล่างไปวางใน `dbdiagram.io` ได้เลย

```dbml
Table roles {
  role_id int [pk, increment]
  role_name varchar(50) [not null, unique]
}

Table users {
  user_id int [pk, increment]
  role_id int [not null, ref: > roles.role_id]
  email varchar(150) [not null, unique]
  first_name varchar(100) [not null]
  last_name varchar(100) [not null]
  password_hash varchar(255) [not null]
  is_active boolean [not null, default: true]
  created_at timestamptz [not null]
  updated_at timestamptz [not null]
}

Table lab_types {
  lab_type_id int [pk, increment]
  type_name varchar(100) [not null, unique]
}

Table labs {
  lab_id int [pk, increment]
  lab_type_id int [ref: > lab_types.lab_type_id]
  room_name varchar(100) [not null, unique]
  capacity int [not null]
  status varchar(50) [not null, default: 'Available']
  created_at timestamptz [not null]
  updated_at timestamptz [not null]
}

Table equipment_categories {
  category_id int [pk, increment]
  category_name varchar(100) [not null, unique]
}

Table equipments {
  equipment_id int [pk, increment]
  category_id int [ref: > equipment_categories.category_id]
  lab_id int [ref: > labs.lab_id]
  equipment_name varchar(150) [not null]
  status varchar(50) [not null, default: 'Available']
  created_at timestamptz [not null]
  updated_at timestamptz [not null]
}

Table lab_reservations {
  reservation_id int [pk, increment]
  lab_id int [not null, ref: > labs.lab_id]
  reserved_by int [not null, ref: > users.user_id]
  start_time timestamptz [not null]
  end_time timestamptz [not null]
  status varchar(50) [not null, default: 'Pending']
  created_at timestamptz [not null]
  updated_at timestamptz [not null]
}

Table reservation_participants {
  reservation_id int [pk, ref: > lab_reservations.reservation_id]
  user_id int [pk, ref: > users.user_id]
}

Table equipment_borrowings {
  borrow_id int [pk, increment]
  user_id int [not null, ref: > users.user_id]
  equipment_id int [not null, ref: > equipments.equipment_id]
  borrow_time timestamptz [not null]
  expected_return timestamptz [not null]
  actual_return timestamptz
  status varchar(50) [not null, default: 'Borrowed']
  created_at timestamptz [not null]
  updated_at timestamptz [not null]
}

Table maintenance_records {
  repair_id int [pk, increment]
  equipment_id int [not null, ref: > equipments.equipment_id]
  reported_by int [not null, ref: > users.user_id]
  technician_id int [ref: > users.user_id]
  report_date timestamptz [not null]
  resolved_date timestamptz
  issue_detail text [not null]
  status varchar(50) [not null, default: 'Reported']
  created_at timestamptz [not null]
  updated_at timestamptz [not null]
}

Table penalties {
  penalty_id int [pk, increment]
  user_id int [not null, ref: > users.user_id]
  borrow_id int [not null, ref: > equipment_borrowings.borrow_id]
  fine_amount numeric(10,2) [not null]
  is_resolved boolean [not null, default: false]
  created_at timestamptz [not null]
  updated_at timestamptz [not null]
}

Table notifications {
  notification_id int [pk, increment]
  user_id int [not null, ref: > users.user_id]
  message text [not null]
  is_read boolean [not null, default: false]
  created_at timestamptz [not null]
  updated_at timestamptz [not null]
}

Table audit_logs {
  audit_log_id int [pk, increment]
  actor_user_id int [ref: > users.user_id]
  action varchar(100) [not null]
  target_type varchar(50)
  target_id int
  details jsonb
  created_at timestamptz [not null]
}
```

## จุดสำคัญที่ควรพูดตอนพรีเซนต์

ระบบนี้ออกแบบเป็น 4 กลุ่มตารางหลัก

1. ตารางอ้างอิงหรือ lookup
- `roles`
- `lab_types`
- `equipment_categories`

หน้าที่คือเก็บค่ามาตรฐานที่ถูกใช้อ้างอิงซ้ำ ทำให้ข้อมูลไม่กระจัดกระจายและลดการพิมพ์ค่าซ้ำผิดกัน

2. ตารางหลักของระบบ
- `users`
- `labs`
- `equipments`

กลุ่มนี้คือ master data ของระบบ ผู้ใช้ ห้องปฏิบัติการ และอุปกรณ์ ซึ่งเป็นศูนย์กลางให้ transaction อื่นมาเชื่อมต่อ

3. ตารางธุรกรรม
- `lab_reservations`
- `reservation_participants`
- `equipment_borrowings`
- `maintenance_records`

กลุ่มนี้เก็บเหตุการณ์ที่เกิดขึ้นจริงในระบบ เช่น การจองห้อง การยืมอุปกรณ์ และการแจ้งซ่อม

4. ตารางสนับสนุนและการตรวจสอบย้อนหลัง
- `penalties`
- `notifications`
- `audit_logs`

ใช้รองรับฟังก์ชันจริงในระบบ เช่น ค่าปรับ การแจ้งเตือน และการเก็บประวัติการกระทำเพื่อความโปร่งใส

## ความสัมพันธ์ที่ควรอธิบาย

### 1) `roles` -> `users`
- 1 role มีผู้ใช้หลายคน
- ผู้ใช้แต่ละคนมี role เดียว

ใช้รองรับการแบ่งสิทธิ์ เช่น Student, Staff, Technician, Admin

### 2) `lab_types` -> `labs`
- 1 ประเภทห้อง มีได้หลายห้อง
- ห้องหนึ่งอยู่ได้ในประเภทเดียว

ช่วยจัดหมวดหมู่ห้อง เช่น Computer Lab, Science Lab

### 3) `labs` -> `equipments`
- 1 ห้องมีอุปกรณ์หลายชิ้น
- อุปกรณ์แต่ละชิ้นสังกัดห้องได้ 1 ห้อง

ทำให้รู้ว่าอุปกรณ์อยู่ที่ไหนและรายงานตามห้องได้

### 4) `users` -> `lab_reservations`
- ผู้ใช้ 1 คนจองได้หลายครั้ง
- การจองแต่ละครั้งมีผู้จองหลัก 1 คน

ใช้เก็บเจ้าของรายการจอง

### 5) `lab_reservations` <-> `users` ผ่าน `reservation_participants`
- เป็นความสัมพันธ์ many-to-many
- การจอง 1 ครั้งมีผู้เข้าร่วมหลายคนได้
- ผู้ใช้ 1 คนเข้าร่วมได้หลายการจอง

ตารางเชื่อมนี้สำคัญ เพราะการจองห้องเรียนหรือห้องแล็บมักไม่ได้มีแค่คนจองคนเดียว

### 6) `users` -> `equipment_borrowings` และ `equipments` -> `equipment_borrowings`
- ผู้ใช้ 1 คนยืมได้หลายครั้ง
- อุปกรณ์ 1 ชิ้นถูกยืมได้หลายครั้งในช่วงเวลาต่างกัน

ตารางนี้เป็นหัวใจของระบบยืมคืน เพราะเก็บทั้งเวลายืม กำหนดคืน เวลาคืนจริง และสถานะ

### 7) `equipment_borrowings` -> `penalties`
- รายการยืม 1 รายการอาจมีค่าปรับ 0 หรือ 1 หรือมากกว่าได้ตามกติกาที่ระบบต้องการ
- ค่าปรับยังเชื่อมกับ `users` โดยตรงด้วย เพื่อสรุปยอดค่าปรับรายคนได้ง่าย

จุดนี้เอาไว้สนับสนุนรายงานเชิงวิเคราะห์ เช่น ค่าปรับรายบุคคล

### 8) `equipments` -> `maintenance_records`
- อุปกรณ์ 1 ชิ้นมีประวัติการซ่อมได้หลายครั้ง
- แต่ละรายการซ่อมมีผู้แจ้ง และอาจมีช่างผู้รับผิดชอบ

ตรงนี้แสดงว่าระบบไม่ได้แค่ยืมคืน แต่ดูแล lifecycle ของอุปกรณ์ด้วย

### 9) `users` -> `notifications`
- ผู้ใช้ 1 คนมีการแจ้งเตือนได้หลายรายการ

ใช้ส่งข้อความเตือน เช่น ใกล้กำหนดคืน หรือมีค่าปรับ

### 10) `users` -> `audit_logs`
- เก็บว่าใครทำอะไรกับข้อมูลไหน เมื่อไร

ช่วยเรื่องการตรวจสอบย้อนหลังและความน่าเชื่อถือของระบบ

## Constraints ที่ควรพูดให้ดูมีน้ำหนัก

ในฐานข้อมูลนี้ไม่ได้มีแค่ PK/FK แต่ยังมี business rules ระดับฐานข้อมูลด้วย

- `users.email` เป็น `unique`
- `labs.room_name` เป็น `unique`
- `capacity > 0`
- มีการจำกัดค่า `status` หลายตาราง เช่น ห้อง อุปกรณ์ การยืม การซ่อม
- `lab_reservations` บังคับว่า `end_time > start_time`
- `penalties.fine_amount > 0`

ประโยชน์คือช่วยกันข้อมูลผิดตั้งแต่ระดับฐานข้อมูล ไม่ต้องพึ่งแค่ฝั่งหน้าเว็บหรือ backend

## จุดเด่นของ schema ล่าสุด

เวอร์ชันล่าสุดมี PostgreSQL exclusion constraint เพิ่มใน `lab_reservations`

แนวคิดคือ:
- ห้องเดียวกัน
- ช่วงเวลาเดียวกันหรือซ้อนทับกัน
- และสถานะยังเป็น `Pending` หรือ `Approved`

จะไม่สามารถจองทับกันได้

ข้อดีคือป้องกันการ double booking ได้ตรงที่ฐานข้อมูลเลย ต่อให้มีหลาย request เข้ามาพร้อมกันก็ยังคุมได้ดีกว่าการเช็กเฉพาะในโค้ด

หมายเหตุ:
- constraint นี้อยู่ใน migration `20260409_0002`
- `dbdiagram.io` วาดความสัมพันธ์ได้ แต่ไม่สามารถแสดง exclusion constraint แบบ PostgreSQL ได้ครบ จึงควรอธิบายด้วยปากตอนพรีเซนต์

## สคริปต์พูดสั้นๆ ตอนพรีเซนต์

"ฐานข้อมูลของระบบ Smart Lab Management System ถูกออกแบบแบบ relational โดยแยกเป็น lookup tables, master tables, transaction tables และ support tables อย่างชัดเจน เพื่อให้ข้อมูลไม่ซ้ำและขยายระบบได้ง่าย

ตารางหลักคือ users, labs และ equipments จากนั้นมี transaction สำคัญคือ lab_reservations สำหรับการจองห้อง และ equipment_borrowings สำหรับการยืมอุปกรณ์ ส่วน reservation_participants ใช้แก้ปัญหา many-to-many เพราะ 1 การจองมีผู้เข้าร่วมได้หลายคน

นอกจากนี้ยังมี maintenance_records สำหรับประวัติการซ่อม, penalties สำหรับค่าปรับ, notifications สำหรับการแจ้งเตือน และ audit_logs สำหรับการตรวจสอบย้อนหลัง

จุดเด่นของ schema นี้คือมีทั้ง primary key, foreign key, unique, check constraint และยังมี exclusion constraint ของ PostgreSQL เพื่อป้องกันการจองห้องซ้อนเวลา ทำให้ฐานข้อมูลช่วย enforce business rules ได้จริง ไม่ได้เป็นแค่ที่เก็บข้อมูลอย่างเดียว" 

## อ้างอิงที่ใช้สร้างไฟล์นี้

- [sql/schema.sql](/abs/path/C:/Users/saifa/Desktop/cn230/sql/schema.sql:1)
- [migrations/versions/20260409_0002_reservation_exclusion_constraint.py](/abs/path/C:/Users/saifa/Desktop/cn230/migrations/versions/20260409_0002_reservation_exclusion_constraint.py:1)
