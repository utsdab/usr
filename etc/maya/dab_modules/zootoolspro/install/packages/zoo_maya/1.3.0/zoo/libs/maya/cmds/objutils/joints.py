import maya.cmds as cmds
import maya.api.OpenMaya as om2

from zoo.libs.maya.cmds.objutils import namehandling
from zoo.libs.maya.cmds.display import viewportmodes
from zoo.libs.maya.cmds.math import mayadag
from zoo.libs.maya.cmds.objutils import moveorient, mesh


UP_VECTOR_WORDS_LIST = ["xup", "xdown", "yup", "ydown", "zup", "zdown"]
UP_VECTOR_POSNEG_LIST = ["+x", "-x", "+y", "-y", "+z", "-z"]


# ------------------------------
# GET JOINTS
# ------------------------------


def filterChildJointList(jointList):
    """retrieves all joints under the joint list in the hierarchy, all child joints

    :param jointList: a list of Maya joints
    :type jointList: list
    :return allJoints: a join list now including children
    :rtype allJoints: list
    """
    allJoints = list()
    for joint in jointList:
        allJoints.append(joint)
        tempJntList = cmds.listRelatives(joint, allDescendents=True, type="joint", fullPath=True)
        if tempJntList:
            allJoints += tempJntList
    return list(set(allJoints))  # remove duplicates


def getJoints(objList, children=True):
    """From an object list filter out the joints, with option for children
    No duplicates

    :param objList: maya object list of strings
    :type objList: list
    :param children: return the child joints of all objects in the objList
    :type children: bool
    :return jntList: list of maya joints as strings
    :rtype jntList: list
    """
    jntList = cmds.ls(objList, type="joint", long=True)
    if children:
        childJnts = cmds.listRelatives(objList, children=True, type="joint", fullPath=True,
                                       allDescendents=True)
        if childJnts:
            jntList = list(set(jntList).union(set(childJnts)))
    return jntList


def getJointsSelected(children=True):
    """from selection return all the joints and most likely all the children too

    :param children: return the child joints of all objects in the objList
    :type children: bool
    :return jntList: list of maya joints as strings
    :rtype jntList: list
    """
    selectedObjs = cmds.ls(selection=True, long=True)
    jntList = getJoints(selectedObjs, children=children)
    return jntList


def getJointChain(startJoint, endJoint=""):
    """Returns a joint list in the order of hierarchy between the start join and the end joint.

    Will check for branches if an endJoint is specified, does not check branches it only start joint is given.

    If the end joint is not given it will return the entire chain.

    :param startJoint: The start joint name of the joint chain
    :type startJoint: str
    :param endJoint: The end joint name of the chain, if "" will return all joints under the first joint.
    :type endJoint: str
    :return jointList: The list of joint names in the chain
    :rtype jointList: list(str)
    """
    # return all joints under the start joint
    startJoint = namehandling.getLongNameFromShort(startJoint)  # force long name
    if endJoint:  # force long name
        endJoint = namehandling.getLongNameFromShort(endJoint)
    startJointChildren = cmds.listRelatives(startJoint, children=True, type="joint", fullPath=True,
                                            allDescendents=True)
    startJointChildren.reverse()
    jointList = [startJoint] + startJointChildren
    if endJoint:  # filter out any other joints
        if endJoint not in startJointChildren:
            return list()  # is not a child of the start joint so is not a legit joint chain
        endJointChildren = cmds.listRelatives(endJoint, children=True, type="joint", fullPath=True,
                                              allDescendents=True)
        # remove joints that are children of the end joint
        if endJointChildren:
            for joint in endJointChildren:
                jointList.remove(joint)
        # remove joints that do not have the end joint as a child, ie in another branch and not in the same chain.
        jointCheckList = list(jointList)
        jointCheckList.remove(startJoint)
        jointCheckList.remove(endJoint)
        for joint in jointCheckList:
            children = cmds.listRelatives(joint, children=True, type="joint", fullPath=True,
                                          allDescendents=True)
            if children:
                if endJoint not in children:
                    jointList.remove(joint)
            else:  # has no children so end joint is not a child.
                jointList.remove(joint)
    else:
        pass  # could figure if chains have branches, currently returns all descendants
    return jointList


