import os
import subprocess
from zipfile import ZipFile

mktorrent_s2_path = r"D:\Seeding\torrent_s2.exe"

root = os.getcwd()
folder_iter = [filename for filename in os.listdir(os.getcwd())]
path_iter = [os.path.join(root, filename) for filename in folder_iter]

for i in range(len(folder_iter)):
    folder_name = folder_iter[i]
    folder_path = path_iter[i]

    if not os.path.isdir(folder_path):
        continue
    print(f"\nProcessing: \"{folder_name}\"")
    
    for filename in os.listdir(folder_path):
        if filename[-4:] == ".md5":
            print(f"Zipping and removing MD5: {filename}")
            with ZipFile(os.path.join(root, filename) + '.zip','w') as zip:
                zip.write(os.path.join(folder_path, filename), filename) 
            os.remove(os.path.join(folder_path, filename))

    subprocess.run([mktorrent_s2_path, folder_name], shell=True)