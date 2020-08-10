"""
Startup function:

    Builds the default asset directories if they don't exist
    Updates .pref dictionary keys if any are missing

"""

from zoo.apps.camera_tools import cameradirectories
from zoo.libs.utils.general import compareDictionaries
from zoo.preferences.core import preference
from zoo.apps.camera_tools import cameraconstants as cc
from zoo.libs.utils import zlogging
logger = zlogging.getLogger("Zoo Camera Tools Startup")


def startup(package):
    """Creates the assets folders if they don't exist

    1. Creates folder if it doesn't exist:
        userPath/zoo_preferences/assets/image_planes

    2. Upgrades .pref to "settings" if upgrading from 2.2.3 or lower

    3. Updates .pref dictionary keys if any are missing
    """
    cameradirectories.buildCameraAssetDirectories()
    updatePrefsKeys()


def updatePrefsKeys():
    """Updates .prefs keys if they are missing.  Useful for upgrading existing preferences"""
    cameraToolsLocalData = preference.findSetting(cc.RELATIVE_PREFS_FILE, None)  # camera .prefs info
    cameraToolsDefaultData = preference.defaultPreferenceSettings("zoo_camera_tools", "maya/zoo_camera_tools")
    # Force upgrade if needed
    camToolsLocalDict = checkUpgradePrefs(cameraToolsLocalData, cameraToolsDefaultData)
    if not camToolsLocalDict:  # Will straight copy across the prefs file or is cool
        return
    # Do the compare on dictionaries
    target, messageLog = compareDictionaries(cameraToolsDefaultData["settings"], camToolsLocalDict)
    if messageLog:  # if keys have been updated
        cameraToolsLocalData.save(indent=True, sort=True)
        logger.info(messageLog)


def checkUpgradePrefs(localData, defaultData):
    """Will upgrade the zoo_camera_tools.prefs file by overwriting if the "settings" key does not exist

    Will only be needed if upgrading from in Zoo 2.2.3 or lower

    :param localData: The preference object for local camera_tools data in zoo_preferences
    :type localData:
    :return camToolsLocalDict: The settings dictionary locally in zoo_preferences, now potentially updated
    :rtype camToolsLocalDict: dict
    """
    try:
        x = localData[cc.PREFS_KEY_IMAGEPLANE]  # if this exists may need upgrading
    except:  # can ignore as not old file
        return dict()
    try:
        camToolsLocalDict = localData["settings"]
        return camToolsLocalDict
    except:  # Upgrade from old prefs
        path = localData[cc.PREFS_KEY_IMAGEPLANE]  # old path
        localData["settings"] = defaultData["settings"]  # add settings
        localData["settings"][cc.PREFS_KEY_IMAGEPLANE] = path  # retain old path
        localData.save(indent=True, sort=True)
        logger.info("Upgraded user `Camera Tools` settings")
        return localData["settings"]

