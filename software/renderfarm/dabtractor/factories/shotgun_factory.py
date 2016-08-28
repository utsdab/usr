#!/usr/bin/env rmanpy
import pprint
import sys
from software.shotgun_api3 import Shotgun
from software.renderfarm.dabtractor.factories import environment_factory as envfac

# ##############################################################
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)5.5s \t%(name)s \t%(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)
# ##############################################################

cfg = envfac.Environment()

class ShotgunBase(object):
    # base object
    def __init__(self):
        self.serverpath = str(cfg.getdefault("shotgun", "serverpath"))
        self.scriptname = str(cfg.getdefault("shotgun", "scriptname"))
        self.scriptkey  = str(cfg.getdefault("shotgun", "scriptkey"))
        self.sg = Shotgun( self.serverpath, self.scriptname, self.scriptkey)
        logger.info("SHOTGUN: talking to shotgun ...... %s" % self.serverpath)



class Projects(ShotgunBase):
    def __init__(self):
        super(Projects, self).__init__()
        __fields = ['id', 'name']
        __filters = [['id','greater_than',0]]

        try:
            self.projects=self.sg.find("Project",__filters,__fields)
        except Exception, err:
            logger.warn("%s"%err)
        else:
            logger.info("Found %d Projects" % (len(self.projects)))
            # logger.debug(self.projects)
            for project in self.projects:
                logger.info("   %s %s"%(project['id'],project['name']))

    def assets(self):
        pass
    def type(self):
        pass

    def sequences(self, projectid):
        # returns a list of dicts  [ {code:, type:, id: } ] of sequences for a given projectid
        fields = ['id', 'code']
        filters = [['project', 'is', {'type': 'Project', 'id': projectid}]]
        sequences= self.sg.find("Sequence",filters,fields)

        if len(sequences) < 1:
            print "couldn't find any Sequences"
        else:
            print "Found %d Sequences" % (len(sequences))
            print sequences


    def shots(self, projectid, sequenceid):
        # returns a list of dicts  [ {code:, type:, id: } ] of sequences for a given projectid
        _fields  = ['id', 'code', 'shots']
        _filters = [
                     ['project',   'is', {'type': 'Project',  'id': projectid}],
                     # ['sequences', 'is', {'type': 'Sequence', 'id': sequenceid }]
                  ]
        shots = self.sg.find("Sequence", _filters, _fields)


        if len(shots) < 1:
            print "couldn't find any shots"
        else:
            print "Found %d shots" % (len(shots))
            print shots

    def tasks(self):
        pass


class NewVersion(ShotgunBase):
    # new version object
    def __init__(self, media = None,
                 projectid = 89,
                 shotname = 'shot',
                 taskname = 'task',
                 versioncode = 'From Tractor',
                 description = 'Created from Farm Job',
                 ownerid = 38,
                 tag = "RenderFarm Proxy"
                 ):
        super(NewVersion, self).__init__()
        self.project = {'type': 'Project', 'id': projectid}
        self.shotname = shotname
        self.taskname = taskname
        self.versioncode = versioncode
        self.description = description
        self.owner = {'type':'HumanUser', 'id': ownerid}
        self.tag = tag
        self.media = media
        logger.info("SHOTGUN: File to upload ...... %s"%self.media)

        self.shotfilters = [ ['project','is', self.project],['code', 'is', self.shotname] ]
        self.shot = self.sg.find_one('Shot', self.shotfilters)

        self.taskfilters = [ ['project','is', self.project],
                    ['entity','is',{'type':'Shot','id': self.shot['id']}],
                    ['content','is',self.taskname] ]
        self.task = self.sg.find_one('Task',self.taskfilters)

        self.data = { 'project': self.project,
                 'code': self.versioncode,
                 'description': self.description,
                 'sg_status_list': 'rev',
                 'entity': {'type':'Shot', 'id':self.shot['id']},
                 'sg_task': {'type':'Task', 'id':self.task['id']},
                 'user': self.owner }
        self.version_result = self.sg.create('Version', self.data)
        logger.info("SHOTGUN: New Version Created : %s" % self.version_result)
        logger.info("SHOTGUN: Sending then transcoding.......")

        # ----------------------------------------------
        # Upload Latest Quicktime
        # ----------------------------------------------
        self.version_id = self.version_result.get('id')
        __result = self.sg.upload("Version", self.version_id, self.media, "sg_uploaded_movie", self.tag)
        logger.info ("SHOTGUN: Done uploading, upload reference is: %s"%__result)


    def test(self):
        pass



# ##############################################################################

if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    logger.info("------------------------------START TESTING")

    #  upload a movie
    # a = ShotgunBase()
    # b=NewVersion(projectid=89,
    #              shotname="tractortesting",
    #              taskname='layout',
    #              versioncode='from tractor 1',
    #              description='test version using shotgun api',
    #              ownerid=38,
    #              media='/Users/Shared/UTS_Dev/test_RMS_aaocean.0006.mov')

    # query projects shots etc
    c=Projects()
    c.sequences(89)
    c.shots(89,48)

    logger.info("-------------------------------FINISHED TESTING")


'''

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

'''
