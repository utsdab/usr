import glob
import os
import tempfile
from zoovendor.six import text_type
from zoo.libs.utils import path, filesystem, zlogging
from zoo.libs.zooscene import constants
from zoo.libs.zooscene.constants import DEPENDENCY_FOLDER, ZOO_THUMBNAIL, ASSETTYPES, INFOASSET, INFOCREATORS, \
    INFOWEBSITES, INFOTAGS, INFODESCRIPTION

# TODO REMOVE ZOO MAYA IMPORTS
from zoo.libs.maya.cmds.objutils import objhandling, meshhandling, namehandling
from zoo.libs.maya.cmds.renderer.exportglobals import ZOOSCENESUFFIX, SHADERS, LIGHTS, AREALIGHTS, IBLSKYDOMES, \
    MESHOBJECTS, VERSIONKEY, GENERICVERSIONNO
from zoo.libs.maya.cmds.shaders import shadermultirenderer
from maya import cmds as cmds
import maya.api.OpenMaya as om2

logger = zlogging.getLogger(__name__)


def thumbnails(directory, fileList):
    """Returns a list of thumbnail image paths from a zooScene list without extensions

    :return thumbPathList: List of thumbnail paths one for each zooScene file (no extension)
    :rtype thumbFullPathList: list of basestring
    """
    thumbFullPathList = list()
    for i, zooSceneFile in enumerate(fileList):
        zooSceneFileName = os.path.basename(zooSceneFile)
        fileNameNoExt = os.path.splitext(zooSceneFileName)[0]
        extension = path.getExtension(zooSceneFileName)

        dependFolder = "_".join([fileNameNoExt, extension, DEPENDENCY_FOLDER])
        dependFolderPath = os.path.join(directory, dependFolder)
        if not os.path.isdir(dependFolderPath):
            thumbFullPathList.append(None)
            continue
        imageList = path.getImageNoExtension(dependFolderPath, ZOO_THUMBNAIL)
        if imageList:  # image list is only thumbnail, take the first image, could be jpg or png
            thumbFullPathList.append(os.path.join(dependFolderPath, imageList[0]))
            continue
        thumbFullPathList.append(None)
    return thumbFullPathList


def infoDictionaries(zooSceneNameList, directory):
    """ Returns a list of info dictionaries for each .zooScene file.

    These dictionaries contain information such as author, tag, descriptions etc

    :return infoDictList: A list of info dictionaries for each .zooScene file
    :rtype infoDictList: list of dict
    """
    infoDictList = list()
    if not zooSceneNameList:
        return dict()
    for zooSceneFile in zooSceneNameList:
        fullPath = os.path.join(directory, zooSceneFile)
        updateOldFolders(zooSceneFile, directory)

        zooInfoDict, fileFound = getZooInfoFromFile(fullPath, message=False)

        if not fileFound:
            zooInfoDict = createEmptyInfoDict()
        infoDictList.append(zooInfoDict)
        zooInfoDict['zooFilePath'] = fullPath
        zooInfoDict['extension'] = path.getExtension(fullPath)
    return infoDictList


def updateOldFolders(fileName, directoryPath):
    """ Renames dependency folder from old to new "fileName_fileDependency" to "fileName_jpg_fileDependency"

    :param zooFilePath: Path to the file
    :type zooFilePath:
    :return:
    :rtype:
    """

    fileNameNoExt = os.path.splitext(fileName)[0]
    extension = path.getExtension(fileName)
    newDirectory = "_".join([fileNameNoExt, extension, constants.DEPENDENCY_FOLDER])

    # AutoFix old dependency folders
    # Check if one with no extensions exists first and rename that to one with extensions
    newDirectoryNoExt = "_".join([fileNameNoExt, constants.DEPENDENCY_FOLDER])
    dirNoExt = os.path.join(directoryPath, newDirectoryNoExt)
    fullDirPath = os.path.join(directoryPath, newDirectory)

    folderUpdated = False
    if os.path.exists(dirNoExt) and not os.path.exists(fullDirPath):
        os.rename(dirNoExt, fullDirPath)
        folderUpdated = True
    elif os.path.exists(dirNoExt) and os.path.exists(fullDirPath):
        # logger.info("Warning fileDependendies for both source ({}) and destination ({}) exists for \"{}\"".
        #      format(newDirectoryNoExt, newDirectory, zooSceneFileName))
        # todo: this needs to handle if both directories already exists (eg move old to new)
        pass

    return folderUpdated


