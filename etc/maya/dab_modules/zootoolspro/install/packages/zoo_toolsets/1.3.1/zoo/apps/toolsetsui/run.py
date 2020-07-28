from zoo.apps.toolsetsui import toolsetui
from zoo.libs.maya.qt import mayaui
from zoo.libs.pyqt.widgets import frameless
from zoovendor.six import string_types
# maintain the instance of the ui

win = None


def launch(framelessChecked=True, toolArgs=None):
    """Load the artist GUI for hive.

    :param toolArgs:
    :type toolArgs:
    :param framelessChecked:
    :type framelessChecked:
    :return:
    :rtype: :class:`toolsetui.ToolsetsUI`
    """
    global win
    try:
        win.close()
    except AttributeError:
        pass

    toolArgs = {} or toolArgs

    toolsetIds = [] or toolArgs.get("toolsetIds")
    position = toolArgs.get("position")

    toolsetUi = toolsetui.ToolsetsUI(parent=mayaui.getMayaWindow(),
                                     iconColour=(231, 133, 255),
                                     hueShift=10, framelessChecked=framelessChecked,
                                     toolsetIds=toolsetIds, position=position)

    toolsetui.addToolsetUi(toolsetUi)

    return toolsetUi


def scriptEditorLaunch(toolsetIds=None, position=None):
    """ Run toolset ui through the script editor

    :param toolsetIds: toolset ids to initialise with
    :type toolsetIds: basestring or list[basestring]
    :return:
    :rtype:
    """
    from zoo.apps.toolpalette import run
    a = run.show()

    toolsetIds = [] or toolsetIds
    if isinstance(toolsetIds, string_types):
        toolsetIds = [toolsetIds]

    ret = a.executePluginById("zoo.toolsets", toolsetIds=toolsetIds, position=position)

    return ret


def toggleFrameless(state):
    # Run through
    toolsetWindows = frameless.getFramelessWindows()

    for t in toolsetWindows:
        t.setFrameless(state)


def openTool(toolsetId, position=None):
    """ Opens a tool given the toolset ID name

    :param toolsetId: The name of the toolset ID eg "cleanObjects" or "createTube" etc
    :type toolsetId: string
    """

    toolOpened = toolsetui.runToolset(toolsetId, logWarning=False)
    if not toolOpened:  # then try again and this time open the toolset window first
        scriptEditorLaunch(toolsetId, position=position)
