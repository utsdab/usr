from zoo.apps.toolsetsui.toolsetcallbacks import SelectionCallbacksMaya
from zoo.apps.toolsetsui.widgets.toolsetwidget import ToolsetWidget
from zoo.libs.maya.cmds.general import undodecorator

undoDecorator = undodecorator.undoDecorator


class ToolsetWidgetMaya(ToolsetWidget):
    """ Maya specific code for toolset widgets

    """

    def __init__(self, *args, **kwargs):
        super(ToolsetWidgetMaya, self).__init__(*args, **kwargs)
        self.selectionCallbacks = SelectionCallbacksMaya()


    def updateFromProperties(self):
        """ Fill in the widgets based on the properties.  Will affect widgets linked in the toolset UI via:

        For Maya block callbacks as well

        :return:
        :rtype:
        """
        self.blockCallbacks(True)
        super(ToolsetWidgetMaya, self).updateFromProperties()
        self.blockCallbacks(False)

    def stopCallbacks(self):
        """ Stop all callbacks

        :return:
        :rtype:
        """
        self.stopSelectionCallback()

    def blockCallbacks(self, block):
        self.selectionCallbacks.blockCallbacks(block)

    def startSelectionCallback(self):
        self.selectionCallbacks.startSelectionCallback()

    def stopSelectionCallback(self):
        self.selectionCallbacks.stopSelectionCallback()

    # ------------------------------------
    # UNDO CHUNKS
    # ------------------------------------
    def openUndoChunk(self):
        """Opens the Maya undo chunk"""
        undodecorator.openUndoChunk()

    def closeUndoChunk(self):
        """Opens the Maya undo chunk"""
        undodecorator.closeUndoChunk()

    def connections(self):
        """ Stop callbacks

        :return:
        :rtype:
        """
        super(ToolsetWidgetMaya, self).connections()
        self.deletePressed.connect(self.stopCallbacks)

