from maya.api import OpenMaya as om2
from zoo.libs.maya.api import scene
from zoo.libs.utils import zlogging

logger = zlogging.getLogger(__name__)


class MCallbackIdWrapper(object):
    """Wrapper class to handle cleaning up of MCallbackIds from registered MMessage
    """

    def __init__(self, callbackId):
        super(MCallbackIdWrapper, self).__init__()
        self.callbackId = callbackId

    def __del__(self):
        om2.MMessage.removeCallback(self.callbackId)

    def __repr__(self):
        return 'MCallbackIdWrapper(%r)' % self.callbackId


def removeCallbacksFromNode(mobject):
    """
    :param mobject: The node to remote all node callbacks from
    :type mobject: om2.MObject
    :return: the number of callbacks removed
    :rtype: int
    """
    calls = om2.MMessage.nodeCallbacks(mobject)
    count = len(calls)
    for cb in iter(calls):
        om2.MMessage.removeCallback(cb)
    return count


def removeCallbacksFromNodes(mobjects):
    """Will remove all callbacks from each node.

    :param mobjects: The nodes to remove callbacks from
    :type mobjects: sequence(MObject)
    :return: total count of all callbacks removed
    :rtype: int
    """

    cbcount = 0
    for mobj in iter(mobjects):
        cbcount += removeCallbacksFromNode(mobj)
    return cbcount


class CallbackSelection(object):
    """ Class handles the management of a single selection callback which can be stored in a GUI.

    To activate the callback use start()
    To cleanup run stop()

    :Note: Selected objects are passed to the callback as a keyword argument "selection"

    .. code-block:: python

        from zoo.libs.maya.api import nodes

        def myCallbackFunction(selection):
            # do stuff to the selection which is a list of OpenMaya.MObjectHandle
            for MObjectHandle in selection:
                if not i.isValid() or not i.isAlive():
                    continue
                # print the fullPathName of the selected, FYI: this has arguments for stripping namespace etc too.
                print(nodes.nameFromMObject(i.object()))

        callbackInstance = CallbackSelection(myCallbackFunction)  # add the function here
        callbackInstance.start()
        callbackInstance.stop()

    """

    def __init__(self, func, *args, **kwargs):
        """
        :param func: Your function to call when the selection is changed
        :type func: a callable object
        :param args: arguments to pass to the callable each time the selection is changed.
        :type args: tuple
        :param kwargs:
        :type kwargs: keyword arguments to pass to the callable each time the selection is changed.
        """
        self.selectionChangeCallback = None
        self.currentSelection = list()
        self.currentCallbackState = False
        self.callable = func
        self.arguments = args
        self.keywordsArgs = kwargs

    def __del__(self):
        """Overridden so we cleanup the callback automatically on instance being deleted
        """
        self.stop()

    def mayaSelectionChanged(self, *args, **kwargs):
        """The Open Maya 2 code for monitoring a selection callback with a short and longname list of strings

        """
        # iterSelectedNodes is a generator which returns MObjects
        # because we're storing the selection on this instance for a undetermine amount
        # of time it's a must to convert to an MObjectHandle
        # it's the client callables responsibility to ensure objects are still valid
        selection = scene.iterSelectedNodes(om2.MFn.kTransform)
        self.currentSelection = map(om2.MObjectHandle, selection)
        # create a new keyword structure so we don't modify the original
        keyWords = {"selection": self.currentSelection}
        keyWords.update(self.keywordsArgs)
        # call the client function
        self.callable(*self.arguments, **keyWords)

    def start(self):
        """Creates and stores the selection callback on this instance.
        """
        if self.currentCallbackState:
            return
        if self.callable is None:
            logger.error("Callable must be supplied!")
            return
        # create callback and store it in a variable
        self.selectionChangeCallback = MCallbackIdWrapper(om2.MEventMessage.addEventCallback("SelectionChanged",
                                                                                             self.mayaSelectionChanged))
        self.currentCallbackState = True

    def stop(self):
        """Cleans up the instance by removing the maya api callback
        """
        if not self.currentCallbackState:
            return
        try:
            self.selectionChangeCallback = None

            self.currentCallbackState = False
            self.currentSelection = []

        except Exception:
            logger.error("Unknown Error Occurred during deleting callback", exc_info=True)
            om2.MGlobal.displayError("Selection Callback Failed To Be Removed")
