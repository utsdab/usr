import collections, os
from functools import partial

from Qt import QtWidgets, QtCore

import maya.api.OpenMaya as om2

from preferences.interface.preference_interface import ZooToolsPreference
from zoo.libs.pyqt import uiconstants as uic
from zoo.apps.preferencesui import model
from zoo.apps.preferencesui.example import examplewidget
from zoo.libs.pyqt import utils, stylesheet
from zoo.libs.utils import colour, filesystem
from zoo.preferences.core import preference
from zoo.libs.maya.qt import cmdswidgets
from zoo.libs.pyqt.widgets import elements
from zoo.apps.preferencesui.stylesheetui import stylesheetui_constants as sc


class InterfaceWidget(model.SettingWidget):
    """Widget that creates the UI with color picker/size/icon settings for Stylesheets
    """
    categoryTitle = "Theme Colors"
    prefDataRelativePath = "prefs/global/stylesheet.pref"

    def __init__(self, parent=None):
        super(InterfaceWidget, self).__init__(parent)
        self.sendStyleSheetUpdate = False
        self.allCurrentThemeDict = dict()
        self.skipComboChange = False  # for methods such as renaming or adding a theme, the UI shouldn't update
        self.globalColorUpdate = True  # when False disables the global color updates as the globals are set
        self.updateSheets()  # update all themes (all dictionaries) each theme is a sheet
        self._initUI()
        self.connections()

    def _initUI(self):
        """Build the UI"""
        layout = QtWidgets.QVBoxLayout()

        self.sectionGridWidgetList = list()
        themeSwitchLayout = QtWidgets.QHBoxLayout()
        layout.addLayout(themeSwitchLayout)
        self.setLayout(layout)
        themeComboBtnsLayout = elements.hBoxLayout()
        toolTip = "Choose the current color UI Theme"
        themeBoxAdminLayout = elements.hBoxLayout()
        self.themeBox = elements.ComboBoxRegular("Theme:",labelRatio=1, boxRatio=2, toolTip=toolTip,
                                                sortAlphabetically=True)
        comboNameList = self.getThemeNameList()
        for i, name in enumerate(comboNameList):
            self.themeBox.addItem(name)
            # self.themeBox.setItemData(self.themeBox.count() - 1, comboInfoList[i])
        toolTip = "Admin save to {} for setting Zoo Defaults".format(InterfaceWidget.prefDataRelativePath)
        self.adminSaveBtn = elements.styledButton("Admin", "save", parent=self, toolTip=toolTip,
                                                    minWidth=uic.BTN_W_REG_SML, maxWidth=uic.BTN_W_REG_SML,
                                                    iconColor=uic.COLOR_ADMIN_GREEN_RGB)
        if os.environ["ZOO_ADMIN"] == "0":
            self.adminSaveBtn.setHidden(True)
        themeBoxAdminLayout.addWidget(self.themeBox)
        themeBoxAdminLayout.addWidget(self.adminSaveBtn)
        toolTip = "Create/add a new UI Theme"
        self.createNewThemeBtn = elements.styledButton(icon="plus", parent=self, toolTip=toolTip,
                                                       style=uic.BTN_TRANSPARENT_BG,
                                                       minWidth=uic.BTN_W_ICN_REG)
        toolTip = "Rename the current UI Theme"
        self.renameThemeBtn = elements.styledButton(icon="editText", parent=self, toolTip=toolTip,
                                                    style=uic.BTN_TRANSPARENT_BG,
                                                    minWidth=uic.BTN_W_ICN_REG)
        toolTip = "Delete the current UI Theme"
        self.deleteThemeBtn = elements.styledButton(icon="trash", parent=self, toolTip=toolTip,
                                                    style=uic.BTN_TRANSPARENT_BG,
                                                    minWidth=uic.BTN_W_ICN_REG)

        toolTip = "Open the Test Colors Window"
        self.themeExampleBtn = elements.styledButton("Test Window", "windowBrowser", parent=self, toolTip=toolTip,
                                                     minWidth=uic.BTN_W_REG_LRG, maxWidth=uic.BTN_W_REG_LRG)

        toolTip = "Revert current theme to factory default"
        self.revertThemeBtn = elements.styledButton(icon="shippingBox", parent=self,
                                                    style=uic.BTN_TRANSPARENT_BG, toolTip=toolTip,
                                                    minWidth=uic.BTN_W_ICN_REG)


        themeComboBtnsLayout.addWidget(self.createNewThemeBtn, 1)
        themeComboBtnsLayout.addWidget(self.renameThemeBtn, 1)
        themeComboBtnsLayout.addWidget(self.revertThemeBtn, 1)
        themeComboBtnsLayout.addWidget(self.deleteThemeBtn, 1)
        themeComboBtnsLayout.addStretch(10)
        themeComboBtnsLayout.addWidget(self.themeExampleBtn, 10)
        themeSwitchLayout.addLayout(themeBoxAdminLayout, 1)
        themeSwitchLayout.addLayout(themeComboBtnsLayout, 1)

        self.themeWindow = examplewidget.exampleWidget(parent=self)

        currentActiveTheme = self.prefs["current_theme"]
        themeDict = self.sheets[currentActiveTheme]
        self.themeBox.setCurrentText(currentActiveTheme)
        self.themeWindow.setStyleSheet(self.prefInterface.stylesheet().data)
        # build the color globals section
        globalColorsVLayout = self.buildGlobalColorsUI(themeDict)
        layout.addLayout(globalColorsVLayout)
        # build the color tweak layouts
        layout.addItem(elements.Spacer(0, 10))
        sectionLabel = elements.Label("Style By Widget", parent=self, upper=True)
        utils.setStylesheetObjectName(sectionLabel, "HeaderLabel")  # set stylesheet
        layout.addWidget(sectionLabel)
        colorTweakVLayout = self.buildColorTweakUI(themeDict)
        layout.addLayout(colorTweakVLayout)
        layout.addStretch(1)

    def ui_createWindowPopup(self):
        message = "Create and save a new theme name."
        newThemeName = elements.InputDialog(windowName="Add A New UI Theme", textValue="New Theme Name", parent=self,
                                           message=message)
        return newThemeName

    def ui_revertThemePopup(self):
        message = "Are you sure you want to revert \"{}\" theme?".format(self.themeBox.currentText())
        okPressed = elements.MessageBox_ok(windowName="Revert theme to default", parent=None, message=message)
        return okPressed

    def ui_adminSave(self):
        """Saves all themes to the stylesheet within zootools_pro

        :return okPressed: has the ok button been pressed, or was it cancelled
        :rtype okPressed: bool
        """
        message = "Are you sure you want to ADMIN save all themes as defaults?"
        # TODO parent is set to None to default to Maya stylesheeting
        okPressed = elements.MessageBox_ok(windowName="Admin theme Save?", parent=None, message=message)
        return okPressed

    def ui_renameWindowPopup(self):
        """rename popup window, returns new name if ok is pressed

        :return newThemeName: the new name of the theme to be renamed
        :rtype newThemeName: str
        """
        currentTheme = self.themeBox.currentText()
        message = "Rename '{}' theme?".format(currentTheme)
        newThemeName = elements.InputDialog(windowName="Rename Theme", textValue=currentTheme, parent=self,
                                           message=message)
        return newThemeName

    def ui_deleteWindowPopup(self):
        """delete popup window asking whether to delete a theme

        :return okPressed: has the ok button been pressed, or was it cancelled
        :rtype okPressed: bool
        """
        currentTheme = self.themeBox.currentText()
        message = "Delete the theme \n\n'{}' \n\nThis will permanently delete the theme".format(currentTheme)
        okPressed = elements.MessageBox_ok(windowName="Delete Theme?", parent=self, message=message)
        return okPressed

    def getThemeNameList(self):
        """returns a list of theme name (strings) alphabetically sorted

        :return comboNameList: list of theme name (strings) alphabetically sorted
        :rtype comboNameList: list
        """
        comboNameList = list()
        for name, info in self.sheets.items():
            comboNameList.append(str(name))
        comboNameList = [x.encode('UTF8') for x in comboNameList]  # if unicode convert to str
        comboNameList.sort(key=str.lower)  # sort alphabetically
        return comboNameList

    def updateComboBox(self):
        pass

    def addItemComboBox(self):
        pass

    def buildGlobalColorsUI(self, themeDict):
        """ Builds the Global Overall Colors section, uses COLOR_GROUP_DICT[colorGroup] to set section color matches

        :param themeDict: a themeDict the sheet from a single theme
        :type themeDict: dict
        :return globalColorsVLayout: the vLayout containing the Global Colors widgets
        :rtype globalColorsVLayout: QLayout
        """
        # get the colors for the initial UI
        colorList = globalColorList(themeDict)
        self.globalColorWidgetList = list()
        # build the ui with collapsable frame layout with a grid layout of color swatches inside
        globalColorsVLayout = elements.vBoxLayout(parent=self, margins=(0, 0, 0, 0), spacing=uic.SPACING)
        collapseWidget = elements.CollapsableFrameLayout("Set Overall Global Colors", parent=self, collapsed=False)
        gridLayout = elements.GridLayout(parent=self, margins=(uic.SMLPAD, uic.TOPPAD, uic.SMLPAD, uic.BOTPAD),
                                        vSpacing=uic.SREG, hSpacing=uic.SVLRG)
        row, col = 0, 0
        for i, (colorGroup, value) in enumerate(iter(sc.COLORGROUP_ODICT.items())):
            col = i % 2
            if col == 0:
                row += 1
            # convert colour
            colorSrgbInt = colour.hexToRGB(colorList[i])  # needs to be in int 255 srgb values
            colorSrgbFloat = colour.rgbIntToFloat(colorSrgbInt)
            colorLinearFloat = colour.convertColorSrgbToLinear(colorSrgbFloat)
            # Color picker
            colorPicker = cmdswidgets.MayaColorBtn(text=colorGroup, color=colorLinearFloat, parent=self,
                                                   colorWidth=100, btnRatio=35, labelRatio=75)
            gridLayout.addWidget(colorPicker, row, col, 1, 1)
            # add the color picker to the self.globalColorWidgetList so it can be iterated over later
            self.globalColorWidgetList.append(colorPicker)
        collapseWidget.addLayout(gridLayout)
        globalColorsVLayout.addWidget(collapseWidget)
        return globalColorsVLayout

    def buildColorTweakUI(self, themeDict):
        """Divides the stylesheet dict into sections for better UI organisation,
        and builds the collapse-able layout

        Uses the function divideThemeDictToSections(themeDict)

        :param themeDict: a themeDict the sheet from a single theme
        :type themeDict: dict
        """
        sectionKeyValue_odict = divideThemeDictToSections(themeDict)
        # now loop through, build each section UI with a bold QLabel then the section widgets
        collapsed = True
        colorTweakVLayout = elements.vBoxLayout(parent=self, margins=(0, 0, 0, 0), spacing=uic.SPACING)

        for sectionLabel, styleKeyDict in sectionKeyValue_odict.items():
            collapseWidget = elements.CollapsableFrameLayout(sectionLabel, parent=self, collapsed=collapsed)
            sectionGridWidget = ThemeSectionWidget(styleKeyDict, parent=self)
            collapseWidget.addWidget(sectionGridWidget)
            colorTweakVLayout.addWidget(collapseWidget)
            sectionGridWidget.colorChanged.connect(self.colorChanged)
            # append each section's grid layout, needed later for extraction and updating the data
            self.sectionGridWidgetList.append(sectionGridWidget)

        return colorTweakVLayout

    def colorChanged(self):
        """ Color changed

        :return:
        """
        # This gets run a few times in one go, so we want to set updateStyleSheet to true then run it after a bit
        if not self.sendStyleSheetUpdate:
            self.sendStyleSheetUpdate = True
            QtCore.QTimer.singleShot(50, self.updateStyleSheet)

    def updateStyleSheet(self):
        self.sendStyleSheetUpdate = False
        sheet = self.prefInterface.stylesheetFromData(self.updateCurrentKeyDict())  # the qss text for this theme
        applyStyleSheet(sheet.data)

    def setGlobalColors(self, colPickerWidget, linearColorFloat):
        """ Called when the user changes a global color, uses COLOR_GROUP_DICT[colorGroup] to set section color matches

        Iterates through the UI sections looking for matches in the color group (using the colPickerWidget label name)
        Will change all matching color pickers to the color from the colPickerWidget

        :param colPickerWidget: a global color widget (Set Overall Global Colors), will retrieve the label name
        :type colPickerWidget: zoo.libs.maya.qt.ColorCmdsWidget
        """
        if not self.globalColorUpdate:  # bail if this variable is not true, could be switching themes
            return
        # get list of Keys
        colorGroup = colPickerWidget.text()  # the label of the widget
        rgbColor = colPickerWidget.colorSrgbInt()
        keylist = list(sc.COLORGROUP_ODICT[colorGroup])  # need a copy of the list as it breaks with reassign
        # convert to nice names to match labels
        for i, key in enumerate(keylist):
            keylist[i] = themeKeyToName(key)
        # iterate through the UI Sections to see if matches and if so change the color
        for sectionGridWidget in self.sectionGridWidgetList:
            for i in range(sectionGridWidget.gridLayout.count()):
                currentWidget = sectionGridWidget.gridLayout.itemAt(i).widget()
                labelName = currentWidget.text()  # widgets are subclassed and have .text methods (label name)

                for key in keylist:  # check if the labelName is a match
                    if labelName == key:
                        currentWidget.setColorSrgbInt(rgbColor)
                        self.colorChanged()

    def updateGlobalUIColorSwatches(self):
        """ Updates the color swatch widgets in the Global grid layout to match the first key in
        each COLOR_GROUP_DICT

        Get the colors from the theme name set in the 'Theme' combo box
        """
        themeName = self.themeBox.currentText()
        themeDict = self.sheets[themeName]
        colorList = globalColorList(themeDict)
        row, col = 0, 0
        # shouldn't update the Style By Widget section so set temp variable to stop the update
        self.globalColorUpdate = False
        for i, (colorGroup, value) in enumerate(iter(sc.COLORGROUP_ODICT.items())):
            col = i % 2
            if col == 0:
                row += 1
            colorSrgbInt = colour.hexToRGB(colorList[i])  # rgb is in 255 values
            colorSrgbFloat = colour.rgbIntToFloat(colorSrgbInt)
            colorLinearFloat = colour.convertColorSrgbToLinear(colorSrgbFloat)
            self.globalColorWidgetList[i].setColorLinearFloat(colorLinearFloat)  # set the widget color
        self.globalColorUpdate = True

    def onThemeChanged(self):
        """ When the theme is changed in the Theme combo box, update the UI to match the current theme

        :return:
        """
        if self.skipComboChange:
            return
        theme = self.themeBox.currentText()

        self.setThemeUI(theme)

    def setThemeUI(self, theme):
        """ Sets the theme in the ui

        :param theme: the theme name
        :rtype theme: str
        """
        sheet = self.prefInterface.stylesheetForTheme(theme)  # the qss text for this theme
        self.themeWindow.setStyleSheet(sheet.data)  # updates the test window

        applyStyleSheet(sheet.data)

        # update the UI
        themeDict = self.sheets[theme]
        sectionKeyValue_odict = divideThemeDictToSections(themeDict)  # returns a OrderedDict(OrderedDict)
        for i, (sectionLabel, sectionDict) in enumerate(iter(sectionKeyValue_odict.items())):
            self.sectionGridWidgetList[i].buildSection(sectionDict)  # clears and rebuilds the grid section layout
        self.updateGlobalUIColorSwatches()  # updates the Overall Global Colors
        self.skipComboChange = False

    def updateCurrentKeyDict(self):
        """ Updates the current dict (one theme only) from current widget settings

        :return self.allCurrentThemeDict: Updates the current dict (one theme only) from current widget settings
        :rtype self.allCurrentThemeDict: dict
        """
        self.allCurrentThemeDict = dict()  # empty the dict
        for i, sectionGridWidget in enumerate(self.sectionGridWidgetList):
            sectionDict = sectionGridWidget.data()
            self.allCurrentThemeDict.update(sectionDict)

        return self.allCurrentThemeDict

    def updateSheets(self):
        """ Update sheets (all theme dicts) with all new settings from preference.interface("core_interface")"""

        self.prefInterface = preference.interface("core_interface")  # type: ZooToolsPreference
        self.prefs = self.prefInterface.settings().settings
        self.sheets = self.prefs["themes"]

    def serialize(self):
        """ Save the Preference file,  saves the current theme and it's dict

        Can update a current theme or add a new theme too.

        Iterate over the grid widget sections adding their dicts together to make a master stylesheet dictionary
        save it to the prefs directory as a json under the current theme name from the theme combo box.

        Keen note: Feels like this should be handled in the PreferenceManager class instead.
        """
        data = self.prefInterface.preference.findSetting(InterfaceWidget.prefDataRelativePath, root=None)
        if data.isValid():
            theme = self.themeBox.currentText()
            # iterate over the section grid layouts to create the dictionary
            data['settings']['themes'][theme] = self.updateCurrentKeyDict()  # save or add the theme dict to disk
            data['settings']['current_theme'] = theme  # save the current theme name to disk
            path = data.save(indent=True, sort=True)  # dump format nicely
            om2.MGlobal.displayInfo("Success: Theme '{}' Saved To Disk '{}'".format(theme, path))

    def revert(self):
        """ Revert settings

        :return:
        """

        # Reset stylesheet
        sheet = self.prefInterface.stylesheet()
        applyStyleSheet(sheet.data)

        self.setThemeUI(self.prefInterface.currentTheme())

    def adminSave(self):
        """ Admin save to /Preferences/prefs/global/stylesheet.pref for setting Zoo Defaults

        Will set all current settings as the Zoo Defaults for everyone

        :return:
        """

        okPressed = self.ui_adminSave()
        if not okPressed:
            om2.MGlobal.displayInfo("Admin Save Cancelled")
            return
        data = self.prefInterface.preference.findSetting(InterfaceWidget.prefDataRelativePath, root=None)
        if data.isValid():
            zoo_preferences_package_root = self.prefInterface.preference.packagePreferenceRootLocation("zoo_preferences")
            stylesheetAdminPath = zoo_preferences_package_root / InterfaceWidget.prefDataRelativePath
            theme = self.themeBox.currentText()
            # self.updateCurrentKeyDict() = iterate over the section grid layouts to create the dictionary
            data['settings']['themes'][theme] = self.updateCurrentKeyDict()  # save or add the theme dict to disk
            data['settings']['current_theme'] = theme  # save the current theme name to disk
            saveFileDict = dict()
            saveFileDict['settings'] = data['settings']  # file should only have one key, 'settings', data has more
            filesystem.saveJson(saveFileDict, str(stylesheetAdminPath), indent=2, sort_keys=True)
            om2.MGlobal.displayInfo("Admin Save: All Themes Saved To Disk '{}'".format(stylesheetAdminPath))

    def createTheme(self):
        """ Adds a new Theme to the combo box

        Saves the data to the user preferences stylesheet.pref and sets combo box

        :return:
        """
        newThemeName = self.ui_createWindowPopup()
        if not newThemeName:
            om2.MGlobal.displayInfo("Theme creation cancelled")
            return
        self.skipComboChange = True  # skip the on combo update as no data yet
        self.themeBox.addItem(newThemeName)
        self.themeBox.model().sort(0)  # sorts alphabetically
        self.themeBox.setToText(newThemeName)
        # save the data
        self.serialize()  # saves to disk with current settings
        self.skipComboChange = False
        self.updateSheets()  # update all theme dicts

    def renameTheme(self):
        oldThemeName = self.themeBox.currentText()
        newThemeName = self.ui_renameWindowPopup()

        if newThemeName == "":
            return

        # rename and save the prefs dict
        data = self.prefInterface.preference.findSetting(InterfaceWidget.prefDataRelativePath, root=None)
        if data.isValid():
            data['settings']['themes'][newThemeName] = data['settings']['themes'].pop(oldThemeName)  # rename the key
            data['settings']['current_theme'] = newThemeName  # save the current theme name to disk
            data.save(indent=True, sort=True)  # dump format nicely
            om2.MGlobal.displayInfo("Success: Theme '{}' Renamed To {}".format(oldThemeName, newThemeName))

        # update the combo box
        self.skipComboChange = True  # skip the on combo update as no data yet
        self.themeBox.addItem(newThemeName)
        self.themeBox.model().sort(0)  # sorts alphabetically
        self.themeBox.setToText(newThemeName)
        self.themeBox.removeItemByText(oldThemeName)
        self.skipComboChange = False
        self.updateSheets()  # update all theme dicts

    def deleteTheme(self):
        okPressed = self.ui_deleteWindowPopup()
        if not okPressed:
            om2.MGlobal.displayInfo("Delete Cancelled")
            return
        currentTheme = self.themeBox.currentText()
        data = self.prefInterface.preference.findSetting(InterfaceWidget.prefDataRelativePath, root=None)
        if data.isValid():
            data['settings']['themes'].pop(currentTheme)  # delete the current theme dict
            # Combo Box current theme update
            self.themeBox.removeItemByText(currentTheme)
            self.themeBox.setIndex(0)
            newThemeName = self.themeBox.currentText()
            data['settings']['current_theme'] = newThemeName  # save the current theme name to disk
            data.save(indent=True)  # dump = format nicely
            # self.onThemeChanged()  # update widgets to first theme
            om2.MGlobal.displayInfo(
                "Success: Theme '{}' has been deleted and all themes have been saved".format(currentTheme))

    def connections(self):
        """ Connect Up The UI

        :return:
        """
        self.themeExampleBtn.clicked.connect(self.themeWindow.show)
        self.revertThemeBtn.clicked.connect(self.revertTheme)
        self.themeBox.currentIndexChanged.connect(self.onThemeChanged)  # combo updates
        self.adminSaveBtn.clicked.connect(self.adminSave)
        self.createNewThemeBtn.clicked.connect(self.createTheme)
        self.renameThemeBtn.clicked.connect(self.renameTheme)
        self.deleteThemeBtn.clicked.connect(self.deleteTheme)

        for widget in self.globalColorWidgetList:  # if global colors are changed
            widget.colorChanged.connect(partial(self.setGlobalColors, widget))  # also emits a linearColorFloat

    def revertTheme(self):
        """ Revert current theme

        :return:
        :rtype:
        """
        if self.ui_revertThemePopup():
            self.prefInterface.revertThemeToDefault(save=False)  # Saved when user presses save
            self.onThemeChanged()  # Refresh current theme


