from turbogears.database import metadata, mapper
from sqlalchemy import Table, Column, ForeignKey, String, Unicode, Integer, DateTime,MetaData,PassiveDefault,text,Index,Text,Float,ForeignKeyConstraint,SmallInteger,Boolean
from sqlalchemy.orm import relation,backref,column_property,deferred
#from sqlalchemy.databases.postgres import PGArray
#from sqlalchemy.orm.collections import InstrumentedList
from turbogears import identity,config,update_config,flash
from turbogears import validators as v

from turbogears.widgets import DataGrid,PaginateDataGrid,WidgetsList,TextField,TableForm,ListForm,CheckBox,HiddenField,SingleSelectField,RadioButtonList,FieldSet,Label,RepeatingFieldSet,CSSSource
from tgfastdata.datawidgets import FastDataGrid
try:
    from elementtree import ElementTree as ET
except:
    import xml.etree.ElementTree as ET
from xml.etree.ElementTree import tostring

import cherrypy
import socket
import string
import random
import os
import shutil
import tempfile
import turbogears
import numpy as N
import time
import operator
import mimetypes
import collections

import tables
from cStringIO import StringIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


#artist datagrid ---------------------------------------
def get_artist_url(row) :
    link = ET.Element('a',href='/artist/%s' % row.id)
    link.text = row.name
    return link

def get_artist_url_for_id(row) :
    link = ET.Element('a',href='/artist/%s' % row.id)
    link.text = str(row.id)
    return link

def get_artist_mb_id_url(row) :
    #this will work with a DataGrid row or with mb_id directly

    if not row :
        return 'None'    
    if type(row)==str or type(row)==unicode :
        mb_id=row
    else :
        if row.mb_id :
            mb_id=row.mb_id
        else :
            return 'None'       
    if mb_id and len(mb_id)>10 :
        link = ET.Element('a',href='http://www.musicbrainz.org/artist/%s.html' % mb_id,target='_blank')
        #link.text = mb_id
        link.text = "%s ..." % mb_id[0:12]
        return link
    else :
        return 'None'
artist_datagrid = PaginateDataGrid(
    fields=[
    PaginateDataGrid.Column('id',  get_artist_url_for_id,'Artist ID', options=dict(sortable=True)),
    PaginateDataGrid.Column('name', get_artist_url,'Artist Name', options=dict(sortable=True)),
    PaginateDataGrid.Column('mb_id', get_artist_mb_id_url, 'MB ID', options=dict(sortable=True)),#reverse_order=True)),    
    ])

#album datagrid --------------------------------------
def get_album_url(row) :
    link = ET.Element('a',href='/album/%s' % row.id)
    link.text = row.name
    return link

def get_album_url_for_id(row) :
    link = ET.Element('a',href='/album/%s' % row.id)
    link.text = str(row.id)
    return link

def get_albumcover_thumb(row,clickable=True) :
    return get_albumcover(row,clickable=clickable,sz=40)

def get_albumcover(row,clickable=False,sz=120):
    url=get_albumcover_urltxt(row)
    if len(url)==0 :
        return ''

    if clickable :
        link = ET.Element('a',href='/album/%s' % row.id)
        link_img = ET.SubElement(link,'img', src=url)
        link_img.set('width','%i' % sz)
        link_img.set('border','0')
    else :
        link = ET.Element('img', src=url)
        link.set('width','%i' % sz)

    return link

    

def get_albumcover_urltxt(row) :
    import gordon.db
    #this will work with a DataGrid row or with mb_id directly
    if type(row)==str :
        asin=row
    elif type(row)==None :
        return '/static/images/emptyalbum.jpg'
    else :
        asin=row.asin

        #here we might be able to recover url from local cache
        albumcover_path=gordon.db.get_full_albumcovername(row.id) 
        #print 'ALBUM',albumcover_path
        if os.path.exists(albumcover_path) :
            return '/cover/A%i.jpg' % row.id

    if asin<>None and len(asin.strip())>5 :
        urltxt = 'http://ec1.images-amazon.com/images/P/%s.jpg' % asin.strip()
    else :
        urltxt = '/static/images/emptyalbum.jpg'
    return urltxt

def get_album_artiststring(album) :
    #gets a comma-delimited list of artists for an album
    artistnames = set()
    for artist in album.artists :
        artistnames.add(artist.name)
    artistnames = list(artistnames)
    artistnames.sort()
    artistnames= string.join(artistnames,',')
    return artistnames

