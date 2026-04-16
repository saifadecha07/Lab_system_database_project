import psycopg2

# 1. ใส่ Connection URL ที่ได้จาก Railway
# (เปลี่ยนข้อความในเครื่องหมายคำพูดเป็นลิงก์ของอาจารย์เอง)
DATABASE_URL = "postgresql://postgres:ehAtBtPRZKyqVQZgzYUWMoOBUIrmntMF@maglev.proxy.rlwy.net:23763/railway"

# 2. เตรียมชุดคำสั่ง SQL (DDL) ทั้ง 12 ตาราง
sql_commands = """
-- ตารางข้อมูลอ้างอิง
CREATE TABLE IF NOT EXISTS roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS equipment_categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS lab_types (
    lab_type_id SERIAL PRIMARY KEY,
    type_name VARCHAR(100) UNIQUE NOT NULL
);

-- ตารางข้อมูลหลัก
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    role_id INT REFERENCES roles(role_id),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS labs (
    lab_id SERIAL PRIMARY KEY,
    lab_type_id INT REFERENCES lab_types(lab_type_id),
    room_name VARCHAR(100) NOT NULL,
    capacity INT NOT NULL CHECK (capacity > 0),
    status VARCHAR(50) NOT NULL DEFAULT 'Available'
);

CREATE TABLE IF NOT EXISTS equipments (
    equipment_id SERIAL PRIMARY KEY,
    category_id INT REFERENCES equipment_categories(category_id),
    lab_id INT REFERENCES labs(lab_id),
    equipment_name VARCHAR(150) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Available'
);

-- ตารางธุรกรรม
CREATE TABLE IF NOT EXISTS lab_reservations (
    reservation_id SERIAL PRIMARY KEY,
    lab_id INT REFERENCES labs(lab_id),
    reserved_by INT REFERENCES users(user_id),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Pending'
);

CREATE TABLE IF NOT EXISTS reservation_participants (
    reservation_id INT REFERENCES lab_reservations(reservation_id),
    user_id INT REFERENCES users(user_id),
    PRIMARY KEY (reservation_id, user_id)
);

CREATE TABLE IF NOT EXISTS equipment_borrowings (
    borrow_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id),
    equipment_id INT REFERENCES equipments(equipment_id),
    borrow_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expected_return TIMESTAMP NOT NULL,
    actual_return TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'Borrowed'
);

CREATE TABLE IF NOT EXISTS maintenance_records (
    repair_id SERIAL PRIMARY KEY,
    equipment_id INT REFERENCES equipments(equipment_id),
    reported_by INT REFERENCES users(user_id),
    technician_id INT REFERENCES users(user_id),
    report_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_date TIMESTAMP,
    issue_detail TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Reported'
);

-- ตารางฟีเจอร์ขั้นสูง
CREATE TABLE IF NOT EXISTS penalties (
    penalty_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id),
    borrow_id INT REFERENCES equipment_borrowings(borrow_id),
    fine_amount DECIMAL(10,2) NOT NULL CHECK (fine_amount >= 0),
    is_resolved BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS notifications (
    notification_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id),
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

# 3. เริ่มกระบวนการเชื่อมต่อและสั่งรัน
try:
    print("กำลังเชื่อมต่อไปยังฐานข้อมูล Railway...")
    # เชื่อมต่อ Database
    conn = psycopg2.connect(DATABASE_URL)
    
    # สร้าง Cursor (ตัวแทนของเราที่ทำหน้าที่เอาคำสั่ง SQL ไปวางรันในฐานข้อมูล)
    cur = conn.cursor()
    
    print("กำลังสร้างตารางทั้ง 12 ตาราง...")
    # สั่งรันคำสั่ง SQL
    cur.execute(sql_commands)
    
    # ยืนยันการเปลี่ยนแปลง (Commit) ถ้าไม่ใส่บรรทัดนี้ ตารางจะไม่ถูกบันทึกจริง
    conn.commit()
    
    # ปิดการเชื่อมต่อ
    cur.close()
    conn.close()
    print("✅ สร้างตารางสำเร็จเรียบร้อยแล้ว! กลับไปกด Refresh ดูที่หน้าเว็บ Railway ได้เลยครับ")

except Exception as e:
    print("❌ เกิดข้อผิดพลาด:")
    print(e)