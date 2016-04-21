"""
V 1.0
Tractor Submit from Maya - designed to integrate into maya UI
By Matt Gidney - mgidney@gmail.com

In maya run this at the moment....

import sys
sys.path.append("/Users/Shared/UTS_Dev/gitRepositories/utsdab/usr")

from software.maya.uts_tools import tractor_submit_maya_UI
tractor_submit_maya_UI.TractorSubmit().show()
tractor_submit_maya_UI.create()
tractor_submit_maya_UI.main()
tractor_submit_maya_UI.delete()

reload(tractor_submit_maya_UI)
reload(tractor_submit_maya_UI.ifac)

########  set up rms camera projector
from software.maya.uts_tools.prman import cam_proj_setup_ui
cam_proj_setup_ui.create_ui()

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
from software.renderfarm.dabtractor.factories import render_prman_factory as rmsfac
from software.renderfarm.dabtractor.factories import render_mr_factory as mrfac
from software.renderfarm.dabtractor.factories import render_nuke_factory as nukefac
from software.renderfarm.dabtractor.factories import command_factory as cmdfac
from software.renderfarm.dabtractor.factories import environment_factory as env

from functools import partial
import tractor.api.query as tq

# -------------------------------------------------------------------------------------------------------------------- #

# Global variable to store the UI status, if it's open or closed
TRACTOT_SUBMIT_DIALOG = None
MAYA_PRESENT = False
COL1 = "background-color:lightgrey;color:black"
COL2 = "background-color:lightgreen;color:darkblue"
VERSION = "0.99"
BUILD = "2016_04_16"

# -------------------------------------------------------------------------------------------------------------------- #
class TractorSubmit(qg.QDialog):
    def __init__(self,mayapresent=False):
        super(TractorSubmit,self).__init__()
        self.job=Job()
        self.job.mayapresent=mayapresent
        self.maya=None

        logger.info("TractorSubmit")
        if self.job.mayapresent:
            self.maya=Maya()
        else:
            logger.info("Maya NOT Present")

        ###########
        try:
            if not os.path.isdir(env.Environment().dabrender):
                raise("Cant find dabrender")
        except Exception,err:
            sys.exit(err)

        self.setWindowTitle('UTS FARM SUBMIT V{}_{}'.format(VERSION,BUILD))
        self.setObjectName('UTS_FARM_SUBMIT')
        self.setWindowFlags(qc.Qt.WindowStaysOnTopHint)
        self.main_widget = TractorSubmitWidget(self.job,self.maya)
        self.setLayout(qg.QVBoxLayout())
        self.setFixedWidth(350)
        self.setMinimumHeight(900)
        self.scroll_area = qg.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFocusPolicy(qc.Qt.NoFocus)
        self.layout().addWidget(self.scroll_area)
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(5, 5, 5, 5)
        self.layout().addWidget(self.main_widget)
        self.scroll_area.setWidget(self.main_widget)

class Maya(object):
    '''
    This is a sidecar like object that holds and examines data in the maya scene found
    '''
    def __init__(self):
        logger.info("Maya is Found")


# -------------------------------------------------------------------------------------------------------------------- #
class Job(env.Environment):
    def __init__(self):
        super(Job, self).__init__()
        # self.env=proj.Environment()
        # self.dabrender=self.env.dabrender
        self.usernumber = None
        self.username = None
        self.projectgroup = None
        self.outformat = None
        self.jobtitle = None
        self.startframe = None
        self.endframe = None
        self.byframe = None
        self.threads = None
        self.threadmemory = None
        self.email = None
        self.fb = None
        self.email = None
        self.options = None
        self.chunks = None
        self.startdirectory = None,
        self.bashcommand = None,
        self.bashoptions = None,

    def printme(self):
        logger.info("\n\n{:_^80}\n".format(" job attributes "))
        for i,key in enumerate(self.__dict__.keys()):
            logger.info("Job Attribute {} : {}={}".format( i, key, self.__dict__[key]))
        logger.info("\n\n{:_^80}\n".format(" job attributes "))

    def rmsvalidate(self):
        try:
            self.tractorjob=rmsfac.RenderPrman(
                 envdabrender=self.dabrender,
                 envtype=self.type,
                 envshow=self.show,
                 envproject=self.project,
                 envscene= self.scene,
                 mayaprojectpath=self.projectpath,
                 mayascenefilefullpath=self.scenefullpath,
                 mayaversion=self.mayaversion,
                 rendermanversion=self.rmanversion,
                 startframe=self.startframe,
                 endframe=self.endframe,
                 byframe=self.byframe,
                 projectgroup=self.projectgroup,
                 outformat=self.outformat,
                 resolution=self.resolution,
                 skipframes=0,
                 makeproxy=0,
                 options=self.options,
                 threadmemory=self.threadmemory,
                 threads=self.threads,
                 rendermaxsamples=self.rms_maxsamples,
                 ribgenchunks=int(self.chunks),
                 email=[]
            )
            self.tractorjob.build()
            self.tractorjob.validate()
            self.fb.write("Validate OK")
        except Exception,err:
            logger.warn("rsmvalidate error: {}".format(err))
            self.fb.write("Validate Fail: {}".format(err))

    def mayavalidate(self):
        if self.renderer == "mr":
            try:
                self.tractorjob=mrfac.RenderMentalray(
                    envdabrender=self.dabrender,
                    envtype=self.type,
                    envshow=self.show,
                    envproject=self.project,
                    envscene= self.scene,
                    mayaprojectpath=self.projectpath,
                    mayascenefilefullpath=self.scenefullpath,
                    mayaversion=self.mayaversion,
                    startframe=self.startframe,
                    endframe=self.endframe,
                    byframe=self.byframe,
                    framechunks=int(self.chunks),
                    projectgroup=self.projectgroup,
                    renderer="mr",
                    outformat="exr",
                    resolution=self.resolution,
                    skipframes=0,
                    makeproxy=0,
                    options="",
                    threads=self.threads,
                    threadmemory=self.threadmemory,
                    email=self.email
                )
                self.tractorjob.build()
                self.tractorjob.validate()
                self.fb.write("Validate OK")
            except Exception,err:
                logger.warn("mrvalidate error: {}".format(err))
                self.fb.write("Validate Fail: {}".format(err))
        else:
            logger.warn("not mr: ")

    def nukevalidate(self):
        try:
            self.tractorjob=nukefac.NukeJob(
                envdabrender=self.dabrender,
                envtype=self.type,
                envshow=self.show,
                envproject=self.project,
                envscene=self.scene,
                scenefullpath=self.scenefullpath,
                framechunks=int(self.chunks),
                startframe=int(self.startframe),
                endframe=int(self.endframe),
                byframe=int(self.byframe),
                options=self.options,
                version=self.version,
                threads=self.threads,
                threadmemory=self.threadmemory,
                projectgroup=self.projectgroup,
                email=[1, 0, 0, 0, 1, 0],
            )
            self.tractorjob.build()
            self.tractorjob.validate()
            self.fb.write("Validate OK")
        except Exception, err:
            logger.warn("nukevalidate error: {}".format(err))
            self.fb.write("Validate Fail: {}".format(err))

    def commandvalidate(self):
        try:
            self.tractorjob=cmdfac.Bash(
                command=self.bashcommand,
                projectgroup=self.projectgroup,
                email=[1, 0, 0, 0, 1, 0],
            )
            self.tractorjob.build()
            self.tractorjob.validate()
            self.fb.write("Validate OK")
        except Exception,err:
            logger.warn("Commandvalidate error: {}".format(err))
            self.fb.write("Validate Fail: {}".format(err))

    def spool(self):
        try:
            self.tractorjob.spool()
            self.fb.write("Spool OK")
        except Exception, err:
            logger.warn("Job spool error: {}".format(err))
            self.fb.write("Spool Fail: {}".format(err))


# -------------------------------------------------------------------------------------------------------------------- #
class TractorSubmitWidget(qg.QFrame):
    def __init__(self, job, maya=None):
        super(TractorSubmitWidget, self).__init__()
        logger.info("TractorSubmitWidget")
        self.job = job
        self.maya = maya
        self.setFrameStyle(qg.QFrame.Panel | qg.QFrame.Raised)
        self.setSizePolicy(qg.QSizePolicy.Minimum, qg.QSizePolicy.Fixed)
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setAlignment(qc.Qt.AlignTop)
        self.feedback_widget = ifac.FeedbackWidget()
        self.job.fb = self.feedback_widget
        if self.maya:
            self.job.fb.write("MAYA PRESENT")
        else:
            self.job.fb.write("MAYA NOT AVAILABLE")

        # ------------------------------------------------------------------------------------ #
        # USER WIDGET
        self.user_widget = ifac.UserWidget(self.job)
        self.layout().addWidget(self.user_widget)

        # COMMON OPTIONS
        self.common_widget = ifac.CommonRenderOptionsWidget(self.job)
        self.layout().addWidget(self.common_widget)

        # ------------------------------------------------------------------------------------ #
        # STACKED WIDGET
        self.stacked_layout = qg.QStackedLayout()
        self.layout().addLayout(self.stacked_layout)
        self.mode_splitter = ifac.Splitter("TRACTOR SUBMIT MODE")
        self.layout().addWidget(self.mode_splitter)
        self.grid_widget = qg.QWidget()
        self.grid_widget.setLayout(qg.QGridLayout())
        self.grid_widget.layout().setSpacing(12)
        self.grid_widget.layout().setContentsMargins(0, 0, 0, 0)

        self.layout_1_bttn = qg.QPushButton('Maya')
        self.layout_2_bttn = qg.QPushButton('Renderman')
        self.layout_3_bttn = qg.QPushButton('Nuke')
        self.layout_4_bttn = qg.QPushButton('Bash Cmd')
        self.layout_5_bttn = qg.QPushButton('Diagnostics')
        self.layout_6_bttn = qg.QPushButton('Bug Report')

        self.grid_widget.layout().addWidget(self.layout_1_bttn, 0, 0)
        self.grid_widget.layout().addWidget(self.layout_2_bttn, 0, 1)
        self.grid_widget.layout().addWidget(self.layout_3_bttn, 0, 2)
        self.grid_widget.layout().addWidget(self.layout_4_bttn, 1, 0)
        self.grid_widget.layout().addWidget(self.layout_5_bttn, 1, 1)
        self.grid_widget.layout().addWidget(self.layout_6_bttn, 1, 2)

        self.layout().addWidget(self.grid_widget)

        self.maya_widget      = ifac.MayaJobWidget(self.job)
        self.renderman_widget = ifac.RendermanJobWidget(self.job)
        self.bash_widget      = ifac.BashJobWidget(self.job)
        self.diag_widget      = ifac.DiagnosticJobWidget(self.job)
        self.nuke_widget      = ifac.NukeJobWidget(self.job)
        self.tractor_widget   = ifac.TractorWidget(self.job)
        self.farmjob_widget   = ifac.FarmJobExtraWidget(self.job)
        self.bug_widget       = ifac.BugWidget(self.job)

        self.stacked_layout.addWidget(self.maya_widget)
        self.stacked_layout.addWidget(self.renderman_widget)
        self.stacked_layout.addWidget(self.nuke_widget)
        self.stacked_layout.addWidget(self.bash_widget)
        self.stacked_layout.addWidget(self.diag_widget)
        self.stacked_layout.addWidget(self.bug_widget)

        self._stackchange(1)

        self.layout_1_bttn.clicked.connect(partial(self._stackchange, 0))
        self.layout_2_bttn.clicked.connect(partial(self._stackchange, 1))
        self.layout_3_bttn.clicked.connect(partial(self._stackchange, 2))
        self.layout_4_bttn.clicked.connect(partial(self._stackchange, 3))
        self.layout_5_bttn.clicked.connect(partial(self._stackchange, 4))
        self.layout_6_bttn.clicked.connect(partial(self._stackchange, 5))
        # self.layout_7_bttn.clicked.connect(partial(self._stackchange, 6))

        self.stacked_layout.setCurrentIndex(1)

        # TRACTOR WIDGET------------------------------------------------------------------------------------ #
        self.tractor_widget= ifac.TractorWidget(self.job)
        self.layout().addWidget(self.tractor_widget)
        # FARM EXTRA WIDGET ------------------------------------------------------------------------------------ #
        self.farmjob_widget= ifac.FarmJobExtraWidget(self.job)
        self.layout().addWidget(self.farmjob_widget)
        # SUBMIT WIDGET ------------------------------------------------------------------------------------ #
        self.submit_widget= ifac.SubmitWidget(self.job,self.feedback_widget)
        self.layout().addWidget(self.submit_widget)
        # FEEDBACK WIDGET------------------------------------------------------------------------------------ #
        self.layout().addWidget(self.feedback_widget)

    def closeWidget(self):
        self.emit(qc.SIGNAL('CLOSE'), self)

    def _stackchange(self,index):
        widgets=["maya", "rms", "nuke", "bash", "diag", "bug"]
        self.feedback_widget.write("MODE changed to {}".format(widgets[index]))
        self.job.mode=widgets[index]
        self.stacked_layout.setCurrentIndex(index)
        self._colourButtons(index)

    def _colourButtons(self, index):
        _default = "background-color:lightgrey;color:black"
        _pressed = "background-color:lightgreen;color:darkblue"
        self.layout_1_bttn.setStyleSheet(_default)
        self.layout_6_bttn.setStyleSheet(_default)
        self.layout_2_bttn.setStyleSheet(_default)
        self.layout_3_bttn.setStyleSheet(_default)
        self.layout_4_bttn.setStyleSheet(_default)
        self.layout_5_bttn.setStyleSheet(_default)

        if index == 0:
            self.layout_1_bttn.setStyleSheet(_pressed)
        elif index == 1:
            self.layout_2_bttn.setStyleSheet(_pressed)
        elif index == 2:
            self.layout_3_bttn.setStyleSheet(_pressed)
        elif index == 3:
            self.layout_4_bttn.setStyleSheet(_pressed)
        elif index == 4:
            self.layout_5_bttn.setStyleSheet(_pressed)
        elif index == 5:
            self.layout_6_bttn.setStyleSheet(_pressed)


def create():
    global tractor_submit_dialog
    if tractor_submit_dialog is None:
        tractor_submit_dialog = TractorSubmit(mayapresent=True)
    tractor_submit_dialog.show()
    tractor_submit_dialog.job.maya = True


def delete():
    global tractor_submit_dialog
    if tractor_submit_dialog is None:
        return

    tractor_submit_dialog.deleteLater()
    tractor_submit_dialog = None


# -------------------------------------------------------------------------------------------------------------------- #
def main():
    global tractor_submit_dialog
    try:
        import maya.cmds  as mc
        import pymel.core as pm
        logger.warn("Maya Found")
        create()

    except Exception,err:
        logger.warn("No maya found {} presuming from a shell".format(err))
        app = qg.QApplication(sys.argv)
        TRACTOR_SUBMIT_DIALOG = TractorSubmit(mayapresent=False)
        TRACTOR_SUBMIT_DIALOG.show()
        sys.exit(app.exec_())

    # finally:
    #     tractor_submit_dialog.job.printme()


if __name__ == '__main__':
    main()
