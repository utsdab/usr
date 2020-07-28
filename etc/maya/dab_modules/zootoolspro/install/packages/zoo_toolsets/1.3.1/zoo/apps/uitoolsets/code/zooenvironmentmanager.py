import os

import maya.api.OpenMaya as om2
from Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import elements

PACKAGE_NAME_KEY = "packageName"
NICE_NAME_KEY = "niceName"
VENDOR_KEY = "vendor"
ACTIVE_KEY = "active"
ROOT_PATH_KEY = "rootPath"
DESCRIPTION_KEY = "description"

VENDOR_TYPE_CUSTOM = "Custom"
VENDOR_TYPE_ZOO = "ZooToolsPro"
VENDOR_TYPE_ALL = "all"

DEFAULT_DIRECTORY_PATH = r"D:/repos/zootools_pro"  # should get this from the Zoo Tools env variable

# Zoo Code Vendor Package Installs
zoocore_dict = {PACKAGE_NAME_KEY: "zoo_core",
                NICE_NAME_KEY: "Zoo Core",
                VENDOR_KEY: "ZooToolsPro",
                ACTIVE_KEY: "True",
                ROOT_PATH_KEY: r"D:/repos/zootools_pro",
                DESCRIPTION_KEY: "core scripts opensource"}
zoocore_maya_dict = {PACKAGE_NAME_KEY: "zoo_maya",
                     NICE_NAME_KEY: "Zoo Core Maya",
                     VENDOR_KEY: VENDOR_TYPE_ZOO,
                     ACTIVE_KEY: "True",
                     ROOT_PATH_KEY: r"D:/repos/zootools_pro",
                     DESCRIPTION_KEY: "maya core scripts opensource"}
zoocore_pro_dict = {PACKAGE_NAME_KEY: "zoo_core_pro",
                    NICE_NAME_KEY: "Zoo Core Pro",
                    VENDOR_KEY: VENDOR_TYPE_ZOO,
                    ACTIVE_KEY: "True",
                    ROOT_PATH_KEY: r"D:/repos/zootools_pro",
                    DESCRIPTION_KEY: "core scripts in commercial version of Zoo Tools Pro"}
zoopyside_dict = {PACKAGE_NAME_KEY: "zoo_pyside",
                  NICE_NAME_KEY: "Zoo PySide",
                  VENDOR_KEY: VENDOR_TYPE_ZOO,
                  ACTIVE_KEY: "True",
                  ROOT_PATH_KEY: r"D:/repos/zootools_pro",
                  DESCRIPTION_KEY: "UI code for zootools"}
zootoolsets_pro_dict = {PACKAGE_NAME_KEY: "zoo_toolsets",
                        NICE_NAME_KEY: "Zoo Tool Sets",
                        VENDOR_KEY: VENDOR_TYPE_ZOO,
                        ACTIVE_KEY: "True",
                        ROOT_PATH_KEY: r"D:/repos/zootools_pro",
                        DESCRIPTION_KEY: "code for the creation of Zoo Tool Sets"}
zoo_utilities_tools_dict = {PACKAGE_NAME_KEY: "zoo_utilities_tools",
                            NICE_NAME_KEY: "Zoo Utilities Tools",
                            VENDOR_KEY: VENDOR_TYPE_ZOO,
                            ACTIVE_KEY: "True",
                            ROOT_PATH_KEY: r"D:/repos/zootools_pro",
                            DESCRIPTION_KEY: "Utility tools for Zoo Tools Pro"}
zoo_preferences_dict = {PACKAGE_NAME_KEY: "zoo_preferences",
                        NICE_NAME_KEY: "Zoo Preferences",
                        VENDOR_KEY: VENDOR_TYPE_ZOO,
                        ACTIVE_KEY: "True",
                        ROOT_PATH_KEY: r"D:/repos/zootools_pro",
                        DESCRIPTION_KEY: "Preferences code for Zoo Tools Pro"}
zoo_light_suite = {PACKAGE_NAME_KEY: "zoo_light_suite",
                   NICE_NAME_KEY: "Zoo Light Suite",
                   VENDOR_KEY: VENDOR_TYPE_ZOO,
                   ACTIVE_KEY: "True",
                   ROOT_PATH_KEY: r"D:/repos/zootools_pro",
                   DESCRIPTION_KEY: "The lighting tools for Zoo Tools Pro"}
zoo_controls_joints_dict = {PACKAGE_NAME_KEY: "zoo_controls_joints",
                            NICE_NAME_KEY: "Zoo Controls And Joints",
                            VENDOR_KEY: VENDOR_TYPE_ZOO,
                            ACTIVE_KEY: "True",
                            ROOT_PATH_KEY: r"D:/repos/zootools_pro",
                            DESCRIPTION_KEY: "Control and Joint tools for Zoo Tools Pro"}
