from zoovendor.six.moves import cPickle
import time

from Qt import QtCore, QtWidgets

from zoo.apps.toolsetsui.registry import ToolsetRegistry
from zoo.apps.toolsetsui.widgets import toolsettree, toolsetwidgetitem
from zoo.apps.toolsetsui.widgets.toolsetframe import ToolsetFrame
from zoo.libs import iconlib
from zoo.libs.pyqt import utils as qtutils, utils
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt.widgets import extendedbutton
from zoo.libs.pyqt.widgets.frameless import FramelessTitleBar
from zoo.libs.pyqt.widgets.framelessmaya import FramelessWindowMaya
from zoo.libs.utils import colour, zlogging
from zoo.preferences.core import preference

logger = zlogging.getLogger(__name__)

_TOOLSETUI_INSTANCES = []

TOOLSETUI_WIDTH = 390
TOOLSETUI_HEIGHT = 20

WINDOWHEIGHT_PADDING = 50


class ToolsetsUI(FramelessWindowMaya):

    def __init__(self, title="Toolsets", iconColour=(231, 133, 255), hueShift=-30,
                 width=qtutils.dpiScale(TOOLSETUI_WIDTH),
                 height=qtutils.dpiScale(TOOLSETUI_HEIGHT),
                 maxHeight=qtutils.dpiScale(800), framelessChecked=True, parent=None,
                 toolsetIds=None, position=None):
        self.toolsetRegistry = ToolsetRegistry()
        self.toolsetRegistry.discoverToolsets()

        super(ToolsetsUI, self).__init__(parent=parent, title=title, width=width, height=height,
                                         framelessChecked=framelessChecked,
                                         titleBarClass=ToolsetTitleBar, alwaysShowAllTitle=True)
        self.toolsetFrame = ToolsetFrame(self, self.toolsetRegistry, iconColour, hueShift,
                                         startHidden=False)
        self.toolsetFrame.setUpdatesEnabled(False)
        self.toolsetFrame.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

        self.setWindowTitle(title)
        
        self.hueShift = hueShift
        self.iconColour = iconColour
        self.mainLayout = elements.vBoxLayout()
        self.maxHeight = maxHeight
        self.resizedHeight = 0
        self.alwaysResizeToTree = True

        self.initUi()

        self.connections()

        self.initStyle()
        self.lastFocusedTime = time.time()

        toolsetIds = [] if toolsetIds is None else toolsetIds

        windowsOffset = (-30-self.width()/2, -50)  # todo: fix this. and may cause issues in other operating systems

        for t in toolsetIds:
            self.toggleToolset(t)
        self.toolsetFrame.setUpdatesEnabled(True)

        QtCore.QTimer.singleShot(0, self.toolsetFrame.updateColors)

        if position is not None:
            QtCore.QTimer.singleShot(0, lambda: self.move(position[0]+windowsOffset[0], position[1]+windowsOffset[1]))
        self.setHighlight(True, updateUis=True)

    def connections(self):
        self.toolsetFrame.resizeRequested.connect(self.resizeWindow)

    def maximize(self):
        width = self.savedSize.width()
        calcHeight = self.calcHeight()
        self.setUiMinimized(False)
        self._minimized = False

        # Use the resized height
        if calcHeight < self.resizedHeight:
            self.window().resize(width, self.resizedHeight)
        else:
            self.window().resize(width, calcHeight)

    def setHighlight(self, highlight, updateUis=False):
        """ Set the logo highlight.

        Update the other toolset uis

        :param highlight:
        :param updateUis:
        :return:
        """
        # Always set this one to highlight and don't unhighlight the other toolsets
        if self.isMinimized() and not highlight:
            self.titleBar.setLogoHighlight(True)
            return

        self.lastFocusedTime = time.time()

        if highlight and updateUis:
            # Get the last visible toolset
            for t in toolsetUis():
                if not t.isMinimized():
                    t.titleBar.setLogoHighlight(False)
            self.titleBar.setLogoHighlight(True)

    def initStyle(self):
        """
        Usually this is handled by ToolDefinitions, but we can also set it here if we need to.
        :return:
        """
        self.prefs = preference
        self.interface = self.prefs.interface("core_interface")
        self.setWindowStyleSheet(self.interface.stylesheet().data)

    def initUi(self):
        self.setMainLayout(self.mainLayout)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)  # this is the grey edge margin to the edge of the window

        self.titleBar.contentsLayout.addWidget(self.toolsetFrame)
        self.mainLayout.addWidget(self.toolsetFrame.tree)  # Pull out of toolsetFrame and add widget here instead
        self.mainLayout.setStretch(1, 1)

        self.titleBar.cornerContentsLayout.addWidget(self.toolsetFrame.menuBtn)
        self.windowResizedFinished.connect(self.resizeEndEvent)

        self.setMaximiseVisible(False)

    def setWindowStyleSheet(self, style):
        super(ToolsetsUI, self).setWindowStyleSheet(style)
        self.toolsetFrame.menuBtn.toolsetPopup.setStyleSheet(style)

    def calcHeight(self):
        self.maxHeight = self.maxWindowHeight()

        # Calc height
        newHeight = self.window().minimumSizeHint().height() + self.toolsetFrame.calcSizeHint().height()
        newHeight = self.maxHeight if newHeight > self.maxHeight else newHeight
        return newHeight

    def lastHidden(self):
        return self.toolsetFrame.tree.lastHidden

    def setLastHidden(self, lastHidden):
        self.toolsetFrame.tree.lastHidden = lastHidden

    def resizeWindow(self, disableScrollBar=True, delayed=False):
        """ Automatically resize the height based on the height of the tree

        :return:
        """

        if delayed:
            QtCore.QTimer.singleShot(0, lambda: self.resizeWindow(disableScrollBar))
            return

        # Max height
        if not self.isDocked():

            if disableScrollBar:
                self.toolsetFrame.tree.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

            self.maxHeight = self.maxWindowHeight()

            newHeight = self.window().minimumSizeHint().height() + self.toolsetFrame.calcSizeHint().height()
            newHeight = self.maxHeight if newHeight > self.maxHeight else newHeight  # Limit height
            width = self.window().rect().width()
            minHeight = self.window().minimumHeight()

            self.window().resize(width, newHeight)

            # Use the resized height
            if newHeight < self.resizedHeight and self.alwaysResizeToTree is False:
                self.window().resize(width, self.resizedHeight)
            else:
                # Resize the window based on the tree size
                self.window().resize(width, newHeight)
                self.resizedHeight = newHeight

            if disableScrollBar:
                self.toolsetFrame.tree.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        else:
            self.setMinimumSize(QtCore.QSize(self.width(), 300))
            self.setMinimumSize(QtCore.QSize(0, 0))

    def maxWindowHeight(self):
        """ Calculate max height depending on the height of the screen.

        :return:
        :rtype:
        """

        pos = self.mapToGlobal(QtCore.QPoint(0, 0))
        desktop = QtWidgets.QApplication.desktop()
        screen = desktop.screenNumber(desktop.cursor().pos())
        screenHeight = desktop.screenGeometry(screen).height()
        relativePos = pos - QtCore.QPoint(desktop.screenGeometry(self).left(), desktop.screenGeometry(self).top())

        return screenHeight - relativePos.y() - WINDOWHEIGHT_PADDING

    def setDockedWidgetHeight(self, height):
        self.setFixedHeight(height)

    def show(self, **kwargs):
        super(ToolsetsUI, self).show(**kwargs)

    def resizeEndEvent(self):
        """ Save the height for us to use
        :return:
        """
        self.resizedHeight = self.rect().height()

    def updateMinimizeBar(self):
        """height = self.window().height()
        minHeight = self.window().minimumHeight()

        if not hasattr(self, "minimizeBar"):
            return

        if height > minHeight:
            self.minimizeBar.setArrowDown(False)
        else:
            self.minimizeBar.setArrowDown(True)"""
        pass

    def toggleToolset(self, toolsetId, activate=True, keepOpen=False):
        """ Toggle toolset

        :param toolsetId:
        :type toolsetId:
        :param activate:
        :type activate:
        :param keepOpen:
        :type keepOpen:
        :return:
        :rtype: toolsetwidgetitem.ToolsetWidgetItem
        """
        return self.toolsetFrame.toggleToolset(toolsetId, activate=activate, keepOpen=keepOpen)

    def openLastToolset(self):
        size = len(self.toolsetFrame.tree.lastHidden)
        if size > 0:
            last = self.toolsetFrame.tree.lastHidden.pop()
            self.toggleToolset(last)
            logger.info("Opening toolset '{}'".format(last))
        else:
            logger.info("openLastToolset(): No toolsets to left to open")

    def enterEvent(self, event):
        """ Mouse Enter Event

        :param event:
        :return:
        """
        self.setHighlight(True, updateUis=True)

    def closeEvent(self, ev):

        self.toolsetFrame.tree.closeEvent(ev)
        super(ToolsetsUI, self).closeEvent(ev)

        try:
            _TOOLSETUI_INSTANCES.remove(self)  # remove itself from the toolset ui instances
        except ValueError:
            pass

    def toolsetUis(self):
        """ Get all toolsetUi instances. Useful to use if can't import toolsetui.py

        :return:
        :rtype:
        """
        return toolsetUis()


