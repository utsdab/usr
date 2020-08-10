from functools import partial

import maya.api.OpenMaya as om2

from Qt import QtCore, QtWidgets

from zoo.preferences.core import preference
from zoo.apps.light_suite import lightconstants as lc
from zoo.preferences import preferencesconstants as pc

from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.apps.toolsetsui import toolsetui
from zoo.libs.maya.cmds.general import undodecorator
from zoo.libs.maya.cmds.lighting import renderertransferlights
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import zlogging

logger = zlogging.getLogger(__name__)

DFLT_RNDR_MODES = [("arnold", "Arnold"), ("redshift", "Redshift"), ("renderman", "Renderman")]
UI_MODE_COMPACT = 0
UI_MODE_MEDIUM = 1
UI_MODE_ADVANCED = 2

EXPOSURE = 1
INTENSITY = 0

INTENSITY_OPTIONS = ["Selected Lights", "All Lights"]
INTENSITY_SELECTED_LIGHTS = 0
INTENSITY_ALL_LIGHTS = 1

SCALE_OPTIONS = ["Selected Lights", "All Wrld Center", "All Area Lights"]
SCALE_SELECTED_LIGHTS = 0
SCALE_ALL_WORLD = 1
SCALE_ALL_AREA = 2

ROTATE_OPTIONS = ["Lights Group", "IBL Light"]
ROTATE_LIGHTS_GROUP = 0
ROTATE_IBL_LIGHT = 1


