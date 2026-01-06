# Sistema de Autenticación Dual

## Descripción General

Este sistema implementa **dos métodos de autenticación independientes**:

1. **Autenticación Tradicional (Base de Datos MySQL)**
2. **Autenticación Corporativa (LDAP)**

---

## 🔐 Autenticación Tradicional (MySQL)

### Usuarios Disponibles

Los siguientes usuarios **SOLO** existen en la base de datos local y **NO** en el servidor LDAP:

| Usuario   | Contraseña | Rol       | Descripción                     |
| --------- | ---------- | --------- | ------------------------------- |
| admin     | admin123   | admin     | Administrador principal         |
| webmaster | web2024    | admin     | Administrador web               |
| operador  | op123456   | user      | Usuario operador                |
| soporte   | support99  | user      | Usuario de soporte técnico      |
| invitado  | guest2024  | guest     | Usuario invitado (solo lectura) |
| testuser  | test123    | user      | Usuario de pruebas              |
| developer | dev2024    | developer | Desarrollador                   |
| auditor   | audit123   | auditor   | Auditor de seguridad            |

### Características

- ✅ Autenticación contra base de datos MySQL
- ⚠️ **VULNERABLE a SQL Injection** (intencional para laboratorio)
- 🔴 Contraseñas en texto plano (NO usar en producción)
- 📊 Indicador de estado: **MySQL Online/Offline**

### Ejemplo de Uso

```
Usuario: admin
Contraseña: admin123
Método: Tradicional
```

### Bypass SQL Injection (Laboratorio)

```sql
Usuario: ' OR 1=1 #
Contraseña: cualquier_cosa
```

---

## 🏢 Autenticación Corporativa (LDAP)

### Configuración

- **Servidor LDAP**: Configurado en `.env` (variable `LDAP_IP`)
- **Puerto**: 389
- **Base DN**: `ou=usuarios,dc=softwarelibre,dc=local`
- **Protocolo**: LDAP v3

### Usuarios Corporativos

Los usuarios corporativos **SOLO** existen en el servidor LDAP del proyecto de Agustín.

Ejemplos (según configuración del servidor LDAP):

- `agustin`
- `jperez`
- `mgarcia`
- etc.

### Características

- ✅ Autenticación segura contra servidor LDAP
- ✅ Detección automática de conectividad del servidor
- ✅ Timeout configurado (2-3 segundos)
- ✅ Manejo robusto de errores
- 📊 Indicador de estado: **LDAP Online/Offline**

### Verificación de Conectividad

El sistema verifica automáticamente:

1. **Socket check** - Verifica si el puerto 389 está abierto
2. **LDAP bind** - Intenta conexión LDAP anónima
3. **Health status** - Actualiza indicadores en UI

---

## 🎯 Indicadores de Estado en UI

### MySQL

- 🟢 **MySQL Online** - Base de datos accesible
- 🔴 **MySQL Offline** - No se puede conectar a la BD

### LDAP

- 🔵 **LDAP Online** - Servidor LDAP accesible y respondiendo
- 🔴 **LDAP Offline** - Servidor LDAP inalcanzable

---

## 📝 Configuración

### Archivo `.env`

```env
DB_IP=127.0.0.1          # IP del servidor MySQL
NGINX_IP=127.0.0.1       # IP del servidor Nginx
LDAP_IP=10.172.86.161    # IP del servidor LDAP corporativo
```

### Cambiar IP del Servidor LDAP

1. Editar archivo `.env`
2. Modificar la variable `LDAP_IP`
3. Reiniciar la aplicación web

---

## 🔧 Funciones Principales

### `verificar_servidor_ldap($host, $port, $timeout)`

Verifica conectividad mediante socket.

### `autenticar_con_ldap($usuario, $password)`

Autentica usuario contra servidor LDAP.

### `verificar_estado_ldap()`

Verifica el estado del servidor LDAP (health check).

---

## ⚠️ Advertencias de Seguridad

### Vulnerabilidades Intencionales (Laboratorio)

1. **SQL Injection** en autenticación tradicional
2. **Contraseñas en texto plano** en base de datos
3. **Sin rate limiting** en intentos de login
4. **Sin HTTPS** (comunicación en texto plano)

### NO USAR EN PRODUCCIÓN

Este sistema es **únicamente para fines educativos** y demostración de vulnerabilidades.

---

## 📚 Casos de Uso

### Escenario 1: Usuario Tradicional

```
1. Usuario selecciona "Tradicional"
2. Ingresa credenciales de BD local
3. Sistema valida contra MySQL
4. Acceso concedido si credenciales correctas
```

### Escenario 2: Usuario Corporativo

```
1. Usuario selecciona "Corporativo (LDAP)"
2. Ingresa credenciales corporativas
3. Sistema verifica conectividad LDAP
4. Si LDAP online → autentica contra servidor
5. Si LDAP offline → muestra error
```

### Escenario 3: Prueba de Penetración

```
1. Atacante selecciona "Tradicional"
2. Inyecta SQL: ' OR 1=1 #
3. Sistema vulnerable permite bypass
4. Suricata IDS detecta ataque
5. Dashboard muestra alerta
```

---

## 🔍 Troubleshooting

### LDAP muestra "Offline" pero el servidor está activo

1. Verificar firewall: `sudo iptables -L -n | grep 389`
2. Probar conectividad: `telnet <LDAP_IP> 389`
3. Verificar IP en `.env`
4. Revisar logs de PHP: `/var/log/apache2/error.log`

### MySQL muestra "Offline"

1. Verificar servicio: `sudo systemctl status mysql`
2. Probar conexión: `mysql -h <DB_IP> -u webuser -p`
3. Verificar firewall en servidor DB
4. Revisar credenciales en `config.php`

---

## 📊 Arquitectura de Autenticación

```
┌─────────────────────────────────────────┐
│         index.php (Login UI)            │
│  ┌─────────────┬──────────────────┐     │
│  │ Tradicional │  Corporativo     │     │
│  └──────┬──────┴────────┬─────────┘     │
└─────────┼───────────────┼───────────────┘
          │               │
          ▼               ▼
    ┌─────────┐     ┌──────────┐
    │  MySQL  │     │   LDAP   │
    │ (Local) │     │ (Remoto) │
    └─────────┘     └──────────┘

    Usuarios        Usuarios
    Tradicionales   Corporativos
```

---

## 📅 Historial de Versiones

### v2.0 (2026-01-06)

- ✅ Detección mejorada de conectividad LDAP
- ✅ Verificación mediante socket antes de LDAP bind
- ✅ Indicadores de estado precisos en UI
- ✅ Configuración centralizada desde `.env`
- ✅ Usuarios tradicionales mejorados (8 usuarios)
- ✅ Manejo robusto de errores LDAP

### v1.0 (Inicial)

- Autenticación dual básica
- Integración LDAP inicial
- Usuarios de prueba básicos

---

## 👥 Créditos

- **Sistema LDAP**: Proyecto de Agustín
- **Aplicación Vulnerable**: Laboratorio de Seguridad
- **Dashboard**: Sistema de Monitoreo Centralizado
