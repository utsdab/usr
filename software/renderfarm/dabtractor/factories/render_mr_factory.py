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

author.setEngineClientParam(hostname="tractor-engine", port=5600, user="pixar", debug=True)

class RenderBase(object):
    """
    Base class for all batch jobs
    """

    def __init__(self):
        self.user = os.getenv("USER")
        self.spooljob = False
        self.testing = False

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


class RenderMentalray(RenderBase):

    """
    This is a maya batch mental ray

    Usage: Render [options] filename
           where "filename" is a Maya ASCII or a Maya binary file.

    Common options:
      -help              Print help
      -test              Print Mel commands but do not execute them
      -verb              Print Mel commands before they are executed
      -keepMel           Keep the temporary Mel file
      -listRenderers     List all available renderers
      -renderer string   Use this specific renderer
      -r string          Same as -renderer
      -proj string       Use this Maya project to load the file
      -log string        Save output into the given file

    Specific options for renderer "mr": Mentalray renderer

    General purpose flags:
      -rd path                    Directory in which to store image files
      -im filename                Image file output name
      -of string                  Output image file format. See the Render Settings window
            to find available formats

    Frame numbering options
      -s float                    Starting frame for an animation sequence
      -e float                    End frame for an animation sequence
      -b float                    By frame (or step) for an animation sequence
      -skipExistingFrames boolean Skip frames that are already rendered (if true) or force rendering all frames (if false)
      -pad int                    Number of digits in the output image frame file name
            extension
      -rfs int                    Renumber Frame Start: number for the first image when
            renumbering frames
      -rfb int                    Renumber Frame By (or step) used for renumbering frames
      -fnc int                    File Name Convention: any of name, name.ext, ... See the
            Render Settings window to find available options. Use namec and
            namec.ext for Multi Frame Concatenated formats. As a shortcut,
            numbers 1, 2, ... can also be used
      -perframe                   Renders animation per-frame, without incremental change

    Camera options
      -cam name                   Specify which camera to be rendered
      -rgb boolean                Turn RGB output on or off
      -alpha boolean              Turn Alpha output on or off
      -depth boolean              Turn Depth output on or off
      -iip                        Ignore Image Planes. Turn off all image planes before
            rendering

    Resolution options
      -x int                      Set X resolution of the final image
      -y int                      Set Y resolution of the final image
      -percentRes float           Renders the image using percent of the resolution
      -ard float                  Device aspect ratio for the rendered image
      -par float                  Pixel aspect ratio for the rendered image

    Render Layers and Passes:
      -rl boolean|name(s)         Render each render layer separately
      -rp boolean|name(s)         Render passes separately. 'all' will render all passes
      -sel boolean|name(s)        Selects which objects, groups and/or sets to render
      -l boolean|name(s)          Selects which display and render layers to render
      -rat/allRenderable          Render all renderable (2D and 3D)
      -rto/renderTargetsOnly      Render target (2D) only rendering
      -ort/omitRenderTargets      Omit render targets and render 3D only

    Mel callbacks
      -preRender string           Mel code executed before rendering
      -postRender string          Mel code executed after rendering
      -preLayer string            Mel code executed before each render layer
      -postLayer string           Mel code executed after each render layer
      -preFrame string            Mel code executed before each frame
      -postFrame string           Mel code executed after each frame
      -pre string                 Obsolete flag
      -post string                Obsolete flag

    Other:
      -v/verbose int              Set the verbosity level.
            0 to turn off messages
            1 for fatal errors only
            2 for all errors
            3 for warnings
            4 for informational messages
            5 for progress messages
            6 for detailed debugging messages
      -rt/renderThreads int       Specify the number of rendering threads.
      -art/autoRenderThreads      Automatically determine the number of rendering threads.
      -mem/memory int             Set the memory limit (in MB).
      -aml/autoMemoryLimit        Compute the memory limit automatically.
      -ts/taskSize int            Set the pixel width/height of the render tiles.
      -at/autoTiling              Automatically determine optimal tile size.
      -fbm/frameBufferMode int    Set the frame buffer mode.
            0 in-memory framebuffers
            1 memory mapped framebuffers
            2 cached framebuffers
      -rnm boolean                Network rendering option. If true, mental ray renders
            almost everything on slave machines, thus reducing the workload on the
            master machine
      -lic string                 Specify satellite licensing option. mu/unlimited or
            mc/complete.
      -reg int int int int        Set sub-region pixel boundary of the final image:
            left, right, bottom, top
      -sa/sampling int            Render the scene using the legacy sampling scheme.
            0 Unified Sampling Mode
            1 Legacy Rasterizer Mode
            2 Legacy Sampling Mode
      -uq/unifiedQuality float    Set the Unified Sampling quality (only meaningful when using the Unified Sampling mode).
     *** Remember to place a space between option flags and their arguments. ***
    Any boolean flag will take the following values as TRUE: on, yes, true, or 1.
    Any boolean flag will take the following values as FALSE: off, no, false, or 0.

        e.g. -s 1 -e 10 -x 512 -y 512 -cam persp -of jpg file.

    """

    def __init__(self,
                 envdabrender="",
                 envtype="",        # user_work
                 envshow="",        # matthewgidney
                 envproject="",     # mayaproject
                 envscene="",       # mayascenename - noextension ### not needed
                 mayaprojectpath="",    # /Users/Shared/UTS_Dev/dabrender/user_work/matthewgidney/matt_maya_project
                 mayascenerelpath="", # scene/mayascene.ma
                 mayascenefilefullpath="", ####### not needed
                 mayaversion="2016",
                 startframe=1,
                 endframe=10,
                 byframe=1,
                 framechunks=5,
                 projectgroup="yr1",
                 threads = 4,
                 threadmemory = 4000,
                 renderer="mr",
                 outformat="exr",
                 resolution="540p",
                 skipframes=0,
                 makeproxy=0,
                 options="",
                 email=[1,0,0,0,1,0]
        ):

        super(RenderMentalray, self).__init__()

        self.envdabrender = envdabrender
        self.envtype=envtype
        self.envproject=envproject
        self.envshow=envshow
        self.envscene=envscene

        self.mayaprojectpathalias       = "$DABRENDER/$TYPE/$SHOW/$PROJECT"
        self.mayaprojectpath = os.path.join(self.envdabrender,self.envtype,
                                            self.envshow,self.envproject)
        self.mayaprojectnamealias       = "$PROJECT"
        self.mayaprojectname = envproject
        self.mayascenefilefullpathalias = "$DABRENDER/$TYPE/$SHOW/$PROJECT/$SCENE"
        self.mayascenefilefullpath = os.path.join(self.envdabrender,self.envtype,self.envshow,
                                                  self.envproject,self.envscene)
        self.scenename = os.path.split(envscene)[-1:][0]
        self.scenebasename = os.path.splitext(self.scenename)[0]
        self.sceneext = os.path.splitext(self.scenename)[1]

        self.mayaversion = mayaversion
        self.envkey_maya="maya{}".format(self.mayaversion)

        self.startframe = int(startframe)
        self.endframe = int(endframe)
        self.byframe = int(byframe)

        self.framechunks = int(framechunks)
        self.renderer = renderer
        if self.renderer == 'mr':
            self.renderername = 'Mental Ray Render'
        elif self.renderer == 'sw':
            self.renderername = 'Maya Render'
        else:
            self.renderername = 'Render'

        self.projectgroup = projectgroup
        self.options = options
        self.email = email
        self.resolution = resolution
        self.outformat = outformat
        self.makeproxy = makeproxy
        self.skipframes = skipframes
        self.threads=threads
        self.threadmemory=threadmemory
        self.sourcetargetsame = False
        self.mayascenepath = os.path.dirname(self.mayascenefilefullpath)
        self.mayascenename = os.path.basename(self.mayascenefilefullpath)
        self.mayascenenamebase = os.path.splitext(self.mayascenename)[0]
        self.mayascenenameext = os.path.splitext(self.mayascenename)[1]
        self.renderdirectory = "images"
        self.environmentkey = 'maya{}'.format(self.mayaversion)

        self.finaloutputpath = "{work}/{proj}/{images}/{scene}".format(
            work=self.dabrenderworkpath,
            proj=self.mayaprojectname,
            scene=self.mayascenenamebase,
            images=self.renderdirectory)
        self.finaloutputimages = "{finaloutputpath}/{scene}.\\*.{ext}".format(
            finaloutputpath=self.finaloutputpath,
            scene=self.mayascenenamebase,
            ext=self.outformat)
        self.proxyoutput = "{work}/{proj}/movies/{scene}.{ext}".format(
            work=self.dabrenderworkpath,
            proj=self.mayaprojectname,
            scene=self.mayascenenamebase,
            ext="mov")

    def build(self):
        """
        Main method to build the job
        """
        ########### TESTING ##############
        # _threadsM=4
        _threadsPixarRender=4
        _threads_RfMRibGen=4
        _threadsMaya=4
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
        self.job = author.Job(title="MentalRay: {} {} {}-{}".format(self.renderusername,
                                                                     self.scenename,self.startframe,self.endframe),
                              priority=10,
                              envkey=[self.envkey_maya,"ProjectX",
                                    "TYPE={}".format(self.envtype),
                                    "SHOW={}".format(self.envshow),
                                    "PROJECT={}".format(self.envproject),
                                    "SCENE={}".format(self.envscene),
                                    "SCENENAME={}".format(self.scenebasename)],
                              metadata="user={} username={} usernumber={}".format(self.user, self.renderusername,
                                                                                  self.renderusernumber),
                              comment="LocalUser is {} {} {}".format(self.user,
                                                                     self.renderusername,
                                                                     self.renderusernumber),
                              projects=[str(self.projectgroup)],

                              tier=_tier,
                              tags=[
                                     "theWholeFarm",
                                    ],
                              service=_service_Testing)

        self.job.newDirMap("/dabrender", "/Volumes/dabrender", "linux")
        self.job.newDirMap("/dabrender", "/Volumes/dabrender", "osx")
        self.job.newDirMap("/dabrender", "Z:", "windows")
        self.job.newDirMap("/Volumes/dabrender", "Z:", "windows")
        # self.job.newDirMap("Z:","//Volumes/dabrender", "UNC")
        # self.job.newDirMap("Z:","/Volumes/dabrender", "NFS")


        # ############## PARENT #################
        task_thisjob = author.Task(title="Maya Render Job", service="MayaMentalRay")
        task_thisjob.serialsubtasks = 1


        # ############## 1 PREFLIGHT ##############


        # ############## 3 RENDER ##############
        task_render = author.Task(title="Rendering",service="MayaMentalRay")
        task_render.serialsubtasks = 0

        if (self.endframe - self.startframe) < self.framechunks:
            self.framechunks = 1
            _chunkend = self.endframe
        else:
            _chunkend = self.startframe + self.framechunks

        _chunkstart = self.startframe

        while self.endframe >= _chunkstart:
            if _chunkend >= self.endframe:
                _chunkend = self.endframe

            t1 = "{}  {}-{}".format(self.renderername,_chunkstart, _chunkend)
            thischunk = author.Task(title=t1,
                                    service="MayaMentalRay")

            commonargs = [
                "Render",
                "-r", self.renderer,
                "-proj", self.mayaprojectpath,
                "-s", "{}".format(_chunkstart),
                "-e", "{}".format(_chunkend),
                "-b", self.byframe,
                "-rd", self.finaloutputpath,
                "-rt", self.threads,
                "-mem", self.threadmemory,
                "-im", self.mayascenenamebase,  # this is the name bit of below
                "-fnc", "3"  # this means name.#.ext
            ]

            rendererspecificargs = []

            if self.resolution == "720p":
                self.xres, self.yres = 1280, 720
                rendererspecificargs.extend(["-x", "%s" % self.xres])
                rendererspecificargs.extend(["-y", "%s" % self.yres])
                rendererspecificargs.extend(["-ard", "1.778"])
            elif self.resolution == "1080p":
                self.xres, self.yres = 1920, 1080
                rendererspecificargs.extend(["-x", "%s" % self.xres])
                rendererspecificargs.extend(["-y", "%s" % self.yres])
                rendererspecificargs.extend(["-ard", "1.778"])
            elif self.resolution == "540p":
                self.xres, self.yres = 960, 540
                rendererspecificargs.extend(["-x", "%s" % self.xres])
                rendererspecificargs.extend(["-y", "%s" % self.yres])
                rendererspecificargs.extend(["-ard", "1.778"])
            elif self.resolution == "108p":
                self.xres, self.yres = 192, 108
                rendererspecificargs.extend(["-x", "%s" % self.xres])
                rendererspecificargs.extend(["-y", "%s" % self.yres])
                rendererspecificargs.extend(["-ard", "1.778"])
            else:
                # dont define the resolutions or aspect - so use what is the file
                pass

            rendererspecificargs.extend([
                "-mem", "4000",
                "-v", "4",
                "-pad", "4",
                #"-of", "%s" % self.outformat,
                # the -of flag is fawlty for setting exr
                "-skipExistingFrames", "%s" % self.skipframes])

            userspecificargs = [
                utils.expandargumentstring(self.options),
                self.mayascenefilefullpath
            ]

            finalargs = commonargs + rendererspecificargs + userspecificargs
            render = author.Command(argv=finalargs,
                                    service="MayaMentalRay",
                                    tags=["maya", "theWholeFarm"],
                                    atmost=int(self.threads),
                                    atleast=int(self.threads),
                                    envkey=["maya{}".format(self.mayaversion)]
                                    )
            # thischunk.addCommand(env)
            thischunk.addCommand(render)
            _chunkstart = _chunkend + 1
            _chunkend += self.framechunks
            task_render.addChild(thischunk)

        task_thisjob.addChild(task_render)

        # ############## 4 PROXY ###############
        # using nuke as exr colour is handled correctly

        if self.makeproxy:

            #### using the proxy_run.py script
            try:
                _directory = "{p}/images/{s}".format( p=self.mayaprojectpath, s=self.mayascenenamebase)
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


        # ############## 7 NOTIFY ###############
        task_notify = author.Task(title="Notify")
        email = author.Command(self.mail("JOB", "COMPLETE", "blah"), service="ShellServices")
        task_notify.addCommand(email)
        logger.info("email = {}".format(self.email))
        """
        window.emailjob.get(),
        window.emailtasks.get(),
        window.emailcommands.get(),
        window.emailstart.get(),
        window.emailcompletion.get(),
        window.emailerror.get()
        """
        task_notify = author.Task(title="Notify", service="ShellServices")
        task_notify.addCommand(self.mail("JOB", "COMPLETE", "blah"))
        task_thisjob.addChild(task_notify)
        self.job.addChild(task_thisjob)

    def validate(self):
        logger.info("\n\n{:_^80}\n{}\n{:_^80}".format("snip", self.job.asTcl(), "snip"))

    def mail(self, level="Level", trigger="Trigger", body="Render Progress Body"):
        bodystring = "{}  Progress: \nLevel: {}\nTrigger: {}\n\n{}".format(self.renderername,level,
                                                                                         trigger,
                                                                                         body)
        subjectstring = "FARM JOB: %s %s" % (str(self.mayascenenamebase), self.renderusername)
        mailcmd = author.Command(argv=["sendmail.py", "-t", "%s@uts.edu.au" % self.user,
                                       "-b", bodystring, "-s", subjectstring], service="ShellServices")
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


