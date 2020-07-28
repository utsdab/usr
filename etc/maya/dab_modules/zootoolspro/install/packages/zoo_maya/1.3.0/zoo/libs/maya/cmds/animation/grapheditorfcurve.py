import maya.cmds as cmds
import maya.api.OpenMaya as om2

def convertKeyIndexList(keyIndexList):
    """Converts a list(long, long) of keys to a format that cmds python can use list(set(int), set(int))

    Example:

        Converts [2L, 3L] to [(2,2), (3,3)]

    :param keyIndexList: A list of keyframe indices, usually [2L, 3L] as per querying Maya
    :type keyIndexList: list
    :return newKeyIndex:  A new list now in a format that the python command recognises [(2,2), (3,3)]
    :rtype objList: list(set)
    """
    newKeyIndex = list()
    for index in keyIndexList:
        newKeyIndex.append((int(index), int(index)))
    return newKeyIndex


def objFromFCurve():
    """Returns a list of objects connected to a graph curve

    :return objList: list of maya object/node names
    :rtype objList: list(str)
    """
    objList = list()
    curvesSelected = cmds.keyframe(query=True, name=True, selected=True)
    if curvesSelected:
        for curve in curvesSelected:
            objList.append(cmds.listConnections(curve, source=True)[0])
    return list(set(objList))


def selectObjFromFCurve(message=True):
    """Selects objects related to any selected curves in Maya's graph editor.

    :param message: report the message back to the user?
    :type message: bool
    :return objList: list of maya object/node names
    :rtype objList: list(str)
    """
    objList = objFromFCurve()
    if not objList:
        if message:
            om2.MGlobal.displayWarning("Please select graph curves attached to an object/s.")
        return objList
    cmds.select(objList, replace=True)
    return objList


def jumpToSelectedKey(closestKey=10000000.0, closestGap=10000000.0, message=True):
    """Changes the current time in the graph editor (Maya timeline) to match to the closest selected keyframe

    :param closestKey: the default closest keyframe, should default to a very large number
    :type closestKey: float
    :param closestGap: the default closest gap between the closestKey and currentTime, should be very large
    :type closestGap: float
    :param message: report the message back to the user?
    :type message: bool
    :return closestKey: the closest keyframe found, will be None if null
    :rtype closestKey: float
    """
    currentTime = cmds.currentTime(query=True)
    selectedKeys = cmds.keyframe(query=True, selected=True)
    if not selectedKeys:
        if message:
            om2.MGlobal.displayWarning("Please select keyframes in order to move the time slider.")
        return
    for key in selectedKeys:
        tempVal = abs(currentTime - key)  # get keyframe distance from current time to curr key, neg numbers become pos
        if tempVal < closestGap:  # then record this key as the closest key
            closestKey = key
            closestGap = tempVal
    if message:
        om2.MGlobal.displayInfo("Time moved to frame {}.".format(closestKey))
    cmds.currentTime(closestKey)
    return closestKey


def moveKeysSelectedTime(message=True):
    """Moves the selected keys to the current time. The first keyframe matching, maintains the spacing of selection

    :param message: report the message back to the user?
    :type message: bool
    """
    currentTime = cmds.currentTime(query=True)
    selKeys = sorted(cmds.keyframe(query=True, selected=True))  # sort list ordered smallest to largest
    firstKey = selKeys[0]  # smallest number, first in timeline of the selection
    moveAmount = currentTime - firstKey  # difference between first key and current time
    cmds.keyframe(timeChange=moveAmount, relative=True, option='over')  # move
    if message:
        om2.MGlobal.displayInfo("Selected keys moved by {} frames".format(moveAmount))


