from maya import cmds
from maya.api import OpenMaya as om

from tests import mayatestutils
from zoo.libs.maya.api import nodes
from maya.api import OpenMaya as om2


class TestNodes(mayatestutils.BaseMayaTest):
    application = "maya"

    def setUp(self):
        self.node = cmds.createNode("transform")

    def test_isValidMDagPath(self):
        obj = om.MFnDagNode(nodes.asMObject(self.node)).getPath()
        self.assertTrue(nodes.isValidMDagPath(obj))

    def test_toApiObjectReturnsDagNode(self):
        obj = nodes.toApiMFnSet(self.node)
        self.assertIsInstance(obj, om.MFnDagNode)

    def test_toApiObjectReturnsDependNode(self):
        node = cmds.createNode("multiplyDivide")
        self.assertIsInstance(nodes.toApiMFnSet(node), om.MFnDependencyNode)

    def test_asMObject(self):
        self.assertIsInstance(nodes.asMObject(self.node), om.MObject)

    def test_hasParent(self):
        obj = nodes.asMObject(self.node)
        self.assertFalse(nodes.hasParent(obj))
        transform = cmds.createNode("transform")
        nodes.setParent(obj, nodes.asMObject(transform))
        self.assertTrue(nodes.hasParent(obj))

    def test_setParent(self):
        obj = nodes.asMObject(self.node)
        self.assertFalse(nodes.hasParent(obj))
        transform = nodes.asMObject(cmds.createNode("transform"))
        nodes.setParent(transform, obj)
        self.assertTrue(nodes.hasParent(transform))

    def test_getParent(self):
        obj = nodes.asMObject(self.node)
        self.assertFalse(nodes.hasParent(obj))
        transform = nodes.asMObject(cmds.createNode("transform"))
        nodes.setParent(transform, obj)
        parent = nodes.getParent(transform)
        self.assertEquals(parent, obj)

    def test_getChildren(self):
        parent = nodes.asMObject(cmds.group(self.node))
        children = nodes.getChildren(parent)
        self.assertEquals(len(children), 1)
        self.assertIsInstance(children[0], om.MObject)
        secondChild = nodes.asMObject(cmds.createNode("transform"))
        nodes.setParent(secondChild, parent)
        children = nodes.getChildren(parent)

        self.assertEquals(len(children), 2)
        thirdChild = nodes.asMObject(cmds.createNode("transform"))
        nodes.setParent(thirdChild, parent)
        children = nodes.getChildren(parent, recursive=True)
        self.assertEquals(len(children), 3)

    def test_iterParent(self):
        cmds.group(self.node)
        cmds.group(self.node)
        cmds.group(self.node)
        parents = [i for i in nodes.iterParents(nodes.asMObject(self.node))]
        self.assertEquals(len(parents), 3)

    def test_childPathAtIndex(self):
        nodeParent = nodes.asMObject(cmds.group(self.node))
        child1 = nodes.asMObject(cmds.createNode("transform"))
        nodes.setParent(child1, nodeParent)
        dagPath = om.MFnDagNode(nodeParent).getPath()
        self.assertEquals(nodes.childPathAtIndex(dagPath, 0).partialPathName(), self.node)

    def test_childPaths(self):
        nodeParent = nodes.asMObject(cmds.group(self.node))
        child1 = nodes.asMObject(cmds.createNode("transform"))
        nodes.setParent(child1, nodeParent)
        dagPath = om.MFnDagNode(nodeParent).getPath()
        self.assertEquals(len(nodes.childPaths(dagPath)), 2)
        self.assertTrue(all(isinstance(i, om.MDagPath) for i in nodes.childPaths(dagPath)))

    def test_childPathsByFn(self):
        nodeParent = nodes.asMObject(cmds.polyCube(ch=False)[0])
        nodes.setParent(nodes.asMObject(self.node), nodeParent)

        child1 = nodes.asMObject(cmds.createNode("transform"))
        child2 = nodes.asMObject(cmds.createNode("transform"))
        nodes.setParent(child1, nodeParent)
        nodes.setParent(child2, nodeParent)
        dagPath = om.MFnDagNode(nodeParent).getPath()
        results = nodes.childPathsByFn(dagPath, om2.MFn.kTransform)
        self.assertEquals(len(results), 3)
        results = nodes.childPathsByFn(dagPath, om2.MFn.kMesh)
        self.assertEquals(len(results), 1)

    def test_childTransforms(self):
        nodeParent = nodes.asMObject(cmds.group(self.node))
        child1 = nodes.asMObject(cmds.createNode("transform"))
        nodes.setParent(child1, nodeParent)
        dagPath = om.MFnDagNode(nodeParent).getPath()
        self.assertEquals(len(nodes.childTransforms(dagPath)), 2)
        self.assertTrue(all(isinstance(i, om.MDagPath) for i in nodes.childPaths(dagPath)))
        self.assertTrue(all(i.apiType() == om.MFn.kTransform for i in nodes.childPaths(dagPath)))

    def test_getShapes(self):
        node = nodes.asMObject(cmds.polyCube(ch=False)[0])
        self.assertEquals(len(nodes.shapes(om.MFnDagNode(node).getPath())), 1)
        self.assertIsInstance(nodes.shapes(om.MFnDagNode(node).getPath())[0], om.MDagPath)

    def test_nameFromMObject(self):
        self.assertEquals(nodes.nameFromMObject(nodes.asMObject(self.node), partialName=False), "|transform1")
        self.assertEquals(nodes.nameFromMObject(nodes.asMObject(self.node), partialName=True), "transform1")

    def test_parentPath(self):
        group = nodes.toApiMFnSet(cmds.createNode("transform"))
        self.assertIsNone(nodes.parentPath(group.getPath()))
        cmds.group(nodes.nameFromMObject(group.object()))
        parent = nodes.parentPath(group.getPath())
        self.assertIsInstance(parent, om.MDagPath)
        self.assertEquals(parent.partialPathName(), "group1")

    def test_deleteNode(self):
        node = om2.MObjectHandle(nodes.createDagNode("testTransform", "transform"))

        self.assertTrue(node.isValid() and node.isAlive())
        nodes.delete(node.object())
        self.assertFalse(node.isValid() and node.isAlive())

    def test_getObjectMatrix(self):
        node = nodes.asMObject(self.node)
        matrix = nodes.getMatrix(node)
        self.assertIsInstance(matrix, om2.MMatrix)
        matPl = om2.MFnDagNode(node).findPlug("matrix", False)
        self.assertEquals(matrix, om2.MFnMatrixData(matPl.asMObject()).matrix())

    def test_getParentMatrix(self):
        node = nodes.asMObject(self.node)
        matrix = nodes.getParentMatrix(node)
        self.assertIsInstance(matrix, om2.MMatrix)
        parentPlug = om2.MFnDagNode(node).findPlug("parentMatrix", False)
        parentPlug.evaluateNumElements()
        matPl = parentPlug.elementByPhysicalIndex(0)
        self.assertEquals(matrix, om2.MFnMatrixData(matPl.asMObject()).matrix())

    def test_getParentInverseMatrix(self):
        node = nodes.asMObject(self.node)
        matrix = nodes.getParentInverseMatrix(node)
        self.assertIsInstance(matrix, om2.MMatrix)
        parentPlug = om2.MFnDagNode(node).findPlug("parentInverseMatrix", False)
        parentPlug.evaluateNumElements()
        matPl = parentPlug.elementByPhysicalIndex(0)
        self.assertEquals(matrix, om2.MFnMatrixData(matPl.asMObject()).matrix())

    def test_getWorldMatrix(self):
        node = nodes.asMObject(self.node)
        matrix = nodes.getWorldMatrix(node)
        self.assertIsInstance(matrix, om2.MMatrix)
        parentPlug = om2.MFnDagNode(node).findPlug("worldMatrix", False)
        parentPlug.evaluateNumElements()
        matPl = parentPlug.elementByPhysicalIndex(0)
        self.assertEquals(matrix, om2.MFnMatrixData(matPl.asMObject()).matrix())

    def test_getWorldInverseMatrix(self):
        node = nodes.asMObject(self.node)
        matrix = nodes.getWorldInverseMatrix(node)
        self.assertIsInstance(matrix, om2.MMatrix)
        parentPlug = om2.MFnDagNode(node).findPlug("worldInverseMatrix", False)
        parentPlug.evaluateNumElements()
        matPl = parentPlug.elementByPhysicalIndex(0)
        self.assertEquals(matrix, om2.MFnMatrixData(matPl.asMObject()).matrix())

    def test_getTranslation(self):
        node = nodes.asMObject(self.node)
        om2.MFnTransform(node).setTranslation(om2.MVector(10, 10, 10), om2.MSpace.kObject)
        translation = nodes.getTranslation(node, om2.MSpace.kObject)
        self.assertIsInstance(translation, om2.MVector)
        self.assertEquals(translation, om2.MVector(10, 10, 10))

    def test_setTranslation(self):
        node = nodes.asMObject(self.node)
        nodes.setTranslation(node, om2.MVector(0, 10, 0))
        self.assertEquals(nodes.getTranslation(node, space=om2.MSpace.kObject), om2.MVector(0, 10, 0))

    def test_iterAttributes(self):
        node = nodes.asMObject(self.node)
        for i in nodes.iterAttributes(node):
            self.assertIsInstance(i, om2.MPlug)
            self.assertFalse(i.isNull)

    def test_createDagNode(self):
        node = nodes.createDagNode("new", "transform")
        self.assertIsInstance(node, om2.MObject)

    def test_createDGNode(self):
        node = nodes.createDGNode("new", "network")
        self.assertIsInstance(node, om2.MObject)
