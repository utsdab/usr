import PySide.QtCore as qc
import PySide.QtGui as qg
import sys
import os
from software.renderfarm.dabtractor.factories import user_factory as ufac

from functools import partial

class ProjectWidget(qg.QWidget):
    def __init__(self):
        super(ProjectWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(2)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        self.project_splitter = Splitter("ENVIRONMENT")
        self.layout().addWidget(self.project_splitter)

        # ------------------------------------------------------------------------------------ #
        #  $DABRENDER
        self.dabrender_text_layout = qg.QHBoxLayout()
        self.dabrender_text_layout.setContentsMargins(4,0,4,0)
        self.dabrender_text_layout.setSpacing(2)

        self.dabrender_text_lb = qg.QLabel('$DABRENDER:')
        self.dabrender_text_le  = qg.QLineEdit()
        self.dabrender_text_le.setPlaceholderText("The dabrender environment variable.....")
        self.dabrender_text_le.setMinimumWidth(300)

        self.dabrender_text_layout.addSpacerItem(qg.QSpacerItem(5,5,qg.QSizePolicy.Expanding))
        self.dabrender_text_layout.addWidget(self.dabrender_text_lb)
        self.dabrender_text_layout.addWidget(self.dabrender_text_le)

        self.layout().addLayout(self.dabrender_text_layout)

        # ------------------------------------------------------------------------------------ #
        #  $TYPE
        self.scene_layout = qg.QHBoxLayout()
        self.scene_layout.setContentsMargins(4,0,4,0)
        self.scene_layout.setSpacing(2)
        self.layout().addLayout(self.scene_layout)

        self.scene_text_lb = qg.QLabel('$TYPE:')
        self.scene_combo  = qg.QComboBox()
        self.scene_combo.addItem('work')
        self.scene_combo.addItem('projects')
        self.scene_combo.setMinimumWidth(300)

        self.scene_layout.addSpacerItem(qg.QSpacerItem(5,5,qg.QSizePolicy.Expanding))
        self.scene_layout.addWidget(self.scene_text_lb)
        self.scene_layout.addWidget(self.scene_combo)

        # ------------------------------------------------------------------------------------ #
        #  $SHOW
        self.show_text_layout = qg.QHBoxLayout()
        self.show_text_layout.setContentsMargins(4,0,4,0)
        self.show_text_layout.setSpacing(2)

        self.show_text_lb = qg.QLabel('$SHOW:')
        self.show_text_le  = qg.QLineEdit()
        self.show_text_le.setMinimumWidth(300)

        self.show_text_le.setPlaceholderText("The show environment variable.....your show")

        self.show_text_layout.addSpacerItem(qg.QSpacerItem(5,5,qg.QSizePolicy.Expanding))
        self.show_text_layout.addWidget(self.show_text_lb)
        self.show_text_layout.addWidget(self.show_text_le)

        self.layout().addLayout(self.show_text_layout)

        # ------------------------------------------------------------------------------------ #
        #  $PROJECT
        self.project_text_layout = qg.QHBoxLayout()
        self.project_text_layout.setContentsMargins(4,0,4,0)
        self.project_text_layout.setSpacing(2)

        self.project_text_lb = qg.QLabel('$PROJECT:')
        self.project_text_le  = qg.QLineEdit()
        self.project_text_le.setMinimumWidth(300)
        self.project_text_le.setPlaceholderText("The project environment variable..... the project in your show")

        self.project_text_layout.addSpacerItem(qg.QSpacerItem(5,5,qg.QSizePolicy.Expanding))
        self.project_text_layout.addWidget(self.project_text_lb)
        self.project_text_layout.addWidget(self.project_text_le)

        self.layout().addLayout(self.project_text_layout)


class SceneWidget(qg.QWidget):
    def __init__(self):
        super(SceneWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(2)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        self.project_splitter = Splitter("SCENE FILE")
        self.layout().addWidget(self.project_splitter)

        # ------------------------------------------------------------------------------------ #
        #  JOB SCENE FILE
        self.scene_layout = qg.QHBoxLayout()
        self.scene_layout.setContentsMargins(4,0,4,0)
        self.scene_layout.setSpacing(2)

        self.scene_text_lb = qg.QLabel('SCENE FILE:')
        self.scene_combo  = qg.QComboBox()
        # self.scene_combo.setCompleter()
        self.scene_combo.addItem('select from list')
        self.scene_combo.setMinimumWidth(300)

        self.scene_layout.addSpacerItem(qg.QSpacerItem(5,5,qg.QSizePolicy.Expanding))
        self.scene_layout.addWidget(self.scene_text_lb)
        self.scene_layout.addWidget(self.scene_combo)

        self.layout().addLayout(self.scene_layout)


class RangeWidget(qg.QWidget):
    def __init__(self):
        super(RangeWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(2)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        self.framerange_splitter = Splitter("FRAME RANGE")
        self.layout().addWidget(self.framerange_splitter)

        # ------------------------------------------------------------------------------------ #
        #  JOB FRAME RANGE
        self.framerange_layout = qg.QHBoxLayout()
        self.framerange_layout.setContentsMargins(4,0,4,0)
        self.framerange_layout.setSpacing(2)

        self.framerange_start_text_lb = qg.QLabel('START:')
        self.framerange_start_text_lb.setMinimumWidth(20)
        self.framerange_start_text_le = qg.QLineEdit()
        self.framerange_start_text_le.setMinimumWidth(20)
        self.framerange_start_text_le.setPlaceholderText("START")

        self.framerange_end_text_lb = qg.QLabel('END:')
        self.framerange_end_text_lb.setMinimumWidth(20)
        self.framerange_end_text_le = qg.QLineEdit()
        self.framerange_end_text_le.setPlaceholderText("END")
        self.framerange_end_text_le.setMinimumWidth(20)

        self.framerange_by_text_lb = qg.QLabel('BY:')
        self.framerange_by_text_lb.setMinimumWidth(20)
        self.framerange_by_text_le = qg.QLineEdit()
        self.framerange_by_text_le.setMinimumWidth(20)
        self.framerange_by_text_le.setPlaceholderText("BY")

        self.framerange_layout.addSpacerItem(qg.QSpacerItem(40,5,qg.QSizePolicy.Expanding))
        self.framerange_layout.addWidget(self.framerange_start_text_lb)
        self.framerange_layout.addWidget(self.framerange_start_text_le)
        self.framerange_layout.addWidget(self.framerange_end_text_lb)
        self.framerange_layout.addWidget(self.framerange_end_text_le)
        self.framerange_layout.addWidget(self.framerange_by_text_lb)
        self.framerange_layout.addWidget(self.framerange_by_text_le)

        self.layout().addLayout(self.framerange_layout)



class MayaWidget(qg.QWidget):
    def __init__(self):
        super(MayaWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(2)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)
        # ------------------------------------------------------------------------------------ #
        # PROJECT WIDGET
        project_widget = ProjectWidget()
        self.layout().addWidget(project_widget)

        self.project_splitter = Splitter("MAYA OPTIONS")
        self.layout().addWidget(self.project_splitter)

        # ------------------------------------------------------------------------------------ #
        self.version_layout = qg.QHBoxLayout()
        self.version_layout.setContentsMargins(4,0,4,0)
        self.version_layout.setSpacing(2)
        self.layout().addLayout(self.version_layout)

        self.version_text_lb = qg.QLabel('VERSION:')
        self.version_combo  = qg.QComboBox()
        self.version_combo.addItem('2016')
        self.version_combo.addItem('2017')
        self.version_combo.setMinimumWidth(300)

        self.version_layout.addSpacerItem(qg.QSpacerItem(5,5,qg.QSizePolicy.Expanding))
        self.version_layout.addWidget(self.version_text_lb)
        self.version_layout.addWidget(self.version_combo)



class MentalRayWidget(qg.QWidget):
    def __init__(self):
        super(MentalRayWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(2)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)
        # ------------------------------------------------------------------------------------ #
        # PROJECT WIDGET
        project_widget = ProjectWidget()
        self.layout().addWidget(project_widget)

        self.project_splitter = Splitter("MAYA OPTIONS")
        self.layout().addWidget(self.project_splitter)

        self.project_splitter = Splitter("MENTALRAY OPTIONS")
        self.layout().addWidget(self.project_splitter)

        # ------------------------------------------------------------------------------------ #
        self.version_layout = qg.QHBoxLayout()
        self.version_layout.setContentsMargins(4,0,4,0)
        self.version_layout.setSpacing(2)
        self.layout().addLayout(self.version_layout)

        self.version_text_lb = qg.QLabel('MAYA VERSION:')
        self.version_combo  = qg.QComboBox()
        self.version_combo.addItem('2016')
        self.version_combo.addItem('2017')
        self.version_combo.setMinimumWidth(300)

        self.version_layout.addSpacerItem(qg.QSpacerItem(5,5,qg.QSizePolicy.Expanding))
        self.version_layout.addWidget(self.version_text_lb)
        self.version_layout.addWidget(self.version_combo)



class RendermanWidget(qg.QWidget):
    def __init__(self):
        super(RendermanWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(2)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)
        # ------------------------------------------------------------------------------------ #
        # PROJECT WIDGET
        project_widget = ProjectWidget()
        self.layout().addWidget(project_widget)


        self.project_splitter = Splitter("MAYA OPTIONS")
        self.layout().addWidget(self.project_splitter)

        self.project_splitter = Splitter("RENDERMAN OPTIONS")
        self.layout().addWidget(self.project_splitter)

        # ------------------------------------------------------------------------------------ #
        self.version_layout = qg.QHBoxLayout()
        self.version_layout.setContentsMargins(4,0,4,0)
        self.version_layout.setSpacing(2)
        self.layout().addLayout(self.version_layout)

        self.version_text_lb = qg.QLabel('RMS VERSION:')
        self.version_combo  = qg.QComboBox()
        self.version_combo.addItem('20.5')
        self.version_combo.addItem('20.6')
        self.version_combo.setMinimumWidth(300)

        self.version_layout.addSpacerItem(qg.QSpacerItem(5,5,qg.QSizePolicy.Expanding))
        self.version_layout.addWidget(self.version_text_lb)
        self.version_layout.addWidget(self.version_combo)

class BashWidget(qg.QWidget):
    def __init__(self):
        super(BashWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(2)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)


        self.project_splitter = Splitter("BASH OPTIONS")
        self.layout().addWidget(self.project_splitter)

                # ------------------------------------------------------------------------------------ #
        self.version_layout = qg.QHBoxLayout()
        self.version_layout.setContentsMargins(4,0,4,0)
        self.version_layout.setSpacing(2)
        self.layout().addLayout(self.version_layout)

        self.version_text_lb = qg.QLabel('VERSION:')
        self.version_combo  = qg.QComboBox()
        self.version_combo.addItem('20.5')
        self.version_combo.addItem('20.6')
        self.version_combo.setMinimumWidth(300)

        self.version_layout.addSpacerItem(qg.QSpacerItem(5,5,qg.QSizePolicy.Expanding))
        self.version_layout.addWidget(self.version_text_lb)
        self.version_layout.addWidget(self.version_combo)

class ArchiveWidget(qg.QWidget):
    def __init__(self):
        super(ArchiveWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(2)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)


        self.project_splitter = Splitter("ARCHIVE OPTIONS")
        self.layout().addWidget(self.project_splitter)

                # ------------------------------------------------------------------------------------ #
        self.version_layout = qg.QHBoxLayout()
        self.version_layout.setContentsMargins(4,0,4,0)
        self.version_layout.setSpacing(2)
        self.layout().addLayout(self.version_layout)

        self.version_text_lb = qg.QLabel('VERSION:')
        self.version_combo  = qg.QComboBox()
        self.version_combo.addItem('20.5')
        self.version_combo.addItem('20.6')
        self.version_combo.setMinimumWidth(300)

        self.version_layout.addSpacerItem(qg.QSpacerItem(5,5,qg.QSizePolicy.Expanding))
        self.version_layout.addWidget(self.version_text_lb)
        self.version_layout.addWidget(self.version_combo)

class NukeWidget(qg.QWidget):
    def __init__(self):
        super(NukeWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(2)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)


        self.project_splitter = Splitter("NUKE OPTIONS")
        self.layout().addWidget(self.project_splitter)

                # ------------------------------------------------------------------------------------ #
        self.version_layout = qg.QHBoxLayout()
        self.version_layout.setContentsMargins(4,0,4,0)
        self.version_layout.setSpacing(2)
        self.layout().addLayout(self.version_layout)

        self.version_text_lb = qg.QLabel('NUKE VERSION:')
        self.version_combo  = qg.QComboBox()
        self.version_combo.addItem('9.0v8')
        self.version_combo.addItem('9.0v7')
        self.version_combo.setMinimumWidth(300)

        self.version_layout.addSpacerItem(qg.QSpacerItem(5,5,qg.QSizePolicy.Expanding))
        self.version_layout.addWidget(self.version_text_lb)
        self.version_layout.addWidget(self.version_combo)

class TractorWidget(qg.QWidget):
    def __init__(self):
        super(TractorWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(2)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)


        self.project_splitter = Splitter("JOB TRACTOR OPTIONS")
        self.layout().addWidget(self.project_splitter)
        # ------------------------------------------------------------------------------------ #
        self.progect_group_layout = qg.QHBoxLayout()
        self.progect_group_layout.setContentsMargins(4,0,4,0)
        self.progect_group_layout.setSpacing(2)

        self.progect_group_text_lb = qg.QLabel('PROJECT GROUP:')
        self.progect_group_combo  = qg.QComboBox()
        # self.progect_group_combo.setCompleter()
        self.progect_group_combo.addItem('Year 1 Assignment')
        self.progect_group_combo.addItem('Year 2 Assignment')
        self.progect_group_combo.addItem('Year 3 Assignment')
        self.progect_group_combo.addItem('Year 4 Assignment')
        self.progect_group_combo.addItem('Personal Job')

        self.progect_group_combo.setMinimumWidth(300)

        self.progect_group_layout.addSpacerItem(qg.QSpacerItem(5,5,qg.QSizePolicy.Expanding))
        self.progect_group_layout.addWidget(self.progect_group_text_lb)
        self.progect_group_layout.addWidget(self.progect_group_combo)

        self.layout().addLayout(self.progect_group_layout)

class Directory(qg.QFileDialog):
    def __init__(self,startplace=None,title="Select a Directory Please"):
        super(Directory, self).__init__()
        self.setWindowTitle(title)
        self.setModal(True)
        self.setDirectory(startplace)
        self.directory = self.getExistingDirectory(self,title)
        if self.directory:
            print self.directory


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

class Splitter(qg.QWidget):
    def __init__(self, text=None, shadow=True, color=(150, 150, 150)):
        super(Splitter, self).__init__()
        self.setMinimumHeight(2)
        self.setLayout(qg.QHBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
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

