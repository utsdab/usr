"""
Note: this whole module is being replaced with spaceSwitching code.
"""

import json


from maya.api import OpenMaya as om2
from maya import cmds

from zoovendor.six.moves import range

from zoo.libs.maya.api import nodes
from zoo.libs.maya.api import plugs
from zoo.libs.maya.api import generic
from zoo.libs.maya.api import attrtypes
from zoo.libs.maya.utils import creation
from zoo.libs.utils import zlogging
logger = zlogging.getLogger(__name__)

PARENTCONSTRAINT_TYPE = 0
SCALECONSTRAINT_TYPE = 1
POINTCONSTRAINT_TYPE = 2
ORIENTCONSTRAINT_TYPE = 3
AIMCONSTRAINT_TYPE = 4
MATRIX_TYPE = 5


class BaseConstraint(object):
    def __init__(self, node=None, name=None):
        self.name = name
        if node is not None:
            self.node = om2.MObjectHandle(node)
        self._mfn = None

    def mobject(self):
        return self.node.object()

    @property
    def mfn(self):
        if self._mfn is not None:
            return self._mfn
        if self.node is None:
            raise ValueError("Must initialize the class with the constaint mobject or call create()")
        self._mfn = om2.MFnDependencyNode(self.node.object())
        return self._mfn

    def drivenObject(self):
        plug = self.mfn.findPlug("constraintParentInverseMatrix", False)
        if plug.isDestination:
            return plug.source().node()

    def driverObjects(self):
        plug = self.mfn.findPlug("target", False)
        targets = []
        for i in range(plug.evaluateNumElements()):
            targetElement = plug.elementByPhysicalIndex(i)
            for element in range(targetElement.numChildren()):
                child = targetElement.child(element)
                if child.isDestination:
                    targets.append(child.source().node())
                    break
        return targets

    def numTargets(self):
        mfn = self.mfn
        return mfn.findPlug("target", False).evaluateNumElements()


class ParentConstraint(BaseConstraint):
    def create(self, driver, driven, skipRotate=None, skipTranslate=None, maintainOffset=False):
        driverName = nodes.nameFromMObject(driver)
        drivenName = nodes.nameFromMObject(driven)

        const = cmds.parentConstraint(driverName, drivenName, skipRotate=skipRotate or [],
                                      skipTranslate=skipTranslate or [],
                                      weight=1.0, maintainOffset=maintainOffset)
        self.node = om2.MObjectHandle(nodes.asMObject(const[0]))
        mapping = dict(skipRotate=skipRotate,
                       skipTranslate=skipTranslate,
                       maintainOffset=maintainOffset)
        kwargsMap = json.dumps(mapping)
        # addConstraintMap(driver, (driven,), (self.node.object(),), kwargsMap=kwargsMap)
        return self.node.object()

    def addTarget(self, driver):
        """Adds the given driver transform to the constraint

        :param driver: The driver mobject transform
        :type driver: MObject

        .. note::
            having to use maya commands here due to api not able to resize the plugs array outside the datablock
        """
        driven = self.drivenObject()
        driverName = nodes.nameFromMObject(driver)  # so we have the fullPath
        driverShortName = om2.MNamespace.stripNamespaceFromName(driverName).split("|")[-1]
        nextWeightIndex = self.numTargets()  # starts at zero so the return is the next element
        drivenFn = om2.MFnDependencyNode(driven)
        offsetMatrix = om2.MTransformationMatrix(nodes.getOffsetMatrix(driver, driven))
        translation = offsetMatrix.translation(om2.MSpace.kTransform)
        rotation = generic.eulerToDegrees(
            offsetMatrix.rotation().reorder(plugs.getPlugValue(drivenFn.findPlug("rotateOrder", False))))
        # create the weight attribute
        weightName = "W".join([driverShortName, str(nextWeightIndex)])
        weightAttr = nodes.addAttribute(self.node.object(), weightName, weightName,
                                        attrType=attrtypes.kMFnNumericDouble)
        weightAttr.setMin(0.0)
        weightAttr.setMax(1.0)
        weightAttr.default = 1.0
        weightAttr.keyable = True
        driverFn = om2.MFnDependencyNode(driver)
        targetPlug = self.mfn.findPlug("target", False).elementByLogicalIndex(nextWeightIndex)
        cmds.connectAttr(driverFn.findPlug("parentMatrix", False).elementByPhysicalIndex(0).name(),
                         targetPlug.child(0).name())  # targetParentMatrix
        cmds.connectAttr(driverFn.findPlug("scale", False).name(), targetPlug.child(13).name())  # targetScale
        cmds.connectAttr(driverFn.findPlug("rotateOrder", False).name(),
                         targetPlug.child(8).name())  # targetRotateOrder
        cmds.connectAttr(driverFn.findPlug("rotate", False).name(), targetPlug.child(7).name())  # targetRotate
        cmds.connectAttr(driverFn.findPlug("rotatePivotTranslate", False).name(),
                         targetPlug.child(5).name())  # targetRotateTranslate
        cmds.connectAttr(driverFn.findPlug("rotatePivot", False).name(),
                         targetPlug.child(4).name())  # targetRotatePivot
        cmds.connectAttr(driverFn.findPlug("translate", False).name(), targetPlug.child(3).name())  # targetTranslate
        cmds.connectAttr(om2.MPlug(self.mfn.object(), weightAttr.object()).name(),
                         targetPlug.child(1).name())  # targetWeight
        # setting offset value
        plugs.setPlugValue(targetPlug.child(6), translation)  # targetOffsetTranslate
        plugs.setPlugValue(targetPlug.child(10), rotation)  # targetOffsetRotate


