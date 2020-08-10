import os
from functools import partial

import maya.cmds as cmds
import maya.api.OpenMaya as om2

from zoo.libs.zooscene import zooscenefiles
from Qt import QtCore, QtWidgets

from zoo.libs.utils import filesystem, path
from zoo.libs.maya.cmds.general import undodecorator

from zoo.apps.controls_joints import controlsjointsconstants as cc
from zoo.apps.controls_joints import controlsdirectories

from zoo.apps.toolsetsui.widgets.toolsetresizer import ToolsetResizer
from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.apps.toolsetsui import toolsetui

from zoo.apps.controls_joints import modelcontrolcurves

from zoo.libs.pyqt import uiconstants as uic, keyboardmouse
from zoo.libs.pyqt.widgets import elements

from zoo.preferences.core import preference

from zoo.libs.maya.cmds.objutils import shapenodes, objcolor, filtertypes, namehandling
from zoo.libs.maya.cmds.rig import controls
# Dots Menu
from zoo.libs.pyqt.widgets.iconmenu import IconMenuButton
from zoo.libs import iconlib
from zoo.libs.pyqt import utils

THEME_PREFS = preference.interface("core_interface")

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

COMBO_UP_LIST = list()
for x in cc.ORIENT_UP_LIST:
    COMBO_UP_LIST.append("Up Axis {}".format(x))