class ThemeSectionWidget(QtWidgets.QWidget):
    colorChanged = QtCore.Signal(tuple)

    def __init__(self, themeDict, parent=None):
        super(ThemeSectionWidget, self).__init__(parent=parent)
        self.gridLayout = elements.GridLayout(parent=parent, margins=(uic.SMLPAD, uic.TOPPAD, uic.SMLPAD, uic.BOTPAD),
                                             vSpacing=uic.SREG, hSpacing=uic.SVLRG)
        self.setLayout(self.gridLayout)
        self.buildSection(themeDict)

    def buildSection(self, themeDict):
        """Builds the UI colors and text box widgets from the current theme

        Automatically figures the type of widgets to build:

            Pixel Scale
            Color
            Icon
            Other (usually regular number, not px scale)

        :param themeDict: The theme dictionary, with all the keys and colors for the current theme
        :type themeDict: dict
        """
        self.clearLayout()

        row, col = 0, 0
        for i, key in enumerate(themeDict.keys()):
            col = i % 2
            if col == 0:
                row += 1
            # int pixel scale
            if stylesheet.valueType(themeDict[key]) == stylesheet.DPI_SCALE:
                textLabel = StyleTextWidget(themeKeyToName(key), key, parent=self,
                                            textType=StyleTextWidget.TYPE_DPISCALE)
                self.gridLayout.addWidget(textLabel, row, col, 1, 1)
                textLabel.setText(str(themeDict[key][1:]))
            # Color
            elif stylesheet.valueType(themeDict[key]) == stylesheet.COLOR:
                colorSrgbInt = colour.hexToRGB(themeDict[key])  # needs to be in int 255 srgb values
                colorSrgbFloat = colour.rgbIntToFloat(colorSrgbInt)
                colorLinearFloat = colour.convertColorSrgbToLinear(colorSrgbFloat)
                colWidget = cmdswidgets.MayaColorBtn(text=themeKeyToName(key), key=key, color=colorLinearFloat,
                                                     parent=self, colorWidth=100, labelRatio=65, btnRatio=35)
                colWidget.colorChanged.connect(self.colorChanged.emit)
                self.gridLayout.addWidget(colWidget, row, col, 1, 1)
            # Icon
            elif stylesheet.valueType(themeDict[key]) == stylesheet.ICON:
                textLabel = StyleTextWidget(themeKeyToName(key), key, parent=self,
                                            textType=StyleTextWidget.TYPE_ICON)

                self.gridLayout.addWidget(textLabel, row, col, 1, 1)
                textLabel.setText(str(themeDict[key][5:]))
            # other?
            else:
                textLabel = StyleTextWidget(themeKeyToName(key), key, parent=self)
                self.gridLayout.addWidget(textLabel, row, col, 1, 1)
                textLabel.setText(str(themeDict[key]))
        # set columns to be the same width, the Maya color widgets don't scale well though
        self.gridLayout.setColumnStretch(0, 1)
        self.gridLayout.setColumnStretch(1, 1)



    def clearLayout(self):
        """deletes all widgets of the current Color/Text layout
        """
        utils.clearLayout(self.gridLayout)

    def data(self):
        """ Iterates through the grid layout and returns a themeDict with the updated data.

        widget.data() is retrieved by the class.method:
            StyleTextWidget().keyHex()
            or
            MayaColorBtn.ColorCmdsWidget().keyHex()

        :return themeDict: A theme dictionary with the new values
        :rtype themeDict: dict
        """
        themeDict = {}

        for i in range(self.gridLayout.count()):
            widget = self.gridLayout.itemAt(i).widget()
            # update the dictionary for a single key value
            # for colors will be like "FRAMELESS_TITLELABEL_COLOR", and value is in hex "ffffff"
            # for string edits "BTN_PADDING" and value might be "30"
            themeDict.update(widget.data())  #

        return themeDict


