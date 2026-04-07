CREATE TABLE rides (
    ride_id INT AUTO_INCREMENT PRIMARY KEY,
    card_id VARCHAR(20),
    from_stop VARCHAR(100) NOT NULL,
    to_stop VARCHAR(100),
    fare DECIMAL(10,2) NOT NULL,
    ride_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (card_id) REFERENCES cards(card_id)
);

