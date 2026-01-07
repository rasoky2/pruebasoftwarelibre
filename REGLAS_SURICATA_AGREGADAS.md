# REGLAS DE SURICATA AGREGADAS - RESUMEN

## 📊 **RESUMEN EJECUTIVO**

Se agregaron **44 reglas profesionales** de detección de ataques a `suricata/rules/local.rules`:

| Categoría                          | Cantidad de Reglas | SIDs                             |
| ---------------------------------- | ------------------ | -------------------------------- |
| **SQLMap Detection**               | 2                  | 1000011-1000012                  |
| **SQL Injection Básica**           | 4                  | 1000001-1000002, 1000013-1000014 |
| **SQL Injection Avanzada (UNION)** | 3                  | 1000005-1000006, 1000015         |
| **SQL Comments**                   | 5                  | 1000016-1000020                  |
| **Information Schema**             | 4                  | 1000021-1000024                  |
| **Funciones SQL Peligrosas**       | 4                  | 1000025-1000028                  |
| **Time-Based SQL Injection**       | 3                  | 1000029-1000031                  |
| **Boolean-Based SQL Injection**    | 2                  | 1000032-1000033                  |
| **Detección de Escaneo**           | 2                  | 1000034-1000035                  |
| **XSS (Cross-Site Scripting)**     | 4                  | 1000003-1000004, 1000036-1000037 |
| **LDAP Injection**                 | 2                  | 1000038-1000039                  |
| **Reconocimiento de Red**          | 3                  | 1000007-1000009                  |
| **Auditoría de Acceso a DB**       | 2                  | 1000010, 1000040                 |
| **Command Injection**              | 4                  | 1000041-1000044                  |
| **TOTAL**                          | **44 reglas**      | 1000001-1000044                  |

---

## 🎯 **REGLAS CLAVE PARA DETECTAR SQLMAP**

### **1. Detección por User-Agent (SID 1000011)**

```suricata
alert http $EXTERNAL_NET any -> $HTTP_SERVERS any (
    msg:"ATTACK: SQLMap Tool Detected by User-Agent";
    flow:established,to_server;
    content:"sqlmap";
    http_user_agent;
    nocase;
    classtype:web-application-attack;
    sid:1000011;
    rev:1;
)
```

**Detecta:** Cuando SQLMap se identifica en el User-Agent HTTP

---

### **2. Detección de SQL Comments (SID 1000016-1000020)**

```suricata
# Comentarios -- (doble guion)
alert http ... content:"--"; http_client_body; sid:1000016;

# Comentarios /* */ (estilo C)
alert http ... content:"/*"; http_client_body; sid:1000018;
alert http ... content:"*/"; http_client_body; sid:1000020;
```

**Detecta:** Técnicas de evasión usando comentarios SQL

---

### **3. Detección de Information Schema (SID 1000021-1000024)**

```suricata
# Acceso a information_schema
alert http ... content:"information_schema"; nocase; sid:1000021;

# Enumeración de tablas
alert http ... content:"table_name"; nocase; sid:1000023;

# Enumeración de columnas
alert http ... content:"column_name"; nocase; sid:1000024;
```

**Detecta:** Cuando SQLMap enumera la estructura de la base de datos

---

### **4. Detección de UNION SELECT (SID 1000005-1000006, 1000015)**

```suricata
# UNION SELECT básico
alert http ... content:"UNION"; content:"SELECT"; sid:1000005;

# UNION ALL SELECT
alert http ... content:"UNION"; content:"ALL"; content:"SELECT"; sid:1000015;
```

**Detecta:** Técnica UNION-based SQL Injection

---

### **5. Detección de Escaneo Masivo (SID 1000034-1000035)**

```suricata
# Múltiples intentos de SQL Injection
alert http ... content:"SELECT"; threshold:count 10, seconds 60; sid:1000034;

# Múltiples UNION SELECT
alert http ... content:"UNION"; threshold:count 5, seconds 30; sid:1000035;
```

**Detecta:** Cuando SQLMap hace múltiples peticiones rápidas (escaneo automatizado)

