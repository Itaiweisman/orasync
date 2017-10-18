# Oracle Application Aware Snapshot script
## Overview
this procedur is used to perform application aware snapshot for Oracle environment.
it contains two scripts:
ora_sync.py - perform oracle hot backup and snapshot.
remove_old_snaps - remove old snaps according to retention policy
## Prerequisites:
* Python 2.7 
* following modules has to be installed: arrow, requests, infinisdk (for remove_old_snaps).
* oracle software (sqlplus) has to be installed ; firewall ports (typically TCP/1521) has to be unblocked and TNS settings has to be set to allow remove connection to Oracle database
database must be on archivelog mode
 
## Procedure steps:
* backup script
    1. Entering database to backup mode
    2.taking snapshot of all DATA volumes (volumes that contains database data files) - with the name convention 'orasync_data_<datestring>' - for instance orasync_data_2016-04-11_093413
    3. taking database out of backup mode
    4. perform switch redo operation (to force flush changes performed during the time the  database was on hot backup mode)
    5. taking snapshot of all ARCHIVE volumes (volumes that contains database archive files) - with the name convention 'orasync_archive_<datestring>' - for instance orasync_archive_2016-04-11_093413
**note**  - step 5 can be disabled if customer uses other method to protect his archive files such as log shipping etc.
procedure is being logged into a logfile with the following name convention - db<instance_name>-<datestring>.log - for instance db-myinstnace-2016-04-11_093413.log

* Retention Script
    1. Searches for all snapshot created before cutoff time (with this customer we used two weeks), and contain the name 'orasync' and delete them.

## Settings:
the following has to be set on the script (first configuration block) prior to running it:

Parameter | Description
--------- | -----------
ORACLE_SERVER | name of the instance to be protected (for logging)
SQLPLUS_CONNECTION_STRING | connection string to be used when connecting to the database
REPLICATED_ARCHIVE_VOLUMES | list of volumes, which contains archive logs files
REPLICATED_DATA_VOLUMES | list of volumes, which contains data files
SOURCE_INFINIBOX | name or IP of the InfiniBox (needs to have DNS set)
SOURCE_INFINIBOX_USER | user to be used when connecting the InfiniBox (has to have the admin role)
SOURCE_INFINIBOX_PASSWORD | password of the user used to connect the InfinBox
ORACLE_HOME	| oracle home (where sqlplus utility resides)

## invoking the script 
simply by running it (#./orasync-dbname.py)

## Notes
due to some limitation with this customer we did not use Infinisdk with the backup script, altough it is the recommended method. it uses raw API instead. it is assumed that there are not so many archive and data volumes, so queries do not cause heavy load on the server, plus there's no need for paging
no resolution between database files location and volumes. this has to be set manually. meaning, if you missed to specify the location of a datafile, the script is not aware of that. 
this version supports snapshoting a volume (rather then consistency group)
 
