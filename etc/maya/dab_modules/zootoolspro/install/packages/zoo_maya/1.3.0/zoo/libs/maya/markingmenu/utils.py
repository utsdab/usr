from zoo.libs.maya.api import nodes
from zoo.libs.maya.api import attrtypes
from zoo.libs.maya.api import plugs
from zoo.libs.maya.meta import base
from zoo.libs.maya import zapi
from maya.api import OpenMaya as om2

TRIGGER_ATTR_NAME = "zooTrigger"
LAYOUTID_ATTR_NAME = "zooTriggerLayoutId"
COMMANDTYPE_ATTR_NAME = "zooTriggerCommandType"
COMMAND_ATTR_NAME = "zooTriggerString"

# command Types
LAYOUT_TYPE = 0
DYNAMIC_TYPE = 1


def updateCommandString(node, value, commandType=None):
    """Function to update the node attributes related to the trigger data

    :param node: The node with the trigger attributes to update
    :type node: om2.MObject
    :param value:
    :type value:
    :param commandType: the command type, see :func:`createTriggerAttributes` for more information
    :type commandType: int
    :return: True if successful
    :rtype: bool
    """
    fn = om2.MFnDependencyNode(node)
    if not fn.hasAttribute(TRIGGER_ATTR_NAME):
        return False
    comp = fn.findPlug(TRIGGER_ATTR_NAME, False)
    commandStr = comp.child(1)
    with plugs.setLockedContext(commandStr):
        commandStr.setString(value)
    if commandType is not None:
        commandTypeP = comp.child(0)
        with plugs.setLockedContext(commandTypeP):
            commandTypeP.setString(commandType)
    return True


def createTriggerAttributes(node, commandType, command):
    """ Create's the standard zootrigger compound attribute including children.


    :param node: the node to add the command to,
    :type node: om2.MObject
    :param commandType: PYTHON_TYPE ,COMMAND_TYPE, LAYOUT_TYPE
    :type commandType: int
    :param command: if COMMAND_TYPE then the command arg value should be a zoocommand id , if PYTHONTYPE then it \
    should be an executable str, if LAYOUT_TYPE then the layoutId.
    :type command: str
    :return: The compound MPlug
    :rtype: om2.MPlug
    """
    children = [
        {"name": COMMANDTYPE_ATTR_NAME, "Type": attrtypes.kMFnNumericInt, "isArray": False, "value": commandType,
         "locked": True},
        {"name": COMMAND_ATTR_NAME, "Type": attrtypes.kMFnDataString, "isArray": False, "value": command,
         "locked": True}]
    fn = om2.MFnDependencyNode(node)
    # todo: should check each attr and add the missing?
    if fn.hasAttribute(TRIGGER_ATTR_NAME):
        return fn.findPlug(TRIGGER_ATTR_NAME, False).attribute()
    return nodes.addCompoundAttribute(node, TRIGGER_ATTR_NAME, TRIGGER_ATTR_NAME, children, False)


def hasTrigger(node):
    """Determines if the current node is attached to a trigger.
    There's two ways a trigger can be determined, the first is the zooTrigger compound attr exist's directly on the node.
    The second is the node is attached to a meta node which has the zooTrigger attr.

    :param node: The node to search
    :type node: om2.MObject
    :return: True if valid Trigger
    :rtype: bool
    """
    fn = zapi.nodeByObject(node)
    # first check on the current node

    if fn.hasAttribute(TRIGGER_ATTR_NAME):
        return True
    # ok so its not on the node, check for a meta node node
    attachedmeta = base.getConnectedMetaNodes(fn)
    for i in attachedmeta:
        if i.hasAttribute(TRIGGER_ATTR_NAME):
            return True
    return False


def layoutIdsFromNode(node):
    """
    :param node:
    :type node:
    :return:
    :rtype: iterable(str)
    """
    fn = zapi.nodeByObject(node)
    layouts = []
    triggerComp = fn.attribute(LAYOUTID_ATTR_NAME)
    if triggerComp is not None:
        layoutId = triggerComp.asString()
        if layoutId:
            layouts.append(layoutId)
        # ok so its not on the node, check for a meta node node
    attachedmeta = base.getConnectedMetaNodes(fn)
    for i in attachedmeta:
        if i.hasAttribute(LAYOUTID_ATTR_NAME):
            triggerComp = i.attribute(LAYOUTID_ATTR_NAME)
            layoutId = triggerComp.asString()
            if layoutId:
                layouts.append(layoutId)
    return layouts


def triggerPlugsFromNode(node):
    fn = zapi.nodeByObject(node)
    triggerPlugs = []
    triggerPlug = fn.attribute(TRIGGER_ATTR_NAME)
    if triggerPlug is not None:
        triggerPlugs.append(triggerPlug)

    attachedmeta = base.getConnectedMetaNodes(fn)
    for i in attachedmeta:
        triggerPlug = i.attribute(TRIGGER_ATTR_NAME)
        if triggerPlug is not None:
            triggerPlugs.append(triggerPlug)
    return triggerPlugs
