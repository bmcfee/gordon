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

from gordon.io import AudioFile
from gordon.db.model import add, commit, Album, Artist, Track, Collection, Annotation
from gordon.db.config import DEF_GORDON_DIR
from gordon.db.gordon_db import get_tidfilename, make_subdirs_and_copy
from gordon.io.mp3_eyeD3 import isValidMP3, getAllTags



log = logging.getLogger('Gordon.AudioIntake')
log.addHandler(logging.StreamHandler(sys.stdout))
log.setLevel(logging.DEBUG) #jorgeorpinel: for now, change DEBUG to INFO here to reduce verbosity (at production)


def add_track(trackpath, source=str(datetime.date.today()), gordonDir=DEF_GORDON_DIR, tag_dict=dict(), artist=None, album=None, fast_import=False, all_md=False):
    """Add track with given filename <trackpath> to database
    
         @param source: audio files data source (string)
         @param gordonDir: main Gordon directory
         @param tag_dict: dictionary of key,val tag pairs - See add_album(...).
         @param artist: The artist for this track. An instance of Artist. None if not present
         @param album: The album for this track. An instance of Album. None if not present
         @param fast_import: If true, do not calculate strip_zero length. Defaults to False
         @param all_md: use True to try to extract all metadata tags embedded in the auudio-file. Defaults to False
    """
    (path, filename) = os.path.split(trackpath) #@UnusedVariable
    (fname, ext) = os.path.splitext(filename) #@UnusedVariable

    log.debug('    Adding file "%s" of "%s" album by %s', filename, album, artist) # debug
    
    # validations
    if 'album' not in tag_dict:
        #todo: currently cannot add singleton files. Need an album which is defined in tag_dict
        log.error('    Cannot add "%s" because it is not part of an album', filename) # error
        return -1 # didn't add ------------------------------------------ return
    if not os.path.isfile(trackpath):
        log.info('    Skipping %s because it is not a file', filename) #        info
        return -1 # not a file ------------------------------------------ return
    try:
        AudioFile(trackpath).read(tlen_sec=0.01)
    except:
        log.error('    Skipping "%s" because it is not a valid audio file', filename) # error
        return -1 # not an audio file ----------------------------------- return

    # required data
    bytes = os.stat(trackpath)[stat.ST_SIZE]

    # reencode name to latin1 !!!
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
    log.debug('    Wrote track record %s to database', track.id) #              debug

    if fast_import :
        track.secs = -1
        track.zsecs = -1
    else :
        a = AudioFile(trackpath)
        [track.secs, track.zsecs] = a.get_secs_zsecs()
        
    track.path = u'%s' % get_tidfilename(track.id, ext[1:]) # creates path to insert in track

    # links track to artist & album in DB
    if artist:
        log.debug('    Linking %s to artist %s', track, artist) #               debug
        track.artist = artist.name
        track.artists.append(artist)
    if album:
        log.debug('    Linking %s to album %s', track, album) #                 debug
        track.album = album.name
        track.albums.append(album)

    commit() # save (again) the track record (this time having the track id)
    log.debug('    Wrote album and artist additions to track into database') #  debug

    # copy the file to the Gordon audio/feature data directory
    tgt = os.path.join(gordonDir, 'audio', 'main', track.path)
    make_subdirs_and_copy(trackpath, tgt)
    log.debug('    Copied "%s" to %s', trackpath, tgt) #                        debug
    
    #chek if file is mp3. if so:
    if all_md:
        if isValidMP3(trackpath):
            #extract all ID3 tags, store each tag value as an annotation type id3.[tagname]
            for tag in getAllTags(trackpath): #todo: skip basic tags already in track
                track.annotations.append(Annotation(type='id3', annotation=tag[0], value=tag[1]))


def _read_csv_tags(cwd, csv=None):
    '''Reads a csv file containing track metadata (v 1.1)
    
    # may use py comments in collection.csv file
    filename, title, artist, album, tracknum, compilation
    per line
    
    Returns a 2D dict in the form dict[<file-name>][<tag>]'''

    #todo: add a header so that the fields need not be predefined?
    #jorgeorpinel: except we do need 4 predefined or required tags to comply with the track table fields
    #              but it would be nice.

    if csv is None:
        filename = cwd
    else:
        filename = os.path.join(cwd, csv)
    
    try:
        csvfile = reader(open(filename))
    except IOError:
        log.error("  Couldn't open '%s'", csv)

    tags = dict()
    for line in csvfile: # each record (file rows)
        if len(line) < 6 : continue
        line[0] = line[0].strip()
        if not line[0] or line[0][0] == '#' : continue # if name empty or comment line
            
        #save title, artist, album, tracknum, compilation in tags[<file-name>]
        tags[line[0]] = dict()
        tags[line[0]]['filename'] = line[0] #joreorpinel: unnecessary ...
        tags[line[0]]['title']  = u'%s' % line[1].strip()
        tags[line[0]]['artist'] = u'%s' % line[2].strip()
        tags[line[0]]['album']  = u'%s' % line[3].strip()
        try:
            tags[line[0]]['tracknum'] = int(line[4])
        except:
            tags[line[0]]['tracknum'] = 0
        tags[line[0]]['compilation'] = u'%s' % line[5].strip()

    return tags

