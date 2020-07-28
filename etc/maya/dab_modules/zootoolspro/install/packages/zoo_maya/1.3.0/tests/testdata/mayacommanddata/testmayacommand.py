from zoo.libs.command import command

from zoo.libs.maya.api import nodes
from maya.api import OpenMaya as om2


class MayaSimpleCommand(command.ZooCommand):
    id = "test.mayaSimpleCommand"
    creator = "David Sparrow"
    isUndoable = True
    _testNode = None

    def doIt(self):
        return "hello world"

    def undoIt(self):
        return "undo"


class MayaNotUndoableCommand(command.ZooCommand):
    id = "test.mayaNotUndoableCommand"
    creator = "David Sparrow"
    isUndoable = False
    _testNode = None

    def doIt(self):
        return "hello world"

    def undoIt(self):
        return "undo"


class MayaTestCreateNodeCommand(command.ZooCommand):
    id = "test.mayaTestCreateNodeCommand"
    creator = "David Sparrow"
    isUndoable = True
    _testNode = None

    def doIt(self):
        node = nodes.createDagNode("testNode", "transform")
        self._testNode = om2.MObjectHandle(node)
        return node

    def undoIt(self):
        if self._testNode is None:
            raise ValueError("failed to undo")
        mod = om2.MDagModifier()
        mod.deleteNode(self._testNode.object())
        mod.doIt()
        self._testNode = None


class MayaTestCommandFailsOnDoIt(command.ZooCommand):
    id = "test.mayaTestCommandFailsOnDoIt"
    creator = "David Sparrow"
    _testNode = None
    isUndoable = False

    def doIt(self):
        raise ValueError("Failed")


class MayaTestCommandFailsOnUndoIt(command.ZooCommand):
    id = "test.mayaTestCommandFailsOnUndoIt"
    creator = "David Sparrow"
    _testNode = None
    isUndoable = True

    def doIt(self):
        node = nodes.createDagNode("testNode", "transform")
        self._testNode = om2.MObjectHandle(node)

    def undoIt(self):
        raise ValueError("Failed")


class MayaTestCommandFailsOnResolveArgs(command.ZooCommand):
    id = "test.mayaTestCommandFailsOnResolveArgs"
    creator = "David Sparrow"
    _testNode = None

    def doIt(self, test, test2=None):
        pass
