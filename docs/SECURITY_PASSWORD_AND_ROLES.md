# Security, Password, And Roles

เอกสารนี้ใช้สำหรับอธิบายเรื่อง security ของระบบ, การจัดการ password, และความสามารถของแต่ละ role โดยอิงจาก implementation จริงในโปรเจกต์

## 1. Opening สั้น ๆ

ประโยคเปิดที่ใช้ได้ทันที:

> ระบบของผมออกแบบ security แบบหลายชั้นครับ ไม่ได้มีแค่ login อย่างเดียว แต่มี session-based authentication, password hashing, CSRF protection, rate limiting, backend role-based access control, trusted hosts, CORS และ audit logs เพื่อควบคุมทั้งการยืนยันตัวตนและการควบคุมสิทธิ์ของผู้ใช้

ถ้าต้องการเวอร์ชันสั้นกว่า:

> ฝั่ง security ของระบบนี้เน้น 2 เรื่องหลัก คือพิสูจน์ตัวตนให้ปลอดภัย และจำกัดสิทธิ์แต่ละ role ให้ทำได้เฉพาะงานของตัวเองครับ

## 2. Security architecture ภาพรวม

security ของระบบนี้แบ่งได้เป็น 6 ชั้นหลัก:

1. Authentication
   - ใช้ session-based authentication

2. Password security
   - ไม่เก็บ plain text password
   - ใช้ password hashing

3. Request protection
   - มี CSRF protection สำหรับคำสั่งที่แก้ข้อมูล

4. Abuse protection
   - มี rate limit ที่หน้า login

5. Authorization
   - มี role-based access control ที่ backend

6. Auditability
   - action สำคัญบางส่วนถูกบันทึกลง audit logs

ประโยคอธิบาย:

> ผมตั้งใจแยกเรื่อง authentication, authorization และ request protection ออกจากกันชัดเจน เพื่อให้ระบบไม่พึ่งแค่การซ่อนปุ่มบน frontend แต่ enforce ความปลอดภัยจาก backend จริง

## 3. ระบบ login และ authentication

ระบบนี้ใช้ `session-based authentication`

เมื่อ login สำเร็จ:

- ระบบตรวจ email และ password
- ถ้าถูกต้อง จะสร้าง session ให้ผู้ใช้
- session จะเก็บอย่างน้อย 2 ค่า:
  - `user_id`
  - `csrf_token`

ประโยคอธิบาย:

> หลัง login ระบบไม่ได้ส่ง JWT กลับไป แต่ใช้ session cookie สำหรับเว็บแอปโดยตรง ซึ่งเหมาะกับ browser-based application และทำงานร่วมกับ CSRF protection ได้ตรงรูปแบบ

## 4. ระบบ password ของผม

### 4.1 การเก็บ password

ระบบนี้ไม่เก็บรหัสผ่านแบบ plain text

สิ่งที่เกิดขึ้นตอนสมัคร:

1. ผู้ใช้ส่ง password เข้ามา
2. backend นำ password ไป hash ก่อน
3. ค่าที่เก็บในฐานข้อมูลคือ `password_hash`

จากโค้ดจริง:

- `app/security/hashing.py` ใช้ `PasswordHash.recommended()`
- config ระบุ scheme ที่ใช้เป็น `argon2`

ประโยคอธิบาย:

> ดังนั้นถึงแม้ฐานข้อมูลรั่ว ผู้โจมตีก็จะไม่เห็นรหัสผ่านจริง เพราะในตาราง users เก็บเฉพาะ hash เท่านั้น

### 4.2 ตอน login ระบบทำอะไร

ตอน login:

1. ระบบค้น user จาก email
2. เอา password ที่ผู้ใช้กรอกมาเทียบกับ hash ที่เก็บไว้
3. ถ้าตรงจึงอนุญาตให้ login
4. ถ้าบัญชีไม่ active จะถูกปฏิเสธ

จุดสำคัญ:

- ถ้า email หรือ password ผิด จะตอบ `401 Invalid email or password`
- ถ้าบัญชีถูกปิดใช้งาน จะตอบ `403 Inactive account`

### 4.3 กติกาของ password

จาก schema ฝั่ง request:

- password ขั้นต่ำ `12` ตัวอักษร
- password ยาวได้สูงสุด `128` ตัวอักษร

