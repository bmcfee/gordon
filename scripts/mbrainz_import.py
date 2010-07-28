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

"""Set up a local copy of the MusicBrainz database"""

import os, pg, sys, socket

import gordon.db.config as config

from gordon import make_subdirs



def logged_on_dbhost() :
    """returns true if we are logged in on local dbhost"""
    if config.DEF_DBHOST.lower() == 'localhost':
        return True
    return socket.getfqdn()==socket.getfqdn(config.DEF_DBHOST)

def do_perms() :
    #this allows us to import using the more powerful brams account but then give the dbs over to gordon
    if not logged_on_dbhost() or os.environ['USER']<>config.DEF_DBSUPERUSER:
        raise ValueError('This must be run as user %s from host %s' % (config.DEF_DBSUPERUSER,config.DEF_DBHOST))


    dbmb = pg.connect('musicbrainz_db', user=config.DEF_DBSUPERUSER)
    result = dbmb.query("select tablename from pg_tables where schemaname = 'public'").getresult()
    for r in result :
        table = r[0]
        if table=='PendingData' :
            continue
        #q = 'alter table %s owner to "%s";' % (table, config.DEF_DBUSER)
        q = 'grant select on %s to "%s";' % (table, config.DEF_DBUSER)
        print q
        try :
            dbmb.query(q)
        except :
            print 'Failed'

def do_import() :
    """import tables.  Does this need to have existing tables dropped first? I think so..."""
    currdir=os.getcwd()

    #first drop tables if they exist
    cmd="dropdb 'musicbrainz_db'"
    print 'Executing',cmd
    os.system(cmd)

    cmd="dropdb 'musicbrainz_db_raw'"
    print 'Executing',cmd
    os.system(cmd)
    
    svnpath='%s/mbrainz/svn' % config.DEF_GORDON_DIR
    reppath='%s/%s' % (svnpath,'mb_server')
    os.chdir(reppath)  
    cmd='./admin/InitDb.pl --createdb --import ../../mbdump/latest/mb*bz2 --echo'
    print 'Executing',cmd
    os.system(cmd)
    os.chdir(currdir)
    
def do_svn() :
    """Gets fresh svn repo to DEF_GORDON_DIR/mbrainz/svn/mb_server from the appropriate branch (NOT TRUNK!)"""
    print 'TODO'
    print 'If you do this you will need to edit cgi-bin/DBDefs.pl in the following way:'
    print 'Replace musicbrainz_user with %s everywhere' % config.DEF_DBUSER
    print 'Replace postgres with your superuser account if you have replaced postgres.  E.g I use eckdoug'
    print 'This should be automated here!'
    print 'E.g replace username	=> "postgres", with username	=> "eckdoug",'
    print 'Also set the password for user %s to be the password' % config.DEF_DBUSER
    print ''
    print 'Also if you are running with local=utf, you need to edit the appropriate part of InitDb.pl to skip'
    print 'The test for locale.'
    print 'E.g. replace in file admin/InitDb.pl: '
    print ' unless ($locale eq "C")'
    print 'with'
    print ' unless (1)'

    currdir=os.getcwd()
    svnpath='%s/mbrainz/svn' % config.DEF_GORDON_DIR
    reppath='%s/%s' % (svnpath,'mb_server')
    if os.path.exists(reppath):
        os.chdir(reppath)
        print 'Doing svn update'
        os.system('svn update')
    else :
        os.chdir(svnpath) 
        #os.system('svn co http://svn.musicbrainz.org/mb_server/trunk mb_server')
        print 'We just rebuilt the musicbrainz svn. you will need to modify some config files. See:'
        print 'Most should be in lib/DBDefs.pm.default lib/DBDefs.pm'
        sys.exit(0)
    os.chdir(currdir)

def do_ftp(site='ftp://ftp.musicbrainz.org/pub/musicbrainz/data/fullexport',force=False) :
    """Imports fresh database files to DEF_GORDON_DIR/mbrainz/mbdump/latest"""
    import ftplib
    ftp=ftplib.FTP('ftp.musicbrainz.org')
    ftp.login('anonymous','')
    ftp.cwd('pub/musicbrainz/data/fullexport')
    for f in ftp.nlst() :
        if f.startswith('latest-is') :
            dr=f[10:]
          
    print 'Latest is',dr    
    testdir=os.path.join(config.DEF_GORDON_DIR,'mbrainz','mbdump',dr)
    if os.path.exists(testdir) :
        print 'We already have this dump... skipping. Set force=True to force download'
        if not force :
            ftp.close()
            return
    
    #handle for our writing
    def _ftp_handle(block) :
        fout.write(block)
        print ".",

    #we should be in the right directory now
    ftp.cwd(dr)
    for f in ftp.nlst() : 
        f=f.strip()
        # Open the file for writing in binary mode
        fnout=os.path.join(config.DEF_GORDON_DIR,'mbrainz','mbdump',dr,f)
        make_subdirs(fnout)
        print 'Opening local file ' + fnout
        fout= open(fnout, 'wb')
        print 'downloading',f
        ftp.retrbinary('RETR ' + f, _ftp_handle)
        print 'Done downloading',f
        fout.close()

    ftp.close()
    
    currdir=os.getcwd()
    #create symlink from latest to our new dump
    os.chdir('%s/mbrainz/mbdump' % config.DEF_GORDON_DIR)
    try :
        os.system('rm latest')
    except :
        pass
    os.system('ln -s %s latest' % dr)
    os.chdir(currdir)

def mbrainz_import():
    if not logged_on_dbhost() or os.environ['USER']<>config.DEF_DBSUPERUSER:
        raise ValueError('This must be run as user %s from host %s' % (config.DEF_DBSUPERUSER,config.DEF_DBHOST))
    do_ftp()
    do_svn()
    #raw_input('commented out do_ftp and do_svn temporarily!')
    do_import()
    do_perms()



def die_with_usage() :
    print 'This program rebuilds the musicbrainz databases.'
    print 'It loads the dumps to %s/mbrainz/mbdump/latest' % config.DEF_GORDON_DIR
    print 'It then updates the svn code in %s/mbrainz/svn' % config.DEF_GORDON_DIR
    print 'It then does necessary data imports from the dumps'
    print ('It then sets appropriate permissions to allow user %s to read the databases'
           % config.DEF_DBUSER)
    print ''
    print 'To run code:'
    print 'Be sure you are logged into %s' % config.DEF_DBHOST
    print 'Be sure you are user %s' % config.DEF_DBSUPERUSER
    print 'mbrainz_import.py go'
    sys.exit(0) 

if __name__=='__main__' :
    if len(sys.argv)<2 :
        die_with_usage()


    mbrainz_import()



