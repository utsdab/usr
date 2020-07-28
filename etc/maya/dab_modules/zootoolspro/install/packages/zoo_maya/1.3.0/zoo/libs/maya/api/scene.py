import contextlib
from contextlib import contextmanager

from zoovendor.six.moves import range

from maya.api import OpenMaya as om2

from zoo.libs.maya.api import nodes, plugs, curves
from zoo.libs.maya.utils import mayamath


def removeFromActiveSelection(node):
    """remove the node from the selection forcefully
    Otherwise maya can crash if someone deletes that node afterwards"""

    currentSelectionList = om2.MGlobal.getActiveSelectionList()
    newList = om2.MSelectionList()
    for i in range(currentSelectionList.length()):
        try:
            currentNode = currentSelectionList.getDagPath(i).node()
        except TypeError:
            currentNode = currentSelectionList.getDependNode(i)
        if currentNode != node:
            newList.add(currentNode)
    om2.MGlobal.setActiveSelectionList(newList, om2.MGlobal.kReplaceList)


def getSelectedNodes(filter=None):
    """Returns the selected nodes

    :return: list(MObject)
    """
    return list(iterSelectedNodes(filter))


def iterSelectedNodes(filter=None):
    sel = om2.MGlobal.getActiveSelectionList()
    for i in range(sel.length()):
        no = sel.getDependNode(i)
        if no.apiType() == filter or not filter:
            yield no


@contextmanager
def keepSelection():
    sel = om2.MSelectionList()
    om2.MGlobal.getActiveSelectionList(sel)
    try:
        yield
    finally:
        om2.MGlobal.setActiveSelectionList(sel)


def getNodesCreatedBy(function, *args, **kwargs):
    """returns a 2-tuple containing all the nodes created by the passed function, and
    the return value of said function

    :param function: func, the function to call and inspect
    :rtype: tuple(MObject)
    """

    # construct the node created callback
    newNodeHandles = []

    def newNodeCB(newNode, data):

        newNodeHandles.append(om2.MObjectHandle(newNode))

    def remNodeCB(remNode, data):
        remNodeHandle = om2.MObjectHandle(remNode)
        if remNodeHandle in newNodeHandles:
            newNodeHandles.remove(remNodeHandle)

    newNodeCBMsgId = om2.MDGMessage.addNodeAddedCallback(newNodeCB, "dependNode")
    remNodeCBMsgId = om2.MDGMessage.addNodeRemovedCallback(remNodeCB, "dependNode")
    try:
        ret = function(*args, **kwargs)
    finally:
        om2.MMessage.removeCallback(newNodeCBMsgId)
        om2.MMessage.removeCallback(remNodeCBMsgId)

    newNodes = [h.object() for h in newNodeHandles]

    return newNodes, ret


def iterDag(root, includeRoot=True, nodeType=None):
    """Generator function to walk the node hierarchy, if a nodeType is provided then the function will only return
    that mobject apitype.

    :param root: the root dagnode to loop
    :type root: MObject
    :param includeRoot: if true include the root mobject
    :type includeRoot: bool
    :param nodeType: defaults to none which will return everything an example user specified type om2.MFn.kTransform
    :type nodeType: int
    :return: yields the mobject
    :rtype: Generator(mobject)
    """
    stack = [om2.MFnDagNode(root)]
    if includeRoot:
        yield stack[0].object()

    while stack:
        child = stack.pop(0)
        children = child.childCount()
        if children > 0:
            for i in range(children):
                subChild = child.child(i)
                stack.append(om2.MFnDagNode(subChild))
                if nodeType is not None and subChild.apiType() != nodeType:
                    continue
                yield subChild


def worldPositionToScreen(camera, point, width, height):
    cam = om2.MFnCamera(camera)

    transMat = cam.getPath().inclusiveMatrix().inverse()

    fullMat = om2.MPoint(point) * transMat * om2.MMatrix(cam.projectionMatrix().matrix())
    return [(fullMat[0] / fullMat[3] * 0.5 + 0.5) * width,
            (fullMat[1] / fullMat[3] * 0.5 + 0.5) * height]


def isPointInView(camera, point, width, height):
    x, y = worldPositionToScreen(camera, point, width, height)
    if x > width or x < 0.0 or y > height or y < 0.0:
        return False
    return True


def serializeNodes(graphNodes, skipAttributes=None, includeConnections=True):
    rawData = {}
    for n in graphNodes:
        nData = nodes.serializeNode(n)
        curveData = None
        if n.mobject().hasFn(om2.MFn.kDagNode):
            curveData = curves.serializeCurve(n, skipAttributes, includeConnections)
        if curveData:
            nData["shape"] = curveData
        rawData[nData["name"]] = nData

    return rawData


def serializeSelectedNodes(skipAttributes, includeConnections):
    selNodes = getSelectedNodes()
    if selNodes:
        return serializeNodes(selNodes, skipAttributes=skipAttributes, includeConnections=includeConnections)
    return {}


def deserializeNodes(data):
    createNodes = []
    for n in iter(data):
        newNode = nodes.deserializeNode(n)
        if newNode:
            createNodes.append(newNode)
    return createNodes


