from Qt import QtCore, QtWidgets

from zoo.libs import iconlib
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import dpiscaling, floatingbutton
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import zlogging


logger = zlogging.getLogger(__name__)


class ResizerWidget(QtWidgets.QFrame, dpiscaling.DPIScaling):
    """ A Layout widget which allows you to flexibly hide widgets.

    """

    LeftToRight = 1
    RightToLeft = -1  # Use negatives to easily get the reverse values
    TopToBottom = 2
    BottomToTop = -2

    Parallel = 1
    Reverse = -1

    Inwards = 0
    Outwards = 1

    LeftPad = utils.dpiScale(12)  # todo: Not sure where the 12 comes from, maybe the frameless window resizers
    RightPad = 1

    def __init__(self, parent=None, layoutDirection=LeftToRight, collapseDirection=Reverse, resizeDirection=Inwards,
                 buttonAlign=QtCore.Qt.AlignVCenter, buttonOffset=None, autoButtonUpdate=True):
        """ A Layout widget which allows you to flexibly hide widgets. When widgets are hidden, it resizes the window

        Features:
            *  Widgets can be laid out In any direction, Left to right, Right to left, Bottom to Top, top to bottom.
            *  Widgets can be collapsed from any direction. Last widget first or first widget first.
            *  Widgets can be external, this is especially useful if you want to keep widgets in their respective
               QSplitters.
            *  Widgets can start hidden, this allows for some flexible behaviour for toggling (eg Hive UI properties
               panel)
            *  Toggle arrow button can be aligned to any target widget, so it will be attached to any widget on resize.
            *  The resizer toggle button's position can be shifted with an offset
            *  Arrow direction is now calculated automatically, don't have to manually set it anymore on toggle.

        The widgets can be hidden and toggled with the ResizerButton which is attached this object.
        Assumes order based on addWidget. Currently you can't change the order.

        ResizerButton is a floating arrow button which position is updated using updateButtonPosition().
        The button can be aligned to a target widget (which is set by setTarget() or as a parameter in addWidget()).
        The button alignment can be set as a __init__() parameter buttonAlign or with setButtonAlign(). it takes
        a horizontal align and a vertical align (eg QtCore.Qt.AlignTop | QtCore.Qt.AlignRight)

        The ResizerButton button's position can be shifted using buttonOffset or with setButtonOffset()

        The button position is automatically updated as set with the parameter "autoButtonUpdate" in __init__() but if
        you want to set this manually for performance purposes you can set this to false. Additional note it only
        updates if the ResizerWidget is resized.

        The widgets layout direction can be set with ResizerWidget.LeftToRight, ResizerWidget.RightToLeft,
        ResizerWidget.TopToBottom, ResizerWidget.BottomToTop. This can be set as a __init__() param "layoutDirection"
        or with setLayoutDirection(). The arrow direction on ResizerButton is set automatically when the widgets are
        toggled based on this.

        The way the widgets collapse on ResizerButton clicked can be set with init() param collapseDirection or
        setCollapseDirection(). It takes ResizerWidget.Parallel or Reverse. Reverse means widgets will hide from the
        last widget first. Parallel means the widget will hide in the order they are added.

            .. code-block:: python

                self.resizerWidget = resizerwidget.ResizerWidget(self,
                                                   layoutDirection=resizerwidget.ResizerWidget.RightToLeft,
                                                   buttonAlign=QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom,
                                                   buttonOffset=QtCore.QPoint(0, -75),
                                                   collapseDirection=resizerwidget.ResizerWidget.Parallel)

                # Adds to the layout widget
                self.resizerWidget.addWidget(self.verticalToolbar)

                # This widget wont be added to ResizerWidget layout, but can still be hidden when toggled.
                self.resizerWidget.addWidget(self.createUi.sidePanel, external=True, target=False)

                # If you want it to be hidden by default on start up to have, set defaultHidden=True
                self.resizerWidget.addWidget(sidePanel, external=True, target=False, defaultHidden=True)


        :param parent:
        :param layoutDirection: Layout direction of widgets
        :type layoutDirection: ResizerWidget.LeftToRight or ResizerWidget.RightToLeft or ResizerWidget.TopToBottom or
                               ResizerWidget.BottomToTop
        :param collapseDirection: The order of the widgets is hidden
        :type collapseDirection: ResizerWidget.Parallel or ResizerWidget.Reverse
        :param resizeDirection:
        :param buttonAlign: Alignment position of the button
        :param buttonOffset: Button offset in QPoint
        :type buttonOffset: QtCore.QPoint
        """
        buttonOffset = buttonOffset or QtCore.QPoint()
        self.mainLayout = None  # type: QtWidgets.QHBoxLayout or QtWidgets.QVBoxLayout
        self.layoutDirection = layoutDirection  # The direction the widgets will be laid out in the layout
        self.collapseDirection = collapseDirection  # collapse the widgets reversed to the layout direction
        self.resizeDirection = resizeDirection  # Resize window inwards
        self.oldSizeHint = None  # type: QtCore.QSize
        self.widgets = []

        self.savedSplitterSize = None
        self.autoButtonUpdate = autoButtonUpdate

        super(ResizerWidget, self).__init__(parent=parent)

        self.resizerBtn = ResizerButton(parent, resizer=self)
        self.resizerBtn.clicked.connect(self.toggleWidget)

        self.setLayoutDirection(layoutDirection)
        self.setButtonAlign(buttonAlign)
        self.setButtonOffset(buttonOffset)

    def setLayoutDirection(self, direction):
        """ Layout Direction of the added widgets

        :param direction: The direction of the widgets
        :type direction: ResizerWidget.LeftToRight or ResizerWidget.RightToLeft or ResizerWidget.TopToBottom or
                         ResizerWidget.BottomToTop
        :return:
        """
        self.layoutDirection = direction

        if direction == ResizerWidget.LeftToRight:
            self.mainLayout = elements.hBoxLayout(self)
            self.resizerBtn.setRoundedEdge(QtCore.Qt.RightEdge)
        elif direction == ResizerWidget.RightToLeft:
            self.mainLayout = elements.hBoxLayout(self)
            self.mainLayout.setDirection(QtWidgets.QBoxLayout.RightToLeft)
            self.resizerBtn.setRoundedEdge(QtCore.Qt.LeftEdge)
        elif direction == ResizerWidget.TopToBottom:
            self.mainLayout = elements.vBoxLayout(self)
            self.resizerBtn.setRoundedEdge(QtCore.Qt.BottomEdge)
        elif direction == ResizerWidget.BottomToTop:
            self.mainLayout = elements.vBoxLayout(self)
            self.mainLayout.setDirection(QtWidgets.QBoxLayout.BottomToTop)
            self.resizerBtn.setRoundedEdge(QtCore.Qt.TopEdge)

        self.setArrowDirectionFromLayout(flip=True)

    def addWidget(self, wgt, target=True, external=False, defaultHidden=False, initialSize=None):
        """ Add a widget to the ResizerWidget layout.

        :param wgt: The widget to add
        :type wgt: QtWidgets.QWidget
        :param target: Set the wgt as a target for the button to attach itself to. True on default
        :type bool: bool
        :param external: If the widget is an external widget or not. This allows for behaviours that may require a
                         widget that is outside of the ResizerWidget (in a separate QSplitter for instance)
        :type external: bool
        :param defaultHidden: If the widget starts off hidden,
        :type defaultHidden: bool
        :param initialSize: Initial size, if none it will use the objects sizeHint

        :return:
        """

        wgt.setProperty("savedSize", None)
        wgt.setProperty("defaultHidden", False)

        if self.mainLayout is None:  # Initialize main layout
            self.setLayoutDirection(ResizerWidget.LeftToRight)

        if not external:
            self.mainLayout.addWidget(wgt)

        if target:
            self.resizerBtn.setTarget(wgt)

        if defaultHidden:
            wgt.setProperty("defaultHidden", True)
            wgt.hide()

        wgt.setProperty("initialSize", initialSize)

        self.widgets.append(wgt)

    def setTarget(self, target):
        """ Set the target widget that the arrow button will attach itself to

        :param target:
        :type target: QtWidgets.QWidget
        :return:
        """
        self.resizerBtn.setTarget(target)
        self.resizerBtn.updatePosition()

    def setButtonAlign(self, align):
        """

        :param align:
        :return:
        """
        self.resizerBtn.setAlignmentPosition(align)
        self.resizerBtn.updatePosition()

    def setButtonOffset(self, offset):
        """ The button offset from the aligned position

        :param offset: The button offset
        :type offset: QtCore.QPoint
        :return:
        """
        self.resizerBtn.setOffsetPos(offset)
        
    def setFixedWidth(self, width):
        return super(ResizerWidget, self).setFixedWidth(utils.dpiScale(width))

    def setCollapseDirection(self, collapseDirection):
        """ Set the collapse direction of how the widgets will be hidden when toggled.

        The way the widgets collapse on ResizerButton clicked can be set with init() param collapseDirection or
        setCollapseDirection(). It takes ResizerWidget.Parallel or Reverse. Reverse means widgets will hide from the last
        widget first. Parallel means the widget will hide in the order they are added.

        :param collapseDirection: Collapse direction
        :type collapseDirection: ResizerWidget.Parallel or ResizerWidget.Reverse
        :return:
        """
        self.collapseDirection = collapseDirection

    def target(self):
        """ The resizer button target. The target is what the button is attached to.

        :return:
        :rtype: QtWidgets.QWidget
        """
        return self.resizerBtn.target

    def setWidgetVisible(self, wgt, visible, resize=True, force=False):
        """ Set the widget visibility. Also set any settings plus resize the window if need be.

        :param wgt: Wgt to resize
        :type wgt: QtWidgets.QWidget
        :param visible: Widget visibility
        :type visible: bool
        :param resize: Resize the window
        :type resize: bool
        :param force: Force visibility set. It will usually just pass through if you try to set the visibility off and
                      it is already invisible. But there are cases where you need it to set the settings or resize.
        :type force: bool
        :return:
        """
        wgeo = wgt.geometry()
        geo = self.window().geometry()
        sizeHint = wgt.sizeHint()
        initial = False

        edgeCollapseDirection = self.layoutDirection

        if not visible and (wgt.isVisible() or force):
            wgt.setProperty("savedSize", QtCore.QSize(wgeo.width(), wgeo.height()))
            wgt.hide()

            if resize:
                if edgeCollapseDirection == ResizerWidget.LeftToRight:

                    geo.setLeft(geo.left() + wgt.property("savedSize").width() + self.LeftPad)
                elif edgeCollapseDirection == ResizerWidget.RightToLeft:
                    geo.setRight(geo.right() - wgt.property("savedSize").width() - self.RightPad)
                elif edgeCollapseDirection == ResizerWidget.BottomToTop:
                    geo.setHeight(geo.height() - wgt.property("savedSize").height())
        elif visible and (not wgt.isVisible() or force):
            wgt.show()
            # New default size
            if wgt.property("savedSize") is None:
                wgt.setProperty("savedSize", wgt.property("initialSize") or sizeHint)
                initial = True

            if edgeCollapseDirection == ResizerWidget.LeftToRight:
                geo.setLeft(geo.left() - wgt.property("savedSize").width() - self.LeftPad)
            elif edgeCollapseDirection == ResizerWidget.RightToLeft:
                right = geo.right() + wgt.property("savedSize").width() + self.RightPad
                geo.setRight(right)
            elif edgeCollapseDirection == ResizerWidget.BottomToTop:
                geo.setHeight(geo.height() + wgt.property("savedSize").height())

        if resize:
            setWgt = wgt if initial else None
            QtCore.QTimer.singleShot(0, lambda: self.setWindowGeometry(geo, setWgt))

    def toggleWidget(self, widget=None):
        """ Toggles the widget and resizes the window


        :param widgets: List of widgets to toggle
        :param edge: Hide the width or height. Has to be "WIDTH" or "HEIGHT"

        :return:
        """
        self.window().setUpdatesEnabled(False)
        hide = False

        if self.collapseDirection == ResizerWidget.Reverse:
            widgets = self.widgets
        else:
            widgets = list(reversed(self.widgets))

        if widget is None:
            for w in widgets:
                if w.isVisible():
                    widget = w
                    break

        if widget is not None:
            self.setWidgetVisible(widget, False)
            hide = True

        # If we didn't hide anything then show all the widgets instead
        if not hide:
            self.showAllWidgets()

        # Set the arrow direction. If nothing got hidden, flip the arrows instead
        self.setArrowDirectionFromLayout(flip=not hide)

    def showAllWidgets(self, ignoreDefaultHidden=False):
        """ Show all the widgets in the ResizerWidget

        :param ignoreDefaultHidden: Ignore default hidden widgets and show everything
        :type ignoreDefaultHidden: bool
        :return:
        """
        edgeCollapseDirection = self.layoutDirection
        geo = self.window().geometry()
        for w in self.widgets:
            if ignoreDefaultHidden or not w.property("defaultHidden"):
                w.show()

                if edgeCollapseDirection == ResizerWidget.LeftToRight:
                    geo.setLeft(geo.left() - w.property("savedSize").width() - self.LeftPad)
                elif edgeCollapseDirection == ResizerWidget.RightToLeft:
                    right = geo.right() + w.property("savedSize").width() + self.RightPad
                    geo.setRight(right)
                elif edgeCollapseDirection == ResizerWidget.BottomToTop:
                    geo.setHeight(geo.height() + w.property("savedSize").height())

        QtCore.QTimer.singleShot(0, lambda: self.setWindowGeometry(geo))

    def setArrowDirectionFromLayout(self, flip=False):
        """ Set Arrow direction based on layout direction and if the window opens outwards or inwards

        :return:
        """

        flip = 1 if not flip else -1  # Flip values if flip is True

        if self.layoutDirection == ResizerWidget.LeftToRight * flip:
            self.resizerBtn.setArrowDirection(QtCore.Qt.LeftArrow)
        elif self.layoutDirection == ResizerWidget.RightToLeft * flip:
            self.resizerBtn.setArrowDirection(QtCore.Qt.RightArrow)
        elif self.layoutDirection == ResizerWidget.TopToBottom * flip:
            self.resizerBtn.setArrowDirection(QtCore.Qt.DownArrow)
        elif self.layoutDirection == ResizerWidget.BottomToTop * flip:
            self.resizerBtn.setArrowDirection(QtCore.Qt.UpArrow)

    def edgeToCollapse(self):
        """ Get the edge to collapse based on the collapseDirection and the layout direction

        todo: maybe we should have a function for each condition? def isLeftToRightLayout(self): *

        :return:
        """
        if self.collapseDirection == ResizerWidget.Reverse and self.layoutDirection == ResizerWidget.LeftToRight or \
                self.collapseDirection == ResizerWidget.Parallel and self.layoutDirection == ResizerWidget.RightToLeft:
            return ResizerWidget.LeftToRight
        elif self.collapseDirection == ResizerWidget.Reverse and self.layoutDirection == ResizerWidget.RightToLeft or \
                self.collapseDirection == ResizerWidget.Parallel and self.layoutDirection == ResizerWidget.LeftToRight:
            return ResizerWidget.RightToLeft
        elif self.collapseDirection == ResizerWidget.Reverse and self.layoutDirection == ResizerWidget.BottomToTop or \
                self.collapseDirection == ResizerWidget.Parallel and self.layoutDirection == ResizerWidget.TopToBottom:
            return ResizerWidget.BottomToTop
        else:
            return ResizerWidget.TopToBottom

    def widgetsHidden(self):
        """ Return true if ALL widgets are hidden, false otherwise

        :return:
        """

        return not any([w.isVisible() for w in self.widgets])

    def setWindowGeometry(self, geo, wgt=None):
        """ Set the window Geometry

        Plus any other resizes that we need to do after

        :param geo: New window geo
        :type geo:
        :param wgt: handle to the widget that might need updating
        :param initial:
        :return:
        """

        splitter = None
        # Prep work for wgt
        if wgt is not None and isinstance(wgt.parent(), QtWidgets.QSplitter):

            splitter = wgt.parent()
            splitterPos = []
            for h in range(0, splitter.count()):
                splitterPos.append(splitter.handle(h).mapToParent(QtCore.QPoint(0,0)).x())

        # Has an issue with splitter parents, if there's no widgets showing, it will show an empty widget
        isSplitter = isinstance(self.parent(), QtWidgets.QSplitter)
        if isSplitter:
            # all Widgets in layout hidden
            if self.widgetsHidden():
                s = self.parent().sizes()  # parent sizes
                index = self.parent().indexOf(self)

                self.savedSplitterSize = list(s)
                s[index] = 0  # set size to zero
                self.parent().setSizes(s)
                self.oldSizeHint = self.parent().sizeHint()
            else:
                index = self.parent().indexOf(self)
                s = self.parent().sizes()

                s[index] = self.savedSplitterSize[index]*0.9
                self.parent().setSizes(s)

        self.window().setUpdatesEnabled(True)
        self.window().setGeometry(geo)

        self.resizerBtn.updatePosition()

        # Update splitter widgets for wgt
        if wgt is not None and splitter is not None:
            wgeo = wgt.property("initialSize") or wgt.sizeHint()
            handlePos = splitter.indexOf(wgt)

            if splitter.orientation() == QtCore.Qt.Horizontal:
                pos = splitter.geometry().width() - wgeo.width()
            else:
                pos = splitter.geometry().height() - wgeo.height()

            splitter.moveSplitter(pos, handlePos)

    def restoreSplitterPositions(self, splitter, positions, exclude=-1):
        """ Restore splitter positions based on a list of positions

        :param splitter: Splitter
        :type splitter: QtWidgets.QSplitter
        :param positions:
        :type positions: list of int
        :param exclude: Exclude any indices
        :type exclude: int
        :return:
        """
        for i, p in enumerate(positions):
            if i != exclude:
                splitter.moveSplitter(p, i)

    def updateButtonPosition(self):
        """ Update button position

        :return:
        """
        self.resizerBtn.updatePosition()

    def resizeEvent(self, *args, **kwargs):
        """ Update the ResizerButton position on resize

        :param args:
        :param kwargs:
        :return:
        """
        ret = super(ResizerWidget, self).resizeEvent(*args, **kwargs)

        if self.autoButtonUpdate:
            self.resizerBtn.updatePosition()
        return ret


