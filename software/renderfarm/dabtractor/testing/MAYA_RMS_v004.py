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


def usedirmap(input):
    # %D(mayabatch)
    return '%D({thing})'.format(thing=input)


proj = "/Volumes/dabrender/120988_matthewgidney/testFarm"
scenefile = "rms_dotty_AOV.ma"
scene, ext = os.path.splitext(scenefile)


by = 4
start = 1
end = 100
extension = "exr"
outputfilename = "output"
finalOutputImages = usedirmap("{0}/images/{1}/{2}.%04d.{3}".format(proj, scene, outputfilename, extension))
proxyOutput = usedirmap("{0}/images/{1}.{2}".format(proj, scene, "mov"))

# cmdpath = usedirmap("/usr/autodesk/maya2015-x64/bin/Render")
cmdpath = "Render"

renderdirectory = usedirmap("%s/images/%s" % (proj, scene))
renderscene = usedirmap("%s/scenes/%s" % (proj, scenefile))
renderproject = usedirmap("%s" % proj)

author.setEngineClientParam(hostname="dabtractor-engine", port=5600, user="pixar", debug=True)

job = author.Job(title="Maya_RMS_v004",
                 priority=100,
                 envkey=["rms-19.0-maya-2015"],
                 service="RfMRender")

dirmap1 = job.newDirMap("/Volumes/dabrender", "/dabrender", "linux")
dirmap2 = job.newDirMap("/dabrender", "/Volumes/dabrender", "osx")
dirmap3 = job.newDirMap(usedirmao("Render"), "/usr/autodesk/maya2015-x64/bin/Render", "linux")

parent = author.Task(title="Parent", service="RfMRender")
parent.serialsubtasks = 1

preflight = author.Task(title="Make Image Directory",
                        service="RfMRender")
makedirectory = author.Command(argv=["mkdir", "-p", "%s" % (renderdirectory)])
environment = author.Command(argv=["printenv"])

preflight.addCommand(environment)
preflight.addCommand(makedirectory)
parent.addChild(preflight)

rendering = author.Task(title="Maya Batch Rendering", argv=[], service="RfMRender")
rendering.serialsubtasks = 0

# loop throught the batch logic for ****** Render -r rman **********
"""
From a command line use the following format:
Render -r rman sceneFile
    If no project is specified, the current project is used.
    Maya Batch Render Flags
    The following flags are supported for Maya Batch Renders via the command line \
    (i.e. Render -r rman foo.ma). They are also valid for the rman render and rman \
    genrib commands, and can be used in scripted workflows:

    Common options:
        -help   Print help
    -test      Print Mel commands but do not execute them
    -verb      Print Mel commands before they are executed
    -keepMel     Keep the temporary Mel file
    -listRenderers     List all available renderers
    -renderer string    Use this specific renderer
    -r string     Same as -renderer
    -proj string     Use this Maya project to load the file
    -log string      Save output into the given file

    All purpose flags:
    -setAttr string string       This flag can be used to set any of the global attributes \
    listed in RenderMan_for_Maya.ini. It takes a name value pair. Attribute values which have \
    multiple data elements should be surrounded by quotes. The flag can be used multiple times. \
    Example:
    Render -r rman -setAttr ShadingRate 5 -setAttr PixelSamples "3 3" -setAttr motionBlur 1 -setAttr
    Format:resolution "320 240" filename
    -setPref string string     This flag can be used to set any of the preferences listed in \
    RenderMan_for_Maya.ini. It takes a name value pair. Attribute values that have multiple \
    data elements should be surrounded by quotes. The flag can be used multiple times. \
    For example:
        Render -r rman -setPref BatchCompileMode zealous filename

    General purpose flags:
    -rd path      Directory in which to store image files
    -fnc string    File Name Convention:  name, name.ext, name.#.ext, name.ext.# name.#, \
    name#.ext, name_#.ext
        As a shortcut, numbers 1, 2, ... can be used.
    -im filename    Image file output name
    -of string     File format of output images: Alias, Cineon, MayaIFF, OpenEXR, SGI8, \
    SGI16, SoftImage, Targa, Tiff8, Tiff16, Tiff32

    Frame numbering options:
    -s float    Starting frame for a sequence
    -e float    End frame for a sequence
    -b float    By frame/step for a sequence
    -pad int    Number of digits in the frame number included in the output image file name
    -rfs int    The initial (renumbered) frame number for the first frame when rendering
    -rfb int     The step by which frames are renumbered (used in conjunction with -rfs).

    Camera options:
    -cam name    The name of the camera from which you are rendering
    -rgb boolean      Enable/disable RGB output
    -alpha boolean    Enable/disable Alpha output
    -depth boolean    Enable/disable Depth output
    -iip     Disable all image planes before rendering
    -res int int    Specify the resolution (X Y) of the rendered image
    -crop float float float float     Specify a crop window for the rendered image

    Render Layers:
    -rl boolean|name(s)    Render each listed layer separately

    MEL callbacks:
    -pre strin     MEL code executed before each frame
    -post string   MEL code executed after each frame

    MEL callbacks for Maya 7.0
    -preRender string    MEL code executed before rendering
    -postRender string   MEL code executed after rendering
    -preLayer string     MEL code executed before each render layer
    -postLayer string    MEL code executed after each render layer
    -preFrame string     MEL code executed before each frame
    -postFrame string    MEL code executed after each frame

Bake Options:
    -bake int
        0: Don't bake, but do regular rendering
        1: Bake texture maps
        2: Bake texture maps and do regular rendering
    -bakeChannels string     Comma delimited list of one or more channels: _ambient,_diffuse,\
    _diffuse_noshadow, _incandescence,_indirect,_indirectdiffuse, _irradiance,_occlusion,\
    _reflection,_refraction, _shadow,_specular,_subsurface,_surfacecolor, _translucence
    -bakeResolution int int    Set X Y resolution of baked maps
    -bakeCamera string   Camera to use while baking
    -bakeFileFormat string    File format of output images: Alias, Cineon, It, MayaIFF, OpenEXR, SGI8, \
    SGI16, SoftImage, Targa, Tiff8, Tiff16, Tiff32
    -bakeFileDepth string

    Depth of output images: byte, short, float
    Other:
    -rep boolean    Do not replace the rendered image if it already exists
    -n int     Number of processors to use. 0 indicates use all available.
    -compile boolean    Forces compilation of all shaders, even if they already exist.

    Note
    Remember to place a space between option flags and their arguments.
    Any boolean flag will take the following values as TRUE: on, yes, true, or 1.
    Any boolean flag will take the following values as FALSE: off, no, false, or 0.
"""



