import os
from functools import partial

import maya.api.OpenMaya as om2
from Qt import QtWidgets
from zoo.apps.camera_tools import cameraconstants as cc
from zoo.apps.camera_tools import cameradirectories
from zoo.apps.toolsetsui import toolsetcallbacks
from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.apps.toolsetsui.widgets.toolsetresizer import ToolsetResizer
from zoo.libs.maya.cmds.cameras import imageplanes
from zoo.libs.maya.cmds.general import undodecorator
from zoo.libs.maya.cmds.objutils import attributes
from zoo.libs.pyqt import uiconstants as uic, keyboardmouse
from zoo.libs.pyqt.extended.imageview.models import filemodel
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import filesystem
from zoo.libs.utils import zlogging
from zoo.libs.zooscene import zooscenefiles
from zoo.preferences.core import preference

THEME_PREFS = preference.interface("core_interface")

logger = zlogging.getLogger(__name__)

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class ImagePlaneTool(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "imagePlaneTool"
    uiData = {"label": "Image Plane Tool",
              "icon": "imagePlane",
              "tooltip": "Mini browser for image planes",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-image-plane-tool/"
              }

    # ------------------------------------
    # START UP
    # ------------------------------------

    def preContentSetup(self):
        """First code to run"""
        self.toolsetWidget = self  # needed for callback decorators
        self.cameraToolsPrefsData = preference.findSetting(cc.RELATIVE_PREFS_FILE, None)  # camera .prefs info
        self.setPrefVariables()  # sets self.directory and self.uniformIcons
        if not self.directory:  # directory can be empty if preferences window hasn't been opened
            # so update the preferences json file with default locations
            self.cameraToolsPrefsData = cameradirectories.buildUpdateCameraAssetPrefs(self.cameraToolsPrefsData)
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

        self.ignoreInstantApply = False
        self.refreshUpdateUIFromSelection(update=True)  # update GUI from current in scene selection
        self.uiconnections()
        self.startSelectionCallback()  # start selection callback

    def currentWidget(self):
        """ Current active widget

        :return:
        :rtype:  AllWidgets
        """
        return super(ImagePlaneTool, self).currentWidget()

    def widgets(self):
        """ List of widgets

        :return:
        :rtype: list[AllWidgets]
        """
        return super(ImagePlaneTool, self).widgets()

    # ------------------------------------
    # PROPERTIES
    # ------------------------------------

    def initializeProperties(self):
        return [{"name": "rotate", "label": "Rotate", "value": 0.0},
                {"name": "scale", "label": "Scale", "value": 1.0},
                {"name": "offsetX", "label": "Offset X", "value": 0.0},
                {"name": "offsetY", "label": "Offset Y", "value": 0.0},
                {"name": "opacity", "label": "Opacity", "value": 1.0}]

    def updateFromProperties(self):
        """ Runs update properties from the base class.

        Widgets will auto update from self.properties if linked via:

            self.linkProperty(widget, "propertyKey")
            or
            self.toolsetWidget.linkProperty(widget, "propertyKey")

        Add code after super() useful for changes such as forcing UI decimal places
        or manually adding unsupported widgets
        """
        self.properties.offsetLeftRightFloatSldr.value = round(self.properties.offsetLeftRightFloatSldr.value, 3)
        self.properties.offsetUpDownFloatSldr.value = round(self.properties.offsetUpDownFloatSldr.value, 3)
        self.properties.opacityFloatSldr.value = round(self.properties.opacityFloatSldr.value, 3)
        super(ImagePlaneTool, self).updateFromProperties()

    # ------------------------------------
    # UTILS
    # ------------------------------------

    def setPrefVariables(self):
        """Sets prefs global variables from the prefs json file
        self.directory : the current folder location for the image planes
        self.uniformIcons : bool whether the thumb icons should be square or non square
        """
        if not self.cameraToolsPrefsData.isValid():  # should be very rare
            om2.MGlobal.displayError("The preferences object is not valid")
            return
        self.directory = self.cameraToolsPrefsData["settings"][cc.PREFS_KEY_IMAGEPLANE]
        self.uniformIcons = self.cameraToolsPrefsData["settings"][cc.PREFS_KEY_IMAGEP_UNIFORM]

    def refreshThumbs(self):
        """Refreshes the GUI """
        self.currentWidget().miniBrowser.refreshThumbs()

    def renameAsset(self):
        """Renames the asset on disk, can fail if alembic animation. Alembic animation must not be loaded"""
        currentImageNoExt = self.currentWidget().browserModel.currentImage
        self.zooScenePath = self.currentWidget().miniBrowser.itemFilePath()
        if not currentImageNoExt or self.zooScenePath is None:  # no image has been selected
            om2.MGlobal.displayWarning("Please select an image to rename.")
            return

        currentImageNoExt = os.path.splitext(currentImageNoExt)[0]
        message = "Rename `{}` and related dependencies as:".format(currentImageNoExt)
        renameText = elements.InputDialog(windowName="Rename Model Asset", textValue=currentImageNoExt, parent=None,
                                          message=message)
        if not renameText:
            return
        # Do the rename
        fileRenameList = zooscenefiles.renameZooSceneOnDisk(renameText, self.zooScenePath)
        if not fileRenameList:
            om2.MGlobal.displayWarning("Files could not be renamed, they are probably in use by the current scene. "
                                       "Do not have the images active in the scene, or check your file permissions.")
            return
        om2.MGlobal.displayInfo("Success: Files `{}*` Have Been Renamed To `{}*`".format(currentImageNoExt, renameText))
        self.refreshThumbs()

    def refreshPrefs(self):
        self.cameraToolsPrefsData = preference.findSetting(cc.RELATIVE_PREFS_FILE, None)  # refresh and update
        if not self.cameraToolsPrefsData.isValid():  # should be very rare
            om2.MGlobal.displayError("The preferences object is not valid")
            return False
        return True

    def openPresetFolder(self):
        """Opens a windows/osx/linux file browser with the model asset directory path"""
        # success = self.refreshPrefs()
        # if not success:
        #    return
        filesystem.openDirectory(self.directory)

    def uniformIconToggle(self, action):
        """Toggles the state of the uniform icons
        """
        self.uniformIcons = action.isChecked()
        self.cameraToolsPrefsData["settings"][cc.PREFS_KEY_IMAGEP_UNIFORM] = self.uniformIcons
        self.cameraToolsPrefsData.save()
        self.refreshThumbs()

    def setAssetQuickDirectory(self):
        """Browse to change/set the Model Asset Folder"""
        success = self.refreshPrefs()
        if not success:
            return
        directoryPath = self.cameraToolsPrefsData["settings"][cc.PREFS_KEY_IMAGEPLANE]
        if not os.path.isdir(directoryPath):  # if dir doesn't exist set to home directory
            directoryPath = os.environ['HOME']
        newDirPath = QtWidgets.QFileDialog.getExistingDirectory(self, "Set the Model Asset folder", directoryPath)
        if not newDirPath:
            return
        self.cameraToolsPrefsData["settings"][cc.PREFS_KEY_IMAGEPLANE] = newDirPath
        self.cameraToolsPrefsData.save()
        self.directory = newDirPath
        # update thumb model on both thumb widgets
        self.compactWidget.browserModel.setDirectory(newDirPath)  # does the refresh
        self.advancedWidget.browserModel.setDirectory(newDirPath)
        om2.MGlobal.displayInfo("Preferences Saved: Model Asset folder saved as "
                                "`{}`".format(newDirPath))

    def deletePresetPopup(self):
        """Popup window that asks the user if they want to delete the currently selected asset from disk?"""
        filenameNoSuffix = self.currentWidget().browserModel.currentImage
        if not filenameNoSuffix:
            om2.MGlobal.displayWarning("Nothing selected. Please select an image to delete.")
        fullImagePath = self.currentWidget().miniBrowser.selectedMetadata()['zooFilePath']
        filenameWithExt = os.path.basename(fullImagePath)
        # Build popup window
        message = "Warning: Delete the preset `{}` and it's dependencies?  " \
                  "This will permanently delete these file/s from disk?".format(filenameWithExt)
        result = elements.MessageBox_ok(windowName="Delete Image From Disk?",
                                        message=message)  # None will parent to Maya
        # After answering Ok or cancel
        if result:  # Ok was pressed
            filesFullPathDeleted = zooscenefiles.deleteZooSceneFiles(fullImagePath, message=True)
            self.refreshThumbs()
            om2.MGlobal.displayInfo("Success, File/s Deleted: {}".format(filesFullPathDeleted))

    # ------------------------------------
    # CALLBACKS
    # ------------------------------------

    def selectionChanged(self, selection):
        """Run when the callback selection changes, updates the GUI if an object is selected

        Callbacks are handled automatically by toolsetcallbacks.py which this class inherits"""
        if not selection:  # then don't update
            return
        self.refreshUpdateUIFromSelection()  # will update the GUI

    # ------------------------------------
    # LOGIC
    # ------------------------------------

    def refreshUpdateUIFromSelection(self, update=True):
        """Gets all the attributes (properties) from the first selected imagePlane and updates the scene

        :param update: if False will skip updating the UI, used on startup because it's auto
        :type update: bool
        """
        self.attrDict = imageplanes.getImagePlaneAttrsWithScaleAuto(message=False)

        if not self.attrDict:  # no image plane found
            return
        self.properties.opacityFloatSldr.value = self.attrDict["alphaGain"]
        self.properties.offsetLeftRightFloatSldr.value = self.attrDict["offsetX"]
        self.properties.offsetUpDownFloatSldr.value = self.attrDict["offsetY"]
        self.properties.scale.value = self.attrDict["scale"]
        if update:
            self.updateFromProperties()

    def setAttrsImagePlane(self):
        """Sets the attributes on an image plane from the current values in the GUI
        """
        attrDict = dict()
        attrDict["alphaGain"] = self.properties.opacityFloatSldr.value
        attrDict["rotate"] = self.properties.rotate.value
        attrDict["offsetX"] = self.properties.offsetLeftRightFloatSldr.value
        attrDict["offsetY"] = self.properties.offsetUpDownFloatSldr.value
        iPShape, iPTransform, camShape = imageplanes.autoImagePlaneInfo()
        if iPShape:
            attributes.setFloatAttrsDict(iPShape, attrDict)
            imageplanes.scaleImagePlaneAuto(self.properties.scale.value)

    @undodecorator.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def createImagePlane(self, image="", forceNew=False):
        """Main method, creates/modified the selected image plane.
        Creates an image plane if one is not already selected or attached to the current active viewport

        :param forceNew: if True will create a new image plane on the camera, even if one already exists
        :type forceNew: bool
        """
        currentImage = self.currentWidget().miniBrowser.itemFilePath()
        if not currentImage:
            om2.MGlobal.displayWarning("Please select an image to create.")
            return
        fullImagePath = os.path.join(self.directory, currentImage)
        iPShape, created = imageplanes.createImagePlaneAuto(iPPath=fullImagePath, forceCreate=forceNew)
        if created and not forceNew:  # sets attrs from GUI if not being built as new
            pass
            # self.setAttrsImagePlane()
        else:  # refresh the GUI with the defaults of the new image plane
            self.refreshUpdateUIFromSelection()


    @undodecorator.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def moveImageplane(self, position="center"):
        """Moves the image plane to one of 5 preset values, will offset and scale.

        :param position: The position to move to, is a string "topLeft", "botLeft", "center" etc
        :type position: str
        """
        if position == "topLeft":
            values = (-0.45, 0.3, 0.4)  # x, y, scale
        elif position == "topRight":
            values = (0.45, 0.3, 0.4)  # x, y, scale
        elif position == "botLeft":
            values = (-0.45, -0.3, 0.4)  # x, y, scale
        elif position == "botRight":
            values = (0.45, -0.3, 0.4)  # x, y, scale
        else:  # position == "center"
            values = (0.0, 0.0, 1.0)  # x, y, scale
        self.properties.scale.value = values[2]
        self.properties.offsetLeftRightFloatSldr.value = values[0]
        self.properties.offsetUpDownFloatSldr.value = values[1]
        imageplanes.moveScaleImagePlaneAuto(values[2], values[0], values[1])  # scale, x, y
        self.updateFromProperties()  # updates the sliders & GUI

    @undodecorator.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def rotateImagePlane(self, positive=True):
        """Rotates the image plane (roll) via button clicks

        :param positive: if False will be negative offset
        :type positive: bool
        """
        multiplier, reset = keyboardmouse.cntrlShiftMultiplier()  # for alt shift and ctrl keys with left click
        multiplyOffset = 5.625 * multiplier  # default offset 11.25
        if reset:
            self.properties.rotate.value = 0.0
        else:
            if positive:
                self.properties.rotate.value += multiplyOffset
            else:
                self.properties.rotate.value -= multiplyOffset
        imageplanes.rotImagePlaneAuto(self.properties.rotate.value)
        self.updateFromProperties()

    @undodecorator.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def scaleImagePlane(self, positive=True):
        """Scales the image plane via button clicks

        :param positive: if False will be negative offset
        :type positive: bool
        """
        multiplier, reset = keyboardmouse.cntrlShiftMultiplier()  # for alt shift and ctrl keys with left click
        multiplyOffset = 0.025 * multiplier  # default offset 0.05
        if reset:
            self.properties.scale.value = 1.0
        else:
            if positive:
                self.properties.scale.value += multiplyOffset
            else:
                self.properties.scale.value -= multiplyOffset
        imageplanes.scaleImagePlaneAuto(self.properties.scale.value)
        self.updateFromProperties()

    @toolsetcallbacks.ignoreCallbackDecorator
    def setImagePlaneOpacity(self):
        opacity = self.properties.opacityFloatSldr.value  # todo: change once properties is working
        imageplanes.opacityImagePlaneAuto(opacity, message=False)
        self.properties.opacity.value = opacity

    @toolsetcallbacks.ignoreCallbackDecorator
    def setImagePlaneOffsetX(self):
        offsetX = self.properties.offsetLeftRightFloatSldr.value  # todo: change once properties is working
        imageplanes.offsetXImagePlaneAuto(offsetX, message=False)
        self.properties.opacity.value = offsetX

    @toolsetcallbacks.ignoreCallbackDecorator
    def setImagePlaneOffsetY(self):
        offsetY = self.properties.offsetUpDownFloatSldr.value  # todo: change once properties is working
        imageplanes.offsetYImagePlaneAuto(offsetY, message=False)
        self.properties.opacity.value = offsetY

    @undodecorator.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def placeInFront(self):
        imageplanes.placeInFrontAuto()

    @undodecorator.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def placeBehind(self):
        imageplanes.placeBehindAuto()

    @undodecorator.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def toggleLayerVis(self):
        """Vis toggles any layer containing the string `imagePlanes_lyr`"""
        imageplanes.toggleVisImagePlaneLayer()

    @undodecorator.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def toggleLayerRef(self):
        """Vis toggles any layer containing the string `imagePlanes_lyr`"""
        imageplanes.toggleRefImagePlaneLayer()

    def getImagePlaneAttrs(self):
        """Retrieves attribute values from the active image plane, selected or camera with focus
        """
        imagePlaneDict = imageplanes.getImagePlaneAttrsAuto()
        if not imagePlaneDict:
            return
        self.properties.rotFloatSldr.value = imagePlaneDict["rotate"]

    # ------------------------------------
    # CONNECTIONS
    # ------------------------------------

    def uiconnections(self):
        """Hooks up the actual button/widgets functionality
        """
        for uiInstance in self.widgets():
            # Create New
            uiInstance.createNewBtn.clicked.connect(partial(self.createImagePlane, forceNew=True))
            # Dots menu viewer
            uiInstance.miniBrowser.dotsMenu.browseAction.connect(self.openPresetFolder)
            uiInstance.browserModel.doubleClicked.connect(self.createImagePlane)
            # Dots menu viewer
            uiInstance.miniBrowser.dotsMenu.applyAction.connect(self.createImagePlane)
            uiInstance.miniBrowser.dotsMenu.renameAction.connect(self.renameAsset)
            uiInstance.miniBrowser.dotsMenu.browseAction.connect(self.openPresetFolder)
            uiInstance.miniBrowser.dotsMenu.setDirectoryAction.connect(self.setAssetQuickDirectory)
            uiInstance.miniBrowser.dotsMenu.deleteAction.connect(self.deletePresetPopup)
            uiInstance.miniBrowser.dotsMenu.refreshAction.connect(self.refreshThumbs)
            uiInstance.miniBrowser.dotsMenu.uniformIconAction.connect(self.uniformIconToggle)
            # Place buttons
            uiInstance.placeTopLeftBtn.clicked.connect(partial(self.moveImageplane, position="topLeft"))
            uiInstance.placeTopRightBtn.clicked.connect(partial(self.moveImageplane, position="topRight"))
            uiInstance.placeBotLeftBtn.clicked.connect(partial(self.moveImageplane, position="botLeft"))
            uiInstance.placeBotRightBtn.clicked.connect(partial(self.moveImageplane, position="botRight"))
            uiInstance.placeCenterBtn.clicked.connect(partial(self.moveImageplane, position="center"))
            # Rotate
            uiInstance.rotNegBtn.clicked.connect(partial(self.rotateImagePlane, positive=False))
            uiInstance.rotPosBtn.clicked.connect(partial(self.rotateImagePlane, positive=True))
            # Scale
            uiInstance.scaleNegBtn.clicked.connect(partial(self.scaleImagePlane, positive=False))
            uiInstance.scalePosBtn.clicked.connect(partial(self.scaleImagePlane, positive=True))
            # Opacity Slider
            uiInstance.opacityFloatSldr.floatSliderChanged.connect(self.setImagePlaneOpacity)
            uiInstance.opacityFloatSldr.sliderPressed.connect(self.openUndoChunk)
            uiInstance.opacityFloatSldr.sliderReleased.connect(self.closeUndoChunk)
            # Offset Sliders
            uiInstance.offsetLeftRightFloatSldr.floatSliderChanged.connect(self.setImagePlaneOffsetX)
            uiInstance.offsetLeftRightFloatSldr.sliderPressed.connect(self.openUndoChunk)
            uiInstance.offsetLeftRightFloatSldr.sliderReleased.connect(self.closeUndoChunk)
            uiInstance.offsetUpDownFloatSldr.floatSliderChanged.connect(self.setImagePlaneOffsetY)
            uiInstance.offsetUpDownFloatSldr.sliderPressed.connect(self.openUndoChunk)
            uiInstance.offsetUpDownFloatSldr.sliderReleased.connect(self.closeUndoChunk)
            # Place front back
            uiInstance.placeFrontBtn.clicked.connect(self.placeInFront)
            uiInstance.placeBehindBtn.clicked.connect(self.placeBehind)
            # toggle Vis Layer
            uiInstance.toggleLyrVisBtn.clicked.connect(self.toggleLayerVis)
            uiInstance.toggleLyrSelBtn.clicked.connect(self.toggleLayerRef)
            # Change directory button
            uiInstance.changeImageDirBtn.clicked.connect(self.setAssetQuickDirectory)

        # callback connections
        self.selectionCallbacks.callback.connect(self.selectionChanged)  # monitor selection
        self.toolsetActivated.connect(self.startSelectionCallback)
        self.toolsetDeactivated.connect(self.stopSelectionCallback)


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
                                                itemName="Image",
                                                applyIcon="imagePlane",
                                                snapshotActive=True,
                                                snapshotNewActive=True,
                                                clipboardActive=True,
                                                newActive=False)

        self.browserModel = filemodel.FileViewModel(self.miniBrowser,
                                                    directory=directory,
                                                    chunkCount=200,
                                                    uniformIcons=uniformIcons)
        self.miniBrowser.setModel(self.browserModel)
        self.resizerWidget = ToolsetResizer(toolsetWidget=self.toolsetWidget, target=self.miniBrowser, fixedHeight=11)
        # Top Icons --------------------------------------------
        toolTip = "Move the selected or current image plane to the top left position."
        self.placeTopLeftBtn = elements.styledButton("", icon="moveTopLeft",
                                                     toolTip=toolTip,
                                                     style=uic.BTN_TRANSPARENT_BG,
                                                     minWidth=uic.BTN_W_ICN_SML)
        toolTip = "Move the selected or current image plane to the top right position."
        self.placeTopRightBtn = elements.styledButton("", "moveTopRight",
                                                      toolTip=toolTip,
                                                      style=uic.BTN_TRANSPARENT_BG,
                                                      minWidth=uic.BTN_W_ICN_SML)
        toolTip = "Move the selected or current image plane to the bot left position."
        self.placeBotLeftBtn = elements.styledButton("", "moveBotLeft",
                                                     toolTip=toolTip,
                                                     style=uic.BTN_TRANSPARENT_BG,
                                                     minWidth=uic.BTN_W_ICN_SML)
        toolTip = "Move the selected or current image plane to the bot right position."
        self.placeBotRightBtn = elements.styledButton("", "moveBotRight",
                                                      toolTip=toolTip,
                                                      style=uic.BTN_TRANSPARENT_BG,
                                                      minWidth=uic.BTN_W_ICN_SML)
        toolTip = "Move the selected or current image plane to the center position."
        self.placeCenterBtn = elements.styledButton("", "moveCenter",
                                                    toolTip=toolTip,
                                                    style=uic.BTN_TRANSPARENT_BG,
                                                    minWidth=uic.BTN_W_ICN_SML)
        # Top Icons Rotate --------------------------------------------
        toolTip = "Rotate Negative (shift faster, ctrl slower, alt reset)"
        self.rotNegBtn = elements.styledButton("", "arrowRollLeft",
                                               toolTip=toolTip,
                                               style=uic.BTN_TRANSPARENT_BG,
                                               minWidth=uic.BTN_W_ICN_SML)
        toolTip = "Rotate Positive (shift faster, ctrl slower, alt reset)"
        self.rotPosBtn = elements.styledButton("", "arrowRollRight",
                                               toolTip=toolTip,
                                               style=uic.BTN_TRANSPARENT_BG,
                                               minWidth=uic.BTN_W_ICN_SML)
        # Top Icons Scale --------------------------------------------
        toolTip = "Scale Negative (shift faster, ctrl slower, alt reset)"
        self.scaleNegBtn = elements.styledButton("", "scaleDown",
                                                 toolTip=toolTip,
                                                 style=uic.BTN_TRANSPARENT_BG,
                                                 minWidth=uic.BTN_W_ICN_SML)
        toolTip = "Scale Positive (shift faster, ctrl slower, alt reset)"
        self.scalePosBtn = elements.styledButton("", "scaleUp",
                                                 toolTip=toolTip,
                                                 style=uic.BTN_TRANSPARENT_BG,
                                                 minWidth=uic.BTN_W_ICN_SML)
        # Opacity Slider --------------------------------------------------------
        toolTip = "Opacity value of the image plane"
        self.opacityFloatSldr = elements.FloatSlider(label="Opacity",
                                                     defaultValue=1.0,
                                                     toolTip=toolTip,
                                                     sliderMin=0.0,
                                                     sliderMax=1.0,
                                                     decimalPlaces=3,
                                                     labelRatio=1,
                                                     editBoxRatio=1,
                                                     sliderRatio=1)
        # Offset Up Down Slider --------------------------------------------------------
        toolTip = "Offset the image plane up and down"
        self.offsetUpDownFloatSldr = elements.FloatSlider(label="Up/Down",
                                                          defaultValue=0.0,
                                                          toolTip=toolTip,
                                                          sliderMin=-1.0,
                                                          sliderMax=1.0,
                                                          decimalPlaces=3,
                                                          labelRatio=1,
                                                          editBoxRatio=1,
                                                          sliderRatio=1)
        # Offset Left Right Slider --------------------------------------------------------
        toolTip = "Offset the image plane left and right"
        self.offsetLeftRightFloatSldr = elements.FloatSlider(label="Left/Right",
                                                             defaultValue=0.0,
                                                             toolTip=toolTip,
                                                             sliderMin=-1.0,
                                                             sliderMax=1.0,
                                                             decimalPlaces=3,
                                                             labelRatio=1,
                                                             editBoxRatio=1,
                                                             sliderRatio=1)
        # Place Front Behind Button ---------------------------------------
        toolTip = "Move image plane to the camera near plane"
        self.placeFrontBtn = elements.styledButton("Place Front/Behind",
                                                   "arrowMoveFront",
                                                   toolTip=toolTip,
                                                   style=uic.BTN_LABEL_SML)
        toolTip = "Move image plane to the camera far plane"
        self.placeBehindBtn = elements.styledButton("",
                                                    "arrowMoveBack",
                                                    toolTip=toolTip,
                                                    style=uic.BTN_LABEL_SML)
        # Create New Button ---------------------------------------
        toolTip = "Creates a new image plane, can add more than one image plane to a single camera."
        self.createNewBtn = elements.styledButton("Create New",
                                                  "imagePlane",
                                                  toolTip=toolTip,
                                                  style=uic.BTN_DEFAULT)
        # Toggle Layer Vis Button ---------------------------------------
        toolTip = "Toggles the visibility of the `imagePlanes_lyr` if it exists."
        self.toggleLyrVisBtn = elements.styledButton("Toggle Layer",
                                                     "visible",
                                                     toolTip=toolTip,
                                                     style=uic.BTN_LABEL_SML)
        # Toggle Layer Ref Button ---------------------------------------
        toolTip = "Toggles the selectability (reference) of the `imagePlanes_lyr` if it exists."
        self.toggleLyrSelBtn = elements.styledButton("",
                                                     "reference",
                                                     toolTip=toolTip,
                                                     style=uic.BTN_LABEL_SML)
        # Change Directory Button ---------------------------------------
        toolTip = "Change the image directory"
        self.changeImageDirBtn = elements.styledButton("",
                                                       "addDir",
                                                       toolTip=toolTip,
                                                       style=uic.BTN_LABEL_SML)
        if self.uiMode == UI_MODE_ADVANCED:  # widgets that only exist in the advanced mode
            pass


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
        # Top buttons
        topButtonLayout = elements.hBoxLayout(margins=(0, uic.SMLPAD, 0, uic.SMLPAD), spacing=uic.SSML)
        topButtonLayout.addWidget(self.placeTopLeftBtn, 1)
        topButtonLayout.addWidget(self.placeTopRightBtn, 1)
        topButtonLayout.addWidget(self.placeBotLeftBtn, 1)
        topButtonLayout.addWidget(self.placeBotRightBtn, 1)
        topButtonLayout.addWidget(self.placeCenterBtn, 1)
        topButtonLayout.addWidget(self.rotNegBtn, 1)
        topButtonLayout.addWidget(self.rotPosBtn, 1)
        topButtonLayout.addWidget(self.scaleNegBtn, 1)
        topButtonLayout.addWidget(self.scalePosBtn, 1)
        # Slider Layout
        sliderLayout = elements.vBoxLayout(margins=(0, uic.SMLPAD, 0, uic.REGPAD), spacing=uic.SREG)
        sliderLayout.addWidget(self.opacityFloatSldr)
        sliderLayout.addWidget(self.offsetLeftRightFloatSldr)
        sliderLayout.addWidget(self.offsetUpDownFloatSldr)
        # Place Front Back Btns
        placeCamPlanesLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SMLPAD)
        placeCamPlanesLayout.addWidget(self.placeFrontBtn, 5)
        placeCamPlanesLayout.addWidget(self.placeBehindBtn, 1)
        # Layer Toggle Btns
        layerBtnsLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SMLPAD)
        layerBtnsLayout.addWidget(self.toggleLyrVisBtn, 5)
        layerBtnsLayout.addWidget(self.toggleLyrSelBtn, 1)
        # layer and front/back Btns
        layerPlaceBtnLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.REGPAD), spacing=uic.SLRG)
        layerPlaceBtnLayout.addLayout(layerBtnsLayout, 1)
        layerPlaceBtnLayout.addLayout(placeCamPlanesLayout, 1)
        bottomBtnLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SREG)
        bottomBtnLayout.addWidget(self.createNewBtn, 10)
        bottomBtnLayout.addWidget(self.changeImageDirBtn, 1)
        # Add to main layout
        mainLayout.addWidget(self.miniBrowser)
        mainLayout.addWidget(self.resizerWidget)
        mainLayout.addLayout(topButtonLayout)
        mainLayout.addLayout(sliderLayout)
        mainLayout.addLayout(placeCamPlanesLayout)
        mainLayout.addLayout(layerPlaceBtnLayout)
        mainLayout.addLayout(bottomBtnLayout, 1)
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
        # Top buttons
        topButtonLayout = elements.hBoxLayout(margins=(0, uic.SMLPAD, 0, uic.SMLPAD), spacing=uic.SSML)
        topButtonLayout.addWidget(self.placeTopLeftBtn, 1)
        topButtonLayout.addWidget(self.placeTopRightBtn, 1)
        topButtonLayout.addWidget(self.placeBotLeftBtn, 1)
        topButtonLayout.addWidget(self.placeBotRightBtn, 1)
        topButtonLayout.addWidget(self.placeCenterBtn, 1)
        topButtonLayout.addWidget(self.rotNegBtn, 1)
        topButtonLayout.addWidget(self.rotPosBtn, 1)
        topButtonLayout.addWidget(self.scaleNegBtn, 1)
        topButtonLayout.addWidget(self.scalePosBtn, 1)
        # Slider Layout
        sliderLayout = elements.vBoxLayout(margins=(0, uic.SMLPAD, 0, uic.REGPAD), spacing=uic.SREG)
        sliderLayout.addWidget(self.opacityFloatSldr)
        sliderLayout.addWidget(self.offsetLeftRightFloatSldr)
        sliderLayout.addWidget(self.offsetUpDownFloatSldr)
        # Place Front Back Btns
        placeCamPlanesLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SMLPAD)
        placeCamPlanesLayout.addWidget(self.placeFrontBtn, 5)
        placeCamPlanesLayout.addWidget(self.placeBehindBtn, 1)
        # Layer Toggle Btns
        layerBtnsLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SMLPAD)
        layerBtnsLayout.addWidget(self.toggleLyrVisBtn, 5)
        layerBtnsLayout.addWidget(self.toggleLyrSelBtn, 1)
        # layer and front/back Btns
        layerPlaceBtnLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.REGPAD), spacing=uic.SLRG)
        layerPlaceBtnLayout.addLayout(layerBtnsLayout, 1)
        layerPlaceBtnLayout.addLayout(placeCamPlanesLayout, 1)
        bottomBtnLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SREG)
        bottomBtnLayout.addWidget(self.createNewBtn, 10)
        bottomBtnLayout.addWidget(self.changeImageDirBtn, 1)
        # Add to main layout
        mainLayout.addWidget(self.miniBrowser)
        mainLayout.addWidget(self.resizerWidget)
        mainLayout.addLayout(topButtonLayout)
        mainLayout.addLayout(sliderLayout)
        mainLayout.addLayout(placeCamPlanesLayout)
        mainLayout.addLayout(layerPlaceBtnLayout)
        mainLayout.addLayout(bottomBtnLayout, 1)
        mainLayout.addStretch(1)

