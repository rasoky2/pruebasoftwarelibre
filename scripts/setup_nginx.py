import os
import sys
import socket
import subprocess
import json
import requests

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

def install_suricata():
    print("\n[*] Instalando Suricata (Sistema de Detección de Intrusos)...")
    try:
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "-y", "suricata"], check=True)
        print("[OK] Suricata instalado.")
    except Exception as e:
        print(f"[!] Error al instalar Suricata: {e}")

def configure_suricata(main_server_ip):
    print("[*] Configurando Suricata en Nodo de Borde...")
    local_ip = get_local_ip()
    suricata_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "suricata"))
    suricata_yaml = os.path.join(suricata_dir, "suricata.yaml")
    local_rules = os.path.join(suricata_dir, "rules", "local.rules")

    if os.path.exists(suricata_yaml):
        with open(suricata_yaml, "r") as f: content = f.read()
        
        # HOME_NET y Reglas
        content = re.sub(r'HOME_NET: "\[.*?\]"', f'HOME_NET: "[{local_ip}/32]"', content)
        if "rule-files:" in content:
            if "local.rules" not in content:
                content = content.replace("rule-files:", f"rule-files:\n  - {local_rules}")
        
        with open(suricata_yaml, "w") as f: f.write(content)
        print(f"[OK] Suricata configurado (HOME_NET: {local_ip})")
    else:
        print("[!] Advertencia: No se encontró suricata.yaml base.")

def setup_nginx():
    if os.geteuid() != 0:
        print("[!] Este script requiere privilegios de superusuario (sudo).")
        sys.exit(1)

    print("\n" + "="*45)
    print("   AUTOMATIC NGINX PROXY SETUP")
    print("="*45)
    
    local_ip = get_local_ip()
    print(f"[*] IP detectada en equipo Nginx: {local_ip}")
    
    backend_ip = input("Ingrese IP del Servidor PHP (Backend) [127.0.0.1]: ") or "127.0.0.1"
    backend_port = input("Ingrese Puerto del Backend [8000]: ") or "8000"
    
    server_name = input(f"Ingrese dominio o IP pública/local [{local_ip}]: ") or local_ip

    nginx_config = f"""server {{
    listen 80;
    server_name {server_name};

    # Configuración de Error 502 Persoalizado
    error_page 502 /error_502.html;
    location = /error_502.html {{
        root {os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "vulnerable_app"))};
        internal;
    }}

    location / {{
        proxy_pass http://{backend_ip}:{backend_port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Manejar fallos del backend
        proxy_intercept_errors on;
    }}
}}
"""

    conf_name = "vulnerable_app"
    available_path = f"/etc/nginx/sites-available/{conf_name}"
    enabled_path = f"/etc/nginx/sites-enabled/{conf_name}"

    try:
        print("[*] Escribiendo configuración en Nginx...")
        with open("nginx_temp.conf", "w") as f:
            f.write(nginx_config)
        
        subprocess.run(["sudo", "cp", "nginx_temp.conf", available_path], check=True)
        
        if not os.path.exists(enabled_path):
            subprocess.run(["sudo", "ln", "-s", available_path, enabled_path], check=True)
        
        # Eliminar el default si existe para evitar conflictos en puerto 80
        if os.path.exists("/etc/nginx/sites-enabled/default"):
            print("[*] Desactivando configuración 'default' de Nginx...")
            subprocess.run(["sudo", "rm", "/etc/nginx/sites-enabled/default"], check=True)

        print("[*] Verificando sintaxis de Nginx...")
        if subprocess.run(["sudo", "nginx", "-t"]).returncode == 0:
            subprocess.run(["sudo", "systemctl", "restart", "nginx"], check=True)
            print(f"\n[+] NGINX CONFIGURADO EN PUERTO 80")
            print(f"    Acceso: http://{server_name}")
        else:
            print("\n[!] Error en la sintaxis de Nginx. Revise la consola.")

        if os.path.exists("nginx_temp.conf"): os.remove("nginx_temp.conf")

        # Configuración de Seguridad (Suricata)
        main_server_ip = input(f"IP Servidor Main (Dashboard) [{local_ip}]: ") or local_ip
        if input("\n¿Desea instalar y configurar Suricata IDS en este nodo? (s/N): ").lower() == 's':
            install_suricata()
            configure_suricata(main_server_ip)
            
            print(f"[*] Sincronizando IP del Dashboard en config.php...")
            from setup_inventory import update_config_php
            update_config_php({
                "MAIN_SERVER_IP": main_server_ip,
                "MAIN_SERVER_PORT": "5000",
                "SURICATA_SENSOR_IP": local_ip
            })
            print(f"[OK] Shipper configurado para enviar a http://{main_server_ip}:5000")
        
    except Exception as e:
        print(f"[!] Error: {e}")
    print("="*45 + "\n")

if __name__ == "__main__":
    setup_nginx()
