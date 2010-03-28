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

#from numpy.distutils.fcompiler import pg #before import pg #jorgeorpinel: more specific import path

#from sqlalchemy.databases.postgres import PGArray #jorgeorpinel: unused

from model import add, commit, Album, Artist, Track

from gordon_db import get_tidfilename, make_subdirs_and_copy
from gordon.io import mp3_eyeD3 as id3
from gordon.io import AudioFile

from config import DEF_GORDON_DIR





def add_mp3(mp3, source = str(datetime.date.today()), gordonDir = DEF_GORDON_DIR, id3_dict = dict(), artist = None, album = None, fast_import = False) :
    '''Add mp3 with filename <mp3> to database
         source -- audio files data source
         gordonDir -- main Gordon directory
         id3_dict -- dictionary of key,val ID3 tags pairs - See add_album(...).
         artist -- The artist for this track. An instance of Artist. None if not present
         album  -- The album for this track. An instance of Album. None if not present
         fast_import -- If true, do not calculate strip_zero length. Defaults to False
    '''
    (path, filename) = os.path.split(mp3) #todo: path unused (but filename very used)
    print '\tAdding mp3 file "%s" of "%s" album by %s' % (filename, album, artist) # debug
    
    # validations
    
    if len(id3_dict) == 0 :
        #todo: currently cannot add singleton mp3s. Need an album which is defined in id3_dict
        print '\tERROR: Cannot add "%s" because it is not part of an album' % filename
        return -1 # didn't add ------------------------------------------ return
    if not os.path.isfile(mp3) :
        print '\tSkipping %s because it is not a file' % filename # should be validated before the call to this function
        return -1 # not a file ------------------------------------------ return

    # required data
    
    bytes = os.stat(mp3)[stat.ST_SIZE]
#    try: #get track length
#        eyed3_secs = int(id3.mp3_gettime(mp3)) #from mp3_eyed3 #jorgeorpinel: eyed3_secs unused 
#    except :
#        print 'Could not read time from mp3', mp3
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

    add(track)
    commit() #to get our track id we need to write this record
    print '\tWrote track record', track.id, 'to database' # debug -------------

    if fast_import :
        track.secs = -1
        track.zsecs = -1
    else :
        #todo: untested code for checking secs and zsecs (DSE Feb 5, 2010)
        a = AudioFile(filename)
        [track.secs, track.zsecs] = a.get_secs_zsecs()

    track.path = get_tidfilename(track.id)


    #This is a bit confusing. For backwards compat
    if artist:
        track.artist = artist.name
        track.artists.append(artist)

    if album:
#        print 'Attaching album',album #debug
        track.album = album.name
        track.albums.append(album)

    commit()
#    print 'Committed album and artist additions to track' #debug

    #copy the file
    tgt = os.path.join(gordonDir, 'audio', 'main', track.path)
    make_subdirs_and_copy(filename, tgt)
    #print 'Copied mp3',filename,'to',tgt

    #stamp the file
    id3.id3v2_putval(tgt, 'tid', 'T%i' % track.id)

    #we update id3 tags in mp3 if necessary
    if track.otitle <> track.title or track.oartist <> track.artist or track.oalbum <> track.album or track.otracknum <> track.tracknum :
        #print 'Updating id3 tags in',track.path
        print 'Trying to update_mp3_from_db '+track.id, os.path.join(gordonDir, 'audio', 'main') #debug
        #from gordon.db.mbrainz_resolver.GordonResolver import update_mp3_from_db #jorgeorpinel
        #update_mp3_from_db(track.id, audioDir = os.path.join(gordonDir, 'audio', 'main'), doit = True)
        #todo: up here is where the script writes to the mp3 files, should try|except for file access crashes

    #if not fast_import :
        #print 'Calculating features for track',track.id
        #update_features(track.id)
    pass # for Eclipse correct folding after comments



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
        #before we didn't do this  . . . pass

    id3_dict['compilation'] = compilation
    return id3_dict

def _prompt_aname(albumDir, id3_dicts, albums, cwd) :
    '''Used to prompt to choose an album if files in a directory have more than 1 (indicated by their tags)'''
    print albumDir, 'Multiple albums found'
    print 'SONGS---'
    for dct in id3_dicts.values() :
        print ' %i %s album=%s track=%s' % (dct['tracknum'], dct['album'], dct['artist'], dct['title'])

    #let user select which album name to use
    print 'ALBUM NAMES---'
    ctr = 1
    for artist in albums :
        print ctr, artist
        ctr += 1
    while True :
        ans = raw_input('Choose one (0=do not import -1=Type album name>')
        try :
            val = int(ans)
            if val == 0 :
                os.chdir(cwd)
                return -1 # --------------------------------------------- return -1
            elif val > 0 and val <= len(albums) :
                album_name = albums[val - 1]
                print 'Using', album_name
                break
            elif val == -1 :
                ans = raw_input('Type name> ')
                ans2 = raw_input('Use %s ? (y/n)> ' % ans)
                if ans2 == 'y' :
                    album_name = ans
                    break
        except :
            pass #stay in loop

