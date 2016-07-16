'''
DABMLB0606627MG:testProject01 120988$ hrender /Users/Shared/UTS_Jobs/TESTING_HOUDINI/HoudiniProjects/testProject01/scripts/torus1.hipnc -d mantra1 -v -f 1 240 -i 1

Usage:

Single frame:   hrender    [options] driver|cop file.hip [imagefile]
Frame range:    hrender -e [options] driver|cop file.hip

driver|cop:     -c /img/imgnet
                -c /img/imgnet/cop_name
                -d output_driver

options:        -w pixels       Output width
                -h pixels       Output height
                -F frame        Single frame
                -b fraction     Image processing fraction (0.01 to 1.0)
		-t take		Render a specified take
                -o output       Output name specification
                -v              Run in verbose mode
                -I              Interleaved, hscript render -I

with "-e":	-f start end    Frame range start and end
                -i increment    Frame increment

Notes:  1)  For output name use $F to specify frame number (e.g. -o $F.pic).
        2)  If only one of width (-w) or height (-h) is specified, aspect ratio
            will be maintained based upon aspect ratio of output driver.

Error: Cannot specify frame range without -e.
'''

# ##############################################################
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)5.5s \t%(name)s \t%(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)
# ##############################################################

import tractor.api.author as author
import tractor.api.query as tq
import os
import sys
import time
from software.renderfarm.dabtractor.factories import user_factory as ufac
from software.renderfarm.dabtractor.factories import utils_factory as utils
from software.renderfarm.dabtractor.factories import configuration_factory as config

author.setEngineClientParam(hostname=config.CurrentConfiguration().tractorengine,
                            port=config.CurrentConfiguration().tractorengineport,
                            user=config.CurrentConfiguration().tractorusername,
                            debug=True)
tq.setEngineClientParam(hostname=config.CurrentConfiguration().tractorengine,
                            port=config.CurrentConfiguration().tractorengineport,
                            user=config.CurrentConfiguration().tractorusername,
                            debug=True)

class RenderBase(object):
    ''' Base class for all batch jobs '''

    def __init__(self):
        self.user = os.getenv("USER")
        self.spooljob = False
        self.testing=False

        try:
            # get the names of the central render location for the user
            ru = ufac.FARMuser()
            self.renderusernumber = ru.number
            self.renderusername = ru.name
            self.dabrender = ru.dabrender
            self.dabrenderworkpath = ru.dabuserworkpath
            self.initialProjectPath = ru.dabuserworkpath

        except Exception, erroruser:
            logger.warn("Cant get the users name and number back %s" % erroruser)
            sys.exit("Cant get the users name")

        if os.path.isdir(self.dabrender):
            logger.info("Found %s" % self.dabrender)
        else:
            self.initialProjectPath = None
            logger.critical("Cant find central filer mounted %s" % self.dabrender)
            raise Exception, "dabrender not a valid mount point"

