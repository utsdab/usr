# @todo mouse tracking
import sys

from Qt import Phonon
from Qt import QtCore, QtGui


class VideoPlayer(Phonon.VideoPlayer):
    def __init__(self, cat, parent=None):
        super(VideoPlayer, self).__init__(cat, parent)
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.isPlaying():
                self.pause()
            else:
                self.play()


class QPlayer(QtGui.QWidget):
    def __init__(self, filePath, parent=None):
        super(QPlayer, self).__init__(parent)
        self.filePath = filePath
        self.player = VideoPlayer(Phonon.VideoCategory, self)
        self.initUi()
        mediaSource = Phonon.MediaSource(filePath)
        self.player.play(mediaSource)

    def initUi(self):

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.player)

        self.setLayout(layout)

    def setSource(self, filepath):
        self.filePath = filepath
        mediaSource = Phonon.MediaSource(filepath)
        self.player.load(mediaSource)

    def play(self, filePath=""):
        if not filePath:
            self.player.play()
        else:
            self.player.play(filePath)

    def pause(self):
        self.player.pause()

    def stop(self):
        self.player.stop()


if __name__ == "__main__":
    from PyQt4 import QtGui

    qapp = QtGui.QApplication(sys.argv)
    w = QPlayer("")

    w.show()
    sys.exit(qapp.exec_())
