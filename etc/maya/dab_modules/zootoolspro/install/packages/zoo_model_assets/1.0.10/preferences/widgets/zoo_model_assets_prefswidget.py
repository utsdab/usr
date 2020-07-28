import os

import maya.api.OpenMaya as om2

from Qt import QtWidgets

from zoo.libs.utils import filesystem
from zoo.apps.preferencesui import model
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt import uiconstants as uic

from zoo.preferences.core import preference
from zoo.apps.model_assets import assetconstants as ac
from zoo.apps.model_assets import assetdirectories


class ZooModelAssetsPrefsWidget(model.SettingWidget):
    categoryTitle = "Model Assets"  # The main title of the Model Asset preferences section and also side menu item

    def __init__(self, parent=None):
        """Builds the Model Asset Section of the preferences window.

        :param parent: the parent widget
        :type parent: Qt.QtWidgets
        """
        super(ZooModelAssetsPrefsWidget, self).__init__(parent)
        # Model Asset Pref Object self.lsPrefsObj stores and saves all the .prefs json data
        self.prefsData = preference.findSetting(ac.RELATIVE_PREFS_FILE, None)
        # Check assets folders and updates if they don't exist
        self.prefsData = assetdirectories.buildUpdateModelAssetPrefs(self.prefsData)
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
        modelAssetsPath = self.prefsData["settings"][ac.PREFS_KEY_MODEL_ASSETS]
        # Model Assets Path -----------------------------------------
        toolTip = "The location of the Model Assets. \n" \
                  "Copy your *.zooScene files along with their dependency folders into the root of this folder. "
        self.modelAssetsLbl = elements.Label("Model Assets Folder", parent=self, toolTip=toolTip)
        self.modelAssetsTxt = elements.StringEdit(label="",
                                                  editText=modelAssetsPath,
                                                  toolTip=toolTip)
        toolTip = "Browse to change the Model Assets folder."
        self.modelAssetsBrowseSetBtn = elements.styledButton("",
                                                            "browse",
                                                               toolTip=toolTip,
                                                               parent=self,
                                                               minWidth=uic.BTN_W_ICN_MED)
        toolTip = "Reset the Model Assets folder to it's default location."
        self.modelAssetsResetBtn = elements.styledButton("",
                                                        "refresh",
                                                           toolTip=toolTip,
                                                           parent=self,
                                                           minWidth=uic.BTN_W_ICN_MED)
        toolTip = "Explore, open the directory in your OS browser."
        self.modelAssetsExploreBtn = elements.styledButton("",
                                                          "globe",
                                                             toolTip=toolTip,
                                                             parent=self,
                                                             minWidth=uic.BTN_W_ICN_MED)

    def uiLayout(self):
        """Adds all the widgets to layouts for the GUI"""
        mainLayout = elements.vBoxLayout(self,
                                         margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Model Assets  Path Layout ------------------------------------
        modelAssetsPathLayout = elements.hBoxLayout()
        modelAssetsPathLayout.addWidget(self.modelAssetsBrowseSetBtn)
        modelAssetsPathLayout.addWidget(self.modelAssetsResetBtn)
        modelAssetsPathLayout.addWidget(self.modelAssetsExploreBtn)
        # Path Grid Top Layout ----------------------------------------------
        pathGridLayout = elements.GridLayout(
            margins=(0, 0, 0, uic.SXLRG),
            columnMinWidth=(0, 120),
            columnMinWidthB=(2, 120))
        pathGridLayout.addWidget(self.modelAssetsLbl, 0, 0)
        pathGridLayout.addWidget(self.modelAssetsTxt, 0, 1)
        pathGridLayout.addLayout(modelAssetsPathLayout, 0, 2)
        # Add to Main Layout  -----------------------------------
        mainLayout.addLayout(pathGridLayout)
        mainLayout.addStretch(1)

    # -------------------
    # LOGIC
    # -------------------

    def getDefaultFolders(self):
        """Returns the default folder paths as created from the global user preferences directory

        userPreferences path + /assets/ + model_asset_folderNames:

            userPath/zoo_preferences/assets/model_assets

        :return modelAssetsDefaultPath: The full path of the userPreferences + assets directory + model assets directory
        :rtype modelAssetsDefaultPath: str
        """
        userPrefsPath = str(preference.root("user_preferences"))
        assetsFolderPath = os.path.join(userPrefsPath, ac.ASSETS_FOLDER_NAME)
        modelAssetsDefaultPath = os.path.join(assetsFolderPath, ac.MODEL_FOLDER_NAME)
        return modelAssetsDefaultPath

    def setModelAssetsPathDefault(self):
        """Sets the UI widget path text to the default Model Assets path"""
        modelAssetsDefaultPath = self.getDefaultFolders()[1]
        self.modelAssetsTxt.setText(modelAssetsDefaultPath)

    def browseChangeModelAssetsFolder(self):
        """Browse to change/set the Model Assets Folder"""
        directoryPath = self.modelAssetsTxt.text()
        if not os.path.isdir(directoryPath):  # if dir doesn't exist set to home directory
            directoryPath = os.environ['HOME']
        newDirPath = QtWidgets.QFileDialog.getExistingDirectory(self, "Set the Model Assets folder", directoryPath)
        if newDirPath:
            self.modelAssetsTxt.setText(newDirPath)

    def exploreModelAssetsFolder(self):
        """Opens an os window for browsing files on disk in the users operating system"""
        filesystem.openDirectory(self.modelAssetsTxt.text())
        om2.MGlobal.displayInfo("OS window opened to the `Model Assets` folder location")

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
        self.prefsData["settings"][ac.PREFS_KEY_MODEL_ASSETS] = self.modelAssetsTxt.text()
        path = self.prefsData.save(indent=True)  # save and format nicely
        om2.MGlobal.displayInfo("Success: Model Asset preferences Saved To Disk '{}'".format(path))

    def revert(self):
        """Reverts to the previous settings, resets the GUI to the previously saved settings

        Automatically connected to the preferences window revert button via model.SettingWidget
        """
        self.modelAssetsTxt.setText(self.prefsData["settings"][ac.PREFS_KEY_MODEL_ASSETS])

    def adminSave(self):
        """Method for admin saving internally to Zoo Tools Pro, not connected
        """
        pass

    # -------------------
    # CONNECTIONS
    # -------------------

    def uiConnections(self):
        """Setup the custom connections for the Model Asset Preferences GUI

        # Save, Apply buttons are automatically connected to the self.serialize() methods
        # Reset Button is automatically connected to the self.revert() method
        """
        # reset paths small buttons
        self.modelAssetsResetBtn.clicked.connect(self.setModelAssetsPathDefault)
        # browse paths small buttons
        self.modelAssetsBrowseSetBtn.clicked.connect(self.browseChangeModelAssetsFolder)
        # explore paths small buttons
        self.modelAssetsExploreBtn.clicked.connect(self.exploreModelAssetsFolder)
