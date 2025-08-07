import os
import requests
import json
import logging

from utilities import time_stamp

QB_URL = ""
USERNAME = ""
PASSWORD = ""
PEER_REPEAT_THREAHOLD = 4
LOG_PATH = ""

logging.basicConfig(filename="", level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

def log(string):
    print(string)
    logging.info(string)

def check_peers():
    # Login to qBittorrent
    session = requests.Session()
    login_data = {"username": USERNAME, "password": PASSWORD}
    login_response = session.post(f"{QB_URL}/api/v2/auth/login", data=login_data)
    if login_response.text != "Ok.":
        log(f"Login failed, Response: {login_response.text}")
        exit()

    # Fetch list of torrents
    torrents_response = session.get(f"{QB_URL}/api/v2/torrents/info?filter=seeding")
    if torrents_response.status_code != 200:
        log(f"Failed to fetch torrents, Response: {ban_response.text}")
        exit()

    torrents = torrents_response.json()

    # Loop through torrents and get peers
    peer_log = {}
    for torrent in torrents:
        hash = torrent["hash"]
        torrent_name = torrent["name"]
        category = torrent["category"]

        peer_response = session.get(f"{QB_URL}/api/v2/sync/torrentPeers?hash={hash}")
        if peer_response.status_code == 200:
            peer_data = peer_response.json()
            peers = peer_data.get("peers", {})
            for peer_ip in peers.keys():
                peer_port = peer_ip.rsplit(':', 1)[-1]
                peer_ip = peer_ip.split(']:')[0] + ']' if ']:' in peer_ip else peer_ip.split(':')[0]
                #if category == "shua":
                #    continue
                info = {"port": peer_port, "category": category, "name": torrent_name}
                if peer_ip not in peer_log:
                    peer_log[peer_ip] = [info]
                else:
                    peer_log[peer_ip].append(info)
        else:
            log(f"Failed to fetch peer info, Response: {ban_response.text}")

    # Loop peers to find repeated ones
    log(f"Obtained {len(peer_log)} peer IPs from {len(torrents)} seeding torrents.")
    repeated_peer = {}
    for peer_ip in peer_log:
        if len(peer_log[peer_ip]) >= PEER_REPEAT_THREAHOLD:
            log(f"Peer [{peer_ip}] has repeated {len(peer_log[peer_ip])} times.")
            for line in peer_log[peer_ip]:
                log(line)
            #if input("Ban? (Y/n): ") != "Y":
            #    continue;
            repeated_peer[peer_ip] = peer_log[peer_ip];
            ban_response = session.post(f"{QB_URL}/api/v2/transfer/banPeers", data={"peers": f"{peer_ip}:10000"})
            if ban_response.status_code == 200:
                log(f"Banned IP: {peer_ip}")
            else:
                log(f"Failed to ban IP: {peer_ip}, Response: {ban_response.text}")

    return
    # Save peer log to file
    if len(repeated_peer) > 0:
        os.makedirs(LOG_PATH, exist_ok=True)

        with open(os.path.join(LOG_PATH, f"peers_log_{time_stamp(no_space=True)}.json"), "w", encoding="utf-8") as file:
            json.dump(repeated_peer, file, indent=4, ensure_ascii=False)

        log(f"Peer log saved to peers_log_{time_stamp(no_space=True)}.json")

if __name__ == "__main__":
    check_peers()
