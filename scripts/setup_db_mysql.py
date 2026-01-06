import os
import sys
import subprocess
import json
import requests
import re
import socket

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception: return "127.0.0.1"

def install_mysql():
    print("\n[*] Instalando MySQL Server...")
    try:
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "-y", "mysql-server"], check=True)
        print("[OK] MySQL Server instalado.")
    except Exception as e:
        print(f"[!] Error al instalar MySQL: {e}")

def install_suricata():
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
    print(f"   Próximo paso: Ejecutar log_shipper.php para enviar datos.")
    print("="*50 + "\n")

if __name__ == "__main__":
    setup_db_config()
