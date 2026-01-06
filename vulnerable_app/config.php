<?php
/**
 * config.php - Configuración centralizada
 */
error_reporting(E_ALL);
ini_set('display_errors', 1);

function loadEnv($path) {
    if(!file_exists($path)) return;
    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        if (strpos(trim($line), '#') === 0) continue;
        list($name, $value) = explode('=', $line, 2);
        $_ENV[trim($name)] = trim($value);
    }
}

// Cargar .env desde la raíz (un nivel arriba de vulnerable_app)
loadEnv(__DIR__ . '/../.env');

// Base de Datos (Prioriza .env, fallback a valores por defecto)
// Protección de Interbloqueo LDAP-DB
session_start();
$is_authorized = (isset($_SESSION['ldap_auth']) && $_SESSION['ldap_auth'] === true) || (isset($_SESSION['role']) && $_SESSION['role'] === 'basic');

if ($is_authorized) {
    $DB_HOST = isset($_ENV['DB_IP']) ? $_ENV['DB_IP'] : '127.0.0.1';
    $DB_USER = 'webuser';
    $DB_PASS = 'web123';
    $DB_NAME = 'lab_vulnerable';
} else {
    // Si no está autorizado, usamos credenciales que fallarán a propósito o valores nulos
    $DB_HOST = 'localhost';
    $DB_USER = 'guest';
    $DB_PASS = '';
    $DB_NAME = 'none';
}

$MAIN_SERVER_IP = isset($_ENV['ADMIN_IP']) ? $_ENV['ADMIN_IP'] : '127.0.0.1';
$LDAP_HOST = isset($_ENV['LDAP_IP']) ? $_ENV['LDAP_IP'] : '127.0.0.1';

// Rutas
$SURICATA_LOG_PATH = '../suricata/logs/eve.json';
$SURICATA_SENSOR_IP = isset($_ENV['NGINX_IP']) ? $_ENV['NGINX_IP'] : '127.0.0.1';
?>
