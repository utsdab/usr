from Qt import QtWidgets, QtCore

import maya.api.OpenMaya as om2

from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.maya.utils import env
from zoo.libs.maya.cmds.general import undodecorator

from zoo.libs.maya.cmds.modeling import mirror

# Dots Menu
from zoo.libs.pyqt.widgets.iconmenu import IconMenuButton
from zoo.preferences.core import preference
from zoo.libs import iconlib
from zoo.libs.pyqt import utils

THEME_PREFS = preference.interface("core_interface")
MAYA_VERSION = env.mayaVersion()  # whole numbers (int) 2020 etc


UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1
DIRECTION_LIST = ["+", "-"]
SYMMETRY_LIST = ["World X", "World Y", "World Z", "Object X", "Object Y", "Object Z"]
SPACE_LIST = ["World", "Object"]
MIRROR_LIST = ["+X to -X", "-X to +X", "+Y to -Y", "-Y to +Y", "+Z to -Z", "-Z to +Z"]

ATTR_MIRROR_AXIS = 0
ATTR_DIRECTION = 0
ATTR_MERGE_THRESHOLD = 0.001
ATTR_SMOOTH_ANGLE = 120.00
ATTR_DELETE_HISTORY = False
ATTR_FORCE_SMOOTH_ALL = False