def animHold(message=True):
    """Creates a held pose with two identical keys and flat tangents intelligently from the current keyframes

    Functionality:

        - For each curve, finds the previous key and copies it to the next keyframe while flattening both tangents.
        - Will work on selected curves only as a priority if curves have been selected
        - If no curve/s are selected then use all default curves, does not need the Graph Editor open
        - Will check if the current attribute values differ from the current curve values (ie object has moved)
        - If finds a mismatch between current curve value and current actual value, then uses the current actual value

    Authors: Original .mel script by David Peers converted to python by Andrew Silke (also co-creator)

    :param message: report the message back to the user?
    :type message: bool
    """
    curveAttrs = list()
    currentAttrVals = list()
    curveAttrVals = list()
    # ---------------
    # Check for any active curves/keyframe data on the current selection
    # ---------------
    curvesActive = cmds.keyframe(query=True, name=True)
    if not curvesActive:  # then bail no keys found
        if message:
            om2.MGlobal.displayWarning("No Curves Active")
        return
    # ---------------
    # Gather Keyframe Data
    # ---------------
    currentTime = cmds.currentTime(query=True)
    selCurves = cmds.keyframe(query=True, name=True, selected=True)
    if not selCurves:  # No selected curves so use the active curves instead
        selCurves = curvesActive
    timePlusOne = currentTime + 1
    lastKey = cmds.findKeyframe(time=(timePlusOne, timePlusOne), which="previous")
    for curve in selCurves:
        curveConnection = cmds.listConnections(curve, plugs=True, source=False)[0]
        curveAttrs.append(curveConnection)  # Attributes list ie pCube3_translateX
        currentAttrVals.append(cmds.getAttr(curveConnection))  # Current attr values, eg. actual obj position
        curveAttrVals.append(cmds.keyframe(curve, query=True, eval=True)[0])  # Current curve value at current frame
    # ---------------
    # Main Logic
    # ---------------
    for i, curve in enumerate(selCurves):
        isLastKey = cmds.keyframe(curve, time=(lastKey, lastKey), query=True, keyframeCount=True)
        if isLastKey == 1:  # then for this curve then there is a key on the frame 'lastKey'
            equivTest = abs(currentAttrVals[i] - curveAttrVals[i]) <= 0.001
            if not equivTest:  # Then there is an unkeyed change in the scene, so set first key to current position
                cmds.setKeyframe(curve, value=currentAttrVals[i], time=(lastKey, lastKey), inTangentType="linear",
                                 outTangentType="linear")
            # Find previous/next keys on the current curve
            lastKey = cmds.findKeyframe(curve, time=(timePlusOne, timePlusOne), which="previous")
            nextKey = cmds.findKeyframe(curve, time=(currentTime, currentTime), which="next")
            # Make the hold
            cmds.keyTangent(curve, time=(lastKey, lastKey), inTangentType="flat", outTangentType="flat")
            cmds.copyKey(curve, time=(lastKey, lastKey))
            cmds.pasteKey(curve, time=(nextKey, nextKey))
            cmds.keyTangent(curve, time=(nextKey, nextKey), inTangentType="flat", outTangentType="flat")
            # Report messages
            if message:
                om2.MGlobal.displayInfo("Created hold on {}".format(curve))
        else:  # then there is no a curve on the frame 'lastKey' so do nothing
            om2.MGlobal.displayInfo("No hold set on {}, no source key on frame".format(curve))


def scaleFromCurveCenter(scaleAmount):
    """Value scales selected keys in the graph editor from the mid point (value scale pivot) of each curve

    Useful for controlling the intensity of random noise on multiple curves, can also be used to invert curves

    :param scaleAmount: the amount to scale the selected keyframes, can be negative numbers or -1.0 for invert
    :type scaleAmount: float
    """
    selCurves = cmds.keyframe(query=True, name=True, selected=True)
    if not selCurves:
        om2.MGlobal.displayWarning("No curves or graph keys are selected. Select keys in the Graph Editor")
        return
    for curve in selCurves:
        # Get the midpoint (scale pivot)
        keyVals = cmds.keyframe(curve, query=True, valueChange=True, selected=True)
        midPoint = (max(keyVals) + min(keyVals)) / 2  # half way point between max and min values
        # Get the selected keys as an index list
        keyIndexList = cmds.keyframe(curve, query=True, indexValue=True, selected=True)
        keyIndexList = convertKeyIndexList(keyIndexList)  # index list must be converted for cmds.scaleKey()
        # Do the scale
        cmds.scaleKey(curve, includeUpperBound=False, index=keyIndexList, valueScale=scaleAmount, valuePivot=midPoint)
