from maya import cmds
import maya.api.OpenMaya as om2
import maya.mel as mel

from zoo.libs.maya.cmds.rig import nodes
from zoo.libs.maya.cmds.objutils import namehandling, objhandling

ZOO_INST_MIRROR_NETWORK = "zooInstMirNetwork"
KEY_MIRROR_GRP = "mirrorGrp"
KEY_MIRROR_OBJS = "mirrorObjs"
KEY_ORIG_GRP = "origGrp"
KEY_ORIG_OBJS = "origObjs"
KEY_PARENT_ROOT = "parentRoot"
MIRROR_INST_SUFFIX_ATTR_1 = "suffix01"
MIRROR_INST_SUFFIX_ATTR_2 = "suffix02"
MIRROR_INSTANCE_NAME = "mirrorName"
INST_MIR_KEY_LIST = [KEY_MIRROR_GRP, KEY_MIRROR_OBJS, KEY_ORIG_GRP, KEY_ORIG_OBJS]

MIR_INST_L = "L"
MIR_INST_R = "R"
MIR_INST_TOP = "Top"
MIR_INST_BOT = "Bottom"
MIR_INST_FRONT = "Front"
MIR_INST_BACK = "Back"

MIR_INST_SFX_LIST = [MIR_INST_L, MIR_INST_R, MIR_INST_TOP, MIR_INST_BOT, MIR_INST_FRONT, MIR_INST_BACK]


def flip():
    """Maya's Mesh > Flip
    """
    mel.eval('FlipMesh')


def symmetrize():
    """Maya's Mesh > Symmetrize
    """
    mel.eval('Symmetrize;')


def symmetryToggle(message=True):
    """Toggles symmetry modelling mode

    :param message: Report a message to the user?
    :type message: bool
    """
    objSel = cmds.ls(selection=True)
    symState = cmds.symmetricModelling(query=True, symmetry=True)
    cmds.symmetricModelling(symmetry=not symState)
    if message:
        if symState:
            om2.MGlobal.displayInfo("Symmetry is On.")
        else:
            om2.MGlobal.displayInfo("Symmetry is Off.")
    cmds.select(objSel, replace=True, symmetry=not symState)
    return not symState


def changeSymmetryMode(symmetryMode="World X", message=False):
    """Changes the Symmetry modeling mode.

    Options (case not important):

        "World X"
        "World Y"
        "World Z"
        "Object X"
        "Object Y"
        "Object Z"

    :param symmetryMode: "World X" or "Object Y" etc.  Can also be an empty string to not affect ""
    :type symmetryMode: str
    """
    about = str.lower(symmetryMode.split(" ")[0])
    axis = str.lower(symmetryMode.split(" ")[-1])
    cmds.symmetricModelling(about=about, axis=axis)
    if message:
        om2.MGlobal.displayInfo("Symmetry plane set to {}".format(symmetryMode))