class MatrixConstraint(BaseConstraint):

    # :todo optimize parentInverse matrix by reconnecting to driven parent
    # :todo blending when needed
    # :todo rediscovery of nodes
    # :todo find drivers

    def __init__(self, node=None, name=None):
        super(MatrixConstraint, self).__init__(node, name)
        # if the constraint should be a dynamic constraint, if True then the parent inverse plug
        # from the child is left connected, else only the values will be copied to the offset
        self.dynamic = False

    def drivenObject(self):
        pass

    def driverObjects(self):
        pass

    def create(self, driver, driven, skipScale=None, skipRotate=None, skipTranslate=None, maintainOffset=False,
               space=om2.MFn.kWorld):
        composename = "_".join([self.name, "wMtxCompose"])

        multMatrix = None
        if maintainOffset:
            offset = nodes.getOffsetMatrix(driver, driven)
            offsetname = "_".join([self.name, "wMtxOffset"])
            parentInverse = nodes.parentInverseMatrixPlug(driven) if self.dynamic else plugs.getPlugValue(
                nodes.parentInverseMatrixPlug(driven))

            multMatrix = creation.createMultMatrix(offsetname,
                                                   inputs=(offset, nodes.worldMatrixPlug(driver),
                                                           parentInverse),
                                                   output=None)
            outputPlug = om2.MFnDependencyNode(multMatrix).findPlug("matrixSum", False)
        else:
            outputPlug = nodes.worldMatrixPlug(driver)

        decompose = creation.createDecompose(composename, destination=driven,
                                             translateValues=skipTranslate,
                                             scaleValues=skipScale, rotationValues=skipRotate)

        decomposeFn = om2.MFnDependencyNode(decompose)
        plugs.connectPlugs(om2.MFnDependencyNode(driver).findPlug("rotateOrder", False),
                           decomposeFn.findPlug("inputRotateOrder", False))
        plugs.connectPlugs(outputPlug, decomposeFn.findPlug("inputMatrix", False))
        self.node = om2.MObjectHandle(decompose)
        mapping = dict(skipScale=skipScale,
                       skipRotate=skipRotate,
                       skipTranslate=skipTranslate,
                       maintainOffset=maintainOffset)
        kwargsMap = json.dumps(mapping)
        # addConstraintMap(driver, (driven,), (decompose, multMatrix), kwargsMap=kwargsMap)
        return decompose, multMatrix


def hasConstraint(node):
    """Determines if this node is constrained by another, this is done by checking the constraints compound attribute

    :param node: the node to search for attached constraints
    :type node: om2.MObject
    :rtype: bool
    """
    # exit early when iterConstraints returns something
    for i in iterConstraints(node):
        return True
    return False


def addConstraintAttribute(node):
    """ Create's and returns the 'constraints' compound attribute, which is used to store all incoming constraints
    no matter how they are created. If the attribute exist's then that will be returned.

    :param node: The node to have the constraint compound attribute.
    :type node: om2.MObject
    :return: Return's the constraint compound attribute.
    :rtype: om2.MPlug
    """
    mfn = om2.MFnDependencyNode(node)
    if mfn.hasAttribute("constraints"):
        return mfn.findPlug("constraints", False)
    attrMap = [{"name": "driven", "Type": attrtypes.kMFnMessageAttribute, "isArray": False},
               {"name": "utilities", "Type": attrtypes.kMFnMessageAttribute, "isArray": False},
               {"name": "kwargs", "Type": attrtypes.kMFnDataString, "isArray": False}]

    return om2.MPlug(node, nodes.addCompoundAttribute(node, "constraints", "constraints", attrMap,
                                                      isArray=True).object())


