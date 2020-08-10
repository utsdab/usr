from Qt import QtWidgets

from maya.api import OpenMaya as om2

from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.libs.maya.cmds.objutils import uvtransfer
from zoo.libs.maya.cmds.skin import bindskin
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1
UV_SAMPLE_SPACE = ["World", "Local", "Component", "Topology"]
SHADER_SAMPLE_SPACE = ["World", "Local", "Topology"]
SHADER_SEARCH_METHOD = ["Normal", "Point"]


class TransferUvs(toolsetwidgetmaya.ToolsetWidgetMaya):
    """Transfers UVs and shaders between meshes.  Select one mesh (source) and then others (targets) and run.
    Most code is based on Maya's cmds.transferAttributes() and cmds.transferShadingSets().
    See from zoo.libs.maya.cmds.objutils.uvtransfer for more info

    Based on a tool by Jason Dobra https://vimeo.com/user46798528
    """
    id = "transferUvs"
    uiData = {"label": "Transfer UVs Shaders",
              "icon": "transferUVs",
              "tooltip": "Transfer UVs -  Based on a tool by Jason Dobra",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-transfer-uvs-shaders/"
              }

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run"""
        pass

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget(), self.initAdvancedWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        parent = QtWidgets.QWidget(parent=self)
        self.compactWidget = GuiCompact(parent=parent, properties=self.properties, toolsetWidget=self)
        return parent

    def initAdvancedWidget(self):
        """Builds the Advanced GUI (self.advancedWidget) """
        parent = QtWidgets.QWidget(parent=self)
        self.advancedWidget = GuiAdvanced(parent=parent, properties=self.properties, toolsetWidget=self)
        return parent

    def postContentSetup(self):
        """Last of the initialize code"""
        self.uiConnections()
        self.toggleDisableEnable()  # auto set the disable values of all widgets

    def defaultAction(self):
        """Double Click"""
        pass

    # ------------------
    # PROPERTIES
    # ------------------

    def initializeProperties(self):
        """Used to store and update UI data

        properties are auto-linked if the name matches the widget name

        :return properties: special dictionary used to save and update all GUI widgets
        :rtype properties: list(dict)
        """
        return [{"name": "transferShaderBx", "value": True},
                {"name": "transferUvsBx", "value": True},
                {"name": "uvSampleSpaceCombo", "value": 3},
                {"name": "shaderSpaceCombo", "value": 2},
                {"name": "searchMethodCombo", "value": 1},
                {"name": "skinnedCombo", "value": 1},
                {"name": "deleteHistoryBx", "value": True}]

    def saveProperties(self):
        """Saves properties, keeps self.properties up to date with every widget change
        Overridden function which automates properties updates. Exposed here in case of extra functionality.

        properties are auto-linked if the name matches the widget name
        """
        super(TransferUvs, self).saveProperties()
        self.toggleDisableEnable()  # disable or enable widgets

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
            uvtransfer.transferSelected(transferUvs=True, transferShader=False)
        elif name == "shader":
            uvtransfer.transferSelected(transferUvs=False, transferShader=True)
        elif name == "uv_shader":
            uvtransfer.transferSelected(transferUvs=True, transferShader=True)

    # ------------------
    # DISABLE/ENABLE WIDGETS
    # ------------------

    def toggleDisableEnable(self):
        """Will disable the name textbox with the autoName checkbox is off"""
        if self.properties.shaderSpaceCombo.value == 2 or not self.properties.transferShaderBx.value:
            # then it's topology or shader is ticked off so disable searchMethodCombo
            self.advancedWidget.searchMethodCombo.setDisabled(True)
        else:
            self.advancedWidget.searchMethodCombo.setDisabled(False)
        for widget in self.widgets():  # both GUIs
            uiInstance = widget.children()[0]
            uiInstance.uvSampleSpaceCombo.setDisabled(not self.properties.transferUvsBx.value)
            uiInstance.shaderSpaceCombo.setDisabled(not self.properties.transferShaderBx.value)
        self.advancedWidget.skinnedCombo.setDisabled(not self.properties.transferUvsBx.value)

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidgetmaya.undoDecorator
    def transferUvsClicked(self):
        """ Transfer UV button clicked, do the main UV/Shader transfer
        """
        if not self.properties.transferUvsBx.value and not self.properties.transferShaderBx.value:
            om2.MGlobal.displayWarning("Nothing to transfer, please check a checkbox.")
            return
        uvtransfer.transferSelected(transferUvs=self.properties.transferUvsBx.value,
                                    transferShader=self.properties.transferShaderBx.value,
                                    uvSampleSpace=self.properties.uvSampleSpaceCombo.value,
                                    shaderSampleSpace=self.properties.shaderSpaceCombo.value,
                                    skinned=self.properties.skinnedCombo.value,
                                    searchMethod=self.properties.searchMethodCombo.value,
                                    deleteHistory=self.properties.deleteHistoryBx.value,
                                    message=True)

    @toolsetwidgetmaya.undoDecorator
    def duplicateOriginal(self):
        """Duplicates the original shape node, which is the mesh before the skin cluster was applied.
        """
        duplicatedMeshes = bindskin.duplicateSelectedBeforeBind()
        if duplicatedMeshes:
            om2.MGlobal.displayInfo("Success: Meshes duplicated {}".format(duplicatedMeshes))

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        self.compactWidget.transferBtn.leftClicked.connect(self.transferUvsClicked)
        self.advancedWidget.transferBtn.leftClicked.connect(self.transferUvsClicked)
        self.advancedWidget.duplicateSkinnedBtn.clicked.connect(self.duplicateOriginal)


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
        # Transfer Shader Checkbox -----------------------------------------------------
        toolTip = "Transfer the first selected object's shader onto others \n" \
                  "Supports skinned or deformed meshes."
        self.transferShaderBx = elements.CheckBox("Transfer Shader",
                                                  checked=self.properties.transferShaderBx.value,
                                                  toolTip=toolTip)
        # Transfer UV Checkbox -----------------------------------------------------
        toolTip = "Transfer the first selected object's UVs onto others \n" \
                  "Supports skinned or deformed meshes."
        self.transferUvsBx = elements.CheckBox("Transfer UVs", checked=self.properties.transferUvsBx.value,
                                               toolTip=toolTip)
        # Transfer UV Sample Space Combobox -----------------------------------------------------
        toolTip = "Topology: Topology matches but vertex numbers don't need to match\n" \
                  "Local: Use if both objects match when zeroed\n" \
                  "World: Are in the exact same place in the scene\n" \
                  "Component: When vertex numbers and topology is both identical"
        self.uvSampleSpaceCombo = elements.ComboBoxRegular(label="UV Sample Space",
                                                           items=UV_SAMPLE_SPACE,
                                                           parent=parent,
                                                           toolTip=toolTip,
                                                           setIndex=self.properties.uvSampleSpaceCombo.value)
        # Transfer Shader Space Combobox -----------------------------------------------------
        toolTip = "Topology: Face numbers match exactly\n" \
                  "Local: If both objects match when zeroed\n" \
                  "World: Are in the exact same place in the scene"
        self.shaderSpaceCombo = elements.ComboBoxRegular(label="Shader Sample Space",
                                                         items=SHADER_SAMPLE_SPACE,
                                                         parent=parent,
                                                         toolTip=toolTip,
                                                         setIndex=self.properties.shaderSpaceCombo.value)
        # Transfer UVs Main Button ---------------------------------------
        toolTip = "Select multiple objects. \n" \
                  "The first selected object is transferred onto other objects \n" \
                  "Supports skinning and deformed meshes."
        self.transferBtn = elements.styledButton("Transfer UVs Shaders",
                                                 "transferUVs",
                                                 parent,
                                                 toolTip,
                                                 style=uic.BTN_DEFAULT)

        if uiMode == UI_MODE_ADVANCED:
            # Delete Button ---------------------------------------
            toolTip = "Normal: Closest along the normal direction \n" \
                      "Point: Closest to each point/vertex in distance "
            self.searchMethodCombo = elements.ComboBoxRegular(label="Shader Search Method",
                                                              items=SHADER_SEARCH_METHOD,
                                                              parent=parent,
                                                              toolTip=toolTip,
                                                              setIndex=self.properties.searchMethodCombo.value)
            toolTip = "Duplicates the undeformed original mesh.  Select a skinned mesh and run. \n " \
                      "The duplicated mesh will be before skinning or deformers were assigned."
            self.duplicateSkinnedBtn = elements.styledButton("Duplicate Unskinned",
                                                             "copy1",
                                                             toolTip=toolTip,
                                                             parent=parent,
                                                             style=uic.BTN_LABEL_SML)
            toolTip = "Auto: Detects if skinned or deformed and transfers appropriately onto the orig node. \n" \
                      "Yes: Assumes there is an original shape node, can be used with skinning or deformers. \n" \
                      "No: Will ignore the original shape node and transfer onto the main mesh. "
            self.skinnedCombo = elements.ComboBoxRegular(label="UV Account For Skinning",
                                                         items=["Auto", "Yes", "No"],
                                                         parent=parent,
                                                         toolTip=toolTip)
            toolTip = "After transferring the skinning delete history?\n" \
                      "Note with skinned or deformed meshes this should be on in most cases;\n" \
                      "it will delete history on the original shape node, not on the main mesh. "
            self.deleteHistoryBx = elements.CheckBox("Delete History",
                                                     checked=self.properties.deleteHistoryBx.value,
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
        contentsLayout = elements.vBoxLayout(parent,
                                             margins=(uic.WINSIDEPAD, uic.LRGPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                             spacing=uic.SREG)
        checkboxLayout = elements.hBoxLayout(parent,
                                             margins=(uic.WINSIDEPAD, 0, uic.WINSIDEPAD, uic.WINBOTPAD),
                                             spacing=uic.SREG)
        # Add To Main Layout ---------------------------------------
        checkboxLayout.addWidget(self.transferUvsBx)
        checkboxLayout.addWidget(self.transferShaderBx)

        contentsLayout.addLayout(checkboxLayout)
        contentsLayout.addWidget(self.uvSampleSpaceCombo)
        contentsLayout.addWidget(self.shaderSpaceCombo)
        contentsLayout.addItem(elements.Spacer(0, uic.REGPAD))  # extra space between widgets, width, height
        contentsLayout.addWidget(self.transferBtn)


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
        contentsLayout = elements.vBoxLayout(parent,
                                             margins=(uic.WINSIDEPAD, uic.LRGPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                             spacing=uic.SREG)
        checkboxLayout = elements.hBoxLayout(parent,
                                             margins=(uic.WINSIDEPAD, 0, uic.WINSIDEPAD, uic.WINBOTPAD),
                                             spacing=uic.SREG)

        layout = elements.hBoxLayout(parent,
                                     margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.SMLPAD),
                                     spacing=uic.SREG)

        # Button Layout ---------------------------------------
        checkboxLayout.addWidget(self.transferUvsBx)
        checkboxLayout.addWidget(self.transferShaderBx)

        contentsLayout.addLayout(checkboxLayout)
        contentsLayout.addWidget(self.uvSampleSpaceCombo)
        contentsLayout.addWidget(self.skinnedCombo)
        contentsLayout.addWidget(self.shaderSpaceCombo)
        contentsLayout.addWidget(self.searchMethodCombo)

        layout.addWidget(self.deleteHistoryBx, 1)
        layout.addWidget(self.duplicateSkinnedBtn, 1)
        contentsLayout.addLayout(layout)

        contentsLayout.addWidget(self.transferBtn)
