from maya import cmds as cmds
from maya.api import OpenMaya as om2

from zoo.libs.maya.cmds.objutils import filtertypes, attributes, namehandling
from zoo.libs.maya.cmds.rig import nodes
from zoo.libs.maya.cmds.shaders import rendermandisplacement, redshiftdisplacement, arnolddisplacement, shaderutils
from zoo.libs.maya.cmds.shaders.shdmultconstants import DISP_ATTR_TYPE, DISP_ATTR_DIVISIONS, DISP_ATTR_SCALE, \
    DISP_ATTR_AUTOBUMP, DISP_ATTR_IMAGEPATH, DISP_ATTR_BOUNDS, NW_DISPLACE_MESH_ATTR, NW_DISPLACE_SG_ATTR, \
    NW_DISPLACE_FILE_ATTR, NW_DISPLACE_PLACE2D_ATTR, NW_DISPLACE_NODE_ATTR, NW_DISPLACE_NODE, NW_ATTR_LIST, ARNOLD, \
    REDSHIFT, RENDERMAN, DISP_ATTR_RENDERER


# ---------------------
# CREATE DISPLACEMENT NETWORK NODES
# ---------------------


def displaceMessageNodeSetup(meshList, shadingGroupList, fileNodeList, place2dTextureNodeList, displacementNode,
                             renderer, autoBump):
    """Connects displacement nodes to a network node named "zooDisplacement_*" (NW_DISPLACE_NODE)

    The network node can be handy later, for deleting or managing objects, return back to default states etc

    :param meshList: list of Maya mesh names strings (nodes)
    :type meshList: list
    :param shadingGroupList: list of Maya shading group names strings (nodes)
    :type shadingGroupList: list
    :param fileNodeList: list of Maya node file node names strings (nodes)
    :type fileNodeList: list
    :return place2dTextureNodeList: The string Maya name of the network node created
    :rtype place2dTextureNodeList: str
    :param renderer: The renderer name
    :type renderer: str
    :param renderer: The autobump value, we store this value for Renderman and Arnold and disable enable the network
    :type renderer: bool
    """
    # Add attrs to each node ----------------------------
    for node in meshList:
        if not cmds.attributeQuery(NW_DISPLACE_MESH_ATTR, node=node, exists=True):
            cmds.addAttr(node, longName=NW_DISPLACE_MESH_ATTR, attributeType='message')
    for node in shadingGroupList:
        if not cmds.attributeQuery(NW_DISPLACE_SG_ATTR, node=node, exists=True):
            cmds.addAttr(node, longName=NW_DISPLACE_SG_ATTR, attributeType='message')
    for node in fileNodeList:
        cmds.addAttr(node, longName=NW_DISPLACE_FILE_ATTR, attributeType='message')
    for node in place2dTextureNodeList:
        cmds.addAttr(node, longName=NW_DISPLACE_PLACE2D_ATTR, attributeType='message')
    # displacementNode
    cmds.addAttr(displacementNode, longName=NW_DISPLACE_NODE_ATTR, attributeType='message')
    # Create Network node and connect to attrs ----------------------------
    networkNodeName = "{}_{}".format(NW_DISPLACE_NODE, shadingGroupList[0])
    networkNodeName = nodes.createNetworkNodeWithConnections(networkNodeName, NW_DISPLACE_MESH_ATTR,
                                                             meshList, createNetworkNode=True)
    nodes.createNetworkNodeWithConnections(networkNodeName, NW_DISPLACE_SG_ATTR,
                                           shadingGroupList, createNetworkNode=False)
    nodes.createNetworkNodeWithConnections(networkNodeName, NW_DISPLACE_FILE_ATTR,
                                           fileNodeList, createNetworkNode=False)
    nodes.createNetworkNodeWithConnections(networkNodeName, NW_DISPLACE_PLACE2D_ATTR,
                                           place2dTextureNodeList, createNetworkNode=False)
    nodes.createNetworkNodeWithConnections(networkNodeName, NW_DISPLACE_NODE_ATTR,
                                           [displacementNode], createNetworkNode=False)
    # Add renderer attribute
    cmds.addAttr(networkNodeName, longName=DISP_ATTR_RENDERER, dataType="string")
    cmds.setAttr(".".join([networkNodeName, DISP_ATTR_RENDERER]), renderer, type="string")
    # Add autobump attribute
    cmds.addAttr(networkNodeName, longName=DISP_ATTR_AUTOBUMP, attributeType="bool")
    cmds.setAttr(".".join([networkNodeName, DISP_ATTR_AUTOBUMP]), autoBump)


