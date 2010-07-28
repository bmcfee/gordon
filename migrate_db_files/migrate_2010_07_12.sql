/* Alter feature_extractor
Jorge Orpinel <jorge@orpinel.com>
*/

ALTER TABLE feature_extractor DROP COLUMN "function";
ALTER TABLE feature_extractor DROP COLUMN code;
ALTER TABLE feature_extractor ADD COLUMN fname character varying(256);
ALTER TABLE feature_extractor ADD COLUMN fdefcode text;
