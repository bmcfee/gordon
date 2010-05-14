/* migrate<date>.sql is for leaving behind sql commands for updating existing installations 
of Gordon to new versions of DB.  

Douglas Eck (douglas.eck@gmail.com)

Before using this file, run db/gordon_initialize.py first!
To use this file simply run the following command:
psql --user DEF_DBUSER --host DEF_DBHOST DEF_DBNAME < the_name_of_this_file.sql 
*/


alter table album add column created_at timestamp without time zone;


