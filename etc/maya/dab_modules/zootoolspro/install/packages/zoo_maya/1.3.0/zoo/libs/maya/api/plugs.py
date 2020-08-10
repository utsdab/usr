import copy
import re
import contextlib

from zoovendor.six.moves import range

from maya.api import OpenMaya as om2

from zoo.libs.maya.api import attrtypes
from zoo.libs.utils import zlogging

logger = zlogging.getLogger(__name__)

AXIS = ("X", "Y", "Z")


def asMPlug(name):
    """Returns the MPlug instance for the given name

    :param name: The mobject to convert to MPlug
    :rtype name: str
    :return: MPlug, or None
    """
    try:
        names = name.split(".")
        sel = om2.MSelectionList()
        sel.add(names[0])
        node = om2.MFnDependencyNode(sel.getDependNode(0))
        return node.findPlug(".".join(names[1:]), False)
    except RuntimeError:
        sel = om2.MSelectionList()
        sel.add(str(name))
        return sel.getPlug(0)


def connectPlugs(source, destination, mod=None, force=True):
    """Connects two MPlugs together

    :type source: MObject
    :type destination: MObject
    :type mod: om2.MDGModifier()
    """

    _mod = mod or om2.MDGModifier()

    if destination.isDestination:
        destinationSource = destination.source()
        if force:
            _mod.disconnect(destinationSource, destination)
        else:
            raise ValueError("Plug {} has incoming connection {}".format(destination.name(), destinationSource.name()))
    _mod.connect(source, destination)
    if mod is None:
        _mod.doIt()
    return _mod


def connectVectorPlugs(sourceCompound, destinationCompound, connectionValues, force=True, modifier=None):
    """

    :param sourceCompound:
    :type sourceCompound: om2.MPlug
    :param destinationCompound:
    :type destinationCompound: om2.MPlug
    :param connectionValues: Bool value for each axis if all axis are tre then just connect the compound
    :type connectionValues: seq(str)

    :rtype: :class:`om2.MDGModifier`

    """
    if all(connectionValues):
        connectPlugs(sourceCompound, destinationCompound, mod=modifier, force=force)
        return
    childCount = destinationCompound.numChildren()
    sourceCount = sourceCompound.numChildren()
    requestLength = len(connectionValues)
    if childCount < requestLength or sourceCount < requestLength:
        raise ValueError("ConnectionValues arg count is larger then the compound child count")

    mod = modifier or om2.MDGModifier()
    for i in range(len(connectionValues)):
        value = connectionValues[i]
        childSource = sourceCompound.child(i)
        childDest = destinationCompound.child(i)
        if not value:
            if childDest.isDestination:
                disconnectPlug(childDest.source(), childDest)
            continue
        connectPlugs(childSource, childDest, mod=mod, force=force)
    mod.doIt()
    return mod


def disconnectPlug(plug, source=True, destination=True, modifier=None):
    """Disconnect the plug connections, if 'source' is True and the 'plug' is a destination then disconnect the source
    from this plug. If 'destination' True and plug is a source then disconnect this plug from the destination.
    This function will also lock the plugs otherwise maya raises an error

    :param plug: the plug to disconnect
    :type plug: om2.MPlug
    :param source: if true disconnect from the connected source plug if it has one
    :type source: bool
    :param destination: if true disconnect from the connected destination plug if it has one
    :type destination: bool
    :return: True if succeed with the disconnection
    :rtype: bool
    :raises: maya api error
    """
    if plug.isLocked:
        plug.isLocked = False
    mod = modifier or om2.MDGModifier()
    if source and plug.isDestination:
        sourcePlug = plug.source()
        if sourcePlug.isLocked:
            sourcePlug.isLocked = False
        mod.disconnect(sourcePlug, plug)
    if destination and plug.isSource:
        for conn in plug.destinations():
            if conn.isLocked:
                conn.isLocked = False
            mod.disconnect(plug, conn)
    if not modifier:
        mod.doIt()
    return True, mod


def removeElementPlug(plug, elementNumber, mod=None, apply=False):
    """Functional wrapper for removing a element plug(multiinstance)

    :param plug: The plug array object
    :type plug: om2.MPlug
    :param elementNumber: the element number
    :type elementNumber: int
    :param mod: If None then a om2.MDGModifier object will be created and returned else the one thats passed will be used.
    :type mod: om2.MDGModifier or None
    :param apply: If False then mod.doIt() will not be called, it is the clients reponsiblity to call doIt,
                useful for batch operations.
    :type apply: bool
    :return: The MDGModifier instance which contains the operation stack.
    :rtype: om2.MDGModifier
    """
    # keep the compound plug unlocked for elements to be deleted
    with setLockedContext(plug):
        mod = mod or om2.MDGModifier()
        # make sure the client has passed an invalid elementIndex.
        if elementNumber in plug.getExistingArrayAttributeIndices():
            # add the op to the stack and let maya handle connections for us.
            mod.removeMultiInstance(plug.elementByLogicalIndex(elementNumber), True)
        # allow the user to batch delete elements if apply is False, this is more efficient.
        if apply:
            try:
                mod.doIt()
            except RuntimeError:
                logger.error("Failed to remove element: {} from plug: {}".format(str(elementNumber), plug.name()),
                             exc_info=True)
                raise
    return mod


def removeUnConnectedEmptyElements(plugArray, mod=None):
    """Removes all unconnected array plug elements.

    This works by iterating through all plug elements and checking the isConnected flag, if
    the element plug is a compound then we can the children too.

    :note: currently one handles two dimensional arrays
    ie.
        |- element_compound
            |- child


    :param plugArray: The plug array instance
    :type plugArray: om2.MPlug
    :param mod: If passed then this modifier will be used instead of creating a new one
    :type mod: om2.MDGModfier or None
    :return: The MDGModifier instance, if one is passed in the mod argument then that will be \
    returned.
    :rtype: om2.MDGModifier
    """
    mod = mod or om2.MDGModifier()
    # separate out the logic so we reduce one condition per iteration.
    # an array can't be both a compound and singleton so handle them separately
    if plugArray.isCompound:
        for element in plugArray.getExistingArrayAttributeIndices():
            for childI in range(element.numChildren()):
                if element.child(childI).isConnected:
                    break
        else:
            mod.removeMultiInstance(element, True)
    else:
        for element in plugArray.getExistingArrayAttributeIndices():
            if not element.isConnected:
                mod.removeMultiInstance(element, True)
    mod.doIt()
    return mod


