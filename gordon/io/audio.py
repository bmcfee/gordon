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
'''ffmpeg wrapper for reading audio files'''

import os, sys, string#,tempfile, time #jorgeorpinel: unused
#from numpy import * #jorgeorpinel: unused
import numpy 
#import tempfile #jorgeorpinel: unused



class AudioFile(object):
    """Represents audio file.  This class is a wrapper for ffmpeg.  It supports reading and writing audio files.
    Reading can be done at native sampling rate or at a target rate. You can also read random chunk of file using tstart_sec and tlen_sec. 
    Finally leading and trailing zeros can be stripped from the file """
    stripvals=['none', 'both', 'leading', 'trailing']
    #todo: use myme/types...
    filetypes=['.wav', '.aif', '.aiff', '.m4a', '.mp3', '.au', '.flac'] #todo: apply them, add more
    
    def __init__(self,fn, mono=False,tlast=-1,tstart_sec=None,tlen_sec=None,fs_target=-1, stripzeros='none',stripzeros_lim=0.0001):
        """Represents an audio file
        Flags:          fn: file name
                     mono: yields a mono sample
                    tlast: is desired last sample in sec (deprecated! do not use. Exception will be raised)
               tstart_sec: is desired starting point in seconds in file
                 tlen_sec: is desired number of seconds to read.  
                fs_target: is a target fs. resampling / decimation will be used to get the target rate
               stripzeros: removes near-zero-values from beginning and/or end of signal
                           values can be 'none','both','leading','trailing'
           stripzeros_lim: is the limit used for stripping leading and trailing zeros; default=0.1             
        """ 
        self.fn=fn
        self.mono=mono  
        self.tlast=tlast
        self.stripzeros=stripzeros
        self.stripzeros_lim=stripzeros_lim
        self.x=None
        self.svals=None
        self.chans=None

        self.tstart_sec=tstart_sec       #starting point in seconds for reading from file
        self.tlen_sec=tlen_sec           #number of seconds to read from file
        if tlast <>-1 :
            raise ValueError("tlast is deprecated. Replace with tstart_sec and tlen_sec")
        
        self.fs_target=fs_target         #target sampling rate for our waveform
        self.fs=None                     #sampling rate of our waveform
        self.fs_file=None                #native sampling rate of our file 
        self.stats_read=False            #marked true when file stats are read in. This allows us to call read_stats() at the start of every read()
        self.stats_looping=False         #a bit of a hack to allow read_stats() to itself call read() when it cannot determine file length
        self.hash=None                   #hash code for read file to keep us from reading multiple times for same parameters
     
    def write(self,x,fs):
        """Writes x to file with sampling rate fs"""
        import scikits.audiolab 
        scikits.audiolab.wavwrite(x,self.fn,fs)

    def read_stats(self,noloop=False) :
        """Returns statistics about file
        [fs_file, chans, lensec]
             fs_file:  the sampling rate of our file (not of our desired waveform, which may be resampled)
               chans:  number of channels
                secs:  length of audio file in seconds
        Stores these same variables in class

        The variable noloop simply keeps us from falling into an infinite loop when we call read from here
        """

        if not os.path.exists(self.fn) :
            raise IOError ('File %s not found' %self.fn )

        if self.stats_read :
            return
        self.stats_read=True

        self.fs_file=None
        self.chans=None
        self.secs=None

        (ignore,stub)=os.path.splitext(self.fn.lower())
        if self.filetypes.count(stub)==0 :
            raise ValueError('Cannot read stats for file of type %s' % stub)

        #read mp3 using ffmpeg
