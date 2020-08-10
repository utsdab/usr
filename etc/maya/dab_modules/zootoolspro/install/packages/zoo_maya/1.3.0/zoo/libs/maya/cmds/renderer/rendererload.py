import maya.cmds as cmds
import maya.api.OpenMaya as om2
import maya.mel as mel

from zoo.libs.maya.cmds.renderer.rendererconstants import REDSHIFT, RENDERMAN, ARNOLD, RENDERER_PLUGIN
from zoo.libs.maya.cmds.renderer import arnoldrendersettings, redshiftrendersettings, rendermanrendersettings


def getRendererIsLoaded(rendererNiceName):
    """checks if the renderer by nice name is loaded
    "Arnold", "Renderman", "Redshift"

    :param rendererNiceName: the nice name of the renderer "Redshift", "Arnold"
    :type rendererNiceName: str
    :return loaded: is the renderer loaded?
    :rtype loaded: bool
    """
    loaded = cmds.pluginInfo(RENDERER_PLUGIN[rendererNiceName], query=True, loaded=True)
    return loaded


def loadRenderer(renderer, setZooDefaults=True):
    """Load renderer by it's nice name, "Arnold", "Renderman", "Redshift"

    :param renderer:  renderer nice name "Arnold", "Renderman", "Redshift"
    :type renderer: str
    :return loaded: did the renderer get loaded?
    :rtype loaded: bool
    """
    if getRendererIsLoaded(renderer):
        om2.MGlobal.displayWarning("{} renderer already loaded".format(renderer))
    if renderer == ARNOLD:
        success = arnoldrendersettings.loadRendererArnold(setZooDefaults=setZooDefaults)
    elif renderer == REDSHIFT:
        success = redshiftrendersettings.loadRendererRedshift(setZooDefaults=setZooDefaults)
    elif renderer == RENDERMAN:
        success = rendermanrendersettings.loadRendererRenderman(setZooDefaults=setZooDefaults)
    if not success:
        om2.MGlobal.displayWarning("{} renderer not found in plugin path, "
                                   "it may not be installed".format(renderer))
        return False
    om2.MGlobal.displayInfo("{} Renderer Loaded".format(renderer))
    return True


def getLoadedRenderers():
    """Returns a nice name renderer list of the renderers currently loaded

    :param rendererNiceNameList: the nice name of the renderer "Redshift", "Arnold"
    :type rendererNiceNameList: str
    """
    rendererNiceNameList = list()
    for renderer in RENDERER_PLUGIN:
        if getRendererIsLoaded(renderer):
            rendererNiceNameList.append(renderer)
    return rendererNiceNameList


def unloadRenderer(rendererNiceName, message=True):
    """Unload renderer by it's nice name, "Arnold", "Renderman", "Redshift"

    :param rendererNiceName:  renderer nice name "Arnold", "Renderman", "Redshift"
    :type rendererNiceName: str
    """
    if rendererNiceName == "Renderman":
        mel.eval('rmanPurgePlugin;')
        return
    cmds.unloadPlugin(RENDERER_PLUGIN[rendererNiceName])
    if message:
        om2.MGlobal.displayInfo("{} Renderer Successfully Unloaded".format(rendererNiceName))


def unloadRendererSafe(rendererNiceName):
    """Safe unloads a renderer by checking if it's ok to unload, renderer is by nicename
    "Arnold", "Renderman", "Redshift"

    :param rendererNiceName:  renderer nice name "Arnold", "Renderman", "Redshift"
    :type rendererNiceName: str
    :return unloaded: did the renderer get unloaded?
    :rtype unloaded: bool
    """
    unloaded = True
    if not getRendererIsLoaded(rendererNiceName):
        om2.MGlobal.displayInfo("{} Renderer Was Already Unloaded".format(rendererNiceName))
        return unloaded
    elif rendererNiceName == "Renderman":
        mel.eval('rmanPurgePlugin;')
        return unloaded
    safeUnload = cmds.pluginInfo(RENDERER_PLUGIN[rendererNiceName], query=True, unloadOk=True)
    if not safeUnload:
        om2.MGlobal.displayInfo("{} Renderer Was Not Safe To Unload".format(rendererNiceName))
        return False
    unloadRenderer(rendererNiceName, message=True)
    return True


def printLoadedRenderPlugins():
    """Prints the renderer if it's loaded, will use the renderer nice name.
    """
    renderMessage = "Loaded Renderers: "
    for renderer in RENDERER_PLUGIN:
        if cmds.pluginInfo(RENDERER_PLUGIN[renderer], query=True, loaded=True):
            renderMessage = "{} {}".format(renderMessage, renderer)
    om2.MGlobal.displayInfo(renderMessage)


def safeUnloadAllRenderers():
    """Turns off all the render plugins, best if this happens in an empty scene, can crash Maya
    """
    renderMessage = "Safe Unloaded Renderers: "
    for renderer in RENDERER_PLUGIN:
        if getRendererIsLoaded(renderer):  # next line checks if the renderer is safe to unload
            safeUnload = cmds.pluginInfo(RENDERER_PLUGIN[renderer], query=True, unloadOk=True)
            if safeUnload:
                cmds.unloadPlugin(RENDERER_PLUGIN[renderer])
                if not getRendererIsLoaded(renderer):  # check it definately unloaded
                    renderMessage = "{} {}".format(renderMessage, renderer)
    om2.MGlobal.displayInfo(renderMessage)