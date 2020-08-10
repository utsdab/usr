from functools import partial

from Qt import QtWidgets

from zoo.apps.toolsetsui.registry import ToolsetRegistry
from zoo.apps.toolsetsui.widgets import toolsetframe
from zoo.libs import iconlib
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt.widgets import extendedbutton, roundbutton, flowtoolbar
from zoovendor.six import string_types


class VerticalToolBar(QtWidgets.QFrame):
    def __init__(self, parent=None, themePref=None, sidePanel=None, resizerWidget=None):
        """ Vertical toolbar (currently on the right side of image browser)

        :type resizerWidget: resizerwidget.ResizerWidget
        :param parent:
        :param themePref:
        :param sidePanel:
        """
        super(VerticalToolBar, self).__init__(parent=parent)

        self.mainLayout = elements.vBoxLayout(self)
        self.setLayout(self.mainLayout)
        self.themePref = themePref
        self.sidePanel = sidePanel
        self.toolsetRegistry = ToolsetRegistry()
        self.toolsetRegistry.discoverToolsets()
        self.resizerWidget = resizerWidget

        if resizerWidget is not None:
            self.setResizerWidget(resizerWidget)

        self.toolsetFrame = toolsetframe.ToolsetFrame(parent=self, toolsetRegistry=self.toolsetRegistry, iconSize=16, iconPadding=0,
                                                      showMenuBtn=False, initialGroup=None)
        self.verticalSliderBtn = roundbutton.RoundButton(icon=iconlib.iconColorized("arrowSingleLeft", 10,
                                                                                    color=(0, 0, 0)))

        self.toolsetFrame.toolbar.setContentsMargins(0, 0, 0, 0)
        self.toolsetFrame.toolbar.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.initUi()
        self.connections()
        self.setFixedWidth(utils.dpiScale(36))

    def initUi(self):
        """ Init UI

        :return:
        """

        col = self.themePref.MAIN_FOREGROUND_COLOR

        # Properties
        propBtn = extendedbutton.ExtendedButton(parent=self)
        propBtn.setIconByName("infoTags", col, 18)
        propBtn.setProperty("widgets", "properties")
        propBtn.leftClicked.connect(self.sidePanel.activateProperties)
        self.mainLayout.addWidget(propBtn)

        editFrame = self.initEditButtonsWgt()
        self.mainLayout.addWidget(editFrame)

        btn = extendedbutton.ExtendedButton(parent=self)
        btn.setIconByName("shippingBox", col, 18)
        btn.leftClicked.connect(partial(self.sidePanel.setCurrentWidget, self.toolsetFrame.tree))
        self.mainLayout.addWidget(btn)

        self.mainLayout.addWidget(self.toolsetFrame)
        self.sidePanel.addWidget(self.toolsetFrame.tree)

        self.mainLayout.addWidget(self.verticalSliderBtn)
        self.mainLayout.setSpacing(utils.dpiScale(10))
        self.mainLayout.setContentsMargins(*utils.marginsDpiScale(4, 0, 4, 10))

    def setResizerWidget(self, resizerWidget):
        self.resizerWidget = resizerWidget
        self.resizerWidget.resizerBtn.hide()
        self.resizerWidget.resizerBtn.clicked.connect(self.updateResizerVis)

    def connections(self):
        """ Connections

        :return:
        """

        self.verticalSliderBtn.clicked.connect(self.sliderButtonClicked)

        self.toolsetFrame.toolsetToggled.connect(partial(self.sidePanel.setCurrentWidget, self.toolsetFrame.tree))

    def sliderButtonClicked(self):
        """ Hide or show the floating button for this toolbar

        :return:
        """
        self.resizerWidget.toggleWidget()
        self.updateResizerVis()

    def updateResizerVis(self):
        """ Show resizerBtn if self is hidden, else hide it

        :return:
        """
        if self.isHidden():
            self.resizerWidget.resizerBtn.show()
        else:
            self.resizerWidget.resizerBtn.hide()

    def initEditButtonsWgt(self):
        """ Initialize edit buttons

        :return:
        """
        col = self.themePref.MAIN_FOREGROUND_COLOR
        editButtons = ["plus", "trash", "pencil", "reload3"]

        editFrame = QtWidgets.QFrame(parent=self)
        editLayout = elements.vBoxLayout(parent=self)
        editFrame.setLayout(editLayout)
        editLayout.setSpacing(utils.dpiScale(5))
        editLayout.setContentsMargins(*utils.marginsDpiScale(0, 5, 0, 5))
        editFrame.setStyleSheet("background-color: #555555; border-radius: 2px;")

        for e in editButtons:

            btn = extendedbutton.ExtendedButton(parent=self)
            btn.setIconByName(e, col, 18)

            editLayout.addWidget(btn)

        editFrame.setFixedSize(editFrame.sizeHint())

        return editFrame


