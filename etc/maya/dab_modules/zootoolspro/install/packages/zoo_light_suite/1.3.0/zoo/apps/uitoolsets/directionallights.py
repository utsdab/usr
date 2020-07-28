import locale
from functools import partial, wraps

import maya.api.OpenMaya as om2
from maya import cmds

from Qt import QtWidgets, QtCore

from zoo.preferences.core import preference
from zoo.apps.light_suite import lightconstants as lc
from zoo.preferences import preferencesconstants as pc

from zoo.apps.toolsetsui import toolsetcallbacks
from zoo.apps.toolsetsui import toolsetui
from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.libs.maya.cmds.general import undodecorator
from zoo.libs.maya.cmds.lighting import renderertransferlights
from zoo.libs.maya.cmds.lighting.renderertransferlights import INTENSITY, LIGHTCOLOR, TEMPERATURE, TEMPONOFF, \
    ROTATE, ANGLE_SOFT, DIRECTIONALS
from zoo.libs.maya.cmds.objutils import namehandling
from zoo.libs.maya.cmds.renderer import rendererload
from zoo.libs.maya.qt import cmdswidgets
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import colour
from zoo.libs.utils import zlogging

logger = zlogging.getLogger(__name__)

DFLT_RNDR_MODES = [("arnold", "Arnold"), ("redshift", "Redshift"), ("renderman", "Renderman")]

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

protect = []


def ignoreInstantApplyDecorator(method):
    """ Decorator to temporarily ignore instant apply in a GUI.

    @undoDecorator
    def lightUIMethod():
        pass
    """

    @wraps(method)
    def _disableMethod(self, *args, **kwargs):
        try:
            rembemberInstantApply = self.ignoreInstantApply
            self.ignoreInstantApply = True  # bool that tells other stuff to activate
            return method(self, *args, **kwargs)  # run the method
        finally:
            self.ignoreInstantApply = rembemberInstantApply

    return _disableMethod