class ToolsetTitleBar(FramelessTitleBar):
    
    def __init__(self, *args, **kwargs):

        super(ToolsetTitleBar, self).__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.logoInactive = preference.interface("core_interface").stylesheetSettingColour("$TOOLSET_LOGO_INACTIVE_COLOR")

    def setFramelessEnabled(self, action=None):
        """ Get the settings and transfer to new ZooToolset

        :param action:
        :return:
        """

        tree = self.frameless.toolsetFrame.tree  # type: toolsettree.ToolsetTreeWidget

        activeItems = tree.activeItems()
        lastHidden = self.frameless.lastHidden()
        lastTime = self.frameless.lastFocusedTime

        newTool = super(ToolsetTitleBar, self).setFramelessEnabled(action)  # type: ToolsetsUI

        newTool.window().setUpdatesEnabled(False)

        for item in activeItems:
            toolsetId = item[0].id()
            newItem = None
            if item[1] == toolsettree.ToolsetTreeWidget.ActiveItem_Active:
                newItem = newTool.toggleToolset(toolsetId)
            elif item[1] == toolsettree.ToolsetTreeWidget.ActiveItem_InActive:
                newItem = newTool.toggleToolset(toolsetId, activate=False)

            # Send the new properties
            if newItem:
                newItem.setPropertiesData(item[0].widgetData())

        newTool.window().setUpdatesEnabled(True)

        newTool.setLastHidden(lastHidden)
        newTool.lastFocusedTime = lastTime

    def dropEvent(self, event):
        """ On dropping toolset on title bar

        :param event:
        :type event:
        :return:
        :rtype:
        """
        ret = None
        source = event.source()  # type: toolsettree.ToolsetTreeWidget

        if self.frameless.toolsetFrame.tree is not source:
            mData = event.mimeData().data("dragData")
            data = cPickle.loads(str(mData))
            properties = toolsetwidgetitem.itemData[data['itemInfos'][0].data]
            toolsetId = properties['toolsetId']

            sourceItem = source.toolsetFrame.toggleToolset(toolsetId)

            targetItem = self.frameless.toolsetFrame.toggleToolset(toolsetId)
            targetItem.setPropertiesData(sourceItem.widgetData())

            ret = super(ToolsetTitleBar, self).dropEvent(event)
            QtCore.QTimer.singleShot(0, lambda x=source:self.dropFinish(x))

        if ret is None:
            super(ToolsetTitleBar, self).dropEvent(event)

        return ret

    def dropFinish(self, source):
        source.toolsetFrame.window().resizeWindow()
        source.toolsetFrame.updateColors()

    def dragEnterEvent(self, event):
        event.accept()

    def setLogoHighlight(self, highlight):
        """ Set the logo colour based on highlight

        :param highlight:
        :return:
        """
        if hasattr(self, "logoInactive") is False:
            return

        if highlight:
            super(ToolsetTitleBar, self).setLogoHighlight(None)
        else:
            super(ToolsetTitleBar, self).setLogoHighlight(self.logoInactive)


