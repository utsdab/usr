import PySide.QtCore as qc
import PySide.QtGui as qg
import sys
import os
from software.renderfarm.dabtractor.factories import user_factory as ufac
from software.renderfarm.dabtractor.factories import utils_factory as utilfac
from software.renderfarm.dabtractor.factories import environment_factory as proj
from software.renderfarm.dabtractor.factories import configuration_factory as config

from functools import partial

# ##############################################################
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)5.5s \t%(filename)s as %(name)s \t%(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)
# ##############################################################


# -------------------------------------------------------------------------------------------------------------------- #

class UserWidget(qg.QWidget):
    def __init__(self,job):
        super(UserWidget, self).__init__()
        self.job = job
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(2)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        self.layout().addWidget(Splitter("USER DETAILS"))
        
        self.usernumber_text_layout = qg.QHBoxLayout()
        self.usernumber_text_layout.setSpacing(2)
        self.usernumber_text_layout.setContentsMargins(0,0,0,0)
        self.usernumber_text_layout.addSpacerItem(qg.QSpacerItem(5,0,qg.QSizePolicy.Fixed))

        self.usernumber_text_lb = qg.QLabel('$USER: {}'.format(self._getuser()))
        self.usernumber_text_layout.addWidget(self.usernumber_text_lb)
        self.layout().addLayout(self.usernumber_text_layout)

        self.username_text_layout = qg.QHBoxLayout()
        self.username_text_layout.setSpacing(2)
        self.username_text_layout.setContentsMargins(0,0,0,0)
        self.username_text_layout.addSpacerItem(qg.QSpacerItem(5,0,qg.QSizePolicy.Fixed))
        self.username_text_lb = qg.QLabel('$USERNAME: {}'.format(self._getusername(self._getuser())))
        self.username_text_layout.addWidget(self.username_text_lb)

        self.layout().addLayout(self.username_text_layout)

    def _getusername(self,_user):
        u=ufac.Map()
        self.username=u.getusername(_user)
        self.job.username=self.username
        return self.username

    def _getuser(self):
        self.usernumber=os.getenv("USER")
        self.job.usernumber=self.usernumber
        return self.usernumber

