-- =============================================================================
-- Smart Lab Management System — PostgreSQL DDL
-- CN230 Database Systems Project
-- =============================================================================
-- Run order matters: lookup tables → core entities → transactions → features
-- To re-create from scratch: DROP TABLE ... CASCADE (handled below)
-- =============================================================================

-- Drop in reverse dependency order (safe re-run)
DROP TABLE IF EXISTS audit_logs              CASCADE;
DROP TABLE IF EXISTS notifications           CASCADE;
DROP TABLE IF EXISTS penalties               CASCADE;
DROP TABLE IF EXISTS maintenance_records     CASCADE;
DROP TABLE IF EXISTS equipment_borrowings    CASCADE;
DROP TABLE IF EXISTS reservation_participants CASCADE;
DROP TABLE IF EXISTS lab_reservations        CASCADE;
DROP TABLE IF EXISTS equipments              CASCADE;
DROP TABLE IF EXISTS equipment_categories    CASCADE;
DROP TABLE IF EXISTS labs                    CASCADE;
DROP TABLE IF EXISTS lab_types               CASCADE;
DROP TABLE IF EXISTS users                   CASCADE;
DROP TABLE IF EXISTS roles                   CASCADE;


-- =============================================================================
-- LOOKUP TABLES
-- =============================================================================

