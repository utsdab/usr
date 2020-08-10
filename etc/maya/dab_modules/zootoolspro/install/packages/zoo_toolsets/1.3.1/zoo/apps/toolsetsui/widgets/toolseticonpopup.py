import math

from Qt import QtCore, QtWidgets

from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import dialog, flowlayout
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt.widgets import extendedbutton
from zoo.libs.maya.qt import mayaui


class ToolsetIconPopup(dialog.Dialog):
    """ The toolset icon popup with all the toolsets in a dialog box

    :param parent: Parent
    :param width:
    :param height:
    :param iconSize:
    :param showOnInitialize:
    :param toolsetRegistry:
    """

    def __init__(self, toolsetFrame, parent=None, width=50, height=50, iconSize=20, showOnInitialize=False, toolsetRegistry=None):

        super(ToolsetIconPopup, self).__init__("Title", width=width, height=height, parent=parent,
                                               showOnInitialize=showOnInitialize)

        self.mainLayout = elements.vBoxLayout(self, margins=(0, 0, 0, 0), spacing=0)
        self.toolsetFrame = toolsetFrame  # Tool

        self.searchEdit = QtWidgets.QLineEdit(self)

        self.tearOffWidget = TearOffWidget(parent=mayaui.getMayaWindow())

        self.toolsetRegistry = toolsetRegistry
        self.nameLabel = QtWidgets.QLabel(self)
        self.iconRowSpacing = utils.dpiScale(5)

        self.defaultWindowFlags = self.windowFlags()
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.btnColumns = 8
        self.iconSize = iconSize

        self.buttons = []
        self.initUi()
        self.connections()

    def connections(self):
        self.tearOffWidget.clicked.connect(lambda: self.setTearOff(True))

    def setButtonColumns(self, col):
        self.btnColumns = col

    def initUi(self):
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Popup)
        self.buttons = []

        self.initSearchEdit()
        self.nameLabel.setIndent(utils.dpiScale(3))

        # Contents Layout
        contentsLayout = elements.vBoxLayout(self, margins=(0, 0, 0, 0), spacing=0)
        contentsLayout.setContentsMargins(utils.dpiScale(5), 0, utils.dpiScale(5), utils.dpiScale(10))
        contentsLayout.setSpacing(utils.dpiScale(5))

        contentsLayout.addWidget(self.nameLabel)
        contentsLayout.addLayout(self.iconFlowLayout())

        # Main Layout settings
        self.setLayout(self.mainLayout)
        self.mainLayout.addWidget(self.tearOffWidget)
        self.mainLayout.addWidget(self.searchEdit)
        self.mainLayout.addLayout(contentsLayout)

        self.mainLayout.setSpacing(utils.dpiScale(6))
        self.mainLayout.addStretch(1)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setContentsMargins(0, 0, 0, 0)

    def resizeDialog(self):
        """ Resize the dialog based on the size hint

        :return:
        """
        self.resize(self.sizeHint())

    def sizeHint(self):
        """ Change the size hint to resize based on the buttons in the icon popup

        :return:
        """

        rows = math.ceil(len(self.buttons) / self.btnColumns)
        spacing = self.iconLayout.spacing()
        paddingX = utils.dpiScale(12)
        paddingY = utils.dpiScale(8)

        width = (self.buttons[0].sizeHint().width() * self.btnColumns) + \
                spacing * (self.btnColumns-1) + paddingX

        height = (self.buttons[0].sizeHint().height() * rows) + \
                 spacing * (rows-1) + paddingY + self.minimumHeight()

        return QtCore.QSize(width, height)

    def initSearchEdit(self):
        """ Search edit to filter out the button

        :return:
        """

        self.searchEdit.setPlaceholderText("Search...")
        self.searchEdit.textChanged.connect(self.updateSearch)

    def iconFlowLayout(self):
        """ Icon flow layout for the buttons

        :return:
        """
        self.iconLayout = flowlayout.FlowLayout(spacingX=1, spacingY=2)
        self.iconLayout.setContentsMargins(0, 0, 0, 0)

        for g in self.toolsetRegistry.toolsetGroups:
            groupType = g['type']
            toolsets = self.toolsetRegistry.toolsets(groupType)

            for t in toolsets:

                btn = self.newButton(t, self.nameLabel)

                self.buttons.append(btn)
                self.iconLayout.addWidget(btn)

        return self.iconLayout

    def setTearOff(self, tearOff):
        """ Set Tear Off

        Tear off the window and add its window frame back if tearOff is true, otherwise turn it back into a
        popup

        :param tearOff:
        :return:
        """
        if tearOff:
            self.setParent(mayaui.getMayaWindow())
            self.setWindowFlags(self.defaultWindowFlags)
            self.tearOffWidget.hide()
            self.show()
            self.resize(self.width(), self.minimumSize().height())

        else:
            self.tearOffWidget.show()
            self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Popup)

    def updateSearch(self, searchString):
        """ Filter buttons by search string

        :param searchString:
        :return:
        """
        searchString = searchString or ""
        for b in self.buttons:
            if searchString.lower() in b.name.lower() or searchString == "":
                b.show()
            else:
                b.hide()

    def newGroup(self, group):
        """ Add a group with each as a row

        :param group:
        :return:
        """
        groupType = group['type']
        toolsets = self.toolsetRegistry.toolsets(groupType)
        layout = elements.hBoxLayout(self, margins=(0, 0, 0, 0), spacing=0)

        for t in toolsets:
            btn = self.newButton(t, self.nameLabel)
            self.buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch(1)

        return layout

    def newButton(self, toolset, nameLabel=None):
        """ Add a new button sets the settings and return so we can add it to the group

        :param toolset:
        :param color:
        :param nameLabel:
        :return:
        """
        color = self.toolsetRegistry.toolsetColor(toolset.id)
        btn = ToolsetIconButton(toolset.uiData['icon'], color)
        btn.setName(toolset.uiData['label'])

        if nameLabel is not None:
            btn.setLabelWidget(nameLabel)

        btn.setToolTip(toolset.uiData['label'])
        btn.setProperty('color', color)
        btn.setProperty('toolsetId', toolset.id)
        activated = True
        btn.leftClicked.connect(lambda: self.toolsetFrame.toggleToolset(toolset.id,activated))
        btn.middleClicked.connect(lambda: self.toolsetFrame.toggleToolset(toolset.id, not activated))

        btn.setIconSize(QtCore.QSize(self.iconSize, self.iconSize))
        return btn

    def show(self):
        self.searchEdit.setText("")
        super(ToolsetIconPopup, self).show()
        self.searchEdit.setFocus()

    def updateColors(self, actives):
        """ Updates colors based on if it active or not. Generally becomes dark if it is active

        todo: What is this doing exactly? doesnt seem to affect anything as far as I can tell
        And it is getting called a lot, can change the colors to bright green, and nothing happens on reload

        :param actives: List of toolsetIds
        :type actives: list
        :return:
        """
        for item in self.iconLayout.items():
            wgt = item.widget()
            if wgt.property('toolsetId') in actives:
                wgt.setIconColor((120, 120, 120))
            else:
                wgt.setIconColor(tuple(wgt.property('color')))