def createEmptyInfoDict():
    """Creates an empty .zooInfo dictionary

    :return infoDict: Zoo info dictionary
    :rtype infoDict: dict()
    """
    infoDict = {text_type("assetType"): text_type(""),
                text_type("animation"): text_type(None),
                text_type("description"): text_type(""),
                text_type("version"): text_type("1.0.0"),
                text_type("tags"): text_type(""),
                text_type("creators"): text_type(""),
                text_type("saved"): text_type(list()),
                text_type("websites"): text_type("")
                }
    return infoDict


def renameZooSceneOnDisk(newNameNoExtension, filePath, extension=ZOOSCENESUFFIX):
    """Renames all .zooScene re-nameable dependency files on disk, and the .zooScene itself
    Also renames the subdir given the newName (no ext)
    will check that the files and directory is writable and error if the files can't be written before renaming

    :param newNameNoExtension: the filename with no extension, will delete all files named this with an extension
    :type newNameNoExtension: str
    :param filePath: the full file path to the zoo scene including file and extension. Expects zooScene, but it doesn't have to be
    :type filePath: str
    :param extension: The file extension
    :type extension: basestring
    :return renamedFullPathFiles: a list of the full paths of the renamed files, can be many dependency files
    :rtype renamedFullPathFiles: list
    """
    notWritableMessage = "This scene cannot be renamed as it's most like in use by Maya or another program"
    if not newNameNoExtension:  # as we don't want to accidentally rename "*" files!
        return
    # get all the files to be renamed and the subDir
    zooSceneRelatedFilesFullPath, subDirfullDirPath = getZooFiles(filePath)
    # check the new filename does not already exist and get adjust new name with numerical suffix if so
    directoryPath = os.path.dirname(filePath)  # get the dir of the file
    newFullPathFileName = os.path.join(directoryPath, ".".join([newNameNoExtension, extension]))  # new full path
    newFullPathFileName = filesystem.uniqueFileName(newFullPathFileName)  # unique name with numerical suffix
    if not newFullPathFileName:  # very rare
        notWritableMessage = "Cannot be renamed as files already exist and numeric unique name limit hit"
    fileName = os.path.basename(newFullPathFileName)
    newNameNoExtension = os.path.splitext(fileName)[0]
    # If no subdirectory, then rename
    if not subDirfullDirPath:  # then there is no sub dir so just rename the .zooscene
        renamedFiles = filesystem.renameMultipleFilesNoExt(newNameNoExtension, [filePath])
        return renamedFiles
    # Check the dir can be renamed, files may not be writable
    if filesystem.checkWritableFile(subDirfullDirPath):  # returns true if not writable
        om2.MGlobal.displayWarning(notWritableMessage)
        return
    # Rename the files and subdirectories
    renamedFiles = filesystem.renameMultipleFilesNoExt(newNameNoExtension, zooSceneRelatedFilesFullPath)
    if not renamedFiles:
        om2.MGlobal.displayWarning(notWritableMessage)
        return
    # rename the folder
    zooSceneDir = os.path.dirname(filePath)
    newDirectoryName = "_".join([newNameNoExtension, extension, constants.DEPENDENCY_FOLDER])
    dependencyDir = os.path.join(zooSceneDir, newDirectoryName)
    os.rename(subDirfullDirPath, dependencyDir)
    return renamedFiles, dependencyDir


def getDependencyFolder(zooSceneFullPath, create=True):
    """creates the dependency directory for .zooscene files, these can contain .abc, .info, .obj, .fbx, textures etc

    :param zooSceneFullPath: the full path to the .zooscene file
    :type zooSceneFullPath: str
    :param create: Create if doesn't exist
    :type create: bool
    :return fullDirPath: the full directory path to the new folder
    :rtype fullDirPath: str
    """
    zooSceneFileName = os.path.basename(zooSceneFullPath)
    directoryPath = os.path.dirname(zooSceneFullPath)
    fileNameNoExt = os.path.splitext(zooSceneFileName)[0]
    extension = path.getExtension(zooSceneFullPath)
    newDirectory = "_".join([fileNameNoExt, extension, constants.DEPENDENCY_FOLDER])
    fullDirPath = os.path.join(directoryPath, newDirectory)

    # Create the dependency folder if it doesnt exist
    if create:  # doesn't already exist
        createDependencies(fullDirPath)
    return fullDirPath, fileNameNoExt


