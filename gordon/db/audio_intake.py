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

'''Functions for importing music to Gordon database'''

import os, datetime, stat, sys#, time, heapq, difflib, shutil, string, copy, random #jorgeorpinel: unused
#import pg
#from sqlalchemy.databases.postgres import PGArray #jorgeorpinel: unused
from csv import reader

from model import add, commit, Album, Artist, Track
from gordon_db import get_tidfilename, make_subdirs_and_copy
from gordon.io import mp3_eyeD3 as id3
from gordon.io import AudioFile

from config import DEF_GORDON_DIR, DEBUG





def add_mp3(mp3, source = str(datetime.date.today()), gordonDir = DEF_GORDON_DIR, id3_dict = dict(), artist = None, album = None, fast_import = False) :
    '''Add mp3 with filename <mp3> to database
         source -- audio files data source
         gordonDir -- main Gordon directory
         id3_dict -- dictionary of key,val ID3 tags pairs - See add_album(...).
         artist -- The artist for this track. An instance of Artist. None if not present
         album  -- The album for this track. An instance of Album. None if not present
         fast_import -- If true, do not calculate strip_zero length. Defaults to False
    '''
    (path, filename) = os.path.split(mp3)
    if DEBUG: print '\tAdding mp3 file "%s" of "%s" album by %s' % (filename, album, artist), '- add_mp3()' # debug
    
    
    # validations
    
    if len(id3_dict) == 0 :
        #todo: currently cannot add singleton mp3s. Need an album which is defined in id3_dict
        print '\tERROR: Cannot add "%s" because it is not part of an album' % filename
        return -1 # didn't add ------------------------------------------ return
    if not os.path.isfile(mp3) :
        if DEBUG: print '\tSkipping %s because it is not a file' % filename # debug
        return -1 # not a file ------------------------------------------ return


    # required data
    
    bytes = os.stat(mp3)[stat.ST_SIZE]
#    try: #get track length
#        eyed3_secs = int(id3.mp3_gettime(mp3)) #from mp3_eyed3 #jorgeorpinel: eyed3_secs unused 
#    except :
#        print '\tERROR: Could not read time from mp3', mp3
#        eyed3_secs = -1

    #we get odd filenames that cannot be easily encoded.  This seems to come 
    #from times when a latin-1 filesystem named files and then those filenames 
    #are brought over to a utf filesystem.
    try:
        fn_recoded = filename.decode('utf-8')
    except :
        try :
            fn_recoded = filename.decode('latin1')
        except :
            fn_recoded = 'unknown'


    # prepare data
    
    if id3_dict['compilation'] not in [True, False, 'True', 'False'] :
        id3_dict['compilation'] = False

    track = Track(title = id3_dict['title'],
                  artist = id3_dict['artist'],
                  album = id3_dict['album'],
                  tracknum = id3_dict['tracknum'],
                  compilation = id3_dict['compilation'],
                  otitle = id3_dict['title'],
                  oartist = id3_dict['artist'],
                  oalbum = id3_dict['album'],
                  otracknum = id3_dict['tracknum'],
                  ofilename = fn_recoded,
                  source = source,
                  bytes = bytes)


    # add data
    
    add(track)
    commit() #to get our track id we need to write this record
    if DEBUG: print '\tWrote track record', track.id, 'to database' # debug ---

    if fast_import :
        track.secs = -1
        track.zsecs = -1
    else :
        #FIXME: untested code for checking secs and zsecs (DSE Feb 5, 2010)
        #jorgeorpinel: well, it seems to work for mp3 files
        a = AudioFile(filename)
        [track.secs, track.zsecs] = a.get_secs_zsecs()

    track.path = u"%s" % get_tidfilename(track.id)

    #This is a bit confusing. For backwards compat #todo: clean up DB relationships
    if artist:
        if DEBUG: print '\Linking to artist', artist # debug ------------------
        track.artist = artist.name
        track.artists.append(artist)

    if album:
        if DEBUG: print '\Linking to album', album # debug --------------------
        track.album = album.name
        track.albums.append(album)

    commit() # save (again) the track record (this time)
    if DEBUG: print '\t* Wrote album and artist additions to track into database' # debug


    #copy the file to the Gordon instal audio/feature data directory
    
    tgt = os.path.join(gordonDir, 'audio', 'main', track.path)
    make_subdirs_and_copy(filename, tgt)
    if DEBUG: print '\tCopied mp3 "' + filename + '" to', tgt # debug ---------

    #stamp the file ("TID n" as an ID3v2 commment)
    id3.id3v2_putval(tgt, 'tid', 'T%i' % track.id) # writes on new audio file (the copy)

    #we update id3 tags in mp3 if necessary (from local MusicBrainz DB, when no info found)
    if track.otitle <> track.title or track.oartist <> track.artist or track.oalbum <> track.album or track.otracknum <> track.tracknum :
        #todo: install musicbrainz_db pgdb first!
        if DEBUG: print '\t(NOT) Trying to update_mp3_from_db', track.id, os.path.join(gordonDir, 'audio', 'main') # debug
