"""
:todo: convert to using a plugin system for type initialization
:todo: convert shelf popup to qtmenu
"""
import os
import uuid
from collections import OrderedDict

from zoo.libs.utils import filesystem
from zoo.apps.toolpalette import palette
from zoo.libs.maya.utils import shelves
from zoo.preferences import core
from zoo.libs.utils import zlogging
from zoo.libs.command import executor
from maya.api import OpenMaya as om2
from maya import cmds

logger = zlogging.getLogger(__name__)

SHELFBUTTON_DEFINTION_COMMAND = """from zoo.apps.toolpalette import run as _paletterun
_zooPalette = _paletterun.show()
_zooPalette.executePluginById("{}", **{})
"""
SHELFBUTTON_ZOOCOMMAND = """from zoo.libs.command import executor as _zooexecutor
_zooexecutor.Executor().execute("{}", **{})
"""
TOOLSET_COMMAND = """from zoo.apps.toolpalette import run as _paletterun
_zooPalette = _paletterun.show()
_zooPalette.openToolSet("{}")
"""


class MayaPalette(palette.ToolPalette):
    SHELFLAYOUTENV = "ZOO_SHELF_LAYOUTS"

    def __init__(self, parent=None):
        # declare before calling super since _loadLayout gets called by the base.
        self.shelfLayout = ShelfLayout()
        super(MayaPalette, self).__init__(parent=parent)
        self.executor = executor.Executor()
        self.preferenceInterface = core.preference.interface("artistPalette")

    def _loadLayouts(self):
        super(MayaPalette, self)._loadLayouts()
        envpath = os.getenv(MayaPalette.SHELFLAYOUTENV, "")
        
        layouts = []
        for path in envpath.split(os.path.pathsep):
            path = os.path.normpath(path)
            if not os.path.exists(path):
                continue
            try:
                logger.debug("Loading Layout: {}".format(path))
                data = filesystem.loadJson(path, object_pairs_hook=OrderedDict)
                layouts.append(data)
            except ValueError:
                logger.error("Failed to load layout file: {}".format(path), exc_info=True)
            except IOError:
                logger.error("Failed to load layout File: {}, due to permission issues?".format(path),
                             exc_info=True, extra={"layoutFile": path, "environ": envpath})
            except AssertionError:
                logger.error("Failed to load shelf: {}".format(path),
                             exc_info=True)
        resultLayout = ShelfLayout()
        for sortedLayout in sorted(layouts, key=lambda x: x.get("sortOrder", 0)):
            resultLayout.update(ShelfLayout(sortedLayout))
        self.shelfLayout = resultLayout

    def createMenus(self):
        super(MayaPalette, self).createMenus()
        # todo convert to a tooldefinition?
        prefsMenu = self.subMenus.get("Preferences")
        if not prefsMenu:
            prefsMenu = self.menu.addMenu("Preferences")
            self.subMenus["Preferences"] = prefsMenu
            prefsMenu.setTearOffEnabled(True)
        newAction = prefsMenu.addAction("Build Zoo Shelves")
        newAction.triggered.connect(self.buildAsShelf)
        newAction = prefsMenu.addAction("Remove Zoo Shelves")
        newAction.triggered.connect(self.removeShelves)
        if self.preferenceInterface.loadShelfAtStartup():
            self.buildAsShelf()

    def removeShelves(self):
        for shelfData in self.shelfLayout.get("shelves", []):
            shelfName = shelfData["name"]
            shelves.cleanOldShelf(shelfName)

    def teardown(self):
        super(MayaPalette, self).teardown()
        self.removeShelves()

    def buildAsShelf(self):
        shelves = {}
        for shelfData in self.shelfLayout.get("shelves", []):
            shelf = self._shelfCreatorMaya(shelfData)
            if shelf:
                shelves[shelf.shortName()] = shelf
        try:
            activeShelf = shelves.get(self.preferenceInterface.defaultShelf())
        except core.SettingsNameDoesntExistError:
            # in the case where the default shelf key isn't defined just warning
            logger.warning("Couldn't set default shelf due to preference key not existing!")
            return
        if activeShelf is not None and self.preferenceInterface.isActiveAtStartup():
            activeShelf.setAsActive()

    def _createShelfButton(self, parentShelf, dataEntry):
        """

        :param parentShelf:
        :type parentShelf: :class:`zoo.libs.maya.utils.shelves.Shelf`
        :param dataEntry:  {id: "", "type": "", variants: [{"name": "", "label": "", "icon": "", "arguments": {}}]}
        :type dataEntry: dict
        :return:
        :rtype:
        """
        pluginId = dataEntry.get("id")
        pluginType = dataEntry.get("type", "definition")
        variants = dataEntry.get("children", [])

        # use mayas separator
        if pluginType == "separator":
            parentShelf.addSeparator()
            return
        command, uiData = "", {}
        if pluginId:
            command, uiData = self._processButtonType(pluginType, pluginId, overrides=dataEntry,
                                                      children=variants)
        if not command and not variants:
            msg = "Unknown supported plugin type: {}, plugin id:{}".format(pluginType, pluginId)
            logger.warning(msg, extra={"type": pluginType, "id": pluginId})
            om2.MGlobal.displayWarning(msg)
            return

        # if the plugin type is a command we except it to be a zoocommand  Id so find it
        # maya has a fit if the command string is empty
        icon = dataEntry.get("icon", uiData.get("icon"))

        uiData.update(dataEntry)
        if icon:
            icon = self._icon(icon, path=True)
        btn = parentShelf.addButton(uiData.get("label", ""), icon=icon,
                                    command=command,
                                    tooltip=uiData.get("tooltip", ""),
                                    style="iconOnly")

        if variants:
            pop = cmds.popupMenu(uiData.get("label", str(uuid.uuid4())) + "ctxMenu", button=1, parent=btn)
            processedVarients = []
            for variant in variants:
                # skip all duplicate variants
                variantId = variant.get("id")
                variantType = variant.get("type")

                if variantId in processedVarients:
                    continue
                elif variantType == "separator":
                    parentShelf.addMenuSeparator(pop)
                    continue
                if variantType is None:
                    variant.setdefault("arguments", {})["variant"] = variantId
                    menuCommand, menuUiData = self._processButtonType(pluginType, pluginId, overrides=variant,
                                                                      children=[])
                else:
                    menuCommand, menuUiData = self._processButtonType(variantType, variantId, overrides=variant,
                                                                      children=[])
                if not menuCommand or not menuUiData:
                    continue
                label = variant.get("label", menuUiData["label"])
                icon = variant.get("icon", menuUiData["icon"])
                if icon:
                    icon = self._icon(icon, path=True)
                parentShelf.addMenuItem(pop, label, command=menuCommand, icon=icon)

    def _processButtonType(self, pluginType, pluginId, overrides, children):
        command, uiInfo = "", {}
        if pluginType == "command":
            plugin = self.executor.findCommand(pluginId)
            if not plugin:
                msg = "Couldn't find zoo command with the id {}".format(pluginId)
                logger.warning(msg)
                om2.MGlobal.displayWarning(msg)
                return command, uiInfo
            uiInfo = plugin.uiData
            args = overrides.get("arguments", {})
            command = SHELFBUTTON_ZOOCOMMAND.format(pluginId, "{}".format(args))
        elif pluginType == "definition":
            plugin = self.pluginFromId(pluginId)
            if not plugin:
                logger.warning("Couldn't load zoo plugin {}".format(pluginId))
                return command, uiInfo
            # returns a list of dict
            uiInfo = plugin.uiData
            args = overrides.get("arguments", {})
            command = SHELFBUTTON_DEFINTION_COMMAND.format(pluginId, args)
            children.extend(plugin.variants())
        elif pluginType == "toolset":
            plugin = self.toolsetFromId(pluginId)
            if not plugin:
                msg = "Couldn't find toolset with the id {}".format(pluginId)
                logger.warning(msg)
                om2.MGlobal.displayWarning(msg)
                return command, uiInfo
            uiInfo = plugin.uiData
            command = TOOLSET_COMMAND.format(pluginId)
        return command, uiInfo

    def _shelfCreatorMaya(self, data):
        shelfName = data["name"]
        children = data["children"]
        # remove the old shelf if it exists
        shelves.cleanOldShelf(shelfName)
        # if we dont have any children then we dont need a shelf
        if not children:
            return
        # create an empty shelf
        newShelf = shelves.Shelf(shelfName)
        newShelf.createShelf()
        for child in children:
            self._createShelfButton(newShelf, child)
        if data.get("active", False):
            newShelf.setAsActive()
        return newShelf


