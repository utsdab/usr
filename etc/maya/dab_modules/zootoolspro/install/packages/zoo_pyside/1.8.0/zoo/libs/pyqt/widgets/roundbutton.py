from Qt import QtCore, QtGui, QtWidgets

from zoo.libs.pyqt.widgets import dpiscaling

METHOD_MASK = 0
METHOD_STYLESHEET = 1


class RoundButton(QtWidgets.QPushButton, dpiscaling.DPIScaling):
    """
    A nice rounded button. Two methods to rendering it out currently.
    You can use this like a QPushButton

    Mask:
    Mask will cut the button into a circle. It also allows for custom stylesheets.
    The downside though is that it is pixelated when drawing it out.

    .. code-block:: python

        roundBtn = RoundButton(self, "Hello World", method=Method.Mask)
        roundBtn.setMethod(Method.Mask)  # Use this if you want to set it after

    Stylesheet:
    Style sheet creates a smooth circle button, no pixelation. However for rectangle buttons,
    it wont be round and the user wont be able to use their own stylesheet.

    .. code-block:: python

        roundBtn = RoundButton(self, "Hello World", method=Method.StyleSheet)
        roundBtn.setMethod(Method.StyleSheet)  # Use this if you want to set it after
        roundBtn.setFixedSize(QtCore.QSize(24,24))  # Square dimensions recommended

    """

    def __init__(self, parent=None, text=None, icon=None, method=METHOD_STYLESHEET, toolTip=""):
        super(RoundButton, self).__init__(parent=parent,text=text, icon=icon)
        self.method = method
        self.customStyle = ""
        self.updateButton()
        self.setToolTip(toolTip)

    def setMethod(self, method=METHOD_MASK):
        """Set the method of rendering, Method.Mask or Method.StyleSheet

        StyleSheet:
            - Can't have own stylesheet
            - Smooth Rendering

        Mask:
            - Pixelated edges
            - Can set custom stylesheet

        :param method: Method.Mask or Method.StyleSheet
        :type method: int
        :return:
        """
        self.method = method
        self.updateButton()

    def resizeEvent(self, event):
        """Resize and update based on the method

        :return:
        """

        self.updateButton()
        super(RoundButton, self).resizeEvent(event)

    def updateButton(self):
        if self.method == METHOD_MASK:
            self.setMask(QtGui.QRegion(self.rect(), QtGui.QRegion.Ellipse))
        elif self.method == METHOD_STYLESHEET:
            super(RoundButton, self).setStyleSheet(self.roundStyle() + self.customStyle)

    def roundStyle(self):
        """ Style for round button

        :return:
        """
        radius = min(self.rect().width() * 0.5, self.rect().height() * 0.5)
        return "border-radius: {}px;".format(radius)

    def setStyleSheet(self, text):
        """ Set stylesheet for button

        :param text:
        :return:
        """

        # Do something different for the stylesheet type button
        if self.method == METHOD_STYLESHEET:
            self.customStyle = text
            self.updateButton()
        else:
            super(RoundButton, self).setStyleSheet(text)




