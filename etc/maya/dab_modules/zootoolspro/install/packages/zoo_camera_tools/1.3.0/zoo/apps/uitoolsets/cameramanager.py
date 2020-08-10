from functools import partial
import webbrowser

from zoo.apps.toolsetsui import toolsetcallbacks
from Qt import QtWidgets

import maya.api.OpenMaya as om2
from maya import cmds
from zoo.libs.maya import zapi
from zoo.libs.maya.zapi import alphabetizeDagList

from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import zlogging
from zoo.libs.maya.cmds.objutils import namehandling
from zoo.libs.maya.cmds.cameras import cameras
from zoo.libs.maya.cmds.cameras.cameraconstants import RESOLUTION_LIST, CLIP_PLANES_LIST, SENSOR_SIZE_LIST, \
    PERSPECTIVE_MODE_LIST, FIT_MODE_LIST, OVERSCAN_VALUES, FOCAL_LENGTHS
from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.libs.utils import colour

logger = zlogging.getLogger(__name__)

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

# Colors are in srgb float
MASK_COLORS = [(0.75, 0.25, 0.25), (0.25, 0.82, 0.25), (0.25, 0.62, 0.82), (0, 0, 0), (0.735, 0.735, 0.735)]


class CameraManager(toolsetwidgetmaya.ToolsetWidgetMaya):
    """
    """
    id = "cameraManager"
    uiData = {"label": "Camera Manager",
              "icon": "movieCamera",
              "tooltip": "Camera Manager for common camera settings",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-camera-manager/"
              }

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run"""
        self.disableLookthrough = False
        self.toolsetWidget = self
        self.excludeSelection = False

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget(), self.initAdvancedWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        self.compactWidget = GuiCompact(parent=self, properties=self.properties, toolsetWidget=self)
        return self.compactWidget

    def initAdvancedWidget(self):
        """Builds the Advanced GUI (self.advancedWidget) """
        self.advancedWidget = GuiAdvanced(parent=self, properties=self.properties, toolsetWidget=self)
        return self.advancedWidget

    def postContentSetup(self):
        """Last of the initialize code"""
        self.uiConnections()
        self.ignoreInstantApply = False
        self.updateUIWithCurrentCamera()  # On open gets from the active viewport or under cursor
        self.updateUiData(updateCombo=True)  # self.updateCameraFromViewport(), self.updateCameraCombo()
        self.startSelectionCallback()

    def defaultAction(self):
        """Double Click"""
        pass

    def selectionChanged(self, selection):
        """ Run when the callback selection changes, updates the GUI if an object is selected

        Callbacks are handled automatically by toolsetcallbacks.py

        :param selection:
        :type selection:
        :return:
        :rtype:
        """
        if not selection:  # then don't update
            return

        selection = list(zapi.nodesByNames(selection))

        self.updateCameraCombo()
        cameraDag = selection[-1]
        self.excludeSelection = False
        self.blockCallbacks(True)
        for i, item in enumerate(self.currentWidget().cameraNameCombo.iterItemData()):
            if item is not None and item == cameraDag:
                self.disableLookthrough = True
                self.currentWidget().cameraNameCombo.setIndexInt(i)
                self.disableLookthrough = False

                break
        self.blockCallbacks(False)


    # ------------------
    # PROPERTIES
    # ------------------

    def initializeProperties(self):
        """Used to store and update UI data

        properties are auto-linked if the name matches the widget name

        :return properties: special dictionary used to save and update all GUI widgets
        :rtype properties: list(dict)
        """
        return [{"name": "cameraNameStr", "value": ""},
                {"name": "longName", "value": ""},
                {"name": "resolutionCombo", "value": 2},
                {"name": "overscanValueFloat", "value": 1.05},
                {"name": "focalLengthEdit", "value": 35.0},
                {"name": "maskOpacityFloat", "value": 1.0},
                {"name": "maskColorPicker", "value": (0.0, 0.0, 0.0)},
                {"name": "perspectiveCombo", "value": 0}]

    def updateFromProperties(self):
        """ Runs update properties from the base class.

        Widgets will auto update from self.properties if linked via:

            self.linkProperty(widget, "propertyKey")
            or
            self.toolsetWidget.linkProperty(widget, "propertyKey")

        Add code after super() useful for changes such as forcing UI decimal places
        or manually adding unsupported widgets
        """
        if self.ignoreInstantApply:  # skip if setting properties while switching, no need to save
            return
        # self.currentWidget().lightNameTxt.clearFocus()  # for uiMode change
        super(CameraManager, self).updateFromProperties()

    # ------------------
    # RIGHT CLICKS
    # ------------------

    def actions(self):
        """Right click menu and actions
        """
        return [
            {"type": "action",
             "name": "uv",
             "label": "Transfer UVs",
             "icon": "transferUVs",
             "tooltip": ""},
            {"type": "action",
             "name": "shader",
             "label": "Transfer Shader",
             "icon": "transferUVs",
             "tooltip": ""},
            {"type": "action",
             "name": "uv_shader",
             "label": "Transfer UVs & Shaders",
             "icon": "transferUVs",
             "tooltip": ""}
        ]

    @toolsetwidgetmaya.undoDecorator
    def executeActions(self, action):
        """Right click actions on the main toolset icon

        :param action:
        :type action:
        """
        name = action['name']
        if name == "uv":
            pass
        elif name == "shader":
            pass
        elif name == "uv_shader":
            pass


    # ------------------
    # LOGIC
    # ------------------

    def widgets(self):
        """

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(CameraManager, self).widgets()

    def currentWidget(self):
        """

        :return:
        :rtype: GuiAdvanced or GuiCompact
        """
        return super(CameraManager, self).currentWidget()

    # ------------------
    # CONNECTIONS
    # ------------------

    def updateCameraFromViewport(self):
        """ Gets the camera from the under active viewport or cursor and updates the GUI, not found returns None

        This method checks in order:

            1. First selected camera
            2. The active viewport
            3. Under Cursor
            4. First opened viewport in the scene

        """
        camList = cameras.cameraTransformsSelected()
        if camList:  # return the first selected camera
            camera = camList[0]
        else:  # Get the active focus cam, or then under cursor or then the first cam viewport in the scene.
            camera = cameras.getFocusCamera(prioritizeUnderCursor=False)  # camera is unique name
            if not camera:
                return
        longName = namehandling.getLongNameFromShort(camera)
        shortName = namehandling.getShortName(camera)
        self.properties.cameraNameStr.value = shortName
        self.properties.longName.value = longName
        self.updateFromProperties()

    def updateUiData(self, updateCombo=False):
        """Fill in the ui data based on the current camera

        :param updateCombo: Update the camera combo to match with Maya. Sort by perspective/orthographic alphabetical
        :type updateCombo: bool
        """
        if updateCombo:
            #self.saveProperties()
            self.updateCameraCombo()

        camShape = self.currentCamShape()
        if camShape is None:
            logger.debug("camShape is None")
            return

        # Update resolution
        width, height, ratio = cameras.renderGlobalsWidthHeight()
        self.properties.resolutionComboEdit.value = [width, height]

        # Other values
        sensorW, sensorH, sensorR = cameras.sensorSizeMm(camShape)

        self.properties.sensorSizeEdit.value = [sensorW, sensorH]

        resSizeWidthMm, resSizeHeightMm = cameras.resolutionSizeMm(camShape)
        self.properties.resolutionSizeVector.value = [resSizeWidthMm, resSizeHeightMm]  # rnd
        self.properties.matchGateRatioCheckbox.value = cameras.zooMatchGateBoolValue(camShape)
        self.properties.resolutionGateCheckBox.value = cameras.resolutionGate(camShape)
        self.properties.focalLengthEdit.value = cameras.focalLength(camShape)
        self.properties.maskColorPicker.value = cameras.camMaskColor(camShape)[0]
        self.properties.maskOpacitySlider.value = cameras.maskOpacity(camShape)
        self.properties.overscanValueFloat.value = cameras.overscan(camShape)
        self.properties.fitGateCombo.value = cameras.camFitResGate(camShape)
        self.properties.perspectiveCombo.value = int(not cameras.isPerspective(camShape))
        self.properties.clippingEdit.value = list(cameras.camClipPlanes(camShape))
        self.properties.filmGateCheckBox.value = cameras.filmGate(camShape)
        self.properties.displayGateMaskCheckBox.value = cameras.gateMask(camShape)
        self.updateFromProperties()


    def duplicateCamera(self):
        """ Duplicates the current camera, looks through it and selects it causing a refresh

        :return:
        :rtype:
        """
        camLongName = self.currentCamTransform()
        if not camLongName:
            om2.MGlobal.displayWarning("No camera found to duplicate")
            return
        duplicatedCam = cameras.duplicateCamera(self.currentCamTransform())[0]
        cmds.select(duplicatedCam, replace=True)
        cameras.lookThrough(duplicatedCam)

    def cameraComboChanged(self, event):
        """ On camera combo changed

        :type event: elements.IndexChangedEvent or elements.EditChangedEvent
        :return:
        :rtype:
        """
        self.updateUiData()
        if not self.disableLookthrough and event.menuButton == event.Primary:
            self.lookThrough()

        if event.menuButton == event.Secondary:
            cameraDag = self.currentCamera()
            self.selectCamera(cameraDag.fullPathName())


    @toolsetcallbacks.ignoreCallbackDecorator
    def selectCamera(self, camFullName):
        cmds.select(camFullName, replace=True)

    def focalLengthChanged(self, event=None):
        """Sets the focal length from the UI

        :param event: Qt event from the comboEdit
        :type event: elements.IndexChangedEvent or elements.EditChangedEvent
        """
        self.setFocalLength()

    def selectCameraClicked(self):
        """ Select Camera button clicked, selects the active camera in the viewport

        :return:
        :rtype:
        """
        cameras.selectCamInView()

    def setCameraAllAttrs(self, camShape, regularSettings=True, filmBack=True, mask=True):
        """Sets all attributes on the current camera, with options

        :param camShape: A maya camera shape node
        :type camShape: str
        """
        if regularSettings:
            cameras.setCamClipPlanes(camShape,
                                     self.properties.clippingEdit.value[0],
                                     self.properties.clippingEdit.value[1])
            cameras.setFocalLength(camShape, self.properties.focalLengthEdit.value)
            cameras.setPespectiveMode(camShape, not bool(self.properties.perspectiveCombo.value))
        if mask:
            cameras.setCamMaskColor(camShape,
                                    colour.convertColorLinearToSrgb(self.properties.maskColorPicker.value))
            cameras.setCamGateMaskOpacity(camShape, self.properties.maskOpacitySlider.value)
            cameras.setCamOverscan(camShape, self.properties.overscanValueFloat.value)
        if filmBack:
            cameras.setCamFitResGate(camShape, fitResolutionGate=self.properties.fitGateCombo.value)
            cameras.setSensorSizeMm(camShape,
                                    self.properties.sensorSizeEdit.value[0],
                                    self.properties.sensorSizeEdit.value[1])
            cameras.setCamResGate(camShape, self.properties.resolutionGateCheckBox.value, message=False)
            cameras.setGateMask(camShape, self.properties.displayGateMaskCheckBox.value)
            cameras.setCamFilmGate(camShape, self.properties.filmGateCheckBox.value)
            if self.properties.matchGateRatioCheckbox.value:
                cameras.matchResolutionFilmGate(camShape)

    def cameraCreateClicked(self):
        """ Create Camera button clicked

        :return:
        :rtype:
        """
        self.blockCallbacks(True)
        camera, camShape = cameras.createCameraNodesZxy()
        # Set attributes from the UI
        self.setCameraAllAttrs(camShape.fullPathName())  # applies all the settings from the UI
        self.blockCallbacks(False)
        # Select will self.setCameraCombo(camera), self.updateCameraCombo() and self.updateUiData()  etc
        cmds.select(camera.fullPathName())  # will refresh UI
        # message already sent

    def setCameraCombo(self, camDag):
        """ Set the camera combo based on camera dag node

        :param camDag: zapi camera maybe shape node?
        :type camDag: zoo.libs.maya.zapi.DagNode
        """
        for i, camera in enumerate(self.currentWidget().cameraNameCombo.iterItemData()):
            if camera == camDag:
                self.properties.cameraNameCombo.value = i
                self.updateUiData(updateCombo=True)
                return

    def renameCamera(self):
        """ Rename Camera based on properties

        :return:
        :rtype:
        """
        widget = self.currentWidget()
        widget.cameraNameCombo.show()
        # cameras.rename(self.currentCamera().fullPathName(), newName)
        self.updateUiData(updateCombo=True)
        # self.updateCameraCombo()

    def renameCamEvent(self, event):
        """ Rename Cam event

        :param event:  QT signal, with  event.before and  event.after
        :type event: zoo.libs.pyqt.extended.combobox.comboeditwidget.EditChangedEvent
        """
        if event.before != "" and cameras.nodeLocked(event.before):
            om2.MGlobal.displayWarning("Cannot rename a read only node.")
            return

        if event.after == "":
            om2.MGlobal.displayWarning("Camera name cant be empty")
            self.currentWidget().cameraNameCombo.setText(event.before)
            return

        newName = namehandling.safeRename(self.currentCamera().fullPathName(), event.after, message=True)
        if event.after != newName:
            om2.MGlobal.displayWarning("Can't rename to \"{}\". Renaming to \"{}\"".format(event.after, newName))

        self.updateUiData(updateCombo=True)

    @toolsetcallbacks.ignoreCallbackDecorator
    def lookThrough(self):
        """ Look through the current camera

        :return:
        :rtype:
        """
        camLongName = self.currentCamTransform()
        if not camLongName:
            return
        cameras.lookThrough(camLongName)


    @toolsetwidgetmaya.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def setResolutionGate(self, checked=False):
        """ Toggle the resolution gate of the current camera shape
        """
        camShapes = self.selectedCamShapes()
        if checked:  # will be 2
            checked = 1
        for camShape in camShapes:
            cameras.setCamResGate(camShape, checked, message=False)

        om2.MGlobal.displayInfo("Resolution Gate is set to \"{}\" for {}".format(bool(checked),
                                                                                 self.shortTNames(camShapes)))

    @toolsetwidgetmaya.undoDecorator
    def setFilmGate(self, checked=False):
        """Sets the film gate setting
        """
        camShapes = self.selectedCamShapes()
        for camShape in camShapes:
            cameras.setCamFilmGate(camShape, self.properties.filmGateCheckBox.value)

        om2.MGlobal.displayInfo("Film Gate is set to \"{}\" for {}".format(bool(checked),
                                                                           self.shortTNames(camShapes)))

    @toolsetwidgetmaya.undoDecorator
    def setDisplayMask(self, checked=False):
        """Sets the display mask setting
        """
        camShapes = self.selectedCamShapes()
        for camShape in camShapes:
            cameras.setGateMask(camShape, self.properties.displayGateMaskCheckBox.value)

        om2.MGlobal.displayInfo("Display Mask is set to \"{}\" "
                                "for {}".format(self.properties.displayGateMaskCheckBox.value,
                                                self.shortTNames(camShapes)))

    @toolsetwidgetmaya.undoDecorator
    def setFocalLength(self):
        """ Set focal length

        """
        selCamShapes = self.selectedCamShapes()
        for camShape in selCamShapes:
            cameras.setFocalLength(camShape, self.properties.focalLengthEdit.value)

        om2.MGlobal.displayInfo("Focal length set to \"{}\" for {}".format(self.properties.focalLengthEdit.value,
                                                                           self.shortTNames(selCamShapes)))

    def selectedCamShapes(self, includeCurrent=True):
        """ Get selected cam shapes and the UI cam if includeCurrent

        :param includeCurrent: Return the current camera in the UI as well as any selected cams, usually True
        :type includeCurrent: bool
        """
        camShapeLongNames = cameras.cameraShapesSelected()
        camShapeLongNames = [] if len(camShapeLongNames) == 1 else camShapeLongNames

        if includeCurrent:
            currentCamShape = self.currentCamShape()
            if currentCamShape not in camShapeLongNames:
                camShapeLongNames.append(currentCamShape)

        return camShapeLongNames

    def shortTNames(self, camShapeList):
        """Returns the short transform names from a list of cam shape nodes names

        Used in user messages

        :param camShapeList: list of camera shape nodes
        :type camShapeList: list(str)
        :return cameraTransforms: cameraTransforms as short names
        :rtype cameraTransforms:
        """
        if not camShapeList:
            return list()
        cameraTransforms = cameras.cameraTransformList(camShapeList)
        return namehandling.getShortNameList(cameraTransforms)

    @toolsetwidgetmaya.undoDecorator
    def maskColorPalettePressed(self, colorPressedEvent):
        """ Mask color palette button pressed event.

        When one of the colored buttons are pressed

        :param colorPressedEvent:
        :type colorPressedEvent:
        :return:
        :rtype:
        """
        srgbFloat = colorPressedEvent.color
        self.currentWidget().maskColorPicker.setColorSrgbFloat(srgbFloat)
        selCamShapes = self.selectedCamShapes()
        for camShape in selCamShapes:
            cameras.setCamMaskColor(camShape, srgbFloat)

        om2.MGlobal.displayInfo("Mask color set to \"{}\" for {}".format(srgbFloat, self.shortTNames(selCamShapes)))

    def updateUIWithCurrentCamera(self):
        """ Update UI with current camera, returns the long name of the current camera

        :return cameraLongName: The long name of the current camera
        :rtype cameraLongName: str
        """
        self.updateCameraCombo()
        self.updateCameraFromViewport()  # Updates the longName
        if not self.properties.longName.value:
            om2.MGlobal.displayWarning("Current Camera not found")
            return self.properties.longName.value
        self.properties.cameraNameCombo.currentData = zapi.nodeByName(self.properties.longName.value)
        return self.properties.longName.value

    def currentCamTransform(self):
        """ Returns the current cam transform as Long name
        """
        # todo: review this code
        if self.currentWidget().cameraNameCombo.count() == 0:
            return ""
        dagNode = self.currentCamera()  # gets from the UI

        if dagNode is None:
            camLongName = self.updateUIWithCurrentCamera()  # Cam not found so try an update
            if not camLongName:  # message reported
                return ""
            return None
        fullFullNameList = zapi.fullNames([dagNode])
        if not fullFullNameList:  # is an issue with the dag node, perhaps camera has been deleted?
            camLongName = self.updateUIWithCurrentCamera()  # Cam not found so try an update
            if not camLongName:  # message reported
                return ""
        else:
            camLongName = fullFullNameList[0]  # usually will find this

        if not camLongName:  # Rare but can happen while doing a new scene for example
            camLongName = self.updateUIWithCurrentCamera()  # updates the combo list and the current camera
            if not camLongName:  # message reported
                return ""
        return camLongName

    def currentCamShape(self):
        """ Returns the current camera shape as long name

        :return cameraShape: name of the camera's shape noce
        :rtype cameraShape: basestring
        """
        camLongName = self.currentCamTransform()
        if camLongName == "":
            return None
        camShape = cameras.cameraShape(camLongName)
        return camShape

    @toolsetwidgetmaya.undoDecorator
    def maskColorPickerChanged(self, color):
        """ Mask color picker color changed

        :param color: a maya linear color as list(float)
        :type color: list(float)
        """
        srgbFloat = colour.convertColorLinearToSrgb(color)
        selCamShapes = self.selectedCamShapes()
        for camShape in selCamShapes:
            cameras.setCamMaskColor(camShape, srgbFloat)
        om2.MGlobal.displayInfo("Mask color set to \"{}\" for {}".format(color, self.shortTNames(selCamShapes)))

    @toolsetwidgetmaya.undoDecorator
    def setMaskOpacity(self):
        """ Set Mask opacity based on the properties
        """
        for camShape in self.selectedCamShapes():
            cameras.setCamGateMaskOpacity(camShape, self.properties.maskOpacitySlider.value)

    def setMaskOpacityRelease(self):
        """Report opacity message only on floatSlider release
        """
        om2.MGlobal.displayInfo("Mask Opacity set to \"{}\" for {}".format(self.properties.maskOpacitySlider.value,
                                                                           self.shortTNames(self.selectedCamShapes())))

    @toolsetwidgetmaya.undoDecorator
    def setOverScan(self, event=None):
        """ Set Overscan based on properties or value

        :param event:
        :type event: zoo.libs.pyqt.extended.combobox.comboeditwidget.IndexChangedEvent or zoo.libs.pyqt.extended.combobox.comboeditwidget.EditChangedEvent
        :return:
        :rtype:
        """

        selCamShapes = self.selectedCamShapes()
        for camShape in selCamShapes:
            cameras.setCamOverscan(camShape, self.properties.overscanValueFloat.value)

        om2.MGlobal.displayInfo("Overscan set to \"{}\" for {}".format(self.properties.overscanValueFloat.value,
                                                                       self.shortTNames(selCamShapes)))

    @toolsetwidgetmaya.undoDecorator
    def setPerspectiveMode(self, index=None, comboValue=None):
        """ Set perspective mode based on properties
        """
        perspMode = not bool(self.properties.perspectiveCombo.value)
        selCamShapes = self.selectedCamShapes()
        for camShape in selCamShapes:
            cameras.setPespectiveMode(camShape, perspMode)


        self.updateCameraCombo()
        om2.MGlobal.displayInfo("Perspective mode set to \"{}\" for {}".format(perspMode,
                                                                               self.shortTNames(selCamShapes)))

    @toolsetwidgetmaya.undoDecorator
    def setFitMode(self, index=None, comboValue=None):
        """ Set perspective mode based on properties
        """
        selCamShapes = self.selectedCamShapes()
        for camShape in selCamShapes:
            cameras.setCamFitResGate(camShape, fitResolutionGate=self.properties.fitGateCombo.value)
        om2.MGlobal.displayInfo("Fit Gate set to \"{}\" for {}".format(comboValue,
                                                                       self.shortTNames(selCamShapes)))
        self.updateUiData()  # update resolution size mm width/height

    @toolsetwidgetmaya.undoDecorator
    def clippingComboEditChanged(self, event=None):
        """ Clipping combo changed

        :param event: Qt event from the comboEdit
        :type event: zoo.libs.pyqt.extended.combobox.comboeditwidget.IndexChangedEvent or zoo.libs.pyqt.extended.combobox.comboeditwidget.EditChangedEvent
        """

        selCamShapes = self.selectedCamShapes()
        for camShape in selCamShapes:
            cameras.setCamClipPlanes(camShape,
                                     self.properties.clippingEdit.value[0],
                                     self.properties.clippingEdit.value[1])

        om2.MGlobal.displayInfo("Clipping Near/Far set to \"{}\" for {}".format(self.properties.clippingEdit.value,
                                                                                self.shortTNames(selCamShapes)))

    @toolsetwidgetmaya.undoDecorator
    def sensorSizeEditChanged(self, event=None):
        """ Sensor Size combo changed

        :param event: Qt event from the comboEdit
        :type event: zoo.libs.pyqt.extended.combobox.comboeditwidget.IndexChangedEvent or zoo.libs.pyqt.extended.combobox.comboeditwidget.EditChangedEvent
        """
        selCamShapes = self.selectedCamShapes()
        for camShape in selCamShapes:
            cameras.setSensorSizeMm(camShape,
                                    self.properties.sensorSizeEdit.value[0],
                                    self.properties.sensorSizeEdit.value[1])
        self.updateUiData()  # update resolution size mm width/height
        om2.MGlobal.displayInfo("Sensor Size changed to {} for {}".format(self.properties.sensorSizeEdit.value, self.shortTNames(selCamShapes)))

    def tearOffCurrent(self):
        """ Tears off the current camera into a new window

        :return:
        :rtype:
        """

        cameras.openTearOffCam(cameras.cameraTransform(self.currentCamShape()))

    @toolsetwidgetmaya.undoDecorator
    def resolutionComboChanged(self, event=None):
        """ Resolution combo changed event

        :param event: Qt event from the comboEdit
        :type event: zoo.libs.pyqt.extended.combobox.comboeditwidget.IndexChangedEvent or zoo.libs.pyqt.extended.combobox.comboeditwidget.EditChangedEvent
        """
        cameras.setGlobalsWidthHeight(self.properties.resolutionComboEdit.value[0],
                                      self.properties.resolutionComboEdit.value[1],
                                      message=False)
        #self.updateUiData()  # Update resolution size mm width/height
        om2.MGlobal.displayInfo("Scene Resolution changed to {}".format(self.properties.resolutionComboEdit.value))

    @toolsetwidgetmaya.undoDecorator
    def setMatchGateRatios(self, checked=False, message=True):
        """ Match Gate ratios for all selected cameras
        """
        selCamShapes = self.selectedCamShapes()
        if checked:
            for camShape in selCamShapes:
                cameras.matchResolutionFilmGate(camShape)
            if message:
                om2.MGlobal.displayInfo("Resolution and Film Gates: "
                                        "Matched for {}".format(self.shortTNames(selCamShapes)))
        else:
            for camShape in selCamShapes:
                cameras.unmatchCamFilmBackRatio(camShape)
            if message:
                om2.MGlobal.displayInfo(
                    "Resolution and Film Gates: Unmatched for {}".format(self.shortTNames(selCamShapes)))
        self.updateUiData()  # Fit Resolution Gate may have changed

    def filmBackApplyOrth(self, camType=cameras.CAM_TYPE_ORTHOGRAPHIC):
        """Applies the film back settings only to all perspective cameras.
        See self.filmBackApplyAll() for documentation"""
        self.filmBackApplyAll(camType=camType)

    @toolsetwidgetmaya.undoDecorator
    def filmBackApplyAll(self, camType=cameras.CAM_TYPE_PERSP):
        """Applies the film back settings only to all perspective cameras:

            CAM_TYPE_ALL = "all"
            CAM_TYPE_PERSP = "perspective"
            CAM_TYPE_ORTHOGRAPHIC = "orthographic"

        :param camType: applies settings to cameras either "all" "perspective" or "orthographic"
        :type camType: str
        """
        cams = cameras.cameraTransformsAll(camType=camType, longname=True)
        cameraShapes = cameras.cameraShapeList(cams)
        for camShape in cameraShapes:
            self.setCameraAllAttrs(camShape, regularSettings=False, filmBack=True, mask=False)
        om2.MGlobal.displayInfo("Success scene cameras updated {}".format(self.shortTNames(cameraShapes)))

    def openVfxDatabase(self):
        """ Opens browser to vfxcamdb.com

        :return:
        :rtype:
        """
        webbrowser.open("https://vfxcamdb.com/")

    def updateCameraCombo(self):
        """ Update the camera combo to match with Maya. Sort by perspective/orthographic and alphabetical

        :return:
        :rtype:
        """
        self.disableLookthrough = True
        combo = self.currentWidget().cameraNameCombo

        perspDagList = cameras.allCamTransformsDag(cameras.CAM_TYPE_PERSP)
        orthoDagList = cameras.allCamTransformsDag(cameras.CAM_TYPE_ORTHOGRAPHIC)

        perspDagList = alphabetizeDagList(perspDagList)
        orthoDagList = alphabetizeDagList(orthoDagList)

        combo.blockSignals(True)
        combo.clear()
        index = None
        for i, cam in enumerate(perspDagList + [elements.ComboEditWidget.SeparatorString] + orthoDagList):
            if str(cam) == elements.ComboEditWidget.SeparatorString:
                combo.addSeparator()
                continue

            currentCam = self.currentCamera()

            combo.addItem(cam.name(), cam)

            if currentCam is not None and cam == currentCam:
                index = i

        if index is not None:
            self.properties.cameraNameCombo.value = index
            combo.setIndexInt(index)

        combo.blockSignals(False)
        self.disableLookthrough = False

    def cameras(self):
        """ Get all the camera dags
        """
        return self.currentWidget().cameraNameCombo.iterItemData()

    def currentCamera(self):
        """ Get the current camera in the UI as a dag node

        :return cameraDag: returns the zapi dag if it is entered in the UI otherwise None
        :rtype cameraDag: zapi.DagNode
        """
        if not type(self.properties.cameraNameCombo.currentData) is zapi.DagNode:
            self.saveProperties()  # make sure the properties get saved from ui

        currentData = self.properties.cameraNameCombo.currentData  # type: zapi.DagNode

        if currentData is not None and not currentData.exists():
            currentData = None

        if currentData is None:  # No camera found? Use default persp
            currentData = zapi.nodeByName("persp")
            self.properties.cameraNameCombo.currentData = currentData

        return currentData

    def enterEvent(self, event):
        """ Enter event

        Update the ui data on mouse enter

        :param event:
        :type event:
        :return:
        :rtype:
        """
        ret = super(CameraManager, self).enterEvent(event)
        self.updateUiData(updateCombo=True)
        return ret


    def uiConnections(self):
        """ Ui Connections

        :return:
        :rtype:
        """
        self.selectionCallbacks.callback.connect(self.selectionChanged)  # monitor selection
        self.toolsetActivated.connect(self.startSelectionCallback)
        self.toolsetDeactivated.connect(self.stopSelectionCallback)

        self.displaySwitched.connect(partial(self.updateUiData, True))

        for widget in self.widgets():
            widget.cameraNameCombo.itemChanged.connect(self.cameraComboChanged)
            widget.cameraNameCombo.itemRenamed.connect(self.renameCamEvent)
            widget.resolutionComboEdit.comboEditChanged.connect(self.resolutionComboChanged)
            widget.focalLengthEdit.comboEditChanged.connect(self.focalLengthChanged)
            widget.clippingEdit.comboEditChanged.connect(self.clippingComboEditChanged)
            widget.resolutionGateCheckBox.stateChanged.connect(self.setResolutionGate)
            widget.createCameraBtn.clicked.connect(self.cameraCreateClicked)
            widget.duplicateCameraBtn.clicked.connect(self.duplicateCamera)
            widget.selectCameraBtn.clicked.connect(self.selectCameraClicked)
            widget.lookThroughCameraBtn.clicked.connect(self.lookThrough)
            widget.matchGateRatioCheckbox.stateChanged.connect(self.setMatchGateRatios)
            widget.overscanValueFloat.comboEditChanged.connect(self.setOverScan)
            widget.fitGateCombo.itemChanged.connect(self.setFitMode)

            if isinstance(widget, GuiAdvanced):
                widget.sensorSizeEdit.comboEditChanged.connect(self.sensorSizeEditChanged)

                widget.maskColorPalette.colorPressed.connect(self.maskColorPalettePressed)
                widget.maskColorPicker.colorChanged.connect(self.maskColorPickerChanged)
                widget.maskOpacitySlider.floatSliderChanged.connect(self.setMaskOpacity)
                widget.maskOpacitySlider.sliderPressed.connect(self.openUndoChunk)
                widget.maskOpacitySlider.sliderReleased.connect(self.closeUndoChunk)
                widget.maskOpacitySlider.sliderReleased.connect(self.setMaskOpacityRelease)
                widget.perspectiveCombo.itemChanged.connect(self.setPerspectiveMode)
                widget.tearOffCurrentBtn.clicked.connect(self.tearOffCurrent)
                widget.tearOffPerspectiveBtn.clicked.connect(cameras.openTearOffCam)
                widget.cameraDatabaseExploreBtn.clicked.connect(self.openVfxDatabase)
                widget.filmGateCheckBox.stateChanged.connect(self.setFilmGate)
                widget.displayGateMaskCheckBox.stateChanged.connect(self.setDisplayMask)
                widget.applyAllPerspBtn.clicked.connect(self.filmBackApplyAll)
                widget.applyAllOrthBtn.clicked.connect(self.filmBackApplyOrth)


