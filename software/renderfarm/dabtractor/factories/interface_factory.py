import PySide.QtCore as qc
import PySide.QtGui as qg
import sys
import os
from software.renderfarm.dabtractor.factories import user_factory as ufac
from software.renderfarm.dabtractor.factories import utils_factory as utilfac
from software.renderfarm.dabtractor.factories import project_factory as proj

from functools import partial

# ##############################################################
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)5.5s \t%(filename)s as %(name)s \t%(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)
# ##############################################################

# -------------------------------------------------------------------------------------------------------------------- #
class UserWidget(qg.QWidget):
    def __init__(self):
        super(UserWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        self.layout().addWidget(Splitter("USER DETAILS"))
        
        self.usernumber_text_layout = qg.QHBoxLayout()
        self.usernumber_text_layout.setSpacing(0)
        self.usernumber_text_layout.setContentsMargins(0,0,0,0)
        self.usernumber_text_lb = qg.QLabel('$USER: {}'.format(self._getuser()))
        # self.usernumber_text_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.usernumber_text_layout.addWidget(self.usernumber_text_lb)
        self.layout().addLayout(self.usernumber_text_layout)

        self.username_text_layout = qg.QHBoxLayout()
        self.username_text_layout.setSpacing(0)
        self.username_text_layout.setContentsMargins(0,0,0,0)
        self.username_text_lb = qg.QLabel('$USERNAME: {}'.format(self._getusername(self._getuser())))
        # self.username_text_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.username_text_layout.addWidget(self.username_text_lb)

        self.layout().addLayout(self.username_text_layout)

    def _getusername(self,_user):
        u=ufac.Map()
        self.username=u.getusername(_user)
        return self.username

    def _getuser(self):
        self.usernumber=os.getenv("USER")
        return self.usernumber

# -------------------------------------------------------------------------------------------------------------------- #
class ProjectWidget(qg.QWidget):
    def __init__(self):
        super(ProjectWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        self.layout().addWidget(Splitter("ENVIRONMENT"))
        self.p= proj.Project()

        _width=90
        # ------------------------------------------------------------------------------------ #
        #  $DABRENDER
        self.dabrender_text_layout = qg.QHBoxLayout()
        self.dabrender_text_layout.setSpacing(0)
        self.dabrender_text_layout.setContentsMargins(0,0,0,0)
        
        self.dabrender_text_lb = qg.QLabel('$DABRENDER:')
        self.dabrender_text_lb.setMinimumWidth(_width)
        self.dabrender_text_le  = qg.QLineEdit(self.p.dabrender)

        # self.dabrender_text_le.setPlaceholderText(self.getdabrender())
        # self.dabrender_text_le.setMinimumWidth(150)

        # self.dabrender_text_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.dabrender_text_layout.addWidget(self.dabrender_text_lb)
        self.dabrender_text_layout.addWidget(self.dabrender_text_le)

        self.layout().addLayout(self.dabrender_text_layout)

        #  $TYPE  ---------------------------------------
        self.scene_layout = qg.QHBoxLayout()
        self.scene_layout.setSpacing(0)
        self.scene_layout.setContentsMargins(0,0,0,0)
        self.layout().addLayout(self.scene_layout)

        self.scene_text_lb = qg.QLabel('$TYPE:')
        self.scene_text_lb.setMinimumWidth(_width)
        self.scene_combo  = qg.QComboBox()
        self.scene_combo.addItem('work')
        self.scene_combo.addItem('projects')
        # self.scene_combo.setMinimumWidth(150)

        # self.scene_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.scene_layout.addWidget(self.scene_text_lb)
        self.scene_layout.addWidget(self.scene_combo)

        self.scene_combo.connect(self.scene_combo,qc.SIGNAL("currentIndexChanged(int)"), self.typeChanged)

        #  $SHOW  ---------------------------------------
        self.show_text_layout = qg.QHBoxLayout()
        self.show_text_layout.setContentsMargins(0,0,0,0)
        self.show_text_layout.setSpacing(0)

        self.show_text_lb = qg.QLabel('$SHOW:')
        self.show_text_lb.setMinimumWidth(_width)
        self.show_text_le  = qg.QLineEdit()
        # self.show_text_le.
        # self.show_text_le.setMinimumWidth(150)

        self.show_text_le.setPlaceholderText(self.p.show)

        # self.show_text_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.show_text_layout.addWidget(self.show_text_lb)
        self.show_text_layout.addWidget(self.show_text_le)

        self.layout().addLayout(self.show_text_layout)

        #  $PROJECT ---------------------------------------
        self.project_text_layout = qg.QHBoxLayout()
        self.project_text_layout.setContentsMargins(0,0,0,0)
        self.project_text_layout.setSpacing(0)

        self.project_text_lb = qg.QLabel('$PROJECT:')
        self.project_text_lb.setMinimumWidth(_width)
        self.project_text_le  = qg.QLineEdit()
        # self.project_text_le.setMinimumWidth(150)
        self.project_text_le.setPlaceholderText(self.p.project)

        # self.project_text_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.project_text_layout.addWidget(self.project_text_lb)
        self.project_text_layout.addWidget(self.project_text_le)

        self.layout().addLayout(self.project_text_layout)

    def typeChanged(self):
        logger.info("Type changed now {}".format(self.scene_combo.currentText()))

    def getdabrender(self):
        _dabrender = os.getenv("DABRENDER")

        self.dabrender = _dabrender
        logger.info("$DABRENDER: {}".format(_dabrender))
        return _dabrender


# -------------------------------------------------------------------------------------------------------------------- #

class SceneWidget(qg.QWidget):
    def __init__(self):
        super(SceneWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        self.layout().addWidget(Splitter("SCENE FILE"))

        #  JOB SCENE FILE
        self.scene_layout = qg.QHBoxLayout()
        self.scene_layout.setContentsMargins(0,0,0,0)
        self.scene_layout.setSpacing(0)

        self.scene_text_lb = qg.QLabel('SCENE FILE:')
        self.scene_combo  = qg.QComboBox()
        # self.scene_combo.setCompleter()
        self.scene_combo.addItem('select from list')
        # self.scene_combo.setMinimumWidth(150)

        self.scene_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.scene_layout.addWidget(self.scene_text_lb)
        self.scene_layout.addWidget(self.scene_combo)

        self.layout().addLayout(self.scene_layout)


# -------------------------------------------------------------------------------------------------------------------- #
class SubmitWidget(qg.QWidget):
    def __init__(self):
        super(SubmitWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        self.layout().addWidget(Splitter("SUBMIT JOB"))

        self.button_group=qg.QWidget()
        self.button_group.setLayout(qg.QHBoxLayout())
        self.button_group.layout().setSpacing(0)
        self.button_group.layout().setContentsMargins(0,0,0,0)

        self.submit_layout_1_bttn = qg.QPushButton('Cancel')
        self.submit_layout_2_bttn = qg.QPushButton('Validate')
        self.submit_layout_3_bttn = qg.QPushButton('Submit')

        self.button_group.layout().addWidget(self.submit_layout_1_bttn)
        self.button_group.layout().addWidget(self.submit_layout_2_bttn)
        self.button_group.layout().addWidget(self.submit_layout_3_bttn)

        self.layout().addWidget(self.button_group)

        self.submit_layout_1_bttn.clicked.connect(self.cancel)
        self.submit_layout_2_bttn.clicked.connect(self.validate)
        self.submit_layout_3_bttn.clicked.connect(self.submit)

    def cancel(self):
        logger.info("Cancel Pressed")

    def validate(self):
        logger.info("Validate Pressed")

    def submit(self):
        logger.info("Submit Pressed")

# -------------------------------------------------------------------------------------------------------------------- #
class RangeWidget(qg.QWidget):
    def __init__(self):
        super(RangeWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        self.layout().addWidget(Splitter("FRAME RANGE"))

        self.framerange_layout = qg.QGridLayout()
        self.framerange_layout.setContentsMargins(0,0,0,0)
        self.framerange_layout.setSpacing(0)

        self.framerange_start_text_lb = qg.QLabel('S:')
        self.framerange_start_text_lb.setMinimumWidth(20)
        self.framerange_start_text_le = qg.QLineEdit()
        self.framerange_start_text_le.setMaximumWidth(60)
        self.framerange_start_text_le.setPlaceholderText("START")

        self.framerange_end_text_lb = qg.QLabel('E:')
        self.framerange_end_text_lb.setMinimumWidth(20)
        self.framerange_end_text_le = qg.QLineEdit()
        self.framerange_end_text_le.setPlaceholderText("END")
        self.framerange_end_text_le.setMaximumWidth(60)

        self.framerange_by_text_lb = qg.QLabel('B:')
        self.framerange_by_text_lb.setMinimumWidth(20)
        self.framerange_by_text_le = qg.QLineEdit()
        self.framerange_by_text_le.setMaximumWidth(60)
        self.framerange_by_text_le.setPlaceholderText("BY")

        self.framerange_layout.addItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding),0,0)
        self.framerange_layout.addWidget(self.framerange_start_text_lb,0,1)
        self.framerange_layout.addWidget(self.framerange_start_text_le,0,2)

        self.framerange_layout.addItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding),0,3)
        self.framerange_layout.addWidget(self.framerange_end_text_lb,0,4)
        self.framerange_layout.addWidget(self.framerange_end_text_le,0,5)

        self.framerange_layout.addItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding),0,6)
        self.framerange_layout.addWidget(self.framerange_by_text_lb,0,7)
        self.framerange_layout.addWidget(self.framerange_by_text_le,0,8)

        self.layout().addLayout(self.framerange_layout)


