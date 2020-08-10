from functools import partial

from Qt import QtWidgets

from maya import cmds
import maya.mel as mel

from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya

from zoo.libs.maya.cmds.objutils import joints
from zoo.libs.pyqt import uiconstants as uic, keyboardmouse
from zoo.libs.pyqt.widgets import elements
from zoo.libs.maya.cmds.general import undodecorator

XYZ_LIST = ["X", "Y", "Z"]
UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1
ROTATE_LIST = ["Rotate X", "Rotate Y", "Rotate Z"]


class ToolsetToolUI(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "jointTool"
    uiData = {"label": "Joint Tool Window",
              "icon": "skeleton",
              "tooltip": "Simple Align Joints Tool",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-joint-tool-window/"
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
        self.compactWidget = CompactLayout(parent=self, properties=self.properties, toolsetWidget=self)
        return self.compactWidget

    def initAdvancedWidget(self):
        """Builds the Advanced GUI (self.advancedWidget) """
        self.advancedWidget = AdvancedLayout(parent=self, properties=self.properties, toolsetWidget=self)
        return self.advancedWidget

    def postContentSetup(self):
        """Last of the initialize code"""

        self.uiConnections()
        self.properties.globalDisplaySize.value = cmds.jointDisplayScale(query=True)  # get global size from scene
        self.updateFromProperties()

    def defaultAction(self):
        """Double Click"""
        pass

    # ------------------
    # PROPERTIES
    # ------------------

    def initializeProperties(self):
        """Used to store and update UI data

        For use in the GUI use:
            current value: self.properties.itemName.value
            default value (automatic): self.properties.itemName.default

        To connect Qt widgets to property methods use:
            self.toolsetWidget.linkProperty(self.widgetQtName, "itemName")

        :return properties: special dictionary used to save and update all GUI widgets
        :rtype properties: list(dict)
        """
        return [{"name": "rotateLra", "value": 45},
                {"name": "selHierarchyRadio", "value": 1},
                {"name": "globalDisplaySize", "value": 1},
                {"name": "jointRadius", "value": 1.0},
                {"name": "mirrorCombo", "value": 0},
                {"name": "rotateCombo", "value": 0}]

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidgetmaya.undoDecorator
    def alignJoint(self, alignYUp=True):
        """Aligns the selected joints in the scene, option to orient children of the selected

        :param alignYUp: point the y axis up (True) or down (False)
        :type alignYUp: bool
        """
        if alignYUp:
            joints.alignJointSelected(secondaryAxisOrient="yup", children=self.properties.selHierarchyRadio.value)
        else:
            joints.alignJointSelected(secondaryAxisOrient="ydown", children=self.properties.selHierarchyRadio.value)

    @toolsetwidgetmaya.undoDecorator
    def LRAVisibility(self, visiblity=True):
        """Show the joints local rotation axis or LRA manipulators
        Can affect the children of selected with the checkbox settings

        :param visiblity: show the local rotation axis (True), or hide (False)
        :type visiblity: bool
        """
        if visiblity:
            joints.displayLocalRotationAxisSelected(children=self.properties.selHierarchyRadio.value, display=True,
                                                    message=False)
        else:
            joints.displayLocalRotationAxisSelected(children=self.properties.selHierarchyRadio.value, display=False,
                                                    message=False)

    @toolsetwidgetmaya.undoDecorator
    def zeroRotAxis(self):
        """Zeroes the rotation axis of the selected joints.  Useful if you've manually reoriented joints with their
        local rotation handles.
        """
        joints.zeroRotAxisSelected(zeroChildren=self.properties.selHierarchyRadio.value)

    @toolsetwidgetmaya.undoDecorator
    def alignJointToParent(self):
        """Aligns the selected joint to its parent
        """
        joints.alignJointToParentSelected()

    @toolsetwidgetmaya.undoDecorator
    def drawJoint(self, drawVis=True):
        """sets the attribute

        :param alignYUp: point the y axis up (True) or down (False)
        :type alignYUp: bool
        """
        if not drawVis:
            joints.jointDrawNoneSelected(children=self.properties.selHierarchyRadio.value)
        else:
            joints.jointDrawBoneSelected(children=self.properties.selHierarchyRadio.value)

    @toolsetwidgetmaya.undoDecorator
    def editLRA(self, editLRA=True):
        """Enter component mode, switch on edit local rotation axis, turn handle vis on
        If editLRA False then turn of local rotation axis in component mode, exit component mode
        """
        joints.editComponentLRA(editLRA=editLRA)

    @toolsetwidgetmaya.undoDecorator
    def rotateLRA(self, neg=False):
        """ Rotate LRA

        :param neg:
        :type neg:
        :return:
        :rtype:
        """
        # for alt shift and ctrl keys with left click, alt (reset is not supported)
        multiplier, reset = keyboardmouse.cntrlShiftMultiplier(shiftMultiply=2.0, ctrlMultiply=0.5)
        if neg:
            rotateLra = -(self.properties.rotateLra.value * multiplier)
        else:
            rotateLra = self.properties.rotateLra.value * multiplier
        if self.displayIndex() == UI_MODE_COMPACT:
            rot = [rotateLra, 0, 0]
        else:
            if self.properties.rotateCombo.value == 0:  # then X
                rot = [rotateLra, 0, 0]
            elif self.properties.rotateCombo.value == 1:
                rot = [0, rotateLra, 0]
            else:
                rot = [0, 0, rotateLra]
        joints.rotateLRASelection(rot, includeChildren=self.properties.selHierarchyRadio.value)

    @toolsetwidgetmaya.undoDecorator
    def mirrorJoint(self):
        """ Mirrors jnt/s across a given plane from the GUI

        :return:
        :rtype:
        """
        axisInt = self.properties.mirrorCombo.value
        if axisInt == 0:
            axis = "X"
        elif axisInt == 1:
            axis = "Y"
        else:
            axis = "Z"
        joints.mirrorJointSelected(axis, searchReplace=(["_L", "_R"], ["_lft", "_rgt"]))

    @toolsetwidgetmaya.undoDecorator
    def setJointRadius(self, null):
        """Sets the joint radius for selected joints"""
        joints.setJointRadiusSelected(self.properties.jointRadius.value,
                                      children=self.properties.selHierarchyRadio.value,
                                      message=False)

    def displayJointSize(self):
        # sets the global display size of joints
        cmds.jointDisplayScale(self.properties.globalDisplaySize.value)

    def createJoint(self):
        """Invokes the joint create tool"""
        mel.eval("JointTool;")

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[AdvancedLayout or CompactLayout]
        """
        return super(ToolsetToolUI, self).widgets()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        for widget in self.widgets():  # both GUIs

            widget.orientYPosBtn.clicked.connect(partial(self.alignJoint, alignYUp=True))
            widget.orientYNegBtn.clicked.connect(partial(self.alignJoint, alignYUp=False))
            widget.showLRABtn.clicked.connect(partial(self.LRAVisibility, visiblity=True))
            widget.hideLRABtn.clicked.connect(partial(self.LRAVisibility, visiblity=False))
            widget.rotateLraNegBtn.clicked.connect(partial(self.rotateLRA, neg=True))
            widget.rotateLraPosBtn.clicked.connect(partial(self.rotateLRA, neg=False))
            widget.createJntBtn.clicked.connect(self.createJoint)
        # Advanced widgets
        self.advancedWidget.jointRadiusTxt.textModified.connect(self.setJointRadius)
        self.advancedWidget.globalDisplaySizeTxt.textModified.connect(self.displayJointSize)
        self.advancedWidget.mirrorBtn.clicked.connect(self.mirrorJoint)
        self.advancedWidget.zeroRotAxisBtn.clicked.connect(self.zeroRotAxis)
        self.advancedWidget.alignParentBtn.clicked.connect(self.alignJointToParent)
        self.advancedWidget.drawHideBtn.clicked.connect(partial(self.drawJoint, drawVis=False))
        self.advancedWidget.drawShowBtn.clicked.connect(partial(self.drawJoint, drawVis=True))
        self.advancedWidget.editLRABtn.clicked.connect(partial(self.editLRA, editLRA=True))
        self.advancedWidget.exitLRABtn.clicked.connect(partial(self.editLRA, editLRA=False))


class GuiWidgets(QtWidgets.QWidget):
    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None):
        """Builds the main widgets for all GUIs

        properties is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: ZooRenamer
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: object
        :param uiMode: 0 is compact ui mode, 1 is advanced ui mode
        :type uiMode: int
        """
        super(GuiWidgets, self).__init__(parent=parent)

        self.toolsetWidget = toolsetWidget
        self.properties = properties
        # Selected Hierarchy Radio Buttons ------------------------------------
        radioNameList = ["Selected", "Hierarchy"]
        radioToolTipList = ["Affect only the selected joints.", "Affect the selection and all child joints."]
        self.selHierarchyRadioWidget = elements.RadioButtonGroup(radioList=radioNameList,
                                                                 toolTipList=radioToolTipList,
                                                                 default=self.properties.selHierarchyRadio.value,
                                                                 parent=parent,
                                                                 margins=(0, 0, 0, 0))
        self.toolsetWidget.linkProperty(self.selHierarchyRadioWidget, "selHierarchyRadio")
        # Orient Up Section
        toolTip = "Orient joints so that +X points towards the next joint, and Y orients up in world space."
        self.orientYPosBtn = elements.styledButton("Orient Y+", "arrowUp", parent, toolTip=toolTip,
                                                   style=uic.BTN_DEFAULT, minWidth=uic.BTN_W_REG_SML)
        toolTip = "Orient joints so that +X points towards the next joint, and Y orients down in world space."
        self.orientYNegBtn = elements.styledButton("Orient Y-", "arrowDown", parent, toolTip=toolTip,
                                                   style=uic.BTN_DEFAULT, minWidth=uic.BTN_W_REG_SML)
        # Display Local Rotation Axis Section
        toolTip = "Show the local rotation axis on the selected object/s"
        self.showLRABtn = elements.styledButton("Show LRA", "axis", parent, toolTip=toolTip,
                                                style=uic.BTN_DEFAULT, minWidth=uic.BTN_W_REG_SML)
        toolTip = "Hide the local rotation axis on the selected object/s."
        self.hideLRABtn = elements.styledButton("Hide LRA", "axis", parent, toolTip=toolTip,
                                                style=uic.BTN_DEFAULT, minWidth=uic.BTN_W_REG_SML)
        # Rotate Section ------------------------------------
        toolTip = "Rotate the local rotation axis in degrees.\n" \
                  "Default is negative 45 degrees"
        self.rotateLraNegBtn = elements.styledButton("",
                                                     "arrowRotLeft",
                                                     toolTip=toolTip,
                                                     parent=parent,
                                                     minWidth=uic.BTN_W_ICN_MED)
        toolTip = "Rotate the local rotation axis in degrees.\n" \
                  "Default is 45 degrees"
        self.rotateLraPosBtn = elements.styledButton("",
                                                     "arrowRotRight",
                                                     toolTip=toolTip,
                                                     parent=parent,
                                                     minWidth=uic.BTN_W_ICN_MED)
        # Create Joint btn ------------------------------------
        toolTip = "Enter the Create Joint Tool, left click in the viewport to draw joints."
        self.createJntBtn = elements.styledButton("Create Joint Tool", "skeleton", parent, toolTip=toolTip,
                                                  style=uic.BTN_DEFAULT)
        if uiMode == UI_MODE_ADVANCED:
            # Joint Size ------------------------------------
            toolTip = "Set the global joint display size, all joints in the scene are affected."
            self.globalDisplaySizeTxt = elements.FloatEdit("Scene Jnt Size",
                                                           self.properties.globalDisplaySize.value,
                                                           parent=parent,
                                                           toolTip=toolTip)
            self.toolsetWidget.linkProperty(self.globalDisplaySizeTxt, "globalDisplaySize")
            toolTip = "Set the joint radius (display size) of the selected joints."
            self.jointRadiusTxt = elements.FloatEdit("Local Jnt Radius",
                                                     self.properties.jointRadius.value,
                                                     parent=parent,
                                                     toolTip=toolTip)
            self.toolsetWidget.linkProperty(self.jointRadiusTxt, "jointRadius")
            # Rotate text
            toolTip = "Rotate the local rotation axis by this angle in degrees."
            self.rotateLraTxt = elements.FloatEdit("",
                                                   self.properties.rotateLra.value,
                                                   parent=parent,
                                                   toolTip=toolTip)
            self.toolsetWidget.linkProperty(self.rotateLraTxt, "rotateLra")
            # Rotation combo ------------------------------------
            toolTip = "Rotate around this axis. X, Y or Z?"
            self.rotateCombo = elements.ComboBoxRegular("Rot Axis",
                                                        items=XYZ_LIST,
                                                        setIndex=self.properties.rotateCombo.value,
                                                        parent=parent, toolTip=toolTip)
            # Mirror btns ------------------------------------
            toolTip = "Set the mirror axis to mirror across. X, Y or Z?"
            self.mirrorCombo = elements.ComboBoxRegular("Mirror Axis",
                                                        items=XYZ_LIST,
                                                        setIndex=self.properties.mirrorCombo.value,
                                                        parent=parent, toolTip=toolTip)
            self.toolsetWidget.linkProperty(self.mirrorCombo, "mirrorCombo")
            toolTip = "Mirror the joints.  Select only the base of each joint chain to mirror."
            self.mirrorBtn = elements.styledButton("Mirror", "symmetryTri", parent, toolTip=toolTip,
                                                   style=uic.BTN_DEFAULT)
            # Edit LRA ------------------------------------
            toolTip = "Enter component mode and make the local rotation axis selectable\n" \
                      "so that the manipulators can be manually rotated."
            self.editLRABtn = elements.styledButton("Edit LRA",
                                                    "editSpanner",
                                                    toolTip=toolTip,
                                                    parent=parent)
            toolTip = "Exit component mode into object mode and turn off the \n" \
                      "local rotation axis selectability."
            self.exitLRABtn = elements.styledButton("Exit LRA",
                                                    "exit",
                                                    toolTip=toolTip,
                                                    parent=parent)
            # Joint Draw Section
            toolTip = "Set 'Draw Style' joint attribute to be 'Bone', joints will be visualized with bones. (default)"
            self.drawShowBtn = elements.styledButton("Draw Joint", "skeleton", parent, toolTip=toolTip,
                                                     style=uic.BTN_DEFAULT, minWidth=uic.BTN_W_REG_SML)
            toolTip = "Set 'Draw Style' joint attribute to be 'None'. \n" \
                      "Joints become permanently hidden no matter the visibility settings."
            self.drawHideBtn = elements.styledButton("Draw Hide", "skeletonHide", parent, toolTip=toolTip,
                                                     style=uic.BTN_DEFAULT, minWidth=uic.BTN_W_REG_SML)
            # Zero Children Section
            toolTip = "After manually reorienting a joints LRA zero the \n" \
                      "joints Rotate Axis attributes; this will keep the \n" \
                      "joints orientations predictable."
            self.zeroRotAxisBtn = elements.styledButton("Zero Rot Axis", "checkOnly", parent, toolTip=toolTip,
                                                        style=uic.BTN_DEFAULT)
            # Align Joint To Parent Section
            toolTip = "Align the selected joint to its parent.  \n" \
                      "Useful for end joints that have no children to orient towards."
            self.alignParentBtn = elements.styledButton("Align To Parent", "3dManipulator", parent, toolTip=toolTip,
                                                        style=uic.BTN_DEFAULT)
            # labels and dividers ------------------------------------
            self.displayLabel = elements.Label("Display", parent=parent, toolTip=toolTip, bold=True)
            self.displayDivider = elements.Divider(parent=parent)
            self.createLabel = elements.Label("Create", parent=parent, toolTip=toolTip, bold=True)
            self.createDivider = elements.Divider(parent=parent)
            self.orientLabel = elements.Label("Orient", parent=parent, toolTip=toolTip, bold=True)
            self.orientDivider = elements.Divider(parent=parent)
            self.mirrorLabel = elements.Label("Mirror", parent=parent, toolTip=toolTip, bold=True)
            self.mirrorDivider = elements.Divider(parent=parent)
            self.sizeLabel = elements.Label("Size", parent=parent, toolTip=toolTip, bold=True)
            self.sizeDivider = elements.Divider(parent=parent)


class CompactLayout(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None):
        """Adds the layout building the compact version of the GUI:

            default uiMode - 0 is advanced (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(CompactLayout, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                            toolsetWidget=toolsetWidget)
        # Main Layout ------------------------------------
        contentsLayout = elements.vBoxLayout(self,
                                             margins=(uic.WINSIDEPAD,
                                                      uic.WINBOTPAD,
                                                      uic.WINSIDEPAD,
                                                      uic.WINBOTPAD),
                                             spacing=uic.SREG)
        self.setLayout(contentsLayout)
        # Orient Up Section ------------------------------------
        orientBtnLayout = elements.hBoxLayout(self, (0, 0, 0, 0), uic.SREG)
        orientBtnLayout.addWidget(self.orientYPosBtn)
        orientBtnLayout.addWidget(self.orientYNegBtn)
        # Display Local Rotation Axis Section ------------------------------------
        displayBtnLayout = elements.hBoxLayout(self, (0, 0, 0, 0), uic.SREG)
        displayBtnLayout.addWidget(self.showLRABtn)
        displayBtnLayout.addWidget(self.hideLRABtn)
        # Radio roll layout
        radioLayout = elements.hBoxLayout(self, (uic.SVLRG, 0, 0, 0))
        radioLayout.addWidget(self.selHierarchyRadioWidget, 5)
        # Main button layout
        createBtnLayout = elements.hBoxLayout(self, (0, 0, 0, 0), uic.SREG)
        createBtnLayout.addWidget(self.createJntBtn, 10)
        createBtnLayout.addWidget(self.rotateLraNegBtn, 1)
        createBtnLayout.addWidget(self.rotateLraPosBtn, 1)
        # Add to main layout ------------------------------------
        contentsLayout.addLayout(radioLayout)
        contentsLayout.addLayout(orientBtnLayout)
        contentsLayout.addLayout(displayBtnLayout)
        contentsLayout.addLayout(createBtnLayout)
        contentsLayout.addStretch(1)


class AdvancedLayout(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_ADVANCED, toolsetWidget=None):
        """Adds the layout building the advanced version of the GUI:

            default uiMode - 1 is advanced (UI_MODE_ADVANCED)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(AdvancedLayout, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                             toolsetWidget=toolsetWidget)
        # Main Layout ------------------------------------
        contentsLayout = elements.vBoxLayout(self,
                                             margins=(uic.WINSIDEPAD,
                                                      uic.WINBOTPAD,
                                                      uic.WINSIDEPAD,
                                                      uic.WINBOTPAD),
                                             spacing=uic.SREG)
        self.setLayout(contentsLayout)
        # Radio Section ------------------------------------
        radioLayout = elements.hBoxLayout(self, (uic.LRGPAD, 0, uic.LRGPAD, 0))
        radioLayout.addWidget(self.selHierarchyRadioWidget)
        # Orient Up Section ------------------------------------
        orientBtnLayout = elements.hBoxLayout(self, (0, 0, 0, 0), uic.SREG)
        orientBtnLayout.addWidget(self.orientYPosBtn)
        orientBtnLayout.addWidget(self.orientYNegBtn)
        # Display Local Rotation Axis Section ------------------------------------
        displayBtnLayout = elements.hBoxLayout(self, (0, 0, 0, 0), uic.SREG)
        displayBtnLayout.addWidget(self.showLRABtn)
        displayBtnLayout.addWidget(self.hideLRABtn)
        # Draw Joint Section ------------------------------------
        drawBtnLayout = elements.hBoxLayout(self, (0, 0, 0, 0), uic.SREG)
        drawBtnLayout.addWidget(self.drawShowBtn)
        drawBtnLayout.addWidget(self.drawHideBtn)
        # Edit LRA Section ------------------------------------
        editLraLayout = elements.hBoxLayout(self, (0, 0, 0, 0), uic.SREG)
        editLraLayout.addWidget(self.editLRABtn, 1)
        editLraLayout.addWidget(self.exitLRABtn, 1)
        # Mirror Section ------------------------------------
        editLraLayout = elements.hBoxLayout(self, (0, 0, 0, 0), uic.SREG)
        editLraLayout.addWidget(self.editLRABtn, 1)
        editLraLayout.addWidget(self.exitLRABtn, 1)
        # zero self layout ------------------------------------
        zeroParentLayout = elements.hBoxLayout(parent, (0, 0, 0, 0), uic.SREG)
        zeroParentLayout.addWidget(self.alignParentBtn, 1)
        zeroParentLayout.addWidget(self.zeroRotAxisBtn, 1)
        # mirror layout ------------------------------------
        mirrorLayout = elements.hBoxLayout(self, (0, 0, 0, 0), uic.SREG)
        mirrorLayout.addWidget(self.mirrorCombo, 1)
        mirrorLayout.addWidget(self.mirrorBtn, 1)
        # Rotate Btn Layout ------------------------------------
        rotateLayout = elements.hBoxLayout(self, (0, 0, 0, 0), uic.SREG)
        rotateLayout.addWidget(self.rotateCombo, 10)
        rotateLayout.addWidget(self.rotateLraTxt, 6)
        rotateLayout.addWidget(self.rotateLraNegBtn, 1)
        rotateLayout.addWidget(self.rotateLraPosBtn, 1)
        # size layout ------------------------------------
        sizeLayout = elements.hBoxLayout(self, (0, 0, 0, 0), uic.SVLRG)
        sizeLayout.addWidget(self.globalDisplaySizeTxt, 1)
        sizeLayout.addWidget(self.jointRadiusTxt, 1)

        # label layouts ------------------------------------
        displayLabelLayout = elements.hBoxLayout(self, margins=(0, uic.SSML, 0, uic.SSML), spacing=uic.SREG)
        displayLabelLayout.addWidget(self.displayLabel, 1)
        displayLabelLayout.addWidget(self.displayDivider, 10)

        createLabelLayout = elements.hBoxLayout(self, margins=(0, uic.SSML, 0, uic.SSML), spacing=uic.SREG)
        createLabelLayout.addWidget(self.createLabel, 1)
        createLabelLayout.addWidget(self.createDivider, 10)

        orientLabelLayout = elements.hBoxLayout(self, margins=(0, uic.SSML, 0, uic.SSML), spacing=uic.SREG)
        orientLabelLayout.addWidget(self.orientLabel, 1)
        orientLabelLayout.addWidget(self.orientDivider, 10)

        mirrorLabelLayout = elements.hBoxLayout(self, margins=(0, uic.SSML, 0, uic.SSML), spacing=uic.SREG)
        mirrorLabelLayout.addWidget(self.mirrorLabel, 1)
        mirrorLabelLayout.addWidget(self.mirrorDivider, 10)

        sizeLabelLayout = elements.hBoxLayout(self, margins=(0, uic.SSML, 0, uic.SSML), spacing=uic.SREG)
        sizeLabelLayout.addWidget(self.sizeLabel, 1)
        sizeLabelLayout.addWidget(self.sizeDivider, 10)

        # add to main layout ------------------------------------
        contentsLayout.addLayout(radioLayout)

        contentsLayout.addLayout(orientLabelLayout)
        contentsLayout.addLayout(orientBtnLayout)
        contentsLayout.addLayout(editLraLayout)
        contentsLayout.addLayout(zeroParentLayout)
        contentsLayout.addLayout(rotateLayout)

        contentsLayout.addLayout(displayLabelLayout)
        contentsLayout.addLayout(displayBtnLayout)
        contentsLayout.addLayout(drawBtnLayout)

        contentsLayout.addLayout(mirrorLabelLayout)
        contentsLayout.addLayout(mirrorLayout)

        contentsLayout.addLayout(sizeLabelLayout)
        contentsLayout.addLayout(sizeLayout)

        contentsLayout.addLayout(createLabelLayout)
        contentsLayout.addWidget(self.createJntBtn)
        contentsLayout.addStretch(1)
