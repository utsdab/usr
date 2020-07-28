import os

from Qt import QtWidgets, QtCore, QtGui
from zoo.libs.pyqt import utils, uiconstants
from zoo.libs.pyqt.extended.lineedit import LineEdit
from zoo.libs.pyqt.widgets.buttons import styledButton
from zoo.libs.pyqt.widgets.framelessmaya import FramelessWindowMaya
import maya.api.OpenMaya as om2
from zoo.libs.pyqt.widgets.label import Label
from zoo.libs.pyqt.widgets.layouts import vBoxLayout, hBoxLayout


class BasicFrameless(FramelessWindowMaya):
    saved = QtCore.Signal(object)

    def __init__(self, parent=None, path=None, onSave=None, imageType="png", framelessChecked=False):
        """ Snapshot ui

        :param parent:
        :type parent:
        :param path:
        :type path:
        :param onSave:
        :type onSave:
        """
        self.imageSizeLabel = None  # type: Label
        self.bottomBar = None  # type: SnapshotFrame
        super(BasicFrameless, self).__init__(parent=parent, title="Snapshot Ui", width=300, height=300, framelessChecked=framelessChecked)
        self._savePath = path
        self.lastSavedLocation = None
        self.snapshotPx = None  # type: QtGui.QPixmap
        self.mainLayout = None  # type: vBoxLayout
        self.snapLayout = None  # type: hBoxLayout
        self.snapWidget = None  # type: QtWidgets.QWidget
        self.widthEdit = None  # type: LineEdit
        self.heightEdit = None  # type: LineEdit
        self.keepAspect = True
        self.snapshotBtn = None  # type: ExtendedButton
        self.aspectLinkBtn = None  # type: ExtendedButton
        self.lockedBtn = None  # type: ExtendedButton
        self.cancelBtn = None  # type: ExtendedButton
        self.imageType = imageType

        self.window().setWindowFlags(self.window().windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        self.setFrameless(False)



class BasicFrameless2(FramelessWindowMaya):
    saved = QtCore.Signal(object)

    def __init__(self, parent=None):
        """ Snapshot ui

        :param parent:
        :type parent:
        :param path:
        :type path:
        :param onSave:
        :type onSave:
        """
        self.imageSizeLabel = None  # type: Label
        self.bottomBar = None  # type: SnapshotFrame
        super(BasicFrameless2, self).__init__(parent=parent, title="Snapshot Ui", width=300, height=300, framelessChecked=False)
        self.window().setWindowFlags(self.window().windowFlags() | QtCore.Qt.WindowStaysOnTopHint)



class SnapshotFrame(QtWidgets.QFrame):
    """ For CSS Purposes"""
    pass