class ControlCreator(toolsetwidgetmaya.ToolsetWidgetMaya):
    directory = None  # type: object
    uniformIcons = None  # type: object

    id = "controlCreator"
    uiData = {"label": "Control Creator",
              "icon": "starControl",
              "tooltip": "GUI for creating control curves",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-control-creator/"
              }

    # ------------------------------------
    # START UP
    # ------------------------------------

    def preContentSetup(self):
        """First code to run"""
        self.setupPrefsDirectory()  # self.directory and self.uniformIcon
        self.selObjs = list()  # Remember the last objects selected if nothing selected
        self.breakObj = ""  # the break object, useful for replace
        self.copyCtrl = ""
        self.copyTranslate = None
        self.copyRotate = None
        self.copyScale = None
        self.copyColor = None
        self.copyShape = ""
        self._defaultControls = None

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        parent = QtWidgets.QWidget(parent=self)
        self.parentWgt = parent
        self.compactWidget = GuiCompact(parent=parent, properties=self.properties, toolsetWidget=self,
                                        directory=self.directory, uniformIcons=self.uniformIcons)
        return self.compactWidget

    def initAdvancedWidget(self):
        """Not used, legacy"""
        parent = QtWidgets.QWidget(parent=self)
        self.advancedWidget = GuiAdvanced(parent=parent, properties=self.properties, toolsetWidget=self,
                                          directory=self.directory, uniformIcons=self.uniformIcons)
        return self.advancedWidget

    def postContentSetup(self):
        """Last of the initizialize code"""
        self.uiconnections()

    def currentWidget(self):
        """ Current active widget

        :return:
        :rtype:  AllWidgets
        """
        return super(ControlCreator, self).currentWidget()

    def widgets(self):
        """ List of widgets

        :return:
        :rtype: list[AllWidgets]
        """
        return super(ControlCreator, self).widgets()

    # ------------------------------------
    # PROPERTIES
    # ------------------------------------

    def updateFromProperties(self):
        """ Runs update properties from the base class.

        Add code after super() useful for changes such as forcing UI decimal places
        or manually adding unsupported widgets
        """
        super(ControlCreator, self).updateFromProperties()
        self.defaultControls()

    def defaultControls(self, refresh=False):
        if not refresh and self._defaultControls != None:
            return self._defaultControls
        shapesDefaultDir = controlsdirectories.defaultControlsPath()
        path.filesInDirectory(shapesDefaultDir, ext=False)
        self._defaultControls = path.filesInDirectory(shapesDefaultDir, ext=False)
        return self._defaultControls

    # ------------------------------------
    # POPUP WINDOWS
    # ------------------------------------

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

    def setupPrefsDirectory(self):
        """Sets up retrieves the preferences directory information. Sets up:

            self.controlsJointsPrefsData
            self.directory
        """
        # Preferences directory
        self.controlsJointsPrefsData = preference.findSetting(cc.RELATIVE_PREFS_FILE, None)  # model asset .prefs info
        self.controlsJointsDirectory()  # creates/updates self.directory
        self.uniformIcons = self.controlsJointsPrefsData["settings"][cc.PREFS_KEY_CONTROL_UNIFORM]
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
        return self.directory

    def refreshThumbs(self):
        """Refreshes the GUI """
        self.currentWidget().miniBrowser.refreshThumbs()

    # ------------------------------------
    # DOTS MENU
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
        if not os.path.isdir(self.directory):  # if dir doesn't exist set to home directory
            self.directory = os.environ['HOME']
        newDirPath = QtWidgets.QFileDialog.getExistingDirectory(self, "Set the Model Asset folder", self.directory)
        if not newDirPath:
            return
        self.controlsJointsPrefsData["settings"][cc.PREFS_KEY_CONTROL_SHAPES] = newDirPath
        self.directory = newDirPath
        self.controlsJointsPrefsData.save()
        # update thumb model on both thumb widgets
        self.compactWidget.browserModel.setDirectory(newDirPath)  # does the images refresh
        #  self.advancedWidget.browserModel.setDirectory(newDirPath)
        om2.MGlobal.displayInfo("Preferences Saved: Control Shapes folder saved as "
                                "`{}`".format(newDirPath))

    def uniformIconToggle(self, action):
        """Toggles the state of the uniform icons
        """

        self.uniformIcons = action.isChecked()
        self.controlsJointsPrefsData["settings"][cc.PREFS_KEY_CONTROL_UNIFORM] = self.uniformIcons
        self.controlsJointsPrefsData.save()
        self.refreshThumbs()

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
            tool.global_receiveCntrlColor(self.properties.colorSwatchBtn.value)

    def global_receiveCntrlColor(self, color):
        """Receives from all GUIs, changes the color"""
        self.properties.colorSwatchBtn.value = color
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
        if self.selObjs:  # check if objs exist as may have been deleted
            deletedObjs = list()
            for obj in self.selObjs:
                if not cmds.objExists(obj):
                    deletedObjs.append(obj)
            if deletedObjs:
                self.selObjs = [x for x in deletedObjs if x not in self.selObjs]
            if not self.selObjs:
                return list()
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

    # ------------------------------------
    # MAIN LOGIC - BUILD
    # ------------------------------------

    def buildControlsAll(self, designShape="", forceCreate=False):
        """Builds all styles depending on the combo value

        Note: Undo is built into this function
        """
        selObjs = cmds.ls(selection=True, long=True)
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj()
        designName = self.currentWidget().browserModel.currentImage
        if not designName:  # no image has been selected
            om2.MGlobal.displayWarning("Please select an asset thumbnail image.")
            return
        if curveTransforms and not forceCreate:  # Replace don't build
            self.replaceWithShapeDesign()
            return
        # Build from scratch
        cmds.select(selObjs, replace=True)
        rotateOffset = controls.convertRotateUpList(self.properties.orientVectorComboBox.value)
        scale = [self.properties.scaleFloat.value, self.properties.scaleFloat.value, self.properties.scaleFloat.value]
        buildType = controls.CONTROL_BUILD_TYPE_LIST[self.properties.buildComboBox.value]
        freeze = self.compactWidget.toolDotsMenu.freezeState.isChecked()
        group = self.compactWidget.toolDotsMenu.groupState.isChecked()
        controlList = controls.buildControlsGUI(buildType=buildType,
                                                folderpath=self.directory,
                                                designName=designName,
                                                rotateOffset=rotateOffset,
                                                scale=scale,
                                                children=self.properties.selHierarchyRadio.value,
                                                rgbColor=self.properties.colorSwatchBtn.value,
                                                postSelectControls=True,
                                                trackScale=True,
                                                lineWidth=-1,
                                                grp=group,
                                                freezeJnts=freeze)
        self.selObjs = controlList
        self.global_sendCntrlSelection()

    # ------------------------------------
    # MAIN LOGIC - EDIT
    # ------------------------------------

    @undodecorator.undoDecorator
    def colorSelected(self, color):
        """Change the selected control color (and potential children) when the color is changed if a selection"""
        self.global_sendCntrlColor()
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj()
        if not curveTransforms:  # then no shapes as nurbsCurves
            return
        controls.colorControlsList(curveTransforms, color, linear=True)

    @undodecorator.undoDecorator
    def replaceCurves(self):
        """Replaces the curves of one shape node from another.  Last selected object remains with it's shape switched"""
        objList = self.filterCurveJoining()
        combinedObject = shapenodes.shapeNodeParentSafe(objList, deleteOriginal=True, reportSuccess=True,
                                                        selectObj=True, delShapeType="nurbsCurve")
        self.selObjs = [combinedObject]

    def replaceWithShapeDesign(self, message=True):
        """Replaces the curves from the combo box shape design list

        Note: Undo is built into this function

        :param message: Report the message to the user?
        :type message: bool
        """
        designName = self.currentWidget().browserModel.currentImage
        if not designName:  # no image has been selected
            om2.MGlobal.displayWarning("Please select an asset thumbnail image.")
            return
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj()
        if not curveTransforms:  # then no shapes as nurbsCurves
            return
        rotateOffset = controls.convertRotateUpList(self.properties.orientVectorComboBox.value)
        controls.replaceControlCuves(curveTransforms,
                                     folderpath=self.directory,
                                     designName=designName,
                                     rotateOffset=rotateOffset,
                                     autoScale=True,
                                     message=False,
                                     maintainLineWidth=True)
        om2.MGlobal.displayInfo("Controls changed to `{}`: {}".format(designName,
                                                                      namehandling.getShortNameList(curveTransforms)))

    @undodecorator.undoDecorator
    def scaleCVs(self, positive=True):
        """UI function that scales nurbs curve objects based on their CVs, will not affect transforms

        :param positive: is the scale bigger positive=True, or smaller positive=False
        :type positive: bool
        """
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj()
        if not curveTransforms:  # Then no shapes as nurbsCurves
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
        scaleComboIndex = 0
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

    @undodecorator.undoDecorator
    def absoluteScale(self, nullTxt=""):
        """Scales all controls from any selected part of the rig, to an exact size give by the GUI"""
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj()
        if not curveTransforms:  # then no shapes as nurbsCurves
            return
        scale = self.properties.scaleFloat.value
        controls.scaleBreakConnectCtrlList(curveTransforms, (scale, scale, scale), relative=False)
        # controls.scaleControlAbsoluteList((scale, scale, scale), curveTransforms)
        cmds.select(deselect=True)

    @undodecorator.undoDecorator
    def rotateCVs(self, positive=True):
        """Rotates CVs by local space rotation"""
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj()
        if not curveTransforms:  # then no shapes as nurbsCurves
            return
        # for alt shift and ctrl keys with left click
        multiplier, reset = keyboardmouse.cntrlShiftMultiplier(shiftMultiply=2.0, ctrlMultiply=0.5)
        rotateComboInt = self.properties.rotateComboBox.value
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

    @undodecorator.undoDecorator
    def offsetColorSelected(self, offsetTuple, resetClicked):
        """Offset the selected control color (and potential children) when the color is changed if there's a selection

        :param offsetTuple: The offset as (hue, saturation, value)
        :type offsetTuple: tuple
        :param resetClicked: Has the reset been activated (alt clicked)
        :type resetClicked: bool
        """
        self.properties.colorSwatchBtn.value = self.compactWidget.colorSwatchBtn.colorLinearFloat()
        self.global_sendCntrlColor()
        if resetClicked:  # set default color
            self.colorSelected(0, 0, 0)
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
        self.colorSelected(self.properties.colorSwatchBtn.value)

    @undodecorator.undoDecorator
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
            self.properties.colorSwatchBtn.value = color
            self.updateFromProperties()  # Update the swatch in the GUI
            self.global_sendCntrlColor()

    @undodecorator.undoDecorator
    def selectControlsByColor(self, color=None):
        """Selects the controls that match the GUI color"""
        if not color:
            color = self.properties.colorSwatchBtn.value
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

    def selectSimilar(self):
        """Select Similar"""
        self.getColorSelected(selectMode=True)  # select similar to the selected object

    def setControlLineWidth(self):
        """Changes the lineWidth attribute of a curve (control) making the lines appear thicker or thinner.

        Note: Don't add @undodecorator.undoDecorator, it doesn't need it"""
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj()
        if not curveTransforms:  # then no shapes as nurbsCurves
            return
        controls.setCurveLineThickness(curveTransforms, self.properties.lineWidthTxt.value)

    @undodecorator.undoDecorator
    def freezeControlTracker(self):
        """Freezes the scale tracker attributes setting them to a scale of 1.0 no matter the current scale"""
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj()
        if not curveTransforms:  # then no shapes as nurbsCurves
            return
        controls.freezeScaleTrackerList(curveTransforms, message=True)

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
            controls.saveControlSelected(newControlName, self.directory, message=True)
            self.refreshThumbs()  # refresh shape/design thumbs

    def deleteShapeDesignFromDisk(self):
        """Deletes specified shape/design from disk, currently Zoo internally and not to zoo_preferences"""
        designName = self.currentWidget().browserModel.currentImage
        self.fullPath = os.path.join(self.directory, "{}.{}".format(designName, cc.CONTROL_SHAPE_EXTENSION))
        okState = self.deleteCurvesPopupWindow(designName)
        if not okState:  # Cancel
            return
        # Delete file and dependency files
        filesFullPathDeleted = zooscenefiles.deleteZooSceneFiles(self.fullPath, message=True)
        self.refreshThumbs()
        om2.MGlobal.displayInfo("Success, File/s Deleted: {}".format(filesFullPathDeleted))

    def renameShapeDesignOnDisk(self):
        designName = self.currentWidget().browserModel.currentImage
        self.fullPath = os.path.join(self.directory, "{}.{}".format(designName, cc.CONTROL_SHAPE_EXTENSION))
        renameText = self.renameCurvesPopupWindow(designName)
        if not renameText:
            return
        fileRenameList = zooscenefiles.renameZooSceneOnDisk(renameText, self.fullPath,
                                                            extension=cc.CONTROL_SHAPE_EXTENSION)
        # newPath = shapelib.renameLibraryShape(designName, newName, message=True)  # Todo:
        if fileRenameList:  # message handled inside function
            self.refreshThumbs()  # refresh shape/design thumbs
            om2.MGlobal.displayInfo("Success Files Renamed: {}".format(fileRenameList))

    # ------------------------------------
    # CONNECTIONS
    # ------------------------------------

    def uiconnections(self):
        """Hooks up the actual button/widgets functionality
        """
        for uiInstance in self.widgets():
            # thumbnail viewer
            uiInstance.browserModel.doubleClicked.connect(self.buildControlsAll)
            # build
            uiInstance.changeBtn.clicked.connect(self.buildControlsAll)
            uiInstance.buildMatchBtn.clicked.connect(partial(self.buildControlsAll, forceCreate=True))
            # dots menu viewer
            uiInstance.miniBrowser.dotsMenu.applyAction.connect(self.buildControlsAll)
            uiInstance.miniBrowser.dotsMenu.createAction.connect(self.saveControlsToLibrary)
            uiInstance.miniBrowser.dotsMenu.renameAction.connect(self.renameShapeDesignOnDisk)
            uiInstance.miniBrowser.dotsMenu.browseAction.connect(self.openPresetFolder)
            uiInstance.miniBrowser.dotsMenu.setDirectoryAction.connect(self.setControlShapesDirectory)
            uiInstance.miniBrowser.dotsMenu.deleteAction.connect(self.deleteShapeDesignFromDisk)
            uiInstance.miniBrowser.dotsMenu.refreshAction.connect(self.refreshThumbs)
            uiInstance.miniBrowser.dotsMenu.uniformIconAction.connect(self.uniformIconToggle)
            # color
            uiInstance.colorSwatchBtn.colorChanged.connect(self.colorSelected)
            uiInstance.colorSwatchBtn.offsetClicked.connect(self.offsetColorSelected)
            # edit
            uiInstance.orientVectorComboBox.itemChanged.connect(self.replaceWithShapeDesign)
            uiInstance.scaleFloat.textModified.connect(self.absoluteScale)
            # offset
            uiInstance.scaleDownBtn.clicked.connect(partial(self.scaleCVs, positive=False))
            uiInstance.scaleUpBtn.clicked.connect(partial(self.scaleCVs, positive=True))
            uiInstance.rotatePosBtn.clicked.connect(partial(self.rotateCVs, positive=True))
            uiInstance.rotateNegBtn.clicked.connect(partial(self.rotateCVs, positive=False))
            # Tool Dots Menu
            uiInstance.toolDotsMenu.getColor.connect(self.getColorSelected)
            uiInstance.toolDotsMenu.selectSimilar.connect(self.selectSimilar)
            uiInstance.toolDotsMenu.selectColor.connect(self.selectControlsByColor)
            uiInstance.toolDotsMenu.setDefaultScale.connect(self.freezeControlTracker)


