import maya.cmds as cmds
from maya.api import OpenMaya as om2

from zoo.libs.maya.cmds.skin import bindskin
from zoo.libs.maya.cmds.objutils import filtertypes, namehandling
from zoo.libs.utils import zlogging
from zoo.libs.maya.cmds.shaders import shaderutils

logger = zlogging.getLogger(__name__)

SHADER_SPACE = {"World": 0, "Local": 1, "Topology": 2}

UV_SPACE = {
    0: 0,  # World
    1: 1,  # Local
    2: 3,  # UV
    3: 4,  # Component
    4: 5  # Topology
}
SEARCH_METHOD = {0: 0,  # Point
                 1: 3}  # Normal

SHADER_SPACE_WORLD = 0
SHADER_SPACE_LOCAL = 1
SHADER_SPACE_TOPOLOGY = 2

SKINNED_AUTO = 0
SKINNED_YES = 1
SKINNED_NO = 2


def transfer(transformObjList, transferUvs=True, transferShader=False, uvSampleSpace=4,
             shaderSampleSpace=SHADER_SPACE_TOPOLOGY, skinned=SKINNED_AUTO, searchMethod=1, deleteHistory=True,
             message=True):
    """ Do a UV/Shader Transfer with an incoming transformObjList. Objects can be poly meshes or nurbsSurfaces

    Most code uses based on Maya's cmds.transferAttributes() and cmds.transferShadingSets().
    Based on a tool by Jason Dobra https://vimeo.com/user46798528

    nurbsSurfaces are ignored on UV transfer and will only transfer the first shader found, unlike poly meshes /
    which are fully supported

    The transformObjList must have a minimum of two objects, the first object is copied to all other objects

    :param transformObjList: maya transforms either poly mesh transforms or nubsSurface transform names
    :type transformObjList: list(str)
    :param transferUvs: Transfer the uvs across from one mesh to another
    :type transferUvs: bool
    :param transferShader: Transfer shader
    :type transferShader: bool
    :param uvSampleSpace: UV Sample space has to be one of the following 0=World, 1=Local, 2=UV, 3=Component, 4=Topology
    :type uvSampleSpace: int
    :param shaderSampleSpace: Shader sample space can be the string "World", or "Local"
    :type shaderSampleSpace: int
    :param skinned: SKINNED_AUTO, SKINNED_YES or SKINNED_NO
    :type skinned: int
    :param searchMethod: 0 = Point, 1 = Normal
    :type searchMethod: int
    :param deleteHistory: Delete the history after finishing. Skinned objects only delete the shapeOrig node history
    :type deleteHistory: bool
    :param message: Report the message to the user?
    :type message: bool
    :return success: True if the transfer was successful, False if not. Note: False if only partially successful
    :rtype success: bool
    :return failList: list of targets that failed in the transfer
    :rtype failList: list(str)
    :return successList: list of targets that were successful in the transfer
    :rtype successList: list(str)
    """
    failList = list()
    successList = list()
    uvSpace = UV_SPACE.get(uvSampleSpace)
    shaderSpace = shaderSampleSpace
    search = SEARCH_METHOD.get(searchMethod)

    # 2 Means transfer uv, 0 means don't transfer
    uvs = 2 if transferUvs else 0
    source = transformObjList[0]
    targets = transformObjList[1:]

    # Do the logic ----------------------------------------------
    for target in targets:
        # skinCluster = bindskin.getSkinCluster(target)  # not needed just deformerList as skin is included
        deformerList = filtertypes.deformerHistoryOnObj(target)

        # Transfer Shaders
        if transferShader:
            if shaderSampleSpace != SHADER_SPACE_TOPOLOGY:
                cmds.transferShadingSets(source, target, sampleSpace=shaderSpace, searchMethod=search)
            else:
                if not shaderutils.transferShaderTopology(source, target):  # if failed
                    failList.append(target)

        if not transferUvs or filtertypes.filterTypeReturnTransforms([target], children=False,
                                                                     shapeType="nurbsSurface"):
            break  # transferUvs not checked try next object

        if filtertypes.filterTypeReturnTransforms([target], children=False, shapeType="nurbsSurface"):
            if message:
                om2.MGlobal.displayWarning("Object is Nurbs so skinning UV transfer")
            failList.append(target)
            break  # is Nurbs try next object

        # Display error messages
        if skinned == SKINNED_YES and not deformerList:
            if message:
                om2.MGlobal.displayWarning("No skin clusters or deformers found. Cancelling transfer UV.")
            failList.append(target)
            break  # try next object

        # Is the target skinned/deformed?
        if deformerList and skinned != SKINNED_NO:
            targetOrigin = bindskin.checkValidOrigShape(target, deleteDeadShapes=True, displayMessage=False)
            cmds.setAttr("{}.intermediateObject".format(targetOrigin), 0)
            cmds.transferAttributes(source, targetOrigin, transferPositions=False, transferNormals=False,
                                    transferUVs=uvs, transferColors=True, sampleSpace=uvSpace, sourceUvSpace="map1",
                                    targetUvSpace="map1", searchMethod=search, flipUVs=False, colorBorders=True)
            if deleteHistory:
                cmds.delete(targetOrigin, constructionHistory=1)
            cmds.setAttr("{}.intermediateObject".format(targetOrigin), 1)

        else:  # If not continue
            cmds.transferAttributes(source, target, transferPositions=False, transferNormals=False,
                                    transferUVs=uvs, transferColors=True, sampleSpace=uvSpace, sourceUvSpace="map1",
                                    targetUvSpace="map1", searchMethod=3, flipUVs=False, colorBorders=True)
            if deleteHistory:
                cmds.delete(target, constructionHistory=1)
        successList.append(target)

    # Return and report messages -------------------------------------------
    if successList and not failList:
        if message:
            om2.MGlobal.displayInfo("Success: Transfer Completed on objects "
                                    "{}".format(namehandling.getUniqueShortNameList(successList)))
        success = True
    else:
        if successList and message:
            om2.MGlobal.displayWarning("Some objects failed and some succeeded. "
                                       "Success: `{}` Failed: "
                                       "`{}`".format(namehandling.getUniqueShortNameList(successList),
                                                     namehandling.getUniqueShortNameList(failList)))
        elif not successList and message:
            om2.MGlobal.displayWarning("Objects failed to transfer: "
                                       "`{}`".format(namehandling.getUniqueShortNameList(failList)))
        success = False
    return success, failList, successList


