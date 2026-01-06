<?php
/**
 * test.php - Archivo de diagnóstico para verificar conectividad
 * Este archivo IGNORA el interbloqueo LDAP para propósitos de diagnóstico
 */

// Cargar .env directamente sin pasar por config.php
function loadEnvDirect($path) {
    $env = [];
    if(!file_exists($path)) return $env;
    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        if (strpos(trim($line), '#') === 0) continue;
        if (strpos($line, '=') === false) continue;
        list($name, $value) = explode('=', $line, 2);
        $env[trim($name)] = trim($value);
    }
    return $env;
}

$env = loadEnvDirect(__DIR__ . '/../.env');

// Usar credenciales directamente del .env (sin interbloqueo)
$DB_HOST = $env['DB_IP'] ?? '127.0.0.1';
$DB_USER = $env['DB_USER'] ?? 'webuser';
$DB_PASS = $env['DB_PASS'] ?? 'web123';
$DB_NAME = $env['DB_NAME'] ?? 'lab_vulnerable';
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Diagnóstico del Sistema</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            padding: 2rem;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        h1 {
            color: white;
            margin-bottom: 2rem;
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        .card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        .card h2 {
            color: #1e3c72;
            margin-bottom: 1rem;
            font-size: 1.2rem;
        }
        .status {
            padding: 0.75rem 1rem;
            border-radius: 8px;
            font-weight: 600;
            margin-top: 0.5rem;
        }
        .success {
            background: #d4edda;
            color: #155724;
            border-left: 4px solid #28a745;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
            border-left: 4px solid #dc3545;
        }
        .info {
            background: #d1ecf1;
            color: #0c5460;
            border-left: 4px solid #17a2b8;
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }
        code {
            background: #f4f4f4;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Diagnóstico del Sistema</h1>
        
        <!-- Test 1: Conexión a Base de Datos -->
        <div class="card">
            <h2>1. Conexión a Base de Datos (MySQL)</h2>
            <?php
            $conn = @new mysqli($DB_HOST, $DB_USER, $DB_PASS, $DB_NAME);
            
            if ($conn->connect_error) {
                echo '<div class="status error">';
                echo '❌ ERROR DE CONEXIÓN';
                echo '</div>';
                echo '<div class="info">';
                echo htmlspecialchars($conn->connect_error);
                echo '</div>';
            } else {
                echo '<div class="status success">';
                echo '✅ CONECTADO';
                echo '</div>';
                echo '<div class="info">';
                echo "Host: <code>$DB_HOST</code><br>";
                echo "Usuario: <code>$DB_USER</code><br>";
                echo "Base de Datos: <code>$DB_NAME</code>";
                echo '</div>';
                $conn->close();
            }
            ?>
        </div>

        <!-- Test 2: Conexión a Servidor LDAP -->
        <div class="card">
            <h2>2. Conexión a Servidor LDAP</h2>
            <?php
            $LDAP_HOST = $env['LDAP_IP'] ?? '127.0.0.1';
            $ldap_conn = @ldap_connect($LDAP_HOST);
            
            if ($ldap_conn) {
                echo '<div class="status success">';
                echo '✅ RESPONDIENDO';
                echo '</div>';
                echo '<div class="info">';
                echo "Servidor LDAP: <code>$LDAP_HOST</code>";
                echo '</div>';
                @ldap_close($ldap_conn);
            } else {
                echo '<div class="status error">';
                echo '❌ NO RESPONDE';
                echo '</div>';
                echo '<div class="info">';
                echo "Servidor LDAP: <code>$LDAP_HOST</code>";
                echo '</div>';
            }
            ?>
        </div>

        <!-- Test 3: Ruta al Dashboard -->
        <div class="card">
            <h2>3. Ruta al Dashboard (Main Server)</h2>
            <?php
            $ADMIN_IP = $env['ADMIN_IP'] ?? '127.0.0.1';
            $dashboard_url = "http://$ADMIN_IP:5000";
            echo '<div class="info">';
            echo "URL configurada: <a href='$dashboard_url' target='_blank'>$dashboard_url</a><br>";
            echo '<small>Nota: El Shipper usará esta ruta para enviar las alertas de Suricata.</small>';
            echo '</div>';
            ?>
        </div>
    </div>
</body>
</html>
