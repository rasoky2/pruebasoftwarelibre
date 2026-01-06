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

def setup_inventory():
    print("\n" + "="*50)
    print("   CONFIGURADOR GLOBAL DE INFRAESTRUCTURA")
    print("="*50)

    # 1. Configuración de Red Local
    local_ip = get_local_ip()
    print(f"[*] IP actual detectada: {local_ip}")

    # 2. Configuración de Base de Datos
    print("\n[ DATOS DE MYSQL ]")
    db_host = input(f"IP Servidor MySQL [192.168.1.57]: ") or "192.168.1.57"
    db_user = input(f"Usuario MySQL [webuser]: ") or "webuser"
    db_pass = input("Contraseña de MySQL [web123]: ") or "web123"

    # 3. Configuración de LDAP (Agustín)
    print("\n[ DATOS DE LDAP (AGUSTÍN) ]")
    ldap_host = input("IP Servidor LDAP de Agustín [10.172.86.161]: ") or "10.172.86.161"
    
    # 4. Configuración Dashboard Main
    print("\n[ DATOS DEL DASHBOARD MAIN ]")
    main_ip = input(f"IP del Servidor Python Dashboard [{local_ip}]: ") or local_ip

    # --- Actualización de .env ---
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        print(f"\n[*] Actualizando archivo .env...")
        with open(env_path, "r") as f:
            lines = f.readlines()
        
        with open(env_path, "w") as f:
            for line in lines:
                if line.startswith("DB_HOST="): f.write(f"DB_HOST={db_host}\n")
                elif line.startswith("DB_USER="): f.write(f"DB_USER={db_user}\n")
                elif line.startswith("DB_PASS="): f.write(f"DB_PASS={db_pass}\n")
                elif line.startswith("MAIN_SERVER_IP="): f.write(f"MAIN_SERVER_IP={main_ip}\n")
                elif line.startswith("SURICATA_SENSOR_IP="): f.write(f"SURICATA_SENSOR_IP={local_ip}\n")
                else: f.write(line)
        print("[+] .env actualizado.")

    # --- Actualización de auth_ldap.php ---
    ldap_php_path = os.path.join(os.path.dirname(__file__), "..", "vulnerable_app", "auth_ldap.php")
    if os.path.exists(ldap_php_path):
        print(f"[*] Actualizando IP de Agustín en auth_ldap.php...")
        with open(ldap_php_path, "r") as f:
            content = f.read()
        
        # Regex para buscar la variable $ldap_host
        new_content = re.sub(r'\$ldap_host\s*=\s*".*?";', f'$ldap_host = "{ldap_host}";', content)
        
        with open(ldap_php_path, "w") as f:
            f.write(new_content)
        print("[+] Módulo LDAP actualizado.")

    print("\n" + "="*50)
    print("   ¡CONFIGURACIÓN COMPLETADA!")
    print("="*50 + "\n")

if __name__ == "__main__":
    setup_inventory()
