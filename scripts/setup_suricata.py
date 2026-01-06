import socket
import json
import requests
import re
import os

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

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

    # Actualizar config.php
    updates = {"MAIN_SERVER_IP": main_server_ip}
    if role_choice == "1":
        updates["SURICATA_SENSOR_IP"] = local_ip
    else:
        updates["DB_HOST"] = local_ip
    
    from setup_inventory import update_config_php
    update_config_php(updates)

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
        if "rule-files:" in content:
            if "local.rules" not in content:
                content = content.replace("rule-files:", f"rule-files:\n  - {local_rules}")
                print("[+] Reglas locales vinculadas a suricata.yaml")
        else:
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
    interface = "eth0"
    print(f"  sudo suricata -c {suricata_yaml} -i {interface}")
    print("="*45 + "\n")

if __name__ == "__main__":
    setup_suricata()