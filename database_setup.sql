-- Script de creación de base de datos para el Servidor MySQL
DROP DATABASE IF EXISTS lab_vulnerable;
CREATE DATABASE lab_vulnerable;
USE lab_vulnerable;

-- Tabla de Usuarios (Vulnerable a SQLi)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(50) NOT NULL,
    role VARCHAR(20) NOT NULL
);

-- Insertar datos de prueba (Usuarios Tradicionales - NO Corporativos)
-- Estos usuarios NO existen en LDAP, solo en la base de datos local
INSERT INTO users (username, password, role) VALUES 
('admin', 'admin123', 'admin'),
('webmaster', 'web2024', 'admin'),
('operador', 'op123456', 'user'),
('soporte', 'support99', 'user'),
('invitado', 'guest2024', 'guest'),
('testuser', 'test123', 'user'),
('developer', 'dev2024', 'developer'),
('auditor', 'audit123', 'auditor');

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

-- Crear un usuario específico para la aplicación
CREATE USER IF NOT EXISTS 'webuser'@'%' IDENTIFIED BY 'web123';
GRANT ALL PRIVILEGES ON lab_vulnerable.* TO 'webuser'@'%';
FLUSH PRIVILEGES;
