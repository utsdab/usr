from maya import cmds
from maya.api import OpenMaya as om2
from tests import mayatestutils
from zoo.libs.maya import zapi


class TestPlug(mayatestutils.BaseMayaTest):
    def setUp(self):
        self.base = zapi.createDag("testNode", "transform")

    def test_parent(self):
        parent = self.base.translateX.parent()
        self.assertIsNotNone(parent)
        self.assertIsInstance(parent, zapi.Plug)

    def test_apiType(self):
        self.base.apiType()

    def test_getOm2GetAttr(self):
        # test __getattr__
        plug = self.base.translate
        self.assertNotEqual(plug.name(), "")
        self.assertFalse(plug.isSource)
        # should fail with a standard python attributeError
        with self.assertRaises(AttributeError):
            plug.helloworld

    def test_standardTypeConversion(self):
        plug = self.base.translateX
        self.assertEquals(str(plug), self.base.name() + ".translateX")
        self.assertEquals(float(plug), 0.0)
        self.assertEquals(int(self.base.rotateOrder), 0.0)
        self.assertEquals(bool(self.base.visibility.get()), True)

    def test_cmdsNameCompatiblity(self):
        self.assertEquals(cmds.getAttr(str(self.base.translate)),
                          [(0.0, 0.0, 0.0)])

    def test_equality(self):
        node = zapi.createDag("testNode1", "transform")
        node.translate.set(om2.MVector(1.0, 0.0, 0.0))
        plug = self.base.translate
        self.assertEquals(plug, plug)
        self.assertNotEquals(plug, self.base.attribute("scale"))

        self.assertIsInstance(plug.plug(), om2.MPlug)
        self.assertIsInstance(plug.node(), zapi.DGNode)

    def test_Iterables(self):
        # test compound length
        n = zapi.nodeByName("lightLinker1")
        # quick test is ensure correctness
        self.assertTrue(n.link.isArray)
        self.assertTrue(n.link.isCompound)
        self.assertEquals(len(self.base.translate), self.base.translate.plug().numChildren())

        # test array length
        self.assertEquals(len(n.link), n.mfn().findPlug("link", False).evaluateNumElements())
        # test iterator
        for child in self.base.translate:
            self.assertIsInstance(child, zapi.Plug)

        for element in n.link:
            self.assertIsInstance(element, zapi.Plug)

            self.assertTrue(element.isElement)

        for child in self.base.translate.children():
            self.assertIsInstance(child, zapi.Plug)
        # indexing
        self.assertIsInstance(self.base.translate[0], zapi.Plug)
        self.base.translate.child(0)

    def test_connect(self):
        nodeB = zapi.createDag("testNode1", "transform")
        nodeB.translate.connect(self.base.translate)
        nodeB.attribute("scale") >> self.base.attribute("scale")
        self.assertEquals(self.base.attribute("scale").source(), nodeB.attribute("scale"))
        self.assertEquals(self.base.translate.source(), nodeB.translate)
        self.assertTrue(nodeB.translate.disconnect(self.base.translate))
        nodeB.attribute("scale") // self.base.attribute("scale")
        self.assertIsNone(self.base.attribute("scale").source(), nodeB.attribute("scale"))

        nodeB.translate >> self.base.translate
        nodeB.attribute("scale") >> self.base.attribute("scale")
        self.assertTrue(len(list(nodeB.translate.destinations())), 2)
        nodeB.translate.disconnectAll()
        self.assertEquals(len(list(nodeB.translate.destinations())), 0)

    def test_get(self):
        self.assertIsInstance(self.base.translate.get(), list)
        self.assertIsInstance(self.base.rotate.get(), list)
        self.assertIsInstance(self.base.attribute("worldMatrix")[0].get(), zapi.Matrix)
        n = zapi.nodeByName("lightLinker1")
        self.assertIsInstance(n.link.get(), list)

    def test_set(self):
        self.base.translate.set((10, 0.0, 0.0))
        self.assertEquals(self.base.translate.get(), [10, 0.0, 0.0])
        self.base.attribute("worldMatrix")[0].set(zapi.Matrix())

    def test_delete(self):
        p = self.base.addAttribute("test_attr", Type=zapi.attrtypes.kMFnDataString)
        self.assertTrue(self.base.hasAttribute("test_attr"))
        self.assertTrue(p.delete())
        self.assertFalse(self.base.hasAttribute("test_attr"))