def mirrorPolyEdgeToZero(smoothEdges=True, deleteHistory=True, smoothAngle=180, mergeThreshold=0.001,
                         disableSoftSelect=True, mirrorAxis="x", direction=1, space="world", message=True):
    """Mirrors poly objects with maya's polyMirrorFace with additional options.

    Can select center verts or edges and will center those while remembering symmetry mode:

        1) Moves selected vertices or edges  to the given mirrorAxis center eg X zero
        2) Mirrors object on the mirrorAxis the given axis ie +X to the opposite -X

    Can also use in object mode.  Supports multiple object selection. Will smooth edges and delete history.
    Also will switch off softSelect by default

    To use: Select the vertices or edges you want on the X axis and run the function
    credit to Ric Williams (co-author with Andrew Silke)

    TODO: add preferences

    :param smoothEdges: Smooth the edges with cmds.polySoftEdge?
    :type smoothEdges: bool
    :param deleteHistory: Delete history after the tool completes?
    :type deleteHistory: bool
    :param smoothAngle: If smoothEdges then this is the angle that the polySoftEdge smooths
    :type smoothAngle: float
    :param mergeThreshold: The merge threshold for the polyMirrorFace tool
    :type mergeThreshold: float
    :param disableSoftSelect: If in soft select mode make sure it's turned off for the center line adjust
    :type disableSoftSelect: bool
    :param mirrorAxis: The axis for the mirror to affect will be this axis eg "x"
    :type mirrorAxis: str
    :param direction: Direction of the mirror "-" or "+" negative or positive
    :type mirrorAxis: str
    :param space: What space is the mirror in "world" or "local"
    :type space: str
    :param message: Report the messages to the user?
    :type message: bool
    """
    if str.lower(mirrorAxis[-1]) == "x":  # last letter
        axis = 0
    elif str.lower(mirrorAxis[-1]) == "y":  # last letter
        axis = 1
    else:  # Z
        axis = 2
    mirrorSpace = 2 if str.lower(space) == 'world' else 1  # 2 is world 1 is object
    moveWorld = True if str.lower(space) == 'world' else False  # 2 is world 1 is object
    # Do the function
    selectionMix = cmds.ls(selection=True)  # this can have verts edges in the selection list
    selectedObjects = cmds.ls(selection=True, objectsOnly=True)  # only the objects, no verts edges
    selVerts = cmds.filterExpand(selectionMask=31)  # the selected edges
    selEdges = cmds.filterExpand(selectionMask=32)  # the selected verts
    symModeRecord = cmds.symmetricModelling(symmetry=True, query=True)  # record the symmetry mode
    softSelectModeRecord = cmds.softSelect(softSelectEnabled=True, query=True)  # record Soft Select mode
    if not selectionMix:  # if nothing selected
        if message:
            om2.MGlobal.displayWarning("Please select an object, or center vertices or center edges")
        return  # bail, since nothing selected
    if selVerts or selEdges:  # Yes vertices or edges are selected
        if symModeRecord:  # symmetry is on so switch it off
            cmds.symmetricModelling(symmetry=False)
        if disableSoftSelect:
            if softSelectModeRecord:  # softSelect is on so switch it off
                cmds.softSelect(softSelectEnabled=False)
        # Do the move on the correct axis
        if axis == 0:  # X
            cmds.move(0, absolute=True, worldSpace=moveWorld, objectSpace=not moveWorld, x=1)
        elif axis == 1:  # Y
            cmds.move(0, absolute=True, worldSpace=moveWorld, objectSpace=not moveWorld, y=1)
        else:  # Z
            cmds.move(0, absolute=True, worldSpace=moveWorld, objectSpace=not moveWorld, z=1)
        cmds.select(selectedObjects, replace=True)  # selects the original objects, not in component mode
    # Now do the mirror
    for obj in selectedObjects:  # Loop over potential multiple objects
        mirrorNode = cmds.polyMirrorFace(obj,
                                         mergeThreshold=mergeThreshold,
                                         cutMesh=True,
                                         mergeMode=True,
                                         mergeThresholdType=1,
                                         smoothingAngle=smoothAngle,
                                         mirrorAxis=mirrorSpace,
                                         axisDirection=direction,
                                         axis=axis)
        if smoothEdges:  # Force whole object to be the smooth value
            cmds.polySoftEdge(obj, angle=smoothAngle)  # can specify the object since with have it as a list
    cmds.select(selectedObjects, replace=True)  # selects the original objects just in case they were dropped
    if deleteHistory:
        cmds.DeleteHistory()  # delete history on selected
    cmds.symmetricModelling(symmetry=symModeRecord)  # return to previous sym mode
    cmds.softSelect(softSelectEnabled=softSelectModeRecord)  # return to previous softSelect mode
    if not deleteHistory:  # show manipulator
        mel.eval('setToolTo ShowManips')
        cmds.select(mirrorNode, deselect=True)
        cmds.select(mirrorNode, addFirst=True)
    if message:
        om2.MGlobal.displayInfo("Success: Object/s mirrored: {}".format(selectedObjects))  # success message


# -----------------------------
# INSTANCE MIRROR NETWORK SETUP AND RETRIEVAL
# -----------------------------