#        from gordon.db.mbrainz_resolver import GordonResolver
#        gordonResolver = GordonResolver()
#        try:
#            if not gordonResolver.update_mp3_from_db(track.id, audioDir = os.path.join(gordonDir, 'audio', 'main'), doit = True) :
#                pass # if file not found ...
#        except Exception: # except for file access crashes?
#            pass

    #if not fast_import :
#        if DEBUG: print '\tCalculating features for track',track.id # debug ---
#        update_features(track.id) #jorgeorpinel: what is this?
    pass # for stupid Eclipse correct folding after comments

def add_wav(wav, source = str(datetime.date.today()), gordonDir = DEF_GORDON_DIR, tag_dict = dict(), artist = None, album = None, fast_import = False) :
    '''Add wav with filename <wav> to database
         source -- audio files data source
         gordonDir -- main Gordon directory
         tag_dict -- dictionary of key,val tag pairs - See add_album(...).
         artist -- The artist for this track. An instance of Artist. None if not present
         album  -- The album for this track. An instance of Album. None if not present
         fast_import -- If true, do not calculate strip_zero length. Defaults to False
    '''
    (path, filename) = os.path.split(wav)
    if DEBUG: print '\tAdding wav file "%s" of "%s" album by %s' % (filename, album, artist), '- add_wav()' # debug
    
    
    # validations
    
    if len(tag_dict) == 0 :
        #todo: currently cannot add singleton files. Need an album which is defined in tag_dict
        print '\tERROR: Cannot add "%s" because it is not part of an album' % filename
        return -1 # didn't add ------------------------------------------ return
    if not os.path.isfile(wav) :
        if DEBUG: print '\tSkipping %s because it is not a file' % filename # debug
        return -1 # not a file ------------------------------------------ return


    # required data
    
    bytes = os.stat(wav)[stat.ST_SIZE]

    # reencode name to latin1
    try:
        fn_recoded = filename.decode('utf-8')
    except :
        try : fn_recoded = filename.decode('latin1')
        except : fn_recoded = 'unknown'


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
                  source = source,
                  bytes = bytes)


    # add data
    
    add(track) # needed to get a track id
    commit() #to get our track id we need to write this record
    if DEBUG: print '\tWrote track record', track.id, 'to database' # debug ---

    if fast_import :
        track.secs = -1
        track.zsecs = -1
    else :
        a = AudioFile(filename)
        [track.secs, track.zsecs] = a.get_secs_zsecs()

    track.path = u'%s' % get_tidfilename(track.id, 'wav') # creates path to insert in track

    # links track to artist & album in DB
    if artist:
        if DEBUG: print '\tAttaching artist', artist # debug ------------------
        track.artist = artist.name
        track.artists.append(artist)
    if album:
        if DEBUG: print '\tAttaching album', album # debug --------------------
        track.album = album.name
        track.albums.append(album)

    commit() # save (again) the track record (this time having the track id)
    if DEBUG: print '\t* Wrote album and artist additions to track into database' # debug


    #copy the file to the Gordon instal audio/feature data directory
    
    tgt = os.path.join(gordonDir, 'audio', 'main', track.path)
    make_subdirs_and_copy(filename, tgt)
    if DEBUG: print '\tCopied wav "' + filename + '" to', tgt # debug ---------


def _prompt_aname(albumDir, tags_dicts, albums, cwd) :
    '''Used to prompt to choose an album if files in a directory have more than 1 (indicated by their tags)'''
    print albumDir + ':', 'Multiple albums found'
    print 'SONGS---'
    for dct in tags_dicts.values() :
        print ' %i album=%s artist=%s title=%s' % (dct['tracknum'], dct['album'], dct['artist'], dct['title'])

    #let user select which album name to use
    print 'ALBUM NAMES---'
    a = 1
    for album in albums :
        print a, '"' + album + '"'
        a += 1
    while True :
        ans = raw_input('Choose one (0=do not import -1=Type album name>')
        try :
            val = int(ans)
            if val == 0 :
                os.chdir(cwd)
                return False # ------------------------------------------ return False
            elif val > 0 and val <= len(albums) :
                album_name = albums[val - 1]
                print 'Using "' + album_name + '"'
                break
            elif val == -1 :
                ans = raw_input('Type name> ')
                ans2 = raw_input('Use "%s" ? (y/n)> ' % ans)
                if ans2 == 'y' :
                    album_name = ans
                    break
        except :
            pass #stay in loop
    
    return album_name # ------------------------------------------------- return album_name 

