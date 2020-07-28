from maya import cmds as cmds
from maya.api import OpenMaya as om2
from zoo.libs.maya.cmds.shaders import shaderutils, textures
from zoo.libs.maya.cmds.shaders.shdmultconstants import DISP_ATTR_AUTOBUMP, DISP_ATTR_DIVISIONS, DISP_ATTR_IMAGEPATH, \
    DISP_ATTR_SCALE, DISP_ATTR_TYPE, DISP_ATTR_BOUNDS, NW_DISPLACE_MESH_ATTR


def createDisplacementNodes(nodeList, imagePath="", displacementType="VDM", tangentType="tangent", autoBump=False,
                            maxDivisions=5, scaleMultiplier=1, bounds=1.0):
    """Creates a displacement setup for Redshift
    Builds the shader node networks and changes the Redshift mesh attributes too
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
    :param autoBump: enable the autoBump checkbox?
    :type autoBump: bool
    :param maxDivisions: The maximum divisions of the displacement
    :type maxDivisions: int
    :param scaleMultiplier: Multiplies the intensity of the displacement by this amount
    :type scaleMultiplier: float
    :param bounds: The clipping bounds, usually set low on displacement in Redshift is "Maximum Displacement"
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
    spaceType = 2  # tangent type by default
    if displacementType == "VDM":
        mapEncoding = 0
        if tangentType != "tangent":
            spaceType = 1  # will be object type
    else:  # is height
        mapEncoding = 2
    # --------------------
    # create VD node setup
    # --------------------
    for i, shadingGroup in enumerate(shadingGroupList):
        # create displacement node
        displacementNode = cmds.shadingNode("RedshiftDisplacement", name="{}_VD".format(shadingGroup), asUtility=True)
        cmds.setAttr("{}.map_encoding".format(displacementNode), mapEncoding)  # set vector 0 or height field 2
        cmds.setAttr("{}.scale".format(displacementNode), scaleMultiplier)  # set scale of displacement
        if displacementType == "VDM":
            cmds.setAttr("{}.space_type".format(displacementNode), spaceType)  # set tangent 2 or object 1
        # create file node, image path and set to raw
        fileNode, place2dTextureNode = textures.createFileTexture(name="{}_fileVDM".format(shadingGroup),
                                                                  colorSpace="Raw",
                                                                  imagePath=imagePath,
                                                                  ignoreColorSpace=True)
        fileNodeList.append(fileNode)  # add to lists
        place2dTextureNodeList.append(place2dTextureNode)
        # connect nodes
        cmds.connectAttr('{}.outColor'.format(fileNode), '{}.texMap'.format(displacementNode), force=True)
        cmds.connectAttr('{}.out'.format(displacementNode), '{}.displacementShader'.format(shadingGroup), force=True)
    cmds.select(fileNodeList, replace=True)
    # -------------
    # change redshift settings of meshes
    # -------------
    for mesh in meshList:
        cmds.setAttr("{}.rsMinTessellationLength".format(mesh), 1)  # set the minimum edge length to 1 pixel quality
        cmds.setAttr("{}.rsEnableSubdivision".format(mesh), 1)  # enable subdivision section
        cmds.setAttr("{}.rsMaxTessellationSubdivs".format(mesh), maxDivisions)  # max subdivision level
        cmds.setAttr("{}.rsEnableDisplacement".format(mesh), 1)  # displacement on
        cmds.setAttr("{}.rsMaxDisplacement".format(mesh), bounds)  # The displacement clipping bounds
        if displacementType == "VDM":  # auto bump doesn't work with VDM, turn it off
            cmds.setAttr("{}.rsAutoBumpMap".format(mesh), 0)
        else:
            if autoBump:
                cmds.setAttr("{}.rsAutoBumpMap".format(mesh), 1)  # auto bump on as specified
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


def createDisplacementNodesSelected(displacementType="VDM", tangentType="tangent", autoBump=False, maxDivisions=5,
                                    scaleMultiplier=1, bounds=1.0):
    """Creates a displacement setup for Redshift from a selection
    Will build the node networks and change the mesh attributes too
    the selection can be any selection type related to a shaders, meshes, transforms, shaders or shading groups

    :param displacementType: either "VDM" (vector displacement map) or "height" (b&w)
    :type displacementType: str
    :param tangentType: either "tangent" or "object"
    :type tangentType: str
    :return meshList: list of the mesh names that now have displacement nodes
    :rtype meshList: list
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
    place2dTextureNodeList = createDisplacementNodes(selObj,
                                                     displacementType=displacementType,
                                                     tangentType=tangentType,
                                                     autoBump=autoBump,
                                                     maxDivisions=maxDivisions,
                                                     scaleMultiplier=scaleMultiplier,
                                                     bounds=bounds)
    return meshList, shadingGroupList, fileNodeList, place2dTextureNodeList