def createDependencies(fullDirPath):
    """ Create dependencies if it doesnt exist

    :param fullDirPath:
    :type fullDirPath:
    :return:
    :rtype:
    """
    if not os.path.exists(fullDirPath):
        os.makedirs(fullDirPath)


def getFileDependenciesList(zooScenePath, ignoreThumbnail=False):
    """Retrieve a list of all files in the dependency directory DIRECTORYNAMEDEPENDENCIES
    Files do not have full path so directory path is also returned,
    files are ["fileName.abc", "fileName.zooInfo"] etc

    :param zooScenePath: the full path to the file usually .zooscene but can be any extension
    :type zooScenePath: str
    :param ignoreThumbnail: ignores the files called thumbnail.* useful for renaming
    :type ignoreThumbnail: str
    :return fileDependencyList: list of short name files found in the subdirectory DIRECTORYNAMEDEPENDENCIES
    :rtype fileDependencyList: list
    :return fullDirPath: the full path of the sub directory DIRECTORYNAMEDEPENDENCIES
    :rtype fullDirPath: str
    """
    fileDependencyList = list()
    zooSceneFileName = os.path.basename(zooScenePath)
    directoryPath = os.path.dirname(zooScenePath)
    fileNameNoExt = os.path.splitext(zooSceneFileName)[0]
    ext = path.getExtension(zooScenePath)

    newDirectory = "_".join([fileNameNoExt, ext, constants.DEPENDENCY_FOLDER])
    fullDirPath = os.path.join(directoryPath, newDirectory)
    if not os.path.exists(fullDirPath):  # doesn't already exist
        return fileDependencyList, ""  # return empty as directory doesn't exist
    globPattern = os.path.join(fullDirPath, fileNameNoExt)
    for fileName in glob.glob("{}.*".format(globPattern)):
        fileDependencyList.append(fileName)
    if not ignoreThumbnail:
        for fileName in glob.glob(os.path.join(fullDirPath, "thumbnail.*")):
            fileDependencyList.append(fileName)
    #  return os.chdir to the temp dir as it gets in the way with file permissions for later renames!
    os.chdir(tempfile.gettempdir())
    return fileDependencyList, fullDirPath


def getZooFiles(filePath, ignoreThumbnail=False):
    """ Retrieves all zoo files related to the given file (usually .zooscene).

    Expects .zooscene file but can be any file under the main folder that has file dependencies

    returns only filenames not the directory path

    :param filePath: full path of a .zooscene file or a file in the main folder
    :type filePath: basestring
    :param ignoreThumbnail: ignores the files called thumbnail.* useful for renaming
    :type ignoreThumbnail: str
    :return relatedFiles, subDir: all files related to the .zooscene in the current directory as string paths, and the dependency subdirectory
    :rtype relatedFiles: tuple(list[basestring], basestring)
    """
    relatedFiles = [filePath]
    fileDependencyList, subDir = getFileDependenciesList(filePath, ignoreThumbnail=ignoreThumbnail)
    for fileName in fileDependencyList:
        relatedFiles.append(os.path.join(subDir, fileName))
    return relatedFiles, subDir


def getSingleFileFromZooScene(zooSceneFullPath, fileExtension):
    """ Check if file exists in zooScene dependencies

    Returns the name of the file if it exists given the extension eg .abc from the zooSceneFullPath
    Gets all the files in the subdirectory associated with the .zooScene file and filters for the file type
    Supports returning of one file, the first it finds so not appropriate for textures

    :param zooSceneFullPath:  the full path of the .zooScene file to be saved
    :type zooSceneFullPath: str
    :param fileExtension:  the file extension to find no ".", so alembic is "abc"
    :type fileExtension: str
    :return extFileName: the filename (no directory) of the extension given > for example "myFileName.abc"
    :rtype extFileName: str
    """

    extFileName = ""
    fileList, directory = getFileDependenciesList(zooSceneFullPath)
    if not directory:
        return extFileName
    for fileName in fileList:  # cycle through the files and find if a match with the extension
        if fileName.lower().endswith(fileExtension.lower()):
            return os.path.join(directory, fileName)
    return extFileName


