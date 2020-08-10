import maya.cmds as cmds
import maya.api.OpenMaya as om2

from zoo.libs.maya.cmds.animation import animobjects


def createTurntable(rotateGrp, start=0, end=200, spinValue=360, startValue=0, attr='rotateY',
                    tangent="spline", prePost="linear", setTimerange=True, reverse=False, angleOffset=0):
    """Creates a spinning object 360 degrees, useful for turntables

    :param rotateGrp: the group name to animate
    :type rotateGrp: str
    :param start: the start frame
    :type start: float
    :param end: the end frame
    :type end: float
    :param spinValue: the value to spin, usually 360
    :type spinValue: float
    :param startValue: the start value usually 0
    :type startValue: float
    :param attr: the attribute to animate, usually "rotateY"
    :type attr: str
    :param tangent: the tangent type "spline", "linear", "fast", "slow", "flat", "stepped", "step next" etc
    :type tangent: str
    :param prePost: the infinity option, linear forever?  "constant", "linear", "cycle", "cycleRelative" etc
    :type prePost: str
    :param setTimerange: do you want to set Maya's timerange to the in (+1) and out at the same time?
    :type setTimerange: bool
    :param angleOffset: the angle offset of the keyframes in degrees, will change the start rotation of the asset
    :type angleOffset: float
    :param reverse: reverses the spin direction
    :type reverse: bool
    :return rotateGrp: the grp/object now with keyframes
    :rtype rotateGrp: str
    """
    cmds.cutKey(rotateGrp, time=(-10000, 100000), attribute=attr)  # delete if any keys on that attr
    startValue = startValue + angleOffset
    if reverse:  # spins the other way -360
        spinValue *= -1
    endValue = spinValue + angleOffset
    cmds.setKeyframe(rotateGrp, time=start, value=startValue, breakdown=0, attribute=attr,
                     inTangentType=tangent, outTangentType=tangent)
    cmds.setKeyframe(rotateGrp, time=end, value=endValue, breakdown=0, attribute=attr,
                     inTangentType=tangent, outTangentType=tangent)
    cmds.setInfinity(rotateGrp, preInfinite=prePost, postInfinite=prePost)
    if setTimerange:
        cmds.playbackOptions(minTime=start + 1, maxTime=end)  # +1 makes sure the cycle plays without repeated frame
    return rotateGrp


def turntableSelectedObj(start=0, end=200, spinValue=360, startValue=0, attr='rotateY', tangent="spline",
                         prePost="linear", setTimerange=True, angleOffset=0, reverse=False, message=True):
    """Creates a turntable by spinning the selected object/s by 360 degrees

    :param rotateGrp: the group name to animate
    :type rotateGrp: str
    :param start: the start frame
    :type start: float
    :param end: the end frame
    :type end: float
    :param spinValue: the value to spin, usually 360
    :type spinValue: float
    :param startValue: the start value usually 0
    :type startValue: float
    :param attr: the attribute to animate, usually "rotateY"
    :type attr: str
    :param tangent: the tangent type "spline", "linear", "fast", "slow", "flat", "stepped", "step next" etc
    :type tangent: str
    :param prePost: the infinity option, linear forever?  "constant", "linear", "cycle", "cycleRelative" etc
    :type prePost: str
    :param setTimerange: do you want to set Maya's timerange to the in (+1) and out at the same time?
    :type setTimerange: bool
    :param angleOffset: the angle offset of the keyframes in degrees, will change the start rotation of the asset
    :type angleOffset: float
    :param reverse: reverses the spin direction
    :type reverse: bool
    :param message: report the message to the user in Maya
    :type message: bool
    :return rotateObjs: the grp/objects now with keyframes
    :rtype rotateGrp: list
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        om2.MGlobal.displayWarning("No Objects Selected. Please Select An Object/s")
        return
    for obj in selObjs:
        createTurntable(obj, start=start, end=end, spinValue=spinValue, startValue=startValue, attr=attr,
                        tangent=tangent, prePost=prePost, setTimerange=setTimerange, angleOffset=angleOffset,
                        reverse=reverse)
    if message:
        om2.MGlobal.displayInfo("Turntable Create on:  {}".format(selObjs))
    return selObjs


def deleteTurntableSelected(attr="rotateY", returnToZeroRot=True, message=True):
    """Deletes a turntable animation of the selected obj/s. Ie. Simply deletes the animation on the rot y attribute

    :param attr: The attribute to delete all keys
    :type attr: str
    :param returnToZeroRot: Return the object to default zero?
    :type returnToZeroRot: bool
    :param message: Report the messages to the user in Maya?
    :type message: bool
    :return assetGrps: The group/s now with animation
    :rtype assetGrps: list
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        om2.MGlobal.displayWarning("No Objects Selected. Please Select An Object/s")
        return
    for obj in selObjs:
        cmds.cutKey(obj, time=(-10000, 100000), attribute=attr)  # delete all keys rotY
    if returnToZeroRot:
        cmds.setAttr(".".join([obj, attr]), 0)
    if message:
        om2.MGlobal.displayInfo("Turntable Keyframes deleted on:  {}".format(selObjs))
    return selObjs