class ThemeInputWidget(QtWidgets.QWidget):
    def __init__(self, key=None, parent=None):
        """ A generic input widget for the themes in preferences

        :param key: The stylesheet pref key eg. "FRAMELESS_TITLELABEL_COLOR"
        :param parent:
        """
        super(ThemeInputWidget, self).__init__(parent=parent)

        self.key = key

    def data(self):
        pass


class StyleTextWidget(ThemeInputWidget):
    """Builds a text style widget "label/lineEdit" usually from stylesheet keys

        Builds a qLabel and text box (qLineEdit) with:
            text "Title Fontsize"
            key "$TITLE_FONTSIZE"

        textType:
            TYPE_DEFAULT = 0
            TYPE_DPISCALE = 1
            TYPE_ICON = 2
    """
    TYPE_DEFAULT = 0
    TYPE_DPISCALE = 1
    TYPE_ICON = 2

    def __init__(self, text="", key=None, parent=None, textType=TYPE_DEFAULT):
        """Builds a text style widget "label/lineEdit" from stylesheet keys

        Builds a qLabel and text box (qLineEdit) with:
            text "Title Fontsize"
            key "$TITLE_FONTSIZE"

        textType:
            TYPE_DEFAULT = 0
            TYPE_DPISCALE = 1
            TYPE_ICON = 2

        :param text: The text title of the QLabel, a nice string version of the Key Eg. "Title Fontsize"
        :type text: str
        :param key: The key from the stylsheet theme Eg. "$TITLE_FONTSIZE"
        :type key: str
        :param parent: the parent widget
        :type parent: QtWidget
        :param textType: The type of widget to build or return TYPE_DEFAULT = 0, TYPE_DPISCALE = 1, TYPE_ICON = 2
        :type textType: int
        """
        super(StyleTextWidget, self).__init__(parent=parent, key=key)
        layout = elements.hBoxLayout(self)
        self.setLayout(layout)
        self.textEdit = elements.LineEdit("", parent=self, fixedWidth=100)
        self.label = QtWidgets.QLabel(parent=self, text=text)
        layout.addWidget(self.label, 65)
        layout.addWidget(self.textEdit, 35)
        self.textType = textType

    def text(self):
        """returns the label name"""
        return self.label.text()

    def data(self):
        """Returns the current values of the current widget depending on the textType:

            TYPE_DEFAULT = 0
            TYPE_DPISCALE = 1
            TYPE_ICON = 2

        :return widgetValue: the value of the widget as a int or str depending on the textType
        :rtype widgetValue: in/str
        """
        if self.textType == StyleTextWidget.TYPE_DEFAULT:
            return {self.key: int(self.textEdit.text())}
        elif self.textType == StyleTextWidget.TYPE_DPISCALE:
            return {self.key: "^{}".format(self.textEdit.text())}
        elif self.textType == StyleTextWidget.TYPE_ICON:
            return {self.key: "icon:{}".format(self.textEdit.text())}

    def __getattr__(self, item):
        """ Use StyleTextWidget like a LineEdit

        :param item:
        :return:
        """
        return getattr(self.textEdit, item)