# ------------------------------
# JOINT DRAW (DISPLAY)
# ------------------------------


def jointDrawNone(jntList):
    """hides joints without affecting the .visibility attr
    uses drawStyle to None

    :param jntList: list of maya joints as strings
    :type jntList: list
    """
    for jnt in jntList:
        cmds.setAttr('{}.drawStyle'.format(jnt), 2)


def jointDrawNoneSelected(children=True):
    """hides joints without affecting the .visibility attr
    uses drawStyle to None

    :param children: should child joints also be affected?
    :type children: Boolean
    """
    jntList = getJointsSelected(children=children)
    if not jntList:
        om2.MGlobal.displayWarning("No Joints Found")
        return
    jointDrawNone(jntList)


def jointDrawBone(jntList):
    """displays joints regular style
    via drawStyle to bone

    :param jntList: list of maya joints as strings
    :type jntList: list
    """
    for jnt in jntList:
        cmds.setAttr('{}.drawStyle'.format(jnt), 0)


def jointDrawBoneSelected(children=True):
    """displays joints regular style
    via drawStyle to bone

    :param children: should child joints also be affected?
    :type children: Boolean
    """
    jntList = getJointsSelected(children=children)
    if not jntList:
        om2.MGlobal.displayWarning("No Joints Found")
        return
    jointDrawBone(jntList)


def toggleJntDrawStyle(jntList):
    """Toggles the visibility of joints without affecting the .visibility attribute
    uses the attribute drawStyle
    Finds the first selected and toggles all joints opposite of that

    :param jntList: list of maya joints as strings
    :type jntList: list
    """
    if not cmds.getAttr('{}.drawStyle'.format(jntList[0])):
        jointDrawNone(jntList)
    else:
        jointDrawBone(jntList)


def toggleJntDrawStyleSelected(children=True):
    """Toggles the visibility of joints without affecting the .visibility attribute
    uses the attribute drawStyle
    Finds the first selected and toggles all joints opposite of that
    Can affect children

    :param children: should child joints also be affected?
    :type children: Boolean
    """
    jntList = getJointsSelected(children=children)
    if not jntList:
        om2.MGlobal.displayWarning("No Joints Found")
        return
    toggleJntDrawStyle(jntList)


# ------------------------------
# ZERO ROT AXIS
# ------------------------------


def zeroRotAxisJointList(jointList, zeroChildren=True):
    """Zero's the Joint Rotation Axis, as the manual rotation of the axis is bad for joints

    :param jointList: The list of maya joints
    :type jointList: list
    :param zeroChildren: Do you want this to affect all children as well?
    :type zeroChildren: bool
    :return:
    :rtype:
    """
    if zeroChildren:
        jointList = filterChildJointList(jointList)
    for joint in jointList:
        cmds.joint(joint, edit=True, zeroScaleOrient=True)


def zeroRotAxisSelected(zeroChildren=True, message=True):
    """Zero's the Joint Rotation Axis, as the manual rotation of the axis is bad for joints
    Works on selection

    :param zeroChildren: Do you want this to affect all children as well?
    :type zeroChildren: bool
    """
    selectedJoints = cmds.ls(selection=True, exactType="joint", long=True)
    if not selectedJoints:
        if message:
            om2.MGlobal.displayWarning('No joints selected. Please select some joints.')
        return
    zeroRotAxisJointList(selectedJoints, zeroChildren=zeroChildren)
    if message:
        om2.MGlobal.displayInfo('Success:  Joints rotation axis zeroed')


# ------------------------------
# DISPLAY LRA
# ------------------------------


