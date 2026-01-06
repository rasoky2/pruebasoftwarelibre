<?php
/**
 * ARCHIVO: auth_ldap.php
 * Propósito: Módulo de autenticación LDAP (Integración Proyecto Agustín)
 */

function autenticar_con_ldap($usuario, $password) {
    // 1. Datos del Servidor LDAP (Agustín)
    $ldap_host = "10.172.86.161"; 
    $ldap_port = 389;
    $ldap_dn_base = "ou=usuarios,dc=softwarelibre,dc=local";

    // 2. Conectar al servidor
    $connect = ldap_connect($ldap_host, $ldap_port);
    
    // Es vital usar la versión 3 para servidores modernos
    ldap_set_option($connect, LDAP_OPT_PROTOCOL_VERSION, 3);
    ldap_set_option($connect, LDAP_OPT_REFERRALS, 0);

    if ($connect) {
        // 3. Formatear el DN del usuario según la estructura de Agustín
        $user_dn = "uid=" . $usuario . "," . $ldap_dn_base;

        // 4. Intentar la vinculación (Login)
        // Usamos @ para que PHP no muestre warnings si la clave está mal
        $bind = @ldap_bind($connect, $user_dn, $password);

        if ($bind) {
            ldap_close($connect);
            return true; 
        } else {
            ldap_close($connect);
            return false;
        }
    } else {
        return false;
    }
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