class MinimizeBar(extendedbutton.ExtendedButton):
    def __init__(self, parent=None):
        col = (128, 128, 128)  # Maybe should be placed somewhere else
        hoverCol = colour.offsetColor(col, 80)

        super(MinimizeBar, self).__init__(parent=parent)
        dpiScale = qtutils.dpiScale(16)
        self.arrowUp = iconlib.iconColorized("sortUp", color=col, size=dpiScale)
        self.arrowUpHover = iconlib.iconColorized("sortUp", color=hoverCol, size=dpiScale)
        self.arrowDown = iconlib.iconColorized("sortDown", color=col, size=dpiScale)
        self.arrowDownHover = iconlib.iconColorized("sortDown", color=hoverCol, size=dpiScale)

        self.setIcon(self.arrowUp)

        self.arrowUp.name = "up"
        self.arrowDown.name = "down"

        self.activeArrow = None
        self.setArrowDown()

    def setArrowDown(self, down=True):
        """
        Set the arrow down.
        :param down:
        :return:
        """

        # Switch icon if the icon is not set
        if down and (self.activeArrow is None or self.activeArrow.name != 'down'):
            self.activeArrow = self.arrowDown
            self.setIconIdle(self.arrowDown)
            self.setIconHover(self.arrowDownHover)
        else:
            self.activeArrow = self.arrowUp
            self.setIconIdle(self.arrowUp)
            self.setIconHover(self.arrowUpHover)


