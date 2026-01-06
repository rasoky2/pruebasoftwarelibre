import subprocess
import os
import sys

def run_cmd(cmd):
    try:
        subprocess.run(cmd, shell=True, check=True)
        return True
    except Exception as e:
        print(f"[!] Error ejecutando comando: {e}")
        return False

def reset_iptables():
    print("[*] Reseteando reglas de iptables...")
    run_cmd("sudo iptables -F")
    run_cmd("sudo iptables -X")
    run_cmd("sudo iptables -P INPUT ACCEPT")
    run_cmd("sudo iptables -P FORWARD ACCEPT")
    run_cmd("sudo iptables -P OUTPUT ACCEPT")

def setup_firewall():
    if os.getuid() != 0:
        print("[!] Este script requiere privilegios de superusuario (sudo).")
        sys.exit(1)

    print("\n" + "="*50)
    print("   CONFIGURACIÓN DE SEGURIDAD: IPTABLES (FIREWALL)")
    print("="*50)

    print("\nSeleccione el ROL de esta máquina:")
    print("1. Servidor de Base de Datos (MySQL)")
    print("2. Nodo de Borde / Web (Nginx)")
    print("3. Servidor Admin / Main (Controlador)")
    
    choice = input("\nOpción (1-3): ")

    # Cargar sugerencias del .env si existe
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    suggested_admin = "127.0.0.1"
    suggested_nginx = "127.0.0.1"
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if "NGINX_IP=" in line: suggested_admin = line.split('=')[1].strip()
                if "NGINX_IP=" in line: suggested_nginx = line.split('=')[1].strip()

    admin_ip = input(f"Ingrese IP del Servidor Admin (Default {suggested_admin}): ") or suggested_admin
    
    reset_iptables()

    # Reglas comunes
    run_cmd("sudo iptables -A INPUT -i lo -j ACCEPT")
    run_cmd("sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT")
    
    # Permitir SSH siempre desde el Admin
    run_cmd(f"sudo iptables -A INPUT -p tcp -s {admin_ip} --dport 22 -j ACCEPT")
    # Permitir PING siempre desde el Admin
    run_cmd(f"sudo iptables -A INPUT -p icmp -s {admin_ip} -j ACCEPT")

    if choice == '1':
        print("[*] Configurando FIREWALL para BASE DE DATOS...")
        nginx_ip = input("Ingrese IP del Nodo Nginx (Web Server): ")
        
        # Solo Nginx puede hablar con MySQL (3306)
        if nginx_ip:
            run_cmd(f"sudo iptables -A INPUT -p tcp -s {nginx_ip} --dport 3306 -j ACCEPT")
            print(f"[OK] Acceso MySQL permitido solo para {nginx_ip}")
        
        # Bloquear todo lo demás
        run_cmd("sudo iptables -P INPUT DROP")
        print("[OK] Acceso externo bloqueado. Solo Admin y Nginx tienen acceso.")

    elif choice == '2':
        print("[*] Configurando FIREWALL para NGINX (Web)...")
        # Nginx debe ser accesible para TODOS en puerto 80
        run_cmd("sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT")
        
        # Pero solo el Admin puede ver el tráfico de gestión o SSH
        run_cmd("sudo iptables -P INPUT DROP")
        print("[OK] Servidor Web (80) abierto al público. Gestión restringida al Admin.")

    elif choice == '3':
        print("[*] Configurando FIREWALL para ADMIN (Main)...")
        # El admin debe poder recibir los logs en el puerto 5000
        run_cmd("sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT")
        # El admin suele tener acceso libre para controlar al resto
        run_cmd("sudo iptables -P INPUT ACCEPT")
        print("[OK] Servidor Admin configurado para recibir alertas en puerto 5000.")

    # Guardar reglas (depende del sistema, instalamos iptables-persistent si no está)
    print("\n[*] ¿Desea hacer las reglas persistentes? (Instalará iptables-persistent)")
    if input("(s/N): ").lower() == 's':
        run_cmd("sudo apt-get update && sudo apt-get install -y iptables-persistent")
        run_cmd("sudo sh -c 'iptables-save > /etc/iptables/rules.v4'")

    print("\n" + "="*50)
    print("   ¡FIREWALL CONFIGURADO EXITOSAMENTE!")
    print("="*50 + "\n")

if __name__ == "__main__":
    setup_firewall()
