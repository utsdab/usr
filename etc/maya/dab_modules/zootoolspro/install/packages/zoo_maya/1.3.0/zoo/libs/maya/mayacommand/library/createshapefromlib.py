from zoo.libs.command import command
from zoo.libs.maya.api import nodes
from zoo.libs.maya import shapelib
from maya.api import OpenMaya as om2
from maya import cmds


class CreateCurveFromLibrary(command.ZooCommand):
    """This command Creates a nurbs curve from the shapelib
    """
    id = "zoo.maya.curves.createFromLib"
    creator = "David Sparrow"
    isUndoable = True
    uiData = {"icon": "",
              "tooltip": "",
              "label": "Create Curve from library",
              "color": "",
              "backgroundColor": ""
              }
    # stores the parent MObject
    _parent = None
    # if the parent requires to be created then this will be True
    _newParent = False
    _shapeNodes = []

    def resolveArguments(self, arguments):
        try:
            parent = arguments.parent
        except AttributeError:
            parent = None
        libraryName = arguments.libraryName
        if parent is not None:
            handle = om2.MObjectHandle(parent)
            if not handle.isValid() or not handle.isAlive():
                self.cancel("Parent no longer exists in the scene: {}".format(parent))
            parent = handle
        else:
            self._newParent = True
        if not libraryName:
            raise ValueError("Library Name is not a valid name: {}".format(libraryName))
        elif not shapelib.findShapePathByName(libraryName):
            raise shapelib.MissingShapeFromLibrary("The shape name '{}' doesn't "
                                                   "exist in the library".format(libraryName))
        arguments["parent"] = parent
        self._parent = parent
        return arguments

    def doIt(self, libraryName=None, parent=None):
        """
        :param: libraryName: The shape name from the library
        :type libraryName: str
        :param parent: The parent transform MObjectHandle to parent the created shapes too.
        :return: see :func:`shapelib.loadAndCreateFromLib`
        :raise: :class:`shapelib.MissingShapeFromLibrary`
        """
        parentMObject, shapeNodes = shapelib.loadAndCreateFromLib(libraryName,
                                                                  parent=parent.object() if parent is not None else None)
        self._parent = om2.MObjectHandle(parentMObject)
        self._shapeNodes = map(om2.MObjectHandle, shapeNodes)
        return parentMObject, shapeNodes

    def undoIt(self):
        # if we have created a new parent transform then we only need to delete the transform

        if self._newParent:

            if _validMObjectHandle(self._parent):
                cmds.delete(nodes.nameFromMObject(self._parent.object()))
        # if the client passed a parent then we delete the individual shapes instead of the transform
        elif self._shapeNodes:
            cmds.delete([nodes.nameFromMObject(i.object()) for i in self._shapeNodes if _validMObjectHandle(i)])


class CreateCurveFromFilePath(command.ZooCommand):
    """This command Creates a nurbs curve from a folder path and shape designName
    """
    id = "zoo.maya.curves.createFromFilePath"
    creator = "David Sparrow"
    isUndoable = True
    uiData = {"icon": "",
              "tooltip": "",
              "label": "Create Curve From File Path",
              "color": "",
              "backgroundColor": ""
              }
    # stores the parent MObject
    _parent = None
    # if the parent requires to be created then this will be True
    _newParent = False
    _shapeNodes = []

    def resolveArguments(self, arguments):
        try:
            parent = arguments.parent
        except AttributeError:
            parent = None
        designName = arguments.designName
        if parent is not None:
            handle = om2.MObjectHandle(parent)
            if not handle.isValid() or not handle.isAlive():
                self.cancel("Parent no longer exists in the scene: {}".format(parent))
            parent = handle
        else:
            self._newParent = True
        if not designName:
            raise ValueError("Library Name is not a valid name: {}".format(designName))
        arguments["parent"] = parent
        self._parent = parent
        return arguments

    def doIt(self, designName=None, parent=None, folderpath=None):
        """
        :param: libraryName: The shape name from the library
        :type libraryName: str
        :param parent: The parent transform MObjectHandle to parent the created shapes too.
        :return: see :func:`shapelib.loadAndCreateFromLib`
        :raise: :class:`shapelib.MissingShapeFromLibrary`
        """
        parentMObject, shapeNodes = shapelib.loadAndCreateFromPath(designName, folderpath,
                                                                  parent=parent.object() if parent is not None else None)
        self._parent = om2.MObjectHandle(parentMObject)
        self._shapeNodes = map(om2.MObjectHandle, shapeNodes)
        return parentMObject, shapeNodes

    def undoIt(self):
        # if we have created a new parent transform then we only need to delete the transform

        if self._newParent:

            if _validMObjectHandle(self._parent):
                cmds.delete(nodes.nameFromMObject(self._parent.object()))
        # if the client passed a parent then we delete the individual shapes instead of the transform
        elif self._shapeNodes:
            cmds.delete([nodes.nameFromMObject(i.object()) for i in self._shapeNodes if _validMObjectHandle(i)])


def _validMObjectHandle(handle):
    return handle.isValid() and handle.isAlive()
