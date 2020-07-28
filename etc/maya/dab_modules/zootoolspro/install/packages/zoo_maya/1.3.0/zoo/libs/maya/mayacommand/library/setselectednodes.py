from maya.api import OpenMaya  as om2
from zoo.libs.command import command
from zoo.libs.maya.api import scene


class SetSelectedNodes(command.ZooCommand):
    """This command selected maya nodes

    """
    id = "zoo.maya.setSelectedNodes"
    creator = "David Sparrow"
    isUndoable = True
    uiData = {"icon": "",
              "tooltip": __doc__,
              "label": "Select Nodes",
              "color": "",
              "backgroundColor": ""
              }
    _modifier = None
    currentSelection = []

    def resolveArguments(self, arguments):
        nodes = arguments.get("nodes")
        if not nodes:
            self.cancel("No nodes to select")
        self.currentSelection = om2.MSelectionList()
        for i in scene.getSelectedNodes():
            self.currentSelection.add(i)
        validNodes = []
        for i in nodes:
            mHandle = om2.MObjectHandle(i)
            if mHandle.isValid() and mHandle.isAlive():
                validNodes.append(mHandle)
        arguments["nodes"] = validNodes
        return arguments

    def doIt(self, nodes=None):
        """
        :param nodes:
        :type nodes: seq or om2.MSelectionList
        :return:
        :rtype: om2.MObjectArray
        """

        mSel = om2.MSelectionList()
        for i in iter(nodes):
            mSel.add(i)
        om2.MGlobal.setActiveSelectionList(mSel)
        return nodes

    def undoIt(self):
        if self.currentSelection:
            om2.MGlobal.setActiveSelectionList(self.currentSelection)