class EditLights(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "editLights"
    uiData = {"label": "Edit Lights",
              "icon": "bulbbright1",
              "tooltip": "Edit lights or groups of lights",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-edit-lights/"
              }

    # ------------------------------------
    # START UP
    # ------------------------------------

    def preContentSetup(self):
        """First code to run"""
        self.toolsetWidget = self  # needed for callback decorators
        # Light Suite Pref Object PREFS_DATA stores and saves all the .prefs json data
        self.lightPresetsPrefsData = preference.findSetting(lc.RELATIVE_PREFS_FILE, None)
        self.generalSettingsPrefsData = preference.findSetting(pc.RELATIVE_PREFS_FILE, None)  # renderer in general pref
        self.properties.renderer.value = self.generalSettingsPrefsData[pc.PREFS_KEY_RENDERER]

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]

    def initCompactWidget(self):
        parent = QtWidgets.QWidget(parent=self)
        self.parentWgt = parent
        self.compactWidget = CompactLayout(parent=parent, properties=self.properties, toolsetWidget=self)
        return self.compactWidget

    def initAdvancedWidget(self):
        pass

    def postContentSetup(self):
        self.ignoreInstantApply = False  # for instant apply directional lights and switching ui modes
        self.uiConnections()

    # ------------------------------------
    # PROPERTIES
    # ------------------------------------

    def initializeProperties(self):
        return [{"name": "calculateCombo", "label": "Calculate", "value": 0},
                {"name": "applyAsCombo", "label": "Apply As", "value": 1},
                {"name": "intensityCombo", "label": "Intensity", "value": 1},
                {"name": "intensityPercent", "label": "%", "value": 10.0},
                {"name": "scaleCombo", "label": "Scale", "value": 1},
                {"name": "scalePercent", "label": "%", "value": 5.0},
                {"name": "rotateCombo", "label": "Rotate", "value": 1},
                {"name": "rotateDegrees", "label": "Deg", "value": 15.0},
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
        super(EditLights, self).updateFromProperties()
        # fix incorrect string entries and convert to floats
        rememberInstantApply = self.ignoreInstantApply
        self.blockCallbacks(True)
        self.compactWidget.ignoreInstantApply = True
        self.compactWidget.intensityEdit.setValue(self.properties.intensityPercent.value)
        self.compactWidget.scaleEdit.setValue(self.properties.scalePercent.value)
        self.compactWidget.rotateEdit.setValue(self.properties.rotateDegrees.value)
        self.ignoreInstantApply = rememberInstantApply
        self.blockCallbacks(False)

    # ------------------------------------
    # RENDERER - AND SEND/RECEIVE ALL TOOL SETS
    # ------------------------------------

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
    # APPLY OFFSETS
    # ------------------------------------

    def offsetMultiplier(self):
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

    @toolsetwidgetmaya.undoDecorator
    def applyIntensity(self, neg=False):
        """Applies the intensity buttons, if neg=True apply the inverse

        Two modes:

            0: Selected Lights: increase/decrease the intensity of all selected lights
            1: All Lights: increase/decrease the intensity of all lights in the scene

        :param neg: if neg=True apply the inverse
        :type neg: bool
        """
        multiplier, reset = self.offsetMultiplier()
        rendererNiceName = self.properties.renderer.value
        intensityPercent = self.properties.intensityPercent.value * multiplier
        if not intensityPercent:  # bail if scale by zero
            om2.MGlobal.displayWarning("Cannot Scale By Zero")
        if neg:  # make the scale percent a negative value
            intensityPercent *= -1
        applyPure = True
        calcExposure = False
        applyExposure = False
        applyTypeCombo = self.properties.intensityCombo.value
        if self.properties.calculateCombo.value == EXPOSURE:  # 1 combo index
            calcExposure = True
        if self.properties.applyAsCombo.value == EXPOSURE:  # 1 combo index
            applyExposure = True
        if applyTypeCombo == INTENSITY_SELECTED_LIGHTS:  # 0 combo index
            renderertransferlights.scaleAllLightsIntensitySelected(intensityPercent, rendererNiceName,
                                                                   calcExposure=calcExposure,
                                                                   applyExposure=applyExposure,
                                                                   applyPure=applyPure)
        elif applyTypeCombo == INTENSITY_ALL_LIGHTS:  # 1 combo index
            renderertransferlights.scaleAllLightIntensitiesScene(intensityPercent, rendererNiceName,
                                                                 calcExposure=calcExposure,
                                                                 applyExposure=applyExposure,
                                                                 applyPure=applyPure)

    @toolsetwidgetmaya.undoDecorator
    def applyScale(self, neg=False):
        """Applies the scale buttons, if neg=True apply the inverse

        Three modes:

            0: Selected Lights, scales from each center
            1: All Wrl Center, scales all lights from the light group
            2: All area Lights, scales all area lights from each light pivot

        :param neg: if neg=True apply the inverse
        :type neg: bool
        """
        multiplier, reset = self.offsetMultiplier()
        scalePercentage = self.properties.scalePercent.value * multiplier
        scaleType = self.properties.scaleCombo.value
        rendererNiceName = self.properties.renderer.value
        if neg:  # make the scale percent a negative value
            scalePercentage *= -1
        if scaleType == SCALE_SELECTED_LIGHTS:  # 0 index
            renderertransferlights.scaleLightSizeSelected(scalePercentage)
        elif scaleType == SCALE_ALL_WORLD:  # 1 index
            renderertransferlights.scaleAllLightsInScene(scalePercentage,
                                                         rendererNiceName,
                                                         scalePivot=(0.0, 0.0, 0.0),
                                                         ignoreNormalization=False,
                                                         ignoreIbl=False,
                                                         message=True)
        elif scaleType == SCALE_ALL_AREA:  # 2 index
            renderertransferlights.scaleAreaLightSizeAll(scalePercentage, rendererNiceName)

    @toolsetwidgetmaya.undoDecorator
    def applyRotation(self, rotOffset=15.0):
        """Rotates the lights y angle by the rotOffset amount.

        Two modes:

            0: IBL Skydome only
            1: The light grp only eg "ArnoldLights_grp" or "RedshiftLights_grp"

        :param rotOffset: the y angle offset to be rotated with each button click
        :type rotOffset: float
        """
        multiplier, reset = self.offsetMultiplier()
        rendererNiceName = self.properties.renderer.value
        rotType = self.properties.rotateCombo.value
        if multiplier > 1.0:
            multiplier = 2.0  # fast mode too fast, slow it down.
        rotOffset *= multiplier
        if rotType == ROTATE_LIGHTS_GROUP:  # 0 index
            renderertransferlights.rotLightGrp(rendererNiceName, rotOffset)
        elif rotType == ROTATE_IBL_LIGHT:  # 1 index
            renderertransferlights.rotIblLightSelectedScene(rendererNiceName, rotOffset)

    # ------------------------------------
    # CONNECTIONS
    # ------------------------------------

    def uiConnections(self):
        """Runs the add suffix command
        """
        self.compactWidget.darkenBtn.clicked.connect(partial(self.applyIntensity, neg=True))
        self.compactWidget.brightenBtn.clicked.connect(self.applyIntensity)
        self.compactWidget.scaleDownBtn.clicked.connect(partial(self.applyScale, neg=True))
        self.compactWidget.scaleUpBtn.clicked.connect(self.applyScale)
        self.compactWidget.rotNegBtn.clicked.connect(partial(self.applyRotation, rotOffset=-15.0))
        self.compactWidget.rotPosBtn.clicked.connect(self.applyRotation)
        # change renderer
        self.compactWidget.rendererLoaded.actionTriggered.connect(self.global_changeRenderer)


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
        if uiMode == UI_MODE_ADVANCED:
            self.parentWidget.setObjectName("createIBLLightsAdv")
        elif uiMode == UI_MODE_COMPACT:
            self.parentWidget.setObjectName("createIBLLightsCmpct")
        # Calculate, Apply As and Change Renderer --------------------------------------
        toolTip = "Multiply the area lights by pure 'intensity' or 'exposure'. \n" \
                  "Intensity is always recommended"
        self.calculateComboBx = elements.ComboBoxRegular(self.properties.calculateCombo.label,
                                                         items=["Intensity", "Exposure"],
                                                         parent=parent,
                                                         labelRatio=2,
                                                         boxRatio=3,
                                                         toolTip=toolTip,
                                                         setIndex=self.properties.calculateCombo.value)
        self.toolsetWidget.linkProperty(self.calculateComboBx, "calculateCombo")
        toolTip = "Apply the area light's brightness as\n" \
                  "1. Intensity only, exposure is set to 1.0\n" \
                  "2. Exposure only, intensity is set to 0.0"
        self.applyPureComboBx = elements.ComboBoxRegular(self.properties.applyAsCombo.label,
                                                         items=["Intensity", "Exposure"],
                                                         parent=parent,
                                                         labelRatio=2,
                                                         boxRatio=3,
                                                         toolTip=toolTip,
                                                         setIndex=self.properties.applyAsCombo.value)
        self.toolsetWidget.linkProperty(self.applyPureComboBx, "applyAsCombo")
        toolTip = "Set the default renderer"
        self.rendererLoaded = elements.iconMenuButtonCombo(DFLT_RNDR_MODES,
                                                           self.properties.renderer.value,
                                                           toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.rendererLoaded, "renderer")
        # Intensity --------------------------------------
        toolTip = "Affects the intensity (brightness) of...\n" \
                  "1. Selected lights\n" \
                  "2. All lights in scene"
        self.intensityComboBx = elements.ComboBoxRegular(self.properties.intensityCombo.label,
                                                         items=["Selected Lights", "All Lights"],
                                                         parent=parent,
                                                         labelRatio=4,
                                                         boxRatio=7,
                                                         toolTip=toolTip,
                                                         setIndex=self.properties.intensityCombo.value)
        self.toolsetWidget.linkProperty(self.intensityComboBx, "intensityCombo")

        toolTip = "Brighten/darken lights by this percentage\n(Buttons: shift faster, ctrl slower, alt reset)"
        self.intensityEdit = elements.FloatEdit(self.properties.intensityPercent.label,
                                                self.properties.intensityPercent.value,
                                                parent=parent,
                                                editWidth=None,
                                                labelRatio=1,
                                                editRatio=1,
                                                toolTip=toolTip,
                                                rounding=1)
        self.toolsetWidget.linkProperty(self.intensityEdit, "intensityPercent")

        toolTip = "Darken lights by this percentage\n(Buttons: shift faster, ctrl slower, alt reset)"
        self.darkenBtn = elements.styledButton("",
                                               "darkenBulb",
                                               parent,
                                               toolTip=toolTip,
                                               style=uic.BTN_TRANSPARENT_BG,
                                               minWidth=uic.BTN_W_ICN_LRG)

        toolTip = "Brighten lights by this percentage\n(Buttons: shift faster, ctrl slower, alt reset)"
        self.brightenBtn = elements.styledButton("",
                                                 "brightenBulb",
                                                 parent,
                                                 toolTip=toolTip,
                                                 style=uic.BTN_TRANSPARENT_BG,
                                                 minWidth=uic.BTN_W_ICN_LRG)
        # Scale --------------------------------------
        toolTip = "Affect scale physical light size...\n" \
                  "1. Center of each selected light\n" \
                  "2. All lights from the world center (Light Grp)\n" \
                  "3. All lights for each light center"
        items = ["Selected Lights", "All Wrld Center", "All Area Lights"]
        self.scaleComboBx = elements.ComboBoxRegular(self.properties.scaleCombo.label,
                                                     items=items,
                                                     parent=parent,
                                                     labelRatio=4,
                                                     boxRatio=7,
                                                     toolTip=toolTip,
                                                     setIndex=self.properties.scaleCombo.value)
        self.toolsetWidget.linkProperty(self.scaleComboBx, "scaleCombo")

        toolTip = "Scale physical size by percentage\n(Buttons: shift faster, ctrl slower, alt Reset)"
        self.scaleEdit = elements.FloatEdit(self.properties.scalePercent.label,
                                            self.properties.scalePercent.value,
                                            parent=parent,
                                            editWidth=None,
                                            labelRatio=1,
                                            editRatio=1,
                                            rounding=1,
                                            toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.scaleEdit, "scalePercent")
        toolTip = "Scale smaller, physical light size\n(Buttons: shift faster, ctrl slower, alt Reset)"
        self.scaleDownBtn = elements.styledButton("",
                                                  "scaleDown",
                                                  parent,
                                                  toolTip=toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=uic.BTN_W_ICN_LRG)
        toolTip = "Scale larger, physical light size\n(Buttons: shift faster, ctrl slower, alt Reset)"
        self.scaleUpBtn = elements.styledButton("",
                                                "scaleUp",
                                                parent,
                                                toolTip=toolTip,
                                                style=uic.BTN_TRANSPARENT_BG,
                                                minWidth=uic.BTN_W_ICN_LRG)
        # Rotate --------------------------------------
        toolTip = "Affect the rotation of lights...\n" \
                  "1. Rotate the light grp\n" \
                  "2. The HDR IBL skydome light"
        self.rotateComboBx = elements.ComboBoxRegular(self.properties.rotateCombo.label,
                                                      items=("Lights Group", "IBL Light"),
                                                      parent=parent,
                                                      labelRatio=4,
                                                      boxRatio=7,
                                                      toolTip=toolTip,
                                                      setIndex=self.properties.rotateCombo.value)
        self.toolsetWidget.linkProperty(self.rotateComboBx, "rotateCombo")
        toolTip = "Rotate light/s in degrees\n(Buttons: shift faster, ctrl slower, alt reset)"
        self.rotateEdit = elements.FloatEdit(self.properties.rotateDegrees.label,
                                             self.properties.rotateDegrees.value,
                                             parent=parent,
                                             editWidth=None,
                                             labelRatio=1,
                                             editRatio=1,
                                             rounding=1,
                                             toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.rotateEdit, "rotateDegrees")
        toolTip = "Rotate light/s\n(Buttons: shift faster, ctrl slower, alt reset)"
        self.rotNegBtn = elements.styledButton("",
                                               "arrowRotLeft",
                                               parent,
                                               toolTip=toolTip,
                                               style=uic.BTN_TRANSPARENT_BG,
                                               minWidth=uic.BTN_W_ICN_LRG)
        self.rotPosBtn = elements.styledButton("",
                                               "arrowRotRight",
                                               parent,
                                               toolTip=toolTip,
                                               style=uic.BTN_TRANSPARENT_BG,
                                               minWidth=uic.BTN_W_ICN_LRG)


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
        # Main Layout -----------------------------------
        mainLayout = elements.vBoxLayout(self,
                                         margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=0)
        # Apply As -----------------------------------
        applyAsLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.REGPAD),
                                            spacing=uic.SLRG)
        applyAsLayout.addWidget(self.calculateComboBx, 6)
        applyAsLayout.addWidget(self.applyPureComboBx, 6)
        applyAsLayout.addWidget(self.rendererLoaded, 1)
        # Grid: Intensity, Scale, Rotation Layout -----------------------------------
        editGridLayout = elements.GridLayout(margins=(0, 0, 0, 0),
                                             spacing=uic.SREG,
                                             columnMinWidth=(0, 180))

        editGridLayout.addWidget(self.intensityComboBx, 0, 0)
        editGridLayout.addWidget(self.intensityEdit, 0, 1)
        editGridLayout.addWidget(self.darkenBtn, 0, 2)
        editGridLayout.addWidget(self.brightenBtn, 0, 3)

        editGridLayout.addWidget(self.scaleComboBx, 1, 0)
        editGridLayout.addWidget(self.scaleEdit, 1, 1)
        editGridLayout.addWidget(self.scaleDownBtn, 1, 2)
        editGridLayout.addWidget(self.scaleUpBtn, 1, 3)

        editGridLayout.addWidget(self.rotateComboBx, 2, 0)
        editGridLayout.addWidget(self.rotateEdit, 2, 1)
        editGridLayout.addWidget(self.rotNegBtn, 2, 2)
        editGridLayout.addWidget(self.rotPosBtn, 2, 3)
        # Add To Main Layout -----------------------------------
        mainLayout.addLayout(applyAsLayout)
        mainLayout.addLayout(editGridLayout)
        mainLayout.addStretch(1)


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
        pass
