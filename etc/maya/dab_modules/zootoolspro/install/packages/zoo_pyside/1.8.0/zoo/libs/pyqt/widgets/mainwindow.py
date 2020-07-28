import platform
from Qt import QtWidgets, QtCore, QtGui
from zoo.libs import iconlib
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import dockwidget


class MainWindow(QtWidgets.QMainWindow):
    closed = QtCore.Signal()

    restoreWindowSize = False

    def __init__(self, title="", width=600, height=800, icon="",
                 parent=None, showOnInitialize=True, transparent=False):
        super(MainWindow, self).__init__(parent=parent)
        self.setObjectName(title or self.__class__.__name__)

        self.setContentsMargins(2, 2, 2, 2)
        self.setDockNestingEnabled(True)
        self.setDocumentMode(True)
        self.title = title
        self.setWindowTitle(title)
        self.resize(width, height)

        self.docks = []
        self.toolBars = {}
        self.hasMainMenu = False
        self.centralWidget = QtWidgets.QWidget(parent=self)
        self.setCentralWidget(self.centralWidget)

        if transparent:
            self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        self.setDockOptions(QtWidgets.QMainWindow.AllowNestedDocks |
                            QtWidgets.QMainWindow.AnimatedDocks |
                            QtWidgets.QMainWindow.AllowTabbedDocks)
        self.setTabPosition(QtCore.Qt.AllDockWidgetAreas, QtWidgets.QTabWidget.North)
        if icon:
            if isinstance(icon, QtGui.QIcon):
                self.setWindowIcon(icon)
            else:
                self.setWindowIcon(iconlib.icon(icon))

        if showOnInitialize:
            self.center()
            self.show()

        self.reapplySettings()

    def center(self):
        """ Centers to center of desktop

        :return:
        """
        frameGm = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        centerPoint = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def window(self):
        """

        :return:
        :rtype: MainWindow
        """
        return super(MainWindow, self).window()

    def addCustomStatusBar(self):
        self.setStatusBar(self.statusBar())
        self.statusBar().showMessage("Status info/tips displayed here..")

    def setupMenuBar(self):
        self.hasMainMenu = True
        self.fileMenu = self.menuBar().addMenu("File")
        self.viewMenu = self.menuBar().addMenu("View")
        self.exitAction = QtWidgets.QAction(self)
        self.exitAction.setIcon(iconlib.icon("close"))
        self.exitAction.setText("Close")
        self.exitAction.setShortcut("ctrl+Q")
        self.exitAction.setToolTip("Closes application")
        self.fileMenu.addAction(self.exitAction)
        self.exitAction.triggered.connect(self.close)

        for i in self.docks:
            self.viewMenu.addAction(i.toggleViewAction())

    def setCustomCentralWidget(self, widget):
        self.centralWidget = widget
        self.setCentralWidget(widget)

    def createDock(self, mainWidget, area=QtCore.Qt.LeftDockWidgetArea,
                   tabify=True):

        dockName = "".join([mainWidget.objectName(), "Dock"])
        existing = self.findDock(dockName)
        if existing:
            existing.raise_()
        dock = dockwidget.DockWidget(mainWidget.objectName(), parent=self, floating=False)

        dock.setObjectName(dockName)
        dock.setWidget(mainWidget)
        self.addDockWidget(area, dock, tabify=tabify)

    def addDockWidget(self, area, dockWidget, orientation=QtCore.Qt.Horizontal, tabify=True):
        """Adds a dock widget to the current window at the specified location, if the location already has a
        :param area:QtCore.Qt.DockWidgetArea
        :param dockWidget: QtWidgets.QDockWidget
        :param orientation: QtCore.Qt.Orientation
        """
        self.docks.append(dockWidget)
        if self.hasMainMenu:
            # add a show/hide action to the view menu
            self.viewMenu.addAction(dockWidget.toggleViewAction())

        if tabify:
            # tabify the dock if one already exists at the area specified
            for currentDock in self.docks:
                if self.dockWidgetArea(currentDock) == area:
                    self.tabifyDockWidget(currentDock, dockWidget)
                    return
        super(MainWindow, self).addDockWidget(area, dockWidget, orientation)

    def findDock(self, dockName):
        """ Returns the dock widget based on the object name passed in as the argument

        :param dockName: str, the objectName to find, docks must be
        :return: QDockWidget
        """
        for dock in self.docks:
            if dock.objectName() == dockName:
                return dock

    def toggleMaximized(self):
        """ Toggles the maximized window state

        :return:
        """

        if self.windowState() and QtCore.Qt.WindowMaximized:
            self.showNormal()
            return
        self.showMaximized()

    def closeEvent(self, ev):
        """ Saves the window state on the close event

        :param ev:
        :return:
        """

        qsettings = QtCore.QSettings()

        qsettings.beginGroup(self.objectName())
        qsettings.setValue("geometry", self.saveGeometry())
        qsettings.setValue("saveState", self.saveState())
        qsettings.setValue("maximized", self.isMaximized())
        if not self.isMaximized():
            qsettings.setValue("pos", self.pos())
            qsettings.setValue("size", self.size())
        qsettings.endGroup()
        self.closed.emit()
        super(MainWindow, self).closeEvent(ev)

    def reapplySettings(self):
        """ Read window attributes from settings,

        using current attributes as defaults (if settings not exist.)

        Called at QMainWindow initialization, before show().

        :return:
        """

        qsettings = QtCore.QSettings()
        # Restore settings if there are any
        if self.objectName() in qsettings.childGroups():

            qsettings.beginGroup(self.objectName())

            if self.restoreWindowSize:
                self.restoreGeometry(qsettings.value("geometry", self.saveGeometry()))
                self.resize(qsettings.value("size", self.size()))

            self.restoreState(qsettings.value("saveState", self.saveState()))
            pos = qsettings.value("pos", None)

            if pos is not None and utils.screensContainPoint(pos):
                self.move(qsettings.value("pos", self.pos()))

            if qsettings.value("maximized", False) == 'true':
                self.showMaximized()

            qsettings.endGroup()

    def helpAbout(self, copyrightDate, about, version=1.0):
        """
        This is a helper method for easily adding a generic help messageBox to self
        Creates a about MessageBox
        :param copyrightDate : string , the copyright date for the tool
        :param about : string, the about information
        """
        __version__ = version
        QtWidgets.QMessageBox.about(self, "About" + self.objectName(),
                                    "<b>'About {0}</b> v {1}Copyright &copy; 2007,{2}.All rights reserved.\
                                    <p>Python {3} - Qt {4} - PyQt {5} on {6}".format(copyrightDate, about,
                                                                                     __version__,
                                                                                     platform.python_version(),
                                                                                     QtCore.QT_VERSION_STR,
                                                                                     QtCore.PYQT_VERSION_STR,
                                                                                     platform.system()))
