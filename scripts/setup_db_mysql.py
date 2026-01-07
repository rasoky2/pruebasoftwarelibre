import os
import sys
import subprocess
import socket
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

def configure_mysql_network():
    """Configura MySQL para escuchar en todas las interfaces de red"""
    print("\n[*] Configurando MySQL para aceptar conexiones de red...")
    
    config_file = "/etc/mysql/mysql.conf.d/mysqld.cnf"
    
    if not os.path.exists(config_file):
        print(f"[!] No se encontró {config_file}")
        return False
    
    try:
        # Leer el archivo
        with open(config_file, "r") as f:
            content = f.read()
        
        # Reemplazar bind-address
        # Busca tanto "bind-address" como "mysqlx-bind-address"
        content = re.sub(
            r'bind-address\s*=\s*127\.0\.0\.1',
            'bind-address = 0.0.0.0',
            content
        )
        content = re.sub(
            r'mysqlx-bind-address\s*=\s*127\.0\.0\.1',
            'mysqlx-bind-address = 0.0.0.0',
            content
        )
        
        # Escribir el archivo modificado
        with open(config_file, "w") as f:
            f.write(content)
        
        print("[OK] MySQL configurado para escuchar en 0.0.0.0")
        return True
    except Exception as e:
        print(f"[!] Error configurando MySQL: {e}")
        return False

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

def load_database_schema(db_name):
    """Carga el esquema de la base de datos desde database_setup.sql"""
    print("\n[*] Cargando esquema de la base de datos...")
    
    # Buscar el archivo database_setup.sql
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file = os.path.join(os.path.dirname(script_dir), "database_setup.sql")
    
    if os.path.exists(sql_file):
        try:
            subprocess.run(
                ["sudo", "mysql", db_name],
                stdin=open(sql_file, 'r'),
                check=True
            )
            print(f"[OK] Esquema cargado desde {sql_file}")
            return True
        except Exception as e:
            print(f"[!] Error cargando esquema: {e}")
            return False
    else:
        print(f"[!] No se encontró {sql_file}")
        print("[*] Creando tablas manualmente...")
        
        # Crear tablas manualmente si no existe el archivo
        sql_commands = """
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            price DECIMAL(10,2)
        );

        CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL,
            password VARCHAR(255) NOT NULL
        );

        INSERT INTO products (name, description, price) VALUES 
        ('Laptop Dell XPS 13', 'Ultrabook potente con pantalla táctil', 1299.99),
        ('Teclado Mecánico RGB', 'Switches Cherry MX Blue con iluminación personalizable', 89.99),
        ('Monitor LG 27 4K', 'Panel IPS con resolución 3840x2160', 449.99),
        ('Mouse Logitech MX Master 3', 'Mouse ergonómico inalámbrico de alta precisión', 99.99),
        ('Webcam Logitech C920', 'Cámara Full HD 1080p con micrófono estéreo', 79.99);

        INSERT INTO usuarios (username, password) VALUES 
        ('admin', 'admin123'),
        ('user', 'user123');
        """
        
        try:
            subprocess.run(
                ["sudo", "mysql", "-e", f"USE {db_name}; {sql_commands}"],
                check=True
            )
            print("[OK] Tablas creadas manualmente.")
            return True
        except Exception as e:
            print(f"[!] Error creando tablas: {e}")
            return False

def setup_db_config():
    print("\n" + "="*50)
    print("   DB SETUP COMPLETO (MySQL + Esquema)")
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
        # 2. Configurar MySQL para red (Escuchar en todas las interfaces)
        configure_mysql_network()
        
        # 3. Crear base de datos y usuarios con PRIVILEGIOS LIBRES (%)
        print(f"[*] Configurando privilegios libres para {db_user}...")
        sql_cmd = f"CREATE DATABASE IF NOT EXISTS {db_name}; " \
                  f"CREATE USER IF NOT EXISTS '{db_user}'@'%' IDENTIFIED BY '{db_pass}'; " \
                  f"CREATE USER IF NOT EXISTS '{db_user}'@'localhost' IDENTIFIED BY '{db_pass}'; " \
                  f"GRANT ALL PRIVILEGES ON {db_name}.* TO '{db_user}'@'%'; " \
                  f"GRANT ALL PRIVILEGES ON {db_name}.* TO '{db_user}'@'localhost'; " \
                  f"ALTER USER '{db_user}'@'%' IDENTIFIED WITH mysql_native_password BY '{db_pass}'; " \
                  f"FLUSH PRIVILEGES;"
        try:
            subprocess.run(["sudo", "mysql", "-e", sql_cmd], check=True)
            print("[OK] Base de datos y usuarios con privilegios '%' configurados.")
        except Exception as e:
            print(f"[!] Error configurando privilegios MySQL: {e}")

        # 4. Cargar esquema de la base de datos
        if input("\n¿Desea cargar el esquema de la base de datos (tablas y datos)? (s/N): ").lower() == 's':
            load_database_schema(db_name)

        # 5. Reiniciar MySQL para aplicar bind-address = 0.0.0.0
        restart_mysql()

    # 6. Actualizar .env (ÚNICA FUENTE DE VERDAD)
    from setup_inventory import update_env
    update_env({
        "DB_IP": db_host,
        "DB_NAME": db_name,
        "DB_USER": db_user,
        "DB_PASS": db_pass
    })
    
    # 7. Verificación Final de la Base de Datos
    print("\n[*] Realizando verificación final de la base de datos...")
    is_healthy = check_db_health(db_user, db_pass, db_host, db_name)
    
    print("\n" + "="*50)
    if is_healthy:
        print("   ¡CONFIGURACIÓN COMPLETADA Y VERIFICADA!")
        print("   Estado de MySQL: ONLINE")
        print(f"   Base de Datos: {db_name}")
        print(f"   Usuario: {db_user}")
        print(f"   Escuchando en: 0.0.0.0:3306")
    else:
        print("   ¡CONFIGURACIÓN COMPLETADA CON ADVERTENCIAS!")
        print("   Estado de MySQL: OFFLINE (Verifica credenciales o red)")
    print("="*50 + "\n")

if __name__ == "__main__":
    setup_db_config()
