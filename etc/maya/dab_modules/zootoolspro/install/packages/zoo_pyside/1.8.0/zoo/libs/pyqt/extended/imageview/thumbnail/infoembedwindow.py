from zoo.libs.pyqt.extended.combobox import ComboBoxSearchable
from zoo.libs.pyqt.extended.embeddedwindow import EmbeddedWindow
from zoo.libs.pyqt.extended.imageview.models import filemodel
from zoo.libs.pyqt.extended.lineedit import LineEdit
from zoo.libs.pyqt.widgets.buttons import styledButton
from zoo.libs.pyqt.widgets.label import Label
from zoo.libs.pyqt.widgets.layouts import hBoxLayout, GridLayout, vBoxLayout
from zoo.libs.pyqt.widgets.textedit import TextEdit
from zoo.libs.utils import path
from zoo.libs.zooscene import zooscenefiles
import maya.api.OpenMaya as om2

from Qt import QtWidgets, QtCore, QtGui
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.extended.imageview import items

from zoo.libs.zooscene.constants import ASSETTYPES


class ExtensionLabel(Label):
    def setText(self, text):
        """ Sets the label width depending on text
        todo: maybe put this in label or in pyqt module

        :param text:
        :type text:
        :return:
        :rtype:
        """
        painter = QtGui.QPainter(self)
        fm = painter.fontMetrics()
        self.setFixedWidth(fm.width(text))
        super(ExtensionLabel, self).setText(text)