def createMirrorInstanceNetwork(groupMirror, origGroup, mirrorSetupObjName, suffixSide01, suffixSide02):
    """Creates the network node steup for the mirror instance setup.  Connections are made via message connections.

    Used while tracking and removing instances.

    :param groupMirror: The group name of the mirror side
    :type groupMirror: str
    :param origGroup: The group name of the non mirror side
    :type origGroup: str
    :param mirrorSetupObjName: The first object in the origObjs, a short name (is instanced so will be doubled)
    :type mirrorSetupObjName: str
    :param suffixSide01: The first suffix of the setup "L" or "R" or "top" or "bottom" etc
    :type suffixSide01: str
    :param suffixSide02: The second suffix of the setup "L" or "R" or "top" or "bottom" etc
    :type suffixSide02: str
    :return networkNodeName: The name of the network node created
    :rtype networkNodeName: str
    :return mirrorInstanceDict: dictionary of all object in the setup
    :rtype mirrorInstanceDict: str
    """
    mirrorObjs = cmds.listRelatives(groupMirror, children=True, type="transform", fullPath=True)  # Get all children
    origObjs = cmds.listRelatives(origGroup, children=True, type="transform", fullPath=True)  # Get all children
    # Create Network node and connect to attrs ----------------------------
    networkNodeName = "{}_{}".format(ZOO_INST_MIRROR_NETWORK, mirrorSetupObjName)
    networkNodeName = cmds.createNode('network', name=networkNodeName)
    nodes.messageNodeObjs(networkNodeName, [groupMirror], KEY_MIRROR_GRP, createNetworkNode=False)
    nodes.messageNodeObjs(networkNodeName, mirrorObjs, KEY_MIRROR_OBJS, createNetworkNode=False)
    nodes.messageNodeObjs(networkNodeName, [origGroup], KEY_ORIG_GRP, createNetworkNode=False)
    cmds.addAttr(networkNodeName, longName=MIRROR_INST_SUFFIX_ATTR_1, dataType="string")
    cmds.addAttr(networkNodeName, longName=MIRROR_INST_SUFFIX_ATTR_2, dataType="string")
    cmds.setAttr(".".join([networkNodeName, MIRROR_INST_SUFFIX_ATTR_1]), suffixSide01, type="string")
    cmds.setAttr(".".join([networkNodeName, MIRROR_INST_SUFFIX_ATTR_2]), suffixSide02, type="string")
    # Return dict
    mirrorInstanceDict = dict()
    mirrorInstanceDict[KEY_MIRROR_GRP] = groupMirror
    mirrorInstanceDict[KEY_MIRROR_OBJS] = mirrorObjs
    mirrorInstanceDict[KEY_ORIG_GRP] = origGroup
    mirrorInstanceDict[KEY_ORIG_OBJS] = origObjs
    return networkNodeName, mirrorInstanceDict


def retrieveMirrorInstanceList(networkNode):
    """Given a Mirror Instance network node name return the dictionary with all data.

    Note that the mirror objcs are instances so it's impossible to tell if they are mirrored or originals:

        {KEY_MIRROR_GRP: "mirrorGroupName_grp",
        KEY_MIRROR_OBJS: ["obj1", "obj2"],
        KEY_ORIG_GRP: "groupName_grp",
        KEY_PARENT_ROOT: None}

    The network node may return None if objects have already been deleted.  KEY_PARENT_ROOT of None may be world.

    :param networkNode: The name of the Mirror Instance Network node.
    :type networkNode: str
    :return mirrorInstanceDict: The returned data containing the applicable transform/object node.
    :rtype mirrorInstanceDict: dict
    """
    mirrorInstanceDict = dict()
    mirrorInstanceDict[KEY_MIRROR_GRP] = nodes.getNodeAttrConnections([networkNode], KEY_MIRROR_GRP)
    if mirrorInstanceDict[KEY_MIRROR_GRP]:
        mirrorInstanceDict[KEY_MIRROR_GRP] = mirrorInstanceDict[KEY_MIRROR_GRP][0]
    mirrorInstanceDict[KEY_MIRROR_OBJS] = nodes.getNodeAttrConnections([networkNode], KEY_MIRROR_OBJS)
    mirrorInstanceDict[KEY_ORIG_GRP] = nodes.getNodeAttrConnections([networkNode], KEY_ORIG_GRP)
    if mirrorInstanceDict[KEY_ORIG_GRP]:
        mirrorInstanceDict[KEY_ORIG_GRP] = mirrorInstanceDict[KEY_ORIG_GRP][0]
    if mirrorInstanceDict[KEY_MIRROR_GRP]:
        if cmds.objExists(mirrorInstanceDict[KEY_MIRROR_GRP]):
            mirrorInstanceDict[KEY_PARENT_ROOT] = cmds.listRelatives(mirrorInstanceDict[KEY_MIRROR_GRP], parent=True)
    else:
        if cmds.objExists(mirrorInstanceDict[KEY_ORIG_GRP]):
            mirrorInstanceDict[KEY_PARENT_ROOT] = cmds.listRelatives(mirrorInstanceDict[KEY_ORIG_GRP], parent=True)
        else:
            mirrorInstanceDict[KEY_PARENT_ROOT] = None
    return mirrorInstanceDict


