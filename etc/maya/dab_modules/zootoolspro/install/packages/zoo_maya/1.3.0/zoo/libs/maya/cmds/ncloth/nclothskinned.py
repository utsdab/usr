'''
Sets Up A Hybrid Skinned NCloth Setup based off a skinned mesh, usually clothing like a shirt. 

1. Select the skinned mesh
2. Run the script

All nCloth Nodes and settings will be applied. 
clothBlenderMesh is created so that the wrinkles can be blendshape paint removed
The script assumes regular proportioned human size character in Maya cms

To Do
- if mesh is not skinned make sure the warning shows!
- remove warnings on names with namespaces
- add a central control with common attributes in one place
- support presets
- add a UI
- support using the same nucleus and central control
- Add Scale Factor
- Change Prefs for play every frame
- Auto Cache Timeline Option
- add world space support for nCloth function, currently local
- add dictionaries as nodes returned are too many
'''

import maya.cmds as cmds
import maya.api.OpenMaya as om2
import maya.mel as mel

from zoo.libs.maya.cmds.objutils import shapenodes
from zoo.libs.maya.cmds.rig import nodes
from zoo.libs.maya.cmds.skin import bindskin
from zoo.libs.maya.cmds.objutils import namehandling
from zoo.libs.maya.cmds.blendshapes import blendshape
from zoo.libs.maya.cmds.ncloth import nclothconstants
from zoo.libs.maya.cmds.ncloth.nclothconstants import TSHIRT_PRESET_DICT, ORIGINAL_MESH_TFRM, POLYSMOOTH_MESH_TFRM, \
    CLOTH_MESH_TFRM, CLOTH_MESH_SHAPE, BLENDER_MESH_TFRM, BLENDSHAPE_ORIG_NODE, BLENDSHAPE_CLOTH_NODE, \
    NCLOTH_NODE, NUCLEUS_NODE, NCLOTH_TRANSFORM, ZOO_SK_NCLOTH_NETWORK, CLOTH_NODES_GRP, \
    SK_NCLOTH_NODE_DICT, NCA_BLEND_ATTR, SKINNED_NCLOTH_ATTRS, NUCLEUS_NCLOTH_ATTRS, BLEND_NCLOTH_ATTRS, \
    NCA_NETWORK_SUBD_DIVISIONS, NUCLEUS_DEFAULT_PRESET, NCA_NETWORK_PRESET_INDEX


# -----------------------------
# CREATE NCLOTH DEFAULT SETUP
# -----------------------------


def createNClothNodes(mesh, nClothTransform='nCloth', nucleusNode="nucleus", timeNode="time1", namespace="",
                      spaceLocal=True, startFrame=1, scale=1.0):
    """Creates a nCloth standard setup as it's not supported in maya cmds

    Currently local space setup, but shouldn't be hard to change to world as it's just a matter of different connections
    Could be issues with multiple setups using the same node, but usually a ncloth works on one mesh at a time I believe
    Should later support specifying the Nucleus node, will always create a new one currently

    Supports Namespaces and duplicated names
    Returns all objects and nodes

    :param mesh: The mesh to attach the nCLoth setup to
    :type mesh: str
    :param nClothTransform: the name of the nCloth (the transform node not the shade node) `Shape` is added for the shape
    :type nClothTransform: str
    :param nucleusNode: Name of the Nucleus node to be created, if already exists will add numbers
    :type nucleusNode: str
    :param timeNode: name of the time1 node, in Maya this is always in the scene and is always called `time1`
    :type timeNode: str
    :param namespace: Does the mesh have a namespace in the name?  if so it must be specified to be added to the new nodes
    :type namespace:  str (no `:` should be in the name)
    :param spaceLocal: Not currently supported. nCloth setups can also be in world, will need to add this option later
    :type spaceLocal: bool
    :param startTime: simulations start from this frame
    :type startTime: int
    :param scale: the spaceScale attribute on the nuleus node, affects total scale of the sims
    :type scale: float
    :return allNodesSet: all the nodes in a set
    :rtype: set
    """
    # Setup Initial Names, namespaces ---------------------
    if namespace:
        namespace = "{}:".format(namespace)
        nClothTransform = "".join([namespace, nClothTransform])
    nClothTransform = namehandling.nonUniqueNameNumber(nClothTransform)  # if exists increment name
    nClothShape = namehandling.nonUniqueNameNumber("{}Shape".format(nClothTransform))  # if exists increment name
    nucleusNode = namehandling.nonUniqueNameNumber("".join([namespace, nucleusNode]))  # if exists increment name

    # Create nCloth ---------------------
    nClothShapeTemp = cmds.createNode('nCloth', name=nClothShape, skipSelect=True)
    nClothTransformTemp = cmds.listRelatives(nClothShapeTemp, parent=True, fullPath=True)
    nClothShape = cmds.rename(nClothShapeTemp, nClothShape, ignoreShape=True)  # rename due to weirdness
    nClothTransform = cmds.rename(nClothTransformTemp, nClothTransform, ignoreShape=True)  # rename due to default name

    # Create Nucleus ---------------------
    nucleusNodeTemp = cmds.createNode('nucleus', name=nucleusNode, skipSelect=True)
    nucleusNode = cmds.rename(nucleusNodeTemp, nucleusNode)  # Must rename otherwise some name weirdness
    cmds.setAttr("{}.startFrame".format(nucleusNode), startFrame)
    cmds.setAttr("{}.spaceScale".format(nucleusNode), scale / 10.0)  # To adjust to cms divide by 10, is in meters

    # --------------------- Connect Nucleus, nCloth, Time
    # TODO Potentially needs to find next slot for nucleus node? outputObjects[0] See below
    cmds.connectAttr("{}.outputObjects[0]".format(nucleusNode), "{}.nextState".format(nClothShape), force=True)
    cmds.connectAttr("{}.startFrame".format(nucleusNode), "{}.startFrame".format(nClothShape), force=True)
    cmds.connectAttr("{}.currentState".format(nClothShape), "{}.inputActive[0]".format(nucleusNode), force=True)
    cmds.connectAttr("{}.startState".format(nClothShape), "{}.inputActiveStart[0]".format(nucleusNode), force=True)
    cmds.connectAttr("{}.outTime".format(timeNode), "{}.currentTime".format(nClothShape), force=True)
    cmds.connectAttr("{}.outTime".format(timeNode), "{}.currentTime".format(nucleusNode), force=True)

    # Build Cloth Mesh Output Shape Node ---------------------
    outputCloth = cmds.duplicate(mesh, name="{}_outputCloth".format(mesh), rr=True)
    meshShape = (shapenodes.filterNotOrigNodes(mesh, fullPath=True))[0]
    outputClothShape = (shapenodes.filterNotOrigNodes(outputCloth, fullPath=True))[0]

    # Shape parent the "Cloth Mesh Output Shape" to the mesh transform
    outputClothShape = (cmds.parent([outputClothShape, mesh], shape=True, relative=True))[0]
    cmds.delete(outputCloth)

    # Connect Shapes Nodes to nCloth Setup ---------------------
    cmds.connectAttr("{}.worldMesh[0]".format(meshShape), "{}.inputMesh".format(nClothShape))
    cmds.connectAttr("{}.outputMesh".format(nClothShape), "{}.inMesh".format(outputClothShape))

    # Create meshShape as hidden and intermediate obj (hide it as it's the incoming into the nCloth)  ------------
    cmds.setAttr("{}.intermediateObject".format(meshShape), 1)
    cmds.setAttr("{}.hiddenInOutliner".format(meshShape), 1)
    return nClothTransform, nClothShape, meshShape, outputClothShape, nucleusNode