def displayLocalRotationAxisJointList(jntList, children=True, display=True, message=True):
    """Function for showing or hiding the Local Rotation Axis on an object list, usually joints

    :param children: Include all children?
    :type children: bool
    :param display: Show or hide?
    :type display: bool
    :param message: Report message to the user?
    :type message: bool
    """
    if not jntList:
        if message:
            om2.MGlobal.displayWarning("No joints selected. Please select joints.")
        return
    if children:
        jntList = filterChildJointList(jntList)  # adds the children
    for jnt in jntList:
        cmds.setAttr('{}.displayLocalAxis'.format(jnt), display)
        if message:
            om2.MGlobal.displayInfo("Joint local rotation axis visibility set to {}".format(display))


def displayLocalRotationAxisSelected(children=True, display=True, message=True):
    """Function for showing or hiding the Local Rotation Axis on selected objects, usually joints

    :param children: Include all children?
    :type children: bool
    :param display: Show or hide?
    :type display: bool
    :param message: Report message to the user?
    :type message: bool
    """
    selectedJoints = cmds.ls(selection=True, long=True, exactType="joint")
    displayLocalRotationAxisJointList(selectedJoints, children=children, display=display, message=message)
    # make sure handles are on in current view panel
    currentPanel = viewportmodes.panelUnderPointerOrFocus(viewport3d=True, message=False)
    cmds.modelEditor(currentPanel, edit=True, handles=True)


def toggleLocalRotationAxisSelection(children=False, message=True):
    """Toggles the Local Rotation Axis on selected objects, usually joints

    :param children: Include all children?
    :type children: bool
    :param message: Report message to the user?
    :type message: bool
    """
    selectedJoints = cmds.ls(selection=True, exactType="joint", long=True)
    if not selectedJoints:
        if message:
            om2.MGlobal.displayWarning('No joints selected. Please select some joints.')
        return
    LRA_Vis = cmds.getAttr('{}.displayLocalAxis'.format(selectedJoints[0]))
    # invert the selection LRA vis state
    displayLocalRotationAxisJointList(selectedJoints, children=children, display=not LRA_Vis, message=message)


# ------------------------------
# ALIGN FUNCTIONS
# ------------------------------


def alignJoint(jointList, secondaryAxisOrient="yup", children=False, freezeJnt=True, message=False):
    """Aligns the joints given a joint list

    :param jointList: The joint names to orient
    :type jointList: list
    :param secondaryAxisOrient: Second axis orient "xup", "xdown", "yup", "ydown", "zup", "zdown", or "none"
    :type secondaryAxisOrient: str
    :param freezeJnt: Freeze the joint before orienting?
    :type freezeJnt: bool
    :param children: Also orient the children?
    :type children: bool
    :param message: Show the message to the user?
    :type message: bool
    """
    if freezeJnt:
        cmds.makeIdentity(jointList, apply=True, scale=True, rotate=True, translate=True)
    cmds.joint(jointList, edit=True, orientJoint="xyz", secondaryAxisOrient=secondaryAxisOrient,
               children=children)
    if message:
        om2.MGlobal.displayInfo("Joints Aligned: {}".format(jointList))


def checkHasChildJoint(joint):
    """Searches for a child joint, only searches two deep

    :param joint: A maya joint name
    :type joint: str
    :return hasChildJoint: True if a child joint is found
    :rtype hasChildJoint: bool
    """
    if cmds.listRelatives(joint, children=True, type="joint", fullPath=True):
        return True
    children = cmds.listRelatives(joint, children=True, fullPath=True)
    if not children:  # no children at all
        return False
    for child in cmds.listRelatives(joint, children=True, fullPath=True):
        if cmds.listRelatives(child, children=True, type="joint"):
            return True  # joint found under child of joint
    return False  # no joints found 2 levels deep