class AllWidgets(QtWidgets.QWidget):
    """Create all the widgets for all GUIs, compact and advanced etc"""

    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None, directory=None,
                 uniformIcons=True):
        """Builds the main widgets for the IBL light UIs, no layouts and no connections:

            uiMode - 0 is compact (UI_MODE_COMPACT)
            uiMode - 1 is medium (UI_MODE_MEDIUM)
            ui mode - 2 is advanced (UI_MODE_ADVANCED)

        properties is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        :param uiMode: 0 is compact ui mode, 1 is medium ui mode, 2 is advanced ui mode
        :type uiMode: int
        :param toolsetWidget: the widget of the toolset
        :type toolsetWidget: qtObject
        :param directory: directory path of the light preset zooScene files
        :type directory: str
        """
        super(AllWidgets, self).__init__(parent=parent)
        self.toolsetWidget = toolsetWidget
        self.properties = properties
        self.uiMode = uiMode
        # Thumbnail Viewer ---------------------------------------
        self.themePref = preference.interface("core_interface")
        # viewer widget and model
        self.miniBrowser = elements.MiniBrowser(columns=3, toolsetWidget=self.toolsetWidget, fixedHeight=382,
                                                uniformIcons=uniformIcons,
                                                applyIcon="starControl",
                                                itemName="Shape Control",
                                                createText="Save New",
                                                applyText="Change/Build Ctrl")
        self.miniBrowser.dotsMenu.setSnapshotActive(True)
        self.browserModel = modelcontrolcurves.ControlCurvesViewerModel(self.miniBrowser, directory=directory,
                                                                        chunkCount=200, uniformIcons=uniformIcons)
        self.miniBrowser.setModel(self.browserModel)
        self.resizerWidget = ToolsetResizer(toolsetWidget=self.toolsetWidget, target=self.miniBrowser)
        self.miniBrowser.itemSelectionChanged.connect(self.selectionChanged)
        # Tool Dots Menu
        self.toolDotsMenu = DotsMenu()
        # Rotate --------------------------------------
        toolTip = "Rotate the selected curves controls on this axis.\n" \
                  "The rotation is performed in the shape's object space\n" \
                  "not in its local space.\n" \
                  "Does not affect channel box rotate values."
        self.rotateComboBox = elements.ComboBoxRegular("",
                                                       cc.ROTATE_LIST,
                                                       toolTip=toolTip,
                                                       setIndex=0)
        toolTip = "Rotate the selected control\n(Shift faster, ctrl slower, alt reset)"
        self.rotatePosBtn = elements.styledButton("",
                                                  "arrowRotLeft",
                                                  self,
                                                  toolTip=toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=uic.BTN_W_ICN_SML)
        self.rotateNegBtn = elements.styledButton("", "arrowRotRight",
                                                  self,
                                                  toolTip=toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=uic.BTN_W_ICN_SML)
        # Orient Up Vector --------------------------------------
        toolTipUpAxis = "Select the up axis orientation. \n" \
                        "+X for joints \n" \
                        "+Y for world controls flat on ground\n" \
                        "+Z for front facing in world"
        self.orientVectorComboBox = elements.ComboBoxRegular("",
                                                             COMBO_UP_LIST,
                                                             toolTip=toolTipUpAxis,
                                                             setIndex=0,
                                                             boxRatio=1,
                                                             labelRatio=2)
        # Color label/color cmds widget  ----------------------------------------------------------------------
        # Color Section  ------------------------------------
        toolTip = "The color of the control to be created or selected controls."
        if self.uiMode == UI_MODE_COMPACT:  # build compact color widget
            self.colorSwatchBtn = elements.MayaColorHsvBtns(text="",
                                                            color=cc.CONTROL_DEFAULT_COLOR,
                                                            parent=parent,
                                                            toolTip=toolTip,
                                                            btnRatio=4,
                                                            labelRatio=2,
                                                            colorWidgetRatio=21,
                                                            hsvRatio=15,
                                                            middleSpacing=uic.SMLPAD,
                                                            resetColor=cc.CONTROL_DEFAULT_COLOR)
        elif self.uiMode == UI_MODE_ADVANCED:  # build hsv buttons
            self.colorSwatchBtn = elements.MayaColorHsvBtns(text="Color",
                                                            color=cc.CONTROL_DEFAULT_COLOR,
                                                            parent=parent,
                                                            toolTip=toolTip,
                                                            btnRatio=4,
                                                            labelRatio=2,
                                                            colorWidgetRatio=21,
                                                            hsvRatio=15,
                                                            middleSpacing=uic.SVLRG,
                                                            resetColor=cc.CONTROL_DEFAULT_COLOR)
            self.colorBtnMenuModeList = [("paintLine", "Get Color From Obj"),
                                         ("cursorSelect", "Select Similar"),
                                         ("cursorSelect", "Select With Color")]
            self.colorBtnMenu = elements.ExtendedMenu(searchVisible=True)
            self.colorSwatchBtn.setMenu(self.colorBtnMenu, modeList=self.colorBtnMenuModeList)  # right click
            self.colorSwatchBtn.setMenu(self.colorBtnMenu,
                                        mouseButton=QtCore.Qt.LeftButton)  # left click, modes set already
            toolTip = "Apply the GUI color to the selected controls."
            self.applyColorBtn = elements.styledButton("",
                                                       "paintLine",
                                                       toolTip=toolTip,
                                                       parent=parent,
                                                       minWidth=uic.BTN_W_ICN_MED,
                                                       maxWidth=uic.BTN_W_ICN_MED)
        # Scale --------------------------------------
        toolTip = "The radius scale size of the control"
        editRatio = 2
        if self.uiMode == UI_MODE_ADVANCED:  # change the ratio for advanced
            editRatio = 1

        self.scaleFloat = elements.FloatEdit("Scale",
                                             "2.0",
                                             labelRatio=1,
                                             editRatio=editRatio,
                                             toolTip=toolTip)
        toolTip = "Scale controls smaller\n(Shift faster, ctrl slower, alt reset)"
        self.scaleDownBtn = elements.styledButton("", "scaleDown",
                                                  toolTip=toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=uic.BTN_W_ICN_SML)
        toolTip = "Scale controls larger\n(Shift faster, ctrl slower, alt reset)"
        self.scaleUpBtn = elements.styledButton("", "scaleUp",
                                                toolTip=toolTip,
                                                style=uic.BTN_TRANSPARENT_BG,
                                                minWidth=uic.BTN_W_ICN_SML)
        # Hierarchy Radio ------------------------------------
        radioNameList = ["Selected", "Hierarchy"]
        radioToolTipList = ["Affect only the selected joints/controls.",
                            "Affect the selection and all of its child joints/controls."]
        self.selHierarchyRadio = elements.RadioButtonGroup(radioList=radioNameList,
                                                           toolTipList=radioToolTipList,
                                                           default=0,
                                                           margins=(0, 0, 0, 0))
        # Build Type Combo --------------------------------------
        toolTip = ""
        self.buildComboBox = elements.ComboBoxRegular("",
                                                      items=controls.CONTROL_BUILD_TYPE_LIST,
                                                      setIndex=1,
                                                      toolTip=toolTip)
        # Change Button ----------------------------------
        toolTip = "Changes all selected controls to the thumbnail. \n" \
                  "If nothing is selected will create at world center. "
        self.changeBtn = elements.styledButton("Change",
                                               "starControl",
                                               parent,
                                               toolTip=toolTip,
                                               style=uic.BTN_DEFAULT)
        # Create Button ----------------------------------
        toolTip = "Builds new control curves, will match to selected object/s. "
        self.buildMatchBtn = elements.styledButton("Create",
                                                   "starControl",
                                                   parent,
                                                   toolTip=toolTip,
                                                   style=uic.BTN_DEFAULT)
        if self.uiMode == UI_MODE_ADVANCED:  # widgets that only exist in the advanced mode
            # Scale Combo ------------------------------------
            toolTip = "Scale the selected curves by all or a single axis\n" \
                      "The scale is performed in the shape's object space\n" \
                      "not in its local space.\n" \
                      "Does not affect channel box scale values."
            self.scaleComboBx = elements.ComboBoxRegular("",
                                                         cc.SCALE_LIST,
                                                         parent,
                                                         toolTip=toolTip,
                                                         setIndex=0)
            # Line Width ------------------------------------
            toolTip = "Sets the thickness of the control curve lines.\n" \
                      "A line thickness of -1 uses the global preferences setting, usually 1."
            self.lineWidthTxt = elements.IntEdit(label="Line Width",
                                                    editText="-1",
                                                    labelRatio=1,
                                                    editRatio=1,
                                                    toolTip=toolTip)
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
            # Orient Up Axis ------------------------------------
            self.upAxisLabel = elements.Label(text="Up Axis", toolTip=toolTipUpAxis)
            # Set Default Scale Button ------------------------------------
            toolTip = "Set the current scale of the control to be it's default scale.\n" \
                      "Useful while resetting. To reset alt-click the scale elements."
            self.setScaleBtn = elements.styledButton(text="Set Default Scale",
                                                     icon="freezeSrt",
                                                     toolTip=toolTip,
                                                     parent=parent,
                                                     style=uic.BTN_LABEL_SML)
            # Group ------------------------------------
            toolTip = "Add groups to zero out the controls/joints (recommended)"
            self.grpJointsCheckBx = elements.CheckBox("Group",
                                                      checked=True,
                                                      parent=parent,
                                                      toolTip=toolTip)
            # Freeze Joints ------------------------------------
            toolTip = "Freeze transform joints only, while adding `Joint Controls` (recommended)"
            self.freezeJntsCheckBx = elements.CheckBox("Freeze Jnt",
                                                       checked=True,
                                                       parent=parent,
                                                       toolTip=toolTip)

    def selectionChanged(self, image, item):
        """ Set the infoEmbedWindow nameEdit to disabled if its one of the default controls

        :param image:
        :type image:
        :param item:
        :type item:
        :return:
        :rtype:
        """
        thumbView = self.sender()  # type: elements.MiniBrowser
        thumbView.infoEmbedWindow.nameEdit.setEnabled(not (item.name in self.toolsetWidget.defaultControls()))


