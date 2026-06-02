CREATE TABLE bus_locations (
    bus_no VARCHAR(20) PRIMARY KEY,
    current_stop VARCHAR(100),
    next_stop VARCHAR(100),
    speed INT,
    eta VARCHAR(20),
    status VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- INSERT INTO bus_locations
-- (bus_no,current_stop,next_stop,speed,eta,status)
-- VALUES
-- ('DN43','Chinar Park','Technopolis',38,'12 mins','Running');