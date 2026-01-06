<?php
/**
 * config.php - Configuración centralizada
 * Carga valores desde el archivo .env en la raíz del proyecto
 */

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
$DB_HOST = isset($_ENV['DB_IP']) ? $_ENV['DB_IP'] : '127.0.0.1';
$DB_NAME = 'lab_vulnerable';
$DB_USER = 'webuser';
$DB_PASS = 'web123';

// Configuración de Servidores
$MAIN_SERVER_IP = isset($_ENV['NGINX_IP']) ? $_ENV['NGINX_IP'] : '127.0.0.1';
$MAIN_SERVER_PORT = '5000';
$LDAP_HOST = isset($_ENV['LDAP_IP']) ? $_ENV['LDAP_IP'] : '127.0.0.1';

// Rutas
$SURICATA_LOG_PATH = '../suricata/logs/eve.json';
$SURICATA_SENSOR_IP = isset($_ENV['NGINX_IP']) ? $_ENV['NGINX_IP'] : '127.0.0.1';
?>
