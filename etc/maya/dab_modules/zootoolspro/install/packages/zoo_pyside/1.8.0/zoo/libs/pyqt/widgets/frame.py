from Qt import QtWidgets, QtCore


class QFrame(QtWidgets.QFrame):
    mouseReleased = QtCore.Signal(object)

    def __init__(self, parent=None):
        super(QFrame, self).__init__(parent)

    def mouseReleaseEvent(self, event):
        self.mouseReleased.emit(event)
        return super(QFrame, self).mouseReleaseEvent(event)
