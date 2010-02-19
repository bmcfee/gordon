/* migrate.sql is for leaving behind sql commands for updating existing installations 
of Gordon to new versions of DB.  

TODO: create migrate_db.py which provides def migrate_db(version)
this function would call migrate_<version>.sql depending on the 
version needed.  That is, paramaterize this to be more flexible. 

Douglas Eck (douglas.eck@gmail.com)
*/

/* 
alter table track alter column mb_id set default '';
alter table track alter column path set default '';
alter table track alter column title set default '';
alter table track alter column artist set default '';
alter table track alter column album set default '';
alter table track alter column tracknum set default -1;
alter table track alter column secs set default -1;
alter table track alter column zsecs set default -1;
alter table track alter column md5 set default '';
alter table track alter column compilation set default false;
alter table track alter column otitle set default '';
alter table track alter column oartist set default '';
alter table track alter column oalbum set default '';
alter table track alter column ofilename set default '';
alter table track alter column otracknum set default -1;
alter table track alter column source set default '';
alter table track alter column bytes set default -1;
*/ 

/* these commands simply rename album_stats to album_status and also do the
same for all indexes and constraints
*/
alter table album_stats rename to album_status;
alter index album_stats_pkey rename to album_status_pkey;
alter table album_status add constraint album_status_album_id_fkey foreign key (album_id) references album(id);
alter table album_status drop constraint album_stats_album_id_fkey;
alter sequence album_stats_id_seq rename to album_status_id_seq;

