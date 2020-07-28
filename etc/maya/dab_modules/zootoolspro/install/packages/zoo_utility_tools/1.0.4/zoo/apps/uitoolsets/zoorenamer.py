from functools import partial

import maya.api.OpenMaya as om2
import maya.mel as mel
from Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.libs.maya.cmds.general import undodecorator
from zoo.libs.maya.cmds.objutils import filtertypes
from zoo.libs.maya.cmds.objutils import namehandling as names
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

NAMESPACE_COMBO_LIST = ("Add/Replace", "Remove")
RENUMBER_COMBO_LIST = ("Replace", "Append", "Change Pad")


class ZooRenamer(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "zooRenamer"
    uiData = {"label": "Zoo Renamer",
              "icon": "zooRenamer",
              "tooltip": "Tools For Renaming Objects",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-zoo-renamer/"
              }

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run"""
        pass

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget(), self.initAdvancedWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        parent = QtWidgets.QWidget(parent=self)
        self.compactWidget = RenamerCompactWidget(parent=parent, properties=self.properties, toolsetWidget=self)
        return parent

    def initAdvancedWidget(self):
        """Builds the Advanced GUI (self.advancedWidget) """
        parent = QtWidgets.QWidget(parent=self)
        self.advancedWidget = RenamerAdvancedWidget(parent=parent, properties=self.properties, toolsetWidget=self)
        return parent

    def postContentSetup(self):
        """Last of the initialize code"""
        self.allDisableWidgets = [self.advancedWidget.atIndexTxt, self.advancedWidget.indexCombo,
                                  self.advancedWidget.indexTxt, self.advancedWidget.atIndexBtn,
                                  self.advancedWidget.indexLabel, self.advancedWidget.removeAllNumbersBtn,
                                  self.advancedWidget.removeTrailingNumbersBtn]
        for widget in self.widgets():  # add from both ui modes
            uiInstance = widget.children()[0]
            self.allDisableWidgets += [uiInstance.indexShuffleNegBtn, uiInstance.indexShuffleLabel,
                                       uiInstance.indexShufflePosBtn, uiInstance.indexShuffleTxt,
                                       uiInstance.indexShuffleTxt, uiInstance.renumberBtn, uiInstance.renumberLabel,
                                       uiInstance.renumberCombo, uiInstance.renumberPaddingTxt]
        self.displaySwitched.connect(self.updateFromProperties)
        self.connectionsRenamer()

    # ------------------
    # PROPERTIES
    # ------------------

    def initializeProperties(self):
        """Used to store and update UI data

        For use in the GUI use:
            current value: self.properties.itemName.value
            default value (automatic): self.properties.itemName.default

        To connect Qt widgets to property methods use:
            self.toolsetWidget.linkProperty(self.widgetQtName, "itemName")

        :return properties: special dictionary used to save and update all GUI widgets
        :rtype properties: list(dict)
        """
        return [{"name": "search", "value": ""},
                {"name": "replace", "value": ""},
                {"name": "prefix", "value": ""},
                {"name": "prefixCombo", "value": 0},
                {"name": "suffix", "value": ""},
                {"name": "suffixCombo", "value": 0},
                {"name": "atIndex", "value": ""},
                {"name": "indexCombo", "value": 0},
                {"name": "index", "value": -2},
                {"name": "renumberCombo", "value": 0},
                {"name": "padding", "value": 2},
                {"name": "optionsRadio", "value": 0},
                {"name": "objFilterCombo", "value": 0},
                {"name": "namespaceCombo", "value": 0},
                {"name": "namespace", "value": ""},
                {"name": "shapesBox", "value": 1},
                {"name": "shuffleIndex", "value": -1}]

    # ------------------
    # UI LOGIC
    # ------------------

    def disableWidgetsInAllMode(self, ):
        if self.displayIndex() == UI_MODE_COMPACT:
            radioOptionsInt = self.compactWidget.optionsRadioWidget.checkedIndex()
        else:
            radioOptionsInt = self.advancedWidget.optionsRadioWidget.checkedIndex()
        if radioOptionsInt == 2:  # disable while in delete mode (self.properties.indexCombo.value)
            for widget in self.allDisableWidgets:
                widget.setDisabled(True)
        else:
            for widget in self.allDisableWidgets:
                widget.setDisabled(False)
            if self.properties.indexCombo.value == 2:  # keep the atIndexTxt disabled if remove mode
                self.advancedWidget.atIndexTxt.setDisabled(True)

    def disableEnableAtIndexTxt(self, indexValue, stringValue):
        """Disables the 'Add At Index' lineEdit while the combo box is in 'Remove' mode"""
        if indexValue == 2:  # disable while in delete mode (self.properties.indexCombo.value)
            self.advancedWidget.atIndexTxt.setDisabled(True)
        else:
            self.advancedWidget.atIndexTxt.setDisabled(False)

    def populatePrefixSuffix(self, comboInt, comboText, sptype=names.SUFFIX):
        """Adds the suffix/prefix text into the prefix or suffix lineEdits when changing the prefix/suffix combo boxes

        :param comboInt: The combo value as an integer
        :type comboInt: int
        :param comboText: The combo value as a string
        :type comboText: str
        :param sptype: "prefix" or "suffix", switches the mode of the method
        :type sptype: str
        """
        if comboText == filtertypes.SUFFIXLIST[0]:  # then it's "Select..." so do nothing
            return
        textParts = comboText.split("'")
        if sptype == names.SUFFIX:
            textParts = comboText.split("'")
            self.properties.suffix.value = "_{}".format(textParts[-2])
        if sptype == names.PREFIX:
            self.properties.prefix.value = "{}_".format(textParts[-2])
        self.updateFromProperties()

    def openNamespaceEditor(self):
        """Opens the Namespace Editor"""
        mel.eval('namespaceEditor')

    def openReferenceEditor(self):
        """Opens the Reference Editor"""
        mel.eval('tearOffRestorePanel "Reference Editor" referenceEditor true')

    # ------------------
    # CORE LOGIC
    # ------------------

    def setFilterVars(self):
        """sets variables for the filter radio box used in the filterTypes.filterByNiceType() function

        :return searchHierarchy: search hierarchy option
        :rtype searchHierarchy: bool
        :return selectionOnly: selectionOnly option
        :rtype selectionOnly: bool
        """
        checkedRadioNumber = self.properties.optionsRadio.value
        if checkedRadioNumber == 0:  # selection
            searchHierarchy = False
            selectionOnly = True
        elif checkedRadioNumber == 1:  # hierarchy
            searchHierarchy = True
            selectionOnly = True
        else:  # all
            searchHierarchy = False
            selectionOnly = False
        return searchHierarchy, selectionOnly

    @undodecorator.undoDecorator
    def searchReplace(self):
        """Prefix and suffix logic, see names.searchReplaceFilteredType() for documentation"""
        searchHierarchy, selectionOnly = self.setFilterVars()
        niceNameType = filtertypes.TYPE_FILTER_LIST[self.properties.objFilterCombo.value]
        searchTxt = self.properties.search.value
        replaceTxt = self.properties.replace.value
        if searchTxt == "":
            om2.MGlobal.displayWarning("Please type search text")
            return
        if ":" in replaceTxt or ":" in searchTxt:
            om2.MGlobal.displayWarning("':' is an illegal character in regular Maya names, use the namespaces instead")
            return
        # Compact UI mode -----------------------------
        if self.displayIndex() == UI_MODE_COMPACT:
            names.searchReplaceFilteredType(searchTxt,
                                            replaceTxt,
                                            filtertypes.ALL,
                                            renameShape=True,
                                            searchHierarchy=searchHierarchy,
                                            selectionOnly=selectionOnly,
                                            dag=False,
                                            removeMayaDefaults=True,
                                            transformsOnly=True,
                                            message=True)
            return
        # Advanced UI mode -----------------------------
        names.searchReplaceFilteredType(searchTxt,
                                        replaceTxt,
                                        niceNameType,
                                        renameShape=self.properties.shapesBox.value,
                                        searchHierarchy=searchHierarchy,
                                        selectionOnly=selectionOnly,
                                        dag=False,
                                        removeMayaDefaults=True,
                                        transformsOnly=True,
                                        message=True)

    @undodecorator.undoDecorator
    def addPrefixSuffix(self, sptype=names.SUFFIX):
        """Prefix and suffix logic, see names.prefixSuffixFilteredType() for documentation

        :param sptype: "suffix" or "prefix"
        :type sptype: str
        """
        searchHierarchy, selectionOnly = self.setFilterVars()
        niceNameType = filtertypes.TYPE_FILTER_LIST[self.properties.objFilterCombo.value]
        if sptype == names.SUFFIX:
            prefixSuffix = self.properties.suffix.value
        else:
            prefixSuffix = self.properties.prefix.value
        if prefixSuffix == "":  # nothing entered
            om2.MGlobal.displayWarning("Please type prefix or suffix text")
            return
        if prefixSuffix[0].isdigit() and sptype == names.PREFIX:  # first letter is a digit which is illegal in Maya
            om2.MGlobal.displayWarning("Maya names cannot start with numbers")
            return

        # Compact UI mode -----------------------------
        if self.displayIndex() == UI_MODE_COMPACT:
            names.prefixSuffixFilteredType(prefixSuffix,
                                           niceNameType,
                                           sptype=sptype,
                                           renameShape=True,
                                           searchHierarchy=searchHierarchy,
                                           selectionOnly=selectionOnly,
                                           dag=False,
                                           removeMayaDefaults=True,
                                           transformsOnly=True,
                                           message=True)
            return
        # Advanced UI mode -----------------------------
        names.prefixSuffixFilteredType(prefixSuffix,
                                       niceNameType,
                                       sptype=sptype,
                                       renameShape=self.properties.shapesBox.value,
                                       searchHierarchy=searchHierarchy,
                                       selectionOnly=selectionOnly,
                                       dag=False,
                                       removeMayaDefaults=True,
                                       transformsOnly=True,
                                       message=True)

    @undodecorator.undoDecorator
    def autoPrefixSuffix(self, sptype=names.SUFFIX):
        """Auto prefix logic, see names.autoPrefixSuffixFilteredType() for documentation

        :param sptype: "suffix" or "prefix"
        :type sptype: str
        """
        searchHierarchy, selectionOnly = self.setFilterVars()
        niceNameType = filtertypes.TYPE_FILTER_LIST[self.properties.objFilterCombo.value]
        # Compact UI mode -----------------------------
        if self.displayIndex() == UI_MODE_COMPACT:
            names.autoPrefixSuffixFilteredType(niceNameType,
                                               sptype=sptype,
                                               renameShape=True,
                                               searchHierarchy=searchHierarchy,
                                               selectionOnly=selectionOnly,
                                               dag=False,
                                               removeMayaDefaults=True,
                                               transformsOnly=True,
                                               message=True)
            return
        # Advanced UI mode -----------------------------
        names.autoPrefixSuffixFilteredType(niceNameType,
                                           sptype=sptype,
                                           renameShape=self.properties.shapesBox.value,
                                           searchHierarchy=searchHierarchy,
                                           selectionOnly=selectionOnly,
                                           dag=False,
                                           removeMayaDefaults=True,
                                           transformsOnly=True,
                                           message=True)

    def renumberUI(self):
        """Method called by the renumber button, combo could be in "Change Pad" or "Append" modes, so run logic
        """
        renumberOptions = RENUMBER_COMBO_LIST[self.properties.renumberCombo.value]
        if renumberOptions == "Change Pad":
            self.changePadding()
            return
        if renumberOptions == "Append":
            self.renumber(trailingOnly=False)
        else:
            self.renumber(trailingOnly=True)

    @undodecorator.undoDecorator
    def renumber(self, trailingOnly=False):
        """Renumber logic
        See names.renumberFilteredType() for filter documentation"""
        searchHierarchy, selectionOnly = self.setFilterVars()
        if not searchHierarchy and not selectionOnly:  # all so bail
            om2.MGlobal.displayWarning("Renumber must be used with 'Selected' or 'Hierarchy', not 'All'")
            return
        niceNameType = filtertypes.TYPE_FILTER_LIST[self.properties.objFilterCombo.value]
        # Compact UI mode -----------------------------
        if self.displayIndex() == UI_MODE_COMPACT:
            names.renumberFilteredType(filtertypes.ALL,
                                       removeTrailingNumbers=trailingOnly,
                                       padding=int(self.properties.padding.value),
                                       addUnderscore=True,
                                       renameShape=True,
                                       searchHierarchy=searchHierarchy,
                                       selectionOnly=selectionOnly,
                                       dag=False,
                                       removeMayaDefaults=True,
                                       transformsOnly=True,
                                       message=True)
            return
        # Advanced UI mode -----------------------------
        if not searchHierarchy and not selectionOnly:  # all so bail
            om2.MGlobal.displayWarning("Renumber must be used with 'Selected' or 'Hierarchy', not 'All'")
            return
        names.renumberFilteredType(niceNameType,
                                   removeTrailingNumbers=trailingOnly,
                                   padding=int(self.properties.padding.value),
                                   addUnderscore=True,
                                   renameShape=self.properties.shapesBox.value,
                                   searchHierarchy=searchHierarchy,
                                   selectionOnly=selectionOnly,
                                   dag=False,
                                   removeMayaDefaults=True,
                                   transformsOnly=True,
                                   message=True)

    @undodecorator.undoDecorator
    def removeNumbers(self, trailingOnly=True):
        """Removing number logic,
        See names.removeNumbersFilteredType() for filter documentation"""
        searchHierarchy, selectionOnly = self.setFilterVars()
        niceNameType = filtertypes.TYPE_FILTER_LIST[self.properties.objFilterCombo.value]
        names.removeNumbersFilteredType(niceNameType,
                                        trailingOnly=trailingOnly,
                                        renameShape=self.properties.shapesBox.value,
                                        searchHierarchy=searchHierarchy,
                                        selectionOnly=selectionOnly,
                                        dag=False,
                                        removeMayaDefaults=True,
                                        transformsOnly=True,
                                        message=True)

    @undodecorator.undoDecorator
    def changePadding(self):
        """Change padding logic
        See names.changeSuffixPaddingFilter() for filter documentation"""
        searchHierarchy, selectionOnly = self.setFilterVars()
        niceNameType = filtertypes.TYPE_FILTER_LIST[self.properties.objFilterCombo.value]
        if not searchHierarchy and not selectionOnly:  # all so bail
            om2.MGlobal.displayWarning("Renumber must be used with 'Selected' or 'Hierarchy', not 'All'")
            return
        # Compact UI mode -----------------------------
        if self.displayIndex() == UI_MODE_COMPACT:
            names.changeSuffixPaddingFilter(filtertypes.ALL,
                                            padding=int(self.properties.padding.value),
                                            addUnderscore=True,
                                            renameShape=True,
                                            searchHierarchy=searchHierarchy,
                                            selectionOnly=selectionOnly,
                                            dag=False,
                                            removeMayaDefaults=True,
                                            transformsOnly=True,
                                            message=True)
            return
        # Advanced UI mode -----------------------------
        names.changeSuffixPaddingFilter(niceNameType,
                                        padding=int(self.properties.padding.value),
                                        addUnderscore=True,
                                        renameShape=self.properties.shapesBox.value,
                                        searchHierarchy=searchHierarchy,
                                        selectionOnly=selectionOnly,
                                        dag=False,
                                        removeMayaDefaults=True,
                                        transformsOnly=True,
                                        message=True)

    @undodecorator.undoDecorator
    def uniqueNames(self):
        """Unique names logic,
        See names.forceUniqueShortNameFiltered() for filter documentation"""
        searchHierarchy, selectionOnly = self.setFilterVars()
        niceNameType = filtertypes.TYPE_FILTER_LIST[self.properties.objFilterCombo.value]
        # Compact UI mode -----------------------------
        if self.displayIndex() == UI_MODE_COMPACT:
            names.forceUniqueShortNameFiltered(filtertypes.ALL,
                                               padding=int(self.properties.padding.value),
                                               shortNewName=True,
                                               renameShape=True,
                                               searchHierarchy=searchHierarchy,
                                               selectionOnly=selectionOnly,
                                               dag=False,
                                               removeMayaDefaults=True,
                                               transformsOnly=True,
                                               message=True)
            return
        # Advanced UI mode -----------------------------
        names.forceUniqueShortNameFiltered(niceNameType,
                                           padding=int(self.properties.padding.value),
                                           shortNewName=True,
                                           renameShape=self.properties.shapesBox.value,
                                           searchHierarchy=searchHierarchy,
                                           selectionOnly=selectionOnly,
                                           dag=False,
                                           removeMayaDefaults=True,
                                           transformsOnly=True,
                                           message=True)

    @undodecorator.undoDecorator
    def editIndex(self, removeSuffix=False, removePrefix=False):
        """

        See names.searchReplaceFilteredType() for filter documentation
        """
        searchHierarchy, selectionOnly = self.setFilterVars()
        if not searchHierarchy and not selectionOnly:  # all so bail
            om2.MGlobal.displayWarning("Move By Index must be used with 'Selected' or 'Hierarchy', not 'All'")
            return
        niceNameType = filtertypes.TYPE_FILTER_LIST[self.properties.objFilterCombo.value]
        text = ""
        if not removePrefix and not removeSuffix:  # then use the GUI settings
            modeInt = int(self.properties.indexCombo.value)
            text = self.properties.atIndex.value
            if modeInt == 0:
                mode = names.EDIT_INDEX_INSERT
            elif modeInt == 1:
                mode = names.EDIT_INDEX_REPLACE
            else:  # == 2
                mode = names.EDIT_INDEX_REMOVE
            index = int(self.properties.index.value)
            if index > 0:  # if not negative, make artist friendly GUI numbers start at 1, (code functions start at 0)
                index -= 1
        if removePrefix:
            mode = names.EDIT_INDEX_REMOVE
            index = 0
        elif removeSuffix:
            mode = names.EDIT_INDEX_REMOVE
            index = -1
        # Compact UI mode -----------------------------
        if self.displayIndex() == UI_MODE_COMPACT:
            names.editIndexItemFilteredType(index,
                                            niceNameType,
                                            text=text,
                                            mode=mode,
                                            separator="_",
                                            renameShape=True,
                                            searchHierarchy=searchHierarchy,
                                            selectionOnly=selectionOnly,
                                            dag=False,
                                            removeMayaDefaults=True,
                                            transformsOnly=True,
                                            message=True)
        else:
            # Advanced UI mode -----------------------------
            names.editIndexItemFilteredType(index,
                                            niceNameType,
                                            text=text,
                                            mode=mode,
                                            separator="_",
                                            renameShape=self.properties.shapesBox.value,
                                            searchHierarchy=searchHierarchy,
                                            selectionOnly=selectionOnly,
                                            dag=False,
                                            removeMayaDefaults=True,
                                            transformsOnly=True,
                                            message=True)
        return

    @undodecorator.undoDecorator
    def shuffleItemByIndex(self, offset):
        """Move text items separated by underscores to a new position.  With filters from GUI
        Updates the GUI after the move so the same item stays in focus

        Example:

            objName: "pCube1_xxx_yyy_001"
            index 3:
            offset -1:
            result: "pCube1_xxx_001_yyy

        See names.searchReplaceFilteredType() for filter documentation
        """
        searchHierarchy, selectionOnly = self.setFilterVars()
        if not searchHierarchy and not selectionOnly:  # all so bail
            om2.MGlobal.displayWarning("Move By Index must be used with 'Selected' or 'Hierarchy', not 'All'")
            return
        niceNameType = filtertypes.TYPE_FILTER_LIST[self.properties.objFilterCombo.value]
        shuffleIndex = int(self.properties.shuffleIndex.value)
        if shuffleIndex > 0:  # if not negative, make artist friendly GUI numbers start at 1, (code functions start 0)
            shuffleIndex -= 1
        # Compact UI mode -----------------------------
        if self.displayIndex() == UI_MODE_COMPACT:
            names.shuffleItemByIndexFilteredType(shuffleIndex,
                                                 niceNameType,
                                                 offset=offset,
                                                 separator="_",
                                                 renameShape=True,
                                                 searchHierarchy=searchHierarchy,
                                                 selectionOnly=selectionOnly,
                                                 dag=False,
                                                 removeMayaDefaults=True,
                                                 transformsOnly=True,
                                                 message=True)
        else:
            # Advanced UI mode -----------------------------
            names.shuffleItemByIndexFilteredType(shuffleIndex,
                                                 niceNameType,
                                                 offset=offset,
                                                 separator="_",
                                                 renameShape=self.properties.shapesBox.value,
                                                 searchHierarchy=searchHierarchy,
                                                 selectionOnly=selectionOnly,
                                                 dag=False,
                                                 removeMayaDefaults=True,
                                                 transformsOnly=True,
                                                 message=True)
        oldValue = int(self.properties.shuffleIndex.value)
        newValue = oldValue + offset
        if newValue == 0:  # make pos 1
            if oldValue > 1:
                newValue = 1
            else:
                newValue = -1
        self.properties.shuffleIndex.value = newValue
        self.updateFromProperties()
        return

    @undodecorator.undoDecorator
    def deleteSelectedNamespace(self):
        """Will empty the first selected namespace and then try and delete the namespace"""
        if self.displayIndex() == UI_MODE_COMPACT:
            names.deleteSelectedNamespace(renameShape=True)
        else:
            names.deleteSelectedNamespace(renameShape=self.properties.shapesBox.value)

    @undodecorator.undoDecorator
    def assignNamespace(self):
        """Assign Namespace names"""
        removeNamespace = False
        searchHierarchy, selectionOnly = self.setFilterVars()
        niceNameType = filtertypes.TYPE_FILTER_LIST[self.properties.objFilterCombo.value]
        namespaceName = self.properties.namespace.value
        if self.properties.namespaceCombo.value == 1:  # remove mode
            removeNamespace = True
        # Compact UI mode -----------------------------
        if self.displayIndex() == UI_MODE_COMPACT:
            names.createAssignNamespaceFilteredType(namespaceName,
                                                    niceNameType,
                                                    removeNamespace=removeNamespace,
                                                    renameShape=True,
                                                    searchHierarchy=searchHierarchy,
                                                    selectionOnly=selectionOnly,
                                                    dag=False,
                                                    removeMayaDefaults=True,
                                                    transformsOnly=True,
                                                    message=True)
            return
        # Advanced UI mode -----------------------------
        names.createAssignNamespaceFilteredType(namespaceName,
                                                niceNameType,
                                                removeNamespace=removeNamespace,
                                                renameShape=self.properties.shapesBox.value,
                                                searchHierarchy=searchHierarchy,
                                                selectionOnly=selectionOnly,
                                                dag=False,
                                                removeMayaDefaults=True,
                                                transformsOnly=True,
                                                message=True)

    # ------------------
    # CONNECTIONS
    # ------------------

    def connectionsRenamer(self):
        """Connects up the buttons to the Zoo Renamer logic """
        # both GUIs
        for widget in self.widgets():
            uiInstance = widget.children()[0]
            uiInstance.searchReplaceBtn.clicked.connect(self.searchReplace)
            uiInstance.prefixBtn.clicked.connect(partial(self.addPrefixSuffix, sptype=names.PREFIX))
            uiInstance.suffixBtn.clicked.connect(partial(self.addPrefixSuffix, sptype=names.SUFFIX))
            uiInstance.autoSuffixBtn.clicked.connect(partial(self.autoPrefixSuffix, sptype=names.SUFFIX))
            uiInstance.renumberBtn.clicked.connect(self.renumberUI)
            uiInstance.indexShuffleNegBtn.clicked.connect(partial(self.shuffleItemByIndex, offset=-1))
            uiInstance.indexShufflePosBtn.clicked.connect(partial(self.shuffleItemByIndex, offset=1))
            uiInstance.prefixListCombo.itemChanged.connect(partial(self.populatePrefixSuffix, sptype=names.PREFIX))
            uiInstance.suffixListCombo.itemChanged.connect(partial(self.populatePrefixSuffix, sptype=names.SUFFIX))
            uiInstance.deleteSelNamespaceBtn.clicked.connect(self.deleteSelectedNamespace)
            uiInstance.optionsRadioWidget.toggled.connect(self.disableWidgetsInAllMode)
            uiInstance.removeAllNumbersBtn.clicked.connect(partial(self.removeNumbers, trailingOnly=False))
            uiInstance.removeTrailingNumbersBtn.clicked.connect(partial(self.removeNumbers, trailingOnly=True))
        # advanced GUI
        self.advancedWidget.atIndexBtn.clicked.connect(self.saveProperties)
        self.advancedWidget.atIndexBtn.clicked.connect(self.editIndex)
        self.advancedWidget.namespaceWindowOpenBtn.clicked.connect(self.openNamespaceEditor)
        self.advancedWidget.referenceWindowOpenBtn.clicked.connect(self.openReferenceEditor)
        self.advancedWidget.removePrefixBtn.clicked.connect(partial(self.editIndex, removePrefix=True))
        self.advancedWidget.indexCombo.itemChanged.connect(self.disableEnableAtIndexTxt)
        self.advancedWidget.namespaceBtn.clicked.connect(self.assignNamespace)
        self.advancedWidget.removeSuffixBtn.clicked.connect(partial(self.editIndex, removeSuffix=True))
        self.advancedWidget.makeUniqueBtn.clicked.connect(self.uniqueNames)


class RenamerWidgets(QtWidgets.QWidget):
    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None):
        """Builds the main widgets for all GUIs

        properties is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: ZooRenamer
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: object
        :param uiMode: 0 is compact ui mode, 1 is advanced ui mode
        :type uiMode: int
        """
        super(RenamerWidgets, self).__init__(parent=parent)

        self.toolsetWidget = toolsetWidget
        self.properties = properties
        # Top Radio Buttons ------------------------------------
        radioNameList = ["Selected", "Hierarchy", "All"]
        radioToolTipList = ["Rename based on selected objects/nodes.",
                            "Rename the selected object and it's hierarchy below.",
                            "Rename all objects/nodes in the scene."]
        self.optionsRadioWidget = elements.RadioButtonGroup(radioList=radioNameList, toolTipList=radioToolTipList,
                                                            default=0, parent=parent)
        self.toolsetWidget.linkProperty(self.optionsRadioWidget, "optionsRadio")
        # Search Replace ------------------------------------
        toolTip = "Search and replace selected object/node names\n" \
                  "Text in the first text box gets replaced by the second."
        self.searchTxt = elements.LineEdit(text=self.properties.search.value,
                                           placeholder="Search",
                                           toolTip=toolTip,
                                           parent=parent)
        self.toolsetWidget.linkProperty(self.searchTxt, "search")
        self.replaceTxt = elements.LineEdit(text=self.properties.replace.value,
                                            placeholder="Replace",
                                            toolTip=toolTip,
                                            parent=parent)
        self.toolsetWidget.linkProperty(self.replaceTxt, "replace")
        self.searchReplaceBtn = elements.styledButton("",
                                                      "searchReplace",
                                                      toolTip=toolTip,
                                                      parent=parent,
                                                      minWidth=uic.BTN_W_ICN_MED)
        # Prefix ------------------------------------
        toolTip = "Add a prefix to the selected object/node names"
        self.prefixTxt = elements.StringEdit(self.properties.prefix.value,
                                             editPlaceholder="Add Prefix",
                                             toolTip=toolTip,
                                             parent=parent)
        self.toolsetWidget.linkProperty(self.prefixTxt, "prefix")
        self.prefixBtn = elements.styledButton("",
                                               "prefix",
                                               toolTip=toolTip,
                                               parent=parent,
                                               minWidth=uic.BTN_W_ICN_MED)
        toolTip = "Predefined Maya suffix/prefix name list"

        self.prefixListCombo = elements.ComboBoxSearchable(items=filtertypes.SUFFIXLIST,
                                                           setIndex=self.properties.prefixCombo.value,
                                                           parent=parent,
                                                           toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.prefixListCombo, "prefixCombo")
        # Suffix ------------------------------------
        toolTip = "Add a suffix to the selected object/node names"
        self.suffixTxt = elements.StringEdit(self.properties.suffix.value,
                                             editPlaceholder="Add Suffix",
                                             toolTip=toolTip,
                                             parent=parent)
        self.toolsetWidget.linkProperty(self.suffixTxt, "suffix")
        self.suffixBtn = elements.styledButton("",
                                               "suffix",
                                               toolTip=toolTip,
                                               parent=parent,
                                               minWidth=uic.BTN_W_ICN_MED)
        toolTip = "Predefined Maya suffix/prefix name list"
        self.suffixListCombo = elements.ComboBoxSearchable(items=filtertypes.SUFFIXLIST,
                                                           setIndex=self.properties.suffixCombo.value,
                                                           parent=parent,
                                                           toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.suffixListCombo, "suffixCombo")
        # Index Shuffle ------------------------------------
        toolTip = "Shuffle the item part of a name, usually separated by underscores '_'\n" \
                  "The index value is artist friendly and starts at 1\n" \
                  "Negative numbers start at the end values\n" \
                  "'object_geo_01' with index -1 (left arrow) will become 'object_01_geo'\n" \
                  "'object_geo_01' with index 1 (right arrow) will become 'geo_object_01'"
        self.indexShuffleLabel = elements.Label("Move By Index", parent=parent, toolTip=toolTip)
        self.indexShuffleNegBtn = elements.styledButton("",
                                                        "arrowStandardLeft",
                                                        toolTip=toolTip,
                                                        parent=parent,
                                                        minWidth=uic.BTN_W_ICN_MED)
        self.indexShuffleTxt = elements.IntEdit("",
                                                   self.properties.shuffleIndex.value,
                                                   toolTip=toolTip,
                                                   parent=parent)
        self.toolsetWidget.linkProperty(self.indexShuffleTxt, "shuffleIndex")
        self.indexShufflePosBtn = elements.styledButton("",
                                                        "arrowStandardRight",
                                                        toolTip=toolTip,
                                                        parent=parent,
                                                        minWidth=uic.BTN_W_ICN_MED)
        # Renumber ------------------------------------
        toolTip = "Renumber or change numerical padding\n" \
                  "Replace: Renumbers in sel or hierarchy order. 'object1' becomes 'object_01'\n" \
                  "Append: Renumbers in sel or hierarchy order. 'object1' becomes 'object1_01'\n" \
                  "Change Pad: Keeps the number and changes padding. 'char1_object3' becomes 'char1_object_03'\n" \
                  "*Change Pad only affects the trailing numbers. 'object3' not 'object3_geo'"
        if uiMode == UI_MODE_COMPACT:
            self.renumberLabel = elements.Label("Renumber", parent, toolTip=toolTip)
        if uiMode == UI_MODE_ADVANCED:
            self.renumberLabel = elements.Label("Renumber", parent, toolTip=toolTip, bold=True)  # bold for advanced
        self.renumberBtn = elements.styledButton("",
                                                 "renumber",
                                                 toolTip=toolTip,
                                                 parent=parent,
                                                 minWidth=uic.BTN_W_ICN_MED)
        self.renumberCombo = elements.ComboBoxRegular(items=RENUMBER_COMBO_LIST,
                                                      parent=parent,
                                                      setIndex=self.properties.renumberCombo.value,
                                                      toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.renumberCombo, "renumberCombo")
        toolTip = "Numeric padding of the trailing number\n" \
                  "1: 1 , 2, 3, 4\n" \
                  "2: 01, 02, 03, 04\n" \
                  "3: 001, 002, 003, 004"
        self.renumberPaddingTxt = elements.IntEdit("Pad",
                                                      int(self.properties.padding.value),
                                                      toolTip=toolTip,
                                                      parent=parent)
        self.toolsetWidget.linkProperty(self.renumberPaddingTxt, "padding")
        # Renumber Remove Buttons ------------------------------------
        toolTip = "Remove all numbers from object names\n" \
                  "'scene2_pcube1' becomes 'scene_pcube'\n" \
                  "Note: names must not clash with other nodes of the same name"
        self.removeAllNumbersBtn = elements.styledButton("Remove All Numbers",
                                                         "trash",
                                                         toolTip=toolTip,
                                                         parent=parent,
                                                         style=uic.BTN_LABEL_SML)
        toolTip = "Remove the trailing numbers from object names\n" \
                  "'scene2_pcube1' becomes 'scene2_pcube'\n" \
                  "Note: names must not clash with other nodes of the same name\n"
        self.removeTrailingNumbersBtn = elements.styledButton("Remove Tail Numbers",
                                                              "trash",
                                                              toolTip=toolTip,
                                                              parent=parent,
                                                              style=uic.BTN_LABEL_SML)
        # Auto Names ------------------------------------
        toolTip = "Automatically suffix objects based off their type\n" \
                  "'pCube1' becomes 'pCube1_geo'\n" \
                  "'locator1' becomes 'locator1_loc'"
        self.autoSuffixBtn = elements.styledButton("Automatic Suffix",
                                                   "suffix",
                                                   toolTip=toolTip,
                                                   parent=parent,
                                                   style=uic.BTN_LABEL_SML)
        # Delete selected Namespace btn ------------------------------------
        toolTip = "Deletes the selected namespace/s for the whole scene. Select objects and run.\n" \
                  "'scene:geo1' becomes 'geo1'\n" \
                  "Will delete the namespace for all objects in the scene."
        self.deleteSelNamespaceBtn = elements.styledButton("Delete Namespace",
                                                           "trash",
                                                           toolTip=toolTip,
                                                           parent=parent,
                                                           style=uic.BTN_LABEL_SML)

        if uiMode == UI_MODE_ADVANCED:
            # filter label ------------------------------------
            toolTip = "Filter renaming with the following options"
            self.filtersLabel = elements.Label("Filters", parent, toolTip=toolTip, bold=True)
            # dividers ------------------------------------
            self.filtersDivider = elements.Divider(parent=parent)
            self.searchReplaceDivider = elements.Divider(parent=parent)
            self.prefixSuffixDivider = elements.Divider(parent=parent)
            self.atIndexDivider = elements.Divider(parent=parent)
            self.renumberDivider = elements.Divider(parent=parent)
            self.namespaceDivider = elements.Divider(parent=parent)
            self.miscDivider = elements.Divider(parent=parent)
            # object filter ------------------------------------
            toolTip = "Only rename these object types"
            self.objFilterCombo = elements.ComboBoxSearchable(items=filtertypes.TYPE_FILTER_LIST,
                                                              setIndex=self.properties.objFilterCombo.value,
                                                              parent=parent,
                                                              toolTip=toolTip)
            self.toolsetWidget.linkProperty(self.objFilterCombo, "objFilterCombo")
            # checkbox options ------------------------------------
            toolTip = "When on, shape nodes will be renamed with the transform names.\n" \
                      "Example: `pCube_002` renames it's shape node `pCube_002Shape`"
            self.autoShapesBox = elements.CheckBox("Auto Shapes",
                                                   checked=self.properties.shapesBox.value,
                                                   parent=parent,
                                                   toolTip=toolTip)
            self.toolsetWidget.linkProperty(self.autoShapesBox, "shapesBox")
            # Index Label ------------------------------------
            toolTip = "Add/Edit by Artist friendly index, underscore seperated \n" \
                      "Example: 01_02_03_-02_-01 etc"
            self.indexLabel = elements.Label("Index", parent=parent, toolTip=toolTip, bold=True)
            # Prefix Suffix Label ------------------------------------
            toolTip = "Add a suffix or prefix to object/node names"
            self.prefixSuffixLabel = elements.Label("Prefix/Suffix", parent=parent, toolTip=toolTip, bold=True)
            # Search & Replace Label ------------------------------------
            toolTip = "Search and replace selected object/node names\n" \
                      "Text in the first text box gets replaced by the second."
            self.searchReplaceLabel = elements.Label("Search And Replace", parent=parent, toolTip=toolTip, bold=True)
            # Prefix Delete Button ------------------------------------
            toolTip = "Removes the prefix separated by an underscore '_'\n" \
                      "'scene1_pCube1_geo', becomes 'pCube1_geo'"
            self.removePrefixBtn = elements.styledButton("Remove Prefix",
                                                         "trash",
                                                         toolTip=toolTip,
                                                         parent=parent,
                                                         style=uic.BTN_LABEL_SML)
            # At Index ------------------------------------
            toolTip = "Add _text_ with artist friendly index value. Examples...  \n" \
                      "1: Adds a prefix\n" \
                      "-1: Adds a suffix\n" \
                      "2: Adds after the first underscore\n" \
                      "-2: Adds before the last underscore"
            self.atIndexTxt = elements.StringEdit(self.properties.atIndex.value,
                                                  editPlaceholder="Add At Index",
                                                  toolTip=toolTip,
                                                  parent=parent)
            self.toolsetWidget.linkProperty(self.atIndexTxt, "atIndex")
            self.indexTxt = elements.IntEdit("Index",
                                                int(self.properties.index.value),
                                                toolTip=toolTip,
                                                parent=parent)
            self.toolsetWidget.linkProperty(self.indexTxt, "index")
            self.atIndexBtn = elements.styledButton("",
                                                    "indexText",
                                                    toolTip=toolTip,
                                                    parent=parent,
                                                    minWidth=uic.BTN_W_ICN_MED)
            toolTip = "Insert: \n" \
                      "'geo' at 2: 'object_char_L' becomes 'object_geo_char_L'\n" \
                      "Replace:\n" \
                      "'geo' at -2: 'object_char_L' becomes 'object_geo_L'\n" \
                      "Remove:\n" \
                      "-2: 'object_char_L' becomes 'object_L'"
            self.indexCombo = elements.ComboBoxRegular(items=("Insert", "Replace", "Remove"),
                                                       setIndex=int(self.properties.indexCombo.value),
                                                       parent=parent,
                                                       toolTip=toolTip)
            self.toolsetWidget.linkProperty(self.indexCombo, "indexCombo")
            # Namespace ------------------------------------
            toolTip = "Edit add or delete namespaces (name suffix followed by a colon)\n" \
                      "Example:  `scene5:pCube1` > `scene5` is the namespace\n" \
                      "Note: Namespaces have hierarchies, use the 'Namespace Editor' for renaming and advanced features"
            self.namespaceLabel = elements.Label("Namespace", parent=parent, toolTip=toolTip, bold=True)
            self.namespaceTxt = elements.StringEdit(self.properties.namespace.value,
                                                    editPlaceholder="Namespace",
                                                    toolTip=toolTip,
                                                    parent=parent)
            self.toolsetWidget.linkProperty(self.namespaceTxt, "namespace")
            self.namespaceCombo = elements.ComboBoxRegular(items=NAMESPACE_COMBO_LIST,
                                                           setIndex=self.properties.namespaceCombo.value,
                                                           parent=parent,
                                                           toolTip=toolTip)
            self.toolsetWidget.linkProperty(self.namespaceCombo, "namespaceCombo")
            self.namespaceBtn = elements.styledButton("",
                                                      "namespace",
                                                      toolTip=toolTip,
                                                      parent=parent,
                                                      minWidth=uic.BTN_W_ICN_MED)
            # Namespace Delete  Empty Buttons ------------------------------------
            toolTip = "Deletes all empty/unused namespaces in the scene."
            self.deleteUnusedNamespaceBtn = elements.styledButton("Unused Namespaces",
                                                                  "trash",
                                                                  toolTip=toolTip,
                                                                  parent=parent,
                                                                  style=uic.BTN_LABEL_SML)
            # General Label ------------------------------------
            toolTip = "General buttons"
            self.miscLabel = elements.Label("Misc", parent=parent, toolTip=toolTip, bold=True)
            # Window Buttons ------------------------------------
            toolTip = "Opens the Namespace Editor, manages semi colon prefix names\n" \
                      "Example: 'scene01:***'"
            self.namespaceWindowOpenBtn = elements.styledButton("Namespace Editor",
                                                                "browserWindow",
                                                                toolTip=toolTip,
                                                                parent=parent,
                                                                style=uic.BTN_LABEL_SML)
            toolTip = "Opens the Reference Editor, manages referenced semi colon prefix names\n" \
                      "Example: 'rig:***'"
            self.referenceWindowOpenBtn = elements.styledButton("Reference Editor",
                                                                "browserWindow",
                                                                toolTip=toolTip,
                                                                parent=parent,
                                                                style=uic.BTN_LABEL_SML)
            # Make Unique Button ------------------------------------
            toolTip = "Make node names unique.\n" \
                      "If a name is duplicated it will be renamed with an incremental number\n" \
                      "Example:\n" \
                      "'shaderName' becomes 'shaderName_01'\n" \
                      "'shaderName2' becomes 'shaderName3'\n" \
                      "'shaderName_04' becomes 'shaderName_05'\n" \
                      "'shaderName_04' becomes 'shaderName_05'\n" \
                      "'shaderName_99' becomes 'shaderName_100'\n" \
                      "'shaderName_0009' becomes 'shaderName_0010'"
            self.makeUniqueBtn = elements.styledButton("Make Unique",
                                                       "snowflake",
                                                       toolTip=toolTip,
                                                       parent=parent,
                                                       style=uic.BTN_LABEL_SML)
            # Delete suffix btn ------------------------------------
            toolTip = "Removes the suffix separated by an underscore '_'\n" \
                      "'scene1_pCube1_geo', becomes 'scene1_pCube1'"
            self.removeSuffixBtn = elements.styledButton("Remove Suffix",
                                                         "trash",
                                                         toolTip=toolTip,
                                                         parent=parent,
                                                         style=uic.BTN_LABEL_SML)


class RenamerCompactWidget(RenamerWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None):
        """Adds the layout building the advanced version of the directional light UI:

            default uiMode - 1 is advanced (UI_MODE_ADVANCED)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(RenamerCompactWidget, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                                   toolsetWidget=toolsetWidget)
        # Main Layout ------------------------------------
        contentsLayout = elements.vBoxLayout(parent,
                                             margins=(uic.WINSIDEPAD,
                                                      0,
                                                      uic.WINSIDEPAD,
                                                      uic.WINBOTPAD),
                                             spacing=uic.SREG)
        # Top Radio Button Layout ------------------------------------
        optionsRadioLayout = elements.hBoxLayout(parent, spacing=0)
        optionsRadioLayout.addWidget(self.optionsRadioWidget)
        # Search Replace Layout ------------------------------------
        searchLayout = elements.hBoxLayout(parent, spacing=uic.SREG)
        searchLayout.addWidget(self.searchTxt, 12)
        searchLayout.addWidget(self.replaceTxt, 12)
        searchLayout.addWidget(self.searchReplaceBtn, 1)
        # Prefix Layout ------------------------------------
        prefixLayout = elements.hBoxLayout(parent, spacing=uic.SREG)
        prefixLayout.addWidget(self.prefixTxt, 12)
        prefixLayout.addWidget(self.prefixListCombo, 12)
        prefixLayout.addWidget(self.prefixBtn, 1)
        # Suffix Layout ------------------------------------
        suffixLayout = elements.hBoxLayout(parent, spacing=uic.SREG)
        suffixLayout.addWidget(self.suffixTxt, 12)
        suffixLayout.addWidget(self.suffixListCombo, 12)
        suffixLayout.addWidget(self.suffixBtn, 1)
        # Index Shuffle ------------------------------------
        indexShuffleLayout = elements.hBoxLayout(parent, spacing=uic.SREG)
        indexShuffleLayout.addWidget(self.indexShuffleLabel, 20)
        indexShuffleLayout.addWidget(self.indexShuffleNegBtn, 1)
        indexShuffleLayout.addWidget(self.indexShuffleTxt, 4)
        indexShuffleLayout.addWidget(self.indexShufflePosBtn, 1)
        # Renumber Layout ------------------------------------
        renumberLayout = elements.hBoxLayout(parent, spacing=uic.SVLRG)
        renumberLayout.addWidget(self.renumberLabel, 8)
        renumberLayout.addWidget(self.renumberCombo, 8)
        renumberLayout.addWidget(self.renumberPaddingTxt, 8)
        renumberLayout.addWidget(self.renumberBtn, 1)
        # Renumber Btn Layout ------------------------------------
        renumberBtnLayout = elements.hBoxLayout(parent, spacing=uic.SVLRG2)
        renumberBtnLayout.addWidget(self.removeAllNumbersBtn, 1)
        renumberBtnLayout.addWidget(self.removeTrailingNumbersBtn, 1)
        # Button Bottom Layout ------------------------------------
        btnLayout = elements.hBoxLayout(parent, spacing=uic.SVLRG2)
        btnLayout.addWidget(self.autoSuffixBtn, 1)
        btnLayout.addWidget(self.deleteSelNamespaceBtn, 1)
        # Add to main Layout ------------------------------------
        contentsLayout.addLayout(optionsRadioLayout)
        contentsLayout.addLayout(searchLayout)
        contentsLayout.addLayout(prefixLayout)
        contentsLayout.addLayout(suffixLayout)
        contentsLayout.addLayout(indexShuffleLayout)
        contentsLayout.addLayout(renumberLayout)
        contentsLayout.addLayout(renumberBtnLayout)
        contentsLayout.addLayout(btnLayout)
        contentsLayout.addStretch(1)


class RenamerAdvancedWidget(RenamerWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_ADVANCED, toolsetWidget=None):
        """Adds the layout building the advanced version of the directional light UI:

            default uiMode - 1 is advanced (UI_MODE_ADVANCED)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(RenamerAdvancedWidget, self).__init__(parent=parent, properties=properties,
                                                    uiMode=uiMode, toolsetWidget=toolsetWidget)
        # Main Layout ------------------------------------
        contentsLayout = elements.vBoxLayout(parent,
                                             margins=(uic.WINSIDEPAD,
                                                      uic.WINBOTPAD,
                                                      uic.WINSIDEPAD,
                                                      uic.WINBOTPAD),
                                             spacing=uic.SREG)
        # Filter Label Layout ------------------------------------
        filterLabelLayout = elements.hBoxLayout(parent, margins=(0, 0, 0, uic.SSML), spacing=uic.SREG)
        filterLabelLayout.addWidget(self.filtersLabel, 1)
        filterLabelLayout.addWidget(self.filtersDivider, 10)
        # Filter Layout ------------------------------------
        filterLayout = elements.hBoxLayout(parent, margins=(uic.REGPAD, 0, uic.REGPAD, 0), spacing=uic.SLRG)
        filterLayout.addWidget(self.objFilterCombo, 2)
        filterLayout.addWidget(self.autoShapesBox, 1)
        # Top Radio Button Layout ------------------------------------
        optionsRadioLayout = elements.hBoxLayout(parent, spacing=0)
        optionsRadioLayout.addWidget(self.optionsRadioWidget)
        # Search Replace Label Layout ------------------------------------
        searchReplaceLabelLayout = elements.hBoxLayout(parent, margins=(0, uic.SSML, 0, uic.SSML), spacing=uic.SREG)
        searchReplaceLabelLayout.addWidget(self.searchReplaceLabel, 1)
        searchReplaceLabelLayout.addWidget(self.searchReplaceDivider, 10)
        # Search Replace Layout ------------------------------------
        searchLayout = elements.hBoxLayout(parent, margins=(uic.REGPAD, 0, uic.REGPAD, 0), spacing=uic.SREG)
        searchLayout.addWidget(self.searchTxt, 12)
        searchLayout.addWidget(self.replaceTxt, 12)
        searchLayout.addWidget(self.searchReplaceBtn, 1)
        # Prefix Suffix Label Layout ------------------------------------
        prefixLabelLayout = elements.hBoxLayout(parent, margins=(0, uic.SSML, 0, uic.SSML), spacing=uic.SREG)
        prefixLabelLayout.addWidget(self.prefixSuffixLabel, 1)
        prefixLabelLayout.addWidget(self.prefixSuffixDivider, 10)
        # Prefix Layout ------------------------------------
        prefixLayout = elements.hBoxLayout(parent, margins=(uic.REGPAD, 0, uic.REGPAD, 0), spacing=uic.SREG)
        prefixLayout.addWidget(self.prefixTxt, 13)
        prefixLayout.addWidget(self.prefixListCombo, 11)
        prefixLayout.addWidget(self.prefixBtn, 1)
        # Suffix Layout ------------------------------------
        suffixLayout = elements.hBoxLayout(parent, margins=(uic.REGPAD, 0, uic.REGPAD, 0), spacing=uic.SREG)
        suffixLayout.addWidget(self.suffixTxt, 13)
        suffixLayout.addWidget(self.suffixListCombo, 11)
        suffixLayout.addWidget(self.suffixBtn, 1)
        # Remove Prefix/Suffix Button Layout ------------------------------------
        removePrefixSuffixLayout = elements.hBoxLayout(parent, margins=(uic.REGPAD, 0, uic.REGPAD, 0),
                                                       spacing=uic.SVLRG2)
        removePrefixSuffixLayout.addWidget(self.removePrefixBtn, 1)
        removePrefixSuffixLayout.addWidget(self.removeSuffixBtn, 1)
        # At Index Label Layout ------------------------------------
        indexAtLabelLayout = elements.hBoxLayout(parent, margins=(0, uic.SSML, 0, uic.SSML), spacing=uic.SREG)
        indexAtLabelLayout.addWidget(self.indexLabel, 1)
        indexAtLabelLayout.addWidget(self.atIndexDivider, 10)
        # At Index Layout ------------------------------------
        indexAtLayout = elements.hBoxLayout(parent, margins=(uic.REGPAD, 0, uic.REGPAD, 0), spacing=uic.SREG)
        indexAtLayout.addWidget(self.atIndexTxt, 8)
        indexAtLayout.addWidget(self.indexCombo, 8)
        indexAtLayout.addWidget(self.indexTxt, 8)
        indexAtLayout.addWidget(self.atIndexBtn, 1)
        # Index Shuffle ------------------------------------
        indexShuffleLayout = elements.hBoxLayout(parent, margins=(uic.REGPAD, 0, uic.REGPAD, 0), spacing=uic.SREG)
        indexShuffleLayout.addWidget(self.indexShuffleLabel, 20)
        indexShuffleLayout.addWidget(self.indexShuffleNegBtn, 1)
        indexShuffleLayout.addWidget(self.indexShuffleTxt, 4)
        indexShuffleLayout.addWidget(self.indexShufflePosBtn, 1)
        # Renumber Label Layout ------------------------------------
        renumberLabelLayout = elements.hBoxLayout(parent, margins=(0, uic.SSML, 0, uic.SSML), spacing=uic.SREG)
        renumberLabelLayout.addWidget(self.renumberLabel, 1)
        renumberLabelLayout.addWidget(self.renumberDivider, 10)
        # Renumber Layout ------------------------------------
        renumberLayout = elements.hBoxLayout(parent, margins=(uic.REGPAD, 0, uic.REGPAD, 0), spacing=uic.SREG)
        renumberLayout.addWidget(self.renumberCombo, 16)
        renumberLayout.addWidget(self.renumberPaddingTxt, 8)
        renumberLayout.addWidget(self.renumberBtn, 1)
        # Renumber Btn Layout ------------------------------------
        renumberBtnLayout = elements.hBoxLayout(parent, margins=(uic.REGPAD, 0, uic.REGPAD, 0), spacing=uic.SVLRG2)
        renumberBtnLayout.addWidget(self.removeAllNumbersBtn, 1)
        renumberBtnLayout.addWidget(self.removeTrailingNumbersBtn, 1)
        # Namespace Label Layout ------------------------------------
        namespaceLabelLayout = elements.hBoxLayout(parent, margins=(0, uic.SSML, 0, uic.SSML), spacing=uic.SREG)
        namespaceLabelLayout.addWidget(self.namespaceLabel, 1)
        namespaceLabelLayout.addWidget(self.namespaceDivider, 10)
        # Namespace Layout ------------------------------------
        namespaceLayout = elements.hBoxLayout(parent, margins=(uic.REGPAD, 0, uic.REGPAD, 0), spacing=uic.SREG)
        namespaceLayout.addWidget(self.namespaceTxt, 16)
        namespaceLayout.addWidget(self.namespaceCombo, 8)
        namespaceLayout.addWidget(self.namespaceBtn, 1)
        # Namespace Delete Btn Layout ------------------------------------
        delNamespaceLayout = elements.hBoxLayout(parent, margins=(uic.REGPAD, 0, uic.REGPAD, 0), spacing=uic.SVLRG2)
        delNamespaceLayout.addWidget(self.deleteSelNamespaceBtn, 1)
        delNamespaceLayout.addWidget(self.deleteUnusedNamespaceBtn, 1)
        # Misc Label Layout ------------------------------------
        miscLabelLayout = elements.hBoxLayout(parent, margins=(0, uic.SREG, 0, uic.SREG), spacing=uic.SREG)
        miscLabelLayout.addWidget(self.miscLabel, 1)
        miscLabelLayout.addWidget(self.miscDivider, 10)
        # Bottom Button Layout 1 ------------------------------------
        bottomBtnLayout1 = elements.hBoxLayout(parent, margins=(uic.REGPAD, 0, uic.REGPAD, 0), spacing=uic.SVLRG2)
        bottomBtnLayout1.addWidget(self.autoSuffixBtn, 1)
        bottomBtnLayout1.addWidget(self.makeUniqueBtn, 1)
        # Bottom Button Layout 2 ------------------------------------
        bottomBtnLayout2 = elements.hBoxLayout(parent, margins=(uic.REGPAD, 0, uic.REGPAD, 0), spacing=uic.SVLRG2)
        bottomBtnLayout2.addWidget(self.namespaceWindowOpenBtn, 1)
        bottomBtnLayout2.addWidget(self.referenceWindowOpenBtn, 1)
        # Add to main Layout ------------------------------------
        contentsLayout.addLayout(filterLabelLayout)
        contentsLayout.addLayout(filterLayout)
        contentsLayout.addLayout(optionsRadioLayout)
        contentsLayout.addItem(elements.Spacer(1, uic.SREG))
        contentsLayout.addLayout(searchReplaceLabelLayout)
        contentsLayout.addLayout(searchLayout)
        contentsLayout.addItem(elements.Spacer(1, uic.SREG))
        contentsLayout.addLayout(prefixLabelLayout)
        contentsLayout.addLayout(prefixLayout)
        contentsLayout.addLayout(suffixLayout)
        contentsLayout.addLayout(removePrefixSuffixLayout)
        contentsLayout.addItem(elements.Spacer(1, uic.SREG))
        contentsLayout.addLayout(indexAtLabelLayout)
        contentsLayout.addLayout(indexAtLayout)
        contentsLayout.addLayout(indexShuffleLayout)
        contentsLayout.addItem(elements.Spacer(1, uic.SREG))
        contentsLayout.addLayout(renumberLabelLayout)
        contentsLayout.addLayout(renumberLayout)
        contentsLayout.addItem(elements.Spacer(1, uic.SREG))
        contentsLayout.addLayout(renumberBtnLayout)
        contentsLayout.addItem(elements.Spacer(1, uic.SREG))
        contentsLayout.addLayout(namespaceLabelLayout)
        contentsLayout.addLayout(namespaceLayout)
        contentsLayout.addLayout(delNamespaceLayout)
        contentsLayout.addLayout(bottomBtnLayout2)
        contentsLayout.addItem(elements.Spacer(1, uic.SREG))
        contentsLayout.addLayout(miscLabelLayout)
        contentsLayout.addLayout(bottomBtnLayout1)
        contentsLayout.addStretch(1)
