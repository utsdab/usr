import os

from Qt import QtWidgets

import maya.api.OpenMaya as om2
from maya import cmds

from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt.extended.imageview.models import zooscenemodel
from zoo.libs.utils import filesystem

from zoo.libs.maya.cmds.general import undodecorator
from zoo.libs.maya.cmds.shaders import shaderutils, shadermultirenderer as shdmult
from zoo.libs.maya.cmds.renderer import rendererload, exportabcshaderlights
from zoo.libs.zooscene import zooscenefiles
from zoo.libs.zooscene.constants import ZOOSCENE_EXT

from zoo.apps.toolsetsui.widgets.toolsetresizer import ToolsetResizer
from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.apps.toolsetsui import toolsetui

from zoo.preferences.core import preference
from zoo.preferences import preferencesconstants as pc
from zoo.apps.shader_tools import shaderconstants as sc
from zoo.apps.shader_tools import shaderdirectories

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1
DFLT_RNDR_MODES = [("arnold", "Arnold"), ("redshift", "Redshift"), ("renderman", "Renderman")]


class ShaderPresets(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "shaderPresets"
    info = "Shader image thumbnail browser with presets"
    uiData = {"label": "Shader Presets",
              "icon": "shaderPresets",
              "tooltip": "Shader image thumbnail browser with presets",
              "helpUrl": "https://create3dcharacters.com/maya-tool-shader-presets/",
              "defaultActionDoubleClick": False}

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        self.toolsetWidget = self  # needed for callback decorators and resizer
        self.generalSettingsPrefsData = preference.findSetting(pc.RELATIVE_PREFS_FILE, None)  # renderer in general pref
        self.properties.rendererIconMenu.value = self.generalSettingsPrefsData[pc.PREFS_KEY_RENDERER]
        self.shaderToolsPrefsData = preference.findSetting(sc.RELATIVE_PREFS_FILE, None)  # camera .prefs info
        self.setPrefVariables()  # sets self.directory and self.uniformIcons
        self.copiedAttributes = dict()  # for copy paste shaders
        self.copiedShaderName = ""  # for copy paste sahders
        if not self.directory:  # directory can be empty if preferences window hasn't been opened
            # so update the preferences json file with default locations
            self.shaderToolsPrefsData = shaderdirectories.buildUpdateShaderAssetPrefs(self.shaderToolsPrefsData)
            self.setPrefVariables()

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget(), self.initAdvancedWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        parent = QtWidgets.QWidget(parent=self)
        self.compactWidget = GuiCompact(parent=parent, properties=self.properties, toolsetWidget=self,
                                        directory=self.directory, uniformIcons=self.uniformIcons)
        return parent

    def initAdvancedWidget(self):
        """Builds the Advanced GUI (self.advancedWidget) """
        parent = QtWidgets.QWidget(parent=self)
        self.advancedWidget = GuiAdvanced(parent=parent, properties=self.properties, toolsetWidget=self,
                                          directory=self.directory, uniformIcons=self.uniformIcons)
        return parent

    def postContentSetup(self):
        """Last of the initialize code"""
        self.uiModeList()
        self.uiConnections()

    def defaultAction(self):
        """Double Click
        Double clicking the tools toolset icon will run this method
        Be sure "defaultActionDoubleClick": True is set inside self.uiData (meta data of this class)"""
        pass

    def currentWidget(self):
        """Returns the current widget class eg. self.compactWidget or self.advancedWidget

        Over ridden class
        :rtype:  GuiWidgets
        """
        return self.widgets()[self.displayIndex()].children()[0]

    def widgets(self):
        """ List of widgets

        :return:
        :rtype: list[GuiWidgets]
        """
        return super(ShaderPresets, self).widgets()


    def uiModeList(self):
        """Creates self.uiInstanceList
        A list of the uiMode widget classes eg [self.compactWidget, self.advancedWidget]
        """
        self.uiInstanceList = list()
        for widget in self.widgets():
            self.uiInstanceList.append(widget.children()[0])

    # ------------------
    # PROPERTIES
    # ------------------

    def initializeProperties(self):
        return [{"name": "rendererIconMenu", "label": "", "value": "Arnold"}]  # will be changed to prefs immediately

    def updateFromProperties(self):
        """ Runs update properties from the base class.

        Widgets will auto update from self.properties if linked via:

            self.linkProperty(widget, "propertyKey")
            or
            self.toolsetWidget.linkProperty(widget, "propertyKey")

        Add code after super() useful for changes such as forcing UI decimal places
        or manually adding unsupported widgets
        """
        super(ShaderPresets, self).updateFromProperties()
        self.guiName = self.buildShaderName()  # this is used for renaming while nothing is selected

    # ------------------------------------
    # UTILS
    # ------------------------------------

    def setPrefVariables(self):
        """Sets prefs global variables from the prefs json file
        self.directory : the current folder location for the shader presets
        self.uniformIcons : bool whether the thumb icons should be square or non square
        """
        if not self.shaderToolsPrefsData.isValid():  # should be very rare
            om2.MGlobal.displayError("The preferences object is not valid")
            return
        self.directory = self.shaderToolsPrefsData["settings"][sc.PREFS_KEY_SHADERPRESETS]
        self.uniformIcons = self.shaderToolsPrefsData["settings"][sc.PREFS_KEY_SHADERP_UNIFORM]

    def refreshThumbs(self):
        """Refreshes the GUI """
        self.currentWidget().miniBrowser.refreshThumbs()

    def refreshPrefs(self):
        self.shaderToolsPrefsData = preference.findSetting(sc.RELATIVE_PREFS_FILE, None)  # refresh and update
        if not self.shaderToolsPrefsData.isValid():  # should be very rare
            om2.MGlobal.displayError("The preferences object is not valid")
            return False
        return True

    def openPresetFolder(self):
        """Opens a windows/osx/linux file browser with the model asset directory path"""
        # success = self.refreshPrefs()
        # if not success:
        #    return
        filesystem.openDirectory(self.directory)

    def renameAsset(self):
        """Renames the asset on disk"""
        currentFileNoSuffix = self.currentWidget().browserModel.currentImage
        self.zooScenePath = self.currentWidget().miniBrowser.selectedMetadata()['zooFilePath']
        if not currentFileNoSuffix:  # no image has been selected
            om2.MGlobal.displayWarning("Please select a shader preset image to rename.")
            return
        # Get the current directory
        message = "Rename Related `{}` Files As:".format(currentFileNoSuffix)
        renameText = elements.InputDialog(windowName="Rename Shader Preset", textValue=currentFileNoSuffix, parent=None,
                                          message=message)
        if not renameText:
            return
        # Do the rename
        fileRenameList = zooscenefiles.renameZooSceneOnDisk(renameText, self.zooScenePath)
        if not fileRenameList:  # shouldn't happen for shaders
            om2.MGlobal.displayWarning("Files could not be renamed, they are probably in use by the current scene. "
                                       "Do not have the renamed assets loaded in the scene, "
                                       "or check your file permissions.")
            return
        om2.MGlobal.displayInfo("Success: Files `{}*` Have Been Renamed To `{}*`".format(currentFileNoSuffix, renameText))
        self.refreshThumbs()

    def setAssetQuickDirectory(self):
        """Browse to change/set the Model Asset Folder"""
        success = self.refreshPrefs()
        if not success:
            return
        directoryPath = self.shaderToolsPrefsData["settings"][sc.PREFS_KEY_SHADERPRESETS]
        if not os.path.isdir(directoryPath):  # if dir doesn't exist set to home directory
            directoryPath = os.environ['HOME']
        newDirPath = QtWidgets.QFileDialog.getExistingDirectory(self, "Set the Model Asset folder", directoryPath)
        if not newDirPath:
            return
        self.shaderToolsPrefsData["settings"][sc.PREFS_KEY_SHADERPRESETS] = newDirPath
        self.shaderToolsPrefsData.save()
        self.directory = newDirPath
        # update thumb model on both thumb widgets
        self.compactWidget.browserModel.setDirectory(newDirPath)  # does the refresh
        self.advancedWidget.browserModel.setDirectory(newDirPath)
        om2.MGlobal.displayInfo("Preferences Saved: Model Asset folder saved as "
                                "`{}`".format(newDirPath))

    def uniformIconToggle(self, action):
        """Toggles the state of the uniform icons
        """
        # TODO should use the checked value instead of inverting, but doesn't work?
        self.uniformIcons = action.isChecked()
        self.shaderToolsPrefsData["settings"][sc.PREFS_KEY_SHADERP_UNIFORM] = self.uniformIcons
        self.shaderToolsPrefsData.save()
        self.refreshThumbs()

    def deletePresetPopup(self):
        """Popup window that asks the user if they want to delete the currently selected asset from disk?"""
        filename = self.currentWidget().browserModel.currentImage
        filenameWithSuffix = ".".join([filename, zooscenefiles.ZOOSCENESUFFIX])
        if not filenameWithSuffix:
            om2.MGlobal.displayWarning("Nothing selected. Please select a shader preset to delete.")
        path = os.path.join(self.currentWidget().browserModel.directory, filenameWithSuffix)
        # Build popup window
        message = "Warning: Delete the preset `{}` and it's dependencies?  " \
                  "This will permanently delete these file/s from disk?".format(filenameWithSuffix)
        result = elements.MessageBox_ok(windowName="Delete Shader Preset From Disk?",
                                        message=message)  # None will parent to Maya
        # After answering Ok or cancel
        if result:  # Ok was pressed
            filesFullPathDeleted = zooscenefiles.deleteZooSceneFiles(path, message=True)
            self.refreshThumbs()
            om2.MGlobal.displayInfo("Success, File/s Deleted: {}".format(filesFullPathDeleted))

    def savePreset(self):
        """Opens a window to save the shader to the library"""
        # Get the shader to save str
        shaderInScene = shaderutils.getShaderNameFromNodeSelected(removeSuffix=False)
        shaderNameNoSuffix = shaderutils.removeShaderSuffix(shaderInScene)
        # Popup save window
        message = "Save Shader to Preset Library?"
        # TODO need to specify a parent as the Maya window, current stylesheet issues with self.parent
        shaderName = elements.InputDialog(windowName="Save Curve Control", textValue=shaderNameNoSuffix,
                                          parent=None, message=message)
        # Do the .zooScene save
        zooSceneFile = ".".join([shaderName, ZOOSCENE_EXT])
        self.directory = self.shaderToolsPrefsData["settings"][sc.PREFS_KEY_SHADERPRESETS]
        zooSceneFullPath = os.path.join(self.directory, zooSceneFile)
        if os.path.exists(zooSceneFullPath):  # file already exists, overwrite?
            message = "File  exists, overwrite?\n" \
                      "   {}".format(zooSceneFullPath)
            if not elements.MessageBox_ok(windowName="File Already Exists", message=message):
                return
        if shaderName:
            exportabcshaderlights.saveShaderPresetZooScene(zooSceneFullPath, shaderName, shaderInScene)
            # Refresh GUI to add new thumbnail
            self.refreshThumbs()

    # ------------------------------------
    # SEND/RECEIVE ALL TOOLSETS (RENDERER AND SHADER CREATE)
    # ------------------------------------

    def global_changeRenderer(self):
        """Updates all GUIs with the current renderer"""
        self.generalSettingsPrefsData = preference.findSetting(pc.RELATIVE_PREFS_FILE, None)  # refresh data
        toolsets = toolsetui.toolsets(attr="global_receiveRendererChange")
        self.generalSettingsPrefsData = elements.globalChangeRenderer(self.properties.rendererIconMenu.value,
                                                                      toolsets,
                                                                      self.generalSettingsPrefsData,
                                                                      pc.PREFS_KEY_RENDERER)

    def global_receiveRendererChange(self, renderer):
        """Receives from other GUIs, changes the renderer when it is changed"""
        self.properties.rendererIconMenu.value = renderer
        self.updateFromProperties()

    def global_shaderUpdated(self):
        """Updates all GUIs with the current renderer"""
        self.generalSettingsPrefsData = preference.findSetting(pc.RELATIVE_PREFS_FILE, None)  # refresh data
        toolsets = toolsetui.toolsets(attr="global_receiveShaderUpdated")
        for tool in toolsets:
            tool.global_receiveShaderUpdated()

    # ------------------------------------
    # COPY PASTE - AND SEND/RECEIVE ALL TOOLSETS
    # ------------------------------------

    def global_sendCopyShader(self):
        """Updates all GUIs with the copied shader"""
        toolsets = toolsetui.toolsets(attr="global_receiveCopiedShader")
        for tool in toolsets:
            tool.global_receiveCopiedShader(self.copiedShaderName, self.copiedAttributes)

    def global_receiveCopiedShader(self, copiedShaderName, copiedAttributes):
        """Receives the copied shader from other GUIs"""
        self.copiedShaderName = copiedShaderName
        self.copiedAttributes = copiedAttributes

    # ------------------
    # LOGIC CREATE & DELETE
    # ------------------

    def buildShaderName(self):
        return shdmult.buildNameWithSuffix("shader01",
                                           True,
                                           self.properties.rendererIconMenu.value)

    @toolsetwidgetmaya.undoDecorator
    def createShaderUndo(self):
        """Creates a shader with one undo"""
        self.createShader()

    def createShader(self):
        """Create Shader
        """
        currRenderer = self.properties.rendererIconMenu.value
        shaderType = shdmult.RENDERERSHADERS[currRenderer][0]
        if not rendererload.getRendererIsLoaded(currRenderer):  # the renderer is not loaded open window
            if not elements.checkRenderLoaded(self.properties.rendererIconMenu.value):
                return
        shaderName = "shader01"  # todo get shader name from dict
        # create shader
        shaderName = shdmult.createShaderTypeSelected(shaderType, shaderName=shaderName, message=True)
        # set the shader attributes
        self.setShaderZooScene(shaderName, renameShader=True)

    def deleteShader(self):
        """Deletes the shader in the UI from the scene"""
        shaderName = self.buildShaderName()
        shdmult.deleteShader(shaderName)

    # ------------------
    # LOGIC TRANSFER SELECT
    # ------------------

    @toolsetwidgetmaya.undoDecorator
    def transferAssign(self):
        """Assigns the shader from the first selected face or object to all other selected objects and faces"""
        success = shaderutils.transferAssignSelection()
        if not success:  # message already reported to user
            return
        shaderName = self.buildShaderName()
        om2.MGlobal.displayInfo("Shader assigned `{}`".format(shaderName))

    @toolsetwidgetmaya.undoDecorator
    def selectObjFacesFromShader(self):
        """Selects objects and faces assigned from a shader"""
        shaderList = shaderutils.getShadersSelected()
        if not shaderList:
            return
        shaderutils.selectMeshFaceFromShaderName(shaderList[0])

    @toolsetwidgetmaya.undoDecorator
    def selectShader(self):
        """Selects the active shader from the GUI"""
        shaderList = shaderutils.getShadersSelected()
        if not shaderList:
            return
        cmds.select(shaderList[0], replace=True)

    # ------------------
    # LOGIC TRANSFER COPY PASTE
    # ------------------

    def copyShader(self, message=False):
        """Copies the shader into a dictionary self.copiedAttributes so it can be applied later
        """
        rendererLoaded = rendererload.getRendererIsLoaded(self.properties.rendererIconMenu.value)
        if not rendererLoaded:
            return
        shaderName = shaderutils.getShaderNameFromNodeSelected(removeSuffix=False)
        if not shaderName:
            om2.MGlobal.displayWarning("No shader found to copy")
            return
        shaderAttributes, nameMatch = shdmult.getShaderSelected(shaderName=shaderName)
        if not shaderAttributes:  # no legit shaders found, message already warned
            return
        self.copiedAttributes = shaderAttributes
        self.copiedShaderName = shaderName
        self.global_sendCopyShader()
        om2.MGlobal.displayInfo("Shader copied `{}`".format(self.copiedShaderName))

    @toolsetwidgetmaya.undoDecorator
    def pasteAttributes(self):
        """sets the copied shader attributes to the selected/active shader, but does not assign, the shader remains"""
        if not self.copiedAttributes:
            om2.MGlobal.displayWarning("Cannot paste as there is nothing in the clipboard.  Please copy a shader.")
            return
        # needs to get shader names of selected of type renderer
        shaderNames = shdmult.getShadersSelectedRenderer(self.properties.rendererIconMenu.value)
        shaderType = shdmult.RENDERERSHADERS[self.properties.rendererIconMenu.value][0]
        for shader in shaderNames:
            shdmult.setShaderAttrs(shader,
                                   shaderType,
                                   self.copiedAttributes,
                                   convertSrgbToLinear=True,
                                   reportMessage=True)
        om2.MGlobal.displayInfo("Shader attributes pasted to `{}`".format(shaderNames))

    @toolsetwidgetmaya.undoDecorator
    def pasteAssign(self):
        """Assigns the copied shader (from the shader name) to the selected object/s or faces"""
        if not self.copiedShaderName:
            om2.MGlobal.displayWarning("Cannot paste as there is nothing in the clipboard.  Please copy a shader.")
            return
        if not cmds.objExists(self.copiedShaderName):
            om2.MGlobal.displayWarning("Shader `` does not exist in this scene".format(self.copiedShaderName))
            return
        shaderutils.assignShaderSelected(self.copiedShaderName)
        om2.MGlobal.displayInfo("Shader assigned `{}`".format(self.copiedShaderName))

    # ------------------
    # LOGIC SET
    # ------------------

    def setShaderZooScene(self, shaderName, renameShader=False, message=True):
        """Sets the shader attributes after creation

        :param shaderName: name of the shader to set
        :type shaderName: str
        :param renameShader: rename the shader to the zooScene shader name?
        :type renameShader: bool
        :param message: report the message to the user?
        :type message: bool
        """
        renderer = self.properties.rendererIconMenu.value
        if not rendererload.getRendererIsLoaded(renderer):  # the renderer is not loaded open window
            if not elements.checkRenderLoaded(renderer):
                return
        shaderType = shdmult.RENDERERSHADERS[renderer][0]
        if shaderType != cmds.nodeType(shaderName):  # shader type does not match so convert the shader
            objList = shaderutils.getObjectsFacesAssignedToShader(shaderName)
            if not objList:
                return
            # Assign a new default shader of the renderer type
            shaderName = shdmult.createShaderTypeObjList(shaderType, objList=objList, shaderName="shaderTempXXX")
            # Set attributes (won't end here or would be a loop)
            self.setShaderZooScene(shaderName, renameShader=True)
            return
        # Get the zooScene
        zooScenePath = os.path.join(self.currentWidget().browserModel.directory,
                                    "{}.{}".format(self.currentWidget().browserModel.currentImage,
                                                   exportabcshaderlights.ZOOSCENESUFFIX))
        # Set the shader attributes
        shadername = exportabcshaderlights.setShaderAttrsZooScene(zooScenePath, shaderName, shaderType, renameToZooName=renameShader,
                                                     message=message)
        cmds.select(shadername, replace=True)
        self.global_shaderUpdated()

    @toolsetwidgetmaya.undoDecorator
    def setShaderSelectedZooScene(self, message=True):
        """From the selected object or shader, return the first found shader and assign it to a .zooScene file

        :param message: report the message to the user?
        :type message: bool
        """
        if not cmds.ls(selection=True):
            om2.MGlobal.displayWarning("Nothing is selected, please select a mesh or shader")
            return
        shaderName = shaderutils.getShaderNameFromNodeSelected(removeSuffix=False)
        if not shaderName:
            return
        self.setShaderZooScene(shaderName, message=True)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for uiInstance in self.uiInstanceList:
            # Thumbnail viewer
            uiInstance.browserModel.doubleClicked.connect(self.setShaderSelectedZooScene)
            # Dots menu
            uiInstance.miniBrowser.dotsMenu.applyAction.connect(self.setShaderSelectedZooScene)
            uiInstance.miniBrowser.dotsMenu.createAction.connect(self.savePreset)
            uiInstance.miniBrowser.dotsMenu.renameAction.connect(self.renameAsset)
            uiInstance.miniBrowser.dotsMenu.browseAction.connect(self.openPresetFolder)
            uiInstance.miniBrowser.dotsMenu.setDirectoryAction.connect(self.setAssetQuickDirectory)
            uiInstance.miniBrowser.dotsMenu.deleteAction.connect(self.deletePresetPopup)
            uiInstance.miniBrowser.dotsMenu.refreshAction.connect(self.refreshThumbs)
            uiInstance.miniBrowser.dotsMenu.uniformIconAction.connect(self.uniformIconToggle)
            # Change Renderer
            uiInstance.rendererIconMenu.actionTriggered.connect(self.global_changeRenderer)
            # Create Change Shaders
            uiInstance.createBtn.clicked.connect(self.createShaderUndo)
            uiInstance.changeBtn.clicked.connect(self.setShaderSelectedZooScene)
        # Transfer
        self.advancedWidget.transferShaderBtn.clicked.connect(self.transferAssign)
        # Select
        self.advancedWidget.selectShaderBtn.clicked.connect(self.selectShader)
        self.advancedWidget.selectObjectsBtn.clicked.connect(self.selectObjFacesFromShader)
        # Copy Paste
        self.advancedWidget.copyShaderBtn.clicked.connect(self.copyShader)
        self.advancedWidget.pasteShaderBtn.clicked.connect(self.pasteAssign)
        self.advancedWidget.pasteAttrBtn.clicked.connect(self.pasteAttributes)

class GuiWidgets(QtWidgets.QWidget):
    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None, directory="", uniformIcons=True):
        """Builds the main widgets for all GUIs

        properties is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: object
        :param uiMode: 0 is compact ui mode, 1 is advanced ui mode
        :type uiMode: int
        """
        super(GuiWidgets, self).__init__(parent=parent)
        # Thumbnail Viewer --------------------------------------------
        # self.themePref = preference.interface("core_interface")
        # viewer widget and model
        self.miniBrowser = elements.MiniBrowser(parent=self,
                                                toolsetWidget=toolsetWidget,
                                                columns=3,
                                                fixedHeight=382,
                                                uniformIcons=uniformIcons,
                                                itemName="Shader Preset",
                                                applyText="Apply To Selected",
                                                applyIcon="shaderBall",
                                                createText="Save")
        self.miniBrowser.dotsMenu.setSnapshotActive(True)
        self.browserModel = zooscenemodel.ZooSceneViewerModel(self.miniBrowser,
                                                              directory=directory,
                                                              chunkCount=200,
                                                              uniformIcons=uniformIcons)
        self.miniBrowser.setModel(self.browserModel)
        self.resizerWidget = ToolsetResizer(toolsetWidget=toolsetWidget, target=self.miniBrowser)
        # Change Assign Button ---------------------------------------
        tooltip = "Changes the selected shader to the preset values \n" \
                  "(Default double-click thumbnail) \n" \
                  "If a non-renderer shader is selected a new shader will be created."
        self.changeBtn = elements.styledButton("Change Apply",
                                               icon="shaderPresets",
                                               toolTip=tooltip,
                                               style=uic.BTN_DEFAULT)
        # Create Button ---------------------------------------
        tooltip = "Creates a new shader on the selected objects or faces from the selected thumbnail. \n" \
                  "If nothing is selected will create a shader only."
        self.createBtn = elements.styledButton("Create New",
                                               icon="shaderBall",
                                               toolTip=tooltip,
                                               style=uic.BTN_DEFAULT)
        # Renderer Button --------------------------------------
        toolTip = "Change the renderer to Arnold, Redshift or Renderman"
        self.rendererIconMenu = elements.iconMenuButtonCombo(DFLT_RNDR_MODES,
                                                             properties.rendererIconMenu.value,
                                                             toolTip=toolTip)
        if uiMode == UI_MODE_ADVANCED:
            # Copy Shader Btn --------------------------------------------
            toolTip = "Copy the current shader settings to the clipboard"
            self.copyShaderBtn = elements.styledButton("Copy", "copyShader",
                                                       toolTip=toolTip,
                                                       style=uic.BTN_DEFAULT)
            # Paste Assign Shader Btn --------------------------------------------
            toolTip = "Paste the shader attribute settings from the clipboard \n" \
                      "Shader attribute settings will be pasted, the existing shader will remain."
            self.pasteAttrBtn = elements.styledButton("Paste", "pasteAttributes",
                                                      toolTip=toolTip,
                                                      style=uic.BTN_DEFAULT)
            # Paste Attribute Shader Btn --------------------------------------------
            toolTip = "Paste/Assign the shader from the clipboard \n" \
                      "Existing shader will be assigned to selected geometry"
            self.pasteShaderBtn = elements.styledButton("Paste", "pasteAssign",
                                                        toolTip=toolTip,
                                                        style=uic.BTN_DEFAULT)
            # Transfer Shader Btn --------------------------------------------
            toolTip = "Transfer the current shader to another object \n" \
                      "- 1. Select two or more objects. \n" \
                      "- 2. The shader from the first object will be transferred to others."
            self.transferShaderBtn = elements.styledButton("Transfer", "transferShader",
                                                           toolTip=toolTip,
                                                           style=uic.BTN_DEFAULT)
            # Select Objects/Faces --------------------------------------------
            toolTip = "Select objects and or faces with this material"
            self.selectObjectsBtn = elements.styledButton("Object Sel",
                                                          "selectObject",
                                                          self,
                                                          toolTip=toolTip,
                                                          style=uic.BTN_DEFAULT)
            # Select Shader Btn --------------------------------------------
            toolTip = "Select shader node / deselect geometry"
            self.selectShaderBtn = elements.styledButton("Shader Sel",
                                                         "selectShader",
                                                         self,
                                                         toolTip=toolTip,
                                                         style=uic.BTN_DEFAULT)


