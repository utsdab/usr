from maya import cmds
import maya.mel as mel

from zoo.libs.maya.cmds.renderer.rendererconstants import ARNOLD, RENDERER_PLUGIN


def setGlobalsArnold():
    """Sets the current renderer in the render globals to renderman and builds the core options
    """
    import mtoa.core as core
    core.createOptions()
    cmds.setAttr("defaultRenderGlobals.currentRenderer", "arnold", type="string")


def loadRendererArnold(setZooDefaults=True):
    """Loads the Arnold renderer and sets the render settings to Arnold too
    """
    try:
        cmds.loadPlugin(RENDERER_PLUGIN[ARNOLD])
        setGlobalsArnold()
        if setZooDefaults:
            setArnoldSamples()
        return True
    except RuntimeError:
        return False



def setArnoldSamples(cameraAA=3, diffuse=2, specular=2, transmission=2, sss=2, volumeIndirect=2, progressive=0,
                     adaptiveSampling=0, maxCamAA=20, adaptiveThreshold=0.015):
    """Sets Arnold's Sample and Adaptive Sample settings in the Render Settings window.

    Globals must be set with setGlobalsArnold()

    :param cameraAA: Camera AA samples
    :type cameraAA: int
    :param diffuse: Diffuse samples
    :type diffuse: int
    :param specular: Specular samples
    :type specular: int
    :param transmission: Transmission samples
    :type transmission: int
    :param sss: Sub Surface Scattering samples
    :type sss: int
    :param volumeIndirect: Volume Indirect samples
    :type volumeIndirect: int
    :param progressive: The Progressive Render check box either 0 or 1
    :type progressive: int
    :param adaptiveSampling: The Adaptive Sampling check box, either 0 or 1
    :type adaptiveSampling: int
    :param maxCamAA: The Max. Camera (AA) setting if Adaptive Sampling is on
    :type maxCamAA: int
    :param adaptiveThreshold: Adaptive Threshold setting if Adaptive Sampling is on
    :type adaptiveThreshold: float
    """
    # Sampling
    cmds.setAttr("defaultArnoldRenderOptions.AASamples", cameraAA)
    cmds.setAttr("defaultArnoldRenderOptions.GIDiffuseSamples", diffuse)
    cmds.setAttr("defaultArnoldRenderOptions.GISpecularSamples", specular)
    cmds.setAttr("defaultArnoldRenderOptions.GITransmissionSamples", transmission)
    cmds.setAttr("defaultArnoldRenderOptions.GISssSamples", sss)
    cmds.setAttr("defaultArnoldRenderOptions.GIVolumeSamples", volumeIndirect)
    cmds.setAttr("defaultArnoldRenderOptions.enableProgressiveRender", progressive)
    # Adaptive Sampling
    cmds.setAttr("defaultArnoldRenderOptions.enableAdaptiveSampling", adaptiveSampling)
    cmds.setAttr("defaultArnoldRenderOptions.AASamplesMax", maxCamAA)
    cmds.setAttr("defaultArnoldRenderOptions.AAAdaptiveThreshold", adaptiveThreshold)


def openArnoldRenderview(final=False, ipr=False):
    """Open the Arnold render view and optionally start rendering

    :param final: True will immediately start final rendering an image
    :type final: bool
    :param ipr: True will immediately start IPR rendering an image
    :type ipr: bool
    """
    import mtoa.ui.arnoldmenu as arnoldmenu
    if final or ipr:
        arnoldmenu.arnoldMtoARenderView()
    else:
        arnoldmenu.arnoldOpenMtoARenderView()