#        cmd = 'ffmpeg -i %s 2>&1' %  self._slashify(self.fn)
        cmd = 'ffmpeg -i "%s" 2>&1' % self.fn #jorgeorpinel: lets just double-quote self.fn (Windiws)
        #here we read in fs_file, chan, secs using the output from ffmpeg -i
        #when pyffmpeg next version comes out we should be able to replace this
        #in the meantime, lets hope fftmpeg never changes its text output. . . .
        data=self._command_with_output(cmd).split('\n')
        for l in data :
            if l.count('Duration:')>0 :
                try :
                    vals = l.strip().split(' ')
                    dur=vals[1]
                    [hours,mins,sec]=dur.split(':')
                    sec=sec[0:len(sec)-1]
                    self.secs=float(hours)*3600+float(mins)*60+float(sec)
                except :
                    pass
            if l.count('Audio:')>0:
                try :
                    [ignore,vals]= l.split('Audio:')
                    vals=vals.split(',')
                    for v in vals :
                        if v.strip().endswith('Hz') :
                            [fs_file,ignore]=v.strip().split(' ')
                            self.fs_file=int(fs_file)
                        #we have two ways to read in number of channels depending on version of ffmpeg.
                        #later versions use the keyword channels, older versions use stereo/mono
                        elif v.strip()=='stereo' :
                            self.chans=2
                        elif v.strip()=='mono' :
                            self.chans=1
                        elif v.strip().endswith('channels') :
                            [chans,ignore]=v.strip().split(' ')
                            self.chans=int(chans)
                            
                except :
                    pass

        if (self.fs_file is None) or (self.chans is None) : 
            raise ValueError("Unable to read fs_file=%s or chans=%s from file. Cannot recover from this\n\n%s" % (str(self.fs_file),str(self.chans),data))

        if self.secs is None :
            #this is a bit of a hack. For certain file types, ffmpeg does not give file length in seconds
            #so we will try to calculate it by loading file. Slow but what can you do?
            if self.stats_looping==False: #we only try this once! 
                self.read() #try to get our values by reading
                self.stats_looping=True
            if self.secs is None :
                raise ValueError('Unable to read length of file. Cannot recover from this')

        return [self.fs_file, self.chans,self.secs]

    def read(self, fs_target=None, mono=None, tstart_sec=None, tlen_sec=None, stripzeros=None, stripzeros_lim=None, tlast=None,force=False):
        """Reads file and returns:
        [x, fs, svals]
                   x:  the data as a numpy array. Stereo will have 2 columns.
                  fs:  the sampling rate of our waveform (not necessarily the native sampling rate of file)
               svals:  [st,en] number of samples stripped from start and end of signal 

        Also keeps references of x,fs,svals in class

        Note: this method will only read the file one time for a given sampling rate, svals, mono setup.
        After doing so it will cache the result. To force a re-read, simply set force to True

        Note: Most of the constructor parameters are echoed here to allow this behavior of reading the same file 
        for different read parameters.  Changing a parameter using read() will store that parameter as new default
        for future calls to read.
        """

        if not os.path.exists(self.fn) :
            raise IOError ('File %s not found' %self.fn )
        
        #get defaults from our class if they are not passed in here
        #this strategy allows us to call read multiple times for same instance and get 
        #different sampling rates, etc
        #print 'FSTARGET is',fs_target
        if fs_target is not None :
            self.fs_target=fs_target
        if mono is not None :
            self.mono=mono
        if tstart_sec is not None :
            self.tstart_sec=tstart_sec
        if tlen_sec is not None:
            self.tlen_sec=tlen_sec
        if tlast is not None :
            raise ValueError('tlast is deprecated. use tstart_sec and tlen_sec')
        if stripzeros is not None :
            self.stripzeros=stripzeros
        if stripzeros_lim is not None :
            self.stripzeros_lim=stripzeros_lim

        #get stats
        self.read_stats()  #get stats (read_stats controls to make sure we don't inefficently read stats twice)

        #this is our hash
        hash=self.fn+'fs_target='+str(self.fs_target)+'%mono='+str(self.mono)+'%tstart_sec='+str(self.tstart_sec)
        hash+='%tlen_sec='+str(self.tlen_sec)+'%stripzeros='+str(self.stripzeros)+'%stripzeros_lim='+str(self.stripzeros_lim)

        if (self.hash is not None) and (self.hash==hash) and not force :
            #we have already read this
            return (self.x,self.fs,self.svals)

        (ignore,stub)=os.path.splitext(self.fn.lower())
        if self.filetypes.count(stub)==0:
            raise ValueError('Cannot read file of type %s' % stub)

        # ffmpeg turns out to be not so accurate with respect to timing. So we 
        # are not trying to do tstart_sec in ffmpeg but rather in tstart_sec is 
        # where we start in seconds, tlen_sec is how many seconds to read in
        bypass_ffmpeg_times=False
        timing=''
        ffmpeg_time_offset=.05

        if not bypass_ffmpeg_times:
            timing ='-async 1'
            if self.tstart_sec is not None and self.tstart_sec>0.0 :
                if self.tstart_sec<ffmpeg_time_offset :
                    raise ValueError('tstart_sec %4.4f must be greater than .05 or else there will be slight alignment errors' % self.tstart_sec)
                timing='%s -ss %4.6f' % (timing,self.tstart_sec-ffmpeg_time_offset)
            if self.tlen_sec is not None:
                timing='%s -t %4.6f' % (timing, self.tlen_sec + ffmpeg_time_offset)

        #resample if necessary
        if self.fs_target<>-1 and (self.fs_target <> self.fs_file) :
            downsamp=' -ar %i' % self.fs_target
            self.fs=self.fs_target  #we presume our resampling is successful
        else :
            downsamp=''
            self.fs=self.fs_file    #we trust the sampling rate stored in the file



        #here is our command.
