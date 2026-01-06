import os
import sys
import socket
import subprocess
import json
import requests

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
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def setup_nginx():
    if os.geteuid() != 0:
        print("[!] Este script requiere privilegios de superusuario (sudo).")
        sys.exit(1)

    print("\n" + "="*45)
    print("   AUTOMATIC NGINX PROXY SETUP")
    print("="*45)
    
    print("\n--- Seleccione el Rol de este Servidor ---")
    print("1) Nodo Borde (Nginx + Suricata)")
    print("2) Servidor de Base de Datos (MySQL)")
    role_choice = input("Seleccione una opción [1]: ") or "1"
    
    if role_choice != "1":
        print("[!] Cancelado: Nginx no debe instalarse en el servidor de Base de Datos.")
        sys.exit(0)

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
        
        os.system(f"cp nginx_temp.conf {available_path}")
        
        if not os.path.exists(enabled_path):
            os.system(f"ln -s {available_path} {enabled_path}")
        
        # Eliminar el default si existe para evitar conflictos en puerto 80
        if os.path.exists("/etc/nginx/sites-enabled/default"):
            print("[*] Desactivando configuración 'default' de Nginx...")
            os.system("rm /etc/nginx/sites-enabled/default")

        print("[*] Verificando sintaxis de Nginx...")
        if os.system("nginx -t") == 0:
            os.system("systemctl restart nginx")
            print(f"\n[+] NGINX CONFIGURADO EN PUERTO 80")
            print(f"    Acceso: http://{server_name}")
        else:
            print("\n[!] Error en la sintaxis de Nginx. Revise la consola.")

        if os.path.exists("nginx_temp.conf"): os.remove("nginx_temp.conf")
        
        # Sincronizar con Firebase
        sync_to_firebase({
            "nginx": {
                "host": local_ip,
                "backend": f"{backend_ip}:{backend_port}",
                "status": "online"
            }
        })

    except Exception as e:
        print(f"[!] Error: {e}")
    print("="*45 + "\n")

if __name__ == "__main__":
    setup_nginx()