class DotsMenu(IconMenuButton):
    menuIcon = "menudots"

    groupEnabled = QtCore.Signal(object)
    freezeEnabled = QtCore.Signal(object)

    getColor = QtCore.Signal()
    selectSimilar = QtCore.Signal()
    selectColor = QtCore.Signal()

    setDefaultScale = QtCore.Signal()

    def __init__(self, parent=None):
        """
        """
        super(DotsMenu, self).__init__(parent=parent)
        iconColor = THEME_PREFS.ICON_PRIMARY_COLOR
        self.setIconByName(self.menuIcon, size=16, colors=iconColor)
        self.setMenuAlign(QtCore.Qt.AlignRight)
        self.setToolTip("File menu. Control Creator")
        # Build the static menu
        # Enable Checkboxes --------------------------------------
        self.groupState = self.addAction("Group New Controls",
                                         connect=lambda x: self.groupEnabled.emit(x),
                                         checkable=True,
                                         checked=True)
        self.freezeState = self.addAction("Freeze New Controls",
                                          connect=lambda x: self.freezeEnabled.emit(x),
                                          checkable=True,
                                          checked=True)
        # Reset To Defaults --------------------------------------
        self.addSeparator()
        colorIcon = iconlib.iconColorized("paintLine", utils.dpiScale(16))
        self.addAction("Get Color", connect=lambda: self.getColor.emit(), icon=colorIcon)

        cursorIcon = iconlib.iconColorized("cursorSelect", utils.dpiScale(16))
        self.addAction("Select Similar Color", connect=lambda: self.selectSimilar.emit(), icon=cursorIcon)

        self.addAction("Select From Color", connect=lambda: self.selectColor.emit(), icon=cursorIcon)
        # Reset To Defaults --------------------------------------
        self.addSeparator()
        scaleIcon = iconlib.iconColorized("freezeSrt", utils.dpiScale(16))
        self.addAction("Set Default Scale", connect=lambda: self.setDefaultScale.emit(), icon=scaleIcon)


