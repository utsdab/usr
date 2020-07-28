"""This module holds utility methods for dealing with nurbscurves
"""
import os
import glob
import maya.api.OpenMaya as om2

from zoo.libs.utils import filesystem

from zoo.libs.maya.api import nodes
from zoo.libs.maya.api import curves

# The shape file extension
SHAPE_FILE_EXT = "shape"
# the shape lib environment variable which specifies all the
# root locations.
SHAPE_LIB_ENV = "ZOO_SHAPE_LIB"



class MissingShapeFromLibrary(Exception):
    pass


def iterShapeRootPaths():
    """Generator function which iterates the root location based on the
    environment variable "ZOO_LIB_PATH"

    :return: Each  absolute path to each shape root directory.
    :rtype: generator(str)
    """
    for root in os.environ.get(SHAPE_LIB_ENV, "").split(os.pathsep):
        if not os.path.exists(root):
            continue
        yield root


def iterShapePaths():
    """iterator function which loops all the "*.shape" paths.

    :return: Generator  with each element == absolute path.shape
    :rtype: generator(str)
    """
    for root in iterShapeRootPaths():
        for shapePath in glob.glob(os.path.join(root, "*.{}".format(SHAPE_FILE_EXT))):
            yield shapePath


def iterAvailableShapesNames():
    """Generator function for looping over all available shape names

    Shapes are sourced from all the set root locations specified by the
    "ZOO_LIB_PATH" environment variable

    :return: An Iterate which returns each shape Name
    :rtype: Generator(str)
    """
    for shapePath in iterShapePaths():
        yield os.path.splitext(os.path.basename(shapePath))[0]


def shapeNames():
    """List all the curve shapes (design/patterns) available.

    Shapes are sourced from all the set root locations specified by the
    "ZOO_LIB_PATH" environment variable

    :return shapeNames: a list of curve designs (strings) available
    :rtype shapeNames: list(str)
    """
    return list(iterAvailableShapesNames())


def findShapePathByName(shapeName):
    """Find's the absolute shape path based on the shape name

    ..code-block: python

        shapePath = findShapePathByName("cube")

    name = (u'circle', u'.shape')
    name[0] = u'circle'

    :param shapeName: The shape name to find. eg. "cube"
    :type shapeName: str
    :return: The absolute shape path
    :rtype: str
    """
    for shapePath in iterShapePaths():
        name = os.path.splitext(os.path.basename(shapePath))
        if name[0] == shapeName:
            return shapePath


def loadFromLib(shapeName, parent=None):
    """Loads the data for the given shape Name

    :param shapeName: The shape name from the library, excluding the extension, see shapeNames()
    :type shapeName: str
    :param parent: if specified then this function will also create the shapes under the parent
    :type parent: MObject
    :return: A 2 tuple the first element is the MObject of the parent and the second is a list /
    of mobjects represents the shapes created
    :rtype: tuple(MObject, list(MObject))
    :raises: ValueError
    """
    matchedPath = findShapePathByName(shapeName)
    if not matchedPath:
        raise MissingShapeFromLibrary("The shape name '{}' doesn't exist in the library".format(shapeName))
    data = filesystem.loadJson(matchedPath)
    if data:
        return data


def loadAndCreateFromLib(shapeName, parent=None):
    """Load's and create's the nurbscurve from the shapelib.  If parent will shape node parent to the given object

    TODO: should combine zoo_preferences and zoo internal directories

    :param shapeName: the shape library name.
    :type shapeName: str
    :param parent: the parent for the nurbscurve default is None.
    :type parent: om2.MObject
    :return: A 2 tuple the first element is the MObject of the parent and the second is a list /
    of mobjects represents the shapes created
    :rtype: tuple(MObject, list(MObject))
    """
    newData = loadFromLib(shapeName, parent)
    return curves.createCurveShape(parent, newData)


def loadAndCreateFromPath(shapeName, folderpath, parent=None):
    """Load's and create's the nurbscurve from the design name and specific folder path.
    If parent will shape node parent to the given object

    TODO: should combine zoo_preferences and zoo internal directories

    :param shapeName: The shape name.
    :type shapeName: str
    :param folderpath: The folder path of the .shape file
    :type folderpath: str
    :param parent: the parent for the nurbscurve default is None.
    :type parent: om2.MObject
    :return: A 2 tuple the first element is the MObject of the parent and the second is a list /
    of mobjects represents the shapes created
    :rtype: tuple(MObject, list(MObject))
    """
    shapePath = os.path.join(folderpath, ".".join([shapeName, SHAPE_FILE_EXT]))
    newData = filesystem.loadJson(shapePath)
    return curves.createCurveShape(parent, newData)


