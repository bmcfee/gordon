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

import traceback
import time, string, sys, shutil#,difflib,os,heapq,datetime,stat,copy,glob,random
#from collections import defaultdict
from numpy import array, argmax

from sqlalchemy import func, select

from model import *
from config import *

from gordon.io.mp3_eyeD3 import * 
#from gordon.io import AudioFile

print 'gordon_db.py: using gordon directory',DEF_GORDON_DIR





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
    albums = track.albums
    artists = track.artists
    session.delete(track)
    session.flush()

    print 'Updating albums and artists'
    for a in albums :
        a.update_trackcount()
        if a.trackcount==0 :
            print 'Someone delete me!',a

    for a in artists :
        a.update_trackcount()
        if a.trackcount==0 :
            print 'Someone delete me!',a

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
  
#commit is defined in model.py      
#def commit() :
    #when we use these functions from the prompt we need to do some commiting
 #   session.flush()
    #try :
    #    session.flush()
    #except :
    #    print 'Unable to commit automatically. If you are in tgadmin shell, do not forget to commit!'
        
def command_with_output(cmd):
    cmd = unicode(cmd,'utf-8')
    #should this be a part of slashify or command_with_output?
    if sys.platform=='darwin' :
        cmd = unicodedata.normalize('NFC',cmd)
    child = os.popen(cmd.encode('utf-8'))
    data = child.read()
    err = child.close()
    return data

def postgres_column_to_str(col) :
    #transforms postgres column tos tring
    
    st = string.join(col)
    try :
        st = unicode(st,'utf-8')
    except :
        print 'Could not translate string',st,'into unicode'
    #commented out but maybe necessairy? st = unicode(st,'utf-8')
    st = st.replace("'",'')
    st = st.replace('"','')
    st = st.replace('\n','')
    return st


pass
#Found on a newsgroup
#Fredrik Lundh fredrik at pythonware.com
#Fri Mar 24 20:37:03 CET 2006

#import sys
import unicodedata
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

class unaccented_map(dict):
    def mapchar(self, key):
        ch = self.get(key)
        if ch is not None:
            return ch
        ch = unichr(key)
        try:
            ch = unichr(int(unicodedata.decomposition(ch).split()[0], 16))
        except (IndexError, ValueError):
            ch = CHAR_REPLACEMENT.get(key, ch)
        # uncomment the following line if you want to remove remaining
        # non-ascii characters
        # if ch >= u"\x80": return None
        self[key] = ch
        return ch
    if sys.version >= "2.5":
        __missing__ = mapchar
    else:
        __getitem__ = mapchar

def _set_perms(path, perm, groupName=None) : #jorgeorpinel: no effect on Windows
    os.system('chmod %d "%s"' % (perm, path))  #todo: check out cacls cmd.exe (Win) command later?
    #if os.system("chmod %d %s" % (perm, path))>0 :
    #    print "Error executing chmod %d on %s" % (perm, path)
    if groupName:
        os.system('chgrp %s "%s"' % (groupName, path))
        #if os.system("chgrp %s %s" % (groupName, path))>0 :
        #    print "Error changing group of %s to %s" % (path, groupName)

def make_subdirs_and_move(src,tgt) :    
    make_subdirs(tgt)
    shutil.move(src,tgt)

def make_subdirs_and_copy(src, tgt) :    
    make_subdirs(tgt)
    shutil.copy(src, tgt)
    _set_perms(tgt, 664)

def make_subdirs(tgt) :
    """Make target directory.

    If necessary, also set permissions for any subdir we make!"""
    parts = os.path.abspath(tgt).split(os.sep)
    subdir = '' if os.name <> 'nt' else parts[0] #jorgeorpinel: part[0] is the drive letter in Windows
    for part in parts[1:len(parts)-1] :
        subdir = subdir + os.sep + part
        if not os.path.isdir(subdir) :
            print 'gordon_db.py: creating dir', subdir # debug ----------------
            os.mkdir(subdir)
            _set_perms(subdir, 775) #jorgeorpinel: this has no effect on Windows

def get_albumcover_filename(aid) :
    return '%s/A%s_cover.jpg' % (get_tiddirectory(aid),str(aid))

