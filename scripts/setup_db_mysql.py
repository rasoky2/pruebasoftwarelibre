import os
import sys
import subprocess
import json
import requests

def install_mysql():
    print("\n[*] Instalando MySQL Server...")
    try:
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "-y", "mysql-server"], check=True)
        print("[OK] MySQL Server instalado.")
    except Exception as e:
        print(f"[!] Error al instalar MySQL: {e}")

def setup_db_config():
    print("\n" + "="*45)
    print("   DB CONFIGURATOR & INSTALLER (MySQL)")
    print("="*45)
    
    install_choice = input("¿Desea instalar MySQL Server ahora? (s/N): ").lower()
    if install_choice == 's':
        install_mysql()

    db_host = input("IP del Servidor MySQL (esta máquina o remota) [10.172.86.69]: ") or "10.172.86.69"
    db_name = input("Nombre de la Base de Datos [lab_vulnerable]: ") or "lab_vulnerable"
    db_user = input("Usuario MySQL [webuser]: ") or "webuser"
    db_pass = input("Contraseña MySQL [web123]: ") or "web123"

    # Configurar privilegios en MySQL local si el host es esta máquina o localhost
    hostname_ip = subprocess.check_output(["hostname", "-I"]).decode().split()[0]
    if db_host in ["127.0.0.1", "localhost", hostname_ip]:
        print("[*] Configurando privilegios para webuser en la DB local...")
        sql_cmd = f"CREATE DATABASE IF NOT EXISTS {db_name}; " \
                  f"CREATE USER IF NOT EXISTS '{db_user}'@'%' IDENTIFIED BY '{db_pass}'; " \
                  f"GRANT ALL PRIVILEGES ON {db_name}.* TO '{db_user}'@'%'; " \
                  f"FLUSH PRIVILEGES;"
        try:
            subprocess.run(["sudo", "mysql", "-e", sql_cmd], check=True)
            print("[OK] Base de Datos y privilegios configurados.")
        except Exception as e:
            print(f"[!] Error al configurar MySQL local: {e}")

    # Actualizar config.php
    config_updates = {
        "DB_HOST": db_host,
        "DB_NAME": db_name,
        "DB_USER": db_user,
        "DB_PASS": db_pass
    }
    
    from setup_inventory import update_config_php
    update_config_php(config_updates)

    print("="*45 + "\n")

if __name__ == "__main__":
    setup_db_config()
