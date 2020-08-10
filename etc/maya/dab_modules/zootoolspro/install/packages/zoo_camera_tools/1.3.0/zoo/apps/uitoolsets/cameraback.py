from Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

SENSOR_AREA = "sensor_area"
RESOLUTION = "resolution"

CAM_DICT = {"ARRI ALEXIA Mini": {"4K UHD": {SENSOR_AREA: (26.40, 14.85),
                                            RESOLUTION: (3840, 2160)},
                                 "3.4K Open Gate": {SENSOR_AREA: (28.25, 18.17),
                                                    RESOLUTION: (3424, 2202)}},
            "Canon EOS 5D Mark IV": {"4k": {SENSOR_AREA: (36.00, 20.25),
                                            RESOLUTION: (4096, 2160)},
                                     "1080p": {SENSOR_AREA: (36.00, 20.25),
                                               RESOLUTION: (1920, 1080)},
                                     "720p": {SENSOR_AREA: (36.00, 20.25),
                                              RESOLUTION: (1280, 720)}}}


class CameraBack(object):  # toolsetwidget.ToolsetWidgetMaya
    id = "cameraBack"
    info = "A UI that controls the type of camera, ie the sensor size."
    uiData = {"label": "Camera Back",
              "icon": "film",
              "tooltip": "A UI that controls the type of camera, ie the sensor size.",
              "defaultActionDoubleClick": False}

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        pass

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]

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
        return self.widgets()[self.displayIndex()].children()[0]

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
        return super(CameraBack, self).widgets()

    # ------------------
    # LOGIC
    # ------------------

    def buttonPressed(self):
        pass

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            pass


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
        # Camera Name ---------------------------------------
        tooltip = ""
        self.cameraString = elements.StringEdit(label="Camera Name",
                                                editText="camera1",
                                                toolTip=tooltip,
                                                editRatio=2,
                                                labelRatio=1)
        camModelList = dict.keys(CAM_DICT)
        camModelList.sort(key=str.lower)
        # Camera Model ---------------------------------------
        tooltip = ""
        self.camModelCombo = elements.ComboBoxSearchable(text="Camera Model",
                                                         toolTip=tooltip,
                                                         items=camModelList,
                                                         labelRatio=1,
                                                         boxRatio=2)
        # Camera Model ---------------------------------------
        tooltip = ""
        self.camOptionCombo = elements.ComboBoxSearchable(text="Camera Option",
                                                          toolTip=tooltip,
                                                          items=dict.keys(CAM_DICT[camModelList[0]]),
                                                          labelRatio=1,
                                                          boxRatio=2,
                                                          sortAlphabetically=True)
        # Sensor Units ---------------------------------------
        tooltip = ""
        self.sensorUnitsCombo = elements.ComboBoxRegular(label="",
                                                         toolTip=tooltip,
                                                         items=["Sensor (mm)", "Sensor (inches)"],
                                                         labelRatio=1,
                                                         boxRatio=2)
        # Sensor Size ---------------------------------------
        tooltip = ""
        self.sensorSizeMmVector = elements.VectorLineEdit(label="",
                                                          value=(36.00, 24.00),
                                                          toolTip=tooltip,
                                                          axis=("x", "y"),
                                                          labelRatio=1,
                                                          editRatio=2)
        # Suggested Resolution Size ---------------------------------------
        tooltip = ""
        self.nativeResolutionVector = elements.VectorLineEdit(label="Suggested Resolution",
                                                              value=(1920, 1080),
                                                              toolTip=tooltip,
                                                              axis=("x", "y"),
                                                              labelRatio=1,
                                                              editRatio=2)
        self.nativeResolutionVector.setEnabled(True)
        # Scene Resolution Size ---------------------------------------
        tooltip = ""
        self.sceneResolutionVector = elements.VectorLineEdit(label="Scene Resolution",
                                                             value=(1920, 1080),
                                                             toolTip=tooltip,
                                                             axis=("x", "y"),
                                                             labelRatio=1,
                                                             editRatio=2)
        # Camera Model ---------------------------------------
        tooltip = ""
        self.fitResolutionGateCombo = elements.ComboBoxRegular(label="Fit Gate",
                                                               toolTip=tooltip,
                                                               items=["Zoo Match Overscan", "Fill", "Horizontal"],
                                                               labelRatio=1,
                                                               boxRatio=2)
        # Apply Scene Film Back Button ---------------------------------------
        toolTip = ""
        self.setFilmBackSceneBtn = elements.styledButton(text="Apply All Cameras",
                                                         icon="film",
                                                         toolTip=toolTip,
                                                         style=uic.BTN_DEFAULT)
        # Apply Camera Film Back Button ---------------------------------------
        toolTip = ""
        self.setFilmBackCamBtn = elements.styledButton(text="Apply Camera",
                                                       icon="film",
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
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Button Layout ---------------------------------------
        btnLayout = elements.hBoxLayout()
        btnLayout.addWidget(self.setFilmBackCamBtn)
        btnLayout.addWidget(self.setFilmBackSceneBtn)
        # Sensor Layout ---------------------------------------
        sensorLayout = elements.hBoxLayout()
        sensorLayout.addWidget(self.sensorUnitsCombo, 1)
        sensorLayout.addWidget(self.sensorSizeMmVector, 2)
        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(self.cameraString)
        mainLayout.addWidget(self.camModelCombo)
        mainLayout.addWidget(self.camOptionCombo)
        mainLayout.addLayout(sensorLayout)
        mainLayout.addWidget(self.nativeResolutionVector)
        mainLayout.addWidget(self.sceneResolutionVector)
        mainLayout.addWidget(self.fitResolutionGateCombo)
        mainLayout.addLayout(btnLayout)


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
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(self.cameraString)
        mainLayout.addWidget(self.camModelCombo)
