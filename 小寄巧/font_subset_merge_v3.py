import sys, os, subprocess

# mkvmerge的路径，win用户可以在mkvtoolnix安装文件夹中找到mkvmerge.exe; Linux用户安装mkvtoolnix即可
mkvmerge_path = 'F:/Encode tools/mkvmerge.exe'
if sys.platform == "linux" or sys.platform == "linux2":
  mkvmerge_path = "mkvmerge"

default_setting_single = (['0:zh-CN'], ['0:yes'], ['0:简体中文'])   # 单字幕轨默认参数
default_setting_double = (['0:zh-CN','0:zh-TW'], ['0:yes','0:no'], ['0:简体中文','0:繁体中文'])   # 双字幕轨默认参数

def get_merge_setting(ass_list, mkv_ass_ratio):
  print('提示：存在多字幕轨时，请确保字幕按集数排序')   # 如 v1.sc1.ass, v1.sc2.ass, v1.sc3.ass, v2.sc1.ass
  print('=====请输入字幕轨参数，用逗号分隔=====')
  print('- 字幕语言: zh-CN（简中）, zh-TW（台繁）, ...')
  print('- 默认轨标记: yes, no')
  print('- 轨道名称: (自行发挥)\n')

  language_list = []
  default_track_list = []
  track_name_list = []
  for i in range(mkv_ass_ratio):
    print(f'字幕轨{i+1} ({ass_list[i]})')
    s = input('字幕语言, 默认轨标记, 轨道名称: ').replace(' ', '').split(',')
    while len(s) != 3:
      s = input('输入参数个数错误，请重新输入（输入q退出）: ').replace(' ', '').split(',')
      if s[0] == 'q':
        return
    language_list.append(f'0:{s[0]}')
    default_track_list.append(f'0:{s[1]}')
    track_name_list.append(f'0:{s[2]}')

  print('=====字幕轨参数收集完成=====')
  return (language_list, default_track_list, track_name_list)

def merge_mkv_ass(mkv_list, ass_list, source_dir, dump_dir, mkv_ass_ratio, setting):
  language_list = setting[0]
  default_track_list = setting[1]
  track_name_list = setting[2]

  for i in range(len(mkv_list)):
    mkv = mkv_list[i]
    mkv_path = os.path.join(source_dir, mkv)
    mkv_path_dump = os.path.join(dump_dir, mkv)
    os.rename(mkv_path, mkv_path_dump)
    ass_path_dump_list = []
    message = f'\n任务 {i+1}:\n视频: {mkv}'
    command = [mkvmerge_path, '--output', mkv_path, '--no-subtitles', '--no-attachments', mkv_path_dump]

    for j in range(mkv_ass_ratio):
      ass = ass_list[i * mkv_ass_ratio + j]
      ass_path = os.path.join(source_dir, ass)
      ass_path_dump = os.path.join(dump_dir, ass)
      os.rename(ass_path, ass_path_dump)
      ass_path_dump_list.append(ass_path_dump)
      message += f'\n字幕: {ass}'
      command.extend(['--language', language_list[j], '--default-track', default_track_list[j], '--track-name', track_name_list[j], ass_path_dump])

    print(message)
    subprocess.run(command)
    print(f'任务 {i+1} 混流完毕')

  print(f'\n{len(mkv_list)}个任务全部混流完毕！')

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

  if (mkv_count == 0) | (ass_count == 0):
    input(f'视频数量({mkv_count})或字幕数量({ass_count})为零，请检查后继续 [Enter]')
    return
  if (ass_count % mkv_count) != 0:
    input(f'视频数量({mkv_count})与字幕数量({ass_count})无法整除，请检查后继续 [Enter]')
    return
  
  mkv_ass_ratio = int(ass_count / mkv_count)
  if mkv_ass_ratio == 1:
    if input(f'使用默认参数？ [y/N]') == 'y':
      merge_mkv_ass(mkv_list, ass_list, source_dir, dump_dir, mkv_ass_ratio, default_setting_single)
      return
  elif mkv_ass_ratio == 2:
    if input(f'使用默认参数？ [y/N]') == 'y':
      merge_mkv_ass(mkv_list, ass_list, source_dir, dump_dir, mkv_ass_ratio, default_setting_double)
      return
    
  setting = get_merge_setting(ass_list, mkv_ass_ratio)
  merge_mkv_ass(mkv_list, ass_list, source_dir, dump_dir, mkv_ass_ratio, setting)

if __name__ == '__main__':
  # 终端模式，循环执行直到用户手动终止
  if len(sys.argv) < 2:
    merge()
    while input('再来一轮? [y/N]') == 'y':
      merge()
  # 命令行模式，依次执行参数中的目标文件夹，执行完毕后退出
  else:
    for source_dir in sys.argv[1:]:
      merge(source_dir)