def selectedZooSceneObjDictFix(zooSceneDict, gShaderDict, objectRootList):
    """This function adjusts for exporting selected nodes on the long file names fixing the paths
    alembic exports from the root and leaves out other dag objects higher in the hierarchy
    so on importing those parent objects are missing.
    this function checks and fixes the long name pathing

    :param zooSceneDict: the main dict in a .zooscene file
    :type zooSceneDict: dict
    :return objectLongList: the object long list now fixed with the parent of the alembic roots cut out of the prefix
    :rtype objectLongList: list
    :param exportSubD: are subds being exported?
    :type exportSubD: bool
    :return zooSceneDict: the now updated zooSceneDict
    :rtype zooSceneDict: dict
    """
    if gShaderDict:  # fix shader full paths
        for shader in gShaderDict:
            if shadermultirenderer.OBJECTSFACES in gShaderDict[shader]:
                if gShaderDict[shader][shadermultirenderer.OBJECTSFACES]:
                    for i, objFaceAssign in enumerate(gShaderDict[shader][shadermultirenderer.OBJECTSFACES]):
                        fixedShaderObFullPath = objhandling.removeRootParentListObj(objFaceAssign, objectRootList)
                        gShaderDict[shader][shadermultirenderer.OBJECTSFACES][i] = fixedShaderObFullPath
    if MESHOBJECTS in zooSceneDict:
        newLightShaderAssignDict = zooSceneDict.copy()
        for meshObject in zooSceneDict[MESHOBJECTS]:  # fix single objects
            newMeshObject = objhandling.removeRootParentListObj(meshObject, objectRootList)
            if meshObject != newMeshObject:
                # to be safe assign to a copy of the dict as we are looping
                newLightShaderAssignDict[MESHOBJECTS][newMeshObject] = newLightShaderAssignDict[
                    MESHOBJECTS].pop(meshObject)
        zooSceneDict = newLightShaderAssignDict
    return zooSceneDict, gShaderDict


def createTagInfoDict(assetType, creator, website, tags, description, saveInfo, animInfo):
    """ Creates a dict ready for the zooInfo file

    :param assetType: the information about asset type, model, scene, lights, shaders, etc
    :type assetType: str
    :param creator: the information about creator/s
    :type creator: str
    :param website: the information about the creators website links
    :type website: str
    :param tags: the tag information
    :type tags: str
    :param description: the full description
    :type description: str
    :param saveInfo: the file information saved as a list ["alembic", "generic lights"] etc
    :type saveInfo: list
    :param animInfo: the animation information of the file "0 100" or "" or None if none
    :type animInfo: str
    :return zooInfoDict: the dict containing all information including the file version number
    :rtype zooInfoDict: str
    """
    zooInfoDict = {constants.INFOASSET: assetType,
                   constants.INFOCREATORS: creator,
                   constants.INFOWEBSITES: website,
                   constants.INFOTAGS: tags,
                   constants.INFODESCRIPTION: description,
                   constants.INFOSAVE: saveInfo,
                   constants.INFOANIM: animInfo,
                   VERSIONKEY: GENERICVERSIONNO}
    return zooInfoDict


