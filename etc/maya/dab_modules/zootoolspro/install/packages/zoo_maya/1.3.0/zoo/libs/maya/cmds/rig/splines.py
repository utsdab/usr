import collections

import maya.cmds as cmds
import maya.api.OpenMaya as om2
from zoo.libs.maya import zapi

from zoo.libs.maya.cmds.rig import parentfk, nodes, deformers, controls
from zoo.libs.maya.cmds.objutils import namehandling, attributes, objcolor, shapenodes, filtertypes, joints
from zoo.libs.maya.cmds.meta import metajointscurve
from zoo.libs.maya.meta import base

UPV_CONTROL = "arrow_1_thinbev"  # up vector control shape name

# Cluster Curve Globals
CLSTRCRVE_NETWORK_SFX = "_clusterCurve_network"
CLSTRCRVE_CONTROL_ATTR = "clstrC_cntrlsTrack"
CLSTRCRVE_CONTROLGRP_ATTR = "clstrC_cntrlGrpTrack"
CLSTRCRVE_CLUSTERS_ATTR = "clstrC_clstrsTrack"
CLSTRCRVE_RIGGROUP_ATTR = "clstrC_rigGrpTrack"
CLSTRCRVE_SPLINE_ATTR = "clstrC_splineTrack"
CLSTRCRVE_ATTR_LIST = [CLSTRCRVE_CLUSTERS_ATTR, CLSTRCRVE_CONTROL_ATTR, CLSTRCRVE_CONTROLGRP_ATTR,
                       CLSTRCRVE_RIGGROUP_ATTR, CLSTRCRVE_SPLINE_ATTR]

COG_CONTROL = ['circle_boom_pointer', 12.0, (0.2, 0.0, .35)]

SPINE_CONTROLS = collections.OrderedDict()  # items are [ctrlType, scale, rgbColor]
SPINE_CONTROLS['spineSpline_cntrlBase'] = ('cube', 2.0, (1, 0, 0))
SPINE_CONTROLS['spineSpline_cntrlBaseSml'] = ('cube', 0.3, (1, 0, 0))
SPINE_CONTROLS['spineSpline_cntrlMid'] = ('cube', 1.0, (1, 0, 0))
SPINE_CONTROLS['spineSpline_cntrlTopSml'] = ('cube', 0.3, (1, 0, 0))
SPINE_CONTROLS['spineSpline_cntrlTop'] = ('cube', 2.0, (1, 0, 0))
SPINE_CONTROLS['spineSpline_rotMid'] = ('sphere', 2.0, (0, 1, 0))

SPINE_CONTROL_COLOR = SPINE_CONTROLS['spineSpline_cntrlBase'][2]
SPINE_MID_COLOR = SPINE_CONTROLS['spineSpline_rotMid'][2]

SPINE = "spine"
FK = "fk"
REVFK = "revFk"
FLOAT = "float"
SPINECTRL = "spineCtrl"
SPINEMIDCTRL = "spineMidCtrl"
FKCTRL = "fkCtrl"
REVFKCTRL = "revFkCtrl"
FLOATCTRL = "floatCtrl"

# Name, scale, color
FK_CONTROLS = ['cube', 2.0, (1.0, 1.0, 0.0)]
REV_FK_CONTROLS = ['cube', 2.0, (0.0, 0.0, 1.0)]
FLOAT_CONTROLS = ['cube', 2.0, (0.0, 1.0, 1.0)]

WORLD_UP_SCENE = "scene"
WORLD_UP_OBJECT = "object"
WORLD_UP_OBJ_ROT = "objectrotation"
WORLD_UP_VECTOR = "vector"
WORLD_UP_OBJ_ROT = "normal"

"""
Build Objects Along Spline
"""


def stepWeightCalculate(spacingWeight, steps):
    """Given the steps and spacing weight returns a list.  Ignores negative values and makes them positive.

    Works off powers.  The spacing weight is a power + 1:

        Spacing weight of 0.0 will be a power of 1.0
        Spacing weight of 1.0 will be a power of 2.0 etc

    Returns a list of spacing values to multiply, the range is normalized from 0.0-1.0:

        Spacing weight: 0.0 with 4 steps returns [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        Spacing Weight: 1.0 with 4 steps returns [0.25, 0.5, 0.7499999999999999, 1.0]
        Spacing Weight: 2.0 with 4 steps returns [0.0625, 0.25, 0.5625, 1.0]

    :param spacingWeight: The spacing value, is a power + 1 so a weight of 0.0 is a power of 1.0
    :type spacingWeight: float
    :param steps: The number of steps to return in the list
    :type steps: int
    :return stepList: A list of values now weighted depending on the spacingWeight [0.25, 0.5, 0.7499999999999999, 1.0]
    :rtype stepList: list(float)
    """
    stepMultiplyList = list()
    if spacingWeight == 0.0:  # Do nothing, return all entries as 1.0
        for n in range(steps):
            stepMultiplyList.append(1.0)
        return stepMultiplyList
    # Do the calculation
    if spacingWeight < 0.0:  # ignore negative values
        spacingWeight *= -1
    spacingWeight += 1  # is a power so zero is one
    addList = list()
    totalPerc = list()
    for n in range(steps):
        count = float(n + 1)
        addList.append((count ** spacingWeight) / count)  # multiply by the power and account for the count size
    total = sum(map(float, addList))
    for n in range(steps):  # Get values as a percentage of the total
        totalPerc.append(addList[n] / total)
    for n in range(steps):  # Normalize range from 0.0-1.0
        stepMultiplyList.append(totalPerc[n] / totalPerc[-1])
    return stepMultiplyList


def calculateSpacing(spacingWeight, steps, startValue, endValue):
    """Returns spacing values in the 0-1 range

    :param spacingWeight: The spacing value, is a power + 1 so a weight of 0.0 is a power of 1.0
    :type spacingWeight: float
    :param steps: The number of steps to return in the list
    :type steps: int
    :param startValue: The start position value
    :type startValue: float
    :param endValue: The end position value
    :type endValue: float
    :return spacingValueList: The spacing value list normalized from 0.0-1.0 range
    :rtype spacingValueList: list(float)
    """
    # Do the math for the distribution
    spacingValueList = list()
    stepLength = 1.0 / (steps - 1)
    stepMultiplyList = stepWeightCalculate(spacingWeight, steps)  # return weighted data [0.25, 0.5, 0.75, 1.0]
    for i, mult in enumerate(stepMultiplyList):  # Calculate step value Note: start and end is ignored
        uValue = stepLength * float(i)
        spacingValueList.append(uValue * mult)
    if spacingWeight < 0.0:  # Reverse
        spacingValueList.reverse()
        for i, mult in enumerate(stepMultiplyList):  # Calculate step value Note: start and end is ignored
            spacingValueList[i] = 1.0 - spacingValueList[i]
    return spacingValueList


def calculateRangeSpacing(spacingWeight, steps, startValue, endValue, rotStart, rotEnd, scaleStart, scaleEnd,
                          weightPosition, weightRotation, weightScale):
    """Returns the spacing values adjusted for range

    :param spacingWeight: The spacing value, is a power + 1 so a weight of 0.0 is a power of 1.0
    :type spacingWeight: float
    :param steps: The number of steps to return in the list
    :type steps: int
    :param startValue: The start position value
    :type startValue: float
    :param endValue: The end position value
    :type endValue: float
    :return spacingValueList: The spacing value list now adjusted to the start and end range
    :rtype spacingValueList: list(float)
    """
    posValueList = list()
    rotValueList = list()
    scaleValueList = list()
    stepLength = 1.0 / (float(steps) - 1.0)
    spacingValueList = calculateSpacing(spacingWeight, steps, startValue, endValue)  # list in 0-1 range

    # Position adjust to the range and offset the start position
    range = endValue - startValue
    if weightPosition:
        for i, spacing in enumerate(spacingValueList):
            posValueList.append(spacingValueList[i] * range + startValue)
    else:
        for i, spacing in enumerate(spacingValueList):
            posValueList.append((stepLength * float(i)) * range + startValue)

    # rotation spacing
    rotRange = [rotEnd[0] - rotStart[0],
                rotEnd[1] - rotStart[1],
                rotEnd[2] - rotStart[2]]
    if weightRotation:
        for i, spacing in enumerate(spacingValueList):
            rotValueList.append([(spacingValueList[i] * rotRange[0] + rotStart[0]),
                                 (spacingValueList[i] * rotRange[1] + rotStart[1]),
                                 (spacingValueList[i] * rotRange[2] + rotStart[2])])
    else:
        for i, spacing in enumerate(spacingValueList):
            rotValueList.append([(stepLength * float(i)) * rotRange[0] + rotStart[0],
                                 (stepLength * float(i)) * rotRange[1] + rotStart[1],
                                 (stepLength * float(i)) * rotRange[2] + rotStart[2]])

    # rotation spacing
    scaleRange = [scaleEnd[0] - scaleStart[0],
                  scaleEnd[1] - scaleStart[1],
                  scaleEnd[2] - scaleStart[2]]
    if weightScale:
        for i, spacing in enumerate(spacingValueList):
            scaleValueList.append([(spacingValueList[i] * scaleRange[0] + scaleStart[0]),
                                   (spacingValueList[i] * scaleRange[1] + scaleStart[1]),
                                   (spacingValueList[i] * scaleRange[2] + scaleStart[2])])
    else:
        for i, spacing in enumerate(spacingValueList):
            scaleValueList.append([(stepLength * float(i)) * scaleRange[0] + scaleStart[0],
                                   (stepLength * float(i)) * scaleRange[1] + scaleStart[1],
                                   (stepLength * float(i)) * scaleRange[2] + scaleStart[2]])

    return posValueList, rotValueList, scaleValueList


