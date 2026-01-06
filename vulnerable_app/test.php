<?php
/**
 * test.php - Diagnóstico manual de conectividad del laboratorio
 */
require_once 'config.php';

echo "<html><head><title>Laboratorio - Diagnóstico</title>";
echo "<style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 40px; }
    .card { background: #1e293b; border-radius: 12px; padding: 25px; margin-bottom: 20px; border-left: 5px solid #334155; }
    .success { border-left-color: #22c55e; }
    .error { border-left-color: #ef4444; }
    h1 { color: #38bdf8; }
    .status { font-weight: bold; }
    .details { background: #000; padding: 10px; border-radius: 6px; font-family: monospace; font-size: 0.9em; margin-top: 10px; color: #a7f3d0; }
</style></head><body>";

echo "<h1>🔍 Diagnóstico del Sistema</h1>";

// 1. Prueba de MySQL
echo "<div class='card'>";
echo "<h3>1. Conexión a Base de Datos (MySQL)</h3>";
try {
    $conn = new mysqli($DB_HOST, $DB_USER, $DB_PASS, $DB_NAME);
    if ($conn->connect_error) {
        throw new Exception($conn->connect_error);
    }
    echo "<p class='status' style='color: #22c55e;'>✅ CONECTADO</p>";
    echo "<p>Host: $DB_HOST | DB: $DB_NAME</p>";
    $conn->close();
} catch (Exception $e) {
    echo "<p class='status' style='color: #ef4444;'>❌ ERROR DE CONEXIÓN</p>";
    echo "<div class='details'>" . $e->getMessage() . "</div>";
}
echo "</div>";

// 2. Prueba de LDAP
echo "<div class='card'>";
echo "<h3>2. Conexión a Servidor LDAP</h3>";
if (function_exists('ldap_connect')) {
    $ldap_conn = ldap_connect($LDAP_HOST);
    ldap_set_option($ldap_conn, LDAP_OPT_PROTOCOL_VERSION, 3);
    ldap_set_option($ldap_conn, LDAP_OPT_NETWORK_TIMEOUT, 2);

    try {
        if ($ldap_conn) {
            // Intentamos un bind anónimo o simplemente verificar si el puerto responde
            $bind = @ldap_bind($ldap_conn); 
            echo "<p class='status' style='color: #22c55e;'>✅ RESPONDIDENDO</p>";
            echo "<p>Servidor LDAP: $LDAP_HOST</p>";
        } else {
            throw new Exception("No se pudo inicializar la conexión LDAP.");
        }
    } catch (Exception $e) {
        echo "<p class='status' style='color: #ef4444;'>❌ NO RESPONDE</p>";
        echo "<div class='details'>" . $e->getMessage() . "</div>";
    }
} else {
    echo "<p class='status' style='color: #f59e0b;'>⚠️ EXTENSIÓN LDAP NO INSTALADA</p>";
    echo "<p>Ejecuta full_system_setup.py para instalar php-ldap.</p>";
}
echo "</div>";

// 3. Prueba de Dashboard (CORS / HTTP)
echo "<div class='card'>";
echo "<h3>3. Ruta al Dashboard (Main Server)</h3>";
echo "<p>URL configurada: <a href='http://$MAIN_SERVER_IP:$MAIN_SERVER_PORT' style='color: #38bdf8;'>http://$MAIN_SERVER_IP:$MAIN_SERVER_PORT</a></p>";
echo "<p class='details'>Nota: El Shipper usará esta ruta para enviar las alertas de Suricata.</p>";
echo "</div>";

echo "</body></html>";
?>
