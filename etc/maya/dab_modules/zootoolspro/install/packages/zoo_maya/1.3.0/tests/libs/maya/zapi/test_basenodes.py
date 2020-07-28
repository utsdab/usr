import types

from maya import cmds
from maya.api import OpenMaya as om2
from zoo.libs.maya import zapi
from zoo.libs.maya.api import attrtypes
from zoo.libs.maya.api import constants as apiconstants
from tests import mayatestutils


class TestBase(mayatestutils.BaseMayaTest):
    def setUp(self):
        self.base = zapi.createDG("testNode", "multiplyDivide")

    def test_mfn(self):
        self.assertIsInstance(self.base.mfn(), om2.MFnDependencyNode)

    def test_name(self):
        self.base.addAttribute("name", Type=attrtypes.kMFnDataString, value="testName", default="")
        self.assertEquals(str(self.base.attribute("name").get()), "testName")
        self.base.deleteAttribute("name")
        self.base.addAttribute("id", Type=attrtypes.kMFnDataString, value="testName", default="")
        self.assertEquals(str(self.base.attribute("id").get()), "testName")
        self.base.deleteAttribute("id")
        self.assertEquals(self.base.name(), "testNode")

    def test_rename(self):
        self.base.rename("newName")
        self.assertEquals(self.base.name(), "newName")

    def test_lock(self):
        self.base.lock(True)
        self.assertTrue(self.base.isLocked)
        self.base.lock(False)
        self.assertFalse(self.base.isLocked)

    def test_namespace(self):
        self.assertEquals(self.base.namespace(), ":")  # root namespace, om2 returns "" though so we fix this crap

    def test_renameNamespace(self):
        self.base.renameNamespace("somenewNamespace")
        self.assertEquals(self.base.namespace(), ":somenewNamespace")
        self.base.renameNamespace("helloWorld")

    def test_parentNamespace(self):
        self.base.renameNamespace("somenewNamespace")
        self.assertEquals(self.base.parentNamespace(), ":")

    def test_removeNamespace(self):
        self.base.renameNamespace("somenewNamespace")
        self.base.removeNamespace()
        self.assertEquals(self.base.parentNamespace(), ":")

    def test_delete(self):
        self.base.lock(True)
        output = self.base.attribute("output")
        output.isLocked = True

        testNode = zapi.createDG("testNode2", "multiplyDivide")
        self.base.output.connect(testNode.input1)
        testNode.isLocked = True
        testNode.input1.isLocked = True
        self.assertTrue(self.base.delete())

    def test_addAttribute(self):
        raise NotImplementedError()

    def test_setAttribute(self):
        raise NotImplementedError()

    def test_getAttribute(self):
        self.assertIsInstance(self.base.attribute("input1"), zapi.Plug)
        self.assertIsNone(self.base.attribute("testAttr"))

    def test_connectSourceAttribute(self):
        testNode = zapi.createDG("testNode", "multiplyDivide")
        testNode.connect("output", self.base.input1)
        self.assertTrue(self.base.input1.source() == testNode.output)
        testNode.delete()

    def test_connectDestinationAttribute(self):
        testNode = zapi.createDG("testNode", "multiplyDivide")
        testNode.connectDestinationAttribute("input1", self.base.output)
        self.assertTrue(testNode.input1.source() == self.base.output)
        testNode.delete()

    def test_createAttributesFromDict(self):
        raise NotImplementedError()

    def test_setMObject(self):
        testNode = zapi.createDG("test", "network")
        # make sure dagnodes will work too
        testNode1 = zapi.createDag("test1", "transform")
        self.base.setObject(testNode.object())
        self.assertEquals(self.base, testNode)
        self.assertIsInstance(self.base.mfn(), om2.MFnDependencyNode)
        self.base.setObject(testNode1.object())
        self.assertEquals(self.base, testNode1)
        self.assertIsInstance(self.base.mfn(), om2.MFnDependencyNode)

    def test_hasAttribute(self):
        base = zapi.createDag("test", "transform")
        self.assertTrue(self.base.hasAttribute("nodeState"))
        self.assertFalse(self.base.hasAttribute("bob"))
        self.assertTrue(base.hasAttribute("worldMatrix"))
        self.assertFalse(base.hasAttribute("worldMatrix[0]"))

    def test_removeAttribute(self):
        self.base.addAttribute("test", attrtypes.kMFnNumericInt)
        self.assertTrue(self.base.hasAttribute("test"))
        self.base.deleteAttribute("test")

    def test_iterAttributes(self):
        self.assertIsInstance(self.base.iterAttributes(), types.GeneratorType)
        for i in self.base.iterAttributes():
            self.assertIsInstance(i, zapi.Plug)

    def test_iterExtraAttributes(self):
        self.assertIsInstance(self.base.iterExtraAttributes(), types.GeneratorType)
        for i in self.base.iterExtraAttributes():
            self.assertIsInstance(i, zapi.Plug)
            self.assertTrue(i.isDynamic)

    def test_addCompoundAttribute(self):
        raise NotImplementedError()

    def test_serializeFromScene(self):
        data = self.base.serializeFromScene()
        self.assertTrue(data != dict())


