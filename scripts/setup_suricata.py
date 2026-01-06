import os
import sys
import re

def setup_suricata():
    print("--- Configurador Automatico de Suricata ---")
    
    # 1. Obtener datos del usuario
    local_ip = input("Ingrese la IP de este Nodo Suricata (ej. 192.168.1.56): ")
    main_server_ip = input("Ingrese la IP del Servidor Main (ej. 192.168.1.15): ")
    
    # 2. Actualizar el archivo .env
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        print(f"[*] Actualizando {env_path}...")
        with open(env_path, "r") as f:
            lines = f.readlines()
        
        with open(env_path, "w") as f:
            for line in lines:
                if line.startswith("MAIN_SERVER_IP="):
                    f.write(f"MAIN_SERVER_IP={main_server_ip}\n")
                elif line.startswith("SURICATA_SENSOR_IP="):
                    f.write(f"SURICATA_SENSOR_IP={local_ip}\n")
                else:
                    f.write(line)
    
    # 3. Configurar suricata.yaml
    suricata_yaml = os.path.join(os.path.dirname(__file__), "..", "suricata", "suricata.yaml")
    if os.path.exists(suricata_yaml):
        print(f"[*] Configurando {suricata_yaml}...")
        with open(suricata_yaml, "r") as f:
            content = f.read()
        
        # Ajustar HOME_NET
        # Buscamos la línea de HOME_NET: "[192.168.0.0/16]" o similar
        pattern = r"HOME_NET: \"\[.*?\]\""
        replacement = f'HOME_NET: "[{local_ip}/32]"'
        new_content = re.sub(pattern, replacement, content)
        
        with open(suricata_yaml, "w") as f:
            f.write(new_content)
    else:
        print("Error: No se encontro el archivo suricata.yaml en su ruta esperada.")

    # 4. Asegurar directorios de logs
    log_dir = os.path.join(os.path.dirname(__file__), "..", "suricata", "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        print(f"[*] Directorio de logs creado en {log_dir}")

    print("\n[+] Configuracion completada exitosamente.")
    print(f"    - Home Net configurado para: {local_ip}")
    print(f"    - Logs se enviaran a: {main_server_ip}:5000")
    print("\nPara iniciar Suricata, use:")
    print(f"  sudo suricata -c {os.path.abspath(suricata_yaml)} -i eth0")
    print("(Reemplace eth0 por su interfaz real)")

if __name__ == "__main__":
    setup_suricata()


# .