def objectsAlongSpline(objectList, splineCurve, deleteMotionPaths=False, spacingWeight=0.0, spacingStart=0.0,
                       spacingEnd=1.0, rotationStart=(0.0, 0.0, 0.0), rotationEnd=(0.0, 0.0, 0.0),
                       scaleStart=(1.0, 1.0, 1.0), scaleEnd=(1.0, 1.0, 1.0), worldUpVector=(0.0, 1, 0.0), follow=True,
                       worldUpType=WORLD_UP_SCENE, upAxis="z", motionPName="moPth", worldUpObject="", followAxis="y",
                       fractionMode=True, inverseFront=False, inverseUp=False, weightPosition=True,
                       weightRotation=True, weightScale=True):
    """Places objects along a spline using motion paths, added weighting kwarg for non-uniform spacing.

    The options are mostly Maya's motionPath kwargs see:

        https://help.autodesk.com/cloudhelp/2016/ENU/Maya-Tech-Docs/CommandsPython/pathAnimation.html

    :param objectList: List of objects in order to distribute along the curve
    :type objectList: list(str)
    :param splineCurve: The NURBS spline transform node to distribute the objects along
    :type splineCurve: str
    :param deleteMotionPaths: Deletes history so there are no motion paths returned
    :type deleteMotionPaths: bool
    :param spacingWeight: The spacing of the objects, 0.5 is uniform.  0.0 weights more towards the start 1.0 to end
    :type spacingWeight: float
    :param spacingStart: The spacing of the objects starts at this ratio along the curve
    :type spacingStart: float
    :param spacingEnd: The spacing of the objects ends at this ratio along the curve
    :type spacingEnd: float
    :param rotationStart: The twist offset start of all objects (frontTwist, upTwist, sideTwist)
    :type rotationStart: float
    :param rotationEnd: The twist offset end of all objects (frontTwist, upTwist, sideTwist)
    :type rotationEnd: float
    :param worldUpVector: The upVector for the joints
    :type worldUpVector: float
    :param follow: Objects will follow the curve
    :type follow: bool
    :param worldUpType: "scene", "object", "objectrotation", "vector", or "normal"
    :type worldUpType: str
    :param upAxis: This flag specifies which object local axis to be aligned a computed up direction. Default is z
    :type upAxis: str
    :param motionPName: The suffix name of the motion path example "obj_moPth"
    :type motionPName: str
    :param worldUpObject: Obj name if worldUpType "object" or "objectrotation". Default value is no up object, or world space.
    :type worldUpObject: str
    :param followAxis: Object local axis to be aligned to the tangent of the path curve. Default is y
    :type followAxis: str
    :param fractionMode: Object local axis to be aligned to the tangent of the path curve. Default is y
    :type fractionMode: str
    :param inverseFront: Invert the follow axis?
    :type inverseFront: bool
    :param inverseUp: Invert the up axis?
    :type inverseUp: bool

    :return motionPathNodes: The motion path nodes created a salist of names
    :rtype motionPathNodes: list(str)
    """
    motionPathNodes = list()

    if len(objectList) > 1:
        posValueList, rotValueList, scaleValueList = calculateRangeSpacing(spacingWeight, len(objectList), spacingStart,
                                                                           spacingEnd, rotationStart, rotationEnd,
                                                                           scaleStart, scaleEnd, weightPosition,
                                                                           weightRotation, weightScale)
    else:  # only one object
        posValueList = [spacingStart]
        rotValueList = [rotationStart]
        scaleValueList = [scaleStart]

    # Assign the motion paths
    for i, obj in enumerate(objectList):
        name = "_".join([obj, namehandling.getShortName(motionPName)])
        if follow:
            motionPathNodes.append(cmds.pathAnimation(obj,
                                                      name=name,
                                                      curve=splineCurve,
                                                      follow=True,
                                                      worldUpVector=worldUpVector,
                                                      worldUpType=worldUpType,
                                                      worldUpObject=worldUpObject,
                                                      upAxis=upAxis,
                                                      followAxis=followAxis,
                                                      fractionMode=fractionMode,
                                                      inverseFront=inverseFront,
                                                      inverseUp=inverseUp,
                                                      startTimeU=0,
                                                      endTimeU=1))
        else:
            motionPathNodes.append(cmds.pathAnimation(obj,
                                                      name=name,
                                                      curve=splineCurve,
                                                      follow=False,
                                                      fractionMode=fractionMode,
                                                      startTimeU=0,
                                                      endTimeU=1))
        # Delete keys and set the uValue attribute
        cmds.cutKey(motionPathNodes[i], time=(0, 1), clear=True, attribute="uValue")
        cmds.setAttr("{}.uValue".format(motionPathNodes[i]), posValueList[i])
        # Rotation Twist, set the offsets
        if follow:  # ignore if follow is off
            cmds.setAttr("{}.frontTwist".format(motionPathNodes[i]), rotValueList[i][0])
            cmds.setAttr("{}.upTwist".format(motionPathNodes[i]), rotValueList[i][1])
            cmds.setAttr("{}.sideTwist".format(motionPathNodes[i]), rotValueList[i][2])
        cmds.setAttr("{}.scale".format(objectList[i]), scaleValueList[i][0], scaleValueList[i][1], scaleValueList[i][2])
    if deleteMotionPaths:
        cmds.setKeyframe(objectList, time=[0], attribute='translate')  # must key to maintain position
        cmds.setKeyframe(objectList, time=[0], attribute='rotate')
        cmds.delete(motionPathNodes)
        cmds.cutKey(objectList, time=(0, 1), clear=True, attribute="translate")  # del keys
        cmds.cutKey(objectList, time=(0, 1), clear=True, attribute="rotate")  # del keys
        motionPathNodes = list()
    return motionPathNodes


def autoWorldUpVector(splineCurve, upVectorName, controlScale=1.0):
    """Creates an arrow attaches it's grp to the start of the motion path with no follow/orientation for up vector"""
    upVArrow = controls.createControlCurve(folderpath="",
                                           ctrlName=upVectorName,
                                           curveScale=(controlScale, controlScale, controlScale),
                                           designName=UPV_CONTROL,
                                           addSuffix=True,
                                           shapeParent=None,
                                           rotateOffset=(90.0, 0.0, 0.0),
                                           trackScale=True,
                                           lineWidth=-1,
                                           rgbColor=None)[0]
    shapenodes.translateObjListCVs([upVArrow], [0.0, 1.0, 0.0])
    upVGrp, upVArrow, grpUuid, objUuid = controls.groupInPlace(upVArrow, grpSwapSuffix=True)
    upVMoPath = cmds.pathAnimation(upVGrp,
                                   name="{}_moPath".format(upVectorName),
                                   curve=splineCurve,
                                   follow=False,
                                   fractionMode=True,
                                   startTimeU=0,
                                   endTimeU=1)
    cmds.cutKey(upVMoPath, time=(0, 1), clear=True, attribute="uValue")  # delete the keys
    return upVGrp, upVArrow, upVMoPath


def objectsAlongSplineDuplicate(objectList, splineCurve, multiplyObjects=5, deleteMotionPaths=False, spacingWeight=0.0,
                                spacingStart=0.0, spacingEnd=1.0, rotationStart=(0, 0, 0), rotationEnd=(0, 0, 0),
                                scaleStart=(1.0, 1.0, 1.0), scaleEnd=(1.0, 1.0, 1.0), worldUpVector=(0, 1, 0),
                                follow=True, worldUpType=WORLD_UP_SCENE, group=True, instance=False,
                                upAxis="z", motionPName="moPth", worldUpObject="", followAxis="y", fractionMode=True,
                                inverseFront=False, inverseUp=False, weightPosition=True, weightRotation=True,
                                weightScale=True, autoWorldUpV=False, message=False):
    """From the selection, object or objects and then a NURBS curve, places objects along a spline using motion paths, \
    added weighting kwarg for non-uniform spacing.

    This function will duplicate or instance the objectList by the multiplyObjects value.

    Can also use MASH but this will work on joints too. MASH only uses meshes.

    The options are mostly Maya's motionPath kwargs see:

        https://help.autodesk.com/cloudhelp/2016/ENU/Maya-Tech-Docs/CommandsPython/pathAnimation.html

    :param objectList: List of object/s in order to distribute along the curve, will be duplicated by multiplyObjects
    :type objectList: list(str)
    :param splineCurve: The NURBS spline transform node to distribute the objects along
    :type splineCurve: str
    :param deleteMotionPaths: Deletes history so there are no motion paths returned
    :type deleteMotionPaths: bool
    :param spacingWeight: The spacing of the objects, 0.5 is uniform.  0.0 weights more towards the start 1.0 to end
    :type spacingWeight: float
    :param spacingStart: The spacing of the objects starts at this ratio along the curve
    :type spacingStart: float
    :param spacingEnd: The spacing of the objects ends at this ratio along the curve
    :type spacingEnd: float
    :param worldUpVector: The upVector for the joints
    :type worldUpVector: float
    :param group: Group all objects
    :type group: bool
    :param instance: Instance objects instead of duplicating?
    :type instance: bool
    :param follow: Objects will follow the curve
    :type follow: bool
    :param worldUpType: "scene", "object", "objectrotation", "vector", or "normal"
    :type worldUpType: str
    :param upAxis: This flag specifies which object local axis to be aligned a computed up direction. Default is z
    :type upAxis: str
    :param motionPName: The suffix name of the motion path example "obj_moPth"
    :type motionPName: str
    :param worldUpObject: Obj name if worldUpType "object" or "objectrotation". Default value is no up object, or world space.
    :type worldUpObject: str
    :param followAxis: Object local axis to be aligned to the tangent of the path curve. Default is y
    :type followAxis: str
    :param fractionMode: Calculate the position as a fraction of curve 0.0-1.0 or distance?
    :type fractionMode: bool
    :param inverseFront: Invert the follow axis?
    :type inverseFront: bool
    :param fractionMode: Calculates in real world coords based on the curve, is affected by the spacing on the CVs.
    :type fractionMode: bool

    :return motionPathNodes: The motion path nodes created, a list of names
    :rtype motionPathNodes: list(str)
    :return objectList: A full list of objects stuck to the spline in the rig
    :rtype objectList: list(str)
    :return grp: The group containing the objects, if no group then will be ""
    :rtype grp: str
    :return splineCurve: The spline object
    :rtype splineCurve: str
    :return upVGrp: The name of the upVector grp if it was built otherwise ""
    :rtype upVGrp: str
    :return upVArrow: The name of the upVector control if it was built otherwise ""
    :rtype upVArrow: str
    :return upVMoPath: The name of the upVector motion path if it was built otherwise ""
    :rtype upVMoPath: str
    """
    if autoWorldUpV:  # build the arrow up vector at the start of the curve
        upVectorName = namehandling.nonUniqueNameNumber("{}_upV".format(splineCurve))
        upVGrp, upVArrow, upVMoPath = autoWorldUpVector(splineCurve, upVectorName)
        worldUpObject = upVArrow
    else:
        upVGrp = ""
        upVArrow = ""
        upVMoPath = ""

    if multiplyObjects > 0:
        dupList = list(objectList)
        for x in range(multiplyObjects):
            objectList += cmds.duplicate(dupList, instanceLeaf=instance, returnRootsOnly=True)
    motionPathNodes = objectsAlongSpline(objectList, splineCurve, deleteMotionPaths=deleteMotionPaths,
                                         spacingWeight=spacingWeight,
                                         spacingStart=spacingStart, rotationStart=rotationStart,
                                         rotationEnd=rotationEnd, scaleStart=scaleStart, scaleEnd=scaleEnd,
                                         spacingEnd=spacingEnd, worldUpVector=worldUpVector, follow=follow,
                                         worldUpType=worldUpType, upAxis=upAxis, motionPName=motionPName,
                                         worldUpObject=worldUpObject, followAxis=followAxis, fractionMode=fractionMode,
                                         inverseFront=inverseFront, inverseUp=inverseUp, weightPosition=weightPosition,
                                         weightRotation=weightRotation, weightScale=weightScale)
    if group:  # grp the objects and rig under a couple of groups
        objDagList = list(zapi.nodesByNames(objectList))  # return objects for hierarchy long renames
        if upVArrow:
            upVectorDagList = list(zapi.nodesByNames([upVGrp, upVArrow, upVMoPath]))
        grp = cmds.group(objectList, name="{}_objs_grp".format(splineCurve))
        grpDagList = list(zapi.nodesByNames([grp]))
        # parent into main group
        rigGrp = cmds.group(name="{}_rig_grp".format(splineCurve), empty=True)
        cmds.parent(grp, splineCurve, rigGrp)
        objectList = zapi.fullNames(objDagList)  # back to long names
        grp = zapi.fullNames(grpDagList)[0]
        if upVArrow:
            cmds.parent(upVGrp, rigGrp)
            upVGrp, upVArrow, upVMoPath = zapi.fullNames(upVectorDagList)
    else:
        grp = ""
        rigGrp = ""
    if message:
        om2.MGlobal.displayInfo("Success: Motion path setup created.")
    return motionPathNodes, objectList, splineCurve, grp, rigGrp, upVGrp, upVArrow, upVMoPath


