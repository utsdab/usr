from zoo.libs.maya.markingmenu import menu, utils
from zoo.libs.maya.api import nodes, scene
from maya import cmds
from maya.api import OpenMaya as om2
from zoo.libs.utils import zlogging


logger = zlogging.getLogger(__name__)


def validateAndBuild(parentMenu, nodeName):
    if cmds.objExists(nodeName):
        triggerNode = nodes.asMObject(nodeName)
    else:
        # ::note should we just check for selection here and validate?
        return 0
    if not utils.hasTrigger(triggerNode):
        return 0
    triggerNodes = [triggerNode] + [i for i in scene.getSelectedNodes() if i != triggerNode]

    visited = []
    validLayout = None
    dynamic = False
    # gather the trigger information from the current node and the selection
    for st in triggerNodes:
        # get the compound trigger plug
        triggerPlugs = utils.triggerPlugsFromNode(st)
        # for each compound found, consolidate and gather info
        for tp in triggerPlugs:
            node = tp.node()
            if node in visited:
                continue
            visited.append(node)
            # pull the command type and command string from the compoundplug
            commandType = tp.child(0).asInt()
            commandStr = tp.child(1).asString()
            if commandType == utils.LAYOUT_TYPE:
                layout = menu.findLayout(commandStr)
                if not layout:
                    continue
                if validLayout:
                    validLayout.merge(layout)
                else:
                    validLayout = layout
            elif commandType == utils.DYNAMIC_TYPE:
                dynamic = True
                break
    if not dynamic:
        if validLayout is None:
            return 0
        validLayout.solve()

        mainMenu = menu.MarkingMenu(validLayout, "zooTriggerMenu", parentMenu, menu.Registry())
        mainMenu.attach(**{"nodes": map(om2.MObjectHandle, triggerNodes)})
    else:
        menu.MarkingMenu.buildDynamicMenu(commandStr, parent=parentMenu,
                                          arguments={"nodes": map(om2.MObjectHandle, triggerNodes)})
    return 1
