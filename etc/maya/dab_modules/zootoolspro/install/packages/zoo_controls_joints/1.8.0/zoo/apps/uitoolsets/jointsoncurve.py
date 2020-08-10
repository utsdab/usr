from Qt import QtWidgets

from maya import cmds

from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.apps.toolsetsui import toolsetcallbacks
from zoo.libs.maya.cmds.rig import splines
from zoo.libs.maya.cmds.objutils import joints, curves

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

uiEnabled = True


class JointsOnCurve(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "jointsOnCurve"
    info = "Builds and orients joints along a curve."
    uiData = {"label": "Joints On Curve",
              "icon": "jointsOnCurve",
              "tooltip": "Builds and orients joints along a curve.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-joints-on-curve/"
              }

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        self.toolsetWidget = self  # needed for callback decorators

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
        self.uiModeList()
        self.uiConnections()
        self.refreshUpdateUIFromSelection(update=False)  # update GUI from current in scene selection
        self.startSelectionCallback()  # start selection callback

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

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(JointsOnCurve, self).widgets()

    # ------------------
    # CALLBACKS
    # ------------------

    # place the method in the main toolset tool class
    def refreshUpdateUIFromSelection(self, update=True):
        # Get data from scene and set GUI self.properties etc here
        attrDict = splines.splineJointsAttrValues(message=False)
        if not attrDict:
            return
        # Find axis index in the joints.UP_VECTOR_WORDS_LIST list
        axisIndex = [idx for idx, s in enumerate(joints.UP_VECTOR_WORDS_LIST) if
                     attrDict["secondaryAxisOrient"] in s][0]
        # Set properties
        self.properties.jointCountInt.value = attrDict["jointCount"]
        self.properties.nameStr.value = attrDict["jointName"]
        self.properties.spacingWeightFSlider.value = float("{0:.3f}".format(round(attrDict["spacingWeight"], 3)))  # rnd
        self.properties.startFloat.value = float("{0:.3f}".format(round(attrDict["spacingStart"], 3)))  # rnd
        self.properties.endFloat.value = float("{0:.3f}".format(round(attrDict["spacingEnd"], 3)))  # rnd
        self.properties.upAxisCombo.value = axisIndex
        self.properties.fractionModeCheckbox.value = attrDict["fractionMode"]
        self.properties.paddingInt.value = attrDict["numberPadding"]
        self.properties.suffixCheckbox.value = attrDict["suffix"]
        self.properties.reverseCheckbox.value = attrDict["reverse"]
        if update:
            self.updateFromProperties()

    def selectionChanged(self, selection):
        """Run when the callback selection changes, updates the GUI if an object is selected

        Callbacks are handled automatically by toolsetcallbacks.py which this class inherits"""
        if not selection:
            joints = cmds.ls(selection=True, type="joint")  # joints aren't handled in the selection return
            if not joints:  # then don't update
                return
        self.refreshUpdateUIFromSelection()  # will update the GUI

    # ------------------
    # LOGIC
    # ------------------

    def createCurveContext(self):
        """Enters the create curve context (user draws cvs).  Uses mel hardcoded 3 bezier curve."""
        curves.createCurveContext(degrees=3)

    @toolsetwidgetmaya.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def jointsOnCurve(self):
        """Builds the joints on a curve from the UI info"""
        upAxis = joints.UP_VECTOR_WORDS_LIST[self.properties.upAxisCombo.value]

        splines.jointsAlongACurveSelected(jointCount=self.properties.jointCountInt.value,
                                          jointName=self.properties.nameStr.value,
                                          spacingWeight=self.properties.spacingWeightFSlider.value,
                                          spacingStart=self.properties.startFloat.value,
                                          spacingEnd=self.properties.endFloat.value,
                                          secondaryAxisOrient=upAxis,
                                          fractionMode=self.properties.fractionModeCheckbox.value,
                                          numberPadding=self.properties.paddingInt.value,
                                          suffix=self.properties.suffixCheckbox.value,
                                          reverseDirection=self.properties.reverseCheckbox.value)

    def quietRebuild(self):
        """Rebuilds with no messages to the user, this function avoids the kwargs issue with widgets"""
        self.rebuildJointsOnCurve(message=False)

    def renameRebuild(self):
        """Rebuilds and includes the rename function, used while renaming"""
        # ToDo: could do a more elegant rename option based off existing joints
        self.rebuildJointsOnCurve(message=False, renameMode=True)

    @toolsetwidgetmaya.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def rebuildJointsOnCurve(self, message=True, renameMode=False):
        """Deletes all joints related to the current selection and rebuilds as per the UI settings"""
        upAxis = joints.UP_VECTOR_WORDS_LIST[self.properties.upAxisCombo.value]
        splines.rebuildSplineJointsSelected(jointCount=self.properties.jointCountInt.value,
                                            jointName=self.properties.nameStr.value,
                                            spacingWeight=self.properties.spacingWeightFSlider.value,
                                            spacingStart=self.properties.startFloat.value,
                                            spacingEnd=self.properties.endFloat.value,
                                            secondaryAxisOrient=upAxis,
                                            fractionMode=self.properties.fractionModeCheckbox.value,
                                            numberPadding=self.properties.paddingInt.value,
                                            suffix=self.properties.suffixCheckbox.value,
                                            renameMode=renameMode,
                                            reverseDirection=self.properties.reverseCheckbox.value,
                                            message=message)

    @toolsetwidgetmaya.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def deleteJointsOnCurve(self):
        """Deletes all joints related to the current selection"""
        splines.deleteSplineJointsSelected()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.createJointsBtn.clicked.connect(self.jointsOnCurve)
            # widget.recreateJointsBtn.clicked.connect(self.rebuildJointsOnCurve)
            widget.curveCvBtn.clicked.connect(self.createCurveContext)
            widget.deleteBtn.clicked.connect(self.deleteJointsOnCurve)
            # rename
            widget.nameStr.textModified.connect(self.renameRebuild)
            # UI updates with quiet build
            widget.jointCountInt.textModified.connect(self.quietRebuild)
            widget.upAxisCombo.currentIndexChanged.connect(self.quietRebuild)
            widget.spacingWeightFSlider.floatSliderMajorChange.connect(self.quietRebuild)
            widget.reverseCheckbox.stateChanged.connect(self.quietRebuild)
        # UI updates with quiet build
        self.advancedWidget.paddingInt.textModified.connect(self.quietRebuild)
        self.advancedWidget.startFloat.textModified.connect(self.quietRebuild)
        self.advancedWidget.endFloat.textModified.connect(self.quietRebuild)
        self.advancedWidget.fractionModeCheckbox.stateChanged.connect(self.quietRebuild)
        self.advancedWidget.suffixCheckbox.stateChanged.connect(self.quietRebuild)
        # callbacks
        self.selectionCallbacks.callback.connect(self.selectionChanged)  # monitor selection
        self.toolsetActivated.connect(self.startSelectionCallback)
        self.toolsetDeactivated.connect(self.stopSelectionCallback)


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
        # Name Str ---------------------------------------
        tooltip = "The name of the joint chain."
        editRatio = 2 if uiMode == UI_MODE_ADVANCED else 100
        labelRatio = 1 if uiMode == UI_MODE_ADVANCED else 31
        self.nameStr = elements.StringEdit(label="Name",
                                           editText="joint",
                                           toolTip=tooltip,
                                           editRatio=editRatio,
                                           labelRatio=labelRatio)
        # Axis Up Combo ---------------------------------------
        tooltip = "The up axis for the Y axis of all joints"
        self.upAxisCombo = elements.ComboBoxRegular(label="World Up",
                                                    items=joints.UP_VECTOR_POSNEG_LIST,
                                                    setIndex=2,
                                                    toolTip=tooltip,
                                                    boxRatio=2,
                                                    labelRatio=1)
        # Joint Count Int ---------------------------------------
        tooltip = "The number of joints to build along the curve."
        self.jointCountInt = elements.IntEdit(label="Count",
                                                 editText=24,
                                                 toolTip=tooltip,
                                                 editRatio=2,
                                                 labelRatio=1)
        # Spacing Weight Slider  ------------------------------------
        tooltip = "The spacing weight between the joints from one end of the curve or the other. \n" \
                  "A value of 0.0 will evenly space objects."
        self.spacingWeightFSlider = elements.FloatSlider(label="Weight",
                                                         toolTip=tooltip,
                                                         sliderMin=-2.0,
                                                         sliderMax=2.0,
                                                         labelRatio=1,
                                                         editBoxRatio=2)
        # Create Joint Button ---------------------------------------
        tooltip = "Build joints along a curve. \n" \
                  "  1. Select a curve \n" \
                  "  2. Run the tool \n" \
                  "Joints will be placed along the curve."
        self.createJointsBtn = elements.styledButton("Create Joints",
                                                     icon="jointsOnCurve",
                                                     toolTip=tooltip,
                                                     style=uic.BTN_DEFAULT)
        # Rebuild Joint Button ---------------------------------------
        """tooltip = "Rebuilds an existing joint setup. \n" \
                  "  1. Select a curve or joint of an existing setup \n" \
                  "  2. Run the tool \n" \
                  "Joints will be rebuilt along the curve."
        self.recreateJointsBtn = elements.styledButton("Rebuild",
                                                       icon="jointsOnCurve",
                                                       toolTip=tooltip,
                                                       style=uic.BTN_DEFAULT)"""
        # Delete Joint Button ------------------------------------
        toolTip = "Deletes all joints related to the current curve or joint selection."
        self.deleteBtn = elements.styledButton("",
                                               "trash",
                                               toolTip=toolTip,
                                               parent=parent,
                                               minWidth=uic.BTN_W_ICN_MED)
        # Create CV Curve Button ------------------------------------
        toolTip = "Create a CV Curve (3 Cubic)"
        self.curveCvBtn = elements.styledButton("",
                                                "curveCv",
                                                toolTip=toolTip,
                                                parent=parent,
                                                minWidth=uic.BTN_W_ICN_MED)
        # Reverse Direction Checkbox ---------------------------------------
        tooltip = "Will reverse the direction the joints are built.  \n" \
                  "Note this will reverse the curve direction temporarily \n" \
                  "do not use if curve has history."
        self.reverseCheckbox = elements.CheckBox(label="Reverse Dir",
                                                 toolTip=tooltip,
                                                 checked=False)
        if uiMode == UI_MODE_ADVANCED:
            # Start Pos Float ---------------------------------------
            tooltip = "The start position along the curve"
            self.startFloat = elements.FloatEdit(label="Start",
                                                  editText=0.0,
                                                  toolTip=tooltip,
                                                  editRatio=2,
                                                  labelRatio=1)
            # End Pos Float ---------------------------------------
            tooltip = "The end position along the curve"
            self.endFloat = elements.FloatEdit(label="End",
                                                editText=1.0,
                                                toolTip=tooltip,
                                                editRatio=2,
                                                labelRatio=1)
            # Padding Int ---------------------------------------
            tooltip = "The numerical padding of each joint."
            self.paddingInt = elements.IntEdit(label="Padding",
                                                  editText=2,
                                                  toolTip=tooltip,
                                                  editRatio=2,
                                                  labelRatio=1)
            # Fraction Checkbox ---------------------------------------
            tooltip = "On: Position textbox of 1.0 represents the full curve length and 0.5 is half way. \n" \
                      "Off: The position textbox will be in Maya units, usually cms though  \n " \
                      "curve CVs must be equally spaced"
            self.fractionModeCheckbox = elements.CheckBox(label="Position As Fraction",
                                                          toolTip=tooltip,
                                                          checked=True)
            # Suffix Checkbox ---------------------------------------
            tooltip = "Suffixes all joints with `jnt`, example `name_01_jnt`"
            self.suffixCheckbox = elements.CheckBox(label="Add jnt Suffix",
                                                    toolTip=tooltip,
                                                    checked=True)


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
        # Name Layout ---------------------------------------
        nameLayout = elements.hBoxLayout()
        nameLayout.addWidget(self.nameStr, 22)
        nameLayout.addWidget(self.reverseCheckbox, 10)
        # Count Layout ---------------------------------------
        countLayout = elements.hBoxLayout()
        countLayout.addWidget(self.jointCountInt, 1)
        countLayout.addWidget(self.upAxisCombo, 1)
        # Button Layout ---------------------------------------
        btnLayout = elements.hBoxLayout()
        btnLayout.addWidget(self.createJointsBtn, 9)
        # btnLayout.addWidget(self.recreateJointsBtn, 3)
        btnLayout.addWidget(self.deleteBtn, 1)
        btnLayout.addWidget(self.curveCvBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(nameLayout)
        mainLayout.addLayout(countLayout)
        mainLayout.addWidget(self.spacingWeightFSlider)
        mainLayout.addLayout(btnLayout)


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
        # Name Layout ---------------------------------------
        nameLayout = elements.hBoxLayout()
        nameLayout.addWidget(self.nameStr, 1)
        nameLayout.addWidget(self.paddingInt, 1)
        # Count Layout ---------------------------------------
        countLayout = elements.hBoxLayout()
        countLayout.addWidget(self.jointCountInt, 1)
        countLayout.addWidget(self.upAxisCombo, 1)
        # Start end Pos Layout ---------------------------------------
        posLayout = elements.hBoxLayout()
        posLayout.addWidget(self.startFloat, 1)
        posLayout.addWidget(self.endFloat, 1)
        # Checkbox Layout ---------------------------------------
        checkBoxLayout = elements.hBoxLayout(margins=(uic.REGPAD, uic.REGPAD, uic.REGPAD, uic.REGPAD))
        checkBoxLayout.addWidget(self.reverseCheckbox, 1)
        checkBoxLayout.addWidget(self.suffixCheckbox, 1)
        checkBoxLayout.addWidget(self.fractionModeCheckbox, 1)
        # Button Layout ---------------------------------------
        btnLayout = elements.hBoxLayout()
        btnLayout.addWidget(self.createJointsBtn, 9)
        # btnLayout.addWidget(self.recreateJointsBtn, 3)
        btnLayout.addWidget(self.deleteBtn, 1)
        btnLayout.addWidget(self.curveCvBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(nameLayout)
        mainLayout.addLayout(countLayout)
        mainLayout.addWidget(self.spacingWeightFSlider)
        mainLayout.addLayout(posLayout)
        mainLayout.addLayout(checkBoxLayout)
        mainLayout.addLayout(btnLayout)
