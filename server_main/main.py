from flask import Flask, request, jsonify, render_template
import subprocess
import os
import platform
import socket
import json
from datetime import datetime
from dotenv import load_dotenv, set_key

app = Flask(__name__)

# Colores para la terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def get_host_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

# Rutas y Estados
env_path = os.path.join(os.path.dirname(__file__), '.env')
logs_storage = []
banned_ips = [] # Lista de IPs bloqueadas por el Admin

# Estado de salud de los sensores
sensors_health = {
    "db": {"status": "OFFLINE", "last_seen": None, "ip": ""},
    "nginx": {"status": "OFFLINE", "last_seen": None, "ip": ""}
}

def load_config():
    if not os.path.exists(env_path):
        with open(env_path, 'w') as f:
            f.write("DB_IP=127.0.0.1\nNGINX_IP=127.0.0.1\n")
    
    load_dotenv(env_path)
    return {
        "db_ip": os.getenv("DB_IP", "127.0.0.1"),
        "nginx_ip": os.getenv("NGINX_IP", "127.0.0.1")
    }

def save_config(config):
    set_key(env_path, "DB_IP", config['db_ip'])
    set_key(env_path, "NGINX_IP", config['nginx_ip'])

current_config = load_config()

# --- API DE BLOQUEO (FIREWALL REMOTO) ---

# --- API DE BLOQUEO (FIREWALL LOCAL) ---

@app.route('/api/ban', methods=['POST'])
def ban_ip():
    """Bloquea una IP en el firewall local usando iptables"""
    data = request.json
    ip_to_ban = data.get('ip')
    
    if not ip_to_ban:
        return jsonify({"status": "error", "message": "IP no proporcionada"}), 400

    if ip_to_ban not in banned_ips:
        try:
            # Comando para bloquear en Linux (iptables)
            subprocess.run(f"sudo iptables -I INPUT -s {ip_to_ban} -j DROP", shell=True, check=True)
            banned_ips.append(ip_to_ban)
            print(f"\n{Colors.FAIL}[!] IP BLOQUEADA MEDIANTE IPTABLES: {ip_to_ban}{Colors.ENDC}")
            return jsonify({"status": "success", "message": f"IP {ip_to_ban} bloqueada con éxito."})
        except Exception as e:
            return jsonify({"status": "error", "message": f"Error al ejecutar iptables: {str(e)}"}), 500
            
    return jsonify({"status": "error", "message": "IP ya está en la lista negra."}), 400

@app.route('/api/banned-list', methods=['GET'])
def get_banned_list():
    return jsonify({"banned_ips": banned_ips})

# --- ENDPOINTS ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/get-latest', methods=['GET'])
def get_latest_logs():
    global logs_storage
    latest = list(logs_storage)
    logs_storage = [] 
    
    return jsonify({
        "logs": latest,
        "health": sensors_health,
        "banned": banned_ips
    })

@app.route('/api/config', methods=['GET', 'POST'])
def manage_config():
    global current_config
    if request.method == 'POST':
        data = request.json
        current_config['db_ip'] = data.get('db_ip', current_config['db_ip'])
        current_config['nginx_ip'] = data.get('nginx_ip', current_config['nginx_ip'])
        save_config(current_config)
        return jsonify({"status": "success", "config": current_config})
    
    config_with_health = dict(current_config)
    config_with_health['health'] = sensors_health
    return jsonify(config_with_health)

@app.route('/', methods=['POST'])
def receive_suricata_log():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error"}), 400

        sensor_ip = request.remote_addr
        data['sensor_source'] = sensor_ip

        # Identificar y Actualizar Salud del Sensor
        # Verificamos si la IP coincide con la configurada en .env
        if sensor_ip == current_config['db_ip']:
            sensors_health['db']['status'] = "ONLINE"
            sensors_health['db']['last_seen'] = datetime.now().strftime('%H:%M:%S')
            sensors_health['db']['ip'] = sensor_ip
        elif sensor_ip == current_config['nginx_ip']:
            sensors_health['nginx']['status'] = "ONLINE"
            sensors_health['nginx']['last_seen'] = datetime.now().strftime('%H:%M:%S')
            sensors_health['nginx']['ip'] = sensor_ip

        logs_storage.append(data)

        if data.get('event_type') == 'alert':
            alert = data.get('alert', {})
            print(f"\n{Colors.FAIL}[!] ALERTA DESDE {sensor_ip} [!]{Colors.ENDC}")
            print(f"Ataque: {alert.get('signature')} | Atacante: {data.get('src_ip')}")
        
        elif data.get('event_type') == 'stats':
            print(f"{Colors.OKGREEN}[H] Heartbeat de {sensor_ip} recibido.{Colors.ENDC}")
            
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    host_ip = get_host_ip()
    print(f"\n{Colors.OKBLUE}[ℹ] Security Dashboard iniciado en http://{host_ip}:5000{Colors.ENDC}")
    print(f"{Colors.OKBLUE}[ℹ] Configuración (.env): DB={current_config['db_ip']} | Nginx={current_config['nginx_ip']}{Colors.ENDC}\n")
    app.run(host='0.0.0.0', port=5000)
