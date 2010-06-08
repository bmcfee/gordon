#!/usr/bin/env python

# Copyright (C) 2010 Douglas Eck
#
# This file is part of Gordon.
#
# Gordon is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Gordon is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Gordon.  If not, see <http://www.gnu.org/licenses/>.

'''
Functions for importing music to Gordon database

script usage:
python audio_intake source dir [doit]
<source> is a name for the collection
<dir> is the collection physical location to browse
<doit> is an optional parameter; if False, no actual import takes
place, only verbose would-dos
'''

import os, collections, datetime, logging, stat, sys

from csv import reader

from gordon.db.model import add, commit, Album, Artist, Track, Collection
from gordon.db.gordon_db import get_tidfilename, make_subdirs_and_copy
from gordon.io import AudioFile

from gordon.db.config import DEF_GORDON_DIR

logger = logging.getLogger('gordon.audio_intake')

def add_track(trackpath, source=str(datetime.date.today()),
              gordonDir=DEF_GORDON_DIR, tag_dict=dict(), artist=None,
              album=None, fast_import=False):
    """Add track with given filename to database

         source -- audio files data source (string)
         gordonDir -- main Gordon directory
         tag_dict -- dictionary of key,val tag pairs - See add_album(...).
         artist -- The artist for this track. An instance of Artist. None if not present
         album  -- The album for this track. An instance of Album. None if not present
         fast_import -- If true, do not calculate strip_zero length. Defaults to False
    """
    (path, filename) = os.path.split(trackpath)
    (fname, ext) = os.path.splitext(filename)

    logger.debug('Adding file "%s" of "%s" album by %s', filename, album,
                 artist)
    
    # validations
    if 'album' not in tag_dict:
        #todo: currently cannot add singleton files. Need an album which is defined in tag_dict
        logger.error('Cannot add "%s" because it is not part of an album',
                     filename)
        return -1 # didn't add ------------------------------------------ return
    if not os.path.isfile(trackpath):
        logger.info('Skipping %s because it is not a file', filename)
        return -1 # not a file ------------------------------------------ return
    try:
        AudioFile(trackpath).read(tlen_sec=0.01)
    except:
        logger.error('Skipping "%s" because it is not a valid audio file',
                     filename)
        return -1 # not an audio file ----------------------------------- return

    # required data
    bytes = os.stat(trackpath)[stat.ST_SIZE]

    # reencode name to latin1
    try:
        fn_recoded = filename.decode('utf-8')
    except:
        try: fn_recoded = filename.decode('latin1')
        except: fn_recoded = 'unknown'


    # prepare data
    if tag_dict['compilation'] not in [True, False, 'True', 'False'] :
        tag_dict['compilation'] = False

    track = Track(title = tag_dict['title'],
                  artist = tag_dict['artist'],
                  album = tag_dict['album'],
                  tracknum = tag_dict['tracknum'],
                  compilation = tag_dict['compilation'],
                  otitle = tag_dict['title'],
                  oartist = tag_dict['artist'],
                  oalbum = tag_dict['album'],
                  otracknum = tag_dict['tracknum'],
                  ofilename = fn_recoded,
                  source = str(source),
                  bytes = bytes)
    # add "source" collection <-> track
    if isinstance(source, Collection):
        track.collections.append(source)

    # add data
    add(track) # needed to get a track id
    commit() #to get our track id we need to write this record
    logger.debug('Wrote track record %s to database', track.id)

    if fast_import :
        track.secs = -1
        track.zsecs = -1
    else :
        a = AudioFile(trackpath)
        [track.secs, track.zsecs] = a.get_secs_zsecs()
        
    track.path = u'%s' % get_tidfilename(track.id, ext[1:]) # creates path to insert in track

    # links track to artist & album in DB
    if artist:
        logger.debug('Linking %s to artist %s', track, artist)
        track.artist = artist.name
        track.artists.append(artist)
    if album:
        logger.debug('Linking %s to album %s', track, album)
        track.album = album.name
        track.albums.append(album)

    commit() # save (again) the track record (this time having the track id)
    logger.debug('Wrote album and artist additions to track into database')


    # copy the file to the Gordon audio/feature data directory
    tgt = os.path.join(gordonDir, 'audio', 'main', track.path)
    make_subdirs_and_copy(trackpath, tgt)
    logger.debug('Copied "%s" to %s', trackpath, tgt)


def _read_csv_tags(cwd, csv=None):
    '''Reads a csv file containing track metadata
    
    # may use py comments in collection.csv file
    filename, title, artist, album, tracknum, compilation
    per line'''

    # TODO: add a header so that the fields need not be predefined?

    if csv is None:
        filename = cwd
    else:
        filename = os.path.join(cwd, csv)
    
    try:
        csvfile = reader(open(filename))
    except IOError:
        print 'here'
        logger.error("Couldn't open '%s'", csv)

    tags = dict()
    for line in csvfile: # each record (file rows)
        if len(line) < 6 : continue
        line[0] = line[0].strip()
        if not line[0] or line[0][0] == '#' : continue # if name empty or comment line
            
        #save title, artist, album, tracknum, compilation in tags[<file name>]
        tags[line[0]] = dict()
        tags[line[0]]['filename'] = line[0]
        tags[line[0]]['title']  = u'%s' % line[1].strip()
        tags[line[0]]['artist'] = u'%s' % line[2].strip()
        tags[line[0]]['album']  = u'%s' % line[3].strip()
        try:
            tags[line[0]]['tracknum'] = int(line[4])
        except:
            tags[line[0]]['tracknum'] = 0
        tags[line[0]]['compilation'] = u'%s' % line[5].strip()

    return tags

