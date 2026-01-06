import os
import socket
import json
import requests
import re

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception: return "127.0.0.1"

def update_config_php(updates):
    config_path = os.path.join(os.path.dirname(__file__), "..", "vulnerable_app", "config.php")
    if not os.path.exists(config_path):
        print(f"[!] Error: {config_path} no existe.")
        return
    
    with open(config_path, "r") as f:
        content = f.read()
    
    for key, value in updates.items():
        # Buscar la variable PHP y reemplazar su valor
        # Ejemplo: $DB_HOST = '...';
        pattern = rf'\${key}\s*=\s*\'.*?\';'
        replacement = f"${key} = '{value}';"
        content = re.sub(pattern, replacement, content)
            
    with open(config_path, "w") as f:
        f.write(content)
    print(f"[+] config.php actualizado.")

def update_env(updates):
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    env_data = {}
    
    # Cargar datos actuales si existe
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    env_data[k] = v
    
    # Aplicar actualizaciones
    env_data.update(updates)
    
    # Guardar de nuevo
    with open(env_path, "w") as f:
        for k, v in env_data.items():
            f.write(f"{k}={v}\n")
    print(f"[+] Archivo .env actualizado.")

def setup_inventory():
    print("\n" + "="*50)
    print("   CONFIGURADOR GLOBAL DE INFRAESTRUCTURA")
    print("="*50)
    local_ip = get_local_ip()
    central_ip = input(f"IP Servidor Central (Dashboard + LDAP) [{local_ip}]: ") or local_ip
    db_host = input(f"IP Servidor MySQL [10.172.86.69]: ") or "10.172.86.69"
    db_user = "webuser"
    db_pass = "web123"
    ldap_host = central_ip
    main_ip = central_ip

    # Actualizar config.php
    update_config_php({
        "DB_HOST": db_host,
        "DB_USER": db_user,
        "DB_PASS": db_pass,
        "MAIN_SERVER_IP": main_ip,
        "SURICATA_SENSOR_IP": local_ip,
        "LDAP_HOST": ldap_host
    })

    # Actualizar auth_ldap.php
    php_path = os.path.join(os.path.dirname(__file__), "..", "vulnerable_app", "auth_ldap.php")
    if os.path.exists(php_path):
        with open(php_path, "r") as f: content = f.read()
        content = re.sub(r'\$ldap_host\s*=\s*".*?";', f'$ldap_host = "{ldap_host}";', content)
        with open(php_path, "w") as f: f.write(content)
        print("[+] Módulo LDAP sincronizado.")

    print("\n" + "="*50)
    print("   ¡CONFIGURACIÓN COMPLETADA!")
    print("="*50 + "\n")

if __name__ == "__main__":
    setup_inventory()
