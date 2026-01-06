import os
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

def update_env(updates):
    """
    Actualiza el archivo .env con las claves proporcionadas.
    Esta es la ÚNICA función que debe modificar el .env.
    """
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    env_data = {}
    
    # Cargar datos actuales si existe
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env_data[k.strip()] = v.strip()
    
    # Aplicar actualizaciones
    env_data.update(updates)
    
    # Guardar de nuevo
    with open(env_path, "w") as f:
        for k, v in env_data.items():
            f.write(f"{k}={v}\n")
    print("[+] Archivo .env actualizado.")

def update_config_php(updates):
    """
    DEPRECATED: Esta función ya NO debe usarse para DB/IPs.
    Solo se mantiene para compatibilidad con código legacy.
    Usa update_env() en su lugar.
    """
    config_path = os.path.join(os.path.dirname(__file__), "..", "vulnerable_app", "config.php")
    if not os.path.exists(config_path):
        print(f"[!] Error: {config_path} no existe.")
        return
    
    with open(config_path, "r") as f:
        content = f.read()
    
    for key, value in updates.items():
        # Buscar la variable PHP y reemplazar su valor
        pattern = rf'\${key}\s*=\s*\'.*?\';'
        replacement = f"${key} = '{value}';"
        content = re.sub(pattern, replacement, content)
            
    with open(config_path, "w") as f:
        f.write(content)
    print("[+] config.php actualizado (legacy).")

def setup_inventory():
    print("\n" + "="*50)
    print("   CONFIGURADOR GLOBAL DE INFRAESTRUCTURA")
    print("="*50)
    local_ip = get_local_ip()
    
    central_ip = input(f"IP Servidor Central (Dashboard + LDAP) [{local_ip}]: ") or local_ip
    db_host = input("IP Servidor MySQL [127.0.0.1]: ") or "127.0.0.1"
    db_name = input("Nombre de la DB [lab_vulnerable]: ") or "lab_vulnerable"
    db_user = input("Usuario MySQL [webuser]: ") or "webuser"
    db_pass = input("Contraseña MySQL [web123]: ") or "web123"
    
    # ÚNICA FUENTE DE VERDAD: .env
    update_env({
        "ADMIN_IP": central_ip,
        "NGINX_IP": local_ip,
        "DB_IP": db_host,
        "DB_NAME": db_name,
        "DB_USER": db_user,
        "DB_PASS": db_pass,
        "LDAP_IP": central_ip
    })

    # Actualizar auth_ldap.php solo para la IP de LDAP (no tiene acceso a .env)
    php_path = os.path.join(os.path.dirname(__file__), "..", "vulnerable_app", "auth_ldap.php")
    if os.path.exists(php_path):
        with open(php_path, "r") as f:
            content = f.read()
        content = re.sub(r'\$ldap_host\s*=\s*".*?";', f'$ldap_host = "{central_ip}";', content)
        with open(php_path, "w") as f:
            f.write(content)
        print("[+] Módulo LDAP sincronizado.")

    print("\n" + "="*50)
    print("   ¡CONFIGURACIÓN COMPLETADA!")
    print("="*50 + "\n")

if __name__ == "__main__":
    setup_inventory()
