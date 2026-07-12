import requests

url = "http://localhost:5001/chat"
payload = {
    "user_id": None,
    "message": "hi"
}
try:
    res = requests.post(url, json=payload)
    print("STATUS", res.status_code)
    print(res.text)
except Exception as e:
    print("ERR", e)