class GuiWidgets(QtWidgets.QWidget):
    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None):
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
        self.properties = properties
        # Camera Name String -----------------------------------------------------
        toolTip = "Edit the camera name, or use the combo box to change the active camera."
        self.cameraNameCombo = elements.ComboEditRename(parent=self, label="Camera Name", labelStretch=3, mainStretch=5,
                                                        secondaryActive=True, secondaryIcon="cursorSelect",
                                                        primaryTooltip="Set To",
                                                        secondaryTooltip="Select Only",
                                                        toolTip=toolTip)
        toolsetWidget.addExtraProperties(self.cameraNameCombo, {"currentData": "currentData"})

        camsTransforms = cameras.allCamTransformsDag(cameras.CAM_TYPE_PERSP) + cameras.allCamTransformsDag(
            cameras.CAM_TYPE_ORTHOGRAPHIC)

        self.cameraNameCombo.addItems([c.name() for c in camsTransforms])
        # Resolution Combobox -----------------------------------------------------
        toolTip = "Set the scene resolution via presets. \n" \
                  "Manually enter values in the advanced mode of this toolset. "

        # todo: needs to be set to default setIndex=self.properties.resolutionCombo.value
        self.resolutionComboEdit = elements.ComboEditWidget(self,
                                                            label="Scene Resolution",
                                                            items=list(RESOLUTION_LIST.keys()),
                                                            data=[r[1] for r in RESOLUTION_LIST.items()],
                                                            aspectRatioButton=True,
                                                            labelStretch=3,
                                                            editCount=2,
                                                            mainStretch=5,
                                                            inputMode="int",
                                                            toolTip=toolTip)
        # Clipping Combobox -----------------------------------------------------
        toolTip = "Set the near and far clipping planes from presets. \n" \
                  "Manually enter values in the advanced mode of this toolset. "
        self.clippingEdit = elements.ComboEditWidget(self,
                                                     label="Clipping Near/Far",
                                                     items=list(CLIP_PLANES_LIST.keys()),
                                                     data=[c[1] for c in CLIP_PLANES_LIST.items()],
                                                     labelStretch=3,
                                                     editCount=2,
                                                     mainStretch=5,
                                                     inputMode="float",
                                                     toolTip=toolTip)
        # Focal Length Float -----------------------------------------------------
        toolTip = "Set the focal length (lens length). "
        self.focalLengthEdit = elements.ComboEditWidget(self,
                                                        label="Focal Length",
                                                        items=FOCAL_LENGTHS,
                                                        text=self.properties.focalLengthEdit.value,
                                                        labelStretch=3,
                                                        mainStretch=5,
                                                        inputMode="float",
                                                        toolTip=toolTip)
        # Overscan Value ---------------------------------------
        toolTip = "Set camera overscan amount, the extra padding around the camera resolution. \n" \
                  "Resolution gate must be on to see changes."
        self.overscanValueFloat = elements.ComboEditWidget(self, items=OVERSCAN_VALUES, label="Mask Overscan",
                                                           text=self.properties.overscanValueFloat.value,
                                                           labelStretch=3, comboRounding=2,
                                                           mainStretch=5, inputMode="float", toolTip=toolTip)
        # Match Aspect Ratio Button ---------------------------------------
        toolTip = "Matches Maya's resolution gate and film gate (sensor size) to be the same aspect ratio. \n" \
                  "Zoo Tools keeps track of the original sensor size (Film Gate). \n" \
                  "Uses the current render resolution to modify... \n" \
                  " - Camera Aperture \n" \
                  " - Film Aspect Ratio \n" \
                  " - Fit Resolution Gate"
        self.matchGateRatioCheckbox = elements.CheckBox(label="Match Res/Film Gate",
                                                        checked=False,
                                                        parent=self,
                                                        toolTip=toolTip)
        # Toggle Resolution Gate Button ---------------------------------------
        toolTip = "Displays the resolution gate (mask) of the camera."
        self.resolutionGateCheckBox = elements.CheckBox(label="Display Resolution Gate",
                                                        checked=False,
                                                        parent=self,
                                                        toolTip=toolTip)
        # Create Camera Button ---------------------------------------
        toolTip = "Creates a new camera with zxy order of rotation."
        self.createCameraBtn = elements.styledButton(text="Create New",
                                                     icon="movieCamera",
                                                     toolTip=toolTip,
                                                     style=uic.BTN_DEFAULT)
        # Duplicate Current Button ---------------------------------------
        toolTip = "Duplicates the current camera and changes the viewport to the new camera."
        self.duplicateCameraBtn = elements.styledButton(text="Duplicate Current",
                                                        icon="dropCamera",
                                                        toolTip=toolTip,
                                                        style=uic.BTN_DEFAULT)

        # Look Through Camera Button ---------------------------------------
        toolTip = "Looks through the current (usually selected) camera."
        self.lookThroughCameraBtn = elements.styledButton(text="Look Through",
                                                          icon="binoculars2",
                                                          toolTip=toolTip,
                                                          style=uic.BTN_LABEL_SML)
        # Select Camera Button ---------------------------------------
        toolTip = "Selects the active camera in the viewport. \n" \
                  "Zoo Hotkey: k "
        self.selectCameraBtn = elements.styledButton(text="Select Viewport Camera",
                                                     icon="cursorSelect",
                                                     toolTip=toolTip,
                                                     style=uic.BTN_LABEL_SML)
        # Fit Mode ---------------------------------------
        toolTip = "Resolution gate fit mode: \n" \
                  "  Fill: Always fits inside the film gate \n" \
                  "  Horizontal: Fits to the film gate horizontally, can overscan \n" \
                  "  Vertical: Fits to the film gate vertically, can overscan \n" \
                  "  Overscan: Always overscans the film gate, also used while matching gates"
        self.fitGateCombo = elements.ComboBoxRegular(label="Fit Mode",
                                                     items=FIT_MODE_LIST,
                                                     toolTip=toolTip,
                                                     setIndex=0,
                                                     labelRatio=3,
                                                     boxRatio=5)
        if uiMode == UI_MODE_ADVANCED:
            # Tear Off Perspective Button ---------------------------------------
            toolTip = "Tear off a floating window with the perspective camera."
            self.tearOffPerspectiveBtn = elements.styledButton(text="Tear Off Perspective",
                                                               icon="windowBrowser",
                                                               toolTip=toolTip,
                                                               style=uic.BTN_LABEL_SML)
            # Tear Off Current Button ---------------------------------------
            toolTip = "Tear off a floating window with the currently active camera."
            self.tearOffCurrentBtn = elements.styledButton(text="Tear Off Current",
                                                           icon="windowBrowser",
                                                           toolTip=toolTip,
                                                           style=uic.BTN_LABEL_SML)
            # Gate Mask Color ---------------------------------------
            toolTip = "Set the color of the camera mask (resolution gate) \n" \
                      "The resolution gate must be on to see changes."
            self.maskColorPicker = elements.MayaColorBtn(color=self.properties.maskColorPicker.value,
                                                         toolTip=toolTip)
            self.maskColorPicker.setWidth(100)  # temp line
            self.maskColorPaletteLabel = elements.Label(text="Mask Color",
                                                        toolTip=toolTip)
            self.maskColorPalette = elements.ColorPaletteColorList(list(MASK_COLORS), rows=1,
                                                                   totalHeight=15,
                                                                   borderRadius=2,
                                                                   spacing=4,
                                                                   toolTip=toolTip)
            # Gate Mask Opacity ---------------------------------------
            toolTip = "Set the opacity (transparency) of the camera mask (resolution gate) \n" \
                      "The resolution gate must be on to see changes."
            self.maskOpacityLabel = elements.Label("Mask Opacity", toolTip=toolTip)
            self.maskOpacitySlider = elements.FloatSlider(defaultValue=0.5,
                                                          toolTip=toolTip,
                                                          sliderMin=0.0,
                                                          sliderMax=1.0,
                                                          decimalPlaces=3, sliderRatio=5
                                                          )
            self.maskOpacitySlider.edit.setFixedWidth(40)
            # Sensor Size Combobox -----------------------------------------------------
            toolTip = "Sets the Sensor Size or Film Gate of the camera."
            self.sensorSizeEdit = elements.ComboEditWidget(self,
                                                           label="Sensor Size (mm)",
                                                           items=list(SENSOR_SIZE_LIST.keys()),
                                                           data=[c[1] for c in SENSOR_SIZE_LIST.items()],
                                                           labelStretch=3,
                                                           editCount=2,
                                                           mainStretch=5,
                                                           inputMode="float",
                                                           toolTip=toolTip)
            # Resolution mm Cropped Size ---------------------------------------
            toolTip = "The actual size used by the scene when rendering \n" \
                      "Usually the cropped size inside the sensor \n" \
                      "Though can be overscanned, ie bigger than the sensor. \n" \
                      "Cannot be modified. Use `Scene Resolution` and `Fit Mode` or `Match Gates`"
            self.resolutionSizeLabel = elements.Label(text="Resolution Size (mm)", parent=self, toolTip=toolTip)
            self.resolutionSizeVector = elements.VectorLineEdit(label="",
                                                                parent=self,
                                                                value=[1.0, 1.0],
                                                                axis=("w", "h"),
                                                                labelRatio=3,
                                                                editRatio=5,
                                                                toolTip=toolTip)
            self.resolutionSizeVector.setEnabled(False)
            # Browse camera settings ---------------------------------------
            toolTip = "Opens a browser to the VFX Camera Database \n" \
                      "https://vfxcamdb.com/"
            self.cameraDatabaseExploreBtn = elements.styledButton("",
                                                                  "globe",
                                                                  toolTip=toolTip,
                                                                  parent=self,
                                                                  minWidth=25)
            # Perspective/Orthographic ---------------------------------------
            toolTip = "Change the camera mode between perspective and orthographic modes."
            self.perspectiveCombo = elements.ComboBoxRegular(label="Perspective Mode",
                                                             items=PERSPECTIVE_MODE_LIST,
                                                             toolTip=toolTip,
                                                             setIndex=self.properties.perspectiveCombo.value,
                                                             labelRatio=3,
                                                             boxRatio=5)
            # Toggle Film Gate Button ---------------------------------------
            toolTip = "Displays the Film Gate Mask of the camera."
            self.filmGateCheckBox = elements.CheckBox(label="Display Film Gate",
                                                      checked=False,
                                                      parent=self,
                                                      toolTip=toolTip)
            # Toggle Film Gate Button ---------------------------------------
            toolTip = "Displays the Gate Mask if Film Gate or Resolution Gates are on."
            self.displayGateMaskCheckBox = elements.CheckBox(label="Display Gate Mask",
                                                             checked=True,
                                                             parent=self,
                                                             toolTip=toolTip)
            # Set Film Back All Persp Button ---------------------------------------
            toolTip = "Applies the current film back settings to all perspective cameras."
            self.applyAllPerspBtn = elements.styledButton(text="Film Back All Persp",
                                                          icon="filmGate",
                                                          toolTip=toolTip,
                                                          style=uic.BTN_DEFAULT)
            # Set Film Back All Orth Button ---------------------------------------
            toolTip = "Applies the current film back settings to all orthographic cameras."
            self.applyAllOrthBtn = elements.styledButton(text="Film Back All Ortho",
                                                         icon="filmGate",
                                                         toolTip=toolTip,
                                                         style=uic.BTN_DEFAULT)