def applyStyleSheet(stylesheet):
    from zoo.apps.toolpalette import run
    run.show().applyStyleSheet(stylesheet)
    preference.interface("core_interface").manualUpdate()



def globalColorList(themeDict):
    """Returns the global hex color list from the first color in each key of the given themeDict

    Used to set the "Overall Global Colors" in the UI

    :param themeDict: a themeDict the sheet from a single theme
    :type themeDict: dict
    :return colorListLinear: the list of colors in hex that match the COLOR_GROUP_LIST
    :rtype colorListLinear: list(str)
    """
    colorList = list()
    for colorGroup, value in sc.COLORGROUP_ODICT.items():
        stylesheetKeyList = sc.COLORGROUP_ODICT[colorGroup]
        if stylesheetKeyList:  # could be empty dict
            colorHex = themeDict[stylesheetKeyList[0]]  # color (Hex) from the first Stylesheet Key entry
            colorList.append(colorHex)
        else:  # there are no widgets
            colorList.append(uic.COLOR_ERROR)  # fluorescent green
    return colorList


def themeKeyToName(key):
    """Converts the Key name in caps with underscores to a nice title string:

        "$TITLE_FONTSIZE" is returned as "Title Fontsize"

    :param key: The title key from the theme dictionary Eg. "TITLE_FONTSIZE"
    :type key: str
    :return labelTitle: The title now lowercase and with Upperscase first letters Eg. "Title Fontsize"
    :rtype labelTitle: str
    """
    uppercaseText = key.replace("_", " ").replace("$", "").upper()
    return uppercaseText.lower().title()  # lowercase and title uppercase first letters


