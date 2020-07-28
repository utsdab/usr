from Qt import QtWidgets, QtGui

from zoo.apps.hotkeyeditor.core import const as c, hotkeys
from zoo.apps.hotkeyeditor.core import utils
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import zlogging
from zoo.libs.pyqt import uiconstants as uic

logger = zlogging.getLogger(__name__)


class HotkeyPropertiesWidget(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        """The properties widget that sits to the right inside the Zoo Hotkey Editor window

        :param parent: the widget parent
        :type parent: class
        """
        super(HotkeyPropertiesWidget, self).__init__(parent)

        self.hotkeyView = self.parent()
        self.keySetManager = self.hotkeyView.keySetManager
        self.blockModified = False

        propLayout = self.initWidgetsLayouts()  # all widgets and layouts

        self.setEnabled(False)
        self.setContentsMargins(0, 0, 0, 0)
        self.setLayout(propLayout)

        self.connections()

    def initWidgetsLayouts(self):
        """Creates the Widgets and Layouts for the properties section of the Zoo Hotkey Editor"""

        # -------------------------------
        # WIDGETS
        # -------------------------------

        # NAME -----------------------
        toolTip = "Name of the selected hotkey. Rename with the rename button (right)."
        nameLbl = elements.Label("Hotkey Name", self, toolTip=toolTip)
        self.nameEdit = elements.LineEdit("", parent=self, toolTip=toolTip)
        self.nameEdit.setEnabled(False)
        self.renameBtn = elements.styledButton("",
                                               "pencil",
                                               self,
                                               toolTip="Rename this hotkey",
                                               style=uic.BTN_TRANSPARENT_BG,
                                               minWidth=uic.BTN_W_ICN_REG)
        # RUNTIME COMMAND -----------------------
        toolTip = "Select/search for to assign a runtime command to this hotkey.\n" \
                  "Add a new runtime command with the add new button (right)."
        runTimeCmdLbl = elements.Label("Runtime Command", self, toolTip=toolTip)
        self.newRuntimeCommandBtn = elements.styledButton("",
                                                          "plus",
                                                          self,
                                                          toolTip="Add and assign a new runtime command",
                                                          style=uic.BTN_TRANSPARENT_BG,
                                                          minWidth=uic.BTN_W_ICN_REG)
        self.runtimeCmdCombo = elements.ComboBoxSearchable(parent=self, toolTip=toolTip)
        self.updateRuntimeCombo()
        # HOTKEY CATEGORY -------------------
        toolTip = "Optional category as shown in Maya's Hotkey Editor\n" \
                  "Example 'Custom Scripts.Category Name'\n" \
                  "Find in Maya's Hotkey Editor...\n" \
                  "Maya Hotkey Editor > Edit Hotkeys For: > Custom Scripts"
        categoryLbl = elements.Label("Hotkey Category", self, toolTip=toolTip)
        self.categoryBox = elements.LineEdit(parent=self, toolTip=toolTip)
        if not utils.isAdminMode():
            self.categoryBox.hide()
            categoryLbl.hide()
        # KEY EVENT -----------------------
        toolTip = "On Press: the hotkey is activated as the keyboard key is pressed (down)\n" \
                  "On Release: the hotkey is activated as the keyboard key is released (up)"
        keyEventLbl = elements.Label("Key Event", self)
        keyEventLbl.setToolTip(toolTip)
        self.keyEventWgt = QtWidgets.QWidget(self)
        self.keyEventWgt.setToolTip(toolTip)
        # Radio Buttons Note: elements.RadioButtonGroup() could use later instead
        self.onPressRadio = QtWidgets.QRadioButton("On Press", self.keyEventWgt)
        self.onReleaseRadio = QtWidgets.QRadioButton("On Release", self.keyEventWgt)
        # LANGUAGE -----------------------  (note: elements.RadioButtonGroup() could be switched later)
        toolTip = "The hotkey code below is either 'MEL' or 'Python'"
        languageLbl = elements.Label("Language", self)
        languageLbl.setToolTip(toolTip)
        self.languageWgt = QtWidgets.QWidget(self)
        self.languageWgt.setToolTip(toolTip)
        # Radio Buttons Note: elements.RadioButtonGroup() could use later instead
        self.languageMelRadio = QtWidgets.QRadioButton("Mel", self.languageWgt)
        self.languagePyRadio = QtWidgets.QRadioButton("Python", self.languageWgt)
        # COMMAND CODE AREA -----------------------
        self.commandEdit = CommandTextEdit(parent=self)
        self.commandEdit.setWordWrapMode(QtGui.QTextOption.WrapMode.NoWrap)

        # -------------------------------
        # LAYOUTS
        # -------------------------------

        # MAIN LAYOUTS -----------------------
        propLayout = elements.vBoxLayout(self)
        gridLayout = elements.GridLayout(self, margins=(uic.SMLPAD, uic.TOPPAD, uic.SMLPAD, uic.BOTPAD),
                                         spacing=uic.SLRG)
        # KEY EVENT LAYOUT -----------------------
        self.keyEventLayout = elements.hBoxLayout(self, margins=(0, 15, 0, 0))
        self.keyEventWgt.setLayout(self.keyEventLayout)
        self.keyEventLayout.addWidget(self.onPressRadio)
        self.keyEventLayout.addWidget(self.onReleaseRadio)
        self.keyEventLayout.setSpacing(0)

        # LANGUAGE LAYOUT -----------------------
        self.languageLayout = elements.hBoxLayout(self, margins=(0, 5, 0, 10))
        self.languageWgt.setLayout(self.languageLayout)
        self.languageLayout.addWidget(self.languageMelRadio)
        self.languageLayout.addWidget(self.languagePyRadio)
        self.languageLayout.setSpacing(0)

        # ADD TO MAIN GRID LAYOUT -----------------------
        r = 0
        gridLayout.addWidget(nameLbl, r, 0)
        gridLayout.addWidget(self.nameEdit, r, 1)
        gridLayout.addWidget(self.renameBtn, r, 2)
        r += 1
        gridLayout.addWidget(runTimeCmdLbl, r, 0)
        gridLayout.addWidget(self.runtimeCmdCombo, r, 1)
        gridLayout.addWidget(self.newRuntimeCommandBtn, r, 2)
        r += 1
        gridLayout.addWidget(categoryLbl, r, 0)
        gridLayout.addWidget(self.categoryBox, r, 1)
        r += 1
        gridLayout.addWidget(keyEventLbl, r, 0)
        gridLayout.addWidget(self.keyEventWgt, r, 1)
        r += 1
        gridLayout.addWidget(languageLbl, r, 0)
        gridLayout.addWidget(self.languageWgt, r, 1)
        # ADD GRID AND CODE TEXT BOTTOM ---------------------------
        propLayout.addLayout(gridLayout)
        propLayout.addWidget(self.commandEdit)

        return propLayout

    def getRuntimeCmdList(self):
        userRTCs, zooRTCs, mayaRTCs = self.keySetManager.getRuntimeCommandNames()

        ret = [""]
        ret.append("=== USER COMMANDS ===")
        ret += utils.sortedIgnoreCase(userRTCs) + ["", ""]
        ret.append("=== ZOO COMMANDS ===")
        ret += utils.sortedIgnoreCase(zooRTCs) + ["", ""]
        ret.append("=== MAYA COMMANDS ===")
        ret += utils.sortedIgnoreCase(mayaRTCs)
        return ret

    def setPropertiesByHotkey(self, hotkey):
        """

        :param hotkey:
        :type hotkey: hotkeys.Hotkey
        :return:
        """
        hotkey.setPrettyName()  # Maybe use getter and setter properties
        name = hotkey.prettyName
        runtimeCmd = hotkey.runtimeCommand
        language = hotkey.language
        category = hotkey.category
        commandScript = hotkey.commandScript
        keyEvent = hotkey.keyEvent
        enableCmd = True

        rtc = {"commandLanguage": "",
               "category": "",
               "command": ""}

        # If command script is empty chances are it's a runtime command from Zoo
        if commandScript == "" or hotkey.runtimeType == c.RTCTYPE_ZOO or hotkey.runtimeType == c.RTCTYPE_MAYA:

            defaultRTC = self.keySetManager.defaultKeySet.getRuntimeCmdByName(runtimeCmd)
            mayaRTC, lang = utils.getMayaRuntimeCommand(runtimeCmd)

            if mayaRTC is not None:
                rtc['command'] = mayaRTC
                hotkey.runtimeType = c.RTCTYPE_MAYA

            elif defaultRTC is not None:
                rtc = defaultRTC.cmdAttrs
                hotkey.runtimeType = c.RTCTYPE_ZOO

            if rtc is not None:
                language = rtc['commandLanguage']
                category = rtc['category']
                commandScript = rtc['command']

                if not utils.isAdminMode():
                    enableCmd = False

        if commandScript == "" or hotkey.runtimeType == c.RTCTYPE_MAYA:

            rtc = self.keySetManager.defaultKeySet.getRuntimeCmdByName(runtimeCmd)
            if rtc is not None:
                language = rtc.cmdAttrs['commandLanguage']
                category = rtc.cmdAttrs['category']
                commandScript = rtc.cmdAttrs['command']

                hotkey.runtimeType = c.RTCTYPE_ZOO
                if not utils.isAdminMode():
                    enableCmd = False

        self.setProperties(name, runtimeCmd,
                           language, keyEvent,
                           category, commandScript,
                           enableCommandScript=enableCmd)

    def setProperties(self, name=None, runtimeCmd=None, language=None,
                      keyEvent=None, category=None, commandScript=None, enableCommandScript=True):
        """ Set up the properties in the UI

        :param name: Name(command) of the hotkey
        :param runtimeCmd: Runtime comand of hotkey
        :param language: Language of command str (mel or python)
        :param keyEvent: Press or Release
        :param category: The category as shown in maya
        :param commandScript: The actual command to be run in the runtime command
        :return:
        """
        if name is not None:
            self.nameEdit.setText(name.strip())

        if runtimeCmd is not None:
            self.runtimeCmdCombo.setToText(runtimeCmd)

            if self.runtimeCmdCombo.currentText() == "" or not enableCommandScript:
                self.categoryBox.setEnabled(False)
                self.commandEdit.setEnabled(False)
            else:
                self.categoryBox.setEnabled(True)
                self.commandEdit.setEnabled(True)

        if language is not None:
            if language == "python":
                self.languagePyRadio.setChecked(True)
            elif language == "mel":
                self.languageMelRadio.setChecked(True)
            else:
                self.languagePyRadio.setChecked(False)
                self.languageMelRadio.setChecked(False)

        if keyEvent is not None:
            if keyEvent == c.KEYEVENT_RELEASE:
                self.onReleaseRadio.setChecked(True)
            elif keyEvent == c.KEYEVENT_PRESS:
                self.onPressRadio.setChecked(True)
            else:
                self.onReleaseRadio.setChecked(False)
                self.onPressRadio.setChecked(False)

        if category is not None:
            self.categoryBox.setText(category)

        # Make it pretty in the ui
        if commandScript is not None:
            commandScript = utils.cleanScript(commandScript)
            self.commandEdit.setText(commandScript)

        # If its locked disable it
        if self.keySetManager.isKeySetLocked():
            self.keyEventWgt.setEnabled(False)
            self.runtimeCmdCombo.setEnabled(False)
        else:
            self.keyEventWgt.setEnabled(True)
            self.runtimeCmdCombo.setEnabled(True)

        self.setEnabled(True)

    def clearProperties(self):
        """
        Clear out the properties in the UI

        :return:
        """

        self.blockModified = True

        self.updateRuntimeCombo()

        self.nameEdit.setText("")

        self.languagePyRadio.setChecked(False)
        self.languageMelRadio.setChecked(False)

        self.onReleaseRadio.setChecked(False)
        self.onPressRadio.setChecked(False)

        self.commandEdit.setText("")

        self.categoryBox.setEnabled(False)
        self.commandEdit.setEnabled(True)

        self.runtimeCmdCombo.setCurrentIndex(0)
        self.blockModified = False

    def updateRuntimeCombo(self):
        self.runtimeCmdCombo.clear()
        runtimeCmdsList = self.getRuntimeCmdList()
        self.runtimeCmdCombo.addItems(runtimeCmdsList)

    def connections(self):
        """
        Connect all the UI elements

        :return:
        """

        self.newRuntimeCommandBtn.clicked.connect(self.newRuntimeBtnClicked)
        self.renameBtn.clicked.connect(self.renameClicked)

        self.languagePyRadio.toggled.connect(self.languageRadioToggled)
        self.languageMelRadio.toggled.connect(self.languageRadioToggled)

        self.onReleaseRadio.toggled.connect(self.keyEventRadioToggled)
        self.onPressRadio.toggled.connect(self.keyEventRadioToggled)

        self.categoryBox.editingFinished.connect(self.categoryBoxFinished)
        self.commandEdit.textChanged.connect(self.commandEditChanged)

        self.runtimeCmdCombo.activated.connect(self.runtimeCmdComboActivated)
        self.runtimeCmdCombo.editTextChanged.connect(self.runtimeCmdComboEdit)

        # self.nameEdit.editingFinished.connect(self.nameEditFinished)

    def runtimeCmdComboEdit(self):
        # Deprecated
        pass

    def nameEditFinished(self):
        if not hasattr(self.hotkeyView, "hotkeyTable"):
            return

        newName = self.nameEdit.text()

        selectedHotkey = self.selectedHotkey()
        # name = selectedHotkey.getNameCmdName(includeSuffix=False)

        selectedHotkey.renameNameCommand(newName)
        self.hotkeyView.hotkeyTable.refreshProperties()

    def renameClicked(self):
        selectedHotkey = self.selectedHotkey()
        name = selectedHotkey.getNameCmdName(includeSuffix=False)

        newName, ret = QtWidgets.QInputDialog.getText(
            self,
            'Rename Name Command',
            'Rename to:',
            text=name)

        if ret:
            checkName = newName + "NameCommand"
            if self.keySetManager.currentKeySet().nameCommandExists(checkName):
                logger.warning("{} hotkey already exists! Cancelling operation.".format(utils.toRuntimeStr(newName)))
                return

            retNameCmd = selectedHotkey.renameNameCommand(newName)

            if " " in newName:
                logger.warning("Spaces Found! Removing and setting name to {}".format(retNameCmd))

            self.hotkeyView.hotkeyTable.refreshProperties()

    def newRuntimeBtnClicked(self):
        # Note setting the parent to None to avoid stylesheet issues
        newRuntime, ret = QtWidgets.QInputDialog.getText(
            None,
            'New Runtime Command',
            'Please enter a name:',
            text="")

        if ret:
            i = 1
            checkName = str.replace(str(newRuntime), " ", "_")

            while utils.runtimeCmdExists(checkName):
                checkName = newRuntime + str(i)
                i += 1

                if i == 99:
                    logger.warning("Couldn't find unique name! No command was created")
                    return

            if not utils.runtimeCmdExists(checkName):
                # TODO: This should be separated out
                self.setupRuntimeCmdUi(checkName)
                self.runtimeCmdCombo.addItem(checkName)
                self.updateRuntimeCombo()
                self.runtimeCmdCombo.setToText(checkName)

    def runtimeCmdComboActivated(self):
        text = self.runtimeCmdCombo.currentText()

        if text == c.RTCOMBO_USERCMDS or text == c.RTCOMBO_MAYACMDS or text == c.RTCOMBO_ZOOCMDS:
            return

        self.setupRuntimeCmdUi(text)

    def setupRuntimeCmdUi(self, text):
        # This place can probably be simplified
        selectedHotkey = self.selectedHotkey()

        # Uses an existing one if it already exists
        # This needs to be cleaned to reflect the switch to combo box
        rtc = self.keySetManager.setupRuntimeCmd(selectedHotkey, text)

        """language = selectedHotkey.language
        category = selectedHotkey.category
        commandScript = selectedHotkey.commandScript
        keyEvent = selectedHotkey.keyEvent"""

        language = rtc['commandLanguage']
        category = rtc['category']
        commandScript = rtc['command']
        keyEvent = ""  # selectedHotkey.keyEvent
        rtcType = rtc['rtcType']

        # If a runtime command already exists populate the ui data
        self.setProperties(language=language, keyEvent=keyEvent,
                           category=category, commandScript=commandScript)

        if selectedHotkey.modified and not self.blockModified:
            self.keySetManager.setModified(True)
            self.hotkeyView.updateRevertUi()

        if text is not "":
            self.categoryBox.setEnabled(True)
            self.commandEdit.setEnabled(True)
            self.languageWgt.setEnabled(True)

        if rtcType == c.RTCTYPE_MAYA or rtcType == c.RTCTYPE_ZOO:
            # Zoo is not editable unless admin mode
            if not utils.isAdminMode():
                self.languageWgt.setEnabled(False)
                self.commandEdit.setEnabled(False)

    def categoryBoxFinished(self):
        category = self.categoryBox.text()
        selectedHotkey = self.selectedHotkey()

        selectedHotkey.setCategory(category)

        if selectedHotkey.modified and not self.blockModified:
            self.keySetManager.setModified(True)
            self.hotkeyView.updateRevertUi()

    def languageRadioToggled(self, toggled):
        selectedHotkey = self.selectedHotkey()

        if self.languagePyRadio.isChecked():
            selectedHotkey.setLanguage(c.LANGUAGE_PYTHON)
        elif self.languageMelRadio.isChecked():
            selectedHotkey.setLanguage(c.LANGUAGE_MEL)
        else:
            logger.warning("HotkeyPropertiesWidget.languageRadioToggled(): Language not set!")

        if selectedHotkey.modified and not self.blockModified:
            self.keySetManager.setModified(True)
            self.hotkeyView.updateRevertUi()

    def keyEventRadioToggled(self, toggled):

        selectedHotkey = self.selectedHotkey()

        if self.onPressRadio.isChecked():
            selectedHotkey.setKeyEvent(c.KEYEVENT_PRESS)
        elif self.onReleaseRadio.isChecked():
            selectedHotkey.setKeyEvent(c.KEYEVENT_RELEASE)
        else:
            logger.warning("HotkeyPropertiesWidget.keyEventRadioToggled(): key Event not set!")

        if selectedHotkey.modified and not self.blockModified:
            self.keySetManager.setModified(True)
            self.hotkeyView.updateRevertUi()

        # Update table ui with new name
        self.nameEdit.setText(selectedHotkey.getPrettyName())
        self.hotkeyView.hotkeyTable.updateRow()

    def commandEditChanged(self):

        selectedHotkey = self.selectedHotkey()
        if selectedHotkey is None or self.blockModified:
            return

        selectedHotkey.setCommandScript(self.commandEdit.toPlainText())

        if selectedHotkey.modified and not self.blockModified:
            self.keySetManager.setModified(True)
            self.hotkeyView.updateRevertUi()

    def selectedHotkey(self):
        """

        :return:
        :rtype: hotkeys.Hotkey
        """

        selectedHotkey = self.hotkeyView.hotkeyTable.selectedHotkey
        return selectedHotkey


class CommandTextEdit(QtWidgets.QTextEdit):
    """ CSS Purposes """
