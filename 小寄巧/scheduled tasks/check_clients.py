import requests
import json

from utilities import time_stamp, send_telegram_message

CLIENTS = [
    {"type": "qb", "url": "", "username": "", "password": "", "name": ""},
    {"type": "tr", "url": "", "username": "", "password": "", "name": ""},
    ]

def check_qbittorrent_alive(url, username, password):
    try:
        session = requests.Session()
        login_data = {"username": username, "password": password}
        response = session.post(f"{url}/api/v2/auth/login", data=login_data)
        if response.text == "Ok.":
            print(f"{time_stamp()} qBittorrent at {url} is alive.")
            return True
        else:
            print(f"{time_stamp()} qBittorrent at {url} login failed. Response: {response.text}")
            return False
    except Exception as e:
        print(f"{time_stamp()} qBittorrent check failed: {e}")
        return False

def check_transmission_alive(url, username=None, password=None):
    try:
        headers = {"X-Transmission-Session-Id": "dummy"}
        auth = (username, password) if username and password else None
        data = json.dumps({"method": "session-get"})

        response = requests.post(f"{url}/transmission/rpc", data=data, headers=headers, auth=auth)
        
        if response.status_code == 409:
            # Retry with correct session ID
            session_id = response.headers["X-Transmission-Session-Id"]
            headers["X-Transmission-Session-Id"] = session_id
            response = requests.post(f"{url}/transmission/rpc", data=data, headers=headers, auth=auth)

        if response.status_code == 200:
            print(f"{time_stamp()} Transmission at {url} is alive.")
            return True
        else:
            print(f"{time_stamp()} Transmission at {url} check failed. Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"{time_stamp()} Transmission check failed: {e}")
        return False

def check_clients():
    for client in CLIENTS:
        alive = True
        if client["type"] == "qb":
            alive = alive & check_qbittorrent_alive(client["url"], client["username"], client["password"])
        elif client["type"] == "tr":
            alive = alive & check_transmission_alive(client["url"], client["username"], client["password"])
        if not alive:                
            send_telegram_message("Client " + client["name"] + " is down.")
