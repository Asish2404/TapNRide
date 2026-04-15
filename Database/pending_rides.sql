CREATE TABLE pending_rides (
    id INT AUTO_INCREMENT PRIMARY KEY,
    card_id VARCHAR(20) NOT NULL,
    from_stop VARCHAR(50) NOT NULL,
    to_stop VARCHAR(50) NOT NULL,
    fare DECIMAL(10,2) NOT NULL
);
