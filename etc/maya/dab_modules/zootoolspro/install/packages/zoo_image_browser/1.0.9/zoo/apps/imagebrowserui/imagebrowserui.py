import os

from Qt import QtCore, QtWidgets, QtGui

from zoo.apps.imagebrowserui.widgets import sidepanel
from zoo.apps.imagebrowserui.widgets.directories import DirectoriesWidget
from zoo.apps.imagebrowserui.widgets.tweakbar import SettingsTweakBar
from zoo.apps.imagebrowserui.widgets.verticaltoolbar import VerticalToolBar
from zoo.libs import iconlib
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.extended.imageview import thumbnail
from zoo.libs.pyqt.extended.imageview.models import filemodel
from zoo.libs.pyqt.widgets import extendedbutton, resizerwidget, iconmenu
from zoo.libs.pyqt.widgets import searchwidget, elements
from zoo.libs.pyqt.widgets.framelessmaya import FramelessWindowMaya
from zoo.preferences.core import preference


class ImageBrowserUI(FramelessWindowMaya):

    Hide_LeftSide = 0
    Hide_RightSide = 1
    Hide_TopSide = 2
    Hide_BottomSide = 3
    resized = QtCore.Signal()

    def __init__(self, title="Browser",
                 width=utils.dpiScale(1060),
                 height=utils.dpiScale(600),
                 framelessChecked=True, parent=None):
        """ Image browser ui

        :param title:
        :param width:
        :param height:
        :param framelessChecked:
        :param parent:
        """

        super(ImageBrowserUI, self).__init__(parent=parent, title=title, width=width, height=height,
                                             framelessChecked=framelessChecked, titleShrinksFirst=False)

        self.searchWidget = None  # type: SearchWidget
        self.titleMenuBtn = extendedbutton.ExtendedButton(parent=self)

        self.themePref = preference.interface("core_interface")
        self.sidePanel = sidepanel.SidePanel(self, themePref=self.themePref, startHidden=False)
        self.verticalToolbar = VerticalToolBar(self, themePref=self.themePref, sidePanel=self.sidePanel)
        self.settingsTweakBar = SettingsTweakBar(parent=self, themePref=self.themePref)
        self.imageBrowser = None  # type: elements.ThumbnailViewWidget
        self.directoriesWgt = DirectoriesWidget(self, themePref=self.themePref)
        self.mainLayout = elements.hBoxLayout(parent)

        self.initUi()

    def initUi(self):
        """ Initialise Ui

        :return:
        """
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setMainLayout(self.mainLayout)

        mainSplitter = QtWidgets.QSplitter(self)

        dirResizerWidget = resizerwidget.ResizerWidget(self,
                                                       buttonAlign=QtCore.Qt.AlignBottom | QtCore.Qt.AlignLeft,
                                                       buttonOffset=QtCore.QPoint(0, -50), autoButtonUpdate=False)
        dirResizerWidget.addWidget(self.directoriesWgt)

        self.resized.connect(dirResizerWidget.updateButtonPosition)
        mainSplitter.addWidget(dirResizerWidget)
        self.browserInit()

        centerWidget = self.centerWidgetInit()
        mainSplitter.addWidget(centerWidget)
        mainSplitter.addWidget(self.sidePanel)
        mainSplitter.setStretchFactor(0, 1)
        mainSplitter.setStretchFactor(1, 3)
        mainSplitter.setStretchFactor(2, 1)

        self.mainLayout.addWidget(mainSplitter)
        vertResizerWidget = resizerwidget.ResizerWidget(self, layoutDirection=resizerwidget.ResizerWidget.RightToLeft,
                                                        buttonAlign=QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom,
                                                        buttonOffset=QtCore.QPoint(0, -50), autoButtonUpdate=False)
        vertResizerWidget.addWidget(self.verticalToolbar)
        vertResizerWidget.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        vertResizerWidget.addWidget(self.sidePanel, target=False, external=True)
        vertResizerWidget.updateButtonPosition()
        vertResizerWidget.autoButtonUpdate = False
        self.resized.connect(vertResizerWidget.updateButtonPosition)
        self.verticalToolbar.setResizerWidget(vertResizerWidget)
        self.mainLayout.addWidget(vertResizerWidget)
        self.titlebarWgtInit()
        self.titlebarCornerWgtInit()

        QtCore.QTimer.singleShot(0, self.resized.emit)


    def centerWidgetInit(self):
        """ The center widget,
        may be changed when the new layout engine is implemented

        :return:
        """

        resizerWgt = resizerwidget.ResizerWidget(self, layoutDirection=resizerwidget.ResizerWidget.BottomToTop,
                                                 buttonAlign=QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter,
                                                 autoButtonUpdate=False)
        resizerWgt.addWidget(self.settingsTweakBar)
        self.resized.connect(resizerWgt.updateButtonPosition)

        centerWidget = QtWidgets.QWidget(self)
        centerWidgetLayout = elements.vBoxLayout(centerWidget)
        centerWidgetLayout.setContentsMargins(0, 0, 0, 0)
        centerWidgetLayout.addWidget(self.imageBrowser)
        centerWidgetLayout.addWidget(resizerWgt)

        centerWidgetLayout.setStretch(0, 1)

        return centerWidget

    def browserInit(self):
        """ Image browser Init

        :return:
        """
        self.imageBrowser = elements.MiniBrowser(parent=self, uniformIcons=False)
        self.imageBrowser.setColumns(5)
        rootDirectory = os.path.join(os.path.dirname(__file__), "example")
        self.browserModel = filemodel.FileViewModel(self.imageBrowser, rootDirectory)
        self.imageBrowser.setModel(self.browserModel)


    def titlebarWgtInit(self):
        """ Initialize the widget that will be placed in the title bar

        :return:
        """
        col = self.themePref.MAIN_FOREGROUND_COLOR

        titleLayout = self.titlebarContentsLayout()
        self.searchWidget = SearchWidget(parent=self, themePref=self.themePref)
        self.searchWidget.setMinimumSize(QtCore.QSize(21, 20))
        self.titleMenuBtn.setIconByName("menudots", col, 18)
        titleLayout.addWidget(self.titleMenuBtn)
        titleLayout.addWidget(self.searchWidget)

        fileMenu = [("plus", "New"),
                    ("trash", "Delete"),
                    ("pencil",  "Rename"),
                    ("reload3", "Refresh")]

        for m in fileMenu:
            self.titleMenuBtn.addAction(m[1], icon=iconlib.iconColorized(m[0], size=20))

    def titlebarCornerWgtInit(self):
        """ Initialise the corner widget that will be placed next to the minimize and close buttons

        :return:
        """

        cornerLayout = self.cornerContentsLayout()
        QtWidgets.QWidget()
        col = self.themePref.MAIN_FOREGROUND_COLOR
        size = 20

        browserMode = iconmenu.IconMenuButton(parent=self)
        modes = [("lightstudio", "Light Presets"),
                 ("globe", "IBL"),
                 ("video",  "Clip Library"),
                 ("shippingBox", "Package Browser")]
        iconOverlay = "arrowmenu"

        for m in modes:
            browserMode.addAction(m[1],
                                  mouseMenu=QtCore.Qt.LeftButton,
                                  connect=lambda x=m[0]: browserMode.setIconByName([x,iconOverlay], colors=col, size=size),
                                  icon=iconlib.iconColorized(m[0], size=size))

        browserMode.menu().mouseButtonClicked.connect(self.browserMenuItemClicked)
        browserMode.setMenuAlign(QtCore.Qt.AlignRight)

        # Middle click menu with the toolset icon popup
        browserMode.setIconByName(["lightstudio", iconOverlay], colors=col, size=size)
        browserMode.setFixedSize(QtCore.QSize(28, 28))
        utils.setStylesheetObjectName(browserMode, "DefaultButton")
        cornerLayout.addWidget(browserMode)

    def browserMenuItemClicked(self, button, action):
        """

        :param button: Mouse Button clicked
        :param action: Action clicked
        :type action: QtWidgets.QAction
        :return:
        """

        if button == QtCore.Qt.MidButton:
            bType = action.text()
            from zoo.apps.imagebrowserui import run
            run.scriptEditorLaunch(browserType=bType)

    def resizeEvent(self, *args, **kwargs):
        self.resized.emit()
        return super(ImageBrowserUI, self).resizeEvent(*args, **kwargs)


