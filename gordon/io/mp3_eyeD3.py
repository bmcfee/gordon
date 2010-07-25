#! /usr/bin/env python

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

#id3v2
import eyeD3
import os


def mp3_gettime(mp3) :
    return eyeD3.tag.Mp3AudioFile(mp3).getPlayTime()

def mp3_get_itunes_cddb(mp3) :
    cs = id3v2_getval(mp3,'comments')
    return eyeD3.tag.Mp3AudioFile(mp3).getPlayTime()


def id3v2_getval(mp3,tagstr) :
    if type(tagstr)==tuple :
        tagstr=list(tagstr)

    tag=eyeD3.Tag()
    try :
        tag.link(mp3)
    except :
        #if we could not link to id3 return empty vals
        if type(tagstr)==list :
            return ['']*len(tagstr)
        else :
            os.sys.stderr.write('eyeD3 unable to link to file %s\n' % (mp3))
            return ''
        

    if type(tagstr)==list :
        retval=list()
        for t in tagstr :
            try :
                val = id3v2_getval_sub(tag,t)
            except :
                os.sys.stderr.write('eyeD3 unable to read id3 tag(s) %s from file %s\n' % (str(tagstr),mp3))
                val=''
            retval.append(val)
        return retval
    else :
        #try :
        val=id3v2_getval_sub(tag,tagstr)
        #except :
        #    val=''
        #    os.sys.stderr.write('eyeD3 unable to read id3 tag %s from file %s\n' % (tagstr,mp3))
        return val
                    
def id3v2_getval_sub(tag,tagstr):
    #eyeD3 throws lots of exceptions. We will ignore most of them
    #can't figure out how to do this the right way ...
    if tagstr=='album' :
        return tag.getAlbum()
    elif tagstr=='bpm':
        return tag.getBPM()
    elif tagstr=='comment':
        return tag.getComment()
    elif tagstr=='date':
        return tag.getDate()
    elif tagstr=='genre':
        return tag.getGenre()
    elif tagstr=='lyrics':
        return tag.getLyrics()
    elif tagstr=='playcount':
        return tag.getPlayCount()
    elif tagstr=='title':
        return tag.getTitle()
    elif tagstr=='urls':
        return tag.getURLs()
    elif tagstr=='textframes':
        return tag.getUserTextFrames()
    elif tagstr=='versionstr':
        return tag.getVersionStr()
    elif tagstr=='artist':
        return tag.getArtist()
    elif tagstr=='cdid':
        return tag.getCDID()
    elif tagstr=='comments':
        return tag.getComments()
    elif tagstr=='discnum':
        return tag.getDiscNum()
    elif tagstr=='images':
        return tag.getImages()
    elif tagstr=='objects':
        return tag.getObjects()
    elif tagstr=='publisher':
        return tag.getPublisher()
    elif tagstr=='trackinfo' :  #trackNum() returns trackinfo, a list (tracknum,trackcount)
        return tag.getTrackNum()
    elif tagstr=='tracknum':
        trackinfo = tag.getTrackNum()
        if len(trackinfo)==2 :
            if trackinfo[0]==None :
                return 0
            return trackinfo[0]
        else :
            return 0
    elif tagstr=='trackcount': #here we return the trackcount
        trackinfo = tag.getTrackNum()
        if len(trackinfo)==2 :
            if trackinfo[1]==None :
                return 0
            return trackinfo[1]
        else :
            return 0
    elif tagstr=='uniquefileid':
        return tag.getUniqueFileIDs()
    elif tagstr=='version':
        return tag.getVersion()
    elif tagstr=='year':
        return tag.getYear()

    #our additions....
    elif tagstr=='compilation':
        #itunes hack
        for f in tag.frames :
            if f.header.id=='TCMP' and f.text==u'1' :
                return True
        return False
    
    elif tagstr=='tid':
        #do tids specially
        comments = tag.getComments()
        tids=list()
        for c in comments:
            if c.description=='TID'  :
                tids.append(c)
        if len(tids)==0 :
            return ''
        elif len(tids)==1 :
            return tids[0].comment
        else :
            return tids
    elif tagstr=='itunes_cddb' :
        comments = tag.getComments()
        tids=list()
        for c in comments:
            if c.description==u'iTunes_CDDB_IDs'  :
                return c.comment
        return ''
    
        
    else :
        print 'Unknown tag:',tagstr
        return ''
    