class TestTreeNode(mayatestutils.BaseMayaTest):
    def setUp(self):
        self.base = zapi.createDag("testNode", "transform")
        self.node2 = zapi.createDag("testNode2", "transform")

    def test_setMObject(self):
        # make sure dgnodes raise
        testNode1 = zapi.createDag("test1", "transform")
        testNod2 = zapi.createDG("test", "network")
        self.base.setObject(testNode1.object())
        self.assertEquals(self.base, testNode1)
        self.assertIsInstance(self.base.mfn(), om2.MFnDagNode)
        with self.assertRaises(TypeError):
            self.base.setObject(testNod2.object())

    def test_mfn(self):
        self.assertIsInstance(self.base.mfn(), om2.MFnDagNode)

    def test_parent(self):
        self.assertIsNone(self.base.parent())
        self.base.setParent(self.node2)
        self.assertIsInstance(self.base.parent(), zapi.DagNode)
        self.assertEqual(self.base.parent(), self.node2)

    def test_delete(self):
        self.base.delete()
        self.assertFalse(cmds.objExists("testNode"))
        self.assertFalse(self.base.exists())

    def test_translation(self):
        self.base.setTranslation(om2.MVector(10, 10, 10), om2.MSpace.kWorld)
        self.assertEquals(self.base.translation(om2.MSpace.kWorld), om2.MVector(10, 10, 10))

    def test_rotation(self):
        self.base.setRotation(om2.MEulerRotation(1.0, 0.0, 0.0))
        self.assertIsInstance(self.base.rotation(asQuaternion=False), om2.MEulerRotation)
        self.assertEquals(self.base.rotation(asQuaternion=False), om2.MEulerRotation(1.0, 0.0, 0.0))
        self.base.setRotation(om2.MQuaternion(1.0, 0.0, 0.0, 1.0))
        self.assertIsInstance(self.base.rotation(asQuaternion=True), om2.MQuaternion)

    def test_scale(self):
        self.base.setScale((10, 10, 10))
        self.assertEquals(self.base.scale(), om2.MVector(10, 10, 10))

    def test_rotationOrder(self):
        self.assertEquals(self.base.rotationOrder(), apiconstants.kRotateOrder_XYZ)
        self.base.setRotationOrder(apiconstants.kRotateOrder_XZY)
        self.assertEquals(self.base.rotationOrder(), apiconstants.kRotateOrder_XZY)
        self.base.setRotationOrder()
        self.assertEquals(self.base.rotationOrder(), apiconstants.kRotateOrder_XYZ)

        def test_setPivot(self):
            raise NotImplementedError()

        def test_getChild(self):
            raise NotImplementedError()

        def test_children(self):
            raise NotImplementedError()

        def test_iterChildren(self):
            raise NotImplementedError()

        def test_addChild(self):
            raise NotImplementedError()

        def test_setParent(self):
            raise NotImplementedError()

        def test_hasConstraint(self):
            raise NotImplementedError()

        def test_addConstraintAttribute(self):
            raise NotImplementedError()

        def test_iterConstraints(self):
            raise NotImplementedError()

        def test_addConstraintMap(self):
            raise NotImplementedError()

        def test_connectToScaleConstraint(self):
            raise NotImplementedError()

        def test_connectToConstraint(self):
            raise NotImplementedError()

        def test_connectToMatrix(self):
            raise NotImplementedError()


    def test_connectLocalTranslate(self):
        testNode = zapi.createDag("driven", "transform")
        self.base.connectLocalTranslate(testNode)
        self.assertTrue(self.base.translate.isSource)
        attrs = (("translate", True), ("translateX", False), ("translateY", True), ("translateZ", False))
        self.base.connectLocalTranslate(testNode, axis=(False, True, False), force=True)
        for i, shConnect in attrs:
            plug = self.base.attribute(i)
            if shConnect:
                self.assertTrue(plug.isSource)
                for dest in plug.destinations():
                    self.assertTrue("translate" in dest.name())
                continue
            self.assertFalse(plug.isSource)

    def test_connectLocalRotate(self):
        testNode = zapi.createDag("driven", "transform")
        self.base.connectLocalRotate(testNode)
        self.assertTrue(self.base.rotate.isSource)
        attrs = (("rotate", True), ("rotateX", False), ("rotateY", True), ("rotateZ", False))
        self.base.connectLocalRotate(testNode, axis=(False, True, False), force=True)
        for i, shConnect in attrs:
            plug = self.base.attribute(i)
            if shConnect:
                self.assertTrue(plug.isSource)
                for dest in plug.destinations():
                    self.assertTrue(i in dest.name())
                continue
            self.assertFalse(plug.isSource)

    def test_connectLocalScale(self):
        testNode = zapi.createDag("driven", "transform")
        self.base.connectLocalScale(testNode)
        self.assertTrue(self.base.attribute("scale").isSource)
        attrs = (("scale", True), ("scaleX", False), ("scaleY", True), ("scaleZ", False))
        self.base.connectLocalScale(testNode, axis=(False, True, False), force=True)
        for i, shConnect in attrs:
            plug = self.base.attribute(i)
            if shConnect:
                self.assertTrue(plug.isSource)
                for dest in plug.destinations():
                    self.assertTrue(i in dest.name())
                continue
            self.assertFalse(plug.isSource)

    def test_connectLocalSrt(self):
        testNode = zapi.createDag("driven", "transform")
        self.base.connectLocalSrt(testNode)

        attrs = (("translate", True), ("rotate", True), ("scale", True),
                 ("translateX", False), ("translateY", True), ("translateZ", False),
                 ("rotateX", False), ("rotateY", True), ("rotateZ", False),
                 ("scaleX", False), ("scaleY", True), ("scaleZ", False))
        self.base.connectLocalSrt(testNode, scaleAxis=(False, True, False),
                                  rotateAxis=(False, True, False), translateAxis=(False, True, False),
                                  force=True)
        for i, shConnect in attrs:
            plug = self.base.attribute(i)
            if shConnect:
                self.assertTrue(plug.isSource)
                for dest in plug.destinations():
                    self.assertTrue(i in dest.name())
                continue
            self.assertFalse(plug.isSource)


class ContainerAsset(mayatestutils.BaseMayaTest):
    def setUp(self):
        pass

    def test_create(self):
        raise NotImplementedError()

    def test_serializeFromScene(self):
        raise NotImplementedError()

