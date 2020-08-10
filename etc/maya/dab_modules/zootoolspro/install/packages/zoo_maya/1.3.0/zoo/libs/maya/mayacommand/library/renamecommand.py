from zoo.libs.command import command

from maya.api import OpenMaya as om2


class ZooRenameCommand(command.ZooCommand):
    """This command batch renames maya nodes, expects om2.MObjects
    """
    id = "zoo.nodes.rename"
    creator = "David Sparrow"
    isUndoable = True
    uiData = {"icon": "cube",
              "tooltip": "Batch renames nodes",
              "label": "Rename",
              "color": "",
              "backgroundColor": ""
              }
    _modifier = None

    def resolveArguments(self, arguments):
        nodes = arguments.get("nodes")
        if not nodes:
            self.cancel("Please provide at least one node!")
        valid = []
        for n, newName in iter(nodes):
            handle = om2.MObjectHandle(n)
            if not handle.isAlive() or not handle.isValid():
                continue
            if n.hasFn(om2.MFn.kDagNode):
                fn = om2.MFnDagNode(n)
                name = fn.fullPathName().split("|")[-1].split(":")[-1]
            else:
                fn = om2.MFnDependencyNode(n)
                name = fn.name()
            if newName == name:
                continue
            valid.append((handle, newName))
        if not valid:
            self.cancel("No valid node to rename, either the nodes don't exist or the names are the same")
        return {"nodes": tuple(valid)}

    def doIt(self, nodes=None):
        modifier = om2.MDGModifier()
        for n, name in iter(nodes):
            modifier.renameNode(n.object(), name)
        modifier.doIt()
        self._modifier = modifier
        return nodes

    def undoIt(self):
        if self._modifier is not None:
            self._modifier.undoIt()
            return True
        return False