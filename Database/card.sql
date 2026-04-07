CREATE TABLE cards (
    card_id VARCHAR(20) PRIMARY KEY,
    balance DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    status ENUM('active','blocked') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);