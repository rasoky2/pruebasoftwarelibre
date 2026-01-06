import os
import yaml
import sys

def configure_netplan():
    print("--- Configuracion de Red (Netplan) ---")
    
    # Intentar detectar archivos netplan existentes
    netplan_dir = "/etc/netplan/"
    if not os.path.exists(netplan_dir):
        print(f"Error: No se encontro el directorio {netplan_dir}. ¿Estas en Ubuntu/Debian?")
        return

    files = [f for f in os.listdir(netplan_dir) if f.endswith(".yaml")]
    if not files:
        target_file = os.path.join(netplan_dir, "01-netcfg.yaml")
    else:
        target_file = os.path.join(netplan_dir, files[0])

    print(f"Archivo de destino: {target_file}")
    
    interface = input("Ingrese el nombre de la interfaz (ej. eth0, ens33): ")
    ip_address = input("Ingrese la IP estatica con mascara (ej. 192.168.1.56/24): ")
    gateway = input("Ingrese la IP del Gateway (ej. 192.168.1.1): ")
    dns = input("Ingrese servidores DNS (separados por coma, ej. 8.8.8.8, 1.1.1.1): ").split(",")

    config = {
        "network": {
            "version": 2,
            "renderer": "networkd",
            "ethernets": {
                interface: {
                    "addresses": [ip_address],
                    "routes": [
                        {"to": "default", "via": gateway}
                    ],
                    "nameservers": {
                        "addresses": [d.strip() for d in dns]
                    }
                }
            }
        }
    }

    try:
        with open("temp_netplan.yaml", "w") as f:
            yaml.dump(config, f, default_flow_style=False)
        
        print("\nConfiguracion generada exitosamente.")
        print("-" * 30)
        with open("temp_netplan.yaml", "r") as f:
            print(f.read())
        print("-" * 30)

        confirm = input(f"¿Desea aplicar esta configuracion en {target_file}? (s/n): ")
        if confirm.lower() == 's':
            os.system(f"sudo cp temp_netplan.yaml {target_file}")
            os.system("sudo netplan apply")
            print("Configuracion aplicada. La conexion podria reiniciarse.")
        else:
            print("Operacion cancelada. El archivo temporal es 'temp_netplan.yaml'.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Este script debe ejecutarse con privilegios de superusuario (sudo).")
        sys.exit(1)
    configure_netplan()
