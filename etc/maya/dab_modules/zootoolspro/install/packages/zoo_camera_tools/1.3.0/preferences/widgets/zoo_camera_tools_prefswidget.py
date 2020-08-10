import os

import maya.api.OpenMaya as om2

from Qt import QtWidgets

from zoo.libs.utils import filesystem
from zoo.apps.preferencesui import model
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt import uiconstants as uic

from zoo.preferences.core import preference
from zoo.apps.camera_tools import cameraconstants as cc
from zoo.apps.camera_tools import cameradirectories


class ZooCameraToolsPrefsWidget(model.SettingWidget):
    categoryTitle = "Camera Tools"  # The main title of the Camera Tools preferences section and also side menu item

    def __init__(self, parent=None):
        """Builds the Camera Tools Section of the preferences window.

        :param parent: the parent widget
        :type parent: Qt.QtWidgets
        """
        super(ZooCameraToolsPrefsWidget, self).__init__(parent)
        # Camera Tools Pref Object self.lsPrefsObj stores and saves all the .prefs json data
        self.prefsData = preference.findSetting(cc.RELATIVE_PREFS_FILE, None)
        # Check assets folders and updates if they don't exist
        self.prefsData = cameradirectories.buildUpdateCameraAssetPrefs(self.prefsData)
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
        imagePlanePath = self.prefsData["settings"][cc.PREFS_KEY_IMAGEPLANE]
        # Camera Tools Path -----------------------------------------
        toolTip = "The location of the Image Plane Folder. \n" \
                  "Plane image planes here or change the folder to a path with images.  Supports .jpg and .png"
        self.imagePlaneLbl = elements.Label("Image Plane Folder", parent=self, toolTip=toolTip)
        self.imagePlaneTxt = elements.StringEdit(label="",
                                                  editText=imagePlanePath,
                                                  toolTip=toolTip)
        toolTip = "Browse to change the Image Plane folder."
        self.imagePlaneBrowseSetBtn = elements.styledButton("",
                                                            "browse",
                                                            toolTip=toolTip,
                                                            parent=self,
                                                            minWidth=uic.BTN_W_ICN_MED)
        toolTip = "Reset the Image Plane folder to it's default location."
        self.imagePlaneResetBtn = elements.styledButton("",
                                                        "refresh",
                                                        toolTip=toolTip,
                                                        parent=self,
                                                        minWidth=uic.BTN_W_ICN_MED)
        toolTip = "Explore, open the directory in your OS browser."
        self.imagePlaneExploreBtn = elements.styledButton("",
                                                          "globe",
                                                          toolTip=toolTip,
                                                          parent=self,
                                                          minWidth=uic.BTN_W_ICN_MED)

    def uiLayout(self):
        """Adds all the widgets to layouts for the GUI"""
        mainLayout = elements.vBoxLayout(self,
                                         margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Camera Tools  Path Layout ------------------------------------
        imagePlanePathLayout = elements.hBoxLayout()
        imagePlanePathLayout.addWidget(self.imagePlaneBrowseSetBtn)
        imagePlanePathLayout.addWidget(self.imagePlaneResetBtn)
        imagePlanePathLayout.addWidget(self.imagePlaneExploreBtn)
        # Path Grid Top Layout ----------------------------------------------
        pathGridLayout = elements.GridLayout(
            margins=(0, 0, 0, uic.SXLRG),
            columnMinWidth=(0, 120),
            columnMinWidthB=(2, 120))
        pathGridLayout.addWidget(self.imagePlaneLbl, 0, 0)
        pathGridLayout.addWidget(self.imagePlaneTxt, 0, 1)
        pathGridLayout.addLayout(imagePlanePathLayout, 0, 2)
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
        assetsFolderPath = os.path.join(userPrefsPath, cc.ASSETS_FOLDER_NAME)
        imagePlaneDefaultPath = os.path.join(assetsFolderPath, cc.IMAGEPLANE_FOLDER_NAME)
        return imagePlaneDefaultPath

    def setImagePlanePathDefault(self):
        """Sets the UI widget path text to the default Image Plane path"""
        imagePlaneDefaultPath = self.getDefaultFolders()[1]
        self.imagePlaneTxt.setText(imagePlaneDefaultPath)

    def browseChangeImagePlaneFolder(self):
        """Browse to change/set the Camera Tools Folder"""
        directoryPath = self.imagePlaneTxt.text()
        if not os.path.isdir(directoryPath):  # if dir doesn't exist set to home directory
            directoryPath = os.environ['HOME']
        newDirPath = QtWidgets.QFileDialog.getExistingDirectory(self, "Set the Image Plane folder", directoryPath)
        if newDirPath:
            self.imagePlaneTxt.setText(newDirPath)

    def exploreImagePlaneFolder(self):
        """Opens an os window for browsing files on disk in the users operating system"""
        filesystem.openDirectory(self.imagePlaneTxt.text())
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
        self.prefsData["settings"][cc.PREFS_KEY_IMAGEPLANE] = self.imagePlaneTxt.text()
        path = self.prefsData.save(indent=True)  # save and format nicely
        om2.MGlobal.displayInfo("Success: Camera Tools preferences Saved To Disk '{}'".format(path))

    def revert(self):
        """Reverts to the previous settings, resets the GUI to the previously saved settings

        Automatically connected to the preferences window revert button via model.SettingWidget
        """
        self.imagePlaneTxt.setText(self.prefsData["settings"][cc.PREFS_KEY_IMAGEPLANE])

    def adminSave(self):
        """Method for admin saving internally to Zoo Tools Pro, not connected
        """
        pass

    # -------------------
    # CONNECTIONS
    # -------------------

    def uiConnections(self):
        """Setup the custom connections for the Camera Tools Preferences GUI

        # Save, Apply buttons are automatically connected to the self.serialize() methods
        # Reset Button is automatically connected to the self.revert() method
        """
        # reset paths small buttons
        self.imagePlaneResetBtn.clicked.connect(self.setImagePlanePathDefault)
        # browse paths small buttons
        self.imagePlaneBrowseSetBtn.clicked.connect(self.browseChangeImagePlaneFolder)
        # explore paths small buttons
        self.imagePlaneExploreBtn.clicked.connect(self.exploreImagePlaneFolder)
