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

def test_socket(ip, port, timeout=2):
    """Prueba conectividad a nivel de red (TCP)"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, port))
        s.close()
        return True
    except Exception:
        return False

def check_package_installed(package_name):
    try:
        result = subprocess.run(["dpkg", "-l", package_name], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def install_nginx():
    if check_package_installed("nginx"):
        print("[OK] Nginx ya está instalado.")
    else:
        print("\n[*] Instalando Nginx...")
        try:
            subprocess.run(["sudo", "apt", "update"], check=True)
            subprocess.run(["sudo", "apt", "install", "-y", "nginx"], check=True)
        except Exception as e:
            print(f"[!] Error al instalar Nginx: {e}")
    
    # Asegurar extensión LDAP para PHP
    install_php_ldap()

def install_php_ldap():
    print("\n[*] Verificando extensión PHP LDAP...")
    
    # Detectar versión de PHP instalada
    try:
        php_v = subprocess.run(["php", "-r", "echo PHP_MAJOR_VERSION.'.'.PHP_MINOR_VERSION;"], capture_output=True, text=True).stdout.strip()
        pkg_name = f"php{php_v}-ldap"
        
        if check_package_installed(pkg_name):
            print(f"[OK] Extensión {pkg_name} ya está instalada.")
            return
            
        print(f"[*] Instalando extensión {pkg_name}...")
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "-y", pkg_name], check=True)
        
        # Reiniciar PHP-FPM para aplicar cambios
        fpm_service = f"php{php_v}-fpm"
        subprocess.run(["sudo", "systemctl", "restart", fpm_service], check=False)
        subprocess.run(["sudo", "systemctl", "restart", "nginx"], check=True)
        print(f"[OK] Extensión LDAP instalada y servicios reiniciados.")
        
    except Exception as e:
        print(f"[!] No se pudo instalar php-ldap automáticamente: {e}")
        print("[!] Por favor, ejecuta: sudo apt install php-ldap")

def install_suricata():
    if check_package_installed("suricata"):
        print("[OK] Suricata ya está instalado.")
        return
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
        
        # Instalar el servicio PHP backend automáticamente
        print("\n[*] Configurando servicio PHP backend...")
        php_service_src = os.path.join(os.path.dirname(os.path.dirname(__file__)), "nginx", "php-backend.service")
        php_service_dst = "/etc/systemd/system/php-backend.service"
        
        if os.path.exists(php_service_src):
            try:
                subprocess.run(["sudo", "cp", php_service_src, php_service_dst], check=True)
                subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
                subprocess.run(["sudo", "systemctl", "enable", "php-backend"], check=True)
                subprocess.run(["sudo", "systemctl", "restart", "php-backend"], check=True)
                print("[OK] Servicio PHP backend instalado y activo (127.0.0.1:8000)")
                
                # Verificar estado
                result = subprocess.run(["systemctl", "is-active", "php-backend"], 
                                      capture_output=True, text=True)
                if result.stdout.strip() == "active":
                    print("[OK] Servicio php-backend verificado: ACTIVO")
                else:
                    print("[!] Advertencia: El servicio php-backend no está activo")
                    print("    Ejecuta: sudo journalctl -u php-backend -n 50")
            except Exception as e:
                print(f"[!] Error instalando php-backend: {e}")
                print("    Puedes iniciarlo manualmente con:")
                print("    cd /var/www/html/pruebasoftwarelibre/vulnerable_app")
                print("    php -S 127.0.0.1:8000")
        else:
            print(f"[!] No se encontró {php_service_src}")
            print("    Inicia PHP manualmente:")
            print("    cd /var/www/html/pruebasoftwarelibre/vulnerable_app")
            print("    php -S 127.0.0.1:8000")


        if os.path.exists("nginx_temp.conf"): os.remove("nginx_temp.conf")

        # Configuración de Seguridad (Suricata)
        main_server_ip = input(f"IP Servidor Main (Dashboard) [{local_ip}]: ") or local_ip
        if input("\n¿Desea instalar y configurar Suricata IDS en este nodo? (s/N): ").lower() == 's':
            install_suricata()
            configure_suricata(main_server_ip)
            
            from setup_inventory import update_env
            update_env({
                "ADMIN_IP": main_server_ip,
                "NGINX_IP": local_ip
            })
            print("[OK] Suricata y .env configurados.")
            
            # Instalar el servicio log-shipper automáticamente
            print("\n[*] Configurando Log Shipper para enviar alertas al Dashboard...")
            shipper_service_src = os.path.join(os.path.dirname(os.path.dirname(__file__)), "suricata", "log-shipper.service")
            shipper_service_dst = "/etc/systemd/system/log-shipper.service"
            
            if os.path.exists(shipper_service_src):
                try:
                    subprocess.run(["sudo", "cp", shipper_service_src, shipper_service_dst], check=True)
                    subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
                    subprocess.run(["sudo", "systemctl", "enable", "log-shipper"], check=True)
                    subprocess.run(["sudo", "systemctl", "start", "log-shipper"], check=True)
                    print(f"[OK] Log Shipper instalado y activo (enviando a {main_server_ip}:5000)")
                    
                    # Verificar estado
                    result = subprocess.run(["systemctl", "is-active", "log-shipper"], 
                                          capture_output=True, text=True)
                    if result.stdout.strip() == "active":
                        print("[OK] Servicio log-shipper verificado: ACTIVO")
                    else:
                        print("[!] Advertencia: El servicio log-shipper no está activo")
                        print("    Ejecuta: sudo journalctl -u log-shipper -n 50")
                except Exception as e:
                    print(f"[!] Error instalando log-shipper: {e}")
                    print("    Puedes instalarlo manualmente con:")
                    print(f"    sudo cp {shipper_service_src} {shipper_service_dst}")
                    print("    sudo systemctl daemon-reload && sudo systemctl enable --now log-shipper")
            else:
                print(f"[!] No se encontró {shipper_service_src}")
                print("    El log-shipper debe instalarse manualmente.")


        # 4. Actualización opcional de DB (config.php)
        if input("\n¿Desea actualizar la IP y credenciales de la Base de Datos? (s/N): ").lower() == 's':
            # Cargar sugerencias de .env para consistencia
            env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
            suggested_db_ip = "127.0.0.1"
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    for line in f:
                        if "DB_IP=" in line:
                            suggested_db_ip = line.split('=')[1].strip()

        # 5. Verificación de conectividad con el Dashboard (Admin)
        print(f"\n[*] Verificando conectividad con el Dashboard en {main_server_ip}:5000...")
        if test_socket(main_server_ip, 5000):
            print(f"[OK] Conexión con Dashboard EXITOSA (Admin está recibiendo logs).")
        else:
            print(f"[!] ADVERTENCIA: No se pudo conectar con el Dashboard en {main_server_ip}:5000.")
            print(f"    Verifica que el script main.py esté corriendo en el Servidor Admin.")

        # 6. Forzar reinicio de servicios para aplicar cambios del .env
        print("\n[*] Reiniciando servicios para aplicar configuración final...")
        subprocess.run(["sudo", "systemctl", "daemon-reload"], check=False)
        subprocess.run(["sudo", "systemctl", "restart", "php-backend"], check=False)
        if check_package_installed("suricata"):
            subprocess.run(["sudo", "systemctl", "restart", "log-shipper"], check=False)
        print("[OK] Servicios actualizados.")

            db_host = input(f"IP del Servidor MySQL [{suggested_db_ip}]: ") or suggested_db_ip
            db_name = input("Nombre de la DB [lab_vulnerable]: ") or "lab_vulnerable"
            db_user = input("Usuario MySQL [webuser]: ") or "webuser"
            db_pass = input("Contraseña MySQL [web123]: ") or "web123"
            
            from setup_inventory import update_env
            update_env({
                "DB_IP": db_host,
                "DB_NAME": db_name,
                "DB_USER": db_user,
                "DB_PASS": db_pass
            })
            print("[OK] Configuración de Base de Datos actualizada en .env.")

        # 5. Configuración de Servidor LDAP
        if input("\n¿Desea configurar la conexión al Servidor LDAP? (s/N): ").lower() == 's':
            # Cargar sugerencias de .env
            env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
            suggested_ldap_ip = main_server_ip  # Por defecto, mismo que el Dashboard
            suggested_ldap_domain = "example.com"
            
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    for line in f:
                        if "LDAP_IP=" in line:
                            suggested_ldap_ip = line.split('=')[1].strip()
                        elif "LDAP_DOMAIN=" in line:
                            suggested_ldap_domain = line.split('=')[1].strip()
            
            ldap_ip = input(f"IP del Servidor LDAP [{suggested_ldap_ip}]: ") or suggested_ldap_ip
            ldap_domain = input(f"Dominio LDAP [{suggested_ldap_domain}]: ") or suggested_ldap_domain
            
            # Actualizar .env
            from setup_inventory import update_env
            update_env({
                "LDAP_IP": ldap_ip,
                "LDAP_DOMAIN": ldap_domain
            })
            
            # Actualizar auth_ldap.php
            auth_ldap_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                         "vulnerable_app", "auth_ldap.php")
            
            if os.path.exists(auth_ldap_path):
                try:
                    with open(auth_ldap_path, "r") as f:
                        content = f.read()
                    
                    # Actualizar IP del servidor LDAP
                    content = re.sub(r'\$ldap_host\s*=\s*".*?";', 
                                   f'$ldap_host = "{ldap_ip}";', content)
                    
                    # Actualizar base DN
                    dc_parts = ldap_domain.split(".")
                    base_dn = ",".join([f"dc={part}" for part in dc_parts])
                    content = re.sub(r'\$base_dn\s*=\s*".*?";', 
                                   f'$base_dn = "ou=users,{base_dn}";', content)
                    
                    with open(auth_ldap_path, "w") as f:
                        f.write(content)
                    
                    print(f"[OK] auth_ldap.php actualizado:")
                    print(f"     Servidor LDAP: {ldap_ip}")
                    print(f"     Base DN: ou=users,{base_dn}")
                except Exception as e:
                    print(f"[!] Error actualizando auth_ldap.php: {e}")
            else:
                print(f"[!] No se encontró {auth_ldap_path}")
            
            print("[OK] Configuración de LDAP actualizada en .env y auth_ldap.php.")

        
        run_system_diagnostics(backend_ip, backend_port)

    except Exception as e:
        print(f"[!] Error: {e}")
    print("="*45 + "\n")

def run_system_diagnostics(backend_ip, backend_port):
    print("\n" + "-"*45)
    print("   DIAGNÓSTICO FINAL DE INFRAESTRUCTURA")
    print("-"*45)
    
    # 1. Probar Socket del Backend
    print(f"[*] Probando Backend PHP ({backend_ip}:{backend_port})... ", end="", flush=True)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        if s.connect_ex((backend_ip, int(backend_port))) == 0:
            print("\033[92m[ONLINE]\033[0m")
        else:
            print("\033[91m[OFFLINE]\033[0m (¿Inició 'php -S ...'?)")
        s.close()
    except:
        print("\033[91m[ERROR]\033[0m")

    # 2. Probar Nginx + PHP + DB (End-to-End)
    url_test = "http://localhost/test.php"
    print(f"[*] Probando acceso Web + Base de Datos... ", end="", flush=True)
    try:
        # Usamos localhost para probar Nginx localmente
        response = requests.get(url_test, timeout=5)
        if response.status_code == 200:
            if "✅ CONECTADO" in response.text:
                print("\033[92m[TODO OK]\033[0m Nginx -> PHP -> DB funcionando.")
            else:
                print("\033[93m[ALERTA]\033[0m PHP responde, pero la DB falla.")
        else:
            print(f"\033[91m[FAIL]\033[0m HTTP {response.status_code}")
    except:
        print("\033[91m[SIN RESPUESTA]\033[0m Nginx no responde o test.php no existe.")
    
    print("-"*45 + "\n")

if __name__ == "__main__":
    setup_nginx()
