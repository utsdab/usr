"""
Arnold related shader functions
"""

import maya.api.OpenMaya as om2
import maya.cmds as cmds
from zoo.libs.maya.cmds.shaders import shaderutils
from zoo.libs.utils import colour


def loadArnold():
    """Load Arnold
    """
    cmds.loadPlugin('mtoa')
    om2.MGlobal.displayInfo("Arnold Renderer Loaded")


def mtoaVersionNumber():
    """Returns the version number of the mtoa plugin and not Arnold!

    :return major: the major version number 4.2.1 will be 4
    :rtype major: int
    :return minor: the minor version number 4.2.1 will be 2
    :rtype minor: int
    :return patch: the major version number 4.2.1 will be 1
    :rtype patch: int
    """
    versionNumber = cmds.pluginInfo('mtoa', query=True, version=True)
    versionList = versionNumber.split(".")
    major = int(versionList[0])
    minor = int(versionList[1])
    patch = int(versionList[-1])
    return major, minor, patch


def createAiStandardSurface(shaderName="shader_ARN", specWeight=0.0, message=True, rgbColor=(.5, .5, .5)):
    """Creates a aiSurfaceStandard Shader In Maya

    :param shaderName:The name of the aiSurfaceStandard shader in Maya to be created
    :type shaderName:str
    :param specOff: If True the specular weight is set to 0 (off)
    :type specOff: bool
    :param message:If on will return the create message to Maya
    :type message:bool
    :return:The name of the pxr shader in Maya that was created
    :type message:str (possibly unicode)
    """
    shaderName = cmds.shadingNode('aiStandardSurface', asShader=True, name=shaderName)
    if message:
        om2.MGlobal.displayInfo('Created Shader: `{}`'.format(shaderName))
    cmds.setAttr("{}.specular".format(shaderName), specWeight)  # spec weight
    rgbColor = colour.convertColorSrgbToLinear(rgbColor)  # linearize colors
    cmds.setAttr("{}.baseColor".format(shaderName), rgbColor[0], rgbColor[1], rgbColor[2], type="double3")  # specW0
    return shaderName


def createAiShadowMatte(shaderName="shadowMatte_ARN", message=True):
    """Creates a aiShadowMatte Shader In Maya
    Shadow mattes are for shadows only and or reflections, usually for comping

    :param shaderName:The name of the aiSurfaceStandard shader in Maya to be created
    :type shaderName:str
    :param message:If on will return the create message to Maya
    :type message:bool
    :return:The name of the pxr shader in Maya that was created
    :type message:str (possibly unicode)
    """
    shaderName = cmds.shadingNode('aiShadowMatte', asShader=True, name=shaderName)
    if message:
        om2.MGlobal.displayInfo('Created Shadow Matte Shader: `{}`'.format(shaderName))
    return shaderName


def assignNewAiStandardSurface(objList, shaderName="shader_ARN", specWeight=0.0, message=True, rgbColor=(.5, .5, .5),
                               selectShader=True):
    """Creates a aiStandardSurface Shader and assigns it to the objList

    :param objList: List of object names
    :type shaderName: list
    :param shaderName: The name of the aiStandardSurface shader in Maya to be created
    :type shaderName: str
    :param specOff: If True the specular weight is set to 0 (off)
    :type specOff: bool
    :param message: If on will return the create message to Maya
    :type message: bool
    :return shaderName: The name of the aiStandardSurface shader in Maya that was created
    :type shaderName: str
    """
    selObjs = cmds.ls(selection=True)  # get current selection
    shaderName = createAiStandardSurface(shaderName=shaderName, specWeight=specWeight,
                                         message=message, rgbColor=rgbColor)
    if objList:
        cmds.select(objList, replace=True)  # select temporarily the objList
        shaderutils.assignShaderSelected(shaderName)
    # return current selection
    cmds.select(selObjs, replace=True)
    if selectShader:
        cmds.select(shaderName, replace=True)
    if message:
        om2.MGlobal.displayInfo('Created New Shader: `{}`, and assigned to {}'.format(shaderName, objList))
    return shaderName


