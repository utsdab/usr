import os
import shutil
import json
import time
import glob

from shutil import copyfile
from os.path import basename
from os.path import splitext
from os.path import dirname

import maya.cmds as cmds

from zoo.apps.hotkeyeditor.core import const as c
from zoo.libs.utils import zlogging
from zoo.preferences.core import preference

timeTest = 0

logger = zlogging.getLogger(__name__)


def hotkeyPathUserPrefs():
    """Returns the path of the user hotkey path

    Return Example:
        "C:/Users/username/Documents/zoo_preferences/prefs/maya/zoo_hotkey_editor"

    """
    return os.path.join(str(preference.root("user_preferences")), c.RELATIVE_USERPREFS_PATH)


def hotkeyPathInternalPrefs():
    """Returns the path of the zoo tools internal hotkey path

    Return Example:
        "D:/somepath/zootools_pro/packages/zoo_hotkey_editor/preferences/prefs/maya"

    """
    return os.path.join(str(preference.packagePreferenceLocation(c.PREF_FOLDER_NAME)), c.RELATIVE_INTERNAL_PATH)


def deleteSet(setName):
    """
    Deletes the set if it already exists
    :param setName:
    :return:
    """
    exists = cmds.hotkeySet(setName, exists=1)
    if exists:
        return cmds.hotkeySet(setName, e=1, delete=1)

    return False


def currentMayaSet():
    return cmds.hotkeySet(q=1, current=1)


def exportKeySet(keySet='', filePath=''):
    """
    Exports the keyset, save to a default location with the current keyset
    if none is given
    :param keySet:
    :param filePath: The exact file path location
    :return:
    """

    if keySet == '':
        keySet = cmds.hotkeySet(current=1, q=1)

    if filePath == '':
        filePath = "{}hotkeys/tmp/{}.mhk".format(c.USERPREF, keySet)

        # Make directory
        dir = "{}hotkeys/tmp/".format(c.USERPREF)

        import os
        if not os.path.exists(dir):
            os.makedirs(dir)

    cmds.hotkeySet(keySet, export=filePath, e=1)

    return filePath


def removeBrackets(bstr):
    """
    Turns "(Hello world)" to "Hello World"
    We don't want to use strip() as it takes off too many characters
    :param bstr: String to remove the brackets from
    :return: The string with the operation applied to
    """

    if bstr is None:
        return None

    if not len(bstr) > 0:
        return bstr

    if bstr[0] == "(" and bstr[-2:] == ");":
        bstr = bstr[1:-2]
    elif bstr[0] == "(" and bstr[-1] == ")":
        bstr = bstr[1:-1]

    return bstr


def getKeySetFromPath(path):
    """
    Helper method to get keyset from path

    :param path: Path
    :return:
    """
    last = path.split("/")[-1]

    if ".mhk" not in last:
        print ("mhk not found in path!")
        return False

    return last.strip().replace(".mhk", "")


def importKeySet(path, override=True):
    """
    Imports the keyset from the mhk file
    :param path: Directory path, not including the file

    """
    keyset = getKeySetFromPath(path)

    # Delete hotkeys if it already exists
    if (deleteSet(keyset) and override):
        print("Deleting set {}".format(keyset))

    cmds.hotkeySet(e=1, ip=path)


def sortedIgnoreCase(li):
    return sorted(li, key=lambda s: s.lower())


def outputJSON(data, fileLoc):
    """
    Outputs the data into a json file

    :param data: The dict to output as json
    :param fileLoc: File location
    """
    jdumps = json.dumps(data, indent=4)

    fileW = open(fileLoc, "w")

    fileW.write(str(jdumps))
    fileW.close()


def toRuntimeStr(s):
    """
    Removes spaces and sets camel case
    :param s:
    :return:
    """
    return camelToSpaces(s).title().replace(" ", "")


def getFileName(filepath, ext=False):
    """
    Extracts the filename from the string.
    "/path/to/file/fileName.json" ===> "fileName"

    :param filepath: The filepath as a string
    :param ext: True to return the file with the extension, false to return with filename only
    :return: The filename
    """
    base = basename(filepath)

    # Remove the extension
    if ext is False:
        return splitext(base)[0]

    return base


