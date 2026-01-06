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

def install_php_ldap():
    print("\n[*] Instalando extensión LDAP para PHP...")
    try:
        result = subprocess.run(["php", "-v"], capture_output=True, text=True)
        version_match = re.search(r"PHP (\d+\.\d+)", result.stdout)
        pkg = "php-ldap"
        if version_match:
            pkg = f"php{version_match.group(1)}-ldap"
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
    if os.geteuid() != 0:
        print("[!] Este script requiere privilegios de superusuario (sudo).")
        sys.exit(1)

    print("\n" + "="*50)
    print("   MASTER SETUP: INFRAESTRUCTURA Y SEGURIDAD")
    print("="*50)

    # 1. Internet Check
    check_internet()

    # 2. Netplan
    conf_net = input("\n¿Desea configurar la IP estática (Netplan)? (s/N): ").lower()
    if conf_net == 's':
        configure_netplan()

    # 3. LDAP Install
    conf_ldap_inst = input("\n¿Desea instalar la extensión LDAP de PHP? (s/N): ").lower()
    if conf_ldap_inst == 's':
        install_php_ldap()

    # 4. Infraestructura
    print("\n--- Configuración de Servicios ---")
    db_ip = input("IP de la Base de Datos [10.172.86.69]: ") or "10.172.86.69"
    db_user = "webuser"
    db_pass = "web123"
    
    central_server_ip = input(f"IP del Servidor Central (Dashboard + LDAP) [{get_local_ip()}]: ") or get_local_ip()
    ldap_server_ip = central_server_ip
    main_server_ip = central_server_ip

    # 5. Actualizar config.php
    updates = {
        "DB_HOST": db_ip,
        "DB_USER": db_user,
        "DB_PASS": db_pass,
        "MAIN_SERVER_IP": main_server_ip,
        "LDAP_HOST": ldap_server_ip,
        "SURICATA_SENSOR_IP": get_local_ip()
    }
    
    from setup_inventory import update_config_php
    update_config_php(updates)

    # 6. Actualizar auth_ldap.php
    ldap_php_path = os.path.join(os.path.dirname(__file__), "..", "vulnerable_app", "auth_ldap.php")
    if os.path.exists(ldap_php_path):
        print(f"[*] Sincronizando IP LDAP en auth_ldap.php...")
        with open(ldap_php_path, "r") as f:
            content = f.read()
        new_content = re.sub(r'\$ldap_host\s*=\s*".*?";', f'$ldap_host = "{ldap_server_ip}";', content)
        with open(ldap_php_path, "w") as f:
            f.write(new_content)

    # Limpieza final: Borrar .env y configuration.json si existen
    for file_to_del in ["../.env", "configuration.json"]:
        path_del = os.path.abspath(os.path.join(os.path.dirname(__file__), file_to_del))
        if os.path.exists(path_del):
            os.remove(path_del)
            print(f"[-] Archivo eliminado por limpieza: {file_to_del}")

    print("\n" + "="*50)
    print("   ¡SISTEMA CONFIGURADO Y SINCRONIZADO!")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
