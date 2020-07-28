# maintain the instance of the ui
from zoo.libs.maya.qt import mayaui

from zoo.apps.imagebrowserui import imagebrowserui

win = None


def launch(framelessChecked=True):
    """Load the artist GUI for hive.

    :return:
    :rtype: :class:`toolsetui.ToolsetsUI`
    """
    global win
    try:
        win.close()
    except AttributeError:
        pass

    toolsetUi = imagebrowserui.ImageBrowserUI(parent=mayaui.getMayaWindow(),
                                              framelessChecked=framelessChecked)

    return toolsetUi


def scriptEditorLaunch(browserType=None):
    from zoo.apps.toolpalette import run

    a = run.show()
    toolDef = a.loadPlugin("ImageBrowserUi")._execute(browserType)
