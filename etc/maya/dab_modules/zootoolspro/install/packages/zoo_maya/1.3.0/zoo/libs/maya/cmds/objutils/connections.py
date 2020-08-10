import maya.api.OpenMaya as om2
from maya import cmds as cmds
import maya.mel as mel

from zoo.libs.maya.cmds.objutils import namehandling


# ---------------------------
# GET CONNECTIONS
# ---------------------------


def getDestinationAttrs(drivenObj, message=False):
    """From a driven object return all it's destination connected attributes as destinationObjAttrs

    Seems to be difficult to retrieve the destinationObjAttrs so have created this function, could be a better way?

    :param drivenObj: A maya node driven by some connections. Eg "pCube4"
    :type drivenObj: str
    :return destinationObjAttrs: List of maya node.connections driven by some connections Eg ["pCube4.visibility"]
    :rtype destinationObjAttrs: list(str)
    """
    destinationObjAttrs = list()
    # Find the all source connections of the current driven
    currentDrivenAllAttrs = cmds.listAttr(drivenObj, connectable=True, inUse=True)
    for attr in currentDrivenAllAttrs:
        objAttr = ".".join([drivenObj, attr])
        try:
            if cmds.listConnections(objAttr, destination=False, source=True):
                destinationObjAttrs.append(objAttr)
        except ValueError:  # some attrs error as can't be found
            pass
    if not destinationObjAttrs:
        if message:
            om2.MGlobal.displayWarning("Node `{}` has no incoming connections ".format(drivenObj))
        return list()
    return destinationObjAttrs


def getDestinationSourceAttrs(drivenObj, message=False):
    """From a driven object return all it's destinationObjAttrs and sourceObAttrs

    Seems to be difficult to retrieve the destinationObjAttrs, once you have those you can get the

    :param drivenObj: A maya node driven by some connections. Eg "pCube4"
    :type drivenObj: str
    :return destinationObjAttrs: List of maya node.connections driven by some connections Eg ["pCube4.visibility"]
    :rtype destinationObjAttrs: list(str)
    :return destinationObjAttrs: List of maya node.connections that drive the connections Eg ["hand_control.hidePCube4"]
    :rtype destinationObjAttrs: list(str)
    """
    sourceObAttrs = list()
    destinationObjAttrs = getDestinationAttrs(drivenObj, message=False)  # Haven't found an easy way
    if not destinationObjAttrs:  # there will be no source attrs
        return list(), list()
    for objAttr in destinationObjAttrs:  # Get the destination attributes, no need to check as will pass
        sourceObAttrs.append(cmds.listConnections(objAttr, destination=False, source=True, plugs=True)[0])
    return sourceObAttrs, destinationObjAttrs


# ---------------------------
# MAKE CONNECTIONS
# ---------------------------


def makeSafeConnectionsTwoObjs(sourceObj, sourceAttr, destinationObj, destinationAttr, breakConnections=True,
                               message=False):
    """Safely connects to objects with cmds.connectAttr()

    Checks:

        - Attributes exist
        - Attributes Match
        - Destination attribute is connectable

    :param sourceObj: A maya node name
    :type sourceObj: str
    :param sourceAttr: name of the source attribute (the from attribute)
    :type sourceAttr: str
    :param destinationObj: A maya node name
    :type destinationObj: str
    :param destinationAttr: name of the destination attribute (target will be connected)
    :type destinationAttr: str
    :param breakConnections: Break existing connections?  May fail if objects are already connected
    :type breakConnections: bool
    :param message: Report messages to the user
    :type message: bool
    :return success:  True if the attributes were connected
    :rtype success: bool
    """
    sourceObjAttr = "{}.{}".format(sourceObj, sourceAttr)
    destinationObjAttr = "{}.{}".format(destinationObj, destinationAttr)
    # Check objects have the attrs
    sourceExists = cmds.attributeQuery(sourceAttr, node=sourceObj, exists=True)
    destinationExists = cmds.attributeQuery(destinationAttr, node=destinationObj, exists=True)
    if not sourceExists or not destinationExists:
        if message:
            om2.MGlobal.displayWarning("Attributes not found on nodes `{}` or `{}`".format(sourceObjAttr,
                                                                                           destinationObjAttr))
        return False
    # Check attrs are the same type
    sourceType = cmds.attributeQuery(destinationAttr, node=destinationObj, attributeType=True)
    destinationType = cmds.attributeQuery(destinationAttr, node=destinationObj, attributeType=True)
    if sourceType != destinationType:  # type mismatch so cannot connect
        if message:
            om2.MGlobal.displayWarning("Attributes types do not match `{}` and `{}`".format(sourceObjAttr,
                                                                                            destinationObjAttr))
        return False
    # Check destination attr is connectable type of attribute
    destinationConnectable = cmds.attributeQuery(destinationAttr, node=destinationObj, connectable=True)
    if not destinationConnectable:  # is not connectable
        if message:
            om2.MGlobal.displayWarning("The destination attribute `{}` is not connectable".format(destinationObjAttr))
        return False
    # Check destination attr does not already have incoming connection
    sourceConnections = cmds.listConnections(destinationObjAttr, destination=False, source=True, plugs=True)
    if sourceConnections:  # is already connected and may fail if not broken
        if breakConnections:
            if not breakAttr(destinationObjAttr):  # Disconnected
                if message:
                    om2.MGlobal.displayWarning("Cannot break the destination attribute `{}`."
                                               " Connections cannot be disconnected".format(destinationObjAttr))
        else:
            if message:
                om2.MGlobal.displayWarning("The destination attribute `{}` "
                                           "already has connections".format(destinationObjAttr))
            return
    # Passed so Connect
    cmds.connectAttr(sourceObjAttr, destinationObjAttr)
    return True


