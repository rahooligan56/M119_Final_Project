import socket
import csv
from datetime import datetime
from pynput import keyboard

HOST = '0.0.0.0'
PORT = 3000

# ==== FILE SETUP ====
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
data_filename = f"imu_data_{timestamp}.csv"
shot_filename = f"shot_times_{timestamp}.txt"

data_file = open(data_filename, 'w', newline='')
writer = csv.writer(data_file)
writer.writerow(['timestamp','ax','ay','az','gx','gy','gz'])

shot_file = open(shot_filename, 'w')

shot_flag = False
stop_flag = False

# ==== KEY HANDLER ====
def on_press(key):
    global shot_flag, stop_flag

    try:
        if key == keyboard.Key.space:
            shot_flag = True
        elif key == keyboard.Key.esc:
            stop_flag = True
            return False
    except:
        pass

listener = keyboard.Listener(on_press=on_press)
listener.start()

# ==== SOCKET SETUP ====
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(1)

print("Waiting for Arduino connection...")
conn, addr = server.accept()
print("Connected by", addr)

print("\nRecording Started")
print("Press SPACE to mark shot")
print("Press ESC to stop\n")

buffer = ""

try:
    while not stop_flag:
        data = conn.recv(1024).decode(errors='ignore')
        if not data:
            break

        buffer += data
        lines = buffer.split("\n")
        buffer = lines[-1]

        for line in lines[:-1]:
            values = line.strip().split(',')
            if len(values) == 7:
                writer.writerow(values)

                if shot_flag:
                    timestamp_value = values[0]
                    shot_file.write(timestamp_value + "\n")
                    shot_file.flush()   # write immediately
                    print(f"Shot marked at {timestamp_value}")
                    shot_flag = False

except KeyboardInterrupt:
    pass

print("Stopping...")

data_file.close()
shot_file.close()
conn.close()
server.close()

print("Saved:")
print(data_filename)
print(shot_filename)