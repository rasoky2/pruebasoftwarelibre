<?php
// Configuración de la base de datos SQLite
$db = new PDO('sqlite:database.sqlite');
$db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

// Crear tabla de usuarios si no existe
$db->exec("CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT,
    role TEXT
)");

// Insertar usuario de prueba si está vacío
$stmt = $db->query("SELECT COUNT(*) FROM users");
if ($stmt->fetchColumn() == 0) {
    $db->exec("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin')");
    $db->exec("INSERT INTO users (username, password, role) VALUES ('user', 'user123', 'user')");
}

// Crear tabla de productos para búsqueda
$db->exec("CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT
)");

$stmt = $db->query("SELECT COUNT(*) FROM products");
if ($stmt->fetchColumn() == 0) {
    $db->exec("INSERT INTO products (name, description) VALUES ('Laptop', 'Potente laptop para gaming')");
    $db->exec("INSERT INTO products (name, description) VALUES ('Mouse', 'Mouse óptico ergonómico')");
    $db->exec("INSERT INTO products (name, description) VALUES ('Teclado', 'Teclado mecánico RGB')");
}
?>