# -------------------------------------------------------------------------------------------------------------------- #
class ProjectWidget(qg.QWidget):
    def __init__(self, job):
        super(ProjectWidget, self).__init__()
        self.job = job
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)
        # self.layout().addWidget(Splitter("ENVIRONMENT"))

        _width=90

        # $DABRENDER ------------------------------------------------------------------------------------ #
        self.dabrender_text_lb = qg.QLabel('$DABRENDER:')
        self.dabrender_text_lb.setMinimumWidth(_width)
        self.dabrender_text_le  = qg.QLineEdit(self.job.dabrender)
        self.dabrender_text_le.setReadOnly(True)
        self.dabrender_text_layout = qg.QHBoxLayout()
        self.dabrender_text_layout.setSpacing(0)
        self.dabrender_text_layout.setContentsMargins(0,0,0,0)
        self.dabrender_text_layout.addWidget(self.dabrender_text_lb)
        self.dabrender_text_layout.addWidget(self.dabrender_text_le)
        self.layout().addLayout(self.dabrender_text_layout)
        # self.job.dabrenderpath=self.job.dabrender

        #  $TYPE  ---------------------------------------
        self.type_text_lb = qg.QLabel('$TYPE:')
        self.type_text_lb.setMinimumWidth(_width)
        self.type_combo  = qg.QComboBox()
        self.type_combo.setMinimumWidth(200)
        self.type_combo.setEditable(False)
        self.type_combo.addItem('user_work')
        self.type_combo.addItem('project_work')
        self.type_combo.setCurrentIndex(0)
        self.type_layout = qg.QHBoxLayout()
        self.type_layout.setSpacing(0)
        self.type_layout.setContentsMargins(0,0,0,0)
        self.type_combo.activated.connect(lambda: self._type_change())
        self.type_layout.addWidget(self.type_text_lb)
        self.type_layout.addWidget(self.type_combo)
        self.type_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.layout().addLayout(self.type_layout)

        #  $SHOW  ---------------------------------------
        self.show_text_lb = qg.QLabel('$SHOW:')
        self.show_text_lb.setMinimumWidth(_width)
        self.show_combo  = qg.QComboBox()
        self.show_combo.setMinimumWidth(200)
        self.show_combo.setEditable(False)
        self.show_combo.addItem(self.job.username)
        self.show_combo.setCurrentIndex(0)
        self.show_layout = qg.QHBoxLayout()
        self.show_layout.setSpacing(0)
        self.show_layout.setContentsMargins(0,0,0,0)
        self.show_combo.activated.connect(lambda: self._show_change())
        self.show_layout.addWidget(self.show_text_lb)
        self.show_layout.addWidget(self.show_combo)
        self.show_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.layout().addLayout(self.show_layout)

        #  $PROJECT ---------------------------------------
        self.project_text_lb = qg.QLabel('$PROJECT:')
        self.project_text_lb.setMinimumWidth(_width)
        self.project_combo  = qg.QComboBox()
        self.project_combo.setMinimumWidth(200)
        self.project_combo.setEditable(False)
        self.project_layout = qg.QHBoxLayout()
        self.project_layout.setSpacing(0)
        self.project_layout.setContentsMargins(0,0,0,0)
        self.project_combo.activated.connect(lambda: self._project_change())
        self.project_layout.addWidget(self.project_text_lb)
        self.project_layout.addWidget(self.project_combo)
        self.project_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.layout().addLayout(self.project_layout)

        # ste initial values
        self._type_change()
        self._show_change()
        self._project_change()

    def _type_change(self):
        _type=self.type_combo.currentText()
        self.job.typepath=os.path.join(self.job.dabrender, _type)

        if _type=="user_work":
            self._combo_from_path(self.show_combo, self.job.username)
            self.job.showpath=os.path.join(self.job.typepath, self.job.username)
            self._combo_from_path(self.project_combo, self.job.showpath)
        elif _type=="project_work":
            self._combo_from_path(self.show_combo, self.job.typepath)
            self._combo_from_path(self.project_combo,"")
        logger.debug("Type changed to {}".format(_type))


    def _show_change(self):
        _show=self.show_combo.currentText()
        self.job.showpath=os.path.join(self.job.dabrender,self.job.type,_show)

        self._combo_from_path(self.type_combo,self.job.showpath)
        logger.debug("Show changed to {}".format(_show))

    def _project_change(self):
        _project=self.project_combo.currentText()
        self.job.projectpath=os.path.join(self.job.showpath,_project)

        self.job.project=_project
        logger.debug("Project changed to {}".format(_project))


    def _get_dabrender(self):
        _dabrender = os.getenv("DABRENDER")
        self.dabrender = _dabrender
        self.job.dabrender = self.dabrender
        logger.debug("$DABRENDER is {}".format(_dabrender))
        return _dabrender

    def _combo_from_path(self,_combobox,_dirpath):
        # rebuild a combobox list from the contents of a path
        # given a path build a list of files and directories
        try:
            _combobox.clear()
            _files=[]
            _dirs=[]
            if os.path.isdir(_dirpath):
                _items = os.listdir(_dirpath)
                for i,_item in enumerate(_items):
                    if os.path.isfile(os.path.join(_dirpath,_item)):
                        _files.append(_item)
                    elif os.path.isdir(os.path.join(_dirpath,_item)):
                        _dirs.append(_item)
            else:
                # just pass thru the string
                print"xxxx"
                _dirs=[_dirpath]

            for i,_item in enumerate(_dirs):
                _combobox.addItem(_item)

        except Exception, err:
            logger.warn("combo from path: %s"%err)

    def _get_show(self):
        pass

# -------------------------------------------------------------------------------------------------------------------- #
class SceneWidget(qg.QWidget):
    def __init__(self,job):
        super(SceneWidget, self).__init__()
        self.job=job
        _width=220
        self.setLayout(qg.QVBoxLayout())
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        # self.layout().addWidget(Splitter("SCENE FILE"))
        self.scene_text_lb = qg.QLabel('SCENE FILE:')
        self.scene_file_lb  = qg.QPushButton("select scene file")
        self.scene_file_lb.setMinimumWidth(_width)
        # self.scene_file_le.setReadOnly(True)
        self.scene_file_layout = qg.QHBoxLayout()
        self.scene_file_layout.setSpacing(0)
        self.scene_file_layout.setContentsMargins(0,0,0,0)
        self.scene_file_layout.addWidget(self.scene_text_lb)
        self.scene_file_layout.addWidget(self.scene_file_lb)
        self.layout().addLayout(self.scene_file_layout)
        self.scene_file_lb.clicked.connect(lambda : self._get_scene())
        
    def _get_scene(self):
        f=File(startplace=self.job.projectpath)
        self.job.scenefullpath=f.fullpath
        self.job.scenerelpath=f.relpath
        self.job.scene=f.relpath
        self.scene_file_lb.setText(f.relpath)
        self.job.putback()
        logger.debug("Scene changed to {}".format(self.job.scene))


