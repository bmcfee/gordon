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

'''Support for resolving albums in the Gordon database agains MusicBrainz'''

from numpy import *
import pg
from model import *
from sqlalchemy import *
import heapq,time,shutil,os,string,datetime,stat,copy,sys,glob,random # unused
#from sqlalchemy.databases.postgres import PGArray # try from sqlalchemy.dialects.postgresql.base import PGArray
from collections import defaultdict
import traceback

import dse_difflib as DL #short term replacement until 200-char limit is addressed
from gordon_db import *
from gordon.io.mp3_eyeD3 import * 

#---------------------
#Resolver code
#---------------------

class GordonResolver(object) :
    """This class resolves Gordon id3 data to MusicBrainz."""
    
    def __init__(self) :
        self.dbmb = pg.connect('musicbrainz_db',user=DEF_DBUSER,passwd=DEF_DBPASS,host=DEF_DBHOST)
        
    def __del__(self) :
        self.dbmb.close()

    def resolve_all_albums(self) :
        """Run the main resolver. Resolves all unresolved albums in Gordon database against MusicBrainz database. Writes results to our db (via resolve_album)"""

        albums = Album.query.filter_by(mb_id='').order_by('id DESC')

        #these get built once to find artists... faster than rebuilding for each album
        #load in the mbart data one time
       
        mbart = self.dbmb.query("SELECT DISTINCT ON (artist.id) artist.name,artist.gid,artist.id FROM artist RIGHT JOIN album ON album.artist = artist.id ORDER BY artist.id").getresult()
        #lower case artists names ordered by artist id
        mbart_lc_list = map(string.lower,asarray(mbart)[:,0])

        ln = albums.count()
        ctr=0
        for a in albums:
            print 'Processing %i of %i' % (ctr,ln)
            self.resolve_album(id=a.id,mbart=mbart,mbart_lc_list=mbart_lc_list)
            ctr+=1

    def resolve_album(self,id,mbart='',mbart_lc_list='') :
        """Resolves a single album in Gordon database against MusicBrainz database. Returns closes music brainz album and writes that info to our database"""
        (win_album,win_mb_id,(conf,conf_album,conf_artist,conf_track,conf_time),reorder_dict)=self._closest_mb_album(id,mbart=mbart,mbart_lc_list=mbart_lc_list)


        #turn reorder dictionary to string
        reorder_str = str(reorder_dict)
        #get other values

        try :
            gordon_album=Album.query.get(id).name
            gordon_artist=Album.query.get(id).artists[0].name
        except:
            print 'Temporary patch here to get around failure for a track missing an artist. TODO: fixme'
            return ''

        recs=Mbalbum_recommend.query.filter_by(album_id=id)
        for r in recs :
            session.delete(r)
        commit()


        if len(win_mb_id)==0 :
            x=''
            pass
            #print 'Not writing record. no winner'
        else :
            print 'Winner is',win_mb_id,'with',conf,'album=',conf_album,'artist=',conf_artist,'track=',conf_track,'time=',conf_time
            #HERE
            [album,mbrid,artist]=self.dbmb.query("""SELECT album.name, album.id, artist.name
            FROM album,artist WHERE album.gid='%s' AND artist.id=album.artist""" % win_mb_id).getresult()[0]
            mb_album=album.decode('utf-8')
            mb_artist=artist.decode('utf-8')
            x=Mbalbum_recommend(album_id=id,mb_id=win_mb_id,gordon_artist=gordon_artist,gordon_album=gordon_album,
                                mb_artist=mb_artist,mb_album=mb_album,conf=conf,
                                conf_album=conf_album,conf_artist=conf_artist,
                                conf_track=conf_track,conf_time=conf_time,trackorder=reorder_str)
            x.album=Album.query.get(id)
            commit()
            y=Album.query.get(id)
            y.recommend.append(x)
            print 'Wrote value',x
            commit()
        return x



    def automatic_update_all_albums(self,conf=.8, conf_time=.95) :
        """Automatically updates Gordon data for albums meeting safe criteria (conf, conf_time)"""
        autoupdates = Mbalbum_recommend.query.filter(Mbalbum_recommend.album.has(or_(Album.mb_id=='',Album.mb_id==None)))
        autoupdates = autoupdates.filter(Mbalbum_recommend.album.has(~Album.status.any()))
        autoupdates = autoupdates.filter(Mbalbum_recommend.conf_time>conf_time).filter(Mbalbum_recommend.conf>conf).order_by("conf desc")
        
        cnt=autoupdates.count()
        for (idx,a) in enumerate(autoupdates) :
            print '%i of %i : Updating album %i' % (idx+1,cnt,a.album_id)
            #print a
            self.update_album(id=a.album_id,mb_id=a.mb_id,use_recommended_track_order=True,doit=True)
          



    def update_album(self,id,mb_id=-1,use_recommended_track_order=False,doit=True) :
        """
        Updates an album from MusicBrainz database
        1) writes mb_id to album table
        2) updates tracks with mb_ids
        3) fix name of album
        4) fix track names
        5) all of this is done using recommended track order from mbalbum_recommend
        """
        #if mb_id is not provided, presumes that album's stored mb_id is the one. This allows us to refresh from new mb db
        if mb_id==-1 :
            mb_id=Album.query.get(id).mb_id

        #collect all the data we need to update album
        result = self.dbmb.query("SELECT R.id, R.name, AM.asin  FROM album as R, albummeta as AM WHERE R.gid = '%s' AND  AM.id = R.id" % mb_id).getresult()
        if not len(result)==1 :
            print 'update_album cannot processes id',id,'mb_id',mb_id,'Mb_Id not found in mb database'
            return
        else :
            new_mbrid=result[0][0]
            new_albumname=result[0][1].decode('utf-8')
            new_asin=result[0][2]

        #we will make a dictionary of info for each track in mbalbum
        result = self.dbmb.query("""SELECT A.name, A.gid, T.name, T.gid, AJ.sequence FROM  (albumjoin as AJ INNER JOIN track as T on AJ.track = T.id)
        INNER JOIN artist as A ON T.artist = A.id WHERE AJ.album = %i""" % new_mbrid).getresult()
        newalbum=dict()
        for r in result :
            (new_artist,new_artist_mb_id,new_track,new_track_mb_id,new_tracknum) = r
            tdict=dict()
            tdict['artist']=new_artist.decode('utf-8')
            tdict['track']=new_track.decode('utf-8')
            tdict['track_mb_id']=new_track_mb_id
            tdict['artist_mb_id']=new_artist_mb_id
            newalbum[new_tracknum]=tdict

            #are we overriding the artist name?
            mbres = Mbartist_resolve.query.filter_by(mb_id=new_artist_mb_id)
            if mbres.count()==1 :
                #print 'Overriding musicbrainz artist name',deaccent_unicode(tdict['artist']),'with',mbres
                tdict['artist']=mbres[0].artist

        newtr = list(newalbum.keys())
        newtr.sort()

        #get existing tracks from our database
        oldalbum = Album.query.get(id)
        oldtracks = oldalbum.tracks


        #reorder the tracks via recommened ordering. This needs to be cleaned up
        res= Mbalbum_recommend.query.filter_by(album_id=id)
        if res.count()==1 and res[0].trackorder<>None :

            trackorder = eval(res[0].trackorder)
            if len(trackorder)==len(oldtracks) :
                trks = [0] * len(oldtracks)
                for t in oldtracks :
                    idx = trackorder[t.id]
                    print 'moving',t.id,'to',idx
                    trks[idx]=t
                oldtracks = trks
                print 'reorder by ',trackorder




        for t in oldtracks:
            if oldalbum.name <> t.album :
                print 'Album name not the same in all tracks for album %s' % deaccent_unicode(oldalbum.name)
                print 'Please fix...'
                return

        #we are sure that (as it should be) the album field in all tracks is equal to album name in album table.

        #update informmation concerning album name and mb_id
        if doit :
            oldalbum.name=new_albumname  #update album name in album table
            oldalbum.asin=new_asin       #update asin
            oldalbum.mb_id=mb_id           #update mb_id        
            for t in oldtracks:
                t.album=new_albumname
        else :
            pass
            #print 'Updating name and mb_id in album, updating name of album in tracks'

        #except for album name, everything else (artist, track name) can differ by track
        mp3_changed=False #trach whether we changed some mp3 information
        aid_changed=False #track whether we made some artist update

        newaids=set()  #new artists for this album
        oldaids=set()  #old artists for this album


        ctr=1 #this will allow us to match albums with inexact match on track numbering
        for track in oldtracks:#oldalbum.tracks:
            nentry = newalbum[ctr]
            if doit :
                #first remove links to existing artists
                #we do not enforce integrity here. We might leave behind an artist which is now an orphan.
                for a in track.artists :
                    oldaids.add(a.id)  #remember which artists we had for this album
                track.artists=[]

                #get new artist. First search for it in the database
                new_artist = Artist.query.filter_by(mb_id=nentry['artist_mb_id'])
                if new_artist.count()==0 :
                    #artist isn't there by mb_id. Generate a new one.
                    #This may mean we orphan an existing artist with the same name but it's safer this way I think
                    new_artist=Artist(name=nentry['artist'],mb_id=nentry['artist_mb_id'])
                    commit()
                    #print 'Generated new artist',new_artist
                else :
                    new_artist=new_artist[0]

                track.artists.append(new_artist)#addArtist(new_artist.id)
                newaids.add(new_artist.id)

                #update track fields
                track.album = new_albumname
                track.title = nentry['track']
                track.artist = nentry['artist']
                track.mb_id = nentry['track_mb_id']
                track.tracknum = ctr
                #print 'Setting tracknum for',track.id,'to',ctr
            #update the mp3 file
            self.update_mp3_from_db(track.id,doit=doit)
            ctr+=1
        if newaids <> oldaids :
            #an artist has changed. remove the old and add the new
            #for a in oldalbum.artists :
            #    oldalbum.removeArtist(a.id)
            oldalbum.artists=[]
            for aid in newaids :
                #oldalbum.addArtist(aid)
                #print 'AID is',aid
                artist = Artist.query.get(aid)
                #print artist
                oldalbum.artists.append(Artist.query.get(aid))
        #commit()
        flush()


    def update_mp3_from_db(self,tid,doit=False) : #todo: extend to non ID3 tags
        """Updates mp3 id3 data based on data from the database"""


        #the fields we want
        fieldnames=list(('title','artist','album','tracknum','compilation'))

        #get fields from database
        trk = Track.query.get(tid)
        d_fields=(trk.title,trk.artist,trk.album,trk.tracknum,trk.compilation)


        #get tags from mp3
        
        fullpath=get_full_mp3filename(tid)
        if not os.path.exists(fullpath) :
            print 'ERROR: Cannot update mp3 tags in',fullpath,'because file does not exist'
            return False
        
        m_fields  = id3v2_getval(fullpath,fieldnames)
        #for (idx,m) in enumerate(m_fields) :
        #    if type(m)==unicode :
        #        m_fields[idx]=unicode(m.encode('utf-8'),'utf-8')
        #        print 'type is now',type(m_fields[idx])


        #compare
        #print type(trk.title),'is title type'
        for i in range(len(fieldnames)) :
            #only write to id3 if there is a change to be made

            if not m_fields[i]==d_fields[i] :
                if doit :
                    id3v2_putval(fullpath,fieldnames[i],d_fields[i])
                else :
                    print m_fields[i],d_fields[i]
                    print 'Would modifiy file',tid,'field', fieldnames[i]


    def validate_album_data(self,id=-1, mode='auto', thresh=.79, force=True):
        """verify that tagged albums still have same info as found in musicbrainz.     
           when mode=='auto' will automatically make changes for anything wiht stringmatch threshold > thresh
           whem mode=='prompt' will *ALSO* do same auto updates but will prompt for user for changes
        when force==True we set all albums marked 'verified' in AlbumStatus to be marked 'unverified'
        calling with default params should be reasonably safe...
        the best way to use this function is to call it once with mode='auto' and force=True 
        this will clear out the verified recoreds (all records will evaluate) and will update all of the easy stuff and then
        then call it a second time with mode='prompt' and force=False to pick up all of the records which require user investigation
        """
        if force :
            #when we force we mark all records as unverified
            for asat in AlbumStatus.query.all() :
                if asat.status=='mb_verified' :
                    asat.status='mb_unverified'
            commit()

        if id==-1 :
            recs = Album.query.filter('LENGTH(mb_id)>0')
        else :
            recs = Album.query.filter_by(id=id)



        #verifies that albums with MBID have the right number of tracks. 
        for r in recs :

            #check to see if album is verified already 
            asat = AlbumStatus.query.filter_by(album_id=r.id).filter_by(status='mb_verified') 
            if asat.count()>0 :
                #print 'Skipping mb_verified album',r
                continue


            verified=True


            q="""SELECT M.tracks FROM album as R INNER JOIN albummeta as M ON R.id=M.id WHERE R.gid='%s'""" % r.mb_id
            result = self.dbmb.query(q).getresult()
            wrong_trackcount=False
            if len(result)==1 :
                mbtrackcount = result[0][0]
                if mbtrackcount <> r.trackcount :
                    print 'Fix by hand : %s bad track count musicbrainz.trackcount=%i for gordon trackcount=%i' % (r,mbtrackcount,r.trackcount)
                    wrong_trackcount=True
                    verified=False   #we do not try to fix bad track count.... that needs to be fixed by hand

            if not wrong_trackcount: 
                redo=False
                redo_thresh=1.0
                #check track ordering and naming of tracks

                result = self.dbmb.query("SELECT R.id, R.name FROM album as R, albummeta as AM WHERE R.gid = '%s' AND  AM.id = R.id" % r.mb_id).getresult()
                if len(result)<>1 :
                    #try to find
                    if len(r.tracks)>0 :

                       # q="""SELECT A.gid FROM track as T 
                       #      INNER JOIN albumjoin as AJ ON T.id = AJ.track 
                       #      INNER JOIN album as A ON AJ.album = A.id WHERE T.gid = '%s'""" % r.tracks[0].mb_id
                        q="""SELECT T.gid FROM track where T.gid = '%s'""" % r.tracks[0].mb_id
                        result2=self.dbmb.query(q).getresult()
                        print 'Executing query',q,'with len',len(result2)
                        if len(result2)>0:
                            print 'new album gid is',result2[0][0]


                    print 'Fix by hand: %s %s did not yield a unique lookup in the mb table. count=%i' % (r,r.mb_id,len(result))
                    verified=False
                else :
                    mbalbumid=result[0][0]
                    mbalbumname=unicode(result[0][1],'utf-8')
                    if mbalbumname<>r.name :
                    #    match = self._get_string_match(mbalbumname,r.name)
                    #    redo_thresh=min(redo_thresh,match)
                    #    print '%i match=%4.4f MBAlbumName=%s GordonAlbumName=%s' % (r.id,self._get_string_match(mbalbumname,r.name),mbalbumname.encode('utf-8'),r.name.encode('utf-8'))
                         match=1 #we don't care if the name changes provided track-level data is still ok
                         redo=True

                    q="""SELECT T.name, T.length, A.name, AJ.sequence FROM track as T INNER JOIN albumjoin as 
                         AJ ON T.id = AJ.track INNER JOIN artist as A ON T.artist = A.id WHERE AJ.album = %i ORDER BY AJ.sequence""" % mbalbumid

                    result = self.dbmb.query(q).getresult()                
                    for idx in range(len(result)) :
                        (mbtrackname,mbtracktime,mbalbumname,mbidx)=result[idx]
                        mbtrackname=unicode(mbtrackname,'utf-8')
                        mbalbumname=unicode(mbalbumname,'utf-8')
                        mbtracktime=float(mbtracktime)
                        gordontrackname=r.tracks[idx].title
                        gordonidx=r.tracks[idx].tracknum
                        match1 = self._get_string_match(mbtrackname,gordontrackname)  #this gives us an idea of string match

                        gordontime=r.tracks[idx].secs*1000                      #this gives us an idea of track length
                        time_term=abs(mbtracktime-gordontime)/(mbtracktime+gordontime+.000001)
                        match2 = max((0.0,1.0-time_term))                    
                        match = max(match1,match2)
                        redo_thresh=min(redo_thresh,match)
                        if mbtrackname<>gordontrackname :
                            print '%s timematch %4.4f namematch=%4.4f MBName=%s GordonName=%s' % (r,match2,match1,mbtrackname.encode('utf-8'),gordontrackname.encode('utf-8'))
                            redo=True
                        if mbidx<>gordonidx :
                            print '%s MBTracknum=%i GordonCount=%i' % (r,mbidx,gordonidx)
                            redo=False
                            break


                if redo :
                    verified=False
                    if redo_thresh>thresh :
                        print 'Automatic update of',r.id
                        self.update_album(id=r.id)
                        verified=True
                    else :
                        if mode=='prompt' :
                            print ''
                            print ''
                            if get_raw_yesno('Update?') : 
                                self.update_album(id=r.id)
                                verified=True
                        else :
                            print 'Skipping',r.id

                if verified: 
                    #if we've in fact verified our unverified record, write it to disk
                    asat = AlbumStatus.query.filter_by(album_id=r.id).filter_by(status='mb_unverified')
                    if asat.count()>=1 :
                        asat[0].status='mb_verified'
                        for i in range(1,asat.count()) :
                            session.delete(asat[i])
                    else :
                        new_rec= AlbumStatus(album_id=r.id,status='mb_verified')
                    print "Marking",r.id,"as mb_verified"
                    commit()

    #Album 3975 MBTrackcount 14  versus Album.trackcount 21  119685
    #Album 4529 MBTrackcount 12  versus Album.trackcount 15
    #Album 5204 MBTrackcount 13  versus Album.trackcount 14
    #Album 5431 MBTrackcount 13  versus Album.trackcount 26
    #Album 6541 MBTrackcount 14  versus Album.trackcount 28
    #Album 8144 MBTrackcount 11  versus Album.trackcount 12
    #Album 8669 MBTrackcount 11  versus Album.trackcount 12
    #MISNUMBERED
    #Album 8745 MBTrackcount 12  versus Album.trackcount 13



    def add_mbalbumdata_to_trackdict(self,mb_id,tracks) :
        """Takes a dictionary keyed by track number and adds MusicBrainz  artist, album, tracknumber data
        Returns tuple with (tracks, status) where status is True if successful creation of dictionary
        Failure results when we do not have the same number of tracks
        This is used by GordonWeb to display a comparaison of Gordon and MB album data"""


        [album,id]= self.dbmb.query("""SELECT name,id from album WHERE gid='%s'""" % mb_id).getresult()[0]
        q="""SELECT T.name, T.length, A.name, AJ.sequence FROM track as T INNER JOIN albumjoin as
        AJ ON T.id = AJ.track INNER JOIN artist as A ON T.artist = A.id WHERE AJ.album = %i ORDER BY AJ.sequence""" % id
        result = self.dbmb.query(q).getresult();


        if len(result)<> len(tracks) :
            return (tracks,False)  #unsuccessful merge of tracks

        for idx in range(len(result)) :
            (track,slen,artist,tracknum) = result[idx]
            tracks[idx].mb_artist = artist.decode('utf-8')
            tracks[idx].mb_album = album.decode('utf-8')
            tracks[idx].mb_track = track.decode('utf-8')
            tracks[idx].mb_tracknum = int(tracknum)
            tracks[idx].mb_secs = float(slen)/1000


        return (tracks,True)


    #HELPER Methods

    def _closest_mb_artists(self,artist,mbart='',mbart_lc_list='',k=5) :
        """returns triples for k-best (score, artist, artist_mb_id) matches for artist artist """


        if artist=='' :
            return (list(),mbart,mbart_lc_list)

        vals_by_artist = dict()
        korig=k
        artist = artist.encode('utf-8')
        mbartists = self.dbmb.query("SELECT DISTINCT ON (artist.id) artist.name,artist.gid,artist.id FROM artist RIGHT JOIN album ON album.artist = artist.id WHERE artist.name='%s'" % pg.escape_string(artist)).getresult()
        if len(mbartists)>0 :
            idxs=range(len(mbartists))
            artist_terms=ones((len(mbartists)))
            k=len(mbartists)

        else : #try case-insensitve search
            mbartists = self.dbmb.query("SELECT DISTINCT ON (artist.id) artist.name,artist.gid,artist.id FROM artist RIGHT JOIN album on album.artist = artist.id WHERE artist.name ILIKE '%s'" % pg.escape_string(artist)).getresult()

            if len(mbartists)>0 :
                idxs=range(len(mbartists))
                artist_terms=ones((len(mbartists)))
                k=len(mbartists)

            else :  #go a hunting'
                if len(mbart)==0 :
                    #lower case artists names ordered by artist id
                    print 'Building mbart list in _closest_mb_artist'
                    mbart = self.dbmb.query("SELECT DISTINCT ON (artist.id) artist.name,artist.gid,artist.id FROM artist RIGHT JOIN album ON album.artist = artist.id ORDER BY artist.id").getresult()
                    #lower case artists names ordered by artist id
                    mbart_lc_list = map(string.lower,asarray(mbart)[:,0])
                mbartists = mbart
                (idxs,artist_terms) = self._get_close_matches(artist.lower(),mbart_lc_list,korig,.8)

        l = list()
        for i in range(len(idxs)) :
            (mbartist,mmaid,mbaid) = mbartists[idxs[i]]
            l.append((artist_terms[i],mbartist,mmaid,mbaid))



        return (l,mbart,mbart_lc_list) #return mbart because the query is expensive to build




    def _closest_mb_album(self, id, mbart='',mbart_lc_list='',tbl='',k=5) :
        """returns pairs of mbartist, mbalbum hashes with our confidence in each 
        tracktimes and tracktitles must be dictionaries keyed by trackidx
        if they are empty, no track info will be considered
        tbl is the stub for the table if we are using an imported table."""

        print 'Processing release id',id,
        tic=time.time()
        artists=list()
        titles=list()
        times=list()

        smatcher = DL.SequenceMatcher()
        #k is the number of artists to consider


        try :
            albumrec = Album.query.get(id)
        except :
            print 'Album',id,'does not exist'
            return ('','',(0,0,0,0,0),dict())

        album = albumrec.name
        mb_id = albumrec.mb_id

        tids=list()
        subtic=time.time()
        for t in albumrec.tracks :
            artists.append(t.artist)
            titles.append(t.title)
            times.append(t.secs*1000.0)
            tids.append(t.id)

        titles=array(titles)
        times=array(times)
        trackcount=len(times)
        totaltime=0
        if len(times)>0 :
            totaltime=sum(times)



        titlestr=string.join(titles).replace("'",'').replace('"','').replace('\n','')
        artiststr=string.join(artists).replace("'",'').replace('"','').replace('\n','')

        #all the artists we are concerned in finding
        artists = array(list(set(artists)))
        artists_results=dict()
        for a in artists :
            if not a.lower()== 'various artists' :
                (res,mbart,mbart_lc_list) = self._closest_mb_artists(a,mbart,mbart_lc_list)
                artists_results[a]=res


        dtime=time.time()-tic

        #generate a set of candidate albums
        mbalbumresult=list()


        tic=time.time()
        for tgt_artist in artists_results.values() :
            for a in tgt_artist :
                #print 'Searching albums for artists',deaccent_unicode(a)
                (strn,artist,mbrid,mbaid)=a
                if trackcount>0 :
                    q="SELECT DISTINCT ON (R.id) R.name, R.gid, R.id  FROM album as R INNER JOIN albummeta as M ON R.id=M.id WHERE M.tracks = %i and R.artist = %i" % (trackcount,mbaid)
                else:  #no tracks sent in so search for any album
                    q="SELECT DISTINCT ON (R.id) R.name, R.gid, R.id  FROM album as R INNER JOIN albummeta as M ON R.id=M.id WHERE R.artist = %i" % (mbaid)
                result = self.dbmb.query(q).getresult()
                for r in result :
                    #print 'Adding album',r
                    mbalbumresult.append(r)


    #3f1163d1-98ef-418a-8ef3-c6e214ddd248
    #e2c495716b0af606f3c8be86a0cb6610
        #searching for soundtracks.

        qcnt=0
        rcnt=0

        for tgt_artist in artists_results.values() :
            for a in tgt_artist :  
                #POSTGRES command create view soundtrack_album as select * from album where artist=1 and 5=any(attributes);
                #print 'Searching soundtracks for artists',deaccent_unicode(a)
                (strn,artist,mbrid,mbaid)=a
                if trackcount>0 :
                    q="""SELECT DISTINCT ON (R.id) R.name, R.gid, R.id FROM album as R, albumjoin as AJ, albummeta as M, track as T 
                    WHERE AJ.album=R.id
                    AND T.id=AJ.track AND T.artist = %i
                    AND M.id=R.id AND M.tracks=%i
                    AND R.artist=1 AND 5 = any(R.attributes)
                    """ % (mbaid,trackcount);

                    result = self.dbmb.query(q).getresult()
                    for r in result :
                        #print 'Adding album',r
                        mbalbumresult.append(r)

                    qcnt+=1
                    rcnt+=len(result)



        tic=time.time()

        if len(mbalbumresult)==0 :
            print 'no result for album'
            return ('','',(0,0,0,0,0),dict())


        mbalbumresult = list(set(mbalbumresult))
        k2=len(mbalbumresult)
        album_terms=ones((k2))
        track_terms=ones((k2))
        reorder_dicts=list()
        artist_terms=ones((k2))
        time_terms=ones((k2))
        mix_terms=ones((k2)) 

        win_albums=list()

        tt_std=200. #set by hand so that time matches of 5 sec or better are reasonably probable.


        for ridx in range(k2):
            (mbalbum,mb_id,mbrid)=mbalbumresult[ridx]


            #if not mb_id.startswith('c041') :
            #    print 'Debug skipping in gordon.py'
            #    contin
            album_terms[ridx]= self._get_string_match(album.lower(),mbalbum.lower(),smatcher)
            #get track info for potential match


            print 'Selected',mbalbum,mb_id,mbrid

            if trackcount > 0 :
                q="""SELECT T.name, T.length, A.name, AJ.sequence FROM track as T INNER JOIN albumjoin as
                AJ ON T.id = AJ.track INNER JOIN artist as A ON T.artist = A.id WHERE AJ.album = %i ORDER BY AJ.sequence""" % mbrid

                mbtrackresult =array(self.dbmb.query(q).getresult())
                mbtitlesstr=postgres_column_to_str(mbtrackresult[:,0])
                mbtimes=array(map(float,mbtrackresult[:,1]))
                mbartists=postgres_column_to_str(mbtrackresult[:,2])


                mb_titles = list()
                mb_artists = list()

                for i in range(shape(mbtrackresult)[0]) :
                    mb_titles.append(mbtrackresult[i,0])
                    mb_artists.append(mbtrackresult[i,2])


                if max(mbtimes)==0 :
                    #no times
                    #we assign a middling value to this. . .
                    #otherwise often a bad version with no track times in mb will win out over a better-labeled version in mb with track times
                    time_term=.8
                else :
                    #this measure is skewed by short songs because it's normalized by mbtime[i]+time[i]
                    #old
                    #time_term=sum(abs(mbtimes-times)/(mbtimes+times+.000001))/float(len(mbtimes))
                    #time_term=max((0.0,1.0-time_term))
                    #new
                    time_term=mean(exp(-(mbtimes/1000.0-times/1000.0)**2/tt_std))


                #for t1,t2 in zip(times/1000.,mbtimes/1000.) :
                #    print 't1sec=%4.4f t2sec=%4.4f diff=%4.4f prob=%4.4f' % (t1,t2,abs(t1-t2), exp(-((t1-t2)**2)/tt_std))
                print '  time %s probabilty %4.4f' % (mb_id,time_term)
                for t1,t2 in zip(times,mbtimes) :
                    print t1,t2,t1-t2
                

