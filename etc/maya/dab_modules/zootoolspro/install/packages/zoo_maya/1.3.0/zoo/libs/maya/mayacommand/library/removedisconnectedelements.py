from zoo.libs.command import command
from zoo.libs.maya.api import plugs
from maya.api import OpenMaya as om2


class RemoveDisconnectElements(command.ZooCommand):
    """This command Removes all disconnected elements from the MPlug array
    """
    id = "zoo.maya.removeDisconnectedElements"
    creator = "David Sparrow"
    isUndoable = True
    uiData = {"icon": "",
              "tooltip": __doc__,
              "label": "Consolidate Plug Elements ",
              "color": "",
              "backgroundColor": ""
              }
    _modifier = None

    def resolveArguments(self, arguments):
        plug = arguments.get("plug")

        if plug is None:
            self.cancel("No Plug specified")
        if not isinstance(plug, om2.MPlug):
            self.cancel("Specified Plug is not MPlyg Type")
        elif not plug.array:
            self.cancel("Specified plug is not an array {}".format(plug.name()))
        return arguments

    def doIt(self, plug=None, disconnect=False):
        """Create the meta node based on the type parameter, if the type isn't specified then the baseMeta class will
        be used instead


        """
        try:
            self._modifier = plugs.removeUnConnectedEmptyElements(plug, disconnect)
        except RuntimeError:
            return False
        return True

    def undoIt(self):
        if self._modifier is not None:
            self._modifier.doIt()
        return False