# -------------------------------------------------------------------------------------------------------------------- #
class SubmitWidget(qg.QWidget):
    def __init__(self,job,feedback):
        super(SubmitWidget, self).__init__()
        self.job = job
        self.fb=feedback
        self.setLayout(qg.QVBoxLayout())
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)
        self.submit_layout_1_bttn = qg.QPushButton('Sanity Check')
        # self.submit_layout_1_bttn.setStyleSheet("background-color: Tan")
        self.submit_layout_2_bttn = qg.QPushButton('Validate')
        # self.submit_layout_2_bttn.setStyleSheet("background-color: Tan")
        self.submit_layout_3_bttn = qg.QPushButton('SUBMIT')
        # self.submit_layout_3_bttn.setStyleSheet("background-color: Tan")
        self.button_group=qg.QWidget()
        self.button_group.setLayout(qg.QHBoxLayout())
        self.button_group.layout().setSpacing(0)
        self.button_group.layout().setContentsMargins(0,0,0,0)
        self.button_group.layout().addWidget(self.submit_layout_1_bttn)
        self.button_group.layout().addWidget(self.submit_layout_2_bttn)
        self.button_group.layout().addWidget(self.submit_layout_3_bttn)
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().addWidget(Splitter("SUBMIT JOB"))
        self.layout().addWidget(self.button_group)

        self.submit_layout_1_bttn.clicked.connect(self.sanity)
        self.submit_layout_2_bttn.clicked.connect(self.validate)
        self.submit_layout_3_bttn.clicked.connect(self.submit)

    def sanity(self):
        logger.debug("Sanity Checker Pressed")
        self.fb.write("---Sanity Check Start---")
        self.fb.write("Not implemented yet")
        self.fb.write("---Sanity Check Ended---")


    def validate(self):
        logger.debug("Validate Job Pressed")
        self.fb.write("Validate Job")
        self.job.printme()
        self.job.rmsvalidate()

    def submit(self):
        self.fb.write("Submit Job")
        logger.debug("Submit Job Pressed")
        self.job.rmsspool()

# -------------------------------------------------------------------------------------------------------------------- #
class OutputWidget(qg.QWidget):
    def __init__(self,job):
        super(OutputWidget, self).__init__()
        self.job=job
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)
        _width1 = 180

        # resolution
        self.resolution_text_lb = qg.QLabel('RESOLUTION:')
        self.resolution_combo  = qg.QComboBox()
        self.resolution_combo.addItems(config.CurrentConfiguration().resolutions)
        self.resolution_combo.setMinimumWidth(_width1)
        self.resolution_layout = qg.QHBoxLayout()
        self.resolution_layout.setContentsMargins(0,0,0,0)
        self.resolution_layout.setSpacing(0)
        self.resolution_layout.addWidget(self.resolution_text_lb)
        self.resolution_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.resolution_layout.addWidget(self.resolution_combo)
        self.layout().addLayout(self.resolution_layout)

        # outformat
        self.outformat_text_lb = qg.QLabel('OUTPUT:')
        self.outformat_combo  = qg.QComboBox()
        self.outformat_combo.addItems(config.CurrentConfiguration().outformats)
        self.outformat_combo.setMinimumWidth(_width1)
        self.outformat_layout = qg.QHBoxLayout()
        self.outformat_layout.setContentsMargins(0,0,0,0)
        self.outformat_layout.setSpacing(0)
        self.outformat_layout.addWidget(self.outformat_text_lb)
        self.outformat_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.outformat_layout.addWidget(self.outformat_combo)
        self.layout().addLayout(self.outformat_layout)

        # set initial
        self._resolution(self.resolution_combo.currentText())
        self._outformat(self.outformat_combo.currentText())
        # connections
        self.outformat_combo.activated.connect(lambda: self._outformat(self.outformat_combo.currentText()))
        self.resolution_combo.activated.connect(lambda: self._resolution(self.resolution_combo.currentText()))

    def _outformat(self,_value):
        self.job.outformat=_value
        logger.debug("Out Format group changed to {}".format(self.job.outformat))

    def _resolution(self,_value):
        self.job.resolution=_value
        logger.debug("Resolution group changed to {}".format(self.job.resolution))

