from Qt import QtWidgets, QtCore
from zoo.libs.pyqt import uiconstants as uic, utils


class GridLayout(QtWidgets.QGridLayout):
    def __init__(self, parent=None, margins=(0, 0, 0, 0), spacing=uic.SREG, columnMinWidth=None, columnMinWidthB=None,
                 vSpacing=None, hSpacing=None):
        """ Grid Layout

        DPI (4k) is handled here
        Defaults use regular spacing and no margins

        :param margins:  override the margins with this value
        :type margins: tuple
        :param spacing: override the spacing with this pixel value
        :type spacing: int
        :param columnMinWidth: option for one column number then it's min width
        :type columnMinWidth: tuple
        :param columnMinWidthB: option for one column number then it's min width, use obj.setColumnMinimumWidth for more
        :type columnMinWidthB: tuple
        """

        super(GridLayout, self).__init__(parent)

        self.setContentsMargins(*utils.marginsDpiScale(*margins))
        if not vSpacing and not hSpacing:
            self.setHorizontalSpacing(utils.dpiScale(spacing))
            self.setVerticalSpacing(utils.dpiScale(spacing))
        elif vSpacing and not hSpacing:
            self.setHorizontalSpacing(utils.dpiScale(hSpacing))
            self.setVerticalSpacing(utils.dpiScale(vSpacing))
        elif hSpacing and not vSpacing:
            self.setHorizontalSpacing(utils.dpiScale(hSpacing))
            self.setVerticalSpacing(utils.dpiScale(spacing))
        else:
            self.setHorizontalSpacing(utils.dpiScale(hSpacing))
            self.setVerticalSpacing(utils.dpiScale(vSpacing))
        if columnMinWidth:  # column number then the width in pixels
            self.setColumnMinimumWidth(columnMinWidth[0], utils.dpiScale(columnMinWidth[1]))
        if columnMinWidthB:  # column number then the width in pixels
            self.setColumnMinimumWidth(columnMinWidthB[0], utils.dpiScale(columnMinWidthB[1]))


def hBoxLayout(parent=None, margins=(0, 0, 0, 0), spacing=uic.SREG):
    """One liner for QtWidgets.QHBoxLayout() to make it easier to create an easy Horizontal Box layout
    DPI (4k) is handled here
    Defaults use regular spacing and no margins

    :param margins: override the margins with this value (left, top, right, bottom)
    :type margins: tuple
    :param spacing: override the spacing with this pixel value
    :type spacing: int
    """
    zooQHBoxLayout = QtWidgets.QHBoxLayout(parent)
    zooQHBoxLayout.setContentsMargins(*utils.marginsDpiScale(*margins))
    zooQHBoxLayout.setSpacing(utils.dpiScale(spacing))
    return zooQHBoxLayout


def vBoxLayout(parent=None, margins=(0, 0, 0, 0), spacing=uic.SREG):
    """One liner for QtWidgets.QVBoxLayout() to make it easier to create an easy Vertical Box layout
    DPI (4k) is handled here
    Defaults use regular spacing and no margins

    :param margins:  override the margins with this value (left, top, right, bottom)
    :type margins: tuple
    :param spacing: override the spacing with this pixel value
    :type spacing: int
    """
    zooQVBoxLayout = QtWidgets.QVBoxLayout(parent)
    zooQVBoxLayout.setContentsMargins(*utils.marginsDpiScale(*margins))
    zooQVBoxLayout.setSpacing(utils.dpiScale(spacing))
    return zooQVBoxLayout


def vGraphicsLinearLayout(parent=None,
                          margins=(0, 0, 0, 0), spacing=0,
                          orientation=QtCore.Qt.Vertical):
    layout = QtWidgets.QGraphicsLinearLayout(parent=parent)
    layout.setSpacing(spacing)
    layout.setContentsMargins(*margins)
    layout.setOrientation(orientation)
    return layout


def hGraphicsLinearLayout(parent=None,
                          margins=(0, 0, 0, 0), spacing=0,
                          orientation=QtCore.Qt.Horizontal):
    layout = QtWidgets.QGraphicsLinearLayout(parent=parent)
    layout.setSpacing(spacing)
    layout.setContentsMargins(*margins)
    layout.setOrientation(orientation)
    return layout


def formLayout(parent=None,
               margins=(0, 0, 0, 0),
               spacing=uic.SREG):
    layout = QtWidgets.QFormLayout(parent=parent)
    layout.setSpacing(spacing)
    layout.setContentsMargins(*margins)
    return layout
