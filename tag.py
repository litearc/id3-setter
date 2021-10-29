#!python
import os, sys, argparse, eyed3
from prettytable import PrettyTable
from colorama import Fore, Style

# for colored text
blue = Fore.BLUE
green = Fore.GREEN
red = Fore.RED
yellow = Fore.YELLOW
nc = Style.RESET_ALL

p = argparse.ArgumentParser(
        description='Set id3 tags of mp3 files, and copy to directory')
p.add_argument('action', metavar='action', type=str,
        help='action to perform, valid options: {get, set}')
p.add_argument('mp3s', metavar='mp3s', type=str, nargs='+',
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
        help='remove id3_tags.txt file if present')
p.add_argument('-o', '--outdir', dest='outdir',
        action='store', type=str, required=True,
        help='output directory to save tagged mp3 files to')

args = p.parse_args()
action = args.action
mp3s = args.mp3s
tags = args.tags
tagsfile = args.tagsfile
remove = args.remove
outdir = args.outdir

def get_tags():
    # create output directory if not present
    cwd = os.getcwd()
    outdirpath = os.path.join(cwd, outdir)
    if not os.path.isdir(outdirpath):
        os.mkdir(outdirpath)

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
                f = os.path.join(root, name)
                i = eyed3.load(f)
                row = [f,f] + [getattr(i.tag, field) for field in tags]
                x.add_row(row)

    s = x.get_string(sortby='filename')
    with open(tagsfile, 'w') as f:
        f.write(s)
        print(f"generated tags file: {green}{tagsfile}{nc}")


def set_tags():
    pass

if action == 'get': get_tags()
if action == 'set': set_tags()
