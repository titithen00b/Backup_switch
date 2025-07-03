import sys
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from netmiko import ConnectHandler
import logging
from datetime import datetime
import os
import threading
import platform
import subprocess
import ipaddress
from dotenv import load_dotenv
import logging
import re
#logging.basicConfig(filename='netmiko_debug.log', level=logging.DEBUG)

def get_exe_dir():
    if getattr(sys, 'frozen', False):
        # Executable PyInstaller
        return os.path.dirname(sys.executable)
    else:
        # En mode script Python
        return os.path.dirname(os.path.abspath(__file__))

env_path = os.path.join(get_exe_dir(), "backup.env")
load_dotenv(dotenv_path=env_path)


# === IPs complètes ===
ips = []
for subnet in range(1, 14):
    for i in range(240, 244):
        ips.append(f"10.{subnet}.2.{i}")
ips += [f"192.168.49.{i}" for i in range(231, 240)]
ips.append("192.168.40.231")
ips.append("192.168.40.232")

device_types = ['cisco_ios', 'hp_procurve', 'aruba_os', 'dell_force10', 'cisco_s300', 'linux']

credentials_by_os = {
    'cisco_ios':     (os.getenv('CISCO_USER'), os.getenv('CISCO_PASS')),
    'hp_procurve':   (os.getenv('ARUBA_USER'), os.getenv('ARUBA_PASS')),
    'aruba_os':      (os.getenv('HPE_USER'), os.getenv('HPE_PASS')),
    'dell_force10':  (os.getenv('DELL_USER'), os.getenv('DELL_PASS')),
    'cisco_s300':    (os.getenv('CISCO_USER'), os.getenv('CISCO_PASS')),
    'linux':         (os.getenv('GENERIC_USER'), os.getenv('GENERIC_PASS')),
}

stop_requested = False
filtered_ips = []

def ping(host):
    param = "-n" if platform.system().lower() == "windows" else "-c"
    command = ["ping", param, "1", host]
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        output = result.stdout.lower()
        return "ttl=" in output
    except Exception:
        return False

def expand_ip_ranges(ip_input):
    result = set()
    parts = ip_input.split(",")
    for part in parts:
        part = part.strip()
        if "-" in part:
            try:
                base = ".".join(part.split(".")[:-1])
                start, end = map(int, part.split(".")[-1].split("-"))
                for i in range(start, end + 1):
                    result.add(f"{base}.{i}")
            except Exception:
                continue
        else:
            try:
                ip = str(ipaddress.ip_address(part))
                result.add(ip)
            except:
                continue
    return sorted(result)

def apply_filter(output_area):
    global filtered_ips
    raw = ip_filter_var.get()
    if not raw.strip():
        filtered_ips = ips[:]
        output_area.insert(tk.END, "\n🔁 Aucun filtre : toutes les IPs seront traitées.\n")
    else:
        filtered_ips = [ip for ip in expand_ip_ranges(raw) if ip in ips]
        output_area.insert(tk.END, f"\n🎯 {len(filtered_ips)} IPs sélectionnées pour traitement.\n")
    output_area.see(tk.END)

# def import_ip_file():
#     file = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
#     if not file:
#         return
#     with open(file, "r") as f:
#         content = f.read().strip()
#         ip_filter_var.set(content)

def stop_backup():
    global stop_requested
    stop_requested = True
    output.insert(tk.END, "\n⛔ Arrêt demandé. Le processus va se terminer après l'équipement en cours...\n")
    output.see(tk.END)

def clear_output():
    output.delete("1.0", tk.END)

def quit_app():
    root.destroy()

