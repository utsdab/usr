from maya import cmds as cmds
from maya.api import OpenMaya as om2

from zoo.libs.maya.cmds.objutils import filtertypes
from zoo.libs.maya.cmds.shaders import shaderutils
from zoo.libs.maya.cmds.shaders.shdmultconstants import DISP_ATTR_AUTOBUMP, DISP_ATTR_DIVISIONS, DISP_ATTR_IMAGEPATH, \
    DISP_ATTR_SCALE, DISP_ATTR_TYPE, DISP_ATTR_BOUNDS

def createVectorDisplacement(shadingGroupList, imagePath="", tangentType="tangent", scaleMultiplier=1, message=True,
                             selectFilenode=True):
    """Creates a vector displacement setup for Renderman on the given shading groups
    Builds the node networks required

    :return shadingGroupList: list of the shading groups names that now have displacement nodes
    :rtype shadingGroupList: list
    :param imagePath:  Optional path of the image, can be left empty str ""
    :type imagePath: str
    :param tangentType: either "tangent" or "object"
    :type tangentType: str
    :param scaleMultiplier: the scale multiplier of the displacement
    :type scaleMultiplier: float
    :param message: display messages for the user success warnings etc
    :type message: bool
    :param selectFilenode: at the end of creation select the filenode for adding the texture?
    :type selectFilenode: bool
    :return pxrDisplaceList: list of pxrDisplace nodes that were created
    :rtype pxrDisplaceList: list
    :return PxrDisplaceTransformList: list of PxrDisplaceTransform nodes that were created
    :rtype PxrDisplaceTransformList: list
    :return PxrTextureList: list of PxrTexture nodes that were created
    :rtype PxrTextureList: list
    """
    pxrDisplaceList = list()
    PxrDispTransformList = list()
    PxrTextureList = list()
    tangentValue = 3  # tangent by default
    if tangentType == "object":
        tangentValue = 2
    elif tangentType == "world":
        tangentValue = 1
    else:
        om2.MGlobal.displayWarning('The tangent Type does not exist or does not match to settings, check the string')
    # build the three nodes
    for shadingGroup in shadingGroupList:
        pxrDisplace = cmds.shadingNode("PxrDisplace", name="{}_PxrDisplace".format(shadingGroup), asUtility=True)
        pxrDisplaceList.append(pxrDisplace)
        PxrDispTransform = cmds.shadingNode("PxrDispTransform", name="{}_dTransform".format(shadingGroup),
                                            asUtility=True)
        PxrDispTransformList.append(PxrDispTransform)
        PxrTexture = cmds.shadingNode("PxrTexture", name="{}_VD".format(shadingGroup), asUtility=True)
        PxrTextureList.append(PxrTexture)
        # make the connections
        cmds.connectAttr('{}.resultRGB'.format(PxrTexture), '{}.dispVector'.format(PxrDispTransform),
                         force=True)
        cmds.connectAttr('{}.resultXYZ'.format(PxrDispTransform), '{}.dispVector'.format(pxrDisplace),
                         force=True)
        cmds.connectAttr('{}.outColor'.format(pxrDisplace), '{}.displacementShader'.format(shadingGroup),
                         force=True)
        # set the attributes
        cmds.setAttr("{}.dispAmount".format(pxrDisplace), scaleMultiplier)  # set the scale (gain)
        cmds.setAttr("{}.dispType".format(PxrDispTransform), 3)  # set Displacement Type to Mudbox Vector
        cmds.setAttr("{}.vectorSpace".format(PxrDispTransform), tangentValue)  # Displacement Type to Mudbox Vector
        if imagePath:
            cmds.setAttr("{}.filename".format(PxrTexture), imagePath, type="string")
    if selectFilenode:
        cmds.select(PxrTextureList[-1], replace=True)  # select the last texture node created for the user
    # messages
    if message:
        om2.MGlobal.displayInfo('Success displacement setup on shading groups {}'.format(shadingGroupList))
    return pxrDisplaceList, PxrDispTransformList, PxrTextureList, pxrDisplace


