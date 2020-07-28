import imghdr
import inspect
import os
import re
import sys
import glob

from zoo.libs.utils import zlogging
from zoovendor.pathlib2 import Path

from zoo.libs.utils import filesystem

logger = zlogging.getLogger(__name__)

UDIM_PATTERN = "u\d+_v\d+"
PATCH_PATTERN = "\d{4,}"
VERSION_REGEX = re.compile("(.*)([._-])v(\d+)\.?([^.]+)?$", re.IGNORECASE)
FRAME_REGEX = re.compile("(.*)([._-])(\d+)\.([^.]+)$", re.IGNORECASE)


def findFirstInPaths(filename, paths):
    """
    given a filename or path fragment, this will return the first occurance of a file with that name
    in the given list of search paths
    """
    for p in paths:
        loc = Path(p) / filename
        if loc.exists():
            return loc

    raise Exception("The file %s cannot be found in the given paths" % filename)


def findFirstInEnv(filename, envVarName):
    """
    given a filename or path fragment, will return the full path to the first matching file found in
    the given env variable
    """
    return findFirstInPaths(filename, os.environ[envVarName].split(os.pathsep))


def findFirstInPath(filename):
    """
    given a filename or path fragment, will return the full path to the first matching file found in
    the PATH env variable
    """
    return findFirstInEnv(filename, 'PATH')


def findInPyPath(filename):
    """
    given a filename or path fragment, will return the full path to the first matching file found in
    the sys.path variable
    """
    return findFirstInPaths(filename, sys.path)


def filesInDirectory(directory, ext=True):
    """ Returns all files in directory

    :param directory:
    :type directory:
    :param ext:
    :type ext:
    :return:
    :rtype:
    """
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    if ext:
        return files
    else:
        return [getFileNameNoExt(f) for f in files]


def filesByExtension(directory, extensionList):
    """Lists all of the files inside of the given directory given a file extension list

    Extension should be without the fullstop ie ["zooScene", "json", "jpg"]

    Return Example:
        ["soft_sunsetSides.zooScene", "sun_redHarsh.zooScene", "sun_warmGlow.zooScene"]

    :param directory: The directory to search and return filenames
    :type directory: str
    :param extensionList: A list of extensions to search ["zooScene", "json", "jpg"]
    :type extensionList: list of basestring
    :return fileList: A list of files returned that are in the directory and match the extension list
    :rtype fileList: list()str
    """
    fileList = list()
    if not os.path.isdir(directory):  # check if directory actually exists
        return fileList  # emptyList and directory

    for ext in extensionList:
        for filePath in glob.glob(os.path.join(directory, "*.{}".format(ext))):
            fileList.append(os.path.basename(filePath))
    # TODO: Probably shouldn't be using glob, return the current path to the directory
    tempDir = filesystem.getTempDir()
    os.chdir(tempDir)
    return fileList


def getExtension(filepath):
    """ Returns the extension of a file path

    :param filepath: The full path to a file with extension
    :type filepath: basestring
    :return: the extension
    :rtype: basestring
    """

    return os.path.splitext(filepath)[1][1:]


def getFilesNoExt(directory, fileNoExtension):
    """Given a file without an extension, find the file name

    Useful for finding a thumbnail image with unknown extension, ie could be .jpg or .png

    :param directory: The directory to search and return filenames
    :type directory: str
    :param fileNoExtension: The name of the file/s to look for
    :type fileNoExtension: str
    :return fileList: List of files matching the name, could be empty or multiple
    :rtype fileList: list(str)
    """
    fileList = list()
    os.chdir(directory)
    for fileName in glob.glob("{}.*".format(fileNoExtension)):
        fileList.append(fileName)
    # TODO: Probably shouldn't be using glob, return the current path to the directory
    tempDir = filesystem.getTempDir()
    os.chdir(tempDir)
    return fileList