def backup_configs(save_path, output_area, target_ips):
    global stop_requested
    stop_requested = False
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    backup_dir = os.path.join(save_path, f"backup_{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)
    log_path = os.path.join(backup_dir, "backup_log.csv")

    progress_bar["maximum"] = len(target_ips)
    progress_bar["value"] = 0

    with open(log_path, "w") as log_file:
        log_file.write("IP,OS,Status,File\n")

        for ip in target_ips:
            if stop_requested:
                output_area.insert(tk.END, f"\n⛔ Arrêt du traitement demandé après {ip}\n")
                output_area.see(tk.END)
                break

            output_area.insert(tk.END, f"\n🔍 Ping {ip}...\n")
            output_area.see(tk.END)

            if not ping(ip):
                output_area.insert(tk.END, f"❌ {ip} injoignable (ping KO)\n")
                log_file.write(f"{ip},N/A,Unreachable,Ping failed\n")
                progress_bar["value"] += 1
                root.update_idletasks()
                continue

            output_area.insert(tk.END, f"✅ {ip} répond. Connexion en cours...\n")
            output_area.see(tk.END)
            connected = False

            for dev_type in device_types:
                creds = credentials_by_os.get(dev_type)
                if not creds:
                    continue
                user, pwd = creds

                if verbose_mode.get():
                    output_area.insert(tk.END, f"→ Test {dev_type} avec {user}...\n")
                    output_area.see(tk.END)

                try:
                    device = {
                        'device_type': dev_type,
                        'host': ip,
                        'username': user,
                        'password': pwd,
                        'fast_cli': False,
                        'conn_timeout': 10,
                        'timeout': 10,
                    }

                    if dev_type == 'dell_force10':
                        enable_pass = os.getenv('DELL_ENABLE_PASS')
                        if not enable_pass:
                            raise Exception("DELL_ENABLE_PASS non défini dans le fichier .env")

                        device['secret'] = enable_pass
                        conn = ConnectHandler(**device)

                        try:
                            conn.enable()
                            prompt = conn.find_prompt()
                            output_area.insert(tk.END, f"🔍 Prompt détecté : {prompt}\n")
                            output_area.see(tk.END)

                            commands_dell = [
                                "show running-config",
                                "show running-config all",
                                "show startup-config",
                                "show config"
                            ]

                            success = False
                            for cmd in commands_dell:
                                try:
                                    config = conn.send_command(
                                        cmd,
                                        delay_factor=2,
                                        read_timeout=60,
                                        cmd_verify=False
                                    )
                                    if "% Invalid input detected" not in config and config.strip():
                                        success = True
                                        if verbose_mode.get():
                                            output_area.insert(tk.END, f"✅ Commande Dell réussie : {cmd}\n")
                                            output_area.see(tk.END)
                                        break
                                except Exception as cmd_error:
                                    output_area.insert(tk.END, f"⚠️ Commande '{cmd}' échouée : {cmd_error}\n")
                                    output_area.see(tk.END)

                            if not success:
                                output_area.insert(tk.END, "❌ Aucune commande Dell n’a fonctionné.\n")
                                output_area.see(tk.END)
                                conn.disconnect()
                                continue

                        except Exception as e:
                            output_area.insert(tk.END, f"❌ Erreur Dell : {str(e)}\n")
                            output_area.see(tk.END)
                            continue

                    else:
                        conn = ConnectHandler(**device)
                        config = conn.send_command("show running-config", delay_factor=2)


                    filename = f"{backup_dir}/{ip.replace('.', '_')}_{dev_type}.txt"
                    with open(filename, "w") as f:
                        f.write(config)
                    output_area.insert(tk.END, f"✅ Sauvegarde OK → {filename}\n")
                    output_area.see(tk.END)
                    log_file.write(f"{ip},{dev_type},Success,{filename}\n")
                    conn.disconnect()
                    connected = True
                    break

                except Exception as e:
                    if verbose_mode.get():
                        output_area.insert(tk.END, f"⚠️  {dev_type} échoué : {str(e).splitlines()[0]}\n")
                        output_area.see(tk.END)
                    continue


            if not connected:
                output_area.insert(tk.END, f"❌ SSH échoué sur {ip}\n")
                output_area.see(tk.END)
                log_file.write(f"{ip},Unknown,SSH failed,No config saved\n")

            progress_bar["value"] += 1
            root.update_idletasks()

    start_button.config(state="normal")
    # import_button.config(state="normal")
    filter_button.config(state="normal")
    clear_button.config(state="normal")

    if not stop_requested:
        messagebox.showinfo("Fin", f"Sauvegarde terminée. Log :\n{log_path}")
    else:
        messagebox.showinfo("Arrêté", "Sauvegarde interrompue par l'utilisateur.")

def start_backup():
    path = path_var.get()
    if not path:
        messagebox.showerror("Erreur", "Veuillez choisir un dossier de sauvegarde.")
        return
    targets = filtered_ips if filtered_ips else ips

    start_button.config(state="disabled")
    # import_button.config(state="disabled")
    filter_button.config(state="disabled")
    clear_button.config(state="disabled")

    threading.Thread(target=backup_configs, args=(path, output, targets), daemon=True).start()

# === GUI ===
root = tk.Tk()
root.title("Sauvegarde Switchs - Complète")
root.geometry("900x750")
root.option_add("*Font", ("Segoe UI", 9))

tk.Label(root, text="Dossier de sauvegarde").grid(row=0, column=0, sticky='e')
path_var = tk.StringVar()
tk.Entry(root, textvariable=path_var, width=60).grid(row=0, column=1)
tk.Button(root, text="📁 Parcourir", command=lambda: path_var.set(filedialog.askdirectory())).grid(row=0, column=2)

start_button = tk.Button(root, text="▶ Lancer", bg="#b2fab4", command=start_backup)
start_button.grid(row=1, column=0, pady=5)
stop_button = tk.Button(root, text="🛑 Stop", bg="#ffb3b3", command=stop_backup)
stop_button.grid(row=1, column=1)
clear_button = tk.Button(root, text="🧹 Effacer", command=clear_output)
clear_button.grid(row=1, column=2)

tk.Label(root, text="IPs/plages (ex: 10.1.2.240-243,192.168.49.231)").grid(row=2, column=0, columnspan=3)
ip_filter_var = tk.StringVar()
tk.Entry(root, textvariable=ip_filter_var, width=70).grid(row=3, column=0, columnspan=2, padx=5, pady=3)
# import_button = tk.Button(root, text="📤 Importer IPs", command=import_ip_file)
# import_button.grid(row=3, column=2, sticky='ew', padx=5)

filter_button = tk.Button(root, text="🎯 Filtrer", command=lambda: apply_filter(output))
filter_button.grid(row=4, column=2, sticky='e')
verbose_mode = tk.BooleanVar(value=False)
tk.Checkbutton(root, text="Afficher les détails", variable=verbose_mode).grid(row=4, column=0, sticky="w", padx=10)

output = scrolledtext.ScrolledText(root, width=108, height=30)
output.grid(row=5, column=0, columnspan=3, padx=10, pady=10)
progress_bar = ttk.Progressbar(root, orient="horizontal", length=750, mode="determinate")
progress_bar.grid(row=6, column=0, columnspan=2, pady=10, padx=10, sticky='w')

tk.Button(root, text="🚪 Quitter", command=quit_app, bg="#e0e0e0").grid(row=6, column=2, sticky="e", padx=10)

root.mainloop()
