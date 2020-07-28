import logging
from Qt import QtGui, QtWidgets, QtCore
from zoo.libs.utils import zlogging
logger = zlogging.getLogger(__name__)



class OutputLogDialog(QtWidgets.QPlainTextEdit):
    """Output dialog

    ::example:
        wid = OutputLogDialog("MyLogWindow")
        wid.show()
        wid.logInfo("helloworld")
        wid.logDebug("helloworld")
        wid.logWarning("helloworld")
        wid.logError("helloworld")
        wid.logCritical("helloworld")

    """
    infoColor = QtGui.QColor(QtCore.Qt.white)
    debugColor = QtGui.QColor("#f4f4f4")
    warningColor = QtGui.QColor("#ffe700")
    errorColor = QtGui.QColor("#CC0000")
    criticalColor = QtGui.QColor("#CC0000")
    html = """<p style="font-weight:300;color:{};"<span>{}</span></p>"""

    def __init__(self, title, parent=None):
        super(OutputLogDialog, self).__init__(parent)
        self.setObjectName('{}OutputLog'.format(title))
        self.setWindowTitle(title)
        self.createLayout()
        # use the built logging module for the levels since that would be more consistent
        self.outputType = logging.INFO

    def createLayout(self):
        """Sets up the layout for the dialog."""

        self.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.setReadOnly(True)

    def logInfo(self, msg):
        self.write(msg, self.infoColor)

    def logDebug(self, msg):
        self.write(msg, self.debugColor)

    def logWarning(self, msg):
        self.write(msg, self.warningColor)

    def logError(self, msg):
        self.write(msg, self.errorColor)

    def logCritical(self, msg):
        self.write(msg, self.criticalColor)

    def keyEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            self.clear()

    def write(self, msg, color=QtGui.QColor(QtCore.Qt.white)):
        # deal with multi line strings
        msg = msg.replace("\n", "<br/>")
        html = self.html.format(color.name(), msg)
        self.appendHtml(html)

    def factoryLog(self, msg, level):
        if level == logging.INFO:
            self.logInfo(msg)
        elif level == logging.DEBUG:
            self.logDebug(msg)
        elif level == logging.WARNING:
            self.logWarning(msg)
        elif level == logging.ERROR:
            self.logError(msg)
        elif level == logging.CRITICAL:
            self.logCritical(msg)

    def wheelEvent(self, event):
        """
        Handles zoom in/out of the text.
        """
        if event.modifiers() & QtCore.Qt.ControlModifier:
            delta = event.delta()
            if delta < 0:
                self.zoom(-1)
            elif delta > 0:
                self.zoom(1)
            return True
        return super(OutputLogDialog, self).wheelEvent(event)

    def zoom(self, direction):
        """
        Zoom in on the text.
        """

        font = self.font()
        size = font.pointSize()
        if size == -1:
            size = font.pixelSize()

        size += direction

        if size < 7:
            size = 7
        if size > 50:
            return

        style = """
        QWidget {
            font-size: %spt;
        }
        """ % (size,)
        self.setStyleSheet(style)


class QWidgetHandler(logging.Handler):
    """Custom Qt Logging Handler for Sending Messages to child Widgets"""

    def __init__(self):
        super(QWidgetHandler, self).__init__()
        self._widgets = []

    def addWidget(self, widget):
        if widget not in self._widgets:
            self._widgets.append(widget)

    def removeWidget(self, widget):
        if widget in self._widgets:
            self._widgets.remove(widget)

    def clearWidgets(self):
        self._widgets = []

    def emit(self, record):
        msg = self.format(record)

        for widget in self._widgets:
            widget.factoryLog(msg, record.levelno)
