import os
from functools import partial

from zoo.libs.zooscene import zooscenefiles
from Qt import QtWidgets, QtCore

import maya.cmds as cmds
import maya.api.OpenMaya as om2

from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.libs.maya.cmds.general import undodecorator
from zoo.libs import iconlib
from zoo.libs.pyqt import utils as qtutils
from zoo.apps.toolsetsui import toolsetui

from zoo.libs.utils import filesystem
from zoo.libs.pyqt import uiconstants as uic, keyboardmouse
from zoo.libs.pyqt.widgets import elements
from zoo.libs.maya import shapelib
from zoo.libs.maya.cmds.objutils import shapenodes, objcolor, filtertypes, matching, namehandling

from zoo.libs.maya.cmds.rig import controls
from zoo.apps.controls_joints import controlsjointsconstants as cc
from zoo.apps.controls_joints import controlsdirectories

from zoo.preferences.core import preference

THEME_PREFS = preference.interface("core_interface")

TRANSLATE_LIST = ["Translate X", "Translate Y", "Translate Z"]
UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1
DEFAULT_SHAPE_STR = "circle"
MIRROR_AXIS = ["X", "Y", "Z"]


class EditControls(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "editControls"
    uiData = {"label": "Edit Controls",
              "icon": "pliers",
              "tooltip": "Create Curve Controls",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-edit-controls/"
              }

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run"""
        self.selObjs = list()  # Remember the last objects selected if nothing selected
        self.setupPrefsDirectory()  # sets up the full shape library list self.controlShapeList
        self.breakObj = ""  # the break object, useful for replace
        self.copyCtrl = ""
        self.copyTranslate = None
        self.copyRotate = None
        self.copyScale = None
        self.copyColor = None
        self.copyShape = ""

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget(), self.initAdvancedWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        parent = QtWidgets.QWidget(parent=self)
        self.compactWidget = CompactLayout(parent=parent, properties=self.properties, toolsetWidget=self)
        return parent

    def initAdvancedWidget(self):
        """Builds the Advanced GUI (self.advancedWidget) """
        parent = QtWidgets.QWidget(parent=self)
        self.advancedWidget = AdvancedLayout(parent=parent, properties=self.properties, toolsetWidget=self)
        return parent

    def postContentSetup(self):
        """Last of the initialize code"""

        self.uiConnections()
        if DEFAULT_SHAPE_STR not in self.controlShapeList:  # "circle" can't be found in the list
            if not self.controlShapeList:  # probably there is an issue with the shapes library, if empty list.
                om2.MGlobal.displayWarning("No Control Shapes found in the Zoo Shapes Library.  "
                                           "Shapes cannot be built!")
            return
        self.properties.shapeCombo.value = self.controlShapeList.index(DEFAULT_SHAPE_STR)  # set sphere as int

    def defaultAction(self):
        """Double Click"""
        return

    def currentWidget(self):
        """Returns the current widget class eg. self.compactWidget or self.advancedWidget

        Over ridden class
        """
        return self.widgets()[self.displayIndex()].children()[0]

    # ------------------
    # PROPERTIES
    # ------------------

    def initializeProperties(self):
        """Used to store and update UI data, sets default values

        For use in the GUI use:
            current value: self.properties.itemName.value
            default value (automatic): self.properties.itemName.default

        To connect Qt widgets to property methods use:
            self.toolsetWidget.linkProperty(self.widgetQtName, "itemName")

        :return properties: special dictionary used to save and update all GUI widgets
        :rtype properties: list(dict)
        """
        return [{"name": "orientCombo", "value": 0},
                {"name": "buildStyle", "value": 0},
                {"name": "rotateCombo", "value": 0},
                {"name": "color", "value": (0.16, 0.3, 0.875)},
                {"name": "shapeCombo", "value": 4},
                {"name": "scaleCombo", "value": 0},
                {"name": "translateCombo", "value": 1},
                {"name": "ctrlSize", "value": 2.0},
                {"name": "scaleVector", "value": (1.0, 1.0, 1.0)},
                {"name": "rotateVector", "value": (0.0, 0.0, 0.0)},
                {"name": "translateVector", "value": (0.0, 0.0, 0.0)},
                {"name": "selHierarchyRadio", "value": 0},
                {"name": "grpJointsCheckBox", "value": 1},
                {"name": "freezeJntsCheckBox", "value": 1},
                {"name": "lineWidth", "value": -1},
                {"name": "mirrorAxisCombo", "value": 0},
                {"name": "mirrorReplaceTxt", "value": "_L _R"},
                {"name": "flipAxisCombo", "value": 0}]

    def updateFromProperties(self):
        """Updates the properties dictionary and applies values to the GUI.
        Overridden function which automates properties updates. Exposed here in case of extra functionality

        To connect Qt widgets to property methods use:
            self.toolsetWidget.linkProperty(self.widgetQtName, "itemName")
        """
        # limit the decimal places in the GUI
        super(EditControls, self).updateFromProperties()
        scaleVector = list()
        rotateVector = list()
        translateVector = list()
        for i, val in enumerate(self.properties.translateVector.value):  # create the new lists with decimal limits
            scaleVector.append(self.properties.rotateVector.value[i])
            rotateVector.append(self.properties.scaleVector.value[i])
            translateVector.append(self.properties.translateVector.value[i])
        self.advancedWidget.scaleTxt.setValue(self.properties.ctrlSize.value)
        self.advancedWidget.scaleVectorTxt.setValue(scaleVector)
        self.advancedWidget.rotateVectorTxt.setValue(rotateVector)
        self.advancedWidget.translateVectorTxt.setValue(translateVector)

    # ------------------
    # POPUP GUI WINDOWS
    # ------------------

    def saveCurvesPopupWindow(self, newControlName):
        """Save control curve popup window with a new name text entry

        :param newControlName: The name of the selected curve transform
        :type newControlName: str
        :return newControlName: The name of the control curve that will be saved to disk *.shape
        :rtype newControlName: str
        """
        message = "Save Selected Curve Control?"
        # TODO need to specify a parent as the Maya window, current stylesheet issues with self.parent
        newControlName = elements.InputDialog(windowName="Save Curve Control", textValue=newControlName,
                                              parent=None, message=message)
        return newControlName

    def deleteCurvesPopupWindow(self, shapeName):
        """Delete control curve popup window asking if the user is sure they want to delete?

        :param shapeName: The name of the shape/design to be deleted from the library on disk
        :type shapeName: str
        :return okState: Ok button was pressed
        :rtype okState: bool
        """
        message = "Are you sure you want to delete `{0}` from the Zoo Curve Library?\n" \
                  "This will permanently delete the file `{0}.shape` from disk.".format(shapeName)
        # TODO need to specify a parent as the Maya window, current stylesheet issues with self.parent
        okState = elements.MessageBox_ok(windowName="Delete Curve From Library",
                                         parent=None, message=message)
        return okState

    def renameCurvesPopupWindow(self, existingControlName):
        """Rename control curve popup window with a new name text entry

        :param existingControlName: The name of the name of the shape to be renamed
        :type existingControlName: str
        :return newControlName: The name of the control to be renamed, without the file extension
        :rtype newControlName: str
        """
        message = "Rename `{}` in the Zoo library to a new name.\n" \
                  "File will be renamed on disk".format(existingControlName)
        # TODO need to specify a parent as the Maya window, current stylesheet issues with self.parent
        newControlName = elements.InputDialog(windowName="Rename Curve/Design In Library",
                                              textValue=existingControlName,
                                              parent=None, message=message)
        return newControlName

    # ------------------------------------
    # UTILS
    # ------------------------------------

    def refreshPrefs(self):
        """Refreshes the preferences reading and updating from the json preferences file

        :return success: True if successful
        :rtype success: bool
        """
        self.controlsJointsPrefsData = preference.findSetting(cc.RELATIVE_PREFS_FILE, None)  # model asset .prefs info
        if self.controlsJointsDirectory():  # updates self.directory
            return True
        return False

    def refreshShapeDesignComboBox(self, setItemText="", setItemIndex=0):
        """Refresh GUI ComboBox"""
        self.controlsJointsDirectory()  # updates self.controlShapeList

        self.advancedWidget.shapeComboBx.blockSignals(True)
        self.advancedWidget.shapeComboBx.clear()
        self.advancedWidget.shapeComboBx.addItems(self.controlShapeList)
        if setItemText:
            index = self.controlShapeList.index(setItemText)
            self.advancedWidget.shapeComboBx.setCurrentIndex(index)
            self.properties.shapeCombo.value = index
        elif setItemIndex:
            self.advancedWidget.shapeComboBx.setCurrentIndex(setItemIndex)
            self.properties.shapeCombo.value = setItemIndex
        else:
            self.properties.shapeCombo.value = 0  # first entry
        self.advancedWidget.shapeComboBx.blockSignals(False)

    def fullRefreshComboList(self):
        """full refreshes the combo list from the json file on disk"""
        self.currentWidget().searchWidget.setSearchText("")
        self.refreshPrefs()
        self.refreshShapeDesignComboBox()

    def setupPrefsDirectory(self):
        """Sets up retrieves the preferences directory information. Sets up:

            self.controlsJointsPrefsData
            self.directory

        """
        # Preferences directory
        self.controlsJointsPrefsData = preference.findSetting(cc.RELATIVE_PREFS_FILE, None)  # model asset .prefs info
        self.controlsJointsDirectory()  # creates/updates self.directory
        if not self.directory:  # directory can be empty if preferences window hasn't been opened
            # so update the preferences json file with default locations
            self.controlsJointsPrefsData = controlsdirectories.buildUpdateControlsJointsPrefs(
                self.controlsJointsPrefsData)
            self.controlsJointsDirectory()  # creates/updates self.directory

    def controlsJointsDirectory(self):
        """Convenience function for updating self.directory

        Does not reload from the preferences json file

        :return self.directory: The path of the current directory for the control shapes
        :rtype self.directory: str
        """
        if not self.controlsJointsPrefsData.isValid():  # should be very rare
            om2.MGlobal.displayError("The preferences object is not valid")
            return ""
        self.directory = self.controlsJointsPrefsData["settings"][cc.PREFS_KEY_CONTROL_SHAPES]
        # todo get list from self.directory at the moment just pulls from the default os.env variable
        self.controlShapeList = shapelib.shapeNames()  # the full shape library list
        return self.directory

    # ------------------
    # RIGHT CLICK MENU
    # ------------------

    def menuColor(self):
        """Runs when a color right-click menu item is clicked"""

        menuColorTxt = self.advancedWidget.colorBtnMenu.currentMenuItem()
        if menuColorTxt == self.advancedWidget.colorBtnMenuModeList[0][1]:  # the menu text from [0]
            self.getColorSelected()
        elif menuColorTxt == self.advancedWidget.colorBtnMenuModeList[1][1]:  # the menu text from [1]
            self.getColorSelected(selectMode=True)  # select similar to the selected object
        elif menuColorTxt == self.advancedWidget.colorBtnMenuModeList[2][1]:  # the menu text from [2]
            self.selectControlsByColor()  # select all objs with color

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
    # HELPER LOGIC
    # ------------------

    def filterCurveTransformsOnlyUpdateSelObj(self, disableHierarchy=False, deselect=True):
        """Return only transforms with curve shapes, also update the selection memory, self.selObjs"""
        if disableHierarchy:
            children = False
        else:
            children = self.properties.selHierarchyRadio.value
        if not self.updateSelectedObjs(message=False, deselect=deselect):  # updates self.selObjs
            return list()  # message reported
        # check shapes are curves and return the list
        return filtertypes.filterTypeReturnTransforms(self.selObjs,
                                                      children=children,
                                                      shapeType="nurbsCurve")

    def updateSelectedObjs(self, message=True, deselect=True):
        """Remembers the object selection so controls can be deselected while changing

        Updates self.selObjs

        :param message: Report the message to the user if nothing selected
        :type message: bool
        :param message: Deselect the objects after recording
        :type message: bool
        :return isSelection: False if nothing is selected
        :rtype isSelection: bool
        """
        newSelection = cmds.ls(selection=True, long=True)
        if newSelection:
            self.selObjs = newSelection
            self.global_sendCntrlSelection()  # updates all windows
        if not self.selObjs:
            if message:
                om2.MGlobal.displayWarning("Please select controls/curves.")
            return False
        if deselect:
            cmds.select(deselect=True)
        return True

    # ------------------
    # MAIN LOGIC
    # ------------------

    def buildControlsAll(self):
        """Builds all styles depending on the combo value

        TODO: Undo not yet supported
        """
        # Build from scratch
        rotateOffset = controls.convertRotateUpList(self.properties.orientCombo.value)
        scale = [self.properties.ctrlSize.value, self.properties.ctrlSize.value, self.properties.ctrlSize.value]
        buildType = controls.CONTROL_BUILD_TYPE_LIST[self.properties.buildStyle.value]
        controlList = controls.buildControlsGUI(buildType=buildType,
                                                designName=self.controlShapeList[self.properties.shapeCombo.value],
                                                rotateOffset=rotateOffset,
                                                scale=scale,
                                                children=self.properties.selHierarchyRadio.value,
                                                rgbColor=self.properties.color.value,
                                                postSelectControls=True,
                                                trackScale=True,
                                                lineWidth=self.properties.lineWidth.value,
                                                grp=self.properties.grpJointsCheckBox.value,
                                                freezeJnts=self.properties.freezeJntsCheckBox.value)
        self.selObjs = controlList
        self.global_sendCntrlSelection()

    def filterCurveJoining(self):
        """Filters the curves for joining, either combine or replace

        The first objects (not the last) must include nurbsCurves, and the last object must be a transform or joint
        If so then return the object list, otherwise returns an empty list
        :return objList: An object list now checked, will be empty if the filtering failed.
        :rtype objList: list(str)
        """
        selObjs = cmds.ls(selection=True, long=True)
        firstObjs = selObjs[:-1]
        lastObject = selObjs[-1]
        nodeType = cmds.nodeType(lastObject)
        if nodeType != "transform" and nodeType != "joint":
            om2.MGlobal.displayWarning("The last object must be an object (transform) or a joint, please reselect")
            return list()
        firstObjs = filtertypes.filterTypeReturnTransforms(firstObjs,
                                                           children=False,
                                                           shapeType="nurbsCurve")
        if not firstObjs:
            om2.MGlobal.displayWarning("The first selected objects must have valid curve shapes, please reselect")
            return list()
        firstObjs.append(lastObject)
        objList = firstObjs
        return objList

    @toolsetwidgetmaya.undoDecorator
    def combineCurves(self):
        """Combines multiple selected curves under one transform, parent is the last selected object"""
        objList = self.filterCurveJoining()
        if not objList:  # then no shapes as nurbsCurves
            return
        combinedObject = shapenodes.shapeNodeParentSafe(objList, deleteOriginal=False, reportSuccess=True,
                                                        selectObj=True, delShapeType="nurbsCurve")
        self.selObjs = [combinedObject]

    @toolsetwidgetmaya.undoDecorator
    def replaceCurves(self):
        """Replaces the curves of one shape node from another.  Last selected object remains with it's shape switched"""
        objList = self.filterCurveJoining()
        combinedObject = shapenodes.shapeNodeParentSafe(objList, deleteOriginal=True, reportSuccess=True,
                                                        selectObj=True, delShapeType="nurbsCurve")
        self.selObjs = [combinedObject]

    def replaceWithShapeDesign(self, message=True):
        """Replaces the curves from the combo box shape design list

        TODO: Undo not yet supported

        :param message: Report the message to the user?
        :type message: bool
        """
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj()
        if not curveTransforms:  # then no shapes as nurbsCurves
            return
        designName = self.controlShapeList[self.properties.shapeCombo.value]
        rotateOffset = controls.convertRotateUpList(self.properties.orientCombo.value)
        controls.replaceControlCuves(curveTransforms,
                                     designName=designName,
                                     rotateOffset=rotateOffset,
                                     autoScale=True,
                                     message=False)
        om2.MGlobal.displayInfo("Controls changed to `{}`: {}".format(designName,
                                                                      namehandling.getShortNameList(curveTransforms)))

    @toolsetwidgetmaya.undoDecorator
    def scaleCVs(self, positive=True):
        """UI function that scales nurbs curve objects based on their CVs, will not affect transforms

        :param positive: is the scale bigger positive=True, or smaller positive=False
        :type positive: bool
        """
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj()
        if not curveTransforms:  # then no shapes as nurbsCurves
            return
        multiplier, reset = keyboardmouse.cntrlShiftMultiplier()  # for alt shift and ctrl keys with left click
        scale = 5.0
        if reset:  # try to reset with the zoo scale tracker (if it exists)
            controls.scaleResetBrkCnctCtrlList(curveTransforms)
            cmds.select(deselect=True)
            return
        scale = scale * multiplier  # if control or shift is held down
        if positive:
            scale = 1 + (scale * .01)  # 5.0 becomes 1.05
        else:  # negative
            scale = 1 - (scale * .01)  # 5.0 becomes 0.95
        scaleComboIndex = self.properties.scaleCombo.value
        if scaleComboIndex == 0:  # all xyz
            scaleXYZ = [scale, scale, scale]
        elif scaleComboIndex == 1:  # x only
            scaleXYZ = [scale, 1, 1]
        elif scaleComboIndex == 2:  # y only
            scaleXYZ = [1, scale, 1]
        else:  # z only
            scaleXYZ = [1, 1, scale]
        controls.scaleBreakConnectCtrlList(curveTransforms, scaleXYZ, relative=True)
        cmds.select(deselect=True)

    @toolsetwidgetmaya.undoDecorator
    def absoluteScale(self, nullTxt=""):
        """Scales all controls from any selected part of the rig, to an exact size give by the GUI"""
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj()
        if not curveTransforms:  # then no shapes as nurbsCurves
            return
        scale = self.properties.ctrlSize.value
        controls.scaleBreakConnectCtrlList(curveTransforms, (scale, scale, scale), relative=False)
        # controls.scaleControlAbsoluteList((scale, scale, scale), curveTransforms)
        cmds.select(deselect=True)

    @toolsetwidgetmaya.undoDecorator
    def rotateCVs(self, positive=True):
        """Rotates CVs by local space rotation"""
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj()
        if not curveTransforms:  # then no shapes as nurbsCurves
            return
        # for alt shift and ctrl keys with left click
        multiplier, reset = keyboardmouse.cntrlShiftMultiplier(shiftMultiply=2.0, ctrlMultiply=0.5)
        rotateComboInt = self.properties.rotateCombo.value
        rotateOffset = 22.5
        multiplyOffset = rotateOffset * multiplier
        if reset:  # try to reset with the zoo scale tracker (if it exists)
            controls.rotateResetBrkCnctCtrlList(curveTransforms)
            cmds.select(deselect=True)
            return
        if not positive:
            multiplyOffset = -multiplyOffset
        if rotateComboInt == 0:  # X
            rotateXYZ = [multiplyOffset, 0, 0]
        elif rotateComboInt == 1:  # Y
            rotateXYZ = [0, multiplyOffset, 0]
        else:  # Z
            rotateXYZ = [0, 0, multiplyOffset]
        controls.rotateBreakConnectCtrlList(curveTransforms, rotateXYZ, relative=True)
        cmds.select(deselect=True)

    @toolsetwidgetmaya.undoDecorator
    def deleteControlCurveShapes(self):
        """Deletes all nurbsCurve shape nodes from the current selection
        """
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj()
        if not curveTransforms:  # then no shapes as nurbsCurves
            return
        delNodes = shapenodes.deleteShapeNodesList(curveTransforms, type="nurbsCurve")
        if not delNodes:
            om2.MGlobal.displayWarning("No curve shapes found in selection, please select curve object/s (transforms)")
        else:
            om2.MGlobal.displayInfo("Success: Shape node nurbsCurves deleted.")

    @toolsetwidgetmaya.undoDecorator
    def colorSelected(self, color):
        """Change the selected control color (and potential children) when the color is changed if a selection"""
        self.global_sendCntrlColor()
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj()
        if not curveTransforms:  # then no shapes as nurbsCurves
            return
        controls.colorControlsList(curveTransforms, color, linear=True)

    @toolsetwidgetmaya.undoDecorator
    def offsetColorSelected(self, offsetTuple, resetClicked):
        """Offset the selected control color (and potential children) when the color is changed if there's a selection

        :param offsetTuple: The offset as (hue, saturation, value)
        :type offsetTuple: tuple
        :param resetClicked: Has the reset been activated (alt clicked)
        :type resetClicked: bool
        """
        self.properties.color.value = self.currentWidget().colorHsvBtns.colorLinearFloat()
        self.global_sendCntrlColor()
        if resetClicked:  # set default color
            self.colorSelected(self.properties.color.default)
            return
        # filter curves ---------------
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj()
        if not curveTransforms:  # then no shapes as nurbsCurves
            return
        # Do the offset ------------------
        offsetFloat, hsvType = objcolor.convertHsvOffsetTuple(offsetTuple)
        controls.offsetHSVControlList(curveTransforms, offsetFloat, hsvType=hsvType, linear=True)

    def setColor(self):
        """Sets the color to the control based on the GUI"""
        self.colorSelected(self.properties.color.value)

    @toolsetwidgetmaya.undoDecorator
    def getColorSelected(self, selectMode=False):
        """From selection get the color of the current control curve and change the GUI to that color"""
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
        color = objcolor.getRgbColor(firstShapeNode, hsv=False, linear=True)
        if selectMode:  # select similar objects
            self.selectControlsByColor(color=color)
        else:  # just update the GUI
            self.properties.color.value = color
            self.updateFromProperties()  # Update the swatch in the GUI
            self.global_sendCntrlColor()

    @toolsetwidgetmaya.undoDecorator
    def selectControlsByColor(self, color=None):
        """Selects the controls that match the GUI color"""
        if not color:
            color = self.properties.color.value
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
        objcolor.selectObjsByColor(curveTransformList, color, message=True)

    @toolsetwidgetmaya.undoDecorator
    def groupZeroSelected(self):
        """Groups selected objs, matching a new group to each object and zero's the obj.  objNames can be long names.
        """
        matching.groupZeroObjSelection(freezeScale=True, message=True, removeSuffixName=filtertypes.CONTROLLER_SX)

    def setControlLineWidth(self):
        """Changes the lineWidth attribute of a curve (control) making the lines appear thicker or thinner.
        """
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj()
        if not curveTransforms:  # then no shapes as nurbsCurves
            return
        controls.setCurveLineThickness(curveTransforms, self.properties.lineWidth.value)

    @toolsetwidgetmaya.undoDecorator
    def freezeControlTracker(self):
        """Freezes the scale tracker attributes setting them to a scale of 1.0 no matter the current scale"""
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj()
        if not curveTransforms:  # then no shapes as nurbsCurves
            return
        controls.freezeScaleTrackerList(curveTransforms, message=True)

    @toolsetwidgetmaya.undoDecorator
    def mirrorControlsWithName(self):
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj()
        if not curveTransforms:  # then no shapes as nurbsCurves
            return
        replaceText = self.properties.mirrorReplaceTxt.value.replace(",", " ")
        replaceTextList = replaceText.split()
        if len(replaceTextList) != 2:
            om2.MGlobal.displayWarning("Search/replace text must be two words, Eg. `_L _R`")
            return
        # text may be in unicode and can be multiple pairs so list(list(str))
        searchTagsList = [[str(replaceTextList[0]), str(replaceTextList[1])]]
        mirrorAxis = MIRROR_AXIS[self.properties.mirrorAxisCombo.value]  # "X", "Y" or "Z"
        controls.mirrorControlAutoNameList(curveTransforms,
                                           searchTags=searchTagsList,
                                           mirrorAxis=mirrorAxis,
                                           keepColor=True,
                                           message=True)

    def setToolToMove(self):
        """checks if the manipulator is not in rot or translation mode, if not set to translate"""
        currentTool = cmds.currentCtx()
        if currentTool == "RotateSuperContext" or currentTool == "moveSuperContext":
            return
        cmds.setToolTo('Move')

    @toolsetwidgetmaya.undoDecorator
    def duplicateControls(self):
        """Duplicates a control without it's children, also becomes a transform if a joint

        If only one object is broken off then the original obj is remembered with self.breakObj, and can be used in \
        conjunction with self.replaceCurves()
        """
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj(disableHierarchy=True)
        if not curveTransforms:  # then no shapes as nurbsCurves
            return
        controls.duplicateControlList(curveTransforms, selectNewCtrls=True, useSelectedName=True)
        if len(curveTransforms) == 1:
            self.breakObj = curveTransforms[0]
        self.setToolToMove()

    @toolsetwidgetmaya.undoDecorator
    def breakOffCntrls(self):
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj(disableHierarchy=True)
        if not curveTransforms:  # then no shapes as nurbsCurves
            return
        newCtrls, newGrps = controls.breakTrackControlList(curveTransforms, applyTempColor=True,
                                                           tempColor=(1.0, 0.0, 1.0), createNetwork=True)
        self.selObjs = newCtrls
        cmds.select(newCtrls, replace=True)
        om2.MGlobal.displayInfo("Success: Controls broken off `{}`".format(newCtrls))
        self.setToolToMove()

    @toolsetwidgetmaya.undoDecorator
    def reconnectCntrls(self):
        masterCtrlList = controls.reconnectAllBreakCtrls()
        if masterCtrlList:
            self.selObjs = masterCtrlList

    def copyControl(self):
        controls.CNTRL_CLIPBOARD_INSTANCE.copyControl()

    def pasteControl(self):
        copiedControl, pastedControls = controls.CNTRL_CLIPBOARD_INSTANCE.pasteControl()
        if pastedControls:
            self.selObjs = pastedControls

    def flipControl(self):
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj(disableHierarchy=True)
        if not curveTransforms:  # then no shapes as nurbsCurves
            om2.MGlobal.displayWarning("No control found to flip, please copy a control.")
            return
        flipAxis = MIRROR_AXIS[self.properties.flipAxisCombo.value]
        controls.flipBreakConnectCtrlList(curveTransforms, flipAxis=flipAxis)
        cmds.select(curveTransforms, replace=True)

    def templateToggle(self):
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj(disableHierarchy=True)
        if not curveTransforms:  # then no shapes as nurbsCurves
            om2.MGlobal.displayWarning("No control found to template. Please select a control.")
            return
        controls.templateRefToggleList(curveTransforms)

    # ------------------
    # LOGIC - SAVE RENAME DEL SHAPE LIB
    # ------------------

    def saveControlsToLibrary(self):
        """Saves the selected control to disk, currently Zoo internally and not to zoo_preferences"""
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
        pureName = namehandling.mayaNamePartTypes(curveTransformList[0])[2]  # return the short name, no namespace
        newControlName = self.saveCurvesPopupWindow(pureName)
        if newControlName:  # Save confirmation from the GUI
            controls.saveControlSelected(newControlName, message=True)
            self.refreshShapeDesignComboBox(setItemText=newControlName)  # refresh shape/design combo box

    def deleteShapeDesignFromDisk(self):
        """Deletes specified shape/design from disk, currently Zoo internally and not to zoo_preferences"""
        designName = self.controlShapeList[self.properties.shapeCombo.value]
        self.fullPath = os.path.join(self.directory, "{}.{}".format(designName, cc.CONTROL_SHAPE_EXTENSION))
        okState = self.deleteCurvesPopupWindow(designName)
        if not okState:  # Cancel
            return
        # Delete file and dependency files
        filesFullPathDeleted = zooscenefiles.deleteZooSceneFiles(self.fullPath, message=True)
        currentIndex = self.properties.shapeCombo.value  # don't reset the list, go to the same index
        if currentIndex == len(self.controlShapeList) + -1:  # Then is the last index
            currentIndex -= 1  # List will become shorter
        self.refreshShapeDesignComboBox(setItemIndex=currentIndex)  # refresh shape/design combo box
        om2.MGlobal.displayInfo("Success, File/s Deleted: {}".format(filesFullPathDeleted))

    def renameShapeDesignOnDisk(self):
        designName = self.controlShapeList[self.properties.shapeCombo.value]
        self.fullPath = os.path.join(self.directory, "{}.{}".format(designName, cc.CONTROL_SHAPE_EXTENSION))
        renameText = self.renameCurvesPopupWindow(designName)
        if not renameText:
            return
        fileRenameList = zooscenefiles.renameZooSceneOnDisk(renameText, self.fullPath,
                                                            extension=cc.CONTROL_SHAPE_EXTENSION)
        # newPath = shapelib.renameLibraryShape(designName, newName, message=True)  # Todo:
        if fileRenameList:  # message handled inside function
            self.refreshShapeDesignComboBox(setItemText=renameText)  # refresh shape/design combo box
            om2.MGlobal.displayInfo("Success Files Renamed: {}".format(fileRenameList))

    def openPresetFolder(self):
        """Opens a windows/osx/linux file browser with the model asset directory path"""
        success = self.refreshPrefs()
        if not success:
            return
        filesystem.openDirectory(self.controlsJointsPrefsData["settings"][cc.PREFS_KEY_CONTROL_SHAPES])

    def setControlShapesDirectory(self):
        """Browse to change/set the Model Asset Folder"""
        success = self.refreshPrefs()
        if not success:
            return
        directoryPath = self.controlsJointsPrefsData["settings"][cc.PREFS_KEY_CONTROL_SHAPES]
        if not os.path.isdir(directoryPath):  # if dir doesn't exist set to home directory
            directoryPath = os.environ['HOME']
        newDirPath = QtWidgets.QFileDialog.getExistingDirectory(self, "Set the Model Asset folder", directoryPath)
        if not newDirPath:
            return
        self.controlsJointsPrefsData["settings"][cc.PREFS_KEY_CONTROL_SHAPES] = newDirPath
        self.directory = newDirPath
        self.controlsJointsPrefsData.save()
        # update thumb model on both thumb widgets
        self.refreshShapeDesignComboBox()  # refresh shape/design combo box
        om2.MGlobal.displayInfo("Preferences Saved: Control Shapes folder saved as "
                                "`{}`".format(newDirPath))

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Hookup the main connections"""
        for widget in self.widgets():  # update both GUIs
            uiInstance = widget.children()[0]
            # break reconnect
            uiInstance.breakOffBtn.clicked.connect(self.breakOffCntrls)
            uiInstance.reconnectBtn.clicked.connect(self.reconnectCntrls)
            # break reconnect
            uiInstance.copyCtrlBtn.clicked.connect(self.copyControl)
            uiInstance.pasteCtrlBtn.clicked.connect(self.pasteControl)
            uiInstance.mirrorBtn.clicked.connect(self.mirrorControlsWithName)
            # combine and replace curves
            uiInstance.combineCurvesBtn.clicked.connect(self.combineCurves)
            uiInstance.replaceCurveBtn.clicked.connect(self.replaceCurves)
        # Advanced GUI only
        # build
        self.advancedWidget.buildMatchBtn.clicked.connect(self.buildControlsAll)
        # edit
        self.advancedWidget.upAxisCombo.itemChanged.connect(self.replaceWithShapeDesign)
        # color
        self.advancedWidget.colorHsvBtns.colorChanged.connect(self.colorSelected)
        self.advancedWidget.applyColorBtn.clicked.connect(self.setColor)
        self.advancedWidget.colorHsvBtns.offsetClicked.connect(self.offsetColorSelected)
        # menu color
        self.advancedWidget.colorBtnMenu.menuChanged.connect(self.menuColor)
        # rot scale offset
        self.advancedWidget.scaleTxt.textModified.connect(self.absoluteScale)
        self.advancedWidget.scaleNegBtn.clicked.connect(partial(self.scaleCVs, positive=False))
        self.advancedWidget.scalePosBtn.clicked.connect(partial(self.scaleCVs, positive=True))
        self.advancedWidget.rotatePosBtn.clicked.connect(partial(self.rotateCVs, positive=True))
        self.advancedWidget.rotateNegBtn.clicked.connect(partial(self.rotateCVs, positive=False))
        # replace
        self.advancedWidget.shapeComboBx.itemChanged.connect(self.replaceWithShapeDesign)
        # dots menu viewer
        self.advancedWidget.dotsMenu.createAction.connect(self.saveControlsToLibrary)
        self.advancedWidget.dotsMenu.renameAction.connect(self.renameShapeDesignOnDisk)
        self.advancedWidget.dotsMenu.browseAction.connect(self.openPresetFolder)
        self.advancedWidget.dotsMenu.setDirAction.connect(self.setControlShapesDirectory)
        self.advancedWidget.dotsMenu.deleteAction.connect(self.deleteShapeDesignFromDisk)
        self.advancedWidget.dotsMenu.refreshAction.connect(self.fullRefreshComboList)
        # other
        self.advancedWidget.getColorBtn.clicked.connect(self.getColorSelected)
        self.advancedWidget.selectColorBtn.clicked.connect(self.selectControlsByColor)
        self.advancedWidget.deleteCurvesBtn.clicked.connect(self.deleteControlCurveShapes)
        self.advancedWidget.groupCurvesBtn.clicked.connect(self.groupZeroSelected)
        self.advancedWidget.lineWidthTxt.textModified.connect(self.setControlLineWidth)
        self.advancedWidget.freezeSrtBtn.clicked.connect(self.freezeControlTracker)
        self.advancedWidget.duplicateBtn.clicked.connect(self.duplicateControls)
        self.advancedWidget.flipBtn.clicked.connect(self.flipControl)
        self.advancedWidget.templateToggleBtn.clicked.connect(self.templateToggle)


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
        # Translate Section (currently not used) ------------------------------------
        toolTip = "Translate (move) the selected curves controls\n" \
                  "Note: This will not affect channel box scale. \n" \
                  "Stored on a hidden attribute."
        self.translateVectorTxt = elements.VectorLineEdit("Trans",
                                                          self.properties.translateVector.value,
                                                          parent=parent,
                                                          toolTip=toolTip,
                                                          labelRatio=1,
                                                          editRatio=4)
        self.toolsetWidget.linkProperty(self.translateVectorTxt, "translateVector")
        self.translateVectorTxt.hide()
        toolTip = "Translate the selected curves by all or a single axis"
        self.translateComboBx = elements.ComboBoxRegular("",
                                                         TRANSLATE_LIST,
                                                         parent,
                                                         toolTip=toolTip,
                                                         setIndex=self.properties.translateCombo.value)
        self.toolsetWidget.linkProperty(self.translateComboBx, "translateCombo")
        toolTip = "Translates positive."
        self.translatePosBtn = elements.styledButton("",
                                                     "arrowUp",
                                                     toolTip=toolTip,
                                                     parent=parent,
                                                     minWidth=uic.BTN_W_ICN_MED)
        toolTip = "Translates negatively."
        self.translateNegBtn = elements.styledButton("",
                                                     "arrowDown",
                                                     toolTip=toolTip,
                                                     parent=parent,
                                                     minWidth=uic.BTN_W_ICN_MED)
        self.translateComboBx.hide()  # hide as not in use
        self.translatePosBtn.hide()
        self.translateNegBtn.hide()
        # Break Off Button ------------------------------------
        toolTip = "Click to `Break Off` selected control/s.  The control/s turn pink until they have been \n" \
                  "reconnected with the `Reconnect All Ctrls` button. Broken off controls can be scaled, \n" \
                  "rotated and translated and will remember their settings after they are reconnected."
        self.breakOffBtn = elements.styledButton(text="Break Off Ctrls",
                                                 icon="breakOff",
                                                 toolTip=toolTip,
                                                 parent=parent,
                                                 style=uic.BTN_LABEL_SML)
        # Reconnect Button ------------------------------------
        toolTip = "Reconnects all `Break Off` (pink) controls in the scene to their original parents.\n" \
                  "`Break Off` controls must already exist in the scene.  To break off controls use the \n" \
                  "`Break Off Ctrls` button."
        self.reconnectBtn = elements.styledButton(text="Reconnect All Ctrls",
                                                  icon="reconnectCtrls",
                                                  toolTip=toolTip,
                                                  parent=parent,
                                                  style=uic.BTN_LABEL_SML)
        # Copy Control ------------------------------------
        toolTip = "Select a single control to copy."
        self.copyCtrlBtn = elements.styledButton(text="Copy Ctrl",
                                                 icon="copy1",
                                                 toolTip=toolTip,
                                                 parent=parent,
                                                 style=uic.BTN_LABEL_SML)
        # Paste Ctrl ------------------------------------
        toolTip = "Paste from the clipboard onto the the selected control curve/s."
        self.pasteCtrlBtn = elements.styledButton(text="Paste Ctrl",
                                                  icon="paste",
                                                  toolTip=toolTip,
                                                  parent=parent,
                                                  style=uic.BTN_LABEL_SML)
        # Mirror Text Search ------------------------------------
        toolTip = "Search and replace text for the mirror, can be in any order. \n" \
                  "Mirror controls must be named with these parts in the names.\n" \
                  "Select only one control, it will be mirrored to the opposite side."
        self.mirrorReplaceTxt = elements.StringEdit(label="Mirror Search",
                                                    editText=self.properties.mirrorReplaceTxt.value,
                                                    parent=parent,
                                                    toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.mirrorReplaceTxt, "mirrorReplaceTxt")
        # Mirror Btn and combo ------------------------------------
        toolTip = "Mirrors a control to it's opposing control, left/right.\n" \
                  "Select one control, the opposite control/s will be found\n" \
                  "automatically from the text box's naming convention."
        self.mirrorBtn = elements.styledButton(text="",
                                               icon="symmetryTri",
                                               toolTip=toolTip,
                                               parent=parent,
                                               style=uic.BTN_LABEL_SML)
        toolTip = "The axis to mirror across, left/right.\n" \
                  "- X is the default for most characters.\n" \
                  "- Y is up and down.\n" \
                  "- Z is forwards and backwards."
        self.mirrorAxisCombo = elements.ComboBoxRegular(label="Mirror Axis",
                                                        items=MIRROR_AXIS,
                                                        parent=parent,
                                                        toolTip=toolTip,
                                                        setIndex=self.properties.mirrorAxisCombo.value)
        self.toolsetWidget.linkProperty(self.mirrorAxisCombo, "mirrorAxisCombo")
        # Combine Button ------------------------------------
        toolTip = "Combines curves with a shape node parent. Select two or more curves. \n" \
                  "The last selected curve will remain with the combined shapes.\n" \
                  "The first objects will be deleted if they have no children."
        self.combineCurvesBtn = elements.styledButton(text="Combine Sel Curves",
                                                      icon="combineCurve",
                                                      toolTip=toolTip,
                                                      parent=parent,
                                                      style=uic.BTN_LABEL_SML)
        # Replace Button ------------------------------------
        toolTip = "Shape parent the curve to a new transform.  If a curve exists it will be replaced. \n" \
                  "Select two or more curve objects. Source to destination. "
        self.replaceCurveBtn = elements.styledButton(text="Shape Parent\Replace",
                                                     icon="replaceCurve",
                                                     toolTip=toolTip,
                                                     parent=parent,
                                                     style=uic.BTN_LABEL_SML)
        if uiMode == UI_MODE_ADVANCED:
            self.controlShapeList = shapelib.shapeNames()
            # Replace Section  ------------------------------------
            toolTip = "Replace curves with the following shapes."
            self.shapeComboBx = elements.ComboBoxSearchable("",
                                                            self.controlShapeList,
                                                            parent,
                                                            labelRatio=4,
                                                            boxRatio=6,
                                                            toolTip=toolTip,
                                                            setIndex=self.properties.shapeCombo.value)
            self.toolsetWidget.linkProperty(self.shapeComboBx, "shapeCombo")
            # Rename Delete Dots Menu  ------------------------------------
            self.dotsMenu = DotsMenu(self)  # See class DotsMenu()
            # Color Section  ------------------------------------
            toolTip = "The color of the control to be created or selected controls."
            self.colorHsvBtns = elements.MayaColorHsvBtns(text="Color",
                                                          color=self.properties.color.value,
                                                          parent=parent,
                                                          toolTip=toolTip,
                                                          btnRatio=4,
                                                          labelRatio=2,
                                                          colorWidgetRatio=21,
                                                          hsvRatio=15,
                                                          middleSpacing=uic.SVLRG,
                                                          resetColor=self.properties.color.value)
            self.toolsetWidget.linkProperty(self.colorHsvBtns, "color")
            self.colorBtnMenuModeList = [("paintLine", "Get Color From Obj"),
                                         ("cursorSelect", "Select Similar"),
                                         ("cursorSelect", "Select With Color")]
            self.colorBtnMenu = elements.ExtendedMenu(searchVisible=True)
            self.colorHsvBtns.setMenu(self.colorBtnMenu, modeList=self.colorBtnMenuModeList)  # right click
            self.colorHsvBtns.setMenu(self.colorBtnMenu,
                                      mouseButton=QtCore.Qt.LeftButton)  # left click, modes set already
            toolTip = "Apply the GUI color to the selected controls."
            self.applyColorBtn = elements.styledButton("",
                                                       "paintLine",
                                                       toolTip=toolTip,
                                                       parent=parent,
                                                       minWidth=uic.BTN_W_ICN_MED,
                                                       maxWidth=uic.BTN_W_ICN_MED)
            # Orient Combo Axis Section  ------------------------------------
            toolTip = "Select the up axis orientation. \n" \
                      "+X for joints \n" \
                      "+Y for world controls flat on ground\n" \
                      "+Z for front facing in world"
            self.upAxisCombo = elements.ComboBoxRegular("",
                                                        cc.ORIENT_UP_LIST,
                                                        parent,
                                                        labelRatio=4,
                                                        boxRatio=6,
                                                        toolTip=toolTip,
                                                        setIndex=self.properties.orientCombo.value)
            self.toolsetWidget.linkProperty(self.upAxisCombo, "orientCombo")
            # Rotate Section ------------------------------------
            toolTip = "Rotate the selected curves controls" \
                      "Note: This will not affect channel box scale. " \
                      "Stored on a hidden attribute."
            self.rotateVectorTxt = elements.VectorLineEdit("Rotate",
                                                           self.properties.rotateVector.value,
                                                           parent=parent,
                                                           toolTip=toolTip,
                                                           labelRatio=1,
                                                           editRatio=4)
            self.rotateVectorTxt.hide()
            self.toolsetWidget.linkProperty(self.rotateVectorTxt, "rotateVector")
            toolTip = "Rotate the selected curves controls on this axis.\n" \
                      "The rotation is performed in the shape's object space\n" \
                      "not in its local space.\n" \
                      "Does not affect channel box rotate values."
            self.rotateComboBx = elements.ComboBoxRegular("",
                                                          cc.ROTATE_LIST,
                                                          parent,
                                                          toolTip=toolTip,
                                                          setIndex=self.properties.rotateCombo.value)
            self.toolsetWidget.linkProperty(self.rotateComboBx, "rotateCombo")
            toolTip = "Rotate the selected control/s by 45 degrees negative.\n" \
                      "Hold shift for faster, ctrl slower, alt for reset.\n" \
                      "The rotation is performed in the shape's object space\n" \
                      "not in its local space.\n" \
                      "Does not affect channel box rotate values."
            self.rotateNegBtn = elements.styledButton("",
                                                      "arrowRotLeft",
                                                      toolTip=toolTip,
                                                      parent=parent,
                                                      minWidth=uic.BTN_W_ICN_MED)
            toolTip = "Rotate the selected control/s by 45 degrees positive.\n" \
                      "Hold shift for faster, ctrl slower, alt for reset.\n" \
                      "The rotation is performed in the shape's object space\n" \
                      "not in its local space.\n" \
                      "Does not affect channel box rotate values."
            self.rotatePosBtn = elements.styledButton("",
                                                      "arrowRotRight",
                                                      toolTip=toolTip,
                                                      parent=parent,
                                                      minWidth=uic.BTN_W_ICN_MED)
            # Scale Section ------------------------------------
            toolTip = "Sets the absolute Scale of the control/s being built or selected.\n" \
                      "Hit return inside this text box to set the scale of selected controls.\n" \
                      "Does not affect channel box scale values."
            self.scaleTxt = elements.FloatEdit("Scale",
                                               self.properties.ctrlSize.value,
                                               parent=parent,
                                               toolTip=toolTip)
            self.toolsetWidget.linkProperty(self.scaleTxt, "ctrlSize")
            toolTip = "Scale the selected curves controls.\n" \
                      "Note: This will not affect channel box scale. \n" \
                      "Stored on a hidden attribute."
            self.scaleVectorTxt = elements.VectorLineEdit("Scale",
                                                          self.properties.scaleVector.value,
                                                          parent=parent,
                                                          toolTip=toolTip,
                                                          labelRatio=1,
                                                          editRatio=4,
                                                          rounding=2)
            self.toolsetWidget.linkProperty(self.scaleVectorTxt, "scaleVector")
            self.scaleVectorTxt.hide()
            toolTip = "Scale the selected curves by all or a single axis\n" \
                      "The scale is performed in the shape's object space\n" \
                      "not in its local space.\n" \
                      "Does not affect channel box scale values."
            self.scaleComboBx = elements.ComboBoxRegular("",
                                                         cc.SCALE_LIST,
                                                         parent,
                                                         toolTip=toolTip,
                                                         setIndex=self.properties.scaleCombo.value)
            self.toolsetWidget.linkProperty(self.scaleComboBx, "scaleCombo")
            toolTip = "Scale selected controls larger by 5 percent.\n" \
                      "Hold shift is faster, ctrl slower, alt for reset.\n" \
                      "The scale is performed in the shape's object space\n" \
                      "not in its local space.\n" \
                      "Does not affect channel box scale values."
            self.scalePosBtn = elements.styledButton("",
                                                     "scaleUp",
                                                     toolTip=toolTip,
                                                     parent=parent,
                                                     minWidth=uic.BTN_W_ICN_MED)
            toolTip = "Scale selected controls smaller by 5 percent.\n" \
                      "Hold shift is faster, ctrl slower, alt for reset.\n" \
                      "The scale is performed in the shape's local space\n" \
                      "not in its object space.\n" \
                      "Does not affect channel box scale values."
            self.scaleNegBtn = elements.styledButton("",
                                                     "scaleDown",
                                                     toolTip=toolTip,
                                                     parent=parent,
                                                     minWidth=uic.BTN_W_ICN_MED)
            # Hierarchy Radio ------------------------------------
            radioNameList = ["Selected", "Hierarchy"]
            radioToolTipList = ["Affect only the selected joints/controls.",
                                "Affect the selection and all of its child joints/controls."]
            self.selHierarchyRadioWidget = elements.RadioButtonGroup(radioList=radioNameList,
                                                                     toolTipList=radioToolTipList,
                                                                     default=self.properties.selHierarchyRadio.value,
                                                                     parent=parent,
                                                                     margins=(0, 0, 0, 0))
            self.toolsetWidget.linkProperty(self.selHierarchyRadioWidget, "selHierarchyRadio")
            # Select Color Button ------------------------------------
            toolTip = "Select all controls with the current color."
            self.selectColorBtn = elements.styledButton(text="Select From Color",
                                                        icon="cursorSelect",
                                                        toolTip=toolTip,
                                                        parent=parent,
                                                        style=uic.BTN_LABEL_SML)
            # Get Color Button ------------------------------------
            toolTip = "Get color from the first selected object."
            self.getColorBtn = elements.styledButton(text="Get Color",
                                                     icon="arrowLeft",
                                                     toolTip=toolTip,
                                                     parent=parent,
                                                     style=uic.BTN_LABEL_SML)
            # Delete Shapes ------------------------------------
            toolTip = "Delete all `nurbsCurve` shape nodes from the selected objects,\n" \
                      "transforms (groups) will remain."
            self.deleteCurvesBtn = elements.styledButton(text="Delete Crv Shapes",
                                                         icon="trash",
                                                         toolTip=toolTip,
                                                         parent=parent,
                                                         style=uic.BTN_LABEL_SML)
            # Group Zero Curve ------------------------------------
            toolTip = "Group a curve and zero its transformations.\n" \
                      "The curve's scale will be reset to 1, 1, 1."
            self.groupCurvesBtn = elements.styledButton(text="Group Zero Object",
                                                        icon="folderadd2",
                                                        toolTip=toolTip,
                                                        parent=parent,
                                                        style=uic.BTN_LABEL_SML)
            # Flip Button ------------------------------------
            toolTip = "Flip-mirrors a single control. Only the selected control/s will flip."
            self.flipBtn = elements.styledButton(text="",
                                                 icon="symmetryTri",
                                                 toolTip=toolTip,
                                                 parent=parent,
                                                 style=uic.BTN_LABEL_SML)
            toolTip = "Flip-mirrors a single control. Select the axis to flip across."
            self.flipAxisCombo = elements.ComboBoxRegular(label="Flip Axis",
                                                          items=MIRROR_AXIS,
                                                          parent=parent,
                                                          toolTip=toolTip,
                                                          setIndex=self.properties.flipAxisCombo.value)
            self.toolsetWidget.linkProperty(self.flipAxisCombo, "flipAxisCombo")
            # Freeze Button ------------------------------------
            toolTip = "Set the current scale of the control to be it's default scale.\n" \
                      "Useful while resetting. To reset alt-click the scale elements."
            self.freezeSrtBtn = elements.styledButton(text="Set Default Scale",
                                                      icon="freezeSrt",
                                                      toolTip=toolTip,
                                                      parent=parent,
                                                      style=uic.BTN_LABEL_SML)
            # Duplicate Ctrl ------------------------------------
            toolTip = "Duplicate a control curve, and parent it to the world."
            self.duplicateBtn = elements.styledButton(text="Duplicate Ctrl",
                                                      icon="duplicateCtrl",
                                                      toolTip=toolTip,
                                                      parent=parent,
                                                      style=uic.BTN_LABEL_SML)
            # Line Width ------------------------------------
            toolTip = "Sets the thickness of the control curve lines.\n" \
                      "A line thickness of -1 uses the global preferences setting, usually 1."
            self.lineWidthTxt = elements.IntEdit(label="Line Width",
                                                 editText=self.properties.lineWidth.value,
                                                 labelRatio=1,
                                                 editRatio=1,
                                                 toolTip=toolTip)
            self.toolsetWidget.linkProperty(self.lineWidthTxt, "lineWidth")
            # Group
            toolTip = "Add groups to zero out the controls/joints (recommended)"
            self.grpJointsCheckBx = elements.CheckBox("Group",
                                                      self.properties.grpJointsCheckBox.value,
                                                      parent=parent,
                                                      toolTip=toolTip)
            self.toolsetWidget.linkProperty(self.grpJointsCheckBx, "grpJointsCheckBox")
            # Freeze Joints
            toolTip = "Freeze transform joints only, while adding `Joint Controls` (recommended)"
            self.freezeJntsCheckBx = elements.CheckBox("Freeze Jnt",
                                                       self.properties.freezeJntsCheckBox.value,
                                                       parent=parent,
                                                       toolTip=toolTip)
            self.toolsetWidget.linkProperty(self.freezeJntsCheckBx, "freezeJntsCheckBox")
            # Template Ctrl ------------------------------------
            toolTip = "Template toggles the selected control/s"
            self.templateToggleBtn = elements.styledButton(text="Template Toggle",
                                                           icon="templateObj",
                                                           toolTip=toolTip,
                                                           parent=parent,
                                                           style=uic.BTN_LABEL_SML)
            # Build Bottom Buttons Section ----------------------------------
            toolTip = "Build control curve/s, will match to selected object/s. \n" \
                      "Controls will be floating and not parented/connected via constraints etc."
            self.buildMatchBtn = elements.styledButton("Create Controls",
                                                       "starControl",
                                                       parent,
                                                       toolTip=toolTip,
                                                       style=uic.BTN_DEFAULT)
            self.buildComboBox = elements.ComboBoxRegular("",
                                                          items=controls.CONTROL_BUILD_TYPE_LIST,
                                                          setIndex=1,
                                                          parent=parent,
                                                          toolTip=toolTip)
            self.toolsetWidget.linkProperty(self.buildComboBox, "buildStyle")


class DotsMenu(elements.IconMenuButton):
    menuIcon = "menudots"
    createAction = QtCore.Signal()
    deleteAction = QtCore.Signal()
    renameAction = QtCore.Signal()
    browseAction = QtCore.Signal()
    setDirAction = QtCore.Signal()
    refreshAction = QtCore.Signal()

    def __init__(self, parent=None):
        """This class is the dots menu button

        :param parent: The Qt Widget parent
        :type parent: Qt Widget
        """
        super(DotsMenu, self).__init__(parent=parent)

    def initUi(self):
        super(DotsMenu, self).initUi()

        iconColor = THEME_PREFS.ICON_PRIMARY_COLOR
        self.setIconByName(self.menuIcon, size=16, colors=iconColor)

        self.setToolTip("File menu. Manage Skydomes")

        saveIcon = iconlib.iconColorized("save", qtutils.dpiScale(16))
        deleteIcon = iconlib.iconColorized("trash", qtutils.dpiScale(16))
        renameIcon = iconlib.iconColorized("editText", qtutils.dpiScale(16))
        browseIcon = iconlib.iconColorized("globe", qtutils.dpiScale(16))
        refreshIcon = iconlib.iconColorized("refresh", qtutils.dpiScale(16))
        setPrefsIcon = iconlib.iconColorized("addDir", qtutils.dpiScale(16))

        self.addAction("New Control Shape", connect=lambda: self.createAction.emit(), icon=saveIcon)
        self.addAction("Delete Control Shape", connect=lambda: self.deleteAction.emit(), icon=deleteIcon)
        self.addAction("Rename Control Shape", connect=lambda: self.renameAction.emit(), icon=renameIcon)
        self.addAction("Browse Files", connect=lambda: self.browseAction.emit(), icon=browseIcon)
        self.addAction("Set Control Shapes Dir", connect=lambda: self.setDirAction.emit(), icon=setPrefsIcon)
        self.addAction("Refresh Thumbnails", connect=lambda: self.refreshAction.emit(), icon=refreshIcon)

        self.setMenuAlign(QtCore.Qt.AlignRight)


class CompactLayout(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None):
        """Adds the layout building the compact version of the GUI.  Call this class for the Compact GUI:

            default uiMode - 0 is advanced (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(CompactLayout, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                            toolsetWidget=toolsetWidget)
        # Main Layout ----------------------------------
        contentsLayout = elements.vBoxLayout(parent,
                                             margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                             spacing=uic.REGPAD)
        # Translate Btn Layout ------------------------------------
        translateLayout = elements.hBoxLayout(parent, margins=(0, 0, 0, 0), spacing=uic.SLRG)
        translateLayout.addWidget(self.translateComboBx, 12)
        translateLayout.addWidget(self.translateNegBtn, 1)
        translateLayout.addWidget(self.translatePosBtn, 1)
        # Mirror Layout --------------------------------------------
        mirrorLayout = elements.hBoxLayout(parent, margins=(0, 0, 0, 0), spacing=uic.SREG)
        mirrorLayout.addWidget(self.mirrorAxisCombo, 5)
        mirrorLayout.addWidget(self.mirrorBtn, 1)
        # grid layout
        gridLayout = elements.GridLayout(parent, margins=(0, 0, 0, 0), vSpacing=uic.SREG,
                                         hSpacing=uic.SVLRG)
        gridLayout.addWidget(self.translateVectorTxt, 0, 0)  # hidden
        gridLayout.addLayout(translateLayout, 0, 1)  # hidden
        gridLayout.addWidget(self.breakOffBtn, 1, 0)
        gridLayout.addWidget(self.reconnectBtn, 1, 1)
        gridLayout.addWidget(self.copyCtrlBtn, 2, 0)
        gridLayout.addWidget(self.pasteCtrlBtn, 2, 1)
        gridLayout.addWidget(self.combineCurvesBtn, 3, 0)
        gridLayout.addWidget(self.replaceCurveBtn, 3, 1)
        gridLayout.addWidget(self.mirrorReplaceTxt, 4, 0)
        gridLayout.addLayout(mirrorLayout, 4, 1)
        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)
        # add to main layout
        contentsLayout.addLayout(gridLayout)
        contentsLayout.addStretch(1)


class AdvancedLayout(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_ADVANCED, toolsetWidget=None):
        """Adds the layout building the advanced version of the GUI.  Call this class for the Compact GUI::

            default uiMode - 1 is advanced (UI_MODE_ADVANCED)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(AdvancedLayout, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                             toolsetWidget=toolsetWidget)
        # Main Layout ------------------------------------
        contentsLayout = elements.vBoxLayout(parent,
                                             margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                             spacing=uic.REGPAD)
        # replace shape/design Layout ------------------------------------
        orientSaveLayout = elements.hBoxLayout(parent, margins=(0, 0, 0, 0), spacing=uic.SLRG)
        orientSaveLayout.addWidget(self.upAxisCombo, 12)
        orientSaveLayout.addWidget(self.dotsMenu, 1)
        comboReplaceLayout = elements.hBoxLayout(parent, margins=(0, 0, 0, 0), spacing=uic.SVLRG)
        comboReplaceLayout.addWidget(self.shapeComboBx, 1)
        comboReplaceLayout.addLayout(orientSaveLayout, 1)
        # color shape/design Layout ------------------------------------
        colorLayout = elements.hBoxLayout(parent, margins=(0, 0, 0, 0), spacing=uic.SVLRG)
        colorLayout.addWidget(self.colorHsvBtns, 24)
        colorLayout.addWidget(self.applyColorBtn, 1)
        # Rotate Btn Layout ------------------------------------
        rotateLayout = elements.hBoxLayout(parent, margins=(0, 0, 0, 0), spacing=uic.SLRG)
        rotateLayout.addWidget(self.rotateComboBx, 12)
        rotateLayout.addWidget(self.rotateNegBtn, 1)
        rotateLayout.addWidget(self.rotatePosBtn, 1)
        # Scale Btn Layout ------------------------------------
        scaleLayout = elements.hBoxLayout(parent, margins=(0, 0, 0, 0), spacing=uic.SLRG)
        scaleLayout.addWidget(self.scaleComboBx, 12)
        scaleLayout.addWidget(self.scaleNegBtn, 1)
        scaleLayout.addWidget(self.scalePosBtn, 1)
        # Translate Btn Layout ------------------------------------
        translateLayout = elements.hBoxLayout(parent, margins=(0, 0, 0, 0), spacing=uic.SLRG)
        translateLayout.addWidget(self.translateComboBx, 12)
        translateLayout.addWidget(self.translateNegBtn, 1)
        translateLayout.addWidget(self.translatePosBtn, 1)
        # Mirror Layout
        mirrorLayout = elements.hBoxLayout(parent, margins=(0, 0, 0, 0), spacing=uic.SREG)
        mirrorLayout.addWidget(self.mirrorAxisCombo, 5)
        mirrorLayout.addWidget(self.mirrorBtn, 1)
        # Mirror Layout
        flipLayout = elements.hBoxLayout(parent, margins=(0, 0, 0, 0), spacing=uic.SREG)
        flipLayout.addWidget(self.flipAxisCombo, 5)
        flipLayout.addWidget(self.flipBtn, 1)
        # grid layout
        gridLayout = elements.GridLayout(parent, margins=(0, 0, 0, 0), vSpacing=uic.SREG,
                                         hSpacing=uic.SVLRG)
        gridLayout.addWidget(self.selectColorBtn, 0, 0)
        gridLayout.addWidget(self.getColorBtn, 0, 1)
        gridLayout.addWidget(self.scaleTxt, 1, 0)
        gridLayout.addLayout(scaleLayout, 1, 1)
        gridLayout.addWidget(self.scaleVectorTxt, 2, 1)  # hidden
        gridLayout.addWidget(self.translateVectorTxt, 2, 0)  # hidden
        gridLayout.addLayout(translateLayout, 3, 1)  # hidden
        gridLayout.addWidget(self.lineWidthTxt, 4, 0)
        gridLayout.addWidget(self.rotateVectorTxt, 4, 0)  # hidden
        gridLayout.addLayout(rotateLayout, 4, 1)
        gridLayout.addWidget(self.breakOffBtn, 5, 0)
        gridLayout.addWidget(self.reconnectBtn, 5, 1)
        gridLayout.addWidget(self.duplicateBtn, 6, 0)
        gridLayout.addWidget(self.replaceCurveBtn, 6, 1)
        gridLayout.addWidget(self.combineCurvesBtn, 7, 0)
        gridLayout.addWidget(self.deleteCurvesBtn, 7, 1)
        gridLayout.addWidget(self.groupCurvesBtn, 8, 0)
        gridLayout.addWidget(self.freezeSrtBtn, 8, 1)
        gridLayout.addWidget(self.copyCtrlBtn, 9, 0)
        gridLayout.addWidget(self.pasteCtrlBtn, 9, 1)
        gridLayout.addWidget(self.mirrorReplaceTxt, 10, 0)
        gridLayout.addLayout(mirrorLayout, 10, 1)
        gridLayout.addWidget(self.templateToggleBtn, 11, 0)
        gridLayout.addLayout(flipLayout, 11, 1)
        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)
        # checkbox layout
        checkboxLayout = elements.hBoxLayout(parent, margins=(0, uic.SSML, 0, uic.SSML), spacing=uic.SVLRG)
        checkboxLayout.addWidget(self.grpJointsCheckBx, 1)
        checkboxLayout.addWidget(self.freezeJntsCheckBx, 1)
        boxLayout = elements.hBoxLayout(parent, spacing=uic.SVLRG)
        boxLayout.addWidget(self.selHierarchyRadioWidget, 2)
        boxLayout.addLayout(checkboxLayout, 2)
        # button layout
        buttonLayout = elements.hBoxLayout(parent, margins=(0, 0, 0, 0), spacing=uic.SLRG)
        buttonLayout.addWidget(self.buildComboBox, 1)
        buttonLayout.addWidget(self.buildMatchBtn, 1)
        # add to main layout
        contentsLayout.addLayout(comboReplaceLayout)
        contentsLayout.addLayout(colorLayout)
        contentsLayout.addLayout(gridLayout)
        contentsLayout.addLayout(boxLayout)
        contentsLayout.addLayout(buttonLayout)
        contentsLayout.addStretch(1)