def createDisplacement(nodeList, imagePath="", displacementType="VDM", tangentType="tangent", scaleMultiplier=1,
                       bounds=0.1, selectFilenode=True):
    """Creates a displacement setup for Renderman
    Builds the shader node networks required
    Shading Group and Mesh selection is automatic
    nodeList can be any selection type related to a shader.  eg mesh, transform, shader or shading group

    :param nodeList: list of nodes names that could be or are related to the shading group
    :type nodeList: list
    :param imagePath:  Optional path of the image, can be left empty str ""
    :type imagePath: str
    :param displacementType: either "VDM" (vector displacement map) or "height" (b&w)
    :type displacementType: str
    :param tangentType: either "tangent" or "object"
    :type tangentType: str
    :param scaleMultiplier: the scale multiplier of the displacement
    :type scaleMultiplier: float
    :param bounds: The scale of the displacement bounds, displacement setting that can cull objects if too low
    :type bounds: float
    :param selectFilenode: at the end of creation select the filenode for adding the texture?
    :type selectFilenode: bool
    """
    shadingGroupList = shaderutils.getShadingGroupsFromNodes(nodeList)  # get shading group from nodeList
    meshList = shaderutils.getMeshFaceFromShaderNodes(nodeList, selectMesh=False, objectsOnly=True)
    # set variables based on args
    if displacementType == "VDM":
        pxrDisplaceList, PxrDispTransformList, PxrTextureList, \
        pxrDisplace = createVectorDisplacement(shadingGroupList,
                                               imagePath=imagePath,
                                               tangentType=tangentType,
                                               scaleMultiplier=scaleMultiplier,
                                               selectFilenode=selectFilenode)
        if meshList and bounds != 0.1:  # 0.1 is the default so no need to set
            shapeList = filtertypes.shapeTypeFromTransformOrShape(meshList, shapeType="mesh")
            if shapeList:
                for shape in shapeList:
                    cmds.setAttr("{}.rman_displacementBound".format(shape), bounds)
        pxrDisplaceNodes = pxrDisplaceList + PxrDispTransformList
        return meshList, shadingGroupList, PxrTextureList, pxrDisplaceNodes, pxrDisplace
    else:  # will be object space for now
        om2.MGlobal.displayInfo('Regular Displacement (Black And White) is not supported by the UI as this stage')
        return list(), list(), list(), list(), ""


def createDisplacementSelected(imagePath="", displacementType="VDM", tangentType="tangent", scaleMultiplier=1,
                               selectFilenode=True):
    """Creates a displacement setup for Renderman from a selection
    Builds the shader node networks required
    Shading Group and Mesh selection is automatic
    nodeList can be any selection type related to a shader.  eg mesh, transform, shader or shading group

    :param imagePath:  Optional path of the image, can be left empty str ""
    :type imagePath: str
    :param displacementType: either "VDM" (vector displacement map) or "height" (b&w)
    :type displacementType: str
    :param tangentType: either "tangent" or "object"
    :type tangentType: str
    :param scaleMultiplier: the scale multiplier of the displacement
    :type scaleMultiplier: float
    :param selectFilenode: at the end of creation select the filenode for adding the texture?
    :type selectFilenode: bool
    """
    selObj = cmds.ls(selection=True)
    if not selObj:
        om2.MGlobal.displayWarning('Nothing selected, please select a mesh, shader or shading group')
    return createDisplacement(displacementType=displacementType, tangentType=tangentType,
                              scaleMultiplier=scaleMultiplier,
                              selectFilenode=selectFilenode)


# -------------------------
# DELETE DISPLACEMENT
# -------------------------


