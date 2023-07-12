import argparse
import subprocess
import os, sys
import re
import logging


default_suffix_types_str = ','.join(['mp4', 'avi'])

logging.basicConfig(stream=sys.stdout, level=logging.INFO)





def find_subtitle_path(filename, subtitle_root_path, suffix='srt'):
    file_base_name = os.path.basename(filename)
    subtitle_base_name = '.'.join(file_base_name.split('.')[0:-1]) + '.' + suffix
    if subtitle_base_name in os.listdir(subtitle_root_path):
        return os.path.join(subtitle_root_path, subtitle_base_name)
    else:
        return None

class Duration(object):
    # using minutes for now
    def __init__(self, hours, minutes, seconds, microseconds):
        self.ori_hours = int(hours)
        self.ori_minutes = int(minutes)
        self.ori_seconds = int(seconds)
        self.ori_microseconds = int(microseconds)
        
    def split(self, length, calibur='minutes'):

        def output_format(input_minutes):
            _hours = int( input_minutes / 60 )
            _minutes = input_minutes % 60
            return f'{_hours}:{_minutes}:00'
        minutes = 60 * self.ori_hours + self.ori_minutes
        pointer = 0
        count = 0
        while minutes > pointer:
            start = output_format(pointer)
            pointer += length
            end = output_format(pointer) if minutes > pointer else None
            yield (start, end, count)
            count += 1


def get_video_duration(video_input: str):
    'Duration: 02:55:32.63, start: 0.000000,'
    result = None
    pattern = r".+Duration: (\d\d):(\d\d):(\d\d).(\d\d),.+"
    cmd = f'ffmpeg -i {video_input}'
    output = subprocess.getoutput(cmd)
    m = re.match(pattern, output.replace('\n', ''))
    if m:
        hours = m.group(1)
        minutes = m.group(2)
        seconds = m.group(3)
        microseconds = m.group(4)
        result = Duration(hours, minutes, seconds, microseconds)
    return result

def split_video(video_input: str, duration: Duration, length: int, dest_dir: str, force=False):
    result = []
    file_base_name = os.path.basename(video_input)
    for start,end,part in duration.split(length):
        dest_file_base_name = '.'.join(file_base_name.split('.')[0:-1]) + f'.part{part}.mp4' # have to use mp4 so far
        dest_filename = os.path.join(dest_dir, dest_file_base_name)
        cmd = None
        if end:
            cmd = f'ffmpeg -ss {start} -to {end} -i {video_input} -c copy {dest_filename}'
        else:
            cmd = f'ffmpeg -ss {start} -i {video_input} -c copy {dest_filename}'
        if not os.path.exists(dest_filename) or force:
            logging.info(f'running cmd: {cmd}')
            subprocess.run(cmd)
        else:
            logging.warning(f'{dest_filename} exists already, skip cmd {cmd}')
        result.append(dest_filename)
    return result

def main():
    parser = argparse.ArgumentParser('split video')
    parser.add_argument('-i', '--input', dest='input', type=str, help='video to be splitted')
    parser.add_argument('-o', '--dest-dir', dest='dest_dir', type=str, default=None, help='output dir, default to the same dir as input video')
    parser.add_argument('-l', '--length', dest='length', type=int, default=10, help='split length in min, default to 10')
    parser.add_argument('-f', '--force', dest='force', type=bool, default=False, help='force operation or skip if already exists')
    parser.add_argument('--suffix', dest='suffix_types', type=str, default=default_suffix_types_str, 
                        help=f'comma-separated suffix types to include, default to {default_suffix_types_str}')
    args = parser.parse_args()
    dest_dir = args.dest_dir
    video_input = args.input
    length = args.length
    force = args.force
    if not dest_dir:
        dest_dir = os.path.dirname(video_input)
    logging.info(f'input: {video_input}, dest_dir: {dest_dir}')
    duration = get_video_duration(video_input)
    output_files = split_video(video_input, duration, length, dest_dir, force)
    logging.info(f'operation complete, {len(output_files)} created')

    #logging.info(f'operation complete, {changed} changed, {error} errors, {total} in total')

if __name__ == '__main__':
    main()



