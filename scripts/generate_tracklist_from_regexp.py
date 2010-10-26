#!/usr/bin/env python

"""Generates a tracklist file for use by gordon's audio_intake scripts

Usage:  generate_tracklist_from_regexp <pattern> <outputfilename> file1 file2 ...

Extracts metadata from each of the given filenames using the specified
regexp pattern to generate a tracklist.  The pattern must name
matching groups with the names "artist", "album", "title", "tracknum",
or "compilation" to fill in the corresponding track metadata fields.

For example, the pattern:
'.*/(?P<artist>.*)-(?P<album>.*)-(?P<tracknum>[0-9]*)-(?P<title>.*)\.'
will match filenames of the form:
/path/to/artist name-album name-track number-title.mp3

For more information about Python regular expressions, see the
documentation for the re module at http://docs.python.org/library/re.html

Note that this script *does not* support gordon annotations.  You must
add them to the generated tracklist manually using e.g. sed.


Example Usage:

generate_tracklist_from_regexp \
    '.*/audio/(?P<artist>The Beatles)/.*_-_(?P<album>.*)/(?P<tracknum>[0-9]*)_-_(?P<title>.*)\.' \
    tracklist.csv \
    ~/data/beatles/audio/The\ Beatles/*/*wav

creates tracklist.csv:

# Header:
filepath,title,artist,album,tracknum,compilation
# Extracting metadata using regular expression: .*/audio/(?P<artist>The Beatles)/.*_-_(?P<album>.*)/(?P<tracknum>[0-9]*)_-_(?P<title>.*)\.
# Tracklist:
/home/ronw/data/beatles/audio/The Beatles/01_-_Please_Please_Me/01_-_I_Saw_Her_Standing_There.wav,I_Saw_Her_Standing_There,The Beatles,Please_Please_Me,01,False
/home/ronw/data/beatles/audio/The Beatles/01_-_Please_Please_Me/02_-_Misery.wav,Misery,The Beatles,Please_Please_Me,02,False
/home/ronw/data/beatles/audio/The Beatles/01_-_Please_Please_Me/03_-_Anna_(Go_To_Him).wav,Anna_(Go_To_Him),The Beatles,Please_Please_Me,03,False
...
/home/ronw/data/beatles/audio/The Beatles/12_-_Let_It_Be/11_-_For_You_Blue.wav,For_You_Blue,The Beatles,Let_It_Be,11,False
/home/ronw/data/beatles/audio/The Beatles/12_-_Let_It_Be/12_-_Get_Back.wav,Get_Back,The Beatles,Let_It_Be,12,False

Author: Ron Weiss <ronw@nyu.edu>
"""

import codecs
import re
import sys


def extract_metadata_from_filename(filename, pattern):
    tagdict = dict(title=None, artist=None, album=None, tracknum=-1,
                   compilation=False)
    
    m = re.match(pattern, filename)
    if m:
        for key, val in m.groupdict().iteritems():
            tagdict[key] = val

    return tagdict

def process_files(filenames, pattern, outfile):
    keys = ('title', 'artist', 'album', 'tracknum', 'compilation')
    outfile.write('# Header:\nfilepath,%s\n' % ','.join(keys))
    outfile.write('# Extracting metadata using regular expression: %s\n'
                  % pattern)
    outfile.write('# Tracklist:\n')
    for filename in filenames:
        print >> sys.stderr, 'Processing %s' % filename
        tagdict = extract_metadata_from_filename(filename, pattern)
        tags = ','.join('"%s"' % unicode(tagdict[k]) for k in keys)
        outfile.write('"%s",%s\n' % (filename, tags))

def main(pattern, outputfilename, files):
    outfile = codecs.open(outputfilename, 'w', encoding='utf-8')
    outfile.write('# -*- coding: UTF-8 -*-\n')
    files = process_files(files, pattern, outfile)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print __doc__
        sys.exit(0)
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
