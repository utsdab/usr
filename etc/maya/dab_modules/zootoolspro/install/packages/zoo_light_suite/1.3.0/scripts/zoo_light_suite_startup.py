"""
Startup function:

    builds the default asset directories if they don't exist

"""
import logging

from zoo.preferences.core import preference
from zoo.libs.utils.general import compareDictionaries
from zoo.apps.light_suite import assetdirectories
from zoo.apps.light_suite import lightconstants as lc

logger = logging.getLogger("Zoo Light Suite Startup")


def startup(package):
    """Creates the assets folders if they don't exist
    1. Creates folder if it doesn't exist:
        userPath/zoo_preferences/assets/light_suite_ibl_skydomes
        userPath/zoo_preferences/assets/light_suite_light_presets

    2. Upgrades .pref to "settings" if upgrading from 2.2.3 or lower

    3. Updates .pref dictionary keys if any are missing
    """
    assetdirectories.buildAssetDirectories()
    updatePrefsKeys()


def updatePrefsKeys():
    """Updates .prefs keys if they are missing.  Useful for upgrading existing preferences"""
    lightLocalData = preference.findSetting("prefs/maya/zoo_light_suite.pref", None)  # light .prefs info
    # print "lightLocalData settings", lightLocalData["settings"]
    lightDefaultData = preference.defaultPreferenceSettings("zoo_light_suite", "maya/zoo_light_suite")
    # Force upgrade if needed
    lightLocalDict = checkUpgradePrefs(lightLocalData, lightDefaultData)
    if not lightLocalDict:  # Will straight copy across the prefs file or is cool
        return
    # Do the compare on dictionaries
    target, messageLog = compareDictionaries(lightDefaultData["settings"], lightLocalDict)
    if messageLog:  # if keys have been updated
        lightLocalData.save(indent=True, sort=True)
        logger.info(messageLog)


def checkUpgradePrefs(localData, defaultData):
    """Will upgrade the zoo_model_assets.prefs file by overwriting if the "settings" key does not exist

    Will only be needed if upgrading from in Zoo 2.2.3 or lower

    :param localData: The preference object for local model_assets data in zoo_preferences
    :type localData:
    :return camToolsLocalDict: The settings dictionary locally in zoo_preferences, now potentially updated
    :rtype assetsLocalDict: dict
    """
    try:
        x = localData[lc.PREFS_KEY_PRESETS]  # if this exists may need upgrading
    except:  # can ignore as not old file
        return dict()
    # File could be old so possibly upgrade
    try:
        assetsLocalDict = localData["settings"]
        return assetsLocalDict  # is ok, settings exist
    except:  # Upgrade from old prefs
        presetPath = localData[lc.PREFS_KEY_PRESETS]  # old path
        iblPath = localData[lc.PREFS_KEY_IBL]  # old path
        localData["settings"] = defaultData["settings"]  # add settings
        localData["settings"][lc.PREFS_KEY_PRESETS] = presetPath  # retain old path
        localData["settings"][lc.PREFS_KEY_IBL] = iblPath  # retain old path
        localData.save(indent=True, sort=True)
        logger.info("Upgraded user `Light Suite` settings")
        return localData["settings"]


