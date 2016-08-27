import logging
logging.basicConfig(level=logging.DEBUG)

import pprint
import sys
from software.shotgun_api3 import Shotgun


###########################  test code snippet
SERVER_PATH = "https://utsanim.shotgunstudio.com"
SCRIPT_NAME = 'shotgun_factory'
SCRIPT_KEY  = '694d48107fc5d7a05652afb060babff34bdfe99b4a2ea47d2adf718fc0a7745f'

sg = Shotgun(SERVER_PATH, SCRIPT_NAME, SCRIPT_KEY,True)
# pprint.pprint([symbol for symbol in sorted(dir(sg)) if not symbol.startswith('_')])

project = {'type': 'Project', 'id': 89}  ## projectx is 89
shotname = 'tractortesting'
taskname = 'layout'
versioncode = 'from tractor 1'
versiondescription = 'test version using shotgun api'
owner = {'type':'HumanUser', 'id':38}
tag = "RenderFarm Proxy"
quicktime = '/Users/Shared/UTS_Dev/test_RMS_aaocean.0006.mov'

filters = [ ['project','is', project],
            ['code', 'is', shotname] ]
shot    = sg.find_one('Shot',filters)

filters = [ ['project','is', project],
            ['entity','is',{'type':'Shot','id':shot['id']}],
            ['content','is',taskname] ]
task = sg.find_one('Task',filters)

data = { 'project': project,
         'code': versioncode,
         'description': versiondescription,
         'sg_status_list': 'rev',
         'entity': {'type':'Shot', 'id':shot['id']},
         'sg_task': {'type':'Task', 'id':task['id']},
         'user': owner }
version_result = sg.create('Version', data)
print "New Version Created"
pprint.pprint(version_result)
print "Sending then transcoding......."


# ----------------------------------------------
# Upload Latest Quicktime
# ----------------------------------------------
version_id = version_result.get('id')
result = sg.upload("Version",version_id,quicktime,"sg_uploaded_movie",tag)
print "Success Number is:",result

sys.exit("exit here")

# ----------------------------------------------
# Find Character Assets in Sequence WRF_03 in projectX
# ----------------------------------------------
fields = ['id', 'code', 'sg_asset_type']
sequence_id = 48 # Sequence "WFR_03"
filters = [
    ['project', 'is', projectx],
    ['sg_asset_type', 'is', 'Character'],
    ['sequences', 'is', {'type': 'Sequence', 'id': sequence_id}]
    ]

assets= sg.find("Asset",filters,fields)

if len(assets) < 1:
    print "couldn't find any Assets"
else:
    print "Found %d Assets" % (len(assets))
    print assets


# ----------------------------------------------
# Find Projects id and name
# ----------------------------------------------
fields = ['id', 'name']
filters = [['id','greater_than',0]]

projects= sg.find("Project",filters,fields)

if len(projects) < 1:
    print "couldn't find any Assets"
else:
    print "Found %d Assets" % (len(projects))
    pprint.pprint(projects)
############################################################


####  make playlist
####  add version to playlist