def safeConnectList(objList, sourceAttr, destinationAttr, breakConnections=True, message=True):
    """Safely connects the first object from an object list to the remaining objects.  Will ignore potential issues.

    Checks:

        - Attributes exist
        - Attributes Match
        - Destination attribute is connectable

    :param objList: A list of Maya nodes
    :type objList: list(str)
    :param sourceAttr: The source attribute (the from attribute) of the first object only
    :type sourceAttr: str
    :param destinationAttr: The destination attribute to be connected on all remaining objects (not first)
    :type destinationAttr: str
    :param breakConnections: Break existing connections?  May fail if objects are already connected
    :type breakConnections: bool
    :param message: Report the message to the user?
    :type message: bool
    :return success: Will report True if any (not all) connections were made successfully
    :rtype success: bool
    """
    success = False
    objList = namehandling.getUniqueShortNameList(objList)
    sourceObj = objList.pop(0)
    for obj in objList:
        if makeSafeConnectionsTwoObjs(sourceObj, sourceAttr, obj, destinationAttr, breakConnections=breakConnections,
                                      message=message):
            success = True
    return success


def safeConnectSelection(sourceAttr, destinationAttr, message=True):
    """Safely connects the first selected object to the remaining selected objects.  Will ignore potential issues.

    Checks:

        - Attributes exist
        - Attributes Match
        - Destination attribute is connectable

    :param sourceAttr: The source attribute (the from attribute) of the first object only
    :type sourceAttr: str
    :param destinationAttr: The destination attribute to be connected on all remaining objects (not first)
    :type destinationAttr: str
    :param message: Report the message to the user?
    :type message: bool
    :return success: Will report True if any (not all) connections were made successfully
    :rtype success: bool
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        if message:
            om2.MGlobal.displayWarning("No objects selected. Please select two or more objects or nodes")
        return False
    if len(selObjs) < 2:
        if message:
            om2.MGlobal.displayWarning("Please select two or more objects or nodes")
        return False
    return safeConnectList(selObjs, sourceAttr, destinationAttr)


def makeConnectionAttrsOrChannelBox(driverAttr="", drivenAttr="", message=True):
    """From a GUI connect the "driver.attr" and "driven.attr" from the selection list
    The first selected object to the remaining selected objects.  Will ignore potential issues.

    If nothing is entered in the GUI then will try to use the channel box selected attribute to fill any missing data.

    Must be only one attribute selected in the channel box.

    :param driverAttr: The source attribute (the from attribute) of the first object only
    :type driverAttr: str
    :param drivenAttr: The destination attribute to be connected on all remaining objects (not first)
    :type drivenAttr: str
    :param message: Report the message to the user?
    :type message: bool
    :return success: Will report True if any (not all) connections were made successfully
    :rtype success: bool
    """
    if driverAttr and drivenAttr:  # don't worry about channel box selection, both names have been entered
        return safeConnectSelection(driverAttr, drivenAttr, message=True)
    # Both names not entered so do from the selected objects and the channel box attribute selection
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        if message:
            om2.MGlobal.displayWarning("No objects selected. Please select two or more objects or nodes")
        return False
    # Get the channel box attribute selection
    selAttrs = mel.eval('selectedChannelBoxAttributes')
    if not selAttrs:
        if message:
            om2.MGlobal.displayWarning("Please fill in both Driver and Driven attributes, or select in channel box")
        return False
    if driverAttr:  # Then driven attr is missing -----------------------------------
        success = True
        drivenAttr = selAttrs[0]
        for attr in selAttrs:
            if not safeConnectList(selObjs, driverAttr, attr, message=message):
                success = False
    elif drivenAttr:  # Then driver attr is missing -----------------------------------
        if len(selAttrs) != 1:
            if message:
                om2.MGlobal.displayWarning("Please select only one channel in the channel box, "
                                           "can only have one driver attribute")
            return False
        driverAttr = selAttrs[0]
        success = safeConnectList(selObjs, driverAttr, drivenAttr, message=message)
    else:  # Neither exists so use channel box for both driver and driven -----------------------------------
        driverAttr = selAttrs[0]
        drivenAttr = selAttrs[0]
        success = True
        for attr in selAttrs:
            if not safeConnectList(selObjs, attr, attr, message=message):
                success = False
    if success:
        if message:
            om2.MGlobal.displayInfo("Success: Attributes connected `{}` to `{}` for `{}` ".format(driverAttr,
                                                                                                  drivenAttr,
                                                                                                  selObjs))
    return success


def makeSrtConnectionsObjs(objList, translate=True, rotation=True, scale=True, matrix=False, message=True):
    """Convenience function for making SRT connections between the first obj, and all others in a list

    :param objList: A list of Maya node names, the first node will be the master
    :type objList: list(str)
    :param translate: Connect all translate values?
    :type translate: bool
    :param rotation: Connect all rotation values?
    :type rotation: bool
    :param scale: Connect all scale values?
    :type scale: bool
    :param matrix: Connect .matrix to .offsetParentMatrix values?
    :type matrix: bool
    :param message:  Report the messages to the user?
    :type message: bool
    :return translateSuccess: True if connected some (not necessarily all object's) translate attributes
    :rtype translateSuccess: bool
    :return rotateSuccess: True if connected some (not necessarily all object's) rotate attributes
    :rtype rotateSuccess: bool
    :return scaleSuccess: True if connected some (not necessarily all object's) scale attributes
    :rtype scaleSuccess: bool
    :return matrixSuccess: True if connected some (not necessarily all object's) matrix attributes
    :rtype matrixSuccess: bool
    """
    translateSuccess = False
    rotateSuccess = False
    scaleSuccess = False
    matrixSuccess = False
    translateMessage = ""
    rotateMessage = ""
    scaleMessage = ""
    matrixMessage = ""
    if translate:
        translateSuccess = safeConnectList(objList, "translate", "translate")
    if rotation:
        rotateSuccess = safeConnectList(objList, "rotate", "rotate")
    if scale:
        scaleSuccess = safeConnectList(objList, "scale", "scale")
    if matrix:
        matrixSuccess = safeConnectList(objList, "matrix", "offsetParentMatrix")
    if message:
        if translateSuccess:
            translateMessage = "Translation"
        if rotateSuccess:
            rotateMessage = "Rotation"
        if scaleSuccess:
            scaleMessage = "Scale"
        if matrixSuccess:
            matrixMessage = "Matrix"
        if translateSuccess or rotateSuccess or scaleSuccess or matrixSuccess:
            om2.MGlobal.displayInfo("Success: {} {} {} {} connected for {}".format(translateMessage,
                                                                                   rotateMessage,
                                                                                   scaleMessage,
                                                                                   matrixMessage,
                                                                                   objList))
        return translateSuccess, rotateSuccess, scaleSuccess, matrixSuccess


def makeSrtConnectionsObjsSel(rotation=False, translate=False, scale=False, matrix=False, message=True):
    """Convenience function for making SRT connections between the first selected obj, and all others

    :param translate: Connect all translate values?
    :type translate: bool
    :param rotation: Connect all rotation values?
    :type rotation: bool
    :param scale: Connect all scale values?
    :type scale: bool
    :param matrix: Connect matrix to offsetParentMatrix values?
    :type matrix: bool
    :param message:  Report the messages to the user?
    :type message: bool
    :return translateSuccess: True if connected some (not necessarily all object's) translate attributes
    :rtype translateSuccess: bool
    :return rotateSuccess: True if connected some (not necessarily all object's) rotate attributes
    :rtype rotateSuccess: bool
    :return scaleSuccess: True if connected some (not necessarily all object's) scale attributes
    :rtype scaleSuccess: bool
    """
    selObjs = cmds.ls(selection=True, long=True)
    # Filter only transforms since dealing with rot trans and scale
    if not selObjs:
        om2.MGlobal.displayWarning("No objects selected. Please select two or more objects (transforms)")
        return
    selTransforms = cmds.ls(selObjs, type="transform")
    # Do the disconnect
    if not selTransforms:
        om2.MGlobal.displayWarning("No transform objects selected. Please select two or more objects (transforms)")
        return
    if len(selTransforms) < 2:
        om2.MGlobal.displayWarning("Please select two or more objects (transforms)")
        return
    return makeSrtConnectionsObjs(selTransforms, rotation=rotation, translate=translate, scale=scale, matrix=matrix,
                                  message=True)


# ---------------------------
# BREAK CONNECTIONS
# ---------------------------


def breakAttr(objectAttribute):
    """Disconnects using only one attribute, as per right click disconnect in the channel box

    :param objectAttribute: "objectName.objectAttribute" node name and attribute name separated by a "."
    :type objectAttribute: str
    """
    # get the connection of that attribute
    oppositeAttr = (cmds.listConnections(objectAttribute, plugs=True))[0]
    try:
        cmds.disconnectAttr(oppositeAttr, objectAttribute)
        return True
    except RuntimeError:
        pass
    return False


def breakAttrList(objAttrList):
    """Disconnects using only one attribute, as per right click disconnect in the channel box on a list:

        objAttrList: ["pCube1.rotateX", "pCube1.translateY"]

    :param objAttrList: a list of objects with attribute names ie ["pCube1.rotateX", "pCube1.translateY"]
    :type objAttrList: list(str)
    :return success: Will be True if any (not all) attributes are disconnected
    :rtype success: bool
    """
    success = False
    for objAttr in objAttrList:
        if breakAttr(objAttr):
            success = True
    return success


def breakConnectionSourceDestination(sourceObj, sourceAttr, destinationObj, destinationAttr):
    """Breaks a connection, with checks to see if it exists.  Must be in the correct order, source and destination

    Can use breakConnectionsTwoObj()  if you do not know the source and destination order

    :param sourceObj:  The source node name
    :type sourceObj: str
    :param sourceAttr: The source node attribute
    :type sourceAttr: str
    :param destinationObj: The destination node name
    :type destinationObj: str
    :param destinationAttr: The destination node attribute
    :type destinationAttr: str
    :return success: Reports True if the connection was disconnected
    :rtype success: bool
    """
    destinationObjAttr = "{}.{}".format(destinationObj, destinationAttr)
    sourceObjAttr = "{}.{}".format(sourceObj, sourceAttr)
    sourceConnections = cmds.listConnections(destinationObjAttr, destination=False, source=True, plugs=True)
    if sourceConnections:
        if sourceObjAttr in sourceConnections:  # then yes confirmed
            cmds.disconnectAttr(sourceObjAttr, destinationObjAttr)
            return True
    return False


def breakConnectionsTwoObj(objOne, objOneAttr, objTwo, objTwoAttr):
    """Breaks a connection, with checks to see if it exists.  The destination/source order does not matter, tries both.

    :param objOne: A node name
    :type objOne: str
    :param objOneAttr: The node one attribute
    :type objOneAttr: str
    :param objTwo: Another node name
    :type objTwo: str
    :param objTwoAttr: The node two attribute
    :type objTwoAttr: str
    :return success: Reports True if the connection was broken
    :rtype success: bool
    """
    if not breakConnectionSourceDestination(objOne, objOneAttr, objTwo, objTwoAttr):  # Try the inverse
        if not breakConnectionSourceDestination(objTwo, objTwoAttr, objOne, objOneAttr):
            return False
    return True


def breakConnectionsList(objList, sourceAttr, destinationAttr, message=True):
    """Safely breaks the connection between the first object from the remaining objects.

    :param objList: A list of Maya nodes
    :type objList: list(str)
    :param sourceAttr: The source attribute (the from attribute) of the first object only
    :type sourceAttr: str
    :param destinationAttr: The destination attribute to be connected on all remaining objects (not first)
    :type destinationAttr: str
    :param message: Report the message to the user?
    :type message: bool
    :return success: Will report True if any (not all) connections were broken successfully
    :rtype success: bool
    """
    success = False
    objList = namehandling.getUniqueShortNameList(objList)
    sourceObj = objList.pop(0)
    for obj in objList:
        if breakConnectionsTwoObj(sourceObj, sourceAttr, obj, destinationAttr):
            success = True
    return success


def breakConnectionsSelection(sourceAttr, destinationAttr, message=True):
    """Safely breaks the connection between the first object from the remaining objects from the selection

    :param sourceAttr: The source attribute (the from attribute) of the first object only
    :type sourceAttr: str
    :param destinationAttr: The destination attribute to be connected on all remaining objects (not first)
    :type destinationAttr: str
    :param message: Report the message to the user?
    :type message: bool
    :return success: Will report True if any (not all) connections were broken successfully
    :rtype success: bool
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        if message:
            om2.MGlobal.displayWarning("No objects selected. Please select two or more objects or nodes")
        return False
    if len(selObjs) < 2:
        if message:
            om2.MGlobal.displayWarning("Please select two or more objects or nodes")
        return False
    return breakConnectionsList(selObjs, sourceAttr, destinationAttr, message=message)


def breakConnectionAttrsOrChannelBox(driverAttr="", drivenAttr="", message=True):
    if driverAttr and drivenAttr:  # don't worry about channel box selection, both names have been entered
        return breakConnectionsSelection(driverAttr, drivenAttr, message=True)
    # Both names not entered so do from the selected objects and the channel box attribute selection
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        if message:
            om2.MGlobal.displayWarning("No objects selected. Please select two or more objects or nodes")
        return False
    # Get the channel box attribute selection
    selAttrs = mel.eval('selectedChannelBoxAttributes')
    if not selAttrs:
        if message:
            om2.MGlobal.displayWarning("Please fill in both Driver and Driven attributes, or select in channel box")
        return False
    if driverAttr:  # Then driven attr is missing -----------------------------------
        drivenAttr = selAttrs[0]
        mel.eval('channelBoxCommand -break;')  # TODO bad mel code doesn't allow for unselecting the driver obj
        success = True
    elif drivenAttr:  # Then driver attr is missing -----------------------------------
        if len(selAttrs) != 1:
            if message:
                om2.MGlobal.displayWarning("Please select only one channel in the channel box, "
                                           "can only have one driver attribute")
            return False
        driverAttr = selAttrs[0]
        success = breakConnectionsList(selObjs, driverAttr, drivenAttr, message=message)
    else:  # Neither exists so just break channel selection -----------------------------------
        driverAttr = selAttrs[0]
        drivenAttr = selAttrs[0]
        mel.eval('channelBoxCommand -break;')  # TODO bad mel code doesn't allow for unselecting the driver obj
        success = True
    if success:
        if message:
            om2.MGlobal.displayInfo("Success: Attributes broken `{}` to `{}` for `{}` ".format(driverAttr,
                                                                                               drivenAttr,
                                                                                               selObjs))
    return


def breakAllDrivenOrChannelBoxSel(message=True):
    """Breaks all the connections on the selection,
    or if channel box has attr selections only break those selected connections

    :param message: Report messages to the user
    :type message: bool
    :return success: True if all operations were successfully completed
    :rtype success: bool
    """
    selObjs = cmds.ls(selection=True, long=True)
    # Filter only transforms since dealing with rot trans and scale
    if not selObjs:
        if message:
            om2.MGlobal.displayWarning("No objects selected. Select object/s and channel box attributes "
                                       "to break connections")
        return False
    # get the selection from the channel box
    selAttrs = mel.eval('selectedChannelBoxAttributes')
    if selAttrs:  # Attributes are selected in the channel box
        mel.eval('channelBoxCommand -break;')
        if message:
            om2.MGlobal.displayInfo("Attributes disconnected from Channel Box selection")
        return True
    # Attributes are not selected so break all
    return breakAllConnectionsObjList(selObjs, message=message)


def breakAllConnectionsObj(obj, message=True):
    """Breaks all the driven connections from an object or node

    :param obj: A Maya object or node
    :type obj: list(str)
    :param message: Report the message to the user?
    :type message: bool
    :return success: True if all connections were broken, will fail if any objects fail
    :rtype success: bool
    """
    success = True
    destinationAttrs = getDestinationAttrs(obj, message=message)
    for objAttr in destinationAttrs:
        if not breakAttr(objAttr):
            success = False
            if message:
                om2.MGlobal.displayWarning("`{}` could not be disconnected".format(objAttr))
    if success and message:
        om2.MGlobal.displayInfo("All attributes disconnected for `{}`".format(obj))
    return success


def breakAllConnectionsObjList(objList, message=True):
    """Breaks all the driven connections from an object list

    :param objList: A list of Maya objects or nodes
    :type objList: list(str)
    :param message: Report the message to the user?
    :type message: bool
    :return success: True if all connections were broken, will fail if any objects fail
    :rtype success: bool
    """
    success = True
    for obj in objList:
        if not breakAllConnectionsObj(obj, message=message):
            success = False
    if success and message:
        om2.MGlobal.displayInfo("All attributes disconnected for `{}`".format(objList))
    return success


def breakAllConnectionsSel(objList, message=True):
    """Breaks all the driven connections from all selected objects

    :param objList: A list of Maya objects or nodes
    :type objList: list(str)
    :param message: Report the message to the user?
    :type message: bool
    :return success: True if all connections were broken, will fail if any objects fail
    :rtype success: bool
    """
    selObjs = cmds.ls(selection=True, long=True)
    # Filter only transforms since dealing with rot trans and scale
    if not selObjs:
        om2.MGlobal.displayWarning("No objects selected. Please select object/s to break connections")
        return False
    return breakAllConnectionsObjList(objList, message=message)


def breakSrtConnectionsObjs(objList, translate=False, rotation=False, scale=False, matrix=False, message=True):
    """Convenience function for breaking SRT connections between the first obj, and all others in a list

    :param objList: A list of Maya node names, the first node will be the master
    :type objList: list(str)
    :param translate: Disconnect all translate values?
    :type translate: bool
    :param rotation: Disconnect all rotation values?
    :type rotation: bool
    :param scale: Disconnect all scale values?
    :type scale: bool
    :param matrix: Disconnect the matrix connections?
    :type matrix: bool
    :param message:  Report the messages to the user?
    :type message: bool
    :return translateSuccess: True if disconnected some (not necessarily all) translate attributes
    :rtype translateSuccess: bool
    :return rotateSuccess: True if disconnected some (not necessarily all) rotate attributes
    :rtype rotateSuccess: bool
    :return scaleSuccess: True if disconnected some (not necessarily all) scale attributes
    :rtype scaleSuccess: bool
    """
    translateSuccess = False
    rotateSuccess = False
    scaleSuccess = False
    matrixSuccess = False
    translateMessage = ""
    rotateMessage = ""
    scaleMessage = ""
    matrixMessage = ""
    objList = namehandling.getUniqueShortNameList(objList)
    masterObj = objList.pop(0)
    for obj in objList:
        if translate:
            if breakConnectionsTwoObj(masterObj, "translate", obj, "translate"):
                translateSuccess = True
        if rotation:
            if breakConnectionsTwoObj(masterObj, "rotate", obj, "rotate"):
                rotateSuccess = True
        if scale:
            if breakConnectionsTwoObj(masterObj, "scale", obj, "scale"):
                scaleSuccess = True
        if matrix:
            if breakConnectionsTwoObj(masterObj, "matrix", obj, "offsetParentMatrix"):
                matrixSuccess = True
    if message:
        if translateSuccess:
            translateMessage = "Translation"
        if rotateSuccess:
            rotateMessage = "Rotation"
        if scaleSuccess:
            scaleMessage = "Scale"
        if matrixSuccess:
            matrixMessage = "Matrix"
        if translateSuccess or rotateSuccess or scaleSuccess or matrixSuccess:
            objList = [masterObj] + objList
            om2.MGlobal.displayInfo("Success: {} {} {} {} disconnected for {}".format(translateMessage,
                                                                                      rotateMessage,
                                                                                      scaleMessage,
                                                                                      matrixMessage,
                                                                                      objList))
    return translateSuccess, rotateSuccess, scaleSuccess


def delSrtConnectionsObjsSel(rotation=False, translate=False, scale=False, matrix=False, message=True):
    """Convenience function for breaking SRT connections between the first selected obj, and all others

    :param translate: Disconnect all translate values?
    :type translate: bool
    :param rotation: Disconnect all rotation values?
    :type rotation: bool
    :param scale: Disconnect all scale values?
    :type scale: bool
    :param matrix: Disconnect the matrix connections?
    :type matrix: bool
    :param message:  Report the messages to the user?
    :type message: bool
    :return translateSuccess: True if disconnected some (not necessarily all) translate attributes
    :rtype translateSuccess: bool
    :return rotateSuccess: True if disconnected some (not necessarily all) rotate attributes
    :rtype rotateSuccess: bool
    :return scaleSuccess: True if disconnected some (not necessarily all) scale attributes
    :rtype scaleSuccess: bool
    """
    selObjs = cmds.ls(selection=True, long=True)
    # Filter only transforms since dealing with rot trans and scale
    if not selObjs:
        om2.MGlobal.displayWarning("No objects selected. Please select two or more objects (transforms)")
        return
    selTransforms = cmds.ls(selObjs, type="transform")
    # Do the disconnect
    if not selTransforms:
        om2.MGlobal.displayWarning("No transform objects selected. Please select two or more objects (transforms)")
        return
    if len(selTransforms) < 2:
        om2.MGlobal.displayWarning("Please select two or more objects (transforms)")
        return
    return breakSrtConnectionsObjs(selTransforms, rotation=rotation, translate=translate, scale=scale, matrix=matrix,
                                   message=True)


# ---------------------------
# SWAP CONNECTIONS DRIVER/DRIVEN
# ---------------------------


def swapDriverConnection(currentDriver, newDriver):
    """Swaps the driver object to a new object, the newDriver object will have all connections.

    :param currentDriver:  Maya node name, a current driver with outgoing connections
    :type currentDriver: str
    :param newDriver: Maya node name, a new driver to replace currentDriver
    :type newDriver: str
    :return success: True if the swap was successful
    :rtype success: bool
    """
    sourceAttributes = list()
    # Find the destination connections of the current driver
    destinationAttributes = cmds.listConnections(currentDriver, destination=True, source=False, plugs=True)
    if not destinationAttributes:
        om2.MGlobal.displayWarning("Node `{}` has no outgoing connections ".format(currentDriver))
        return False
    # Get the source attributes, this must pass
    for objAttr in destinationAttributes:
        sourceAttributes.append(cmds.listConnections(objAttr, destination=False, source=True, plugs=True)[0])
    # Check the new object has the same attributes
    for objAttr in sourceAttributes:
        attr = objAttr.split(".")[1]  # just the attribute name
        if not cmds.attributeQuery(attr, node=newDriver, exists=True):
            # TODO: report actual missing attributes
            om2.MGlobal.displayWarning("Node `{}` does not have all the attributes "
                                       "for switching `{}` ".format(newDriver, sourceAttributes))
            return False
    # Break attrs
    breakAttrList(destinationAttributes)
    # Connect new attrs
    for i, sourceAttr in enumerate(sourceAttributes):
        attr = sourceAttr.split(".")[1]  # just the attribute name
        cmds.connectAttr(".".join([newDriver, attr]), destinationAttributes[i])
    return True


def swapDrivenConnection(currentDriven, newDriven):
    """Swaps the driven/target object to a new object, the newDriven object will have all connections.

    :param currentDriven:  Maya node name, a current driven with outgoing connections
    :type currentDriven: str
    :param newDriven: Maya node name, a new driven to replace currentDriven
    :type newDriven: str
    :return success: True if the swap was successful
    :rtype success: bool
    """
    sourceObAttrs, destinationObjAttrs = getDestinationSourceAttrs(currentDriven)
    # Check the new object has the same attributes
    for objAttr in destinationObjAttrs:
        attr = objAttr.split(".")[1]  # just the attribute name
        if not cmds.attributeQuery(attr, node=newDriven, exists=True):
            # TODO: report actual missing attributes
            om2.MGlobal.displayWarning("Node `{}` does not have all the attributes "
                                       "for switching `{}` ".format(newDriven, destinationObjAttrs))
            return False
    # Break attrs
    breakAttrList(destinationObjAttrs)
    # Connect new attrs
    for i, destinationAttr in enumerate(destinationObjAttrs):
        destAttr = destinationAttr.split(".")[1]  # just the attribute name
        sourceAttrParts = sourceObAttrs[i].split(".")
        # safe connect as may have connections already
        makeSafeConnectionsTwoObjs(sourceAttrParts[0], sourceAttrParts[1], newDriven, destAttr)
    return True


def swapConnectionSelected(driver=True, message=True):
    """Swaps the first (driver/driven) object to a new unrelated object, the second object will receive/emit all \
    connections.

    Can only swap two objects if driven

    driver: If True the driver (source) attributes will be swapped

    :param driver: True if the driver object should be switched, False is driven
    :type driver: bool
    :param message: report the message to the user?
    :type message: bool
    :return success: True if the swap was successful for some objects
    :rtype success: bool
    """
    selObjs = cmds.ls(selection=True, long=True)
    # Filter only transforms since dealing with rot trans and scale
    if not selObjs:
        om2.MGlobal.displayWarning("No objects selected. Please select")
        return False
    if driver and len(selObjs) <= 1:
        om2.MGlobal.displayWarning("Please select two or more objects or nodes")
        return False
    if not driver and len(selObjs) != 2:
        om2.MGlobal.displayWarning("Please select two objects or nodes")
        return False
    # Do the switch
    if driver:
        swapDriverConnection(selObjs[0], selObjs[1])
    else:
        swapDrivenConnection(selObjs[0], selObjs[1])


# ---------------------------
# SWAP DIRECTION
# ---------------------------


def getConnectionsBetweenNodes(objA, objB, message=True):
    """Returns the connections between two objects

    Will only the first direction found, nodes should not be connected in different directions (source/destination)

    :param objA: Maya object or node name, preferably a long or unique name
    :type objA: str
    :param objB: Maya object or node name, preferably a long or unique name
    :type objB: str
    :param message: Report the message to the user?
    :type message: bool
    :return sourceAttrList: The source connections as object.attribute eg "pCube1.rotate"
    :rtype sourceAttrList: str
    :return destinationAttrList: The destination connections as object.attribute eg "pCube1.rotate"
    :rtype destinationAttrList: str
    """
    destinationAttrList = list()
    sourceAttrList = list()
    # Must be unique names to match
    objA = namehandling.getUniqueShortName(objA)
    objB = namehandling.getUniqueShortName(objB)
    # List destination attrs of objA
    objADestinationAttrs = cmds.listConnections(objA, destination=True, source=False, plugs=True)
    for objAttr in objADestinationAttrs:
        if objB == objAttr.split(".")[0]:
            destinationAttrList.append(objAttr)
    if not destinationAttrList:  # try inverse
        # List destination attrs of objB
        objBDestinationAttrs = cmds.listConnections(objB, destination=True, source=False, plugs=True)
        for objAttr in objBDestinationAttrs:
            if objA == objAttr.split(".")[0]:
                destinationAttrList.append(objAttr)
                # Get the source attributes, this must pass
    if destinationAttrList:  # Then get the source attrs
        for objAttr in destinationAttrList:
            sourceAttrList.append(cmds.listConnections(objAttr, destination=False, source=True, plugs=True)[0])
    return sourceAttrList, destinationAttrList


def swapConnectionDirection(objA, objB, message=True):
    """Swaps connection directions between two objects.  Attributes must exist for the switch to take place.

    :param objA: Maya object or node name, preferably a long or unique name
    :type objA: str
    :param objB: Maya object or node name, preferably a long or unique name
    :type objB: str
    :param message: Report the message to the user?
    :type message: bool
    :return success: True if the switch took place
    :rtype success: bool
    """
    sourceAttrList, destinationAttrList = getConnectionsBetweenNodes(objA, objB, message=True)
    if not destinationAttrList:
        if message:
            om2.MGlobal.displayWarning("No connections found between `{}` and `{}`".format(objA, objB))
        return False
    # Check all attributes exist when switched
    for i, sourceObjAttr in enumerate(sourceAttrList):
        destParts = destinationAttrList[i].split(".")
        sourceParts = sourceObjAttr.split(".")
        sourceExists = cmds.attributeQuery(destParts[1], node=sourceParts[0], exists=True)
        destinationExists = cmds.attributeQuery(sourceParts[1], node=destParts[0], exists=True)
        if not sourceExists:
            if message:
                om2.MGlobal.displayWarning("Node `{}` has no attribute `{}` and cannot be "
                                           "switched".format(sourceParts[0], destParts[1]))
            return False
        if not destinationExists:
            if message:
                om2.MGlobal.displayWarning("Node `{}` has no attribute `{}` and cannot be "
                                           "switched".format(destParts[0], sourceParts[1]))
            return False
    # Break connections so can be reconnected
    for i, sourceObjAttr in enumerate(sourceAttrList):
        cmds.disconnectAttr(sourceObjAttr, destinationAttrList[i])
    # Connect Reverse Direction
    for i, sourceObjAttr in enumerate(sourceAttrList):
        cmds.connectAttr(destinationAttrList[i], sourceObjAttr)
    if message:
        om2.MGlobal.displayInfo("Success: Node connections switched direction `{}` and "
                                "`{}`".format(objA, objB))
    return True


def swapConnectionDirectionSel(message=True):
    """Swaps connection directions between two selected objects.  Attributes must exist for the switch to take place.

    :param message: Report the message to the user?
    :type message: bool
    :return success: True if the switch took place
    :rtype success: bool
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        if message:
            om2.MGlobal.displayWarning(
                "No object selected to switch attributes. Please select two objects or nodes")
        return False
    if len(selObjs) != 2:
        if message:
            om2.MGlobal.displayWarning(
                "{} node selected.  Please select 2 objects or nodes".format(str(len(selObjs))))
        return False
    return swapConnectionDirection(selObjs[0], selObjs[1], message=True)


# ---------------------------
# COPY PASTE CONNECTIONS
# ---------------------------


def copyDrivenConnectedAttrs(obj, message=True):
    """Copy driven attributes.  Used in copy attributes GUI command

    Returns:

        1. The sources for connected attributes, from the driving object/s list(object.attribute)
        2. All the driven attributes, ie those attributes with a connection incoming to the node list(attributeNames)

    :param obj: A node that has incoming connections.  Ie is a driven object
    :type obj: str
    :param message: Report messages to the user?
    :type message: bool
    :return sourceObjAttrs: The sources for connected attributes, from the driving object/s list(object.attribute)
    :rtype sourceObjAttrs: list(str)
    :return destinationAttrs: All the driven attributes, attributes with an incoming connection list(attributeNames)
    :rtype destinationAttrs: list(str)
    """
    destinationAttrs = list()
    sourceObjAttrs, destObjAttrs = getDestinationSourceAttrs(obj)
    for obAttr in destObjAttrs:
        destinationAttrs.append(obAttr.split(".")[1])
    if destinationAttrs:
        if message:
            om2.MGlobal.displayInfo("Success: Copied `{}` connected attributes `{}`".format(obj, destinationAttrs))
    else:
        if message:
            om2.MGlobal.displayWarning("No incoming connections found on `{}`, no data copied.".format(obj))
    return sourceObjAttrs, destinationAttrs


def copyDrivenConnectedAttrsSel(message=True):
    """Copy driven attributes for the first selected object.  Used in copy attributes GUI command

    Returns:

        1. The sources for those attributes, from the driving object/s list(object.attribute)
        2. All the driven attributes, ie those attributes with a connection incoming to the node list(attributeNames)

    :param message: Report messages to the user?
    :type message: bool
    :return sourceObjAttrs: The sources for connected attributes, from the driving object/s list(object.attribute)
    :rtype sourceObjAttrs: list(str)
    :return destinationAttrs: All the driven attributes, attributes with an incoming connection list(attributeNames)
    :rtype destinationAttrs: list(str)
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        if message:
            om2.MGlobal.displayWarning("No object selected to copy connected attributes. Please select")
        return list(), list()
    return copyDrivenConnectedAttrs(selObjs[0], message=message)  # User messages in this function


def pasteDrivenConnectedAttrs(objList, sourceObjAttrs, destinationAttrs, message=True):
    """Paste connects a list of destinationAttrs onto all objects.  From sourceObjAttrs

    All objects must have all attributes

    :param objList: A list of Maya objects/nodes
    :type objList: list(str)
    :param sourceObjAttrs: The sources for connected attributes, from the driving object/s list(object.attribute)
    :type sourceObjAttrs: list(str)
    :param destinationAttrs: All the driven attributes, attributes with an incoming connection list(attributeNames)
    :type destinationAttrs: list(str)
    :param message: Report messages to the user?
    :type message: bool
    :return success: True if successfully completed
    :rtype success: bool
    """
    # Check the new object has the same attributes
    for obj in objList:
        for attr in destinationAttrs:
            if not cmds.attributeQuery(attr, node=obj, exists=True):
                # TODO: report all missing attributes
                if message:
                    om2.MGlobal.displayWarning("Node `{}` does not have all the attributes "
                                               "for switching `{}` missing".format(obj, attr))
                return False
    for obj in objList:
        for i, destAttr in enumerate(destinationAttrs):
            sourceAttrParts = sourceObjAttrs[i].split(".")
            # safe connect as may have connections already
            makeSafeConnectionsTwoObjs(sourceAttrParts[0], sourceAttrParts[1], obj, destAttr)
    if message:
        om2.MGlobal.displayInfo("Success attributes connected `{}` on objects ``".format(destinationAttrs, objList))
    return True


def pasteDrivenConnectedAttrsSel(sourceObjAttrs, destinationAttrs, message=True):
    """Paste connects a list of destinationAttrs onto all selected objects.  From sourceObjAttrs

    All objects must have all attributes.  Used in GUI command

    :return sourceObjAttrs: The sources for connected attributes, from the driving object/s list(object.attribute)
    :rtype sourceObjAttrs: list(str)
    :return destinationAttrs: All the driven attributes, attributes with an incoming connection list(attributeNames)
    :rtype destinationAttrs: list(str)
    :param message: Report messages to the user?
    :type message: bool
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        if message:
            om2.MGlobal.displayWarning("No object selected to copy connected attributes. Please select")
        return list(), list()
    # User messages in copyDrivenConnectedAttrs()
    return pasteDrivenConnectedAttrs(selObjs, sourceObjAttrs, destinationAttrs, message=message)

