from Qt import QtWidgets, QtCore

from zoo.libs.pyqt.widgets import elements


class SlidingWidget(QtWidgets.QWidget):

    def __init__(self, parent=None, duration=80):
        """ Sliding Widget

        A widget that accepts two widgets. The primary widget slides open on mouse focus, slides closed
        when the mouse moves out of the widget and loses focus.

        .. code-block:: python

            slidingWidget = SlidingWidget(self)
            slidingWidget.setWidgets(self.searchEdit, self.titleLabel)


        :param parent:
        :param duration:
        """

        super(SlidingWidget, self).__init__(parent=parent)

        self.secondaryWidget = None
        self.anim = None  # type: QtCore.QPropertyAnimation
        self.mainLayout = elements.hBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.primaryWidget = None
        self.timeoutActive = True
        self.timeout = 3000

        self.slideDirection = QtCore.Qt.RightToLeft

        self.setLayout(self.mainLayout)
        self.primaryIndex = 1
        self.secondaryIndex = 0
        self.duration = duration
        self.origKeyPressEvent = None

        self._slideStretch = 0
        self.initial = None

        self.closeTimer = QtCore.QTimer(self)
        self.closeTimer.timeout.connect(self.clearedFocus)

    def clearedFocus(self):
        if self.timeoutActive:
            self.primaryWidget.clearFocus()

    def setTimeoutActive(self, active):
        self.timeoutActive = active

    def setSlideDirection(self, direction=QtCore.Qt.RightToLeft):
        """

        :param direction:
        :type direction: QtCore.Qt.RightToLeft or QtCore.Qt.LeftToRight
        :return:
        """

        if direction == QtCore.Qt.RightToLeft:
            self.primaryIndex = 1
            self.secondaryIndex = 0
        else:
            self.primaryIndex = 0
            self.secondaryIndex = 1

    def setDuration(self, duration):
        """ Duration of animation

        :param duration: Time in milliseconds
        :type duration: int
        :return:
        """
        self.duration = duration

    def setWidgets(self, primary, secondary):
        """ Set the widgets of the primary and secondary widget



        :param primary: Primary widget is the one that will expand when clicked.
        :type primary: QtWidgets.QWidget
        :param secondary: Secondary will be be hidden when primary widget is focused
        :type secondary: QtWidgets.QWidget
        :return:
        """
        while self.mainLayout.count():
            self.mainLayout.takeAt(0)

        self._setSecondaryWidget(secondary)
        self._setPrimaryWidget(primary)

    def _setPrimaryWidget(self, widget):
        """ Set the primary widget. Primary widget will be the one that will expand when clicked

        :param widget:
        :return:
        """
        self.mainLayout.addWidget(widget)
        self.primaryWidget = widget

        self.updateInitial()

        self.origKeyPressEvent = widget.keyPressEvent
        self.origFocusOutEvent = widget.focusOutEvent
        self.origFocusInEvent = widget.focusInEvent

        widget.focusOutEvent = self.widgetFocusOut
        widget.focusInEvent = self.widgetFocusIn
        widget.keyPressEvent = self.widgetKeyPressEvent

    def widgetKeyPressEvent(self, event):
        self.closeTimer.start(self.timeout)
        self.origKeyPressEvent(event)  # run original

    def _setSecondaryWidget(self, widget):
        """ Set secondary widget.

        The secondary widget will be shown most of the time but will be hidden when the primary is clicked.

        :param widget:
        :return:
        """
        self.mainLayout.addWidget(widget)
        self.secondaryWidget = widget
        self.secondaryWidget.setMinimumWidth(1)

        self.updateInitial()

    def updateInitial(self):
        """ Set up the initial stretch

        :return:
        """

        if self.primaryWidget is not None and self.secondaryWidget is not None:
            QtWidgets.QApplication.processEvents()
            self.mainLayout.setStretch(self.secondaryIndex, 100)
            self.mainLayout.setStretch(self.primaryIndex, 1)

    def setSlideStretch(self, value):
        """ Set the stretch for the mainlayout widgets.

        Usually used in the QPropertyAnimation

        :param value:
        :return:
        """
        self._slideStretch = value
        self.mainLayout.setStretch(self.secondaryIndex, 100-value)
        self.mainLayout.setStretch(self.primaryIndex, value)

    def getSlideStretch(self):
        """ The current slide stretch

        :return:
        """
        return self._slideStretch

    # Property to be animated
    slideStretch = QtCore.Property(int, getSlideStretch, setSlideStretch)

    def widgetFocusIn(self, event):
        """ Expand the primary widget event

        :param event:
        :type event: QtGui.QFocusEvent
        :return:
        """

        if hasattr(event, "reason") and event.reason() == QtCore.Qt.FocusReason.MouseFocusReason or \
            hasattr(event, "reason") is False:
            self.animate(expand=True)
            self.closeTimer.start(self.timeout)  # close after a few seconds

        self.origFocusInEvent(event)  # run original

    def widgetFocusOut(self, event=None):
        """ Collapse the primary widget event

        :param event:
        :return:
        """
        self.animate(expand=False)
        self.origFocusOutEvent(event)

    def animate(self, expand=True):
        """ Animate the sliding of the widget

        :param expand:
        :return:
        """

        if expand:
            self.anim = QtCore.QPropertyAnimation(self, "slideStretch")
            self.anim.setDuration(self.duration)
            self.anim.setStartValue(1)
            self.anim.setEndValue(99)
            self.anim.setEasingCurve(QtCore.QEasingCurve.InOutSine)
            self.anim.start()
        else:
            self.anim = QtCore.QPropertyAnimation(self, "slideStretch")
            self.anim.setDuration(self.duration)
            self.anim.setStartValue(self.mainLayout.stretch(1))
            self.anim.setEndValue(self.primaryIndex)
            self.anim.setEasingCurve(QtCore.QEasingCurve.InOutSine)
            self.anim.start()

