from functools import partial

from Qt import QtWidgets, QtCore

import maya.api.OpenMaya as om2

from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.maya.utils import env
from zoo.libs.command import executor
from zoo.libs.maya.cmds.objutils import connections, attributes

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

MAYA_VERSION = env.mayaVersion()  # whole numbers (int) 2020 etc


class MakeConnections(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "makeConnections"
    info = "Connects rotate, translate and scale between nodes"
    uiData = {"label": "Attribute Connections",
              "icon": "connectionSRT",
              "tooltip": "Connects rotate, translate and scale between nodes",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-attribute-connections/"}

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        self.sourceObjAttrs = list()  # copy/paste globals
        self.destinationAttrs = list()  # copy/paste globals

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
    # UI DISPLAY CHECK BOX TOGGLES
    # ------------------

    def matrixChecked(self):
        """Toggle off the SRT checkboxes if Matrix goes on"""
        if not self.properties.matrixCheckBox.value:
            return
        self.properties.translateCheckBox.value = False
        self.properties.rotateCheckBox.value = False
        self.properties.scaleCheckBox.value = False
        self.updateFromProperties()

    def srtCheckboxChecked(self, checked, rot=False, trans=False, scale=False):
        """Turns the Matrix checkbox off if any other checkboxes come on

        :param checked: Null value from the checkbox
        :type checked: int
        :param rot: Scale checkbox changed
        :type rot: bool
        :param trans: Scale checkbox changed
        :type trans: bool
        :param scale: Scale checkbox changed
        :type scale: bool
        """
        if trans:
            if not self.properties.translateCheckBox.value:
                return
        if rot:
            if not self.properties.rotateCheckBox.value:
                return
        if scale:
            if not self.properties.scaleCheckBox.value:
                return
        self.properties.matrixCheckBox.value = False
        self.updateFromProperties()

    # ------------------
    # MENUS
    # ------------------

    def buildSourceMenu(self):
        """Builds the attributes in the source menu"""
        icon = "plugMale"
        attrs = attributes.listConnectableAttrsSel(selectionIndex=0)
        modeList = list()
        if not attrs:  # Show No Obj Selected
            modeList.append([icon, "No Obj Selected"])
        else:  # Build the attribute list
            for attr in attrs:
                modeList.append([icon, attr])
        # Build the menu
        self.currentWidget().sourceAttrMenu.actionConnectList(modeList)

    def buildDestinationMenu(self):
        """Builds the attributes in the destination/target menu"""
        icon = "plugFemale"
        attrs = attributes.listConnectableAttrsSel(selectionIndex=1)
        modeList = list()
        if not attrs:  # Show No Obj Selected
            attrs = attributes.listConnectableAttrsSel(selectionIndex=0)  # search first object
            if not attrs:
                modeList.append([icon, "No Obj Selected"])
                om2.MGlobal.displayWarning("Please select object/s")
                return
        for attr in attrs:
            modeList.append([icon, attr])
        # Build the menu
        self.currentWidget().destinationAttrMenu.actionConnectList(modeList)

    def setSourceText(self):
        """After the menu has been clicked set the text to the Source text box"""
        self.properties.sourceAttrTxt.value = self.currentWidget().sourceAttrMenu.currentMenuItem()
        self.updateFromProperties()

    def setDestinationTxt(self):
        """After the menu has been clicked set the text to the Destination/Target text box"""
        self.properties.destinationAttrTxt.value = self.currentWidget().destinationAttrMenu.currentMenuItem()
        self.updateFromProperties()

    def sourceChannelBox(self):
        """Gets the selected attribute from the channel box and sets it in the driver text box"""
        attrs = attributes.getChannelBoxAttrs(message=True)
        if not attrs:  # message already reported
            return
        self.properties.sourceAttrTxt.value = attrs[0]
        self.updateFromProperties()

    def destinationChannelBox(self):
        """Gets the selected attribute from the channel box and sets it in the driven text box"""
        attrs = attributes.getChannelBoxAttrs(message=True)
        if not attrs:  # message already reported
            return
        self.properties.destinationAttrTxt.value = attrs[0]
        self.updateFromProperties()

    # ------------------
    # LOGIC SRT CONNECTIONS
    # ------------------

    @toolsetwidgetmaya.undoDecorator
    def makeConnectionsPressed(self):
        """Connects Translate, Rotate and Scale depending on the GUI
        """
        translate = self.properties.translateCheckBox.value
        rotate = self.properties.rotateCheckBox.value
        scale = self.properties.scaleCheckBox.value
        matrix = self.properties.matrixCheckBox.value
        if not translate and not rotate and not scale and not matrix:
            om2.MGlobal.displayWarning("Nothing checked.  Please check a checkbox to connect")
            return
        connections.makeSrtConnectionsObjsSel(translate=translate,
                                              rotation=rotate,
                                              scale=scale,
                                              matrix=matrix)
        return
        # API code disabled, just not using due to lack of user warnings
        exe = executor.Executor()
        if self.properties.translateCheckBox.value:
            exe.execute("zoo.maya.connect.selection.localsrt", translate=True, rotate=False, scale=False)
        if self.properties.rotateCheckBox.value:
            exe.execute("zoo.maya.connect.selection.localsrt", translate=False, rotate=True, scale=False)
        if self.properties.scaleCheckBox.value:
            exe.execute("zoo.maya.connect.selection.localsrt", translate=False, rotate=False, scale=True)

    @toolsetwidgetmaya.undoDecorator
    def deleteConnectionsPressed(self):
        """Deletes attributes between the first selected objects and all others

        Will disconnect attributes in th check box section in the GUI, if there are connections
        """
        connections.delSrtConnectionsObjsSel(translate=self.properties.translateCheckBox.value,
                                             rotation=self.properties.rotateCheckBox.value,
                                             scale=self.properties.scaleCheckBox.value,
                                             matrix=self.properties.matrixCheckBox.value)

    # ------------------
    # LOGIC CUSTOM CONNECTIONS
    # ------------------

    @toolsetwidgetmaya.undoDecorator
    def makeCustomConnections(self):
        """Makes a custom connection user warning checks from the GUI

        Select multiple objects, the first is the source and the other objects are treated as targets
        """
        sourceAttr = self.properties.sourceAttrTxt.value
        targetAttr = self.properties.destinationAttrTxt.value
        connections.makeConnectionAttrsOrChannelBox(driverAttr=sourceAttr,
                                                    drivenAttr=targetAttr)

    @toolsetwidgetmaya.undoDecorator
    def deleteCustomConnections(self):
        """Deletes a custom connection as per the custom attributes in the GUI

        Select multiple objects, the first is the source and the other objects are treated as targets
        """
        sourceAttr = self.properties.sourceAttrTxt.value
        targetAttr = self.properties.destinationAttrTxt.value
        connections.breakConnectionAttrsOrChannelBox(sourceAttr, targetAttr, message=True)

    # ------------------
    # LOGIC SWAP CONNECTIONS
    # ------------------

    @toolsetwidgetmaya.undoDecorator
    def swapDriverConnectionsPressed(self):
        """Swaps the driver object to a new object, select two objects, the last object should have the connections
        """
        connections.swapConnectionSelected(driver=True, message=True)
        return
        # API code disabled, just not using due to lack of user warnings
        exe = executor.Executor()
        exe.execute("zoo.maya.connections.swap.all")

    @toolsetwidgetmaya.undoDecorator
    def swapDrivenConnectionsPressed(self):
        """Swaps the driver object to a new object, select two objects, the last object should have the connections
        """
        connections.swapConnectionSelected(driver=False, message=True)

    @toolsetwidgetmaya.undoDecorator
    def swapDirectionConnections(self):
        """Swaps the connection direction between two objects
        """
        connections.swapConnectionDirectionSel()

    @toolsetwidgetmaya.undoDecorator
    def breakDrivenConnectionsAll(self):
        """Breaks the connections of a driven object.
        Will break all, but if channel box selection then will break the selected
        """
        connections.breakAllDrivenOrChannelBoxSel()


    # ------------------
    # LOGIC COPY PASTE CONNECTIONS
    # ------------------

    @toolsetwidgetmaya.undoDecorator
    def copyDrivenConnections(self):
        """Copies to the clip board any incoming connections from the first selected obj"""
        self.sourceObjAttrs, self.destinationAttrs = connections.copyDrivenConnectedAttrsSel()

    @toolsetwidgetmaya.undoDecorator
    def pasteDrivenConnections(self):
        """Pastes from the clip board incoming connections from self.sourceObjAttrs and self.destinationAttrs"""
        if not self.sourceObjAttrs:
            om2.MGlobal.displayWarning("Nothing in the clipboard to paste.  Please copy attributes first.")
            return
        connections.pasteDrivenConnectedAttrsSel(self.sourceObjAttrs, self.destinationAttrs)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for uiInstance in self.uiInstanceList:
            # SRT Connections
            uiInstance.makeConnectionsBtn.clicked.connect(self.makeConnectionsPressed)
            uiInstance.deleteConnectionsBtn.clicked.connect(self.deleteConnectionsPressed)
            # Checkbox UI Changes
            uiInstance.matrixCheckBox.stateChanged.connect(self.matrixChecked)
            uiInstance.translateCheckBox.stateChanged.connect(partial(self.srtCheckboxChecked, trans=True))
            uiInstance.rotateCheckBox.stateChanged.connect(partial(self.srtCheckboxChecked, rot=True))
            uiInstance.scaleCheckBox.stateChanged.connect(partial(self.srtCheckboxChecked, scale=True))
            # Custom Connections
            uiInstance.connectCustomBtn.clicked.connect(self.makeCustomConnections)
            uiInstance.deleteCustomConnectionsBtn.clicked.connect(self.deleteCustomConnections)
            # Menu modes dynamic list attributes
            uiInstance.sourceAttrMenu.aboutToShow.connect(self.buildSourceMenu)
            uiInstance.sourceAttrMenu.menuChanged.connect(self.setSourceText)
            uiInstance.destinationAttrMenu.aboutToShow.connect(self.buildDestinationMenu)
            uiInstance.destinationAttrMenu.menuChanged.connect(self.setDestinationTxt)
            # Menu modes - Channel box
            uiInstance.channelBoxSrcAttrMenu.menuChanged.connect(self.sourceChannelBox)
            uiInstance.channelBoxDstAttrMenu.menuChanged.connect(self.destinationChannelBox)
        # Swap Connections
        self.advancedWidget.swapConnectDriverBtn.clicked.connect(self.swapDriverConnectionsPressed)
        self.advancedWidget.swapConnectDrivenBtn.clicked.connect(self.swapDrivenConnectionsPressed)
        self.advancedWidget.swapConnectDirectionBtn.clicked.connect(self.swapDirectionConnections)
        # Copy Paste Driven Connections
        self.advancedWidget.copyTargetsBtn.clicked.connect(self.copyDrivenConnections)
        self.advancedWidget.pasteTargetsBtn.clicked.connect(self.pasteDrivenConnections)
        self.advancedWidget.deleteDrivenBtn.clicked.connect(self.breakDrivenConnectionsAll)


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
        # --------------------------------
        # SRT Title Label
        # --------------------------------
        toolTip = "SRT (Scale Rotation and Translate) and Matrix auto setup connections"
        self.srtConnectionLabelDiv = elements.LabelDivider(text="SRT & Matrix Connection", toolTip=toolTip, bold=True)
        # Check Boxes ---------------------------------------
        delMessage = "To break, both the driver and driven need to be selected "
        toolTip = "Connect or break all translate attributes \n{}".format(delMessage)
        self.translateCheckBox = elements.CheckBox(label="Translate", checked=True, toolTip=toolTip)
        toolTip = "Connect or break all rotation attributes \n{}".format(delMessage)
        self.rotateCheckBox = elements.CheckBox(label="Rotate", checked=True, toolTip=toolTip)
        toolTip = "Connect or break all scale attributes \n{}".format(delMessage)
        self.scaleCheckBox = elements.CheckBox(label="Scale", checked=True, toolTip=toolTip)
        toolTip = "Connect or break the attributes .matrix to .offsetParentMatrix\n" \
                  "Only Maya 2020 and above. This will affect rotation, scale and \n" \
                  "translate without affecting the target's SRT attributes \n{}".format(delMessage)
        self.matrixCheckBox = elements.CheckBox(label="Matrix", checked=False, toolTip=toolTip)
        if MAYA_VERSION < 2020:
            self.matrixCheckBox.hide()
        # Make Connections Button ---------------------------------------
        toolTip = "Select two or more transform objects \n" \
                  "  1. Driver Object \n" \
                  "  2. Driven Object/s \n" \
                  "The objects will be connected via the GUI's check box attributes"
        self.makeConnectionsBtn = elements.styledButton("Make Connections",
                                                        icon="connectionSRT",
                                                        toolTip=toolTip,
                                                        style=uic.BTN_DEFAULT)
        # Delete Connections Button ---------------------------------------
        toolTip = "Breaks attribute connections between two objects if they exist. \n" \
                  "  1. Select two or more connected objects \n" \
                  "  2. Check the attributes to break in the GUI check boxes \n" \
                  "  3. Run \n" \
                  "Matching attributes will be broken"
        self.deleteConnectionsBtn = elements.styledButton("",
                                                          icon="trash",
                                                          toolTip=toolTip,
                                                          style=uic.BTN_DEFAULT)
        # --------------------------------
        # Custom Title Label
        # --------------------------------
        labelInfo = "Note: \n" \
                    "  - Click the label for full list of available attributes. \n" \
                    "  - Right Click to fill from channel box selection \n" \
                    "  - Leave the text box empty, will try to use channel box selection"
        toolTip = "Connect attributes of any type.  \n{}".format(labelInfo)
        self.customConnectionLabelDiv = elements.LabelDivider(text="Custom Connection", toolTip=toolTip)
        # Source and Destination Menus -----------------------------------
        self.sourceAttrMenu = elements.ExtendedMenu(searchVisible=True)
        self.destinationAttrMenu = elements.ExtendedMenu(searchVisible=True)
        self.channelBoxDstAttrMenu = elements.ExtendedMenu(searchVisible=False)
        self.channelBoxSrcAttrMenu = elements.ExtendedMenu(searchVisible=False)
        # Source Custom Attribute ---------------------------------------
        toolTip = "The driver attribute name. \n" \
                  "The driver object will be the first object in the selection.\n\n" \
                  "{}".format(labelInfo)
        self.sourceAttrTxt = elements.StringEdit(label="Driver",
                                                 editPlaceholder="attributeName",
                                                 labelRatio=2,
                                                 editRatio=5,
                                                 toolTip=toolTip)
        # Menu Attach ---
        channelBoxMenuSrc = [("plugMale", "From Channel Box Selection")]
        self.sourceAttrTxt.setMenu(self.channelBoxSrcAttrMenu, modeList=channelBoxMenuSrc)  # right click channel box
        self.sourceAttrTxt.setMenu(self.sourceAttrMenu, mouseButton=QtCore.Qt.LeftButton)  # left click for dynamic menu
        # Destination Custom Attribute ---------------------------------------
        toolTip = "The driven attribute name, from the second object in the selection. \n" \
                  "The driven object/s will be all *other* selected objects, not the first. \n\n{}".format(labelInfo)
        self.destinationAttrTxt = elements.StringEdit(label="Driven",
                                                      editPlaceholder="attributeName",
                                                      labelRatio=2,
                                                      editRatio=5,
                                                      toolTip=toolTip)
        # Menu Attach ---
        channelBoxMenuDst = [("plugFemale", "From Channel Box Selection")]
        self.destinationAttrTxt.setMenu(self.channelBoxDstAttrMenu, modeList=channelBoxMenuDst)  # right click chnl bx
        self.destinationAttrTxt.setMenu(self.destinationAttrMenu, mouseButton=QtCore.Qt.LeftButton)  # left click
        # Custom Create Connections Button ---------------------------------------
        toolTip = "Connects between user inputted attribute/s\n" \
                  "  1. Enter the Driver and Driven attribute names, or select in channel box \n" \
                  "  2. Select two or more objects \n" \
                  "  3. The first object will be the Driver Object \n" \
                  "  4. Other objects will be Driven Object/s \n" \
                  "The Driver attribute will be connected to the Driven/s attributes."
        self.connectCustomBtn = elements.styledButton("Connect Custom Or Channel Box",
                                                      icon="connectionSRT",
                                                      toolTip=toolTip,
                                                      style=uic.BTN_DEFAULT)
        # Delete Custom Connections Button ---------------------------------------
        toolTip = "Breaks the custom connection between two selected objects if it exists. \n" \
                  "  1. Select two or more connected objects \n" \
                  "  2. Enter the Driver and Driven attribute names, or select in channel box \n" \
                  "  3. Run \n" \
                  "Connections that match the attributes will be broken"
        self.deleteCustomConnectionsBtn = elements.styledButton("",
                                                                icon="trash",
                                                                toolTip=toolTip,
                                                                style=uic.BTN_DEFAULT)
        if uiMode == UI_MODE_ADVANCED:
            # --------------------------------
            # Swap Title Label
            # --------------------------------
            toolTip = "Swap connections between objects and reverse connection direction"
            self.swapLabelDiv = elements.LabelDivider(text="Swap Connections", toolTip=toolTip)
            # Swap Connections Button ---------------------------------------
            toolTip = "Transfers the driver object's connections to a new object \n" \
                      "  1. Select a current driver object \n" \
                      "  2. Select a new driven object \n" \
                      "  3. Run \n" \
                      "The driver connections will switch to the new object"
            self.swapConnectDriverBtn = elements.styledButton("Swap Driver",
                                                              icon="connectionSwap_64",
                                                              toolTip=toolTip,
                                                              style=uic.BTN_DEFAULT)
            # Swap Connections Button ---------------------------------------
            toolTip = "Transfers a driven object's connection to a new object \n" \
                      "  1. Select a current driver object \n" \
                      "  2. Select a new driven object \n" \
                      "  3. Run \n" \
                      "The driven object's connections will be switched to the new object"
            self.swapConnectDrivenBtn = elements.styledButton("Swap Driven",
                                                              icon="connectionSwap_64",
                                                              toolTip=toolTip,
                                                              style=uic.BTN_DEFAULT)
            # Swap Connections Button ---------------------------------------
            toolTip = "Swaps the connection direction between objects \n" \
                      "  1. Select two objects or nodes \n" \
                      "  2. Run \n" \
                      "Any shared connections will be reversed in direction"
            self.swapConnectDirectionBtn = elements.styledButton("Swap Direction",
                                                                 icon="connectionSwap_64",
                                                                 toolTip=toolTip,
                                                                 style=uic.BTN_DEFAULT)
            # --------------------------------
            # Copy Paste Title Label
            # --------------------------------

            toolTip = "Copy and paste driven connections to other objects or nodes"
            self.copyPasteLabelDiv = elements.LabelDivider(text="Copy Paste Connections", toolTip=toolTip)
            # Copy Driven Targets Button ---------------------------------------
            toolTip = "Copies incoming connections \n" \
                      "  1. Select a driven object \n" \
                      "  2. Run \n" \
                      "The driven connections will be copied to the clipboard"
            self.copyTargetsBtn = elements.styledButton("Copy Driven",
                                                        icon="copy2",
                                                        toolTip=toolTip,
                                                        style=uic.BTN_DEFAULT)
            # Paste Driven Targets Button ---------------------------------------
            toolTip = "Pastes incoming connections from the clipboard \n" \
                      "  1. Copy driven connections to clipboard \n" \
                      "  2. Select new object/s to paste the connections onto \n" \
                      "  3. Run \n" \
                      "Connections will be pasted onto the new object/s"
            self.pasteTargetsBtn = elements.styledButton("Paste Driven",
                                                         icon="paste",
                                                         toolTip=toolTip,
                                                         style=uic.BTN_DEFAULT)
            # Delete Driven Targets Button ---------------------------------------
            toolTip = "Breaks all incoming connections, same as right click > break connections. \n" \
                      "If there is a channel box selection it will only break the highlighted attributes."
            self.deleteDrivenBtn = elements.styledButton("Break Driven",
                                                         icon="trash",
                                                         toolTip=toolTip,
                                                         style=uic.BTN_DEFAULT)


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
        mainLayout = elements.vBoxLayout(parent, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SLRG)
        # Check Boxes ---------------------------------------
        checkBoxLayout = elements.hBoxLayout(margins=(uic.SVLRG, 0, uic.SVLRG, 0))
        checkBoxLayout.addWidget(self.translateCheckBox)
        checkBoxLayout.addWidget(self.rotateCheckBox)
        checkBoxLayout.addWidget(self.scaleCheckBox)
        checkBoxLayout.addWidget(self.matrixCheckBox)
        # SRT Buttons SRT ---------------------------------------
        buttonSrtLayout = elements.hBoxLayout()
        buttonSrtLayout.addWidget(self.makeConnectionsBtn, 9)
        buttonSrtLayout.addWidget(self.deleteConnectionsBtn, 1)
        # Text Box Custom ---------------------------------------
        textBoxCustomLayout = elements.hBoxLayout(spacing=uic.SVLRG)
        textBoxCustomLayout.addWidget(self.sourceAttrTxt, 1)
        textBoxCustomLayout.addWidget(self.destinationAttrTxt, 1)
        # Buttons Custom ---------------------------------------
        buttonCustomLayout = elements.hBoxLayout()
        buttonCustomLayout.addWidget(self.connectCustomBtn, 9)
        buttonCustomLayout.addWidget(self.deleteCustomConnectionsBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(self.srtConnectionLabelDiv)
        mainLayout.addLayout(checkBoxLayout)
        mainLayout.addLayout(buttonSrtLayout)
        mainLayout.addWidget(self.customConnectionLabelDiv)
        mainLayout.addLayout(textBoxCustomLayout)
        mainLayout.addLayout(buttonCustomLayout)


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
        mainLayout = elements.vBoxLayout(parent, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SLRG)
        # Check Boxes ---------------------------------------
        checkBoxLayout = elements.hBoxLayout(margins=(uic.SVLRG, 0, uic.SVLRG, 0))
        checkBoxLayout.addWidget(self.translateCheckBox)
        checkBoxLayout.addWidget(self.rotateCheckBox)
        checkBoxLayout.addWidget(self.scaleCheckBox)
        checkBoxLayout.addWidget(self.matrixCheckBox)
        # SRT Buttons SRT ---------------------------------------
        buttonSrtLayout = elements.hBoxLayout()
        buttonSrtLayout.addWidget(self.makeConnectionsBtn, 9)
        buttonSrtLayout.addWidget(self.deleteConnectionsBtn, 1)
        # Text Box Custom ---------------------------------------
        textBoxCustomLayout = elements.hBoxLayout(spacing=uic.SVLRG)
        textBoxCustomLayout.addWidget(self.sourceAttrTxt, 1)
        textBoxCustomLayout.addWidget(self.destinationAttrTxt, 1)
        # Buttons Custom ---------------------------------------
        buttonCustomLayout = elements.hBoxLayout()
        buttonCustomLayout.addWidget(self.connectCustomBtn, 9)
        buttonCustomLayout.addWidget(self.deleteCustomConnectionsBtn, 1)
        # Swap Buttons ---------------------------------------
        buttonSwapLayout = elements.hBoxLayout()
        buttonSwapLayout.addWidget(self.swapConnectDriverBtn, 1)
        buttonSwapLayout.addWidget(self.swapConnectDrivenBtn, 1)
        buttonSwapLayout.addWidget(self.swapConnectDirectionBtn, 1)
        # Copy Paste Buttons ---------------------------------------
        copyPasteBtnLayout = elements.hBoxLayout()
        copyPasteBtnLayout.addWidget(self.copyTargetsBtn, 1)
        copyPasteBtnLayout.addWidget(self.pasteTargetsBtn, 1)
        copyPasteBtnLayout.addWidget(self.deleteDrivenBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(self.srtConnectionLabelDiv)
        mainLayout.addLayout(checkBoxLayout)
        mainLayout.addLayout(buttonSrtLayout)
        mainLayout.addWidget(self.customConnectionLabelDiv)
        mainLayout.addLayout(textBoxCustomLayout)
        mainLayout.addLayout(buttonCustomLayout)
        mainLayout.addWidget(self.swapLabelDiv)
        mainLayout.addLayout(buttonSwapLayout)
        mainLayout.addWidget(self.copyPasteLabelDiv)
        mainLayout.addLayout(copyPasteBtnLayout)