def divideThemeDictToSections(themeDict):
    """create the section dicts now with colors/values OrderedDict(OrderedDict()):

        sectionLabel([stylesheetKey, value])

    :param themeDict: a themeDict the sheet from a single theme, Stylesheet Keys and values
    :type themeDict: dict
    :return sectionKeyValue_odict: And ordered dict of an orderedDict sectionLabel([stylesheetKey, value])
    :rtype sectionKeyValue_odict: orderedDict(orderedDict)
    """
    # create the section dicts now
    copyThemeDict = dict(themeDict)
    sectionKeyValue_odict = collections.OrderedDict()
    # create the sectionKeyValue_odict
    for i, (sectionLabel, keyList) in enumerate(iter(sc.SECTION_ODICT.items())):
        keyValue_odict = collections.OrderedDict()
        for key in keyList:
            del copyThemeDict[key]
            keyValue_odict[key] = themeDict[key]
        sectionKeyValue_odict[sectionLabel] = keyValue_odict
    if copyThemeDict:  # then there are leftover keys, add them to the last list - otherSettingsDict
        for key in copyThemeDict:
            lastKey = next(reversed(sectionKeyValue_odict))  # last key should be the section "Other"
            sectionKeyValue_odict[lastKey][key] = themeDict[key]
        om2.MGlobal.displayWarning("Zoo Admin: Stylesheet's 'widgets.py' is missing the key/s {}".format(copyThemeDict))
    return sectionKeyValue_odict