def nucleusDefaults(nucleusNode, presetDict=NUCLEUS_DEFAULT_PRESET):
    """Set nucleus node defaults, see NUCLEUS_DEFAULT_PRESET dictionary

    :param presetDict: The nucleus preset dictionary of attributes and values
    :type presetDict: str
    """
    for attribute in presetDict:
        cmds.setAttr('.'.join([nucleusNode, attribute]), presetDict[attribute])


def nClothDefaults(nClothShape, presetDict=TSHIRT_PRESET_DICT):
    """Adjust nCloth defaults to a Tshirt like setup with some tweaks

    :param nClothShape: The name of the nCloth node to be adjusted (the shape node not transform)
    :type nClothShape: str
    :param presetDict: Preset Dictionary with ncloth attrs and values. See zoo.libs.maya.cmds.ncloth.nclothconstants
    :type presetDict: dict
    """
    for attribute in presetDict:
        cmds.setAttr('.'.join([nClothShape, attribute]), presetDict[attribute])


# -----------------------------
# CREATE SKINNED NCLOTH
# -----------------------------


def nClothSkinned(mesh, divisionsPolySmooth=2, nucleusNode='nucleus', nClothTransform='nCloth',
                  deleteDeadShapes=False, startFrame=1, scale=1.0, blendMultiply=1.0, presetDict=TSHIRT_PRESET_DICT,
                  nucleusAttrs=NUCLEUS_DEFAULT_PRESET, createNetworkNode=True, presetIndex=0, message=True):
    """Sets up a skinned hybrid nCloth setup with blendshapes for painting out and adjusting intensity:

        1. the nCloth setup is local, not world sticks to a skinned/deformed mesh, designed for wrinkle generation
        2. Mesh should be skinned or deformed, only works with animation
        3. Will create 4 meshes:
            - original (mesh) is left untouched it's shape info is are fed into the other objects
            - cloth object (has the cloth sim on it)
            - polySmooth mesh, is a duplicate of the original mesh with a polySmooth and no sim
            - blender mesh, is a new mesh with a blendshape to the cloth object so the user can weight in the nCloth
        4. All nCloth nodes are created as per normal
        5. nCloth defaults have no gravity and rough Maya t-shirt settings for defaults, or can be passed in
        Setup supports auto namespaces and duplicated names

    :param mesh: the mesh name to apply the cloth sim onto (transform node)
    :type mesh: str
    :param divisionsPolySmooth: how many divisions should the cloth mesh have for polygon density?
    :type divisionsPolySmooth: int
    :param nucleusNode: the name of the nucleus node to be created
    :type nucleusNode: str
    :param nClothTransform: the name of the nCloth node to be created (the transform node)
    :type nClothTransform: str
    :param startFrame: The frame to start the sim from
    :type startFrame: int
    :param scale: The scale of the ncloth wrinkles
    :type scale: float
    :param blendMultiply: Multiply the wrinkles by this amount, will affect a blendshape attribute
    :type blendMultiply: float
    :param presetDict: Preset Dictionary with ncloth attrs and values. See zoo.libs.maya.cmds.ncloth.nclothconstants
    :type presetDict: dict
    :param presetIndex: This is for GUI tracking, if a preset combo then track the index on the network node
    :type presetIndex: int
    :param createNetworkNode: Create the network node for tracking and deletion
    :type createNetworkNode: bool
    :param createNetworkNode: Create the network node for tracking and deletion
    :type createNetworkNode: bool
    :return skinnedNClothNodes: Dictionary of all nodes, uses keys from zoo.libs.maya.cmds.ncloth.nclothconstants
    :rtype skinnedNClothNodes: dict
    :return networkNodeName: The name of the network node created
    :rtype networkNodeName: str
    """
    longPrefix, namespace, mshShortName = namehandling.mayaNamePartTypes(mesh)
    clothObject = "{}_cloth".format(mshShortName)
    clothBlenderObject = "{}_clothBlender".format(mshShortName)

    # Create polySmooth mesh ---------------------
    polySmoothMesh = bindskin.duplicateMeshBeforeBind(mesh, fullPath=True, suffix="_polySmooth", message=message,
                                                      deleteDeadShapes=deleteDeadShapes)
    if not polySmoothMesh:
        mshShortUniqueName = namehandling.getUniqueShortName(mesh)
        polySmoothMesh = cmds.duplicate(mesh, name="{}_polySmooth".format(mshShortUniqueName))[0]

    # Shader Transfer cause can be out, supports component assign. ---------------------
    cmds.transferShadingSets(mesh, polySmoothMesh, sampleSpace=1, searchMethod=0)  # space=local, search=point
    cmds.delete(polySmoothMesh, constructionHistory=True)  # Delete history

    # Create cloth mesh ---------------------
    clothObject = cmds.duplicate(polySmoothMesh, name=clothObject, rr=True)[0]

    polySmoothNode1 = cmds.polySmooth(clothObject, dv=divisionsPolySmooth)[0]
    cmds.setAttr("{}.keepBorder".format(polySmoothNode1), 0)

    # Shader Transfer, supports component assign. polysmooth > clothObject ---------------------
    cmds.transferShadingSets(polySmoothMesh, clothObject, sampleSpace=1, searchMethod=0)  # space=local, search=point
    cmds.delete(clothObject, constructionHistory=True)  # Delete history

    # Create clothBlendMesh ---------------------
    clothBlenderObject = (cmds.duplicate(clothObject, name=clothBlenderObject, returnRootsOnly=True))[0]

    # PolySmoothMesh add the polySmooth and blendshape ---------------------
    polySmoothBlendShapeNode = cmds.blendShape(mesh, polySmoothMesh, name="{}Blend".format(polySmoothMesh))
    cmds.setAttr(".".join([polySmoothBlendShapeNode[0], mshShortName]), 1)
    polySmoothNode2 = (cmds.polySmooth(polySmoothMesh, dv=divisionsPolySmooth))[0]
    cmds.setAttr("{}.keepBorder".format(polySmoothNode2), 0)

    # Build NCloth ---------------------
    nClothTransform = "_".join([nClothTransform, mshShortName])
    nucleusNode = "_".join([nucleusNode, mshShortName])
    nClothTransform, nClothShape, hiddenClothShape, \
    outputClothShape, nucleusNode = createNClothNodes(clothObject,
                                                      nucleusNode=nucleusNode,
                                                      nClothTransform=nClothTransform,
                                                      namespace=namespace,
                                                      startFrame=startFrame,
                                                      scale=scale)

    # Be sure of the polySmoothMeshShape since it could be mistaken as an original shape node.
    polySmoothMeshShape = shapenodes.filterNotOrigNodes(polySmoothMesh, fullPath=True)[0]
    polySmoothShapeShortName = namehandling.mayaNamePartTypes(polySmoothMeshShape)[2]

    # Setup blendshape to hidden shape node before nCloth, needs to take off intermediate obj and then toggle back on
    cmds.setAttr("{}.intermediateObject".format(hiddenClothShape), 0)
    cmds.setAttr("{}.hiddenInOutliner".format(hiddenClothShape), 0)
    hiddenClothShapeShort = namehandling.mayaNamePartTypes(hiddenClothShape)[2]
    hiddenClothShapeBlendshape = cmds.blendShape(polySmoothMeshShape, hiddenClothShape,
                                                 name="{}Blend".format(hiddenClothShapeShort))[0]
    cmds.setAttr("{}.intermediateObject".format(hiddenClothShape), 1)
    cmds.setAttr("{}.hiddenInOutliner".format(hiddenClothShape), 1)
    cmds.setAttr('{}.{}'.format(hiddenClothShapeBlendshape, polySmoothShapeShortName), 1)

    #  Setup blendshape to the blender object ---------------------
    blenderBlend_orig = (cmds.blendShape(polySmoothMesh, clothBlenderObject,
                                         name="{}Blend_orig".format(clothBlenderObject)))[0]
    blenderBlend_cloth = (cmds.blendShape(clothObject, clothBlenderObject,
                                          name="{}Blend_cloth".format(clothBlenderObject)))[0]
    cmds.setAttr('{}.{}'.format(blenderBlend_orig, polySmoothMesh.split(":")[-1]), 1.0)
    cmds.setAttr('{}.{}'.format(blenderBlend_cloth, clothObject.split(":")[-1]), blendMultiply)  # blend multiply attr
    blendshape.renameBlendshape(blenderBlend_cloth, clothObject, NCA_BLEND_ATTR, message=False)

    # Setup nucleus and nCloth attribute defaults -----------------------
    nucleusDefaults(nucleusNode, presetDict=nucleusAttrs)
    nClothDefaults(nClothShape, presetDict=presetDict)
    # Cleanup: hide all meshes except the clothBlenderMesh, and group the nucleusNode and nClothNode -------
    cmds.setAttr('{}.visibility'.format(mesh), 0)
    cmds.setAttr('{}.visibility'.format(polySmoothMesh), 0)
    cmds.setAttr('{}.visibility'.format(clothObject), 0)
    groupName = 'clothNodes_{}_grp'.format(mshShortName)
    clothNodes_grp = cmds.group(nucleusNode, nClothTransform, name=groupName)  # TODO name nicely
    # network node for tracking
    skinnedNClothNodes = {ORIGINAL_MESH_TFRM: mesh,
                          POLYSMOOTH_MESH_TFRM: polySmoothMesh,
                          CLOTH_MESH_TFRM: clothObject,
                          CLOTH_MESH_SHAPE: outputClothShape,
                          BLENDER_MESH_TFRM: clothBlenderObject,
                          BLENDSHAPE_ORIG_NODE: blenderBlend_orig,
                          BLENDSHAPE_CLOTH_NODE: blenderBlend_cloth,
                          NCLOTH_NODE: nClothShape,
                          NCLOTH_TRANSFORM: nClothTransform,
                          NUCLEUS_NODE: nucleusNode,
                          CLOTH_NODES_GRP: clothNodes_grp}
    if createNetworkNode:
        networkNodeName = skinnedNClothMessageNodeSetup(skinnedNClothNodes,
                                                        divisionsPolySmooth,
                                                        presetIndex=presetIndex)
    else:
        networkNodeName = ""
    # Success message ---------------------
    om2.MGlobal.displayInfo("Success: A Skinned NCloth setup has been created and "
                            "applied to the mesh `{}`".format(namehandling.getShortName(mesh)))
    return skinnedNClothNodes, networkNodeName