zoo_dev_utilities_dict = {PACKAGE_NAME_KEY: "zoo_dev_utilities",
                          NICE_NAME_KEY: "Zoo Developer Utilities",
                          VENDOR_KEY: VENDOR_TYPE_ZOO,
                          ACTIVE_KEY: "True",
                          ROOT_PATH_KEY: r"D:/repos/zootools_pro",
                          DESCRIPTION_KEY: "Code for Dev Utilities in Zoo Tools Pro"}
zoo_artist_palette_dict = {PACKAGE_NAME_KEY: "zoo_artist_palette",
                           NICE_NAME_KEY: "Zoo Artist Palette",
                           VENDOR_KEY: VENDOR_TYPE_ZOO,
                           ACTIVE_KEY: "True",
                           ROOT_PATH_KEY: r"D:/repos/zootools_pro",
                           DESCRIPTION_KEY: "Code for adding tools to Zoo Tools Pro"}
image_browser_dict = {PACKAGE_NAME_KEY: "zoo_image_browser",
                      NICE_NAME_KEY: "Zoo Image Browser",
                      VENDOR_KEY: VENDOR_TYPE_ZOO,
                      ACTIVE_KEY: "True",
                      ROOT_PATH_KEY: r"D:/repos/zootools_pro",
                      DESCRIPTION_KEY: "The image browser in Zoo Tools Pro"}
hotkeyeditor_dict = {PACKAGE_NAME_KEY: "zoo_hotkey_editor",
                     NICE_NAME_KEY: "Zoo Hotkey Editor",
                     VENDOR_KEY: VENDOR_TYPE_ZOO,
                     ACTIVE_KEY: "True",
                     ROOT_PATH_KEY: r"D:/repos/zootools_pro",
                     DESCRIPTION_KEY: "Code for the Hotkey Editor in Zoo Tools Pro"}
hive_dict = {PACKAGE_NAME_KEY: "zoo_hive",
             NICE_NAME_KEY: "Hive",
             VENDOR_KEY: VENDOR_TYPE_ZOO,
             ACTIVE_KEY: "True",
             ROOT_PATH_KEY: r"D:/repos/zootools_pro",
             DESCRIPTION_KEY: "Code for the Hive Autorigger (without the ui) in Zoo Tools Pro"}
hive_artist_ui_dict = {PACKAGE_NAME_KEY: "zoo_hive_artist_ui",
                       NICE_NAME_KEY: "Hive Artist UI",
                       VENDOR_KEY: VENDOR_TYPE_ZOO,
                       ACTIVE_KEY: "True",
                       ROOT_PATH_KEY: r"D:/repos/zootools_pro",
                       DESCRIPTION_KEY: "The UI for the Hive Autorigger in Zoo Tools Pro"}
my_custom_tools_dict = {PACKAGE_NAME_KEY: "zoo_example_custom_tools",
                        NICE_NAME_KEY: "Example Custom Tools",
                        VENDOR_KEY: VENDOR_TYPE_ZOO,
                        ACTIVE_KEY: "True",
                        ROOT_PATH_KEY: r"D:/repos/my_custom_tools",
                        DESCRIPTION_KEY: "Custom example tool repository demo for Zoo Tools Pro"}
# Custom/User Vendor Package Installs
your_project_a_dict = {PACKAGE_NAME_KEY: "your_project_a_tools",
                       NICE_NAME_KEY: "Your Project A Tools",
                       VENDOR_KEY: "Your Company",
                       ACTIVE_KEY: "True",
                       ROOT_PATH_KEY: r"D:/repos/your_project_a_tools",
                       DESCRIPTION_KEY: "A set of tools for your company that can be loaded/unloaded"}
your_project_b_dict = {PACKAGE_NAME_KEY: "your_project_b_tools",
                       NICE_NAME_KEY: "Your Project B Tools",
                       VENDOR_KEY: "Your Company",
                       ACTIVE_KEY: "True",
                       ROOT_PATH_KEY: r"D:/repos/your_project_b_tools",
                       DESCRIPTION_KEY: "A set of tools for your company that can be loaded/unloaded"}
your_modelling_tools_dict = {PACKAGE_NAME_KEY: "your_modelling_tools",
                             NICE_NAME_KEY: "Your Modelling Tools",
                             VENDOR_KEY: "Your Company",
                             ACTIVE_KEY: "False",
                             ROOT_PATH_KEY: r"D:/repos/your_modelling_tools",
                             DESCRIPTION_KEY: "A set of tools for your modelling dept that can be loaded/unloaded"}
your_animation_tools_dict = {PACKAGE_NAME_KEY: "your_animation_tools",
                             NICE_NAME_KEY: "Your Animation Tools",
                             VENDOR_KEY: "Your Company",
                             ACTIVE_KEY: "False",
                             ROOT_PATH_KEY: r"D:/repos/your_animation_tools",
                             DESCRIPTION_KEY: "A set of tools for your animation dept that can be loaded/unloaded"}
an_old_project_dict = {PACKAGE_NAME_KEY: "an_old_project_tools",
                       NICE_NAME_KEY: "An Old Project Tools",
                       VENDOR_KEY: "Your Company",
                       ACTIVE_KEY: "False",
                       ROOT_PATH_KEY: r"D:/repos/an_old_project_tools",
                       DESCRIPTION_KEY: "A set of tools for an old project that can be loaded/unloaded"}

