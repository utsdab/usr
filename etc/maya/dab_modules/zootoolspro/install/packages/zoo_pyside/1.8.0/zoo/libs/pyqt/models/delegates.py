from Qt import QtWidgets, QtCore, QtGui
from zoo.libs.pyqt.extended import combobox
from zoo.libs.pyqt.models import constants


def drawRect(painter, option, color):
    points = (QtCore.QPoint(option.rect.x() + 5, option.rect.y()),
              QtCore.QPoint(option.rect.x(), option.rect.y()),
              QtCore.QPoint(option.rect.x(), option.rect.y() + 5))
    polygonTriangle = QtGui.QPolygon.fromList(points)

    painter.save()
    painter.setRenderHint(painter.Antialiasing)
    painter.setBrush(QtGui.QBrush(color))
    painter.setPen(QtGui.QPen(color))
    painter.drawPolygon(polygonTriangle)
    painter.restore()


class NumericDoubleDelegate(QtWidgets.QItemDelegate):
    def __init__(self, parent):
        super(NumericDoubleDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        model = index.model()
        widget = QtWidgets.QDoubleSpinBox(parent=parent)
        widget.setMinimum(model.data(index, constants.minValue))
        widget.setMaximum(constants.maxValue)
        return widget

    def setEditorData(self, widget, index):
        value = index.model().data(index, QtCore.Qt.EditRole)
        widget.setValue(value)

    def setModelData(self, widget, model, index):
        value = widget.value()
        model.setData(index, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def paint(self, painter, option, index):
        super(NumericDoubleDelegate, self).paint(painter, option, index)
        model = index.model()
        color = model.data(index, constants.editChangedRole)
        if color is None:
            return
        drawRect(painter, option, color)

class NumericIntDelegate(QtWidgets.QItemDelegate):
    def __init__(self, parent):
        super(NumericIntDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        model = index.model()
        widget = QtWidgets.QSpinBox(parent=parent)
        widget.setMinimum(model.data(index, constants.minValue))
        widget.setMaximum(model.data(index, constants.maxValue))
        return widget

    def setEditorData(self, widget, index):
        value = index.model().data(index, QtCore.Qt.EditRole)
        widget.setValue(value)

    def setModelData(self, widget, model, index):
        value = widget.value()
        model.setData(index, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def paint(self, painter, option, index):
        super(NumericIntDelegate, self).paint(painter, option, index)
        model = index.model()
        color = model.data(index, constants.editChangedRole)
        if color is None:
            return
        drawRect(painter, option, color)


class EnumerationDelegate(QtWidgets.QItemDelegate):
    def __init__(self, parent):
        super(EnumerationDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        model = index.model()
        combo = combobox.ExtendedComboBox(model.data(index, constants.enumsRole), parent)
        return combo

    def setEditorData(self, editor, index):
        editor.blockSignals(True)
        text = index.model().data(index, QtCore.Qt.DisplayRole)
        index = editor.findText(text, QtCore.Qt.MatchFixedString)
        if index >= 0:
            editor.setCurrentIndex(index)
        editor.blockSignals(False)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentIndex(), role=QtCore.Qt.EditRole)

    def paint(self, painter, option, index):
        super(EnumerationDelegate, self).paint(painter, option, index)
        model = index.model()
        color = model.data(index, constants.editChangedRole)
        if color is None:
            return
        drawRect(painter, option, color)


class ButtonDelegate(QtWidgets.QItemDelegate):
    def __init__(self, parent):
        super(ButtonDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        model = index.model()

        widget = QtWidgets.QPushButton(model.data(QtCore.Qt.DisplayRole), parent=parent)
        widget.clicked.connect(self.onClicked)
        return widget

    def onClicked(self):
        self.commitData.emit(self.sender())

    def setEditorData(self, widget, index):
        pass

    def setModelData(self, widget, model, index):
        model.setData(index, 1, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def paint(self, painter, option, index):
        super(ButtonDelegate, self).paint(painter, option, index)
        model = index.model()
        color = model.data(index, constants.editChangedRole)
        if color is None:
            return
        drawRect(painter, option, color)


class CheckBoxDelegate(QtWidgets.QStyledItemDelegate):
    """
    A delegate that places a fully functioning QCheckBox in every
    cell of the column to which it's applied
    """

    def __init__(self, parent):
        super(CheckBoxDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        """
        Important, otherwise an editor is created if the user clicks in this cell.
        ** Need to hook up a signal to the model
        """
        return None

    def paint(self, painter, option, index):
        """
        Paint a checkbox without the label.
        """

        checked = bool(index.data())
        check_box_style_option = QtWidgets.QStyleOptionButton()
        isEnabled = (index.flags() & QtCore.Qt.ItemIsEditable) > 0 and (index.flags() & QtCore.Qt.ItemIsEnabled) > 0
        if isEnabled:
            check_box_style_option.state |= QtWidgets.QStyle.State_Enabled
        else:
            check_box_style_option.state |= QtWidgets.QStyle.State_ReadOnly

        if checked:
            check_box_style_option.state |= QtWidgets.QStyle.State_On
        else:
            check_box_style_option.state |= QtWidgets.QStyle.State_Off
        check_box_style_option.rect = self.getCheckBoxRect(option)

        check_box_style_option.state |= QtWidgets.QStyle.State_Enabled

        QtWidgets.QApplication.style().drawControl(QtWidgets.QStyle.CE_CheckBox, check_box_style_option, painter)
        model = index.model()
        color = model.data(index, constants.editChangedRole)
        if color is None:
            return
        drawRect(painter, option, color)

    def editorEvent(self, event, model, option, index):
        """
        Change the data in the model and the state of the checkbox
        if the user presses the left mousebutton or presses
        Key_Space or Key_Select and this cell is editable. Otherwise do nothing.
        """
        if index.flags() & QtCore.Qt.ItemIsEditable < 1:
            return False

        # Do not change the checkbox-state
        if event.type() == QtCore.QEvent.MouseButtonPress or event.type() == QtCore.QEvent.MouseMove or event.type() == QtCore.QEvent.KeyPress:
            return False
        elif event.type() == QtCore.QEvent.MouseButtonRelease or event.type() == QtCore.QEvent.MouseButtonDblClick:
            if event.button() != QtCore.Qt.LeftButton or not self.getCheckBoxRect(option).contains(event.pos()):
                return False
            if event.type() == QtCore.QEvent.MouseButtonDblClick:
                return True

        # Change the checkbox-state
        self.setModelData(None, model, index)
        return True

    def setModelData(self, editor, model, index):
        """
        The user wanted to change the old state in the opposite.
        """
        newValue = not index.data()
        model.setData(index, newValue, QtCore.Qt.EditRole)

    def getCheckBoxRect(self, option):
        check_box_style_option = QtWidgets.QStyleOptionButton()
        check_box_rect = QtWidgets.QApplication.style().subElementRect(QtWidgets.QStyle.SE_CheckBoxIndicator,
                                                                       check_box_style_option, None)
        check_box_point = QtCore.QPoint(option.rect.x() +
                                        option.rect.width() / 2 -
                                        check_box_rect.width() / 2,
                                        option.rect.y() +
                                        option.rect.height() / 2 -
                                        check_box_rect.height() / 2)
        return QtCore.QRect(check_box_point, check_box_rect.size())


class PixmapDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent):
        super(PixmapDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        icon = index.data(index, role=QtCore.Qt.DecorationRole)
        pixmap = icon.pixmap(icon.actualSize())
        painter.drawPixmap(option.rect.topLeft, pixmap)
        model = index.model()
        color = model.data(index, constants.editChangedRole)
        if color is None:
            return
        drawRect(painter, option, color)
        super(PixmapDelegate, self).paint(painter, option, index)


class DateColumnDelegate(QtWidgets.QStyledItemDelegate):

    def __init__(self, dateFormat="yyyy-MM-dd", parent=None):
        super(DateColumnDelegate, self).__init__(parent)
        self.format = dateFormat

    def createEditor(self, parent, option, index):
        model = index.model()
        dateedit = QtWidgets.QDateEdit(parent)
        dateedit.setDateRange(model.data(index, constants.minValue), model.data(index, constants.maxValue))
        dateedit.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        dateedit.setDisplayFormat(self.format)
        dateedit.setCalendarPopup(True)
        return dateedit

    def setEditorData(self, editor, index):
        value = index.model().data(index, QtCore.Qt.DisplayRole)
        editor.setDate(value)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.date())

    def paint(self, painter, option, index):
        super(DateColumnDelegate, self).paint(painter, option, index)
        model = index.model()
        color = model.data(index, constants.editChangedRole)
        if color is None:
            return
        drawRect(painter, option, color)