def getInstNetworkNodeFromObj(obj):
    """From an object check if it is connected the a Mirror Instance network node.

    :param obj: A Maya object name
    :type obj: str
    :return networkNode: Name of a Maya network node, "" empty string if it None found.
    :rtype networkNode: str
    """
    for key in INST_MIR_KEY_LIST:
        networkNode = nodes.getNodeAttrConnections([obj], key)
        if networkNode:
            return networkNode[0]
    return ""


def retrieveMirrorInstanceNetworkSel():
    """From the current selection retrieve all network nodes and their data as dictionaries.

    :return networkNodeList: A list of network node names connected to the current selection
    :rtype networkNodeList: list(str)
    :return mirrorSetupDictList: a list of dictionaries with contents matching the network node names.
    :rtype mirrorSetupDictList: list(dict(str))
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        return list(), list()
    mirrorSetupDictList = list()
    networkNodeList = list()
    for obj in selObjs:
        networkNode = getInstNetworkNodeFromObj(obj)
        if networkNode:
            networkNodeList.append(networkNode)
    if not networkNodeList:
        return networkNodeList, list()
    networkNodeList = list(set(networkNodeList))  # remove duplicates
    for networkNode in networkNodeList:
        mirrorInstanceDict = retrieveMirrorInstanceList(networkNode)
        mirrorSetupDictList.append(mirrorInstanceDict)
    return networkNodeList, mirrorSetupDictList


def cleanupMirrorInstanceNetwork(networkNodeList):
    """From a network node list remove the setups that are broken.

    :param networkNodeList: A list of mirror instance network node names
    :type networkNodeList: list(str)
    :return validNetworkNodes: A list of netowrk nodes that are not broken.
    :rtype validNetworkNodes: list(str)
    :return objs: Any objects that have been removed from the setup, long names will change as hierarchy change
    :rtype objs: list(str)
    """
    objs = list()
    validNetworkNodes = list()
    for networkNode in networkNodeList:
        mirrorInstanceDict = retrieveMirrorInstanceList(networkNode)
        # check both groups still exist
        mirrorGrp = mirrorInstanceDict[KEY_MIRROR_GRP]
        origGrp = mirrorInstanceDict[KEY_ORIG_GRP]
        mirrorObjs = mirrorInstanceDict[KEY_MIRROR_OBJS]
        if not mirrorObjs:
            continue
        if mirrorGrp and origGrp:
            if objhandling.isInstanced(mirrorObjs[0]):
                validNetworkNodes.append(networkNode)
                continue
        # If not then delete the setup
        mirrorSetupDict = retrieveMirrorInstanceList(networkNode)
        objs += uninstanceMirrorInstance(networkNode, mirrorSetupDict)
    return validNetworkNodes, objs


# -----------------------------
# INSTANCE MIRROR CREATE
# -----------------------------


def instanceMirror(groupName="instance_grp", mirrorAxis="x", space="world", direction="+", message=True):
    """Instance mirrors selected objects by instance group and duplicate, then invert scale.

    Handles naming and network node setup so that the setup can be uninstanced cleanly later.

    Also checks for broken networks and if an instanced network already exists.

    :param groupName: The non instanced new suffix, by default is "instance_grp", prefix is first selected object
    :rtype groupName:
    :param mirrorAxis: The axis for the mirror to affect will be this axis eg "x"
    :type mirrorAxis: str
    :param space: What space is the mirror in "world" or "local"
    :type space: str
    :param direction: Which direction is the mirror "+" or "-", only affects names
    :type direction: str
    :param message: Report the message to the user
    :type message: bool
    :return group: Name of the first mirror group
    :rtype group: str
    :return groupMirror: The instanced group mirror name
    :rtype groupMirror: str
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        om2.MGlobal.displayWarning('No Objects Selected, please select')
        return None, None
    # Check that selection isn't already in a setup
    networkNodeList, mirrorSetupDictList = retrieveMirrorInstanceNetworkSel()
    if networkNodeList:
        networkNodeList, objs = cleanupMirrorInstanceNetwork(networkNodeList)
        if networkNodeList:
            om2.MGlobal.displayWarning("Some objects in the selection are already connected to a "
                                       "mirror instance setup {}".format(networkNodeList))
            return "", dict()
        else:
            if objs:  # the network was deleted so mirror these objects
                selObjs = objs
    # Get the suffix names dependant on direction --------------------------------------
    if mirrorAxis == str.lower("x"):
        suffixSide01 = MIR_INST_L if direction == "-" else MIR_INST_R
        suffixSide02 = MIR_INST_L if direction == "+" else MIR_INST_R
    elif mirrorAxis == str.lower("y"):
        suffixSide01 = MIR_INST_TOP if direction == "-" else MIR_INST_BOT
        suffixSide02 = MIR_INST_TOP if direction == "+" else MIR_INST_BOT
    else:  # Z
        suffixSide01 = MIR_INST_FRONT if direction == "-" else MIR_INST_BACK
        suffixSide02 = MIR_INST_FRONT if direction == "+" else MIR_INST_BACK
    # Get network name --------------------------------------
    mirrorSetupObjName = namehandling.stripSuffixExact(namehandling.getShortName(selObjs[0]), suffixSide01)
    mirrorSetupObjName = namehandling.stripSuffixExact(mirrorSetupObjName, suffixSide02)
    mirrorSetupObjName = namehandling.mayaNamePartTypes(mirrorSetupObjName)[2]  # remove namespaces and longnames
    # Strip suffix names if a match and rename actual objects --------------------------------------
    for i, obj in enumerate(selObjs):
        newName = namehandling.stripSuffixExact(obj, suffixSide01)
        newName = namehandling.stripSuffixExact(newName, suffixSide02)
        if newName != obj:  # then will need to rename
            selObjs[i] = namehandling.safeRename(obj, newName)
    # Group first object and name groups --------------------------------------
    group = cmds.group(em=True, n="{}_{}".format(mirrorSetupObjName, groupName))  # Create a group
    if str.lower(space) == "object" or str.lower(
            space) == "local":  # Technically can only instance mirror on local axis
        # Get the parent of object01 and match the group
        parent = cmds.listRelatives(selObjs[0], parent=True)
        if parent:
            parent = parent[0]
            group = cmds.parent(group, parent, relative=True, absolute=False)[0]
    cmds.parent(selObjs, group)  # Parent selected objects
    # Create opposite group --------------------------------------
    groupMirror = (cmds.instance(group, name="_".join([group, suffixSide01])))[0]  # Instance group
    cmds.setAttr(('{}.scale{}'.format(groupMirror, mirrorAxis.upper())), -1)  # Scale -1
    group = cmds.rename(group, "_".join([group, suffixSide02]))
    # Create network message nodes --------------------------------------
    networkNodeName, mirrorInstanceDict = createMirrorInstanceNetwork(groupMirror, group, mirrorSetupObjName,
                                                                      suffixSide01, suffixSide02)
    # Finish --------------------------------------
    if message:
        om2.MGlobal.displayInfo('Success: Objects grouped in `{}` and instance created `{}`'.format(group, groupMirror))
    return networkNodeName, mirrorInstanceDict