def saveToLib(node, name, override=True, saveMatrix=False):
    """Save's the current transform node shapes to the zoo library
    Uses the default first SHAPE_LIB_ENV location as the directory:

        See saveToDirectory() for documentation

    """
    directory = os.environ.get(SHAPE_LIB_ENV, "").split(os.pathsep)[0]
    return saveToDirectory(node, name, directory, override=override, saveMatrix=saveMatrix)


def saveToDirectory(node, name, directory, override=True, saveMatrix=False):
    """Save's the current transform node shapes to a directory path

    :param node: The MObject to the transform that you want to save
    :type node: MObject
    :param name: The name of the file to create, if not specified the node name will be used, usually the design name
    :type name: str
    :param directory: The directory folder to save into
    :type directory: str
    :param saveMatrix: If True save the matrix information. On import can override matching, usually matrix not wanted.
    :type saveMatrix: bool
    :return: The file path to the newly created shape file
    :rtype: str

    .. code-block:: python

        nurbsCurve = cmds.circle()[0]
        # requires an MObject of the shape node
        data, path = saveToDirectory(api.asMObject(nurbsCurve))

    """
    if name is None:
        name = nodes.nameFromMObject(node, True, False)
    if not name.endswith(".{}".format(SHAPE_FILE_EXT)):
        name = ".".join([name, SHAPE_FILE_EXT])
    # if we don't want to override raise an error if there's a conflict in naming
    if not override and name in shapeNames():
        raise ValueError("name-> {} already exists in the shape library!".format(name))
    # serialize all the child shapes straight to a dict
    data = curves.serializeCurve(node)
    if not saveMatrix:  # remove the matrix key and info, usually not wanted, see docs
        for curveShape in data:
            data[curveShape].pop("matrix", None)
    path = os.path.join(directory, name)
    filesystem.saveJson(data, path)

    return data, path


def deleteShapeFromLib(shapeName, message=True):
    """Deletes a shape from the internal zoo library.  Deletes the file on disk.

    TODO: replace maya displayMessages with logging and create a maya log handler

    :param shapeName: The name of the shape without the extension.  Eg "circle" deletes "path/circle.shape"
    :type shapeName: str
    :param message: Report the message to the user?
    :type message: bool
    :return fileDeleted: If the file was deleted return True
    :rtype fileDeleted: bool
    """
    shapePath = findShapePathByName(shapeName)
    if not shapePath:
        if message:
            om2.MGlobal.displayWarning("The file could not be deleted, it does not exist.")
        return False
    # delete
    os.remove(shapePath)
    if message:
        om2.MGlobal.displayInfo("The Curve `{}` has been deleted from the Zoo Library".format(shapeName))
    return True


def renameLibraryShape(shapeName, newName, message=True):
    """Renames a shape from the internal zoo library.  Renames the file on disk.

    TODO: replace messages with a maya log handler

    :param shapeName: The name of the shape without the extension.  Eg "circle" deletes "path/circle.shape"
    :type shapeName: str
    :param newName: The new name of the shape.  Should not have the file extension.  eg. "star_05"
    :type newName: str
    :param message: Report the message to the user?
    :type message: bool
    :return newPath: the full path of the file now renamed.  Empty string if could not be renamed
    :rtype newPath: str
    """
    shapePath = findShapePathByName(shapeName)

    if not os.path.exists(shapePath):  # if not current path exists
        if message:
            om2.MGlobal.displayWarning("File not found: `{}`".format(shapePath))
        return ""
    newPath = os.path.join(os.path.dirname(shapePath), ".".join([newName, SHAPE_FILE_EXT]))
    # can't rename as new name already exists
    if os.path.exists(newPath):
        if message:
            om2.MGlobal.displayWarning("Cannot rename, new filename already exists: `{}`".format(newPath))
        return ""
    os.rename(shapePath, newPath)
    if message:
        om2.MGlobal.displayInfo("Success: Filename `{}` renamed to `{}`".format(shapePath, newPath))
    return newPath
