import os

def setup_db_config():
    print("\n" + "="*45)
    print("   DB CONFIGURATOR (MySQL)")
    print("="*45)
    
    db_host = input("IP del Servidor MySQL (ej. 10.172.86.69): ")
    db_name = input("Nombre de la Base de Datos [lab_vulnerable]: ") or "lab_vulnerable"
    db_user = input("Usuario MySQL [webuser]: ") or "webuser"
    db_pass = input("Contraseña MySQL [web123]: ") or "web123"

    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    
    if os.path.exists(env_path):
        print(f"[*] Actualizando {env_path}...")
        with open(env_path, "r") as f:
            lines = f.readlines()
        
        with open(env_path, "w") as f:
            for line in lines:
                if line.startswith("DB_HOST="):
                    f.write(f"DB_HOST={db_host}\n")
                elif line.startswith("DB_NAME="):
                    f.write(f"DB_NAME={db_name}\n")
                elif line.startswith("DB_USER="):
                    f.write(f"DB_USER={db_user}\n")
                elif line.startswith("DB_PASS="):
                    f.write(f"DB_PASS={db_pass}\n")
                else:
                    f.write(line)
        print("[+] Configuración de DB guardada en el archivo .env")
    else:
        # Si no existe, lo creamos con valores básicos
        print("[!] .env no encontrado. Creando nuevo archivo...")
        with open(env_path, "w") as f:
            f.write(f"DB_HOST={db_host}\n")
            f.write(f"DB_NAME={db_name}\n")
            f.write(f"DB_USER={db_user}\n")
            f.write(f"DB_PASS={db_pass}\n")
            f.write("MAIN_SERVER_IP=192.168.1.15\n")
            f.write("MAIN_SERVER_PORT=5000\n")

    print("="*45 + "\n")

if __name__ == "__main__":
    setup_db_config()
