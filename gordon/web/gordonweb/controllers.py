# -*- coding: utf-8 -*-
"""This module contains the controller classes of the application."""

# symbols which are imported by "from gordonweb.controllers import *"
__all__ = ['Root']

# standard library imports
# import logging
import datetime

# third-party imports
from cherrypy import request
from turbogears import controllers, expose, flash, identity,\
    redirect, visit, paginate, validate, error_handler

from sqlalchemy import or_, func
import numpy as N
import pg,random,time,glob,string,sys

from widgets import *  #BAD  TODO remove this line and run pylint to find missing 
import widgets

from cherrypy.lib.cptools import serveFile
# project specific imports
#from gordonweb import model
import gordon.db.model as gordon_model
import gordon.db as gordon_db
import gordon.db.mbrainz_resolver
# from gordonweb import json
import gordon.db.config as config
import gordon.db

# log = logging.getLogger("gordonweb.controllers")


GORDON_DIR=config.DEF_GORDON_DIR_ON_WEBSERVER

class Root(controllers.RootController):
    """The root controller of the application."""

    @expose(template="gordonweb.templates.index")
    # @identity.require(identity.in_group("admin"))
    def index(self):
        """"Show the welcome page."""
        # log.debug("Happy TurboGears Controller Responding For Duty")
        #flash(_(u"Your application is now running"))
        return dict(now=datetime.datetime.now())


    @expose(template='gordonweb.templates.admin')
    @identity.require(identity.has_permission("edit"))
    def admin(self,task=''):

        if task=='resolve_all_albums': #closest_mb_albums_to_db' :
            mbrainz_resolver = gordon.db.mbrainz_resolver.GordonResolver()
            flash("Running mbrainz_resolver.resolve_all_albums()")
            mbrainz_resolver.resolve_all_albums()

        return dict()


    @expose("json")
    @identity.require(identity.has_permission("listen"))
    def mp3(self,fn_or_track_id) :
        #this should be flexible enough to do either a filename or track_id
        fn_or_track_id=str(fn_or_track_id)
        (path,fn) = os.path.split(fn_or_track_id)
        vals = fn.split('.')
        stub = vals[0]
        if stub.startswith('T') :
            stub=stub[1:]
        try :
            track_id = int(stub) 
        except :
            return "Cannot find mp3 %s" % str(fn_or_track_id)


        #we are hardcoding a path here to get around NFS issues
        outfn = gordon_db.get_full_mp3filename(track_id,gordonDir=GORDON_DIR)
        print 'Serving',outfn
        return cherrypy.lib.cptools.serveFile(path=outfn,disposition='attachment',name=os.path.basename(outfn))  


    @expose("json")
    @identity.require(identity.has_permission("listen"))
    def feature(self,fn_or_track_id) :
        #this should be flexible enough to do either a filename or track_id
        fn_or_track_id=str(fn_or_track_id)
        (path,fn) = os.path.split(fn_or_track_id)
        vals = fn.split('.')
        stub = vals[0]
        if stub.startswith('T') :
            stub=stub[1:]
        try :
            track_id = int(stub) 
        except :
            return "Cannot find feature %s" % str(fn_or_track_id)

        outfn = gordon_db.get_full_featurefilename(track_id,gordonDir=GORDON_DIR)
        #outfn = gordon_db.get_full_mp3filename(track_id,gordonDir=GORDON_DIR)
        print 'Serving',outfn
        return cherrypy.lib.cptools.serveFile(path=outfn,disposition='attachment',name=os.path.basename(outfn))  
        #return serve_file(fn)


    @expose("json")
    @identity.require(identity.has_permission("listen"))
    def cover(self,fn_or_album_id) :
        #this should be flexible enough to do either a filename or album_id
        #serves a cover if it is found. Otherwise serves an empty album graphic
        fn_or_album_id=str(fn_or_album_id)
        (path,fn) = os.path.split(fn_or_album_id)
        vals = fn.split('.')
        stub = vals[0]
        if stub.startswith('A') :
            stub=stub[1:]
        try :
            album_id = int(stub) 
        except :
            return "Cannot find cover %s" % str(fn_or_album_id)

        fn=''
        try :
            album = gordon_db.Album.query.get(album_id)
            fn=album.fn_albumcover
        except:
            pass
        if fn=='' or not os.path.exists(fn) :
            fn = '/static/images/emptyalbum.jpg'
