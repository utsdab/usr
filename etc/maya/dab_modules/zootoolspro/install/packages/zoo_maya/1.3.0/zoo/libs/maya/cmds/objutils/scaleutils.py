import maya.cmds as cmds
import maya.api.OpenMaya as om2

from zoo.libs.maya.cmds.objutils import namehandling, shapenodes, matching

def getRawBoundingBox(obj, worldSpace=True):
    """Returns the raw limits in Maya units (cms) of the outer limits of the bounding box in world

    :param obj: The maya object to measure
    :type obj: str
    :return objBoundingBoxRaw: raw world limits of the bounding box Maya units (cms) [-x, -y, -z, +x, +y, +z]
    :rtype objBoundingBoxRaw: list
    """
    if worldSpace:
        return cmds.xform(obj, q=1, boundingBox=1, worldSpace=True)
    else:
        return cmds.xform(obj, q=1, boundingBox=1, objectSpace=True)


def scaleBoundingBox(boundingBox, scaleXYZ):
    """Scales a bounding box by a xyz scale amount

    :param boundingBox: The bounding box to scale a list of 6 floats [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    :type boundingBox: list(float)
    :param scaleXYZ: Scale in x y z (1.0, 2.0, 1.5)
    :type scaleXYZ: list(float)
    :return boundingBox: The new bounding box now scaled
    :rtype boundingBox: list(float)
    """
    for i, value in enumerate(boundingBox):
        if i == 0 or i == 3:  # scale x
            boundingBox[i] *= scaleXYZ[0]
        elif i == 1 or i == 4:  # scale y
            boundingBox[i] *= scaleXYZ[1]
        elif i == 2 or i == 5:  # scale z
            boundingBox[i] *= scaleXYZ[2]
    return boundingBox

