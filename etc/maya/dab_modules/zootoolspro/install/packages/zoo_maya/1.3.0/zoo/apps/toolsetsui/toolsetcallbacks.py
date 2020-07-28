from functools import wraps
from zoo.libs.utils import zlogging
logger = zlogging.getLogger(__name__)
from Qt import QtCore

try:
    from zoo.libs.maya.api import nodes
except ImportError:
    logger.warning("toolsetcallbacks.py: Maya Modules not loaded")


UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class SelectionCallbacksMaya(QtCore.QObject):
    """ SelectionCallbacksMaya

    Might be better used as an object rather than an inheritable class
    # ! make this a referenced object on the toolsetwidgetMaya. ie. self.event = SelectionCallbackMaya()
    """

    callback = QtCore.Signal(object)

    def __init__(self):
        super(SelectionCallbacksMaya, self).__init__()
        self._initCallbacks()

    def _initCallbacks(self):
        """ Initialize the callbacks

        :return:
        :rtype:
        """

        from zoo.libs.maya.api import callbacks

        self._blockCallbacks = False
        self.callbackActive = False
        self.callbackInstance = callbacks.CallbackSelection(self.mayaSelChangedCallback)

    def callbacksBlocked(self):
        return self._blockCallbacks

    def blockCallbacks(self, block):
        self._blockCallbacks = block

    def convertMObjsToStringList(self, selection):
        """ Converts MObjectHandles (or MObjects) to a list of strings

        :param selection: list of mObject pointers
        :type selection: list(mObject)
        :return selection: object names as strings
        :rtype selection: list(str)
        """
        selObjs = list()
        for i in selection:
            if not i.isValid() or not i.isAlive():
                continue
            selObjs.append(nodes.nameFromMObject(i.object()))
        return selObjs

    def mayaSelChangedCallback(self, selection):
        """ The selection callback the triggers on selection changed, is triggered by:

            callbacks.CallbackSelection(self.mayaSelChangedCallback)

        :param selection: The callback automatically passes in this list of MObjectHandles (or MObjects)
        :type selection: list(:class:om2.MObject)
        :return:
        :rtype:
        """
        if not self.callbacksBlocked():
            self.callback.emit(self.convertMObjsToStringList(selection))  # sel is converted from mObjects

    def startSelectionCallback(self):
        """Starts the callback, selectionCallback signal will be emitted with a selection list(str)"""
        if self.callbackActive:
            return
        self.callbackInstance.start()
        self.callbackActive = True
        logger.debug("Callback Started >>  ON <<")
        return self.callbackActive

    def stopSelectionCallback(self):
        """Stops the callback by deleting it, the python instance still remains (self.callbackInstance)"""
        if not self.callbackActive:
            return
        self.callbackInstance.stop()
        self.callbackActive = False
        logger.debug("Callback Stopped >> OFF <<")

        return self.callbackActive

    def setSelectionCallbackState(self, state):
        """Sets the callback state either True or False"""
        if state:
            self.startSelectionCallback()  # returns self.callbackActive
        else:
            self.stopSelectionCallback()  # returns self.callbackActive


def ignoreCallbackDecorator(method):
    """ Decorator to temporarily disable the selection callback if it is running in the UI.

    @undoDecorator
    def lightUIMethod():
        pass
    """

    @wraps(method)
    def _disableMethod(self, *args, **kwargs):
        try:
            # todo: fix this, toolsetWidget currently needs to be here since this is run in the arealight subclass,
            #  need to figure a way to specify right place to call blockCallbacks
            self.toolsetWidget.blockCallbacks(True)  # bool that tells other stuff to activate
            return method(self, *args, **kwargs)  # run the method
        finally:
            self.toolsetWidget.blockCallbacks(False)

    return _disableMethod