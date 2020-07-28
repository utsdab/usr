"""
Startup function:

    builds the default control shapes directory if it doesn't exist

"""
import logging

from zoo.libs.utils.general import compareDictionaries
from zoo.preferences.core import preference

logger = logging.getLogger("Upgrade artist palette prefs")


def startup(package):
    """Upgrades the prefs file JSON if needed
    """
    updatePrefsKeys()


def updatePrefsKeys():
    """Updates .prefs keys if they are missing.  Useful for upgrading existing preferences

    Will only be needed if upgrading from Zoo 2.2.5 or lower"""
    artistPrefsLocalData = preference.findSetting("prefs/maya/artistpalette.pref", None)  # artistpalette .prefs info
    artistPrefsDefaultData = preference.defaultPreferenceSettings("zoo_artist_palette", "maya/artistpalette")
    # Force upgrade if needed
    artistPrefsLocalDict = checkUpgradePrefs(artistPrefsLocalData, artistPrefsDefaultData)
    if not artistPrefsLocalDict:  # Is already ok
        return
    # Do the compare on dictionaries
    target, messageLog = compareDictionaries(artistPrefsDefaultData["settings"], artistPrefsLocalDict)
    if messageLog:  # if keys have been updated
        artistPrefsLocalData.save(indent=True, sort=True)
        logger.info(messageLog)


def checkUpgradePrefs(localData, defaultData):
    """Checks for new keys in the users artistpalette.pref file

    :param localData: The preference object for local camera_tools data in zoo_preferences
    :type localData:
    :return controlsLocalDict: The settings dictionary locally in zoo_preferences, now potentially updated
    :rtype controlsLocalDict: dict
    """
    try:
        x = localData["isActiveAtStartup"]  # if this exists is cool
        return dict()
    except:  # Needs upgrading, or is a fresh install
        if 'settings' in localData:  # needs upgrading
            return localData["settings"]
        return dict()  # is a fresh install so ignore

