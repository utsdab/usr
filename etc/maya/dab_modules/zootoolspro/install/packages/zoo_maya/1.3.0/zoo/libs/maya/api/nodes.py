import contextlib
from maya.api import OpenMaya as om2
from maya import cmds

from zoovendor.six.moves import range


from zoo.libs.maya.api import plugs, generic
from zoo.libs.maya.api import attrtypes
from zoo.libs.maya.utils import mayamath
from zoo.libs.utils import zoomath, zlogging

logger = zlogging.getLogger(__name__)

MIRROR_BEHAVIOUR = 0
MIRROR_ORIENTATION = 1




def asMObject(name):
    """ Returns the MObject from the given name

    :param name: The name to get from maya to convert to an mobject
    :type name: str or MObjectHandle or MDagPath
    :return: The mobject for the given str
    :rtype: MObject

    """
    sel = om2.MSelectionList()
    sel.add(name)
    try:
        return sel.getDagPath(0).node()
    except TypeError:
        return sel.getDependNode(0)


def nameFromMObject(mobject, partialName=False, includeNamespace=True):
    """This returns the full name or partial name for a given mobject, the mobject must be valid.

    :param mobject:
    :type mobject: MObject
    :param partialName: if False then this function will return the fullpath of the mobject.
    :type partialName: bool
    :param includeNamespace: if False the namespace will be stripped
    :type includeNamespace: bool
    :return:  the name of the mobject
    :rtype: str

    .. code-block:: python

        from zoo.libs.maya.api import nodes
        node = nodes.asMobject(cmds.polyCube())
        print nodes.nameFromMObject(node, partial=False) # returns the fullpath, always prepends '|' eg '|polyCube'
        print nodes.nameFromMObject(node, partial=True) # returns the partial name eg. polyCube1

    """
    if mobject.hasFn(om2.MFn.kDagNode):
        if partialName:
            name = om2.MFnDagNode(mobject).partialPathName()
        else:
            name = om2.MFnDagNode(mobject).fullPathName()
    else:
        # dependency node
        name = om2.MFnDependencyNode(mobject).name()
    if not includeNamespace:
        name = om2.MNamespace.stripNamespaceFromName(name)

    return name


def toApiMFnSet(node):
    """
    Returns the appropriate mObject from the api 2.0

    :param node: str, the name of the node
    :type node: str, MObjectHandle
    :return: MFnDagNode, MPlug, MFnDependencyNode
    :rtype: MPlug or MFnDag or MFnDependencyNode

    .. code-block:: python

        from zoo.libs.maya.api import nodes
        node = cmds.polyCube()[0] # str
        nodes.toApiObject(node)
        # Result MFnDagNode
        node = cmds.createNode("multiplyDivide")
        nodes.toApiObject(node)
        # Result MFnDependencyNode
    """
    if isinstance(node, om2.MObjectHandle):
        node = node.object()
    elif isinstance(node, (om2.MFnDependencyNode, om2.MFnDagNode)):
        return node

    sel = om2.MSelectionList()
    sel.add(node)
    try:
        tmp = sel.getDagPath(0)
        tmp = om2.MFnDagNode(tmp)
    except TypeError:
        tmp = om2.MFnDependencyNode(sel.getDependNode(0))
    return tmp


def asDagPath(node):
    sel = om2.MSelectionList()
    sel.add(node)
    return sel.getDagPath(0)


def setNodeColour(node, colour, outlinerColour=None, useOutlinerColour=False):
    """Set the given node mobject override color can be a mobject representing a transform or shape

    :param node: the node which you want to change the override colour of
    :type node: mobject
    :param colour: The RGB colour to set
    :type colour: MColor or tuple
    """
    dependNode = om2.MFnDagNode(om2.MFnDagNode(node).getPath())
    plug = dependNode.findPlug("overrideColorRGB", False)
    enabledPlug = dependNode.findPlug("overrideEnabled", False)
    overrideRGBColors = dependNode.findPlug("overrideRGBColors", False)
    if not enabledPlug.asBool():
        enabledPlug.setBool(True)
    if not overrideRGBColors.asBool():
        dependNode.findPlug("overrideRGBColors", False).setBool(True)
    plugs.setPlugValue(plug, colour)
    # deal with the outliner
    if outlinerColour:
        useOutliner = dependNode.findPlug("useOutlinerColor", False)
        if useOutlinerColour:
            useOutliner.setBool(True)
        plugs.setPlugValue(dependNode.findPlug("outlinerColor", False), outlinerColour)


def getNodeColourData(node):
    """
    :param node: The maya node mobject that you want to get the override colour from

    :type node: MObject
    :return: {"overrideEnabled": bool,
            "overrideColorRGB": plugs.getAttr(plug),
            "overrideRGBColors": plugs.getAttr(overrideRGBColors)}

    :rtype: dict
    """

    dependNode = om2.MFnDagNode(om2.MFnDagNode(node).getPath())
    plug = dependNode.findPlug("overrideColorRGB", False)
    enabledPlug = dependNode.findPlug("overrideEnabled", False)
    overrideRGBColors = dependNode.findPlug("overrideRGBColors", False)
    useOutliner = dependNode.findPlug("useOutlinerColor", False)
    return {"overrideEnabled": plugs.getPlugValue(enabledPlug),
            "overrideColorRGB": plugs.getPlugValue(plug),
            "overrideRGBColors": plugs.getPlugValue(overrideRGBColors),
            "useOutlinerColor": plugs.getPlugValue(useOutliner),
            "outlinerColor": plugs.getPlugValue(dependNode.findPlug("outlinerColor", False))}


def createDagNode(name, nodeType, parent=None, modifier=None):
    """Create's a new dag node and if theres a parent specified then parent the new node

    :param name: The new name of the created node
    :type name: str
    :param nodeType: The node type to create
    :type nodeType: str
    :param parent: The node the parent the new node to, if the parent is none or MObject.kNullObj then it will parent \
    to the world, defaults to world
    :type parent: MObject or MObject.kNullObj
    :return: The newly create nodes mobject
    :rtype: MObject
    """
    if parent is None or parent.isNull() or parent.apiType() in (om2.MFn.kInvalid, om2.MFn.kWorld):
        parent = om2.MObject.kNullObj

    mod = modifier or om2.MDagModifier()
    node = mod.createNode(nodeType)
    mod.renameNode(node, name)
    mod.reparentNode(node, parent)
    if modifier is None:
        mod.doIt()
    return node


def createDGNode(name, nodeType, modifier=None):
    """Creates and dependency graph node and returns the nodes mobject

    :param name: The newname of the node
    :type name: str
    :param nodeType: the node type to create
    :type nodeType: str
    :return: The mobject of the newly created node
    :rtype: MObject
    """
    mod = modifier or om2.MDGModifier()
    node = mod.createNode(nodeType)
    mod.renameNode(node, name)
    if modifier is None:
        mod.doIt()
    return node