class GuiCompact(AllWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None, directory=None,
                 uniformIcons=True):
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
        super(GuiCompact, self).__init__(parent=parent, properties=properties,
                                         uiMode=uiMode, toolsetWidget=toolsetWidget, directory=directory,
                                         uniformIcons=uniformIcons)
        # Main Layout
        mainLayout = elements.vBoxLayout(self,
                                         margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=0)
        # Rotate Layout
        rotateLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SLRG)
        rotateLayout.addWidget(self.rotateComboBox, 4)
        rotateLayout.addWidget(self.rotatePosBtn, 1)
        rotateLayout.addWidget(self.rotateNegBtn, 1)
        # Color Layout
        colorLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SLRG)
        colorLayout.addWidget(self.colorSwatchBtn, 1)
        # Combo Dots Layout
        comboDotsLayout = elements.hBoxLayout(spacing=uic.SLRG)
        comboDotsLayout.addWidget(self.orientVectorComboBox, 4)
        comboDotsLayout.addItem(elements.Spacer(32, 5))
        comboDotsLayout.addWidget(self.toolDotsMenu, 1)
        # Scale Layout
        scaleLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SLRG)
        scaleLayout.addWidget(self.scaleFloat, 4)
        scaleLayout.addWidget(self.scaleDownBtn, 1)
        scaleLayout.addWidget(self.scaleUpBtn, 1)
        # Bottom Grid Layout
        gridLayout = elements.GridLayout(margins=(0, 0, 0, 0), spacing=uic.SLRG)

        gridLayout.addLayout(colorLayout, 0, 0)
        gridLayout.addLayout(comboDotsLayout, 0, 1)
        gridLayout.addLayout(scaleLayout, 1, 0)
        gridLayout.addLayout(rotateLayout, 1, 1)
        gridLayout.addWidget(self.buildComboBox, 2, 0)
        gridLayout.addWidget(self.selHierarchyRadio, 2, 1)
        gridLayout.addWidget(self.changeBtn, 3, 0)
        gridLayout.addWidget(self.buildMatchBtn, 3, 1)

        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)

        # Add to main layout
        mainLayout.addWidget(self.miniBrowser)
        mainLayout.addWidget(self.resizerWidget)
        mainLayout.addLayout(gridLayout)
        mainLayout.addStretch(1)


