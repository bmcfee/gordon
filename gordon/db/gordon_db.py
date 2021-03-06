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
Main Gordon namespace

Includes the database model and a set of utility functions for
validating the contents of the database, removing duplicates, etc.
'''

import numpy, os, logging

from shutil import move, copy
from sqlalchemy import func, select
from string import join, replace
from sys import platform, version
from time import sleep
from unicodedata import decomposition, normalize

from gordon.db.model import (Artist, Album, Annotation, Track, Collection, FeatureExtractor,
                             session, commit, album, Mbalbum_recommend,
                             execute_raw_sql)
#from gordon.db.config import DEF_GORDON_DIR, DEF_DBUSER, DEF_DBPASS, DEF_DBHOST
from gordon.db import config
from gordon.io import AudioFile


log = logging.getLogger('gordon')
log.info('Using gordon directory %s', config.DEF_GORDON_DIR)


#------------------
#Helper functions
#-------------------            
#we have some values cached (album.trackcount, artist.trackcount) 
#after we do our cascading deletes we need to update those things....

def reassign_artist(oldid,newid) :
    """Reassigns all tracks and albums from oldid to newid then
    deletes old artist."""
    oldartist = Artist.query.get(oldid)
    newartist = Artist.query.get(newid)

    if not oldartist :
        raise ValueError('Bad id for oldartist')
    if not newartist :
        raise ValueError('Bad id for newartist')

    print "Tracks"
    for t in oldartist.tracks :
        print t
        if len(t.artists)==0 :
            print 'Missing artist'
        elif len(t.artists)==1 :
            if t.artists[0]==oldartist :
                t.artists[0]=newartist
                t.artist=newartist.name
                print 'Reassigned',oldartist,'to',newartist
                
            else :
                print 'Mismatched artist'
        else :
            print 'Multiple artists'

    print "Albums"
    for r in oldartist.albums :
        print r
        for idx in range(len(r.artists)) :
            a = r.artists[idx]
            if a==oldartist :
                r.artists[idx]=newartist
                print "Replaced",oldartist,"with",newartist


    print "Updating trackcount"
    newartist.update_trackcount()
    session.delete(oldartist)
    commit()

def delete_source(source) :
    """Deletes all tracks and albums for a given source. The source is 
    stored in the Track. Must be run interactively because it runs gordon_validate
    which asks questions at the prompt"""

    #This woudl be the "right" way to do it but it's slow because
    #we update track count on every track
    #for t in Track.query.filter_by(source=source) :
    #    print 'Deleting',t
    #    delete_track(t)


    for t in Track.query.filter_by(source=source) :
        print 'Deleting',t
        session.delete(t)
    commit()
    gordon_validate()

def delete_album(album) :
    #we handle cascading deletes ourselves for track and artist
    for t in album.tracks :
        artists = t.artists 
        session.delete(t)
        for a in artists :
            a.update_trackcount()
    session.delete(album)
    commit()
    
def delete_track(track) :
    session.delete(track)
    session.flush()  #should this be a commit?

    # Updating albums and artists too
    
    for a in track.albums :
        a.update_trackcount()
        if a.trackcount==0 :
            session.delete(a)

    for a in track.artists :
        a.update_trackcount()
        if a.trackcount==0 :
            session.delete(a)

    commit()

def deaccent_unicode(s):
    if not isinstance(s,unicode) :
        return s
    #save some time by checking if we already have an ascii-compatable string
    if s==s.encode('ascii','replace') :
        return s
    #we don't have an ascii-compatable string so translate it
    return s.translate(unaccented_map())

def delete(rec) :
    session.delete(rec)

def command_with_output(cmd):
    cmd = unicode(cmd,'utf-8')
    #should this be a part of slashify or command_with_output?
    if platform=='darwin' :
        cmd = normalize('NFC',cmd)
    child = os.popen(cmd.encode('utf-8'))
    data = child.read()
#    err = child.close()
    child.close()
    return data

def postgres_column_to_str(col) :
    #transforms postgres column tos tring
    
    st = join(col)
    try :
        st = unicode(st,'utf-8')
    except :
        log.warning('Could not translate string '+st+' into utf-8 unicode')

    st = st.replace("'",'')
    st = st.replace('"','')
    st = st.replace('\n','')
    return st

class unaccented_map(dict):
    #Found on a newsgroup
    #Fredrik Lundh fredrik at pythonware.com
    #Fri Mar 24 20:37:03 CET 2006
    
    #import sys
    #import unicodedata
    CHAR_REPLACEMENT = {
        0xc6: u"AE", # LATIN CAPITAL LETTER AE
        0xd0: u"D",  # LATIN CAPITAL LETTER ETH
        0xd8: u"OE", # LATIN CAPITAL LETTER O WITH STROKE
        0xde: u"Th", # LATIN CAPITAL LETTER THORN
        0xdf: u"ss", # LATIN SMALL LETTER SHARP S
        0xe6: u"ae", # LATIN SMALL LETTER AE
        0xf0: u"d",  # LATIN SMALL LETTER ETH
        0xf8: u"oe", # LATIN SMALL LETTER O WITH STROKE
        0xfe: u"th", # LATIN SMALL LETTER THORN
        }
    def mapchar(self, key):
        ch = self.get(key)
        if ch is not None:
            return ch
        ch = unichr(key)
        try:
            ch = unichr(int(decomposition(ch).split()[0], 16))
        except (IndexError, ValueError):
            ch = self.CHAR_REPLACEMENT.get(key, ch)
        # uncomment the following line if you want to remove remaining
        # non-ascii characters
        # if ch >= u"\x80": return None
        self[key] = ch
        return ch
    if version >= "2.5":
        __missing__ = mapchar
    else:
        __getitem__ = mapchar

def _set_perms(path, perm, groupName=None) :
    if os.name == 'nt': return #jorgeorpinel: may render file unreadable on Windows ... check out cacls for cmd.exe
    os.system('chmod %d "%s"' % (perm, path))
    #if os.system("chmod %d %s" % (perm, path))>0 :
    #    print "Error executing chmod %d on %s" % (perm, path)
    if groupName:
        os.system('chgrp %s "%s"' % (groupName, path))
        #if os.system("chgrp %s %s" % (groupName, path))>0 :
        #    print "Error changing group of %s to %s" % (path, groupName)
        pass

def make_subdirs_and_move(src,tgt) :    
    make_subdirs(tgt)
    move(src,tgt)

def make_subdirs_and_copy(src, tgt) :    
    make_subdirs(tgt)
    copy(src, tgt)
    _set_perms(tgt, 664)

def make_subdirs(tgt) :
    """Make target directory.

    If necessary, also set permissions for any subdir we make!"""
    parts = os.path.abspath(tgt).split(os.sep)
    subdir = '' if os.name <> 'nt' else parts[0] #jorgeorpinel: part[0] is the drive letter in Windows
    for part in parts[1:len(parts)-1] :
        subdir = subdir + os.sep + part
        if not os.path.isdir(subdir) :
            print ' * creating dir', subdir
            os.mkdir(subdir)
            _set_perms(subdir, 775) #jorgeorpinel: no effect on Windows

def get_albumcover_filename(aid) :
    return '%s/A%s_cover.jpg' % (get_tiddirectory(aid), str(aid))


def get_full_albumcovername(aid, gordonDir=config.DEF_GORDON_DIR) :
    """Returns the full album cover name.

    If gordonDir is not provided, we use config.DEF_GORDON_DIR as the prefix.
    """
    return os.path.join(gordonDir, 'data', 'covers', get_albumcover_filename(aid))

def get_full_audiofilename(tid,gordonDir=config.DEF_GORDON_DIR) :
    """Returns the full audio file name.

    If gordonDir is not provided, we use config.DEF_GORDON_DIR as the prefix.
    """
    return os.path.join(gordonDir,'audio','main',get_tidfilename(tid))

def get_tidfilename(tid, ext='mp3', featurestub='') :
    '''Gets the path to the track with <tid> filename from audio/main in gordonDir
    If the record doesn't exist yet or doesn't have 'path' attribute, one is created
    <ext> is the expected audio file extension
    <featurestub> seems to be intended for feature file extentions further to .mp3 or .wav, etc'''
    from model import query as squery
    
    fn = squery(Track.path).filter_by(id=tid).first()
    if fn is None or fn[0] == '': # creates the path with the expected file ext:
        fn = os.path.join(get_tiddirectory(tid), 'T%s.%s' % (tid, ext))
    else:   # retrieves the path from DB (ignoring <ext>)
        fn = fn[0]
    
    if featurestub <> '' :
        fn = '%s.%s' % (fn, featurestub)
    return fn

def get_tiddirectory(tid) :
    dr=''
    if type(tid)==str or type(tid)==unicode :
        if tid[0]=='T' :
            tid=tid[1:]
        try :
            tidint = int(tid)
            t=tidint/1000.0
            ceil=int(t+1)*1000
            dr= str(ceil)
        except :
            pass
    else:
        t=tid/1000.0
        ceil=int(t+1)*1000
        dr= str(ceil)

    return dr

def get_tidfilename_new(tid) :
    return '%s/%s' % (get_tiddirectory_new(tid),'T%s.mp3' % tid)

def get_tiddirectory_new(tid) :
#    dr=''
    if type(tid)==str or type(tid)==unicode and tid[0]=='T' :
        tid=tid[1:]
    try :
        tid = int(tid)
    except :
        raise ValueError('Cannot parse TID %s' % str(tid))
    
    t=tid/1000.0
    ceil=int(t+1)*1000
    dr= str(ceil)

    res = tid-(ceil-1000)
    t=res/100.0
    ceil=int(t+1)*100
    subdr= str(ceil)

    return '%s/%s' % (dr,subdr)

# read a list of strings in filefnIn, one per line
# @return list of strings
def read_string_list(fnIn) :
    fid = open(fnIn,'r')
    l = list()
    for line in fid.xreadlines() :
        if line == '' or line.strip() == '':
            continue
        l.append( line.strip() )
    fid.close()
    return l

def update_secs_zsecs(tid_or_track,force=False,fast=False,do_commit=True):
    """Updates the seconds and optionally zero-stripped seconds (sec,zsec) for a track
    Takes either a Track object or a track id.  
    If force is False (default) then only computes if values are missing
    If fast is True we don't decode the file. Instead we read in times from track header.  
    Also we set zsecs to -1 if it is not already...

    If do_commit is true, we commit this to the database. Otherwise we do not"""

    #album 6451 does not work for our audioio
    if isinstance(tid_or_track,Track) :
        track=tid_or_track
    else :
        track = Track.query.get(tid_or_track)

    if track==None :
        raise ValueError('Track for id %i not found in update_secs_zsecs' % tid_or_track)

    #fast case we only update the secs

    #the defaults for these is -1 in the database. There should be no NULL values
    if track.secs is None :
        track.secs=-1
    if track.zsecs is None:
        track.zsecs=-1

    if force or (fast and track.secs<=0) or ((not fast) and (track.secs<=0 or track.zsecs <=0)) :
        a = AudioFile(track.fn_audio)
        if fast :  #update secs but not zsecs based on file header (no decoding)
            zsecs=-1
            (fs,chans,secs)=a.read_stats()
        else :     #update both secs and zsecs by decoding file and actually working with audio (more accurate)
            secs, zsecs = a.get_secs_zsecs()
        track.secs=secs
        track.zsecs=zsecs
        print 'Processed track',track.id,secs,zsecs
        if do_commit :
            commit()
        
    return (track.secs,track.zsecs) 
   
#END Helper functions


##-----------------------
#validation of database / audio
#------------------------

def get_raw_yesno(msg) :
    while True:
        ans = raw_input('%s (y/n) > ' % msg)
        if ans=='y' :
            return True
        if ans=='n' :
            return False

def verify_delete(vals,msg) :
    print vals.count(),msg
    if vals.count()==0 :
        return
    
    for v in vals:
        print v
    if get_raw_yesno('Delete them?') :
        for v in vals :
            try  :
                session.delete(v)
                session.flush()
            except :
                print 'Could not delete',v,'probably because there are artist_sims for this artist'

def check_missing_mp3s(deleteMissing=False, gordonDir=config.DEF_GORDON_DIR) :
    print 'Checking for missing mp3s... this takes a while'
    for t in Track.query.all() :
        mp3=os.path.join(gordonDir,'audio','main',get_tidfilename(t.id))
        if not os.path.exists(mp3) :
            if deleteMissing :
                print 'Deleting',t
                delete_track(t)
            else :
                print t.id,'missing mp3',mp3,'!'

def check_orphans_new(gordonDir=config.DEF_GORDON_DIR,doFeatures=False, doMp3s=True) :
    """Finds tracks and features on disk for which there is no Track record.

    The opposite (db recs missing mp3s) is done below in gordon_validate()
    """
    #this could be faster if I built two sets, one of tids from db, other of tids from database
    #this is indeed the faster version! 

    db_tids=get_valid_tids()  #all tids as ints

    file_tids=list()
    if doMp3s :
        print 'Checking for tracks having no database record'
#        currDir = os.getcwd()
        os.chdir(os.path.join(gordonDir,'audio','main'))
        for root,dirs,files in os.walk('.') :
            print 'Checking directory',root
            for f in files :
                if f.endswith('.mp3') :
                    vals = f.split('.')
                    try :
                        tid=int(vals[0][1:])
                        file_tids.append(tid)
                    except :
                        pass

        db_tids=set(db_tids)
        file_tids=set(file_tids)
        orphans=file_tids-db_tids
        for o in orphans :
            f= get_tidfilename(o) 
            print 'Orphan',f
            inF =os.path.join(gordonDir,'audio','main',f)
            outF=os.path.join(gordonDir,'audio','offline',f)
            print 'Moving',inF,'to',outF
            make_subdirs_and_move(inF,outF)

    if doFeatures :
        print 'Checking for orphan features'
#        currDir = os.getcwd()
        os.chdir(os.path.join(gordonDir,'data','features'))
        for root,dirs,files in os.walk('.') :
            print 'Checking directory',root
            for f in files :
                vals = f.split('.')
                try :
                    tid=int(vals[0][1:])
                except :
                    continue
                try :
                    Track.query.get(tid)
                except LookupError :
                    print 'Deleting orphan',f
                    os.unlink(os.path.join(root,f))

def check_orphans(gordonDir=config.DEF_GORDON_DIR,doFeatures=False, doMp3s=True) :
    """Finds tracks and features on disk for which there is no Track record.

    The opposite (db recs missing mp3s) is done below in gordon_validate().
    """

    #this could be faster if I built two sets, one of tids from db, other of tids from database
    if doMp3s :
        print 'Checking for tracks having no database record'
#        currDir = os.getcwd()
        os.chdir(os.path.join(gordonDir,'audio','main'))
        for root,dirs,files in os.walk('.') :
            print 'Checking directory',root
            for f in files :
                if f.endswith('.mp3') :
                    vals = f.split('.')
                    try :
                        tid=int(vals[0][1:])
                    except :
                        continue
                    try :
                        Track.query.get(tid)
                    except LookupError :
                        print 'Orphan',f
                        make_subdirs_and_move(os.path.join(root,f),os.path.join(gordonDir,'audio','offline',root,f))
    if doFeatures :
        print 'Checking for orphan features'
#        currDir = os.getcwd()
        os.chdir(os.path.join(gordonDir,'data','features'))
        for root,dirs,files in os.walk('.') :
            print 'Checking directory',root
            for f in files :
                vals = f.split('.')
                try :
                    tid=int(vals[0][1:])
                except :
                    continue
                try :
                    Track.query.get(tid)
                except LookupError :
                    print 'Deleting orphan',f
                    os.unlink(os.path.join(root,f))

def update_trackcounts() :
    update_artist_trackcounts()
    update_album_trackcounts()

def update_artist_trackcounts() :
    """Updates value Artist.trackcount which caches the number of
    tracks per artist for fast querying.
    """
    artists = Artist.query.all()
    for (ctr,a) in enumerate(artists) :
        a.update_trackcount()
        if ctr % 100 ==0 :
            session.flush()
            print 'Processed artist',ctr
    session.flush()

def update_track_times(fast=False) :
    """Updates track times and zsec times. If fast is true, we only update the time, not the ztime
    and we do it without decoding the mp3. If we fail, we just keep going."""
    if fast:
        tracks = Track.query.filter("secs is NULL OR secs<=0 ")
    else :
        tracks = Track.query.filter("secs is NULL OR zsecs is NULL or secs<=0 or zsecs <=0")
    cnt=tracks.count()

    print 'Calculating',cnt,'track times'
    for ctr,t in enumerate(tracks) :
        #the function update_secs_zsecs will skip those with valid sec,zsec
        try :
            update_secs_zsecs(t,force=False,fast=fast,do_commit=False)
            #print 'Recalculated %i of %i: %s' % (ctr,cnt,str(t))

        except:
            print "Unable to calculate track time for " + str(t)
        if ctr%1000==0 :
            print ctr,'...committing'
            commit()
    commit()

def update_album_trackcounts() :
    """Updates value Album.trackcount which caches the number of
    tracks per album for fast querying
    """
    albums= Album.query.all()
    for (ctr,a) in enumerate(albums) :
        a.update_trackcount()
        if ctr % 100 ==0 :
            session.flush()
            print 'Processed album',ctr
    session.flush()

def delete_duplicate_mb_albums() :
    """Identify and delete duplicate albums
    Only delete those albums labeled by musicbrainz.  We always keep
    the biggest (in bytes) complete album songs / features are
    preserved in offline directory.  If the track times are sufficiently different from the
    published track times, we skip and recommend user delete by hand. This is to avoid deleting
    a good import while leaving behind an erroneous import.  See the Track class in model.py
    """
    #cannot figure out how to do this without a select :
    s = select([album.c.mb_id, func.count(album.c.mb_id)]).group_by(album.c.mb_id).having(func.count(album.c.mb_id)>1)
    dupes=session.execute(s).fetchall()

    tt_std=200. #hand set in matcher. But not so important..
    import pg
    dbmb = pg.connect('musicbrainz_db',user=config.DEF_DBUSER,passwd=config.DEF_DBPASS,host=config.DEF_DBHOST)
    for [mb_id,count] in dupes :
        if len(mb_id.strip())<10 :
            continue
        dupealbums = Album.query.filter(func.length(Album.mb_id)>10).filter_by(mb_id=mb_id)


        #look up track times. This requires two queries. One to translate the mb_id (their published text key)
        #into an mb_numeric_id (their internal key). Then the query against the mb_numeric_id
        mb_numeric_id = dbmb.query("SELECT R.id FROM album as R, albummeta as AM WHERE R.gid = '%s' AND  AM.id = R.id" % mb_id).getresult()[0][0]
        q="""SELECT T.length  FROM track as T INNER JOIN albumjoin as AJ ON T.id = AJ.track 
             INNER JOIN artist as A ON T.artist = A.id WHERE AJ.album = %i ORDER BY AJ.sequence""" % mb_numeric_id
        mbtrackresult =numpy.array(dbmb.query(q).getresult())
        mbtimes=numpy.array(mbtrackresult[:,]).flatten()/1000.
        bytes=list()
        timeterms=list()
        for a in dupealbums :
            ttimes=numpy.array(map(lambda t: t.secs,a.tracks))
#            df=abs(ttimes-mbtimes)
            time_term=numpy.mean(numpy.exp(-(mbtimes/1000.0-ttimes/1000.0)**2/tt_std))
            currbytes=0
            for t in a.tracks :
                currbytes+=t.bytes
            bytes.append(currbytes)
            timeterms.append(time_term)
            
        
    
    
        keepidx=numpy.argmax(numpy.array(bytes))
        if timeterms[keepidx]<.9 :
            print 'Not deleting',dupealbums[keepidx] ,'because the time match is not very good. Do so by hand!'
            print '  Times to delete:',numpy.array(map(lambda t: t.secs,dupealbums[keepidx].tracks))
            print '  Times from MBrZ:',mbtimes
        else :
            for (idx,a) in enumerate(dupealbums) :
                if idx<>keepidx :
                    print 'Deleting',a,timeterms[idx]
                    delete_album(a)
    dbmb.close()

def check_nulls() :
    """Finds instances where trackcount, Artist.mb_id, Track.mb_id, Album.mb_id are null.
    This should not be the case and causes problems.
    """
    # For sqlalchemy queries (we treat empty string as "null" for
    # strings and don't want to have to query for both is None and
    # len==0).
    artists=Artist.query.filter('mb_id is NULL')
    if artists.count()>0 :
        print 'Fixing %i null mb_ids in artists' % artists.count()
        for a in artists:
            a.mb_id=''
        commit()
    else :
        print 'No null mb_ids in artists'

    albums=Album.query.filter('mb_id is NULL')
    if albums.count()>0 :
        print 'Fixing %i null mb_ids in albums' % albums.count()
        for r in albums:
            r.mb_id=''
        commit()
    else :
        print 'No null mb_ids in albums'

    tracks=Track.query.filter('mb_id is NULL')
    if tracks.count()>0 :
        print 'Fixing %i null mb_ids in tracks' % tracks.count()
        for t in tracks:
            t.mb_id=''
        commit()
    else :
        print 'No null mb_ids in tracks'

    artists=Artist.query.filter('trackcount is NULL')
    if artists.count()>0 :
        print 'Fixing %i null trackcounts in artists' % artists.count()
        for a in artists:
            a.trackcount=-1
        commit()
    else :
        print 'No null trackcounts  in artists'

    albums=Album.query.filter('trackcount is NULL')
    if albums.count()>0 :
        print 'Fixing %i null trackcounts in albums' % albums.count()
        for a in albums:
            a.trackcount=-1
        commit()
    else :
        print 'No null trackcounts  in albums'

def gordon_validate(gordonDir=config.DEF_GORDON_DIR,updateCounts=True,checkMissingMp3s=False,deleteMissingMp3Recs=False,checkOrphans=False,checkNulls=True,updateTrackTimes=False) :
    """This script does a lot of different validations. It is a good thing to run once a week"""

    #gets rid of null values in some fields. 
    if checkNulls :
        check_nulls()


    if updateTrackTimes :
        #will calculate track time from mp3 for missing track times
        update_track_times()


    #Finds track records which have no mp3 file (more serious)
    if checkMissingMp3s:
        check_missing_mp3s(gordonDir=gordonDir,deleteMissing=deleteMissingMp3Recs) 

    #these are necessary because I'm afraid to do cascading deletes for
    #orphaned tracks, albums, artists
    vals = Artist.query.filter_by(tracks=None)
    verify_delete(vals,'artists having no tracks')

    vals = Artist.query.filter_by(albums=None)
    verify_delete(vals,'artists having no albums')

    vals = Album.query.filter_by(artists=None)
    verify_delete(vals,'albums having no artists')

    vals = Album.query.filter_by(tracks=None)
    verify_delete(vals,'albums having no tracks')

    vals = Track.query.filter_by(artists=None)
    verify_delete(vals,'tracks having no artists')

    vals = Track.query.filter_by(albums=None)
    verify_delete(vals,'tracks having no albums')

    vals = Mbalbum_recommend.query.filter_by(album=None)
    verify_delete(vals,'mbalbum_recommend having no album')

    if updateCounts :
        print 'Updating artist and album trackcount values... this takes a while'
        update_trackcounts()  #this is not done automatically
        print 'Done updating counts'

    #finds files on disk which have no Track record
    if checkOrphans :
        check_orphans(gordonDir=gordonDir)

def get_albumcover_urltxt(asin) :
    #here we might be able to recover url from local cache
    albumcover_path=get_full_albumcovername(asin.id)        
    if os.path.exists(albumcover_path) :
        return '/cover/A%i.jpg' % asin.id

    if asin<>None and len(asin.strip())>5 :
        urltxt = 'http://ec1.images-amazon.com/images/P/%s.jpg' % asin.strip()
    else :
        urltxt = '/static/images/emptyalbum.jpg'
    return urltxt

def cache_albumcovers(aid=None) :
    """Caches album cover jpgs to directory config.DEF_GORDON_DIR/data/covers/K/A<aid>_cover.jpg

    TODO: needs a minor fix to keep from downloading empty jpgs from
    Amazon.  Amazon will sometimes return an empgy (800byte or so) jpg
    which should not be stored to disk.
    """
    import urllib2

    if aid is None :
        albums=Album.query.all()
    else :
        albums=[Album.query.get(aid)]

    for a in albums:
        fn_albumcover=a.fn_albumcover
        if os.path.exists(fn_albumcover) :# and gt 800 bytes 
            continue
    
        url=a.asin_url
        print a
        if url == '/static/images/emptyalbum.jpg' :
            print 'No image for',url
            continue

        #file does not exist and we have a valid url
        make_subdirs(fn_albumcover)
        try :
            print 'Cache',url,'to',fn_albumcover
            opener1 = urllib2.build_opener()
            pg = opener1.open(url)
            img = pg.read()
            fh = open(fn_albumcover, "wb")
            fh.write(img)
            fh.close()
            print 'Saved',a,'to',
            sleep(.2)
            _set_perms(fn_albumcover,644)
        except :
            print 'Failed on',a
 
def get_valid_tids(limit=-1,features_only=False) :
    """ Returns ordered list of all valid tids in system. 

    If limit>0 then limit to that many ids

    If features_only is true then we return only tids with zsecs>15
    (where features should exist)
    """
    if limit>0 :
        lstr=' limit %i' % limit
    else :
        lstr=''

    if features_only :
        fstr=' where 15 <= zsecs'
    else :
        fstr=''

    query='select id from track%s order by id%s' % (fstr,lstr)
    
    tids = map(int,numpy.array(execute_raw_sql(query).fetchall()).flatten())
    return tids

def slashify(fname) :
    s_fname=replace(fname," ","\ ")
    s_fname=replace(s_fname,"\'","\\'")
    s_fname=replace(s_fname,"\"","\\\"")
    s_fname=replace(s_fname,"(","\(")
    s_fname=replace(s_fname,")","\)")
    s_fname=replace(s_fname,"&","\&")
    s_fname=replace(s_fname,";","\;")
    s_fname=replace(s_fname,"$","\$")
    s_fname=replace(s_fname,"/","\/") # linux specific
    s_fname=replace(s_fname,",","\,")
    s_fname=replace(s_fname,"-","\-")
    return s_fname



def add_to_collection(tracks, name):
    """Adds a python collection of SQLA Track objects to a given Gordon collection (by name)
    @raise AttributeError: when the <tracks> passed are not gordon.db.model.Track (sqla) instances
    @author: Jorge Orpinel <jorge@orpinel.com>"""
    
    collection = Collection.query.filter_by(name=unicode(name)).first()
    if not collection:
        # Create the collection if non existant.
        collection = Collection(name=unicode(name))
    
    for track in tracks:
        try:
            collection.tracks.append(track)
        except AttributeError:
            log.warning('Track %s does not appear to be a gordon Track. '
                        'Skipping...', track)
            raise
        
    commit()
        
    return collection

def is_binary(filename):
    """Return true if the given filename is binary.
    @raise EnvironmentError: if the file does not exist or cannot be accessed.
    @attention: found @ http://bytes.com/topic/python/answers/21222-determine-file-type-binary-text on 6/08/2010
    @author: Trent Mick <TrentM@ActiveState.com>
    @author: Jorge Orpinel <jorge@orpinel.com>"""
    
    try: fin = open(filename, 'rb')
    except EnvironmentError:
        log.error("Can't open %s.", filename)
        raise
    
    try:
        CHUNKSIZE = 1024
        while 1:
            chunk = fin.read(CHUNKSIZE)
            if '\0' in chunk: # found null byte
                return True
            if len(chunk) < CHUNKSIZE:
                break # done
    # A-wooo! Mira, python no necesita el "except:". Achis... Que listo es.
    finally:
        fin.close()
    
    return False

