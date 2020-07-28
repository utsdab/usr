import os

from zoovendor.six.moves.html_parser import HTMLParser

from Qt import QtCore, QtWidgets, QtGui

from zoo.libs import iconlib
from zoo.libs.pyqt.widgets import dialog


class ExpandedTooltipPopup(dialog.Dialog):
    """
    Expanded tooltips for when we press control (or the key as defined by popupKey).
    Features richtext labels and animated gifs in a transparent window.
    ::examples:

    To install the tooltip on a PyQt widget:

    .. code-block:: python

        btn = QtWidgets.QPushButton()
        toolTip = componentWidgetExpand = \
            {
                "title": "Expand / Collapse Widget",
                "icon": "magic",
                "tooltip": "Expand / Collapse Widget",
                "expanded": "Expand / Collapse Widget <p><b><i>Everything here can be customized using HTML tags.</i></b></p><p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Duis et cursus libero. </p><p>Etiam viverra quam sit amet eros volutpat, ac <span class=\"highlight\"><i>aliquam ligula fringilla</i></span>. In semper volutpat nunc, ac placerat nisi mollis a. Donec condimentum urna eu elementum hendrerit. Sed pellentesque.</p><p> <a href=\"http://create3dcharacters.com\">Click for full documentation</a>"
            }
        installTooltips(btn, tooltipDict=toolTip)

    The "expanded" attribute allows for rich text:

    .. code-block:: python

        {"expanded":
            ''' Expand / Collapse Widget
                <p><b><i>Everything here can be customized using HTML tags.</i></b></p>
                <p><span class=\"highlight\">Highlighted text with custom highlight color </span>
                <p>Gifs can be used as well. <zoo gif=\"selectAllAnimCurvesInTheScene\" /></p>
                <p> <a href=\"http://create3dcharacters.com\">Click for full documentation</a>"'''}

    Gifs folders are set up in the package.json:
    "HIVE_UI_GIFS": "{self}/zoo/apps/hiveartistui/gifs"

    ExpandedTooltipPopup is just a dialogue box, so instantiate it then move it like a normal window:

    .. code-block:: python

        # On holding down control the popup (this class) will be displayed. ON Key release it will be closed
        def keyPressEvent(self, event):
            if event.key() == QtCore.Qt.Key_Control:
                pos = QtGui.QCursor.pos()
                widgetAt = QtWidgets.QApplication.widgetAt(pos)
                if expandedtooltip.hasExpandedTooltips(widgetAt):
                    self._popuptooltip = expandedtooltip.ExpandedTooltipPopup(widgetAt, keyRelease=QtCore.Qt.Key_Control)
                    self._popuptooltip.move(QtGui.QCursor.pos())
            self.ctrlEvent = True
        def keyReleaseEvent(self, event):
            if event.key() == QtCore.Qt.Key_Control:
                self.ctrlEvent = False

    Example Stylesheet:

    .. code-block:: python

        style = '''
           ExpandedTooltipPopup .QFrame {{
               border-width: 1px;
               border-style: solid;
               border-radius: 3px;
               border-color: rgba(255,255,255,0.5);
               background-color: rgba(20,20,20,0.8);
           }}
           ExpandedTooltipPopup QLabel {{
               border-width: 0px; background: transparent;
               font-size: 11pt;
           }}
           ExpandedTooltipPopup QLabel#title {{
               padding: 5px 0px 0px 0px;
               font-size: 14pt;
           }}
           ExpandedTooltipPopup GifWidget {{
               border-width: 0px; background: transparent;
           }}
        '''

    """

    defaultIcon = "magic"
    popupKey = QtCore.Qt.Key_Control

    ETT_ICONCOLOUR = (82, 133, 166)
    ETT_LINKCOLOUR = (255, 255, 255)
    ETT_THEMECOLOUR = (82, 133, 166)

    def __init__(self, widget,
                 width=450, height=50,
                 iconSize=40, parent=None, showOnInitialize=False, stylesheet="",
                 popupRelease=QtCore.Qt.Key_Control, showAtCursor=True):
        super(ExpandedTooltipPopup, self).__init__(None, width, height, "", parent, showOnInitialize)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.font = QtGui.QFont("sans")
        self.titleFont = QtGui.QFont("sans")

        # Maybe should link this with the stylesheets
        self.iconColour = self.ETT_ICONCOLOUR
        self.themeColour = self.ETT_THEMECOLOUR
        self.linkColour = self.ETT_LINKCOLOUR
        self.popupKey = popupRelease
        self.iconSize = iconSize

        self.frameLayout = QtWidgets.QVBoxLayout()
        self.titleLayout = QtWidgets.QHBoxLayout()
        self.frame = QtWidgets.QFrame(self)
        self.titleLabel = QtWidgets.QLabel(self)

        self.tooltipIcon = None  # type: QtCore.QIcon
        self.widget = widget

        if stylesheet != "":
            self.setStyleSheet(stylesheet)

        self.initUi()

        self.show()

        if showAtCursor:
            self.move(QtGui.QCursor.pos())

        self.setStyle(self.style())

    def initUi(self):
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        self.frame.setLayout(self.frameLayout)

        self.setIcon(self.widget._expandedTooltips_.icon)
        self.setTitle(self.widget._expandedTooltips_.title)

        self.titleLayout.addWidget(self.tooltipIcon)
        self.titleLayout.setContentsMargins(1, 1, 1, 1)
        self.titleLayout.setSpacing(2)
        self.titleLayout.addWidget(self.titleLabel)
        self.titleLayout.setStretch(1, 3)
        self.setMouseTracking(True)

        self.titleLabel.setObjectName("title")

        self.setLayout(self.layout)
        self.layout.setContentsMargins(6, 4, 6, 8)
        self.layout.addWidget(self.frame)
        self.frameLayout.addLayout(self.titleLayout)

        self.setText(self.widget._expandedTooltips_.text)

    def center(self):
        """Override the center from parent class and ignore everything.
        """
        pass

    def setText(self, text, applyStyle=True):
        """Sets the text for the ExpandedTooltip. It will parse through the text and split it up into
        Labels and GifWidgets and add it to the layout if need be.

        :param text:
        :param applyStyle:
        :return:
        """
        if applyStyle:
            text = self.applyStyle(text)

        parser = WidgetsFromTextParser(text)

        # self.clear()
        self.addWidgets(parser.widgets())

    def applyStyle(self, text):
        """Apply our own custom style to the text. A bit hacky but it replaces the text to
        what we want. Until we figure a way to apply custom classes to the rich text inside
        labels

        class="link"       ====>    style="color:rgb()"
        class="highlight"  ====>    style="color: rgb{}; font-weight: bold"
        etc..

        :param text:
        :type text: str
        :return:
        :rtype: str
        """
        # Not sure how to add styles in qt css so I'm going to add my hacky way here.. Maybe QTextBrowser better?
        text = text.replace("class=\"link\"", "style=\"color: rgb{}\" ".format(self.linkColour))
        text = text.replace("class=\"highlight\"",
                            "style=\"color: rgb{}; font-weight: bold\" ".format(self.themeColour))
        text = text.replace("<a href=", "<a style=\"color: rgb{}; font-weight: bold\" href=".format(self.themeColour))
        return text

    def addWidgets(self, wlist):
        """Adds the list of widgets into our layout

        :param wlist:
        :type wlist: list(QtWidgets.QWidget)
        """
        for w in wlist:
            self.frameLayout.addWidget(w)

    def clear(self):
        """Clear all the widgets in the frameLayout
        """
        for i in reversed(range(self.frameLayout.count())):
            self.frameLayout.itemAt(i).widget().setParent(None)

    def setIcon(self, icon):
        """Sets the large icon of this tooltip dialogue window

        :param icon:
        """
        icon = icon or self.defaultIcon
        qicon = iconlib.iconColorized(icon, self.iconSize, self.iconColour)
        iconWgt = QtWidgets.QToolButton()
        iconWgt.setIconSize(QtCore.QSize(self.iconSize, self.iconSize))

        iconWgt.setIcon(qicon)
        self.tooltipIcon = iconWgt

    def setTitle(self, title, applyStyle=True):
        """Set the title text and apply our style by replacing text if we need to.

        :param title:
        :param applyStyle:
        """
        if applyStyle:
            title = self.applyStyle(title)
        self.titleLabel.setText(title)

    def keyReleaseEvent(self, event):
        """Close the dialogue on expanded tooltip key release

        :param event:
        """

        if event.key() == self.popupKey:
            self.close()


