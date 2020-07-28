from Qt import QtCore

from zoo.libs.utils import path

from zoo.libs.zooscene import zooscenefiles
from zoo.libs.pyqt.extended.imageview.models import filemodel

from zoo.apps.controls_joints.controlsjointsconstants import CONTROL_SHAPE_EXTENSION

# List is backwards
CONTROL_PRIORITY_LIST = ["slider_square_handle",
                         "slider_square",
                         "circle_half_thick",
                         "circle_halved_thick",
                         "bean_4_all",
                         "locator",
                         "arrow_1_thinbev",
                         "arrow_2way_thinbev",
                         "arrow_4way_circle3",
                         "arrow_4way_roundFlat",
                         "pin_tri_fat",
                         "pick_tri_fat",
                         "pear",
                         "pill",
                         "triangle_round",
                         "square_rounded_front",
                         "square_bev",
                         "octagon_bevel",
                         "hex",
                         "circle",
                         "cube",
                         "sphere"]


class ControlCurvesViewerModel(filemodel.FileViewModel):
    # Emit signals
    parentClosed = QtCore.Signal(bool)  # should be in the base class can be removed?
    doubleClicked = QtCore.Signal(str)
    selectionChanged = QtCore.Signal(str)

    def __init__(self, view, directory="", chunkCount=20, uniformIcons=False):
        """Loads control shape model data from a directory for a ThumbnailView widget
        Pulls thumbnails which are in dependency directories and tooltips are generated from the zooInfo files.

        Uses filemodel.FileViewModel as a base class and overrides controlshape related code, see more documentation at:
            zoo.libs.pyqt.extended.imageview.models.filemodel.FileViewModel()

        :param view: The viewer to assign this model data?
        :type view: qtWidget?
        :param directory: The directory full path where the .zooScenes live
        :type directory: str
        :param chunkCount: The number of images to load at a time into the ThumbnailView widget
        :type chunkCount: int
        """
        super(ControlCurvesViewerModel, self).__init__(view, directory=directory, chunkCount=chunkCount,
                                                       uniformIcons=uniformIcons)

    def _thumbnails(self):
        """Returns a list of thumbnail image paths, from the sub directory "fileName_fileDependencies" of each file:

            ["C:/aPath/image01_fileDependencies/thumbnail.jpg", "C:/aPath/image02_fileDependencies/thumbnail.jpg"]

        Overrides base class

        :return currentFilesList:
        :rtype list(str):
        :return thumbNameList:
        :rtype list(str):
        """
        return zooscenefiles.thumbnails(self.directory, self.fileNameList)

    def fileList(self):
        """Generates the file list:

            ["control01.shape", "control02.shape"]

        Overrides base class
        """
        # CONTROL_SHAPE_EXTENSION is "shapes"
        self.fileNameList = path.filesByExtension(self.directory, [CONTROL_SHAPE_EXTENSION])
        if self.fileNameList:  # Hard code top controls from the CONTROL_PRIORITY_LIST list
            for ctrl in CONTROL_PRIORITY_LIST:
                self.moveToListFront(ctrl)

    def moveToListFront(self, text):
        """Moves a control name to the top of the list, if it exists in the list with .shape extension
        Image will be at the top of the thumbnail browser when opened

        :param text: control name minus the extension eg. "sphere"
        :type text: str
        """
        text = ".".join([text, CONTROL_SHAPE_EXTENSION])
        if text in self.fileNameList:
            index = self.fileNameList.index(text)
            self.fileNameList.insert(0, self.fileNameList.pop(index))
