import maya.api.OpenMaya as om2
import maya.cmds as cmds

MAYA_TRANSLATE_ATTRS = ["translateX", "translateY", "translateZ"]
MAYA_ROTATE_ATTRS = ["rotateX", "rotateY", "rotateZ"]
MAYA_SCALE_ATTRS = ["scaleX", "scaleY", "scaleZ"]
MAYATRANSFORMATTRS = MAYA_TRANSLATE_ATTRS + MAYA_ROTATE_ATTRS + MAYA_SCALE_ATTRS


def getTransRotScaleAttrsAsList(transformNode):
    """Returns the attribute values of MAYATRANSFORMATTRS as a list, each value is a float value.

    ["translateX", "translateY", "translateZ", "rotateX", "rotateY", "rotateZ", "scaleX", "scaleY", "scaleZ"]

    :param transformNode: The transform or joint node name to return
    :type transformNode: str
    :return attrValueList: list with all the float values
    :rtype attrValueList: list(float)
    """
    attrValueList = list()
    for attribute in MAYATRANSFORMATTRS:
        attrValueList.append(cmds.getAttr(".".join([transformNode, attribute])))
    return attrValueList


def srtAttrsDict(transformNode, rotate=True, translate=True, scale=True):
    """Creates a dictionary with rot translate and scale attributes and their values.

    Useful for copying default SRT values.

    :param transformNode: Maya transform node name
    :type transformNode: str
    :param rotate: Record the rotate values
    :type rotate: bool
    :param translate: Record the rotate values
    :type translate: bool
    :param scale: Record the rotate values
    :type scale: bool
    :return srtAttrDict: A dictionary with rot translate and scale attributes and their values
    :rtype srtAttrDict: dict()
    """
    srtAttrDict = dict()
    if rotate:
        for attr in MAYA_ROTATE_ATTRS:
            srtAttrDict[attr] = cmds.getAttr(".".join([transformNode, attr]))
    if translate:
        for attr in MAYA_TRANSLATE_ATTRS:
            srtAttrDict[attr] = cmds.getAttr(".".join([transformNode, attr]))
    if scale:
        for attr in MAYA_SCALE_ATTRS:
            srtAttrDict[attr] = cmds.getAttr(".".join([transformNode, attr]))
    return srtAttrDict


def setFloatAttrsDict(mayaNode, attrDict):
    """Sets the dictionary with attributes that are floats (or ints?)

    Useful for pasting default SRT values

    :param mayaNode: Maya node name
    :type mayaNode: str
    :param attrDict: A dictionary with any attribute names as keys and floats as values
    :type attrDict: dict()
    """
    for attr in attrDict:
        cmds.setAttr(".".join([mayaNode, attr]), attrDict[attr])


def checkAllAttrsZeroed(transformNode):
    """Checks to see if all the current pos values are zeroed, a useful check before freezing transforms.  Uses a \
     tolerance in case of micro values which is often on Maya objects.

    Checks these values are zeroed:

        ["translateX", "translateY", "translateZ", "rotateX", "rotateY", "rotateZ"]

    Checks these values are 1.0:

        ["scaleX", "scaleY", "scaleZ"]

    :param transformNode: The name of the Maya transform or joint node
    :type transformNode: str
    :return isZero: True if zeroed, False if not
    :rtype isZero: bool
    """
    attrValList = getTransRotScaleAttrsAsList(transformNode)
    for val in attrValList[:-3]:
        if val > 0.0001 or val < -0.0001:
            return False
    for val in attrValList[6:]:
        if val > 1.0001 or val < -0.9999:
            return False
    return True