#        return serve_file(fn)
        return cherrypy.lib.cptools.serveFile(path=fn)


    @expose(template="gordonweb.templates.login")
    def login(self, forward_url=None, *args, **kw):
        """Show the login form or forward user to previously requested page."""

        if forward_url:
            if isinstance(forward_url, list):
                forward_url = forward_url.pop(0)
            else:
                del request.params['forward_url']

        new_visit = visit.current()
        if new_visit:
            new_visit = new_visit.is_new

        if (not new_visit and not identity.current.anonymous
                and identity.was_login_attempted()
                and not identity.get_identity_errors()):
            redirect(forward_url or '/', kw)

        if identity.was_login_attempted():
            if new_visit:
                msg = _(u"Cannot log in because your browser "
                         "does not support session cookies.")
            else:
                msg = _(u"The credentials you supplied were not correct or "
                         "did not grant access to this resource.")
        elif identity.get_identity_errors():
            msg = _(u"You must provide your credentials before accessing "
                     "this resource.")
        else:
            msg = _(u"Please log in.")
            if not forward_url:
                forward_url = request.headers.get("Referer", "/")

        # we do not set the response status here anymore since it
        # is now handled in the identity exception.
        return dict(logging_in=True, message=msg,
            forward_url=forward_url, previous_url=request.path_info,
            original_parameters=request.params)

    @expose()
    def logout(self):
        """Log out the current identity and redirect to start page."""
        identity.current.logout()
        redirect("/")




    @expose(template="gordonweb.templates.stats")
    @identity.require(identity.has_permission("listen"))
    def stats(self) :
        track_total=gordon_model.Track.query.count()
        artist_total=gordon_model.Artist.query.count()
        album_total=gordon_model.Album.query.count()
        sec_total=gordon_model.session.query(func.sum(gordon_model.Track.secs)).first()[0]
        


        #string
        s=sec_total
        temp = float(s) / (60*60*24)
        d    = int(temp)
        temp = (temp - d) * 24
        h = int(temp)
        temp = (temp - h) * 60
        m = int(temp)
        temp = (temp - m) * 60
        sec = temp
        time_total='%s days %s hours %s minutes %i seconds' % (d,h,m,int(sec))

        track_labeled=track_total - gordon_model.Track.query.filter_by(mb_id='').count()
        artist_labeled=artist_total - gordon_model.Artist.query.filter_by(mb_id='').count()
        album_labeled=album_total - gordon_model.Album.query.filter_by(mb_id='').count()
        x=100.0*track_labeled/track_total

        track_pct = '%2.2f%%' % (100.0*track_labeled/track_total)
        artist_pct = '%2.2f%%' % (100.0*artist_labeled/artist_total)
        album_pct = '%2.2f%%' % (100.0*album_labeled/album_total)

        
        return dict(track_total=track_total,artist_total=artist_total,album_total=album_total,
                    track_labeled=track_labeled,artist_labeled=artist_labeled,album_labeled=album_labeled,
                    track_pct=track_pct,artist_pct=artist_pct,album_pct=album_pct,time_total=time_total,sec_total=sec_total)



   #track-------------------------------------------
    @expose(template="gordonweb.templates.track")
    @identity.require(identity.has_permission("listen"))
    @paginate('artists', default_order='name',limit=20)
    @paginate('albums', default_order='name',limit=20)
    def track(self, id=1, action='view') :

        if len(id)==36 :
            #mbid
            track = gordon_model.Track.query.filter_by(mb_id=id)
            if track.count()>0 :
                track=track.first()
                id = track.id
            else :
                track=None
        else :
            track = gordon_model.Track.query.get(id)
        if track==None :
            flash('gordon_model.Track %s not found' % str(id))
            redirect('/')
        track = gordon_model.Track.query.get(id)
        referer = cherrypy.request.headerMap.get("Referer", "/")
        track.referer=referer
        yahoo_url=get_yahoo_player_mp3(track)
        #widget_data is for the widget to render while track is the actual record.
        #allows us to render for viewing using DataGrid
        track_time=widgets.get_track_time(track)

    
        #feat_pathlist = widgets.get_featurelist(track.id)
        feat_urllist = list()
        #for p in feat_pathlist :
        #    elem =ET.Element('a',href='/%s' % p)
        #    (pth,feat)=os.path.split(p)##

            #set a short name to display in url