def get_album_mb_id_url(row) :
    #this will work with a DataGrid row or with mb_id directly
    if not row :
        return 'None'    
    if type(row)==str or type(row)==unicode :
        mb_id=row
    else :
        if row.mb_id :
            mb_id=row.mb_id
        else :
            return 'None'
        
    if mb_id and len(mb_id)>10 :
        link = ET.Element('a',href='http://www.musicbrainz.org/release/%s.html' % mb_id, target='_blank')
        link.text = "%s ..." % mb_id[0:12]
        return link
    else :
        return 'None'

def get_album_playlist(row) :
    link = ET.Element('a',href='/playlist?params=rid:%i!randomize:0' % row.id, type="application/xspf+xml")
    link.text=''
    return link

#why is this not sortable?
album_datagrid = PaginateDataGrid(
    fields=[
#    PaginateDataGrid.Column('playlist', get_album_playlist, 'Play'),
    PaginateDataGrid.Column('cover', get_albumcover_thumb, ''),
    PaginateDataGrid.Column('id', get_album_url_for_id, 'Album ID',options=dict(sortable=True)),
    PaginateDataGrid.Column('name', get_album_url,'Album Name',options=dict(sortable=True)),
    PaginateDataGrid.Column('mb_id', get_album_mb_id_url, 'MB ID',options=dict(sortable=True)),
    PaginateDataGrid.Column('trackcount', 'trackcount', 'Count',options=dict(sortable=True)),
    PaginateDataGrid.Column('asin', 'asin', 'ASIN',options=dict(sortable=True)),
    ],
 )


#collection datagrid --------------------------------------
def get_collection_url(row) :
    link = ET.Element('a',href='/collection/%s' % row.id)
    link.text = row.name
    return link

def get_collection_url_for_id(row) :
    link = ET.Element('a',href='/collection/%s' % row.id)
    link.text = str(row.id)
    return link

def get_collection_trackcount(row) :
    return row.trackcount

collection_datagrid = PaginateDataGrid(
    fields=[
    PaginateDataGrid.Column('id', get_collection_url_for_id, 'Collection ID',options=dict(sortable=True)),
    PaginateDataGrid.Column('name', get_collection_url,'Collection Name',options=dict(sortable=True)),
    PaginateDataGrid.Column('trackcount', get_collection_trackcount, 'Count',options=dict(sortable=True)),
    PaginateDataGrid.Column('description', 'description', 'Description'),
    ],
 )


#track datagrid -------------------------------------
#        id          int4 PRIMARY KEY,  -- Track id
#        mb_         varchar(64),       -- Musicbrainz track id
#        path        varchar(512),      -- Path to audio file
#        title       varchar(256),      -- Title
#        artist      varchar(256),      -- Artist
#        album       varchar(256),      -- Album
#        tracknum    int2,              -- Track number
#        secs        float,             -- Seconds in track
#        zsecs       float,             -- Zero-stripped second
#        md5         varchar(64),       -- MD5 value of audio file
#        compilation bool,              -- True if part of a compilation
#        otitle      varchar(256),      -- Original Title
#        oartist     varchar(256),      -- Original Artist
#        oalbum      varchar(256),      -- Original Album
#        source      varchar(64),       -- Source of music
#        bytes       int4  DEFAULT 0    -- Number of bytes in file

def get_track_url(row) :
    link = ET.Element('a',href='/track/%s' % row.id)
    link.text = row.name
    return link

def get_track_url_for_id(row) :
    link = ET.Element('a',href='/track/%s' % row.id)
    link.text = str(row.id)
    return link


def get_track_url_for_tracknum(row) :
    link = ET.Element('a',href='/track/%s' % row.id)
    link.text = str(row.tracknum)
    return link


def get_track_url_for_title(row) :
    link = ET.Element('a',href='/track/%s' % row.id)
    link.text = row.title
    return link

def get_track_artist_url(row) :
    #this probably doesn't need to be a query
    if len(row.artists)>0:
        link = ET.Element('a',href='/artist/%s' % row.artists[0].id)
        link.text = row.artist
    else :
        link = row.artist
    return link

def get_track_time(row) :
    if row.secs==-1 :
        return '??:??'
    else :
        mins = int(row.secs/60.0)
        remsecs = int(row.secs - mins*60)
        return '%s:%s' % (str(mins).zfill(1),str(remsecs).zfill(2))


def get_mbtrack_time(row) :
    mins = int(row.mb_secs/60.0)
    remsecs = int(row.mb_secs - mins*60)
    return '%s:%s' % (str(mins).zfill(1),str(remsecs).zfill(2))


def get_track_mb_id_url(row) :
    #this will work with a DataGrid row or with mb_id directly
        #this will work with a DataGrid row or with mb_id directly
    if not row :
        return 'None'    
    if type(row)==str :
        mb_id=row
    else :
        if row.mb_id :
            mb_id=row.mb_id
        else :
            return 'None'
    if mb_id and len(mb_id)>10 :
        link = ET.Element('a',href='http://www.musicbrainz.org/track/%s.html' % row.mb_id,target='_blank')
        link.text = '%s...' % mb_id[0:8]
        return link
    else :
        return 'None'


