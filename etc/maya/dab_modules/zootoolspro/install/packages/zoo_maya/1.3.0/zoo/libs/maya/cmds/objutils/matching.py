import maya.cmds as cmds
import maya.api.OpenMaya as om2

from zoo.libs.maya.cmds.objutils import namehandling, filtertypes, attributes


def matchZooAlSimpErrConstrain(obj, matchObj):
    """Tries the 2017 new match function, if it fails do the old 2017 constraint version
    cmds.delete(cmds.parentConstraint(obj, matchObj))

    :param obj: the Maya object to match to
    :type obj: str
    :param matchObj: the Maya object to match
    :type matchObj: str
    """
    try:  # 2017 and above Match
        cmds.matchTransform(([matchObj, obj]), pos=1, rot=1, scl=0, piv=0)
        return
    except:  # will fail if not 2017+ and use old style constrain match
        cmds.delete(cmds.parentConstraint(obj, matchObj))


def groupZeroObj(objName, freezeScale=True, removeSuffixName=""):
    """Groups the selected object, matching the group to the object and zero's the obj.  objName can be long name.

    Will freeze scale by default, the group will not be scaled

    :param objName: The name of the control, can be a long name
    :type objName: str
    :param freezeScale: Freeze the scale of the objName?
    :type freezeScale: bool
    :param removeSuffixName: Don't include this suffix on the group if in the objName, don't include the underscore
    :type removeSuffixName: str
    :return objName: The name of the original object, if fullname the name will have changed, will be unique
    :rtype objName: str
    :return grpName:  The name of the new group, will be a unique name
    :rtype grpName: str
    """
    pureName = namehandling.mayaNamePartTypes(objName)[2]
    pureName = namehandling.stripSuffixExact(pureName, removeSuffixName)  # remove suffix if it exists
    grpName = "_".join([pureName, filtertypes.GROUP_SX])
    grpName = cmds.group(name=grpName, em=True)
    cmds.matchTransform([grpName, objName], pos=1, rot=1, scl=0, piv=0)
    objParent = cmds.listRelatives(objName, parent=True, fullPath=True)
    if objParent:  # then parent to the control's parent, and reset scale
        grpName = cmds.parent(grpName, objParent)[0]
        attributes.resetTransformAttributes(grpName, translate=False, rotate=False, scale=True, visibility=False)
    objName = cmds.parent(objName, grpName)[0]
    if freezeScale:
        if cmds.getAttr(".".join([objName, "scale"]))[0] != (1, 1, 1):  # if scale not 1, 1, 1
            cmds.makeIdentity(objName, apply=True, translate=False, rotate=False, scale=True)  # freeze transform scale
    return objName, grpName


def groupZeroObjList(objList, freezeScale=True, removeSuffixName=""):
    """Groups an object list, matching a new group to each object and zero's the obj.  objNames can be long names.

    Will freeze scale by default, the groups will not be scaled

    :param objList: The names of the controls, can be a long names
    :type objList: list(str)
    :param freezeScale: Freeze the scale of the objName?
    :type freezeScale: bool
    :param removeSuffixName: Don't include this suffix on the group if in the objName, don't include the underscore
    :type removeSuffixName: str
    :return updatedObjList: The names of the original objects, if fullnames the names will have changed, will be unique
    :rtype updatedObjList: list(str)
    :return grpList:  The names of the new groups, will be unique names
    :rtype grpList: list(str)
    """
    updatedObjList = list()
    grpList = list()
    for obj in objList:
        obj, grp = groupZeroObj(obj, freezeScale=freezeScale, removeSuffixName=removeSuffixName)
        updatedObjList.append(obj)
        grpList.append(grp)
    return updatedObjList, grpList


def groupZeroObjSelection(freezeScale=True, message=True, removeSuffixName=""):
    """Groups selected objs, matching a new group to each object and zero's the obj.  objNames can be long names.

    Will freeze scale by default, the groups will not be scaled

    :param objList: The names of the controls, can be a long names
    :type objList: list(str)
    :param freezeScale: Freeze the scale of the objName?
    :type freezeScale: bool
    :param removeSuffixName: Don't include this suffix on the group if in the objName, don't include the underscore
    :type removeSuffixName: str
    :param message: Return a message to the user
    :type message: bool
    :return updatedObjList: The names of the original objects, if fullnames the names will have changed, will be unique
    :rtype updatedObjList: list(str)
    :return grpList:  The names of the new groups, will be unique names
    :rtype grpList: list(str)
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        if message:
            om2.MGlobal.displayWarning("Please select an object/s to group")
        return list(), list()
    return groupZeroObjList(selObjs, freezeScale=freezeScale, removeSuffixName=removeSuffixName)

