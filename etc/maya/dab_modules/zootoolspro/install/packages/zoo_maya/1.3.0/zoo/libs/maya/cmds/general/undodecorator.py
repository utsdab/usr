from functools import wraps
from maya import cmds


def undoDecorator(func):
    """ Puts the wrapped `func` into a single Maya Undo action, then
    undoes it when the function enters the finally: block

    @undoDecorator
    def myoperationFunc():
        pass
    """

    @wraps(func)
    def _undofunc(*args, **kwargs):
        try:
            # start an undo chunk
            cmds.undoInfo(openChunk=True)
            return func(*args, **kwargs)
        finally:
            # after calling the func, end the undo chunk and undo
            cmds.undoInfo(closeChunk=True)
    return _undofunc


def openUndoChunk():
    """Opens a Maya undo chunk
    """
    cmds.undoInfo(openChunk=True)


def closeUndoChunk():
    """Opens a Maya undo chunk
    """
    cmds.undoInfo(closeChunk=True)