def _get_id3_dict(mp3) :
    '''Returns title, artist, album, tracknum & compilation ID3 tags from <mp3> file arg.'''
    id3_dict = dict()
    (title, artist, album, tracknum, compilation) = id3.id3v2_getval(mp3, ('title', 'artist', 'album', 'tracknum', 'compilation'))
    id3_dict['title'] = title
    id3_dict['artist'] = artist
    id3_dict['album'] = album
    try :
        id3_dict['tracknum'] = int(tracknum)
    except :
        id3_dict['tracknum'] = 0
    id3_dict['compilation'] = compilation
    return id3_dict

def _read_csv_tags(cwd, csv):
    '''Reads a csv text file with tags for WAV files
    
    filename, title, artist, album, tracknum, compilation
    per line'''
    
    tags = dict()
    
    try:
        csvfile = reader(open(os.path.join(cwd, csv)))
        for line in csvfile:
            if len(line) < 6 : continue
            if line[0][0] == '#' : continue
            
            #save title, artist, album, tracknum, compilation in tags[<file name>]
            tags[line[0]] = dict()
            tags[line[0]]['title']  = line[1]
            tags[line[0]]['artist'] = line[2]
            tags[line[0]]['album']  = line[3]
            try: tags[line[0]]['tracknum'] = int(line[4])
            except: tags[line[0]]['tracknum'] = 0
            tags[line[0]]['compilation'] = line[5]
    except IOError:
        print 'audio_intake.py: Error: Couldn\'t open "' + csv + '"'

    return tags

def add_album(albumDir, source = str(datetime.date.today()), gordonDir = DEF_GORDON_DIR, prompt_aname = False, fast_import = False):
    '''Add a directory with audio files
        * when we do an album we need to read all files in before trying anything
        * we can't just add each track individually. We have to make Artist ids for all artists
        * we will presume that 2 songs by same artist string are indeed same artist
    '''
    if DEBUG: print ' Adding album', albumDir, '- add_album()' # debug --------
    
    tags_dicts = dict()
    albums = set()
    artists = set()
    
    cwd = os.getcwd()
    os.chdir(albumDir)
    addfunction = False
    #todo: have a list of supported formats and check the actual MIME type, not only the extension
    for filename in os.listdir('.') :
        if not os.path.isdir(os.path.join(cwd, filename)) :
            if DEBUG: print '\tChecking', '"' + filename + '"...', # debug ----
            csvtags = False
            if filename.lower().endswith('.mp3') : # gets ID3 tags from mp3s
                id3tags = _get_id3_dict(filename)
                if DEBUG: print 'is MP3 w/ ID3 tags', id3tags # debug ---------
                tags_dicts[filename] = id3tags
                albums.add(id3tags['album'])
                artists.add(id3tags['artist'])
                addfunction = 'add_mp3'
            elif filename.lower().endswith('.wav') :
                if not csvtags : csvtags = _read_csv_tags(os.getcwd(), 'tags.csv')
                if DEBUG: print 'is WAV', # debug -----------------------------
                try:
                    if csvtags[filename] : print 'w/ CSV tags', csvtags[filename] # debug
                    tags_dicts[filename] = csvtags[filename]
                except: #make empty tags on the fly
                    if DEBUG: print '... nothing found in tags.csv' # debug ---
                    tags_dicts[filename] = dict()
                    tags_dicts[filename]['title'] = filename
                    tags_dicts[filename]['artist'] = ''
                    tags_dicts[filename]['album'] = ''
                    tags_dicts[filename]['tracknum'] = 0
                    tags_dicts[filename]['compilation'] = ''
                albums.add(tags_dicts[filename]['album'])
                artists.add(tags_dicts[filename]['artist'])
                addfunction = 'add_wav'
            elif DEBUG: print 'not a supported audio file format' # debug -----
            
        #todo: work with other non-mp3 audio files/tags!
    
    albums = list(albums)
    
    if len(artists) == 0 :
        os.chdir(cwd)
        print ' Nothing to add' #debug
        return  # no songs ---------------------------------------------- return
    elif DEBUG: print '', len(artists), 'artists in directory:', artists # debug
    
    if len(artists) <> 1 :  # if more than 1 artist found in ID3 tags
        if prompt_aname :
            # prompt user to choose an album
            album_name = _prompt_aname(albumDir, tags_dicts, albums, cwd)
            if album_name == False : return # why? see _prompt_aname() -- return
        else :
            os.chdir(cwd)
            print ' Not adding', len(albums),'album names in album', albumDir, albums #debug
            return  # more than one album in directory ------------------ return
    else : # there's only one album in the directory (as should be)
        album_name = albums[0]
    
    #add our album to Album table
    if DEBUG: print ' Album has', len(tags_dicts), 'recordings' #debug-
    albumrec = Album(name = album_name, trackcount = len(tags_dicts), a='1') #jorgeorpinel: a='1' ?

    #if we have an *exact* string match we will use the existing artist
    artist_dict = dict()
    for artist in set(artists) :
        match = Artist.query.filter_by(name = artist) #@UndefinedVariable #todo: remove this stupid Eclipse
        if match.count() == 1 :
            if DEBUG: print ' Matched', artist, match[0], 'in database' # debug 
            artist_dict[artist] = match[0]
        else :
            # add our Artist to artist table
            newartist = Artist(name = artist)
            artist_dict[artist] = newartist

        #add artist to album (album_artist table)
        albumrec.artists.append(artist_dict[artist])

    commit() #commit these changes #jorgeorpinel: hold it... shouldn't it commit until the very end?

    #now add our tracks to album
    for file in tags_dicts.keys() :
        tag_dict = tags_dicts[file] #@UnusedVariable becaue it is used at the following eval() call:
        # calls add_mp3(), add_wav(), or other
        eval(addfunction+"(file, source, gordonDir, tag_dict, artist_dict[tag_dict['artist']], albumrec, fast_import)")
        if DEBUG: print '\tAdded', '"' + file + '"' # debug -------------------

    #now update our track counts
