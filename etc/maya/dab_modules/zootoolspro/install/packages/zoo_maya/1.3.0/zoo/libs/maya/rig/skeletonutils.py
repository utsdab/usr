from maya.api import OpenMaya as om2

from zoo.libs.utils import zlogging
from zoo.libs.maya.api import nodes
from zoo.libs.maya.api import plugs

logger = zlogging.getLogger(__name__)


def poleVectorPosition(start, mid, end, multiplier=1.0):
    """This function gets the position of the polevector from 3 MVectors

    :param start: the start vector
    :type start: MVector
    :param mid: the mid vector
    :type mid: MVector
    :param end: the end vector
    :type end: MVector
    :return: the vector position of the pole vector
    :rtype: MVector
    """
    # calculate distance between
    startEnd = end - start
    startMid = mid - start
    dotP = startMid * startEnd

    try:
        proj = float(dotP) / float(startEnd.length())
    except ZeroDivisionError:
        logger.error("trying to divide by zero is unpredictable returning")
        raise ZeroDivisionError

    startEndN = startEnd.normal()
    projV = startEndN * proj
    arrowV = (startMid - projV) * multiplier
    finalV = arrowV + mid

    return finalV


def convertToNode(node, parent, prefix, nodeType="joint"):
    """Converts a node into a joint but does not delete the node ,
    transfers matrix over as well

    :param node: mobject, the node that will be converted
    :param parent: mobject to the transform to parent to
    :param prefix: str, the str value to give to the start of the node name
    :param nodeType: str, the node type to convert to. must be a dag type node
    :return: mObject, the mobject of the joint
    """
    jnt = nodes.createDagNode(nodeType, prefix + nodes.nameFromMObject(node, partialName=True), parent=parent)
    plugs.setPlugValue(om2.MFnDagNode(jnt).findPlug("worldMatrix", False), nodes.getWorldMatrix(node))

    return jnt


def convertToSkeleton(rootNode, prefix="skel_", parentObj=None):
    """Converts a hierarchy of nodes into joints that have the same transform,
    with their name prefixed with the "prefix" arg.

    :param rootNode: anything under this node gets converted.
    :type rootNode: :class:`om2.MObject`
    :param prefix: The name to add to the node name .
    :type prefix: str
    :param parentObj: The node to parent to skeleton to.
    :type parentObj: :class:`om2.MObject`
    :return: MObject
    """
    if parentObj is None:
        parentObj = nodes.getParent(rootNode)
    j = convertToNode(rootNode, parentObj, prefix)
    for c in nodes.getChildren(rootNode):
        convertToSkeleton(c, prefix, j)
    return j


def jointLength(joint):
    jointFn = om2.MFnDagNode(joint)
    parent = jointFn.parent()
    if nodes.isSceneRoot(parent):
        return 0.0
    parentPos = nodes.getTranslation(parent, space=om2.MSpace.kWorld)
    jointPos = nodes.getTranslation(joint, space=om2.MSpace.kWorld)
    return (jointPos - parentPos).length()


def chainLength(start, end):
    joints = [end]
    for i in nodes.iterParents(end):
        if i.apiType() == om2.MFn.kJoint:
            joints.append(i)
            if i == start:
                break
    joints.reverse()
    total = 0
    for j in iter(joints):
        total += jointLength(j)

    return total


def jointRoot(node, depthLimit=256):
    parent = node
    while parent is not None or parent.apiType() == om2.MFn.kJoint or depthLimit > 1:
        parent = nodes.getParent(parent)
        depthLimit -= 1
    return parent