def deleteDisplacementNodes(meshList, fileNodeList, otherNodeList):
    """Deletes a displacement setup for Renderman

    Deletes the displacement nodes and resets the mesh subdivision attributes to be off

    :param meshList: The list of meshes affected by the displacement, subdivision will be turned off
    :type meshList: list(str)
    :param fileNodeList: list of texture nodes, will be deleted
    :type fileNodeList: list(str)
    :param otherNodeList: list of other displacement nodes, will be deleted
    :type otherNodeList: list()
    """
    if fileNodeList is None:  # might be None
        fileNodeList = list()
    if otherNodeList is None:  # might be None
        otherNodeList = list()
    deleteNodeList = fileNodeList + otherNodeList
    if deleteNodeList:
        for node in fileNodeList + otherNodeList:
            if cmds.objExists(node):
                cmds.delete(node)
    if meshList:
        for mesh in meshList:
            if cmds.objExists(mesh):
                shapeList = filtertypes.shapeTypeFromTransformOrShape(meshList, shapeType="mesh")
                if shapeList:
                    for shape in shapeList:
                        cmds.setAttr("{}.rman_displacementBound".format(shape), 0.1)  # Set default bounds


# -------------------------
# RETRIEVE AND SET DISPLACEMENT ATTRS
# -------------------------


def getDisplacementAttrValues(meshList, shadingGroupList, fileNodeList, place2dTextureNodeList, displaceNode):
    """Retrieves the main attribute values of the displacement setup, usually for the UI

    :param meshList: The list of meshes affected by the displacement, subdivision will be turned off
    :type meshList: list(str)
    :param fileNodeList: list of texture file nodes, will be deleted
    :type fileNodeList: list(str)
    :param place2dTextureNodeList: list of 2d place texture file nodes, will be deleted
    :type place2dTextureNodeList: list()
    :param displaceNode: the Arnold displacement node type "displacementShader"
    :type displaceNode: str
    :return:
    :rtype:
    """
    autoBump = False
    image = cmds.getAttr(".".join([fileNodeList[0], "filename"]))
    divisions = 4
    scale = cmds.getAttr(".".join([displaceNode, "dispAmount"]))
    bounds = cmds.getAttr(".".join([meshList[0], "rman_displacementBound"]))
    dtypeInt = cmds.getAttr(".".join([place2dTextureNodeList[0], "vectorSpace"]))
    if dtypeInt == 3:  # Tangent
        dtype = "Tangent"
    else:  # Note can also be world, but ignore.  2 is object FYI
        dtype = "Object"
    return dtype, divisions, scale, autoBump, image, bounds


def setDisplacementAttrValues(meshList, shadingGroupList, fileNodeList, place2dTextureNodeList, displaceNode, attrDict,
                              message=False):
    """

    """
    for mesh in meshList:
        cmds.setAttr(".".join([mesh, "rman_displacementBound"]), attrDict[DISP_ATTR_BOUNDS])
    cmds.setAttr(".".join([fileNodeList[0], "filename"]), attrDict[DISP_ATTR_IMAGEPATH], type="string")
    cmds.setAttr(".".join([displaceNode, "dispAmount"]), attrDict[DISP_ATTR_SCALE])
    if attrDict[DISP_ATTR_TYPE] == "Tangent":
        dtypeInt = 3
    else:
        dtypeInt = 2
    cmds.setAttr(".".join([place2dTextureNodeList[0], "vectorSpace"]), dtypeInt)
    if message:
        om2.MGlobal.displayInfo("Success: Attributes set on `{}` displacement".format(shadingGroupList))


# -------------------------
# ENABLE DISABLE
# -------------------------


def setEnabled(displaceNode, enableValue=True):
    """Sets the enable state of the entire displacement network

    In Renderman use .enabled on the PxrDisplace node

    :param displaceNode: A PxrDisplace node
    :type displaceNode: str
    :param enableValue: Enable True or disable False
    :type enableValue: bool
    """
    cmds.setAttr("{}.enabled".format(displaceNode), enableValue)


def getEnabled(displaceNode):
    """Gets the enable state of the entire displacement network

    In Renderman query .enabled on the PxrDisplace node

    :param displaceNode: A PxrDisplace node
    :type displaceNode: str
    :return enableValue: Enable True or disable False
    :rtype enableValue: bool
    """
    return cmds.getAttr("{}.enabled".format(displaceNode))