class SearchWidget(QtWidgets.QWidget):
    def __init__(self, parent=None, themePref=None):
        """ Search Widget

        :param parent:
        :param themePref:
        """
        super(SearchWidget, self).__init__(parent=parent)
        self.searchEdit = None  #
        self.searchFilter = QtWidgets.QComboBox(self)
        self.mainLayout = elements.hBoxLayout(self)

        self.themePref = themePref

        self.setLayout(self.mainLayout)
        self.initUi()

    def initUi(self):
        col = self.themePref.FRAMELESS_TITLELABEL_COLOR
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        size = utils.dpiScale(16)
        searchIcon = iconlib.iconColorized("magnifier", size, col)  # these should be in layouts
        closeIcon = iconlib.iconColorized("close", size, col)
        self.searchEdit = searchwidget.SearchLineEdit(searchIcon, closeIcon, self)
        self.searchEdit.setPlaceholderText("Search...")
        self.searchEdit.setMinimumSize(QtCore.QSize(21, 20))

        self.searchFilter.addItem("Tags")
        self.searchFilter.addItem("Title")
        self.searchFilter.addItem("Description")

        self.mainLayout.addStretch(3)
        self.mainLayout.addWidget(self.searchFilter)
        self.mainLayout.setSpacing(5)

        self.mainLayout.addWidget(self.searchEdit)
        self.mainLayout.setStretch(2, 4)
        self.mainLayout.addStretch(2)
        self.searchEdit.setFixedHeight(utils.dpiScale(20))