class InfoEmbedWindow(EmbeddedWindow):

    def __init__(self, parent=None, margins=(0, 0, 0, 0),
                 defaultVisibility=False, resizeTarget=None):
        """ Info Embed Window

        For setting the settings of browser items

        :param parent:
        :param toolsetWidget:
        """
        self.typeCombo = None  # type: ComboBoxSearchable
        self.nameEdit = None  # type: LineEdit
        self.extensionLabel = None  # type: LineEdit
        self.authorEdit = None  # type: QtWidgets.QTextEdit
        self.websiteEdit = None  # type: QtWidgets.QTextEdit
        self.tagsEdit = None  # type: QtWidgets.QTextEdit
        self.descriptionEdit = None  # type: QtWidgets.QTextEdit
        self.metadata = None  # type: dict
        self.defaultMetadata = None  # type: dict
        self.item = None
        self._miniBrowser = parent
        self.browserModel = None  # type: filemodel.FileViewModel

        super(InfoEmbedWindow, self).__init__(parent, margins=margins, defaultVisibility=defaultVisibility,
                                              resizeTarget=resizeTarget)

    def initUi(self):
        """ Initialize Ui

        :return:
        """
        super(InfoEmbedWindow, self).initUi()  # Subclass builds the frame border and display/hide functionality
        self._buildWidgets()  # Build internal widgets
        self._buildLayouts()  # Build internal layout

    @property
    def miniBrowser(self):
        """

        :return:
        :rtype: zoo.libs.pyqt.extended.imageview.thumbnail.minibrowser.MiniBrowser
        """
        return self._miniBrowser

    @miniBrowser.setter
    def miniBrowser(self, value):
        """

        :param value:
        :type value: zoo.libs.pyqt.extended.imageview.thumbnail.minibrowser.MiniBrowser
        :return:
        :rtype:
        """
        self._miniBrowser = value


    def _buildWidgets(self):
        """ Builds all internal widgets for the Info Embed Window, includes the title and close button

        :return:
        :rtype:
        """
        # Top thumbnail ---------------------------
        self.thumbnail = QtWidgets.QToolButton(self)
        self.thumbnail.setStyleSheet("background-color: grey")  # todo fix this
        self.thumbnail.setFixedSize(QtCore.QSize(70, 70))
        # Information Title ---------------------------
        self.infoLabel = Label("Information", bold=True, upper=True)
        # Close Window Button ---------------------------
        # Note: self.hidePropertiesBtn name is important, links up to close behaviour automatically
        toolTip = "Close the Information window"
        self.hidePropertiesBtn = styledButton(icon="closeX",
                                              toolTip=toolTip,
                                              maxWidth=uic.BTN_W_ICN_SML,
                                              minWidth=uic.BTN_W_ICN_SML,
                                              style=uic.BTN_TRANSPARENT_BG)
        # Type Combo ---------------------------
        toolTip = "Specifies the type of asset, can be optional"
        self.typeLabel = Label(parent=self, text="Type", toolTip=toolTip)
        self.typeCombo = ComboBoxSearchable(items=ASSETTYPES, toolTip=toolTip)
        # Name Combo ---------------------------
        toolTip = "The filename of the asset with no extension"
        self.nameLabel = Label("Name", toolTip=toolTip)
        self.nameEdit = LineEdit(toolTip=toolTip)
        self.extensionLabel = Label(parent=self)
        self.extensionLabel.setEnabled(False)
        # Author/s ---------------------------
        toolTip = "The author/s of the asset\n " \
                  "Add each author on a new line"
        placeholderText = "3d Model: Your Name \n" \
                          "2d Concept: Artist Name"
        self.authorLabel = Label("Author/s", toolTip=toolTip)
        self.authorEdit = TextEdit(placeholderText=placeholderText, fixedHeight=52)
        # Website ---------------------------
        toolTip = "The website/s of the author/s, add each website on a new line"
        placeholderText = "www.yourwebsite.com\n" \
                          "www.conceptartist.com"
        self.websiteLabel = Label("Website/s", toolTip=toolTip)
        self.websiteEdit = TextEdit(placeholderText=placeholderText, fixedHeight=52)
        # Tags ---------------------------
        toolTip = "Add search tags for finding this asset later \n" \
                  "Eg. tagOne, tagTwo, tagThree"
        placeholderText = "tagOne, tagTwo, tagThree"
        self.tagsLabel = Label("Tags", toolTip=toolTip)
        self.tagsEdit = TextEdit(placeholderText=placeholderText, fixedHeight=52)
        # Description ---------------------------
        placeholderText = "Description"
        self.descriptionEdit = TextEdit(placeholderText=placeholderText, fixedHeight=78)

    def _buildLayouts(self):
        """ Builds the internal layout for the Info Embed Window

        :return:
        :rtype:
        """

        # Main layout ---------------------------
        layout = self.getLayout()  # gets self.propertiesLayout
        # Info Title and Close Button layout ---------------------------
        infoTitleLayout = hBoxLayout()
        infoTitleLayout.addWidget(self.infoLabel, 15)
        infoTitleLayout.addWidget(self.hidePropertiesBtn, 1)
        # Type and Name only ---------------------------
        basicInfoGrid = GridLayout()
        basicInfoGrid.addWidget(self.nameLabel, 0, 0)
        nameLayout = hBoxLayout()
        basicInfoGrid.addLayout(nameLayout, 0, 1)
        nameLayout.addWidget(self.nameEdit)
        nameLayout.addWidget(self.extensionLabel)
        basicInfoGrid.addWidget(self.typeLabel, 1, 0)
        basicInfoGrid.addWidget(self.typeCombo, 1, 1)
        basicInfoGrid.setColumnStretch(0, 1)
        basicInfoGrid.setColumnStretch(1, 3)
        # Info title, close button, type combo and name txt ---------------------------
        basicInfoLayout = vBoxLayout(margins=(uic.SMLPAD, 0, 0, 0), spacing=uic.SSML)
        basicInfoLayout.addLayout(infoTitleLayout)
        basicInfoLayout.addLayout(basicInfoGrid)
        # Label Layouts  (needed for the top margin spacing)
        authorLabelLayout = vBoxLayout(margins=(0, uic.SMLPAD, 0, 0), spacing=0)
        authorLabelLayout.addWidget(self.authorLabel)
        websiteLabelLayout = vBoxLayout(margins=(0, uic.SMLPAD, 0, 0), spacing=0)
        websiteLabelLayout.addWidget(self.websiteLabel)
        tagLabelLayout = vBoxLayout(margins=(0, uic.SMLPAD, 0, 0), spacing=0)
        tagLabelLayout.addWidget(self.tagsLabel)
        # Main grid layout ---------------------------
        gridLayout = GridLayout()
        gridLayout.addWidget(self.thumbnail, 0, 0)
        gridLayout.addLayout(basicInfoLayout, 0, 1)
        gridLayout.addLayout(authorLabelLayout, 1, 0)
        gridLayout.addWidget(self.authorEdit, 1, 1)
        gridLayout.addLayout(websiteLabelLayout, 2, 0)
        gridLayout.addWidget(self.websiteEdit, 2, 1)
        gridLayout.addLayout(tagLabelLayout, 3, 0)
        gridLayout.addWidget(self.tagsEdit, 3, 1)
        gridLayout.addWidget(self.descriptionEdit, 4, 0, 1, 2)
        # Set label v alignments
        gridLayout.setAlignment(authorLabelLayout, QtCore.Qt.AlignTop)
        gridLayout.setAlignment(websiteLabelLayout, QtCore.Qt.AlignTop)
        gridLayout.setAlignment(tagLabelLayout, QtCore.Qt.AlignTop)
        # Add to main layout ---------------------------
        layout.addLayout(gridLayout)

    def connections(self):
        """ Connections

        :return:
        """
        super(InfoEmbedWindow, self).connections()
        self.nameEdit.editingFinished.connect(self.rename)
        self.authorEdit.textChanged.connect(self.saveMetaData)
        self.tagsEdit.textChanged.connect(self.saveMetaData)
        self.websiteEdit.textChanged.connect(self.saveMetaData)
        self.descriptionEdit.textChanged.connect(self.saveMetaData)
        self.typeCombo.itemChanged.connect(self.saveMetaData)

    def setModel(self, model):
        """ Set the parent's model so we can get the information

        :param model:
        :type model:
        :return:
        :rtype:
        """
        self.browserModel = model
        self.browserModel.itemSelectionChanged.connect(self.selectionChanged)


    def model(self):
        """ Returns the thumbnailview model related to this info embed window

        :return:
        :rtype:
        """
        return self.browserModel

    def cancelClicked(self):
        """ Cancel clicked

        :return:
        """
        self.revert(True)
        self.hideEmbedWindow()

    def rename(self):
        """ Rename the zoo file and its dependencies

        :return:
        :rtype:
        """
        # Empty Text
        if self.nameEdit.text().strip() == "":
            self.revert(updateUi=True)
            om2.MGlobal.displayWarning("Name Field can't be empty")
            self.nameEdit.selectAll()
            return

        if self.metadata['name'] != self.nameEdit.text():
            self.saveMetaData()
            scenePath = self.metadata['zooFilePath']
            ext = self.metadata['extension']
            newName = self.nameEdit.text()

            renamedFiles, depDir = zooscenefiles.renameZooSceneOnDisk(newName, scenePath, ext)

            newName = path.getFileNameNoExt(renamedFiles[0])
            self.nameEdit.setText(newName)
            self.metadata['name'] = self.nameEdit.text()
            self.browserModel.refreshList()
            self.miniBrowser.thumbWidget.setItemByText(newName)
            self.visibilityChanged.emit(True)

    def saveMetaData(self):
        """ Save the meta data to

        :return:
        """
        zooscenefiles.writeZooInfo(self.metadata['zooFilePath'], self.typeCombo.currentText(),
                                   self.authorEdit.toPlainText(), self.websiteEdit.toPlainText(),
                                   self.tagsEdit.toPlainText(), self.descriptionEdit.toPlainText(),
                                   self.metadata['saved'], self.metadata['animation'])
        self.metadata['creators'] = self.authorEdit.toPlainText()
        self.metadata['tags'] = self.tagsEdit.toPlainText()
        self.metadata['websites'] = self.websiteEdit.toPlainText()
        self.metadata['description'] = self.descriptionEdit.toPlainText()
        self.metadata['assetType'] = self.typeCombo.currentText()
        self.metadata['extension'] = path.getExtension(self.metadata['zooFilePath'])
        self.item.metadata.update(self.metadata)

    def revert(self, updateUi=False):
        """ Revert back to original settings

        :param updateUi:
        :return:
        """
        self.metadata.update(self.defaultMetadata)
        if updateUi:
            self.applyMetaData(self.metadata)
        self.saveMetaData()

    def selectionChanged(self, image, item):
        """ Selection Changed

        :param image:
        :param item:
        :type item: items.BaseItem
        :return:
        """
        self.item = item
        self.metadata = item.metadata
        self.metadata['name'] = item.name  # todo: maybe this should be added to metadata initially

        self.defaultMetadata = dict(self.metadata)

        self.applyMetaData(self.metadata)

        if item.iconThread.image is not None:
            self.thumbnail.setIcon(QtGui.QPixmap.fromImage(item.iconThread.image))
        else:
            icon = QtGui.QIcon(item.iconPath)
            self.thumbnail.setIcon(icon)
        self.thumbnail.setIconSize(self.thumbnail.size())

    def applyMetaData(self, metadata):
        """ Apply the metadata to the UI

        :param metadata:
        :return:
        """
        applyText = ((self.nameEdit, metadata['name']),
                     (self.authorEdit, metadata['creators']),
                     (self.tagsEdit, metadata['tags']),
                     (self.websiteEdit, metadata['websites']),
                     (self.descriptionEdit, metadata['description']),
                     (self.extensionLabel, ".{}".format(metadata['extension'].upper()))
                     )

        for widget, text in applyText:
            widget.blockSignals(True)
            widget.setText(text)
            widget.blockSignals(False)

        self.typeCombo.setToTextQuiet(self.metadata['assetType'])