def objectsAlongSplineSelected(multiplyObjects=5, deleteMotionPaths=False, spacingWeight=0.0, spacingStart=0.0,
                               spacingEnd=1.0, rotationStart=(0, 0, 0), rotationEnd=(0, 0, 0),
                               scaleStart=(1.0, 1.0, 1.0),
                               scaleEnd=(1.0, 1.0, 1.0), worldUpVector=(0, 1, 0),
                               follow=True, worldUpType=WORLD_UP_SCENE, group=True, instance=False,
                               upAxis="z", motionPName="moPth", worldUpObject="", followAxis="y", fractionMode=True,
                               inverseFront=False, inverseUp=False, weightPosition=True, weightRotation=True,
                               weightScale=True, autoWorldUpV=False):
    """Same as objectsAlongSplineDuplicate() but for selection

    The selection is the objects to duplicate and then the curve transform last.

    See objectsAlongSplineDuplicate() for documentation
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs or len(selObjs) < 2:
        om2.MGlobal.displayWarning("Selection incorrect.  Please select an object or objects and a curve last")
        return
    splineCurve = selObjs[-1]
    if not filtertypes.filterTypeReturnTransforms([splineCurve], children=False, shapeType="nurbsCurve"):
        om2.MGlobal.displayWarning("The last selected object must be a NURBS curve")
        return
    del selObjs[-1]
    return objectsAlongSplineDuplicate(selObjs, splineCurve, multiplyObjects=multiplyObjects,
                                       deleteMotionPaths=deleteMotionPaths, spacingWeight=spacingWeight,
                                       spacingStart=spacingStart, spacingEnd=spacingEnd, rotationStart=rotationStart,
                                       rotationEnd=rotationEnd, scaleStart=scaleStart,
                                       scaleEnd=scaleEnd, worldUpVector=worldUpVector, follow=follow,
                                       worldUpType=worldUpType, group=group, instance=instance, upAxis=upAxis,
                                       motionPName=motionPName, worldUpObject=worldUpObject, followAxis=followAxis,
                                       fractionMode=fractionMode, inverseFront=inverseFront, inverseUp=inverseUp,
                                       weightPosition=weightPosition, weightRotation=weightRotation,
                                       weightScale=weightScale, autoWorldUpV=autoWorldUpV, message=True)


"""
Joints Along A Spline
"""


def jointsAlongACurve(splineCurve, jointCount=30, jointName="joint", spacingWeight=0.0, spacingStart=0.0,
                      spacingEnd=1.0, secondaryAxisOrient="yup", fractionMode=True, numberPadding=2, suffix=True,
                      buildMetaNode=True, reverseDirection=False, message=True):
    """Given a spline curve build joints along the curve, parent and orient them into an FK chain.

    :param splineCurve: The name of the transform node of the curve
    :type splineCurve: str
    :param jointCount: The number of joints to build in the chain
    :type jointCount: int
    :param jointName: The base name of the joints to be created
    :type jointName: str
    :param spacingWeight: The weighting of the spacing, causes more joints to be sqashed to one end or another 0.0 - 1.0
    :type spacingWeight: float
    :param spacingStart: The start of the curve where the joint chain will start usually 0.0 (start)
    :type spacingStart: float
    :param spacingEnd: The end of the curve where the joint chain will start usually 1.0 (end)
    :type spacingEnd: float
    :param secondaryAxisOrient: this axis of the joints orients in what direction?  Default is "yup"
    :type secondaryAxisOrient: str
    :param fractionMode: calculates in real world coords based on the curve, is affected by the spacing on the CVs.
    :type fractionMode: bool
    :param numberPadding: Pad the joint names with numbers and this padding.  ie 2 is 01, 02, 03
    :type numberPadding: int
    :param suffix: Add a joint suffix "jnt" to the end of the joint names ie "joint_01_jnt"
    :type suffix: bool
    :param buildMetaNode: builds the meta node for tracking and altering the joints later
    :type buildMetaNode: bool
    :param reverseDirection: reverses the curve while building, the reverses it back after build
    :type reverseDirection: bool
    :param message: return any messages to the user?
    :type message: bool

    :return jointList: A list of joint string names
    :rtype jointList: list(str)
    """
    if jointCount < 1:
        jointCount = 1
    jointList = list()
    if fractionMode:  # Normalize values
        if spacingStart < 0.0:
            spacingStart = 0.0
        if spacingEnd > 1.0:
            spacingEnd = 1.0
    buildCurve = splineCurve
    if reverseDirection:  # Reverse the direction of the curve
        buildCurve = cmds.reverseCurve(splineCurve, replaceOriginal=False)[0]
    for n in range(jointCount):  # create joints
        cmds.select(deselect=True)
        if suffix:
            n = "_".join([jointName, str(n + 1).zfill(numberPadding), filtertypes.JOINT_SX])
        else:
            n = "_".join([jointName, str(n + 1).zfill(numberPadding)])
        jointList.append(cmds.joint(name=namehandling.nonUniqueNameNumber(n)))
    # Place joints on the curve
    objectsAlongSplineDuplicate(jointList, buildCurve, multiplyObjects=0, deleteMotionPaths=True,
                                spacingWeight=spacingWeight, spacingStart=spacingStart, spacingEnd=spacingEnd,
                                follow=False, group=False, fractionMode=fractionMode, weightPosition=True,
                                weightRotation=False, weightScale=False, autoWorldUpV=False, message=False)
    # Parent the joints to each other
    jntDagList = list(zapi.nodesByNames(jointList))  # objects to api dag objects for names
    for n in range(1, len(jointList)):
        cmds.parent(jointList[n], jointList[n - 1])
    jointList = zapi.fullNames(jntDagList)  # back to long names
    # Orient joints
    if len(jointList) > 1:
        joints.alignJoint(jointList, secondaryAxisOrient=secondaryAxisOrient, children=False, freezeJnt=True, message=False)
        joints.alignJointToParent(jointList[-1])  # orient last joint to parent
    if reverseDirection:  # Delete reverse direction curve
        cmds.delete(buildCurve)
        # cmds.select(jointList[-1])  # reverse curve drops selection
    if buildMetaNode:  # Builds the network meta node on all joints and the curve
        name = namehandling.nonUniqueNameNumber("{}_joints_meta".format(splineCurve))
        metaNode = metajointscurve.ZooJointsCurve(name=name)
        metaNode.connectAttributes(list(zapi.nodesByNames(jointList)),
                                   zapi.nodeByName(splineCurve))
        metaNode.setMetaAttributes(jointCount, jointName, spacingWeight, spacingStart, spacingEnd, secondaryAxisOrient,
                                   fractionMode, numberPadding, suffix, reverseDirection)
    if message:
        om2.MGlobal.displayInfo("Success: Joints created and oriented along `{}`.".format(splineCurve))
    return jointList


def jointsAlongACurveSelected(jointCount=30, jointName="joint", spacingWeight=0.0, spacingStart=0.0,
                              spacingEnd=1.0, secondaryAxisOrient="yup", fractionMode=True, numberPadding=2,
                              suffix=True, buildMetaNode=True, reverseDirection=False):
    """Given a selected spline curve build joints along the curve, parent and orient them into an FK chain.

    :param jointCount: The number of joints to build in the chain
    :type jointCount: int
    :param jointName: The base name of the joints to be created
    :type jointName: str
    :param spacingWeight: The weighting of the spacing, causes more joints to be sqashed to one end or another 0.0 - 1.0
    :type spacingWeight: float
    :param spacingStart: The start of the curve where the joint chain will start usually 0.0 (start)
    :type spacingStart: float
    :param spacingEnd: The end of the curve where the joint chain will start usually 1.0 (end)
    :type spacingEnd: float
    :param secondaryAxisOrient: this axis of the joints orients in what direction?  Default is "yup"
    :type secondaryAxisOrient: str
    :param fractionMode: calculates in real world coords based on the curve, is affected by the spacing on the CVs.
    :type fractionMode: bool
    :param numberPadding: Pad the joint names with numbers and this padding.  ie 2 is 01, 02, 03
    :type numberPadding: int
    :param suffix: Add a joint suffix "jnt" to the end of the joint names ie "joint_01_jnt"
    :type suffix: bool
    :param buildMetaNode: builds the meta node for tracking and altering the joints later
    :type buildMetaNode: bool
    :param reverseDirection: reverses the curve while building, the reverses it back after build
    :type reverseDirection: bool

    :return jointListList: A list of a list of joint string names
    :rtype jointListList: list(list(str))
    """
    selObjs = cmds.ls(selection=True)
    curveTransforms = filtertypes.filterTypeReturnTransforms(selObjs, children=False, shapeType="nurbsCurve")
    if not curveTransforms:
        om2.MGlobal.displayWarning("Selection incorrect.  Please a curve type object.")
        return
    if len(curveTransforms) > 1:  # multiple curves found build a joint chain on each curve, names are different
        jointListList = list()
        uniqueName = namehandling.nonUniqueNameNumber(jointName)
        for i, curve in enumerate(curveTransforms):
            jointName = "_".join([uniqueName, str(i + 1).zfill(numberPadding)])
            jointList = jointsAlongACurve(curve, jointCount=jointCount, jointName=jointName,
                                          spacingWeight=spacingWeight,
                                          spacingStart=spacingStart, spacingEnd=spacingEnd,
                                          secondaryAxisOrient=secondaryAxisOrient,
                                          fractionMode=fractionMode, numberPadding=numberPadding,
                                          buildMetaNode=buildMetaNode, reverseDirection=reverseDirection)
            jointListList.append(jointList)
        return jointListList
    # Else only one curve found
    jointList = jointsAlongACurve(curveTransforms[0], jointCount=jointCount, jointName=jointName,
                                  spacingWeight=spacingWeight,
                                  spacingStart=spacingStart, spacingEnd=spacingEnd,
                                  secondaryAxisOrient=secondaryAxisOrient,
                                  fractionMode=fractionMode, numberPadding=numberPadding, suffix=suffix,
                                  buildMetaNode=buildMetaNode, reverseDirection=reverseDirection)
    return [jointList]


def deleteSplineJoints(relatedObjs, message=False):
    """Deletes all joints and the meta node setup related to the selection

    :param relatedObjs: any maya nodes by name, should be joints or curves related to joint setup
    :type relatedObjs: str
    :param message: report the message to the user
    :type message: bool
    """
    metajointscurve.deleteSplineJoints(list(zapi.nodesByNames(relatedObjs)), message=message)


def deleteSplineJointsSelected(message=True):
    """Deletes all joints and the meta node setup related to the selection

    :param message: report the message to the user
    :type message: bool
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        om2.MGlobal.displayWarning("Please select a joint or curve related to the spline joint setup")
        return
    metajointscurve.deleteSplineJoints(list(zapi.nodesByNames(selObjs)), message=message)


