import sys, os, subprocess

# mkvmerge.exe的路径，可以在mkvtoolnix安装文件夹中找到
mkvmerge_path = 'F:/Encode tools/mkvmerge.exe'

def merge_single(mkv_list, ass_list, source_dir, dump_dir):
  for i in range(len(mkv_list)):
    mkv = mkv_list[i]
    mkv_path = os.path.join(source_dir, mkv)
    mkv_path_dump = os.path.join(dump_dir, mkv)
    ass = ass_list[i]
    ass_path = os.path.join(source_dir, ass)
    ass_path_dump = os.path.join(dump_dir, ass)
    print(f'\n任务 {i+1}:\n视频：{mkv}\n字幕：{ass}')
    os.rename(mkv_path, mkv_path_dump)
    os.rename(ass_path, ass_path_dump)
    subprocess.run([mkvmerge_path,
                    '--output', mkv_path,
                    '--no-subtitles', '--no-attachments', mkv_path_dump, 
                    '--language', '0:zh-CN', '--default-track', '0:yes', '--track-name', '0:简体中文', ass_path_dump]) # 这里设置单字幕字幕轨的参数
    print(f'任务 {i+1} 混流完毕')

def merge_double(mkv_list, ass_list, source_dir, dump_dir):
  for i in range(len(mkv_list)):
    mkv = mkv_list[i]
    mkv_path = os.path.join(source_dir, mkv)
    mkv_path_dump = os.path.join(dump_dir, mkv)
    ass1 = ass_list[2*i]
    ass1_path = os.path.join(source_dir, ass1)
    ass1_path_dump = os.path.join(dump_dir, ass1)
    ass2 = ass_list[2*i+1]
    ass2_path = os.path.join(source_dir, ass2)
    ass2_path_dump = os.path.join(dump_dir, ass2)
    print(f'\n任务 {i+1}:\n视频：{mkv}\n字幕1：{ass1}\n字幕2：{ass2}')
    os.rename(mkv_path, mkv_path_dump)
    os.rename(ass1_path, ass1_path_dump)
    os.rename(ass2_path, ass2_path_dump)
    subprocess.run([mkvmerge_path,
                    '--output', mkv_path,
                    '--no-subtitles', '--no-attachments', mkv_path_dump,
                    '--language', '0:zh-CN', '--default-track', '0:yes', '--track-name', '0:简体中文', ass1_path_dump, # 这里设置双字幕字幕轨1的参数
                    '--language', '0:zh-TW', '--default-track', '0:no', '--track-name', '0:繁体中文', ass2_path_dump]) # 这里设置双字幕字幕轨2的参数
    print(f'任务 {i+1} 混流完毕')

def merge(source_dir=""):
  if source_dir == "":
    source_dir = input('目标文件夹 > ').replace('\"','')
  print(f"\n开始处理源文件夹: {source_dir}")
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
  mkv_count = len(mkv_list)
  ass_count = len(ass_list)

  if mkv_count == ass_count:
    merge_single(mkv_list, ass_list, source_dir, dump_dir)
  elif mkv_count * 2 == ass_count:
    merge_double(mkv_list, ass_list, source_dir, dump_dir)
  else:
    input(f'视频数量({mkv_count})与字幕数量({ass_count})不匹配，请检查后继续 [Enter]')
    return
    
  print(f'\n{len(mkv_list)}个任务全部混流完毕！')

if __name__ == '__main__':
  if len(sys.argv) < 2:
    merge()
    while (input('再来一轮? [y/N]') == 'y'):
      merge()
  else:
    for source_dir in sys.argv[1:]:
      merge(source_dir)