def runtimeCmdExists(cmd, checkDefault=True):
    """ Check if runtime command exists in maya

    :param cmd:
    :param checkDefault:
    :return:
    """

    if cmds.runTimeCommand(cmd, exists=1, q=1):
        if checkDefault:
            return cmds.runTimeCommand(cmd, d=1, q=1)

        return True

    return False


def getMayaRuntimeCommand(cmd):
    ret = None, None
    if cmds.runTimeCommand(cmd, exists=1, q=1) and cmds.runTimeCommand(cmd, d=1, q=1):
        ret = (cmds.runTimeCommand(cmd, q=1, command=1), cmds.runTimeCommand(cmd, q=1, commandLanguage=1))
    else:
        return ret

    return ret


def getDefaultRuntimeCmdsList():
    defaultRtcs = cmds.runTimeCommand(defaultCommandArray=1, q=1)
    return defaultRtcs


def pprint(s):
    import pprint
    pprint.pprint(s)


def camelToSpaces(s):
    import re
    splitted = re.sub('(?!^)([A-Z][a-z]+)', r' \1', s).split()

    ret = ' '.join(splitted).replace("_", " ").replace("  ", " ").title()
    return ret


def getDirPath(filepath):
    return dirname(filepath)


def removePrefix(prefix, remStr):
    if prefix == remStr[:len(prefix)]:
        return remStr[len(prefix):]
    return remStr


def hasPrefix(prefix, val):
    if prefix == val[:len(prefix)]:
        return True
    return False


def backupFile(filePath, backupDir="backup", timestamp=True, max=10):
    import os

    path = getDirPath(filePath)

    if timestamp:
        timestamp = time.strftime("_%Y-%m-%d_%H%M%S")

    # Check if backup directory exists
    bakDir = "{}/{}".format(path, backupDir)
    if not os.path.exists(bakDir):
        os.makedirs(bakDir)

    # Only do it if the original file exists, and there's no bak file with the same name
    dst = "{}/{}/{}{}.bak".format(path, backupDir, getFileName(filePath), timestamp)
    if os.path.isfile(filePath) and not os.path.isfile(dst):
        copyfile(filePath, dst)

    # Delete if more than max
    files = glob.glob("{}/{}/{}_*.bak".format(path, backupDir, getFileName(filePath)))
    if len(files) > max:
        for f in files[max:]:
            os.remove(f)


def copyFile(destPath, origPath, extension=None):
    """ Copies file across if doesn't exist

    :param destPath:
    :param original:
    :return:
    """
    destPath += extension
    origPath += extension

    if not os.path.isfile(destPath):
        if not os.path.exists(os.path.dirname(destPath)):
            os.makedirs(os.path.dirname(destPath))
        shutil.copyfile(origPath, destPath)
        return True
    return False


def deleteKeySets():
    for k in c.KEYSETS:
        cmds.hotkeySet(k, delete=1, e=1)


def deleteAllMayaKeysets():
    li = cmds.hotkeySet(q=1, hotkeySetArray=1)
    for l in li:
        cmds.hotkeySet(l, e=1, delete=1)


def mayaKeySetExists(keySetName):
    return cmds.hotkeySet(keySetName, exists=1, q=1)


def cleanScript(script):
    """
    Cleans the python script for the UI

    :param script:
    :return:
    """
    return script.replace('\\n', '\n').replace('\\t', '    ').strip()


def setAdminMode(adminMode):
    """

    :param adminMode:
    :type adminMode:
    :return:
    :rtype:
    """
    logger.info("Admin Mode set to {}".format(str(adminMode)))
    if adminMode:
        os.environ["ZOO_ADMIN"] = "1"
    else:
        os.environ["ZOO_ADMIN"] = "0"


def isAdminMode():
    """Is the admin mode on or off so the user can make changes.

    Returns True if os.environ["ZOO_ADMIN"] == "1"
    Note: The environ variable must be a string and set to "1"
    If set to "True" or 1, or "true" will return False
    Exception Maya startup in a .bat file is:
        set ZOO_ADMIN=1

    :return result: Returns True if the os.environ["ZOO_ADMIN"] == "1" must be a string not "True" or 1
    :rtype result: bool
    """
    try:
        if os.environ["ZOO_ADMIN"] == "1":
            return True
    except KeyError:
        os.environ["ZOO_ADMIN"] = "0"
    return False