def isValidMPlug(plug):
    """Checks whether the MPlug is valid in the scene

    :param plug: OpenMaya.MPlug
    :return: bool
    """
    return True if not plug.isNull else False


@contextlib.contextmanager
def setLockedContext(plug):
    """Context manager to set the 'plug' lock state to False then reset back to what the state was at the end

    :param plug: the MPlug to work on
    :type plug: om2.MPlug
    """
    current = plug.isLocked
    if current:
        plug.isLocked = False
    yield
    plug.isLocked = current


def setLockState(plug, state):
    """Sets the 'plug' lock state

    :param plug: the Plug to work on.
    :type plug: om2.MPlug
    :param state: False to unlock , True to lock.
    :type state: bool
    :return: True if the operation succeeded.
    :rtype: bool
    """
    if plug.isLocked != state:
        plug.isLocked = state
        return True
    return False


def filterConnected(plug, filter):
    """Filters all connected plugs by name using a regex with the `filter` argument. The filter is applied to the plugs
    connected plug eg. if nodeA.translateX is connected to nodeB.translateX  and this func is used on nodeA.translateX
    then nodeB.translateX will have the filter applied to the plug.name()
    :param plug: The plug to search the connections from.
    :type plug: om2.MPlug
    :param filter: the regex string
    :type filter: str
    :rtype: iterable(om2.MPlug)
    """
    if not plug.isConnected:
        return list()

    filteredNodes = []
    for connected in plug.connectedTo(False, True) + plug.connectedTo(True, False):
        grp = re.search(filter, connected.name())
        if grp:
            filteredNodes.append(connected)
    return filteredNodes


def filterConnectedNodes(plug, filter, source=True, destination=False):
    filteredNodes = []
    if (source and not plug.isSource) or (destination and not plug.isDestination):
        return []
    destinations = []
    if destination and plug.isDestination:
        destinations.extend(plug.connectedTo(False, True))
    if source and plug.isSource:
        destinations.extend(plug.connectedTo(True, False))
    for connected in destinations:
        node = connected.node()
        if node.hasFn(om2.MFn.kDagNode):
            dep = om2.MFnDagNode(node)
            name = dep.fullPathName()
        else:
            dep = om2.MFnDependencyNode(node)
            name = dep.name()
        grp = re.search(filter, name)
        if grp:
            filteredNodes.append(connected)
    return filteredNodes


def iterDependencyGraph(plug, alternativeName="", depthLimit=256, transverseType="down"):
    """This recursive function walks the dependency graph based on the name. so each node it visits if that attribute
    exists it will be return.
    example connections : nodeA.test -> nodeB.test -> nodeC.test
    [nodeA,nodeB, nodeC] will be return as a generator

    :param plug:
    :type plug: om2.MPlug
    :param alternativeName:
    :type alternativeName: str
    :param depthLimit:
    :type depthLimit: int
    :return:
    :rtype: generator(MObject)
    """

    plugSearchname = alternativeName or plug.partialName(useLongNames=True)
    if transverseType == "down":
        connections = plug.destinations()
    else:
        connections = [plug.source()]
    for connection in connections:
        node = connection.node()
        dep = om2.MFnDependencyNode(node)
        if not dep.hasAttribute(plugSearchname):
            continue
        nodePlug = dep.findPlug(plugSearchname, False)
        if depthLimit < 1:
            return
        yield nodePlug
        if nodePlug.isConnected:
            for i in iterDependencyGraph(nodePlug, plugSearchname, depthLimit=depthLimit - 1,
                                         transverseType=transverseType):
                yield i


def serializePlug(plug):
    """Take's a plug and serializes all necessary information into a dict.

    Return data is in the form::

        {name: str, "isDynamic": bool, "default": type, "min": type, "max": type, "softMin": type, "softMax": type}

    :param plug: the valid MPlug to serialize
    :type plug: MPlug
    :return: with out connection data.
    :rtype: dict
    """
    data = {"isDynamic": plug.isDynamic}
    attrType = plugType(plug)
    if not plug.isDynamic:

        # skip any default attribute that hasn't changed value, this could be a tad short sighted since other state
        # options can change, also skip array attributes since we still pull the elements if the value has changed
        if plug.isDefaultValue() or plug.isArray:
            return {}
        elif plug.isCompound:
            data["children"] = [serializePlug(plug.child(i)) for i in range(plug.numChildren())]
    elif attrType != attrtypes.kMFnMessageAttribute:
        if plug.isDefaultValue() or plug.isArray:
            data["children"] = []
        elif plug.isCompound:
            data["children"] = [serializePlug(plug.child(i)) for i in range(plug.numChildren())]
        else:
            data.update({"min": mayaTypeToPythonType(getPlugMin(plug)),
                         "max": mayaTypeToPythonType(getPlugMax(plug)),
                         "softMin": mayaTypeToPythonType(getSoftMin(plug)),
                         "softMax": mayaTypeToPythonType(getSoftMax(plug)),
                         }
                        )

    data.update({"name": plug.partialName(includeNonMandatoryIndices=True, useLongNames=True,
                                          includeInstancedIndices=True),
                 "channelBox": plug.isChannelBox,
                 "keyable": plug.isKeyable,
                 "locked": plug.isLocked,
                 "isArray": plug.isArray,
                 "default": mayaTypeToPythonType(plugDefault(plug)),
                 "Type": attrType,
                 "value": getPythonTypeFromPlugValue(plug),
                 })

    if plugType(plug) == attrtypes.kMFnkEnumAttribute:
        data["enums"] = enumNames(plug)
    return data