def alignJointSelected(secondaryAxisOrient="yup", children=False, message=True, endAlignParent=True):
    """Aligns the joints that are selected

    :param secondaryAxisOrient: second axis orient "xup", "xdown", "yup", "ydown", "zup", "zdown", or "none"
    :type secondaryAxisOrient: str
    :param children: also orient the children?
    :type children: bool
    :param message: show the message to the user?
    :type message: bool
    """
    jointsToAlign = list()
    jointsToParentAlign = list()
    selectedJoints = cmds.ls(selection=True, exactType="joint", long=True)
    if not selectedJoints:
        if message:
            om2.MGlobal.displayWarning("No joints selected.  Please select some joints.")
        return
    if children:
        allJoints = filterChildJointList(selectedJoints)
    else:
        allJoints = selectedJoints
    for joint in allJoints:
        if checkHasChildJoint(joint):
            jointsToAlign.append(joint)
        else:
            jointsToParentAlign.append(joint)
    if jointsToAlign:  # align joints
        # ignore children is already in the list
        alignJoint(jointsToAlign, secondaryAxisOrient=secondaryAxisOrient, children=False, message=message)
    if jointsToParentAlign and endAlignParent:  # align these joints to parent
        alignJointToParentList(jointsToParentAlign)


def alignJointToParent(jnt):
    """Align Joints To Parent useful for end joints
    Uses orient constraint (while temp unparenting children) to reorient the joint to match it's parent
    Freezes the Joint transforms bfore reparenting children

    :param jnt: the joint to be aligned
    :type jnt: str
    """
    children = cmds.listRelatives(jnt, children=True, fullPath=True)
    parentJnt = cmds.listRelatives(jnt, parent=True, fullPath=True)
    if children:
        children = cmds.parent(children, world=True)
    cmds.delete(cmds.orientConstraint(parentJnt[0], jnt, maintainOffset=False))
    cmds.makeIdentity(jnt, apply=True, r=True)
    if children:
        cmds.parent(children, jnt)


def alignJointToParentList(jntList):
    for jnt in jntList:
        alignJointToParent(jnt)


def alignJointToParentSelected(message=True):
    """Align Joints To Parent useful for end joints
    Uses orient constraint (while temp unparenting children) to reorient the joint to match it's parent
    Freezes the Joint transforms before reparenting children

    :param message: display the success message to the user
    :type message: bool
    """
    selectedJoints = cmds.ls(selection=True, exactType="joint", long=True)
    if not selectedJoints:
        if message:
            om2.MGlobal.displayWarning("No joints found.  Please select some joints.")
        return
    alignJointToParentList(selectedJoints)
    # because Maya screws selection with cmds.parent, return to original selection
    cmds.select(selectedJoints, replace=True)
    if message:
        om2.MGlobal.displayInfo("Success: Joints Aligned to their parent {}".format(selectedJoints))


# ------------------------------
# EDIT MANUAL LRA
# ------------------------------


def editComponentLRA(editLRA=True):
    """Makes the local rotation axis editable in component mode, when False will disable and exit to object mode

    :param editLRA: When True will enter the component mode with localRotationAxis editable, False exits
    :type editLRA: bool
    """
    if editLRA:
        cmds.selectMode(component=True)
        cmds.selectType(localRotationAxis=True)
        # make sure handles are visible in the current panel
        currentPanel = viewportmodes.panelUnderPointerOrFocus(viewport3d=True, message=False)
        cmds.modelEditor(currentPanel, edit=True, handles=True)
    else:
        cmds.selectType(localRotationAxis=False)
        cmds.selectMode(object=True)


# ------------------------------
# ROTATE LRA
# ------------------------------


