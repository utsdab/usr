from Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.preferences.core import preference
from zoo.preferences import preferencesconstants as pc

from zoo.libs.maya.cmds.general import undodecorator

from zoo.libs.maya.cmds.shaders import shadermultirenderer as shdmult
from zoo.libs.maya.cmds.renderer import rendererload
from zoo.libs.maya.cmds.renderer.rendererconstants import DFLT_RNDR_MODES

from zoo.apps.toolsetsui import toolsetui

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class CreateMattesAovs(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "createMattesAovs"
    info = "Easily create shader AOV mattes."
    uiData = {"label": "Create Mattes AOVs",
              "icon": "rgb",
              "tooltip": "Easily create shader AOV mattes.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-create-mattes-aovs/"
              }

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        self.toolsetWidget = self  # needed for callback decorators and resizer
        self.generalSettingsPrefsData = preference.findSetting(pc.RELATIVE_PREFS_FILE, None)  # renderer in general pref
        self.properties.rendererIconMenu.value = self.generalSettingsPrefsData[pc.PREFS_KEY_RENDERER]

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        parent = QtWidgets.QWidget(parent=self)
        self.compactWidget = GuiCompact(parent=parent, properties=self.properties, toolsetWidget=self)
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
        """
        return self.widgets()[self.displayIndex()].children()[0]

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
        return [
            {"name": "rendererIconMenu", "label": "", "value": "Arnold"}]  # will be changed to prefs immediately

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

    def comboColorUpdate(self):
        """On combobox change update the color button to red, green, blue or black
        """
        colorList = [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (0.0, 0.0, 0.0)]  # r, g, b, black
        self.properties.colorSwatchBtn.value = colorList[self.properties.colorsCombo.value]
        self.updateFromProperties()

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidgetmaya.undoDecorator
    def createMatte(self):
        """Create Matte
        """
        renderer = self.properties.rendererIconMenu.value
        if not rendererload.getRendererIsLoaded(renderer):  # the renderer is not loaded open window
            if not elements.checkRenderLoaded(renderer):
                return
        shdmult.createMatteAOVRenderer(renderer,
                                       self.properties.colorSwatchBtn.value,
                                       self.properties.imageNoInt.value)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        self.compactWidget.assignMatteBtn.clicked.connect(self.createMatte)
        # Change Renderer
        self.compactWidget.rendererIconMenu.actionTriggered.connect(self.global_changeRenderer)
        # Change Combo Box update color
        self.compactWidget.colorsCombo.itemChanged.connect(self.comboColorUpdate)


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
        # Image Number ---------------------------------------
        toolTip = "The image number, starts at zero. \n" \
                  "Each image can hold up to three colors. \n" \
                  "Red, Green and Blue"
        self.imageNoInt = elements.IntEdit(label="Image No.",
                                              editText="0",
                                              toolTip=toolTip)
        # Color Combo ---------------------------------------
        toolTip = "The color to assign \n" \
                  "This color will be the matte color \n" \
                  "Black will disable the current shader"
        colors = ["Red", "Green", "Blue", "Black"]
        self.colorsCombo = elements.ComboBoxRegular(label="Color",
                                                    items=colors,
                                                    toolTip=toolTip,
                                                    labelRatio=2,
                                                    boxRatio=5)
        # Color Swatch ---------------------------------------
        self.colorSwatchBtn = elements.MayaColorBtn(color=(1.0, 0.0, 0.0), toolTip=toolTip)
        # Assign Matte Button ---------------------------------------
        tooltip = "Select a shader, shading group, or object. \n" \
                  "The related shader will be rendered as a matte color AOV. \n" \
                  "Red, Green or Blue.  Each image can contain three mattes. \n" \
                  "Note: In Renderman the geometry needs to be manually setup. \n" \
                  "See the help for more information. Cryptomattes supersede this tool"
        self.assignMatteBtn = elements.styledButton("Assign Matte",
                                                    icon="transferShader",
                                                    toolTip=tooltip,
                                                    style=uic.BTN_DEFAULT)
        # Renderer Button --------------------------------------
        toolTip = "Change the renderer to Arnold, Redshift or Renderman"
        self.rendererLabel = elements.Label(text="Renderer", toolTip=toolTip)
        self.rendererIconMenu = elements.iconMenuButtonCombo(DFLT_RNDR_MODES,
                                                             properties.rendererIconMenu.value,
                                                             toolTip=toolTip)


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
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(parent,
                                         margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Top Row ---------------------------------------
        topRowLayout = elements.hBoxLayout(parent, spacing=uic.SREG)
        topRowLayout.addWidget(self.imageNoInt, 3)
        topRowLayout.addSpacerItem(elements.Spacer(width=15, height=1))
        topRowLayout.addWidget(self.colorsCombo, 3)
        topRowLayout.addWidget(self.colorSwatchBtn, 1)
        # Button Layout ---------------------------------------
        buttonLayout = elements.hBoxLayout(parent, spacing=uic.SREG)
        buttonLayout.addWidget(self.assignMatteBtn, 9)
        buttonLayout.addWidget(self.rendererIconMenu, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(topRowLayout)
        mainLayout.addLayout(buttonLayout)
