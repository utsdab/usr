from Qt import QtWidgets, QtCore
from zoo.libs.pyqt.widgets.label import Label
from zoo.libs.pyqt.widgets.layouts import hBoxLayout, vBoxLayout
from zoo.libs.pyqt import uiconstants as uic, utils


class EmbeddedWindow(QtWidgets.QFrame):
    targetSizeVPolicy = None  # type: None
    visibilityChanged = QtCore.Signal(bool)

    def __init__(self, parent=None, title="", defaultVisibility=False, uppercase=False, closeButton=None,
                 margins=(0, 0, 0, 0), resizeTarget=None):
        """An embedded window is a QFrame widget that appears like a window inside of another ui.

        It is not a window itself, more like a fake window.  It has some simple stylesheeting and a title
        The widget area can also be easily closed and shown again with it's methods

        Assign other widgets to the window by adding to it's QVLayout:
            EmbeddedWindow.propertiesLayout()

        or return the layout with:
            layout = EmbeddedWindow.getLayout()

        A button is passed in as an optional close button because it'll probably be using the zoo package zoo_core_pro

        :param parent: the parent widget to parent this widget
        :type parent: QtWidgets.QWidget
        :param title: The title of the window, can be changed
        :type title: basestring
        :param defaultVisibility: Is the embedded window visible? Can be queried with self.visible
        :type defaultVisibility: bool
        :param closeButton: the button (object) used to close the window
        :type closeButton: QtWidgets.QAbstractButton
        :param resizeTarget: The widget to shrink when the embedded window is active
        :type resizeTarget: QtWidgets.QWidget
        """
        super(EmbeddedWindow, self).__init__(parent)
        self.resizeTarget = None  # type: QtWidgets.QWidget
        self.targetSavedHeight = None
        self.margins = margins
        self.title = title
        self.parentWgt = parent
        self.uppercase = uppercase
        self.innerQFrame = None  # type: QtWidgets.QFrame
        self.outerLayout = None  # type: QtWidgets.QHBoxLayout
        self.propertiesLayout = None  # type: QtWidgets.QVBoxLayout
        self.propertiesLbl = None  # type: QtWidgets.QLabel
        self.hidePropertiesBtn = closeButton or None
        self.setEmbedVisible(defaultVisibility)
        self.initUi()
        self.connections()
        self.setResizeTarget(resizeTarget)

    def initUi(self):
        """Create the UI with an optional title and close icon top right.  Pass in no title or close button and the \n
        Embed Window will be empty.

        If adding your own close button, pass into the class:
            closeButton=None

        and subclass this method with your own button named:
            self.hidePropertiesBtn

        The class will pick this button up and use it for close functionality.

        self.propertiesLayout is the VLayout where other items can be added to the window. This can also be returned
        with the method getLayout()
        """
        # The Embed Window frame outlined with a border (self.innerQFrame.setFrameStyle()) in a layout --------------
        self.innerQFrame = QtWidgets.QFrame(parent=self)
        self.innerQFrame.setFrameStyle(QtWidgets.QFrame.Box | QtWidgets.QFrame.Plain)
        self.outerLayout = hBoxLayout(parent=self, margins=(utils.marginsDpiScale(*self.margins)))
        utils.setStylesheetObjectName(self.innerQFrame, "embededWindowBG")  # setObjectName with ui update
        self.outerLayout.addWidget(self.innerQFrame)
        self.propertiesLayout = vBoxLayout(parent=self.innerQFrame, margins=(uic.WINSIDEPAD, 4, uic.WINSIDEPAD,
                                                                             uic.WINBOTPAD), spacing=uic.SREG)
        # Optional title and close button on the Embedded Window ---------------------------
        if self.hidePropertiesBtn or self.title:
            self.propertyTitleLayout = hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SSML)
            if self.title:
                self.propertiesLbl = Label(self.title, parent=self.parentWgt, upper=self.uppercase, bold=True)
                self.propertyTitleLayout.addWidget(self.propertiesLbl, 10)
            if self.hidePropertiesBtn:  # close button passed in as uses zoo_core_pro
                self.propertyTitleLayout.addWidget(self.hidePropertiesBtn, 10)
            self.propertiesLayout.addLayout(self.propertyTitleLayout)

    def getLayout(self):
        """Returns the QVLayout where other widgets can be added to the embedded window
        """
        return self.propertiesLayout

    def getTitleLbl(self):
        """Returns the title QLabel widget so that it can be altered
        """
        return self.propertiesLbl

    def getHideButton(self):
        """Returns the hide button so functionality can be assigned to it
        """
        if self.hidePropertiesBtn:
            return self.hidePropertiesBtn

    def setTitle(self, title):
        """Set the title of the embedded window

        :param title: the Title of the embedded window
        :type title: str
        """
        if title != "":
            self.propertyTitleLayout.setStretch(self.propertyTitleLayout.indexOf(self.propertiesLbl), 0)
            self.propertiesLbl.setVisible(title != "")  # Visible if its not empty
        else:
            self.propertyTitleLayout.setStretch(0, 0)

        self.propertiesLbl.setVisible(title != "")

        self.propertiesLbl.setText(title)

    def hideEmbedWindow(self):
        """Hide the embedded window
        """
        self.setEmbedVisible(False)

    def showEmbedWindow(self):
        """Show the embedded window
        """
        self.setEmbedVisible(True)

    def setEmbedVisible(self, visible, resizeTarget=True):
        """Show or hide the embed window

        If resizeTarget resize the target widget to it's minimumHeight when the embed window on show, return to \n
        default on hide.  The widget should be passed in or set with self.setResizeTarget(widget)

        :param visible: Is the embed window visible or not
        :type visible: bool
        :param resizeTarget: If True resize the target widget to it's minimumHeight when the embed window is visable
        :type resizeTarget:
        """
        hidden = not visible
        self.setHidden(hidden)
        self.visibilityChanged.emit(visible)

    def sizeHint(self):
        """ Size hint

        :return:
        :rtype:
        """
        # Makes sure contents never gets squashed
        sizeHint = super(EmbeddedWindow, self).sizeHint()
        self.setMinimumHeight(sizeHint.height())
        return sizeHint

    def connections(self):
        """UI interaction connections, hide button
        """
        if self.hidePropertiesBtn:
            self.hidePropertiesBtn.clicked.connect(self.hideEmbedWindow)

    def setState(self, state):
        self.targetSavedHeight = state["savedSize"]

        if state.get("visible") is not None:
            self.setEmbedVisible(state["visible"], resizeTarget=False)

    def state(self):
        state = {"visible": self.isVisible(),
                 "savedSize": self.targetSavedHeight}
        return state

    def setResizeTarget(self, target):
        """ The resize target widget

        The Target to resize when this embedded window appears. For example, we want the embedded window to appear
        but that would make the window too big. It will shrink the target widget so our window will be the same size.

        :param target:
        :type target: QtWidgets.QWidget
        :return:
        """
        self.resizeTarget = target

