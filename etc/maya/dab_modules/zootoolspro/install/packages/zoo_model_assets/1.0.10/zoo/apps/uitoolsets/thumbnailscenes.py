from Qt import QtWidgets

import maya.api.OpenMaya as om2
from functools import partial

from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.apps.toolsetsui import toolsetui

from zoo.preferences.core import preference
from zoo.preferences import preferencesconstants as pc

from zoo.libs.maya.cmds.assets import defaultassets
from zoo.libs.maya.cmds.filemanage import saveexportimport
from zoo.libs.maya.cmds.renderer import rendererload

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1
DFLT_RNDR_MODES = [("arnold", "Arnold"), ("redshift", "Redshift"), ("renderman", "Renderman")]


class ThumbnailScenes(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "thumbnailScenes"
    info = "Builds default thumbnail scenes for browsers."
    uiData = {"label": "Thumbnail Scenes",
              "icon": "addThumbnail",
              "tooltip": "Template file for building new GUIs.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-thumbnail-scenes/"
              }

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
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
        # TODO temp fix for the image buttons
        self.updateTree(True)  # temp fix

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

    # ------------------
    # CHECK NEW SCENE
    # ------------------

    def saveCurrentScene(self):
        """Checks if the file has already been saved. Returns "save", "discard" or "cancel".

        If not saved opens "save", "discard" or "cancel" window.  Returns the button pressed if "discard" or "cancel"

        If "save" is clicked it will try to save the current file, if cancelled will return "cancel"

        :return buttonClicked: The button clicked returned as a lower case string "save", "discard" or "cancel"
        :rtype buttonClicked: str
        """
        # TODO move this into elements under maya cmds
        sceneModified = saveexportimport.fileModified()
        if not sceneModified:  # Has been saved already so continue
            saveexportimport.createNewScene()
            return "save"
        # Open dialog window with Save/Discard/Cancel buttons
        fullMessage = "Creating a new scene, save the current file?"
        buttonPressed = elements.MessageBox_save(windowName="Save File", parent=None, message=fullMessage)
        if buttonPressed == "save":
            if saveexportimport.saveAsDialogMaMb():  # file saved
                return "save"
            else:
                return "cancel"
        return buttonPressed

    # ------------------
    # LOGIC: HELPER LOGIC
    # ------------------

    def newSceneChecks(self, checkRenderer=True):
        if checkRenderer:
            renderer = self.properties.rendererIconMenu.value
            if not rendererload.getRendererIsLoaded(renderer):  # the renderer is not loaded open window
                if not elements.checkRenderLoaded(renderer):
                    return False
        # Create new scene
        if not self.createNewScene():
            om2.MGlobal.displayInfo("New scene cancelled.")
            return False
        return True

    def createNewScene(self):
        """Creates a new scene with tests from newSceneCheckBox.value and self.saveCurrentScene()

        :return newSceneCreated: True new scene has been created, False has not been created
        :rtype newSceneCreated: bool
        """
        if not self.properties.newSceneCheckBox.value:  # If new scene not checked import into current scene
            return True
        buttonPressed = self.saveCurrentScene()
        if buttonPressed == "cancel":
            return False
        # File has been saved, free to build a new scene
        saveexportimport.createNewScene()  # Create new scene
        return True

    # ------------------
    # LOGIC: BUILD SCENES
    # ------------------

    def buildLightPresetScene(self):
        """Builds a light preset scene and sets render globals depending on the renderer

        Will create a new scene and save the existing scene depending the settings
        """
        if not self.newSceneChecks():
            return
        # checks passed import
        defaultassets.buildDefaultLightSceneCyc(renderer=self.properties.rendererIconMenu.value)

    def buildShaderPresetScene(self):
        """Builds a shader preset scene and sets render globals depending on the renderer

        Will create a new scene and save the existing scene depending the settings
        """
        if not self.newSceneChecks():
            return
        # Checks passed so import
        defaultassets.buildDefaultShaderSceneCyc(renderer=self.properties.rendererIconMenu.value)

    def buildAssetsScene(self, bot=False):
        """Builds an empty assets scene and sets render globals depending on the renderer

        Will create a new scene and save the existing scene depending the settings
        """
        if not self.newSceneChecks():
            return
        # Checks passed so import
        defaultassets.buildDefaultAssetsSceneCyc(renderer=self.properties.rendererIconMenu.value, buildBot=bot)

    def buildHdrScene(self):
        """Builds an empty HDR Skydome scene and sets render globals depending on the renderer

        Will create a new scene and save the existing scene depending the settings
        """
        if not self.newSceneChecks():
            return
        # Checks passed so import
        defaultassets.buildDefaultHDRIScene(renderer=self.properties.rendererIconMenu.value)

    def buildControlsScene(self):
        """Builds an empty controls scene and sets render globals depending on the renderer

        Will create a new scene and save the existing scene depending the settings
        """
        if not self.newSceneChecks(checkRenderer=False):
            return
        # Checks passed so import
        defaultassets.buildDefaultControlsScene()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for uiInstance in self.uiInstanceList:
            uiInstance.lightPresetsSceneBtn.clicked.connect(self.buildLightPresetScene)
            uiInstance.shaderPresetsSceneBtn.clicked.connect(self.buildShaderPresetScene)
            uiInstance.modelAssetsSceneEmptyBtn.clicked.connect(self.buildAssetsScene)
            uiInstance.modelAssetsSceneBotBtn.clicked.connect(partial(self.buildAssetsScene, bot=True))
            uiInstance.hdriSceneBtn.clicked.connect(self.buildHdrScene)
            uiInstance.controlShapesSceneBtn.clicked.connect(self.buildControlsScene)
            # Change Renderer
            uiInstance.rendererIconMenu.actionTriggered.connect(self.global_changeRenderer)


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
        # Light Presets Button ---------------------------------------
        tooltip = "Creates the default scene for light presets with Shader Bot. \n" \
                  "After building use the Model Assets browser for other models."
        self.lightPresetsSceneBtn = elements.ImageButton(text="Light Presets",
                                                         image="lightPresetsScene",
                                                         icon="lightstudio",
                                                         toolTip=tooltip)
        # HDR Skydomes ---------------------------------------
        tooltip = "Creates the default scene for HDR Skydomes. \n" \
                  "After building add your skydome, spin it to see the \n" \
                  "main light source and render."
        self.hdriSceneBtn = elements.ImageButton(text="HDR Skydomes",
                                                 image="hdriSkydomeScene",
                                                 icon="sky",
                                                 toolTip=tooltip)
        # Model Assets Empty Button ---------------------------------------
        tooltip = "Creates the default scene for Model Assets. \n" \
                  "After building add your asset to the scene and render."
        self.modelAssetsSceneEmptyBtn = elements.ImageButton(text="Assets Empty",
                                                             image="modelAssetsSceneEmpty",
                                                             icon="packageAssets",
                                                             toolTip=tooltip)
        # Model Assets Bot Button ---------------------------------------
        tooltip = "Creates the default scene for Model Assets. \n" \
                  "After building add your asset to the scene and render."
        self.modelAssetsSceneBotBtn = elements.ImageButton(text="Model Assets",
                                                           image="modelAssetsSceneBot",
                                                           icon="packageAssets",
                                                           toolTip=tooltip)
        # Shader Presets Button ---------------------------------------
        tooltip = "Creates the default scene for light presets with Shader Bot. \n" \
                  "After building use the Model Assets browser for other models."
        self.shaderPresetsSceneBtn = elements.ImageButton(text="Shader Presets",
                                                          image="shaderPresetsScene",
                                                          icon="shaderPresets",
                                                          toolTip=tooltip)
        # Control Shapes Button ---------------------------------------
        tooltip = "Creates the default scene for Control Shapes. \n" \
                  "After building either screenshot or playblast a frame."
        self.controlShapesSceneBtn = elements.ImageButton(text="Control Creator",
                                                          image="controlCreatorScene",
                                                          icon="starControl",
                                                          toolTip=tooltip)
        # New Scene Check Box -----------------------------------
        toolTip = "If on will create a new scene (recommended)."
        self.newSceneCheckBox = elements.CheckBox(label="Create New Scene", checked=True, toolTip=toolTip)
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
        mainLayout = elements.vBoxLayout(parent, margins=(uic.WINSIDEPAD, uic.SMLPAD, uic.WINSIDEPAD-1, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Renderer Layout ---------------------------------------
        rendererLayout = elements.hBoxLayout()
        rendererLayout.addItem(elements.Spacer(width=75, height=3))
        rendererLayout.addWidget(self.rendererLabel, 6)
        rendererLayout.addWidget(self.rendererIconMenu, 1)
        # Btn grid Layout ---------------------------------------
        btnGridLayout = elements.GridLayout(margins=(0, uic.SREG, 0, 0), spacing=0)
        btnGridLayout.addWidget(self.shaderPresetsSceneBtn, 0, 0)
        btnGridLayout.addWidget(self.lightPresetsSceneBtn, 0, 1)
        btnGridLayout.addWidget(self.modelAssetsSceneBotBtn, 0, 2)
        btnGridLayout.addWidget(self.hdriSceneBtn, 1, 0)
        btnGridLayout.addWidget(self.controlShapesSceneBtn, 1, 1)
        btnGridLayout.addWidget(self.modelAssetsSceneEmptyBtn, 1, 2)
        btnGridLayout.setColumnStretch(0, 1)
        btnGridLayout.setColumnStretch(1, 1)
        btnGridLayout.setColumnStretch(2, 1)
        # New Scene Renderer Layout ---------------------------------------
        newSceneRendererLayout = elements.hBoxLayout(margins=(0, uic.SREG, 0, 0))
        newSceneRendererLayout.addWidget(self.newSceneCheckBox, 1)
        newSceneRendererLayout.addLayout(rendererLayout, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(btnGridLayout)
        mainLayout.addLayout(newSceneRendererLayout)
