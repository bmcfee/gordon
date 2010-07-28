/* Jorge Orpinel
Changing annotation name index
*/

-- annotation
DROP INDEX IF EXISTS ix_annotation_tid_name_value;
CREATE UNIQUE INDEX ix_annotation_tid_name ON annotation USING btree (track_id, name);