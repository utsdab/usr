from maya import cmds
from maya.api import OpenMaya as om2

from tests import mayatestutils
from zoo.libs.maya.api import scene
from zoo.libs.maya.api import nodes


class TestScene(mayatestutils.BaseMayaTest):
    def setUp(self):
        self.node = cmds.createNode("transform")

    def test_getSelected(self):
        cmds.select([self.node, cmds.createNode("transform")])
        selected = scene.getSelectedNodes()
        self.assertEquals(len(selected), 2)
        self.assertTrue(all(isinstance(i, om2.MObject) for i in selected))

    def test_removeFromActiveSelection(self):
        cmds.select([self.node, cmds.createNode("transform")])
        selected = scene.getSelectedNodes()
        self.assertEquals(len(selected), 2)
        scene.removeFromActiveSelection(nodes.asMObject(self.node))
        selected = scene.getSelectedNodes()
        self.assertEquals(len(selected), 1)

    def test_getNodesCreatedBy(self):
        def testCreate():

            return nodes.asMObject(cmds.createNode("transform")), nodes.createDagNode("test", "transform")

        results = scene.getNodesCreatedBy(testCreate)

        self.assertEquals(len(results), 2)
        for i in results:
            for n in i:
                self.assertIsInstance(n, om2.MObject)
