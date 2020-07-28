from Qt import QtCore

from zoo.preferences.core import preference
from zoo.libs.utils import path

from zoo.libs.zooscene import zooscenefiles
from zoo.libs.pyqt.extended.imageview.models import filemodel

from zoo.apps.light_suite import lightconstants as lc


class HdrSkydomeViewerModel(filemodel.FileViewModel):
    # Emit signals
    parentClosed = QtCore.Signal(bool)
    doubleClicked = QtCore.Signal(str)
    selectionChanged = QtCore.Signal(str)

    def __init__(self, view, directory="", chunkCount=20, uniformIcons=False):
        """Loads skydome model data from a directory for a ThumbnailView widget
        Pulls thumbnails which are in dependency directories and tooltips are generated from the zooInfo files.

        Uses filemodel.FileViewModel as a base class and overrides skydome related code, see more documentation at:
            zoo.libs.pyqt.extended.imageview.models.filemodel.FileViewModel()

        :param view: The viewer to assign this model data?
        :type view: qtWidget?
        :param directory: The directory full path where the .zooScenes live
        :type directory: str
        :param chunkCount: The number of images to load at a time into the ThumbnailView widget
        :type chunkCount: int
        """
        super(HdrSkydomeViewerModel, self).__init__(view, directory=directory, chunkCount=chunkCount,
                                                    uniformIcons=uniformIcons, extVis=False)

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

            ["image01.hdr", "image02.tif"]

        Overrides base class
        """
        self.fileNameList = path.filesByExtension(self.directory, self._hdrExtensions())
        if self.fileNameList:  # hardcode exception for braverabbit skydome and move it last, looks better
            if self.fileNameList[0].startswith("braverabbit_"):
                self.fileNameList.append(self.fileNameList.pop(0))

    def _hdrExtensions(self):
        """returns a list of HDR extensions dependant on the zoo preferences checked states
        Return Example:
            ["exr", "hdr", "tif", "tiff"]
        """
        hdrExtList = list()
        # Light Suite Pref Object self.lsPrefsObj stores and saves all the .prefs json data
        self.prefsData = preference.findSetting(lc.RELATIVE_PREFS_FILE, None)
        if self.prefsData["settings"][lc.PREFS_KEY_EXR]:  # exrState
            hdrExtList.append("exr")
        if self.prefsData["settings"][lc.PREFS_KEY_HDR]:  # hdrState
            hdrExtList.append("hdr")
            hdrExtList.append("hdri")
        if self.prefsData["settings"][lc.PREFS_KEY_TIF]:  # tifState
            hdrExtList.append("tif")
            hdrExtList.append("tiff")
        if self.prefsData["settings"][lc.PREFS_KEY_TEX]:  # texState
            hdrExtList.append("tex")
        if self.prefsData["settings"][lc.PREFS_KEY_TX]:  # txState
            hdrExtList.append("tx")
        return hdrExtList
