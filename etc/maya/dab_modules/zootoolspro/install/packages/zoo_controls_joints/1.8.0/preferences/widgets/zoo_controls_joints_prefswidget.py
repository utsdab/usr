import os

import maya.api.OpenMaya as om2

from Qt import QtWidgets

from zoo.libs.utils import filesystem
from zoo.apps.preferencesui import model
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt import uiconstants as uic

from zoo.preferences.core import preference
from zoo.apps.controls_joints import controlsjointsconstants as cc
from zoo.apps.controls_joints import controlsdirectories


class ZooControlsJointsPrefsWidget(model.SettingWidget):
    categoryTitle = "Controls Joints"  # The main title of the Model Asset preferences section and also side menu item

    def __init__(self, parent=None):
        """Builds the Controls Joints Section of the preferences window.

        :param parent: the parent widget
        :type parent: Qt.QtWidgets
        """
        super(ZooControlsJointsPrefsWidget, self).__init__(parent)
        # Model Asset Pref Object self.lsPrefsObj stores and saves all the .prefs json data
        self.prefsData = preference.findSetting(cc.RELATIVE_PREFS_FILE, None)
        # Check assets folders and updates if they don't exist
        self.prefsData = controlsdirectories.buildUpdateControlsJointsPrefs(self.prefsData)
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
        controlsJointsPath = self.prefsData["settings"][cc.PREFS_KEY_CONTROL_SHAPES]
        # Controls Joints Path -----------------------------------------
        toolTip = "The location of the Controls Joints. \n" \
                  "Copy your *.zooScene files along with their dependency folders into the root of this folder. "
        self.controlsJointsLbl = elements.Label("Control Shapes Folder", parent=self, toolTip=toolTip)
        self.controlsJointsTxt = elements.StringEdit(label="",
                                                     editText=controlsJointsPath,
                                                     toolTip=toolTip)
        toolTip = "Browse to change the Controls Joints folder."
        self.controlsJointsBrowseSetBtn = elements.styledButton("",
                                                            "browse",
                                                               toolTip=toolTip,
                                                               parent=self,
                                                               minWidth=uic.BTN_W_ICN_MED)
        toolTip = "Reset the Controls Controls Joints folder to it's default location."
        self.controlsJointsResetBtn = elements.styledButton("",
                                                        "refresh",
                                                           toolTip=toolTip,
                                                           parent=self,
                                                           minWidth=uic.BTN_W_ICN_MED)
        toolTip = "Explore, open the directory in your OS browser."
        self.ControlsJointsExploreBtn = elements.styledButton("",
                                                          "globe",
                                                             toolTip=toolTip,
                                                             parent=self,
                                                             minWidth=uic.BTN_W_ICN_MED)

    def uiLayout(self):
        """Adds all the widgets to layouts for the GUI"""
        mainLayout = elements.vBoxLayout(self,
                                         margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Controls Joints  Path Layout ------------------------------------
        controlsJointsPathLayout = elements.hBoxLayout()
        controlsJointsPathLayout.addWidget(self.controlsJointsBrowseSetBtn)
        controlsJointsPathLayout.addWidget(self.controlsJointsResetBtn)
        controlsJointsPathLayout.addWidget(self.ControlsJointsExploreBtn)
        # Path Grid Top Layout ----------------------------------------------
        pathGridLayout = elements.GridLayout(
            margins=(0, 0, 0, uic.SXLRG),
            columnMinWidth=(0, 120),
            columnMinWidthB=(2, 120))
        pathGridLayout.addWidget(self.controlsJointsLbl, 0, 0)
        pathGridLayout.addWidget(self.controlsJointsTxt, 0, 1)
        pathGridLayout.addLayout(controlsJointsPathLayout, 0, 2)
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

        :return controlsJointsDefaultPath: The full path of the userPreferences + assets directory + Controls Joints directory
        :rtype controlsJointsDefaultPath: str
        """
        userPrefsPath = str(preference.root("user_preferences"))
        assetsFolderPath = os.path.join(userPrefsPath, cc.ASSETS_FOLDER_NAME)
        controlsJointsDefaultPath = os.path.join(assetsFolderPath, cc.SHAPES_FOLDER_NAME)
        return controlsJointsDefaultPath

    def setControlsJointsPathDefault(self):
        """Sets the UI widget path text to the default Controls Joints path"""
        controlsJointsDefaultPath = self.getDefaultFolders()[1]
        self.controlsJointsTxt.setText(controlsJointsDefaultPath)

    def browseChangeControlsJointsFolder(self):
        """Browse to change/set the Controls Joints Folder"""
        directoryPath = self.controlsJointsTxt.text()
        if not os.path.isdir(directoryPath):  # if dir doesn't exist set to home directory
            directoryPath = os.environ['HOME']
        newDirPath = QtWidgets.QFileDialog.getExistingDirectory(self, "Set the Controls Joints folder", directoryPath)
        if newDirPath:
            self.controlsJointsTxt.setText(newDirPath)

    def exploreControlsJointsFolder(self):
        """Opens an os window for browsing files on disk in the users operating system"""
        filesystem.openDirectory(self.controlsJointsTxt.text())
        om2.MGlobal.displayInfo("OS window opened to the `Controls Joints` folder location")

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
        self.prefsData["settings"][cc.PREFS_KEY_CONTROL_SHAPES] = self.controlsJointsTxt.text()
        path = self.prefsData.save(indent=True)  # save and format nicely
        om2.MGlobal.displayInfo("Success: Model Asset preferences Saved To Disk '{}'".format(path))

    def revert(self):
        """Reverts to the previous settings, resets the GUI to the previously saved settings

        Automatically connected to the preferences window revert button via model.SettingWidget
        """
        self.controlsJointsTxt.setText(self.prefsData["settings"][cc.PREFS_KEY_CONTROL_SHAPES])

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
        self.controlsJointsResetBtn.clicked.connect(self.setControlsJointsPathDefault)
        # browse paths small buttons
        self.controlsJointsBrowseSetBtn.clicked.connect(self.browseChangeControlsJointsFolder)
        # explore paths small buttons
        self.ControlsJointsExploreBtn.clicked.connect(self.exploreControlsJointsFolder)
