"""
A Simple Script editor with basic syntax highlighting which include mel and python.
Nothing fancy
"""

from zoo.libs.maya.qt import mayaui
from zoo.libs.pyqt.widgets import dialog, layouts
from zoo.libs.pyqt.extended import pythoneditor
from Qt import QtWidgets, QtGui


class MayaScriptEditorDialog(dialog.Dialog):
    """A Simple Mel/python dialog which contains a mel textEditor including autocompletion and highlighter"""
    def __init__(self, title="", width=600, height=800, icon="", parent=None, showOnInitialize=True):
        super(MayaScriptEditorDialog, self).__init__(title, width, height, icon, parent, showOnInitialize)
        layout = elements.vBoxLayout(self)
        self.currentType = "python"
        self.sourceTypeWidget = elements.RadioButtonGroup(("mel", "python"), default=1, parent=self)
        layout.addWidget(self.sourceTypeWidget)
        self.melEditor, self._melInternalWidget = mayaui.highlighterEditorWidget(sourceType="mel",
                                                                                 **{"showLineNumbers": True})
        self.melEditor.hide()
        melHighlighter = self.melEditor.findChild(QtGui.QSyntaxHighlighter)
        melHighlighter.setDocument(self._melInternalWidget.document())
        self.pythonEditor = pythoneditor.Editor(parent=self)
        layout.addWidget(self.melEditor)
        layout.addWidget(self.pythonEditor)
        self.sourceTypeWidget.toggled.connect(self.onSourceTypeChanged)

    def onSourceTypeChanged(self, arg):
        self.currentType = self.sourceTypeWidget.isChecked().text()
        if self.currentType == "python":
            self.pythonEditor.show()
            self.melEditor.hide()
            return
        self.pythonEditor.hide()
        self.melEditor.show()

    def text(self):
        return {"python": self.pythonEditor.text(),
                "mel": self.melEditor.toPlainText()}