def checkAllAttrsZeroedList(transformNodeList):
    """Checks to see if all the current pos values are zeroed on an object list, a useful check before freezing \
    transforms.  Uses a tolerance in case of micro values which is often on Maya objects.

    Returns a list of True False values.

    Checks these values are zeroed:

        ["translateX", "translateY", "translateZ", "rotateX", "rotateY", "rotateZ"]

    Checks these values are 1.0:

        ["scaleX", "scaleY", "scaleZ"]

    :param transformNodeList: A list of Maya transform or joint node names
    :type transformNodeList: list(str)
    :return isZeroList: A list of True or False values, True if the object is zeroed, False if not
    :rtype isZeroList: list(bool)
    """
    for transform in transformNodeList:
        if not checkAllAttrsZeroed(transform):
            return False
    return True


def setTransRotScaleAttrsAsList(transformNode, attrValueList):
    """Given an attribute value list set the rotation, translation, and scale values on a transformNode

    :param transformNode: The name of the Maya transform or joint node
    :type transformNode: str
    :param attrValueList: A list of 9 float values to set for each value in MAYATRANSFORMATTRS
    :type attrValueList: list(float)
    """
    for i, attribute in enumerate(MAYATRANSFORMATTRS):
        cmds.setAttr(".".join([transformNode, attribute]), attrValueList[i])


def setAttrAutoType(node, attr, value, message=False, debugMe=False):
    """Sets a Maya attribute with auto type discovery functionality
    Ie. Will find the type iof the attribute and this function adds the type flag into the cmds.setAttr command
    **Will have to add more support for multiple attribute types

    :param node: The name of the Maya node
    :type node: str
    :param attr: The maya attribute name, attribute only, not the node or object
    :type attr: str
    :param value: The value of the attribute multi-type (can be many types)
    :type value: multiple
    :param message: Report a message for each attribute set, off by default
    :type message: bool
    """
    if debugMe:
        om2.MGlobal.displayInfo("Node `{}`, attr `{}`, value `{}`".format(node, attr, value))
    attrType = cmds.getAttr(".".join([node, attr]), type=True)  # get the attribute type
    if debugMe:
        om2.MGlobal.displayInfo("attrType `{}`".format(attrType))
    # if regular one value
    if (attrType == "doubleLinear") or (attrType == "float") or (attrType == "enum") \
            or (attrType == "long") or (attrType == "double") or (attrType == "bool") \
            or (attrType == "doubleAngle"):
        cmds.setAttr(".".join([node, attr]), value)
        if message:
            om2.MGlobal.displayInfo("Attribute `{}` Set {}".format(".".join([node, attr]), value))
    elif attrType == "float3":  # if type
        cmds.setAttr(".".join([node, attr]), value[0], value[1], value[2], type="double3")
        if message:
            om2.MGlobal.displayInfo("Attribute `{}` Set {}".format(".".join([node, attr]), value))
    elif attrType == "string":
        cmds.setAttr(".".join([node, attr]), value, type="string")
        if message:
            om2.MGlobal.displayInfo("Attribute `{}` Set {}".format(".".join([node, attr]), value))
    else:
        om2.MGlobal.displayWarning("The type `{}` for the attribute `{}` not "
                                   "found".format(attrType, ".".join([node, attr]), value))


def setAttrributesFromDict(node, attributeDict, message=False):
    """Takes an attribute dictionary and applies it to a node setting all the attributes
    d = {'translateX': (1.2, 'diffuseColor': (.5, .5, .5)}

    :param node: the name of the Maya node
    :type node: str
    :param attributeDict: The dictionary with attribute names as keys and values as values
    :type attributeDict: dict
    :param message: Report a message for each attribute set, off by default
    :type message: bool
    """
    for attr, value in iter(attributeDict.items()):
        if value is None:  # must look for None as some values can be 0
            continue
        setAttrAutoType(node, attr, value, message=message)


