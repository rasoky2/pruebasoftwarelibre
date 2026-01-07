import time
import requests
import socket
import os
from dotenv import load_dotenv
import psutil


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
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        return {"cpu": cpu, "ram": ram}
    except:
        return {"cpu": 0, "ram": 0}

def send_heartbeat():
    # Cargar .env para saber la IP del Admin
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    load_dotenv(env_path)
    
    admin_ip = os.getenv("ADMIN_IP", "127.0.0.1")
    local_ip = get_local_ip()
    url = f"http://{admin_ip}:5000/api/heartbeat"
    
    print(f"[*] Iniciando Latido de Base de Datos ({local_ip})")
    print(f"[*] Reportando a Dashboard en: {url}")
    
    while True:
        try:
            stats = get_system_stats()
            payload = {
                "status": "ONLINE",
                "sensor_type": "database",
                "timestamp": time.time(),
                "metrics": stats
            }
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                print(f"[OK] {time.strftime('%H:%M:%S')} - Latido enviado. CPU: {stats['cpu']}% RAM: {stats['ram']}%")
            else:
                print(f"[!] {time.strftime('%H:%M:%S')} - Error de respuesta: {response.status_code}")
        except Exception as e:
            print(f"[!] {time.strftime('%H:%M:%S')} - Error al conectar con Dashboard: {e}")
        
        time.sleep(10) # Enviar cada 10 segundos para mayor precisión

if __name__ == "__main__":
    send_heartbeat()
