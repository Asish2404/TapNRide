CREATE TABLE buses (
bus_id INT AUTO_INCREMENT PRIMARY KEY,
bus_no VARCHAR(20),
owner_id int,
route VARCHAR(150)
);

-- DUMMY DATA
-- INSERT INTO buses(bus_id,bus_no,owner_id,route) VALUES
-- (1,'1234',101,'R-BB'),
-- (2,'7235',101,'R-HG'),
-- (3,'AS3',101,'R-GSTN'),
-- (4,'9907',101,'R-KH'),
-- (5,'9828',101,'R-KD');