class DirectionalLights(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "directionalLights"
    uiData = {"label": "Directional Lights",
              "icon": "lightarrows",
              "tooltip": "Create and manage directional light attributes with this tool",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-directional-lights/"
              }

    # ------------------------------------
    # START UP
    # ------------------------------------

    def preContentSetup(self):
        """First code to run"""
        self.toolsetWidget = self  # needed for callback decorators
        # Light Suite Pref Object PREFS_DATA stores and saves all the .prefs json data
        self.lightSuitePrefsData = preference.findSetting(lc.RELATIVE_PREFS_FILE, None)  # light suite preferences
        self.generalSettingsPrefsData = preference.findSetting(pc.RELATIVE_PREFS_FILE, None)  # renderer in general pref
        self.properties.renderer.value = self.generalSettingsPrefsData[pc.PREFS_KEY_RENDERER]

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget(), self.initAdvancedWidget()]

    def initCompactWidget(self):
        parent = QtWidgets.QWidget(parent=self)
        self.parentWgt = parent
        self.compactWidget = CompactLayout(parent=parent, properties=self.properties, toolsetWidget=self)
        self.compactWidget.colorBtn._color_widget.setStyleSheet("initCompactWidget")
        return self.compactWidget

    def initAdvancedWidget(self):
        parent = QtWidgets.QWidget(parent=self)
        self.advancedWidget = AdvancedLayout(parent=parent, properties=self.properties, toolsetWidget=self)
        return self.advancedWidget

    def postContentSetup(self):
        """Last of the initizialize code"""
        self.ignoreInstantApply = False  # for instant apply directional lights and switching ui modes
        self.uiConnections()
        self.disableEnableTemperatureWidgets()  # auto sets the disable/enable state of the temperature lineEdit
        self.refreshUpdateUIFromSelection(update=False)  # update GUI from current in scene selection
        self.instantApplyOnOff()  # show hide btns depending on the state
        self.startSelectionCallback()  # start selection callback

    # ------------------------------------
    # PROPERTIES
    # ------------------------------------

    def initializeProperties(self):
        return [{"name": "name", "label": "Light Name", "value": "directional",
                 "longName": "|ArnoldLights_grp|directional_ARN"},
                {"name": "suffix", "label": "Add Suffix", "value": True},
                {"name": "intensityTxt", "label": "Intensity", "value": 1.0},
                {"name": "softAngle", "label": "Soft Angle", "value": 2.0},
                {"name": "rotX", "label": "X Elevation", "value": -45.0},
                {"name": "rotY", "label": "Y Spin", "value": -45.0},
                {"name": "rotZ", "label": "Z Roll", "value": -0.0},
                {"name": "color", "label": "Color (Hue/Sat)", "value": (1.0, 1.0, 1.0)},
                {"name": "temperature", "label": "Temperature", "value": 6500},
                {"name": "tempBool", "label": "", "value": False},
                {"name": "instantApply", "label": "Instant Apply", "value": True},
                {"name": "renderer", "label": "", "value": "Arnold"}]

    def updateFromProperties(self):
        """ Runs update properties from the base class.

        Widgets will auto update from self.properties if linked via:

            self.linkProperty(widget, "propertyKey")
            or
            self.toolsetWidget.linkProperty(widget, "propertyKey")

        Add code after super() useful for changes such as forcing UI decimal places
        or manually adding unsupported widgets
        """
        super(DirectionalLights, self).updateFromProperties()
        rememberInstantApply = self.ignoreInstantApply
        self.blockCallbacks(True)
        self.ignoreInstantApply = True

        for uiInstance in self.widgets():  # both GUIs
            uiInstance.intensityTxt.setValue(self.properties.intensityTxt.value)
            uiInstance.softnessTxt.setValue(self.properties.softAngle.value)
        # UI_MODE_ADVANCED:
        self.advancedWidget.rotXTxt.setValue(self.properties.rotX.value)
        self.advancedWidget.rotYTxt.setValue(self.properties.rotY.value)
        self.advancedWidget.rotZTxt.setValue(self.properties.rotZ.value)
        self.advancedWidget.temperatureTxt.setValue(self.properties.temperature.value)

        self.ignoreInstantApply = rememberInstantApply
        self.blockCallbacks(False)

    def widgets(self):
        """

        :return:
        :rtype:  list[AdvancedLayout or CompactLayout]
        """
        return super(DirectionalLights, self).widgets()

    # ------------------------------------
    # POPUP WINDOWS
    # ------------------------------------

    def ui_loadRenderer(self):
        message = "The {} renderer isn't loaded. Load now?".format(self.properties.renderer.value)
        # parent is None to parent to Maya to fix stylesheet issues
        okPressed = elements.MessageBox_ok(windowName="Load Renderer", parent=None, message=message)
        return okPressed

    # ------------------------------------
    # CALLBACKS
    # ------------------------------------

    def selectionChanged(self, selection):
        """Run when the callback selection changes, updates the GUI if an object is selected

        Callbacks are handled automatically by toolsetcallbacks.py which this class inherits"""
        if not selection:  # then don't update
            return
        logger.debug(">>>>>>>>>>>>>>> SELECTION CHANGED UPDATING 'CREATE DIRECTIONAL GUI' <<<<<<<<<<<<<<<<<<<<")
        self.refreshUpdateUIFromSelection()  # will update the GUI

    # ------------------------------------
    # MENUS - RIGHT CLICK
    # ------------------------------------

    @toolsetcallbacks.ignoreCallbackDecorator
    def setLightNameMenuModes(self):
        """Retrieves all area lights in the scene and creates the self.lightNameMenu menu so the user can switch

        Does a bunch of name handling to account for the UI LongName (self.properties.name.longName)
        Auto compares the long name to see if it is the first obj selected, Note: could use UUIDs instead

        The current light in the ui is removed from the menu list if selected
        """
        logger.debug("setLightNameMenuModes()")
        modeList = list()
        currentNameUnique = None
        # area light list will be long names
        lightListLong = renderertransferlights.getAllDirectionalLightsInScene(self.properties.renderer.value)[0]
        currentUiNameLong = self.properties.name.longName  # already has suffix
        currentNameExits = cmds.objExists(currentUiNameLong)
        if currentNameExits:  # then get the display name
            currentNameUnique = namehandling.getUniqueShortName(currentUiNameLong)
        if lightListLong:  # There are other area lights in the scene
            for i, obj in enumerate(lightListLong):
                if currentUiNameLong == obj:
                    lightListLong.pop(i)  # is the UI name so remove
                    break
        selObjs = cmds.ls(selection=True, long=True)
        if not selObjs and currentNameExits:
            modeList.append(("cursorSelect", "Select {}".format(currentNameUnique)))  # user can select the light
            modeList.append((None, "separator"))
        elif selObjs and currentNameExits:
            objLongName = selObjs[0]
            if currentUiNameLong != objLongName:  # current light is not selected
                modeList.append(("cursorSelect", "Select {}".format(currentNameUnique)))  # user can select the light
        if lightListLong:
            locale.setlocale(locale.LC_ALL, '')  # needed for sorting unicode
            sorted(lightListLong, cmp=locale.strcoll)  # alphabetalize
            for light in lightListLong:
                modeList.append(("lightarrows", namehandling.getUniqueShortName(light)))
        else:
            modeList.append(("", "No Other Directional Lights"))
        modeList.append((None, "separator"))
        modeList.append(("windowBrowser", "Open Light Editor"))
        self.currentWidget().lightNameMenu.actionConnectList(modeList)

    def selectCurrentLight(self):
        """Selects the current light from the UI Light Name text box as called by a right click menu
        """
        logger.debug("selectCurrentLight()")
        lightNameLong = self.properties.name.longName
        if not cmds.objExists(lightNameLong):
            currentUIName = self.returnLightNameSuffixed(self.properties.name.value)
            if not cmds.objExists(currentUIName):
                om2.MGlobal.displayWarning("Area Light `{}` or `{}` does not exist in the scene".format(lightNameLong,
                                                                                                        currentUIName))
                return
        cmds.select(lightNameLong, replace=True)

    @toolsetcallbacks.ignoreCallbackDecorator
    def menuSwitchToAreaLight(self):
        """Runs the light logic called from the drop-down right-click menu on the Light Name lineEdit (name text):

            - Select Current Light
            - Select Other Lights from scene
            - Open the Mayas Light Editor

        """
        logger.debug("menuSwitchToAreaLight()")
        lightTransformName = self.currentWidget().lightNameMenu.currentMenuItem()
        if lightTransformName == "No Other Area Lights":
            return
        elif "Select " in lightTransformName:  # then is the select object
            self.selectCurrentLight()
            return
        elif lightTransformName == "Open Light Editor":
            # opens Maya's Light Editor
            import maya.app.renderSetup.views.lightEditor.editor as __mod
            try:
                __mod.openEditorUI()
            finally:
                del __mod
            return
        cmds.select(lightTransformName, replace=True)
        self.refreshUpdateUIFromSelection()

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
    # CREATE LIGHTS
    # ------------------------------------

    @toolsetcallbacks.ignoreCallbackDecorator
    @undodecorator.undoDecorator
    def createDirectionalDropCam(self):
        """Creates a directional light from the same position as the current camera, with ui settings"""
        logger.debug("createDirectionalDropCam()")
        rendererNiceName, newName, addSuffix, lightDictAttributes = self.getAllUiAttrs()
        lightTransform, lightShape, warningState = renderertransferlights.createDirectionalLightMatchPos(
            lightDictAttributes,
            newName,
            rendererNiceName,
            suffix=addSuffix,
            position="camera")
        lightsTransformList = [lightTransform]
        renderertransferlights.cleanupLights(rendererNiceName, lightsTransformList,
                                             selectLights=True)  # group the light

    @toolsetcallbacks.ignoreCallbackDecorator
    @undodecorator.undoDecorator
    def createDirectionalLight(self):
        """Create a directional light at world center with the ui settings"""
        logger.debug("createDirectionalLight()")
        rendererNiceName, newName, addSuffix, lightDictAttributes = self.getAllUiAttrs()
        if not self.checkRenderLoaded(rendererNiceName):
            return
        lightTransform, lightShape, warningState = renderertransferlights.createDirectionalDictRenderer(
            lightDictAttributes,
            newName,
            rendererNiceName,
            cleanup=False,
            suffix=addSuffix)
        lightsTransformList = [lightTransform]
        renderertransferlights.cleanupLights(rendererNiceName, lightsTransformList,
                                             selectLights=True)  # group the light

    # ------------------------------------
    # SET (APPLY) LIGHTS
    # ------------------------------------

    def findUILightSelection(self, prioritizeNameBool=True, message=True):
        """Finds all the directional lights in the scene intelligently, also uses GUI name too

        :param prioritizeNameBool: a name, usually from the GUI to affect even if it's not selected
        :type prioritizeNameBool: bool
        :param message: report the message to the user?
        :type message: bool
        :return dirLightTransforms: a list of light transform names
        :rtype dirLightTransforms: list
        :return dirLightShapes: a list of light shape names
        :rtype dirLightShapes: list
        """
        logger.debug("findUILightSelection()")
        prioritizeLongName = ""
        if prioritizeNameBool:
            prioritizeLongName = self.properties.name.longName
        rendererNiceName = self.properties.renderer.value
        dirLightTransforms, dirLightShapes = \
            renderertransferlights.getSelectedDirectionalLights(rendererNiceName, message=message,
                                                                prioritizeName=prioritizeLongName)
        return dirLightTransforms, dirLightShapes

    def setAttributesGUI(self, lightDictAttributes, message=True, prioritizeNameBool=True):
        """ Set attributes from the GUI using selection and the name of the GUI light, if it exists in the scene
        Uses a smart selection filter to set lights

        :param lightDictAttributes: a dict with all the Maya attributes to set on the light
        :type lightDictAttributes: dict
        :param message: report the message to the user?
        :type message: bool
        :param prioritizeNameBool: a name, usually from the GUI to affect even if it's not selected
        :type prioritizeNameBool: bool
        """
        logger.debug("setAttributesGUI()")
        dirLightTransforms, dirLightShapes = self.findUILightSelection(prioritizeNameBool, message)
        if not dirLightTransforms:
            return
        if not dirLightTransforms:  # nothing found
            return
        for lightShape in dirLightShapes:  # should be updated to mix behaviour
            lightDictCopy = dict(lightDictAttributes)  # must make a copy as can be altered by the following function
            renderertransferlights.setDirectionalAttr(lightShape,
                                                      self.properties.renderer.value,
                                                      lightDictCopy)

        if message:
            lightShapesUnique = list(namehandling.getUniqueShortNameList(dirLightShapes))  # be sure a copy list
            om2.MGlobal.displayInfo("Success Directional Light Attributes Changed: {}".format(lightShapesUnique))
        self.updateFromProperties()  # update the GUI in case of changes

    @toolsetcallbacks.ignoreCallbackDecorator
    @undodecorator.undoDecorator
    def directionalSetAttributes(self, allAttrs=False, intensity=False, lightColor=False, temperature=False,
                                 softAngle=False, rotX=False, rotY=False, rotZ=False, message=True,
                                 prioritizeNameBool=True):
        """Sets the directional lights values
        """
        logger.debug("directionalSetAttributes()")
        lightDictAttributes = renderertransferlights.getDirectionalDictAttributes()  # dict with keys but empty values
        if intensity or allAttrs:
            lightDictAttributes[INTENSITY] = self.properties.intensityTxt.value
        if lightColor or allAttrs:
            lightDictAttributes[LIGHTCOLOR] = self.properties.color.value
        if temperature or allAttrs:
            lightDictAttributes[TEMPONOFF] = self.properties.tempBool.value
            lightDictAttributes[TEMPERATURE] = self.properties.temperature.value
            if self.properties.tempBool.value:
                colorSrgbInt = colour.convertKelvinToRGB(self.properties.temperature.value)
                colorSrgbFloat = colour.rgbIntToFloat(colorSrgbInt)
                colorLinear = colour.convertColorSrgbToLinear(colorSrgbFloat)
                self.properties.color.value = colorLinear
                lightDictAttributes[LIGHTCOLOR] = colorLinear
        if softAngle or allAttrs:
            lightDictAttributes[ANGLE_SOFT] = self.properties.softAngle.value
        if any((rotX, rotY, rotZ, allAttrs)):  # should be split to support individual attr changes
            lightDictAttributes[ROTATE] = (self.properties.rotX.value, self.properties.rotY.value,
                                           self.properties.rotZ.value)
        self.setAttributesGUI(lightDictAttributes, message=message, prioritizeNameBool=prioritizeNameBool)

    # ------------------------------------
    # INSTANT SET (APPLY) LIGHTS
    # ------------------------------------

    def instantApplyOnOff(self):
        """Stops/starts the selection callback and hides/shows the get/set arrow icons
        """
        self.toolsetWidget.saveProperties()
        if self.properties.instantApply.value:
            self.startSelectionCallback()
            for uiInstance in self.widgets():
                for btn in uiInstance.pushPullBtns:
                    btn.hide()
        else:
            self.stopSelectionCallback()
            for uiInstance in self.widgets():
                for btn in uiInstance.pushPullBtns:
                    btn.show()

    def instantSetLightDirectionalName(self):
        """renames lights with instant apply on
        """
        if not self.properties.instantApply.value:  # instant apply not checked
            return
        if self.ignoreInstantApply:  # will be set if changing ui modes
            return
        logger.debug("instantSetLightDirectionalName()")
        self.dirRenameLight()

    def instantSetDirectional(self, intensity=False, lightColor=False, temperature=False, softAngle=False,
                              rotX=False, rotY=False, rotZ=False, message=True):
        """sets the directional light attributes instantly if instant apply is checked on
        """
        logger.debug("instantSetDirectional()")
        if not self.properties.instantApply.value:  # instant apply not checked
            return
        if self.ignoreInstantApply:  # will be set if changing ui modes
            return
        rendererNiceName = self.properties.renderer.value
        if not renderertransferlights.getAllDirectionalLightsInScene(rendererNiceName)[0]:
            message = False  # switches off as no directional lights in scene, so don't report error for instant apply
        if lightColor:
            self.properties.tempBool.value = 0
            temperature = True  # also set temperature to update the tempBool value
        if lightColor:
            temperature = True  # also update the color swatch
        self.directionalSetAttributes(intensity=intensity, lightColor=lightColor, temperature=temperature,
                                      softAngle=softAngle, rotX=rotX, rotY=rotY, rotZ=rotZ, message=message)

    # ------------------------------------
    # GET (RETRIEVE) LIGHTS
    # ------------------------------------

    def refreshUpdateUIFromSelection(self, update=True):
        """Gets all the attributes (properties) from the first selected light and updates the scene

        :param update: if False will skip updating the UI, refreshUpdateUIFromSelection otherwise updates too much
        :type update: bool
        """
        logger.debug("refreshUpdateUIFromSelection()")
        if not rendererload.getRendererIsLoaded(self.properties.renderer.value):
            return  # the renderer is not loaded so don't update from scene
        rememberInstantApply = self.ignoreInstantApply
        self.ignoreInstantApply = True
        self.getDirectionalAttrs(getAll=True, update=False)  # get intensity/exposure as per the light
        self.getLightName(update=False)
        if update:
            self.updateFromProperties()
        self.ignoreInstantApply = rememberInstantApply

    def getAllUiAttrs(self):
        """Return all the Maya directional light attributes for the create light functions"""
        logger.debug("getAllUiAttrs()")
        lightDictAttributes = renderertransferlights.getDirectionalDictAttributes()  # dict with keys but empty values
        rendererNiceName = self.properties.renderer.value
        newName = self.properties.name.value
        addSuffix = self.properties.suffix.value
        lightDictAttributes[INTENSITY] = self.properties.intensityTxt.value
        lightDictAttributes[LIGHTCOLOR] = self.properties.color.value  # is linear
        lightDictAttributes[TEMPERATURE] = self.properties.temperature.value
        lightDictAttributes[TEMPONOFF] = self.properties.tempBool.value
        lightDictAttributes[ROTATE] = (self.properties.rotX.value, self.properties.rotY.value,
                                       self.properties.rotZ.value)
        lightDictAttributes[ANGLE_SOFT] = self.properties.softAngle.value
        return rendererNiceName, newName, addSuffix, lightDictAttributes

    @toolsetcallbacks.ignoreCallbackDecorator
    def getLightName(self, update=False):
        """retrieves the name of the first selected light in the scene

        :param update: if False will skip updating the UI, refreshUpdateUIFromSelection otherwise updates too much
        :type update: bool
        """
        # TODO: could include the ui name in the getLightNameSelected
        newName, suffixRemoved = \
            renderertransferlights.getLightNameSelected(removeSuffix=True, message=False,
                                                        lightFamily=renderertransferlights.DIRECTIONALS,
                                                        rendererNiceName=self.properties.renderer.value)
        if not newName:  # could be None
            return
        # incoming newName is unique, can be long or short and has no suffix
        self.properties.suffix.value = suffixRemoved
        newNameWithSuffix = self.returnLightNameSuffixed(newName)
        self.properties.name.longName = namehandling.getLongNameFromShort(newNameWithSuffix)
        newName = newName.split("|")[-1]  # may not be in scene as no suffix, may be long name
        self.properties.name.value = newName
        if update:
            self.updateFromProperties()

    @toolsetcallbacks.ignoreCallbackDecorator
    def getDirectionalName(self):
        """Pulls the name of the selected directional light
        """
        logger.debug("getDirectionalName()")
        rendererNiceName = self.properties.renderer.value
        removeSuffix = self.properties.suffix.value
        newName, suffixRemoved = renderertransferlights.getLightNameSelected(removeSuffix=removeSuffix,
                                                                             lightFamily=DIRECTIONALS,
                                                                             rendererNiceName=rendererNiceName)
        if not newName:
            return
        # incoming newName is long and has no suffix
        self.properties.suffix.value = suffixRemoved
        newLongWithSuffix = self.returnLightNameSuffixed(newName)  # must add potential suffix for long name
        newShortName = namehandling.getShortName(newName)  # is the short name for the GUI
        self.properties.name.value = newShortName
        self.properties.name.longName = newLongWithSuffix
        self.updateFromProperties()

    @toolsetcallbacks.ignoreCallbackDecorator
    @undodecorator.undoDecorator
    def getDirectionalAttrs(self, getAll=False, getIntensity=False, getColor=False, getTemperature=False,
                            getTempOnOff=False, getRotation=False, getSoftAngle=False, message=False, update=True):
        """gets directional light attributes from any selected directional light,
        Note will return random light if multiple selected due to dictionary

        :param message: report the message to the user?
        :type message: bool
        :param update: if False will skip updating the UI, refreshUpdateUIFromSelection otherwise updates too much
        :type update: bool
        """
        logger.debug("getDirectionalAttrs()")
        rendererNiceName = self.properties.renderer.value
        attrValDict = renderertransferlights.getDirectionalAttrSelected(rendererNiceName, getIntensity=True,
                                                                        getColor=True, getTemperature=True,
                                                                        getTempOnOff=True, getAngleSoft=True,
                                                                        getRotation=True, message=message,
                                                                        returnFirstLight=True)
        if not attrValDict:
            if message:
                om2.MGlobal.displayWarning("No Directional Lights Found For Renderer {}".format(rendererNiceName))
            return
        attrValDict = attrValDict[attrValDict.keys()[0]]  # get any dict from the nested dict (should be only one light)
        if attrValDict:  # set properties
            if getIntensity or getAll:
                self.properties.intensityTxt.value = attrValDict[INTENSITY]
            if getColor or getAll:
                self.properties.color.value = attrValDict[LIGHTCOLOR]  # is already linear
            if getTemperature or getAll:
                self.properties.temperature.value = attrValDict[TEMPERATURE]
                self.properties.tempBool.value = attrValDict[TEMPONOFF]
            if getSoftAngle or getAll:
                self.properties.softAngle.value = attrValDict[ANGLE_SOFT]
            if getRotation or getAll:
                self.properties.rotX.value = attrValDict[ROTATE][0]
                self.properties.rotY.value = attrValDict[ROTATE][1]
                self.properties.rotZ.value = attrValDict[ROTATE][2]
            if update:
                self.updateFromProperties()  # update GUI

    # ------------------------------------
    # OFFSET ATTRIBUTES
    # ------------------------------------

    @toolsetcallbacks.ignoreCallbackDecorator
    @ignoreInstantApplyDecorator
    @undodecorator.undoDecorator
    def directionalOffsets(self, rotX=False, rotY=False, rotZ=False, softAngle=False, temperature=False,
                           intensity=False, neg=False, message=True, prioritizeNameBool=True):
        """controls the offset buttons and offset amounts

        All kwargs are bools.  Will be True if offsetting the Maya attribute
        """
        logger.debug("directionalOffsets()")
        multiplier, reset = self.dirCntrlShiftMultiplier()
        rendererNiceName = self.properties.renderer.value
        lightDictAttributes = renderertransferlights.getDirectionalDictAttributes()
        dirLightTransforms, dirLightShapes = self.findUILightSelection(prioritizeNameBool, message)
        if not dirLightTransforms:  # nothing found
            return
        if rotX or rotY or rotZ:
            if not reset:
                offset = 5.0 * multiplier
                if neg:
                    offset = -offset
                rotXValue = self.properties.rotX.value
                rotYValue = self.properties.rotY.value
                rotZValue = self.properties.rotZ.value
            if rotX:
                if reset:
                    rotXValue = self.properties.rotX.default
                else:
                    rotXValue += offset
                self.properties.rotX.value = rotXValue
            if rotY:
                if reset:
                    rotYValue = self.properties.rotY.default
                else:
                    rotYValue += offset
                self.properties.rotY.value = rotYValue
            if rotZ:
                if reset:
                    rotZValue = self.properties.rotZ.default
                else:
                    rotZValue += offset
                self.properties.rotZ.value = rotZValue
            lightDictAttributes[ROTATE] = (rotXValue, rotYValue, rotZValue)
        if temperature:
            if reset:
                lightDictAttributes[TEMPERATURE] = self.properties.temperature.default
                lightDictAttributes[TEMPONOFF] = self.properties.tempBool.default
            else:
                offset = 200.0 * multiplier
                if neg:
                    offset = -offset
                lightDictAttributes[TEMPERATURE] = self.properties.temperature.value + offset
                lightDictAttributes[TEMPONOFF] = True
            self.properties.temperature.value = lightDictAttributes[TEMPERATURE]
            self.properties.tempBool.value = lightDictAttributes[TEMPONOFF]
            colorSrgbInt = colour.convertKelvinToRGB(self.properties.temperature.value)
            colorSrgbFloat = colour.rgbIntToFloat(colorSrgbInt)
            colorLinear = colour.convertColorSrgbToLinear(colorSrgbFloat)
            self.properties.color.value = colorLinear
            lightDictAttributes[LIGHTCOLOR] = colorLinear
        if softAngle:
            if reset:
                lightDictAttributes[ANGLE_SOFT] = self.properties.softAngle.default
            else:
                offset = 2.0 * multiplier
                if neg:
                    offset = -offset
                lightDictAttributes[ANGLE_SOFT] = self.properties.softAngle.value + offset
                if lightDictAttributes[ANGLE_SOFT] < 0:
                    lightDictAttributes[ANGLE_SOFT] = 0.0
            self.properties.softAngle.value = lightDictAttributes[ANGLE_SOFT]
        if intensity:
            if reset:
                lightDictAttributes[INTENSITY] = self.properties.intensityTxt.default
            else:
                offset = 10.0 * multiplier
                if neg:
                    offset = -10.0

                intensity = self.properties.intensityTxt.value
                lightDictAttributes[INTENSITY] = intensity + (intensity * (offset / 100.0))
            self.properties.intensityTxt.value = lightDictAttributes[INTENSITY]
        for lightShape in dirLightShapes:  # should be updated to mix behaviour
            renderertransferlights.setDirectionalAttr(lightShape, rendererNiceName, lightDictAttributes)
        self.updateFromProperties()
        if message:
            lightShapesUnique = list(namehandling.getUniqueShortNameList(dirLightShapes))  # be sure a copy list
            om2.MGlobal.displayInfo("Success Directional Light Attributes Changed: {}".format(lightShapesUnique))

    def dirCntrlShiftMultiplier(self):
        """For offset functions multiply shift and minimise if ctrl is held down
        If alt then call the reset option

        :return multiplier: multiply value, .2 if ctrl 5 if shift 1 if None
        :rtype multiplier: float
        :return reset: reset becomes true for resetting
        :rtype reset: bool
        """
        logger.debug("dirCntrlShiftMultiplier()")
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            return 5.0, False
        elif modifiers == QtCore.Qt.ControlModifier:
            return 0.2, False
        elif modifiers == QtCore.Qt.AltModifier:
            return 1, True
        return 1.0, False

    def dirHueSatOffset(self, offsetHue=False, offsetSat=False, neg=False):
        logger.debug("dirHueSatOffset()")
        if self.properties.tempBool.value:  # is in temp mode so disable the hue sat buttons
            self.properties.tempBool.value = 0
        colorSrgbFloat = colour.convertColorLinearToSrgb(self.properties.color.value)
        hsvColor = colour.convertRgbToHsv(colorSrgbFloat)
        multiplier, reset = self.dirCntrlShiftMultiplier()
        # do the offset
        if offsetHue:
            if reset:
                hsvColor = (0.0, 0.0, 1.0)
            else:
                offset = 18.0 * multiplier
                if neg:
                    offset = -offset
                hsvColor = colour.offsetHueColor(hsvColor, offset)
        elif offsetSat:
            if reset:
                hsvColor = (0.0, 0.0, 1.0)
            else:
                offset = .05 * multiplier
                if neg:
                    offset = -offset
                hsvColor = colour.offsetSaturation(hsvColor, offset)
        # change the color swatch
        colorSrgbFloat = colour.convertHsvToRgb(hsvColor)
        colorLinearFloat = colour.convertColorSrgbToLinear(colorSrgbFloat)
        self.properties.color.value = colorLinearFloat
        self.properties.tempBool.value = 0
        # set color
        self.updateFromProperties()  # update the GUI
        self.directionalSetAttributes(lightColor=True, temperature=True, prioritizeNameBool=True)

    # ------------------------------------
    # LIGHT NAME/RENAME
    # ------------------------------------

    def returnLightNameNoSuffix(self, lightName):
        """Returns the light name now without it's suffix matching any renderer eg "lightName_ARN" > "lightName"

        :param lightName: the string name of the light potentially with the suffix
        :type lightName: str
        :return lightName: the light renamed now without it's suffix
        :rtype lightName: str
        """
        if self.properties.suffix.value:
            return renderertransferlights.removeRendererSuffix(lightName)[0]
        return lightName

    def returnLightNameSuffixed(self, lightName):
        """Returns the light name now with a suffix matching the renderer eg "lightName" > "lightName_ARN" (Arnold)

        :param lightName: the string name of the light before the suffix
        :type lightName: str
        :return lightName: the light renamed now with a suffix
        :rtype lightName: str
        """
        if not self.properties.suffix.value:
            return lightName
        suffix = renderertransferlights.RENDERER_SUFFIX[self.properties.renderer.value]
        return "_".join([lightName, suffix])

    @toolsetcallbacks.ignoreCallbackDecorator
    @ignoreInstantApplyDecorator
    @undodecorator.undoDecorator
    def dirRenameLight(self):
        """rename the directional light
        """
        logger.debug("dirRenameLight()")
        newName = self.properties.name.value
        renameLight = self.properties.name.longName
        if not cmds.objExists(renameLight):
            om2.MGlobal.displayWarning("Directional light does not exist: {}".format(renameLight))
            return
        lightTransform, lightShape = renderertransferlights.renameLight(renameLight,
                                                                        newName,
                                                                        addSuffix=self.properties.suffix.value,
                                                                        lightFamily=renderertransferlights.DIRECTIONALS)
        # lightTransform is always unique so can longname it
        self.properties.name.longName = namehandling.getLongNameFromShort(lightTransform)
        # see whether to update the ui name
        lightTransformNoSuffix = self.returnLightNameNoSuffix(namehandling.getShortName(lightTransform))
        if lightTransformNoSuffix != newName:  # then the UI needs to update
            self.properties.name.value = lightTransformNoSuffix
            self.updateFromProperties()

    # ------------------------------------
    # THIRD PARTY
    # ------------------------------------

    def placeReflection(self):
        """placeReflection by braverabbit https://github.com/IngoClemens/placeReflection"""
        try:  # Place reflection is a community tool and may not be installed
            from zoo.apps.braverabbit_place_reflection import placeReflection
            placeReflectionTool = placeReflection.PlaceReflection()
            placeReflectionTool.create()
        except ImportError:
            om2.MGlobal.displayWarning("The package `third_party_community` must be installed for "
                                       "Place Reflection by Braverabbit.")

    def placeReflectionDirectional(self):
        """Automatically select a directional lights if only one in the scene then run placeReflection
        placeReflection by braverabbit https://github.com/IngoClemens/placeReflection"""
        logger.debug("placeReflectionDirectional()")
        rendererNiceName = self.properties.renderer.value
        dirLightTransforms, dirLightShapes = renderertransferlights.getSelectedDirectionalLights(rendererNiceName,
                                                                                                 message=False)
        if dirLightTransforms:
            cmds.select(dirLightTransforms[0], replace=True)
        self.placeReflection()

    # ------------------------------------
    # COLOR
    # ------------------------------------

    def disableEnableTemperatureWidgets(self):
        """Disable/enable temperature widget
        """
        logger.debug("disableEnableTemperatureWidgets()")
        for uiInstance in self.widgets():
            uiInstance.colorBtn.setDisabledLabel(self.properties.tempBool.value)
        self.advancedWidget.temperatureTxt.setDisabled(not self.properties.tempBool.value)

    # ------------------------------------
    # CONNECTIONS
    # ------------------------------------

    def uiConnections(self):
        """Hooks up the actual button/widgets functionality
        """
        for uiInstance in self.widgets():  # both GUIs
            uiInstance.renameBtn.clicked.connect(self.dirRenameLight)
            uiInstance.createLightBtn.clicked.connect(self.createDirectionalLight)
            uiInstance.camDropBtn.clicked.connect(self.createDirectionalDropCam)
            # place reflection
            uiInstance.placeReflectionBtn.clicked.connect(self.placeReflectionDirectional)
            # push
            uiInstance.allPushBtn.clicked.connect(partial(self.directionalSetAttributes, allAttrs=True))
            uiInstance.intensityPushBtn.clicked.connect(partial(self.directionalSetAttributes, intensity=True))
            uiInstance.colorPushBtn.clicked.connect(partial(self.directionalSetAttributes, lightColor=True))
            uiInstance.softnessPushBtn.clicked.connect(partial(self.directionalSetAttributes, softAngle=True))
            # pull
            uiInstance.allPullBtn.clicked.connect(partial(self.getDirectionalAttrs, getAll=True))
            uiInstance.namePullBtn.clicked.connect(self.getDirectionalName)
            uiInstance.intensityPullBtn.clicked.connect(partial(self.getDirectionalAttrs, getIntensity=True))
            uiInstance.colorPullBtn.clicked.connect(partial(self.getDirectionalAttrs, getColor=True))
            uiInstance.softnessPullBtn.clicked.connect(partial(self.getDirectionalAttrs, getSoftAngle=True))
            # offsets
            uiInstance.intensityBrightenBtn.clicked.connect(partial(self.directionalOffsets, neg=False, intensity=True))
            uiInstance.intensityDarkenBtn.clicked.connect(partial(self.directionalOffsets, neg=True, intensity=True))
            uiInstance.softnessPosBtn.clicked.connect(partial(self.directionalOffsets, neg=False, softAngle=True))
            uiInstance.softnessNegBtn.clicked.connect(partial(self.directionalOffsets, neg=True, softAngle=True))
            uiInstance.colHuePosBtn.clicked.connect(partial(self.dirHueSatOffset, neg=False, offsetHue=True))
            uiInstance.colHueNegBtn.clicked.connect(partial(self.dirHueSatOffset, neg=True, offsetHue=True))
            uiInstance.colSatPosBtn.clicked.connect(partial(self.dirHueSatOffset, neg=False, offsetSat=True))
            uiInstance.colSatBtnNeg.clicked.connect(partial(self.dirHueSatOffset, neg=True, offsetSat=True))
            # instant apply
            uiInstance.nameTxt.edit.textModified.connect(self.instantSetLightDirectionalName)
            uiInstance.suffixCheckbox.stateChanged.connect(self.instantSetLightDirectionalName)
            uiInstance.intensityTxt.edit.textModified.connect(partial(self.instantSetDirectional, intensity=True))
            uiInstance.colorBtn.colorChanged.connect(partial(self.instantSetDirectional, lightColor=True))
            uiInstance.softnessTxt.edit.textModified.connect(partial(self.instantSetDirectional, softAngle=True))
            # menu
            uiInstance.lightNameMenu.aboutToShow.connect(self.setLightNameMenuModes)
            uiInstance.lightNameMenu.menuChanged.connect(self.menuSwitchToAreaLight)
            # change renderer
            uiInstance.rendererLoaded.actionTriggered.connect(self.global_changeRenderer)
        # UI_MODE_ADVANCED only ---------------------
        # push adv
        self.advancedWidget.rotXPushBtn.clicked.connect(partial(self.directionalSetAttributes, rotX=True))
        self.advancedWidget.rotYPushBtn.clicked.connect(partial(self.directionalSetAttributes, rotY=True))
        self.advancedWidget.rotZPushBtn.clicked.connect(partial(self.directionalSetAttributes, rotZ=True))
        self.advancedWidget.tempPushBtn.clicked.connect(partial(self.directionalSetAttributes, temperature=True))
        # pull adv
        self.advancedWidget.rotXPullBtn.clicked.connect(partial(self.getDirectionalAttrs, getRotation=True))
        self.advancedWidget.rotYPullBtn.clicked.connect(partial(self.getDirectionalAttrs, getRotation=True))
        self.advancedWidget.rotZPullBtn.clicked.connect(partial(self.getDirectionalAttrs, getRotation=True))
        self.advancedWidget.tempPullBtn.clicked.connect(partial(self.getDirectionalAttrs, getTemperature=True))
        # offsets adv
        self.advancedWidget.rotXOffsetBtnPos.clicked.connect(partial(self.directionalOffsets, neg=False, rotX=True))
        self.advancedWidget.rotXOffsetBtnNeg.clicked.connect(partial(self.directionalOffsets, neg=True, rotX=True))
        self.advancedWidget.rotYOffsetPosBtn.clicked.connect(partial(self.directionalOffsets, neg=False, rotY=True))
        self.advancedWidget.rotYOffsetNegBtn.clicked.connect(partial(self.directionalOffsets, neg=True, rotY=True))
        self.advancedWidget.rotZOffsetPosBtn.clicked.connect(partial(self.directionalOffsets, neg=False, rotZ=True))
        self.advancedWidget.rotZOffsetNegBtn.clicked.connect(partial(self.directionalOffsets, neg=True, rotZ=True))
        self.advancedWidget.tempOffsetPosBtn.clicked.connect(
            partial(self.directionalOffsets, neg=False, temperature=True))
        self.advancedWidget.tempOffsetNegBtn.clicked.connect(
            partial(self.directionalOffsets, neg=True, temperature=True))
        # instant apply
        self.advancedWidget.rotXTxt.edit.textModified.connect(partial(self.instantSetDirectional, rotX=True))
        self.advancedWidget.rotYTxt.edit.textModified.connect(partial(self.instantSetDirectional, rotY=True))
        self.advancedWidget.rotZTxt.edit.textModified.connect(partial(self.instantSetDirectional, rotZ=True))
        self.advancedWidget.temperatureTxt.edit.textModified.connect(
            partial(self.instantSetDirectional, temperature=True))
        self.advancedWidget.tempOnOffBx.stateChanged.connect(partial(self.instantSetDirectional, temperature=True))
        # disable enable
        self.advancedWidget.tempOnOffBx.stateChanged.connect(self.disableEnableTemperatureWidgets)
        self.advancedWidget.instantApplyCheckbox.stateChanged.connect(self.instantApplyOnOff)
        # callback connections
        self.selectionCallbacks.callback.connect(self.selectionChanged)  # monitor selection
        self.toolsetActivated.connect(self.startSelectionCallback)
        self.toolsetDeactivated.connect(self.stopSelectionCallback)