# -------------------------------------------------------------------------------------------------------------------- #
class RangeWidget(qg.QWidget):
    def __init__(self,job):
        super(RangeWidget, self).__init__()
        self.job=job
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        self.framerange_layout = qg.QGridLayout()
        self.framerange_layout.setContentsMargins(0,0,0,0)
        self.framerange_layout.setSpacing(0)

        self.framerange_start_text_lb = qg.QLabel('START:')
        self.framerange_start_text_lb.setMinimumWidth(20)
        self.framerange_start_text_le = qg.QLineEdit("1")
        self.framerange_start_text_le.setMaximumWidth(50)
        # self.framerange_start_text_le.setPlaceholderText("START")

        self.framerange_end_text_lb = qg.QLabel('END:')
        self.framerange_end_text_lb.setMinimumWidth(15)
        self.framerange_end_text_le = qg.QLineEdit("12")
        # self.framerange_end_text_le.setPlaceholderText("END")
        self.framerange_end_text_le.setMaximumWidth(50)

        self.framerange_by_text_lb = qg.QLabel('BY:')
        self.framerange_by_text_lb.setMinimumWidth(15)
        self.framerange_by_text_le = qg.QLineEdit("1")
        self.framerange_by_text_le.setMaximumWidth(50)
        # self.framerange_by_text_le.setPlaceholderText("BY")

        self.framerange_layout.addItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding),0,0)
        self.framerange_layout.addWidget(self.framerange_start_text_lb,0,1)
        self.framerange_layout.addWidget(self.framerange_start_text_le,0,2)

        self.framerange_layout.addItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding),0,3)
        self.framerange_layout.addWidget(self.framerange_end_text_lb,0,4)
        self.framerange_layout.addWidget(self.framerange_end_text_le,0,5)

        self.framerange_layout.addItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding),0,6)
        self.framerange_layout.addWidget(self.framerange_by_text_lb,0,7)
        self.framerange_layout.addWidget(self.framerange_by_text_le,0,8)
        self.framerange_layout.addItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding),0,9)

        self._start()
        self._end()
        self._by()

        self.framerange_start_text_le.textEdited.connect(lambda: self._start())
        self.framerange_end_text_le.textEdited.connect(lambda: self._end())
        self.framerange_by_text_le.textEdited.connect(lambda: self._by())

        self.layout().addLayout(self.framerange_layout)
        self.layout().addSpacerItem(qg.QSpacerItem(0,10,qg.QSizePolicy.Expanding))

        
    def _start(self):
        self.job.startframe=self.framerange_start_text_le.text()
        logger.debug("Start changed to {}".format(self.job.scene))

    def _end(self):
        self.job.endframe=self.framerange_end_text_le.text()
        logger.debug("End changed to {}".format(self.job.endframe))

    def _by(self):
        self.job.byframe=self.framerange_by_text_le.text()
        logger.debug("By changed to {}".format(self.job.byframe))

# -------------------------------------------------------------------------------------------------------------------- #
class MayaJobWidget(qg.QWidget):
    def __init__(self, job):
        super(MayaJobWidget, self).__init__()
        self.job=job
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().setAlignment(qc.Qt.AlignTop)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        # PROJECT WIDGET
        self.project_widget = ProjectWidget(self.job)
        self.layout().addWidget(self.project_widget)


        self.layout().addWidget(Splitter("COMMON RENDER OPTIONS"))
        # OUTPUT WIDGET
        self.outformat_widget = OutputWidget(self.job)
        self.layout().addWidget(self.outformat_widget)
        # RANGE WIDGET
        self.range_widget = RangeWidget(self.job)
        self.layout().addWidget(self.range_widget)
        # SCENE WIDGET
        self.scene_widget=SceneWidget(self.job)
        self.layout().addWidget(self.scene_widget)


        # BUILD MAYA WIDGET BITS
        self.maya_widget = MayaWidget(self.job)
        self.layout().addWidget(self.maya_widget)