# -----------------------------
# UNINSTANCE MIRROR INSTANCE
# -----------------------------


def uninstanceMirrorInstance(networkNode, mirrorSetupDict):
    """Uninstance a Mirror Instance setup while unparenting and renaming objects cleanly.  Checks for broken setups.

    :param networkNode: The name of a Mirror Instance network node
    :type networkNode: str
    :param mirrorSetupDict: The dictionary information of the network node
    :type mirrorSetupDict: dict
    :return objs: The remaining object list if successful otherwise will be an empty list
    :rtype objs: list(str)
    """
    #  Uninstance objects -------------------------
    origGrp = mirrorSetupDict[KEY_ORIG_GRP]
    mirrorGrp = mirrorSetupDict[KEY_MIRROR_GRP]
    origObjs = list()
    mirrorObjs = list()
    namespace = ""
    # Rename geo objects and remove instancing -------------------------
    obj1_suffix = cmds.getAttr(".".join([networkNode, MIRROR_INST_SUFFIX_ATTR_1]), type=False)
    obj2_suffix = cmds.getAttr(".".join([networkNode, MIRROR_INST_SUFFIX_ATTR_2]), type=False)
    if origGrp:
        cmds.select(origGrp, replace=True)
        objhandling.uninstanceSelected()
        origObjs = cmds.listRelatives(origGrp, children=True, type="transform", fullPath=True)
        origObjs = namehandling.addPrefixSuffixList(origObjs, obj2_suffix, addUnderscore=True)
    if mirrorGrp:
        cmds.select(mirrorGrp, replace=True)
        objhandling.uninstanceSelected()
        mirrorObjs = cmds.listRelatives(mirrorGrp, children=True, type="transform", fullPath=True)
        mirrorObjs = namehandling.addPrefixSuffixList(mirrorObjs, obj1_suffix, addUnderscore=True)
        namespace = namehandling.mayaNamePartTypes(mirrorObjs[0])[1]
        if namespace:  # rename all objects
            mirrorObjs = namehandling.removeNamespaceFromObjList(mirrorObjs)
    objs = origObjs + mirrorObjs
    if namespace:
        objs = namehandling.createAssignNamespaceList(objs, namespace)
    # Unparent -------------------------
    rootObj = mirrorSetupDict[KEY_PARENT_ROOT]
    if objs:
        if not rootObj:  # Then is root is world
            objs = cmds.parent(objs, world=True)
        else:
            objs = cmds.parent(objs, rootObj)
    # Delete groups and network node -------------------------
    deleteList = [networkNode]
    if origGrp:
        deleteList.append(origGrp)
    if mirrorGrp:
        deleteList.append(mirrorGrp)
    for obj in deleteList:
        if cmds.objExists(obj):
            cmds.delete(obj)
    if not objs:
        return
    # Delete network attributes on remaining objects -------------------------
    for obj in objs:
        cmds.deleteAttr(".".join([obj, KEY_MIRROR_OBJS]))
    return objs