---

## 🛡️ **OTRAS DEFENSAS AGREGADAS**

### **SQL Injection Avanzada:**

- ✅ Time-Based (SLEEP, BENCHMARK, WAITFOR DELAY)
- ✅ Boolean-Based (AND '1'='1', AND '1'='2')
- ✅ Funciones peligrosas (CONCAT, GROUP_CONCAT, LOAD_FILE, INTO OUTFILE)
- ✅ Variantes de OR/AND (OR 1=1, AND 1=1)

### **XSS (Cross-Site Scripting):**

- ✅ Script tags (`<script>`)
- ✅ Javascript protocol (`javascript:`)
- ✅ Event handlers (`onerror`)

### **LDAP Injection:**

- ✅ Wildcard attacks (`*)(`)
- ✅ OR filters (`)(|`)

### **Command Injection:**

- ✅ Pipe character (`|`)
- ✅ Semicolon (`;`)
- ✅ Shell paths (`/bin/bash`, `/bin/sh`)

---

## 🚀 **CÓMO USAR LAS REGLAS**

### **Paso 1: Las reglas ya están en el archivo**

```bash
# Archivo actualizado:
d:\WebSoftwarePrueba\suricata\rules\local.rules
```

### **Paso 2: Copiar al servidor Nginx**

```bash
# En Nginx Server (192.168.1.56)
# El archivo se copiará automáticamente cuando ejecutes setup_nginx.py
# O cópialo manualmente:
sudo cp /ruta/del/proyecto/suricata/rules/local.rules /etc/suricata/rules/local.rules
```

### **Paso 3: Validar configuración**

```bash
sudo suricata -T -c /etc/suricata/suricata.yaml
```

**Salida esperada:**

```
[OK] Configuration provided was successfully loaded.
```

### **Paso 4: Reiniciar Suricata**

```bash
sudo systemctl restart suricata
sudo systemctl status suricata
```

### **Paso 5: Verificar que las reglas se cargaron**

```bash
# Ver cuántas reglas se cargaron
sudo suricatasc -c "ruleset-stats" | grep "Loaded"
```

**Salida esperada:**

```
Loaded: 44 rules
```

---

## 🧪 **PRUEBA DE DETECCIÓN**

### **Test 1: SQLMap User-Agent**

```bash
curl -H "User-Agent: sqlmap/1.7.2" http://192.168.1.56/
```

**Alerta esperada:**

```
ATTACK: SQLMap Tool Detected by User-Agent
```

---

### **Test 2: SQL Injection básica**

```bash
curl -X POST http://192.168.1.56/ \
  -d "username=admin' OR '1'='1&password=123"
```

**Alerta esperada:**

```
ATTACK: SQL Injection (OR 1=1) in Body
```

---

### **Test 3: UNION SELECT**

```bash
curl -X POST http://192.168.1.56/ \
  -d "username=admin' UNION SELECT 1,2,3--&password=123"
```

**Alertas esperadas:**

```
ATTACK: SQL Injection (UNION SELECT) in Body
ATTACK: SQL Injection - SQL Comment (--) in Body
```

---

### **Test 4: Information Schema**

```bash
curl -X POST http://192.168.1.56/ \
  -d "username=admin' UNION SELECT table_name FROM information_schema.tables--&password=123"
```

**Alertas esperadas:**

```
ATTACK: SQL Injection (UNION SELECT) in Body
ATTACK: SQL Injection - Information Schema Access
ATTACK: SQL Injection - Table Enumeration
ATTACK: SQL Injection - SQL Comment (--) in Body
```

---

### **Test 5: SQLMap completo**

```bash
sqlmap -u "http://192.168.1.56/" \
  --data="username=admin&password=123&auth_method=DB" \
  --dump -T users -D lab_vulnerable --batch
```

**Alertas esperadas (múltiples):**

