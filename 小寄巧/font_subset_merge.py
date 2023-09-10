import os, subprocess

# mkvmerge.exe的路径，可以在mkvtoolnix安装文件夹中找到
mkvmerge_path = 'F:/Encode tools/mkvmerge.exe'

def merge():
  source_dir = input('目标文件夹 > ').replace('\"','')
  dump_dir = source_dir + '\dump'
  os.makedirs(dump_dir, exist_ok=True)

  mkv_list = []
  ass_list = []
  files = os.listdir(source_dir)
  for filename in files:
    if '.mkv' in filename:
      mkv_list.append(filename)
    elif '.ass' in filename:
      ass_list.append(filename)
  mkv_list.sort()
  ass_list.sort()

  if len(mkv_list) != len(ass_list):
    if input('视频与字幕数量不匹配，是否继续? [y/N]') != 'y':
      quit()

  for i in range(len(mkv_list)):
    mkv = mkv_list[i]
    mkv_path = os.path.join(source_dir, mkv)
    mkv_path_dump = os.path.join(dump_dir, mkv)
    ass = ass_list[i]
    ass_path = os.path.join(source_dir, ass)
    ass_path_dump = os.path.join(dump_dir, ass)
    print('\n' + mkv + '\n' + ass)
    os.rename(mkv_path, mkv_path_dump)
    os.rename(ass_path, ass_path_dump)
    subprocess.getoutput([mkvmerge_path, '--output', mkv_path, mkv_path_dump, ass_path_dump], encoding='utf-8')
    print('混流完毕')
    
  print(f'\n{len(mkv_list)}个任务全部混流完毕！')

if __name__ == '__main__':
  merge()
  while (input('再来一轮? [y/N]') == 'y'):
    merge()