import os
from functools import partial

import maya.api.OpenMaya as om2
from maya import cmds

from Qt import QtWidgets
from zoo.apps.model_assets import assetconstants as ac
from zoo.apps.model_assets import assetdirectories
from zoo.apps.toolsetsui import toolsetui
from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.apps.toolsetsui.widgets.toolsetresizer import ToolsetResizer
from zoo.libs.maya.cmds.assets import assetsimportexport
from zoo.libs.maya.cmds.general import undodecorator
from zoo.libs.maya.cmds.objutils import namehandling
from zoo.libs.maya.cmds.renderer import rendererload, exportabcshaderlights
from zoo.libs.pyqt import keyboardmouse
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.extended.imageview.models import zooscenemodel
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import filesystem
from zoo.libs.utils import zlogging
from zoo.libs.zooscene import zooscenefiles
from zoo.preferences import preferencesconstants as pc
from zoo.preferences.core import preference

THEME_PREFS = preference.interface("core_interface")

logger = zlogging.getLogger(__name__)

DFLT_RNDR_MODES = [("arnold", "Arnold"), ("redshift", "Redshift"), ("renderman", "Renderman")]
REPLACE_COMBO = ["Replace Asset By Type", "Replace All Assets", "Add To Scene"]
UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class ModelAssets(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "modelAssets"
    uiData = {"label": "Model Assets",
              "icon": "packageAssets",
              "tooltip": "Mini browser for models, object assets",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-model-assets/"
              }

    # ------------------------------------
    # START UP
    # ------------------------------------

    def preContentSetup(self):
        """First code to run"""
        self.toolsetWidget = self  # needed for callback decorators
        self.modelAssetsPrefsData = preference.findSetting(ac.RELATIVE_PREFS_FILE, None)  # model asset .prefs info
        self.generalSettingsPrefsData = preference.findSetting(pc.RELATIVE_PREFS_FILE, None)  # renderer in general pref
        self.properties.rendererIconMenu.value = self.generalSettingsPrefsData[pc.PREFS_KEY_RENDERER]
        self.setPrefVariables()  # sets self.directory and self.uniformIcons
        if not self.directory:  # directory can be empty if preferences window hasn't been opened
            # so update the preferences json file with default locations
            self.modelAssetsPrefsData = assetdirectories.buildUpdateModelAssetPrefs(self.modelAssetsPrefsData)
            self.setPrefVariables()

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget(), self.initAdvancedWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        parent = QtWidgets.QWidget(parent=self)
        self.parentWgt = parent
        self.compactWidget = GuiCompact(parent=parent, properties=self.properties, toolsetWidget=self,
                                        directory=self.directory, uniformIcons=self.uniformIcons)
        return self.compactWidget

    def initAdvancedWidget(self):
        """Builds the Advanced GUI (self.advancedWidget) """
        parent = QtWidgets.QWidget(parent=self)
        self.advancedWidget = GuiAdvanced(parent=parent, properties=self.properties, toolsetWidget=self,
                                          directory=self.directory, uniformIcons=self.uniformIcons)
        return self.advancedWidget

    def postContentSetup(self):
        """Last of the initizialize code"""
        self.uiconnections()
        self.disableStartEndFrame()  # set embed window int boxes disabled state

    def currentWidget(self):
        """ Current active widget

        :return:
        :rtype:  AllWidgets
        """
        return super(ModelAssets, self).currentWidget()

    def widgets(self):
        """ List of widgets

        :return:
        :rtype: list[AllWidgets]
        """
        return super(ModelAssets, self).widgets()

    # ------------------------------------
    # PROPERTIES
    # ------------------------------------

    def initializeProperties(self):
        return [{"name": "rendererIconMenu", "label": "", "value": "Arnold"}]

    def updateFromProperties(self):
        """ Runs update properties from the base class.

        Widgets will auto update from self.properties if linked via:

            self.linkProperty(widget, "propertyKey")
            or
            self.toolsetWidget.linkProperty(widget, "propertyKey")

        Add code after super() useful for changes such as forcing UI decimal places
        or manually adding unsupported widgets
        """
        super(ModelAssets, self).updateFromProperties()

    # ------------------------------------
    # POPUP WINDOWS
    # ------------------------------------

    def ui_loadRenderer(self):
        message = "The {} renderer isn't loaded. Load now?".format(self.properties.rendererIconMenu.value)
        # parent is None to parent to Maya to fix stylesheet issues
        okPressed = elements.MessageBox_ok(windowName="Load Renderer", parent=None, message=message)
        return okPressed

    # ------------------------------------
    # UTILS
    # ------------------------------------

    def setPrefVariables(self):
        """Sets prefs global variables from the prefs json file
        self.directory : the current folder location for the assets
        self.uniformIcons : bool whether the thumb icons should be square or non square
        """
        if not self.modelAssetsPrefsData.isValid():  # should be very rare
            om2.MGlobal.displayError("The preferences object is not valid")
            return
        self.directory = self.modelAssetsPrefsData["settings"][ac.PREFS_KEY_MODEL_ASSETS]
        self.uniformIcons = self.modelAssetsPrefsData["settings"][ac.PREFS_KEY_MODEL_UNIFORM]

    # ------------------------------------
    # THUMBNAIL
    # ------------------------------------

    def refreshThumbs(self):
        """Refreshes the GUI """
        self.currentWidget().miniBrowser.refreshThumbs()

    # ------------------------------------
    # RENDERER - AND SEND/RECEIVE ALL TOOLSETS
    # ------------------------------------

    def checkRenderLoaded(self, renderer):
        """Checks that the renderer is loaded, if not opens a window asking the user to load it

        :param renderer: the nice name of the renderer "Arnold" or "Redshift" etc
        :type renderer: str
        :return rendererLoaded: True if the renderer is loaded
        :rtype rendererLoaded: bool
        """
        logger.debug("checkRenderLoaded()")
        if not rendererload.getRendererIsLoaded(renderer):
            okPressed = self.ui_loadRenderer()
            if okPressed:
                rendererload.loadRenderer(renderer)
                return True
            return False
        return True

    def global_changeRenderer(self):
        """Updates all GUIs with the current renderer"""
        toolsets = toolsetui.toolsets(attr="global_receiveRendererChange")
        for tool in toolsets:
            tool.global_receiveRendererChange(self.properties.rendererIconMenu.value)
        # save renderer to the general settings preferences .pref json
        self.generalSettingsPrefsData = preference.findSetting(pc.RELATIVE_PREFS_FILE, None)  # refresh data

        if not self.generalSettingsPrefsData.isValid():  # should be very rare
            om2.MGlobal.displayError("The preferences object is not valid")
            return
        self.generalSettingsPrefsData[pc.PREFS_KEY_RENDERER] = self.properties.rendererIconMenu.value
        self.generalSettingsPrefsData.save(indent=True)  # save and format nicely
        om2.MGlobal.displayInfo("Preferences Saved: Global renderer saved as "
                                "`{}`".format(self.properties.rendererIconMenu.value))

    def global_receiveRendererChange(self, renderer):
        """Receives from other GUIs, changes the renderer when it is changed"""
        self.properties.rendererIconMenu.value = renderer
        self.updateFromProperties()

    # ------------------------------------
    # DOTS MENU
    # ------------------------------------

    def exportGenericAlembic(self):
        """Exports all geo, cams and lights in the scene/selected as generic type .zooScene:

            - Objects.geo and cameras are saved as alembic
            - Lights saved as generic .zooLights
            - Shaders saved as generic .zooShaders

        """
        # Get UI data
        renderer = self.properties.rendererIconMenu.value
        exportSelected = not self.properties.fromSelectedRadio.value
        frameRange = ""
        if self.properties.animationRadio.value:
            frameRange = " ".join([str(self.properties.startFrameInt.value),
                                   str(self.properties.endFrameInt.value)])
        # Get Model Asset directory
        self.refreshPrefs()
        modelAssetsDirectory = self.modelAssetsPrefsData["settings"][ac.PREFS_KEY_MODEL_ASSETS]
        # Check can export
        if exportSelected and not cmds.ls(selection=True):
            om2.MGlobal.displayWarning("Nothing Selected, Please Select Object/s")
            return
        # Open the Save window
        fullFilePath = elements.SaveDialog(modelAssetsDirectory,
                                           fileExtension=exportabcshaderlights.ZOOSCENESUFFIX,
                                           nameFilters=[
                                               'ZOOSCENE (*.{})'.format(exportabcshaderlights.ZOOSCENESUFFIX)])
        # After the Save window
        if not fullFilePath:  # If window clicked cancel then cancel
            return ""
        # Save
        assetsimportexport.saveAsset(fullFilePath, renderer,
                                     exportSelected=exportSelected,
                                     exportShaders=True,
                                     exportLights=False,
                                     exportAbc=True,
                                     noMayaDefaultCams=True,
                                     exportGeo=True,
                                     exportCams=True,
                                     exportAll=False,
                                     dataFormat="ogawa",
                                     frameRange=frameRange,
                                     visibility=True,
                                     creases=True,
                                     uvSets=True,
                                     exportSubD=True)
        # Refresh browser UIs
        self.refreshThumbs()
        return fullFilePath

    def renameAsset(self):
        """Renames the asset on disk, can fail if alembic animation. Alembic animation must not be loaded"""
        currentFileNoSuffix = self.currentWidget().miniBrowser.itemFileName()
        if not currentFileNoSuffix:  # no image has been selected
            om2.MGlobal.displayWarning("Please select an asset thumbnail image to rename.")
            return
        message = "Rename Related `{}` Files As:".format(currentFileNoSuffix)
        renameText = elements.InputDialog(windowName="Rename Model Asset", textValue=currentFileNoSuffix, parent=None,
                                          message=message)
        if not renameText:
            return
        # Do the rename
        fileRenameList = zooscenefiles.renameZooSceneOnDisk(renameText, self.zooScenePath)
        if not fileRenameList:
            om2.MGlobal.displayWarning("Files could not be renamed, they are probably in use by the current scene. "
                                       "Do not have the renamed assets loaded in the scene, "
                                       "or check your file permissions.")
            return
        om2.MGlobal.displayInfo("Success: Files `{}*` Have Been Renamed To `{}*`".format(currentFileNoSuffix, renameText))
        self.refreshThumbs()

    def refreshPrefs(self):
        self.modelAssetsPrefsData = preference.findSetting(ac.RELATIVE_PREFS_FILE, None)  # refresh and update
        if not self.modelAssetsPrefsData.isValid():  # should be very rare
            om2.MGlobal.displayError("The preferences object is not valid")
            return False
        return True

    def openPresetFolder(self):
        """Opens a windows/osx/linux file browser with the model asset directory path"""
        success = self.refreshPrefs()
        if not success:
            return
        filesystem.openDirectory(self.modelAssetsPrefsData["settings"][ac.PREFS_KEY_MODEL_ASSETS])

    def setAssetQuickDirectory(self):
        """Browse to change/set the Model Asset Folder"""
        success = self.refreshPrefs()
        if not success:
            return
        directoryPath = self.modelAssetsPrefsData["settings"][ac.PREFS_KEY_MODEL_ASSETS]
        if not os.path.isdir(directoryPath):  # if dir doesn't exist set to home directory
            directoryPath = os.environ['HOME']
        newDirPath = QtWidgets.QFileDialog.getExistingDirectory(self, "Set the Model Asset folder", directoryPath)
        if not newDirPath:
            return
        self.modelAssetsPrefsData["settings"][ac.PREFS_KEY_MODEL_ASSETS] = newDirPath
        self.modelAssetsPrefsData.save()
        # update thumb model on both thumb widgets
        self.compactWidget.browserModel.setDirectory(newDirPath)  # does the refresh
        self.advancedWidget.browserModel.setDirectory(newDirPath)
        om2.MGlobal.displayInfo("Preferences Saved: Model Asset folder saved as "
                                "`{}`".format(newDirPath))

    def deletePresetPopup(self):
        """Popup window that asks the user if they want to delete the currently selected asset from disk?"""
        fileNameNoSuffix = self.currentWidget().browserModel.currentImage
        filenameWithSuffix = "{}.{}".format(fileNameNoSuffix, exportabcshaderlights.ZOOSCENESUFFIX)
        self.zooScenePath = os.path.join(self.currentWidget().browserModel.directory, filenameWithSuffix)
        # Build popup window
        message = "Warning: Delete the preset `{}` and it's dependencies?  " \
                  "This will permanently delete these file/s from disk?".format(filenameWithSuffix)
        result = elements.MessageBox_ok(windowName="Delete Asset From Disk?",
                                        message=message)  # None will parent to Maya
        # After answering Ok or cancel
        if result:  # Ok was pressed
            filesFullPathDeleted = zooscenefiles.deleteZooSceneFiles(self.zooScenePath, message=True)
            self.refreshThumbs()
            om2.MGlobal.displayInfo("Success, File/s Deleted: {}".format(filesFullPathDeleted))

    def uniformIconToggle(self, action):
        """ Toggles the state of the uniform icons

        :param action:
        :type action:
        :return:
        :rtype:
        """
        self.uniformIcons = action.isChecked()
        self.modelAssetsPrefsData["settings"][ac.PREFS_KEY_MODEL_UNIFORM] = self.uniformIcons
        self.modelAssetsPrefsData.save()
        self.refreshThumbs()

    # ------------------------------------
    # MANAGE IN SCENE
    # ------------------------------------

    def selectPackageRootGrpsInScene(self):
        """Selects all package asset grps from selected, if none found then tries from the UI selection
        """
        uiSelectedName = self.getImageNameWithoutExtension()
        assetsimportexport.selectZooAssetGrps(uiSelectedName=uiSelectedName)

    def getImageNameWithoutExtension(self):
        """Returns the name of the current selection in the browser without the file extension
        Handles the Maya version of the name which cannot have spaces etc

        :return uiSelectedName: the selection without file extension, Maya name with "_". None if nothing selected
        :rtype uiSelectedName: str
        """
        uiSelectedName = self.currentWidget().browserModel.currentImage
        if uiSelectedName:
            uiSelectedName = os.path.splitext(uiSelectedName)[0]
            uiSelectedName = namehandling.convertStringToMayaCompatibleStr(uiSelectedName)
        return uiSelectedName

    @undodecorator.undoDecorator
    def deleteAssetInScene(self):
        """Removes the package asset from the scene
        Tries the selected objects package, if not found will try the UI name matches
        * needs undo support
        """
        uiSelectedName = self.getImageNameWithoutExtension()  # TODO probably missing
        assetsimportexport.deleteZooAssetSelected(uiSelectedName=uiSelectedName)

    # ------------------------------------
    # ALEMBIC MANAGEMENT
    # ------------------------------------

    def loadAbcPopup(self):
        """The popup window if alembic plugins aren't loaded
        """
        message = "The Alembic (.abc) plugins need to be loaded. \nLoad Now?"
        result = elements.MessageBox_ok(windowName="Load Alembic Plugin?", message=message)  # None will parent to Maya
        if result:
            assetsimportexport.loadAbcPlugin()
        return result

    def checkAbcLoaded(self):
        """Checks if the alembic plugins are loaded
        """
        if not assetsimportexport.getPluginAbcLoaded()[0] or not assetsimportexport.getPluginAbcLoaded()[1]:
            result = self.loadAbcPopup()
            return result
        return True

    @undodecorator.undoDecorator
    def loopAbc(self):
        """Loops selected objects if they have alembic nodes with anim data.

        Tries the selected objects package, if not found will try the GUI name matches.
        """
        uiSelectedName = self.getImageNameWithoutExtension()
        alembicNodes = assetsimportexport.loopAbcSelectedAsset(cycleInt=1, uiSelectedName=uiSelectedName, message=True)
        if alembicNodes:
            om2.MGlobal.displayInfo("Alembic Nodes Set To Cycle: {}".format(alembicNodes))
        else:
            om2.MGlobal.displayWarning("No Alembic Nodes found via asset or mesh connections, please select")

    @undodecorator.undoDecorator
    def unLoopAbc(self):
        """Removes abc loop of selected objects if they have alembic nodes with anim data checks all selected meshes \
        and assets, sets to constant
        """
        uiSelectedName = self.getImageNameWithoutExtension()
        alembicNodes = assetsimportexport.loopAbcSelectedAsset(cycleInt=0, uiSelectedName=uiSelectedName, message=True)
        if alembicNodes:
            om2.MGlobal.displayInfo("Alembic Nodes Set To Constant: {}".format(alembicNodes))
        else:
            om2.MGlobal.displayWarning("No Alembic Nodes found via asset or mesh connections, please select")

    # ------------------------------------
    # SCALE ROTATE ASSETS
    # ------------------------------------

    @undodecorator.undoDecorator
    def scaleRotSelPackage(self, x=None, y=None):
        """Scales and rotates the selected objects package, if not found will try the UI name matches

        x and y values are for connected widgets
        """
        scaleValue = self.properties.scaleFloat.value
        rotYValue = self.properties.rotateFloat.value

        uiSelectedName = self.getImageNameWithoutExtension()
        assetsimportexport.scaleRotateAssetSelected(scaleValue, rotYValue, uiSelectedName, message=False)
        self.updateFromProperties()  # updates the UI

    def packageRotOffset(self, offset=15.0, neg=False):
        """Scales the rotate value by a potential multiplier, alt shift etc, then runs the scale/rotate function"""
        multiplier, reset = keyboardmouse.cntrlShiftMultiplier(shiftMultiply=5.0, ctrlMultiply=0.2, altMultiply=1.0)
        rotYValue = self.properties.rotateFloat.value
        if reset:
            self.properties.rotateFloat.value = 0.0
        else:
            if neg:
                offset = -offset
            if multiplier > 1:
                multiplier = 2.0  # dim faster value as 5.0 is too fast
            offset = offset * multiplier
            self.properties.rotateFloat.value = rotYValue + offset
        self.scaleRotSelPackage()  # Do the scale/rot and update UI

    def packageScaleOffset(self, offset=.1, neg=False):
        """Scales the scale value by a potential multiplier, alt shift etc, then runs the scale/rotate function"""
        multiplier, reset = keyboardmouse.cntrlShiftMultiplier(shiftMultiply=5.0, ctrlMultiply=0.2, altMultiply=1.0)
        scaleValue = self.properties.scaleFloat.value
        if reset:
            self.properties.scaleFloat.value = 1.0
        else:
            offset = offset * multiplier
            if neg:
                offset = - offset
            self.properties.scaleFloat.value = scaleValue + offset
        self.scaleRotSelPackage()  # Do the scale/rot and update UI

    # ------------------------------------
    # CREATE IMPORT ASSETS
    # ------------------------------------

    @undodecorator.undoDecorator
    def importAsset(self, assetName=""):
        """ Imports the zooScene asset given the GUI settings

        :param assetName:
        :type assetName:
        :return:
        :rtype:
        """
        logger.debug("importAsset()")
        currentImage = self.currentWidget().browserModel.currentImage
        if not currentImage:  # no image has been selected
            om2.MGlobal.displayWarning("Please select an asset thumbnail image.")
            return
        self.zooScenePath = os.path.join(self.currentWidget().browserModel.directory,
                                         "{}.{}".format(self.currentWidget().browserModel.currentImage,
                                                        exportabcshaderlights.ZOOSCENESUFFIX))
        # Renderer loaded?
        rendererNiceName = self.properties.rendererIconMenu.value
        if not self.checkRenderLoaded(rendererNiceName):
            return
        # Alembic loaded?
        abcState = self.checkAbcLoaded()
        if not abcState:
            return
        # Replace Assets
        replaceIndex = self.properties.replaceCombo.value
        if replaceIndex == 0:
            replaceAssets = True
            replaceByType = True
        elif replaceIndex == 1:
            replaceAssets = True
            replaceByType = False
        else:
            replaceAssets = False
            replaceByType = False
        # Do the import
        allNodes = assetsimportexport.importZooSceneAsAsset(self.zooScenePath,
                                                            rendererNiceName,
                                                            replaceAssets=replaceAssets,
                                                            importAbc=True,
                                                            importShaders=True,
                                                            importLights=True,
                                                            replaceShaders=False,
                                                            addShaderSuffix=True,
                                                            importSubDInfo=True,
                                                            replaceRoots=True,
                                                            turnStart=0,
                                                            turnEnd=0,
                                                            turnOffset=0.0,
                                                            loopAbc=self.properties.autoLoopCheckBox.value,
                                                            replaceByType=replaceByType,
                                                            rotYOffset=self.properties.rotateFloat.value,
                                                            scaleOffset=self.properties.scaleFloat.value)
        if allNodes:
            om2.MGlobal.displayInfo("Success: File Imported As An Asset")

    # ------------------------------------
    # GET (RETRIEVE) LIGHTS
    # ------------------------------------

    def fullRefreshUiAndThumbs(self):
        """Updates the UI and refreshes the thumbnail images, full refresh

        1. Gets all the attributes (properties) from the first selected light and updates the GUI
        2. Refreshes the Thumbnail images
        """
        # self.refreshUpdateUIFromSelection(update=True)  # update UI
        # self.refreshThumbs()  # refreshes the thumbnails
        pass

    # ------------------------------------
    # EMBED WINDOWS
    # ------------------------------------

    def setEmbedVisible(self, vis=False):
        """Shows and hides the saveEmbedWindow"""
        if not vis:
            pass
        self.currentWidget().saveEmbedWinContainer.setEmbedVisible(vis)

    # ------------------------------------
    # DISABLE ENABLE
    # ------------------------------------

    def disableStartEndFrame(self):
        """Sets the disabled/enabled state of the Start and End frame int boxes
        """
        for uiInstance in self.widgets():
            uiInstance.startFrameInt.setDisabled(not self.properties.animationRadio.value)
            uiInstance.endFrameInt.setDisabled(not self.properties.animationRadio.value)

    # ------------------------------------
    # CONNECTIONS
    # ------------------------------------

    def uiconnections(self):
        """Hooks up the actual button/widgets functionality
        """
        logger.debug("connections()")
        for uiInstance in self.widgets():
            # dots menu viewer
            uiInstance.miniBrowser.dotsMenu.applyAction.connect(self.importAsset)
            uiInstance.miniBrowser.dotsMenu.createAction.connect(partial(self.setEmbedVisible, vis=True))
            uiInstance.saveModelAssetBtn.clicked.connect(self.exportGenericAlembic)  # does the save asset
            uiInstance.miniBrowser.dotsMenu.renameAction.connect(self.renameAsset)
            uiInstance.miniBrowser.dotsMenu.browseAction.connect(self.openPresetFolder)
            uiInstance.miniBrowser.dotsMenu.setDirectoryAction.connect(self.setAssetQuickDirectory)
            uiInstance.miniBrowser.dotsMenu.deleteAction.connect(self.deletePresetPopup)
            uiInstance.miniBrowser.dotsMenu.refreshAction.connect(self.refreshThumbs)
            uiInstance.miniBrowser.dotsMenu.uniformIconAction.connect(self.uniformIconToggle)
            # Thumbnail viewer
            uiInstance.browserModel.doubleClicked.connect(self.importAsset)
            # Offsets
            uiInstance.rotatePosBtn.clicked.connect(partial(self.packageRotOffset, neg=False))
            uiInstance.rotateNegBtn.clicked.connect(partial(self.packageRotOffset, neg=True))
            uiInstance.rotateFloat.textModified.connect(self.scaleRotSelPackage)
            uiInstance.scaleUpBtn.clicked.connect(partial(self.packageScaleOffset, neg=False))
            uiInstance.scaleDownBtn.clicked.connect(partial(self.packageScaleOffset, neg=True))
            uiInstance.scaleFloat.textModified.connect(self.scaleRotSelPackage)
            # Change renderer
            uiInstance.rendererIconMenu.actionTriggered.connect(self.global_changeRenderer)
            # Embed window
            uiInstance.animationRadio.toggled.connect(self.disableStartEndFrame)
            uiInstance.cancelSaveBtn.clicked.connect(partial(self.setEmbedVisible, vis=False))
            uiInstance.removeFromSceneBtn.clicked.connect(self.deleteAssetInScene)
            # Manage object in scene
            uiInstance.selectRootBtn.clicked.connect(self.selectPackageRootGrpsInScene)

        # Abc
        self.advancedWidget.loopAbcAnimationBtn.clicked.connect(self.loopAbc)
        self.advancedWidget.removeAbcLoopBtn.clicked.connect(self.unLoopAbc)

        # menu
        # self.advancedWidget.lightNameMenu.aboutToShow.connect(self.setLightNameMenuModes)


class AllWidgets(QtWidgets.QWidget):
    """Create all the widgets for all GUIs, compact and advanced etc"""

    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None, directory=None,
                 uniformIcons=True):
        """Builds the main widgets for the IBL light UIs, no layouts and no connections:

            uiMode - 0 is compact (UI_MODE_COMPACT)
            uiMode - 1 is medium (UI_MODE_MEDIUM)
            ui mode - 2 is advanced (UI_MODE_ADVANCED)

        properties is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        :param uiMode: 0 is compact ui mode, 1 is medium ui mode, 2 is advanced ui mode
        :type uiMode: int
        :param toolsetWidget: the widget of the toolset
        :type toolsetWidget: qtObject
        :param directory: directory path of the light preset zooScene files
        :type directory: str
        """
        super(AllWidgets, self).__init__(parent=parent)
        self.savedThumbHeight = None
        self.toolsetWidget = toolsetWidget
        self.properties = properties
        self.uiMode = uiMode
        # Thumbnail Viewer --------------------------------------------
        self.themePref = preference.interface("core_interface")
        # viewer widget and model
        self.miniBrowser = elements.MiniBrowser(parent=self,
                                                toolsetWidget=self.toolsetWidget,
                                                columns=3,
                                                fixedHeight=382,
                                                uniformIcons=uniformIcons,
                                                itemName="Asset",
                                                applyText="Import",
                                                applyIcon="packageAssets")
        self.miniBrowser.dotsMenu.setSnapshotActive(True)
        self.browserModel = zooscenemodel.ZooSceneViewerModel(self.miniBrowser,
                                                              directory=directory,
                                                              chunkCount=200,
                                                              uniformIcons=uniformIcons)
        self.miniBrowser.setModel(self.browserModel)
        self.resizerWidget = ToolsetResizer(toolsetWidget=self.toolsetWidget, target=self.miniBrowser)
        # Replace Combo --------------------------------------
        toolTip = "Replace the imported asset by \n" \
                  " Type: Replaces any other assets where the asset type matches, see the info section\n" \
                  " All:  Replaces all assets in the scene \n" \
                  " Add: Does not replace, only adds new assets"
        self.replaceCombo = elements.ComboBoxRegular(items=REPLACE_COMBO, toolTip=toolTip)
        # Scale --------------------------------------
        toolTip = "Scale the current selected asset"
        self.scaleFloat = elements.FloatEdit("Scale",
                                              "1.0",
                                              labelRatio=2,
                                              editRatio=3,
                                              toolTip=toolTip)
        toolTip = "Scale the current asset smaller\n" \
                  "(Shift faster, ctrl slower, alt reset)"
        self.scaleDownBtn = elements.styledButton("", "scaleDown",
                                                  self,
                                                  toolTip=toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=uic.BTN_W_ICN_MED)
        toolTip = "Scale the current asset larger\n" \
                  "(Shift faster, ctrl slower, alt reset)"
        self.scaleUpBtn = elements.styledButton("",
                                                "scaleUp",
                                                toolTip=toolTip,
                                                style=uic.BTN_TRANSPARENT_BG,
                                                minWidth=uic.BTN_W_ICN_MED)
        # Rotation --------------------------------------
        toolTip = "Rotate the current selected asset"
        self.rotateFloat = elements.FloatEdit("Rotate",
                                               "0.0",
                                               toolTip=toolTip)
        toolTip = "Rotate the current asset in degrees\n" \
                  "(Shift faster, ctrl slower, alt reset)"
        self.rotatePosBtn = elements.styledButton("",
                                                  "arrowRotLeft",
                                                  toolTip=toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=uic.BTN_W_ICN_MED)
        self.rotateNegBtn = elements.styledButton("", "arrowRotRight",
                                                  toolTip=toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=uic.BTN_W_ICN_MED)
        # Renderer Button --------------------------------------
        toolTip = "Change the Renderer to Arnold, Redshift or Renderman"
        self.rendererIconMenu = elements.iconMenuButtonCombo(DFLT_RNDR_MODES,
                                                             self.properties.rendererIconMenu.value,
                                                             toolTip=toolTip)
        self.saveEmbedWinContainer = self.saveModelAssetEmbedWin(parent)
        if uiMode == UI_MODE_COMPACT:
            #  Delete Select Label
            self.delSelectLabel = elements.Label(text="Select/Delete")

        # Remove From Scene Button --------------------------------------
        toolTip = "Deletes the selected asset from scene. \n" \
                  "Asset can be selected in the 3d view or in the GUI."
        if uiMode == UI_MODE_COMPACT:
            self.removeFromSceneBtn = elements.styledButton("",
                                                            icon="crossXFat",
                                                            toolTip=toolTip,
                                                            style=uic.BTN_LABEL_SML)
        if uiMode == UI_MODE_ADVANCED:
            self.removeFromSceneBtn = elements.styledButton("Delete From Scene",
                                                            icon="crossXFat",
                                                            toolTip=toolTip,
                                                            style=uic.BTN_LABEL_SML)
        # Select Root Button --------------------------------------
        toolTip = "Selects the root froup of the current asset. \n" \
                  "Select any part of an asset in the 3d viewport or the GUI and run."
        if self.uiMode == UI_MODE_COMPACT:
            self.selectRootBtn = elements.styledButton("",
                                                       icon="cursorSelect",
                                                       toolTip=toolTip,
                                                       style=uic.BTN_LABEL_SML)
        if self.uiMode == UI_MODE_ADVANCED:  # widgets that only exist in the advanced mode
            # Select Root Button --------------------------------------
            self.selectRootBtn = elements.styledButton("Select Root",
                                                       icon="cursorSelect",
                                                       toolTip=toolTip,
                                                       style=uic.BTN_LABEL_SML)
            # Loop ABC Button --------------------------------------
            toolTip = "Loop an alembic asset if is has animation, cycle animation will loop.\n" \
                      "Select any part of an asset in the 3d viewport or the GUI and run."
            self.loopAbcAnimationBtn = elements.styledButton("Loop .abc Animation",
                                                             icon="loopAbc",
                                                             toolTip=toolTip,
                                                             style=uic.BTN_LABEL_SML)
            # Loop ABC Button --------------------------------------
            toolTip = "Remove looping alembic animation, if animation exists on the asset.\n" \
                      "Select any part of an asset in the 3d viewport or the GUI and run."
            self.removeAbcLoopBtn = elements.styledButton("Remove .abc Loop",
                                                          icon="removeLoop",
                                                          toolTip=toolTip,
                                                          style=uic.BTN_LABEL_SML)
            # Auto Loop Button --------------------------------------
            toolTip = "On import cycle any imported animation"
            self.autoLoopCheckBox = elements.CheckBox("Auto Loop",
                                                      checked=False,
                                                      toolTip=toolTip)

    def saveModelAssetEmbedWin(self, parent=None):
        """The popup properties UI embedded window for saving assets

        :param parent: the parent widget
        :type parent: Qt.object
        """
        toolTip = "Close the save window"
        self.hidePropertiesBtn = elements.styledButton("",
                                                       "closeX",
                                                       toolTip=toolTip,
                                                       maxWidth=uic.BTN_W_ICN_SML,
                                                       minWidth=uic.BTN_W_ICN_SML,
                                                       style=uic.BTN_TRANSPARENT_BG)
        saveEmbedWindow = elements.EmbeddedWindow(title="Create Asset From Scene",
                                                  closeButton=self.hidePropertiesBtn,
                                                  margins=(0, uic.SMLPAD, 0, uic.REGPAD),
                                                  uppercase=True,
                                                  resizeTarget=self.miniBrowser)
        saveEmbedWindow.visibilityChanged.connect(self.embedWindowVisChanged)

        self.saveEmbedWinLayout = saveEmbedWindow.getLayout()
        self.saveEmbedWinLbl = saveEmbedWindow.getTitleLbl()
        # Current Frame Radio ------------------------------
        toolTipList = ["", ""]
        radioList = ["Current Frame", "Animation"]
        self.animationRadio = elements.RadioButtonGroup(radioList=radioList,
                                                        toolTipList=toolTipList,
                                                        default=0,
                                                        margins=(0, uic.REGPAD, 0, uic.REGPAD),
                                                        spacing=uic.LRGPAD)
        # Start End Frame Txt ------------------------------
        toolTip = ""
        self.startFrameInt = elements.IntEdit("Start",
                                                 editText=0,
                                                 editRatio=2,
                                                 labelRatio=1,
                                                 toolTip=toolTip, )
        toolTip = ""
        self.endFrameInt = elements.IntEdit("End",
                                               editText=100,
                                               editRatio=2,
                                               labelRatio=1,
                                               toolTip=toolTip, )
        # From Selected Radio ------------------------------
        toolTipList = ["", ""]
        radioList = ["From Selected", "Save From Scene"]
        self.fromSelectedRadio = elements.RadioButtonGroup(radioList=radioList,
                                                           toolTipList=toolTipList,
                                                           default=0,
                                                           margins=(0, uic.REGPAD, 0, uic.REGPAD),
                                                           spacing=uic.LRGPAD)
        # Save Button -------------------------------------
        toolTip = ""
        self.saveModelAssetBtn = elements.styledButton("Create Asset",
                                                       icon="save",
                                                       toolTip=toolTip,
                                                       style=uic.BTN_DEFAULT)
        # Cancel Button -------------------------------------
        toolTip = ""
        self.cancelSaveBtn = elements.styledButton("Cancel",
                                                   icon="xMark",
                                                   toolTip=toolTip,
                                                   style=uic.BTN_DEFAULT)
        # start end frame layout -------------------------------------
        startEndFrameLayout = elements.hBoxLayout(spacing=uic.LRGPAD)
        startEndFrameLayout.addWidget(self.startFrameInt)
        startEndFrameLayout.addWidget(self.endFrameInt)
        # save Button  layout -------------------------------------
        saveButtonLayout = elements.hBoxLayout()
        saveButtonLayout.addWidget(self.saveModelAssetBtn)
        saveButtonLayout.addWidget(self.cancelSaveBtn)
        # add to main layout -------------------------------------
        self.saveEmbedWinLayout.addWidget(self.animationRadio)
        self.saveEmbedWinLayout.addLayout(startEndFrameLayout)
        self.saveEmbedWinLayout.addWidget(self.fromSelectedRadio)
        self.saveEmbedWinLayout.addLayout(saveButtonLayout)
        return saveEmbedWindow

    def embedWindowVisChanged(self, visibility):
        self.toolsetWidget.updateTree(delayed=True)


