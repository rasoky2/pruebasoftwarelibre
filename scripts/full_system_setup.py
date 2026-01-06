import os
import sys
import socket
import subprocess
import re
import yaml
import json
import requests

def check_internet():
    print("[*] Verificando conexión a Internet...")
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        print("[OK] Conexión a Internet detectada.")
        return True
    except Exception:
        print("[!] Error: No hay conexión a Internet.")
        return False

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception: return "127.0.0.1"

def check_package_installed(package_name):
    try:
        result = subprocess.run(["dpkg", "-l", package_name], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def install_php_ldap():
    # Detectar versión de PHP y nombre del paquete
    try:
        result = subprocess.run(["php", "-v"], capture_output=True, text=True)
        version_match = re.search(r"PHP (\d+\.\d+)", result.stdout)
        if not version_match:
            print("[!] No se detectó PHP instalado.")
            return
        php_version = version_match.group(1)
        pkg = f"php{php_version}-ldap"
    except Exception:
        pkg = "php-ldap"

    # Verificar si ya está instalado
    print(f"[*] Verificando {pkg}...")
    try:
        check_ext = subprocess.run(["php", "-m"], capture_output=True, text=True)
        if "ldap" in check_ext.stdout.lower():
            print(f"[OK] La extensión LDAP ya está instalada en PHP.")
            return
    except Exception: pass

    print(f"\n[*] Instalando extensión LDAP para PHP ({pkg})...")
    try:
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "-y", pkg], check=True)
        print("[OK] LDAP instalado correctamente.")
    except Exception as e:
        print(f"[!] Error al instalar LDAP: {e}")

