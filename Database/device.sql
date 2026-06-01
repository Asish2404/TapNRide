CREATE TABLE devices (
    device_id VARCHAR(150) PRIMARY KEY,   
    bus_id INT,  
    FOREIGN KEY (bus_id) REFERENCES buses(bus_id)
);

-- dummy data
-- INSERT INTO devices VALUES
-- ('1.0.0.1',1),
-- ('10.0.0.2',2),
-- ('100.0.0.3',3),
-- ('105.0.0.4',4),
-- ('123.0.0.5',5);