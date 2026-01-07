import time
import json
import requests
import os
import subprocess
import socket
from dotenv import load_dotenv
import psutil
import threading

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def get_system_stats():
    """Obtiene métricas de CPU y Memoria"""
    try:
        # psutil necesita un intervalo para calcular el cambio de CPU
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory().percent
        return {"cpu": cpu, "ram": ram}
    except:
        return {"cpu": 0, "ram": 0}

def send_heartbeat_loop(url, local_ip):
    """Manda un latido cada 10s con métricas de sistema"""
    while True:
        try:
            stats = get_system_stats()
            payload = {
                "status": "ONLINE",
                "sensor_type": "nginx",
                "timestamp": time.time(),
                "metrics": stats
            }
            requests.post(url, json=payload, timeout=5)
        except:
            pass
        time.sleep(10)

def ship_suricata_logs():
    # Cargar configuración...
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    load_dotenv(env_path)
    
    admin_ip = os.getenv("ADMIN_IP", "127.0.0.1")
    dashboard_url = f"http://{admin_ip}:5000/api/heartbeat"
    log_file = "/var/log/suricata/eve.json"
    
    print(f"[*] Iniciando Shipper (Python) con Métricas de Sistema...")
    print(f"[*] Reportando a: {dashboard_url}")
    
    # Iniciar hilo de latido/métricas
    threading.Thread(target=send_heartbeat_loop, args=(dashboard_url, get_local_ip()), daemon=True).start()
    
    # Continuar con el tail de logs...
    if not os.path.exists(log_file):
        try: open(log_file, 'a').close()
        except: pass

    proc = subprocess.Popen(['tail', '-F', log_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        line = proc.stdout.readline()
        if not line:
            time.sleep(0.1)
            continue
            
        try:
            log_data = json.loads(line.decode('utf-8'))
            if log_data.get('event_type') == 'alert':
                # Enriquecer log con tipo de sensor
                log_data['sensor_type'] = 'nginx'
                requests.post(dashboard_url, json=log_data, timeout=2)
        except:
            continue

if __name__ == "__main__":
    ship_suricata_logs()