def getTexturesNames(textures, input="zbrush", output="mari", prefix=None):
    """Renames given textures.

    :param textures: Textures.
    :type textures: list
    :param input: Input format ( "mari", "mudbox", "zbrush" ).
    :type input: str
    :param output: Output format ( "mari", "mudbox", "zbrush" ).
    :type output: str
    :param prefix: Rename prefix.
    :type prefix: str
    :return: Converted textures names.
    :rtype: list

    .. code-block:: python

        getTexturesNames(["Diffuse_u0_v0.exr", "Diffuse_u9_v0.exr"])
        #[(u'Diffuse_u0_v0.exr', u'Diffuse_1001.exr'), (u'Diffuse_u9_v0.exr', u'Diffuse_1010.exr')]
        getTexturesNames(["Diffuse_u0_v0.exr", "Diffuse_u9_v0.exr"], "zbrush", "mudbox")
        #[(u'Diffuse_u9_v0.exr', u'Diffuse_u10_v1.exr'), (u'Diffuse_u0_v0.exr', u'Diffuse_u1_v1.exr')]
        getTexturesNames(["Diffuse_1001.exr", "Diffuse_1010.exr"], "mari", "zbrush")
        #[(u'Diffuse_1001.exr', u'Diffuse_u0_v0.exr'), (u'Diffuse_1010.exr', u'Diffuse_u9_v0.exr')]
        getTexturesNames(["Diffuse_1001.exr", "Diffuse_1010.exr"], "mari", "mudbox")
        #[(u'Diffuse_1001.exr', u'Diffuse_u1_v1.exr'), (u'Diffuse_1010.exr', u'Diffuse_u10_v1.exr')]
        getTexturesNames(["Diffuse_u0_v0.exr", "Diffuse_u9_v0.exr"], prefix="")
        #[(u'Diffuse_u0_v0.exr', u'1001.exr'), (u'Diffuse_u9_v0.exr', u'1010.exr')]
        getTexturesNames(["Diffuse_u0_v0.exr", "Diffuse_u9_v0.exr"], prefix="Color_")
        #[(u'Diffuse_u0_v0.exr', u'Color_1001.exr'), (u'Diffuse_u9_v0.exr', u'Color_1010.exr')]

    """

    inputMethod = "udim" if input in ("mudbox", "zbrush") else "patch"
    outputMethod = "udim" if output in ("mudbox", "zbrush") else "patch"
    pattern = UDIM_PATTERN if inputMethod == "udim" else PATCH_PATTERN

    offsetUdim = lambda x, y: (x[0] + y, x[1] + y)

    if input == "zbrush" and output == "mudbox":
        textures = reversed(textures)

    texturesMapping = []
    for texture in textures:
        basename = os.path.basename(texture)
        search = re.search(r"({0})".format(pattern), basename)
        if not search:
            logger.warning("'{0}' | '{1}' file doesn't match '{2}' pattern!".format(inspect.getmodulename(__file__),
                                                                                    texture,
                                                                                    inputMethod.title()))
            continue

        if inputMethod == "udim":
            udim = [int(value[1:]) for value in search.group(0).split("_")]
        elif inputMethod == "patch":
            udim = udimFromPatch(int(search.group(0)))

        udim = offsetUdim(udim, -1) if input == "mudbox" else udim
        udim = offsetUdim(udim, 1) if output == "mudbox" else udim

        if outputMethod == "udim":
            outputAffix = "u{0}_v{1}".format(*udim)
        elif outputMethod == "patch":
            outputAffix = patchFromUdim(udim)

        if prefix is not None:
            path = os.path.join(os.path.dirname(texture), "{0}{1}{2}".format(prefix,
                                                                             outputAffix,
                                                                             os.path.splitext(texture)[-1]))
        else:
            path = os.path.join(os.path.dirname(texture), re.sub(r"({0})".format(pattern), str(outputAffix), basename))

        texturesMapping.append((texture, path))

    return texturesMapping


def patchFromUdim(udim):
    """Returns the patch from given udim.

    :param udim: Udim to convert.
    :type udim: tuple
    :return: Patch.
    :rtype: int

    .. code-block:: python

        patchFromUdim((0, 0))
        #1001
    """

    return 1000 + (udim[0] + 1) + (udim[1] * 10)


