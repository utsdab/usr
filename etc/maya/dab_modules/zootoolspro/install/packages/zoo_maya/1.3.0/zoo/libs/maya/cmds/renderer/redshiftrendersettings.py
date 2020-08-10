from maya import cmds
import maya.mel as mel
from maya.api import OpenMaya as om2

from zoo.libs.maya.cmds.renderer.rendererconstants import REDSHIFT, RENDERER_PLUGIN


def setGlobalsRedshift():
    """Sets the current renderer in the render globals to Redshift and builds the core options
    """
    cmds.setAttr("defaultRenderGlobals.currentRenderer", "redshift", type="string")
    if not cmds.objExists("redshiftOptions"):  # Redshift need to create the redshiftOptions node if doesn't exist
        mel.eval('redshiftGetRedshiftOptionsNode(true);')


def loadRendererRedshift(setZooDefaults=True):
    """Loads the Redshift renderer and sets the render settings to Redshift too
    """
    try:
        cmds.loadPlugin(RENDERER_PLUGIN[REDSHIFT])
        setGlobalsRedshift()
        if setZooDefaults:
            setBounces()
            setIPRMaxPasses()
            setMinMaxSamples()
        return True
    except RuntimeError:
        return False


def setBounces(bounces=3, primaryEngine=4, secondaryEngine=4, message=True):
    """Sets the GI bounces in Redshift

    Primary Engine:

        0: None
        1: Photon Map
        3: Irradiance Cache
        4: Brute Force

    Secondary Engine:

        0: None
        1: Photon Map
        2: Irradiance Point Cloud
        4: Brute Force

    :param bounces: The number of bounces
    :type bounces: int
    :param primaryEngine: The primary engine to use, see documentation above, represents the combo box
    :type primaryEngine: int
    :param secondaryEngine: The secondary engine to use, see documentation above, represents the combo box
    :type secondaryEngine: int
    :param message: Report a message to the user?
    :type message: float
    :return success: True if successfully completed, can fail easily if Renderman Globals are not in the scene
    :rtype success: bool
    """
    try:  # Will fail on load renderer as the Redshift Options need to be built first
        if bounces >= 1:
            cmds.setAttr("redshiftOptions.primaryGIEngine", primaryEngine)  # Primary GI Engine to Brute Force
        else:
            cmds.setAttr("redshiftOptions.primaryGIEngine", 0)  # set to None
        if bounces >= 2:
            cmds.setAttr("redshiftOptions.secondaryGIEngine", secondaryEngine)  # Secondary GI Engine to Brute Force
        else:
            cmds.setAttr("redshiftOptions.secondaryGIEngine", 0)  # set to None
        cmds.setAttr("redshiftOptions.numGIBounces", bounces)
        return True
    except RuntimeError:
        setGlobalsRedshift()  # the redshiftOptions needs to build
        if message:
            om2.MGlobal.displayWarning("Warning Settings have not been set, Renderman Globals have now been built. "
                                       "Set settings again.")
            return False


def setIPRMaxPasses(passes=256, forceProgressive=1, message=True):
    """Sets the IPR passes in Redshift

    :param passes: The amount of passes to use
    :type passes: int
    :param forceProgressive: The toggle for force progressive checkbox 1 or 0
    :type forceProgressive: int
    :param message: Report a message to the user?
    :type message: float
    :return success: True if successfully completed, can fail easily if Renderman Globals are not in the scene
    :rtype success: bool
    """
    try:  # Will fail on load renderer as the Redshift Options need to be built first
        cmds.setAttr("redshiftOptions.autoProgressiveRenderingIprEnabled", forceProgressive)
        cmds.setAttr("redshiftOptions.progressiveRenderingNumPasses", passes)
        return True
    except RuntimeError:
        setGlobalsRedshift()  # the redshiftOptions needs to build
        if message:
            om2.MGlobal.displayWarning("Warning Settings have not been set, Renderman Globals have now been built. "
                                       "Set settings again.")
        return False


def setMinMaxSamples(maxSamples=256, minSamples=64, adaptiveThreshold=0.010, message=True):
    """Sets the minimum and maximum samples for Redshift

    :param minSamples: The minimum samples number under unified sampling
    :type minSamples: int
    :param maxSamples: The maximum samples number under unified sampling
    :type maxSamples: int
    :param adaptiveThreshold: The Adaptive Error Threshold samples number under unified sampling
    :type adaptiveThreshold: float
    :param message: Report a message to the user?
    :type message: float
    :return success: True if successfully completed, can fail easily if Renderman Globals are not in the scene
    :rtype success: bool
    """
    try:  # Will fail on load renderer as the Redshift Options need to be built first
        cmds.setAttr("redshiftOptions.unifiedMinSamples", minSamples)
        cmds.setAttr("redshiftOptions.unifiedMaxSamples", maxSamples)
        cmds.setAttr("redshiftOptions.unifiedAdaptiveErrorThreshold", adaptiveThreshold)
        return True
    except RuntimeError:
        setGlobalsRedshift()  # the redshiftOptions needs to build
        if message:
            om2.MGlobal.displayWarning("Warning Settings have not been set, Renderman Globals have now been built. "
                                       "Set settings again.")
        return False


def openRedshiftRenderview(final=False, ipr=False):
    """Open the redshift render view and optionally start rendering

    :param final: True will immediately start final rendering an image
    :type final: bool
    :param ipr: True will immediately start IPR rendering an image
    :type ipr: bool
    """
    if ipr:
        mel.eval('redshiftRvRender "ipr" "";')
    elif final:
        mel.eval('redshiftRvRender "render" "";')
    else:
        mel.eval('redshiftRvShow;')