def get_full_featurefilename(tid,gordonDir=DEF_GORDON_DIR) :
    """Returns the full feature file name.

    If gordonDir is not provided, we use DEF_GORDON_DIR as the
    prefix. Only valid for .h5 files since individual txt/bin files
    are named differently.
    """
    return os.path.join(gordonDir,'data','features','%s.h5' % get_tidfilename(tid))

def get_full_albumcovername(aid,gordonDir=DEF_GORDON_DIR) :
    """Returns the full album cover name.

    If gordonDir is not provided, we use DEF_GORDON_DIR as the prefix.
    """
    return os.path.join(gordonDir,'data','covers',get_albumcover_filename(aid))

def get_full_mp3filename(tid,gordonDir=DEF_GORDON_DIR) :
    """Returns the full audio file name.

    If gordonDir is not provided, we use DEF_GORDON_DIR as the prefix.
    """
    return os.path.join(gordonDir,'audio','main',get_tidfilename(tid))

def get_tidfilename(tid, featurestub='') :
    fn = os.path.join(get_tiddirectory(tid), 'T%s.mp3' % tid)
    if featurestub<>'' :
        fn = '%s.%s' % (fn,featurestub)
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
    dr=''
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


#END Helper functions

#------------------------
#Functions for working with features
#------------------------



#we really want to call just this one! 
def update_all(tid=-1,gordonDir=DEF_GORDON_DIR,force=False) :
    if tid==-1 :
        tids = get_valid_tids(features_only=True)
    else :
        tids=[tid]

    for (ctr,tid) in enumerate(tids) :
        if ctr%1000 == 0  :
            print 'update_all processing',tid
        try :
            #this will update all audio features
            update_features(tid,gordonDir=gordonDir,force=force)
            
        except :
            print 'Unable to update tid',tid
            traceback.print_exc()

def update_features(tid=-1,gordonDir=DEF_GORDON_DIR,force=False):
    #This shoudl update everything of importance. Because force is false, it should be relatively fast
    #when called on files where everything is already done. 
    #if called with no tid, we loop on entire database
    (secs,zsecs)=update_secs_zsecs(tid,gordonDir=gordonDir,force=force)
    if zsecs>=15:
        update_audio_features(tid,gordonDir=gordonDir,force=force)
        update_summarized_features(tid,gordonDir=gordonDir,force=force)
        #update_booster_features(tid,gordonDir=gordonDir,force=force)
      
    else :
        pass# print 'Skipping',tid,'because it is <15sec'
        
def update_secs_zsecs(tid,gordonDir=DEF_GORDON_DIR,force=False):
    #album 6451 does not work for our audioio
    track = Track.query.get(tid)
    if track==None :
        raise ValueError('Track for id %i not found in update_secs_zsecs' % tid)
    if force or track.secs==None or track.secs<0 or track.zsecs==None or track.zsecs <0 :
        fullpath = os.path.join(gordonDir,'audio','main',Track.query.get(tid).path)
        print 'Track',track.id,'gordondir',gordonDir,'with path',fullpath#'setting secs and zsecs',secs,zsecs
        a = AudioFile(fullpath)
        secs, zsecs = a.get_secs_and_zsecs()
        track.secs=secs
        track.zsecs=zsecs
        commit()
    return (track.secs,track.zsecs) 
   
def update_audio_features(tid,gordonDir=DEF_GORDON_DIR,force=False,params=dict()):
    ##this is a convenience function to be called by GORDONWeb
    #it simply calles calc_feat for default features (as defined in params.sfeat_features)
    #for tid
    from pygmy.audio import calc_feat as C
    #for p in params :
    #    print p,params[p]
    params = C.assert_defaults(params)    
    if force :
        action=C.FORCE
    else :
        action=C.COMPUTE
    for f in params['sfeat_features']:
        params['do_%s' % f] = action        
    shortMp3=get_tidfilename(tid)
    fullMp3=os.path.join(gordonDir,'audio','main',shortMp3)
    featDir=os.path.join(gordonDir,'data','features')
    #for p in params :
    #    print p,params[p]
    C.calc_feat(fullMp3,fnOutStub=shortMp3,fnOutDir=featDir,params=params)        
    set_feature_perms(tid,gordonDir)

