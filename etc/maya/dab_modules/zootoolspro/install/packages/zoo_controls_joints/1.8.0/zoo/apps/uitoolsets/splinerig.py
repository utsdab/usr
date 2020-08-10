from Qt import QtWidgets
from maya import cmds
import maya.api.OpenMaya as om2

from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.maya.cmds.rig import splinebuilder

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

uiEnabled = True
UP_AXIS_LIST = ["+Y", "-Y", "+X", "-X", "+Z", "-Z"]


class SplineRig(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "splineRig"
    info = "Builds a spline rig with various options"
    uiData = {"label": "Spline Rig (beta)",
              "icon": "splineRig",
              "tooltip": "Builds a spline rig with various options.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-spline-rig/"
              }

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        pass

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """

        return [self.initCompactWidget()]


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
        self.updateWidgets()
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
        return super(SplineRig, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(SplineRig, self).widgets()

    # ------------------
    # LOGIC
    # ------------------

    def updateWidgets(self):
        if self.properties.controlsIntE.value != 5:  # disable the spine checkbox
            self.properties.spineCheckBox.value = False
            self.compactWidget.spineCheckBox.setEnabled(False)
        else:
            self.compactWidget.spineCheckBox.setEnabled(True)
        if self.properties.typeCombo.value == 0:  # enable spine checkbox
            self.compactWidget.controlsIntE.setEnabled(False)
            self.properties.controlsIntE.value = 5
            self.compactWidget.spineCheckBox.setEnabled(True)
        else:
            self.compactWidget.controlsIntE.setEnabled(True)
        self.updateFromProperties()

    def inputStartJoint(self):
        """Inputs a starting joint into the start textfield"""
        selection = cmds.ls(selection=True, type="joint")
        if not selection:
            om2.MGlobal.displayWarning("Please select a joint")
            return
        self.properties.startJointStrE.value = selection[0]
        self.updateFromProperties()

    def inputEndJoint(self):
        """Inputs a end joint into the start textfield"""
        selection = cmds.ls(selection=True, type="joint")
        if not selection:
            om2.MGlobal.displayWarning("Please select a joint")
            return
        self.properties.endJointStrE.value = selection[0]
        self.updateFromProperties()

    @toolsetwidgetmaya.undoDecorator
    def buildRig(self):
        """
        """
        cogUpAxis = UP_AXIS_LIST[self.properties.orientRootCombo.value].lower()
        splinebuilder.buildSpine(self.properties.nameStrE.value,
                                 startJoint=self.properties.startJointStrE.value,
                                 endJoint=self.properties.endJointStrE.value,
                                 controlCount=self.properties.controlsIntE.value,
                                 scale=self.properties.scaleFloatE.value,
                                 buildFk=self.properties.fkCheckBox.value,
                                 buildRevFk=self.properties.reverseCheckBox.value,
                                 buildSpine=self.properties.spineCheckBox.value,
                                 buildFloat=self.properties.floatCheckBox.value,
                                 cogUpAxis=cogUpAxis)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.buildBtn.clicked.connect(self.buildRig)
            widget.getStartJntBtn.clicked.connect(self.inputStartJoint)
            widget.getEndJntBtn.clicked.connect(self.inputEndJoint)
            widget.typeCombo.itemChanged.connect(self.updateWidgets)
            widget.controlsIntE.textModified.connect(self.updateWidgets)


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
        # Titles Dividers ---------------------------------------
        self.setupTitle = elements.LabelDivider(text="Specify Joints")
        self.controlRigsTitle = elements.LabelDivider(text="Add Control Rigs")
        self.optionsTitle = elements.LabelDivider(text="Rig Options")
        # Checkboxes ---------------------------------------
        tooltip = "If on, a FK control setup will be built"
        self.fkCheckBox = elements.CheckBox(label="FK Controls",
                                            checked=True,
                                            toolTip=tooltip)
        tooltip = "If on, a Reverse FK control setup will be built. \n" \
                  "The controls will be parented backwards"
        self.reverseCheckBox = elements.CheckBox(label="Reverse FK Controls",
                                                 checked=True,
                                                 toolTip=tooltip)
        tooltip = "If on, a Floating control setup will be built \n" \
                  "All controls will be parented to the root only"
        self.floatCheckBox = elements.CheckBox(label="Floating Controls",
                                               checked=True,
                                               toolTip=tooltip)
        tooltip = "If on, a Spine control setup will be built \n" \
                  "This setup is handy for character spine setups."
        self.spineCheckBox = elements.CheckBox(label="Spine Controls",
                                               checked=True,
                                               toolTip=tooltip)
        # Start Joint ---------------------------------------
        tooltip = "Specify the first joint in the joint chain. \n" \
                  "The base of the spline rig will start here."
        self.startJointStrE = elements.StringEdit(label="First Joint",
                                                  editPlaceholder="Enter the start joint name of the chain",
                                                  editText="",
                                                  toolTip=tooltip,
                                                  editRatio=17,
                                                  labelRatio=4)
        # Get Start Joint ---------------------------------------
        toolTip = "Select the start joint and press to add to the UI."
        self.getStartJntBtn = elements.styledButton("",
                                                    "arrowLeft",
                                                    self,
                                                    toolTip=toolTip,
                                                    style=uic.BTN_TRANSPARENT_BG,
                                                    minWidth=15)
        # End Joint ---------------------------------------
        tooltip = "Specify the last joint in the joint chain. \n" \
                  "The end of the spline rig will end here."
        self.endJointStrE = elements.StringEdit(label="End Joint",
                                                editPlaceholder="Enter the end joint name of the chain",
                                                editText="",
                                                toolTip=tooltip,
                                                editRatio=17,
                                                labelRatio=4)
        # Get End Joint ---------------------------------------
        toolTip = "Select the end joint and press to add to the UI."
        self.getEndJntBtn = elements.styledButton("",
                                                  "arrowLeft",
                                                  self,
                                                  toolTip=toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=15)
        # Control Number ---------------------------------------
        tooltip = "The amount of controls to create \n" \
                  "To enable change the `Type` combo box to `Custom Count`. \n" \
                  "The `Spine` rig type can only be created with 5 controls."
        self.controlsIntE = elements.IntEdit(label="Controls",
                                             editText=5,
                                             toolTip=tooltip,
                                             editRatio=20,
                                             labelRatio=8)
        # Options Combo ---------------------------------------
        tooltip = "Build a Spine rig setup limited to five controls or enter any amount of controls. \n" \
                  "The spine rig cannot be built without five controls and will be disabled."
        self.typeCombo = elements.ComboBoxRegular(label="Type",
                                                  items=["Spine 5 Controls", "Custom Count"],
                                                  toolTip=tooltip,
                                                  labelRatio=8,
                                                  boxRatio=20)
        # Scale ---------------------------------------
        tooltip = "Sets the scale of the rig controls."
        self.scaleFloatE = elements.FloatEdit(label="Scale",
                                              editText=1.0,
                                              toolTip=tooltip,
                                              editRatio=20,
                                              labelRatio=12)
        # Name ---------------------------------------
        tooltip = "Set the name of the spline rig"
        self.nameStrE = elements.StringEdit(label="Rig Name",
                                            editText="splineRig",
                                            toolTip=tooltip,
                                            editRatio=80,
                                            labelRatio=17)
        # Options Combo ---------------------------------------
        tooltip = "Orients the root control to face this direction. \n" \
                  "The control also affects the up vector for the rig. \n" \
                  "The up vector is always -Z of the Root Control."
        self.orientRootCombo = elements.ComboBoxRegular(label="Orient Root",
                                                        items=UP_AXIS_LIST,
                                                        setIndex=0,
                                                        toolTip=tooltip,
                                                        labelRatio=12,
                                                        boxRatio=20)
        # Build Button ---------------------------------------
        tooltip = "Builds the spline rig"
        self.buildBtn = elements.styledButton("Build Spline Rig",
                                              icon="splineRig",
                                              toolTip=tooltip,
                                              style=uic.BTN_DEFAULT)
        # Trash Button ---------------------------------------
        """
        tooltip = "Select any part of the rig and press to delete"
        self.deleteBtn = elements.styledButton("", "trash",
                                               toolTip=tooltip,
                                               maxWidth=uic.BTN_W_ICN_LRG,
                                               minWidth=uic.BTN_W_ICN_LRG)
        """


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
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Grid Checkbox Layout --------------------------------------
        checkboxLayout = elements.GridLayout(margins=(uic.REGPAD, uic.REGPAD, uic.REGPAD, uic.REGPAD),
                                             spacing=uic.SVLRG)
        checkboxLayout.addWidget(self.fkCheckBox, 0, 0)
        checkboxLayout.addWidget(self.reverseCheckBox, 0, 1)
        checkboxLayout.addWidget(self.floatCheckBox, 1, 0)
        checkboxLayout.addWidget(self.spineCheckBox, 1, 1)
        checkboxLayout.setColumnStretch(0, 1)
        checkboxLayout.setColumnStretch(1, 1)
        # Start Layout --------------------------------------
        startLayout = elements.hBoxLayout()
        startLayout.addWidget(self.startJointStrE, 10)
        startLayout.addWidget(self.getStartJntBtn, 1)
        # End Layout --------------------------------------
        endLayout = elements.hBoxLayout()
        endLayout.addWidget(self.endJointStrE, 10)
        endLayout.addWidget(self.getEndJntBtn, 1)
        # Orient Options Layout --------------------------------------
        orientLayout = elements.hBoxLayout(spacing=uic.SLRG)
        orientLayout.addWidget(self.orientRootCombo, 1)
        orientLayout.addWidget(self.typeCombo, 1)
        # Controls Layout --------------------------------------
        controlsLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.REGPAD), spacing=uic.SLRG)
        controlsLayout.addWidget(self.scaleFloatE, 1)
        controlsLayout.addWidget(self.controlsIntE, 1)
        # Button Layout --------------------------------------
        buttonLayout = elements.hBoxLayout()
        buttonLayout.addWidget(self.buildBtn, 10)
        # buttonLayout.addWidget(self.deleteBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(self.setupTitle)
        mainLayout.addLayout(startLayout)
        mainLayout.addLayout(endLayout)

        mainLayout.addWidget(self.controlRigsTitle)
        mainLayout.addLayout(checkboxLayout)

        mainLayout.addWidget(self.optionsTitle)
        mainLayout.addWidget(self.nameStrE)
        mainLayout.addLayout(orientLayout)
        mainLayout.addLayout(controlsLayout)

        mainLayout.addLayout(buttonLayout)


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
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Currently not used
