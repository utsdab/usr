from functools import partial

from Qt import QtWidgets, QtCore

import maya.mel as mel
import maya.api.OpenMaya as om2
import maya.cmds as cmds

from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.libs.maya.cmds.general import undodecorator
from zoo.apps.toolsetsui import toolsetui

from zoo.libs.maya.qt import cmdswidgets
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.utils.colors.colorpalettes import PASTEL_PALETTE, NEON_PALETTE, CAMPFIRE_PALETTE, CONTRAD_PALETTE, \
    LRXD_PALETTE, PRIMARIES_PALETTE, SATURATED_PALETTE, MIDDLE_PALETTE, FADED_PALETTE, SATURATED_FULL_PALETTE, \
    MIDDLE_FULL_PALETTE, FADED_FULL_PALETTE, DARK_PALETTE
from zoo.libs.maya.utils.mayacolors import MAYA_COLOR_SRGB
from zoo.libs.maya.cmds.objutils import objcolor, filtertypes, shapenodes
from zoo.libs.maya.cmds.rig import controls

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1
SATURATED_TXT = "Saturated"
MIDDLE_TXT = "Middle"
FADED_TXT = "Faded"
SATURATEDFULL_TXT = "Saturated Full"
MIDDLEFULL_TXT = "Middle Full"
FADEDFULL_TXT = "Faded Full"
DARK_TXT = "Dark"
PASTEL_TXT = "Pastel"
NEON_TXT = "Neon"
CONTRAD_TXT = "Contrad"
CAMPFIRE_TXT = "Campfire"
MAYADEFAULT_TXT = "Maya Default"
LRXD_TXT = "LRXD"
PRIMARIES_TXT = "Primaries"

# There are three palettes to cycle through, hide/show
DISPLAY_PALETTE_MAYA = 0
DISPLAY_PALETTE_HUE = 1
DISPLAY_PALETTE_CUSTOM = 2

# Palettes with 10 colors
CUSTOM_PALETTE_LIST = [PASTEL_TXT, NEON_TXT, CONTRAD_TXT, CAMPFIRE_TXT, LRXD_TXT, PRIMARIES_TXT]
# Palettes with 20 colors
HUE_PALETTE_LIST = [SATURATED_TXT, MIDDLE_TXT, FADED_TXT, SATURATEDFULL_TXT, MIDDLEFULL_TXT, FADEDFULL_TXT]
# All palette options, add Maya with 32 colors
FULL_PALETTE_LIST = HUE_PALETTE_LIST + CUSTOM_PALETTE_LIST + [MAYADEFAULT_TXT]

FULL_PALETTE_DICT = {PASTEL_TXT: PASTEL_PALETTE,
                     NEON_TXT: NEON_PALETTE,
                     CONTRAD_TXT: CONTRAD_PALETTE,
                     CAMPFIRE_TXT: CAMPFIRE_PALETTE,
                     LRXD_TXT: LRXD_PALETTE,
                     PRIMARIES_TXT: PRIMARIES_PALETTE,
                     MIDDLE_TXT: MIDDLE_PALETTE,
                     MIDDLEFULL_TXT: MIDDLE_FULL_PALETTE,
                     SATURATED_TXT: SATURATED_PALETTE,
                     SATURATEDFULL_TXT: SATURATED_FULL_PALETTE,
                     DARK_TXT: DARK_PALETTE,
                     FADEDFULL_TXT: FADED_PALETTE,
                     FADED_TXT: FADED_FULL_PALETTE,
                     MAYADEFAULT_TXT: []}


