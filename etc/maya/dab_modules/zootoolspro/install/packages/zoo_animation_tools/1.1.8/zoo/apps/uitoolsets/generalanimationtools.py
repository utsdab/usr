from Qt import QtWidgets

import maya.api.OpenMaya as om2

from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.maya.cmds.general import undodecorator

ROTATE_ORDERS = ["xyz", "yzx", "zxy", "xzy", "yxz", "zyx"]



class GeneralAnimationTools(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "generalAnimationTools"
    uiData = {"label": "General Animation Tools",
              "icon": "key",
              "tooltip": "Assorted Maya animation tools",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-general-animation-tools"
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
    # RIGHT CLICK TOOLSET ICON
    # ------------------

    def actions(self):
        """Right click menu on the main toolset tool icon"""
        return [{"type": "action",
                 "name": "rotOrderXYZ",
                 "label": "XYZ Rot Order",
                 "icon": "key",
                 "tooltip": ""},
                {"type": "action",
                 "name": "rotOrderYZX",
                 "label": "YZX Rot Order",
                 "icon": "key",
                 "tooltip": ""},
                {"type": "action",
                 "name": "rotOrderZXY",
                 "label": "ZXY Rot Order",
                 "icon": "key",
                 "tooltip": ""},
                {"type": "action",
                 "name": "rotOrderXZY",
                 "label": "XZY Rot Order",
                 "icon": "key",
                 "tooltip": ""},
                {"type": "action",
                 "name": "rotOrderYXZ",
                 "label": "YXZ Rot Order",
                 "icon": "key",
                 "tooltip": ""},
                {"type": "action",
                 "name": "rotOrderZYX",
                 "label": "ZYX Rot Order",
                 "icon": "key",
                 "tooltip": ""}]

    def executeActions(self, action):
        name = action["name"]
        if name == "rotOrderXYZ":
            self.changeRotOrder(newRotOrder="xyz")
        elif name == "rotOrderYZX":
            self.changeRotOrder(newRotOrder="yzx")
        elif name == "rotOrderZXY":
            self.changeRotOrder(newRotOrder="zxy")
        elif name == "rotOrderXZY":
            self.changeRotOrder(newRotOrder="xzy")
        elif name == "rotOrderYXZ":
            self.changeRotOrder(newRotOrder="yxz")
        elif name == "rotOrderZYX":
            self.changeRotOrder(newRotOrder="zyx")

    # ------------------
    # UI WIDGETS
    # ------------------

    def widgetsAll(self, parent):
        """Builds all widgets for the compact UI

        :param parent: the parent widget for these widgets
        :type parent: object
        """
        # Name Line Edit
        toolTip = "Change Rotation Order - Will change the xyz rotation order on selected transforms\n" \
                  "If objects have keyframes will change each key to compensate for the correct rotation.\n" \
                  "Credit Morgan Loomis - http://morganloomis.com \n" \
                  "`third_party_community` package must be installed."
        self.changeRotOrderCombo = elements.ComboBoxRegular(label="Change Rotation Order",
                                                            items=(ROTATE_ORDERS),
                                                            setIndex=self.properties.changeRotOrderCombo.value,
                                                            parent=parent,
                                                            toolTip=toolTip)
        self.linkProperty(self.changeRotOrderCombo, "changeRotOrderCombo")
        # Change Rot Order Button
        toolTip = ""
        self.changeRotOrderBtn = elements.styledButton("",
                                                       "key",
                                                       toolTip=toolTip,
                                                       parent=parent,
                                                       minWidth=uic.BTN_W_ICN_MED)

    # ------------------
    # UI LAYOUT
    # ------------------

    def compactLayout(self, parent):
        """Builds the layouts for the compact UI and adds widgets.

        :param parent: the parent widget for these widgets
        :type parent: object
        """
        # Main Layout
        contentsLayout = elements.vBoxLayout(parent,
                                             margins=(uic.WINSIDEPAD,
                                                      uic.WINBOTPAD,
                                                      uic.WINSIDEPAD,
                                                      uic.WINBOTPAD),
                                             spacing=uic.SREG)
        parent.setLayout(contentsLayout)
        # change rot order layout
        changeRotLayout = elements.hBoxLayout(parent)
        changeRotLayout.addWidget(self.changeRotOrderCombo, 8)
        changeRotLayout.addWidget(self.changeRotOrderBtn, 1)

        # add to main layout
        contentsLayout.addLayout(changeRotLayout)
        contentsLayout.addStretch(1)

    # ------------------
    # MAIN LOGIC
    # ------------------

    @toolsetwidgetmaya.undoDecorator
    def changeRotOrder(self):
        """Main function, uses the GUI to change rotation order of the selected objs in Maya
        The logic here is an open source script by Morgan Loomis, see rotateorder for more info.
        """
        try:
            from zoo.libs.morganloomis import rotateorder
            newRotOrder = rotateorder.ROTATE_ORDERS[self.properties.changeRotOrderCombo.value]
            rotateorder.convertRotateOrderSelected(roo=newRotOrder, message=True)
        except:
            om2.MGlobal.displayWarning("The package `third_party_community` must be installed for "
                                       "Change Rotation Order.")

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
        return [{"name": "changeRotOrderCombo", "value": 0}]

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        self.changeRotOrderBtn.clicked.connect(self.changeRotOrder)