def setAttCurrentDefault(obj, attr, report=True):
    """Sets an attribute's current value to the default value

    :param obj: The objects name
    :type obj: str
    :param attr: the attribute name to set
    :type attr: str
    :param report: report error messages?
    :type report: bool
    :return value: the default value set, or None if none set
    :rtype: float
    """
    try:
        value = cmds.getAttr('.'.join([obj, attr]))
        cmds.addAttr('.'.join([obj, attr]), e=1, dv=value)
        if report:
            om2.MGlobal.displayInfo('Object `{}` Attribute `{}` default set to `{}`'.format(obj, attr, value))
        return value
    except RuntimeError:
        if report:
            om2.MGlobal.displayInfo('Attribute Skipped: {}'.format(attr))
    return None


def setAllAttrsCurrentDefualts(obj, report=True):
    """Sets all the attributes current value of the given object to be the default value
    Will only work on user defined attributes as you're unable to cahnge default attributes

    :param obj: The objects name
    :type obj: str
    :param report: report error messages?
    :type report: bool
    """
    attributeList = cmds.listAttr(obj, visible=True, userDefined=True)
    for attr in attributeList:
        setAttCurrentDefault(obj, attr, report=report)


def setSelCurValuesAsDefaults(report=True):
    '''Iterates through the current object selection setting it's current attribute values as the default values
    Will only work on user defined attributes as you're unable to change default attributes

    :param report: report error messages?
    :type report: bool
    '''
    objectList = cmds.ls(selection=True)
    for obj in objectList:
        setAllAttrsCurrentDefualts(obj, report=report)


def unlockAll(obj, translate=True, rotate=True, scale=True, visibility=True, lock=False, keyable=True):
    """Unlocks All Common (rotation, translation, scale and vis) Attributes

    :param obj: The name of the object
    :type obj: str
    :param translate: Do you want to affect translate?
    :type translate: bool
    :param rotate: Do you want to affect rotate?
    :type rotate: bool
    :param scale: Do you want to affect scale?
    :type scale: bool
    :param visibility: Do you want to affect visibility?
    :type visibility: bool
    :param lock: this state will either lock or unlock, True will lock all attributes
    :type lock: bool
    """
    if translate:  # must unlock on the individual attr translateX and not translate for some reason
        for transAttr in MAYA_TRANSLATE_ATTRS:
            cmds.setAttr("{}.{}".format(obj, transAttr), lock=lock, keyable=keyable)
    if rotate:
        for transAttr in MAYA_ROTATE_ATTRS:
            cmds.setAttr("{}.{}".format(obj, transAttr), lock=lock, keyable=keyable)
    if scale:
        for transAttr in MAYA_SCALE_ATTRS:
            cmds.setAttr("{}.{}".format(obj, transAttr), lock=lock, keyable=keyable)
    if visibility:
        cmds.setAttr("{}.visibility".format(obj), lock=lock, keyable=keyable)


def showAllAttrChannelBox(obj, translate=True, rotate=True, scale=True, visibility=True, channelBValue=True,
                          keyable=True):
    """Shows Common (rotation, translation, scale and vis) attributes in the channel box

    :param obj: Maya object name to reset
    :type obj: str
    :param rotate: reset rotate
    :type rotate: bool
    :param translate: reset translate
    :type translate: bool
    :param scale: reset scale
    :type scale: bool
    :param visibility: reset visibility
    :type visibility: bool
    :param channelBValue: Display in the channel box, should be True in most cases
    :type channelBValue: bool
    :param keyable: Make the attribute keyable, should be true in most cases
    :type keyable: bool
    """
    if translate:
        cmds.setAttr("{}.translate".format(obj), channelBox=channelBValue)
        cmds.setAttr("{}.translate".format(obj), keyable=keyable)  # must add as channel box makes non keyable
    if rotate:
        cmds.setAttr("{}.rotate".format(obj), channelBox=channelBValue)
        cmds.setAttr("{}.rotate".format(obj), keyable=keyable)
    if scale:
        cmds.setAttr("{}.scale".format(obj), channelBox=channelBValue)
        cmds.setAttr("{}.scale".format(obj), keyable=keyable)
    if visibility:
        cmds.setAttr("{}.visibility".format(obj), channelBox=channelBValue)
        cmds.setAttr("{}.visibility".format(obj), keyable=keyable)


