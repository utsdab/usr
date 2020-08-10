"""This Module handles the base class for the zootools main menu.

:todo: replace hardcoded tool types with a plugin system to better handle tool distribution
"""
import abc
import os
import sys
import traceback
import uuid
from zoovendor import six
from functools import partial
from collections import OrderedDict
from zoovendor.six import string_types
from zoovendor.six import itervalues

from zoo.libs import iconlib

from zoo.libs.plugin import plugin
from zoo.libs.plugin import pluginmanager
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.extended import searchablemenu
from zoo.libs.utils import filesystem, env
from zoo.libs.utils import zlogging
from zoo.preferences.core import preference
from zoo.core import api

if env.isInMaya():
    from zoo.libs.maya.qt import mayaui

logger = zlogging.getLogger(__name__)


class ToolPalette(pluginmanager.PluginManager):
    TOOLSENV = "ZOO_TOOLDEFINITION_MODULES"
    LAYOUTENV = "ZOO_MENU_LAYOUTS"

    def __init__(self, parent=None):
        super(ToolPalette, self).__init__()
        self.parent = parent
        self.subMenus = {}

        # builds the environment for zap plugin
        self.menuName = preference.findSetting("prefs/maya/artistpalette.pref", root=None, name="menu_name")
        self.menuObjectName = "Zootools_mainMenu"
        self.menu = None
        self.layout = {}
        self._loadLayouts()
        self.loadAllPlugins()

    def removePreviousMenus(self):
        """Removes Any zoo plugin menu from maya by iterating through the children of the main window looking for any
        widget with the objectname Zoo Tools.
        """
        for childWid in self.parent.menuBar().children():
            if childWid.objectName() == self.menuObjectName:
                childWid.deleteLater()

    def createMainMenu(self):
        # todo: investigate why custom classes fails in maya menus and cmds.menu(q=True, label=self.menuName)
        # self.menu = searchablemenu.SearchableMenu(objectName=self.menuObjectName,
        #                                           title=self.menuName, parent=self.parent.menuBar())

        self.menu = self.parent.menuBar().addMenu(self.menuName)
        self.menu.setObjectName(self.menuObjectName)
        self.menu.setTearOffEnabled(True)

    def createMenus(self):
        """Loops through all loadedPlugins and creates a menu/action for each. Uses the plugin class objects parent
        variable to determine where  it sits within the menu.
        """
        self.removePreviousMenus()
        self.createMainMenu()
        # load the layout
        for i in iter(self.layout["menu"]):
            if isinstance(i, string_types) and i == "separator":
                self.menu.addSeparator()
                continue
            self._menuCreator(self.menu, i)
        devMenu = self.subMenus.get("Developer")
        if not devMenu:
            # build developer menu
            devMenu = self.menu.addMenu("Developer")
            self.subMenus["Developer"] = devMenu
        devMenu.setTearOffEnabled(True)
        logMenu = utils.loggingMenu()
        devMenu.addMenu(logMenu)
        self.menu.addSeparator()
        self.menu.addAction("Zoo Tools PRO - {}".format(api.currentConfig().buildVersion()))
        # a fix for 2016
        self.parent.menuBar().show()

    def _menuCreator(self, parentMenu, data):
        menu = self.getMenu(data["label"])
        if menu is None and data.get("type", "") == "menu":
            menu = parentMenu.addMenu(data["label"])
            menu.setObjectName(data["label"])
            menu.setTearOffEnabled(True)
            self.subMenus[data["label"]] = menu

        if "children" not in data:
            return
        for i in iter(data["children"]):
            actionType = i.get("type", "definition")
            if actionType == "separator":
                self.menu.addSeparator()
                continue
            elif actionType == "group":
                sep = menu.addSeparator()
                sep.setText(i["label"])
                continue
            elif actionType == "menu":
                self._menuCreator(menu, i)
                continue
            self._addAction(i, menu)

    def _addAction(self, itemInfo, parent):
        pluginId = itemInfo["id"]
        pluginType = itemInfo.get("type", "definition")
        plugin = None
        if pluginType == "definition":
            plugin = self.pluginFromId(pluginId)
        elif pluginType == "toolset":
            plugin = self.toolsetFromId(pluginId)
        if plugin is None:
            # skip any plugin which can't be found
            logger.warning("Failed to find Plugin: {}, type: {}".format(pluginId, pluginType))
            return
        uiData = plugin.uiData
        label = uiData.get("label", "No_label")
        taggedAction = searchablemenu.TaggedAction(label, parent=self.parent)
        isCheckable = uiData.get("isCheckable", False)
        isChecked = uiData.get("isChecked", False)
        if isCheckable:
            taggedAction.setCheckable(isCheckable)
            taggedAction.setChecked(isChecked)
            taggedAction.toggled.connect(partial(self.executePlugin, plugin))
            if pluginType == "definition":
                taggedAction.toggled.connect(partial(self.executePlugin, plugin))
                if uiData.get("loadOnStartup", False):
                    self.executePlugin(plugin, isChecked)
            elif pluginType == "toolset":
                taggedAction.toggled.connect(partial(self.openToolSet, pluginId))

        else:
            if pluginType == "definition":
                taggedAction.triggered.connect(partial(self.executePlugin, plugin))
                if uiData.get("loadOnStartup", False):
                    self.executePlugin(plugin)
            elif pluginType == "toolset":
                taggedAction.triggered.connect(partial(self.openToolSet, pluginId))

        icon = uiData["icon"]
        if icon:
            icon = self._icon(icon)
            if icon:
                taggedAction.setIcon(icon)
        taggedAction.tags = set(plugin.tags)

        parent.addAction(taggedAction)
        logger.debug("Added action, {}".format(label))

    def _icon(self, iconName, path=False):
        if path:
            icon = iconlib.iconPathForName(iconName, size=32)
            return icon
        icon = iconlib.icon(iconName, size=32)
        if icon is None:
            return
        elif not icon.isNull():
            return icon

    def shutdown(self):
        """Shutdown's all of zoo triggers the reloads zoo code.
        """
        self.teardown()
        self.removePreviousMenus()

    def executePluginById(self, pluginId, *args, **kwargs):
        """Executes the tooldefinition plugin by the id string.

        :param pluginId: The tooldefinition id.
        :type pluginId: str
        :param args: The arguments to pass to the execute method
        :type args: tuple
        :param kwargs: The keyword arguments to pass to the execute method
        :type kwargs: dict
        :return: The executed tooldefinition instance or none
        :rtype: :class:`ToolDefinition` or None
        """
        for p in self.loadedPlugins.values():
            if p.id == pluginId:
                return self.executePlugin(p, *args, **kwargs)

    def executePluginByName(self, name, *args, **kwargs):
        """Executes the tooldefinition plugin by the className.

        :param pluginId: The tooldefinition className.
        :type pluginId: str
        :param args: The arguments to pass to the execute method
        :type args: tuple
        :param kwargs: The keyword arguments to pass to the execute method
        :type kwargs: dict
        :return: The executed tooldefinition instance or none
        :rtype: :class:`ToolDefinition` or None
        """
        if name in self.loadedPlugins:
            plugin = self.loadedPlugins[name]
            self.executePlugin(plugin, *args, **kwargs)

    def applyStyleSheet(self, stylesheet):
        """ Apply stylesheet to all plugins

        :param stylesheet: Stylesheet
        :type stylesheet: basestring
        :return:
        """
        for plugin in self.loadedPlugins.values():
            plugin.setStyleSheet(stylesheet)

    def executePlugin(self, plugin, *args, **kwargs):
        """Executes the tooldefinition plugin.

        :param pluginId: The tooldefinition instance.
        :type pluginId: :class:`ToolDefinition`
        :param args: The arguments to pass to the execute method
        :type args: tuple
        :param kwargs: The keyword arguments to pass to the execute method
        :type kwargs: dict
        :return: The executed tooldefinition instance or none
        :rtype: :class:`ToolDefinition` or None
        """
        plugin._execute(*args, **kwargs)
        logger.debug("Execution time:: {}".format(plugin.stats.executionTime))
        return plugin

    def executeAll(self):
        """Calls the execute method on all currently loaded plugins
        """
        for plug in itervalues(self.loadedPlugins):
            plug.execute()

    def teardown(self):
        logger.debug("Attempting to teardown plugins")
        for plugName, plug in self.loadedPlugins.items():
            plug.runTearDown()
            logger.debug("shutting down tool -> {}".format(plug.id))
        self.unloadAllPlugins()

        self.plugins = {}
        if self.menu:
            logger.debug("Closing menu-> %s" % self.menuName)
            self.removePreviousMenus()
            self.menu = None

    def getMenu(self, menuName):
        """Returns the menu object if it exists else None.

        :param menuName: str, the menuName to retrieve.
        :return: QMenu.
        """
        if menuName == self.menu.objectName():
            return self.menu
        return self.subMenus.get(menuName)

    def pluginFromId(self, id):
        """Returns the plugin by id string.

        :param id: The tooldefinition id.
        :type id: str
        :return: The executed tooldefinition instance or none
        :rtype: :class:`ToolDefinition` or None
        """
        for i in iter(self.loadedPlugins.values()):
            if i.id == id:
                return i

    def pluginFromTool(self, tool):
        for i in iter(self.loadedPlugins.values()):
            for t in i.tool:
                if t['tool'] == tool:
                    return i

    def _loadLayouts(self):
        self.registerPaths(paths=[i for i in os.environ.get(ToolPalette.TOOLSENV, "").split(os.pathsep) if i])
        paletteLayout = os.environ.get(ToolPalette.LAYOUTENV, "").split(os.pathsep)
        if not paletteLayout:
            raise ValueError("No Layout configuration has been defined")
        layout = MenuLayout()
        layouts = []
        for f in iter(paletteLayout):
            if os.path.exists(f) and f.endswith(".layout") and os.path.isfile(f):
                try:
                    dataStruct = filesystem.loadJson(f, object_pairs_hook=OrderedDict)
                except ValueError:
                    logger.error("Failed to load menu layout file due to possible syntax issue, {}".format(f))
                    continue
                layouts.append(dataStruct)
        for sortedLayout in sorted(layouts, key=lambda x: x.get("sortOrder", 0)):
            layout.update(sortedLayout)

        self.layout = layout

    def toolsetFromId(self, toolId):
        """ Finds and returns a toolset class.

        :param toolId: The toolset id value
        :type toolId: str
        :return:
        :rtype:
        :note: toolset raises a key error but we ignore it here and just log a warning
        this way the menus and shelf continue to build but skips creating actions.
        :note: if a Import error occurs it's because toolsets isnt part of the environment
        and someone left a toolset in the env.
        :note: We internal cache the toolset registry on this instance because toolset
        discovery isn't cached but rediscovered so here we do the cache ourselves.
        """
        try:
            # if importing fails it means some dummy left a toolset definition in the
            # layout
            from zoo.apps.toolsetsui import registry

            if hasattr(self, "_toolsetRegistry"):
                reg = getattr(self, "_toolsetRegistry")
            else:
                # due to the inefficient toolset discovery we just cache the a local
                # registry
                reg = registry.ToolsetRegistry()
                self._toolsetRegistry = reg
                reg.discoverToolsets()

            return reg.toolset(toolId)
        except ImportError:
            logger.warning("Missing Toolset in environment skipping tool: {}".format(toolId),
                           exc_info=True)
        except KeyError:
            logger.warning("Missing Toolset by id: {}".format(toolId),
                           exc_info=True)

    def openToolSet(self, toolId):
        """ Open toolset by the tool id

        :param toolId:
        :type toolId:
        :return:
        :rtype:
        """
        from zoo.apps.toolsetsui import run
        run.openTool(toolId)