def getBoundingBoxNoChildren(obj, worldSpace=True):
    """Measures the bounding box of a transform with no children.  Measures all shape nodes, adds them up to get the \
    total bounding box of the object.

    Result is in objectSpace to the object not it's parent

    :param obj: The maya object to measure
    :type obj: str
    :return boundingBox: raw world limits of the bounding box Maya units (cms) [-x, -y, -z, +x, +y, +z]
    :rtype boundingBox:
    """
    shapeList = cmds.listRelatives(obj, shapes=True, fullPath=True)
    if not shapeList:
        return [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    boundingBoxList = list()
    for shape in shapeList:
        minBoundingBox = cmds.getAttr("{}.boundingBoxMin".format(shape))[0]
        maxBoundingBox = cmds.getAttr("{}.boundingBoxMax".format(shape))[0]
        boundingBoxList.append(minBoundingBox + maxBoundingBox)
    boundingBox = getBoundingBoxMultiple(boundingBoxList)  # get the bounding box of all shape nodes
    if worldSpace:  # temp create a transform to measure the world space scale of the obj
        # TODO: must be a better way of getting the worldspace size
        tempNode = cmds.group(empty=True, name="{}_tempZooXX".format(obj))
        cmds.matchTransform([tempNode, obj], pos=True, rot=True, scl=True, piv=0)
        objScale = cmds.getAttr("{}.scale".format(tempNode))[0]
        cmds.delete(tempNode)
    else:
        objScale = cmds.getAttr("{}.scale".format(obj))[0]
    boundingBox = scaleBoundingBox(boundingBox, objScale)
    return boundingBox


def getBoudingBoxNoChildrenLegacy(obj, worldSpace=True):
    """Duplicate a copy of the current object so that it can be measured in isolation, read warning below.

    WARNING!! This can be bad as shape node is parented in and out of the object. Useful for controls but not polys.
    If the shape nodes are heavy will take time to compute.

    TODO find a better way of managing this

    :param obj: The maya object to measure
    :type obj: str
    :param worldSpace: If True will calculate in world space, if False in local space
    :type worldSpace: bool
    :return boundingBox: raw world limits of the bounding box Maya units (cms) [-x, -y, -z, +x, +y, +z]
    :rtype boundingBox:
    """
    dupObj = shapenodes.duplicateWithoutChildren(obj, name="deleteMeScaleMeasure")
    dupObj, grpName = matching.groupZeroObj(dupObj, freezeScale=True, removeSuffixName="")
    boundingBox = getRawBoundingBox(dupObj, worldSpace=worldSpace)
    cmds.delete([grpName, dupObj])
    return boundingBox

def getLongestBbEdge(bbHWL):
    """returns the longest edge of a height width and length bounding box

    :param bbHWL: height width and length of the bounding box in Maya units (cms) [x, y, z]
    :type bbHWL: list
    :return longestEdge: the longest edge of a height width length bounding box
    :rtype: int
    """
    return max(bbHWL)


def getLongestEdgeObj(obj, worldSpace=True, ignoreChildren=False):
    """Returns the longest edge of the selected object in maya units, will include children in the scale.

    WARNING with the flag ignoreChildren!!
    This can be bad as shape node is parented in and out of the object. Useful for controls but not polys.
    If the shape nodes are heavy will take time to compute.

    :param obj: The maya object to measure
    :type obj: str
    :return longestEdge: The longest edge of the selected object in maya units
    :rtype longestEdge: float
    """
    if ignoreChildren:  # worldSpace will be ignored
        objBoundingBoxRaw = getBoundingBoxNoChildren(obj, worldSpace=worldSpace)
    else:
        objBoundingBoxRaw = getRawBoundingBox(obj, worldSpace=worldSpace)
    bbHWL = getBoundingBoxHWL(objBoundingBoxRaw)  # bounding box height width length
    return getLongestBbEdge(bbHWL)


def getBoundingBoxHWL(rawBoundingBox):
    """Returns the the height, width and length

    :param obj: The maya object to measure
    :type obj: str
    :return bbHWL: height width and length of the bounding box in Maya units (cms) [x, y, z]
    :rtype bbHWL: list
    """
    bbWidthX = rawBoundingBox[3] - rawBoundingBox[0]  # biggest - smallest
    bbHeightY = rawBoundingBox[4] - rawBoundingBox[1]
    bbLengthZ = rawBoundingBox[5] - rawBoundingBox[2]
    bbHWL = [bbWidthX, bbHeightY, bbLengthZ]
    return bbHWL


def getBoundingBoxMultiple(boundingBoxList):
    """Calculates the total bounding box of multiple bounding boxes.

    :param boundingBoxList: A bounding box list of 6 floats [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    :type boundingBoxList: list(float)
    :return totalBoundingBox: Total bounding box list(6 floats)
    :rtype totalBoundingBox: list(float)
    """
    totalBoundingBox = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    for boundingBox in boundingBoxList:
        for i, totalLimit in enumerate(totalBoundingBox):
            if boundingBox[i] < totalLimit and i <= 3:  # get the lower limit for x y z
                totalBoundingBox[i] = boundingBox[i]
            if boundingBox[i] > totalLimit and i > 2:  # get the upper limit for x y z
                totalBoundingBox[i] = boundingBox[i]
    return totalBoundingBox

def getBoundingBoxMultipleObjs(objList):
    """Returns the total bounding box raw limits of multiple objects

    :param objList: list of Maya object names
    :type objList: list
    :return totalBoundingBoxRaw: raw world limits of the bounding box Maya units (cms) [-x, -y, -z, +x, +y, +z]
    :rtype totalBoundingBoxRaw: list
    """
    totalBoundingBoxRaw = getRawBoundingBox(objList[0])
    if len(objList) == 1:  # finish if only one obj selected
        return totalBoundingBoxRaw
    for obj in objList[1:]:  # skip first as already recorded
        newBoundingBox = getRawBoundingBox(obj)
        for i, totalLimit in enumerate(totalBoundingBoxRaw):
            if newBoundingBox[i] < totalLimit and i < 3:  # get the lower limit for x y z
                totalBoundingBoxRaw[i] = newBoundingBox[i]
            if newBoundingBox[i] > totalLimit and i > 2:  # get the upper limit for x y z
                totalBoundingBoxRaw[i] = newBoundingBox[i]
    return totalBoundingBoxRaw


def getRawBoundingBoxMultipleSelObjs(message=True):
    """Returns the total bounding box raw limits of multiple selected objects

    :param message: report the message to the user?
    :type message: bool
    :return totalBoundingBoxRaw: raw world limits of the bounding box Maya units (cms) [-x, -y, -z, +x, +y, +z]
    :rtype totalBoundingBoxRaw: list
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:  # probably should filter the type of object/node too
        om2.MGlobal.displayWarning("No Objects Selected,please select objects")
        return
    boundingObjs = cmds.ls(selObjs, type="transform")  # filter only transforms
    if not boundingObjs:
        om2.MGlobal.displayWarning("No Bounding Box Compatible Objects Selected, Please Select Objects With A 3d Size")
        return
    return getBoundingBoxMultipleObjs(boundingObjs)


def getBoundingBoxHWLMultipleSelObjs():
    """Returns the total length width and height for multiple selected objects in Maya

    :return totalBoundingBoxHWL: The total bounding boxes for multiple object [WidthX HeightY LengthZ]
    :rtype totalBoundingBoxHWL: list
    """
    totalBoundingBoxRaw = getRawBoundingBoxMultipleSelObjs()
    if not totalBoundingBoxRaw:
        return
    return getBoundingBoxHWL(totalBoundingBoxRaw)


def getLongestEdgeMultipleSelObjs():
    """From multiple selected objects returns the longest edge of the all object bounding box

    :return longestEdge: The longest edge (from width X height y and length z), largest number
    :rtype longestEdge: float
    """
    totalBoundingBoxHWL = getBoundingBoxHWLMultipleSelObjs()
    if not totalBoundingBoxHWL:
        return
    return getLongestBbEdge(totalBoundingBoxHWL)


def scaleObjListPivot(transformList, gScale, scalePivot=(0,0,0)):
    """Receives a uniquely/long named transformList will scale from a pivot by parenting to a temp grp and scaling,
    then reparenting back to the original parents.

    Names should be unique/long

    If objects can be pivot centered after scale can use scaleWorldPivotCenterPivot()

    :param transformList: list of object names in Maya
    :type transformList: list
    :param gScale: the scale amount as a float ie 0.9 (is 90% of the current size)
    :type gScale: float
    :param scalePivot: tuple of floats, the scale pivot in world space
    :type scalePivot: tuple
    """
    cmds.select(deselect=True)
    lightParent = list()
    for lightT in transformList:
        lightParent.append(cmds.listRelatives(lightT, parent=True, fullPath=True))  # get their parents
    tempGrp = namehandling.nonUniqueNameNumber('normalizeLightsTemp_XX_grp', shortNewName=True, paddingDefault=2)
    tempGrp = cmds.group(empty=True, n=tempGrp)
    cmds.move(scalePivot[0], scalePivot[1], scalePivot[2], tempGrp, absolute=True)
    for i, transform in enumerate(transformList):
        transformList[i] = cmds.parent(transform, tempGrp)
    cmds.scale(gScale, gScale, gScale, tempGrp)
    for i, lightT in enumerate(transformList):  # parent back to original
        if lightParent[i]:
            cmds.parent(lightT, lightParent[i])
        else:
            cmds.parent(lightT, world=True)
    cmds.delete(tempGrp)


def scaleWorldPivotCenterPivot(transformList, gScale, scalePivot=(0,0,0)):
    """Receives a uniquely/long named transformList will scale from a pivot by world space xform scale.

    Note: All objects pivots will be centered after the scale.  Avoids parenting, but center pivot isn't appropriate in
    many situations

    If pivots are an issue use scaleObjListPivot() instead

    Names should be unique or long

    :param transformList: list of object names in Maya
    :type transformList: list
    :param gScale: the scale amount as a float ie 0.9 (is 90% of the current size)
    :type gScale: float
    :param scalePivot: tuple of floats, the scale pivot in world space
    :type scalePivot: tuple
    """
    for transform in transformList:
        transformScale = cmds.xform(transform, query=True, scale=True, worldSpace=True)
        newScale = (transformScale[0] * gScale,
                    transformScale[1] * gScale,
                    transformScale[2] * gScale)
        cmds.xform(transform, scale=newScale, worldSpace=True, scalePivot=scalePivot, preserve=True,
                   centerPivots=True, zeroTransformPivots=True)