class ZooMirrorGeo(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "zooMirrorGeo"
    info = "Modeling mirror geometry tool."
    uiData = {"label": "Zoo Mirror Geo",
              "icon": "mirrorGeo",
              "tooltip": "Modeling mirror geometry tool.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-zoo-mirror-geo/"
              }

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
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
        # not used
        parent = QtWidgets.QWidget(parent=self)
        self.advancedWidget = GuiAdvanced(parent=parent, properties=self.properties, toolsetWidget=self)
        return parent

    def postContentSetup(self):
        """Last of the initialize code"""
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
    # LOGIC
    # ------------------

    def resetSettings(self):
        """Resets all settings back to the default values

        :return:
        :rtype:
        """
        self.properties.symmetryCombo.value = ATTR_MIRROR_AXIS
        self.properties.directionCombo.value = ATTR_DIRECTION
        self.properties.mergeThresholdFloat.value = ATTR_MERGE_THRESHOLD
        self.properties.smoothAngleFloat.value = ATTR_SMOOTH_ANGLE
        self.properties.deleteHistoryCheckBox.value = ATTR_DELETE_HISTORY
        self.properties.smoothAngleCheckbox.value = ATTR_FORCE_SMOOTH_ALL
        self.updateFromProperties()

    # ------------------
    # LOGIC
    # ------------------

    @undodecorator.undoDecorator
    def symmetrize(self):
        """Uninstance all instances in the scene
        """
        mirror.symmetrize()

    @undodecorator.undoDecorator
    def flip(self):
        """Uninstance all instances in the scene
        """
        mirror.flip()

    @undodecorator.undoDecorator
    def toggleSymmetry(self):
        """Mirrors with maya's polygon mirror with added steps for centering the selected line
        """
        symmetryMode = SYMMETRY_LIST[self.properties.symmetryCombo.value]
        symState = mirror.symmetryToggle(message=False)
        mirror.changeSymmetryMode(symmetryMode=symmetryMode)
        if symState:
            symState = "Off"
        else:
            symState = "On"
        om2.MGlobal.displayInfo("Symmetry mode is `{}`, {}".format(symState, symmetryMode))

    @undodecorator.undoDecorator
    def symmetryComboChanged(self, symmetryIndex):
        """Changes the symmetry mode

        :param symmetryIndex: Index from the Symmetry combo box (not used)
        :type symmetryIndex: int
        """
        symmetryMode = SYMMETRY_LIST[self.properties.symmetryCombo.value]
        direction = DIRECTION_LIST[self.properties.directionCombo.value]
        mirror.changeSymmetryMode(symmetryMode=symmetryMode, message=False)
        om2.MGlobal.displayInfo("Symmetry plane set to `{}`, direction is `{}`".format(symmetryMode, direction))

    @undodecorator.undoDecorator
    def mirrorPolygon(self):
        """Mirrors with maya's polygon mirror with added steps for centering the selected line
        """
        symmetryMode = SYMMETRY_LIST[self.properties.symmetryCombo.value]
        direction = DIRECTION_LIST[self.properties.directionCombo.value]
        space = str.lower(symmetryMode.split(" ")[0])
        axis = str.lower(symmetryMode.split(" ")[-1])
        direction = 1 if direction == '+' else -1
        mirror.mirrorPolyEdgeToZero(smoothEdges=self.properties.smoothAngleCheckbox.value,
                                    deleteHistory=self.properties.deleteHistoryCheckBox.value,
                                    smoothAngle=self.properties.smoothAngleFloat.value,
                                    mergeThreshold=self.properties.mergeThresholdFloat.value,
                                    mirrorAxis=axis,
                                    direction=direction,
                                    space=space)

    @undodecorator.undoDecorator
    def instanceMirror(self):
        """Mirrors with grp instance and negative scale
        """
        symmetryMode = SYMMETRY_LIST[self.properties.symmetryCombo.value]
        direction = DIRECTION_LIST[self.properties.directionCombo.value]
        space = str.lower(symmetryMode.split(" ")[0])
        axis = str.lower(symmetryMode.split(" ")[-1])
        mirror.instanceMirror(mirrorAxis=axis, space=space, direction=direction)

    @undodecorator.undoDecorator
    def uninstanceAll(self):
        """Uninstance all instances in the scene
        """
        mirror.uninstanceMirrorInstacesAll()

    @undodecorator.undoDecorator
    def uninstanceSelected(self):
        """Uninstance selected instances
        """
        mirror.uninstanceMirrorInstanceSel()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for uiInstance in self.uiInstanceList:
            uiInstance.mirrorPolygonBtn.clicked.connect(self.mirrorPolygon)
            uiInstance.mirrorInstanceBtn.clicked.connect(self.instanceMirror)
            uiInstance.toggleSymmetryBtn.clicked.connect(self.toggleSymmetry)
            uiInstance.uninstanceAllBtn.clicked.connect(self.uninstanceAll)
            uiInstance.uninstanceSelBtn.clicked.connect(self.uninstanceSelected)
            uiInstance.symmetrizeBtn.clicked.connect(self.symmetrize)
            uiInstance.flipBtn.clicked.connect(self.flip)
            uiInstance.symmetryCombo.currentIndexChanged.connect(self.symmetryComboChanged)
            uiInstance.directionCombo.currentIndexChanged.connect(self.symmetryComboChanged)
            # Dots Menu
            uiInstance.dotsMenu.resetSettings.connect(self.resetSettings)


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
        # Symmetry Combo ---------------------------------------
        toolTip = "The mirror axis for all modes, also changes symmetry mode.\n" \
                  "  - World: Mirror/Symmetry across world coordinates. \n" \
                  "  - Object: Mirror/Symmetry across object space coordinates. \n" \
                  "Note:  Object mode affects instances in local coordinates"
        self.symmetryCombo = elements.ComboBoxRegular(label="Mirror",
                                                      items=SYMMETRY_LIST,
                                                      labelRatio=1,
                                                      boxRatio=2,
                                                      toolTip=toolTip)
        # Symmetry Combo ---------------------------------------
        toolTip = "The direction of the mirror, + mirrors from positive to negative. \n" \
                  "Note: Regarding instances the direction only affects naming."
        self.directionCombo = elements.ComboBoxRegular(label="Direction",
                                                       items=DIRECTION_LIST,
                                                       labelRatio=1,
                                                       boxRatio=2,
                                                       toolTip=toolTip)
        # Dots Menu -------------------------------------------
        self.dotsMenu = DotsMenu()
        # Zoo Mirror Polygon ---------------------------------------
        toolTip = "Toggles Maya's native symmetry mode. On/Off. \n" \
                  "Zoo Hotkey: Alt M "
        self.toggleSymmetryBtn = elements.styledButton("Toggle Sym Mode",
                                                       icon="symmetryMode",
                                                       toolTip=toolTip,
                                                       style=uic.BTN_DEFAULT)

        # Symmetrize Polygon ---------------------------------------
        toolTip = "Symmetrize a mesh while keeping mesh vertex orders. \n" \
                  "  1. Select the vertices to symmetrize. \n" \
                  "  2. Press the Symmetrize button.  \n" \
                  "  3. Select a center edge.  \n" \
                  "The mesh will be symmetrized while keeping UVs and point orders."
        self.symmetrizeBtn = elements.styledButton("Symmetrize Mesh",
                                                   icon="mirrorGeo",
                                                   toolTip=toolTip,
                                                   style=uic.BTN_DEFAULT)
        # Flip Polygon ---------------------------------------
        toolTip = "Flip mirrors a mesh while keeping mesh vertex orders. \n" \
                  "  1. Select the vertices to symmetrize. \n" \
                  "  2. Press the Flip button.  \n" \
                  "  3. Select a center edge.  \n" \
                  "The mesh will be mirror flipped and will keep UVs and point orders."
        self.flipBtn = elements.styledButton("Flip Mesh",
                                             icon="mirrorGeo",
                                             toolTip=toolTip,
                                             style=uic.BTN_DEFAULT)
        if MAYA_VERSION < 2019:  # only in 2019 and above
            self.symmetrizeBtn.hide()
            self.flipBtn.hide()
        # Zoo Mirror Polygon ---------------------------------------
        toolTip = "Uses Maya's `Mesh > Mirror` with extra functionality. Rebuilds the opposite side.\n" \
                  "- In object mode acts as `Mesh > Mirror` \n" \
                  "- In component mode if verts or edges are selected the selection \n" \
                  "will be centered and then the whole object mirrored\n" \
                  "  1. Select center edges or vertices. \n" \
                  "  2. Run \n" \
                  "Zoo Hotkey: Shift M"
        self.mirrorPolygonBtn = elements.styledButton("Zoo Mirror Polygon",
                                                      icon="mirrorGeo",
                                                      toolTip=toolTip,
                                                      style=uic.BTN_DEFAULT)
        # Instance Mirror Button ---------------------------------------
        toolTip = "Instance mirrors an object. \n" \
                  "Will group selected objects, then duplicates an instanced group with negative scale. \n" \
                  "  1. Select objects and run  \n" \
                  "Use the uninstance buttons to remove instancing. \n" \
                  "Zoo Hotkey: Alt Shift M"
        self.mirrorInstanceBtn = elements.styledButton("Mirror Obj Instance",
                                                       icon="symmetryTri",
                                                       toolTip=toolTip,
                                                       style=uic.BTN_DEFAULT)
        # Remove Instance All Button ---------------------------------------
        toolTip = "Will uninstance all Mirror Instances in the scene. Removes instances while leaving geometry."
        if uiMode == UI_MODE_ADVANCED:
            self.uninstanceAllBtn = elements.styledButton("Uninstance All",
                                                          icon="crossXFat",
                                                          toolTip=toolTip,
                                                          style=uic.BTN_DEFAULT)
        else:
            self.uninstanceAllBtn = elements.styledButton("All",
                                                          icon="crossXFat",
                                                          toolTip=toolTip,
                                                          style=uic.BTN_DEFAULT)
        # Remove Instance Selected Button ---------------------------------------
        toolTip = "Uninstances selected Mirror Instance setup/s."
        if uiMode == UI_MODE_ADVANCED:
            self.uninstanceSelBtn = elements.styledButton("Uninstance Selected",
                                                          icon="crossXFat",
                                                          toolTip=toolTip,
                                                          style=uic.BTN_DEFAULT)
        else:
            self.uninstanceSelBtn = elements.styledButton("Sel",
                                                          icon="crossXFat",
                                                          toolTip=toolTip,
                                                          style=uic.BTN_DEFAULT)
        if uiMode == UI_MODE_ADVANCED:
            # Symmetry Polygon Title Divider -------------------------------------------------------
            self.symmetryTitle = elements.LabelDivider(text="Symmetry Mode (Non Destructive)")
            # Mirror Polygon Title Divider -------------------------------------------------------
            self.mirrorPolygonTitle = elements.LabelDivider(text="Mirror Polygon (Delete/Rebuild)")
            # Merge threshold ---------------------------------------
            toolTip = "Vertices within this threshold will be merged. \n" \
                      "Note: This setting only affects shells, the cut mesh is not affected"
            self.mergeThresholdFloat = elements.FloatEdit(label="Merge Threshold",
                                                           editText="0.001",
                                                           toolTip=toolTip,
                                                           labelRatio=20,
                                                           editRatio=15)
            # Smooth Angle ---------------------------------------
            toolTip = "Affects the soften/harden edge crease value across the seam. \n" \
                      "If `Force Smooth All` is checked then the whole object will be smoothed. "
            self.smoothAngleFloat = elements.FloatEdit(label="Smooth Angle",
                                                        editText="120.0",
                                                        toolTip=toolTip,
                                                        labelRatio=20,
                                                        editRatio=15)
            self.smoothAngleCheckbox = elements.CheckBox(label="Force Smooth All",
                                                         checked=False,
                                                         toolTip=toolTip)
            # Delete History Check Box ---------------------------------------
            toolTip = "Delete history after the mirror is performed?"
            self.deleteHistoryCheckBox = elements.CheckBox(label="Delete History",
                                                           checked=False,
                                                           toolTip=toolTip)
            # Mirror Polygon Title Divider -----------------------------------------------------------
            self.instanceMirrorTitle = elements.LabelDivider(text="Instance Mirror (Separate Objects)")


class DotsMenu(IconMenuButton):
    menuIcon = "menudots"
    resetSettings = QtCore.Signal()

    def __init__(self, parent=None, networkEnabled=False):
        """Builds the dots menu with > Reset Settings
        """
        super(DotsMenu, self).__init__(parent=parent)
        self.networkEnabled = networkEnabled
        iconColor = THEME_PREFS.ICON_PRIMARY_COLOR
        self.setIconByName(self.menuIcon, size=16, colors=iconColor)
        self.setMenuAlign(QtCore.Qt.AlignRight)
        self.setToolTip("File menu. Zoo Mirror Poly")
        self.disableActionList = list()
        # Build the static menu
        # Reset To Defaults --------------------------------------
        reloadIcon = iconlib.iconColorized("reload2", utils.dpiScale(16))
        self.addAction("Reset Settings", connect=lambda: self.resetSettings.emit(), icon=reloadIcon)


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
        mainLayout = elements.vBoxLayout(parent,
                                         margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SLRG)
        # Direction Bots Menu Layout ---------------------------------------
        dirDotsLayout = elements.hBoxLayout(spacing=uic.SVLRG)
        dirDotsLayout.addWidget(self.directionCombo, 6)
        dirDotsLayout.addWidget(self.dotsMenu, 1)
        # Options Layout ---------------------------------------
        optionsLayout = elements.hBoxLayout(spacing=uic.SVLRG)
        optionsLayout.addWidget(self.symmetryCombo, 1)
        optionsLayout.addLayout(dirDotsLayout, 1)
        # Sym Button Layout ---------------------------------------
        symFlipLayout = elements.hBoxLayout()
        symFlipLayout.addWidget(self.symmetrizeBtn, 1)
        symFlipLayout.addWidget(self.flipBtn, 1)
        # Poly Mirror Sym Button Layout ---------------------------------------
        polMSymLayout = elements.hBoxLayout()
        polMSymLayout.addWidget(self.mirrorPolygonBtn, 1)
        polMSymLayout.addWidget(self.toggleSymmetryBtn, 1)
        # Remove Instance Layout ---------------------------------------
        uninstanceLayout = elements.hBoxLayout()
        uninstanceLayout.addWidget(self.uninstanceAllBtn, 1)
        uninstanceLayout.addWidget(self.uninstanceSelBtn, 1)
        # Instance Layout ---------------------------------------
        instanceLayout = elements.hBoxLayout()
        instanceLayout.addWidget(self.mirrorInstanceBtn, 1)
        instanceLayout.addLayout(uninstanceLayout, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(optionsLayout)
        mainLayout.addLayout(symFlipLayout)
        mainLayout.addLayout(polMSymLayout)
        mainLayout.addLayout(instanceLayout)


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
        mainLayout = elements.vBoxLayout(parent,
                                         margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.SVLRG),
                                         spacing=uic.SLRG)
        # Direction Bots Menu Layout ---------------------------------------
        dirDotsLayout = elements.hBoxLayout(spacing=uic.SVLRG)
        dirDotsLayout.addWidget(self.directionCombo, 6)
        dirDotsLayout.addWidget(self.dotsMenu, 1)
        # Options Layout ---------------------------------------
        optionsLayout = elements.hBoxLayout(spacing=uic.SVLRG)
        optionsLayout.addWidget(self.symmetryCombo, 1)
        optionsLayout.addLayout(dirDotsLayout, 1)
        # Sym Flip Button Layout ---------------------------------------
        symFlipLayout = elements.hBoxLayout()
        symFlipLayout.addWidget(self.symmetrizeBtn, 1)
        symFlipLayout.addWidget(self.flipBtn, 1)
        # Symmetry Mode Layout ---------------------------------------
        symmetryLayout = elements.hBoxLayout()
        symmetryLayout.addWidget(self.toggleSymmetryBtn)
        # Merge/Direction Layout ---------------------------------------
        mergeDirectionLayout = elements.hBoxLayout(margins=(uic.SREG, 0, uic.SREG, 0),
                                                   spacing=uic.SVLRG)
        mergeDirectionLayout.addWidget(self.mergeThresholdFloat, 10)
        mergeDirectionLayout.addWidget(self.deleteHistoryCheckBox, 6)
        # Smooth/History Layout ---------------------------------------
        smoothSpaceLayout = elements.hBoxLayout(margins=(uic.SREG, 0, uic.SREG, 0),
                                                spacing=uic.SVLRG)
        smoothSpaceLayout.addWidget(self.smoothAngleFloat, 10)
        smoothSpaceLayout.addWidget(self.smoothAngleCheckbox, 6)
        # Mirror Button Layout ---------------------------------------
        mirrorPolyLayout = elements.hBoxLayout(margins=(uic.SREG, 0, uic.SREG, 0))
        mirrorPolyLayout.addWidget(self.mirrorPolygonBtn)
        # Mirror Instance Layout ---------------------------------------
        instanceMirrorLayout = elements.hBoxLayout(margins=(uic.SREG, 0, uic.SREG, 0))
        instanceMirrorLayout.addWidget(self.mirrorInstanceBtn, 1)
        # Remove Instance Layout ---------------------------------------
        removeInstanceLayout = elements.hBoxLayout(margins=(uic.SREG, 0, uic.SREG, 0))
        removeInstanceLayout.addWidget(self.uninstanceAllBtn, 1)
        removeInstanceLayout.addWidget(self.uninstanceSelBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(optionsLayout)
        mainLayout.addWidget(self.symmetryTitle)
        mainLayout.addLayout(symFlipLayout)
        mainLayout.addLayout(symmetryLayout)
        mainLayout.addWidget(self.mirrorPolygonTitle)
        mainLayout.addLayout(mergeDirectionLayout)
        mainLayout.addLayout(smoothSpaceLayout)
        mainLayout.addLayout(mirrorPolyLayout)
        mainLayout.addWidget(self.instanceMirrorTitle)
        mainLayout.addLayout(instanceMirrorLayout)
        mainLayout.addLayout(removeInstanceLayout)
