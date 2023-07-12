import argparse
import subprocess
import os, sys
import glob
import logging


default_suffix_types_str = ','.join(['mp4', 'avi'])

logging.basicConfig(stream=sys.stdout, level=logging.INFO)



def bake_subtitle(filename, subtitle_path, dest_dir, force=False):
    result = None
    file_base_name = os.path.basename(filename)
    dest_file_base_name = '.'.join(file_base_name.split('.')[0:-1]) + '.translated.mp4' # have to use mp4 so far
    dest_filename = os.path.join(dest_dir, dest_file_base_name)
    subtitle_path_linux = subtitle_path.replace('\\', '/')
    cmd = f'ffmpeg -i {filename} -vf "subtitles={subtitle_path_linux}" {dest_filename}'
    #cmd = f'ffmpeg -i {filename} -i {subtitle_path} -c copy -c:s mov_text -metadata:s:s:0 language=eng {dest_filename}'
    if not os.path.exists(dest_filename) or force:
        logging.info(f'running cmd: {cmd}')
        result = subprocess.run(cmd)
    else:
        logging.warning(f'{dest_filename} exists already, skip')
    return dest_filename

def find_or_create_subtitle(filename, subtitle_root_path, suffix='srt'):
    file_base_name = os.path.basename(filename)
    subtitle_base_name = '.'.join(file_base_name.split('.')[0:-1]) + '.' + suffix
    result = None
    if subtitle_base_name in os.listdir(subtitle_root_path):
        result = os.path.join(subtitle_root_path, subtitle_base_name)
    else:
        try:
            cmd = f'whisper {filename} --language ja --task translate --output_dir {subtitle_root_path} --model medium'
            subprocess.run(cmd)
            result = os.path.join(subtitle_root_path, subtitle_base_name)
        except Exception as ex:
            logging.error(f'error translating {filename}: {str(ex)}')
    return result

