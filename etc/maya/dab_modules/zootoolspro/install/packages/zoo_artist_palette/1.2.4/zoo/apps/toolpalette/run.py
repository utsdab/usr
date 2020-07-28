from zoo.libs.utils import env

if env.isInMaya():
    from zoo.apps.maya_integrate import palette

paletteUI = None


def show():
    global paletteUI
    if paletteUI:
        return paletteUI
    parent = None
    if env.isInMaya():
        from zoo.apps.maya_integrate import palette
        from zoo.libs.maya.qt import mayaui
        parent = mayaui.getMayaWindow()
        instance = palette.MayaPalette
    else:
        from zoo.apps.toolpalette import palette
        instance = palette.ToolPalette
    tools = instance(parent=parent)
    if not env.isMayapy():
        tools.createMenus()

    paletteUI = tools
    return tools


def close():
    global paletteUI
    try:
        paletteUI.shutdown()
    except AttributeError:
        # happens when zootoolsUi global is none
        pass
    paletteUI = None