def serializeConnection(plug):
    """Take's destination om2.MPlug and serializes the connection as a dict.

    :param plug: A om2.MPlug that is the destination of a connection
    :type plug: om2.MPlug
    :return: {sourcePlug: str,
              destinationPlug: str,
              source: str, # source node
              destination: str} # destination node

    :rtype: dict
    """
    source = plug.source()
    sourceNPath = ""
    if source:
        sourceN = source.node()
        sourceNPath = om2.MFnDagNode(sourceN).fullPathName() if sourceN.hasFn(
            om2.MFn.kDagNode) else om2.MFnDependencyNode(sourceN).name()
    destN = plug.node()
    return {"sourcePlug": source.partialName(includeNonMandatoryIndices=True, useLongNames=True,
                                             includeInstancedIndices=True),
            "destinationPlug": plug.partialName(includeNonMandatoryIndices=True, useLongNames=True,
                                                includeInstancedIndices=True),
            "source": sourceNPath,
            "destination": om2.MFnDagNode(destN).fullPathName() if destN.hasFn(om2.MFn.kDagNode) else
            om2.MFnDependencyNode(destN).name()}


def enumNames(plug):
    """Returns the 'plug' enumeration field names.

    :param plug: the MPlug to query
    :type plug: om2.MPlug
    :return: A sequence of enum names
    :rtype: list(str)
    """
    obj = plug.attribute()
    enumoptions = []
    if obj.hasFn(om2.MFn.kEnumAttribute):
        attr = om2.MFnEnumAttribute(obj)
        min = attr.getMin()
        max = attr.getMax()
        for i in range(min, max + 1):
            # enums can be a bit screwed, i.e 5 options but max 10
            try:
                enumoptions.append(attr.fieldName(i))
            except:
                pass
    return enumoptions


def enumIndices(plug):
    """Returns the 'plug' enums indices as a list.

    :param plug: The MPlug to query
    :type plug: om2.MPlug
    :return: a sequence of enum indices
    :rtype: list(int)
    """
    obj = plug.attribute()
    if obj.hasFn(om2.MFn.kEnumAttribute):
        attr = om2.MFnEnumAttribute(obj)
        return range(attr.getMax() + 1)


def plugDefault(plug):
    obj = plug.attribute()
    if obj.hasFn(om2.MFn.kNumericAttribute):
        attr = om2.MFnNumericAttribute(obj)
        if attr.numericType() == om2.MFnNumericData.kInvalid:
            return None
        return attr.default
    elif obj.hasFn(om2.MFn.kTypedAttribute):
        attr = om2.MFnTypedAttribute(obj)
        default = attr.default
        if default.apiType() == om2.MFn.kInvalid:
            return None
        elif default.apiType() == om2.MFn.kStringData:
            return om2.MFnStringData(default).string()
        return default
    elif obj.hasFn(om2.MFn.kUnitAttribute):
        attr = om2.MFnUnitAttribute(obj)
        return attr.default
    elif obj.hasFn(om2.MFn.kMatrixAttribute):
        attr = om2.MFnMatrixAttribute(obj)
        return attr.default
    elif obj.hasFn(om2.MFn.kEnumAttribute):
        attr = om2.MFnEnumAttribute(obj)
        return attr.default
    return None


def setPlugDefault(plug, default):
    obj = plug.attribute()
    if obj.hasFn(om2.MFn.kNumericAttribute):
        attr = om2.MFnNumericAttribute(obj)
        Type = attr.numericType()
        attr.default = tuple(default) if Type in (om2.MFnNumericData.k2Double, om2.MFnNumericData.k3Double,
                                                  om2.MFnNumericData.k4Double) else default
        return True
    elif obj.hasFn(om2.MFn.kTypedAttribute):
        if not isinstance(default, om2.MObject):
            raise ValueError(
                "Wrong type passed to MFnTypeAttribute must be on type MObject, received : {}".format(type(default)))
        attr = om2.MFnTypedAttribute(obj)
        attr.default = default
        return True
    elif obj.hasFn(om2.MFn.kUnitAttribute):
        if not isinstance(default, (om2.MAngle, om2.MDistance, om2.MTime)):
            raise ValueError(
                "Wrong type passed to MFnUnitAttribute must be on type MAngle,MDistance or MTime, received : {}".format(
                    type(default)))
        attr = om2.MFnUnitAttribute(obj)
        attr.default = default
        return True
    elif obj.hasFn(om2.MFn.kMatrixAttribute):
        attr = om2.MFnMatrixAttribute(obj)
        attr.default = default
        return True
    elif obj.hasFn(om2.MFn.kEnumAttribute):
        if not isinstance(default, (int, str)):
            raise ValueError(
                "Wrong type passed to MFnEnumAttribute must be on type int or float, received : {}".format(
                    type(default)))
        attr = om2.MFnEnumAttribute(obj)
        if isinstance(default, int):
            attr.default = default
        else:
            attr.setDefaultByName(default)
        return True
    return False


def hasPlugMin(plug):
    obj = plug.attribute()
    if obj.hasFn(om2.MFn.kNumericAttribute):
        attr = om2.MFnNumericAttribute(obj)
        return attr.hasMin()
    elif obj.hasFn(om2.MFn.kUnitAttribute):
        attr = om2.MFnUnitAttribute(obj)
        return attr.hasMin()
    elif obj.hasFn(om2.MFn.kEnumAttribute):
        attr = om2.MFnEnumAttribute(obj)
        return attr.hasMin()
    return False


def hasPlugMax(plug):
    obj = plug.attribute()
    if obj.hasFn(om2.MFn.kNumericAttribute):
        attr = om2.MFnNumericAttribute(obj)
        return attr.hasMax()
    elif obj.hasFn(om2.MFn.kUnitAttribute):
        attr = om2.MFnUnitAttribute(obj)
        return attr.hasMax()
    elif obj.hasFn(om2.MFn.kEnumAttribute):
        attr = om2.MFnEnumAttribute(obj)
        return attr.hasMax()
    return False


