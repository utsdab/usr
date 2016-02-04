"""
V 1.0
Tractor Submit from Maya - designed to integrate into maya UI
By Matt Gidney - mgidney@gmail.com

In maya run this at the moment....

import sys
sys.path.append("/Users/Shared/UTS_Dev/gitRepositories/utsdab/usr")

from software.maya.utils import tractor_submit_maya_UI
reload(tractor_submit_maya_UI)
tractor_submit_maya_UI.create()

"""

# -------------------------------------------------------------------------------------------------------------------- #
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)5.5s \t%(filename)s as %(name)s \t%(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)
# -------------------------------------------------------------------------------------------------------------------- #

import PySide.QtCore as qc
import PySide.QtGui as qg
import sys
import os
from software.renderfarm.dabtractor.factories import user_factory as ufac
from software.renderfarm.dabtractor.factories import interface_factory as ifac
from software.renderfarm.dabtractor.factories import environment_factory as proj

from functools import partial

try:
    import maya.cmds  as mc
    import pymel.core as pm
    import shiboken
    import maya.OpenMayaUI as mui
except Exception,err:
    logger.warn("No maya import {} presuming from a shell".format(err))

# -------------------------------------------------------------------------------------------------------------------- #

# Global variable to store the UI status, if it's open or closed
tractor_submit_dialog = None

# -------------------------------------------------------------------------------------------------------------------- #
class TractorSubmit(qg.QDialog):
    def __init__(self):
        super(TractorSubmit,self).__init__()
        logger.info("TractorSubmit")
        self.setWindowTitle('UTS_FARM_SUBMIT')
        self.setObjectName('UTS_FARM_SUBMIT')
        self.setWindowFlags(qc.Qt.WindowStaysOnTopHint)
        self.main_widget = TractorSubmitWidget()
        self.setLayout(qg.QVBoxLayout())
        self.setFixedWidth(330)
        # self.setFixedWidth(314)
        self.setMinimumHeight(750)
        self.scroll_area=qg.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFocusPolicy(qc.Qt.NoFocus)
        self.layout().addWidget(self.scroll_area)
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(5,5,5,5)
        self.layout().addWidget(self.main_widget)
        self.scroll_area.setWidget(self.main_widget)
        self._dock_widget = self._dock_name = None

    def connectDockWidget(self, dock_name, dock_widget):
        logger.info("connect {} {}".format(dock_name,dock_widget))
        self._dock_widget = dock_widget
        self._dock_name   = dock_name

    def close(self):
        logger.info("close")
        if self._dock_widget:
            mc.deleteUI(self._dock_name)
        else:
            qg.QDialog.close(self)

        self._dock_widget = self._dock_name = None

# -------------------------------------------------------------------------------------------------------------------- #
class FeedbackWidget(qg.QWidget):
    def __init__(self):
        super(FeedbackWidget, self).__init__()
        logger.info("FeedbacktWidget")
        self.setLayout(qg.QVBoxLayout())
        self.splitter = ifac.Splitter("FEEDBACK")
        self.layout().addWidget(self.splitter)
        self.widget = ifac.FeedbackWidget()
        self.widget.append("Farm Submit Interface")
        self.layout().addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().addWidget(self.splitter)
        self.layout().addWidget(self.widget)

    def append(self,_text):
        self.widget.append(_text)