def nClothSkinnedSelected(divisionsPolySmooth=2, deleteDeadShapes=True, startFrame=1, scale=1.0, blendMultiply=1.0,
                          presetDict=TSHIRT_PRESET_DICT, nucleusAttrs=NUCLEUS_DEFAULT_PRESET, presetIndex=0,
                          message=True):
    """Sets up a skinned hybrid nCloth setup with blendshapes for painting out and adjusting intensity
    Will work off the first selected object which should be nCloth compatible, usually a mesh (transform node)

    See function docstring nClothSkinned() for documentation
    """
    networkNodeList = list()
    objList = cmds.ls(selection=True, long=True)
    if not objList:
        if message:
            om2.MGlobal.displayWarning("No Mesh Selected, Please Select A Mesh")
        return list()
    for obj in objList:
        skinnedNClothNodes, networkNode = getSkinnedNClothDictNode(obj)
        if skinnedNClothNodes:
            if message:
                obj = namehandling.getShortName(obj)
                om2.MGlobal.displayWarning("This mesh `{}` is already connected to a Skinned Cloth setup `{}`.  "
                                           "Please delete before rebuilding.".format(obj, networkNode))
            return list()
        skinnedNClothNodes, networkNodeName = nClothSkinned(obj,
                                                            divisionsPolySmooth=divisionsPolySmooth,
                                                            deleteDeadShapes=deleteDeadShapes,
                                                            startFrame=startFrame,
                                                            scale=scale,
                                                            blendMultiply=blendMultiply,
                                                            presetDict=presetDict,
                                                            nucleusAttrs=nucleusAttrs,
                                                            presetIndex=presetIndex,
                                                            message=message)
        networkNodeList.append(networkNodeName)
    return networkNodeList


# -----------------------------
# CREATE SKINNED NCLOTH NETWORK NODE
# -----------------------------


def skinnedNClothMessageNodeSetup(skinnedNClothNodes, divisionsPolySmooth, presetIndex=0):
    """Connects skinned NCloth nodes to a network node named "zooSkNClothNetwork_*" (ZOO_SK_NCLOTH_NETWORK)

    The network node can be handy later, for deleting or managing objects, manage attrs etc

    :param skinnedNClothNodes: Dictionary of all nodes, uses keys from zoo.libs.maya.cmds.ncloth.nclothconstants
    :type skinnedNClothNodes: dict
    :return networkNodeName: The name of the network node created
    :rtype networkNodeName: str
    """
    # Create Network node and connect to attrs ----------------------------
    longSuffix, namespace, origObj = namehandling.mayaNamePartTypes(skinnedNClothNodes[ORIGINAL_MESH_TFRM])
    networkNodeName = "{}_{}".format(ZOO_SK_NCLOTH_NETWORK, origObj)
    networkNodeName = cmds.createNode('network', name=networkNodeName)
    for key in skinnedNClothNodes:
        nodes.messageNodeObjs(networkNodeName, [skinnedNClothNodes[key]], key,
                              createNetworkNode=False)
    # GUI Tracking SubDs
    cmds.addAttr(networkNodeName, longName=NCA_NETWORK_SUBD_DIVISIONS)
    cmds.setAttr(".".join([networkNodeName, NCA_NETWORK_SUBD_DIVISIONS]), divisionsPolySmooth)
    # GUI Tracking Preset Index
    cmds.addAttr(networkNodeName, longName=NCA_NETWORK_PRESET_INDEX)
    cmds.setAttr(".".join([networkNodeName, NCA_NETWORK_PRESET_INDEX]), presetIndex)
    return networkNodeName


