"""
Startup function:

    builds the default asset directories if they don't exist

"""
import logging

from zoo.apps.model_assets import assetdirectories
from zoo.libs.utils.general import compareDictionaries
from zoo.preferences.core import preference
from zoo.apps.model_assets import assetconstants as ac

logger = logging.getLogger("Zoo Model Assets Startup")


def startup(package):
    """Creates the assets folders if they don't exist

    1. Creates folder if it doesn't exist:
        userPath/zoo_preferences/assets/model_assets

    2. Upgrades .pref to "settings" if upgrading from 2.2.3 or lower

    3. Updates .pref dictionary keys if any are missing"""


    assetdirectories.buildModelAssetDirectories()
    updatePrefsKeys()


def updatePrefsKeys():
    """Updates .prefs keys if they are missing.  Useful for upgrading existing preferences"""
    modelAssetsLocalData = preference.findSetting(ac.RELATIVE_PREFS_FILE, None)  # camera .prefs info
    modelAssetsDefaultData = preference.defaultPreferenceSettings("zoo_model_assets", "maya/zoo_model_assets")
    # Force upgrade if needed
    modelAssetsLocalDict = checkUpgradePrefs(modelAssetsLocalData, modelAssetsDefaultData)
    if not modelAssetsLocalDict:  # Will straight copy across the prefs file or is cool
        return
    # Do the compare on dictionaries
    target, messageLog = compareDictionaries(modelAssetsDefaultData["settings"], modelAssetsLocalDict)
    if messageLog:  # if keys have been updated
        modelAssetsLocalData.save(indent=True, sort=True)
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
        x = localData[ac.PREFS_KEY_MODEL_ASSETS]  # if this exists may need upgrading
    except:  # can ignore as not old file
        return dict()
    # File could be old so possibly upgrade
    try:
        assetsLocalDict = localData["settings"]
        return assetsLocalDict
    except:  # Upgrade from old prefs
        path = localData[ac.PREFS_KEY_MODEL_ASSETS]  # old path
        localData["settings"] = defaultData["settings"]  # add settings
        localData["settings"][ac.PREFS_KEY_MODEL_ASSETS] = path  # retain old path
        localData.save(indent=True, sort=True)
        logger.info("Upgraded user `Model Assets` settings")
        return localData["settings"]