# -------------------------------------------------------------------------------------------------------------------- #
class MayaJobWidget(qg.QWidget):
    def __init__(self):
        super(MayaJobWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        # PROJECT WIDGET
        project_widget = ProjectWidget()
        self.layout().addWidget(project_widget)
        # RANGE WIDGET
        range_widget = RangeWidget()
        self.layout().addWidget(range_widget)

        # BUILD MAYA WIDGET BITS
        maya_widget = MayaWidget()
        self.layout().addWidget(maya_widget)

# -------------------------------------------------------------------------------------------------------------------- #
class MayaWidget(qg.QWidget):
    def __init__(self):
        super(MayaWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        self.layout().addWidget(Splitter("MAYA OPTIONS"))

        self.version_layout = qg.QHBoxLayout()
        self.version_layout.setContentsMargins(0,0,0,0)
        self.version_layout.setSpacing(0)
        self.layout().addLayout(self.version_layout)

        self.version_text_lb = qg.QLabel('VERSION:')
        self.version_combo  = qg.QComboBox()
        self.version_combo.addItem('2016')
        self.version_combo.addItem('2017')
        # self.version_combo.setMinimumWidth(150)

        self.version_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.version_layout.addWidget(self.version_text_lb)
        self.version_layout.addWidget(self.version_combo)

# -------------------------------------------------------------------------------------------------------------------- #
class MentalRayJobWidget(qg.QWidget):
    def __init__(self):
        super(MentalRayJobWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        # PROJECT WIDGET
        self.project_widget = ProjectWidget()
        self.layout().addWidget(self.project_widget)

        # RANGE WIDGET
        self.range_widget = RangeWidget()
        self.layout().addWidget(self.range_widget)

        # MAYA OPTIONS
        self.maya_widget = MayaWidget()
        self.layout().addWidget(self.maya_widget)

        # MENTAL RAY OPTIONS
        self.mentalray_widget = MentalRayWidget()
        self.layout().addWidget(self.mentalray_widget)


# -------------------------------------------------------------------------------------------------------------------- #
class MentalRayWidget(qg.QWidget):
    def __init__(self):
        super(MentalRayWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        self.project_splitter = Splitter("MENTALRAY OPTIONS")
        self.layout().addWidget(self.project_splitter)

        self.version_layout = qg.QHBoxLayout()
        self.version_layout.setContentsMargins(0,0,0,0)
        self.version_layout.setSpacing(0)
        self.layout().addLayout(self.version_layout)

        self.version_text_lb = qg.QLabel('MENTAL RAY:')
        self.version_combo  = qg.QComboBox()
        self.version_combo.addItem('2016')
        self.version_combo.addItem('2017')
        # self.version_combo.setMinimumWidth(150)

        self.version_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.version_layout.addWidget(self.version_text_lb)
        self.version_layout.addWidget(self.version_combo)


# -------------------------------------------------------------------------------------------------------------------- #
class FeedbackWidget(qg.QTextEdit):

    def __init__(self):
        super(FeedbackWidget, self).__init__()
        self.setMinimumHeight(200)
        # self.setAlignment()
        self.setWordWrapMode(qg.QTextOption.WordWrap)
        self.setReadOnly(True)
        self.append("Some feedback here")

    def clear(self):
        self.clear()

    def write(self,_text):
        self.append(_text)


# -------------------------------------------------------------------------------------------------------------------- #
class RendermanJobWidget(qg.QWidget):
    def __init__(self):
        super(RendermanJobWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        # PROJECT WIDGET
        self.project_widget = ProjectWidget()
        self.layout().addWidget(self.project_widget)

        # RANGE WIDGET
        self.range_widget = RangeWidget()
        self.layout().addWidget(self.range_widget)

        # BUILD MAYA OPTIONS
        self.maya_widget = MayaWidget()
        self.layout().addWidget(self.maya_widget)

        # BUILD RENDERMAN OPTIONS
        self.renderman_widget = RendermanWidget()
        self.layout().addWidget(self.renderman_widget)


# -------------------------------------------------------------------------------------------------------------------- #
class RendermanWidget(qg.QWidget):
    def __init__(self):
        super(RendermanWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        self.project_splitter = Splitter("RENDERMAN OPTIONS")
        self.layout().addWidget(self.project_splitter)

        self.version_layout = qg.QHBoxLayout()
        self.version_layout.setContentsMargins(0,0,0,0)
        self.version_layout.setSpacing(0)
        self.layout().addLayout(self.version_layout)

        self.version_text_lb = qg.QLabel('RMS VERSION:')
        self.version_combo  = qg.QComboBox()
        self.version_combo.addItem('20.5')
        self.version_combo.addItem('20.6')
        # self.version_combo.setMinimumWidth(150)

        self.version_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.version_layout.addWidget(self.version_text_lb)
        self.version_layout.addWidget(self.version_combo)


# -------------------------------------------------------------------------------------------------------------------- #
class BashJobWidget(qg.QWidget):
    def __init__(self):
        super(BashJobWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        # BASH WIDGET
        self.bash_widget = BashWidget()
        self.layout().addWidget(self.bash_widget)

# -------------------------------------------------------------------------------------------------------------------- #
class BashWidget(qg.QWidget):
    def __init__(self):
        super(BashWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)


        self.project_splitter = Splitter("BASH OPTIONS")
        self.layout().addWidget(self.project_splitter)

        self.version_layout = qg.QHBoxLayout()
        self.version_layout.setContentsMargins(0,0,0,0)
        self.version_layout.setSpacing(0)
        self.layout().addLayout(self.version_layout)

        self.version_text_lb = qg.QLabel('VERSION:')
        self.version_combo  = qg.QComboBox()
        self.version_combo.addItem('20.5')
        self.version_combo.addItem('20.6')
        # self.version_combo.setMinimumWidth(150)

        self.version_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.version_layout.addWidget(self.version_text_lb)
        self.version_layout.addWidget(self.version_combo)

# -------------------------------------------------------------------------------------------------------------------- #
class ArchiveJobWidget(qg.QWidget):
    def __init__(self):
        super(ArchiveJobWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        # ARCHIVE WIDGET
        self.archive_widget = ArchiveWidget()
        self.layout().addWidget(self.archive_widget)


# -------------------------------------------------------------------------------------------------------------------- #
class ArchiveWidget(qg.QWidget):
    def __init__(self):
        super(ArchiveWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)


        self.project_splitter = Splitter("ARCHIVE OPTIONS")
        self.layout().addWidget(self.project_splitter)

        self.version_layout = qg.QHBoxLayout()
        self.version_layout.setContentsMargins(0,0,0,0)
        self.version_layout.setSpacing(0)
        self.layout().addLayout(self.version_layout)

        self.version_text_lb = qg.QLabel('VERSION:')
        self.version_combo  = qg.QComboBox()
        self.version_combo.addItem('20.5')
        self.version_combo.addItem('20.6')
        # self.version_combo.setMinimumWidth(150)

        self.version_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.version_layout.addWidget(self.version_text_lb)
        self.version_layout.addWidget(self.version_combo)

# -------------------------------------------------------------------------------------------------------------------- #
class NukeJobWidget(qg.QWidget):
    def __init__(self):
        super(NukeJobWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        # PROJECT WIDGET
        self.project_widget = ProjectWidget()
        self.layout().addWidget(self.project_widget)

        # RANGE WIDGET
        self.range_widget = RangeWidget()
        self.layout().addWidget(self.range_widget)

        # NUKE WIDGET
        self.nuke_widget = NukeWidget()
        self.layout().addWidget(self.nuke_widget)

# -------------------------------------------------------------------------------------------------------------------- #
class NukeWidget(qg.QWidget):
    def __init__(self):
        super(NukeWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        self.project_splitter = Splitter("NUKE OPTIONS")
        self.layout().addWidget(self.project_splitter)

        self.version_layout = qg.QHBoxLayout()
        self.version_layout.setContentsMargins(0,0,0,0)
        self.version_layout.setSpacing(0)
        self.layout().addLayout(self.version_layout)

        self.version_text_lb = qg.QLabel('NUKE VERSION:')
        self.version_combo  = qg.QComboBox()
        self.version_combo.addItem('9.0v8')
        self.version_combo.addItem('9.0v7')
        # self.version_combo.setMinimumWidth(150)

        self.version_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.version_layout.addWidget(self.version_text_lb)
        self.version_layout.addWidget(self.version_combo)

# -------------------------------------------------------------------------------------------------------------------- #
class TractorWidget(qg.QWidget):
    def __init__(self):
        super(TractorWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)


        self.project_splitter = Splitter("JOB TRACTOR OPTIONS")
        self.layout().addWidget(self.project_splitter)
        self.progect_group_layout = qg.QHBoxLayout()
        self.progect_group_layout.setContentsMargins(0,0,0,0)
        self.progect_group_layout.setSpacing(0)

        self.progect_group_text_lb = qg.QLabel('PROJECT GROUP:')
        self.progect_group_combo  = qg.QComboBox()
        # self.progect_group_combo.setCompleter()
        self.progect_group_combo.addItem('Year 1 Assignment')
        self.progect_group_combo.addItem('Year 2 Assignment')
        self.progect_group_combo.addItem('Year 3 Assignment')
        self.progect_group_combo.addItem('Year 4 Assignment')
        self.progect_group_combo.addItem('Personal Job')

        # self.progect_group_combo.setMinimumWidth(150)

        self.progect_group_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.progect_group_layout.addWidget(self.progect_group_text_lb)
        self.progect_group_layout.addWidget(self.progect_group_combo)

        self.layout().addLayout(self.progect_group_layout)

# -------------------------------------------------------------------------------------------------------------------- #
class Directory(qg.QFileDialog):
    def __init__(self,startplace=None,title="Select a Directory Please"):
        super(Directory, self).__init__()
        self.setWindowTitle(title)
        self.setModal(True)
        self.setDirectory(startplace)
        self.directory = self.getExistingDirectory(self,title)
        if self.directory:
            print self.directory


# -------------------------------------------------------------------------------------------------------------------- #
class File(qg.QFileDialog):
    def __init__(self,startplace=None,title='Select a File Please',filetypes=["*.ma","*.mb"]):
        super(File, self).__init__()
        # self.setWindowTitle(title)
        '''
        osx dialogue doesnt see the title dammit
        '''
        self.setModal(True)
        self.setDirectory(startplace)
        self.setFilter('*.ma')
        self.fileName = self.getOpenFileName(self,
            title, startplace,
            "Files (%s)" % " ".join(filetypes))
        if self.fileName:
            print self.fileName

# -------------------------------------------------------------------------------------------------------------------- #
class Splitter(qg.QWidget):
    def __init__(self, text=None, shadow=True, color=(150, 150, 150)):
        super(Splitter, self).__init__()
        self.setMinimumHeight(2)
        self.setLayout(qg.QHBoxLayout())
        self.layout().setContentsMargins(0,8,0,4)
        self.layout().setSpacing(0)
        self.layout().setAlignment(qc.Qt.AlignVCenter)

        first_line = qg.QFrame()
        first_line.setFrameStyle(qg.QFrame.HLine)
        self.layout().addWidget(first_line)

        main_color   = 'rgba( %s, %s, %s, 255)' %color
        shadow_color = 'rgba( 45,  45,  45, 255)'

        bottom_border = ''
        if shadow:
            bottom_border = 'border-bottom:1px solid %s;' %shadow_color

        style_sheet = "border:0px solid rgba(0,0,0,0); \
                       background-color: %s; \
                       max-height:1px; \
                       %s" %(main_color, bottom_border)

        first_line.setStyleSheet(style_sheet)

        if text is None:
            return

        first_line.setMaximumWidth(5)
        font = qg.QFont()
        font.setBold(True)

        text_width = qg.QFontMetrics(font)
        width = text_width.width(text) + 6

        label = qg.QLabel()
        label.setText(text)
        label.setFont(font)
        label.setMaximumWidth(width)
        label.setAlignment(qc.Qt.AlignHCenter | qc.Qt.AlignVCenter)

        self.layout().addWidget(label)

        second_line = qg.QFrame()
        second_line.setFrameStyle(qg.QFrame.HLine)
        second_line.setStyleSheet(style_sheet)
        self.layout().addWidget(second_line)

# -------------------------------------------------------------------------------------------------------------------- #
class FarmJobExtraWidget(qg.QWidget):
    def __init__(self):
        super(FarmJobExtraWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)