def updateZooInfo(zooSceneFullPath, assetType=ASSETTYPES[0], creator="", website="", tags="", description="",
                  saveInfo="", animInfo=""):
    """Updates the .zooInfo file depending on the incoming values, if not variable then leave the values as are.

    :param zooSceneFullPath: the full path of the zooScene file, this will save out as another file zooInfo
    :type zooSceneFullPath: str
    :param assetType: the information about asset type, model, scene, lights, shaders, etc
    :type assetType: str
    :param creator: the information about creator/s
    :type creator: str
    :param website: the information about the creators website links
    :type website: str
    :param tags: the tag information
    :type tags: str
    :param description: the full description
    :type description: str
    :param saveInfo: the file information saved as a list ["alembic", "generic lights"] etc
    :type saveInfo: list
    :param animInfo: the animation information of the file "0 100" or "" or None if none
    :type animInfo: str
    :return zooInfoFullPath: the full path of the .zooInfo file
    :rtype zooInfoFullPath: str
    :return zooInfoDict: the dict containing all information including the file version number
    :rtype zooInfoDict: str
    """
    # find if the .zooInfo file exists
    zooInfoDict, fileFound = getZooInfoFromFile(zooSceneFullPath, message=True)
    # if it does get the current information
    if not fileFound:
        zooInfoDict = createTagInfoDict(assetType, creator, website, tags, description, saveInfo, animInfo)
    else:
        if assetType != ASSETTYPES[0]:  # if not default "Not Specified"
            zooInfoDict[constants.INFOASSET] = assetType
        if creator:
            zooInfoDict[constants.INFOCREATORS] = creator
        if website:
            zooInfoDict[constants.INFOWEBSITES] = website
        if tags:
            zooInfoDict[constants.INFOTAGS] = tags
        if description:
            zooInfoDict[constants.INFODESCRIPTION] = description
        if saveInfo:
            zooInfoDict[constants.INFODESCRIPTION] = saveInfo
        if animInfo:
            zooInfoDict[constants.INFODESCRIPTION] = animInfo
    # save the updated dict
    zooInfoFullPath = writeZooInfo(zooSceneFullPath, zooInfoDict[constants.INFOASSET],
                                   zooInfoDict[constants.INFOCREATORS],
                                   zooInfoDict[constants.INFOWEBSITES], zooInfoDict[constants.INFOTAGS],
                                   zooInfoDict[constants.INFODESCRIPTION],
                                   zooInfoDict[constants.INFOSAVE], zooInfoDict[constants.INFOANIM],
                                   message=False)
    return zooInfoFullPath, zooInfoDict


def writeZooInfo(zooSceneFullPath, assetType, creator, website, tags, description, saveInfo, animInfo, message=True):
    """Saves a zooInfo file in the subdirectory from the zooScene file

    :param zooSceneFullPath: the full path of the zooScene file, this will save out as another file zooInfo
    :type zooSceneFullPath: str
    :param assetType: the information about asset type, model, scene, lights, shaders, etc
    :type assetType: str
    :param creator: the information about creator/s
    :type creator: str
    :param website: the information about the creators website links
    :type website: str
    :param tags: the tag information
    :type tags: str
    :param description: the full description
    :type description: str
    :param saveInfo: the save info list, what did the file save?
    :type saveInfo: list
    :param animInfo:
    :type animInfo:
    :param message: report the save success message to the user?
    :type message: bool

    :return zooInfoFullPath: the full path of the file saved (zooInfo)
    :rtype zooInfoFullPath:
    """
    zooInfoDict = createTagInfoDict(assetType, creator, website, tags, description, saveInfo, animInfo)
    fullDirPath, fileNameNoExt = getDependencyFolder(zooSceneFullPath)
    zooInfoFileName = ".".join([fileNameNoExt, constants.ZOO_INFO_EXT])
    zooInfoFullPath = os.path.join(fullDirPath, zooInfoFileName)
    filesystem.saveJson(zooInfoDict, zooInfoFullPath, indent=4, separators=(",", ":"), message=False)
    return zooInfoFullPath


def getZooInfoFromFile(zooSceneFullPath, message=True):
    """Gets other files from the .zooScene, for example .zooInfo from a file on disk

    :param zooSceneFullPath: the full path of the zooScene file, this will save out as another file zooInfo
    :type zooSceneFullPath: str
    :return zooInfoDict: the dictionary with all info information, if None the file wasn't found
    :rtype zooInfoDict: dict
    :return fileFound: was the zooInfo file found?
    :rtype fileFound: bool
    """
    zooInfoPath = getSingleFileFromZooScene(zooSceneFullPath, constants.ZOO_INFO_EXT)
    if not os.path.exists(zooInfoPath):  # doesn't exist
        if message:
            om2.MGlobal.displayWarning("ZooInfo File Not Found")
        fileFound = False
        return createTagInfoDict(ASSETTYPES[0], "", "", "", "", "",
                                 ""), fileFound  # return the empty dict as no file found
    fileFound = True
    return filesystem.loadJson(zooInfoPath), fileFound  # returns zooInfoDict


