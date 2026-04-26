# Project Story From Zero

เอกสารนี้ใช้เล่าโปรเจกต์ตั้งแต่ปัญหาเริ่มต้นจนกลายเป็นระบบที่ส่งงานได้จริง

## 1. จุดเริ่มต้นของโปรเจกต์

โจทย์ของระบบนี้คือการจัดการห้องปฏิบัติการและอุปกรณ์ในบริบทมหาวิทยาลัยหรือรายวิชา โดยปัญหาหลักที่พบในงานลักษณะนี้มีหลายอย่าง

- การจองห้องชนกัน
- ไม่รู้ว่าอุปกรณ์อยู่ที่ไหนหรือถูกยืมไปหรือยัง
- เมื่ออุปกรณ์เสีย ไม่มีประวัติการแจ้งซ่อมและติดตามสถานะได้ยาก
- การคืนของล่าช้าทำให้การคิดค่าปรับไม่เป็นระบบ
- อาจารย์หรือเจ้าหน้าที่อยากดูรายงานจากฐานข้อมูลจริง ไม่ใช่แค่หน้าบ้านสวยๆ

ดังนั้นระบบนี้จึงถูกออกแบบให้เป็นมากกว่า CRUD ธรรมดา แต่เป็นระบบที่มี transaction จริง, business rules จริง, role-based access control, และฐานข้อมูล PostgreSQL ที่ enforce กฎสำคัญได้จริง

## 2. เป้าหมายของระบบ

เป้าหมายหลักของโปรเจกต์นี้คือสร้าง Smart Lab Management System ที่มีองค์ประกอบครบในเชิงวิชา database systems และใช้งานได้ในเชิงระบบงานจริง

เป้าหมายที่ระบบต้องตอบให้ได้:

- มี relational database ที่ออกแบบเป็นระบบ
- มี primary key, foreign key, unique, check constraints
- มี web application ที่เชื่อมกับฐานข้อมูลจริง
- รองรับผู้ใช้หลายบทบาท
- มี transaction สำคัญ เช่น จองห้อง, ยืมอุปกรณ์, แจ้งซ่อม, คืนอุปกรณ์
- มี advanced SQL reports อย่างน้อย 5 รายการ
- มีการควบคุมสิทธิ์และความปลอดภัยในระดับที่สมเหตุสมผล

## 3. ทำไมเลือกทำเป็นระบบนี้

โปรเจกต์นี้เหมาะกับรายวิชา database เพราะมีทั้ง master data, transaction data, many-to-many relation, audit trail, และ analytic reports อยู่ในระบบเดียว

ข้อดีของโจทย์นี้คืออธิบาย database design ได้ชัดมาก เช่น

- ทำไมต้องมี lookup tables
- ทำไม reservation ต้องมี participant table
- ทำไม borrowing ต้องแยก penalty ออกอีกตาราง
- ทำไม maintenance ต้องแยกจาก equipment
- ทำไมต้องมี audit_logs

## 4. แนวคิดการพัฒนา

แนวคิดของระบบนี้คือแบ่งปัญหาออกเป็น 4 ชั้น

1. ข้อมูลอ้างอิง
- roles
- lab_types
- equipment_categories

2. ข้อมูลหลัก
- users
- labs
- equipments

3. ธุรกรรมหลัก
- lab_reservations
- reservation_participants
- equipment_borrowings
- maintenance_records

4. ฟีเจอร์สนับสนุน
- penalties
- notifications
- audit_logs

แนวคิดนี้ช่วยให้ระบบขยายได้ง่าย และสามารถอธิบาย normalisation ได้ชัดเจน

## 5. การตัดสินใจด้านเทคโนโลยี

ระบบนี้เลือกใช้:

- FastAPI สำหรับ web API
- SQLAlchemy ORM สำหรับเชื่อมฐานข้อมูล
- PostgreSQL เป็นฐานข้อมูลหลัก
- Alembic สำหรับ migrations
- Jinja2 + Vanilla JavaScript สำหรับหน้าเว็บ

เหตุผลที่เลือกชุดนี้:

- FastAPI ทำให้สร้าง API ได้เร็วและมี schema ชัด
- SQLAlchemy ช่วย map database กับ business logic ได้ดี
- PostgreSQL รองรับ constraint และ feature เชิง relational ได้แข็งแรง
- Alembic ทำให้ schema versioning เป็นระบบ
- หน้าเว็บแบบเรียบง่ายช่วยเน้นที่ logic และ database มากกว่าความซับซ้อนของ frontend framework

## 6. วิธีคิดเรื่องผู้ใช้และบทบาท