#        cmd = 'ffmpeg -i %s %s %s -f s16le 2>/dev/null -' % (self._slashify(self.fn),downsamp,timing)
        #jorgeorpinel: is this really necesary? it needs permissions on the original file's dir:
        cmd = 'ffmpeg -i "%s" %s %s -f s16le 2>/dev/null -' % (self.fn, downsamp, timing) #jorgeorpinel: lets 2blequote instead (Windows)
        #jorgeorpinel: NOTE - /dev/null in Windows simply make ffmpeg say "The system cannot find the path specified." to stderr


        #old slow
        if 0 :
            data=numpy.fromstring(self._command_with_output(cmd),'short')
            x = numpy.zeros(len(data),'float')
            x[:] = data/float(32768)
        else : #faster ...less memory alloc
            x=numpy.fromstring(self._command_with_output(cmd),'short').astype('float')/float(32768)
        
        

        x=x.reshape(-1,self.chans)

        if bypass_ffmpeg_times:
            if self.tlen_sec is not None :
                tlast_sec = self.tlen_sec
                if self.tstart_sec is not None:
                    tlast_sec+=tstart_sec
                x=x[0:tlast_sec*float(self.fs),:]

            if self.tstart_sec is not None:
                x=x[self.tstart_sec*float(self.fs):,:]
        else :
            #we used ffmpeg to read a random segment. remove leading zeros introduced by -async 1
            if self.tstart_sec is not None:
                x=x[ffmpeg_time_offset*self.fs:,:]
            if self.tlen_sec is not None:
                if len(x)>=self.tlen_sec*self.fs :
                    x=x[:self.tlen_sec*self.fs,:]


        if self.secs==None :
            self.secs=x.shape[0]/float(self.fs)

        if self.mono and len(numpy.shape(x))>1 :
            x=numpy.mean(x,1)
        assert(len(numpy.shape(x))<= 2)  #better be stereo or mono!

        (x,svals) = self._strip_zeros(x)    
        self.x=x
        self.svals=svals
        self.hash=hash        

        return (self.x,self.fs,self.svals)
    
    def get_secs_zsecs(self) :
        """Returns a tuple containing the number of seconds in the file
        as well as the number of seconds in the file after stripping zeros from front and back."""  
        [x,fs,svals]=self.read(stripzeros='both')
        zsecs=len(x)/float(fs)
        secs=zsecs+(svals[0]+svals[1])/float(fs)
        return [secs,zsecs]

    def plot(self) :
        if self.x is None:
            raise ValueError('You must first read audio file before plotting')
        import pylab
        t=numpy.arange(len(self.x))/float(self.fs)
        t+=self.svals[0]/float(self.fs)

        if len(self.x.shape)>1 and self.x.shape[1]==2 :
            pylab.subplot(211)
            pylab.plot(t,self.x[:,0])
            pylab.title(self.fn)
            pylab.ylabel('amplitude')
            pylab.xlabel('time (sec)')
            pylab.subplot(212)
            pylab.plot(t,self.x[:,1])
            pylab.ylabel('amplitude')
            pylab.xlabel('time (sec)')
        else :
            pylab.plot(t,self.x)
            pylab.title(self.fn)
            pylab.ylabel('amplitude')
            pylab.xlabel('time (sec)')

        pylab.show()


    def _strip_zeros(self,x) :
        """strips zeros from front and or end of x depending on value self.stripzeros"""
        if self.stripvals.count(self.stripzeros)<>1 :
            print 'Invalid value',self.stripzeros,'given for stripzeros; must be leading, trailing, both or none'
            print 'Setting to none'
            stripzeros='none'
   
        if self.stripzeros=='none' :
            return (x,numpy.zeros(2))
        
        

        leading_samples=0
        trailing_samples=0
        if len(x) == 0 :
            return (x,numpy.zeros(2))
        if not self.stripzeros == 'none':
            #prepare mono abs sequence for checking zerovals
            if len(numpy.shape(x))==1 :
                x.reshape((-1,1))
            #be sure our sequence is not all zeros (or <self.stripzeros_lim)
            #we will sample from the middle of the file K times. If they're all 0
            #we will take the max. This way we won't always take the max, which is expensive!
            if len(x)>100 :
                midIdx=int(len(x)/2)
                takeMax=True
                for i in range(midIdx,midIdx+10) :
                    if numpy.mean(abs(x[i,:])) >= self.stripzeros_lim :
                        takeMax=False
                        break
                if takeMax :
                    if abs(x).max()<self.stripzeros_lim :
                        #print 'here',abs(x).max()
                        return([],(len(x),0))

        if self.stripzeros == 'leading' or self.stripzeros == 'both' :
            leading_samples=0
            while numpy.mean(abs(x[leading_samples,:]))<self.stripzeros_lim and leading_samples<(len(x)-1) :
                #print xAbs[leading_samples],leading_samples,self.stripzeros_lim
                leading_samples += 1

            if leading_samples>0:
                x=x[leading_samples:,:]  #stereo                

        if self.stripzeros == 'trailing' or self.stripzeros == 'both' :
            trailing_idx=len(x)-1
            orig_len=len(x)
            while numpy.mean(abs(x[trailing_idx,:]))<self.stripzeros_lim and trailing_idx>0 :
                trailing_idx -= 1
            if trailing_idx<len(x)-1:
                x=x[0:trailing_idx,:]  #stereo
            trailing_samples=orig_len-trailing_idx
    
        svals=numpy.zeros(2)
        svals[0]=leading_samples
        svals[1]=trailing_samples

        if x.shape[1]==1 :
            x.reshape((-1,0))

        return (x,svals) 

    def _slashify(self,fname) : #todo: this is not being used now
        """slashify filename to be safe for calling os.popen(cmd)"""
        s_fname=string.replace(fname," ","\ ")
        s_fname=string.replace(s_fname,"\'","\\'")
        s_fname=string.replace(s_fname,"\"","\\\"")
        s_fname=string.replace(s_fname,"(","\(")
        s_fname=string.replace(s_fname,")","\)")
        s_fname=string.replace(s_fname,"&","\&")
        s_fname=string.replace(s_fname,";","\;")
        s_fname=string.replace(s_fname,"$","\$")
        s_fname=string.replace(s_fname,"`","\`")
        s_fname=string.replace(s_fname,",","\,")
        s_fname=string.replace(s_fname,"-","\-")
        return s_fname

    def _command_with_output(self, cmd):
        """Runs command on system and returns output"""
        import subprocess
        if not type(cmd) == unicode :
