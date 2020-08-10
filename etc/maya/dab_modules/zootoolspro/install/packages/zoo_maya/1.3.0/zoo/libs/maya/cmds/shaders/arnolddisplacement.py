from maya import cmds as cmds
from maya.api import OpenMaya as om2
from zoo.libs.maya.cmds.shaders import shaderutils, textures
from zoo.libs.maya.cmds.shaders.shdmultconstants import DISP_ATTR_AUTOBUMP, DISP_ATTR_DIVISIONS, DISP_ATTR_IMAGEPATH, \
    DISP_ATTR_SCALE, DISP_ATTR_TYPE, DISP_ATTR_BOUNDS, NW_DISPLACE_MESH_ATTR


def createDisplacementNodes(nodeList, imagePath="", displacementType="VDM", tangentType="tangent", autoBump=False,
                            maxDivisions=5, scaleMultiplier=1.0, bounds=0.1):
    """Creates a displacement setup for Arnold

    Builds the shader node networks and changes the Arnold mesh attributes too
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
    :param autoBump: autobump is a setting for regular displacement only and potentially adds a bump for fine details
    :type autoBump: bool
    :param maxDivisions: max divisions is the highest level of subdivides the mesh can go
    :type maxDivisions: int
    :param scaleMultiplier: the scale multiplier of the displacement
    :type scaleMultiplier: float
    :param bounds: Increase this value if clipping occurs in the displacement
    :type bounds: float
    :return shadingGroupList: list of the shading groups names that now have displacement nodes
    :rtype shadingGroupList: list
    :return fileNodeList: list of the fileNodes (texture) names that have been created
    :rtype fileNodeList: list
    :return place2dTextureNodeList: list of the  place2dTextureNode names that have been created
    :rtype place2dTextureNodeList: list
    """
    fileNodeList = list()
    place2dTextureNodeList = list()
    shadingGroupList = shaderutils.getShadingGroupsFromNodes(nodeList)  # get shading group from nodeList
    meshList = shaderutils.getMeshFaceFromShaderNodes(nodeList, selectMesh=False, objectsOnly=True)
    # --------------------
    # set variables based on args
    # --------------------
    spaceType = 2  # Tangent type by default
    if displacementType == "VDM":
        if tangentType != "tangent":
            spaceType = 1  # will be object type
            # Arnold also has world type, can leave this for now
    # --------------------
    # create VD node setup
    # --------------------
    for i, shadingGroup in enumerate(shadingGroupList):
        # create displacement node
        displacementNode = cmds.shadingNode("displacementShader", name="{}_VD".format(shadingGroup), asUtility=True)
        cmds.setAttr("{}.scale".format(displacementNode), scaleMultiplier)  # set scale of displacement
        cmds.setAttr("{}.aiDisplacementPadding".format(displacementNode), bounds)  # set scale of displacement
        if displacementType == "VDM":
            cmds.setAttr("{}.vectorSpace".format(displacementNode), spaceType)  # set tangent 2 or object 1, 0 is world
        # create file node and set to raw
        fileNode, place2dTextureNode = textures.createFileTexture(name="{}_fileVDM".format(shadingGroup),
                                                                  colorSpace="Raw",
                                                                  imagePath=imagePath,
                                                                  ignoreColorSpace=True)
        fileNodeList.append(fileNode)  # add to lists
        place2dTextureNodeList.append(place2dTextureNode)
        # connect nodes, the file texture setup will depend on the type of displacement as previously
        if displacementType == "VDM":
            cmds.connectAttr('{}.outColor'.format(fileNode), '{}.vectorDisplacement'.format(displacementNode),
                             force=True)
            cmds.connectAttr('{}.displacement'.format(displacementNode), '{}.displacementShader'.format(shadingGroup),
                             force=True)
    cmds.select(fileNodeList, replace=True)
    # -------------
    # change arnold settings of meshes
    # -------------
    for mesh in meshList:
        cmds.setAttr("{}.aiSubdivType".format(mesh), 1)  # enable subdivision smoothing catclarke
        cmds.setAttr("{}.aiSubdivUvSmoothing".format(mesh), 1)  # this is the smooth Uvs settings to pin borders
        cmds.setAttr("{}.aiSubdivIterations".format(mesh), maxDivisions)  # max subdivision level

    # -------------
    # report message
    # -------------
    if displacementType == "VDM":
        message = "VDM with {} type, scale {}, maxDivisions {}".format(tangentType, scaleMultiplier, maxDivisions)
    else:
        message = "height, scale {}, maxDivisions {}".format(tangentType, scaleMultiplier, maxDivisions)
    if len(shadingGroupList) > 1:  # then multiple displacements have been created
        om2.MGlobal.displayInfo('Multiple displacements created. '
                                'Type {} on shading groups `{}`'
                                'and meshes... `{}`'.format(message, shadingGroupList, meshList))
    else:
        om2.MGlobal.displayInfo('Single displacement created.'
                                'Type {} on shading group `{}`'
                                'and meshes... `{}`'.format(message, shadingGroupList[0], meshList))
    return meshList, shadingGroupList, fileNodeList, place2dTextureNodeList, displacementNode


