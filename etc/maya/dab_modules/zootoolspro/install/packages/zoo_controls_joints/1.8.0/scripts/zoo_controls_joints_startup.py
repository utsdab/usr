"""
Startup function:

    builds the default control shapes directory if it doesn't exist

"""
import logging

from zoo.apps.controls_joints import controlsdirectories
from zoo.libs.utils.general import compareDictionaries
from zoo.preferences.core import preference
from zoo.apps.controls_joints import controlsjointsconstants as cc

logger = logging.getLogger("Zoo Controls Joints Startup")


def startup(package):
    """Creates the assets folders if they don't exist

    Creates folder if it doesn't exist:
        userPath/zoo_preferences/assets/control_shapes
    """
    controlsdirectories.buildControlsDirectories()
    updatePrefsKeys()


def updatePrefsKeys():
    """Updates .prefs keys if they are missing.  Useful for upgrading existing preferences"""
    controlsJointsLocalData = preference.findSetting(cc.RELATIVE_PREFS_FILE, None)  # camera .prefs info
    controlsJointsDefaultData = preference.defaultPreferenceSettings("zoo_controls_joints", "maya/zoo_controls_joints")
    # Force upgrade if needed
    controlsLocalDict = checkUpgradePrefs(controlsJointsLocalData, controlsJointsDefaultData)
    if not controlsLocalDict:  # Will straight copy across the prefs file or is cool
        return
    # Do the compare on dictionaries
    target, messageLog = compareDictionaries(controlsJointsDefaultData["settings"], controlsLocalDict)
    if messageLog:  # if keys have been updated
        controlsJointsLocalData.save(indent=True, sort=True)
        logger.info(messageLog)


def checkUpgradePrefs(localData, defaultData):
    """Will upgrade the zoo_camera_tools.prefs file by overwriting if the "settings" key does not exist

    Will only be needed if upgrading from in Zoo 2.2.3 or lower

    :param localData: The preference object for local camera_tools data in zoo_preferences
    :type localData:
    :return controlsLocalDict: The settings dictionary locally in zoo_preferences, now potentially updated
    :rtype controlsLocalDict: dict
    """
    try:
        x = localData[cc.PREFS_KEY_CONTROL_SHAPES]  # if this exists may need upgrading
    except:  # can ignore as not old file
        return dict()
    try:
        controlsLocalDict = localData["settings"]
        return controlsLocalDict
    except:  # Upgrade from old prefs
        path = localData[cc.PREFS_KEY_CONTROL_SHAPES]  # old path
        localData["settings"] = defaultData["settings"]  # add settings
        localData["settings"][cc.PREFS_KEY_CONTROL_SHAPES] = path  # retain old path
        localData.save(indent=True, sort=True)
        logger.info("Upgraded user `Camera Tools` settings")
        return localData["settings"]


