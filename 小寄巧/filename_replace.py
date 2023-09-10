import os

root = input('Target folder: ').replace('\"','')
old_title = input('Old title: ')
new_title = input('New title: ')

filename_iter = [filename for filename in os.listdir(root)]
path_iter = [os.path.join(root, filename) for filename in filename_iter]

for i, filename in enumerate(filename_iter):
    if old_title in filename:
        path = path_iter[i]
        new_path = os.path.join(root, filename.replace(old_title, new_title))
        os.rename(path, new_path)
        print(f'Renamed {path} to {new_path}')

input('complete')