class GuiCompact(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None):
        """Adds the layout building the compact version of the GUI:

            default uiMode - 0 is advanced (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(GuiCompact, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                         toolsetWidget=toolsetWidget)

        self.setProperty("compact", True)
        # Main Layout ---------------------------------------
        contentsLayout = elements.vBoxLayout(self,
                                             margins=(uic.WINSIDEPAD, uic.REGPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                             spacing=uic.SREG)
        # Camera Combo Layout ---------------------------------------
        camComboLayout = elements.hBoxLayout()
        camComboLayout.addWidget(self.cameraNameCombo, 11)

        # Match Aspect Toggle Btn Layout ---------------------------------------
        matchAspectBtnLayout = elements.hBoxLayout(margins=(uic.REGPAD, uic.REGPAD, uic.REGPAD, uic.REGPAD),
                                                   spacing=uic.SVLRG2)
        matchAspectBtnLayout.addWidget(self.matchGateRatioCheckbox)
        matchAspectBtnLayout.addWidget(self.resolutionGateCheckBox)
        # Main Button Layout ---------------------------------------
        buttonLayout = elements.hBoxLayout(margins=(0, uic.SMLPAD, 0, 0),
                                           spacing=uic.SREG)
        buttonLayout.addWidget(self.createCameraBtn, 6)
        buttonLayout.addWidget(self.duplicateCameraBtn, 6)
        # Look through and select btn  ---------------------------------------
        lookSelectBtnLayout = elements.hBoxLayout(spacing=uic.SVLRG2)
        lookSelectBtnLayout.addWidget(self.lookThroughCameraBtn)
        lookSelectBtnLayout.addWidget(self.selectCameraBtn)
        # Add To Main Layout ---------------------------------------
        contentsLayout.addLayout(camComboLayout)
        contentsLayout.addWidget(self.resolutionComboEdit)
        contentsLayout.addWidget(self.clippingEdit)
        contentsLayout.addWidget(self.focalLengthEdit)
        contentsLayout.addWidget(self.overscanValueFloat)
        contentsLayout.addWidget(self.fitGateCombo)
        # buttons
        contentsLayout.addLayout(matchAspectBtnLayout)
        contentsLayout.addLayout(lookSelectBtnLayout)
        contentsLayout.addLayout(buttonLayout)


class GuiAdvanced(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_ADVANCED, toolsetWidget=None):
        """Adds the layout building the advanced version of the GUI:

            default uiMode - 1 is advanced (UI_MODE_ADVANCED)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(GuiAdvanced, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                          toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        contentsLayout = elements.vBoxLayout(self,
                                             margins=(uic.WINSIDEPAD, uic.REGPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                             spacing=uic.SREG)
        # Cam Name Layout ---------------------------------------
        camComboLayout = elements.hBoxLayout()
        camComboLayout.addWidget(self.cameraNameCombo, 11)
        # Look Select Btn Layout ---------------------------------------
        lookSelectBtnLayout = elements.hBoxLayout(spacing=uic.SVLRG2)
        lookSelectBtnLayout.addWidget(self.lookThroughCameraBtn)
        lookSelectBtnLayout.addWidget(self.selectCameraBtn)
        # Match Aspect Toggle Btn Layout ---------------------------------------
        matchCheckboxLayout = elements.hBoxLayout(margins=(uic.REGPAD, uic.REGPAD, uic.REGPAD, uic.REGPAD),
                                                  spacing=uic.SVLRG2)
        matchCheckboxLayout.addWidget(self.matchGateRatioCheckbox)
        matchCheckboxLayout.addWidget(self.resolutionGateCheckBox)
        # Film Gate Mask Layout---------------------------------------
        filmGateCheckboxLayout = elements.hBoxLayout(margins=(uic.REGPAD, 0, uic.REGPAD, uic.VSMLPAD),
                                                     spacing=uic.SVLRG2)
        filmGateCheckboxLayout.addWidget(self.displayGateMaskCheckBox)
        filmGateCheckboxLayout.addWidget(self.filmGateCheckBox)
        # Tear Off Btn Layout ---------------------------------------
        tearOffBtnLayout = elements.hBoxLayout(spacing=uic.SVLRG2)
        tearOffBtnLayout.addWidget(self.tearOffPerspectiveBtn)
        tearOffBtnLayout.addWidget(self.tearOffCurrentBtn)
        # Mask Layout ---------------------------------------
        maskColorPaletteLayout = elements.hBoxLayout()
        maskColorWidgetsLayout = elements.hBoxLayout()
        maskColorPaletteLayout.addWidget(self.maskColorPaletteLabel, 3)
        maskColorPaletteLayout.addLayout(maskColorWidgetsLayout, 5)
        maskColorWidgetsLayout.addWidget(self.maskColorPicker)
        maskColorWidgetsLayout.addWidget(self.maskColorPalette)
        maskColorWidgetsLayout.addStretch(1)
        # Mask Opacity Layout ---------------------------------------
        opacityLayout = elements.hBoxLayout()
        opacityLayout.addWidget(self.maskOpacityLabel, 3)
        opacityLayout.addWidget(self.maskOpacitySlider, 5)
        # Resolution Size mm Layout ---------------------------------------
        resSizeMmLayout = elements.hBoxLayout()
        resMmEmptyLayout = elements.hBoxLayout(spacing=5)
        resMmEmptyLayout.addWidget(self.resolutionSizeVector)
        resMmEmptyLayout.addWidget(self.cameraDatabaseExploreBtn)
        resSizeMmLayout.addWidget(self.resolutionSizeLabel, 3)
        resSizeMmLayout.addLayout(resMmEmptyLayout, 5)
        # Main Button Layout ---------------------------------------
        applyGateBtnLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SREG)
        applyGateBtnLayout.addWidget(self.applyAllPerspBtn, 1)
        applyGateBtnLayout.addWidget(self.applyAllOrthBtn, 1)
        # Create Button Layout ---------------------------------------
        buttonLayout = elements.hBoxLayout(margins=(0, uic.SMLPAD, 0, 0))
        buttonLayout.addWidget(self.createCameraBtn, 1)
        buttonLayout.addWidget(self.duplicateCameraBtn, 1)
        # Add To Main Layout ---------------------------------------
        contentsLayout.addLayout(camComboLayout)
        contentsLayout.addWidget(self.resolutionComboEdit)
        contentsLayout.addWidget(elements.LabelDivider(text="Camera Options"))
        contentsLayout.addWidget(self.clippingEdit)
        contentsLayout.addWidget(self.focalLengthEdit)
        contentsLayout.addWidget(self.perspectiveCombo)
        contentsLayout.addWidget(elements.LabelDivider(text="Camera Mask"))
        contentsLayout.addLayout(maskColorPaletteLayout)
        contentsLayout.addLayout(opacityLayout)
        contentsLayout.addWidget(self.overscanValueFloat)
        contentsLayout.addWidget(elements.LabelDivider(text="Camera Film Back"))
        contentsLayout.addWidget(self.fitGateCombo)
        contentsLayout.addWidget(self.sensorSizeEdit)
        contentsLayout.addLayout(resSizeMmLayout)
        contentsLayout.addLayout(matchCheckboxLayout)
        contentsLayout.addLayout(filmGateCheckboxLayout)
        contentsLayout.addLayout(applyGateBtnLayout)
        # buttons
        contentsLayout.addWidget(elements.LabelDivider(text="Camera Other"))
        contentsLayout.addLayout(lookSelectBtnLayout)
        contentsLayout.addLayout(tearOffBtnLayout)
        contentsLayout.addLayout(buttonLayout)