# -----------------------------
# RETRIEVE SKINNED NCLOTH NETWORK
# -----------------------------


def getNClothNetworkObjs(nodeList):
    """Returns a network node from an object list, will return "" if none.

    :param nodeList: A list of Maya node names, for example the selection
    :type nodeList: list(str)
    :return networkNode: A skinned NCloth network node name, "" if none.
    :rtype networkNode: str
    """
    for node in nodeList:
        for key in SK_NCLOTH_NODE_DICT:
            networkNode = nodes.getNodeAttrConnections([node], key, shapes=True)  # loop through all keys
            if networkNode:  # found
                return networkNode
    return ""


def getSkinnedNClothDictNetwork(networkNode):
    """Returns a dictionary of connected nodes to the network node, uses SK_NCLOTH_NODE_DICT to categorize the objects

    If an expected object does not exist it will not be in the dictionary at all

    :param networkNode: A skinned NCloth network node name
    :type networkNode: str
    :return skinnedNClothNodes: A dictionary of nodes as values with SK_NCLOTH_NODE_DICT as keys
    :rtype skinnedNClothNodes: dict()
    """
    skinnedNClothNodes = dict()
    for key in SK_NCLOTH_NODE_DICT:  # retrieve nodes and build dict ----------------------------
        # Keys are the attributes to look for
        obj = nodes.getNodeAttrConnections([networkNode], key, shapes=True)
        if obj:
            skinnedNClothNodes[key] = obj[0]  # may be issues here if multiple meshes?
    return skinnedNClothNodes


def getSkinnedNClothDictNode(node):
    """From a node, see if it is connected to a skin nCloth network, if so return:

        1. skinnedNClothNodes: dict (all nodes related to the setup in a nice dict)
        2. networkNode: The network node name that connects to all objects

    Will return dict() and "" if no node found

    :param node: Any maya node that may be a part of a skin nCloth network
    :type node: str
    :return skinnedNClothNodes: skinnedNClothNodes dict (all nodes related to the setup in a nice dict)
    :rtype skinnedNClothNodes: dict
    :return networkNode: The network node name that connects to all objects
    :rtype networkNode: str
    """
    # Check object is a network node
    if ZOO_SK_NCLOTH_NETWORK in node and cmds.nodeType(node) == "network":
        networkNodeList = [node]
    else:
        networkNodeList = getNClothNetworkObjs([node])
    if not networkNodeList:  # No network found
        return dict(), networkNodeList
    skinnedNClothNodes = getSkinnedNClothDictNetwork(networkNodeList[0])

    return skinnedNClothNodes, networkNodeList[0]


def getNetworkNodesAll():
    """Gets all skinned nCloth nodes in the scene and returns them as a list

    :return networkNodes: a list of displacement network nodes in the scene
    :rtype networkNodes: list(str)
    """
    return cmds.ls("*{}*".format(ZOO_SK_NCLOTH_NETWORK), type="network")


