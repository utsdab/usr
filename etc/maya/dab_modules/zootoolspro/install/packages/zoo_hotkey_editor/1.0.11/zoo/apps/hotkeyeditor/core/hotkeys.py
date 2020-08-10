from shlex import split as shlexSplit

import maya.cmds as cmds
from zoo.apps.hotkeyeditor.core import const as c
from zoo.apps.hotkeyeditor.core import utils
from zoo.libs.utils import zlogging
import pprint

logger = zlogging.getLogger(__name__)


class Hotkey(object):

    modifiers = ['ctl', 'sht', 'alt', 'cmd']

    class MHKCmds(object):
        """
        Struct like class to hold our data.
        The data in here matches the .json file
        """
        def __init__(self):
            self.hotkeyCmd = None  # type: MHKCommand
            self.nameCmd = None  # type: MHKCommand
            self.runtimeCmd = None  # type: MHKCommand
            self.hotkeyCtxCmd = None  # type: MHKCommand

    def __init__(self, hotkeyCmd=""):
        self.name = ""
        self.releaseName = ""
        self.prettyName = ""
        self.nameCommand = ""  # Set in setName()
        self.runtimeCommand = ""
        self.category = ""
        self.language = ""
        self.keyShortcut = ""
        self.annotation = ""
        self.ncAnnotation = ""
        self.rtAnnotation = ""
        self.ctxClient = ""
        self.keyEvent = ""
        self.ctxType = ""
        self.runtimeType = ""
        self.ctxAddClient = ""
        self.modifier = {"ctl": False,
                         "sht": False,
                         "alt": False,
                         "cmd": False}

        self.modified = False

        self.mhkcmds = self.MHKCmds()

        self.commandScript = ""

        if hotkeyCmd != "":
            self.setHotkeyCmd(hotkeyCmd)

    def getNameCmdName(self, includeSuffix=True):
        """

        :param includeSuffix: Suffix is "NameCommand" ie "DoHotkeyThingNameCommand"
        :return:
        """
        suffix = "NameCommand"
        ret = ""

        if self.keyEvent == c.KEYEVENT_PRESS:
            ret = self.name

        elif self.keyEvent == c.KEYEVENT_RELEASE:
            ret = self.releaseName

        if not includeSuffix:
            ret = ret[:-len(suffix)]

        return ret

    def dataOut(self):
        return str(pprint.pformat(self.__dict__))

    def renameNameCommand(self, newName):
        newName = utils.toRuntimeStr(newName)
        newName += "NameCommand"
        self.nameCommand = newName

        if self.keyEvent == c.KEYEVENT_PRESS:
            self.name = newName
        elif self.keyEvent == c.KEYEVENT_RELEASE:
            self.releaseName = newName

        # Maybe should't be done here
        self.mhkcmds.nameCmd.cmdAttrs['cmdInput'] = newName

        return newName

    def setHotkeyCmd(self, hotkeyCmd):
        """
        Pretty much just sets the names
        :param hotkeyCmd:
        :return:
        """
        self.mhkcmds.hotkeyCmd = hotkeyCmd

        try:
            self.name = hotkeyCmd.cmdAttrs['name']
            self.keyEvent = c.KEYEVENT_PRESS
        except KeyError:
            pass
        try:
            self.releaseName = hotkeyCmd.cmdAttrs['releaseName']
            self.keyEvent = c.KEYEVENT_RELEASE
        except KeyError:
            pass

        if self.name != "":
            self.nameCommand = self.name
        elif self.releaseName != "":
            self.nameCommand = self.releaseName
        else:
            logger.warning("Hotkey.setName(): Warning! nameCommand not found! {}".format(hotkeyCmd))
            logger.warning("Hotkey Attributes: CHECK FOR ISSUES HERE >>>> {}".format(hotkeyCmd.cmdAttrs))
            pass

        self.setPrettyName()

        self.keyShortcut = hotkeyCmd.cmdAttrs['keyShortcut']
        self.runtimeCommand = ''

        # Set commands based on hotkeyCmd
        self.setModifiers(hotkeyCmd)

    def setRuntimeCmd(self, runtimeCmd):
        self.mhkcmds.runtimeCmd = runtimeCmd
        self.category = runtimeCmd.cmdAttrs['category']
        self.language = runtimeCmd.cmdAttrs['commandLanguage']
        self.runtimeCommand = runtimeCmd.cmdAttrs['cmdInput']
        self.commandScript = runtimeCmd.cmdAttrs['command']

    def setNameCmd(self, nameCmd):

        # Make sure its the same name
        if nameCmd.cmdAttrs['cmdInput'] != self.nameCommand:
            logger.info("Hotkey.setNameCmd(): It shouldn't reach here!")
            return

        self.mhkcmds.nameCmd = nameCmd

        self.runtimeCommand = nameCmd.cmdAttrs['command']
        self.annotation = nameCmd.cmdAttrs['annotation']

    def setHotkeyCtxCmd(self, hotkeyCtxCmd):
        # Obsolete
        pass
        self.mhkcmds.hotkeyCtxCmd = hotkeyCtxCmd
        self.ctxType = self.hotkeyCtxCmd['type']
        self.ctxAddClient = self.hotkeyCtxCmd['addClient']

    def setHotkey(self, hotkeyStr):
        """
        Sets a hotkey based on the string ie. "Shift+Alt+P"

        :param hotkeyStr:
        :return:
        """

        mod, newShortcut = strToData(hotkeyStr)

        if self.modifier != mod or newShortcut != self.keyShortcut:
            self.modifier = mod
            self.keyShortcut = newShortcut

            return True

    def setPrettyName(self, suffix=True):
        prettyName = self.nameCommand

        nc = "NameCommand"
        if prettyName.endswith(nc):
            prettyName = prettyName[0:-len(nc)]

        self.prettyName = utils.camelToSpaces(prettyName)
        self.prettyName = self.prettyName.replace("C3Dc", "C3dC")

        if suffix and self.prettyName.strip() != "":

            nameSuffix = ""
            if self.keyEvent == c.KEYEVENT_PRESS:
                nameSuffix = "[PRESS]"
            elif self.keyEvent == c.KEYEVENT_RELEASE:
                nameSuffix = "[RELEASE]"

            self.prettyName += " " + nameSuffix

    def getPrettyName(self):
        if self.prettyName != "":
            return self.prettyName

        return self.prettyName

    def toString(self):
        """
        The hotkey shortcut to string eg. "Ctrl+Shift+E"
        :return:
        """

        modifiers = [
            ('ctl', "Ctrl+"),
            ('sht', "Shift+"),
            ('alt', "Alt+"),
            ('cmd', "Cmd+"),
        ]

        ret = ''

        # Go through each one and add to the string
        for modStr in modifiers:
            if self.modifier[modStr[0]]:
                ret += modStr[1]

        ret += self.keyShortcut.upper()

        return ret

    def setModifiers(self, hotkeyCmd):
        """
        Sets the modifiers in self.modifier to true if found in hotkeyCmd
        :param hotkeyCmd:
        :return:
        """

        for mod in Hotkey.modifiers:
            try:
                self.modifier[mod] = True if hotkeyCmd.cmdAttrs[mod] == c.JSON_TRUE else False
            except KeyError:
                pass

    def updateMHKCommands(self):
        """ Update MHK commands

        Updates everything in to the self.MHKCmds(), cmdAttrs dictionary. cmdAttrs is what gets saved out.

        :return:
        """
        self._updateHotkeys()
        self.updateRuntimeCmd()
        self._updateNameCommand()
        #self._updateHotkeyCtx()

    def _updateHotkeys(self):
        self.mhkcmds.hotkeyCmd.setHotkeyCmd(self.nameCommand,
                                            self.keyShortcut,
                                            self.keyEvent,
                                            alt=self.modifier['alt'],
                                            ctl=self.modifier['ctl'],
                                            cmd=self.modifier['cmd'],
                                            sht=self.modifier['sht'],
                                            ctxClient=self.ctxClient)

    def updateRuntimeCmd(self):
        if self.mhkcmds.runtimeCmd:
            self.mhkcmds.runtimeCmd.setRuntimeCmd(self.runtimeCommand,
                                                  self.language,
                                                  self.category,
                                                  command=self.commandScript,
                                                  annotation=self.annotation)#,
                                                  #hotkeyCtx="")

    def _updateNameCommand(self):
        if self.mhkcmds.nameCmd:
            self.mhkcmds.nameCmd.setNameCommand(self.nameCommand,
                                                self.runtimeCommand,
                                                "mel") # Todo: Language cant be always mel, its different to self.language. NameCommand language is different to runtimeCommand language. Check json for more details
                                                #annotation="") # Todo: annotation is different to runtime command

    def _updateHotkeyCtx(self):
        # Obsolete
        self.mhkcmds.hotkeyCtxCmd.setHotkeyCtxCmd(self.ctxType, self.addClient)

    def setLanguage(self, language):

        if language != c.LANGUAGE_MEL and language != c.LANGUAGE_PYTHON:
            logger.error("Hotkey().setLanguage(): Invalid Language! " + language)
            return

        if self.language != language:
            self.language = language
            self.modified = True

        # This might cause problems since this recreates the cmdAttr dict.
        self.updateRuntimeCmd()

    def setCategory(self, category):
        if self.category != category:
            self.category = category
            self.modified = True

    def setCommandScript(self, commandStr):
        cleanedScript = utils.cleanScript(self.commandScript)
        if cleanedScript != commandStr:
            self.commandScript = commandStr
            self.modified = True

        # This might cause problems since this recreates the cmdAttr dict.
        self.updateRuntimeCmd()

    def setKeyEvent(self, keyEvent):

        if keyEvent != c.KEYEVENT_PRESS and keyEvent != c.KEYEVENT_RELEASE:
            logger.error("Hotkey().setKeyEvent(): Invalid KeyEvent! " + keyEvent)
            return

        if self.keyEvent != keyEvent:
            self.keyEvent = keyEvent
            self.modified = True

        self.setPrettyName(suffix=True)

        # Update the mhkcommand as this is how the json is saved
        if self.mhkcmds.hotkeyCmd is not None:

            name = self.mhkcmds.hotkeyCmd.cmdAttrs.get("name", "")
            releaseName = self.mhkcmds.hotkeyCmd.cmdAttrs.get("releaseName", "")

            if name == "" and releaseName == "":
                logger.warn("Hotkey.setKeyEvent(): Missing name and releaseName from hotkeyCmd!")
                return

            if name != self.nameCommand and releaseName != self.nameCommand:
                logger.warning("Hotkey.setKeyEvent(): nameCommand mismatch! [{},{},{}]".format(
                    self.nameCommand, name, releaseName
                ))
                return

            # Clear out the data and put in the one we want
            self.mhkcmds.hotkeyCmd.cmdAttrs['name'] = ""
            self.mhkcmds.hotkeyCmd.cmdAttrs['releaseName'] = ""

            if keyEvent == c.KEYEVENT_PRESS:
                self.mhkcmds.hotkeyCmd.cmdAttrs['name'] = self.nameCommand
            elif keyEvent == c.KEYEVENT_RELEASE:
                self.mhkcmds.hotkeyCmd.cmdAttrs['releaseName'] = self.nameCommand
            else:
                logger.error("Hotkey.setKeyEvent(): Key event not set!")

        else:
            logger.error("Hotkey.setKeyEvent(): Unable to set language!")


