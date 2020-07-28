from Qt import QtWidgets


class MessageBox(QtWidgets.QMessageBox):
    def __init__(self, parent=None, text="", applyStyleSheet=True):
        super(self.__class__, self).__init__(parent, text)

        if applyStyleSheet:
            self.applyStyleSheet()

    def applyStyleSheet(self):
        pass
