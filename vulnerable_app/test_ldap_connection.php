#!/usr/bin/env php
<?php
/**
 * Script de prueba de conectividad LDAP
 * Uso: php test_ldap_connection.php
 */

require_once __DIR__ . '/config.php';
require_once __DIR__ . '/auth_ldap.php';

echo "\n";
echo "═══════════════════════════════════════════════════════════\n";
echo "  PRUEBA DE CONECTIVIDAD LDAP - Sistema de Autenticación\n";
echo "═══════════════════════════════════════════════════════════\n\n";

// Mostrar configuración actual
echo "📋 CONFIGURACIÓN ACTUAL:\n";
echo "   - Servidor LDAP: $LDAP_HOST\n";
echo "   - Puerto: 389\n";
echo "   - Base DN: ou=usuarios,dc=softwarelibre,dc=local\n\n";

// Prueba 1: Verificación de socket
echo "🔍 PRUEBA 1: Verificación de Socket\n";
echo "   Intentando conectar al puerto 389...\n";

$socket_ok = verificar_servidor_ldap($LDAP_HOST, 389, 3);

if ($socket_ok) {
    echo "   ✅ Socket ABIERTO - El servidor responde en el puerto 389\n\n";
} else {
    echo "   ❌ Socket CERRADO - No se puede alcanzar el servidor\n";
    echo "   Posibles causas:\n";
    echo "   - Firewall bloqueando el puerto 389\n";
    echo "   - Servidor LDAP apagado\n";
    echo "   - IP incorrecta en .env\n";
    echo "   - Problemas de red\n\n";
}

// Prueba 2: Verificación de estado LDAP
echo "🔍 PRUEBA 2: Verificación de Estado LDAP\n";
echo "   Intentando conexión LDAP completa...\n";

$ldap_ok = verificar_estado_ldap();

if ($ldap_ok) {
    echo "   ✅ LDAP ONLINE - El servidor LDAP está operativo\n\n";
} else {
    echo "   ❌ LDAP OFFLINE - El servidor no responde correctamente\n";
    if ($ldap_connection_error) {
        echo "   Error: $ldap_connection_error\n\n";
    }
}

// Prueba 3: Autenticación de prueba (opcional)
echo "🔍 PRUEBA 3: Autenticación de Prueba (Opcional)\n";
echo "   ¿Desea probar autenticación con un usuario? (s/N): ";

$handle = fopen("php://stdin", "r");
$response = trim(fgets($handle));

if (strtolower($response) === 's') {
    echo "   Usuario: ";
    $username = trim(fgets($handle));
    
    echo "   Contraseña: ";
    system('stty -echo');
    $password = trim(fgets($handle));
    system('stty echo');
    echo "\n";
    
    echo "   Autenticando...\n";
    
    if (autenticar_con_ldap($username, $password)) {
        echo "   ✅ AUTENTICACIÓN EXITOSA\n";
        echo "   El usuario '$username' existe en el servidor LDAP\n\n";
    } else {
        echo "   ❌ AUTENTICACIÓN FALLIDA\n";
        if ($ldap_connection_error) {
            echo "   Error: $ldap_connection_error\n\n";
        }
    }
} else {
    echo "   Omitiendo prueba de autenticación.\n\n";
}

fclose($handle);

// Resumen final
echo "═══════════════════════════════════════════════════════════\n";
echo "  RESUMEN DE PRUEBAS\n";
echo "═══════════════════════════════════════════════════════════\n\n";

echo "Estado del Servidor LDAP:\n";
echo "   - Socket (Puerto 389): " . ($socket_ok ? "✅ ABIERTO" : "❌ CERRADO") . "\n";
echo "   - Servicio LDAP: " . ($ldap_ok ? "✅ ONLINE" : "❌ OFFLINE") . "\n\n";

if ($socket_ok && $ldap_ok) {
    echo "🎉 RESULTADO: El servidor LDAP está completamente operativo\n";
    echo "   Puede usar autenticación corporativa sin problemas.\n\n";
} elseif ($socket_ok && !$ldap_ok) {
    echo "⚠️  RESULTADO: El puerto está abierto pero el servicio no responde\n";
    echo "   Verifique la configuración del servidor LDAP.\n\n";
} else {
    echo "❌ RESULTADO: No se puede conectar al servidor LDAP\n";
    echo "   Revise la configuración de red y firewall.\n\n";
}

// Comandos de diagnóstico sugeridos
if (!$socket_ok || !$ldap_ok) {
    echo "🔧 COMANDOS DE DIAGNÓSTICO SUGERIDOS:\n\n";
    echo "   1. Verificar conectividad de red:\n";
    echo "      ping $LDAP_HOST\n\n";
    echo "   2. Verificar puerto LDAP:\n";
    echo "      telnet $LDAP_HOST 389\n";
    echo "      # o\n";
    echo "      nc -zv $LDAP_HOST 389\n\n";
    echo "   3. Verificar firewall local:\n";
    echo "      sudo iptables -L -n | grep 389\n\n";
    echo "   4. Verificar configuración:\n";
    echo "      cat ../.env | grep LDAP_IP\n\n";
}

echo "═══════════════════════════════════════════════════════════\n\n";
