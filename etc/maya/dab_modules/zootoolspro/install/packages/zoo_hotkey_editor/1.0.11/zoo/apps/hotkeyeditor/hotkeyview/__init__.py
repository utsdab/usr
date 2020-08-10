from Qt import QtWidgets, QtCore

from maya import cmds
from zoo.apps.hotkeyeditor.core import const as c, const
from zoo.apps.hotkeyeditor.core import keysets, utils as hotkeyutils
from zoo.apps.hotkeyeditor.hotkeyview import propertieswidget, hotkeytable, keysetwidget
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import zlogging
from zoo.libs.pyqt import uiconstants as uic

logger = zlogging.getLogger(__name__)


class HotkeyView(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(HotkeyView, self).__init__(parent)

        self.deleteKeySetMsgBox = QtWidgets.QMessageBox()
        self.hotkeyTableWgt = None  # type: QtWidgets.QWidget
        self.hotkeyManagerUi = parent  # type: hotkeyeditorui.HotkeyEditorUI
        self.keySetManager = keysets.KeySetManager()

        self.saveCloseBtn = elements.styledButton(text="Save", icon="save", parent=self, textCaps=True,
                                                  style=uic.BTN_DEFAULT, toolTip="Save All Current Hotkey Settings")
        self.applyBtn = elements.styledButton(text="Apply", icon="checkMark", parent=self, textCaps=True,
                                              style=uic.BTN_DEFAULT, toolTip="Save All Current Hotkey Settings")
        self.cancelBtn = elements.styledButton(text="Cancel", icon="xCircleMark", parent=self, textCaps=True,
                                               style=uic.BTN_DEFAULT,
                                               toolTip="Cancel these changes and close the window")

        self.newHotkeyBtn = elements.styledButton(icon="plus", parent=self, toolTip="Create a new hotkey",
                                                  style=uic.BTN_TRANSPARENT_BG)
        self.deleteHotkeyBtn = elements.styledButton(icon="xCircleMark", parent=self, toolTip="Delete selected hotkey",
                                                     style=uic.BTN_TRANSPARENT_BG)
        self.revertHotkeysBtn = elements.styledButton(icon="arrowback", parent=self,
                                                      toolTip="Revert hotkey to previous",
                                                      style=uic.BTN_TRANSPARENT_BG)

        self.hotkeyPropertiesWgt = propertieswidget.HotkeyPropertiesWidget(self)
        self.hotkeyTable = hotkeytable.HotkeyTableWidget(self)
        self.keySetWidget = keysetwidget.KeySetWidget(self)
        self.searchWidget = hotkeytable.SearchWidget(self, self.hotkeyTable, minWidth=200)

        self.sourceCombo = SourceCombo(parent=self, keysetManager=self.keySetManager)

        self.initUI()
        self.connections()
        self.checkInstalled()

    def initUI(self):
        # icon
        self.initDialogBoxes()

        # Inner layout (With the hotkey and properties)
        # The Keyset selection layout at the top

        self.hotkeyTableWgt = self.getHotkeyTableWgt()
        splitter = QtWidgets.QSplitter(self)

        splitter.addWidget(self.hotkeyTableWgt)
        splitter.addWidget(self.hotkeyPropertiesWgt)
        windowWidth = self.hotkeyManagerUi.windowWidth  # see hotkeyeditorui.HotkeyEditorUI for setting window size
        splitter.setSizes([windowWidth / 2, windowWidth / 2])

        self.hotkeyManagerUi.titlebarContentsLayout().addWidget(self.keySetWidget)

        # Main Layout
        mainLayout = QtWidgets.QVBoxLayout()

        headerLayout = QtWidgets.QHBoxLayout()
        headerLayout.insertStretch(2, 1)
        headerLayout.setContentsMargins(0, 0, 0, 0)

        mainLayout.addLayout(headerLayout)
        mainLayout.addWidget(splitter)
        mainLayout.setStretch(2, 1)

        self.revertHotkeysBtn.setEnabled(False)
        self.setLayout(mainLayout)

    def checkInstalled(self, ):
        # Check if the following keysets exist
        installed = False

        for k in c.KEYSETS:
            if hotkeyutils.mayaKeySetExists(k):
                installed = True
                break

        if not installed:
            installCheckBox = QtWidgets.QCheckBox("Use new hotkeys")
            installCheckBox.setChecked(True)
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIcon(QtWidgets.QMessageBox.Information)
            msgbox.setWindowTitle('Install Zoo Hotkeys')
            msgbox.setText("Zoo Hotkeys has not yet been installed.\n\n"
                           "Do you wish to install? You can also optionally use the new hotkeys.\n")
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            msgbox.setCheckBox(installCheckBox)
            ret = msgbox.exec_()

            if ret == QtWidgets.QMessageBox.Yes:
                self.installHotkeys(applySet=installCheckBox.isChecked())
            else:
                self.close()

    def initDialogBoxes(self):
        self.deleteKeySetMsgBox.setText("The document has been modified.")
        self.deleteKeySetMsgBox.setInformativeText("Do you want to save your changes?")
        self.deleteKeySetMsgBox.setStandardButtons(QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard |
                                                   QtWidgets.QMessageBox.Cancel)
        self.deleteKeySetMsgBox.setDefaultButton(QtWidgets.QMessageBox.Save)

    def getHotkeyTableWgt(self):
        wgt = QtWidgets.QWidget(self)
        tableLayout = elements.GridLayout(parent=self,
                                          margins=(uic.SMLPAD, uic.SMLPAD, 0, uic.BOTPAD),
                                          spacing=uic.SREG)

        # Hotkey Buttons
        tableBtnsLayout = elements.hBoxLayout(parent=self,
                                              margins=(uic.SMLPAD, uic.SMLPAD, uic.SMLPAD, 0),
                                              spacing=uic.SSML)

        if self.keySetManager.isLockedKeySet() and not hotkeyutils.isAdminMode():
            self.newHotkeyBtn.setEnabled(False)
            self.deleteHotkeyBtn.setEnabled(False)
        else:
            self.newHotkeyBtn.setEnabled(True)
            self.deleteHotkeyBtn.setEnabled(True)

        hotkeyBtnLabel = elements.Label("Add/Remove Hotkeys", self)

        tableBtnsLayout.addWidget(hotkeyBtnLabel)
        tableBtnsLayout.addWidget(self.newHotkeyBtn)
        tableBtnsLayout.addWidget(self.deleteHotkeyBtn)
        tableBtnsLayout.addStretch(1)
        tableBtnsLayout.addWidget(self.searchWidget)
        tableBtnsLayout.addWidget(self.revertHotkeysBtn)

        # Reset Apply Save
        dialogueLayout = elements.hBoxLayout(parent=self, margins=(0, uic.SMLPAD, 0, 0), spacing=uic.SREG)

        dialogueLayout.addWidget(self.saveCloseBtn)
        dialogueLayout.addWidget(self.applyBtn)
        dialogueLayout.addWidget(self.cancelBtn)

        tableLayout.addWidget(self.sourceCombo, 1, 0, 1, 1)

        tableLayout.addWidget(self.hotkeyTable, 2, 0, 1, 1)
        tableLayout.addLayout(tableBtnsLayout, 3, 0, 1, 1)
        tableLayout.addLayout(dialogueLayout, 4, 0, 1, 1)
        wgt.setLayout(tableLayout)

        return wgt

    def reloadActive(self):
        pass

    def setRevertEnabled(self, value):
        self.revertHotkeysBtn.setEnabled(value)

    def updateRevertUi(self):
        modified = self.keySetManager.isModified()
        self.revertHotkeysBtn.setEnabled(modified)

    def setHotkeyUiEnabled(self, enabled):
        if self.deleteHotkeyBtn and self.newHotkeyBtn:
            self.deleteHotkeyBtn.setEnabled(enabled)
            self.newHotkeyBtn.setEnabled(enabled)

    def setKeySet(self, name):
        self.hotkeyTable.setKeySet(name)
        self.hotkeyPropertiesWgt.clearProperties()

    def setKeySetUi(self, keySet):
        self.hotkeyTable.setKeySet(keySet)

    def deleteHotkey(self):
        hotkey = self.hotkeyTable.selectedHotkey
        if self.keySetManager.deleteHotkey(hotkey):

            # note parenting to None to avoid stylesheet issues
            ret = QtWidgets.QMessageBox.warning(
                None,
                'Delete Hotkey',
                'Are you sure you want to delete the Hotkey: \n\n{}'.format(hotkey.prettyName),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)

            if ret == QtWidgets.QMessageBox.Yes:
                self.hotkeyTable.removeRow(self.hotkeyTable.selectedRow)
                self.hotkeyPropertiesWgt.setEnabled(False)
                self.hotkeyPropertiesWgt.clearProperties()
                self.keySetManager.setModified(True)
                self.updateRevertUi()

    def keySetCleanUp(self):
        """
        The UI clean up after a key set has been deleted
        :return:
        """
        self.hotkeyTable.empty()

    def newHotkey(self):
        # note setting the parent to None to avoid stylesheet issues
        newHotkey, ret = QtWidgets.QInputDialog.getText(
            None,
            'New Hotkey',
            'Please enter a name for this Hotkey',
            text="")

        if ret:
            hotkey = self.keySetManager.newHotkey(newHotkey)

            if hotkey is False:
                logger.warning("{} already exists! Cancelling operation.".format(newHotkey))
                return

            self.hotkeyTable.addRow(hotkey)
            self.keySetManager.setModified(True)
            self.updateRevertUi()

    def connections(self):
        self.deleteHotkeyBtn.leftClicked.connect(self.deleteHotkey)
        self.newHotkeyBtn.leftClicked.connect(self.newHotkey)
        self.revertHotkeysBtn.leftClicked.connect(self.revertHotkeysClicked)
        self.keySetWidget.keySetCombo.activated.connect(self.sourceCombo.updateSources)

        self.applyBtn.leftClicked.connect(self.applyClicked)
        self.saveCloseBtn.leftClicked.connect(self.saveCloseClicked)
        self.cancelBtn.leftClicked.connect(self.cancelClicked)

    def installHotkeys(self, applySet=True):
        """ Install hotkeys

        :return:
        """

        switch = ""

        if not applySet:
            switch = cmds.hotkeySet(current=1, q=1)

        # Everything should be loaded from the keySetManager constructor
        self.keySetManager.installAll()
        self.keySetManager.save()

        self.keySetWidget.setEnabled(True)
        self.hotkeyTableWgt.setEnabled(True)

        if applySet:
            # Probably should be moved to hotkeyView rather than keysetwidget
            self.keySetWidget.keySetUiSwitch(c.DEFAULT_KEYSET)

            self.keySetWidget.applySet(c.DEFAULT_KEYSET)
            self.sourceCombo.updateSources()
        else:
            # self.setActive(switch, mayaOnly=True)
            cmds.hotkeySet(switch, current=1, e=1)

    def applyClicked(self):
        QtCore.QTimer.singleShot(0, self.keySetManager.save)

    def saveCloseClicked(self):
        """ Save and close

        :return:
        :rtype:
        """
        self.hotkeyManagerUi.hide()
        currentKeySet = self.keySetManager.currentKeySet().keySetName
        self.keySetManager.save()
        self.keySetManager.setActive(currentKeySet)  # todo: this is hacky, it shouldnt change the keyset on .save()
        self.close()

    def cancelClicked(self):
        self.close()

    def revertHotkeysClicked(self):
        current = self.keySetManager.currentKeySet().keySetName

        # Note parenting to None to avoid stylesheet issues
        ret = QtWidgets.QMessageBox.warning(
            None,
            'Revert Hotkey Changes?',
            'Are you sure you want to revert the all changes made this session to: \n\n{}'.format(current),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)

        if ret == QtWidgets.QMessageBox.Yes:
            logger.info("Reverting hotkeys")
            self.keySetManager.revertCurrentKeySet()

            self.hotkeyTable.updateHotkeys()
            self.setRevertEnabled(False)

        elif ret == QtWidgets.QMessageBox.Cancel:
            logger.info("cancel was clicked")

    def close(self):
        """
        Close hotkeyManager window.
        """
        self.hotkeyManagerUi.close()


class SourceCombo(elements.ComboBoxSearchable):
    separator = "------"
    suffix = "[ZOO]"

    def __init__(self, parent=None, keysetManager=None):

        self.keysetManager = keysetManager

        super(SourceCombo, self).__init__(parent=parent, text="Override Base Hotkey Set:", items=const.KEYSETS)

        self.itemChanged.connect(self.sourceChanged)

        self.updateSources()

    def updateSources(self):

        keyset = self.keysetManager.currentKeySet()
        self.clear()
        defaultHotkeySets = [const.DEFAULT_MAYA_NOZOO, const.DEFAULT_MAYA, const.DEFAULT_KEYSET]
        hotkeySets = cmds.hotkeySet(q=True, hotkeySetArray=True)

        try:
            [hotkeySets.remove(d) for d in defaultHotkeySets]
        except ValueError:
            # Hotkeys not set up yet, return through and let the program install it first
            return

        hotkeySets = [self.toNice(h) for h in hotkeySets]

        hotkeySets = defaultHotkeySets + [self.separator, ""] + hotkeySets

        if keyset is not None:
            hotkeySets.remove(self.toNice(keyset.keySetName))

        self.blockSignals(True)
        self.addItems(hotkeySets)
        self.blockSignals(False)

        if keyset:
            self.setToText(self.toNice(keyset.source))

    def toNice(self, keysetName):
        if keysetName is None:
            return ""

        if "Zoo_User_" in keysetName:
            return keysetName.replace("Zoo_User_", "") + " " + self.suffix
        return keysetName

    def toKeySetName(self, niceName):
        if self.suffix in niceName:
            text = niceName.replace(" " + self.suffix, "")
            text = "Zoo_User_" + text
            return text
        return niceName

    def sourceChanged(self, index, text):
        if text == self.separator or text == "":
            return

        text = self.toKeySetName(text)

        keyset = self.keysetManager.currentKeySet()
        keyset.setSource(text)
        keyset.updateHotkeys()
