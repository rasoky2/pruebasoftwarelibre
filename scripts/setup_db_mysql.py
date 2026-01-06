import os
import sys
import subprocess
import json
import requests
import re
import socket
import threading

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception: return "127.0.0.1"

def check_package_installed(package_name):
    try:
        result = subprocess.run(["dpkg", "-l", package_name], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def install_mysql():
    if check_package_installed("mysql-server"):
        print("[OK] MySQL Server ya está instalado.")
        return
    print("\n[*] Instalando MySQL Server...")
    try:
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "-y", "install", "mysql-server"], check=True)
        print("[OK] MySQL Server instalado.")
    except Exception as e:
        print(f"[!] Error al instalar MySQL: {e}")

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
    print("[*] Configurando Suricata para monitorear esta máquina...")
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

def check_db_health(user, password, host, database):
    """Verifica si la base de datos está activa"""
    try:
        # Usar el comando mysql directamente para evitar dependencias extras de python-mysql
        cmd = f"mysql -u{user} -p{password} -h{host} -e 'SELECT 1;' {database}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def run_health_server(config):
    """Inicia un servidor Flask minimalista para reportar el estado de la DB"""
    try:
        from flask import Flask, Response
    except ImportError:
        print("[*] Instalando Flask para el Health Server...")
        subprocess.run([sys.executable, "-m", "pip", "install", "flask"], check=True)
        from flask import Flask, Response

    app = Flask(__name__)

    @app.route('/')
    def status():
        is_healthy = check_db_health(
            config['DB_USER'], 
            config['DB_PASS'], 
            config['DB_HOST'], 
            config['DB_NAME']
        )
        status_text = "DATABASE STATUS: ONLINE" if is_healthy else "DATABASE STATUS: OFFLINE"
        return Response(status_text, mimetype='text/plain')

    local_ip = get_local_ip()
    print(f"\n{Colors_OKGREEN}[*] Health Server iniciado en http://{local_ip}:5001{Colors_ENDC}")
    print("[*] Presiona Ctrl+C para detener el monitor.")
    app.run(host='0.0.0.0', port=5001, debug=False)

# Definir colores para consistencia
Colors_OKGREEN = '\033[92m'
Colors_FAIL = '\033[91m'
Colors_WARNING = '\033[93m'
Colors_OKBLUE = '\033[94m'
Colors_ENDC = '\033[0m'

def setup_db_config():
    print("\n" + "="*50)
    print("   DB & SECURITY SETUP (MySQL + Suricata)")
    print("="*50)
    
    # 1. MySQL
    if input("¿Instalar MySQL Server? (s/N): ").lower() == 's':
        install_mysql()

    db_host = input("IP Servidor MySQL [127.0.0.1]: ") or "127.0.0.1"
    db_name = input("Nombre de la DB [lab_vulnerable]: ") or "lab_vulnerable"
    db_user = input("Usuario [webuser]: ") or "webuser"
    db_pass = input("Password [web123]: ") or "web123"

    local_ip = get_local_ip()
    if db_host in ["127.0.0.1", "localhost", local_ip]:
        sql_cmd = f"CREATE DATABASE IF NOT EXISTS {db_name}; " \
                  f"CREATE USER IF NOT EXISTS '{db_user}'@'%' IDENTIFIED BY '{db_pass}'; " \
                  f"GRANT ALL PRIVILEGES ON {db_name}.* TO '{db_user}'@'%'; " \
                  f"FLUSH PRIVILEGES;"
        subprocess.run(["sudo", "mysql", "-e", sql_cmd], check=True)
        print("[OK] DB local configurada.")

    # 2. Suricata
    main_server_ip = input(f"IP Servidor Main (Dashboard) [{local_ip}]: ") or local_ip
    
    if input("¿Instalar y Configurar Suricata IDS? (s/N): ").lower() == 's':
        install_suricata()
        configure_suricata(main_server_ip)
        
        # Configurar Shipper para enviar datos al puerto 5000
        print(f"[*] Configurando reenvío de alertas a http://{main_server_ip}:5000")
        from setup_inventory import update_config_php
        update_config_php({
            "DB_HOST": db_host,
            "DB_NAME": db_name,
            "DB_USER": db_user,
            "DB_PASS": db_pass,
            "MAIN_SERVER_IP": main_server_ip,
            "MAIN_SERVER_PORT": "5000"
        })
    
    print("\n" + "="*50)
    print("   ¡CONFIGURACIÓN COMPLETADA!")
    print("="*50)

    # 3. Health Server
    if input("\n¿Desea iniciar el Servidor de Estado (Health Server) en el puerto 5001? (s/N): ").lower() == 's':
        config = {
            'DB_USER': db_user,
            'DB_PASS': db_pass,
            'DB_HOST': db_host,
            'DB_NAME': db_name
        }
        run_health_server(config)

if __name__ == "__main__":
    setup_db_config()
