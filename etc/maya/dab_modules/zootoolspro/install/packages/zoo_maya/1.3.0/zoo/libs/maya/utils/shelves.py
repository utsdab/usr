from maya import cmds, mel
from zoo.libs.utils import zlogging
from zoo.libs.maya.utils import env

logger = zlogging.getLogger(__name__)


class Shelf(object):
    """A simple class to build shelves in maya. Since the build method is empty,
    it should be extended by the derived class to build the necessary shelf elements.
    By default it creates an empty shelf called "customShelf"."""

    def __init__(self, name="Animation"):
        self.name = name
        self.labelBackground = (0, 0, 0, 0)
        self.labelColour = (.9, .9, .9)

    def setAsActive(self):
        cmds.tabLayout(primaryshelfLayout(), edit=True, selectTab=self.name)

    def shortName(self):
        return self.name.split("|")[-1]

    def createShelf(self):
        assert not cmds.shelfLayout(self.name, exists=True), "Shelf by the name {} already exists".format(self.name)
        logger.debug("Creating shelf: {}".format(self.name))
        self.name = cmds.shelfLayout(self.name, parent="ShelfLayout")

    def addButton(self, label, tooltip=None, icon="commandButton.png", command=None, doubleCommand=None, Type="python",
                  style="iconOnly"):
        """Adds a shelf button with the specified label, command, double click command and image."""

        cmds.setParent(self.name)
        command = command or ""
        doubleCommand = doubleCommand or ""
        kwargs = dict(width=34, height=34, image=icon or "", label=label, command=command,
                      doubleClickCommand=doubleCommand, annotation=tooltip or "",
                      overlayLabelBackColor=self.labelBackground,
                      style=style,
                      overlayLabelColor=self.labelColour,
                      sourceType=Type,
                      scaleIcon=True)

        if env.mayaVersion() > 2018:
            kwargs["statusBarMessage"] = tooltip
        if style is not "iconOnly":
            kwargs["imageOverlayLabel"] = label
        logger.debug("Adding Shelf button: {}".format(label), extra={"command": kwargs})
        return cmds.shelfButton(**kwargs)

    @staticmethod
    def addMenuItem(parent, label, command="", icon=""):
        """Adds a menu item with the specified label, command, and image."""

        return cmds.menuItem(parent=parent, label=label, command=command, image=icon or "")

    @staticmethod
    def addSubMenu(parent, label, icon=None):
        """Adds a sub menu item with the specified label and icon to the specified parent popup menu."""
        return cmds.menuItem(parent=parent, label=label, icon=icon or "", subMenu=1)

    @staticmethod
    def addMenuSeparator(parent, **kwargs):
        """Adds a separator(line) on the parent menu.

        This uses the cmds.menuItem to create the separator

        :param parent: The full UI path to the parent menu
        :type parent: str
        """
        arguments = dict(parent=parent,
                         divider=True)
        arguments.update(kwargs)
        cmds.menuItem(**arguments)

    def addSeparator(self):
        """ Adds a maya shelf separator to the parent shelf

        :return: The full path to the separator
        :rtype: str
        """
        cmds.separator(parent=self.name, manage=True, visible=True,
                       horizontal=True, style="shelf", enableBackground=False, preventOverride=False)

    def _cleanOldShelf(self):
        """Checks if the shelf exists and empties it if it does or creates it if it does not."""
        cleanOldShelf(self.name)


def cleanOldShelf(shelfName):
    """Checks if the shelf exists and empties it if it does"""
    if cmds.shelfLayout(shelfName, exists=1):
        if cmds.shelfLayout(shelfName, query=1, childArray=1):
            for each in cmds.shelfLayout(shelfName, query=1, childArray=1):
                cmds.deleteUI(each)
        logger.debug("Removing shelf: {}".format(shelfName))
        cmds.deleteUI(shelfName)


def primaryshelfLayout():
    """Returns the main maya shelf layer path.

    Have to mel globals here, the hell?

    :return: The shelf layout path
    :rtype: str
    """
    return mel.eval("$_tempVar = $gShelfTopLevel")


def activeShelf():
    """Returns the currently active maya shelf as a :class:`Shelf` object.

    :return:
    :rtype: :class:`Shelf`
    """
    return Shelf(cmds.tabLayout(primaryshelfLayout(), query=True, selectTab=True))
