#!python
import os, sys, argparse, eyed3, shutil, re
from prettytable import PrettyTable
from colorama import Fore, Style
from datetime import datetime
from pathlib import Path

# for colored text
blue = Fore.BLUE
green = Fore.GREEN
red = Fore.RED
yellow = Fore.YELLOW
nc = Style.RESET_ALL

# https://realpython.com/command-line-interfaces-python-argparse
p = argparse.ArgumentParser(
        description='Set id3 tags of mp3 files, and copy to directory')
p.add_argument('action', metavar='action', type=str,
        help='action to perform, valid options: {get, set}')
p.add_argument('mp3s', metavar='mp3s', type=str, nargs='*',
        help='mp3 files to set the id3 tag for')
p.add_argument('-t', '--tags', dest='tags',
        action='store', type=str, required=False,
        default=['title', 'artist', 'album', 'disc_num', 'track_num', 'genre', 'composer'],
        help='id3 tags to set (see ')
p.add_argument('-f', '--tagsfile', dest='tagsfile',
        action='store', type=str, required=False,
        default='/tmp/id3_tags.txt',
        help='file to store/read id3 tags')
p.add_argument('-r', '--remove', action='store_true',
        help='remove files if present')
p.add_argument('-o', '--outdir', dest='outdir',
        action='store', type=str, required=False,
        default='',
        help='directory to save tagged mp3 files to (only needed for action = get)')

args = p.parse_args()
action = args.action
mp3s = args.mp3s
tags = args.tags
tagsfile = args.tagsfile
remove = args.remove
outdir = args.outdir

if action == 'get' and len(mp3s) == 0:
    print(f"{red}error:{nc} need to supply mp3s")

# if output directory not provided, set based on current date/time
if outdir == '':
    now = datetime.now()
    outdir = now.strftime('output-%y%m%d-%H%M%S')

# create table with id3 tags info for each mp3 file in `mp3s`, and write to file
def get_tags():
    # check if tags file already exists
    if os.path.isfile(tagsfile):
        if remove:
            print(f"found tags file {blue}{tagsfile}{nc}. removing...")
            os.remove(tagsfile)
        else:
            print(f"{red}error:{nc} tags file {blue}{tagsfile}{nc} already exists. "
                "remove file or set {blue}-r{nc} flag. exiting...")
            sys.exit()

    x = PrettyTable()
    x.field_names = ['filename', 'new_filename'] + tags
    x.align = 'l'

    for p in mp3s:
        # mp3s may include directories, in which case walk through
        for root, _, files in os.walk(p):
            for name in files:
                print(f'name: {name}')
                f = os.path.join(root, name)
                # for non-mp3 files, simply add filename columns
                if os.path.splitext(name)[-1] != '.mp3':
                    row = [f,f] + ['' for _ in range(len(tags))]
                else:
                    e = eyed3.load(f)
                    if e is None:
                        print(f"{red}error:{nc} could not read data from {blue}{f}{nc}. skipping...")
                        continue # bad mp3
                    row = [f,f] + [getattr(e.tag, field) for field in tags]
                x.add_row(row)

    s = x.get_string(sortby='filename')
    with open(tagsfile, 'w') as f:
        f.write(s)
        print(f"generated tags file: {green}{tagsfile}{nc}")

# use tags file to copy, rename, and set id3 tags for each mp3 file
def set_tags():
    # create output directory if not present
    if not os.path.isdir(outdir):
        os.mkdir(outdir)

    # if output directory is not empty, don't continue
    # if os.listdir(outdir):
    #     print(f"{red}error:{nc} output directory {outdir} is not empty! exiting...")
    #     sys.exit()

    f = open(tagsfile, 'r')
    f.readline() # discard first line
    columns = [s.strip() for s in f.readline().split('|')[1:-1]]
    f.readline() # discard third line also
    iorig = columns.index('filename')
    icopy = columns.index('new_filename')
    tup2 = r'\((\w+), (\w+)\)'

    while True:
        sections = f.readline().split('|')[1:-1]
        if not sections: break # last line (bottom border of table)
        vals = [s.strip() for s in sections]
        orig, copy = vals[iorig], vals[icopy]
        copypath = os.path.join(outdir, copy)
        # check that file to copy is in output directory
        if Path(outdir) in Path(copypath).parents:
            # create output directory if it doesn't exist
            copydir = os.path.dirname(copypath)
            os.makedirs(copydir, exist_ok=True)
            if not remove and os.path.isfile(copypath):
                print(f"{yellow}warning:{nc} file {blue}{copypath}{nc} already exists. "
                    "remove file or set {blue}-r{nc} flag. skipping...")
                continue
            shutil.copy(orig, copypath)
            if os.path.splitext(copy)[-1] != '.mp3':
                continue
            # set id3 tags
            e = eyed3.load(copypath)
            for i,val in enumerate(vals):
                if i != iorig and i != icopy:
                    col = columns[i]
                    # parse method depends on column type
                    if col in set(('track_num', 'disc_num')):
                        m = re.search(tup2, val)
                        num, tot = m.groups()
                        num = None if num == 'None' else int(num)
                        tot = None if tot == 'None' else int(tot)
                        setattr(e.tag, col, (num, tot))
                        continue
                    if col in set(('genre', 'composer')):
                        setattr(e.tag, col, None if val == 'None' else val)
                        continue
                    setattr(e.tag, col, val)
                    print(col, val)
                    print(getattr(e.tag, col))
            e.tag.save()
        else:
            print(f"{red}error:{nc} output file {blue}{copypath}{nc} must be in output directory {blue}{outdir}{nc}. skipping...")

if action == 'get': get_tags()
if action == 'set': set_tags()
