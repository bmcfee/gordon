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
"""Gordon database model"""

import os, glob, logging, sys.stdout

from sqlalchemy import Table, Column, ForeignKey, String, Unicode, Integer, Index, Float, SmallInteger, Boolean, DateTime#,text,PassiveDefault,ForeignKeyConstraint,MetaData,Text #jorgeorpinel: unused
#from sqlalchemy.databases.postgres import PGArray #jorgeorpinel: unused
from sqlalchemy.orm import relation, sessionmaker, MapperExtension, backref#,dynamic_loader,column_property,deferred #jorgeorpinel: unused
from datetime import datetime #from sqlalchemy.sql.expression import text

from gordon.io import AudioFile #todo: this imports itself ultimately... code in this file is executed twice.

from gordon.db import config

log = logging.getLogger('Gordon.AudioIntake')
log.addHandler(logging.StreamHandler(sys.stdout))
log.setLevel(logging.DEBUG) #jorgeorpinel: for now, change DEBUG to INFO here to reduce verbosity (at production)



#Connects to PostgreSQL: #is this done 2ice??? are 2 connections opened?

try :     #this will try to use turbogears if we are already in the middle of a turbogears session
    import turbogears.database #@UnresolvedImport (for projects running only cmd-line)
    engine = turbogears.database.get_engine() #this should generate an exception if we have not properly configured via dev.cfg or prod.cfg
    from turbogears.database import mapper, metadata #@UnresolvedImport (for projects running only cmd-line)
    session = turbogears.database.session
    log.info('model.py: initialized turbogears connection to gordon database')  # debug (info)
    AUTOCOMMIT=False  

except :  #this will set up a scoped session using native sqlalchemy (no turbogears!)
#    import traceback,sys
#    traceback.print_exc(file=sys.stdout)

    from sqlalchemy.orm import scoped_session
    import sqlalchemy
    # works in SQLAlchemy 0.6
    dburl = 'postgresql://%s:%s@%s/%s' % (config.DEF_DBUSER, config.DEF_DBPASS,
                                          config.DEF_DBHOST, config.DEF_DBNAME)
    try:
        engine = sqlalchemy.create_engine(dburl)
    except ImportError:
        # Works in sqlalchemy 0.5.5
        dburl = dburl.replace('postgresql', 'postgres')
        engine = sqlalchemy.create_engine(dburl)

    Session = scoped_session(sessionmaker(bind=engine,autoflush=True, autocommit=True))
    session = Session()
    import sqlalchemy.schema
    metadata = sqlalchemy.schema.MetaData(None)
#    mapper = Session.mapper #jorgeorpinel: SQLA 0.5. This is deprecated... (see 4 lines down)
    log.info('model.py: intialized external connection to gordon database on %s  (SQL Alchemy ver. %s)' % (config.DEF_DBHOST, sqlalchemy.__version__)) #debug (info)
    AUTOCOMMIT=True
    
    #jorgeorpinel: this is a SQLA 0.5+ legacy workaround found at http://www.sqlalchemy.org/trac/wiki/UsageRecipes/SessionAwareMapper
    from sqlalchemy.orm import mapper as sqla_mapper
    def session_mapper(scoped_session):
        def mapper(cls, *arg, **kw):
            if cls.__init__ is object.__init__:
                def __init__(self, **kwargs):
                    for key, value in kwargs.items():
                        setattr(self, key, value)
                    scoped_session.add(self) # new mapped objects will be automatically added to the session
                cls.__init__ = __init__
            cls.query = scoped_session.query_property()
            return sqla_mapper(cls, *arg, **kw)
        return mapper
    mapper = session_mapper(Session)

#todo: test database connection!



# auto-generation code:


mbartist_resolve =  Table('mbartist_resolve', metadata,
    Column(u'artist', Unicode(length=256), primary_key=False),
    Column(u'mb_id', String(length=64, convert_unicode=False, assert_unicode=None), primary_key=False),
    Column(u'id', Integer(), primary_key=True, nullable=False, autoincrement=True),
    )
