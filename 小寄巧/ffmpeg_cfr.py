import os


def get_video_file_paths(folder_path):
    file_paths = [
        os.path.join(dirpath, filename)
        for (dirpath, _, filenames) in os.walk(folder_path)
        for filename in filenames
    ]
    video_paths = []

    for file_path in file_paths:
        if not file_path.endswith('.mkv'):
            continue
        if any(s in file_path.lower() for s in ['extra', 'sp', 'bonus']):
            continue
        video_paths.append(file_path)

    return video_paths

def run_ffmpeg(folder_path):
    crf = 18
    preset = 'medium'

    file_paths = get_video_file_paths(folder_path)

    for infile in file_paths:
        outfile = infile.replace(folder_path, folder_path + f'\\Converted-CFR{crf}')
        outfile = outfile.replace('.mkv', '.H265-CFR18.mkv')
        output_path = os.path.dirname(outfile)
        print(outfile, output_path)
        os.makedirs(output_path, exist_ok=True)

        os.system(f'ffmpeg -i "{infile}" '
                  f'-c:v libx265 -preset {preset} -crf {crf} -profile:v main10 -map_chapters 0 '
                  f'-c:a aac -b:a 128k '
                  f'"{outfile}"')


if __name__ == '__main__':
    folder_path = os.getcwd()
    run_ffmpeg(folder_path)
    input("Complete")
