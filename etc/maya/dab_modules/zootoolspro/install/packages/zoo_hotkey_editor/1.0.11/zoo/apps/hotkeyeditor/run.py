# maintain the instance of the ui
from zoo.apps.hotkeyeditor import hotkeyeditorui
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

    toolsetUi = hotkeyeditorui.HotkeyEditorUI(parent=mayaui.getMayaWindow(),
                                              framelessChecked=framelessChecked)

    return toolsetUi


def scriptEditorLaunch():
    from zoo.apps.toolpalette import run

    a = run.show()
    toolDef = a.loadPlugin("HotkeyEditorUi")._execute()
