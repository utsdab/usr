import os
import random
import uuid

from maya import cmds

from zoo.libs.utils import filesystem
from tests import mayatestutils
from zoo.libs.maya.api import nodes
from zoo.libs.maya import shapelib


class TestShapeLib(mayatestutils.BaseMayaTest):
    def setUp(self):
        super(TestShapeLib, self).setUp()
        self.shapePath = ""

    def test_shapeLibDiscoveryReturnsNames(self):
        names = [i for i in shapelib.iterAvailableShapesNames()]
        self.assertIsNotNone(names)
        self.assertTrue(len(names) > 0)
        self.assertIsInstance(names[random.randrange(0, len(names))], basestring)

    def test_shapeLoadsFromLibrary(self):
        names = [i for i in shapelib.iterAvailableShapesNames()]
        data = shapelib.loadFromLib(names[random.randrange(0, len(names))])
        self.assertIsInstance(data, dict)

        self.assertRaises(shapelib.MissingShapeFromLibrary, shapelib.loadFromLib, str(uuid.uuid4()))

    def test_shapeSaveToLibrary(self):
        circle = cmds.circle(ch=False)[0]
        self.data, self.shapePath = shapelib.saveToLib(nodes.asMObject(circle), "circleTest")
        data = filesystem.loadJson(self.shapePath)

        for shapeName, shapeData in iter(data.items()):
            self.assertTrue("cvs" in shapeData)
            self.assertTrue("degree" in shapeData)
            self.assertTrue("form" in shapeData)
            self.assertTrue("knots" in shapeData)
            self.assertTrue("overrideColorRGB" in shapeData)
            self.assertTrue("overrideEnabled" in shapeData)
            self.assertTrue(shapeName in cmds.listRelatives(circle, s=True)[0])
            self.assertEquals(len(shapeData["cvs"]), len(self.data[shapeName]["cvs"]))
            self.assertEquals(len(shapeData["knots"]), len(self.data[shapeName]["knots"]))
            self.assertEquals(shapeData["degree"], self.data[shapeName]["degree"])
            self.assertEquals(shapeData["form"], self.data[shapeName]["form"])
            self.assertEquals(tuple(shapeData["knots"]), self.data[shapeName]["knots"])
            self.assertEquals(shapeData["overrideColorRGB"], self.data[shapeName]["overrideColorRGB"])
            self.assertEquals(shapeData["overrideEnabled"], self.data[shapeName]["overrideEnabled"])

    def tearDown(self):
        super(TestShapeLib, self).tearDown()
        if os.path.exists(self.shapePath):
            os.remove(self.shapePath)
