CREATE TABLE login (
    id INT AUTO_INCREMENT PRIMARY KEY,
    card_id VARCHAR(20),
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(15),
    password VARCHAR(255),
    role ENUM('passenger','driver','admin')
);