def get_yahoo_player_audio_url(row,arrow=True,albumcover=False) :
    #gets url to track with album image if album image exists
    #if arrow is true, arrow icon is shown on page
    #if album cover is true, album cover is shown on page
    try :
        ext = get_track_audio_extension(row)
        if not arrow :
            link = ET.Element('a',style='display:none', title="%s - %s (%s)" % (row.artist,row.title,row.album),href='/audio/T%s.%s' % (str(row.id), ext))
        else :
            link = ET.Element('a',title="%s - %s (%s)" % (row.artist,row.title,row.album),href='/audio/T%s.%s' % (str(row.id), ext))
        #don't show text for this
        link.text=''
        #now add the album cover
        if len(row.albums)>0 :#atand row.albums.count()>0 :
            albumcover_url = get_albumcover_urltxt(row.albums[0])
            if len(albumcover_url)<>'' :
                link_img = ET.SubElement(link,'img',align='right',style='display:none', src=albumcover_url)
    except :
        link=''

    return link



track_datagrid = PaginateDataGrid(
    fields=[
    PaginateDataGrid.Column('audio',         get_yahoo_player_audio_url, 'Play',options=dict(sortable=False)),
    PaginateDataGrid.Column('id',            get_track_url_for_id,       'Track ID', options=dict(sortable=True)),
    PaginateDataGrid.Column('tracknum',      get_track_url_for_tracknum, 'Track',options=dict(sortable=True)),
    PaginateDataGrid.Column('title',         get_track_url_for_title,    'Title',options=dict(sortable=True)),
    PaginateDataGrid.Column('artist',        get_track_artist_url,       'Artist',options=dict(sortable=True)),
    PaginateDataGrid.Column('album',         'album',                    'Album',options=dict(sortable=True)),
    PaginateDataGrid.Column('time',          get_track_time,             'Time',options=dict(sortable=True)),
#    PaginateDataGrid.Column('compilation',   'compilation',              'Compilation',options=dict(sortable=True)),
    PaginateDataGrid.Column('source',        'source',                   'Source',options=dict(sortable=True)),
    PaginateDataGrid.Column('mb_id',         get_track_mb_id_url,        'MB ID',options=dict(sortable=True)),

    ])


track_datagrid_no_album = PaginateDataGrid(
    fields=[
    PaginateDataGrid.Column('audio',         get_yahoo_player_audio_url, 'Play',options=dict(sortable=False)),
    PaginateDataGrid.Column('id',            get_track_url_for_id,       'Track ID', options=dict(sortable=True)),
    PaginateDataGrid.Column('tracknum',      get_track_url_for_tracknum, 'Track',options=dict(sortable=True)),
    PaginateDataGrid.Column('title',         get_track_url_for_title,    'Title',options=dict(sortable=True)),
    PaginateDataGrid.Column('artist',        get_track_artist_url,       'Artist',options=dict(sortable=True)),
    PaginateDataGrid.Column('time',          get_track_time,             'Time',options=dict(sortable=True)),
#    PaginateDataGrid.Column('compilation',   'compilation',              'Compilation',options=dict(sortable=True)),
    PaginateDataGrid.Column('source',        'source',                   'Source',options=dict(sortable=True)),
    PaginateDataGrid.Column('mb_id',          get_track_mb_id_url,       'MB ID',options=dict(sortable=True)),

    ])

#identical to above but with delete checkbox
def get_trackrec_checkbox(row) :
    link = ET.Element('input',type='checkbox',name='%s' % str(row.id))
    return link

track_edit_datagrid = PaginateDataGrid(
    fields=[
    PaginateDataGrid.Column('selector',     get_trackrec_checkbox, 'Delete'),
    PaginateDataGrid.Column('id',            get_track_url_for_id,       'Track ID', options=dict(sortable=True)),
    PaginateDataGrid.Column('tracknum',      'tracknum',                 'Track',options=dict(sortable=True)),
    PaginateDataGrid.Column('title',         'title',                    'Title',options=dict(sortable=True)),
    PaginateDataGrid.Column('artist',        get_track_artist_url,       'Artist',options=dict(sortable=True)),
    PaginateDataGrid.Column('album',         'album',                    'Album',options=dict(sortable=True)),
    PaginateDataGrid.Column('time',          get_track_time,             'Time',options=dict(sortable=True)),
#    PaginateDataGrid.Column('compilation',   'compilation',              'Compilation',options=dict(sortable=True)),
    PaginateDataGrid.Column('source',        'source',                   'Source',options=dict(sortable=True)),
    PaginateDataGrid.Column('mb_id',          get_track_mb_id_url,               'MB ID',options=dict(sortable=True)),

    ])


