"""
Renderman related shader functions
"""

import maya.mel as mel

import maya.api.OpenMaya as om2
import maya.cmds as cmds
from zoo.libs.maya.cmds.shaders import shaderutils


def loadRenderman():
    """Loads Renderman
    """
    cmds.loadPlugin('RenderMan_for_Maya')
    om2.MGlobal.displayInfo("Renderman Renderer Loaded")


def createPxrSurface(shaderName="shader_PXR", specWeight=0.0, message=True, rgbColor=(.5, .5, .5)):
    """Creates a PxrSurface Shader In Maya

    :param shaderName:The name of the pxr shader in Maya to be created
    :type shaderName:str
    :param message:If on will return the create message to Maya
    :type message:bool
    :return:The name of the pxr shader in Maya that was created
    :type message:str (possibly unicode)
    """
    PxrSurface = cmds.shadingNode('PxrSurface', asShader=True, name=shaderName)
    if message:
        om2.MGlobal.displayInfo('Created Shader: `{}`'.format(PxrSurface))
    return PxrSurface


def assignNewPxrSurface(objList, shaderName="shader_PXR", specWeight=0.0, message=True, rgbColor=(.5, .5, .5),
                        selectShader=True):
    """Creates a PxrSurface Shader and assigns it to the objList

    :param objList: List of object names
    :type shaderName: list
    :param shaderName:The name of the PxrSurface shader in Maya to be created
    :type shaderName:str
    :param specOff: If True the specular weight is set to 0 (off)
    :type specOff: bool
    :param message: If on will return the create message to Maya
    :type message: bool
    :return:The name of the RedshiftMaterial shader in Maya that was created
    :type message:str (possibly unicode)
    """
    selObjs = cmds.ls(selection=True)  # get current selection
    PxrSurface = createPxrSurface(shaderName=shaderName, specWeight=specWeight,
                                  message=message, rgbColor=rgbColor)
    if objList:
        cmds.select(objList, replace=True)  # select temporarily the objList
        shaderutils.assignShaderSelected(PxrSurface)
    # return current selection
    cmds.select(selObjs, replace=True)
    if selectShader:
        cmds.select(PxrSurface, replace=True)
    if message:
        om2.MGlobal.displayInfo('Success: Created New Shader: `{}`, and assigned to {}'.format(PxrSurface, objList))
    return PxrSurface


def assignSelectedNewPxrSurface(shaderName="shader_PXR", specWeight=0.0, message=True, rgbColor=(.5, .5, .5)):
    """Creates a PxrSurface Shader and assigns it to the current selection

    :param shaderName: The name of the PxrSurface shader in Maya to be created
    :type shaderName: str
    :param specOff: If True the specular weight is set to 0 (off)
    :type specOff: bool
    :param message:If on will return the create message to Maya
    :type message: bool
    :return shaderName: The name of the redshift shader in Maya that was created
    :type shaderName: str
    """
    selObjs = cmds.ls(selection=True)
    shaderName = assignNewPxrSurface(selObjs, shaderName=shaderName, specWeight=specWeight,
                                     message=message, rgbColor=rgbColor)
    return shaderName


def setShadowHoldout(objList, message=True):
    """Creates a shadow holdout (shadow matte) for the selected objects.
    In Renderman the mesh attribute Mesh Shape > Render Stats > Hold-Out is ticked to be on.
    Renderman will Render the shader as per usual but it will be invisible.
    So the reflective properties of the object/s are set via their shaders.

    :param objList: List of object names
    :type shaderName: list
    :param message: If on will return the create message to Maya
    :type message: bool
    :return objList:
    :rtype objList:
    """
    selObjs = cmds.ls(selection=True)  # get current selection
    cmds.select(objList, replace=True)  # select temporarily the objList
    mel.eval('rmanCreateHoldout;')  # in Renderman this creates the holdout on selected objects
    cmds.select(selObjs, replace=True)  # return current selection
    if message:
        om2.MGlobal.displayInfo('Success: Holdout has been set on objects: `{}`'.format(objList))


def setSelectedShadowHoldout(message=True):
    """Creates a shadow holdout (shadow matte) for the selected objects.
    In Renderman the mesh attribute Mesh Shape > Render Stats > Hold-Out is ticked to be on.
    Renderman will Render the shader as per usual but it will be invisible.
    So the reflective properties of the object/s are set via their shaders.

    :param message:If on will return the create message to Maya
    :type message: bool
    :return selObjs: the objects set to holdout on
    :rtype selObjs: list
    """
    selObjs = cmds.ls(selection=message)
    setShadowHoldout(selObjs, message=message)
    return selObjs