def assignNewAiShadowMatte(objList, shaderName="shadowMatte_ARN", message=True, selectShader=True):
    """Creates a aiShadowMatte Shader and assigns it to the objList
    Shadow mattes are for shadows only and or reflections, usually for comping

    :param objList: List of object names
    :type shaderName: list
    :param shaderName: The name of the aiShadowMatte shader in Maya to be created
    :type shaderName: str
    :param message: If on will return the create message to Maya
    :type message: bool
    :return shaderName: The name of the aiShadowMatte shader in Maya that was created
    :type shaderName: str
    """
    selObjs = cmds.ls(selection=True)  # get current selection
    shaderName = createAiShadowMatte(shaderName=shaderName, message=message)
    cmds.select(objList, replace=True)  # select temporarily the objList
    shaderutils.assignShaderSelected(shaderName)
    cmds.select(selObjs, replace=True)  # return current selection
    if selectShader:
        cmds.select(shaderName, replace=True)
    if message:
        om2.MGlobal.displayInfo('Created New Shadow Matte Shader: `{}`, and assigned to {}'.format(shaderName, objList))


def assignSelectedNewAiStandardSurface(shaderName="shader_ARN", specWeight=0.0, message=True, rgbColor=(.5, .5, .5)):
    """Creates a aiStandardSurface Shader and assigns it to the current selection

    :param shaderName: The name of the aiStandardSurface shader in Maya to be created
    :type shaderName: str
    :param specOff: If True the specular weight is set to 0 (off)
    :type specOff: bool
    :param message: If on will return the create message to Maya
    :type message: bool
    :return shaderName: The name of the aiStandardSurface shader in Maya that was created
    :type shaderName: str
    """
    selObjs = cmds.ls(selection=True)
    shaderName = assignNewAiStandardSurface(selObjs, shaderName=shaderName, specWeight=specWeight,
                                            message=message, rgbColor=rgbColor)
    return shaderName


def assignSelectedNewAiShadowMatte(shaderName="shadowMatte_ARN", message=True):
    """Creates a aiShadowMatte Shader and assigns it to the current selection
    Shadow mattes are for shadows only and or reflections, usually for comping

    :param shaderName: The name of the aiShadowMatte shader in Maya to be created
    :type shaderName: str
    :param message: If on will return the create message to Maya
    :type message: bool
    :return shaderName: The name of the aiShadowMatte shader in Maya that was created
    :type shaderName: str
    """
    selObjs = cmds.ls(selection=True)
    shaderName = assignNewAiShadowMatte(selObjs, shaderName=shaderName, message=message)
    return shaderName


# -------------------------
# ARNOLD CHANNEL BOX ATTRS HIDE
# -------------------------


def showHideArnoldChannelAttrs(showAttr=False):
    """Hides (or shows) all the Arnold attributes that annoyingly get keys in rigs

    :param showAttr: if False will hide all the attributes in the scene, True will unhide
    :type showAttr: bool
    """
    attrList = ["ai_shadow_density", "ai_exposure", "aiUseSubFrame", "aiOverrideLightLinking", "aiOverrideShaders",
                "aiUseFrameExtension", "aiFrameNumber", "aiFrameOffset", "aiOverrideNodes", "aiOverrideReceiveShadows",
                "aiOverrideDoubleSided", "aiOverrideSelfShadows", "aiOverrideOpaque", "aiOverrideMatte"]
    crvAttrList = ["aiRenderCurve", "aiCurveWidth", "aiSampleRate", "aiCurveShaderR", "aiCurveShaderG",
                   "aiCurveShaderB"]
    meshes = cmds.ls(type="mesh")
    nurbsCrvs = cmds.ls(type="nurbsCurve")
    for mesh in meshes:
        for attr in attrList:
            cmds.setAttr(".".join([mesh, attr]), channelBox=showAttr)
            cmds.setAttr(".".join([mesh, attr]), keyable=showAttr)
    for crv in nurbsCrvs:
        for attr in crvAttrList:
            cmds.setAttr(".".join([crv, attr]), channelBox=showAttr)
            cmds.setAttr(".".join([crv, attr]), keyable=showAttr)

