from zoo.libs.utils import unittestBase
from zoo.libs.command import command


class TestZooCommand(command.ZooCommand):
    id = "helloWorld"
    creator = "davidsp"
    isUndoable = False
    isEnabled = True

    def doIt(self):
        return "helloWorld"


class TestZooPrepareFailsCommand(command.ZooCommand):
    id = "zooPrepareFailsCommand"
    creator = "davidsp"
    isUndoable = False
    isEnabled = True

    def doIt(self, shouldfail, value="bob"):
        return "helloWorld"


class TestZooPreparePassesCommand(command.ZooCommand):
    id = "zooPreparePassesCommand"
    creator = "davidsp"
    isUndoable = False
    isEnabled = True

    def doIt(self, shouldFail="yea baby", value="bob"):
        return "helloWorld"


class TestCommand(unittestBase.BaseUnitest):
    def setUp(self):
        self.command = TestZooCommand()

    def testPrepareCommand(self):
        self.command._prepareCommand()
        self.assertEquals(self.command.arguments, dict())
        prepped = TestZooPrepareFailsCommand()
        self.assertRaises(ValueError, prepped._prepareCommand)
        passCommand = TestZooPreparePassesCommand()
        self.assertEquals(len(passCommand._prepareCommand()), 2)

    def testResolveArguments(self):
        command = TestZooPreparePassesCommand()
        command._prepareCommand()
        self.assertTrue(command._resolveArguments({"shouldFail":
                                                       "hopeful",
                                                   "value": "hello"}))

