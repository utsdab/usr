#!/opt/pixar/Tractor-2.0/bin/rmanpy
__author__ = '120988'


import sys

###############################################################
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)5.5s \t%(name)s \t%(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)
###############################################################
logger.info("Name = %s"%(__name__))


from PySide import QtGui


class Example(QtGui.QMainWindow):

    def __init__(self):
        super(Example, self).__init__()

        self.initUI()

    def initUI(self):

        self.textEdit = QtGui.QTextEdit()
        self.setCentralWidget(self.textEdit)
        self.statusBar()

        openfile = QtGui.QAction(QtGui.QIcon('open.png'), 'Open', self)
        openfile.setShortcut('Ctrl+O')
        openfile.setStatusTip('Open new File')
        openfile.triggered.connect(self.showDialog)

        menubar = self.menuBar()
        filemenu = menubar.addMenu('&File')
        filemenu.addAction(openfile)

        self.setGeometry(300, 300, 350, 300)
        self.setWindowTitle('File dialog')
        self.show()

    def showDialog(self):

        fname, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open file', '/home')

        f = open(fname, 'r')

        with f:
            data = f.read()
            self.textEdit.setText(data)


def main():

    app = QtGui.QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()