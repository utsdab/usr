import sys

from zoo.libs import iconlib
from Qt import QtWidgets, QtGui, QtCore


class CollapsibleGroupBox(QtWidgets.QGroupBox):
    """Collapsible Group box using arrow icons to indicate current state.

    The size of the expansion is determined by the size of the contents.

    :note:
        All standard groupbox features are supported

    .. code-block: python

        box = CollapsibleGroupBox()
        box.setTitle("test")
        box.setLayout(QtWidgets.QVBoxLayout(box))
        box.layout().addWidget(QtWidgets.QPushButton("test", parent=box))
        box.show()

    """

    def __init__(self, parent=None):
        super(CollapsibleGroupBox, self).__init__(parent)
        self.setCheckable(True)
        self.setChecked(True)
        self.toggled.connect(self.resizeGroupBox)
        plusIcon = iconlib.icon('arrowSingleUp')
        self.plusPixmap = plusIcon.pixmap(plusIcon.availableSizes()[0])
        icon = iconlib.icon('arrowSingleDown')
        self.minusPixmap = icon.pixmap(icon.availableSizes()[0])

    def resizeGroupBox(self, fullSize):
        """handles the sizing on toggle
        """
        if fullSize:
            self.setFixedHeight(self.sizeHint().height())
            self.setMinimumSize(0, 0)
        else:
            fontHeight = QtGui.QFontMetrics(QtWidgets.QApplication.font()).height() + 4
            self.setFixedHeight(fontHeight)

    def paintEvent(self, e):
        painter = QtWidgets.QStylePainter(self)
        option = QtWidgets.QStyleOptionGroupBox()
        self.initStyleOption(option)
        style = self.style()
        proxyStyle = style.proxy()
        textRect = proxyStyle.subControlRect(QtWidgets.QStyle.CC_GroupBox, option, QtWidgets.QStyle.SC_GroupBoxLabel,
                                             self)
        checkBoxRect = proxyStyle.subControlRect(QtWidgets.QStyle.CC_GroupBox, option,
                                                 QtWidgets.QStyle.SC_GroupBoxCheckBox, self)

        # deal with the checkstate of the group box
        if self.isChecked():
            frame = QtWidgets.QStyleOptionFrame()
            frame.operator = option
            frame.features = option.features
            frame.lineWidth = option.lineWidth
            frame.midLineWidth = option.midLineWidth
            frame.rect = proxyStyle.subControlRect(QtWidgets.QStyle.CC_GroupBox, option,
                                                   QtWidgets.QStyle.SC_GroupBoxFrame, self)
            proxyStyle.drawPrimitive(QtWidgets.QStyle.PE_FrameGroupBox, frame, painter, self)
        # now draw the title
        if option.text:
            painter.setPen(QtGui.QPen(option.palette.windowText(), 1))
            alignment = int(option.textAlignment)
            if not proxyStyle.styleHint(QtWidgets.QStyle.SH_UnderlineShortcut, option, self):
                alignment = alignment | QtCore.Qt.TextHideMnemonic
            style.proxy().drawItemText(painter, textRect, QtCore.Qt.TextShowMnemonic | QtCore.Qt.AlignLeft | alignment,
                                       option.palette, option.state & QtWidgets.QStyle.State_Enabled, option.text,
                                       QtGui.QPalette.NoRole)
        # deal with the arrow icons
        proxyStyle.drawItemPixmap(painter, checkBoxRect, QtCore.Qt.AlignLeft,
                                  self.minusPixmap if self.isChecked() else self.plusPixmap)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    box = CollapsibleGroupBox()
    box.setTitle("test")
    box.setLayout(QtWidgets.QVBoxLayout(box))
    box.layout().addWidget(QtWidgets.QPushButton("test", parent=box))
    box.show()
    sys.exit(app.exec_())