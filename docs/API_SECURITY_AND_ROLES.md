# API, Security, And Roles

เอกสารนี้ใช้ตอบคำถามเกี่ยวกับ endpoint, สิทธิ์ผู้ใช้, และมาตรการความปลอดภัย

## 1. แนวคิดการออกแบบ API

ระบบนี้แยก API ตามโดเมนงาน ไม่ได้รวมทุกอย่างไว้ไฟล์เดียว

โมดูลหลัก:

- `auth`
- `users`
- `labs`
- `equipments`
- `reservations`
- `borrowings`
- `maintenance`
- `notifications`
- `penalties`
- `admin`
- `staff`
- `reports`

ข้อดีคือ:

- อ่านง่าย
- maintain ง่าย
- แยก responsibility ชัด

## 2. กลุ่ม endpoint สำคัญ

### Auth

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`

### Reservations

- `GET /reservations/my`
- `GET /reservations`
- `GET /reservations/availability`
- `POST /reservations`
- `POST /reservations/{reservation_id}/cancel`
- `PATCH /reservations/{reservation_id}`
- `DELETE /reservations/{reservation_id}`

### Borrowings

- `GET /borrowings/my`
- `GET /borrowings`
- `POST /borrowings`
- `PATCH /borrowings/{borrow_id}/return`

### Maintenance

- `GET /maintenance/queue`
- `POST /maintenance`
- `PATCH /maintenance/{repair_id}`

### Notifications and penalties

- `GET /notifications/my`
- `PATCH /notifications/{notification_id}`
- `GET /penalties/my`

### Admin

- `GET /admin/users`
- `GET /admin/roles`
- `GET/POST/PATCH/DELETE /admin/labs`
- `GET/POST/PATCH/DELETE /admin/equipments`
- `PATCH /admin/users/{user_id}/role`
- `PATCH /admin/users/{user_id}/status`
- `GET /admin/audit-logs`

### Reports

- `GET /reports/late-borrowings`
- `GET /reports/top-borrowers`
- `GET /reports/lab-utilization`
- `GET /reports/equipment-repairs`
- `GET /reports/reservation-summary`

## 3. Role matrix

### Student

ทำได้:
- สมัครและ login
- ดูข้อมูลของตัวเอง
- จองห้อง
- ยกเลิก reservation ของตัวเอง
- ดูรายการยืมของตัวเอง
- ดูค่าปรับของตัวเอง
- ดูและ mark notification ของตัวเอง
- แจ้งซ่อม

ทำไม่ได้:
- เข้าถึง admin routes
- ดูรายงานระดับ staff/admin
- ปรับ role ผู้ใช้

### Staff

ทำได้:
- ดูผู้ใช้ทั้งหมด
- สร้างรายการยืม
- ดูรายการยืมที่ active
- รับคืนอุปกรณ์
- ดู summary report
- ดู advanced SQL reports

### Technician

ทำได้:
- ดู maintenance queue
- อัปเดตสถานะซ่อม

### Admin

ทำได้ทุกอย่างที่สำคัญในเชิงจัดการ:
- ดู users
- เปลี่ยน role และ active status
- CRUD labs
- CRUD equipments
- ดู audit logs
- จัดการ reservation เชิง admin
- ดู reports

## 4. Authentication design

ระบบใช้ session-based authentication

จาก [app/security/session.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/security/session.py:1)

เมื่อ login สำเร็จ ระบบจะเก็บ:

- `user_id`
- `csrf_token`

เหตุผลที่ใช้ session:

- เหมาะกับ browser app
- ใช้งานกับ CSRF middleware ได้ตรงรูปแบบ
- ไม่ต้องจัดการ token ฝั่ง frontend ซับซ้อนแบบ JWT

## 5. Password security

จาก config ระบบใช้ password hashing scheme เป็น `argon2`

เหตุผล:

- ไม่เก็บ plain text password
- Argon2 เป็นอัลกอริทึมที่เหมาะกับการ hash password

## 6. CSRF protection

จาก [app/security/csrf.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/security/csrf.py:1)

หลักการ:

- request ที่เป็น `GET`, `HEAD`, `OPTIONS` ไม่ต้องตรวจ CSRF
- request ที่แก้ข้อมูลต้องมี header `X-CSRF-Token`
- token ต้องตรงกับ token ใน session
- ถ้าไม่ตรงจะถูกปฏิเสธด้วย `403`

เหตุผล:

- ระบบใช้ session cookie
- session cookie มีความเสี่ยงเรื่อง CSRF
- จึงต้องมี middleware ป้องกัน

## 7. Rate limiting

จาก [app/api/routers/auth.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/api/routers/auth.py:1) และ [app/config.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/config.py:1)

login route มี rate limit:

- ค่า default คือ `5/minute`

เหตุผล:

- ลด brute-force attacks
- แสดงให้เห็นว่าระบบคิดเรื่อง security มากกว่า requirement ขั้นต่ำ

## 8. Trusted hosts และ CORS

จาก [app/main.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/main.py:1)

ระบบมี:

- `TrustedHostMiddleware`
- `CORSMiddleware`

ประโยชน์:

- จำกัด host ที่ระบบยอมรับ
- คุมการเรียกข้าม origin ให้เหมาะกับ deployment

## 9. Readiness check

`/readyz` ไม่ได้ตอบแค่ว่า app รันอยู่ แต่เช็กด้วยว่าตารางที่ model ต้องใช้มีครบ

ข้อดี:

- ถ้า deploy แล้ว schema ยังไม่พร้อม จะรู้ทันที
- สื่อให้เห็นว่าระบบคิดถึง deployment health

## 10. Auditability

หลาย endpoint ฝั่ง admin, borrowing, maintenance มีการสร้าง `audit_logs`

ข้อดี:

- ตรวจสอบย้อนหลังได้
- ช่วยตอบคำถามว่า "ใครเปลี่ยนข้อมูลนี้"
- เหมาะกับระบบที่มีหลายบทบาท

## 11. ประเด็นที่ควรตอบเวลาอาจารย์ถามว่า "ซ่อนปุ่มพอไหม?"

คำตอบคือไม่พอ

เพราะถึง frontend จะซ่อนปุ่ม แต่ attacker ยังยิง request ตรงไปที่ API ได้

ดังนั้นระบบนี้จึง enforce role ที่ backend ด้วย `require_roles(...)`

## 12. ประโยคสรุปสำหรับตอบอาจารย์

"ระบบนี้ใช้ session-based authentication สำหรับเว็บแอป, มี CSRF protection สำหรับ request ที่แก้ไขข้อมูล, มี rate limiting ที่ login, มี role-based access control ที่ enforce ฝั่ง backend และมี audit logs สำหรับ action สำคัญ ทำให้ตอบโจทย์ทั้งเรื่องความปลอดภัยและการควบคุมสิทธิ์ในระดับระบบจริง"

## แหล่งอ้างอิง

- [app/api/routers/auth.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/api/routers/auth.py:1)
- [app/security/rbac.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/security/rbac.py:1)
- [app/security/csrf.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/security/csrf.py:1)
- [app/config.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/config.py:1)
- [app/main.py](/abs/path/C:/Users/saifa/Desktop/cn230/app/main.py:1)