def deleteZooDependencies(filePathZooScene, message=True, keepThumbnailOverride=False):
    """Deletes zoo file dependencies and the .zooScene leaving the subDirectory, deletes the actual files on disk.
    Useful for saving over existing files

    :param filePathZooScene: The full file path of the .zooscene to be deleted, other files are deleted automatically
    :type filePathZooScene: str
    :param message: report the message to the user in Maya?
    :type message: bool
    :param keepThumbnailOverride: keeps the existing thumbnail image if over righting, usually for delete when renaming
    :type keepThumbnailOverride: bool
    :return filesFullPathDeleted: The files deleted
    :rtype filesFullPathDeleted: list
    """
    filesFullPathDeleted = list()
    # get all the files to be renamed and the subDir
    zooSceneRelatedFilesFullPath, subDirfullDirPath = getZooFiles(filePathZooScene,
                                                                  ignoreThumbnail=keepThumbnailOverride)
    if filesystem.checkWritableFile(subDirfullDirPath) or filesystem.checkWritableFiles(zooSceneRelatedFilesFullPath):
        if message:
            om2.MGlobal.displayWarning("This scene cannot be written at this time as it's most like in use by Maya or "
                                       "another program")
        return
    if len(zooSceneRelatedFilesFullPath) > 100:
        om2.MGlobal.displayWarning("This function is deleting more than 100 files!! "
                                   "something is wrong, check the files in dir `{}`".format(subDirfullDirPath))
        return
    for fileFullPath in zooSceneRelatedFilesFullPath:
        os.remove(fileFullPath)
        filesFullPathDeleted.append(fileFullPath)
    return filesFullPathDeleted


def deleteZooSceneFiles(fileFullPath, message=True, keepThumbnailOverride=False):
    """Deletes a file and it's related dependencies on disk, usually a .zooScene but can have any extension

    :param fileFullPath: The full file path of the file to be deleted, dependency files are deleted automatically
    :type fileFullPath: str
    :param message: report the message to the user in Maya?
    :type message: bool
    :param keepThumbnailOverride: If True will skip the thumbnail image deletion. Used while renaming.
    :type keepThumbnailOverride: bool
    :return filesFullPathDeleted: The files deleted
    :rtype filesFullPathDeleted: list
    """
    filesFullPathDeleted = list()
    # get all the files to be renamed and the subDir
    zooSceneRelatedFilesFullPath, subDirfullDirPath = getZooFiles(fileFullPath)
    if keepThumbnailOverride:
        if "thumbnail.jpg" in zooSceneRelatedFilesFullPath:
            zooSceneRelatedFilesFullPath.remove("thumbnail.jpg")
        if "thumbnail.png" in zooSceneRelatedFilesFullPath:
            zooSceneRelatedFilesFullPath.remove("thumbnail.png")
    if not subDirfullDirPath:  # there's no subdirectory so just delete the file and return it
        # doesn't need a check as it should be deletable
        os.remove(fileFullPath)
        filesFullPathDeleted.append(fileFullPath)
        return filesFullPathDeleted
    # check the files and dir file-permissions, rename of itself to the same name, returns true if not writable
    if filesystem.checkWritableFile(subDirfullDirPath) or filesystem.checkWritableFiles(zooSceneRelatedFilesFullPath):
        if message:
            om2.MGlobal.displayWarning("This scene cannot be deleted/renamed as it's most like in use by Maya or "
                                       "another program")
        return
    if len(zooSceneRelatedFilesFullPath) > 20:
        om2.MGlobal.displayWarning("This function is deleting more than 20 files!! "
                                   "something is wrong, check the files in dir `{}`".format(subDirfullDirPath))
        return
    for fileFullPath in zooSceneRelatedFilesFullPath:
        os.remove(fileFullPath)
        filesFullPathDeleted.append(fileFullPath)
    # delete subdir
    if not keepThumbnailOverride:
        os.rmdir(subDirfullDirPath)
    filesFullPathDeleted.append(subDirfullDirPath)
    return filesFullPathDeleted


