import locale

from Qt import QtWidgets

from maya import cmds
from maya.api import OpenMaya as om2


from zoo.libs.maya import zapi

from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya


from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.maya.cmds.general import undodecorator

from zoo.preferences.core import preference
from zoo.preferences import preferencesconstants as pc
from zoo.apps.toolsetsui import toolsetui, toolsetcallbacks

from zoo.libs.maya.cmds.objutils import namehandling, filtertypes, selection

from zoo.libs.maya.cmds.shaders import shaderutils, shadermultirenderer as shdmult
from zoo.libs.maya.cmds.renderer import rendererload
from zoo.libs.maya.cmds.renderer.rendererconstants import RENDERER_SUFFIX_DICT

THEME_PREFS = preference.interface("core_interface")

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1
DFLT_RNDR_MODES = [("arnold", "Arnold"), ("redshift", "Redshift"), ("renderman", "Renderman")]
SHADER_TYPES = ["Standard IOR"]
SHADER_PRESETS = ["Presets...", "Gold", "Car Paint", "Shiny Plastic", "Rough Plastic"]
MAYA_DEFAULT_SHADER_COLOR = (0.735, 0.735, 0.735)  # SRGB float
MAYA_DEFAULT_SPECULAR_COLOR = (0.0, 0.0, 0.0)  # SRGB float
MAYA_DEFAULT_COAT_COLOR = (0.0, 0.0, 0.0)  # SRGB float

DEFAULT_SHADER_NAME = "shader_01"

