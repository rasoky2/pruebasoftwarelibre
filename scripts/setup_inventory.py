import os
import socket
import json
import requests
import re

def get_firebase_config():
    config_path = os.path.join(os.path.dirname(__file__), "configuration.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    return None

def sync_to_firebase(data):
    config = get_firebase_config()
    if not config: return
    project_id = config['projectId']
    # Firestore REST URL para el documento 'config/infrastructure'
    url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/config/infrastructure"
    
    # Preparar campos para Firestore (formato campos: { "key": { "stringValue": "val" } })
    fields = {}
    for key, value in data.items():
        if isinstance(value, dict):
            # Aplanar diccionarios anidados para Firestore simplificado
            for sub_key, sub_val in value.items():
                fields[f"{key}_{sub_key}"] = {"stringValue": str(sub_val)}
        else:
            fields[key] = {"stringValue": str(value)}
            
    try:
        # Usamos PATCH con query string para actualizar o crear campos específicos
        params = {"updateMask.fieldPaths": list(fields.keys())}
        requests.patch(url, json={"fields": fields}, params=params)
        print("[OK] Sincronizado con Firestore (Nube).")
    except Exception:
        print("[!] Error: No se pudo conectar a Firestore.")

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
    central_ip = input(f"IP Servidor Central (Dashboard + LDAP) [{local_ip}]: ") or local_ip
    db_host = input(f"IP Servidor MySQL [10.172.86.69]: ") or "10.172.86.69"
    db_user = "webuser"
    db_pass = "web123"
    ldap_host = central_ip
    main_ip = central_ip

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

    # Sincronizar con Firebase
    sync_to_firebase({
        "mysql": {"host": db_host, "user": db_user, "password": db_pass},
        "ldap": {"host": ldap_host},
        "dashboard": {"host": main_ip},
        "edge_node": {"host": local_ip}
    })

    print("\n" + "="*50)
    print("   ¡CONFIGURACIÓN COMPLETADA!")
    print("="*50 + "\n")

if __name__ == "__main__":
    setup_inventory()
