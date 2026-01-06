import os
import sys

def configure_nginx():
    print("--- Configuracion de Proxy Inverso Nginx ---")
    
    nginx_conf_path = "/etc/nginx/sites-available/vulnerable_app"
    nginx_enabled_path = "/etc/nginx/sites-enabled/vulnerable_app"
    
    backend_ip = input("Ingrese la IP interna del servidor PHP (ej. 127.0.0.1): ")
    backend_port = input("Ingrese el puerto del servidor PHP (ej. 8000): ")
    domain = input("Ingrese el nombre de dominio o localhost: ")

    nginx_config = f"""server {{
    listen 80;
    server_name {domain};

    location / {{
        proxy_pass http://{backend_ip}:{backend_port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""

    try:
        # Escribir configuracion localmente primero
        with open("nginx_vulnerable.conf", "w") as f:
            f.write(nginx_config)
        
        print("\nConfiguracion de Nginx generada:")
        print("-" * 30)
        print(nginx_config)
        print("-" * 30)

        confirm = input(f"¿Desea instalar esta configuracion? (s/n): ")
        if confirm.lower() == 's':
            # Escribir en sites-available
            os.system(f"sudo bash -c 'cat > {nginx_conf_path}' < nginx_vulnerable.conf")
            
            # Crear enlace simbolico si no existe
            if not os.path.exists(nginx_enabled_path):
                os.system(f"sudo ln -s {nginx_conf_path} {nginx_enabled_path}")
            
            # Probar y reiniciar nginx
            print("Probando configuracion de Nginx...")
            os.system("sudo nginx -t")
            os.system("sudo systemctl restart nginx")
            print("Nginx configurado y reiniciado correctamente.")
        else:
            print("Operacion cancelada.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Este script debe ejecutarse con privilegios de superusuario (sudo).")
        sys.exit(1)
    configure_nginx()