class GraphDeserializer(dict):

    def __init__(self, data):
        super(GraphDeserializer, self).__init__(data)
        self.results = {}

    def process(self, nodeMap):
        """
        :param nodeMap: {nodeName: om2.MObject}
        :type nodeMap: dict
        :return:
        :rtype:
        """
        self.results.update(nodeMap)
        createdNodes = []
        connections = []
        for k, n in self.items():
            # skip any currently processed nodes.
            newNode = self.results.get(k)
            if newNode is None:
                parent = n.get("parent")
                parentNode = None
                # if we have a parentNode that means we're a Dag node, so try to resolve the parent,
                if parent:
                    parentNode = self.results.get(parent)
                    # if we have come across the parent before it should already have been process so skip
                    if parentNode is None and parent in self:
                        # ok in this case we have visited the parent so process it
                        parentData = self[parent]
                        parentNode, attrs = nodes.deserializeNode(parentData,
                                                                  self.results.get(self[parent]["parent"]))
                        createdNodes.append(parentNode)
                        self.results[parent] = parentNode
                        connections.extend(parentData.get("connections", []))

                newNode, attrs = nodes.deserializeNode(n, parentNode)
                if not newNode:
                    continue
                createdNodes.append(newNode)
                self.results[k] = newNode
            # remap the connection destination and destinationPlug to be the current node plus plug
            currentConnections = n.get("connections", [])
            for conn in currentConnections:
                conn["destination"] = newNode
                conn["destinationPlug"] = ".".join([nodes.nameFromMObject(newNode), conn["destinationPlug"]])
            if not currentConnections:
                continue
            connections.extend(currentConnections)
        if connections:
            for conn in connections:
                if conn["source"] in self.results:
                    conn["source"] = self.results[conn["source"]]
                source = conn["source"]
                if isinstance(conn["source"], om2.MObject):
                    source = nodes.nameFromMObject(conn["source"])
                conn["sourcePlug"] = ".".join([source, conn["sourcePlug"]])
            self._deserializeConnections(connections)
        return createdNodes

    def _deserializeConnections(self, connections):
        # plugList = om2.MSelectionList()
        for conn in connections:
            sourceNode = conn["source"]
            destinationNode = conn["destination"]
            if sourceNode is None or destinationNode is None:
                continue
            # connect the source and destination plug
            try:
                sourcePlug = plugs.asMPlug(conn["sourcePlug"])
                destinationPlug = plugs.asMPlug(conn["destinationPlug"])
                if destinationPlug.isDestination:
                    continue
                with contextlib.nested(plugs.setLockedContext(sourcePlug),
                                       plugs.setLockedContext(destinationPlug)):
                    plugs.connectPlugs(sourcePlug,
                                       destinationPlug,
                                       force=False)
            except RuntimeError:
                continue


def aimNodes(targetNode, driven, aimVector=None,
             upVector=None):
    for i in iter(driven):
        children = []
        for child in list(nodes.iterChildren(i, False, (om2.MFn.kTransform, om2.MFn.kJoint))):
            nodes.setParent(child, None, True)
            children.append(child)
        mayamath.aimToNode(i, targetNode, aimVector, upVector)

        for child in iter(children):
            nodes.setParent(child, i, True)


def aimSelected(aimVector=None,
                upVector=None):
    """Aim the the selected nodes to the last selected node.

    :param aimVector: see mayamath.aimToNode for details
    :type aimVector: om2.MVector
    :param upVector: see mayamath.aimToNode for details
    :type upVector: om2.MVector
    """
    selected = getSelectedNodes()
    if len(selected) < 2:
        raise ValueError("Please Select more than 2 nodes")
    target = selected[-1]  # driver
    toAim = selected[:-1]  # driven

    aimNodes(target, toAim, aimVector=aimVector, upVector=upVector)


def dgIterator(*args, **kwargs):
    """ A more ideal python DGIterator for maya, this function just wraps the iterator in a try/finally statement
    so that we dont need to call iterator.next().
    See maya.api.OpenMaya.MItDependencyGraph documentation for the arguments

    :rtype: Generator(om2.MItDependencyGraph)

    .. code-block:: python

        mesh = asMObject("pCube1")
        for dgIter in dgIterator(mesh, om2.MFn.kSkinClusterFilter, om2.MItDependencyGraph.kUpstream):
            dgIter.currentNode()

    """
    iterator = om2.MItDependencyGraph(*args, **kwargs)
    while not iterator.isDone():
        try:
            yield iterator
        finally:
            iterator.next()


def iterReferences():
    """Generator function that returns a Mobject for each valid referene node.

    :return: Generator function with each element representing the reference node
    :rtype: Generator(om2.MObject)
    """
    iterator = om2.MItDependencyNodes(om2.MFn.kReference)

    while not iterator.isDone():
        try:
            fn = om2.MFnReference(iterator.thisNode())
            try:
                if not fn.isLoaded() or fn.isLocked():
                    continue
            except RuntimeError:
                continue
            yield fn.object()
        finally:
            iterator.next()

