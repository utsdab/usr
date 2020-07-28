import maya.cmds as cmds
from zoo.apps.hotkeyeditor.core import const as c
from zoo.apps.hotkeyeditor.core import hotkeys
from zoo.apps.hotkeyeditor.core import utils
import glob
import os
import logging

logger = logging.getLogger(__name__)


def parseMHK(mhkStr):
    """
    :param mhkStr:
    :return:
    """
    # Use Regex to get all the commands in the file
    import re
    regex = r"(^runTimeCommand.*?;$)|(^nameCommand.*?;$)|(^hotkeySet .*?;$)|(^hotkey .*?;$)|(^hotkeyCtx.*?;$)"

    matches = re.finditer(regex, mhkStr, re.MULTILINE | re.DOTALL)
    mhkCommands = []

    for matchNum, match in enumerate(matches):
        mhkCommands.append(match.group())

    # Put the matched data into an MHKCommand object
    mayaDefault = []
    for r in mhkCommands:
        mayaDefault.append(hotkeys.MHKCommand(melStr=r))

    return mayaDefault


def saveMHKs():
    # Save the MHK files first
    for k in c.KEYSETS:
        saveLoc = os.path.join(utils.hotkeyPathUserPrefs(), k + ".mhk")
        cmds.hotkeySet(k, e=1, export=saveLoc)
        logger.debug("File saved to {}".format(saveLoc))


def saveHotkeys():
    # Now open those mhk files and save it as JSON
    for k in c.KEYSETS:
        keySet = os.path.join(utils.hotkeyPathUserPrefs(), k + ".mhk")
        with open(keySet, "r") as f:
            mhkStr = f.read()
            f.close()
            mhkCommands = parseMHK(mhkStr)
            # Use Regex to get all the commands in the file
            saveJSON(mhkCommands, k)


def saveJSON(commands, outName):
    outData = []
    for cmd in commands:
        outData.append(cmd.cmdAttrs)

    fileOut = os.path.join(utils.hotkeyPathUserPrefs(), outName + ".json")

    utils.outputJSON(outData, fileOut)


def loadFromMHK():
    for k in c.KEYSETS:

        if cmds.hotkeySet(k, exists=1):
            cmds.hotkeySet(k, e=1, delete=1)

        path = os.path.join(utils.hotkeyPathUserPrefs(), k + ".mhk")

        utils.importKeySet(path)

    # Set the hotkeys
    cmds.hotkeySet(c.DEFAULT_MAYA, current=1, e=1)


def load():
    loadFromMHK()


def deleteZooKeySets(deletePrefHotkeys=True):
    deleteMayaKeySets()
    deleteZooHotkeyJsons()

    if deletePrefHotkeys:
        deleteZooHotkeysFiles()


def deleteMayaKeySets():
    li = cmds.hotkeySet(q=1, hotkeySetArray=1)
    toDel = []
    for l in li:
        if l in c.KEYSETS:
            toDel.append(l)
        if utils.hasPrefix(c.KEYSET_PREFIX, l):
            toDel.append(l)

    for d in toDel:
        cmds.hotkeySet(d, e=1, delete=1)


def deleteZooHotkeyJsons():
    """
    Delete all the jsons files as well.

    :return:
    """
    files = glob.glob("{}/{}*.json".format(utils.hotkeyPathUserPrefs(), c.KEYSET_PREFIX))

    for f in files:
        os.remove(f)


def deleteZooHotkeysFiles():
    files = glob.glob("{}/*".format(utils.hotkeyPathUserPrefs()))
    removed = set()
    for f in files:
        try:
            if os.path.isfile(f):
                os.remove(f)
                removed.add(f)
            elif os.path.isdir(f):
                import shutil
                shutil.rmtree(f)
                removed.add(f)
        except OSError:
            logger.error("Failed to remove File: {}".format(f),
                         exc_info=True)

    return removed