def get_mbrec_album_url(row) :
    if type(row)==str :
        album_id=row
    else :
        album_id=row.album_id
    
    link = ET.Element('a',href='/resolve_viewalbum/%s' % album_id)
    link.text = row.album_id

    return link


def get_mbrec_checkbox(row) :
    link = ET.Element('input',type='checkbox',name='%sSEP%s' % (str(row.album_id),str(row.mb_id).replace('-','H')))
    return link





mbrecommend_datagrid = PaginateDataGrid(
    fields=[
    PaginateDataGrid.Column('albumID',     get_mbrec_album_url,     'Album',options=dict(sortable=True)),
    PaginateDataGrid.Column('mb_album',     'mb_album',     'MBAlbum',options=dict(sortable=True)),
    PaginateDataGrid.Column('gordon_album',     'gordon_album',     'GordonAlbum',options=dict(sortable=True)),
    PaginateDataGrid.Column('mb_artist',     'mb_artist',     'MBArtist',options=dict(sortable=True)),
    PaginateDataGrid.Column('gordon_artist',     'gordon_artist',     'GordonArtist',options=dict(sortable=True)),
    PaginateDataGrid.Column('conf',         lambda row:'%2.3f' % row.conf,         'Overall Conf',options=dict(reverse_order=True,sortable=True)),
    PaginateDataGrid.Column('conf_artist',  lambda row:'%2.3f' % row.conf_artist,  'Artist Conf',options=dict(reverse_order=True,sortable=True)),
    PaginateDataGrid.Column('conf_album',   lambda row:'%2.3f' % row.conf_album,   'Album Conf',options=dict(reverse_order=True,sortable=True)),
    PaginateDataGrid.Column('conf_track',   lambda row:'%2.3f' % row.conf_track,   'Track Conf',options=dict(reverse_order=True,sortable=True)),
    PaginateDataGrid.Column('conf_time',    lambda row:'%2.3f' % row.conf_time,    'Time Conf',options=dict(reverse_order=True,sortable=True)),
    PaginateDataGrid.Column('selector',     get_mbrec_checkbox, 'Accept'),
    ])



def get_track_edit_url(row) :
    if type(row)==str :
        track_id=row
    else :
        track_id=row.id
    
    link = ET.Element('a',href='/track/%s/edit' % str(track_id))
    link.text = str(track_id)

    return link

mbrecommend_track_datagrid = PaginateDataGrid(
    fields=[
    PaginateDataGrid.Column('audio',         get_yahoo_player_audio_url, 'PlayIt',options=dict(sortable=False)),
    PaginateDataGrid.Column('id',            get_track_edit_url,         'Gordon ID'),
    PaginateDataGrid.Column('tracknum',      'tracknum',                 'Gordon Track'),
    PaginateDataGrid.Column('mb_tracknum',      'mb_tracknum',           'MB Track'),
    PaginateDataGrid.Column('title',         'title',                    'Gordon Title'),
    PaginateDataGrid.Column('mb_track',         'mb_track',              'MB Title'),
    PaginateDataGrid.Column('artist',        get_track_artist_url,       'Gordon Artist'),
    PaginateDataGrid.Column('mb_artist',        'mb_artist',             'MB Artist'),
    PaginateDataGrid.Column('time',          get_track_time,             'Gordon Time'),
    PaginateDataGrid.Column('mb_time',          get_mbtrack_time,        'MB Time'),
    ])








def getfullhost() :
    #this must be integrated into cherrypy somewhere. . . . 
    host=cherrypy.config.configs.get('global').get('server.socket_host')
    if host=='' :
        host=socket.gethostname()
    port=cherrypy.config.configs.get('global').get('server.socket_port')
    if port>0 and port<>80 :
        host='%s:%s' % (host,port)
    return host

def slashify_xml(str) :
    #ampersand is used by xml.  Surely there is an xml string massager already
    return str.replace('&','&amp;')
    return str.replace('<','&lt;')
    return str.replace('>','&gt;')






                  
