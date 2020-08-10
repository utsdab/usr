import os
from functools import partial

import maya.api.OpenMaya as om2

from zoo.libs.zooscene import zooscenefiles
from Qt import QtWidgets, QtCore

from zoo.apps.light_suite import prefsdata
from zoo.apps.light_suite import lightconstants as lc
from zoo.preferences import preferencesconstants as pc
from zoo.apps.light_suite import assetdirectories

from zoo.libs.zooscene.constants import ZOOSCENE_EXT

from zoo.apps.toolsetsui.widgets.toolsetresizer import ToolsetResizer
from zoo.apps.toolsetsui import toolsetui
from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya

from zoo.libs.maya.cmds.general import undodecorator
from zoo.libs.maya.cmds.lighting import renderertransferlights
from zoo.libs.maya.cmds.lighting.renderertransferlights import LIGHTVISIBILITY
from zoo.libs.maya.cmds.objutils import scaleutils
from zoo.libs.maya.cmds.renderer import exportabcshaderlights, rendererload

from zoo.libs.pyqt.extended.imageview.models import zooscenemodel
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.utils import zlogging
from zoo.libs.utils import filesystem
from zoo.preferences.core import preference

THEME_PREFS = preference.interface("core_interface")

logger = zlogging.getLogger(__name__)

DFLT_RNDR_MODES = [("arnold", "Arnold"), ("redshift", "Redshift"), ("renderman", "Renderman")]
UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

DFLT_RNDR_MODE = "Arnold"