# -------------------------------------------------------------------------------------------------------------------- #
class MayaWidget(qg.QWidget):
    def __init__(self,job):
        super(MayaWidget, self).__init__()
        _width=180
        self.job=job

        # self.scene_widget=SceneWidget(self.job)
        # self.layout().addWidget(self.scene_widget)

        self.setLayout(qg.QVBoxLayout())
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        self.version_layout = qg.QHBoxLayout()
        self.version_layout.setContentsMargins(0,0,0,0)
        self.version_layout.setSpacing(0)

        self.version_text_lb = qg.QLabel('MAYA VERSION:')
        self.version_combo  = qg.QComboBox()
        self.version_combo.setMinimumWidth(_width)
        self.version_combo.addItems(config.CurrentConfiguration().mayaversions)

        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        # self.layout().addWidget(Splitter("MAYA OPTIONS"))
        # self.layout().addWidget(self.scene_widget)
        self.layout().addLayout(self.version_layout)

        self.version_layout.addWidget(self.version_text_lb)
        self.version_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.version_layout.addWidget(self.version_combo)

        self._maya(self.version_combo.currentText())
        self.version_combo.activated.connect(lambda: self._maya(self.version_combo.currentText()))

    def _maya(self,_value):
        self.job.mayaversion=_value
        logger.debug("Maya changed to {}".format(self.job.mayaversion))




# -------------------------------------------------------------------------------------------------------------------- #
class MentalRayJobWidget(qg.QWidget):
    def __init__(self,job):
        super(MentalRayJobWidget, self).__init__()
        self.job=job
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().setAlignment(qc.Qt.AlignTop)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        # PROJECT WIDGET
        self.project_widget = ProjectWidget(self.job)
        self.layout().addWidget(self.project_widget)


        self.layout().addWidget(Splitter("COMMON RENDER OPTIONS"))
        # OUTPUT WIDGET
        self.outformat_widget = OutputWidget(self.job)
        self.layout().addWidget(self.outformat_widget)
        # RANGE WIDGET
        self.range_widget = RangeWidget(self.job)
        self.layout().addWidget(self.range_widget)
        # SCENE WIDGET
        self.scene_widget=SceneWidget(self.job)
        self.layout().addWidget(self.scene_widget)

        # MAYA OPTIONS
        self.maya_widget = MayaWidget(self.job)
        self.layout().addWidget(self.maya_widget)
        # MENTAL RAY OPTIONS
        self.mentalray_widget = MentalRayWidget(self.job)
        self.layout().addWidget(self.mentalray_widget)



# -------------------------------------------------------------------------------------------------------------------- #
class MentalRayWidget(qg.QWidget):
    def __init__(self,job):
        super(MentalRayWidget, self).__init__()
        self.job=job
        _width1=180
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        self.project_splitter = Splitter("MENTALRAY OPTIONS")
        self.layout().addWidget(self.project_splitter)


# -------------------------------------------------------------------------------------------------------------------- #
class FeedbackWidget(qg.QTextEdit):
    def __init__(self):
        super(FeedbackWidget, self).__init__()
        self.setMinimumHeight(100)
        self.setMaximumHeight(130)
        self.setWordWrapMode(qg.QTextOption.WordWrap)
        self.setReadOnly(True)

    def clear(self):
        self.clear()

    def write(self,_text):
        self.append(_text)


# -------------------------------------------------------------------------------------------------------------------- #
class RendermanJobWidget(qg.QWidget):
    def __init__(self,job):
        super(RendermanJobWidget, self).__init__()
        self.job=job
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().setAlignment(qc.Qt.AlignTop)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        # PROJECT WIDGET
        self.project_widget = ProjectWidget(self.job)
        self.layout().addWidget(self.project_widget)


        self.layout().addWidget(Splitter("COMMON RENDER OPTIONS"))
        # OUTPUT WIDGET
        self.outformat_widget = OutputWidget(self.job)
        self.layout().addWidget(self.outformat_widget)
        # RANGE WIDGET
        self.range_widget = RangeWidget(self.job)
        self.layout().addWidget(self.range_widget)
        # SCENE WIDGET
        self.scene_widget=SceneWidget(self.job)
        self.layout().addWidget(self.scene_widget)


        # BUILD MAYA OPTIONS
        self.maya_widget = MayaWidget(self.job)
        self.layout().addWidget(self.maya_widget)
        # BUILD RENDERMAN OPTIONS
        self.renderman_widget = RendermanWidget(self.job)
        self.layout().addWidget(self.renderman_widget)