def rebuildSplineJointsSelected(jointCount=30, jointName="joint", spacingWeight=0.0, spacingStart=0.0,
                                spacingEnd=1.0, secondaryAxisOrient="yup", fractionMode=True, numberPadding=2,
                                suffix=True, buildMetaNode=True, reverseDirection=False, message=True,
                                renameMode=False):
    """Deletes all joints and the meta node setup related to the selection and then rebuilds it as per the kwargs

    See jointsAlongACurve() for documentation

    :param renameMode: If True will use the incoming name to build the new setup.  If False will use the existing name
    :type renameMode: bool
    """
    lastJointList = list()
    selNodes = zapi.selected()
    if not selNodes:
        if message:
            om2.MGlobal.displayWarning("Please select a joint or curve related to the spline joint setup")
        return
    metaNodes = base.findRelatedMetaNodesByClassType(selNodes, metajointscurve.META_TYPE)
    if not metaNodes:
        if message:
            om2.MGlobal.displayWarning("No `{}` related setups found connected to "
                                       "objects".format(metajointscurve.META_TYPE))
        return

    for metaNode in metaNodes:
        curve = metaNode.getCurveStr()
        if not curve:  # no curve so bail
            continue
        jointList = metaNode.getJointsStr()
        if not renameMode:  # get the previous name
            jointName = metaNode.getMetaJointName()
        if jointList:
            metaNode.deleteJoints()
            metaNode.delete()
        jointList = jointsAlongACurve(curve, jointCount=jointCount, jointName=jointName, spacingWeight=spacingWeight,
                                      spacingStart=spacingStart, spacingEnd=spacingEnd,
                                      secondaryAxisOrient=secondaryAxisOrient,
                                      fractionMode=fractionMode, numberPadding=numberPadding, suffix=suffix,
                                      buildMetaNode=buildMetaNode, reverseDirection=reverseDirection, message=message)
        lastJointList.append(jointList[-1])
        if message:
            om2.MGlobal.displayInfo("Success: Joints rebuilt on `{}`".format(curve))
    if len(metaNodes) > 1:  # select all last joints
        cmds.select(lastJointList, add=True)


def splineJointsAttrValues(message=True):
    """Returns all the attribute (usually related to the UI) settings from the jointsOnCurve meta node

    Finds related meta node from selected objects either the joints or curves

    :param message: report messages to the user
    :type message: bool
    """
    selNodes = zapi.selected()
    if not selNodes:
        if message:
            om2.MGlobal.displayWarning("Please select a joint or curve related to the spline joint setup")
        return dict()
    metaNodes = base.findRelatedMetaNodesByClassType(selNodes, metajointscurve.META_TYPE)
    if not metaNodes:
        if message:
            om2.MGlobal.displayWarning("No `{}` related setups found connected to "
                                       "objects".format(metajointscurve.META_TYPE))
        return dict()
    return metaNodes[-1].getMetaAttributes()


"""
Misc
"""


def clusterTransforms(clusterPairs, transform=True):
    """Lazy helper function to return the transforms in the cluster list annoying nested list that should be a list \
    of dicts.

    Input:

        [[clusterName, clusterTransformName], [clusterName2, clusterTransformName2]]

    Returns:
        [clusterTransformName, clusterTransformName2]

    of if transform = False then:
        [clusterTransformName, clusterTransformName2]

    :param clusterPairs: list of lists [[clusterName, clusterTransformName], [clusterName2, clusterTransformName2]]
    :type clusterPairs: list(list)
    :param transform: return as a transform True or clusters False
    :type transform: bool
    :return: Returns a list of names
    :rtype: list(str)
    """
    nameList = list()
    for clusterTuple in clusterPairs:
        nameList.append(clusterTuple[transform])
    return nameList


"""
Build Control Structures
"""


def createSplineIk(partPrefixName, jointChain, curveSpans=2):
    """Creates spline ik with given curve spans from a joint list

    :param partPrefixName:  The prefix, name of the rig/part
    :type partPrefixName: str
    :param jointList: The joint names
    :type jointList: list
    :param curveSpans: the amount of curve spans to be built on the spine. Add 3 to get CVs (2=5 cvs)
    :type curveSpans:  int
    :return splineIkList: 0 = ?, 2 = ?,  3 = The Curve
    :rtype splineIkList: list
    :param clusterList: Cluster names must be 5 total
    :type clusterList: list
    :return splineSolver: spline solver name
    :rtype splineSolver: str
    """
    name = namehandling.nonUniqueNameNumber("{}_splineIkhandle".format(partPrefixName))  # create spline ik
    splineIkList = cmds.ikHandle(name=name, startJoint=jointChain[0], endEffector=jointChain[-1],
                                 solver='ikSplineSolver',
                                 numSpans=curveSpans)
    splineSolver = cmds.ikHandle(splineIkList[0], query=True, solver=True)
    name = namehandling.nonUniqueNameNumber("{}_ikSplineCurve".format(partPrefixName))  # name curve
    splineIkList[2] = cmds.rename(splineIkList[2], name)
    name = namehandling.nonUniqueNameNumber("{}_splineIkEffector".format(partPrefixName))  # name effector
    splineIkList[1] = cmds.rename(splineIkList[1], name)
    return splineIkList, splineSolver


"""
Build Control Structures
"""


def buildSplineCogControl(partPrefixName, clusterList, scale=1.0, suffixName="cog", upAxis="+y"):
    """Builds a cog control at the first cluster

    :param partPrefixName: The name of the part prefix "eg spine"
    :type partPrefixName: str
    :param clusterList: Cluster names must be 5 total
    :type clusterList: list
    :param scale: overall scale multiplier of the controls
    :type scale: float
    :param suffixName: name of the second half of the control
    :type suffixName: str
    :param upAxis: The direction to face the control "+y", "-z" etc
    :type upAxis: str
    :return cogControl: the control name
    :rtype cogControl: string
    :return cogGroup: the group name
    :rtype cogGroup: str
    """
    ctrlType = COG_CONTROL[0]
    cntrlScale = scale * COG_CONTROL[1]
    cntrlRgbColor = COG_CONTROL[2]
    cntrlName = "_".join([partPrefixName, suffixName])
    cogControl, cogGroup = controls.createControlsMatch(matchObj=clusterList[0][1],
                                                        newName=cntrlName,
                                                        curveScale=(cntrlScale, cntrlScale, cntrlScale),
                                                        designName=ctrlType,
                                                        rgbColor=cntrlRgbColor)
    # rotate the cog group for to match the up vector, important as all the matching references cog +z
    rotOffset = controls.ROT_AXIS_DICT[upAxis]
    cmds.setAttr("{}.rotate".format(cogGroup), rotOffset[0], rotOffset[1], rotOffset[2])
    return cogControl, cogGroup


def buildControlsSplineFk(partPrefixName, clusterList, scale=1.0, suffixName="fkSpline", orientControls=True,
                          orientGlobalVectorObj="", controlColor=FK_CONTROLS[2]):
    """Builds controls for a spline cluster in regular fk

    :param partPrefixName: The name of the part prefix "eg spine"
    :type partPrefixName: str
    :param clusterList: Cluster names must be 5 total
    :type clusterList: list
    :param scale: overall scale multiplier of the controls
    :type scale: float
    :param suffixName: name of the second half of the controls, will also have _i on the end
    :type suffixName: str
    :param orientGlobalVectorObj: the object for the world up on aims, uses obj -z (ie spine), if "" will be 1st ctrl
    :type orientGlobalVectorObj: str
    :param controlColor: control color in rgb float srgb (0, 0, 1)
    :type controlColor: tuple
    :return fkControlList: control names created
    :rtype fkControlList: list
    :return fkGroupList: group names created
    :rtype fkGroupList: list
    """
    ctrlType = FK_CONTROLS[0]
    cntrlScale = scale * FK_CONTROLS[1]
    cntrlName = "_".join([partPrefixName, suffixName])
    fkControlList, fkGroupList = controls.createControlsMatchList(clusterTransforms(clusterList),
                                                                  overrideName=cntrlName,
                                                                  curveScale=(cntrlScale, cntrlScale, cntrlScale),
                                                                  designName=ctrlType,
                                                                  rgbColor=controlColor)
    if orientControls:
        controls.orientControlsAims(fkGroupList, orientGlobalVectorObj)  # todo this
    parentfk.parentGroupControls(fkControlList, fkGroupList, reverse=False)
    return fkControlList, fkGroupList


def buildControlsSplineRevfk(partPrefixName, clusterList, scale=1.0, suffixName="revfkSpline", orientControls=True,
                             orientGlobalVectorObj="", controlColor=REV_FK_CONTROLS[2]):
    """Builds controls for a spline cluster in reversed fk

    :param partPrefixName: The name of the part prefix "eg spine"
    :type partPrefixName: str
    :param clusterList: Cluster names must be 5 total
    :type clusterList: list
    :param scale: overall scale multiplier of the controls
    :type scale: float
    :param suffixName: name of the second half of the controls, will also have _i on the end
    :type suffixName: str
    :param orientGlobalVectorObj: the object for the world up on aims, uses obj -z (ie spine), if "" will be 1st ctrl
    :type orientGlobalVectorObj: str
    :param controlColor: control color in rgb float srgb (0, 0, 1)
    :type controlColor: tuple
    :return revfkControlList: control names created
    :rtype revfkControlList: list
    :return revfkGroupList: grp names created
    :rtype revfkGroupList: list
    """
    ctrlType = REV_FK_CONTROLS[0]
    cntrlScale = scale * REV_FK_CONTROLS[1]
    cntrlName = "_".join([partPrefixName, suffixName])
    revfkControlList, revfkGroupList = controls.createControlsMatchList(clusterTransforms(clusterList),
                                                                        overrideName=cntrlName,
                                                                        curveScale=(cntrlScale, cntrlScale, cntrlScale),
                                                                        designName=ctrlType,
                                                                        rgbColor=controlColor)
    if orientControls:
        controls.orientControlsAims(revfkGroupList, orientGlobalVectorObj)
    revfkControlList, revfkGroupList = parentfk.parentGroupControls(revfkControlList, revfkGroupList, reverse=True)
    revfkControlList.reverse()
    revfkGroupList.reverse()
    return revfkControlList, revfkGroupList


def buildControlsSplineFloat(partPrefixName, clusterList, scale=1.0, suffixName="floatSpline", orientControls=True,
                             orientGlobalVectorObj="", controlColor=FLOAT_CONTROLS[2]):
    """Builds controls for a spline cluster floating (no parenting)

    :param partPrefixName: The name of the part prefix "eg spine"
    :type partPrefixName: str
    :param clusterList: Cluster names must be 5 total
    :type clusterList: list
    :param scale: overall scale multiplier of the controls
    :type scale: float
    :param suffixName: name of the second half of the controls, will also have _i on the end
    :type suffixName: str
    :param orientGlobalVectorObj: the object for the world up on aims, uses obj -z (ie spine), if "" will be 1st ctrl
    :type orientGlobalVectorObj: str
    :param controlColor: control color in rgb float srgb (0, 0, 1)
    :type controlColor: tuple
    :return floatControlList: control names created
    :rtype floatControlList: list
    :return floatControlList: grp names created
    :rtype floatControlList: list
    """
    ctrlType = FLOAT_CONTROLS[0]
    cntrlScale = scale * FLOAT_CONTROLS[1]
    cntrlName = "_".join([partPrefixName, suffixName])
    floatControlList, floatGroupList = controls.createControlsMatchList(clusterTransforms(clusterList),
                                                                        overrideName=cntrlName,
                                                                        curveScale=(cntrlScale, cntrlScale, cntrlScale),
                                                                        designName=ctrlType,
                                                                        rgbColor=controlColor)
    if orientControls:
        controls.orientControlsAims(floatGroupList, orientGlobalVectorObj)
    return floatControlList, floatGroupList


