<?php
/**
 * test.php - Diagnóstico de Infraestructura Avanzado
 * Propósito: Detectar EXACTAMENTE por qué falla la conexión entre componentes.
 */

// Forzar visualización de errores solo aquí para diagnosticar
error_reporting(E_ALL);
ini_set('display_errors', 1);

function loadEnvDirect($path) {
    if(!file_exists($path)) return [];
    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    $env = [];
    foreach ($lines as $line) {
        if (strpos(trim($line), '#') === 0 || strpos($line, '=') === false) continue;
        list($name, $value) = explode('=', $line, 2);
        $env[trim($name)] = trim($value);
    }
    return $env;
}

$env = loadEnvDirect(__DIR__ . '/../.env');

// Configuración leída del .env
$db_ip = $env['DB_IP'] ?? 'NO DEFINIDA';
$db_user = $env['DB_USER'] ?? 'webuser';
$db_pass = $env['DB_PASS'] ?? 'web123';
$db_name = $env['DB_NAME'] ?? 'lab_vulnerable';
$ldap_ip = $env['LDAP_IP'] ?? 'NO DEFINIDA';
$admin_ip = $env['ADMIN_IP'] ?? 'NO DEFINIDA';

/**
 * Función para probar sockets (Conectividad real a nivel de red)
 */
function test_socket($ip, $port, $timeout = 2) {
    $start = microtime(true);
    $fp = @fsockopen($ip, $port, $errno, $errstr, $timeout);
    $end = microtime(true);
    $ms = round(($end - $start) * 1000, 2);
    
    if ($fp) {
        fclose($fp);
        return ["ok" => true, "ms" => $ms];
    }
    return ["ok" => false, "error" => $errstr, "code" => $errno];
}

/**
 * Función para simular envío del Log Shipper
 */
function test_shipper($admin_ip) {
    $url = "http://$admin_ip:5000/api/heartbeat";
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 3);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode(['status' => 'diagnostic_test', 'time' => date('Y-m-d H:i:s')]));
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    
    $response = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $curl_error = curl_error($ch);
    curl_close($ch);
    
    return [
        "url" => $url,
        "code" => $http_code,
        "response" => $response,
        "error" => $curl_error
    ];
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>SIA Diagnostics | Professional View</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #f8fafc; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .status-badge { @apply px-2 py-1 rounded text-xs font-bold uppercase; }
    </style>