class GuiCompact(AllWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None, directory=None,
                 uniformIcons=True):
        """Builds the compact version of GUI, sub classed from AllWidgets() which creates the widgets:

            default uiMode - 1 is compact (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: Special dictionary which tracks the properties of each widget for the GUI
        :type properties: list[dict]
        :param uiMode: The UI mode to build, either UI_MODE_COMPACT = 0 or UI_MODE_ADVANCED = 1
        :type uiMode: int
        :param toolsetWidget: The instance of the toolsetWidget class, needed for setting properties.
        :type toolsetWidget: object
        """
        super(GuiCompact, self).__init__(parent=parent, properties=properties,
                                         uiMode=uiMode, toolsetWidget=toolsetWidget, directory=directory,
                                         uniformIcons=uniformIcons)
        # Main Layout
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=0)
        # Renderer layout
        rendererLayout = elements.hBoxLayout()
        rendererLayout.addWidget(self.delSelectLabel, 9)
        rendererLayout.addWidget(self.selectRootBtn, 1)
        rendererLayout.addWidget(self.removeFromSceneBtn, 1)
        rendererLayout.addWidget(self.rendererIconMenu, 1)
        # Rotate layout
        rotateLayout = elements.hBoxLayout()
        rotateLayout.addWidget(self.rotateFloat, 9)
        rotateLayout.addWidget(self.rotatePosBtn, 1)
        rotateLayout.addWidget(self.rotateNegBtn, 1)
        # Scale layout
        scaleLayout = elements.hBoxLayout()
        scaleLayout.addWidget(self.scaleFloat, 9)
        scaleLayout.addWidget(self.scaleDownBtn, 1)
        scaleLayout.addWidget(self.scaleUpBtn, 1)
        # Grid Layout
        gridLayout = elements.GridLayout(margins=(0, 0, 0, 0), hSpacing=uic.SVLRG, vSpacing=uic.SREG)
        gridLayout.addWidget(self.replaceCombo, 0, 0)
        gridLayout.addLayout(rendererLayout, 0, 1)
        gridLayout.addLayout(rotateLayout, 1, 0)
        gridLayout.addLayout(scaleLayout, 1, 1)
        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)
        # Add to main layout
        mainLayout.addWidget(self.saveEmbedWinContainer)  # will be hidden
        mainLayout.addWidget(self.miniBrowser)
        mainLayout.addWidget(self.resizerWidget)
        mainLayout.addLayout(gridLayout)
        mainLayout.addStretch(1)