def id3v2_putval(mp3,tagstr,txt=''):
    tag=eyeD3.Tag()
    tag.link(mp3)
    tag.update(eyeD3.ID3_V2_4) # writes on file
    tag.header.setVersion(eyeD3.ID3_V2_4) # writes on file
    try :
        tag.setTextEncoding(eyeD3.UTF_8_ENCODING)
    except TypeError :
        #work around bug in tag.py of eyeD3
        pass

    #catch some obvious problems with typing
    if type(txt)==int or type(txt)==float  or type(txt)==bool :
        #print 'Translating',txt,'of type',type(txt),'to str',str(txt)
        txt=str(txt)

        
    #can't figure out how to do this the right way so we'll do it in a big ugly if :-)
    if tagstr=='album' :
        retval = tag.setAlbum(txt)
    elif tagstr=='bpm':
        retval = tag.setBPM(txt)
    elif tagstr=='comment':
        retval = tag.setComment(txt)
    elif tagstr=='date':
        retval = tag.setDate(txt)
    elif tagstr=='genre':
        retval = tag.setGenre(txt)
    elif tagstr=='lyrics':
        retval = tag.setLyrics(txt)
    elif tagstr=='playcount':
        retval = tag.setPlayCount(txt)
    elif tagstr=='title':
        retval = tag.setTitle(txt)
    elif tagstr=='urls':
        retval = tag.setURLs(txt)
    elif tagstr=='textframes':
        retval = tag.setUserTextFrames(txt)
    elif tagstr=='versionstr':
        retval = tag.setVersionStr(txt)
    elif tagstr=='artist':
#        import db_utils
#        print 'Setting title to something of len',len(txt)
#        if type(txt)==str  :
#            print txt
#        else :
#            print db_utils.deaccent_unicode(txt)
        retval = tag.setArtist(txt)
    elif tagstr=='cdid':
        retval = tag.setCDID(txt)
    elif tagstr=='comments':
        retval = tag.setComments(txt)
    elif tagstr=='discnum':
        retval = tag.setDiscNum(txt)
    elif tagstr=='images':
        retval = tag.setImages(txt)
    elif tagstr=='objects':
        retval = tag.setObjects(txt)
    elif tagstr=='publisher':
        retval = tag.setPublisher(txt)
    elif tagstr=='tracknum':
        trackcount = tag.getTrackNum()[1]
        retval = tag.setTrackNum((txt,trackcount))
    elif tagstr=='trackcount':
        tracknum = tag.getTrackNum()[0]
        retval = tag.setTrackNum((tracknum,txt))
    elif tagstr=='uniquefileid':
        retval = tag.setUniqueFileIDs(txt)
    elif tagstr=='version':
        retval = tag.setVersion(txt)
    elif tagstr=='year':
        retval = tag.setYear(txt)
    elif tagstr=='compilation' :
        #itunes hack
        if txt.lower()=='false' :
            pass
            #we want to remove the TCMP frame if it exists
        else :            
            #we want to add the TCMP frame
            #does it already exist?
            hasComp=False
            for f in tag.frames :
                if f.header.id=='TCMP' :
                    f.text=u'1'
                    hasComp = True          

            if not hasComp :
                #print 'Adding frame'
                hdr = eyeD3.frames.FrameHeader()
                frame = eyeD3.frames.TextFrame(hdr)
                frame.header.id='TCMP'
                frame.text=u'1'
                tag.frames.append(frame)
            else :
                print 'File already has TCMP frame'
        retval=''
        
    elif tagstr=='tid' :
        #do tids specially
        comments = tag.getComments()
        retval=''
        if len(comments)>0 :
            #remove existing TID comments (by adding non-TID comments back into empty comment)
            tag.removeComments()
            for c in comments:
                if not c.description=='TID':
                    tag.addComment(unicode(c.comment),c.description,c.lang)
                else :
                    retval=c.comment  #return old value
        #add tid comment
        #print 'adding comment is commented'
        tag.addComment(unicode(txt),'TID','eng')
    else :
        retval=''
        print 'Unknown tag:',tagstr
    #we fall back to v2.3 for itunes compat.

    try :
        tag.setTextEncoding(eyeD3.UTF_8_ENCODING)
    except TypeError :
        #work around bug in tag.py of eyeD3
        pass
    tag.update(eyeD3.ID3_V2_3)
    return retval