ประโยคอธิบาย:

> ผมบังคับขั้นต่ำ 12 ตัวอักษรเพื่อให้ password policy ไม่อ่อนเกินไป แม้ระบบนี้จะเป็นโปรเจกต์วิชา แต่ก็พยายามตั้ง baseline ที่จริงจังพอสำหรับระบบงาน

### 4.4 ทำไมเลือก Argon2

ประโยคตอบได้เลย:

> ผมเลือก Argon2 เพราะเป็น algorithm ที่ออกแบบมาสำหรับ password hashing โดยเฉพาะ และปลอดภัยกว่าการเก็บ plain text หรือการใช้ hash ทั่วไปแบบ SHA ตรง ๆ ที่ไม่เหมาะกับ password storage

## 5. Session security

ระบบใช้ `SessionMiddleware`

ค่าที่เกี่ยวข้องใน config:

- `session_cookie_name = smartlab_session`
- `session_max_age = 3600`
- `session_same_site = lax`
- `session_https_only` เปิดใช้ใน production

สิ่งที่เกิดขึ้น:

- session cookie ถูกใช้ระบุตัวตนของผู้ใช้
- ถ้า logout ระบบจะ clear session และลบ cookie
- ถ้า session ไม่มี `user_id` หรือ user ไม่ valid แล้ว จะเข้า endpoint ที่ต้อง login ไม่ได้

ประโยคอธิบาย:

> การใช้ session ทำให้ backend เป็นคนควบคุมสถานะ login โดยตรง และเมื่อ logout ก็สามารถ clear session ฝั่งเซิร์ฟเวอร์ได้ทันที

## 6. CSRF protection

เพราะระบบใช้ session cookie จึงต้องมีการป้องกัน CSRF

หลักการของระบบนี้:

- request แบบ `GET`, `HEAD`, `OPTIONS` ไม่ต้องตรวจ CSRF
- request ที่แก้ข้อมูล เช่น `POST`, `PATCH`, `DELETE` ต้องส่ง header token มาด้วย
- token ใน header ต้องตรงกับ `csrf_token` ที่อยู่ใน session
- ถ้าไม่ตรง ระบบจะตอบ `403 CSRF validation failed`

ยกเว้นบาง path:

- `/auth/login`
- `/auth/register`
- `/healthz`

ประโยคอธิบาย:

> เพราะระบบใช้ cookie-based session attacker อาจพยายามให้ browser ของเหยื่อยิง request แทนได้ ผมจึงเพิ่ม CSRF middleware เพื่อบังคับว่าคำสั่งที่เปลี่ยนข้อมูลต้องมี token ที่ตรงกับ session จริง

## 7. Rate limiting

ระบบมี rate limit ที่หน้า login

ค่า default:

- `5/minute`

หลักการ:

- จำกัดจำนวนครั้งที่ login ต่อ IP ในช่วงเวลาหนึ่ง
- ถ้าเกินจะตอบ `429 Too many requests`

ประโยคอธิบาย:

> จุดนี้ช่วยลด brute-force attack และแสดงให้เห็นว่าระบบคิดเรื่อง abuse protection มากกว่าการเช็ก password อย่างเดียว

## 8. Backend authorization และ role-based access control

ระบบนี้ไม่ได้พึ่งการซ่อนปุ่มบน frontend

สิทธิ์ถูก enforce ที่ backend ด้วย `require_roles(...)`

หลักการทำงาน:

1. backend อ่าน current user จาก session
2. โหลด role ของ user
3. เช็กว่า role นี้อยู่ในกลุ่มที่ endpoint อนุญาตหรือไม่
4. ถ้าไม่อยู่ จะตอบ `403 Insufficient permissions`

ประโยคอธิบาย:

> ต่อให้ผู้ใช้เปิด DevTools หรือยิง API ตรง ถ้า role ไม่ผ่าน backend ก็จะถูกปฏิเสธอยู่ดี ดังนั้น security จริงอยู่ที่ server side ไม่ใช่การซ่อน UI

## 9. ความสามารถของแต่ละ role

ระบบนี้มี 4 role หลัก:

- Student
- Staff
- Technician
- Admin

## 10. Role matrix แบบเล่าทีละ role

### 10.1 Student

Student ทำได้:

- สมัครสมาชิกผ่าน `POST /auth/register`
- login / logout
- ดูข้อมูลตัวเองผ่าน `/auth/me` และ `/users/me`
- ดูห้องที่เปิดให้จองผ่าน `/labs`
- ดูอุปกรณ์ที่พร้อมใช้งานผ่าน `/equipments`
- ดูเวลาว่างของห้องผ่าน `/reservations/availability`
- สร้าง reservation ของตัวเองผ่าน `POST /reservations`
- ดู reservation ของตัวเองผ่าน `/reservations/my`
- ยกเลิก reservation ของตัวเองผ่าน `POST /reservations/{reservation_id}/cancel`
- ดู borrowing ของตัวเองผ่าน `/borrowings/my`
- แจ้งซ่อมอุปกรณ์ผ่าน `POST /maintenance`
- ดู penalty ของตัวเองผ่าน `/penalties/my`
- ดู notification ของตัวเองผ่าน `/notifications/my`
- mark notification ของตัวเองว่าอ่านแล้วผ่าน `PATCH /notifications/{notification_id}`

Student ทำไม่ได้:

- ดูรายการ reservation ทั้งระบบ
- สร้าง borrowing ให้คนอื่น
- รับคืนอุปกรณ์
- ดู maintenance queue
- ดู summary report หรือ advanced SQL reports
- จัดการ users, roles, labs, equipments
- ดู audit logs
- เปลี่ยน role หรือสถานะผู้ใช้

ประโยคอธิบาย:

> Student เป็นผู้ใช้ปลายทางครับ จึงถูกจำกัดให้เข้าถึงเฉพาะข้อมูลของตัวเองและ workflow ที่เกี่ยวกับการใช้งานระบบ เช่น จองห้อง ดูค่าปรับ และแจ้งซ่อม

### 10.2 Staff

Staff ทำได้:

- ทุกอย่างที่ user login ปกติทำได้ในส่วนข้อมูลของตัวเอง
- ดูผู้ใช้ทั้งหมดผ่าน `/staff/users`
- ดู reservation ทั้งระบบผ่าน `GET /reservations`
- สร้าง borrowing ให้ผู้ใช้อื่นผ่าน `POST /borrowings`
- ดู borrowing ทั้งระบบผ่าน `GET /borrowings`
- รับคืนอุปกรณ์ผ่าน `PATCH /borrowings/{borrow_id}/return`
- ดู summary report ผ่าน `/staff/reports/summary`
- ดู advanced SQL reports ทั้ง 5 ตัวผ่าน `/reports/...`

Staff ทำไม่ได้:

- แก้ role ผู้ใช้
- ปิด/เปิดบัญชีผู้ใช้
- CRUD labs แบบ admin
- CRUD equipments แบบ admin
- ดู audit logs แบบ admin
- อัปเดตสถานะ maintenance ถ้าไม่ใช่ Technician หรือ Admin

ประโยคอธิบาย:

> Staff เป็น role ฝั่งปฏิบัติการประจำวัน จึงถูกออกแบบให้จัดการงานธุรกรรม เช่น ยืมคืนอุปกรณ์และดู report ได้ แต่ยังไม่มีสิทธิ์ด้าน governance ของระบบ

### 10.3 Technician

Technician ทำได้:

- ทุกอย่างที่ user login ปกติทำได้ในส่วนข้อมูลของตัวเอง
- ดู maintenance queue ผ่าน `GET /maintenance/queue`
- อัปเดตสถานะงานซ่อมผ่าน `PATCH /maintenance/{repair_id}`

Technician ทำไม่ได้:

- สร้าง borrowing
- รับคืนอุปกรณ์ในนาม staff
- ดู advanced reports แบบ staff/admin
- จัดการ users, labs, equipments
- ดู audit logs

ประโยคอธิบาย:

> Technician มีสิทธิ์เฉพาะสายงานซ่อมครับ คือเห็นคิวซ่อมและอัปเดตสถานะซ่อมได้ แต่ไม่ยุ่งกับงานบริหารข้อมูลหลักหรือรายงานเชิงบริหาร

### 10.4 Admin

Admin ทำได้:

- ทุกอย่างที่ role อื่นทำได้ในเชิงบริหารระบบ
- ดู users ทั้งหมดผ่าน `/admin/users`
- ดู roles ผ่าน `/admin/roles`
- เปลี่ยน role ผู้ใช้ผ่าน `PATCH /admin/users/{user_id}/role`
- เปลี่ยน active status ผู้ใช้ผ่าน `PATCH /admin/users/{user_id}/status`
- ดู labs ทั้งหมดผ่าน `/admin/labs`
- สร้าง, แก้ไข, ลบ labs
- ดู equipments ทั้งหมดผ่าน `/admin/equipments`
- สร้าง, แก้ไข, ลบ equipments
- ดู audit logs ผ่าน `/admin/audit-logs`
- อัปเดต reservation ผ่าน `PATCH /reservations/{reservation_id}`
- ลบ reservation ผ่าน `DELETE /reservations/{reservation_id}`
- ดู maintenance queue และอัปเดตสถานะ maintenance ได้เหมือน technician
- ดู summary report และ advanced SQL reports ได้เหมือน staff

ประโยคอธิบาย:

> Admin เป็น role ที่ดูแลทั้ง master data, user governance และการตรวจสอบย้อนหลัง จึงมีสิทธิ์กว้างที่สุดในระบบ

## 11. Security point ที่ควรเน้นเวลาโดนถาม

### ถ้า frontend ซ่อนปุ่มไว้พอไหม

คำตอบ:

> ไม่พอครับ เพราะ attacker ยังยิง API ตรงได้ ดังนั้นระบบนี้บังคับ role ที่ backend ด้วย `require_roles(...)` ทุก endpoint สำคัญ

### ถ้าฐานข้อมูลรั่วจะเห็น password จริงไหม

คำตอบ:

> ไม่เห็นครับ เพราะระบบเก็บเฉพาะ password hash ไม่ได้เก็บ plain text password

### ถ้าผู้ใช้ login แล้วโดนหลอกให้ submit form จากเว็บอื่นล่ะ

คำตอบ:

> ระบบนี้มี CSRF protection สำหรับ request ที่แก้ข้อมูล จึงต้องมี token จาก session ที่ตรงกันถึงจะผ่าน

### ถ้ามีคนลองเดารหัสผ่านรัว ๆ

คำตอบ:

> login route มี rate limit default 5 ครั้งต่อนาที ช่วยลด brute-force ได้ระดับหนึ่ง

### ถ้า account ถูกปิดใช้งานแต่ยังมี session เดิมอยู่

คำตอบ:

> `get_current_user` จะเช็ก `is_active` ทุกครั้ง ถ้าบัญชีไม่ active แล้วจะใช้ session เดิมเข้า endpoint ที่ต้อง auth ไม่ได้

## 12. ประโยคสรุปพร้อมใช้

ประโยคปิด:

> สรุปคือระบบนี้ออกแบบ security แบบหลายชั้นครับ เริ่มจาก password hashing และ session-based authentication จากนั้นเพิ่ม CSRF protection, rate limiting, trusted hosts, CORS, backend RBAC และ audit logs ทำให้ทั้งการยืนยันตัวตนและการจำกัดสิทธิ์ของแต่ละ role มีความชัดเจนและปลอดภัยกว่าการพึ่ง frontend อย่างเดียว

## 13. ไฟล์อ้างอิงในโปรเจกต์

- [app/security/hashing.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/security/hashing.py:1)
- [app/security/session.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/security/session.py:1)
- [app/security/csrf.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/security/csrf.py:1)
- [app/security/rbac.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/security/rbac.py:1)
- [app/security/rate_limit.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/security/rate_limit.py:1)
- [app/services/auth_service.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/services/auth_service.py:1)
- [app/schemas/auth.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/schemas/auth.py:1)
- [app/api/deps.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/api/deps.py:1)
- [app/api/routers/auth.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/api/routers/auth.py:1)
- [app/api/routers/admin.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/api/routers/admin.py:1)
- [app/api/routers/staff.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/api/routers/staff.py:1)
- [app/api/routers/reservations.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/api/routers/reservations.py:1)
- [app/api/routers/borrowings.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/api/routers/borrowings.py:1)
- [app/api/routers/maintenance.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/api/routers/maintenance.py:1)
- [app/api/routers/notifications.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/api/routers/notifications.py:1)
- [app/api/routers/penalties.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/api/routers/penalties.py:1)
- [app/main.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/main.py:1)