Index('mbartist_resolve_artist_idx',mbartist_resolve.c.artist, unique=False)
Index('mbartist_resolve_mb_id_idx',mbartist_resolve.c.mb_id, unique=False)

mbalbum_recommend =  Table('mbalbum_recommend', metadata,
    Column(u'id', Integer(), primary_key=True, nullable=False, autoincrement=True),
    Column(u'album_id', Integer(), ForeignKey('album.id'), index=True, nullable=False),
    Column(u'mb_id', String(length=64, convert_unicode=False, assert_unicode=None), default='', primary_key=False),
    Column(u'mb_artist', Unicode(length=None), primary_key=False),
    Column(u'mb_album', Unicode(length=None), primary_key=False),
    Column(u'gordon_artist', Unicode(length=None), primary_key=False),
    Column(u'gordon_album', Unicode(length=None), primary_key=False),
    Column(u'conf', Float(precision=53, asdecimal=False), primary_key=False),
    Column(u'conf_artist', Float(precision=53, asdecimal=False), primary_key=False),
    Column(u'conf_album', Float(precision=53, asdecimal=False), primary_key=False),
    Column(u'conf_track', Float(precision=53, asdecimal=False), primary_key=False),
    Column(u'conf_time', Float(precision=53, asdecimal=False), primary_key=False),
    Column(u'trackorder', String(length=None, convert_unicode=False, assert_unicode=None), primary_key=False),
#    ForeignKeyConstraint([u'album_id'], [u'public.album.id'], name=u'album_id_exists'),
    )
Index('mbalbum_recommend_album_id_key', mbalbum_recommend.c.album_id, unique=True)
Index('mbalbum_recommend_pkey', mbalbum_recommend.c.id, unique=True)


album =  Table('album', metadata,
    Column(u'id', Integer(), primary_key=True, nullable=False, autoincrement=True),
    Column(u'mb_id', String(length=64, convert_unicode=False, assert_unicode=None), default='', primary_key=False),
    Column(u'name', Unicode(length=256), default='', primary_key=False),
    Column(u'asin', String(length=32, convert_unicode=False, assert_unicode=None), default='', primary_key=False),
    Column(u'trackcount', Integer(), default=-1, primary_key=False),
    Column(u'created_at', DateTime, default=datetime.now),#server_default=text("sysdate")
    )
Index('album_name_idx', album.c.name, unique=False)
Index('album_mb_id_idx', album.c.mb_id, unique=False)
Index('album_trackcount_idx', album.c.trackcount, unique=False)
Index('album_pkey', album.c.id, unique=True)


album_status =  Table('album_status', metadata,
     Column(u'id', Integer(), primary_key=True, nullable=False, autoincrement=True),
     Column(u'album_id', Integer(), ForeignKey('album.id'),nullable=False),
     Column(u'status', String(length=None), primary_key=False),
     )
Index('album_status_pkey', album_status.c.id, unique=True)

album_artist =  Table('album_artist', metadata,
    Column(u'album_id', Integer(), ForeignKey('album.id'), nullable=False),
    Column(u'artist_id', Integer(), ForeignKey('artist.id'),  nullable=False),
    Column(u'id', Integer(), primary_key=True, nullable=False, autoincrement=True)
    )
Index('artist2album_aid_idx', album_artist.c.artist_id, unique=False)
Index('artist2album_id_idx', album_artist.c.id, unique=False)
Index('artist2album_rid_idx', album_artist.c.album_id, unique=False)

album_track =  Table('album_track', metadata,
     Column(u'album_id', Integer(), ForeignKey('album.id'), nullable=False),
     Column(u'track_id', Integer(), ForeignKey('track.id'),  nullable=False),
     Column(u'id', Integer(), primary_key=True, nullable=False, autoincrement=True),
     )