class ToolsetTabs(flowtoolbar.FlowToolBar):
    def __init__(self, parent=None, themePref=None, linkedWidget=None, toolsetRegistry=None, toolsetGroups=None, toolsets=None, separatorPos=[]):
        """ The tabs that will create the toolsets. Generally on the right side


        .. code-block:: python

            self.toolsetTabs = ToolsetTabs(parent=self, themePref=self.themePref, linkedWidget=sidePanel,
                               toolsetGroups="lights",
                               separatorPos=[3, 6])

        :param parent:
        :param themePref:
        :param linkedWidget: The stackedWidget that it is connected to. May change this to signals later
        :type linkedWidget: side
        :param separatorPos: Indices of the separators to be placed in toolsetTabs
        :type separatorPos: list
        :param linkedWidget: StackedLayout
        """

        self.themePref = themePref
        self.selected = None  # type: iconmenu.IconMenuButton
        self.linkedWidget = linkedWidget
        self.toolsets = toolsets

        self.toolsetRegistry = toolsetRegistry

        self.separatorPos = separatorPos

        self.toolsetGroups = toolsetGroups

        super(ToolsetTabs, self).__init__(parent=parent, iconSize=16)

        self.mainLayout.setContentsMargins(0, 0, 0, 0)

    def setLinkedWidget(self, widget):
        """ Set the toolbar where the stackedWidget will be

        :param widget:
        :return:
        """
        self.linkedWidget = widget

    def initUi(self):
        """ Init Ui

        :return:
        """
        super(ToolsetTabs, self).initUi()

        toolsets = self.toolsetRegistry.toolsets(self.toolsetGroups)

        col = self.themePref.MAIN_FOREGROUND_COLOR

        propBtn = self.addToolButton("infoTags", iconColor=col)
        propBtn.setProperty("widgets", "properties")
        propBtn.leftClicked.connect(partial(self.activateTab, propBtn))
        i = 0

        for t in toolsets:
            if i in self.separatorPos:
                self.flowLayout.addWidget(elements.QHLine())
            i += 1

            btn = self.addToolButton(t.uiData['icon'], iconColor=col)
            btn.setProperty("toolsetId", t.id)
            btn.setProperty("icon", t.uiData['icon'])
            widgets = self.toolsetRegistry.toolsetWidget(t.id)
            btn.setProperty("widgets", widgets)
            for w in widgets:
                w.setParent(self)
                self.linkedWidget.addWidget(w)

            btn.leftClicked.connect(lambda x=btn: self.activateTab(x))

        self.setSpacingY(2)
        self.activateTab(propBtn)

    def activateTab(self, btn):
        """

        :param btn:
        :type btn: iconmenu.IconMenuButton
        :return:
        """
        col = self.themePref.MAIN_FOREGROUND_COLOR
        if self.selected:
            self.selected.setIconColor(col)
            utils.setStylesheetObjectName(self.selected, "")

        if self.selected == btn:
            self.linkedWidget.hide()
            self.selected = None
            return

        btn.setIconColor(colors=(255, 255, 255))

        self.selected = btn
        self.selected.setStyleSheet("")
        utils.setStylesheetObjectName(btn, "ToolsetTabSelected")
        self.linkedWidget.show()
        btnWgt = btn.property("widgets")

        if btnWgt is not None and not isinstance(btnWgt, string_types):
            self.linkedWidget.setCurrentWidget(btnWgt[-1])
        elif btnWgt == "properties":

            self.linkedWidget.activateProperties()














