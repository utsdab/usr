from zoo.apps.preferencesui.example import main_view
from Qt import QtWidgets


def exampleWidget(parent=None):
    win = QtWidgets.QMainWindow(parent)
    ui = main_view.Ui_MainWindow()
    ui.setupUi(win)
    return win
