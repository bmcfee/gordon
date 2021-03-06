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

import os, datetime, logging, stat, sys

from csv import reader
from glob import glob

from gordon.io import AudioFile
from gordon.io import mp3_eyeD3 as id3
from gordon.db.config import DEF_GORDON_DIR
from gordon.db.gordon_db import get_tidfilename, make_subdirs_and_copy, is_binary
from gordon.db.model import add, commit, Album, Artist, Track, Collection, Annotation


log = logging.getLogger('gordon.audio_intake')


def _store_annotations(audiofile, track, all_md=False):
    """Searches for metadata related to the audio-file (v 1.0; for now only ID3 in MP3): type <id3> annotation [tagname];
    Searches for text-files with the same base-name whithin the folder (any [ext]ension): type <txt> annotation [ext];
    Stores these annotation values in the track_annotation DB table
    
    @param audiofile: the file (should be previously verified as an actual audio file)
    @param track: previously stored track record in the database, represented by a gordon.db.model.Track class (SQL Alchemy)
    @param all_md: use True to extract all tags from the audio-file (defaults to False) 
    
    returns number of annotations (0 to *) stored"""
    
    annots = 0
    
    #chek if file is mp3. if so:
    if all_md:
        if id3.isValidMP3(audiofile):
            #extract all ID3 tags, store each tag value as an annotation type id3.[tagname]
            for tag in id3.getAllTags(audiofile, skipTrackFields=True): # this skips the 4 basic tags already in track
                track.annotations.append(Annotation(name=unicode(tag[0]), value=tag[1])) #todo: value=unicode(tag[1])
                annots += 1
    
        #future todo: apply tagpy or other method to extract more metadata formats
    
    if annots == 0: log.debug('    No ID3 metadata found.')
    
    # check text file annotations
    (pathandbase, ext) = os.path.splitext(audiofile)
    simfiles = list()
    if os.path.exists(pathandbase): simfiles.append(pathandbase)
    for s in glob(pathandbase+'.*'): simfiles.append(s)
    txt=None

    for simfile in simfiles: # for every file sharing base-name (any or no extension)
        try:
            if not is_binary(simfile): # if its a text file
#                if simfile == audiofile: continue # (we skip the original) #unnecesary; it is_binary

                # copy text (file content) to new track annotation (type txt.[ext])
                txt=open(simfile)
                (xxx, ext) = os.path.splitext(simfile)
                track.annotations.append(Annotation(name=unicode(ext[1:]), value=unicode(txt.read())))
                annots += 1
        finally:
            if type(txt)==file: txt.close()
            
    commit() #saves all appended annotations in the track
    
    log.debug('    Stored %s annotations overall', annots)
    return annots

def add_mp3(mp3, source=str(datetime.date.today()), gordonDir=DEF_GORDON_DIR, id3_dict=dict(), artist=None, album=None, fast_import=False, import_id3=False):
    '''Add mp3 with filename <mp3> to database
         @param source: audio files data source
         @param gordonDir: main Gordon directory
         @param tag_dict: dictionary of key,val ID3 tags pairs - See add_album(...).
         @param artist: The artist for this track. An instance of Artist. None if not present
         @param album: The album for this track. An instance of Album. None if not present
         @param fast_import: If true, do not calculate strip_zero length. Defaults to False
         @param import_id3: Specifies if we want to get the id3 tags from the file. Defaults to True
    '''
    (filepath, filename) = os.path.split(mp3)
    log.debug('    Adding mp3 file "%s" of "%s" album by %s - add_mp3()', filename, album, artist)    
    
    # validations
    
    if len(id3_dict) == 0 :
        #todo: currently cannot add singleton mp3s. Need an album which is defined in id3_dict
        log.error('    Cannot add "%s" because it is not part of an album', filename)
        return -1 # didn't add
    if not os.path.isfile(mp3) :
        log.debug('    Skipping %s because it is not a file', filename)
        return -1 # not a file


    # required data
    
    bytes = os.stat(mp3)[stat.ST_SIZE]