# -------------------------
# DELETE DISPLACEMENT
# -------------------------


def deleteDisplacementNodes(meshList, fileNodeList, place2dTextureNodeList):
    """Deletes a displacement setup for Redshift

    Deletes the displacement nodes and resets the mesh subdivision attributes to be off

    :param meshList: The list of meshes affected by the displacement, subdivision will be turned off
    :type meshList: list(str)
    :param fileNodeList: list of texture file nodes, will be deleted
    :type fileNodeList: list(str)
    :param place2dTextureNodeList: list of 2d place texture file nodes, will be deleted
    :type place2dTextureNodeList: list()
    """
    if fileNodeList is None:  # might be None
        fileNodeList = list()
    if place2dTextureNodeList is None:  # might be None
        place2dTextureNodeList = list()
    deleteNodeList = fileNodeList + place2dTextureNodeList
    if deleteNodeList:
        for node in fileNodeList + place2dTextureNodeList:
            if cmds.objExists(node):
                cmds.delete(node)
    if meshList:
        for mesh in meshList:  # Reset the redshift settings to defaults
            if cmds.objExists(mesh):  # may be deleted
                cmds.setAttr("{}.rsEnableSubdivision".format(mesh), 0)  # disable subdivision section
                cmds.setAttr("{}.rsEnableDisplacement".format(mesh), 0)  # disable subdivision section
                cmds.setAttr("{}.rsMaxDisplacement".format(mesh), 1.0)  # reset bounds attribute
                cmds.setAttr("{}.rsMinTessellationLength".format(mesh), 4)  # redshift default


# -------------------------
# RETRIEVE AND SET DISPLACEMENT ATTRS
# -------------------------


def getDisplacementAttrValues(meshList, shadingGroupList, fileNodeList, place2dTextureNodeList, displaceNode):
    """Retrieves the main attribute values of the displacement setup, usually for the UI

    TODO: could export with a dictionary would be cleaner

    :param meshList: The list of meshes affected by the displacement, subdivision will be turned off
    :type meshList: list(str)
    :param shadingGroupList: List of shading group names
    :type shadingGroupList: list(str)
    :param fileNodeList: list of texture file nodes, will be deleted
    :type fileNodeList: list(str)
    :param place2dTextureNodeList: list of 2d place texture file nodes, will be deleted
    :type place2dTextureNodeList: list()
    :param displaceNode: the Arnold displacement node type "displacementShader"
    :type displaceNode: str
    :return dtype: displacement type "Tangent" or "Object"
    :rtype dtype: str
    :return divisions: The amount of displacment divisions
    :rtype divisions: int
    :return scale: The scale of the displacement
    :rtype scale: float
    :return autoBump: Is the autobump on or off?
    :rtype autoBump: bool
    :return image: The full image file path
    :rtype image: str
    :return bounds:  The clipping bounds of the displacement
    :rtype bounds:
    """
    autoBump = cmds.getAttr(".".join([meshList[0], "rsAutoBumpMap"]))  # note attribute editor UI refresh issues
    bounds = cmds.getAttr(".".join([meshList[0], "rsMaxDisplacement"]))  # bounds
    image = cmds.getAttr(".".join([fileNodeList[0], "fileTextureName"]))
    divisions = cmds.getAttr(".".join([meshList[0], "rsMaxTessellationSubdivs"]))
    scale = cmds.getAttr(".".join([displaceNode, "scale"]))
    dtypeInt = cmds.getAttr(".".join([displaceNode, "space_type"]))
    if dtypeInt == 2:  # Tangent
        dtype = "Tangent"
    else:  # Note can also be world, but ignore.  1 is object FYI
        dtype = "Object"
    return dtype, divisions, scale, autoBump, image, bounds