# -------------------------------------------------------------------------------------------------------------------- #
class RendermanWidget(qg.QWidget):
    def __init__(self,job):
        super(RendermanWidget, self).__init__()
        self.job=job
        _width1 = 180
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        self.layout().addWidget(Splitter("RENDERMAN OPTIONS"))

        self.version_text_lb = qg.QLabel('RMS VERSION:')
        self.version_combo  = qg.QComboBox()
        self.version_combo.addItems(config.CurrentConfiguration().rendermanversions)
        self.version_combo.setMinimumWidth(_width1)
        self.version_layout = qg.QHBoxLayout()
        self.version_layout.setContentsMargins(0,0,0,0)
        self.version_layout.setSpacing(0)
        self.version_layout.addWidget(self.version_text_lb)
        self.version_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.version_layout.addWidget(self.version_combo)
        self.layout().addLayout(self.version_layout)

        self.threads_text_lb = qg.QLabel('THREADS:')
        self.threads_combo  = qg.QComboBox()
        self.threads_combo.addItems(config.CurrentConfiguration().renderthreads)
        self.threads_combo.setCurrentIndex(2)
        self.threads_combo.setMinimumWidth(_width1)
        self.threads_layout = qg.QHBoxLayout()
        self.threads_layout.setContentsMargins(0,0,0,0)
        self.threads_layout.setSpacing(0)
        self.threads_layout.addWidget(self.threads_text_lb)
        self.threads_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.threads_layout.addWidget(self.threads_combo)
        self.layout().addLayout(self.threads_layout)
        
        self.memory_text_lb = qg.QLabel('MEMORY MB:')
        self.memory_combo  = qg.QComboBox()
        self.memory_combo.addItems(config.CurrentConfiguration().rendermemorys)
        self.memory_combo.setCurrentIndex(1)
        self.memory_combo.setMinimumWidth(_width1)
        self.memory_layout = qg.QHBoxLayout()
        self.memory_layout.setContentsMargins(0,0,0,0)
        self.memory_layout.setSpacing(0)
        self.memory_layout.addWidget(self.memory_text_lb)
        self.memory_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.memory_layout.addWidget(self.memory_combo)
        self.layout().addLayout(self.memory_layout)
        
        self.integrator_text_lb = qg.QLabel('INTEGRATOR:')
        self.integrator_combo  = qg.QComboBox()
        self.integrator_combo.addItems(config.CurrentConfiguration().rendermanintegrators)
        self.integrator_combo.setMinimumWidth(_width1)
        self.integrator_layout = qg.QHBoxLayout()
        self.integrator_layout.setContentsMargins(0,0,0,0)
        self.integrator_layout.setSpacing(0)
        self.integrator_layout.addWidget(self.integrator_text_lb)
        self.integrator_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.integrator_layout.addWidget(self.integrator_combo)
        self.layout().addLayout(self.integrator_layout)
                
        self.maxsamples_text_lb = qg.QLabel('MAX SAMPLES:')
        self.maxsamples_combo  = qg.QComboBox()
        self.maxsamples_combo.addItems(config.CurrentConfiguration().rendermaxsamples)
        self.maxsamples_combo.setMinimumWidth(_width1)
        self.maxsamples_layout = qg.QHBoxLayout()
        self.maxsamples_layout.setContentsMargins(0,0,0,0)
        self.maxsamples_layout.setSpacing(0)
        self.maxsamples_layout.addWidget(self.maxsamples_text_lb)
        self.maxsamples_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.maxsamples_layout.addWidget(self.maxsamples_combo)
        self.layout().addLayout(self.maxsamples_layout)
        
        self.ribchunks_text_lb = qg.QLabel('RIBGEN CHUNKS:')
        self.ribchunks_combo  = qg.QComboBox()
        self.ribchunks_combo.addItems(config.CurrentConfiguration().ribgenchunks)
        self.ribchunks_combo.setMinimumWidth(_width1)
        self.ribchunks_layout = qg.QHBoxLayout()
        self.ribchunks_layout.setContentsMargins(0,0,0,0)
        self.ribchunks_layout.setSpacing(0)
        self.ribchunks_layout.addWidget(self.ribchunks_text_lb)
        self.ribchunks_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.ribchunks_layout.addWidget(self.ribchunks_combo)
        self.layout().addLayout(self.ribchunks_layout)
        
        # set initial values
        self._rms_maxsamples(self.maxsamples_combo.currentText())
        self._rms_integrator(self.integrator_combo.currentText())
        self._rms_memory(self.memory_combo.currentText())
        self._rms_threads(self.threads_combo.currentText())
        self._rms_version(self.version_combo.currentText())
        self._rms_ribchunks(self.ribchunks_combo.currentText())
        
        # connect vlaues to widget
        self.maxsamples_combo.activated.connect(lambda: self._rms_maxsamples(self.maxsamples_combo.currentText()))
        self.integrator_combo.activated.connect(lambda: self._rms_integrator(self.integrator_combo.currentText()))
        self.memory_combo.activated.connect(lambda: self._rms_memory(self.memory_combo.currentText()))
        self.threads_combo.activated.connect(lambda: self._rms_threads(self.threads_combo.currentText()))
        self.version_combo.activated.connect(lambda: self._rms_version(self.version_combo.currentText()))
        self.ribchunks_combo.activated.connect(lambda: self._rms_ribchunks(self.ribchunks_combo.currentText()))

    def _rms_maxsamples(self,_value):
        self.job.rms_maxsamples=_value
        logger.debug("Maya changed to {}".format(self.job.rms_maxsamples))

    def _rms_version(self,_value):
        self.job.rms_version=_value
        logger.debug("RMS Version changed to {}".format(self.job.rms_version))

    def _rms_integrator(self,_value):
        self.job.rms_integrator=_value
        logger.debug("Integrator changed to {}".format(self.job.rms_integrator))

    def _rms_memory(self,_value):
        self.job.rms_memory=_value
        logger.debug("Memory changed to {}".format(self.job.rms_memory))

    def _rms_threads(self,_value):
        self.job.rms_threads=_value
        logger.debug("Threads changed to {}".format(self.job.rms_threads))
        
    def _rms_ribchunks(self,_value):
        self.job.rms_ribchunks=_value
        logger.debug("Ribchunks changed to {}".format(self.job.rms_ribchunks))