</head>
<body class="p-4 md:p-8">
    <div class="max-w-5xl mx-auto">
        <header class="mb-8 flex justify-between items-end border-b pb-4">
            <div>
                <h1 class="text-3xl font-bold text-slate-800">🔍 Diagnóstico de Infraestructura</h1>
                <p class="text-slate-500">Verificando conectividad entre Nginx, DB, LDAP y Dashboard</p>
            </div>
            <div class="text-right text-xs text-slate-400 mono">
                PHP Version: <?php echo phpversion(); ?><br>
                Time: <?php echo date('H:i:s'); ?>
            </div>
        </header>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            <!-- 1. BASE DE DATOS (MYSQL) -->
            <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                <div class="flex justify-between items-start mb-4">
                    <h2 class="font-bold text-slate-700 flex items-center gap-2">
                        <span class="text-xl">🗄️</span> Base de Datos (3306)
                    </h2>
                    <?php 
                    $net_db = test_socket($db_ip, 3306);
                    if ($net_db['ok']): ?>
                        <span class="status-badge bg-green-100 text-green-700">Red OK (<?php echo $net_db['ms']; ?>ms)</span>
                    <?php else: ?>
                        <span class="status-badge bg-red-100 text-red-700">Inalcanzable</span>
                    <?php endif; ?>
                </div>
                
                <div class="space-y-3">
                    <div class="bg-slate-50 p-3 rounded mono text-[11px]">
                        Target: <?php echo $db_ip; ?>:3306<br>
                        User: <?php echo $db_user; ?><br>
                        DB: <?php echo $db_name; ?>
                    </div>

                    <?php
                    mysqli_report(MYSQLI_REPORT_OFF);
                    $start = microtime(true);
                    $conn = @new mysqli($db_ip, $db_user, $db_pass, $db_name);
                    $end = microtime(true);
                    $time = round(($end - $start) * 1000, 2);

                    if ($conn->connect_error): ?>
                        <div class="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-xs">
                            <strong>Error de MySQL:</strong><br>
                            <?php echo $conn->connect_error; ?>
                            <div class="mt-2 text-[10px] text-red-500 italic">
                                Sugerencia: Verifica privilegios del usuario '<?php echo $db_user; ?>'@'%' en la BD.
                            </div>
                        </div>
                    <?php else: ?>
                        <div class="p-3 bg-green-50 border border-green-200 rounded text-green-700 text-xs">
                            ✅ Autenticación Exitosa (<?php echo $time; ?>ms)<br>
                            <?php 
                            $res = $conn->query("SELECT VERSION() as v");
                            $row = $res->fetch_assoc();
                            echo "Server: " . $row['v'];
                            ?>
                        </div>
                    <?php $conn->close(); endif; ?>
                </div>
            </div>

            <!-- 2. SERVIDOR LDAP -->
            <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                <div class="flex justify-between items-start mb-4">
                    <h2 class="font-bold text-slate-700 flex items-center gap-2">
                        <span class="text-xl">🔑</span> Servidor LDAP (389)
                    </h2>
                    <?php 
                    $net_ldap = test_socket($ldap_ip, 389);
                    if ($net_ldap['ok']): ?>
                        <span class="status-badge bg-green-100 text-green-700">Red OK (<?php echo $net_ldap['ms']; ?>ms)</span>
                    <?php else: ?>
                        <span class="status-badge bg-red-100 text-red-700">Inalcanzable</span>
                    <?php endif; ?>
                </div>

                <div class="space-y-3">
                    <div class="bg-slate-50 p-3 rounded mono text-[11px]">
                        Target: <?php echo $ldap_ip; ?>:389<br>
                        Auth: Anonymous Bind Test
                    </div>

                    <?php if (!extension_loaded('ldap')): ?>
                        <div class="p-3 bg-orange-50 border border-orange-200 rounded text-orange-700 text-xs">
                            Extension 'ldap' no instalada en PHP.
                        </div>
                    <?php else: 
                        $ldap_conn = @ldap_connect($ldap_ip, 389);
                        if ($ldap_conn):
                            ldap_set_option($ldap_conn, LDAP_OPT_PROTOCOL_VERSION, 3);
                            ldap_set_option($ldap_conn, LDAP_OPT_NETWORK_TIMEOUT, 2);
                            $bind = @ldap_bind($ldap_conn); // Anonymous bind simple test
                    ?>
                            <div class="p-3 bg-blue-50 border border-blue-200 rounded text-blue-700 text-xs">
                                Respondiendo a nivel de protocolo.<br>
                                Anonymous Bind: <?php echo $bind ? "Habilitado" : "No permitido (Requiere credenciales)"; ?>
                            </div>
                        <?php else: ?>
                            <div class="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-xs">
                                Fallo al conectar con el protocolo LDAP.
                            </div>
                    <?php endif; endif; ?>
                </div>
            </div>

            <!-- 3. LOG SHIPPER & DASHBOARD -->
            <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                <div class="flex justify-between items-start mb-4">
                    <h2 class="font-bold text-slate-700 flex items-center gap-2">
                        <span class="text-xl">📊</span> Dashboard Shipper (5000)
                    </h2>
                    <?php 
                    $net_dash = test_socket($admin_ip, 5000);
                    if ($net_dash['ok']): ?>
                        <span class="status-badge bg-green-100 text-green-700">Red OK (<?php echo $net_dash['ms']; ?>ms)</span>
                    <?php else: ?>
                        <span class="status-badge bg-red-100 text-red-700">Inalcanzable</span>
                    <?php endif; ?>
                </div>

                <div class="space-y-3">
                    <div class="bg-slate-50 p-3 rounded mono text-[11px]">
                        Dashboard: <?php echo $admin_ip; ?>:5000<br>
                        Endpoint: /api/heartbeat
                    </div>

                    <?php 
                    $ship_res = test_shipper($admin_ip);
                    if ($ship_res['code'] == 200 || $ship_res['code'] == 404): // 404 es aceptable si el endpoint no existe pero el server responde ?>
                        <div class="p-3 bg-green-50 border border-green-200 rounded text-green-700 text-xs">
                            ✅ Dashboard Responde (HTTP <?php echo $ship_res['code']; ?>)<br>
                            <span class="text-[10px]">Response: <?php echo htmlspecialchars(substr($ship_res['response'], 0, 50)); ?>...</span>
                        </div>
                    <?php else: ?>
                        <div class="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-xs">
                            ❌ Dashboard sin respuesta HTTP.<br>
                            Error: <?php echo $ship_res['error'] ?: "Código HTTP " . $ship_res['code']; ?>
                            <div class="mt-2 text-[10px] text-red-500 italic">
                                Asegúrate de que main.py esté corriendo en <?php echo $admin_ip; ?>.
                            </div>
                        </div>
                    <?php endif; ?>
                </div>
            </div>

            <!-- 4. PERMISOS Y ENTORNO -->
            <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                <h2 class="font-bold text-slate-700 flex items-center gap-2 mb-4">
                    <span class="text-xl">📁</span> Entorno y Permisos
                </h2>
                <div class="grid grid-cols-2 gap-2 text-[11px]">
                    <div class="p-2 border rounded flex justify-between">
                        <span>Archivo .env</span>
                        <span class="<?php echo file_exists(__DIR__ . '/../.env') ? 'text-green-600' : 'text-red-600'; ?>">
                            <?php echo file_exists(__DIR__ . '/../.env') ? 'Detectado' : 'FALTANTE'; ?>
                        </span>
                    </div>
                    <div class="p-2 border rounded flex justify-between">
                        <span>Escritura Temp</span>
                        <span class="<?php echo is_writable(sys_get_temp_dir()) ? 'text-green-600' : 'text-red-600'; ?>">
                            <?php echo is_writable(sys_get_temp_dir()) ? 'OK' : 'Error'; ?>
                        </span>
                    </div>
                </div>
                
                <div class="mt-4 p-3 bg-indigo-50 border border-indigo-100 rounded text-indigo-700 text-[10px] mono">
                    <strong>Local IP:</strong> <?php echo $_SERVER['SERVER_ADDR'] ?? 'Unknown'; ?><br>
                    <strong>Web root:</strong> <?php echo __DIR__; ?><br>
                    <strong>Extensions:</strong> 
                    <?php echo extension_loaded('mysqli') ? '[mysqli] ' : '[Falta mysqli] '; ?>
                    <?php echo extension_loaded('ldap') ? '[ldap] ' : '[Falta ldap] '; ?>
                    <?php echo extension_loaded('curl') ? '[curl]' : '[Falta curl]'; ?>
                </div>
            </div>

        </div>

        <footer class="mt-8 text-center text-slate-400 text-xs">
            Refresca para volver a probar. SIA Infrastructure Diagnostic Tool v2.0
        </footer>
    </div>
</body>
</html>