def buildControlsSplineSpine(partPrefixName, clusterList, scale=1.0, extraRotation=True, orientControls=True,
                             orientGlobalVectorObj="", controlColor=SPINE_CONTROL_COLOR, midCntrlColor=SPINE_MID_COLOR):
    """builds the controls for a simple spline spline
    This is 5 main controls with a rotation offset extra mid control, so 6 controls in all
    Expects the cluster list to match to 5 clusters of the main controls

    :param partPrefixName: The name of the part prefix "eg spine"
    :type partPrefixName: str
    :param clusterList: Cluster names must be 5 total
    :type clusterList: list
    :param scale: overall scale multiplier of the controls
    :type scale: float
    :param orientGlobalVectorObj: the object for the world up on aims, uses obj -z (ie spine), if "" will be 1st ctrl
    :type orientGlobalVectorObj: str
    :return spineControlList: The five main control names
    :rtype spineControlList: list
    :return spineGroupList: The five control group names
    :rtype spineGroupList: list
    :return otherConstraintList: The constraints needed by the part
    :rtype otherConstraintList: list
    :return spineRotControl: The cntrl and grp name of the extra rotation control
    :rtype spineRotControl: list
    """
    spineControlList = list()
    spineGroupList = list()
    # Build the main controls from the ordered dict
    for i, (cntrlName, items) in enumerate(SPINE_CONTROLS.items()):
        cntrlName = "_".join([partPrefixName, cntrlName])
        ctrlType = items[0]
        cntrlScale = scale * items[1]
        floatControl, floatGroup = controls.createControlsMatch(matchObj=clusterList[i][1],
                                                                newName=cntrlName,
                                                                curveScale=(cntrlScale, cntrlScale, cntrlScale),
                                                                designName=ctrlType,
                                                                rgbColor=controlColor)
        spineControlList.append(floatControl)
        spineGroupList.append(floatGroup)
        if i == 4:
            break
    if orientControls:
        controls.orientControlsAims(spineGroupList, orientGlobalVectorObj)
    # get uuids for retrieval later
    spineControlUuids = cmds.ls(spineControlList, uuid=True)
    spineGroupUuids = cmds.ls(spineGroupList, uuid=True)
    # parent smallBase to base, smallTop to top
    spineGroupList[1] = cmds.parent(spineGroupList[1], spineControlList[0])[0]
    spineGroupList[3] = cmds.parent(spineGroupList[3], spineControlList[4])[0]
    # build extra controls setup, constraints extra controls etc
    constraintList = (spineControlList[0], spineControlList[4], spineGroupList[2])  # start, end, mid
    # build constraint and append to list as could be another
    otherConstraintList = list()
    otherConstraintList.append((cmds.parentConstraint(constraintList, maintainOffset=1))[0])
    if extraRotation:  # build rotationMid control
        ctrlSuffix = SPINE_CONTROLS.items()[5][0]  # ordered dict gotta be an easier way
        cntrlName = "_".join([partPrefixName, ctrlSuffix])
        ctrlType = SPINE_CONTROLS[ctrlSuffix][0]
        cntrlScale = scale * SPINE_CONTROLS[ctrlSuffix][1]
        midRotCntrl, midRotGrp = controls.createControlsMatch(matchObj=spineControlList[2],
                                                              newName=cntrlName,
                                                              curveScale=(cntrlScale, cntrlScale, cntrlScale),
                                                              designName=ctrlType,
                                                              rgbColor=midCntrlColor)
        # todo need to offset offset=(0, 0, -4 * scale)
        cmds.parent(spineGroupList[2], midRotCntrl)  # mid control, mid rotation control
        spineRotControl = [midRotCntrl, midRotGrp]
        # constrain the startControlGrp to extraSpineControl
        otherConstraintList.append(cmds.parentConstraint([midRotCntrl, spineGroupList[0]], maintainOffset=1)[0])
    else:
        spineRotControl = None
    # Unpack uuids
    spineGroupList = cmds.ls(spineGroupUuids, long=True)
    spineControlList = cmds.ls(spineControlUuids, long=True)
    return spineControlList, spineGroupList, otherConstraintList, spineRotControl


"""
Hookup Spline To Structures Code
"""


def createEnumList(fkControlList, fkGroupList, revfkControlList, revfkGroupList, floatControlList, floatGroupList,
                   spineControlList, spineGroupList):
    """gets a list of the keys in mainControls for the drop down name list "controlEnumList"

    :param fkControlList: list of the fk controls, can be empty
    :type fkControlList: list
    :param fkGroupList: list of the fk srt groups, can be empty
    :type fkGroupList: list
    :param revfkControlList: list of the revFk controls, can be empty
    :type revfkControlList: list
    :param revfkGroupList: list of the revFk srt groups, can be empty
    :type revfkGroupList: list
    :param floatControlList: list of the float controls, can be empty
    :type floatControlList: list
    :param floatGroupList: list of the float srt groups, can be empty
    :type floatGroupList: list
    :param spineControlList: list of the spine controls , can be empty
    :type spineControlList: list
    :param spineGroupList: list of the spine srt groups, can be empty
    :type spineGroupList: list
    :return controlEnumList: list for the enum dropdown attribute ["spine", "fk", "revFk", "float"] etc
    :rtype controlEnumList: list
    :return controlDict: dictionary with the control lists, enum values as keys
    :rtype controlDict: list
    :return controlGrpDict: dictionary with the control grps, enum values as keys
    :rtype controlGrpDict: list
    """
    controlEnumList = list()
    controlDict = dict()
    controlGrpDict = dict()
    if spineControlList:
        controlEnumList.append(SPINE)
        controlDict[SPINE] = spineControlList
        controlGrpDict[SPINE] = spineGroupList
    if fkControlList:
        controlEnumList.append(FK)
        controlDict[FK] = fkControlList
        controlGrpDict[FK] = fkGroupList
    if floatControlList:
        controlEnumList.append(FLOAT)
        controlDict[FLOAT] = floatControlList
        controlGrpDict[FLOAT] = floatGroupList
    if revfkControlList:
        controlEnumList.append(REVFK)
        controlDict[REVFK] = revfkControlList
        controlGrpDict[REVFK] = revfkGroupList
    return controlEnumList, controlDict, controlGrpDict


def constrainControls(constrainToList, controlEnumList, controlDict, rigName):
    """ Constrains the spline to the controls, no switching, needs setupConditionNodesConstraints() later

    :param constrainToList: the objects that are constrained, most likely clusters, not always
    :type constrainToList: list
    :param controlEnumList: list for the enum dropdown attribute ["spine", "fk", "revFk", "float"] etc
    :rtype controlEnumList: list
    :param controlDict: dictionary with the control lists, enum values as keys
    :type controlDict: dict
    :param rigName: the name of the rig
    :type rigName: str
    :return objConstraintList: list of the constraint names created
    :rtype objConstraintList: list
    """
    objConstraintList = list()
    for i, cnstrObj in enumerate(constrainToList):  # will create a list of max 5 objects, 4 controls, last cluster
        constraintObjList = list()
        for part in controlEnumList:  # part is spine, spine, revFk, float etc
            constraintObjList.append(controlDict[part][i])  # get existing controls for this cluster
        constraintObjList.append(cnstrObj)  # Last to append is the target object with the constraint
        # constrain cluster to control
        constraintNm = namehandling.nonUniqueNameNumber('{}_pointConstraint_{}'.format(rigName, str(i + 1)))
        constraintNm = cmds.parentConstraint(constraintObjList, maintainOffset=True, name=constraintNm)[0]
        objConstraintList.append(constraintNm)
    return objConstraintList


def setupConditionNodesConstraints(controlEnumList, controlDict, controlGrpDict, objConstraintList, rigName,
                                   driverAttr, spineRotGrp):
    """setup condition node switching for constraints and vis switching

    :param controlEnumList: list for the enum dropdown attribute ["spine", "fk", "revFk", "float"] etc
    :rtype controlEnumList: list
    :param controlDict: dictionary with the control lists, enum values as keys
    :type controlDict: dict
    :param controlGrpDict: dictionary with the srt grp lists, enum values as keys
    :type controlGrpDict: dict
    :param objConstraintList: list of the constraint names created
    :type objConstraintList: list
    :param rigName: the name of the rig
    :type rigName: str
    :param driverAttr: the attribute name that drives the switching i think?
    :type driverAttr: str
    :return hchySwitchCondPnts: condition node name for switching parents
    :rtype hchySwitchCondPnts: str
    :return hchySwitchCondVis: condition node name for switching visibility
    :rtype hchySwitchCondVis: str
    """
    hchySwitchCondPnts = list()
    hchySwitchCondVis = list()
    for x, part in enumerate(controlEnumList):
        constraintList = list()
        visAttrList = list()
        for i, control in enumerate(controlDict[part]):  # loop through controls
            controlGrpName = controlGrpDict[part][i]
            constraintList.append(''.join([(objConstraintList[i]), '.',
                                           namehandling.getShortName(control),
                                           'W',
                                           str(x)]))
            visAttrList.append('{}.visibility'.format(namehandling.getShortName(controlGrpName)))
        if part == SPINE:
            visAttrList.append('{}.visibility'.format(namehandling.getShortName(spineRotGrp)))
        hchySwitchCondPnts.append(nodes.conditionMulti(driverAttr, constraintList, x, suffix=""))
        hchySwitchCondVis.append(nodes.conditionMulti(driverAttr, visAttrList, x, suffix=""))
    return hchySwitchCondPnts, hchySwitchCondVis


