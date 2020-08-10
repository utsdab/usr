from functools import partial

from Qt import QtWidgets, QtCore

import maya.api.OpenMaya as om2
from maya import cmds

from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.apps.toolsetsui import toolsetui

from zoo.libs.pyqt import uiconstants as uic, keyboardmouse, utils
from zoo.libs.pyqt.widgets import elements
from zoo.libs.maya.cmds.rig import deformers, splines, controls, nodes
from zoo.libs.maya.cmds.objutils import curves, objcolor, shapenodes, filtertypes
from zoo.libs.maya.cmds.general import undodecorator
from zoo.libs.maya import shapelib

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1
SCALE_LIST = ["Scale XYZ", "Scale X", "Scale Y", "ScaleZ"]
DEFAULT_SHAPE_STR = "sphere"


class ControlsOnCurve(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "controlsOnCurve"
    uiData = {"label": "Controls On Curve",
              "icon": "controlsOnCurve",
              "tooltip": "Add clusters to a curve with various options",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-controls-on-curves"
              }

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run"""
        self.controlShapeList = shapelib.shapeNames()
        self.clstrCrvControls = list()
        self.clstrCrvSpline = list()
        self.selObjs = list()  # only used to send to other GUIs

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
        self.toggleTextBoxDisable()  # disable/enable the name textbox depending on autoName checkbox
        self.toggleControlsDisable()  # disable/enable controls section
        if DEFAULT_SHAPE_STR not in self.controlShapeList:  # "sphere" can't be found in the list
            if not self.controlShapeList:  # probably there is an issue with the shapes library, if empty list...
                om2.MGlobal.displayWarning("No Control Shapes found in the Zoo Shapes Library.  "
                                           "Shapes cannot be built!")
            return
        self.properties.shapeCombo.value = self.controlShapeList.index(DEFAULT_SHAPE_STR)  # set sphere as int
        self.updateFromProperties()

    def defaultAction(self):
        """Double Click"""
        pass

    def widgets(self):
        """

        :return:
        :rtype: list[AdvancedLayout or CompactLayout]
        """
        return super(ControlsOnCurve, self).widgets()

    def currentWidget(self):
        """ Currently active widget

        :return:
        :rtype: CompactLayout or AdvancedLayout
        """
        return super(ControlsOnCurve, self).currentWidget()

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
        return [{"name": "name", "value": ""},
                {"name": "autoNameCheckBox", "value": True},
                {"name": "relativeCheckBox", "value": False},
                {"name": "showHandleCheckBox", "value": False},
                {"name": "buildControlsCheckBox", "value": True},
                {"name": "shapeCombo", "value": 6},
                {"name": "scale", "value": 1.0},
                {"name": "color", "value": (0.16, 0.3, 0.875)}]

    def updateFromProperties(self):
        """Updates the properties dictionary and applies values to the GUI.
        Overridden function which automates properties updates. Exposed here in case of extra functionality

        To connect Qt widgets to property methods use:
            self.toolsetWidget.linkProperty(self.widgetQtName, "itemName")
        """
        super(ControlsOnCurve, self).updateFromProperties()
        for widget in self.widgets():  # both GUIs
            widget.scaleTxt.setValue(self.properties.scale.value)

    # ------------------
    # GLOBAL METHODS - SEND/RECEIVE ALL TOOLSETS
    # ------------------

    def global_sendCntrlSelection(self):
        """Updates all GUIs with the current selection memory self.selObjs"""
        toolsets = toolsetui.toolsets(attr="global_receiveCntrlSelection")
        for tool in toolsets:
            tool.global_receiveCntrlSelection(self.selObjs)

    def global_receiveCntrlSelection(self, selObjs):
        """Receives from all GUIs, changes the current selection stored in self.selObjs"""
        self.selObjs = selObjs

    def global_sendCntrlColor(self):
        """Updates all GUIs with the current color"""
        toolsets = toolsetui.toolsets(attr="global_receiveCntrlColor")
        for tool in toolsets:
            tool.global_receiveCntrlColor(self.properties.color.value)

    def global_receiveCntrlColor(self, color):
        """Receives from all GUIs, changes the color"""
        self.properties.color.value = color
        self.updateFromProperties()

    # ------------------
    # UI LOGIC
    # ------------------

    def toggleTextBoxDisable(self):
        """Will disable the name textbox with the autoName checkbox is off"""
        self.advancedWidget.nameTxt.setDisabled(self.properties.autoNameCheckBox.value)

    def toggleControlsDisable(self):
        """Will disable the name textbox with the autoName checkbox is off"""
        disableEnable = not self.properties.buildControlsCheckBox.value
        self.advancedWidget.scaleTxt.setDisabled(disableEnable)
        self.advancedWidget.scalePosBtn.setDisabled(disableEnable)
        self.advancedWidget.scaleNegBtn.setDisabled(disableEnable)
        self.advancedWidget.shapeComboBx.setDisabled(disableEnable)
        self.advancedWidget.colorHsvBtns.setDisabled(disableEnable)
        self.advancedWidget.relativeCheckBx.setDisabled(not disableEnable)
        self.advancedWidget.showHandleCheckBx.setDisabled(not disableEnable)
        self.advancedWidget.relativeCheckBx.setChecked(False)
        self.advancedWidget.showHandleCheckBx.setChecked(False)

    # ------------------
    # COLOR RIGHT CLICK MENU
    # ------------------

    def menuColor(self):
        menuColorTxt = self.advancedWidget.colorBtnMenu.currentMenuItem()
        if menuColorTxt == self.advancedWidget.colorBtnMenuModeList[0][1]:  # the menu text from [0]
            self.getColorSelected()
            return
        elif menuColorTxt == self.advancedWidget.colorBtnMenuModeList[1][1]:  # the menu text from [1]
            self.selectControlsByColor()  # select all objs with color
            return

    # ------------------
    # HELPER LOGIC
    # ------------------

    def updateSelectedRig(self, message=True, deselect=True, objOverride=""):
        """Remembers the object selection so controls/splines can be deselected while changing

        Finds the rig controls and rig main spline control
        Updating self.clstrCrvControls, self.clstrCrvSpline

        Will be empty lists if nothing has been created or selected in the given GUI session.

        :param message: Report the message to the user if nothing selected
        :type message: bool
        :param message: Deselect the objects after recording
        :type message: bool
        :param objOverride: Pass in an object to override the selection, useful after building, bit of a hack.
        :type objOverride: str
        :return isSelection: False if nothing is selected
        :rtype isSelection: bool
        """
        newClstrCrvControls = list()
        clstrCrvSpline = list()
        if cmds.ls(selection=True) and not objOverride:
            newClstrCrvControls = splines.getClstrCrvSelected(message=False)
            clstrCrvSpline = splines.getClstrCrvSelected(message=False, attr=splines.CLSTRCRVE_SPLINE_ATTR)
        elif objOverride:  # from the objOverride return the associated lists, have to get manual
            networkNodeList = splines.getClusterCurveNetworkNodes([objOverride])
            newClstrCrvControls = nodes.getNodeAttrConnections(networkNodeList, splines.CLSTRCRVE_CONTROL_ATTR)
            clstrCrvSpline = nodes.getNodeAttrConnections(networkNodeList, splines.CLSTRCRVE_SPLINE_ATTR)
        if newClstrCrvControls:  # new selection has been found so update
            self.clstrCrvControls = newClstrCrvControls
            self.clstrCrvSpline = clstrCrvSpline
            self.selObjs = newClstrCrvControls
            self.global_sendCntrlSelection()
        else:  # No new selection
            if self.clstrCrvControls:  # Check existing control exists, as it may have been deleted
                if not cmds.objExists(self.clstrCrvControls[0]):  # deleted so reset the memory lists
                    self.clstrCrvControls = list()
                    self.clstrCrvSpline = list()
                    self.selObjs = list()
                    self.global_updateCntrlSelection()
        if not self.clstrCrvControls:
            om2.MGlobal.displayWarning("Please select controls/curves of the cluster curve rig.")
            return False
        if deselect:
            cmds.select(deselect=True)
        return True

    # ------------------
    # MAIN LOGIC
    # ------------------

    def createSplineRig(self, scaleXYZ):
        """Creates the spline Rig"""
        design = self.controlShapeList[self.properties.shapeCombo.value]
        name = ""
        if not self.properties.autoNameCheckBox.value:
            name = self.properties.name.value
        spline = splines.controlsClusterCurveSelected(partPrefixName=name,
                                                      scale=scaleXYZ,
                                                      design=design,
                                                      relative=False,
                                                      showHandles=False,
                                                      rgbColor=self.properties.color.value,
                                                      padding=2)
        if spline:
            self.updateSelectedRig(objOverride=spline)

    @undodecorator.undoDecorator
    def clusterCurve(self):
        """Main function, uses the GUI to add clusters to a curve in Maya"""
        partPrefixName = ""
        scale = self.properties.scale.value
        scaleXYZ = (scale, scale, scale)
        if self.displayIndex() == UI_MODE_COMPACT:  # hardcode for compact mode
            self.createSplineRig(scaleXYZ)
            return
        if self.properties.name.value and not self.properties.autoNameCheckBox.value:
            partPrefixName = self.properties.name.value
        if not self.properties.buildControlsCheckBox.value:  # don't build controls
            deformers.createClustersOnCurveSelection(partPrefixName,
                                                     relative=self.properties.relativeCheckBox.value,
                                                     showHandles=self.properties.showHandleCheckBox.value)
        else:
            self.createSplineRig(scaleXYZ)

    def createCurveContext(self):
        """Enters the create curve context (user draws cvs).  Uses mel hardcoded 3 bezier curve.
        """
        curves.createCurveContext(degrees=3)

    @undodecorator.undoDecorator
    def deleteClusterCurveSelected(self):
        """Removes the rig, and optionally the original spline curve of a controlsClusterCurve() setup"""
        self.updateSelectedRig(message=True, deselect=True)  # updates self.clstrCrvControls, self.clstrCrvSpline
        if not self.clstrCrvControls:  # already messages
            return
        splines.deleteClusterCurve(self.clstrCrvControls, deleteSpline=False, message=True)

    @undodecorator.undoDecorator
    def toggleVis(self):
        """Toggles the vis of the controls and curve for the cluster curve spline rig"""
        self.updateSelectedRig(message=True, deselect=True)  # updates self.clstrCrvControls, self.clstrCrvSpline
        if not self.clstrCrvControls:  # already messages
            return
        splines.toggleVisClusterCurve(self.clstrCrvControls)

    @undodecorator.undoDecorator
    def toggleTemplate(self):
        """Toggles the vis of the controls and curve for the cluster curve spline rig"""
        self.updateSelectedRig(message=True, deselect=True)  # updates self.clstrCrvControls, self.clstrCrvSpline
        if not self.clstrCrvControls:  # already messages
            return
        splines.toggleTemplateClusterCurve(self.clstrCrvControls)

    @undodecorator.undoDecorator
    def scaleOffsetControls(self, positive=True):
        """UI function that scales all controls from any selected part of the rig, does not affect transform scale

        :param positive: is the scale bigger positive=True, or smaller positive=False
        :type positive: bool
        """
        multiplier, reset = keyboardmouse.cntrlShiftMultiplier()  # for alt shift and ctrl keys with left click
        self.updateSelectedRig(message=True, deselect=True)  # updates self.clstrCrvControls, self.clstrCrvSpline
        if not self.clstrCrvControls:  # already messages
            return
        scale = 5.0
        if reset:  # try to reset with the zoo scale tracker (if it exists)
            controls.resetScaleList(self.clstrCrvControls)
        else:  # do the scale offset
            scale = scale * multiplier  # if control or shift is held down
            if positive:
                scale = 1 + (scale * .01)  # 5.0 becomes 1.05
            else:  # negative
                scale = 1 - (scale * .01)  # 5.0 becomes 0.95
            scaleList = [scale, scale, scale]
            controls.scaleAndTrackControlList(self.clstrCrvControls, scaleList)
        # update ui
        # get 0 control's scale
        self.properties.scale.value = controls.getCreateControlScale(self.clstrCrvControls[0])[0]
        self.updateFromProperties()

    @undodecorator.undoDecorator
    def scaleControlsExact(self, nullTxt=""):
        """Scales all controls from any selected part of the rig, to an exact size give by the GUI"""
        scale = self.properties.scale.value
        self.updateSelectedRig(message=True, deselect=True)  # updates self.clstrCrvControls, self.clstrCrvSpline
        if not self.clstrCrvControls:  # already messages
            return
        controls.scaleControlAbsoluteList((scale, scale, scale), self.clstrCrvControls)

    @undodecorator.undoDecorator
    def replaceWithShapeDesign(self, null="", null2="", null3="", message=True):
        """Replaces the curves from the combo box shape design list

        :param null: Not used, combo boxes must pass in values
        :type null:
        :param null2: Not used, combo boxes must pass in values
        :type null2:
        :param null3: Not used, combo boxes must pass in values
        :type null3:
        :param message: Report the message to the user?
        :type message: bool
        """
        self.updateSelectedRig(message=True, deselect=True)  # updates self.clstrCrvControls, self.clstrCrvSpline
        if not self.clstrCrvControls:  # already messages
            return
        controls.replaceWithShapeDesignList(self.clstrCrvControls,
                                            designName=self.controlShapeList[self.properties.shapeCombo.value],
                                            autoScale=True,
                                            message=message)

    @undodecorator.undoDecorator
    def colorSelected(self, color):
        """Change the selected control color (and potential children) when the color is changed if a selection"""
        self.updateSelectedRig(message=True, deselect=True)  # updates self.clstrCrvControls, self.clstrCrvSpline
        if not self.clstrCrvControls:  # already messages
            return
        curves = self.clstrCrvControls + self.clstrCrvSpline
        objcolor.setColorListRgb(curves, color, displayMessage=False, linear=True)

    @undodecorator.undoDecorator
    def offsetColorSelected(self, offsetTuple, resetClicked):
        """Offset the selected control color (and potential children) when the color is changed if there's a selection

        :param offsetTuple: The offset as (hue, saturation, value)
        :type offsetTuple: tuple
        :param resetClicked: Has the reset been activated (alt clicked)
        :type resetClicked: bool
        """
        self.properties.color.value = self.advancedWidget.colorHsvBtns.colorLinearFloat()
        self.updateSelectedRig(message=True, deselect=True)  # updates self.clstrCrvControls, self.clstrCrvSpline
        if not self.clstrCrvControls:  # already messages
            return
        curves = self.clstrCrvControls + self.clstrCrvSpline
        if resetClicked:  # set default color
            self.colorSelected(self.properties.color.default)
            return
        # Do the offset ------------------
        offsetFloat, hsvType = objcolor.convertHsvOffsetTuple(offsetTuple)
        objcolor.offsetListHsv(curves, offset=offsetFloat, hsvType=hsvType)
        # update properties from the color swatch

    def setColor(self):
        """Sets the color to the control based on the GUI"""
        self.colorSelected(self.properties.color.value)

    def getColorSelected(self):
        """Gets the color of the selected curve shapes"""
        curveTransformList = filtertypes.filterByNiceTypeKeepOrder(filtertypes.CURVE,
                                                                   searchHierarchy=False,
                                                                   selectionOnly=True,
                                                                   dag=False,
                                                                   removeMayaDefaults=False,
                                                                   transformsOnly=True,
                                                                   message=True)
        if not curveTransformList:
            om2.MGlobal.displayWarning("Please select a curve object (transform)")
            return
        firstShapeNode = shapenodes.filterShapesInList(curveTransformList)[0]  # must be a curve
        self.properties.color.value = objcolor.getRgbColor(firstShapeNode, hsv=False, linear=True)
        self.updateFromProperties()  # update ui

    def selectControlsByColor(self):
        """Selects all curves with the matching color"""
        curveTransformList = filtertypes.filterByNiceTypeKeepOrder(filtertypes.CURVE,
                                                                   searchHierarchy=False,
                                                                   selectionOnly=False,
                                                                   dag=False,
                                                                   removeMayaDefaults=False,
                                                                   transformsOnly=True,
                                                                   message=True)
        if not curveTransformList:
            om2.MGlobal.displayWarning("No curve objects found in the scene")
            return
        objcolor.selectObjsByColor(curveTransformList, self.properties.color.value, message=True)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        for widget in self.widgets():  # both GUIs
            widget.clusterCurveBtn.clicked.connect(self.clusterCurve)
            widget.curveCvBtn.clicked.connect(self.createCurveContext)
            widget.deleteBtn.clicked.connect(self.deleteClusterCurveSelected)
            widget.hideBtn.clicked.connect(self.toggleVis)
            widget.templateBtn.clicked.connect(self.toggleTemplate)
            widget.scaleNegBtn.clicked.connect(partial(self.scaleOffsetControls, positive=False))
            widget.scalePosBtn.clicked.connect(partial(self.scaleOffsetControls, positive=True))
            widget.scaleTxt.textModified.connect(self.scaleControlsExact)
            widget.shapeComboBx.itemChanged.connect(self.replaceWithShapeDesign)
        self.advancedWidget.autoNameCheckBx.stateChanged.connect(self.toggleTextBoxDisable)
        self.advancedWidget.buildControlsCheckBx.stateChanged.connect(self.toggleControlsDisable)
        self.advancedWidget.colorHsvBtns.colorChanged.connect(self.colorSelected)
        self.advancedWidget.applyColorBtn.clicked.connect(self.setColor)
        self.advancedWidget.colorHsvBtns.offsetClicked.connect(self.offsetColorSelected)
        self.advancedWidget.colorBtnMenu.menuChanged.connect(self.menuColor)


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
        self.controlShapeList = shapelib.shapeNames()
        # Cluster Curve Button
        toolTip = "Select a curve and run, will add clusters to all curve CVs"
        self.clusterCurveBtn = elements.styledButton("Build Controls Selected", "controlsOnCurve",
                                                     self,
                                                     toolTip=toolTip,
                                                     style=uic.BTN_DEFAULT)
        # Controls Section  ------------------------------------
        toolTip = "Replace curves with the following shapes.\n" \
                  "If Auto Apply is on will instantly apply to the selection."
        self.shapeComboBx = elements.ComboBoxSearchable("",
                                                        self.controlShapeList,
                                                        self,
                                                        labelRatio=4,
                                                        boxRatio=6,
                                                        toolTip=toolTip,
                                                        setIndex=self.properties.shapeCombo.value)
        self.toolsetWidget.linkProperty(self.shapeComboBx, "shapeCombo")
        # Scale Section ------------------------------------
        toolTip = "Scale in Maya units usually cms.  Scale is the control's radius, not width."
        self.scaleTxt = elements.FloatEdit("Scale",
                                           self.properties.scale.value,
                                           parent=self,
                                           toolTip=toolTip,
                                           rounding=2)
        self.toolsetWidget.linkProperty(self.scaleTxt, "scale")
        toolTip = "Scales smaller by 5%. Select any rig object and run\n" \
                  "Hold shift for faster, ctrl for slower and alt for reset."
        self.scalePosBtn = elements.styledButton("",
                                                 "scaleUp",
                                                 toolTip=toolTip,
                                                 parent=self,
                                                 minWidth=uic.BTN_W_ICN_MED)
        toolTip = "Scales smaller by 5%. Select any rig object and run\n" \
                  "Hold shift for faster, ctrl for slower and alt for reset."
        self.scaleNegBtn = elements.styledButton("",
                                                 "scaleDown",
                                                 toolTip=toolTip,
                                                 parent=self,
                                                 minWidth=uic.BTN_W_ICN_MED)
        # Create CV Curve ------------------------------------
        toolTip = "Create a CV Curve (3 Cubic)"
        self.curveCvBtn = elements.styledButton("",
                                                "curveCv",
                                                toolTip=toolTip,
                                                parent=self,
                                                minWidth=uic.BTN_W_ICN_MED)
        toolTip = "Toggle template the main Curve, template/untemplate," \
                  "Select any rig object and run"
        self.templateBtn = elements.styledButton("",
                                                 "templateObj",
                                                 toolTip=toolTip,
                                                 parent=self,
                                                 minWidth=uic.BTN_W_ICN_MED)
        toolTip = "Toggle the visibility of the controls and clusters.\n" \
                  "Select any rig object and run"
        self.hideBtn = elements.styledButton("",
                                             "eye",
                                             toolTip=toolTip,
                                             parent=self,
                                             minWidth=uic.BTN_W_ICN_MED)
        toolTip = "Delete the Cluster Curve Spline rig, controls and clusters.\n" \
                  "Select any rig object and run."
        self.deleteBtn = elements.styledButton("",
                                               "trash",
                                               toolTip=toolTip,
                                               parent=self,
                                               minWidth=uic.BTN_W_ICN_MED)

        if uiMode == UI_MODE_ADVANCED:
            # Name Line Edit
            toolTip = "The name prefix of each cluster. \n" \
                      "If auto is on then will prefix with the curve's name"
            self.nameTxt = elements.StringEdit("Name",
                                               self.properties.name.value,
                                               parent=self,
                                               toolTip=toolTip,
                                               labelRatio=1,
                                               editRatio=3)
            self.toolsetWidget.linkProperty(self.nameTxt, "name")
            # Auto Name Checkbox
            toolTip = "Auto adds a prefix using the curve's name\n" \
                      "If off prefixes with the text box name (above)"
            self.autoNameCheckBx = elements.CheckBox("Auto Name",
                                                     self.properties.autoNameCheckBox.value,
                                                     parent=self,
                                                     toolTip=toolTip)
            self.toolsetWidget.linkProperty(self.autoNameCheckBx, "autoNameCheckBox")
            # Relative Checkbox
            toolTip = "If on the cluster deformation won't be affected by the clusters parent/s.\n" \
                      "Deformation are only made by transforming the clusters themselves."
            self.relativeCheckBx = elements.CheckBox("Relative",
                                                     self.properties.relativeCheckBox.value,
                                                     parent=self,
                                                     toolTip=toolTip)
            self.toolsetWidget.linkProperty(self.relativeCheckBx, "relativeCheckBox")
            # Show Handles Checkbox
            toolTip = "Displays a Maya handle (small black cross) for each cluster"
            self.showHandleCheckBx = elements.CheckBox("Handles",
                                                       self.properties.showHandleCheckBox.value,
                                                       parent=self,
                                                       toolTip=toolTip)
            self.toolsetWidget.linkProperty(self.showHandleCheckBx, "showHandleCheckBox")
            # Build Controls Checkbox
            toolTip = "Build controls on each cluster"
            self.buildControlsCheckBx = elements.CheckBox("Controls",
                                                          self.properties.buildControlsCheckBox.value,
                                                          parent=self,
                                                          toolTip=toolTip)
            self.toolsetWidget.linkProperty(self.buildControlsCheckBx, "buildControlsCheckBox")
            # Color Section ------------------------------------
            toolTip = "The color of the new control, if existing curves are selected will instantly change colors"
            self.colorHsvBtns = elements.MayaColorHsvBtns(text="Color",
                                                          color=self.properties.color.value,
                                                          parent=self,
                                                          toolTip=toolTip,
                                                          btnRatio=4,
                                                          labelRatio=2,
                                                          colorWidgetRatio=21,
                                                          hsvRatio=15,
                                                          middleSpacing=uic.SVLRG,
                                                          resetColor=self.properties.color.value)
            self.toolsetWidget.linkProperty(self.colorHsvBtns, "color")
            self.colorBtnMenuModeList = [("paintLine", "Get Color From Curve"),
                                         ("cursorSelect", "Select Ctrls With Color")]
            self.colorBtnMenu = elements.ExtendedMenu(searchVisible=True)
            self.colorHsvBtns.setMenu(self.colorBtnMenu, modeList=self.colorBtnMenuModeList)  # right click
            self.colorHsvBtns.setMenu(self.colorBtnMenu,
                                      mouseButton=QtCore.Qt.LeftButton)  # left click, modes set already
            toolTip = "Apply the GUI color to selected controls."
            self.applyColorBtn = elements.styledButton("",
                                                       "paintLine",
                                                       toolTip=toolTip,
                                                       parent=self,
                                                       minWidth=uic.BTN_W_ICN_MED,
                                                       maxWidth=uic.BTN_W_ICN_MED)


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
        # Controls layout ------------------------------------
        controlsLayout = elements.hBoxLayout(self, margins=(0, 0, 0, uic.SMLPAD), spacing=uic.SLRG)
        controlsLayout.addWidget(self.shapeComboBx, 12)
        controlsLayout.addWidget(self.scaleTxt, 8)
        controlsLayout.addWidget(self.scaleNegBtn, 1)
        controlsLayout.addWidget(self.scalePosBtn, 1)
        # create layout ------------------------------------
        createLayout = elements.hBoxLayout(self, margins=(0, 0, 0, 0), spacing=uic.SLRG)
        createLayout.addWidget(self.curveCvBtn, 1)
        createLayout.addWidget(self.clusterCurveBtn, 20)
        createLayout.addWidget(self.hideBtn, 1)
        createLayout.addWidget(self.templateBtn, 1)
        createLayout.addWidget(self.deleteBtn, 1)
        # Add to main layout ------------------------------------
        contentsLayout.addLayout(controlsLayout)
        contentsLayout.addLayout(createLayout)
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
        # Checkbox layout ------------------------------------
        checkBoxLayout = elements.hBoxLayout(self, margins=(0, uic.SMLPAD, 0, uic.SMLPAD), spacing=uic.SLRG)
        checkBoxLayout.addWidget(self.buildControlsCheckBx, 1)
        checkBoxLayout.addWidget(self.autoNameCheckBx, 1)
        checkBoxLayout.addWidget(self.relativeCheckBx, 1)
        checkBoxLayout.addWidget(self.showHandleCheckBx, 1)
        # Controls layout ------------------------------------
        controlsLayout = elements.hBoxLayout(self, margins=(0, 0, 0, 0), spacing=uic.SLRG)
        controlsLayout.addWidget(self.shapeComboBx, 12)
        controlsLayout.addWidget(self.scaleTxt, 8)
        controlsLayout.addWidget(self.scaleNegBtn, 1)
        controlsLayout.addWidget(self.scalePosBtn, 1)
        # color shape/design Layout ------------------------------------
        colorLayout = elements.hBoxLayout(parent, margins=(0, 0, 0, uic.SMLPAD), spacing=uic.SVLRG)
        colorLayout.addWidget(self.colorHsvBtns, 24)
        colorLayout.addWidget(self.applyColorBtn, 1)
        # create layout ------------------------------------
        createLayout = elements.hBoxLayout(parent, margins=(0, 0, 0, 0), spacing=uic.SLRG)
        createLayout.addWidget(self.curveCvBtn, 1)
        createLayout.addWidget(self.clusterCurveBtn, 20)
        createLayout.addWidget(self.hideBtn, 1)
        createLayout.addWidget(self.templateBtn, 1)
        createLayout.addWidget(self.deleteBtn, 1)
        # Add to main layout ------------------------------------
        contentsLayout.addWidget(self.nameTxt)
        contentsLayout.addLayout(checkBoxLayout)
        contentsLayout.addLayout(controlsLayout)
        contentsLayout.addLayout(colorLayout)
        contentsLayout.addLayout(createLayout)
        contentsLayout.addStretch(1)