def uninstanceMirrorInstanceSel():
    """From the selection uninstance a Mirror Instance netowrk selection, if it exists.

    Uninstance a Mirror Instance setup while unparenting and renaming objects cleanly.  Checks for broken setups.

    :return networkNodeList: A list of Mirror Instance network nodes that have been removed from the scene.
    :rtype networkNodeList: list(str)
    """
    networkNodeList, mirrorSetupDictList = retrieveMirrorInstanceNetworkSel()
    if not networkNodeList:
        om2.MGlobal.displayWarning("No mirror instance setups found. "
                                   "Please select an object from a mirror instance setup.")
        return
    for i, networkNode in enumerate(networkNodeList):
        uninstanceMirrorInstance(networkNode, mirrorSetupDictList[i])
    om2.MGlobal.displayInfo("Success: Mirror Instance setups uninstanced {}".format(networkNodeList))
    return networkNodeList


def uninstanceMirrorInstacesAll():
    """Uninstance all Mirror Instance networks if they exist.

    Uninstances while unparenting and renaming objects cleanly.  Checks for broken setups and will remove broken setups.

    :return networkNodeList: A list of Mirror Instance network nodes that have been removed from the scene.
    :rtype networkNodeList: list(str)
    """
    networkNodeList = cmds.ls("*{}*".format(ZOO_INST_MIRROR_NETWORK))
    if not networkNodeList:
        om2.MGlobal.displayWarning("No mirror instance setups found in scene.")
        return list()
    for i, networkNode in enumerate(networkNodeList):
        mirrorInstanceDict = retrieveMirrorInstanceList(networkNode)
        if mirrorInstanceDict:
            uninstanceMirrorInstance(networkNode, mirrorInstanceDict)
    om2.MGlobal.displayInfo("Success: Mirror Instance setups uninstanced {}".format(networkNodeList))
    return networkNodeList