def toolsetUis():
    """ All toolset uis

    :return:
    :rtype: list[ToolsetsUI]
    """

    global _TOOLSETUI_INSTANCES
    return _TOOLSETUI_INSTANCES


def addToolsetUi(toolsetUi):
    _TOOLSETUI_INSTANCES.append(toolsetUi)


def toolsets(attr=""):
    """ All toolsets in toolset uis

    :return:
    :rtype: list[toolsetwidgetitem.ToolsetWidgetItem]
    """

    uis = toolsetUis()
    ret = []

    for toolsetUi in uis:
        if attr == "":
            ret += toolsetUi.toolsetFrame.tree.toolsets()
        else:
            tsets = toolsetUi.toolsetFrame.tree.toolsets()
            for t in tsets:
                if hasattr(t.widget, attr):
                    ret.append(t.widget)

    return ret


def getLastOpenedToolsetUi():

    uis = toolsetUis()

    # Get the last visible toolset
    tool = None
    for t in uis:
        if t.isVisible():
            tool = t

    return tool


def getLastFocusedToolsetUi(includeMinimized=True):
    """ Get last focused toolset ui

    :return:
    """
    tool = None
    max = 0

    uis = toolsetUis()
    for t in uis:

        if t.isVisible() and t.lastFocusedTime > max:
            if (not includeMinimized and not t.isMinimized()) or includeMinimized:
                tool = t
                max = t.lastFocusedTime

    return tool


def runToolset(toolsetId, logWarning=True):
    """ Runs a toolset tool, and loads it to the active toolset window

    Returns False if no toolset window is open

    :param toolsetId: the name of the toolSet by it's type (unique string)
    :type toolsetId: string
    :return taskCompleted: did the tool load?
    :rtype taskCompleted: bool
    """
    tool = getLastFocusedToolsetUi(includeMinimized=False)
    if tool is not None:
        tool.toggleToolset(toolsetId)
        return True
    else:
        if logWarning:
            logger.warning("Toolset Not found")
        return False


def runLastClosedToolset():
    tool = getLastFocusedToolsetUi()  # type: ToolsetsUI
    if tool is not None:
        tool.openLastToolset()
    else:
        logger.warning("Toolset Not found")