def updateZooSceneDir(directory):
    """Updates .zoo Scenes from pre v1 format where generic light and shader data was saved inside the .zooScene
    Will batch all .zooScene files in the given directory and fix them from the old format

    :param directory:
    :type directory:
    """
    # get a list of the .zooScenes
    zooSceneList = list()
    os.chdir(directory)
    for fileName in glob.glob("*.{}".format(ZOOSCENESUFFIX)):
        zooSceneList.append(fileName)
    # return os.chdir to the temp dir as it gets in the way with file permissions for later renames!
    os.chdir(tempfile.gettempdir())
    # start loop
    for zooScene in zooSceneList:
        zooSceneFullPath = os.path.join(directory, zooScene)
        zooSceneDict = filesystem.loadJson(zooSceneFullPath)
        if SHADERS in zooSceneDict:
            shaderDict = zooSceneDict[SHADERS]
        else:
            shaderDict = dict()
        lightDict = zooSceneDict[LIGHTS]
        # see if the directory dependancies exists if not create it
        getDependencyFolder(zooSceneFullPath)
        # create the shader dict and the light dict files if they exists
        if lightDict[AREALIGHTS] or lightDict[IBLSKYDOMES]:
            # create the light dict
            writeZooGLights(lightDict, zooSceneFullPath)
        if shaderDict:
            # create the shader dict
            writeZooGShaders(shaderDict, zooSceneFullPath)
        # remove the shader and light dicts
        zooSceneDict.pop(SHADERS, None)
        zooSceneDict.pop(LIGHTS, None)
        filesystem.saveJson(zooSceneDict, zooSceneFullPath, indent=4, separators=(",", ":"))


def writeZooGShaders(zooShaderDict, zooSceneFullPath):
    """Writes a shader dict to disk in the zoo dependency sub folder

    :param zooShaderDict: the generic shader dictionary
    :type zooShaderDict: dict
    :param zooSceneFullPath: the full path to the zooScene file
    :type zooSceneFullPath: str
    :return zooShadFullPath: the full path to the shader file that has been saved
    :rtype zooShadFullPath: str
    """
    fullDirPath, fileNameNoExt = getDependencyFolder(zooSceneFullPath)
    zooShadFileName = ".".join([fileNameNoExt, constants.ZOO_SHADER_EXT])
    zooShadFullPath = os.path.join(fullDirPath, zooShadFileName)
    filesystem.saveJson(zooShaderDict, zooShadFullPath, indent=4, separators=(",", ":"))
    return zooShadFullPath


def writeZooGLights(zooLightsDict, zooSceneFullPath):
    """Writes a light dict to disk inside the zoo dependency sub folder of the given .zooScene file

    :param zooLightsDict: the generic lights dictionary
    :type zooLightsDict: dict
    :param zooSceneFullPath: the full path to the zooScene file
    :type zooSceneFullPath: str
    :return zooShadFullPath: the full path to the shader file that has been saved
    :rtype zooShadFullPath: str
    """
    fullDirPath, fileNameNoExt = getDependencyFolder(zooSceneFullPath)
    zooLightsFileName = ".".join([fileNameNoExt, constants.ZOO_LIGHT_EXT])
    zooLightsFullPath = os.path.join(fullDirPath, zooLightsFileName)
    filesystem.saveJson(zooLightsDict, zooLightsFullPath, indent=4, separators=(",", ":"))
    return zooLightsFullPath