def set_feature_perms(tid,gordonDir=DEF_GORDON_DIR) :
    """Sets permissions for newly-created files"""
    fn= Track.query.get(tid).fn_feature
    if os.path.exists(fn) :
        os.system('chgrp musique %s' % fn)
        os.system('chmod g+rw %s' % fn)

def update_summarized_features(tid,gordonDir=DEF_GORDON_DIR,force=False,params=dict()):
    from pygmy.audio import calc_feat as C
    params = C.assert_defaults(params)  
    #override default to compute the summarized features
    if force :
        params['do_sfeat']=C.FORCE
    else :
        params['do_sfeat']=C.COMPUTE
    update_audio_features(tid=tid,gordonDir=gordonDir,force=False,params=params)
    
def update_booster_features(tid,gordonDir=DEF_GORDON_DIR,force=False,params=dict()):
    from pygmy.audio import calc_feat as C

    params['boostDir']=os.path.join(gordonDir,'data','boosters')
    params = C.assert_defaults(params)  
    if force :
        action=C.FORCE
    else :
        action=C.COMPUTE
    for p in params :
        if p.startswith('do_bfeat') :
            params[p]=action
            print 'Setting',p,'to',action
#    for (k,v) in params.iteritems() :
#        print k,v
        
    update_audio_features(tid=tid,gordonDir=gordonDir,force=False,params=params)


#def read_feature_file(tid,feature,params_only=False,gordonDir=DEF_GORDON_DIR) :
#    #todo: get rid of this version. It's a dumb name and was replaced with get_feature
#    return get_feature(tid=tid,feattype=feature,params_only=params_only,gordonDir=gordonDir)


#def init_feature_cache(fn=os.path.join(DEF_GORDON_DIR,'data','features','sfeat.h5')) :

def get_feature(tid,feattype,params_only=False,gordonDir=DEF_GORDON_DIR) :
    """Returns (feature,params) for given tid. 
    If feature is not calculated, calls update_features(tid)
    Features include sfeat,acorr,logspec,mfcc"""
    from pygmy.audio import calc_feat as C
    shortMp3=get_tidfilename(tid)
    featDir=os.path.join(gordonDir,'data','features')
    featFn=os.path.join(featDir,'%s.%s' % (shortMp3,'h5'))
    if not os.path.exists(featFn) :
        update_features(tid)
        if not os.path.exists(featFn) :
            return ([],[])    
    return C.read_feature_file(featFn,feattype=feattype,params_only=params_only) 

#End feature functions


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

def check_missing_mp3s(deleteMissing=False, gordonDir=DEF_GORDON_DIR) :
    print 'Checking for missing mp3s... this takes a while'
    for t in Track.query() :
        mp3=os.path.join(gordonDir,'audio','main',get_tidfilename(t.id))
        if not os.path.exists(mp3) :
            if deleteMissing :
                print 'Deleting',t
                delete_track(t)
            else :
                print t.id,'missing mp3',mp3,'!'

def check_orphans_new(gordonDir=DEF_GORDON_DIR,doFeatures=False, doMp3s=True) :
    """Finds tracks and features on disk for which there is no Track record.

    The opposite (db recs missing mp3s) is done below in gordon_validate()
    """
    #this could be faster if I built two sets, one of tids from db, other of tids from database
    #this is indeed the faster version! 

    db_tids=get_valid_tids()  #all tids as ints

    file_tids=list()
    if doMp3s :
        print 'Checking for tracks having no database record'
        currDir = os.getcwd()
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
        currDir = os.getcwd()
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
                except SQLObjectNotFound :
                    print 'Deleting orphan',f
                    os.unlink(os.path.join(root,f))

def check_orphans(gordonDir=DEF_GORDON_DIR,doFeatures=False, doMp3s=True) :
    """Finds tracks and features on disk for which there is no Track record.

    The opposite (db recs missing mp3s) is done below in gordon_validate().
    """

    #this could be faster if I built two sets, one of tids from db, other of tids from database
    if doMp3s :
        print 'Checking for tracks having no database record'
        currDir = os.getcwd()
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
                    except SQLObjectNotFound :
                        print 'Orphan',f
                        make_subdirs_and_move(os.path.join(root,f),os.path.join(gordonDir,'audio','offline',root,f))
    if doFeatures :
        print 'Checking for orphan features'
        currDir = os.getcwd()
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
                except SQLObjectNotFound :
                    print 'Deleting orphan',f
                    os.unlink(os.path.join(root,f))

