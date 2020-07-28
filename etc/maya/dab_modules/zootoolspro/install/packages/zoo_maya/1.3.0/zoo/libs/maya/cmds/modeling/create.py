import maya.cmds as cmds
import maya.api.OpenMaya as om2

from zoo.libs.maya.cmds.objutils import matching

def createPrimitiveAndMatch(cube=False, sphere=False, cylinder=False, plane=False):
    """Creates an object and matches it to the currently selected object.
    Only creates one object at a time
    To Do:  Could add a snap to center "component selection" too

    :param cube: If True will build a cube
    :type cube: bool
    :param sphere: If True will build a sphere
    :type sphere: bool
    :param cylinder: If True will build a cylinder
    :type cylinder: bool
    :param plane: If True will build a plane
    :type plane: bool
    :return newObj: The name of the new object created
    :rtype: str
    """
    selectedObjList = cmds.ls(sl=1, l=1)
    if cube:
        newObj = (cmds.polyCube())[0]
    elif sphere:
        newObj = (cmds.polySphere(subdivisionsAxis=12, subdivisionsHeight=8))[0]
    elif cylinder:
        newObj = (cmds.polyCylinder(subdivisionsAxis=12))[0]
    elif plane:
        newObj = (cmds.polyPlane(subdivisionsHeight=1, subdivisionsWidth=1))[0]
    else:
        om2.MGlobal.displayWarning("Invalid parameters given in code, no objects given")
        return
    if selectedObjList:
        firstSelObj = selectedObjList[0]
        matching.matchZooAlSimpErrConstrain(firstSelObj, newObj)  # match
        om2.MGlobal.displayInfo("`{}` created and matched to `{}`".format(newObj, firstSelObj.split("|")[-1]))
    else:
        om2.MGlobal.displayInfo("Created `{}`".format(newObj))
    return newObj