def rotateLRA(obj, rot):
    """Will rotate the local rotation axis of the given object usually a joint by the rotation amount.

    :param obj: A Maya object name, usually a joint, must be a transform
    :type obj: str
    :param rot: the rotation offset a list [0.0, 90.0, 0.0]
    :type rot: list(float)
    """
    cmds.rotate(rot[0], rot[1], rot[2], "{}.rotateAxis".format(obj), objectSpace=True, forceOrderXYZ=True)
    if cmds.objectType(obj) == "joint":  # then freeze the orientation too
        cmds.joint(obj, edit=True, zeroScaleOrient=True)


def rotateLRAList(objList, rot):
    """Will rotate the local rotation axis of the given object list usually a joint list by the rotation amount.

    :param objList: A list of Maya object names, usually joints, must be a transforms
    :type objList: str
    :param rot: the rotation offset a list [0.0, 90.0, 0.0]
    :type rot: list(float)
    """
    for obj in objList:
        rotateLRA(obj, rot)


def rotateLRASelection(rot, includeChildren=True):
    """Will rotate the local rotation axis of the given object list usually a joint list by the rotation amount.

    :param rot: the rotation offset a list [0.0, 90.0, 0.0]
    :type rot: list(float)
    :param includeChildren: include the hierarchy (children) in the operation
    :type includeChildren: bool
    """
    jointList = cmds.ls(selection=True, long=True, type="joint")
    if includeChildren:  # then include all joint children
        jointList = filterChildJointList(jointList)
    rotateLRAList(jointList, rot)


# ------------------------------
# MIRROR JOINTS
# ------------------------------


def mirrorJoint(joint, axis, searchReplace=(["_L", "_R"], ["_lft", "_rgt"])):
    """Mirrors a joint along an axis

    Finds the first search string in the list and will do the mirror based on that two entry list.
    ie. Will not search all lists, only the first matching string it finds.

    :param joint: The name of the Maya joint
    :type joint: str
    :param axis: the axis to mirror across, "X", "Y", "Z"
    :type axis: str
    :param searchReplace: a tuple of lists, with the search and replace text (["_L", "_R"], ["_lft", "_rgt"])
    :type searchReplace: tuple(list(str))
    :return jointList: A list of joint names
    :rtype jointList: list(str)
    """
    # get all joints
    origJointList = [joint]
    orgJoinDescendants = cmds.listRelatives(joint, allDescendents=True, type="joint")
    if orgJoinDescendants:
        origJointList += reversed(orgJoinDescendants)
    searchList = ["", ""]  # No search
    if searchReplace:  # Finds the first matching search string in the joint list, will be list() if None
        for i, sList in enumerate(searchReplace):
            for jnt in origJointList:
                if sList[0] in jnt:  # first value is a match
                    searchList = sList
                    break
                elif sList[1] in jnt:  # then the second value is a match
                    sList.reverse()
                    searchList = sList
                    break
    # Does the mirror with cmds
    if axis == "X":
        jointList = cmds.mirrorJoint(joint, mirrorYZ=True, mirrorBehavior=True, searchReplace=searchList)
    elif axis == "Y":
        jointList = cmds.mirrorJoint(joint, mirrorXZ=True, mirrorBehavior=True, searchReplace=searchList)
    else:  # "Z"
        jointList = cmds.mirrorJoint(joint, mirrorXY=True, mirrorBehavior=True, searchReplace=searchList)
    return jointList


def mirrorJointList(jointList, axis, searchReplace=(["_L", "_R"], ["_lft", "_rgt"])):
    """Mirrors a joint list along an axis

    :param jointList: The list of jnt names
    :type jointList: list(str)
    :param axis: the axis to mirror across, "X", "Y", "Z"
    :type axis: str
    :param searchReplace: a tuple of lists, with the search and replace text (["_L", "_R"], ["_lft", "_rgt"])
    :type searchReplace: tuple(list(str))
    :return jointList: A list of joint names
    :rtype jointList: list(str)
    """
    mirroredJointList = list()
    for joint in jointList:
        mirroredJointList += mirrorJoint(joint, axis, searchReplace=searchReplace)
    return mirroredJointList


