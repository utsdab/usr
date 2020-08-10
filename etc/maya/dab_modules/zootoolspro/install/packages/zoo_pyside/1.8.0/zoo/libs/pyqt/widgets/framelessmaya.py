from Qt import QtWidgets, QtCore
from zoo.libs.maya.qt import mayaui

from zoo.libs.pyqt.widgets.frameless import FramelessWindow


class FramelessWindowMaya(FramelessWindow):

    def __init__(self, *args, **kwargs):
        super(FramelessWindowMaya, self).__init__(*args, **kwargs)
        # Magic property for the frameless window to parent to the maya window for macs
        self.setProperty("saveWindowPref", True)

    def bootstrapWidget(self):
        """ Handle of the bootstrap widget which is holding this window.
        May remove this since this is not maya-independent.

        :return:
        """
        bootstrapWidget = self.property("bootstrapWidget")

        if self.currentDocked is None and bootstrapWidget is not None:
            self.currentDocked = not bootstrapWidget.isFloating()

        return bootstrapWidget

    def isDocked(self):
        """Returns if the window is currently docked

        :return:
        """
        bootstrap = self.bootstrapWidget()

        if bootstrap is None:
            return False
        else:
            return not bootstrap.isFloating()

    def close(self):
        try:
            super(FramelessWindowMaya, self).close()
        except RuntimeError:
            pass

        if self.isDocked():
            self.deleteBootstrap()

    def deleteBootstrap(self):
        """ Delete the bootstrap Widget

        :return:
        :rtype:
        """
        bootstrap = self.bootstrapWidget()

        if bootstrap is not None:
            self.setProperty("bootstrapWidget", None) # avoid recursion by setting to none
            bootstrap.close()


