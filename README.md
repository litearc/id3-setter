# ID3 setter

This tool allows you to:
- Extract id3 tags into a text file in a table format (call this the "get" step)
- Set id3 tags from a text file with the same format (call this the "set" step)

Together, these two functionalities allow you to easily edit the id3 tags of mp3
files, assuming you can edit the files efficiently (since otherwise it would be
easier to just use a different approach). In vim, I've found that a combination
of macros, visual-block mode, and a plugin to align text highly effective.

Here is an example workflow:

First, extract id3 tags to a file (default output path is: `/tmp/id3_tags.txt`)
```
./tag.py -r get "path-to-ost-folder"
```

Open the file in a text editor (here we use vim but you can use another editor)
```
vim /tmp/id3_tags.txt
```

Let's say it looks like:

```
+---------------------------------+---------------------------------+----------------+---------------+------------+-------------+------------+--------+
| filename                        | newfilename                     | title          | artist        | album      | tracknumber | discnumber | genre  |
+---------------------------------+---------------------------------+----------------+---------------+------------+-------------+------------+--------+
| 'ost-path/101-prologue.mp3'     | 'ost-path/101-prologue.mp3'     | 'Prologue'     | 'Artist Name' | 'OST Name' |             |            | 'Game' |
| 'ost-path/102-opening.mp3'      | 'ost-path/102-opening.mp3'      | 'Opening'      | 'Artist Name' | 'OST Name' |             |            | 'Game' |
| 'ost-path/201-battle.mp3'       | 'ost-path/201-battle.mp3'       | 'Battle'       | 'Artist Name' | 'OST Name' |             |            | 'Game' |
| "ost-path/202-battle's end.mp3" | "ost-path/202-battle's end.mp3" | "Battle's End" | 'Artist Name' | 'OST Name' |             |            | 'Game' |
+---------------------------------+---------------------------------+----------------+---------------+------------+-------------+------------+--------+
```

The `filename` column shows the input file paths (don't edit these since the
tool uses them to find the mp3 files in the "set" step). The `newfilename`
column contains, for each file, the path (relative to an output directory
specified in the "set" command) the file is copied to before editing the id3
tags. This can also be used to rename the input files. The rest of the columns
correspond to id3 tags (they use the same names as mutagen's EasyID3). All the
values need to be valid python strings (you may need to use single or double
quoted strings or even `\'` and `\"` depending on if the field contains `'` or
`"`).

Here, notice that the `tracknumber` and `discnumber` columns are empty, but the
information is in the filename, i.e. the first (100's) digit contains the
discnumber and the next two contain the tracknumber. In vim, using visual-block
copy/paste, it's pretty easy to modify the table to:

```
+---------------------------------+---------------------------------+----------------+---------------+------------+-------------+------------+--------+
| filename                        | newfilename                     | title          | artist        | album      | tracknumber | discnumber | genre  |
+---------------------------------+---------------------------------+----------------+---------------+------------+-------------+------------+--------+
| 'ost-path/101-prologue.mp3'     | 'ost-path/101-prologue.mp3'     | 'Prologue'     | 'Artist Name' | 'OST Name' | '1'         | '1'        | 'Game' |
| 'ost-path/102-opening.mp3'      | 'ost-path/102-opening.mp3'      | 'Opening'      | 'Artist Name' | 'OST Name' | '2'         | '1'        | 'Game' |
| 'ost-path/201-battle.mp3'       | 'ost-path/201-battle.mp3'       | 'Battle'       | 'Artist Name' | 'OST Name' | '1'         | '2'        | 'Game' |
| "ost-path/202-battle's end.mp3" | "ost-path/202-battle's end.mp3" | "Battle's End" | 'Artist Name' | 'OST Name' | '2'         | '2'        | 'Game' |
+---------------------------------+---------------------------------+----------------+---------------+------------+-------------+------------+--------+
```

Here, we've copied the track/disc numbers from the filenames.
Let's copy the files to the folder 'output' and set the id3 tags:
```
./tag.py -t /tmp/id3_tags.txt -r -i -o output set
```

And we're done! The mp3 files with the new id3 tags will be
located in the folder `output/ost-path`.

