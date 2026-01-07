import time
import requests
import socket
import os
from dotenv import load_dotenv

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
            payload = {
                "status": "ONLINE",
                "sensor_type": "database",
                "timestamp": time.time()
            }
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                print(f"[OK] {time.strftime('%H:%M:%S')} - Latido enviado correctamente.")
            else:
                print(f"[!] {time.strftime('%H:%M:%S')} - Error de respuesta: {response.status_code}")
        except Exception as e:
            print(f"[!] {time.strftime('%H:%M:%S')} - Error al conectar con Dashboard: {e}")
        
        time.sleep(30) # Enviar cada 30 segundos

if __name__ == "__main__":
    send_heartbeat()
