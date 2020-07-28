import os
from functools import partial

from Qt import QtWidgets, QtCore

from maya.api import OpenMaya as om2
from maya import cmds

from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.apps.toolsetsui import toolsetcallbacks
from zoo.apps.toolsetsui import toolsetui

from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.maya.cmds.shaders import displacementmulti
from zoo.preferences.core import preference
from zoo.preferences import preferencesconstants as pc
from zoo.libs.maya.cmds.workspace import mayaworkspace
from zoo.libs.maya.cmds.shaders import shaderutils
from zoo.libs.maya.cmds.objutils import filtertypes
from zoo.libs.maya.cmds.shaders.shdmultconstants import DISP_ATTR_TYPE, DISP_ATTR_DIVISIONS, DISP_ATTR_SCALE, \
    DISP_ATTR_BOUNDS, DISP_ATTR_AUTOBUMP, DISP_ATTR_IMAGEPATH, DISP_ATTR_RENDERER, NW_DISPLACE_NODE, \
    NW_DISPLACE_MESH_ATTR, NW_DISPLACE_SG_ATTR, NW_DISPLACE_FILE_ATTR, NW_DISPLACE_NODE_ATTR
# Dots Menu
from zoo.libs.pyqt.widgets.iconmenu import IconMenuButton
from zoo.libs import iconlib
from zoo.libs.pyqt import utils

THEME_PREFS = preference.interface("core_interface")

UI_MODE_COMPACT = 0
DISP_METHODS = ["Vector"]  # TODO add "Height B&W"
DISP_TYPE = ["Tangent", "Object"]
DFLT_RNDR_MODES = [("arnold", "Arnold"), ("redshift", "Redshift"), ("renderman", "Renderman")]

DFLT_SHADER = "None"
DFLT_ACTIVE = "Off"
DFLT_METHOD = 0
DFLT_TYPE = 0
DFLT_DIVISIONS = 4
DFLT_SCALE = 1.0
DFLT_AUTOBUMP = True
DFLT_IMAGEPATH = ""
DFLT_BOUNDS = 0.2


