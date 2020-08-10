import locale
from functools import partial, wraps

import maya.api.OpenMaya as om2
from maya import cmds

from Qt import QtWidgets, QtCore

from zoo.apps.toolsetsui import toolsetcallbacks
from zoo.apps.toolsetsui import toolsetui
from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya

from zoo.preferences.core import preference
from zoo.apps.light_suite import lightconstants as lc
from zoo.preferences import preferencesconstants as pc

from zoo.libs.maya.cmds.general import undodecorator
from zoo.libs.maya.cmds.lighting import renderertransferlights, lightingutils
from zoo.libs.maya.cmds.lighting.renderertransferlights import INTENSITY, EXPOSURE, LIGHTCOLOR, TEMPERATURE, TEMPONOFF, \
    NORMALIZE, SHAPE, LIGHTVISIBILITY, SCALE
from zoo.libs.maya.cmds.lighting.renderertransferlights import getLightDictAttributes
from zoo.libs.maya.cmds.objutils import namehandling
from zoo.libs.maya.cmds.renderer import rendererload
from zoo.libs.maya.cmds.renderer.rendererconstants import RENDERER_SUFFIX

from zoo.libs.maya.qt import cmdswidgets
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import colour
from zoo.libs.utils import zlogging

logger = zlogging.getLogger(__name__)

# Widget Defaults
DFLT_RNDR_MODES = [("arnold", "Arnold"), ("redshift", "Redshift"), ("renderman", "Renderman")]
SHAPE_LIST_NICE = lightingutils.SHAPE_ATTR_ENUM_LIST_NICE
CREATE_OPTIONS_LIST = ["World Center", "Selected"]
AREA_INTENSITY_OFFSET = 10

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


def ignoreInstantApplyDecorator(method):
    """ Decorator to temporarily ignore instant apply in a GUI.

    @undoDecorator
    def lightUIMethod():
        pass
    """

    @wraps(method)
    def _disableMethod(self, *args, **kwargs):
        try:
            rememberInstantApply = self.ignoreInstantApply
            self.ignoreInstantApply = True  # bool that tells other stuff to activate
            return method(self, *args, **kwargs)  # run the method
        finally:
            self.ignoreInstantApply = rememberInstantApply

    return _disableMethod