class TearOffWidget(QtWidgets.QPushButton):
    """
    Tear off widget so we can detach the menu and turn it into a popup dialog
    """

    def __init__(self, parent=None):
        super(TearOffWidget, self).__init__(parent=parent)
        self.initUi()
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed)

    def initUi(self):
        self.setFixedHeight(utils.dpiScale(15))

        # Tear off pattern
        patternChars = ":::::::"
        dottedPattern = ""
        for i in range(1, 50):
            dottedPattern += patternChars
        self.setText(dottedPattern)


class ToolsetIconButton(extendedbutton.ExtendedButton):
    """ Toolset Icon Button

    The icon button that represents a toolset. When moused over it will
    change the label based on the name

    Example:

    .. code-block: python
        btn = ToolsetIconButton("magic", color=(255,255,255))
        btn.setName("Toolset Icon Button")
        btn.setLabelWidget(QtWidgets.QLabel())

    """
    def __init__(self, iconName, color):
        super(ToolsetIconButton, self).__init__()
        self.setIconByName(iconName, colors=color, size=24, colorOffset=50)
        self.nameLabel = None  # type: QtWidgets.QLabel
        self.name = None  # Name of toolset

    def setLabelWidget(self, label):
        """ The label to change when moused over

        :param label:
        :return:
        """
        self.nameLabel = label

    def setName(self, name):
        self.name = name

    def enterEvent(self, event):
        super(ToolsetIconButton, self).enterEvent(event)
        if self.nameLabel:
            self.nameLabel.setText(self.name)

    def leaveEvent(self, event):
        super(ToolsetIconButton, self).leaveEvent(event)
        if self.nameLabel:
            self.nameLabel.setText("")