class RenderMayaSW(RenderBase):
    '''Specific options for renderer "sw": Maya software renderer

    General purpose flags:
      -rd path                    Directory in which to store image files
      -im filename                Image file output name
      -fnc int                    File Name Convention: any of name, name.ext, ... See the
            Render Settings window to find available options. Use namec and
            namec.ext for Multi Frame Concatenated formats. As a shortcut,
            numbers 1, 2, ... can also be used
      -of string                  Output image file format. See the Render Settings window
            to find available formats

      -s float                    Starting frame for an animation sequence
      -e float                    End frame for an animation sequence
      -b float                    By frame (or step) for an animation sequence
      -skipExistingFrames boolean Skip frames that are already rendered (if true) or force rendering all frames (if false)
      -pad int                    Number of digits in the output image frame file name
            extension
      -rfs int                    Renumber Frame Start: number for the first image when
            renumbering frames
      -rfb int                    Renumber Frame By: step used for renumbering frames
      -se int                     Obsolete flag identical to -rfs. Used only for backward
            compatibility
      -be int                     Obsolete flag identical to -rfe. Used only for backward
            compatibility

      -cam name                   Specify which camera to be rendered
      -rgb boolean                Turn RGB output on or off
      -alpha boolean              Turn Alpha output on or off
      -depth boolean              Turn Depth output on or off
      -iip                        Ignore Image Planes turn off all image planes before
            rendering

      -x int                      Set X resolution of the final image
      -y int                      Set Y resolution of the final image
      -percentRes float           Renders the image using percent of the resolution
      -ard float                  Device aspect ratio for the rendered image
      -par float                  Pixel aspect ratio for the rendered image

    More advanced flags:

    Anti-aliasing quality:
      -eaa int                    The anti-aliasing quality of EAS (Abuffer). One of:
            highest(0), high(1), medium(2), low(3)
      -ss int                     Global number of shading samples per surface in a pixel
      -mss int                    Maximum number of adaptive shading samples per surface
            in a pixel
      -mvs int                    Number of motion blur visibility samples
      -mvm int                    Maximum number of motion blur visibility samples
      -pss int                    Number of particle visibility samples
      -vs int                     Global number of volume shading samples
      -ufil boolean               If true, use the multi-pixel filtering; otherwise use
            single pixel filtering
      -pft int                    When useFilter is true, identifies one of the following
            filters: box(0), triangle(2), gaussian(4), quadratic(5)
      -pfx float                  When useFilter is true, defines the X size of the filter
      -pfy float                  When useFilter is true, defines the Y size of the filter
      -rct float                  Red channel contrast threshold
      -gct float                  Green channel contrast threshold
      -bct float                  Blue channel contrast threshold
      -cct float                  Pixel coverage contrast threshold (default is 1.0/8.0)

    Raytracing quality:
      -ert boolean                Enable ray tracing
      -rfl int                    Maximum ray-tracing reflection level
      -rfr int                    Maximum ray-tracing refraction level
      -sl int                     Maximum ray-tracing shadow ray depth

    Field Options:
      -field boolean              Enable field rendering. When on, images are interlaced
      -pal                        When field rendering is enabled, render even field
            first (PAL)
      -ntsc                       When field rendering is enabled, render odd field
            first (NTSC)

    Motion Blur:
      -mb boolean                 Motion blur on/off
      -mbf float                  Motion blur by frame
      -sa float                   Shutter angle for motion blur (1-360)
      -mb2d boolean               Motion blur 2D on/off
      -bll float                  2D motion blur blur length
      -bls float                  2D motion blur blur sharpness
      -smv int                    2D motion blur smooth value
      -smc boolean                2D motion blur smooth color on/off
      -kmv boolean                Keep motion vector for 2D motion blur on/off

    Render Options:
      -ifg boolean                Use the film gate for rendering if false
      -edm boolean                Enable depth map usage
      -g float                    Gamma value
      -premul boolean             Premultiply color by the alpha value
      -premulthr float            When premultiply is on, defines the threshold used to
            determine whether to premultiply or not

    Memory and Performance:
      -uf boolean                 Use the tessellation file cache
      -oi boolean                 Dynamically detects similarly tessellated surfaces
      -rut boolean                Reuse render geometry to generate depth maps
      -udb boolean                Use the displacement bounding box scale to optimize
            displacement-map performance
      -mm int                     Renderer maximum memory use (in Megabytes)

    Render Layers and Passes:
      -rl boolean|name(s)         Render each render layer separately
      -rp boolean|name(s)         Render passes separately. 'all' will render all passes
      -rs boolean                 Obsolete flag. Used only for backward compatibility
      -sel boolean|name(s)        Selects which objects, groups and/or sets to render
      -l boolean|name(s)          Selects which display and render layers to render

    Mel callbacks
      -preRender string           Mel code executed before rendering
      -postRender string          Mel code executed after rendering
      -preLayer string            Mel code executed before each render layer
      -postLayer string           Mel code executed after each render layer
      -preFrame string            Mel code executed before each frame
      -postFrame string           Mel code executed after each frame
      -pre string                 Obsolete flag
      -post string                Obsolete flag

    Other:
      -rep boolean                Do not replace the rendered image if it already exists
      -reg int int int int        Set sub-region pixel boundary of the final image:
            left, right, bottom, top
      -n int                      Number of processors to use (0 indicates use all
            available)
      -mf boolean                 Append image file format to image name if true
      -sp boolean                 Generate shadow depth maps only
      -amt boolean                Abort renderer when encountered missing texture
      -ipr boolean                Create an IPR file
      -keepPreImage boolean       Keep the renderings prior to post-process around

    *** Remember to put a space between option flags and their arguments. ***
    Any boolean flag will take the following values as TRUE: on, yes, true, or 1.
    Any boolean flag will take the following values as FALSE: off, no, false, or 0.

        e.g. -x 512 -y 512 -cam persp -im test -of jpg -mb on -sa 180 file
    '''

    def __init__(self):
        pass


if __name__ == "__main__":
    ## as rmanpy has no unit testing - this is a substitute

    logger.setLevel(logging.DEBUG)
    logger.info("START TESTING")
    TEST = RenderMentalray( mayascenefilefullpath="/usr/local/tmp/scene/file.ma",
                           mayaprojectpath="/usr/local/tmp",
                           mayaversion="2016",
                           startframe=1,
                           endframe=4,
                           byframe=1,
                           framechunks=1,
                           renderer="mr",
                           outformat="exr",
                           resolution="540p",
                           threads=4,
                           threadmemory=4000,
                           options="",
                           skipframes=0,
                           makeproxy=0,
                           email=[0,0,0,0,0,0]
        )
    TEST.build()
    TEST.validate()
    logger.info("FINISHED TESTING")





