-- Users Table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR NOT NULL UNIQUE,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR NOT NULL,
    department VARCHAR NOT NULL,
    phone_number VARCHAR NOT NULL,
    acc_role VARCHAR NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'Pending',
    is_employee BOOLEAN NOT NULL DEFAULT TRUE,
    is_approved BOOLEAN NOT NULL DEFAULT FALSE,
    hashed_password VARCHAR NOT NULL
);

CREATE INDEX ix_users_id ON users (id);
CREATE INDEX ix_users_email ON users (email);

-- Account Requests Table
CREATE TABLE account_requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR NOT NULL,
    email VARCHAR NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'Pending',
    department VARCHAR,
    phone_number VARCHAR,
    acc_role VARCHAR,
    approved_acc_role VARCHAR,
    is_supervisor BOOLEAN NOT NULL DEFAULT FALSE,
    is_intern BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_account_requests_id ON account_requests (id);

-- Notifications Table
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title VARCHAR NOT NULL,
    message VARCHAR NOT NULL,
    type VARCHAR NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_notifications_id ON notifications (id);

-- Facilities Table
CREATE TABLE facilities (
    facility_id SERIAL PRIMARY KEY,
    facility_name VARCHAR NOT NULL,
    facility_type VARCHAR NOT NULL,
    floor_level VARCHAR NOT NULL,
    capacity INTEGER,
    connection_type VARCHAR,
    cooling_tools VARCHAR,
    building VARCHAR,
    description VARCHAR,
    remarks VARCHAR,
    status VARCHAR NOT NULL DEFAULT 'Available',
    image_url VARCHAR,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX ix_facilities_facility_id ON facilities (facility_id);

-- Bookings Table
CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    bookers_id INTEGER NOT NULL,
    facility_id INTEGER,
    equipment_id INTEGER,
    supply_id INTEGER,
    purpose VARCHAR NOT NULL,
    start_date VARCHAR NOT NULL,
    end_date VARCHAR NOT NULL,
    return_date VARCHAR,
    status VARCHAR NOT NULL DEFAULT 'Pending',
    request_type VARCHAR NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    FOREIGN KEY (bookers_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (facility_id) REFERENCES facilities (facility_id) ON DELETE CASCADE
);

CREATE INDEX ix_bookings_id ON bookings (id);

-- Equipments Table
CREATE TABLE equipments (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    name VARCHAR NOT NULL,
    po_number VARCHAR,
    unit_number VARCHAR,
    brand_name VARCHAR,
    description VARCHAR,
    facility VARCHAR,
    facility_id INTEGER,
    category VARCHAR,
    status VARCHAR,
    availability VARCHAR NOT NULL DEFAULT 'Available',
    date_acquire VARCHAR,
    supplier VARCHAR,
    amount VARCHAR,
    estimated_life VARCHAR,
    item_number VARCHAR,
    property_number VARCHAR,
    control_number VARCHAR,
    serial_number VARCHAR,
    person_liable VARCHAR,
    remarks VARCHAR,
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    image VARCHAR,
    FOREIGN KEY (facility_id) REFERENCES facilities (facility_id)
);

CREATE INDEX ix_equipments_id ON equipments (id);

-- Borrowing Table
CREATE TABLE borrowing (
    id SERIAL PRIMARY KEY,
    borrowed_item INTEGER NOT NULL,
    borrowers_id INTEGER NOT NULL,
    purpose VARCHAR NOT NULL,
    start_date VARCHAR NOT NULL,
    end_date VARCHAR NOT NULL,
    return_date VARCHAR NOT NULL,
    request_status VARCHAR,
    return_status VARCHAR,
    availability VARCHAR,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    FOREIGN KEY (borrowed_item) REFERENCES equipments (id) ON DELETE CASCADE,
    FOREIGN KEY (borrowers_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_borrowing_id ON borrowing (id);

-- Supplies Table
CREATE TABLE supplies (
    supply_id SERIAL PRIMARY KEY,
    supply_name VARCHAR NOT NULL,
    description VARCHAR,
    category VARCHAR NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    stocking_point INTEGER NOT NULL DEFAULT 0,
    stock_unit VARCHAR NOT NULL,
    facility_id INTEGER,
    remarks VARCHAR,
    image_url VARCHAR,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    FOREIGN KEY (facility_id) REFERENCES facilities (facility_id)
);

CREATE INDEX ix_supplies_supply_id ON supplies (supply_id);

-- Acquiring Table
CREATE TABLE acquiring (
    id SERIAL PRIMARY KEY,
    acquirers_id INTEGER NOT NULL,
    supply_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    purpose VARCHAR,
    status VARCHAR NOT NULL DEFAULT 'Pending',
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    FOREIGN KEY (acquirers_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (supply_id) REFERENCES supplies (supply_id) ON DELETE CASCADE
);

CREATE INDEX ix_acquiring_id ON acquiring (id);

-- Return Notifications Table
CREATE TABLE return_notifications (
    id SERIAL PRIMARY KEY,
    borrowing_id INTEGER NOT NULL,
    receiver_name VARCHAR NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'pending_confirmation',
    message VARCHAR NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    FOREIGN KEY (borrowing_id) REFERENCES borrowing (id) ON DELETE CASCADE
);

CREATE INDEX ix_return_notifications_id ON return_notifications (id);

-- Done Notifications Table
CREATE TABLE done_notifications (
    id SERIAL PRIMARY KEY,
    booking_id INTEGER NOT NULL,
    completion_notes VARCHAR,
    status VARCHAR NOT NULL DEFAULT 'pending_confirmation',
    message VARCHAR NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    FOREIGN KEY (booking_id) REFERENCES bookings (id) ON DELETE CASCADE
);

CREATE INDEX ix_done_notifications_id ON done_notifications (id);

-- Equipment Logs Table
CREATE TABLE equipment_logs (
    id SERIAL PRIMARY KEY,
    equipment_id INTEGER,
    action VARCHAR NOT NULL,
    details VARCHAR,
    user_email VARCHAR NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    FOREIGN KEY (equipment_id) REFERENCES equipments (id)
);

CREATE INDEX ix_equipment_logs_id ON equipment_logs (id);

-- Facility Logs Table
CREATE TABLE facility_logs (
    id SERIAL PRIMARY KEY,
    facility_id INTEGER,
    action VARCHAR NOT NULL,
    details VARCHAR,
    user_email VARCHAR NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    FOREIGN KEY (facility_id) REFERENCES facilities (facility_id)
);

CREATE INDEX ix_facility_logs_id ON facility_logs (id);

-- Supply Logs Table
CREATE TABLE supply_logs (
    id SERIAL PRIMARY KEY,
    supply_id INTEGER,
    action VARCHAR NOT NULL,
    details VARCHAR,
    user_email VARCHAR NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    FOREIGN KEY (supply_id) REFERENCES supplies (supply_id)
);

CREATE INDEX ix_supply_logs_id ON supply_logs (id);

