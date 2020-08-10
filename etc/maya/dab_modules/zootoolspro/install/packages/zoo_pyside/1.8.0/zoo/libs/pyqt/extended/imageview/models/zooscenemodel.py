from Qt import QtGui, QtCore, QtWidgets

from zoo.libs.utils import path
from zoo.libs.pyqt.extended.imageview.models import filemodel
from zoo.libs.zooscene import zooscenefiles
from zoo.libs.zooscene.constants import ZOOSCENE_EXT


class ZooSceneViewerModel(filemodel.FileViewModel):
    # Emit signals
    parentClosed = QtCore.Signal(bool)
    doubleClicked = QtCore.Signal(str)
    selectionChanged = QtCore.Signal(str)

    def __init__(self, view, directory="", chunkCount=20, uniformIcons=False):
        """Loads .zooscene model data from a directory for a ThumbnailView widget

        Pulls thumbnails which are in dependency directories and tooltips are generated from the file.zooInfo files.

        Also see the inherited class FileViewModel() in zoo_core_pro for more functionality and documentation.:
            zoo.libs.pyqt.extended.imageview.models.filemodel.FileViewModel()

        This class can be overridden further for custom image loading in subdirectories such as Skydomes or Controls \
        which use the .zooScene tag and thumbnail information.

        :param view: The viewer to assign this model data?
        :type view: qtWidget?
        :param directory: The directory full path where the .zooScenes live
        :type directory: str
        :param chunkCount: The number of images to load at a time into the ThumbnailView widget
        :type chunkCount: int
        """
        super(ZooSceneViewerModel, self).__init__(view, directory=directory, chunkCount=chunkCount,
                                                  uniformIcons=uniformIcons)

    def _thumbnails(self):
        """Returns a list of thumbnail image paths, from the sub directory "fileName_fileDependencies" of each file:

            ["C:/aPath/scene01_fileDependencies/thumbnail.jpg", "C:/aPath/scene02_fileDependencies/thumbnail.jpg"]

        Overrides base class

        :return currentFilesList:
        :rtype list(str):
        :return thumbNameList:
        :rtype list(str):
        """
        return zooscenefiles.thumbnails(self.directory, self.fileNameList)

    def fileList(self):
        """Generates the file list:

            ["scene01.zooScene", "scene02.zooScene"]

        Overrides base class
        """
        self.fileNameList = path.filesByExtension(self.directory, [ZOOSCENE_EXT])




