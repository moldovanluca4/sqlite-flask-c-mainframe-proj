CREATE TABLE IF NOT EXISTS cvt (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    iso_date TEXT,
    yday INTEGER,
    cvt_address TEXT,
    ecvt_address TEXT,
    tasks TEXT,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
