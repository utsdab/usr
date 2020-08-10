from maya import cmds
from maya.api import OpenMaya as om2
import maya.mel as mel

from zoo.libs.maya.cmds.renderer.rendererconstants import RENDERMAN, RENDERER_PLUGIN


def setGlobalsRenderman():
    """Sets the current renderer in the render globals to renderman
    """
    try:
        import rfm2.render
        rfm2.render_with_renderman()
    except:
        pass
    cmds.setAttr("defaultRenderGlobals.currentRenderer", "renderman", type="string")
    # mel.eval('unifiedRenderGlobalsWindow();')


def loadRendererRenderman(setZooDefaults=True):
    """Loads the Renderman renderer and sets the render settings to Renderman too
    """
    try:
        cmds.loadPlugin(RENDERER_PLUGIN[RENDERMAN])
        setGlobalsRenderman()
        if setZooDefaults:
            setMinMaxSamples()
        return True
    except RuntimeError:
        return False


def setMinMaxSamples(maxSamples=256, minSamples=0, pixelVariance=0.015, iprMax=256, iprPixelVariance=0.015,
                     message=-True):
    """Sets the Renderman max and min samples for regular and IPR rendering

    :param maxSamples: The maximum samples for full quality Renderman renders
    :type maxSamples: int
    :param minSamples: The minimum samples for full quality Renderman renders
    :type minSamples: int
    :param pixelVariance: The pixel variance for full quality Renderman renders
    :type pixelVariance: float
    :param iprMax: The maximum samples for IPR (interactive) Renderman renders
    :type iprMax: int
    :param iprPixelVariance: The pixel variance for IPR Renderman renders
    :type iprPixelVariance: float
    :param message: Report a message to the user?
    :type message: float
    :return success: True if successfully completed, can fail easily if Renderman Globals are not in the scene
    :rtype success: bool
    """
    try:  # Will fail on scene load as the Renderman Globals need to be built first
        cmds.setAttr("rmanGlobals.hider_minSamples", minSamples)
        cmds.setAttr("rmanGlobals.hider_maxSamples", maxSamples)
        cmds.setAttr("rmanGlobals.ri_pixelVariance", pixelVariance)
        cmds.setAttr("rmanGlobals.ipr_hider_maxSamples", iprMax)
        cmds.setAttr("rmanGlobals.ipr_ri_pixelVariance", iprPixelVariance)
        return True
    except RuntimeError:
        cmds.setAttr("defaultRenderGlobals.currentRenderer", "renderman", type="string")
        if message:
            om2.MGlobal.displayWarning("Warning Settings have not been set, Renderman Globals have now been built. "
                                       "Set settings again.")
        return False


def openRendermanRenderview(final=False, ipr=False):
    """Open the Renderman render view and optionally start rendering

    :param final: True will immediately start final rendering an image
    :type final: bool
    :param ipr: True will immediately start IPR rendering an image
    :type ipr: bool
    """
    if ipr:
        mel.eval('rmanIprStartCmd();')
    elif final:
        mel.eval('rmanPreviewStartCmd();')
    else:
        try:
            import rfm2
            rfm2.render.show_it()
        except:
            mel.eval('rmanIprStartCmd();')
