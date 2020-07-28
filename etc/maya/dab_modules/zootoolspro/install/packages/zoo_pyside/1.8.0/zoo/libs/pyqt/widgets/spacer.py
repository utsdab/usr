from Qt import QtWidgets
from zoo.libs.pyqt import utils


class Divider(QtWidgets.QLabel):
    def __init__(self, labelName="", parent=None):
        """ A nice horizontal line divider, shadowed 2px looks nice on most bgs """
        super(Divider, self).__init__(labelName, parent=parent)
        # TODO Stylesheet!!
        self.setStyleSheet("QLabel {background-color: #3e3e3e; padding: 0; margin: 0; border-bottom: "
                           "1 solid #666; border-top: 1 solid #2a2a2a;}")
        self.setMaximumHeight(2)


class QHLine(QtWidgets.QFrame):
    def __init__(self, parent=None):
        """ A nice horizontal line to space ui
        TODO: 3 pixels high can't seem to adjust, try divider() see above"""
        super(QHLine, self).__init__(parent=parent)
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)


class QVLine(QtWidgets.QFrame):
    def __init__(self, parent=None):
        """ A nice vertical line to space ui """
        super(QVLine, self).__init__(parent=parent)
        self.setFrameShape(QtWidgets.QFrame.VLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)


def Spacer(width, height, hMin=QtWidgets.QSizePolicy.Minimum, vMin=QtWidgets.QSizePolicy.Minimum):
    """creates an expanding spacer (empty area) with easy options.  DPI auto handled

    Size Policies are
    https://srinikom.github.io/pyside-docs/PySide/QtGui/QSizePolicy.html#PySide.QtGui.PySide.QtGui.QSizePolicy.Policy
        QtWidgets.QSizePolicy.Fixed -  never grows or shrinks
        QtWidgets.QSizePolicy.Minimum - no advantage being larger
        QtWidgets.QSizePolicy.Maximum - no advantage being smaller
        QtWidgets.QSizePolicy.Preferred - The sizeHint() is best, but the widget can be shrunk/expanded
        QtWidgets.QSizePolicy.Expanding -  but the widget can be shrunk or make use of extra space
        QtWidgets.QSizePolicy.MinimumExpanding - The sizeHint() is minimal, and sufficient
        QtWidgets.QSizePolicy.Ignored - The sizeHint() is ignored. Will get as much space as possible

    :param width: width of the spacer in pixels, DPI is auto handled
    :type width: int
    :param height: height of the spacer in pixels, DPI is auto handled
    :type height: int
    :param hMin: height of the spacer in pixels, DPI is auto handled
    :type hMin: PySide.QtGui.QSizePolicy.Policy
    :param vMin: vertical minimum
    :type vMin: PySide.QtGui.QSizePolicy.Policy
    :return spacerItem: item returned, ie the spacerItem
    :rtype spacerItem: object
    """
    return QtWidgets.QSpacerItem(utils.dpiScale(width), utils.dpiScale(height), hMin, vMin)
