#!/usr/bin/env rmanpy
"""
To do:
    find commonality in render jobs and put it in base class

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


class RenderBase(object):
    """
    Base class for all batch jobs
    """

    def __init__(self):
        self.user = os.getenv("USER")
        self.spooljob = False
        self.job = ""

        try:
            # get the names of the central render location for the user
            ru = ufac.Student()
            self.renderusernumber = ru.number
            self.renderusername = ru.name
            self.dabrender = ru.dabrender
            self.dabrenderworkpath = ru.dabrenderwork
            self.initialProjectPath = ru.dabrenderwork

        except Exception, erroruser:
            logger.warn("Cant get the users name and number back %s" % erroruser)
            sys.exit("Cant get the users name")

        if os.path.ismount(self.dabrender):
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
                 envtype="",
                 envshow="",
                 envproject="",
                 envscene="",
                 mayaprojectpath="",
                 mayascenefilefullpath="",
                 mayaversion="",
                 rendermanversion="",
                 startframe=1,
                 endframe=10,
                 byframe=1,
                 projectgroup="",
                 outformat="",
                 resolution="",
                 skipframes=0,
                 makeproxy=0,
                 options="",
                 rendermemory="",
                 renderthreads="",
                 rendermaxsamples="",
                 ribgenchunks="",
                 email=[]
    ):

        super(RenderPrman, self).__init__()
        self.mayaprojectpath = "$DABRENDERPATH/$TYPE/$SHOW/$PROJECT"
        self.mayaprojectname = "$PROJECT"
        self.mayascenefilefullpath = "$DABRENDERPATH/$TYPE/$SHOW/$PROJECT/scenes/$SCENE"
        self.mayaversion = mayaversion,
        self.rendermanversion = rendermanversion,
        self.envkey_rms = "rms-{}-maya-{}".format(self.rendermanversion[0], self.mayaversion[0])
        self.startframe = startframe
        self.endframe = endframe
        self.byframe = byframe
        self.framechunks = 1  # prman jobs are one at a time
        self.projectgroup = projectgroup
        self.options = options
        self.email = email
        self.resolution = resolution
        self.outformat = outformat
        self.makeproxy = makeproxy
        self.skipframes = skipframes
        self.envtype= envtype
        self.envshow=envshow
        self.envproject=envproject
        self.envscene=envscene
        self.rendermaxsamples=rendermaxsamples
        self.renderthreads=renderthreads
        self.rendermemory=rendermemory
        self.sourcetargetsame = False
        self.mayaprojectname = os.path.basename(self.mayaprojectpath)
        self.mayascenepath = "$DABRENDERPATH/$TYPE/$SHOW/$PROJECT/scenes/$SCENE"
        self.mayascenename = "$SCENE"
        self.mayascenenamebase = os.path.splitext(self.mayascenename)[0]
        self.mayascenenameext = os.path.splitext(self.mayascenename)[1]
        self.renderdirectory = "renderman/$SCENE/images"
        self.imageoutputpath = "$DABRENDERPATH/$TYPE/$SHOW/$PROJECT/renderman/$SCENE/images"
        self.finaloutputimages = "{finaloutputpath}/{scene}.\\*.{ext}".format(
            finaloutputpath=self.imageoutputpath,
            scene=self.mayascenenamebase,
            ext=self.outformat)
        self.ribpath = "$DABRENDERPATH/$TYPE/$SHOW/$PROJECT/renderman/$SCENE/rib".format(
            work=self.dabrenderworkpath,
            proj=self.mayaprojectname,
            scene=self.mayascenenamebase)
        self.finaloutputimagebase = "{finaloutputpath}/{scene}".format(
            finaloutputpath=self.imageoutputpath,
            scene=self.mayascenenamebase)
        self.proxyoutput = "$DABRENDERPATH/$TYPE/$SHOW/$PROJECT/movies/$SCENE_{}.mov".format("datehere")

    def build(self):
        """
        Main method to build the job
        """

        # ################ 0 JOB ################
        self.job = author.Job(title="Prman Render Job: {} {}".format(self.renderusername,
                                                                     self.mayascenename),
                              priority=10,
                              envkey=[self.envkey_rms],
                              metadata="user={} username={} usernumber={}".format(self.user, self.renderusername,
                                                                                  self.renderusernumber),
                              comment="LocalUser is {} {} {}".format(self.user,
                                                                     self.renderusername,
                                                                     self.renderusernumber),
                              projects=[self.projectgroup],
                              tier="batch",
                              tags=["theWholeFarm","ProjectX",
                                    "TYPE={}".format(self.envtype),
                                    "SHOW={}".format(self.envshow),
                                    "PROJECT={}".format(self.envproject),
                                    "SCENE={}".format(self.envscene),
                                    ],
                              service="")


        # ############## 0 ThisJob #################
        task_thisjob = author.Task(title="Renderman Job")
        task_thisjob.serialsubtasks = 1

        # ############## 1 PREFLIGHT ##############
        task_preflight = author.Task(title="Preflight")
        task_preflight.serialsubtasks = 1
        task_thisjob.addChild(task_preflight)
        task_generate_rib_preflight = author.Task(title="Generate RIB Preflight")
        command_ribgen = author.Command(argv=["maya",
                                              "-batch",
                                              "-proj", self.mayaprojectpath,
                                              "-command",
                                              "renderManBatchGenRibForLayer {layerid} {start} {end} {phase}".format(
                                                  layerid=0, start=self.startframe, end=self.endframe, phase=1),
                                              "-file", self.mayascenefilefullpath],
                                              tags=["maya", "rms", "theWholeFarm"],
                                              atleast=int(self.renderthreads),
                                              atmost=int(self.renderthreads),
                                              service="RfMRibGen")
        task_generate_rib_preflight.addCommand(command_ribgen)
        task_preflight.addChild(task_generate_rib_preflight)
        task_render_preflight = author.Task(title="Render Preflight")
        command_render_preflight = author.Command(argv=["prman",
                                                        "-t:2",
                                                        "-Progress", "-recover", "%r", "-checkpoint", "5m",
                                                        "-cwd", "$DABRENDERPATH/$TYPE/$SHOW/$PROJECT",
                                                        "renderman/{scene}/rib/job/job.rib".format(
                                                            scene=self.mayascenenamebase)],
                                                  tags=["prman", "theWholeFarm"],
                                                  atleast=int(self.renderthreads),
                                                  atmost=int(self.renderthreads),
                                                  service="PixarRender")

        task_render_preflight.addCommand(command_render_preflight)
        task_preflight.addChild(task_render_preflight)

        # ############## 3 RENDER ##############
        task_render_allframes = author.Task(title="Frames {}-{}".format(self.startframe, self.endframe))
        task_render_allframes.serialsubtasks = 1
        task_generate_rib = author.Task(title="Generate RIB {}-{}".format(self.startframe, self.endframe))
        command_generate_rib = author.Command(argv=["maya",
                                                    "-batch",
                                                    "-proj", self.mayaprojectpath, "-command",
                                                    "renderManBatchGenRibForLayer {layerid} {start} {end} {phase}".format(
                                                        layerid=0, start=self.startframe, end=self.endframe, phase=2),
                                                    "-file", self.mayascenefilefullpath],
                                              tags=["maya", "rms", "theWholeFarm"],
                                              atleast=int(self.renderthreads),
                                              atmost=int(self.renderthreads),
                                              service="RfMRibGen")

        task_generate_rib.addCommand(command_generate_rib)
        task_render_allframes.addChild(task_generate_rib)
        task_render_frames = author.Task(title="Render Frames {}-{}".format(self.startframe, self.endframe))
        task_render_frames.serialsubtasks = 0

        for frame in range(self.startframe, (self.endframe + 1),self.byframe):
            _shofile = "{proj}/renderman/{scene}/images/{scene}.{frame:04d}.{ext}".format(
                proj=self.mayaprojectpath, scene=self.mayascenenamebase, frame=frame, ext=self.outformat)
            _imgfile = "{proj}/renderman/{scene}/images/{scene}.{frame:04d}.{ext}".format(
                proj=self.mayaprojectpath, scene=self.mayascenenamebase, frame=frame, ext=self.outformat)
            _statsfile = "{proj}/renderman/{scene}/rib/{frame:04d}/{frame:04d}.xml".format(
                proj=self.mayaprojectpath, scene=self.mayascenenamebase, frame=frame)
            _ribfile = "{proj}/renderman/{scene}/rib/{frame:04d}/{frame:04d}.rib".format(
                proj="$DABRENDERPATH/$TYPE/$SHOW/$PROJECT", scene=self.mayascenenamebase, frame=frame)

            task_render_rib = author.Task(title="Render Frame %s" % frame,
                                          preview="sho {}".format(_shofile),

                                          metadata="statsfile={} imgfile={}".format(_statsfile, _imgfile))

            commonargs = ["prman", "-cwd", self.mayaprojectpath]

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
            else:
                # dont define the resolutions or aspect - so use what is the file
                pass

            rendererspecificargs.extend([
                # "-pad", "4",
                "-memorylimit", self.rendermemory,  # mb
                "-t:{}".format(self.renderthreads), "-Progress",
                "-recover", "%r",
                "-checkpoint", "5m",
                "-statslevel", "2",
                "-maxsamples", "{}".format(self.rendermaxsamples)  # override RIB ray trace hider maxsamples
                # "-pixelvariance","3"      # override RIB PixelVariance
                # "-d", ""                  # dispType
                #                 -version          : print the version
                # -progress         : print percent complete while rendering
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
                                            atleast=int(self.renderthreads),
                                            atmost=int(self.renderthreads),
                                            service="PixarRender")

            task_render_rib.addCommand(command_render)
            task_render_frames.addChild(task_render_rib)

        task_render_allframes.addChild(task_render_frames)
        task_thisjob.addChild(task_render_allframes)


        # ############## 4 PROXY ###############
        # using nuke as exr colour is handled correctly

        if self.makeproxy:

            #### using the proxy_run.py script
            try:
                _directory = "{p}/renderman/{s}/images".format( p=self.mayaprojectpath, s=self.mayascenenamebase)
                _nuke_envkey = "proxynuke{}".format(config.CurrentConfiguration().nukeversion)
                _proxy_runner_cmd = ["proxy_run.py","-s",_directory]

                task_proxy = author.Task(title="Proxy Generation", service="NukeRender")
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
        subjectstring = "FARM JOB: %s %s" % (str(self.mayascenenamebase), self.renderusername)
        mailcmd = author.Command(argv=["sendmail.py", "-t", "%s@uts.edu.au" % self.user,
                                       "-b", bodystring, "-s", subjectstring], service="Ffmpeg")
        return mailcmd

    def spool(self):
        if os.path.exists(self.mayascenefilefullpath):

            try:
                logger.info("Spooled correctly")
                # all jobs owner by pixar user on the farm
                self.job.spool(owner="pixar")
            except Exception, spoolerr:
                logger.warn("A spool error %s" % spoolerr)
        else:
            message = "Maya scene file non existant %s" % self.mayascenefilefullpath
            logger.critical(message)
            sys.exit(message)


# ##############################################################################

if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    logger.info("START TESTING")

    TEST = RenderPrman(
                       envproject="testFarm",
                       envshow="matthewgidney",
                       envscene="dottyrms.ma",
                       envtype="work",
                       mayascenefilefullpath="/usr/local/tmp/scene/file.ma",
                       mayaprojectpath="/usr/local/tmp/",
                       mayaversion="2016",
                       rendermanversion="20.2",
                       startframe=1,
                       endframe=1,
                       byframe=1,
                       outformat="exr",
                       resolution="540p",
                       options="",
                       skipframes=1,
                       makeproxy=1,
                       rendermemory="4000",
                       rendermaxsamples="128",
                       renderthreads="8",
                       email=[1, 0, 0, 0, 1, 0]
    )
    TEST.build()
    TEST.validate()
    logger.info("FINISHED TESTING")