#            cmd = unicode(cmd, 'utf-8') #jorgeorpinel: this may cause UnicodeDecodeError
            cmd = '%s' % cmd
        print "audio.py: Running cmd '"+cmd+"' from", os.getcwd() # debug -------
        #child = subprocess.Popen(cmd, shell=True, bufsize=-1, stdout=subprocess.PIPE).stdout
        #dat = child.read() # dat has the cmd line output
        #err = child.close()


        process = subprocess.Popen(cmd, shell=True, bufsize=-1, stdout=subprocess.PIPE)
        (dat,err)=process.communicate()
        #dat = child.read() # dat has the cmd line output
        #err = child.close()

        if err<>None :
            print 'Error',err,'in running command',cmd
        return dat # stdout command output ------------------------------ return dat

    def __str__(self) :
        if self.fs is None:
            self.read_stats()
        return 'AudioFile %s fs_sequence=%s fs_file=%s fs_target=%s channels=%i secs=%4.4f' % (self.fn, str(self.fs),str(self.fs_file),str(self.fs_target), self.chans, self.secs)


def die_with_usage() :
    print 'audio.py [flags] file'
    print 'This is mainly a library function to be used by other code'
    print 'Flags:'
    print ' -decoder <decoder> where decoder is mpg123 (default), madplayer or pymad'
    print ' -testdecoders will compare decoders'
    print ' -mono will force mono'
    print ' -fs <rate> sets target sample rate'
    print 'Arguments :'
    print '  <file> is a valid mp3, wave or au file'
    sys.exit(0)

if __name__=='__main__' :
    import sys

    if len(sys.argv)<2 :
        die_with_usage()

    fs_target=-1
    mono=False
    while True :
        if sys.argv[1] == '-fs' :
            fs_target=int(sys.argv[2])
            sys.argv.pop(1)
        elif sys.argv[1] == '-mono' :
            mono=True
        else :
            break
        sys.argv.pop(1)

    import time
    tic=time.time()
    af = AudioFile(sys.argv[1],fs_target=fs_target,mono=mono)

    #print af.get_secs_zsecs()
    #print time.time()-tic,'for total'



    af.read()
    af.plot()