def lockNode(mobject, state=True, modifier=None):
    """Set the lock state of the node

    :param mobject: the node mobject to set the lock state on
    :type mobject: MObject
    :param state: the lock state for the node
    :type state: bool
    """
    if om2.MFnDependencyNode(mobject).isLocked != state:
        mod = modifier or om2.MDGModifier()
        mod.setNodeLockState(mobject, state)
        if modifier is not None:
            mod.doIt()
        return mod


def unlockConnectedAttributes(mobject):
    """Unlocks all connected attributes to this node

    :param mobject: MObject representing the DG node
    :type mobject: MObject
    """
    for thisNodeP, otherNodeP in iterConnections(mobject, source=True, destination=True):
        if thisNodeP.isLocked:
            thisNodeP.isLocked = False


def unlockedAndDisconnectConnectedAttributes(mobject):
    """Unlcoks and disocnnects all attributes on the given node

    :param mobject: MObject respresenting the DG node
    :type mobject: MObject
    """
    for thisNodeP, otherNodeP in iterConnections(mobject, source=False, destination=True):
        plugs.disconnectPlug(thisNodeP)


def containerFromNode(mobj):
    """Finds and returns the AssetContainer mobject from the give node.

    :param mobj: The om2.MObject representing the node to filter.
    :type mobj: om2.MObject
    :return: The container MObject found from the mobject else None
    :rtype: om2.MObject or None
    """
    fn = om2.MFnDependencyNode(mobj)
    messagePlug = fn.findPlug("message", False)
    for dest in messagePlug.destinations():
        node = dest.node()
        if node.hasFn(om2.MFn.kHyperLayout):
            continue
        hyperLayoutMsg = fn.setObject(dest.node()).findPlug("message", False)
        for possibleObj in hyperLayoutMsg.destinations():
            node = possibleObj.node()
            if node.hasFn(om2.MFn.kContainer):
                return node


def childPathAtIndex(path, index):
    """From the given MDagPath return a new MDagPath for the child node at the given index.

    :param path: MDagPath
    :type index: int
    :return: MDagPath, this path's child at the given index
    """

    existingChildCount = path.childCount()
    if existingChildCount < 1:
        return None
    if index < 0:
        index = path.childCount() - abs(index)
    copy = om2.MDagPath(path)
    copy.push(path.child(index))
    return copy


def childPaths(path):
    """Returns all the MDagPaths that are a child of path.

    :param path: MDagPath
    :return: list(MDagPaths), child MDagPaths which have path as parent
    """
    outPaths = [childPathAtIndex(path, i) for i in range(path.childCount())]
    return outPaths


def childPathsByFn(path, fn):
    """Get all children below path supporting the given MFn.type

    :param path: MDagpath
    :param fn: member of MFn
    :return: list(MDagPath), all matched paths below this path
    """
    return [p for p in childPaths(path) if p.hasFn(fn)]


def iterShapes(path, filterTypes=()):
    """Generator function which all the shape dagpaths directly below this dagpath

    :param path: The MDagPath to search
    :return: list(MDagPath)
    """
    for i in range(path.numberOfShapesDirectlyBelow()):
        dagPath = om2.MDagPath(path)
        dagPath.extendToShape(i)
        if not filterTypes or dagPath.apiType() in filterTypes:
            yield dagPath


def shapes(path, filterTypes=()):
    """
    :Depreciated Use IterShapes()
    """
    return list(iterShapes(path, filterTypes))


def shapeAtIndex(path, index):
    """Finds and returns the shape DagPath under the specified path for the index

    :param path: the MDagPath to the parent node that you wish to search under
    :type path: om2.MDagPath
    :param index: the shape index
    :type index: int
    :rtype: om2.MDagPath or None
    """
    if index in range(path.numberOfShapesDirectlyBelow()):
        return om2.MDagPath(path).extendToShape(index)


def childTransforms(path):
    """Returns all the child transform from the given DagPath

    :type path: om2.MDagPath
    :return: list(MDagPath) to all transforms below path
    """
    return childPathsByFn(path, om2.MFn.kTransform)


def setParent(child, newParent, maintainOffset=False):
    """Sets the parent for the given child

    :param child: the child node which will have its parent changed
    :type child: om2.MObject
    :param newParent: The new parent for the child
    :type newParent: om2.MObject
    :param maintainOffset: if True then the current transformation is maintained relative to the new parent
    :type maintainOffset: bool
    :rtype: bool
    """

    newParent = newParent or om2.MObject.kNullObj
    if child == newParent:
        return False
    dag = om2.MDagModifier()
    if maintainOffset:
        if newParent == om2.MObject.kNullObj:
            offset = getWorldMatrix(child)
        else:
            start = getWorldMatrix(newParent)
            end = getWorldMatrix(child)
            offset = end * start.inverse()
    dag.reparentNode(child, newParent)
    dag.doIt()
    if maintainOffset:
        setMatrix(child, offset)
    return True


@contextlib.contextmanager
def childContext(parent):
    children = []
    for child in iterChildren(parent, False, (om2.MFn.kTransform, om2.MFn.kJoint)):
        setParent(child, om2.MObject.kNullObj)
        children.append(child)
    yield
    for i in iter(children):
        setParent(i, parent, True)


def hasParent(mobject):
    """Determines if the given MObject has a mobject

    :param mobject: the MObject node to check
    :type mobject: MObject
    :rtype: bool
    """
    parent = getParent(mobject)
    if parent is None or parent.isNull():
        return False
    return True


def rename(mobject, newName, modifier=None):
    """Renames the given mobject node, this is undoable.

    :param mobject: the node to rename
    :type mobject: om2.MObject
    :param newName: the new unique name for the node
    :type newName: str
    :param modifier: if you pass a instance then the rename will be added to the queue then \
    returned otherwise a new  instance will be created and immediately executed.
    :type modifier: om2.MDGModifier or None

    .. note::
        If you pass a MDGModfifier then you should call doIt() after callig this function

    """
    dag = modifier or om2.MDGModifier()
    dag.renameNode(mobject, newName)
    # if a modifier is passed into the function then let the user deal with DoIt
    if modifier is None:
        dag.doIt()
    return dag


def parentPath(path):
    """Returns the parent nodes MDagPath

    :param path: child DagPath
    :type path: MDagpath
    :return: MDagPath, parent of path or None if path is in the scene root.
    """
    parent = om2.MDagPath(path)
    parent.pop(1)
    if parent.length() == 0:  # ignore world !
        return
    return parent


def isValidMDagPath(dagPath):
    """ Determines if the given MDagPath is valid

    :param dagPath: MDagPath
    :return: bool
    """
    return dagPath.isValid() and dagPath.fullPathName()


