from maya.api import OpenMaya as om2
from zoovendor.six import string_types
from zoo.libs.maya.api import constants


class MObjectHandleWrap(om2.MObjectHandle):
    """Simple class to do what Autodesk should of done, this class makes the
    MObjectHandle hashable so it can be used in sets and dicts correctly.

    :note::
        maya's documentation says >, >=, <, <= but this isn't true at all
        part from the errors the c++ docs don't specify it so c++ is right, geez get
        your shit right.
    """

    def __hash__(self):
        return self.hashCode()


def isValidMObjectHandle(mObjHandle):
    """Checks whether the MObjectHandle is valid in the scene and still alive

    :param mObjHandle: OpenMaya.MObjectHandle
    """
    return mObjHandle.isValid() and mObjHandle.isAlive()


def isValidMObject(mObj):
    """Checks whether the MObject is valid in the scene.

    :param mObj: The mobject to validate.
    :type mObj: OpenMaya.MObject.
    :return: Whether or not this MObject is currently valid in the scene.
    :rtype: bool.
    """
    return isValidMObjectHandle(om2.MObjectHandle(mObj))


def compareMObjects(a, b):
    """Compares two nodes and returns whether they're equivalent or not - the compare is done on MObjects
    not strings.
    """

    if a is b:
        return True

    # make sure the objects are valid types...
    if b is None:
        return False

    if isinstance(a, string_types):
        a = asMObject(a)

    if isinstance(b, string_types):
        b = asMObject(b)

    if not isinstance(a, om2.MObject) or not isinstance(b, om2.MObject):
        return False

    return a == b


def asMObject(name):
    if isinstance(name, string_types):
        sel = om2.MSelectionList()
        sel.add(name)
        if "." in name:
            sel = om2.MSelectionList()
            sel.add(name)
            plug = sel.getPlug(0)
            return plug.asMObject()
        try:
            return sel.getDagPath(0).node()
        except TypeError:
            return sel.getDependNode(0)
    elif isinstance(name, om2.MObject):
        return name
    elif isinstance(name, om2.MObjectHandle):
        return name.object()
    elif isinstance(name, om2.MDagPath):
        return name.node()


def asEuler(rotation):
    """Converts tuple(float3) into a MEulerRotation

    :param rotation: a tuple of 3 elements in degrees which will be converted to redians for the eulerRotation
    :type rotation: tuple(float)
    :rtype: MEulerRotation
    """
    return om2.MEulerRotation([om2.MAngle(i, om2.MAngle.kDegrees).asRadians() for i in rotation])


def eulerToDegrees(euler):
    return [om2.MAngle(i, om2.MAngle.kRadians).asDegrees() for i in euler]


def softSelection():
    """Gets the current component softSelection

    :return: a set of tuples with 2 elements, the first is the vertexId and second is the weight value of the selection
    :rtype: set(tuple(id, float))
    """
    data = set()
    sel = om2.MGlobal.getRichSelection().getSelection()
    for i in range(sel.length()):
        try:
            dag, component = sel.getComponent(i)
        except TypeError:
            continue
        fnComp = om2.MFnSingleIndexedComponent(component)
        for cIdx in range(fnComp.elementCount):
            if fnComp.hasWeights:
                weight = fnComp.weight(cIdx).influence
                data.add((fnComp.element(cIdx), weight))
    return data


def intToMTransformRotationOrder(rotateOrder):
    if rotateOrder == constants.kRotateOrder_XYZ:
        return om2.MTransformationMatrix.kXYZ
    elif rotateOrder == constants.kRotateOrder_YZX:
        return om2.MTransformationMatrix.kYZX
    elif rotateOrder == constants.kRotateOrder_ZXY:
        return om2.MTransformationMatrix.kZXY
    elif rotateOrder == constants.kRotateOrder_XZY:
        return om2.MTransformationMatrix.kXZY
    elif rotateOrder == constants.kRotateOrder_YXZ:
        return om2.MTransformationMatrix.kYXZ
    elif rotateOrder == constants.kRotateOrder_ZYX:
        return om2.MTransformationMatrix.kZYX
    return -1


def stripNamespaceFromName(name):
    """Does what maya's om2.MNamespace.stripNamespaceFromName(name) was suppose to do.
    Autodesk results:

    .. code-block:: python

        name = u'|agagaa:NewNamespace1:joint1|agagaa:NewNamespace1:joint2|agagaa:NewNamespace1:joint3
        om2.MNamespace.stripNamespaceFromName(name)
        # 'joint3'
        generic.stripNamespaceFromName(name)
        # u'|joint1|joint2|joint3'

    :param name: the name to strip
    :type name: str
    :return: the name without the namespace while preserving the full path
    :rtype: str
    """
    return name.replace(om2.MNamespace.getNamespaceFromName(name).split("|")[-1] + ":", "")
