CREATE TABLE transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    type ENUM('ride','recharge','fine') NOT NULL,
    card_id VARCHAR(20),
    description VARCHAR(255),
    amount DECIMAL(10,2) NOT NULL,
    transaction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    bus_no VARCHAR(20),
    device_id VARCHAR(150),
    fine_reason VARCHAR(150),
    FOREIGN KEY (card_id) REFERENCES cards(card_id)
);

-- dummy data
-- INSERT INTO transactions (transaction_id, card_id, bus_no, device_id, amount, type, transaction_time, description)
-- VALUES
-- (1001, 'x1190', '1234', '1.0.0.1', 15.00, 'ride', '2026-06-01 08:15:00','Garia St. -> Newtown');
