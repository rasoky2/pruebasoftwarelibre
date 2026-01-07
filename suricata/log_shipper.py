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
    """Obtiene métricas de CPU y Memoria (arreglado para no dar 0)"""
    try:
        # psutil necesita un intervalo para calcular el cambio de CPU
        cpu = psutil.cpu_percent(interval=1.0)
        ram = psutil.virtual_memory().percent
        return {"cpu": cpu, "ram": ram}
    except:
        return {"cpu": 0, "ram": 0}

def send_heartbeat_loop(url, local_ip, sensor_type):
    """Bucle infinito de envío de latidos con métricas reales"""
    print(f"[*] Hilo de Heartbeat iniciado para {sensor_type}...")
    while True:
        try:
            stats = get_system_stats()
            payload = {
                "sensor_type": sensor_type,
                "status": "ONLINE",
                "timestamp": time.time(),
                "metrics": stats,
                "ip": local_ip
            }
            # Enviamos el latido con las métricas
            response = requests.post(url, json=payload, timeout=5)
            # print(f"[DEBUG] Heartbeat enviado: {stats}") # Opcional para debug
        except Exception as e:
            # print(f"[!] Error en Heartbeat: {e}")
            pass
        time.sleep(10)

def ship_suricata_logs():
    # Intentar cargar .env desde múltiples ubicaciones posibles
    possible_paths = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")), # Desde suricata/..
        "/var/www/html/pruebasoftwarelibre/.env", # Ruta absoluta estándar
        os.path.join(os.getcwd(), ".env") # Ruta actual
    ]
    
    env_loaded = False
    for env_path in possible_paths:
        if os.path.exists(env_path):
            load_dotenv(env_path)
            print(f"[*] Configuración cargada desde: {env_path}")
            env_loaded = True
            break
            
    if not env_loaded:
        print("[!] ADVERTENCIA: No se encontró archivo .env. Usando valores por defecto.")
    
    admin_ip = os.getenv("ADMIN_IP", "127.0.0.1")
    sensor_type = os.getenv("SENSOR_TYPE", "nginx") # 'nginx' o 'database'
    dashboard_url = f"http://{admin_ip}:5000/api/heartbeat"
    local_ip = get_local_ip()
    
    print(f"\n" + "="*50)
    print(f"   LOG SHIPPER DINÁMICO [{sensor_type.upper()}]")
    print(f"   Reportando a: {dashboard_url}")
    print(f"   IP Local: {local_ip}")
    print("="*50 + "\n")
    
    # INICIAR HILO DE MÉTRICAS (Heartbeat)
    # Esto asegura que las métricas de CPU/RAM se envíen cada 10s independientemente de los logs
    heartbeat_thread = threading.Thread(target=send_heartbeat_loop, args=(dashboard_url, local_ip, sensor_type), daemon=True)
    heartbeat_thread.start()
    
    # TAIL DE LOGS DE SURICATA (Alertas)
    if not os.path.exists(log_file):
        print(f"[!] Archivo de log {log_file} no encontrado. Creando...")
        try: 
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            open(log_file, 'a').close()
        except: pass

    # Usar tail -F para manejar rotación de logs de forma robusta
    proc = subprocess.Popen(['tail', '-F', log_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    while True:
        line = proc.stdout.readline()
        if not line:
            time.sleep(0.1)
            continue
            
        try:
            log_data = json.loads(line)
            if log_data.get('event_type') == 'alert':
                # Enriquecer log con identidad del sensor y sus métricas actuales
                log_data['sensor_type'] = sensor_type
                log_data['sensor_source'] = local_ip
                # Opcional: Incluir métricas en la alerta para actualización inmediata
                log_data['metrics'] = get_system_stats()
                
                requests.post(dashboard_url, json=log_data, timeout=5)
                print(f"[ALERT] {log_data['alert']['signature']} de {log_data.get('src_ip')}")
        except:
            continue

if __name__ == "__main__":
    ship_suricata_logs()
