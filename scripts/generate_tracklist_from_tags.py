#!/usr/bin/env python

"""Generates a tracklist file for use by gordon's audio_intake scripts

Usage:  generate_tracklist_from_tags <dir> [outputfilename]

Searches all audio files under the specified directory and extracts
artist/album/etc. metadata from the e.g. ID3 tags embedded in the
file.  If outputfilename is not specified, the tracklist is printed to
stdout.

Note that this script *does not* support gordon annotations.  You must
added them to the generated tracklist manually using e.g. sed.

Author: Ron Weiss <ronw@nyu.edu>
"""

import os
import sys

try:
    import tagpy
except ImportError:
    pass

try:
    from gordon.io import mp3_eyeD3
except ImportError:
    pass


def read_tags_using_tagpy(filename):
    fileref = tagpy.FileRef(filename)
    tag = fileref.tag()
    compilation = extract_compilation_flag_using_tagpy(fileref)
    tagdict =  dict(title=tag.title, artist=tag.artist, album=tag.album,
                    tracknum=tag.track, compilation=compilation)
    return tagdict

def extract_compilation_flag_using_tagpy(fileref):
    """Copies the behavior of mp3_eyeD3.id3v2_getval_sub"""
    compilation = False
    try:
        framelistmap = fileref.file().ID3v2Tag().frameListMap()
        for frame in framelistmap['TCMP']:
            if frame.toString()  == u'1':
                compilation = True
                break
    except:
        pass
    return compilation

def read_tags_using_eyeD3(filename):
    tagnames = ('title', 'artist', 'album', 'tracknum', 'compilation')
    tagdict = dict((x, mp3_eyeD3.id3v2_getval(filename, x)) for x in tagnames)
    return tagdict

def read_tags(filename):
    try:
        tagdict = read_tags_using_tagpy(filename)
    except ValueError:
        tagdict = read_tags_using_eyeD3(filename)
    return tagdict

def walk_music_dir(musicdir, outfile):
    keys = ('title', 'artist', 'album', 'tracknum', 'compilation')
    outfile.write('# Header:\nfilepath,%s\n# Tracklist:\n' % ','.join(keys))

    for dirpath, dirnames, filenames in os.walk(musicdir):
        outfile.write('# Directory %s\n' % dirpath)
        for filename in sorted(filenames):
            fn = os.path.join(dirpath, filename)
            try:
                print >> sys.stderr, 'Processing %s' % fn
                tagdict = read_tags(fn)
                outfile.write('"%s",%s\n' % (filename,
                                             ','.join('"%s"' % str(tagdict[k])
                                                      for k in keys)))
            except (ValueError, NameError):
                print >> sys.stderr, 'Error reading %s' % fn


def main(musicdir='.', outputfilename=None):
    if outputfilename:
        outfile = open(outputfilename, 'w')
    else:
        outfile = sys.stdout
    files = walk_music_dir(musicdir, outfile)


if __name__ == "__main__":
    if not 2 <= len(sys.argv) <= 3:
        print __doc__
        sys.exit(0)
    main(*sys.argv[1:])
