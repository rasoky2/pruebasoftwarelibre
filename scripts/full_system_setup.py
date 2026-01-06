import os
import sys
import socket
import subprocess
import re
import yaml

def check_internet():
    print("[*] Verificando conexión a Internet...")
    try:
        # Intentar conectar al DNS de Google
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        print("[OK] Conexión a Internet detectada.")
        return True
    except OSError:
        print("[!] Error: No hay conexión a Internet.")
        return False

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except: return "127.0.0.1"

def update_env(updates):
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if not os.path.exists(env_path):
        with open(env_path, "w") as f:
            f.write("# Configuración del Laboratorio\n")
    
    with open(env_path, "r") as f:
        lines = f.readlines()
    
    new_lines = []
    keys_updated = set()
    
    for line in lines:
        updated = False
        for key, value in updates.items():
            if line.startswith(f"{key}="):
                new_lines.append(f"{key}={value}\n")
                keys_updated.add(key)
                updated = True
                break
        if not updated:
            new_lines.append(line)
            
    for key, value in updates.items():
        if key not in keys_updated:
            new_lines.append(f"{key}={value}\n")
            
    with open(env_path, "w") as f:
        f.writelines(new_lines)
    print(f"[+] Archivo .env actualizado en {env_path}")

def install_php_ldap():
    print("\n[*] Instalando extensión LDAP para PHP...")
    try:
        # Intentar detectar versión de PHP para instalar el paquete correcto
        result = subprocess.run(["php", "-v"], capture_output=True, text=True)
        version_match = re.search(r"PHP (\d+\.\d+)", result.stdout)
        pkg = "php-ldap"
        if version_match:
            v = version_match.group(1)
            pkg = f"php{v}-ldap"
        
        print(f"[*] Ejecutando: sudo apt install -y {pkg}")
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "-y", pkg], check=True)
        print("[OK] LDAP instalado correctamente.")
    except Exception as e:
        print(f"[!] Error al instalar LDAP: {e}")

def configure_netplan():
    print("\n--- Configuración de Red (Netplan) ---")
    interface = input("Interfaz de red (ej. ens33, eth0): ")
    new_ip = input("Ingrese IP estática con CIDR (ej. 10.172.86.110/24): ")
    gateway = input("Gateway (ej. 10.172.86.1): ")
    dns = input("DNS [8.8.8.8, 1.1.1.1]: ") or "8.8.8.8, 1.1.1.1"

    config = {
        "network": {
            "version": 2,
            "renderer": "networkd",
            "ethernets": {
                interface: {
                    "addresses": [new_ip],
                    "routes": [{"to": "default", "via": gateway}],
                    "nameservers": {"addresses": [d.strip() for d in dns.split(",")]}
                }
            }
        }
    }

    netplan_dir = "/etc/netplan/"
    if not os.path.exists(netplan_dir):
        print("[!] Directorio netplan no encontrado. Saltando configuración de red.")
        return

    yamls = [f for f in os.listdir(netplan_dir) if f.endswith(".yaml")]
    target_file = os.path.join(netplan_dir, yamls[0] if yamls else "01-netcfg.yaml")

    try:
        with open("temp_netplan.yaml", "w") as f:
            yaml.dump(config, f, default_flow_style=False)
        subprocess.run(["sudo", "cp", "temp_netplan.yaml", target_file], check=True)
        print("[*] Aplicando Netplan...")
        subprocess.run(["sudo", "netplan", "apply"], check=True)
        print("[OK] Red configurada.")
        os.remove("temp_netplan.yaml")
    except Exception as e:
        print(f"[!] Error en Netplan: {e}")

def main():
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
    
    ldap_server_ip = input("IP de la Computadora Principal (LDAP Agustín) [10.172.86.161]: ") or "10.172.86.161"
    main_server_ip = input(f"IP del Dashboard Central (Python) [{get_local_ip()}]: ") or get_local_ip()

    # 5. Actualizar .env
    updates = {
        "DB_HOST": db_ip,
        "DB_USER": db_user,
        "DB_PASS": db_pass,
        "MAIN_SERVER_IP": main_server_ip,
        "LDAP_HOST": ldap_server_ip
    }
    update_env(updates)

    # 6. Actualizar auth_ldap.php
    ldap_php_path = os.path.join(os.path.dirname(__file__), "..", "vulnerable_app", "auth_ldap.php")
    if os.path.exists(ldap_php_path):
        print(f"[*] Sincronizando IP LDAP en auth_ldap.php...")
        with open(ldap_php_path, "r") as f:
            content = f.read()
        new_content = re.sub(r'\$ldap_host\s*=\s*".*?";', f'$ldap_host = "{ldap_server_ip}";', content)
        with open(ldap_php_path, "w") as f:
            f.write(new_content)

    print("\n" + "="*50)
    print("   ¡SISTEMA CONFIGURADO Y SINCRONIZADO!")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
