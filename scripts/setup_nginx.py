import os
import sys
import socket

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
    
    local_ip = get_local_ip()
    print(f"[*] IP detectada en este equipo: {local_ip}")
    
    backend_ip = input("Ingrese IP del Servidor PHP (Backend) [127.0.0.1]: ") or "127.0.0.1"
    backend_port = input("Ingrese Puerto del Backend [8000]: ") or "8000"
    
    server_name = input(f"Ingrese dominio o IP pública/local [{local_ip}]: ") or local_ip

    nginx_config = f"""server {{
    listen 80;
    server_name {server_name};

    # Configuración de Logs para Suricata
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    location / {{
        proxy_pass http://{backend_ip}:{backend_port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout para apps vulnerables lentas
        proxy_read_timeout 90;
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

        os.remove("nginx_temp.conf")

    except Exception as e:
        print(f"[!] Error: {e}")
    print("="*45 + "\n")

if __name__ == "__main__":
    setup_nginx()
