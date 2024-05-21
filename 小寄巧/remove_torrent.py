import sys
import qbittorrentapi as qb_api
from math import ceil, floor
from wcwidth import wcswidth
from tabulate import tabulate


def client_info(qbc):
    try:
        qbc.auth_log_in()
    except qb_api.LoginFailed as e:
        print(e)

    main_data = qbc.sync_maindata()
    print(f"Connected to qBittorrent client {qbc.app_version()}")
    print(f"Active torrents: {len(main_data['torrents'])}")
    free_space = format(main_data['server_state']['free_space_on_disk'] / 1073741824, '.2f')

    return main_data, free_space


def process_torrents(main_data, qbc, free_space):
    tdata = dict()
    torrent_count = len(main_data['torrents'])
    count = 0
    output_len = 0

    for torrent in qbc.torrents_info():
        hash_val = torrent.info['hash']
        name = main_data['torrents'][hash_val]['name']

        count += 1
        output_blank = ""
        for _ in range(output_len):
            output_blank += " "
        sys.stdout.write(f"\r{output_blank}")
        output = f"Loading torrent {count}/{torrent_count} [{hash_val[-6:]}]: {name}"
        sys.stdout.write(f"\r{output}")
        output_len = wcswidth(output)

        site_id = -1
        tracker_msg = ''
        num_seeds = 0
        tracker_info = qbc.torrents_trackers(hash=hash_val)
        for info in tracker_info[3:]:
            tracker_url = info['url']
            if site_id == -1:
                if "monikadesign.uk" in tracker_url:
                    site_id = 0
                elif "daydream.dmhy.best" in tracker_url:
                    site_id = 1
                elif "pt.skyey.win" in tracker_url:
                    site_id = 2

            if info['msg'] != "":
                tracker_msg += info['msg']

            if info['num_seeds'] > num_seeds:
                num_seeds = info['num_seeds']

        size = main_data['torrents'][hash_val]['size']
        seed_time = main_data['torrents'][hash_val]['seeding_time']
        upload = main_data['torrents'][hash_val]['uploaded']

        if name not in tdata.keys():
            tdata[name] = {
                'name': name,
                'hash': ['n/a', 'n/a', 'n/a'],
                'seed_time': 0.0,
                'size': size,
                'total_seeds': [-1, -1, -1],
                'total_upload': 0.0,
                'tracker_msg': ""
            }

        if site_id == -1:
            tdata[name]['hash'].append(hash_val)
            continue

        tdata[name]['hash'][site_id] = hash_val
        if seed_time > tdata[name]['seed_time']:
            tdata[name]['seed_time'] = seed_time
        tdata[name]['total_seeds'][site_id] = num_seeds
        tdata[name]['total_upload'] += upload
        tdata[name]['tracker_msg'] += tracker_msg

        # if count > 50: break

    print(f"\nFree disk space: {free_space} GiB\n")

    return {key: value for key, value in sorted(tdata.items(), key=lambda item: item[1]['seed_time'], reverse=True)}


def display_torrents(tlist, start, step_size, total_seed_filter):
    title_width = 70
    table = []
    display_list = []

    i = start - 1
    count = 0
    while (i < len(tlist) - 1) & (count < step_size):
        i += 1
        torrent = tlist[i]

        # Skip dying torrent in MonikaDesign
        if (torrent['total_seeds'][0] < total_seed_filter) & (torrent['total_seeds'][0] > -1):
            continue

        # Skip torrnets younger than 14 days
        if torrent['seed_time'] < 7 * 86400:
            continue

        line = [str(i)]
        if wcswidth(torrent['name']) <= title_width:
            line.append(torrent['name'])
        else:
            front = ceil(title_width * 2 / 3)
            rear = ceil(title_width * 1 / 3)
            string = torrent['name'][:front] + " ... " + torrent['name'][-rear:]
            while wcswidth(string) > title_width:
                front -= 1
                rear -= 1
                string = torrent['name'][:front] + " ... " + torrent['name'][-rear:]
            line.append(string)

        line.append(str(count))
        line.append(format(torrent['seed_time'] / 86400, '.2f'))
        line.append(format(torrent['size'] / 1073741824, '.2f'))

        for j in range(3):
            if torrent['total_seeds'][j] == -1:
                line.append("-")
            else:
                line.append(torrent['total_seeds'][j])
        table.append(line)

        line.append(format(torrent['total_upload'] / 1073741824, '.2f'))
        line.append(torrent['tracker_msg'])

        count += 1
        display_list.append(i)

    print("")
    print(tabulate(table, headers=['#', 'Name', 'ID', 'Days', 'Size', 'MDU', 'U2', 'Skyey', 'Upload', 'Tracker msg'],
                   tablefmt="github"))

    return display_list