PACKAGE_LIST = [zoocore_dict, zoocore_maya_dict, zoocore_pro_dict, zootoolsets_pro_dict, zoo_utilities_tools_dict,
                zoo_light_suite, zoo_controls_joints_dict, zoo_dev_utilities_dict,
                zoo_artist_palette_dict, image_browser_dict, hotkeyeditor_dict, hive_dict, hive_artist_ui_dict,
                my_custom_tools_dict, your_project_a_dict, your_project_b_dict, your_modelling_tools_dict,
                your_animation_tools_dict, an_old_project_dict]

PACKAGE_NAME_DEFAULT = "new_package_name"
VENDOR_TXT_DEFAULT = "Your Name Or Company"
FOLDER_PATH_DEFAULT = r"D:/repos/zootools_pro"
DESCRIPTION_DEFAULT = "Description"


class ZooEnvironmentManager(object):  # return to toolsetwidget.ToolsetWidgetMaya
    id = "zooEnvironmentManager"
    uiData = {"label": "Zoo Environment Manager",
              "icon": "addDir",
              "tooltip": "Creates and manages Zoo Code Packages",
              "defaultActionDoubleClick": False
              }

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run"""
        self.theSelectedPkgDict = None
        self.propertiesMode = True  # this mode is True is Editing Properties, and False if Creating Packages
        self.allPackagesDictList = list(PACKAGE_LIST)  # make unique
        self.currentPackageDictList = list(PACKAGE_LIST)  # make unique

    def contents(self):
        """This method controls the simple/medium/advanced ui options"""
        return [self.initAdvancedWidget()]

    def initAdvancedWidget(self):
        """The advanced settings UI create
        """
        parent = QtWidgets.QWidget(parent=self)
        self.ui_advanced(parent=parent)
        return parent

    def postContentSetup(self):
        """Last of the initizialize code"""
        self.uiConnections()

    def ui_simple(self, parent):
        pass

    def ui_advanced(self, parent):
        """Creates the advanced UI for the toolset, UI Code goes here.

        In this case there is only one UI, but toolsets supports up to three UI modes (top right icon auto generates)

        :param parent: the parent widget
        :type parent: obj
        """
        self.parent = parent
        # Main Layout
        mainLayout = elements.vBoxLayout(parent, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)

        showFilterComboLayout = elements.hBoxLayout(parent, margins=(0, 0, 0, 0), spacing=uic.SLRG)
        # Filter Combo
        toolTip = ""
        self.comboList = ["All Packages", "User Or Third Party", "Zoo Tools Pro Official"]
        self.filterCombo = elements.ComboBoxRegular("Filter By", self.comboList, labelRatio=1, boxRatio=2,
                                                    toolTip=toolTip)
        showFilterComboLayout.addWidget(self.filterCombo)

        # Radio buttons for Active (hidden)
        radioNameList = ["Activated/Deactivated", "Activated", "Deactivated"]
        radioToolTipList = ["Shows all activated and deactivated code packages",
                            "Shows only the activated code packages",
                            "Shows only the deactivated code packages"]
        self.activeRadioWidget = elements.RadioButtonGroup(radioList=radioNameList, toolTipList=radioToolTipList,
                                                           default=0, parent=parent)
        self.activeRadioWidget.setHidden(True)  # this is hidden as won't be used.

        # table layout
        self.table = QtWidgets.QTableWidget(0, 2, parent)  # row, column, parent. Rows set later in populate
        self.table.setStyleSheet("QHeaderView::section:horizontal {margin-left: 20; margin-right: 30")
        self.columnLabels = ["Zoo Code Packages"]
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().resizeSection(0, utils.dpiScale(160))
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setHorizontalHeaderLabels(["Package Name", r"Vendor/Creator"])
        self.table.setMinimumHeight(utils.dpiScale(450))
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)  # don't edit the text on double click
        self.table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)

        # manage layout
        manageLayout = elements.hBoxLayout(parent, margins=(0, 0, 0, 0), spacing=uic.SREG)
        toolTip = "Add a new code package"
        self.openCreatePackageBtn = elements.styledButton("Create New Package", "plus", parent, toolTip)
        toolTip = "Edit a code package's properties"
        self.editPackageBtn = elements.styledButton("Edit", "editText", parent, toolTip)
        toolTip = "Delete a code package"
        self.deletePackageBtn = elements.styledButton("", "trash", parent, toolTip, maxWidth=uic.BTN_W_ICN_LRG,
                                                      minWidth=uic.BTN_W_ICN_LRG)
        toolTip = "Menu Options..."
        self.menuPackageBtn = elements.styledButton("", "menudots", parent, toolTip, maxWidth=uic.BTN_W_ICN_LRG,
                                                    minWidth=uic.BTN_W_ICN_LRG, style=uic.BTN_TRANSPARENT_BG)
        self.menuPackageBtn.setHidden(True)  # is hidden but should be a self.menuBtn anyway

        manageLayout.addWidget(self.menuPackageBtn, 1)
        manageLayout.addWidget(self.openCreatePackageBtn, 4)
        manageLayout.addWidget(self.editPackageBtn, 2)
        manageLayout.addWidget(self.deletePackageBtn, 1)

        # build main layout
        mainLayout.addLayout(showFilterComboLayout)
        mainLayout.addWidget(self.activeRadioWidget)
        mainLayout.addWidget(self.table)
        mainLayout.addItem(elements.Spacer(0, 5))  # width, height
        mainLayout.addItem(elements.Spacer(0, 5))  # width, height
        mainLayout.addLayout(manageLayout)

        # create the table contents, rows and columns
        self.populatePackageTable()

        # add the properties section of the ui
        self.ui_properties(parent)
        mainLayout.addItem(elements.Spacer(0, 10))  # width, height
        mainLayout.addWidget(self.propertiesContainer)

    def ui_properties(self, parent):
        """The popup properties UI embedded window for both "Create New Package" and "Edit Properties"

        The same UI is used for both modes with changes in:
            - self.setCreatePropertiesWidgets()
            - self.updatePropertiesWidgetsFromDict()

        :param parent: the parent widget
        :type parent: Qt.object
        """
        toolTip = "Close this embedded window"
        self.hidePropertiesBtn = elements.styledButton("", "closeX", self.parent, toolTip,
                                                       maxWidth=uic.BTN_W_ICN_SML, minWidth=uic.BTN_W_ICN_SML,
                                                       style=uic.BTN_TRANSPARENT_BG)
        self.propertiesContainer = elements.EmbeddedWindow(parent, "CREATE NEW PACKAGE",
                                                           closeButton=self.hidePropertiesBtn)
        self.propertiesLayout = self.propertiesContainer.getLayout()
        self.propertiesLbl = self.propertiesContainer.getTitleLbl()

        # Package Name Section
        toolTip = ""
        self.packageNameTxt = elements.StringEdit("Package Name", editPlaceholder="new_package_name", toolTip=toolTip,
                                                  labelRatio=4,
                                                  editRatio=10, parent=parent)

        # Vendor Type (combo) and hidden active checkbox
        vendorActiveLayout = elements.hBoxLayout(parent, margins=(0, 0, 0, 0), spacing=uic.SLRG)
        toolTip = ""
        self.vendorTxt = elements.StringEdit("Vendor/Creator", editPlaceholder="Your Name Or Company", toolTip=toolTip,
                                             labelRatio=4, editRatio=10, parent=parent)
        # active checkbox (hidden and not used)
        toolTip = ""
        self.activeChkBx = elements.CheckBoxRegular(label="Active", checked=True, toolTip=toolTip, parent=parent)
        self.activeChkBx.setHidden(True)
        vendorActiveLayout.addWidget(self.vendorTxt)
        vendorActiveLayout.addWidget(self.activeChkBx)

        # Directory path
        directoryPathLayout = elements.hBoxLayout(parent, margins=(0, 0, 0, 0), spacing=uic.SREG)
        toolTip = ""
        self.directoryPathLbl = elements.Label("Directory Path", parent, toolTip=toolTip)
        directoryPathLayoutR = elements.hBoxLayout(parent, margins=(0, 0, 0, 0), spacing=uic.SREG)
        self.directoryPathTxt = elements.LineEdit(text=r"D:/repos/zootools_pro", toolTip=toolTip, parent=parent)
        toolTip = ""
        self.browseBtn = elements.styledButton("...", "", parent, toolTip, maxWidth=uic.BTN_W_ICN_REG,
                                               minWidth=uic.BTN_W_ICN_REG)
        directoryPathLayoutR.addWidget(self.directoryPathTxt, 4)
        directoryPathLayoutR.addWidget(self.browseBtn, 1)
        directoryPathLayout.addWidget(self.directoryPathLbl, 4)
        directoryPathLayout.addLayout(directoryPathLayoutR, 10)

        # Description text
        toolTip = ""
        self.descriptionTxt = elements.TextEdit(placeholderText="Description...", parent=parent, toolTip=toolTip,
                                                minimumHeight=50, maximumHeight=50)
        saveHideBtnLayout = elements.hBoxLayout(parent, margins=(0, 0, 0, 0), spacing=uic.SLRG)

        # Create and Update Buttons, only one button shows at a time
        toolTip = ""
        self.createNewPackageBtn = elements.styledButton("Create New Package", "saveZooScene", parent, toolTip)
        toolTip = ""
        self.updatePropertiesSaveBtn = elements.styledButton("Update Package Properties", "saveZooScene", parent,
                                                             toolTip)
        saveHideBtnLayout.addWidget(self.createNewPackageBtn)
        saveHideBtnLayout.addWidget(self.updatePropertiesSaveBtn)

        self.propertiesLayout.addWidget(self.packageNameTxt)
        self.propertiesLayout.addLayout(vendorActiveLayout)
        self.propertiesLayout.addLayout(directoryPathLayout)
        self.propertiesLayout.addWidget(self.descriptionTxt)
        self.propertiesLayout.addItem(elements.Spacer(0, 5))  # width, height
        self.propertiesLayout.addLayout(saveHideBtnLayout)

    def ui_deleteWindowPopup(self, deletedPackageName, fullDirectoryPath):
        message = "Do you really want to delete the folder \n\n'{}' \n\nThis will permanently delete the directory " \
                  "and all of it's contents from disk...\n\n{}".format(deletedPackageName, fullDirectoryPath)
        # Delete Popup Window
        okPressed = elements.MessageBox_ok(windowName="Delete This Package?", parent=None, message=message)
        return okPressed

    def ui_createWindowPopup(self, fullDirectoryPath):
        message = "Are you sure you want to create a new Zoo Code Package with the following path?\n\n" \
                  "{}".format(fullDirectoryPath)
        okPressed = elements.MessageBox_ok(windowName="Move/Rename Package Directory", parent=None,
                                           message=message)
        return okPressed

    def ui_moveRenamePackage(self, oldFullPath, fullDirectoryPath):
        message = "Are you sure you want to move\\rename this package directory?\n\n" \
                  "Old Directory:\n\n" \
                  "{}\n\n" \
                  "New Directory:\n\n" \
                  "{}".format(oldFullPath, fullDirectoryPath)
        okPressed = elements.MessageBox_ok(windowName="Move/Rename Package Directory", parent=None,
                                           message=message)
        return okPressed

    # filter methods

    def getPackageDict_zoo(self):
        """return a list of package dicts that are by the vendor creator VENDOR_TYPE_ZOO ("ZooToolsPro")

        :return packageDictList: A list of package dictionaries now filtered
        :rtype packageDictList: list(dict)
        """
        packageDictList = list()
        for packageDict in self.allPackagesDictList:
            if packageDict[VENDOR_KEY] == VENDOR_TYPE_ZOO:
                packageDictList.append(packageDict)
        return packageDictList

    def getPackageDict_customThirdParty(self):
        """return a list of User/Third Party package dicts, NOT by the vendor creator VENDOR_TYPE_ZOO ("ZooToolsPro")

        :return packageDictList: A list of package dictionaries now filtered
        :rtype packageDictList: list(dict)
        """
        packageDictList = list()
        for packageDict in self.allPackagesDictList:
            if packageDict[VENDOR_KEY] != VENDOR_TYPE_ZOO:
                packageDictList.append(packageDict)
        return packageDictList

    # return key values from dict lists

    def getPackageNameList(self, packageDictList):
        """Returns a list of package names from the given packageDictList

        :param packageDictList: a list of package dictionaries
        :type packageDictList: list(dict)
        :return packageVendorList: a list of package names extracted from the packageDictList
        :rtype packageVendorList: list(str)
        """
        packageNameList = list()
        for packageDict in packageDictList:
            packageNameList.append(packageDict[PACKAGE_NAME_KEY])
        return packageNameList

    def getPackageActiveList(self, packageDictList):
        """**Returns a list of "active" "True"/"False" strings from the given packageDictList

        **Not in use, this is disabled in the current UI

        :param packageDictList: a list of package dictionaries
        :type packageDictList: list(dict)
        :return packageVendorList: a list of "active" "True"/"False" strings extracted from the packageDictList
        :rtype packageVendorList: list(str)
        """
        packageActiveList = list()
        for packageDict in packageDictList:
            packageActiveList.append(packageDict[ACTIVE_KEY])
        return packageActiveList

    def getPackageVendorList(self, packageDictList):
        """Returns a list of vendor/creator names from the given packageDictList

        :param packageDictList: a list of package dictionaries
        :type packageDictList: list(dict)
        :return packageVendorList: a list of vendor/creator names extracted from the packageDictList
        :rtype packageVendorList: list(str)
        """
        packageVendorList = list()
        for packageDict in packageDictList:
            packageVendorList.append(packageDict[VENDOR_KEY])
        return packageVendorList

    # get Dict From UI filters

    def getDictFromComboBox(self):
        """Returns a list of dictionaries from all dictionaries, filtered by the combo box options:

            - All
            - Custom/Third Party Creators
            - ZooToolsPro

        :return packageDictList: a list of package dictionaries now filtered
        :rtype packageDictList: list(dict)
        """
        comboValue = self.filterCombo.value()
        if comboValue == self.comboList[0]:  # "All"
            return self.allPackagesDictList
        elif comboValue == self.comboList[1]:  # "Custom/Third Party"
            return self.getPackageDict_customThirdParty()
        else:  # "Zoo Tools Official"
            return self.getPackageDict_zoo()

    def getPackageDict_activated(self, packageDictList):
        """**returns a list of package dictionaries filtered by the radio btn "active state" ticked

        **This isn't in used and is hidden from the UI for future use

        :param packageDictList: a list of package dictionaries
        :type packageDictList: list(dict)
        :return packageFilteredDictList: list of package dictionaries now with only activated or deactivated states
        :rtype packageFilteredDictList: list(dict)
        """
        activeIndex = self.activeRadioWidget.checkedIndex()  # the radio btn index
        if activeIndex == 0:
            return packageDictList
        elif activeIndex == 1:  # if radio button active index = "True"
            checkActiveState = "True"
        else:  # else radio button active index = "False"
            checkActiveState = "False"
        packageFilteredDictList = list()
        for packageDict in packageDictList:
            if packageDict[ACTIVE_KEY] == checkActiveState:
                packageFilteredDictList.append(packageDict)
        return packageFilteredDictList

    def getDictFromComboBoxAndRadio(self):
        """**Filters from both the Active state radio check boxes, and the creator combo box options

        **Not in use as the Active state radio check boxes are hidden

        :return packageDictList: a list of package dictionaries now filtered
        :rtype packageDictList: list(dict)
        """
        packageDictList = self.getDictFromComboBox()  # returns from combobox settings
        packageDictList = self.getPackageDict_activated(packageDictList)  # then filters from the radio btn
        return packageDictList

    #  Build the table

    def populatePackageTable(self):
        """Creates the table rows with the package info, will also refresh/repopulate if table exists already
        """
        packageDictList = self.getDictFromComboBox()  # only look from combo box as active will be hidden
        packageNameList = self.getPackageNameList(packageDictList)
        packageVendorList = self.getPackageVendorList(packageDictList)
        self.clearTable()
        self.currentPackageDictList = list(packageDictList)  # add to current loaded dicts so we can extract data
        self.table.setRowCount(len(packageNameList))
        for i, packageName in enumerate(packageNameList):  # build the new rows/columns
            self.table.setItem(i, 0, QtWidgets.QTableWidgetItem("  {}  ".format(packageName)))
            self.table.setItem(i, 1, QtWidgets.QTableWidgetItem("  {}  ".format(packageVendorList[i])))

    def clearTable(self):
        """Clears the table removing all rows and contents
        """
        listLength = len(self.currentPackageDictList)
        for i, package in enumerate(self.currentPackageDictList):  # reverse the list
            self.table.removeRow(listLength - i - 1)  # remove row in reverse ending in 0

    # Update properties sections with widget values

    def disablePropertiesWidgets(self, disableBool):
        """sets the disable mode for widgets

        :param disableBool: True will disable the widgets, False will enable
        :type disableBool: bool
        """
        self.packageNameTxt.setDisabled(disableBool)
        self.directoryPathTxt.setDisabled(disableBool)
        self.vendorTxt.setDisabled(disableBool)
        self.descriptionTxt.setDisabled(disableBool)

    def updatePropertiesWidgetsFromDict(self, rowNumber):
        """Updates the Edit Properties widgets, including their titles and the Update Package button too.

        Also checks for admin mode and will disable widgets if not Admin and the packages are by ZooToolsPro

        :param rowNumber: the current row number selected, will match the self.currentPackageDictList[rowNumber]
        :type rowNumber: int
        """
        self.theSelectedPkgDict = self.currentPackageDictList[rowNumber]
        self.propertiesLbl.setText("EDIT PROPERTIES - ({})".format(self.theSelectedPkgDict[PACKAGE_NAME_KEY]))
        self.packageNameTxt.setText(self.theSelectedPkgDict[PACKAGE_NAME_KEY])
        self.directoryPathTxt.setText(self.theSelectedPkgDict[ROOT_PATH_KEY])
        self.vendorTxt.setText(self.theSelectedPkgDict[VENDOR_KEY])
        self.descriptionTxt.setText(self.theSelectedPkgDict[DESCRIPTION_KEY])
        self.disablePropertiesWidgets(False)
        if self.theSelectedPkgDict[VENDOR_KEY] == VENDOR_TYPE_ZOO:  # if zoo disable widgets so they can't be changed
            if os.environ["ZOO_ADMIN"] != "1":  # only disable if not in Zoo Admin mode
                self.disablePropertiesWidgets(True)

    def setCreatePropertiesWidgets(self):
        """Resets "Create Package" widgets to defaults
        """
        self.disablePropertiesWidgets(False)
        self.packageNameTxt.setText("")
        self.packageNameTxt.edit.setPlaceholderText(PACKAGE_NAME_DEFAULT)
        self.directoryPathTxt.setText(FOLDER_PATH_DEFAULT)
        self.vendorTxt.setText("")
        self.vendorTxt.edit.setPlaceholderText(VENDOR_TXT_DEFAULT)
        self.descriptionTxt.setText("")
        self.descriptionTxt.setPlaceholderText(DESCRIPTION_DEFAULT)

    # Hide/show

    def hideProperties(self):
        """Hides the properties widget both for "Create New Package" And "Edit Properties"
        """
        self.propertiesContainer.setHidden(True)

    def showCreateNewPackage(self):
        """Resets the properties area to the "Create Package" mode

        Changes widget defaults, titles and the Create New Package btn
        """
        self.propertiesMode = False
        self.table.setMinimumHeight(utils.dpiScale(50))
        self.propertiesLbl.setText("CREATE NEW PACKAGE")
        self.createNewPackageBtn.setHidden(False)
        self.setCreatePropertiesWidgets()
        self.updatePropertiesSaveBtn.setHidden(True)
        self.propertiesContainer.setHidden(False)

    def showEditProperties(self, row=None):
        """Updates the Edit Properties widgets, including their titles and the Update Package button too.
        """
        self.propertiesMode = True
        if row is None:
            try:
                row = sorted(set(index.row() for index in self.table.selectedIndexes()))[0]
            except IndexError:
                om2.MGlobal.displayWarning("Nothing is selected in the package table. Please select a package.")
                return
        self.table.setMinimumHeight(utils.dpiScale(50))
        self.createNewPackageBtn.setHidden(True)
        self.updatePropertiesWidgetsFromDict(row)
        self.updatePropertiesSaveBtn.setHidden(False)
        self.propertiesContainer.setHidden(False)

    # File Manager
    def zooAdminMessage(self):
        """Checks if Zoo Tools Pro is in the Administrator mode, if it is reports and message and returns True

        :return zooAdminMode: If Zoo Tools Pro is in admin mode returns True, if not then False
        :rtype zooAdminMode: bool
        """
        if os.environ["ZOO_ADMIN"] != "1":
            om2.MGlobal.displayWarning("Cannot be changed without being a Zoo Tools Pro Administrator")
            return True
        return False

    def setDirectoryPath(self):
        """Sets the directory path of the self.directoryPathTxt widget only, does not affect packages until saved
        """
        if self.propertiesMode:
            if self.theSelectedPkgDict[VENDOR_KEY] == VENDOR_TYPE_ZOO:
                if self.zooAdminMessage():
                    return
        directorypath = elements.FileDialog_directory(windowName="Package Directory Root Folder", parent=self.parent,
                                                      defaultPath=DEFAULT_DIRECTORY_PATH)
        if directorypath:
            self.directoryPathTxt.setText(directorypath)

    # Create Package, Update Properties, Delete Package
    def updatePkgNamePath(self, currentDict, pkgName, pkgPath, fullDirectoryPath):
        """Will move/rename the current package location on disk and returns the updated dictionary

        Also warns the user with a QtPopup ok/cancel window

        :param currentDict: is the dictionary to update, the old data is in here
        :type currentDict: dict
        :param pkgName: the new folder name of the new package
        :type pkgName: str
        :param pkgPath: the new root path of the package, not including the folder name
        :type pkgPath: str
        :param fullDirectoryPath: the new full path including the package folder
        :type fullDirectoryPath: str
        :return currentDict: The package dictionary now updated
        :rtype currentDict: dict
        """
        # check that fullDirectoryPath is unique and that it doesn't exist
        oldFullPath = os.path.join(currentDict[ROOT_PATH_KEY], currentDict[PACKAGE_NAME_KEY])
        currentDict[PACKAGE_NAME_KEY] = pkgName
        currentDict[ROOT_PATH_KEY] = pkgPath
        okPressed = self.ui_moveRenamePackage(oldFullPath, fullDirectoryPath)  # popup confrim window ok/cancel
        if not okPressed:
            om2.MGlobal.displayInfo("Directory moved/rename cancelled")
            return
        # do the directory and file changes here
        om2.MGlobal.displayInfo("Directory moved/renamed. Old Path: {} New Path: {}".format(oldFullPath,
                                                                                            fullDirectoryPath))
        return currentDict

    def updatePkgVendor(self, currentDict, pkgVendor):
        currentDict[VENDOR_KEY] = pkgVendor
        # do the file changes here
        return currentDict

    def updatePkDescription(self, currentDict, pkgDescription):
        currentDict[DESCRIPTION_KEY] = pkgDescription
        # do the file changes here
        return currentDict

    def updatePackageInfo(self):
        """"Update Package Properties" button pressed. Updates/saves the current settings
        """
        if self.propertiesMode:
            if self.theSelectedPkgDict[VENDOR_KEY] == VENDOR_TYPE_ZOO:
                if self.zooAdminMessage():
                    return
        try:
            row = sorted(set(index.row() for index in self.table.selectedIndexes()))[0]
        except IndexError:
            om2.MGlobal.displayWarning("Nothing is selected in the package table. Please select a package.")
            return
        pkgName = self.packageNameTxt.text()
        pkgPath = self.directoryPathTxt.text()
        fullDirectoryPath = os.path.join(pkgPath, pkgName)
        pkgVendor = self.vendorTxt.text()
        pkgDescription = self.descriptionTxt.toPlainText()
        # check the changes by comparing to the current dict
        currentDict = self.currentPackageDictList[row]
        updated = False
        if pkgName != currentDict[PACKAGE_NAME_KEY] or pkgPath != currentDict[ROOT_PATH_KEY]:
            currentDict = self.updatePkgNamePath(currentDict, pkgName, pkgPath, fullDirectoryPath)
            updated = True
        if pkgVendor != currentDict[VENDOR_KEY]:
            currentDict = self.updatePkgVendor(currentDict, pkgVendor)
            updated = True
        if pkgDescription != currentDict[DESCRIPTION_KEY]:
            currentDict = self.updatePkDescription(currentDict, pkgDescription)
            updated = True
        if not updated:
            om2.MGlobal.displayWarning("No package properties have changed.  Please change a package property.")
            return
        oldPkgName = currentDict[PACKAGE_NAME_KEY]
        for i, pkgDict in enumerate(self.allPackagesDictList):  # update both the dictionaries
            if oldPkgName == pkgName:
                self.currentPackageDictList[row] = list(currentDict)  # make unique
                self.allPackagesDictList[i][row] = list(currentDict)  # make unique
                self.populatePackageTable()  # recreate the table to account for potential changes
                om2.MGlobal.displayInfo("Success: Package properties hae been updated {}".format(fullDirectoryPath))
                return
        else:
            om2.MGlobal.displayError("Could not find package dictionary to change.")

    def createPackage(self):
        pkgName = self.packageNameTxt.text()
        pkgPath = self.directoryPathTxt.text()
        fullDirectoryPath = os.path.join(pkgPath, pkgName)
        pkgVendor = self.vendorTxt.text()
        pkgDescription = self.descriptionTxt.toPlainText()
        if not pkgName or not pkgPath:
            om2.MGlobal.displayWarning("Package needs a name and a path to be created")
            return
        okPressed = self.ui_createWindowPopup(fullDirectoryPath)  # confirm window popup ok/cancel
        if not okPressed:
            om2.MGlobal.displayInfo("Create package cancelled")
            return
        newDict = {PACKAGE_NAME_KEY: pkgName,
                   VENDOR_KEY: pkgVendor,
                   ROOT_PATH_KEY: pkgPath,
                   DESCRIPTION_KEY: pkgDescription}
        # create directory and files code goes here
        self.allPackagesDictList.append(newDict)
        om2.MGlobal.displayInfo("New zoo code package created {}".format(fullDirectoryPath))
        self.populatePackageTable()

    def deletePackageFromDisk(self, row, fullDirectoryPath):
        """Code for deleting a package from disk and in the UI given the row selection and fullPathDirectory

        Called by self.deletePackage()

        :param row: The selected row selection from the table, to be deleted
        :type row: int
        :param fullDirectoryPath: the full path of the directory to be deleted
        :type fullDirectoryPath: str
        :return directoryDeleted: was the directory deleted?
        :rtype directoryDeleted: bool
        """
        packageName = (self.currentPackageDictList[row])[PACKAGE_NAME_KEY]
        for i, packageDict in enumerate(self.allPackagesDictList):
            if packageDict[PACKAGE_NAME_KEY] == packageName:
                del self.allPackagesDictList[i]  # delete the entry in the all list
                del self.currentPackageDictList[row]  # delete entry in the current list
                self.populatePackageTable()  # update the table
                # do the disk delete here
                om2.MGlobal.displayInfo("Success: This package directory was deleted {}".format(fullDirectoryPath))
                return True
        om2.MGlobal.displayError("This package cannot be found in the currentPackageDictList and allPackagesDictList")
        return False

    def deletePackage(self):
        """Method for when the delete button is pressed, will open a popup and delete the first selected package
        """
        try:
            row = sorted(set(index.row() for index in self.table.selectedIndexes()))[0]
        except IndexError:
            om2.MGlobal.displayWarning("Nothing is selected in the package table. Please select a package.")
            return
        if (self.currentPackageDictList[row])[VENDOR_KEY] == VENDOR_TYPE_ZOO:
            if self.zooAdminMessage():
                return
        deletedPackageName = (self.currentPackageDictList[row])[PACKAGE_NAME_KEY]
        directoryPath = (self.currentPackageDictList[row])[ROOT_PATH_KEY]
        fullDirectoryPath = os.path.join(directoryPath, deletedPackageName)
        okPressed = self.ui_deleteWindowPopup(deletedPackageName, fullDirectoryPath)  # popup window ok/cancel
        if okPressed:
            self.deletePackageFromDisk(row, fullDirectoryPath)
            return
        om2.MGlobal.displayInfo("Remove Directory Skipped")

    # Connections

    def uiConnections(self):
        """UI interaction connections
        """
        self.filterCombo.itemChanged.connect(self.populatePackageTable)
        self.table.currentCellChanged.connect(self.showEditProperties)
        # buttons
        self.openCreatePackageBtn.clicked.connect(self.showCreateNewPackage)
        self.editPackageBtn.clicked.connect(self.showEditProperties)
        self.browseBtn.clicked.connect(self.setDirectoryPath)
        self.updatePropertiesSaveBtn.clicked.connect(self.updatePackageInfo)
        self.createNewPackageBtn.clicked.connect(self.createPackage)
        self.deletePackageBtn.clicked.connect(self.deletePackage)
        # self.activeRadioWidget.toggled.connect(self.populatePackageTable)  # disabled for later
