from Qt import QtWidgets

import maya.cmds as cmds

from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.maya.cmds.objutils import cleanup

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class ObjectCleaner(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "objectCleaner"
    info = "Cleans polygon objects ready for publishing."
    uiData = {"label": "Object Cleaner",
              "icon": "sprayCleaner",
              "tooltip": "Cleans polygon objects ready for publishing.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-object-cleaner/"}

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        self.meshTransforms_sel = list()
        self.laminaFaces_sel = list()
        self.nonManifold_sel = list()
        self.interiorVertex_sel = list()
        self.zeroFace_sel = list()

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

    def defaultAction(self):
        """Double Click
        Double clicking the tools toolset icon will run this method
        Be sure "defaultActionDoubleClick": True is set inside self.uiData (meta data of this class)"""
        pass

    def currentWidget(self):
        """Returns the current widget class eg. self.compactWidget or self.advancedWidget

        Over ridden class
        """
        return super(ObjectCleaner, self).currentWidget()

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
        return super(ObjectCleaner, self).widgets()

    # ------------------------------------
    # EMBED WINDOWS
    # ------------------------------------

    def setEmbedVisible(self, vis=False):
        """Shows and hides the saveEmbedWindow"""
        if isinstance(self.currentWidget(), GuiCompact):
            self.compactWidget.checkMeshEmbedWinContainer.setEmbedVisible(vis)

    def closeEmbedWindow(self):
        """Shows and hides the saveEmbedWindow"""
        self.setEmbedVisible(vis=False)

    # ------------------------------------
    # SHOW HIDE BUTTONS
    # ------------------------------------

    def showHideButtons(self, embedVis):
        self.compactWidget.checkMeshIssuesBtn.setVisible(not embedVis)
        self.compactWidget.meshCheckLabel.setVisible(not embedVis)

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidgetmaya.undoDecorator
    def nonManifold(self):
        cleanup.nonManifold()

    @toolsetwidgetmaya.undoDecorator
    def interiorVertex(self, includeBoundary=False):
        cleanup.interiorVertex()

    @toolsetwidgetmaya.undoDecorator
    def zeroFace(self):
        cleanup.zeroFaceSelected()

    @toolsetwidgetmaya.undoDecorator
    def findLaminaFaces(self):
        cleanup.findLaminaFaces()

    @toolsetwidgetmaya.undoDecorator
    def fixLaminaFaces(self):
        cleanup.findLaminaFaces(delete=True)

    @toolsetwidgetmaya.undoDecorator
    def unlockVertexNormals(self):
        cleanup.unlockVertexNormalsList()

    @toolsetwidgetmaya.undoDecorator
    def averageVertexNormals(self):
        cleanup.averageVertexNormals()

    @toolsetwidgetmaya.undoDecorator
    def conformNormals(self):
        cleanup.conformNormals()

    @toolsetwidgetmaya.undoDecorator
    def reverseFaceNormals(self):
        cleanup.reverseFaceNormals()

    @toolsetwidgetmaya.undoDecorator
    def mergeIdenticalVertices(self):
        cleanup.mergeIdenticalVertices()

    @toolsetwidgetmaya.undoDecorator
    def deleteHistory(self):
        cleanup.deleteHistory()

    @toolsetwidgetmaya.undoDecorator
    def freezeTransforms(self):
        cleanup.freezeTransforms()

    @toolsetwidgetmaya.undoDecorator
    def removeInstances(self):
        cleanup.interiorVertex()

    @toolsetwidgetmaya.undoDecorator
    def checkSymmetry(self):
        cleanup.checkSymmetry()

    @toolsetwidgetmaya.undoDecorator
    def softenEdge(self):
        cleanup.softenEdgeSelection()

    @toolsetwidgetmaya.undoDecorator
    def hardenEdge(self):
        cleanup.hardenEdgeSelection()

    def recheckMeshTranforms(self):
        self.checkMeshIssues(objList=self.meshTransforms_sel)  # recheck the meshes
        self.updateTree(delayed=True)  # Refresh GUI  Needs a second refresh :/
        return True

    @toolsetwidgetmaya.undoDecorator
    def select_nonManifold(self):
        if not self.nonManifold_sel:
            return
        self.nonManifold_sel = cleanup.nonManifold(objList=self.meshTransforms_sel)
        if not self.nonManifold_sel:  # hide UI
            self.compactWidget.selectNonManifold_imgBtn.setVisible(False)
            self.recheckMeshTranforms()  # if True will display the checkbox image, does the GUI refresh

    @toolsetwidgetmaya.undoDecorator
    def select_interiorVertex(self):
        if not self.interiorVertex_sel:
            return
        self.interiorVertex_sel = cleanup.interiorVertex(objList=self.meshTransforms_sel)
        if not self.interiorVertex_sel:
            self.compactWidget.selectInteriorVert_imgBtn.setVisible(False)
            self.recheckMeshTranforms()  # if True will display the checkbox image, does the GUI refresh

    @toolsetwidgetmaya.undoDecorator
    def select_zeroFace(self):
        if not self.zeroFace_sel:
            return
        self.zeroFace = cleanup.zeroFace(self.meshTransforms_sel, select=True, message=True)
        if not self.zeroFace:
            self.compactWidget.selectZeroFace_imgBtn.setVisible(False)
            self.recheckMeshTranforms()  # if True will display the checkbox image, does the GUI refresh

    @toolsetwidgetmaya.undoDecorator
    def select_laminaFaces(self):
        if not self.laminaFaces_sel:
            return
        self.laminaFaces_sel = cleanup.findLaminaFaces(objList=self.meshTransforms_sel)
        if not self.laminaFaces_sel:
            self.compactWidget.selectLaminaFace_imgBtn.setVisible(False)
            self.recheckMeshTranforms()  # if True will display the checkbox image, does the GUI refresh

    @toolsetwidgetmaya.undoDecorator
    def checkMeshIssues(self, objList=list()):
        if not objList:  # check selection
            if not cleanup.checkMeshSelection():
                return  # message already sent
        self.meshTransforms_sel, \
        self.nonManifold_sel, \
        self.interiorVertex_sel, \
        self.zeroFace_sel, \
        self.laminaFaces_sel = cleanup.checkMeshIssues(objList=objList, message=True)
        # Show/Hide the buttons --------------------------
        if self.nonManifold_sel:
            self.compactWidget.selectNonManifold_imgBtn.setVisible(True)
        else:
            self.compactWidget.selectNonManifold_imgBtn.setVisible(False)

        if self.interiorVertex_sel:
            self.compactWidget.selectInteriorVert_imgBtn.setVisible(True)
        else:
            self.compactWidget.selectInteriorVert_imgBtn.setVisible(False)

        if self.laminaFaces_sel:
            self.compactWidget.selectLaminaFace_imgBtn.setVisible(True)
        else:
            self.compactWidget.selectLaminaFace_imgBtn.setVisible(False)

        if self.zeroFace_sel:
            zeroFaceVal = True
        else:
            zeroFaceVal = False
        self.compactWidget.selectZeroFace_imgBtn.setVisible(zeroFaceVal)
        self.compactWidget.mergeIdenticalBtn.setVisible(zeroFaceVal)
        self.compactWidget.laminaBtn.setVisible(zeroFaceVal)
        self.compactWidget.fixLaminaBtn.setVisible(zeroFaceVal)

        if self.nonManifold_sel or self.interiorVertex_sel or self.zeroFace_sel or self.laminaFaces_sel:
            self.compactWidget.noIssuesFound_imgBtn.setVisible(False)
        else:
            self.compactWidget.noIssuesFound_imgBtn.setVisible(True)

        # Show the embed window ------------------------
        self.setEmbedVisible(vis=True)  # Show the embed window with results
        self.updateTree(delayed=True)  # Refresh GUI needs a kick here

    def objClean(self):
        """Object cleans in two undo chunks, undo handled internally.

        1. Export import the objects
        2. Optional delete the old objects
        """
        cmds.undoInfo(openChunk=True)
        newObjectList, oldObjectList = cleanup.objClean(deleteOldObj=False,
                                                        keepNormals=self.properties.keepNormalsCheckbox.value,
                                                        keepShaders=self.properties.keepShadersCheckbox.value)
        if not newObjectList:
            return  # message sent
        cmds.undoInfo(closeChunk=True)
        if self.properties.removeOriginalCheckbox.value:
            cmds.undoInfo(openChunk=True)
            cmds.delete(oldObjectList)
            cmds.undoInfo(closeChunk=True)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.unlockNormalsBtn.clicked.connect(self.unlockVertexNormals)
            widget.softenBtn.clicked.connect(self.softenEdge)
            widget.hardenBtn.clicked.connect(self.hardenEdge)
            widget.conformNormalsBtn.clicked.connect(self.conformNormals)
            widget.reverseNormalsBtn.clicked.connect(self.reverseFaceNormals)
            widget.deleteHistoryBtn.clicked.connect(self.deleteHistory)
            widget.freezeTransformsBtn.clicked.connect(self.freezeTransforms)
            widget.checkSymmetryBtn.clicked.connect(self.checkSymmetry)
            widget.removeInstancesBtn.clicked.connect(self.removeInstances)
            widget.cleanBtn.clicked.connect(self.objClean)
            widget.mergeIdenticalBtn.clicked.connect(self.mergeIdenticalVertices)
            widget.laminaBtn.clicked.connect(self.findLaminaFaces)
            widget.fixLaminaBtn.clicked.connect(self.fixLaminaFaces)
            if isinstance(widget, GuiCompact):
                widget.checkMeshIssuesBtn.clicked.connect(self.checkMeshIssues)
                widget.recheckGeometryBtn.clicked.connect(self.checkMeshIssues)
                widget.noIssuesFound_imgBtn.clicked.connect(self.closeEmbedWindow)
                widget.checkMeshEmbedWinContainer.visibilityChanged.connect(self.showHideButtons)
                # Image buttons for selecting mesh issues
                widget.selectNonManifold_imgBtn.clicked.connect(self.select_nonManifold)
                widget.selectInteriorVert_imgBtn.clicked.connect(self.select_interiorVertex)
                widget.selectZeroFace_imgBtn.clicked.connect(self.select_zeroFace)
                widget.selectLaminaFace_imgBtn.clicked.connect(self.select_laminaFaces)
            if isinstance(widget, GuiAdvanced):
                widget.nonManifoldBtn.clicked.connect(self.nonManifold)
                widget.interiorVertexBtn.clicked.connect(self.interiorVertex)
                widget.zeroFaceBtn.clicked.connect(self.zeroFace)


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
        self.toolsetWidget = toolsetWidget  # needed for the embed window
        # Conform Normals ---------------------------------------
        tooltip = "Conforms face normals so they point the right way. \n" \
                  "Select polygon object/s and run."
        self.conformNormalsBtn = elements.styledButton("Conform Face Normals",
                                                       icon="conformNormals",
                                                       toolTip=tooltip,
                                                       style=uic.BTN_LABEL_SML)
        # Reverse Normals ---------------------------------------
        tooltip = "Reverses face normals so they point the opposite direction. \n" \
                  "Select polygon faces or object/s and run. "
        self.reverseNormalsBtn = elements.styledButton("Reverse Face Normals",
                                                       icon="flipFaceNormals",
                                                       toolTip=tooltip,
                                                       style=uic.BTN_LABEL_SML)
        # Unlock Vertex Normals ---------------------------------------
        tooltip = "Unlocks Vertex Normals. Select polygon object/s and run"
        self.unlockNormalsBtn = elements.styledButton("Unlock Vertex Normals",
                                                      icon="unlock",
                                                      toolTip=tooltip,
                                                      style=uic.BTN_LABEL_SML)
        # Soften Harden Normals ---------------------------------------
        tooltip = "Soften or Harden selected Edges"
        self.softenBtn = elements.styledButton("Soft/Hard Edges",
                                               icon="softenEdge",
                                               toolTip=tooltip,
                                               style=uic.BTN_LABEL_SML)
        tooltip = "Soften or Harden selected Edges"
        self.hardenBtn = elements.styledButton("",
                                               icon="hardenEdge",
                                               toolTip=tooltip,
                                               style=uic.BTN_LABEL_SML)
        # Check Symmetry Vertex ---------------------------------------
        tooltip = "Check an object/s symmetry. Select polygon object/s and run"
        self.checkSymmetryBtn = elements.styledButton("Check Symmetry",
                                                      parent=parent,
                                                      icon="symmetryTri",
                                                      toolTip=tooltip,
                                                      style=uic.BTN_LABEL_SML)
        # Remove Instances ---------------------------------------
        tooltip = "Removes any instances in the scene, leaving the geometry in place. \n" \
                  "Select objects and run."
        self.removeInstancesBtn = elements.styledButton("Remove Instances",
                                                        parent=parent,
                                                        icon="crossXFat",
                                                        toolTip=tooltip,
                                                        style=uic.BTN_LABEL_SML)
        # Delete History ---------------------------------------
        tooltip = "Delete History on the selected polygon objects"
        self.deleteHistoryBtn = elements.styledButton("Delete History",
                                                      icon="crossXFat",
                                                      toolTip=tooltip,
                                                      style=uic.BTN_LABEL_SML)
        # Freeze Transforms ---------------------------------------
        tooltip = "Freeze Transforms on the selected polygon objects"
        self.freezeTransformsBtn = elements.styledButton("Freeze Transforms",
                                                         icon="freezeSnowFlake",
                                                         toolTip=tooltip,
                                                         style=uic.BTN_LABEL_SML)
        # Clean Import Export ---------------------------------------
        tooltip = "instantly .OBJ Exports the selected files to disk, and then \n" \
                  "immediately imports the object back into the scene as a new object.  \n" \
                  "This cleans the selected object/s of extra nodes and Maya baggage. \n" \
                  "Shader, SubD, and Vertex-Normals assignments are retained if checked."
        self.cleanBtn = elements.styledButton("Clean Import/Export",
                                              icon="sprayCleaner",
                                              toolTip=tooltip)
        # Remove Original Objects Checkbox -----------------------------
        tooltip = "If on will delete the original objects while cleaning. \n" \
                  "Objects can be recovered with a single undo level."
        self.removeOriginalCheckbox = elements.CheckBox(label="Delete Orig Objects",
                                                        checked=True,
                                                        toolTip=tooltip)
        # Shaders Checkbox -----------------------------
        tooltip = "On will keep the shader assignments. \n" \
                  "Off will assign lamberts to new objects."
        self.keepShadersCheckbox = elements.CheckBox(label="Keep Shaders",
                                                     checked=True,
                                                     toolTip=tooltip)
        # Normals Checkbox -----------------------------
        tooltip = "On will keep the vertex normal information. \n" \
                  "Off will destroy normal info all edges will be hard."
        self.keepNormalsCheckbox = elements.CheckBox(label="Keep Normals",
                                                     checked=True,
                                                     toolTip=tooltip)
        # Merge Identical Verts ---------------------------------------
        tooltip = "Merges vertices with identical positions. \n" \
                  "Select polygon object/s and run."
        self.mergeIdenticalBtn = elements.styledButton("Merge Identical Vertices",
                                                       icon="mergeVertex",
                                                       toolTip=tooltip,
                                                       style=uic.BTN_LABEL_SML)

        # Lamina Faces ---------------------------------------
        tooltip = "Find lamina face issues. Select polygon object/s and run"
        self.laminaBtn = elements.styledButton("Find Lamina Faces",
                                               icon="laminaFace",
                                               toolTip=tooltip,
                                               style=uic.BTN_LABEL_SML)
        # Fix Lamina Faces ---------------------------------------
        tooltip = "Merges vertices then deletes lamina faces. Select polygon object/s and run"
        self.fixLaminaBtn = elements.styledButton("Fix Lamina Faces",
                                                  icon="laminaFace",
                                                  toolTip=tooltip,
                                                  style=uic.BTN_LABEL_SML)
        # Hide unused widgets for later
        self.removeInstancesBtn.hide()
        self.checkSymmetryBtn.hide()

        if uiMode == UI_MODE_COMPACT:
            # Mesh Check All ---------------------------------------
            tooltip = "Checks meshes for mesh issues. Select polygon object/s and run. \n" \
                      " - non-manifold \n" \
                      " - interior-vertex\n" \
                      " - lamina-faces\n" \
                      " - zero area faces"
            self.checkMeshIssuesBtn = elements.styledButton("Check Mesh Issues",
                                                            icon="checkMark",
                                                            toolTip=tooltip)
            # Check Mesh Label ---------------------------------------
            self.meshCheckLabel = elements.LabelDivider(text="Mesh Checks")
            # Check Mesh Embed Window ---------------------------------------
            self.checkMeshEmbedWinContainer = self.checkMeshEmbedWin(parent=parent)

        if uiMode == UI_MODE_ADVANCED:
            # Non-Manifold ---------------------------------------
            tooltip = "Find non-manifold geometry issues. \n" \
                      "Non-Manifold areas are where three or more faces connect to a single edge. \n" \
                      "Select polygon object/s and run."
            self.nonManifoldBtn = elements.styledButton("Find Non-Manifold",
                                                        icon="nonManifold",
                                                        toolTip=tooltip,
                                                        style=uic.BTN_LABEL_SML)
            # Interior Vertex ---------------------------------------
            tooltip = "Find interior vertex issues. Select polygon object/s and run"
            self.interiorVertexBtn = elements.styledButton("Find Interior Vertex",
                                                           icon="interiorVertex",
                                                           toolTip=tooltip,
                                                           style=uic.BTN_LABEL_SML)
            # Zero Face Area ---------------------------------------
            tooltip = "Selects faces with zero area. Select polygon object/s and run"
            self.zeroFaceBtn = elements.styledButton("Zero Face Area",
                                                     icon="zeroFace",
                                                     toolTip=tooltip,
                                                     style=uic.BTN_LABEL_SML)

    def checkMeshEmbedWin(self, parent=None):
        """The popup properties UI embedded window for saving assets

        :param parent: the parent widget
        :type parent: Qt.object
        """
        toolTip = "Close the save window"
        self.hidePropertiesBtn = elements.styledButton("",
                                                       "closeX",
                                                       toolTip=toolTip,
                                                       maxWidth=uic.BTN_W_ICN_SML,
                                                       minWidth=uic.BTN_W_ICN_SML,
                                                       style=uic.BTN_TRANSPARENT_BG)
        saveEmbedWindow = elements.EmbeddedWindow(title="MESH CHECK",
                                                  closeButton=self.hidePropertiesBtn,
                                                  margins=(0, uic.SMLPAD, 0, uic.REGPAD),
                                                  uppercase=True,
                                                  defaultVisibility=True,
                                                  parent=parent)
        saveEmbedWindow.visibilityChanged.connect(self.embedWindowVisChanged)

        self.checkEmbedWinLayout = saveEmbedWindow.getLayout()
        self.saveEmbedWinLbl = saveEmbedWindow.getTitleLbl()
        # Check Issues Button -------------------------------------
        tooltip = "No issues have been found regarding the following issues. \n" \
                  " - Non-Manifold \n" \
                  " - Interior-Vertex \n" \
                  " - Lamina Faces \n" \
                  " - Zero Face \n" \
                  "Click to close this section."
        self.noIssuesFound_imgBtn = elements.ImageButton(text="Meshes Checked. No Issues Found",
                                                         image="image_check",
                                                         icon="checkOnly",
                                                         imageHeight=322,
                                                         imageWidth=104,
                                                         toolTip=tooltip,
                                                         square=False)
        # Image Non Manifold Button -------------------------------------
        tooltip = "Non-Manifold issues found, click to isolate this issue. \n" \
                  "Non-Manifold is when an edge has 3 or more connecting faces."
        self.selectNonManifold_imgBtn = elements.ImageButton(text="Select Non-Manifold Issues Found",
                                                             image="image_nonManifold",
                                                             icon="cursorSelect",
                                                             imageHeight=322,
                                                             imageWidth=104,
                                                             toolTip=tooltip,
                                                             square=False)
        # Image Interior Vertex Button -------------------------------------
        tooltip = "Interior-Vertex issues found, click to isolate this issue. \n" \
                  "Interior-Vertex is when a vertex is only connected by two edges \n" \
                  "and is not on the border edge."
        self.selectInteriorVert_imgBtn = elements.ImageButton(text="Select Interior-Vertex Issues Found",
                                                              image="image_interiorVertex",
                                                              icon="cursorSelect",
                                                              imageHeight=322,
                                                              imageWidth=104,
                                                              toolTip=tooltip,
                                                              square=False)
        # Image Lamina-Face Button -------------------------------------
        tooltip = "Lamina-Face issues found, click to isolate this issue. \n" \
                  "A Lamina-Face is a face that shares all vertices with another face. \n" \
                  "Usually caused by accidental extrudes and merge vertices. \n" \
                  "To fix just delete the selected faces."
        self.selectLaminaFace_imgBtn = elements.ImageButton(text="Select Lamina-Face Issues Found",
                                                            image="image_laminaFace",
                                                            icon="cursorSelect",
                                                            imageHeight=322,
                                                            imageWidth=104,
                                                            toolTip=tooltip,
                                                            square=False)
        # Image Zero-Face Button -------------------------------------
        tooltip = "Zero-Face issues found, click to isolate this issue. \n" \
                  "A Zero-Face is a face that has no area. \n" \
                  "To fix pull offending vertices away from each other or merge them together."
        self.selectZeroFace_imgBtn = elements.ImageButton(text="Select Zero-Face Issues Found",
                                                          image="image_zeroFace",
                                                          icon="cursorSelect",
                                                          imageHeight=322,
                                                          imageWidth=104,
                                                          toolTip=tooltip,
                                                          square=False)
        # Layout -------------------------------------------------------
        zeroFaceOptionsGridLayout = elements.GridLayout(hSpacing=uic.SVLRG)
        zeroFaceOptionsGridLayout.addWidget(self.mergeIdenticalBtn, 0, 0)
        zeroFaceOptionsGridLayout.addWidget(self.laminaBtn, 0, 1)
        zeroFaceOptionsGridLayout.addWidget(self.fixLaminaBtn, 1, 0)
        zeroFaceOptionsGridLayout.setColumnStretch(0, 1)
        zeroFaceOptionsGridLayout.setColumnStretch(1, 1)
        # Save Button -------------------------------------
        toolTip = ""
        self.recheckGeometryBtn = elements.styledButton("Recheck Selected Geometry",
                                                        icon="reload2",
                                                        toolTip=toolTip,
                                                        style=uic.BTN_DEFAULT)
        # save Button  layout -------------------------------------
        saveButtonLayout = elements.hBoxLayout()
        saveButtonLayout.addWidget(self.recheckGeometryBtn)
        # add to main layout -------------------------------------
        self.checkEmbedWinLayout.addWidget(self.noIssuesFound_imgBtn)
        self.checkEmbedWinLayout.addWidget(self.selectNonManifold_imgBtn)
        self.checkEmbedWinLayout.addWidget(self.selectInteriorVert_imgBtn)
        self.checkEmbedWinLayout.addWidget(self.selectLaminaFace_imgBtn)
        self.checkEmbedWinLayout.addWidget(self.selectZeroFace_imgBtn)
        self.checkEmbedWinLayout.addLayout(zeroFaceOptionsGridLayout)
        self.checkEmbedWinLayout.addLayout(saveButtonLayout)
        return saveEmbedWindow

    def embedWindowVisChanged(self, visibility):
        self.toolsetWidget.updateTree(delayed=True)


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
        # Soften Harden Layout ---------------------------------------
        softenHardenLayout = elements.hBoxLayout()
        softenHardenLayout.addWidget(self.softenBtn, 6)
        softenHardenLayout.addWidget(self.hardenBtn, 1)
        # Checkbox Layout ---------------------------------------
        checkboxLayout = elements.hBoxLayout(margins=(uic.REGPAD, uic.SMLPAD, uic.REGPAD, uic.SMLPAD))
        checkboxLayout.addWidget(self.keepShadersCheckbox, 1)
        checkboxLayout.addWidget(self.keepNormalsCheckbox, 1)
        checkboxLayout.addWidget(self.removeOriginalCheckbox, 1)
        # Grid Layout ---------------------------------------
        gridLayout = elements.GridLayout(hSpacing=uic.SVLRG)
        gridLayout.addWidget(self.meshCheckLabel, 0, 0, 1, 2)
        gridLayout.addWidget(self.checkMeshIssuesBtn, 1, 0, 1, 2)
        gridLayout.addWidget(elements.LabelDivider(text="Normals"), 5, 0, 1, 2)
        gridLayout.addWidget(self.unlockNormalsBtn, 6, 0)
        gridLayout.addLayout(softenHardenLayout, 6, 1)
        gridLayout.addWidget(self.conformNormalsBtn, 7, 0)
        gridLayout.addWidget(self.reverseNormalsBtn, 7, 1)
        gridLayout.addWidget(elements.LabelDivider(text="Freeze & Delete History"), 8, 0, 1, 2)
        gridLayout.addWidget(self.freezeTransformsBtn, 9, 0)
        gridLayout.addWidget(self.deleteHistoryBtn, 9, 1)
        gridLayout.addWidget(self.checkSymmetryBtn, 10, 0)  # hidden
        gridLayout.addWidget(self.removeInstancesBtn, 10, 1)  # hidden
        gridLayout.addWidget(elements.LabelDivider(text="OBJ Clean Import/Export"), 12, 0, 1, 2)
        gridLayout.addLayout(checkboxLayout, 13, 0, 1, 2)
        gridLayout.addWidget(self.cleanBtn, 14, 0, 1, 2)
        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(self.checkMeshEmbedWinContainer)
        mainLayout.addLayout(gridLayout)


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
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Soften Harden Layout ---------------------------------------
        softenHardenLayout = elements.hBoxLayout()
        softenHardenLayout.addWidget(self.softenBtn, 6)
        softenHardenLayout.addWidget(self.hardenBtn, 1)
        # Checkbox Layout ---------------------------------------
        checkboxLayout = elements.hBoxLayout(margins=(uic.REGPAD, uic.SMLPAD, uic.REGPAD, uic.SMLPAD))
        checkboxLayout.addWidget(self.keepShadersCheckbox, 1)
        checkboxLayout.addWidget(self.keepNormalsCheckbox, 1)
        checkboxLayout.addWidget(self.removeOriginalCheckbox, 1)
        # Grid Layout ---------------------------------------
        gridLayout = elements.GridLayout(hSpacing=uic.SVLRG)
        gridLayout.addWidget(elements.LabelDivider(text="Non-Manifold & Interior Vertex"), 0, 0, 1, 2)
        gridLayout.addWidget(self.nonManifoldBtn, 1, 0)
        gridLayout.addWidget(self.interiorVertexBtn, 1, 1)
        gridLayout.addWidget(elements.LabelDivider(text="Lamina Faces (Accidental Extrude)"), 2, 0, 1, 2)
        gridLayout.addWidget(self.zeroFaceBtn, 3, 0)
        gridLayout.addWidget(self.mergeIdenticalBtn, 3, 1)
        gridLayout.addWidget(self.laminaBtn, 4, 0)
        gridLayout.addWidget(self.fixLaminaBtn, 4, 1)
        gridLayout.addWidget(elements.LabelDivider(text="Normals"), 5, 0, 1, 2)
        gridLayout.addWidget(self.unlockNormalsBtn, 6, 0)
        gridLayout.addLayout(softenHardenLayout, 6, 1)
        gridLayout.addWidget(self.conformNormalsBtn, 7, 0)
        gridLayout.addWidget(self.reverseNormalsBtn, 7, 1)
        gridLayout.addWidget(elements.LabelDivider(text="Freeze & Delete History"), 8, 0, 1, 2)
        gridLayout.addWidget(self.freezeTransformsBtn, 9, 0)
        gridLayout.addWidget(self.deleteHistoryBtn, 9, 1)
        gridLayout.addWidget(self.checkSymmetryBtn, 10, 0)  # hidden
        gridLayout.addWidget(self.removeInstancesBtn, 10, 1)  # hidden
        gridLayout.addWidget(elements.LabelDivider(text="OBJ Clean Import/Export"), 12, 0, 1, 2)
        gridLayout.addLayout(checkboxLayout, 13, 0, 1, 2)
        gridLayout.addWidget(self.cleanBtn, 14, 0, 1, 2)
        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(gridLayout)
