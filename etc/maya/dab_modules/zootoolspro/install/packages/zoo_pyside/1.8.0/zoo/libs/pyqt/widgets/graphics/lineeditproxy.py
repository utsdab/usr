from Qt import QtWidgets, QtCore


class LineEditProxyWidget(QtWidgets.QGraphicsProxyWidget):
    editingFinished = QtCore.Signal()

    def __init__(self, parent, text):
        super(LineEditProxyWidget, self).__init__()
        self.setParentItem(parent)
        self.lineedit = QtWidgets.QLineEdit()
        self.setWidget(self.lineedit)
        self.lineedit.setText(text)
        self.setZValue(100)
        self.lineedit.editingFinished.connect(self.done)
        self._text = text
        self._done = False

    def text(self):
        return self._text

    def done(self):
        if self._done:
            return
        self._done = True
        self._text = self.lineedit.text()
        self.lineedit.clearFocus()
        self.setParentItem(None)
        self.editingFinished.emit()

    def focusOutEvent(self, event):
        super(LineEditProxyWidget, self).focusOutEvent(event)
        self.done()
