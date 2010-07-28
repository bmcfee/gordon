/* Rename some columns.

Ron Weiss (ronw@nyu.edu)
*/

alter table annotation rename column annotation to name;
alter table collection rename column source to name;
alter table feature_extractor rename column identifier to name;


