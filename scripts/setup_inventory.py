import os
import socket
import re

def get_local_ip():
    """Obtiene la IP local de la máquina"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def load_env():
    """Lee el archivo .env y devuelve un diccionario con las variables"""
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    env_data = {}
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env_data[k.strip()] = v.strip()
    return env_data

def update_env(updates):
    """
    Actualiza el archivo .env con las claves proporcionadas.
    Esta es la ÚNICA función que debe modificar el .env.
    
    Args:
        updates (dict): Diccionario con las claves y valores a actualizar
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

# Este archivo ahora solo contiene funciones de utilidad
# Para configurar LDAP, usa: setup_ldap.py
# Para configurar MySQL, usa: setup_db_mysql.py
# Para configurar Nginx, usa: setup_nginx.py
# Para configurar Firewall, usa: setup_firewall.py