class LightPresets(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "lightPresets"
    uiData = {"label": "Light Presets",
              "icon": "lightstudio",
              "tooltip": "Miniature version of the Light Presets Browser",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-light-presets/"
              }

    # ------------------------------------
    # START UP
    # ------------------------------------

    def preContentSetup(self):
        """First code to run"""
        self.toolsetWidget = self  # needed for callback decorators
        self.lightData = prefsdata.LightSuitePreferences()  # the lightData, prefsData objs for retrieving files
        self.lightSuitePrefsData = self.lightData.getPrefsData()  # light suite preferences
        self.generalSettingsPrefsData = preference.findSetting(pc.RELATIVE_PREFS_FILE, None)  # renderer in general pref
        self.properties.renderer.value = self.generalSettingsPrefsData[pc.PREFS_KEY_RENDERER]
        self.setPrefVariables()  # sets self.directory and self.uniformIcons
        if not self.directory:  # directory can be empty if preferences window hasn't been opened
            # so update the preferences json file with default locations
            self.lightSuitePrefsData = assetdirectories.buildUpdateLightPrefs(self.lightSuitePrefsData)
            self.setPrefVariables()

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]

    def initCompactWidget(self):
        parent = QtWidgets.QWidget(parent=self)
        self.parentWgt = parent
        self.compactWidget = GuiCompact(parent=parent, properties=self.properties, toolsetWidget=self,
                                        directory=self.directory, uniformIcons=self.uniformIcons)
        return self.compactWidget

    def initAdvancedWidget(self):
        return  # disabled
        parent = QtWidgets.QWidget(parent=self)
        self.advancedWidget = GuiAdvanced(parent=parent, properties=self.properties, toolsetWidget=self,
                                          directory=self.directory, uniformIcons=self.uniformIcons)
        return self.advancedWidget

    def postContentSetup(self):
        """Last of the initizialize code"""
        self.presetPath = ""  # This is the path of the selected image
        self.ignoreInstantApply = False  # For instant apply directional lights and switching ui modes
        self.listeningForRenderer = True  # If True the renderer can be set from other windows or toolsets
        self.updateFromProperties()
        self.uiConnections()

    def currentWidget(self):
        """ Current active widget

        :return:
        :rtype:  AllWidgets
        """
        return super(LightPresets, self).currentWidget()

    def widgets(self):
        """ List of widgets

        :return:
        :rtype: list[AllWidgets]
        """
        return super(LightPresets, self).widgets()

    # ------------------------------------
    # PROPERTIES
    # ------------------------------------

    def initializeProperties(self):
        return [{"name": "scale", "label": "Scale (cms)", "value": 180.00},
                {"name": "rotationOffset", "label": "Rotation Offset", "value": 0.00},
                {"name": "intensity", "label": "Intensity", "value": 1.00},
                {"name": "backgroundVisibility", "label": "Background Visibility", "value": False},
                {"name": "instantApply", "label": "Instant Apply", "value": True},
                {"name": "deleteLightsCheckBx", "label": "Delete Lights", "value": True},
                {"name": "renderer", "label": "", "value": "Arnold"}]

    def updateFromProperties(self):
        """ Runs update properties from the base class.

        Widgets will auto update from self.properties if linked via:

            self.linkProperty(widget, "propertyKey")
            or
            self.toolsetWidget.linkProperty(widget, "propertyKey")

        Ignore this method unless unsupported widgets are needed to update from properties.
        self.postupdateFromProperties() runs after this method and is useful for changes such as forcing UI decimal places
        """
        super(LightPresets, self).updateFromProperties()
        rememberInstantApply = self.ignoreInstantApply
        self.blockCallbacks(True)
        self.ignoreInstantApply = True
        for uiInstance in self.widgets():  # limit decimal places for intensity and rotation
            # update the decimal places from properties -----------------------------------
            uiInstance.scaleEdit.setText(self.properties.scale.value)
            uiInstance.rotEdit.setText(self.properties.rotationOffset.value)
            uiInstance.intensityEdit.setText(self.properties.intensity.value)
        self.ignoreInstantApply = rememberInstantApply
        self.blockCallbacks(False)

    # ------------------------------------
    # POPUP WINDOWS
    # ------------------------------------

    def ui_loadRenderer(self):
        message = "The {} renderer isn't loaded. Load now?".format(self.properties.renderer.value)
        # parent is None to parent to Maya to fix stylesheet issues
        okPressed = elements.MessageBox_ok(windowName="Load Renderer", parent=None, message=message)
        return okPressed

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
            # self.loadRendererPopup(renderer)
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
            tool.global_receiveRendererChange(self.properties.renderer.value)
        # save renderer to the general settings preferences .pref json
        self.generalSettingsPrefsData = preference.findSetting(pc.RELATIVE_PREFS_FILE, None)  # refresh data
        if not self.generalSettingsPrefsData.isValid():  # should be very rare
            om2.MGlobal.displayError("The preferences object is not valid")
            return
        self.generalSettingsPrefsData[pc.PREFS_KEY_RENDERER] = self.properties.renderer.value
        self.generalSettingsPrefsData.save(indent=True)  # save and format nicely
        om2.MGlobal.displayInfo("Preferences Saved: Global renderer saved as "
                                "`{}`".format(self.properties.renderer.value))

    def global_receiveRendererChange(self, renderer):
        """Receives from other GUIs, changes the renderer when it is changed"""
        self.properties.renderer.value = renderer
        self.updateFromProperties()

    # ------------------------------------
    # UTILITIES - PREFERENCES
    # ------------------------------------

    def setPrefVariables(self):
        """Sets prefs global variables from the prefs json file
        self.directory : the current folder location for the light presets
        self.uniformIcons : bool whether the thumb icons should be square or non square
        """
        if not self.lightSuitePrefsData.isValid():  # should be very rare
            om2.MGlobal.displayError("The preferences object is not valid")
            return
        self.directory = self.lightSuitePrefsData["settings"][lc.PREFS_KEY_PRESETS]
        self.uniformIcons = self.lightSuitePrefsData["settings"][lc.PREFS_KEY_PRESETS_UNIFORM]

    def openPresetFolder(self):
        """Opens a windows/osx/linux file browser with the IBL directory path"""
        self.lightSuitePrefsData = self.lightData.getUpdatedPrefsData()  # refresh and get update self.prefsData
        if not self.lightSuitePrefsData.isValid():  # should be very rare
            om2.MGlobal.displayError("The preferences object is not valid")
            return
        filesystem.openDirectory(self.lightSuitePrefsData["settings"][lc.PREFS_KEY_PRESETS])

    def thumbnailChangePresetsFolder(self):
        """Browse to change/set the IBL Skydome Folder"""
        self.lightSuitePrefsData = self.lightData.getUpdatedPrefsData()  # refresh and get update self.prefsData
        self.setPrefVariables()  # updates self.directory
        if not os.path.isdir(self.directory):  # if dir doesn't exist set to home directory
            om2.MGlobal.displayWarning("Preferences directory not found {}".format(self.directory))
        newDirPath = QtWidgets.QFileDialog.getExistingDirectory(self, "Set the Light Presets folder", self.directory)
        if not newDirPath:
            return
        # update prefs
        self.lightSuitePrefsData["settings"][lc.PREFS_KEY_PRESETS] = newDirPath
        self.lightSuitePrefsData.save()
        # update thumb model
        self.currentWidget().browserModel.setDirectory(newDirPath)  # does the refresh
        om2.MGlobal.displayInfo("Preferences Saved: Light Presets folder saved as "
                                "`{}`".format(newDirPath))

    # ------------------------------------
    # DOTS MENU
    # ------------------------------------

    def refreshThumbs(self):
        """Refreshes the thumbs for both thumb widgets advanced and compact"""
        self.currentWidget().miniBrowser.refreshThumbs()

    def saveLightPreset(self):
        """Saves all lights in the scene of the current renderer to a .zooScene generic file

        Saves with with the dialog window elements.SaveDialog() which uses Qt's QFileDialog

        :return fullFilePath: The full file path of the .json file created, empty string if cancelled
        :rtype fullFilePath: str
        """
        renderer = self.properties.renderer.value
        # check exist lights in the scene for the renderer
        areaLightShapeList, directionalLightShapeList, \
        skydomeShapeList = renderertransferlights.getAllLightShapesInScene(renderer)
        if not areaLightShapeList and not directionalLightShapeList and not skydomeShapeList:
            om2.MGlobal.displayWarning("No Lights Found To Export For {}".format(renderer))
            return
        self.lightData.refreshPrefsData()  # refresh update in case of changes
        lightPresetDirectory = self.lightSuitePrefsData["settings"][lc.PREFS_KEY_PRESETS]
        # Open the Save window
        fullFilePath = elements.SaveDialog(lightPresetDirectory,
                                           fileExtension=exportabcshaderlights.ZOOSCENESUFFIX,
                                           nameFilters=['ZOOSCENE (*.{})'.format(exportabcshaderlights.ZOOSCENESUFFIX)])
        # After the Save window
        if not fullFilePath:  # If window clicked cancel then cancel
            return ""
        exportabcshaderlights.exportAbcGenericShaderLights(fullFilePath,
                                                           rendererNiceName=renderer,
                                                           exportSelected=False,
                                                           exportShaders=False,
                                                           exportLights=True,
                                                           exportAbc=False,
                                                           noMayaDefaultCams=True,
                                                           exportGeo=False,
                                                           exportCams=False,
                                                           exportAll=True,
                                                           keepThumbnailOverride=True)
        # refresh
        om2.MGlobal.displayInfo("File and it's dependencies saved: {}".format(fullFilePath))
        self.refreshThumbs()
        return fullFilePath

    def getPresetFileFolders(self):
        """Return file information from the thumb widget"""
        lightPresetDirectory = self.currentWidget().browserModel.directory
        fileNoExt = self.currentWidget().browserModel.currentImage
        fileName = ".".join([fileNoExt, ZOOSCENE_EXT])
        zooSceneFullPath = os.path.join(lightPresetDirectory, fileName)
        return lightPresetDirectory, fileName, fileNoExt, zooSceneFullPath

    def renamePreset(self):
        """Opens a Rename Window and renames the current .zooScene file on disk while updating
        """
        # get the current directory
        lightPresetDirectory, fileName, fileNoExt, zooSceneFullPath = self.getPresetFileFolders()
        if not lightPresetDirectory:
            return
        # Open the rename window
        message = "Rename Related `{}` Files As:".format(fileNoExt)
        renameText = elements.InputDialog(windowName="Rename The Current Light Preset",
                                          textValue=fileNoExt,
                                          parent=None,
                                          message=message)
        # After rename window
        if not renameText:
            return
        # Renaming
        renameFilename = "{}.{}".format(renameText, ".", ZOOSCENE_EXT)
        if os.path.isfile(os.path.join(lightPresetDirectory, renameFilename)):
            om2.MGlobal.displayWarning("This filename already exists, please use a different name")
            return
        fileRenameList = zooscenefiles.renameZooSceneOnDisk(renameText, zooSceneFullPath)
        if not fileRenameList:
            om2.MGlobal.displayWarning("Files could not be renamed, they are most likely in use. "
                                       "Do not have the renamed assets loaded in the scene, or check file permissions.")
            return
        om2.MGlobal.displayInfo("Success: Files `{}*` Have Been Renamed To `{}*`".format(fileNoExt, renameText))
        self.refreshThumbs()

    def deletePreset(self):
        """Deletes the current preset, shows a popup window asking to confirm
        """
        lightPresetDirectory, fileName, fileNoExt, zooSceneFullPath = self.getPresetFileFolders()
        if not lightPresetDirectory:
            return
        message = "Warning: Delete the preset `{}` and it's dependencies?  " \
                  "This will permanently delete these file/s from disk?".format(fileNoExt)
        result = QtWidgets.QMessageBox.question(None, "Delete File?", message,
                                                QtWidgets.QMessageBox.Cancel | QtWidgets.QMessageBox.Ok)
        if result == QtWidgets.QMessageBox.Ok:
            filesFullPathDeleted = zooscenefiles.deleteZooSceneFiles(zooSceneFullPath, message=True)
            om2.MGlobal.displayInfo("Success, File/s Deleted: {}".format(filesFullPathDeleted))
        self.refreshThumbs()

    def refreshBrowserList(self):

        self.currentWidget().miniBrowser.refreshThumbs()
        om2.MGlobal.displayInfo("Success: Browser Refreshed `{}`".format(self.currentWidget().browserModel.directory))

    def uniformIconToggle(self, action):
        """Toggles the state of the uniform icons
        """
        # TODO should use the checked value instead of inverting, but doesn't work?
        self.uniformIcons = action.isChecked()
        self.lightSuitePrefsData["settings"][lc.PREFS_KEY_PRESETS_UNIFORM] = self.uniformIcons
        self.lightSuitePrefsData.save()
        self.refreshThumbs()

    # ------------------------------------
    # CREATE LIGHT PRESETS
    # ------------------------------------

    def getScaleSelected(self):
        """Gets the longest edge from a bounding box of the selected objects and updates the GUI
        """
        logger.debug("getScaleSelected()")
        longestEdge = scaleutils.getLongestEdgeMultipleSelObjs()
        if not longestEdge:
            return
        self.properties.scale.value = longestEdge
        self.updateFromProperties()
        self.presetInstantApply()

    # ------------------------------------
    # CREATE LIGHT PRESETS
    # ------------------------------------

    def presetInstantApply(self):
        """Creates/recreates the light presets checking if instant apply is on
        Now depreciated due to the thumbnail browser"""
        if not self.properties.instantApply.value:
            return
        logger.debug("presetInstantApply()")
        self.presetApply()

    @undodecorator.undoDecorator
    def applyPresetUndo(self, overideDeleteLights, renderer, presetPath, showIBL=False):
        """Creates the lights from the preset and handles Maya's undo queue"""
        logger.debug("applyPresetUndo()")
        # TODO should switch all updates over to os.environ['ZOO_PREFS_IBLS_PATH']
        os.environ['ZOO_PREFS_IBLS_PATH'] = self.lightData.getUpdatedPrefsData()["settings"][lc.PREFS_KEY_IBL]
        exportabcshaderlights.importLightPreset(presetPath, renderer, overideDeleteLights)
        allIblLightShapes = renderertransferlights.getIBLLightsInScene(renderer)
        if allIblLightShapes:  # check if IBL exists to apply the bgVisibility setting from the GUI
            lightDictAttributes = renderertransferlights.getSkydomeLightDictAttributes()  # dict with keys/empty values
            lightDictAttributes[LIGHTVISIBILITY] = showIBL
            renderertransferlights.setIblAttrAuto(lightDictAttributes, renderer, message=False)

    def presetApplyThumbnail(self):
        """Applies the thumbnail view image
        """
        try:
            self.presetPath = self.currentWidget().miniBrowser.itemFilePath()
            self.presetApply()
        except AttributeError:
            om2.MGlobal.displayWarning("Please select an image")

    def presetApply(self):
        """Creates/updates the lights from the preset from the GUI properties """
        logger.debug("presetApply()")
        if not self.presetPath:  # no image has been selected
            om2.MGlobal.displayWarning("Please select an image")
            return
        rendererNiceName = self.properties.renderer.value
        if not self.checkRenderLoaded(rendererNiceName):
            return
        overideDeleteLights = self.properties.deleteLightsCheckBx.value
        showIBL = self.properties.backgroundVisibility.value
        scale = self.properties.scale.value
        rot = self.properties.rotationOffset.value
        intensity = self.properties.intensity.value
        self.applyPresetUndo(overideDeleteLights, rendererNiceName, self.presetPath,
                             showIBL=showIBL)  # apply the preset
        scalePercentage = - (100 - ((scale / 180.0) * 100))
        # scale
        renderertransferlights.scaleAllLightsInScene(scalePercentage, rendererNiceName, scalePivot=(0.0, 0.0, 0.0),
                                                     ignoreNormalization=False, ignoreIbl=False, message=True)
        # rot
        renderertransferlights.rotLightGrp(rendererNiceName, rot, setExactRotation=True)
        # multiply the intensity
        intensityPercentage = (intensity - 1) * 100
        renderertransferlights.scaleAllLightsIntensitySelected(intensityPercentage, rendererNiceName,
                                                               applyExposure=True)

    # ------------------------------------
    # OFFSET BUTTONS
    # ------------------------------------

    def presetMultiplier(self):
        """For offset functions multiply shift and minimise if ctrl is held down
        If alt then call the reset option

        :return multiplier: multiply value, .2 if ctrl 5 if shift 1 if None
        :rtype multiplier: float
        :return reset: reset becomes true for resetting
        :rtype reset: bool
        """
        logger.debug("presetMultiplier()")
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            return 5.0, False
        elif modifiers == QtCore.Qt.ControlModifier:
            return 0.2, False
        elif modifiers == QtCore.Qt.AltModifier:
            return 1, True
        return 1.0, False

    def presetSetScale(self, neg=False):
        """Used when the offset buttons are pressed, set scale values

        Must rebuild the entire light setup
        :param neg: set to True while scaling smaller
        :type neg: bool
        """
        logger.debug("presetSetScale()")
        multiplier, reset = self.presetMultiplier()
        if reset:
            self.properties.scale.value = 180.0
        else:
            scale = self.properties.scale.value
            offset = 5.0 * multiplier
            if neg:
                offset = - offset
            self.properties.scale.value = scale * (1.0 + (offset / 100.0))
        self.updateFromProperties()
        self.presetInstantApply()

    def presetSetRot(self, neg=False):
        """Used when the offset buttons are pressed, set rotation values

        Must rebuild the entire light setup
        :param neg: set to True while rotating negatively
        :type neg: bool
        """
        logger.debug("presetSetRot()")
        multiplier, reset = self.presetMultiplier()
        if reset:
            self.properties.rotationOffset.value = 0.0
        else:
            rot = self.properties.rotationOffset.value
            if multiplier > 1.0:
                multiplier = 2.0  # dim the fast mode as it's too fast
            offset = 15.0 * multiplier
            if neg:
                offset = - offset
            self.properties.rotationOffset.value = rot + offset
        self.updateFromProperties()
        self.presetInstantApply()

    def presetSetIntensity(self, neg=False):
        """Used when the offset buttons are pressed, set intensity brighten/darken values

        Must rebuild the entire light setup
        :param neg: set to True while darkening the intensity
        :type neg: bool
        """
        logger.debug("presetSetIntensity()")
        multiplier, reset = self.presetMultiplier()
        if reset:
            self.properties.intensity.value = 1.0
        else:
            intensity = self.properties.intensity.value
            offset = .1 * multiplier
            if neg:
                offset = - offset
            self.properties.intensity.value = intensity + offset
        self.updateFromProperties()
        self.presetInstantApply()

    # ------------------------------------
    # DOUBLE CLICK ICON
    # ------------------------------------

    def command(self):
        """Double Click Icon Function
        """
        pass

    # ------------------------------------
    # CONNECTIONS
    # ------------------------------------

    def uiConnections(self):
        """Runs the add suffix command
        """
        for uiInstance in self.widgets():
            # dots menu viewer
            uiInstance.miniBrowser.dotsMenu.createAction.connect(self.saveLightPreset)
            uiInstance.miniBrowser.dotsMenu.renameAction.connect(self.renamePreset)
            uiInstance.miniBrowser.dotsMenu.deleteAction.connect(self.deletePreset)
            uiInstance.miniBrowser.dotsMenu.applyAction.connect(self.presetApplyThumbnail)
            uiInstance.miniBrowser.dotsMenu.browseAction.connect(self.openPresetFolder)
            uiInstance.miniBrowser.dotsMenu.setDirectoryAction.connect(self.thumbnailChangePresetsFolder)
            uiInstance.miniBrowser.dotsMenu.refreshAction.connect(self.refreshBrowserList)
            uiInstance.miniBrowser.dotsMenu.uniformIconAction.connect(self.uniformIconToggle)
            # widget changes
            uiInstance.scaleEdit.textModified.connect(self.presetInstantApply)
            uiInstance.rotEdit.textModified.connect(self.presetInstantApply)
            uiInstance.intensityEdit.textModified.connect(self.presetInstantApply)
            uiInstance.bgVisCheckBx.stateChanged.connect(self.presetInstantApply)
            # thumbnail viewer
            uiInstance.browserModel.doubleClicked.connect(self.presetApplyThumbnail)
            # offset buttons
            uiInstance.scaleDownBtn.clicked.connect(partial(self.presetSetScale, neg=True))
            uiInstance.scaleUpBtn.clicked.connect(self.presetSetScale)
            uiInstance.rotNegBtn.clicked.connect(partial(self.presetSetRot, neg=True))
            uiInstance.rotPosBtn.clicked.connect(self.presetSetRot)
            uiInstance.darkenBtn.clicked.connect(partial(self.presetSetIntensity, neg=True))
            uiInstance.brightenBtn.clicked.connect(self.presetSetIntensity)
            # change renderer
            uiInstance.rendererLoaded.actionTriggered.connect(self.global_changeRenderer)
            uiInstance.scaleFromBtn.clicked.connect(self.getScaleSelected)