def get_default_gateway():
    try:
        result = subprocess.run(["ip", "route"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if "default via" in line:
                return line.split()[2]
    except Exception: pass
    return "10.172.86.1"

def configure_netplan():
    print("\n--- Configuración de Red (Netplan) ---")
    try:
        interface = subprocess.check_output("ip -o link show | awk -F': ' '{print $2}' | grep -v 'lo' | head -n1", shell=True).decode().strip()
    except Exception: interface = "ens33"
    gateway = get_default_gateway()
    local_ip = get_local_ip()
    suggested_ip = f"{local_ip}/24"
    interface = input(f"Interfaz de red [{interface}]: ") or interface
    new_ip = input(f"Ingrese IP estática con CIDR [{suggested_ip}]: ") or suggested_ip
    gateway = input(f"Gateway [{gateway}]: ") or gateway
    dns = input("DNS [8.8.8.8, 1.1.1.1]: ") or "8.8.8.8, 1.1.1.1"
    config = {"network": {"version": 2, "renderer": "networkd", "ethernets": {interface: {"addresses": [new_ip], "routes": [{"to": "default", "via": gateway}], "nameservers": {"addresses": [d.strip() for d in dns.split(",")]}}}}}
    target_file = "/etc/netplan/01-netcfg.yaml"
    try:
        with open("temp_netplan.yaml", "w") as f: yaml.dump(config, f)
        subprocess.run(["sudo", "cp", "temp_netplan.yaml", target_file], check=True)
        subprocess.run(["sudo", "netplan", "apply"], check=True)
        print("[OK] Red configurada.")
        if os.path.exists("temp_netplan.yaml"): os.remove("temp_netplan.yaml")
    except Exception as e: print(f"[!] Error en Netplan: {e}")
def run_diagnostics(ips):
    print("\n" + "-"*30)
    print("   DIAGNÓSTICO DE CONEXIÓN")
    print("-"*30)
    
    for name, ip in ips.items():
        if not ip or ip == "127.0.0.1":
            continue
            
        print(f"[*] Probando {name} ({ip})... ", end="", flush=True)
        try:
            # Usar comando ping (1 paquete, wait 2s)
            param = "-n" if platform.system().lower() == "windows" else "-c"
            command = ["ping", param, "1", "-W", "2", ip]
            result = subprocess.run(command, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"{Colors.OKGREEN}[CONECTADO]{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}[SIN RESPUESTA]{Colors.ENDC}")
        except Exception:
            print(f"{Colors.FAIL}[ERROR AL PROBAR]{Colors.ENDC}")
    print("-"*30 + "\n")

import platform

class Colors:
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def main():
    if os.getuid() != 0:
        print("[!] Este script requiere privilegios de superusuario (sudo).")
        sys.exit(1)

    print("\n" + "="*50)
    print("   MASTER SETUP: INFRAESTRUCTURA Y SEGURIDAD")
    print("="*50)

    # 1. Internet Check inicial
    check_internet()

    # 2. Netplan
    conf_net = input("\n¿Desea configurar la IP estática (Netplan)? (s/N): ").lower()
    if conf_net == 's':
        configure_netplan()
        print("\n[*] Re-verificando internet tras cambio de red...")
        check_internet()

    # 3. LDAP Install
    conf_ldap_inst = input("\n¿Desea instalar la extensión LDAP de PHP? (s/N): ").lower()
    if conf_ldap_inst == 's':
        install_php_ldap()

    # 4. Infraestructura e IPs
    print("\n--- Configuración de Roles y Servicios ---")
    local_ip = get_local_ip()
    
    is_admin = input("¿Es esta máquina el Servidor LDAP (Admin)? (S/n): ").lower() != 'n'
    
    if is_admin:
        print("[*] Configurando como Servidor LDAP (Admin).")
        ldap_server_ip = local_ip
    else:
        ldap_server_ip = input("IP del Servidor LDAP Admin: ")
        if not ldap_server_ip:
            ldap_server_ip = "127.0.0.1"
            print("[!] No se ingresó IP, usando 127.0.0.1 por defecto.")

    db_ip = input("IP de la Base de Datos [127.0.0.1]: ") or "127.0.0.1"
    central_server_ip = input(f"IP del Dashboard (Servidor Central) [{ldap_server_ip}]: ") or ldap_server_ip
    
    # 5. Diagnóstico Voluntario
    if input("\n¿Desea realizar un diagnóstico de conexión con los servidores? (s/N): ").lower() == 's':
        run_diagnostics({
            "Servidor LDAP (Admin)": ldap_server_ip,
            "Base de Datos": db_ip,
            "Dashboard": central_server_ip
        })

    # 6. Actualizar config.php
    updates = {
        "DB_HOST": db_ip,
        "DB_NAME": "lab_vulnerable",
        "DB_USER": "webuser",
        "DB_PASS": "web123",
        "MAIN_SERVER_IP": central_server_ip,
        "LDAP_HOST": ldap_server_ip,
        "SURICATA_SENSOR_IP": local_ip
    }
    
    from setup_inventory import update_config_php
    update_config_php(updates)

    # 7. Actualizar auth_ldap.php
    ldap_php_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "vulnerable_app", "auth_ldap.php"))
    if os.path.exists(ldap_php_path):
        print(f"[*] Sincronizando IP LDAP en auth_ldap.php...")
        with open(ldap_php_path, "r") as f:
            content = f.read()
        new_content = re.sub(r'\$ldap_host\s*=\s*".*?";', f'$ldap_host = "{ldap_server_ip}";', content)
        with open(ldap_php_path, "w") as f:
            f.write(new_content)

    # Limpieza final
    for file_to_del in ["../.env", "configuration.json"]:
        path_del = os.path.abspath(os.path.join(os.path.dirname(__file__), file_to_del))
        if os.path.exists(path_del):
            try:
                os.remove(path_del)
                print(f"[-] Archivo eliminado por limpieza: {file_to_del}")
            except: pass

    print("\n" + "="*50)
    print("   ¡SISTEMA CONFIGURADO Y SINCRONIZADO!")
    print("   Usa setup_nginx.py o setup_db_mysql.py para servicios específicos.")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