def hasPlugSoftMin(plug):
    obj = plug.attribute()
    if obj.hasFn(om2.MFn.kNumericAttribute):
        attr = om2.MFnNumericAttribute(obj)
        return attr.hasSoftMin()
    elif obj.hasFn(om2.MFn.kUnitAttribute):
        attr = om2.MFnUnitAttribute(obj)
        return attr.hasSoftMin()
    elif obj.hasFn(om2.MFn.kEnumAttribute):
        attr = om2.MFnEnumAttribute(obj)
        return attr.hasSoftMin()
    return False


def hasPlugSoftMax(plug):
    obj = plug.attribute()
    if obj.hasFn(om2.MFn.kNumericAttribute):
        attr = om2.MFnNumericAttribute(obj)
        return attr.hasSoftMin()
    elif obj.hasFn(om2.MFn.kUnitAttribute):
        attr = om2.MFnUnitAttribute(obj)
        return attr.hasSoftMin()
    elif obj.hasFn(om2.MFn.kEnumAttribute):
        attr = om2.MFnEnumAttribute(obj)
        return attr.hasSoftMin()
    return False


def getPlugMin(plug):
    obj = plug.attribute()
    if obj.hasFn(om2.MFn.kNumericAttribute):
        attr = om2.MFnNumericAttribute(obj)
        if attr.hasMin():
            return attr.getMin()
    elif obj.hasFn(om2.MFn.kUnitAttribute):
        attr = om2.MFnUnitAttribute(obj)
        if attr.hasMin():
            return attr.getMin()
    elif obj.hasFn(om2.MFn.kEnumAttribute):
        attr = om2.MFnEnumAttribute(obj)
        return attr.getMin()


def getPlugMax(plug):
    obj = plug.attribute()
    if obj.hasFn(om2.MFn.kNumericAttribute):
        attr = om2.MFnNumericAttribute(obj)
        if attr.hasMax():
            return attr.getMax()
    elif obj.hasFn(om2.MFn.kUnitAttribute):
        attr = om2.MFnUnitAttribute(obj)
        if attr.hasMax():
            return attr.getMax()
    elif obj.hasFn(om2.MFn.kEnumAttribute):
        attr = om2.MFnEnumAttribute(obj)
        return attr.getMax()


def getSoftMin(plug):
    obj = plug.attribute()
    if obj.hasFn(om2.MFn.kNumericAttribute):
        attr = om2.MFnNumericAttribute(obj)
        if attr.hasSoftMin():
            return attr.getSoftMin()
    elif obj.hasFn(om2.MFn.kUnitAttribute):
        attr = om2.MFnUnitAttribute(obj)
        if attr.hasSoftMin():
            return attr.getSoftMin()


def setSoftMin(plug, value):
    obj = plug.attribute()
    if obj.hasFn(om2.MFn.kNumericAttribute):
        attr = om2.MFnNumericAttribute(obj)
        attr.setSoftMin(value)
        return True
    elif obj.hasFn(om2.MFn.kUnitAttribute):
        attr = om2.MFnUnitAttribute(obj)
        attr.setSoftMin(value)
        return True
    return False


def getSoftMax(plug):
    obj = plug.attribute()
    if obj.hasFn(om2.MFn.kNumericAttribute):
        attr = om2.MFnNumericAttribute(obj)
        if attr.hasSoftMax():
            return attr.getSoftMax()
    elif obj.hasFn(om2.MFn.kUnitAttribute):
        attr = om2.MFnUnitAttribute(obj)
        if attr.hasSoftMax():
            return attr.getSoftMax()


def setSoftMax(plug, value):
    obj = plug.attribute()
    if obj.hasFn(om2.MFn.kNumericAttribute):
        attr = om2.MFnNumericAttribute(obj)
        attr.setSoftMax(value)
        return True
    elif obj.hasFn(om2.MFn.kUnitAttribute):
        attr = om2.MFnUnitAttribute(obj)
        attr.setSoftMax(value)
        return True
    return False


def setMin(plug, value):
    obj = plug.attribute()
    if obj.hasFn(om2.MFn.kNumericAttribute):
        attr = om2.MFnNumericAttribute(obj)
        attr.setMin(value)
        return True
    elif obj.hasFn(om2.MFn.kUnitAttribute):
        attr = om2.MFnUnitAttribute(obj)
        attr.setMin(value)
        return True
    return False


def setMax(plug, value):
    obj = plug.attribute()
    if obj.hasFn(om2.MFn.kNumericAttribute):
        attr = om2.MFnNumericAttribute(obj)
        attr.setMax(value)
        return True
    elif obj.hasFn(om2.MFn.kUnitAttribute):
        attr = om2.MFnUnitAttribute(obj)
        attr.setMax(value)
        return True
    return False


def getPlugValue(plug):
    return getPlugAndType(plug)[1]


def getPlugAndType(plug):
    """Given an MPlug, get its value

    :param plug: MPlug
    :return: the dataType of the given plug. Will return standard python types where necessary eg. float else maya type
    :rtype: tuple(int, plugValue)
    """
    obj = plug.attribute()

    if plug.isArray:
        count = plug.evaluateNumElements()
        res = [None] * count, [None] * count
        data = [getPlugAndType(plug.elementByPhysicalIndex(i)) for i in range(count)]
        for i in range(len(data)):
            res[0][i] = data[i][0]
            res[1][i] = data[i][1]
        return res

    if obj.hasFn(om2.MFn.kNumericAttribute):
        return getNumericValue(plug)

    elif obj.hasFn(om2.MFn.kUnitAttribute):
        uAttr = om2.MFnUnitAttribute(obj)
        ut = uAttr.unitType()
        if ut == om2.MFnUnitAttribute.kDistance:
            return attrtypes.kMFnUnitAttributeDistance, plug.asMDistance()
        elif ut == om2.MFnUnitAttribute.kAngle:
            return attrtypes.kMFnUnitAttributeAngle, plug.asMAngle()
        elif ut == om2.MFnUnitAttribute.kTime:
            return attrtypes.kMFnUnitAttributeTime, plug.asMTime()
    elif obj.hasFn(om2.MFn.kEnumAttribute):
        return attrtypes.kMFnkEnumAttribute, plug.asInt()
    elif obj.hasFn(om2.MFn.kTypedAttribute):
        return getTypedValue(plug)
    elif obj.hasFn(om2.MFn.kMessageAttribute):
        return attrtypes.kMFnMessageAttribute, None

    elif obj.hasFn(om2.MFn.kMatrixAttribute):
        return attrtypes.kMFnDataMatrix, om2.MFnMatrixData(plug.asMObject()).matrix()

    if plug.isCompound:
        count = plug.numChildren()
        res = [None] * count, [None] * count
        data = [getPlugAndType(plug.child(i)) for i in range(count)]
        for i in range(len(data)):
            res[0][i] = data[i][0]
            res[1][i] = data[i][1]
        return res

    return None, None


