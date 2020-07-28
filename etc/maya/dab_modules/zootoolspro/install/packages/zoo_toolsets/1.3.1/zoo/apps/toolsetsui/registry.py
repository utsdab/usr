import logging
import os

from Qt import QtWidgets, QtCore

from zoo.apps.toolsetsui.widgets import toolsetwidget, toolsetwidgetmaya
from zoo.libs.plugin import pluginmanager
from zoo.libs.utils import colour, env
from zoo.libs.utils import filesystem

logger = logging.getLogger(__name__)


class ToolsetRegistry(QtCore.QObject):
    """Registry class to gather all the toolset classes.

    .. code-block:: python

        os.environ["ZOO_TOOLSET_UI_PATHS"] = "../examples/widgets"
        os.environ["ZOO_TOOLSET_LAYOUTS"] = "../examples/zootoolsets"
        reg = ToolsetRegistry()
        self.logger.debug("{}".format(reg.toolsetDefs))
        {'ConvertAllShadersRenderer': <class zoo.apps.generictoolsetui.zootoolsets.convertallshaders_renderer.ConvertAllShadersRendererToolset>,
        'importExportShaders': <class zoo.apps.generictoolsetui.zootoolsets.importexportshaders.ImportExportShadersToolset}

    """
    registryEnv = "ZOO_TOOLSET_UI_PATHS"
    toolsetJsons = "ZOO_TOOLSET_LAYOUTS"

    def __init__(self):
        # for discovering the component models
        self.toolsetDefs = {}
        self.toolsetGroups = []

        # should consult with dave?
        if env.isInMaya():
            self._manager = pluginmanager.PluginManager(interface=[
                toolsetwidgetmaya.ToolsetWidgetMaya, toolsetwidget.ToolsetWidget], variableName="id")
        else:
            self._manager = pluginmanager.PluginManager(interface=toolsetwidget.ToolsetWidget, variableName="id")

    def readJsons(self):
        """
        Merge the data in the jsons and put into one data structure: self.toolsetGroups

        :todo: Work with collisions
        :return:
        """
        jsonPaths = os.environ[self.toolsetJsons].split(os.pathsep)

        for jp in jsonPaths:
            self.toolsetGroups += filesystem.loadJson(jp)['toolsetGroups']

        self.toolsetGroups.sort(key=lambda x: x["name"])

    def discoverToolsets(self):
        """Searches the component library specfied by the environment variable "ZOO_TOOLSET_UI_PATHS"
        """
        self.readJsons()
        self.toolsetDefs = {}
        paths = os.environ[self.registryEnv].split(os.pathsep)

        if not paths:
            return False

        self._manager.registerPaths(paths)

        for toolset in self._manager.plugins.values():
            self.toolsetDefs[toolset.id] = toolset

        return True

    def groupType(self, groupName):
        """Get type by group name

        :param groupName:
        :return:
        """
        for g in self.toolsetGroups:
            if g['name'] == groupName:
                return g['type']

    def groupColor(self, groupType):
        for g in self.toolsetGroups:
            if g['type'] == groupType:
                return g['color']

    def toolsetColor(self, toolsetId):
        """
        Calculate colour based on the group colour from where it was found.
        Also shifts the colour depending on its position in the list.
        The further down the list, the more the colour gets shifted.

        :param toolsetId:
        :return:
        """
        for g in self.toolsetGroups:
            if toolsetId in g['toolsets']:
                index = g['toolsets'].index(toolsetId)
                groupColor = tuple(g['color'])
                hueShift = g['hueShift'] * (index + 1)

                return tuple(colour.hueShift(groupColor, hueShift))

        logger.warning("toolsetId \"{}\" not found in any toolset group data dictionary for colours".format(toolsetId))

        return (255, 255, 255)

    def groupTypes(self):
        """Return group types

        :return: list(type)
        """
        return [g['type'] for g in self.toolsetGroups]

    def groupNames(self):
        """Return list of names

        :return:
        """
        return [g['name'] for g in self.toolsetGroups]

    def definitions(self, sort=True):
        """Returns a list of toolset definitions

        :return:
        """
        ret = self.toolsetDefs.values()
        if sort:
            ret = list(ret)
            ret.sort(key=lambda toolset: toolset.uiData['label'])

        return ret

    def toolsetIds(self, groupType):
        """ Return toolsets based on group type.

        :param groupType:
        :return:
        """
        for g in self.toolsetGroups:
            if g['type'] == groupType:
                return g['toolsets']

    def groupFromToolset(self, toolsetId):
        """ Looks for the original group

        :param toolsetId:
        :return groupType: groupType
        """

        for g in self.toolsetGroups:
            for t in g['toolsets']:
                if t == toolsetId:
                    return g['type']

    def toolsets(self, groupType):
        """ List of toolsets under the group type

        :param groupType:
        :return:
        :rtype: class of toolsetwidget.ToolsetWidgetMaya
        """
        toolsetIds = self.toolsetIds(groupType)
        return [self.toolset(t) for t in toolsetIds]

    def toolsetWidget(self, toolsetId):
        """ Creates a new toolset widget based on the toolsetId

        returns list of widgets. Each widget is the different content sizes eg simplified, advanced
        # todo this needs to be updated to work with the new toolsetWidget changes

        :param toolsetId:
        :return:
        """

        toolsetClass = self.toolset(toolsetId)

        ret = []
        for applyContents in toolsetClass.contents():
            newWidget = QtWidgets.QWidget()
            newWidget.setProperty("color", self.toolsetColor(toolsetId))
            applyContents(newWidget, None, None)  # Apply contents to widget
            ret.append(newWidget)

        return ret

    def toolset(self, toolsetID):
        """ Returns toolset based on Id

        :param toolsetID: toolset to find by id
        :type toolsetID: basestring
        :rtype: toolsetwidgetmaya.ToolsetWidgetMaya
        """
        ret = self.toolsetDefs.get(toolsetID)

        if ret is None:
            raise KeyError("\"{}\" tool set not found. Make sure the toolset ID name is correct in toolsetgroups, "
                           "or make sure the toolset has been added correctly..".format(toolsetID))

        return ret


def toolset(toolsetID):
    """ Gets a toolset definition class by ID.

    Creates a new toolsetRegsistry instance and runs ToolsetRegistry.toolset()
    May be slow since it creates the instance and discovers the toolsets.

    .. code-block:: python

        from zoo.apps.toolsetsui import registry
        toolsetCls = registry.toolset("zooVertSkinning")

        zooVertSkinning = toolsetCls()

    :param toolsetID: toolset to find by id
    :type toolsetID: basestring
    :return: Subclass of ToolsetWidgetItem. Toolset class definition
    :rtype: toolsetwidgetmaya.ToolsetWidgetMaya

    """

    toolsetRegistry = ToolsetRegistry()
    toolsetRegistry.discoverToolsets()
    return toolsetRegistry.toolset(toolsetID)