#we go song by song and take average match over songs for title and artist

                #track_term=_get_string_match(mbtitlesstr,titlestr,smatcher)
                track_term=0.0
                for idx in range(len(titles)) :
                    curr = self._get_string_match(mb_titles[idx].lower(),titles[idx].lower())
                    track_term+= curr
                track_term /= float(len(titles))

                #artist_term=_get_string_match(mbartists,artiststr,smatcher)
                artist_term=0.0
                for idx in range(len(artists)) :
                    curr = self._get_string_match(mb_artists[idx],artists[idx])
                    artist_term += curr
                artist_term /= float(len(artists))



                #if we have poorly numbered album, try reordering based on goodness of match to this album
                #This will override the terms above (repetitive but easy to code)




                #check to see if we need to look for reordering
                tnums=[t.tracknum for t in albumrec.tracks]     
                do_reorder =  tnums <> range(1,len(tnums)+1)

                reorder_dict=dict()
                reorder_idxs=[]
                #q=AlbumStatus.query.filter_by(album_id = rid)
                #if q.count()==1 :

                
                if do_reorder or 1:
                    #we have all zeroes. Find a reordering based on track times
                    mbidxs = argsort(mbtimes)
                    idxs = argsort(times)
                    mbsorted = mbtimes[mbidxs]
                    sorted = array(times)[idxs]


                    #this is repeated code which is a bad thing... same calc for time prob as above
                    #old
                    #time_term=sum(abs(mbsorted-sorted)/(mbsorted+sorted+.000001))/float(len(mbsorted))
                    #time_term=max((0.0,1.0-time_term))
                    #new
                    time_term=mean(exp(-(mbsorted/1000.0-sorted/1000.0)**2/tt_std))

                    reorder_idxs=zeros((len(mbidxs)),int)
                    reorder_idxs[idxs]=mbidxs

                    #check to see how good it is
                    reorder_comp_idxs=argsort(reorder_idxs)                
                    reorder_rtimes=times[reorder_comp_idxs]
                    #old
                    #reorder_time_term=sum(abs(mbtimes-reorder_rtimes)/(mbtimes+reorder_rtimes+.000001))/float(len(mbtimes))
                    #reorder_time_term=max((0.0,1.0-reorder_time_term))
                    #new
                    reorder_time_term=mean(exp(-(mbtimes/1000.0-reorder_rtimes/1000.0)**2/tt_std))

                    reorder_track_term=0.0
                    for idx in range(len(titles)) :
                        reorder_track_term+= self._get_string_match(mb_titles[idx].lower(),titles[reorder_comp_idxs[idx]].lower())
                    reorder_track_term /= float(len(titles))

                    #now try reordering based on track names
                    if len(set(titles))>1 :
                        name_reorder_idxs=list()
                        titleidxs = range(len(titles))
                        mb_titles2 = copy.copy(mb_titles) #we will destroy this cpy
                        for title in titles:
                            #(idxs,scores)=self._get_close_matches(unicode(title),unicode(mb_titles2))
                            (idxs,scores)=self._get_close_matches(title,mb_titles2)
                            winner = idxs[0]
