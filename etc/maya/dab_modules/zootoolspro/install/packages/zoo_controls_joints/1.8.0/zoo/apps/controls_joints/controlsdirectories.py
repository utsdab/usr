import os

from zoo.libs.utils import filesystem, path
from zoo.libs.zooscene import constants, zooscenefiles
from zoo.preferences.core import preference
from zoo.apps.controls_joints import controlsjointsconstants as cc


def buildControlsDirectories():
    """Creates the asset directory if it is missing

    :return shapesDefaultPath: The path of the control shapes directory
    :rtype shapesDefaultPath: str
    """
    userPrefsPath = str(preference.root("user_preferences"))
    assetsFolderPath = os.path.join(userPrefsPath, cc.ASSETS_FOLDER_NAME)
    shapesDefaultPath = os.path.join(assetsFolderPath, cc.SHAPES_FOLDER_NAME)

    if not os.path.isdir(shapesDefaultPath):  # check if directory actually exists
        os.makedirs(shapesDefaultPath)  # make directories

    # Check to see if there are old folder. Update if there are
    fileNameList = path.filesByExtension(shapesDefaultPath, [cc.CONTROL_SHAPE_EXTENSION])
    for zooSceneFile in fileNameList:
        zooscenefiles.updateOldFolders(zooSceneFile, shapesDefaultPath)

    # Copy default over if not found
    copyDefaultControlShapes(shapesDefaultPath)
    return shapesDefaultPath


def copyDefaultControlShapes(shapesDefaultPath):
    """Copies the default control shapes to the zoo_preferences/assets location"""
    controlShapesInternalPath = defaultControlsPath()
    filesystem.copyDirectoryContents(controlShapesInternalPath, shapesDefaultPath)


def defaultControlsPath():
    """ Get the default controls path

    :return controlShapesInternalPath: internal path of the zoo_controls_joints/preferences/assets/control_shapes dir
    :rtype controlShapesInternalPath: str
    """
    currentPath = os.path.abspath(__file__)
    packagePath = filesystem.upDirectory(currentPath, depth=5)
    return os.path.join(packagePath, "preferences", cc.ASSETS_FOLDER_NAME, cc.SHAPES_FOLDER_NAME)


def buildUpdateControlsJointsPrefs(prefsData):
    """Creates the control shape folder if it doesn't exist

    1. Creates if it doesn't exist:
        userPath/zoo_preferences/assets/control_shapes

    2. Checks the json data is valid, if not updates the data to defaults if directories aren't found
    """
    shapesDefaultPath = buildControlsDirectories()
    save = False
    # Check valid folders in the .prefs JSON data
    if not prefsData["settings"][cc.PREFS_KEY_CONTROL_SHAPES]:  # if empty then make default path
        prefsData["settings"][cc.PREFS_KEY_CONTROL_SHAPES] = shapesDefaultPath  # set default location
        save = True
    elif not os.path.isdir(prefsData["settings"][cc.PREFS_KEY_CONTROL_SHAPES]):  # json directory not found
        prefsData["settings"][cc.PREFS_KEY_CONTROL_SHAPES] = shapesDefaultPath  # set default location
        save = True
    if save:
        prefsData.save(indent=True)  # save format nicely
    return prefsData