def getDisplaceNetworkNode(nodeList):
    """From a node list, find the displacement network nodes and return them as a list

    :param nodeList: Any maya node list
    :type nodeList: list(str)
    :return networkNodeList:  A list of Displacement Network names.  Empty list if nothing found.
    :rtype networkNodeList: list(str)
    """
    networkNodeList = list()
    filteredNodeList = list()
    # add shape nodes of objects
    for node in nodeList:
        if cmds.objectType(node) == "network":  # check for the network itself
            if NW_DISPLACE_NODE in node:  # do not place in the filtered list instead add to networkNodeList
                networkNodeList.append(node)
            else:
                filteredNodeList.append(node)  # is not a displace network so append
        if cmds.nodeType(node) == "transform":
            filteredNodeList += filtertypes.filterTypeReturnShapes([node], children=False, shapeType="mesh")
        filteredNodeList.append(node)
    for attr in NW_ATTR_LIST:
        networkNodeList += nodes.getNodeAttrConnections(filteredNodeList, attr)
    return networkNodeList


def getDisplaceNetworkSelected():
    """From the selected objects or sel nodes, find the displacement network nodes and return them as a list

    :return networkNodeList:  A list of Displacement Network names.  Empty list if nothing found.
    :rtype networkNodeList: list(str)
    """
    selNodes = cmds.ls(selection=True, long=True)
    if not selNodes:
        return list()
    return getDisplaceNetworkNode(selNodes)


def getDisplaceNetworkNodeAll():
    """Gets all displacement nodes in the scene and returns them as a list

    :return networkNodes: a list of displacement network nodes in the scene
    :rtype networkNodes: list(str)
    """
    return cmds.ls("*{}*".format(NW_DISPLACE_NODE), type="network")


def getDisplacementNetworkItems(networkNode):
    """Given a displacement network node name return its objects and shaders

    :param renderer: The renderer nice name
    :type renderer: str
    :param networkNode: Name of the network node that relates to the displacement needing deletion
    :type networkNode: str
    """
    # Get the meshList, shadingGroupList, fileNodeList, place2dTextureNodeList ------------------------
    meshList = nodes.getNodesFromNetworkNodeAttr(networkNode, NW_DISPLACE_MESH_ATTR)
    shadingGroupList = nodes.getNodesFromNetworkNodeAttr(networkNode, NW_DISPLACE_SG_ATTR)
    fileNodeList = nodes.getNodesFromNetworkNodeAttr(networkNode, NW_DISPLACE_FILE_ATTR)
    place2dTextureNodeList = nodes.getNodesFromNetworkNodeAttr(networkNode, NW_DISPLACE_PLACE2D_ATTR)
    displaceNodeList = nodes.getNodesFromNetworkNodeAttr(networkNode, NW_DISPLACE_NODE_ATTR)
    renderer = cmds.getAttr(".".join([networkNode, DISP_ATTR_RENDERER]))
    if displaceNodeList:
        displaceNode = displaceNodeList[0]
    else:
        displaceNode = ""
    return meshList, shadingGroupList, fileNodeList, place2dTextureNodeList, displaceNode, renderer


# ---------------------
# CREATE DISPLACEMENT
# ---------------------


def createDisplacementRenderer(renderer, nodeList, imagePath="", displacementType="VDM", tangentType="tangent",
                               autoBump=False, maxDivisions=5, scaleMultiplier=1, networkNodes=True, recreated=False,
                               bounds=0.1):
    """Creates displacement on multiple renderers based on nice names. "Arnold", "Renderman", "Redshift"
    From a given node list

    :param renderer:  renderer nice name "Arnold", "Renderman", "Redshift"
    :type renderer: str
    :param nodeList: list of nodes names that could be or are related to the shading group
    :type nodeList: list
    :param imagePath:  Optional path of the image, can be left empty str ""
    :type imagePath: str
    :param displacementType: either "VDM" (vector displacement map) or "height" (b&w)
    :type displacementType: str
    :param tangentType: either "tangent" or "object"
    :type tangentType: str
    :param networkNodes: create the network nodes for deletion and displacement management
    :type networkNodes: bool
    :param recreated: Only for messages, reports "recreated" to the user instead of 'created'
    :type recreated: bool
    :param bounds: Renderman only setting that can cull objects if too low
    :type bounds: bool
    """
    if renderer == ARNOLD:
        meshList, shadingGroupList, fileNodeList, \
        otherNodeList, displacementNode = arnolddisplacement.createDisplacementNodes(nodeList,
                                                                                     imagePath=imagePath,
                                                                                     displacementType=displacementType,
                                                                                     tangentType=tangentType,
                                                                                     autoBump=autoBump,
                                                                                     maxDivisions=maxDivisions,
                                                                                     scaleMultiplier=scaleMultiplier,
                                                                                     bounds=bounds)
    elif renderer == REDSHIFT:
        meshList, shadingGroupList, fileNodeList, \
        otherNodeList, displacementNode = redshiftdisplacement.createDisplacementNodes(nodeList,
                                                                                       imagePath=imagePath,
                                                                                       displacementType=displacementType,
                                                                                       tangentType=tangentType,
                                                                                       autoBump=autoBump,
                                                                                       maxDivisions=maxDivisions,
                                                                                       scaleMultiplier=scaleMultiplier,
                                                                                       bounds=bounds)
    elif renderer == RENDERMAN:
        meshList, shadingGroupList, fileNodeList, \
        otherNodeList, displacementNode = rendermandisplacement.createDisplacement(nodeList,
                                                                                   imagePath=imagePath,
                                                                                   displacementType=displacementType,
                                                                                   tangentType=tangentType,
                                                                                   scaleMultiplier=scaleMultiplier,
                                                                                   selectFilenode=True,
                                                                                   bounds=bounds)
    else:
        om2.MGlobal.displayError("Renderer Not Found")
        return False
    if not recreated:
        om2.MGlobal.displayInfo("Success: Displacement created on `{}`.  "
                                "See script editor for more information".format(shadingGroupList))
    else:
        om2.MGlobal.displayInfo("Success: Displacement recreated on `{}`.  "
                                "See script editor for more information".format(shadingGroupList))
    if not networkNodes:
        return shadingGroupList, fileNodeList, otherNodeList
    # Network nodes ----------------------
    displaceMessageNodeSetup(meshList, shadingGroupList, fileNodeList, otherNodeList, displacementNode, renderer,
                             autoBump)
    cmds.select(fileNodeList[0], replace=True)
    return meshList, shadingGroupList, fileNodeList, otherNodeList, displacementNode


