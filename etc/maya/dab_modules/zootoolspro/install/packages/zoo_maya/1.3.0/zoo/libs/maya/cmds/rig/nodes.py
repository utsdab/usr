import maya.cmds as cmds
from zoo.libs.maya.cmds.rig import connections  # todo move
from zoo.libs.maya.cmds.objutils import connections as connect

def conditionMulti(driverAttr, drivenAttrList, value, suffix=""):
    """Creates a condition node, on/off values to multiple nodes
    useful for visibility and constraint switching
    Common to use this multiple times on the same driverAttr

    :param driverAttr: Name of driver attr 'object.attribute'
    :type driverAttr: str
    :param drivenAttrList: List of attributes [object.attr, object2.attr]
    :type drivenAttrList: list
    :param value: The value of the on state
    :type value: float
    :param suffix: suffix for naming
    :type suffix: str
    :return conditionNode: Name of the condition node created
    :rtype conditionNode: str
    """
    # nice names
    driverAttrNiceName = driverAttr.replace(".", "_")
    drivenNiceName = (drivenAttrList[0]).replace(".", "_")
    # create condition node
    if suffix:
        conditionNode = cmds.createNode('condition', n='_'.join([suffix, driverAttrNiceName, drivenNiceName]))
    else:
        conditionNode = cmds.createNode('condition', n='_'.join([driverAttrNiceName, drivenNiceName]))
    # Set Node Attributes
    cmds.setAttr('{}.secondTerm'.format(conditionNode), value)
    cmds.setAttr('{}.colorIfTrueR'.format(conditionNode), 1)
    cmds.setAttr('{}.colorIfFalseR'.format(conditionNode), 0)
    # connect node first item
    cmds.connectAttr(driverAttr, '{}.firstTerm'.format(conditionNode))
    for i, obAttr in enumerate(drivenAttrList):
        # connect outgoing to driven
        cmds.connectAttr('{}.outColor.outColorR'.format(conditionNode), obAttr)
    return conditionNode


# -------------------------------------------
# Network Nodes (Tracking objects meta data)
# -------------------------------------------


def createNetworkNodeWithConnections(nodeName, attributeName, connectionList, createNetworkNode=True):
    """Creates a new network node with connections to all nodes in the connection list via message connections
    Handy for rigging and keeping track of connected objects to delete or handle later, like metadata

    :param nodeName: the name of the network node
    :type nodeName: str
    :param attributeName: the attribute name to connect to the objects
    :type attributeName: str
    :param connectionList: the list of maya node names
    :type connectionList: list
    :param createNetworkNode: Option to create the network node, or if False, connect to an existing node
    :type createNetworkNode: bool
    """
    if createNetworkNode:  # create the node, otherwise just connect an existing node
        nodeName = cmds.createNode('network', name=nodeName)
    connections.createMessageConnectionList(nodeName, attributeName, connectionList)
    return nodeName


def messageNodeObjs(networkNodeName, nodeList, connectAttr, createNetworkNode=True):
    """Connects all nodes in the list to a network node

    The network node can be handy later, when we want to delete the cube array and all objects connected to it

    :param networkNodeName: the name of the network node, can exist or will be created, see kwarg `createNetworkNode`
    :type networkNodeName: str
    :param nodeList: list of Maya node names strings (nodes)
    :type nodeList: list
    :param connectAttr: the attribute on each node to connect to
    :type connectAttr: str
    :param createNetworkNode: Option to create the network node, or if False, connect to an existing node
    :type createNetworkNode: bool
    :return networkNodeName: The name of the network node created, Maya name string
    :rtype networkNodeName: str
    """
    for node in nodeList:
        if not cmds.attributeQuery(connectAttr, node=node, exists=True):
            cmds.addAttr(node, longName=connectAttr, attributeType='message')
    return createNetworkNodeWithConnections(networkNodeName, connectAttr, nodeList,
                                            createNetworkNode=createNetworkNode)


def getNodeAttrConnections(nodeList, attributeName, shapes=False):
    """Returns a list of network nodes connected to the given objects/nodes, searches nodes by their attribute name
    For each object find if it has an network node attached

    Note: Known issues regarding shapes not being returned in some tool code, should fix all references to shapes = True
    Shapes=True will return the shape node if that's the connected node, so should be always on. Need to check all tools

    :param nodeList: list of maya object names
    :type nodeList: list
    :param attributeName: the name of the attribute to find connections
    :type attributeName: str
    :param shapes: While listing connections return the shape nodes if a shape, should always be True, but issues
    :type shapes: bool

    :return connectedNodes: list of unique network nodes connected to the objects
    :rtype connectedNodes: list
    """
    connectedNodes = list()
    for node in nodeList:
        if cmds.attributeQuery(attributeName, node=node, exists=True):  # if attribute exists
            addNodes = cmds.listConnections('.'.join([node, attributeName]), shapes=shapes)
            if addNodes:  # may be empty
                connectedNodes += addNodes
    if not connectedNodes:
        return connectedNodes
    return list(set(connectedNodes))  # remove duplicates


def getNodesFromNetworkNodeAttr(networkNode, attribute):
    """From a network node return the nodes connected via the attribute name"""
    if cmds.attributeQuery(attribute, node=networkNode, exists=True):  # if attribute exists
        return cmds.listConnections('.'.join([networkNode, attribute]))
    return list()