class MenuLayout(OrderedDict):
    def shelf(self, name):
        """Returns the shelf with the given name from the Layout"""
        for i in self.get("menu", []):
            if i["label"] == name:
                return i

    def updateFromChild(self, shelf, child):
        """Recursive function that loops the child of the dict.children

        If a child with the id already exists then :meth:`updateFromChild` will be called on the child
        If the child doesn't exist it will be appended.
        """

        if child.get("id") is not None:
            for shelfChild in shelf["children"]:
                if shelfChild.get("id", "") == child["id"]:
                    for subChild in child.get("children", []):
                        self.updateFromChild(shelfChild, subChild)
                    break
            else:
                shelf.setdefault("children", []).append(child)
        else:
            shelf.setdefault("children", []).append(child)

    def update(self, layout):
        sourceShelves = layout.get("menu")
        assert sourceShelves is not None, "menu key is missing"

        for shelf in sourceShelves:
            self.updateMenu(shelf)

    def updateMenu(self, shelf):
        shelfName = shelf["label"]
        sourceShelf = self.shelf(shelfName)
        if sourceShelf is None:
            self.setdefault("menu", []).append(shelf)
            return
        for child in shelf.get("children", []):
            self.updateFromChild(sourceShelf, child)


@six.add_metaclass(abc.ABCMeta)
class ToolDefinition(plugin.Plugin):
    uiData = {"icon": "",
              "tooltip": "",
              "label": "",
              "color": "",
              "backgroundColor": "",
              "dock": {"dockable": False, "area": "left"},
              "isCheckable": True,
              "isChecked": True,
              "frameless": {"frameless": True, "force": False},
              "multipleTools": False,
              "loadOnStartup": True
              }

    def __init__(self, manager):
        super(ToolDefinition, self).__init__(manager=manager)
        self.tool = []
        self._bootstrap = []

    @abc.abstractproperty
    def id(self):
        pass

    @abc.abstractproperty
    def creator(self):
        pass

    @abc.abstractmethod
    def execute(self, *args, **kwargs):
        pass

    def runTearDown(self):
        try:
            self.teardown()
        except RuntimeError:
            logger.error("Failed to teardown plugin: {}".format(self.id),
                         exc_info=True)
        finally:
            try:
                for bootstrap in self._bootstrap:
                    bootstrap.close()
            except RuntimeError:
                logger.error("Bootstrap already deleted: {}".format(str(self._bootstrap)),
                             exc_info=True)
            except Exception:
                logger.error("Failed to remove bootstrap window: {}".format(str(self._bootstrap)),
                             exc_info=True)

    def teardown(self):
        pass

    def variants(self):
        return []

    def setStyleSheet(self, style):
        pass

    def setFrameless(self, tool, frameless):
        pass

    def runTool(self, framelessActive=True, toolArgs=None):
        pass

    def toolClosed(self, tool):
        pass

    def latestTool(self):
        """ Get latest added tool

        :return:
        :rtype:
        """
        try:
            return self.tool[-1]['tool']
        except IndexError:
            return None

    @staticmethod
    def latestStyleSheet():
        """ Returns the latest stylesheet from the zootools preferences

        :return: the stylesheet str which can be used to directly set the widget stylesheet
        :rtype: str
        """
        coreInterface = preference.interface("core_interface")
        try:
            result = coreInterface.stylesheet()
            return result.data
        except ValueError:
            logger.warning("Failed to set stylesheet, no biggie continue with life!")

    def _execute(self, *args, **kwargs):
        """ Modified version from ToolDefinition to allow multiple tools.

        :param args:
        :param kwargs:
        :return:
        """
        self.stats.start()
        exc_type, exc_value, exc_tb = None, None, None
        try:
            tool = self.execute(*args, **kwargs)
            if tool is not None and tool.get("tool") is not None:
                # temp until a maya version of the tooldefinition is added
                if self.uiData.get("dock", {}).get("dockable", False):
                    uid = None
                    if self.uiData.get("multipleTools"):
                        # Create unique id
                        uid = "{0} [{1}]".format(self.uiData["label"], str(uuid.uuid4()))
                    bootstrapWidget = mayaui.BootStrapWidget(tool['tool'], self.uiData["label"], uid)
                    tool['bootstrap'] = bootstrapWidget
                    tool['bootstrap'].show(retain=False, **self.uiData.get("dock", {}))
                    tool['tool'].window().setProperty('tool', tool['tool'])  # temp code till new frameless comes in
                    self._bootstrap.append(bootstrapWidget)

        except Exception:
            exc_type, exc_value, exc_tb = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_tb)
            raise
        finally:
            tb = None
            if exc_type and exc_value and exc_tb:
                tb = traceback.format_exception(exc_type, exc_value, exc_tb)
            self.stats.finish(tb)

    def executeFrameless(self, *args, **kwargs):
        """ Run the frameless code

        Runs the tool and applies the frameless code to it

        :param toolArgs: dictionary of arguments for runTool
        :type toolArgs: dict
        :param defaultFrameless: The default value for frameless if frameless is not forced by the ToolDefinition
        :return:
        """
        # todo: Should be replaced with universal behaviour,
        # todo: re-evaluate all of the frameless code to not be such a hack on widgets
        # todo: should be a plug and play solution and and not care whether its a frameless window or not.

        executeFrameless = kwargs.get("executeFrameless", None)
        defaultFrameless = self.framelessWindowToggle()

        # If frameless is forced use what is given in uiData
        if executeFrameless is None:
            framelessActive = defaultFrameless
        else:
            framelessActive = executeFrameless

        # Launch the tool and set the stylesheet
        tool = self.runTool(framelessActive, kwargs)

        ret = {'tool': tool, 'bootstrap': None}
        if hasattr(tool, "closed"):
            # Append the tool to self.tool and save settings
            self.uiData['dock']['dockable'] = not framelessActive
            self.tool.append(ret)

            # On tool closed, clean up
            tool.closed.connect(partial(self.toolClosed, ret))

        return ret

    def framelessWindowToggle(self):
        """ Return the current framelessWindowToggle

        :return:
        """
        ret = self.manager.pluginFromId("zoo.frameless.state").state
        return ret
