"""Toggles/Swaps Shaders in a scene, usually given by two suffix's
Can mod this later for doing various things with two sets of shaders such as linking shaders to
shading groups of Arnold and Redshift too.
Main shader toggle is most handy in Renderman where shaders cannot be overidden for the viewport in the shading
group.
"""

import maya.cmds as cmds
import maya.api.OpenMaya as om2

from zoo.libs.maya.cmds.shaders import shaderutils
from zoo.libs.maya.cmds.shaders import createshadernetwork
from zoo.libs.maya.cmds.objutils import namewildcards


def findFirstWildcardShader(suffix1, suffix2):
    """This checks the scene for polygon meshes and returns the first suffix that it finds in a shader name
    This may be either `suffix1` or `suffix2`

    :param suffix1: the name of the first suffix
    :type suffix1: str
    :param suffix2: the name of the second suffix
    :type suffix2: str
    :return suffix: either the name of suffix1 or suffix1
    :rtype suffix: str
    """
    allGeo = cmds.ls(type="mesh")  # get all meshes in the scene
    shaderList = shaderutils.getShadersObjList(allGeo)  # get shaders of objects
    if not shaderList:
        return
    for shader in shaderList:
        if suffix1 in shader:
            return suffix1
        if suffix2 in shader:
            return suffix2


def toggleShader(shaderFromSuffix, shaderToSuffix):
    """Toggles all shaders in a scene swapping the shaders with the given suffix's.
    Swap goes from shaderFrom and applies it to shaderToSuffix so the shaderToSuffix are assigned
    Only works on polygons, not currently NURBS

    :param shaderFromSuffix:
    :type shaderFromSuffix:
    :param shaderToSuffix:
    :type shaderToSuffix:
    """
    shadersAssigned = 0
    shaderFromList = namewildcards.getWildcardObjs(shaderFromSuffix)  # find all shaders with suffix
    shaderFromList = cmds.ls(shaderFromList, materials=True)  # check legitimate shaders filtering out other nodes
    for shader in shaderFromList:
        shaderGroupName = shaderutils.getShadingGroupFromShader(shader)  # get shading group from shader
        if not shaderGroupName:  # create shading group
            shaderGroupName = createshadernetwork.createSGOnShader(shader)
        objFaceList = shaderutils.getObjectsFacesAssignedToSG(shaderGroupName)  # get objects/faces shader assigned
        if not objFaceList:  #select objects and faces
            om2.MGlobal.displayWarning("Skipping Shader `{}` as it's not assigned to any faces".format(shader))
            continue
        oppShaderName = shader.replace(shaderFromSuffix, shaderToSuffix)  # get opposite shader
        if not cmds.objExists(oppShaderName):
            om2.MGlobal.displayWarning("Skipping Shader `{}` as it doesn't exist".format(oppShaderName))
            continue
        shaderutils.assignShader(objFaceList, oppShaderName)
        shadersAssigned += 1
    return shadersAssigned


def toggleShaderAuto(shader1Suffix='VP2', shader2Suffix='PXR'):
    """Toggles all shaders in a scene swapping the shaders with the given suffix's.
    The swap is based off the first shader found in the scene that includes either suffix
    So the swap is automatic and will swap all shaders with the corresponding suffix's
    Only works on polygons, not currently NURBS

    :param shader1Suffix: the suffix of the first set of shader names `PXR` would match to skinShader_PXR
    :type shader1Suffix: str
    :param shader2Suffix:  the suffix of the second set of shader names `viewport` would match to skinShader_viewport
    :type shader2Suffix: str
    """
    suffixFound = findFirstWildcardShader(shader1Suffix, shader2Suffix)  # find first shader with any suffix in scene
    if not suffixFound:
        om2.MGlobal.displayWarning("No shaders with either suffix `{}` or `{}` have been found in "
                                   "the scene".format(shader1Suffix, shader2Suffix))
        return
    if suffixFound == shader1Suffix:
        shaderFromSuffix = shader1Suffix
        shaderToSuffix = shader2Suffix
    else:
        shaderToSuffix = shader1Suffix
        shaderFromSuffix = shader2Suffix
    shadersAssigned = toggleShader(shaderFromSuffix, shaderToSuffix)  # toggle the all the shaders
    if not shadersAssigned:
        om2.MGlobal.displayWarning('No shaders with suffix `{}` were assigned.'.format(shaderToSuffix))
        return
    om2.MGlobal.displayInfo('All shaders with suffix `{}` are now assigned (Toggled from shaders with '
                            'suffix `{}`). {} shaders swapped.'.format(shaderToSuffix, shaderFromSuffix, shadersAssigned))

