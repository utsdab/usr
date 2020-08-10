from zoo.libs.command import command
from zoo.libs.maya.meta import base

from maya.api import OpenMaya as om2


class CreateMetaCommand(command.ZooCommand):
    """This command Creates a meta node from the registry.
    """
    id = "zoo.meta.create"
    creator = "David Sparrow"
    isUndoable = True
    uiData = {"icon": "",
              "tooltip": "Create meta node",
              "label": "Create meta Node",
              "color": "",
              "backgroundColor": ""
              }
    _meta = None

    def resolveArguments(self, arguments):
        node = arguments.get("node")
        Type = arguments.get("type")
        registry = base.MetaRegistry()
        matchedType = registry.types.get(Type)
        if matchedType is None:
            Type = base.MetaBase
        # we need to store the node as mobjecthandle this the arguments get store for the life time of the command
        # instance
        if node is not None:
            node = om2.MObjectHandle(node)
            arguments["node"] = node
        arguments["type_"] = Type
        return arguments

    def doIt(self, node=None, name=None, type_=None, initDefaults=True):
        """Create the meta node based on the type parameter, if the type isn't specified then the baseMeta class will
        be used instead

        :param node: The node to convert to the meta class(optional)
        :type node: MObject
        :param name: The new name for the create meta node(optional)
        :type name: str
        :param type_: The meta node class name, if not specified then the base meta class is used. This is converted \
        to the class instance during command.resolvearguments method operation.
        :type type_: str
        :param initDefaults: If true then the standard meta attributes are added
        :type initDefaults: bool
        :return: Returns the class instance of the meta class thats created
        :rtype: base.MetaBase
        """
        if node:
            node = node.object()
        self._meta = type_(node=node, name=name, initDefaults=initDefaults)
        return self._meta

    def undoIt(self):
        if self._meta is not None and self._meta.exists():
            self._meta.delete()
            return True
        return False
