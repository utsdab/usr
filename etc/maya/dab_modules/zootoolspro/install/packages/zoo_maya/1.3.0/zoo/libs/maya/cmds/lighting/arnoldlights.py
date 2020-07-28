import maya.cmds as cmds

from zoo.libs.maya.cmds.lighting import lightingutils

ALLLIGHTTYPES = ["aiAreaLight", "aiSkyDomeLight"]
AREALIGHTS = ["aiAreaLight"]


def createArnoldDirectionalLight(name="directionalLight", samples=3):
    """Creates a Maya directional light, Arnold uses this as a directional light type

    :param name: the name of the light
    :type name: str
    :return lightTransformName: the name of the light (transform node)
    :rtype lightTransformName: str
    :return shapeNodeName: the name of the shape node
    :rtype shapeNodeName: str
    """
    lightTransformName, shapeNodeName = lightingutils.createLight(name, "directionalLight")
    # must connect to default light set
    cmds.connectAttr("{}.instObjGroups".format(lightTransformName), "defaultLightSet.dagSetMembers", nextAvailable=True)
    cmds.setAttr(".aiSamples".format(shapeNodeName), 3)
    return lightTransformName, shapeNodeName


def createArnoldPhysicalLight(name="aiAreaLight", fixSamples=True):
    """Creates a aiAreaLight

    :param name: the name of the light
    :type name: str
    :param fixSamples: Set the Arnold light samples to 4 rather than the default of 1
    :type fixSamples: bool
    :return lightTransformName: the name of the light (transform node)
    :rtype lightTransformName: str
    :return shapeNodeName: the name of the shape node
    :rtype shapeNodeName: str
    """
    lightTransformName, shapeNodeName = lightingutils.createLight(name, "aiAreaLight")
    # must connect to default light set in Arnold
    cmds.connectAttr("{}.instObjGroups".format(lightTransformName), "defaultLightSet.dagSetMembers", nextAvailable=True)
    if fixSamples:
        cmds.setAttr("{}.aiSamples".format(shapeNodeName), 4)
    return lightTransformName, shapeNodeName


def createArnoldSkydomeLight(name="aiSkyDomeLight", fixSamples=True):
    """Creates an IBL Skydome Light

    :param name: the name of the light
    :type name: str
    :param fixSamples: Set the Arnold light samples to 4 rather than the default of 1
    :type fixSamples: bool
    :return lightTransformName: the name of the light (transform node)
    :rtype lightTransformName: str
    :return shapeNodeName: the name of the shape node
    :rtype shapeNodeName: str
    """
    lightTransformName, shapeNodeName = lightingutils.createLight(name, "aiSkyDomeLight")
    # must connect to default light set
    cmds.connectAttr("{}.instObjGroups".format(lightTransformName), "defaultLightSet.dagSetMembers", nextAvailable=True)
    if fixSamples:
        cmds.setAttr("{}.aiSamples".format(shapeNodeName), 4)
    return lightTransformName, shapeNodeName


def getAllLightShapesInScene():
    """Returns any lights in the scene that may be in the global list ALLLIGHTTYPES

    :return allLightShapes: all the area lights in the scene as shapeNode names
    :rtype allLightShapes: list
    """
    return lightingutils.getAllLightShapesInScene(ALLLIGHTTYPES)


def getAllLightTransformsInScene():
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
    return lightingutils.filterAllLightTypesFromSelection(AREALIGHTS)

def deleteAllLights():
    """deletes all lights of types ALLLIGHTTYPES in the scene

    :return deletedLights: All the deleted light names
    :rtype deletedLights: list
    """
    return lightingutils.deleteAllLightTypes(ALLLIGHTTYPES)