# -------------------------------------------------------------------------------------------------------------------- #
class BashJobWidget(qg.QWidget):
    def __init__(self,job):
        super(BashJobWidget, self).__init__()
        self.job=job
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().setAlignment(qc.Qt.AlignTop)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        # BASH WIDGET
        self.bash_widget = BashWidget(self.job)
        self.layout().addWidget(self.bash_widget)

# -------------------------------------------------------------------------------------------------------------------- #
class BashWidget(qg.QWidget):
    def __init__(self,job):
        super(BashWidget, self).__init__()
        self.job=job
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        self.layout().addWidget(Splitter("BASH OPTIONS"))

        self.version_layout = qg.QHBoxLayout()
        self.version_layout.setContentsMargins(0,0,0,0)
        self.version_layout.setSpacing(0)
        self.layout().addLayout(self.version_layout)

        self.version_text_lb = qg.QLabel('VERSION:')
        self.version_combo  = qg.QComboBox()
        self.version_combo.addItems(config.CurrentConfiguration().rendermanversions)
        # self.version_combo.setMinimumWidth(150)

        self.version_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.version_layout.addWidget(self.version_text_lb)
        self.version_layout.addWidget(self.version_combo)

# -------------------------------------------------------------------------------------------------------------------- #
class ArchiveJobWidget(qg.QWidget):
    def __init__(self,job):
        super(ArchiveJobWidget, self).__init__()
        self.job=job
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().setAlignment(qc.Qt.AlignTop)

        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        # ARCHIVE WIDGET
        self.archive_widget = ArchiveWidget(self.job)
        self.layout().addWidget(self.archive_widget)


# -------------------------------------------------------------------------------------------------------------------- #
class ArchiveWidget(qg.QWidget):
    def __init__(self,job):
        super(ArchiveWidget, self).__init__()
        self.job=job
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        self.layout().addWidget(Splitter("ARCHIVE OPTIONS"))

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
    def __init__(self,job):
        super(NukeJobWidget, self).__init__()
        self.job=job
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().setAlignment(qc.Qt.AlignTop)

        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)


        # PROJECT WIDGET
        self.project_widget = ProjectWidget(self.job)
        self.layout().addWidget(self.project_widget)

        self.layout().addWidget(Splitter("COMMON RENDER OPTIONS"))

        # RANGE WIDGET
        self.range_widget = RangeWidget(self.job)
        self.layout().addWidget(self.range_widget)

        # SCENE WIDGET
        self.scene_widget=SceneWidget(self.job)
        self.layout().addWidget(self.scene_widget)

        # NUKE WIDGET
        self.nuke_widget = NukeWidget(self.job)
        self.layout().addWidget(self.nuke_widget)