def getNumericValue(plug):
    """Returns the maya numeric type and value from the given plug

    :param plug: The plug to get the value from
    :type plug: om2.MPlug
    :rtype: attrtypes.kType,
    """
    obj = plug.attribute()
    nAttr = om2.MFnNumericAttribute(obj)
    dataType = nAttr.numericType()
    if dataType == om2.MFnNumericData.kBoolean:
        return attrtypes.kMFnNumericBoolean, plug.asBool()
    elif dataType == om2.MFnNumericData.kByte:
        return attrtypes.kMFnNumericByte, plug.asBool()
    elif dataType == om2.MFnNumericData.kShort:
        return attrtypes.kMFnNumericShort, plug.asShort()
    elif dataType == om2.MFnNumericData.kInt:
        return attrtypes.kMFnNumericInt, plug.asInt()
    elif dataType == om2.MFnNumericData.kLong:
        return attrtypes.kMFnNumericLong, plug.asInt()
    elif dataType == om2.MFnNumericData.kDouble:
        return attrtypes.kMFnNumericDouble, plug.asDouble()
    elif dataType == om2.MFnNumericData.kFloat:
        return attrtypes.kMFnNumericFloat, plug.asFloat()
    elif dataType == om2.MFnNumericData.kAddr:
        return attrtypes.kMFnNumericAddr, plug.asAddr()
    elif dataType == om2.MFnNumericData.kChar:
        return attrtypes.kMFnNumericChar, plug.asChar()
    elif dataType == om2.MFnNumericData.k2Double:
        return attrtypes.kMFnNumeric2Double, om2.MFnNumericData(plug.asMObject()).getData()
    elif dataType == om2.MFnNumericData.k2Float:
        return attrtypes.kMFnNumeric2Float, om2.MFnNumericData(plug.asMObject()).getData()
    elif dataType == om2.MFnNumericData.k2Int:
        return attrtypes.kMFnNumeric2Int, om2.MFnNumericData(plug.asMObject()).getData()
    elif dataType == om2.MFnNumericData.k2Long:
        return attrtypes.kMFnNumeric2Long, om2.MFnNumericData(plug.asMObject()).getData()
    elif dataType == om2.MFnNumericData.k2Short:
        return attrtypes.kMFnNumeric2Short, om2.MFnNumericData(plug.asMObject()).getData()
    elif dataType == om2.MFnNumericData.k3Double:
        return attrtypes.kMFnNumeric3Double, om2.MFnNumericData(plug.asMObject()).getData()
    elif dataType == om2.MFnNumericData.k3Float:
        return attrtypes.kMFnNumeric3Float, om2.MFnNumericData(plug.asMObject()).getData()
    elif dataType == om2.MFnNumericData.k3Int:
        return attrtypes.kMFnNumeric3Int, om2.MFnNumericData(plug.asMObject()).getData()
    elif dataType == om2.MFnNumericData.k3Long:
        return attrtypes.kMFnNumeric3Long, om2.MFnNumericData(plug.asMObject()).getData()
    elif dataType == om2.MFnNumericData.k3Short:
        return attrtypes.kMFnNumeric3Short, om2.MFnNumericData(plug.asMObject()).getData()
    elif dataType == om2.MFnNumericData.k4Double:
        return attrtypes.kMFnNumeric4Double, om2.MFnNumericData(plug.asMObject()).getData()
    return None, None


def getTypedValue(plug):
    """Returns the maya type from the given typedAttributePlug

    :param plug: MPLug
    :return: maya type
    """
    tAttr = om2.MFnTypedAttribute(plug.attribute())
    dataType = tAttr.attrType()
    if dataType == om2.MFnData.kInvalid:
        return None, None
    elif dataType == om2.MFnData.kString:
        return attrtypes.kMFnDataString, plug.asString()
    elif dataType == om2.MFnData.kNumeric:
        return getNumericValue(plug)
    elif dataType == om2.MFnData.kMatrix:
        return attrtypes.kMFnDataMatrix, om2.MFnMatrixData(plug.asMObject()).matrix()
    elif dataType == om2.MFnData.kFloatArray:
        return attrtypes.kMFnDataFloatArray, om2.MFnFloatArrayData(plug.asMObject()).array()
    elif dataType == om2.MFnData.kDoubleArray:
        return attrtypes.kMFnDataDoubleArray, om2.MFnDoubleArrayData(plug.asMObject()).array()
    elif dataType == om2.MFnData.kIntArray:
        return attrtypes.kMFnDataIntArray, om2.MFnIntArrayData(plug.asMObject()).array()
    elif dataType == om2.MFnData.kPointArray:
        return attrtypes.kMFnDataPointArray, om2.MFnPointArrayData(plug.asMObject()).array()
    elif dataType == om2.MFnData.kVectorArray:
        return attrtypes.kMFnDataVectorArray, om2.MFnVectorArrayData(plug.asMObject()).array()
    elif dataType == om2.MFnData.kStringArray:
        return attrtypes.kMFnDataStringArray, om2.MFnStringArrayData(plug.asMObject()).array()
    elif dataType == om2.MFnData.kMatrixArray:
        return attrtypes.kMFnDataMatrixArray, om2.MFnMatrixArrayData(plug.asMObject()).array()
    return None, None


