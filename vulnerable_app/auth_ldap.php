<?php
/**
 * ARCHIVO: auth_ldap.php
 * Propósito: Módulo de autenticación LDAP (Integración Proyecto Agustín)
 */

$ldap_connection_error = null;

function autenticar_con_ldap($usuario, $password) {
    global $ldap_connection_error;
    
    // 1. Datos del Servidor LDAP (Configurables)
    $ldap_host = "10.172.86.161"; 
    $ldap_port = 389;
    $ldap_dn_base = "ou=usuarios,dc=softwarelibre,dc=local";

    // 2. Conectar al servidor
    $connect = @ldap_connect($ldap_host, $ldap_port);
    
    if (!$connect) {
        $ldap_connection_error = "Servidor LDAP inalcanzable.";
        return false;
    }

    ldap_set_option($connect, LDAP_OPT_PROTOCOL_VERSION, 3);
    ldap_set_option($connect, LDAP_OPT_NETWORK_TIMEOUT, 2);

    if ($connect) {
        $user_dn = "uid=" . $usuario . "," . $ldap_dn_base;
        $bind = @ldap_bind($connect, $user_dn, $password);

        if ($bind) {
            ldap_close($connect);
            return true; 
        } else {
            $ldap_connection_error = "Credenciales LDAP incorrectas o servidor rechazó conexión.";
            ldap_close($connect);
            return false;
        }
    }
    return false;
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
