from Qt import QtGui, QtCore, QtWidgets


class ClippedLabel(QtWidgets.QLabel):
    _width = _text = _elided = None

    def __init__(self, text='', width=0, parent=None, ellipsis=True, alwaysShowAll=False):
        """ Label that will clip itself if the widget width is smaller than the text

        QLabel doesn't do this, so we have to do this here.

        .. code-block:: python

            # Ellipsis false will omit the ellipsis (...)
            wgt = ClippedLabel(text="Hello World", ellipsis=False)

            # With triple dot added if the size of the widget is too small
            wgt = ClippedLabel(text="Hello World", ellipsis=True)

            # Use it like any other QLabel
            layout = QtWidgets.QHBoxWidget()
            layout.addWidget(wgt)

        :param text:
        :param width:
        :param parent:
        :param ellipsis: True to show ellipsis, false for otherwise
        :param alwaysShowAll: True to always show the full text, if theres no space it wont show anything
        """
        super(ClippedLabel, self).__init__(text, parent)
        self.alwaysShowAll = alwaysShowAll
        self.setMinimumWidth(width if width > 0 else 1)
        self.ellipsis = ellipsis

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        self.drawFrame(painter)
        margin = self.margin()
        rect = self.contentsRect()
        rect.adjust(margin, margin, -margin, -margin)
        text = self.text()
        width = rect.width()
        if text != self._text or width != self._width:
            self._text = text
            self._width = width
            self._elided = self.fontMetrics().elidedText(
                text, QtCore.Qt.ElideRight, width)

        option = QtWidgets.QStyleOption()
        option.initFrom(self)

        if self.alwaysShowAll:
            # Show all text or show nothing
            if self._width >= self.sizeHint().width():
                self.style().drawItemText(
                    painter, rect, self.alignment(), option.palette,
                    self.isEnabled(), self.text(), self.foregroundRole())

        else:  # if alwaysShowAll is false though, draw the ellipsis as normal
            if self.ellipsis:
                self.style().drawItemText(
                    painter, rect, self.alignment(), option.palette,
                    self.isEnabled(), self._elided, self.foregroundRole())
            else:
                self.style().drawItemText(
                    painter, rect, self.alignment(), option.palette,
                    self.isEnabled(), self.text(), self.foregroundRole())