def iterParents(mobject):
    parent = getParent(mobject=mobject)
    while parent is not None:
        yield parent
        parent = getParent(parent)


def isSceneRoot(node):
    fn = om2.MFnDagNode(node)
    return fn.object().hasFn(om2.MFn.kDagNode) and fn.name() == "world"


def isUnderSceneRoot(node):
    """Determines if the specified node is currently parented to world.

    :param node: The maya Dag MObject
    :type node: :class:`om2.MObject`
    :rtype: bool
    """
    fn = om2.MFnDagNode(node)
    par = fn.parent(0)
    return isSceneRoot(par)


def iterChildren(mObject, recursive=False, filter=None):
    """Generator function that can recursive iterate over the children of the given MObject.

    :param mObject: The MObject to traverse must be a MObject that points to a transform
    :type mObject: MObject
    :param recursive: Whether to do a recursive search
    :type recursive: bool
    :param filter: tuple(om.MFn) or None, the node type to find, can be either 'all' for returning everything or a \
    om.MFn type constant does not include shapes
    :type filter: tuple or None
    :return: om.MObject
    """
    dagNode = om2.MDagPath.getAPathTo(mObject)
    childCount = dagNode.childCount()
    if not childCount:
        return
    filter = filter or ()

    for index in range(childCount):
        childObj = dagNode.child(index)
        if not filter or childObj.apiType() in filter:
            yield childObj
            if recursive:
                for x in iterChildren(childObj, recursive, filter):
                    yield x


def breadthFirstSearchDag(node, filter=None):
    ns = tuple(iterChildren(node, False, filter=filter))
    if not ns:
        return
    yield ns
    for i in ns:
        for t in breadthFirstSearchDag(i):
            yield t


def getChildren(mObject, recursive=False, filter=(om2.MFn.kTransform,)):
    """This function finds and returns all children mobjects under the given transform, if recursive then including
     sub children.

    :param mObject: om.MObject, the mObject of the transform to search under
    :param recursive: bool
    :param filter: tuple(om.MFn.kTransform, the node type to filter by
    :return: list(MFnDagNode)
    """
    return tuple(iterChildren(mObject, recursive, filter))


def iterAttributes(node, skip=None, includeAttributes=()):
    skip = skip or ()
    dep = om2.MFnDependencyNode(node)
    for idx in range(dep.attributeCount()):
        attr = dep.attribute(idx)
        plug = om2.MPlug(node, attr)
        name = plug.name()

        if any(i in name for i in skip) and not any(i in name for i in includeAttributes):
            continue
        elif plug.isElement or plug.isChild:
            continue
        yield plug
        for child in plugs.iterChildren(plug):
            yield child


def iterExtraAttributes(node, filteredType=None):
    """Generator function to iterate over all extra plugs(dynamic) of a given node.

    :param node: The DGNode or DagNode to iterate
    :type node: om2.MObject
    :param filteredType:
    :type filteredType: attrtypes.kType
    :return: Generator function with each item equaling a om2.MPlug
    :rtype: om2.MPlug
    """
    dep = om2.MFnDependencyNode(node)
    for idx in range(dep.attributeCount()):
        attr = dep.attribute(idx)
        plug = om2.MPlug(node, attr)
        if plug.isDynamic:
            if filteredType is None or plugs.plugType(plug) == filteredType:
                yield plug


def iterConnections(node, source=True, destination=True):
    """Returns a generator function containing a tuple of MPlugs

    :param node: The node to search
    :type node: om2.MObject
    :param source: If true then all upstream connections are returned
    :type source: bool
    :param destination: If true all downstream connections are returned
    :type destination: bool
    :return: tuple of om2.MPlug instances, the first element is the connected MPlug of the given node(``node``) \
    The second element is the connected MPlug from the other node.
    :rtype: Generator(tuple(om2.MPlug, om2.MPlug))
    """
    dep = om2.MFnDependencyNode(node)
    for pl in iter(dep.getConnections()):
        if source and pl.isSource:
            for i in iter(pl.destinations()):
                yield pl, i
        if destination and pl.isDestination:
            yield pl, pl.source()


def iterKeyablePlugs(node):
    dep = om2.MFnDependencyNode(node)
    for i in range(dep.attributeCount()):
        attr = dep.attribute(i)
        plug = om2.MPlug(node, attr)
        if plug.isKeyable:
            yield plug


def iterChannelBoxPlugs(node):
    dep = om2.MFnDependencyNode(node)
    for i in range(dep.attributeCount()):
        attr = dep.attribute(i)
        plug = om2.MPlug(node, attr)
        if plug.isKeyable and plug.isChannelBox:
            yield plug


def getRoots(nodes):
    roots = set()
    for node in nodes:
        root = getRoot(node)
        if root:
            roots.add(root)
    return list(roots)


def getRoot(mobject):
    """Traversals the objects parent until the root node is found and returns the MObject

    :param mobject: MObject
    :return: MObject
    """
    current = mobject
    for node in iterParents(mobject):
        if node is None:
            return current
        current = node
    return current


def getParent(mobject):
    """Returns the parent MFnDagNode if it has a parent else None

    :param mobject: MObject
    :return: MObject or None
    """
    if mobject.hasFn(om2.MFn.kDagNode):
        dagpath = om2.MDagPath.getAPathTo(mobject)
        if dagpath.node().apiType() == om2.MFn.kWorld:
            return None
        dagNode = om2.MFnDagNode(dagpath).parent(0)
        if dagNode.apiType() == om2.MFn.kWorld:
            return None
        return dagNode


def isValidMObject(node):
    mo = om2.MObjectHandle(node)
    return mo.isValid() and mo.isAlive()


def delete(node):
    """Delete the given nodes

    :param node:
    """
    if not isValidMObject(node):
        return
    lockNode(node, False)
    unlockedAndDisconnectConnectedAttributes(node)

    mod = om2.MDagModifier()
    mod.deleteNode(node)
    mod.doIt()


def removeUnknownNodes():
    unknownNodes = cmds.ls(type="unknown")
    try:
        nodesToDelete = []
        for node in unknownNodes:
            if cmds.referenceQuery(node, isNodeReferenced=True):
                continue
            cmds.lockNode(node, lock=False)
            nodesToDelete.append(node)
        if nodesToDelete:
            cmds.delete(nodesToDelete)
    except RuntimeError:
        logger.error("Failed to remove Unknown Nodes",
                     exc_info=True)
    return True


def getOffsetMatrix(startObj, endObj, space=om2.MFn.kWorld):
    if space == om2.MFn.kWorld:
        start = getWorldMatrix(startObj)
        end = getWorldMatrix(endObj)
    else:
        start = getMatrix(startObj)
        end = getMatrix(endObj)
    mOutputMatrix = end * start.inverse()
    return mOutputMatrix