#            shortfeat=feat.split('.')
 #           shortfeat=string.join(shortfeat[2:],'.')
  #          elem.text=shortfeat
   #         feat_urllist.append(elem)


        if action=='edit':
            track_widget=track_edit_widget
            track_widget_data=track
            alternate_action=list()
            sub1=ET.Element('a',href='/track/%s/view' % str(id)); 
            sub1.text='View'
            alternate_action.append(sub1)

            print alternate_action
            #alternate_action=ET.Element('a',href='/track/%s/view' % str(id))
            #alternate_action.text='View'
            afeat_graph=''
        else :  #view
            track_widget=null_widget
            track_widget_data=list()#rotate_record(track)
            alternate_action=list()
            sub1=ET.Element('a',href='/track/%s/edit' % str(id))
            sub1.text='Edit'
            alternate_action.append(sub1)
            #afeat_graph=ET.Element('img',width='200',src='/dynimage?track=%s&typ=afeat' % str(id))
            grstr='/dynimage?track=%s&typ=afeat' % str(id)
            afeat_graph=ET.Element('a',href=grstr)
            afeat_img = ET.SubElement(afeat_graph,'img',align='right',src=grstr, width='400')
            
        #suppress alternate action if we are not an editor
        if not ("edit" in identity.current.permissions) :
            alternate_action=''
        
        if track.mb_id<>None and len(track.mb_id)>5 :
            track_mb_id_link = ET.Element('a',href='http://www.musicbrainz.org/track/%s.html' % track.mb_id)#,target='_blank')
            track_mb_id_link.text = "MusicBrainz"
        else :
            track_mb_id_link=''

        return dict(track_widget=track_widget,track_widget_data=track_widget_data,track=track,afeat_graph=afeat_graph,
                    alternate_action=alternate_action,artist_widget=artist_datagrid,artists=track.artists,track_time=track_time,
                    album_widget=album_datagrid,albums=track.albums,
                    yahoo_url=yahoo_url,feat_urllist=feat_urllist,track_mb_id_link=track_mb_id_link)


    @expose(template='gordonweb.templates.tracks')
    @identity.require(identity.has_permission("listen"))
    @paginate('tracks', default_order='id',limit=20)
    def tracks(self,track=''):
        print 'gordon_model.Track is',track
        if track <> '' :
            track=pg.escape_string(track)
            tracks = gordon_model.Track.query.filter("(lower(track.title) ~ ('%s'))" % track.lower())
            if tracks.count()==1 :
                #we only have one track, redirect to the album page
                redirect("/track/%s/view" % tracks[0].id)            
            print 'gordon_model.Tracks',tracks.count()
        else :
            tracks = gordon_model.Track.query().order_by('title')
        print 'gordon_model.Tracks',tracks.count(),type(tracks)
        return dict(tracks=tracks, tracklist=track_datagrid)

    @expose()
    @validate(form=track_edit_widget)
    @error_handler(track)
    @identity.require(identity.has_permission("edit"))
    def track_modify(self,**kw):
        operation=kw.pop('operation')
        id=kw.pop('id')
        referer=kw.pop('referer')
        track = gordon_model.Track.query.get(id)
        modfields=list()
        if operation=='edit' :
            for field in kw.keys() :
                #if track._SO_getValue(field)<> kw[field] :
                if track.__getattribute__(field)<> kw[field] :
                    modfields.append(field)
                    track.__setattr__(field,kw[field])
                    #not sure how to set a value using field name so we use eval
                    #exec('track.%s=%s' % (field,repr(kw[field])))

            if len(modfields)>0 :
                st='Saved track %s with field(s) %s' % (str(id),string.join(modfields,','))
            else :
                st='Nothing to save in track %s'% str(id)
            flash(st)
            if referer.count('resolve')>0 :
                raise(redirect(referer))
            else :
                raise redirect('/track/%s/edit' % id)

        elif operation=='delete' :
            #decrement track count for related album
            #I wish this could happen in the gordon_model.Track class but can't figure out how to get things to work.
            albums = track.albums;
            session.delete(track)
            flash('Deleted track %s' % str(id))

            for album in albums:
                if album.trackcount>0 :
                    print 'Decrementing track count of album',album
                    album.trackcount-=1
                    print 'gordon_model.Album track count is now',album.trackcount

            redirect(referer)
            
       
        
    @expose("json")
    @identity.require(identity.has_permission("listen"))
    def dynimage(self,track=1,typ='afeat'):
        raise ValueError('Plotting is turned off')
        from gordon.db import gordon_plotting as SP
        if typ=='afeat' :
            h = SP.plot_track_afeats(track=track)
        else :
            pass
            #let it crash. 
        cherrypy.response.headers['Content-Type']= "image/png"
        page=h.getvalue()
        return  page
    


    

                   
    #artists-----------------------------------------  
    @expose(template="gordonweb.templates.artist")
    @paginate('albums', default_order='name',limit=25)
    @paginate('artist_top_sims', default_order='value',limit=20)
    @paginate('artist_bottom_sims', default_order='value',limit=20)
    #@paginate('tracks', default_order='title',limit=10)
    @identity.require(identity.has_permission("listen"))
    def artist(self,id=1,action='view',shuffle=''):
        if len(id)==36 :
            #mbid
            artist = gordon_model.Artist.query.filter_by(mb_id=id)
            if artist.count()>0 :
                artist=artist.first()
                id = artist.id
            else :
                artist=None
        else :
            artist = gordon_model.Artist.query.get(id)
        
        if artist==None :
            flash('gordon_model.Artist %s not found' % str(id))
            redirect('/')

        referer = cherrypy.request.headerMap.get("Referer", "/")
        artist.referer=referer

        if artist.mb_id<>None and len(artist.mb_id)>5 :
            artist_mb_id_link = ET.Element('a',href='http://www.musicbrainz.org/artist/%s.html' % artist.mb_id)#,target='_top')
            artist_mb_id_link.text = "MusicBrainz"
        else :
            artist_mb_id_link=''
        #widget_data is for the widget to render while track is the actual record.
        #allows us to render for viewing using DataGrid
        if action=='edit':
            artist_widget=artist_edit_widget
            artist_widget_data=artist
            alternate_action=ET.Element('a',href='/artist/%s/view' % str(id))
            alternate_action.text='View'
        else :
            artist_widget=null_widget
            artist_widget_data=list()#rotate_record(artist)
            alternate_action=ET.Element('a',href='/artist/%s/edit' % str(id))
            alternate_action.text='Edit'
            
        artist_sims=list()
        artist_top_sims=list()
        artist_bottom_sims=list()
        #artist_sims=gordon_model.ArtistSim.query.filter_by(artist_id=id)
        #if artist_sims.count()==0 :
        #    artist_top_sims=list()
        #    artist_bottom_sims=list()
        #else :
        #    artist_sims=artist_sims[artist_sims.count()-1]
        #    artist_top_sims=artist_sims.top_sims
        #    artist_bottom_sims=artist_sims.bottom_sims

        #build list of mp3s
        #for t in artist.tracks :
        tracks = artist.tracks
        random.shuffle(tracks)
        mp3s=list()
        for (ctr,t) in enumerate(tracks) :
            link = widgets.get_yahoo_player_mp3(t,arrow=False)#ET.Element('a',title="%s - %s (%s)" % (t.artist,t.title,t.album),style='display:none',href='/mp3/T%s.mp3' % str(t.id))
            mp3s.append(link)
            if ctr==100 :
                break
        
        if shuffle=='' :
            shuffle_state=0
        else :
            shuffle_state=1
        return dict(artist_widget=artist_widget,artist_widget_data=artist_widget_data,artist=artist,alternate_action=alternate_action,
                    album_widget=album_datagrid,albums=artist.albums,artist_mb_id_link=artist_mb_id_link,shuffle_state=shuffle_state,action=action,
                    artist_top_sims=artist_top_sims,artist_bottom_sims=artist_bottom_sims,
                    artist_top_sim_datagrid=artist_top_sim_datagrid,artist_bottom_sim_datagrid=artist_bottom_sim_datagrid,
                    mp3s=mp3s)
     

    @expose(template='gordonweb.templates.artists')
    @identity.require(identity.has_permission("listen"))
    @paginate('artists', default_order='name',limit=20)
    def artists(self,artist='',album=''):
        if artist <> '' :
            artist=pg.escape_string(artist)
            artists = gordon_model.Artist.query.filter("(lower(artist.name) ~ ('%s'))" % artist.lower())
            if artists.count()==1 :
                redirect("/artist/%s/view" % artists[0].id)
        else :
            artists = gordon_model.Artist.query()

        return dict(artists=artists, artistlist=artist_datagrid)
    
    @expose(template="gordonweb.templates.artists")
    @identity.require(identity.has_permission("listen"))
    @paginate('artists', default_order='name',limit=10000000)
    def artists_all(self) :
        artists = gordon_model.Artist.query()
        return dict(artists=artists, artistlist=artist_datagrid)


    @expose()
    @validate(form=artist_edit_widget)
    @identity.require(identity.has_permission("edit"))
    @error_handler(artist)
    def artist_modify(self,**kw):
        operation=kw.pop('operation')
        id=kw.pop('id')
        mergeid=kw.pop('mergeid')

        referer=kw.pop('referer')
        artist = gordon_model.Artist.query.get(id)
        modfields=list()
        if operation=='edit' :
            for field in kw.keys() :
                #if artist._SO_getValue(field)<> kw[field] :
                if artist.__getattribute__(field)<> kw[field] :
                    modfields.append(field)
                    artist.__setattr__(field,kw[field])


            if len(modfields)>0 :
                st='Saved artist %s with field(s) %s' % (str(id),string.join(modfields,','))
            else :
                st='Nothing to save in artist %s'% str(id)
            flash(st)
            if referer.count('resolve')>0 :
                raise(redirect(referer))
            else :
                raise redirect('/artist/%s/edit' % id)
            
        elif operation=='delete' :
            #session.delete(artist)
            flash('Would have deleted artist %s' % str(id))
            redirect(referer)
            

        elif operation=='merge' :
            #str = 'Would have merged artist %s with artist %s' % (str(id),str(mergeid))
            flash('Would have merged artist %s with artist %s' % (str(id),str(mergeid)))
            tracks = gordon_model.Artist.query.get(int(id))
            for t in tracks :
                print

            redirect(referer)
    #queries -----------------------
    @expose("json")
    @identity.require(identity.has_permission("listen"))
    def query(self,album='',artist='',track='') :
        if album <> '' :
            redirect("/albums",dict(album=album))
        elif artist <> '' :
            redirect("/artists",dict(artist=artist))
        elif track <> '' :
            redirect("/tracks",dict(track=track))
        else :
            referrer=request.headers.get("Referer", "/")
            if referrer.endswith('query') :
                #break feedback loop
                redirect('/')
            else :
                redirect(referrer)

    #albums-----------------------------------------
    @expose(template="gordonweb.templates.album")
    @identity.require(identity.has_permission("listen"))
    @paginate('tracks', default_order='tracknum',limit=1000000)
    @paginate('artists', default_order='name',limit=50)
    def album(self,id=1,action='view',shuffle='') :
        if len(id)==36 :
            #mbid
            album = gordon_model.Album.query.filter_by(mb_id=id)
            if album.count()>0 :
                album=album.first()
                id = album.id
            else :
                album=None
        else :
            album = gordon_model.Album.query.get(id)
        if album==None :
            flash('gordon_model.Album %s not found' % str(id))
            redirect('/')

        referer = cherrypy.request.headerMap.get("Referer", "/")
        album.referer=referer
        albumcover = widgets.get_albumcover(album)
        artiststring = widgets.get_album_artiststring(album)
        if album.mb_id<>None and len(album.mb_id)>5 :
            album_mb_id_link = ET.Element('a',href='http://www.musicbrainz.org/release/%s.html' % album.mb_id)#target='_blank')
            album_mb_id_link.text = "MusicBrainz"
        else :
            album_mb_id_link=''
        #widget_data is for the widget to render while track is the actual record.
        #allows us to render for viewing using DataGrid
        if action=='edit':
            album_widget=album_edit_widget
            album_widget_data=album
            alternate_action=ET.Element('a',href='/album/%s/view' % str(id))
            alternate_action.text='View'
            track_widget=track_edit_datagrid
            deleteform_header=ET.Element('form',action='/album_modify/deletetracks', method="post")
            deleteform_button=ET.Element('input',type='submit',value='Delete Selected gordon_model.Tracks')
            deleteform_footer=ET.Element('/form')
        else :
            album_widget=null_widget
            album_widget_data=list()#rotate_record(artist)
            alternate_action=ET.Element('a',href='/album/%s/edit' % str(id))
            alternate_action.text='Edit'
            track_widget=track_datagrid_no_album
            deleteform_header=''
            deleteform_button=''
            deleteform_footer=''
            



        album_sims=list()
        album_top_sims=list()
        album_bottom_sims=list()