class AllWidgets(QtWidgets.QWidget):
    """Create all the widgets for all GUIs, compact and advanced etc"""

    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None):
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
        """
        super(AllWidgets, self).__init__(parent=parent)
        self.toolsetWidget = toolsetWidget
        self.properties = properties
        self.uiMode = uiMode
        self.parentWidget = parent
        self.listeningForRenderer = True  # if True the renderer can be set from other windows or toolsets
        self.pushPullBtns = list()
        # Directional Name --------------------------------------
        toolTip = "The light's name. Suffix will be added if checkbox on."
        self.nameTxt = elements.StringEdit(self.properties.name.label,
                                           self.properties.name.value,
                                           parent=self,
                                           toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.nameTxt, "name")
        self.lightNameMenu = elements.ExtendedMenu(searchVisible=True)
        self.nameTxt.setMenu(self.lightNameMenu)  # right click. Menu items are dynamic self.setLightNameMenuModes()
        self.nameTxt.setMenu(self.lightNameMenu, mouseButton=QtCore.Qt.LeftButton)  # left click
        # for further menu set see self.setLightNameMenuModes()
        toolTip = "Automatically add a suffix to the light's name Eg. directional_ARN\n" \
                  "Arnold: _ARN\n" \
                  "Redshift: _RS\n" \
                  "Renderman: _PXR"
        self.suffixCheckbox = elements.CheckBox(self.properties.suffix.label,
                                                checked=self.properties.suffix.default,
                                                parent=self,
                                                toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.suffixCheckbox, "suffix")
        toolTip = "Rename the selected, or the only directional light in the scene"
        self.renameBtn = elements.styledButton("", "arrowRight",
                                               self,
                                               toolTip,
                                               style=uic.BTN_TRANSPARENT_BG,
                                               minWidth=uic.BTN_W_ICN_REG)
        self.pushPullBtns.append(self.renameBtn)
        toolTip = "Get the name of the selected, or the only directional light in the scene"
        self.namePullBtn = elements.styledButton("", "arrowLeft",
                                                 self,
                                                 toolTip,
                                                 style=uic.BTN_TRANSPARENT_BG,
                                                 minWidth=uic.BTN_W_ICN_REG)
        self.pushPullBtns.append(self.namePullBtn)
        # Directional Intensity --------------------------------------
        self.intensityTxt = elements.FloatEdit(self.properties.intensityTxt.label,
                                               self.properties.intensityTxt.value,
                                               parent=self)
        self.intensityTxt.setToolTip("Set the light's intensity value.\n"
                                     "Affects selected, or the only directional light in the scene.\n"
                                     "Generic intensity values may not match depending on the renderer")
        toolTip = "Darken the directional light's intensity\n" \
                  "(Shift faster, ctrl slower, alt reset)\n" \
                  "Generic intensity values may not match depending on the renderer."
        self.intensityDarkenBtn = elements.styledButton("", "darkenBulb",
                                                        self,
                                                        toolTip,
                                                        style=uic.BTN_TRANSPARENT_BG,
                                                        minWidth=uic.BTN_W_ICN_REG)
        toolTip = "Brighten the directional light's intensity\n" \
                  "(Shift faster, ctrl slower, alt reset).\n" \
                  "Generic intensity values may not match depending on the renderer."
        self.intensityBrightenBtn = elements.styledButton("", "brightenBulb",
                                                          self, toolTip,
                                                          style=uic.BTN_TRANSPARENT_BG,
                                                          minWidth=uic.BTN_W_ICN_REG)
        toolTip = "Set the intensity of the selected, or the only directional light in the scene/s\n" \
                  "Affects selected, or the only directional light in the scene.\n" \
                  "Generic intensity values may not match depending on the renderer."
        self.intensityPushBtn = elements.styledButton("", "arrowRight",
                                                      self,
                                                      toolTip,
                                                      style=uic.BTN_TRANSPARENT_BG,
                                                      minWidth=uic.BTN_W_ICN_REG)
        self.pushPullBtns.append(self.intensityPushBtn)
        toolTip = "Get the intensity of the selected, or the only directional light in the scene.\n" \
                  "Generic intensity values may not match depending on the renderer."
        self.intensityPullBtn = elements.styledButton("", "arrowLeft",
                                                      self,
                                                      toolTip,
                                                      style=uic.BTN_TRANSPARENT_BG,
                                                      minWidth=uic.BTN_W_ICN_REG)
        self.pushPullBtns.append(self.intensityPullBtn)
        # Directional Softness Angle --------------------------------------
        self.softnessTxt = elements.FloatEdit(self.properties.softAngle.label,
                                              self.properties.softAngle.value,
                                              parent=self)
        self.toolsetWidget.linkProperty(self.softnessTxt, "softAngle")

        self.softnessTxt.setToolTip("The blur (soft angle) of the directional light's shadow\n"
                                    "Affects selected, or the only directional light in the scene")
        toolTip = "Sharpen the directional light's shadow\n" \
                  "(Shift faster, ctrl slower, alt reset)"
        self.softnessNegBtn = elements.styledButton("", "scaleDown",
                                                    self,
                                                    toolTip,
                                                    style=uic.BTN_TRANSPARENT_BG,
                                                    minWidth=uic.BTN_W_ICN_REG)
        toolTip = "Blur the directional light's shadow\n" \
                  "(Shift faster, ctrl slower, alt reset)"
        self.softnessPosBtn = elements.styledButton("", "scaleUp",
                                                    self,
                                                    toolTip,
                                                    style=uic.BTN_TRANSPARENT_BG,
                                                    minWidth=uic.BTN_W_ICN_REG)
        toolTip = "Set the angle softness of directional light/s\n" \
                  "Affects selected, or the only directional light in the scene"
        self.softnessPushBtn = elements.styledButton("", "arrowRight",
                                                     self,
                                                     toolTip,
                                                     style=uic.BTN_TRANSPARENT_BG,
                                                     minWidth=uic.BTN_W_ICN_REG)
        self.pushPullBtns.append(self.softnessPushBtn)
        toolTip = "Get the angle softness of the selected, or only directional light in the scene"
        self.softnessPullBtn = elements.styledButton("", "arrowLeft",
                                                     self,
                                                     toolTip,
                                                     style=uic.BTN_TRANSPARENT_BG,
                                                     minWidth=uic.BTN_W_ICN_REG)
        self.pushPullBtns.append(self.softnessPullBtn)
        # Directional Color --------------------------------------
        toolTip = "The color of the directional light\n Affects selected, or the only directional light in the scene"
        self.colorBtn = cmdswidgets.MayaColorBtn(text=self.properties.color.label,
                                                 color=self.properties.color.value,
                                                 parent=self,
                                                 toolTip=toolTip)

        self.toolsetWidget.linkProperty(self.colorBtn, "color")

        toolTip = "Hue: Decrease value (Shift faster, ctrl slower, alt reset)"
        self.colHueNegBtn = elements.styledButton("", "previousSml",
                                                  self,
                                                  toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=uic.BTN_W_ICN_SML)
        toolTip = "Hue: Increase value (Shift faster, ctrl slower, alt reset)"
        self.colHuePosBtn = elements.styledButton("", "nextSml",
                                                  self,
                                                  toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=uic.BTN_W_ICN_SML)
        toolTip = "Saturation: Decrease value (Shift faster, ctrl slower, alt reset)"
        self.colSatBtnNeg = elements.styledButton("", "previousSml",
                                                  self,
                                                  toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=uic.BTN_W_ICN_SML)
        toolTip = "Saturation: Increase value (Shift faster, ctrl slower, alt reset)"
        self.colSatPosBtn = elements.styledButton("", "nextSml",
                                                  self,
                                                  toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=uic.BTN_W_ICN_SML)
        toolTip = "Set the color\n" \
                  "Affects selected, or the only directional light in the scene/s"
        self.colorPushBtn = elements.styledButton("", "arrowRight",
                                                  self,
                                                  toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=uic.BTN_W_ICN_REG)
        self.pushPullBtns.append(self.colorPushBtn)
        toolTip = "Get the color\n" \
                  "From selected, or the only directional light in the scene"
        self.colorPullBtn = elements.styledButton("", "arrowLeft",
                                                  self,
                                                  toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=uic.BTN_W_ICN_REG)
        self.pushPullBtns.append(self.colorPullBtn)
        # Create Buttons --------------------------------------
        toolTip = "Create a new directional light from settings above"
        self.createLightBtn = elements.styledButton("Create", "lightarrows",
                                                    self,
                                                    toolTip,
                                                    style=uic.BTN_DEFAULT)
        toolTip = "Place Reflection by www.braverabbit.com (Ingo Clemens).\n" \
                  "(Third Party Community Tools must be installed).\n" \
                  "With a light selected, click-drag on a surface to place the light's highlight \n" \
                  "Hold Ctrl or Shift, click-drag to vary the distance of the light from the surface \n" \
                  "Open source repository: https://github.com/IngoClemens/placeReflection"
        self.placeReflectionBtn = elements.styledButton("Place", "placeReflection",
                                                        self,
                                                        toolTip,
                                                        style=uic.BTN_DEFAULT,
                                                        minWidth=uic.BTN_W_ICN_REG)
        toolTip = "Create a new light at the camera position"
        self.camDropBtn = elements.styledButton("", "dropCamera",
                                                self,
                                                toolTip,
                                                style=uic.BTN_DEFAULT,
                                                minWidth=uic.BTN_W_ICN_REG)
        # Renderer Button --------------------------------------
        toolTip = "Set the default renderer"
        self.rendererLoaded = elements.iconMenuButtonCombo(DFLT_RNDR_MODES,
                                                           self.properties.renderer.value,
                                                           toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.rendererLoaded, "renderer")
        # Push/Pull Bottom Buttons --------------------------------------
        toolTip = "Get all settings from directional light\n" \
                  "From the selected, or the only directional light in the scene\n" \
                  "Names are not affected"
        self.allPullBtn = elements.styledButton("Pull Selected", "arrowLeft",
                                                self,
                                                toolTip,
                                                style=uic.BTN_DEFAULT,
                                                minWidth=uic.BTN_W_ICN_REG)
        toolTip = "Set all settings for directional light/s\n" \
                  "Affects selected, or the only directional light in the scene/s\n" \
                  "Names are not affected"
        self.allPushBtn = elements.styledButton("Apply All", "arrowRight",
                                                self,
                                                toolTip,
                                                style=uic.BTN_DEFAULT,
                                                minWidth=uic.BTN_W_ICN_REG)
        # hide push main buttons
        self.allPushBtn.hide()
        self.allPullBtn.hide()
        # ----------------------------------------------------------------------
        # ADVANCED UI WIDGETS
        # ----------------------------------------------------------------------
        if self.uiMode == UI_MODE_ADVANCED:
            # Directional Rot X --------------------------------------
            self.rotXTxt = elements.FloatEdit(self.properties.rotX.label,
                                              self.properties.rotX.value,
                                              rounding=2,
                                              parent=self)
            self.toolsetWidget.linkProperty(self.rotXTxt, "rotX")

            self.rotXTxt.setToolTip("The rotation X (up/down) of the directional light\n"
                                    "Affects selected, or the only directional light in the scene")
            toolTip = "Lower the directional light\n" \
                      "(Shift faster, ctrl slower, alt reset)"
            self.rotXOffsetBtnNeg = elements.styledButton("", "arrowRotUp",
                                                          self,
                                                          toolTip,
                                                          style=uic.BTN_TRANSPARENT_BG,
                                                          minWidth=uic.BTN_W_ICN_REG)
            toolTip = "Raise the directional light\n" \
                      "(Shift faster, ctrl slower, alt reset)"
            self.rotXOffsetBtnPos = elements.styledButton("", "arrowRotDown",
                                                          self,
                                                          toolTip,
                                                          style=uic.BTN_TRANSPARENT_BG,
                                                          minWidth=uic.BTN_W_ICN_REG)
            toolTip = "Set the rotation X value of the directional light\n" \
                      "Affects selected, or the only directional light in the scene"
            self.rotXPushBtn = elements.styledButton("", "arrowRight", self,
                                                     toolTip,
                                                     style=uic.BTN_TRANSPARENT_BG,
                                                     minWidth=uic.BTN_W_ICN_REG)
            self.pushPullBtns.append(self.rotXPushBtn)
            toolTip = "Get the rotation X value of the directional light\n" \
                      "From the selected, or the only directional light"
            self.rotXPullBtn = elements.styledButton("", "arrowLeft",
                                                     self,
                                                     toolTip,
                                                     style=uic.BTN_TRANSPARENT_BG,
                                                     minWidth=uic.BTN_W_ICN_REG)
            self.pushPullBtns.append(self.rotXPullBtn)
            # Directional Rot Y --------------------------------------
            self.rotYTxt = elements.FloatEdit(self.properties.rotY.label,
                                              self.properties.rotY.value,
                                              rounding=2,
                                              parent=self)
            self.toolsetWidget.linkProperty(self.rotYTxt, "rotY")

            self.rotYTxt.setToolTip("The rotation Y (left/right) of the directional light\n"
                                    "Affects selected, or the only directional light in the scene")
            toolTip = "Spin the directional light\n" \
                      "(Shift faster, ctrl slower, alt reset)"
            self.rotYOffsetNegBtn = elements.styledButton("", "arrowRotLeft",
                                                          self,
                                                          toolTip,
                                                          style=uic.BTN_TRANSPARENT_BG,
                                                          minWidth=uic.BTN_W_ICN_REG)
            toolTip = "Spin the directional light\n" \
                      "(Shift faster, ctrl slower, alt reset)"
            self.rotYOffsetPosBtn = elements.styledButton("", "arrowRotRight",
                                                          self,
                                                          toolTip,
                                                          style=uic.BTN_TRANSPARENT_BG,
                                                          minWidth=uic.BTN_W_ICN_REG)
            toolTip = "Set the rotation Y value of the directional light\n" \
                      "Affects selected, or the only directional light in the scene"
            self.rotYPushBtn = elements.styledButton("", "arrowRight",
                                                     self, toolTip,
                                                     style=uic.BTN_TRANSPARENT_BG,
                                                     minWidth=uic.BTN_W_ICN_REG)
            self.pushPullBtns.append(self.rotYPushBtn)
            toolTip = "Get the rotation Y value of the directional light\n" \
                      "From the selected, or the only directional light"
            self.rotYPullBtn = elements.styledButton("", "arrowLeft",
                                                     self,
                                                     toolTip,
                                                     style=uic.BTN_TRANSPARENT_BG,
                                                     minWidth=uic.BTN_W_ICN_REG)
            self.pushPullBtns.append(self.rotYPullBtn)
            # Directional Rot Z --------------------------------------
            self.rotZTxt = elements.FloatEdit(self.properties.rotZ.label,
                                              self.properties.rotZ.value,
                                              rounding=2,
                                              parent=self)
            self.toolsetWidget.linkProperty(self.rotZTxt, "rotZ")
            self.rotZTxt.setToolTip("The rotation Z (roll) of the directional light\n"
                                    "Affects selected, or the only directional light in the scene")
            toolTip = "Roll the directional light\n" \
                      "(Shift faster, ctrl slower, alt reset)"
            self.rotZOffsetNegBtn = elements.styledButton("", "arrowRollLeft",
                                                          self,
                                                          toolTip,
                                                          style=uic.BTN_TRANSPARENT_BG,
                                                          minWidth=uic.BTN_W_ICN_REG)
            self.rotZOffsetPosBtn = elements.styledButton("", "arrowRollRight",
                                                          self,
                                                          toolTip,
                                                          style=uic.BTN_TRANSPARENT_BG,
                                                          minWidth=uic.BTN_W_ICN_REG)
            toolTip = "Set the rotation Z value of the directional light/s\n" \
                      "Affects selected, or the only directional light in the scene"
            self.rotZPushBtn = elements.styledButton("", "arrowRight",
                                                     self,
                                                     toolTip,
                                                     style=uic.BTN_TRANSPARENT_BG,
                                                     minWidth=uic.BTN_W_ICN_REG)
            self.pushPullBtns.append(self.rotZPushBtn)
            toolTip = "Get the rotation Z value of the directional light\n" \
                      "From the selected, or the only directional light"
            self.rotZPullBtn = elements.styledButton("", "arrowLeft",
                                                     self,
                                                     toolTip,
                                                     style=uic.BTN_TRANSPARENT_BG,
                                                     minWidth=uic.BTN_W_ICN_REG)
            self.pushPullBtns.append(self.rotZPullBtn)
            # Directional Temperature --------------------------------------
            self.temperatureTxt = elements.FloatEdit(self.properties.temperature.label,
                                                     self.properties.temperature.value,
                                                     parent=self,
                                                     rounding=2,
                                                     editRatio=20,
                                                     labelRatio=25)
            self.toolsetWidget.linkProperty(self.temperatureTxt, "temperature")

            self.temperatureTxt.setToolTip("The color temperature in degrees kelvin for directional light/s")
            toolTip = "Color temperature on/off\n" \
                      "Off: Color (Hue/Sat) will be used\n" \
                      "On: Temperature will be used"
            self.tempOnOffBx = elements.CheckBox(self.properties.tempBool.label,
                                                 checked=self.properties.tempBool.value,
                                                 parent=self,
                                                 toolTip=toolTip)
            self.toolsetWidget.linkProperty(self.tempOnOffBx, "tempBool")

            toolTip = "Warm the color temperature in degrees kelvin\n" \
                      "(Shift faster, ctrl slower, alt reset)"
            self.tempOffsetNegBtn = elements.styledButton("", "hot",
                                                          self,
                                                          toolTip,
                                                          style=uic.BTN_TRANSPARENT_BG,
                                                          minWidth=uic.BTN_W_ICN_REG)
            toolTip = "Cool the color temperature in degrees kelvin\n" \
                      "(Shift faster, ctrl slower, alt reset)"
            self.tempOffsetPosBtn = elements.styledButton("", "cold",
                                                          self,
                                                          toolTip,
                                                          style=uic.BTN_TRANSPARENT_BG,
                                                          minWidth=uic.BTN_W_ICN_REG)
            toolTip = "Set the color in temperature (degrees kelvin) for directional light/s\n" \
                      "Affects selected, or the only directional light in the scene"
            self.tempPushBtn = elements.styledButton("", "arrowRight",
                                                     self,
                                                     toolTip,
                                                     style=uic.BTN_TRANSPARENT_BG,
                                                     minWidth=uic.BTN_W_ICN_REG)
            self.pushPullBtns.append(self.tempPushBtn)
            toolTip = "Get the color in temperature (degrees kelvin) directional light\n" \
                      "From the selected, or the only directional light in the scene"
            self.tempPullBtn = elements.styledButton("", "arrowLeft",
                                                     self,
                                                     toolTip,
                                                     style=uic.BTN_TRANSPARENT_BG,
                                                     minWidth=uic.BTN_W_ICN_REG)
            self.pushPullBtns.append(self.tempPullBtn)
            # Instant Apply  --------------------------------------
            toolTip = "Always apply changes instantly\n" \
                      "With instant apply off, changes will only be applied while\n" \
                      "pressing the apply/set buttons"
            self.instantApplyCheckbox = elements.CheckBox(self.properties.instantApply.label,
                                                          parent=self,
                                                          toolTip=toolTip,
                                                          checked=self.properties.instantApply.value)
            self.toolsetWidget.linkProperty(self.instantApplyCheckbox, "instantApply")
            # Hide instant apply checkbox, no longer needed
            self.instantApplyCheckbox.hide()


class CompactLayout(AllWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None):
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
        super(CompactLayout, self).__init__(parent=parent, properties=properties,
                                            uiMode=uiMode, toolsetWidget=toolsetWidget)
        # Create Main Layout -------------------------------
        self.contentsLayoutSimple = elements.vBoxLayout(self,
                                                        margins=(uic.WINSIDEPAD, uic.WINBOTPAD,
                                                                 uic.WINSIDEPAD, uic.WINBOTPAD),
                                                        spacing=0)
        # Create Grid Layout -------------------------------
        dirGridLayout = elements.GridLayout(columnMinWidth=(0, 180))
        # Directional Name Layout -------------------------------
        suffixPadLayout = elements.hBoxLayout(margins=(12, 0, 0, 0), spacing=0)
        suffixPadLayout.addWidget(self.suffixCheckbox)
        nameButtonsLayout = elements.hBoxLayout()
        nameButtonsLayout.addWidget(self.namePullBtn)
        nameButtonsLayout.addWidget(self.renameBtn)
        # Directional Intensity Layout -------------------------------
        intensityBtnLayout = elements.hBoxLayout()
        intensityBtnLayout.addWidget(self.intensityDarkenBtn, 1)
        intensityBtnLayout.addWidget(self.intensityBrightenBtn, 1)
        intensityButtonsLayout = elements.hBoxLayout()
        intensityButtonsLayout.addWidget(self.intensityPullBtn)
        intensityButtonsLayout.addWidget(self.intensityPushBtn)
        # Directional Softness Angle Layout -------------------------------
        softnessOffsetBtnLayout = elements.hBoxLayout()
        softnessOffsetBtnLayout.addWidget(self.softnessNegBtn)
        softnessOffsetBtnLayout.addWidget(self.softnessPosBtn)
        softnessButtonsLayout = elements.hBoxLayout()
        softnessButtonsLayout.addWidget(self.softnessPullBtn)
        softnessButtonsLayout.addWidget(self.softnessPushBtn)
        colOffsetBtnLayout = elements.hBoxLayout()
        # Directional Color Layout -------------------------------
        colOffsetBtnLayout.addWidget(self.colHueNegBtn)
        colOffsetBtnLayout.addWidget(self.colHuePosBtn)
        colOffsetBtnLayout.addWidget(self.colSatBtnNeg)
        colOffsetBtnLayout.addWidget(self.colSatPosBtn)
        colorButtonsLayout = elements.hBoxLayout()
        colorButtonsLayout.addWidget(self.colorPullBtn)
        colorButtonsLayout.addWidget(self.colorPushBtn)
        # Apply the content to the grid layout -------------------------------
        dirGridLayout.addWidget(self.nameTxt, 0, 0)
        dirGridLayout.addLayout(suffixPadLayout, 0, 1)
        dirGridLayout.addLayout(nameButtonsLayout, 0, 2)

        dirGridLayout.addWidget(self.intensityTxt, 1, 0)
        dirGridLayout.addLayout(intensityBtnLayout, 1, 1)
        dirGridLayout.addLayout(intensityButtonsLayout, 1, 2)

        dirGridLayout.addWidget(self.softnessTxt, 2, 0)
        dirGridLayout.addLayout(softnessOffsetBtnLayout, 2, 1)
        dirGridLayout.addLayout(softnessButtonsLayout, 2, 2)

        dirGridLayout.addWidget(self.colorBtn, 6, 0)
        dirGridLayout.addLayout(colOffsetBtnLayout, 6, 1)
        dirGridLayout.addLayout(colorButtonsLayout, 6, 2)
        # Create Buttons Layout -------------------------------
        # main bottom buttons, adjust text and size
        self.placeReflectionBtn.setText("")
        self.allPullBtn.setText("")
        self.allPushBtn.setText("")

        createButtonsLayout = elements.hBoxLayout(margins=(0, uic.REGPAD, 0, 0), spacing=uic.SSML)

        createButtonsLayout.addWidget(self.createLightBtn, 6)
        createButtonsLayout.addWidget(self.camDropBtn, 1)
        createButtonsLayout.addWidget(self.placeReflectionBtn, 1)
        createButtonsLayout.addWidget(self.rendererLoaded, 1)
        createButtonsLayout.addWidget(self.allPullBtn, 1)
        createButtonsLayout.addWidget(self.allPushBtn, 1)

        self.contentsLayoutSimple.addLayout(dirGridLayout)
        self.contentsLayoutSimple.addLayout(createButtonsLayout)
        self.contentsLayoutSimple.addStretch(1)


class AdvancedLayout(AllWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_ADVANCED, toolsetWidget=None):
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
        super(AdvancedLayout, self).__init__(parent=parent, properties=properties,
                                             uiMode=uiMode, toolsetWidget=toolsetWidget)
        # create main layout ---------------------------
        self.contentsLayoutAdv = elements.vBoxLayout(self,
                                                     margins=(uic.WINSIDEPAD, uic.WINBOTPAD,
                                                              uic.WINSIDEPAD, uic.WINBOTPAD),
                                                     spacing=0)
        # create main grid layout ---------------------------
        dirGridLayout = elements.GridLayout(columnMinWidth=(0, 180))
        # Name ---------------------------
        suffixPadLayout = elements.hBoxLayout(margins=(12, 0, 0, 0), spacing=0)
        suffixPadLayout.addWidget(self.suffixCheckbox)

        nameButtonsLayout = elements.hBoxLayout()
        nameButtonsLayout.addWidget(self.namePullBtn)
        nameButtonsLayout.addWidget(self.renameBtn)
        # Directional Intensity ---------------------------
        intensityBtnLayout = elements.hBoxLayout()
        intensityBtnLayout.addWidget(self.intensityDarkenBtn, 1)
        intensityBtnLayout.addWidget(self.intensityBrightenBtn, 1)
        intensityButtonsLayout = elements.hBoxLayout()
        intensityButtonsLayout.addWidget(self.intensityPullBtn)
        intensityButtonsLayout.addWidget(self.intensityPushBtn)
        # Directional Softness Angle ---------------------------
        softnessOffsetBtnLayout = elements.hBoxLayout()
        softnessOffsetBtnLayout.addWidget(self.softnessNegBtn)
        softnessOffsetBtnLayout.addWidget(self.softnessPosBtn)
        softnessButtonsLayout = elements.hBoxLayout()
        softnessButtonsLayout.addWidget(self.softnessPullBtn)
        softnessButtonsLayout.addWidget(self.softnessPushBtn)
        # Directional Rot X ---------------------------
        rotXOffsetBtnLayout = elements.hBoxLayout()
        rotXOffsetBtnLayout.addWidget(self.rotXOffsetBtnNeg)
        rotXOffsetBtnLayout.addWidget(self.rotXOffsetBtnPos)
        rotXButtonsLayout = elements.hBoxLayout()
        rotXButtonsLayout.addWidget(self.rotXPullBtn)
        rotXButtonsLayout.addWidget(self.rotXPushBtn)
        # Directional Rot Y ---------------------------
        rotYOffsetBtnLayout = elements.hBoxLayout()
        rotYOffsetBtnLayout.addWidget(self.rotYOffsetNegBtn)
        rotYOffsetBtnLayout.addWidget(self.rotYOffsetPosBtn)
        rotYButtonsLayout = elements.hBoxLayout()
        rotYButtonsLayout.addWidget(self.rotYPullBtn)
        rotYButtonsLayout.addWidget(self.rotYPushBtn)
        # Directional Rot Z ---------------------------
        rotZOffsetBtnLayout = elements.hBoxLayout()
        rotZOffsetBtnLayout.addWidget(self.rotZOffsetNegBtn)
        rotZOffsetBtnLayout.addWidget(self.rotZOffsetPosBtn)
        rotZButtonsLayout = elements.hBoxLayout()
        rotZButtonsLayout.addWidget(self.rotZPullBtn)
        rotZButtonsLayout.addWidget(self.rotZPushBtn)
        colOffsetBtnLayout = elements.hBoxLayout()
        # Directional Color ---------------------------
        colOffsetBtnLayout.addWidget(self.colHueNegBtn)
        colOffsetBtnLayout.addWidget(self.colHuePosBtn)
        colOffsetBtnLayout.addWidget(self.colSatBtnNeg)
        colOffsetBtnLayout.addWidget(self.colSatPosBtn)
        colorButtonsLayout = elements.hBoxLayout()
        colorButtonsLayout.addWidget(self.colorPullBtn)
        colorButtonsLayout.addWidget(self.colorPushBtn)
        # Directional Temperature ---------------------------
        tempColOnOffLayout = elements.hBoxLayout()
        tempColOnOffLayout.addWidget(self.temperatureTxt)
        tempColOnOffLayout.addWidget(self.tempOnOffBx)
        tempOffsetBtnLayout = elements.hBoxLayout()
        tempOffsetBtnLayout.addWidget(self.tempOffsetNegBtn)
        tempOffsetBtnLayout.addWidget(self.tempOffsetPosBtn)
        tempButtonsLayout = elements.hBoxLayout()
        tempButtonsLayout.addWidget(self.tempPullBtn)
        tempButtonsLayout.addWidget(self.tempPushBtn)
        # Apply the content to the grid layout ---------------------------
        dirGridLayout.addWidget(self.nameTxt, 0, 0)
        dirGridLayout.addLayout(suffixPadLayout, 0, 1)
        dirGridLayout.addLayout(nameButtonsLayout, 0, 2)

        dirGridLayout.addWidget(self.intensityTxt, 1, 0)
        dirGridLayout.addLayout(intensityBtnLayout, 1, 1)
        dirGridLayout.addLayout(intensityButtonsLayout, 1, 2)

        dirGridLayout.addWidget(self.softnessTxt, 2, 0)
        dirGridLayout.addLayout(softnessOffsetBtnLayout, 2, 1)
        dirGridLayout.addLayout(softnessButtonsLayout, 2, 2)

        dirGridLayout.addWidget(self.rotXTxt, 3, 0)
        dirGridLayout.addLayout(rotXOffsetBtnLayout, 3, 1)
        dirGridLayout.addLayout(rotXButtonsLayout, 3, 2)

        dirGridLayout.addWidget(self.rotYTxt, 4, 0)
        dirGridLayout.addLayout(rotYOffsetBtnLayout, 4, 1)
        dirGridLayout.addLayout(rotYButtonsLayout, 4, 2)

        dirGridLayout.addWidget(self.rotZTxt, 5, 0)
        dirGridLayout.addLayout(rotZOffsetBtnLayout, 5, 1)
        dirGridLayout.addLayout(rotZButtonsLayout, 5, 2)

        dirGridLayout.addWidget(self.colorBtn, 6, 0)
        dirGridLayout.addLayout(colOffsetBtnLayout, 6, 1)
        dirGridLayout.addLayout(colorButtonsLayout, 6, 2)

        dirGridLayout.addLayout(tempColOnOffLayout, 7, 0)
        dirGridLayout.addLayout(tempOffsetBtnLayout, 7, 1)
        dirGridLayout.addLayout(tempButtonsLayout, 7, 2)
        # Create Bottom Buttons ---------------------------
        createButtonsLayout = elements.hBoxLayout(margins=(0, uic.REGPAD, 0, 0))
        # Renderer Button ---------------------------
        rendererSmlLayout = elements.hBoxLayout()
        rendererSmlLayout.addWidget(self.camDropBtn)
        rendererSmlLayout.addWidget(self.rendererLoaded)
        createButtonsLayout.addWidget(self.createLightBtn, 12)
        createButtonsLayout.addWidget(self.placeReflectionBtn, 12)
        createButtonsLayout.addLayout(rendererSmlLayout, 9)
        # Push/Pull Instant Buttons (hidden, and not used) ---------------------------
        pushPullLayout = elements.hBoxLayout(margins=(0, 0, 0, 0))
        instantSmlLayout = elements.hBoxLayout()
        instantSpacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        instantSmlLayout.addItem(instantSpacer)
        instantSmlLayout.addWidget(self.instantApplyCheckbox)
        pushPullLayout.addWidget(self.allPullBtn, 12)
        pushPullLayout.addWidget(self.allPushBtn, 12)
        pushPullLayout.addLayout(instantSmlLayout, 9)
        # Main Layouts ---------------------------
        self.contentsLayoutAdv.addLayout(dirGridLayout)
        self.contentsLayoutAdv.addLayout(createButtonsLayout)
        self.contentsLayoutAdv.addLayout(pushPullLayout)

        self.contentsLayoutAdv.addStretch(1)