def createDisplacementNodesSelected(imagePath="", displacementType="VDM", tangentType="tangent", autoBump=False,
                                    maxDivisions=5,
                                    scaleMultiplier=1):
    """Creates a displacement setup for Arnold from a selection
    Will build the node networks and change the mesh attributes too
    the selection can be any selection type related to a shaders, meshes, transforms, shaders or shading groups

    :param imagePath:  Optional path of the image, can be left empty str ""
    :type imagePath: str
    :param displacementType: either "VDM" (vector displacement map) or "height" (b&w)
    :type displacementType: str
    :param tangentType: either "tangent" or "object"
    :type tangentType: str
    :return shadingGroupList: list of the shading groups names that now have displacement nodes
    :rtype shadingGroupList: list
    :return fileNodeList: list of the fileNodes (texture) names that have been created
    :rtype fileNodeList: list
    :return place2dTextureNodeList: list of the  place2dTextureNode names that have been created
    :rtype place2dTextureNodeList: list
    """
    selObj = cmds.ls(selection=True)
    if not selObj:
        om2.MGlobal.displayWarning('Nothing Selected. Please Select Meshes, Shaders or Shading Groups')
        return
    meshList, shadingGroupList, fileNodeList, \
    place2dTextureNodeList, displacementNode = createDisplacementNodes(selObj,
                                                                       imagePath=imagePath,
                                                                       displacementType=displacementType,
                                                                       tangentType=tangentType,
                                                                       autoBump=autoBump,
                                                                       maxDivisions=maxDivisions,
                                                                       scaleMultiplier=scaleMultiplier)
    return meshList, shadingGroupList, fileNodeList, place2dTextureNodeList, displacementNode


# -------------------------
# DELETE DISPLACEMENT
# -------------------------


def deleteDisplacementNodes(meshList, fileNodeList, place2dTextureNodeList, displaceNode):
    """Deletes a displacement setup for Arnold

    Deletes the displacement nodes and resets the mesh subdivision attributes to be off

    :param meshList: The list of meshes affected by the displacement, subdivision will be turned off
    :type meshList: list(str)
    :param fileNodeList: list of texture file nodes, will be deleted
    :type fileNodeList: list(str)
    :param place2dTextureNodeList: list of 2d place texture file nodes, will be deleted
    :type place2dTextureNodeList: list()
    :param displaceNode: the Arnold displacement node type "displacementShader"
    :type displaceNode: str
    """
    if fileNodeList is None:  # might be None
        fileNodeList = list()
    if place2dTextureNodeList is None:  # might be None
        place2dTextureNodeList = list()
    deleteNodeList = fileNodeList + place2dTextureNodeList
    if displaceNode:
        deleteNodeList.append(displaceNode)
    if deleteNodeList:
        for node in deleteNodeList:
            if cmds.objExists(node):
                cmds.delete(node)
    if meshList:
        for mesh in meshList:
            if cmds.objExists(mesh):  # may be deleted
                cmds.setAttr("{}.aiSubdivType".format(mesh), 0)  # disable Arnold subdivision smoothing
                cmds.setAttr("{}.aiDispAutobump".format(mesh), 0)  # auto bump off, note attribute ed refresh issues
                cmds.setAttr("{}.aiSubdivUvSmoothing".format(mesh), 0)  # default smooth Uvs settings to pin borders


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
    autoBump = cmds.getAttr(".".join([displaceNode, "aiDisplacementAutoBump"]))
    image = cmds.getAttr(".".join([fileNodeList[0], "fileTextureName"]))
    divisions = cmds.getAttr(".".join([meshList[0], "aiSubdivIterations"]))
    scale = cmds.getAttr(".".join([displaceNode, "scale"]))
    bounds = cmds.getAttr(".".join([displaceNode, "aiDisplacementPadding"]))
    dtypeInt = cmds.getAttr(".".join([displaceNode, "vectorSpace"]))
    if dtypeInt == 2:  # Tangent
        dtype = "Tangent"
    else:  # Note can also be world, but ignore.  1 is object FYI
        dtype = "Object"
    return dtype, divisions, scale, autoBump, image, bounds