class AllWidgets(QtWidgets.QWidget):
    """Create all the widgets for all GUIs, compact and advanced etc"""

    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None, directory=None,
                 uniformIcons=True):
        """Builds the main widgets for the Mini Light Presets UIs, no layouts and no connections:

            uiMode - 0 is compact (UI_MODE_COMPACT)
            ui mode - 1 is advanced (UI_MODE_ADVANCED)

        "properties" is the list(dictionaries) used to set logic and pass between the different UI layouts
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
        self.toolsetWidget = toolsetWidget
        self.properties = properties
        self.uiMode = uiMode
        self.parentWidget = parent
        # Thumbnail Viewer ---------------------------------------
        self.themePref = preference.interface("core_interface")
        self.miniBrowser = elements.MiniBrowser(parent=self, toolsetWidget=self.toolsetWidget, fixedHeight=382,
                                                columns=3,
                                                uniformIcons=uniformIcons, itemName="Preset",
                                                applyIcon="lightstudio",
                                                createText="Save",
                                                createThumbnailActive=True)
        self.miniBrowser.dotsMenu.setSnapshotActive(True)
        self.browserModel = zooscenemodel.ZooSceneViewerModel(self.miniBrowser, directory=directory, chunkCount=200,
                                                              uniformIcons=uniformIcons)
        self.miniBrowser.setModel(self.browserModel)
        self.resizerWidget = ToolsetResizer(parent=self, toolsetWidget=self.toolsetWidget, target=self.miniBrowser)
        # Scale --------------------------------------
        toolTip = "Import light presets for models at this scale\n180cm (Maya units) is the default size\n" \
                  "Presets should be saved at 180cm to fit the subject"
        if self.uiMode == UI_MODE_ADVANCED:
            editRatio = 74
            labelRatio = 100
            self.scaleEdit = elements.FloatEdit(self.properties.scale.label,
                                                self.properties.scale.value,
                                                parent=self,
                                                editWidth=None,
                                                labelRatio=labelRatio,
                                                editRatio=editRatio,
                                                rounding=2,
                                                toolTip=toolTip)
        if self.uiMode == UI_MODE_COMPACT:
            editRatio = 1
            labelRatio = 1

            self.scaleEdit = elements.FloatEdit("Scale cms",
                                                self.properties.scale.value,
                                                parent=self,
                                                editWidth=None,
                                                labelRatio=labelRatio,
                                                editRatio=editRatio,
                                                rounding=2,
                                                toolTip=toolTip)

        self.toolsetWidget.linkProperty(self.scaleEdit, "scale")

        toolTip = "Get the scale size of the current object/grp selection\nScale is measured from the longest axis"
        self.scaleFromBtn = elements.styledButton("",
                                                  "arrowLeft",
                                                  self,
                                                  toolTip=toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=15)
        toolTip = "Scale all lights smaller from world center\n(Shift faster, ctrl slower, alt reset)\n" \
                  "Rebuilds the light preset, changes will be lost"
        self.scaleDownBtn = elements.styledButton("",
                                                  "scaleDown",
                                                  self,
                                                  toolTip=toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=15)
        toolTip = "Scale all lights larger from world center\n(Shift faster, ctrl slower, alt reset)\n" \
                  "Rebuilds the light preset, changes will be lost"
        self.scaleUpBtn = elements.styledButton("",
                                                "scaleUp",
                                                self,
                                                toolTip=toolTip,
                                                style=uic.BTN_TRANSPARENT_BG,
                                                minWidth=15)
        # Rotation --------------------------------------
        toolTip = "The rotate offset in degrees\nThe rotation offset is also applied when importing"
        self.rotEdit = elements.FloatEdit(self.properties.rotationOffset.label,
                                          self.properties.rotationOffset.value,
                                          parent=self,
                                          editWidth=None,
                                          labelRatio=1,
                                          editRatio=1,
                                          toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.rotEdit, "rotationOffset")

        if self.uiMode == UI_MODE_COMPACT:
            self.rotEdit.label.setText("Rotate")
        toolTip = "Rotate all lights from the light group\n(Shift faster, ctrl slower, alt reset)\n" \
                  "Rebuilds the light preset, changes will be lost"
        self.rotNegBtn = elements.styledButton("",
                                               "arrowRotLeft",
                                               self,
                                               toolTip=toolTip,
                                               style=uic.BTN_TRANSPARENT_BG,
                                               minWidth=uic.BTN_W_ICN_SML)
        self.rotPosBtn = elements.styledButton("",
                                               "arrowRotRight",
                                               self,
                                               toolTip=toolTip,
                                               style=uic.BTN_TRANSPARENT_BG,
                                               minWidth=15)
        # Intensity --------------------------------------
        toolTip = "The brightness offset\nBrightens/darkens light presets when imported, default is 1.0"
        self.intensityEdit = elements.FloatEdit(self.properties.intensity.label,
                                                self.properties.intensity.value,
                                                parent=self,
                                                editWidth=None,
                                                labelRatio=1,
                                                editRatio=1,
                                                toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.intensityEdit, "intensity")

        toolTip = "Darken all lights\n(Shift faster, ctrl slower, alt reset)\n" \
                  "Rebuilds the preset, changes will be lost"
        self.darkenBtn = elements.styledButton("",
                                               "darkenBulb",
                                               self,
                                               toolTip=toolTip,
                                               style=uic.BTN_TRANSPARENT_BG,
                                               minWidth=15)
        toolTip = "Brighten all lights in the preset\n(Shift faster, ctrl slower, alt reset)\n" \
                  "Rebuilds the preset, changes will be lost"
        self.brightenBtn = elements.styledButton("",
                                                 "brightenBulb",
                                                 self,
                                                 toolTip=toolTip,
                                                 style=uic.BTN_TRANSPARENT_BG,
                                                 minWidth=15)
        # Background Visibility --------------------------------------
        toolTip = "Render the skydome background on/off, if it exists in the current preset\n" \
                  "The skydome will continue to light the scene, the dome texture only will become invisible"
        self.bgVisCheckBx = elements.CheckBox(self.properties.backgroundVisibility.label,
                                              self.properties.backgroundVisibility.value,
                                              self,
                                              toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.bgVisCheckBx, "backgroundVisibility")

        if self.uiMode == UI_MODE_COMPACT:
            self.bgVisCheckBx.setText("Bg Vis")
        # Renderer Button --------------------------------------
        toolTip = "Set the default renderer"
        self.rendererLoaded = elements.iconMenuButtonCombo(DFLT_RNDR_MODES,
                                                           self.properties.renderer.value,
                                                           toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.rendererLoaded, "renderer")
        # Keep Lights Apply --------------------------------------
        # TODO names seem to conflict this is not a great feature
        toolTip = "Delete the lights while changing the light preset?  Recommended On."
        self.deleteLightsCheckBx = elements.CheckBox("Del",
                                                     self.properties.deleteLightsCheckBx.value,
                                                     self,
                                                     toolTip=toolTip)


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
        :param directory: directory path of the light preset zooScene files
        :type directory: str
        """
        super(GuiCompact, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                         toolsetWidget=toolsetWidget, directory=directory, uniformIcons=uniformIcons)
        # Main Layout --------------------------
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=0)
        # Grid Layout --------------------------
        attributesGridLayout = elements.GridLayout(margins=(0, 0, 0, 0), spacing=10)

        scaleBtnLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=10)
        scaleBtnLayout.addWidget(self.scaleDownBtn)
        scaleBtnLayout.addWidget(self.scaleUpBtn)

        rotBtnLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=10)
        rotBtnLayout.addWidget(self.rotNegBtn)
        rotBtnLayout.addWidget(self.rotPosBtn)

        intensityBtnLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=10)
        intensityBtnLayout.addWidget(self.darkenBtn)
        intensityBtnLayout.addWidget(self.brightenBtn)

        directoryRendererLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=10)
        directoryRendererLayout.addWidget(self.deleteLightsCheckBx)
        directoryRendererLayout.addWidget(self.rendererLoaded)

        attributesGridLayout.addWidget(self.scaleEdit, 0, 0)
        attributesGridLayout.addWidget(self.scaleFromBtn, 0, 1)
        attributesGridLayout.addLayout(scaleBtnLayout, 0, 2)
        attributesGridLayout.addWidget(self.rotEdit, 0, 3)
        attributesGridLayout.addLayout(rotBtnLayout, 0, 4)

        attributesGridLayout.addWidget(self.intensityEdit, 1, 0)
        attributesGridLayout.addLayout(intensityBtnLayout, 1, 2)
        attributesGridLayout.addWidget(self.bgVisCheckBx, 1, 3)
        attributesGridLayout.addLayout(directoryRendererLayout, 1, 4)

        attributesGridLayout.setColumnStretch(0, 100)
        attributesGridLayout.setColumnStretch(1, 1)
        attributesGridLayout.setColumnStretch(2, 3)
        attributesGridLayout.setColumnStretch(3, 70)
        attributesGridLayout.setColumnStretch(4, 3)

        # Assign To Main Layout --------------------------
        mainLayout.addWidget(self.miniBrowser)
        mainLayout.addWidget(self.resizerWidget)
        mainLayout.addLayout(attributesGridLayout)
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
        :param directory: directory path of the light preset zooScene files
        :type directory: str
        """
        super(GuiAdvanced, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                          toolsetWidget=toolsetWidget, directory=directory, uniformIcons=uniformIcons)

        # Main Layout --------------------------
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=0)
        # Grid Layout --------------------------
        attributesGridLayout = elements.GridLayout(margins=(0, 0, 0, uic.LRGPAD), spacing=uic.SREG,
                                                   columnMinWidth=(0, 180))
        # Scale Layout --------------------------
        scaleOptionsSmlLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SREG)
        scaleOptionsSmlLayout.addWidget(self.scaleEdit)
        scaleOptionsSmlLayout.addWidget(self.scaleFromBtn)
        # Bottom Checkbox Section --------------------------
        bottomCheckBxLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.REGPAD), spacing=uic.SREG)
        bottomCheckBxLayout.addItem(elements.Spacer(20, 0, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        bottomCheckBxLayout.addWidget(self.bgVisCheckBx)
        bottomCheckBxLayout.addWidget(self.deleteLightsCheckBx)
        bottomCheckBxLayout.addWidget(self.rendererLoaded)
        # Create Buttons Section --------------------------
        attributesGridLayout.addLayout(scaleOptionsSmlLayout, 0, 0)
        attributesGridLayout.addWidget(self.scaleDownBtn, 0, 1)
        attributesGridLayout.addWidget(self.scaleUpBtn, 0, 2)

        attributesGridLayout.addWidget(self.rotEdit, 1, 0)
        attributesGridLayout.addWidget(self.rotNegBtn, 1, 1)
        attributesGridLayout.addWidget(self.rotPosBtn, 1, 2)

        attributesGridLayout.addWidget(self.intensityEdit, 2, 0)
        attributesGridLayout.addWidget(self.darkenBtn, 2, 1)
        attributesGridLayout.addWidget(self.brightenBtn, 2, 2)
        # Assign To Main Layout --------------------------
        mainLayout.addWidget(self.miniBrowser)
        mainLayout.addWidget(self.resizerWidget)
        mainLayout.addLayout(attributesGridLayout)
        mainLayout.addLayout(bottomCheckBxLayout)
        mainLayout.addStretch(1)