class MHKCommand(object):
    """
    Commands found in the MHK file.
    """

    def __init__(self, melStr="", cmdDict="", cmdType="", name=""):
        self.cmdAttrs = {}

        # Parse command only if its not empty
        if melStr != "":
            self.parseCommand(melStr)
            return

        # Use the json dict only if its not empty
        if cmdDict != "":
            self.cmdAttrs = cmdDict  # type: dict

        # For anything else we populate the class the normal way

    def dataOut(self):
        return str(pprint.pformat(self.__dict__))

    def parseCommand(self, newCmd):
        # Since mel commands are similar to unix commands, we can use pythons lex analyzer to parse it for us
        cmd = shlexSplit(newCmd)
        self.cmdAttrs = self.cmdToDict(cmd)

    def getKey(self, key, dict):
        try:
            ret = dict[key]
        except KeyError:
            ret = ""
        return ret

    def setHotkeyCmd(self, nameCommand, keyShortcut, keyEvent, alt=False, ctl=False, cmd=False, sht=False, ctxClient=""):
        newDict = {"cmdType": "hotkey",
                   "keyShortcut": keyShortcut}

        if keyEvent == c.KEYEVENT_PRESS:
            newDict['name'] = nameCommand
        elif keyEvent == c.KEYEVENT_RELEASE:
            newDict['releaseName'] = nameCommand

        # alt, ctl, cmd or sht arg is true set newDict to JSON_TRUE
        mods = Hotkey.modifiers
        for m in mods:
            if locals()[m] is True:
                newDict[m] = c.JSON_TRUE

        if ctxClient != "":
            newDict['ctxClient'] = ctxClient

        self.cmdAttrs = newDict

    def setHotkeyCtxCmd(self, type, addClient):

        self.cmdAttrs = {
            "cmdType": "hotkeyCtx",
            "type": type,
            "addClient": addClient
        }

    def setRuntimeCmd(self, runtimeCmdName, language, category, command="", annotation="", hotkeyCtx=""):
        newDict = {
            "cmdType": "runTimeCommand",
            "cmdInput": runtimeCmdName,
            "category": category,
            "commandLanguage": language,
            "hotkeyCtx": hotkeyCtx,
            "command": command,
            "annotation": annotation
        }
        self.cmdAttrs = newDict

    def setNameCommand(self, name, runtimeCommand, language, annotation=""):

        annotation = name  # todo: this needs to be done properly
        newDict = {
            "cmdType": "nameCommand",
            "sourceType": language,
            "cmdInput": name,
            "annotation": annotation,
            "command": runtimeCommand,
        }

        self.cmdAttrs = newDict

    def setHotkeySet(self, name, source, current=True):
        self.cmdAttrs = {
            "cmdType": "hotkeySet",
            "cmdInput": name,
            "source": source,
            "current": current
        }

    def run(self):
        mel = ""

        # Todo: Code here looks like a dog's breakfast... should fix
        if self.cmdAttrs['cmdType'] == "hotkey":
            ctxClient = ""
            alt = self.getKey('alt', self.cmdAttrs)
            ctl = self.getKey('ctl', self.cmdAttrs)
            cmd = self.getKey('cmd', self.cmdAttrs)
            sht = self.getKey('sht', self.cmdAttrs)

            name = None
            releaseName = None

            try:
                name = self.cmdAttrs['name']
            except KeyError:
                releaseName = self.cmdAttrs['releaseName']

            try:
                ctxClient = self.cmdAttrs['ctxClient']
            except KeyError:
                pass

            self.cmdHotkey(self.cmdAttrs['keyShortcut'],
                           name=name,
                           releaseName=releaseName,
                           alt=alt, ctl=ctl, cmd=cmd, sht=sht,
                           ctxClient=ctxClient)

        elif self.cmdAttrs['cmdType'] == c.MHKType.hotkeyCtx:
            # Todo: needs to handle extra arguments better
            self.cmdHotkeyCtx(ctxType=self.cmdAttrs['type'],
                              addClient=self.cmdAttrs['addClient'])
        elif self.cmdAttrs['cmdType'] == c.MHKType.hotkeySet:
            # Todo: needs to handle extra arguments better
            self.cmdHotkeySet(name=self.cmdAttrs['cmdInput'],
                              source=self.cmdAttrs['source'],
                              current=self.cmdAttrs['current'])

        elif self.cmdAttrs['cmdType'] == c.MHKType.runTimeCommand:
            runtimeInput = self.cmdAttrs.copy()
            name = runtimeInput.pop("cmdInput")
            runtimeInput.pop('cmdType')
            self.cmdRunTimeCommand(name=name, **runtimeInput)
        elif self.cmdAttrs['cmdType'] == "nameCommand":
            sourceType = self.getKey('sourceType', self.cmdAttrs)
            command = self.getKey('command', self.cmdAttrs)
            self.cmdNameCommand(name=self.cmdAttrs['cmdInput'], annotation=self.getKey('annotation', self.cmdAttrs),
                                sourceType=sourceType,
                                command=command)
        else:
            logger.error("Invalid command! {}".format(self.cmdAttrs['cmdType']))

        return mel

    def cmdHotkey(self, keyShortcut, name=None, releaseName=None, alt="", ctl="", cmd="", mod="", pcr="", rcr="",
                  sht="", autosave=0, ctxClient=""):

        # name = name.strip("() ")
        name = utils.removeBrackets(name)
        releaseName = utils.removeBrackets(releaseName)

        # From 'Shift+2' to '@'
        if sht:
            charNum = ord(keyShortcut)
            if charNum in c.ORIGNUMBERS:
                keyShortcut = chr(c.ORIGNUMBERS[ord(keyShortcut)])
                sht = ""

        args = ('alt', 'sht', 'ctl', 'cmd', 'mod', 'pcr', 'rcr')
        inputs = {}

        for a in args:
            inputs[a] = 1 if locals()[a] == c.JSON_TRUE else 0

        if autosave != 0:
            logger.warning("Warning! cmdHotkey Autosave is not zero!")

        keyShortcut = keyShortcut.lower()

        if name is not None:
            cmds.hotkey(keyShortcut=keyShortcut, name=name,
                        alt=inputs['alt'], ctl=inputs['ctl'], mod=inputs['mod'], cmd=inputs['cmd'],
                        pcr=inputs['pcr'], rcr=inputs['rcr'], sht=inputs['sht'], ctxClient=ctxClient)
        elif releaseName is not None:
            cmds.hotkey(keyShortcut=keyShortcut, releaseName=releaseName,
                        alt=inputs['alt'], ctl=inputs['ctl'], mod=inputs['mod'], cmd=inputs['cmd'],
                        pcr=inputs['pcr'], rcr=inputs['rcr'], sht=inputs['sht'], ctxClient=ctxClient)

    def cmdHotkeyCtx(self, ctxType, addClient):
        cmds.hotkeyCtx(type=ctxType, addClient=addClient)

    def cmdHotkeySet(self, name, source="", current=0):
        current = 1 if current == c.JSON_TRUE else 0

        # Maybe just set it to not automatically set the set as active for now
        # current = 0
        cmds.hotkeySet(name, source=source, current=current)

    def cmdRunTimeCommand(self, name, annotation="", category="", hotkeyCtx="", commandLanguage="", command=""):
        # command = command.strip("() ")
        command = utils.removeBrackets(command)
        command = command.replace("\\n", "\n").replace("\\t", "    ")

        # Delete runtime command if it already exists and its not a default runtime command
        if utils.runtimeCmdExists(name, checkDefault=False) and not cmds.runTimeCommand(name, q=1, d=1):
            cmds.runTimeCommand(name, delete=1, e=1)

        if commandLanguage == "":
            commandLanguage = "mel"

        # Create runtime command
        cmds.runTimeCommand(name, annotation=annotation, category=category,
                            hotkeyCtx=hotkeyCtx, command=command, commandLanguage=commandLanguage)

    def cmdNameCommand(self, name, annotation="", sourceType="mel", command=""):
        # command = command.strip("() ")
        command = utils.removeBrackets(command)
        cmds.nameCommand(name, annotation=annotation, sourceType=sourceType, command=command)

    def cmdToDict(self, cmdStr):
        """ Convert the str from the regex match to a dictionary

        :param cmdStr:
        :type cmdStr: str
        :return:
        """
        ret = {'cmdType': cmdStr[0]}

        # Remove the "cmdType" eg runTimeCommand
        cmdStr = cmdStr[1:]

        # Process all the single arguments
        single = []
        if ret['cmdType'] == "hotkey":
            single = ("alt", "ctl", "cmd", "mod", "sht", "fs", "suh")
        elif ret['cmdType'] == "hotkeySet":
            single = (("current"),)
        elif ret['cmdType'] == "runTimeCommand":
            single = (("d"),)

        # Process all the single arguments
        for s in single:

            try:
                arg = "-{}".format(s)
                i = cmdStr.index(arg)

                cmdStr.remove(arg)
            except ValueError:  # Cant find index?
                continue

            ret[s] = c.JSON_TRUE

        if ret['cmdType'] == "nameCommand" or ret['cmdType'] == "runTimeCommand" or \
                        ret['cmdType'] == "hotkeySet":
            ret['cmdInput'] = cmdStr[-1].strip(";")
            cmdStr = cmdStr[:-1]

        # Add the paired arguments in
        for i in range(0, len(cmdStr), 2):
            if cmdStr[i][0] != '-':
                logger.warning("Something went wrong! Not a command!")

            newRet = cmdStr[i + 1]
            newRet = utils.removeBrackets(newRet)
            # ret[cmdStr[i][1:]] = cmdStr[i + 1].strip(";")#.strip("()")
            ret[cmdStr[i][1:]] = newRet

        return ret


def strToData(hotkeyStr, lower=False):
    """ Creates an easily comparable data structure.

    eg "Ctrl+Alt+C" ==> ({"ctl": True, "alt": True, "sht": False, "cmd": False}, "C")

    :return: hotkey in a form of a data structure
    :rtype: tuple(dict, basestr)
    """
    mod = {"ctl": True if "ctrl" in hotkeyStr.lower() else False,
           "sht": True if "shift" in hotkeyStr.lower() else False,
           "alt": True if "alt" in hotkeyStr.lower() else False,
           "cmd": True if "cmd" in hotkeyStr.lower() else False}

    if hotkeyStr == "":
        return mod, ""

    # Exclude "+" shortcut
    if hotkeyStr[-1] == "+":
        keyShortcut = "+"
    else:
        keyShortcut = hotkeyStr.split("+")[-1]

    if lower:
        keyShortcut = keyShortcut.lower()

    return mod, str(keyShortcut)