def add_album(albumDir, source = str(datetime.date.today()), gordonDir = DEF_GORDON_DIR, prompt_aname = False, fast_import = False):
    '''Add a directory with audio files
        * when we do an album we need to read all files in before trying anything
        * we can't just add each track individually. We have to make Artist ids for all artists
        * we will presume that 2 songs by same artist string are indeed same artist
    '''
    print 'Adding album', albumDir # debug -------------------------------------
    
    id3_dicts = dict()
    albums = set()
    artists = set()
    
    cwd = os.getcwd()
    os.chdir(albumDir)
    for filename in os.listdir('.') :
        if not os.path.isdir(os.path.join(cwd, filename)) : #jorgeorpnel: before if nor filename.startswith('.') :
            print '\tChecking', '"'+filename+'"...', # debug ------------------
            if filename.lower().endswith('.mp3') : # gets ID3 tags from mp3s
                id3tags = _get_id3_dict(filename)
                print 'MP3 ID3 tags read', id3tags # debug --------------------
                id3_dicts[filename] = id3tags
                albums.add(id3tags['album'])
                artists.add(id3tags['artist'])
            else : print 'not an MP3' # debug ---------------------------------
        
        #todo: work with non-mp3 audio files/tags!
    
    albums = list(albums)
    
    if len(artists) == 0 :
        os.chdir(cwd)
        print ' Nothing to add' #debug
        return  # no songs ---------------------------------------------- return
    else : print '', len(artists), 'artists in directory:', artists # debug ---
    
    if len(artists) <> 1 :  # if more than 1 artist found in ID3 tags
        if prompt_aname :
            # prompt user to choose an album
            if _prompt_aname(albumDir, id3_dicts, albums, cwd) == -1 :    return # why? see _prompt_aname()
        else :
            os.chdir(cwd)
            print ' Not adding', len(albums),'album names in album', albumDir, albums #debug
            return  # more than one album in directory ------------------ return
    else : # there's only one album in the directory (as should be)
        album_name = albums[0]
    
    #add our album to Album table
    print ' Adding album with', len(id3_dicts), 'recordings' #debug
    albumrec = Album(name = album_name, trackcount = len(id3_dicts), a='1') #jorgeorpinel: a='1' ?

    #if we have an *exact* string match we will use the existing artist
    artist_dict = dict()
    for artist in set(artists) :
        match = Artist.query.filter_by(name = artist) #@UndefinedVariable #todo: remove this stupid Eclipse
        if match.count() == 1 :
            print ' Matched', artist, match[0], 'in database' # debug --------- 
            artist_dict[artist] = match[0]
        else :
            # add our Artist to artist table
            newartist = Artist(name = artist)
            artist_dict[artist] = newartist

        #add artist to album (album_artist table)
        albumrec.artists.append(artist_dict[artist])

    #commit these changes #jorgeorpinel: holdn't it commit until the very end?
    commit()

    #now add our tracks to album
    for mp3 in id3_dicts.keys() :
        id3_dict = id3_dicts[mp3]
        add_mp3(mp3 = mp3, gordonDir = gordonDir, id3_dict = id3_dict, artist = artist_dict[id3_dict['artist']], album = albumrec, source = source, fast_import = fast_import)
        print '\tAdded', '"'+mp3+'"' # debug ----------------------------------

    #now update our track counts
    print artist_dict
    for aname, artist in artist_dict.iteritems() :
        #print 'Updating trackcount for',artist
        artist.update_trackcount()
    albumrec.update_trackcount()
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
    print 'Importing from', os.getcwd() + os.sep

    #handle root as a potential album
    if not iTunesDir :
        if not doit :
            print 'Would import .' + os.sep
        else :
            add_album('.', gordonDir = gordonDir, source = source, prompt_aname = False, fast_import = fast_import)
            print 'Proccessed', '.'

    for root, dirs, files in os.walk('.') :
        if iTunesDir and len(root.split('/')) <> 2 :
            print 'iTunesDir skipping (artists) directories under root', root
            continue

        for dir in dirs :
            if not doit :
                print 'Would import', root + os.sep + dir
            else :
                add_album(os.path.join(root, dir), gordonDir = gordonDir, source = source, prompt_aname = False, fast_import = fast_import)
                print 'Added album', os.path.join(root, dir)

    #now go do it again prompting to import albums which have more than one name per directory
    if prompt_incompletes :
        for root, dirs, files in os.walk('.') :
            if iTunesDir and len(root.split('/')) <> 2 :
                continue
            
            for dir in dirs:
                if doit :
                    add_album(os.path.join(root, dir), gordonDir = gordonDir, source = source, prompt_aname = True, fast_import = fast_import)

#    #remove empty dirs #jorgeorpinel: no! why? it only works on linux anyway
#    if doit:
#        print 'Removing any empty directories. This command will fail if none of the directories are empty. No worries'
#        os.system('find . -depth -type dir -empty -print0 | xargs -0 rmdir')
#    os.chdir(cwd)
    pass





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
    print 'audio_intake.py: Gordon audio intake script running...'
    if len(sys.argv) < 3:
        _die_with_usage()

    source = sys.argv[1]
    dir = sys.argv[2]
    doit = None
    try :
        if sys.argv[3] == 0: doit = False
        else: doit = True
    except Exception as ex :
        print ' * No <doit> (3rd) argument given. Thats 0K (Pass no args for script usage)'
    doit = True if doit is None else doit   #jorgeorpinel: just trying Python's ternary opperator :p

    print 'audio_intake.py: using <source>', '"'+source+'",', '<dir>', eval("'"+dir+"'")
    #sys.exit(0)
    add_collection(collectionDir = dir, source = source, doit = doit, fast_import = False)


