import os


from zoo.preferences.core import preference
from zoo.apps.camera_tools import cameraconstants


def buildCameraAssetDirectories():
    """Creates the asset directory if it is missing

    :return imagePlaneDefaultPath: The path of the assets directory
    :rtype imagePlaneDefaultPath: str
    """
    userPrefsPath = str(preference.root("user_preferences"))
    assetsFolderPath = os.path.join(userPrefsPath, cameraconstants.ASSETS_FOLDER_NAME)
    imagePlaneDefaultPath = os.path.join(assetsFolderPath, cameraconstants.IMAGEPLANE_FOLDER_NAME)

    if not os.path.isdir(imagePlaneDefaultPath):  # check if directory actually exists
        os.makedirs(imagePlaneDefaultPath)  # make directories

    return imagePlaneDefaultPath


def buildUpdateCameraAssetPrefs(prefsData):
    """Creates the assets folders if they don't exist

    1. Creates if they don't exist:
        userPath/zoo_preferences/assets/image_planes

    2. Checks the json data is valid, if not updates the data to defaults if directories aren't found
    """
    imagePlaneDefaultPath = buildCameraAssetDirectories()
    save = False
    # Check valid folders in the .prefs JSON data
    settingsDict = prefsData["settings"]
    if not settingsDict[cameraconstants.PREFS_KEY_IMAGEPLANE]:  # if empty then make default path
        settingsDict[cameraconstants.PREFS_KEY_IMAGEPLANE] = imagePlaneDefaultPath  # set default location
        save = True
    elif not os.path.isdir(settingsDict[cameraconstants.PREFS_KEY_IMAGEPLANE]):  # json directory not found
        settingsDict[cameraconstants.PREFS_KEY_IMAGEPLANE] = imagePlaneDefaultPath  # set default location
        save = True
    if save:
        prefsData.save(indent=True)  # save format nicely
    return prefsData

