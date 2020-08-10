import os
from zoo.preferences.core import preference
from zoo.apps.model_assets import assetconstants


def buildModelAssetDirectories():
    """Creates the asset directory if it is missing

    :return modelDefaultPath: The path of the assets directory
    :rtype modelDefaultPath: str
    """
    userPrefsPath = str(preference.root("user_preferences"))
    assetsFolderPath = os.path.join(userPrefsPath, assetconstants.ASSETS_FOLDER_NAME)
    modelDefaultPath = os.path.join(assetsFolderPath, assetconstants.MODEL_FOLDER_NAME)

    if not os.path.isdir(modelDefaultPath):  # check if directory actually exists
        os.makedirs(modelDefaultPath)  # make directories
    return modelDefaultPath


def buildUpdateModelAssetPrefs(prefsData):
    """Creates the assets folders if they don't exist

    1. Creates if they don't exist:
        userPath/zoo_preferences/assets/light_suite_ibl_skydomes
        userPath/zoo_preferences/assets/light_suite_light_presets

    2. Checks the json data is valid, if not updates the data to defaults if directories aren't found
    """
    modelDefaultPath = buildModelAssetDirectories()
    save = False
    # Check valid folders in the .prefs JSON data
    if not prefsData["settings"][assetconstants.PREFS_KEY_MODEL_ASSETS]:  # if empty then make default path
        prefsData["settings"][assetconstants.PREFS_KEY_MODEL_ASSETS] = modelDefaultPath  # set default location
        save = True
    elif not os.path.isdir(prefsData["settings"][assetconstants.PREFS_KEY_MODEL_ASSETS]):  # json directory not found
        prefsData["settings"][assetconstants.PREFS_KEY_MODEL_ASSETS] = modelDefaultPath  # set default location
        save = True
    if save:
        prefsData.save(indent=True)  # save format nicely
    return prefsData

