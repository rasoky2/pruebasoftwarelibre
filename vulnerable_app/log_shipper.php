<?php
/**
 * Log Shipper - Envia logs de Suricata al Servidor Main
 * 
 * Este script debe ejecutarse en segundo plano en el Nodo de Borde.
 * Lee el archivo eve.json y envía cada alerta vía HTTP POST.
 */

/**
 * Carga variables desde un archivo .env simple
 */
function loadEnv($path) {
    if (!file_exists($path)) return [];
    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    $env = [];
    foreach ($lines as $line) {
        if (strpos(trim($line), '#') === 0) continue;
        list($name, $value) = explode('=', $line, 2);
        $env[trim($name)] = trim($value);
    }
    return $env;
}

$env = loadEnv(__DIR__ . '/../.env');

$suricataLogPath = __DIR__ . '/' . ($env['SURICATA_LOG_PATH'] ?? '../suricata/logs/eve.json');
$mainServerIp = $env['MAIN_SERVER_IP'] ?? '127.0.0.1';
$mainServerPort = $env['MAIN_SERVER_PORT'] ?? '5000';
$mainServerUrl = "http://$mainServerIp:$mainServerPort";

echo "Iniciando Shipper de Logs apuntando a $mainServerUrl...\n";

// Abrir el archivo de logs
$handle = fopen($suricataLogPath, 'r');
if (!$handle) {
    die("Error: No se pudo abrir el archivo de logs en $suricataLogPath\n");
}

// Mover el puntero al final para solo enviar logs nuevos
fseek($handle, 0, SEEK_END);

while (true) {
    $line = fgets($handle);
    
    if ($line === false) {
        // No hay líneas nuevas, esperar un momento
        usleep(500000); // 0.5 segundos
        clearstatcache();
        continue;
    }

    $logData = json_decode($line, true);
    
    // Solo enviar si es una alerta
    if (isset($logData['event_type']) && $logData['event_type'] === 'alert') {
        enviarLog($logData, $mainServerUrl);
    }
}

function enviarLog($data, $url) {
    echo "Enviando alerta detectada: " . ($data['alert']['signature'] ?? 'Unknown') . "\n";
    
    $payload = json_encode($data);
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
    curl_setopt($ch, CURLOPT_HTTPHEADER, array('Content-Type:application/json'));
    
    $result = curl_exec($ch);
    $status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($status !== 200) {
        echo "Error al enviar log al Main (Status: $status)\n";
    }
}
?>
