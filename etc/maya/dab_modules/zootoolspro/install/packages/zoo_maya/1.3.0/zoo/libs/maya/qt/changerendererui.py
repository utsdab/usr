from maya.api import OpenMaya as om2

from zoo.libs.pyqt.widgets.popups import MessageBox_ok
from zoo.libs.maya.cmds.renderer import rendererload


# ------------------------------------
# POPUP WINDOW
# ------------------------------------

def ui_loadRenderer(renderer):
    """Popup window for loading a renderer

    :param renderer: Renderer nicename
    :type renderer: str
    :return okPressed: Was the ok button pressed or not
    :rtype okPressed: bool
    """
    message = "The {} renderer isn't loaded. Load now?".format(renderer)
    # parent is None to parent to Maya to fix stylesheet issues
    okPressed = MessageBox_ok(windowName="Load Renderer", parent=None, message=message)
    return okPressed


def checkRenderLoaded(renderer, bypassWindow=False):
    """Checks that the renderer is loaded, if not opens a window asking the user to load it

    :param renderer: the nice name of the renderer "Arnold" or "Redshift" etc
    :type renderer: str
    :param bypassWindow: If True don't show the popup window, just return if the renderer is loaded or not
    :type bypassWindow: bool
    :return rendererLoaded: True if the renderer is loaded
    :rtype rendererLoaded: bool
    """
    if not rendererload.getRendererIsLoaded(renderer):
        if bypassWindow:
            return False
        okPressed = ui_loadRenderer(renderer)
        if okPressed:
            success = rendererload.loadRenderer(renderer)
            return success
        return False
    return True


# ------------------------------------
# RENDERER - AND SEND/RECEIVE ALL TOOLSETS
# ------------------------------------


def globalChangeRenderer(renderer, toolsets, generalSettingsPrefsData, saveKey):
    """Updates all GUIs with the current renderer

    From toolset code run:

        toolsets = toolsetui.toolsets(attr="global_receiveRendererChange")
        self.generalSettingsPrefsData = elements.globalChangeRenderer(self.properties.rendererIconMenu.value,
                                                                      toolsets,
                                                                      self.generalSettingsPrefsData,
                                                                      pc.PREFS_KEY_RENDERER)

    :param renderer: The renderer nice name to change to for all UIs
    :type renderer: str
    :param toolsets: A list of all the toolset UIs to change
    :type toolsets:
    :param generalSettingsPrefsData: The preferences data file
    :type generalSettingsPrefsData: object
    :param saveKey: The dictionary key to save to, will depend on the preferences setting to save
    :type saveKey: str
    :return generalSettingsPrefsData: The preferences data file now updated
    :rtype generalSettingsPrefsData: object
    """
    for tool in toolsets:
        tool.global_receiveRendererChange(renderer)
    # save renderer to the general settings preferences .pref json
    if not generalSettingsPrefsData.isValid():  # should be very rare
        om2.MGlobal.displayError("The preferences object is not valid")
        return
    generalSettingsPrefsData[saveKey] = renderer
    generalSettingsPrefsData.save(indent=True)  # save and format nicely
    om2.MGlobal.displayInfo("Preferences Saved: Global renderer saved as "
                            "`{}`".format(renderer))
    return generalSettingsPrefsData
