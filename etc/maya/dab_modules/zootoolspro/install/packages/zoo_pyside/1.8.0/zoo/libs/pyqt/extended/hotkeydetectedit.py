from Qt import QtCore, QtGui, QtWidgets
from zoo.libs import iconlib
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets.searchwidget import SearchLineEdit


class HotkeyDetectEdit(SearchLineEdit):
    hotkeyEdited = QtCore.Signal()

    def __init__(self, text="", parent=None, prefix="", suffix="", iconsEnabled=False, searchIcon="key"):
        """ A line Edit which detects key combinations are being pressed(for hotkeys for instance).

        Usage: It works similarly to a QLineEdit. Type in a hotkey combination to show the hotkey.

        Example::

            # eg Type in Ctrl+Alt+P and it would set the text of the QLineEdit to "Ctrl+Alt+P"
            wgt = HotkeyDetectEdit()

        :param text:
        :param parent:
        :param prefix:
        :param suffix:
        """

        super(HotkeyDetectEdit, self).__init__(parent=parent,
                                               searchPixmap=iconlib.iconColorized(searchIcon, utils.dpiScale(16),
                                                                                  (128, 128, 128)),
                                               iconsEnabled=iconsEnabled)

        self.prefix = prefix
        self.suffix = suffix

        self.setText(text)
        self.backspaceClears = True

        # str.maketrans('~!@#$%^&*()_+{}|:"<>?', '`1234567890-=[]\\;\',./')
        self.specialkeys = {64: 50, 33: 49, 34: 39, 35: 51, 36: 52, 37: 53, 38: 55, 40: 57, 41: 48, 42: 56, 43: 61,
                            63: 47, 60: 44, 126: 96, 62: 46, 58: 59, 123: 91, 124: 92, 125: 93, 94: 54, 95: 45}

    def setText(self, text, resetCursor=True):
        """ Set text of HotKeyEdit

        :param text:
        :param resetCursor:
        :return:
        """
        text = self.prefix + text + self.suffix

        super(HotkeyDetectEdit, self).setText(text)

        if resetCursor:
            self.setCursorPosition(0)

    def keyPressEvent(self, e):
        """ Update the text edit to whatever the hotkey is inputted

        For example type in Ctrl+Alt+P and it would set the text of the QLineEdit to "Ctrl+Alt+P"

        :param e:
        :return:
        """
        keyStr = QtGui.QKeySequence(self.convertSpecChars(e.key())).toString()

        # Return out if its only a modifier
        if str(e.text()) == "":
            return

        self.text()
        modifiers = QtWidgets.QApplication.keyboardModifiers()

        # Feels like theres a better way to do this..
        if modifiers == QtCore.Qt.ShiftModifier:
            hotkey = 'Shift+' + keyStr
        elif modifiers == QtCore.Qt.ControlModifier:
            hotkey = 'Ctrl+' + keyStr
        elif modifiers == QtCore.Qt.AltModifier:
            hotkey = 'Alt+' + keyStr
        elif modifiers == (QtCore.Qt.AltModifier | QtCore.Qt.ControlModifier):
            hotkey = 'Ctrl+Alt+' + keyStr
        elif modifiers == (QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier):
            hotkey = 'Ctrl+Shift+' + keyStr
        elif modifiers == (QtCore.Qt.AltModifier | QtCore.Qt.ShiftModifier):
            hotkey = 'Shift+Alt+' + keyStr
        elif modifiers == (QtCore.Qt.AltModifier | QtCore.Qt.ControlModifier |
                               QtCore.Qt.ShiftModifier):
            hotkey = 'Ctrl+Alt+Shift+' + keyStr
        elif modifiers == (QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier):
            hotkey = 'Ctrl+' + keyStr
        else:
            hotkey = keyStr

        if ((hotkey == "Backspace" or hotkey == "Del") and self.backspaceClears) or hotkey == "Esc":
            hotkey = ""

        self.setText(hotkey)

        self.hotkeyEdited.emit()

    def convertSpecChars(self, charInt):
        """ Converts special characters back to the original keyboard number

        :param charInt:
        :return:
        """
        if charInt in self.specialkeys:
            return self.specialkeys[charInt]
        return charInt