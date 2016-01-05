import PySide.QtCore as qc
import PySide.QtGui as qg
import sys
import os
from software.renderfarm.dabtractor.factories import user_factory as ufac
from software.renderfarm.dabtractor.factories import interface_factory as ifac

from functools import partial

class UserWidget(qg.QWidget):
    def __init__(self):
        super(UserWidget, self).__init__()
        self.setLayout(qg.QVBoxLayout())
        self.layout().setSpacing(2)
        self.layout().setContentsMargins(0,0,0,0)
        self.setSizePolicy(qg.QSizePolicy.Minimum,qg.QSizePolicy.Fixed)

        self.project_splitter = ifac.Splitter("USER DETAILS")
        self.layout().addWidget(self.project_splitter)
        # ------------------------------------------------------------------------------------ #
        self.usernumber_text_layout = qg.QHBoxLayout()
        self.usernumber_text_layout.setContentsMargins(4,0,4,0)
        self.usernumber_text_layout.setSpacing(2)

        self.usernumber_text_lb = qg.QLabel('$USER: {}'.format(self._getuser()))
        self.usernumber_text_layout.addSpacerItem(qg.QSpacerItem(5,5,qg.QSizePolicy.Expanding))
        self.usernumber_text_layout.addWidget(self.usernumber_text_lb)
        self.layout().addLayout(self.usernumber_text_layout)
        
        # ------------------------------------------------------------------------------------ #
        self.username_text_layout = qg.QHBoxLayout()
        self.username_text_layout.setContentsMargins(4,0,4,0)
        self.username_text_layout.setSpacing(2)
        self.username_text_lb = qg.QLabel('$USERNAME: {}'.format(self._getusername(self._getuser())))
        self.username_text_layout.addSpacerItem(qg.QSpacerItem(5,5,qg.QSizePolicy.Expanding))
        self.username_text_layout.addWidget(self.username_text_lb)

        self.layout().addLayout(self.username_text_layout)

    def _getusername(self,_user):
        u=ufac.Map()
        self.username=u.getusername(_user)
        return self.username

    def _getuser(self):
        self.usernumber=os.getenv("USER")
        return self.usernumber




class TractorSubmit(qg.QDialog):
    def __init__(self):
        super(TractorSubmit, self).__init__()
        self.setWindowTitle('UTS FARM SUBMIT')
        self.setWindowFlags(qc.Qt.WindowStaysOnTopHint)
        self.setModal(False)
        self.setMinimumHeight(250)
        self.setMinimumWidth(314)
        self.setSizePolicy(qg.QSizePolicy.Minimum,
                           qg.QSizePolicy.Fixed)

        self.setLayout(qg.QVBoxLayout())

        self.layout().setContentsMargins(5,5,5,5)
        self.layout().setSpacing(0)
        self.layout().setAlignment(qc.Qt.AlignTop)

        # ------------------------------------------------------------------------------------ #
        # USER WIDGET
        user_widget = UserWidget()
        self.layout().addWidget(user_widget)


        self.stacked_layout = qg.QStackedLayout()
        self.layout().addLayout(self.stacked_layout)


        button_layout = qg.QHBoxLayout()
        layout_1_bttn = qg.QPushButton('Maya Render')
        layout_2_bttn = qg.QPushButton('Mental Ray')
        layout_3_bttn = qg.QPushButton('Renderman')
        layout_4_bttn = qg.QPushButton('Bash Command')
        layout_5_bttn = qg.QPushButton('Nuke Render')
        layout_6_bttn = qg.QPushButton('Archive')

        button_layout.addWidget(layout_1_bttn)
        button_layout.addWidget(layout_2_bttn)
        button_layout.addWidget(layout_3_bttn)
        button_layout.addWidget(layout_4_bttn)
        button_layout.addWidget(layout_5_bttn)
        button_layout.addWidget(layout_6_bttn)


        self.layout().addLayout(button_layout)
        # ------------------------------------------------------------------------------------ #

        # SCENE WIDGET
        scene_widget = ifac.SceneWidget()
        # self.layout().addWidget(scene_widget)

        # RANGE WIDGET
        range_widget = ifac.RangeWidget()
        # self.layout().addWidget(range_widget)

        # MAYA WIDGET
        maya_widget= ifac.MayaWidget()
        # self.layout().addWidget(maya_widget)

        # MENTALRAY WIDGET
        mentalray_widget= ifac.MentalRayWidget()
        # self.layout().addWidget(maya_widget)


        # RENDERMAN WIDGET
        renderman_widget= ifac.RendermanWidget()
        # self.layout().addWidget(renderman_widget)


        # BASH WIDGET
        bash_widget= ifac.BashWidget()
        # self.layout().addWidget(bash_widget)

        # ARCHIVE WIDGET
        archive_widget= ifac.ArchiveWidget()
        # self.layout().addWidget(bash_widget)

        # NUKE WIDGET
        nuke_widget= ifac.NukeWidget()
        # self.layout().addWidget(bash_widget)

        # TRACTOR WIDGET
        tractor_widget= ifac.TractorWidget()
        # self.layout().addWidget(tractor_widget)

        # FARM JOB EXTRAS WIDGET
        # farm_extras_widget = qg.QWidget()
        # farm_extras_widget.setLayout(qg.QVBoxLayout())
        # farm_extras_widget.layout().setSpacing(2)
        # farm_extras_widget.layout().setContentsMargins(0,0,0,0)

        # TEST WIDGET
        # test_widget = Test()

        # ------------------------------------------------------------------------------------ #

        self.path="/Users/Shared/UTS_Dev/dabrender"
        # d=Directory(startplace=self.path, title="Pick a directory")
        # f=File(startplace=self.path, title="Pick a file")

        self.stacked_layout.addWidget(maya_widget)
        self.stacked_layout.addWidget(mentalray_widget)
        self.stacked_layout.addWidget(renderman_widget)
        self.stacked_layout.addWidget(bash_widget)
        self.stacked_layout.addWidget(nuke_widget)
        self.stacked_layout.addWidget(archive_widget)

        layout_1_bttn.clicked.connect(partial(self.stacked_layout.setCurrentIndex, 0))
        layout_2_bttn.clicked.connect(partial(self.stacked_layout.setCurrentIndex, 1))
        layout_3_bttn.clicked.connect(partial(self.stacked_layout.setCurrentIndex, 2))
        layout_4_bttn.clicked.connect(partial(self.stacked_layout.setCurrentIndex, 3))
        layout_5_bttn.clicked.connect(partial(self.stacked_layout.setCurrentIndex, 4))
        layout_6_bttn.clicked.connect(partial(self.stacked_layout.setCurrentIndex, 5))





def main():

    app = qg.QApplication(sys.argv)
    dialog = TractorSubmit()
    dialog.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()