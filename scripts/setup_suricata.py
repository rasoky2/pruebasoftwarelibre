import os
import sys
import re
import socket

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
    print(f"[*] Configurando como: {role_name}")

    # 2. Detección automática de IP
    detected_ip = get_local_ip()
    print(f"[*] IP detectada en equipo {role_name}: {detected_ip}")
    use_detected = input(f"¿Usar esta IP? (S/n): ").lower()
    
    if use_detected == '' or use_detected == 's':
        local_ip = detected_ip
    else:
        local_ip = input(f"Ingrese la IP manual para {role_name}: ")

    main_server_ip = input("Ingrese la IP del Servidor Main (Dashboard): ")
    
    # 3. Actualizar el archivo .env
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        print(f"[*] Actualizando variables en .env...")
        with open(env_path, "r") as f:
            lines = f.readlines()
        
        with open(env_path, "w") as f:
            for line in lines:
                if line.startswith("MAIN_SERVER_IP="):
                    f.write(f"MAIN_SERVER_IP={main_server_ip}\n")
                elif line.startswith("SURICATA_SENSOR_IP=") and role_choice == "1":
                    f.write(f"SURICATA_SENSOR_IP={local_ip}\n")
                elif line.startswith("DB_HOST=") and role_choice == "2":
                    f.write(f"DB_HOST={local_ip}\n")
                else:
                    f.write(line)
    
    # 3. Configurar suricata.yaml
    suricata_yaml = os.path.join(os.path.dirname(__file__), "..", "suricata", "suricata.yaml")
    if os.path.exists(suricata_yaml):
        print(f"[*] Modificando HOME_NET en {suricata_yaml}...")
        with open(suricata_yaml, "r") as f:
            content = f.read()
        
        # Ajustar HOME_NET: "[IP/32]"
        pattern = r"HOME_NET: \"\[.*?\]\""
        replacement = f'HOME_NET: "[{local_ip}/32]"'
        new_content = re.sub(pattern, replacement, content)
        
        with open(suricata_yaml, "w") as f:
            f.write(new_content)
    else:
        print("[!] Error: No se encontró suricata.yaml")

    # 4. Directorio de logs
    log_dir = os.path.join(os.path.dirname(__file__), "..", "suricata", "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    print("\n[+] CONFIGURACION SURICATA EXITOSA")
    print(f"    - Sensor IP (HOME_NET): {local_ip}")
    print(f"    - Reportando a Main: {main_server_ip}")
    print("\nComando para iniciar:")
    print(f"  sudo suricata -c {os.path.abspath(suricata_yaml)} -i eth0")
    print("="*45 + "\n")

if __name__ == "__main__":
    setup_suricata()