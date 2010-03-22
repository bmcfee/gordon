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

"""Functions for importing music to Gordon database"""

import pg
#jorgeorpinel: for windows:
#import numpy.distutils.fcompiler.pg

from numpy import *
from model import *
from sqlalchemy import *

import gordon.io.mp3_eyeD3 as id3 
#jorgeorpinel: for windows:
#from gordon.io import mp3_eyeD3 as id3

import time,difflib,shutil,os,heapq,string,datetime,stat,copy,sys,random

from sqlalchemy.databases.postgres import PGArray
#jorgeorpinel: for my windows which never finds python paths/packages (plus im using more recent vesions of everything)
#from sqlalchemy.databases import postgres
#PGArray = postgres.PGArray

from collections import defaultdict
import traceback

from gordon.io import AudioFile

from config import *
from gordon_db import *

def add_mp3(mp3,source=str(datetime.date.today()),gordonDir=DEF_GORDON_DIR,id3_dict=dict(),artist=None,album=None,fast_import=False) :
    """Add mp3 with filename <mp3> to database
          source -- data source
         gordonDir -- main Gordon directory
        id3_dict -- dictionary of key,val ID3 pairs.  See add_album. 
          artist -- The artist for this track. An instance of Artist. None if not present
          album  -- The album for this track. An instance of Album. None if not present
     fast_import -- If true, do not calculate strip_zero length. Defaults to False
    """
    if len(id3_dict)==0 :
        #currently cannot add singleton mp3s. Need an album which is defined in id3_didt
        print 'Cannot add file',mp3,'because it is not part of an album'
        return
    if not os.path.isfile(mp3) :
        print 'Skipping %s because it is not a file'
        return

        
    (pth,fn)=os.path.split(mp3)

    bytes = os.stat(mp3)[stat.ST_SIZE]

    #track length. 
    try:
        eyed3_secs = int(id3.mp3_gettime(mp3)) #from mp3_eyed3
    except :
        print 'Could not read time from mp3',mp3
        eyed3_secs = -1

    
    
    if id3_dict['compilation'] not in [True, False, 'True', 'False'] :
        id3_dict['compilation'] = False
    

    #we get odd filenames that cannot be easily encoded.  This seems to come from times when a latin-1 filesystem named files
    #and then those filenames are brought over to a utf filesystem.
    try:
        fn_recoded = fn.decode('utf-8')
    except :
        try :
            fn_recoded = fn.decode('latin1')
        except :
            fn_recoded='unknown'

    track = Track(title=id3_dict['title'],
                  artist=id3_dict['artist'],
                  album=id3_dict['album'],
                  tracknum=id3_dict['tracknum'],
                  compilation=id3_dict['compilation'],
                  otitle=id3_dict['title'],
                  oartist=id3_dict['artist'],
                  oalbum=id3_dict['album'],
                  otracknum=id3_dict['tracknum'],
                  ofilename=fn_recoded,
                  source=source,
                  bytes=bytes)

    #to get our track id we need to write this record
    commit()

#    print 'Wrote track record',track.id
    
    if fast_import :
        track.secs=-1
        track.zsecs=-1
    else :
        #untested code for checking secs and zsecs (DSE Feb 5, 2010)
        a=AudioFile(fn)
        [track.secs,track.zsecs]=a.get_secs_zsecs()

    
    track.path=get_tidfilename(track.id)


    #This is a bit confusing. For backwards compat
    if artist:
        track.artist=artist.name
        track.artists.append(artist)

    if album:
  #      print 'Attaching album',album
        track.album=album.name
        track.albums.append(album)
    
    commit()
#    print 'Committed album and artist additions to track'

    #copy the file
    tgt=os.path.join(gordonDir,'audio','main',track.path)
    make_subdirs_and_copy(fn,tgt)
    #print 'Copied mp3',fn,'to',tgt

    #stamp the file
    id3.id3v2_putval(tgt,'tid','T%i' % track.id)

    #we update id3 tags in mp3 if necessary
    if track.otitle<>track.title or track.oartist<>track.artist or track.oalbum<>track.album or track.otracknum<>track.tracknum :
        #print 'Updating id3 tags in',track.path
        update_mp3_from_db(track.id,audioDir=os.path.join(gordonDir,'audio','main'),doit=True)         
    
 #   if not fast_import :
 #       print 'Calculating features for track',track.id
 #       update_features(track.id)

    
    
