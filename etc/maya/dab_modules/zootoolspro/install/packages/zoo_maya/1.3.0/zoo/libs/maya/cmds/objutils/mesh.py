import maya.cmds as cmds
import maya.api.OpenMaya as om2

from zoo.libs.maya.cmds.objutils import matching


def createPrimitiveMatch(matchObj=None, type="cube", message=True, scale=1.0):
    """Creates an primitive and tries to match it to the object given.
    If matchObj is None then defaults to world center.

    :param matchObj: the object to match to, if None will be world center
    :type matchObj: str
    :param type: the type of primitive to build "cube", "sphere", "cylinder", "plane"
    :type type: str
    :param message: output the result to Maya?
    :type message: bool
    :param scale: How big is the primitive object
    :type scale: float
    :return newObj: The newly created primitive
    :rtype: str
    """
    if type == "cube":
        newObj = (cmds.polyCube(height=scale, width=scale))[0]
    elif type == "sphere":
        newObj = (cmds.polySphere(subdivisionsAxis=12, subdivisionsHeight=8, radius=0.5*scale))[0]
    elif type == "cylinder":
        newObj = (cmds.polyCylinder(subdivisionsAxis=12, height=scale, radius=0.5*scale))[0]
    elif type =="plane":
        newObj = (cmds.polyPlane(subdivisionsHeight=1, subdivisionsWidth=1, height=scale, width=scale))[0]
    else:
        om2.MGlobal.displayWarning("Invalid parameters given, no objects found")
        return
    if matchObj:
        matching.matchZooAlSimpErrConstrain(newObj, matchObj)
        if message:
            om2.MGlobal.displayInfo("`{}` created and matched to `{}`".format(newObj, matchObj.split("|")[-1]))
    else:
        om2.MGlobal.displayInfo("Created `{}`".format(newObj))
    return newObj


def createPrimitiveSelected(type="cube", message=True, scale=1.0):
    """Creates an primitive and tries to match it to the first selected object if one is selected.
    Otherwise defaults to world center.

    :param type: the type of primitive to build "cube", "sphere", "cylinder", "plane"
    :type type: str
    :param message: output the result to Maya?
    :type message: bool
    :param scale: How big is the primitive object
    :type scale: float
    :return newObj: The newly created primitive
    :rtype: str
    """
    selectedObjs = cmds.ls(sl=1, l=1)
    if selectedObjs:
        newObj = createPrimitiveMatch(matchObj=selectedObjs[0], type=type, message=message, scale=scale)
    else:
        newObj = createPrimitiveMatch(matchObj=None, type=type, message=message, scale=scale)
    return newObj


def createPrimitiveFromList(matchObjList, type="cube", message=False, scale=1.0, parent=True, matchNames=True):
    """Creates new primitive objects from a list of existing objects.
    Matches the position and rotation, possibly scale

    :param matchObjList: list of objects to create new primitives at that location
    :type matchObjList: list
    :param type: the type of primitive to build "cube", "sphere", "cylinder", "plane"
    :type type: str
    :param message: output the result to Maya?
    :type message: bool
    :param scale: How big is the primitive object
    :type scale: float
    :return newObjList: The newly created primitives
    :rtype newObjList: list
    """
    newObjList = list()
    for obj in matchObjList:
        newObj = createPrimitiveMatch(matchObj=obj, type=type, message=message, scale=scale)
        newObjList.append(newObj)
        if matchNames:
            newObj = cmds.rename("_".join([type, obj]))
        if parent:
            cmds.parent(newObj, obj)
    return newObjList