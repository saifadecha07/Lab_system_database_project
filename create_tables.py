import os
import sys

import psycopg2


DEFAULT_DATABASE_URL = (
    "postgresql://postgres:xxxxxxxx@junction.proxy.rlwy.net:xxxxx/railway"
)

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

SQL_COMMANDS = """
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


def validate_database_url(database_url: str) -> None:
    if database_url == DEFAULT_DATABASE_URL:
        raise ValueError(
            "DATABASE_URL is still using the placeholder value. "
            "Set the real Railway/PostgreSQL connection string first."
        )

    if "xxxxxxxx" in database_url or "xxxxx" in database_url:
        raise ValueError(
            "DATABASE_URL still contains placeholder parts (xxxxxxxx / xxxxx)."
        )


def main() -> int:
    try:
        validate_database_url(DATABASE_URL)
        print("Connecting to PostgreSQL...")

        with psycopg2.connect(DATABASE_URL, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                print("Creating tables...")
                cur.execute(SQL_COMMANDS)

        print("Tables created successfully.")
        return 0
    except Exception as error:
        print("Failed to create tables:")
        print(error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