def setDisplacementAttrValues(meshList, shadingGroupList, fileNodeList, place2dTextureNodeList, displaceNode, attrDict,
                              message=False):
    """Sets all attributes on the displacement network

    :param meshList: The list of meshes affected by the displacement, subdivision will be turned off
    :type meshList: list(str)
    :param shadingGroupList: List of shading Group names
    :type shadingGroupList: list(str)
    :param fileNodeList: list of texture file nodes, will be deleted
    :type fileNodeList: list(str)
    :param place2dTextureNodeList: list of 2d place texture file nodes, will be deleted
    :type place2dTextureNodeList: list()
    :param displaceNode: the Arnold displacement node type "displacementShader"
    :type displaceNode: str
    :param attrDict:  Dictionary with displacement attr values see keys DISP_ATTR in shdmulticonstants.py
    :type attrDict: dict()
    :param message: Report the message to the user?
    :type message: bool
    """
    for mesh in meshList:
        cmds.setAttr(".".join([mesh, "aiSubdivIterations"]), attrDict[DISP_ATTR_DIVISIONS])
    cmds.setAttr(".".join([fileNodeList[0], "fileTextureName"]), attrDict[DISP_ATTR_IMAGEPATH], type="string")
    cmds.setAttr("{}.colorSpace".format(fileNodeList[0]), "Raw", type='string')  # Keep raw!
    cmds.setAttr(".".join([displaceNode, "scale"]), attrDict[DISP_ATTR_SCALE])
    cmds.setAttr(".".join([displaceNode, "aiDisplacementAutoBump"]), attrDict[DISP_ATTR_AUTOBUMP])
    cmds.setAttr(".".join([displaceNode, "aiDisplacementPadding"]), attrDict[DISP_ATTR_BOUNDS])
    if attrDict[DISP_ATTR_TYPE] == "Tangent":
        dtypeInt = 2
    else:
        dtypeInt = 1
    cmds.setAttr(".".join([displaceNode, "vectorSpace"]), dtypeInt)
    if message:
        om2.MGlobal.displayInfo("Success: Attributes set on `{}` displacement".format(shadingGroupList))


def updateMeshes(newConnectionsList, breakConnectionsList, attrDict, enabled):
    """When a new mesh is connected, update the mesh to match the settings of the shader displacement

    :param newConnectionsList: A list of Maya meshes to update, these are newly connected
    :type newConnectionsList: list(str)
    :param breakConnectionsList: A list of Maya meshes to update, these are no longer part of the network
    :type breakConnectionsList: list(str)
    :param attrDict:  Dictionary with displacement attr values see keys DISP_ATTR in shdmulticonstants.py
    :type attrDict: dict()
    :param enabled: Is the displacement enabled?  Affects .aiSubdivType attribute
    :type enabled: bool
    """
    if newConnectionsList:
        for mesh in newConnectionsList:  # set attrs to new values
            cmds.setAttr(".".join([mesh, "aiSubdivIterations"]), attrDict[DISP_ATTR_DIVISIONS])
            if enabled:
                cmds.setAttr("{}.aiSubdivType".format(mesh), 1)  # enable subdivision smoothing catclarke
            else:
                cmds.setAttr("{}.aiSubdivType".format(mesh), 0)  # disablenable subdivision smoothing catclarke
            cmds.setAttr("{}.aiSubdivUvSmoothing".format(mesh), 1)  # this is the smooth Uvs settings to pin borders
    if breakConnectionsList:
        for mesh in breakConnectionsList:  # delete attr and reset attrs
            # Delete the network attribute name
            if cmds.attributeQuery(NW_DISPLACE_MESH_ATTR, node=mesh, exists=True):  # if attr exists, it should
                cmds.deleteAttr(mesh, attribute=NW_DISPLACE_MESH_ATTR)
            # Reset the attribute to defaults
            cmds.setAttr("{}.aiSubdivType".format(mesh), 0)  # disable Arnold subdivision smoothing
            cmds.setAttr("{}.aiDispAutobump".format(mesh), 0)  # auto bump off, note attribute ed refresh issues
            cmds.setAttr("{}.aiSubdivUvSmoothing".format(mesh), 0)  # default smooth Uvs settings to pin borders
            cmds.setAttr(".".join([mesh, "aiSubdivIterations"]), 1)  # divisions default


# -------------------------
# ENABLE DISABLE
# -------------------------


def setEnabled(meshList, displaceNode, enableValue=True, autoBump=False):
    """Sets the enable state of the entire displacement network

    In Arnold use aiSubdivType on each mesh and disconnect the displacement from the sahder

    :param meshList: A list of mesh names
    :type meshList: list(str)
    :param enableValue: Enable True or disable False
    :type enableValue: nool
    """
    if not enableValue:
        autoBump = False
    for mesh in meshList:
        cmds.setAttr("{}.aiSubdivType".format(mesh), enableValue)
    cmds.setAttr("{}.aiDisplacementAutoBump".format(displaceNode), autoBump)


def getEnabled(meshList):
    """Gets the enable state of the entire displacement network

    In Arnold just query aiSubdivType on each mesh

    :param meshList: A list of mesh names
    :type meshList: list(str)
    :return enableValue: Enable True or disable False
    :rtype enableValue: bool
    """
    if not meshList:
        return
    enableValue = cmds.getAttr("{}.aiSubdivType".format(meshList[0]))
    if enableValue > 1:  # can be 2 etc
        enableValue = 1
    return enableValue