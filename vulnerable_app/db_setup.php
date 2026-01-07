<?php
/**
 * db_setup.php - Configuración de la conexión a MySQL
 * 
 * Migrado de SQLite a MySQL (Servidor remoto: 192.168.1.57)
 */

require_once __DIR__ . '/config.php';

$host = $DB_HOST;
$dbname = $DB_NAME;
$user = $DB_USER;
$pass = $DB_PASS;

$db_connection_error = null;
$db = null;
try {
    // Conexión a MySQL usando PDO
    $dsn = "mysql:host=$host;dbname=$dbname;charset=utf8mb4";
    $db = new PDO($dsn, $user, $pass);
    
    // IMPORTANTE para el laboratorio: 
    // Mantenemos esta configuración para que las inyecciones SQL funcionen correctamente
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $db->setAttribute(PDO::ATTR_EMULATE_PREPARES, true); 

} catch (PDOException $e) {
    $db_connection_error = "MySQL Off-line: " . $e->getMessage();
}
?>