def remove_torrents_by_input(tlist, step_size, display_list):
    id_input = input("\nTorrents IDs to remove ('n' for next, 'q' to quit): ")

    id_list = id_input.split(" ")
    remove_size = 0.0
    removed_index = []

    for s in id_list:
        if s == "q":
            exit(1)
        if s == "n":
            break
        if s == "":
            continue

        s_list = []
        if "-" in s:
            try:
                start = int(s.split("-")[0])
                end = int(s.split("-")[1])
            except (TypeError, ValueError) as e:
                print(e)
                continue
            s_list = range(start, end + 1)
        else:
            try:
                s_list = [int(s)]
            except (TypeError, ValueError) as e:
                print(e)
                continue

        for index in s_list:
            if (index < 0) | (index > step_size - 1):
                print(f"ID {index} is out of range")
                continue

            torrent = tlist[display_list[index]]
            removed_index.append(display_list[index])
            name = torrent['name']
            print(f"Removing torrent {index}: {name}")

            hash_list = []
            for hash_val in torrent['hash']:
                if hash_val != "n/a":
                    hash_list.append(hash_val)
            print(qbc.torrents_delete(torrent_hashes=hash_list, delete_files=True))
            remove_size += torrent['size']

    return remove_size, removed_index


def remove_torrents_tracker_msg(tlist):
    title_width = 70
    count = 0
    table = []
    display_list = []

    for i, torrent in enumerate(tlist):
        if torrent['tracker_msg'] == "":
            continue

        line = [str(i)]
        line.append(format(torrent['seed_time'] / 86400, '.2f'))

        if wcswidth(torrent['name']) <= title_width:
            line.append(torrent['name'])
        else:
            front = ceil(title_width * 2 / 3)
            rear = ceil(title_width * 1 / 3)
            string = torrent['name'][:front] + " ... " + torrent['name'][-rear:]
            while wcswidth(string) > title_width:
                front -= 1
                rear -= 1
                string = torrent['name'][:front] + " ... " + torrent['name'][-rear:]
            line.append(string)

        line.append(str(count))
        line.append(format(torrent['size'] / 1073741824, '.2f'))
        line.append(torrent['tracker_msg'])

        table.append(line)
        count += 1
        display_list.append(i)

    if len(table) == 0:
        print("No torrent with tracker msg")
    else:
        print("")
        print(tabulate(table, headers=['#', 'Days', 'Name', 'ID', 'Size', 'Tracker msg'], tablefmt="github"))

        _, removed_index = remove_torrents_by_input(tlist, 10 ** 9, display_list)

        removed_index.sort(reverse=True)
        for index in removed_index:
            tlist.pop(index)

    return tlist


def remove_torrents_seedtime(tlist, qbc, start, step_size, free_space, total_remove, total_seed_filter):
    display_list = display_torrents(tlist, start, step_size, total_seed_filter)
    if len(display_list) == 0:
        return

    removed_size, _ = remove_torrents_by_input(tlist, step_size, display_list)
    total_remove += removed_size

    new_free_space = format(qbc.sync_maindata()['server_state']['free_space_on_disk'] / 1073741824, '.2f')
    print(f"Removed size    :  {format(total_remove / 1073741824, '.2f')} GiB")
    print(f"Free disk space :  {free_space} -> {new_free_space} GiB\n")

    if len(display_list) < step_size:
        return

    remove_torrents_seedtime(tlist, qbc, display_list[-1] + 1, step_size, free_space, total_remove, total_seed_filter)


if __name__ == "__main__":
    # Connect with qBittorrent client and get main data
    qbc = qb_api.Client(host=input('host: '), port=input('port: '), username=input('username: '), password=input('password: '))

    tsf = 5	# Total seed filter
    if len(sys.argv) < 2:
        pass
    else:
        try:
            tsf = int(sys.argv[1])
        except (TypeError, ValueError) as e:
            print(e)

    main_data, free_space = client_info(qbc)

    # Organize torrent data
    tdata = process_torrents(main_data, qbc, free_space)

    # Display and remove torrent
    tlist = remove_torrents_tracker_msg(list(tdata.values()))
    remove_torrents_seedtime(tlist, qbc, 0, 25, free_space, 0.0, tsf)

    # Log out connection
    qbc.auth_log_out()