ระบบรองรับผู้ใช้ 4 บทบาท:

- `Student`
- `Staff`
- `Technician`
- `Admin`

เหตุผลที่แยกแบบนี้:

- `Student` เป็นผู้ใช้งานหลัก: จองห้อง, ดูรายการตัวเอง, ดูค่าปรับ, ดูแจ้งเตือน
- `Staff` ดูภาพรวมผู้ใช้และจัดการงานยืมคืน รวมถึงดู reports
- `Technician` รับงานซ่อมและอัปเดตสถานะซ่อม
- `Admin` ดูแลข้อมูลหลักและสิทธิ์ผู้ใช้

การแยก role แบบนี้ทำให้ระบบมีความสมจริงมากกว่าให้ทุกคนทำได้ทุกอย่าง

## 7. Workflow หลักที่ทำให้โปรเจกต์นี้เป็น "ระบบงานจริง"

### การสมัครและเข้าสู่ระบบ

- ผู้ใช้สมัครผ่าน `/auth/register`
- ระบบกำหนด role เริ่มต้นเป็น `Student`
- เข้าสู่ระบบผ่าน session-based auth
- ทุก request ที่แก้ไขข้อมูลต้องผ่าน CSRF check

### การจองห้อง

- ผู้ใช้เลือกวันที่
- ระบบแสดง availability ตาม fixed time slots
- ผู้ใช้จองได้เฉพาะช่วง `08:00-12:00`, `12:00-16:00`, `16:00-20:00`
- ระบบกันเวลา overlap ทั้งใน service layer และ database layer

### การยืมอุปกรณ์

- Staff/Admin เป็นผู้สร้างรายการยืม
- ต้องเช็กว่าอุปกรณ์ยัง available
- ต้องไม่มี active borrowing
- ต้องไม่มี open maintenance
- ตอนคืน ระบบจะคำนวณค่าปรับถ้าคืนช้า

### การซ่อมอุปกรณ์

- ผู้ใช้แจ้งซ่อมได้
- Technician/Admin อัปเดตสถานะได้
- เมื่อซ่อมเสร็จ ระบบแจ้งเตือนผู้แจ้ง
- status ของ equipment ถูก derive จากสถานะการยืมและการซ่อม

### การรายงาน

- Staff/Admin สามารถเปิดรายงาน SQL 5 รายการ
- รายงานมาจาก query จริงแบบ join/group by ไม่ใช่ mock data

## 8. จุดที่ทำให้โปรเจกต์นี้ตอบอาจารย์ได้ดี

โปรเจกต์นี้ไม่ใช่แค่มีตารางครบ แต่มีการออกแบบกฎธุรกิจลงไปในหลายชั้น

- ที่ UI มีการจำกัด input
- ที่ schema/Pydantic มีการ validate
- ที่ service layer มีการเช็ก business logic
- ที่ PostgreSQL มี constraints จริง

แนวคิดนี้สำคัญมาก เพราะเป็นการออกแบบแบบ defense in depth

## 9. จุดเด่นด้านฐานข้อมูล

สิ่งที่ตอบในมุม database ได้ชัด:

- มี lookup tables ลดข้อมูลซ้ำ
- มี transaction tables ที่แยกตามเหตุการณ์
- มี junction table สำหรับ many-to-many
- มี check constraints, unique constraints, FK
- มี exclusion constraint ป้องกันจองห้องเวลา overlap
- มี SQL reports เชิงวิเคราะห์จากหลายตาราง

## 10. จุดเด่นด้านระบบ

- มี readiness check ตรวจ schema จริง
- มี audit logging
- มี notifications
- มี role-based access control
- มี CSRF protection
- มี login rate limiting
- มี tests ครอบคลุม flow สำคัญ

## 11. ถ้าจะเล่าเป็นประโยคเดียว

"โปรเจกต์นี้เริ่มจากปัญหาการจัดการห้องแล็บและอุปกรณ์ที่มักเกิดข้อมูลชนกัน ติดตามยาก และตรวจสอบย้อนหลังลำบาก เราจึงออกแบบเป็นระบบ web + PostgreSQL ที่มีหลาย role, transaction จริง, constraints จริง, และ advanced reports เพื่อให้ตอบทั้งเชิงใช้งานจริงและเชิงออกแบบฐานข้อมูลได้ครบ"

## แหล่งอ้างอิง

- [README.md](/abs/path/C:/Users/saifa/Desktop/cn230/README.md:1)
- [app/main.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/main.py:1)
- [sql/schema.sql](/abs/path/C:/Users/saifa/Desktop/cn230/sql/schema.sql:1)
