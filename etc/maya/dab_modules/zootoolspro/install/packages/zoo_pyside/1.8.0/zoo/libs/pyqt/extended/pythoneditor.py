import os
import sys
import traceback

from Qt import QtWidgets, QtGui, QtCore
from zoo.libs.pyqt.syntaxhighlighter import highlighter
from zoo.libs.pyqt.widgets import elements


class NumberBar(QtWidgets.QWidget):

    def __init__(self, edit):
        super(NumberBar, self).__init__(edit)

        self.edit = edit
        self.adjustWidth(1)

    def paintEvent(self, event):
        self.edit.numberbarPaint(self, event)
        super(NumberBar, self).paintEvent(event)

    def adjustWidth(self, count):
        pass
        # width = self.fontMetrics().width(count)
        # if self.width() != width:
        #     self.setFixedWidth(width)

    def updateContents(self, rect, scroll):
        if scroll:
            self.scroll(0, scroll)
        else:
            self.update()


class TextEditor(QtWidgets.QPlainTextEdit):

    def __init__(self, parent=None):
        super(TextEditor, self).__init__(parent=parent)
        self.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
        self.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.setFrameStyle(QtWidgets.QFrame.NoFrame)
        self.centerOnScroll()
        self.highlight()
        self.cursorPositionChanged.connect(self.highlight)
        metrics = QtGui.QFontMetrics(self.document().defaultFont())
        self.setTabStopWidth(4 * metrics.width(' '))
        font = QtGui.QFont("Courier")
        font.setStyleHint(QtGui.QFont.Monospace)
        font.setFixedPitch(True)
        self.setFont(font)

    def highlight(self):
        hi_selection = QtWidgets.QTextEdit.ExtraSelection()

        # hi_selection.format.setBackground(self.palette().dark()) # temp
        hi_selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
        hi_selection.cursor = self.textCursor()
        hi_selection.cursor.clearSelection()

        self.setExtraSelections([hi_selection])

    def numberbarPaint(self, number_bar, event):
        font_metrics = self.fontMetrics()
        current_line = self.document().findBlock(self.textCursor().position()).blockNumber() + 1

        block = self.firstVisibleBlock()
        line_count = block.blockNumber()
        painter = QtGui.QPainter(number_bar)
        painter.fillRect(event.rect(), self.palette().base())

        # Iterate over all visible text blocks in the document.
        while block.isValid():
            line_count += 1
            block_top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()

            # Check if the position of the block is out side of the visible
            # area.
            if not block.isVisible() or block_top >= event.rect().bottom():
                break

            # We want the line number for the selected line to be bold.
            if line_count == current_line:
                font = painter.font()
                font.setBold(True)
                painter.setFont(font)
            else:
                font = painter.font()
                font.setBold(False)
                painter.setFont(font)

            # Draw the line number right justified at the position of the line.
            paint_rect = QtCore.QRect(0, block_top, number_bar.width(), font_metrics.height())
            painter.drawText(paint_rect, QtCore.Qt.AlignRight, line_count)

            block = block.next()

        painter.end()

    def wheelEvent(self, event):
        """
        Handles zoom in/out of the text.
        """
        if event.modifiers() & QtCore.Qt.ControlModifier:
            delta = event.delta()
            if delta < 0:
                self.zoom(-1)
            elif delta > 0:
                self.zoom(1)
            return True
        return super(TextEditor, self).wheelEvent(event)

    def zoom(self, direction):
        """
        Zoom in on the text.
        """

        font = self.font()
        size = font.pointSize()
        if size == -1:
            size = font.pixelSize()

        size += direction

        if size < 7:
            size = 7
        if size > 50:
            return

        style = """
        QWidget {
            font-size: %spt;
        }
        """ % (size,)
        self.setStyleSheet(style)

    def keyPressEvent(self, event):
        if (event.modifiers() & QtCore.Qt.ShiftModifier and
                event.key() in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]):
            self.insertPlainText("\n")
            event.accept()
        elif event.key() == QtCore.Qt.Key_Tab:
            # intercept the tab key and insert 4 spaces
            self.insertPlainText("    ")
            event.accept()
        else:
            super(TextEditor, self).keyPressEvent(event)
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter) and event.modifiers() == QtCore.Qt.ControlModifier:
            self.parent().execute()