class GuiAdvanced(AllWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_ADVANCED, toolsetWidget=None, directory=None,
                 uniformIcons=True):
        """Builds the advanced version of GUI, subclassed from AllWidgets() which creates the widgets:

            default uiMode - 1 is advanced (UI_MODE_ADVANCED)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: Special dictionary which tracks the properties of each widget for the GUI
        :type properties: list[dict]
        :param uiMode: The UI mode to build, either UI_MODE_COMPACT = 0 or UI_MODE_ADVANCED = 1
        :type uiMode: int
        :param toolsetWidget: The instance of the toolsetWidget class, needed for setting properties.
        :type toolsetWidget: object
        """
        super(GuiAdvanced, self).__init__(parent=parent, properties=properties,
                                          uiMode=uiMode, toolsetWidget=toolsetWidget, directory=directory,
                                          uniformIcons=uniformIcons)
        # Main Layout
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=0)
        # Renderer layout
        rendererLayout = elements.hBoxLayout()
        rendererLayout.addWidget(self.autoLoopCheckBox, 9)
        rendererLayout.addWidget(self.rendererIconMenu, 1)
        # Rotate layout
        rotateLayout = elements.hBoxLayout()
        rotateLayout.addWidget(self.rotateFloat, 3)
        rotateLayout.addWidget(self.rotatePosBtn, 1)
        rotateLayout.addWidget(self.rotateNegBtn, 1)
        # Scale layout
        scaleLayout = elements.hBoxLayout()
        scaleLayout.addWidget(self.scaleFloat, 3)
        scaleLayout.addWidget(self.scaleDownBtn, 1)
        scaleLayout.addWidget(self.scaleUpBtn, 1)
        # Grid Layout
        gridLayout = elements.GridLayout(margins=(0, 0, 0, 0), hSpacing=uic.SVLRG, vSpacing=uic.SREG)
        gridLayout.addWidget(self.selectRootBtn, 0, 0)
        gridLayout.addWidget(self.removeFromSceneBtn, 0, 1)
        gridLayout.addWidget(self.loopAbcAnimationBtn, 1, 0)
        gridLayout.addWidget(self.removeAbcLoopBtn, 1, 1)
        gridLayout.addWidget(self.replaceCombo, 2, 0)
        gridLayout.addLayout(rendererLayout, 2, 1)
        gridLayout.addLayout(rotateLayout, 3, 0)
        gridLayout.addLayout(scaleLayout, 3, 1)
        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)
        # Add to main layout
        mainLayout.addWidget(self.saveEmbedWinContainer)  # will be hidden
        mainLayout.addWidget(self.miniBrowser)
        mainLayout.addWidget(self.resizerWidget)
        mainLayout.addLayout(gridLayout)
        mainLayout.addStretch(1)