def getSkinnedNClothDictSelected():
    """From the selection returns:

        1. skinnedDictList list(dict) A list of dicts with nodes related to each setup in a nice dict
        2. networkNodeList list(str) A list of network node names

    :return skinnedDictList: A list of dicts with nodes related to each setup in a nice dict
    :rtype skinnedDictList: list(dict)
    :return networkNodeList: A list of network node names
    :rtype networkNodeList: list(str)
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        return list(), list()
    skinnedDictList = list()
    networkNodeList = list()
    for obj in selObjs:
        skinnedNClothNodes, networkNode = getSkinnedNClothDictNode(obj)
        if skinnedNClothNodes:
            skinnedDictList.append(skinnedNClothNodes)
            networkNodeList.append(networkNode)
    return skinnedDictList, networkNodeList


# -----------------------------
# VALIDATE SKINNED NCLOTH SETUP
# -----------------------------


def validateNClothNetwork(skinnedNClothNodes):
    """Returns whether a network is valid from it's skinnedNClothNodes dict

    If any keys of SK_NCLOTH_NODE_DICT are not found in skinnedNClothNodes, then objects are missing and invalid

    :param skinnedNClothNodes: skinnedNClothNodes dict (all nodes related to the setup in a nice dict)
    :type skinnedNClothNodes: dict()
    :return isValid: True if valid, False if objects are missing
    :rtype isValid: bool
    """
    for key in SK_NCLOTH_NODE_DICT:
        if key not in skinnedNClothNodes:
            return False
    return True


def validateNClothNetworkNodes(objList):
    """From a list of Maya objects Returns whether the skinned nCloth network is valid and the network node name

    :param objList: A list of Maya object names
    :type objList: list(str)
    :return isValid: True if valid, False if objects are missing
    :rtype isValid: bool
    :return networkNode: The network node name that connects to all objects
    :rtype networkNode: str
    """
    for obj in objList:
        skinnedNClothNodes, networkNode = getSkinnedNClothDictNode(obj)
        if networkNode:
            break
    return validateNClothNetwork(skinnedNClothNodes), networkNode


# -----------------------------
# DELETE SKINNED NCLOTH SETUP
# -----------------------------


def deleteSkinnedNClothNodes(skinnedDictList):
    """Deletes objects from a Skinned NCloth setup from a dictionary of each object.

    Iterates over the keys and deletes each object while skipping the ORIGINAL_MESH_TFRM

    :param skinnedDictList: skinnedNClothNodes dict (all nodes related to the setup in a nice dict)
    :type skinnedDictList: dict()
    """
    for skinnedDict in skinnedDictList:
        delObjList = list()
        # Skip these objects -----------------------
        if ORIGINAL_MESH_TFRM in skinnedDict:
            skinnedDict.pop(ORIGINAL_MESH_TFRM)   # then skip, we don't want to delete
        # Do the delete --------------------------------
        for key in skinnedDict:
            delObjList.append(skinnedDict[key])
        if NCLOTH_NODE in skinnedDict:  # Might have been deleted by a user, not sure why doing this?
            if cmds.objExists(skinnedDict[NCLOTH_NODE]):
                delObjList.append(skinnedDict[NCLOTH_NODE])
        cmds.delete(delObjList)  # delete the entire list in one go, easier


def bakeSkinnedNClothNodes(skinnedDictList):
    """Bakes the current Skinned NCloth blender mesh in it's current position and removes all other nodes.

        Iterates over the keys and deletes each object while skipping the BLENDER_MESH_TFRM

        :param skinnedDictList: skinnedNClothNodes dict (all nodes related to the setup in a nice dict)
        :type skinnedDictList: dict()
        """
    for skinnedDict in skinnedDictList:
        delObjList = list()
        cmds.delete(skinnedDict[BLENDER_MESH_TFRM], constructionHistory=True)  # delete history
        if cmds.objExists(skinnedDict[ORIGINAL_MESH_TFRM]) and ORIGINAL_MESH_TFRM in skinnedDict:  # check reference
            if cmds.referenceQuery(skinnedDict[ORIGINAL_MESH_TFRM], isNodeReferenced=True):
                skinnedDict.pop(ORIGINAL_MESH_TFRM)
        # Skip these objects -----------------------
        if BLENDSHAPE_ORIG_NODE in skinnedDict:  # then skip, already deleted by delete history
            skinnedDict.pop(BLENDSHAPE_ORIG_NODE)
        if BLENDSHAPE_CLOTH_NODE in skinnedDict:  # then skip, already deleted by delete history
            skinnedDict.pop(BLENDSHAPE_CLOTH_NODE)
        if BLENDER_MESH_TFRM in skinnedDict:  # then skip, we don't want to delete
            skinnedDict.pop(BLENDER_MESH_TFRM)
        # Do the delete --------------------------------
        for key in skinnedDict:
            delObjList.append(skinnedDict[key])
        cmds.delete(delObjList)  # delete the entire list in one go, easier


def deleteSkinnedNClothSetupNetwork(networkNode, selectOrigMesh=True, bakeCurrent=False, message=True):
    """Deletes or bakes a Skinned NCloth Setup from the network node name.

    Bake will leave the nCloth blender mesh in it's current state.

    :param networkNode: The network node name that connects to all ncloth objects
    :type networkNode: str
    :param selectOrigMesh: Will select the original mesh after the delete, default True
    :type selectOrigMesh: bool
    :param message: Report messages to the user?
    :type message: bool
    """
    skinnedDict = getSkinnedNClothDictNetwork(networkNode)
    if not bakeCurrent:
        deleteSkinnedNClothNodes([dict(skinnedDict)])  # don't operate on the dict
        remainingObject = skinnedDict[ORIGINAL_MESH_TFRM]
    else:
        bakeSkinnedNClothNodes([dict(skinnedDict)])  # don't operate on the dict
        remainingObject = skinnedDict[BLENDER_MESH_TFRM]
    if remainingObject:
        cmds.setAttr("{}.visibility".format(remainingObject), True)
        if not bakeCurrent:
            cmds.deleteAttr(".".join([remainingObject, ORIGINAL_MESH_TFRM]))  # remove the network attr
        else:
            cmds.deleteAttr(".".join([remainingObject, BLENDER_MESH_TFRM]))  # remove the network attr
        if selectOrigMesh:
            cmds.select(remainingObject, replace=True)
    cmds.delete(networkNode)
    if message:
        if not bakeCurrent:
            om2.MGlobal.displayInfo("Success: NCloth setup deleted {}".format(networkNode))
        else:
            om2.MGlobal.displayInfo("Success: NCloth setup baked to current {}".format(networkNode))


# -----------------------------
# SET ATTRS SKINNED NCLOTH SETUP
# -----------------------------


def setAttrNetwork(networkNode, nodeKey, attribute, value):
    """Generic function that sets an attribute and checks if it exists

    Needs a node key (dictionary key) to specify the node to set the attribute on.

    A list of keys can be found in the dictionary ZOO_SK_NCLOTH_NETWORK

    :param networkNode: The network node name that connects to all ncloth objects
    :type networkNode: str
    :param nodeKey: A dictionary key who's value is the node to set
    :type nodeKey: str
    :param attribute: The attribute to set
    :type attribute: str
    :param value: The value to set the attribute
    :type value: float
    :return success: The attribute was set successfully
    :rtype success: bool
    """
    skinnedNClothNodes = getSkinnedNClothDictNetwork(networkNode)
    if not skinnedNClothNodes:
        return False
    objToSet = skinnedNClothNodes[nodeKey]
    if cmds.objExists(objToSet):
        cmds.setAttr(".".join([objToSet, attribute]), value)
        return True
    return False


def nClothSetAttrNetwork(networkNode, attribute, value):
    """Sets an attribute on the nCloth node

    :param networkNode: The network node name that connects to all ncloth objects
    :type networkNode: str
    :param attribute: The attribute to set
    :type attribute: str
    :param value: The value to set the attribute
    :type value: float
    :return success: The attribute was set successfully
    :rtype success: bool
    """
    return setAttrNetwork(networkNode, NCLOTH_NODE, attribute, value)


def nucleusSetAttrNetwork(networkNode, attribute, value):
    """Sets an attribute on the nucleus node

    :param networkNode: The network node name that connects to all ncloth objects
    :type networkNode: str
    :param attribute: The attribute to set
    :type attribute: str
    :param value: The value to set the attribute
    :type value: float
    :return success: The attribute was set successfully
    :rtype success: bool
    """
    return setAttrNetwork(networkNode, NUCLEUS_NODE, attribute, value)


def blendshapeSetAttrNetwork(networkNode, attribute, value):
    """Sets an attribute on the blendshape node

    :param networkNode: The network node name that connects to all ncloth objects
    :type networkNode: str
    :param attribute: The attribute to set
    :type attribute: str
    :param value: The value to set the attribute
    :type value: float
    :return success: The attribute was set successfully
    :rtype success: bool
    """
    return setAttrNetwork(networkNode, BLENDSHAPE_CLOTH_NODE, attribute, value)


def enableDisableNucleus(selObjs, value):
    """Finds the related nucleus node and enables or disables it, used while caching which requires selection.

    :param selObjs: A list of Maya node names
    :type selObjs: list(str)
    :param value: True will be enabled, False disables
    :type value: bool
    :return nucleusNodes: A list of nucleus node names
    :rtype nucleusNodes: list(str)
    :return success: Was a node or nodes set
    :rtype success: bool
    """
    success = False
    nucleusNodes = list()
    for obj in selObjs:
        skinnedNClothNodes, networkNode = getSkinnedNClothDictNode(obj)
        if skinnedNClothNodes:
            cmds.setAttr("{}.enable".format(skinnedNClothNodes[NUCLEUS_NODE]), value)
            nucleusNodes.append(skinnedNClothNodes[NUCLEUS_NODE])
            success = True
    nucleusNodes = set(nucleusNodes)
    cmds.select(selObjs, replace=True)
    return nucleusNodes, success


def setPresetIndexNetwork(networkNode, value):
    """Sets the preset index value on the network node, usually after the combo box has changed"""
    cmds.setAttr(".".join([networkNode, NCA_NETWORK_PRESET_INDEX]), value)


# -----------------------------
# GET ATTRS SKINNED NCLOTH SETUP
# -----------------------------


def getAttrDictNetworkAll(networkNode):
    """Gets all attribute values of the nodes:

        nCloth: see dict keys SKINNED_NCLOTH_ATTRS
        nucleus: see dict keys NUCLEUS_NCLOTH_ATTRS
        blendshape: see dict keys BLEND_NCLOTH_ATTRS

    Only keys in the dicts are recorded.

    Also returns the networks subD division count for GUI display

    :param networkNode: The network node name that connects to all ncloth objects
    :type networkNode: str
    :return nclothSkinAttrValueDict: nCloth dictionary of attributes as keys and values
    :rtype nclothSkinAttrValueDict: dict()
    :return nucleusAttrValueDict: nucleus dictionary of attributes as keys and values
    :rtype nucleusAttrValueDict: dict()
    :return blendshapeAttrValueDict: blendshape dictionary of attributes as keys and values
    :rtype blendshapeAttrValueDict: dict()
    :return subDDivisions: Number of subdivisions of the Skinned NCloth setup
    :rtype subDDivisions: int
    """
    nclothSkinAttrValueDict = dict()
    nucleusAttrValueDict = dict()
    blendshapeAttrValueDict = dict()
    skinnedNClothNodes = getSkinnedNClothDictNetwork(networkNode)
    if not skinnedNClothNodes:
        return dict(), dict(), dict(), None
    valid = validateNClothNetwork(skinnedNClothNodes)
    if not valid:
        return dict(), dict(), dict(), None
    nClothNode = skinnedNClothNodes[NCLOTH_NODE]
    nucleusNode = skinnedNClothNodes[NUCLEUS_NODE]
    blendshapeNode = skinnedNClothNodes[BLENDSHAPE_CLOTH_NODE]
    for attr in SKINNED_NCLOTH_ATTRS:
        nclothSkinAttrValueDict[attr] = cmds.getAttr(".".join([nClothNode, attr]))
    for attr in NUCLEUS_NCLOTH_ATTRS:
        nucleusAttrValueDict[attr] = cmds.getAttr(".".join([nucleusNode, attr]))
    for attr in BLEND_NCLOTH_ATTRS:
        blendshapeAttrValueDict[attr] = cmds.getAttr(".".join([blendshapeNode, attr]))
    subDDivisions = cmds.getAttr(".".join([networkNode, NCA_NETWORK_SUBD_DIVISIONS]))
    presetIndex = cmds.getAttr(".".join([networkNode, NCA_NETWORK_PRESET_INDEX]))
    return nclothSkinAttrValueDict, nucleusAttrValueDict, blendshapeAttrValueDict, subDDivisions, presetIndex


def getNucleusEnabledState(networkNode):
    """Returns the state of the Nucleus attribute "enable" 1 or 0 on or off.

    :param networkNode: The network node name that connects to all ncloth objects
    :type networkNode: str
    :return enabledState: 1 is enabled or 0 is off
    :rtype enabledState: bool
    """
    skinnedNClothNodes = getSkinnedNClothDictNetwork(networkNode)
    nucleusNode = skinnedNClothNodes[NUCLEUS_NODE]
    if not nucleusNode:
        return False
    return cmds.getAttr(".".join([nucleusNode, "enable"]))


# -----------------------------
# CREATE & DELETE GEO CACHE
# -----------------------------


def selectClothMeshes(networkNode):
    """Selects the nCloth mesh which is necessary for cache operations, returns the transform and shape nodes

    :param networkNode: The network node name that connects to all ncloth objects
    :type networkNode: str
    :return clothMesh: nCloth transform node name, will be "" if empty
    :rtype clothMesh: str
    :return clothShape: nCloth shape node name, will be "" if empty
    :rtype clothShape: str
    """
    skinnedNClothNodes = getSkinnedNClothDictNetwork(networkNode)
    if skinnedNClothNodes:  # then try to select the cloth mesh instead
        clothMesh = skinnedNClothNodes[CLOTH_MESH_TFRM]
        clothShape = skinnedNClothNodes[CLOTH_MESH_SHAPE]
        if clothMesh:  # Then select those instead, better to cache the cloth meshes
            cmds.select(clothMesh, replace=True)
        return clothMesh, clothShape
    return "", ""


def createCache(networkNode, delCacheFirst=True):
    """Hardcoded mel for the menu item:

        Cache > Create New Cache

    Defaults with "One file" set to be True

    cmds.cacheFile() is the python but would be annoying to use as it doesn't reconnect the nodes to the current mesh.

    :param delCacheFirst: Will try to delete existing caches before creating new.
    :type delCacheFirst: bool
    """
    rememberSelection = cmds.ls(selection=True)
    clothMesh, clothShape = selectClothMeshes(networkNode)
    if not clothMesh:
        return
    if delCacheFirst:
        # Check if cache is connected as need to avoid bad mel error
        checkDeleteConnectedCache(networkNode, clothShape)
    mel.eval('doCreateGeometryCache 6 { "2", "1", "10", "OneFile", "1", "","0","","0", '
             '"add", "0", "1", "1","0","1","mcx","0" }')
    # Disable nucleus
    nucleusNodes, success = enableDisableNucleus([clothMesh], False)
    cmds.select(rememberSelection, replace=True)
    if success:
        om2.MGlobal.displayInfo(
            "Success: Geometry Cached {}.  Nucleus nodes disabled {}".format(clothMesh, nucleusNodes))


def deleteCache(networkNode, reportNoCache=True, checkClothMeshes=True):
    """Hardcoded mel for the menu item:

        Cache > Delete Cache

    Delete Files = True

    :param reportNoCache: Reports a message if no cache's found
    :type reportNoCache: bool
    """
    rememberSelection = cmds.ls(selection=True)
    if checkClothMeshes:
        clothMesh, clothShape = selectClothMeshes(networkNode)  # Will select the cloth meshes if they can
        if not clothMesh:
            return
    try:
        # do the delete cache
        mel.eval('deleteCacheFile 3 { "delete", "", "geometry" }')
    except RuntimeError:  # probably no cache's found to remove
        if reportNoCache:
            om2.MGlobal.displayWarning("No cache found on object {}".format(clothMesh))
        cmds.select(rememberSelection, replace=True)
        return
    # Enable nucleus
    nucleusNodes, success = enableDisableNucleus([clothMesh], True)
    cmds.select(rememberSelection, replace=True)
    if success:
        om2.MGlobal.displayInfo("Success: Geometry cache deleted {}.  "
                                "Nucleus nodes enabled {}".format(clothMesh, nucleusNodes))


def checkConnectedCache(clothShape):
    """Checks the shape node is connected to a cache with a hardcoded name "cache"

    :param clothShape: The nCloth shape node name
    :type clothShape: str
    :return cacheExists: True if a cache has been found
    :rtype cacheExists: bool
    """
    cacheObject = cmds.listConnections("{}.inMesh".format(clothShape), destination=False, source=True)
    if cacheObject:
        if "cache" in cacheObject[0]:
            return True
    return False


def checkDeleteConnectedCache(networkNode, clothShape):
    """Checks the shape node is connected to a cache with a hardcoded name "cache" and if so will delete it from disk

    Similar to:

        Cache > Create New Cache

    :param networkNode: The network node name that connects to all ncloth objects
    :type networkNode: str
    :param clothShape: The nCloth shape node name
    :type clothShape: str
    """
    if clothShape:  # test if any has a cache and if so remove.
        if checkConnectedCache(clothShape):  # if cache found
            rememberObjs = cmds.ls(selection=True)
            cmds.select(clothShape, replace=True)
            deleteCache(networkNode, reportNoCache=False)
            cmds.select(rememberObjs, replace=True)


# -----------------------------
# BLENDSHAPE MANAGEMENT
# -----------------------------


def paintNClothBlendshape(networkNode):
    """Opens the paint weights window for the Blendshape weights, sets the paint color to black (value) and .5 opacity

    :param networkNode: The network node name that connects to all ncloth objects
    :type networkNode: str
    """
    skinnedNClothNodes = getSkinnedNClothDictNetwork(networkNode)
    blendshape = skinnedNClothNodes[BLENDSHAPE_CLOTH_NODE]
    mel.eval('artSetToolAndSelectAttr("artAttrCtx", "blendShape.{}.baseWeights");'.format(blendshape))
    cmds.toolPropertyWindow()  # Opens the tool window
    currentContext = cmds.currentCtx()
    cmds.artAttrCtx(currentContext, edit=True, value=0.0, opacity=0.5)


# -----------------------------
# SELECT NODES
# -----------------------------


def selectNode(networkNode, nodeKey=BLENDSHAPE_CLOTH_NODE, selectNetworkNode=False):
    """Selects a node from the network using the dictionary keys:

        ORIGINAL_MESH_TFRM = "originalMeshTransform"
        POLYSMOOTH_MESH_TFRM = "polySmoothMeshTransform"
        CLOTH_MESH_TFRM = "clothMeshTransform"
        CLOTH_MESH_SHAPE = "clothMeshShape"
        BLENDER_MESH_TFRM = "blenderMeshTransform"
        BLENDSHAPE_ORIG_NODE = "blendshapeOrigNode"
        BLENDSHAPE_CLOTH_NODE = "blendshapeClothNode"
        NCLOTH_NODE = "nClothNode"
        NCLOTH_TRANSFORM = "nClothTransform"
        NUCLEUS_NODE = "nucleusNode"
        CLOTH_NODES_GRP = "clothNodesGrp"

    :param networkNode: The network node name that connects to all ncloth objects
    :type networkNode: str
    :param nodeKey: The dictionary key representing an attribute of the network node that links to the objects
    :type nodeKey: dict
    :param selectNetworkNode: If True will ignore all other kwargs and select the netowrk node only
    :type selectNetworkNode: bool
    """
    if selectNetworkNode:
        cmds.select(networkNode, replace=True)
        return
    skinnedNClothNodes = getSkinnedNClothDictNetwork(networkNode)
    node = skinnedNClothNodes[nodeKey]
    cmds.select(node, replace=True)


# -----------------------------
# SELECT NODES
# -----------------------------


def showMesh(networkNode, nodeKey=ORIGINAL_MESH_TFRM):
    """Shows one of four meshes in the Skinned NCloth setup while hiding the others.

    Meshes are defined as constants see the nodeKeys at nclothconstants.py:

        ORIGINAL_MESH_TFRM = "originalMeshTransform"
        POLYSMOOTH_MESH_TFRM = "polySmoothMeshTransform"
        CLOTH_MESH_TFRM = "clothMeshTransform"
        BLENDER_MESH_TFRM = "blenderMeshTransform"

    :param networkNode: The network node name that connects to all ncloth objects
    :type networkNode: str
    :param nodeKey: The dictionary key representing an attribute of the network node that links to the objects
    :type nodeKey: dict
    """
    origVis = 0
    polySmoothVis = 0
    clothVis = 0
    blenderVis = 0
    skinnedNClothNodes = getSkinnedNClothDictNetwork(networkNode)
    if nodeKey == ORIGINAL_MESH_TFRM:
        origVis = 1
        mesh = skinnedNClothNodes[ORIGINAL_MESH_TFRM]
    elif nodeKey == POLYSMOOTH_MESH_TFRM:
        polySmoothVis = 1
        mesh = skinnedNClothNodes[POLYSMOOTH_MESH_TFRM]
    elif nodeKey == CLOTH_MESH_TFRM:
        clothVis = 1
        mesh = skinnedNClothNodes[CLOTH_MESH_TFRM]
    elif nodeKey == BLENDER_MESH_TFRM:
        blenderVis = 1
        mesh = skinnedNClothNodes[BLENDER_MESH_TFRM]
    else:
        return
    cmds.setAttr("{}.visibility".format(skinnedNClothNodes[ORIGINAL_MESH_TFRM]), origVis)
    cmds.setAttr("{}.visibility".format(skinnedNClothNodes[POLYSMOOTH_MESH_TFRM]), polySmoothVis)
    cmds.setAttr("{}.visibility".format(skinnedNClothNodes[CLOTH_MESH_TFRM]), clothVis)
    cmds.setAttr("{}.visibility".format(skinnedNClothNodes[BLENDER_MESH_TFRM]), blenderVis)
    om2.MGlobal.displayInfo("Success: Mesh display now showing `{}`".format(mesh))


# -----------------------------
# ENABLE DISABLE
# -----------------------------


def checkNetworkEnabled(networkNode):
    """Returns if the entire nCloth network enabled True or disabled False, is tricky to calculate.

    The returned enable state relates to the entire network, and not the nucleus state, so getting it's value can be \n
    tricky.

    The checkbox is set via checking the node network, depends on a few things as nucleus is disabled while \n
    caching even though the network state is still valid and on (enabled).
    If nucleus is disabled but the blender mesh is visible and there is a cache, then the network is considered \n
    enabled.  Otherwise it'll go with the nucleus state.

    :param networkNode: Name of a skinned NCloth network node
    :type networkNode: str
    :return networkEnabled: Is the entire network enabled True or disabled False, see doc description
    :rtype networkEnabled: bool
    """
    skinnedNClothNodes = getSkinnedNClothDictNetwork(networkNode)
    clothShape = skinnedNClothNodes[CLOTH_MESH_SHAPE]
    nucleusNode = skinnedNClothNodes[NUCLEUS_NODE]
    blenderTransform = skinnedNClothNodes[BLENDER_MESH_TFRM]
    if not clothShape or not nucleusNode or not blenderTransform:
        return False
    if not clothShape:  # not found so False
        return False
    cacheExists = checkConnectedCache(clothShape)
    if cacheExists:
        # Check the visibility of the blenderTransform
        return cmds.getAttr("{}.visibility".format(blenderTransform))  # probably the vis matches the enabled state
    # Otherwise no cache so check the state of the nucleus node
    return cmds.getAttr("{}.enable".format(nucleusNode))  # no cache so is this on?


def enableDisableNetwork(networkNode, enable=True, affectMeshVis=True):
    """This function will enable or disable the whole nCloth network.

    Enable:

        The nucleus will be enabled only if there is not a cache connected to the clothMeshShape node.
        The blender mesh (the fully enabled cloth mesh with a blendshape) will be shown if affectMeshVis=True

    Disable:

        The nucleus will be disabled, and the original mesh (the skinned mesh before the setup) will be shown if \n
        affectMeshVis=True

    :param networkNode: Name of a skinned NCloth network node
    :type networkNode: str
    :param enable: Should the network be enabled or disabled?
    :type enable: bool
    :param affectMeshVis: Also toggle the visibility of mesh objects?  Usually True
    :type affectMeshVis: bool
    :return isEnabled: The resulting state of the setup, usually the same as the enable incoming unless issues.
    :rtype isEnabled: bool
    :return success: Will report False if there were issues.
    :rtype success: bool
    """
    skinnedNClothNodes = getSkinnedNClothDictNetwork(networkNode)
    clothShape = skinnedNClothNodes[CLOTH_MESH_SHAPE]
    nucleusNode = skinnedNClothNodes[NUCLEUS_NODE]
    isEnabled = False
    if not clothShape:
        om2.MGlobal.displayWarning("Cloth mesh shape node not found for `{}`".format(networkNode))
        return isEnabled, False
    if not nucleusNode:
        om2.MGlobal.displayWarning("NCloth nucleus node not found for `{}`".format(networkNode))
        return isEnabled, False
    if enable:
        if affectMeshVis:
            showMesh(networkNode, nodeKey=BLENDER_MESH_TFRM)
        # Check if cache exists
        if not checkConnectedCache(clothShape):  # Cache does not exist change the state
            cmds.setAttr("{}.enable".format(nucleusNode), 1)
        isEnabled = True
    else:  # Disable
        if affectMeshVis:
            showMesh(networkNode, nodeKey=ORIGINAL_MESH_TFRM)
        cmds.setAttr("{}.enable".format(nucleusNode), 0)
    return isEnabled, True


def enableDisableNetworkAll(enable=True, affectMeshVis=True, message=True):
    """Enables or disables all network nodes in the scene

    :param enable: True enables, False disables
    :type enable: bool
    :param affectMeshVis: Also toggle the visibility of mesh objects?  Usually True
    :type affectMeshVis: bool
    :param message: Report the messages to the user?
    :type message: bool
    """
    networkNodeList = getNetworkNodesAll()
    if not networkNodeList:
        if message:
            om2.MGlobal.displayWarning("No displacement networks found in the scene.")
        return
    for network in networkNodeList:
        enableDisableNetwork(network, enable=enable, affectMeshVis=affectMeshVis)
    if message:
        if enable:
            om2.MGlobal.displayInfo("NCloth skinned networks enabled `{}`".format(networkNodeList))
        else:
            om2.MGlobal.displayInfo("NCloth skinned networks disabled `{}`".format(networkNodeList))


# -----------------------------
# MAKE HARDCODED PRESETS
# -----------------------------


def textCurrentPreset(nClothShape):
    """Builds a nicely formatted dictionary code for use as a python preset.  Used internally only. Don't remove.

    Code use:

        from zoo.libs.maya.cmds.ncloth import nclothskinned
        print nclothskinned.textCurrentPreset("nClothShape")

    Returns string used in nclothconstants.py, Eg:

        {NCA_INPUT_ATTRACT: 1.0,
        NCA_LIFT: 0.0001,
        NCA_STRETCH_RESISTANCE: 35.0,
        NCA_COMPRESSION_RESISTANCE: 10.0,
        NCA_BEND_RESISTANCE: 0.4,
        NCA_BEND_ANGLE_DROPOFF: 0.4,
        NCA_SHEAR_RESISTANCE: 0.0,
        NCA_POINT_MASS: 0.6,
        NCA_TANGENTIAL_DRAG: 0.1,
        NCA_DAMP: 0.8,
        NCA_SCALING_RELATION: 1.0,
        NCA_PUSH_OUT_RADIUS: 10.0,
        NCA_THICKNESS: 0.005,
        NCA_LOCAL_SPACE_OUTPUT: 1.0,
        NCA_SELF_COLLIDE_WIDTH_SCALE: 1
        }

    :param nClothShape: nCloth shape node name
    :type nClothShape: str
    :return text: text formatted for manually creating a python preset
    :rtype text: str
    """

    def textAttr(text, nClothShape, attr, comma=True):
        value = cmds.getAttr(".".join([nClothShape, attr]))
        text = "{}: {}".format(text, round(value, 3))
        if comma:
            text = "{},\n".format(text)
        else:
            text = "{}\n".format(text)
        return text

    text = "{"
    text += textAttr("NCA_INPUT_ATTRACT", nClothShape, nclothconstants.NCA_INPUT_ATTRACT)
    text += textAttr("NCA_LIFT", nClothShape, nclothconstants.NCA_LIFT)
    text += textAttr("NCA_STRETCH_RESISTANCE", nClothShape, nclothconstants.NCA_STRETCH_RESISTANCE)
    text += textAttr("NCA_COMPRESSION_RESISTANCE", nClothShape, nclothconstants.NCA_COMPRESSION_RESISTANCE)
    text += textAttr("NCA_BEND_RESISTANCE", nClothShape, nclothconstants.NCA_BEND_RESISTANCE)
    text += textAttr("NCA_BEND_ANGLE_DROPOFF", nClothShape, nclothconstants.NCA_BEND_ANGLE_DROPOFF)
    text += textAttr("NCA_SHEAR_RESISTANCE", nClothShape, nclothconstants.NCA_SHEAR_RESISTANCE)
    text += textAttr("NCA_POINT_MASS", nClothShape, nclothconstants.NCA_POINT_MASS)
    text += textAttr("NCA_TANGENTIAL_DRAG", nClothShape, nclothconstants.NCA_TANGENTIAL_DRAG)
    text += textAttr("NCA_DAMP", nClothShape, nclothconstants.NCA_DAMP)
    text += textAttr("NCA_SCALING_RELATION", nClothShape, nclothconstants.NCA_SCALING_RELATION)
    text += textAttr("NCA_PUSH_OUT_RADIUS", nClothShape, nclothconstants.NCA_PUSH_OUT_RADIUS)
    text += textAttr("NCA_THICKNESS", nClothShape, nclothconstants.NCA_THICKNESS)
    text += textAttr("NCA_LOCAL_SPACE_OUTPUT", nClothShape, nclothconstants.NCA_LOCAL_SPACE_OUTPUT)
    text += textAttr("NCA_SELF_COLLIDE_WIDTH_SCALE", nClothShape, nclothconstants.NCA_SELF_COLLIDE_WIDTH_SCALE)
    text += "}"
    return text
