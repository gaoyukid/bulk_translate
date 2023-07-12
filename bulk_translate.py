import argparse
import subprocess
import os, sys
import glob
import logging
from split_translate import split_files_and_translate, default_subtitle_type_str
from translate import bake_subtitle, find_or_create_subtitle
default_suffix_types_str = ','.join(['mp4', 'avi'])

logging.basicConfig(stream=sys.stdout, level=logging.INFO)




def get_file_iterators(root_path: str):
    target_path = os.path.join(root_path, '**')
    return glob.iglob(target_path, recursive=True)

def translate_files(root_path, subtitle_root_path, dest_dir, force, suffix_types, length, clean):
    logging.info(f'root: {root_path}, subtitle_root_path: {subtitle_root_path}, dest_dir: {dest_dir}, force: {force}')
    total = 0
    changed = 0
    error = 0
    translate_results = {}
    for fp in get_file_iterators(root_path):
        fp_suffix = os.path.basename(fp).split('.')[-1] if not os.path.isdir(fp) else None
        if fp_suffix in suffix_types:
            total += 1
            if length > 0:
                try:
                    result = split_files_and_translate(fp, dest_dir, tmp_dir=None, length=length, 
                                                       force=force, suffix_type=default_subtitle_type_str, 
                                                       clean=clean) # should always clean up
                    changed += 1
                except Exception as ex:
                    error += 1
                    logging.error(f'error translating {fp} with ex: ' + str(ex))
            else:
                subtitle_path = find_or_create_subtitle(fp, subtitle_root_path=subtitle_root_path)
                if not subtitle_path:
                    error += 1
                else:
                    try:
                        logging.info(f'start translating {fp}')
                        result = bake_subtitle(fp, subtitle_path, dest_dir=dest_dir, force=force)
                        changed += 1
                    except Exception as ex:
                        error += 1
                        logging.error(f'error translating {fp} with ex: ' + str(ex))
        

    logging.info(f'operation complete, {changed} changed, {error} errors, {total} in total')

def main():
    parser = argparse.ArgumentParser('bulk_translate')
    parser.add_argument('-r', '--root', dest='root', type=str, help='root of the dir to translate')
    parser.add_argument('-sp', '--subtitle-path', dest='subtitle_path', type=str, help='root of the subtitle dir')
    parser.add_argument('-o', '--dest-dir', dest='dest_dir', type=str, help='output dir')    
    parser.add_argument('-l', '--length', dest='length', type=int, default=0, help='split length in min, default to 0 means no split')
    parser.add_argument('-f', '--force', dest='force', type=bool, default=False, help='force operation or skip if already exists')
    parser.add_argument('-c', '--clean', dest='clean', action='store_true', help='clean up tmp dir')
    parser.add_argument('--suffix', dest='suffix_types', type=str, default=default_suffix_types_str, 
                        help=f'comma-separated suffix types to include, default to {default_suffix_types_str}')
    args = parser.parse_args()
    subtitle_root_path = args.subtitle_path
    suffix_types = args.suffix_types.split(',')
    dest_dir = args.dest_dir
    if not subtitle_root_path:
        subtitle_root_path = dest_dir
    root_path = args.root
    length = args.length
    force = args.force
    clean=args.clean
    if not root_path:
        # use where the script is
        # would be interesting to see what happens when
        # it is an exe
        root_path = os.path.dirname(__file__)
    translate_files(root_path, subtitle_root_path, dest_dir, force, suffix_types, length, clean)

if __name__ == '__main__':
    main()



