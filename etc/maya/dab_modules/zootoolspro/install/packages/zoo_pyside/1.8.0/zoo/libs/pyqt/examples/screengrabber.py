from zoo.libs.pyqt.widgets import screengrabber
from zoo.libs.pyqt import utils


if __name__ == "__main__":
    win = screengrabber.ScreenGrabDialog()
    win.exec_()
    print(utils.desktopPixmapFromRect(win.thumbnailRect))