def add_album(album_name, tags_dicts, source=str(datetime.date.today()), gordonDir=DEF_GORDON_DIR, prompt_aname=False, import_md=False):
    """Add an album from a list of metadata in <tags_dicts> v "1.0 CSV"
    """
    log.debug('  Adding album "%s" - add_album()', album_name) #                debug
    
    # create set of artists from tag_dicts
    
    artists = set()
    for track in tags_dicts.itervalues():
        artists.add(track['artist'])
    
    if len(artists) == 0:
        log.debug('  Nothing to add') #                                         debug
        return  # no songs ---------------------------------------------- return
    else:
        log.debug('  %d artists in directory: %s', len(artists), artists) #     debug
    
    #add album to Album table
    log.debug('  Album has %d tracks', len(tags_dicts))
    albumrec = Album(name = album_name, trackcount = len(tags_dicts))
    match = Collection.query.filter_by(source=source) #@UndefinedVariable (Eclipse vs SQLA)
    if match.count() == 1:
        log.debug('  Matched source %s in database', match[0])
        collection = match[0]
    else:
        collection = Collection(source=source)
    albumrec.collections.append(collection)

    #if we have an *exact* string match we will use the existing artist
    artist_dict = dict()
    for artist in artists:
        match = Artist.query.filter_by(name=artist) #@UndefinedVariable (Eclipse vs SQLA)
        if match.count() == 1 :
            log.debug('Matched %s to %s in database', artist, match[0])
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
        add_track(filename, collection, gordonDir, tags_dicts[filename], artist_dict[tags_dicts[filename]['artist']], albumrec, fast_import, import_md)
        log.debug('  Added "%s"!', filename) #                                  debug

    #now update our track counts
    for aname, artist in artist_dict.iteritems() : #@UnusedVariable
        artist.update_trackcount()
        log.debug('  * Updated trackcount for artist %s', artist) #             debug
    albumrec.update_trackcount()
    log.debug('  * Updated trackcount for album %s', albumrec) #                debug
    commit()


def add_collection_from_csv_file(csvfile, source=str(datetime.date.today()), prompt_incompletes=False, doit=False, gordonDir=DEF_GORDON_DIR, fast_import=False, import_md=False):
    """Adds tracks from a CSV (file) list of file-paths.
     
    Only imports if all songs actually have same album name. 
    With flag prompt_incompletes will prompt for incomplete albums as well

    Use doit=True to actually commit the addition of songs
    """
    try:
        metadata = _read_csv_tags(csvfile)
    except:
        log.error('Error opening %s' % csvfile)
        sys.exit(1)

    # Turn metadata into a list of albums:
    albums = collections.defaultdict(dict)
    for filename, x in metadata.iteritems():
        albums[x['album']][filename] = x    #jogeorpinel: so x[<album>][<filename>] has the metadata including x[<album>][<filename>]['filename'], the file name ...

    for albumname, tracks in albums.iteritems(): # iterate album-ordered metadata (so "for each album:")
        if not doit:
            print 'Would import album "%s"' % albumname
        else:                  # tracks is a 2D dict[<file-name>][<tag>] only for that album
            add_album(albumname, tracks, source, gordonDir, prompt_incompletes, fast_import)
    
    log.info('audio_intake.py: Finished!')



def _die_with_usage() :
    print 'This program imports a set of tracks (and their corresponding metdata) listed in a csv file into the database'
    print 'Usage: '
    print 'audio_intake [flags] <source> <csvfile> [doit] [metadata]'
    print 'Flags:' 
    print '  -fast: imports without calculating zero-stripped track times.'
    print '  -noprompt: will not prompt for incomplete albums.  See log for what we skipped'
    print 'Arguments: '
    print '  <source> is the string stored to the database for source (to identify the collection) e.g. DougDec22'
    print '  <csvfile> is the csv file listing tracks to be imported'
    print '  <doit> (default 1) use 0 to test the intake harmlessly'
    print '  <metadata> (default 0) use 1 to import all metadata tags from the file'
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

    # parse arguments
    source = sys.argv[1]
    csvfile = sys.argv[2]
    try: doit = False if sys.argv[3] == 0 else True
    except: doit = True
    try: import_md = True if sys.argv[4] == 1 else False
    except: import_md = False

    log.info('audio_intake_from_csv.py: using <source>', '"'+source+'",', '<csvfile>', csvfile) #info
    add_collection_from_csv_file(csvfile, source=source, prompt_incompletes=prompt_incompletes, doit=doit, fast_import=fast_import, import_md=import_md)
    