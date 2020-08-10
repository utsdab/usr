# maintain the instance of the ui
from zoo.apps.preferencesui import preferencesui
from zoo.libs.maya.qt import mayaui

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

    prefui = preferencesui.PreferencesUI(parent=mayaui.getMayaWindow(),
                                         framelessChecked=framelessChecked)

    return prefui


def scriptEditorLaunch():
    from zoo.apps.toolpalette import run
    a = run.show()
    return a.executePluginById("zoo.preferencesui")