Index('album2track_id_idx', album_track.c.id, unique=False)
Index('album2track_rid_idx', album_track.c.album_id, unique=False)
Index('album2track_tid_idx', album_track.c.track_id, unique=False)


artist = Table('artist', metadata,
    Column(u'id', Integer(), primary_key=True, nullable=False, autoincrement=True),
    Column(u'mb_id', String(length=64, convert_unicode=False, assert_unicode=None), default='', primary_key=False),
    Column(u'name', Unicode(length=256), default='', primary_key=False),
    Column(u'trackcount', Integer(), default=-1, primary_key=False),    
    )
Index('artist_mb_id_idx', artist.c.mb_id, unique=False)
Index('artist_name_idx', artist.c.name, unique=False)
Index('artist_pkey', artist.c.id, unique=True)
Index('artist_trackcount_idx', artist.c.trackcount, unique=False)    

artist_track =  Table('artist_track', metadata,
    Column(u'artist_id', Integer(), ForeignKey('artist.id'), nullable=False),
    Column(u'track_id', Integer(), ForeignKey('track.id'),  nullable=False),
    Column(u'id', Integer(), primary_key=True, nullable=False, autoincrement=True),
    )
Index('artist2track_aid_idx', artist_track.c.artist_id, unique=False)
Index('artist2track_id_idx', artist_track.c.id, unique=False)
Index('artist2track_tid_idx', artist_track.c.track_id, unique=False)

track =  Table('track', metadata,
    Column(u'id', Integer(), primary_key=True, nullable=False, autoincrement=True),
    Column(u'mb_id', String(length=64, convert_unicode=False, assert_unicode=None), default='', primary_key=False),
    Column(u'path', Unicode(length=512), default=u'', primary_key=False),
    Column(u'title', Unicode(length=256), default=u'', primary_key=False),
    Column(u'artist', Unicode(length=256),default=u'',  primary_key=False),
    Column(u'album', Unicode(length=256), default=u'', primary_key=False),
    Column(u'tracknum', SmallInteger(), default = -1, primary_key=False),
    Column(u'secs', Float(precision=53, asdecimal=False), default=-1 ,primary_key=False),
    Column(u'zsecs', Float(precision=53, asdecimal=False), default=-1,primary_key=False),
    Column(u'md5', String(length=64, convert_unicode=False, assert_unicode=None), default='', primary_key=False),
    Column(u'compilation', Boolean(), default = False, primary_key=False),
    Column(u'otitle', Unicode(length=256), default=u'', primary_key=False),
    Column(u'oartist', Unicode(length=256), default=u'',primary_key=False),
    Column(u'oalbum', Unicode(length=256), default=u'', primary_key=False),
    Column(u'source', Unicode(length=64), default=u'', primary_key=False),
    Column(u'bytes', Integer(), primary_key=False, default=-1),
    Column(u'otracknum', SmallInteger(), default=-1, primary_key=False),
    Column(u'ofilename', Unicode(length=256), default=u'', primary_key=False),
    )
Index('track_pkey', track.c.id, unique=True)
Index('track_album_idx', track.c.album, unique=False)
Index('track_artist_idx', track.c.artist, unique=False)
Index('track_mb_id_idx', track.c.mb_id, unique=False)
Index('track_title_idx', track.c.title, unique=False)

track_annotation =  Table('track_annotation', metadata,
    Column(u'id', Integer(), primary_key=True, nullable=False, autoincrement=True),
    Column(u'track_id', Integer(), ForeignKey('track.id'),  nullable=False),
    Column(u'type', Unicode(length=256), default=u'', primary_key=False),
    Column(u'annotation', Unicode(length=256),default=u'',  primary_key=False),
    Column(u'value', Unicode(length=512), default=u'', primary_key=False),
    )
Index('track_annotation_pkey', track_annotation.c.id, unique=True)
Index('track_annotation_track_idx', track_annotation.c.track_id, unique=False)