def getMatrix(mobject):
    """ Returns the MMatrix of the given mobject

    :param mobject: MObject
    :return: :class:`om2.MMatrix`
    """
    return plugs.getPlugValue(om2.MFnDependencyNode(mobject).findPlug("matrix", False))


def worldMatrixPlug(mobject):
    wm = om2.MFnDependencyNode(mobject).findPlug("worldMatrix", False)
    return wm.elementByLogicalIndex(0)


def getWorldMatrix(mobject):
    """Returns the worldMatrix value as an MMatrix.

    :param mobject: the MObject that points the dagNode
    :type mobject: :class:`om2.MObject`
    :return: MMatrix
    """
    return plugs.getPlugValue(worldMatrixPlug(mobject))


def decomposeMatrix(matrix, rotationOrder, space=om2.MSpace.kWorld):
    transformMat = om2.MTransformationMatrix(matrix)
    transformMat.reorderRotation(rotationOrder)
    rotation = transformMat.rotation(asQuaternion=(space == om2.MSpace.kWorld))
    return transformMat.translation(space), rotation, transformMat.scale(space)


def parentInverseMatrixPlug(mobject):
    wm = om2.MFnDependencyNode(mobject).findPlug("parentInverseMatrix", False)
    return wm.elementByLogicalIndex(0)


def getWorldInverseMatrix(mobject):
    """Returns the world inverse matrix of the given MObject

    :param mobject: MObject
    :return: MMatrix
    """
    wm = om2.MFnDependencyNode(mobject).findPlug("worldInverseMatrix", False)
    wm.evaluateNumElements()
    matplug = wm.elementByPhysicalIndex(0)
    return plugs.getPlugValue(matplug)


def getParentMatrix(mobject):
    """Returns the parent matrix of the given MObject

    :param mobject: MObject
    :return: MMatrix
    """
    wm = om2.MFnDependencyNode(mobject).findPlug("parentMatrix", False)
    wm.evaluateNumElements()
    matplug = wm.elementByPhysicalIndex(0)
    return plugs.getPlugValue(matplug)


def getParentInverseMatrix(mobject):
    """Returns the parent inverse matrix from the Mobject

    :param mobject: MObject
    :return: MMatrix
    """
    return plugs.getPlugValue(parentInverseMatrixPlug(mobject))


def hasAttribute(node, name):
    """Searches the node for a give a attribute name and returns True or False

    :param node: MObject, the nodes MObject
    :param name: str, the attribute name to find
    :return: bool
    """
    return om2.MFnDependencyNode(node).hasAttribute(name)


def setMatrix(mobject, matrix, space=om2.MSpace.kTransform):
    """Sets the objects matrix using om2.MTransform.

    :param mobject: The transform Mobject to modify
    :type mobject: :class:`om2.MSpace.kWorld`
    :param matrix: The maya MMatrix to set
    :type matrix: :class:`om2.MMatrix`
    :param space: The coordinate space to set the matrix by
    """
    dag = om2.MFnDagNode(mobject)
    transform = om2.MFnTransform(dag.getPath())
    tMtx = om2.MTransformationMatrix(matrix)
    transform.setTranslation(tMtx.translation(space), space)
    transform.setRotation(tMtx.rotation(asQuaternion=True), space)
    transform.setScale(tMtx.scale(space))


def setTranslation(obj, position, space=None):
    path = om2.MFnDagNode(obj).getPath()
    space = space or om2.MSpace.kTransform
    trans = om2.MFnTransform(path)
    trans.setTranslation(position, space)
    return True


def getTranslation(obj, space=None):
    space = space or om2.MSpace.kTransform
    path = om2.MFnDagNode(obj).getPath()
    trans = om2.MFnTransform(path)
    return trans.translation(space)


def cvPositions(shape, space=None):
    space = space or om2.MSpace.kObject
    curve = om2.MFnNurbsCurve(shape)
    return curve.cvPositions(space)


def setCurvePositions(shape, points, space=None):
    space = space or om2.MSpace.kObject
    curve = om2.MFnNurbsCurve(shape)
    if len(points) != curve.numCVs:
        raise ValueError("Mismatched current curves cv count and the length of points to modify")
    curve.setCVPositions(points, space)


def setRotation(node, rotation, space=om2.MSpace.kTransform):
    path = om2.MFnDagNode(node).getPath()
    trans = om2.MFnTransform(path)
    if isinstance(rotation, (list, tuple)):
        rotation = om2.MEulerRotation([om2.MAngle(i, om2.MAngle.kDegrees).asRadians() for i in rotation])
    trans.setRotation(rotation, space)


def getRotation(obj, space, asQuaternion=False):
    """
    :param obj:
    :type obj: om2.MObject or om2.MDagPath
    :param space:
    :type space:
    :param asQuaternion:
    :type asQuaternion:
    :return:
    :rtype:
    """
    space = space or om2.MSpace.kTransform
    trans = om2.MFnTransform(obj)
    return trans.rotation(space, asQuaternion=asQuaternion)


def addProxyAttribute(node, sourcePlug, **kwargs):
    if kwargs["Type"] == attrtypes.kMFnCompoundAttribute:
        attr1 = addCompoundAttribute(node, attrMap=kwargs["children"], **kwargs)
        attrPlug = om2.MPlug(node, attr1.object())
        # turn all the child plugs to proxy, since maya doesn't support doing this
        # at the compound level, then do the connection between the matching children
        for childIdx in range(attrPlug.numChildren()):
            childPlug = attrPlug.child(childIdx)
            attr = childPlug.attribute()
            # turn the proxy state on and do the connection
            plugs.getPlugFn(attr)(attr).isProxyAttribute = True
            plugs.connectPlugs(sourcePlug.child(childIdx), attrPlug.child(childIdx))
    else:
        attr1 = addAttribute(node, **kwargs)
        attr1.isProxyAttribute = True
        plugs.connectPlugs(sourcePlug, om2.MPlug(node, attr1.object()))

    return attr1