class ShaderManager(toolsetwidgetmaya.ToolsetWidgetMaya):
    """Large tool for managing and assigning shaders
    """
    id = "shaderManager"
    uiData = {"label": "Shader Manager",
              "icon": "shaderBall",
              "tooltip": "Shader Manager for creating and managing the main shaders in Arnold Redshift and Renderman",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-shader-manager/"
              }

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run"""
        self.toolsetWidget = self  # needed for callback decorators
        self.generalSettingsPrefsData = preference.findSetting(pc.RELATIVE_PREFS_FILE, None)  # renderer in general pref
        self.properties.rendererIconMenu.value = self.generalSettingsPrefsData[pc.PREFS_KEY_RENDERER]
        self.undoStateOpen = False
        self.copiedAttributes = dict()
        self.copiedShaderName = ""
        self.buildPresets()  # builds the preset dictionary self.presetDict
        self.uiShaderName = ""

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget(), self.initAdvancedWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        parent = QtWidgets.QWidget(parent=self)
        self.compactWidget = GuiCompact(parent=parent, properties=self.properties, toolsetWidget=self,
                                        presetShaderList=self.presetShaderList)
        return parent

    def initAdvancedWidget(self):
        """Builds the Advanced GUI (self.advancedWidget) """
        parent = QtWidgets.QWidget(parent=self)
        self.advancedWidget = GuiAdvanced(parent=parent, properties=self.properties, toolsetWidget=self,
                                          presetShaderList=self.presetShaderList)
        return parent

    def postContentSetup(self):
        """Last of the initialize code"""
        self.uiModeList()
        self.uiConnections()

        self.oldShaderName = (shdmult.getFirstSupportedShaderSelected())[0]
        self.properties.shaderNameComboE.value = 0  # sets the shaderNameComboE to be the first name found
        self.updateNameComboE(updateCombo=True)
        self.shaderToGui(self.currentShader())
        if cmds.ls(selection=True):
            self.shaderToGuiSel()
        self.startSelectionCallback()  # start selection callback

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
        return [{"name": "rendererIconMenu", "label": "", "value": "Arnold"}]

    def updateFromProperties(self):
        """ Runs update properties from the base class.

        Widgets will auto update from self.properties if linked via:

            self.linkProperty(widget, "propertyKey")
            or
            self.toolsetWidget.linkProperty(widget, "propertyKey")

        Add code after super() useful for changes such as forcing UI decimal places
        or manually adding unsupported widgets
        """
        super(ShaderManager, self).updateFromProperties()

    # ------------------
    # SHADER PRESETS CLICKS
    # ------------------

    def buildPresets(self):
        """Shader presets as combo
        """
        import os
        from zoo.libs.utils import filesystem
        path = os.path.abspath(__file__)
        dir_path = os.path.dirname(path)
        jsonPath = os.path.join(dir_path, "shaderPresets.json")
        self.presetDict = filesystem.loadJson(jsonPath)
        self.presetShaderList = list()
        for key in self.presetDict:
            self.presetShaderList.append(str(key))
        self.presetShaderList.sort(key=str.lower)  # alphabetical
        self.presetShaderList.insert(0, "Presets...")

    # ------------------
    # RIGHT CLICKS
    # ------------------

    def actions(self):
        """Right click menu and actions
        """
        return []

    # ------------------
    # CALLBACKS
    # ------------------

    def selectionChanged(self, selection):
        """Run when the callback selection changes, updates the GUI if an object is selected

        Callbacks are handled automatically by toolsetcallbacks.py which this class inherits"""
        if not selection:  # then still may be a component face selection TODO add this to internal callbacks maybe?
            selection = cmds.ls(selection=True)
            if not selection:  # then nothing is selected
                return
        self.shaderToGuiSel()  # try to update the GUI

    # ------------------
    # UPDATE COMBO
    # ------------------

    def enterEvent(self, event):
        """When the cursor enters the UI update it"""
        # note known issue entering Event can cause a double shaderGUI combo update, difficult to solve so leaving.
        self.updateNameComboE(updateCombo=True)  # auto update lists
        self.shaderToGui(self.currentShader())

    def shaderComboEChanged(self, event):
        """ On camera combo changed

        # Note will cause a double gui and combo update in most cases (short lists) because of enterEvent

        :type event: zoo.libs.pyqt.extended.combobox.comboeditwidget.IndexChangedEvent
        """
        # Update the GUI and self.uiShaderName to the new shader --------------------------
        self.uiShaderName = event.items[0].text()  # the new text after changing
        if self.currentShader():  # safe check zapi for self.uiShaderName, then update UI
            self.shaderToGui(self.currentShader(), updateCombo=False)  # don't update combo potential crash loops
        # Do Primary or Secondary Function ------------------------------------------------
        if event.menuButton == event.Primary:
            self.changeToShader()
        elif event.menuButton == event.Secondary:
            self.selectShader()

    def alphabetizeLists(self, list):
        locale.setlocale(locale.LC_ALL, '')  # needed for sorting unicode
        if list:
            list = sorted(list, cmp=locale.strcoll)  # alphabetalize
        return list

    def updateNameComboE(self, updateCombo=True, setName=None):
        """Updates the rename combo edit with option to set the current combo edit index with the setname (str)

        :param updateCombo: Will update the rename combo edit if it needs updating
        :type updateCombo: bool
        :param setName: Set this name as the current index in the combo edit, None uses self.currentShader()
        :type setName: str
        """
        shadersCombinedList = list()
        nodeCombinedList = list()
        # Builds allShaders and shadersSelected lists ----------------------------------------------
        shadersAll = self.alphabetizeLists(shdmult.getShadersSceneRenderer(self.properties.rendererIconMenu.value))
        shadersSelected = self.alphabetizeLists(shaderutils.getShadersSelected(reportMessage=False))

        # Build shadersCombinedList which is used by the rename combo edit -------------------------
        if shadersSelected:
            shadersCombinedList += shadersSelected + [elements.ComboEditWidget.SeparatorString]
            nodeCombinedList += list(zapi.nodesByNames(shadersSelected)) + [None]
        if shadersAll:
            shadersCombinedList += shadersAll
            nodeCombinedList += list(zapi.nodesByNames(shadersAll))
        else:
            shadersCombinedList = ["No {} Shaders Found".format(self.properties.rendererIconMenu.value)]
            nodeCombinedList = [None]

        # Updates the Rename Combo Edit -----------------------------------------------------------
        if updateCombo:
            combo = self.currentWidget().shaderNameComboE
            if setName is None:
                combo.updateList(shadersCombinedList, dataList=nodeCombinedList, setName=self.currentShader())
                self.uiShaderName = combo.currentText()
            else:
                combo.updateList(shadersCombinedList, dataList=nodeCombinedList, setName=setName)
                self.uiShaderName = combo.currentText()
            self.properties.shaderNameComboE.value = combo.currentIndexInt()  # must update the combo

    def renameShaderEvent(self, event):
        """ Rename Cam event

        :param event:
        :type event: zoo.libs.pyqt.extended.combobox.comboeditwidget.EditChangedEvent
        """
        if event.before == event.after:  # Seems to trigger twice weird can't figure
            return
        if event.after == "":
            om2.MGlobal.displayWarning("Cannot rename with no text")
            return
        newName = namehandling.safeRename(self.currentShader(), event.after)  # current shader should be more accurate
        self.updateNameComboE(updateCombo=True, setName=newName)  # updates all the lists new name
        om2.MGlobal.displayInfo("Success: Shader `{}` renamed to `{}`".format(self.currentShader(), event.after))

    # ------------------------------------
    # RENDERER - AND SEND/RECEIVE ALL TOOLSETS
    # ------------------------------------

    def global_changeRenderer(self):
        """Updates all GUIs with the current renderer"""
        self.generalSettingsPrefsData = preference.findSetting(pc.RELATIVE_PREFS_FILE, None)  # refresh data
        toolsets = toolsetui.toolsets(attr="global_receiveRendererChange")
        self.generalSettingsPrefsData = elements.globalChangeRenderer(self.properties.rendererIconMenu.value,
                                                                      toolsets,
                                                                      self.generalSettingsPrefsData,
                                                                      pc.PREFS_KEY_RENDERER)

    def global_receiveRendererChange(self, renderer):
        """Receives from other GUIs, changes the renderer when it is changed"""
        self.properties.rendererIconMenu.value = renderer
        self.updateFromProperties()

    def global_receiveShaderUpdated(self):
        """Receives from other GUIs, changes the renderer when it is changed"""
        self.shaderToGuiSel()

    # ------------------------------------
    # COPY PASTE - AND SEND/RECEIVE ALL TOOLSETS
    # ------------------------------------

    def global_sendCopyShader(self):
        """Updates all GUIs with the copied shader"""
        toolsets = toolsetui.toolsets(attr="global_receiveCopiedShader")
        for tool in toolsets:
            tool.global_receiveCopiedShader(self.copiedShaderName, self.copiedAttributes)

    def global_receiveCopiedShader(self, copiedShaderName, copiedAttributes):
        """Receives the copied shader from other GUIs"""
        self.copiedShaderName = copiedShaderName
        self.copiedAttributes = copiedAttributes

    # ------------------------------------
    # SLIDER UNDO CHUNKS
    # ------------------------------------

    def openUndoChunk(self):
        """Opens the Maya undo chunk, on sliderPressed"""
        super(ShaderManager, self).openUndoChunk()
        self.undoStateOpen = True

    def closeUndoChunk(self):
        """Opens the Maya undo chunk, on sliderReleased"""
        super(ShaderManager, self).openUndoChunk()
        self.undoStateOpen = False

    # ------------------
    # LOGIC PULL
    # ------------------

    def currentShader(self):
        """Returns the current shader with a few checks, such as falling back on zapi"""
        if cmds.objExists(self.uiShaderName):
            return self.uiShaderName  # all is well
        # Node doesn't exist so fallback on the zapi node stored in the rename combo edit widget
        node = self.currentWidget().shaderNameComboE.currentData()  # zapi node
        if node:
            try:  # new scene can destroy zapi nodes
                if node.exists():
                    self.uiShaderName = node.fullPathName()
                    return self.uiShaderName  # name was probably updated
            except AttributeError:
                pass
        self.uiShaderName = ""  # Node no longer exists
        return self.uiShaderName  # shader was probably deleted somehow


    def disableEnableAttr(self, genKey, enable=True):
        """Disables or enables a widget based off it's key dict for both UIs advanced and compact.

        Some widgets are only in advanced mode.

        :param genKey: a generic key from shdmult.GEN_KEY_LIST
        :type genKey: str
        :param enable: Enable the widget True or disable with False
        :type enable: bool
        """
        if genKey == shdmult.DIFFUSEWEIGHT:
            self.advancedWidget.diffuseWeightFloatSldr.setEnabled(enable)
        if genKey == shdmult.DIFFUSE:
            for uiMode in self.uiInstanceList:
                uiMode.diffuseColorSldr.setEnabled(enable)
        if genKey == shdmult.SPECWEIGHT:
            self.advancedWidget.specularWeightFloatSldr.setEnabled(enable)
        if genKey == shdmult.SPECCOLOR:
            for uiMode in self.uiInstanceList:
                uiMode.specularColorSldr.setEnabled(enable)
        if genKey == shdmult.SPECROUGHNESS:
            for uiMode in self.uiInstanceList:
                uiMode.specularRoughFloatSldr.setEnabled(enable)
        if genKey == shdmult.SPECIOR:
            for uiMode in self.uiInstanceList:
                uiMode.iorFloatSldr.setEnabled(enable)
        if genKey == shdmult.COATWEIGHT:
            self.advancedWidget.clearCoatWeightFloatSldr.setEnabled(enable)
        if genKey == shdmult.COATCOLOR:
            self.advancedWidget.clearCoatColorSldr.setEnabled(enable)
        if genKey == shdmult.COATROUGHNESS:
            self.advancedWidget.clearCoatRoughFoatSldr.setEnabled(enable)
        if genKey == shdmult.COATIOR:
            self.advancedWidget.clearCoatIorFloatSldr.setEnabled(enable)

    def disableEnableSliders(self, textureList):
        for genKey in shdmult.GEN_KEY_LIST:  # All generic keys
            if genKey in textureList:
                self.disableEnableAttr(genKey, enable=False)
            else:
                self.disableEnableAttr(genKey, enable=True)

    def setGuiShaderDict(self, shaderAttributes):
        self.properties.diffuseColorSldr.value = shaderAttributes[shdmult.DIFFUSE]
        self.properties.diffuseWeightFloatSldr.value = round(shaderAttributes[shdmult.DIFFUSEWEIGHT], 3)
        self.properties.specularWeightFloatSldr.value = round(shaderAttributes[shdmult.SPECWEIGHT], 3)
        self.properties.specularColorSldr.value = shaderAttributes[shdmult.SPECCOLOR]
        self.properties.specularRoughFloatSldr.value = round(shaderAttributes[shdmult.SPECROUGHNESS], 3)
        self.properties.iorFloatSldr.value = round(shaderAttributes[shdmult.SPECIOR], 3)
        self.properties.clearCoatWeightFloatSldr.value = round(shaderAttributes[shdmult.COATWEIGHT], 3)
        self.properties.clearCoatColorSldr.value = shaderAttributes[shdmult.COATCOLOR]
        self.properties.clearCoatRoughFoatSldr.value = round(shaderAttributes[shdmult.COATROUGHNESS], 3)
        self.properties.clearCoatIorFloatSldr.value = round(shaderAttributes[shdmult.COATIOR], 3)
        self.updateFromProperties()

    def shaderToGui(self, shaderName, updateCombo=True, message=False):
        """From a shader name pull it into the GUI

        :param shaderName: A maya shader node name
        :type shaderName: str
        :param message: report the message to the user?
        :type message: bool
        """
        shaderAttributes = shdmult.getShaderAttributes(shaderName)
        if not shaderAttributes:
            return
        # Update GUI ----------------------------------------------------
        self.setGuiShaderDict(shaderAttributes)  # Sets and updates properties
        if updateCombo:
            self.updateNameComboE(updateCombo=updateCombo, setName=shaderName)
        # Disable Sliders on Textured slots ----------------------------
        textureList = shdmult.getShaderTexturedAttrs(shaderName, self.properties.rendererIconMenu.value)
        self.disableEnableSliders(textureList)
        if message:
            om2.MGlobal.displayInfo("Success: Shader UI Updated {}".format(self.currentWidget()))

    def shaderToGuiSel(self, message=False):
        """Pulls the shader info from the first selected shader found and pulls into the GUI
        """
        rendererLoaded = rendererload.getRendererIsLoaded(self.properties.rendererIconMenu.value)
        if not rendererLoaded:
            return
        shaderAttributes, nameMatch = shdmult.getShaderSelected(shaderName=self.currentShader())
        if not shaderAttributes:  # no legit shaders found, message already warned
            return
        shaderName = str(self.currentShader())
        if not nameMatch:  # nameMatch is True if nothing selected and found the GUI name, so False pull the name
            shaderName = shaderutils.getShaderNameFromNodeSelected(removeSuffix=False)
            shaderAttributes = shdmult.getShaderAttributes(shaderName)  # get the attributes again, order is important
        self.updateNameComboE(updateCombo=True, setName=shaderName)  # New name update and recreate lists
        if not shaderAttributes:  # the dictionary is empty possibly an unsupported shader
            return
        if not shdmult.checkShaderRendererMatch(shaderName,
                                                self.properties.rendererIconMenu.value):  # could be incorrect renderer
            return
        # Update GUI
        self.setGuiShaderDict(shaderAttributes)  # Sets and updates properties
        # Disable Sliders on Textured slots
        textureList = shdmult.getShaderTexturedAttrs(shaderName, self.properties.rendererIconMenu.value)
        self.disableEnableSliders(textureList)

        if message:
            om2.MGlobal.displayInfo("Success: Shader UI Updated")

    # ------------------
    # LOGIC CREATE & DELETE
    # ------------------

    @undodecorator.undoDecorator
    def createShaderUndo(self):
        """Creates a shader with one undo"""
        self.createShader()

    @toolsetcallbacks.ignoreCallbackDecorator
    def createShader(self):
        """Create Shader
        """
        currRenderer = self.properties.rendererIconMenu.value
        shaderType = shdmult.RENDERERSHADERS[currRenderer][0]
        if not rendererload.getRendererIsLoaded(currRenderer):  # the renderer is not loaded open window
            if not elements.checkRenderLoaded(self.properties.rendererIconMenu.value):
                return
        # Build unique name ----------------------------------------
        uniqueShaderName = namehandling.getUniqueNameSuffix(DEFAULT_SHADER_NAME,
                                                            RENDERER_SUFFIX_DICT[self.properties.rendererIconMenu.value])
        # Create Set Shader -------------------------------------------------------
        uniqueShaderName = shdmult.createShaderTypeSelected(shaderType, shaderName=uniqueShaderName, message=True)
        # set the shader attributes
        self.setShader(uniqueShaderName, shaderType)
        # UI -------------------------------------------------------
        self.shaderToGui(uniqueShaderName)  # update the GUI (updates properties)
        self.updateNameComboE(updateCombo=True, setName=uniqueShaderName)  # recreates all lists and combo edit
        # Disable Sliders on Textured slots
        textureList = shdmult.getShaderTexturedAttrs(uniqueShaderName, currRenderer)
        self.disableEnableSliders(textureList)

    def deleteShader(self):
        """Deletes the shader in the UI from the scene"""
        if not self.currentShader():
            return
        shdmult.deleteShader(self.currentShader())
        self.uiShaderName = ""
        self.updateNameComboE()  # resets self.uiShaderName
        self.shaderToGui(self.uiShaderName)  # self.currentShader()

    # ------------------
    # PRESETS AND RESET
    # ------------------

    def presetChanged(self):
        """Change all attributes on the GUI and shader when the preset combo box is changed"""
        shaderName = self.presetShaderList[self.properties.shaderPresetsCombo.value]
        if shaderName == self.presetShaderList[0]:  # Ignore is the first entry "Presets..."
            return
        shaderAttributes = self.presetDict[shaderName]
        # Update GUI
        self.setGuiShaderDict(shaderAttributes)  # Sets and updates properties
        self.uiChangeApplyShader()

    def resetToPreset(self):
        """Reset the current shader attributes to the current preset
        If no preset is selected use the 'bright grey 1 matte' setting"""
        shaderName = self.presetShaderList[self.properties.shaderPresetsCombo.value]
        if shaderName == self.presetShaderList[0]:  # is "Presets..." so use matte
            shaderAttributes = self.presetDict[self.presetShaderList[1]]
        else:
            shaderAttributes = self.presetDict[shaderName]
        # Update GUI
        self.setGuiShaderDict(shaderAttributes)  # Sets and updates properties
        self.uiChangeApplyShader()

    # ------------------
    # LOGIC SELECT
    # ------------------

    @undodecorator.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def selectObjFacesFromShader(self):
        """Selects objects and faces assigned from a shader"""
        if self.currentShader():
            if cmds.objExists(self.currentShader()):
                shaderutils.selectMeshFaceFromShaderName(self.currentShader())

    @toolsetcallbacks.ignoreCallbackDecorator
    def selectShader(self):
        """Selects the active shader from the GUI"""
        if self.currentShader():
            if cmds.objExists(self.currentShader()):
                cmds.select(self.currentShader(), replace=True)

    @undodecorator.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def changeToShader(self, shaderOverride=""):
        """Changes to the GUI to match and assign the current shader
        """
        selObj = cmds.ls(selection=True)
        selGeo = list()
        if selObj:  # Filter just geometry
            meshObjs = filtertypes.filterTypeReturnTransforms(selObj, children=False, shapeType="mesh")
            nurbsObjs = filtertypes.filterTypeReturnTransforms(selObj, children=False, shapeType="nurbsSurface")
            faceSelection = selection.componentSelectionFilterType(selObj, selectType="faces")
            selGeo = meshObjs + nurbsObjs + faceSelection
        if not selGeo:
            return
        if not shaderOverride:
            shader = self.currentShader()
        else:
            shader = shaderOverride
        if not shader:
            return ""
        shaderutils.assignShader(selGeo, shader)
        return shader

    # ------------------
    # LOGIC TRANSFER COPY PASTE
    # ------------------

    def copyShader(self):
        """Copies the shader attributes and shader name"""
        if not self.currentShader():
            om2.MGlobal.displayWarning("No Shader found in GUI".format(self.copiedShaderName))
            return
        if not cmds.objExists(self.currentShader()):
            om2.MGlobal.displayWarning("Shader {} not found in scene".format(self.currentShader()))
            return
        self.copiedAttributes = self.shaderDict()
        self.copiedShaderName = str(self.currentShader())
        self.global_sendCopyShader()
        om2.MGlobal.displayInfo("Shader copied `{}`".format(self.copiedShaderName))

    @undodecorator.undoDecorator
    def pasteAttributes(self):
        """sets the copied shader attributes to the selected/active shader, but does not assign, the shader remains"""
        if not self.copiedAttributes:
            om2.MGlobal.displayWarning("Cannot paste as there is nothing in the clipboard.  Please copy a shader.")
            return
        # needs to get shader names of selected of type renderer
        shaderNames = shdmult.getShadersSelectedRenderer(self.properties.rendererIconMenu.value)
        shaderType = shdmult.RENDERERSHADERS[self.properties.rendererIconMenu.value][0]
        for shader in shaderNames:
            shdmult.setShaderAttrs(shader,
                                   shaderType,
                                   self.copiedAttributes,
                                   convertSrgbToLinear=True,
                                   reportMessage=True)
        # Update GUI
        self.setGuiShaderDict(self.copiedAttributes)  # Sets and updates properties
        om2.MGlobal.displayInfo("Shader attributes pasted to `{}`".format(shaderNames))

    def pasteAssign(self):
        """Assigns the copied shader (from the shader name) to the selected object/s or faces"""
        if not self.copiedShaderName:
            om2.MGlobal.displayWarning("Cannot paste as there is nothing in the clipboard.  Please copy a shader.")
            return
        if not cmds.objExists(self.copiedShaderName):
            om2.MGlobal.displayWarning("Shader `` no longer exists in the scene".format(self.copiedShaderName))
            return
        self.changeToShader(shaderOverride=self.copiedShaderName)
        self.shaderToGuiSel()  # updates the GUI
        om2.MGlobal.displayInfo("Shader assigned `{}`".format(self.copiedShaderName))

    @undodecorator.undoDecorator
    def transferAssign(self):
        """Assigns the shader from the first selected face or object to all other selected objects and faces"""
        success = shaderutils.transferAssignSelection()
        if not success:  # message already reported to user
            return
        om2.MGlobal.displayInfo("Shader assigned `{}`".format(self.currentShader()))

    # ------------------
    # LOGIC APPLY
    # ------------------

    def shaderDict(self):
        """Updates the UI to reflect the preset shader selection
        """
        shaderDict = {}
        shaderDict[shdmult.DIFFUSE] = self.properties.diffuseColorSldr.value
        shaderDict[shdmult.DIFFUSEWEIGHT] = self.properties.diffuseWeightFloatSldr.value
        shaderDict[shdmult.SPECWEIGHT] = self.properties.specularWeightFloatSldr.value
        shaderDict[shdmult.SPECCOLOR] = self.properties.specularColorSldr.value
        shaderDict[shdmult.SPECROUGHNESS] = self.properties.specularRoughFloatSldr.value
        shaderDict[shdmult.SPECIOR] = self.properties.iorFloatSldr.value
        shaderDict[shdmult.COATWEIGHT] = self.properties.clearCoatWeightFloatSldr.value
        shaderDict[shdmult.COATCOLOR] = self.properties.clearCoatColorSldr.value
        shaderDict[shdmult.COATROUGHNESS] = self.properties.clearCoatRoughFoatSldr.value
        shaderDict[shdmult.COATIOR] = self.properties.clearCoatIorFloatSldr.value
        return shaderDict

    @toolsetcallbacks.ignoreCallbackDecorator
    def setShader(self, shaderName, shaderType, message=True):
        """Sets the shader attributes after creation
        """
        # Get the shader attributes and assign them to a dict
        shaderDict = self.shaderDict()
        # set the shader attributes
        shdmult.setShaderAttrs(shaderName, shaderType, shaderDict, convertSrgbToLinear=True, reportMessage=message)

    def uiChangeApplyShader(self, value=None):
        """Apply UI settings to the current shader, manages the undo with self.undoStateOpen
        Auto detects if the slider is being pressed concerning the undo stack"""
        closeUndo = False
        if not self.undoStateOpen:  # open the undo state if it is not already open (slider hasn't been pressed)
            undodecorator.openUndoChunk()
            closeUndo = True
        shaderName = str(self.currentShader())
        if not shaderName:  # will be ""
            shaderName, shaderType = shdmult.getFirstSupportedShaderSelected()  # check auto selection
            if not shaderName:
                return
        if not cmds.objExists(shaderName):  # the name in the GUI does not exist
            shaderName, shaderType = shdmult.getFirstSupportedShaderSelected()  # check auto selection
            if not shaderName:
                return
        else:
            shaderType = shdmult.supportedShaderType(shaderName)
        self.setShader(shaderName, shaderType, message=False)
        if closeUndo:  # close the undo chunk (if slider hadn't been pressed)
            undodecorator.closeUndoChunk()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Widget GUI connections"""
        colSliderList = list()
        floatSliderList = list()

        self.displaySwitched.connect(self.shaderToGuiSel)

        self.toolsetActivated.connect(self.startSelectionCallback)
        self.toolsetDeactivated.connect(self.stopSelectionCallback)

        for widget in self.widgets():
            uiInstance = widget.children()[0]
            uiInstance.shaderNameComboE.itemRenamed.connect(self.renameShaderEvent)
            uiInstance.shaderNameComboE.itemChanged.connect(self.shaderComboEChanged)
            uiInstance.shaderNameComboE.aboutToShow.connect(self.updateNameComboE)
            uiInstance.shaderPresetsCombo.itemChanged.connect(self.presetChanged)
            uiInstance.createShaderBtn.clicked.connect(self.createShaderUndo)
            uiInstance.reloadShaderBtn.clicked.connect(self.resetToPreset)
            uiInstance.deleteShaderBtn.clicked.connect(self.deleteShader)
            uiInstance.copyShaderBtn.clicked.connect(self.copyShader)
            uiInstance.pasteShaderBtn.clicked.connect(self.pasteAssign)
            uiInstance.pasteAttrBtn.clicked.connect(self.pasteAttributes)
            uiInstance.transferShaderBtn.clicked.connect(self.transferAssign)
            uiInstance.selectShaderBtn.clicked.connect(self.selectShader)
            uiInstance.selectObjectsBtn.clicked.connect(self.selectObjFacesFromShader)
            uiInstance.rendererIconMenu.actionTriggered.connect(self.global_changeRenderer)
            colSliderList.append(uiInstance.diffuseColorSldr)
            colSliderList.append(uiInstance.specularColorSldr)
            floatSliderList.append(uiInstance.specularRoughFloatSldr)
            floatSliderList.append(uiInstance.iorFloatSldr)
        # GUI Change
        floatSliderList.append(self.advancedWidget.diffuseWeightFloatSldr)
        floatSliderList.append(self.advancedWidget.specularWeightFloatSldr)
        floatSliderList.append(self.advancedWidget.clearCoatWeightFloatSldr)
        colSliderList.append(self.advancedWidget.clearCoatColorSldr)
        floatSliderList.append(self.advancedWidget.clearCoatRoughFoatSldr)
        floatSliderList.append(self.advancedWidget.clearCoatIorFloatSldr)
        # Connect the float and color sliders correctly
        for colorSlider in colSliderList:
            colorSlider.colorSliderChanged.connect(self.uiChangeApplyShader)
            colorSlider.sliderPressed.connect(self.openUndoChunk)
            colorSlider.sliderReleased.connect(self.closeUndoChunk)
        for floatSlider in floatSliderList:
            floatSlider.floatSliderChanged.connect(self.uiChangeApplyShader)
            floatSlider.sliderPressed.connect(self.openUndoChunk)
            floatSlider.sliderReleased.connect(self.closeUndoChunk)
        # Callback methods
        self.selectionCallbacks.callback.connect(self.selectionChanged)  # monitor selection
        self.toolsetActivated.connect(self.startSelectionCallback)
        self.toolsetDeactivated.connect(self.stopSelectionCallback)