def setPlugInfoFromDict(plug, **kwargs):
    """Sets the standard plug settings via a dict.


    :param plug: The Plug to change
    :type plug: om2.MPlug
    :param kwargs: currently includes, default, min, max, softMin, softMin, value, Type, channelBox, keyable, locked.
    :type kwargs: dict



    .. code-block:: python

        data = {
            "Type": 5, # attrtypes.kType
            "channelBox": true,
            "default": 1.0,
            "isDynamic": true,
            "keyable": true,
            "locked": false,
            "max": 99999,
            "min": 0.0,
            "name": "scale",
            "softMax": None,
            "softMin": None,
            "value": 1.0,
            "children": [{}] # in the same format as the parent info
          }
        somePLug = om2.MPlug()
        setPlugInfoFromDict(somePlug, **data)

    """
    children = kwargs.get("children", [])
    # just to ensure we dont crash we check to make sure the requested plug is a compound.
    if plug.isCompound and not plug.isArray:
        # cache the childCount
        childCount = plug.numChildren()
        if not children:
            # not a huge fan of doing a deepcopy just to deal with modifying the value/default further down
            children = [copy.deepcopy(kwargs) for i in range(childCount)]

            # now iterate the children data which contains a dict which is in the format
            for i, childInfo in enumerate(children):
                # it's possible that no data was passed for this child so skip
                if not childInfo:
                    continue
                # ensure the child index exists
                if i in range(childCount):
                    # modify the value and default value if we passed one in, this is done because the
                    # children would support a single value over and compound i.e kNumeric3Float
                    value = childInfo.get("value")
                    defaultValue = childInfo.get("default")
                    if value is not None and i in range(len(value)):
                        childInfo["value"] = value[i]
                    if defaultValue is not None and i in range(len(defaultValue)):
                        childInfo["default"] = defaultValue[i]
                    setPlugInfoFromDict(plug.child(i), **childInfo)
        else:
            # now iterate the children data which contains a dict which is in the format
            for i, childInfo in enumerate(children):
                # it's possible that no data was passed for this child so skip
                if not childInfo:
                    continue
                # ensure the child index exists
                if i in range(childCount):
                    childPlug = plug.child(i)
                    try:
                        setPlugInfoFromDict(childPlug, **childInfo)
                    except RuntimeError:
                        logger.error("Failed to set default values on plug: {}".format(childPlug.name()),
                                     extra=childInfo)
                        raise

    default = kwargs.get("default")
    min = kwargs.get("min")
    max = kwargs.get("max")
    softMin = kwargs.get("softMin")
    softMax = kwargs.get("softMax")
    value = kwargs.get("value")
    Type = kwargs.get("Type")

    # certain data types require casting i.e MDistance
    if default is not None and Type is not None:
        if Type == attrtypes.kMFnDataString:
            default = om2.MFnStringData().create(default)
        elif Type == attrtypes.kMFnDataMatrix:
            default = om2.MMatrix(default)
            value = om2.MMatrix(value)
        elif Type == attrtypes.kMFnUnitAttributeAngle:
            default = om2.MAngle(default, om2.MAngle.kRadians)
            value = om2.MAngle(value, om2.MAngle.kRadians)
        elif Type == attrtypes.kMFnUnitAttributeDistance:
            default = om2.MDistance(default)
            value = om2.MDistance(value)
        elif Type == attrtypes.kMFnUnitAttributeTime:
            default = om2.MTime(default)
            value = om2.MTime(value)
        try:
            setPlugDefault(plug, default)
        except Exception:
            logger.error("Failed to set plug default values: {}".format(plug.name()),
                         exc_info=True,
                         extra={"data": default})
    if value is not None and not plug.attribute().hasFn(om2.MFn.kMessageAttribute) and not plug.isCompound and not \
            plug.isArray:
        setPlugValue(plug, value)
    if min is not None:
        setMin(plug, min)
    if max is not None:
        setMax(plug, max)
    if softMin is not None:
        setSoftMin(plug, softMin)
    if softMax is not None:
        setSoftMax(plug, softMax)
    plug.isChannelBox = kwargs.get("channelBox", False)
    plug.isKeyable = kwargs.get("keyable", False)
    plug.isLocked = kwargs.get("locked", False)


def setPlugValue(plug, value):
    """
    Sets the given plug's value to the passed in value.

    :param plug: MPlug, The node plug.
    :param value: type, Any value of any data type.
    """

    if plug.isArray:
        count = plug.evaluateNumElements()
        if count != len(value):
            return
        for i in range(count):
            setPlugValue(plug.elementByPhysicalIndex(i), value[i])
        return
    elif plug.isCompound:
        count = plug.numChildren()
        if count != len(value):
            return
        for i in range(count):
            setPlugValue(plug.child(i), value[i])
        return
    obj = plug.attribute()
    if obj.hasFn(om2.MFn.kUnitAttribute):
        attr = om2.MFnUnitAttribute(obj)
        ut = attr.unitType()
        if ut == om2.MFnUnitAttribute.kDistance:
            plug.setMDistance(om2.MDistance(value))
        elif ut == om2.MFnUnitAttribute.kTime:
            plug.setMTime(om2.MTime(value))
        elif ut == om2.MFnUnitAttribute.kAngle:
            plug.setMAngle(om2.MAngle(value))
    elif obj.hasFn(om2.MFn.kNumericAttribute):
        attr = om2.MFnNumericAttribute(obj)
        at = attr.numericType()
        if at in (om2.MFnNumericData.k2Double, om2.MFnNumericData.k2Float, om2.MFnNumericData.k2Int,
                  om2.MFnNumericData.k2Long, om2.MFnNumericData.k2Short, om2.MFnNumericData.k3Double,
                  om2.MFnNumericData.k3Float, om2.MFnNumericData.k3Int, om2.MFnNumericData.k3Long,
                  om2.MFnNumericData.k3Short, om2.MFnNumericData.k4Double):
            data = om2.MFnNumericData().create(value)
            plug.setMObject(data.object())
        elif at == om2.MFnNumericData.kDouble:
            plug.setDouble(value)
        elif at == om2.MFnNumericData.kFloat:
            plug.setFloat(value)
        elif at == om2.MFnNumericData.kBoolean:
            plug.setBool(value)
        elif at == om2.MFnNumericData.kChar:
            plug.setChar(value)
        elif at in (om2.MFnNumericData.kInt, om2.MFnNumericData.kInt64, om2.MFnNumericData.kLong,
                    om2.MFnNumericData.kLast):
            plug.setInt(value)
        elif at == om2.MFnNumericData.kShort:
            plug.setInt(value)

    elif obj.hasFn(om2.MFn.kEnumAttribute):
        plug.setInt(value)

    elif obj.hasFn(om2.MFn.kTypedAttribute):
        attr = om2.MFnTypedAttribute(obj)
        at = attr.attrType()
        if at == om2.MFnData.kMatrix:
            mat = om2.MFnMatrixData().create(om2.MMatrix(value))
            plug.setMObject(mat)
        elif at == om2.MFnData.kString:
            plug.setString(value)

    elif obj.hasFn(om2.MFn.kMatrixAttribute):
        mat = om2.MFnMatrixData().create(om2.MMatrix(value))
        plug.setMObject(mat)
    elif obj.hasFn(om2.MFn.kMessageAttribute) and isinstance(value, om2.MPlug):
        # connect the message attribute
        connectPlugs(plug, value)
    else:
        raise ValueError(
            "Currently we don't support dataType ->{} contact the developers to get this implemented".format(
                obj.apiTypeStr))