class GuiAdvanced(AllWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_ADVANCED, toolsetWidget=None, directory=None,
                 uniformIcons=True):
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
        super(GuiAdvanced, self).__init__(parent=parent, properties=properties,
                                          uiMode=uiMode, toolsetWidget=toolsetWidget, directory=directory,
                                          uniformIcons=uniformIcons)
        # Main Layout
        mainLayout = elements.vBoxLayout(self,
                                         margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=0)
        # Rotate Layout
        rotateLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SLRG)
        rotateLayout.addWidget(self.rotateComboBox, 4)
        rotateLayout.addWidget(self.rotatePosBtn, 1)
        rotateLayout.addWidget(self.rotateNegBtn, 1)
        # Scale Layout
        scaleLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SLRG)
        scaleLayout.addWidget(self.scaleComboBx, 4)
        scaleLayout.addWidget(self.scaleDownBtn, 1)
        scaleLayout.addWidget(self.scaleUpBtn, 1)
        # Color Layout
        colorLayout = elements.hBoxLayout(margins=(0, uic.SSML, 0, uic.SREG), spacing=uic.SLRG)
        colorLayout.addWidget(self.colorSwatchBtn, 8)
        colorLayout.addWidget(self.applyColorBtn, 1)
        # Up Axis Layout
        upAxisLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SLRG)
        upAxisLayout.addWidget(self.orientVectorComboBox, 1)
        # Top Grid Layout
        gridLayout1 = elements.GridLayout(margins=(0, 0, 0, 0), hSpacing=uic.SLRG, vSpacing=uic.SREG)
        gridLayout1.addWidget(self.scaleFloat, 0, 0)
        gridLayout1.addLayout(scaleLayout, 0, 1)
        gridLayout1.addWidget(self.lineWidthTxt, 1, 0)
        gridLayout1.addLayout(rotateLayout, 1, 1)
        gridLayout1.setColumnStretch(0, 1)
        gridLayout1.setColumnStretch(1, 1)
        # Bottom Grid Layout
        gridLayout2 = elements.GridLayout(margins=(0, 0, 0, 0), hSpacing=uic.SLRG, vSpacing=uic.SREG)
        gridLayout2.addWidget(self.selectColorBtn, 0, 0)
        gridLayout2.addWidget(self.getColorBtn, 0, 1)
        gridLayout2.addLayout(upAxisLayout, 1, 0)
        gridLayout2.addWidget(self.setScaleBtn, 1, 1)
        gridLayout2.addWidget(self.grpJointsCheckBx, 3, 0)
        gridLayout2.addWidget(self.freezeJntsCheckBx, 3, 1)
        gridLayout2.addWidget(self.buildComboBox, 2, 0)
        gridLayout2.addWidget(self.selHierarchyRadio, 2, 1)
        gridLayout2.addWidget(self.changeBtn, 4, 0)
        gridLayout2.addWidget(self.buildMatchBtn, 4, 1)

        gridLayout2.setColumnStretch(0, 1)
        gridLayout2.setColumnStretch(1, 1)

        # Add to main layout
        mainLayout.addWidget(self.miniBrowser)
        mainLayout.addWidget(self.resizerWidget)
        mainLayout.addLayout(gridLayout1)
        mainLayout.addLayout(colorLayout)
        mainLayout.addLayout(gridLayout2)
        mainLayout.addStretch(1)
