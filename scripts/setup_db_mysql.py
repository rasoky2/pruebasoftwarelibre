import os
import sys
import subprocess
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

def restart_mysql():
    print("\n[*] Reiniciando servicio MySQL...")
    try:
        subprocess.run(["sudo", "systemctl", "restart", "mysql"], check=True)
        print("[OK] MySQL reiniciado correctamente.")
        return True
    except Exception as e:
        print(f"[!] Error al reiniciar MySQL: {e}")
        return False

def check_db_health(user, password, host, database):
    """Verifica si la base de datos está activa"""
    try:
        cmd = f"mysql -u{user} -p{password} -h{host} -e 'SELECT 1;' {database}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def setup_db_config():
    print("\n" + "="*50)
    print("   DB & SECURITY SETUP (MySQL)")
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
                  f"CREATE USER IF NOT EXISTS '{db_user}'@'localhost' IDENTIFIED BY '{db_pass}'; " \
                  f"CREATE USER IF NOT EXISTS '{db_user}'@'127.0.0.1' IDENTIFIED BY '{db_pass}'; " \
                  f"GRANT ALL PRIVILEGES ON {db_name}.* TO '{db_user}'@'%'; " \
                  f"GRANT ALL PRIVILEGES ON {db_name}.* TO '{db_user}'@'localhost'; " \
                  f"GRANT ALL PRIVILEGES ON {db_name}.* TO '{db_user}'@'127.0.0.1'; " \
                  f"ALTER USER '{db_user}'@'%' IDENTIFIED WITH mysql_native_password BY '{db_pass}'; " \
                  f"FLUSH PRIVILEGES;"
        try:
            subprocess.run(["sudo", "mysql", "-e", sql_cmd], check=True)
            print("[OK] DB local configurada con soporte para Interbloqueo LDAP.")
        except Exception as e:
            print(f"[!] Error configurando MySQL: {e}")

    # 2. Reiniciar MySQL para aplicar cambios
    restart_mysql()

    # 3. Actualizar .env (ÚNICA FUENTE DE VERDAD)
    from setup_inventory import update_env
    update_env({
        "DB_IP": db_host,
        "DB_NAME": db_name,
        "DB_USER": db_user,
        "DB_PASS": db_pass
    })
    
    # 4. Verificación Final de la Base de Datos
    print("\n[*] Realizando verificación final de la base de datos...")
    is_healthy = check_db_health(db_user, db_pass, db_host, db_name)
    
    print("\n" + "="*50)
    if is_healthy:
        print("   ¡CONFIGURACIÓN COMPLETADA Y VERIFICADA!")
        print("   Estado de MySQL: ONLINE")
    else:
        print("   ¡CONFIGURACIÓN COMPLETADA CON ADVERTENCIAS!")
        print("   Estado de MySQL: OFFLINE (Verifica credenciales o red)")
    print("="*50 + "\n")

if __name__ == "__main__":
    setup_db_config()
