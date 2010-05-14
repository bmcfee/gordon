/* migrate<date>.sql is for leaving behind sql commands for updating existing installations 
of Gordon to new versions of DB.  

Douglas Eck (douglas.eck@gmail.com)

For this version be sure and run db/gordon_initialize.py first!
*/


alter table album add column created_at timestamp without time zone;