def transferSelected(transferUvs=True, transferShader=False, uvSampleSpace=4, shaderSampleSpace=SHADER_SPACE_TOPOLOGY,
                     skinned=SKINNED_AUTO, searchMethod=1, deleteHistory=True, message=True):
    """ Do a UV/Shader Transfer on the selection, must be two or more mesh objects or two or more NURBS objects

    The first object is copied to all other objects

    Based on a tool by Jason Dobra https://vimeo.com/user46798528

    :param transferUvs: Transfer the uvs across from one mesh to another
    :type transferUvs: bool
    :param transferShader: Transfer shader
    :type transferShader: bool
    :param uvSampleSpace: UV Sample space has to be one of the following 0=World, 1=Local, 2=UV, 3=Component, 4=Topology
    :type uvSampleSpace: int
    :param shaderSampleSpace: Shader sample space can be the string "World", or "Local"
    :type shaderSampleSpace: int
    :param skinned: SKINNED_AUTO, SKINNED_YES or SKINNED_NO
    :type skinned: int
    :param searchMethod: 0 = Point, 1 = Normal
    :type searchMethod: int
    :param deleteHistory: Delete the history after finishing. Skinned objects only delete the shapeOrig node history
    :type deleteHistory: bool
    :param message: Report the message to the user?
    :type message: bool
    :return success: True if the transfer was successful, False if not. Note: False if only partially successful
    :rtype success: bool
    :return failList: list of targets that failed in the transfer
    :rtype failList: list(str)
    :return successList: list of targets that were successful in the transfer
    :rtype successList: list(str)
    """
    selObjs = cmds.ls(selection=True, long=True)
    selMeshObjs = filtertypes.filterTypeReturnTransforms(selObjs, children=False, shapeType="mesh")
    selNurbsObjs = filtertypes.filterTypeReturnTransforms(selObjs, children=False, shapeType="nurbsSurface")
    if len(selMeshObjs) < 2 and len(selNurbsObjs) < 2:
        if message:
            om2.MGlobal.displayWarning("Not enough objects selected. Please select either two poly mesh or two "
                                       "nurbs objects")
        return False

    elif len(selMeshObjs) > 1:  # poly meshes
        return transfer(selMeshObjs, transferUvs=transferUvs, transferShader=transferShader,
                        uvSampleSpace=uvSampleSpace, shaderSampleSpace=shaderSampleSpace, skinned=skinned,
                        searchMethod=searchMethod, deleteHistory=deleteHistory)
    elif len(selNurbsObjs) > 1:  # not poly so try nurbs surfaces
        return transfer(selNurbsObjs, transferUvs=transferUvs, transferShader=transferShader,
                        uvSampleSpace=uvSampleSpace, shaderSampleSpace=shaderSampleSpace, skinned=skinned,
                        searchMethod=searchMethod, deleteHistory=deleteHistory)