def mirrorJointSelected(axis, searchReplace=(["_L", "_R"], ["_lft", "_rgt"]), message=True):
    """Mirrors selected joints along an axis

    :param axis: the axis to mirror across, "X", "Y", "Z"
    :type axis: str
    :param searchReplace: a tuple of lists, with the search and replace text (["_L", "_R"], ["_lft", "_rgt"])
    :type searchReplace: tuple(list(str))
    :param message: report the message to the user?
    :type message: bool
    :return jointList: A list of joint names
    :rtype jointList: list(str)
    """
    selJoints = cmds.ls(selection=True, type="joint", long=True)
    if not selJoints:
        if message:
            om2.MGlobal.displayWarning("Nothing selected. Please select joints.")
        return list()
    return mirrorJointList(selJoints, axis, searchReplace=searchReplace)


# ------------------------------
# SIZE AND RADIUS
# ------------------------------


def setJointRadiusSelected(radius, children=False, message=True):
    """Sets the joint radius for selected joints and potentially their children.

    :param radius: The radius attribute size
    :type radius: float
    :param children: Include all child joints while adjusting the radius?
    :type children: bool
    :param message: Report the message to the user
    :type message: bool
    """
    selJoints = cmds.ls(selection=True, type="joint", long=True)
    if not selJoints:
        if message:
            om2.MGlobal.displayWarning("Nothing selected. Please select joints.")
        return
    if children:
        selJoints = filterChildJointList(selJoints)
    for joint in selJoints:
        cmds.setAttr("{}.radius".format(joint), radius)


# ------------------------------
# BUILD FUNCTIONS
# ------------------------------


def buildJointStraight(jntName="joint", suffixName="", jointCount=10, jointSpacing=2):
    jointList = list()
    for i in range(jointCount):  # create a joints with unique names
        padCurNumber = str(format(i + 1, '02d'))
        jointName = '{}{}_jnt_{}'.format(suffixName, jntName, padCurNumber)
        jointName = namehandling.nonUniqueNameNumber(
            jointName)  # checks name is unique returns appropriate new name if needed
        if i:  # everything but first count
            jointList.append(cmds.joint(name=jointName, position=(jointSpacing, 0, 0), relative=True))
        else:  # first count
            jointList.append(cmds.joint(name=jointName, position=(0, 0, 0), relative=True))
    return jointList


def buildJointTwoPoints(startPosition, endPosition, jointCount=10, worldUpVector=[0, 1, 0], suffixName="",
                        jntName="jointStraight"):
    """Builds the spine joints in a straight line, given two positions as start and end as [x,y,z]
    returns the joint list as names

    :param startPostition:
    :type startPostition:
    :param endPosition:
    :type endPosition:
    :param jointSpacing: Distance in X between each joint
    :type jointSpacing: float
    :param worldUpVector:
    :type worldUpVector:
    :return jointList: List of joint names, long fullpath names
    :rtype jointList: list
    """
    selobjs = cmds.ls(selection=True)  # only because cmds selects unwanted objects
    if suffixName:
        suffixName = "{}_".format(suffixName)
    jointSpacing = mayadag.straightLineSpacing(startPosition, endPosition, jointCount)  # get joint spacing
    # build joints
    jointList = buildJointStraight(jntName=jntName, suffixName=suffixName, jointCount=jointCount,
                                   jointSpacing=jointSpacing)
    # get direction to aim joints and apply
    posRotRoo = mayadag.getAimTwoPositions(startPosition, endPosition, worldUpVector)
    moveorient.setPosRotRoo(jointList[0], posRotRoo)
    cmds.select(selobjs, replace=True)  # back to original selection because cmds selects unwanted objects
    return jointList, jointSpacing


def buildCubesOnJoints(jointList):
    cubeList = mesh.createPrimitiveFromList(jointList, type="cube", message=False, scale=1.0)
    return cubeList