# -------------------------------------------------------------------------------------------------------------------- #
class TractorSubmitWidget(qg.QFrame):
    def __init__(self):
        super(TractorSubmitWidget, self).__init__()

        logger.info("TractorSubmitWidget")
        self.setFrameStyle(qg.QFrame.Panel | qg.QFrame.Raised)
        self.setSizePolicy(qg.QSizePolicy.Minimum,
                           qg.QSizePolicy.Fixed)

        self.setLayout(qg.QVBoxLayout())

        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().setAlignment(qc.Qt.AlignTop)

        self.feedback_widget = FeedbackWidget()

        # ------------------------------------------------------------------------------------ #
        # USER WIDGET
        self.user_widget = ifac.UserWidget()
        self.layout().addWidget(self.user_widget)

        # ------------------------------------------------------------------------------------ #
        # STACKED WIDGET
        self.stacked_layout = qg.QStackedLayout()
        self.layout().addLayout(self.stacked_layout)

        self.mode_splitter = ifac.Splitter("MODE")
        self.layout().addWidget(self.mode_splitter)

        self.grid_widget = qg.QWidget()
        self.grid_widget.setLayout(qg.QGridLayout())
        self.grid_widget.layout().setSpacing(0)
        self.grid_widget.layout().setContentsMargins(0,0,0,0)

        self.layout_1_bttn = qg.QPushButton('Maya')
        self.layout_2_bttn = qg.QPushButton('Mental Ray')
        self.layout_3_bttn = qg.QPushButton('Renderman')
        self.layout_4_bttn = qg.QPushButton('Bash Cmd')
        self.layout_5_bttn = qg.QPushButton('Nuke')
        self.layout_6_bttn = qg.QPushButton('Archive')

        self.grid_widget.layout().addWidget(self.layout_1_bttn,0,0)
        self.grid_widget.layout().addWidget(self.layout_2_bttn,0,1)
        self.grid_widget.layout().addWidget(self.layout_3_bttn,0,2)
        self.grid_widget.layout().addWidget(self.layout_4_bttn,1,0)
        self.grid_widget.layout().addWidget(self.layout_5_bttn,1,1)
        self.grid_widget.layout().addWidget(self.layout_6_bttn,1,2)

        self.layout().addWidget(self.grid_widget)

        self.maya_widget      = ifac.MayaJobWidget()
        self.mentalray_widget = ifac.MentalRayJobWidget()
        self.renderman_widget = ifac.RendermanJobWidget()
        self.bash_widget      = ifac.BashJobWidget()
        self.archive_widget   = ifac.ArchiveJobWidget()
        self.nuke_widget      = ifac.NukeJobWidget()
        self.tractor_widget   = ifac.TractorWidget()
        self.farmjob_widget   = ifac.FarmJobExtraWidget()

        self.stacked_layout.addWidget(self.maya_widget)
        self.stacked_layout.addWidget(self.mentalray_widget)
        self.stacked_layout.addWidget(self.renderman_widget)
        self.stacked_layout.addWidget(self.bash_widget)
        self.stacked_layout.addWidget(self.nuke_widget)
        self.stacked_layout.addWidget(self.archive_widget)

        self.layout_1_bttn.clicked.connect(partial(self.stacked_layout.setCurrentIndex, 0))
        self.layout_2_bttn.clicked.connect(partial(self.stacked_layout.setCurrentIndex, 1))
        self.layout_3_bttn.clicked.connect(partial(self.stacked_layout.setCurrentIndex, 2))
        self.layout_4_bttn.clicked.connect(partial(self.stacked_layout.setCurrentIndex, 3))
        self.layout_5_bttn.clicked.connect(partial(self.stacked_layout.setCurrentIndex, 4))
        self.layout_6_bttn.clicked.connect(partial(self.stacked_layout.setCurrentIndex, 5))

        # ------------------------------------------------------------------------------------ #
        # TRACTOR WIDGET

        self.tractor_widget= ifac.TractorWidget()
        self.layout().addWidget(self.tractor_widget)

        # ------------------------------------------------------------------------------------ #
        # FARM EXTRA WIDGET
        self.farmjob_widget= ifac.FarmJobExtraWidget()
        self.layout().addWidget(self.farmjob_widget)

        # ------------------------------------------------------------------------------------ #
        # SUBMIT WIDGET
        self.submit_widget= ifac.SubmitWidget()
        self.layout().addWidget(self.submit_widget)

        # ------------------------------------------------------------------------------------ #
        # FEEDBACK WIDGET
        # self.layout().addSpacerItem(qg.QSpacerItem(5,20,qg.QSizePolicy.Expanding))

        self.layout().addWidget(self.feedback_widget)

    def closeWidget(self):
        self.emit(qc.SIGNAL('CLOSE'), self)


# -------------------------------------------------------------------------------------------------------------------- #
def create(docked=True):
    global tractor_submit_dialog
    logging.info("create dialog tractor_submit_dialog")
    if tractor_submit_dialog is None:
        tractor_submit_dialog = TractorSubmit()

    if docked is True:
        ptr = mui.MQtUtil.mainWindow()
        main_window = shiboken.wrapInstance(long(ptr), qg.QWidget)

        tractor_submit_dialog.setParent(main_window)
        size = tractor_submit_dialog.size()

        name = mui.MQtUtil.fullName(long(shiboken.getCppPointer(tractor_submit_dialog)[0]))
        dock = mc.dockControl(
            allowedArea =['right', 'left'],
            area        = 'right',
            floating    = False,
            content     = name,
            width       = size.width(),
            height      = size.height(),
            label       = 'UTS_FARM_SUBMIT')

        widget      = mui.MQtUtil.findControl(dock)
        dock_widget = shiboken.wrapInstance(long(widget), qg.QWidget)
        tractor_submit_dialog.connectDockWidget(dock, dock_widget)
    else:
        tractor_submit_dialog.show()

# -------------------------------------------------------------------------------------------------------------------- #
def delete():
    logging.info("tractor_submit_dialog delete")
    global tractor_submit_dialog
    if tractor_submit_dialog:
        tractor_submit_dialog.close()
        tractor_submit_dialog = None

def getMayaWindow():
    """
    Get the main Maya window as a QtGui.QMainWindow instance
    @return: QtGui.QMainWindow instance of the top level Maya windows
    """
    ptr = mui.MQtUtil.mainWindow()
    if ptr is not None:
        return shiboken.wrapInstance(long(ptr), qg.QWidget)

# -------------------------------------------------------------------------------------------------------------------- #
def main():
    try:
        maya = getMayaWindow()
    except Exception,e:
        print e
    else:
        print "else"
    finally:
        print "finally"
    app = qg.QApplication(sys.argv)
    tractor_submit_dialog = TractorSubmit()
    tractor_submit_dialog.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()