class GifWidget(QtWidgets.QLabel):
    """
    A QLabel which plays our gif out
    """
    gifEnv = "HIVE_UI_GIFS"

    def __init__(self, gifPath):
        self.MAX_WIDTH = 400

        super(GifWidget, self).__init__("Name")

        path = os.environ[self.gifEnv].split(os.pathsep)[0]
        gifFile = os.path.join(path, gifPath + ".gif")
        self.movie = QtGui.QMovie(gifFile, QtCore.QByteArray(), self)
        self.movie.setCacheMode(QtGui.QMovie.CacheAll)
        self.movie.setSpeed(100)
        self.setMovie(self.movie)
        self.setAlignment(QtCore.Qt.AlignHCenter)
        self.movie.start()


class WidgetsFromTextParser(HTMLParser):
    """
    Parses an string (with html tags) and splits it up into a list of widgets. This is so we
    can inject the GifWidgets into the main layout.

    The documentation here describes how to use HTMLParser quite well:
    https://docs.python.org/2/library/htmlparser.html

    Pretty much we feed the string into HTMLParser, and we reconstruct it with self.constructed.
    Once it reaches a <zoo> tag, it creates a new widget for each zoo tag.
    """

    def __init__(self, text):
        HTMLParser.__init__(self)
        self._widgets = []

        self.constructed = ""
        self.font = QtGui.QFont("sans")

        self.feed(text)

    def feed(self, data):
        """Goes through the string and throws out handle events as it comes across
        tags.

        :param data:
        """
        HTMLParser.feed(self, data)
        self.addLabelFromConstructed()

    def widgets(self):
        """Return the widgets generated from the string that is fed in.

        :return: list
        """
        return self._widgets

    def handle_starttag(self, tag, attrs):
        """Every time it finds a start tag eg. <a>, <img>, <span> this function is run
        along with the data.

        Here we add our own tags eg. <zoo gif="example" />.
        Create a label from all the previous text, and create a new GifWidget for this gif

        :param tag:
        :param attrs:
        """
        startTag = self.get_starttag_text()
        self.constructed += startTag

        # if we find our own tag eg <zoo gif="example" />
        if tag == "zoo":
            if attrs[0][0] == "gif":
                rem = len(startTag)
                self.constructed = self.constructed[:-rem]  # Remove the last tag
                self.addLabelFromConstructed()
                self.addGifWidget(attrs[0][1])

    def handle_endtag(self, tag):
        """Close tags
        eg. </span> </b> </div>

        :param tag:
        :type tag: str
        """

        if tag == 'zoo':
            return

        self.constructed += "</{}>".format(tag)

    def handle_data(self, data):
        """Data in between tags
        eg. <span>data in between tags</span>

        :param data:
        """
        self.constructed += data

    def addGifWidget(self, file):
        """Add a GifWidget when gif tag is found

        :param file:
        """
        gifWidget = GifWidget(file)
        self._widgets.append(gifWidget)

    def addLabelFromConstructed(self):
        """Add a label with the current text in constructed.
        """
        label = QtWidgets.QLabel(self.constructed)
        label.setOpenExternalLinks(True)
        label.setWordWrap(True)
        label.setFont(self.font)
        self.constructed = ""

        self._widgets.append(label)


