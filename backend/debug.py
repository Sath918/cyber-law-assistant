import subprocess
import time

p = subprocess.Popen(["python", "app.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
time.sleep(3) # wait to start

import requests
try:
    print("Testing chat endpoint")
    r = requests.post("http://localhost:5000/chat", json={"message": "hi", "user_id": None}, timeout=60)
    print("RESULT:", r.status_code, r.text)
except Exception as e:
    print("ERR:", e)

p.kill()
stdout, stderr = p.communicate()
print("FLASK STDOUT:")
print(stdout)
print("FLASK STDERR:")
print(stderr)