#    try: #get track length
#        eyed3_secs = int(id3.mp3_gettime(mp3)) #from mp3_eyed3
#    except :
#        log.error('    Could not read time from mp3 %s', mp3)
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

    track = Track(title = id3_dict[u'title'],
                  artist = id3_dict[u'artist'],
                  album = id3_dict[u'album'],
                  tracknum = id3_dict[u'tracknum'],
                  compilation = id3_dict[u'compilation'],
                  otitle = id3_dict[u'title'],
                  oartist = id3_dict[u'artist'],
                  oalbum = id3_dict[u'album'],
                  otracknum = id3_dict[u'tracknum'],
                  ofilename = os.path.join(filepath,fn_recoded),
                  source = unicode(source),
                  bytes = bytes)
    
    # add data
    
    add(track)
    commit() #to get our track id we need to write this record
    log.debug('    Wrote track record %s to database', track.id)

    if fast_import :
        #try to get the seconds from ffmpeg
        track.zsecs = -1
        track.secs= -1
        try :
            a = AudioFile(filename)
            [ignore_fs,ignore_chans,track.secs] = a.read_stats()
        except :
            log.warn("    Could not read stats from", filename)
            
    else :
        a = AudioFile(filename)
        [track.secs, track.zsecs] = a.get_secs_zsecs()

    track.path = u"%s" % get_tidfilename(track.id)

    #This is a bit confusing. For backwards compat #todo: clean up DB relationships
    if artist:
        log.debug('    Linking to artist %s', artist)
        track.artist = artist.name
        track.artists.append(artist)

    if album:
        log.debug('    Linking to album %s', album)
        track.album = album.name
        track.albums.append(album)

    commit() # save (again) the track record (this time)
    log.debug('    * Wrote album and artist additions to track into database')

    #copy the file to the Gordon instal audio/feature data directory
    
    tgt = os.path.join(gordonDir, 'audio', 'main', track.path)
    make_subdirs_and_copy(filename, tgt)
    log.debug('    Copied mp3 "%s" to %s', filename, tgt)

    #stamp the file ("TID n" as an ID3v2 commment)
    id3.id3v2_putval(tgt, 'tid', 'T%i' % track.id) # writes on new audio file (the copy)

    # We update id3 tags in mp3 if necessary (from local MusicBrainz DB, when no info found)
    #todo: try this when Gordon has no write access to the files, does the script handle the error? (can't roll back saved tracks now)
    if track.otitle <> track.title or track.oartist <> track.artist or track.oalbum <> track.album or track.otracknum <> track.tracknum :
        log.debug('    (NOT) Trying to update_mp3_from_db %s %s', track.id,
                  os.path.join(gordonDir, 'audio', 'main'))
        try:
            from gordon.db.mbrainz_resolver import GordonResolver
            gordonResolver = GordonResolver()
            try:
                if not gordonResolver.update_mp3_from_db(track.id, audioDir = os.path.join(gordonDir, 'audio', 'main'), doit = True) :
                    pass # if file not found ...
            except Exception: # except for file access crashes?
                pass
        except:
            log.warning('    MusicBrainz interface is not installed. Refer to Gordon INSTALL notes.')

    #search for other annotations and store them in the database
    
    _store_annotations(mp3, track, import_id3)

