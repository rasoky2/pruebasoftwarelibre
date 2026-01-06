from flask import Flask, request, jsonify, render_template
import subprocess
import os
import platform
import socket
import json
from datetime import datetime

app = Flask(__name__)

# Almacenamiento temporal y persistencia de configuración
logs_storage = []
config_path = os.path.join(os.path.dirname(__file__), 'config.json')

def load_config():
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except: pass
    return {
        "db_ip": "192.168.1.57",
        "nginx_ip": "192.168.1.56",
        "last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def save_config(config):
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)

current_config = load_config()

# Colores para la terminal (ANSI)
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def get_network_devices():
    """Escanea dispositivos en la red local usando ARP (Funciona en Linux)"""
    devices = []
    try:
        # Intentamos usar arp -a (común en Linux/Windows)
        output = subprocess.check_output(["arp", "-a"]).decode('utf-8')
        for line in output.split('\n'):
            if '(' in line and ')' in line: # Formato típico de Linux
                ip = line.split('(')[1].split(')')[0]
                mac = line.split('at ')[1].split(' ')[0] if 'at ' in line else "Desconocida"
                devices.append({"ip": ip, "mac": mac})
    except: pass
    return devices

def get_host_ip():
    """Obtiene la IP local del servidor"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # No necesita conectarse realmente para obtener la IP
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

# The block_ip function was removed as per the provided edit.

@app.route('/')
def index():
    """Renderiza el Dashboard Web Shadcn Light"""
    return render_template('index.html')

@app.route('/api/get-latest', methods=['GET'])
def get_latest_logs():
    """Endpoint para que el frontend obtenga logs nuevos"""
    global logs_storage
    latest = list(logs_storage)
    logs_storage = [] # Limpiamos después de enviar
    return jsonify(latest)

@app.route('/api/config', methods=['GET', 'POST'])
def manage_config():
    global current_config
    if request.method == 'POST':
        data = request.json
        current_config['db_ip'] = data.get('db_ip', current_config['db_ip'])
        current_config['nginx_ip'] = data.get('nginx_ip', current_config['nginx_ip'])
        current_config['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        save_config(current_config)
        return jsonify({"status": "success", "config": current_config})
    return jsonify(current_config)

@app.route('/', methods=['POST'])
def receive_suricata_log():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error"}), 400

        # Identificar la IP del Sensor que nos envía el log
        sensor_ip = request.remote_addr
        data['sensor_source'] = sensor_ip

        # Almacenamos el log para la web
        logs_storage.append(data)

        # Si es una alerta, mostrar en consola también
        if data.get('event_type') == 'alert':
            alert = data.get('alert', {})
            src_ip = data.get('src_ip', 'Desconocida')
            signature = alert.get('signature', 'Firma desconocida')
            
            print(f"\n{Colors.BOLD}{Colors.FAIL}[!] ALERTA DESDE SENSOR {sensor_ip} [!]{Colors.ENDC}")
            print(f"{Colors.OKBLUE}Ataque:{Colors.ENDC} {signature} | {Colors.OKBLUE}Atacante:{Colors.ENDC} {src_ip}")
        
        # Si son estadísticas de recursos del sensor
        elif data.get('event_type') == 'stats':
            stats = data.get('stats', {})
            uptime = stats.get('uptime', 0)
            print(f"{Colors.OKGREEN}[H] Salud Sensor {sensor_ip}:{Colors.ENDC} Uptime: {uptime}s | Log recibido OK")
            
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print(r"      ____             _cata Monitor")
    print(r"     / ___| _   _ _ __(_) ___ __ _ _ __ __ _")
    print(r"    \___ \| | | | '__| |/ __/ _` | '__/ _` |")
    print(r"     ___) | |_| | |  | | (_| (_| | | | (_| |")
    print(r"    |____/ \__,_|_|  |_|\___\__,_|_|  \__,_|")
    print(f"{Colors.ENDC}")

    # Mostrar la IP local del servidor
    host_ip = get_host_ip()
    print(f"{Colors.BOLD}{Colors.OKBLUE}[ℹ] Panel Web disponible en: {Colors.WARNING}http://{host_ip}:5000{Colors.ENDC}")

    print(f"\n{Colors.OKGREEN}Servidor Main y Dashboard iniciados...{Colors.ENDC}")
    print(f"{Colors.OKBLUE}Configuración actual:{Colors.ENDC} DB: {current_config['db_ip']} | Nginx: {current_config['nginx_ip']}")
    app.run(host='0.0.0.0', port=5000)
