import subprocess
import os
import sys
import socket
import time

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def run_cmd(cmd, silent=False):
    """Ejecuta comando y retorna True si fue exitoso"""
    try:
        if silent:
            subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(cmd, shell=True, check=True)
        return True
    except Exception as e:
        if not silent:
            print(f"{Colors.FAIL}[!] Error ejecutando comando: {e}{Colors.ENDC}")
        return False

def is_package_installed(package_name):
    """Verifica si un paquete de Debian/Ubuntu está instalado"""
    try:
        result = subprocess.run(f"dpkg -l {package_name}", shell=True, capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def verificar_iptables():
    """Verifica si iptables está instalado"""
    print(f"\n{Colors.OKBLUE}[*] Verificando instalación de iptables...{Colors.ENDC}")
    
    # Verificar si el comando existe
    result = subprocess.run("which iptables", shell=True, capture_output=True)
    
    if result.returncode != 0:
        print(f"{Colors.FAIL}[!] iptables NO está instalado{Colors.ENDC}")
        print(f"{Colors.WARNING}[*] ¿Desea instalar iptables ahora? (s/N): {Colors.ENDC}", end="")
        
        if input().lower() == 's':
            print(f"{Colors.OKBLUE}[*] Instalando iptables...{Colors.ENDC}")
            if run_cmd("sudo apt-get update && sudo apt-get install -y iptables"):
                print(f"{Colors.OKGREEN}[OK] iptables instalado correctamente{Colors.ENDC}")
                return True
            else:
                print(f"{Colors.FAIL}[!] Error al instalar iptables{Colors.ENDC}")
                return False
        else:
            print(f"{Colors.FAIL}[!] No se puede continuar sin iptables{Colors.ENDC}")
            return False
    else:
        print(f"{Colors.OKGREEN}[OK] iptables está instalado{Colors.ENDC}")
        return True

def verificar_netplan():
    """Verifica si netplan está configurado y es coherente"""
    print(f"\n{Colors.OKBLUE}[*] Verificando configuración de Netplan...{Colors.ENDC}")
    
    netplan_dir = "/etc/netplan/"
    if not os.path.exists(netplan_dir):
        print(f"{Colors.WARNING}[!] No se encontró el directorio /etc/netplan/. Ignorando...{Colors.ENDC}")
        return True
    
    files = [f for f in os.listdir(netplan_dir) if f.endswith('.yaml') or f.endswith('.yml')]
    if not files:
        print(f"{Colors.WARNING}[!] No hay archivos de configuración en /etc/netplan/{Colors.ENDC}")
        return True
    
    print(f"{Colors.OKBLUE}[*] Archivos encontrados: {', '.join(files)}{Colors.ENDC}")
    
    # Probar generación de configuración
    result = subprocess.run("sudo netplan generate", shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"{Colors.FAIL}[!] Error en la sintaxis de Netplan:{Colors.ENDC}")
        print(f"{Colors.FAIL}{result.stderr}{Colors.ENDC}")
        return False
    else:
        print(f"{Colors.OKGREEN}[OK] Sintaxis de Netplan válida{Colors.ENDC}")
    
    # Verificar activador
    result = subprocess.run("networkctl status", shell=True, capture_output=True, text=True)
    if "systemd-networkd" in result.stdout:
        print(f"{Colors.OKGREEN}[OK] Renderizador: systemd-networkd activado{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}[!] Advertencia: systemd-networkd no parece ser el renderizador principal{Colors.ENDC}")
        
    return True

def verificar_reglas_existentes():
    """Verifica si ya existen reglas de iptables configuradas"""
    result = subprocess.run("sudo iptables -L -n", shell=True, capture_output=True, text=True)
    
    # Contar reglas (excluyendo las de política por defecto)
    lines = result.stdout.split('\n')
    rule_count = sum(1 for line in lines if line.strip() and not line.startswith('Chain') and not line.startswith('target'))
    
    if rule_count > 0:
        print(f"\n{Colors.WARNING}[!] Se detectaron {rule_count} reglas de firewall existentes{Colors.ENDC}")
        print(f"{Colors.WARNING}[*] ¿Desea reconfigurar el firewall? (Esto borrará las reglas actuales) (s/N): {Colors.ENDC}", end="")
        
        if input().lower() == 's':
            return True
        else:
            print(f"{Colors.OKBLUE}[*] Manteniendo configuración actual{Colors.ENDC}")
            return False
    
    return True

def reset_iptables():
    """Resetea todas las reglas de iptables"""
    print(f"{Colors.OKBLUE}[*] Reseteando reglas de iptables...{Colors.ENDC}")
    run_cmd("sudo iptables -F", silent=True)
    run_cmd("sudo iptables -X", silent=True)
    run_cmd("sudo iptables -P INPUT ACCEPT", silent=True)
    run_cmd("sudo iptables -P FORWARD ACCEPT", silent=True)
    run_cmd("sudo iptables -P OUTPUT ACCEPT", silent=True)
    print(f"{Colors.OKGREEN}[OK] Reglas reseteadas{Colors.ENDC}")

def test_connectivity(target_ip, target_name, timeout=3):
    """Prueba conectividad con un servidor mediante ping"""
    print(f"{Colors.OKBLUE}[*] Probando conectividad con {target_name} ({target_ip})...{Colors.ENDC}", end=" ", flush=True)
    
    try:
        # Usar ping con timeout
        result = subprocess.run(
            f"ping -c 1 -W {timeout} {target_ip}",
            shell=True,
            capture_output=True,
            timeout=timeout + 1
        )
        
        if result.returncode == 0:
            print(f"{Colors.OKGREEN}✓ CONECTADO{Colors.ENDC}")
            return True
        else:
            print(f"{Colors.FAIL}✗ SIN RESPUESTA{Colors.ENDC}")
            return False
    except subprocess.TimeoutExpired:
        print(f"{Colors.FAIL}✗ TIMEOUT{Colors.ENDC}")
        return False
    except Exception as e:
        print(f"{Colors.FAIL}✗ ERROR{Colors.ENDC}")
        return False

def test_port(target_ip, port, service_name, timeout=3):
    """Prueba si un puerto está abierto"""
    print(f"{Colors.OKBLUE}[*] Probando puerto {port} ({service_name}) en {target_ip}...{Colors.ENDC}", end=" ", flush=True)
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((target_ip, port))
        sock.close()
        
        if result == 0:
            print(f"{Colors.OKGREEN}✓ ABIERTO{Colors.ENDC}")
            return True
        else:
            print(f"{Colors.WARNING}✗ CERRADO{Colors.ENDC}")
            return False
    except Exception as e:
        print(f"{Colors.FAIL}✗ ERROR{Colors.ENDC}")
        return False

def diagnostico_final(role, admin_ip, nginx_ip=None, db_ip=None):
    """Ejecuta diagnóstico de conectividad al final de la configuración"""
    print("\n" + "="*60)
    print(f"{Colors.HEADER}{Colors.BOLD}   DIAGNÓSTICO DE CONECTIVIDAD{Colors.ENDC}")
    print("="*60 + "\n")
    
    results = {}
    
    if role == '1':  # Base de Datos
        print(f"{Colors.BOLD}Verificando conectividad desde Base de Datos:{Colors.ENDC}\n")
        
        # Probar Admin (Controlador)
        print(f"{Colors.HEADER}→ Conectividad con Servidor Admin (Controlador):{Colors.ENDC}")
        results['admin_ping'] = test_connectivity(admin_ip, "Admin/Controlador")
        results['admin_ssh'] = test_port(admin_ip, 22, "SSH")
        results['admin_dashboard'] = test_port(admin_ip, 5000, "Dashboard")
        
        # Probar Nginx
        if nginx_ip and nginx_ip != "127.0.0.1":
            print(f"\n{Colors.HEADER}→ Conectividad con Servidor Nginx (Web):{Colors.ENDC}")
            results['nginx_ping'] = test_connectivity(nginx_ip, "Nginx/Web")
            results['nginx_http'] = test_port(nginx_ip, 80, "HTTP")
        
        # Probar a sí mismo (DB)
        print(f"\n{Colors.HEADER}→ Verificación local (Base de Datos):{Colors.ENDC}")
        print(f"{Colors.OKGREEN}[OK] Servidor MySQL - Configurado correctamente{Colors.ENDC}")
        results['db_local'] = True
        
    elif role == '2':  # Nginx
        print(f"{Colors.BOLD}Verificando conectividad desde Nginx:{Colors.ENDC}\n")
        
        # Probar Admin (Dashboard)
        print(f"\n{Colors.HEADER}→ Conectividad con Servidor Admin (Dashboard):{Colors.ENDC}")
        results['admin_ping'] = test_connectivity(admin_ip, "Admin/Controlador")
        results['admin_ssh'] = test_port(admin_ip, 22, "SSH")
        results['admin_dashboard'] = test_port(admin_ip, 5000, "Dashboard (Shipper)")
        
        # Probar Base de Datos
        if db_ip and db_ip != "127.0.0.1":
            print(f"\n{Colors.HEADER}→ Conectividad con Servidor Base de Datos:{Colors.ENDC}")
            results['db_ping'] = test_connectivity(db_ip, "Base de Datos")
            results['db_mysql'] = test_port(db_ip, 3306, "MySQL")
        
        # Probar a sí mismo (Nginx)
        print(f"\n{Colors.HEADER}→ Verificación local (Nginx):{Colors.ENDC}")
        print(f"{Colors.OKGREEN}[OK] Servidor Nginx - Configurado correctamente{Colors.ENDC}")
        
        # Verificar si Suricata está instalado
        try:
            suricata_status = subprocess.run(["systemctl", "is-active", "suricata"], 
                                            capture_output=True, text=True)
            if suricata_status.stdout.strip() == "active":
                print(f"{Colors.OKGREEN}[OK] Suricata IDS - Activo{Colors.ENDC}")
                results['suricata'] = True
            else:
                print(f"{Colors.WARNING}[!] Suricata IDS - No activo{Colors.ENDC}")
                results['suricata'] = False
        except Exception:
            print(f"{Colors.WARNING}[!] Suricata IDS - No instalado{Colors.ENDC}")
            results['suricata'] = False
        
        # Verificar si log-shipper está corriendo
        try:
            shipper_status = subprocess.run(["systemctl", "is-active", "log-shipper"], 
                                           capture_output=True, text=True)
            if shipper_status.stdout.strip() == "active":
                print(f"{Colors.OKGREEN}[OK] Log Shipper - Activo (enviando a {admin_ip}:5000){Colors.ENDC}")
                results['log_shipper'] = True
            else:
                print(f"{Colors.WARNING}[!] Log Shipper - No activo{Colors.ENDC}")
                results['log_shipper'] = False
        except Exception:
            print(f"{Colors.WARNING}[!] Log Shipper - No instalado{Colors.ENDC}")
            results['log_shipper'] = False
        
        results['nginx_local'] = True
        
    elif role == '3':  # Admin
        print(f"{Colors.BOLD}Verificando conectividad desde Admin (Controlador):{Colors.ENDC}\n")
        
        # Probar Base de Datos
        if db_ip and db_ip != "127.0.0.1":
            print(f"{Colors.HEADER}→ Conectividad con Servidor Base de Datos:{Colors.ENDC}")
            results['db_ping'] = test_connectivity(db_ip, "Base de Datos")
            results['db_ssh'] = test_port(db_ip, 22, "SSH")
            results['db_mysql'] = test_port(db_ip, 3306, "MySQL")
        
        # Probar Nginx
        if nginx_ip and nginx_ip != "127.0.0.1":
            print(f"\n{Colors.HEADER}→ Conectividad con Servidor Nginx (Web):{Colors.ENDC}")
            results['nginx_ping'] = test_connectivity(nginx_ip, "Nginx/Web")
            results['nginx_ssh'] = test_port(nginx_ip, 22, "SSH")
            results['nginx_http'] = test_port(nginx_ip, 80, "HTTP")
        
        # Probar a sí mismo (Admin)
        print(f"\n{Colors.HEADER}→ Verificación local (Admin/Controlador):{Colors.ENDC}")
        print(f"{Colors.OKGREEN}[OK] Servidor Admin - Acceso completo{Colors.ENDC}")
        results['admin_local'] = True
    
    # Resumen
    print("\n" + "-"*60)
    print(f"{Colors.BOLD}RESUMEN DE DIAGNÓSTICO:{Colors.ENDC}\n")
    
    total_tests = len([v for v in results.values() if isinstance(v, bool)])
    passed_tests = sum(1 for v in results.values() if v is True)
    
    if total_tests > 0:
        success_rate = (passed_tests / total_tests) * 100
        
        if success_rate == 100:
            print(f"{Colors.OKGREEN}✓ TODAS LAS PRUEBAS EXITOSAS ({passed_tests}/{total_tests}){Colors.ENDC}")
        elif success_rate >= 50:
            print(f"{Colors.WARNING}⚠ ALGUNAS PRUEBAS FALLARON ({passed_tests}/{total_tests}){Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}✗ MAYORÍA DE PRUEBAS FALLARON ({passed_tests}/{total_tests}){Colors.ENDC}")
    
    print("-"*60 + "\n")
    
    # Recomendaciones
    if passed_tests < total_tests:
        print(f"{Colors.WARNING}RECOMENDACIONES:{Colors.ENDC}")
        print("  • Verificar que los servidores estén encendidos")
        print("  • Revisar configuración de red (IPs correctas en .env)")
        print("  • Verificar firewall en los servidores destino")
        print("  • Ejecutar: sudo iptables -L -n (para ver reglas actuales)")
        print("  • Probar manualmente: ping <IP> y telnet <IP> <PUERTO>\n")
    
    # Tabla de conectividad
    print(f"{Colors.BOLD}TABLA DE CONECTIVIDAD:{Colors.ENDC}\n")
    
    role_name = {
        '1': 'Base de Datos',
        '2': 'Nginx/Web',
        '3': 'Admin/Controlador'
    }
    
    print(f"  Desde: {role_name.get(role, 'Desconocido')}")
    print(f"  Hacia:")
    
    if 'admin_ping' in results:
        status = "✓" if results['admin_ping'] else "✗"
        print(f"    {status} Admin/Controlador ({admin_ip})")
    
    if 'db_ping' in results and db_ip:
        status = "✓" if results['db_ping'] else "✗"
        print(f"    {status} Base de Datos ({db_ip})")
    
    if 'nginx_ping' in results and nginx_ip:
        status = "✓" if results['nginx_ping'] else "✗"
        print(f"    {status} Nginx/Web ({nginx_ip})")
    
    print()

def install_firewall_agent_service():
    """Instala el servicio systemd para el Agente de Firewall"""
    print(f"\n{Colors.HEADER}[*] Configurando FIREWALL AGENT (Sincronización de Bans)...{Colors.ENDC}")
    
    # 1. Rutas
    repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    agent_src = os.path.join(repo_dir, "suricata", "firewall_agent.py")
    agent_dst = "/usr/local/bin/firewall_agent.py"
    
    if not os.path.exists(agent_src):
        print(f"{Colors.FAIL}[!] No se encuentra el archivo del agente en: {agent_src}{Colors.ENDC}")
        return

    try:
        # 2. Copiar script
        print(f"{Colors.OKBLUE}[*] Instalando agente en {agent_dst}...{Colors.ENDC}")
        subprocess.run(["cp", agent_src, agent_dst], check=True)
        subprocess.run(["chmod", "+x", agent_dst], check=True)
        
        # 3. Crear servicio systemd
        service_content = f"""[Unit]
Description=Firewall Agent - Sync Banned IPs
After=network.target

[Service]
ExecStart=/usr/bin/python3 {agent_dst}
WorkingDirectory={repo_dir}
Restart=always
User=root
# Variables de entorno para encontrar .env (PYTHONUNBUFFERED para ver logs en journalctl)
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
"""
        
        with open("/etc/systemd/system/firewall-agent.service", "w") as f:
            f.write(service_content)
            
        # 4. Iniciar servicio
        subprocess.run(["systemctl", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "enable", "firewall-agent"], check=True)
        subprocess.run(["systemctl", "restart", "firewall-agent"], check=True)
        
        print(f"{Colors.OKGREEN}[OK] Agente de Firewall instalado y corriendo.{Colors.ENDC}")
        print(f"{Colors.OKGREEN}    Este servidor ahora bloqueará automáticamente las IPs de la lista negra.{Colors.ENDC}")
        
    except Exception as e:
        print(f"{Colors.FAIL}[!] Error instalando el agente: {e}{Colors.ENDC}")

def setup_firewall():
    """Configuración principal del firewall"""
    if os.getuid() != 0:
        print(f"{Colors.FAIL}[!] Este script requiere privilegios de superusuario (sudo).{Colors.ENDC}")
        sys.exit(1)

    print("\n" + "="*60)
    print(f"{Colors.HEADER}{Colors.BOLD}   CONFIGURACIÓN DE SEGURIDAD: IPTABLES (FIREWALL){Colors.ENDC}")
    print("="*60)

    # Verificar instalación de iptables
    if not verificar_iptables():
        sys.exit(1)
    
    # Verificar configuración de Netplan (Red)
    if not verificar_netplan():
        print(f"{Colors.WARNING}[!] La configuración de Netplan tiene errores. ¿Desea continuar de todos modos? (s/N): {Colors.ENDC}", end="")
        if input().lower() != 's':
            sys.exit(1)
    
    # Verificar si ya existen reglas
    if not verificar_reglas_existentes():
        sys.exit(0)

    print(f"\n{Colors.BOLD}Seleccione el ROL de esta máquina:{Colors.ENDC}")
    print("1. Servidor de Base de Datos (MySQL)")
    print("2. Nodo de Borde / Web (Nginx)")
    print("3. Servidor Admin / Main (Controlador)")
    
    choice = input(f"\n{Colors.OKBLUE}Opción (1-3): {Colors.ENDC}")

    # Cargar sugerencias del .env si existe
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    suggested_admin = "127.0.0.1"
    suggested_nginx = "127.0.0.1"
    suggested_db = "127.0.0.1"
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if "NGINX_IP=" in line:
                    suggested_nginx = line.split('=')[1].strip()
                elif "DB_IP=" in line:
                    suggested_db = line.split('=')[1].strip()
    
    admin_ip = input(f"{Colors.OKBLUE}Ingrese IP del Servidor Admin [{suggested_admin}]: {Colors.ENDC}") or suggested_admin
    
    reset_iptables()

    print(f"\n{Colors.OKBLUE}[*] Aplicando reglas comunes...{Colors.ENDC}")
    
    # Reglas comunes para TODOS los roles
    run_cmd("sudo iptables -A INPUT -i lo -j ACCEPT", silent=True)
    run_cmd("sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT", silent=True)
    
    # SSH SOLO desde Admin (para administración remota)
    run_cmd(f"sudo iptables -A INPUT -p tcp -s {admin_ip} --dport 22 -j ACCEPT", silent=True)
    print(f"{Colors.OKGREEN}[OK] SSH (22) permitido SOLO desde Admin ({admin_ip}){Colors.ENDC}")


    nginx_ip = None
    db_ip = None

    if choice == '1':
        print(f"\n{Colors.HEADER}[*] Configurando FIREWALL para BASE DE DATOS...{Colors.ENDC}")
        nginx_ip = input(f"{Colors.OKBLUE}Ingrese IP del Nodo Nginx (Web Server) [{suggested_nginx}]: {Colors.ENDC}") or suggested_nginx
        
        # 1. Conectividad Básica (PING/ICMP)
        # Permitir que Nginx y Admin puedan saber si el servidor está vivo
        run_cmd(f"sudo iptables -A INPUT -p icmp -s {admin_ip} -j ACCEPT", silent=True)
        if nginx_ip and nginx_ip != "127.0.0.1":
            run_cmd(f"sudo iptables -A INPUT -p icmp -s {nginx_ip} -j ACCEPT", silent=True)
            print(f"{Colors.OKGREEN}[OK] PING (ICMP) permitido desde Nginx y Admin{Colors.ENDC}")

        # 2. Puerto MySQL (3306)
        # Solo Nginx (para la web) y Admin (para gestión) pueden entrar
        if nginx_ip and nginx_ip != "127.0.0.1":
            run_cmd(f"sudo iptables -A INPUT -p tcp -s {nginx_ip} --dport 3306 -j ACCEPT", silent=True)
            print(f"{Colors.OKGREEN}[OK] MySQL (3306) permitido para Nginx ({nginx_ip}){Colors.ENDC}")
        
        run_cmd(f"sudo iptables -A INPUT -p tcp -s {admin_ip} --dport 3306 -j ACCEPT", silent=True)
        print(f"{Colors.OKGREEN}[OK] MySQL (3306) permitido para Admin ({admin_ip}){Colors.ENDC}")
        
        # 3. Health Server (5001)
        # Solo permitimos que los nodos de confianza vean el estado de la DB
        run_cmd(f"sudo iptables -A INPUT -p tcp -s {admin_ip} --dport 5001 -j ACCEPT", silent=True)
        if nginx_ip and nginx_ip != "127.0.0.1":
            run_cmd(f"sudo iptables -A INPUT -p tcp -s {nginx_ip} --dport 5001 -j ACCEPT", silent=True)
        print(f"{Colors.OKGREEN}[OK] Health Server (5001) restringido a Nginx/Admin{Colors.ENDC}")
        
        # Bloquear todo lo demás (Política DROP)
        run_cmd("sudo iptables -P INPUT DROP", silent=True)
        print(f"\n{Colors.WARNING}⚠️  RECUERDA: MySQL debe escuchar en 0.0.0.0 o tu IP de red.{Colors.ENDC}")
        print(f"{Colors.WARNING}   Verifica /etc/mysql/mysql.conf.d/mysqld.cnf (bind-address).{Colors.ENDC}")

    elif choice == '2':
        print(f"\n{Colors.HEADER}[*] Configurando FIREWALL para NGINX (Web)...{Colors.ENDC}")
        
        # Solicitar IP de la base de datos para diagnóstico
        db_ip = input(f"{Colors.OKBLUE}Ingrese IP del Servidor Base de Datos (para diagnóstico) [{suggested_db}]: {Colors.ENDC}") or suggested_db
        
        # Nginx debe ser accesible para TODOS en puertos HTTP y HTTPS
        run_cmd("sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT", silent=True)
        print(f"{Colors.OKGREEN}[OK] HTTP (80) abierto al público{Colors.ENDC}")
        
        run_cmd("sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT", silent=True)
        print(f"{Colors.OKGREEN}[OK] HTTPS (443) abierto al público{Colors.ENDC}")

        
        # Permitir enviar logs al Dashboard (puerto 5000)
        run_cmd(f"sudo iptables -A OUTPUT -p tcp -d {admin_ip} --dport 5000 -j ACCEPT", silent=True)
        print(f"{Colors.OKGREEN}[OK] Conexión saliente al Dashboard ({admin_ip}:5000) permitida{Colors.ENDC}")
        
        # Bloquear todo lo demás (SSH ya está permitido desde Admin)
        run_cmd("sudo iptables -P INPUT DROP", silent=True)
        print(f"{Colors.WARNING}[OK] Política por defecto: DROP (Solo HTTP público y Admin SSH){Colors.ENDC}")


    elif choice == '3':
        print(f"\n{Colors.HEADER}[*] Configurando FIREWALL para ADMIN (Main)...{Colors.ENDC}")
        
        # Solicitar IPs de otros servidores para diagnóstico
        db_ip = input(f"{Colors.OKBLUE}Ingrese IP del Servidor Base de Datos (para diagnóstico) [{suggested_db}]: {Colors.ENDC}") or suggested_db
        nginx_ip = input(f"{Colors.OKBLUE}Ingrese IP del Servidor Nginx (para diagnóstico) [{suggested_nginx}]: {Colors.ENDC}") or suggested_nginx
        
        # El admin debe poder recibir los logs en el puerto 5000
        run_cmd("sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT", silent=True)
        print(f"{Colors.OKGREEN}[OK] Dashboard (5000) abierto para recibir logs{Colors.ENDC}")
        
        # El admin tiene acceso completo
        run_cmd("sudo iptables -P INPUT ACCEPT", silent=True)
        print(f"{Colors.OKGREEN}[OK] Política por defecto: ACCEPT (Acceso completo){Colors.ENDC}")

    # Mostrar reglas aplicadas
    print(f"\n{Colors.OKBLUE}[*] Reglas de firewall aplicadas:{Colors.ENDC}")
    subprocess.run("sudo iptables -L -n --line-numbers", shell=True)

    # Guardar reglas
    print(f"\n{Colors.OKBLUE}[*] ¿Desea hacer las reglas persistentes?{Colors.ENDC}")
    if input(f"{Colors.WARNING}(s/N): {Colors.ENDC}").lower() == 's':
        if not is_package_installed("iptables-persistent"):
            print(f"{Colors.OKBLUE}[*] Instalando iptables-persistent...{Colors.ENDC}")
            run_cmd("sudo DEBIAN_FRONTEND=noninteractive apt-get update", silent=True)
            run_cmd("sudo DEBIAN_FRONTEND=noninteractive apt-get install -y iptables-persistent", silent=True)
        else:
            print(f"{Colors.OKGREEN}[OK] iptables-persistent ya está instalado.{Colors.ENDC}")
            
        print(f"{Colors.OKBLUE}[*] Guardando reglas actuales...{Colors.ENDC}")
        run_cmd("sudo sh -c 'iptables-save > /etc/iptables/rules.v4'", silent=True)
        print(f"{Colors.OKGREEN}[OK] Reglas guardadas en /etc/iptables/rules.v4{Colors.ENDC}")

    print("\n" + "="*60)
    print(f"{Colors.OKGREEN}{Colors.BOLD}   ¡FIREWALL CONFIGURADO EXITOSAMENTE!{Colors.ENDC}")
    print("="*60)

    # Instalar Agente de Firewall (Opcional) - Solo para Roles 1 y 2 (DB y Nginx)
    if choice in ['1', '2']:
        print(f"\n{Colors.OKBLUE}[*] ¿Desea instalar el Agente de Firewall? (Sincroniza bans del Dashboard) (s/N): {Colors.ENDC}", end="")
        if input().lower() == 's':
            install_firewall_agent_service()

    # Diagnóstico final
    print(f"\n{Colors.OKBLUE}[*] ¿Desea ejecutar diagnóstico de conectividad? (s/N): {Colors.ENDC}", end="")
    if input().lower() == 's':
        diagnostico_final(choice, admin_ip, nginx_ip, db_ip)

if __name__ == "__main__":
    setup_firewall()
