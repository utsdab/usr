import os
from maya import cmds
from tests import mayatestutils

from zoo.libs.command import executor
from maya.api import OpenMaya as om2


class TestMayaCommandExecutor(mayatestutils.BaseMayaTest):
    @classmethod
    def setUpClass(cls):
        super(TestMayaCommandExecutor, cls).setUpClass()
        os.environ["TESTDATA"] = os.pathsep.join(["tests.testdata.mayacommanddata.testmayacommand",
                                                  "tests.testdata.commanddata.testcommands"])

    def setUp(self):
        self.executor = executor.Executor()
        self.executor.flush()
        self.env = "TESTDATA"
        self.executor.registry.registerByEnv(self.env)

    def testCommandExecutes(self):
        result = self.executor.execute("test.mayaSimpleCommand")
        self.assertEquals(result, "hello world")
        self.assertEquals(len(self.executor.undoStack), 1)

    # standalone based commands need to be tested in maya as well
    def testCommandFailsArguments(self):
        with self.assertRaises(ValueError) as context:
            self.executor.execute("Test.FailCommandArguments", value="helloWorld")
        self.assertTrue('Test.FailCommandArguments' in str(context.exception))
        self.assertEquals(len(self.executor.undoStack), 0)

    def testUndoLast(self):
        self.assertEquals(len(self.executor.undoStack), 0)
        result = self.executor.execute("test.mayaTestCreateNodeCommand")
        self.assertIsInstance(result, om2.MObject)
        self.assertEquals(len(self.executor.undoStack), 1)
        cmds.undo()
        self.assertEquals(len(self.executor.undoStack), 0)
        self.assertEquals(len(self.executor.redoStack), 1)
        cmds.redo()
        self.assertEquals(len(self.executor.redoStack), 0)
        self.assertEquals(len(self.executor.undoStack), 1)

    def testUndoSkips(self):
        result = self.executor.execute("test.mayaNotUndoableCommand")
        self.assertEquals(result, "hello world")
        self.assertEquals(len(self.executor.undoStack), 0)
        result = self.executor.undoLast()
        self.assertFalse(result)

    def testFlush(self):
        result = self.executor.execute("test.mayaTestCreateNodeCommand")
        self.assertIsInstance(result, om2.MObject)
        self.assertEquals(len(self.executor.undoStack), 1)
        self.executor.flush()
        self.assertEquals(len(self.executor.undoStack), 0)
