from Qt import QtCore, QtWidgets

from zoo.apps.hotkeyeditor import hotkeyview
from zoo.apps.hotkeyeditor.core import utils as hotkeyutils
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt.widgets.framelessmaya import FramelessWindowMaya
from zoo.preferences.core import preference


class HotkeyEditorUI(FramelessWindowMaya):
    def __init__(self, title="Zoo Hotkey Editor",
                 width=utils.dpiScale(1000),
                 height=utils.dpiScale(600),
                 framelessChecked=True, parent=None):

        super(HotkeyEditorUI, self).__init__(parent=parent, title=title, width=width, height=height,
                                             framelessChecked=framelessChecked)
        self.windowWidth = width
        self.windowHeight = height
        self.adminMode = False
        self.hotkeyView = hotkeyview.HotkeyView(parent=self)
        self.tabLayout = elements.hBoxLayout(self)
        self.themePref = preference.interface("core_interface")

        # UI
        self.setWindowTitle(title)
        self.mainLayout = elements.hBoxLayout(self)
        self.mainLayout.setContentsMargins(*utils.marginsDpiScale(0, 0, 0, 0))
        self.mainLayout.setSpacing(0)

        self.setMainLayout(self.mainLayout)
        self.resize(width, height)

        self.initUi()
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def initUi(self):
        self.tabLayout.setContentsMargins(0, 0, 0, 0)

        self.tabLayout.addWidget(self.hotkeyView)

        self.mainLayout.addLayout(self.tabLayout)

        if hotkeyutils.isAdminMode():
            self.setLogoColor(self.themePref.HOTKEY_ADMIN_LOGO_COLOR)

    def resizeWindow(self):
        for i in range(0, 10):
            QtWidgets.QApplication.processEvents()  # this must be here otherwise the resize is calculated too quickly
        self.resize(self.width(), self.minimumSizeHint().height())

    def focusInEvent(self, event):
        self.hotkeyView.reloadActive()

    def connections(self):
        pass


