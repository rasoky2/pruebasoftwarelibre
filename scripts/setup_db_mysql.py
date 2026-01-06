import os
import sys
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
    if not config:
        print("[!] No se encontró configuration.json para sincronizar con Firebase.")
        return
    
    url = f"{config['databaseURL']}/infrastructure.json"
    try:
        response = requests.patch(url, json=data)
        if response.status_code == 200:
            print("[OK] Configuración sincronizada en la nube (Firebase).")
        else:
            print(f"[!] Error al sincronizar con Firebase: {response.status_code}")
    except Exception as e:
        print(f"[!] Fallo de conexión con Firebase: {e}")

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
    if db_host in ["127.0.0.1", "localhost"] or db_host == subprocess.check_output(["hostname", "-I"]).decode().split()[0]:
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

    # Actualizar .env
    env_updates = {
        "DB_HOST": db_host,
        "DB_NAME": db_name,
        "DB_USER": db_user,
        "DB_PASS": db_pass
    }
    
    # Actualizar .env
    from setup_inventory import update_env
    update_env(env_updates)

    # Sincronizar con Firebase
    firebase_data = {
        "mysql": {
            "host": db_host,
            "database": db_name,
            "user": db_user,
            "password": db_pass,
            "last_update": subprocess.check_output(["date"]).decode().strip()
        }
    }
    sync_to_firebase(firebase_data)

    print("="*45 + "\n")

if __name__ == "__main__":
    setup_db_config()
