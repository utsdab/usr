"""Temporary module while doing the replacement on constraints.py.

.. todo::

    Function to return the constraint driving space attribute and node.
    Function to remove a space.


"""
from maya.api import OpenMaya as om2
from maya import cmds

from zoovendor.six.moves import range

from zoo.libs.maya.api import nodes, attrtypes, plugs
from zoo.libs.maya.utils import creation



# constant mapping between maya api constraint types and maya cmds string types
APITOCMDS_CONSTRAINT_MAP = {om2.MFn.kParentConstraint: {"type": 'parentConstraint', "targetPlugIndex": 1},
                            om2.MFn.kPointConstraint: {"type": 'pointConstraint', "targetPlugIndex": 4},
                            om2.MFn.kOrientConstraint: {"type": 'orientConstraint', "targetPlugIndex": 4},
                            om2.MFn.kScaleConstraint: {"type": "scaleConstraint", "targetPlugIndex": 2},
                            om2.MFn.kAimConstraint: {"type": "aimConstraint", "targetPlugIndex": 4}}


def findConstraint(node, kType, includeReferenced=True):
    """Searches the upstream graph one level  in search for the corresponding kConstraintType

    :param node: The node to search upstream from
    :type node: om2.MObject
    :param kType: The maya MFn.kConstraintType eg. om2.MFn.kParentConstraint
    :type kType: om2.MFn.kConstraintType
    :param includeReferenced: If True will return the constraint regardless of whether the node is referenced /
    If False then only non-referenced constraints would be returned
    :type includeReferenced: bool
    :return: The MObject representing the constraint
    :rtype: om2.MObject or None
    """
    for source, destination in nodes.iterConnections(node, source=False, destination=True):
        dest = destination.node()
        if dest.apiType() == kType and (includeReferenced or not om2.MFnDependencyNode(dest).isFromReferencedFile):
            return dest


def iterTargetsFromConstraint(constraint):
    """Generator function that search the upstream graph and returns the target nodes

    The target nodes are returned in order of creation i.e target[0] element index of the targetArray plug
    would be returned first.

    :param constraint: The Constraint MObject
    :type constraint: om2.MObject
    :return: The generator containing target node MObject.
    :rtype: generator(om2.MObject)
    """
    fn = om2.MFnDependencyNode(constraint)
    targetArray = fn.findPlug("target", False)
    visited = []
    # to safe guard the possible situation where the first child plug(parentInverseMatrix) isn't connected
    # we iterate through the child plugs to find the first connected plug.
    for tElementIndex in targetArray.getExistingArrayAttributeIndices():
        targetElement = targetArray.elementByLogicalIndex(tElementIndex)
        for i in range(targetElement.numChildren()):
            childPlug = targetElement.child(i)
            source = childPlug.source()
            # if the plug is not connected to a source skip!
            if not source:
                continue
            # strange scenario where the source plugs node isn't valid?
            sNode = source.node()
            # make sure we haven't seen this node before just in case
            # the user did random connections manually.
            if not sNode.isNull() and sNode not in visited:
                visited.append(sNode)
                yield sNode
                # we only want the first incoming connection so lets
                # go straight back up to the next target array element
                break