class RenderMantra(RenderBase):
    ''' Renderman job defined using the tractor api '''

    def __init__(self,
                 envdabrender="",
                 envtype="",        # user_work
                 envshow="",        # matthewgidney
                 envproject="",     # mayaproject
                 envscene="",       # mayascenename - noextension ### not needed
                 mayaprojectpath="",    # /Users/Shared/UTS_Dev/dabrender/user_work/matthewgidney/matt_maya_project
                 mayascenerelpath="", # scene/mayascene.ma
                 mayascenefilefullpath="", ####### not needed
                 mayaversion="",
                 houdiniversion="",
                 startframe=1,
                 endframe=10,
                 byframe=1,
                 projectgroup="yr1",
                 outformat="",
                 resolution="720p",
                 skipframes=0,
                 sendmail=0,
                 makeproxy=0,
                 options="",
                 threadmemory=4000,
                 threads=4,
                 rendermaxsamples=64,
                 ribgenchunks=1,
                 email=[]
    ):
        super(RenderMantra, self).__init__()
        self.envdabrender = envdabrender
        self.envtype=envtype
        self.envproject=envproject
        self.envshow=envshow
        self.envscene=envscene


        # self.mayaprojectpathalias       = "$DABRENDER/$TYPE/$SHOW/$PROJECT"
        # self.mayaprojectpath = os.path.join(self.envdabrender, self.envtype, self.envshow, self.envproject)
        # self.mayaprojectnamealias       = "$PROJECT"
        # self.mayaprojectname = envproject
        # self.mayascenefilefullpathalias = "$DABRENDER/$TYPE/$SHOW/$PROJECT/$SCENE"
        # self.mayascenefilefullpath = os.path.join( self.envdabrender, self.envtype, self.envshow, self.envproject,
        #                                            self.envscene)
        self.scenename = os.path.split(envscene)[-1:][0]
        self.scenebasename = os.path.splitext(self.scenename)[0]
        self.sceneext = os.path.splitext(self.scenename)[1]
        # self.rendermanpath = os.path.join( self.envdabrender, self.envtype, self.envshow, self.envproject,
        #                                    "renderman", self.scenebasename)
        # self.rendermanpathalias = "$DABRENDER/$TYPE/$SHOW/$PROJECT/renderman/$SCENENAME"
        # self.renderdirectory = os.path.join(self.rendermanpath,"images")
        # self.renderimagesalias  = "$DABRENDER/$TYPE/$SHOW/$PROJECT/renderman/$SCENENAME/images"
        # self.mayaversion = mayaversion,
        self.houdiniversion = houdiniversion,
        self.envkey_mantra = "rms-houdini{}".format(self.houdiniversion[0])
        self.startframe = int(startframe)
        self.endframe = int(endframe)
        self.byframe = int(byframe)
        # self.ribgenchunks = int(ribgenchunks)  # pixar jobs are one at a time
        self.projectgroup = projectgroup
        self.options = options
        self.email = email
        self.resolution = resolution
        self.outformat = outformat
        self.makeproxy = makeproxy
        self.sendmail = sendmail
        self.skipframes = skipframes
        self.rendermaxsamples=rendermaxsamples
        self.threads = threads
        self.threadmemory = threadmemory
        # self.mayaprojectname = os.path.basename(self.mayaprojectpath)
        # self.ribpath = "{}/rib".format(self.rendermanpath)
        # self.finaloutputimagebase = "{}/{}".format(self.rendermanpath,self.scenebasename)
        # self.proxyoutput = "$DABRENDER/$TYPE/$SHOW/$PROJECT/movies/$SCENENAME_{}.mov".format("datehere")

    def build(self):
        '''
        Main method to build the job
        :return:
        '''

        # ################ 0 JOB ################
        self.job = author.Job(title="RM: {} {} {}-{}".format(
              self.renderusername,self.scenename,self.startframe,self.endframe),
              priority=10,
              envkey=[self.envkey_mantra,"ProjectX",
                    "TYPE={}".format(self.envtype),
                    "SHOW={}".format(self.envshow),
                    "PROJECT={}".format(self.envproject),
                    "SCENE={}".format(self.envscene),
                    "SCENENAME={}".format(self.scenebasename)],
              metadata="user={} username={} usernumber={}".format( self.user, self.renderusername,
                                                                   self.renderusernumber),
              comment="LocalUser is {} {} {}".format(self.user,self.renderusername,self.renderusernumber),
              projects=[str(self.projectgroup)],
              tier=config.CurrentConfiguration().defaultrendertier,
              tags=["theWholeFarm", ],
              service="")

    def validate(self):
        logger.info("\n\n{:_^80}\n{}\n{:_^80}".format("snip", self.job.asTcl(), "snip"))

    def mail(self, level="Level", trigger="Trigger", body="Render Progress Body"):
        bodystring = "Prman Render Progress: \nLevel: {}\nTrigger: {}\n\n{}".format(level, trigger, body)
        subjectstring = "FARM JOB: %s %s" % (str(self.scenebasename), self.renderusername)
        mailcmd = author.Command(argv=["sendmail.py", "-t", "%s@uts.edu.au" % self.user,
                                       "-b", bodystring, "-s", subjectstring], service="ShellServices")
        return mailcmd

    def spool(self):
        # double check scene file exists
        logger.info("Double Checking: {}".format(os.path.expandvars(self.mayascenefilefullpath)))
        if os.path.exists(os.path.expandvars(self.mayascenefilefullpath)):
            try:
                logger.info("Spooled correctly")
                # all jobs owner by pixar user on the farm
                self.job.spool(owner="pixar")
            except Exception, spoolerr:
                logger.warn("A spool error %s" % spoolerr)
        else:
            message = "Maya scene file non existant %s" % self.mayascenefilefullpath
            logger.critical(message)
            logger.critical(os.path.normpath(self.mayascenefilefullpath))
            logger.critical(os.path.expandvars(self.mayascenefilefullpath))

            sys.exit(message)

# ##############################################################################

if __name__ == "__main__":
    logger.setLevel(logging.INFO)
    logger.info("START TESTING")



    TEST = RenderMantra(
                       envdabrender="/Volumes/dabrender",
                       envproject="testFarm",
                       envshow="matthewgidney",
                       envscene="dottyrms.ma",
                       envtype="user_work",
                       # mayascenefilefullpath="/usr/local/tmp/scene/file.ma",
                       # mayaprojectpath="/usr/local/tmp/",
                       # mayaversion="2016",
                       # rendermanversion="20.2",
                       startframe=1,
                       endframe=12,
                       byframe=1,
                       outformat="exr",
                       resolution="540p",
                       options="",
                       skipframes=1,
                       makeproxy=1,
                       threadmemory="4000",
                       rendermaxsamples="128",
                       threads="4",
                       ribgenchunks=3,
                       email=[1, 0, 0, 0, 1, 0]
    )
    TEST.build()
    TEST.validate()
    logger.info("FINISHED TESTING")
