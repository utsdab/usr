from functools import partial

from Qt import QtWidgets, QtCore

from maya import cmds
import maya.api.OpenMaya as om2

from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.apps.toolsetsui import toolsetcallbacks

from zoo.libs.maya.cmds.general import undodecorator

from zoo.libs.maya.cmds.ncloth import nclothskinned
from zoo.libs.maya.cmds.ncloth import nclothconstants
from zoo.libs.maya.cmds.ncloth.nclothconstants import TSHIRT_PRESET_DICT, NCA_BEND_ANGLE_DROPOFF, \
    NCA_COMPRESSION_RESISTANCE, NCA_STRETCH_RESISTANCE, NCA_SHEAR_RESISTANCE, NCA_BEND_RESISTANCE, NCA_THICKNESS, \
    NCA_BLEND_ATTR, NCA_NUCLEUS_SUBSTEPS, NCA_NUCLEUS_STARTFRAME, NCA_NUCLEUS_MAX_COLLISIONS, NCA_INPUT_ATTRACT, \
    NUCLEUS_DEFAULT_PRESET, NCLOTH_SKINNED_PRESET_DICT, NCLOTH_PRESET_NAME_LIST, BLENDSHAPE_CLOTH_NODE, NCLOTH_NODE, \
    NUCLEUS_NODE, ORIGINAL_MESH_TFRM, POLYSMOOTH_MESH_TFRM, CLOTH_MESH_TFRM, BLENDER_MESH_TFRM

# Dots Menu
from zoo.libs.pyqt.widgets.iconmenu import IconMenuButton
from zoo.preferences.core import preference
from zoo.libs import iconlib
from zoo.libs.pyqt import utils

THEME_PREFS = preference.interface("core_interface")

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1
CLOTH_PRESET = TSHIRT_PRESET_DICT
NO_NETWORK_TXT = "No Network Detected"