def constrainToControls(fkControlList, fkGroupList, revfkControlList, revfkGroupList, floatControlList, floatGroupList,
                        spineControlList, spineGroupList, clusterList, switchAttrObject, rigName, spineRotGrp,
                        switchAttrName='hierarchySwitch'):
    """Main function that constrains the spline to various control structures, can be multiple, empty control lists
    aren't created. Constraints are all hooked up to condition nodes for vis and parent switching

    :param fkControlList: list of the fk controls, can be empty
    :type fkControlList: list
    :param fkGroupList: list of the fk srt groups, can be empty
    :type fkGroupList: list
    :param revfkControlList: list of the revFk controls, can be empty
    :type revfkControlList: list
    :param revfkGroupList: list of the revFk srt groups, can be empty
    :type revfkGroupList: list
    :param floatControlList: list of the float controls, can be empty
    :type floatControlList: list
    :param floatGroupList: list of the float srt groups, can be empty
    :type floatGroupList: list
    :param spineControlList: list of the spine controls , can be empty
    :type spineControlList: list
    :param spineGroupList: list of the spine srt groups, can be empty
    :type spineGroupList: list
    :param clusterList: list of the spline cluster names
    :type clusterList: list
    :param switchAttrObject: the object where the switching attributes will be built
    :type switchAttrObject: str
    :param rigName: the name of the rig
    :type rigName: str
    :param switchAttrName: the name of the switch attribute 'hierarchySwitch'
    :type switchAttrName: str
    :return controlEnumList: list for the enum dropdown attribute ["spine", "fk", "revFk", "float"] etc
    :rtype controlEnumList: list
    :return driverAttr: the attribute name that drives the switching i think?
    :rtype driverAttr: str
    :return hchySwitchCondPnts: condition node name for switching parents
    :rtype hchySwitchCondPnts: str
    :return hchySwitchCondVis: condition node name for switching visibility
    :rtype hchySwitchCondVis: str
    :return objConstraintList: list of the constraint names created
    :rtype objConstraintList: list
    """
    driverAttr = ""
    hchySwitchCondPnts = ""
    hchySwitchCondVis = ""
    constrainToList = clusterList
    # create the drop down list for the switching attribute and dicts with keys for controls and control grps
    controlEnumList, controlDict, controlGrpDict = createEnumList(fkControlList, fkGroupList, revfkControlList,
                                                                  revfkGroupList, floatControlList, floatGroupList,
                                                                  spineControlList, spineGroupList)
    if len(controlEnumList) > 1:  # create switch attribute as enum list
        driverAttr = attributes.createEnumAttributeFromList(controlEnumList, switchAttrObject, switchAttrName)
        driverAttr = driverAttr.split("|")[-1]  # otherwise the name is too long
    # do constraints and vis switching
    objConstraintList = constrainControls(constrainToList, controlEnumList, controlDict, rigName)
    if len(controlEnumList) != 1:  # if more than 1 set of controls do switching
        hchySwitchCondPnts, hchySwitchCondVis = setupConditionNodesConstraints(controlEnumList, controlDict,
                                                                               controlGrpDict, objConstraintList,
                                                                               rigName, driverAttr, spineRotGrp)
    return controlEnumList, driverAttr, hchySwitchCondPnts, hchySwitchCondVis, objConstraintList


def createMessageNodeSetupSpline(messageManager, fkControlList, revfkControlList, floatControlList, spineControlList,
                                 spineRotControl):
    """Connects the message nodes to the spine controls

    :param messageManager: the message node name
    :type messageManager: str
    :param fkControlList:  list of the fk controls, can be empty
    :type fkControlList: list
    :param revfkControlList:  list of the revFk controls, can be empty
    :type revfkControlList: list
    :param floatControlList:  list of the float controls, can be empty
    :type floatControlList: list
    :param spineControlList:  list of the spine controls, can be empty
    :type spineControlList: list
    :param spineRotControl:  the extra spine rot control for the spine setup name
    :type spineRotControl: str
    """
    if fkControlList:
        for i, control in enumerate(fkControlList):
            cmds.addAttr(messageManager, longName="{}_{}".format(FKCTRL, i), attributeType='message')
            cmds.connectAttr('{}.message'.format(control), '.'.join([messageManager, "{}_{}".format(FKCTRL, i)]))
    if floatControlList:  # create/connect float attributes
        for i, control in enumerate(floatControlList):
            cmds.addAttr(messageManager, longName="{}_{}".format(FLOATCTRL, i), attributeType='message')
            cmds.connectAttr('{}.message'.format(control), '.'.join([messageManager, "{}_{}".format(FLOATCTRL, i)]))
    if revfkControlList:  # create/connect revFk attributes
        for i, control in enumerate(revfkControlList):
            cmds.addAttr(messageManager, longName="{}_{}".format(REVFKCTRL, i), attributeType='message')
            cmds.connectAttr('{}.message'.format(control), '.'.join([messageManager, "{}_{}".format(REVFKCTRL, i)]))
    if spineControlList:  # create connect spine attributes
        for i, control in enumerate(spineControlList):
            cmds.addAttr(messageManager, longName="{}_{}".format(SPINECTRL, i), attributeType='message')
            cmds.connectAttr('{}.message'.format(control), '.'.join([messageManager, "{}_{}".format(SPINECTRL, i)]))
        # create/connect spine midRot control attribute
        cmds.addAttr(messageManager, longName=SPINEMIDCTRL, attributeType='message')
        cmds.connectAttr('{}.message'.format(spineRotControl),
                         '.'.join([messageManager, SPINEMIDCTRL]))
    cmds.lockNode(messageManager, l=True)  # lock messageNodeManager


def cleanupSplineRig(fkGroupList, revfkGroupList, floatGroupList, spineGroupList, clusterList, rigName, splineIkList,
                     splineSolver, jointList, spineRotControl, cogControl, cogGroup, scaleGroup):
    """Parents the objects so that the spine rig all sits under one group. Creates extra groups, hides unwanted grps

    :param fkGroupList:
    :type fkGroupList:
    :param revfkGroupList:
    :type revfkGroupList:
    :param floatGroupList:
    :type floatGroupList:
    :param spineGroupList:
    :type spineGroupList:
    :param clusterList:
    :type clusterList:
    :param rigName:
    :type rigName:
    :param splineIkList:
    :type splineIkList:
    :param splineSolver:
    :type splineSolver:
    :param jointList:
    :type jointList:
    :param spineRotControl:
    :type spineRotControl:
    :param cogControl:
    :type cogControl:
    :param cogGroup:
    :type cogGroup:
    """
    # Spline ik group srt
    splinIkGrpContents = clusterList + [splineIkList[0], splineIkList[2]]
    splineIkGrp = cmds.group(empty=True, name="{}_splineIk_srt".format(rigName))
    for obj in splinIkGrpContents:
        cmds.parent(obj, splineIkGrp)
    # Parent rig structures to the cog
    cogParentContents = list()
    if floatGroupList:
        cogParentContents += floatGroupList
    if fkGroupList:
        cogParentContents.append(fkGroupList[0])
    if revfkGroupList:
        cogParentContents.append(revfkGroupList[-1])
    if spineGroupList:
        cogParentContents += [spineGroupList[0], spineGroupList[-1], spineRotControl[1]]
    for obj in cogParentContents:
        cmds.parent(obj, cogControl)
    # Create main grp and parent
    rigGrp = cmds.group(empty=True, name="{}_spineRig_srt".format(rigName))
    cmds.parent(splineIkGrp, cogGroup, jointList[0], rigGrp)
    cmds.parent(scaleGroup, rigGrp)
    cmds.setAttr('{}.visibility'.format(splineIkGrp), 0, lock=1)
    cmds.select(deselect=True)
    return rigGrp


"""
Spline Twist And Stretchy
"""


def advancedSplineIkTwist(splineIk, objStart, objectEnd, startVector=(0, 0, -1), endVector=(0, 0, -1)):
    """Sets up advanced ik twist on existing splineIK handle
    Currently obj rot up start and end

    :param splineIk: splineIk handle
    :type splineIk: str
    :param objStart: first obj for twist
    :type objStart: str
    :param objectEnd: second obj for twist
    :type objectEnd: str
    :param startVector: (0,0,1) start up vector
    :type startVector: tuple
    :param endVector: (0,0,1) end up vector
    :type endVector: tuple
    """
    cmds.setAttr("{}.dTwistControlEnable".format(splineIk), 1)  # advanced on
    cmds.setAttr("{}.dWorldUpType".format(splineIk), 4)  # obj rot up start/end
    # start/end objects
    cmds.connectAttr("{}.xformMatrix".format(objStart), "{}.dWorldUpMatrix".format(splineIk), force=True)
    cmds.connectAttr("{}.xformMatrix".format(objectEnd), "{}.dWorldUpMatrixEnd".format(splineIk), force=True)
    # start/end vectors
    cmds.setAttr("{}.dWorldUpVectorX".format(splineIk), startVector[0])
    cmds.setAttr("{}.dWorldUpVectorY".format(splineIk), startVector[1])
    cmds.setAttr("{}.dWorldUpVectorZ".format(splineIk), startVector[2])
    cmds.setAttr("{}.dWorldUpVectorEndX".format(splineIk), endVector[0])
    cmds.setAttr("{}.dWorldUpVectorEndY".format(splineIk), endVector[1])
    cmds.setAttr("{}.dWorldUpVectorEndZ".format(splineIk), endVector[2])


def jointStretchMultiplySetup(joints, curveInfo, splineCurve):
    """Sets up the "stretch" part of a squash/stretch component for a regular spline ik chain
    Returns a blend node (and multiplyDivideA) which can blend between the stretch and the non stretch modes
    The blend node attribute should later be hooked up to the controls

    :param joints: the joint names
    :type joints: list
    :param curveInfo: the curveInfo node name
    :type curveInfo: str
    :param splineCurve: the spline curve name
    :type splineCurve: str
    :return splineMultiplyNode: multiply/divide node
    :rtype splineMultiplyNode: str
    :return splineStretchBlendTwoAttr: spline stretch blend node
    :rtype splineStretchBlendTwoAttr: str
    :return multiplyStretchNodes: multiply nodes created if the joints have uneven lengths. Will be empty list if even.
    :rtype multiplyStretchNodes: list
    """
    # create multiplyDivide math node with settings
    splineCurveShort = namehandling.getShortName(splineCurve)
    name = namehandling.nonUniqueNameNumber('{}_multiplyDivideA'.format(splineCurveShort))  # unique name
    splineMultiplyNode = cmds.createNode('multiplyDivide', n=name)
    cmds.setAttr('{}.input2X'.format(splineMultiplyNode), len(joints) - 1)  # divide by number of joints
    cmds.setAttr('{}.operation'.format(splineMultiplyNode), 2)  # set to divide
    cmds.connectAttr('{}.arcLength'.format(curveInfo), '{}.input1X'.format(splineMultiplyNode))
    # The no scale initial value for no stretch (curve length / joint count)
    length = cmds.getAttr('{}.arcLength'.format(str(curveInfo))) / len(joints)
    cmds.setAttr('{}.input1Z'.format(str(splineMultiplyNode)), length)
    # stretch blend setup
    name = namehandling.nonUniqueNameNumber('{}_stretchBlendTwoAttr'.format(splineCurveShort))  # unique name
    splineStretchBlendTwoAttr = cmds.createNode('blendTwoAttr', n=name)
    cmds.connectAttr('{}.outputX'.format(splineMultiplyNode),
                     '{}.input[1]'.format(splineStretchBlendTwoAttr))  # stretch
    cmds.connectAttr('{}.input1Z'.format(splineMultiplyNode),
                     '{}.input[0]'.format(splineStretchBlendTwoAttr))  # no stretch
    cmds.setAttr('{}.attributesBlender'.format(splineStretchBlendTwoAttr), 1)
    """
    Connect The Joints While Checking For Varying Joint Length
    """
    sameLength = jointListLengthSame(joints)  # tests to see if all joints have the same length (x value)
    multiplyStretchNodes = list()
    if sameLength:  # then the connection can be a simple and same for each joint
        for jnt in joints:
            cmds.connectAttr('{}.output'.format(splineStretchBlendTwoAttr), '{}.translateX'.format(jnt))
    else:  # build a multiply node for every joint to account for joints that have different lengths
        for i, jnt in enumerate(joints):
            if i == 0:
                cmds.connectAttr('{}.output'.format(splineStretchBlendTwoAttr), '{}.translateX'.format(joints[0]))
                continue
            multiNode = cmds.createNode('multiplyDivide',
                                        name='multStrtch{}'.format(namehandling.getShortName(jnt)))
            multiplyStretchNodes.append(multiNode)
            jntLength = cmds.getAttr("{}.translateX".format(jnt))
            # set the multiplier from the even joint length = jntLength / (total length / joint count -1)
            evenLength = cmds.getAttr('{}.arcLength'.format(str(curveInfo))) / (len(joints) - 1)
            cmds.setAttr("{}.input1.input1X".format(multiNode), jntLength / evenLength)
            cmds.connectAttr('{}.output'.format(splineStretchBlendTwoAttr),
                             '{}.input2.input2X'.format(multiNode))
            cmds.connectAttr('{}.output.outputX'.format(multiNode), '{}.translateX'.format(jnt))
    return splineMultiplyNode, splineStretchBlendTwoAttr, multiplyStretchNodes