def update_trackcounts() :
    update_artist_trackcounts()
    update_album_trackcounts()

def update_artist_trackcounts() :
    """Updates value Artist.trackcount which caches the number of
    tracks per artist for fast querying.
    """
    artists = Artist.query()
    for (ctr,a) in enumerate(artists) :
        a.update_trackcount()
        if ctr % 100 ==0 :
            session.flush()
            print 'Processed artist',ctr
    session.flush()

def update_album_trackcounts() :
    """Updates value Album.trackcount which caches the number of
    tracks per album for fast querying
    """
    albums= Album.query()
    for (ctr,a) in enumerate(albums) :
        a.update_trackcount()
        if ctr % 100 ==0 :
            session.flush()
            print 'Processed album',ctr
    session.flush()

def delete_duplicate_mb_albums(gordonDir=DEF_GORDON_DIR) :
    """Identify and delete duplicate albums.

    Only delete those albums labeled by musicbrainz.  We always keep
    the biggest (in bytes) complete album songs / features are
    preserved in offline directory.  See the Track class in model.py
    """
    #cannot figure out how to do this without a select :
    s = select([album.c.mb_id, func.count(album.c.mb_id)]).group_by(album.c.mb_id).having(func.count(album.c.mb_id)>1)
    dupes=session.execute(s).fetchall()
    for [mb_id,count] in dupes :
        dupealbums = Album.query.filter(func.length(Album.mb_id)>10).filter_by(mb_id=mb_id)
        
        if dupealbums.count()==0 :
            print "Skipping mb_id",mb_id
            continue
        print mb_id
        bytes=list()
        
        for a in dupealbums :
            currbytes=0
            for t in a.tracks :
                currbytes+=t.bytes
            bytes.append(currbytes)
            print '  ',a,currbytes
        
        keepidx=argmax(array(bytes))
        print 'Keeping',keepidx
        for (idx,a) in enumerate(dupealbums) :
            if idx<>keepidx :
                print 'Deleting',a
                delete_album(a)

def check_nulls(gordonDir=DEF_GORDON_DIR) :
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

def gordon_validate(gordonDir=DEF_GORDON_DIR,updateCounts=True,checkMissingMp3s=False,deleteMissingMp3Recs=False,checkOrphans=False,checkNulls=True) :
    #this would be a good script to run once a week.  It does a lot of work. 

    #gets rid of null values in some fields. 
    if checkNulls :
        check_nulls()

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
    albumcover_path=gordon_db.get_full_albumcovername(row.id)        
    if os.path.exists(albumcover_path) :
        return '/cover/A%i.jpg' % row.id

    if asin<>None and len(asin.strip())>5 :
        urltxt = 'http://ec1.images-amazon.com/images/P/%s.jpg' % asin.strip()
    else :
        urltxt = '/static/images/emptyalbum.jpg'
    return urltxt

def cache_albumcovers(gordonDir=DEF_GORDON_DIR,aid=None) :
    """Caches album cover jpgs to directory DEF_GORDON_DIR/data/covers/K/A<aid>_cover.jpg

    TODO: needs a minor fix to keep from downloading empty jpgs from
    Amazon.  Amazon will sometimes return an empgy (800byte or so) jpg
    which should not be stored to disk.
    """
    import urllib2

    if aid is None :
        albums=Album.query()
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
            time.sleep(.2)
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
    
    tids = map(int,array(execute_raw_sql(query).fetchall()).flatten())
    return tids

def slashify(fname) :
    s_fname=string.replace(fname," ","\ ")
    s_fname=string.replace(s_fname,"\'","\\'")
    s_fname=string.replace(s_fname,"\"","\\\"")
    s_fname=string.replace(s_fname,"(","\(")
    s_fname=string.replace(s_fname,")","\)")
    s_fname=string.replace(s_fname,"&","\&")
    s_fname=string.replace(s_fname,";","\;")
    s_fname=string.replace(s_fname,"$","\$")
    s_fname=string.replace(s_fname,"/","\/") # linux specific
    s_fname=string.replace(s_fname,",","\,")
    s_fname=string.replace(s_fname,"-","\-")
    return s_fname