class GuiWidgets(QtWidgets.QWidget):
    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None, presetShaderList=None):
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
        # Shader Name Rename Combo edit -----------------------------------------------------
        toolTip = ""
        self.shaderNameComboE = elements.ComboEditRename(parent=self, label="Shader Name",
                                                         secondaryActive=True,
                                                         secondaryIcon="cursorSelect",
                                                         primaryTooltip="Set To",
                                                         secondaryTooltip="Select Only",
                                                         labelStretch=3, mainStretch=8,
                                                         toolTip=toolTip)
        # Shader Type Combo ---------------------------------------
        toolTip = "Select a shader Type \n" \
                  "- Standard IOR: Offline renderer, physically based shader type, full options \n" \
                  "- Metalness: Based off the Disney BRDF, or common games shader. Eg. Substance `PBR`"
        self.shaderTypeCombo = elements.ComboBoxRegular(label="",
                                                        items=SHADER_TYPES,
                                                        parent=parent,
                                                        toolTip=toolTip,
                                                        setIndex=0)
        # Shader Presets Combo ---------------------------------------
        toolTip = "Select a preset to set the current shader."
        self.shaderPresetsCombo = elements.ComboBoxRegular(label="",
                                                           items=presetShaderList,
                                                           parent=parent,
                                                           toolTip=toolTip,
                                                           setIndex=0)
        # Diffuse Color Slider ---------------------------------------
        toolTip = "Diffuse color, value in SRGB \n" \
                  "- The main color of the shader if not metal (IOR below 2) \n" \
                  "- Becomes black or very dark if metal (IOR above 4)"
        self.diffuseColorSldr = elements.MayaColorSlider(label="Diffuse Color",
                                                         color=MAYA_DEFAULT_SHADER_COLOR,
                                                         toolTip=toolTip)
        # Diffuse Color Slider ---------------------------------------
        toolTip = "Specular color, value in SRGB \n" \
                  "- Black if disabled, non reflective \n" \
                  "- White for most objects (IOR is set to 2 or below) \n" \
                  "- Becomes a color when shader is metal (IOR above 4)"
        self.specularColorSldr = elements.MayaColorSlider(label="Spec Color",
                                                          color=MAYA_DEFAULT_SPECULAR_COLOR,
                                                          toolTip=toolTip)
        # Specular Roughness Slider --------------------------------------------------------
        toolTip = "Specular Roughness \n" \
                  " 0.0 Shiny \n" \
                  " 0.6 Rough"
        self.specularRoughFloatSldr = elements.FloatSlider(label="Spec Rough",
                                                           defaultValue=0.2,
                                                           toolTip=toolTip,
                                                           decimalPlaces=3)
        # IOR Slider --------------------------------------------------------
        toolTip = "Incidence Of Refraction value, also Fresnel or Refractive Index. \n" \
                  "Although named `refractive` IOR also affects `specular reflection`. \n" \
                  " 1.0 Not Reflective or Refractive \n" \
                  " 1.3 Water \n" \
                  " 1.5 Most Objects, Plastics and Glass \n" \
                  " 2.0 Crystal \n" \
                  " 4.0 Dull Metal \n" \
                  " 12.0 Shiny Metal \n" \
                  " 20.0 Full Mirror"
        self.iorFloatSldr = elements.FloatSlider(label="IOR",
                                                 defaultValue=1.50,
                                                 toolTip=toolTip,
                                                 sliderMin=1.0,
                                                 sliderMax=20.0,
                                                 decimalPlaces=2,
                                                 sliderAccuracy=2000)
        # Create Main Button ---------------------------------------
        toolTip = "Creates a new shader on the selected object/s"
        self.createShaderBtn = elements.styledButton("Create",
                                                     "shaderBall",
                                                     parent,
                                                     toolTip,
                                                     style=uic.BTN_DEFAULT)
        # Transfer Shader Btn --------------------------------------------
        toolTip = "Transfer the current shader to another object \n" \
                  "- 1. Select two or more objects. \n" \
                  "- 2. The shader from the first object will be transferred to others."
        self.transferShaderBtn = elements.styledButton("Transfer", "transferShader",
                                                       toolTip=toolTip,
                                                       style=uic.BTN_DEFAULT)
        # Copy Shader Btn --------------------------------------------
        toolTip = "Copy the current shader settings to the clipboard"
        self.copyShaderBtn = elements.styledButton("Copy", "copyShader",
                                                   toolTip=toolTip,
                                                   style=uic.BTN_DEFAULT)
        # Paste Assign Shader Btn --------------------------------------------
        toolTip = "Paste the shader attribute settings from the clipboard \n" \
                  "Shader attribute settings will be pasted, the existing shader will remain."
        self.pasteAttrBtn = elements.styledButton("Paste", "pasteAttributes",
                                                  toolTip=toolTip,
                                                  style=uic.BTN_DEFAULT)
        # Paste Attribute Shader Btn --------------------------------------------
        toolTip = "Paste/Assign the shader from the clipboard \n" \
                  "Existing shader will be assigned to selected geometry"
        self.pasteShaderBtn = elements.styledButton("Paste", "pasteAssign",
                                                    toolTip=toolTip,
                                                    style=uic.BTN_DEFAULT)
        # Reset Shader Btn --------------------------------------------
        toolTip = "Reset the shader's attributes to the default or the current preset's values"
        self.reloadShaderBtn = elements.styledButton("", "reload2",
                                                     toolTip=toolTip,
                                                     style=uic.BTN_TRANSPARENT_BG)
        # Select Objects/Faces --------------------------------------------
        toolTip = "Select objects and or faces with this material"
        self.selectObjectsBtn = elements.styledButton("",
                                                      "selectObject",
                                                      self,
                                                      toolTip=toolTip,
                                                      style=uic.BTN_DEFAULT)
        # Select Shader Btn --------------------------------------------
        toolTip = "Select shader node / deselect geometry"
        self.selectShaderBtn = elements.styledButton("",
                                                     "selectShader",
                                                     self,
                                                     toolTip=toolTip,
                                                     style=uic.BTN_DEFAULT)
        # Delete Shader Btn --------------------------------------------
        toolTip = "Delete the active shader from the scene"
        self.deleteShaderBtn = elements.styledButton("",
                                                     "trash",
                                                     self,
                                                     toolTip=toolTip,
                                                     style=uic.BTN_TRANSPARENT_BG)
        # Renderer Button --------------------------------------
        toolTip = "Change the renderer to Arnold, Redshift or Renderman"
        self.rendererIconMenu = elements.iconMenuButtonCombo(DFLT_RNDR_MODES,
                                                             self.properties.rendererIconMenu.value,
                                                             toolTip=toolTip)
        if uiMode == UI_MODE_ADVANCED:
            # Diffuse Title
            self.diffuseTitle = elements.LabelDivider(text="Diffuse")
            # Diffuse Weight Slider --------------------------------------------------------
            toolTip = "Diffuse Weight adjusts the value (brightness) of the Diffuse Color "
            self.diffuseWeightFloatSldr = elements.FloatSlider(label="Diffuse Weight",
                                                               defaultValue=1.0,
                                                               toolTip=toolTip,
                                                               decimalPlaces=3)
            # Specular Title
            self.specularTitle = elements.LabelDivider(text="Specular")
            # Specular Weight Slider --------------------------------------------------------
            toolTip = "Specular Weight adjusts the value (brightness) of the Specular Color "
            self.specularWeightFloatSldr = elements.FloatSlider(label="Spec Weight",
                                                                defaultValue=1.0,
                                                                toolTip=toolTip,
                                                                decimalPlaces=3)
            # Clear Coat Title
            self.clearCoatTitle = elements.LabelDivider(text="Clear Coat")
            # Clear Coat Weight Slider --------------------------------------------------------
            toolTip = "Clear Coat Weight adjusts the value (brightness) of the Clear Coat Specular Color"
            self.clearCoatWeightFloatSldr = elements.FloatSlider(label="Coat Weight",
                                                                 defaultValue=0.0,
                                                                 toolTip=toolTip,
                                                                 decimalPlaces=3)
            # Clear Coat Color Slider ---------------------------------------
            toolTip = "The second specular layer, Clear Coat color. \n" \
                      "- Usually white for a glassy polish"
            self.clearCoatColorSldr = elements.MayaColorSlider(label="Coat Color",
                                                               color=MAYA_DEFAULT_COAT_COLOR,
                                                               toolTip=toolTip)
            # Specular Weight Slider --------------------------------------------------------
            toolTip = "Adjusts the roughness of the second specular layer, Clear Coat. \n" \
                      " 0.0 Shiny \n" \
                      " 0.6 Rough"
            self.clearCoatRoughFoatSldr = elements.FloatSlider(label="Coat Rough",
                                                               defaultValue=0.2,
                                                               toolTip=toolTip,
                                                               decimalPlaces=3)
            # IOR Clear Coat Slider --------------------------------------------------------
            toolTip = "value for clear coat is usually \n" \
                      "- 1.5 Glass Polish \n" \
                      "- 1.3 Wet Water"
            self.clearCoatIorFloatSldr = elements.FloatSlider(label="IOR",
                                                              defaultValue=1.50,
                                                              toolTip=toolTip,
                                                              sliderMin=1.0,
                                                              sliderMax=20.0,
                                                              decimalPlaces=2,
                                                              sliderAccuracy=2000)


