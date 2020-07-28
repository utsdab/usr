from maya import cmds
import maya.api.OpenMaya as om2
import maya.mel as mel


def matchPivotParent(obj):
    """Matches the pivot to the objects parent if it has one, if not match to world center

    :param obj: a Maya transform node
    :type obj: str
    """
    parentList = cmds.listRelatives(obj, parent=True)
    if not parentList:
        centerPivotWorld(obj)
        return
    parent = parentList[0]
    cmds.matchTransform([obj, parent], pos=False, rot=False, scl=False, piv=True)


def matchPivotParentList(objList):
    """Matches the pivot to each object's parent if it has one, if not match to world center

    :param objList: A list of Maya transforms
    :type objList: list(str)
    """
    for obj in objList:
        matchPivotParent(obj)


def matchPivotParentSel(message=True):
    """Matches the selected object's pivot to each object's parent if it has one, if not match to world center
    """
    objList = cmds.ls(selection=True)
    if not objList:
        if message:
            om2.MGlobal.displayWarning("Please select an object")
        return
    # Check selection is a list of transform nodes.
    transformList = cmds.ls(objList, type="transform")
    if not transformList:
        if message:
            om2.MGlobal.displayWarning("Selected objects must be transform nodes, please select geo etc")
        return
    matchPivotParentList(transformList)
    om2.MGlobal.displayInfo("Success: Pivots matched to parents, {}".format(transformList))


def centerPivotSelected():
    """Maya's center pivot selected command"""
    mel.eval("xform - cpc")


def centerPivotWorld(obj):
    """Centers the pivot of an object (transform node) to the center of the world or parent zero position.

    :param obj: A single Maya object transform node name
    :type obj: str
    :param worldSpace: Center to the world, False will center to the parent space center
    :type worldSpace: bool
    """
    cmds.move(0, 0, 0,
              ["{}.scalePivot".format(obj),
               "{}.rotatePivot".format(obj)],
              absolute=True,
              worldSpace=True)


def centerPivotWorldList(objList):
    """Centers the pivot of each object (transform node) in a list to the center of the world or parent zero position.

    :param objList: A list of Maya objects, transform node names
    :type objList: str
    :param worldSpace: Center to the world, False will center to the parent space center
    :type worldSpace: bool
    """
    for obj in objList:
        centerPivotWorld(obj)


def centerPivotWorldSel(message=True):
    """Centers the pivot of each object (transform node) in a selection to center of the world or parent zero position.

    :param message: Report a message to the user?
    :type message: bool
    """
    objList = cmds.ls(selection=True)
    if not objList:
        if message:
            om2.MGlobal.displayWarning("Please select an object")
        return
    # Check selection is a list of transform nodes.
    transformList = cmds.ls(objList, type="transform")
    if not transformList:
        if message:
            om2.MGlobal.displayWarning("Selected objects must be transform nodes, please select geo etc")
        return
    centerPivotWorldList(transformList)
    if message:
        om2.MGlobal.displayInfo("Object pivots centered to world, `{}`".format(transformList))

