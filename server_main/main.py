from flask import Flask, request, jsonify
import json
from datetime import datetime
import subprocess
import os
import platform

app = Flask(__name__)

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
    print(f"\n{Colors.OKBLUE}[*] Escaneando dispositivos en la red...{Colors.ENDC}")
    devices = []
    try:
        # Intentamos usar arp -a (común en Linux/Windows)
        output = subprocess.check_output(["arp", "-a"]).decode('utf-8')
        for line in output.split('\n'):
            if '(' in line and ')' in line: # Formato típico de Linux
                ip = line.split('(')[1].split(')')[0]
                mac = line.split('at ')[1].split(' ')[0] if 'at ' in line else "Desconocida"
                devices.append({"ip": ip, "mac": mac})
    except Exception as e:
        print(f"{Colors.FAIL}Error al escanear red: {e}{Colors.ENDC}")
    return devices

def block_ip(ip):
    """Ejecuta el bloqueo del atacante usando iptables"""
    if platform.system() != "Linux":
        print(f"{Colors.WARNING}[!] Bloqueo cancelado: iptables solo disponible en Linux.{Colors.ENDC}")
        return False
    
    try:
        print(f"{Colors.WARNING}[*] Aplicando bloqueo a {ip}...{Colors.ENDC}")
        # Comando: sudo iptables -A INPUT -s IP -j DROP
        cmd = ["sudo", "iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"]
        subprocess.run(cmd, check=True)
        print(f"{Colors.OKGREEN}[+] IP {ip} bloqueada exitosamente.{Colors.ENDC}")
        return True
    except subprocess.CalledProcessError:
        print(f"{Colors.FAIL}[-] Error: Asegúrate de ejecutar con sudo y tener iptables instalado.{Colors.ENDC}")
        return False

@app.route('/', methods=['POST'])
def receive_suricata_log():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error"}), 400

        if data.get('event_type') == 'alert':
            alert = data.get('alert', {})
            src_ip = data.get('src_ip', 'Desconocida')
            signature = alert.get('signature', 'Firma desconocida')
            severity = alert.get('severity', 0)

            print(f"\n{Colors.BOLD}{Colors.FAIL}[!] ALERTA DETECTADA: {signature} [!]{Colors.ENDC}")
            print(f"{Colors.OKBLUE}Origen:{Colors.ENDC} {Colors.WARNING}{src_ip}{Colors.ENDC}")
            
            # Lógica de respuesta activa para Inyección SQL
            if "SQL Injection" in signature or severity >= 3:
                print(f"\n{Colors.BOLD}{Colors.FAIL}!!! AMENAZA CRÍTICA DETECTADA !!!{Colors.ENDC}")
                print(f"{Colors.UNDERLINE}Acción sugerida:{Colors.ENDC}")
                print(f"Para bloquear al atacante usa: {Colors.BOLD}sudo iptables -A INPUT -s {src_ip} -j DROP{Colors.ENDC}")
                
                # Ofrecer bloqueo (Simulado o automático si es crítico)
                if severity >= 3:
                    print(f"{Colors.WARNING}>> Se recomienda ejecutar el bloqueo inmediato de {src_ip}.{Colors.ENDC}")
                    # block_ip(src_ip) # Descomentar para bloqueo automático
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

    # Mostrar dispositivos al inicio
    devs = get_network_devices()
    if devs:
        print(f"{Colors.OKGREEN}Dispositivos encontrados:{Colors.ENDC}")
        for d in devs:
            print(f"  • {d['ip']} [{d['mac']}]")
    else:
        print(f"{Colors.WARNING}No se detectaron otros dispositivos en la caché ARP.{Colors.ENDC}")

    print(f"\n{Colors.OKGREEN}Servidor Main escuchando en puerto 5000...{Colors.ENDC}")
    app.run(host='0.0.0.0', port=5000)
