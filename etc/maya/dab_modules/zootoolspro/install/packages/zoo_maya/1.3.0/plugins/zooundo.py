"""This module stores our Custom undo MPxCommand. Due to shit maya api undo support we're had to implement
our own that supports mel and API code. This MPx store's a zoo command which operate on the maya eg node creation.
When undo is called by maya or by the user the MpxCommand will call the zooExecutor class which manages undo.
"""
import sys

from maya.api import OpenMaya as om2

if not hasattr(om2, "_ZOOCOMMAND"):
    om2._ZOOCOMMAND = None
    om2._COMMANDEXECUTOR = None


def maya_useNewAPI():
    """WTF AutoDesk? Its existence tells maya that we are using api 2.0. seriously this should of just been a flag
    """
    pass


class UndoCmd(om2.MPxCommand):
    """Specialised MPxCommand to get around maya api retarded features.
    Stores zoo Commands on the UndoCmd
    """

    kCmdName = "zooAPIUndo"

    def __init__(self):
        """We initialize a storage variable for a list of commands.
        """
        om2.MPxCommand.__init__(self)
        # store the zoo command and executor for the life of the MPxcommand instance.
        self._command = None
        self._commandExecutor = None

    def doIt(self, argumentList):
        """Grab the list of current commands from the stack and dump it on our command so we can call undo.

        :param argumentList: MArgList
        """
        # add the current queue into the mpxCommand instance then clean the queue since we dont need it anymore
        if om2._ZOOCOMMAND is not None:
            self._command = om2._ZOOCOMMAND
            om2._ZOOCOMMAND = None
            self._commandExecutor = om2._COMMANDEXECUTOR
            self.redoIt()

    def redoIt(self):
        """Runs the doit method on each of our stored commands
        """
        if self._command is None:
            return
        self._commandExecutor._callDoIt(self._command)

    def undoIt(self):
        """Calls undoIt on each stored command in reverse order
        """
        if self._command is None:
            return
        elif self._command != om2._COMMANDEXECUTOR.undoStack[-1]:
            raise ValueError("Undo stack has become out of the sync with zoocommands {}".format(self._command.id))
        elif self._command.isUndoable:
            try:
                self._command.undoIt()
            finally:
                om2._COMMANDEXECUTOR.redoStack.append(self._command)
                om2._COMMANDEXECUTOR.undoStack.pop()

    def isUndoable(self):
        """True if we have stored commands
        :return: bool
        """

        return self._command.isUndoable

    @classmethod
    def cmdCreator(cls):
        return UndoCmd()

    @classmethod
    def syntaxCreator(cls):
        return om2.MSyntax()


def initializePlugin(mobject):
    mplugin = om2.MFnPlugin(mobject, "David Sparrow", "1.0", "Any")
    try:
        mplugin.registerCommand(UndoCmd.kCmdName, UndoCmd.cmdCreator, UndoCmd.syntaxCreator)
    except:
        sys.stderr.write('Failed to register command: ' + UndoCmd.kCmdName)


# Uninitialize the script plug-in
def uninitializePlugin(mobject):
    mplugin = om2.MFnPlugin(mobject)
    try:
        mplugin.deregisterCommand(UndoCmd.kCmdName)
    except:
        sys.stderr.write('Failed to unregister command: %s' % UndoCmd.kCmdName)