#        album_sims=gordon_model.AlbumSim.query.filter_by(album_id=id)
#        if album_sims.count()==0 :
#            album_top_sims=list()
#            album_bottom_sims=list()
#        else :
#            album_sims=album_sims[album_sims.count()-1]
#            album_top_sims=album_sims.top_sims
#            album_bottom_sims=album_sims.bottom_sims



        top_albumcovers=list()
        top_albumtitles=list()
        top_albumartists=list()
        albumtitles=set()
        albumartists=set()
        albumids=set() #albums already used
        ctr=0
        idx=0
        #build our grid for similar albums
        doall=False        
        do_albumgrid=False    
        while do_albumgrid and len(album_top_sims)>0:
            if idx==len(album_top_sims) :
                #oops we ran out of data. Loop again and take whatever we can get
                idx=1
                doall=True

            if ctr==9 :
                break
            
            other = album_top_sims[idx].other
            if not other :
                break
            album_id= other.id
            atitle = other.name
            if len(album_top_sims[idx].other.artists)>1 :
                aartist="Various gordon_model.Artists"
            elif len(album_top_sims[idx].other.artists)== 0:
                aartist="Unknown"
            else :
                aartist=album_top_sims[idx].other.artists[0].name
            albumcvr = widgets.get_albumcover(album_top_sims[idx].other,clickable=False,sz=90)

            albumtitle = ET.Element('a',href='/album/%s' % album_id)
            if len(atitle)>20 :
                atitle='%s...' % atitle[0:19]
            albumtitle.text = atitle

            albumartist = ET.Element('a',href='/album/%s' % album_id)
            albumartist.text = aartist
            idx+=1
            
            if not doall :
                #we try to skip some undesirable albums
                if atitle=="" : #skip blank albums
                    continue
                if atitle.lower()==gordon_model.Album.query.get(id).name.lower and aartist.lower()==gordon_model.Album.query.get(id).artists[0].name :
                    continue
                if aartist.lower()=='various artists' :
                    continue
                if aartist.lower() in albumartists :
                    continue
            albumartists.add(aartist.lower())
            albumtitles.add(atitle.lower())
 
            top_albumcovers.append(albumcvr)
            top_albumtitles.append(albumtitle)
            top_albumartists.append(albumartist)
            ctr+=1
        do_albumgrid= len(top_albumcovers)>8  #should we show an album grid?

        tracks=album.tracks
        if shuffle<>'' :
            random.shuffle(tracks)

        return dict(album_widget=album_widget,album_widget_data=album_widget_data,album=album,alternate_action=alternate_action,
                    artiststring=artiststring,album_mb_id_url=get_album_mb_id_url(album.mb_id),albumcover=albumcover,tracks=album.tracks,track_widget=track_widget,
                    artist_widget=artist_datagrid,artists=album.artists,deleteform_header=deleteform_header,
                    deleteform_button=deleteform_button,deleteform_footer=deleteform_footer,album_mb_id_link=album_mb_id_link,action=action,
                    album_top_sims=album_top_sims,album_bottom_sims=album_bottom_sims,
                    album_top_sim_datagrid=album_top_sim_datagrid,album_bottom_sim_datagrid=album_bottom_sim_datagrid,
                    top_albumcovers=top_albumcovers,top_albumtitles=top_albumtitles,top_albumartists=top_albumartists, do_albumgrid=do_albumgrid)


    @expose()
    @validate(form=album_edit_widget)
    @identity.require(identity.has_permission("edit"))
    @error_handler(album)
    def album_modify(self,**kw):
        operation=kw.pop('operation')
        id=kw.pop('id')
        referer=kw.pop('referer')
        album = gordon_model.Album.query.get(id)
        modfields=list()
        if operation=='edit' :
            for field in kw.keys() :
                if album.__getattribute__(field)<> kw[field] :
                    modfields.append(field)
                    album.__setattr__(field,kw[field])
                    #not sure how to set a value using field name so we use eval
                    exec('album.%s=%s' % (field,repr(kw[field])))

            if len(modfields)>0 :
                st='Saved album %s with field(s) %s' % (str(id),string.join(modfields,','))
            else :
                st='Nothing to save in album %s'% str(id)
            flash(st)
            if referer.count('resolve')>0 :
                raise(redirect(referer))
            else :
                raise redirect('/album/%s/edit' % id)

        elif operation=='delete' :
            session.delete(album)
            flash('Deleted album %s' % str(id))
            redirect(referer)
        
        elif operation=='deletetracks' :
            for field in kw.keys() :
                #delete checked tracks
                if kw[field]=='on' :
                    try :
                        id = int(field)
                        track = gordon_model.Track.query.get(id)
                        print 'Deleting',track
                        gordon_db.delete_track(track)
                    except :
                        print 'Could not delete track',field
            redirect(referer)