class Editor(QtWidgets.QFrame):
    outputText = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(Editor, self).__init__(parent=parent)
        self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Sunken)
        self._locals = {}
        self.textEdit = TextEditor(parent=self)
        self.numberBar = NumberBar(self.textEdit)

        hbox = elements.hBoxLayout(parent=self)
        hbox.addWidget(self.numberBar)
        hbox.addWidget(self.textEdit)

        self.textEdit.blockCountChanged.connect(self.numberBar.adjustWidth)
        self.textEdit.updateRequest.connect(self.numberBar.updateContents)
        self.pythonHighlighter = highlighter.highlighterFromJson(os.path.join(os.path.dirname(highlighter.__file__),
                                                                              "highlightdata.json"),
                                                                 self.textEdit.document())

    def text(self):
        return self.textEdit.toPlainText()

    def setText(self, text):
        self.textEdit.setPlainText(text)

    def isModified(self):
        return self.edit.document().isModified()

    def setModified(self, modified):
        self.edit.document().setModified(modified)

    def setLineWrapMode(self, mode):
        self.edit.setLineWrapMode(mode)

    def execute(self):
        original_stdout = sys.stdout

        class stdoutProxy():
            def __init__(self, write_func):
                self.write_func = write_func
                self.skip = False

            def write(self, text):
                if not self.skip:
                    stripped_text = text.rstrip('\n')
                    self.write_func(stripped_text)
                self.skip = not self.skip

            def flush(self):
                pass

        sys.stdout = stdoutProxy(self.outputText.emit)

        cursor = self.textEdit.textCursor()
        script = cursor.selectedText()
        script = script.replace(u"\u2029", "\n")

        if not script:
            script = str(self.toPlainText().strip())
        if not script:
            return
        self.outputText.emit(script)
        evalCode = True
        try:
            try:
                outputCode = compile(script, "<string>", "eval")
            except SyntaxError:
                evalCode = False
                outputCode = compile(script, "<string>", "exec")
            except Exception:
                trace = traceback.format_exc()
                self.outputText.emit(trace)
                return

            # ok we've compiled the code now exec
            if evalCode:
                try:
                    results = eval(outputCode, globals(), self._locals)
                    self.outputText.emit(str(results))
                except Exception:
                    trace = traceback.format_exc()
                    self.outputText.emit(trace)
            else:
                try:
                    exec (outputCode, globals(), self._locals)
                except Exception:
                    trace = traceback.format_exc()
                    self.outputText.emit(trace)
        finally:
            sys.stdout = original_stdout


class TabbedEditor(QtWidgets.QTabWidget):
    outputText = QtCore.Signal(str)

    def __init__(self, parent):
        super(TabbedEditor, self).__init__(parent=parent)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.newTabBtn = QtWidgets.QPushButton("+", parent=self)
        self.newTabBtn.setMaximumWidth(40)
        self.newTabBtn.setToolTip("Add New Tab")
        self.setCornerWidget(self.newTabBtn, QtCore.Qt.TopLeftCorner)
        self.newTabBtn.clicked.connect(self.addNewEditor)
        self.tabCloseRequested.connect(self.closeCurrentTab)

    def addNewEditor(self, name=None):
        name = name or "New tab"
        edit = Editor(parent=self)
        self.addTab(edit, name)
        edit.outputText.connect(self.outputText.emit)
        edit.textEdit.moveCursor(QtGui.QTextCursor.Start)
        self.setCurrentIndex(self.count() - 1)

    def closeCurrentTab(self, index):
        self.removeTab(index)