class GuiCompact(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None, directory="",
                 uniformIcons=True):
        """Adds the layout building the compact version of the GUI:

            default uiMode - 0 is advanced (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(GuiCompact, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                         toolsetWidget=toolsetWidget, directory=directory, uniformIcons=uniformIcons)
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(parent, margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Button Layout ---------------------------------------
        btnLayout = elements.hBoxLayout()
        btnLayout.addWidget(self.changeBtn, 10)
        btnLayout.addWidget(self.createBtn, 10)
        btnLayout.addWidget(self.rendererIconMenu, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(self.miniBrowser)
        mainLayout.addWidget(self.resizerWidget)
        mainLayout.addLayout(btnLayout)



class GuiAdvanced(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_ADVANCED, toolsetWidget=None, directory="",
                 uniformIcons=True):
        """Adds the layout building the advanced version of the GUI:

            default uiMode - 1 is advanced (UI_MODE_ADVANCED)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(GuiAdvanced, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                          toolsetWidget=toolsetWidget, directory=directory, uniformIcons=uniformIcons)
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(parent, margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Button Layout ---------------------------------------
        btnLayout = elements.hBoxLayout(margins=(0, uic.SMLPAD, 0, 0))
        btnLayout.addWidget(self.changeBtn, 10)
        btnLayout.addWidget(self.createBtn, 10)
        btnLayout.addWidget(self.rendererIconMenu, 1)

        transferSelLayout = elements.GridLayout()
        transferSelLayout.addWidget(self.copyShaderBtn, 0, 0)
        transferSelLayout.addWidget(self.pasteShaderBtn, 0, 1)
        transferSelLayout.addWidget(self.pasteAttrBtn, 0, 2)
        transferSelLayout.addWidget(self.transferShaderBtn, 1, 0)
        transferSelLayout.addWidget(self.selectShaderBtn, 1, 1)
        transferSelLayout.addWidget(self.selectObjectsBtn, 1, 2)
        transferSelLayout.setColumnStretch(0, 1)
        transferSelLayout.setColumnStretch(1, 1)
        transferSelLayout.setColumnStretch(2, 1)

        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(self.miniBrowser)
        mainLayout.addWidget(self.resizerWidget)
        mainLayout.addLayout(transferSelLayout)
        mainLayout.addLayout(btnLayout)
