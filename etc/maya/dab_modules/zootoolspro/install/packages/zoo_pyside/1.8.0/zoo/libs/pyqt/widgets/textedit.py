from Qt import QtWidgets
from zoo.libs.pyqt import utils


class TextEdit(QtWidgets.QTextEdit):
    def __init__(self, text="", parent=None, placeholderText="", toolTip="", editWidth=None, minimumHeight=None,
             maximumHeight=None, fixedWidth=None, fixedHeight=None):
        super(TextEdit, self).__init__(parent=parent)

        # utils.setStylesheetObjectName(self, "textEditForced")  # TODO: might be removed once stack widget fixed
        if fixedHeight:
            self.setFixedHeight(utils.dpiScale(fixedHeight))
        if minimumHeight:
            self.setMinimumHeight(utils.dpiScale(minimumHeight))
        if maximumHeight:
            self.setMaximumHeight(utils.dpiScale(maximumHeight))
        if fixedWidth:
            self.setFixedWidth(utils.dpiScale(fixedWidth))
        self.setPlaceholderText(placeholderText)
        self.setText(text)
        self.setToolTip(toolTip)