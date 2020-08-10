from Qt import QtWidgets

from zoo.apps.preferencesui import model
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.extended import treeviewplus
from zoo.libs.pyqt.models import treemodel
from zoo.libs.pyqt.widgets.framelessmaya import FramelessWindowMaya
from zoo.preferences.core import preference
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt import uiconstants as uic


class PreferencesUI(FramelessWindowMaya):
    def __init__(self, title="Zoo Preferences ",
                 width=utils.dpiScale(850),
                 height=utils.dpiScale(700),
                 framelessChecked=True, parent=None):

        super(PreferencesUI, self).__init__(parent=parent, title=title, width=width, height=height,
                                            framelessChecked=framelessChecked)
        self.windowWidth = width
        self.themePref = preference.interface("core_interface")
        self.treeModel = treemodel.TreeModel(None)
        self._dpiScale = utils.dpiScale(16)
        self._initUi()

        self.model = model.Model(qmodel=self.treeModel, order=["General", "Theme Colors"])
        self.prefTreeView.setModel(self.treeModel)
        self.prefTreeView.expandAll()

        firstWgtSource = self.firstDataSourceWithWidget(self.model.root)
        if firstWgtSource is not None:
            self.prefStackedWgt.addSource(firstWgtSource)

        self.connections()

    def _initUi(self):
        self.mainLayout = elements.vBoxLayout(margins=(0, 0, 0, 0), spacing=0)

        toolTipBtn = "Save only the current section's preferences settings, and close the window. "
        self.saveBtn = elements.styledButton(text="Save", icon="save", parent=self, textCaps=True,
                                             style=uic.BTN_DEFAULT, toolTip=toolTipBtn)
        toolTipBtn = "Save only the current section's preferences settings. "
        self.applyBtn = elements.styledButton(text="Apply", icon="checkMark", parent=self, textCaps=True,
                                              style=uic.BTN_DEFAULT, toolTip=toolTipBtn)
        toolTipBtn = "Revert this section's preferences settings to the previous (not default) settings. "
        self.resetBtn = elements.styledButton(text="Revert", icon="reload2", parent=self, textCaps=True,
                                              style=uic.BTN_DEFAULT, toolTip=toolTipBtn)
        toolTipBtn = "Cancel the current changes and close the window. "
        self.cancelBtn = elements.styledButton(text="Cancel", icon="xCircleMark", parent=self, textCaps=True,
                                               style=uic.BTN_DEFAULT, toolTip=toolTipBtn)

        self.prefStackedWgt = PrefStackedWidget(parent=self)
        self.prefTreeView = PrefTreeView(parent=self, stackedWidget=self.prefStackedWgt)

        splitter = QtWidgets.QSplitter(parent=self)

        scrollArea = QtWidgets.QScrollArea(self)
        scrollArea.setWidget(self.prefStackedWgt)
        scrollArea.setWidgetResizable(True)
        scrollArea.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)

        splitter.addWidget(self.prefTreeView)
        splitter.addWidget(scrollArea)
        treeWidgetSize = utils.dpiScale(165)
        splitter.setSizes([treeWidgetSize, self.windowWidth - treeWidgetSize])

        self.mainLayout.addWidget(splitter)

        # Bottom buttons
        botButtonsLayout = elements.hBoxLayout(parent=None, margins=(uic.SMLPAD, uic.SMLPAD, uic.SMLPAD, uic.SMLPAD))

        botButtonsLayout.addWidget(self.saveBtn)
        botButtonsLayout.addWidget(self.applyBtn)
        botButtonsLayout.addWidget(self.resetBtn)
        botButtonsLayout.addWidget(self.cancelBtn)

        self.mainLayout.addLayout(botButtonsLayout)

        self.setMainLayout(self.mainLayout)

    def firstDataSourceWithWidget(self, dataSource):
        """ Recursively gets the first datasource with a widget

        :type dataSource: model.SettingDataSource, model.PathDataSource
        :return:
        """

        if dataSource is None:
            return

        wgt = dataSource.widget()
        if wgt is not None:
            return dataSource
        for child in dataSource.children:
            source = self.firstDataSourceWithWidget(child)
            if source is not None and source.widget() is not None:
                return source

    def connections(self):
        self.saveBtn.clicked.connect(self.savePressed)
        self.applyBtn.clicked.connect(self.applyPressed)
        self.cancelBtn.clicked.connect(self.cancelPressed)
        self.resetBtn.clicked.connect(self.resetPressed)

    def savePressed(self):
        self.window().hide()
        self.prefStackedWgt.apply()
        self.window().close()

    def applyPressed(self):
        self.prefStackedWgt.apply()

    def resetPressed(self):
        self.prefStackedWgt.revert()

    def cancelPressed(self):
        self.window().hide()
        self.prefStackedWgt.revert()
        self.window().close()


class PrefStackedWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(PrefStackedWidget, self).__init__(parent)
        self.titleLabel = QtWidgets.QLabel(parent=self)
        self._initUi()
        self.source = None  # type: model.SettingDataSource

    def _initUi(self):
        layout = elements.vBoxLayout(parent=self, margins=(0, 0, 0, 0), spacing=0)
        self._stackedWidget = QtWidgets.QStackedWidget(self)
        titleLayout = elements.vBoxLayout(parent=None,
                                          margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINBOTPAD, uic.WINSIDEPAD),
                                          spacing=0)
        titleLayout.addWidget(self.titleLabel)
        layout.addLayout(titleLayout)
        layout.addWidget(self._stackedWidget)
        utils.setStylesheetObjectName(self.titleLabel, "HeaderLabel")  # set stylesheet

    def __getattr__(self, item):
        """ Use PrefStackedWidget as if it is using self._stackedWidget

        :param item:
        :return:
        """
        try:
            return getattr(self._stackedWidget, item)
        except:
            raise AttributeError(item)

    def addSource(self, source, activate=True):
        self.addWidget(source.widget())

        if activate:
            self.setSource(source)

    def setSource(self, source):
        self.setTitle(source.label)
        self.setCurrentWidget(source.widget())
        self.source = source

    def setTitle(self, text):
        self.titleLabel.setText(text.upper())

    def apply(self):
        self.source.save()

    def revert(self):
        self.source.revert()


class PrefTreeView(treeviewplus.TreeViewPlus):
    def __init__(self, parent, stackedWidget):
        super(PrefTreeView, self).__init__(searchable=True, parent=parent, expand=True, sorting=False,
                                           labelVisible=False, comboVisible=False)

        self.stackedWidget = stackedWidget  # type: PrefStackedWidget
        self.treeView.setHeaderHidden(True)
        self.treeView.setSelectionMode(QtWidgets.QTreeView.SingleSelection)
        self.selectionChanged.connect(self.onSelectionChangedEvent)
        self.setAlternatingColorEnabled(False)

    def onSelectionChangedEvent(self, itemSelection):
        for dataSource in self.selectedItems():
            wgt = dataSource.widget()
            if wgt is None:
                return

            if self.stackedWidget.indexOf(wgt) == -1:
                self.stackedWidget.addSource(dataSource)
                break

            self.stackedWidget.setCurrentWidget(wgt)
            self.stackedWidget.setTitle(dataSource.label)

            break
