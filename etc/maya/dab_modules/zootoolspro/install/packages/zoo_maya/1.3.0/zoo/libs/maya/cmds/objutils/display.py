"""Various functions for displaying Maya objects

To Do
Have the selected functions work with bad selections and with hierarchy option too, should be in a UI

"""

import maya.cmds as cmds
import maya.api.OpenMaya as om2

from zoo.libs.maya.cmds.objutils import objhandling


def setPrimaryVisible(objList, value=True):
    """Sets all objects to primary visibility with a value of "value"

    :param objList: maya object names
    :type objList: list
    :param value: value of the attribute to be changed
    :type value: bool
    """
    for obj in objList:
        cmds.setAttr('{}.primaryVisibility'.format(obj), value)


def setDoubleSided(objList, value=True):
    """Sets all objects to double sided with a value of "value"

    :param objList: maya object names
    :type objList: list
    :param value: value of the attribute to be changed
    :type value: bool
    """
    for obj in objList:
        cmds.setAttr('{}.doubleSided'.format(obj), value)


def setCastShadows(objList, value=True):
    """Sets all objects to cast shadows with a value of "value"

    :param objList: maya object names
    :type objList: list
    :param value: value of the attribute to be changed
    :type value: bool
    """
    for obj in objList:
        cmds.setAttr('{}.castsShadows'.format(obj), value)


def setReceiveShadows(objList, value=True):
    """Sets all objects to receive shadows with a value of "value"

    :param objList: maya object names
    :type objList: list
    :param value: value of the attribute to be changed
    :type value: bool
    """
    for obj in objList:
        cmds.setAttr('{}.receiveShadows'.format(obj), value)


def setReflectionVisibility(objList, value=True):
    """Sets all objects reflection visibility with a value of "value"

    :param objList: maya object names
    :type objList: list
    :param value: value of the attribute to be changed
    :type value: bool
    """
    for obj in objList:
        cmds.setAttr('{}.visibleInReflections'.format(obj), value)

def setRefractionVisibility(objList, value=True):
    """Sets all objects refraction visibility with a value of "value"

    :param objList: maya object names
    :type objList: list
    :param value: value of the attribute to be changed
    :type value: bool
    """
    for obj in objList:
        cmds.setAttr('{}.visibleInRefractions'.format(obj), value)


def setPrimaryVisibleSelected(value=True):
    """Sets all selected objects to primary visibility with a value of "value"

    :param value: value of the attribute to be changed
    :type value: bool
    :return success: The function succeeded or failed
    :rtype success: bool
    """
    objList = cmds.ls(selection=True)
    if not objList:
        om2.MGlobal.displayWarning("No Objects Selected, Please Select And Run Again")
        return False
    setPrimaryVisible(objList, value=value)
    om2.MGlobal.displayInfo("Success: Objects Now Have Visibility of `{}` - `{}` ".format(value, objList))
    return True


def setDoubleSidedSelected(value=True):
    """Sets all selected objects to double sided with a value of "value"

    :param value: value of the attribute to be changed
    :type value: bool
    :return success: The function succeeded or failed
    :rtype success: bool
    """
    objList = cmds.ls(selection=True)
    if not objList:
        om2.MGlobal.displayWarning("No Objects Selected, Please Select And Run Again")
        return False
    setDoubleSided(objList, value=value)
    om2.MGlobal.displayInfo("Success: Objects Now Have DoubleSided set to `{}` - `{}` ".format(value, objList))
    return True


def setCastShadowsSelected(value=True):
    """Sets all selected objects to cast shadows with a value of "value"

    :param value: value of the attribute to be changed
    :type value: bool
    :return success: The function succeeded or failed
    :rtype success: bool
    """
    objList = cmds.ls(selection=True)
    if not objList:
        om2.MGlobal.displayWarning("No Objects Selected, Please Select And Run Again")
        return False
    setCastShadows(objList, value=value)
    om2.MGlobal.displayInfo("Success: Objects Now Have CastShadows set to `{}` - `{}` ".format(value, objList))
    return True


def setReceiveShadowsSelected(value=True):
    """Sets all selected objects to receive shadows with a value of "value"

    :param value: value of the attribute to be changed
    :type value: bool
    :return success: The function succeeded or failed
    :rtype success: bool
    """
    objList = cmds.ls(selection=True)
    if not objList:
        om2.MGlobal.displayWarning("No Objects Selected, Please Select And Run Again")
        return False
    setReceiveShadows(objList, value=value)
    om2.MGlobal.displayInfo("Success: Objects Now Have ReceiveShadows set to `{}` - `{}` ".format(value, objList))
    return True


def setHierarchyToRenderable(objList, value=True):
    """Sets the hierarchy below to be either renderable or not renderable depending on the value
    primary visibility, cast shadows, and receive shadows, reflections and refraction vis

    :param objList: maya object names
    :type objList: list
    :param value: value of the attribute to be changed
    :type value: bool
    :return meshList: The mesh names affected
    :rtype meshList: list
    """
    meshList = objhandling.getTypeTransformsHierarchy(objList, type="mesh")
    setPrimaryVisible(meshList, value=value)
    setCastShadows(meshList, value=value)
    setReceiveShadows(meshList, value=value)
    setReflectionVisibility(meshList, value=value)
    setRefractionVisibility(meshList, value=value)
    return meshList


def setHierarchyToPrimaryVis(objList, value=True):
    """Sets all objects in the hierarchy to primary visibility with a value of "value"

    :param objList: maya object names
    :type objList: list
    :param value: value of the attribute to be changed
    :type value: bool
    :return meshList: The mesh names affected
    :rtype meshList: list
    """
    meshList = objhandling.getTypeTransformsHierarchy(objList, type="mesh")
    setPrimaryVisible(meshList, value=value)
    return meshList


def setHierarchyToRenderableSelected(value=True):
    """Sets the selected hierarchy below to be either renderable or not renderable depending on the value
    primary visibility, cast shadows, and receive shadows

    :param value: value of the attribute to be changed
    :type value: bool
    :return success: The function succeeded or failed
    :rtype success: bool
    """
    objList = cmds.ls(selection=True)
    if not objList:
        om2.MGlobal.displayWarning("No Objects Selected, Please Select And Run Again")
        return False
    meshList = setHierarchyToRenderable(objList, value=value)
    if not meshList:
        om2.MGlobal.displayWarning("No Objects Found To Affect")
        return False
    meshListLength = len(meshList)
    om2.MGlobal.displayInfo("Objects All Renderable Attributes "
                            "set to `{}` - `{}` ".format(value, meshList))
    om2.MGlobal.displayInfo("Success: Objects Now Have All Renderable Attributes "
                            "set to `{}` - `{}` ".format(value, meshListLength))
    return True


def setHierarchyToPrimaryVisSelected(value=True):
    """Sets all selected objects in the hierarchy to primary visibility with a value of "value"

    :param value: value of the attribute to be changed
    :type value: bool
    :return success: The function succeeded or failed
    :rtype success: bool
    """
    objList = cmds.ls(selection=True)
    if not objList:
        om2.MGlobal.displayWarning("No Objects Selected, Please Select And Run Again")
        return False
    meshList = setHierarchyToPrimaryVis(objList, value=value)
    if not meshList:
        om2.MGlobal.displayWarning("No Objects Found To Affect")
        return False
    meshListLength = len(meshList)
    om2.MGlobal.displayInfo("Objects Primary Visibility "
                            "set to `{}` - `{}` ".format(value, meshList))
    om2.MGlobal.displayInfo("Success: Objects Now Have Primary Visibility set to `{}` "
                            "on {} objects".format(value, meshListLength))
    return True