# -------------------------------------------------------------------------------------------------------------------- #
class NukeWidget(qg.QWidget):
    def __init__(self,job):
        super(NukeWidget, self).__init__()
        self.job=job
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        self.layout().addWidget(Splitter("NUKE OPTIONS"))

        self.version_layout = qg.QHBoxLayout()
        self.version_layout.setContentsMargins(0,0,0,0)
        self.version_layout.setSpacing(0)
        self.layout().addLayout(self.version_layout)

        self.version_text_lb = qg.QLabel('NUKE VERSION:')
        self.version_combo  = qg.QComboBox()
        self.version_combo.addItem('9.0v8')
        self.version_combo.addItem('9.0v7')

        self.version_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.version_layout.addWidget(self.version_text_lb)
        self.version_layout.addWidget(self.version_combo)

# -------------------------------------------------------------------------------------------------------------------- #
class TractorWidget(qg.QWidget):
    def __init__(self,job):
        super(TractorWidget, self).__init__()
        self.job=job
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        self.tractor_options_splitter = Splitter("JOB TRACTOR OPTIONS")
        self.layout().addWidget(self.tractor_options_splitter)

        self.project_group_layout = qg.QHBoxLayout()
        self.project_group_layout.setContentsMargins(0,0,0,0)
        self.project_group_layout.setSpacing(0)

        self.project_group_text_lb = qg.QLabel('PROJECT GROUP:')
        self.project_group_combo  = qg.QComboBox()
        self.project_group_combo.addItems(config.CurrentConfiguration().projectgroups)

        self.project_group_layout.addSpacerItem(qg.QSpacerItem(0,5,qg.QSizePolicy.Expanding))
        self.project_group_layout.addWidget(self.project_group_text_lb)
        self.project_group_layout.addWidget(self.project_group_combo)

        self.layout().addLayout(self.project_group_layout)

        # set initial
        self._projectgroup(self.project_group_combo.currentText())
        # connections
        self.project_group_combo.activated.connect(lambda: self._projectgroup(self.project_group_combo.currentText()))

    def _projectgroup(self,_value):
        self.job.projectgroup =_value
        logger.debug("Project group changed to {}".format(self.job.projectgroup))



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
        self.fullpath=None
        self.relpath=None
        self.fileName = self.getOpenFileName(self,
            title, startplace,
            "Files (%s)" % " ".join(filetypes))
        if self.fileName:
            logger.info( "scene file: {}".format(self.fileName))
            self.relpath= os.path.join(os.path.relpath(os.path.dirname(self.fileName[0]),startplace),os.path.basename(
                self.fileName[0]))
            self.fullpath=self.fileName[0]

# -------------------------------------------------------------------------------------------------------------------- #
class Splitter(qg.QWidget):
    def __init__(self, text=None, shadow=True, color=(150, 150, 150)):
        super(Splitter, self).__init__()
        self.setMinimumHeight(2)
        self.setLayout(qg.QHBoxLayout())
        self.layout().setContentsMargins(2,8,2,4)
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
    def __init__(self,job):
        super(FarmJobExtraWidget, self).__init__()
        self.job=job
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(4)
        self.layout().setContentsMargins(2,2,2,2)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)
        
        self.layout().addWidget(Splitter("FARM EXTRA OPTIONS"))

        self.farm_group_box = qg.QGroupBox("Farm Options")
        self.farm_group_box_layout = qg.QGridLayout()
        self.farm_radio_box1 = qg.QRadioButton("Send Email")
        self.farm_radio_box1.setChecked(True)
        self.farm_radio_box2 = qg.QRadioButton("Make Editorial Proxy")
        self.farm_radio_box2.setChecked(True)
        self.farm_radio_box3 = qg.QRadioButton("Make Perfect")
        self.farm_radio_box4 = qg.QRadioButton("Wipe My Ass")

        self.farm_radio_box1.setCheckable(True)
        self.farm_radio_box1.setAutoExclusive(False)

        self.farm_radio_box2.setCheckable(True)
        self.farm_radio_box2.setAutoExclusive(False)

        self.farm_radio_box2.setCheckable(True)
        self.farm_radio_box3.setAutoExclusive(False)

        self.farm_radio_box4.setCheckable(True)
        self.farm_radio_box4.setAutoExclusive(False)

        self.farm_group_box_layout.addWidget(self.farm_radio_box1,0,0)
        self.farm_group_box_layout.addWidget(self.farm_radio_box2,0,1)
        self.farm_group_box_layout.addWidget(self.farm_radio_box3,1,0)
        self.farm_group_box_layout.addWidget(self.farm_radio_box4,1,1)

        self.layout().addLayout(self.farm_group_box_layout)