def download(tracks, album='', randomize=0, host=-1)  :
    import widgets
    import cherrypy.lib.cptools
    import tarfile
    import zipfile
    import glob
    import gordon.db

    (topdir,ignore)=os.path.split(widgets.__file__)


    if os.path.exists('/Tmp') :
        tmpdir='/Tmp'
    else :
        tmpdir='/tmp'
    tempdir=tempfile.mkdtemp(dir=tmpdir)

    
    msg=''
    ctr=1
    for t in tracks :
        src = gordon.db.get_full_audiofilename(t.id)

        artist = t.artist
        album = t.album
        title = t.title
        tracknum = t.tracknum

        if not album:
            album='Unknown'
        if not title:
            title='Unknown'
        if tracknum<=0:
            tracknum=ctr

        ext = get_track_audio_extension(t)
        tracknum=str(tracknum).zfill(2)
        fname='%s - %s - %s - %s.%s' % (artist,album,tracknum,title,ext)
        fname=itunes_slashify(fname)  #get rid of dangerous characters
        tgt=os.path.join(tempdir,fname)
        msg='%s\n copy %s to %s' % (msg,src,tgt)
        shutil.copy(src,tgt)
        ctr+=1
    
    cwd=os.getcwd()
    os.chdir(tempdir)
    os.chdir('..')
    tardir=os.getcwd()
    bn = os.path.basename(tempdir)






    #FOR MAKING TARBALLS
    comptyp='zip'
    if len(tracks)>1:
        if comptyp=='zip' :
            outfn='%s/gordon_download_%s.zip' % (tardir,bn)    
            zip = zipfile.ZipFile(outfn,'w')
            for f in glob.glob('%s/*' % bn) :
                zip.write(f,os.path.basename(f),zipfile.ZIP_STORED)
            zip.close()
            typ='application/x-zip'
        elif comptyp=='tar' :
            outfn='%s/gordon_download_%s.tar' % (tardir,bn)    
            tar = tarfile.open(outfn,'w')
            for f in glob.glob('%s/*' % bn) :
                tar.add(f)
            tar.close()
            typ='application/x-tar'
            print 'Tar is left at',tar
            print 'not deleteing. See widgets.py'
        else :
            raise ValueError('comptype is wrong which is silly because it is hardcoded above. Duh')
        shutil.rmtree(bn)        
    else :
        #here we leave the directory because it contains our only file
        typ,ignored = mimetypes.guess_type(tgt)
        outfn=tgt

    os.chdir(cwd)
    #return cherrypy.lib.cptools.serveFile(path=outfn,contentType=typ,disposition='attachment',name=os.path.basename(outfn))
    return deletable_file(outfn,typ,os.path.basename(outfn))
    
def deletable_file(fname,typ,name) :
    """Serves and then deletes a zip file"""
    cherrypy.response.headers['Content-Type'] = typ
    cherrypy.response.headers["Content-Disposition"] = 'attachment; filename="%s"' % (name)
    zipfile=open(fname,'r+b')
    for line in zipfile:
        yield line
    zipfile.close()
    os.unlink(fname)
    

def playlist(tracks, album='', randomize=0, host=-1)  :
    if host==-1:
        host=getfullhost()
    str= '<?xml version="1.0" encoding="UTF-8" ?>\n'
    str+='<playlist version="1" xmlns="http://xspf.org/ns/0/">\n'

    artist = set()
    for track in tracks :
        artist.add(track.artist)

    albumcover_urltxt=''
    if album<>'' :
        str+='<title>%s</title>\n' % album.name
        if len(artist)==1 :
            str+='<creator>%s</creator>\n' % list(artist)[0]
        else :
            str+='<creator>Various artists</creator>\n'


        albumcover_urltxt = get_albumcover_urltxt(album)#.asin)
            
    str+='   <trackList>\n'

    if randomize :
        random.shuffle(tracks)
        
        
    ctr=0
    for track in tracks :
        #if we are not given an album (this is a playlist) grab the cover from the first album this track is part of
        if album == '' :
            try :
                albumcover_urltxt=get_albumcover_urltxt(track.albums[0])
            except :
                albumcover_urltxt=''
        ext = get_track_audio_extension(track)
        str+='     <track>\n'
        str+='            <location>http://%s/audio/T%i.%s</location>\n' % (host,track.id,ext)
        str+='            <album>%s</album>\n' % slashify_xml(track.album)
        str+='            <title>%s</title>\n' % slashify_xml(track.title)
        str+='            <creator>%s</creator>\n' % slashify_xml(track.artist)
        str+='            <duration>%i</duration>\n' % (int(track.zsecs)*1000)
        if len(albumcover_urltxt)>0 :
            str+='            <image>%s</image>\n'  % albumcover_urltxt
        str+='     </track>\n'
        ctr+=1
        if ctr>=10 :
            break

    str+='   </trackList>\n'
    str+='</playlist>'    
    return str

        
#"rotate" a db row to be multiple records for displaying in datagrid
class rotrec :
    field=''
    value=''
    def __init__(self,f,v) :
        self.field=f
        self.value=v
        
def rotate_record(rec) :
    l=list()
    for col in rec.__dict__.keys() :
        if col[0]<>'_' :
            #one of my keys
            val = rec.__dict__[col]
            if type(val)<>unicode :
                val=unicode(str(val),'utf-8')
            l.append(rotrec(col,val))
    return l

