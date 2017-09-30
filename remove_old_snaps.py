from infinisdk import InfiniBox
import arrow
SNAP_NAME='a.snap'
CUTOFF=3
SYSTEM='ibox1150'
AUTH=('admin','123456')

try:
	now=arrow.utcnow()
	before=now.replace(days=-CUTOFF)
	system=InfiniBox(SYSTEM,AUTH)
	system.login()
	for snapshot in (system.volumes.find(system.volumes.fields.created_at < before, system.volumes.fields.name.like(SNAP_NAME)).to_list()):
		if (snapshot.get_parent()):
			print snapshot.get_name()
			snapshot.delete()
	
except:
	pass
