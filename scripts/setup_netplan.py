import os
import sys
import socket
import yaml

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None

def setup_netplan():
    if os.geteuid() != 0:
        print("[!] Este script requiere sudo.")
        sys.exit(1)

    print("\n" + "="*45)
    print("   AUTOMATIC NETPLAN CONFIGURATOR")
    print("="*45)
    
    current_ip = get_local_ip()
    if current_ip:
        print(f"[*] IP actual del sistema: {current_ip}")
    
    interface = input("Interfaz de red (ej. ens33, eth0): ")
    new_ip = input(f"Nueva IP estática con CIDR (ej. {current_ip or '192.168.1.56'}/24): ")
    gateway = input("Gateway (ej. 192.168.1.1): ")
    dns = input("DNS (comas para varios) [8.8.8.8, 1.1.1.1]: ") or "8.8.8.8, 1.1.1.1"

    config = {
        "network": {
            "version": 2,
            "renderer": "networkd",
            "ethernets": {
                interface: {
                    "addresses": [new_ip],
                    "routes": [{"to": "default", "via": gateway}],
                    "nameservers": {"addresses": [d.strip() for d in dns.split(",")]}
                }
            }
        }
    }

    netplan_dir = "/etc/netplan/"
    # Tomar el primer archivo yaml o crear uno nuevo
    yamls = [f for f in os.listdir(netplan_dir) if f.endswith(".yaml")]
    target_file = os.path.join(netplan_dir, yamls[0] if yamls else "01-netcfg.yaml")

    print(f"[*] Guardando cambios en {target_file}...")
    
    try:
        with open("netplan_temp.yaml", "w") as f:
            yaml.dump(config, f, default_flow_style=False)
        
        os.system(f"cp netplan_temp.yaml {target_file}")
        print("[*] Aplicando cambios (esto podría desconectar su sesión SSH)...")
        os.system("netplan apply")
        print("[+] RED CONFIGURADA EXITOSAMENTE")
        os.remove("netplan_temp.yaml")
    except Exception as e:
        print(f"[!] Error: {e}")
    
    print("="*45 + "\n")

if __name__ == "__main__":
    setup_netplan()
