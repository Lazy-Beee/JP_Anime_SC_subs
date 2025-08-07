import os
import requests
import json

from utilities import time_stamp

QB_URL = ""
USERNAME = ""
PASSWORD = ""
PEER_REPEAT_THREAHOLD = 5

def check_peers():
    # Login to qBittorrent
    session = requests.Session()
    login_data = {"username": USERNAME, "password": PASSWORD}
    login_response = session.post(f"{QB_URL}/api/v2/auth/login", data=login_data)
    if login_response.text != "Ok.":
        print(f"Login failed, Response: {login_response.text}")
        exit()

    # Fetch list of torrents
    torrents_response = session.get(f"{QB_URL}/api/v2/torrents/info?filter=seeding")
    if torrents_response.status_code != 200:
        print(f"Failed to fetch torrents, Response: {ban_response.text}")
        exit()

    torrents = torrents_response.json()

    # Loop through torrents and get peers
    peer_log = {}
    for torrent in torrents:
        hash = torrent["hash"]
        torrent_name = torrent["name"]
        tags = torrent["tags"]

        peer_response = session.get(f"{QB_URL}/api/v2/sync/torrentPeers?hash={hash}")
        if peer_response.status_code == 200:
            peer_data = peer_response.json()
            peers = peer_data.get("peers", {})
            for peer_ip in peers.keys():
                peer_port = peer_ip.rsplit(':', 1)[-1]
                peer_ip = peer_ip.split(']:')[0] + ']' if ']:' in peer_ip else peer_ip.split(':')[0]
                info = {"name": torrent_name, "hash": hash, "tags": tags, "port": peer_port}
                if peer_ip not in peer_log:
                    peer_log[peer_ip] = [info]
                else:
                    peer_log[peer_ip].append(info)
        else:
            print(f"Failed to fetch peer info, Response: {ban_response.text}")

    # Loop peers to find repeated ones
    repeated_peer = {}
    for peer_ip in peer_log:
        if len(peer_log[peer_ip]) > PEER_REPEAT_THREAHOLD:
            repeated_peer[peer_ip] = peer_log[peer_ip];
            ban_response = session.post(f"{QB_URL}/api/v2/transfer/banPeers", data={"peers": f"{peer_ip}:10000"})
            if ban_response.status_code == 200:
                print(f"{time_stamp()} Banned IP: {peer_ip}")
            else:
                print(f"Failed to ban IP: {peer_ip}, Response: {ban_response.text}")

    # Save peer log to file
    if len(repeated_peer) > 0:
        out_path = f"{os.getcwd()}\peer_block_logs"
        os.makedirs(out_path, exist_ok=True)

        with open(f"{out_path}\peers_log_{time_stamp(no_space=True)}.json", "w", encoding="utf-8") as file:
            json.dump(repeated_peer, file, indent=4, ensure_ascii=False)

        print(f"{time_stamp()} Peer log saved to peers_log_{time_stamp(no_space=True)}.json")

if __name__ == '__main__':
    check_peers()