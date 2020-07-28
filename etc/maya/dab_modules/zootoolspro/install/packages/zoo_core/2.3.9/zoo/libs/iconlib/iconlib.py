import os

from Qt import QtGui, QtCore, QtWidgets
from zoo.libs.utils import env, classtypes
from zoo.libs.pyqt import utils
from zoo.libs.utils import zlogging
from zoovendor.six import string_types
from zoovendor import six


logger = zlogging.getLogger(__name__)


@six.add_metaclass(classtypes.Singleton)
class Icon(object):
    """This class acts as a uniform interface to manipulate, create, retrieve Qt icons from the zoo library.
    """

    iconCollection = {}
    iconPaths = []

    def __init__(self):
        Icon.reload()

    @classmethod
    def reload(cls):
        cls.iconCollection = {}

        # find and store all the found icons with the base zoo paths
        cls.iconPaths = os.environ.get("ZOO_ICON_PATHS", "").split(os.pathsep)
        for iconPath in cls.iconPaths:
            if not iconPath or not os.path.exists(iconPath):
                continue
            for root, dirs, files in os.walk(iconPath):
                for f in files:
                    if not f.endswith(".png"):
                        continue
                    fname = f.split(os.extsep)[0]
                    nameSplit = fname.split("_")
                    if len(nameSplit) < 1:
                        continue
                    name = "_".join(nameSplit[:-1])
                    size = int(nameSplit[-1])
                    if name in cls.iconCollection:
                        sizes = cls.iconCollection[name]["sizes"]
                        if size in sizes:
                            continue
                        sizes[size] = {"path": os.path.join(root, f)}

                    else:
                        cls.iconCollection[name] = {"sizes": {size: {"path": os.path.join(root, f)}},
                                                    "name": name}

    @classmethod
    def iconPath(cls, iconName):
        """ Convenience function to return the paths to icons

        :param iconName:
        :type iconName:
        :return:
        :rtype:
        """
        return cls.iconCollection.get(iconName)

    @classmethod
    def icon(cls, iconName, size=16):
        """Returns a QtGui.QIcon instance intialized to the icon path for the icon name if the icon name is found within
        the cache

        :param iconName: iconName_size or iconName, then it will resize the largest icon found
        :type iconName: str
        :param size: int, the size of the icon, the size will be used for both the width and height.
                     setting size=-1 will return the largest icon as well
        :type size: int
        :return QIcon: QtGui.Qicon
        :rtype QIcon: object
        """
        # size = utils.dpiScale(size)  # TODO: too many references to add the dpi scale here?
        if env.isMayapy():
            return
        iconData = cls.iconDataForName(iconName, size)
        newIcon = QtGui.QIcon(iconData.get("path", ""))
        if size != -1:
            newIcon = cls.resizeIcon(newIcon, QtCore.QSize(size, size))
        return newIcon

    @classmethod
    def resizeIcon(cls, icon, size):
        """
        Resizes the icon. Defaults to smooth bilinear scaling and keep aspect ratio.
        :param icon: Icon to resize
        :param size: New size to scale to
        :type size: QtCore.QSize
        :return:
        """
        if len(icon.availableSizes()) == 0:
            return

        origSize = icon.availableSizes()[0]
        pixmap = icon.pixmap(origSize)
        pixmap = pixmap.scaled(size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

        return QtGui.QIcon(pixmap)

    @classmethod
    def iconDataForName(cls, iconName, size=16):
        """
        Sets up the icon data that is used by qt based on the iconName
        :param iconName:
        :param size:
        :return:
        """
        if "_" in iconName:
            splitter = iconName.split("_")
            if splitter[-1].isdigit():
                iconName = "_".join(splitter[:-1])
                # user requested the size in the name
                size = splitter[-1]
        else:
            size = str(size)
        if iconName not in cls.iconCollection:
            return {}

        for name, data in iter(cls.iconCollection.items()):
            if name != iconName:
                continue
            sizes = data["sizes"]

            if size not in sizes:
                # in py3 we need to cast to list before indexing
                size = list(sizes.keys())[-1]
                iconData = sizes[size]
            else:
                iconData = data["sizes"][size]
            return iconData
        return {}

    @classmethod
    def iconPathForName(cls, iconName, size=16):
        return cls.iconDataForName(iconName, size).get("path", "")

    @classmethod
    def iconColorized(cls, iconName, size=16, color=(255, 255, 255), overlayName=None, overlayColor=(255,255,255)):
        """ Colorizes the icon from the library expects the default icon
        to be white for tinting.

        :param iconName: the icon name from the library
        :type iconName: str
        :param size: the uniform icon size
        :type size: int
        :param color: 3 tuple for the icon color
        :type color: tuple(int)
        :return: the colorized icon
        :param overlayName: The name of the icon that will be overlayed on top of the original icon
        :param overlayColor: The colour of the overlay
        :rtype: QtGui.QIcon
        """
        size = utils.dpiScale(size)
        iconLargest = cls.icon(iconName, -1)

        if not iconLargest:
            return iconLargest

        origSize = iconLargest.availableSizes()[0]
        pixmap = cls.colorPixmap(iconLargest.pixmap(origSize), color)
        # Add overlay icon
        if overlayName is not None:
            overlayIcon = cls.icon(overlayName, -1)
            overlayPixmap = overlayIcon.pixmap(origSize)
            cls.addOverlay(pixmap, overlayPixmap, overlayColor)

        pixmap = pixmap.scaled(QtCore.QSize(size, size), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

        return QtGui.QIcon(pixmap)

    @classmethod
    def iconColorizedLayered(cls, iconNames, size=16, colors=None, iconScaling=None, tintColor=None,
                             tintComposition=QtGui.QPainter.CompositionMode_Plus, grayscale=None):
        """ Layers multiple icons with various colours into one qicon. Maybe can replace icon colorized

        :param iconNames: the icon name from the library. Allow string or list for convenience
        :type iconNames: list or basestring
        :param size: the uniform icon size
        :type size: int
        :param colors: 3 tuple for the icon color
        :type colors: list of tuple
        :return: the colorized icon
        :param overlayName: The name of the icon that will be overlayed on top of the original icon
        :param overlayColor: The colour of the overlay
        :rtype: QtGui.QIcon
        """
        defaultSize = 1
        size = utils.dpiScale(size)
        if isinstance(iconNames, string_types):
            iconNames = [iconNames]
        elif isinstance(iconNames, list):
            iconNames = list(iconNames)  # copy

        if isinstance(iconScaling, list):
            iconScaling = list(iconScaling)  # copy

        if not isinstance(colors, list):
            colors = [colors]
        else:
            colors = list(colors)  # copy

        if iconNames is []:
            logger.warning("iconNames cannot be none for iconColorizedLayered")
            p = QtGui.QPixmap(16, 16)
            p.fill(QtGui.QColor(255, 255, 255))

        # Fill out the colours to match the length of iconNames
        if colors is None or (len(iconNames) > len(colors)):
            colors = colors or []
            colors += [None] * (len(iconNames) - len(colors))

        # Fill out the sizes to match the length of iconNames
        if iconScaling is None or len(iconNames) > len(iconScaling):
            iconScaling = iconScaling or []
            iconScaling += [defaultSize] * (len(iconNames) - len(iconScaling))

        iconLargest = cls.icon(iconNames.pop(0), -1)

        if not iconLargest:
            return iconLargest

        origSize = iconLargest.availableSizes()[0]
        col = colors.pop(0)
        scale = iconScaling.pop(0)
        if col is not None:
            pixmap = cls.colorPixmap(iconLargest.pixmap(origSize*scale), col)
        else:
            pixmap = iconLargest.pixmap(origSize*scale)

        # Layer the additional icons
        for i, name in enumerate(iconNames):
            if name is None:
                continue
            overlayIcon = cls.icon(name, -1)
            overlayPixmap = overlayIcon.pixmap(origSize * iconScaling[i])
            cls.addOverlay(pixmap, overlayPixmap, colors[i])

        # Tint
        if tintColor is not None:
            cls.tint(pixmap, tintColor, compositionMode=tintComposition)

        pixmap = pixmap.scaled(QtCore.QSize(size, size), QtCore.Qt.KeepAspectRatio,
                               QtCore.Qt.SmoothTransformation)  # type: QtGui.QPixmap

        icon = QtGui.QIcon(pixmap)
        if grayscale:
            pixmap = cls.grayscale(pixmap)

            # todo: rough code to darken icon for alpha, this should removed and done in tint
            icon = QtGui.QIcon(pixmap)
            icon.addPixmap(icon.pixmap(size, QtGui.QIcon.Disabled))

        return icon

    @classmethod
    def grayscaleIcon(cls, iconName, size):
        """ Returns a grayscale version of a given icon. Returns the original icon
        if it cannot be converted.
        :param iconName: The icon name from the library
        :type iconName: str
        :param size: the size of the icon to retrieve
        :type size: int
        :rtype: QtGui.QIcon
        """
        icon = cls.icon(iconName, size)
        if not icon:
            return icon  # will return an empty QIcon
        # Rebuild all sizes of the icon as grayscale
        for size in icon.availableSizes():
            icon.addPixmap(icon.pixmap(size, QtGui.QIcon.Disabled))
        return icon

    @classmethod
    def colorPixmap(cls, pixmap, color):
        """
        Colorize the pixmap with a new color based on its alpha map
        :param pixmap: Pixmap
        :type pixmap: QtGui.QPixmap
        :param color: new color in tuple format (255,255,255)
        :return:
        """
        color = QtGui.QColor(*color)
        mask = pixmap.mask()
        pixmap.fill(color)
        pixmap.setMask(mask)

        return pixmap

    @classmethod
    def addOverlay(cls, pixmap, overlayPixmap, color, align=QtCore.Qt.AlignCenter):
        """ Overlays one pixmap over the other

        :param align: Aligns the icon based
        :param pixmap: The source pixmap
        :type pixmap: QtGui.QPixmap
        :param overlayPixmap: the pixmap to overlay on top of the source pixmap
        :type overlayPixmap: QtGui.QPixmap
        :param color: The colour of the overlay pixmap
        :type color: tuple(int,int,int)
        :return:
        """
        # Set the color for the overlay if there is colour
        if color is not None:
            overlayPixmap = cls.colorPixmap(overlayPixmap, color)

        # Paint the overlay pixmap over the original
        painter = QtGui.QPainter(pixmap)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)

        x = y = 0
        if align is QtCore.Qt.AlignCenter:
            x = pixmap.width() / 2 - overlayPixmap.width() / 2
            y = pixmap.height() / 2 - overlayPixmap.height() / 2
        elif align is None:
            x = y = 0  # Write more here if we need different variations of icon alignment

        painter.drawPixmap(x, y, overlayPixmap.width(), overlayPixmap.height(), overlayPixmap)
        painter.end()

    @classmethod
    def tint(cls, pixmap, color=(255, 255, 255, 100), compositionMode=QtGui.QPainter.CompositionMode_Plus):
        """ Composite one pixmap over another

        :param pixmap:
        :param color:
        :param compositionMode:
        :return:
        """
        # Set the color for the overlay

        color = QtGui.QColor(*color)
        overlayPixmap = QtGui.QPixmap(pixmap.width(), pixmap.height())
        overlayPixmap.fill(color)
        overlayPixmap.setMask(pixmap.mask())

        # Paint the overlay pixmap over the original
        painter = QtGui.QPainter(pixmap)
        painter.setCompositionMode(compositionMode)

        painter.drawPixmap(0, 0, overlayPixmap.width(), overlayPixmap.height(), overlayPixmap)
        painter.end()

    @classmethod
    def grayscale(cls, pixmap):
        """

        :param icon:
        :type icon: QtGui.QIcon
        :return:
        """

        # This might be slow! Converts to grayscale format then back. Not sure if this the fastest way or not.
        image = pixmap.toImage()  # type: QtGui.QImage
        alpha = image.alphaChannel()
        gray = image.convertToFormat(QtGui.QImage.Format_Grayscale8)  # type: QtGui.QImage
        image = gray.convertToFormat(QtGui.QImage.Format_ARGB32)  # type: QtGui.QImage
        image.setAlphaChannel(alpha)

        return QtGui.QPixmap(image)