def resetTransformAttributes(obj, rotate=True, translate=True, scale=True, visibility=False):
    """Resets the transforms (and potentially visibility) of a Maya object.

    :param obj: Maya object name to reset
    :type obj: str
    :param rotate: reset rotate
    :type rotate: bool
    :param translate: reset translate
    :type translate: bool
    :param scale: reset scale
    :type scale: bool
    :param visibility: reset visibility
    :type visibility: bool
    """
    if translate:
        cmds.setAttr("{}.translate".format(obj), 0.0, 0.0, 0.0)
    if rotate:
        cmds.setAttr("{}.rotate".format(obj), 0.0, 0.0, 0.0)
    if scale:
        cmds.setAttr("{}.scale".format(obj), 1.0, 1.0, 1.0)
    if visibility:
        cmds.setAttr("{}.visibility".format(obj), 1.0)


def createEnumAttributeFromList(enumList, node, attrName, keyable=True):
    """creates a drop down attribute (enum attribute) from a list

    :param enumList: dropdown list of strings
    :param node: string, the object
    :param attrName: string of the attribute
    :return: string driver attribute 'object.attribute'
    """
    enumString = ":".join(enumList)
    cmds.addAttr(node, longName=attrName, attributeType='enum', enumName=enumString, keyable=keyable)
    driverAttr = '.'.join([str(node), attrName])
    return driverAttr


def addProxyAttribute(obj, existingObj, existingAttr, proxyAttr="", keyable=True):
    """creates a proxy attribute on the `obj`
    if `proxyAttr` is empty will use the `existingAttr` name

    :param obj: The maya object the proxy attribute will be created on
    :type obj: str
    :param existingObj: The Maya obj that already exists with the attribute to be copied
    :type existingObj: str
    :param existingAttr: The existing attribute to be copied on the existing obj, don't include obj
    :type existingAttr: str
    :param proxyAttr: the name of the proxy attribute, if empty will clone the existingAttr name
    :type proxyAttr: str
    :param keyable: is the proxy attribute keyable?
    :type keyable: bool
    :return obj: The object name with the new proxy attribute
    :rtype obj: str
    :return proxyAttr: The attribute of the new proxy attribute
    :rtype proxyAttr: str
    """
    if not proxyAttr:
        proxyAttr = existingAttr
    # get attribute type, not sure if this is needed
    attrType = cmds.attributeQuery(existingAttr, node=existingObj, attributeType=True)
    cmds.addAttr(obj, longName=proxyAttr, proxy=".".join([existingObj, existingAttr]), keyable=keyable,
                 attributeType=attrType)
    return obj, proxyAttr


def addProxyAttributeCheckVersion(obj, existingObj, existingAttr, proxyAttr="", keyable=True):
    """creates a proxy attribute on the `obj` also checks the
    if `proxyAttr` is empty will use the `existingAttr` name

    :param obj: The maya object the proxy attribute will be created on
    :type obj: str
    :param existingObj: The Maya obj that already exists with the attribute to be copied
    :type existingObj: str
    :param existingAttr: The existing attribute to be copied on the existing obj, don't include obj
    :type existingAttr: str
    :param proxyAttr: the name of the proxy attribute, if empty will clone the existingAttr name
    :type proxyAttr: str
    :param keyable: is the proxy attribute keyable?
    :type keyable: bool
    :return obj: The object name with the new proxy attribute
    :rtype obj: str
    :return proxyAttr: The attribute of the new proxy attribute
    :rtype proxyAttr: str
    """
    mayaVersion = cmds.about(version=True)
    if float(mayaVersion) < 2017.0:
        om2.MGlobal.displayWarning("Skipping Proxy Attributes as this version of Maya doesn't support proxies. "
                                   "Only available in 2017 and above")
        return "", ""
    return addProxyAttribute(obj, existingObj, existingAttr, proxyAttr=proxyAttr, keyable=keyable)


