from zoo.libs.command import command


class TestCommandReg(command.ZooCommand):
    id = "test.testCommand"
    creator = "davidsp"
    isUndoable = False
    isEnabled = True

    def doIt(self, value="hello"):
        return value


class FailCommandArguments(command.ZooCommand):
    id = "test.failCommandArguments"
    creator = "davidsp"
    isUndoable = False
    isEnabled = True

    def doIt(self, value):
        pass


class TestCommandUndoable(command.ZooCommand):
    id = "test.testCommandUndoable"
    creator = "davidsp"
    isUndoable = True
    isEnabled = True
    value = ""

    def doIt(self, value="hello"):
        self.value = value
        return value

    def undoIt(self):
        self.value = ""


class TestCommandNotUndoable(command.ZooCommand):
    id = "test.testCommandNotUndoable"
    creator = "davidsp"
    isUndoable = False
    isEnabled = True
    value = ""

    def doIt(self, value="hello"):
        self.value = value
        return value

    def undoIt(self):
        self.value = ""