def getPlugFn(obj):
    """Returns the MfunctionSet for the MObject

    :param obj: MObject that has the MFnAttribute functionset
    :type obj: MObject
    """
    if obj.hasFn(om2.MFn.kCompoundAttribute):
        return om2.MFnCompoundAttribute
    elif obj.hasFn(om2.MFn.kEnumAttribute):
        return om2.MFnEnumAttribute
    elif obj.hasFn(om2.MFn.kGenericAttribute):
        return om2.MFnGenericAttribute
    elif obj.hasFn(om2.MFn.kLightDataAttribute):
        return om2.MFnLightDataAttribute
    elif obj.hasFn(om2.MFn.kMatrixAttribute):
        return om2.MFnMatrixAttribute
    elif obj.hasFn(om2.MFn.kMessageAttribute):
        return om2.MFnMessageAttribute
    elif obj.hasFn(om2.MFn.kNumericAttribute):
        return om2.MFnNumericAttribute
    elif obj.hasFn(om2.MFn.kTypedAttribute):
        return om2.MFnTypedAttribute
    elif obj.hasFn(om2.MFn.kUnitAttribute):
        return om2.MFnUnitAttribute
    return om2.MFnAttribute


def hasChildPlugByName(parentPlug, childName):
    for child in iterChildren(parentPlug):
        if childName in child.partialName(includeNonMandatoryIndices=True, useLongNames=True,
                                          includeInstancedIndices=True):
            return True
    return False


def iterChildren(plug):
    if plug.isArray:
        for p in range(plug.evaluateNumElements()):
            child = plug.elementByPhysicalIndex(p)
            yield child
            for leaf in iterChildren(child):
                yield leaf
    elif plug.isCompound:
        for p in range(plug.numChildren()):
            child = plug.child(p)
            yield child
            for leaf in iterChildren(child):
                yield leaf


def plugType(plug):
    obj = plug.attribute()
    if obj.hasFn(om2.MFn.kCompoundAttribute):
        return attrtypes.kMFnCompoundAttribute
    if obj.hasFn(om2.MFn.kNumericAttribute):
        nAttr = om2.MFnNumericAttribute(obj)
        dataType = nAttr.numericType()
        if dataType == om2.MFnNumericData.kBoolean:
            return attrtypes.kMFnNumericBoolean
        elif dataType == om2.MFnNumericData.kByte:
            return attrtypes.kMFnNumericByte
        elif dataType == om2.MFnNumericData.kShort:
            return attrtypes.kMFnNumericShort
        elif dataType == om2.MFnNumericData.kInt:
            return attrtypes.kMFnNumericInt
        elif dataType == om2.MFnNumericData.kLong:
            return attrtypes.kMFnNumericLong
        elif dataType == om2.MFnNumericData.kDouble:
            return attrtypes.kMFnNumericDouble
        elif dataType == om2.MFnNumericData.kFloat:
            return attrtypes.kMFnNumericFloat
        elif dataType == om2.MFnNumericData.kAddr:
            return attrtypes.kMFnNumericAddr
        elif dataType == om2.MFnNumericData.kChar:
            return attrtypes.kMFnNumericChar
        elif dataType == om2.MFnNumericData.k2Double:
            return attrtypes.kMFnNumeric2Double
        elif dataType == om2.MFnNumericData.k2Float:
            return attrtypes.kMFnNumeric2Float
        elif dataType == om2.MFnNumericData.k2Int:
            return attrtypes.kMFnNumeric2Int
        elif dataType == om2.MFnNumericData.k2Long:
            return attrtypes.kMFnNumeric2Long
        elif dataType == om2.MFnNumericData.k2Short:
            return attrtypes.kMFnNumeric2Short
        elif dataType == om2.MFnNumericData.k3Double:
            return attrtypes.kMFnNumeric3Double
        elif dataType == om2.MFnNumericData.k3Float:
            return attrtypes.kMFnNumeric3Float
        elif dataType == om2.MFnNumericData.k3Int:
            return attrtypes.kMFnNumeric3Int
        elif dataType == om2.MFnNumericData.k3Long:
            return attrtypes.kMFnNumeric3Long
        elif dataType == om2.MFnNumericData.k3Short:
            return attrtypes.kMFnNumeric3Short
        elif dataType == om2.MFnNumericData.k4Double:
            return attrtypes.kMFnNumeric4Double
    elif obj.hasFn(om2.MFn.kUnitAttribute):
        uAttr = om2.MFnUnitAttribute(obj)
        ut = uAttr.unitType()
        if ut == om2.MFnUnitAttribute.kDistance:
            return attrtypes.kMFnUnitAttributeDistance
        elif ut == om2.MFnUnitAttribute.kAngle:
            return attrtypes.kMFnUnitAttributeAngle
        elif ut == om2.MFnUnitAttribute.kTime:
            return attrtypes.kMFnUnitAttributeTime
    elif obj.hasFn(om2.MFn.kEnumAttribute):
        return attrtypes.kMFnkEnumAttribute
    elif obj.hasFn(om2.MFn.kTypedAttribute):
        tAttr = om2.MFnTypedAttribute(obj)
        dataType = tAttr.attrType()
        if dataType == om2.MFnData.kString:
            return attrtypes.kMFnDataString
        elif dataType == om2.MFnData.kMatrix:
            return attrtypes.kMFnDataMatrix
        elif dataType == om2.MFnData.kFloatArray:
            return attrtypes.kMFnDataFloatArray
        elif dataType == om2.MFnData.kDoubleArray:
            return attrtypes.kMFnDataDoubleArray
        elif dataType == om2.MFnData.kIntArray:
            return attrtypes.kMFnDataIntArray
        elif dataType == om2.MFnData.kPointArray:
            return attrtypes.kMFnDataPointArray
        elif dataType == om2.MFnData.kVectorArray:
            return attrtypes.kMFnDataVectorArray
        elif dataType == om2.MFnData.kStringArray:
            return attrtypes.kMFnDataStringArray
        elif dataType == om2.MFnData.kMatrixArray:
            return attrtypes.kMFnDataMatrixArray

    elif obj.hasFn(om2.MFn.kMessageAttribute):
        return attrtypes.kMFnMessageAttribute
    elif obj.hasFn(om2.MFn.kMatrixAttribute):
        return attrtypes.kMFnDataMatrix
    return None