def toggleAndKeyVisibility():
    """Inverts the visibility of an object in Maya and keys it's visibility attribute
    Works on selected objects. Example:

        "cube1.visibility True"
        becomes
        "cube1.visibility False"
        and the visibility attribute is also keyed

    """
    selObjs = cmds.ls(selection=True)
    for obj in selObjs:
        if cmds.getAttr("{}.visibility".format(obj)):  # if visibility is True
            cmds.setAttr("{}.visibility".format(obj), 0)
        else:  # False so set visibility to True
            cmds.setAttr("{}.visibility".format(obj), 1)
        cmds.setKeyframe(obj, breakdown=False, hierarchy=False, attribute="visibility")


def animRetimer(startRange=0, endRange=100, timeScale=1.0, snapKeys=True, message=True, wholeScene=False):
    """Numeric time scale of keyframes within a time range, will ripple offset the keys after the endRange

    Time scale is in Maya scale float:

        1.0 is 100% speed (same speed)
        0.5 is 200% speed (or twice as fast)
        2.0 is 50% speed (or twice as slow)

    Can also be scaled by:

        Frames Per Second: See the function animRetimerFps()
        Percentage: See the function animRetimerPercentage()

    :param startRange: The start frame of the section to re-time
    :type startRange: float
    :param endRange: The end frame of the section to re-time
    :type endRange: float
    :param timeScale: The scale of the section of keyframes between startRange - endRange.  in Maya units 1.0 is 100%
    :type timeScale: bool
    :param snapKeys: True if the user wants to snap keyframes to whole frames after scaling
    :type snapKeys: bool
    :param message: report the message back to the user?
    :type message: bool
    :param wholeScene: affect all animated objects in the entire scene
    :type wholeScene: bool
    """
    endOfTime = 1000000000
    animRange = endRange - startRange
    moveKeys = (animRange - (animRange * timeScale)) * -1
    if wholeScene:  # then affect all animated objects in the scene
        rememberSelection = cmds.ls(selection=True)
        animObjs = animobjects.getAnimatedNodes(selectFlag="all", message=False, select=True)  # select all anim objs
        if not animObjs:
            om2.MGlobal.displayWarning("No animated objects in the scene were found")
            cmds.select(rememberSelection, replace=True)
            return
    # Check for any active curves/keyframe data on the current selection
    curvesActive = cmds.keyframe(query=True, name=True)
    if not curvesActive:  # then bail no keys found
        if message:
            om2.MGlobal.displayWarning("No FCurves active, please select objects with keyframes")
        return
    if not wholeScene:  # then check for selected curves on sel objs, "wholeScene True" this should be ignored
        selCurves = cmds.keyframe(query=True, name=True, selected=True)
        if not selCurves:  # No selected curves so use the active curves instead
            curvesActive = selCurves
    # Do the logic
    if moveKeys > 0:  # If move keys is a positive value
        for curve in curvesActive:  # Move and then scale
            cmds.keyframe(curve, time=((endRange + 1), endOfTime), edit=True, relative=True, timeChange=moveKeys)
            cmds.scaleKey(curve, time=(startRange, endRange), timeScale=timeScale, timePivot=startRange)
    else:  # If move keys is negative switch order: Scale, then move
        for curve in curvesActive:  # Scale and then move
            cmds.scaleKey(time=(curve, startRange, endRange), timeScale=timeScale, timePivot=startRange)
            cmds.keyframe(time=(curve, (endRange + 1), endOfTime), edit=True, relative=True, timeChange=moveKeys)
    if snapKeys:  # Snap keys to integer time
        for curve in curvesActive:
            cmds.snapKey(curve, timeMultiple=True)
    if wholeScene:  # return to original selection
        cmds.select(rememberSelection, replace=True)