def jointSquashMultiplySetup(joints, splineCurve, curveInfo, splineMultiplyNode):
    """Sets up the stretch part of a squash/stretch component for a regular spline ik chain
    Returns a blend node (and multiplyDivideB) which can blend between the stretch and the non stretch modes
    also builds and returns the curve info node for measuring the length of the spline curve
    The blend node attribute should later be hooked up to the controls

    :param joints: the joint names
    :type joints: list
    :param splineCurve: the spline curve name
    :type splineCurve: str
    :param curveInfo: the curveInfo node name
    :type curveInfo: str
    :param splineMultiplyNode: multiply/divide node
    :type splineMultiplyNode: str
    :return splineSquashBlendTwoAttr: spline stretch blend 2 node
    :rtype splineSquashBlendTwoAttr: str
    :return splineMultiplyNode2: multiply/divide 2 node
    :rtype splineMultiplyNode2: string
    """
    cmds.connectAttr('{}.arcLength'.format(curveInfo), '{}.input1Y'.format(splineMultiplyNode))
    cmds.setAttr('{}.input2Y'.format(splineMultiplyNode), cmds.getAttr('{}.arcLength'.format(curveInfo)))
    splineCurveShort = namehandling.getShortName(splineCurve)
    name = namehandling.nonUniqueNameNumber('{}_multiplyDivideB'.format(splineCurveShort))  # unique name
    splineMultiplyNode2 = cmds.createNode('multiplyDivide', n=name)
    cmds.connectAttr('{}.outputY'.format(splineMultiplyNode), '{}.input2Y'.format(splineMultiplyNode2))
    cmds.setAttr('{}.input1Y'.format(splineMultiplyNode2), 1)
    cmds.setAttr('{}.operation'.format(splineMultiplyNode2), 2)  # set to divide
    # no scale value
    cmds.setAttr('{}.input1Z'.format(splineMultiplyNode2), 1)
    # squash blend setup
    name = namehandling.nonUniqueNameNumber('{}_squashBlendTwoAttr'.format(splineCurveShort))
    splineSquashBlendTwoAttr = cmds.createNode('blendTwoAttr', n=name)
    cmds.connectAttr('{}.outputY'.format(splineMultiplyNode2), '{}.input[1]'.format(splineSquashBlendTwoAttr))  # squash
    cmds.connectAttr('{}.input1Z'.format(splineMultiplyNode2),
                     '{}.input[0]'.format(splineSquashBlendTwoAttr))  # no squash
    cmds.setAttr('{}.attributesBlender'.format(splineSquashBlendTwoAttr), 1)
    for jnt in joints:
        cmds.connectAttr('{}.output'.format(splineSquashBlendTwoAttr), '{}.scaleY'.format(jnt))
        cmds.connectAttr('{}.output'.format(splineSquashBlendTwoAttr), '{}.scaleZ'.format(jnt))
    return splineSquashBlendTwoAttr, splineMultiplyNode2


def createStretchy(splineCurve, joints):
    """Builds the squash and stretch setup for regular spline ik
    The blend nodes are needed for later setup when assigning attributes to the controls (.attributesBlender attrs)
    Squash and Stretch can be mixed/multiplied independently
    Returned nodes
    curveInfo: node to measure the length of a curve
    splineMultiplyNode: multiplies to find the offset for x (length joints)

    :param splineCurve: the spline curve name
    :type splineCurve: str
    :param joints: the joint list
    :type joints: list
    :return curveInfo: the curve info node
    :rtype curveInfo: str
    :return splineMultiplyNode: the spline multiply node, multiplies to find the offset for x (length joints)
    :rtype splineMultiplyNode: str
    :return splineMultiplyNode2: the second spline multiply node?
    :rtype splineMultiplyNode2: str
    :return splineStretchBlendTwoAttr: the stretch blend two node name also used for attribute too I think
    :rtype splineStretchBlendTwoAttr: str
    :return splineSquashBlendTwoAttr: the stretch blend two node name aslo used for attribute too I think
    :rtype splineSquashBlendTwoAttr: str
    :return multiplyStretchNodes: the multiplyDivide stretch nodes
    :rtype multiplyStretchNodes: list
    """
    curveInfo = cmds.arclen(splineCurve, ch=True)  # create curve info node for measuring length of curve
    # stretch setup
    splineMultiplyNode, splineStretchBlendTwoAttr, multiplyStretchNodes = jointStretchMultiplySetup(joints, curveInfo,
                                                                                                    splineCurve)
    # squash setup
    splineSquashBlendTwoAttr, splineMultiplyNode2 = jointSquashMultiplySetup(joints, splineCurve, curveInfo,
                                                                             splineMultiplyNode)
    return curveInfo, splineMultiplyNode, splineMultiplyNode2, splineStretchBlendTwoAttr, \
           splineSquashBlendTwoAttr, multiplyStretchNodes


def stretchyConnectCntrlAttributes(stretchBlend, squashBlend, controlObj):
    """Adds and connects the squash and stretch setup to a control and creates 2 attributes
    - squash
    - stretch
    for multiplying the squash and stretch

    :param stretchBlend: the stretch blend node
    :type stretchBlend: str
    :param squashBlend: the squash blend node
    :type squashBlend: str
    :param controlObj: the control object where the control attributes go
    :type controlObj: str
    """
    cmds.addAttr(controlObj, longName='squash', attributeType='float',
                 keyable=1, defaultValue=1)
    cmds.addAttr(controlObj, longName='stretch', attributeType='float',
                 keyable=1, defaultValue=1)
    cmds.connectAttr('{}.squash'.format(controlObj), '{}.attributesBlender'.format(squashBlend))
    cmds.connectAttr('{}.stretch'.format(controlObj), '{}.attributesBlender'.format(stretchBlend))


def stretchyWorldScaleMod(cogControl, splineMultiplyNode2, rigName):
    """A mod that fixes world scale to the squash and stretch spline setup.

    Creates a grp that is scale constrained to the cog, this will keep world scale info, needs to be parented later.

    The scale_grp then feeds into a multiple node doubling it's size, this can be plugged into the splineMultiplyNode2 \
    to maintain world scale while scaling the entire rig.

    :param cogControl: The main cog control of the spine rig
    :type cogControl: str
    :param splineMultiplyNode2: node named splineRig_ikSplineCurve_multiplyDivideB a node that connects the curveInfo
    :type splineMultiplyNode2: str
    :param rigName: the name of the rig
    :type rigName: str
    :return scaleGroup: The name of the scaleGrp that was created to measure world scale of the rig.
    :rtype scaleGroup: str
    :return scaleMultiplyNode: The new multiply node that doubles the scaleGrp size
    :rtype scaleMultiplyNode: str
    :return scaleGroupConstraint: The scale constraint node, connects the cogControl to the scaleGrp
    :rtype scaleGroupConstraint: str
    """
    # create group
    scaleGroup = cmds.group(empty=True, name="{}_measure_scale_grp".format(rigName))
    # scale constrain group
    scaleGroupConstraint = cmds.scaleConstraint([cogControl, scaleGroup])
    # create multiply and divide
    scaleMultiplyNode = cmds.createNode('multiplyDivide', n="{}_worldScale_mult".format(rigName))
    # connect the scale grp to the multiply node for the double math
    cmds.connectAttr('{}.scaleX'.format(scaleGroup),
                     '{}.input1.input1X'.format(scaleMultiplyNode))
    cmds.connectAttr('{}.scaleX'.format(scaleGroup),
                     '{}.input2.input2X'.format(scaleMultiplyNode))
    # connect to the live multiply node
    cmds.connectAttr('{}.output.outputX'.format(scaleMultiplyNode),
                     '{}.input1.input1Y'.format(splineMultiplyNode2))
    return scaleGroup, scaleMultiplyNode, scaleGroupConstraint


"""
Misc
"""


def all_same(items):
    """tests if all items in a list are the same

    :param items: any python list
    :type items: list
    :return same: True if all items are the same
    :rtype same: bool
    """
    return all(x == items[0] for x in items)


def jointListLengthSame(jointList):
    """checks to see if all the lengths of joints are the same ignoring the first joint

    :param jointList: joint names
    :type jointList: list
    :return lengthSame: is every joint the same distance apart?
    :rtype lengthSame: bool
    """
    jointLengthList = list()
    for jnt in jointList[1:]:  # skip first joint as it's always 0
        jointLengthList.append(cmds.getAttr("{}.translateX".format(jnt)))
    lengthSame = all_same(jointList)
    return lengthSame


"""
Control Cluster Curve
"""


def controlsClusterCurve(splineCurve, partPrefixName="", scale=(1.0, 1.0, 1.0), design="cube", relative=False,
                         showHandles=False,
                         rgbColor=(0.0, 0.0, 1.0), padding=2):
    """Creates clusters parented to controls from a spline curve. The spline be a transform or a nurbsCurve shape

    Uses:
        deformers.createClustersOnCurve()
        controls.createControlsMatchList()

    :param splineCurve: The name of the spline curve to create the clusters, can be a transform or a nurbsCurve shape
    :type splineCurve: str
    :param partPrefixName: The prefix, name of the rig/part, optional, can be an empty string (auto), is a shortname
    :type partPrefixName: str
    :param relative: If True only the transformations directly above the cluster are used by the cluster.
    :type relative: bool
    :param showHandles: If True show the Maya handles display mode, little crosses on each handle
    :type showHandles: bool
    :param padding: The numerical padding
    :type padding: int
    :param scale: The scale size of the curves to be created in x y z (1.0, 1.0, 1.0)
    :type scale: tuple(float)
    :param design: The name of the shape to create from the shape library
    :type design: str
    """
    if cmds.objectType(splineCurve) != "transform":  # be sure splineCurve is a transform for coloring and attrQuery
        splineCurve = cmds.listRelatives(splineCurve, parent=True, fullPath=True)
    if cmds.attributeQuery(CLSTRCRVE_SPLINE_ATTR, node=splineCurve, exists=True):
        cmds.deleteAttr(splineCurve, at=CLSTRCRVE_SPLINE_ATTR)  # delete leftover attr in case of user error
    objcolor.setColorListRgb([splineCurve], rgbColor, colorShapes=True, displayMessage=True, linear=True)
    # Create Clusters  --------------------------
    clusterPairs = deformers.createClustersOnCurve(partPrefixName,
                                                   splineCurve,
                                                   relative=relative,
                                                   showHandles=showHandles,
                                                   padding=padding)
    clusterList = clusterTransforms(clusterPairs)
    clusterListUuid = cmds.ls(clusterList, uuid=True)
    # Create Controls  --------------------------
    controlList, controlGroupList = controls.createControlsMatchList(clusterList,
                                                                     curveScale=scale,
                                                                     rotateOffset=(0, 0, 0),
                                                                     designName=design,
                                                                     grp=True,
                                                                     rgbColor=rgbColor)
    controlListUuid = cmds.ls(controlList, uuid=True)
    controlGroupListUuid = cmds.ls(controlGroupList, uuid=True)
    for i, cluster in enumerate(clusterList):  # hide clusters
        cmds.parent(cluster, controlList[i])[0]
        cmds.setAttr("{}.visibility".format(cluster), False)
    if not partPrefixName:
        partPrefixName = namehandling.mayaNamePartTypes(splineCurve)[2]  # get pure name
    else:
        cmds.rename(splineCurve, "{}_spline".format(partPrefixName))
    rigGroup = cmds.group(controlGroupList, name="{}_controls_grp".format(partPrefixName))
    # Template splineCurve  --------------------------
    shapenodes.templateRefShapeNodes(splineCurve, template=True, message=False)
    # Get full names  --------------------------
    controlList = cmds.ls(controlListUuid, long=True)
    clusterList = cmds.ls(clusterListUuid, long=True)
    controlGroupList = cmds.ls(controlGroupListUuid, long=True)
    # Create Network node and message connections --------------------------
    networkName = "".join([partPrefixName, CLSTRCRVE_NETWORK_SFX])
    networkName = nodes.messageNodeObjs(networkName, clusterList, CLSTRCRVE_CLUSTERS_ATTR, createNetworkNode=True)
    nodes.messageNodeObjs(networkName, controlList, CLSTRCRVE_CONTROL_ATTR, createNetworkNode=False)
    nodes.messageNodeObjs(networkName, controlGroupList, CLSTRCRVE_RIGGROUP_ATTR, createNetworkNode=False)
    nodes.messageNodeObjs(networkName, [splineCurve], CLSTRCRVE_SPLINE_ATTR, createNetworkNode=False)
    nodes.messageNodeObjs(networkName, [rigGroup], CLSTRCRVE_RIGGROUP_ATTR, createNetworkNode=False)


