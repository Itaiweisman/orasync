import time
import json
import logging
import sys
import os
from subprocess import Popen, PIPE
import requests
from time import strftime

# This script is recommended to run from crontab of 'oracle' user
# make sure you can connect with sqlplus from the host with those parameters

ORACLE_SERVER = 'dbuat'
SQLPLUS_CONNECTION_STRING = 'system/dbuatsys@'
ORACLE_HOME = '/u01/app/oracle/product/11.2.0/dbhome_1/'
REPLICATED_DATA_VOLUMES = ['']
REPLICATED_ARCHIVE_VOLUMES = ['']
SOURCE_INFINIBOX = ''
SOURCE_INFINIBOX_USER = 'admin'
SOURCE_INFINIBOX_PASSWORD = 'admin'  # infinidat level credentials needed

headers={'Content-Type':'application/json'}

def setup_logger(db):
	file=db+"-"+strftime("%Y-%m-%d_%H%M%S")+".log"
	logging.basicConfig(format='%(asctime)s %(message)s',filename=file,level=logging.DEBUG)
	print ("logfile is {}".format(file))
	logging.info("Started")
	logging.info("db is {}".format(db))



def run_sql_query(oracle_home, connection_string, sql_command):
    """
    :param oracle_home:
    :param connection_string:
    :param sql_command:
    :return: Left(error) or Right(execution_result)
    """
    sql_plus = '{0}/bin/sqlplus'.format(oracle_home)
    session = Popen(
        [sql_plus, '-S', connection_string],
        env=dict(os.environ, ORACLE_HOME=oracle_home),
        stdin=PIPE, stdout=PIPE, stderr=PIPE
    )
    session.stdin.write(sql_command)
    stdout, _ = session.communicate()
    stdout = "ERROR: Please check query string (should end with ;)" if not stdout else stdout
    print(stdout)
    logging.info("response for SQL: {}".format(stdout))
    if 'ERROR' in stdout:
        print("Unable to run SQL Query ; response {}".format(stdout))
		logging.error("Unable to run SQL Query ;Query {}; response {}".format(sql_command,stdout))
		error(10)
    else:
        return 



def start_db_backup():
    return run_sql_query(ORACLE_HOME, SQLPLUS_CONNECTION_STRING, 'alter database begin backup;')



def end_db_backup():
    return run_sql_query(ORACLE_HOME, SQLPLUS_CONNECTION_STRING, 'alter database end backup;')
	

def switch_redo():
    return run_sql_query(ORACLE_HOME,SQLPLUS_CONNECTION_STRING, 'alter system switch logfile;')

def get_vol_id(vol_list):
	returned=[]
	for vol in vol_list:
		url="http://"+SOURCE_INFINIBOX+"/api/rest/volumes?name="+vol
		try:
			id=requests.get(auth=(SOURCE_INFINIBOX_USER,SOURCE_INFINIBOX_PASSWORD),url=url).json()['result'][0]['id']
		except Exception as E:
			logging.error("Unable to list volume")
			print ("Unable to list volumes, error: {}".format(E))
			print ("Occured in {}".format(vol))
			print ("Exiting")
			exit(1)
		returned.append(id)
		print (vol,id)
	return returned 

def create_snap(pref,lista):
	try:
		for vol in lista:
			snap_name="orasync_"+pref+"_"+strftime("%Y-%m-%d_%H%M%S")
			print ("snap name {}".format(snap_name))
			url="http://"+SOURCE_INFINIBOX+"/api/rest/volumes"
			data={"parent_id":vol, "name":snap_name}
			#print ("Url: {}, Data: {}, headers:, {}".format(url,data,headers))
			snap=requests.post(auth=(SOURCE_INFINIBOX_USER,SOURCE_INFINIBOX_PASSWORD),url=url,data=json.dumps(data),headers=headers)
			error=snap.json()['error']
			if (error):
				
				logging.error('Unable to take snap, error: {}'.format(error))
				raise Exception('Unable to take snap, error: {}'.format(error))
	except Exception as E:
		print ("unable to create snap, excption {}".format(E))
		logging.error("unable to create snap, excption {}".format(E))
		print ("Exiting Hot Backup Mode")
		end_db_backup()
		exit(1)

def main():
	setup_logger(ORACLE_SERVER)
	data_volumes=get_vol_id(REPLICATED_DATA_VOLUMES)
	archive_volumes=get_vol_id(REPLICATED_ARCHIVE_VOLUMES)

	print ("entering hot backup")
	logging.info("entering hot backup")
	start_db_backup()
	time.sleep(5)
	print ("creating snapshot for data")
	logging.info("creating snapshot for data")
	create_snap("data",data_volumes)
	time.sleep(5)
	print ("ending hot backup mode")
	logging.info("ending hot backup mode")
	end_db_backup()
	time.sleep(5)
	print ("switching redo log")
	logging.info("switching redo log")
	switch_redo()
	time.sleep(5)
	print ("creating snapshot for archive")
	logging.info("creating snapshot for archive")
	create_snap("archive",archive_volumes)
	logging.info("Done!")
	exit(0)

if __name__ == "__main__":
    main()

