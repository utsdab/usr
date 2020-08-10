import maya.cmds as cmds

from zoo.libs.maya.cmds.objutils import alignutils


def parentGroupControls(controlList, groupList, reverse=False, long=False):
    """Parents controls with groups into a simple hierarchy, zeroing the controls, can be reversed in order

    :param controlList: list of the controls
    :param groupList: list of groups of the controls
    :param reverse: boolean, whether to backwards reverse the parent hierarchy
    :return:
    """
    if reverse:
        controlList = list(reversed(controlList))
        groupList = list(reversed(groupList))
    for i, control in enumerate(controlList):
        if i:
            groupList[i] = (cmds.parent(groupList[i], controlList[i - 1]))[0]
            controlList[i] = (cmds.listRelatives(groupList[i], children=True, type="transform", fullPath=long))[0]
    if long:
        controlList = cmds.ls(controlList, long=True)
        groupList = cmds.ls(groupList, long=True)
    return controlList, groupList

