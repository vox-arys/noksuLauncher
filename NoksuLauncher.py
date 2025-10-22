import os
import sys

if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    os.environ['TCL_LIBRARY'] = os.path.join(base_path, 'tcl', 'tcl8.6')
    os.environ['TK_LIBRARY'] = os.path.join(base_path, 'tcl', 'tk8.6')

import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
import webbrowser
import json
import requests
import time
import threading

CONFIG_FILE = "noksuLauncherConfig.json"

def browse_file(index):
    path = filedialog.askopenfilename(title="Select a Program or Shortcut")
    if path:
        entries[index].delete(0, tk.END)
        entries[index].insert(0, path)
        update_app_label(index, path)
        save_config()

def update_app_label(index, path):
    """Update the app label based on file name or Steam link."""
    if not path:
        app_labels[index].config(text="(Nothing selected)")
        return

    if path.startswith("steam://rungameid/"):
        app_labels[index].config(text="Fetching Steam name...")
        appid = path.split("/")[-1]
        # Run Steam lookup in background
        threading.Thread(target=async_steam_lookup, args=(index, appid), daemon=True).start()
        return

    name = os.path.basename(path)
    if name:
        app_labels[index].config(text=name)
    else:
        app_labels[index].config(text="(No file selected)")

def async_steam_lookup(index, appid):
    """Fetch Steam name in a separate thread and update UI."""
    app_name = get_steam_app_name(appid)
    if app_name:
        result = f"{app_name} (Steam)"
    else:
        result = f"Steam App {appid}"
    # Update UI safely from main thread
    root.after(0, lambda: app_labels[index].config(text=result))

def get_steam_app_name(appid):
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
        response = requests.get(url, timeout=3)
        data = response.json()
        if data.get(appid, {}).get("success"):
            return data[appid]["data"]["name"]
    except Exception:
        pass
    return None

def launch_selected():
    for i in range(5):
        if check_vars[i].get():
            path = entries[i].get().strip()
            if not path:
                continue
            try:
                if path.startswith("steam://"):
                    webbrowser.open(path)
                    time.sleep(3)  # Let Steam handle launch
                elif path.startswith(("http://", "https://")):
                    webbrowser.open(path)
                elif os.path.isfile(path):
                    working_dir = os.path.dirname(path) or None
                    subprocess.Popen([path], cwd=working_dir, shell=True)
                elif os.path.isdir(path):
                    os.startfile(path)
                else:
                    os.startfile(path)
            except Exception as e:
                messagebox.showerror("Launch Error", f"Failed to launch:\n{path}\n\n{e}")
    save_config()

def save_config():
    """Save paths and checkbox states to JSON."""
    config = {
        "entries": [entry.get() for entry in entries],
        "checked": [var.get() for var in check_vars]
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

def load_config():
    """Load config from JSON (if exists)."""
    if not os.path.exists(CONFIG_FILE):
        return
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        for i in range(min(5, len(config.get("entries", [])))):
            path = config["entries"][i]
            entries[i].insert(0, path)
            check_vars[i].set(config["checked"][i])
            update_app_label(i, path)
    except Exception as e:
        print(f"Failed to load config: {e}")

def clear_all():
    """Clear all fields, checkboxes, and labels."""
    for i in range(5):
        entries[i].delete(0, tk.END)
        check_vars[i].set(False)
        app_labels[i].config(text="(No file selected)")
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)

def on_entry_enter(event, index):
    """When Enter is pressed, update label and save config."""
    path = entries[index].get().strip()
    update_app_label(index, path)
    save_config()

# --- UI Setup ---
root = tk.Tk()
root.title("Program Launcher")
root.geometry("840x480")
root.resizable(False, False)

check_vars = []
entries = []
app_labels = []

for i in range(5):
    frame = tk.Frame(root)
    frame.pack(pady=5, padx=10, fill="x")

    var = tk.BooleanVar()
    check = tk.Checkbutton(frame, variable=var)
    check.pack(side="left", padx=(0, 8))

    name_label = tk.Label(frame, text="(Nothing selected)", width=25, anchor="w")
    name_label.pack(side="left", padx=(0, 8))
    app_labels.append(name_label)

    entry = tk.Entry(frame, width=60)
    entry.pack(side="left", fill="x", expand=True)
    entry.bind("<Return>", lambda event, i=i: on_entry_enter(event, i))
    entries.append(entry)

    browse_btn = tk.Button(frame, text="Browse", command=lambda i=i: browse_file(i))
    browse_btn.pack(side="left", padx=(8, 0))

    check_vars.append(var)

# Bottom control buttons
button_frame = tk.Frame(root)
button_frame.pack(pady=20)

launch_button = tk.Button(
    button_frame,
    text="🚀 Launch Selected",
    font=("Segoe UI", 14, "bold"),
    bg="#4CAF50",
    fg="white",
    padx=20,
    pady=10,
    command=launch_selected
)
launch_button.pack(side="left", padx=10)

clear_button = tk.Button(
    button_frame,
    text="🧹 Clear All",
    font=("Segoe UI", 12),
    bg="#F44336",
    fg="white",
    padx=15,
    pady=8,
    command=clear_all
)
clear_button.pack(side="left", padx=10)

# Load saved configuration
load_config()

root.mainloop()