class DisplacementCreator(toolsetwidgetmaya.ToolsetWidgetMaya):
    """Creates Vector Displacement for the given renderer
    """
    id = "displacementCreator"
    uiData = {"label": "Displacement Manager",
              "icon": "displacement",
              "tooltip": "Creates and manages displacement setups in Arnold Redshift and Renderman",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-displacement-creator/"
              }

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run setup renderer info from preferences"""
        self.generalSettingsPrefsData = preference.findSetting(pc.RELATIVE_PREFS_FILE, None)  # renderer in general pref
        self.properties.rendererIconMenu.value = self.generalSettingsPrefsData[pc.PREFS_KEY_RENDERER]
        self.toolsetWidget = self  # needed for callback decorators
        self.shaderName = ""
        self.oldDivisions = DFLT_DIVISIONS
        self.setupEnabled = False  # will the current displacement render for Network Enabled checkbox in dots menu?

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        parent = QtWidgets.QWidget(parent=self)
        self.compactWidget = GuiCompact(parent=parent, properties=self.properties, toolsetWidget=self)
        return parent

    def postContentSetup(self):
        """Last of the initialize code"""
        self.hideShowRendererWidgets()
        self.uiConnections()
        self.updateUIFromSelection(bypassRenderer=True)  # update GUI from current in scene selection
        self.startSelectionCallback()  # start selection callback

    def defaultAction(self):
        """Double Click"""
        pass

    # ------------------
    # PROPERTIES
    # ------------------

    def initializeProperties(self):
        return [{"name": "rendererIconMenu", "label": "", "value": "Arnold"}]

    # ------------------
    # RIGHT CLICKS
    # ------------------

    def actions(self):
        """Right click menu and actions
        """
        return []

    # ------------------------------------
    # UPDATE WIDGET VISIBILITY RENDERER CHANGE
    # ------------------------------------

    def hideShowRendererWidgets(self):
        renderer = self.properties.rendererIconMenu.value
        if renderer == "Renderman":
            # Disable Max Divisions
            self.compactWidget.maxDivisionsInt.setDisabled(True)
            self.compactWidget.autoBumpCheckBox.setDisabled(True)
            self.compactWidget.autoBumpLabel.setDisabled(True)
        else:  # Arnold and Redshift
            # Enable Max Divisions
            self.compactWidget.maxDivisionsInt.setDisabled(False)
            self.compactWidget.autoBumpCheckBox.setDisabled(False)
            self.compactWidget.autoBumpLabel.setDisabled(False)

    # ------------------------------------
    # RENDERER - AND SEND/RECEIVE ALL TOOLSETS
    # ------------------------------------

    def global_changeRenderer(self):
        """Updates all GUIs with the current renderer"""
        self.hideShowRendererWidgets()  # update the GUI widgets
        # Change renderer
        self.generalSettingsPrefsData = preference.findSetting(pc.RELATIVE_PREFS_FILE, None)  # refresh data
        toolsets = toolsetui.toolsets(attr="global_receiveRendererChange")
        self.generalSettingsPrefsData = elements.globalChangeRenderer(self.properties.rendererIconMenu.value,
                                                                      toolsets,
                                                                      self.generalSettingsPrefsData,
                                                                      pc.PREFS_KEY_RENDERER)

    def global_receiveRendererChange(self, renderer):
        """Receives from other GUIs, changes the renderer when it is changed"""
        self.properties.rendererIconMenu.value = renderer
        self.hideShowRendererWidgets()
        self.updateFromProperties()

    # ------------------
    # BROWSE IMAGE
    # ------------------

    def browseImage(self):
        """Browse for the image popup window"""
        projectDirectory = mayaworkspace.getCurrentMayaWorkspace()
        projectDirectory = os.path.join(projectDirectory, "sourceImages/")
        # Todo: check if this directory exists
        fullFilePath, filter = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", projectDirectory)
        if not str(fullFilePath):
            return
        # Todo: check file extensions here
        self.properties.imagePathTxt.value = str(fullFilePath)
        self.setAttrsDisplacement()
        self.updateFromProperties()

    # ------------------
    # CALLBACKS
    # ------------------

    def selectionChanged(self, selection):
        """Run when the callback selection changes, updates the GUI if an object is selected

        Callbacks are handled automatically by toolsetcallbacks.py which this class inherits"""
        if not selection:  # then still may be a selection TODO add this to internal callbacks maybe?
            selection = cmds.ls(selection=True)  # catches component and node selections
            if not selection:  # then nothing is selected
                return
        self.updateUIFromSelection()  # will update the GUI

    # ------------------
    # GET AND SET ATTRS
    # ------------------

    def setDefaultValues(self):
        """Sets the default values for the UI, disables the delete button as no displacement is found.
        """
        self.properties.activeDisplacementTxt.value = DFLT_ACTIVE
        self.properties.scaleFloat.value = DFLT_SCALE
        self.properties.autoBumpCheckBox.value = DFLT_AUTOBUMP
        if self.properties.rendererIconMenu.value == "Renderman":  # force renderman as False
            self.properties.autoBumpCheckBox.value = False
        self.properties.imagePathTxt.value = DFLT_IMAGEPATH
        self.properties.maxDivisionsInt.value = DFLT_DIVISIONS
        self.properties.dispTypeCombo.value = DFLT_TYPE
        self.properties.boundsFloat.value = DFLT_BOUNDS
        self.oldDivisions = DFLT_DIVISIONS

    def checkForNetworkShaderName(self, bypassRenderer=False):
        """Will check for zoo displacement networks and gets the related shader name:

        This ugly method gets tricky because the shader name is not in the network!
        Shader names are preferred for the user as the network node may not be named intuitively.

        Sets the active property on the UI. self.properties.activeShader.value

        Checks for a displacement network and gets the related shader name.
        If the displacement network does not exist, check if any geometry or shaders/SGs are selected
        Return shaders as None if no geo network or shaders are found, will bail in next method
        If geometry or shaders are selected then show the shader name if one is found related to those objects.

        :param bypassRenderer: If True don't warn the user with a popup load renderer window, used on startup
        :type bypassRenderer: bool
        :return networkNodes: A list of network nodes found, will be empty list if none found
        :rtype networkNodes: list(str)
        :return shader: The shader's name, will be empty string in none found, if None has special bail properties
        :rtype shader: str
        """
        # ----------------
        # Check for a displacement network and get the related shader name
        # If displacement network does not exist
        # the UI will only show the shader name if found
        # ----------------
        renderer = self.properties.rendererIconMenu.value
        if not elements.checkRenderLoaded(renderer, bypassWindow=bypassRenderer):
            return list(), ""  # check renderer is loaded
        networkNodes = displacementmulti.getDisplaceNetworkSelected()
        if networkNodes:  # Get the shader name from the shading group
            shadingGroups = displacementmulti.getDisplacementNetworkItems(networkNodes[0])[1]  # shadingGroups
            if not shadingGroups:  # no shading group
                om2.MGlobal.displayWarning("This shader has no shading group")
            else:  # get the shader
                shader = shaderutils.getShaderFromSG(shadingGroups[0])
                self.shaderName = shader
            if not shader:  # will be rare, but should check in case of passing errors
                self.shaderName = shadingGroups[0]  # unsure what to do in this case so saving the shading group
        else:  # No network, could be a shader selection or geo, try to find the related shader name
            sel = cmds.ls(selection=True)
            if sel:  # Check if geo or shaders otherwise ignore as don't want the GUI to update
                materials = cmds.ls(sel, materials=True)
                geo = filtertypes.filterGeoOnly(sel)
                if not materials and not geo:
                    return list(), None  # dodgy return shader as None not "" so can bail in updateUIFromSelection()
            shaders = shaderutils.getShadersFromSelectedNodes()
            if shaders:
                shader = shaders[0]
                self.shaderName = shader
                # Try to find the network from the shading group, it's not connected to the shader
                shadingGroup = shaderutils.getShadingGroupFromShader(shader)
                if shadingGroup:  # try finding network from shading group
                    networkNodes = displacementmulti.getDisplaceNetworkNode([shadingGroup])
            else:  # No shader name found
                shader = "None"
                self.shaderName = ""
        self.properties.activeShader.value = shader
        return networkNodes, shader

    def brokenNetwork(self, networkNodes):
        """Pops up a window for a broken network

        :param networkNodes: The network node name list of the displacement setup
        :type networkNodes: list(str)
        """
        om2.MGlobal.displayWarning("This displacement network is broken `{}`".format(networkNodes[0]))
        windowMessage = "This displacement network is broken: \n\n" \
                        "  `{}` \n\n" \
                        "Delete? Recommended.  This will clean the displacement network.".format(networkNodes[0])
        if elements.MessageBox_ok(windowName="Broken Displacement",
                                  message=windowMessage):
            displacementmulti.deleteDisplacementNetwork(networkNodes[0])

    def enableDisableUI(self):
        """Depending on the active state adjust the GUI enable states to match
        """
        activeState = self.properties.activeDisplacementTxt.value
        if "On" in activeState:  # Disable/Enable
            self.compactWidget.deleteDisplacementBtn.setEnabled(True)  # Enable Trash button
            self.compactWidget.imagePathTxt.setEnabled(True)
            self.compactWidget.browseBtn.setEnabled(True)
            self.compactWidget.createDisplacementBtn.setEnabled(False)
            for action in self.compactWidget.dotsMenu.disableActionList:
                action.setEnabled(True)
        else:  # Off so Disable/Enable
            self.compactWidget.dotsMenu.enabledAction.setChecked(False)
            self.compactWidget.deleteDisplacementBtn.setDisabled(True)  # Disable Trash button, nothing to delete
            self.compactWidget.imagePathTxt.setEnabled(False)
            self.compactWidget.browseBtn.setEnabled(False)
            self.compactWidget.createDisplacementBtn.setEnabled(True)
            for action in self.compactWidget.dotsMenu.disableActionList:
                action.setEnabled(False)
        # Set checkbox in dots menu
        if activeState == "On (Enabled)":
            self.compactWidget.dotsMenu.enabledAction.setChecked(True)
        elif activeState == "On (Disabled)":
            self.compactWidget.dotsMenu.enabledAction.setChecked(False)
        elif activeState == "Off":
            self.compactWidget.dotsMenu.enabledAction.setChecked(False)

    def updateUIFromSelection(self, update=True, bypassRenderer=False):
        """Will check for zoo displacement networks and gets the related shader name:

            1. If a network is found then update the UI from the attributes.
            -  Also checks if all shader meshes are linked to the geo
            2. If a network is not found, display the shader name or "None" and set Active to "Off",
            set attributes to default values.
            3. If network is found check it's valid and not broken, if broken warn the user.
            4. Set the UI from the current network if found and valid (active)
            5. Get the displacement enabled state, will it render or not (only if a network is found)

        :param update: Run self.updateProperties?
        :type update: bool
        :param bypassRenderer: If True don't warn the user with a popup load renderer window, used on startup
        :type bypassRenderer: bool
        """
        renderer = self.properties.rendererIconMenu.value
        networkNodes, shader = self.checkForNetworkShaderName(bypassRenderer=bypassRenderer)
        if shader is None:
            return  # no need to update special case where no networks found or geo or shaders/shading groups selected
        if not networkNodes:  # no displacement
            self.setDefaultValues()  # set to defaults here
            self.setupEnabled = False
            if update:
                self.updateFromProperties()
            self.enableDisableUI()
            return
        # Displacement network has been found, continue ----------------------
        attrDict = displacementmulti.getDisplacementNetworkAttrs(networkNodes[0])
        if not attrDict:  # Network is broken in some way and should be rebuilt, checks failed
            self.brokenNetwork(networkNodes)
            return
        # Passed network found, so set GUI properties ------------------
        self.setupEnabled = displacementmulti.getEnableDisplacement(networkNodes[0], renderer)  # for dots menu
        # Auto check and connect new meshes from the shader to the network, important for Arnold and Redshift
        connectedMeshes = displacementmulti.connectNewMeshesToNetwork(networkNodes[0], shader)
        disconnectedMeshes = displacementmulti.disconnectUnusedMeshesFromNetwork(networkNodes[0], shader)
        if connectedMeshes or disconnectedMeshes:  # then update the new meshes to the displacement
            displacementmulti.updateMeshes(renderer, connectedMeshes, disconnectedMeshes, attrDict, self.setupEnabled)
        # Passed network found, so set GUI properties ------------------
        if self.setupEnabled:
            enableMessage = "On (Enabled)"
        else:
            enableMessage = "On (Disabled)"
        self.properties.activeDisplacementTxt.value = enableMessage
        self.properties.scaleFloat.value = round(attrDict[DISP_ATTR_SCALE], 4)
        self.properties.autoBumpCheckBox.value = attrDict[DISP_ATTR_AUTOBUMP]
        self.properties.imagePathTxt.value = attrDict[DISP_ATTR_IMAGEPATH]
        self.properties.boundsFloat.value = round(attrDict[DISP_ATTR_BOUNDS], 4)
        if attrDict[DISP_ATTR_DIVISIONS]:  # might be None
            self.properties.maxDivisionsInt.value = attrDict[DISP_ATTR_DIVISIONS]
            self.oldDivisions = self.properties.maxDivisionsInt.value
        else:
            self.oldDivisions = DFLT_DIVISIONS
        if attrDict[DISP_ATTR_TYPE] == "Tangent":  # Type combobox
            self.properties.dispTypeCombo.value = 0
        else:
            self.properties.dispTypeCombo.value = 1
        # Enable/disable UI elements
        self.enableDisableUI()
        # Update GUI
        if update:
            self.updateFromProperties()
        # Finish
        if renderer != attrDict[DISP_ATTR_RENDERER]:  # warn user if mismatch between renderer and displacement
            om2.MGlobal.displayWarning("Renderer does not match the current Displacement Network, "
                                       "please change to `{}`".format(attrDict[DISP_ATTR_RENDERER]))

    def getShadingGroupFromShader(self):
        """Returns the shading group from self.shaderName which may be a shading group, custom for this UI

        :return shadingGroup: The shading group name, will be an empty string if None
        :rtype shadingGroup: str
        """
        if self.shaderName:
            if cmds.nodeType(self.shaderName) == "shadingEngine":  # can be a shading group in rare cases
                return self.shaderName
            else:  # will be a shader so try to find the shading group and use it for setting the attrs
                shadingGroup = shaderutils.getShadingGroupFromShader(self.shaderName)
                if not shadingGroup:
                    return ""
                return shadingGroup
        return ""

    def setMaxDisplacement(self):
        """Checks max displacement and warns the user it could be too high, returns to self.oldDivisions if cancelled"""
        divisions = self.properties.maxDivisionsInt.value
        if self.properties.maxDivisionsInt.value > 5:
            message = "The division level is high, are you sure you want to continue?\n\n" \
                      "High division can hang Maya. Check the division level."
            divisions = elements.InputDialog(windowName="Check Divisions", textValue=str(divisions), message=message)
            try:
                self.properties.maxDivisionsInt.value = int(divisions)
            except:
                self.compactWidget.maxDivisionsInt.clearFocus()
                self.properties.maxDivisionsInt.value = self.oldDivisions
                self.updateFromProperties()
                return
        self.oldDivisions = self.properties.maxDivisionsInt.value
        self.setAttrsDisplacement()

    def setAttrsDisplacement(self):
        """Sets the attributes on the displacement network"""
        attrDict = dict()
        attrDict[DISP_ATTR_SCALE] = self.properties.scaleFloat.value
        attrDict[DISP_ATTR_AUTOBUMP] = self.properties.autoBumpCheckBox.value
        attrDict[DISP_ATTR_IMAGEPATH] = self.properties.imagePathTxt.value
        attrDict[DISP_ATTR_DIVISIONS] = self.properties.maxDivisionsInt.value
        attrDict[DISP_ATTR_BOUNDS] = self.properties.boundsFloat.value
        attrDict[DISP_ATTR_TYPE] = DISP_TYPE[self.properties.dispTypeCombo.value]
        shadingGroup = self.getShadingGroupFromShader()
        if not shadingGroup:  # no shading group so bail
            return
        displacementmulti.setDisplacementNetworkAttrsNodes([shadingGroup],
                                                           attrDict,
                                                           self.properties.rendererIconMenu.value)

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidgetmaya.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def createDisplacement(self):
        """Create Displacement
        """
        renderer = self.properties.rendererIconMenu.value
        recreated = displacementmulti.deleteDisplacementNetworkSelected(message=False)
        if not elements.checkRenderLoaded(renderer):  # The renderer is not loaded open MessageBox_ok window
            return
        displaceType = DISP_METHODS[self.properties.dispTypeCombo.value]
        if displaceType == DISP_METHODS[0]:  # "Vector"
            displaceType = "VDM"
        else:  # "Height"
            # displaceType = "height"
            om2.MGlobal.displayWarning("Height B&W Displacement Type is not supported in this interface yet")
            return
        tangentType = DISP_TYPE[self.properties.dispMethodCombo.value]
        if tangentType == DISP_TYPE[0]:  # "Tangent"
            tangentType = "tangent"
        else:  # "Object"
            tangentType = "object"
        shadingGroup = self.getShadingGroupFromShader()
        if not shadingGroup:  # no shading group so bail
            om2.MGlobal.displayWarning("No Shading Group found, please select objects with a shader and shading group.")
            return
        displacementmulti.createDisplacementNodes([shadingGroup],
                                                  renderer,
                                                  imagePath=self.properties.imagePathTxt.value,
                                                  displacementType=displaceType,
                                                  tangentType=tangentType,
                                                  autoBump=self.properties.autoBumpCheckBox.value,
                                                  maxDivisions=self.properties.maxDivisionsInt.value,
                                                  scaleMultiplier=self.properties.scaleFloat.value,
                                                  recreated=recreated,
                                                  bounds=self.properties.boundsFloat.value)
        self.updateUIFromSelection()  # update GUI from current in scene selection

    @toolsetwidgetmaya.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def deleteDisplacement(self):
        """Deletes the displacement related to selected object/s"""
        shadingGroup = self.getShadingGroupFromShader()
        if not shadingGroup:  # no shading group so bail
            return
        displacementmulti.deleteDisplacementNetworkNodes([shadingGroup])
        self.updateUIFromSelection()  # Update GUI from current in scene selection

    @toolsetwidgetmaya.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def deleteBrokenDisplacementAll(self):
        """Deletes all broken displacement networks in the scene"""
        displacementmulti.deleteBrokenDisplacementAll()
        self.updateUIFromSelection()  # Update GUI from current in scene selection

    # ------------------
    # SELECT
    # ------------------

    @toolsetwidgetmaya.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def selectNode(self, nodeKey):
        """From a node key select the mesh in the scene:

        If nodeKey equals "network" then select the netowrk node itself

        :param nodeKey: The dictionary key named the same as the network attribute name for the node
        :type nodeKey: str
        """
        selNetworkNode = False
        shadingGroup = self.getShadingGroupFromShader()
        if not shadingGroup:  # no shading group so bail
            return
        if nodeKey == NW_DISPLACE_NODE:
            selNetworkNode = True
        displacementmulti.selectNode(shadingGroup, nodeKey=nodeKey, selectNetworkNode=selNetworkNode)

    @toolsetwidgetmaya.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def selectShader(self):
        """Select the shader in the scene if it exists"""
        shader = self.properties.activeShader.value
        displacementmulti.selectShader(shader)

    def resetAttrsDefaults(self):
        """Resets selected UI elements to the default values, does not reset the imagePath or active or shader states
        """
        self.properties.dispMethodCombo.value = 0
        self.properties.dispTypeCombo.value = 0
        self.properties.maxDivisionsInt.value = 4
        self.oldDivisions = 4
        self.properties.scaleFloat.value = 1.0
        self.properties.boundsFloat.value = 0.2
        self.properties.autoBumpCheckBox.value = False
        self.updateFromProperties()
        om2.MGlobal.displayInfo("Settings Reset")

    def enableDisplacement(self, action=None):
        """Will enable or disable the displacement network

        Called from the checkbox action on the dots menu

        :param action: The menu action as an object, will query and set the checked state of the checkbox action
        :type action: object
        """
        shadingGroup = self.getShadingGroupFromShader()
        self.setupEnabled = action.isChecked()
        if not shadingGroup:  # no shading group so bail
            return
        displacementmulti.enableDisplacementSG(shadingGroup,
                                               self.properties.rendererIconMenu.value,
                                               enableValue=self.setupEnabled)
        action.setChecked(self.setupEnabled)
        self.updateFromProperties()

    def enableDisplacementAll(self, enable=1):
        """Enables or disables all displacement networks in the scene"""
        displacementmulti.enableDisableAll(self.properties.rendererIconMenu.value, enable)
        self.updateUIFromSelection()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        # Apply displacement
        self.compactWidget.createDisplacementBtn.clicked.connect(self.createDisplacement)
        # Delete displacement
        self.compactWidget.deleteDisplacementBtn.clicked.connect(self.deleteDisplacement)
        # Change renderer
        self.compactWidget.rendererIconMenu.actionTriggered.connect(self.global_changeRenderer)
        # Browse Image browseImage
        self.compactWidget.browseBtn.clicked.connect(self.browseImage)
        self.selectionCallbacks.callback.connect(self.selectionChanged)  # monitor selection
        self.toolsetActivated.connect(self.startSelectionCallback)
        self.toolsetDeactivated.connect(self.stopSelectionCallback)
        # Attribute changes
        self.compactWidget.dispTypeCombo.currentIndexChanged.connect(self.setAttrsDisplacement)
        self.compactWidget.maxDivisionsInt.textModified.connect(self.setMaxDisplacement)
        self.compactWidget.scaleFloat.textModified.connect(self.setAttrsDisplacement)
        self.compactWidget.boundsFloat.textModified.connect(self.setAttrsDisplacement)
        self.compactWidget.imagePathTxt.textModified.connect(self.setAttrsDisplacement)
        self.compactWidget.autoBumpCheckBox.stateChanged.connect(self.setAttrsDisplacement)
        # Dots Menu
        self.compactWidget.dotsMenu.resetSettings.connect(self.resetAttrsDefaults)
        self.compactWidget.dotsMenu.displacementEnabled.connect(self.enableDisplacement)
        self.compactWidget.dotsMenu.enableAll.connect(partial(self.enableDisplacementAll, enable=1))
        self.compactWidget.dotsMenu.disableAll.connect(partial(self.enableDisplacementAll, enable=0))
        self.compactWidget.dotsMenu.selectDisplacement.connect(partial(self.selectNode, NW_DISPLACE_NODE_ATTR))
        self.compactWidget.dotsMenu.selectMeshes.connect(partial(self.selectNode, NW_DISPLACE_MESH_ATTR))
        self.compactWidget.dotsMenu.selectShader.connect(self.selectShader)
        self.compactWidget.dotsMenu.selectShadingGroup.connect(partial(self.selectNode, NW_DISPLACE_SG_ATTR))
        self.compactWidget.dotsMenu.selectTextureNode.connect(partial(self.selectNode, NW_DISPLACE_FILE_ATTR))
        self.compactWidget.dotsMenu.selectNetwork.connect(partial(self.selectNode, NW_DISPLACE_NODE))
        self.compactWidget.dotsMenu.deleteBroken.connect(self.deleteBrokenDisplacementAll)



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
        # Active Displacement ----------------------------------------
        toolTip = "Displacement is assigned to the shader's shading group \n" \
                  "To change, select any node in a displacement network or the affected meshes."
        self.activeShader = elements.StringEdit(label="Shader",
                                                editText=DFLT_SHADER,
                                                labelRatio=12,
                                                editRatio=20,
                                                toolTip=toolTip)
        toolTip = "`On`: The shader has a displacement network.  \n" \
                  "`Off`: The shader has no displacement network`"
        self.activeDisplacementTxt = elements.StringEdit(label="Active",
                                                         editText=DFLT_ACTIVE,
                                                         labelRatio=10,
                                                         editRatio=24,
                                                         toolTip=toolTip)
        self.activeShader.edit.setDisabled(True)
        self.activeDisplacementTxt.edit.setDisabled(True)
        # Dots Menu -------------------------------------------
        self.dotsMenu = DotsMenu()
        # Displace Method Combo ---------------------------------------
        toolTip = "Displacement Method \n" \
                  " 1. Vector: A colored vector displacement map, is more accurate \n" \
                  " 2. Height B&W: A black and white map white is easier to understand, up/down \n" \
                  "Note: Black & White is not yet supported"
        self.dispMethodCombo = elements.ComboBoxRegular(label="Method",
                                                        items=DISP_METHODS,
                                                        toolTip=toolTip,
                                                        setIndex=0,
                                                        labelRatio=12,
                                                        boxRatio=20)
        # Displacement Type Combo ---------------------------------------
        toolTip = "Displacement Type \n" \
                  " 1. Tangent: Displacement is projected relative to the normals/surface direction, most common. \n" \
                  " 2. Object: Displacement is projected from object coordinates"
        self.dispTypeCombo = elements.ComboBoxRegular(label="Type",
                                                      items=DISP_TYPE,
                                                      toolTip=toolTip,
                                                      setIndex=DFLT_TYPE,
                                                      labelRatio=8,
                                                      boxRatio=26)
        # Divisions String Edit -----------------------------------------------------
        toolTip = "The maximum amount of subdivisions that will render. (Arnold, Redshift)\n" \
                  "Note for each level the mesh is multiplied by four times the polygons \n" \
                  "High values will get very heavy and can crash or hang.\n\n" \
                  "Arnold Note:  Arnold adds the viewport SubD setting to the division value, \n" \
                  "so if subD is on an Arnold object take two from the value. Or turn viewport \n" \
                  "SubDs off."
        self.maxDivisionsInt = elements.IntEdit(label="Divisions",
                                                   editText=DFLT_DIVISIONS,
                                                   toolTip=toolTip,
                                                   labelRatio=12,
                                                   editRatio=20)
        # Bounds String Edit -----------------------------------------------------
        toolTip = "If clipping occurs in the displacement bounds may be too low. \n" \
                  "Increase the displacement bounds until the clipping no longer occurs. \n" \
                  "This value refers to cms (or Maya units) if the object is scaled to one."
        self.boundsFloat = elements.FloatEdit(label="Bounds",
                                               editText=DFLT_BOUNDS,
                                               toolTip=toolTip,
                                               labelRatio=12,
                                               editRatio=20)
        # Scale String Edit -----------------------------------------------------
        toolTip = "The scale multiplier of the displacement"
        self.scaleFloat = elements.FloatEdit(label="Scale",
                                              editText=DFLT_SCALE,
                                              toolTip=toolTip,
                                              labelRatio=12,
                                              editRatio=20)
        # Auto Bump Checkbox -----------------------------------------------------
        toolTip = "Will convert fine detail into a bump map rather than polygonal detail. (Redshift & Arnold)"
        self.autoBumpLabel = elements.Label(text="Auto Bump",
                                            toolTip=toolTip)
        self.autoBumpCheckBox = elements.CheckBox("",
                                                  checked=DFLT_AUTOBUMP,
                                                  toolTip=toolTip)
        # Displacement Image Location --------------------------------------
        toolTip = "The path of the displacement map"
        self.imagePathTxt = elements.StringEdit("Image Path",
                                                editText=DFLT_IMAGEPATH,
                                                labelRatio=1,
                                                editRatio=4,
                                                toolTip=toolTip)
        toolTip = "Browse to load a displacement image"
        self.browseBtn = elements.styledButton("...",
                                               toolTip=toolTip,
                                               style=uic.BTN_DEFAULT)
        # Create Displacement Btn --------------------------------------------
        toolTip = "Creates displacement on the objects with the current shader \n" \
                  " 1. Browse to the Image Path displacement file \n" \
                  " 2. Select an object or shader or shading group \n" \
                  " 2. Create Displacement \n" \
                  "All objects with the shader will be affected."
        self.createDisplacementBtn = elements.styledButton("Create Displacement",
                                                           icon="displacement",
                                                           toolTip=toolTip,
                                                           style=uic.BTN_DEFAULT)
        # Delete Displacement Btn --------------------------------------------
        toolTip = "Deletes the displacement network associated with a selected object. \n" \
                  "Selected object can be any mesh or node in the displacement network"
        self.deleteDisplacementBtn = elements.styledButton("",
                                                           icon="trash",
                                                           toolTip=toolTip,
                                                           style=uic.BTN_DEFAULT)
        # Renderer Button --------------------------------------
        toolTip = "Change the Renderer to Arnold, Redshift or Renderman"
        self.rendererIconMenu = elements.iconMenuButtonCombo(DFLT_RNDR_MODES,
                                                             self.properties.rendererIconMenu.value,
                                                             toolTip=toolTip)


class DotsMenu(IconMenuButton):
    menuIcon = "menudots"
    resetSettings = QtCore.Signal()

    displacementEnabled = QtCore.Signal(object)
    enableAll = QtCore.Signal()
    disableAll = QtCore.Signal()

    selectDisplacement = QtCore.Signal()
    selectMeshes = QtCore.Signal()
    selectShader = QtCore.Signal()
    selectShadingGroup = QtCore.Signal()
    selectTextureNode = QtCore.Signal()
    selectNetwork = QtCore.Signal()

    deleteBroken = QtCore.Signal()

    def __init__(self, parent=None, networkEnabled=False):
        """
        """
        super(DotsMenu, self).__init__(parent=parent)
        self.networkEnabled = networkEnabled
        iconColor = THEME_PREFS.ICON_PRIMARY_COLOR
        self.setIconByName(self.menuIcon, size=16, colors=iconColor)
        self.setMenuAlign(QtCore.Qt.AlignRight)
        self.setToolTip("File menu. Displacement")
        self.disableActionList = list()
        # Build the static menu
        # Reset To Defaults --------------------------------------
        reloadIcon = iconlib.iconColorized("reload2", utils.dpiScale(16))
        self.addAction("Reset Settings", connect=lambda: self.resetSettings.emit(), icon=reloadIcon)
        self.addSeparator()
        # Enable Network --------------------------------------
        self.enabledAction = self.addAction("Network Enabled",
                                            connect=lambda x: self.displacementEnabled.emit(x),
                                            checkable=True,
                                            checked=self.networkEnabled)
        self.disableActionList.append(self.enabledAction)
        enableIcon = iconlib.iconColorized("on", utils.dpiScale(16))
        self.addAction("Enable All Scene", connect=lambda: self.enableAll.emit(), icon=enableIcon)
        disableIcon = iconlib.iconColorized("off", utils.dpiScale(16))
        self.addAction("Disable All Scene", connect=lambda: self.disableAll.emit(), icon=disableIcon)
        self.addSeparator()
        # Select --------------------------------------
        cursorIcon = iconlib.iconColorized("cursorSelect", utils.dpiScale(16))
        self.disableActionList.append(
            self.addAction("Select Displacement Node", connect=lambda: self.selectDisplacement.emit(), icon=cursorIcon))
        self.disableActionList.append(
            self.addAction("Select Meshes", connect=lambda: self.selectMeshes.emit(), icon=cursorIcon))
        self.disableActionList.append(
            self.addAction("Select Shader", connect=lambda: self.selectShader.emit(), icon=cursorIcon))
        self.disableActionList.append(
            self.addAction("Select Shading Group", connect=lambda: self.selectShadingGroup.emit(), icon=cursorIcon))
        self.disableActionList.append(
            self.addAction("Select Texture Node", connect=lambda: self.selectTextureNode.emit(), icon=cursorIcon))
        self.disableActionList.append(
            self.addAction("Select Network Node", connect=lambda: self.selectNetwork.emit(), icon=cursorIcon))
        self.addSeparator()
        # Clean --------------------------------------
        deleteIcon = iconlib.iconColorized("trash", utils.dpiScale(16))
        self.addAction("Delete Broken Networks", connect=lambda: self.deleteBroken.emit(), icon=deleteIcon)


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
        contentsLayout = elements.vBoxLayout(parent=parent,
                                             margins=(uic.WINSIDEPAD, uic.LRGPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                             spacing=uic.SLRG)
        # Active Dots Layout ---------------------------------------
        activeDotsLayout = elements.hBoxLayout()
        activeDotsLayout.addWidget(self.activeDisplacementTxt, 6)
        activeDotsLayout.addWidget(self.dotsMenu, 1)
        # Shader Active Layout ---------------------------------------
        shaderActiveLayout = elements.hBoxLayout()
        shaderActiveLayout.addWidget(self.activeShader, 1)
        shaderActiveLayout.addLayout(activeDotsLayout, 1)
        # Top Combo Layout ---------------------------------------
        topComboLayout = elements.hBoxLayout(margins=(0, 0, 0, 0),
                                             spacing=uic.SREG)
        topComboLayout.addWidget(self.dispMethodCombo, 1)
        topComboLayout.addWidget(self.dispTypeCombo, 1)
        # Name Layout ---------------------------------------
        nameMainLayout = elements.hBoxLayout(margins=(0, 0, 0, 0),
                                             spacing=uic.SREG)
        nameMainLayout.addWidget(self.maxDivisionsInt, 1)  # maxDivisions will be hidden if Renderman
        nameMainLayout.addWidget(self.scaleFloat, 1)
        # Autobump Layout ---------------------------------------
        autobumpLayout = elements.hBoxLayout()
        autobumpLayout.addWidget(self.autoBumpLabel, 12)
        autobumpLayout.addWidget(self.autoBumpCheckBox, 20)
        # Bounds Autobump Layout ---------------------------------------
        boundsLayout = elements.hBoxLayout()
        boundsLayout.addWidget(self.boundsFloat, 1)
        boundsLayout.addLayout(autobumpLayout, 1)
        # Btn Layout ---------------------------------------
        btnLayout = elements.hBoxLayout()
        btnLayout.addWidget(self.createDisplacementBtn, 9)
        btnLayout.addWidget(self.deleteDisplacementBtn, 1)
        btnLayout.addWidget(self.rendererIconMenu, 1)
        # Path Browse Layout ---------------------------------------
        pathLayout = elements.hBoxLayout()
        pathLayout.addWidget(self.imagePathTxt, 9)
        pathLayout.addWidget(self.browseBtn, 1)
        # Add To Main Layout ---------------------------------------
        contentsLayout.addLayout(shaderActiveLayout)
        contentsLayout.addLayout(topComboLayout)
        contentsLayout.addLayout(nameMainLayout)
        contentsLayout.addLayout(boundsLayout)
        contentsLayout.addLayout(pathLayout)
        contentsLayout.addLayout(btnLayout)
