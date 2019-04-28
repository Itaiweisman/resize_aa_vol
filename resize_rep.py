import requests
import os
import json
from infinisdk import InfiniBox
from capacity import GiB
import argparse
box_a='ibox2373'
box_b='ibox606'
auth=('infinidat','123456')
box_a_object=InfiniBox(box_a,auth)
box_b_object=InfiniBox(box_b,auth)
box_a_object.login()
box_b_object.login()
volume_name='ds3'
host='iocloudcore-02'
additional=2*GiB

def get_args():
    """
    Supports the command-line arguments listed below.
    """
    parser = argparse.ArgumentParser(description="Resizing replica for Active/Active")
    parser.add_argument('-v', '--volume', nargs=1, required=True, help='Name of the volume')
    parser.add_argument('-s', '--size', nargs=1, required=True, help='size to add in GiB')
    args = parser.parse_args()
    return args

def delete_replica(box,auth,volume):
	vol_replica=volume.get_replica().get_id()
	vol_replica_link=volume.get_replica().get_link().get_id()
	delete_url='http://'+box+'/api/rest/replicas/'+str(vol_replica)+'?retain_staging_area=True&approved=true'
	#print "delete url",delete_url
	delete_json=requests.delete(url=delete_url,auth=auth).json()
	#print delete_json
	local_snapshot_id=delete_json['result']['entity_pairs'][0]['_local_reclaimed_snapshot_id']
	remote_snapshot_id=delete_json['result']['entity_pairs'][0]['_remote_reclaimed_snapshot_id']
	remote_volume_id=delete_json['result']['entity_pairs'][0]['remote_entity_id']
	return (remote_volume_id,local_snapshot_id, remote_snapshot_id,vol_replica_link)

def recreate_replica_from_base(box,auth,link_id,local_volume_id,local_base_id,remote_volume_id,remote_base_id):
	DATA= {'replication_type':'ACTIVE_ACTIVE', 'entity_type':'VOLUME', 'link_id':link_id, 
		'entity_pairs':[ {
		'remote_base_action' : 'BASE',
		'local_base_action' : 'BASE',
		'local_entity_id': local_volume_id,
		'remote_entity_id' :remote_volume_id,
		'local_base_entity_id' : local_base_id,
		'remote_base_entity_id' : remote_base_id
			} 
		]
	}
	url='http://'+box+'/api/rest/replicas'
	headers={'Content-Type': 'application/json'}
	#print "DATA",DATA

	return requests.post(url=url,auth=auth,data=json.dumps(DATA),headers=headers)

def move_path_to_stb(box,auth,vol_id,to_active=True):
	headers={'Content-Type': 'application/json'}
	#box='ibox606'
	#auth=('infinidat','123456')
	url='http://'+box+'//api/internal/bridge/CORE_SERVICE'
	#vol_id=2108886
	to_standby = {
  	   "meta_data":{
       "command_id":"port_1",
       "command_type":"command",
       "magic":"0xab565ba",
       "module":"ScsiPort"
   },
       "params":{
          "action":"set_volumes_alua_parameters",
          "volume_entity_ids":[vol_id],
          "paths_available": to_active
       }
   }
	#print to_standby
	return requests.post(url=url,headers=headers,auth=auth,data=json.dumps(to_standby)).json()


args=get_args()

volume_name=args.volume[0]
size=args.size[0]
additional=int(size)*GiB

volume_box_b=box_b_object.volumes.find(name=volume_name).to_list()[0]
volume_box_a=box_a_object.volumes.find(name=volume_name).to_list()[0]
volume_id_box_b=volume_box_b.get_id()
volume_id_box_a=volume_box_a.get_id()

host=box_b_object.hosts.find(name=host).to_list()[0]

#print "Moving Paths to standby"
#move_path_to_stb(box_b,auth,volume_id_box_b,to_active=False)
#os.system("ssh root@io-cloudcore02 esxcli storage core adapter rescan -a")
print "Unmapping "
volume_box_b.unmap()
replica=volume_box_a.get_replica()
print "Deleting Replica"
remote_volume_id,local_snapshot_id, remote_snapshot_id,vol_replica_link=delete_replica(box_a,auth,volume_box_a)
print "Resizing on first box"
volume_box_a.resize(additional)
print "Resizing on second box"
volume_box_b.resize(additional)
print "Recreating Replica"
recreate=recreate_replica_from_base(box_a,auth,vol_replica_link,volume_id_box_a,local_snapshot_id,volume_id_box_b,remote_snapshot_id)
print "Remapping"
host.map_volume(volume_box_b)
#print "Moving Paths to active"
#move_path_to_stb(box_b,auth,volume_id_box_b)
#os.system("ssh root@io-cloudcore02 esxcli storage core adapter rescan -a")


