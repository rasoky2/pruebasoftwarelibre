from flask import Flask, request, jsonify, render_template
import subprocess
import os
import platform
import socket
import json
from datetime import datetime
from dotenv import load_dotenv, set_key

app = Flask(__name__)

# Rutas y Estados
env_path = os.path.join(os.path.dirname(__file__), '.env')
logs_storage = []

# Estado de salud de los sensores
sensors_health = {
    "db": {"status": "OFFLINE", "last_seen": None, "ip": ""},
    "nginx": {"status": "OFFLINE", "last_seen": None, "ip": ""}
}

def load_config():
    if not os.path.exists(env_path):
        # Crear .env con valores por defecto
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/get-latest', methods=['GET'])
def get_latest_logs():
    global logs_storage
    latest = list(logs_storage)
    logs_storage = [] 
    
    # También enviamos el estado de salud de los sensores
    return jsonify({
        "logs": latest,
        "health": sensors_health
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