class AreaLights(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "areaLights"
    uiData = {"label": "Area Lights",
              "icon": "lightarea",
              "tooltip": "Create & Manage Area Lights",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-area-lights/"
              }

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run"""
        self.toolsetWidget = self  # needed for callback decorators
        # Light Suite Pref Object PREFS_DATA stores and saves all the .prefs json data
        self.lightSuitePrefsData = preference.findSetting(lc.RELATIVE_PREFS_FILE, None)  # light suite preferences
        self.generalSettingsPrefsData = preference.findSetting(pc.RELATIVE_PREFS_FILE, None)  # renderer in general pref
        self.properties.rendererIconMenu.value = self.generalSettingsPrefsData[pc.PREFS_KEY_RENDERER]

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget(), self.initAdvancedWidget()]

    def initCompactWidget(self):
        self.compactWidget = CompactLayout(parent=self, properties=self.properties, toolsetWidget=self)
        return self.compactWidget

    def initAdvancedWidget(self):
        self.advancedWidget = AdvancedLayout(parent=self, properties=self.properties, toolsetWidget=self)
        return self.advancedWidget

    def postContentSetup(self):
        """Last of the initizialize code"""

        self.ignoreInstantApply = False  # for instant apply area lights and switching ui modes
        self.uiConnections()
        self.disableEnableTemperatureWidgets()  # auto sets the disable/enable state of the temperature lineEdit
        self.refreshUpdateUIFromSelection(update=False)  # update GUI from current in scene selection
        self.instantApplyOnOff()  # show hide btns depending on the state
        self.startSelectionCallback()  # start selection callback

    def defaultAction(self):
        # double click top icon
        pass

    # ------------------------------------
    # PROPERTIES
    # ------------------------------------

    def initializeProperties(self):
        return [{"name": "rendererIconMenu", "label": "", "value": "Arnold"},
                {"name": "name", "label": "Light Name", "value": "area",
                 "longName": "|ArnoldLights_grp|area_ARN"},
                {"name": "suffix", "label": "Add Suffix", "value": True},
                {"name": "intensity", "label": "Intensity", "value": 1.0},
                {"name": "exposure", "label": "Exposure", "value": 16.0},
                {"name": "shape", "label": "Shape", "value": 0},
                {"name": "normalize", "label": "Normalize", "value": True},
                {"name": "visibility", "label": "Visibility", "value": False},
                {"name": "color", "label": "Color (Hue/Sat)", "value": (1.0, 1.0, 1.0)},
                {"name": "temperature", "label": "Temperature", "value": 6500},
                {"name": "tempBool", "label": "", "value": False},
                {"name": "scale", "label": "Scale", "value": (50.0, 50.0, 50.0)},
                {"name": "createFrom", "label": "Create From", "value": 0},
                {"name": "instantApply", "label": "Instant Apply", "value": True}]

    def saveProperties(self):
        """ Runs save properties from the base class.

        Widgets will auto save to self.properties if linked via:

            self.linkProperty(widget, "propertyKey")
            or
            self.toolsetWidget.linkProperty(widget, "propertyKey")

        Add code after super(), useful for changes such as type conversions
        or manually adding unsupported widgets
        """
        if self.ignoreInstantApply:  # skip if setting properties while switching, no need to save
            return
        super(AreaLights, self).saveProperties()

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
        super(AreaLights, self).updateFromProperties()
        # disable callbacks and updates
        rememberInstantApply = self.ignoreInstantApply
        self.blockCallbacks(True)
        self.ignoreInstantApply = True
        # compact intensity and exposure, limit to exposure only
        if self.displayIndex() == UI_MODE_COMPACT:
            intensity, exposure = lightingutils.convertExpAndIntToExposure(self.properties.intensity.value,
                                                                           self.properties.exposure.value)
            self.compactWidget.exposureTxt.setValue(exposure)
            self.properties.intensity.value = intensity
            self.properties.exposure.value = exposure
        else:
            # advanced limit the decimal places and use properties
            self.advancedWidget.exposureTxt.setValue(self.properties.exposure.value)
            self.advancedWidget.intensityTxt.setValue(self.properties.intensity.value)
        # limit decimal places on the scale values
        scale = list()
        for i, axis in enumerate(self.properties.scale.value):
            scale.append(float("{0:.3f}".format(round(axis, 3))))
        self.advancedWidget.scaleVEdit.setValue(scale)
        # re-enable callbacks and updates
        self.disableEnableTemperatureWidgets()
        self.ignoreInstantApply = rememberInstantApply
        self.blockCallbacks(False)

    # ------------------
    # RIGHT CLICK TOOLSET ICON
    # ------------------

    def actions(self):
        """Right click menu on the main toolset tool icon"""
        return [{"type": "action",
                 "name": "create1",
                 "label": "Create Area Light 1cm",
                 "icon": "lightarea",
                 "tooltip": ""},
                {"type": "action",
                 "name": "create10",
                 "label": "Create Area Light 10cm",
                 "icon": "lightarea",
                 "tooltip": ""},
                {"type": "action",
                 "name": "create50",
                 "label": "Create Area Light 50cm",
                 "icon": "lightarea",
                 "tooltip": ""},
                {"type": "action",
                 "name": "create200",
                 "label": "Create Area Light 2m",
                 "icon": "lightarea",
                 "tooltip": ""}]

    def executeActions(self, action):
        name = action["name"]
        if name == "create1":
            newLight = self.createAreaLight()
            cmds.setAttr("{}.scale".format(newLight), 1.0, 1.0, 1.0, type="double3")
        elif name == "create10":
            newLight = self.createAreaLight()
            cmds.setAttr("{}.scale".format(newLight), 10.0, 10.0, 10.0, type="double3")
        elif name == "create50":
            newLight = self.createAreaLight()
            cmds.setAttr("{}.scale".format(newLight), 50.0, 50.0, 50.0, type="double3")
        elif name == "create200":
            newLight = self.createAreaLight()
            cmds.setAttr("{}.scale".format(newLight), 200.0, 200.0, 200.0, type="double3")

    # ------------------------------------
    # POPUP WINDOWS
    # ------------------------------------

    def ui_loadRenderer(self):
        message = "The {} renderer isn't loaded. Load now?".format(self.properties.rendererIconMenu.value)
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
        logger.debug(">>>>>>>>>>>>>>> SELECTION CHANGED UPDATING 'CREATE AREA LIGHT GUI' <<<<<<<<<<<<<<<<<<<<")
        self.refreshUpdateUIFromSelection()  # will update the GUI

    # ------------------------------------
    # MENUS - RIGHT CLICK
    # ------------------------------------

    @toolsetcallbacks.ignoreCallbackDecorator
    def setLightNameMenuModes(self):
        """Retrieves all area lights in the scene and creates the self.lightNameMenu menu so the user can switch

        Does a bunch of name handling to account for the UI LongName (self.properties.name.longName)
        Auto compares the long name to see if it is the first obj selected

        The current light in the ui is removed from the menu list if selected
        """
        logger.debug("setLightNameMenuModes()")
        modeList = list()
        currentNameUnique = None
        # area light list will be long names
        areaLightListLong = renderertransferlights.getAllAreaLightsInScene(self.properties.rendererIconMenu.value)[0]
        currentUiNameLong = self.properties.name.longName  # already has suffix
        currentNameExits = cmds.objExists(currentUiNameLong)
        if currentNameExits:  # then get the display name
            currentNameUnique = namehandling.getUniqueShortName(currentUiNameLong)
        if areaLightListLong:  # There are other area lights in the scene
            for i, obj in enumerate(areaLightListLong):
                if currentUiNameLong == obj:
                    areaLightListLong.pop(i)  # is the UI name so remove
                    break
        selObj = cmds.ls(selection=True, long=True)
        if not selObj and currentNameExits:
            modeList.append(("cursorSelect", "Select {}".format(currentNameUnique)))  # user can select the light
            modeList.append((None, "separator"))
        elif selObj and currentNameExits:
            objLongName = selObj[0]
            if currentUiNameLong != objLongName:  # current light is not selected
                modeList.append(("cursorSelect", "Select {}".format(currentNameUnique)))  # user can select the light
        if areaLightListLong:
            locale.setlocale(locale.LC_ALL, '')  # needed for sorting unicode
            sorted(areaLightListLong, cmp=locale.strcoll)  # alphabetalize
            for light in areaLightListLong:
                modeList.append(("lightarea", namehandling.getUniqueShortName(light)))
        else:
            modeList.append(("", "No Other Area Lights"))
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

    def showColorMenu(self):
        """Creates the dynamic menu item in the Color Button menu
        """
        modeList = list()
        if self.properties.tempBool.value:
            modeList.append(("checkboxPublish", "Color On (Temperature Off)"))
        modeList.append(("reload", "Reset Color White"))
        self.colorBtnMenu.actionConnectList(modeList)

    def turnOffTemperatureMenu(self):
        """After the color button menu has been clicked, this method runs the logic on the menu clicked:

        - "Color On (Temperature Off)": turns the temperature off
        - "Reset Color White":  turns the temperature off and resets the light to white
        """
        if self.colorBtnMenu.currentText() == "Color On (Temperature Off)":
            self.properties.tempBool.value = False
            self.updateFromProperties()
            self.disableEnableTemperatureWidgets()
            self.areaSetAttributes(temperature=True, lightColor=True)
        if self.colorBtnMenu.currentText() == "Reset Color White":
            self.properties.color.value = self.properties.color.default
            self.properties.tempBool.value = False
            self.updateFromProperties()
            self.disableEnableTemperatureWidgets()
            self.areaSetAttributes(temperature=True, lightColor=True)

    def intExpMenuChanged(self):
        """When the right click menu intensity/exposure is pressed convert the intensity/exposure
        """
        logger.debug("intExpMenuChanged()")
        intensity = self.properties.intensity.value
        exposure = self.properties.exposure.value
        if self.advancedWidget.intExpMenu.currentMenuItem() == self.advancedWidget.intExpMenuModeList[0][1]:
            # convert to pure intensity
            intensity, exposure = lightingutils.convertExpAndIntToIntensity(intensity, exposure)
        elif self.advancedWidget.intExpMenu.currentMenuItem() == self.advancedWidget.intExpMenuModeList[1][1]:
            # convert to pure exposure
            intensity, exposure = lightingutils.convertExpAndIntToExposure(intensity, exposure)
        if intensity > 99999999999.0:  # intensity of extremely large numbers is easily created with exposure convert
            om2.MGlobal.displayWarning("Intensity is too large a number {} for this UI, "
                                       "please lower the exposure".format(intensity))
            return
        self.properties.intensity.value = intensity
        self.properties.exposure.value = exposure
        self.updateFromProperties()
        if self.properties.instantApply.value:
            self.areaSetAttributes(intensity=True, exposure=True, message=False)

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
    # CREATE LIGHTS
    # ------------------------------------

    @undodecorator.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def createAreaLight(self, createFrom=None):
        """ Creates an area light from the GUI settings

        :param createFrom: over ride for creating the light from a position, 0 world center, 1 selected, 2 camera pos
        :type createFrom: int
        """
        newName = self.properties.name.value
        addSuffix = self.properties.suffix.value
        renderer = self.properties.rendererIconMenu.value
        if not self.checkRenderLoaded(renderer):
            return
        logger.debug("createAreaLight()")
        if createFrom is None:
            createFrom = self.properties.createFrom.value
            if self.displayIndex() == UI_MODE_COMPACT:  # compact always create from world center
                createFrom = 0  # world
        if createFrom == 0:
            position = "world"
        elif createFrom == 1:
            position = "selected"
        else:
            position = "camera"
        lightTransform = renderertransferlights.createAreaLightMatchPos("TempNameXXX", renderer, warningState=False,
                                                                        position=position)[0]
        lightTransform, lightShape = renderertransferlights.renameLight(lightTransform, newName,
                                                                        addSuffix=addSuffix)
        lightsTransformList = [lightTransform]
        transformList, shapeList = renderertransferlights.cleanupLights(renderer, lightsTransformList,
                                                                        selectLights=True)  # group, should make if
        newShapeLong = shapeList[0]  # light may have been renamed
        newTransformLong = transformList[0]
        newTransformShort = namehandling.getShortName(newTransformLong)
        self.setLightAllTransform(newShapeLong)
        # update GUI name
        self.properties.name.longName = newTransformLong
        self.properties.name.value = self.returnLightNameNoSuffix(newTransformShort)
        self.updateFromProperties()
        return newTransformLong

    def setLightAllTransform(self, lightShape, noScale=False):
        """Sets all attributes on a light transform node from the GUI using rendererTransferLights.setLightAttr()

        Usually only used while creating lights

        :param lightShape: a single Maya light shape node
        :type lightShape: str
        :param noScale: don't set the scale
        :type noScale: bool
        """
        lightDictAttributes = getLightDictAttributes()  # dict with keys but empty values
        lightDictAttributes[EXPOSURE] = self.properties.exposure.value
        lightDictAttributes[INTENSITY] = self.properties.intensity.value
        lightDictAttributes[LIGHTCOLOR] = self.properties.color.value
        lightDictAttributes[TEMPONOFF] = self.properties.tempBool.value
        lightDictAttributes[TEMPERATURE] = self.properties.temperature.value
        lightDictAttributes[SHAPE] = self.properties.shape.value
        lightDictAttributes[LIGHTVISIBILITY] = self.properties.visibility.value
        lightDictAttributes[NORMALIZE] = self.properties.normalize.value
        if not noScale:
            lightDictAttributes[SCALE] = self.properties.scale.value
        renderertransferlights.setLightAttr(lightShape, lightDictAttributes)

    # ------------------------------------
    # SET (APPLY) LIGHTS
    # ------------------------------------

    def findUIAreaLightSelection(self, prioritizeNameBool=True, message=True):
        """returns the area lights transform/shapes to change based on select and the GUI prioritizeName flag (bool)

        "prioritizeName" takes the long name from the ui and tries to find it as the first item, even if not selected

        :param prioritizeNameBool: takes the name from the ui and tries to find it as the first item, includes selection
        :type prioritizeNameBool: bool
        :param message: report the messages to the user?
        :type message: bool
        """
        prioritizeLongName = ""
        if prioritizeNameBool:
            prioritizeLongName = self.properties.name.longName
        # get the lights taking into consideration the GUI name
        areaLightTransforms, areaLightShapes \
            = renderertransferlights.getSelectedAreaLights(self.properties.rendererIconMenu.value,
                                                           message=message,
                                                           prioritizeName=prioritizeLongName)
        if prioritizeNameBool:  # can have duplicates so remove
            areaLightShapes = list(set(areaLightShapes))
            areaLightTransforms = list(set(areaLightTransforms))
        return areaLightTransforms, areaLightShapes

    def setAreaLightsUI(self, lightDictAttributes, message=True, prioritizeNameBool=True):
        """Sets the area light's attributes dependent on the GUI "prioritizeName" flag and the current selection

        "prioritizeName" takes the long name from the ui and tries to find it as the first item even if not selected

        :param lightDictAttributes: the dictionary of Maya attributes to set
        :type lightDictAttributes: dict
        :param message: report the messages to the user?
        :type message: bool
        :param prioritizeNameBool: takes the name from the ui and tries to find it as the first item, includes selection
        :type prioritizeNameBool: bool
        """
        logger.debug("setAreaLightsUI()")
        areaLightTransforms, areaLightShapes = self.findUIAreaLightSelection(prioritizeNameBool, message)
        if not areaLightTransforms:  # nothing found so bail
            return
        for lightShape in areaLightShapes:  # should be updated to mix behaviour onto other light types ie directionals
            # lightDictAttributes dict is modified so duplicate
            lightDictAttributesCopy = dict(lightDictAttributes)
            renderertransferlights.setLightAttr(lightShape, lightDictAttributesCopy)
        self.ignoreInstantApply = False  # switch instant apply off so can update
        self.updateFromProperties()  # update the GUI

    @undodecorator.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def areaSetAttributes(self, intensity=False, exposure=False, shape=False, normalize=False, lightVis=False,
                          lightColor=False, temperature=False, scale=False, message=True, noScale=False,
                          allAttrs=False, prioritizeNameBool=True):
        """Sets selected lights in the scene with the given attribute states, kwarg as False will be ignored

        Can be overridden to include all attributes with allAttrs
        noScale will stop scale being included even with allAttrs
        "prioritizeName" takes the long name from the GUI and tries to find it as the first item even if not selected

        :param message: report the messages to the user
        :type message: bool
        :param noScale: ignore the scale attribute, overrides scale
        :type noScale: bool
        :param allAttrs: include all attrs as True, noScale is still respected
        :type allAttrs: bool
        :param prioritizeNameBool: takes the name from the ui and tries to find it as the first item, includes selection
        :type prioritizeNameBool: bool
        """
        # self.saveProperties()  # be sure nothing's changed
        logger.debug("areaSetAttributes()")
        lightDictAttributes = renderertransferlights.getLightDictAttributes()  # dict with keys but empty values
        if intensity and not exposure:
            lightDictAttributes[INTENSITY] = self.properties.intensity.value
            lightDictAttributes[EXPOSURE] = self.properties.exposure.value
        if exposure and not intensity:
            lightDictAttributes[EXPOSURE] = self.properties.exposure.value
        if exposure and intensity:
            lightDictAttributes[EXPOSURE] = self.properties.exposure.value
            lightDictAttributes[INTENSITY] = self.properties.intensity.value
        if allAttrs:  # if applying all then combine the intensity and exposure values
            lightDictAttributes[EXPOSURE] = self.properties.exposure.value
            lightDictAttributes[INTENSITY] = self.properties.intensity.value
            intensityVal, exposureVal = \
                lightingutils.convertExpAndIntToExposure(lightDictAttributes[INTENSITY],
                                                         lightDictAttributes[EXPOSURE])
            lightDictAttributes[INTENSITY] = intensityVal
            lightDictAttributes[EXPOSURE] = exposureVal
            self.properties.intensity.value = intensityVal
            self.properties.exposure.value = exposureVal
        if shape or allAttrs:
            lightDictAttributes[SHAPE] = self.properties.shape.value
        if normalize or allAttrs:
            lightDictAttributes[NORMALIZE] = self.properties.normalize.value
        if lightVis or allAttrs:
            lightDictAttributes[LIGHTVISIBILITY] = self.properties.visibility.value
        if temperature or allAttrs:
            temperatureFloat = self.properties.temperature.value
            if temperatureFloat < 0.0:  # clamp so doesn't go below zero
                temperatureFloat = 0.0
                self.properties.temperature.value = 0.0
            lightDictAttributes[TEMPONOFF] = self.properties.tempBool.value
            lightDictAttributes[TEMPERATURE] = temperatureFloat
            if self.properties.tempBool.value:  # temp on so update the color swatch
                kelvinSrgbInt = colour.convertKelvinToRGB(temperatureFloat)
                kelvinSrgbFloat = colour.rgbIntToFloat(kelvinSrgbInt)
                self.properties.color.value = colour.convertColorSrgbToLinear(kelvinSrgbFloat)
        if lightColor or allAttrs or temperature:
            lightDictAttributes[LIGHTCOLOR] = self.properties.color.value  # light color is already linear
            if not temperature and not allAttrs:  # only set this if temp is not being set, ie color is being set
                lightDictAttributes[TEMPONOFF] = 0
                self.properties.tempBool.value = 0
        if scale or allAttrs:
            if not noScale:
                lightDictAttributes[SCALE] = self.properties.scale.value
        # set the attributes and update the GUI
        self.setAreaLightsUI(lightDictAttributes, message=message, prioritizeNameBool=prioritizeNameBool)

    # ------------------------------------
    # INSTANT SET (APPLY) LIGHTS
    # ------------------------------------

    def instantApplyOnOff(self):
        """Stops/starts the selection callback and hides/shows the get/set arrow icons
        """
        self.saveProperties()
        if self.properties.instantApply.value:
            self.startSelectionCallback()
            for widget in self.widgets():
                for btn in widget.pushPullBtns:
                    btn.hide()
        else:
            self.stopSelectionCallback()
            for widget in self.widgets():
                for btn in widget.pushPullBtns:
                    btn.show()

    def instantSetLightAreaName(self):
        """Instant method for renaming lights"""
        if not self.properties.instantApply.value:  # instant apply not checked
            return
        if self.ignoreInstantApply:  # will be set if changing ui modes
            return
        logger.debug("instantSetLightAreaName()")
        self.renameLight()

    def instantSetAreaVisCheckBox(self):
        """Instant method for light visibility checkbox"""
        # checkbox feeds in an extra value when connected
        if self.ignoreInstantApply:  # will be set if changing ui modes
            return
        logger.debug("instantSetAreaVisCheckBox()")
        self.instantSetAreaLight(lightVis=True)

    def instantSetAreaNormCheckBox(self):
        """Instant method for normalize checkbox"""
        # checkbox feeds in an extra value when connected
        if self.ignoreInstantApply:  # will be set if changing ui modes
            return
        logger.debug("instantSetAreaNormCheckBox()")
        self.instantSetAreaLight(normalize=True)

    def instantSetAreaTempCheckBox(self):
        """Instant method for temperature checkbox"""
        # checkbox feeds in an extra value when connected
        if self.ignoreInstantApply:  # will be set if changing ui modes
            return
        logger.debug("instantSetAreaTempCheckBox()")
        self.instantSetAreaLight(temperature=True)

    def instantSetShapeCombo(self):
        """Instant method for changing the shape of the light"""
        # checkbox feeds in an extra value when connected
        if self.ignoreInstantApply:  # will be set if changing ui modes
            return
        logger.debug("instantSetShapeCombo()")
        self.instantSetAreaLight(shape=True)

    @toolsetcallbacks.ignoreCallbackDecorator
    def instantSetAreaLight(self, intensity=False, exposure=False, shape=False, normalize=False, lightVis=False,
                            lightColor=False, temperature=False, scale=False, message=True):
        """Will instantly apply any kwarg values set to True.  Applies the attributes using self.areaSetAttributes()

        :param message: report the message to the user?
        :type message: bool
        """
        if not self.properties.instantApply.value:  # instant apply not checked
            return
        if self.ignoreInstantApply:  # will be set if changing ui modes
            return
        logger.debug("instantSetAreaLight()")
        rendererNiceName = self.properties.rendererIconMenu.value
        if not renderertransferlights.getAllAreaLightsInScene(rendererNiceName)[0]:
            message = False  # switches off as no area lights in scene, so don't report error for instant apply
        self.areaSetAttributes(intensity=intensity, exposure=exposure, shape=shape, normalize=normalize,
                               lightVis=lightVis, lightColor=lightColor, temperature=temperature, scale=scale,
                               message=message, prioritizeNameBool=True)

    # ------------------------------------
    # GET (RETRIEVE) LIGHTS
    # ------------------------------------

    def refreshUpdateUIFromSelection(self, update=True):
        """Gets all the attributes (properties) from the first selected light and updates the scene

        :param update: if False will skip updating the UI, used on startup because it's auto
        :type update: bool
        """
        logger.debug("refreshUpdateUIFromSelection()")
        if not rendererload.getRendererIsLoaded(self.properties.rendererIconMenu.value):
            return  # the renderer is not loaded so don't update from scene
        rememberInstantApply = self.ignoreInstantApply
        self.ignoreInstantApply = True
        self.getAreaAttributes(allAttrs=True, setIntensityAs=None)  # get intensity/exposure as per the light
        self.getLightName()
        self.ignoreInstantApply = rememberInstantApply
        if update:
            self.updateFromProperties()

    @toolsetcallbacks.ignoreCallbackDecorator
    def getLightName(self, update=True):
        """retrieves the name of the first selected light in the scene

        :param update: if False will skip updating the UI, refreshUpdateUIFromSelection otherwise updates too much
        :type update: bool
        """
        # TODO: could include the ui name in the getLightNameSelected
        newName, suffixRemoved = \
            renderertransferlights.getLightNameSelected(removeSuffix=True, message=False,
                                                        lightFamily=renderertransferlights.AREALIGHTS)
        if not newName:  # could be None
            return
        # incoming newName is unique, can be long or short and has no suffix
        self.properties.suffix.value = suffixRemoved
        newNameWithSuffix = self.returnLightNameSuffixed(newName)
        if not cmds.objExists(newNameWithSuffix):
            om2.MGlobal.displayWarning("Check renderer and light type match, light not found.")
            return
        self.properties.name.longName = namehandling.getLongNameFromShort(newNameWithSuffix)
        newName = newName.split("|")[-1]  # may not be in scene as no suffix, may be long name
        self.properties.name.value = newName
        if update:
            self.updateFromProperties()

    @undodecorator.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def getAreaAttributes(self, intensity=False, exposure=False, shape=False, normalize=False, lightVis=False,
                          lightColor=False, temperature=False, scale=False, message=True, noScale=False,
                          allAttrs=False, setIntensityAs="exposure", update=True):
        """Updates self.properties with the specified values, then updates the whole UI with self.updateFromProperties()

        :param allAttrs: Will override and set all properties
        :type allAttrs: bool
        :param setIntensityAs: sets the intensity as pure "intensity" or "exposure" or None to ignore
        :type setIntensityAs: str
        :param update: if False will skip updating the UI, refreshUpdateUIFromSelection otherwise updates too much
        :type update: bool
        """
        logger.debug("getAreaAttributes()")
        if allAttrs:
            attrValDict = renderertransferlights.getLightAttrSelected(getIntensity=True, getExposure=True,
                                                                      getColor=True, getTemperature=True,
                                                                      getTempOnOff=True, getShape=True,
                                                                      getNormalize=True, getLightVisible=True,
                                                                      getScale=True, message=False)
        else:
            attrValDict = renderertransferlights.getLightAttrSelected(getIntensity=intensity, getExposure=exposure,
                                                                      getColor=lightColor, getTemperature=temperature,
                                                                      getTempOnOff=temperature, getShape=shape,
                                                                      getNormalize=normalize, getLightVisible=lightVis,
                                                                      getScale=scale)
        if not attrValDict:  # bail as nothing found
            return
        # EXPOSURE
        if attrValDict[EXPOSURE] is not None and setIntensityAs == "exposure":  # apply pure exposure
            intensityVal, exposureVal = lightingutils.convertExpAndIntToExposure(attrValDict[INTENSITY],
                                                                                 attrValDict[EXPOSURE])
            self.properties.intensity.value = float("{0:.3f}".format(round(intensityVal, 3)))
            self.properties.exposure.value = float("{0:.4f}".format(round(exposureVal, 4)))
        elif attrValDict[EXPOSURE] is not None and self.displayIndex() == UI_MODE_COMPACT:  # force pull, pure exposure
            intensityVal, exposureVal = lightingutils.convertExpAndIntToExposure(attrValDict[INTENSITY],
                                                                                 attrValDict[EXPOSURE])
            self.properties.intensity.value = float("{0:.3f}".format(round(intensityVal, 3)))
            self.properties.exposure.value = float("{0:.4f}".format(round(exposureVal, 4)))
        elif attrValDict[EXPOSURE] is not None and setIntensityAs is None:  # no convert on get
            self.properties.exposure.value = float("{0:.4f}".format(round(attrValDict[EXPOSURE], 4)))
            self.properties.intensity.value = float("{0:.3f}".format(round(attrValDict[INTENSITY], 3)))
        # INTENSITY
        elif attrValDict[INTENSITY] is not None and setIntensityAs == "intensity":  # apply pure exposure
            intensityVal, exposureVal = lightingutils.convertExpAndIntToIntensity(attrValDict[INTENSITY],
                                                                                  attrValDict[EXPOSURE])
            self.properties.intensity.value = float("{0:.3f}".format(round(intensityVal, 3)))
            self.properties.exposure.value = float("{0:.4f}".format(round(exposureVal, 4)))
        elif attrValDict[INTENSITY] is not None and setIntensityAs is None:  # no convert on get
            self.properties.intensity.value = float("{0:.3f}".format(round(attrValDict[INTENSITY], 3)))
        # LIGHT COLOR
        if attrValDict[LIGHTCOLOR] is not None:
            self.properties.color.value = attrValDict[LIGHTCOLOR]
        # TEMPERATURE
        if attrValDict[TEMPERATURE] is not None:
            temperature = float("{0:.2f}".format(round(attrValDict[TEMPERATURE], 2)))
            self.properties.temperature.value = temperature
            self.properties.tempBool.value = attrValDict[TEMPONOFF]
        # SHAPE
        if attrValDict[SHAPE] is not None:
            self.properties.shape.value = attrValDict[SHAPE]
        # NORMALIZE
        if attrValDict[NORMALIZE] is not None:
            self.properties.normalize.value = attrValDict[NORMALIZE]
        # LIGHT VIS
        if attrValDict[LIGHTVISIBILITY] is not None:
            self.properties.visibility.value = attrValDict[LIGHTVISIBILITY]
        # SCALE
        if attrValDict[SCALE] is not None:
            scaleValue = list()
            scaleValue.append(float("{0:.2f}".format(round(attrValDict[SCALE][0], 2))))  # round 2 decimal places
            scaleValue.append(float("{0:.2f}".format(round(attrValDict[SCALE][1], 2))))
            scaleValue.append(float("{0:.2f}".format(round(attrValDict[SCALE][2], 2))))
            self.properties.scale.value = scaleValue
        if update:
            self.updateFromProperties()

    # ------------------------------------
    # OFFSET ATTRIBUTES
    # ------------------------------------

    def areaCntrlShiftMultiplier(self):
        """For offset functions multiply shift and minimise if ctrl is held down
        If alt then call the reset option

        :return multiplier: multiply value, .2 if ctrl 5 if shift 1 if None
        :rtype multiplier: float
        :return reset: reset becomes true for resetting
        :rtype reset: bool
        """
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            return 5.0, False
        elif modifiers == QtCore.Qt.ControlModifier:
            return 0.2, False
        elif modifiers == QtCore.Qt.AltModifier:
            return 1, True
        return 1.0, False

    def areaHueSatOffset(self, offsetHue=False, offsetSat=False, neg=False):
        """The Hue and Saturation button logic

        :param offsetHue: do you want to offset the hue?
        :type offsetHue: bool
        :param offsetSat: do you want to offset the saturation?
        :type offsetSat: bool
        :param neg: reverse the offset in the negative (lower) values
        :type neg: bool
        """
        logger.debug("areaHueSatOffset()")
        colorSrgbFloat = colour.convertColorLinearToSrgb(self.properties.color.value)
        hsvColor = colour.convertRgbToHsv(colorSrgbFloat)
        multiplier, reset = self.areaCntrlShiftMultiplier()
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
        self.currentWidget().colorLightBtn.setColorLinearFloat(colorLinearFloat, noEmit=True)
        self.properties.color.value = colorLinearFloat
        # set color
        self.properties.tempBool.value = False
        self.areaSetAttributes(lightColor=True, temperature=True)

    @toolsetcallbacks.ignoreCallbackDecorator
    @ignoreInstantApplyDecorator
    @undodecorator.undoDecorator
    def areaLightOffsets(self, scale=False, normalize=False, lightVis=False, temperature=False,
                         intensity=False, exposure=False, shape=False, neg=False, message=True,
                         prioritizeNameBool=True):
        """Offsets the lights based on the buttons pressed given as True

        Usually will pass onto self.setAreaLightsUI() where the attributes and the GUI is updated.
        The exception is for the intensity and exposure buttons (without resetting) which return here

        "prioritizeNameBool" takes the name from the ui and tries to find it as the first item, includes selection

        :param neg: reverses the behaviour ie if brighten then will darken
        :type neg: bool
        :param message: report the message to the user
        :type message: bool
        :param prioritizeNameBool: takes the name from the ui and tries to find it as the first item, includes selection
        :type prioritizeNameBool: bool
        """
        logger.debug("areaLightOffsets()")
        multiplier, reset = self.areaCntrlShiftMultiplier()
        rendererNiceName = self.properties.rendererIconMenu.value
        lightDictAttributes = renderertransferlights.getLightDictAttributes()
        areaLightTransforms, areaLightShapes = self.findUIAreaLightSelection(prioritizeNameBool, message)
        if intensity and reset or exposure and reset:  # for resetting
            lightDictAttributes[INTENSITY] = self.properties.intensity.default
            lightDictAttributes[EXPOSURE] = self.properties.exposure.default
            self.properties.intensity.value = lightDictAttributes[INTENSITY]
            self.properties.exposure.value = lightDictAttributes[EXPOSURE]
        if intensity and not reset:  # set as pure intensity, will return here
            offset = AREA_INTENSITY_OFFSET * multiplier
            if neg:
                offset = -offset
            renderertransferlights.scaleAllLightIntensitiesLightList(offset,
                                                                     areaLightShapes,
                                                                     [],
                                                                     [],
                                                                     rendererNiceName,
                                                                     applyExposure=False,
                                                                     applyPure=True)
            # apply to UI
            intensity = self.properties.intensity.value
            exposure = self.properties.exposure.value
            intensity, exposure = lightingutils.convertExpAndIntToIntensity(intensity, exposure)
            intensity += intensity * (offset / 100)  # add a percentage of the intensity (use offset as percentage)
            self.properties.intensity.value = intensity
            self.properties.exposure.value = exposure
            self.ignoreInstantApply = False
            self.updateFromProperties()  # update the GUI
            return  # end since it's not related to setting other attrs
        elif exposure and not reset:  # set as pure exposure, will return here
            offset = AREA_INTENSITY_OFFSET * multiplier
            if neg:
                offset = -offset
            renderertransferlights.scaleAllLightIntensitiesLightList(offset,
                                                                     areaLightShapes,
                                                                     [],
                                                                     [],
                                                                     rendererNiceName,
                                                                     applyExposure=True,
                                                                     applyPure=True)
            # applies to UI as pure exposure
            intensity = self.properties.intensity.value
            exposure = self.properties.exposure.value
            intensity, exposure = lightingutils.convertExpAndIntToIntensity(intensity, exposure)
            intensity += intensity * (offset / 100)
            intensity, exposure = lightingutils.convertExpAndIntToExposure(intensity, exposure)
            self.properties.intensity.value = intensity
            self.properties.exposure.value = exposure
            self.ignoreInstantApply = False
            self.updateFromProperties()  # update the GUI
            return  # end since it's not related to setting other attrs
        elif shape:
            if reset:
                lightDictAttributes[SHAPE] = self.properties.shape.default  # is an int so 0
            else:
                offset = 1
                if neg:
                    offset = -offset
                lightDictAttributes[SHAPE] = self.properties.shape.value
                if lightDictAttributes[SHAPE] == 3 and not neg:
                    lightDictAttributes[SHAPE] = 0
                elif lightDictAttributes[SHAPE] == 0 and neg:
                    lightDictAttributes[SHAPE] = 3
                else:
                    lightDictAttributes[SHAPE] += offset
            self.properties.shape.value = lightDictAttributes[SHAPE]
        elif scale:
            if reset:
                lightDictAttributes[SCALE] = self.properties.scale.default
                scaleX = lightDictAttributes[SCALE][0]
                scaleY = lightDictAttributes[SCALE][1]
                scaleZ = lightDictAttributes[SCALE][2]
            else:
                offset = .1 * multiplier
                if neg:
                    offset = -offset
                lightDictAttributes[SCALE] = self.properties.scale.value
                scaleX = lightDictAttributes[SCALE][0]
                scaleY = lightDictAttributes[SCALE][1]
                scaleZ = lightDictAttributes[SCALE][2]
                scaleX = scaleX + (scaleX * offset)
                scaleY = scaleY + (scaleY * offset)
                scaleZ = scaleZ + (scaleZ * offset)
                lightDictAttributes[SCALE] = (scaleX, scaleY, scaleZ)
            self.properties.scale.value = (scaleX, scaleY, scaleZ)
        elif normalize:
            if reset:
                lightDictAttributes[NORMALIZE] = self.properties.normalize.default
            else:
                doNormalize = False
                if neg and self.properties.normalize.value is True:
                    doNormalize = True
                if not neg and self.properties.normalize.value is False:
                    doNormalize = True
                if doNormalize:
                    self.properties.normalize.value = not self.properties.normalize.value  # switch
                    self.advancedWidget.normalizeBx.blockSignals(True)
                    self.advancedWidget.normalizeBx.setChecked(self.properties.normalize.value)
                    self.advancedWidget.normalizeBx.blockSignals(False)
                    self.ignoreInstantApply = False
                    self.normalizeSwitch()
                return  # no other attributes are needed
        elif lightVis:
            if reset:
                lightDictAttributes[LIGHTVISIBILITY] = self.properties.visibility.default
            else:
                lightDictAttributes[LIGHTVISIBILITY] = not neg  # invert neg True False
            self.properties.visibility.value = lightDictAttributes[LIGHTVISIBILITY]
        elif temperature:
            if reset:
                lightDictAttributes[TEMPERATURE] = self.properties.temperature.default
                lightDictAttributes[TEMPONOFF] = self.properties.tempBool.default
                lightDictAttributes[LIGHTCOLOR] = self.properties.color.default
                self.properties.temperature.value = self.properties.temperature.default
                self.properties.tempBool.value = self.properties.tempBool.default
                self.properties.color.value = self.properties.color.default
            else:
                offset = 200.0 * multiplier
                if neg:
                    offset = -offset
                temperatureFloat = self.properties.temperature.value + offset
                if temperatureFloat < 0.0:  # clamp so doesn't go below zero
                    lightDictAttributes[TEMPERATURE] = 0.0
                    self.properties.temperature.value = 0.0
                else:  # is greater than zero
                    lightDictAttributes[TEMPERATURE] = temperatureFloat
                    self.properties.temperature.value = temperatureFloat
                lightDictAttributes[TEMPONOFF] = True
                self.properties.tempBool.value = True
                # adjust color of the light to match temp
                kelvinSrgbInt = colour.convertKelvinToRGB(self.properties.temperature.value)
                kelvinSrgbFloat = colour.rgbIntToFloat(kelvinSrgbInt)
                linearMayaColor = colour.convertColorSrgbToLinear(kelvinSrgbFloat)
                self.properties.color.value = linearMayaColor
                lightDictAttributes[LIGHTCOLOR] = linearMayaColor
            self.disableEnableTemperatureWidgets()
        # set the attributes and update GUI
        self.setAreaLightsUI(lightDictAttributes, message=message, prioritizeNameBool=prioritizeNameBool)

    # ------------------------------------
    # LIGHT NAME/RENAME
    # ------------------------------------

    def returnLightNameNoSuffix(self, lightName):
        """Returns the light name now without it's suffix matching any renderer eg "lightName_ARN" > "lightName"

        :param lightName: the string name of the light potentially with the suffix
        :type lightName: str
        """
        if self.properties.suffix.value:
            return renderertransferlights.removeRendererSuffix(lightName)[0]
        return lightName

    def returnLightNameSuffixed(self, lightName):
        """Returns the light name now with a suffix matching the renderer eg "lightName" > "lightName_ARN" (Arnold)

        :param lightName: the string name of the light before the suffix
        :type lightName: str
        """
        if not self.properties.suffix.value:
            return lightName
        suffix = RENDERER_SUFFIX[self.properties.rendererIconMenu.value]
        return "_".join([lightName, suffix])

    @undodecorator.undoDecorator
    @ignoreInstantApplyDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def renameLight(self):
        """renames the selected light updates self.properties

        Updates the UI as the new light name might be a duplicate and not unique
        Updates self.properties.name.longName
        """
        newName = self.properties.name.value
        addSuffix = self.properties.suffix.value
        logger.debug("Renaming self.properties.name.longName {}".format(self.properties.name.longName))
        renameLight = self.properties.name.longName
        if not cmds.objExists(renameLight):
            om2.MGlobal.displayWarning("Area light does not exist: {}".format(renameLight))
            return
        lightTransform, lightShape = renderertransferlights.renameLight(renameLight,
                                                                        newName,
                                                                        addSuffix=addSuffix,
                                                                        lightFamily=renderertransferlights.AREALIGHTS)
        # lightTransform is unique so can longname it
        self.properties.name.longName = namehandling.getLongNameFromShort(lightTransform)
        # see whether to update the ui name
        lightTransformNoSuffix = namehandling.getShortName(self.returnLightNameNoSuffix(lightTransform))
        if lightTransformNoSuffix != newName:  # then the UI needs to update
            self.properties.name.value = lightTransformNoSuffix  # doesn't like unicode
            self.ignoreInstantApply = False
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

    # ------------------------------------
    # COLOR
    # ------------------------------------

    def disableEnableTemperatureWidgets(self):
        """Disable/enable temperature widget, uses self.properties.tempBool.value
        """
        logger.debug("disableEnableTemperatureWidgets()")
        for uiInstance in self.widgets():
            uiInstance.colorLightBtn.setDisabledLabel(self.properties.tempBool.value)
        self.advancedWidget.temperatureTxt.setDisabled(not self.properties.tempBool.value)

    # ------------------------------------
    # NORMALIZE
    # ------------------------------------

    @undodecorator.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def normalizeSwitch(self, value=0, skipAdjustIntExp=False):
        """ When the normalize checkbox changes, this converts the selected lights automatically and updates the ui.

        The "value" kwarg is because the checkbox passes in a value that we don't use, it must remain

        Updates exposure and intensity in the ui.
        """
        if self.ignoreInstantApply:
            return
        logger.debug("normalizeSwitch(skipAdjustIntExp={})".format(skipAdjustIntExp))
        if skipAdjustIntExp:  # do not change the intensity and exposure just invert intensity
            self.properties.normalize.value = not self.properties.normalize.value
            self.advancedWidget.normalizeBx.blockSignals(True)
            self.advancedWidget.normalizeBx.setChecked(self.properties.normalize.value)
            self.advancedWidget.normalizeBx.blockSignals(False)
            if not self.ignoreInstantApply:  # set the actual light/s
                self.areaSetAttributes(normalize=True, message=False)
            return
        if self.properties.intensity.value == 0:  # can't calculate with intensity of 0
            om2.MGlobal.displayWarning("Intensity must not be zero. Illegitimate Value.")
            return
        # auto figure applying as intensity or exposure
        convertAsInt = False
        if self.properties.exposure.value == 0:  # auto apply as intensity if exposure is set to zero
            convertAsInt = True
        # UI convert intensity and exposure
        rendererNiceName = self.properties.rendererIconMenu.value
        intensity, exposure = renderertransferlights.convertNormalizeRenderer(self.properties.normalize.value,
                                                                              self.properties.intensity.value,
                                                                              self.properties.exposure.value,
                                                                              self.properties.shape.value,
                                                                              self.properties.scale.value,
                                                                              rendererNiceName,
                                                                              convertAsIntensity=convertAsInt)
        self.properties.intensity.value = float("{0:.3f}".format(round(intensity, 3)))
        self.properties.exposure.value = float("{0:.4f}".format(round(exposure, 4)))
        if self.properties.instantApply.value:  # instant apply checkbox is on so apply normalization to scene lights
            lightTransforms, lightShapes = self.findUIAreaLightSelection()
            # normalize the light list and set in the scene
            renderertransferlights.convertNormalizeList(lightTransforms,
                                                        self.properties.normalize.value,
                                                        applyAsIntensity=convertAsInt,
                                                        renderer=self.properties.rendererIconMenu.value)
        self.ignoreInstantApply = False  # return ignore to inverse of the checkbox
        self.updateFromProperties()  # update the UI without effecting the scene

    # ------------------------------------
    # CONNECTIONS
    # ------------------------------------

    def uiConnections(self):
        """Hooks up the actual button/widgets functionality
        """
        for uiInstance in self.widgets():
            uiInstance.createAreaLightBtn.clicked.connect(self.createAreaLight)
            uiInstance.dropAreaLightBtn.clicked.connect(partial(self.createAreaLight, createFrom=2))
            # bottom get/set all buttons
            uiInstance.applyToSelectedBtn.clicked.connect(partial(self.areaSetAttributes, allAttrs=True))
            uiInstance.pullFromSelectedBtn.clicked.connect(partial(self.getAreaAttributes, allAttrs=True))
            # place reflection
            uiInstance.areaPlaceReflectionBtn.clicked.connect(self.placeReflection)
            # set/get buttons
            uiInstance.renameLightBtn.clicked.connect(self.renameLight)
            uiInstance.namePullBtn.clicked.connect(self.getLightName)
            uiInstance.exposureBtn.clicked.connect(partial(self.areaSetAttributes, exposure=True))
            uiInstance.exposurePullBtn.clicked.connect(partial(self.getAreaAttributes, exposure=True, intensity=True))
            uiInstance.colorApplyBtn.clicked.connect(partial(self.areaSetAttributes, lightColor=True))
            uiInstance.colorPullBtn.clicked.connect(partial(self.getAreaAttributes, lightColor=True))
            uiInstance.shapeBtn.clicked.connect(partial(self.areaSetAttributes, shape=True))
            uiInstance.shapePullBtn.clicked.connect(partial(self.getAreaAttributes, shape=True))
            # Instant Apply Area Lights
            uiInstance.lightNameTxt.edit.textModified.connect(self.instantSetLightAreaName)
            uiInstance.lightSuffixCheckbox.stateChanged.connect(self.instantSetLightAreaName)
            uiInstance.exposureTxt.edit.textModified.connect(partial(self.instantSetAreaLight, exposure=True))
            uiInstance.colorLightBtn.colorChanged.connect(partial(self.instantSetAreaLight, lightColor=True))
            uiInstance.shapeCombo.itemChanged.connect(self.instantSetShapeCombo)
            # offsets
            uiInstance.scaleAreaNegExposureBtn.clicked.connect(partial(self.areaLightOffsets, exposure=True, neg=True))
            uiInstance.scaleAreaPosExposureBtn.clicked.connect(partial(self.areaLightOffsets, exposure=True, neg=False))
            uiInstance.areaColHueBtnNeg.clicked.connect(partial(self.areaHueSatOffset, offsetHue=True, neg=True))
            uiInstance.areaColHueBtnPos.clicked.connect(partial(self.areaHueSatOffset, offsetHue=True, neg=False))
            uiInstance.areaColSatBtnNeg.clicked.connect(partial(self.areaHueSatOffset, offsetSat=True, neg=True))
            uiInstance.areaColSatBtnPos.clicked.connect(partial(self.areaHueSatOffset, offsetSat=True, neg=False))
            uiInstance.areaShapeOffsetBtnNeg.clicked.connect(partial(self.areaLightOffsets, shape=True, neg=True))
            uiInstance.areaShapeOffsetBtnPos.clicked.connect(partial(self.areaLightOffsets, shape=True, neg=False))
            # menu modes
            uiInstance.lightNameMenu.aboutToShow.connect(self.setLightNameMenuModes)
            uiInstance.lightNameMenu.menuChanged.connect(self.menuSwitchToAreaLight)
            uiInstance.colorBtnMenu.aboutToShow.connect(self.showColorMenu)
            uiInstance.colorBtnMenu.menuChanged.connect(self.turnOffTemperatureMenu)
            # change renderer
            uiInstance.rendererIconMenu.actionTriggered.connect(self.global_changeRenderer)
        # advanced only
        self.advancedWidget.applyToSelectedNoScaleBtn.clicked.connect(partial(self.areaSetAttributes, allAttrs=True,
                                                                              noScale=True))
        # set/get buttons adv
        self.advancedWidget.intensityBtn.clicked.connect(partial(self.areaSetAttributes, intensity=True))
        self.advancedWidget.intensityPullBtn.clicked.connect(partial(self.getAreaAttributes, intensity=True,
                                                                     exposure=True, setIntensityAs="intensity"))
        self.advancedWidget.tempBtn.clicked.connect(partial(self.areaSetAttributes, temperature=True))
        self.advancedWidget.tempPullBtn.clicked.connect(partial(self.getAreaAttributes, temperature=True))
        self.advancedWidget.normalizeBtn.clicked.connect(partial(self.areaSetAttributes, normalize=True))
        self.advancedWidget.normalizePullBtn.clicked.connect(partial(self.getAreaAttributes, normalize=True))
        self.advancedWidget.lightVisBtn.clicked.connect(partial(self.areaSetAttributes, lightVis=True))
        self.advancedWidget.lightVisPullBtn.clicked.connect(partial(self.getAreaAttributes, lightVis=True))
        self.advancedWidget.scaleBtn.clicked.connect(partial(self.areaSetAttributes, scale=True))
        self.advancedWidget.scalePullBtn.clicked.connect(partial(self.getAreaAttributes, scale=True))
        # instant apply adv
        self.advancedWidget.intensityTxt.edit.textModified.connect(partial(self.instantSetAreaLight, intensity=True))
        self.advancedWidget.temperatureTxt.edit.textModified.connect(partial(self.instantSetAreaLight,
                                                                             temperature=True))
        self.advancedWidget.tempOnOffBx.stateChanged.connect(self.instantSetAreaTempCheckBox)
        self.advancedWidget.normalizeBx.stateChanged.connect(self.normalizeSwitch)  # special case due to multiple vals
        self.advancedWidget.scaleVEdit.textModified.connect(partial(self.instantSetAreaLight, scale=True))
        self.advancedWidget.lightVisBx.stateChanged.connect(self.instantSetAreaVisCheckBox)
        # offsets adv
        self.advancedWidget.scaleAreaNegIntensityBtn.clicked.connect(partial(self.areaLightOffsets, intensity=True,
                                                                             neg=True))
        self.advancedWidget.scaleAreaPosIntensityBtn.clicked.connect(partial(self.areaLightOffsets, intensity=True,
                                                                             neg=False))
        self.advancedWidget.areaScaleOffsetBtnNeg.clicked.connect(partial(self.areaLightOffsets, scale=True,
                                                                          neg=True))
        self.advancedWidget.areaScaleOffsetBtnPos.clicked.connect(partial(self.areaLightOffsets, scale=True,
                                                                          neg=False))
        self.advancedWidget.areaTempOffsetBtnNeg.clicked.connect(partial(self.areaLightOffsets, temperature=True,
                                                                         neg=True))
        self.advancedWidget.areaTempOffsetBtnPos.clicked.connect(partial(self.areaLightOffsets, temperature=True,
                                                                         neg=False))
        self.advancedWidget.normalizeOffsetBtnNeg.clicked.connect(partial(self.areaLightOffsets, normalize=True,
                                                                          neg=True))
        self.advancedWidget.normalizeOffsetBtnPos.clicked.connect(partial(self.areaLightOffsets, normalize=True,
                                                                          neg=False))
        self.advancedWidget.areaVisOffsetBtnNeg.clicked.connect(partial(self.areaLightOffsets, lightVis=True,
                                                                        neg=True))
        self.advancedWidget.areaVisOffsetBtnPos.clicked.connect(partial(self.areaLightOffsets, lightVis=True,
                                                                        neg=False))
        # disable enable hide show uis
        self.advancedWidget.tempOnOffBx.stateChanged.connect(self.disableEnableTemperatureWidgets)
        self.advancedWidget.areaInstantBx.stateChanged.connect(self.instantApplyOnOff)
        # menu connections
        self.advancedWidget.intExpMenu.menuChanged.connect(self.intExpMenuChanged)
        self.advancedWidget.normalizeMenu.menuChanged.connect(partial(self.normalizeSwitch, skipAdjustIntExp=True))
        # callback connections
        self.selectionCallbacks.callback.connect(self.selectionChanged)  # monitor selection
        self.toolsetActivated.connect(self.startSelectionCallback)
        self.toolsetDeactivated.connect(self.stopSelectionCallback)

    # ------------------
    # RIGHT CLICK TOOLSET ICON
    # ------------------

    def actions(self):
        """Right click menu on the main toolset tool icon"""
        return [{"type": "action",
                 "name": "create1",
                 "label": "Create Area Light 1cm",
                 "icon": "lightarea",
                 "tooltip": ""},
                {"type": "action",
                 "name": "create10",
                 "label": "Create Area Light 10cm",
                 "icon": "lightarea",
                 "tooltip": ""},
                {"type": "action",
                 "name": "create50",
                 "label": "Create Area Light 50cm",
                 "icon": "lightarea",
                 "tooltip": ""},
                {"type": "action",
                 "name": "create200",
                 "label": "Create Area Light 2m",
                 "icon": "lightarea",
                 "tooltip": ""}]

    def executeActions(self, action):
        pass
        return
        name = action["name"]
        if name == "create1":
            print("area light 1cm created")
        elif name == "create10":
            print("area light 10cm created")
        elif name == "create50":
            print("area light 50cm created")
        elif name == "create200":
            print("area light 2m created")


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
        # Name  ----------------------------------------------------------------------
        toolTip = ("Name of the light.  Suffix will be added if checked")
        self.lightNameTxt = elements.StringEdit(self.properties.name.label,
                                                self.properties.name.value,
                                                parent=parent,
                                                toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.lightNameTxt, "name")
        # TODO Parenting messes the stylesheet but it should have one
        self.lightNameMenu = elements.ExtendedMenu(searchVisible=True)
        self.lightNameTxt.setMenu(self.lightNameMenu)  # right click. Note the menu items will be dynamic
        self.lightNameTxt.setMenu(self.lightNameMenu, mouseButton=QtCore.Qt.LeftButton)  # left click
        toolTip = "Automatically add a suffix to the light name Eg. area_ARN\n" \
                  "Arnold: _ARN\n" \
                  "Redshift: _RS\n" \
                  "Renderman: _PXR"
        self.lightSuffixCheckbox = elements.CheckBox(self.properties.suffix.label,
                                                     parent=parent,
                                                     toolTip=toolTip,
                                                     checked=self.properties.suffix.value)
        self.toolsetWidget.linkProperty(self.lightSuffixCheckbox, "suffix")
        toolTip = "Rename the selected light"
        self.renameLightBtn = elements.styledButton("", "arrowRight",
                                                    parent,
                                                    toolTip,
                                                    style=uic.BTN_TRANSPARENT_BG,
                                                    minWidth=uic.BTN_W_ICN_REG)
        self.pushPullBtns.append(self.renameLightBtn)
        toolTip = "Get the name of the selected light"
        self.namePullBtn = elements.styledButton("", "arrowLeft",
                                                 parent,
                                                 toolTip,
                                                 style=uic.BTN_TRANSPARENT_BG,
                                                 minWidth=uic.BTN_W_ICN_REG)
        self.pushPullBtns.append(self.namePullBtn)
        # Exposure label/edit  ----------------------------------------------------------------------
        toolTip = ("Set the light's exposure value \n"
                   "Exposure can be used instead of Intensity without requiring large numbers.\n"
                   "Exposure is usually used when Normalize is on.\n"
                   "Intensity should be set to 1.0 when using exposure")
        self.exposureTxt = elements.FloatEdit(self.properties.exposure.label,
                                              self.properties.exposure.value,
                                              parent=parent,
                                              toolTip=toolTip,
                                              enableMenu=True,
                                              rounding=4)
        self.toolsetWidget.linkProperty(self.exposureTxt, "exposure")

        toolTip = "Darken all selected light's exposure.\n" \
                  "Ignores the UI setting and multiplies based on each light's current exposure value\n" \
                  "(shift faster, ctrl slower, alt reset)"
        self.scaleAreaNegExposureBtn = elements.styledButton("", "exposureClosed",
                                                             parent,
                                                             toolTip,
                                                             style=uic.BTN_TRANSPARENT_BG,
                                                             minWidth=uic.BTN_W_ICN_LRG)
        toolTip = "Brighten all selected light's exposure.\n" \
                  "Ignores the UI setting and multiplies based on each lights current exposure value\n" \
                  "(shift faster, ctrl slower, alt reset)"
        self.scaleAreaPosExposureBtn = elements.styledButton("", "exposureOpen",
                                                             parent,
                                                             toolTip,
                                                             style=uic.BTN_TRANSPARENT_BG,
                                                             minWidth=uic.BTN_W_ICN_LRG)
        toolTip = "Set the exposure of the selected area light/s\n" \
                  "Intensity will be set to 1.0" \
                  "*Redshift: Exposure is converted to intensity in old versions.\n"
        self.exposureBtn = elements.styledButton("", "arrowRight",
                                                 parent,
                                                 toolTip,
                                                 style=uic.BTN_TRANSPARENT_BG,
                                                 minWidth=uic.BTN_W_ICN_REG)
        self.pushPullBtns.append(self.exposureBtn)
        toolTip = "Get the selected light's exposure value"
        self.exposurePullBtn = elements.styledButton("", "arrowLeft",
                                                     parent,
                                                     toolTip,
                                                     style=uic.BTN_TRANSPARENT_BG,
                                                     minWidth=uic.BTN_W_ICN_REG)
        self.pushPullBtns.append(self.exposurePullBtn)
        # Shape combo box  ----------------------------------------------------------------------
        toolTip = "Set the light's shape\n" \
                  "Arnold does not support sphere lights.\n" \
                  "Renderman does not support cylinder lights."
        self.shapeCombo = elements.ComboBoxRegular(self.properties.shape.label,
                                                   SHAPE_LIST_NICE,
                                                   parent=parent,
                                                   toolTip=toolTip,
                                                   setIndex=self.properties.shape.value)
        self.toolsetWidget.linkProperty(self.shapeCombo, "shape")

        toolTip = "Step through the shapes"
        self.areaShapeOffsetBtnNeg = elements.styledButton("", "previousLine",
                                                           parent,
                                                           toolTip,
                                                           style=uic.BTN_TRANSPARENT_BG,
                                                           minWidth=uic.BTN_W_ICN_LRG)
        toolTip = "Step through the shapes"
        self.areaShapeOffsetBtnPos = elements.styledButton("", "nextLine",
                                                           parent, toolTip,
                                                           style=uic.BTN_TRANSPARENT_BG,
                                                           minWidth=uic.BTN_W_ICN_LRG)
        toolTip = "Set the shape of the selected light/s"
        self.shapeBtn = elements.styledButton("", "arrowRight",
                                              parent,
                                              toolTip,
                                              style=uic.BTN_TRANSPARENT_BG,
                                              minWidth=uic.BTN_W_ICN_REG)
        self.pushPullBtns.append(self.shapeBtn)
        toolTip = "Get the shape of the selected light"
        self.shapePullBtn = elements.styledButton("", "arrowLeft",
                                                  parent,
                                                  toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=uic.BTN_W_ICN_REG)
        self.pushPullBtns.append(self.shapePullBtn)
        # Color label/color cmds widget  ----------------------------------------------------------------------
        toolTip = "The color of the area light"
        self.colorLightBtn = cmdswidgets.MayaColorBtn(text=self.properties.color.label,
                                                      color=self.properties.color.value,
                                                      parent=parent,
                                                      toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.colorLightBtn, "color")
        # TODO Parenting messes the stylesheet but it should have one
        self.colorBtnMenu = elements.ExtendedMenu(searchVisible=False)

        toolTip = "Hue: Decrease (shift faster, ctrl slower, alt reset)"
        self.areaColHueBtnNeg = elements.styledButton("", "previousSml",
                                                      parent,
                                                      toolTip,
                                                      style=uic.BTN_TRANSPARENT_BG,
                                                      minWidth=uic.BTN_W_ICN_SML)
        toolTip = "Hue: Increase (shift faster, ctrl slower, alt reset)"
        self.areaColHueBtnPos = elements.styledButton("", "nextSml",
                                                      parent,
                                                      toolTip,
                                                      style=uic.BTN_TRANSPARENT_BG,
                                                      minWidth=uic.BTN_W_ICN_SML)
        toolTip = "Saturation: Decrease (shift faster, ctrl slower, alt reset)"
        self.areaColSatBtnNeg = elements.styledButton("", "previousSml",
                                                      parent,
                                                      toolTip,
                                                      style=uic.BTN_TRANSPARENT_BG,
                                                      minWidth=uic.BTN_W_ICN_SML)
        toolTip = "Saturation: Increase (shift faster, ctrl slower, alt reset)"
        self.areaColSatBtnPos = elements.styledButton("", "nextSml",
                                                      parent,
                                                      toolTip,
                                                      style=uic.BTN_TRANSPARENT_BG,
                                                      minWidth=uic.BTN_W_ICN_SML)
        toolTip = "Set the color of the selected area light/s"
        self.colorApplyBtn = elements.styledButton("", "arrowRight",
                                                   parent,
                                                   toolTip,
                                                   style=uic.BTN_TRANSPARENT_BG,
                                                   minWidth=uic.BTN_W_ICN_REG)
        self.pushPullBtns.append(self.colorApplyBtn)
        toolTip = "Get the color of the selected area light"
        self.colorPullBtn = elements.styledButton("", "arrowLeft",
                                                  parent,
                                                  toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=uic.BTN_W_ICN_REG)
        self.pushPullBtns.append(self.colorPullBtn)
        # create area light ----------------------------------------------------------------------
        toolTip = "Create a new light with the current settings"
        self.createAreaLightBtn = elements.styledButton("Create", "lightAreaRect",
                                                        parent,
                                                        toolTip)
        toolTip = "Create a new light at the camera position"
        self.dropAreaLightBtn = elements.styledButton("Drop", "dropCamera",
                                                      parent,
                                                      toolTip)
        toolTip = "Place Reflection by www.braverabbit.com (Ingo Clemens).\n" \
                  "(Third Party Community Tools must be installed).\n" \
                  "With a light selected, click-drag on a surface to place the light's highlight \n" \
                  "Hold Ctrl or Shift, click-drag to vary the distance of the light from the surface \n" \
                  "Open source repository: https://github.com/IngoClemens/placeReflection"
        self.areaPlaceReflectionBtn = elements.styledButton("Place", "placeReflection",
                                                            parent,
                                                            toolTip)
        # get values  ----------------------------------------------------------------------
        toolTip = "Get all values from the first selected area light\nLight name is not included"
        self.pullFromSelectedBtn = elements.styledButton("Pull Selected", "arrowLeft",
                                                         parent,
                                                         toolTip)

        toolTip = "Applies the selected area light/s with the above settings\n" \
                  "Lights are not renamed"
        self.applyToSelectedBtn = elements.styledButton("Apply All", "arrowRight",
                                                        parent,
                                                        toolTip)
        # set default renderer  ----------------------------------------------------------------------
        self.rendererIconMenu = elements.iconMenuButtonCombo(DFLT_RNDR_MODES,
                                                             self.properties.rendererIconMenu.value,
                                                             toolTip=toolTip)
        # hide push and pull major buttons as no longer needed
        self.pullFromSelectedBtn.hide()
        self.applyToSelectedBtn.hide()

        # ----------------------------------------------------------------------
        # ADVANCED UI WIDGETS
        # ----------------------------------------------------------------------
        if self.uiMode == UI_MODE_ADVANCED:
            # Intensity label/edit  ----------------------------------------------------------------------
            toolTip = ("Set the light's intensity value")
            self.intensityTxt = elements.FloatEdit(self.properties.intensity.label,
                                                   self.properties.intensity.value,
                                                   parent=self,
                                                   toolTip=toolTip,
                                                   enableMenu=True, rounding=3)
            self.toolsetWidget.linkProperty(self.intensityTxt, "intensity")

            # menu for intensity and exposure only in Advanced mode
            self.intExpMenuModeList = [("brightenBulb", "Convert To Pure Intensity"),
                                       ("exposureOpen", "Convert To Pure Exposure")]
            self.intExpMenu = elements.ExtendedMenu(searchVisible=False)
            self.exposureTxt.setMenu(self.intExpMenu, modeList=self.intExpMenuModeList)  # right click
            self.exposureTxt.setMenu(self.intExpMenu, mouseButton=QtCore.Qt.LeftButton)  # left click
            self.intensityTxt.setMenu(self.intExpMenu)  # right click, same menu created as per exposureTxt
            self.intensityTxt.setMenu(self.intExpMenu, mouseButton=QtCore.Qt.LeftButton)  # left click
            # intensity buttons
            toolTip = "Darken all selected light's intensity.\n" \
                      "Ignores the UI setting and multiplies based on each light's current intensity value\n" \
                      "(shift faster, ctrl slower, alt reset)"
            self.scaleAreaNegIntensityBtn = elements.styledButton("", "darkenBulb",
                                                                  self,
                                                                  toolTip,
                                                                  style=uic.BTN_TRANSPARENT_BG,
                                                                  minWidth=uic.BTN_W_ICN_LRG)
            toolTip = "Brighten all selected light's intensity.\n" \
                      "Ignores the UI setting and multiplies based on each light's current intensity value\n" \
                      "(shift faster, ctrl slower, alt reset)"
            self.scaleAreaPosIntensityBtn = elements.styledButton("", "brightenBulb",
                                                                  self,
                                                                  toolTip,
                                                                  style=uic.BTN_TRANSPARENT_BG,
                                                                  minWidth=uic.BTN_W_ICN_LRG)
            toolTip = "Set the intensity of the selected area light. Exposure becomes 0.0"
            self.intensityBtn = elements.styledButton("", "arrowRight",
                                                      self,
                                                      toolTip,
                                                      style=uic.BTN_TRANSPARENT_BG,
                                                      minWidth=uic.BTN_W_ICN_REG)
            self.pushPullBtns.append(self.intensityBtn)
            toolTip = "Get the intensity of the selected area light. Exposure becomes 0.0"
            self.intensityPullBtn = elements.styledButton("", "arrowLeft",
                                                          self,
                                                          toolTip,
                                                          style=uic.BTN_TRANSPARENT_BG,
                                                          minWidth=uic.BTN_W_ICN_REG)
            self.pushPullBtns.append(self.intensityPullBtn)
            # Normalize Label  ----------------------------------------------------------------------
            toolTip = "Set the normalize value of an area light\n" \
                      "On: The intensity/exposure is spread across the light's area\n" \
                      "Off: Each square cm is set to the intensity/exposure\n" \
                      "Intensity/Exposure will automatically adjust, right-click to ignore auto-adjust."
            self.normalizeLabel = elements.Label(self.properties.normalize.label,
                                                 self,
                                                 toolTip=toolTip,
                                                 enableMenu=True)

            self.normalizeBx = elements.CheckBox("",
                                                 parent=self,
                                                 checked=self.properties.normalize.value,
                                                 toolTip=toolTip,
                                                 enableMenu=True)
            self.toolsetWidget.linkProperty(self.normalizeBx, "normalize")

            self.normalizeMenuModeList = [("off", "Normalize Don't Change Int/Exp")]
            # TODO Parenting messes the stylesheet but it should have one
            self.normalizeMenu = elements.ExtendedMenu(searchVisible=False)
            self.normalizeBx.setMenu(self.normalizeMenu, modeList=self.normalizeMenuModeList)
            self.normalizeLabel.setMenu(self.normalizeMenu)  # label uses same menu as normalizeBx
            self.normalizeLabel.setMenu(self.normalizeMenu, mouseButton=QtCore.Qt.LeftButton)  # left click

            toolTip = "Set the normalize attribute off"
            self.normalizeOffsetBtnNeg = elements.styledButton("", "off",
                                                               self,
                                                               toolTip,
                                                               style=uic.BTN_TRANSPARENT_BG,
                                                               minWidth=uic.BTN_W_ICN_LRG)
            toolTip = "Set the normalize attribute on"
            self.normalizeOffsetBtnPos = elements.styledButton("", "on",
                                                               self,
                                                               toolTip,
                                                               style=uic.BTN_TRANSPARENT_BG,
                                                               minWidth=uic.BTN_W_ICN_LRG)
            toolTip = "Set the normalize value of the selected area light"
            self.normalizeBtn = elements.styledButton("", "arrowRight",
                                                      self,
                                                      toolTip,
                                                      style=uic.BTN_TRANSPARENT_BG,
                                                      minWidth=uic.BTN_W_ICN_REG)
            self.pushPullBtns.append(self.normalizeBtn)
            toolTip = "Get the normalize value of the selected area light"
            self.normalizePullBtn = elements.styledButton("", "arrowLeft",
                                                          self,
                                                          toolTip,
                                                          style=uic.BTN_TRANSPARENT_BG,
                                                          minWidth=uic.BTN_W_ICN_REG)
            self.pushPullBtns.append(self.normalizePullBtn)
            # Light Visibility label  ----------------------------------------------------------------------
            toolTip = "The light's primary visibility as viewed through the camera.\n" \
                      "In older versions of Arnold, this isn't supported"
            self.lightVisLabel = elements.Label(self.properties.visibility.label,
                                                self,
                                                toolTip=toolTip)
            toolTip = "The light's primary visibility as viewed through the camera.\n" \
                      "In older versions of Arnold, this isn't supported"
            self.lightVisBx = elements.CheckBox("",
                                                parent=self,
                                                checked=self.properties.visibility.value,
                                                toolTip=toolTip)
            self.toolsetWidget.linkProperty(self.lightVisBx, "visibility")

            toolTip = "Invisible: The light source cannot be seen by the camera"
            self.areaVisOffsetBtnNeg = elements.styledButton("", "invisible",
                                                             self,
                                                             toolTip,
                                                             style=uic.BTN_TRANSPARENT_BG,
                                                             minWidth=uic.BTN_W_ICN_LRG)
            toolTip = "Visible: The light source can be seen by the camera"
            self.areaVisOffsetBtnPos = elements.styledButton("", "visible",
                                                             self,
                                                             toolTip,
                                                             style=uic.BTN_TRANSPARENT_BG,
                                                             minWidth=uic.BTN_W_ICN_LRG)
            toolTip = "Set the camera visibility for the selected area light/s"
            self.lightVisBtn = elements.styledButton("", "arrowRight",
                                                     self,
                                                     toolTip,
                                                     style=uic.BTN_TRANSPARENT_BG,
                                                     minWidth=uic.BTN_W_ICN_REG)
            self.pushPullBtns.append(self.lightVisBtn)
            toolTip = "Get the camera visibility for the selected area light"
            self.lightVisPullBtn = elements.styledButton("", "arrowLeft",
                                                         self,
                                                         toolTip,
                                                         style=uic.BTN_TRANSPARENT_BG,
                                                         minWidth=uic.BTN_W_ICN_REG)
            self.pushPullBtns.append(self.lightVisPullBtn)
            # Temperature label/edit  ----------------------------------------------------------------------
            toolTip = ("The color in temperature (degrees kelvin).\nColor (Hue/Sat) is ignored.")
            self.temperatureTxt = elements.FloatEdit(self.properties.temperature.label,
                                                     str(self.properties.temperature.value),
                                                     parent=self,
                                                     toolTip=toolTip,
                                                     labelRatio=25,
                                                     editRatio=20)
            self.toolsetWidget.linkProperty(self.temperatureTxt, "temperature")

            toolTip = "Color Temperature on/off\n" \
                      "Off: Color (hue/sat) only will be used\n" \
                      "On: Temperature only will be used"
            self.tempOnOffBx = elements.CheckBox(self.properties.tempBool.label,
                                                 parent=self,
                                                 checked=self.properties.tempBool.value,
                                                 toolTip=toolTip)
            self.toolsetWidget.linkProperty(self.tempOnOffBx, "tempBool")

            toolTip = "Warm the color temperature in degrees kelvin\n" \
                      "(shift faster, ctrl slower, alt reset)"
            self.areaTempOffsetBtnNeg = elements.styledButton("", "hot",
                                                              self,
                                                              toolTip,
                                                              style=uic.BTN_TRANSPARENT_BG,
                                                              minWidth=uic.BTN_W_ICN_LRG)
            toolTip = "Cool the color temperature in degrees kelvin\n" \
                      "(shift faster, ctrl slower, alt reset)"
            self.areaTempOffsetBtnPos = elements.styledButton("", "cold",
                                                              self,
                                                              toolTip,
                                                              style=uic.BTN_TRANSPARENT_BG,
                                                              minWidth=uic.BTN_W_ICN_LRG)
            toolTip = "Set the color in temperature (degrees kelvin) for the selected area light/s"
            self.tempBtn = elements.styledButton("", "arrowRight",
                                                 self,
                                                 toolTip,
                                                 style=uic.BTN_TRANSPARENT_BG,
                                                 minWidth=uic.BTN_W_ICN_REG)
            self.pushPullBtns.append(self.tempBtn)
            toolTip = "Get the color in temperature (degrees kelvin) for the selected area light"
            self.tempPullBtn = elements.styledButton("", "arrowLeft",
                                                     self,
                                                     toolTip,
                                                     style=uic.BTN_TRANSPARENT_BG,
                                                     minWidth=uic.BTN_W_ICN_REG)
            self.pushPullBtns.append(self.tempPullBtn)
            # Scale label vector edit  ----------------------------------------------------------------------
            toolTip = "The physical scale size of the area light/s"
            self.scaleVEdit = elements.VectorLineEdit(self.properties.scale.label,
                                                      self.properties.scale.value,
                                                      axis=("x", "y", "z"),
                                                      parent=self,
                                                      toolTip=toolTip,
                                                      labelRatio=1,
                                                      editRatio=4,
                                                      spacing=uic.SREG)
            self.toolsetWidget.linkProperty(self.scaleVEdit, "scale")

            toolTip = "Scale smaller: Make the physical scale size smaller\n" \
                      "(shift faster, ctrl slower, alt reset)"
            self.areaScaleOffsetBtnNeg = elements.styledButton("", "scaleDown",
                                                               self,
                                                               toolTip,
                                                               style=uic.BTN_TRANSPARENT_BG,
                                                               minWidth=uic.BTN_W_ICN_LRG)
            toolTip = "Scale larger: Make the physical scale size smaller\n" \
                      "(shift faster, ctrl slower, alt reset)"
            self.areaScaleOffsetBtnPos = elements.styledButton("", "scaleUp",
                                                               self,
                                                               toolTip,
                                                               style=uic.BTN_TRANSPARENT_BG,
                                                               minWidth=uic.BTN_W_ICN_LRG)
            toolTip = "Set the physical scale size for selected area light/s"
            self.scaleBtn = elements.styledButton("", "arrowRight",
                                                  self,
                                                  toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=uic.BTN_W_ICN_REG)
            self.pushPullBtns.append(self.scaleBtn)
            toolTip = "Get the physical scale size for selected area light/s"
            self.scalePullBtn = elements.styledButton("", "arrowLeft",
                                                      self,
                                                      toolTip,
                                                      style=uic.BTN_TRANSPARENT_BG,
                                                      minWidth=uic.BTN_W_ICN_REG)
            self.pushPullBtns.append(self.scalePullBtn)
            # create area combo box  ----------------------------------------------------------------------
            toolTip = "Create area light at this postion/orientation\n" \
                      "World Center: Creates at world center\n" \
                      "Selected: Creates by matching the pos/orient of a selected obj"
            self.createAreaAtCombo = elements.ComboBoxRegular(self.properties.createFrom.label,
                                                              CREATE_OPTIONS_LIST,
                                                              parent=self,
                                                              toolTip=toolTip,
                                                              setIndex=self.properties.createFrom.value,
                                                              labelRatio=17,
                                                              boxRatio=30)
            self.toolsetWidget.linkProperty(self.createAreaAtCombo, "createFrom")

            toolTip = "Always apply changes instantly\n" \
                      "With instant apply off, changes will only be applied while\n" \
                      "pressing the apply/set buttons"
            self.areaInstantBx = elements.CheckBox(self.properties.instantApply.label,
                                                   parent=self,
                                                   checked=self.properties.instantApply.value,
                                                   toolTip=toolTip)
            self.toolsetWidget.linkProperty(self.areaInstantBx, "instantApply")
            self.areaInstantBx.hide()
            # apply no scale  ----------------------------------------------------------------------
            toolTip = "Applies the selected area light/s with the above settings\n" \
                      "Scale values are skipped.\nLights are not renamed"
            self.applyToSelectedNoScaleBtn = elements.styledButton("No Scale", "arrowRight",
                                                                   self,
                                                                   toolTip)
            self.applyToSelectedNoScaleBtn.hide()


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
        # main layout ------------------------------
        contentsLayout = elements.vBoxLayout(self,
                                             margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                             spacing=0)
        # grid layout start
        self.threeGridLayout = elements.GridLayout(columnMinWidth=(0, 180))
        # Name -------------------------------------
        suffixPadLayout = elements.hBoxLayout(margins=(12, 0, 0, 0), spacing=0)
        suffixPadLayout.addWidget(self.lightSuffixCheckbox)
        self.nameButtonsLayout = elements.hBoxLayout()
        self.nameButtonsLayout.addWidget(self.namePullBtn)
        self.nameButtonsLayout.addWidget(self.renameLightBtn)
        # Exposure -------------------------------------
        self.areaExposureOffsetLayout = elements.hBoxLayout(spacing=uic.SSML)
        self.areaExposureOffsetLayout.addWidget(self.scaleAreaNegExposureBtn, 1)
        self.areaExposureOffsetLayout.addWidget(self.scaleAreaPosExposureBtn, 1)
        self.exposureButtonsLayout = elements.hBoxLayout()
        self.exposureButtonsLayout.addWidget(self.exposurePullBtn)
        self.exposureButtonsLayout.addWidget(self.exposureBtn)
        # Shape -------------------------------------
        self.areaShapeOffsetBtnLayout = elements.hBoxLayout()
        self.areaShapeOffsetBtnLayout.addWidget(self.areaShapeOffsetBtnNeg)
        self.areaShapeOffsetBtnLayout.addWidget(self.areaShapeOffsetBtnPos)
        self.shapeButtonsLayout = elements.hBoxLayout()
        self.shapeButtonsLayout.addWidget(self.shapePullBtn)
        self.shapeButtonsLayout.addWidget(self.shapeBtn)
        # Color -------------------------------------
        self.areaColOffsetBtnLayout = elements.hBoxLayout()
        self.areaColOffsetBtnLayout.addWidget(self.areaColHueBtnNeg)
        self.areaColOffsetBtnLayout.addWidget(self.areaColHueBtnPos)
        self.areaColOffsetBtnLayout.addWidget(self.areaColSatBtnNeg)
        self.areaColOffsetBtnLayout.addWidget(self.areaColSatBtnPos)
        self.colorButtonsLayout = elements.hBoxLayout()
        self.colorButtonsLayout.addWidget(self.colorPullBtn)
        self.colorButtonsLayout.addWidget(self.colorApplyBtn)
        # apply to grid layout -------------------------------------
        self.threeGridLayout.addWidget(self.lightNameTxt, 0, 0)
        self.threeGridLayout.addLayout(suffixPadLayout, 0, 1)
        self.threeGridLayout.addLayout(self.nameButtonsLayout, 0, 2)

        self.threeGridLayout.addWidget(self.exposureTxt, 1, 0)
        self.threeGridLayout.addLayout(self.areaExposureOffsetLayout, 1, 1)
        self.threeGridLayout.addLayout(self.exposureButtonsLayout, 1, 2)

        self.threeGridLayout.addWidget(self.shapeCombo, 2, 0)
        self.threeGridLayout.addLayout(self.areaShapeOffsetBtnLayout, 2, 1)
        self.threeGridLayout.addLayout(self.shapeButtonsLayout, 2, 2)

        self.threeGridLayout.addWidget(self.colorLightBtn, 5, 0)
        self.threeGridLayout.addLayout(self.areaColOffsetBtnLayout, 5, 1)
        self.threeGridLayout.addLayout(self.colorButtonsLayout, 5, 2)

        self.threeGridLayout.setColumnStretch(0, 10)
        self.threeGridLayout.setColumnStretch(1, 1)
        self.threeGridLayout.setColumnStretch(2, 1)

        # main bottom buttons, adjust text and size
        self.dropAreaLightBtn.setText("")
        self.areaPlaceReflectionBtn.setText("")
        self.pullFromSelectedBtn.setText("")
        self.applyToSelectedBtn.setText("")

        # main bottom buttons layout
        self.createBtnLayout = elements.hBoxLayout(margins=(0, uic.REGPAD, 0, 0), spacing=uic.SSML)
        self.createBtnLayout.addWidget(self.createAreaLightBtn, 6)
        self.createBtnLayout.addWidget(self.dropAreaLightBtn, 1)
        self.createBtnLayout.addWidget(self.areaPlaceReflectionBtn, 1)
        self.createBtnLayout.addWidget(self.rendererIconMenu, 1)
        self.createBtnLayout.addWidget(self.pullFromSelectedBtn, 1)
        self.createBtnLayout.addWidget(self.applyToSelectedBtn, 1)

        # mainLayout
        contentsLayout.addLayout(self.threeGridLayout)
        contentsLayout.addLayout(self.createBtnLayout)

        contentsLayout.addStretch(1)


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
        # Main Layout -----------------------------------
        contentsLayout = elements.vBoxLayout(self,
                                             margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                             spacing=0)
        # create Main Grid layout -----------------------------------
        self.threeGridLayout = elements.GridLayout(columnMinWidth=(0, 180))
        # Name Area Light  Suffix Layout -----------------------------------
        suffixPadLayout = elements.hBoxLayout(margins=(12, 0, 0, 0), spacing=0)
        suffixPadLayout.addWidget(self.lightSuffixCheckbox)
        # Area Light Get Set Layout
        self.nameButtonsLayout = elements.hBoxLayout()
        self.nameButtonsLayout.addWidget(self.namePullBtn)
        self.nameButtonsLayout.addWidget(self.renameLightBtn)
        # Intensity Brighten Darken Layout -----------------------------------
        self.areaIntensityOffsetLayout = elements.hBoxLayout(spacing=uic.SSML)
        self.areaIntensityOffsetLayout.addWidget(self.scaleAreaNegIntensityBtn)
        self.areaIntensityOffsetLayout.addWidget(self.scaleAreaPosIntensityBtn)
        # Intensity Get Set Layout
        self.intensityButtonsLayout = elements.hBoxLayout()
        self.intensityButtonsLayout.addWidget(self.intensityPullBtn)
        self.intensityButtonsLayout.addWidget(self.intensityBtn)
        # Exposure Brighten Darken Layout -----------------------------------
        self.areaExposureOffsetLayout = elements.hBoxLayout(spacing=uic.SSML)
        self.areaExposureOffsetLayout.addWidget(self.scaleAreaNegExposureBtn, 1)
        self.areaExposureOffsetLayout.addWidget(self.scaleAreaPosExposureBtn, 1)
        # Exposure Get Set Layout
        self.exposureButtonsLayout = elements.hBoxLayout()
        self.exposureButtonsLayout.addWidget(self.exposurePullBtn)
        self.exposureButtonsLayout.addWidget(self.exposureBtn)
        # Shape Next Previous Layout -----------------------------------
        self.areaShapeOffsetBtnLayout = elements.hBoxLayout()
        self.areaShapeOffsetBtnLayout.addWidget(self.areaShapeOffsetBtnNeg)
        self.areaShapeOffsetBtnLayout.addWidget(self.areaShapeOffsetBtnPos)
        # Shape Get Set Layout
        self.shapeButtonsLayout = elements.hBoxLayout()
        self.shapeButtonsLayout.addWidget(self.shapePullBtn)
        self.shapeButtonsLayout.addWidget(self.shapeBtn)
        # Normalize Checkbox Layout -----------------------------------
        self.normalizeValueLayout = elements.hBoxLayout()
        self.normalizeValueLayout.addWidget(self.normalizeLabel)
        self.normalizeValueLayout.addWidget(self.normalizeBx)
        # Normalize On Off Layout
        self.normalizeOffsetBtnLayout = elements.hBoxLayout()
        self.normalizeOffsetBtnLayout.addWidget(self.normalizeOffsetBtnNeg)
        self.normalizeOffsetBtnLayout.addWidget(self.normalizeOffsetBtnPos)
        # Normalize Get Set Layout
        self.normalizeButtonsLayout = elements.hBoxLayout()
        self.normalizeButtonsLayout.addWidget(self.normalizePullBtn)
        self.normalizeButtonsLayout.addWidget(self.normalizeBtn)
        # Light Visibility Checkbox layout -----------------------------------
        self.lightVisValueLayout = elements.hBoxLayout()
        self.lightVisValueLayout.addWidget(self.lightVisLabel)
        self.lightVisValueLayout.addWidget(self.lightVisBx)
        # Light Visibility On Off layout
        self.areaVisOffsetBtnLayout = elements.hBoxLayout()
        self.areaVisOffsetBtnLayout.addWidget(self.areaVisOffsetBtnNeg)
        self.areaVisOffsetBtnLayout.addWidget(self.areaVisOffsetBtnPos)
        # Light Visibility Get Set layout
        self.lightVisButtonsLayout = elements.hBoxLayout()
        self.lightVisButtonsLayout.addWidget(self.lightVisPullBtn, 1)
        self.lightVisButtonsLayout.addWidget(self.lightVisBtn, 1)
        # Color cmds widget layout -----------------------------------
        self.areaColOffsetBtnLayout = elements.hBoxLayout(spacing=0)
        self.areaColOffsetBtnLayout.addWidget(self.areaColHueBtnNeg)
        self.areaColOffsetBtnLayout.addWidget(self.areaColHueBtnPos)
        self.areaColOffsetBtnLayout.addWidget(self.areaColSatBtnNeg)
        self.areaColOffsetBtnLayout.addWidget(self.areaColSatBtnPos)
        # Color get set layout
        self.colorButtonsLayout = elements.hBoxLayout()
        self.colorButtonsLayout.addWidget(self.colorPullBtn)
        self.colorButtonsLayout.addWidget(self.colorApplyBtn)
        # Temperature label edit layout -----------------------------------
        self.tempValueLayout = elements.hBoxLayout()
        self.tempValueLayout.addWidget(self.temperatureTxt)
        self.tempValueLayout.addWidget(self.tempOnOffBx)
        # Temperature warmer cooler layout
        self.areaTempOffsetBtnLayout = elements.hBoxLayout()
        self.areaTempOffsetBtnLayout.addWidget(self.areaTempOffsetBtnNeg)
        self.areaTempOffsetBtnLayout.addWidget(self.areaTempOffsetBtnPos)
        # Temperature get set layout
        self.tempButtonsLayout = elements.hBoxLayout()
        self.tempButtonsLayout.addWidget(self.tempPullBtn)
        self.tempButtonsLayout.addWidget(self.tempBtn)
        # Scale up down layout -----------------------------------
        self.areaScaleOffsetBtnLayout = elements.hBoxLayout()
        self.areaScaleOffsetBtnLayout.addWidget(self.areaScaleOffsetBtnNeg)
        self.areaScaleOffsetBtnLayout.addWidget(self.areaScaleOffsetBtnPos)
        # Scale set get layout
        self.scaleButtonsLayout = elements.hBoxLayout()
        self.scaleButtonsLayout.addWidget(self.scalePullBtn)
        self.scaleButtonsLayout.addWidget(self.scaleBtn)
        # Add widgets and layouts to the main grid layout
        self.threeGridLayout.addWidget(self.lightNameTxt, 0, 0)
        self.threeGridLayout.addLayout(suffixPadLayout, 0, 1)
        self.threeGridLayout.addLayout(self.nameButtonsLayout, 0, 2)

        self.threeGridLayout.addWidget(self.intensityTxt, 1, 0)
        self.threeGridLayout.addLayout(self.areaIntensityOffsetLayout, 1, 1)
        self.threeGridLayout.addLayout(self.intensityButtonsLayout, 1, 2)

        self.threeGridLayout.addWidget(self.exposureTxt, 2, 0)
        self.threeGridLayout.addLayout(self.areaExposureOffsetLayout, 2, 1)
        self.threeGridLayout.addLayout(self.exposureButtonsLayout, 2, 2)

        self.threeGridLayout.addWidget(self.shapeCombo, 3, 0)
        self.threeGridLayout.addLayout(self.areaShapeOffsetBtnLayout, 3, 1)
        self.threeGridLayout.addLayout(self.shapeButtonsLayout, 3, 2)

        self.threeGridLayout.addLayout(self.normalizeValueLayout, 4, 0)
        self.threeGridLayout.addLayout(self.normalizeOffsetBtnLayout, 4, 1)
        self.threeGridLayout.addLayout(self.normalizeButtonsLayout, 4, 2)

        self.threeGridLayout.addLayout(self.lightVisValueLayout, 5, 0)
        self.threeGridLayout.addLayout(self.areaVisOffsetBtnLayout, 5, 1)
        self.threeGridLayout.addLayout(self.lightVisButtonsLayout, 5, 2)

        self.threeGridLayout.addWidget(self.colorLightBtn, 6, 0)
        self.threeGridLayout.addLayout(self.areaColOffsetBtnLayout, 6, 1)
        self.threeGridLayout.addLayout(self.colorButtonsLayout, 6, 2)

        self.threeGridLayout.addLayout(self.tempValueLayout, 7, 0)
        self.threeGridLayout.addLayout(self.areaTempOffsetBtnLayout, 7, 1)
        self.threeGridLayout.addLayout(self.tempButtonsLayout, 7, 2)

        self.threeGridLayout.addWidget(self.scaleVEdit, 8, 0)
        self.threeGridLayout.addLayout(self.areaScaleOffsetBtnLayout, 8, 1)
        self.threeGridLayout.addLayout(self.scaleButtonsLayout, 8, 2)

        self.threeGridLayout.setColumnStretch(0, 10)
        self.threeGridLayout.setColumnStretch(1, 1)
        self.threeGridLayout.setColumnStretch(2, 1)

        # the create options layout
        self.createAtLayout = elements.hBoxLayout(margins=(0, uic.LRGPAD, 0, 0))
        self.createAtLayout.addWidget(self.createAreaAtCombo, 1)
        self.createAtLayout.addWidget(self.areaInstantBx, 4)
        self.createAtLayout.addWidget(self.rendererIconMenu, 1)

        # the main create button layout
        self.createBtnLayout = elements.hBoxLayout(margins=(0, uic.SSML, 0, 0), spacing=uic.SSML)
        self.createBtnLayout.addWidget(self.createAreaLightBtn, 1)
        self.createBtnLayout.addWidget(self.dropAreaLightBtn, 1)
        self.createBtnLayout.addWidget(self.areaPlaceReflectionBtn, 1)

        # bottom apply buttons layout (not used, hidden)
        self.applyBtnsLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=0)
        self.applyBtnsLayout.addWidget(self.pullFromSelectedBtn)
        self.applyBtnsLayout.addWidget(self.applyToSelectedNoScaleBtn)
        self.applyBtnsLayout.addWidget(self.applyToSelectedBtn)

        # add everything to the main layout
        contentsLayout.addLayout(self.threeGridLayout)
        contentsLayout.addLayout(self.createAtLayout)
        contentsLayout.addLayout(self.createBtnLayout)
        contentsLayout.addLayout(self.applyBtnsLayout)

        contentsLayout.addStretch(1)