#    print artist_dict
    for aname, artist in artist_dict.iteritems() :
        artist.update_trackcount()
        if DEBUG: print ' Updated trackcount for', artist # debug
    albumrec.update_trackcount()
    if DEBUG: print ' Updated trackcount for', albumrec # debug
    commit()

    os.chdir(cwd)


def add_collection(collectionDir, source = str(datetime.date.today()), prompt_incompletes = False, doit = False, iTunesDir = False, gordonDir = DEF_GORDON_DIR, fast_import = False):
    """recursively adds mp3s from a directory tree.
    treats all files in same directory as being in same album!
     
    Only imports if all songs actually have same album name. 
    With flag prompt_incompletes will prompt for incomplete albums as well

    When iTunesDir==True, add only directories of the form <collectionDir>/<artist>/<album>
    This does *not* import all songs in the tree but only those two plys deep...

    Use doit=True to actually commit the addition of songs
    """
    #When fast_import=True
    os.chdir(collectionDir)
    if DEBUG: print 'Looking for a collection in', os.sep + '. - add_collection()' # debug

    #handle root as a potential album
    if not iTunesDir :
        if not doit :
            print 'Would import .' + os.sep
        else :
            add_album('.', gordonDir = gordonDir, source = source, prompt_aname = prompt_incompletes, fast_import = fast_import)
            if DEBUG: print 'Proccessed', os.sep + '.' # debug -------------------------

    for root, dirs, files in os.walk('.') :
        if iTunesDir and len(root.split(os.sep)) <> 2 :
            print 'iTunesDir skipping (artists) directories under root', root
            continue

        for dir in dirs :
            if not doit :
                print 'Would import', root + os.sep + dir
            else :
                add_album(os.path.join(root, dir), gordonDir = gordonDir, source = source, prompt_aname = prompt_incompletes, fast_import = fast_import)
                if DEBUG: print ' Added album', os.path.join(root, dir) # debug

#    #remove empty dirs #jorgeorpinel: no! why? it only works on linux anyway
#    if doit:
#        print 'Removing any empty directories. This command will fail if none of the directories are empty. No worries'
#        os.system('find . -depth -type dir -empty -print0 | xargs -0 rmdir')
#    os.chdir(cwd)
    print 'audio_intake.py: Finished!'





def _die_with_usage() :
    print 'This program imports a directory into the database'
    print 'Usage: '
    print 'audio_intake <source> <dir>'
    print 'Arguments: '
    print '  <source> is the string stored to the database for source e.g. DougDec22'
    print '  <dir> is the directory to be imported'
    print '  <doit> (default 1) use 0 to test the intake harmlessly'
    print 'More options are available by using the function add_collection()'
    sys.exit(0)

if __name__ == '__main__':
    print 'audio_intake.py: Gordon audio intake script running...' # i
    if len(sys.argv) < 3:
        _die_with_usage()

    source = sys.argv[1]
    dir = sys.argv[2]
    doit = None
    try :
        if sys.argv[3] == 0: doit = False
        else: doit = True
    except Exception :
        pass
    doit = True if doit is None else doit   #jorgeorpinel: just trying Python's ternary opperator :p

    print 'audio_intake.py: using <source>', '"'+source+'",', '<dir>', eval("'"+dir+"'") # i
    if doit is False: print ' * No <doit> (3rd) argument given. Thats 0K (Pass no args for script usage)' # i
    add_collection(collectionDir = dir, source = source, prompt_incompletes = True, doit = doit, fast_import = False)
    
