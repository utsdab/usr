#!/usr/bin/env rmanpy

# Import PySide classes
# import sys
# from PySide.QtCore import *
# from PySide.QtGui import *
#
# # Create a Qt application
# app = QApplication(sys.argv)
# # Create a Label and show it
# label = QLabel("Hello World")
# label = QLabel("<font color=red size=40>Hello World</font>")
# label.show()
# # Enter Qt application main loop
# app.exec_()
# sys.exit()


import sys
from PySide import QtGui


class Example(QtGui.QWidget):

    def __init__(self):
        super(Example, self).__init__()

        self.initUI()

    def initUI(self):

        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('Message box')
        self.show()

    def closeEvent(self, event):

        reply = QtGui.QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QtGui.QMessageBox.Yes |
            QtGui.QMessageBox.No, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


def main():

    app = QtGui.QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()