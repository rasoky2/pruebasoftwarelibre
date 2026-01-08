import os
import sys
import subprocess
import socket
import re

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def test_socket(ip, port, timeout=2):
    """Prueba conectividad a nivel de red (TCP)"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, port))
        s.close()
        return True
    except Exception:
        return False

def check_package_installed(package_name):
    try:
        result = subprocess.run(["dpkg", "-l", package_name], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def install_mysql():
    if check_package_installed("mysql-server"):
        print("[OK] MySQL Server ya está instalado.")
        return
    print("\n[*] Instalando MySQL Server...")
    try:
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "-y", "install", "mysql-server"], check=True)
        print("[OK] MySQL Server instalado.")
    except Exception as e:
        print(f"[!] Error al instalar MySQL: {e}")

def configure_mysql_network():
    """Configura MySQL para escuchar en todas las interfaces de red"""
    print("\n[*] Configurando MySQL para aceptar conexiones de red...")
    
    config_file = "/etc/mysql/mysql.conf.d/mysqld.cnf"
    
    if not os.path.exists(config_file):
        print(f"[!] No se encontró {config_file}")
        return False
    
    try:
        # Leer el archivo
        with open(config_file, "r") as f:
            content = f.read()
        
        # Reemplazar bind-address
        # Busca tanto "bind-address" como "mysqlx-bind-address"
        content = re.sub(
            r'bind-address\s*=\s*127\.0\.0\.1',
            'bind-address = 0.0.0.0',
            content
        )
        content = re.sub(
            r'mysqlx-bind-address\s*=\s*127\.0\.0\.1',
            'mysqlx-bind-address = 0.0.0.0',
            content
        )
        
        # Escribir el archivo modificado
        with open(config_file, "w") as f:
            f.write(content)
        
        print("[OK] MySQL configurado para escuchar en 0.0.0.0")
        return True
    except Exception as e:
        print(f"[!] Error configurando MySQL: {e}")
        return False

def restart_mysql():
    print("\n[*] Reiniciando servicio MySQL...")
    try:
        subprocess.run(["sudo", "systemctl", "restart", "mysql"], check=True)
        print("[OK] MySQL reiniciado correctamente.")
        return True
    except Exception as e:
        print(f"[!] Error al reiniciar MySQL: {e}")
        return False

def check_db_health(user, password, host, database):
    """Verifica si la base de datos está activa"""
    try:
        cmd = f"mysql -u{user} -p{password} -h{host} -e 'SELECT 1;' {database}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def load_database_schema(db_name):
    """Carga el esquema de la base de datos desde database_setup.sql"""
    print("\n[*] Cargando esquema de la base de datos...")
    
    # Buscar el archivo database_setup.sql
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file = os.path.join(os.path.dirname(script_dir), "database_setup.sql")
    
    if os.path.exists(sql_file):
        try:
            subprocess.run(
                ["sudo", "mysql", db_name],
                stdin=open(sql_file, 'r'),
                check=True
            )
            print(f"[OK] Esquema cargado desde {sql_file}")
            return True
        except Exception as e:
            print(f"[!] Error cargando esquema: {e}")
            return False
    else:
        print(f"[!] No se encontró {sql_file}")
        print("[*] Creando tablas manualmente...")
        
        # Crear tablas manualmente si no existe el archivo
        sql_commands = """
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            price DECIMAL(10,2)
        );

        CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL,
            password VARCHAR(255) NOT NULL
        );

        INSERT INTO products (name, description, price) VALUES 
        ('Laptop Dell XPS 13', 'Ultrabook potente con pantalla táctil', 1299.99),
        ('Teclado Mecánico RGB', 'Switches Cherry MX Blue con iluminación personalizable', 89.99),
        ('Monitor LG 27 4K', 'Panel IPS con resolución 3840x2160', 449.99),
        ('Mouse Logitech MX Master 3', 'Mouse ergonómico inalámbrico de alta precisión', 99.99),
        ('Webcam Logitech C920', 'Cámara Full HD 1080p con micrófono estéreo', 79.99);

        INSERT INTO usuarios (username, password) VALUES 
        ('admin', 'admin123'),
        ('user', 'user123');
        """
        
        try:
            subprocess.run(
                ["sudo", "mysql", "-e", f"USE {db_name}; {sql_commands}"],
                check=True
            )
            print("[OK] Tablas creadas manualmente.")
            return True
        except Exception as e:
            print(f"[!] Error creando tablas: {e}")
            return False

def setup_db_config():
    print("\n" + "="*50)
    print("   DB SETUP COMPLETO (MySQL + Esquema)")
    print("="*50)
    
    # 1. MySQL
    if input("¿Instalar MySQL Server? (s/N): ").lower() == 's':
        install_mysql()

    db_host = input("IP Servidor MySQL [127.0.0.1]: ") or "127.0.0.1"
    db_name = input("Nombre de la DB [lab_vulnerable]: ") or "lab_vulnerable"
    db_user = input("Usuario [webuser]: ") or "webuser"
    db_pass = input("Password [web123]: ") or "web123"

    local_ip = get_local_ip()
    if db_host in ["127.0.0.1", "localhost", local_ip]:
        # 2. Configurar MySQL para red (Escuchar en todas las interfaces)
        configure_mysql_network()
        
        # 3. Crear base de datos y usuarios con PRIVILEGIOS LIBRES (%)
        print(f"[*] Configurando privilegios libres para {db_user}...")
        sql_cmd = f"CREATE DATABASE IF NOT EXISTS {db_name}; " \
                  f"CREATE USER IF NOT EXISTS '{db_user}'@'%' IDENTIFIED BY '{db_pass}'; " \
                  f"CREATE USER IF NOT EXISTS '{db_user}'@'localhost' IDENTIFIED BY '{db_pass}'; " \
                  f"GRANT ALL PRIVILEGES ON {db_name}.* TO '{db_user}'@'%'; " \
                  f"GRANT ALL PRIVILEGES ON {db_name}.* TO '{db_user}'@'localhost'; " \
                  f"ALTER USER '{db_user}'@'%' IDENTIFIED WITH mysql_native_password BY '{db_pass}'; " \
                  f"FLUSH PRIVILEGES;"
        try:
            subprocess.run(["sudo", "mysql", "-e", sql_cmd], check=True)
            print("[OK] Base de datos y usuarios con privilegios '%' configurados.")
        except Exception as e:
            print(f"[!] Error configurando privilegios MySQL: {e}")

        # 4. Cargar esquema de la base de datos
        if input("\n¿Desea cargar el esquema de la base de datos (tablas y datos)? (s/N): ").lower() == 's':
            load_database_schema(db_name)

        # 5. Reiniciar MySQL para aplicar bind-address = 0.0.0.0
        restart_mysql()

    # 6. Actualizar .env (ÚNICA FUENTE DE VERDAD)
    from setup_inventory import load_env, update_env
    env_data = load_env()
    
    current_admin = env_data.get("ADMIN_IP", "127.0.0.1")
    print(f"\n[*] Configuración de Red del Dashboard:")
    admin_ip = input(f"   IP del Servidor Admin/Dashboard [{current_admin}]: ") or current_admin

    update_env({
        "ADMIN_IP": admin_ip,
        "DB_IP": db_host,
        "DB_NAME": db_name,
        "DB_USER": db_user,
        "DB_PASS": db_pass,
        "SENSOR_TYPE": "database"
    })
    print("[OK] Configuración de Base de Datos y SENSOR_TYPE actualizados en .env")
    
    # 7. Configuración de Seguridad (Suricata en DB)
    print("\n" + "="*50)
    print("   MONITOREO DE SEGURIDAD (Suricata IDS)")
    print("="*50)
    if input("¿Desea instalar y configurar Suricata IDS en el servidor de DB? (s/N): ").lower() == 's':
        if not check_package_installed("suricata"):
            print("[*] Instalando Suricata en Servidor Database...")
            subprocess.run(["sudo", "apt", "update"], check=False)
            subprocess.run(["sudo", "apt", "install", "-y", "suricata"], check=False)
        else:
            print("[OK] Suricata ya está instalado.")
        
        # Asegurar psutil
        if not check_package_installed("python3-psutil"):
            subprocess.run(["sudo", "apt", "install", "-y", "python3-psutil"], check=False)
        
        # Configurar Suricata (usamos una versión simplificada de la lógica de nginx)
        local_ip = get_local_ip()
        suricata_yaml = "/etc/suricata/suricata.yaml"
        # Intentar copiar nuestras reglas personalizadas
        rules_src = os.path.join(os.path.dirname(os.path.dirname(__file__)), "suricata", "rules", "local.rules")
        rules_dst = "/etc/suricata/rules/local.rules"
        
        if os.path.exists(rules_src):
            subprocess.run(["sudo", "mkdir", "-p", "/etc/suricata/rules"], check=False)
            subprocess.run(["sudo", "cp", rules_src, rules_dst], check=True)
            print("[OK] Reglas de seguridad copiadas.")

        # Parchear suricata.yaml para incluir las reglas y el HOME_NET
        if os.path.exists(suricata_yaml):
            try:
                with open(suricata_yaml, "r") as f: content = f.read()
                
                # Configurar HOME_NET
                content = re.sub(r'HOME_NET: "\[.*?\]"', f'HOME_NET: "[{local_ip}/32]"', content)
                
                # Asegurar que incluya local.rules
                if "rule-files:" in content:
                    if "local.rules" not in content:
                        content = content.replace("rule-files:", f"rule-files:\n  - {rules_dst}")
                
                # Guardar cambios (usando sudo para escribir en /etc)
                with open("/tmp/suricata.yaml", "w") as f: f.write(content)
                subprocess.run(["sudo", "cp", "/tmp/suricata.yaml", suricata_yaml], check=True)
                
                subprocess.run(["sudo", "systemctl", "restart", "suricata"], check=True)
                print(f"[OK] Suricata configurado y reiniciado (HOME_NET: {local_ip})")
            except Exception as e:
                print(f"[!] Error configurando suricata.yaml: {e}")
        else:
            print("[!] No se encontró /etc/suricata/suricata.yaml. ¿Está instalado?")

        # Configurar el Log Shipper para la DB
        print("[*] Instalando Log Shipper para Database...")
        shipper_src = os.path.join(os.path.dirname(os.path.dirname(__file__)), "suricata", "log_shipper.py")
        service_src = os.path.join(os.path.dirname(os.path.dirname(__file__)), "suricata", "log-shipper.service")
        service_dst = "/etc/systemd/system/log-shipper.service"

        if os.path.exists(service_src):
            try:
                # Detectar ruta actual del proyecto de forma dinámica
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                scripts_dir = os.path.join(project_root, "scripts")
                suricata_dir = os.path.join(project_root, "suricata")
                
                # Leer y parchear Log Shipper
                with open(service_src, 'r') as f: content = f.read()
                content = content.replace("/var/www/html/pruebasoftwarelibre/suricata", suricata_dir)
                temp_shipper = "/tmp/log-shipper.service"
                with open(temp_shipper, 'w') as f: f.write(content)
                
                subprocess.run(["sudo", "cp", temp_shipper, service_dst], check=True)
                subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
                subprocess.run(["sudo", "systemctl", "enable", "log-shipper"], check=True)
                subprocess.run(["sudo", "systemctl", "restart", "log-shipper"], check=True)
                print("[OK] Log Shipper de Seguridad activo en DB con ruta detectada.")
            except Exception as e:
                print(f"[!] Error instalando log-shipper: {e}")

    # 7. Instalación del Servicio Heartbeat (Python)
    if input("\n¿Desea instalar/actualizar el servicio de latido (Heartbeat) para el Dashboard? (s/N): ").lower() == 's':
        print("[*] Configurando servicio db-heartbeat...")
        
        # ... (instalación de psutil ya optimizada arriba) ...
        
        service_src = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mysql", "db-heartbeat.service")
        service_dst = "/etc/systemd/system/db-heartbeat.service"
        
        if os.path.exists(service_src):
            try:
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                scripts_dir = os.path.join(project_root, "scripts")
                
                with open(service_src, 'r') as f: content = f.read()
                content = content.replace("/var/www/html/pruebasoftwarelibre/scripts", scripts_dir)
                temp_db = "/tmp/db-heartbeat.service"
                with open(temp_db, 'w') as f: f.write(content)

                subprocess.run(["sudo", "cp", temp_db, service_dst], check=True)
                subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
                subprocess.run(["sudo", "systemctl", "enable", "db-heartbeat"], check=True)
                subprocess.run(["sudo", "systemctl", "restart", "db-heartbeat"], check=True)
                print("[OK] Servicio db-heartbeat configurado con ruta detectada.")
            except Exception as e:
                print(f"[!] Error instalando servicio db-heartbeat: {e}")
        else:
            print(f"[!] No se encontró {service_src}. Saltando instalación de servicio.")

    # 8. Verificación de conectividad con el Dashboard (Admin)
    print(f"\n[*] Verificando conectividad con el Dashboard en {admin_ip}:5000...")
    dash_test = test_socket(admin_ip, 5000)
    if dash_test:
        print(f"[OK] Conexión con Dashboard EXITOSA (Admin está recibiendo logs).")
    else:
        print(f"[!] ADVERTENCIA: No se pudo conectar con el Dashboard en {admin_ip}:5000.")
        print(f"    Verifica que el script main.py esté corriendo en el Servidor Admin.")

    # 9. DIAGNÓSTICO DE SURICATA Y LOG SHIPPER
    print("\n" + "="*50)
    print("   DIAGNÓSTICO DE MONITOREO DE SEGURIDAD")
    print("="*50)
    
    # Verificar si Suricata está instalado
    suricata_installed = check_package_installed("suricata")
    print(f"\n[*] Suricata instalado: {'SÍ' if suricata_installed else 'NO'}")
    
    if suricata_installed:
        # Verificar si Suricata está corriendo
        try:
            result = subprocess.run(["systemctl", "is-active", "suricata"], capture_output=True, text=True)
            suricata_running = result.stdout.strip() == "active"
            print(f"[*] Suricata corriendo: {'SÍ' if suricata_running else 'NO'}")
            
            if not suricata_running:
                print("[!] ADVERTENCIA: Suricata NO está corriendo")
                print("    Ejecuta: sudo systemctl start suricata")
        except:
            print("[!] No se pudo verificar el estado de Suricata")
        
        # Verificar reglas cargadas
        if os.path.exists("/etc/suricata/rules/local.rules"):
            try:
                with open("/etc/suricata/rules/local.rules", "r") as f:
                    rules_content = f.read()
                    rule_count = rules_content.count("alert ")
                    
                print(f"[OK] Reglas personalizadas: {rule_count} reglas cargadas")
                
                # Verificar reglas específicas importantes
                has_mysql = "3306" in rules_content
                has_ssh = "22" in rules_content and "SSH" in rules_content
                has_ping = "icmp" in rules_content
                
                print(f"    - Detección MySQL (3306): {'✓' if has_mysql else '✗'}")
                print(f"    - Detección SSH (22): {'✓' if has_ssh else '✗'}")
                print(f"    - Detección PING (ICMP): {'✓' if has_ping else '✗'}")
            except:
                print("[!] No se pudo leer /etc/suricata/rules/local.rules")
        else:
            print("[!] ADVERTENCIA: No se encontró /etc/suricata/rules/local.rules")
            print("    Las reglas personalizadas NO están instaladas")
        
        # Verificar archivo de logs de Suricata
        if os.path.exists("/var/log/suricata/eve.json"):
            try:
                file_size = os.path.getsize("/var/log/suricata/eve.json")
                print(f"[OK] Archivo de logs: /var/log/suricata/eve.json ({file_size} bytes)")
                
                # Leer últimas líneas para ver si hay actividad
                result = subprocess.run(["tail", "-n", "5", "/var/log/suricata/eve.json"], 
                                      capture_output=True, text=True)
                if result.stdout.strip():
                    print("[OK] Suricata está generando logs")
                else:
                    print("[!] El archivo de logs está vacío (sin actividad aún)")
            except:
                print("[!] No se pudo verificar /var/log/suricata/eve.json")
        else:
            print("[!] ADVERTENCIA: /var/log/suricata/eve.json no existe")
    else:
        print("[!] ADVERTENCIA: Suricata NO está instalado")
        print("    Ejecuta nuevamente el script y acepta instalar Suricata")
    
    # Verificar Log Shipper
    print(f"\n[*] Verificando Log Shipper...")
    try:
        result = subprocess.run(["systemctl", "is-active", "log-shipper"], capture_output=True, text=True)
        shipper_running = result.stdout.strip() == "active"
        print(f"[*] Log Shipper corriendo: {'SÍ' if shipper_running else 'NO'}")
        
        if shipper_running:
            print("[OK] Log Shipper está enviando alertas al Dashboard")
            
            # Mostrar últimas líneas del log del shipper
            try:
                result = subprocess.run(["journalctl", "-u", "log-shipper", "-n", "3", "--no-pager"], 
                                      capture_output=True, text=True)
                if result.stdout.strip():
                    print("\n[*] Últimas líneas del Log Shipper:")
                    for line in result.stdout.strip().split("\n")[-3:]:
                        if line.strip():
                            print(f"    {line}")
            except:
                pass
        else:
            print("[!] ADVERTENCIA: Log Shipper NO está corriendo")
            print("    Ejecuta: sudo systemctl start log-shipper")
    except:
        print("[!] Log Shipper NO está instalado")
        print("    Ejecuta nuevamente el script y acepta instalar el Log Shipper")
    
    # Verificar conectividad con Dashboard
    print(f"\n[*] Verificando conectividad con Dashboard ({admin_ip}:5000)...")
    if dash_test:
        print(f"[OK] Dashboard ACCESIBLE - Las alertas llegarán correctamente")
    else:
        print(f"[!] ADVERTENCIA: Dashboard NO ACCESIBLE")
        print(f"    Verifica que main.py esté corriendo en {admin_ip}")
        print(f"    Verifica el firewall y las reglas de red")
    
    # Resumen de qué se detectará
    print("\n" + "="*50)
    print("   ¿QUÉ SE DETECTARÁ Y MOSTRARÁ EN EL DASHBOARD?")
    print("="*50)
    
    if suricata_installed and shipper_running:
        print("\n✓ Accesos a MySQL (puerto 3306)")
        print("  - Conexiones desde Nginx (AUTHORIZED)")
        print("  - Conexiones desde otras IPs (UNAUTHORIZED ACCESS)")
        print("\n✓ Intentos de SSH (puerto 22)")
        print("  - Cualquier intento de conexión SSH")
        print("\n✓ Pings (ICMP)")
        print("  - Detección de reconocimiento de red")
        print("\n✓ Escaneo de puertos")
        print("  - Detección de Nmap y otros scanners")
        print("\n✓ Métricas del sistema")
        print("  - CPU y RAM en tiempo real")
    else:
        print("\n[!] CONFIGURACIÓN INCOMPLETA")
        if not suricata_installed:
            print("  ✗ Suricata NO instalado - No se detectarán ataques")
        if not shipper_running:
            print("  ✗ Log Shipper NO corriendo - No se enviarán alertas")
    
    # Instrucciones de prueba
    print("\n" + "="*50)
    print("   CÓMO PROBAR QUE FUNCIONA")
    print("="*50)
    print("\n1. Desde otra máquina, intenta conectarte a MySQL:")
    print(f"   mysql -h {db_host} -u {db_user} -p")
    print("\n2. Desde otra máquina, haz ping:")
    print(f"   ping {db_host}")
    print("\n3. Intenta SSH:")
    print(f"   ssh usuario@{db_host}")
    print("\n4. Abre el Dashboard:")
    print(f"   http://{admin_ip}:5000")
    print("\n5. Verás las alertas en 'Security Alerts (Database)'")
    print("   - Accesos autorizados en AZUL")
    print("   - Accesos no autorizados en ROJO")
    
    # Comandos útiles para diagnóstico
    print("\n" + "="*50)
    print("   COMANDOS ÚTILES PARA DIAGNÓSTICO")
    print("="*50)
    print("\n# Ver logs de Suricata en tiempo real:")
    print("sudo tail -f /var/log/suricata/eve.json | jq 'select(.event_type==\"alert\")'")
    print("\n# Ver estado de servicios:")
    print("sudo systemctl status suricata")
    print("sudo systemctl status log-shipper")
    print("\n# Ver logs del Log Shipper:")
    print("sudo journalctl -u log-shipper -f")
    print("\n# Reiniciar servicios si es necesario:")
    print("sudo systemctl restart suricata")
    print("sudo systemctl restart log-shipper")

    # 10. Verificación Final de la Base de Datos
    print("\n" + "="*50)
    print("   VERIFICACIÓN FINAL DE MYSQL")
    print("="*50)
    is_healthy = check_db_health(db_user, db_pass, db_host, db_name)
    
    print("\n" + "="*50)
    if is_healthy:
        print("   ¡CONFIGURACIÓN COMPLETADA Y VERIFICADA!")
        print("   Estado de MySQL: ONLINE")
        print(f"   Base de Datos: {db_name}")
        print(f"   Usuario: {db_user}")
        print(f"   Escuchando en: 0.0.0.0:3306")
        print(f"   Conectividad Admin: {'OK' if dash_test else 'FALLIDA'}")
        print(f"   Suricata: {'ACTIVO' if suricata_installed else 'NO INSTALADO'}")
        print(f"   Log Shipper: {'ACTIVO' if shipper_running else 'NO ACTIVO'}")
    else:
        print("   ¡CONFIGURACIÓN COMPLETADA CON ADVERTENCIAS!")
        print("   Estado de MySQL: OFFLINE (Verifica credenciales o red)")
    print("="*50 + "\n")

if __name__ == "__main__":
    setup_db_config()