def setDisplacementAttrValues(meshList, shadingGroupList, fileNodeList, place2dTextureNodeList, displaceNode, attrDict,
                              message=False):
    """Sets the attributes for the vector displacement setup

    :param meshList: The list of meshes affected by the displacement, subdivision will be turned off
    :type meshList: list(str)
    :param shadingGroupList: List of shading group names
    :type shadingGroupList: list(str)
    :param fileNodeList: list of texture file nodes, will be deleted
    :type fileNodeList: list(str)
    :param place2dTextureNodeList: list of 2d place texture file nodes, will be deleted
    :type place2dTextureNodeList: list()
    :param displaceNode: the Arnold displacement node type "displacementShader"
    :type displaceNode: str
    :param attrDict: The dictionary with values to set, see shdmulticonstants.py for a list of keys
    :type attrDict: dict
    :param message: report the message to the user?
    :type message: bool
    """
    for mesh in meshList:
        cmds.setAttr(".".join([mesh, "rsAutoBumpMap"]), attrDict[DISP_ATTR_AUTOBUMP])
        cmds.setAttr(".".join([mesh, "rsMaxDisplacement"]), attrDict[DISP_ATTR_BOUNDS])
        cmds.setAttr(".".join([mesh, "rsMaxTessellationSubdivs"]), attrDict[DISP_ATTR_DIVISIONS])
    cmds.setAttr(".".join([fileNodeList[0], "fileTextureName"]), attrDict[DISP_ATTR_IMAGEPATH], type="string")
    cmds.setAttr("{}.colorSpace".format(fileNodeList[0]), "Raw", type='string')  # Keep raw!
    cmds.setAttr(".".join([displaceNode, "scale"]), attrDict[DISP_ATTR_SCALE])
    if attrDict[DISP_ATTR_TYPE] == "Tangent":
        dtypeInt = 2
    else:
        dtypeInt = 1
    cmds.setAttr(".".join([displaceNode, "space_type"]), dtypeInt)
    if message:
        om2.MGlobal.displayInfo("Success: Attributes set on `{}` displacement".format(shadingGroupList))


def updateMeshes(newConnectionsList, breakConnectionsList, displacementAttrDict, enabled):
    """When a new mesh is connected, update the mesh to match the settings of the shader displacement

    :param newConnectionsList: A list of Maya meshes to update, these are new connections
    :type newConnectionsList: list(str)
    :param breakConnectionsList: A list of Maya meshes to update, these are no longer part of the network
    :type breakConnectionsList: list(str)
    :param displacementAttrDict:  Dictionary with displacement attr values see keys DISP_ATTR in shdmulticonstants.py
    :type displacementAttrDict: dict()
    :param enabled: Is the displacement enabled?
    :type enabled: bool
    """
    if newConnectionsList:
        for mesh in newConnectionsList:
            cmds.setAttr(".".join([mesh, "rsAutoBumpMap"]), displacementAttrDict[DISP_ATTR_AUTOBUMP])
            cmds.setAttr(".".join([mesh, "rsMaxDisplacement"]), displacementAttrDict[DISP_ATTR_BOUNDS])
            cmds.setAttr(".".join([mesh, "rsMaxTessellationSubdivs"]), displacementAttrDict[DISP_ATTR_DIVISIONS])
            cmds.setAttr("{}.rsEnableDisplacement".format(mesh), enabled)
            cmds.setAttr("{}.rsMinTessellationLength".format(mesh), 1)  # set the minimum edge length to 1 pixel quality
            cmds.setAttr("{}.rsEnableSubdivision".format(mesh), 1)  # enable subdivision section
    if breakConnectionsList:
        for mesh in breakConnectionsList:
            # Delete the network attribute name
            if cmds.attributeQuery(NW_DISPLACE_MESH_ATTR, node=mesh, exists=True):  # if attr exists, it should
                cmds.deleteAttr(mesh, attribute=NW_DISPLACE_MESH_ATTR)
            # Reset the attribute to defualts
            cmds.setAttr("{}.rsEnableSubdivision".format(mesh), 0)  # disable subdivision section
            cmds.setAttr("{}.rsEnableDisplacement".format(mesh), 0)  # disable subdivision section
            cmds.setAttr("{}.rsMaxDisplacement".format(mesh), 1.0)  # reset bounds attribute
            cmds.setAttr("{}.rsMinTessellationLength".format(mesh), 4)  # redshift default


# -------------------------
# ENABLE DISABLE
# -------------------------


def setEnabled(meshList, enableValue=True):
    """Sets the enable state of the entire displacement network

    In Redshift just use rsEnableSubdivision on each mesh

    :param meshList: A list of mesh names
    :type meshList: list(str)
    :param enableValue: Enable True or disable False
    :type enableValue: nool
    """
    for mesh in meshList:
        cmds.setAttr("{}.rsEnableDisplacement".format(mesh), enableValue)


def getEnabled(meshList):
    """Gets the enable state of the entire displacement network

    In Redshift just query rsEnableSubdivision on each mesh

    :param meshList: A list of mesh names
    :type meshList: list(str)
    :return enableValue: Enable True or disable False
    :rtype enableValue: bool
    """
    if not meshList:
        return
    return cmds.getAttr("{}.rsEnableDisplacement".format(meshList[0]))