def animRetimerFps(startRange=0.0, endRange=100.0, scaleFps=24.0, sceneFps=24.0, snapKeys=True, message=True,
                   wholeScene=False):
    """Numeric time scale of keyframes within a time range, will ripple offset the keys after the endRange

    Time scale is in `Frames Per Second` as per Final Cut, if the scene time code is 24fps then:

        24fps scales in Maya as 1.0 (same speed)
        48 scales in Maya as 0.5 (or twice as fast)
        12 scales in Maya as 2.0 (or twice as slow)

    Can also be scaled by:

        Maya float: See the function animRetimer()
        Percentage: See the function animRetimerPercentage()

    :param startRange: The start frame of the section to re-time
    :type startRange: float
    :param endRange: The end frame of the section to re-time
    :type endRange: float
    :param scaleFps: The main scale value to scale by 48fps (at scene 24fps) will be twice as fast or 0.5
    :type scaleFps: float
    :param sceneFps: The base frames per second of the whole scene
    :type sceneFps: float
    :param snapKeys: True if the user wants to snap keyframes to whole frames after scaling
    :type snapKeys: bool
    :param message: report the message back to the user?
    :type message: bool
    :param wholeScene: affect all animated objects in the entire scene
    :type wholeScene: bool
    """
    timeScale = 1 / (scaleFps / sceneFps)  # 1 / (48 / 24) = 0.5  or twice as fast for this section
    animRetimer(startRange=startRange, endRange=endRange, timeScale=timeScale, snapKeys=snapKeys, message=message,
                wholeScene=wholeScene)


def animRetimerPercentage(startRange=0, endRange=100, scalePercentage=24, snapKeys=True, message=True,
                          wholeScene=False):
    """Numeric time scale of keyframes within a time range, will ripple offset the keys after the endRange

    Time scale is in a percentage as per Adobe Premiere:

        100% scales in Maya as 1.0 (same speed)
        50% scales in Maya as 2.0  (or twice as slow)
        200% scales in Maya as 0.5 (or twice as fast)

    Can also be scaled by:

        Maya float: See the function animRetimer()
        Frames Per Second: See the function animRetimerFps()

    :param startRange: The start frame of the section to re-time
    :type startRange: float
    :param endRange: The end frame of the section to re-time
    :type endRange: float
    :param scalePercentage: The scale as a percentage like Adobe Premiere.  200% is twice as fast or 0.5 in Maya units
    :type scalePercentage: float
    :param snapKeys: True if the user wants to snap keyframes to whole frames after scaling
    :type snapKeys: bool
    :param message: report the message back to the user?
    :type message: bool
    :param wholeScene: affect all animated objects in the entire scene
    :type wholeScene: bool
    """
    timeScale = 100 / scalePercentage  # 100 / 50 = 2.0
    animRetimer(startRange=startRange, endRange=endRange, timeScale=timeScale, snapKeys=snapKeys, message=message,
                wholeScene=wholeScene)

