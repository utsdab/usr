from zoo.libs.command import command
from zoo.libs.maya.api import scene
from zoo.libs.maya.api import nodes
from maya.api import OpenMaya as om2


class AlignSelectedCommand(command.ZooCommand):
    """This command Creates a meta node from the registry.
    """
    id = "zoo.maya.alignSelected"
    creator = "David Sparrow"
    isUndoable = True
    uiData = {"icon": "",
              "tooltip": "Align rotation of two objects",
              "label": "Align selected nodes",
              "color": "",
              "backgroundColor": ""
              }
    transformations = None

    def resolveArguments(self, arguments):
        selected = scene.getSelectedNodes()
        if len(selected) < 2:
            self.cancel("Please Select more than 2 nodes")
        target = om2.MObjectHandle(selected[-1])  # driver
        driven = [om2.MObjectHandle(i) for i in selected[:-1]]  # driven
        data = [None] * len(driven)
        for i, nod in enumerate(iter(driven)):
            data[i] = (nod, nodes.getRotation(nod.object(), om2.MSpace.kTransform))
        self.transformations = data
        arguments["target"] = target
        arguments["driven"] = driven
        return arguments

    def doIt(self, target=None, driven=None, aimVector=om2.MVector(1.0,0.0,0.0), upVector=om2.MVector(0.0, 1.0, 0.0)):
        """Create the meta node based on the type parameter, if the type isn't specified then the baseMeta class will
        be used instead

        """
        scene.aimNodes(targetNode=target.object(), driven=[i.object() for i in driven], aimVector=aimVector, upVector=upVector)
        return True

    def undoIt(self):
        if not self.transformations:
            return False
        for node, rotation in iter(self.transformations):
            children = []
            node = node.object()
            for child in list(nodes.iterChildren(node, False, (om2.MFn.kTransform, om2.MFn.kJoint))):
                nodes.setParent(child, None, True)
                children.append(child)
            nodes.setRotation(node, rotation)

            for child in iter(children):
                nodes.setParent(child, node, True)
