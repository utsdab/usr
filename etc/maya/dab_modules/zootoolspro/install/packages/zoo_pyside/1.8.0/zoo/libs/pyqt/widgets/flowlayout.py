"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
FlowLayout
Custom layout that mimics the behaviour of a flow layout (not supported in PyQt by default)
@source https://qt.gitorious.org/pyside/pyside-examples/source/060dca8e4b82f301dfb33a7182767eaf8ad3d024:examples/layouts/flowlayout.py
Comments added by Jos Balcaen(http://josbalcaen.com/)
@date 1/1/2015

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
from Qt import QtWidgets, QtCore
import shiboken2

from zoo.libs.pyqt import utils


class FlowLayout(QtWidgets.QLayout):
    """Custom layout that mimics the behaviour of a flow layout"""

    def __init__(self, parent=None, margin=0, spacingX=2, spacingY=2):
        """ Create a new FlowLayout instance.

        This layout will reorder the items automatically.

        :param parent (QWidget)
        :param margin (int)
        :param spacing (int)
        """
        super(FlowLayout, self).__init__(parent)
        # Set margin and spacing
        if parent is not None:
            self.setMargin(margin)

        self.spacingX = 0
        self.spacingY = 0
        self._orientation = QtCore.Qt.Horizontal
        self.setSpacing(spacingX)
        self.setSpacingX(spacingX)
        self.setSpacingY(spacingY)
        self.itemList = []
        self.overflow = None

        self.sizeHintLayout = self.minimumSize()

    def __del__(self):
        """Delete all the items in this layout"""
        self.clear()

    def orientation(self):
        return self._orientation

    def setOrientation(self, orientation):
        """ Set out how the widgets will be laid out. Horizontally or vertically

        :param orientation: Orientation of the widgets
        :type orientation: QtCore.Qt.Horizontal or QtCore.Qt.Horizontal
        :return:
        """
        self._orientation = orientation

    def clear(self):
        """
        Clear all widgets
        :return:
        """
        item = self.takeAt(0)
        while item:
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

            item = self.takeAt(0)

    def addItem(self, item):
        """Add an item at the end of the layout.
        This is automatically called when you do addWidget()

        :param item:
        :type item: QWidgetItem
        """
        self.itemList.append(item)

    def addSpacing(self, spacing):
        spaceWgt = QtWidgets.QWidget()
        spaceWgt.setFixedSize(QtCore.QSize(spacing, spacing))
        self.addWidget(spaceWgt)

    def count(self):
        """Get the number of items in the this layout

        :return (int)"""
        return len(self.itemList)

    def itemAt(self, index):
        """Get the item at the given index

        :param index (int)
        :return (QWidgetItem)"""
        if 0 <= index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        """Remove an item at the given index

        :param index (int)
        :return (None)"""
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def insertWidget(self, index, widget):
        """Insert a widget at a given index

        :param index (int)
        :param widget (QWidget)"""
        item = QtWidgets.QWidgetItem(widget)
        self.itemList.insert(index, item)

    def items(self):
        remove = []
        for item in self.itemList:
            if not shiboken2.isValid(item):
                remove.append(item)

        [self.itemList.remove(r) for r in remove]
        return self.itemList

    def expandingDirections(self):
        """ This layout grows only in the horizontal dimension or vertical direction
        depending on current orientation """

        return QtCore.Qt.Orientations(self.orientation())

    def hasHeightForWidth(self):
        """If this layout's preferred height depends on its width

        :return (boolean) Always True """

        return self.orientation() == QtCore.Qt.Horizontal

    def heightForWidth(self, width):
        """Get the preferred height a layout item with the given width

        :param width (int)"""

        height = self.doLayout(QtCore.QRect(0, 0, width, 0), True)

        self.sizeHintLayout = QtCore.QSize(width, height)

        return height

    def setGeometry(self, rect):
        """Set the geometry of this layout

        :param rect (QRect)"""
        super(FlowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)

    def allowOverflow(self, allow):
        """ Allows the flow layouts to overflow, rather than go onto the next line

        :param allow: True to allow, False to not allow
        :type allow: bool
        :return:
        """
        self.overflow = allow

    def sizeHint(self):
        """ Get the preferred size of this layout

        :return (QSize) The minimum size"""
        return self.sizeHintLayout

    def minimumSize(self):
        """ Get the minimum size of this layout

        :return (QSize)"""
        # Calculate the size
        size = QtCore.QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
        # Add the margins
        size += QtCore.QSize(2, 2)
        return size

    def setSpacingX(self, spacing):
        """X Spacing for each item

        :param spacing:
        :return:
        """
        self.spacingX = utils.dpiScale(spacing)

    def setSpacingY(self, spacing):
        """ Y Spacing for each item

        :param spacing:
        :return:
        """
        self.spacingY = utils.dpiScale(spacing)

    def doLayout(self, rect, testOnly):
        """ Layout all the items

        :param rect (QRect) Rect where in the items have to be laid out
        :param testOnly (boolean) Do the actual layout"""

        x = rect.x()
        y = rect.y()
        lineSize = 0
        orientation = self.orientation()

        for item in self.itemList:

            if item.widget().isHidden():
                continue

            spaceX = self.spacingX
            spaceY = self.spacingY

            if orientation == QtCore.Qt.Horizontal:
                nextX = x + item.sizeHint().width() + spaceX
                if nextX - spaceX > rect.right() and lineSize > 0:
                    if not self.overflow:
                        x = rect.x()
                        y = y + lineSize + (spaceY * 2)
                        nextX = x + item.sizeHint().width() + spaceX
                        lineSize = 0

                if not testOnly:
                    item.setGeometry(
                            QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))
                x = nextX
                lineSize = max(lineSize, item.sizeHint().height())
            else:
                nextY = y + item.sizeHint().height() + spaceY
                if nextY - spaceY > rect.bottom() and lineSize > 0:
                    if not self.overflow:
                        y = rect.y()
                        x = x + lineSize + (spaceX * 2)
                        nextY = y + item.sizeHint().height() + spaceY
                        lineSize = 0

                if not testOnly:
                    item.setGeometry(
                        QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))
                x = nextY
                lineSize = max(lineSize, item.sizeHint().height())

        if orientation == QtCore.Qt.Horizontal:
            return y + lineSize - rect.y()
        else:
            return x + lineSize - rect.x()