def isValidMP3(filePath):
    """Uses eyeD3.tag.link to determine whether a file is a vliad MP3
    @author Jorge Orpinel <jorge@orpinel.com>"""
    tag=eyeD3.Tag()
    return True if tag.link(filePath) else False

def getAllTags(mp3fp, skipTrackFields=True):
    """Return a list with all tags in the form [description, content]
    or False if mp3fp is not an MP3 file (path).
    
    These are the Frame types and their instance fields (see eyeD3.frame) :
    *Text*: text, date_str, (description)
    *URL*: url, (description)
    Comment|Lyrics: (lang), (description), comment|lyrics
    Image: (mimeType), (pictureType), (description), imageData, imageURL
    Object: (mimeType), (description), filename, objectData
    PlayCount: count
    UniqueFileID: owner_id, id
    Unknown: data
    MusicCDId: toc
    See also http://www.id3.org/id3v2.3.0#head-e4b3c63f836c3eb26a39be082065c21fba4e0acc (6/11/2010)
    
    @author Jorge Orpinel <jorge@orpinel.com>"""
    
    tag=eyeD3.Tag()
    if not tag.link(mp3fp): return False
    
    tags = list()
    for frame in tag.frames:
        frameCode = frame.render()[:4]
        
        #skip basic tags already in track (employ skipTrackFields)
        if skipTrackFields and\
        frameCode in [eyeD3.TITLE_FID,     # title
                      eyeD3.ARTIST_FID,    # artist
                      eyeD3.ALBUM_FID,     # album
                      eyeD3.TRACKNUM_FID,  # track #
                      "TCP"]:              # iTunes "compilation"
            continue
        
        thisTag=list()
        
        # gets tag description #todo: prepend "ID3 vX.X"
        thisTag.append(frameCode + ': ' + frame.getFrameDesc())
        try: thisTag[0] += ' - ' + frame.description
        except: pass
        try: thisTag[0] += ' (' + frame.lang + ')'
        except: pass
        try: thisTag[0] += ' ' + frame.mimeType
        except: pass
        try: thisTag[0] += ' ' + frame.pictureType
        except: pass
        thisTag[0]=thisTag[0].strip()
        
        # gets tag content
        thisTag.append(str())
        try: thisTag[1] += frame.text+' '
        except: pass
        try: thisTag[1] += frame.date_str
        except: pass
        try: thisTag[1] += frame.url
        except: pass
        try: thisTag[1] += frame.comment
        except: pass
        try: thisTag[1] += frame.lyrics
        except: pass
        try: thisTag[1] += frame.imageURL # images contain data in bytes: frame.imageData
        except: pass
        try: thisTag[1] += frame.filename # objects contain data in bytes: frame.objectData
        except: pass
        try: thisTag[1] += frame.count
        except: pass
        try: thisTag[1] += frame.owner_id + ': ' + frame.id
        except: pass
        try: thisTag[1] += frame.data
        except: pass
        try: thisTag[1] += frame.toc
        except: pass
        thisTag[1]=thisTag[1].strip()
        
        tags.append(thisTag)
        
    return tags


if __name__=='__main__' :
    import sys
    import shutil
    import random
    import os

    #pressure test    
    ctr=0
    files=list()
    dir=sys.argv[1]
    for root,dirs,files in os.walk(dir) :
        for f in files :
            if f[len(f)-4:len(f)]=='.mp3' :
                fullF='%s/%s' % (root,f)
                files.append(fullF)
                ctr=1
                if ctr>10000:
                    break


    random.shuffle(files)
    i=0
    for f in files :
        tid=db_utils.id3v2_getval(fullfile,'tid')
        print i,fullfile
        i+=1

    sys.exit(0)
        
    #mp3=sys.argv[1]

    #2.3 to 2.4
    v24='v24_%s' % mp3
    shutil.copyfile(mp3,v24)
    tag=eyeD3.Tag()
    tag.link(v24)
    print 'Curr version of',v24,'is',tag.getVersion()
    tag.update(eyeD3.ID3_V2_4)
    print 'New version is',tag.getVersion()

    #2.3 to 2.4 to 2.3
    v23from24='v23from24_%s' % mp3
    shutil.copyfile(v24,v23from24)
    tag=eyeD3.Tag()
    tag.link(v23from24)
    print 'Curr version of',v23from24,'is',tag.getVersion()
    tag.update(eyeD3.ID3_V2_3)
    print 'New version is',tag.getVersion()
    