class ShelfLayout(OrderedDict):

    def __init__(self, seq=None):  # known special case of dict.__init__
        seq = seq or {}
        shelves = seq.get("shelves", [])
        for shelf in shelves:
            shelf["name"] = shelf["name"].replace(" ", "_")
        super(ShelfLayout, self).__init__(seq)

    def shelf(self, name):
        """Returns the shelf with the given name from the Layout"""
        for i in self.get("shelves", []):
            if i["name"] == name:
                return i

    def updateFromChild(self, shelf, child):
        """Recursive function that loops the child of the dict.children

        If a child with the id already exists then :meth:`updateFromChild` will be called on the child
        If the child doesn't exist it will be appended.
        """
        if child.get("type") == "separator":
            shelf.setdefault("children", []).append(child)
            return
        for shelfChild in shelf.get("children", []):
            if shelfChild.get("id", "") == child["id"]:
                for subChild in child.get("children", []):
                    self.updateFromChild(shelfChild, subChild)
                break
        else:
            shelf.setdefault("children", []).append(child)

    def update(self, layout):
        sourceShelves = layout.get("shelves")

        assert sourceShelves is not None, "shelves key is missing"
        for shelf in sourceShelves:
            self.updateShelf(shelf)

    def updateShelf(self, shelf):
        shelfName = shelf["name"]
        sourceShelf = self.shelf(shelfName)
        if sourceShelf is None:
            self.setdefault("shelves", []).append(shelf)
            return
        for child in shelf.get("children", []):
            self.updateFromChild(sourceShelf, child)