def addCompoundAttribute(node, longName, shortName, attrMap, isArray=False, apply=True, **kwargs):
    """

    :param node: the node to add the compound attribute too.
    :type node: om2.MObject
    :param longName: the compound longName
    :type longName: str
    :param shortName: the compound shortName
    :type shortName: str
    :param attrMap: [{"name":str, "type": attrtypes.kType, "isArray": bool}]
    :type attrMap: list(dict())
    :return: the MObject attached to the compound attribute
    :rtype: om2.MObject

    .. code-block:: python

        attrMap = [{"name":"something", "Type": attrtypes.kMFnMessageAttribute, "isArray": False}]
        print attrMap
        # result <OpenMaya.MObject object at 0x00000000678CA790> #

    """
    compound = om2.MFnCompoundAttribute()
    compObj = compound.create(longName, shortName)
    compound.array = isArray
    children = []
    for attrData in attrMap:
        if attrData["Type"] == attrtypes.kMFnCompoundAttribute:
            # When create child compounds maya only wants the root attribute to
            # created. All children will be created because we execute the addChild()
            child = addCompoundAttribute(node, attrData["name"], attrData["name"],
                                         attrData.get("children", []), apply=False, **attrData)
        else:
            child = addAttribute(node, shortName=attrData["name"], longName=attrData["name"], attrType=attrData["Type"],
                                 apply=False, **attrData)
        if child is not None:
            attrObj = child.object()
            compound.addChild(attrObj)
            children.append(om2.MPlug(node, attrObj))
    if apply:
        mod = om2.MDGModifier()
        mod.addAttribute(node, compObj)
        mod.doIt()
        kwargs["children"] = attrMap
        plugs.setPlugInfoFromDict(om2.MPlug(node, compObj), **kwargs)

    return compound


def addAttributesFromList(node, data):
    """Creates an attribute on the node given a list(dict) of attribute data::

        [{
            "channelBox": true,
            "default": 3,
            "isDynamic": true,
            "keyable": false,
            "locked": false,
            "max": 9999,
            "min": 1,
            "name": "jointCount",
            "softMax": null,
            "softMin": null,
            "Type": 2,
            "value": 3
            "isArray": True
        }]

    :param data: The serialized form of the attribute
    :type data: dict
    :return: A list of create MPlugs
    :rtype: list(om2.MPlug)
    """
    created = []
    for attrData in iter(data):
        Type = attrData["Type"]
        default = attrData["default"]
        value = attrData["value"]
        name = attrData["name"]

        if Type == attrtypes.kMFnDataString:
            default = om2.MFnStringData().create(default)
        elif Type == attrtypes.kMFnDataMatrix:
            default = om2.MFnMatrixData().create(om2.MMatrix(default))
        elif Type == attrtypes.kMFnUnitAttributeAngle:
            default = om2.MAngle(default, om2.MAngle.kDegrees)
            value = om2.MAngle(value, om2.MAngle.kDegrees)

        plug = om2.MPlug(node, addAttribute(node, name, name, Type, isArray=data.get("array", False), apply=True))
        plugs.setPlugDefault(plug, default)

        plug.isChannelBox = attrData["value"]
        plug.isKeyable = attrData["keyable"]
        plugs.setLockState(plug, attrData["locked"])
        plugs.setMin(plug, attrData["min"])
        plugs.setMax(plug, attrData["max"])
        plugs.setSoftMin(plug, attrData["softMin"])
        plugs.setSoftMax(plug, attrData["softMax"])
        if not plug.attribute().hasFn(om2.MFn.kMessageAttribute):
            plugs.setPlugValue(plug, value)
        created.append(plug)
    return created