def getPythonTypeFromPlugValue(plug):
    dataType, value = getPlugAndType(plug)
    types = (attrtypes.kMFnDataMatrix, attrtypes.kMFnDataFloatArray,
             attrtypes.kMFnDataFloatArray, attrtypes.kMFnDataDoubleArray,
             attrtypes.kMFnDataIntArray, attrtypes.kMFnDataPointArray, attrtypes.kMFnDataStringArray,
             attrtypes.kMFnNumeric2Double, attrtypes.kMFnNumeric2Float, attrtypes.kMFnNumeric2Int,
             attrtypes.kMFnNumeric2Long, attrtypes.kMFnNumeric2Short, attrtypes.kMFnNumeric3Double,
             attrtypes.kMFnNumeric3Int, attrtypes.kMFnNumeric3Long, attrtypes.kMFnNumeric3Short,
             attrtypes.kMFnNumeric4Double)
    if dataType is None:
        return None
    elif isinstance(dataType, (list, tuple)):
        res = []
        for idx, dt in enumerate(dataType):
            if dt == attrtypes.kMFnDataMatrix:
                res.append(tuple(value[idx]))
            elif dt in (
                    attrtypes.kMFnUnitAttributeDistance, attrtypes.kMFnUnitAttributeAngle,
                    attrtypes.kMFnUnitAttributeTime):
                res.append(value[idx].value)
        return res
    elif dataType in (attrtypes.kMFnDataMatrixArray, attrtypes.kMFnDataVectorArray):
        return map(tuple, value)
    elif dataType in (
            attrtypes.kMFnUnitAttributeDistance, attrtypes.kMFnUnitAttributeAngle, attrtypes.kMFnUnitAttributeTime):
        return value.value
    elif dataType in types:
        return tuple(value)

    return value


def mayaTypeToPythonType(mayaType):
    if isinstance(mayaType, (om2.MDistance, om2.MTime, om2.MAngle)):
        return mayaType.value
    elif isinstance(mayaType, (om2.MMatrix, om2.MVector, om2.MPoint)):
        return list(mayaType)
    return mayaType


def pythonTypeToMayaType(dataType, value):
    if dataType == attrtypes.kMFnDataMatrixArray:
        return map(om2.MMatrix, value)
    elif attrtypes.kMFnDataVectorArray:
        return map(om2.MVector, value)
    elif dataType == attrtypes.kMFnUnitAttributeDistance:
        return om2.MDistance(value)
    elif dataType == attrtypes.kMFnUnitAttributeAngle:
        return om2.MAngle(value, om2.MAngle.kDegrees)
    elif dataType == attrtypes.kMFnUnitAttributeTime:
        return om2.MTime(value)
    return value


def nextAvailableElementPlug(arrayPlug):
    """Returns the next available element plug from th plug array, if the plugArray is a compoundArray then the children
    of immediate children of the compound is searched.
    ::note: How does it work?
            loops through all current elements looking for a outgoing connection, if one doesn't exist then this element
            plug is returned. if the element plug is a compound then if immediate children are searched and the element parent
            plug will be returned if there's a connection.

    :param arrayPlug: the plugArray to search
    :type arrayPlug: om2.MPlug
    """
    count = arrayPlug.evaluateNumElements()
    if count == 0:
        return arrayPlug.elementByLogicalIndex(0)
    for i in range(1, count):
        availPlug = arrayPlug.elementByLogicalIndex(i)
        if arrayPlug.isCompound:
            connected = False
            for childIndex in range(availPlug.numChildren()):
                if availPlug.child(childIndex).isSource:
                    connected = True
                    break
        else:
            connected = availPlug.isSource
        if connected or availPlug.isSource:
            continue
        return availPlug
    else:
        return arrayPlug.elementByLogicalIndex(count)


def nextAvailableDestElementPlug(arrayPlug):
    count = arrayPlug.evaluateNumElements()
    if count == 0:
        return arrayPlug.elementByLogicalIndex(0)
    for i in range(count):
        availPlug = arrayPlug.elementByPhysicalIndex(i)
        if availPlug.isCompound:
            connected = False
            for childIndex in range(availPlug.numChildren()):
                if availPlug.child(childIndex).isDestination:
                    connected = True
                    break
            if connected:
                continue
        if availPlug.isDestination:
            continue
        return availPlug
    else:
        return arrayPlug.elementByLogicalIndex(count)