def udimFromPatch(patch):
    """Returns the udim from given patch.

    :param patch: Patch to convert.
    :type patch: int
    :return: Udim.
    :rtype: tuple(int,int)

    .. code-block:: python

        udimFromPatch(1001)
        #(0, 0)
    """
    patchMinus = patch - 1000
    u = patchMinus % 10
    v = patchMinus / 10
    return 9 if u == 0 else u - 1, v - 1 if u % 10 == 0 else v


def getFrameSequencePath(path, frameSpec=None):
    """Converts the given path with the frame number into a sequence path using 
    the frameSpec value. If not frameSpec then it will default to '%4d'
    
    :param path: The path with a frame number
    :type path: str
    :param frameSpec: The frame specification to replace the frame number with.
    :type frameSpec: str
    :return: The full sequence path
    :rtype: str
    """

    # see if there is a frame number
    frame_pattern_match = re.search(FRAME_REGEX, os.path.basename(path))
    if not frame_pattern_match:
        return ""
    # make sure we maintain the same padding
    if not frameSpec:
        frameSpec = "%0{:d}d".format(len(frame_pattern_match.group(3)), )

    newSeqName = "".join([frame_pattern_match.group(1),
                          frame_pattern_match.group(2),
                          frameSpec])
    extension = frame_pattern_match.group(4) or ""
    if extension:
        newSeqName = ".".join([newSeqName, extension])

    # build the full sequence path
    return os.path.join(os.path.dirname(path), newSeqName)


def getFileNameNoExt(path):
    """ Get File Name with extension removed
    "C:/Program Files/HelloWorld.py" ==> "HelloWorld"

    :param path:
    :type path:
    :return:
    :rtype:
    """
    base = os.path.basename(path)
    return os.path.splitext(base)[0]

def getVersionNumber(path):
    """ Extract a version number from the supplied path.

    :param path: The path to a file, likely one to be published.
    :return: An integer representing the version number in the supplied \
        path. If no version found, ``None`` will be returned.
    """

    # default if no version number detected
    version_number = -1

    # if there's a version in the filename, extract it
    version_pattern_match = re.search(VERSION_REGEX, os.path.basename(path))

    if version_pattern_match:
        version_number = int(version_pattern_match.group(3))

    return version_number


def getVersionNumberAsStr(path):
    # default if no version number detected
    version_number = ""

    # if there's a version in the filename, extract it
    version_pattern_match = re.search(VERSION_REGEX, os.path.basename(path))

    if version_pattern_match:
        version_number = version_pattern_match.group(3)

    return version_number


QTSUPPORTEDIMAGES = ('bmp', 'gif', 'jpg', 'jpeg', 'mng', 'png', 'pbm', 'pgm', 'ppm', 'tiff', 'xbm', 'xpm', 'svg', 'tga')


def getImageNoExtension(directory, nameNoExtension):
    """Returns a list of images with the name (with no file extension) in a directory,

    Useful for finding say "thumbnail.png or thumbnail.jpg"

    Returns a list of the files found

    :param directory: the full path directory to search for files
    :type directory: str
    :param nameNoExtension: the filename with no file extension
    :type nameNoExtension: str
    :return imagePathList: a list of images matching the nameNoExtension
    :rtype imagePathList: list
    """
    imagePathList = list()
    fileList = getFilesNoExt(directory, nameNoExtension)
    if not fileList:
        return
    for file in fileList:
        filename, file_extension = os.path.splitext(file)
        file_extension = file_extension.replace(".", "")
        if file_extension in QTSUPPORTEDIMAGES:
            imagePathList.append(file)
    return imagePathList


def isImage(path):
    try:
        return imghdr.what(path) is not None or path.split(os.extsep)[-1] in QTSUPPORTEDIMAGES
    except IOError:
        return False


def imageSupportByQt(path):
    imageType = imghdr.what(path)
    if imageType is not None:
        return imageType.lower() in QTSUPPORTEDIMAGES
    return False
