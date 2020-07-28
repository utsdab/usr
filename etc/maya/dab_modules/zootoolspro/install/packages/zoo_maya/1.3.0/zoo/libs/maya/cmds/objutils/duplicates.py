import maya.cmds as cmds
import maya.api.OpenMaya as om2

from zoo.libs.maya.cmds.objutils import shapenodes


def duplicateWithoutChildrenList(nodeList):
    """Duplicates nodes without their children

    :param nodeList: a list of Maya node names
    :type nodeList: list(str)
    :return duplicateList: A list of the duplicated nodes/objects
    :rtype duplicateList: list(str)
    """
    duplicateList = list()
    for node in nodeList:
        duplicateList.append(shapenodes.duplicateWithoutChildren(node))
    return duplicateList


def duplicateWithoutChildrenSelected(message=True):
    """Duplicates selected nodes without their children

    :return duplicateList: A list of the duplicated nodes/objects
    :rtype duplicateList: list(str)
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        if message:
            om2.MGlobal.displayWarning("No objects selected, please select object/s.")
        return
    return duplicateWithoutChildrenList(selObjs)

