CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_number TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS parking_slots (
    slot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_name TEXT UNIQUE NOT NULL,
    is_available INTEGER DEFAULT 1,
    location TEXT DEFAULT 'Nwssu Calbayog City, Samar, Philippines'
);

CREATE TABLE IF NOT EXISTS bookings (
    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    slot_id INTEGER NOT NULL,
    entry_date TEXT NOT NULL,
    entry_time TEXT NOT NULL,
    exit_date TEXT NOT NULL,
    exit_time TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    booked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (slot_id) REFERENCES parking_slots(slot_id) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE (slot_id, entry_date, entry_time)
);

INSERT OR IGNORE INTO parking_slots (slot_name)
VALUES ('A1'), ('A2'), ('A3'), ('A4'), ('A5'), ('A6'), ('A7'), ('A8'), ('A9'), ('A10');

INSERT OR IGNORE INTO users (student_number, full_name, password_hash)
VALUES (
    '12345',
    'Admin User',
    'scrypt:32768:8:1$O2R3EJ0ddKbkgPAU$0b730c33a5cb0efc904ce9628ecb45641590bd79749e000d394356ee00f8b4344eecba02308971becee98ac922b4b7e672a673dbb6a7b4f74c47ec14d858dcb1'
);