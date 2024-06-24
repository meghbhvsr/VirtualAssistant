/* Run this SQL script to create the reminders table */

CREATE TABLE reminders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    task VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    time TIME NOT NULL,
    duration VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES accounts(id)
);

SELECT * FROM reminders WHERE user_id = 1