album_collection =  Table('album_collection', metadata,
    Column(u'id', Integer(), primary_key=True, nullable=False, autoincrement=True),
    Column(u'album_id', Integer(), ForeignKey('album.id')),
    Column(u'collection_id', Integer(), ForeignKey('collection.id')),
    )
#Index('album2collection_id_idx', album_collection.c.id, unique=True)

artist_collection =  Table('artist_collection', metadata,
    Column(u'id', Integer(), primary_key=True, nullable=False, autoincrement=True),
    Column(u'artist_id', Integer(), ForeignKey('artist.id')),
    Column(u'collection_id', Integer(), ForeignKey('collection.id')),
    )
#Index('artist2collection_id_idx', artist_collection.c.id, unique=True)

collection_track =  Table('collection_track', metadata,
    Column(u'id', Integer(), primary_key=True, nullable=False, autoincrement=True),
    Column(u'collection_id', Integer(), ForeignKey('collection.id')),
    Column(u'track_id', Integer(), ForeignKey('track.id')),
    )
#Index('collection2track_id_idx', collection_track.c.id, unique=True)

collection = Table('collection', metadata,
    Column(u'id', Integer(), primary_key=True, nullable=False, autoincrement=True),
    Column(u'source', Unicode(length=256)),
    Column(u'description', Unicode(length=256)),
    )
#Index('collection_pkey', collection.c.id, unique=True)

#end autogenerated code





def execute_raw_sql(sql, transactional = False) : #todo: transactional unused
    '''executes raw sql query and returns result. Can get all results as tuples using result.fetchall()'''
    Session = sessionmaker()
    raw_session = Session(bind = engine) #,transactional=transactional)  #part of current transaction...
    result = raw_session.execute(sql)
    #can then do result.fetchall()
    return result
    
def commit() :
    """commit transaction (used when transactional=True)
    Is smart enough to do the right thing with Turbogears versus our own auto-commit auto-flush session"""
    if not AUTOCOMMIT:
        #session.commit()
        session.flush()
    else :
        session.flush()

def flush() :
    """flush transaction"""
    session.flush()

def add(object) :
    '''add object to session'''
    session.add(object)

def query(*entities, **kwargs):
    '''Share new SQL Alchemy 0.6+ Session.query()'''
    return session.query(*entities, **kwargs)



   

def _get_filedir(tid) :
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

def _get_shortfile(tid, featurestub = '') :
    fn = '%s/%s' % (_get_filedir(tid), 'T%s.mp3' % tid)
    if featurestub <> '' :
        fn = '%s.%s' % (fn, featurestub)
    return fn

