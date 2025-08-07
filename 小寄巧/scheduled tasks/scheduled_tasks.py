import time
import datetime

from utilities import time_stamp
from check_peers import check_peers
from check_clients import check_clients
from tag_torrent import tag_torrent

def run_module(module, description):
    print(f"{time_stamp()} Start [{description}].")
    try:
        module()
        print(f"{time_stamp()} [{description}] complete.")
    except:
        print(f"{time_stamp()} [{description}] failed due to unknown error.")

if __name__ == "__main__":
    while True:
        # run modules
        run_module(check_clients, "client health check")
        run_module(check_peers, "peer check")
        run_module(tag_torrent, "torrent tag")
            
        # wait for next run
        now = datetime.datetime.now()
        dt = now + datetime.timedelta(minutes=10 - now.minute % 10)
        dt = dt.replace(second=0, microsecond=0)
        while datetime.datetime.now() < dt:
            time.sleep(1)