from Qt import QtWidgets

from maya.api import OpenMaya as om2

from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.maya.cmds.general import undodecorator

from zoo.preferences.core import preference
from zoo.preferences import preferencesconstants as pc

from zoo.libs.maya.cmds.shaders import toggleshaders
from zoo.libs.maya.cmds.renderer.rendererconstants import RENDERER_SUFFIX_DICT, ALL_RENDERER_NAMES

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

RENDERER_SUFFIXES = [RENDERER_SUFFIX_DICT[ALL_RENDERER_NAMES[0]],
                     RENDERER_SUFFIX_DICT[ALL_RENDERER_NAMES[1]],
                     RENDERER_SUFFIX_DICT[ALL_RENDERER_NAMES[2]],
                     RENDERER_SUFFIX_DICT[ALL_RENDERER_NAMES[3]]]


class ShaderSwapSuffix(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "shaderSwapSuffix"
    info = "Swaps shader assignments by suffix names."
    uiData = {"label": "Shader Swap",
              "icon": "shaderSwap",
              "tooltip": "Swaps shader assignments by suffix names.",
              "helpUrl": "https://create3dcharacters.com/maya-tool-shader-swap/",
              "defaultActionDoubleClick": False}

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        self.generalSettingsPrefsData = preference.findSetting(pc.RELATIVE_PREFS_FILE, None)  # renderer in general pref
        self.renderer = self.generalSettingsPrefsData[pc.PREFS_KEY_RENDERER]

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
        self.properties.quickSuffix1Combo.value = ALL_RENDERER_NAMES.index(self.renderer)  # set first suffix index
        self.updateSwapSuffixOne()  # update the suffix and properties
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
    # RENDERER - AND SEND/RECEIVE ALL TOOLSETS
    # ------------------

    def global_receiveRendererChange(self, renderer):
        """Receives from other GUIs, changes the renderer when it is changed"""
        self.renderer = renderer
        self.properties.quickSuffix1Combo.value = ALL_RENDERER_NAMES.index(renderer)  # set first suffix index
        self.updateSwapSuffixOne()  # update the suffix and properties

    # ------------------
    # UPDATE GUI
    # ------------------

    def updateSwapSuffixOne(self):
        """Updates the text for Suffix One on the combobox change"""
        index = self.properties.quickSuffix1Combo.value
        self.properties.suffix1Txt.value = RENDERER_SUFFIXES[index]
        self.updateFromProperties()

    def updateSwapSuffixTwo(self):
        """Updates the text for Suffix Two on the combobox change"""
        index = self.properties.quickSuffix2Combo.value
        self.properties.suffix2Txt.value = RENDERER_SUFFIXES[index]
        self.updateFromProperties()

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidgetmaya.undoDecorator
    def shaderSwap(self):
        """Swaps shader assignments based on the suffixes from the GUI
        """
        if self.properties.suffix2Txt.value == self.properties.suffix1Txt.value:
            om2.MGlobal.displayWarning("Shader suffix's are identical, suffix types must be unique.")
            return
        toggleshaders.toggleShaderAuto(shader1Suffix=self.properties.suffix1Txt.value,
                                       shader2Suffix=self.properties.suffix2Txt.value)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        # Main Button
        self.compactWidget.shaderSwapBtn.clicked.connect(self.shaderSwap)
        # Combo Update GUI
        self.compactWidget.quickSuffix1Combo.itemChanged.connect(self.updateSwapSuffixOne)
        self.compactWidget.quickSuffix2Combo.itemChanged.connect(self.updateSwapSuffixTwo)


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
        # Quick Suffix Combos ---------------------------------------
        toolTip = "Switch to quickly add the renderer's suffix in the textbox below"
        self.quickSuffix1Combo = elements.ComboBoxRegular(label="Quick Suffix",
                                                          items=ALL_RENDERER_NAMES,
                                                          setIndex=0,
                                                          toolTip=toolTip,
                                                          labelRatio=3,
                                                          boxRatio=5)
        self.quickSuffix2Combo = elements.ComboBoxRegular(label="Quick Suffix",
                                                          items=ALL_RENDERER_NAMES,
                                                          setIndex=3,
                                                          toolTip=toolTip,
                                                          labelRatio=3,
                                                          boxRatio=5)
        # Suffix Text Boxes ---------------------------------------
        toolTip = "The name of a suffix to swap, the order does not matter"
        self.suffix1Txt = elements.StringEdit(label="Suffix One",
                                              editText=RENDERER_SUFFIXES[0],
                                              toolTip=toolTip,
                                              labelRatio=3,
                                              editRatio=5)
        self.suffix2Txt = elements.StringEdit(label="Suffix Two",
                                              editText=RENDERER_SUFFIXES[3],
                                              toolTip=toolTip,
                                              labelRatio=3,
                                              editRatio=5)
        # Shader Swap Button ---------------------------------------
        tooltip = "Swap reassigns all shaders in the scene. Order does not matter. \n" \
                  "Any matching shaders will be swapped between suffix1 and suffix2 names \n" \
                  "Example Suffix One `ARN`, Suffix 2 `VP2`: \n" \
                  "    `gold_ARN` geo assignments will be swapped to the \n" \
                  "    `gold_VP2` shader if it exists"
        self.shaderSwapBtn = elements.styledButton("Shader Swap Toggle",
                                                   icon="transferShader",
                                                   toolTip=tooltip,
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
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(parent, margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Combo Row ---------------------------------------
        comboLayout = elements.hBoxLayout(parent, spacing=uic.SREG)
        comboLayout.addWidget(self.quickSuffix1Combo)
        comboLayout.addWidget(self.quickSuffix2Combo)
        # Suffix Row ---------------------------------------
        suffixLayout = elements.hBoxLayout(parent, spacing=uic.SREG)
        suffixLayout.addWidget(self.suffix1Txt)
        suffixLayout.addWidget(self.suffix2Txt)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(comboLayout)
        mainLayout.addLayout(suffixLayout)
        mainLayout.addWidget(self.shaderSwapBtn)
