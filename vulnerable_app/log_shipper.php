<?php
/**
 * log_shipper.php - Envía eventos de la aplicación al Dashboard Central
 */

function ship_log($event_type, $message, $extra_data = []) {
    require_once __DIR__ . '/config.php';
    global $MAIN_SERVER_IP, $MAIN_SERVER_PORT;

    $url = "http://$MAIN_SERVER_IP:$MAIN_SERVER_PORT/";
    
    $log_data = [
        "timestamp" => date('c'),
        "event_type" => "app_event",
        "app_module" => $event_type,
        "message" => $message,
        "src_ip" => $_SERVER['REMOTE_ADDR'] ?? 'unknown',
        "user_agent" => $_SERVER['HTTP_USER_AGENT'] ?? 'unknown',
        "uri" => $_SERVER['REQUEST_URI'] ?? 'unknown'
    ];

    $payload = array_merge($log_data, $extra_data);

    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($payload));
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    curl_setopt($ch, CURLOPT_TIMEOUT, 1); // No bloquear la web si el dashboard está lento
    
    $result = curl_exec($ch);
    curl_close($ch);
    return $result;
}
?>