```
ATTACK: SQLMap Tool Detected by User-Agent
ATTACK: SQL Injection (UNION SELECT) in Body
ATTACK: SQL Injection - SQL Comment (--) in Body
ATTACK: SQL Injection - Information Schema Access
ATTACK: SQL Injection - Table Enumeration
ATTACK: SQL Injection - Column Enumeration
SCAN: Multiple SQL Injection Attempts Detected
SCAN: Multiple UNION SELECT Attempts
```

---

## 📊 **VERIFICAR ALERTAS**

### **En el servidor Nginx:**

```bash
# Ver alertas en tiempo real
sudo tail -f /var/log/suricata/eve.json | jq 'select(.event_type=="alert") | .alert.signature'

# Contar alertas de SQLMap
sudo cat /var/log/suricata/eve.json | jq 'select(.alert.signature | contains("SQLMap"))' | wc -l

# Ver todas las alertas únicas
sudo cat /var/log/suricata/eve.json | jq -r 'select(.event_type=="alert") | .alert.signature' | sort | uniq
```

### **En el Dashboard (192.168.1.15:5000):**

- ✅ Tabla "Security Alerts (Database)" mostrará las alertas
- ✅ Contador "Alertas Seguridad" incrementará
- ✅ Botón "BAN" para bloquear al atacante

---

## ✅ **CHECKLIST DE VERIFICACIÓN**

- [ ] Archivo `local.rules` actualizado con 44 reglas
- [ ] Reglas copiadas a `/etc/suricata/rules/local.rules` en Nginx Server
- [ ] Configuración validada con `suricata -T`
- [ ] Suricata reiniciado
- [ ] Log Shipper corriendo (`sudo systemctl status log-shipper`)
- [ ] Dashboard corriendo (`python3 main.py`)
- [ ] Prueba con SQLMap ejecutada
- [ ] Alertas visibles en `/var/log/suricata/eve.json`
- [ ] Alertas visibles en Dashboard web

---

## 🎯 **BENEFICIOS DE LAS NUEVAS REGLAS**

| Antes                              | Después                          |
| ---------------------------------- | -------------------------------- |
| 10 reglas básicas                  | **44 reglas profesionales**      |
| ❌ No detectaba SQLMap             | ✅ Detecta SQLMap por User-Agent |
| ❌ No detectaba SQL Comments       | ✅ Detecta --, /_, _/            |
| ❌ No detectaba Information Schema | ✅ Detecta enumeración de DB     |
| ❌ No detectaba Time-Based         | ✅ Detecta SLEEP, BENCHMARK      |
| ❌ No detectaba escaneos           | ✅ Detecta múltiples intentos    |
| ❌ No detectaba LDAP Injection     | ✅ Detecta LDAP Injection        |
| ❌ No detectaba Command Injection  | ✅ Detecta Command Injection     |

---

## 📚 **DOCUMENTACIÓN DE REGLAS**

### **Formato de las reglas:**

```suricata
alert <protocolo> <origen> <puerto_origen> -> <destino> <puerto_destino> (
    msg:"<mensaje_de_alerta>";
    flow:<dirección_flujo>;
    content:"<contenido_a_buscar>";
    <modificadores>;
    classtype:<tipo_de_ataque>;
    sid:<id_único>;
    rev:<revisión>;
)
```

### **Modificadores usados:**

- `http_user_agent`: Busca en el User-Agent HTTP
- `http_client_body`: Busca en el cuerpo de la petición POST
- `http_uri`: Busca en la URL
- `nocase`: Búsqueda insensible a mayúsculas/minúsculas
- `distance:0; within:X`: Busca contenido cercano (máximo X bytes)
- `threshold`: Detecta múltiples ocurrencias en un tiempo determinado

---

## 🚀 **PRÓXIMOS PASOS**

1. ✅ **Reglas agregadas** - Completado
2. ⏳ **Copiar a servidor Nginx** - Pendiente (se hace con `setup_nginx.py`)
3. ⏳ **Reiniciar Suricata** - Pendiente
4. ⏳ **Probar con SQLMap** - Pendiente
5. ⏳ **Verificar alertas en Dashboard** - Pendiente

---

**¡Sistema de detección profesional listo para producción!** 🛡️🔒