class ColorOverrides(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "colorOverrides"
    uiData = {"label": "Color Overrides",
              "icon": "paintLine",
              "tooltip": "Color Control Shapes Palette",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-color-overrides/"
              }

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run"""
        self.selObjs = list()
        self.customPalette = PASTEL_PALETTE

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
        self.uiModeList()
        self.uiConnections()
        self.updateColorPalette(uiSetup=True)

    def defaultAction(self):
        """Double Click"""
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
        """Used to store and update UI data

        For use in the GUI use:
            current value: self.properties.itemName.value
            default value (automatic): self.properties.itemName.default

        To connect Qt widgets to property methods use:
            self.toolsetWidget.linkProperty(self.widgetQtName, "itemName")

        :return properties: special dictionary used to save and update all GUI widgets
        :rtype properties: list(dict)
        """
        return [{"name": "color", "value": (0.16, 0.3, 0.875)},
                {"name": "curveCheckBox", "value": True},
                {"name": "meshCheckBox", "value": False},
                {"name": "otherCheckBox", "value": False},
                {"name": "outlinerCheckBox", "value": False},
                {"name": "paletteCombo", "value": 1}]

    # ------------------
    # MENU
    # ------------------

    def menuColor(self):
        uiInstance = self.currentWidget()
        menuColorTxt = uiInstance.colorBtnMenu.currentMenuItem()
        if menuColorTxt == uiInstance.colorBtnMenuModeList[0][1]:  # the menu text from [0]
            self.getColorSelected()
        elif menuColorTxt == uiInstance.colorBtnMenuModeList[1][1]:  # the menu text from [1]
            self.getColorSelected(selectMode=True)  # select similar to the selected object
        elif menuColorTxt == uiInstance.colorBtnMenuModeList[2][1]:  # the menu text from [2]
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
        if self.properties.curveCheckBox.value:  # only receive if curves in checked
            self.selObjs = selObjs

    def global_sendCntrlColor(self, color=list()):
        """Updates all GUIs with the current color"""
        if self.properties.curveCheckBox.value:
            toolsets = toolsetui.toolsets(attr="global_receiveCntrlColor")
            for tool in toolsets:
                if not color:
                    tool.global_receiveCntrlColor(self.properties.color.value)
                else:
                    tool.global_receiveCntrlColor(color)

    def global_receiveCntrlColor(self, color):
        """Receives from all GUIs, changes the color"""
        if self.properties.curveCheckBox.value:  # only receive if curves in checked
            self.properties.color.value = color
            self.updateFromProperties()

    # ------------------
    # HELPER LOGIC
    # ------------------

    def returnAllSceneNodesGUI(self):
        """Searches the whole scene for matches to the top filter types in the GUI (checkboxes)"""
        otherFilterTypesList = list()
        otherObjs = list()
        curves = list()
        joints = list()
        geometry = list()
        if self.properties.curveCheckBox.value:
            curves = filtertypes.filterByNiceType(filtertypes.CURVE, searchHierarchy=False, selectionOnly=False,
                                                  dag=False, removeMayaDefaults=True, transformsOnly=True,
                                                  message=False)
        if self.properties.meshCheckBox.value:
            geometry = filtertypes.filterByNiceType(filtertypes.GEOMETRY, searchHierarchy=False, selectionOnly=False,
                                                    dag=False, removeMayaDefaults=True, transformsOnly=True,
                                                    message=False)
        if self.properties.otherCheckBox.value:
            otherFilterTypesList.append(filtertypes.LOCATOR)
            otherFilterTypesList.append(filtertypes.CAMERA)
            otherFilterTypesList.append(filtertypes.LIGHT)
            otherFilterTypesList.append(filtertypes.DEFORMER)
            for objFilter in otherFilterTypesList:
                otherObjs += filtertypes.filterByNiceType(objFilter, searchHierarchy=False, selectionOnly=False,
                                                          dag=False, removeMayaDefaults=True, transformsOnly=True,
                                                          message=False)
            joints = filtertypes.filterByNiceType(filtertypes.JOINT, searchHierarchy=False, selectionOnly=False,
                                                  dag=False, removeMayaDefaults=True, transformsOnly=True,
                                                  message=False)
        return curves, geometry, otherObjs, joints

    def getFilteredObjsJoints(self):
        """Returns joint and object lists for coloring from the GUI.  Objs and joints must be returned separately.

        Returned objs will affect their shape nodes, joints will affect their transform:

            1. Color Shape nodes: In most cases (drawing override)
            2. Color Transform nodes: Joints (drawing override)

        :return objs: Object list of objects who's shape nodes should be colored.
        :rtype objs: list(str)
        :return joints: Joint list, these joint colors will be affected as transforms, not shapes.
        :rtype joints: list(str)
        """
        objs = list()
        joints = list()
        if not self.updateSelectedObjs(message=True, deselect=False):  # updates self.selObjs
            return objs, joints
        # There is selection so filter via the GUI  --------------------------------
        for filterType in self.getfilterTypes():  # Returns transforms (for shape node colors). Filters via GUI
            objs += self.filterType(filterType, message=False, deselect=True)
        if self.properties.otherCheckBox.value:  # Returns joints
            joints = self.filterType(filtertypes.JOINT, message=False, deselect=True)
        if objs:  # Shape Node objects set the colors
            objs = list(set(objs))  # remove duplicates
        return objs, joints

    def getFilteredObjsJointsState(self):
        """Returns joint and object lists for coloring from the GUI.  Also returns colorState, if False, nothing found

        Obj lists will affect their shape nodes, joints will affect their transform:

            1. Color Shape nodes: In most cases (drawing override)
            2. Color Transform nodes: Joints (drawing override)

        The last option returned colorState is related to Outliner colors.  If colorState is True then nodes have been \
        found to color.

        :return objs: Object list of objects who's shape nodes should be colored.
        :rtype objs: list(str)
        :return joints: Joint list, these joint colors will be affected as transforms, not shapes.
        :rtype joints: list(str)
        :return colorState: If True nodes have been found to color.
        :rtype colorState: bool
        """
        objs, joints = self.getFilteredObjsJoints()  # return filtered objs (will color shapes) and joints
        if not objs and not joints and not self.selObjs:  # Bail nothing found
            return objs, joints, False
        if not objs and not joints and not self.properties.outlinerCheckBox.value:  # Bail nothing found
            return objs, joints, False
        return objs, joints, True

    def getfilterTypes(self):
        """Returns the filtered objects related to the GUI settings and shape nodes (not joints or outliner)

        For more info on filterTypesList see filterTypesList.filterByNiceType()

        :return filterTypesList: The nice name type list,  more documentation at filterTypesList.filterByNiceType()
        :rtype filterTypesList: str
        """
        filterTypesList = list()
        if self.properties.curveCheckBox.value:
            filterTypesList.append(filtertypes.CURVE)
        if self.properties.meshCheckBox.value:
            filterTypesList.append(filtertypes.GEOMETRY)
        if self.properties.otherCheckBox.value:
            filterTypesList.append(filtertypes.LOCATOR)
            filterTypesList.append(filtertypes.CAMERA)
            filterTypesList.append(filtertypes.LIGHT)
            filterTypesList.append(filtertypes.DEFORMER)
        return filterTypesList

    def filterType(self, filterType, message=True, deselect=True):
        """Uses the selection stored in special variable self.selObjs to filter objects by nicename type

        For more information about nicename type see the documentation for filterTypes.filterByNiceType()

        :param filterType: The nicename type as per documentation from filterTypes.filterByNiceType()
        :type filterType: str
        :param message: Report the message to the user
        :type message: bool
        :param deselect: Deselect the objects after storing the list?
        :type deselect: bool
        :return selObjs: The selected objects now filtered
        :rtype selObjs: list(str)
        """
        cmds.select(self.selObjs, replace=True)
        selObjs = filtertypes.filterByNiceType(filterType, searchHierarchy=False,
                                               selectionOnly=True, dag=False,
                                               removeMayaDefaults=True, transformsOnly=True, message=False)
        if not selObjs:
            if message:
                om2.MGlobal.displayWarning("No objects found of type: {}".format(filterType))
        if deselect:
            cmds.select(deselect=True)
        return selObjs

    def updateSelectedObjs(self, message=True, deselect=True):
        """Remembers the object selection so objects can be deselected while changing

        Updates self.selObjs

        :param message: Report the message to the user if nothing selected
        :type message: bool
        :param message: Deselect the objects after recording the objList?
        :type message: bool
        :return isSelection: False if nothing is selected
        :rtype isSelection: bool
        """
        newSelection = cmds.ls(selection=True, long=True)
        if newSelection:
            self.selObjs = newSelection
            if self.properties.curveCheckBox.value:  # only receive if curves in checked
                self.global_sendCntrlSelection()  # updates all GUIs
        if not self.selObjs:
            om2.MGlobal.displayWarning("Please select controls/curves.")
            return False
        if deselect:
            cmds.select(deselect=True)
        return True

    # ------------------
    # UI LOGIC
    # ------------------

    def updateColorPalette(self, comboInt=None, comboTxt=None, uiSetup=False):
        """Update the colors depending on the drop-box settings"""
        for uiInstance in self.uiInstanceList:
            paletteTxt = FULL_PALETTE_LIST[self.properties.paletteCombo.value]
            self.paletteDisplay = DISPLAY_PALETTE_MAYA
            # Update the palette colors ----------------
            if len(FULL_PALETTE_DICT[paletteTxt]) == 20:  # Then is hue palette with 30
                self.customPalette = list(FULL_PALETTE_DICT[paletteTxt])  # make unique
                uiInstance.colorPaletteHOffset.updatePaletteColors(self.customPalette)
                self.paletteDisplay = DISPLAY_PALETTE_HUE
            elif paletteTxt == MAYADEFAULT_TXT:  # Is the maya palette
                pass  # Do nothing
            elif len(FULL_PALETTE_DICT[paletteTxt]) == 10:  # Is a custom palette
                self.customPalette = list(FULL_PALETTE_DICT[paletteTxt])  # make unique
                uiInstance.colorPaletteListCustom.updatePaletteColors(self.customPalette)
                self.paletteDisplay = DISPLAY_PALETTE_CUSTOM
            # Update the palette Connections ----------------
            if uiSetup:  # Only run on start
                self.setPaletteHueConnections()
                self.setPaletteCustomConnections()
            else:  # reset palette connections
                if self.paletteDisplay == DISPLAY_PALETTE_HUE:
                    self.resetPaletteHueConnections()
                elif self.paletteDisplay == DISPLAY_PALETTE_CUSTOM:
                    self.resetPaletteCustomConnections()
            # Hide show the palettes ----------------
            self.displayPalette()

    def displayPalette(self):
        """Shows and hides any of the three color palettes depending on the drop-down menu"""
        for uiInstance in self.uiInstanceList:
            if self.paletteDisplay == DISPLAY_PALETTE_MAYA:
                uiInstance.colorPaletteListMaya.show()
                uiInstance.colorPaletteHOffset.hide()
                uiInstance.colorPaletteListCustom.hide()
            elif self.paletteDisplay == DISPLAY_PALETTE_CUSTOM:
                uiInstance.colorPaletteListMaya.hide()
                uiInstance.colorPaletteHOffset.hide()
                uiInstance.colorPaletteListCustom.show()
            else:  # Will be hue
                uiInstance.colorPaletteListMaya.hide()
                uiInstance.colorPaletteHOffset.show()
                uiInstance.colorPaletteListCustom.hide()

    # ------------------
    # MAIN LOGIC
    # ------------------

    def getColorSelected(self, selectMode=False):
        """Get the color of the first selected object and update the GUI"""
        # Filter as per the GUI ------------------
        objs, joints, colorState = self.getFilteredObjsJointsState()
        if not colorState:  # Bail nothing found
            om2.MGlobal.displayWarning("No objects with the current GUI filters could be found")
            return
        # Main, get the colors  --------------------------------------
        if objs:  # Shape Node objects get the color

            firstShapeNode = shapenodes.filterShapesInList(objs)[0]
            color = objcolor.getRgbColor(firstShapeNode, hsv=False, linear=True)
        elif joints:  # return the transform color
            color = objcolor.getRgbColor(joints[0], hsv=False, linear=True)
        else:  # return the outliner color
            color = objcolor.getOutlinerColors(self.selObjs[0], returnLinear=True)
        if selectMode:  # select similar objects
            self.selectControlsByColor(color=color)
        else:  # just update the GUI
            self.properties.color.value = color
            self.updateFromProperties()  # Update the swatch in the GUI
            self.global_sendCntrlColor()

    def setColor(self):
        """Sets the color to the control based on the GUI"""
        self.colorSelected(self.properties.color.value)

    @undodecorator.undoDecorator
    def colorSelected(self, color):
        """Change the selected obj color (and potential children) when the color is changed if a selection

        This method is made difficult by the GUI filtering which can be:

            1. Color Shape nodes: In most cases (drawing override)
            2. Color Transform nodes: Joints (drawing override)
            3. Color Outliner colors: all node types and is a different attribute type (Use Outliner Color)

        Filters objects from the GUI, color is in linear float
        """
        self.global_sendCntrlColor(color=color)
        objs, joints, colorState = self.getFilteredObjsJointsState()
        if not colorState:  # Bail nothing found
            om2.MGlobal.displayWarning("No objects with the current GUI filters could be found")
            return
        # Main, set the colors  --------------------------------------
        if objs:  # Shape Node objects set the colors
            objcolor.setColorListRgb(objs, color, displayMessage=False, linear=True)
        if joints:  # Set joints colour on the transform not the shape node/s
            objcolor.setColorListRgb(joints, color, colorShapes=False, displayMessage=False, linear=True)
        if self.properties.outlinerCheckBox.value:  # set Outliner here, color is in linear so set flag to True
            objcolor.setOutlinerColorList(self.selObjs, color, incomingIsLinear=True)
            mel.eval("AEdagNodeCommonRefreshOutliners();")  # manually refresh the outliner
            cmds.select(deselect=True)  # deselect as may not be deselected already
        # If curves then update color tracker attr if tracker info exists
        if self.properties.curveCheckBox.value and objs:
            curveObjs = filtertypes.filterTypeReturnTransforms(objs, children=False, shapeType="nurbsCurve")
            controls.colorUpdateTrackerList(curveObjs, color)
        # Update GUI Main Color picker  ---------------------------------
        self.properties.color.value = color
        self.updateFromProperties()

    @undodecorator.undoDecorator
    def offsetColorSelected(self, offsetTuple, resetClicked):
        """Offset the selected control color (and potential children) when the color is changed if there's a selection

        :param offsetTuple: The offset as (hue 0-360, saturation 0-1, value 0-1)
        :type offsetTuple: tuple
        :param resetClicked: Has the reset been activated (alt clicked)
        :type resetClicked: bool
        """
        self.updateSelectedObjs(deselect=True)  # for outliner if checked on
        self.properties.color.value = self.advancedWidget.colorHsvBtns.colorLinearFloat()  # can only be in adv
        self.global_sendCntrlColor()
        # Do the offset
        if resetClicked:  # set default color
            self.colorSelected(self.properties.color.default)
            return
        # Filter as per the GUI ------------------
        objs, joints, colorState = self.getFilteredObjsJointsState()
        if not colorState:  # Bail nothing found
            om2.MGlobal.displayWarning("No objects with the current GUI filters could be found")
            return
        # Do the color offset ------------------
        offsetFloat, hsvType = objcolor.convertHsvOffsetTuple(offsetTuple)
        if objs:  # then affect their shape nodes
            objcolor.offsetListHsv(objs, colorShapes=True, offset=offsetFloat, hsvType=hsvType, displayMessage=False)
        if joints:  # then affect the transforms
            objcolor.offsetListHsv(joints, colorShapes=False, offset=offsetFloat, hsvType=hsvType, displayMessage=False)
        if self.properties.outlinerCheckBox.value:  # affect the outliner colors
            objcolor.offsetOutlinerColorListHsv(self.selObjs, offsetFloat, hsvType=hsvType, displayMessage=True)
            mel.eval("AEdagNodeCommonRefreshOutliners();")  # manually refresh the outliner

    def selectControlsByColor(self, color=None):
        """Selects objects by their color depending on the filter GUI settings"""
        # Filter as per the GUI ------------------
        if not color:
            color = self.properties.color.value
        curves, geometry, otherObjs, joints = self.returnAllSceneNodesGUI()
        if not curves and not geometry and not otherObjs and not self.properties.outlinerCheckBox.value:  # Bail
            om2.MGlobal.displayWarning("No objects with the current GUI filters could be found in the scene")
            return
        # select by color -------------
        matchObjs = list()
        if curves:
            matchObjs += objcolor.selectObjsByColor(curves, color, queryShapes=True, message=False, selectObjs=False)
        if geometry:
            matchObjs += objcolor.selectObjsByColor(geometry, color, queryShapes=True, message=False, selectObjs=False)
        if otherObjs:
            matchObjs += objcolor.selectObjsByColor(otherObjs, color, queryShapes=True, message=False, selectObjs=False)
        if joints:  # from transform, not shapes
            matchObjs += objcolor.selectObjsByColor(joints, color, queryShapes=False, message=False, selectObjs=False)
        # search whole scene for outliner colors
        if self.properties.outlinerCheckBox.value:
            allSceneTransforms = filtertypes.filterAllNodeTypes(selectionOnly=False, searchHierarchy=False, dag=False,
                                                                transformsOnly=True, removeMayaDefaults=True,
                                                                message=False)
            matchObjs += objcolor.selectObjsByOutlinerColor(allSceneTransforms, color, tolerance=0.05,
                                                            incomingLinear=True, selectObjs=False)
        if not matchObjs:
            om2.MGlobal.displayWarning("No objects found matching the color `{}`".format(color))
            return
        cmds.select(list(set(matchObjs)), replace=True)
        om2.MGlobal.displayInfo("Success: Objs matching color `{}` found.".format(color))

    def resetColors(self):
        """Resets the colors of objects/Outliner depending on the filter GUI settings"""
        self.properties.color.value = self.properties.color.default
        self.global_sendCntrlColor()
        objs, joints, colorState = self.getFilteredObjsJointsState()
        if not colorState:  # Bail nothing found
            om2.MGlobal.displayWarning("No objects with the current GUI filters could be found")
            return
        # Main, reset the colors  --------------------------------------
        if objs:  # reset shape nodes
            objcolor.resetOverrideObjColorList(objs, colorShapes=True)
        if joints:  # reset joints
            objcolor.resetOverrideObjColorList(joints, colorShapes=False)
        if self.properties.outlinerCheckBox.value:  # reset Outliner colors
            objcolor.resetOutlinerColorList(self.selObjs)
            mel.eval("AEdagNodeCommonRefreshOutliners();")  # manually refresh Maya's outliner
            cmds.select(deselect=True)  # deselect as may not be deselected already
        self.updateFromProperties()

    # ------------------
    # CONNECTIONS
    # ------------------

    def resetPaletteHueConnections(self):
        """Resets the btn connections for the hue palette, usually on palette change"""
        for uiInstance in self.uiInstanceList:  # iterate both GUIs
            for i, btn in enumerate(uiInstance.colorPaletteHOffset.colorBtnList):  # hue offset palette buttons
                btn.clicked.disconnect()
            self.setPaletteHueConnections()

    def setPaletteHueConnections(self):
        """Set the connections for the hue color palette"""
        for uiInstance in self.uiInstanceList:  # iterate both GUIs
            for i, btn in enumerate(uiInstance.colorPaletteHOffset.colorBtnList):  # hue offset palette buttons
                color = uiInstance.colorPaletteHOffset.colorListLinear[i]
                btn.clicked.connect(partial(self.colorSelected, color=color))

    def resetPaletteCustomConnections(self):
        """Resets the btn connections for the custom palette, usually on palette change"""
        for uiInstance in self.uiInstanceList:  # iterate both GUIs
            for i, btn in enumerate(uiInstance.colorPaletteListCustom.colorBtnList):  # hue offset palette buttons
                btn.clicked.disconnect()
        self.setPaletteCustomConnections()

    def setPaletteCustomConnections(self):
        """Set the connections for the custom color palette"""
        for uiInstance in self.uiInstanceList:  # iterate both GUIs
            for i, btn in enumerate(uiInstance.colorPaletteListCustom.colorBtnList):  # Maya palette buttons
                color = uiInstance.colorPaletteListCustom.colorListLinear[i]  # update with the latest palette list
                btn.clicked.connect(partial(self.colorSelected, color=color))

    def uiConnections(self):
        """"""
        for uiInstance in self.uiInstanceList:  # iterate both GUIs
            for i, btn in enumerate(uiInstance.colorPaletteListMaya.colorBtnList):  # Maya palette buttons
                color = uiInstance.colorPaletteListMaya.colorListLinear[i]
                btn.clicked.connect(partial(self.colorSelected, color=color))
            uiInstance.paletteCombo.itemChanged.connect(self.updateColorPalette)
            uiInstance.resetColorBtn.clicked.connect(self.resetColors)
            uiInstance.colorBtnMenu.menuChanged.connect(self.menuColor)
        self.compactWidget.colorPickerBtn.colorChanged.connect(self.colorSelected)
        self.advancedWidget.applyColorBtn.clicked.connect(self.setColor)
        self.advancedWidget.colorHsvBtns.colorChanged.connect(self.colorSelected)
        self.advancedWidget.colorHsvBtns.offsetClicked.connect(self.offsetColorSelected)
        self.advancedWidget.getColorBtn.clicked.connect(self.getColorSelected)
        self.advancedWidget.selectColorBtn.clicked.connect(self.selectControlsByColor)
        self.advancedWidget.selectSimilarBtn.clicked.connect(partial(self.getColorSelected, selectMode=True))


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
        # Top Checkboxes  ------------------------------------
        toolTip = "Changes the display color of curves/controls.\n" \
                  "- nurbsCurves"
        self.curveCheckBx = elements.CheckBox("Curve",
                                              checked=self.properties.curveCheckBox.value,
                                              parent=parent,
                                              toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.curveCheckBx, "curveCheckBox")
        toolTip = "Changes the display color of meshes. \n" \
                  "- polygons\n" \
                  "- nurbsSurfaces\n"
        self.meshCheckBx = elements.CheckBox("Mesh",
                                             checked=self.properties.meshCheckBox.value,
                                             parent=parent,
                                             toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.meshCheckBx, "meshCheckBox")
        toolTip = "Changes the display color of\n" \
                  "- joints\n" \
                  "- locators\n" \
                  "- deformers\n" \
                  "- cameras"
        self.locatorCheckBx = elements.CheckBox("Other",
                                                checked=self.properties.otherCheckBox.value,
                                                parent=parent,
                                                toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.locatorCheckBx, "otherCheckBox")
        toolTip = "Changes the display color of the Outliner window text"
        self.outlinerCheckBx = elements.CheckBox("Outliner",
                                                 checked=self.properties.outlinerCheckBox.value,
                                                 parent=parent,
                                                 toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.outlinerCheckBx, "outlinerCheckBox")
        # Color Palettes  ------------------------------------
        # 3 palettes are hidden/shown depending on the combo, each palette grid is locked but colors can change
        toolTip = "Color palettes, click a color to apply to selected objects.\n" \
                  "Change palettes in the dropdown below.\n" \
                  "Change filter options (above)"
        self.colorPaletteHOffset = elements.ColorPaletteColorList(list(MIDDLE_PALETTE), parent=parent, rows=2,
                                                                  totalHeight=70, toolTip=toolTip)  # Hue 20 colors
        self.colorPaletteListCustom = elements.ColorPaletteColorList(list(PASTEL_PALETTE), parent=parent, rows=2,
                                                                     totalHeight=70,
                                                                     toolTip=toolTip)  # Custom 10 colors
        self.colorPaletteListMaya = elements.ColorPaletteColorList(list(MAYA_COLOR_SRGB), parent=parent, rows=2,
                                                                   totalHeight=70, toolTip=toolTip)  # Maya 32 colors
        toolTip = "Cycle through different color palette styles. \n" \
                  "(middle scroll wheel or up/down arrows)"
        if uiMode == UI_MODE_COMPACT:
            self.paletteCombo = elements.ComboBoxRegular("Palette",
                                                         items=FULL_PALETTE_LIST,
                                                         setIndex=self.properties.paletteCombo.value,
                                                         parent=parent,
                                                         toolTip=toolTip,
                                                         labelRatio=2,
                                                         boxRatio=5)
        else:  # advanced
            self.paletteCombo = elements.ComboBoxRegular("Palette",
                                                         items=FULL_PALETTE_LIST,
                                                         setIndex=self.properties.paletteCombo.value,
                                                         parent=parent,
                                                         toolTip=toolTip,
                                                         labelRatio=1,
                                                         boxRatio=1)

        self.toolsetWidget.linkProperty(self.paletteCombo, "paletteCombo")
        toolTip = "Reset selected to default colours. Filters based on the top checkboxes"
        self.resetColorBtn = elements.styledButton("",
                                                   "reload2",
                                                   toolTip=toolTip,
                                                   parent=parent,
                                                   minWidth=uic.BTN_W_ICN_MED,
                                                   maxWidth=uic.BTN_W_ICN_MED)
        if uiMode == UI_MODE_ADVANCED:
            self.resetColorLabel = elements.Label("Reset To Maya Default", parent, toolTip=toolTip)
        # Color right click menu  -------------------------------------
        self.colorBtnMenuModeList = [("paintLine", "Get Color From Obj"),
                                     ("cursorSelect", "Select Similar"),
                                     ("cursorSelect", "Select With Color")]
        self.colorBtnMenu = elements.ExtendedMenu(searchVisible=False)
        if uiMode == UI_MODE_COMPACT:
            # Color Picker Simple  ------------------------------------
            toolTip = "The color of selected object. Click to change."
            self.colorPickerBtn = cmdswidgets.MayaColorBtn(text="Color",
                                                           color=self.properties.color.value,
                                                           parent=parent,
                                                           toolTip=toolTip,
                                                           labelRatio=1,
                                                           btnRatio=2)
            self.toolsetWidget.linkProperty(self.colorPickerBtn, "color")
            self.colorPickerBtn.setMenu(self.colorBtnMenu, modeList=self.colorBtnMenuModeList)  # right click
            self.colorPickerBtn.setMenu(self.colorBtnMenu, mouseButton=QtCore.Qt.LeftButton)  # left click modes set
        elif uiMode == UI_MODE_ADVANCED:
            # Color Picker HSV Section  ------------------------------------
            toolTip = "The color of selected object. Click to change."
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
            self.colorHsvBtns.setMenu(self.colorBtnMenu, modeList=self.colorBtnMenuModeList)  # right click
            self.colorHsvBtns.setMenu(self.colorBtnMenu, mouseButton=QtCore.Qt.LeftButton)  # left click, modes set
            toolTip = "Apply the GUI color to selected controls."
            self.applyColorBtn = elements.styledButton("",
                                                       "paintLine",
                                                       toolTip=toolTip,
                                                       parent=parent,
                                                       minWidth=uic.BTN_W_ICN_MED,
                                                       maxWidth=uic.BTN_W_ICN_MED)
            # Get Color and Select Buttons ------------------------------------
            toolTip = "Retrieves the color of the selection"
            self.getColorLabel = elements.Label("Get Color", parent, toolTip=toolTip)
            self.getColorBtn = elements.styledButton("",
                                                     "arrowLeft",
                                                     toolTip=toolTip,
                                                     parent=parent,
                                                     minWidth=uic.BTN_W_ICN_MED,
                                                     maxWidth=uic.BTN_W_ICN_MED)
            toolTip = "Select objects by their color.  Filters based on the top checkboxes"
            self.selectColorLabel = elements.Label("Select From Color", parent, toolTip=toolTip)
            self.selectColorBtn = elements.styledButton("",
                                                        "cursorSelect",
                                                        toolTip=toolTip,
                                                        parent=parent,
                                                        minWidth=uic.BTN_W_ICN_MED,
                                                        maxWidth=uic.BTN_W_ICN_MED)
            toolTip = "Select all objects with a matching color to the first selected object."
            self.selectSimilarLabel = elements.Label("Select Similar", parent, toolTip=toolTip)
            self.selectSimilarBtn = elements.styledButton("",
                                                          "cursorSelect",
                                                          toolTip=toolTip,
                                                          parent=parent,
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
        # Main Layout ----------------------------------
        contentsLayout = elements.vBoxLayout(parent,
                                             margins=(uic.WINSIDEPAD,
                                                      uic.WINBOTPAD,
                                                      uic.WINSIDEPAD,
                                                      uic.WINBOTPAD),
                                             spacing=uic.SREG)
        parent.setLayout(contentsLayout)
        # checkbox top layout
        checkBoxLayout = elements.hBoxLayout(parent, margins=(0, 0, 0, uic.VSMLPAD), spacing=uic.SSML)
        checkBoxLayout.addWidget(self.curveCheckBx)
        checkBoxLayout.addWidget(self.meshCheckBx)
        checkBoxLayout.addWidget(self.locatorCheckBx)
        checkBoxLayout.addWidget(self.outlinerCheckBx)
        # palette combo layout
        colorPaletteComboLayout = elements.hBoxLayout(parent, margins=(0, 0, 0, uic.VSMLPAD), spacing=uic.SVLRG)
        colorPaletteComboLayout.addWidget(self.colorPickerBtn, 1)
        colorPaletteComboLayout.addWidget(self.paletteCombo, 2)
        colorPaletteComboLayout.addWidget(self.resetColorBtn, 8)
        # main layout
        contentsLayout.addLayout(checkBoxLayout)
        contentsLayout.addWidget(self.colorPaletteHOffset)
        contentsLayout.addWidget(self.colorPaletteListMaya)
        contentsLayout.addWidget(self.colorPaletteListCustom)
        contentsLayout.addLayout(colorPaletteComboLayout)


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
        contentsLayout = elements.vBoxLayout(parent,
                                             margins=(uic.WINSIDEPAD,
                                                      uic.WINBOTPAD,
                                                      uic.WINSIDEPAD,
                                                      uic.WINBOTPAD),
                                             spacing=uic.SREG)
        parent.setLayout(contentsLayout)
        # checkbox top layout
        checkBoxLayout = elements.hBoxLayout(parent, margins=(0, 0, 0, uic.VSMLPAD), spacing=uic.SVLRG)
        checkBoxLayout.addWidget(self.curveCheckBx)
        checkBoxLayout.addWidget(self.meshCheckBx)
        checkBoxLayout.addWidget(self.locatorCheckBx)
        checkBoxLayout.addWidget(self.outlinerCheckBx)
        # palette combo layout
        colorPaletteComboLayout = elements.hBoxLayout(parent, margins=(0, 0, 0, uic.VSMLPAD), spacing=uic.SVLRG)
        colorPaletteComboLayout.addWidget(self.paletteCombo)
        # Get Color Reset Color Btn Layout ------------------------------------
        getResetLayout = elements.hBoxLayout(parent, margins=(0, uic.SMLPAD, 0, 0), spacing=uic.SVLRG)
        getResetLayout.addWidget(self.getColorLabel, 12)
        getResetLayout.addWidget(self.getColorBtn, 1)
        getResetLayout.addWidget(self.resetColorLabel, 12)
        getResetLayout.addWidget(self.resetColorBtn, 1)
        # Get Color Select Color Btn Layout ------------------------------------
        selectLayout = elements.hBoxLayout(parent, margins=(0, uic.SMLPAD, 0, 0), spacing=uic.SVLRG)
        selectLayout.addWidget(self.selectColorLabel, 12)
        selectLayout.addWidget(self.selectColorBtn, 1)
        selectLayout.addWidget(self.selectSimilarLabel, 12)
        selectLayout.addWidget(self.selectSimilarBtn, 1)
        # color shape/design Layout ------------------------------------
        colorLayout = elements.hBoxLayout(parent, margins=(0, 0, 0, 0), spacing=uic.SVLRG)
        colorLayout.addWidget(self.colorHsvBtns, 24)
        colorLayout.addWidget(self.applyColorBtn, 1)
        # main layout
        contentsLayout.addLayout(checkBoxLayout)
        contentsLayout.addWidget(self.colorPaletteHOffset)
        contentsLayout.addWidget(self.colorPaletteListMaya)
        contentsLayout.addWidget(self.colorPaletteListCustom)
        contentsLayout.addLayout(colorLayout)
        contentsLayout.addLayout(colorPaletteComboLayout)
        contentsLayout.addLayout(getResetLayout)
        contentsLayout.addLayout(selectLayout)