class Track(object) :
    def __str__(self) :
        if not self.id :
            return '<Empty Track>'
        st= '<Track %i %s by %s from %s>' % (self.id,self.title,self.artist,self.album)
        return st.encode('utf-8')
    def _get_fn_audio(self) :
        return os.path.join(config.DEF_GORDON_DIR,'audio','main', self.path)

    fn_audio = property(fget=_get_fn_audio,doc="""returns absolute path to audio file.  Does *not* verify that the file is actually present!""")

    def _get_fn_audio_extension(self) :
        root,ext = os.path.splitext(self.path) #@UnusedVariable
        return ext[1:]

    fn_audio_extension = property(fget=_get_fn_audio_extension,doc="""returns file extension of the audio file.  Does *not* verify that the file is actually present!""")

    def _get_fn_feature(self,gordonDir='') :
        return os.path.join(config.DEF_GORDON_DIR,'data','features',_get_shortfile(self.id,'h5'))
    
    fn_feature= property(fget=_get_fn_feature,doc="""returns absolute path to feature file.  Does *not* verify that feature file is actually present!""")

    def audio(self,stripzeros='none',mono=False) :
        """Returns audio for file
        Param stripzeros can be 'leading','trailing','both','none'
        Param mono returns mono if True, otherwise native signal
        Returns triple [x,fs,svals]         
          x is signal
          fs is sampling rate
          svals is a tuple containing [zeros stripped from front, zeros stripped from end] of file
        see gordon.io.audio.AudioFile for more details."""
        
        audioFile = AudioFile(self.fn_audio,stripzeros=stripzeros,mono=mono)
        x, fs, sval = audioFile.read()
        return x, fs, sval

    def _delete_related_files(self,gordonDir='')  :
        """Deletes files related to this Track. Triggered by mapper. Do not call"""
        #will be triggered by mapper when a track is deleted
        if gordonDir=='' :
            gordonDir = config.DEF_GORDON_DIR

        tid = self.id

        #we tried to do this using cascading deletes but it didn't work. 
        #if we are the last track for an album, delete that album
        for a in self.albums :
            # "I am connected to album",a
            if a.trackcount :
                a.trackcount-=1

        for a in self.artists :
            #log.debug("I am connected to artist", a)                            # debug
            if a.trackcount :
                a.trackcount-=1
                
        #jorgeorpinel: what is S supposed to be ? ill import from gordon_db :
        from gordon_db import get_tidfilename as get_tidfilename, get_tiddirectory, make_subdirs_and_move
        #move the corresponding MP3 and features to GORDON_DIR/audio/offline
#        srcMp3Path = os.path.join(gordonDir, 'audio', 'main', S.get_tidfilename(tid))
#        dstMp3Path = os.path.join(gordonDir, 'audio', 'offline', S.get_tidfilename(tid))
        srcMp3Path = os.path.join(gordonDir, 'audio', 'main', get_tidfilename(tid))
        dstMp3Path = os.path.join(gordonDir, 'audio', 'offline', get_tidfilename(tid))
        if os.path.exists(srcMp3Path) :
#            S.make_subdirs_and_move(srcMp3Path, dstMp3Path)
            make_subdirs_and_move(srcMp3Path, dstMp3Path)
            log.debug('Moved', srcMp3Path, 'to', dstMp3Path)                    # debug
            
        #move corresponding features to GORDON_DIR/data/features_offline
#        srcFeatPath = os.path.join(gordonDir, 'data', 'features', S.get_tiddirectory(tid))
#        dstFeatPath = os.path.join(gordonDir, 'data', 'features_offline', S.get_tiddirectory(tid))
        srcFeatPath = os.path.join(gordonDir, 'data', 'features', get_tiddirectory(tid))
        dstFeatPath = os.path.join(gordonDir, 'data', 'features_offline', get_tiddirectory(tid))
        featFiles =  glob.glob('%s/T%i.*' % (srcFeatPath,tid))
        for srcF in featFiles :
            (pth,fl) = os.path.split(srcF) #@UnusedVariable
            dstF = os.path.join(dstFeatPath,fl)
#            S.make_subdirs_and_move(srcF, dstF)
            make_subdirs_and_move(srcF, dstF)
            log.debug('Moved', srcF, 'to', dstF)                                # debug

#jorgeorpinel: for psycopg (used by SQL Alchemy) to know how to adapt (used in SQL queries) the numpy.float64 type
#              ...here since this is first used with track data (when running audio_intake.py)
#              found @ http://initd.org/psycopg/docs/advanced.html#adapting-new-python-types-to-sql-syntax
from psycopg2.extensions import register_adapter, AsIs
import numpy
def addapt_numpy_float64(numpy_float64):
    return AsIs(numpy_float64)
register_adapter(numpy.float64, addapt_numpy_float64)


class Artist(object) :
    def __str__(self) :
        if not self.id :
            return '<Empty Artist>'
        if not self.trackcount :
            tc=-1
        else :
            tc = self.trackcount
        st= '<Artist %i %s Trackcount=%i>' % (self.id,self.name,tc)
        return st.encode('utf-8')
    
    def __repr__(self): return self.__str__()

    def update_trackcount(self) :
        tc = session.query(ArtistTrack).filter(ArtistTrack.artist_id==self.id).count()
        if self.trackcount <> tc :
            self.trackcount=tc