#123979
    @expose(template='gordonweb.templates.albums')
    @paginate('albums', default_order='name',limit=20)
    @identity.require(identity.has_permission("listen"))
    def albums(self,album='') :
        if album <> '' :
            album=pg.escape_string(album)
            print 'Searching for',album
            albums = gordon_model.Album.query.filter("(lower(album.name) ~ ('%s'))" % album.lower())
            if albums.count()==1 :
                #we only have one album, redirect to the album page
                redirect("/album/%s/view" % albums[0].id)
        else :
            albums = gordon_model.Album.query()

        return dict(albums=albums, albumlist=album_datagrid)
    
    @expose(template="gordonweb.templates.albums")
    @paginate('albums', default_order='name',limit=1000000)
    @identity.require(identity.has_permission("listen"))
    def albums_all(self) :
        albums = gordon_model.Album.query()
        return dict(albums=albums, albumlist=album_datagrid)

   

    #resolver---------------------------------------------
    @expose("json")
    @identity.require(identity.has_permission("edit"))
    def resolve_submitalbum(self,id=0,mb_id='') :
        mbrainz_resolver = gordon.db.mbrainz_resolver.GordonResolver()
        if  mb_id=='' :
            st= 'Recieved no mb_id'
        elif id==0 :
            st= 'Recieved invalid id'
        else :
            mbrainz_resolver.update_album(id=id,mb_id=mb_id,use_recommended_track_order=True,doit=True)
            st= 'Resolved musicbrainz album id %s against internal album id %s' % (mb_id,id)

        flash(st)


        #now go back to our review page
        redirect("/resolve_viewalbums")
        #referrer=request.headers.get("Referer", "/")
        #redirect(referrer)


    @expose()
    @identity.require(identity.has_permission("edit"))
    def resolve_submitalbums(self,**kw):
        mbrainz_resolver = gordon.db.mbrainz_resolver.GordonResolver()
        st=''
        for k in kw :
            (id,mb_id)=k.split('SEP')
            mb_id=mb_id.replace('H','-')
            mbrainz_resolver.update_album(id=id,mb_id=mb_id,use_recommended_track_order=True,doit=True)
            st="%s\nUpdated %s" % (st,id)
        flash(st)
        redirect("/resolve_viewalbums")


    @expose()
    @identity.require(identity.has_permission("edit"))
    def resolve_recommendalbum(self,id=1) :
        mbrainz_resolver = gordon.db.mbrainz_resolver.GordonResolver()
        mbrainz_resolver.resolve_album(id=id)
        redirect(request.headers.get("Referer", "/"))


    @expose()
    @identity.require(identity.has_permission("edit"))
    def resolve_setalbumstatus(self,id,status="weird",sort_order='conf') :
        #set the status of an album. 
        id = int(id)
        album=gordon_model.Album.query.get(id)
        if gordon_model.AlbumStatus.query.filter_by(album=album,status=status).count()==0 :
            gordon_model.AlbumStatus(album=album,status=status)


        #TODO: this next line will not ever return recommendations for albums marked with *any* AlbumStatus
        #it should probably be to only ignore those which are from a fixed list of AlbumStatus codewords.  Anyway this warrants
        #discussion. . . 

        #here we pull up the next album in the list. Is that what we want to do?
        mbrecommend = gordon_model.Mbalbum_recommend.query.filter(gordon_model.Mbalbum_recommend.album.has(gordon_model.Album.mb_id=='')).filter(gordon_model.Mbalbum_recommend.album.has(~gordon_model.Album.status.any())).order_by('%s DESC' % sort_order)
        print 'Redirecting to',str(mbrecommend[0].album_id)
        redirect("/resolve_viewalbum/%s" % str(mbrecommend[0].album_id))
        
        


    @expose(template="gordonweb.templates.resolve_viewalbum")
    @paginate('tracks',limit=100000000)
    @identity.require(identity.has_permission("edit"))
    def resolve_viewalbum(self,id=1) :

        album = gordon_model.Album.query.get(id)
        tracks = album.tracks
        albumcover = widgets.get_albumcover(album)
        artiststring = widgets.get_album_artiststring(album)
        res= gordon_model.Mbalbum_recommend.query.filter_by(album_id=id)
            
        if res.count()<>1 :
            flash('No recommendation or multiple recommendations for album %s' % id)
            redirect("/resolve_viewalbums")
        else :
            mbrecommend=res[0]


        if mbrecommend.trackorder<>None :
            trackorder = eval(mbrecommend.trackorder)
            if len(trackorder)==len(tracks) :
                trks = [0] * len(tracks)
                for t in tracks :
                    idx = trackorder[t.id]
                    trks[idx]=t
                tracks = trks



        mbrainz_resolver = gordon.db.mbrainz_resolver.GordonResolver()        

        #get the recommended album name for display

        (recommend_tracks,status) = mbrainz_resolver.add_mbalbumdata_to_trackdict(mbrecommend.mb_id,tracks) #adds mb tracks to tracks structure
        if status==False :
            #try redoing the recommmendation
            print 'Trying to get closest album'
            mbrainz_resolver.resolve_album(id) 
            (recommend_tracks,status) = mbrainz_resolver.add_mbalbumdata_to_trackdict(mbrecommend.mb_id,tracks) #adds mb tracks to tracks structure
            if status==False :
                flash('Unable to merge tracks for album %s' % id)
                redirect('/resolve_viewalbums')
        mbrecommend_mb_id_url=widgets.get_album_mb_id_url(mbrecommend.mb_id)
        mb_album=mbrecommend.mb_album
        submit_form = TableForm(
            fields=[TextField(name='mb_id',default=mbrecommend.mb_id,label='Recommended MB_ID',attrs=dict(size='38'))],
            action="../resolve_submitalbum/%s" % str(id),
            submit_text="Accept and Update(!)",
            )
        return dict(album=album,artiststring=artiststring,albumcover=albumcover,tracks=recommend_tracks,mb_album=mb_album,
                    tracklist=mbrecommend_track_datagrid,mbrecommend=mbrecommend,submit_form=submit_form,mbrecommend_mb_id_url=mbrecommend_mb_id_url)


    @expose(template="gordonweb.templates.resolve_viewalbums")
    @paginate('mbrecommend', default_order='-conf',limit=20)
    def resolve_viewalbums(self) :
        #get recommendations for un-mbrid albums with no status messages
        #here we assume that any status is a bad one. But this could be softened  by changing the any part of the query
        mbrecommend = gordon_model.Mbalbum_recommend.query.filter(gordon_model.Mbalbum_recommend.album.has(or_(gordon_model.Album.mb_id=='',gordon_model.Album.mb_id==None))).filter(gordon_model.Mbalbum_recommend.album.has(~gordon_model.Album.status.any()))
        return dict(mbrecommend=mbrecommend, mbrecommend_list=mbrecommend_datagrid)
    


    #download ---------------------------------------
    #@expose("json")
    @expose()
    #@identity.require(identity.has_permission("listen"))
    def download(self,params=''):
        pdict={'track_id':'','artist_id':'','album_id':'','randomize':'0'}
        pairs = params.split('!') 
        for p in pairs :
            (key,val)=p.split(':')
            pdict[key]=val
        tracks=''
        album=''
        if pdict['album_id']<>'' :
            album = gordon_model.Album.query.get(int(pdict['album_id']))
            tracks = album.tracks
        elif pdict['artist_id']<>'' :
            tracks = gordon_model.Artist.query.get(int(pdict['artist_id'])).tracks
        elif pdict['track_id']<>'' :
            tracks = [gordon_model.Track.query.get(int(pdict['track_id']))]
        
        return widgets.download(tracks=tracks,album=album,randomize=int(pdict['randomize']))



    #playlist ---------------------------------------
#    @expose("json", format="xml")
    @expose("gordonweb.templates.playlist_album", format="XML")
    #@identity.require(identity.has_permission("listen"))
    def playlist(self,params=''):
        if params.endswith('.xml') :
            params=params[0:len(params)-4]
            print params
        pdict={'track_id':'','artist_id':'','album_id':'','randomize':'0'}
        pairs = params.split('!') 
        for p in pairs :
            (key,val)=p.split(':')
            pdict[key]=val
        tracks=''
        album=''
        if pdict['album_id']<>'' :
            album = gordon_model.Album.query.get(int(pdict['album_id']))
            tracks = album.tracks
        elif pdict['artist_id']<>'' :
            tracks = gordon_model.Artist.query.get(int(pdict['artist_id'])).tracks
        elif pdict['track_id']<>'' :
            tracks = [gordon_model.Track.query.get(int(pdict['track_id']))]
        return widgets.playlist(tracks=tracks,album=album,randomize=int(pdict['randomize']))
