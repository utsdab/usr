from zoo.libs.command import command
from zoo.libs.maya.utils import gui
from zoo.libs.maya.api import nodes


class SwapConnectionsCommand(command.ZooCommand):
    """This command Creates a meta node from the registry.
    """
    id = "zoo.maya.connections.swap.all"
    creator = "David Sparrow"
    isUndoable = True
    uiData = {"icon": "transfer",
              "tooltip": "Swaps all connections between two selected nodes",
              "label": "Swap connections",
              "color": "",
              "backgroundColor": ""
              }
    _modifier = None

    def resolveArguments(self, arguments):
        plugs, sel = gui.selectedChannelboxAttributes()
        if len(sel) != 2:
            raise ValueError("Must have no more than 2 nodes selected")

        return {"source": sel[0], "target": sel[1], "plugs": plugs}

    def doIt(self, source=None, target=None, plugs=None):
        """Create the meta node based on the type parameter, if the type isn't specified then the baseMeta class will
        be used instead
        """
        self._modifier = nodes.swapOutgoingConnections(source, target, plugs)
        self._modifier.doIt()
        return True

    def undoIt(self):
        if self._modifier is not None:
            self._modifier.undoIt()