class Album(object) :
    def __str__(self) :
        if not self.id :
            return '<Empty Album>'
        if not self.trackcount :
            tc=-1
        else :
            tc = self.trackcount
        if len(self.artists)>1 :
            artiststr= '%s and others' % self.artists[0].name
        elif len(self.artists)==1 :
            artiststr='%s' % self.artists[0].name
        else :
            artiststr='Unknown Artist'
        st ='<Album %s %s (by %s) Trackcount=%i MusicbrainzId=%s>' % (str(self.id).ljust(5),self.name.ljust(20),artiststr.ljust(20),tc,self.mb_id)
        return st.encode('utf-8')

    def __repr__(self): return self.__str__()

    def _get_fn_albumcover(self) :
        return os.path.join(config.DEF_GORDON_DIR,'data','covers',_get_filedir(self.id),'A%i_cover.jpg' % self.id)
    fn_albumcover= property(fget=_get_fn_albumcover,doc="""returns absolute path to album cover.  Does *not* verify that album cover is actually present!""")

    def _get_asin_url(self) :
        if self.asin<>None and len(self.asin.strip())>5 :
            urltxt = 'http://ec1.images-amazon.com/images/P/%s.jpg' % self.asin.strip()
        else :
            urltxt = '/static/images/emptyalbum.jpg'
        return urltxt
    asin_url= property(fget=_get_asin_url,doc="""returns Amazon URL for album cover for asin stored in self.asin.""")

    def update_trackcount(self) :
        tc = session.query(AlbumTrack).filter(AlbumTrack.album_id==self.id).count()
        if self.trackcount <> tc :
            log.debug("Updating track count to", tc)                            # debug
            self.trackcount=tc


class AlbumTrack(object) : pass


class ArtistTrack(object) : pass


class AlbumArtist(object) : pass


class AlbumStatus(object) :
    def __str__(self) :
        st='<AlbumStatus id=%i album_id=%i status=%s>' % (self.id, self.album_id,self.status)
        return st

    def __repr__(self): return self.__str__()


class Mbartist_resolve(object) : pass


class Mbalbum_recommend(object) :
    def __str__(self) :
        if self.album and len(self.album.artists)>0 :
            artist=self.album.artists[0].name
        else :
            artist=''
        if not self.album :
            album_name=''
        else :
            album_name = self.album.name
        #fixme album_id not always bound #st = '<MBAlbum_recommend %4.4f [%i Name=%s Artist=%s] [%s MBAlbumName=%s MBAlbumArtist=%s] > ' % (self.conf,self.album_id,album_name, artist,self.mb_id, self.mb_album,self.mb_artist)
        st = '<MBAlbum_recommend conf=%4.4f conf_time=%4.4f conf_album=%4.4f conf_artist=%4.4f conf_track=%4.4f [Name=%s Artist=%s] [%s MBAlbumName=%s MBAlbumArtist=%s] > ' % (self.conf,self.conf_time,self.conf_album, self.conf_artist,self.conf_track,album_name, artist,self.mb_id, self.mb_album,self.mb_artist)
        return st.encode('utf-8')

    def __repr__(self): return self.__str__()


class Collection(object):
#    def __init__(self, source):
#        self.source = source
    
    def __repr__(self) :
        if not self.id: return '<Empty Collection>'
        else: return '<Collection %s "%s">' % (self.source, self.description) # ------------------ return
    

class Annotation(object):
    def __repr__(self) :
        if not self.id: return '<Empty Annotation>'
        value = self.value
        if len(value) > 32: long=True
        return '<Annotation %s.%s: %s%s>' % (self.type, self.annotation, value[:16], '...' if long else '') #return
    