def _empty_tags():
    tags = dict()
    tags['title'] = ''
    tags['artist'] = ''
    tags['album'] = ''
    tags['tracknum'] = 0
    tags['compilation'] = ''
    return tags

def add_album(album_name, tags_dicts, source=str(datetime.date.today()),
              gordonDir=DEF_GORDON_DIR, prompt_aname=False, fast_import=False):
    """Add a directory with audio files
        * when we do an album we need to read all files in before trying anything
        * we can't just add each track individually. We have to make Artist ids for all artists
        * we will presume that 2 songs by same artist string are indeed same artist
    """
    logger.debug('Adding album %s', album_name)
    
    artists = set()
    for track in tags_dicts.itervalues():
        artists.add(track['artist'])
    
    if len(artists) == 0:
        logger.debug('Nothing to add')
        return  # no songs ---------------------------------------------- return
    else:
        logger.debug('%d artists in directory: %s', len(artists), artists)
    
    #add our album to Album table
    logger.debug('Album has %d tracks', len(tags_dicts))
    albumrec = Album(name = album_name, trackcount = len(tags_dicts))
#    collection = None
    match = Collection.query.filter_by(source=source)
    if match.count() == 1:
        logger.debug('Matched source %s in database', match[0])
        collection = match[0]
    else:
        collection = Collection(source=source)
    albumrec.collections.append(collection)

    #if we have an *exact* string match we will use the existing artist
    artist_dict = dict()
    for artist in artists:
        match = Artist.query.filter_by(name=artist)
        if match.count() == 1 :
            logger.debug('Matched %s to %s in database', artist, match[0])
            artist_dict[artist] = match[0]
            #eckdoug: TODO what happens if match.count()>1? This means we have multiple artists in db with same 
            #name. Do we try harder to resolve which one? Or just add a new one.  I added a new one (existing code)
            #but it seems risky.. like we will generate lots of new artists.  Anyway, we resolve this in the musicbrainz 
            #resolver....
        else :
            # add our Artist to artist table
            newartist = Artist(name = artist)
            newartist.collections.append(collection)
            artist_dict[artist] = newartist

        #add artist to album (album_artist table)
        albumrec.artists.append(artist_dict[artist])

    commit() #commit these changes in order to have access to this album record when adding tracks

    #now add our tracks to album
    for filename in tags_dicts.keys() :
        add_track(filename, collection, gordonDir, tags_dicts[filename],
                  artist_dict[tags_dicts[filename]['artist']], albumrec,
                  fast_import)
        logger.debug('  Added "%s"!', filename) #                                  debug

    #now update our track counts
    for aname, artist in artist_dict.iteritems() :
        artist.update_trackcount()
        logger.debug('  * Updated trackcount for artist %s', artist) #             debug
    albumrec.update_trackcount()
    logger.debug('  * Updated trackcount for album %s', albumrec) #                debug
    commit()


def add_collection_from_csv_file(csvfile, source=str(datetime.date.today()), prompt_incompletes=False, doit=False, gordonDir=DEF_GORDON_DIR, fast_import=False):
    """recursively adds tracks from a CSV list of files.
     
    Only imports if all songs actually have same album name. 
    With flag prompt_incompletes will prompt for incomplete albums as well

    Use doit=True to actually commit the addition of songs
    """
    try:
        metadata = _read_csv_tags(csvfile)
    except:
        logger.error('Error opening %s' % csvfile)
        sys.exit(1)

    # Turn metadata into a list of albums:
    albums = collections.defaultdict(dict)
    for filename,x in metadata.iteritems():
        albums[x['album']][filename] = x

    for albumname,tracks in albums.iteritems():
        if not doit:
            print 'Would import album "%s"' % albumname
        else:
            add_album(albumname, tracks, gordonDir=gordonDir, source=source,
                      prompt_aname=prompt_incompletes, fast_import=fast_import)
    
    logger.info('audio_intake.py: Finished!')


def _die_with_usage() :
    print 'This program imports a set of tracks (and their corresponding metdata) listed in a csv file into the database'
    print 'Usage: '
    print 'audio_intake [flags] <source> <csvfile> [doit]'
    print 'Flags:' 
    print '  -fast: imports without calculating zero-stripped track times.'
    print '  -noprompt: will not prompt for incomplete albums.  See log for what we skipped'
    print 'Arguments: '
    print '  <source> is the string stored to the database for source e.g. DougDec22'
    print '  <csvfile> is the csv file listing tracks to be imported'
    print '  <doit> (default 1) use 0 to test the intake harmlessly'
    print 'More options are available by using the function add_collection()'
    sys.exit(0)                                                    # sys.exit(0)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        _die_with_usage()                                       # -> sys.exit(0)

    prompt_incompletes=True
    fast_import=False
    
    # parse flags
    while True:
        if sys.argv[1]=='-fast' :
            fast_import=True
        elif sys.argv[1]=='-noprompt' :
            prompt_incompletes=False
        else :
            break
        sys.argv.pop(1)

    # pase arguments
    source = sys.argv[1]
    csvfile = sys.argv[2]
    doit = None
    try :
        if sys.argv[3] == 0: doit = False
        else: doit = True
    except Exception :
        pass
    doit = True if doit is None else True 

    logger.info('audio_intake.py: using <source>', '"'+source+'",', '<csvfile>', csvfile) #info
    if doit is False: logger.info(' * No <doit> (3rd) argument given. Thats 0K. (Pass no args for script usage.)') #info
    add_collection_from_csv_file(csvfile, source = source, prompt_incompletes = prompt_incompletes, doit = doit, fast_import = fast_import)
    
