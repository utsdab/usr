import os
from zoo.preferences.core import preference
from zoo.apps.light_suite import lightconstants as lc


def buildAssetDirectories():
    userPrefsPath = str(preference.root("user_preferences"))
    assetsFolderPath = os.path.join(userPrefsPath, lc.ASSETS_FOLDER_NAME)
    iblDefaultPath = os.path.join(assetsFolderPath, lc.IBL_SKYDOME_FOLDER_NAME)
    presetDefaultPath = os.path.join(assetsFolderPath, lc.LIGHT_PRESET_FOLDER_NAME)

    if not os.path.isdir(iblDefaultPath):  # check if directory actually exists
        os.makedirs(iblDefaultPath)  # make directories
    if not os.path.isdir(presetDefaultPath):  # check if directory actually exists
        os.makedirs(presetDefaultPath)  # make directories
    return presetDefaultPath, iblDefaultPath


def buildUpdateLightPrefs(prefsData):
    """Creates the assets folders if they don't exist

    1. Creates if they don't exist:
        userPath/zoo_preferences/assets/light_suite_ibl_skydomes
        userPath/zoo_preferences/assets/light_suite_light_presets

    2. Checks the json data is valid, if not updates the data to defaults if directories aren't found
    """
    presetDefaultPath, iblDefaultPath = buildAssetDirectories()
    save = False
    # Check valid folders in the .prefs JSON data
    if not prefsData["settings"][lc.PREFS_KEY_IBL]:  # if empty then make default path
        prefsData["settings"][lc.PREFS_KEY_IBL] = iblDefaultPath  # set default location
        save = True
    elif not os.path.isdir(prefsData["settings"][lc.PREFS_KEY_IBL]):  # json directory not found
        prefsData["settings"][lc.PREFS_KEY_IBL] = iblDefaultPath  # set default location
        save = True
    if not prefsData["settings"][lc.PREFS_KEY_PRESETS]:  # if empty then make default path
        prefsData["settings"][lc.PREFS_KEY_PRESETS] = presetDefaultPath
        save = True
    elif not os.path.isdir(prefsData["settings"][lc.PREFS_KEY_PRESETS]):  # .prefs json directory not found
        prefsData["settings"][lc.PREFS_KEY_PRESETS] = presetDefaultPath  # so set default location
        save = True
    if save:
        prefsData.save(indent=True)  # save format nicely
    return prefsData
