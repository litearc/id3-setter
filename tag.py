#!python
import argparse, ast, os, sys, shutil
from prettytable import PrettyTable
from colorama import Fore, Style
from datetime import datetime
from pathlib import Path
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError
from mutagen import MutagenError
from functools import cmp_to_key

# print info, warning, error messages nicely ...................................

# colors
cred = Fore.RED
cblue = Fore.BLUE
cgreen = Fore.GREEN
cyellow = Fore.YELLOW
nc = Style.RESET_ALL

def red(t):
    return f'{cred}{t}{nc}'

def blue(t):
    return f'{cblue}{t}{nc}'

def green(t):
    return f'{cgreen}{t}{nc}'

def yellow(t):
    return f'{cyellow}{t}{nc}'

def info(m):
    print(f'{blue("[info]:")} {m}')

def warning(m):
    print(f'{yellow("[warning]:")} {m}')

def error(m):
    print(f'{red("[error]:")} {m}')

# default params ...............................................................

# default id3 tags to add to tags file
deftags = ['title', 'artist', 'album', 'tracknumber', 'discnumber', 'genre']

# id3 tags to remove from mp3s
deltags = ['acoustid_fingerprint', 'acoustid_id', 'albumartist',
        'albumartistsort', 'albumsort', 'arranger', 'artistsort', 'asin',
        'author', 'barcode', 'bpm', 'catalognumber', 'compilation', 'composer',
        'composersort', 'conductor', 'copyright', 'date',
        'discsubtitle', 'encodedby', 'isrc', 'language', 'length', 'lyricist',
        'media', 'mood', 'musicbrainz_albumartistid', 'musicbrainz_albumid',
        'musicbrainz_albumstatus', 'musicbrainz_albumtype',
        'musicbrainz_artistid', 'musicbrainz_discid',
        'musicbrainz_releasegroupid', 'musicbrainz_releasetrackid',
        'musicbrainz_trackid', 'musicbrainz_trmid', 'musicbrainz_workid',
        'musicip_fingerprint', 'musicip_puid', 'organization', 'originaldate',
        'performer', 'performer:*', 'releasecountry', 'replaygain_*_gain',
        'replaygain_*_peak', 'titlesort', 'version', 'website']

# parse command-line arguments .................................................

# https://realpython.com/command-line-interfaces-python-argparse
p = argparse.ArgumentParser(
        description='Set id3 tags of mp3 files, and copy to directory')

p.add_argument('action', metavar='action',
        help='action to perform, valid options: {get, set}')

p.add_argument('mp3s', metavar='mp3s', nargs='*',
        help='mp3 files to set the id3 tags for')

p.add_argument('-t', '--tags', dest='tags', default=deftags,
        help='id3 tags to set (see mutagen easyid3 tags for valid values')

p.add_argument('-d', '--delete', dest='delete', default=deltags,
        help='id3 tags to delete (see mutagen easyid3 tags for valid values')

p.add_argument('-f', '--tagsfile', dest='tagsfile',
        default='/tmp/id3_tags.txt', help='file to store/read id3 tags')

p.add_argument('-r', '--remove', action='store_true',
        help='remove files if present')

p.add_argument('-i', '--ignore', dest='ignore',
        action='store_true', help='ignore non-mp3 files')

p.add_argument('-o', '--outdir', dest='outdir', default='',
        help='directory to save mp3 files to (only needed for action = get)')

p.add_argument('-v', '--verbosity', dest='verbosity', default=2,
        help='verbosity level (0: +errors, 1: +warnings, 2: +info)')

args = p.parse_args()
action = args.action
mp3s = args.mp3s
tags = args.tags
delete = args.delete
tagsfile = args.tagsfile
ignore = args.ignore
remove = args.remove
outdir = args.outdir
verbosity = int(args.verbosity)

if action == 'get' and len(mp3s) == 0:
    error(f'need to supply mp3s')

# if output directory not provided, set based on current date/time
if outdir == '':
    now = datetime.now()
    outdir = now.strftime('output-%y%m%d-%H%M%S')

# "get" action .................................................................

