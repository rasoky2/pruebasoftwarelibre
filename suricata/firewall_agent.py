import time
import requests
import subprocess
import os
import json

# Configuración
DASHBOARD_API = "http://{admin_ip}:5000/api/banned-list"
LOCAL_BANNED_FILE = "/tmp/local_banned_ips.json"
CHECK_INTERVAL = 10  # Segundos

def get_admin_ip():
    """Intenta obtener la IP del Admin desde .env"""
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "..", ".env"),
        "/var/www/html/pruebasoftwarelibre/.env",
        os.path.abspath(".env")
    ]
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                for line in f:
                    if line.startswith("ADMIN_IP="):
                        return line.split("=")[1].strip()
    return "127.0.0.1"

def get_current_iptables_bans():
    """Obtiene IPs ya bloqueadas en iptables para no repetir comandos"""
    try:
        # Listar reglas INPUT y buscar las IPs droppeadas
        res = subprocess.run("sudo iptables -L INPUT -n", shell=True, capture_output=True, text=True)
        return res.stdout
    except:
        return ""

def sync_bans():
    admin_ip = get_admin_ip()
    api_url = DASHBOARD_API.format(admin_ip=admin_ip)
    
    print(f"[*] Sincronizando bloqueos desde {api_url}...")
    
    try:
        response = requests.get(api_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            remote_bans = set(data.get("banned_ips", []))
            
            # Leer cacheados locales
            local_bans = set()
            if os.path.exists(LOCAL_BANNED_FILE):
                try:
                    with open(LOCAL_BANNED_FILE, 'r') as f:
                        local_bans = set(json.load(f))
                except: pass

            # Nuevas IPs a banear
            new_bans = remote_bans - local_bans
            
            current_rules = get_current_iptables_bans()
            
            for ip in new_bans:
                print(f"[+] Nueva IP para bloquear: {ip}")
                # Verificar si ya está en iptables (por si acaso se reinició el script)
                if ip not in current_rules:
                    subprocess.run(f"sudo iptables -I INPUT -s {ip} -j DROP", shell=True, check=True)
                    print(f"    [OK] IP {ip} bloqueada en Firewall Local.")
                else:
                    print(f"    [SKIP] IP {ip} ya estaba en iptables.")
            
            # Guardar estado actual
            with open(LOCAL_BANNED_FILE, 'w') as f:
                json.dump(list(remote_bans), f)
                
        else:
            print(f"[!] Error API: {response.status_code}")
            
    except Exception as e:
        print(f"[!] Error de conexión: {e}")

if __name__ == "__main__":
    print("=== FIREWALL AGENT ===")
    print("Sincronizando lista negra global...")
    while True:
        sync_bans()
        time.sleep(CHECK_INTERVAL)
