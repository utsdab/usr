# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/sbourgoing/dev/dpAutoRigSystem/dpAutoRigSystem/Extras/Ui/PoseReader.ui'
#
# Created: Mon Oct 26 16:05:36 2015
#      by: pyside-uic 0.2.14 running on PySide 1.2.0
#
# WARNING! All changes made in this file will be lost!

# from PySide import QtCore, QtGui
from PySide2 import QtGui, QtCore, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(613, 282)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setEnabled(True)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btnCreate = QtGui.QPushButton(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnCreate.sizePolicy().hasHeightForWidth())
        self.btnCreate.setSizePolicy(sizePolicy)
        self.btnCreate.setMaximumSize(QtCore.QSize(93, 27))
        self.btnCreate.setObjectName("btnCreate")
        self.horizontalLayout.addWidget(self.btnCreate)
        self.edtNewName = QtGui.QLineEdit(self.centralwidget)
        self.edtNewName.setObjectName("edtNewName")
        self.horizontalLayout.addWidget(self.edtNewName)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.tblData = QtGui.QTableWidget(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tblData.sizePolicy().hasHeightForWidth())
        self.tblData.setSizePolicy(sizePolicy)
        self.tblData.setFrameShape(QtGui.QFrame.StyledPanel)
        self.tblData.setFrameShadow(QtGui.QFrame.Sunken)
        self.tblData.setLineWidth(1)
        self.tblData.setMidLineWidth(0)
        self.tblData.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tblData.setAlternatingRowColors(False)
        self.tblData.setObjectName("tblData")
        self.tblData.setColumnCount(4)
        self.tblData.setRowCount(0)
        item = QtGui.QTableWidgetItem()
        self.tblData.setHorizontalHeaderItem(0, item)
        item = QtGui.QTableWidgetItem()
        self.tblData.setHorizontalHeaderItem(1, item)
        item = QtGui.QTableWidgetItem()
        self.tblData.setHorizontalHeaderItem(2, item)
        item = QtGui.QTableWidgetItem()
        self.tblData.setHorizontalHeaderItem(3, item)
        self.tblData.horizontalHeader().setVisible(True)
        self.tblData.horizontalHeader().setCascadingSectionResizes(True)
        self.tblData.horizontalHeader().setDefaultSectionSize(150)
        self.tblData.horizontalHeader().setStretchLastSection(True)
        self.tblData.verticalHeader().setVisible(False)
        self.verticalLayout.addWidget(self.tblData)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.btnRefresh = QtGui.QPushButton(self.centralwidget)
        self.btnRefresh.setObjectName("btnRefresh")
        self.horizontalLayout_3.addWidget(self.btnRefresh)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.btnCreate.setText(QtGui.QApplication.translate("MainWindow", "Create", None, QtGui.QApplication.UnicodeUTF8))
        self.tblData.setSortingEnabled(True)
        self.tblData.horizontalHeaderItem(0).setText(QtGui.QApplication.translate("MainWindow", "Name", None, QtGui.QApplication.UnicodeUTF8))
        self.tblData.horizontalHeaderItem(1).setText(QtGui.QApplication.translate("MainWindow", "Axis", None, QtGui.QApplication.UnicodeUTF8))
        self.tblData.horizontalHeaderItem(2).setText(QtGui.QApplication.translate("MainWindow", "Extract Axis Order", None, QtGui.QApplication.UnicodeUTF8))
        self.tblData.horizontalHeaderItem(3).setText(QtGui.QApplication.translate("MainWindow", "Angle", None, QtGui.QApplication.UnicodeUTF8))
        self.btnRefresh.setText(QtGui.QApplication.translate("MainWindow", "Refresh", None, QtGui.QApplication.UnicodeUTF8))

