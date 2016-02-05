#!/usr/bin/env rmanpy
"""
To do:
    find commonality in render jobs and put it in base class

    implement ribchunks - DONE
    implement option args and examples - rms.ini

    implement previews???
    implement stats to browswer

"""
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
import os
import sys
import time
from software.renderfarm.dabtractor.factories import user_factory as ufac
from software.renderfarm.dabtractor.factories import utils_factory as utils
from software.renderfarm.dabtractor.factories import configuration_factory as config

author.setEngineClientParam(hostname="tractor-engine", port=5600, user="pixar", debug=True)

class RenderBase(object):
    """
    Base class for all batch jobs
    """

    def __init__(self):
        self.user = os.getenv("USER")
        self.spooljob = False
        self.testing=True

        try:
            # get the names of the central render location for the user
            ru = ufac.User()
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


class RenderPrman(RenderBase):
    '''
        Renderman job defined using the tractor api
    '''

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
                 rendermanversion="",
                 startframe=1,
                 endframe=10,
                 byframe=1,
                 projectgroup="yr1",
                 outformat="",
                 resolution="720p",
                 skipframes=0,
                 makeproxy=0,
                 options="",
                 threadmemory=4000,
                 threads=4,
                 rendermaxsamples=64,
                 ribgenchunks=1,
                 email=[]
    ):
        super(RenderPrman, self).__init__()
        self.testing=True
        self.envdabrender = envdabrender
        self.envtype=envtype
        self.envproject=envproject
        self.envshow=envshow
        self.envscene=envscene
        self.mayaprojectpathalias       = "$DABRENDER/$TYPE/$SHOW/$PROJECT"
        self.mayaprojectpath = os.path.join(self.envdabrender,self.envtype,self.envshow,self.envproject)
        self.mayaprojectnamealias       = "$PROJECT"
        self.mayaprojectname = envproject
        self.mayascenefilefullpathalias = "$DABRENDER/$TYPE/$SHOW/$PROJECT/$SCENE"
        self.mayascenefilefullpath = os.path.join(
                self.envdabrender,self.envtype,self.envshow,self.envproject,self.envscene)
        self.scenename = os.path.split(envscene)[-1:][0]
        self.scenebasename = os.path.splitext(self.scenename)[0]
        self.sceneext = os.path.splitext(self.scenename)[1]
        self.rendermanpath = os.path.join(
                self.envdabrender,self.envtype,self.envshow,self.envproject,"renderman",self.scenebasename)
        self.rendermanpathalias = "$DABRENDER/$TYPE/$SHOW/$PROJECT/renderman/$SCENENAME"
        self.renderdirectory = os.path.join(self.rendermanpath,"images")
        self.renderimagesalias  = "$DABRENDER/$TYPE/$SHOW/$PROJECT/renderman/$SCENENAME/images"
        self.mayaversion = mayaversion,
        self.rendermanversion = rendermanversion,
        self.envkey_rms = "rms-{}-maya-{}".format(self.rendermanversion[0], self.mayaversion[0])
        self.startframe = int(startframe)
        self.endframe = int(endframe)
        self.byframe = int(byframe)
        self.ribgenchunks = int(ribgenchunks)  # pixar jobs are one at a time
        self.projectgroup = projectgroup
        self.options = options
        self.email = email
        self.resolution = resolution
        self.outformat = outformat
        self.makeproxy = makeproxy
        self.skipframes = skipframes
        self.rendermaxsamples=rendermaxsamples
        self.threads=threads
        self.threadmemory=threadmemory
        self.mayaprojectname = os.path.basename(self.mayaprojectpath)
        self.finaloutputimages = "{finaloutputpath}/$SCENENAME.\\*.{ext}".format(
                finaloutputpath=self.rendermanpathalias,ext=self.outformat)
        self.renderimages = "{}/{}.\\*.{}".format(self.rendermanpathalias,self.scenebasename,self.outformat)
        self.ribpath = "{}/rib".format(self.rendermanpathalias)
        self.finaloutputimagebase = "{}/{}".format(self.rendermanpathalias,self.scenebasename)
        self.proxyoutput = "$DABRENDER/$TYPE/$SHOW/$PROJECT/movies/$SCENENAME_{}.mov".format("datehere")

    def build(self):
        """
        Main method to build the job
        """
        ########### TESTING ##############
        # _threadsM=4
        _threadsPixarRender=4
        _threads_RfMRibGen=1
        _servicePixarRender=_service_RfMRibGen=_serviceMaya=None

        if self.testing:
            _service_Testing="Testing"
            _tier="admin"

        else:
            _service_Testing=""
            _tier="batch"

        _servicePixarRender="PixarRender"
        _serviceMaya="PixarRender"
        _service_RfMRibGen="RfMRibGen"
        _service_NukeRender="NukeRender"

        #############################


        # ################ 0 JOB ################
        self.job = author.Job(title="Renderman: {} {} {}-{}".format(
              self.renderusername,self.scenename,self.startframe,self.endframe),
              priority=10,
              envkey=[self.envkey_rms,"ProjectX",
                    "TYPE={}".format(self.envtype),
                    "SHOW={}".format(self.envshow),
                    "PROJECT={}".format(self.envproject),
                    "SCENE={}".format(self.envscene),
                    "SCENENAME={}".format(self.scenebasename)],
              metadata="user={} username={} usernumber={}".format(
                      self.user, self.renderusername,self.renderusernumber),
              comment="LocalUser is {} {} {}".format(self.user,self.renderusername,self.renderusernumber),
              projects=[str(self.projectgroup)],
              tier=_tier,
              tags=["theWholeFarm",],
              service=_service_Testing)

        self.job.newDirMap("/dabrender", "/dabrender", "linux")
        self.job.newDirMap("/dabrender", "/Volumes/dabrender", "osx")
        self.job.newDirMap("/dabrender", "Z:", "windows")
        self.job.newDirMap("/Volumes/dabrender", "Z:", "windows")

        '''
        self.job.newDirMap("Z:","//Volumes/dabrender", "UNC")
        self.job.newDirMap("Z:","/Volumes/dabrender", "NFS")
         {{mayabatch} {maya} NFS}
         {{X:/} {//fileserver/projects/} UNC}
         {{X:/} {/fileserver/projects/} NFS}
         { { source } { destination } zone }
        '''


        # ############## 0 ThisJob #################
        task_thisjob = author.Task(title="Renderman Job")
        task_thisjob.serialsubtasks = 1

        # ############## 1 PREFLIGHT ##############
        task_preflight = author.Task(title="Preflight")
        task_preflight.serialsubtasks = 1
        task_thisjob.addChild(task_preflight)
        task_generate_rib_preflight = author.Task(title="Generate RIB Preflight")
        command_ribgen = author.Command(argv=["maya","-batch","-proj", utils.usedirmap(self.mayaprojectpath),
                                              "-command",
                                              "renderManBatchGenRibForLayer {layerid} {start} {end} {phase}".format(
                                                  layerid=0, start=self.startframe, end=self.endframe, phase=1),
                                              "-file", utils.usedirmap(self.mayascenefilefullpath)],
                                              tags=["maya", "rms", "theWholeFarm"],
                                              atleast=_threads_RfMRibGen,atmost=_threads_RfMRibGen,
                                              service=_service_RfMRibGen)
        task_generate_rib_preflight.addCommand(command_ribgen)
        task_preflight.addChild(task_generate_rib_preflight)
        task_render_preflight = author.Task(title="Render Preflight")

        command_render_preflight = author.Command(argv=[
                "prman","-t:{}".format(_threadsPixarRender), "-Progress", "-recover", "%r", "-checkpoint", "5m",
                "-cwd", utils.usedirmap(self.mayaprojectpath),
                "renderman/{}/rib/job/job.rib".format(self.scenebasename)],
                tags=["prman", "theWholeFarm"],
                atleast=_threadsPixarRender,atmost=_threadsPixarRender,
                service=_servicePixarRender)

        task_render_preflight.addCommand(command_render_preflight)
        task_preflight.addChild(task_render_preflight)

        # ############## 3 RIBGEN ##############
        task_render_allframes = author.Task(title="ALL FRAMES {}-{}".format(self.startframe, self.endframe))
        task_render_allframes.serialsubtasks = 1
        task_ribgen_allframes = author.Task(title="RIB GEN {}-{}".format(self.startframe, self.endframe))

        # divide the frame range up into chunks
        _totalframes=int(self.endframe-self.startframe+1)
        _chunks = int(self.ribgenchunks)
        _framesperchunk=_totalframes
        if _chunks < _totalframes:
            _framesperchunk=int(_totalframes/_chunks)
        else:
            _chunks=1

        # loop thru chunks
        for i,chunk in enumerate(range(1,_chunks+1)):
            _offset=i*_framesperchunk
            _chunkstart=(self.startframe+_offset)
            _chunkend=(_offset+_framesperchunk)
            logger.info("Chunk {} is frames {}-{}".format(chunk,_chunkstart,_chunkend))

            if chunk ==_chunks:
                _chunkend = self.endframe

            task_generate_rib = author.Task(title="RIB GEN chunk {} frames {}-{}".format(
                    chunk,_chunkstart, _chunkend ))
            command_generate_rib = author.Command(argv=[
                    "maya","-batch","-proj", utils.usedirmap(self.mayaprojectpath),"-command",
                    "renderManBatchGenRibForLayer {layerid} {start} {end} {phase}".format(
                            layerid=0, start=_chunkstart, end=_chunkend, phase=2),
                            "-file", utils.usedirmap(self.mayascenefilefullpath)],
                    tags=["maya", "rms", "theWholeFarm"],
                    atleast=int(_threads_RfMRibGen),atmost=int(_threads_RfMRibGen),
                    service=_service_RfMRibGen)
            task_generate_rib.addCommand(command_generate_rib)
            task_ribgen_allframes.addChild(task_generate_rib)

        task_render_allframes.addChild(task_ribgen_allframes)


        # ############### 4 RENDER ##############
        task_render_frames = author.Task(title="RENDER Frames {}-{}".format(self.startframe, self.endframe))
        task_render_frames.serialsubtasks = 0

        for frame in range(self.startframe, (self.endframe + 1),self.byframe):
            _shofile = utils.usedirmap("{proj}/{scenebase}.{frame:04d}.{ext}".format(
                proj=self.renderimagesalias, scenebase=self.scenebasename, frame=frame, ext=self.outformat))
            _imgfile = utils.usedirmap("{proj}/{scenebase}.{frame:04d}.{ext}".format(
                proj=self.finaloutputimagebase,scenebase=self.scenebasename, frame=frame, ext=self.outformat))
            _statsfile = utils.usedirmap("{proj}/rib/{frame:04d}/{frame:04d}.xml".format(
                proj=self.rendermanpath, frame=frame))
            _ribfile = utils.usedirmap("{proj}/rib/{frame:04d}/{frame:04d}.rib".format(
                proj=self.rendermanpath, frame=frame))

            task_render_rib = author.Task(title="RENDER Frame %s" % frame,preview="sho {}".format(_shofile),
                                          metadata="statsfile={} imgfile={}".format(_statsfile, _imgfile))
            commonargs = ["prman", "-cwd", utils.usedirmap(self.mayaprojectpath)]

            rendererspecificargs = []

            # ################ handle image resolution formats ###########
            if self.resolution == "720p":
                self.xres, self.yres = 1280, 720
                rendererspecificargs.extend(["-res", "%s" % self.xres, "%s" % self.yres])
            elif self.resolution == "1080p":
                self.xres, self.yres = 1920, 1080
                rendererspecificargs.extend(["-res", "%s" % self.xres, "%s" % self.yres])
            elif self.resolution == "540p":
                self.xres, self.yres = 960, 540
                rendererspecificargs.extend(["-res", "%s" % self.xres, "%s" % self.yres])
            elif self.resolution == "108p":
                self.xres, self.yres = 192, 108
                rendererspecificargs.extend(["-res", "%s" % self.xres, "%s" % self.yres])


            if self.rendermaxsamples != "FROMFILE":
                rendererspecificargs.extend([ "-maxsamples", "{}".format(self.rendermaxsamples) ])
            if self.threadmemory != "FROMFILE":
                rendererspecificargs.extend([ "-memorylimit", "{}".format(self.threadmemory) ])
            # if self.rendermaxsamples != "FROMFILE":
            #     rendererspecificargs.extend([ "-maxsamples", "{}".format(self.rendermaxsamples) ])
            # if self.threads != "FROMFILE":
            #     rendererspecificargs.extend([ "-maxsamples", "{}".format(self.rendermaxsamples) ])


            rendererspecificargs.extend([
                # "-pad", "4",
                # "-memorylimit", self.threadmemory,  # mb
                "-t:{}".format(self.threads),
                "-Progress",
                "-recover", "%r",
                "-checkpoint", "5m",
                "-statslevel", "2",
                # "-maxsamples", "{}".format(self.rendermaxsamples)  # override RIB ray trace hider maxsamples
                # "-pixelvariance","3"      # override RIB PixelVariance
                # "-d", ""                  # dispType
                #                 -version          : print the version
                # "-progress    ",     : print percent complete while rendering
                # -recover [0|1]    : resuming rendering partial frames
                # -t:X              : render using 'X' threads
                # -woff msgid,...   : suppress error messages from provided list
                # -catrib file      : write RIB to 'file' without rendering
                # -ascii            : write RIB to ASCII format file
                # -binary           : write RIB to Binary format file
                # -gzip             : compress output file
                # -capture file     : write RIB to 'file' while rendering
                # -nobake           : disallow re-render baking
                # -res x y[:par]    : override RIB Format
                # -crop xmin xmax ymin ymax
                #                   : override RIB CropWindow
                # -maxsamples i     : override RIB ray trace hider maxsamples
                # -pixelvariance f  : override RIB PixelVariance
                # -d dispType       : override RIB Display type
                # -statsfile f      : override RIB stats file & level (1)
                # -statslevel i     : override RIB stats level
                # -memorylimit f    : override RIB to set memory limit ratio
                # -checkpoint t[,t] : checkpoint interval and optional exit time
            ])
            userspecificargs = [
                utils.expandargumentstring(self.options),
                "{}".format(_ribfile)
            ]
            finalargs = commonargs + rendererspecificargs + userspecificargs
            command_render = author.Command(argv=finalargs,
                                            #envkey=[self.envkey_prman],
                                            tags=["prman", "theWholeFarm"],
                                            atleast=int(self.threads),
                                            atmost=int(self.threads),
                                            service=_servicePixarRender)

            task_render_rib.addCommand(command_render)
            task_render_frames.addChild(task_render_rib)

        task_render_allframes.addChild(task_render_frames)
        task_thisjob.addChild(task_render_allframes)


        # ############## 5 PROXY ###############
        # using nuke as exr colour is handled correctly

        if self.makeproxy:

            #### using the proxy_run.py script
            try:
                _directory = "{p}/renderman/{s}/images".format( p=self.mayaprojectpath, s=self.scenebasename)
                _nuke_envkey = "proxynuke{}".format(config.CurrentConfiguration().nukeversion)
                _proxy_runner_cmd = ["proxy_run.py","-s",_directory]

                task_proxy = author.Task(title="Proxy Generation", service=_service_NukeRender)
                nukecommand = author.Command(argv=_proxy_runner_cmd,
                                      service="NukeRender",
                                      tags=["nuke", "theWholeFarm"],
                                      envkey=[_nuke_envkey])
                task_proxy.addCommand(nukecommand)
                task_thisjob.addChild(task_proxy)
            except Exception, proxyerror:
                logger.warn("Cant make a proxy {}".format(proxyerror))


        # ############## 5 NOTIFY ###############
        logger.info("email = {}".format(self.email))
        task_notify = author.Task(title="Notify", service="Ffmpeg")
        task_notify.addCommand(self.mail("JOB", "COMPLETE", "email details still wip"))
        task_thisjob.addChild(task_notify)

        self.job.addChild(task_thisjob)


    def validate(self):
        logger.info("\n\n{:_^80}\n{}\n{:_^80}".format("snip", self.job.asTcl(), "snip"))

    def mail(self, level="Level", trigger="Trigger", body="Render Progress Body"):
        bodystring = "Prman Render Progress: \nLevel: {}\nTrigger: {}\n\n{}".format(level, trigger, body)
        subjectstring = "FARM JOB: %s %s" % (str(self.scenebasename), self.renderusername)
        mailcmd = author.Command(argv=["sendmail.py", "-t", "%s@uts.edu.au" % self.user,
                                       "-b", bodystring, "-s", subjectstring], service="Ffmpeg")
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
    logger.setLevel(logging.DEBUG)
    logger.info("START TESTING")

    TEST = RenderPrman(
                       envdabrender="/Volumes/dabrender",
                       envproject="testFarm",
                       envshow="matthewgidney",
                       envscene="dottyrms.ma",
                       envtype="user_work",
                       mayascenefilefullpath="/usr/local/tmp/scene/file.ma",
                       mayaprojectpath="/usr/local/tmp/",
                       mayaversion="2016",
                       rendermanversion="20.2",
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
                       threads="8",
                       ribgenchunks=3,
                       email=[1, 0, 0, 0, 1, 0]
    )
    TEST.build()
    TEST.validate()
    logger.info("FINISHED TESTING")





