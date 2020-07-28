from Qt import QtWidgets
from zoo.libs.pyqt import utils


def FileDialog_directory(windowName="", parent="", defaultPath=""):
    """simple function for QFileDialog.getExistingDirectory, a window popup that searches for a directory

    Browses for a directory with a fileDialog window and returns the selected directory

    :param windowName: The name of the fileDialog window
    :type windowName: str
    :param parent: The parent widget
    :type parent: Qt.widget
    :param defaultPath: The default directory path, where to open the fileDialog window
    :type defaultPath: str
    :return directoryPath: The selected full directory path
    :rtype directoryPath: str
    """
    directoryPath = str(QtWidgets.QFileDialog.getExistingDirectory(parent, windowName, defaultPath))
    if not directoryPath:
        return
    return directoryPath


def MessageBox_ok(windowName="Confirm", parent=None, message="Proceed?", okButton=QtWidgets.QMessageBox.Ok):
    """Simple function for ok/cancel QMessageBox.question, a window popup that with ok/cancel buttons

    :param windowName: The name of the ok/cancel window
    :type windowName: str
    :param parent: The parent widget
    :type parent: Qt.widget
    :param message: The message to ask the user
    :type message: str
    :return okPressed: True if the Ok button was pressed, False if cancelled
    :rtype okPressed: bool
    """
    result = QtWidgets.QMessageBox.question(parent, windowName, message, QtWidgets.QMessageBox.Cancel | okButton)
    if result != QtWidgets.QMessageBox.Cancel:
        return True
    return False


def MessageBox_save(windowName="Confirm", parent=None, message="Proceed?", showDiscard=True):
    """Simple function for save/don't save/cancel QMessageBox.question, a window popup with buttons

    Can have two or three buttons:

        showDiscard True: Save, Discard, Cancel
        showDiscard False: Save, Cancel

    :param windowName: The name of the ok/cancel window
    :type windowName: str
    :param parent: The parent widget
    :type parent: Qt.widget
    :param message: The message to ask the user
    :type message: str
    :return buttonClicked: "cancel", "save", or "discard"
    :rtype buttonClicked: str
    """
    if showDiscard:
        result = QtWidgets.QMessageBox.question(parent, windowName, message,
                                                QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard |
                                                QtWidgets.QMessageBox.Cancel)
    else:
        result = QtWidgets.QMessageBox.question(parent, windowName, message,
                                                QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Cancel)
    if result == QtWidgets.QMessageBox.Cancel:
        return "cancel"
    if result == QtWidgets.QMessageBox.Save:
        return "save"
    if result == QtWidgets.QMessageBox.Discard:
        return "discard"


def InputDialog(windowName="Add Name", textValue="", parent=None, message="Rename?", windowWidth=270, windowHeight=100):
    """Opens a simple QT window that locks the program asking the user to input a string into a text box

    Useful for renaming etc.

    :param windowName: The name of the ok/cancel window
    :type windowName: str
    :param textValue: The initial text in the textbox, eg. The name to be renamed
    :type textValue: str
    :param parent: The parent widget
    :type parent: Qt.widget
    :param message: The message to ask the user
    :type message: str
    :return newTextValue: The new text name entered
    :rtype newTextValue: str
    """
    dialog = QtWidgets.QInputDialog(parent)
    dialog.setInputMode(QtWidgets.QInputDialog.TextInput)
    dialog.setTextValue(textValue)
    dialog.setWindowTitle(windowName)
    dialog.setLabelText(message)
    dialog.resize(utils.dpiScale(windowWidth), utils.dpiScale(windowHeight))
    ok = dialog.exec_()
    newTextValue = dialog.textValue()
    if not ok:
        return ""
    return newTextValue


def SaveDialog(directory, fileExtension="", nameFilters=""):
    """Opens a Qt save window with options

    Returns the path of the file to be created, or "" if the cancel button was clicked.

    :param directory: The path of the directory to default when the dialog window appears
    :type directory: str
    :param fileExtension: Optional fileExtension eg ".zooScene"
    :type fileExtension:
    :param nameFilters: Optional list of filters, example ['ZOOSCENE (*.zooScene)']
    :type nameFilters: list(str)
    :return fullFilePath: The fullPath of the file to be saved, else "" if cancelled
    :rtype fullFilePath: str
    """
    saveDialog = QtWidgets.QFileDialog()
    if fileExtension:
        saveDialog.setDefaultSuffix(fileExtension)
    saveDialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
    saveDialog.setDirectory(directory)
    if nameFilters:
        saveDialog.setNameFilters(nameFilters)
    if saveDialog.exec_() == QtWidgets.QDialog.Accepted:
        return saveDialog.selectedFiles()[0]
    else:
        return ""