import socket
import numpy as np
from collections import deque

print("Script started!")

# ==========================
# SETTINGS
# ==========================
HOST = '0.0.0.0'
PORT = 3000

DYNAMIC_THRESHOLD = 1.2     # Tune (start ~1.0–1.5 based on your analysis)
COOLDOWN_MS = 1200
BASELINE_WINDOW = 100       # Number of samples for rolling baseline

last_shot_time = 0
accel_history = deque(maxlen=BASELINE_WINDOW)

print("\n=== ACCEL-ONLY SHOT DETECTOR STARTED ===")
print("Waiting for Arduino connection...")

# ==========================
# SOCKET SETUP
# ==========================
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(1)

conn, addr = server.accept()
print("Connected to Arduino:", addr)
print("Monitoring paddle movement...\n")

buffer = ""

try:
    while True:
        data = conn.recv(1024).decode(errors='ignore')
        if not data:
            break

        buffer += data
        lines = buffer.split("\n")
        buffer = lines[-1]

        for line in lines[:-1]:
            values = line.strip().split(',')

            if len(values) == 7:
                timestamp = int(values[0])

                ax = float(values[1])
                ay = float(values[2])
                az = float(values[3])

                # Compute acceleration magnitude
                accel_mag = np.sqrt(ax*ax + ay*ay + az*az)

                # Update baseline buffer
                accel_history.append(accel_mag)

                # Wait until buffer fills
                if len(accel_history) < BASELINE_WINDOW:
                    continue

                baseline = np.mean(accel_history)
                dynamic_accel = accel_mag - baseline

                # Detection condition
                if (dynamic_accel > DYNAMIC_THRESHOLD and
                    timestamp - last_shot_time > COOLDOWN_MS):

                    print(f"SHOT DETECTED at {timestamp} | DynamicAccel={dynamic_accel:.2f}")
                    last_shot_time = timestamp

except KeyboardInterrupt:
    print("\nStopped.")
    conn.close()
    server.close()