def addProxyAttrList(obj, existingObj, existingAttrList, keyable=True):
    """creates a proxy attributes from a list on the `obj` from attributes on `existingObj`
    if `proxyAttr` is empty will use the `existingAttr` name

    :param obj: The maya object the proxy attribute will be created on
    :type obj: str
    :param existingObj: The Maya obj that already exists with the attribute to be copied
    :type existingObj: str
    :param existingAttrList: The existing attribute to be copied on the existing obj, don't include obj
    :type existingAttr: list
    :param proxyAttr: the name of the proxy attribute, if empty will clone the existingAttr name
    :type proxyAttr: str
    :param keyable: is the proxy attribute keyable?
    :type keyable: bool
    """
    for i, attr in enumerate(existingAttrList):
        addProxyAttribute(obj, existingObj, attr, keyable=keyable)


def createColorAttribute(node, attrName="color", keyable=True):
    """Creates a color attribute in maya on the node, attrName can be changed from color

    :param node: any maya node
    :type node: str
    :param attrName: the name of the attribute, subattributes will be nameR, nameG nameB
    :type attrName: str
    :param keyable: Add attribute into the channel box and make it keyable?
    :type keyable: bool
    :return:
    :rtype:
    """
    cmds.addAttr(node, longName=attrName, usedAsColor=True, attributeType='float3', keyable=keyable)
    cmds.addAttr(node, longName='{}R'.format(attrName), attributeType='float', parent=attrName, keyable=keyable)
    cmds.addAttr(node, longName='{}G'.format(attrName), attributeType='float', parent=attrName, keyable=keyable)
    cmds.addAttr(node, longName='{}B'.format(attrName), attributeType='float', parent=attrName, keyable=keyable)


def deleteNodesWithAttributeList(nodeList, attributeName):
    """deletes nodes that have an attribute with attributeName

    :param nodeList: a list of maya nodes
    :type nodeList: list
    :param attributeName: the name of the attribute without the node
    :type attributeName: str
    :return deletedNodes: list of the nodes that have been deleted
    :rtype deletedNodes: list
    """
    deletedNodes = list()
    for node in nodeList:
        if cmds.attributeQuery(attributeName, node=node, exists=True):
            cmds.delete(node)
            deletedNodes.append(node)
    return deletedNodes


def checkRemoveAttr(node, attrName):
    """Checks if the attribute exists and if it does remove/delete the attribute

    :param node: A maya node name
    :type node: str
    :param attrName: the attribute to remove name
    :type attrName: str
    :return deleted:  True if deleted False if not
    :rtype deleted: bool
    """
    if cmds.attributeQuery(attrName, n=node, exists=True):
        cmds.deleteAttr(".".join([node, attrName]))
        return True
    return False


def getLockedConnectedAttrs(obj, attrList=None):
    """Gets all the locked or connected attributes from either:

        1. attrList=None: all keyable attributes on an object
        2. attrList=list(attrs): the given attributes

    Returns connected or locked attributes as a list, empty list if none found

    :param obj: the maya objects name
    :type obj: str
    :param attrList: list of attributes to check
    :type attrList: str
    :return: locked or connected attributes
    :rtype: list
    """
    lockedConnectedAttrs = list()
    if attrList:  # check the given attributes
        for attr in cmds.listAttr(obj, keyable=True):
            if not cmds.getAttr(".".join([obj, attr]), settable=True):
                lockedConnectedAttrs.append(".".join([obj, attr]))
    else:  # check all keyable attrs
        for attr in cmds.listAttr(obj, keyable=True):
            if not cmds.getAttr(".".join([obj, attr]), settable=True):
                lockedConnectedAttrs.append(".".join([obj, attr]))
    return lockedConnectedAttrs