def createDisplacementNodes(nodeList, renderer, imagePath="", displacementType="VDM", tangentType="tangent",
                            autoBump=False, maxDivisions=5, scaleMultiplier=1, recreated=False, bounds=0.1):
    meshList, shadingGroupList, fileNodeList, \
    place2dTextureNodeList, displacementNode = createDisplacementRenderer(renderer,
                                                                          nodeList,
                                                                          imagePath=imagePath,
                                                                          displacementType=displacementType,
                                                                          tangentType=tangentType,
                                                                          autoBump=autoBump,
                                                                          maxDivisions=maxDivisions,
                                                                          scaleMultiplier=scaleMultiplier,
                                                                          recreated=recreated,
                                                                          bounds=bounds)
    return meshList, shadingGroupList, fileNodeList, place2dTextureNodeList, displacementNode


def createDisplacementSelectedRenderer(renderer, imagePath="", displacementType="VDM", tangentType="tangent",
                                       autoBump=False, maxDivisions=5, scaleMultiplier=1, recreated=False, bounds=0.1):
    """Creates displacement on multiple renderers based on nice names. "Arnold", "Renderman", "Redshift"
    From selection

    The selection can be any selection type related to a shaders, meshes, transforms, shaders or shading groups

    :param renderer:  renderer nice name "Arnold", "Renderman", "Redshift"
    :type renderer: str
    :param imagePath:  Optional path of the image, can be left empty str ""
    :type imagePath: str
    :param displacementType: either "VDM" (vector displacement map) or "height" (b&w)
    :type displacementType: str
    :param tangentType: either "tangent" or "object"
    :type tangentType: str
    :param recreated: Only for messages, reports "recreated" to the user instead of 'created'
    :type recreated: bool
    :param bounds: Can cull objects if too low, so may need to use a larger value for all renderers
    :type bounds: float
    :return meshList: list of the mesh shape names that now are affected by the displacement
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
        om2.MGlobal.displayWarning('Nothing selected, please select a mesh, shader or shading group')
        return
    meshList, shadingGroupList, fileNodeList, \
    place2dTextureNodeList, displacementNode = createDisplacementRenderer(renderer,
                                                                          selObj,
                                                                          imagePath=imagePath,
                                                                          displacementType=displacementType,
                                                                          tangentType=tangentType,
                                                                          autoBump=autoBump,
                                                                          maxDivisions=maxDivisions,
                                                                          scaleMultiplier=scaleMultiplier,
                                                                          recreated=recreated,
                                                                          bounds=bounds)
    return meshList, shadingGroupList, fileNodeList, place2dTextureNodeList, displacementNode


# ---------------------
# CHECK VALID (NOT BROKEN) SETUPS
# ---------------------


def checkValidDisplacementNetwork(shadingGroupList, fileNodeList, place2dTextureNodeList, displaceNode,
                                  renderer):
    """Checks the displacement network is valid, see getDisplacementNetworkAttrs() for documentation

    This checks if the displacement has been broken, ie the user most likely manually deleted nodes.

    :return displacementValid:  True if valid, False if not valid (broken)
    :rtype displacementValid:
    """
    if not shadingGroupList:
        return False
    if not fileNodeList:
        return False
    if not place2dTextureNodeList:
        return False
    if not displaceNode:
        return False
    if not renderer:
        return False
    if renderer == RENDERMAN and len(place2dTextureNodeList) != 2:  # Renderman must have two nodes here
        return False
    return True


def getShaderAndNetworkMeshes(networkNode, shader):
    """Returns the mesh shape list that is attached to the network node, and also returns the shapes/faces connected \
    the shader.

    This is used for comparing the current shader assignments with the displacement nodes.

    :param networkNode: A displacement network node
    :type networkNode: str
    :param shader: A shader name
    :type shader: str
    :return networkShapesList: The mesh shapes attached to the network node
    :rtype networkShapesList: list(str)
    :return shadMeshList: The mesh shapes connected to the shader, can be faces
    :rtype shadMeshList: list(str)
    """
    networkShapesList = list()
    meshList, shadingGroupList, fileNodeList, \
    place2dTextureNodeList, displaceNode, renderer = getDisplacementNetworkItems(networkNode)
    shadMeshList = shaderutils.getMeshFaceFromShaderNodes([shader], selectMesh=False, objectsOnly=True)
    for mesh in meshList:  # mesh list is being returned as transform nodes which is bad, may need to fix this
        shapeList = cmds.listRelatives(mesh, shapes=True)
        for shape in shapeList:
            if not cmds.getAttr("{}.intermediateObject".format(shape)):  # if is not an intermediate object
                networkShapesList.append(shape)
    networkShapesList = namehandling.getLongNameList(networkShapesList)  # force long names
    shadMeshList = namehandling.getLongNameList(shadMeshList)  # force long names
    return networkShapesList, shadMeshList


def connectNewMeshesToNetwork(networkNode, shader, message=True):
    """Checks if a new object has been created and adds it to the meshList on the network node.

    Compares the meshList from the network node with the meshList from the shader assignment

    If a new mesh from shader assignments is not in the network meshList then connect it.

    :param networkNode: A displacement network node name
    :type networkNode: str
    :param shader: The shader name of the network node, usually grab it from the shading group
    :type shader: str
    :param message: Report new connections to the user?
    :type message: bool
    :return connectedMeshes: a list of meshes that were connected, should be an empty list most of the time
    :rtype connectedMeshes: list(str)
    """
    connectedMeshes = list()
    networkShapesList, shadMeshList = getShaderAndNetworkMeshes(networkNode, shader)
    if not shadMeshList:
        return list()
    for mesh in shadMeshList:
        if mesh not in networkShapesList:
            nodes.createNetworkNodeWithConnections(networkNode, NW_DISPLACE_MESH_ATTR,
                                                   [mesh], createNetworkNode=False)
            connectedMeshes.append(mesh)
            if message:
                om2.MGlobal.displayInfo("Mesh `{}` added to displacement network `{}`".format(mesh, networkNode))
    return connectedMeshes


def disconnectUnusedMeshesFromNetwork(networkNode, shader, message=True):
    """Checks the shader assigned mesh shapes against the network node shapes, if mismatch will disconnect meshes

    :param networkNode: A displacement network node
    :type networkNode: str
    :param shader: A shader name
    :type shader: str
    :param message: report the message to the user?
    :type message: bool
    :return disconnectedMeshes: Any disconnected meshes that have been disconnected, can be empty
    :rtype disconnectedMeshes: list(str)
    """
    disconnectedMeshes = list()
    networkShapesList, shadMeshList = getShaderAndNetworkMeshes(networkNode, shader)
    if not networkShapesList:
        return disconnectedMeshes  # will be empty
    for mesh in networkShapesList:
        if mesh not in shadMeshList:  # break the network connection
            cmds.disconnectAttr(".".join([networkNode, NW_DISPLACE_MESH_ATTR]),
                                ".".join([mesh, NW_DISPLACE_MESH_ATTR]))
            disconnectedMeshes.append(mesh)
            if message:
                om2.MGlobal.displayInfo("Mesh `{}` disconnected from displace network `{}`".format(mesh, networkNode))
    return disconnectedMeshes


# ---------------------
# RETURN DISPLACEMENT NETWORK ATTRIBUTE VALUES
# ---------------------


def getDisplacementNetworkAttrs(networkNode):
    """From a displacement network node return all the network node's related UI attribute values in a dictionary

    DISP_ATTR_TYPE: str "Tangent" or "Object"
    DISP_ATTR_DIVISIONS: int  (Redshift Arnold only, Renderman returns to 4)
    DISP_ATTR_SCALE: Float
    DISP_ATTR_AUTOBUMP: Bool
    DISP_ATTR_IMAGEPATH: string The file path
    DISP_ATTR_RENDERER: float (Renderman only)

    :param networkNode: A displacement network node name
    :type networkNode: str
    :return displacementAttrValDict: A dictionary with the values of the UI attributes
    :rtype displacementAttrValDict: dict()
    """
    displacementAttrValDict = dict()
    meshList, shadingGroupList, fileNodeList, \
    place2dTextureNodeList, displaceNode, renderer = getDisplacementNetworkItems(networkNode)
    if not checkValidDisplacementNetwork(shadingGroupList, fileNodeList, place2dTextureNodeList, displaceNode,
                                         renderer):
        return dict()  # the network is broken
    if renderer == ARNOLD:
        dtype, divisions, scale, autoBump, \
        image, bounds = arnolddisplacement.getDisplacementAttrValues(meshList,
                                                                     shadingGroupList,
                                                                     fileNodeList,
                                                                     place2dTextureNodeList,
                                                                     displaceNode)
    elif renderer == REDSHIFT:
        dtype, divisions, scale, autoBump, \
        image, bounds = redshiftdisplacement.getDisplacementAttrValues(meshList,
                                                                       shadingGroupList,
                                                                       fileNodeList,
                                                                       place2dTextureNodeList,
                                                                       displaceNode)
    elif renderer == RENDERMAN:
        dtype, divisions, scale, autoBump, \
        image, bounds = rendermandisplacement.getDisplacementAttrValues(meshList,
                                                                        shadingGroupList,
                                                                        fileNodeList,
                                                                        place2dTextureNodeList,
                                                                        displaceNode)
    displacementAttrValDict[DISP_ATTR_TYPE] = dtype
    displacementAttrValDict[DISP_ATTR_DIVISIONS] = divisions
    displacementAttrValDict[DISP_ATTR_SCALE] = scale
    if renderer == ARNOLD:
        displacementAttrValDict[DISP_ATTR_AUTOBUMP] = cmds.getAttr(".".join([networkNode, DISP_ATTR_AUTOBUMP]))
    else:
        displacementAttrValDict[DISP_ATTR_AUTOBUMP] = autoBump
    displacementAttrValDict[DISP_ATTR_IMAGEPATH] = image
    displacementAttrValDict[DISP_ATTR_BOUNDS] = bounds
    displacementAttrValDict[DISP_ATTR_RENDERER] = cmds.getAttr(".".join([networkNode, DISP_ATTR_RENDERER]))
    return displacementAttrValDict


def getDisplacementNetworkAttrsSel(renderer):
    """

    Type: Tangent or Object
    Divisions: int  (Redshift Arnold)
    Scale: Float
    Auto Bump: Bool
    Image Path: string
    Bounds: float (Renderman only)

    :param renderer:
    :type renderer:
    :return:
    :rtype:
    """
    networkNodeList = getDisplaceNetworkSelected()
    if not networkNodeList:
        return dict()
    return getDisplacementNetworkAttrs(renderer, networkNodeList[0])


def setDisplacementNetworkAttrs(displacementAttrDict, renderer, networkNode, message=True):
    """Sets displacement attributes on the Displacement Network

    :param displacementAttrDict:  Dictionary with displacement attr values see keys DISP_ATTR in shdmulticonstants.py
    :type displacementAttrDict: dict()
    :param renderer: Name of the renderer
    :type renderer: str
    :param networkNode: A displacement network node name
    :type networkNode: str
    :param message: Report the message to the user?
    :type message: bool
    :return success: True if successful, False if not
    :rtype success: bool
    """
    meshList, shadingGroupList, fileNodeList, \
    place2dTextureNodeList, displaceNode, renderer = getDisplacementNetworkItems(networkNode)
    if renderer == ARNOLD:
        # Fix autobump value, store on network node and query if the network is enabled
        cmds.setAttr(".".join([networkNode, DISP_ATTR_AUTOBUMP]), displacementAttrDict[DISP_ATTR_AUTOBUMP])  # store
        if not getEnableDisplacement(networkNode, renderer):
            displacementAttrDict[DISP_ATTR_AUTOBUMP] = False
    if renderer == ARNOLD:
        arnolddisplacement.setDisplacementAttrValues(meshList,
                                                     shadingGroupList,
                                                     fileNodeList,
                                                     place2dTextureNodeList,
                                                     displaceNode,
                                                     displacementAttrDict)
    elif renderer == REDSHIFT:
        redshiftdisplacement.setDisplacementAttrValues(meshList,
                                                       shadingGroupList,
                                                       fileNodeList,
                                                       place2dTextureNodeList,
                                                       displaceNode,
                                                       displacementAttrDict)
    elif renderer == RENDERMAN:
        rendermandisplacement.setDisplacementAttrValues(meshList,
                                                        shadingGroupList,
                                                        fileNodeList,
                                                        place2dTextureNodeList,
                                                        displaceNode,
                                                        displacementAttrDict)
    else:
        if message:
            om2.MGlobal.displayError("Renderer Not Found")
        return False
    if message:
        om2.MGlobal.displayInfo("Success: Displacement network updated `{}`".format(networkNode))
    return True


def setDisplacementNetworkAttrsNodes(nodeList, displacementAttrDict, renderer, message=True):
    """Sets all attributes on the network nodes associated with nodeList names

    :param nodeList: A list of any nodes names, often from selection
    :type nodeList: list(str)
    :param displacementAttrDict:  Dictionary with displacement attr values see keys DISP_ATTR in shdmulticonstants.py
    :type displacementAttrDict: dict()
    :param renderer: Name of the renderer
    :type renderer: str
    :param message: Report the message to the user?
    :type message: bool
    :return success: True if successful, False if not
    :rtype success: bool
    """
    networkNodeList = getDisplaceNetworkNode(nodeList)
    if not networkNodeList:
        return dict()
    return setDisplacementNetworkAttrs(displacementAttrDict, renderer, networkNodeList[0], message=message)


def setDisplacementNetworkAttrsSel(displacementAttrDict, renderer):
    """Sets displacement attributes on the Displacement Network

    :param displacementAttrDict:  Dictionary with displacement attr values see keys DISP_ATTR in shdmulticonstants.py
    :type displacementAttrDict: dict()
    :param renderer: Name of the renderer
    :type renderer: str
    :return success: True if successful, False if not
    :rtype success: bool
    """
    networkNodeList = getDisplaceNetworkSelected()
    if not networkNodeList:
        return dict()
    return setDisplacementNetworkAttrs(displacementAttrDict, renderer, networkNodeList[0])


def updateMeshes(renderer, newConnectionsList, breakConnectionsList, attrDict, enabled):
    """When a new mesh is connected, update the mesh to match the settings of the shader displacement

    :param renderer: The nice name of the renderer
    :type renderer: str
    :param newConnectionsList: A list of Maya meshes to update, these are newly connected
    :type newConnectionsList: list(str)
    :param breakConnectionsList: A list of Maya meshes to update, these are no longer part of the network
    :type breakConnectionsList: list(str)
    :param attrDict:  Dictionary with displacement attr values see keys DISP_ATTR in shdmulticonstants.py
    :type attrDict: dict()
    :param enabled: Is the displacement enabled?  Affects .aiSubdivType attribute
    :type enabled: bool
    """
    if renderer == RENDERMAN:  # Renderman needs no setup
        return
    if renderer == ARNOLD:
        arnolddisplacement.updateMeshes(newConnectionsList, breakConnectionsList, attrDict, enabled)
    elif renderer == REDSHIFT:
        redshiftdisplacement.updateMeshes(newConnectionsList, breakConnectionsList, attrDict, enabled)


# ---------------------
# ENABLE DISABLE DISPLACEMENT
# ---------------------


def enableDisplacement(networkNode, renderer, enableValue=1):
    """Enables the displacement network so that it renders or doesn't render.

    :param networkNode: A displacement network node name
    :type networkNode: str
    :param renderer: The name of the renderer
    :type renderer: str
    :param enableValue: True is enabled False is disabled
    :type enableValue: bool
    """
    autoBump = False
    meshList, shadingGroupList, fileNodeList, place2dTextureNodeList, \
    displaceNode, renderer = getDisplacementNetworkItems(networkNode)
    if not meshList or not displaceNode:
        return
    if renderer == ARNOLD:  # track the autobump as interferes with enable disable
        autoBump = cmds.getAttr(".".join([networkNode, DISP_ATTR_AUTOBUMP]))
    if renderer == REDSHIFT:
        redshiftdisplacement.setEnabled(meshList, enableValue)
    elif renderer == ARNOLD:  # Need to disconnect displacement
        arnolddisplacement.setEnabled(meshList, displaceNode, enableValue, autoBump)
    elif renderer == RENDERMAN:
        rendermandisplacement.setEnabled(displaceNode, enableValue)


def enableDisplacementSG(shadingGroup, renderer, enableValue=True):
    """Enables the displacement network so that it renders or doesn't render. Takes the shading group.

    :param shadingGroup: A shading group name
    :type shadingGroup: str
    :param renderer: The name of the renderer
    :type renderer: str
    :param enableValue: True is enabled False is disabled
    :type enableValue: bool
    """
    networkNodes = getDisplaceNetworkNode([shadingGroup])
    if not networkNodes:
        return
    networkNode = networkNodes[0]
    enableDisplacement(networkNode, renderer, enableValue=enableValue)


def enableDisableAll(renderer, enableValue=1, message=True):
    """Enables or disables all network nodes in the scene

    :param renderer: The nice name of the renderer
    :type renderer: str
    :param enableValue: 1 is enabled 0 is off (could also be a bool)
    :type enableValue: int
    :param message: Report the messages to the user?
    :type message: bool
    """
    networkNodeList = getDisplaceNetworkNodeAll()
    if not networkNodeList:
        if message:
            om2.MGlobal.displayWarning("No displacement networks found in the scene.")
        return
    for network in networkNodeList:
        enableDisplacement(network, renderer, enableValue=enableValue)
    if message:
        if enableValue:
            om2.MGlobal.displayInfo("Displacement networks enabled `{}`".format(networkNodeList))
        else:
            om2.MGlobal.displayInfo("Displacement networks disabled `{}`".format(networkNodeList))


def getEnableDisplacement(networkNode, renderer):
    """Retrieves the enable state of the displacement network as True (enabled) or False (disabled)

    Takes a network node

    :param networkNode: A displacement network node name
    :type networkNode: str
    :param renderer: The name of the renderer
    :type renderer: str
    :return isEnabled: True is enabled, False is disabled
    :rtype isEnabled: bool
    """
    meshList, shadingGroupList, fileNodeList, place2dTextureNodeList, \
    displaceNode, renderer = getDisplacementNetworkItems(networkNode)
    if not meshList or not displaceNode:
        return
    if renderer == REDSHIFT:
        return redshiftdisplacement.getEnabled(meshList)
    elif renderer == ARNOLD:
        return arnolddisplacement.getEnabled(meshList)
    elif renderer == RENDERMAN:
        return rendermandisplacement.getEnabled(displaceNode)


def getEnableDisplacementSG(shadingGroup, renderer):
    """Retrieves the enable state of the displacement network as True (enabled) or False (disabled)

    Takes a shading group

    :param shadingGroup: A shading group name
    :type shadingGroup: str
    :param renderer: The name of the renderer
    :type renderer: str
    :return isEnabled: True is enabled, False is disabled
    :rtype isEnabled: bool
    """
    networkNodes = getDisplaceNetworkNode([shadingGroup])
    if not networkNodes:
        return
    networkNode = networkNodes[0]
    return getEnableDisplacement(networkNode, renderer)


# ---------------------
# DELETE DISPLACEMENT
# ---------------------


def deleteDisplacementRenderer(renderer, meshList, fileNodeList, otherNodeList, displaceNode):
    """Deletes the displacement setup for a given renderer.

    Note will delete texture nodes even if they are used on other attributes. Uncommon in rendering

    Does not delete the displacement node

    :param renderer: The renderer nice name
    :type renderer: str
    :param meshList: list of the mesh shape names that are affected by the displacement
    :type meshList: list(str)
    :param fileNodeList: list of the fileNodes (texture) names that have been created
    :type fileNodeList: list(str)
    :param otherNodeList: list of the  place2dTextureNode names that have been created
    :type otherNodeList: list(str)
    :param displaceNode: the main displacement node
    :type displaceNode: list(str)
    :return success:  True if successful
    :rtype success: bool
    """
    if renderer == ARNOLD:
        arnolddisplacement.deleteDisplacementNodes(meshList, fileNodeList, otherNodeList, displaceNode)
    elif renderer == REDSHIFT:
        redshiftdisplacement.deleteDisplacementNodes(meshList, fileNodeList, otherNodeList)
    elif renderer == RENDERMAN:
        rendermandisplacement.deleteDisplacementNodes(meshList, fileNodeList, otherNodeList)
    else:
        om2.MGlobal.displayError("Renderer Not Found")
        return False
    return True


def deleteDisplacementNetwork(networkNode, message=True):
    """Given a displacement network node name, delete it's displacement setup

    :param renderer: The renderer nice name
    :type renderer: str
    :param networkNode: Name of the network node that relates to the displacement needing deletion
    :type networkNode: str
    """
    # Get the meshList, shadingGroupList, fileNodeList, place2dTextureNodeList ------------------------
    meshList, shadingGroupList, fileNodeList, \
    place2dTextureNodeList, displaceNode, renderer = getDisplacementNetworkItems(networkNode)
    renderer = cmds.getAttr(".".join([networkNode, DISP_ATTR_RENDERER]))
    # Delete the rest of the displacement setup related to the renderer ------------------------
    deleteDisplacementRenderer(renderer, meshList, fileNodeList, place2dTextureNodeList, displaceNode)
    # Remove network attributes from meshList and shadingGroupList ------------------------
    if shadingGroupList:
        for node in shadingGroupList:
            attributes.checkRemoveAttr(node, NW_DISPLACE_SG_ATTR)
    if meshList:
        for node in meshList:
            # Could be a transform so guarantee the shape node
            shapeList = filtertypes.filterTypeReturnShapes([node], children=False, shapeType="mesh")
            for shape in shapeList:  # most likely only one shape
                attributes.checkRemoveAttr(shape, NW_DISPLACE_MESH_ATTR)
    cmds.delete(networkNode)
    if message:
        om2.MGlobal.displayInfo("Displacement deleted related to `{}`".format(shadingGroupList))


def deleteBrokenDisplaceNetwork(networkNode):
    meshList, shadingGroupList, fileNodeList, \
    place2dTextureNodeList, displaceNode, renderer = getDisplacementNetworkItems(networkNode)
    deleteDisplacementRenderer(renderer, meshList, fileNodeList, place2dTextureNodeList, displaceNode)


def deleteDisplacementNetworkNodes(nodeList, message=True):
    networkNodeList = getDisplaceNetworkNode(nodeList)
    if not networkNodeList:
        if message:
            om2.MGlobal.displayWarning("No Zoo displacment found on the selected nodes")
        return False
    for networkNode in networkNodeList:
        deleteDisplacementNetwork(networkNode, message=message)
    return True


def deleteDisplacementNetworkSelected(message=True):
    """From the selected objects or sel nodes, find the displacement network and delete it.

    :param renderer: The renderer nice name
    :type renderer: str
    :param message: Report the message to the user
    :type message: bool
    """
    networkNodeList = getDisplaceNetworkSelected()
    if not networkNodeList:
        if message:
            om2.MGlobal.displayWarning("No Zoo displacment found on the selected nodes")
        return False
    for networkNode in networkNodeList:
        deleteDisplacementNetwork(networkNode, message=message)
    return True


def deleteBrokenDisplacementAll():
    """Deletes all broken networks in the scene
    """
    networkNodeList = getDisplaceNetworkNodeAll()
    brokenNetworks = list()
    if not networkNodeList:
        om2.MGlobal.displayWarning("No displacement networks found.")
        return
    for network in networkNodeList:
        meshList, shadingGroupList, fileNodeList, \
        place2dTextureNodeList, displaceNode, renderer = getDisplacementNetworkItems(network)
        renderer = cmds.getAttr(".".join([network, DISP_ATTR_RENDERER]))
        if not checkValidDisplacementNetwork(shadingGroupList, fileNodeList, place2dTextureNodeList,
                                             displaceNode, renderer):
            deleteBrokenDisplaceNetwork(network)
            cmds.delete(network)
            brokenNetworks.append(network)
    if not brokenNetworks:
        om2.MGlobal.displayInfo("All displacement networks are valid `{}`".format(networkNodeList))
        return
    else:
        om2.MGlobal.displayInfo("Broken displacement networks deleted `{}`".format(brokenNetworks))


# ---------------------
# SELECT NODES
# ---------------------


def selectNode(shadingGroup, nodeKey=NW_DISPLACE_NODE, selectNetworkNode=False):
    """Selects a node from the network using the dictionary keys:

        NW_DISPLACE_NODE = "zooDisplacementNetwork"
        NW_DISPLACE_MESH_ATTR = "zooDisplaceMeshConnect"
        NW_DISPLACE_SG_ATTR = "zooDisplaceSGConnect"
        NW_DISPLACE_FILE_ATTR = "zooDisplaceFileConnect"
        NW_DISPLACE_PLACE2D_ATTR = "zooDisplacePlace2dConnect"
        NW_DISPLACE_NODE_ATTR = "zooDisplaceNode"

    :param shadingGroup: The shading group node name that connects to all ncloth objects
    :type shadingGroup: str
    :param nodeKey: The dictionary key representing an attribute of the network node that links to the objects
    :type nodeKey: str
    :param selectNetworkNode: If True will ignore all other kwargs and select the network node only
    :type selectNetworkNode: bool
    """
    networkNodes = getDisplaceNetworkNode([shadingGroup])
    if not networkNodes:
        return
    networkNode = networkNodes[0]
    if selectNetworkNode:
        cmds.select(networkNode, replace=True)
        return
    meshList, shadingGroupList, fileNodeList, place2dTextureNodeList, \
    displaceNode, renderer = getDisplacementNetworkItems(networkNode)
    if nodeKey == NW_DISPLACE_NODE_ATTR:
        nodes = displaceNode
    elif nodeKey == NW_DISPLACE_MESH_ATTR:
        nodes = meshList
    elif nodeKey == NW_DISPLACE_MESH_ATTR:
        nodes = meshList
    elif nodeKey == NW_DISPLACE_SG_ATTR:
        nodes = shadingGroupList
    elif nodeKey == NW_DISPLACE_FILE_ATTR:
        nodes = fileNodeList
    elif nodeKey == NW_DISPLACE_PLACE2D_ATTR:
        nodes = place2dTextureNodeList
    else:
        return
    if nodes:
        cmds.select(nodes, replace=True, noExpand=True)  # For no expand for shading groups etc.


def selectShader(shaderName):
    """Simple function to select the shader by its name"""
    if cmds.objExists(shaderName):
        cmds.select(shaderName, replace=True)

