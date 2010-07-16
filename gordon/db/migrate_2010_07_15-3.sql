ALTER TABLE feature_extractor DROP COLUMN fname;
ALTER TABLE feature_extractor DROP COLUMN fdefcode;
ALTER TABLE feature_extractor ADD COLUMN module_path character varying(512);
