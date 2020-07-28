import os

import maya.api.OpenMaya as om2

from Qt import QtWidgets

from zoo.libs.utils import filesystem
from zoo.libs.pyqt import utils
from zoo.apps.toolsetsui import toolsetui
from zoo.apps.preferencesui import model
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt import uiconstants as uic

from zoo.preferences.core import preference
from zoo.apps.light_suite import lightconstants as lc
from zoo.apps.light_suite import assetdirectories

class ZooLightSuitePrefsWidget(model.SettingWidget):
    categoryTitle = "Light Suite"  # The main title of the Light Suite preferences section and also side menu item

    def __init__(self, parent=None):
        """Builds the Light Suite Section of the preferences window.

        :param parent: the parent widget
        :type parent: Qt.QtWidgets
        """
        super(ZooLightSuitePrefsWidget, self).__init__(parent)
        # Light Suite Pref Object self.lsPrefsObj stores and saves all the .prefs json data
        self.prefsData = preference.findSetting(lc.RELATIVE_PREFS_FILE, None)
        # Check assets folders and updates if they don't exist
        self.prefsData = assetdirectories.buildUpdateLightPrefs(self.prefsData)
        self.uiWidgets()  # Builds the widgets
        self.uiLayout()  # Adds widgets to the layouts
        # Save, Apply buttons are automatically connected to the self.serialize() method
        # Reset Button is automatically connected to the self.revert() method
        self.uiConnections()

    # -------------------
    # WIDGETS LAYOUT
    # -------------------

    def uiWidgets(self):
        """Builds all the widgets needed in the GUI"""
        # Retrieve data from user's .prefs json -------------------------
        presetPath = self.prefsData["settings"][lc.PREFS_KEY_PRESETS]
        iblPath = self.prefsData["settings"][lc.PREFS_KEY_IBL]
        exrState = self.prefsData["settings"][lc.PREFS_KEY_EXR]
        hdrState = self.prefsData["settings"][lc.PREFS_KEY_HDR]
        tifState = self.prefsData["settings"][lc.PREFS_KEY_TIF]
        texState = self.prefsData["settings"][lc.PREFS_KEY_TEX]
        txState = self.prefsData["settings"][lc.PREFS_KEY_TX]
        # Light Presets Path -----------------------------------------
        toolTip = "The location of the Light Presets. \n" \
                  "Copy your *.zooScene files along with their dependency folders into the root of this folder. "
        self.lightPresetLbl = elements.Label("Light Presets Folder", parent=self, toolTip=toolTip)
        self.lightPresetTxt = elements.StringEdit(label="",
                                                  editText=presetPath,
                                                  toolTip=toolTip)
        toolTip = "Browse to change the Light Presets folder."
        self.lightPresetBrowseSetBtn = elements.styledButton("",
                                                            "browse",
                                                               toolTip=toolTip,
                                                               parent=self,
                                                               minWidth=uic.BTN_W_ICN_MED)
        toolTip = "Reset the Light Preset folder to it's default location."
        self.lightPresetResetBtn = elements.styledButton("",
                                                        "refresh",
                                                           toolTip=toolTip,
                                                           parent=self,
                                                           minWidth=uic.BTN_W_ICN_MED)
        toolTip = "Explore, open the directory in your OS browser."
        self.lightPresetExploreBtn = elements.styledButton("",
                                                          "globe",
                                                             toolTip=toolTip,
                                                             parent=self,
                                                             minWidth=uic.BTN_W_ICN_MED)
        # IBL Images Path -----------------------------------------
        toolTip = "The location of the IBL Skydome Images. \n" \
                  "Copy/move your HDR image files and optional dependency folders to the root of this directory. "
        self.iblImagePathLbl = elements.Label("IBL Skydomes Folder", parent=self, toolTip=toolTip)
        self.iblImagePathTxt = elements.StringEdit(label="",
                                                   editText=iblPath,
                                                   toolTip=toolTip)
        toolTip = "Browse to change the IBL Skydome folder."
        self.iblImageBrowseSetBtn = elements.styledButton("",
                                                         "browse",
                                                            toolTip=toolTip,
                                                            parent=self,
                                                            minWidth=uic.BTN_W_ICN_MED)
        toolTip = "Reset the IBL Skydome folder to it's default location."
        self.iblImageResetBtn = elements.styledButton("",
                                                     "refresh",
                                                        toolTip=toolTip,
                                                        parent=self,
                                                        minWidth=uic.BTN_W_ICN_MED)
        toolTip = "Explore, open the directory in your OS browser."
        self.iblImageExploreBtn = elements.styledButton("",
                                                       "globe",
                                                          toolTip=toolTip,
                                                          parent=self,
                                                          minWidth=uic.BTN_W_ICN_MED)
        # HDR Image Type Vis -----------------------------------------
        toolTip = "Checked image types will be viewable in your Skydome IBL windows.\n" \
                  "It's recommended to leave .tex and .tx off to avoid doubled textures. Renderman converts \n" \
                  "all textures to .tx and Arnold converts to .tex behind the scenes, but in most cases\n " \
                  "you do not need to see those file types. The renderers will automatically convert and\n" \
                  "manage the tx/tex textures for you."
        self.imageTypesTitleLabel = elements.Label(text="HDR Image Types", parent=self, upper=True, toolTip=toolTip)
        utils.setStylesheetObjectName(self.imageTypesTitleLabel, "HeaderLabel")  # set title stylesheet
        self.tifChkbx = elements.CheckBox(label=".TIF(F)",
                                          checked=tifState,
                                          parent=self,
                                          toolTip=toolTip)
        self.hdrChkbx = elements.CheckBox(label=".HDR(I)",
                                          checked=hdrState,
                                          parent=self,
                                          toolTip=toolTip)
        self.exrChkbx = elements.CheckBox(label=".EXR",
                                          checked=exrState,
                                          parent=self,
                                          toolTip=toolTip)
        self.texChkbx = elements.CheckBox(label=".TEX (Renderman)",
                                          checked=texState,
                                          parent=self,
                                          toolTip=toolTip)
        self.txChkbx = elements.CheckBox(label=".TX (Arnold)",
                                         checked=txState,
                                         parent=self,
                                         toolTip=toolTip)

    def uiLayout(self):
        """Adds all the widgets to layouts for the GUI"""
        mainLayout = elements.vBoxLayout(self,
                                                              margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                                              spacing=uic.SREG)

        # Light Preset Path Layout ------------------------------------
        lightPresetPathLayout = elements.hBoxLayout()
        lightPresetPathLayout.addWidget(self.lightPresetBrowseSetBtn)
        lightPresetPathLayout.addWidget(self.lightPresetResetBtn)
        lightPresetPathLayout.addWidget(self.lightPresetExploreBtn)
        # Light Preset Path Layout ------------------------------------
        iblImagePathLayout = elements.hBoxLayout()
        iblImagePathLayout.addWidget(self.iblImageBrowseSetBtn)
        iblImagePathLayout.addWidget(self.iblImageResetBtn)
        iblImagePathLayout.addWidget(self.iblImageExploreBtn)
        # Path Grid Top Layout ----------------------------------------------
        pathGridLayout = elements.GridLayout(
                                             margins=(0, 0, 0, uic.SXLRG),
                                             columnMinWidth=(0, 120),
                                             columnMinWidthB=(2, 120))
        pathGridLayout.addWidget(self.lightPresetLbl, 0, 0)
        pathGridLayout.addWidget(self.lightPresetTxt, 0, 1)
        pathGridLayout.addLayout(lightPresetPathLayout, 0, 2)
        pathGridLayout.addWidget(self.iblImagePathLbl, 1, 0)
        pathGridLayout.addWidget(self.iblImagePathTxt, 1, 1)
        pathGridLayout.addLayout(iblImagePathLayout, 1, 2)
        # Image Checkboxes Layout ------------------------------------
        imageCheckboxLayout = elements.hBoxLayout(margins=(0, uic.SVLRG, 0, 0))
        imageCheckboxLayout.addWidget(self.tifChkbx)
        imageCheckboxLayout.addWidget(self.hdrChkbx)
        imageCheckboxLayout.addWidget(self.exrChkbx)
        imageCheckboxLayout.addWidget(self.txChkbx)
        imageCheckboxLayout.addWidget(self.texChkbx)
        # Add to Main Layout  -----------------------------------
        mainLayout.addLayout(pathGridLayout)
        mainLayout.addWidget(self.imageTypesTitleLabel)
        mainLayout.addLayout(imageCheckboxLayout)
        mainLayout.addStretch(1)

    # -------------------
    # CHANGE PREFERENCES UPDATE OTHER WINDOWS - GLOBAL TOOL SETS
    # -------------------

    def global_changeRenderer(self):
        """Updates all GUIs with the current renderer"""
        toolsets = toolsetui.toolsets(attr="global_receiveRendererChange")
        for tool in toolsets:
            tool.global_receiveRendererChange(self.rendererCombo.currentText())

    def global_receiveRendererChange(self, renderer):
        """Receives from other GUIs, changes the renderer when it is changed

        TO DO currently not in use"""
        index = lc.RENDERER_LIST.index(renderer)
        self.rendererCombo.setCurrentIndex(index)

    def global_changePresetPath(self):
        """Changes the light preset path on all toolsets with the method refreshPresetQuickList()

        TODO: create a receive method to catch from other windows
        """
        toolsets = toolsetui.toolsets(attr="refreshPresetQuickList")
        for tool in toolsets:
            tool.refreshPresetQuickList()

    def global_changeIblSkydomePath(self):
        """Changes the ibl skydome path on all toolsets with the method refreshIblQuickList()

        TODO: create a receive method to catch from other windows
        """
        toolsets = toolsetui.toolsets(attr="refreshIblQuickList")
        for tool in toolsets:
            tool.refreshIblQuickList()

    # -------------------
    # LOGIC
    # -------------------

    def getDefaultFolders(self):
        """Returns the default folder paths as created from the global user preferences directory

        userPreferences path + /assets/ + light_suite_folderNames:

            userPath/zoo_preferences/assets/light_suite_ibl_skydomes
            userPath/zoo_preferences/assets/light_suite_light_presets

        :return iblDefaultPath: The full path of the userPreferences + assets directory + ibl directory
        :rtype iblDefaultPath: str
        :return presetDefaultPath: The full path of the userPreferences + assets directory + light presets directory
        :rtype presetDefaultPath: str
        """
        userPrefsPath = str(preference.root("user_preferences"))
        assetsFolderPath = os.path.join(userPrefsPath, lc.ASSETS_FOLDER_NAME)
        iblDefaultPath = os.path.join(assetsFolderPath, lc.IBL_SKYDOME_FOLDER_NAME)
        presetDefaultPath = os.path.join(assetsFolderPath, lc.LIGHT_PRESET_FOLDER_NAME)
        return iblDefaultPath, presetDefaultPath

    def setLightPresetPathDefault(self):
        """Sets the UI widget path text to the default Light Presets path"""
        presetDefaultPath = self.getDefaultFolders()[1]
        self.lightPresetTxt.setText(presetDefaultPath)

    def setIblPathDefault(self):
        """Sets the UI widget path text to the default IBL Skydome path"""
        iblDefaultPath = self.getDefaultFolders()[0]
        self.iblImagePathTxt.setText(iblDefaultPath)

    def browseChangeIblSkydomeFolder(self):
        """Browse to change/set the IBL Skydome Folder"""
        directoryPath = self.iblImagePathTxt.text()
        if not os.path.isdir(directoryPath):  # if dir doesn't exist set to home directory
            directoryPath = os.environ['HOME']
        newDirPath = QtWidgets.QFileDialog.getExistingDirectory(self, "Set the IBL Skydome folder", directoryPath)
        if newDirPath:
            self.iblImagePathTxt.setText(newDirPath)

    def browseChangeLightPresetFolder(self):
        """Browse to change/set the Light Preset Folder"""
        directoryPath = self.lightPresetTxt.text()
        if not os.path.isdir(directoryPath):  # if dir doesn't exist set to home directory
            directoryPath = os.environ['HOME']
        newDirPath = QtWidgets.QFileDialog.getExistingDirectory(self, "Set the Light Preset folder", directoryPath)
        if newDirPath:
            self.lightPresetTxt.setText(newDirPath)

    def exploreIblSkydomeFolder(self):
        """Opens an os window for browsing files on disk in the users operating system"""
        filesystem.openDirectory(self.iblImagePathTxt.text())
        om2.MGlobal.displayInfo("OS window opened to the `Ibl Skydome` folder location")

    def exploreLightPresetFolder(self):
        """Opens an os window for browsing files on disk in the users operating system"""
        filesystem.openDirectory(self.lightPresetTxt.text())
        om2.MGlobal.displayInfo("OS window opened to the `Zoo Light Presets` folder location")

    # -------------------
    # SAVE, APPLY, RESET
    # -------------------

    def serialize(self):
        """ Save the current settings to the preference file, used for both Apply and Save buttons

        Automatically connected to the preferences window buttons via model.SettingWidget
        """
        if not self.prefsData.isValid():
            om2.MGlobal.displayError("The preferences object is not valid")
            return
        self.prefsData["settings"][lc.PREFS_KEY_PRESETS] = self.lightPresetTxt.text()
        self.prefsData["settings"][lc.PREFS_KEY_IBL] = self.iblImagePathTxt.text()
        self.prefsData["settings"][lc.PREFS_KEY_TIF] = self.tifChkbx.isChecked()
        self.prefsData["settings"][lc.PREFS_KEY_HDR] = self.hdrChkbx.isChecked()
        self.prefsData["settings"][lc.PREFS_KEY_EXR] = self.exrChkbx.isChecked()
        self.prefsData["settings"][lc.PREFS_KEY_TX] = self.txChkbx.isChecked()
        self.prefsData["settings"][lc.PREFS_KEY_TEX] = self.texChkbx.isChecked()
        path = self.prefsData.save(indent=True)  # save and format nicely
        om2.MGlobal.displayInfo("Success: Light Suite preferences Saved To Disk '{}'".format(path))
        self.global_changeIblSkydomePath()
        self.global_changePresetPath()

    def revert(self):
        """Reverts to the previous settings, resets the GUI to the previously saved settings

        Automatically connected to the preferences window revert button via model.SettingWidget
        """
        self.lightPresetTxt.setText(self.prefsData["settings"][lc.PREFS_KEY_PRESETS])
        self.iblImagePathTxt.setText(self.prefsData["settings"][lc.PREFS_KEY_IBL])
        self.tifChkbx.setChecked(self.prefsData["settings"][lc.PREFS_KEY_TIF])
        self.hdrChkbx.setChecked(self.prefsData["settings"][lc.PREFS_KEY_HDR])
        self.exrChkbx.setChecked(self.prefsData["settings"][lc.PREFS_KEY_EXR])
        self.txChkbx.setChecked(self.prefsData["settings"][lc.PREFS_KEY_TX])
        self.texChkbx.setChecked(self.prefsData["settings"][lc.PREFS_KEY_TEX])

    def adminSave(self):
        """Method for admin saving internally to Zoo Tools Pro, not connected
        """
        pass

    # -------------------
    # CONNECTIONS
    # -------------------

    def uiConnections(self):
        """Setup the custom connections for the Light Suite Preferences GUI

        # Save, Apply buttons are automatically connected to the self.serialize() methods
        # Reset Button is automatically connected to the self.revert() method
        """
        # reset paths small buttons
        self.lightPresetResetBtn.clicked.connect(self.setLightPresetPathDefault)
        self.iblImageResetBtn.clicked.connect(self.setIblPathDefault)
        # browse paths small buttons
        self.iblImageBrowseSetBtn.clicked.connect(self.browseChangeIblSkydomeFolder)
        self.lightPresetBrowseSetBtn.clicked.connect(self.browseChangeLightPresetFolder)
        # explore paths small buttons
        self.iblImageExploreBtn.clicked.connect(self.exploreIblSkydomeFolder)
        self.lightPresetExploreBtn.clicked.connect(self.exploreLightPresetFolder)

