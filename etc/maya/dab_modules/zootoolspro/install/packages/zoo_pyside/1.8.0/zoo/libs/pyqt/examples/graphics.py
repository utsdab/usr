import sys

from Qt import QtWidgets
from zoo.libs.pyqt.widgets import mainwindow
from zoo.libs.pyqt.widgets.graphics import graphbackdrop
from zoo.libs.pyqt.widgets.graphics import graphicsscene
from zoo.libs.pyqt.widgets.graphics import graphicsview
from zoo.libs.pyqt.widgets.graphics import graphviewconfig


class Window(mainwindow.MainWindow):
    def __init__(self, title="test", width=600, height=800, icon="", parent=None, showOnInitialize=True):
        super(Window, self).__init__(title, width, height, icon, parent, showOnInitialize)
        layout = QtWidgets.QVBoxLayout()
        self.centralWidget.setLayout(layout)
        self.view = graphicsview.GraphicsView(config=graphviewconfig.Config, parent=self)
        self.scene = graphicsscene.GraphicsScene(parent=self)
        self.view.setScene(self.scene)
        layout.addWidget(self.view)

        backdrop = graphbackdrop.BackDrop("test backdrop")
        self.scene.addItem(backdrop)

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    win = Window()
    sys.exit(app.exec_())