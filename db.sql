CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fullname VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    password VARCHAR(255),
    role ENUM('user','owner','admin') DEFAULT 'user',
    isadmin BOOLEAN DEFAULT FALSE,
    isverified BOOLEAN DEFAULT FALSE,
    isactive BOOLEAN DEFAULT TRUE
);

CREATE TABLE owners (
    owner_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE,
    citizenship_no VARCHAR(50),
    citizenship_photo VARCHAR(255),
    profile_photo VARCHAR(255),
    address VARCHAR(255),
    approved BOOLEAN DEFAULT FALSE,
    approved_by INT,
    approved_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE rooms (
    room_id INT AUTO_INCREMENT PRIMARY KEY,

    owner_id INT NOT NULL,

    title VARCHAR(150) NOT NULL,
    description TEXT,

    price DECIMAL(10,2) NOT NULL,

    address VARCHAR(255) NOT NULL,

    latitude DECIMAL(10,8) NOT NULL,
    longitude DECIMAL(11,8) NOT NULL,

    room_image VARCHAR(255),

    is_available BOOLEAN DEFAULT TRUE,

    approved BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (owner_id)
    REFERENCES owners(owner_id)
    ON DELETE CASCADE
);

CREATE TABLE interesteds(

    interest_id INT AUTO_INCREMENT PRIMARY KEY,

    room_id INT NOT NULL,

    user_id INT NOT NULL,

    message TEXT,

    status ENUM('pending','accepted','rejected') DEFAULT 'pending',

    interested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (room_id)
        REFERENCES rooms(room_id)
        ON DELETE CASCADE,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    UNIQUE(room_id, user_id)

);