import socket
import numpy as np
import time
from collections import deque

import tkinter as tk
from tkinter import ttk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# ==========================
# SETTINGS
# ==========================
HOST = "0.0.0.0"
PORT = 3000

DYNAMIC_THRESHOLD = 0.5
COOLDOWN_MS = 1200
BASELINE_WINDOW = 100

last_shot_time = 0
shot_count = 0
accel_history = deque(maxlen=BASELINE_WINDOW)

# ==========================
# GUI SETUP
# ==========================
root = tk.Tk()
root.title("Shot Dashboard")

root.geometry("800x600")
root.configure(bg="black")

label_counter = tk.Label(root, text="0", font=("Arial", 80), fg="white", bg="black")
label_counter.pack(pady=20)

label_strength = tk.Label(root, text="Impact: 0.0", font=("Arial", 30), fg="white", bg="black")
label_strength.pack()

# Graph area
fig, ax = plt.subplots(figsize=(8,3))
ax.set_title("Dynamic Acceleration")
ax.set_xlabel("Samples")
ax.set_ylabel("Accel")
line_plot, = ax.plot([], [], color="red")
ax.set_ylim(-0.5, 4)

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack()

dynamic_buffer = deque(maxlen=300)

# ==========================
# UPDATE GUI FUNCTION
# ==========================
def update_graph():
    if len(dynamic_buffer) > 0:
        line_plot.set_data(range(len(dynamic_buffer)), list(dynamic_buffer))
        ax.set_xlim(0, len(dynamic_buffer))
        canvas.draw()
    root.after(50, update_graph)

update_graph()

# ==========================
# ARDUINO LISTENER
# ==========================
def arduino_listener():
    global last_shot_time, shot_count

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)

    print("Waiting for Arduino...")
    conn, addr = server.accept()
    print("Connected:", addr)

    buffer = ""

    while True:
        data = conn.recv(1024).decode(errors="ignore")
        if not data:
            break

        buffer += data
        lines = buffer.split("\n")
        buffer = lines[-1]

        for line in lines[:-1]:
            values = line.strip().split(",")

            if len(values) == 7:
                timestamp = int(values[0])

                ax = float(values[1])
                ay = float(values[2])
                az = float(values[3])

                accel_mag = np.sqrt(ax*ax + ay*ay + az*az)
                accel_history.append(accel_mag)

                if len(accel_history) < BASELINE_WINDOW:
                    continue

                baseline = np.mean(accel_history)
                dynamic_accel = accel_mag - baseline

                dynamic_buffer.append(dynamic_accel)

                if (dynamic_accel > DYNAMIC_THRESHOLD and
                    timestamp - last_shot_time > COOLDOWN_MS):

                    shot_count += 1
                    last_shot_time = timestamp

                    # Update UI
                    label_counter.config(text=str(shot_count))
                    label_strength.config(text=f"Impact: {dynamic_accel:.2f}")
                    root.configure(bg="red")
                    root.after(200, lambda: root.configure(bg="black"))

    conn.close()

# ==========================
# START LISTENER THREAD
# ==========================
import threading
threading.Thread(target=arduino_listener, daemon=True).start()

# ==========================
# RUN GUI
# ==========================
root.mainloop()
