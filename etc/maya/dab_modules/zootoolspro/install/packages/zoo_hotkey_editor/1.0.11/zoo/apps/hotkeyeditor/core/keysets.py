import copy
import glob
import os

import maya.cmds as cmds
import maya.api.OpenMaya as om2

from zoo.apps.hotkeyeditor.core import const as c
from zoo.apps.hotkeyeditor.core import hotkeys
from zoo.apps.hotkeyeditor.core import utils
from zoo.libs.utils import zlogging
from zoovendor.six import string_types

logger = zlogging.getLogger(__name__)


class KeySetManager(object):
    """
    All the keysets together to manage
    """

    defaultKeySetName = c.DEFAULT_KEYSET
    mayaKeySetName = c.DEFAULT_MAYA
    newKeySetTemplateName = c.DEFAULT_TEMPLATE
    prefix = c.KEYSET_PREFIX
    defaultLanguage = "python"  # or "mel"

    def __init__(self):
        self.hkUserPath = utils.hotkeyPathUserPrefs()
        self.hkInternalPath = utils.hotkeyPathInternalPrefs()
        self.defaultKeySetPath = os.path.join(self.hkInternalPath, self.defaultKeySetName)
        self.mayaKeySetPath = os.path.join(self.hkInternalPath, self.mayaKeySetName)
        self.newKeySetTemplatePath = os.path.join(self.hkInternalPath, self.newKeySetTemplateName)

        self.defaultKeySetPathUser = os.path.join(self.hkUserPath, self.defaultKeySetName)
        self.mayaKeySetPathUser = os.path.join(self.hkUserPath, self.mayaKeySetName)
        self.newKeySetTemplatePathUser = os.path.join(self.hkUserPath, self.newKeySetTemplateName)

        self.copyToUserPref()

        self.defaultKeySet = KeySet(jsonPath=self.defaultKeySetPathUser+".json")
        self.mayaKeySet = KeySet(jsonPath=self.mayaKeySetPathUser+".json")
        self.newKeySetTemplate = KeySet(jsonPath=self.newKeySetTemplatePathUser + ".json")

        self._currentKeySet = ""

        self.keySets = []  # type: list[KeySet]
        self.reverts = []
        self.locked = [self.defaultKeySetName, self.mayaKeySetName]

        self.keySetInit()

    def copyToUserPref(self):
        """ Copy hotkey files to user

        :return:
        """

        userPath = 0
        originalPath = 1

        files = ((self.defaultKeySetPathUser, self.defaultKeySetPath),
                 (self.mayaKeySetPathUser, self.mayaKeySetPath),
                 (self.newKeySetTemplatePathUser, self.newKeySetTemplatePath))

        jsonFileIndex = (0, 1, 2)
        mhkFileIndex = (0, 1)

        for j in jsonFileIndex:
            if utils.copyFile(files[j][userPath], files[j][originalPath], ".json"):
                print ("Creating preference file {}.json".format(os.path.basename(files[j][userPath])))

        for m in mhkFileIndex:
            if utils.copyFile(files[m][userPath], files[m][originalPath], '.mhk'):
                print ("Creating preference file {}.mhk".format(os.path.basename(files[m][userPath])))

    def keySetInit(self):
        """
        Reads the hotkey folder for key set jsons and loads them into memory.

        :return:
        """
        # Get all jsons in the folder

        os.chdir(self.hkUserPath)

        userJson = []
        for f in glob.glob("*.json"):
            if f.startswith(self.prefix):
                userJson.append(f)  # Remove ".json"

        keySetFiles = userJson

        self.keySets = []
        self.keySets.append(self.mayaKeySet)
        self.keySets.append(self.defaultKeySet)
        #self.keySets.append(self.newKeySet)
        for f in keySetFiles:
            keyset = KeySet(jsonPath="{}/{}".format(self.hkUserPath, f))
            self.keySets.append(keyset)

        # Get the current keyset
        self.currentKeySet()
        self.setAllReverts()

    def setAllReverts(self):
        """ Sets the revert data based on the keysets
        :return:
        """
        self.reverts = []
        for k in self.keySets:
            r = KeySet(k)
            self.reverts.append(r)

    def setRevert(self, keySet):
        toDel = ""
        for r in self.reverts:
            if r.keySetName == keySet.keySetName:
                toDel = r
                break

        self.reverts.remove(toDel)
        newR = KeySet(keySet)
        self.reverts.append(newR)

    def revertKeySet(self, keySet):
        """ Set the data from the revert data

        :param keySet:
        :return:
        """
        for r in self.reverts:
            if keySet.keySetName == r.keySetName:
                keySet.setData(r)

                return

    def revertCurrentKeySet(self):
        current = self.currentKeySet()
        self.revertKeySet(current)

    def getKeySetNames(self, excludeMaya=False):
        """ Generally used by the UI

        :return:
        """
        keysets = []

        for i, k in enumerate(self.keySets):
            # Remove .json
            kset = utils.getFileName(k.filePath)

            # Skip the the defaultKeyset one since its our default Zoo_Tools_Default one
            if kset == self.defaultKeySetName or kset == self.newKeySet:
                keysets.append(kset)
                continue

            # Exclude Maya default key set
            if kset == self.mayaKeySetName and excludeMaya:
                continue

            # Otherwise Assumes that it is prefixed with "Zoo_User_"
            removedPre = utils.removePrefix(self.prefix, kset)
            keysets.append(removedPre)

        return keysets

    def installAll(self):
        """ Install all keysets

        :return:
        """

        for k in self.keySets:
            k.install()


    def nextKeySet(self):
        """
        Goes to the next keyset.

        Usage:
        from zoo.libs.maya.cmds.hotkeys import keysets
        keysets.KeySetManager().nextKeySet()
        :return:
        """

        nextK = False
        current = self.currentKeySet(forceMaya=True)

        # Loop through keysets
        for ks in self.keySets:
            if nextK:
                om2.MGlobal.displayInfo("Hotkey set switched to :  `{}`".format(ks.keySetName))
                self.setActive(ks, mayaOnly=True)
                return

            if ks == current and current != self.keySets[-1]:
                nextK = True

        # If it reached here loop it back to the start
        if nextK is False:
            self.setActive(self.keySets[0], mayaOnly=True)
            om2.MGlobal.displayInfo("Hotkey set switched to :  `{}`".format(self.keySets[0].keySetName))
            return

        if current is None:
            self.setActive(self.getDefaultKeySet())
            om2.MGlobal.displayInfo("Hotkey set switched to :  `{}`".format(self.getDefaultKeySet().keySetName))

            return

    def getRuntimeCommandNames(self):
        current = self.currentKeySet()
        userRTCs = []
        mayaRTCs = utils.sortedIgnoreCase(utils.getDefaultRuntimeCmdsList())
        zooRTCs = self.defaultKeySet.getRuntimeCommandNames()

        if current is not None:
            userRTCs = current.getRuntimeCommandNames()

        return userRTCs, zooRTCs, mayaRTCs

    def setActive(self, keySet, install=False, mayaOnly=False):
        """
        Set keyset as active. Everything is set up here

        :param keySet:
        :type keySet: KeySet or basestring
        :param install:
        :param mayaOnly:
        :return:
        """

        switchSet = ""
        # By Object
        if isinstance(keySet, KeySet):
            switchSet = keySet

        # By String
        if isinstance(keySet, string_types):
            for ks in self.keySets:
                if keySet == ks.keySetName or self.prefix+keySet == ks.keySetName:
                    switchSet = ks
                    break

        if switchSet != "":
            self._currentKeySet = switchSet

            if install and mayaOnly is False:
                self._currentKeySet.install()

                logger.info("Applying set {}".format(switchSet.keySetName))

            if mayaOnly:
                cmds.hotkeySet(self._currentKeySet.keySetName, current=1, e=1)
                logger.info("Applying set {}".format(switchSet.keySetName))

            return self._currentKeySet

        logger.warning("Key set not found! " + keySet, self.keySets)

    def setModified(self, value):
        current = self.currentKeySet()
        current.modified = value

    def isModified(self):
        current = self.currentKeySet()
        return current.modified

    def currentKeySet(self, forceMaya=False):
        """

        :param forceMaya:
        :return:
        :rtype: KeySet
        """


        if self._currentKeySet != "" and forceMaya is False:
            return self._currentKeySet

        current = utils.currentMayaSet()

        allKeySetNames = self.keySets + [self.mayaKeySet]

        # Get the name only
        nameOnly = list(map(lambda x: utils.getFileName(x.filePath), allKeySetNames))

        allKeySets = self.keySets + [self.mayaKeySet]
        if current in nameOnly:
            for ks in allKeySets:

                if ks.keySetName == current:
                    self._currentKeySet = ks
                    return self._currentKeySet

            logger.info("getCurrentKeySet(): Zoo Key set not found for \"{}\".".format(current))

        return None

    def newKeySet(self, name):
        """ Create new key set

        :param name:
        :return:
        """
        # New key set object
        name = self.prefix + name

        # Check to see if it exists first
        for k in self.keySets:
            if k.keySetName == name or k.prettyName.lower() == name.lower():
                return False

        # Copy the Zoo_Tools_Default key set
        keyset = copy.deepcopy(self.newKeySetTemplate)
        keyset.keySetName = name
        keysetFile = os.path.join(self.hkUserPath, name+".json")
        keyset.filePath = keysetFile

        self.keySets.append(keyset)
        self.setActive(keyset, install=True)

        # Save it as a json since its a new set
        keyset.save()

        return keyset

    def isDefaultKeySet(self):
        """
        If current active keyset is default
        :return:
        """

        if self.currentKeySet() is not None and \
                        self.currentKeySet().keySetName == self.defaultKeySetName:
            return True
        return False

    def isLockedKeySet(self):
        """ Checks if the current keyset is a locked one
        :return:
        """
        current = self.currentKeySet()
        if current is not None and current.keySetName in self.locked:
            return True
        return False

    def isKeySetLocked(self, keySetName=None):
        """
        Checks if the keyset is one of the locked keysets

        :param keySetName:
        :return:
        """
        keySetName = keySetName or self.currentKeySet().keySetName
        locked = [utils.removePrefix(self.prefix, x) for x in self.locked]
        return keySetName in locked

    def getDefaultKeySet(self):
        """

        :return:
        """
        if self.defaultKeySet == "":
            self.defaultKeySet = filter(lambda x: x.keySetName == self.defaultKeySetName, self.keySets)[0]

        return self.defaultKeySet

    def getMayaKeySet(self):
        """

        :return:
        """
        if self.mayaKeySet == "":
            self.mayaKeySet = filter(lambda x: x.keySetName == self.mayaKeySetName, self.keySets)[0]

        return self.mayaKeySet

    def newHotkey(self, name):
        """
        New hotkey based on name, created in the current keyset

        :param name:
        :return:
        """
        return self._currentKeySet.newHotkey(name)

    def deleteHotkey(self, hotkey):
        """

        :param hotkey:
        :return:
        """
        if not isinstance(hotkey, hotkeys.Hotkey):
            logger.info("KeySetManager.deleteHotkey(): Expecting Hotkey")
            return
        return self._currentKeySet.deleteHotkey(hotkey)

    def save(self):
        """ Save all keysets to their json files
        :return:
        """

        # Export as mhk
        # Save as json

        for k in self.keySets:
            if not self.isKeySetLocked(k.keySetName) or utils.isAdminMode():
                logger.info("{}: Saving to {}".format(k.keySetName, k.filePath))
                utils.backupFile(k.filePath)
                k.save()
            else:
                logger.info("{} is Read-Only. Ignoring.".format(k.keySetName))

        # Reset all the revert data
        self.setAllReverts()

    def getKeySetByName(self, name):
        """
        Gets key set by name
        :param name:
        :return:
        """

        find = filter(lambda x: x.keySetName == name or
                                x.keySetName == KeySetManager.prefix+name,
                      self.keySets)

        if len(find) > 0:
            return find[0]

    def deleteKeySet(self, keySet):
        """
        Delete Key set
        :param keySet:
        :return:
        """
        ks = self.getKeySetByName(keySet)
        utils.backupFile(ks.filePath)
        os.remove(ks.filePath)
        self.keySets.remove(ks)
        cmds.hotkeySet(ks.keySetName, e=1, delete=1)
        del(ks)

    def setupRuntimeCmd(self, selectedHotkey, runtimeCmdName, keySet=""):
        """ Set up Runtime command for the key set with the selectedHotkey

        :param selectedHotkey:
        :param runtimeCmdName:
        :param keySet:
        :return: Returns a dictionary full of what the UI should be filled with
        :rtype: dict
        """
        if keySet == "":
            keySet = self.currentKeySet()

        ui = {'commandLanguage': self.defaultLanguage,
              'category': "",
              'command': ""}

        currentRTC = keySet.getRuntimeCmdByName(runtimeCmdName)
        defaultRTC = self.defaultKeySet.getRuntimeCmdByName(runtimeCmdName)
        mayaRTC, lang = utils.getMayaRuntimeCommand(runtimeCmdName)

        rtcType = ""

        if mayaRTC is not None:
            # Maya Runtime Command found
            rtcType = c.RTCTYPE_MAYA
            ui['command'] = mayaRTC
            ui['commandLanguage'] = lang
        elif currentRTC is not None:
            # Runtime Command in current keyset
            ui = dict(currentRTC.cmdAttrs)
            rtcType = c.RTCTYPE_CURRENT
        elif currentRTC is None and defaultRTC is not None:
            # Runtime command in Zoo key set
            ui = dict(defaultRTC.cmdAttrs)
            rtcType = c.RTCTYPE_ZOO
        elif currentRTC is None and defaultRTC is None and not mayaRTC:
            # No runtime found, create a new one. Might want to separate this one out
            rtcType = c.RTCTYPE_NEW

        ui['rtcType'] = rtcType

        keySet.setUpRuntimeCommand(selectedHotkey, runtimeCmdName, rtcType=rtcType)

        return ui


