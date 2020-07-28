from Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.maya.cmds.general import undodecorator

from zoo.libs.maya.cmds.animation import keyframes


class CreateTurntable(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "createTurntable"
    info = "This tool creates a turntable of the selected object or Zoo Package Asset by rotating it 360 degrees."
    defaultActionDoubleClick = True
    uiData = {"label": "Create Turntable",
              "icon": "rotateTurntable",
              "tooltip": "",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-create-turntable/"
              }

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run"""
        pass

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        parent = QtWidgets.QWidget(parent=self)
        self.widgetsAll(parent)
        self.compactLayout(parent)
        return parent

    def postContentSetup(self):
        """Last of the initialize code"""
        self.uiConnections()

    def defaultAction(self):
        """Double Click"""
        pass

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
        return [{"name": "startFrameFloatTxt", "value": 0},
                {"name": "endFrameFloatTxt", "value": 200},
                {"name": "angleOffsetFloatTxt", "value": -90},
                {"name": "spinAmountFloatTxt", "value": 360},
                {"name": "setTimeBx", "value": True},
                {"name": "reverseBx", "value": False}]

    # ------------------
    # UI WIDGETS
    # ------------------

    def widgetsAll(self, parent):
        """Builds all widgets for the compact UI

        :param parent: the parent widget for these widgets
        :type parent: object
        """
        # Start Frame Line Edit
        toolTip = ""
        self.startFrameFloatTxt = elements.FloatEdit(label="Start Frame",
                                                      editText=self.properties.startFrameFloatTxt.value,
                                                      toolTip=toolTip)
        # End Frame Line Edit
        toolTip = ""
        self.endFrameFloatTxt = elements.FloatEdit(label="End Frame",
                                                    editText=self.properties.endFrameFloatTxt.value,
                                                    toolTip=toolTip)
        # spine amount Line Edit
        toolTip = ""
        self.spinAmountFloatTxt = elements.FloatEdit(label="Spin Amount",
                                                      editText=self.properties.spinAmountFloatTxt.value,
                                                      toolTip=toolTip)
        # Start angle Offset Line Edit
        toolTip = ""
        self.angleOffsetFloatTxt = elements.FloatEdit(label="Angle Offset",
                                                       editText=self.properties.angleOffsetFloatTxt.value,
                                                       toolTip=toolTip)
        # Start angle Offset Line Edit
        toolTip = ""
        self.setTimeBx = elements.CheckBox(label="Auto Set Timerange",
                                           checked=self.properties.setTimeBx.value,
                                           parent=parent,
                                           toolTip=toolTip)
        # Start angle Offset Line Edit
        toolTip = ""
        self.reverseBx = elements.CheckBox(label="Reverse",
                                           checked=self.properties.reverseBx.value,
                                           parent=parent,
                                           toolTip=toolTip)
        # Change Rot Order Button
        toolTip = ""
        self.createTurntableBtn = elements.styledButton("Create Turntable Selected",
                                                       "rotateTurntable",
                                                          toolTip=toolTip,
                                                          parent=parent)
        # Delete Rot Order Button
        toolTip = ""
        self.deleteTurntableBtn = elements.styledButton("",
                                                       "trash",
                                                          toolTip=toolTip,
                                                          parent=parent,
                                                          minWidth=uic.BTN_W_ICN_MED)

    # ------------------
    # UI LAYOUT
    # ------------------

    def compactLayout(self, parent):
        """Builds the layouts for the compact UI and adds widgets.

        :param parent: the parent widget for these widgets
        :type parent:
        """
        # Main Layout
        contentsLayout = elements.vBoxLayout(parent,
                                                                  margins=(uic.WINSIDEPAD,
                                                     uic.WINBOTPAD,
                                                     uic.WINSIDEPAD,
                                                     uic.WINBOTPAD),
                                                                  spacing=uic.SREG)
        parent.setLayout(contentsLayout)
        # Start End layout
        startEndLayout = elements.hBoxLayout(parent)
        startEndLayout.addWidget(self.startFrameFloatTxt, 1)
        startEndLayout.addWidget(self.endFrameFloatTxt, 1)
        # Spin Amount and Angle Offset layout
        spinAndOffsetLayout = elements.hBoxLayout(parent)
        spinAndOffsetLayout.addWidget(self.spinAmountFloatTxt, 1)
        spinAndOffsetLayout.addWidget(self.angleOffsetFloatTxt, 1)
        # checkbox layout
        checkBoxLayout = elements.hBoxLayout(parent, margins=(uic.REGPAD,
                                                                                   uic.REGPAD,
                                                                                   uic.REGPAD,
                                                                                   uic.REGPAD))
        checkBoxLayout.addWidget(self.reverseBx, 1)
        checkBoxLayout.addWidget(self.setTimeBx, 1)
        # btn layout
        btnLayout = elements.hBoxLayout(parent)
        btnLayout.addWidget(self.createTurntableBtn, 8)
        btnLayout.addWidget(self.deleteTurntableBtn, 1)
        # Add to main layout
        contentsLayout.addLayout(startEndLayout)
        contentsLayout.addLayout(spinAndOffsetLayout)
        contentsLayout.addLayout(checkBoxLayout)
        contentsLayout.addLayout(btnLayout)
        contentsLayout.addStretch(1)

    # ------------------
    # MAIN LOGIC
    # ------------------

    @undodecorator.undoDecorator
    def createTurntable(self):
        """Main function, uses the GUI to change rotation order of the selected objs in Maya"""
        keyframes.turntableSelectedObj(start=self.properties.startFrameFloatTxt.value,
                                       end=self.properties.endFrameFloatTxt.value,
                                       spinValue=self.properties.spinAmountFloatTxt.value,
                                       setTimerange=self.properties.setTimeBx.value,
                                       reverse=self.properties.reverseBx.value,
                                       angleOffset=self.properties.angleOffsetFloatTxt.value)

    @undodecorator.undoDecorator
    def deleteTurntable(self):
        keyframes.deleteTurntableSelected()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        self.createTurntableBtn.clicked.connect(self.createTurntable)
        self.deleteTurntableBtn.clicked.connect(self.deleteTurntable)