def addAttribute(node, longName, shortName, attrType=attrtypes.kMFnNumericDouble, isArray=False, apply=True, **kwargs):
    """This function uses the api to create attributes on the given node, currently WIP but currently works for
    string,int, float, bool, message, matrix. if the attribute exists a ValueError will be raised.

    :param node: MObject
    :param longName: str, the long name for the attribute
    :param shortName: str, the shortName for the attribute
    :param attrType: attribute Type, attrtypes constants
    :param apply: if False the attribute will be immediately created on the node else just return the attribute instance
    :rtype: om.MObject

    .. code-block:: python

        # message attribute
        attrMobj = addAttribute(myNode, "testMsg", "testMsg", attrType=attrtypes.kMFnMessageAttribute,
                                 isArray=False, apply=True)
        # double angle
        attrMobj = addAttribute(myNode, "myAngle", "myAngle", attrType=attrtypes.kMFnUnitAttributeAngle,
                                 keyable=True, channelBox=False)
        # double angle
        attrMobj = addAttribute(myNode, "myEnum", "myEnum", attrType=attrtypes.kMFnkEnumAttribute,
                                 keyable=True, channelBox=True, enums=["one", "two", "three"])


    """
    if hasAttribute(node, longName):
        raise ValueError("Node -> '%s' already has attribute -> '%s'" % (nameFromMObject(node), longName))
    aobj = None
    attr = None
    if attrType == attrtypes.kMFnNumericDouble:
        attr = om2.MFnNumericAttribute()
        aobj = attr.create(longName, shortName, om2.MFnNumericData.kDouble)
    elif attrType == attrtypes.kMFnNumericFloat:
        attr = om2.MFnNumericAttribute()
        aobj = attr.create(longName, shortName, om2.MFnNumericData.kFloat)
    elif attrType == attrtypes.kMFnNumericBoolean:
        attr = om2.MFnNumericAttribute()
        aobj = attr.create(longName, shortName, om2.MFnNumericData.kBoolean)
    elif attrType == attrtypes.kMFnNumericInt:
        attr = om2.MFnNumericAttribute()
        aobj = attr.create(longName, shortName, om2.MFnNumericData.kInt)
    elif attrType == attrtypes.kMFnNumericShort:
        attr = om2.MFnNumericAttribute()
        aobj = attr.create(longName, shortName, om2.MFnNumericData.kShort)
    elif attrType == attrtypes.kMFnNumericLong:
        attr = om2.MFnNumericAttribute()
        aobj = attr.create(longName, shortName, om2.MFnNumericData.kLong)
    elif attrType == attrtypes.kMFnNumericByte:
        attr = om2.MFnNumericAttribute()
        aobj = attr.create(longName, shortName, om2.MFnNumericData.kByte)
    elif attrType == attrtypes.kMFnNumericChar:
        attr = om2.MFnNumericAttribute()
        aobj = attr.create(longName, shortName, om2.MFnNumericData.kChar)
    elif attrType == attrtypes.kMFnNumericAddr:
        attr = om2.MFnNumericAttribute()
        aobj = attr.createAddr(longName, shortName)
    elif attrType == attrtypes.kMFnkEnumAttribute:
        attr = om2.MFnEnumAttribute()
        aobj = attr.create(longName, shortName)
        fields = kwargs.get("enums")
        if fields is not None:
            for index in range(len(fields)):
                attr.addField(fields[index], index)
    elif attrType == attrtypes.kMFnCompoundAttribute:
        attr = om2.MFnCompoundAttribute()
        aobj = attr.create(longName, shortName)
    elif attrType == attrtypes.kMFnMessageAttribute:
        attr = om2.MFnMessageAttribute()
        aobj = attr.create(longName, shortName)
    elif attrType == attrtypes.kMFnDataString:
        attr = om2.MFnTypedAttribute()
        stringData = om2.MFnStringData().create("")
        aobj = attr.create(longName, shortName, om2.MFnData.kString, stringData)
    elif attrType == attrtypes.kMFnUnitAttributeDistance:
        attr = om2.MFnUnitAttribute()
        aobj = attr.create(longName, shortName, om2.MDistance())
    elif attrType == attrtypes.kMFnUnitAttributeAngle:
        attr = om2.MFnUnitAttribute()
        aobj = attr.create(longName, shortName, om2.MAngle())
    elif attrType == attrtypes.kMFnUnitAttributeTime:
        attr = om2.MFnUnitAttribute()
        aobj = attr.create(longName, shortName, om2.MTime())
    elif attrType == attrtypes.kMFnDataMatrix:
        attr = om2.MFnMatrixAttribute()
        aobj = attr.create(longName, shortName)
    elif attrType == attrtypes.kMFnDataFloatArray:
        attr = om2.MFnFloatArray()
        aobj = attr.create(longName, shortName)
    elif attrType == attrtypes.kMFnDataDoubleArray:
        data = om2.MFnDoubleArrayData().create(om2.MDoubleArray())
        attr = om2.MFnTypedAttribute()
        aobj = attr.create(longName, shortName, om2.MFnData.kDoubleArray, data)
    elif attrType == attrtypes.kMFnDataIntArray:
        data = om2.MFnIntArrayData().create(om2.MIntArray())
        attr = om2.MFnTypedAttribute()
        aobj = attr.create(longName, shortName, om2.MFnData.kIntArray, data)
    elif attrType == attrtypes.kMFnDataPointArray:
        data = om2.MFnPointArrayData().create(om2.MPointArray())
        attr = om2.MFnTypedAttribute()
        aobj = attr.create(longName, shortName, om2.MFnData.kPointArray, data)
    elif attrType == attrtypes.kMFnDataVectorArray:
        data = om2.MFnVectorArrayData().create(om2.MVectorArray())
        attr = om2.MFnTypedAttribute()
        aobj = attr.create(longName, shortName, om2.MFnData.kVectorArray, data)
    elif attrType == attrtypes.kMFnDataStringArray:
        data = om2.MFnStringArrayData().create(om2.MStringArray())
        attr = om2.MFnTypedAttribute()
        aobj = attr.create(longName, shortName, om2.MFnData.kStringArray, data)
    elif attrType == attrtypes.kMFnDataMatrixArray:
        data = om2.MFnMatrixArrayData().create(om2.MMatrixArray())
        attr = om2.MFnTypedAttribute()
        aobj = attr.create(longName, shortName, om2.MFnData.kMatrixArray, data)
    elif attrType == attrtypes.kMFnNumericInt64:
        attr = om2.MFnNumericAttribute()
        aobj = attr.create(longName, shortName, om2.MFnNumericData.kInt64)
    elif attrType == attrtypes.kMFnNumericLast:
        attr = om2.MFnNumericAttribute()
        aobj = attr.create(longName, shortName, om2.MFnNumericData.kLast)
    elif attrType == attrtypes.kMFnNumeric2Double:
        attr = om2.MFnNumericAttribute()
        aobj = attr.create(longName, shortName, om2.MFnNumericData.k2Double)
    elif attrType == attrtypes.kMFnNumeric2Float:
        attr = om2.MFnNumericAttribute()
        aobj = attr.create(longName, shortName, om2.MFnNumericData.k2Float)
    elif attrType == attrtypes.kMFnNumeric2Int:
        attr = om2.MFnNumericAttribute()
        aobj = attr.create(longName, shortName, om2.MFnNumericData.k2Int)
    elif attrType == attrtypes.kMFnNumeric2Long:
        attr = om2.MFnNumericAttribute()
        aobj = attr.create(longName, shortName, om2.MFnNumericData.k2Long)
    elif attrType == attrtypes.kMFnNumeric2Short:
        attr = om2.MFnNumericAttribute()
        aobj = attr.create(longName, shortName, om2.MFnNumericData.k2Short)
    elif attrType == attrtypes.kMFnNumeric3Double:
        attr = om2.MFnNumericAttribute()
        aobj = attr.create(longName, shortName, om2.MFnNumericData.k3Double)
    elif attrType == attrtypes.kMFnNumeric3Float:
        attr = om2.MFnNumericAttribute()
        aobj = attr.createPoint(longName, shortName)
    elif attrType == attrtypes.kMFnNumeric3Int:
        attr = om2.MFnNumericAttribute()
        aobj = attr.create(longName, shortName, om2.MFnNumericData.k3Int)
    elif attrType == attrtypes.kMFnNumeric3Long:
        attr = om2.MFnNumericAttribute()
        aobj = attr.create(longName, shortName, om2.MFnNumericData.k3Long)
    elif attrType == attrtypes.kMFnNumeric3Short:
        attr = om2.MFnNumericAttribute()
        aobj = attr.create(longName, shortName, om2.MFnNumericData.k3Short)
    elif attrType == attrtypes.kMFnNumeric4Double:
        attr = om2.MFnNumericAttribute()
        aobj = attr.create(longName, shortName, om2.MFnNumericData.k4Double)

    attr.array = isArray
    storable = kwargs.get("storable", True)
    writable = kwargs.get("writable", True)
    connectable = kwargs.get("connectable", True)
    attr.storable = storable
    attr.writable = writable
    attr.connectable = connectable

    if aobj is not None and apply:
        mod = om2.MDGModifier()
        mod.addAttribute(node, aobj)

        mod.doIt()
        plug = om2.MPlug(node, aobj)
        kwargs["Type"] = attrType
        plugs.setPlugInfoFromDict(plug, **kwargs)
    return attr


