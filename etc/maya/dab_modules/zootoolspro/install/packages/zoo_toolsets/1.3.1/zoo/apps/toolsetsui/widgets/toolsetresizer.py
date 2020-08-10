from Qt import QtWidgets, QtCore, QtGui
from zoo.libs.pyqt import utils


class ToolsetResizer(QtWidgets.QFrame):
    def __init__(self, parent=None, toolsetWidget=None, target=None, fixedHeight=11):
        """ Resizes a target widget when clicked and dragged.

        This modifies the FixedSize of the target widget.

        :param parent:
        :type parent:
        :param toolsetWidget:
        :type toolsetWidget: toolsetwidgetmaya.ToolsetWidgetMaya
        :param target:
        :type target:
        """
        super(ToolsetResizer, self).__init__(parent=parent)

        self._prevMouse = None
        self._sizeStart = None
        self._orientation = QtCore.Qt.Vertical

        mainLayout = QtWidgets.QHBoxLayout()
        self.setLayout(mainLayout)

        self.decorationWidget = ToolsetResizerHandle(parent=self)
        mainLayout.addWidget(self.decorationWidget)
        self.decorationWidget.setSizePolicy(
            QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum))


        self.target = target
        self.toolsetWidget = toolsetWidget
        self.setFixedHeight(utils.dpiScale(fixedHeight))
        self.toolsetFrame = self.toolsetWidget.treeWidget.toolsetFrame

    def enterEvent(self, event):
        """ Change the mouse to vertical resizer

        :param event:
        :type event:
        :return:
        :rtype:
        """
        if self.orientation() == QtCore.Qt.Vertical:
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.SizeVerCursor)
        else:
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.SizeHorCursor)

    def setFixedHeight(self, h):
        """ Set fixed height

        :param h:
        :type h:
        :return:
        :rtype:
        """
        self.decorationWidget.setFixedHeight(max(0, h-utils.dpiScale(10)))

    def orientation(self):
        """ Orientation and direction to resize

        :return:
        :rtype:
        """
        return self._orientation

    def setOrientation(self, orientation=QtCore.Qt.Vertical or QtCore.Qt.Horizontal):
        """ Set new orientation

        :param orientation:
        :type orientation:
        :return:
        :rtype:
        """
        self._orientation = orientation

    def leaveEvent(self, event):
        """ Change the mouse back

        :param event:
        :type event:
        :return:
        :rtype:
        """
        # we do this three because sometimes it doesnt revert after only 1
        for i in range(3):
            QtWidgets.QApplication.restoreOverrideCursor()

    def mouseMoveEvent(self, event):
        """ Resizes the target

        :param event:
        :type event:
        :return:
        :rtype:
        """
        pos = self.parent().mapFromGlobal(QtGui.QCursor.pos()).y()

        if self._prevMouse is None:
            self._prevMouse = pos
            self._sizeStart = self.target.size()

        size = self._sizeStart
        size.setHeight(size.height() - (self._prevMouse-pos))

        if self.orientation() == QtCore.Qt.Vertical:
            self.target.setFixedHeight(size.height())
        else:
            self.target.setFixedWidth(size.width())

        tree = self.toolsetWidget.treeWidget
        tree.updateTreeWidget()

        self._prevMouse = pos

    def mouseReleaseEvent(self, event):
        """ Mouse Release Event

        :param event:
        :type event:
        :return:
        :rtype:
        """
        self._prevMouse = None
        self._sizeStart = None


class ToolsetResizerHandle(QtWidgets.QFrame):
    """ CSS Purposes """


class ToolsetSplitterHandle(QtWidgets.QSplitterHandle):
    """ Override the splitter handle so we can have our own events
    """
    handleMoved = QtCore.Signal(object)
    handleReleased = QtCore.Signal(object)

    def mouseMoveEvent(self, event):
        self.handleMoved.emit(event.pos())
        super(ToolsetSplitterHandle, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.handleReleased.emit(event.pos())
        super(ToolsetSplitterHandle, self).mouseReleaseEvent(event)


class ToolsetSplitter(QtWidgets.QSplitter):
    def __init__(self, parent=None, toolsetWidget=None, target=None):
        """ Splitter version of the resizer

        :param parent:
        :type parent:
        :param toolsetWidget:
        :type toolsetWidget:
        :param target:
        :type target:
        """
        super(ToolsetSplitter, self).__init__(parent=parent)
        self._prevMouse = None
        self._prevSizes = None
        self._sizeStart = None

        self.resizeTarget = target
        self.toolsetWidget = toolsetWidget
        self.setOrientation(QtCore.Qt.Vertical)

    def addWidget(self, widget):
        """ Add Widget
        Connect some signals

        :param widget:
        :type widget:
        :return:
        :rtype:
        """

        super(ToolsetSplitter, self).addWidget(widget)
        handle = self.handle(1)
        if handle is not None:
            handle.handleMoved.connect(self.handleMoved)
            handle.handleReleased.connect(self.handleReleased)

    def handle(self, index):
        """

        :param index:
        :type index:
        :return:
        :rtype: ToolsetSplitterHandle
        """
        return super(ToolsetSplitter, self).handle(index)

    def handleMoved(self, pos):
        pos = self.mapFromGlobal(QtGui.QCursor.pos()).y()

        if self._prevMouse is None:
            self._prevMouse = pos
            self._prevSizes = self.sizes()
            self._sizeStart = self.size()

        size = self._sizeStart
        size.setHeight(size.height() - (self._prevMouse-pos))

        self.setFixedSize(size)

        self.setSizes(self._prevSizes)
        toolsetFrame = self.toolsetWidget.treeWidget.toolsetFrame
        toolsetFrame.tree.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.toolsetWidget.treeWidget.updateTreeWidget()
        toolsetFrame.window().resizeWindow()


        self._prevMouse = pos
        self._prevSizes = self.sizes()

    def handleReleased(self, pos):
        self._prevMouse = None
        self._prevSizes = None
        self._sizeStart = None

    def createHandle(self):
        """ Use our own handle

        :return:
        :rtype:
        """
        return ToolsetSplitterHandle(self.orientation(), self)