def buildConstraint(source, targets, maintainOffset=False,
                    constraintType=om2.MFn.kParentConstraint, **kwargs):
    """This Function build a space switching constraint.

    Currently Supporting types of
        kParentConstraint
        kPointConstraint
        kOrientConstraint

    :param source: The transform to drive
    :param source: om2.MObject
    :param targets: A dict containing the target information(see below example)
    :param targets: dict or None
    :param: maintainOffset: whether or not the constraint should maintain offset
    :type maintainOffset: bool
    :param constraintType: The maya api kType eg. om2.MFn.kParentConstraint, defaults to kParentConstraint
    :type constraintType: om2.MFn.kType
    :param kwargs: The cmds.kconstraintType extra arguments to use
    :type kwargs: dict

    .. code-block: python

        targets = []
        for n in ("locator1", "locator2", "locator3"):
            targets.append((n, nodes.createDagNode(n, "locator")))
        spaceNode =nodes.createDagNode("control", "locator")
        drivenNode = nodes.createDagNode("driven", "locator")
        spaces = {"spaceNode": spaceNode,
                    "attributeName": "parentSpace", "targets": targets}
        constraint, conditions = build(drivenNode, targets=spaces)

        # lets add to the existing system
        spaces = {"spaceNode": spaceNode, "attributeName": "parentSpace", "targets": (
                 ("locator8", nodes.createDagNode("locator8", "locator")),)}

        constraint, conditions = build(drivenNode, targets=spaces)

      )


    """
    # make sure we support the constrainttype the user wants
    assert constraintType in APITOCMDS_CONSTRAINT_MAP, "No Constraint of type: {}, supported".format(constraintType)

    spaceNode = targets.get("spaceNode")
    attrName = targets.get("attributeName", "parent")
    targetInfo = targets["targets"]
    targetLabels, targetNodes = zip(*targetInfo)

    # first try to find an existing constraint
    existingConstraint = findConstraint(source, constraintType, includeReferenced=False)
    # if we found existing constraint then check to see if the target is already
    # constraining, if so just excluded it.
    targetList = targetNodes
    if existingConstraint:
        existingTargets = list(iterTargetsFromConstraint(existingConstraint))
        targetList = [t for t in targetNodes if t not in existingTargets]
        # in the case that all target already exist just early out
        if not targetList:
            return None, []

    # create the constraint
    constraintMap = APITOCMDS_CONSTRAINT_MAP[constraintType]
    cmdsFunc = getattr(cmds, constraintMap["type"])
    arguments = {"maintainOffset": maintainOffset}
    arguments.update(kwargs)
    constraint = cmdsFunc(map(nodes.nameFromMObject, targetList), nodes.nameFromMObject(source),
                          **arguments)[0]
    # if we have been provided a spaceNode, which will contain our switch, otherwise ignore the setup of a switch
    # and just return the constraint
    constraintMObject = nodes.asMObject(constraint)
    if spaceNode is None:
        return constraintMObject, []

    spaceFn = om2.MFnDependencyNode(spaceNode)
    if spaceFn.hasAttribute(attrName):
        spacePlug = spaceFn.findPlug(attrName, False)
        existingFieldNames = plugs.enumNames(spacePlug)
        spaceAttr = om2.MFnEnumAttribute(spacePlug.attribute())
        # add any missing fields to enumAttribute
        for field in targetLabels:
            if field not in existingFieldNames:
                spaceAttr.addField(field, len(existingFieldNames))

    else:
        spaceAttr = nodes.addAttribute(spaceNode, attrName, attrName, attrType=attrtypes.kMFnkEnumAttribute,
                                       keyable=True,
                                       channelBox=True, locked=False,
                                       enums=targetLabels)
        spacePlug = om2.MPlug(spaceNode, spaceAttr.object())

    constraintFn = om2.MFnDependencyNode(constraintMObject)
    targetArray = constraintFn.findPlug("target", False)
    sourceShortName = nodes.nameFromMObject(source, partialName=True, includeNamespace=False)
    conditions = []
    constraintTargetWeightIndex = constraintMap["targetPlugIndex"]
    # first iterate over the target array on the constraint
    for index in targetArray.getExistingArrayAttributeIndices():
        targetElement = targetArray.elementByLogicalIndex(index)
        targetElementWeight = targetElement.child(constraintTargetWeightIndex)
        targetWeightSource = targetElementWeight.source()
        # just in case the target weight plug is disconnected
        if targetWeightSource is None:
            targetWeightSource = targetElementWeight
        else:
            # lets make sure that we're not already connected to a condition node
            # if so skip
            weightSourceNode = targetWeightSource.node()
            # if we connected to the constraint i.e spaceWO1
            if weightSourceNode == constraintMObject:
                upstreamWeight = targetWeightSource.source()
                if upstreamWeight and upstreamWeight.node().apiType() == om2.MFn.kCondition:
                    continue
            else:
                if weightSourceNode.apiType() == om2.MFn.kCondition:
                    continue
        targetNode = targetElement.child(0).source().node()
        targetShortName = nodes.nameFromMObject(targetNode, partialName=True, includeNamespace=False)
        # create the condition node and do the connections
        conditionNode = creation.conditionVector(firstTerm=spacePlug, secondTerm=float(targetElement.logicalIndex()),
                                                 colorIfTrue=(1.0, 0.0, 0.0),
                                                 colorIfFalse=(0.0, 0.0, 0.0), operation=0,
                                                 name="_".join([targetShortName, sourceShortName, "space"]))
        condFn = om2.MFnDependencyNode(conditionNode)
        plugs.connectPlugs(condFn.findPlug("outColorR", False), targetWeightSource)
        conditions.append(conditionNode)

    return constraintMObject, conditions