def serializeNode(node, skipAttributes=None, includeConnections=True, includeAttributes=()):
    """This function takes an om2.MObject representing a maya node and serializes it into a dict,
    This iterates through all attributes, serializing any extra attributes found, any default attribute has not changed
    (defaultValue) and not connected or is an array attribute will be skipped.
    if `arg` includeConnections is True then all destination connections are serializated as a dict per connection.

    :param node: The node to serialize
    :type node: om2.MObject
    :param skipAttributes: The list of attribute names to serialization.
    :type skipAttributes: list or None
    :param includeConnections: If True find and serialize all connections where the destination is this node.
    :type includeConnections: bool
    :rtype: dict

    Returns values::

        {
                    "attributes": [
                    {
                      "Type": 10,
                      "channelBox": false,
                      "default": 0.0,
                      "isArray": false,
                      "isDynamic": true,
                      "keyable": true,
                      "locked": false,
                      "max": null,
                      "min": null,
                      "name": "toeRest",
                      "softMax": 3.14,
                      "softMin": -1.7,
                      "value": 0.31353071143768485
                    },
                  ],
                  "connections": [
                    {
                      "destination": "|legGlobal_L_cmpnt|control|configParameters",
                      "destinationPlug": "plantLength",
                      "source": "|legGlobal_L_guide_heel_ctrl|legGlobal_L_guide_tip_ctrl",
                      "sourcePlug": "translateZ"
                    },
                  ],
                  "name": "|legGlobal_L_cmpnt|control|configParameters",
                  "parent": "|legGlobal_L_cmpnt|control",
                  "type": "transform"
        }

    """
    dep = om2.MFnDagNode(node) if node.hasFn(om2.MFn.kDagNode) else om2.MFnDependencyNode(node)
    name = (dep.fullPathName() if node.hasFn(om2.MFn.kDagNode) else dep.name())
    name = name.replace(om2.MNamespace.getNamespaceFromName(name).split("|")[-1] + ":", "")
    data = {"name": name,
            "type": dep.typeName,
            }
    req = dep.pluginName
    if req:
        data["requirements"] = req
    if node.hasFn(om2.MFn.kDagNode):
        data["parent"] = om2.MFnDagNode(dep.parent(0)).fullPathName()
    attributes = []
    visited = []
    for pl in iterAttributes(node, skip=skipAttributes, includeAttributes=includeAttributes):
        if (pl.isDefaultValue() or pl.isChild) and not any(i in pl.name() for i in includeAttributes):
            continue
        attrData = plugs.serializePlug(pl)
        if attrData:
            attributes.append(attrData)
        visited.append(pl)

    if includeConnections:
        connections = []
        for destination, source in iterConnections(node, source=False, destination=True):
            connections.append(plugs.serializeConnection(destination))
        if connections:
            data["connections"] = connections
    if attributes:
        data["attributes"] = attributes

    return data


def deserializeNode(data, parent=None):
    """

    example Data::

        {
                "attributes": [
                {
                  "Type": 10,
                  "channelBox": false,
                  "default": 0.0,
                  "isArray": false,
                  "isDynamic": true,
                  "keyable": true,
                  "locked": false,
                  "max": null,
                  "min": null,
                  "name": "toeRest",
                  "softMax": 3.14,
                  "softMin": -1.7,
                  "value": 0.31353071143768485
                },
              ],
              "name": "|legGlobal_L_cmpnt|control|configParameters",
              "parent": "|legGlobal_L_cmpnt|control",
              "type": "transform"
        }

    :param data: Same data as serializeNode()
    :type data: dict
    :param parent: The parent of the newly created node if any defaults to None which is the same as the world node
    :type parent: om2.MObject
    :return: The created node MObject, a list of created attributes
    :rtype: tuple(MObject, list(om2.MPlug))
    """
    nodeName = data["name"].split("|")[-1]
    nodeType = data.get("type")
    if nodeType is None:
        return None, []
    req = data.get("requirements", "")
    if req and not cmds.pluginInfo(req, loaded=True, query=True):
        try:
            cmds.loadPlugin(req)
        except RuntimeError:
            logger.error("Could not load plugin->{}".format(req), exc_info=True)
            return None, []

    if "parent" in data:
        newNode = createDagNode(nodeName, nodeType, parent)
    else:
        newNode = createDGNode(nodeName, nodeType)
    nodeName = nameFromMObject(newNode)
    plugList = om2.MSelectionList()
    createdAttributes = []
    for attrData in data.get("attributes", tuple()):
        name = attrData["name"]
        fullName = ".".join([nodeName, name])
        try:
            plugList.add(fullName)
            found = True
        except RuntimeError:
            found = False
        if found:
            try:
                plugs.setPlugInfoFromDict(plugList.getPlug(plugList.length() - 1), **attrData)
            except RuntimeError:
                logger.error("Failed to set plug data: {}".format(fullName), exc_info=True)
        else:
            children = attrData.get("children")
            if children:
                attr = addCompoundAttribute(newNode, name, name, attrMap=children, **attrData)
            else:
                attr = addAttribute(newNode, name, name, attrData["Type"], **attrData)
            createdAttributes.append(om2.MPlug(newNode, attr.object()))
    return newNode, createdAttributes


def setLockStateOnAttributes(node, attributes, state=True):
    """Locks and unlocks the given attributes

    :param node: the node that have its attributes locked
    :type node: MObject
    :param attributes: a list of attribute name to lock
    :type attributes: seq(str)
    :param state: True to lock and False to unlcck
    :type state: bool
    :return: True is successful
    :rtype: bool
    """
    dep = om2.MFnDependencyNode(node)
    for attr in attributes:
        plug = dep.findPlug(attr, False)
        if plug.isLocked != state:
            plug.isLocked = state
    return True


def showHideAttributes(node, attributes, state=True):
    """Shows or hides and attribute in the channelbox

    :param node: The MObject representing the DG node
    :type node: MObject
    :param attributes: attribute names on the given node
    :type attributes: seq(str)
    :param state: True for show False for hide, defaults to True
    :type state: bool
    :return: True if successful
    :rtype: bool
    """
    dep = om2.MFnDependencyNode(node)
    for attr in attributes:
        plug = dep.findPlug(attr, False)
        if plug.isChannelBox != state:
            plug.isChannelBox = state
    return True


def mirrorJoint(node, parent, translate, rotate, mirrorFunction=MIRROR_BEHAVIOUR):
    nFn = om2.MFnDependencyNode(node)
    rotateOrder = nFn.findPlug("rotateOrder", False).asInt()
    transMatRotateOrder = generic.intToMTransformRotationOrder(rotateOrder)
    translation, rotMatrix = mirrorTransform(node, parent, translate, rotate, mirrorFunction)  # MVector, MMatrix
    jointOrder = om2.MEulerRotation(plugs.getPlugValue(nFn.findPlug("jointOrient", False)))
    # deal with joint orient
    jo = om2.MTransformationMatrix().setRotation(jointOrder).asMatrixInverse()
    # applyRotation and translation
    rot = mayamath.toEulerFactory(rotMatrix * jo, transMatRotateOrder)
    setRotation(node, rot)
    setTranslation(node, translation)