class KeySet(object):
    """
    The KeySet class. Reads in the list
    """
    def __init__(self, keySet=None, jsonPath="", name="", source=""):
        """ Either create Keyset through the jsonPath or create a new one by name

        :param jsonPath:
        :param name:
        """
        if isinstance(keySet, KeySet):
            self.__dict__ = copy.deepcopy(keySet.__dict__)
            return

        # All these are lists of MHKCommand()
        self._hotkeyCmds = []
        self._runtimeCmds = []
        self._nameCmds = []
        self._hotkeyCtxCmds = []

        self.keySetName = name
        self.source = source

        self.hotkeys = []
        self.filePath = jsonPath
        self.readOnly = False
        self.modified = False

        self._prettyName = ""

        if jsonPath != "":
            self.loadJson(jsonPath)
            self.sort()
            self.setNameFromJson()

    @property
    def prettyName(self):
        return utils.removePrefix(KeySetManager.prefix, self.keySetName)

    def setData(self, keySet):
        if isinstance(keySet, KeySet):
            self.__dict__ = copy.deepcopy(keySet.__dict__)

    def newHotkey(self, name):
        """
        Adds a new hotkey to the current keyset
        :return:
        """

        checkName = (name + "NameCommand").lower()
        # Check to see if hotkey exists
        if self.nameCommandExists(checkName):
            return False

        name = utils.toRuntimeStr(name)

        hotkeyCmd = hotkeys.MHKCommand(cmdType=c.MHKType.hotkey, name=name)
        hotkeyCmd.setHotkeyCmd(name+"NameCommand", "", c.KEYEVENT_PRESS)

        hotkey = hotkeys.Hotkey(hotkeyCmd)

        self.hotkeys.append(hotkey)
        self._hotkeyCmds.append(hotkeyCmd)

        return hotkey

    def getRuntimeCommandNames(self):
        return [r.cmdAttrs['cmdInput'] for r in self._runtimeCmds]

    def nameCommandExists(self, nameCommand):
        nameCommand = utils.toRuntimeStr(nameCommand)
        nameCommand = nameCommand.lower()
        for h in self.hotkeys:
            if nameCommand == h.nameCommand.lower():
                return True

        return False

    def deleteHotkey(self, hotkey):

        if not isinstance(hotkey, hotkeys.Hotkey):
            logger.info("KeySet.deleteHotkey(): Expecting Hotkey")
            return

        # Todo: Should check if everything got removed properly
        if hotkey.mhkcmds.hotkeyCmd is not None:
            try:
                self._hotkeyCmds.remove(hotkey.mhkcmds.hotkeyCmd)
            except ValueError:
                logger.warning("KeySet.deleteHotkey(): hotkeyCmd Missing!")
                return False
        else:
            logger.warning("KeySet.deleteHotkey(): hotkeyCmd Missing!")
            return False

        if hotkey.mhkcmds.nameCmd is not None:
            try:
                self._nameCmds.remove(hotkey.mhkcmds.nameCmd)
            except ValueError:
                logger.warning("KeySet.deleteHotkey(): hotkeyCmd Missing!")

        if hotkey.mhkcmds.runtimeCmd is not None:
            try:
                self._runtimeCmds.remove(hotkey.mhkcmds.runtimeCmd)
            except ValueError:
                logger.warning("KeySet.deleteHotkey(): hotkeyCmd Missing!")

        if hotkey.mhkcmds.hotkeyCtxCmd is not None:
            try:
                self._hotkeyCtxCmds.remove(hotkey.mhkcmds.hotkeyCtxCmd)
            except ValueError:
                logger.warning("KeySet.deleteHotkey(): hotkeyCmd Missing!")

        try:
            self.hotkeys.remove(hotkey)
        except ValueError:
            logger.warning("KeySet.deleteHotkey(): Hotkey() not found!")

        return True

    def setNameFromJson(self):
        """
        Set the name based on the jsonPath
        :return:
        """

        if self.filePath != "":
            self.keySetName = utils.getFileName(self.filePath)

    def setSource(self, source):
        """ Set the keyset source to use as a hotkey base on.

        eg Maya_Default, Maya_Default_ZooMod, Zoo_Tools_Default

        :param source:
        :return:
        """
        self.source = source

    def count(self, includeEmpty=False):
        """
        Get number of hotkey entries there are.

        :param includeEmpty: Sometimes Maya gives empty hotkey entries. Set to false to exclude them
        :return:
        """

        hotkeyCount = len(self.hotkeys)

        # Clear out the empty
        if includeEmpty is False:
            nonEmptyList = filter(lambda x: x.prettyName != "", self.hotkeys)
            nonEmptyCount = len(nonEmptyList)

            return nonEmptyCount

        return len(self.hotkeys)

    def loadJson(self, path):
        file = open(path, "r")

        jsonStr = file.read()

        import json

        commandList = json.loads(jsonStr)
        file.close()
        self.filePath = path
        # Get hotkeys only for now
        self.setupCommands(commandList)

    def setupCommands(self, commandList):

        hotkeySet = []

        # Separate out the commands out first
        for cmd in commandList:
            mhkCommand = hotkeys.MHKCommand(cmdDict=cmd)

            if cmd['cmdType'] == c.MHKType.hotkey:
                self._hotkeyCmds.append(mhkCommand)
            elif cmd['cmdType'] == c.MHKType.nameCommand:
                self._nameCmds.append(mhkCommand)
            elif cmd['cmdType'] == c.MHKType.runTimeCommand:
                self._runtimeCmds.append(mhkCommand)
            elif cmd['cmdType'] == c.MHKType.hotkeyCtx:
                self._hotkeyCtxCmds.append(mhkCommand)
            elif cmd['cmdType'] == c.MHKType.hotkeySet:
                hotkeySet = cmd
                pass
            else:
                print("KeySet(): Invalid command type! \"{}\"".format(cmd['cmdType']))

        # Now lets do the set up
        try:
            self.source = hotkeySet['source']
        except TypeError:
            from zoo.apps.hotkeyeditor.core import admin
            admin.SaveAsNewDefaults()
            logger.info("Warning! JSON may be empty! New JSON Files generated!")

        self.setupHotkeys()

    def sort(self):
        if len(self.hotkeys) <= 1:
            return

        self.hotkeys.sort(key=lambda x: x.nameCommand.lower(), reverse=False)

        # Move empty entries to the end (Sort moves empty entries to the front)
        empty = []
        while self.hotkeys is not None and self.hotkeys[0].prettyName == "":
            empty.append(self.hotkeys[0])
            self.hotkeys = self.hotkeys[1:]

        self.hotkeys += empty

    def install(self, override=True):
        """ Installs the keyset

        :param useZoo:
        :type useZoo:
        :type override: object
        :return: If it was installed or not
        """

        if override and self.exists():
            cmds.hotkeySet(self.keySetName, delete=1, e=1)

        if cmds.hotkeySet(self.keySetName, exists=1):
            return False

        # Source
        cmds.hotkeySet(self.keySetName, source=self.source, current=1)

        # Runtime Commands
        for r in self._runtimeCmds:
            r.run()

        # Name commands
        for n in self._nameCmds:
            n.run()

        # Hotkey commands
        for h in self._hotkeyCmds:
            h.run()

        # hotkeyCTX commands
        for hctx in self._hotkeyCtxCmds:
            hctx.run()


    def exists(self):
        """
        Returns true if it already exists in Maya
        :return:
        """
        return cmds.hotkeySet(self.keySetName, exists=1)

    def setupHotkeys(self, hotkeyCmds='', nameCmds='', runtimeCmds='',hotkeyCtxCmds=''):

        # Use the classes attributes no command lists were given in
        if hotkeyCmds == '':
            hotkeyCmds = self._hotkeyCmds
        if nameCmds == '':
            nameCmds = self._nameCmds
        if runtimeCmds == '':
            runtimeCmds = self._runtimeCmds
        if hotkeyCtxCmds == '':
            hotkeyCtxCmds = self._hotkeyCtxCmds

        # Probably a better way to do this
        for h in hotkeyCmds:  # Populate the KeySet with hotkeys
            hotkey = hotkeys.Hotkey(hotkeyCmd=h)

            try:
                hotkey.ctxClient = h.cmdAttrs['ctxClient']
            except:
                pass

            # Get the info from the name commands
            for n in nameCmds:
                if n.cmdAttrs['cmdInput'] == hotkey.nameCommand:
                    hotkey.setNameCmd(n)
                    break

            if hotkey.runtimeCommand != "":
                for r in runtimeCmds:
                    if r.cmdAttrs['cmdInput'] == hotkey.runtimeCommand:
                        hotkey.setRuntimeCmd(r)
                        break
            else:
                pass

            self.hotkeys.append(hotkey)

    def save(self):
        """ Saves to filePath

        :return:
        """
        self.updateHotkeys()
        hotkeyCmds = (o.cmdAttrs for o in self._hotkeyCmds)
        runtimeCmds = (o.cmdAttrs for o in self._runtimeCmds)
        nameCmds = (o.cmdAttrs for o in self._nameCmds)
        hotkeyCtxCmds = (o.cmdAttrs for o in self._hotkeyCtxCmds)

        hotkeySet = self.getHotkeySetDict()
        jsonExport = list(hotkeyCmds) + \
                     list(runtimeCmds) + \
                     list(nameCmds) + \
                     list(hotkeyCtxCmds) + \
                     [hotkeySet]

        utils.outputJSON(jsonExport, self.filePath)

        # We also need to install them all
        self.install()

    def updateHotkeys(self):
        """ Updates cmds array to get ready for saving

        :return:
        """
        for h in self.hotkeys:
            h.updateMHKCommands()

    def getHotkeySetDict(self):
        """ Get hotkeySet dict for json output

        :param self:
        :return:
        """

        ret = {
            "current": c.JSON_TRUE,
            "source": self.source,
            "cmdInput": self.keySetName,
            "cmdType": "hotkeySet"
        }

        return ret

    def setUpRuntimeCommand(self, selectedHotkey, runtimeCmdName, rtcType):
        """ Set up Runtime Command in the mhks classes


        :param selectedHotkey:
        :type selectedHotkey:
        :param runtimeCmdName:
        :type runtimeCmdName:
        :param rtcType:
        :type rtcType:
        :return:
        :rtype:
        """
        if selectedHotkey not in self.hotkeys:
            logger.error("Selected hotkey not found in current keyset! " + self.keySetName)

        if runtimeCmdName == "":
            self.clearHotkey(selectedHotkey)
            return

        runtimeCmd = self.getRuntimeCmdByName(runtimeCmdName)
        newNameCommandName = selectedHotkey.nameCommand

        nameCmd = self.getNameCmdByName(selectedHotkey.nameCommand)

        if rtcType == c.RTCTYPE_MAYA or rtcType == c.RTCTYPE_ZOO:
            # We only want to connect the name command to the runtime command for
            # Maya runtime commands and Zoo runtime commands
            selectedHotkey.mhkcmds.runtimeCmd = None
            selectedHotkey.runtimeCommand = runtimeCmdName
            selectedHotkey.category = ""
            selectedHotkey.commandScript = ""
            selectedHotkey.runtimeType = rtcType

        elif rtcType == c.RTCTYPE_CURRENT:
            # Runtime command exists in current keyset
            selectedHotkey.setRuntimeCmd(runtimeCmd)
            selectedHotkey.runtimeType = rtcType

        elif rtcType == c.RTCTYPE_NEW:
            # Runtime command doesn't exist, create a new one

            runtimeCmd = hotkeys.MHKCommand()
            runtimeCmd.setRuntimeCmd(runtimeCmdName, language=c.LANGUAGE_MEL, category=c.DEFAULT_CATEGORY,
                                     annotation=runtimeCmdName)
            self._runtimeCmds.append(runtimeCmd)
            selectedHotkey.setRuntimeCmd(runtimeCmd)

        # Name command set up
        if nameCmd is None:
            newNameCommand = hotkeys.MHKCommand()
            self._nameCmds.append(newNameCommand)
            selectedHotkey.mhkcmds.nameCmd = newNameCommand
            newNameCommand.setNameCommand(newNameCommandName, runtimeCmdName, c.LANGUAGE_MEL)

        selectedHotkey.modified = True

    def clearHotkey(self, hotkey):
        hotkey.category = ""
        hotkey.commandScript = ""
        hotkey.modified = True

        hotkey.mhkcmds.runtimeCmd = None
        hotkey.runtimeCommand = ""

    def getRuntimeCmdByName(self, runtimeCmdName):
        for r in self._runtimeCmds:
            if r.cmdAttrs['cmdInput'] == runtimeCmdName:
                return r

    def getNameCmdByName(self, nameCmdName):
        for n in self._nameCmds:
            if n.cmdAttrs['cmdInput'] == nameCmdName:
                return n

