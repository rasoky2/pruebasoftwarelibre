import os
import sys
import socket
import subprocess
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

def update_env(updates):
    """
    Actualiza el archivo .env con las claves proporcionadas.
    Esta es la ÚNICA función que debe modificar el .env.
    """
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    env_data = {}
    
    # Cargar datos actuales si existe
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env_data[k.strip()] = v.strip()
    
    # Aplicar actualizaciones
    env_data.update(updates)
    
    # Guardar de nuevo
    with open(env_path, "w") as f:
        for k, v in env_data.items():
            f.write(f"{k}={v}\n")
    print("[+] Archivo .env actualizado.")

def check_package_installed(package_name):
    try:
        result = subprocess.run(["dpkg", "-l", package_name], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def install_ldap_server():
    """Instala OpenLDAP Server"""
    print("\n[*] Instalando OpenLDAP Server...")
    
    packages = ["slapd", "ldap-utils"]
    
    for pkg in packages:
        if check_package_installed(pkg):
            print(f"[OK] {pkg} ya está instalado.")
        else:
            try:
                subprocess.run(["sudo", "apt", "update"], check=True)
                subprocess.run(["sudo", "DEBIAN_FRONTEND=noninteractive", "apt", "install", "-y", pkg], check=True)
                print(f"[OK] {pkg} instalado.")
            except Exception as e:
                print(f"[!] Error instalando {pkg}: {e}")
                return False
    
    return True

def configure_ldap_domain(domain, org_name, admin_password):
    """Configura el dominio LDAP"""
    print(f"\n[*] Configurando dominio LDAP: {domain}")
    
    # Reconfigurar slapd con los nuevos parámetros
    debconf_config = f"""
slapd slapd/internal/generated_adminpw password {admin_password}
slapd slapd/internal/adminpw password {admin_password}
slapd slapd/password2 password {admin_password}
slapd slapd/password1 password {admin_password}
slapd slapd/dump_database_destdir string /var/backups/slapd-VERSION
slapd slapd/domain string {domain}
slapd shared/organization string {org_name}
slapd slapd/backend string MDB
slapd slapd/purge_database boolean true
slapd slapd/move_old_database boolean true
slapd slapd/allow_ldap_v2 boolean false
slapd slapd/no_configuration boolean false
"""
    
    try:
        # Escribir configuración debconf
        process = subprocess.Popen(["sudo", "debconf-set-selections"], 
                                  stdin=subprocess.PIPE, text=True)
        process.communicate(input=debconf_config)
        
        # Reconfigurar slapd
        subprocess.run(["sudo", "dpkg-reconfigure", "-f", "noninteractive", "slapd"], check=True)
        print("[OK] Dominio LDAP configurado.")
        return True
    except Exception as e:
        print(f"[!] Error configurando dominio: {e}")
        return False

def create_ldap_user(domain, username, password, admin_password):
    """Crea un usuario en LDAP"""
    print(f"\n[*] Creando usuario LDAP: {username}")
    
    # Convertir dominio a formato DN (ej: example.com -> dc=example,dc=com)
    dc_parts = domain.split(".")
    base_dn = ",".join([f"dc={part}" for part in dc_parts])
    
    # LDIF para crear la unidad organizativa de usuarios
    ou_ldif = f"""
dn: ou=users,{base_dn}
objectClass: organizationalUnit
ou: users
"""
    
    # LDIF para crear el usuario
    user_ldif = f"""
dn: uid={username},ou=users,{base_dn}
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
uid: {username}
sn: {username.capitalize()}
givenName: {username.capitalize()}
cn: {username.capitalize()}
displayName: {username.capitalize()}
uidNumber: 10000
gidNumber: 10000
userPassword: {password}
gecos: {username.capitalize()}
loginShell: /bin/bash
homeDirectory: /home/{username}
"""
    
    try:
        # Crear OU de usuarios
        process = subprocess.Popen(
            ["sudo", "ldapadd", "-x", "-D", f"cn=admin,{base_dn}", "-w", admin_password],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout, stderr = process.communicate(input=ou_ldif)
        
        if process.returncode != 0 and "Already exists" not in stderr:
            print(f"[!] Advertencia al crear OU: {stderr}")
        
        # Crear usuario
        process = subprocess.Popen(
            ["sudo", "ldapadd", "-x", "-D", f"cn=admin,{base_dn}", "-w", admin_password],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout, stderr = process.communicate(input=user_ldif)
        
        if process.returncode == 0:
            print(f"[OK] Usuario {username} creado exitosamente.")
            return True
        elif "Already exists" in stderr:
            print(f"[OK] Usuario {username} ya existe.")
            return True
        else:
            print(f"[!] Error creando usuario: {stderr}")
            return False
            
    except Exception as e:
        print(f"[!] Error: {e}")
        return False

def test_ldap_connection(domain, username, password):
    """Prueba la conexión LDAP"""
    print(f"\n[*] Probando conexión LDAP...")
    
    dc_parts = domain.split(".")
    base_dn = ",".join([f"dc={part}" for part in dc_parts])
    user_dn = f"uid={username},ou=users,{base_dn}"
    
    try:
        result = subprocess.run(
            ["ldapwhoami", "-x", "-D", user_dn, "-w", password],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            print(f"[OK] Conexión LDAP exitosa: {result.stdout.strip()}")
            return True
        else:
            print(f"[!] Error en conexión LDAP: {result.stderr}")
            return False
    except Exception as e:
        print(f"[!] Error probando conexión: {e}")
        return False

def update_auth_ldap_php(ldap_ip, domain):
    """Actualiza auth_ldap.php con la configuración correcta"""
    php_path = os.path.join(os.path.dirname(__file__), "..", "vulnerable_app", "auth_ldap.php")
    
    if not os.path.exists(php_path):
        print(f"[!] No se encontró {php_path}")
        return False
    
    try:
        with open(php_path, "r") as f:
            content = f.read()
        
        # Actualizar IP del servidor LDAP
        content = re.sub(r'\$ldap_host\s*=\s*".*?";', f'$ldap_host = "{ldap_ip}";', content)
        
        # Actualizar base DN
        dc_parts = domain.split(".")
        base_dn = ",".join([f"dc={part}" for part in dc_parts])
        content = re.sub(r'\$base_dn\s*=\s*".*?";', f'$base_dn = "ou=users,{base_dn}";', content)
        
        with open(php_path, "w") as f:
            f.write(content)
        
        print("[+] auth_ldap.php actualizado.")
        return True
    except Exception as e:
        print(f"[!] Error actualizando auth_ldap.php: {e}")
        return False

def setup_ldap():
    print("\n" + "="*60)
    print("   CONFIGURACIÓN DE LDAP SERVER (Main Server)")
    print("="*60)
    
    local_ip = get_local_ip()
    print(f"\n[*] IP detectada: {local_ip}")
    
    # Preguntar si desea instalar LDAP
    if input("\n¿Desea instalar OpenLDAP Server? (s/N): ").lower() == 's':
        if not install_ldap_server():
            print("[!] Error en la instalación. Abortando.")
            sys.exit(1)
    
    # Configuración del dominio
    print("\n" + "-"*60)
    print("CONFIGURACIÓN DEL DOMINIO LDAP")
    print("-"*60)
    
    domain = input("Dominio LDAP [example.com]: ") or "example.com"
    org_name = input("Nombre de la Organización [Example Corp]: ") or "Example Corp"
    admin_password = input("Contraseña del Admin LDAP [admin123]: ") or "admin123"
    
    # Configurar dominio
    if input(f"\n¿Configurar dominio {domain}? (s/N): ").lower() == 's':
        configure_ldap_domain(domain, org_name, admin_password)
    
    # Crear usuarios
    print("\n" + "-"*60)
    print("CREACIÓN DE USUARIOS LDAP")
    print("-"*60)
    
    users_to_create = []
    
    while True:
        username = input("\nNombre de usuario (Enter para terminar): ").strip()
        if not username:
            break
        
        password = input(f"Contraseña para {username} [user123]: ") or "user123"
        users_to_create.append((username, password))
    
    # Si no se ingresaron usuarios, crear uno por defecto
    if not users_to_create:
        print("\n[*] Creando usuario por defecto: denys")
        users_to_create.append(("denys", "denys123"))
    
    # Crear los usuarios
    for username, password in users_to_create:
        create_ldap_user(domain, username, password, admin_password)
    
    # Probar conexión con el primer usuario
    if users_to_create:
        test_username, test_password = users_to_create[0]
        test_ldap_connection(domain, test_username, test_password)
    
    # Actualizar .env
    update_env({
        "LDAP_IP": local_ip,
        "ADMIN_IP": local_ip,
        "LDAP_DOMAIN": domain,
        "LDAP_ADMIN_PASSWORD": admin_password
    })
    
    # Actualizar auth_ldap.php
    update_auth_ldap_php(local_ip, domain)
    
    # Resumen final
    print("\n" + "="*60)
    print("   ¡CONFIGURACIÓN DE LDAP COMPLETADA!")
    print("="*60)
    print(f"\nServidor LDAP: {local_ip}")
    print(f"Dominio: {domain}")
    print(f"Organización: {org_name}")
    print(f"\nUsuarios creados:")
    for username, _ in users_to_create:
        print(f"  - {username}")
    
    print("\n" + "-"*60)
    print("PRÓXIMOS PASOS:")
    print("-"*60)
    print("1. Verifica que slapd esté corriendo:")
    print("   sudo systemctl status slapd")
    print("\n2. Prueba la autenticación desde la web:")
    print(f"   http://<IP_NGINX>/index.php")
    print("\n3. Inicia el Dashboard:")
    print("   cd server_main && python3 main.py")
    print("="*60 + "\n")

if __name__ == "__main__":
    setup_ldap()
