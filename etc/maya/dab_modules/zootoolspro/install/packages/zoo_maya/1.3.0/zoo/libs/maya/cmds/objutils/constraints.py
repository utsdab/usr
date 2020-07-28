import maya.api.OpenMaya as om2
import maya.cmds as cmds


def deleteConstraintsFromObjList(objList, message=True):
    """Deletes any constraints attached to any object in an object list

    :param objList: list of maya objects or nodes
    :type objList: str
    :param message: report the message to the user?
    :type message: bool
    :return constrainList: the constraints deleted, will be empty list if none found
    :rtype constrainList: list(str)
    """
    constrainList = cmds.listConnections(objList, t="constraint")
    if not constrainList:
        om2.MGlobal.displayWarning("No constraints found attached to these objects")
        return list()
    cmds.delete(list(set(constrainList)))
    if message:
        om2.MGlobal.displayInfo("Success: Deleted constraints: {}".format(", ".join(constrainList)))
    return constrainList


def deleteConstraintsFromSelObj(message=True):
    """Deletes any constraints attached to any object from the current selection

    :param message: report the message to the user?
    :type message: bool
    :return constrainList: the constraints deleted, will be empty list if none found
    :rtype constrainList: list(str)
    """
    selObj = cmds.ls(selection=True)
    constrainList = deleteConstraintsFromObjList(selObj, message=message)
    return constrainList