def getLockedConnectedAttrsList(nodeList, attrList=None, unlock=True):
    """Gets all the locked or connected attributes from a node list.

    Attributes can be either:

        1. attrList=None: all keyable attributes on an object
        2. attrList=list(attrs): the given attributes

    Returns two lists:
        lockedNodes: A list of nodes with locked or connected attributes
        lockedAttrList: Records the attrs locked/connected.  Is a list(list) of attributes matching the lockedNodes

    :param nodeList: A list of Maya nodes
    :type nodeList: list(str)
    :param attrList: A list of attributes to check, if empty or None will check all keyable attributes
    :type attrList: list(str)
    :return lockedNodes: A list of nodes with locked or connected attributes, is empty if no locked or connected attrs
    :rtype lockedNodes: list(str)
    :return lockedNodes: Records the attrs locked/connected.  Is a list(list) of attributes matching the lockedNodes
    :rtype lockedNodes: list(list(str))
    """
    lockedNodes = list()
    lockedAttrList = list()
    for node in nodeList:
        lockedConnectedAttrs = getLockedConnectedAttrs(node, attrList=None)
        if lockedConnectedAttrs:
            lockedNodes.append(node)
            lockedAttrList.append(lockedConnectedAttrs)
    return lockedNodes, lockedAttrList

# ---------------------------
# LIST CONNECTABLE ATTRIBUTES
# ---------------------------

def listConnectableAttrs(obj):
    """List all the connectable attributes of a Maya node

    :param obj: A Maya object or node name
    :type obj: str
    :return attributeList: list of potentially connectable attributes on the node
    :rtype attributeList: list(str)
    """
    return cmds.listAttr(obj, connectable=True)

def listConnectableAttrsSel(selectionIndex=0, message=True):
    """From the selection list all the connectable attributes

    :param selectionIndex: Only takes one object from the selection, this is the index number of the selection
    :type selectionIndex: int
    :param message: Report the message to the user
    :type message: bool
    :return attributeList: list of potentially connectable attributes on the node
    :rtype attributeList: list(str)
    """
    selObjs = cmds.ls(selection=True, long=True)
    # Filter only transforms since dealing with rot trans and scale
    if not selObjs:
        if message:
            om2.MGlobal.displayWarning("No objects selected, please select an object or node")
        return list()
    if len(selObjs) < (selectionIndex + 1):
        return list()
    return listConnectableAttrs(selObjs[selectionIndex])


# ---------------------------
# GET CHANNEL BOX ATTRS
# ---------------------------


def getChannelBoxAttrs(message=False):
    """Returns the long name of the selected attribute from the channel box

    Annoying function as it's not easy to retrieve the long name. Mel has a one liner for short names.

    selAttrs = mel.eval('selectedChannelBoxAttributes')

    :param message: Report the message to the user
    :type message: bool
    :return attrNames: list of long attribute names eg ["translateX", "rotateX"]
    :rtype attrNames: list(str)
    """
    mainObjs = cmds.channelBox("mainChannelBox", query=True, mainObjectList=True)
    mainAttrs = cmds.channelBox("mainChannelBox", query=True, selectedMainAttributes=True)
    histObjs = cmds.channelBox("mainChannelBox", query=True, historyObjectList=True)
    histAttrs = cmds.channelBox("mainChannelBox", query=True, selectedHistoryAttributes=True)
    shapeObjs = cmds.channelBox("mainChannelBox", query=True, shapeObjectList=True)
    shapeAttrs = cmds.channelBox("mainChannelBox", query=True, selectedShapeAttributes=True)
    # now combine and get the long names
    attrNames = []
    for pair in ((mainObjs, mainAttrs), (histObjs, histAttrs), (shapeObjs, shapeAttrs)):
        objs, attrs = pair
        if attrs is not None:
            for nodeName in objs:
                # get the long name not the short name
                resultList = [cmds.attributeQuery(a, node=nodeName, longName=1) for a in attrs]
                attrNames += resultList
    attrNames = list(set(attrNames))  # remove duplicates
    if not attrNames and message:
        om2.MGlobal.displayWarning("Please select attributes in the channel box")
    return attrNames
