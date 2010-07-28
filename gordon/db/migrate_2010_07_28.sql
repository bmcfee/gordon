/* Jorge Orpinel

DB Schema cleanup (commit 197 and up) assumes you have ran all previous migrate .sql files
If this doesn't quite fix the DB, please backup data, drop_all_tables.sql (or just drop the database and recreate it, and run gordon_initialize script)

*/

-- album
ALTER TABLE album DROP COLUMN created_at;

CREATE INDEX ix_album_id ON album USING btree (id);
DROP INDEX IF EXISTS album_name_idx;
CREATE INDEX ix_album_mb_id ON album USING btree (mb_id);
DROP INDEX IF EXISTS album_mb_id_idx;
CREATE INDEX ix_album_name ON album USING btree (name);
DROP INDEX IF EXISTS album_trackcount_idx;

-- album_artist
DROP INDEX IF EXISTS artist2album_aid_idx;
CREATE INDEX ix_album_artist_album_id ON album_artist USING btree (album_id);
DROP INDEX IF EXISTS artist2album_rid_idx;
CREATE INDEX ix_album_artist_artist_id ON album_artist USING btree (artist_id)
CREATE INDEX ix_album_artist_id ON album_artist USING btree (id);

-- album_status
CREATE INDEX ix_album_status_album_id ON album_status USING btree (album_id);
CREATE INDEX ix_album_status_id ON album_status USING btree (id);

-- album_track
DROP INDEX IF EXISTS album2track_rid_idx ;
CREATE INDEX ix_album_track_album_id ON album_track USING btree (album_id);
DROP INDEX IF EXISTS album2track_tid_idx;
CREATE INDEX ix_album_track_track_id ON album_track USING btree (track_id);
CREATE INDEX ix_album_track_id ON album_track USING btree (id);

-- annotation
CREATE INDEX ix_annotation_id ON annotation USING btree (id);
DROP INDEX IF EXISTS annotation_track_idx;
CREATE INDEX ix_annotation_track_id ON annotation USING btree (track_id);
DROP INDEX IF EXISTS annotation_name;
CREATE INDEX ix_annotation_name ON annotation USING btree (name);
CREATE UNIQUE INDEX ix_annotation_tid_name_value ON annotation USING btree (track_id, name, value);

-- artist
CREATE INDEX ix_artist_id ON artist USING btree (id);
DROP INDEX IF EXISTS artist_mb_id_idx;
CREATE INDEX ix_artist_mb_id ON artist USING btree (mb_id);
DROP INDEX IF EXISTS artist_name_idx;
CREATE INDEX ix_artist_name ON artist USING btree (name);
DROP INDEX IF EXISTS artist_trackcount_idx;

-- artist_track
DROP INDEX IF EXISTS artist2track_aid_idx;
CREATE INDEX ix_artist_track_artist_id ON artist_track USING btree (artist_id);
DROP INDEX IF EXISTS artist2track_tid_idx;
CREATE INDEX ix_artist_track_track_id ON artist_track USING btree (track_id);
CREATE INDEX ix_artist_track_id ON artist_track USING btree (id);

-- collection
CREATE INDEX ix_collection_id ON collection USING btree (id);
CREATE UNIQUE INDEX ix_collection_name ON collection USING btree (name);

-- collection_track
CREATE INDEX ix_collection_track_collection_id ON collection_track USING btree (collection_id);
CREATE INDEX ix_collection_track_track_id ON collection_track USING btree (track_id);
CREATE INDEX ix_collection_track_id ON collection_track USING btree (id);

-- feature_extractor
CREATE INDEX ix_feature_extractor_id ON feature_extractor USING btree (id);
DROP INDEX IF EXISTS ix_feature_extractor_name;
CREATE UNIQUE INDEX ix_feature_extractor_name ON feature_extractor USING btree (name);

-- mbalbum_recommend
CREATE INDEX ix_mbalbum_recommend_id ON mbalbum_recommend USING btree (id);
DROP INDEX IF EXISTS mbalbum_recommend_album_id_key;
CREATE INDEX ix_mbalbum_recommend_album_id
  ON mbalbum_recommend
  USING btree
  (album_id);

-- mbartist_resolve
DROP INDEX IF EXISTS mbartist_resolve_mb_id_idx;
CREATE INDEX ix_mbartist_resolve_mb_id ON mbartist_resolve USING btree (mb_id);
DROP INDEX IF EXISTS mbartist_resolve_artist_idx;
CREATE INDEX ix_mbartist_resolve_artist ON mbartist_resolve USING btree (artist);
CREATE INDEX ix_mbartist_resolve_id ON mbartist_resolve USING btree (id);

-- track
ALTER TABLE track ADD COLUMN created_at timestamp without time zone;
ALTER TABLE track ALTER COLUMN created_at SET STORAGE PLAIN;

CREATE INDEX ix_track_id ON track USING btree (id);
DROP INDEX IF EXISTS track_mb_id_idx;
CREATE INDEX ix_track_mb_id ON track USING btree (mb_id);
DROP INDEX IF EXISTS track_title_idx;
CREATE INDEX ix_track_title ON track USING btree (title);
DROP INDEX IF EXISTS track_artist_idx;
CREATE INDEX ix_track_artist ON track USING btree (artist);
DROP INDEX IF EXISTS track_album_idx;
CREATE INDEX ix_track_album ON track USING btree (album);