def add_uncomp(wav, source=str(datetime.date.today()), gordonDir=DEF_GORDON_DIR, tag_dict=dict(), artist=None, album=None, fast_import=False, import_md=False):
    """Add uncompressed wav/aif with filename <wav> to database
         @param source: audio files data source - Collection object
         @param gordonDir: main Gordon directory
         @param tag_dict: dictionary of key,val tag pairs - See add_album(...).
         @param artist: The artist for this track. An instance of Artist. None if not present
         @param album: The album for this track. An instance of Album. None if not present
         @param fast_import: If true, do not calculate strip_zero length. Defaults to False
         @param import_md: Specifies if we want to get the metadata tags from the file. Defaults to True
    """
    (xxx, filename) = os.path.split(wav)
    (xxx, ext) = os.path.splitext(filename)
    log.debug('    Adding uncompressed file "%s" of "%s" album by %s - add_uncomp()', filename, album, artist)
    
    
    # validations
    
    if len(tag_dict) == 0 :
        #todo: currently cannot add singleton files. Need an album which is defined in tag_dict
        log.error('    Cannot add "%s" because it is not part of an album', filename)
        return -1 # didn't add
    if not os.path.isfile(wav) :
        log.debug('    Skipping %s because it is not a file', filename)
        return -1 # not a file

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

    track = Track(title = tag_dict[u'title'],
                  artist = tag_dict[u'artist'],
                  album = tag_dict[u'album'],
                  tracknum = tag_dict[u'tracknum'],
                  compilation = tag_dict[u'compilation'],
                  otitle = tag_dict[u'title'],
                  oartist = tag_dict[u'artist'],
                  oalbum = tag_dict[u'album'],
                  otracknum = tag_dict[u'tracknum'],
                  ofilename = fn_recoded,
                  source = unicode(source),
                  bytes = bytes)
    
    # add data
    
    add(track) # needed to get a track id
    commit() #to get our track id we need to write this record
    log.debug('    Wrote track record %s to database', track.id)

    if fast_import :
        track.secs = -1
        track.zsecs = -1
    else :
        a = AudioFile(filename)
        [track.secs, track.zsecs] = a.get_secs_zsecs()

    track.path = u'%s' % get_tidfilename(track.id, ext[1:]) # creates path to insert in track

    # links track to artist & album in DB
    if artist:
        log.debug('    Attaching artist %s', artist)
        track.artist = artist.name
        track.artists.append(artist)
    if album:
        log.debug('    Attaching album %s', album)
        track.album = album.name
        track.albums.append(album)

    commit() # save (again) the track record (this time having the track id)
    log.debug('    * Wrote album and artist additions to track into database')


    #copy the file to the Gordon instal audio/feature data directory
    
    tgt = os.path.join(gordonDir, 'audio', 'main', track.path)
    make_subdirs_and_copy(filename, tgt)
    log.debug('    Copied uncompressed "%s" to %s', filename, tgt)
    
    #search for other annotations and store them in the database
    
    _store_annotations(wav, track, import_md)


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
                return False
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
    
    return album_name 

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
    
    # check that theres info. in the ID3 tags 
    empty = True # if this remains True, we have empty tags [same as _empty_tags()]
    for tag in id3_dict:
        if tag:
            empty = False
            break
    
    id3_dict['empty'] = empty
    return id3_dict

def _read_csv_tags(cwd, csv):
    '''Reads a csv text file with tags for WAV files (v 1.0)
    
    # may use py comments in tags.csv file (in album-folder)
    filename, title, artist, album, tracknum, compilation
    per line
    
    Returns a 2D dict in the form dict[<filename>][<tag>]
    
    @param cwd: path to directory to work in
    @param csv: csv file-name (in <cwd> dir)'''
    
    tags = dict()
    
    try:
        csvfile = reader(open(os.path.join(cwd, csv)))
        for line in csvfile: # each record (file rows)
            if len(line) < 6 : continue
            line[0] = line[0].strip()
            if not line[0] or line[0][0] == '#' : continue # if name empty or comment line
            
            #save title, artist, album, tracknum, compilation in tags[<file-name>]
            tags[line[0]] = dict()
            tags[line[0]]['title']  = line[1].strip()
            tags[line[0]]['artist'] = line[2].strip()
            tags[line[0]]['album']  = line[3].strip()
            try: tags[line[0]]['tracknum'] = int(line[4])
            except: tags[line[0]]['tracknum'] = 0
            line[5] = line[5].strip().lower()
            tags[line[0]]['compilation'] = True if line[5]=='true' or line[5]=='1' else False
    except IOError:
        log.error('  Couldn\'t open "%s"', csv)

    return tags

def _empty_tags():
    tags = dict()
    tags['title'] = ''
    tags['artist'] = ''
    tags['album'] = ''
    tags['tracknum'] = 0
    tags['compilation'] = ''
    return tags