CREATE TABLE roles (
    role_id   SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE lab_types (
    lab_type_id SERIAL PRIMARY KEY,
    type_name   VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE equipment_categories (
    category_id   SERIAL PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE NOT NULL
);


-- =============================================================================
-- CORE ENTITIES
-- =============================================================================

CREATE TABLE users (
    user_id       SERIAL PRIMARY KEY,
    role_id       INT NOT NULL
                      REFERENCES roles(role_id)
                      ON UPDATE CASCADE ON DELETE RESTRICT,
    email         VARCHAR(150) UNIQUE NOT NULL,
    first_name    VARCHAR(100) NOT NULL,
    last_name     VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_users_email    ON users(email);
CREATE INDEX idx_users_role_id  ON users(role_id);

CREATE TABLE labs (
    lab_id      SERIAL PRIMARY KEY,
    lab_type_id INT REFERENCES lab_types(lab_type_id)
                    ON UPDATE CASCADE ON DELETE SET NULL,
    room_name   VARCHAR(100) UNIQUE NOT NULL,
    capacity    INT NOT NULL,
    status      VARCHAR(50) NOT NULL DEFAULT 'Available',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_labs_capacity_positive CHECK (capacity > 0),
    CONSTRAINT ck_labs_status CHECK (
        status IN ('Available','Reserved','Maintenance','Closed')
    )
);
CREATE INDEX idx_labs_status ON labs(status);

CREATE TABLE equipments (
    equipment_id   SERIAL PRIMARY KEY,
    category_id    INT REFERENCES equipment_categories(category_id)
                       ON UPDATE CASCADE ON DELETE SET NULL,
    lab_id         INT REFERENCES labs(lab_id)
                       ON UPDATE CASCADE ON DELETE SET NULL,
    equipment_name VARCHAR(150) NOT NULL,
    status         VARCHAR(50) NOT NULL DEFAULT 'Available',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_equipments_status CHECK (
        status IN ('Available','Borrowed','In_Repair')
    )
);
CREATE INDEX idx_equipments_status ON equipments(status);
CREATE INDEX idx_equipments_lab_id ON equipments(lab_id);


-- =============================================================================
-- TRANSACTION TABLES
-- =============================================================================

CREATE TABLE lab_reservations (
    reservation_id SERIAL PRIMARY KEY,
    lab_id         INT NOT NULL
                       REFERENCES labs(lab_id)
                       ON UPDATE CASCADE ON DELETE RESTRICT,
    reserved_by    INT NOT NULL
                       REFERENCES users(user_id)
                       ON UPDATE CASCADE ON DELETE RESTRICT,
    start_time     TIMESTAMPTZ NOT NULL,
    end_time       TIMESTAMPTZ NOT NULL,
    status         VARCHAR(50) NOT NULL DEFAULT 'Pending',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_reservations_time  CHECK (end_time > start_time),
    CONSTRAINT ck_reservations_status CHECK (
        status IN ('Pending','Approved','Cancelled')
    )
);
CREATE INDEX idx_reservations_lab_id ON lab_reservations(lab_id);
CREATE INDEX idx_reservations_status ON lab_reservations(status);
CREATE INDEX idx_reservations_time   ON lab_reservations(start_time, end_time);

-- M:N junction — group members in a reservation
CREATE TABLE reservation_participants (
    reservation_id INT NOT NULL
                       REFERENCES lab_reservations(reservation_id)
                       ON UPDATE CASCADE ON DELETE CASCADE,
    user_id        INT NOT NULL
                       REFERENCES users(user_id)
                       ON UPDATE CASCADE ON DELETE CASCADE,
    PRIMARY KEY (reservation_id, user_id)
);

CREATE TABLE equipment_borrowings (
    borrow_id       SERIAL PRIMARY KEY,
    user_id         INT NOT NULL
                        REFERENCES users(user_id)
                        ON UPDATE CASCADE ON DELETE RESTRICT,
    equipment_id    INT NOT NULL
                        REFERENCES equipments(equipment_id)
                        ON UPDATE CASCADE ON DELETE RESTRICT,
    borrow_time     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expected_return TIMESTAMPTZ NOT NULL,
    actual_return   TIMESTAMPTZ,
    status          VARCHAR(50) NOT NULL DEFAULT 'Borrowed',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_borrowings_status CHECK (
        status IN ('Borrowed','Returned')
    )
);
CREATE INDEX idx_borrowings_user_id  ON equipment_borrowings(user_id);
CREATE INDEX idx_borrowings_equip_id ON equipment_borrowings(equipment_id);
CREATE INDEX idx_borrowings_status   ON equipment_borrowings(status);

CREATE TABLE maintenance_records (
    repair_id     SERIAL PRIMARY KEY,
    equipment_id  INT NOT NULL
                      REFERENCES equipments(equipment_id)
                      ON UPDATE CASCADE ON DELETE RESTRICT,
    reported_by   INT NOT NULL
                      REFERENCES users(user_id)
                      ON UPDATE CASCADE ON DELETE RESTRICT,
    technician_id INT
                      REFERENCES users(user_id)
                      ON UPDATE CASCADE ON DELETE SET NULL,
    report_date   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_date TIMESTAMPTZ,
    issue_detail  TEXT NOT NULL,
    status        VARCHAR(50) NOT NULL DEFAULT 'Reported',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_maintenance_status CHECK (
        status IN ('Reported','In Progress','Fixed')
    )
);
CREATE INDEX idx_maintenance_equip_id ON maintenance_records(equipment_id);
CREATE INDEX idx_maintenance_status   ON maintenance_records(status);


-- =============================================================================
-- ADVANCED FEATURE TABLES
-- =============================================================================

CREATE TABLE penalties (
    penalty_id  SERIAL PRIMARY KEY,
    user_id     INT NOT NULL
                    REFERENCES users(user_id)
                    ON UPDATE CASCADE ON DELETE RESTRICT,
    borrow_id   INT NOT NULL
                    REFERENCES equipment_borrowings(borrow_id)
                    ON UPDATE CASCADE ON DELETE RESTRICT,
    fine_amount NUMERIC(10,2) NOT NULL
                    CONSTRAINT ck_penalties_fine_positive CHECK (fine_amount > 0),
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_penalties_user_id  ON penalties(user_id);
CREATE INDEX idx_penalties_borrow_id ON penalties(borrow_id);

CREATE TABLE notifications (
    notification_id SERIAL PRIMARY KEY,
    user_id         INT NOT NULL
                        REFERENCES users(user_id)
                        ON UPDATE CASCADE ON DELETE CASCADE,
    message         TEXT NOT NULL,
    is_read         BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);

CREATE TABLE audit_logs (
    audit_log_id  SERIAL PRIMARY KEY,
    actor_user_id INT
                      REFERENCES users(user_id)
                      ON UPDATE CASCADE ON DELETE SET NULL,
    action        VARCHAR(100) NOT NULL,
    target_type   VARCHAR(50),
    target_id     INT,
    details       JSONB,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_audit_actor    ON audit_logs(actor_user_id);
CREATE INDEX idx_audit_action   ON audit_logs(action);
CREATE INDEX idx_audit_created  ON audit_logs(created_at DESC);


-- =============================================================================
-- DEFAULT SEED — Lookup values (safe to run on an empty DB)
-- =============================================================================

INSERT INTO roles (role_name) VALUES
    ('Student'),
    ('Staff'),
    ('Technician'),
    ('Admin')
ON CONFLICT (role_name) DO NOTHING;

INSERT INTO lab_types (type_name) VALUES
    ('Computer Lab'),
    ('Science Lab'),
    ('General Purpose'),
    ('Electronics Lab')
ON CONFLICT (type_name) DO NOTHING;

INSERT INTO equipment_categories (category_name) VALUES
    ('Computer'),
    ('Microscope'),
    ('Chemistry Equipment'),
    ('Electronics'),
    ('Projector / AV')
ON CONFLICT (category_name) DO NOTHING;