class NClothWrinkleCreator(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "nclothwrinklecreator"
    info = "Instantly builds nCloth setups with wrinkle only simulation."
    uiData = {"label": "NCloth Wrinkle Creator",
              "icon": "tshirt",
              "tooltip": "Instantly builds nCloth setups with wrinkle only simulation.",
              "defaultActionDoubleClick": False}

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        self.toolsetWidget = self  # needed for callback decorators
        self.attrUpdated = False  # for undo sliders
        self.undoStateOpen = False  # for undo sliders
        self.setupEnabled = False  # tracks whether the current network is enabled or not

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
        self.uiModeList()
        self.uiConnections()
        self.updateUIFromSelection(cmds.ls(selection=True))  # Update UI from selected objects
        self.disableEnable(self.properties.nClothNetworkTxt.value)  # first time enable disable, could be no selection
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

    # ------------------
    # SELECTION CALLBACKS
    # ------------------

    def selectionChanged(self, selection):
        """Run when the callback selection changes, updates the GUI if an object is selected

        Callbacks are handled automatically by toolsetcallbacks.py which this class inherits"""
        if not selection:  # then still may be a selection TODO add this to internal callbacks maybe?
            selection = cmds.ls(selection=True)  # catches component and node selections
            if not selection:  # then nothing is selected
                return
        self.updateUIFromSelection(selection)  # will update the GUI

    def updateUIFromNetwork(self, networkNodeList, update=True, allAttrs=True):
        """Usually called from selectionChanged, will update the UI finds network nodes and updates accordingly
        Also used after creating and deleting a new setup

        :param networkNodeList: A list of network nodes
        :type networkNodeList: list(str)
        :param update: Update the UI with self.updateProperties?  Usually True
        :type update: bool
        """
        if not networkNodeList:
            self.properties.nClothNetworkTxt.value = NO_NETWORK_TXT
            self.resetAttrsDefaults(allAttrs=allAttrs)
            if update:
                self.updateFromProperties()
            self.disableEnable(NO_NETWORK_TXT)
            return
        self.properties.nClothNetworkTxt.value = networkNodeList[0]
        self.getAllAttrs()  # Will update the UI with latest attribute settings
        if update:
            self.updateFromProperties()

    def updateUIFromSelection(self, selection, update=True):
        """Update the GUI from an object list, usually the selection

        If Network found will display it in the UI
        Checks for broken network and will warn user with a popup window
        If Network not found will set default values to all widgets and network names "No Network Detected".

        :param selection: list of Maya objects or node names
        :type selection: list(str)
        :param update: Update the UI with self.updateProperties?  Usually True
        :type update: bool
        """
        # Get data from scene and set GUI self.properties etc here
        if not selection:
            return
        valid, networkNode = nclothskinned.validateNClothNetworkNodes(selection)  # Check valid
        if not valid and networkNode:  # Is broken
            self.reportBrokenNetwork(networkNode)  # Warn user with window
            return
        skinnedDictList, networkNodeList = nclothskinned.getSkinnedNClothDictSelected()
        self.updateUIFromNetwork(networkNodeList, update=update, allAttrs=True)  # update UI

    # ------------------------------------
    # SLIDER UNDO CHUNKS
    # ------------------------------------

    def openUndoChunk(self):
        """Opens the Maya undo chunk, on sliderPressed"""
        undodecorator.openUndoChunk()
        self.undoStateOpen = True

    def closeUndoChunk(self):
        """Opens the Maya undo chunk, on sliderReleased"""
        undodecorator.closeUndoChunk()
        if self.attrUpdated:
            om2.MGlobal.displayInfo("Skinned nCloth attributes updated")
            self.attrUpdated = False
        self.undoStateOpen = False

    # ------------------------------------
    # DISABLE ENABLE UI ELEMENTS
    # ------------------------------------

    def dotsMenuSetStates(self, checked, networkNode):
        """Sets the enabled and disables dots menu states, also sets the "Network Enabled" checkbox

        The checkbox is set via the kwarg
        The disabled (greyed out) or enabled settings are calculated by the network node and if it exists or not

        :param checked: Is the "Network Enabled" checked on or off
        :type checked: bool
        :param networkNode: Name of a skinned NCloth network node
        :type networkNode: str
        """
        for uiInstance in self.uiInstanceList:
            uiInstance.dotsMenu.enabledAction.setChecked(checked)
        if networkNode == NO_NETWORK_TXT:
            enabled = False
        else:
            enabled = True
        for uiInstance in self.uiInstanceList:
            uiInstance.dotsMenu.enabledAction.setEnabled(enabled)
            for action in uiInstance.dotsMenu.disableActionList:
                action.setEnabled(enabled)

    def setNClothEnabledState(self, networkNode):
        """Sets the self.setEnabledState and disable/enables dots menu, also sets the "Network Enabled" checkbox

        The checkbox relates to the entire network, and not the nucleus state, so getting it's value can be tricky.
        The checkbox is set via checking the node network, depends on a few things as nucleus is disabled while \n
        caching even though the network state is still valid and on (enabled).
        If nucleus is disabled but the blender mesh is visible and there is a cache, then the network is considered \n
        enabled.  Otherwise it'll go with the nucleus state.

        The disabled (greyed out) or enabled settings are calculated by the network node and if it exists or not

        :param networkNode: Name of a skinned NCloth network node
        :type networkNode: str
        """
        if networkNode == NO_NETWORK_TXT:
            self.setEnabledState = False
            self.dotsMenuSetStates(False, networkNode)
            return
        self.setEnabledState = nclothskinned.checkNetworkEnabled(networkNode)
        self.dotsMenuSetStates(self.setEnabledState, networkNode)

    def disableEnable(self, networkNode):
        """Disables and enables the use of various UI widgets depending on whether a legit network node is active

        :param networkNode: Name of a skinned NCloth network node
        :type networkNode: str
        """
        if networkNode == NO_NETWORK_TXT:
            network = False
        else:
            network = True
        for uiInstance in self.uiInstanceList:
            uiInstance.createCacheBtn.setEnabled(network)
            uiInstance.deleteCacheBtn.setEnabled(network)
            uiInstance.selectBlendshapeBtn.setEnabled(network)
            uiInstance.paintBlendshapeBtn.setEnabled(network)
            uiInstance.deleteNClothBtn.setEnabled(network)
            uiInstance.bakeNClothBtn.setEnabled(network)
            uiInstance.skinnedNClothBtn.setEnabled(not network)
            uiInstance.divisionsInt.setEnabled(not network)

        self.setNClothEnabledState(networkNode)  # Figures the dots menu and the enabled state

    # ------------------------------------
    # DISABLE ENABLE THE NCLOTH NETWORK
    # ------------------------------------

    def enableSetup(self, action):
        """Will enable or disable the entire ncloth network, see nclothskinned.enableDisableNetwork() for documentation

        Called from the checkbox action on the dots menu

        :param action: The menu action as an object, will query and set the checked state of the checkbox action
        :type action: object
        """
        networkNode = self.properties.nClothNetworkTxt.value
        self.setupEnabled = action.isChecked()
        if networkNode == NO_NETWORK_TXT:
            om2.MGlobal.displayWarning("No Skinned NCloth setup selected")
            return
        isEnabled, success = nclothskinned.enableDisableNetwork(networkNode, enable=self.setupEnabled)
        action.setChecked(isEnabled)
        self.setupEnabled = isEnabled
        # report messages
        if success and self.setupEnabled:
            om2.MGlobal.displayInfo("Skinned NCloth setup enabled `{}`".format(networkNode))
        if success and not self.setupEnabled:
            om2.MGlobal.displayInfo("Skinned NCloth setup disabled `{}`".format(networkNode))

    def enableDisableAll(self, enableState=True):
        """Enables or disables all cloth setups in the scene

        :param enableState: True enables all, False disables all
        :type enableState:
        """
        nclothskinned.enableDisableNetworkAll(enable=enableState)
        networkNode = self.properties.nClothNetworkTxt.value
        networkNodeList = [networkNode]
        if networkNode == NO_NETWORK_TXT:
            networkNodeList = list()
        self.updateUIFromNetwork(networkNodeList, update=True, allAttrs=True)

    # ------------------
    # CHANGE PRESET UPDATE UI
    # ------------------

    def changePreset(self):
        """Sets an ncloth network and GUI settings to the new preset
        """
        presetName = NCLOTH_PRESET_NAME_LIST[self.properties.nClothPresetsCombo.value]
        presetDict = NCLOTH_SKINNED_PRESET_DICT[presetName]
        self.getNClothPreset(presetDict=presetDict)
        self.updateFromProperties()
        networkNode = self.properties.nClothNetworkTxt.value
        if networkNode == NO_NETWORK_TXT:
            return
        self.disableEnable(networkNode)
        self.setAllNCloth()

    def paintBlendshape(self):
        """Opens the tool for painting blendshapes
        """
        networkNode = self.properties.nClothNetworkTxt.value
        if networkNode == NO_NETWORK_TXT:
            om2.MGlobal.displayWarning("Select a node from a Skinned NCloth setup to paint.")
            return
        nclothskinned.paintNClothBlendshape(networkNode)

    def selectBlendshape(self):
        """Selects the blendshape node
        """
        networkNode = self.properties.nClothNetworkTxt.value
        if networkNode == NO_NETWORK_TXT:
            om2.MGlobal.displayWarning("Select a node from a Skinned NCloth setup to paint.")
            return
        nclothskinned.selectNode(networkNode, nclothconstants.BLENDSHAPE_CLOTH_NODE)

    # ------------------
    # LOGIC CREATE
    # ------------------

    @undodecorator.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def createSkinnedNCloth(self):
        """Creates the NCloth Setup"""
        nucleusDict = dict()
        CLOTH_PRESET[NCA_THICKNESS] = self.properties.thicknessFSlider.value
        CLOTH_PRESET[NCA_STRETCH_RESISTANCE] = self.properties.stretchResistFSlider.value
        CLOTH_PRESET[NCA_COMPRESSION_RESISTANCE] = self.properties.compressResistFSlider.value
        CLOTH_PRESET[NCA_SHEAR_RESISTANCE] = self.properties.shearResistFSlider.value
        CLOTH_PRESET[NCA_BEND_RESISTANCE] = self.properties.bendResistFSlider.value
        CLOTH_PRESET[NCA_BEND_ANGLE_DROPOFF] = self.properties.bendDropoffFSlider.value
        CLOTH_PRESET[NCA_INPUT_ATTRACT] = self.properties.attractFSlider.value
        nucleusDict[NCA_NUCLEUS_STARTFRAME] = self.properties.startFrameInt.value
        nucleusDict[NCA_NUCLEUS_MAX_COLLISIONS] = self.properties.maxCollisionsFSlider.value
        nucleusDict[NCA_NUCLEUS_SUBSTEPS] = self.properties.subStepsFSlider.value
        # Build the setup
        networkNodeList = nclothskinned.nClothSkinnedSelected(divisionsPolySmooth=self.properties.divisionsInt.value,
                                                              startFrame=self.properties.startFrameInt.value,
                                                              blendMultiply=self.properties.blendshapeMultiplyFSlider.value,
                                                              deleteDeadShapes=True,
                                                              presetDict=CLOTH_PRESET,
                                                              nucleusAttrs=nucleusDict,
                                                              presetIndex=self.properties.nClothPresetsCombo.value)
        self.updateUIFromNetwork(networkNodeList, allAttrs=True)

    # ------------------
    # LOGIC CACHES
    # ------------------

    @undodecorator.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def createCache(self):
        """Creates nCloth Geometry Cache on the selected object"""
        networkNode = self.properties.nClothNetworkTxt.value
        if networkNode == NO_NETWORK_TXT:
            om2.MGlobal.displayWarning("No objects of a skinned nCloth setup are selected")
            return
        if not nclothskinned.getNucleusEnabledState(networkNode):
            self.showMesh(BLENDER_MESH_TFRM)  # Be sure to show the Blender mesh as could be disabled
        nclothskinned.createCache(networkNode)
        self.setNClothEnabledState(networkNode)

    @undodecorator.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def deleteCache(self):
        """Deletes nCloth Geometry Cache on the selected object"""
        networkNode = self.properties.nClothNetworkTxt.value
        if networkNode == NO_NETWORK_TXT:
            om2.MGlobal.displayWarning("No objects of a skinned nCloth setup are selected")
            return
        nclothskinned.deleteCache(networkNode)

    # ------------------
    # LOGIC DELETE NCLOTH
    # ------------------

    @undodecorator.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def deleteSkinnedNClothSetup(self):
        """Deletes the entire Skinned NCloth setup from the active network
        """
        networkNode = self.properties.nClothNetworkTxt.value
        if networkNode == NO_NETWORK_TXT:
            om2.MGlobal.displayWarning("No objects of a skinned nCloth setup are selected")
            return
        nclothskinned.deleteSkinnedNClothSetupNetwork(networkNode)
        self.properties.nClothNetworkTxt.value = NO_NETWORK_TXT
        self.updateUIFromNetwork([NO_NETWORK_TXT], allAttrs=True)

    @undodecorator.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def bakeSkinnedNClothSetup(self):
        """Deletes the entire Skinned NCloth setup from the active network
        """
        networkNode = self.properties.nClothNetworkTxt.value
        if networkNode == NO_NETWORK_TXT:
            om2.MGlobal.displayWarning("No objects of a skinned nCloth setup are selected")
            return
        nclothskinned.deleteSkinnedNClothSetupNetwork(networkNode, bakeCurrent=True)
        self.properties.nClothNetworkTxt.value = NO_NETWORK_TXT
        self.updateUIFromNetwork([NO_NETWORK_TXT], allAttrs=True)

    # ------------------
    # LOGIC GET ATTRS
    # ------------------

    def reportBrokenNetwork(self, networkNode):
        """Shows a popup menu for a broken network is broken in some way and should be rebuilt, checks failed

        :param networkNode: Name of a skinned NCloth network node
        :type networkNode: str
        """
        om2.MGlobal.displayWarning("This Skinned NCloth network is broken `{}`".format(networkNode))
        windowMessage = "This Skinned NCloth network is broken: \n\n" \
                        "  `{}` \n\n" \
                        "Delete? Recommended.  This will clean the NCloth network.".format(networkNode)
        if elements.MessageBox_ok(windowName="Broken NCloth", message=windowMessage):
            nclothskinned.deleteSkinnedNClothSetupNetwork(networkNode)
            self.properties.nClothNetworkTxt.value = NO_NETWORK_TXT
            self.getAllAttrs()  # Will update the UI with "No Network Detected"

    def getNClothPreset(self, presetDict=TSHIRT_PRESET_DICT, allAttrs=False):
        """Updates the cloth preset attributes, if from a preset don't update all, if selection update all

        :param presetDict: Dictionary of presets to set attrs
        :type presetDict: dict
        :param allAttrs: Update thickness and attract, usually on selection updates, ignore for preset changes
        :type allAttrs: bool
        """
        if allAttrs:  # if updating from selection not presets
            self.properties.thicknessFSlider.value = presetDict[NCA_THICKNESS]  # Ignore thickness
            self.properties.attractFSlider.value = presetDict[NCA_INPUT_ATTRACT]  # Ignore attract
        self.properties.stretchResistFSlider.value = presetDict[NCA_STRETCH_RESISTANCE]
        self.properties.compressResistFSlider.value = presetDict[NCA_COMPRESSION_RESISTANCE]
        self.properties.shearResistFSlider.value = presetDict[NCA_SHEAR_RESISTANCE]
        self.properties.bendResistFSlider.value = presetDict[NCA_BEND_RESISTANCE]
        self.properties.bendDropoffFSlider.value = presetDict[NCA_BEND_ANGLE_DROPOFF]

    def resetAttrsDefaults(self, allAttrs=False):
        """Resets all UI elements to the default values
        """
        self.properties.divisionsInt.value = 2
        # nucleus
        self.properties.startFrameInt.value = int(NUCLEUS_DEFAULT_PRESET[NCA_NUCLEUS_STARTFRAME])
        self.properties.subStepsFSlider.value = NUCLEUS_DEFAULT_PRESET[NCA_NUCLEUS_SUBSTEPS]
        self.properties.maxCollisionsFSlider.value = NUCLEUS_DEFAULT_PRESET[NCA_NUCLEUS_MAX_COLLISIONS]
        # blendshape
        self.properties.blendshapeMultiplyFSlider.value = 1.0
        # ncloth settings
        self.getNClothPreset(presetDict=TSHIRT_PRESET_DICT, allAttrs=allAttrs)
        # Preset
        self.properties.nClothPresetsCombo.value = NCLOTH_PRESET_NAME_LIST.index("TShirt")

    def getAllAttrs(self):
        """Gets all attributes from the active network in the scene node and updates the GUI.
        If no network found updates the GUI only with default settings.
        """
        networkNode = self.properties.nClothNetworkTxt.value
        self.disableEnable(networkNode)
        if networkNode == NO_NETWORK_TXT:
            self.resetAttrsDefaults()
            self.updateFromProperties()
            return
        nClothAttrDict, nucleusAttrDict, blendshapeAttrDict, \
        subDDivisions, presetIndex = nclothskinned.getAttrDictNetworkAll(networkNode)
        if not nClothAttrDict:  # then the network is broken
            self.reportBrokenNetwork(networkNode)
            return
        # Get NCloth
        self.properties.thicknessFSlider.value = round(nClothAttrDict[NCA_THICKNESS], 3)
        self.properties.attractFSlider.value = round(nClothAttrDict[NCA_INPUT_ATTRACT], 3)
        self.properties.stretchResistFSlider.value = round(nClothAttrDict[NCA_STRETCH_RESISTANCE], 3)
        self.properties.compressResistFSlider.value = round(nClothAttrDict[NCA_COMPRESSION_RESISTANCE], 3)
        self.properties.shearResistFSlider.value = round(nClothAttrDict[NCA_SHEAR_RESISTANCE], 3)
        self.properties.bendResistFSlider.value = round(nClothAttrDict[NCA_BEND_RESISTANCE], 3)
        self.properties.bendDropoffFSlider.value = round(nClothAttrDict[NCA_BEND_ANGLE_DROPOFF], 3)
        # Get Nucleus
        self.properties.subStepsFSlider.value = round(nucleusAttrDict[NCA_NUCLEUS_SUBSTEPS], 3)
        self.properties.maxCollisionsFSlider.value = round(nucleusAttrDict[NCA_NUCLEUS_MAX_COLLISIONS], 3)
        self.properties.startFrameInt.value = int(nucleusAttrDict[NCA_NUCLEUS_STARTFRAME])
        # Get Blendshape
        self.properties.blendshapeMultiplyFSlider.value = round(blendshapeAttrDict[NCA_BLEND_ATTR], 3)
        # Get Network Node
        self.properties.divisionsInt.value = int(subDDivisions)
        self.properties.nClothPresetsCombo.value = int(presetIndex)
        # Update UI
        self.updateFromProperties()

    # ------------------
    # LOGIC SET ATTRS
    # ------------------

    def setAttrBlendshape(self, value=0, attr=""):
        """Sets the blendshape slider

        :param value: Null value from the slider, not used
        :type value: float
        :param attr: The attribute name to change, currently only using the global NCA_BLEND_ATTR
        :type attr: str
        """
        # Slider Undo -------------------
        closeUndo = False
        if not self.undoStateOpen:  # open the undo state if it is not already open (slider hasn't been pressed)
            undodecorator.openUndoChunk()
            closeUndo = True
        # Method start -------------------
        networkNode = self.properties.nClothNetworkTxt.value
        if networkNode == NO_NETWORK_TXT:
            return
        if attr == NCA_BLEND_ATTR:
            value = self.properties.blendshapeMultiplyFSlider.value
        else:
            return
        nclothskinned.blendshapeSetAttrNetwork(networkNode, attr, value)
        # Slider undo -------------------
        self.attrUpdated = True  # this relates to the change attr message in the slider undo methods
        if closeUndo:  # close the undo chunk (if slider hadn't been pressed)
            undodecorator.closeUndoChunk()

    def setAttrNucleus(self, value=0, attr=""):
        """Sets the attributes related to the nucleus node

        :param value: Null value from the slider, not used
        :type value: float
        :param attr: The attribute name to change, using the globals NCA_NUCLEUS_* (ncloth attributes)
        :type attr: str
        """
        # Slider Undo -------------------
        closeUndo = False
        if not self.undoStateOpen:  # open the undo state if it is not already open (slider hasn't been pressed)
            undodecorator.openUndoChunk()
            closeUndo = True
        # Start method -------------------
        networkNode = self.properties.nClothNetworkTxt.value
        if networkNode == NO_NETWORK_TXT:
            return
        if attr == NCA_NUCLEUS_SUBSTEPS:
            value = int(self.properties.subStepsFSlider.value)
        elif attr == NCA_NUCLEUS_MAX_COLLISIONS:
            value = self.properties.maxCollisionsFSlider.value
        elif attr == NCA_NUCLEUS_STARTFRAME:
            value = self.properties.startFrameInt.value
        else:
            return
        nclothskinned.nucleusSetAttrNetwork(networkNode, attr, value)
        # Slider undo -------------------
        self.attrUpdated = True  # this relates to the change attr message in the slider undo methods
        if closeUndo:  # close the undo chunk (if slider hadn't been pressed)
            undodecorator.closeUndoChunk()

    def setAttrNCloth(self, attr):
        """Sets the attributes related to the NCloth node, sets one attribute at a time

        :param attr: The attribute name to change, using the globals NCA_* (ncloth attributes)
        :type attr: str
        """
        # Slider Undo -------------------
        closeUndo = False
        if not self.undoStateOpen:  # open the undo state if it is not already open (slider hasn't been pressed)
            undodecorator.openUndoChunk()
            closeUndo = True
        # Start method -------------------
        networkNode = self.properties.nClothNetworkTxt.value
        if networkNode == NO_NETWORK_TXT:
            return
        if attr == NCA_THICKNESS:
            value = self.properties.thicknessFSlider.value
        elif attr == NCA_INPUT_ATTRACT:
            value = self.properties.attractFSlider.value
        elif attr == NCA_STRETCH_RESISTANCE:
            value = self.properties.stretchResistFSlider.value
        elif attr == NCA_COMPRESSION_RESISTANCE:
            value = self.properties.compressResistFSlider.value
        elif attr == NCA_SHEAR_RESISTANCE:
            value = self.properties.shearResistFSlider.value
        elif attr == NCA_BEND_RESISTANCE:
            value = self.properties.bendResistFSlider.value
        elif attr == NCA_BEND_ANGLE_DROPOFF:
            value = self.properties.bendDropoffFSlider.value
        else:
            return
        # Set
        nclothskinned.nClothSetAttrNetwork(networkNode,
                                           attr,
                                           value)
        # Slider undo -------------------
        self.attrUpdated = True  # this relates to the change attr message in the slider undo methods
        if closeUndo:  # close the undo chunk (if slider hadn't been pressed)
            undodecorator.closeUndoChunk()

    @undodecorator.undoDecorator
    def setAllNCloth(self):
        """Sets all attributes from the GUI"""
        networkNode = self.properties.nClothNetworkTxt.value
        if networkNode == NO_NETWORK_TXT:
            return
        for attr in nclothconstants.SKINNED_NCLOTH_ATTRS:
            self.setAttrNCloth(attr)
        nclothskinned.setPresetIndexNetwork(networkNode, self.properties.nClothPresetsCombo.value)

    @undodecorator.undoDecorator
    def selectNode(self, nodeKey):
        """From a node key select the mesh in the scene:

            BLENDSHAPE_CLOTH_NODE = "blendshapeClothNode"
            NCLOTH_NODE = "nClothNode"
            NUCLEUS_NODE = "nucleusNode"

        If nodeKey equals "network" then select the netowrk node itself

        :param nodeKey: The dictionary key named the same as the network attribute name for the node
        :type nodeKey: str
        """
        networkNode = self.properties.nClothNetworkTxt.value
        selNetworkNode = False
        if networkNode == NO_NETWORK_TXT:
            om2.MGlobal.displayWarning("No Skinned NCloth setup selected")
            return
        if nodeKey == "network":
            selNetworkNode = True
        nclothskinned.selectNode(networkNode, nodeKey=nodeKey, selectNetworkNode=selNetworkNode)

    @undodecorator.undoDecorator
    def showMesh(self, nodeKey):
        """Shows one of four meshes in the scene, and hides the others.

            ORIGINAL_MESH_TFRM = "originalMeshTransform"
            POLYSMOOTH_MESH_TFRM = "polySmoothMeshTransform"
            CLOTH_MESH_TFRM = "clothMeshTransform"
            BLENDER_MESH_TFRM = "blenderMeshTransform"

        :param nodeKey: The dictionary key named the same as the network attribute name for the node
        :type nodeKey: str
        """
        networkNode = self.properties.nClothNetworkTxt.value
        if networkNode == NO_NETWORK_TXT:
            om2.MGlobal.displayWarning("No Skinned NCloth setup selected")
            return
        nclothskinned.showMesh(networkNode, nodeKey)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        sliderList = list()
        for uiInstance in self.uiInstanceList:
            uiInstance.skinnedNClothBtn.clicked.connect(self.createSkinnedNCloth)
            uiInstance.nClothPresetsCombo.itemChanged.connect(self.changePreset)
            uiInstance.paintBlendshapeBtn.clicked.connect(self.paintBlendshape)
            uiInstance.selectBlendshapeBtn.clicked.connect(self.selectBlendshape)
            uiInstance.createCacheBtn.clicked.connect(self.createCache)
            uiInstance.deleteCacheBtn.clicked.connect(self.deleteCache)
            uiInstance.deleteNClothBtn.clicked.connect(self.deleteSkinnedNClothSetup)
            uiInstance.bakeNClothBtn.clicked.connect(self.bakeSkinnedNClothSetup)
            uiInstance.updateGuiBtn.clicked.connect(self.getAllAttrs)
            # Dots Menu
            uiInstance.dotsMenu.resetSettings.connect(self.getAllAttrs)
            uiInstance.dotsMenu.selectNCloth.connect(partial(self.selectNode, NCLOTH_NODE))
            uiInstance.dotsMenu.selectNucleus.connect(partial(self.selectNode, NUCLEUS_NODE))
            uiInstance.dotsMenu.selectBlendshape.connect(partial(self.selectNode, BLENDSHAPE_CLOTH_NODE))
            uiInstance.dotsMenu.selectNetwork.connect(partial(self.selectNode, "network"))
            uiInstance.dotsMenu.showMain.connect(partial(self.showMesh, BLENDER_MESH_TFRM))
            uiInstance.dotsMenu.showCloth.connect(partial(self.showMesh, CLOTH_MESH_TFRM))
            uiInstance.dotsMenu.showSubD.connect(partial(self.showMesh, POLYSMOOTH_MESH_TFRM))
            uiInstance.dotsMenu.showOrig.connect(partial(self.showMesh, ORIGINAL_MESH_TFRM))
            uiInstance.dotsMenu.nucleusEnabled.connect(self.enableSetup)
            uiInstance.dotsMenu.enableAll.connect(partial(self.enableDisableAll, enableState=True))
            uiInstance.dotsMenu.disableAll.connect(partial(self.enableDisableAll, enableState=False))
            # NCloth Attr Changes
            uiInstance.thicknessFSlider.floatSliderChanged.connect(partial(self.setAttrNCloth,
                                                                           NCA_THICKNESS))
            # Nucleus Attr Changes
            uiInstance.maxCollisionsFSlider.floatSliderChanged.connect(partial(self.setAttrNucleus,
                                                                               attr=NCA_NUCLEUS_MAX_COLLISIONS))
            uiInstance.startFrameInt.textModified.connect(partial(self.setAttrNucleus,
                                                                  attr=NCA_NUCLEUS_STARTFRAME))
            # Blendshape Attr Changes
            uiInstance.blendshapeMultiplyFSlider.floatSliderChanged.connect(partial(self.setAttrBlendshape,
                                                                                    attr=NCA_BLEND_ATTR))
            sliderList.append(uiInstance.thicknessFSlider)
            sliderList.append(uiInstance.maxCollisionsFSlider)

        # NCloth Attr Changes
        self.advancedWidget.attractFSlider.floatSliderChanged.connect(partial(self.setAttrNCloth,
                                                                              NCA_INPUT_ATTRACT))
        self.advancedWidget.stretchResistFSlider.floatSliderChanged.connect(partial(self.setAttrNCloth,
                                                                                    NCA_STRETCH_RESISTANCE))
        self.advancedWidget.compressResistFSlider.floatSliderChanged.connect(partial(self.setAttrNCloth,
                                                                                     NCA_COMPRESSION_RESISTANCE))
        self.advancedWidget.shearResistFSlider.floatSliderChanged.connect(partial(self.setAttrNCloth,
                                                                                  NCA_SHEAR_RESISTANCE))
        self.advancedWidget.bendResistFSlider.floatSliderChanged.connect(partial(self.setAttrNCloth,
                                                                                 NCA_BEND_RESISTANCE))
        self.advancedWidget.bendDropoffFSlider.floatSliderChanged.connect(partial(self.setAttrNCloth,
                                                                                  NCA_BEND_ANGLE_DROPOFF))
        # Nucleus Attr Changes
        self.advancedWidget.subStepsFSlider.floatSliderChanged.connect(partial(self.setAttrNucleus,
                                                                               attr=NCA_NUCLEUS_SUBSTEPS))

        sliderList.append(self.advancedWidget.attractFSlider)
        sliderList.append(self.advancedWidget.stretchResistFSlider)
        sliderList.append(self.advancedWidget.compressResistFSlider)
        sliderList.append(self.advancedWidget.shearResistFSlider)
        sliderList.append(self.advancedWidget.bendResistFSlider)
        sliderList.append(self.advancedWidget.bendDropoffFSlider)
        sliderList.append(self.advancedWidget.subStepsFSlider)
        # Connect the float and color sliders correctly
        for floatSlider in sliderList:
            floatSlider.sliderPressed.connect(self.openUndoChunk)
            floatSlider.sliderReleased.connect(self.closeUndoChunk)
        # Selection callbacks
        self.selectionCallbacks.callback.connect(self.selectionChanged)  # Monitor selection
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
        toolTip = "Select any node in the Skinned Mesh network to activate the Zoo NCloth Network."
        self.nClothNetworkTxt = elements.StringEdit(label="NCloth Network",
                                                    editText=NO_NETWORK_TXT,
                                                    toolTip=toolTip,
                                                    editRatio=21,
                                                    labelRatio=9)
        self.nClothNetworkTxt.edit.setDisabled(True)
        # Dots Menu -------------------------------------------
        self.dotsMenu = DotsMenu()
        # Update GUI Shader Btn --------------------------------------------
        toolTip = "Update the GUI refresh with latest values"
        self.updateGuiBtn = elements.styledButton("",
                                                  "arrowLeft",
                                                  self,
                                                  toolTip=toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG)
        # NCloth Presets Combo --------------------------------------------
        toolTip = "Maya's NCloth Presets \n" \
                  "Note: that these presets only affect the sliders in the advanced GUI \n" \
                  "and do not affect all nCloth settings.  To change all nCloth settings \n" \
                  "select the nCloth node in the attribute editor and use the presets there. \n" \
                  "Be sure to always change `Mesh Attract` back to `1.0` after using Maya's presets."
        nclothDefaultIndex = NCLOTH_PRESET_NAME_LIST.index("TShirt")
        self.nClothPresetsCombo = elements.ComboBoxSearchable(text="NCloth Preset",
                                                              items=NCLOTH_PRESET_NAME_LIST,
                                                              setIndex=nclothDefaultIndex,
                                                              labelRatio=10,
                                                              boxRatio=30,
                                                              toolTip=toolTip)
        # SubD Divisions Int ---------------------------------------
        tooltip = "The amount of subdivisions on the nCloth mesh.  \n" \
                  "Each division will divide the mesh by four. \n" \
                  "Two divisions and the mesh will be sixteen times as dense.\n\n" \
                  "Denser meshes usually create more wrinkles but will slow \n" \
                  "simulation times. Higher `Substeps` may also be required. \n\n" \
                  "This setting cannot be changed after building."
        self.divisionsInt = elements.IntEdit(label="SubD Divisions",
                                             editText="2",
                                             toolTip=tooltip)
        # Start Frame Int ---------------------------------------
        tooltip = "The start frame for the simulation. \n" \
                  "Affects attributes found on the nucleus and ncloth nodes. "
        self.startFrameInt = elements.IntEdit(label="Start Frame",
                                              editText="1",
                                              toolTip=tooltip)
        # Slider Settings ---------------------------------------
        tooltip = "Cloth thickness in centimeters. \n" \
                  "Higher thicknesses create larger wrinkles. \n\n" \
                  "Note that smaller values will be limited by \n" \
                  "your mesh density.  For very small wrinkles \n" \
                  "you'll need a very dense mesh."
        self.thicknessFSlider = elements.FloatSlider(label="Thickness",
                                                     defaultValue=0.005,
                                                     sliderAccuracy=4000,
                                                     sliderMax=4.0,
                                                     toolTip=tooltip,
                                                     decimalPlaces=3)
        # Max Collisions Slider Settings ---------------------------------------
        tooltip = "Specifies the maximum number of collision iterations per simulation step. \n" \
                  "Increase this slider to help reduce buzzing effects. \n\n" \
                  "Higher values are more accurate and minimize buzzing effects but \n" \
                  "the simulation will slow. This is a nucleus attribute."
        self.maxCollisionsFSlider = elements.FloatSlider(label="Max Collisions",
                                                         defaultValue=4,
                                                         sliderAccuracy=100,
                                                         sliderMax=100,
                                                         toolTip=tooltip,
                                                         decimalPlaces=1)
        # Blendshape Settings Title -----------------------------------
        self.blendshapeTitle = elements.LabelDivider(text="Blendshape Settings")
        # Paint Blendshape NCloth ---------------------------------------
        tooltip = "Click this button to paint blendshape weights. \n\n" \
                  "Painting black will eliminate wrinkles. \n" \
                  "Painting white will show hidden wrinkles."
        self.paintBlendshapeBtn = elements.styledButton("Paint Blendshape",
                                                        icon="paintLine",
                                                        toolTip=tooltip,
                                                        style=uic.BTN_LABEL_SML)
        # Blendshape Multiplier Float ---------------------------------------
        tooltip = "A multiplier effect using the blendshape node. \n" \
                  "Zero and the wrinkles have no effect, two and the wrinkles will double. \n\n" \
                  "Note: You may also paint the blendshape to paint out unwanted wrinkles. \n" \
                  "See the `Paint Blendshape` button below."
        self.blendshapeMultiplyFSlider = elements.FloatSlider(label="Blend Multiplier",
                                                              defaultValue=1.0,
                                                              sliderAccuracy=200,
                                                              sliderMax=4.0,
                                                              toolTip=tooltip,
                                                              decimalPlaces=3)
        # Paint Blendshape NCloth ---------------------------------------
        tooltip = "This button selects the blendshape node. \n" \
                  "The main mesh is the *_clothBlender mesh, it's a \n" \
                  "mix between the *_polysmooth and *_cloth mehses. \n" \
                  "Use the blendshape node to dial the wrinkles up and down."
        self.selectBlendshapeBtn = elements.styledButton("Select Blendshape",
                                                         icon="cursorSelect",
                                                         toolTip=tooltip,
                                                         style=uic.BTN_LABEL_SML)
        # Paint Wrinkle Map Button ---------------------------------------
        tooltip = ""
        self.paintWrinkleMapBtn = elements.styledButton("Paint Wrinkle Map",
                                                        icon="paintLine",
                                                        toolTip=tooltip,
                                                        style=uic.BTN_LABEL_SML)
        # Wrinkle Map Scale Float ---------------------------------------
        tooltip = ""
        self.wrinkleMapScaleFloat = elements.FloatEdit(label="Map Scale",
                                                       editText="1.0",
                                                       toolTip=tooltip)
        # Create Cache Button ---------------------------------------
        tooltip = "Creates a geometry-cache on the selected Skinned NCloth setup for faster/realtime playback. \n" \
                  "The cache affects the mesh `*_cloth` hidden mesh. " \
                  "The cache is saved to disk and uses the timeline range.\n\n" \
                  "After the cache completes the nucleus node is disabled for timeline scrubbing. \n" \
                  "Deleting the cache will enable the nucleus node to be on again."
        self.createCacheBtn = elements.styledButton("Create/Recreate Cache",
                                                    icon="cacheAdd",
                                                    toolTip=tooltip,
                                                    style=uic.BTN_LABEL_SML)
        # Delete Cache Button ---------------------------------------
        tooltip = "Deletes a geometry-cache on the selected Skinned NCloth setup. \n" \
                  "Will delete the cache file from disk, and re-enable the nucleus node."
        self.deleteCacheBtn = elements.styledButton("Delete Cache",
                                                    icon="cacheRemove",
                                                    toolTip=tooltip,
                                                    style=uic.BTN_LABEL_SML)
        # Create Skinned NCloth ---------------------------------------
        tooltip = "Creates the `Skinned NCloth` setup on selected geo. \n" \
                  " - Select deforming/skinned geometry and run. \n\n" \
                  "The geometry must be animated for the simulation to calculate. \n" \
                  "Use the `Create Cache` button to run and save the simulation and to disk."
        self.skinnedNClothBtn = elements.styledButton("Create Skinned NCloth",
                                                      icon="tshirt",
                                                      toolTip=tooltip,
                                                      style=uic.BTN_DEFAULT)
        # Delete Skinned NCloth ---------------------------------------
        tooltip = "Deletes the `Skinned NCloth` setup and removes all extra nodes. \n" \
                  "The original geometry remains and will be shown. \n\n" \
                  "To keep wrinkle-modeled geometry use bake, or duplicate\n" \
                  "the geometry before deleting."
        self.deleteNClothBtn = elements.styledButton("Delete",
                                                     icon="trash",
                                                     toolTip=tooltip,
                                                     style=uic.BTN_DEFAULT)
        # Bake Skinned NCloth ---------------------------------------
        tooltip = "Bakes the `Skinned NCloth` setup and removes all related nodes. \n" \
                  "The final *_clothBlender mesh will remain and be shown in it's current wrinkled state. \n" \
                  "Note: Any animation will be lost."
        self.bakeNClothBtn = elements.styledButton("Bake",
                                                   icon="bake",
                                                   toolTip=tooltip,
                                                   style=uic.BTN_DEFAULT)
        if uiMode == UI_MODE_ADVANCED:
            # Initialize Title -----------------------------------
            self.initializeTitle = elements.LabelDivider(text="Initialize")
            # Wrinkle Settings Title -----------------------------------
            self.wrinkleTitle = elements.LabelDivider(text="NCloth Wrinkle Properties")
            # NCloth Advanced Sliders ---------------------------------------
            tooltip = "Specifies how much the nCloth is attracted to the shape of the \n" \
                      "original mesh. \n" \
                      "Values below one will cause the mesh to lag and bounce. \n" \
                      "If the mesh is too laggy, try slighty increasing the slider above one."
            self.attractFSlider = elements.FloatSlider(label="Mesh Attract",
                                                       defaultValue=1.0,
                                                       sliderAccuracy=400,
                                                       sliderMax=2.0,
                                                       toolTip=tooltip,
                                                       decimalPlaces=3)
            tooltip = "Higher values resist (less) wrinkles while the mesh is stretching, \n" \
                      "and the simulation will slow."
            self.stretchResistFSlider = elements.FloatSlider(label="Stretch Resist",
                                                             defaultValue=35.0,
                                                             sliderAccuracy=2000,
                                                             sliderMax=200.0,
                                                             toolTip=tooltip)
            tooltip = "Higher values resist (less) wrinkles while the mesh is compressing, \n" \
                      "and the simulation will slow."
            self.compressResistFSlider = elements.FloatSlider(label="Compression",
                                                              defaultValue=10.0,
                                                              sliderAccuracy=2000,
                                                              sliderMax=200.0,
                                                              toolTip=tooltip)
            tooltip = "Higher values resist (less) wrinkles while the mesh is bending, \n" \
                      "and the simulation will slow."
            self.bendResistFSlider = elements.FloatSlider(label="Bend Resist",
                                                          defaultValue=0.1,
                                                          sliderMax=200.0,
                                                          sliderAccuracy=2000,
                                                          toolTip=tooltip)
            tooltip = "Higher values resist (less) wrinkles while the mesh is shearing, \n" \
                      "and the simulation will slow."
            self.shearResistFSlider = elements.FloatSlider(label="Shear Resist",
                                                           defaultValue=0.0,
                                                           sliderAccuracy=2000,
                                                           sliderMax=200.0,
                                                           toolTip=tooltip)
            tooltip = "The Bend Angle Dropoff, affects wrinkle limits while the mesh is being bent. \n" \
                      "Higher values create less wrinkles"
            self.bendDropoffFSlider = elements.FloatSlider(label="Bend Dropoff",
                                                           defaultValue=0.4,
                                                           sliderAccuracy=200,
                                                           sliderMax=1.0,
                                                           toolTip=tooltip)
            # Accuracy Settings Title -----------------------------------
            self.accuracyTitle = elements.LabelDivider(text="Nucleus Accuracy Properties")
            # NCloth Advanced Sliders Substeps ---------------------------------------
            tooltip = "The amount of steps in between frames calculated by the simulation. \n" \
                      "Usually try to increase `Max Collisions` before adjusting this slider. \n\n" \
                      "Higher values are more accurate and minimize buzzing effects but \n" \
                      "the simulation will slow.  Higher values may increase mesh lag.\n\n" \
                      "Please note that higher values may not always give desired results \n" \
                      "Try to keep this value as low as possible."
            self.subStepsFSlider = elements.FloatSlider(label="Substeps",
                                                        defaultValue=3,
                                                        sliderAccuracy=20,
                                                        sliderMax=20,
                                                        toolTip=tooltip,
                                                        decimalPlaces=1)
            # Texture Settings Title -----------------------------------
            self.mapTitle = elements.LabelDivider(text="Map Settings")
            # Cache Settings Title -----------------------------------
            self.cacheTitle = elements.LabelDivider(text="Cache Settings")
            # Create Title -----------------------------------
            self.createTitle = elements.LabelDivider(text="Create Setup")


class DotsMenu(IconMenuButton):
    menuIcon = "menudots"
    resetSettings = QtCore.Signal()

    nucleusEnabled = QtCore.Signal(object)
    enableAll = QtCore.Signal()
    disableAll = QtCore.Signal()

    selectNCloth = QtCore.Signal()
    selectNucleus = QtCore.Signal()
    selectBlendshape = QtCore.Signal()
    selectNetwork = QtCore.Signal()

    showMain = QtCore.Signal()
    showCloth = QtCore.Signal()
    showSubD = QtCore.Signal()
    showOrig = QtCore.Signal()

    def __init__(self, parent=None, networkEnabled=False):
        """
        """
        super(DotsMenu, self).__init__(parent=parent)
        self.networkEnabled = networkEnabled
        iconColor = THEME_PREFS.ICON_PRIMARY_COLOR
        self.setIconByName(self.menuIcon, size=16, colors=iconColor)
        self.setMenuAlign(QtCore.Qt.AlignRight)
        self.setToolTip("File menu. Skinned NCloth")
        self.disableActionList = list()
        # Build the static menu
        # Reset To Defaults --------------------------------------
        reloadIcon = iconlib.iconColorized("reload2", utils.dpiScale(16))
        self.addAction("Reset Settings", connect=lambda: self.resetSettings.emit(), icon=reloadIcon)
        self.addSeparator()
        # Reset To Defaults --------------------------------------
        self.enabledAction = self.addAction("Network Enabled",
                                            connect=lambda x: self.nucleusEnabled.emit(x),
                                            checkable=True,
                                            checked=self.networkEnabled)
        enableIcon = iconlib.iconColorized("on", utils.dpiScale(16))
        self.addAction("Enable All Scene", connect=lambda: self.enableAll.emit(), icon=enableIcon)
        disableIcon = iconlib.iconColorized("off", utils.dpiScale(16))
        self.addAction("Disable All Scene", connect=lambda: self.disableAll.emit(), icon=disableIcon)
        self.addSeparator()
        # Select --------------------------------------
        cursorIcon = iconlib.iconColorized("cursorSelect", utils.dpiScale(16))
        self.disableActionList.append(
            self.addAction("Select NCloth", connect=lambda: self.selectNCloth.emit(), icon=cursorIcon))
        self.disableActionList.append(
            self.addAction("Select Nucleus", connect=lambda: self.selectNucleus.emit(), icon=cursorIcon))
        self.disableActionList.append(
            self.addAction("Select Blendshape", connect=lambda: self.selectBlendshape.emit(), icon=cursorIcon))
        self.disableActionList.append(
            self.addAction("Select Network Node", connect=lambda: self.selectNetwork.emit(), icon=cursorIcon))
        self.addSeparator()
        showIcon = iconlib.iconColorized("eye", utils.dpiScale(16))
        self.disableActionList.append(
            self.addAction("Show Main Blend Mesh", connect=lambda: self.showMain.emit(), icon=showIcon))
        self.addSeparator()

        # Show --------------------------------------
        self.disableActionList.append(
            self.addAction("Show Before Mesh", connect=lambda: self.showOrig.emit(), icon=showIcon))
        self.disableActionList.append(
            self.addAction("Show Divided Mesh", connect=lambda: self.showSubD.emit(), icon=showIcon))
        self.disableActionList.append(
            self.addAction("Show Cloth Only Mesh", connect=lambda: self.showCloth.emit(), icon=showIcon))


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
                                         spacing=uic.SREG)
        # Top NCloth Netowrk Layout ---------------------------------------
        topLayout = elements.hBoxLayout(margins=(0, 0, 0, 0))
        topLayout.addWidget(self.nClothNetworkTxt, 10)
        topLayout.addWidget(self.updateGuiBtn, 1)
        topLayout.addWidget(self.dotsMenu, 1)
        # Divisions Start Frame Layout ---------------------------------------
        divStartFrameLayout = elements.hBoxLayout()
        divStartFrameLayout.addWidget(self.divisionsInt, 1)
        divStartFrameLayout.addWidget(self.startFrameInt, 1)
        # Blendshape Layout ---------------------------------------
        blendshapeLayout = elements.hBoxLayout(margins=(0, uic.SREG, 0, uic.SREG), spacing=uic.SVLRG)
        blendshapeLayout.addWidget(self.paintBlendshapeBtn, 1)
        blendshapeLayout.addWidget(self.selectBlendshapeBtn, 1)
        # Wrinkle Map Layout ---------------------------------------
        mapLayout = elements.hBoxLayout(spacing=uic.SVLRG)
        mapLayout.addWidget(self.wrinkleMapScaleFloat, 1)
        mapLayout.addWidget(self.paintWrinkleMapBtn, 1)
        # Cache Layout ---------------------------------------
        cacheLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.SREG), spacing=uic.SVLRG)
        cacheLayout.addWidget(self.createCacheBtn, 1)
        cacheLayout.addWidget(self.deleteCacheBtn, 1)
        # Create Delete Layout ---------------------------------------
        createLayout = elements.hBoxLayout()
        createLayout.addWidget(self.skinnedNClothBtn, 2)
        createLayout.addWidget(self.deleteNClothBtn, 1)
        createLayout.addWidget(self.bakeNClothBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(topLayout)
        mainLayout.addWidget(self.nClothPresetsCombo)
        mainLayout.addLayout(divStartFrameLayout)
        mainLayout.addWidget(self.thicknessFSlider)
        mainLayout.addWidget(self.maxCollisionsFSlider)
        mainLayout.addWidget(self.blendshapeMultiplyFSlider)
        mainLayout.addLayout(blendshapeLayout)
        # mainLayout.addLayout(mapLayout)
        mainLayout.addLayout(cacheLayout)
        mainLayout.addLayout(createLayout)


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
                                         margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Top NCloth Netowrk Layout ---------------------------------------
        topLayout = elements.hBoxLayout()
        topLayout.addWidget(self.nClothNetworkTxt, 10)
        topLayout.addWidget(self.updateGuiBtn, 1)
        topLayout.addWidget(self.dotsMenu, 1)
        # Divisions Start Frame Layout ---------------------------------------
        divStartFrameLayout = elements.hBoxLayout(spacing=uic.SVLRG)
        divStartFrameLayout.addWidget(self.divisionsInt, 1)
        divStartFrameLayout.addWidget(self.startFrameInt, 1)
        # Blendshape Layout ---------------------------------------
        blendshapeLayout = elements.hBoxLayout(margins=(0, uic.SREG, 0, 0), spacing=uic.SVLRG)
        blendshapeLayout.addWidget(self.paintBlendshapeBtn, 1)
        blendshapeLayout.addWidget(self.selectBlendshapeBtn, 1)
        # Wrinkle Map Layout ---------------------------------------
        mapLayout = elements.hBoxLayout(spacing=uic.SVLRG)
        mapLayout.addWidget(self.wrinkleMapScaleFloat, 1)
        mapLayout.addWidget(self.paintWrinkleMapBtn, 1)
        # Cache Layout ---------------------------------------
        cacheLayout = elements.hBoxLayout(spacing=uic.SVLRG)
        cacheLayout.addWidget(self.createCacheBtn, 1)
        cacheLayout.addWidget(self.deleteCacheBtn, 1)
        # Create Delete Layout ---------------------------------------
        createLayout = elements.hBoxLayout()
        createLayout.addWidget(self.skinnedNClothBtn, 2)
        createLayout.addWidget(self.deleteNClothBtn, 1)
        createLayout.addWidget(self.bakeNClothBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(topLayout)
        mainLayout.addWidget(self.initializeTitle)
        mainLayout.addLayout(divStartFrameLayout)

        mainLayout.addWidget(self.wrinkleTitle)
        mainLayout.addWidget(self.nClothPresetsCombo)
        mainLayout.addWidget(self.thicknessFSlider)
        mainLayout.addWidget(self.attractFSlider)
        mainLayout.addWidget(self.stretchResistFSlider)
        mainLayout.addWidget(self.compressResistFSlider)
        mainLayout.addWidget(self.shearResistFSlider)
        mainLayout.addWidget(self.bendResistFSlider)
        mainLayout.addWidget(self.bendDropoffFSlider)

        mainLayout.addWidget(self.accuracyTitle)
        mainLayout.addWidget(self.maxCollisionsFSlider)
        mainLayout.addWidget(self.subStepsFSlider)

        mainLayout.addWidget(self.blendshapeTitle)
        mainLayout.addWidget(self.blendshapeMultiplyFSlider)
        mainLayout.addLayout(blendshapeLayout)

        # mainLayout.addWidget(self.mapTitle)
        # mainLayout.addLayout(mapLayout)

        mainLayout.addWidget(self.cacheTitle)
        mainLayout.addLayout(cacheLayout)

        mainLayout.addWidget(self.createTitle)
        mainLayout.addLayout(createLayout)