def add_album(albumDir, source = str(datetime.date.today()), gordonDir = DEF_GORDON_DIR, prompt_aname = False, fast_import = False, import_md=False):
    """Add a directory with audio files v 1.2
        * when we do an album we need to read all files in before trying anything
        * we can't just add each track individually. We have to make Artist ids for all artists
        * we will presume that 2 songs by same artist string are indeed same artist
    """
    log.debug('  Adding album "%s" - add_album()', albumDir)
    
    tags_dicts = dict()
    albums = set()
    artists = set()
    
    cwd = os.getcwd()
    os.chdir(albumDir)
    for filename in os.listdir('.') :
        (xxx, ext) = os.path.splitext(filename)
        if not os.path.isdir(os.path.join(cwd, filename)) :
            log.debug('  Checking "%s" ...', filename)
            csvtags = False
            
#            if ext.lower() == '.mp3' : # gets ID3 tags from mp3s
            if id3.isValidMP3(os.path.join(cwd, filename)):
                log.debug('  %s is MP3', filename)
                tags_dicts[filename] = _get_id3_dict(filename)
                if not tags_dicts[filename]['empty']: # non empty tags obtained :)
                    log.debug('  .. w/ ID3 tags', tags_dicts[filename])
                    del(tags_dicts[filename]['empty'])
                tags_dicts[filename]['func'] = 'add_mp3'
                albums.add(tags_dicts[filename]['album'])
                artists.add(tags_dicts[filename]['artist'])
            elif ext.lower() in ['.wav', '.aif', '.aiff']: # since this is wav/aif, use possible csv tags file
            #todo: check for file binary content to determine wether it is wav/aiff instead of extension check...
                if not csvtags : csvtags = _read_csv_tags(os.getcwd(), 'tags.csv')
                log.debug('  %s is %s', filename, ext)
                try: # if csvtags[filename] is not empty:
                    if csvtags[filename] : log.debug('  .. w/ CSV tags (tags.csv)', csvtags[filename])
                    tags_dicts[filename] = csvtags[filename]
                except: # make empty tags on the fly
                    tags_dicts[filename] = _empty_tags()
                tags_dicts[filename]['func'] = 'add_uncomp'
                albums.add(tags_dicts[filename]['album'])
                artists.add(tags_dicts[filename]['artist'])
            else:
                log.debug('  %s is not a supported audio file format', filename)
                
            #todo: work with other non-mp3 audio files/tags!
    
    albums = list(albums)
    
    if len(artists) == 0 :
        os.chdir(cwd)
        log.debug('  Nothing to add')
        return # no songs
    else:
        log.debug('  %d artists in directory: %s', len(artists), artists)
    
    if len(albums) <> 1 :  # if more than 1 album found found in ID3 tags
        if prompt_aname :
            # prompt user to choose an album
            album_name = _prompt_aname(albumDir, tags_dicts, albums, cwd)
            if album_name == False : return # why? see _prompt_aname() -- return
        else :
            os.chdir(cwd)
            log.debug('  Not adding %d album names in album %s %s', len(albums), albumDir, str(albums))
            return # more than one album in directory
    else : # there's only one album in the directory (as should be)
        album_name = albums[0]
    
    #add our album to Album table
    log.debug('  Album has %d recordings', len(tags_dicts))
    albumrec = Album(name = unicode(album_name), trackcount = len(tags_dicts))
#    collection = None
    source = unicode(source)
    match = Collection.query.filter_by(name = source)
    if match.count() == 1:
        log.debug('  Matched source %s in database', match[0])
#        collection = match[0]
#    else:
#        collection = Collection(name=unicode(source))
#    albumrec.collections.append(collection)

    #if we have an *exact* string match we will use the existing artist
    artist_dict = dict()
    for artist in set(artists) :
        match = Artist.query.filter_by(name = artist)
        if match.count() == 1 :
            log.debug('  Matched %s %s in database', artist, match[0])
            artist_dict[artist] = match[0]
            #todo: (eckdoug) what happens if match.count()>1? This means we have multiple artists in db with same 
            # name. Do we try harder to resolve which one? Or just add a new one.  I added a new one (existing code)
            # but it seems risky.. like we will generate lots of new artists. 
            # Anyway, we resolve this in the musicbrainz resolver....
        else :
            # add our Artist to artist table
            newartist = Artist(name = unicode(artist))