#when we do an album we need to read all files in before trying anythin
def add_album(albumDir,source=str(datetime.date.today()),gordonDir=DEF_GORDON_DIR,prompt_aname=False,fast_import=False):
    print 'Adding album',albumDir
    id3_dicts=dict()
    albums=set()
    artists=set()
    #we can't just add each track individually. We have to make Artist ids for all artists
    #we will presume that 2 songs by same artist string are indeed same artist 
    cwd=os.getcwd()
    os.chdir(albumDir)
    for f in os.listdir('.') :
        #print 'Checking',f
        if f.lower().endswith('.mp3') and not f.startswith('.'):
            #print 'Adding',f
            d=get_id3_dict(f)
            albums.add(d['album'])
            artists.add(d['artist'])
            id3_dicts[f]=d
    
    albums = list(albums)
    if len(artists)==0 :
        os.chdir(cwd)
        #print 'Nothing to add'
        return #no songs
    
    
    if len(albums)<>1 :
        if prompt_aname :
            print albumDir,'Multiple albums found'
            print 'SONGS---'
            for dct in id3_dicts.values() :
                
                print ' %i %s album=%s track=%s' % (dct['tracknum'],dct['album'],dct['artist'],dct['title'])
                                       
            
                
            #let user select which album name to use
            print 'ALBUM NAMES---'
            ctr=1
            for a in albums :
                print ctr,a
                ctr+=1
            while True :
                ans=raw_input('Choose one (0=do not import -1=Type album name>')
                try :
                    val = int(ans)
                    if val==0 :
                        os.chdir(cwd)
                        return
                    elif val>0 and val<=len(albums) :
                        album_name=albums[val-1]
                        print 'Using',album_name
                        break
                    elif val==-1 :
                        ans = raw_input('Type name> ')
                        ans2 = raw_input('Use %s ? (y/n)> ' % ans)
                        if ans2=='y' :
                            album_name=ans
                            break
                except :
                    pass #stay in loop
        else :
            os.chdir(cwd)
            #print len(albums),'album names in album',albumDir
            #print albums
            #print 'not adding'
            return
    else :
        album_name=albums[0]

    #add our album to Album table
    #print 'Adding album with',len(id3_dicts),'recs'
    albumrec = Album(name=album_name,trackcount=len(id3_dicts))
    
    #if we have an *exact* string match we will use the existing artist
    artist_dict=dict()
    for a in set(artists) :
        match = Artist.query.filter_by(name=a)
        if match.count()==1 :
            #print 'Matched',a,match[0]
            artist_dict[a]=match[0]
        else :
            newartist = Artist(name=a)
            artist_dict[a]=newartist

        #add artist to album
        albumrec.artists.append(artist_dict[a])

    #commit these changes
    commit()

    #now add our tracks to album
    for mp3 in id3_dicts.keys() :
        id3_dict=id3_dicts[mp3]
        #print 'adding',artist_dict[id3_dict['artist']],'artist_id'
        add_mp3(mp3=mp3,gordonDir=gordonDir,id3_dict=id3_dict,artist=artist_dict[id3_dict['artist']], album=albumrec,source=source,fast_import=fast_import)

    
    #now update our track counts
    print artist_dict
    for aname,a in artist_dict.iteritems() :
        #print 'Updating trackcount for',a
        a.update_trackcount()
    albumrec.update_trackcount()
    commit()

    os.chdir(cwd)






def add_collection(collectionDir,source=str(datetime.date.today()),prompt_incompletes=False, doit=False, iTunesDir=False, gordonDir=DEF_GORDON_DIR,fast_import=False):
    """recursively adds mp3s from a directory tree.
    treats all files in same directory as being in same album!
     
    Only imports if all songs actually have same album name. 
    With flag prompt_incompletes will prompt for incomplete albums as well

    When iTunesDir==True, add only directories of the form <collectionDir>/<artist>/<album>
    This does *not* import all songs in the tree but only those two plys deep...

    Use doit=True to actually commit the addition of songs
    """
    #When fast_import=True
    cwd=os.getcwd()
    os.chdir(collectionDir)

    #handle root as a potential album
    if not iTunesDir :
        if not doit :
            print 'Would import',os.getcwd()
        else :
            add_album('.',gordonDir=gordonDir,source=source,prompt_aname=False,fast_import=fast_import)
    
    for root,dirs,files in os.walk('.') :
        if iTunesDir and len(root.split('/'))<>2 :
            print 'iTunesDir skipping directories under root',root
            continue
        for d in dirs :
            if not doit :
                print 'Would import', os.path.join(root,d)
            else :
                add_album(os.path.join(root,d),gordonDir=gordonDir,source=source,prompt_aname=False,fast_import=fast_import)
                print 'Added album',os.path.join(root,d)
                
    #now go do it again prompting to import albums which have more than one name per directory
    if prompt_incompletes :
        for root,dirs,files in os.walk('.') :
            if iTunesDir and len(root.split('/'))<>2 :
                continue
            for d in dirs :
                if doit :
                    add_album(os.path.join(root,d),gordonDir=gordonDir,source=source,prompt_aname=True,fast_import=fast_import)

    #remove empty dirs
    if doit:
        print 'Removing any empty directories. This command will fail if none of the directories are empty. No worries'
        os.system('find . -depth -type d -empty -print0 | xargs -0 rmdir')
    os.chdir(cwd)

    
def get_id3_dict(mp3) :
    id3_dict=dict()
    (title,artist,album,tracknum,compilation) = id3.id3v2_getval(mp3,('title','artist','album','tracknum','compilation'))
    id3_dict['title']=title
    id3_dict['artist']=artist
    id3_dict['album']=album
    try :
        id3_dict['tracknum']=int(tracknum)
    except :
        id3_dict['tracknum']=0
        #before we didn't do this  . . . pass

    id3_dict['compilation']=compilation
    return id3_dict





def die_with_usage() :
    print 'This program imports a directory into the database'
    print 'Usage: '
    print 'audio_intake <source> <dir>'
    print 'Arguments: '
    print '  <source> is the string stored to the database for source e.g. DougDec22'
    print '  <dir> is the directory to be imported'
    print 'More options are available by using the function add_collection()'
    sys.exit(0) 


if __name__=='__main__':
    if len(sys.argv)<3:
        die_with_usage()

    source=sys.argv[1]
    dir=sys.argv[2]
    print 'Using source',source,'directory',dir
    #sys.exit(0)
    add_collection(collectionDir=dir,source=source,doit=True,fast_import=False)
