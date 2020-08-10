import maya.cmds as cmds
from maya import mel
from zoo.libs.maya.api import scene, nodes
from maya.api import OpenMaya as om2

INFO = 0
WARNING = 1
ERROR = 2


def inViewMessage(header, message, type_=INFO, fadeStayTime=1000):
    """Smaller wrapper function for nicely formatting maya inview message, INFO,WARNING,ERROR message types supported.
    Each message type will have a set color.

    :param header: The main header title for the message , ideally one word
    :type header: str
    :param message: The message to display
    :type message: str
    :param type_: gui.INFO,gui.WARNING, gui.ERROR
    :type type_: int
    :param fadeStayTime: the fade time
    :type fadeStayTime: int
    """
    useInViewMsg = cmds.optionVar(q='inViewMessageEnable')
    if not useInViewMsg:
        return
    if type_ == "info":
        msg = " <span style=\"color:#82C99A;\">{}:</span> {}"
        position = 'topCenter'
    elif type_ == "Warning":
        msg = "<span style=\"color:#F4FA58;\">{}:</span> {}"
        position = 'midCenterTop'
    elif type_ == "Error":
        msg = "<span style=\"color:#F05A5A;\">{}:</span> {}"
        position = 'midCenter'
    else:
        return
    cmds.inViewMessage(assistMessage=msg.format(header, message), fadeStayTime=fadeStayTime, dragKill=True,
                       position=position, fade=True)


def refreshContext():
    try:
        cmds.refresh(suppend=True)
        yield
    finally:
        cmds.refresh(suppend=False)


def selectedChannelboxAttributes():
    gChannelBoxName = mel.eval('$temp=$gChannelBoxName')
    attrs = cmds.channelBox(gChannelBoxName, query=True, selectedMainAttributes=True)
    selectedNodes = scene.getSelectedNodes()
    if not attrs:
        return list(), selectedNodes
    apiPlugs = []
    for node in selectedNodes:
        fn = om2.MFnDependencyNode(node)
        for a in attrs:
            # is there a a gurnettee that the node has the attribute?
            if fn.hasAttribute(a):
                p = fn.findPlug(a, False)
                apiPlugs.append(p)
    return apiPlugs, selectedNodes


def swapOutgoingConnectionsOnSelectedAttrs():
    selectedPlugs, selectedNodes = selectedChannelboxAttributes()
    if len(selectedNodes) != 2:
        raise ValueError("Must have no more than 2 nodes selected")
    return nodes.swapOutgoingConnections(selectedNodes[0], selectedNodes[1], selectedPlugs)

