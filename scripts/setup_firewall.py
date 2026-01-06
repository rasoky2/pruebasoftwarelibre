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

def diagnostico_final(role, admin_ip, nginx_ip=None):
    """Ejecuta diagnóstico de conectividad al final de la configuración"""
    print("\n" + "="*60)
    print(f"{Colors.HEADER}{Colors.BOLD}   DIAGNÓSTICO DE CONECTIVIDAD{Colors.ENDC}")
    print("="*60 + "\n")
    
    results = {}
    
    if role == '1':  # Base de Datos
        print(f"{Colors.BOLD}Verificando conectividad desde Base de Datos:{Colors.ENDC}\n")
        
        # Probar Admin
        results['admin_ping'] = test_connectivity(admin_ip, "Servidor Admin")
        results['admin_ssh'] = test_port(admin_ip, 22, "SSH Admin")
        
        # Probar Nginx
        if nginx_ip and nginx_ip != "127.0.0.1":
            print()
            results['nginx_ping'] = test_connectivity(nginx_ip, "Servidor Nginx")
            results['nginx_http'] = test_port(nginx_ip, 80, "HTTP Nginx")
        
    elif role == '2':  # Nginx
        print(f"{Colors.BOLD}Verificando conectividad desde Nginx:{Colors.ENDC}\n")
        
        # Probar Admin
        results['admin_ping'] = test_connectivity(admin_ip, "Servidor Admin")
        results['admin_dashboard'] = test_port(admin_ip, 5000, "Dashboard Admin")
        
    elif role == '3':  # Admin
        print(f"{Colors.BOLD}Verificando conectividad desde Admin:{Colors.ENDC}\n")
        
        # El admin puede probar contra sí mismo
        print(f"{Colors.OKGREEN}[OK] Servidor Admin - Acceso completo{Colors.ENDC}")
        results['admin_ok'] = True
    
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
        print("  • Revisar configuración de red (IPs correctas)")
        print("  • Verificar firewall en los servidores destino")
        print("  • Ejecutar: sudo iptables -L -n (para ver reglas actuales)\n")

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
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if "NGINX_IP=" in line:
                    suggested_nginx = line.split('=')[1].strip()
                # Asumimos que el admin es la máquina local o se especifica
    
    admin_ip = input(f"{Colors.OKBLUE}Ingrese IP del Servidor Admin [{suggested_admin}]: {Colors.ENDC}") or suggested_admin
    
    reset_iptables()

    print(f"\n{Colors.OKBLUE}[*] Aplicando reglas comunes...{Colors.ENDC}")
    
    # Reglas comunes
    run_cmd("sudo iptables -A INPUT -i lo -j ACCEPT", silent=True)
    run_cmd("sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT", silent=True)
    
    # Permitir SSH desde el Admin
    run_cmd(f"sudo iptables -A INPUT -p tcp -s {admin_ip} --dport 22 -j ACCEPT", silent=True)
    print(f"{Colors.OKGREEN}[OK] SSH permitido desde Admin ({admin_ip}){Colors.ENDC}")
    
    # Permitir PING desde el Admin
    run_cmd(f"sudo iptables -A INPUT -p icmp -s {admin_ip} -j ACCEPT", silent=True)
    print(f"{Colors.OKGREEN}[OK] PING permitido desde Admin{Colors.ENDC}")

    nginx_ip = None

    if choice == '1':
        print(f"\n{Colors.HEADER}[*] Configurando FIREWALL para BASE DE DATOS...{Colors.ENDC}")
        nginx_ip = input(f"{Colors.OKBLUE}Ingrese IP del Nodo Nginx (Web Server) [{suggested_nginx}]: {Colors.ENDC}") or suggested_nginx
        
        # Solo Nginx y Admin pueden hablar con MySQL (3306)
        if nginx_ip and nginx_ip != "127.0.0.1":
            run_cmd(f"sudo iptables -A INPUT -p tcp -s {nginx_ip} --dport 3306 -j ACCEPT", silent=True)
            print(f"{Colors.OKGREEN}[OK] MySQL (3306) accesible desde Nginx ({nginx_ip}){Colors.ENDC}")
        
        # Permitir MySQL desde Admin también
        run_cmd(f"sudo iptables -A INPUT -p tcp -s {admin_ip} --dport 3306 -j ACCEPT", silent=True)
        print(f"{Colors.OKGREEN}[OK] MySQL (3306) accesible desde Admin ({admin_ip}){Colors.ENDC}")
        
        # Bloquear todo lo demás
        run_cmd("sudo iptables -P INPUT DROP", silent=True)
        print(f"{Colors.WARNING}[OK] Política por defecto: DROP (Solo Admin y Nginx permitidos){Colors.ENDC}")

    elif choice == '2':
        print(f"\n{Colors.HEADER}[*] Configurando FIREWALL para NGINX (Web)...{Colors.ENDC}")
        
        # Nginx debe ser accesible para TODOS en puerto 80
        run_cmd("sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT", silent=True)
        print(f"{Colors.OKGREEN}[OK] HTTP (80) abierto al público{Colors.ENDC}")
        
        # Bloquear todo lo demás (SSH ya está permitido desde Admin)
        run_cmd("sudo iptables -P INPUT DROP", silent=True)
        print(f"{Colors.WARNING}[OK] Política por defecto: DROP (Solo HTTP público y Admin SSH){Colors.ENDC}")

    elif choice == '3':
        print(f"\n{Colors.HEADER}[*] Configurando FIREWALL para ADMIN (Main)...{Colors.ENDC}")
        
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
    print(f"\n{Colors.OKBLUE}[*] ¿Desea hacer las reglas persistentes? (Instalará iptables-persistent){Colors.ENDC}")
    if input(f"{Colors.WARNING}(s/N): {Colors.ENDC}").lower() == 's':
        print(f"{Colors.OKBLUE}[*] Instalando iptables-persistent...{Colors.ENDC}")
        run_cmd("sudo DEBIAN_FRONTEND=noninteractive apt-get update", silent=True)
        run_cmd("sudo DEBIAN_FRONTEND=noninteractive apt-get install -y iptables-persistent", silent=True)
        run_cmd("sudo sh -c 'iptables-save > /etc/iptables/rules.v4'", silent=True)
        print(f"{Colors.OKGREEN}[OK] Reglas guardadas en /etc/iptables/rules.v4{Colors.ENDC}")

    print("\n" + "="*60)
    print(f"{Colors.OKGREEN}{Colors.BOLD}   ¡FIREWALL CONFIGURADO EXITOSAMENTE!{Colors.ENDC}")
    print("="*60)

    # Diagnóstico final
    print(f"\n{Colors.OKBLUE}[*] ¿Desea ejecutar diagnóstico de conectividad? (s/N): {Colors.ENDC}", end="")
    if input().lower() == 's':
        diagnostico_final(choice, admin_ip, nginx_ip)

if __name__ == "__main__":
    setup_firewall()
