import maya.cmds as cmds

from zoo.libs.maya.cmds.lighting import lightingutils

ALLLIGHTTYPES = ["RedshiftPhysicalLight", "RedshiftDomeLight"]
AREALIGHTS = ["RedshiftPhysicalLight"]


def createRedshiftDirectionalLight(name="directionalLight"):
    """Creates a Maya directional light, Redshift uses this as a directional light type

    :param name: the name of the light
    :type name: str
    :return lightTransformName: the name of the light (transform node)
    :rtype lightTransformName: str
    :return shapeNodeName: the name of the shape node
    :rtype shapeNodeName: str
    """
    lightTransformName, shapeNodeName = createRedshiftPhysicalLight(name)
    # redshift directional is just a rsPhysicalLight with the lightType attribute switched, so switch it
    cmds.setAttr("{}.lightType".format(shapeNodeName), 3)
    return lightTransformName, shapeNodeName


def createRedshiftPhysicalLight(name="rsPhysicalLight"):
    """Creates a RedshiftPhysicalLight

    :param name: the name of the light
    :type name: str
    :return lightTransformName: the name of the light (transform node)
    :rtype lightTransformName: str
    :return shapeNodeName: the name of the shape node
    :rtype shapeNodeName: str
    """
    lightTransformName, shapeNodeName = lightingutils.createLight(name, "RedshiftPhysicalLight")
    # must connect to default light set
    cmds.connectAttr("{}.instObjGroups".format(lightTransformName), "defaultLightSet.dagSetMembers", nextAvailable=True)
    return lightTransformName, shapeNodeName


def createRedshiftSkydomeLight(name="RedshiftDomeLight"):
    """Creates an IBL Skydome Light

    :param name: the name of the light
    :type name: str
    :return lightTransformName: the name of the light (transform node)
    :rtype lightTransformName: str
    :return shapeNodeName: the name of the shape node
    :rtype shapeNodeName: str
    """
    lightTransformName, shapeNodeName = lightingutils.createLight(name, "RedshiftDomeLight")
    # must connect to default light set
    cmds.connectAttr("{}.instObjGroups".format(lightTransformName), "defaultLightSet.dagSetMembers", nextAvailable=True)
    return lightTransformName, shapeNodeName


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
    # note this also returns directional lights too
    areaLights = lightingutils.filterAllLightTypesFromSelection(AREALIGHTS)
    return areaLights


def deleteAllLights():
    """deletes all lights of types ALLLIGHTTYPES in the scene

    :return deletedLights: All the deleted light names
    :rtype deletedLights: list
    """
    return lightingutils.deleteAllLightTypes(ALLLIGHTTYPES)

