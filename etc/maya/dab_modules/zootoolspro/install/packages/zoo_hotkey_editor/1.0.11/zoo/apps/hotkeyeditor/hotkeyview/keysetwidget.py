from Qt import QtCore, QtWidgets

from zoo.apps.hotkeyeditor.core import keysets
from zoo.apps.hotkeyeditor.core import utils
from zoo.libs.utils import zlogging
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from maya.api import OpenMaya as om2

logger = zlogging.getLogger(__name__)


class KeySetWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(KeySetWidget, self).__init__(parent)

        self.hotkeyView = self.parent()
        self.keySetManager = self.hotkeyView.keySetManager

        self.newSetBtn = elements.styledButton(icon="plus", parent=self, toolTip="Create new hotkey set",
                                               style=uic.BTN_TRANSPARENT_BG)
        self.deleteSetBtn = DeleteSetButton(parent=self)
        self.helpBtn = elements.styledButton(icon="help", parent=self, toolTip="Hotkey help",
                                             style=uic.BTN_TRANSPARENT_BG)
        self.keySetCombo = elements.ComboBoxRegular.setupComboBox(items=(self.keySetManager.getKeySetNames()),
                                                                  parent=self,
                                                                  toolTip="Choose a hotkey set")

        self.initUi()
        self.connections()

        self.setUpKeySet()

        # Disable the delete button if the keyset is locked
        current = self.keySetCombo.currentText()
        if self.keySetManager.isKeySetLocked(current):
            self.deleteSetBtn.setEnabled(False)

    def initUi(self):
        keySetLayout = elements.hBoxLayout(self, margins=(0, 2, 0, 2), spacing=uic.SSML)

        keySetLayout.addWidget(self.keySetCombo)
        keySetLayout.addItem(elements.Spacer(5, 0))
        keySetLayout.addWidget(self.newSetBtn)
        keySetLayout.addWidget(self.deleteSetBtn)
        keySetLayout.addWidget(self.helpBtn)
        keySetLayout.addStretch(1)

        self.setLayout(keySetLayout)

    def connections(self):
        self.newSetBtn.leftClicked.connect(self.newKeySet)
        # self.applySetBtn.clicked.connect(self.applySetClicked)
        self.keySetCombo.activated.connect(self.keySetComboSwitch)

        self.deleteSetBtn.leftClicked.connect(self.deleteKeySet)
        self.helpBtn.leftClicked.connect(self.helpBtnClicked)

    def keySetComboSwitch(self):
        switchSet = self.keySetCombo.currentText()
        self.keySetUiSwitch(switchSet)
        self.applySet(switchSet)

    def keySetUiSwitch(self, name):
        current = self.keySetManager.setActive(name)
        mod = current.modified
        logger.info("Switching to \"{}\"".format(current.keySetName))
        self.hotkeyView.setKeySet(current)
        self.setComboToText(self.keySetCombo, name)

        # Don't allow the user to delete things in ui
        current = self.keySetCombo.currentText()
        if self.keySetManager.isKeySetLocked(current):
            self.deleteSetBtn.setEnabled(False)
        else:
            self.deleteSetBtn.setEnabled(True)

        # For admin mode allow a few things
        if not self.keySetManager.isKeySetLocked(current) or utils.isAdminMode():
            self.hotkeyView.setHotkeyUiEnabled(True)
        elif self.keySetManager.isKeySetLocked(current):
            self.hotkeyView.setHotkeyUiEnabled(False)

        # Make sure the revert button is enabled properly
        self.hotkeyView.updateRevertUi()

    def helpBtnClicked(self):
        import webbrowser
        webbrowser.open("http://create3dcharacters.com/maya-zoo-tools-pro-install/")

    def applySet(self, setName):
        # Maybe should move this to hotkeyView
        self.keySetManager.setActive(setName, install=True)
        # self.hotkeyView.setActiveLabel(setName)

    def setUpKeySet(self, forceMaya=False):
        current = self.keySetManager.currentKeySet(forceMaya=forceMaya)
        if current is not None:
            self.hotkeyView.setKeySetUi(current)
            self.setComboToText(self.keySetCombo, current.prettyName)

    def setComboToText(self, combo, text):
        """ Sets the index based on the text

        :param text: Text to search and switch item to.
        :return:
        """
        index = combo.findText(text, QtCore.Qt.MatchFixedString)
        if index >= 0:
            combo.setCurrentIndex(index)

    def newKeySet(self):
        # Note parenting to None to inherit from Maya and fix stylesheet issues
        newSet, ret = QtWidgets.QInputDialog.getText(
            None,
            'Enter Set Name',
            'Please enter a name for the new hotkey set',
            text="")

        if ret:
            # Check to see if it exists first.
            if newSet == "":
                logger.warning("Name can't be empty! Cancelling operation.")

            if self.keySetManager.newKeySet(newSet) is False:
                logger.warning("{} already exists! Cancelling operation.".format(newSet))
                return

            self.updateKeySets(newSet)

    def deleteKeySet(self):
        """ Delete key set

        :return:
        :rtype:
        """

        if self.deleteSetBtn.enabled:

            current = self.keySetCombo.currentText()

            # Note parenting to None to inherit from Maya and fix stylesheet issues
            ret = QtWidgets.QMessageBox.warning(
                None,
                'Are You Sure?',
                'Are you sure you want to delete Key Set: \n\n{}'.format(current),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)

            if ret == QtWidgets.QMessageBox.Yes:
                logger.info("Yes was clicked")

                self.keySetManager.deleteKeySet(current)
                self.updateKeySets(keysets.KeySetManager.defaultKeySetName)
                self.hotkeyView.keySetCleanUp()
                self.keySetComboSwitch()

            elif ret == QtWidgets.QMessageBox.Cancel:
                logger.info("cancel was clicked")
        else:
            om2.MGlobal.displayWarning(
                "Default Hotkey sets are locked cannot be deleted here. You may delete them in Zoo Preferences.")

    def updateKeySets(self, setToName=""):
        """ Update the keysets. Usually run when there's been a change to the keysets
        :param setToName: Set the combo box to the name

        """
        self.keySetCombo.clear()
        self.keySetCombo.addItems(self.keySetManager.getKeySetNames())

        if setToName != "":
            index = self.keySetCombo.findText(setToName, QtCore.Qt.MatchFixedString)
            self.keySetCombo.setCurrentIndex(index)
            self.keySetComboSwitch()
            self.hotkeyView.sourceCombo.updateSources()


class DeleteSetButton(elements.ExtendedButton):
    icon = "trash"

    def __init__(self, parent=None):
        """ Override set enabled so we can print something when it is clicked

        :param parent:
        :type parent:
        """
        self.enabled = True

        super(DeleteSetButton, self).__init__(parent=parent)

        self.setIconByName(self.icon)
        self.setToolTip("Delete the current hotkey set")

    def setEnabled(self, enabled):
        if enabled:
            self.setIconColor((255, 255, 255))
        else:
            self.setIconColor((128, 128, 128))

        self.enabled = enabled
