#!/usr/bin/env rmanpy
"""
    Using Tractors internal version of python - rmanpy
    This file is for testing jobs to build.
    It should be broken ouy into two files,
    One a command line script that takes all the necessary args which may be a master that calls upon a factory of
    render class objects.
    Then one a UI that wraps the first command line script. Initially this will be a simple tkinter script then
    should become a sexier pyside/qt version - all these modules should be within the python dabtractor distro.

"""

import dabtractor.api.author as author
import os
import sys
import platform


def usedirmap(input):
    # %D(mayabatch)
    return '%D({thing})'.format(thing=input)


thisfile = os.path.basename(__file__)
localuser = os.getenv("USER") 
proj = "/Volumes/dabrender/120988_matthewgidney/testFarm"
scenefile = "mr_dotty_test.ma"

scene, ext = os.path.splitext(scenefile)

by = 2
start = 1
end = 300
imageextension = "exr"
finalOutputImages = usedirmap("{}/images/{}/{}.\%04d.{}".format(proj, scene, scene, imageextension))
proxyOutput = usedirmap("{}/images/{}.{}".format(proj, scene, "mov"))

# cmdpath = usedirmap("/usr/autodesk/maya2015-x64/bin/Render")
cmdpath = "Render"

renderdirectory = usedirmap("%s/images/%s" % (proj, scene))
renderscene = usedirmap("%s/scenes/%s" % (proj, scenefile))
renderproject = usedirmap("%s" % proj)

author.setEngineClientParam(hostname="dabtractor-engine", port=5600, user="mattg", debug=True)

job = author.Job(title = thisfile,
                 priority=100,
                 envkey=["maya2015"],
		         metadata=localuser,
	             comment="LocalUser is %s"%localuser,
                 service="MayaMentalRay")

dirmap1 = job.newDirMap("/Volumes/dabrender", "/dabrender", "linux")
dirmap2 = job.newDirMap("/dabrender", "/Volumes/dabrender", "osx")

parent = author.Task(title="Parent", service="MayaMentalRay")
parent.serialsubtasks = 1

preflight = author.Task(title="Make Image Directory",
                        service="MayaMentalRay")
makedirectory = author.Command(argv=["mkdir", "-p", "%s" % (renderdirectory)])
environment = author.Command(argv=["printenv"])

preflight.addCommand(environment)
preflight.addCommand(makedirectory)
parent.addChild(preflight)

rendering = author.Task(title="Maya Rendering", argv=[], service="MayaMentalRay")
rendering.serialsubtasks = 0

# loop throught the batch logic  for *********** Render -r mr **************
"""
Usage: ./Render [options] filename
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

for chunk in range(start, end, by):
    t1 = "Mental Ray Render %s-%s" % (chunk, chunk + by - 1)
    thischunk = author.Task(title=t1, service="MayaMentalRay")

    rarg = ["%s" % cmdpath]  # Main command - typically it is Render
    rarg.append("-x")  # output image height
    rarg.append("1280")
    rarg.append("-y")  # output image width
    rarg.append("720")
    rarg.append("-ard")  # output image aspect ratio
    rarg.append("1.778")
    rarg.append("-of")  # output file format
    rarg.append("exr")
    rarg.append("-s")  # output start frame
    rarg.append("%s" % chunk)
    rarg.append("-e")  # output end frame
    rarg.append("%s" % (chunk + by - 1))
    rarg.append("-b")  # output by frame
    rarg.append("1")
    rarg.append("-pad")  # output frame number padding
    rarg.append("4")
    rarg.append("-fnc")  # output file template
    rarg.append("name.#.ext")
    rarg.append("-im")  # output image name
    rarg.append("%s" % scene)
    rarg.append("-rd")  # output render directory
    rarg.append("%s" % renderdirectory)
    rarg.append("-r")  # render renderer
    rarg.append("mr")
    rarg.append("-rt")  # render threads
    rarg.append("2")
    rarg.append("-mem")  # render memory allocated MB
    rarg.append("200")
    rarg.append("-v")
    rarg.append("5")
    rarg.append("-proj")  # render maya project
    rarg.append("%s" % renderproject)
    rarg.append("%s" % renderscene)  # render scene file

    render = author.Command(argv=rarg)  # render scene file

    environment = author.Command(argv=["printenv"])
    thischunk.addCommand(environment)
    thischunk.addCommand(render)
    rendering.addChild(thischunk)

parent.addChild(rendering)
"""
    ffmpeg_exe  -i 020me_090_lighting_review_mono_v002_mpg720p.mov 
    -codec:v prores -profile:v 2 -y 
    020me_090_lighting_review_mono_v002_pro720p_ffmpeg2.mov
"""
proxy = author.Task(title="Make Proxy")

ffmpeg = author.Command(argv=["ffmpeg_osx","-f", "image2",
                                "-i", "%s" % finalOutputImages,
                                "-codec:v", "prores","-profile:v","0",
                                "-s","960x540","-threads","2","-loglevel","info","-y",
                                "%s" % proxyOutput], service="Transcoding")
env = author.Command(argv=["printenv"],service="ShellServices")
proxy.addCommand(env)
proxy.addCommand(ffmpeg)
parent.addChild(proxy)
job.addChild(parent)

print "#############################\n%s\n############################" % job.asTcl()

user = "pixar"
try:
    user = os.getenv("USER")
    user = "pixar"
    job.spool(owner="%s" % user)
except Exception, err:
    logger.critical("Couldnt submit job to spooler %s" % err)
