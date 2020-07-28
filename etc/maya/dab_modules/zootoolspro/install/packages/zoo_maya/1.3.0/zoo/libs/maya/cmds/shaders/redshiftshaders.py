"""
Redshift related shader functions
"""

import maya.api.OpenMaya as om2
import maya.cmds as cmds
from zoo.libs.maya.cmds.shaders import shaderutils

REDSHIFTSUFFIX = "RS"  # the suffix on redshift shaders


def loadRedshift():
    """Load Redshift
    """
    cmds.loadPlugin('redshift4maya')
    mel.eval('redshiftGetRedshiftOptionsNode(true)')
    om2.MGlobal.displayInfo("Redshift Renderer Loaded")


def createRedshiftMaterial(shaderName="shader_RS", specWeight=0.0, message=True, rgbColor=(.5, .5, .5)):
    """Creates a RedshiftMaterial Shader In Maya

    :param shaderName:The name of the RedshiftMaterial shader in Maya to be created
    :type shaderName:str
    :param specOff: If True the specular weight is set to 0 (off)
    :type specOff: bool
    :param message:If on will return the create message to Maya
    :type message:bool
    :return:The name of the redshift material shader in Maya that was created
    :type message:str (possibly unicode)
    """
    redshiftMaterial = cmds.shadingNode('RedshiftMaterial', asShader=True, name=shaderName)
    if message:
        om2.MGlobal.displayInfo('Created Shader: `{}`'.format(redshiftMaterial))
    cmds.setAttr("{}.refl_weight".format(redshiftMaterial), specWeight)  # spec weight
    # colorSrgbInt = colour.convertColorSrgbToLinear(colorSrgbInt)  # linearize colors
    # diffuse
    cmds.setAttr("{}.diffuse_color".format(redshiftMaterial), rgbColor[0], rgbColor[1], rgbColor[2], type="double3")
    return redshiftMaterial


def createRedshiftMatteShadowCatcher(shaderName="shadowMatte_RS", message=True):
    """Creates a RedshiftMatteShadowCatcher Shader In Maya
    Shadow mattes are for shadows only and or reflections, usually for comping

    :param shaderName:The name of the RedshiftMatteShadowCatcher shader in Maya to be created
    :type shaderName:str
    :param message:If on will return the create message to Maya
    :type message:bool
    :return:The name of the RedshiftMatteShadowCatcher shader in Maya that was created
    :type message:str (possibly unicode)
    """
    shaderName = cmds.shadingNode('RedshiftMatteShadowCatcher', asShader=True, name=shaderName)
    if message:
        om2.MGlobal.displayInfo('Created Shader: `{}`'.format(shaderName))
    return shaderName


def assignNewRedshiftMaterial(objList, shaderName="shader_RS", specWeight=0.0, message=True, rgbColor=(.5, .5, .5),
                              selectShader=True):
    """Creates a RedshiftMaterial Shader and assigns it to the objList

    If None will just create the shader

    :param objList: List of object names
    :type shaderName: list
    :param shaderName:The name of the RedshiftMaterial shader in Maya to be created
    :type shaderName:str
    :param specOff: If True the specular weight is set to 0 (off)
    :type specOff: bool
    :param message:If on will return the create message to Maya
    :type message:bool
    :return:The name of the RedshiftMaterial shader in Maya that was created
    :type message:str (possibly unicode)
    """
    selObjs = cmds.ls(selection=True)  # get current selection
    redshiftMaterial = createRedshiftMaterial(shaderName=shaderName, specWeight=specWeight,
                                              message=message, rgbColor=rgbColor)
    if objList:
        cmds.select(objList, replace=True)  # select temporarily the objList
        shaderutils.assignShaderSelected(redshiftMaterial)
    # return current selection
    cmds.select(selObjs, replace=True)
    if selectShader:
        cmds.select(redshiftMaterial, replace=True)
    if message:
        om2.MGlobal.displayInfo('Created New Shader: `{}`, and assigned to {}'.format(redshiftMaterial, objList))
    return redshiftMaterial


def assignNewRedshiftMatteShadowCatcher(objList, shaderName="shadowMatte_RS", message=True, selectShader=True):
    """Creates a RedshiftMatteShadowCatcher Shader and assigns it to the objList
    Shadow mattes are for shadows only and or reflections, usually for comping

    :param objList: List of object names
    :type shaderName: list
    :param shaderName:The name of the RedshiftMatteShadowCatcher shader in Maya to be created
    :type shaderName:str
    :param message:If on will return the create message to Maya
    :type message:bool
    :return:The name of the RedshiftMatteShadowCatcher shader in Maya that was created
    :type message:str (possibly unicode)
    """
    selObjs = cmds.ls(selection=True)  # get current selection
    shaderName = createRedshiftMatteShadowCatcher(shaderName=shaderName, message=message)
    cmds.select(objList, replace=True)  # select temporarily the objList
    shaderutils.assignShaderSelected(shaderName)
    cmds.select(selObjs, replace=True)  # return current selection
    if selectShader:
        cmds.select(shaderName, replace=True)
    if message:
        om2.MGlobal.displayInfo('Created New Matte Shadow Catcher Shader: `{}`, '
                                'and assigned to {}'.format(shaderName, objList))
    return shaderName


def assignSelectedNewRedshiftMaterial(shaderName="shader_RS", specWeight=0.0, message=True, rgbColor=(.5, .5, .5)):
    """Creates a RedshiftMaterial Shader and assigns it to the current selection

    :param shaderName: The name of the RedshiftMaterial shader in Maya to be created
    :type shaderName: str
    :param specOff: If True the specular weight is set to 0 (off)
    :type specOff: bool
    :param message:If on will return the create message to Maya
    :type message: bool
    :return shaderName: The name of the redshift shader in Maya that was created
    :type shaderName: str
    """

    selObjs = cmds.ls(selection=True)
    shaderName = assignNewRedshiftMaterial(selObjs, shaderName=shaderName, specWeight=specWeight,
                                           message=message, rgbColor=rgbColor)
    return shaderName


def assignSelectedNewRedshiftMatteShadowCatcher(shaderName="shadowMatte_RS", message=True):
    """Creates a RedshiftMatteShadowCatcher Shader and assigns it to the current selection
    Shadow mattes are for shadows only and or reflections, usually for comping

    :param shaderName: The name of the RedshiftMatteShadowCatcher shader in Maya to be created
    :type shaderName: str
    :param message:If on will return the create message to Maya
    :type message: bool
    :return shaderName: The name of the RedshiftMatteShadowCatcher shader in Maya that was created
    :type shaderName: str
    """
    selObjs = cmds.ls(selection=True)
    shaderName = assignNewRedshiftMatteShadowCatcher(selObjs, shaderName=shaderName, message=message)
    return shaderName




