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
alter table album_stats rename to album_status;
alter index album_stats_pkey rename to album_status_pkey;
alter relation album_stats_album_id_fkey rename to album_status_album_id_fkey;
alter index album_stats_album_id_fkey rename to album_status_album_id_fkey;
alter table album_status drop constraint album_stats_album_id_fkey;
alter sequence album_stats_id_seq rename to album_status_id_seq;