def controlsClusterCurveSelected(partPrefixName="", scale=(1.0, 1.0, 1.0), design="cube", relative=False,
                                 showHandles=False,
                                 rgbColor=(0.0, 0.0, 1.0), padding=2, message=True):
    """Creates clusters parented to controls from a selected spline curve.

    :param partPrefixName:  The prefix, name of the rig/part, optional, can be an empty string (auto), is a shortname
    :type partPrefixName: str
    :param relative:  If True only the transformations directly above the cluster are used by the cluster.
    :type relative: bool
    :param showHandles:  If True show the Maya handles display mode, little crosses on each handle
    :type showHandles: bool
    :param padding:  The numerical padding
    :type padding: int
    :param scale: the scale size of the curves to be created in x y z (1.0, 1.0, 1.0)
    :type scale: tuple(float)
    :param design: the name of the shape to create from the shape library
    :type design: str
    :param message: Report the message to the user?
    :type message: bool
    :return splineTransform: the spline transform name, empty string if none found
    :rtype splineTransform: str
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        if message:
            om2.MGlobal.displayWarning("Nothing selected. Please select a curve")
        return ""
    splineShape = shapenodes.transformHasShapeOfType(selObjs[0], "nurbsCurve")
    if not splineShape:
        if message:
            om2.MGlobal.displayWarning("Please select a curve.")
        return ""
    controlsClusterCurve(selObjs[0], partPrefixName=partPrefixName, scale=scale, design=design,
                         relative=relative, showHandles=showHandles, rgbColor=rgbColor, padding=padding)
    return selObjs[0]


def getClusterCurveNetworkNodes(nodeList):
    """From a node list return the Cluster Curve Network node/s

    :param nodeList: Any objects related to the controlsClusterCurve() setup, auto finds network nodes
    :type nodeList: list
    :return networkNodeList: A list of network nodes, one for each Cluster Curve Spline rig
    :rtype networkNodeList:
    """
    networkNodeList = list()
    for attr in CLSTRCRVE_ATTR_LIST:
        networkNodeList += nodes.getNodeAttrConnections(nodeList, attr)
    return list(set(networkNodeList))  # remove duplicates


"""
Delete Cluster Curve
"""


def deleteClusterCurve(nodeList, deleteSpline=False, deleteHistory=True, message=True):
    """Removes the rig, and optionally the original spline curve of a controlsClusterCurve() setup

    Pass in any object/s of the Cluster Curve Rig, will find the associated network nodes and delete the rig/setup.

    :param nodeList: Any objects related to the controlsClusterCurve() setup, auto finds all objects from network nodes
    :type nodeList: list
    :param deleteSpline: If True deletes the whole setup including the original spline curve, False leaves the spline.
    :type deleteSpline: bool
    :param deleteHistory: If the spline is left, delete it's history so that it doesn't assume it's old shape.
    :type deleteHistory: bool
    :param message: Report the message to the user
    :type message: bool
    """
    networkNodeList = getClusterCurveNetworkNodes(nodeList)
    if not networkNodeList:
        if message:
            om2.MGlobal.displayWarning("No Cluster Curve Spline rigs found.")
        return
    splineList = nodes.getNodeAttrConnections(networkNodeList, CLSTRCRVE_SPLINE_ATTR)
    if deleteHistory:  # del history on the original curve
        for spline in splineList:
            cmds.delete(spline, constructionHistory=True)
    # Delete ------------------------
    for attr in CLSTRCRVE_ATTR_LIST[:-1]:  # don't iterate over the last which is the spline
        cmds.delete(nodes.getNodeAttrConnections(networkNodeList, attr))
    if deleteSpline:
        cmds.delete(splineList)
    else:  # reset the spline color
        objcolor.resetOverrideObjColorList(splineList, colorShapes=True)
        for spline in splineList:  # delete the rig connection attribute
            cmds.deleteAttr(spline, at=CLSTRCRVE_SPLINE_ATTR)
            shapenodes.templateRefShapeNodes(spline, template=True, message=False, unTemplateRef=True)  # un-template
    cmds.delete(networkNodeList)
    # Message -------------------------
    if message:
        om2.MGlobal.displayInfo("Success: Deleted Cluster Curve Rig connected "
                                "to the network/s {}".format(networkNodeList))


def deleteClusterCurveSelected(deleteSpline=False, message=True):
    """From selected removes the rig, and optionally the original spline curve of a controlsClusterCurve() setup

    :param deleteSpline: If True deletes the whole setup including the original spline curve, False leaves the spline.
    :type deleteSpline: bool
    :param message: Report the message to the user
    :type message: bool
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        om2.MGlobal.displayWarning("No objects selected. Please select any Zoo Cluster Curve Rig objects")
        return
    deleteClusterCurve(selObjs, deleteSpline=False, message=True)


"""
Toggle Visibility And Template Cluster Curve Rig
"""


def visControlsClusterCurve(controls, splineCurve, show=True):
    """Shows or hides the controls of Cluster Curve rig/s.  Main curve is template/un-templated

    :param controls: The control list of the Cluster Curve rig/s
    :type controls: list(str)
    :param splineCurve: The main spline curve list of the Cluster Curve rig/s
    :type splineCurve: list(str)
    :param show: Show the controls (True) or hide them (False)
    :type show: bool
    """
    vis = show
    for ctrl in controls:
        cmds.setAttr("{}.visibility".format(ctrl), vis)
    for spline in splineCurve:
        shapenodes.templateRefShapeNodes(spline, template=True, message=False, unTemplateRef=not vis)
        cmds.setAttr("{}.visibility".format(spline), 1)  # always show curve


def toggleVisClusterCurve(nodeList, message=True):
    """Toggles the controls of Cluster Curve rig/s.  Main curve is template/un-templated

    :param nodeList: Any objects related to the controlsClusterCurve() setup, auto finds all objects from network nodes
    :type nodeList: list
    :param message: Report the message to the user?
    :type message: bool
    """
    networkNodeList = getClusterCurveNetworkNodes(nodeList)
    if not networkNodeList:
        if message:
            om2.MGlobal.displayWarning("No Cluster Curve Rigs found in the current selection")
            return
    splineList = nodes.getNodeAttrConnections(networkNodeList, CLSTRCRVE_SPLINE_ATTR)
    controls = nodes.getNodeAttrConnections(networkNodeList, CLSTRCRVE_CONTROL_ATTR)
    if cmds.getAttr("{}.visibility".format(controls[0])):  # if control 1 is visible hide controls un-template spline
        visControlsClusterCurve(controls, splineList, show=False)
    else:  # else show and template
        visControlsClusterCurve(controls, splineList, show=True)


def toggleVisClusterCurveSelected(message=True):
    """Toggles the controls of Cluster Curve rig/s from any selected object on the rig.
    Main curve is template/un-templated

    :param message: Report the message to the user?
    :type message: bool
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        om2.MGlobal.displayWarning("No objects selected. Please select any Zoo Cluster Curve Rig objects")
        return
    toggleVisClusterCurve(selObjs, message=message)


def toggleTemplateClusterCurve(nodeList, message=False):
    """Toggles the template state of the main curve on the ClusterCurve rig.

    :param nodeList: Any objects related to the controlsClusterCurve() setup, auto finds all objects from network nodes
    :type nodeList: list
    :param message: Report the message to the user?
    :type message: bool
    """
    networkNodeList = getClusterCurveNetworkNodes(nodeList)
    if not networkNodeList:
        if message:
            om2.MGlobal.displayWarning("No Cluster Curve Rigs found in the current selection")
            return
    splineList = nodes.getNodeAttrConnections(networkNodeList, CLSTRCRVE_SPLINE_ATTR)
    shapes = cmds.listRelatives(splineList[0], shapes=True, fullPath=True)
    if not shapes:
        return
    overrideAttr = cmds.getAttr("{}.overrideEnabled".format(shapes[0]))
    displayTypeAttr = cmds.getAttr("{}.overrideDisplayType".format(shapes[0]))
    if overrideAttr and displayTypeAttr == 1:  # then the first spline is templated so un-template
        for spline in splineList:
            shapenodes.templateRefShapeNodes(spline, message=False, unTemplateRef=True)
        if message:
            om2.MGlobal.displayInfo("Curve/s are un-templated: {}".format(splineList))
    else:  # template the curve
        for spline in splineList:
            shapenodes.templateRefShapeNodes(spline, message=False, unTemplateRef=False)
        if message:
            om2.MGlobal.displayInfo("Curve/s are templated: {}".format(splineList))


def toggleTemplateClstrCrvSelected(message=True):
    """Toggles template state of the main curve in the Cluster Curve rig/s from any selected rig object.

    :param message: Report the message to the user?
    :type message: bool
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        om2.MGlobal.displayWarning("No objects selected. Please select any Zoo Cluster Curve Rig objects")
        return
    toggleTemplateClusterCurve(selObjs, message=message)


"""
Cluster Crv Get Controls
"""


def getClstrCrvSelected(message=True, attr=CLSTRCRVE_CONTROL_ATTR):
    """Returns a list of control curves from any selected control on the rig"""
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        om2.MGlobal.displayWarning("No objects selected. Please select any Zoo Cluster Curve Rig objects")
        return list()
    networkNodeList = getClusterCurveNetworkNodes(selObjs)
    if not networkNodeList:
        if message:
            om2.MGlobal.displayWarning("No Cluster Curve Rigs found in the current selection")
            return list()
    return nodes.getNodeAttrConnections(networkNodeList, attr)
