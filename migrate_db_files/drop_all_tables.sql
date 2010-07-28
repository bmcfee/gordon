/* Jorge Orpinel
Use this file if you want to rebuild the entire database WITHOUT dropping the database itself.
This is the correct table drop order. Run gordon_initialize script afterwards to rebuild the db with the most current structure.
NOTE: all your data will be lost when you use this code. Try backing up the data before and restoring it later, you might need to manually edit the data to conform to a new structure eg if any columns have been dropped.
*/

DROP TABLE album, artist, collection, track CASCADE;
DROP TABLE album_artist, album_status, album_track, annotation, artist_track, collection_track, feature_extractor, mbalbum_recommend, mbartist_resolve;
