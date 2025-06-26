CREATE TABLE cvt(
    id INTEGER PRIMARY KEY AUTOINCREMENT,                    /* identifier for each row in the table */
    iso_date TEXT,                                           /* stores the calendar date in ISO 8601 format YYYY-MM-DD */
    yday INTEGER,                                            /* represents the day of the year - I used because it is useful for system-level date references often used in z/OS */
    cvt_address TEXT,                                        /* address of the communication vector table is stored here*/
    ecvt_address TEXT,                                       /* addrress of the extended CVT - points to newer control blocks and services that were not present in eralier OS states */
    tasks TEXT,                                              /* stores the ongoing task */
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP          /* records when snapshots are inserted into table - each row in the table is a snapshot*/
);
