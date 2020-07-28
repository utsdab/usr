import os

from zoo.libs.utils import filesystem
from zoo.preferences.core import preference
from zoo.apps.shader_tools import shaderconstants as sc


def buildShaderAssetDirectories():
    """Creates the asset directory if it is missing

    :return shaderPresetDefaultPath: The path of the assets directory
    :rtype shaderPresetDefaultPath: str
    """
    userPrefsPath = str(preference.root("user_preferences"))
    assetsFolderPath = os.path.join(userPrefsPath, sc.ASSETS_FOLDER_NAME)
    shaderPresetDefaultPath = os.path.join(assetsFolderPath, sc.SHADERPRESETS_FOLDER_NAME)

    if not os.path.isdir(shaderPresetDefaultPath):  # check if directory actually exists
        os.makedirs(shaderPresetDefaultPath)  # make directories

    # Copy default over if not found
    copyDefaultControlShapes(shaderPresetDefaultPath)

    return shaderPresetDefaultPath


def buildUpdateShaderAssetPrefs(prefsData):
    """Creates the assets folders if they don't exist

    1. Creates if they don't exist:
        userPath/zoo_preferences/assets/shaders

    2. Checks the json data is valid, if not updates the data to defaults if directories aren't found
    """
    shaderPresetsDefaultPath = buildShaderAssetDirectories()
    save = False
    # Check valid folders in the .prefs JSON data
    settingsDict = prefsData["settings"]
    if not settingsDict[sc.PREFS_KEY_SHADERPRESETS]:  # if empty then make default path
        settingsDict[sc.PREFS_KEY_SHADERPRESETS] = shaderPresetsDefaultPath  # set default location
        save = True
    elif not os.path.isdir(settingsDict[sc.PREFS_KEY_SHADERPRESETS]):  # json directory not found
        settingsDict[sc.PREFS_KEY_SHADERPRESETS] = shaderPresetsDefaultPath  # set default location
        save = True
    if save:
        prefsData.save(indent=True)  # save format nicely
    return prefsData


def copyDefaultControlShapes(shadersUserPath):
    """Copies the default control shapes to the zoo_preferences/assets location"""
    shaderPresetsInternalPath = defaultShaderPresetsPath()
    filesystem.copyDirectoryContents(shaderPresetsInternalPath, shadersUserPath)


def defaultShaderPresetsPath():
    """ Get the default controls path

    :return shaderPresetsInternalPath: directory path of the internal zoo_shader_tools/preferences/assets/shaders dir
    :rtype shaderPresetsInternalPath: str
    """
    currentPath = os.path.abspath(__file__)
    packagePath = filesystem.upDirectory(currentPath, depth=5)  # relative to the current .py location up 5 dirs
    return os.path.join(packagePath, "preferences", sc.ASSETS_FOLDER_NAME, sc.SHADERPRESETS_FOLDER_NAME)