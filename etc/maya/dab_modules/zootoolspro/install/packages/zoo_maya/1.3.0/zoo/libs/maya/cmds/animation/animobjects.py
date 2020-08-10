import maya.cmds as cmds
import maya.api.OpenMaya as om2

from zoo.libs.maya.cmds.objutils import objhandling


def filterAnimatedNodes(nodeList):
    """Filters a list returning a new list of nodes that have keyframes

    :param nodeList: Incoming list of nodes
    :type list:
    :return animNodeList: The filtered list
    :type list:
    """
    animNodeList = []
    for n in nodeList:
        if cmds.keyframe(n, query=True, keyframeCount=True, time=(-100000, 10000000)):
            animNodeList.append(n)
    return animNodeList


def getAnimatedNodes(selectFlag="all", select="True", message="True"):
    """Selects nodes animated with keyframes.  Flag allows for three select options:

        1. "all" : All in scene
        2. "selected" : only selected
        3. "hierarchy" : search selected hierarchy

    :param selectFlag: "all", "selected", "hierarchy".  All in scene, only selected and search selected hierarchy
    :type selectFlag: str
    :param select: If True will select the objects
    :type select: bool
    :param message: if True will report a message
    :type message: bool
    :return animNodeList: The list of animated nodes
    :type animNodeList: list
    """
    nodeList, selectionWarning = objhandling.returnSelectLists(selectFlag=selectFlag)
    animNodeList = []
    if nodeList:
        animNodeList = filterAnimatedNodes(nodeList)
        if select:
            cmds.select(animNodeList, r=True)
    if message:
        if animNodeList:
            om2.MGlobal.displayInfo('Success: Animated nodes: %s' % animNodeList)
        else:
            if selectionWarning:
                om2.MGlobal.displayWarning('Please select object/s')
            else:
                om2.MGlobal.displayWarning('No animated nodes found')
    return animNodeList