for chunk in range(start, end, by):
    t1 = "RMS Render %s-%s" % (chunk, chunk + by - 1)
    thischunk = author.Task(title=t1, service="RfMRender")

    rarg = ["%s" % cmdpath]  # Main command - typically it is Render
    # rarg.append("-at")  # ?????
    rarg.append("-res")  # output image height
    rarg.append("720")
    rarg.append("1280")
    # rarg.append("-ard")  # output image aspect ratio
    # rarg.append("1.778")
    # rarg.append("-par")  # output pixel aspect ratio
    # rarg.append("1.0")
    rarg.append("-of")  # output file format
    rarg.append("OpenExr")
    rarg.append("-s")  # output start frame
    rarg.append("%s" % chunk)
    rarg.append("-e")  # output end frame
    rarg.append("%s" % (chunk + by - 1))
    rarg.append("-b")  # output by frame
    rarg.append("1")
    rarg.append("-pad")  # output frame number padding
    rarg.append("4")
    # rarg.append("-fnc")  # output file template
    # rarg.append("namec.#.ext")
    rarg.append("-im")  # output image name
    rarg.append("%s" % outputfilename)
    rarg.append("-rd")  # output render directory
    rarg.append("%s" % renderdirectory)
    rarg.append("-r")  # render renderer
    rarg.append("rman")
    rarg.append("-n")  # render threads
    rarg.append("1")
    # rarg.append("-mem")  # render memory allocated MB
    # rarg.append("2000")
    rarg.append("-proj")  # render maya project
    rarg.append("%s" % renderproject)
    #rarg.append("-cam")  # render which camera to render
    # rarg.append("renderCamera")
    rarg.append("%s" % renderscene)  # render scene file

    render = author.Command(argv=rarg)  # render scene file

    environment = author.Command(argv=["printenv"])
    thischunk.addCommand(environment)
    thischunk.addCommand(render)
    rendering.addChild(thischunk)

parent.addChild(rendering)

proxy = author.Task(title="Make Proxy - ffmpeg", argv=["ffmpeg",
                                                       "-i", "%s" % finalOutputImages,
                                                       "-vcodec", "acpn",
                                                       "%s" % proxyOutput], service="RfMRender")
parent.addChild(proxy)
job.addChild(parent)

print "#############################\n%s\n############################" % job.asTcl()

user=""
try:
    user=os.getenv("USER")
    user = "pixar"
    job.spool(owner="%s" % user)
except Exception, err:
    logger.critical("Couldnt submit job to spooler %s" % err)
