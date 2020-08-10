from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import dialog, layouts
from Qt import QtCore, QtWidgets


class FloatingButton(dialog.Dialog):
    clicked = QtCore.Signal()

    def __init__(self, parent=None, size=24):
        """ Floating Button that can be placed anywhere on the screen

        Essentially a floating frameless transparent window. It doesn't float outside the parent,
        so make sure the button is within the parent bounds to be visible.

        .. code-block:: python

            # use .button to access the actual push button
            floatBtn = FloatingButton(parent=self)
            floatBtn.button.clicked.connect(self.floatButtonClicked)

            # Use .move to move it around the window. Note: It's not visible outside the parent's bounds
            floatBtn.move(20,20)

            # Use setAlignment() to align the edge of the FloatingButton when moving.
            floatBtn.setAlignment(QtCore.Qt.AlignTop) # Top of button will at the new move position
            floatBtn.setAlignment(QtCore.Qt.AlignLeft) # Bottom of button will at the new move position

            floatBtn.move(20,20) # Use move to update the position

        :param parent:
        """
        super(FloatingButton, self).__init__(parent=parent, showOnInitialize=False)
        self.button = QtWidgets.QPushButton(parent=self)
        self.mainLayout = layouts.hBoxLayout(self)
        self.resize(utils.dpiScale(size), utils.dpiScale(size))
        self.alignment = QtCore.Qt.AlignBottom

        self.initUi()
        self.setStyleSheet("background-color: transparent;")

    def setAlignment(self, align):
        """ Set alignment of the button. Use .move() to update the position

        :param align:
        :return:
        """
        self.alignment = align

    def initUi(self):
        """ Init Ui

        :return:
        """

        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.button.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        self.mainLayout.addWidget(self.button)

        self.show()

        self.button.clicked.connect(self.clicked.emit)

    def move(self, x, y):
        """ Move the FloatingButton based on alignment.

        :param x:
        :param y:
        :return:
        """
        w = self.rect().width()
        h = self.rect().height()

        if self.alignment == QtCore.Qt.AlignTop:
            super(FloatingButton, self).move(x+(w*0.5), y)
        elif self.alignment == QtCore.Qt.AlignRight:
            super(FloatingButton, self).move(x-w, y-(h*0.5))
        elif self.alignment == QtCore.Qt.AlignBottom:
            super(FloatingButton, self).move(x, y-h)
        elif self.alignment == QtCore.Qt.AlignLeft:
            super(FloatingButton, self).move(x, y-(h*0.5))
