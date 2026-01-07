<?php
/**
 * ARCHIVO: auth_ldap.php
 * Propósito: Módulo de autenticación LDAP (Integración Proyecto Agustín)
 * Versión: 2.0 - Detección mejorada de conectividad
 */

require_once __DIR__ . '/config.php';

$ldap_connection_error = null;
$ldap_server_online = false;

/**
 * Verifica si el servidor LDAP está accesible mediante socket
 */
function verificar_servidor_ldap($host, $port = 389, $timeout = 2) {
    $socket = @fsockopen($host, $port, $errno, $errstr, $timeout);
    if ($socket) {
        fclose($socket);
        return true;
    }
    return false;
}

/**
 * Autenticación con servidor LDAP corporativo
 */
function autenticar_con_ldap($usuario, $password) {
    global $ldap_connection_error, $LDAP_HOST, $LDAP_DOMAIN;
    
    // Datos del Servidor LDAP (desde config.php / .env)
    $ldap_host = $LDAP_HOST;
    $ldap_port = 389;
    
    // Construir base DN desde el dominio configurado
    // Ejemplo: "prueba.com" -> "dc=prueba,dc=com"
    $domain_parts = explode('.', $LDAP_DOMAIN);
    $dc_parts = array_map(function($part) { return "dc=$part"; }, $domain_parts);
    $ldap_dn_base = "ou=users," . implode(',', $dc_parts);

    // Verificación previa de conectividad
    if (!verificar_servidor_ldap($ldap_host, $ldap_port, 2)) {
        $ldap_connection_error = "Servidor LDAP inalcanzable ($ldap_host:$ldap_port)";
        return false;
    }

    // Intentar conexión LDAP
    $connect = @ldap_connect($ldap_host, $ldap_port);
    
    if (!$connect) {
        $ldap_connection_error = "Error al inicializar conexión LDAP";
        return false;
    }

    // Configurar opciones de protocolo
    ldap_set_option($connect, LDAP_OPT_PROTOCOL_VERSION, 3);
    ldap_set_option($connect, LDAP_OPT_NETWORK_TIMEOUT, 3);
    ldap_set_option($connect, LDAP_OPT_REFERRALS, 0);

    // Construir DN del usuario
    $user_dn = "uid=" . ldap_escape($usuario, '', LDAP_ESCAPE_DN) . "," . $ldap_dn_base;
    
    // Intentar autenticación
    $bind = @ldap_bind($connect, $user_dn, $password);

    if ($bind) {
        ldap_close($connect);
        return true;
    } else {
        $error_code = ldap_errno($connect);
        if ($error_code === 49) {
            $ldap_connection_error = "Credenciales LDAP incorrectas";
        } else {
            $ldap_connection_error = "Error de autenticación LDAP (Código: $error_code)";
        }
        ldap_close($connect);
        return false;
    }
}

/**
 * Verifica el estado del servidor LDAP (para health check)
 */
function verificar_estado_ldap() {
    global $ldap_server_online, $ldap_connection_error, $LDAP_HOST;
    
    $ldap_host = $LDAP_HOST;
    $ldap_port = 389;
    
    // Verificar conectividad básica
    if (!verificar_servidor_ldap($ldap_host, $ldap_port, 2)) {
        $ldap_server_online = false;
        $ldap_connection_error = "Servidor LDAP inalcanzable";
        return false;
    }
    
    // Intentar conexión completa
    $connect = @ldap_connect($ldap_host, $ldap_port);
    if ($connect) {
        ldap_set_option($connect, LDAP_OPT_PROTOCOL_VERSION, 3);
        ldap_set_option($connect, LDAP_OPT_NETWORK_TIMEOUT, 2);
        
        // Intentar bind anónimo para verificar que el servidor responde
        $bind = @ldap_bind($connect);
        ldap_close($connect);
        
        $ldap_server_online = true;
        $ldap_connection_error = null;
        return true;
    }
    
    $ldap_server_online = false;
    $ldap_connection_error = "Servidor LDAP no responde";
    return false;
}

// Verificar estado al cargar el módulo
verificar_estado_ldap();

/**
 * Busca usuarios en el directorio LDAP
 * VULNERABLE A LDAP INJECTION: No sanitiza la entrada $busqueda
 */
function buscar_usuarios_ldap($busqueda) {
    global $LDAP_HOST, $LDAP_DOMAIN;

    $ldap_host = $LDAP_HOST;
    $ldap_port = 389;

    // DN Base
    $domain_parts = explode('.', $LDAP_DOMAIN);
    $dc_parts = array_map(function($part) { return "dc=$part"; }, $domain_parts);
    $ldap_dn_base = "ou=users," . implode(',', $dc_parts);

    $connect = @ldap_connect($ldap_host, $ldap_port);
    if (!$connect) return [];

    ldap_set_option($connect, LDAP_OPT_PROTOCOL_VERSION, 3);
    ldap_set_option($connect, LDAP_OPT_REFERRALS, 0);

    // Bind Anónimo para búsqueda pública
    if (@ldap_bind($connect)) {
        // FILTRO VULNERABLE: Concatenación directa
        // Intenta inyectar: *) (uid=admin
        $filter = "(|(uid=*$busqueda*)(cn=*$busqueda*)(mail=*$busqueda*))";
        
        // Solo buscar personas
        $final_filter = "(&(objectClass=person)$filter)";

        $search = @ldap_search($connect, $ldap_dn_base, $final_filter);
        if ($search) {
            $entries = ldap_get_entries($connect, $search);
            ldap_close($connect);
            return $entries;
        }
    }
    ldap_close($connect);
    return [];
}

// Logica de procesamiento si se accede directamente (opcional)
if (isset($_POST['ldap_login'])) {
    $user = $_POST['usuario'];
    $pass = $_POST['password'];

    if (autenticar_con_ldap($user, $pass)) {
        session_start();
        $_SESSION['usuario'] = $user;
        $_SESSION['auth_method'] = 'LDAP';
        header("Location: welcome.php");
    } else {
        header("Location: index.php?error=ldap_failed");
    }
}
?>
