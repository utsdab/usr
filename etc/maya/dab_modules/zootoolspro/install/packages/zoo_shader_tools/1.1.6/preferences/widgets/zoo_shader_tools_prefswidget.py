import os

import maya.api.OpenMaya as om2

from Qt import QtWidgets

from zoo.libs.utils import filesystem
from zoo.apps.preferencesui import model
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt import uiconstants as uic

from zoo.preferences.core import preference
from zoo.apps.shader_tools import shaderconstants as sc
from zoo.apps.shader_tools import shaderdirectories


class ZooShaderToolsPrefsWidget(model.SettingWidget):
    categoryTitle = "Shader Tools"  # The main title of the Camera Tools preferences section and also side menu item

    def __init__(self, parent=None):
        """Builds the Camera Tools Section of the preferences window.

        :param parent: the parent widget
        :type parent: Qt.QtWidgets
        """
        super(ZooShaderToolsPrefsWidget, self).__init__(parent)
        # Camera Tools Pref Object self.lsPrefsObj stores and saves all the .prefs json data
        self.prefsData = preference.findSetting(sc.RELATIVE_PREFS_FILE, None)
        # Check assets folders and updates if they don't exist
        self.prefsData = shaderdirectories.buildUpdateShaderAssetPrefs(self.prefsData)
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
        shaderPath = self.prefsData["settings"][sc.PREFS_KEY_SHADERPRESETS]
        # Camera Tools Path -----------------------------------------
        toolTip = "The location of the Shader Presets Folder. \n" \
                  "Place shader presets here or change the folder to a path with .zooScene shader files.  \n" \
                  "Supports .jpg and .png"
        self.shaderPresetLbl = elements.Label("Shader Presets Folder", parent=self, toolTip=toolTip)
        self.shaderPresetTxt = elements.StringEdit(label="",
                                                   editText=shaderPath,
                                                   toolTip=toolTip)
        toolTip = "Browse to change the Shader Presets folder."
        self.shaderBrowseSetBtn = elements.styledButton("",
                                                        "browse",
                                                        toolTip=toolTip,
                                                        parent=self,
                                                        minWidth=uic.BTN_W_ICN_MED)
        toolTip = "Reset the Shader Preset folder to it's default location."
        self.shaderPresetResetBtn = elements.styledButton("",
                                                          "refresh",
                                                          toolTip=toolTip,
                                                          parent=self,
                                                          minWidth=uic.BTN_W_ICN_MED)
        toolTip = "Explore, open the directory in your OS browser."
        self.shaderPresetExploreBtn = elements.styledButton("",
                                                            "globe",
                                                            toolTip=toolTip,
                                                            parent=self,
                                                            minWidth=uic.BTN_W_ICN_MED)

    def uiLayout(self):
        """Adds all the widgets to layouts for the GUI"""
        mainLayout = elements.vBoxLayout(self,
                                         margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Shader Tools Path Layout ------------------------------------
        shaderToolsPathLayout = elements.hBoxLayout()
        shaderToolsPathLayout.addWidget(self.shaderBrowseSetBtn)
        shaderToolsPathLayout.addWidget(self.shaderPresetResetBtn)
        shaderToolsPathLayout.addWidget(self.shaderPresetExploreBtn)
        # Path Grid Top Layout ----------------------------------------------
        pathGridLayout = elements.GridLayout(
            margins=(0, 0, 0, uic.SXLRG),
            columnMinWidth=(0, 120),
            columnMinWidthB=(2, 120))
        pathGridLayout.addWidget(self.shaderPresetLbl, 0, 0)
        pathGridLayout.addWidget(self.shaderPresetTxt, 0, 1)
        pathGridLayout.addLayout(shaderToolsPathLayout, 0, 2)
        # Add to Main Layout  -----------------------------------
        mainLayout.addLayout(pathGridLayout)
        mainLayout.addStretch(1)

    # -------------------
    # LOGIC
    # -------------------

    def getDefaultFolders(self):
        """Returns the default folder paths as created from the global user preferences directory

        userPreferences path + /assets/ + image_planes:

            userPath/zoo_preferences/assets/image_planes

        :return imagePlaneDefaultPath: The full path of the userPreferences + assets directory + imageplane directory
        :rtype imagePlaneDefaultPath: str
        """
        userPrefsPath = str(preference.root("user_preferences"))
        assetsFolderPath = os.path.join(userPrefsPath, sc.ASSETS_FOLDER_NAME)
        shaderPresetsDefaultPath = os.path.join(assetsFolderPath, sc.SHADERPRESETS_FOLDER_NAME)
        return shaderPresetsDefaultPath

    def setShaderPresetPathDefault(self):
        """Sets the UI widget path text to the default Image Plane path"""
        shaderPresetsDefaultPath = self.getDefaultFolders()[1]
        self.shaderPresetTxt.setText(shaderPresetsDefaultPath)

    def browseChangeShaderPresetFolder(self):
        """Browse to change/set the Camera Tools Folder"""
        directoryPath = self.shaderPresetTxt.text()
        if not os.path.isdir(directoryPath):  # if dir doesn't exist set to home directory
            directoryPath = os.environ['HOME']
        newDirPath = QtWidgets.QFileDialog.getExistingDirectory(self, "Set the Image Plane folder", directoryPath)
        if newDirPath:
            self.shaderPresetTxt.setText(newDirPath)

    def exploreShaderPresetsFolder(self):
        """Opens an os window for browsing files on disk in the users operating system"""
        filesystem.openDirectory(self.shaderPresetTxt.text())
        om2.MGlobal.displayInfo("OS window opened to the `Image Plane` folder location")

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
        self.prefsData["settings"][sc.PREFS_KEY_SHADERPRESETS] = self.shaderPresetTxt.text()
        path = self.prefsData.save(indent=True)  # save and format nicely
        om2.MGlobal.displayInfo("Success: Camera Tools preferences Saved To Disk '{}'".format(path))

    def revert(self):
        """Reverts to the previous settings, resets the GUI to the previously saved settings

        Automatically connected to the preferences window revert button via model.SettingWidget
        """
        self.shaderPresetTxt.setText(self.prefsData["settings"][sc.PREFS_KEY_SHADERPRESETS])

    def adminSave(self):
        """Method for admin saving internally to Zoo Tools Pro, not connected
        """
        pass

    # -------------------
    # CONNECTIONS
    # -------------------

    def uiConnections(self):
        """Setup the custom connections for the Shader Tools Preferences GUI

        # Save, Apply buttons are automatically connected to the self.serialize() methods
        # Reset Button is automatically connected to the self.revert() method
        """
        # reset paths small buttons
        self.shaderPresetResetBtn.clicked.connect(self.setShaderPresetPathDefault)
        # browse paths small buttons
        self.shaderBrowseSetBtn.clicked.connect(self.browseChangeShaderPresetFolder)
        # explore paths small buttons
        self.shaderPresetExploreBtn.clicked.connect(self.exploreShaderPresetsFolder)
