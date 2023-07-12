import argparse

import os, sys, re, shutil

import logging
from split_video import get_video_duration, split_video
from translate import find_or_create_subtitle, bake_subtitle
default_subtitle_type_str = 'srt'

logging.basicConfig(stream=sys.stdout, level=logging.INFO)




'''
1
00:00:00,000 --> 00:00:02,000
This is the end of the video.

2
00:00:02,000 --> 00:00:04,000
Thank you for watching until the end.

'''


class SrtRecord(object):

    def __init__(self, index=None, start=None, end=None, text=None):
        self.index = index
        self.start = start
        self.end = end
        self.text = text

    def convert_to_srt_content(self):
        return f"{self.index}\n{self.start} --> {self.end}\n{self.text}\n\n"
    
    def offset_by_minutes(self, index_offset: int, time_offset: int):

        def offset_time_str(time_str):
            new_time_str = None
            time_pattern = r"(\d\d):(\d\d):(\d\d),(\d+)"
            m = re.match(time_pattern, time_str)
            if m:
                hour = int(m.group(1))
                minute = int( m.group(2) )
                second_str = m.group(3)
                millisecond_str = m.group(4)
                minute += time_offset
                if minute > 60:
                    hour += int(minute / 60)
                    minute = minute % 60
                hour_str = f'0{hour}' if hour < 10 else f'{hour}'
                minute_str = f'0{minute}' if minute < 10 else f'{minute}'
                new_time_str = f"{hour_str}:{minute_str}:{second_str},{millisecond_str}"
            else:
                raise Exception(f'cannot parse {time_str} by pattern {time_pattern}')
            
            return new_time_str
        
        self.index = int(self.index) + index_offset
        self.start = offset_time_str(self.start)
        self.end = offset_time_str(self.end)

    @classmethod
    def parse_content(cls, input_file):
        index_pattern = r"^(\d+)$"
        counter = 0
        result = []
        record = None
        with open(input_file) as f:
            #line = f.readline()
            for line in f:
                line = line.rstrip()
                if counter == 2:
                    # start and end
                    start_end_strs = line.split(' --> ')
                    if len(start_end_strs) == 2:
                        counter -= 1
                        record.start = start_end_strs[0]
                        record.end = start_end_strs[1]
                    else:
                        logging.warning(f'expect start end str, but got {line}')
                elif counter == 1:
                    # text str
                    text = line
                    record.text = text
                    counter -= 1
                    result.append(record)
                    record = None
                else:
                    # new start
                    m = re.match(index_pattern, line)
                    if m:
                        # match index pattern
                        index = int(m.group(1))
                        counter = 2
                        record = SrtRecord()
                        record.index = index
        return result

def split_files_and_translate(video_input, dest_dir, tmp_dir, length, force, suffix_type, clean):
    if not dest_dir:
        dest_dir = os.path.dirname(video_input)
    if not tmp_dir:
        tmp_dir = os.path.join(dest_dir, '_parts')

    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir, exist_ok=True)

    logging.info(f'input: {video_input}, dest_dir: {dest_dir}, tmp_dir: {tmp_dir}')
    duration = get_video_duration(video_input)
    output_files = split_video(video_input, duration, length, tmp_dir, force)
    logging.info(f'split_video operation complete, {len(output_files)} created in {tmp_dir}')
    subtitle_files = []
    logging.info(f'start find_or_create_subtitle for {len(output_files)} videos')

    for fp in output_files:
        subtitle_path = find_or_create_subtitle(fp, subtitle_root_path=tmp_dir, suffix=suffix_type)
        subtitle_files.append(subtitle_path)
    logging.info(f'finish find_or_create_subtitle with {len(subtitle_files)} subtitle_files in {tmp_dir}')
    merged_subtitle_path = os.path.join(dest_dir, os.path.basename(video_input).split('.')[0] + f'.{suffix_type}' )

    with open(merged_subtitle_path, 'w') as f:
        logging.info(f'start merging {len(subtitle_files)} subtitles into {merged_subtitle_path}')
        last_index_offset = 0
        for idx, sf in enumerate(subtitle_files):
            srt_records = SrtRecord.parse_content(sf)
            time_offset = idx * length
            for sr in srt_records:
                sr.offset_by_minutes(index_offset = last_index_offset, time_offset = time_offset)
                f.write(sr.convert_to_srt_content())
            last_index_offset = srt_records[-1].index

    logging.info(f'start baking {merged_subtitle_path} into {video_input}')
    result = bake_subtitle(video_input, merged_subtitle_path, dest_dir=dest_dir, force=force)
    logging.info(f'final video {result} with subtitle {merged_subtitle_path}')

    if clean:
        shutil.rmtree(tmp_dir)
    return result

def main():
    parser = argparse.ArgumentParser('split video then translate')
    parser.add_argument('-i', '--input', dest='input', type=str, help='video to be splitted')
    parser.add_argument('-o', '--dest-dir', dest='dest_dir', type=str, default=None, help='output dir, default to the same dir as input video')
    parser.add_argument('-tmp', '--tmp-dir', dest='tmp_dir', type=str, default=None, help='tmp dir, default to the sub dir "_parts" as input video')
    parser.add_argument('-c', '--clean', dest='clean', action='store_true', help='clean up tmp dir')
    parser.add_argument('-l', '--length', dest='length', type=int, default=10, help='split length in min, default to 10')
    parser.add_argument('-f', '--force', dest='force', action='store_true', help='force operation or skip if already exists')
    parser.add_argument('--suffix', dest='suffix_type', type=str, default=default_subtitle_type_str, 
                        help=f'comma-separated suffix types to include, default to {default_subtitle_type_str}')
    
    args = parser.parse_args()
    dest_dir = args.dest_dir
    tmp_dir = args.tmp_dir
    video_input = args.input
    length = args.length
    force = args.force
    suffix_type = args.suffix_type
    clean = args.clean

    if suffix_type != 'srt':
        raise Exception(f'suffix_type {suffix_type} not supported yet')
    
    
    split_files_and_translate(video_input, dest_dir, tmp_dir, length, force, suffix_type, clean)


if __name__ == '__main__':
    main()



