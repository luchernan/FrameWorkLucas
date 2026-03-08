# Educational Pentesting Framework

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![Platform](https://img.shields.io/badge/Platform-Kali%20Linux-557C94?logo=linux)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

> **An interactive, educational CLI pentesting framework for controlled lab environments.**  
> Designed for CTF players, cybersecurity students, and red team learners.

---

## What is this?

`edu_pentest_framework.py` is a fully interactive Python script that **orchestrates industry-standard penetration testing tools** through a structured, phase-based menu — while explaining what each tool does and why you use it.

It's not just a script. It's a **learning companion** for ethical hacking labs.

```
   ███████╗██████╗ ██╗   ██╗ ██████╗ █████╗ ████████╗██╗ ██╗   ██╗███████╗
   ██╔════╝██╔══██╗██║   ██║██╔════╝██╔══██╗╚══██╔══╝██║ ██║   ██║██╔════╝
   █████╗  ██║  ██║██║   ██║██║     ███████║   ██║   ██║ ██║   ██║█████╗
   ██╔══╝  ██║  ██║██║   ██║██║     ██╔══██║   ██║   ██║ ╚██╗ ██╔╝██╔══╝
   ███████╗██████╔╝╚██████╔╝╚██████╗██║  ██║   ██║   ██║  ╚████╔╝ ███████╗
   ╚══════╝╚═════╝  ╚═════╝  ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝   ╚═══╝  ╚══════╝
  ════════════  Educational Pentesting Framework  v2.0  |  Linux Only  ════
```

---

## Features

### Workflow
The framework follows a real-world OSCP-style pentesting workflow:

| Phase | Tools |
|-------|-------|
| **Recon & Discovery** | ARP-Scan, Ping TTL fingerprint, Nmap (2-phase) |
| **Web Enumeration** | Gobuster, FFuF, Nikto, WPScan, SQLMap, Nuclei |
| **Exploitation** | SearchSploit, Hydra brute force |
| **Post-exploitation** | Netcat listener, HTTP payload server |
| **Reporting** | Auto-generated HTML dashboard |

### UX Highlights
- **Animated spinner** with elapsed time for long-running tools (Gobuster, Nuclei, FFuF, Nikto)
- **Clean result tables** after each tool — no raw dumps
- **Educational panels** explaining each tool before execution
- **Auto HTML report** with port table, Nuclei CVE findings, FFuF subdomains, and raw logs
- **VHost auto-detection** from Nmap certificate/redirect parsing
- **Nmap scan speed picker** — fast+noisy (T4) vs slow+stealthy (T2)
- **IP/hostname validation** before any scan

---

## Requirements

### System (Kali Linux / Debian)
```bash
sudo ./install.sh
```

Or manually:
```bash
sudo apt install nmap gobuster nikto ffuf wpscan hydra sqlmap enum4linux exploitdb netcat-traditional arp-scan nuclei
```

### Python
```bash
pip install -r requirements.txt
```

---

## Usage

```bash
# Clone / enter directory
cd edu_pentest_framework/

# Install all dependencies
sudo ./install.sh

# Run
sudo python3 edu_pentest_framework.py
```

### Quick workflow example
```
[MENU PRINCIPAL]
  [2] Configure Target manually
  > 10.0.2.7

[PANEL DE ATAQUE -- 10.0.2.7]
  [2] Nmap scan  → Select: 1 (Fast) or 2 (Stealth)
  [4] Gobuster   → auto spinner → table of found paths
  [8] Nuclei     → auto spinner → CVE severity table
  [9] Nikto      → auto spinner → list of findings
 [14] HTML Report → opens browser
```

---

## Output Structure

Each target creates an organized workspace:

```
workspace_10_0_2_7/
├── nmap/
│   ├── nmap.xml
│   └── escaneo_principal.txt
├── web/
│   ├── gobuster_directorios.txt
│   ├── nuclei.json
│   ├── nikto_resultados.txt
│   └── ffuf_<domain>.json
├── exploits/
│   └── hydra_ssh_bruteforce.txt
└── report_10_0_2_7_<timestamp>.html
```

---

## HTML Report

Auto-generated after any scan session:

- **Stats dashboard** — open ports, Nuclei findings, FFuF results
- **Port table** from Nmap XML (service, version, state)
- **CVE table** from Nuclei JSON (severity color-coded)
- **Subdomain table** from FFuF
- **Raw log dumps** from every other tool

---

## Legal Disclaimer

> ⚠️ **This tool is designed EXCLUSIVELY for educational use in controlled environments:**  
> CTFs, personal VMs, HackTheBox, TryHackMe, or authorized lab networks.  
>  
> **Using this tool against systems you do not own or have explicit written permission to test is illegal** and may result in criminal prosecution.  
>  
> The author assumes no liability for misuse.

---

## Tested On
- Kali Linux 2024.x
- Metasploitable 2/3
- HackTheBox / TryHackMe machines
- Custom DVWA Docker setups

---

## License

MIT — see [LICENSE](LICENSE)
