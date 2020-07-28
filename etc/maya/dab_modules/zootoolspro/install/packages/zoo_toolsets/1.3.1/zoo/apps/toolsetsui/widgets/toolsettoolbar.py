from zoo.apps.toolsetsui.widgets import toolsetwidgetitem
from zoo.libs.pyqt.widgets import flowtoolbar, iconmenu
from zoo.libs.utils import colour


class ToolsetToolBar(flowtoolbar.FlowToolBar):
    """ Toolset Toolbar, builds the shelf icons up the top

    """

    def __init__(self, toolbarFrame, parent=None, toolsetRegistry=None, iconSize=20, iconPadding=2):
        """

        :param toolbarFrame:
        :type toolbarFrame: zoo.apps.toolsetsui.widgets.toolsetframe.ToolsetFrame
        :param parent:
        """

        super(ToolsetToolBar, self).__init__(parent=parent, iconSize=iconSize, iconPadding=iconPadding)

        self.toolbarFrame = toolbarFrame
        self.toolsetRegistry = toolsetRegistry
        self.overflowMenuActive(True)

    def addToolset(self, toolset, toggleConnect=None):
        """ ToolsetToolbars version of addTool

        :param toggleConnect: Connect the toggle visibility event, expects a function that takes \
                              one parameter (toolsetId)
        :type toggleConnect: toolsetframe.ToolsetFrame.toggleToolset
        :param toolset: Class definitions of the toolset, usually passed in by the toolset registry
        :type toolset: toolsetwidgetitem.ToolsetWidgetItem
        :param color:
        :return:
        :rtype: iconmenu.IconMenuButton
        """
        color = self.toolsetRegistry.toolsetColor(toolset.id)
        dullColor = colour.desaturate(color, 0.75)

        retBtn = self.addToolButton(toolset.uiData['icon'], toolset.uiData['label'], dullColor, doubleClickEnabled=True)
        retBtn.setToolTip(toolset.uiData['label'])
        retBtn.setProperty('toolsetId', toolset.id)
        retBtn.setProperty('colorDisabled', dullColor)
        retBtn.setProperty('color', color)
        retBtn.setProperty('iconName', toolset.uiData['icon'])

        retBtn.leftClicked.connect(lambda btn=retBtn: toggleConnect(toolset.id, activate=True))
        retBtn.middleClicked.connect(lambda btn=retBtn: toggleConnect(toolset.id, activate=False))

        if toolset.uiData['defaultActionDoubleClick']:
            retBtn.leftDoubleClicked.connect(lambda: self.doubleClicked(toolset, toggleConnect=toggleConnect))
        else:
            retBtn.setDoubleClickEnabled(False)

        return retBtn

    def doubleClicked(self, toolset, toggleConnect):
        """ Default action of the toolset

        :param toggleConnect:
        :param toolset:
        :return:
        """

        toolsetObj = self.toolbarFrame.toolset(toolset.id)

        # Create a toolset and add it to the tree if its not done yet
        if toolsetObj is None:
            toolsetObj = toggleConnect(toolset.id, hidden=True)

        # Run default action
        toolsetObj.defaultAction()