""" ======================================================================

    Functions to install the expanded tooltip into a widget

    Works in conjunction with artistui.keyPressEvent() to display a popup 

    ======================================================================
"""


def installTooltips(widget, tooltipDict):
    """ Installs the expanded tooltip onto a widget.
    Works in conjunction with artistui.keyPressEvent() to display a popup (zoo.apps.hiveartistui.views.expandedtooltip.ExpandedTooltipPopup)

    :param widget:
    :type widget: QtWidgets.QWidget
    :param tooltipDict:
    :type tooltipDict:
    """
    tooltip = tooltipDict['tooltip']
    widget.setToolTip(tooltip)
    widget._expandedTooltips_ = ExpandedTooltips(tooltipDict)


def hasExpandedTooltips(widget):
    """Returns whether the widget has the injected _expandedTooltips_ object present in the widget

    :param widget:
    """
    return hasattr(widget, "_expandedTooltips_") and widget._expandedTooltips_.text != ""


def copyExpandedTooltips(source, dest):
    """Copy the _expandedTooltips_ from source widget to destination

    :param source:
    :param dest:
    """
    dest._expandedTooltips_ = source._expandedTooltips_


class ExpandedTooltips(QtCore.QObject):
    """
    Acts as a Data storage for the Expanded tooltips.

    Works in conjunction with artistui.keyPressEvent() to display a popup

    """
    icon = ""
    text = ""
    title = ""

    def __init__(self, dict):
        """Distribute the data into the strings

        :param dict:
        """
        try:
            self.title = dict['title']
        except KeyError:
            pass

        try:
            self.text = dict['expanded']
        except KeyError:
            pass

        try:
            self.icon = dict['icon']
        except KeyError:
            pass