def iterIncomingConstraints(node):
    """Walks upstream of this `node` to find the incoming constraintMap Attribute

    :param node:
    :type node:
    :return:
    :rtype:
    """
    fn = om2.MFnDependencyNode(node)
    if not fn.hasAttribute("constraint"):
        logger.debug("No constraint attr on", fn.name())
        return
    constraintPlug = fn.findPlug("constraint", False)
    for index in range(constraintPlug.evaluateNumElements()):
        element = constraintPlug.elementByPhysicalIndex(index)
        if not element.isDestination:
            continue
        parentPlug = element.source().parent()
        utilsPlug = parentPlug.child(1)
        destinations = utilsPlug.destinations()
        # driver, utilties
        yield parentPlug.node(), [i.node() for i in destinations]


def serializeIncomingConstraints(node):
    results = []
    for driver, utilties in iterIncomingConstraints(node):
        driverName = nodes.nameFromMObject(driver)
        results.append({"utilities": [nodes.serializeNode(i) for i in utilties],
                        "driver": driverName})


def iterConstraints(node):
    """Generator function that loops over the attached constraints, this is done
    by iterating over the compound array attribute `constraints`.

    :param node: The node to iterate, this node should already have the compound attribute
    :type node: om2.MObject
    :return: First element is a list a driven transforms, the second is a list of \
    utility nodes used to create the constraint.
    :rtype: tuple(list(om2.MObject), list(om2.MObject))
    """
    mfn = om2.MFnDependencyNode(node)
    if not mfn.hasAttribute("constraints"):
        return
    compoundPlug = mfn.findPlug("constraints", False)

    for i in range(compoundPlug.evaluateNumElements()):
        compElement = compoundPlug.elementByPhysicalIndex(i)
        drivenDest = compElement.child(0).destinations()
        utilDest = compElement.child(1).destinations()
        if drivenDest or utilDest:
            yield [i.node() for i in drivenDest], [i.node() for i in utilDest]


def addConstraintMap(node, driven, utilities, kwargsMap=None):
    """Adds a mapping of drivers and utilities to the constraint compound array attribute

    :param node: The node to add or has the constraint map , typically this would be the driver node \
    of the constraint.
    :type node: om2.MObject
    :param driven: a list of driven transform nodes.
    :type driven: tuple(om2.MObject)
    :param utilities: a list of utilities/support nodes that make up the constraint, this could be the \
    constraint node itself or any math node etc.
    :type utilities: tuple(om2.MObject)
    """
    kwargsmap = kwargsMap or ""
    mfn = om2.MFnDependencyNode(node)
    if not mfn.hasAttribute("constraints"):
        compoundPlug = addConstraintAttribute(node)
    else:
        compoundPlug = mfn.findPlug("constraints", False)
    availPlug = plugs.nextAvailableElementPlug(compoundPlug)
    drivenPlug = availPlug.child(0)
    # lets add the driven nodes to the xth of the element compound
    for drive in iter(driven):
        if drive is None:
            continue
        drivenFn = om2.MFnDependencyNode(drive)
        if drivenFn.hasAttribute("constraint"):
            p = drivenFn.findPlug("constraint", False)
            elementP = plugs.nextAvailableElementPlug(p)
            plugs.connectPlugs(drivenPlug, elementP)
            continue
        attr = nodes.addAttribute(drive, "constraint", "constraint", attrtypes.kMFnMessageAttribute, isArray=True)
        attrP = om2.MPlug(drive, attr.object())
        plugs.connectPlugs(drivenPlug, attrP.elementByLogicalIndex(0))
    utilPlug = availPlug.child(1)
    # add all the utilities
    for i in iter(utilities):
        if i is None:
            continue
        utilFn = om2.MFnDependencyNode(i)
        if utilFn.hasAttribute("constraint"):
            p = utilFn.findPlug("constraint", False)
            if p.isDestination:
                continue
            plugs.connectPlugs(utilPlug, p)
            continue
        attr = nodes.addAttribute(i, "constraint", "constraint", attrtypes.kMFnMessageAttribute)
        plugs.connectPlugs(utilPlug, om2.MPlug(i, attr.object()))
    # set the kwargs map plug, so we know how the constraint was created
    plugs.setPlugValue(availPlug.child(2), kwargsmap)
    return compoundPlug