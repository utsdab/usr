import os
import glob

from zoo.libs.maya.cmds.renderer import exportglobals
from zoo.preferences.core import preference
from zoo.apps.light_suite import lightconstants as lc

LIGHTS = exportglobals.LIGHTS
PRESETSUFFIX = [exportglobals.ZOOSCENESUFFIX]


class LightSuitePreferences(object):
    """Class for extracting specific Light Suite Preferences information such as hdr image and light preset files.

    Note: This class uses the self.prefsData object to retrieve zoo preferences .pref (json) information.
    See zoo.preferences.core.PreferenceManager for more documentation on the prefsData object

    Use:
        from zoo.apps.light_suite import prefsdata
        prefsDataInstance = prefsdata.LightSuitePreferences()
        something = prefsDataInstance.runSomeMethod()

    Get:
        prefsData = prefsDataInstance.prefsData()  # the dataObject itself
        iblSkydomeImageList = prefsDataInstance.iblSkydomeImageList()
        iblSkydomeFileExtList = prefsDataInstance.iblSkydomeExtensionList()
        lightPresetsFileList = prefsDataInstance.runMethod()

    Refresh the instance with:
        prefsDataInstance.refreshPrefsData()

    """
    def __init__(self):
        """Get the latest light suite .prefs info as a data object
        """
        self.refreshPrefsData()

    def getPrefsData(self):
        """Returns the zoo prefs data interface object for the light suite preferences .pref (json).

        The returned object can be used like a dict but also for other functions such as saving the .pref file and more.

        See zoo.preferences.core.PreferenceManager for more documentation
        """
        return self.prefsData

    def getUpdatedPrefsData(self):
        """Returns the updated (refreshed) zoo prefs data interface object for the light suite preferences .pref (json).

        The returned object can be used like a dict but also for other functions such as saving the .pref file and more.

        See zoo.preferences.core.PreferenceManager for more documentation
        """
        self.refreshPrefsData()
        return self.prefsData

    def refreshPrefsData(self):
        """Refreshes the preferences data internally in case of changes from the time the instance was created.

        Should be used if calling the class instance where changes to the prefs may have been made after instance \
        creation"""
        self.prefsData = preference.findSetting(lc.RELATIVE_PREFS_FILE, None)  # get latest .prefs info

    def iblSkydomeExtensionList(self, ignoreTxTex=False):
        """returns the current ibl image extension list

        Return Example:
            ["hdr", "tif", "tiff", "hdri", "exr", "ibl"]

        :param ignoreTxTex: If True do not return "tx" or "tex" file extensions
        :type ignoreTxTex: bool
        :return iblSkydomeExtensionList: A list of the current ibl skydome extensions in use from the preferences
        :rtype iblSkydomeExtensionList: list(str)
        """
        iblSkydomeExtensionList = list()
        if self.prefsData[lc.PREFS_KEY_EXR]:
            iblSkydomeExtensionList.append("exr")
        if self.prefsData[lc.PREFS_KEY_HDR]:
            iblSkydomeExtensionList.append("hdr")
            iblSkydomeExtensionList.append("hdri")
        if self.prefsData[lc.PREFS_KEY_TIF]:
            iblSkydomeExtensionList.append("tif")
            iblSkydomeExtensionList.append("tiff")
        if self.prefsData[lc.PREFS_KEY_TEX] and not ignoreTxTex:
            iblSkydomeExtensionList.append("tex")
        if self.prefsData[lc.PREFS_KEY_TX] and not ignoreTxTex:
            iblSkydomeExtensionList.append("tx")
        return iblSkydomeExtensionList

    def iblSkydomeImageList(self, ignoreTxTex=False):
        """Lists all the images inside of the prefs IBL directory.
        Automatically filters images by the Hdr image types given in the preferences.

        Return Example:
            ["HDRIHaven_autoshop_01.hdr", "HDRI-SKIES_Sky092.exr", "HDRLabs_StadiumCenter.tif"]

        :param ignoreTxTex: If True do not return "tx" or "tex" file extensions
        :type ignoreTxTex: bool
        :return iblImageList: List of the IBL images inside of the iblQuickDir
        :rtype iblImageList: list
        """
        iblFolder = self.prefsData[lc.PREFS_KEY_IBL]
        iblImageList = list()
        imageExtList = self.iblSkydomeExtensionList(ignoreTxTex=ignoreTxTex)
        if not os.path.isdir(iblFolder):  # check if directory actually exists
            return iblImageList
        for ext in imageExtList:  # find images in directory
            for filePath in glob.glob(os.path.join(iblFolder, "*.{}".format(ext))):
                iblImageList.append(os.path.basename(filePath))
        return iblImageList

    def lightPresetDirectory(self):
        return self.prefsData[lc.PREFS_KEY_PRESETS]

    def lightPresetZooSceneList(self):
        """Lists all of the light presets inside the Light Presets directory
        The light presets are files each with a single scene light setup

        Return Example:
            ["soft_sunsetSides.zooScene", "sun_redHarsh.zooScene", "sun_warmGlow.zooScene"]

        :return presetList: A list of .zooScene files each with a single scene light setup
        :rtype presetList: list(str)
        """
        lightPresetFolder = self.prefsData[lc.PREFS_KEY_PRESETS]
        lightPresetList = list()
        if not os.path.isdir(lightPresetFolder):  # check if directory actually exists
            return lightPresetList  # emptyList and directory
        for ext in PRESETSUFFIX:
            for filePath in glob.glob(os.path.join(lightPresetFolder, "*.{}".format(ext))):
                lightPresetList.append(os.path.basename(filePath))
        return lightPresetList

