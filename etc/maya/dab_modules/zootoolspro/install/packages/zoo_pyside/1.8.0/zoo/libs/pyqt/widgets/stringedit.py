from Qt import QtWidgets, QtCore
from zoo.libs.pyqt import uiconstants, utils
from zoo.libs.pyqt.extended.lineedit import LineEdit, FloatLineEdit, IntLineEdit
from zoo.libs.pyqt.widgets.label import Label
from zoo.libs.pyqt.widgets.layouts import hBoxLayout, vBoxLayout


class StringEdit(QtWidgets.QWidget):
    textChanged = QtCore.Signal(str)  # Any change, each keypress
    buttonClicked = QtCore.Signal()  # if the button is clicked
    editingFinished = QtCore.Signal()  # qt style editFinish, does not update appropriately like Maya
    textModified = QtCore.Signal(str)  # Maya style update, on return and switching out of the text box use for GUIs
    returnPressed = QtCore.Signal()

    def __init__(self, label="", editText="", editPlaceholder="", buttonText=None, parent=None, editWidth=None,
                 labelRatio=1, btnRatio=1, editRatio=1, toolTip="",
                 orientation=QtCore.Qt.Horizontal, enableMenu=True, rounding=3):
        """Creates a label, textbox (QLineEdit) and an optional button
        if the button is None then no button will be created

        :param label: the label name
        :type label: str
        :param buttonText: optional button name, if None no button will be created
        :type buttonText: str
        :param parent: the qt parent
        :type parent: class
        :param editWidth: the width of the textbox in pixels optional, None is ignored
        :type editWidth: int
        :param labelRatio: the width ratio of the label/text/button corresponds to the ratios of ratioEdit/ratioBtn
        :type labelRatio: int
        :param btnRatio: the width ratio of the label/text/button corresponds to the ratios of editRatio/labelRatio
        :type btnRatio: int
        :param editRatio: the width ratio of the label/text/button corresponds to the ratios of labelRatio/btnRatio
        :type editRatio: int
        :param toolTip: the tool tip message on mouse over hover, extra info
        :type toolTip: str
        :param orientation: the orientation of the box layout QtCore.Qt.Horizontal HBox QtCore.Qt.Vertical VBox
        :type orientation: bool
        :param enableMenu: If True (default) uses ExtendedLineEdit, right/middle/left click menus can be added
        :type enableMenu: bool
        :return StringEdit: returns the class with various options, see the methods
        :rtype StringEdit: QWidget
        """
        super(StringEdit, self).__init__(parent=parent)

        self.label = None
        self.enableMenu = enableMenu
        self.QLineEditBool = True
        if orientation == QtCore.Qt.Horizontal:
            self.layout = hBoxLayout(self, (0, 0, 0, 0), spacing=uiconstants.SREG)
        else:
            self.layout = vBoxLayout(self, (0, 0, 0, 0), spacing=uiconstants.SREG)

        self._initValues = {"editText"}

        self.edit = self._initEdit(editText, placeholder=editPlaceholder, parent=parent, toolTip=toolTip,
                                   editWidth=editWidth, enableMenu=enableMenu, rounding=rounding)
        utils.setSkipChildren(self, True)

        if label:
            self.label = Label(label, parent=parent, toolTip=toolTip)
            self.layout.addWidget(self.label, labelRatio)
        self.layout.addWidget(self.edit, editRatio)
        self.buttonText = buttonText
        if self.buttonText:
            # todo button connections should be added from this class (connections)
            self.btn = QtWidgets.QPushButton(buttonText, parent)
            self.layout.addWidget(self.btn, btnRatio)
        self.connections()

    def _initEdit(self, editText, placeholder, parent, toolTip, editWidth, enableMenu, rounding=None):
        """ To be Overridden by class

        :return:
        :rtype: LineEdit
        """
        return LineEdit(editText, placeholder=placeholder, parent=parent, toolTip=toolTip, editWidth=editWidth,
                        enableMenu=enableMenu)

    def connections(self):
        """ Connects the buttons and text changed emit

        :return:
        :rtype:
        """
        self.edit.textChanged.connect(self._onTextChanged)
        self.edit.textModified.connect(self._onTextModified)
        if self.buttonText:
            self.btn.clicked.connect(self.buttonClicked.emit)
        self.editingFinished = self.edit.editingFinished
        self.edit.returnPressed.connect(self.returnPressed.emit)

    def _onTextChanged(self):
        """If the text is changed emit"""
        self.textChanged.emit(self.text())

    def _onTextModified(self):
        """If the text is modified (like Maya) emit"""
        self.textModified.emit(self.text())

    def text(self):
        """ Get the text from the edit

        :return:
        """
        return self.edit.text()

    def selectAll(self):
        """ Select all in the edit

        :return:
        :rtype:
        """
        return self.edit.selectAll()

    def setValue(self, value):
        """ Set the value

        :param value:
        :type value:
        :return:
        :rtype:
        """
        self.edit.setValue(value)

    def value(self):
        """ Get the edit value

        :return:
        :rtype:
        """
        return self.edit.value()

    def setDisabled(self, state):
        """Disable the text (make it grey)"""
        self.edit.setDisabled(state)
        if self.label:
            self.label.setDisabled(state)

    def setText(self, value):
        """Change the text at any time"""
        self.edit.setText(str(value))

    def setFocus(self):
        """ Set the focus of the edit

        :return:
        :rtype:
        """
        self.edit.setFocus()

    def setLabelFixedWidth(self, width):
        """Set the fixed width of the label"""
        self.label.setFixedWidth(utils.dpiScale(width))

    def setTxtFixedWidth(self, width):
        """Set the fixed width of the lineEdit"""
        self.edit.setFixedWidth(utils.dpiScale(width))

    def clearFocus(self):
        """ Clear the focus of the edit

        :return:
        :rtype:
        """
        self.edit.clearFocus()

    def blockSignals(self, b):
        """ Block signals properly

        :param b:
        :type b:
        :return:
        :rtype:
        """
        [c.blockSignals(b) for c in utils.iterChildren(self)]

    # ----------
    # MENUS
    # ----------

    def setMenu(self, menu, modeList=None, mouseButton=QtCore.Qt.RightButton):
        """Add the left/middle/right click menu by passing in a QMenu

        If a modeList is passed in then create/reset the menu to the modeList:

            [("icon1", "menuName1"), ("icon2", "menuName2")]

        If no modelist the menu won't change

        :param menu: the Qt menu to show on middle click
        :type menu: QtWidgets.QMenu
        :param modeList: a list of menu modes (tuples) eg [("icon1", "menuName1"), ("icon2", "menuName2")]
        :type modeList: list(tuple(str))
        :param mouseButton: the mouse button clicked QtCore.Qt.LeftButton, QtCore.Qt.RightButton, QtCore.Qt.MiddleButton
        :type mouseButton: QtCore.Qt.ButtonClick
        """
        if mouseButton != QtCore.Qt.LeftButton:  # don't create an edit menu if left mouse button menu
            self.edit.setMenu(menu, mouseButton=mouseButton)
        # only add the action list (menu items) to the label, as the line edit uses the same menu
        if self.label:
            self.label.setMenu(menu, modeList=modeList, mouseButton=mouseButton)

    def addActionList(self, modes, mouseButton=QtCore.Qt.RightButton):
        """resets the appropriate mouse click menu with the incoming modes

            modeList: [("icon1", "menuName1"), ("icon2", "menuName2"), ("icon3", "menuName3")]

        resets the lists and menus:

            self.menuiconstantsonList: ["icon1", "icon2", "icon3"]
            self.menuiconstantsonList: ["menuName1", "menuName2", "menuName3"]

        :param modes: a list of menu modes (tuples) eg [("icon1", "menuName1"), ("icon2", "menuName2")]
        :type modes: list(tuple(str))
        :param mouseButton: the mouse button clicked QtCore.Qt.LeftButton, QtCore.Qt.RightButton, QtCore.Qt.MiddleButton
        :type mouseButton: QtCore.Qt.ButtonClick
        """
        # only add the action list (menu items) to the label, as the line edit uses the same menu
        self.label.addActionList(modes, mouseButton=mouseButton)


class FloatEdit(StringEdit):

    def _initEdit(self, editText, placeholder, parent, toolTip, editWidth, enableMenu, rounding=None):
        """ To be Overridden by class

        :return:
        :rtype: FloatLineEdit
        """

        return FloatLineEdit(editText, placeholder=placeholder, parent=parent, toolTip=toolTip, editWidth=editWidth,
                             enableMenu=enableMenu, rounding=rounding)


class IntEdit(StringEdit):

    def _initEdit(self, editText, placeholder, parent, toolTip, editWidth, enableMenu, rounding=None):
        """ To be Overridden by class

        :return:
        :rtype: LineEdit
        """
        return IntLineEdit(editText, placeholder=placeholder, parent=parent, toolTip=toolTip, editWidth=editWidth,
                           enableMenu=enableMenu)
