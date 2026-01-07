<?php
/**
 * config.php - Configuración centralizada
 * ÚNICA FUENTE DE VERDAD: Archivo .env
 */
error_reporting(0);
ini_set('display_errors', 0);

function loadEnv($path) {
    if(!file_exists($path)) return;
    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        if (strpos(trim($line), '#') === 0) continue;
        if (strpos($line, '=') === false) continue;
        list($name, $value) = explode('=', $line, 2);
        $_ENV[trim($name)] = trim($value);
    }
}

// Cargar .env desde la raíz (un nivel arriba de vulnerable_app)
loadEnv(__DIR__ . '/../.env');

// Protección de Interbloqueo LDAP-DB
session_start();
$is_login_page = basename($_SERVER['PHP_SELF']) === 'index.php';
$is_authorized = (isset($_SESSION['ldap_auth']) && $_SESSION['ldap_auth'] === true) || 
                 (isset($_SESSION['role']) && $_SESSION['role'] === 'basic') || 
                 $is_login_page;

// Base de Datos - SOLO desde .env
if ($is_authorized) {
    $DB_HOST = isset($_ENV['DB_IP']) ? $_ENV['DB_IP'] : '127.0.0.1';
    $DB_USER = isset($_ENV['DB_USER']) ? $_ENV['DB_USER'] : 'webuser';
    $DB_PASS = isset($_ENV['DB_PASS']) ? $_ENV['DB_PASS'] : 'web123';
    $DB_NAME = isset($_ENV['DB_NAME']) ? $_ENV['DB_NAME'] : 'lab_vulnerable';
} else {
    // Si no está autorizado, credenciales que fallarán
    $DB_HOST = 'localhost';
    $DB_USER = 'guest';
    $DB_PASS = '';
    $DB_NAME = 'none';
}

// Configuración de Servidores - SOLO desde .env
$MAIN_SERVER_IP = isset($_ENV['ADMIN_IP']) ? $_ENV['ADMIN_IP'] : '127.0.0.1';
$MAIN_SERVER_PORT = '5000';
$LDAP_HOST = isset($_ENV['LDAP_IP']) ? $_ENV['LDAP_IP'] : '127.0.0.1';
$LDAP_DOMAIN = isset($_ENV['LDAP_DOMAIN']) ? $_ENV['LDAP_DOMAIN'] : 'example.com';
$SURICATA_SENSOR_IP = isset($_ENV['NGINX_IP']) ? $_ENV['NGINX_IP'] : '127.0.0.1';

// Rutas
$SURICATA_LOG_PATH = '../suricata/logs/eve.json';

// --- SEGUIMIENTO GLOBAL DE ACTIVIDAD ---
require_once __DIR__ . '/log_shipper.php';
if (basename($_SERVER['PHP_SELF']) !== 'test.php') {
    ship_log("page_view", "Usuario visitó la página", [
        "page" => basename($_SERVER['PHP_SELF']),
        "user" => $_SESSION['user'] ?? 'Anonimo'
    ]);
}
?>
