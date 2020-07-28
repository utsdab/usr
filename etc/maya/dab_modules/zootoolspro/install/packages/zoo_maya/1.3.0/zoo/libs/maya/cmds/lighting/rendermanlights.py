import maya.cmds as cmds

from zoo.libs.maya.cmds.lighting import lightingutils


AREALIGHTTYPES = ["PxrRectLight", "PxrSphereLight", "PxrDiskLight"]

DISTANT_LIGHT_TYPE = "PxrDistantLight"

ALLLIGHTTYPES = ["PxrRectLight", "PxrSphereLight", "PxrDiskLight", "PxrDistantLight", "PxrDomeLight"]

def getRendermanVersion():
    """Returns the version number of renderman if 22 or above.
    Returns 21.0 if below v22 will not be accurate to the version.
    Possibly could use old .mel but it's not important

    :return rendermanVersionNumber: The version number of Renderman, accurate above v22.0, otherwise is 21.0
    :rtype rendermanVersionNumber: float
    """
    try:  #rfm2.config doesn't exist in v21 so far as I know
        import rfm2
        return float(rfm2.config.cfg().build_info.version())
    except:  # not sure of the error type
        return 21.0


def createRendermanDirectionalLight(name="PxrDistantLight", normalize=True):
    """Creates a Renderman directional light

    :param name: the name of the light
    :type name: str
    :param name: Rendermans light should be normalized by default in most cases for normalize
    :type name: bool
    :return lightTransformName: the name of the light (transform node)
    :rtype lightTransformName: str
    :return shapeNodeName: the name of the shape node
    :rtype shapeNodeName: str
    """
    lightTransformName, shapeNodeName = lightingutils.createLight(name, "PxrDistantLight")
    # must connect to default light set
    cmds.connectAttr("{}.instObjGroups".format(lightTransformName), "defaultLightSet.dagSetMembers", nextAvailable=True)
    if normalize:  # normalize the light on
        cmds.setAttr("{}.areaNormalize".format(shapeNodeName), 1)
    return lightTransformName, shapeNodeName


def createRendermanPxrRectLight(name="PxrRectLight"):
    """Creates a PxrRectLight

    :param name: the name of the light
    :type name: str
    :return lightTransformName: the name of the light (transform node)
    :rtype lightTransformName: str
    :return shapeNodeName: the name of the shape node
    :rtype shapeNodeName: str
    """
    lightTransformName, shapeNodeName = lightingutils.createLight(name, "PxrRectLight")
    try:  # lights must switch off shading in v22
        cmds.setAttr("{}.overrideEnabled".format(shapeNodeName), 1)
        cmds.setAttr("{}.overrideShading".format(shapeNodeName), 0)
    except RuntimeError:  # attribute may not exist in lower versions (21 and lower)
        pass
    # must connect to default light set in Renderman
    cmds.connectAttr("{}.instObjGroups".format(lightTransformName), "defaultLightSet.dagSetMembers", nextAvailable=True)
    return lightTransformName, shapeNodeName


def createRendermanPxrSphereLight(name="PxrSphereLight"):
    """Creates a PxrSphereLight

    :param name: the name of the light
    :type name: str
    :return lightTransformName: the name of the light (transform node)
    :rtype lightTransformName: str
    :return shapeNodeName: the name of the shape node
    :rtype shapeNodeName: str
    """
    lightTransformName, shapeNodeName = lightingutils.createLight(name, "PxrSphereLight")
    try:  # lights must switch off shading in v22
        cmds.setAttr("{}.overrideEnabled".format(shapeNodeName), 1)
        cmds.setAttr("{}.overrideShading".format(shapeNodeName), 0)
    except RuntimeError:  # attribute may not exist in lower versions (21 and lower)
        pass
    # must connect to default light set in Arnold
    cmds.connectAttr("{}.instObjGroups".format(lightTransformName), "defaultLightSet.dagSetMembers", nextAvailable=True)
    return lightTransformName, shapeNodeName


def createRendermanPxrDiskLight(name="PxrDiskLight"):
    """Creates a PxrDiskLight

    :param name: the name of the light
    :type name: str
    :return lightTransformName: the name of the light (transform node)
    :rtype lightTransformName: str
    :return shapeNodeName: the name of the shape node
    :rtype shapeNodeName: str
    """
    lightTransformName, shapeNodeName = lightingutils.createLight(name, "PxrDiskLight")
    try:  # lights must switch off shading in v22
        cmds.setAttr("{}.overrideEnabled".format(shapeNodeName), 1)
        cmds.setAttr("{}.overrideShading".format(shapeNodeName), 0)
    except RuntimeError:  # attribute may not exist in lower versions (21 and lower)
        pass
    # must connect to default light set in Arnold
    cmds.connectAttr("{}.instObjGroups".format(lightTransformName), "defaultLightSet.dagSetMembers", nextAvailable=True)
    return lightTransformName, shapeNodeName


def createRendermanSkydomeLight(name="PxrDomeLight"):
    """Creates an IBL Skydome Light

    :param name: the name of the light
    :type name: str
    :return lightTransformName: the name of the light (transform node)
    :rtype lightTransformName: str
    :return shapeNodeName: the name of the shape node
    :rtype shapeNodeName: str
    """
    lightTransformName, shapeNodeName = lightingutils.createLight(name, "PxrDomeLight")
    # must connect to default light set
    cmds.connectAttr("{}.instObjGroups".format(lightTransformName), "defaultLightSet.dagSetMembers", nextAvailable=True)
    return lightTransformName, shapeNodeName


def getAllRendermanAreaLightsInScene():
    """Returns any lights in the scene that may be in the global list AREALIGHTTYPES
    "PxrRectLight", "PxrSphereLight", "PxrDiskLight"

    :return allLights: all the area lights in the scene as shapeNode names
    :rtype allLights: list
    """
    return lightingutils.getAllLightShapesInScene(AREALIGHTTYPES)


def getAllLightShapesInScene():
    """Returns any lights in the scene that may be in the global list ALLLIGHTTYPES

    :return allLightShapes: all the area lights in the scene as shapeNode names
    :rtype allLightShapes: list
    """
    return lightingutils.getAllLightShapesInScene(ALLLIGHTTYPES)


def getAllTransformsInScene():
    """Returns all the transforms of lights from ALLLIGHTTYPES in the scene

    :return lightsTransformList:
    :rtype lightsTransformList:
    """
    return lightingutils.getAllLightTransformsInScene(ALLLIGHTTYPES)


def filterAllAreaLightTypesFromSelection():
    """filters all the lights of types lightTypeList from the selected list

    :return lightsTransformList:  Light Name List of Transforms
    :rtype lightsTransformList: list
    """
    return lightingutils.filterAllLightTypesFromSelection(AREALIGHTTYPES)


def deleteAllLights():
    """deletes all lights of types ALLLIGHTTYPES in the scene

    :return deletedLights: All the deleted light names
    :rtype deletedLights: list
    """
    return lightingutils.deleteAllLightTypes(ALLLIGHTTYPES)