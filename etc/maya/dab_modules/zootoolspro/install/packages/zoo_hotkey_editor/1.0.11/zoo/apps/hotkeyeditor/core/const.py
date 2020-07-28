import os
import maya.cmds as cmds
from zoo.preferences.core import preference

DEFAULT_KEYSET = "Zoo_Tools_Default"
DEFAULT_MAYA = "Maya_Default_ZooMod"
DEFAULT_MAYA_NOZOO = "Maya_Default"
DEFAULT_TEMPLATE = "New_KeySet_Template"

KEYSET_PREFIX = "Zoo_User_"
KEYSETS = [DEFAULT_KEYSET, DEFAULT_MAYA]
USERPREF = cmds.internalVar(userPrefDir=1)
PREF_FOLDER_NAME = "zoo_hotkey_editor"

# relative paths of the main hotkeys folder, todo: both paths should be the same
RELATIVE_USERPREFS_PATH = "prefs/maya/{}".format(PREF_FOLDER_NAME)
RELATIVE_INTERNAL_PATH = "maya/{}".format(PREF_FOLDER_NAME)

SPECIALKEYS = {64: 50, 33: 49, 34: 39, 35: 51, 36: 52, 37: 53, 38: 55, 40: 57, 41: 48, 42: 56, 43: 61, 63: 47, 60: 44,
               126: 96, 62: 46, 58: 59, 123: 91, 124: 92, 125: 93, 94: 54, 95: 45}
ORIGNUMBERS = {96: 126, 59: 58, 39: 34, 47: 63, 44: 60, 45: 95, 46: 62, 93: 125, 48: 41, 49: 33, 50: 64, 51: 35, 52: 36,
               53: 37, 54: 94, 55: 38, 56: 42, 57: 40, 91: 123, 92: 124, 61: 43}

KEYEVENT_PRESS = "press"
KEYEVENT_RELEASE = "release"

LANGUAGE_PYTHON = "python"
LANGUAGE_MEL = "mel"

DEFAULT_CATEGORY = "Custom Scripts.zooTools"

JSON_TRUE = "##TRUE##"

RTCOMBO_USERCMDS = "=== MAYA COMMANDS ==="
RTCOMBO_MAYACMDS = "=== USER COMMANDS ==="
RTCOMBO_ZOOCMDS = "=== ZOO COMMANDS ==="

RTCTYPE_MAYA = "maya"
RTCTYPE_ZOO = "Zoo"
RTCTYPE_CURRENT = "current"
RTCTYPE_NEW = "new"


# Should be made into subclasses maybe
class MHKType(object):
    hotkey = "hotkey"
    nameCommand = "nameCommand"
    runTimeCommand = "runTimeCommand"
    hotkeyCtx = "hotkeyCtx"
    hotkeySet = "hotkeySet"
