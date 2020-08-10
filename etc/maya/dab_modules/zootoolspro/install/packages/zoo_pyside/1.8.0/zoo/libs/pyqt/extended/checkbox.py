from functools import partial

from Qt import QtWidgets, QtCore
from zoo.libs.pyqt.extended.menu import MenuCreateClickMethods
from zoovendor.six import iteritems


class CheckBox(QtWidgets.QCheckBox, MenuCreateClickMethods):
    leftClicked = QtCore.Signal()
    middleClicked = QtCore.Signal()
    rightClicked = QtCore.Signal()

    def __init__(self, label, checked=False, parent=None,  toolTip="", enableMenu=True, menuVOffset=20):
        """This class adds the capacity for a middle/right click menu to be added to the QCheckBox

        Note: This class disables the regular left click button states of a checkbox so has to handle them manual
        Inherits from QtWidgets.QCheckBox and MenuCreateClickMethods

        Menus are not added by default they must be set in the ui code. QMenu's can be passed in via setMenu():

            zooQtWidget.setMenu(myQMenu, mouseButton=QtCore.Qt.RightButton)

        If using zoocore_pro's ExtendedMenu() you can pass that in instead of a QMenu for extra functionality

        See the class docs for MenuCreateClickMethods() for more information

        :param parent: the parent widget
        :type parent: QWidget
        :param menuVOffset:  The vertical offset (down) menu drawn from widget top corner.  DPI is handled
        :type menuVOffset: int
        """
        super(CheckBox, self).__init__(label, parent=parent)

        if toolTip != "":
            self.setToolTip(toolTip)

        self.setChecked(checked)

        if enableMenu:
            self.setupMenuClass(menuVOffset=menuVOffset)

            self.leftClicked.connect(partial(self.contextMenu, QtCore.Qt.LeftButton))
            self.middleClicked.connect(partial(self.contextMenu, QtCore.Qt.MidButton))
            self.rightClicked.connect(partial(self.contextMenu, QtCore.Qt.RightButton))
            # TODO: the setDown should turn off as soon as the mouse moves off the widget, like a hover state, looks tricky

    def mousePressEvent(self, event):
        """ mouseClick emit

        Checks to see if a menu exists on the current clicked mouse button, if not, use the original Qt behaviour

        :param event: the mouse pressed event from the QLineEdit
        :type event: QEvent
        """
        for mouseButton, menu in iteritems(self.clickMenu):
            if menu and event.button() == mouseButton:  # if a menu exists and that mouse has been pressed
                if mouseButton == QtCore.Qt.LeftButton:
                    return self.leftClicked.emit()
                if mouseButton == QtCore.Qt.MidButton:
                    return self.middleClicked.emit()
                if mouseButton == QtCore.Qt.RightButton:
                    return self.rightClicked.emit()
        super(CheckBox, self).mousePressEvent(event)

    def setCheckedQuiet(self, value):
        """Sets the checkbox in quiet box without emitting a signal

        :param value: True if checked, False if not checked
        :type value: bool
        """
        self.blockSignals(True)
        self.setChecked(value)
        self.blockSignals(False)