def mirrorTransform(node, parent, translate, rotate, mirrorFunction=MIRROR_BEHAVIOUR):
    """ Mirror's the translation and rotation of a node relative to another unless the parent
    is specified as om2.MObject.kNullObj in which case world.

    :param node: the node transform the mirror
    :type node: om2.MObject
    :param parent: the parent Transform to mirror relative too.
    :type parent: om2.MObject or om2.MObject.kNullObj
    :param translate: the axis to mirror, can be one or more
    :type translate: tuple(str)
    :param rotate: "xy", "yz" or "xz"
    :type rotate: str
    :param mirrorFunction:
    :type mirrorFunction: int
    :return: mirrored translation vector and the mirrored rotation matrix
    :rtype: om2.MVector, om2.MMatrix
    """
    currentMat = getWorldMatrix(node)

    transMat = om2.MTransformationMatrix(currentMat)

    translation = transMat.translation(om2.MSpace.kWorld)
    if len(translate) == 3:
        translation *= -1
    else:
        for i in translate:
            translation[zoomath.AXIS[i]] *= -1
    transMat.setTranslation(translation, om2.MSpace.kWorld)
    # mirror the rotation on a plane
    quat = transMat.rotation(asQuaternion=True)
    # behavior
    if mirrorFunction == MIRROR_BEHAVIOUR:
        if rotate == "xy":
            newQuat = om2.MQuaternion(quat.y * -1, quat.x, quat.w, quat.z * -1)
        elif rotate == "yz":
            newQuat = om2.MQuaternion(quat.w * -1, quat.z, quat.y * -1, quat.x)
        else:
            newQuat = om2.MQuaternion(quat.z, quat.w, quat.x * -1, quat.y * -1)
    else:
        if rotate == "xy":
            quat.z *= -1
            quat.w *= -1
        elif rotate == "yz":
            quat.x *= -1
            quat.w *= -1
        else:
            quat.y *= -1
            quat.w *= -1
    transMat.setRotation(newQuat)
    rot = transMat.asRotateMatrix()

    # put the mirror rotationMat in the space of the parent
    if parent != om2.MObject.kNullObj:
        parentMatInv = getParentInverseMatrix(parent)
        rot *= parentMatInv

    return translation, om2.MTransformationMatrix(rot).rotation(asQuaternion=True)


def mirrorNode(node, parent, translate, rotate, mirrorFunction=MIRROR_BEHAVIOUR):
    translation, quat = mirrorTransform(node, parent, translate, rotate, mirrorFunction)  # MVector, MMatrix
    setRotation(node, quat)
    setTranslation(node, translation)


def matchTransformMulti(targetPaths, source, translation=True, rotation=True, scale=True, space=om2.MSpace.kWorld,
                        pivot=False):
    """Matches the transform(SRT) for a list of nodes to another node.

    :param targetPaths: A list om2.MDagPaths to snap to the source
    :type targetPaths: list(om2.MDagPath)
    :param source: The source transform node switch the target nodes will match
    :type source: om2.MObject
    :param translation: True to match translation
    :type translation: bool
    :param rotation: True to match rotation
    :type rotation: bool
    :param scale: True to match scale
    :type scale: bool
    :param space: coordinate space
    :type space: int
    :param pivot:
    :type pivot: True to match pivot
    :return: True if passed
    :rtype: bool
    """
    # get the proper matrix of source
    if space == om2.MSpace.kWorld:
        sourceMatrix = getWorldMatrix(source)
        srcTfm = om2.MTransformationMatrix(sourceMatrix)
    else:
        sourceMatrix = getMatrix(source)
        srcTfm = om2.MTransformtionMatrix(sourceMatrix)
        tfm = srcTfm
    # source pos
    pos = srcTfm.translation(space)

    # source pivot
    srcPivot = srcTfm.scalePivot(space)

    fn = om2.MFnTransform()
    for targetPath in targetPaths:
        targetNode = targetPath.node()
        fn.setObject(targetNode)
        if space != om2.MSpace.kWorld:
            invParent = getParentInverseMatrix(targetNode)
            tfm = om2.MTransformationMatrix(sourceMatrix * invParent)
        # rotation
        rot = tfm.rotation()
        # scale
        scl = tfm.scale(space)
        # set Scaling
        if scale:
            fn.setScale(scl)
        # set Rotation
        if rotation:
            fn.setRotation(rot, om2.MSpace.kTransform)
        # set Translation
        if translation:
            if pivot:
                nodePivot = fn.scalePivot(space)
                pos += srcPivot - nodePivot
            fn.setTranslation(pos, space)
    return True


def matchTransformSingle(targetPath, source, translation=True, rotation=True, scale=True, space=om2.MSpace.kWorld,
                         pivot=False):
    """Matches the transform(SRT) for a list of nodes to another node.

    :param targetPath: om2.MDagPath to snap to the source
    :type targetPath: om2.MDagPath
    :param source: The source transform node switch the target nodes will match
    :type source: om2.MObject
    :param translation: True to match translation
    :type translation: bool
    :param rotation: True to match rotation
    :type rotation: bool
    :param scale: True to match scale
    :type scale: bool
    :param space: coordinate space
    :type space: int
    :param pivot:
    :type pivot: True to match pivot
    :return: True if passed
    :rtype: bool
    """
    targetNode = targetPath.node()
    # get the proper matrix of source
    if space == om2.MSpace.kWorld:
        sourceMatrix = getWorldMatrix(source)
        srcTfm = om2.MTransformationMatrix(sourceMatrix)
        # multiply the global scale and rotation by the nodes parent inverse world matrix to get local rot & scl
        invParent = getParentInverseMatrix(targetNode)
        tfm = om2.MTransformationMatrix(sourceMatrix * invParent)
    else:
        srcTfm = om2.MTransformtionMatrix(getMatrix(source))
        tfm = srcTfm
    # source pos
    pos = srcTfm.translation(space)

    # source pivot
    srcPivot = srcTfm.scalePivot(space)

    # rotation
    rot = tfm.rotation()
    # scale
    scl = tfm.scale(space)
    fn = om2.MFnTransform(targetPath)
    # set Scaling
    if scale:
        fn.setScale(scl)
    # set Rotation
    if rotation:
        fn.setRotation(rot, om2.MSpace.kTransform)
    # set Translation
    if translation:
        if pivot:
            nodePivot = fn.scalePivot(space)
            pos += srcPivot - nodePivot
        fn.setTranslation(pos, space)
    return True


def swapOutgoingConnections(source, destination, plugs=None):
    """
    :param source: The source node to transfer connections from
    :param destination: The destination node to transfer connections to.
    :param plugs: plug list to to swap, if None is used then all connections will be swapped
    :rtype: om2.modifier the maya modifier which will require you to call doIt()

    .. todo:: deal with selected child attributes when only the compound is selected
    """
    plugs = plugs or []
    destFn = om2.MFnDependencyNode(destination)
    mod = om2.MDGModifier()
    for sourcePlug, destinationPlug in iterConnections(source, True, False):
        if plugs and sourcePlug not in plugs:
            continue
        name = sourcePlug.partialName(includeNonMandatoryIndices=True, useLongNames=True,
                                      includeInstancedIndices=True)

        if not destFn.hasAttribute(name):
            continue
        targetPlug = destFn.findPlug(sourcePlug.attribute(), False)
        if destinationPlug.isLocked:
            destinationPlug.isLocked = False
        mod.disconnect(sourcePlug, destinationPlug)
        mod.connect(targetPlug, destinationPlug)

    return mod
