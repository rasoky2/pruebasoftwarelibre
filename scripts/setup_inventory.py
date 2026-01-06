import os
import sys
import re
import socket

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
        with open(env_path, "w") as f: f.write("# Config\n")
    
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
        if not updated: new_lines.append(line)
            
    for key, value in updates.items():
        if key not in keys_updated:
            new_lines.append(f"{key}={value}\n")
            
    with open(env_path, "w") as f:
        f.writelines(new_lines)
    print(f"[+] .env actualizado.")

def setup_inventory():
    print("\n" + "="*50)
    print("   CONFIGURADOR GLOBAL DE INFRAESTRUCTURA")
    print("="*50)

    local_ip = get_local_ip()
    db_host = input(f"IP Servidor MySQL [10.172.86.69]: ") or "10.172.86.69"
    db_user = "webuser"
    db_pass = "web123"
    ldap_host = input("IP Servidor LDAP [10.172.86.161]: ") or "10.172.86.161"
    main_ip = input(f"IP Dashboard Main [{local_ip}]: ") or local_ip

    # Actualizar .env
    update_env({
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

    print("="*50 + "\n")

    print("\n" + "="*50)
    print("   ¡CONFIGURACIÓN COMPLETADA!")
    print("="*50 + "\n")

if __name__ == "__main__":
    setup_inventory()
