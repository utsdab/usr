
AEBASEDIRNAME = "AE-project"
AESOURCEIMAGES = "source-images"
AEPROJECTS = "projects"
AEOUTPUT = "output-video"
AEOUTPUTSTILLS = "output-stillImages"

AEBASEFOLDERS = {AESOURCEIMAGES: "",
                 AEPROJECTS: "",
                 AEOUTPUT: "",
                 AEOUTPUTSTILLS: ""}

AEDIRECTORYSTRUCTURE = {AEBASEDIRNAME: AEBASEFOLDERS}


def getAEProjectDirPaths(insideMayaProject=True, baseDirOveride=""):
    """Gets the directory paths of the After Effects project directory

    :param insideMayaProject: if true the AE folder is found inside the Maya path, else outside
    :type insideMayaProject: bool
    :param baseDirOveride: user can give an explicit path, is ignored if ""
    :type baseDirOveride: str
    :return AEDirectoryPaths: A nested dictionary containing the directory structure with paths
    :rtype AEDirectoryPaths: dict
    """

    # get the current maya project

    # fix file path if outside Maya project and rename dir

    # build directory paths

    pass

def buildDiscoverAEDirStructure(insideMayaProject=True, baseDirOveride=""):
    """Will create the folders on disk of the AE base directorys from the global nested dict.
    If the folders exist just return their paths

    :param insideMayaProject: if true the AE folder is found inside the Maya path, else outside
    :type insideMayaProject: bool
    :param baseDirOveride: user can give an explicit path, is ignored if ""
    :type baseDirOveride: str
    :return:
    :rtype:
    """
    pass
    #  get the paths
    AEDirectoryPaths = getAEProjectDirPaths(insideMayaProject=insideMayaProject,
                                            baseDirOveride=baseDirOveride)

    # build them if they don't exist

    pass
    # return the paths
    return AEDirectoryPaths

def moveImageFilesToAEDirectory(insideMayaProject=True, baseDirOveride="", imageDirOverride="",
                                overwrite=False, moveNotCopy=True, additionalSubDir=""):
    """Moves the images and creates folder based on image sequence names.
     Names should follow the convention {fileName} . {AOVType} . {frameNumber}. {ext}
    They will be placed in the directory
        AEBASEDIRNAME\AESOURCEIMAGES\fileName\AOVType
    Ready for import into AE
    If the user wants they can provide an additional subdirectory
        AEBASEDIRNAME\AESOURCEIMAGES\additionalSubDir\fileName\AOVType
    Or provide an explicit path with

    :param insideMayaProject: if true the AE folder is found inside the Maya path, else outside
    :type insideMayaProject: bool
    :param baseDirOveride: user can give an explicit path, is ignored if ""
    :type baseDirOveride: str
    :param imageDirOverride: the user can provide filepath directory to place images
    :type imageDirOverride: str
    :param overwrite: If images exist delete and overwite them, otherwise a new unique folder 001 is created
    :type overwrite: bool
    :param moveNotCopy: do you want to move or copy the files?
    :type moveNotCopy: bool
    :return filesMovedList: return the files moved/copied fileName.AOV.#.ext
    :rtype filesMovedList: list
    """
    # get the AE project directory paths
    AEDirectoryPaths = buildDiscoverAEDirStructure(insideMayaProject=insideMayaProject,
                                       baseDirOveride=baseDirOveride)
    # get all the files in the Maya images directory

    # get all the files with the same name (first part separated by ".")

    # see if AE dir exists if not build it

    # build a list of directory names to be built for each sequence
    #  AEBASEDIRNAME/AESOURCEIMAGES/SameName

    # if overwrite is false then find unique names for those sequences that already exist

    # build the folder for each file or ignore if already built depending on overwrite

    # build the subFolders based on the middle split section [1] "." fileName.FG.exr, so FG

    # or move the the files

    pass

    return filesMovedList