def null_widget(rec) :
    return ''

record_view_widget = DataGrid(
    #    fields = [DataGrid.Column('Field','field'),DataGrid.Co('Value','value')]
    fields = [DataGrid.Column('Field','field'),DataGrid.Column('Value','value')]
  )

#-----------track------------------
def get_track_fields() :
    options = []
    options.append(('edit','Edit'))
    options.append(('delete','Delete'))
    fields=[
    HiddenField(name='referer'),
    HiddenField(name='id'),
    TextField(name='mb_id', label='MB Id', attrs={'size': 37, 'maxlength': 64}, validator=v.UnicodeString),
    TextField(name='path', label='Path', attrs={'size': 24, 'maxlength': 512}, validator=v.UnicodeString),
    TextField(name='title', label='Title', attrs={'size': 64, 'maxlength': 256}, validator=v.UnicodeString),
    TextField(name='artist', label='Artist', attrs={'size': 64, 'maxlength': 256}, validator=v.UnicodeString),
    TextField(name='album', label='Album', attrs={'size': 64, 'maxlength': 256}, validator=v.UnicodeString),
    TextField(name='tracknum', label='Tracknum', attrs={'size': 3, 'maxlength': 3}, validator = v.Int),
    TextField(name='secs', label='Secs', attrs={'size': 10, 'maxlength': 10}, validator = v.Number),
    TextField(name='zsecs', label='ZSecs', attrs={'size': 10, 'maxlength': 10}, validator = v.Number),
    TextField(name='md5', label='MD5', attrs={'size': 32, 'maxlength': 64}, validator=v.UnicodeString),
    TextField(name='source', label='Source', attrs={'size': 32, 'maxlength': 64}, validator=v.UnicodeString),
    TextField(name='bytes', label='Bytes', attrs={'size': 12, 'maxlength': 32}, validator = v.Int),
    CheckBox(name='compilation', label='Compilation', attrs={'size': 5, 'maxlength': 5}),
    SingleSelectField(name='operation',options=options),]
    return fields

track_edit_widget = TableForm(
    fields = get_track_fields(),
    action='/track_modify',
    method='post',
    submit_text='Do Selected Operation',
    )




#------------artist----------------------
def get_artist_fields() :
    options = []
    options.append(('edit','Edit'))
    options.append(('delete','Delete'))
    options.append(('merge','Merge all records for this artist with Merge Artist Id; Then Delete'))
    fields=[
    HiddenField(name='referer'),
    HiddenField(name='id'),
    TextField(name='name', label='Name', attrs={'size': 64, 'maxlength': 256}, validator=v.UnicodeString),
    TextField(name='mb_id', label='MB id', attrs={'size': 37, 'maxlength': 64}, validator=v.UnicodeString),
    TextField(name='mergeid', label='Merge Artist Id', attrs={'size': 12, 'maxlength': 12}),
    SingleSelectField(name='operation',options=options),]
    return fields

artist_edit_widget = TableForm(
    fields = get_artist_fields(),
    action='/artist_modify',
    method='post',
    submit_text='Do Selected Operation',
    )



#--------------album-------------------------
def get_album_fields() :
    options = []
    options.append(('edit','Edit'))
    options.append(('delete','Delete'))
    fields=[
    HiddenField(name='referer'),
    HiddenField(name='id'),
    TextField(name='name', label='Name', attrs={'size': 64, 'maxlength': 256}, validator=v.UnicodeString),
    TextField(name='mb_id', label='MB id', attrs={'size': 37, 'maxlength': 64}, validator=v.UnicodeString),
    TextField(name='asin', label='ASIN', attrs={'size': 20, 'maxlength': 64}, validator=v.UnicodeString),
    #TextField(name='trackcount', label='trackcount', attrs={'size': 4, 'maxlength': 10}, validator=v.UnicodeString),
    SingleSelectField(name='operation',options=options),]
    return fields

album_edit_widget = TableForm(
    fields = get_album_fields(),
    action='/album_modify',
    method='post',
    submit_text='Do Selected Operation',
    )


def get_album_short_artist(row) :
    if len(row.artists)==1 :
        return get_artist_url(row.artists[0])
    elif len(row.artists)==0 :
        return 'None'
    else :
        return 'Various Artists'
    


def get_artist_sim_url(row) :
    try :
        link = ET.Element('a',href='/artist/%s' % row.id)
        link.text = row.other.name
    except :
        link=''
    return link

