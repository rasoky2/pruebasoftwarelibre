import socket
import json
import requests
import re
import os

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
    url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/config/infrastructure"
    
    fields = {}
    for key, value in data.items():
        if isinstance(value, dict):
            for sub_key, sub_val in value.items():
                fields[f"{key}_{sub_key}"] = {"stringValue": str(sub_val)}
        else:
            fields[key] = {"stringValue": str(value)}
            
    try:
        params = {"updateMask.fieldPaths": list(fields.keys())}
        requests.patch(url, json={"fields": fields}, params=params)
        print("[OK] Sincronizado con Firestore (Nube).")
    except Exception:
        print("[!] Error: No se pudo conectar a Firestore.")

def get_local_ip():
    """Detecta la IP local de la interfaz principal"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

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
    print("[+] .env actualizado.")

def setup_suricata():
    print("\n" + "="*45)
    print("   AUTOMATIC SURICATA CONFIGURATOR")
    print("="*45)
    
    # 1. Identificar Rol del Servidor
    print("\n--- Seleccione el Rol de este Servidor ---")
    print("1) Nodo Borde (Nginx + Suricata)")
    print("2) Servidor de Base de Datos (MySQL)")
    role_choice = input("Seleccione una opción [1]: ") or "1"
    
    role_name = "Nginx/Edge" if role_choice == "1" else "Database"
    local_ip = get_local_ip()
    print(f"[*] IP detectada ({role_name}): {local_ip}")
    
    main_server_ip = input(f"IP del Servidor Central (Dashboard + LDAP) [{local_ip}]: ") or local_ip

    # Actualizar .env
    updates = {"MAIN_SERVER_IP": main_server_ip}
    if role_choice == "1":
        updates["SURICATA_SENSOR_IP"] = local_ip
    else:
        updates["DB_HOST"] = local_ip
    
    update_env(updates)
    
    # 3. Configurar suricata.yaml (HOME_NET y Reglas)
    suricata_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "suricata"))
    suricata_yaml = os.path.join(suricata_dir, "suricata.yaml")
    local_rules = os.path.join(suricata_dir, "rules", "local.rules")

    if os.path.exists(suricata_yaml):
        print(f"[*] Configurando {suricata_yaml}...")
        with open(suricata_yaml, "r") as f:
            content = f.read()
        
        # A. Ajustar HOME_NET: "[IP/32]"
        pattern_net = r"HOME_NET: \"\[.*?\]\""
        replacement_net = f'HOME_NET: "[{local_ip}/32]"'
        content = re.sub(pattern_net, replacement_net, content)
        
        # B. Sincronizar Reglas (Asegurar que local.rules esté mapeado)
        # Buscamos la sección rule-files
        if "rule-files:" in content:
            if "local.rules" not in content:
                # Si no está, lo añadimos al inicio de la lista de reglas
                content = content.replace("rule-files:", f"rule-files:\n  - {local_rules}")
                print("[+] Reglas locales vinculadas a suricata.yaml")
        else:
            # Si no existe la sección, la creamos
            content += f"\nrule-files:\n  - {local_rules}\n"
            print("[+] Sección rule-files creada en suricata.yaml")

        with open(suricata_yaml, "w") as f:
            f.write(content)
    else:
        print("[!] Error: No se encontró suricata.yaml")

    # 4. Directorio de logs
    log_dir = os.path.join(suricata_dir, "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    print("\n[+] CONFIGURACION SURICATA EXITOSA")
    print(f"    - Sensor IP (HOME_NET): {local_ip}")
    print(f"    - Reglas vinculadas: {local_rules}")
    print("\nComando para iniciar:")
    interface = "eth0" # Podríamos detectarlo, pero eth0 es estándar
    print(f"  sudo suricata -c {suricata_yaml} -i {interface}")
    
    # Sincronizar con Firebase
    sync_to_firebase({
        "suricata": {
            "host": local_ip,
            "main_server": main_server_ip,
            "rules": local_rules
        }
    })
    
    print("="*45 + "\n")

if __name__ == "__main__":
    setup_suricata()