class ResizerButton(floatingbutton.FloatingButton):

    arrowColor = (0, 0, 0)

    def __init__(self, parent, offset=None, target=None, resizer=None):
        """ Rounded button that resizes the parent window when clicked based on the widgets passed in

        :param parent:
        :param target: Target widget to attach itself to
        :type target: QtWidgets.QWidget
        :param resizer: The ResizerWidget that has connected all its behaviour to
        :type resizer: ResizerWidget
        :param offset: The position of the button when widgets are toggled.
        :type offset: QtCore.QPoint
        :
        """
        self.buttonSize = 24
        self.iconSize = 10
        self.icons = {"left": None,
                      "right": None,
                      "up": None,
                      "down": None}
        self.arrowDirection = QtCore.Qt.DownArrow
        self.roundedDirection = QtCore.Qt.TopEdge
        self.posAlign = QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft

        self.target = target
        self.offsets = None
        self.resizerWidget = resizer

        self.setOffsetPos(offset)

        super(ResizerButton, self).__init__(parent=parent, size=24)

    def setOffsetPos(self, offsets):
        self.offsets = self.pointByDpi(offsets or QtCore.QPoint())

    def setTarget(self, target):
        """ Set target to attach itself to

        :param target: Target widget
        :type target: QtWidgets.QWidget
        :return:
        """
        self.target = target
        self.updatePosition()

    def pointByDpi(self, point):
        """ Scales the QPoint by the current dpi scaling from maya.

        :param point: The QPoint to Scale by the current dpi settings
        :type point: QtCore.QPoint
        :return: The newly scaled QPoint
        :rtype: QtCore.QPoint
        """

        return QtCore.QPoint(utils.dpiScale(point.x()), utils.dpiScale(point.y()))

    def initUi(self):

        super(ResizerButton, self).initUi()
        self.initIcons()

        self.setArrowDirection(QtCore.Qt.DownArrow)

        self.resize(self.buttonSize, self.buttonSize)
        self.setStyle()

    def initIcons(self):
        """ Initialize icons by setting icon size

        :return:
        """
        self.setIconSize(self.iconSize)

    def setAlignmentPosition(self, align):
        """ Sets the positional alignment of the resizer button.

        eg QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop

        :param align: The positional alignment the resizer button in comparison to the parent.
        :return:
        """

        self.posAlign = align

    def setArrowDirection(self, direction):
        """ Set the icon arrow direction

        :param direction: Direction to set the arrow to
        :type direction: QtCore.Qt.LeftArrow | QtCore.Qt.RightArrow | QtCore.Qt.UpArrow | QtCore.Qt.DownArrow
        :return:
        """
        self.arrowDirection = direction

        if self.arrowDirection == QtCore.Qt.LeftArrow:
            self.button.setIcon(self.icons['left'])
        elif self.arrowDirection == QtCore.Qt.UpArrow:
            self.button.setIcon(self.icons['up'])
        elif self.arrowDirection == QtCore.Qt.RightArrow:
            self.button.setIcon(self.icons['right'])
        elif self.arrowDirection == QtCore.Qt.DownArrow:
            self.button.setIcon(self.icons['down'])

    def setIconSize(self, iconSize):
        """ Set Icon size of the arrow

        :param iconSize:
        :return:
        """
        self.iconSize = iconSize

        self.icons['left'] = iconlib.iconColorized("arrowSingleLeft", self.iconSize, color=self.arrowColor)
        self.icons['right'] = iconlib.iconColorized("arrowSingleRight", self.iconSize, color=self.arrowColor)
        self.icons['up'] = iconlib.iconColorized("arrowSingleUp", self.iconSize, color=self.arrowColor)
        self.icons['down'] = iconlib.iconColorized("arrowSingleDown", self.iconSize, color=self.arrowColor)

    def flipArrowDirection(self):
        """ Flip the visual arrow direction

        :return:
        """

        if self.arrowDirection == QtCore.Qt.RightArrow:
            self.setArrowDirection(QtCore.Qt.LeftArrow)
        elif self.arrowDirection == QtCore.Qt.LeftArrow:
            self.setArrowDirection(QtCore.Qt.RightArrow)
        elif self.arrowDirection == QtCore.Qt.UpArrow:
            self.setArrowDirection(QtCore.Qt.DownArrow)
        elif self.arrowDirection == QtCore.Qt.DownArrow:
            self.setArrowDirection(QtCore.Qt.UpArrow)

    def setRoundedEdge(self, edge):
        """ Set edge that will be rounded

        :param edge: QtCore.Qt.LeftEdge, QtCore.Qt.TopEdge, QtCore.Qt.RightEdge,QtCore.Qt.BottomEdge
        :type edge: QtCore.Qt.LeftEdge | QtCore.Qt.TopEdge | QtCore.Qt.RightEdge | QtCore.Qt.BottomEdge
        :return:
        """

        # todo: for some reason the style colour doesnt get set when rounded edge isnt set

        self.roundedDirection = edge

        if edge == QtCore.Qt.LeftEdge:
            self.setAlignment(QtCore.Qt.AlignRight)
        elif edge == QtCore.Qt.TopEdge:
            self.setAlignment(QtCore.Qt.AlignBottom)
        elif edge == QtCore.Qt.RightEdge:
            self.setAlignment(QtCore.Qt.AlignLeft)
        elif edge == QtCore.Qt.BottomEdge:
            self.setAlignment(QtCore.Qt.AlignTop)

        self.setStyle()

    def resize(self, width, height):
        super(ResizerButton, self).resize(utils.dpiScale(width), utils.dpiScale(height))

        if hasattr(self, 'button'):
            self.setStyle()

    def setStyle(self):
        """ Round the edges with Stylesheets

        :return:
        """
        radius = self.buttonSize / 2 - 2

        border = (0, 0, 0, 0)  # topleft, topright, bottomleft, bottomright

        if self.roundedDirection == QtCore.Qt.TopEdge:
            border = (radius, radius, 0, 0)
        elif self.roundedDirection == QtCore.Qt.BottomEdge:
            border = (0, 0, radius, radius)
        elif self.roundedDirection == QtCore.Qt.RightEdge:
            border = (0, radius, radius, 0)
        elif self.roundedDirection == QtCore.Qt.LeftEdge:
            border = (radius, 0, 0, radius)

        style = "border-top-left-radius: {}px; border-top-right-radius: {}px;" \
                "border-bottom-right-radius: {}px; border-bottom-left-radius: {}px;".format(*border)

        self.setStyleSheet(style)

    def updatePosition(self):
        """ Update position of button based on target and alignment

        :return:
        """

        if self.target is None:
            return

        pos = self.target.mapTo(self.window(), QtCore.QPoint(0, 0))

        if self.target.isHidden():
            parentGeo = self.resizerWidget.geometry()
        else:
            parentGeo = self.target.geometry()

        # Horizontals
        if self.posAlign & QtCore.Qt.AlignLeft == QtCore.Qt.AlignLeft:
            pass  # Already left aligned so pass
        elif self.posAlign & QtCore.Qt.AlignHCenter == QtCore.Qt.AlignHCenter:
            pos.setX(pos.x() + parentGeo.width() * 0.5)
        elif self.posAlign & QtCore.Qt.AlignRight == QtCore.Qt.AlignRight:
            pos.setX(pos.x() + parentGeo.width())

        # Verticals
        if self.posAlign & QtCore.Qt.AlignTop == QtCore.Qt.AlignTop:
            pass  # Already top aligned so pass
        elif self.posAlign & QtCore.Qt.AlignVCenter == QtCore.Qt.AlignVCenter:
            pos.setY(pos.y() + parentGeo.height() * 0.5)
        elif self.posAlign & QtCore.Qt.AlignBottom == QtCore.Qt.AlignBottom:
            pos.setY(pos.y() + parentGeo.height())

        # Offset the position
        pos += self.offsets

        self.move(pos.x(), pos.y())