#                            print titleidxs
#                            print winner
#                            print 'idxs',idxs
                            name_reorder_idxs.append(titleidxs[winner])
                            mb_titles2.pop(winner)
                            titleidxs.pop(winner)

                        #check to see how good it is
                        name_reorder_comp_idxs=argsort(name_reorder_idxs)                
                        name_reorder_rtimes=times[name_reorder_comp_idxs]
                        #old
                        #name_reorder_time_term=sum(abs(mbtimes-name_reorder_rtimes)/(mbtimes+name_reorder_rtimes+.000001))/float(len(mbtimes))
                        #name_reorder_time_term=max((0.0,1.0-name_reorder_time_term))
                        #new
                        name_reorder_time_term=mean(exp(-(mbtimes/1000.0-name_reorder_rtimes/1000.0)**2/tt_std))
                        name_reorder_track_term=0.0
                        for idx in range(len(titles)) :
                            name_reorder_track_term+= self._get_string_match(mb_titles[idx].lower(),titles[name_reorder_comp_idxs[idx]].lower())
                        name_reorder_track_term /= float(len(titles))

                        if (name_reorder_track_term+name_reorder_time_term)>(reorder_track_term+reorder_time_term):
                            reorder_idxs=name_reorder_idxs


                #now pick a winner between the two
                if len(reorder_idxs)>0 :
                    #reordered versions...
                    comp_idxs=argsort(reorder_idxs)                
                    rtimes=times[comp_idxs]
                    #old
                    #time_term=sum(abs(mbtimes-rtimes)/(mbtimes+rtimes+.000001))/float(len(mbtimes))
                    #time_term=max((0.0,1.0-time_term))
                    #new
                    time_term=mean(exp(-(mbtimes/1000.0-rtimes/1000.0)**2/tt_std))

                    track_term=0.0
                    for idx in range(len(titles)) :
                        curr = self._get_string_match(mb_titles[idx].lower(),titles[comp_idxs[idx]].lower())
                        track_term+= curr
                    track_term /= float(len(titles))

                    #build reorder dictionary
                    for idx in range(len(comp_idxs)) :
                        reorder_dict[tids[idx]]=reorder_idxs[idx]



                track_terms[ridx]=track_term
                time_terms[ridx]=time_term
                artist_terms[ridx]=artist_term
                reorder_dicts.append(reorder_dict)



        #mix_terms = album_terms * artist_terms * track_terms * time_terms
        mix_terms = (album_terms + artist_terms + track_terms + time_terms)/4.0
        #mix_terms = artist_terms * track_terms * time_terms
        win_idx = argmax(mix_terms)
        mix_term=mix_terms[win_idx]
        album_term=album_terms[win_idx]
        artist_term=artist_terms[win_idx]
        track_term=track_terms[win_idx]
        time_term=time_terms[win_idx]
        reorder_dict=reorder_dicts[win_idx]
        (win_album,win_mb_id,ignore)=mbalbumresult[win_idx]
        vals = map(float,(mix_term,album_term,artist_term,track_term,time_term))
        return (win_album,win_mb_id,vals,reorder_dict)


    def _get_string_match(self,word1,word2,s=-1) :
        if s==-1 :
            s = DL.SequenceMatcher()
        s.set_seq1(word1)
        s.set_seq2(word2)
        x=s.real_quick_ratio()
        if x<.6:
            return x
        x=s.quick_ratio()
        if x<.6:
            return x
        return s.ratio()


    def _get_close_matches(self,word, possibilities, n=3, cutoff=0):

        tic=time.time()
        #taken from difflib to return idx of winner as well as its score
        if not n >  0:
            raise ValueError("n must be > 0: %r" % (n,))
        if not 0.0 <= cutoff <= 1.0:
            raise ValueError("cutoff must be in [0.0, 1.0]: %r" % (cutoff,))
        result = []
        s = DL.SequenceMatcher()
        s.set_seq2(word)
        for idx in range(len(possibilities)) :
            x=possibilities[idx]
            s.set_seq1(x)
            if s.real_quick_ratio() >= cutoff and \
               s.quick_ratio() >= cutoff and \
               s.ratio() >= cutoff:
                result.append((s.ratio(), idx))



        #replace words with indexes

        # Move the best scorers to head of list
        result = heapq.nlargest(n, result)
        # Strip scores for the best n matches



        #ugly
        scores=list()
        idxs=list()
        for r in result :
            (score,idx)=r
            scores.append(score)
            idxs.append(idx)

        return (idxs,scores)


    #End Resolver 