artist_top_sim_datagrid = PaginateDataGrid(
    fields=[
        PaginateDataGrid.Column('name',          get_artist_sim_url,      'Most Similar Artists', options=dict(sortable=False)),
      #  PaginateDataGrid.Column('id',            get_artist_url_for_id,    'Artist ID', options=dict(sortable=False)),
        PaginateDataGrid.Column('value',         'value',                  'Sim Value', options=dict(sortable=False)),
        ])

artist_bottom_sim_datagrid = PaginateDataGrid(
    fields=[
        PaginateDataGrid.Column('name',          get_artist_sim_url,      'Least Similar Artists', options=dict(sortable=False)),
     #   PaginateDataGrid.Column('id',            get_artist_url_for_id,    'Artist ID', options=dict(sortable=False)),
        PaginateDataGrid.Column('value',         'value',                  'Sim Value', options=dict(sortable=False)),
        ])


def get_album_sim_url(row) :
    if row and row.other :
        link = ET.Element('a',href='/album/%s' % row.id)
        link.text = row.other.name
    else :
        link=''
    return link

album_top_sim_datagrid = PaginateDataGrid(
    fields=[
        PaginateDataGrid.Column('name',          get_album_sim_url,      'Most Similar Albums', options=dict(sortable=False)),
      #  PaginateDataGrid.Column('id',            get_album_url_for_id,    'Album ID', options=dict(sortable=False)),
        PaginateDataGrid.Column('value',         'value',                  'Sim Value', options=dict(sortable=False)),
        ])

album_bottom_sim_datagrid = PaginateDataGrid(
    fields=[
        PaginateDataGrid.Column('name',          get_album_sim_url,      'Least Similar Albums', options=dict(sortable=False)),
     #   PaginateDataGrid.Column('id',            get_album_url_for_id,    'Album ID', options=dict(sortable=False)),
        PaginateDataGrid.Column('value',         'value',                  'Sim Value', options=dict(sortable=False)),
        ])

def itunes_slashify(fname) :
    fname=fname.replace('/','_')
    fname=fname.replace(':','_')
    fname=fname.replace(':','_')
    fname=fname.replace('"','_')
    #fname=fname.replace('`','_')
    fname=fname.replace('*','_')
    fname=fname.replace('?','_')
    if len(fname)>1 and fname.endswith('.') :
        fname=fname[0:len(fname)-1] + '_'

    if len(fname)>1 and fname.startswith('.') :
        fname='_' + fname[1:]

    if len(fname)>1 and fname.endswith('-') :
        fname=fname[0:len(fname)-1] + '_'

    if len(fname)>1 and fname.startswith('-') :
        fname='_' + fname[1:]
    return fname


def get_track_audio_extension(track):
    root, ext = os.path.splitext(track.fn_audio)
    return ext[1:]


def generate_htk_annotation_datatables_for_track(track):
    datatables = dict()
    for x in track.annotations:
        try:
            datatables[x.name] = generate_htk_annotation_datatable(x)
        except:
            pass
    return datatables

def generate_htk_annotation_datatable(annotation):
    header = [('datetime', 'Time')]

    # Create one-to-one mapping from labels to integers.
    labels = []
    for line in annotation.value.split('\n'):
        if not line:
            continue
        fields = line.split()
        label = ' '.join(fields[2:])
        if not label in labels:
            labels.append(label)

    # Are the labels numbers that we should plot, or should we treat
    # them as strings?
    try:
        for label in labels:
            tmp = float(label)
        header.append(('number', annotation.name))
        header.append(('string', annotation.name))
        add_points_fun = _add_points_assuming_numeric_labels
    except ValueError:
        for label in labels:
            header.append(('number', label))
            header.append(('string', label))
        add_points_fun = _add_points_assuming_string_labels

    # Group times into repetitions of the same label.
    rows = collections.defaultdict(list)
    for line in annotation.value.split('\n'):
        if not line:
            continue
        fields = line.split()
        starttime, endtime = [float(x) for x in fields[:2]]
        label = ' '.join(fields[2:])
        labelnum = labels.index(label)
        add_points_fun(rows, starttime, endtime, label, labelnum)

    # Format labels as a javascript array.  See here for an example:
    # http://code.google.com/apis/visualization/documentation/gallery/annotatedtimeline.html#Example
    data_strs = ["var data = new google.visualization.DataTable();"]
    for type, name in header:
        data_strs.append("data.addColumn('%s', '%s');" % (type, name))
    data_strs.append("data.addRows(%d);" % (len(rows)))
    for n, time in enumerate(sorted(rows)):
        for plot, yval, label in rows[time]: 
            currpt = ["data.setValue(%d,0, new Date(0,0,0,0,0,%f,0));" % (n, time),
                      "data.setValue(%d,%d, %s);" % (n, 2*plot+1, yval)]
            if label:
                currpt.append("data.setValue(%d,%d, %s);" % (n, 2*plot+2, label))
        data_strs.append("  ".join(currpt))
    return " ".join(data_strs)