class GuiCompact(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None,
                 presetShaderList=None):
        """Adds the layout building the compact version of the GUI:

            default uiMode - 0 is advanced (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(GuiCompact, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                         toolsetWidget=toolsetWidget, presetShaderList=presetShaderList)
        # Main Layout ---------------------------------------
        contentsLayout = elements.vBoxLayout(parent=parent,
                                             margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD))
        # Type Combo Update btn Layout ---------------------------------------
        typeUpdateLayout = elements.hBoxLayout()
        typeUpdateLayout.addWidget(self.reloadShaderBtn, 1)
        typeUpdateLayout.addWidget(self.shaderTypeCombo, 10)
        # Top Grid Layout
        topGridLayout = elements.GridLayout(margins=(0, 0, 0, uic.VSMLPAD), spacing=uic.SREG)
        topGridLayout.addWidget(self.shaderPresetsCombo, 0, 0)
        topGridLayout.addLayout(typeUpdateLayout, 0, 1)
        topGridLayout.setColumnStretch(0, 1)
        topGridLayout.setColumnStretch(1, 1)
        # Name Checkbox Layout ---------------------------------------
        nameCheckboxLayout = elements.hBoxLayout()
        nameCheckboxLayout.addWidget(self.shaderNameComboE, 20)
        nameCheckboxLayout.addWidget(self.deleteShaderBtn, 1)
        # Slider Layout ---------------------------------------
        sliderLayout = elements.vBoxLayout(margins=(0, 0, 0, uic.SMLPAD), spacing=uic.SLRG)
        sliderLayout.addWidget(self.diffuseColorSldr)
        sliderLayout.addWidget(self.specularColorSldr)
        sliderLayout.addWidget(self.specularRoughFloatSldr)
        sliderLayout.addWidget(self.iorFloatSldr)
        # Bot Button Layout ---------------------------------------
        botButtonLayout = elements.hBoxLayout()
        botButtonLayout.addWidget(self.selectShaderBtn, 1)
        botButtonLayout.addWidget(self.selectObjectsBtn, 1)
        botButtonLayout.addWidget(self.rendererIconMenu, 1)
        # Buttons Main Layout ---------------------------------------
        buttonsLayout = elements.GridLayout()
        buttonsLayout.addWidget(self.copyShaderBtn, 0, 0)
        buttonsLayout.addWidget(self.pasteShaderBtn, 0, 1)
        buttonsLayout.addWidget(self.pasteAttrBtn, 0, 2)
        buttonsLayout.addWidget(self.createShaderBtn, 1, 0)
        buttonsLayout.addWidget(self.transferShaderBtn, 1, 1)
        buttonsLayout.addLayout(botButtonLayout, 1, 2)
        buttonsLayout.setColumnStretch(0, 1)
        buttonsLayout.setColumnStretch(1, 1)
        buttonsLayout.setColumnStretch(2, 1)
        # Add To Main Layout ---------------------------------------
        contentsLayout.addLayout(topGridLayout)
        contentsLayout.addLayout(nameCheckboxLayout)
        contentsLayout.addLayout(typeUpdateLayout)
        contentsLayout.addLayout(sliderLayout)
        contentsLayout.addLayout(buttonsLayout)


class GuiAdvanced(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_ADVANCED, toolsetWidget=None,
                 presetShaderList=None):
        """Adds the layout building the advanced version of the GUI:

            default uiMode - 1 is advanced (UI_MODE_ADVANCED)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(GuiAdvanced, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                          toolsetWidget=toolsetWidget, presetShaderList=presetShaderList)
        # Main Layout ---------------------------------------
        contentsLayout = elements.vBoxLayout(parent,
                                             margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                             spacing=uic.SREG)
        # Type Combo Update btn Layout ---------------------------------------
        typeUpdateLayout = elements.hBoxLayout()
        typeUpdateLayout.addWidget(self.reloadShaderBtn, 1)
        typeUpdateLayout.addWidget(self.shaderTypeCombo, 10)
        # Top Grid Layout
        topGridLayout = elements.GridLayout(margins=(0, 0, 0, uic.VSMLPAD), spacing=uic.SREG)
        topGridLayout.addWidget(self.shaderPresetsCombo, 0, 0)
        topGridLayout.addLayout(typeUpdateLayout, 0, 1)
        topGridLayout.setColumnStretch(0, 1)
        topGridLayout.setColumnStretch(1, 1)
        # Name Checkbox Layout ---------------------------------------
        nameCheckboxLayout = elements.hBoxLayout()
        nameCheckboxLayout.addWidget(self.shaderNameComboE, 20)
        nameCheckboxLayout.addWidget(self.deleteShaderBtn, 1)
        # Diffuse Layout ---------------------------------------
        diffuseLayout = elements.vBoxLayout(margins=(uic.SREG, 0, uic.SREG, 0), spacing=uic.SLRG)
        diffuseLayout.addWidget(self.diffuseWeightFloatSldr, 1)
        diffuseLayout.addWidget(self.diffuseColorSldr, 1)
        # Specular Layout ---------------------------------------
        specularLayout = elements.vBoxLayout(margins=(uic.SREG, 0, uic.SREG, 0), spacing=uic.SLRG)
        specularLayout.addWidget(self.specularWeightFloatSldr, 1)
        specularLayout.addWidget(self.specularColorSldr, 1)
        specularLayout.addWidget(self.specularRoughFloatSldr, 1)
        specularLayout.addWidget(self.iorFloatSldr, 1)
        # Clear Coat Layout ---------------------------------------
        clearCoatLayout = elements.vBoxLayout(margins=(uic.SREG, 0, uic.SREG, 0), spacing=uic.SLRG)
        clearCoatLayout.addWidget(self.clearCoatWeightFloatSldr, 1)
        clearCoatLayout.addWidget(self.clearCoatColorSldr, 1)
        clearCoatLayout.addWidget(self.clearCoatRoughFoatSldr, 1)
        clearCoatLayout.addWidget(self.clearCoatIorFloatSldr, 1)
        # Bot Button Layout ---------------------------------------
        botButtonLayout = elements.hBoxLayout()
        botButtonLayout.addWidget(self.selectShaderBtn, 1)
        botButtonLayout.addWidget(self.selectObjectsBtn, 1)
        botButtonLayout.addWidget(self.rendererIconMenu, 1)
        # Buttons Main Layout ---------------------------------------
        buttonsLayout = elements.GridLayout()
        buttonsLayout.addWidget(self.copyShaderBtn, 0, 0)
        buttonsLayout.addWidget(self.pasteShaderBtn, 0, 1)
        buttonsLayout.addWidget(self.pasteAttrBtn, 0, 2)
        buttonsLayout.addWidget(self.createShaderBtn, 1, 0)
        buttonsLayout.addWidget(self.transferShaderBtn, 1, 1)
        buttonsLayout.addLayout(botButtonLayout, 1, 2)
        buttonsLayout.setColumnStretch(0, 1)
        buttonsLayout.setColumnStretch(1, 1)
        buttonsLayout.setColumnStretch(2, 1)
        # Add To Main Layout ---------------------------------------
        contentsLayout.addLayout(topGridLayout)
        contentsLayout.addLayout(nameCheckboxLayout)
        contentsLayout.addWidget(self.diffuseTitle)
        contentsLayout.addLayout(diffuseLayout)
        contentsLayout.addWidget(self.specularTitle)
        contentsLayout.addLayout(specularLayout)
        contentsLayout.addWidget(self.clearCoatTitle)
        contentsLayout.addLayout(clearCoatLayout)
        contentsLayout.addLayout(buttonsLayout)