def die_with_usage() :
    print 'Resolves Gordon database albums to MusicBrainz'
    print 'gordon_resolver.py <operation>'
    print 'Arguments:'
    print '<operation> is one of the following possiblities:'
    print '    resolve [id]   : resolves unresolved album(s) in Gordon database and saves those predictions. This does not actually'
    print '                     change the tracks, albums, artists. It simply predicts a musicbrainz album and stores that prediction.'
    print '                     Resolving ALL will take an hour or so! If [id] is provided, this is done for only that album.'
    print '    commit_safe    : commits safe unresolved albums. This actually writes the predictions to the track, album, artist databases'
    print '                     and modifies the mp3 id3 tags. To commit unsafe mids use the Gordon webserver.'
    print '    validate [id]  : validates *already-resolved* albums against current MusicBrainz database and saves any changes.' 
    print '                     For example, if the spelling of a track changed since we resolved an album to MusicBrainz,'
    print '                     we would incorporate those changes with this code. If [id] is provided, this is done for only that album'                   
    print ''
    print 'It is faster to be logged into %s' % DEF_DBHOST
    sys.exit(0) 

pass
##----MAIN ----
if __name__=='__main__' :
    if len(sys.argv)<2 :
        die_with_usage()


    res = GordonResolver()
    command=sys.argv[1]
    if command=='resolve' :
        if len(sys.argv)>=3 :
            id=int(sys.argv[2])
            print 'Resolving album',id
            res.resolve_album(id=id)
        else :
            print 'Resolving all albums'
            res.resolve_all_albums()
    elif command=='commit_safe' :
        print 'Committing safe predictions to database'
        res.automatic_update_all_albums()
    elif command=='validate' :
        if len(sys.argv)>=3:
            id=int(sys.argv[2])
            print 'Validating album',id,'against MusicBrainz data'
        else :
            id=-1
            print 'Validating all albums against MusicBrainz data'
        res.validate_album_data(id=id)
    else :
        die_with_usage()

      
        
