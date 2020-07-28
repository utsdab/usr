import glob, os

from zoo.libs.utils import filesystem

from zoo.libs.maya.cmds.renderer import exportglobals

LIGHTS = exportglobals.LIGHTS


IBLFILESUFFIXTYPES = ("hdr", "tif", "tiff", "hdri", "exr", "ibl")
PRESETSUFFIX = [exportglobals.ZOOSCENESUFFIX]

LIGHTFILEPATHPRESETS = "lightpresets.json"

IBLQUICKDIRKEY = "iblQuickDir"
PRESETQUICKDIR = "presetQuickDir"


def getLightPresetDict(filename=LIGHTFILEPATHPRESETS):
    """Retrieves the preset dictionary from the .json file of the saved filepaths for the quick directory
    The preset dictionary only contains the file paths of the IBL and light preset

    :param filename: the name of the preset file
    :type filename: str
    :return presetLightFilePathDict: The preset shader dictionary
    :rtype presetLightFilePathDict: dict
    """
    jsonShaderFilePath = os.path.join(os.path.dirname(__file__), filename)
    return filesystem.loadJson(jsonShaderFilePath)


def writeLightPresetDict(presetLightFilePathDict):
    """Writes the preset shader dict to a .json file

    :param presetLightsDict: The preset shader dictionary
    :type presetLightsDict: dict
    """
    jsonFilePath = os.path.join(os.path.dirname(__file__), LIGHTFILEPATHPRESETS)
    filesystem.saveJson(presetLightFilePathDict, jsonFilePath)


def listIblQuickDirImages():
    """Lists all the images inside of the "iblQuickDir"

    :return iblList: List of the IBL images inside of the iblQuickDir
    :rtype iblList: list
    :return iblQuickDir: The file path of the IBL directory
    :rtype iblQuickDir: str
    """
    presetLightDict = getLightPresetDict()
    iblList = list()
    if not presetLightDict[IBLQUICKDIRKEY]:
        return iblList, presetLightDict[IBLQUICKDIRKEY]  # emptyList
    if not os.path.isdir(presetLightDict[IBLQUICKDIRKEY]):  # check if directory actually exists
        return iblList, ""
    os.chdir(presetLightDict[IBLQUICKDIRKEY])
    for ext in IBLFILESUFFIXTYPES:  # find images in directory
        for file in glob.glob("*.{}".format(ext)):
            iblList.append(file)
    return iblList, presetLightDict[IBLQUICKDIRKEY]


def listQuickDirPresets():
    """Lists all of the light presets inside of the "presetQuickDir" directory
    The light presets are files each with a single scene light setup

    :return presetList: A list of .json files each with a single scene light setup
    :rtype presetList: list
    :return presetQuickDir: The full file path of the light preset directory
    :rtype presetQuickDir: str
    """
    presetLightDict = getLightPresetDict()
    presetList = list()
    if not presetLightDict[PRESETQUICKDIR]:
        return presetList, presetLightDict[PRESETQUICKDIR]  # emptyList
    if not os.path.isdir(presetLightDict[PRESETQUICKDIR]):  # check if directory actually exists
        return presetList, ""  # emptyList and directory
    os.chdir(presetLightDict[PRESETQUICKDIR])
    for ext in PRESETSUFFIX:
        for fileName in glob.glob("*.{}".format(ext)):
            presetList.append(fileName)
    return presetList, presetLightDict[PRESETQUICKDIR]