mapper(AlbumTrack,album_track)

mapper(ArtistTrack,artist_track)

mapper(AlbumArtist,album_artist)


#we cascade deletes from Album to AlbumSim and Artist to ArtistSim
#but we currently do not cascade deletes from Artist to Track nor Artist to Album...
#we do cascade fromm album to track but

#IMPORTANT
#we *do* allow tracks to exist without an associated album or artist. Is that a good idea? I dunno...

#Here we set up a trigger to call Track.delete_related_files() 
class DeleteFileMapperExtension(MapperExtension) :
    def after_delete(self,mapper,connection,instance) :
        instance._delete_related_files()

mapper(Track,track, extension=DeleteFileMapperExtension(),
       properties={
                   'artists':relation(Artist,secondary=artist_track,lazy=True), 
                   'albums':relation(Album,secondary=album_track,lazy=True), #this causes all sorts of headaches, cascade='delete-orphan'), 
                   }
       )

mapper(Album,album,
       properties={'artists':relation(Artist,secondary=album_artist),   
                   'tracks':relation(Track,secondary=album_track,order_by=Track.tracknum, cascade='all,delete'), #removed delete-orphan
                   'recommend':relation(Mbalbum_recommend, backref='album',cascade='all,delete,delete-orphan'),
                   'status':relation(AlbumStatus,backref='album',cascade='all,delete,delete-orphan')
                   }
       )

mapper(Artist,artist,
       properties={'albums':relation(Album,secondary=album_artist,order_by=Album.name),   
                   'tracks':relation(Track,secondary=artist_track, order_by=Track.title, cascade='all,delete'),  #removed delete-orphan
                   }
       )

mapper(AlbumStatus,album_status)

mapper(Mbartist_resolve,mbartist_resolve)

mapper(Mbalbum_recommend,mbalbum_recommend)

mapper(Collection, collection,
    properties={
       'albums':  relation(Album,  secondary=album_collection,  order_by=Album.name, backref='collections'),
       'artists': relation(Artist, secondary=artist_collection, order_by=Artist.name, backref='collections'),
       'tracks':  relation(Track,  secondary=collection_track,  order_by=Track.tracknum, backref='collections'),
    }
)

mapper(Annotation, track_annotation,
    properties={
       'track': relation(Track, backref=backref('annotations', order_by='track_annotation.type')),
    }
)

#jorgeorpinel: this didn't work (again)... no track_annotationn table is created with metadata.create_all(engine)...
# before, used to create Collection, when calling metadata.create_all(engine), no table is found at album_collection (et al) foreign key (ie collection.id) declaration
##jorgeorpinel: trying out the declarative way to create table, class and mapper (@ http://www.sqlalchemy.org/docs/05/ormtutorial.html#creating-table-class-and-mapper-all-at-once-declaratively)
##from sqlalchemy import ForeignKey # don't need this...
##from sqlalchemy.orm import relation, backref # got them already
#from sqlalchemy.ext.declarative import declarative_base
#Base = declarative_base()
#
#class Annotation (Base):
#    __tablename__ = 'track_annotation'
#    
#    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
#    track_id = Column(Integer, ForeignKey('track.id'), nullable=False)
#    type = Column(Unicode(length=256), default=u'', nullable=False)
#    annotation = Column(Unicode(length=256),default=u'')
#    value = Column(Unicode(length=512), default=u'')
#
#    # these are the mapper relationships (and backref "collections" at Album, Artist, and Track)
##    artists = relation("Artist", secondary="artist_collection", order_by="Artist.name",  backref="collections")
#    tracks =  relation(Track, order_by=Track.tracknum, backref=backref('annotations', order_by=type))
#
#    def __repr__(self) :
#        if not self.id: return '<Empty Annotation>'
#        else: return '<Annotation (%s) %s: %s>' % (self.type, self.annotation, self.value) #return
    
