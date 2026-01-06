-- Script de creación de base de datos para el Servidor MySQL (192.168.1.57)

CREATE DATABASE IF NOT EXISTS lab_vulnerable;
USE lab_vulnerable;

-- Tabla de Usuarios (Vulnerable a SQLi)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(50) NOT NULL,
    role VARCHAR(20) NOT NULL
);

-- Insertar datos de prueba
INSERT INTO users (username, password, role) VALUES 
('admin', 'admin123', 'admin'),
('user', 'user123', 'user'),
('root', 'toor', 'admin');

-- Tabla de Productos (Vulnerable a XSS/SQLi)
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL
);

-- Insertar datos de prueba
INSERT INTO products (name, description) VALUES 
('Laptop Pro', 'Potente estación de trabajo para desarrollo.'),
('Mouse Gamer', 'Mouse con sensor óptico de alta precisión.'),
('Teclado Mecánico', 'Teclado con switches Blue y retroiluminación RGB.'),
('Monitor 4K', 'Monitor Ultra HD para diseño gráfico.');

-- Crear un usuario específico para la aplicación (Opcional pero recomendado)
-- CREATE USER 'app_user'@'%' IDENTIFIED BY 'password123';
-- GRANT ALL PRIVILEGES ON lab_vulnerable.* TO 'app_user'@'%';
-- FLUSH PRIVILEGES;
