# Testing, Demo, And Limitations

เอกสารนี้ใช้ตอบคำถามเรื่องความถูกต้องของระบบ, สิ่งที่ทดสอบแล้ว, วิธี demo, และข้อจำกัดปัจจุบัน

## 1. ทำไมต้องมี tests

โปรเจกต์ฐานข้อมูลหรือเว็บแอปมักถูกถามว่า "รู้ได้ยังไงว่าระบบถูกต้อง"

คำตอบของโปรเจกต์นี้คือใช้ automated tests กับ flow สำคัญจริง ไม่ได้อาศัยการคลิก manual อย่างเดียว

## 2. สิ่งที่ tests ครอบคลุม

จาก [tests/test_app.py](/abs/path/C:/Users/saifa/Desktop/cn230/tests/test_app.py:1)

ระบบทดสอบประเด็นสำคัญ เช่น

- หน้า root เปิดได้
- registration กำหนด role เริ่มต้นเป็น `Student`
- login คืน CSRF token
- นักศึกษาเข้า admin routes ไม่ได้
- admin create lab ต้องมี CSRF
- reservation overlap ถูก reject
- reservation response serialize เวลาเป็น timezone ที่จอง
- reservation ต้องตรง fixed slots เท่านั้น
- availability แสดงข้อมูลตาม booking date
- คืนอุปกรณ์ช้าจะสร้าง penalty และ audit log
- staff สร้างและ list borrowing ได้
- invalid lab status ถูก reject
- maintenance บนอุปกรณ์ที่ยังถูกยืมอยู่ไม่ทำให้ status เพี้ยน
- ห้ามยืมอุปกรณ์ที่มี open maintenance
- admin list users และ roles ได้
- admin update/delete lab ได้
- admin update/delete equipment ได้
- user mark notification read ได้
- admin toggle user status ได้
- admin update/delete reservation ได้
- `healthz` ยังตอบได้แม้ schema ยังไม่พร้อม
- favicon route ตอบ 204
- allowed hosts ยังคงรวม host ที่ใช้บน Railway

## 3. สิ่งที่ tests เหล่านี้พิสูจน์

tests ไม่ได้แค่เช็กว่า endpoint ตอบ 200 แต่เช็กกฎธุรกิจด้วย

ตัวอย่าง:

- reservation overlap ไม่ใช่แค่ validation ทั่วไป แต่เป็น core business rule
- late return ต้องทำทั้ง penalty และ audit log
- maintenance กับ borrowing ต้องทำงานร่วมกันถูก
- security flow เช่น CSRF และ RBAC ต้องใช้งานได้จริง

## 4. วิธี demo ที่แนะนำ

### Demo flow 1: Student

1. สมัคร user ใหม่
2. login
3. ดูว่าระบบแสดง role เป็น Student
4. เปิด reservation availability
5. จองห้อง 1 slot
6. ดูรายการจองของตัวเอง
7. ลองเปิด admin route ให้เห็นว่าเข้าไม่ได้

### Demo flow 2: Staff

1. login เป็น staff
2. สร้าง borrowing ให้ผู้ใช้
3. แสดง active borrowings
4. รับคืนอุปกรณ์
5. ถ้าคืนช้าให้โชว์ penalty และ notification

### Demo flow 3: Technician

1. login เป็น technician
2. เปิด maintenance queue
3. เปลี่ยนสถานะจาก `Reported` เป็น `In Progress` หรือ `Fixed`

### Demo flow 4: Admin

1. login เป็น admin
2. เปิดหน้าจัดการ users
3. เปลี่ยน role หรือ active status
4. CRUD ห้องหรืออุปกรณ์
5. เปิด audit logs

### Demo flow 5: Reports

1. เปิดรายงาน late borrowings
2. เปิดค่าปรับรายบุคคล
3. เปิด lab utilization
4. อธิบายว่า query มาจาก join/group by จริง

## 5. ประเด็นที่ควรโชว์ตอน demo database

- ตารางหลักใน schema
- reservation_participants ในฐานะ many-to-many table
- penalty แยกออกจาก borrowing
- audit_logs สำหรับ traceability
- PostgreSQL exclusion constraint กัน booking overlap

## 6. ข้อจำกัดปัจจุบันของระบบ

ข้อจำกัดที่พูดได้ตรงๆ และดูเป็นมืออาชีพ:

- frontend ยังเป็น dashboard แบบเรียบ ไม่ได้เน้น UX ขั้นสูง
- notification ยังเป็น in-app notification ยังไม่มี email หรือ push
- รายงานยังเป็น predefined reports ไม่ใช่ ad-hoc analytics
- penalty policy ยังเป็นแบบง่ายต่อชั่วโมง ยังไม่ได้รองรับหลายระดับกฎ
- participant management ยังไม่ได้ expose UI เชิงลึกครบทุก flow
- test suite ยังขยายต่อได้อีกในด้าน login rate limit และ admin audit coverage บางส่วน

## 7. ทำไมข้อจำกัดเหล่านี้ไม่ทำให้โปรเจกต์อ่อน

เพราะแกนสำคัญของงานวิชานี้คือ:

- schema design
- referential integrity
- business transactions
- SQL reporting
- integration กับเว็บแอปจริง

ซึ่งโปรเจกต์นี้มีครบและค่อนข้างชัด

## 8. ถ้าอาจารย์ถามว่า "ถ้ามีเวลาต่อจะพัฒนาอะไร"

ตอบได้ว่า:

- เพิ่ม dashboard analytics เชิงภาพ
- เพิ่ม export reports
- เพิ่ม email notification
- เพิ่ม reservation participant management เต็มรูปแบบ
- เพิ่ม test coverage ด้าน security และ concurrency
- แยก service บางส่วนให้ modular มากขึ้น

## 9. ประโยคสรุปสำหรับตอบอาจารย์

"ระบบนี้ไม่ได้หยุดที่การทำ feature ให้ครบ แต่มี automated tests สำหรับ business rules สำคัญ เช่น การจองห้องซ้อน, การคืนช้าและค่าปรับ, การควบคุมสิทธิ์, CSRF และการประสานกันของ borrowing กับ maintenance ทำให้ยืนยันได้ว่าระบบทำงานถูกต้องใน flow หลักจริง"

## แหล่งอ้างอิง

- [tests/test_app.py](/abs/path/C:/Users/saifa/Desktop/cn230/tests/test_app.py:1)
- [tests/README.md](/abs/path/C:/Users/saifa/Desktop/cn230/tests/README.md:1)
