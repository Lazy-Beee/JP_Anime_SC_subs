import qbittorrentapi as qb
from wcwidth import wcswidth
from tabulate import tabulate

def client_info(qbc):

    try:
        qbc.auth_log_in()
    except qb.LoginFailed as e:
        print(e)

    main_data = qbc.sync_maindata()
    print(f"Connected to qBittorrent client {qbc.app_version()}")
    print(f"Active torrents: {len(main_data['torrents'])}")
    free_space = format(main_data['server_state']['free_space_on_disk']/1073741824, '.2f')

    return main_data, free_space

def process_torrents(main_data, qbc, free_space):

    tdata = dict()
    torrent_count = len(main_data['torrents'])
    count = 0

    for torrent in qbc.torrents_info():
        hash_val = torrent.info['hash']
        name = main_data['torrents'][hash_val]['name']

        count += 1
        print(f"Loading torrent {count}/{torrent_count} [{hash_val[-6:]}]: {name}")

        tracker = main_data['torrents'][hash_val]['tracker']
        site_id = -1
        if "monikadesign.uk" in tracker:
            site_id = 0
        elif "daydream.dmhy.best" in tracker:
            site_id = 1
        elif "pt.skyey.win" in tracker:
            site_id = 2

        size = main_data['torrents'][hash_val]['size']
        seed_time = main_data['torrents'][hash_val]['seeding_time']
        total_seeds = torrent.properties['seeds_total']

        if name not in tdata.keys():
            tdata[name] = {
                'name': name,
                'hash': ['n/a', 'n/a', 'n/a'],
                'seed_time': 0,
                'size': size,
                'total_seeds': [-1, -1, -1]
            }

        if site_id == -1:
            tdata[name]['hash'].append(hash_val)
            continue

        tdata[name]['hash'][site_id] = hash_val
        if seed_time > tdata[name]['seed_time']:
            tdata[name]['seed_time'] = seed_time
        tdata[name]['total_seeds'][site_id] = total_seeds

        if count > 50: break

    print(f"\nFree disk space: {free_space} GB\n")

    return {key: value for key, value in sorted(tdata.items(), key=lambda item: item[1]['seed_time'], reverse=True)}

def display_torrents(tlist, start, step_size):
    table = []
    display_list = []

    i = start-1
    count = 0
    while (i < len(tlist) - 1) & (count < step_size):
        i += 1
        torrent = tlist[i]

        if torrent['total_seeds'][0] < 5:
            continue
        # if torrent['seed_time'] < 30 * 86400:
        #     continue

        line = [str(count) + "/" + str(i)]
        if wcswidth(torrent['name']) <= 50:
            line.append(torrent['name'])
        else:
            front = 30
            rear = 15
            string = torrent['name'][:front] + " ... " + torrent['name'][-rear:]
            while wcswidth(string) > 50:
                front -= 1
                rear -= 1
                string = torrent['name'][:front] + " ... " + torrent['name'][-rear:]
            line.append(string)
        line.append(format(torrent['seed_time']/86400, '.2f'))
        line.append(format(torrent['size']/1073741824, '.2f'))

        for j in range(3):
            if torrent['total_seeds'][j] == -1:
                line.append("x")
            else:
                line.append(torrent['total_seeds'][j])
        table.append(line)

        count += 1
        display_list.append(i)

    print("")
    print(tabulate(table, headers=['ID', 'Name', 'Days', 'Size', 'MDU', 'U2', 'Skyey'], tablefmt="github"))

    return display_list

def remove_torrents(tlist, qbc, start, free_space, total_remove):
    step_size = 10
    display_list = display_torrents(tlist, start, step_size)
    if len(display_list) == 0:
        return

    id_input = input("\nTorrents IDs to remove ('n' for next, 'q' to quit): ")

    id_list = id_input.split(" ")
    for i in id_list:
        if i == "q":
            return
        if i == "n":
            break

        try:
            index = int(i)
        except (TypeError, ValueError) as e:
            print(e)
            continue

        if (index < 0) | (index > step_size - 1):
            print(f"ID {index} is out of range")
            continue

        torrent = tlist[display_list[index]]
        name = torrent['name']
        print(f"Removing torrent {i}: {name}")

        hash_list = []
        for hash_val in torrent['hash']:
            if hash_val != "n/a":
                hash_list.append(hash_val)
        print(qbc.torrents_delete(torrent_hashes=hash_list, delete_files=True))
        total_remove += torrent['size']

    new_free_space = format(qbc.sync_maindata()['server_state']['free_space_on_disk'] / 1073741824, '.2f')
    print(f"Removed size: {format(total_remove / 1073741824, '.2f')}")
    print(f"Free disk space: {free_space} -> {new_free_space} GB\n")

    if len(display_list) < step_size:
        return

    remove_torrents(tlist, qbc, display_list[-1] + 1, free_space, total_remove)

if __name__ == "__main__":

    # Connect with qBittorrent client and get main data
    # qbc = qb.Client(host="localhost", port=8080, username="", password="")
    qbc = qb.Client(host=input('host: '), port=input('port: '), username=input('username: '), password=input('password: '))
    main_data, free_space = client_info(qbc)

    # Organize torrent data
    tdata = process_torrents(main_data, qbc, free_space)

    # Display and remove torrent
    remove_torrents(list(tdata.values()), qbc, 0, free_space, 0)

    # Log out connection
    qbc.auth_log_out()