def writeExportZooInfo(zooSceneFullPath, zooSceneDict, gShaderDict, gLightDict, objectRootList, tagInfoDict,
                       animationInfo):
    """While exporting writes the .zooInfo file
    Should add cameras

    :param zooSceneFullPath: full path the the .zooScene
    :type zooSceneFullPath: str
    :param zooSceneDict: the dictionary that will be written to the .zooScene
    :type zooSceneDict: dict
    :param objectRootList: the scene roots from alemebic
    :type objectRootList: list
    :param tagInfoDict: the tag info if provided ok if it's empty, this will be written
    :type tagInfoDict: dict
    :return zooInfoFullPath: the full path to the zooInfo file
    :rtype zooInfoFullPath: str
    :return fileInfoSaved: the info list with what was saved
    :rtype fileInfoSaved: list
    """
    fileInfoSaved = list()
    if objectRootList:
        fileInfoSaved.append(constants.SAVE_ALEMBIC)
    if gShaderDict:
        fileInfoSaved.append(constants.SAVE_G_SHADERS)
    if gLightDict:
        fileInfoSaved.append(constants.SAVE_LIGHTS)
    if MESHOBJECTS in zooSceneDict:
        if zooSceneDict[MESHOBJECTS]:
            fileInfoSaved.append(constants.SAVE_MESH)
    if not tagInfoDict:  # create an empty dict to pass in
        # ASSETTYPES[0] is "Not Specified"
        tagInfoDict = createTagInfoDict(ASSETTYPES[0], "", "", "", "", "", "")
    zooInfoFullPath = writeZooInfo(zooSceneFullPath, tagInfoDict[INFOASSET], tagInfoDict[INFOCREATORS],
                                   tagInfoDict[INFOWEBSITES], tagInfoDict[INFOTAGS], tagInfoDict[INFODESCRIPTION],
                                   fileInfoSaved, animationInfo)
    return zooInfoFullPath, fileInfoSaved


def setSudbDDict(zooSceneDict):
    """Sets the subD attributes from the zooSceneDict

    :param zooSceneDict: the nested exported dict which contains subD information
    :type zooSceneDict: dict
    """
    if MESHOBJECTS in zooSceneDict:  # check if meshesDict were recorded
        for meshTransform in zooSceneDict[MESHOBJECTS]:  # cycle through meshes
            if cmds.objExists(meshTransform):  # if the mesh is in the scene set subDs
                meshhandling.setMeshSubDSettings(meshTransform,
                                                 zooSceneDict[MESHOBJECTS][meshTransform],
                                                 longName=True)


def loadGenericShaderLightFiles(zooSceneFullPath):
    """loads a .zooGShad and .zooGLight information from a zooSceneFullPath

    :param zooSceneFullPath: the full path to the .zooScene file
    :type zooSceneFullPath: str
    :return shadMultDict: the generic shader dictionary
    :rtype shadMultDict: dict
    :return lightMultDict: the generic light dictionary
    :rtype lightMultDict: dict
    """
    shadMultDict = dict()
    lightMultDict = dict()
    directoryPath = getDependencyFolder(zooSceneFullPath)[0]  # just pull the path and not the filename
    if not directoryPath:  # could not find folder so dicts are empty
        return shadMultDict, lightMultDict
    lightFile = getSingleFileFromZooScene(zooSceneFullPath,
                                          constants.ZOO_LIGHT_EXT)  # the filename only no path
    shaderFile = getSingleFileFromZooScene(zooSceneFullPath, constants.ZOO_SHADER_EXT)
    if shaderFile:
        shaderFullPath = os.path.join(directoryPath, shaderFile)
        if os.path.isfile(shaderFullPath):
            shadMultDict = filesystem.loadJson(shaderFullPath)
    if lightFile:
        lightFullPath = os.path.join(directoryPath, lightFile)
        if os.path.isfile(lightFullPath):
            lightMultDict = filesystem.loadJson(lightFullPath)
    return shadMultDict, lightMultDict


def getExportedNamespaces(objectRootList, gShaderDict):
    """Gets all namespaces in the nodes under the objectRootList and from shader names

    :param objectRootList: object roots as to be exported from alembic, needs to all children
    :type objectRootList: list
    :param zooSceneDict: the .zooScene dictionary with light data
    :type zooSceneDict: dict
    :return namespaceList: A list of Maya Namespaces Found
    :rtype namespaceList: list
    """
    # get all objects below the roots
    if objectRootList:  # may only be shaders
        objectRootList += cmds.listRelatives(objectRootList, allDescendents=True)
    # collect any namespaces
    namespaceList = namehandling.getNamespacesFromList(objectRootList)
    # get a shader list
    if not gShaderDict:
        return namespaceList
    for shaderDictKey in gShaderDict:
        if ":" in shaderDictKey:
            namespaceList.append(shaderDictKey.split(":")[0])
    return list(set(namespaceList))