# create table with id3 tags info for each mp3 file in `mp3s`, and write to file
def get_tags():
    # check if tags file already exists
    if os.path.isfile(tagsfile):
        if remove:
            if verbosity >= 2:
                info(f'found tags file {green(tagsfile)}. removing...')
                os.remove(tagsfile)
        else:
            if verbosity >= 0:
                error(f'tags file {green(tagsfile)} already exists. '
                    f'remove file or set {yellow("-r")} flag. exiting...')
            sys.exit()

    x = PrettyTable()
    x.field_names = ['filename', 'newfilename'] + tags
    x.align = 'l'

    for p in mp3s:
        # mp3s may include directories, in which case walk through
        for root, _, files in os.walk(p):
            for name in files:
                f = os.path.join(root, name)
                r = repr(f)
                # for non-mp3 files, simply add filename columns
                if os.path.splitext(name)[-1] != '.mp3' and not ignore:
                    row = [r,r] + ['' for _ in range(len(tags))]
                else:
                    try:
                        e = EasyID3(f)
                        row = [r,r] + [(repr(e[field] if len(e[field])>1 else
                            e[field][0]) if field in e else '') for field in tags]
                    except MutagenError as e:
                        if verbosity >= 1:
                            warning(f'could not read id3 tags for {green(f)}. writing empty tag...')
                        row = [r,r] + ['' for _ in range(len(tags))]
                    x.add_row(row)

    # sort by album, then discnumber, then tracknumber (if these columns are
    # present, otherwise sort by file path)
    def sortfn(a, b):
        find = lambda arr, item: arr.index(item) if item in arr else -1
        # the '+3' below is because we add [filename, newfilename] columns, and
        # prettytable adds the "sortby" column so 3 columns in total
        ialbum = find(tags, 'album')+3
        idisc = find(tags, 'discnumber')+3
        itrack = find(tags, 'tracknumber')+3
        # val = lambda x: int(ast.literal_eval(x))
        def val(x):
            if '/' in x: x = x[:x.index('/')] + x[0]
            try: return int(ast.literal_eval(x))
            except BaseException: return float('inf')
            # if x == '': return float('inf')
            # return int(ast.literal_eval(x))
        if ialbum >= 0 and a[ialbum] != b[ialbum]:
            return +1 if a[ialbum] > b[ialbum] else -1
        if idisc >= 0 and val(a[idisc]) != val(b[idisc]):
            return val(a[idisc]) - val(b[idisc])
        if itrack >= 0 and val(a[itrack]) != val(b[itrack]):
            return val(a[itrack]) - val(b[itrack])
        return +1 if a[1] > b[1] else -1

    s = x.get_string(sortby='filename', sort_key=cmp_to_key(sortfn))
    with open(tagsfile, 'w') as f:
        f.write(s)
        if verbosity >= 2:
            info(f'generated tags file: {green(tagsfile)}')

# "set" action .................................................................

# use tags file to copy, rename, and set id3 tags for each mp3 file
def set_tags():
    # create output directory if not present
    if not os.path.isdir(outdir):
        os.mkdir(outdir)

    f = open(tagsfile, 'r')
    f.readline() # discard first line
    columns = [s.strip() for s in f.readline().split('|')[1:-1]]
    f.readline() # discard third line also
    iorig = columns.index('filename')
    icopy = columns.index('newfilename')

    while True:
        sections = f.readline().split('|')[1:-1]
        if not sections: break # last line (bottom border of table)
        vals = [s.strip() for s in sections]
        orig, copy = ast.literal_eval(vals[iorig]), ast.literal_eval(vals[icopy])
        copypath = os.path.join(outdir, copy)
        # check that file to copy is in output directory
        if Path(outdir) in Path(copypath).parents:
            # create output directory if it doesn't exist
            copydir = os.path.dirname(copypath)
            os.makedirs(copydir, exist_ok=True)
            if not remove and os.path.isfile(copypath):
                if verbosity >= 1:
                    warning(f'{green(copypath)} already exists. '
                        f'remove file or set {yellow("-r")} flag. skipping...')
                continue
            shutil.copy(orig, copypath)
            if os.path.splitext(copy)[-1] != '.mp3':
                continue
            try:
                e = EasyID3(copypath)
            except ID3NoHeaderError:
                e = EasyID3()
            for i,val in enumerate(vals):
                if i != iorig and i != icopy:
                    col = columns[i]
                    e[col] = '' if val == '' else ast.literal_eval(val)
            for key in delete:
                if key in e and key not in columns:
                    del e[key]
            e.save(copypath)
        else:
            if verbosity >= 1:
                warning(f'output file {green(copypath)} must be in output directory {green(outdir)}. skipping...')

if action == 'get': get_tags()
if action == 'set': set_tags()