def _add_points_assuming_string_labels(rows, starttime, endtime, label, labelnum):
    # Make sure the label is at 0 before the onset.
    rows[starttime-1e-3].append((labelnum, 0, None))
    # Event onset.
    rows[starttime].append((labelnum, 1, "'%s'" % label))
    # Event offset - don't use the exact end time, or the
    # widget will get confused if another label starts immediately
    # after this one ends.
    if endtime > starttime:
        rows[endtime-2e-3].append((labelnum, 1, None))
        rows[endtime-1.5e-3].append((labelnum, 0, None))
    else:
        rows[endtime+1e-3].append((labelnum, 0, None))


def _add_points_assuming_numeric_labels(rows, starttime, endtime, label, labelnum):
    yval = float(label)
    # Event onset
    rows[starttime].append((0, yval, "'%s'" % label))
    # Event offset - don't use the exact end time or the widget
    # will get confused.
    rows[endtime-1e-3].append((0, yval, None))


#feature_extractor datagrid --------------------------------------
def get_feature_extractor_url(row) :
    link = ET.Element('a',href='/feature_extractor/%s' % row.id)
    link.text = row.name
    return link

def get_feature_extractor_url_for_id(row) :
    link = ET.Element('a',href='/feature_extractor/%s' % row.id)
    link.text = str(row.id)
    return link

def get_feature_extractor_short_description(row) :
    return row.description.split('\n')[0]


def get_feature_extractor_source_code(fe) :
    f = open(fe.module_fullpath)
    lines = f.readlines()
    f.close()
    return lines

feature_extractor_datagrid = PaginateDataGrid(
    fields=[
    PaginateDataGrid.Column('id', get_feature_extractor_url_for_id, 'FeatureExtractor ID',options=dict(sortable=True)),
    PaginateDataGrid.Column('name', get_feature_extractor_url,'FeatureExtractor Name',options=dict(sortable=True)),
    PaginateDataGrid.Column('description', get_feature_extractor_short_description, 'Description'),
    ],
 )

def str_to_bool(val):
    if val.lower() == 'true':
        return True
    elif val.lower() == 'false':
        return False
    else:
        raise ValueError('Unable to convert %s to bool' % val)

def clean_kwargs(kwargs):
    cleaned_kwargs = {}
    for key,val in kwargs.iteritems():
        cleaned_val = val
        for conversion_func in [int, float, str_to_bool]:
            try:
                cleaned_val = conversion_func(val)
                break
            except ValueError:
                pass
        cleaned_kwargs[key] = cleaned_val
    return cleaned_kwargs

def load_all_cached_features(track):
    features = {}
    h5file = tables.openFile(track.fn_feature, mode='r')
    for fe_node in h5file.iterNodes(h5file.root):
        for array in h5file.iterNodes(fe_node):
            key = '%s (kwargs=%s)' % (array.attrs.feature_extractor_name,
                                      array.attrs.kwargs)
            features[key] = N.copy(array)
    h5file.close()
    return features

def plot_feats(feats):
    COLORBAR_WIDTH = 0.035
    COLORBAR_PAD = 0.015

    if feats.ndim == 2:
        plt.imshow(feats.T, origin='lower', interpolation='nearest',
                   aspect='auto')
        plt.colorbar(fraction=COLORBAR_WIDTH, pad=COLORBAR_PAD)
    else: 
        plt.plot(feats)
        # Compensate for colorbar axes in case this figure also
        # contains some images.
        axes = plt.gca()
        bounds = axes.get_position().bounds
        axes.set_position((bounds[0], bounds[1],
                           bounds[2] * (1 - COLORBAR_WIDTH - COLORBAR_PAD),
                           bounds[3]))
    plt.gca().set_xlim((0, len(feats)-1))

def plot_track_features(track, name=None, **kwargs):
    feats = {}
    if name:
        cleaned_kwargs = clean_kwargs(kwargs)
        key = '%s (kwargs=%s)' % (name, cleaned_kwargs)
        feats[key] = track.features(name, **cleaned_kwargs)
    else:
        feats = load_all_cached_features(track)
        
    plt.clf()
    nsubplots = len(feats)
    plt.gcf().set_size_inches((10,3*nsubplots))
    plt.subplots_adjust(left=0.10, bottom=0.10, top=0.9, right=0.95)

    for n, name in enumerate(sorted(feats.keys())):
        plt.subplot(nsubplots, 1, n+1)
        plot_feats(feats[name])
        plt.title(name)

    buf = StringIO()
    plt.savefig(buf, dpi=96, format='png')
    return buf
