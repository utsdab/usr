from maya import cmds
from maya.api import OpenMaya as om2

from tests import mayatestutils
from zoo.libs.maya.api import plugs


class TestPlugs(mayatestutils.BaseMayaTest):
    application = "maya"

    def setUp(self):
        self.node = cmds.createNode("transform")

    def test_asMPlug(self):
        self.assertIsInstance(plugs.asMPlug(self.node + ".translate"), om2.MPlug)
        self.assertIsInstance(plugs.asMPlug(self.node + ".translateX"), om2.MPlug)
        self.assertIsInstance(plugs.asMPlug(self.node + ".worldMatrix[0]"), om2.MPlug)

    def test_isValidMPlug(self):
        obj = plugs.asMPlug(self.node + ".translate")
        self.assertTrue(plugs.isValidMPlug(obj))

    def test_connectPlugs(self):
        node = cmds.createNode("transform")
        plugSource = plugs.asMPlug(self.node + ".translate")
        plugdestination = plugs.asMPlug(node + ".translate")
        plugs.connectPlugs(plugSource, plugdestination)
        self.assertTrue(plugSource.isConnected)
        self.assertTrue(plugSource.isSource)
        self.assertTrue(plugdestination.isConnected)
        self.assertTrue(plugdestination.isDestination)
        connections = plugSource.connectedTo(False, True)
        self.assertTrue(connections[0] == plugdestination)

    def test_disconnect(self):
        node2 = cmds.createNode("transform")
        node3 = cmds.createNode("transform")
        plugSource = plugs.asMPlug(node2 + ".translate")
        plugMid = plugs.asMPlug(self.node + ".translate")
        plugDest = plugs.asMPlug(node3 + ".translate")
        plugs.connectPlugs(plugSource, plugMid)
        plugs.connectPlugs(plugMid, plugDest)
        plugSource.isLocked = True
        plugMid.isLocked = True
        plugDest.isLocked = True
        self.assertTrue(plugs.disconnectPlug(plugMid))
        self.assertFalse(plugSource.isSource)
        self.assertFalse(plugMid.isSource)
        self.assertFalse(plugDest.isSource)
        self.assertFalse(plugDest.isDestination)

    def test_setLockState(self):
        p = plugs.asMPlug(self.node + ".translate")
        self.assertTrue(plugs.setLockState(p, True))
        self.assertTrue(p.isLocked)
        self.assertTrue(plugs.setLockState(p, False))
        self.assertFalse(p.isLocked)

    def test_isLockedContext(self):
        p = plugs.asMPlug(self.node + ".translate")
        p.isLocked = True
        with plugs.setLockedContext(p):
            self.assertFalse(p.isLocked)
        self.assertTrue(p.isLocked)

    def test_enumNames(self):
        p = plugs.asMPlug(self.node + ".rotateOrder")
        self.assertEquals(len(plugs.enumNames(p)), 6)

    def test_enumIndices(self):
        p = plugs.asMPlug(self.node + ".rotateOrder")
        self.assertEquals(len(list(plugs.enumIndices(p))), 6)
        self.assertEquals(list(plugs.enumIndices(p)), list(range(6)))

    def test_iterChildren(self):
        translate = plugs.asMPlug(self.node + ".translate")
        worldMatrix = plugs.asMPlug(self.node + ".parentInverseMatrix")
        for i in plugs.iterChildren(translate):
            self.assertIsInstance(i, om2.MPlug)
        for i in plugs.iterChildren(worldMatrix):
            self.assertIsInstance(i, om2.MPlug)
