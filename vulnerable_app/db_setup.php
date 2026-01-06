<?php
/**
 * db_setup.php - Configuración de la conexión a MySQL
 * 
 * Migrado de SQLite a MySQL (Servidor remoto: 192.168.1.57)
 */

function loadEnv($path) {
    if (!file_exists($path)) return [];
    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    $env = [];
    foreach ($lines as $line) {
        if (strpos(trim($line), '#') === 0) continue;
        if (strpos($line, '=') === false) continue;
        list($name, $value) = explode('=', $line, 2);
        $env[trim($name)] = trim($value);
    }
    return $env;
}

$env = loadEnv(__DIR__ . '/../.env');

$host = $env['DB_HOST'] ?? '127.0.0.1';
$dbname = $env['DB_NAME'] ?? 'lab_vulnerable';
$user = $env['DB_USER'] ?? 'root';
$pass = $env['DB_PASS'] ?? '';

try {
    // Conexión a MySQL usando PDO
    $dsn = "mysql:host=$host;dbname=$dbname;charset=utf8mb4";
    $db = new PDO($dsn, $user, $pass);
    
    // IMPORTANTE para el laboratorio: 
    // Mantenemos esta configuración para que las inyecciones SQL funcionen correctamente
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $db->setAttribute(PDO::ATTR_EMULATE_PREPARES, true); 

} catch (PDOException $e) {
    die("Error de conexión a la base de datos: " . $e->getMessage());
}
?>