#            newartist.collections.append(collection)
            artist_dict[artist] = newartist

        #add artist to album (album_artist table)
        albumrec.artists.append(artist_dict[artist])

    commit() #commit these changes in order to have access to this album record when adding tracks

    #now add our tracks to album
    for file in tags_dicts.keys() :
        # calls add_mp3(), add_uncomp(), or other...
        addfunction = tags_dicts[file].pop('func')
        eval(addfunction + "(file, source, gordonDir, tags_dicts[file], artist_dict[tags_dicts[file]['artist']], albumrec, fast_import, import_md)")
        log.debug('  Added "%s"!', file)

    #now update our track counts
    for aname, artist in artist_dict.iteritems() :
        artist.update_trackcount()
        log.debug('  * Updated trackcount for artist %s', artist)
    albumrec.update_trackcount()
    log.debug('  * Updated trackcount for album %s', albumrec) 
    commit()

    os.chdir(cwd) # and return to original working dir

def add_collection(location, source = str(datetime.date.today()), prompt_incompletes = False, doit = False, iTunesDir = False, gordonDir = DEF_GORDON_DIR, fast_import = False, import_md=False):
    """Recursively adds mp3s from a directory tree.
    treats all files in same directory as being in same album!
     
    Only imports if all songs actually have same album name. 
    With flag prompt_incompletes will prompt for incomplete albums as well

    When iTunesDir==True, add only directories of the form <location>/<artist>/<album>
    This does *not* import all songs in the tree but only those two plys deep...

    Use doit=True to actually commit the addition of songs
    """
        
    try:
        os.chdir(location)
    except Exception:
        log.critical('%s not found' % location)
        sys.exit(1)
    
    log.debug('Looking for a collection in %s. - add_collection()', os.sep)

    #handle root as a potential album
    if not iTunesDir :
        if not doit :
            print 'Would import .' + os.sep
        else :
            add_album('.', gordonDir=gordonDir, source=source, prompt_aname=prompt_incompletes, fast_import=fast_import, import_md=import_md)
            log.debug('Proccessed %s.', os.sep)

    for root, dirs, files in os.walk('.') :
        if iTunesDir and len(root.split(os.sep)) <> 2 :
            print 'iTunesDir skipping (artists) directories under root', root
            continue

        for dir in dirs :
            if not doit :
                print 'Would import', root + os.sep + dir
            else :
                add_album(os.path.join(root, dir), gordonDir=gordonDir, source=source, prompt_aname=prompt_incompletes, fast_import=fast_import, import_md=import_md)
                log.debug('Added album %s', os.path.join(root, dir))

#    #remove empty dirs # only works on linux
#    if doit:
#        print 'Removing any empty directories. This command will fail if none of the directories are empty. No worries'
#        os.system('find . -depth -type dir -empty -print0 | xargs -0 rmdir')
#    os.chdir(cwd)
    log.info('audio_intake.py: Finished!')



def _die_with_usage() :
    print 'This program imports a directory into the database'
    print 'Usage: '
    print 'audio_intake [flags] <source> <dir> [doit] [metadata]'
    print 'Flags:' 
    print '  -fast: imports without calculating zero-stripped track times.'
    print '  -noprompt: will not prompt for incomplete albums.  See log for what we skipped'
    print 'Arguments: '
    print '  <source> is the string stored to the database to identify the intake opperation e.g. "DougDec22". Defaults to current date'
    print '  <dir> is the directory to be imported'
    print '  optional [doit] (default 1) use 0 to test the intake harmlessly'
    print '  optional [metadata] (default 0) use 1 to import all metadata tags from the file'
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
    source = unicode(sys.argv[1])
    dir = sys.argv[2]
    doit = True
    try:
        if int(sys.argv[3]) == 0: doit = False
    except: pass
    import_md = None
    try: import_md = True if int(sys.argv[4]) == 1 else False
    except: import_md = False

    log.info('audio_intake.py: using <source>'+' "'+source+'", <dir> %s'%dir)
    add_collection(location=dir, source=source, prompt_incompletes=prompt_incompletes, doit=doit, fast_import=fast_import, import_md=import_md)
    
