from Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.maya.cmds.general import undodecorator

from zoo.libs.maya.cmds.cameras import imageplanes


class ImagePlaneAnim(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "imagePlaneAnim"
    info = "Animates an image plane on frames 1, 2, 3, and 4 ready for character modelling"
    uiData = {"label": "Animate Image Plane",
              "icon": "animatedImagePlane",
              "tooltip": "Animates an image plane on frames 1, 2, 3, and 4 ready for character modelling.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-animate-image-plane/"}

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        pass

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced, in this case we are only building one UI mode """
        return [self.initCompactWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        parent = QtWidgets.QWidget(parent=self)
        self.widgetsAll(parent)
        self.allLayouts(parent)
        return parent

    def postContentSetup(self):
        """Last of the initialize code"""
        self.uiConnections()

    def defaultAction(self):
        """Double Click"""
        pass

    # ------------------
    # UI WIDGETS
    # ------------------

    def widgetsAll(self, parent):
        """Creates the single UI for the toolset, UI Code goes here.

        :param parent: the parent widget
        :type parent: obj
        """
        # Opacity ---------------------------------------
        toolTip = "The amount of frames to fade the image plane over, frames 3+"
        self.fadeLengthFloat = elements.FloatEdit(label="Fade Frames",
                                                editText="6",
                                                toolTip=toolTip)
        # Siz Pos ---------------------------------------
        toolTip = "The minimized scale size of the image plane on frame 1"
        self.sizeXFloat = elements.FloatEdit(label="Minimized Scale",
                                              editText="0.4",
                                              toolTip=toolTip)
        toolTip = "The image pos X offset of the image plane on frame 1"
        self.posXFloat = elements.FloatEdit(label="Screen Pos X",
                                             editText="-0.45",
                                             toolTip=toolTip)
        toolTip = "The image pos Y offset of the image plane on frame 1"
        self.posYFloat = elements.FloatEdit(label="Screen Pos Y",
                                             editText="0.3",
                                             toolTip=toolTip)
        # Create Delete Buttons ---------------------------------------
        toolTip = "Animate the selected image plane\n" \
                  "  Frame 1: Image plane is small and top left in frame\n" \
                  "  Frame 2: Image plane is far back, behind the model\n" \
                  "  Frames will then fade from transparent to opaque base on `Frame Fades` value"
        self.createBtn = elements.styledButton("Animate Image Plane", "imagePlane", parent, toolTip,
                                               style=uic.BTN_DEFAULT)

    def allLayouts(self, parent):
        """Builds the layout for the GUI.  Builds all qt layouts and adds all widgets

        :param parent: the parent widget
        :type parent: obj
        """
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(parent, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Button Layout ---------------------------------------
        gridLayout = elements.GridLayout(margins=(0, 0, 0, 0), spacing=uic.SREG)
        gridLayout.addWidget(self.fadeLengthFloat, 1, 0)
        gridLayout.addWidget(self.sizeXFloat, 1, 1)
        gridLayout.addWidget(self.posXFloat, 2, 0)
        gridLayout.addWidget(self.posYFloat, 2, 1)
        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)

        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(gridLayout)
        mainLayout.addWidget(self.createBtn)

    # ------------------
    # LOGIC
    # ------------------

    @undodecorator.undoDecorator
    def animateImagePlane(self):
        """Main function, animates the image plane as per the user settings.

        Keys 4 frames:

            Frame 1: Image plane is far back, behind the model
            Frame 2: Image plane is close to camera, in front of the model and faded
            Frames will then fade from transparent to opaque base on `Frame Fades` value

        """
        imageplanes.animateImagePlane(fadeLength=self.properties.fadeLengthFloat.value,
                                      minScale=self.properties.sizeXFloat.value,
                                      offsetX=self.properties.posXFloat.value,
                                      offsetY=self.properties.posYFloat.value)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        self.createBtn.clicked.connect(self.animateImagePlane)
