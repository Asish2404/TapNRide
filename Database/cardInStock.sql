CREATE TABLE cards_in_stock (
    id INT AUTO_INCREMENT PRIMARY KEY,   -- internal unique identifier for each card
    card_id VARCHAR(20) UNIQUE NOT NULL, -- actual RFID UID
    status ENUM('OPEN','CLOSED') DEFAULT 'OPEN' -- status of the card in stock,
);