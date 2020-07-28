from maya import cmds
from maya import OpenMaya as om

from zoo.libs.maya.api import nodes

def castToMObjects(items):
    """A reasonably efficient way to map a list of nodes to mobjects

    Should be in a library,possibly this code exists elsewhere and in om2 instead of om1

    Original Author: Hamish McKenzie

    :param items: a list of Maya nodes
    :type items: list(str)
    :return newItems: list of nodes now as mObjects?
    :rtype newItems: list(mObjects)
    """
    # TODO: upgrade to om2
    sel = om.MSelectionList()
    newItems = []
    for n, item in enumerate(items):
        sel.add(item)
        mobject = om.MObject()
        try:
            sel.getDependNode(n, mobject)
        # this can happen if a node appears twice in items...  sel.add doesn't actually add anything because
        # the node is already in the selection list
        except RuntimeError:
            continue
        newItems.append(mobject)
    return newItems


def resetNodes(nodes, skipVisibility=True):
    """Resets all keyable attributes on given objects to their default values
    Great for running on a large selection such as all character controls.

    :param nodes: a list of Maya transform nodes
    :type nodes: list
    :param skipVisibility: don't reset the visibility attribute
    :type skipVisibility: bool
    """
    selAttrs = cmds.channelBox('mainChannelBox', q=True, sma=True) or cmds.channelBox('mainChannelBox', q=True,
                                                                                      sha=True)
    for node in nodes:
        attrs = cmds.listAttr(node, keyable=True)
        for attr in attrs:
            if skipVisibility and attr == 'visibility':
                continue
            # if there are selected attributes AND the current attribute isn't in the list of selected attributes, skip
            if selAttrs is not None and attr.shortName() not in selAttrs:
                continue
            default = 0
            try:
                default = cmds.attributeQuery(attr, n=node, listDefault=True)[0]
            except RuntimeError:
                pass
            attrpath = ".".join([node, attr])
            if not cmds.getAttr(attrpath, settable=True):
                continue
            # need to catch because maya will let the default value lie outside an attribute's
            # valid range (ie maya will let you create an attrib with a default of 0, min 5, max 10)
            try:
                cmds.setAttr(attrpath, default, clamp=True)
            except RuntimeError:
                pass


def resetNode(node, skipVisibility=True):
    """Resets all keyable attributes on a single Maya object to it's default value
    Great for running on a large selection such as all character controls.

    Original Author: Hamish McKenzie

    :param skipVisibility: don't reset the visibility attribute
    :type skipVisibility: bool
    """
    return resetNodes([node], skipVisibility=skipVisibility)


def resetSelection(skipVisibility=True):
    """Resets all keyable attributes on a selection of object to their default value
    Great for running on a large selection such as all character controls.

    Original Author: Hamish McKenzie

    :param skipVisibility: don't reset the visibility attribute
    :type skipVisibility: bool
    """
    resetNodes(cmds.ls(sl=True, type="transform"), skipVisibility=skipVisibility)
