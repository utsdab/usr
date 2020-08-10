import os


from zoovendor.pathlib2 import Path

import maya.api.OpenMaya as om2
from maya import cmds

from Qt import QtCore, QtWidgets

from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt import uiconstants as uic

from zoo.libs.utils import filesystem

from zoo.apps.preferencesui import model
from zoo.preferences.core import preference
from zoo.preferences import preferencesconstants as pc


class GeneralPrefsWidget(model.SettingWidget):
    categoryTitle = "General"  # The main title of the General preferences section and also side menu item

    def __init__(self, parent=None):
        """Builds the General Section of the preferences window.

        :param parent: the parent widget
        :type parent: Qt.QtWidgets
        """
        super(GeneralPrefsWidget, self).__init__(parent)
        # Light Suite Pref Object self.lsPrefsObj stores and saves all the .prefs json data
        self.prefsData = preference.findSetting(pc.RELATIVE_PREFS_FILE, None)
        self.initialUserPrefsPath = self.getUserPreferences()
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
        primaryRenderer = self.prefsData[pc.PREFS_KEY_RENDERER]
        # Light Presets Path -----------------------------------------
        toolTip = "The location of the Zoo User Preferences folder. \n" \
                  "All Zoo Asset and Prefs folder locations are found in this folder unless \n" \
                  "otherwise specified. \n" \
                  "Moving this folder will require a Maya restart."
        self.userPrefPathLbl = elements.Label("Zoo Preferences Folder", parent=self, toolTip=toolTip)
        self.userPrefPathTxt = elements.StringEdit(label="",
                                                  editText=self.initialUserPrefsPath,
                                                  toolTip=toolTip)
        toolTip = "Browse to change the Zoo User Preferences folder."
        self.userPrefPathBrowseSetBtn = elements.styledButton("",
                                                             "browse",
                                                                toolTip=toolTip,
                                                                parent=self,
                                                                minWidth=uic.BTN_W_ICN_MED)
        toolTip = "Reset the Zoo User Preferences folder to it's default location."
        self.userPrefPathResetBtn = elements.styledButton("",
                                                         "refresh",
                                                            toolTip=toolTip,
                                                            parent=self,
                                                            minWidth=uic.BTN_W_ICN_MED)
        toolTip = "Explore, open the directory in your OS browser."
        self.userPrefPathExploreBtn = elements.styledButton("",
                                                           "globe",
                                                              toolTip=toolTip,
                                                              parent=self,
                                                              minWidth=uic.BTN_W_ICN_MED)
        # Primary Renderer -----------------------------------------
        toolTip = "Set your primary renderer, will be used by all windows, can be changed at anytime.\n" \
                  "The renderer must be installed on your computer (Redshift or Renderman)."
        self.rendererTitleLabel = elements.Label(text="Primary Renderer",
                                                                    parent=self,
                                                                    upper=True,
                                                                    toolTip=toolTip)
        utils.setStylesheetObjectName(self.rendererTitleLabel, "HeaderLabel")  # set title stylesheet
        currentIndex = pc.RENDERER_LIST.index(primaryRenderer)
        self.rendererComboLbl = elements.Label("Set Renderer", parent=self, toolTip=toolTip)
        self.rendererCombo = elements.ComboBoxRegular(label="",
                                                      items=pc.RENDERER_LIST,
                                                      toolTip=toolTip,
                                                      setIndex=currentIndex,
                                                      labelRatio=1,
                                                      boxRatio=2,
                                                      boxMinWidth=150)
        toolTip = "Load the Renderer selected in the drop-down combobox.\n " \
                  "The renderer may already be loaded"
        self.loadRendererBtn = elements.styledButton("Load Renderer",
                                                    "checkOnly",
                                                       self,
                                                       toolTip=toolTip,
                                                       style=uic.BTN_DEFAULT,
                                                       minWidth=120)

    def uiLayout(self):
        """Adds all the widgets to layouts for the GUI"""
        mainLayout = elements.vBoxLayout(self,
                                                              margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                                              spacing=uic.SREG)
        # Light Preset Path Layout ------------------------------------
        generalPathBtnLayout = elements.hBoxLayout()
        generalPathBtnLayout.addWidget(self.userPrefPathBrowseSetBtn)
        generalPathBtnLayout.addWidget(self.userPrefPathResetBtn)
        generalPathBtnLayout.addWidget(self.userPrefPathExploreBtn)

        pathGridLayout = elements.GridLayout(
                                            margins=(0, 0, 0, uic.SXLRG),
                                            columnMinWidth=(0, 120),
                                            columnMinWidthB=(2, 120))
        pathGridLayout.addWidget(self.userPrefPathLbl, 0, 0)
        pathGridLayout.addWidget(self.userPrefPathTxt, 0, 1)
        pathGridLayout.addLayout(generalPathBtnLayout, 0, 2)
        # Primary Renderer Combo ------------------------------------
        rendererLayout = elements.hBoxLayout()
        rendererLayout.addWidget(self.rendererCombo)
        rendererLayout.addStretch(1)
        # Primary Renderer Grid top ----------------------------------------------
        rendererGridLayout = elements.GridLayout(margins=(0, uic.SLRG, 0, uic.SXLRG),
                                                 columnMinWidth=(0, 120),
                                                 columnMinWidthB=(2, 120))
        rendererGridLayout.addWidget(self.rendererComboLbl, 0, 0)
        rendererGridLayout.addLayout(rendererLayout, 0, 1)
        rendererGridLayout.addWidget(self.loadRendererBtn, 0, 2)
        # main layout
        mainLayout.addLayout(pathGridLayout)
        mainLayout.addWidget(self.rendererTitleLabel)
        mainLayout.addLayout(rendererGridLayout)
        mainLayout.addStretch(1)

    # ------------------------------------
    # POPUP WINDOWS
    # ------------------------------------

    def ui_changePrefsPopup(self):
        """Popup window dialog asking the user wants to change the preferences folder, will require a restart

        :return okPressed: True if the ok button was pressed, else False if cancelled
        :rtype okPressed: bool
        """
        message = "Are you sure you want to change the Zoo User Preferences Folder? \n\n" \
                  "This will move the entire preferences directory with all files and assets.\n\n" \
                  "Changing the location of this folder will require a full Maya restart after save."
        okPressed = elements.MessageBox_ok(windowName="Change Zoo User Preferences "
                                                     "Folder?", parent=None, message=message)
        return okPressed

    def ui_resetPopup(self, prefsDefautlPath):
        """Popup window dialog asking the user wants to return to the preferences folder default, will require restart

        :return okPressed: True if the ok button was pressed, else False if cancelled
        :rtype okPressed: bool
        """
        message = "Are you sure you want to return to the DefaultZoo User Preferences Folder? \n\n" \
                  "{} \n\n" \
                  "This will move the entire preferences directory with all files and assets.\n" \
                  "Changing the location of this folder will require a full Maya restart after save.".format(
            prefsDefautlPath)
        okPressed = elements.MessageBox_ok(windowName="Change Zoo User Preferences"
                                                     "Folder?", parent=None, message=message)
        return okPressed

    def ui_restartPopup(self, newPrefsPath):
        """Popup window dialog asking the user to restart Maya after the Zoo User Preferences have changed.

        :param newPrefsPath: The new path to the zoo_preferences folder
        :type newPrefsPath: str
        :return okPressed: True if the ok button was pressed, else False if cancelled
        :rtype okPressed: bool
        """
        message = "The Zoo User Preferences path has been moved to \n\n  " \
                  "{}\n\n" \
                  "You should restart Maya. Close Maya now?".format(newPrefsPath)
        okPressed = elements.MessageBox_ok(windowName="Close And Restart Maya?", parent=None, message=message)
        return okPressed

    # ------------------------------------
    # POPUP WINDOWS
    # ------------------------------------

    def ui_loadRenderer(self, renderer):
        """Popup window dialog asking the user if they'd like to load the given renderer

        :param renderer: The renderer nice name eg. "Arnold"
        :type renderer: str
        :return okPressed: True if the ok button was pressed, else False if cancelled
        :rtype okPressed: bool
        """
        message = "The {} renderer isn't loaded. Load now?".format(renderer)
        okPressed = elements.MessageBox_ok(windowName="Load Renderer?", parent=None, message=message)
        return okPressed

    def checkRenderLoaded(self):
        """Checks that the renderer is loaded, if not opens a popup window asking the user to load?

        :return rendererLoaded: True if the renderer is loaded
        :rtype rendererLoaded: bool
        """
        try:  # zoo_core_pro may not be loaded (though unlikely
            from zoo.libs.maya.cmds.renderer import rendererload
            renderer = self.rendererCombo.currentText()
            if not rendererload.getRendererIsLoaded(renderer):
                okPressed = self.ui_loadRenderer(renderer)  # open the popup dialog window
                if okPressed:
                    rendererload.loadRenderer(renderer)  # load the renderer
                    return True
                return False
            else:
                om2.MGlobal.displayInfo("The renderer `{}` is already loaded".format(renderer))
            return True
        except:
            om2.MGlobal.displayWarning("Check renderer loaded failed, the package zoo_core_pro may "
                                       "not be loaded")

    # -------------------
    # CHANGE PREFERENCES UPDATE OTHER WINDOWS - GLOBAL TOOL SETS
    # -------------------

    def global_changeRenderer(self):
        """Updates all GUIs with the current renderer"""
        try:  # toolsets may not be loaded
            from zoo.apps.toolsetsui import toolsetui
            toolsets = toolsetui.toolsets(attr="global_receiveRendererChange")
            for tool in toolsets:
                tool.global_receiveRendererChange(self.rendererCombo.currentText())
        except:
            om2.MGlobal.displayWarning("Change renderer did not send to Toolsets, the package zoo_toolsets may "
                                       "not be loaded")

    def global_receiveRendererChange(self, renderer):
        """Receives from other GUIs, changes the renderer when it is changed

        TODO currently not in use"""
        index = pc.RENDERER_LIST.index(renderer)
        self.rendererCombo.setCurrentIndex(index)

    # -------------------
    # LOGIC
    # -------------------

    def getUserPreferences(self):
        """Retrieves the path to the Zoo Tools User Preferences, if '~/zoo_preferences' then displays full path"""
        userPrefsPath = os.path.normpath(str(preference.root("user_preferences")))
        if userPrefsPath != "~/zoo_preferences":
            return userPrefsPath
        # else return the full path directory to users home directory + "zoo_preferences"
        return os.path.normpath(str(Path("~/zoo_preferences").expanduser()))

    def setZooPrefsDefault(self):
        """Sets the UI widget path text to the default Zoo User Preferences path"""
        zooDefaultPrefsPath = os.path.normpath(str(Path("~/zoo_preferences").expanduser()))  # check this
        if os.path.normpath(self.userPrefPathTxt.text()) == zooDefaultPrefsPath:
            return  # hasn't changed from the saved version
        if self.getUserPreferences() == zooDefaultPrefsPath:
            self.userPrefPathTxt.setText(zooDefaultPrefsPath)  # matches the saved path
            return
        okPressed = self.ui_resetPopup(zooDefaultPrefsPath)
        if not okPressed:
            return
        self.userPrefPathTxt.setText(zooDefaultPrefsPath)

    def browseChangeZooPrefsFolder(self):
        """Browse to change/set the Zoo User Preferences Folder"""
        directoryPath = self.userPrefPathTxt.text()
        if not os.path.isdir(directoryPath):  # if dir doesn't exist set to home directory
            directoryPath = os.path.expanduser("~")
        changeDirPressed = self.ui_changePrefsPopup()  # open "are you sure?" popup window
        if not changeDirPressed:  # cancelled
            return
        newDirPath = QtWidgets.QFileDialog.getExistingDirectory(self, "Set the Zoo User Preferences "
                                                                      "folder", directoryPath)
        if not newDirPath:
            return  # cancelled or folder is the same
        newDirPath = os.path.join(newDirPath, 'zoo_preferences')
        self.userPrefPathTxt.setText(os.path.normpath(newDirPath))  # update path GUI

    def exploreZooPrefsFolder(self):
        """Opens an os window for browsing files on disk in the users operating system"""
        filesystem.openDirectory(self.userPrefPathTxt.text())
        om2.MGlobal.displayInfo("OS window opened to the `Zoo User Preferences` folder location")

    # -------------------
    # SAVE/APPLY AND RESET
    # -------------------

    def serialize(self):
        """ Save the current settings to the preference file, used for both Apply and Save buttons

        Automatically connected to the preferences window buttons via model.SettingWidget
        """
        # save renderer to preferences "general_settings.pref"
        self.prefsData[pc.PREFS_KEY_RENDERER] = self.rendererCombo.currentText()
        self.prefsData.save(indent=True)  # save and format nicely
        # save zoo_preferences path
        previousPath = self.getUserPreferences()
        newDirPath = os.path.normpath(self.userPrefPathTxt.text())
        if previousPath == newDirPath:  # no change
            return
        if os.path.isdir(newDirPath):
            om2.MGlobal.displayWarning("The directory already exists, "
                                       "it should not currently exist: `{}`".format(newDirPath))
            return
        # do the prefs move/change
        preference.moveRootLocation("user_preferences", newDirPath)
        interface = preference.interface("core_interface")
        interface.bakePreferenceRoots()
        # restart popup window
        restartPressed = self.ui_restartPopup(newDirPath)  # restart popup window
        if not restartPressed:  # canceled window
            return
        cmds.quit()  # close Maya

    def revert(self):
        """Reverts to the previous settings, resets the GUI to the previously saved settings

        Automatically connected to the preferences window revert button via model.SettingWidget
        """
        self.userPrefPathTxt.setText(self.getUserPreferences())

    # -------------------
    # CONNECTIONS
    # -------------------

    def uiConnections(self):
        """Setup the custom connections for the Light Suite Preferences GUI

        # Save, Apply buttons are automatically connected to the self.serialize() methods
        # Reset Button is automatically connected to the self.revert() method
        """
        # load/change renderer
        self.loadRendererBtn.clicked.connect(self.checkRenderLoaded)
        self.rendererCombo.itemChanged.connect(self.global_changeRenderer)
        # zoo_preferences path changes
        self.userPrefPathBrowseSetBtn.clicked.connect(self.browseChangeZooPrefsFolder)
        self.userPrefPathExploreBtn.clicked.connect(self.exploreZooPrefsFolder)
        self.userPrefPathResetBtn.clicked.connect(self.setZooPrefsDefault)
