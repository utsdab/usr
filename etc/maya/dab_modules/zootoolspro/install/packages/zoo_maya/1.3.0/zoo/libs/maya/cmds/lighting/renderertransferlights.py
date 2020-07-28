"""TO DO
- filter check should check the type of light, directional, ibl, or area
"""
import json
import os

import maya.api.OpenMaya as om2
import maya.cmds as cmds

from zoo.libs.maya.cmds.objutils import attributes, namehandling, shapenodes, objhandling, matching, scaleutils
from zoo.libs.maya.cmds.lighting import redshiftlights, arnoldlights, rendermanlights, lightingutils
from zoo.libs.maya.cmds.cameras import cameras
from zoo.libs.maya.cmds.renderer import rendererload, exportglobals
from zoo.libs.maya.cmds.renderer.rendererconstants import RENDERER_SUFFIX, RENDERER_SUFFIX_DICT
from zoo.libs.maya.cmds.shaders import textures
from zoo.libs.utils import colour

# default keys for the generic light dicts
INTENSITY = 'gIntensity'
EXPOSURE = 'gExposure'
LIGHTCOLOR = 'gLightColor_srgb'
TEMPERATURE = 'gTemperature'
TEMPONOFF = "gTempOnOff"
NORMALIZE = 'gNormalize'
SHAPE = 'gShape_shape'
LIGHTVISIBILITY = 'gLightVisibility'
SCALE = 'gScale'
ANGLE_SOFT = "gAngleSoft"

ROTATE = 'gRotate'
TRANSLATE = 'gTranslate'
IBLTEXTURE = 'gIblTexture'

RENDERERTAGATTRIBUTE = "rendererC3dC"

SRGBSUFFIX = '_srgb'

LOCGRPNAME = exportglobals.LOCGRPNAME  # "lightMatchLocs_grp"
LIGHTGRPNAME = exportglobals.LIGHTGRPNAME  # "Lights_grp" the base group that the lights are automatically built inside

REDSHIFT = exportglobals.REDSHIFT  # "Redshift"
RENDERMAN = exportglobals.RENDERMAN
ARNOLD = exportglobals.ARNOLD
GENERIC = exportglobals.GENERIC

AREALIGHTS = exportglobals.AREALIGHTS
IBLSKYDOMES = exportglobals.IBLSKYDOMES
DIRECTIONALS = exportglobals.DIRECTIONALS

SHAPE_ATTR_ENUM_LIST = lightingutils.SHAPE_ATTR_ENUM_LIST
SHAPE_ATTR_ENUM_LIST_NICE = lightingutils.SHAPE_ATTR_ENUM_LIST_NICE

# note Renderman has more than one light type for other shapes
RENDERERAREALIGHTS = {REDSHIFT: "RedshiftPhysicalLight",
                      RENDERMAN: rendermanlights.AREALIGHTTYPES,
                      ARNOLD: "aiAreaLight"}

RENDERERDIRECTIONALLIGHTS = {REDSHIFT: "RedshiftPhysicalLight",
                             RENDERMAN: "PxrDistantLight",
                             ARNOLD: "directionalLight"}

RENDERERSKYDOMELIGHTS = {REDSHIFT: "RedshiftDomeLight",
                         RENDERMAN: "PxrDomeLight",
                         ARNOLD: "aiSkyDomeLight"}

RENDERER_SUFFIX["Generic"] = "lgtLc"

# --------------------
# Area Light dict keys
# --------------------
GENERICLIGHTATTRDICT = {INTENSITY: "intensity",
                        EXPOSURE: "exposure",
                        LIGHTCOLOR: "color",
                        TEMPERATURE: "temperature",
                        TEMPONOFF: "tempOnOff",
                        NORMALIZE: "normalize",
                        SHAPE: "areaShape",
                        LIGHTVISIBILITY: "lightVis"}

# arnold requires a special use of code for changing the light type (aiTranslator)
# arnold does not have a light visibility switch (show the lights as white etc) in older versions
ARNOLDLIGHTATTRDICT = {INTENSITY: "intensity",
                       EXPOSURE: "exposure",
                       LIGHTCOLOR: "color",
                       TEMPERATURE: "aiColorTemperature",
                       TEMPONOFF: "aiUseColorTemperature",
                       NORMALIZE: "aiNormalize",
                       SHAPE: "aiTranslator",
                       LIGHTVISIBILITY: "aiCamera"}

# set Redshift attribute keys, Redshift has no exposure in older versions
REDSHIFTLIGHTATTRDICT = {INTENSITY: "intensity",
                         EXPOSURE: "exposure",
                         LIGHTCOLOR: "color",
                         TEMPERATURE: "temperature",
                         TEMPONOFF: "colorMode",
                         NORMALIZE: "normalize",
                         SHAPE: "areaShape",
                         LIGHTVISIBILITY: "areaVisibleInRender"}

# Renderman area light shapes are separate light types
# in v21 is "primaryVisibility" is "rman__riattr__visibility_camera", is fixed in the code, which recreates the lights
RENDERMANLIGHTATTRDICT = {INTENSITY: "intensity",
                          EXPOSURE: "exposure",
                          LIGHTCOLOR: "lightColor",
                          TEMPERATURE: "temperature",
                          TEMPONOFF: "enableTemperature",
                          NORMALIZE: "areaNormalize",
                          SHAPE: None,
                          LIGHTVISIBILITY: "primaryVisibility"}

# --------------------
# Directional Light dict keys
# --------------------

GENERIC_DIRECTIONAL_ATTR_DICT = {INTENSITY: "intensity",
                                 LIGHTCOLOR: "color",
                                 TEMPERATURE: "temperature",
                                 TEMPONOFF: "tempOnOff",
                                 ANGLE_SOFT: "angleSoft"}

ARNOLD_DIRECTIONAL_ATTR_DICT = {INTENSITY: "intensity",
                                LIGHTCOLOR: "color",
                                TEMPERATURE: "aiColorTemperature",
                                TEMPONOFF: "aiUseColorTemperature",
                                ANGLE_SOFT: "aiAngle"}

REDSHIFT_DIRECTIONAL_ATTR_DICT = {INTENSITY: "intensity",
                                  LIGHTCOLOR: "color",
                                  TEMPERATURE: "temperature",
                                  TEMPONOFF: "colorMode",
                                  ANGLE_SOFT: "SAMPLINGOVERRIDES_shadowSamplesScale"}

RENDERMAN_DIRECTIONAL_ATTR_DICT = {INTENSITY: "intensity",
                                   LIGHTCOLOR: "lightColor",
                                   TEMPERATURE: "temperature",
                                   TEMPONOFF: "enableTemperature",
                                   ANGLE_SOFT: "angleExtent"}

# --------------------
# IBL Light dict keys
# --------------------

GENERICSKYDOMEATTRDICT = {INTENSITY: "intensity",
                          EXPOSURE: "exposure",
                          LIGHTCOLOR: "color",
                          TEMPERATURE: "temperature",
                          TEMPONOFF: "tempOnOff",
                          NORMALIZE: "normalize",
                          SHAPE: "areaShape",
                          LIGHTVISIBILITY: "lightVis",
                          IBLTEXTURE: "IblTexturePath"}

# TODO Redshift IBLs does have exposure called "exposure0" in newer versions should check?
REDSHIFTSKYDOMEATTRDICT = {INTENSITY: "color",
                           EXPOSURE: None,
                           LIGHTCOLOR: "color",
                           LIGHTVISIBILITY: "background_enable",
                           IBLTEXTURE: "tex0"}

# Renderman IBL
# in v21 is "primaryVisibility" is "rman__riattr__visibility_camera", is fixed in the code
RENDERMANSKYDOMEATTRDICT = {INTENSITY: "intensity",
                            EXPOSURE: "exposure",
                            LIGHTCOLOR: "lightColor",
                            LIGHTVISIBILITY: "primaryVisibility",
                            IBLTEXTURE: "lightColorMap"}

# Arnold's skydomes do have a visibilty slider attr and the texture needs to be mapped to a texture node
ARNOLDSKYDOMEATTRDICT = {INTENSITY: "intensity",
                         EXPOSURE: "exposure",
                         LIGHTCOLOR: "color",
                         LIGHTVISIBILITY: "camera",
                         IBLTEXTURE: "color"}

"""
MISC
"""


def rotateObjectSpaceXForm(obj, rotation):
    """Rotate object based on local position, ie rotate from current position, xform offset ignore gimbal

    Used for Redshift cylinder which is rotated 90, needs to also account while pulling tht info too

    :param matchObj: object to match will change
    :type matchObj: str
    :param targetObj: the target object doesn't move
    :type targetObj: str
    :param rotation: tuple in degrees (0, 0, 90)
    :type rotation: tuple
    """
    cmds.xform(obj, rotation=rotation, objectSpace=True, relative=True)


"""
LIGHT DICT SIMPLE
"""


def getLightDictAttributes():
    lightApplyAttrDict = {INTENSITY: None,
                          EXPOSURE: None,
                          LIGHTCOLOR: None,
                          TEMPERATURE: None,
                          TEMPONOFF: None,
                          NORMALIZE: None,
                          SHAPE: None,
                          LIGHTVISIBILITY: None,
                          SCALE: None}
    return lightApplyAttrDict


def getDirectionalDictAttributes():
    lightApplyAttrDict = {INTENSITY: None,
                          LIGHTCOLOR: None,
                          TEMPERATURE: None,
                          TEMPONOFF: None,
                          ANGLE_SOFT: None}
    return lightApplyAttrDict


def getSkydomeLightDictAttributes():
    lightApplyAttrDict = {INTENSITY: None,
                          EXPOSURE: None,
                          LIGHTCOLOR: None,
                          LIGHTVISIBILITY: None,
                          IBLTEXTURE: None,
                          ROTATE: None,
                          TRANSLATE: None,
                          SCALE: None}
    return lightApplyAttrDict


def getRendererAttrDict(rendererNiceName):
    """Returns the correct attribute generic dict for the given renderer for area lights

    :param rendererNiceName: the renderer nice name "Redshift", "Arnold", "Renderman"
    :type rendererNiceName: str
    :return attrDict: the attribute dictionary of the appropriate renderer
    :rtype attrDict: dict
    """
    attrDict = dict()
    if rendererNiceName == REDSHIFT:
        attrDict = REDSHIFTLIGHTATTRDICT
    elif rendererNiceName == ARNOLD:
        attrDict = ARNOLDLIGHTATTRDICT
    elif rendererNiceName == RENDERMAN:
        attrDict = RENDERMANLIGHTATTRDICT
    elif rendererNiceName == GENERIC:
        attrDict = GENERICLIGHTATTRDICT
    return attrDict


def getRendererDirectionalAttrDict(rendererNiceName):
    """Returns the correct attribute generic dict for the given renderer for area lights

    :param rendererNiceName: the renderer nice name "Redshift", "Arnold", "Renderman"
    :type rendererNiceName: str
    :return attrDict: the attribute dictionary of the appropriate renderer
    :rtype attrDict: dict
    """
    attrDict = dict()
    if rendererNiceName == REDSHIFT:
        attrDict = REDSHIFT_DIRECTIONAL_ATTR_DICT
    elif rendererNiceName == ARNOLD:
        attrDict = ARNOLD_DIRECTIONAL_ATTR_DICT
    elif rendererNiceName == RENDERMAN:
        attrDict = RENDERMAN_DIRECTIONAL_ATTR_DICT
    elif rendererNiceName == GENERIC:
        attrDict = GENERIC_DIRECTIONAL_ATTR_DICT
    return attrDict


def getRendererAttrDictSkydome(rendererNiceName):
    """Returns the correct attribute dict for the given renderer for area lights

    :param rendererNiceName: the renderer nice name "Redshift", "Arnold", "Renderman"
    :type rendererNiceName: str
    :return attrDict: the attribute dictionary of the appropriate renderer
    :rtype attrDict: dict
    """
    attrDict = dict()
    if rendererNiceName == REDSHIFT:
        attrDict = REDSHIFTSKYDOMEATTRDICT
    elif rendererNiceName == ARNOLD:
        attrDict = ARNOLDSKYDOMEATTRDICT
    elif rendererNiceName == RENDERMAN:
        attrDict = RENDERMANSKYDOMEATTRDICT
    elif rendererNiceName == GENERIC:
        attrDict = GENERICSKYDOMEATTRDICT
    return attrDict


"""
SIMPLE RETRIEVE
"""


def checkAreaShape(node):
    """Returns the name if it is a directional light node type (any renderer), returns None if not.

    :param node: any Maya node name
    :type node: str
    :return directionalShape: will return a str if it's a directional light shape node, None if not
    :rtype directionalShape: str
    """
    objType = cmds.objectType(node)
    # directionals
    if objType == RENDERERAREALIGHTS[REDSHIFT]:  # "RedshiftPhysicalLight"
        return node
    elif objType == RENDERERAREALIGHTS[ARNOLD]:  # aiAreaLight
        return node
    else:
        for lightType in RENDERERAREALIGHTS[RENDERMAN]:  # Could be three lights
            if objType == lightType:
                return node
    return None


def getLightShape(lightTransform, lightFamily="All"):
    """Returns a single light shape, checks if it is a light from the type dict
    RENDERERAREALIGHTS and RENDERERDIRECTIONALLIGHTS

    :param lightTransform: the light transform name
    :type lightTransform: str
    :return shape: The light shape name, None if not found
    :rtype shape: str
    """
    shapes = cmds.listRelatives(lightTransform, fullPath=True)
    if not shapes:
        return None
    for shape in shapes:
        if lightFamily == AREALIGHTS or lightFamily == "All":  # area lights
            objType = cmds.objectType(shape)
            if objType == RENDERERAREALIGHTS[REDSHIFT]:  # "RedshiftPhysicalLight"
                return shape
            elif objType == RENDERERAREALIGHTS[ARNOLD]:  # aiAreaLight
                return shape
            else:
                for lightType in RENDERERAREALIGHTS[RENDERMAN]:  # Could be three lights
                    if objType == lightType:
                        return shape
        if lightFamily == DIRECTIONALS or lightFamily == "All":  # directional lights
            for renderer in RENDERERDIRECTIONALLIGHTS:
                if objType == RENDERERDIRECTIONALLIGHTS[renderer]:
                    return shape
        # IBL lights
        if lightFamily == IBLSKYDOMES or lightFamily == "All":  # directional lights
            for renderer in RENDERERSKYDOMELIGHTS:
                if objType == RENDERERSKYDOMELIGHTS[renderer]:
                    return shape
        return None


def findFirstAreaLight(nodeList, lightFamily=AREALIGHTS):
    """Returns the first light found in a list, usually for GUI displays.

    Light family can be AREALIGHTS, DIRECTIONALS, or "All"

    :param nodeList: list of Maya nodes, can be shapes or transforms, any nodes
    :type nodeList: list
    :return directionalListFound: the name of the first directional light found, None if none found
    :rtype directionalListFound: str
    """
    obj = None
    for obj in nodeList:  # check to find the first directional light
        if cmds.objectType(obj) == "transform":  # transform so get the shape
            shape = getLightShape(obj, lightFamily=AREALIGHTS)  # returns None if not
            if not shape:  # is not a directional
                obj = None
        else:  # could be a shape node
            obj = checkAreaShape(obj)  # will be None if not a area light node
        if obj:
            break
    return obj


def getLightShapeList(transformList):
    """takes a transform list and returns valid light shapes, Renderman Redshift Arnold etc

    :param transformList: list of Maya transforms
    :type transformList: list
    :return lightShapeList: a list of light shapes
    :rtype lightShapeList: list
    """
    lightShapeList = list()
    for transform in transformList:
        lightShape = getLightShape(transform)
        if lightShape:
            lightShapeList.append(lightShape)
    return lightShapeList


def getIblShape(lightTransform):
    """Gets the light shape, checks if it is a light from the type dict

    :param lightTransform: the light transform name
    :type lightTransform: str
    :return shape: The light shape name, None if not found
    :rtype shape: str
    """
    shapes = cmds.listRelatives(lightTransform, fullPath=True)
    if not shapes:
        return None
    for shape in shapes:
        objType = cmds.objectType(shape)
        for renderer in RENDERERSKYDOMELIGHTS:  # check shape skydome light
            if objType == RENDERERSKYDOMELIGHTS[renderer]:
                return shape
    return None


def getIblShapeList(iblTransformList):
    iblShapeList = list()
    for iblTransform in iblTransformList:
        lightShape = getIblShape(iblTransform)
        if lightShape:
            iblShapeList.append(lightShape)
    return iblShapeList


def findFirstDirectionalLight(nodeList, rendererNiceName=None):
    """Returns the first directional light found in a list, for GUI displays.

    :param nodeList: list of Maya nodes, can be shapes or transforms, any nodes
    :type nodeList: list
    :return directionalListFound: the name of the first directional light found, None if none found
    :rtype directionalListFound: str
    """
    obj = None
    for obj in nodeList:  # check to find the first directional light
        if cmds.objectType(obj) == "transform":  # transform so get the shape
            shape = getDirectionalShape(obj, rendererNiceName=rendererNiceName)  # returns None if not
            if not shape:  # is not a directional
                obj = None
        else:  # could be a shape node
            obj = checkDirectionalShape(obj,
                                        rendererNiceName=rendererNiceName)  # will be None if not a directional light node
        if obj:
            break
    return obj


def checkDirectionalShape(node, rendererNiceName=None):
    """Returns the name if it is a directional light node type (any renderer), returns None if not.

    :param node: any Maya node name
    :type node: str
    :return directionalShape: will return a str if it's a directional light shape node, None if not
    :rtype directionalShape: str
    """
    objType = cmds.objectType(node)
    # directionals
    if rendererNiceName:
        if objType == RENDERERDIRECTIONALLIGHTS[rendererNiceName]:
            return node
    else:
        for renderer in RENDERERDIRECTIONALLIGHTS:
            if objType == RENDERERDIRECTIONALLIGHTS[renderer]:
                return node
    return None


def getDirectionalShape(lightTransform, rendererNiceName=None):
    """Gets the light shape, checks if it is a ldirectionlal ight from the type dict

    :param lightTransform: the light transform name
    :type lightTransform: str
    :return shape: The light shape name, None if not found
    :rtype shape: str
    """
    nodes = cmds.listRelatives(lightTransform, fullPath=True)
    if not nodes:  # probably a group
        return None
    for node in nodes:
        directionalShapeName = checkDirectionalShape(node, rendererNiceName=rendererNiceName)
        if directionalShapeName:
            return directionalShapeName
    return None


def getDirectionalShapeList(directionalTransformList):
    directionalShapeList = list()
    for directionalTransform in directionalTransformList:
        lightShape = getDirectionalShape(directionalTransform)
        if lightShape:
            directionalShapeList.append(lightShape)
    return directionalShapeList


def getRendererNiceNameFromLightShape(shapeNode):
    """From a shape node, light shape return the nice name of the current renderer
    Directional lights are tricky because can be Redshift or Arnold. The light create UI adds a attribute on creation
    which tells what renderer it was created in, but easily possible for a directional light not to have this if
    created from the menus.

    :param shapeNode: light shape node name
    :type shapeNode: str
    :return rendererNiceName: nice name of the renderer, "Redshift", "Arnold" etc
    :rtype rendererNiceName: str
    """
    objType = cmds.objectType(shapeNode)
    # check area lights
    if objType == RENDERERAREALIGHTS[REDSHIFT]:  # "RedshiftPhysicalLight"
        if cmds.getAttr("{}.lightType".format(shapeNode)) == 0:  # then is area light
            return REDSHIFT
    elif objType == RENDERERAREALIGHTS[ARNOLD]:  # aiAreaLight
        return ARNOLD
    for lightType in RENDERERAREALIGHTS[RENDERMAN]:  # Could be three lights
        if objType == lightType:
            return RENDERMAN
    for renderer in RENDERERDIRECTIONALLIGHTS:
        # directional lights
        if objType == RENDERERDIRECTIONALLIGHTS[renderer]:
            if renderer == REDSHIFT:  # check redshift area light as could be an area light
                if cmds.getAttr("{}.lightType".format(shapeNode)) == 3:  # then is directional light
                    return renderer
            else:  # other renderers are cool
                return renderer
        # skydome lights
        if objType == RENDERERSKYDOMELIGHTS[renderer]:
            return renderer
    if objType == "directionalLight":  # final check of directional, can't find special C3dC attribute
        om2.MGlobal.displayWarning("Light Shape shapeNode is a directionalLight, and can't determine the "
                                   "renderer, defaulting to Arnold XX")
        return ARNOLD


def getRendererNiceNameFromLightTransfrom(transformNode):
    """From a transform node, return the nice name of the current renderer
    Directional lights are tricky because can be Redshift or Arnold. The light create UI adds a attribute on creation
    which tells what renderer it was created in, but easily possible for a directional light not to have this if
    created from the menus.

    :param transformNode: a light transform node
    :type transformNode: str
    :return rendererNiceName: nice name of the renderer, "Redshift", "Arnold" etc
    :rtype rendererNiceName: str
    """
    shapeNode = cmds.listRelatives(transformNode, shapes=True, fullPath=True)[0]
    return getRendererNiceNameFromLightShape(shapeNode)


"""
SET/CONVERT EXPOSURE INTENSITY
"""


def setIntensityExposure(shapeNode, intensityVal, exposureVal):
    """Sets the intensity and exposure on an area light

    Note: older versions of Redshift have no exposure so this accounts for auto detecting if exposure exists

    :param shapeNode: The light shape node
    :type shapeNode: str
    :param intensityVal: The current intensity of the light
    :type intensityVal: float
    :param exposureVal: The current exposre of the light
    :type exposureVal: float
    :return intensityVal: the applied intensity value, generally unchanged
    :rtype intensityVal: float
    :return exposureVal: The applied exposure value, generally unchanged
    :rtype exposureVal: float
    """
    rendererNiceName = getRendererNiceNameFromLightShape(shapeNode)
    attrDict = getRendererAttrDict(rendererNiceName)
    if rendererNiceName == REDSHIFT:
        if not redshiftAreaExposureExists(shapeNode, attrDict):  # then Redshift exposure doesn't exist
            intensityVal, exposureVal = lightingutils.convertExpAndIntToIntensity(intensityVal, exposureVal)
            cmds.setAttr(".".join([shapeNode, attrDict[INTENSITY]]), intensityVal)
            shapeUnique = namehandling.getUniqueShortName(shapeNode)
            om2.MGlobal.displayInfo("Light `{}` Set To Intensity: `{}`".format(shapeUnique, intensityVal))
            return intensityVal, exposureVal
    # all clear set attributes with regular attr names
    cmds.setAttr(".".join([shapeNode, attrDict[EXPOSURE]]), exposureVal)
    cmds.setAttr(".".join([shapeNode, attrDict[INTENSITY]]), intensityVal)
    shapeUnique = namehandling.getUniqueShortName(shapeNode)
    om2.MGlobal.displayInfo("Light `{}` Set To Intensity: `{}`, "
                            "Exposure `{}` ".format(shapeUnique, intensityVal, exposureVal))
    return intensityVal, exposureVal


def setIntensityExposureSelected(intensityVal, exposureVal):
    """Sets the intensity and exposure on selected lights
    Redshift only has intensity so this function converts so that the intensity is correctly applied with exposure

    :param intensityVal: The current intensity of the light
    :type intensityVal: float
    :param exposureVal: The current exposre of the light
    :type exposureVal: float
    """
    selObj = cmds.ls(selection=True, long=True)
    for transform in (selObj):
        lightShape = getLightShape(transform)
        if lightShape:  # may not be a light if not will be None
            setIntensityExposure(lightShape, intensityVal, exposureVal)


def convertApplyExposure(shapeNode, intensityVal, exposureVal):
    """Converts the intensity of a light to exposure. Exposure is calulated as 2**exposure (2 to the power of exposure)

    Note: Intensity will always be 1 except in old versions of Redshift where exposure did not exist

    :param shapeNode: The light shape node
    :type shapeNode: str
    :param intensityVal: The current intensity of the light
    :type intensityVal: float
    :param exposureVal: The current exposre of the light
    :type exposureVal: float
    :return intensityVal: the intensity value will usually be 1 except if the renderer is redshift
    :rtype intensityVal: float
    :return exposureVal: The new exposure value
    :rtype exposureVal: float
    """
    intensityVal, exposureVal = lightingutils.convertExpAndIntToExposure(intensityVal, exposureVal)
    rendererNiceName = getRendererNiceNameFromLightShape(shapeNode)
    attrDict = getRendererAttrDict(rendererNiceName)
    if rendererNiceName == REDSHIFT:
        if not redshiftAreaExposureExists(shapeNode, attrDict):  # then Redshift exposure doesn't exist
            intensityVal, exposureVal = lightingutils.convertExpAndIntToIntensity(intensityVal, exposureVal)
            cmds.setAttr(".".join([shapeNode, attrDict[INTENSITY]]), intensityVal)
            shapeUnique = namehandling.getUniqueShortName(shapeNode)
            om2.MGlobal.displayInfo("Redshift Light `{}` Set As Intensity Not Exposure.  "
                                    "Intensity set: {}".format(shapeUnique, intensityVal))
            return intensityVal, exposureVal
    # all clear set attributes with regular attr names
    cmds.setAttr(".".join([shapeNode, attrDict[EXPOSURE]]), exposureVal)
    cmds.setAttr(".".join([shapeNode, attrDict[INTENSITY]]), intensityVal)
    shapeUnique = namehandling.getUniqueShortName(shapeNode)
    om2.MGlobal.displayInfo("Light `{}` Set To Exposure: {}".format(shapeUnique, exposureVal))
    return intensityVal, exposureVal


def convertApplyIntensity(shapeNode, intensityVal, exposureVal):
    """Converts the intensity of a light's exposure and intensity attributes to be pure intensity with a value of 0 for
    Exposure. Exposure doesn't exist on Redshift lights so will always apply
    as intensity. Exposure is calulated as 2**exposure (2 to the power of exposure)
    Exposure will always be 0

    :param shapeNode: The light shape node
    :type shapeNode: str
    :param intensityVal: The current intensity of the light
    :type intensityVal: float
    :param exposureVal: The current exposre of the light
    :type exposureVal: float
    :return intensityVal: the applied intensity value, exposure is always set to zero
    :rtype intensityVal:
    """
    rendererNiceName = getRendererNiceNameFromLightShape(shapeNode)
    attrDict = getRendererAttrDict(rendererNiceName)
    intensityVal, exposureVal = lightingutils.convertExpAndIntToIntensity(intensityVal, exposureVal)
    cmds.setAttr(".".join([shapeNode, attrDict[INTENSITY]]), intensityVal)
    shapeUnique = namehandling.getUniqueShortName(shapeNode)
    om2.MGlobal.displayInfo("Light `{}` Set To Intensity: {}".format(shapeUnique, intensityVal))
    if rendererNiceName == REDSHIFT:
        if not redshiftAreaExposureExists(shapeNode, attrDict):  # then Redshift exposure doesn't exist
            return intensityVal
    cmds.setAttr(".".join([shapeNode, attrDict[EXPOSURE]]), exposureVal)
    return intensityVal


def convertApplyExposureSelected(intensityVal, exposureVal):
    """Converts the intensity of a light's exposure and intensity attributes to be pure intensity with a value of 0 for
    Exposure. For selected lights

    Exposure doesn't exist on Redshift lights so will always apply  as intensity. Exposure is calulated as 2**exposure
    (2 to the power of exposure)  Exposure will always be 0

    :param shapeNode: The light shape node
    :type shapeNode: str
    :param intensityVal: The current intensity of the light
    :type intensityVal: float
    :param exposureVal: The current exposre of the light
    :type exposureVal: float
    :return intensityVal: the applied intensity value, exposure is always set to zero
    :rtype intensityVal:
    """
    selObj = cmds.ls(selection=True, long=True)
    for transform in (selObj):
        lightShape = getLightShape(transform)
        if lightShape:  # may not be a light if not will be None
            convertApplyExposure(lightShape, intensityVal, exposureVal)


def convertApplyIntensitySelected(intensityVal, exposureVal):
    """Converts the intensity/exposure of a light to be pure exposure with a value of 1 for intensity for selected
    lights.  Exposure is set as zero except with Redshift which has no attribute for exposure


    :param shapeNode: The light shape node
    :type shapeNode: str
    :param intensityVal: The current intensity of the light
    :type intensityVal: float
    :param exposureVal: The current exposre of the light
    :type exposureVal: float
    """
    selObj = cmds.ls(selection=True, long=True)
    for transform in (selObj):
        lightShape = getLightShape(transform)
        if lightShape:  # may not be a light if not will be None
            convertApplyIntensity(lightShape, intensityVal, exposureVal)


def convertToExposureRenderer(rendererNiceName, shapeNode):
    """Converts exposure and intensity to be pure exposure (with intensity set to 1)
    Will not work on Redshift as it doesn't have exposure right now

    :param rendererNiceName: the renderer nice name "Arnold", "Renderman"
    :type rendererNiceName: str
    :param shapeNode: the lights shape node name
    :type shapeNode: str
    """
    attrDict = getRendererAttrDict(rendererNiceName)
    intensityVal = cmds.getAttr(".".join([shapeNode, attrDict[INTENSITY]]))
    exposureVal = cmds.getAttr(".".join([shapeNode, attrDict[EXPOSURE]]))
    intensityVal, exposureVal = lightingutils.convertExpAndIntToExposure(intensityVal, exposureVal)
    cmds.setAttr(".".join([shapeNode, attrDict[INTENSITY]]), intensityVal)
    cmds.setAttr(".".join([shapeNode, attrDict[EXPOSURE]]).format(shapeNode), exposureVal)
    return intensityVal, exposureVal


def convertToIntensityRenderer(rendererNiceName, shapeNode):
    """Converts exposure and intensity to be pure intensity (with intensity set to 0)
    Will not work on Redshift as it doesn't have exposure right now

    :param rendererNiceName: the renderer nice name "Redshift", "Arnold", "Renderman"
    :type rendererNiceName: str
    :param shapeNode: the lights shape node name
    :type shapeNode: str
    """
    attrDict = getRendererAttrDict(rendererNiceName)
    intensityVal = cmds.getAttr(".".join([shapeNode, attrDict[INTENSITY]]))
    exposureVal = cmds.getAttr(".".join([shapeNode, attrDict[EXPOSURE]]))
    intensityVal, exposureVal = lightingutils.convertExpAndIntToIntensity(intensityVal, exposureVal)
    cmds.setAttr(".".join([shapeNode, attrDict[EXPOSURE]]), exposureVal)
    cmds.setAttr(".".join([shapeNode, attrDict[INTENSITY]]).format(shapeNode), intensityVal)


"""
CHECK VALID LIGHTS
"""


def checkValidLightType(lightShape, filterDirectionalOnly=False):
    """Check to see if the light shape is a valid area light or directional or ibl
    Checks from three dicts
    RENDERERAREALIGHTS, RENDERERDIRECTIONALLIGHTS, RENDERERDIRECTIONALLIGHTS

    :param lightShape: The light shape node
    :type lightShape: str
    :return validity: True if the light is recognised, False if not
    :rtype: bool
    """
    lightType = cmds.nodeType(lightShape)
    if lightType == RENDERERAREALIGHTS[ARNOLD]:
        return True
    elif lightType == RENDERERAREALIGHTS[REDSHIFT]:
        return True
    for lightTypeRenderman in RENDERERAREALIGHTS[RENDERMAN]:  # Could be three lights
        if lightType == lightTypeRenderman:
            return True
    for renderer in RENDERERDIRECTIONALLIGHTS:  # check directional light types
        if lightType == RENDERERDIRECTIONALLIGHTS[renderer]:
            return True
    for renderer in RENDERERSKYDOMELIGHTS:
        if lightType == RENDERERSKYDOMELIGHTS[renderer]:
            return True
    return False


def checkValidIblType(lightShape):
    """Check to see if the light shape is a valid skydome light
    Checks from dict RENDERERSKYDOMELIGHTS

    :param lightShape: The light shape node
    :type lightShape: str
    :return validity: True if the light is recognised, False if not
    :rtype: bool
    """
    lightType = cmds.nodeType(lightShape)
    for renderer in RENDERERSKYDOMELIGHTS:
        if lightType == RENDERERSKYDOMELIGHTS[renderer]:
            return True
    return False


"""
SCALE INTENSITY, SIZE, MATCH
"""


def scaleAreaLightIntensity(lightShape, scalePercentage, calcExposure=False, applyExposure=False, applyPure=True):
    """Scales the intensity of the lightShape. Multiple modes.  Scales by 'scalePercentage'
    1. Only Intensity (ignores Exposure)
    2. Only Exposure (ignores Intensity)
    3. Calculate As Pure Intensity Apply As Intensity (Exposure becomes 0)
    4. Calculate As Pure Intensity Apply As Exposure (Intensity becomes 1)
    5. Calculate As Pure Exposure Apply As Intensity (Exposure becomes 0)
    6. Calculate As Pure Exposure Apply As Exposure (Intensity becomes 1)

    :param lightShape: The light shape node
    :type lightShape: str
    :param scalePercentage: The percentage to be scaled
    :type scalePercentage: float
    :param calcExposure: Calculate As Exposure? False is Intensity, and null if "applyPure" is True
    :type calcExposure: bool
    :param applyExposure: Applies the new value as exposure if True, or intensity is False, also controls "applyPure"
    :type applyExposure: bool
    :param applyPure: if True reads/applies only the value designated by "applyExposure" Exposure if True, Intense False
    :type applyPure: bool
    :return intensityVal: the returned intensity value
    :rtype intensityVal: float
    :return exposureVal: the returned exposure value
    :rtype exposureVal: float
    """
    rendererNiceName = getRendererNiceNameFromLightShape(lightShape)
    attrDict = getRendererAttrDict(rendererNiceName)
    attrVDict = getLightAttr(lightShape, getIntensity=True, getExposure=True, getColor=False, getTemperature=False,
                             getTempOnOff=False, getShape=False, getNormalize=False, getLightVisible=False,
                             getScale=False)
    skipOldRedshift = not redshiftAreaExposureExists(lightShape, attrDict)  # True if Redshift exp should be skipped
    if skipOldRedshift:  # then Redshift exposure doesn't exist
        attrVDict[EXPOSURE] = 0.0  # set exposure to zero
    exposureVal = attrVDict[EXPOSURE]
    intensityVal = attrVDict[INTENSITY]
    # convert to pure exposure or intensity
    if not applyPure and not skipOldRedshift:  # if not all pure value calculate only one intensity
        if applyExposure:
            exposureVal += exposureVal * (scalePercentage / 100)
            cmds.setAttr(".".join([lightShape, attrDict[EXPOSURE]]), exposureVal)
            return intensityVal, exposureVal
        intensityVal += intensityVal * (scalePercentage / 100)
        cmds.setAttr(".".join([lightShape, attrDict[INTENSITY]]), intensityVal)
        return intensityVal, exposureVal
    if calcExposure:
        # convert to exposure
        intensityVal, exposureVal = lightingutils.convertExpAndIntToExposure(intensityVal,
                                                                             exposureVal)
        intensityVal = 1.0
        exposureVal += exposureVal * (scalePercentage / 100)
    else:
        # convert to intensity
        intensityVal, exposureVal = lightingutils.convertExpAndIntToIntensity(intensityVal,
                                                                              exposureVal)
        intensityVal += intensityVal * (scalePercentage / 100)
        exposureVal = 0.0
    # convert to exposure or intensity
    if applyExposure and not calcExposure and not skipOldRedshift:
        # only convert to exposure if necessary, may already be converted
        intensityVal, exposureVal = lightingutils.convertExpAndIntToExposure(intensityVal,
                                                                             exposureVal)
    elif not applyExposure and calcExposure:
        # convert to intensity if necessary, may already be converted
        intensityVal, exposureVal = lightingutils.convertExpAndIntToIntensity(intensityVal,
                                                                              exposureVal)
    cmds.setAttr(".".join([lightShape, attrDict[INTENSITY]]), intensityVal)
    if skipOldRedshift:  # don't set exposure
        return intensityVal, exposureVal
    cmds.setAttr(".".join([lightShape, attrDict[EXPOSURE]]), exposureVal)
    return intensityVal, exposureVal


def scaleAreaLightIntensitySelected(scalePercentage, calcExposure=False, applyExposure=False, applyPure=True):
    """Scales the intensity of selected area lights.  Multiple modes.  Scales by 'scalePercentage'
    1. Only Intensity (ignores Exposure)
    2. Only Exposure (ignores Intensity)
    3. Calculate As Pure Intensity Apply As Intensity (Exposure becomes 0)
    4. Calculate As Pure Intensity Apply As Exposure (Intensity becomes 1)
    5. Calculate As Pure Exposure Apply As Intensity (Exposure becomes 0)
    6. Calculate As Pure Exposure Apply As Exposure (Intensity becomes 1)

    :param scalePercentage: The percentage to be scaled
    :type scalePercentage: float
    :param calcExposure: Calculate As Exposure? False is Intensity, and null if "applyPure" is True
    :type calcExposure: bool
    :param applyExposure: Applies the new value as exposure if True, or intensity is False, also controls "applyPure"
    :type applyExposure: bool
    :param applyPure: if True reads/applies only the value designated by "applyExposure" Exposure if True, Intense False
    :type applyPure: bool
    :return intensityVal: the returned intensity value
    :rtype intensityVal: float
    :return exposureVal: the returned exposure value
    :rtype exposureVal: float
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        om2.MGlobal.displayWarning("No Lights Selected Please Select")
    for obj in selObjs:
        if cmds.objectType(obj) != "transform":  # if not a transform node, it could be a shape node so try the parent
            obj = cmds.listRelatives(obj, parent=True, fullPath=True)
        lightShape = getLightShape(obj)
        if checkValidLightType(lightShape):
            scaleAreaLightIntensity(lightShape, scalePercentage, calcExposure=calcExposure, applyExposure=applyExposure,
                                    applyPure=applyPure)


def scaleDirectionalLightIntensity(lightShape, scalePercentage, rendererNiceName):
    """scales the light intensity of a directional light by the percentage given.

    :param lightShape: the Maya lightshape name
    :type lightShape: str
    :param scalePercentage: the percentage to be scaled by
    :type scalePercentage: float
    """
    attrValDict = getDirectionalAttr(lightShape, getIntensity=True, getColor=False, getTemperature=False,
                                     getTempOnOff=False, getAngleSoft=False, getRotation=False)
    attrValDict[INTENSITY] = (attrValDict[INTENSITY] * (scalePercentage / 100)) + attrValDict[INTENSITY]
    setDirectionalAttr(lightShape, rendererNiceName, attrValDict)


def scaleIblLightIntensity(lightShape, scalePercentage):
    """scales the light intensity of an ibl skydome light by the percentage given.

    :param lightShape: the Maya lightshape name
    :type lightShape: str
    :param scalePercentage: the percentage to be scaled by
    :type scalePercentage: float
    """
    attrValDict = getIblAttr(lightShape, getIntensity=True, getExposure=False, getColor=False, getLightVisible=False,
                             getIblTexture=False, getTranslation=False, getRotation=False, getScale=False)
    attrValDict[INTENSITY] = (attrValDict[INTENSITY] * (scalePercentage / 100)) + attrValDict[INTENSITY]
    setIblAttr(lightShape, attrValDict)


def scaleAllLightIntensitiesLightList(scalePercentage, areaLightShapeList, directionalLightShapeList, skydomeShapeList,
                                      rendererNiceName, calcExposure=False, applyExposure=False, applyPure=True):
    """Scales the light intensities off multiple light types given the shape list for
    - area shapes list
    - directional shapes
    - ibl shapes list

    :param scalePercentage: the percentage to scale by
    :type scalePercentage: float
    :param areaLightShapeList: list of area light shapes names
    :type areaLightShapeList: list
    :param directionalLightShapeList: list of directional light shapes names
    :type directionalLightShapeList: list
    :param skydomeShapeList: list of directional light shapes names
    :type skydomeShapeList: list
    :param rendererNiceName: the nice name of the renderer Redshift, Arnold etc
    :type rendererNiceName: list
    :param calcExposure: calculate using the exposure of area lights?  Should be false, should always be intensity
    :type calcExposure: bool
    :param applyExposure: apply as exposure of area lights only
    :type applyExposure: bool
    :param applyPure: area lights apply as pure, either intensity to 1 or exposure to zero depending on applyExposure
    :type applyPure:
    """
    "scalePercentage scaleAllLightIntensitiesLightList", scalePercentage
    if not areaLightShapeList and not directionalLightShapeList and not skydomeShapeList:
        om2.MGlobal.displayWarning("No {0} Lights Selected Or Found.  "
                                   "Please Create Or Select {0} Lights".format(rendererNiceName))
        return
    if areaLightShapeList:
        for areaLightShape in areaLightShapeList:
            scaleAreaLightIntensity(areaLightShape, scalePercentage, calcExposure=calcExposure,
                                    applyExposure=applyExposure, applyPure=applyPure)
    if directionalLightShapeList:
        for directionalLightShape in directionalLightShapeList:
            scaleDirectionalLightIntensity(directionalLightShape, scalePercentage, rendererNiceName)
    if skydomeShapeList:
        for skydomeShape in skydomeShapeList:
            scaleIblLightIntensity(skydomeShape, scalePercentage)
    lightShapeList = areaLightShapeList + directionalLightShapeList + skydomeShapeList
    shapeListUnique = namehandling.getUniqueShortNameList(lightShapeList)
    om2.MGlobal.displayInfo("Success {} Light's Intensities Scaled: {}".format(rendererNiceName, shapeListUnique))


def scaleAllLightsIntensitySelected(scalePercentage, rendererNiceName, calcExposure=False, applyExposure=False,
                                    applyPure=True):
    """Scales all the light intensities of lights by percentage.  This function is filtered by selection

    Area lights can be calculated with options:

        1. Only Intensity (ignores Exposure)
        2. Only Exposure (ignores Intensity)
        3. Calculate As Pure Intensity Apply As Intensity (Exposure becomes 0)
        4. Calculate As Pure Intensity Apply As Exposure (Intensity becomes 1)
        5. Calculate As Pure Exposure Apply As Intensity (Exposure becomes 0)
        6. Calculate As Pure Exposure Apply As Exposure (Intensity becomes 1)

    :param scalePercentage: the percentage to be scaled by
    :type scalePercentage: float
    :param rendererNiceName: the renderer name ie "Redshift" or "Arnold" etc
    :type rendererNiceName: str
    :param calcExposure: Calculate As Exposure? False is Intensity, and null if "applyPure" is True
    :type calcExposure: bool
    :param applyExposure: Applies the new value as exposure if True, or intensity is False, also controls "applyPure"
    :type applyExposure: bool
    :param applyPure: if True reads/applies only the value designated by "applyExposure" Exposure if True, Intense False
    :type applyPure: bool
    """
    areaLightShapeList, directionalLightShapeList, skydomeShapeList = \
        filterAllLightShapesFromSelection(rendererNiceName, message=True)
    scaleAllLightIntensitiesLightList(scalePercentage, areaLightShapeList, directionalLightShapeList, skydomeShapeList,
                                      rendererNiceName, calcExposure=calcExposure, applyExposure=applyExposure,
                                      applyPure=applyPure)


def scaleAllLightIntensitiesScene(scalePercentage, rendererNiceName, calcExposure=False, applyExposure=False,
                                  applyPure=True):
    """Scales all the light intensities of lights by percentage. This function ignores selection and scales all lights
    of the renderer type in the scene.

    Area lights can be calculated with options:

        1. Only Intensity (ignores Exposure)
        2. Only Exposure (ignores Intensity)
        3. Calculate As Pure Intensity Apply As Intensity (Exposure becomes 0)
        4. Calculate As Pure Intensity Apply As Exposure (Intensity becomes 1)
        5. Calculate As Pure Exposure Apply As Intensity (Exposure becomes 0)
        6. Calculate As Pure Exposure Apply As Exposure (Intensity becomes 1)

    :param scalePercentage: the percentage to be scaled by
    :type scalePercentage: float
    :param rendererNiceName: the renderer name ie "Redshift" or "Arnold" etc
    :type rendererNiceName: str
    :param calcExposure: Calculate As Exposure? False is Intensity, and null if "applyPure" is True
    :type calcExposure: bool
    :param applyExposure: Applies the new value as exposure if True, or intensity is False, also controls "applyPure"
    :type applyExposure: bool
    :param applyPure: if True reads/applies only the value designated by "applyExposure" Exposure if True, Intense False
    :type applyPure: bool
    """
    areaLightShapeList, directionalLightShapeList, skydomeShapeList = getAllLightShapesInScene(rendererNiceName)
    scaleAllLightIntensitiesLightList(scalePercentage, areaLightShapeList, directionalLightShapeList, skydomeShapeList,
                                      rendererNiceName, calcExposure=calcExposure, applyExposure=applyExposure,
                                      applyPure=applyPure)


def scaleLightSize(lightTransform, scalePercentage):
    """Scales the physical size of a light by the percentage amount

    :param lightShape: The light shape node
    :type lightShape: str
    :param scalePercentage: The percentage to be scaled
    :type scalePercentage: float
    :return scale: The scale result as (1.5, 1.5, 1.5)
    :rtype scale: list
    """
    scale = cmds.getAttr("{}.scale".format(lightTransform))[0]
    scaleX = scale[0] + (scale[0] * (scalePercentage / 100))
    scaleY = scale[1] + (scale[1] * (scalePercentage / 100))
    scaleZ = scale[2] + (scale[2] * (scalePercentage / 100))
    cmds.setAttr("{}.scale".format(lightTransform), scaleX, scaleY, scaleZ)
    return scaleX, scaleY, scaleZ


def scaleLightSizeSelected(scalePercentage):
    """Scales physical size of the selected lights by the percentage amount
    Checks valid lights only

    :param lightShape: The light shape node
    :type lightShape: str
    :param scalePercentage: The percentage to be scaled
    :type scalePercentage: float
    :return scale: The scale result as (1.5, 1.5, 1.5)
    :rtype scale: list
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        om2.MGlobal.displayWarning("No Lights Selected Please Select")
    for obj in selObjs:
        if cmds.objectType(obj) != "transform":  # if not a transform node, it could be a shape node so try the parent
            obj = cmds.listRelatives(obj, parent=True, fullPath=True)
        lightShape = getLightShape(obj)
        if checkValidLightType(lightShape):
            scaleLightSize(obj, scalePercentage)


def scaleAreaLightSizeAll(scalePercentage, rendererNiceName):
    """Scales all area lights of a given renderer type, scales from each light center
    Will rename non unique lights

    :param scalePercentage: The percentage of the scale, eg 90.0 (is 90% or will scale by 1.9)
    :type scalePercentage: float
    :param rendererNiceName: the nice name of the renderer eg "Redshift"
    :type rendererNiceName: str
    """
    areaLightTransformList, areaLightShapeList = getAllAreaLightsInScene(rendererNiceName)  # area lights
    if not areaLightTransformList:
        om2.MGlobal.displayWarning("No Lights Found To Scale For {}".format(rendererNiceName))
        return
    areaLightTransformList = namehandling.forceUniqueShortNameList(areaLightTransformList)
    for areaLight in areaLightTransformList:
        scaleLightSize(areaLight, scalePercentage)


def scaleLightsList(scalePercentage, rendererNiceName, areaLightTransformList, areaLightShapeList,
                    iblSkydomeTransformList, directionalTransformList, scalePivot=(0.0, 0.0, 0.0),
                    ignoreNormalization=False):
    """Scales The Light Lists from world 0, 0, 0 by a scale percentage eg 90.0 (is 90% or will scale by 1.9)
    
    Will scale area lights by toggling normalization off (then back on) by default. The default keeps the lights 
    correctly scaled relative to the scene and models.
    
    Lights should have unique or long names.

    :param scalePercentage: The percentage of the scale, eg 90.0 (is 90% or will scale by 1.9)
    :type scalePercentage: float
    :param rendererNiceName: the nice name of the renderer eg "Redshift"
    :type rendererNiceName: str
    :param areaLightTransformList: the area light transform list
    :type areaLightTransformList: list
    :param areaLightShapeList: the area light shape list
    :type areaLightShapeList: list
    :param iblSkydomeTransformList: the ibl light transform list
    :type iblSkydomeTransformList: list
    :param directionalTransformList: the directional light transform list
    :type directionalTransformList: list
    :param scalePivot: tuple of floats, the scale pivot in world space
    :type scalePivot: tuple
    :param ignoreNormalization: area lights can be normalized affecting the scale lighting, should you ignore this?
    :type ignoreNormalization: bool
    """
    if scalePercentage == 0:
        om2.MGlobal.displayWarning("Scale Percentage Cannot Be Zero, has no effect")
        return
    rememberObjSelection = cmds.ls(selection=True, long=True)
    gScale = 1.0 + (scalePercentage / 100.00)
    allLightTransforms = areaLightTransformList + iblSkydomeTransformList + directionalTransformList
    # -----------------------------------------
    # De-normalize Any Normalized Area Lights
    # -----------------------------------------
    if not ignoreNormalization:
        lightNormalizeTransformList = list()
        for i, lightTransform in enumerate(areaLightTransformList):
            normalValue = getLightNormalizeValue(areaLightShapeList[i])
            if normalValue:  # normalize off for all lights and record normalize states
                lightNormalizeTransformList.append(lightTransform)
        if lightNormalizeTransformList:  # convert lights that have normalization on
            convertNormalizeList(lightNormalizeTransformList, False, applyAsIntensity=False, renderer=rendererNiceName)
    # -----------------------------------------
    # Do The Scale
    # -----------------------------------------
    # note could use scaleUtils.scaleObjListPivot() which doesn't mess with pivots,
    # scaleObjListPivot.scaleObjListPivot() is ok with pure lights
    scaleutils.scaleWorldPivotCenterPivot(allLightTransforms, gScale, scalePivot=scalePivot)
    # -----------------------------------------
    # Re Normalize
    # -----------------------------------------
    if not ignoreNormalization:
        if lightNormalizeTransformList:  # normalize lights back on that had normalize on
            convertNormalizeList(lightNormalizeTransformList, True, applyAsIntensity=False, renderer=rendererNiceName)
    cmds.select(rememberObjSelection, replace=True)


def scaleAllLightsInScene(scalePercentage, rendererNiceName, scalePivot=(0.0, 0.0, 0.0), ignoreNormalization=False,
                          ignoreIbl=False, ignoreDirectionals=False, message=True, forceShortName=False):
    """Scales All The Lights in the scene from world 0, 0, 0 by a scale percentage eg 90.0 is 90% or will scale by 1.9
    
    Will scale area lights by toggling normalization off (then back on) by default.  The default keeps the lights 
    correctly scaled relative to the scene and models.

    :param scalePercentage: the percentage of the scale offset
    :type scalePercentage: float
    :param rendererNiceName: the nice name of the renderer eg "Redshift", "Arnold", "Renderman"
    :type rendererNiceName: str
    :param scalePivot: tuple of floats, the scale pivot in world space
    :type scalePivot: tuple
    :param ignoreNormalization: area lights can be normalized affecting the scale lighting, should you ignore this?
    :type ignoreNormalization: bool
    :param ignoreIbl: don't scale the IBLs if True
    :type ignoreIbl: bool
    :param message: don't scale the IBLs if True
    :type message: bool
    :return areaLightTransformList: the area light transforms scaled (now renamed if not unique)
    :rtype areaLightTransformList: list
    :return areaLightShapeList: the area light shapes scaled (now renamed if not unique)
    :rtype areaLightShapeList: list
    :return iblSkydomeTransformList: the ibl light transforms scaled (now renamed if not unique)
    :rtype iblSkydomeTransformList: list
    :return iblSkydomeShapeList: the ibl light shapes scaled (now renamed if not unique)
    :rtype iblSkydomeShapeList: list
    """
    iblSkydomeTransformList = list()
    iblSkydomeShapeList = list()
    directionalTransformList = list()
    directionalShapeList = list()
    areaLightTransformList, areaLightShapeList = getAllAreaLightsInScene(rendererNiceName)  # area lights
    if forceShortName:
        areaLightTransformList = namehandling.forceUniqueShortNameList(areaLightTransformList)
        areaLightShapeList = namehandling.forceUniqueShortNameList(areaLightShapeList)
    if not ignoreIbl:  # IBLs
        iblSkydomeTransformList, iblSkydomeShapeList = getAllIblSkydomeLightsInScene(rendererNiceName)
        if forceShortName:
            iblSkydomeTransformList = namehandling.forceUniqueShortNameList(iblSkydomeTransformList)
            iblSkydomeShapeList = namehandling.forceUniqueShortNameList(iblSkydomeShapeList)
    if not ignoreDirectionals:
        directionalTransformList, directionalShapeList = getAllDirectionalLightsInScene(rendererNiceName)
        if forceShortName:
            directionalTransformList = namehandling.forceUniqueShortNameList(directionalTransformList)
            directionalShapeList = namehandling.forceUniqueShortNameList(directionalShapeList)
    if not areaLightTransformList and not iblSkydomeTransformList and not directionalTransformList:  # no lights found
        om2.MGlobal.displayWarning("No Lights Found To Scale For {}".format(rendererNiceName))
        return
    # do the scale
    scaleLightsList(scalePercentage, rendererNiceName, areaLightTransformList, areaLightShapeList,
                    iblSkydomeTransformList, directionalTransformList, scalePivot=scalePivot,
                    ignoreNormalization=ignoreNormalization)
    if message:  # success
        om2.MGlobal.displayInfo("Success {} Lights Scaled By {} %".format(rendererNiceName, scalePercentage))
    return areaLightTransformList, areaLightShapeList, iblSkydomeTransformList, iblSkydomeShapeList, \
           directionalTransformList, directionalShapeList


def matchLights(rendererNiceName, matchObject, targetObject, locatorMode=False):
    """match object to object only 2017 plus should be modified

    :param rendererNiceName: the renderer name ie "Redshift" or "Arnold" etc
    :type rendererNiceName: str
    :param matchObject: the transform to match (move)
    :type matchObject: str
    :param targetObject: the transform thats the target (doesn't move)
    :type targetObject: str
    :param locatorMode: if matching with locators then use this, as it overrides renderman scale
    :type locatorMode: bool
    """
    cmds.matchTransform([matchObject, targetObject], pos=1, rot=1, scl=1, piv=0)
    if rendererNiceName == RENDERMAN and not locatorMode:  # if a light and renderman is the renderer
        fixRendermanScale(matchObject, locatorMode=locatorMode)  # scales the Renderman light *2 to match
    elif rendererNiceName == RENDERMAN and locatorMode:  # if a locator and renderman is the renderer
        fixRendermanScale(matchObject, locatorMode=locatorMode)  # scales the Renderman light *.5 to match
    elif rendererNiceName == REDSHIFT and locatorMode:
        shape = cmds.getAttr(".".join([targetObject, "areaShape"]))
        if shape == 3:  # then is cylinder so rotate 90 on z to match arnold
            rotateObjectSpaceXForm(matchObject, (0, 0, 90))


"""
FIX RENDERER ATTRIBUTES
"""


def fixRendermanAttrs(genericValuesDict, warningState=False):
    """Renderman's attribute related to changing the light shape doesn't exist, instead it requires different shape
    nodes.  There is no shape type for cylinder
    Also the scale values of renderman lights should be doubled to match Arnold and Redshift

    :param genericValuesDict: values dict with Attrs as keys and values as values
    :type genericValuesDict:
    :return genericValuesDict: genericValuesDict now fixed with the gShape_shape set to string rather than an int
    :rtype genericValuesDict:
    """
    if genericValuesDict[SHAPE] == 3:  # shape is cylinder
        genericValuesDict[SHAPE] = 0
        om2.MGlobal.displayWarning("Cylinder Light is not supported in Renderman, setting to Rectangle")
        warningState = True
    genericValuesDict[SHAPE] == SHAPE_ATTR_ENUM_LIST_NICE[genericValuesDict[SHAPE]]  # converts from int to string
    return genericValuesDict, warningState


def fixGetRendermanIntensity(intensity):
    """Fixes the Renderman light intensity while getting attributes (getAttr)

    :param intensity: the incoming light intensity
    :type intensity: float
    :return intensity: the outgoing fixed light intensity
    :rtype intensity: float
    """
    if intensity != 0.0:
        intensity /= 46000.0
    return intensity


def fixRendermanScale(transformNode, locatorMode=False):
    """doubles the scale of Renderman lights to match other renderers
    if in locator mode then it halves the scale

    :param transformNode: The Renderman light's transform node
    :type transformNode: str
    :param locatorMode: if passing in a locator then this should be True
    :type locatorMode: bool
    :param scaleValues: if the scaleValues are known set this attribute as a tuple/list (float, float, float)
    :type scaleValues: list
    """
    scaleAmount = 2
    if locatorMode:
        scaleAmount = .5
    scale = cmds.getAttr("{}.scale".format(transformNode))[0]
    cmds.setAttr("{}.scale".format(transformNode), scale[0] * scaleAmount, scale[1] * scaleAmount,
                 scale[2] * scaleAmount)


def fixRendermanShape(transformNodeOld, newShape, warningState=False, keepPosition=True, keepSelection=True):
    """Remakes the Renderman area light with a new shape Rectangle, Disk or Sphere.

    Note: Cylinder is not available in Renderman

    :param transformNodeOld: The old transform node name
    :type transformNodeOld: str
    :param newShape: Shape is an int that matches SHAPE_ATTR_ENUM_LIST_NICE
    :type newShape: int
    :param warningState: Carry through the warning state
    :type warningState: bool
    :param keepPosition:
    :type keepPosition:
    :param keepSelection: Maintain selection?
    :type keepSelection: bool
    :return transform: The transform node of the new light
    :rtype transform: str
    :return shape: The shape node of the new light
    :rtype shape: str
    :return warningState: The warning state
    :rtype warningState: bool
    """
    transformShortName = namehandling.getShortName(transformNodeOld)
    if keepSelection:
        selObjs = cmds.ls(selection=True, long=True)
    if keepPosition:
        # record the parent long name and position, rotation and scale
        parentObj = cmds.listRelatives(transformNodeOld, parent=True, fullPath=True)
        attrValueList = attributes.getTransRotScaleAttrsAsList(transformNodeOld)
    cmds.refresh()  # refresh UI must be here or else Renderman 22+ errors an annoying warning after deleting the light
    cmds.delete(transformNodeOld)
    if newShape == 0:  # Shape is rect see SHAPE_ATTR_ENUM_LIST_NICE
        transform, shape = rendermanlights.createRendermanPxrRectLight(name=transformShortName)
        om2.MGlobal.displayWarning("Renderman Light Has Been Deleted And Rebuilt To Become A Rectangle")
        warningState = True
    elif newShape == 1:  # Shape is disc see SHAPE_ATTR_ENUM_LIST_NICE
        transform, shape = rendermanlights.createRendermanPxrDiskLight(name=transformShortName)
        om2.MGlobal.displayWarning("Renderman Light Has Been Deleted And Rebuilt To Become A Disc")
        warningState = True
    elif newShape == 2:  # Shape is sphere see SHAPE_ATTR_ENUM_LIST_NICE
        transform, shape = rendermanlights.createRendermanPxrSphereLight(name=transformShortName)
        om2.MGlobal.displayWarning("Renderman Light Has Been Deleted And Rebuilt To Become A Sphere")
        warningState = True
    elif newShape == 3:  # Shape is cylinder see SHAPE_ATTR_ENUM_LIST_NICE
        transform, shape = rendermanlights.createRendermanPxrRectLight(name=transformShortName)
        om2.MGlobal.displayWarning("Cylinder Light is not supported in Arnold, setting to Rect")
    else:
        transform, shape = rendermanlights.createRendermanPxrRectLight(name=transformShortName)
        om2.MGlobal.displayWarning("Shape type `{}` not found! "
                                   "Creating a Rect".format(SHAPE_ATTR_ENUM_LIST_NICE[newShape]))
        warningState = True
    if keepPosition:  # Reparent and restore transforms
        if parentObj:
            cmds.parent(transform, parentObj)
        attributes.setTransRotScaleAttrsAsList(transform, attrValueList)
    if keepSelection:
        if selObjs:
            cmds.select(selObjs, replace=True)
    return transform, shape, warningState


def fixRendermanGetLightShape(lightShape, warningState=False):
    """Records the light type of a renderman light and returns the shape as an int for the generic attribute type
    0 = rect, 1 = disk, 2 = sphere

    :param lightShape: the name of the lightShape node
    :type lightShape: str
    :return genericShape: the shape as an int 0 = rect, 1 = disk, 2 = sphere
    :rtype genericShape: int
    """
    # get the light type
    lightType = cmds.nodeType(lightShape)
    if lightType == "PxrRectLight":
        genericShape = 0  # shape is rect
    elif lightType == "PxrDiskLight":
        genericShape = 1  # shape is disc
    elif lightType == "PxrSphereLight":
        genericShape = 2  # shape is sphere
    else:
        genericShape = 0  # shape is rect
        om2.MGlobal.displayWarning("Shape type `{}` not found or supported by Renderman!  "
                                   "Will record as a Rect".format(lightType))
        warningState = True
    return genericShape, warningState


def fixRendermanLightVisAttr(attrDict, lightShape):
    """Renderman's light visibility attr has changed in v22, check it exists, if not use the old attr name

    :param attrDict: the attribute dictionary of the Renderman renderer
    :type attrDict: dict
    :param lightShape: a single redshift light shape node
    :type lightShape: str
    :return attrDict: The Renderman attr dict, now with the correct light visibility attribute name
    :rtype attrDict: dict
    """
    if not cmds.attributeQuery(attrDict[LIGHTVISIBILITY], node=lightShape, exists=True):
        attrDict[LIGHTVISIBILITY] = "rman__riattr__visibility_camera"  # will be v21 not v22 or above
    return attrDict


def fixRendermanIBLScale(scale):
    """Fix for setAttr Renderman Scale
    In v21 and below invert scaleZ as Renderman's IBLs are inverted, the scale should be multiplied by
    2000 to match Arnold
    In v22 and above there's no offset and multiply by 0.4 to match

    :param scale: the scale of the IBL three values
    :type scale: list
    :return scale: the scale of the IBL three values
    :rtype scale: list
    """
    if scale is not None:
        if rendermanlights.getRendermanVersion() < 22.0:  # renderman was inverted skydomes pre v22
            scale = (scale[0] * 2000.0, scale[1] * 2000.0, (scale[2] * -1) * 2000.0)
        else:  # new scale is 0.4 compared to arnold
            scale = (scale[0] * 0.4, scale[1] * 0.4, scale[2] * 0.4)
    return scale


def fixGetRendermanIBLScale(scale):
    """Fix for getAttr Renderman Scale
    In v21 and below invert scaleZ as Renderman's IBLs are inverted, the scale should be divided by
    2000 to match Arnold
    In v22 and above there's no offset and multiply by 0.4 to match

    :param scale: the scale of the IBL three values
    :type scale: list
    :return scale: the scale of the IBL three values
    :rtype scale: list
    """
    if rendermanlights.getRendermanVersion() < 22.0:
        return (scale[0] / 2000, scale[1] / 2000, scale[2] / 2000 * -1)
    else:
        return (scale[0] / 0.4, scale[1] / 0.4, scale[2] / 0.4)


def fixRendermanIBLRot(rotate):
    """fix rotation only if v21 or lower rotating -180, since the IBL is inverted

    :param rotate: the IBLs rotation in 3 values
    :type rotate: list
    :return: the IBLs rotation in 3 values
    :rtype: list
    """
    if rotate is not None:
        return rotate
    if rendermanlights.getRendermanVersion() < 22.0:  # renderman had a rotated IBL offset pre v22
        return (rotate[0], rotate[1] - 180.0, rotate[2])
    # else v22 and above there is now no rotation offset
    return rotate


def fixGetRendermanIBLRot(rotate):
    """fix rotation only if v21 or lower rotating +180, since the IBL is inverted

    :param rotate: the IBLs rotation in 3 values
    :type rotate: list
    :return: the IBLs rotation in 3 values
    :rtype: list
    """
    if not rotate:
        return rotate
    if rendermanlights.getRendermanVersion() < 22.0:  # renderman had a rotated IBL offset pre v22
        return (rotate[0], rotate + 180, rotate[2])
    # else v22 and above there is now no rotation offset
    return rotate


def fixRedshiftIblIntensity(attrValDict):
    """ Redshift intensity is a color so set value is as rgb 0-1 range

    :param attrValDict: attribute dictionary from the IBL light
    :type attrValDict: dict
    :return attrValDict: attribute dictionary from the IBL light
    :rtype attrValDict: dict
    """
    if attrValDict[INTENSITY] is not None:
        attrValDict[INTENSITY] = (attrValDict[INTENSITY], attrValDict[INTENSITY], attrValDict[INTENSITY])
        attrValDict[INTENSITY]
    if attrValDict[EXPOSURE] is not None:
        attrValDict.pop(EXPOSURE, None)
    return attrValDict


def redshiftAreaExposureExists(lightShape, attrDict):
    """older versions of Redshift had no exposure on the area lights, return True if this attribute exists

    :param lightShape: a single redshift light shape node
    :type lightShape: str
    :param attrDict: the attribute dictionary of the redshift renderer
    :type attrDict: dict
    :return exposureExists:  Does the exposure attr exist?
    :rtype exposureExists: bool
    """
    return cmds.attributeQuery(attrDict[EXPOSURE], node=lightShape, exists=True)  # exposure does not exist


def fixRedshiftAreaSetExposure(attrValDict, lightShape, attrDict):
    """Fixes potential issues with intensity/exposure in old versions of Redshift

    If exposure does not exist then convert to pure intensity and remove the exposure attr from attrValDict
    If exposure does exist then leave the attrValDict as per normal

    :param attrValDict: attribute dictionary of attr values for an area light
    :type attrValDict: dict
    :param lightShape: a single redshift light shape node
    :type lightShape: str
    :param attrDict: the attribute dictionary of the redshift renderer
    :type attrDict: dict
    :return attrValDict: attribute dictionary of attr values for an area light
    :rtype attrValDict: dict
    """
    if attrValDict[EXPOSURE] is None and attrValDict[INTENSITY] is None:  # skip this check
        return attrValDict
    if redshiftAreaExposureExists(lightShape, attrDict):  # exposure exists so return
        return attrValDict
    # must be an old version of Redshift so convert to pure intensity value
    if attrValDict[EXPOSURE] is None:
        attrValDict[EXPOSURE] = 0.0
    intensityVal = lightingutils.convertExpAndIntToIntensity(float(attrValDict[INTENSITY]),
                                                             float(attrValDict[EXPOSURE]))[0]
    if attrValDict[EXPOSURE]:  # if any exposure then redshift light will need conversion
        shapeUnique = namehandling.getUniqueShortName(lightShape)
        om2.MGlobal.displayInfo("Redshift Light `{}` Set As Intensity Not Exposure.  "
                                "Intensity set: {}".format(shapeUnique, intensityVal))
    attrValDict[INTENSITY] = intensityVal  # set new intensity
    attrValDict.pop(EXPOSURE, None)  # now remove the exposure
    return attrValDict


def fixRedshiftAreaCylinder(attrValDict, scale, lightShape):
    """if the shape for an area light is a cylinder then switch the scale and rotate to match

    :param attrValDict: attribute dictionary of attr values for an area light
    :type attrValDict: dict
    :param scale: the scale value x y z
    :type scale: tuple(float)
    :param lightShape: a single redshift light shape node
    :type lightShape: str
    :return scale: the new generic area light scale
    :rtype scale: tuple(float)
    """
    if attrValDict[SHAPE] is None:
        return scale
    if attrValDict[SHAPE] != 3:  # not cylinder bail
        return scale
    if scale:  # redshift cylinder scales are out, switch x and y
        xTemp = scale[0]
        x = scale[1]
        y = xTemp
        scale = (x, y, scale[2])
        lightTransform = cmds.listRelatives(lightShape, parent=True, fullPath=True)[0]
        rotateObjectSpaceXForm(lightTransform, (0, 0, 90))
    return scale


def fixRedshiftIblRot(rotate):
    """Redshift IBL skydome rotation is -90 degrees behind Arnold's so we match to Arnold

    :param rotate: the 3 value rotation of the light, if not needed will be None
    :type rotate: list
    :return rotate: the 3 value rotation of the light, if not needed will be None
    :rtype rotate: list
    """
    if rotate is not None:
        rotate = (rotate[0], rotate[1] - 90, rotate[2])
    return rotate


def arnoldVisibilityExists(attrDict, lightShape):
    """Older versions of Arnold had no visbility (aiCamera) on area lights, return True if this attribute now exists

    :param lightShape: a single arnold light shape node
    :type lightShape: str
    :param attrDict: the attribute dictionary of the arnold renderer
    :type attrDict: dict
    :return visibilityExists:  Does the visibility (aiCamera) attr exist?
    :rtype visibilityExists: bool
    """
    return cmds.attributeQuery(attrDict[LIGHTVISIBILITY], node=lightShape, exists=True)


def fixArnoldVisibility(attrDict, lightShape):
    """Older versions of Arnold had no visbility (aiCamera) on area lights, this fixes and converts the attribute

    round the attr float value if new arnold and visibility (aiCamera) att exists.  new value will be 1 or 0
    if old Arnold then return the visibility as 0

    :param lightShape: a single arnold light shape node
    :type lightShape: str
    :param attrDict: the attribute dictionary of the arnold renderer
    :type attrDict: dict
    :return exposureExists:  Does the visibility (aiCamera) attr exist?
    :rtype exposureExists: bool
    """
    if arnoldVisibilityExists(attrDict, lightShape):  # check for aiCamera attribute in new version
        visiblityFloat = cmds.getAttr(".".join([lightShape, attrDict[LIGHTVISIBILITY]]))
        visiblityInt = int("{0:.0f}".format(round(visiblityFloat, 0)))  # round to zero or one
        return visiblityInt
    else:  # is an old version of Arnold so disable visibility of the light
        return 0


def fixArnoldAttrs(genericValuesDict, warningState=False):
    """Arnold's attribute related to it's shape is in string format not int and contains no sphere setting so must
    be converted.  This function changes this attribute value in the generic dictionary. Should be modified as it's
    about to be passed into the set method/s

    :param genericValuesDict: values dict with Attrs as keys and values as values
    :type genericValuesDict:
    :return genericValuesDict: genericValuesDict now fixed with the gShape_shape set to string rather than an int
    :rtype genericValuesDict:
    """
    if genericValuesDict[SHAPE] == 0:  # shape is rect
        genericValuesDict[SHAPE] = "quad"
    elif genericValuesDict[SHAPE] == 1:  # shape is disc
        genericValuesDict[SHAPE] = "disk"
    elif genericValuesDict[SHAPE] == 2:  # shape is sphere
        genericValuesDict[SHAPE] = "quad"
        om2.MGlobal.displayWarning("Spherical Light is not supported in Arnold, setting to Quad")
        warningState = True
    elif genericValuesDict[SHAPE] == 3:  # shape is cylinder
        genericValuesDict[SHAPE] = "cylinder"
    return genericValuesDict, warningState


def fixGetArnoldIntensity(intensity):
    """Fixes the Arnold light intensity for directional lights while getting attributes (getAttr)

    :param intensity: the incoming light intensity
    :type intensity: float
    :return intensity: the outgoing fixed light intensity
    :rtype intensity: float
    """
    if intensity != 0.0:
        intensity /= 3.13
    return intensity


def fixArnoldGetLightShape(lightShape, warningState=False):
    """Fixes the arnold shape attribute which is in string format, changes it to int for pulling info

    :param lightShape: the light shape node name
    :type lightShape: str
    :param warningState: the warning state, usually passed in and warning if the type not found
    :type warningState: bool
    :return shapeValue: the value of the shape attribute, now changed to int 0 = "quad", 1 = "disk", 3 = "cylinder"
    :rtype shapeValue:
    :return warningState: the warning state, could be changed if type not found
    :rtype warningState: bool
    """
    shapeValue = cmds.getAttr("{}.aiTranslator".format(lightShape))
    if shapeValue == "quad":  # shape is rect
        shapeValue = 0
    elif shapeValue == "disk":  # shape is disc
        shapeValue = 1
    elif shapeValue == "cylinder":  # shape is cylinder
        shapeValue = 3
    else:
        om2.MGlobal.displayWarning("The Shape Value `{}` is not supported, defaults to `Quad`".format(shapeValue))
        warningState = True
    return shapeValue, warningState


def fixArnoldIBLTexture(lightShape, attrValDict):
    """Fixes Arnolds IBL texture as building an extra texture map node as file node is required

    :param lightShape: the lightshape skydome name
    :type lightShape: str
    :param attrValDict: the dictionary of the skyDome values
    :type attrValDict: dict
    :return attrValDict: the dictionary of the skyDome values
    :rtype attrValDict: dict
    """
    if attrValDict[IBLTEXTURE] is not None:
        iblTexturePath = attrValDict[IBLTEXTURE]
        attrValDict.pop(IBLTEXTURE, None)
        attrValDict.pop(LIGHTCOLOR, None)
        # build texture or modify existing
        warning, nodes = textures.setOrCreateFileTexturePath(lightShape, "color", iblTexturePath,
                                                             textureNodeName="hdriImageFile", nodeType="file",
                                                             colorSpace="Raw", asAlpha=False)
        if warning:
            om2.MGlobal.displayError("The Connected Texture Node Is Not Valid or Is Not A Supported Texture Type, "
                                     "Please Check The Connected Texture Node")
            return False
    return attrValDict


"""
NAME & RENAME
"""


def removeRendererSuffix(lightTransform):
    """Finds the suffix of a light's transform node and checks if it matches a legitimate renderer suffix
    if so then remove it.

    :param lightTransform:  A light's transform node name
    :type lightTransform: str
    :return lightTransform: Light Transform name now with Renderer suffix removed
    :rtype lightTransform: str
    :return suffixRemoved: bool True if the suffix was removed, False if it wasn't
    :rtype suffixRemoved: bool
    """
    suffixRemoved = False
    nameChunkList = lightTransform.split('_')
    suffix = nameChunkList[-1]
    for key in RENDERER_SUFFIX_DICT:
        if RENDERER_SUFFIX_DICT[key] == suffix:
            nameChunkList.pop(-1)
            suffixRemoved = True
            lightTransform = "_".join(nameChunkList)
            break
    return lightTransform, suffixRemoved


def renameLight(lightTransform, newName, addSuffix=True, renderer=None, lightFamily=AREALIGHTS, forceUnique=False):
    """Renames a light and handles the renderer suffix, also checks for non unique names and applies with numeric
    padding

    :param lightTransform:  A light's transform node name best if longName
    :type lightTransform: str
    :param newName: The incoming new name of the light
    :type newName: str
    :param addSuffix: add a suffix?  Will also remove/replace existing Renderer suffixes
    :type addSuffix: bool
    :param renderer: if the light is a directional light then the renderer name should be passed in, otherwise auto
    :type renderer: str
    :param lightTransform:  A light's transform new node name
    :type lightTransform: str
    :param forceUnique:  will auto rename the light with a number if it is not unique in the whole scene
    :type forceUnique: str
    :return lightShape: A light's shape new node name
    :rtype lightShape: str
    """
    if lightFamily == AREALIGHTS:
        lightShape = getLightShape(lightTransform)
    elif lightFamily == IBLSKYDOMES:
        lightShape = getIblShape(lightTransform)
    elif lightFamily == DIRECTIONALS:
        lightShape = getDirectionalShape(lightTransform)
    renderNiceName = getRendererNiceNameFromLightShape(lightShape)
    if addSuffix:
        nameWithSuffix = "_".join([newName, RENDERER_SUFFIX[renderNiceName]])
        if nameWithSuffix != namehandling.getShortName(lightTransform):  # if names don't match

            # otherwise make sure unique name with suffix
            newName = namehandling.getUniqueNameSuffix(newName, RENDERER_SUFFIX[renderNiceName])
        else:  # don't rename, only rename shape nodes
            lightShape = shapenodes.renameShapeNodes(lightTransform)[0]
            return lightTransform, lightShape
    else:
        if namehandling.getShortName(lightTransform) != newName:
            newName = namehandling.nonUniqueNameNumber(newName)
        else:  # only rename the shape node
            lightShape = shapenodes.renameShapeNodes(lightTransform)[0]
            return lightTransform, lightShape
    if forceUnique:
        newName = namehandling.nonUniqueNameNumber(newName, shortNewName=False)  # be sure it's unique, keep longname
    lightTransform = cmds.rename(lightTransform, newName)
    lightShape = shapenodes.renameShapeNodes(lightTransform)[0]
    return lightTransform, lightShape


def renameIblLightSelected(newName, addSuffix, rendererNiceName, findIBLOutsideOfSelection=True):
    """Auto renames IBL lights given the renderer, will search the selection and if findIBLOutsideOfSelection=True
    then will find any IBLs in the scene.
    Must be one IBL found to rename, not multiple
    Will error if trying to rename itself with the same name and add _001

    :param newName: The incoming new name of the light
    :type newName: str
    :param addSuffix: add a suffix?  Will also remove/replace existing Renderer suffixes
    :type addSuffix: bool
    :param rendererNiceName: the renderer nice name "Arnold" etc
    :type rendererNiceName: str
    :param findIBLOutsideOfSelection: search IBLs in the scene if none found in the selection?
    :type findIBLOutsideOfSelection:
    """
    iblShapeList = getIblFromSelectedOrScene(rendererNiceName, findUnselected=findIBLOutsideOfSelection)
    if not iblShapeList:
        om2.MGlobal.displayWarning("No IBL Lights Selected And None Found. Please Select")
        return
    elif len(iblShapeList) != 1:
        om2.MGlobal.displayWarning("There is more than one IBL in this scene or selected, "
                                   "Please Select One IBL To Rename It.")
        return
    else:  # one IBL found
        IblTransformList = objhandling.getTransformListFromShapeNodes(iblShapeList)  # convert to transform
        renameLight(IblTransformList[0], newName, addSuffix=addSuffix, lightFamily=IBLSKYDOMES)
        om2.MGlobal.displayInfo("Success: Lights Renamed")
        return IblTransformList[0]


def renameLightSelected(newName, addSuffix=True):
    """Renames selected lights, handles the renderer suffix, also checks for non unique names and applies with numeric
    padding.
    Auto figures out the renderer light suffix
    RendererNiceName is not needed unless looking to rename an IBL that is not selected (findIBLOutsideOfSelection)

    :param newName: The incoming new name of the light
    :type newName: str
    :param addSuffix: add a suffix?  Will also remove/replace existing Renderer suffixes
    :type addSuffix: bool
    """
    selObjs = cmds.ls(selection=True, long=True)
    for obj in selObjs:
        lightShape = getLightShape(obj)
        if checkValidLightType(lightShape):
            lightTransform, lightShape = renameLight(obj, newName, addSuffix=addSuffix, lightFamily=AREALIGHTS)
            om2.MGlobal.displayInfo("Success: Lights Renamed")
            return lightTransform, lightShape
    om2.MGlobal.displayWarning("No Valid Lights Selected.  Please select Renderman, Arnold, Redshift "
                               "(Area, Directional or IBL) Lights")
    return


def renameDirectionalSelected(newName, rendererNiceName, addSuffix=True, message=True):
    """Renames selected lights, handles the renderer suffix, also checks for non unique names and applies with numeric
    padding.
    Auto figures out the renderer light suffix
    RendererNiceName is not needed unless looking to rename an IBL that is not selected (findIBLOutsideOfSelection)

    :param newName: The incoming new name of the light
    :type newName: str
    :param addSuffix: add a suffix?  Will also remove/replace existing Renderer suffixes
    :type addSuffix: bool
    """
    directionalTransformList, directionalShapeList = getSelectedDirectionalLights(rendererNiceName, message=True,
                                                                                  returnIfOneDirectional=True)
    if not directionalTransformList:  # messages already reported
        return
    for directionalTransform in directionalTransformList:
        renameLight(directionalTransform, newName, addSuffix=addSuffix, lightFamily=DIRECTIONALS)
        if message:
            transformListUnique = namehandling.getUniqueShortNameList(directionalTransformList)
            om2.MGlobal.displayInfo("Success: Lights Renamed: {}".format(transformListUnique))
        return
    return


def getLightName(lightTransform, removeSuffix=True):
    """Returns the light name with the suffix potentially removed

    :param lightTransform:  A light's transform node name
    :type lightTransform: str
    :param removeSuffix: Removes the suffix as per the renderer suffixes
    :type removeSuffix: bool
    :return lightTransform: A light's transform node name with the suffix potentially removed
    :rtype lightTransform: str
    :return suffixRemoved: bool True if the suffix was removed, False if it wasn't
    :rtype suffixRemoved: bool
    """
    suffixRemoved = False
    if removeSuffix:
        lightTransform, suffixRemoved = removeRendererSuffix(lightTransform)
    return lightTransform, suffixRemoved


def getLightNameSelected(removeSuffix=True, lightFamily=AREALIGHTS, rendererNiceName=None, message=False):
    """Returns the first light name found. Suffix can be removed for GUIs.

    :param removeSuffix: Removes the suffix as per the renderer suffixes
    :type removeSuffix: bool
    :return lightTransform: the first selected light's transform node name with the suffix potentially removed
    :rtype lightTransform: str
    :return suffixRemoved: bool True if the suffix was removed, False if it wasn't
    :rtype suffixRemoved: bool
    """
    suffixRemoved = False
    if lightFamily == DIRECTIONALS:  # special directional light finder
        selObj = findFirstDirectionalLight(cmds.ls(selection=True, long=True), rendererNiceName=rendererNiceName)
        if not selObj:
            if message and rendererNiceName:
                om2.MGlobal.displayWarning("No directional lights selected or found for {}. "
                                           "Please select".format(rendererNiceName))
            elif message and not rendererNiceName:
                om2.MGlobal.displayWarning("No directional lights selected or found. Please select")
            return None, suffixRemoved
    elif lightFamily == IBLSKYDOMES and rendererNiceName:  # special skydome light finder, finds unselected
        transforms, shapes = getIblLightSelected(rendererNiceName, includeSelChildren=False, returnFirstObj=False,
                                                 prioritizeName="", findUnselected=True)
        if transforms:
            selObj = transforms[0]
        else:  # return as transforms are None
            if message:
                om2.MGlobal.displayWarning("No IBL lights selected or found for {}. "
                                           "Please select".format(rendererNiceName))
            return None, suffixRemoved
    elif lightFamily == AREALIGHTS:
        selObj = findFirstAreaLight(cmds.ls(selection=True))
        if not selObj:
            if message:
                om2.MGlobal.displayWarning("No area lights selected or found for {}. "
                                           "Please select".format(rendererNiceName))
            return None, suffixRemoved
    if lightFamily == IBLSKYDOMES:
        lightShape = getIblShape(selObj)
        if not checkValidIblType(lightShape):
            if message:
                om2.MGlobal.displayWarning("No Valid Lights Selected, must be Renderman, Arnold, Redshift "
                                           "IBL Skydome Lights")
            return None, suffixRemoved
    selObj, suffixRemoved = getLightName(selObj, removeSuffix=removeSuffix)
    if message:
        transformUnique = namehandling.getUniqueShortName(selObj)
        om2.MGlobal.displayInfo("Success: Name Returned `{}`".format(transformUnique))
    return selObj, suffixRemoved


"""
LOCATOR GENERIC LIGHTS
"""


def getLocatorAttr(locatorTransform):
    """Gets the current light values of the locator
    Returns as a dictionary with all the light values in generic format
    """
    attrValDict = getLightDictAttributes()  # get empty dict to add values
    attrValDict[INTENSITY] = cmds.getAttr(".".join([locatorTransform, GENERICLIGHTATTRDICT[INTENSITY]]))
    attrValDict[EXPOSURE] = cmds.getAttr(".".join([locatorTransform, GENERICLIGHTATTRDICT[EXPOSURE]]))
    attrValDict[LIGHTCOLOR] = cmds.getAttr(".".join([locatorTransform, GENERICLIGHTATTRDICT[LIGHTCOLOR]]))[0]
    attrValDict[TEMPONOFF] = cmds.getAttr(".".join([locatorTransform, GENERICLIGHTATTRDICT[TEMPONOFF]]))
    attrValDict[TEMPERATURE] = cmds.getAttr(".".join([locatorTransform, GENERICLIGHTATTRDICT[TEMPERATURE]]))
    attrValDict[SHAPE] = cmds.getAttr(".".join([locatorTransform, GENERICLIGHTATTRDICT[SHAPE]]))
    attrValDict[NORMALIZE] = cmds.getAttr(".".join([locatorTransform, GENERICLIGHTATTRDICT[NORMALIZE]]))
    attrValDict[LIGHTVISIBILITY] = cmds.getAttr(".".join([locatorTransform, GENERICLIGHTATTRDICT[LIGHTVISIBILITY]]))
    attrValDict[SCALE] = cmds.getAttr("{}.scale".format(locatorTransform))[0]
    return attrValDict


def getAllLocsInScene():
    """returns all the generic area light locators with the suffix RENDERER_SUFFIX["Generic"] in the scene

    :return allLightLocs:  All light-locator transforms in the scene by name
    :rtype allLightLocs: list
    """
    lightLocatorList = cmds.ls("*_{}".format(RENDERER_SUFFIX["Generic"], long=True))
    return lightLocatorList


def cleanupLightLocators(lightLocatorList):
    """Cleans up light-locators by creating a grp or parents them the grp already exists
    from the given lightLocatorList

    :param lightLocatorList: a list of lightLocator Names
    :type lightLocatorList: list
    """
    if cmds.objExists(LOCGRPNAME):
        for locator in lightLocatorList:
            cmds.parent(locator, LOCGRPNAME)
    else:
        cmds.group(lightLocatorList, name=LOCGRPNAME)


"""
LIGHT ATTRIBUTE DICTIONARY
"""


def getLightAttr(lightShape, getIntensity=True, getExposure=True, getColor=True, getTemperature=True,
                 getTempOnOff=True, getShape=True, getNormalize=True, getLightVisible=True, getScale=True):
    """Gets the current value/s of the light as per the kwargs
    Returns as a dictionary with None as the attribute value if it hasn't been requested
    The returned dict is in generic format

    :param lightShape: the light shape node name
    :type lightShape: str
    :param getIntensity: return the intensity Value?
    :type getIntensity: bool
    :param getExposure: return Exposure Value if it exists?
    :type getExposure: bool
    :param getColor: return the color as (0.1, 0.1, 1.0) 0-1 tuple or list?
    :type getColor: bool
    :param getTemperature: the temperature value in kelvin 6500.0 for example
    :type getTemperature: float
    :param getTempOnOff: Is the temperature value being used on this light?
    :type getTempOnOff: bool
    :param getShape: return the type of geometric shape, rectangle, sphere etc?  Usually an int, see other functions
    :type getShape: return
    :param getNormalize:  Is the light normalized?  (size doesn't affect intensity)
    :type getNormalize: bool
    :param getLightVisible: Can the light be seen in the scene?  Arnold doesn't support this.
    :type getLightVisible: bool
    :param getScale: the physical scale of the light as a tuple/list
    :type getScale: bool
    :return attrValDict:  The dictionary of light attribute values in generic format, not renderer
    :rtype attrValDict: dict
    """
    attrValDict = getLightDictAttributes()  # get empty dict to add values
    rendererNiceName = getRendererNiceNameFromLightShape(lightShape)
    attrDict = getRendererAttrDict(rendererNiceName)
    if getIntensity:
        attrValDict[INTENSITY] = cmds.getAttr(".".join([lightShape, attrDict[INTENSITY]]))
    if getExposure:
        if rendererNiceName == REDSHIFT:  # if not Redshift
            if not redshiftAreaExposureExists(lightShape, attrDict):  # check if exposure exists
                attrValDict[EXPOSURE] = 0
            else:
                attrValDict[EXPOSURE] = cmds.getAttr(".".join([lightShape, attrDict[EXPOSURE]]))
        else:
            attrValDict[EXPOSURE] = cmds.getAttr(".".join([lightShape, attrDict[EXPOSURE]]))
    if getColor:
        attrValDict[LIGHTCOLOR] = cmds.getAttr(".".join([lightShape, attrDict[LIGHTCOLOR]]))[0]
    if getTempOnOff:
        attrValDict[TEMPONOFF] = cmds.getAttr(".".join([lightShape, attrDict[TEMPONOFF]]))
    if getTemperature:
        attrValDict[TEMPERATURE] = cmds.getAttr(".".join([lightShape, attrDict[TEMPERATURE]]))
    if getShape:
        if rendererNiceName == RENDERMAN:
            attrValDict[SHAPE] = fixRendermanGetLightShape(lightShape)[0]
        elif rendererNiceName == ARNOLD:
            attrValDict[SHAPE] = fixArnoldGetLightShape(lightShape)[0]
        else:
            attrValDict[SHAPE] = cmds.getAttr(".".join([lightShape, attrDict[SHAPE]]))
    if getNormalize:
        attrValDict[NORMALIZE] = cmds.getAttr(".".join([lightShape, attrDict[NORMALIZE]]))
    if getLightVisible:
        if rendererNiceName == ARNOLD:
            attrValDict[LIGHTVISIBILITY] = fixArnoldVisibility(attrDict, lightShape)
        else:
            attrValDict[LIGHTVISIBILITY] = cmds.getAttr(".".join([lightShape, attrDict[LIGHTVISIBILITY]]))
    if getScale:
        lightTransform = cmds.listRelatives(lightShape, parent=True, fullPath=True)[0]
        attrValDict[SCALE] = cmds.getAttr("{}.scale".format(lightTransform))[0]
        if rendererNiceName == RENDERMAN:
            # TODO add to fix renderman functions, messy being here
            attrValDict[SCALE] = (attrValDict[SCALE][0] / 2, attrValDict[SCALE][1] / 2, attrValDict[SCALE][2] / 2)
        if getShape:
            if attrValDict[SHAPE] == 3 and rendererNiceName == ARNOLD:  # cylinder and arnold
                # TODO add to fix arnold functions, messy being here
                x = ((attrValDict[SCALE])[0] + (attrValDict[SCALE])[2]) / 2  # can only be round
                z = ((attrValDict[SCALE])[0] + (attrValDict[SCALE])[2]) / 2  # can only be round
                attrValDict[SCALE] = (x, (attrValDict[SCALE])[1], z)
            elif attrValDict[SHAPE] == 3:
                if rendererNiceName == REDSHIFT:  # cylinder/disk and redshift
                    # TODO add to fix redshift functions, messy being here
                    scaleXOrig = (attrValDict[SCALE])[0]
                    x = (attrValDict[SCALE])[1]  # flip x and y scales
                    y = scaleXOrig  # flip x and y scales
                    attrValDict[SCALE] = (x, y, (attrValDict[SCALE])[2])
    return attrValDict


def getLightAttrList(lightShapeList, getIntensity=True, getExposure=True, getColor=True, getTemperature=True,
                     getTempOnOff=True, getShape=True, getNormalize=True, getLightVisible=True, getScale=True):
    """Returns a nested dictionary when each key is the are lightShape name.
    Each value is generic dictionaries of attribute values of the area lightShape

    :param lightShape: the light shape node name
    :type lightShape: str
    :param getIntensity: return the intensity Value?
    :type getIntensity: bool
    :param getExposure: return Exposure Value if it exists?
    :type getExposure: bool
    :param getColor: return the color as (0.1, 0.1, 1.0) 0-1 tuple or list?
    :type getColor: bool
    :param getTemperature: the temperature value in kelvin 6500.0 for example
    :type getTemperature: float
    :param getTempOnOff: Is the temperature value being used on this light?
    :type getTempOnOff: bool
    :param getShape: return the type of geometric shape, rectangle, sphere etc?  Usually an int, see other functions
    :type getShape: return
    :param getNormalize:  Is the light normalized?  (size doesn't affect intensity)
    :type getNormalize: bool
    :param getLightVisible: Can the light be seen in the scene?  Arnold doesn't support this.
    :type getLightVisible: bool
    :param getScale: the physical scale of the light as a tuple/list
    :type getScale: bool
    :return lightDictGenericValues:  A nested dict of attribute value dictionaries, with lightShapes as keys
    :rtype lightDictGenericValues: dict
    """
    lightDictGenericValues = dict()
    for lightShape in lightShapeList:
        lightDictGenericValues[lightShape] = getLightAttr(lightShape, getIntensity=getIntensity,
                                                          getExposure=getExposure, getColor=getColor,
                                                          getTemperature=getTemperature, getTempOnOff=getTempOnOff,
                                                          getShape=getShape, getNormalize=getNormalize,
                                                          getLightVisible=getLightVisible, getScale=getScale)
    return lightDictGenericValues


def getLightAttrSelected(getIntensity=False, getExposure=False, getColor=False, getTemperature=False,
                         getTempOnOff=False, getShape=False, getNormalize=False, getLightVisible=False, getScale=False,
                         message=False):
    """Gets the first selected area light's current attribute value/s as per the kwargs
    Returns as a dictionary with None as the attribute value if it hasn't been requested
    The returned dict is in generic format

    :param getIntensity: return the intensity Value?
    :type getIntensity: bool
    :param getExposure: return Exposure Value if it exists?
    :type getExposure: bool
    :param getColor: return the color as (0.1, 0.1, 1.0) 0-1 tuple or list?
    :type getColor: bool
    :param getTemperature: the temperature value in kelvin 6500.0 for example
    :type getTemperature: float
    :param getTempOnOff: Is the temperature value being used on this light?
    :type getTempOnOff: bool
    :param getShape: return the type of geometric shape, rectangle, sphere etc?  Usually an int, see other functions
    :type getShape: return
    :param getNormalize:  Is the light normalized?  (size doesn't affect intensity)
    :type getNormalize: bool
    :param getLightVisible: Can the light be seen in the scene?  Arnold doesn't support this.
    :type getLightVisible: bool
    :param getScale: the physical scale of the light as a tuple/list
    :type getScale: bool
    :param getScale: the physical scale of the light as a tuple/list
    :type getScale: bool
    :param message: report the messages to the user?
    :type message: bool
    :return attrValDict:  The dictionary of light attribute values in generic format, not renderer
    :rtype attrValDict: dict
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        if message:
            om2.MGlobal.displayWarning("No Valid Lights Selected.  Please select Renderman, Arnold, Redshift "
                                       "(Area, Directional or IBL) Lights")
    for obj in selObjs:
        if cmds.objectType(obj) != "transform":  # if not a transform node, it could be a shape node so try the parent
            obj = cmds.listRelatives(obj, parent=True, fullPath=True)
        lightShape = getLightShape(obj, lightFamily=AREALIGHTS)
        if checkValidLightType(lightShape):
            attrValDict = getLightAttr(lightShape, getIntensity=getIntensity, getExposure=getExposure,
                                       getColor=getColor,
                                       getTemperature=getTemperature, getTempOnOff=getTempOnOff,
                                       getShape=getShape, getNormalize=getNormalize,
                                       getLightVisible=getLightVisible, getScale=getScale)
            return attrValDict
    if message:
        om2.MGlobal.displayWarning("No Valid Lights Selected.  Please select Renderman, Arnold, Redshift "
                                   "(Area, Directional or IBL) Lights")


def getDirectionalAttr(lightShape, getIntensity=True, getColor=True, getTemperature=True,
                       getTempOnOff=True, getAngleSoft=True, getRotation=True):
    """Gets the current value/s of the directional light as per the kwargs
    Returns as a dictionary with None as the attribute value if it hasn't been requested
    The returned dict is in generic format

    :param lightShape: the light shape node name
    :type lightShape: str
    :param getIntensity: return the intensity Value?
    :type getIntensity: bool
    :param getColor: return the color as (0.1, 0.1, 1.0) 0-1 tuple or list?
    :type getColor: bool
    :param getTemperature: the temperature value in kelvin 6500.0 for example
    :type getTemperature: float
    :param getTempOnOff: Is the temperature value being used on this light?
    :type getTempOnOff: bool
    :param getAngleSoft: get the directional softness (angle) value
    :type getAngleSoft: bool
    :param getRotation: the rotation of the directional light as a tuple/list
    :type getRotation: bool
    :return attrValDict:  The dictionary of light attribute values in generic format, not renderer
    :rtype attrValDict: dict
    """
    attrValDict = getDirectionalDictAttributes()  # get empty dict to add values
    rendererNiceName = getRendererNiceNameFromLightShape(lightShape)
    attrDict = getRendererDirectionalAttrDict(rendererNiceName)
    if getIntensity:  # will have to do some conversion here as renderers have different intensity values
        attrValDict[INTENSITY] = cmds.getAttr(".".join([lightShape, attrDict[INTENSITY]]))
        if rendererNiceName == RENDERMAN:  # fix Renderman
            attrValDict[INTENSITY] = fixGetRendermanIntensity(attrValDict[INTENSITY])
        if rendererNiceName == ARNOLD:  # fix Arnold
            attrValDict[INTENSITY] = fixGetArnoldIntensity(attrValDict[INTENSITY])
    if getColor:
        attrValDict[LIGHTCOLOR] = cmds.getAttr(".".join([lightShape, attrDict[LIGHTCOLOR]]))[0]
    if getTempOnOff:
        attrValDict[TEMPONOFF] = cmds.getAttr(".".join([lightShape, attrDict[TEMPONOFF]]))
    if getTemperature:
        attrValDict[TEMPERATURE] = cmds.getAttr(".".join([lightShape, attrDict[TEMPERATURE]]))
    if getAngleSoft:
        attrValDict[ANGLE_SOFT] = cmds.getAttr(".".join([lightShape, attrDict[ANGLE_SOFT]]))
    if getRotation:
        lightTransform = cmds.listRelatives(lightShape, parent=True, fullPath=True)[0]
        attrValDict[ROTATE] = cmds.getAttr("{}.rotate".format(lightTransform))[0]
    return attrValDict


def getDirectionalAttrList(lightShapeList, getIntensity=True, getColor=True, getTemperature=True,
                           getTempOnOff=True, getAngleSoft=True, getRotation=True):
    """Returns a nested dictionary when each key is the is a directional lightShape name.
    Each value is generic dictionaries of attribute values of the directional lightShape

    :param lightShapeList: list of directional light shape node names
    :type lightShapeList: list
    :param lightShape: the light shape node name
    :type lightShape: str
    :param getIntensity: return the intensity Value?
    :type getIntensity: bool
    :param getColor: return the color as (0.1, 0.1, 1.0) 0-1 tuple or list?
    :type getColor: bool
    :param getTemperature: the temperature value in kelvin 6500.0 for example
    :type getTemperature: float
    :param getTempOnOff: Is the temperature value being used on this light?
    :type getTempOnOff: bool
    :param getAngleSoft: get the directional softness (angle) value
    :type getAngleSoft: bool
    :param getRotation: the rotation of the directional light as a tuple/list
    :type getRotation: bool
    :return directionalDictGenericValues:   A nested dict of attribute value dictionaries, with lightShapes as keys
    :rtype : dict
    """
    directionalDictGenericValues = dict()
    for lightShape in lightShapeList:
        directionalDictGenericValues[lightShape] = getDirectionalAttr(lightShape, getIntensity=getIntensity,
                                                                      getColor=getColor, getTemperature=getTemperature,
                                                                      getTempOnOff=getTempOnOff,
                                                                      getAngleSoft=getAngleSoft,
                                                                      getRotation=getRotation)
    return directionalDictGenericValues


def getDirectionalAttrSelected(rendererNiceName, getIntensity=True, getColor=True, getTemperature=True,
                               getTempOnOff=True, getAngleSoft=True, getRotation=True, message=True,
                               returnFirstLight=False):
    """From the slected directional lights, returns a nested dictionary when each key is the is a directional
    lightShape name.  Each value is generic dictionaries of attribute values of the directional lightShape

    :param lightShapeList: list of directional light shape node names
    :type lightShapeList: list
    :param lightShape: the light shape node name
    :type lightShape: str
    :param getIntensity: return the intensity Value?
    :type getIntensity: bool
    :param getColor: return the color as (0.1, 0.1, 1.0) 0-1 tuple or list?
    :type getColor: bool
    :param getTemperature: the temperature value in kelvin 6500.0 for example
    :type getTemperature: float
    :param getTempOnOff: Is the temperature value being used on this light?
    :type getTempOnOff: bool
    :param getAngleSoft: get the directional softness (angle) value
    :type getAngleSoft: bool
    :param getRotation: the rotation of the directional light as a tuple/list
    :type getRotation: bool
    :param message: return messages due to selection to the user?
    :type message: bool
    :param returnFirstLight: returns only the attr dict from the first light selected
    :type returnFirstLight: bool
    :return directionalDictGenericValues:   A nested dict of attribute value dictionaries, with lightShapes as keys
    :rtype : dict
    """
    directionalTransformList, directionalShapeList = getSelectedDirectionalLights(rendererNiceName, message=message,
                                                                                  returnIfOneDirectional=True,
                                                                                  returnFirstLight=returnFirstLight)
    if not directionalTransformList:
        return dict()
    directionalDictGenericValues = getDirectionalAttrList(directionalShapeList, getIntensity=getIntensity,
                                                          getColor=getColor, getTemperature=getTemperature,
                                                          getTempOnOff=getTempOnOff, getAngleSoft=getAngleSoft,
                                                          getRotation=getRotation)
    return directionalDictGenericValues


def getLightAttrFromLocator(locatorTransform, rendererNiceName=None):
    """From the given locator retrieve a single generic light dict
    returned dict includes the custom light attributes with translation, scale and rotation attributes as well

    :param locTransform: a generic light locator name "_lgtLc" with the custom light attributes
    :type locTransform: str
    :return singleLightDict:  A dict with attributes and values for one light only
    :rtype singleLightDict: dict
    """
    singleLightDict = dict()
    for key, attr in GENERICLIGHTATTRDICT.items():
        singleLightDict[key] = cmds.getAttr(".".join([locatorTransform, attr]))
        if SRGBSUFFIX in key:  # it's in a nested tuple-list so remove ?? Don't like this, affects and lists (0,0,0)
            singleLightDict[key] = singleLightDict[key][0]
    for attr in attributes.MAYATRANSFORMATTRS:  # this is a list of rot translate and scale attrs
        singleLightDict[attr] = cmds.getAttr(".".join([locatorTransform, attr]))
    if rendererNiceName == ARNOLD:
        locLightShape = cmds.getAttr(".".join([locatorTransform, GENERICLIGHTATTRDICT[SHAPE]]))
        objScale = None
        if locLightShape == 3:  # if arnold and a cylinder then the scales x and z should be the same
            objScale = cmds.getAttr(".".join([locatorTransform, "scale"]))[0]
            newXZScale = (objScale[0] + objScale[2]) / 2
            objScale = (newXZScale, objScale[1], newXZScale)
        elif locLightShape == 1:  # if arnold and a disk then the scales x and y should be the same
            objScale = cmds.getAttr(".".join([locatorTransform, "scale"]))[0]
            newXZScale = (objScale[0] + objScale[1]) / 2
            objScale = (newXZScale, newXZScale, objScale[2])
        if objScale:
            cmds.setAttr(".".join([locatorTransform, "scale"]), objScale[0], objScale[1], objScale[2])
            singleLightDict["scaleX"] = objScale[0]
            singleLightDict["scaleY"] = objScale[1]
            singleLightDict["scaleZ"] = objScale[2]
    return singleLightDict


def getLightAttrFromLocatorList(locatorTransformList, rendererNiceName=None):
    """retrieves the attributes of a list of "_lgtLc" locators and puts them in a nested dictionary
    multiLightDict keys are the locator names minus the suffix,
    multiLightDict values is a dictionary of attributes and with attrValues

    :param locTransformList: list of generic light locator names "_lgtLc"
    :type locTransformList: list
    :return multiLightDict: a nested dictionary of locator names and then attributes and attrValues
    :rtype multiLightDict: dict
    """
    multiLightDict = dict()
    for loc in locatorTransformList:
        locNameNoSuffix = namehandling.stripSuffixExact(loc, RENDERER_SUFFIX["Generic"])
        multiLightDict[locNameNoSuffix] = getLightAttrFromLocator(loc, rendererNiceName=rendererNiceName)
    return multiLightDict


def getLightAttrFromLocatorSelected():
    """from selected light-locators in the scene retrieve their values and return as a nested dict
    multiLightDict keys are the locator names minus the suffix,
    multiLightDict values is a dictionary of attributes and with attrValues

    :return multiLightDict: a nested dictionary of locator names and then attributes and attrValues
    :rtype multiLightDict: dict
    """
    selObj = cmds.ls(selection=True, long=True)
    suffix = "_{}".format(RENDERER_SUFFIX["Generic"])
    locatorList = list()
    if not selObj:
        om2.MGlobal.displayWarning("Nothing Selected. Please Select Light-Locators")
        return
    for i, obj in enumerate(selObj):
        if suffix in obj:
            locatorList.append(obj)
    if not locatorList:
        om2.MGlobal.displayWarning("No Light-Locators found in selection, please select light-locators")
        return
    return getLightAttrFromLocatorList(locatorList)


def getLightAttrFromLocatorScene(rendererNiceName, message=True):
    """from all area lights in the scene of the given renderer `self.renderer` retrieve their values and
    return as a nested dict

    multiLightDict keys are the locator names minus the suffix,
    multiLightDict values is a dictionary of attributes and with attrValues
    This function returns rotation and translate values in world coords

    :param rendererNiceName: the renderer nice name "Redshift", "Arnold", "Renderman"
    :type rendererNiceName: str
    :return multiLightDict: a nested dictionary of locator names and then attributes and attrValues
    :rtype multiLightDict: dict
    """
    deleteAllLightLocsInScene()
    lightLocatorList, warning = createLocatorLightScene(rendererNiceName, message=message)
    if warning:
        return
    multiLightDict = getLightAttrFromLocatorList(lightLocatorList, rendererNiceName=rendererNiceName)
    deleteAllLightLocsInScene()
    return multiLightDict


def getLightAttrFromLightSelected(rendererNiceName, includeSelChildren=False, message=True):
    """from the selected area lights in the scene of the given renderer `self.renderer` retrieve their values and
    return as a nested dict
    multiLightDict keys are the locator names minus the suffix,
    multiLightDict values is a dictionary of attributes and with attrValues

    :param rendererNiceName: the renderer nice name "Redshift", "Arnold", "Renderman"
    :type rendererNiceName: str
    :return multiLightDict: a nested dictionary of locator names and then attributes and attrValues
    :rtype multiLightDict: dict
    """
    selObjsOrig = cmds.ls(selection=True, long=True)
    if includeSelChildren:
        selObjs = objhandling.returnSelectLists(selectFlag="hierarchy")[0]
        cmds.select(selObjs, replace=True)
    deleteAllLightLocsInScene()
    lightTransformList, lightShapeList = getSelectedAreaLights(rendererNiceName, message=False)
    if not lightTransformList:
        return dict()
    lightLocList, warning = createLocatorForAreaLightList(lightTransformList, rendererNiceName)
    if not lightLocList:
        return dict()
    multiLightDict = getLightAttrFromLocatorList(lightLocList)
    deleteAllLightLocsInScene()
    cmds.select(selObjsOrig, replace=True)  # back to original selection
    return multiLightDict


def setLightAttr(lightShape, attrValDict, ignoreIntensity=False):
    """Sets the lights attributes as passed in from the dict genieric "attrValDict" for area lights
    This function does all the checking and converting to set the attributes correctly for the renderer
    Renderer is auto found from the light shape
    **Note, this will pop dict values, so any reusable dicts should be duplicated before passing in data

    :param lightShape: The name of the light shape
    :type lightShape: str
    :param attrValDict: the incoming generic dictionary, None values will be ignored
    :type attrValDict: dict
    :param ignoreIntensity: Only for Redshift if setting as pure exposure, this needs to be set to convert Redshift
    :type ignoreIntensity: bool
    :return createWarning: Should warnings be displayed to the user? Ie have warnings occurred? could be multiple
    :rtype createWarning: bool
    """
    createWarning = False
    rendererNiceName = getRendererNiceNameFromLightShape(lightShape)
    attrDict = getRendererAttrDict(rendererNiceName)
    # pop scale as it isn't part of the generic dict, but may be in the incoming attrValDict
    if SCALE in attrValDict:
        scale = attrValDict[SCALE]
        attrValDict.pop(SCALE, None)
    else:
        scale = None
    # pop rotate as it isn't part of the generic dict, but may be in the incoming attrValDict
    # ----------------
    # fix Arnold
    # ----------------
    if rendererNiceName == ARNOLD:  # fix the SHAPE attribute to string, Arnold also doesn't have light render vis
        attrValDict, createWarning = fixArnoldAttrs(attrValDict, warningState=createWarning)
        if attrValDict[LIGHTVISIBILITY] is not None:  # check if attr exists in newer versions of Arnold
            if not arnoldVisibilityExists(attrDict, lightShape):
                attrValDict.pop(LIGHTVISIBILITY, None)  # older versions of Arnold have no light visibility attr
                createWarning = True
                om2.MGlobal.displayWarning("This version of Arnold has no `light render visibility` attribute, "
                                           "it cannot be visible")
    # ----------------
    # fix Renderman
    # ----------------
    if rendererNiceName == RENDERMAN:
        if attrValDict[SHAPE] is not None:  # potential fix the SHAPE attribute to string
            if attrValDict[SHAPE] != fixRendermanGetLightShape(lightShape, warningState=False)[0]:  # shapes no match
                attrValDict, createWarning = fixRendermanAttrs(attrValDict, warningState=createWarning)
                # delete the dict key entry for shape after recording the value which is now a string
                lightTransform = cmds.listRelatives(lightShape, parent=True, fullPath=True)[0]
                lightTransform, lightShape, createWarning = fixRendermanShape(lightTransform, attrValDict[SHAPE],
                                                                              warningState=createWarning,
                                                                              keepPosition=True)  # deletes/creates new light
            attrValDict.pop(SHAPE, None)  # delete the shape from attrValDict
        # v21 fix for primaryVis attribute which is updated in version 22
        attrDict = fixRendermanLightVisAttr(attrDict, lightShape)
    # ----------------
    # fix Redshift
    # ----------------
    if rendererNiceName == REDSHIFT:  # Redshift has no light exposure attr in early versions
        attrValDict = fixRedshiftAreaSetExposure(attrValDict, lightShape, attrDict)
        scale = fixRedshiftAreaCylinder(attrValDict, scale, lightShape)  # fix scale and orientation if cylinder
    # ----------------
    # Set the attributes if not none
    # ----------------
    if ignoreIntensity:  # a hack override, older versions of Redshift need intensity when exposing
        if rendererNiceName == REDSHIFT:
            if redshiftAreaExposureExists(lightShape, attrDict):  # then exposure exists in new Redshift
                attrValDict[INTENSITY] = None
        else:
            attrValDict[INTENSITY] = None
    for genericAttr, value in attrValDict.items():
        if value is not None:
            attributes.setAttrAutoType(lightShape, attrDict[genericAttr], value, message=False)
    # ----------------
    # set the name and scale if not None
    # ----------------
    if scale is not None:
        lightTransform = cmds.listRelatives(lightShape, parent=True, fullPath=True)[0]
        if rendererNiceName == RENDERMAN:
            scale = (scale[0] * 2, scale[1] * 2, scale[2] * 2)

        cmds.setAttr("{}.scale".format(lightTransform), scale[0], scale[1], scale[2], type="double3")
    if createWarning:  # there's been a problem if this is True
        om2.MGlobal.displayWarning("Lights Set With Warnings, See Script Editor For Details")
    else:
        shapeUnique = namehandling.getUniqueShortName(lightShape)
        om2.MGlobal.displayInfo("Success: Light Shape Attributes Set `{}`".format(shapeUnique))
    return createWarning


def setLightAttrSelected(attrValDict, ignoreIntensity=False):
    """Sets the lights attributes as passed in from the dict genieric "attrValDict" on selected lights
    This function does all the checking and converting to set the attributes correctly for the renderer
    Renderer is auto found from the selection
    **Note, this will pop dict values, so any reusable dicts should be duplicated before passing in data

    :param attrValDict: the incoming generic dictionary, None values will be ignored
    :type attrValDict: dict
    :param ignoreIntensity: Only for Redshift if setting as pure exposure, this needs to be set to convert Redshift
    :type ignoreIntensity: bool
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        om2.MGlobal.displayWarning("No Lights Selected Please Select")
    for obj in selObjs:
        if cmds.objectType(obj) != "transform":  # if not a transform node, it could be a shape node so try the parent
            obj = cmds.listRelatives(obj, parent=True, fullPath=True)
        lightShape = getLightShape(obj)
        if checkValidLightType(lightShape):
            # duplicate dict because setLightAttr pops keys which is bad for loops
            tempDict = dict(attrValDict)
            setLightAttr(lightShape, tempDict, ignoreIntensity=ignoreIntensity)


def setDirectionalAttr(lightShape, rendererNiceName, attrValDict):
    """sets the attributes for directional lights.  sets automatically from the attrValDict, in dict key values are
    None then skips the setting

    :param lightShape: the lightShape node name to be set
    :type lightShape: str
    :param rendererNiceName: the renderer nice name "Redshift", "Arnold", "Renderman"
    :type rendererNiceName: str
    :param attrValDict: the incoming generic dictionary with attribute values, None values will be ignored
    :type attrValDict: dict
    """
    # pop rotate as it needs to be set on the transform node instead.
    attrDict = getRendererDirectionalAttrDict(rendererNiceName)
    if ROTATE in attrValDict:
        rotate = attrValDict[ROTATE]
        attrValDict.pop(ROTATE, None)
    else:
        rotate = None
    # ----------------
    # Cap min value of light angle
    # ----------------
    if attrValDict[ANGLE_SOFT] is not None and attrValDict[ANGLE_SOFT] <= 0:
        attrValDict[ANGLE_SOFT] = 0.0
    # ----------------
    # Fix Arnold
    # ----------------
    if rendererNiceName == ARNOLD:
        if attrValDict[INTENSITY] is not None:
            attrValDict[INTENSITY] *= 3.13
    # ----------------
    # Fix Renderman
    # ----------------
    if rendererNiceName == RENDERMAN:
        if attrValDict[INTENSITY] is not None:  # renderman intensity is 50000 x
            attrValDict[INTENSITY] *= 46000.0  # actually 37400.0 tech matches up as a note
        if attrValDict[TEMPONOFF] is not None:
            if attrValDict[TEMPONOFF] == 1:  # set the color to white if renderman as it combines with temp
                attrValDict[LIGHTCOLOR] = (1.0, 1.0, 1.0)
        if attrValDict[ANGLE_SOFT] is not None:
            if attrValDict[ANGLE_SOFT] == 0:  # Renderman can't handle a light Angle of 0, the light goes out
                attrValDict[ANGLE_SOFT] = 0.1
    # ----------------
    # Set Shape Attrs
    # ----------------
    for genericAttr, value in attrValDict.items():
        if value is not None:
            attributes.setAttrAutoType(lightShape, attrDict[genericAttr], value, message=False)
    # ----------------
    # Set The Transform Attrs
    # ----------------
    if rotate is not None:
        lightTransform = cmds.listRelatives(lightShape, parent=True, fullPath=True)[0]
        cmds.setAttr("{}.rotate".format(lightTransform), rotate[0], rotate[1], rotate[2], type="double3")


def setDirectionalAttrSelected(attrValDict, rendererNiceName, ignoreIntensity=False):
    """Sets the directional lights attributes as passed in from the dict generic "attrValDict" on selected lights
    This function does all the checking and converting to set the attributes correctly for the renderer
    Renderer is auto found from the selection
    **Note, this will pop dict values, so any reusable dicts should be duplicated before passing in data

    :param attrValDict: the incoming generic dictionary, None values will be ignored
    :type attrValDict: dict
    :param ignoreIntensity: Only for Redshift if setting as pure exposure, this needs to be set to convert Redshift
    :type ignoreIntensity: bool
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        # find directionals in scene
        om2.MGlobal.displayWarning("No Directional Lights Selected Please Select")
    for obj in selObjs:
        if cmds.objectType(obj) != "transform":  # if not a transform node, it could be a shape node so try the parent
            obj = cmds.listRelatives(obj, parent=True, fullPath=True)
        lightShape = getLightShape(obj)
        if checkValidLightType(lightShape):
            if cmds.nodeType(lightShape) == "RedshiftPhysicalLight":  # check because could be an area light
                if cmds.getAttr("{}.lightType".format(lightShape)) != 3:  # then is a directional
                    break
            # duplicate dict because setLightAttr pops keys which is bad for loops
            tempDict = dict(attrValDict)
            setLightAttr(lightShape, tempDict, ignoreIntensity=ignoreIntensity)


def getIblAttr(lightShape, getIntensity=True, getExposure=True, getColor=True, getLightVisible=True, getIblTexture=True,
               getTranslation=True, getRotation=True, getScale=True):
    """gets attributes in generic format from IBL Skydome lightshape, multi renderer compatible

    :param lightShape: name of the light's shape node
    :type lightShape: str
    :param getIntensity: get the intensity value and add to the returned dict?
    :type getIntensity: bool
    :param getExposure: get exposure value and add to the returned dict?
    :type getExposure: bool
    :param getColor: get color and add to the returned dict rgb? (0.1, 1.0, 0.5)
    :type getColor: bool
    :param getLightVisible: get light visibility and add to the returned dict?
    :type getLightVisible: bool
    :param getIblTexture: get the full file path of the IBL texture and add to the returned dict?
    :type getIblTexture: bool
    :param getTranslation: get translation and add to the returned dict?
    :type getTranslation: bool
    :param getRotation: get rotation and add to the returned dict?
    :type getRotation: bool
    :param getScale: get rotation and add to the returned dict?
    :type getScale: bool
    :return attrValDict: dictionary with updated values, unused attributes will be None
    :rtype attrValDict: dict
    """
    attrValDict = getSkydomeLightDictAttributes()  # get empty dict to add values
    rendererNiceName = getRendererNiceNameFromLightShape(lightShape)
    attrDict = getRendererAttrDictSkydome(rendererNiceName)
    lightTransform = cmds.listRelatives(lightShape, parent=True, fullPath=True)[0]
    if getIntensity:
        if rendererNiceName == REDSHIFT:  # redshift ibl is a color, convert to hsv and grab value
            attrValDict[INTENSITY] = (cmds.getAttr(".".join([lightShape, attrDict[INTENSITY]])))[0]
            hsv = colour.convertRgbToHsv(attrValDict[INTENSITY])
            attrValDict[INTENSITY] = hsv[2]  # grab the value
        else:
            attrValDict[INTENSITY] = cmds.getAttr(".".join([lightShape, attrDict[INTENSITY]]))
    if getExposure:  # ibl??  Not sure if exposure is used anywhere
        if rendererNiceName != REDSHIFT:
            attrValDict[EXPOSURE] = cmds.getAttr(".".join([lightShape, attrDict[EXPOSURE]]))
    if getColor:
        if rendererNiceName == REDSHIFT or rendererNiceName == ARNOLD:
            # redshift's color is intensity so set to color to one
            # arnolds's color is the map and it doesn't have tint, could be done in nodes
            attrValDict[LIGHTCOLOR] = (1.0, 1.0, 1.0)
        else:
            attrValDict[LIGHTCOLOR] = cmds.getAttr(".".join([lightShape, attrDict[LIGHTCOLOR]]))[0]
    if getLightVisible:
        attrValDict[LIGHTVISIBILITY] = cmds.getAttr(".".join([lightShape, attrDict[LIGHTVISIBILITY]]))
        if rendererNiceName == ARNOLD:  # round to one or zero, no floats are supported
            int(round(attrValDict[LIGHTVISIBILITY]))
    if getIblTexture:
        if rendererNiceName != ARNOLD:
            attrValDict[IBLTEXTURE] = cmds.getAttr(".".join([lightShape, attrDict[IBLTEXTURE]]))
        else:
            attrValDict[IBLTEXTURE] = textures.getFileTextureNameFromAttr(lightShape, attrDict[IBLTEXTURE])
    if getTranslation:
        attrValDict[TRANSLATE] = cmds.getAttr("{}.translate".format(lightTransform))[0]
    if getRotation:
        attrValDict[ROTATE] = cmds.getAttr("{}.rotate".format(lightTransform))[0]
        if rendererNiceName == REDSHIFT:  # add 90 degrees to Redshift while getting
            attrValDict[ROTATE] = (attrValDict[ROTATE][0], attrValDict[ROTATE][1] + 90, attrValDict[ROTATE][2])
        if rendererNiceName == RENDERMAN:
            attrValDict[ROTATE] = fixGetRendermanIBLRot(attrValDict[ROTATE])
    if getScale:
        attrValDict[SCALE] = cmds.getAttr("{}.scale".format(lightTransform))[0]
        if rendererNiceName == RENDERMAN:  # invert scaleZ since Renderman IBLs are inverted, scale is / 2000
            attrValDict[SCALE] = fixGetRendermanIBLScale(attrValDict[SCALE])
    return attrValDict


def getIblAttrSelected(rendererNiceName, getIntensity=True, getExposure=True, getColor=True, getLightVisible=True,
                       getIblTexture=True, getTranslation=True, getRotation=True, getScale=True, message=True):
    """Gets the first selected IBL light's attribute values and returns as a dict
    Unused values are stored as None

    :param getIntensity: get the intensity value and add to the returned dict?
    :type getIntensity: bool
    :param getExposure: get exposure value and add to the returned dict?
    :type getExposure: bool
    :param getColor: get color and add to the returned dict rgb? (0.1, 1.0, 0.5)
    :type getColor: bool
    :param getLightVisible: get light visibility and add to the returned dict?
    :type getLightVisible: bool
    :param getIblTexture: get the full file path of the IBL texture and add to the returned dict?
    :type getIblTexture: bool
    :param getTranslation: get translation and add to the returned dict?
    :type getTranslation: bool
    :param getRotation: get rotation and add to the returned dict?
    :type getRotation: bool
    :param getScale: get rotation and add to the returned dict?
    :type getScale: bool
    :param message: report the message to the user?
    :type message: bool
    :return attrValDict: dictionary with updated values, unused attributes will be None
    :rtype attrValDict: dict
    """
    iblShapeList = getIblFromSelectedOrScene(rendererNiceName, findUnselected=True)
    if not iblShapeList:
        if message:
            om2.MGlobal.displayWarning("No IBL Lights Found, Please Create Or Select")
        return
    if len(iblShapeList) is not 1:
        if message:
            om2.MGlobal.displayWarning("More Than One IBL Found, Please Select One IBL")
        return
    attrValDict = getIblAttr(iblShapeList[0], getIntensity=getIntensity, getExposure=getExposure, getColor=getColor,
                             getLightVisible=getLightVisible, getIblTexture=getIblTexture,
                             getTranslation=getTranslation, getRotation=getRotation, getScale=getScale)
    return attrValDict


def checkIBLTextureFound(iblTexturePath):
    """Checks if the IBL path exists, if it doesn't check to see if the file exists in the IBL presets folder

    :param iblTexturePath: the full path with the file to the ibl texture
    :type iblTexturePath: str
    :return iblTexturePath: the ibl path if not found & in the prefs direct then will be a new path
    :rtype iblTexturePath: str
    """
    if os.path.isfile(iblTexturePath):
        return iblTexturePath
    fileName = os.path.split(iblTexturePath)[-1]
    try:
        prefsIblFilePath = os.path.join(os.environ['ZOO_PREFS_IBLS_PATH'], fileName)
    except KeyError:  # No IBL os.env variable so ignore, may happen if using default assets
        prefsIblFilePath = iblTexturePath
    if os.path.isfile(prefsIblFilePath):
        om2.MGlobal.displayWarning(
            "Ibl file texture does not exist, switching to IBL Prefs Path: {}".format(prefsIblFilePath))
        return prefsIblFilePath
    om2.MGlobal.displayWarning("Ibl file texture does not exist: {}".format(iblTexturePath))
    return iblTexturePath


def setIblAttr(lightShape, attrValDict, invertScaleZ=False):
    """Given a shape node, it will set the attributes of an IBL, HDRI Skydome light from the attrValDict dictionary
    Automatically detects the renderer from the light node

    :param lightShape: The light shape node of the IBL light
    :type lightShape: str
    :param attrValDict: The generic attribute dictionary of the light
    :type attrValDict: dict
    :param invertScaleZ: Will invert the scale of the light causing the texture to display backwards
    :type invertScaleZ: bool
    """
    if attrValDict[IBLTEXTURE]:
        attrValDict[IBLTEXTURE] = checkIBLTextureFound(attrValDict[IBLTEXTURE])
    rendererNiceName = getRendererNiceNameFromLightShape(lightShape)
    attrDict = getRendererAttrDictSkydome(rendererNiceName)
    lightTransform = cmds.listRelatives(lightShape, parent=True, fullPath=True)[0]
    # pop scale as it isn't part of the generic dict, but may be in the incoming attrValDict
    translate = attrValDict[TRANSLATE]
    rotate = attrValDict[ROTATE]
    scale = attrValDict[SCALE]
    if invertScaleZ and scale is not None and scale[2] > 0:
        scale = (scale[0], scale[1], scale[2] * -1)
    elif not invertScaleZ and scale is not None and scale[2] < 0:
        scale = (scale[0], scale[1], scale[2] * -1)
    attrValDict.pop(TRANSLATE, None)
    attrValDict.pop(ROTATE, None)
    attrValDict.pop(SCALE, None)
    if rendererNiceName == ARNOLD:  # Fix Arnold - needs to set the IBL image as a texture node
        attrValDict = fixArnoldIBLTexture(lightShape, attrValDict)
    if rendererNiceName == REDSHIFT:  # Fix Redshift's intensity
        attrValDict = fixRedshiftIblIntensity(attrValDict)
        rotate = fixRedshiftIblRot(rotate)
    if rendererNiceName == RENDERMAN:  # Fix RENDERMAN's scale and rot check for changed attributes in v22
        scale = fixRendermanIBLScale(scale)
        rotate = fixRendermanIBLRot(rotate)
        # check IBL vis attribute LIGHTVISIBILITY for v22 change
        try:
            cmds.getAttr(".".join([lightShape, attrDict[LIGHTVISIBILITY]]))
        except ValueError:  # will be version 22 so replace with version 21 attribute
            attrDict[LIGHTVISIBILITY] = "rman__riattr__visibility_camera"
    # Set the attributes if not none
    for genericAttr, value in attrValDict.items():
        if value is not None:
            attributes.setAttrAutoType(lightShape, attrDict[genericAttr], value, message=False)
    # set trans rot scale if not None
    if translate is not None:
        cmds.setAttr("{}.translate".format(lightTransform), translate[0], translate[1], translate[2], type="double3")
    if rotate is not None:
        cmds.setAttr("{}.rotate".format(lightTransform), rotate[0], rotate[1], rotate[2], type="double3")
    if scale is not None:
        cmds.setAttr("{}.scale".format(lightTransform), scale[0], scale[1], scale[2], type="double3")


def setIBLAttrList(attrValDict, iblShapeList, invertScaleZ=False):
    """Sets the attributes to a list of IBLs

    :param attrValDict: The generic attribute dictionary of the light
    :type attrValDict: str
    :param invertScaleZ: Will invert the scale of the light causing the texture to display backwards
    :type invertScaleZ: bool
    :param iblShapeList: a list of valid IBL nodes
    :type iblShapeList: list
    """
    for iblLightShape in iblShapeList:
        # duplicate dict because setLightAttr pops keys which is bad for loops
        tempDict = dict(attrValDict)
        setIblAttr(iblLightShape, tempDict, invertScaleZ=invertScaleZ)


def setIblAttrSelected(attrValDict, invertScaleZ=False):
    """Sets the attributes of an IBL, HDRI Skydome light from the attrValDict dictionary
    Works on the selected ibl light
    Automatically detects the renderer from the light node
    Automatically detects if the select contains a valid IBL dome light

    :param attrValDict: The generic attribute dictionary of the light
    :type attrValDict: str
    :param invertScaleZ: Will invert the scale of the light causing the texture to display backwards
    :type invertScaleZ: bool
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        om2.MGlobal.displayWarning("No IBL Lights Selected Please Select")
        return
    iblShapeList = filterIblLightInList(selObjs)
    if not iblShapeList:
        om2.MGlobal.displayWarning("Current selection is not a valid IBL skydome light")
        return
    setIBLAttrList(attrValDict, iblShapeList, invertScaleZ=invertScaleZ)
    cmds.select(selObjs, replace=True)


def setIblAttrAuto(attrValDict, rendererNiceName, invertScaleZ=False, findUnselected=True, autoCreate=True,
                   createName="skydomeLight", prioritizeName="", addSuffix=True, returnFirstObj=False, message=True):
    """intelligently sets the attributes of ibl lights on the selected IBLs with the following options:

        prioritizeName: will include this obj name even if it's not selected (usually from a GUI)
        findUnselected: will return a light if none found and only one light exists in the scene
        returnFirstObj: will return the first obj found (usually for GUI)
        includeSelChildren: will search the children of the selected objs
        autoCreate: will automatically create a light if none found, be careful setting other kwargs if True

    Note: getIblLightSelected() does something very similar to this function, it just doesn't set the light attributes

    :param attrValDict: The generic attribute dictionary of the light
    :type attrValDict: str
    :param rendererNiceName: the renderer nice name "Redshift", "Arnold", "Renderman"
    :type rendererNiceName: str
    :param invertScaleZ: Will invert the scale of the light causing the texture to display backwards
    :type invertScaleZ: bool
    :param findUnselected: if nothing is selected will try to find the only light in the scene
    :type findUnselected: bool
    :param autoCreate: will automatically create a light if none found, be careful setting other kwargs if True
    :type autoCreate: bool
    :param createName: if autoCreate is True then this is the name of the light to be created
    :type createName: bool
    :param prioritizeName: tries to select this light as a priority from the GUI, will also include other lights
    :type prioritizeName: bool
    :param addSuffix: add the light suffix from the renderer _ARN etc
    :type addSuffix: bool
    :param returnFirstObj: will return only the first obj found (usually for GUI)
    :type returnFirstObj: bool
    :param message: report a message to the user in case of error
    :type message: bool
    """
    iblShapeList = getIblLightSelected(rendererNiceName, includeSelChildren=False, prioritizeName=prioritizeName,
                                       returnFirstObj=False, findUnselected=findUnselected)[1]
    if iblShapeList:  # set the lights if any found
        setIBLAttrList(attrValDict, iblShapeList, invertScaleZ=invertScaleZ)
        shapeListUnique = namehandling.getUniqueShortNameList(iblShapeList)
        if message:
            om2.MGlobal.displayInfo("Success: IBL Updated: {}".format(shapeListUnique))
        return
    elif not iblShapeList and autoCreate:  # create lights because none found
        lightTransformName, shapeNodeName, warningState = createSkydomeLightRenderer(createName, rendererNiceName,
                                                                                     warningState=False, cleanup=True)
        lightTransformName, shapeNodeName = renameLight(lightTransformName, createName, addSuffix=addSuffix,
                                                        lightFamily=IBLSKYDOMES)
        iblShapeList = cmds.listRelatives(lightTransformName, shapes=True, fullPath=True)
        setIBLAttrList(attrValDict, iblShapeList, invertScaleZ=invertScaleZ)
        if message:
            shapeListUnique = namehandling.getUniqueShortNameList(iblShapeList)
            om2.MGlobal.displayInfo("Success: IBL Created: {}".format(shapeListUnique))
        return
    if message:
        om2.MGlobal.displayWarning("No IBL Skydome Lights found for the Renderer")
        return


def setLightTransformDict(lightTransform, attrDictGenericValues):
    """Sets the lights translate, rotation and scale from the attrDictGenericValues
    Also pops the values from the dict so they aren't in the dict for the shape node setting

    :param lightTransform: the transform node name of a single light
    :type lightTransform: str
    :param attrDictGenericValues: generic light dictionary of attributes and values
    :type attrDictGenericValues: dict
    :return attrDictGenericValues: generic light dictionary of attributes and values, now missing trans rot scale
    :rtype attrDictGenericValues: dict
    """
    changeRot = False
    if attrDictGenericValues[SHAPE] == 3 and attrDictGenericValues["scaleX"]:
        if getRendererNiceNameFromLightTransfrom(lightTransform) == REDSHIFT:  # cylinder and redshift
            changeRot = True
    for attr in attributes.MAYATRANSFORMATTRS:  # this is a list of rot translate and scale attrs
        cmds.setAttr(".".join([lightTransform, attr]), attrDictGenericValues[attr])
        attrDictGenericValues.pop(attr, None)
    if changeRot:  # redshift and cylinder
        rotateObjectSpaceXForm(lightTransform, (0, 0, 90))  # add local rotation offset to the light
    return attrDictGenericValues


"""
FILTER FIND SELECTION
"""


def mergeLightShapesTransforms(areaLightTransformList, areaLightShapeList, directionalLightTransformList,
                               directionalLightShapeList, skyDomeTransformList, skydomeShapeList):
    """Takes shapes and transforms and returns only the combined shape lists for each light type

    :param areaLightTransformList: list of area light transform node names
    :type areaLightTransformList: list
    :param areaLightShapeList: list of area light shape node names
    :type areaLightShapeList: list
    :param directionalLightTransformList: list of directional light transform node names
    :type directionalLightTransformList:
    :param directionalLightShapeList: list of directional light shape node names
    :type directionalLightShapeList: list
    :param skyDomeTransformList: list of skydome light transform node names
    :type skyDomeTransformList: list
    :param skydomeShapeList: list of skydone light shape node names
    :type skydomeShapeList: list
    :return directionalLightShapeList: List of directional light shapes in the scene
    :rtype directionalLightShapeList: list
    :return skyDomeTransformList: List of skyDome light Transforms in the scene
    :rtype skyDomeTransformList: list
    :return skydomeShapeList: List of skyDome light Shapes in the scene
    :rtype skydomeShapeList: list
    """
    if areaLightTransformList:
        areaLightShapeList += getLightShapeList(areaLightTransformList)
        areaLightShapeList = list(set(areaLightShapeList))  # make unique
    if directionalLightTransformList:
        directionalLightShapeList += getLightShapeList(directionalLightTransformList)
        directionalLightShapeList = list(set(directionalLightShapeList))  # make unique
    if skyDomeTransformList:
        skydomeShapeList += getIblShapeList(skyDomeTransformList)
        skydomeShapeList = list(set(skydomeShapeList))  # make unique
    return areaLightShapeList, directionalLightShapeList, skydomeShapeList


def filterIblLightInList(nodeList):
    """Finds ibl light shapes in a list, returns empty list if None

    :param nodeList: maya node list
    :type nodeList: list
    :return iblShapeList: list of ibl shapes
    :rtype iblShapeList: list
    """
    iblShapeList = list()
    for obj in nodeList:
        if cmds.objectType(obj) != "transform":
            obj = cmds.listRelatives(obj, parent=True, fullPath=True)
        if obj is not None:  # No transform sound so bail
            lightShape = getIblShape(obj)
            if lightShape:
                iblShapeList.append(lightShape)
    return iblShapeList


def filterIblLightInListRenderer(nodeList, rendererNiceName):
    """Finds ibl light shapes in a list and checks if they are a match with the rendererNiceName
    returns empty list if None

    :param nodeList: maya node list
    :type nodeList: list
    :param rendererNiceName: the renderer nice name "Redshift", "Arnold", "Renderman"
    :type rendererNiceName: str
    :return iblShapeList: list of ibl shapes
    :rtype iblShapeList: list
    """
    iblShapeList = list()
    currentIblShapeList = filterIblLightInList(nodeList)
    if not currentIblShapeList:  # is none so return empty list
        return iblShapeList
    for iblShape in currentIblShapeList:
        if cmds.objectType(iblShape) == RENDERERSKYDOMELIGHTS[rendererNiceName]:  # if node match on the found IBL
            iblShapeList.append(iblShape)
    return iblShapeList


def getAreaLightShapesInScene(rendererNiceName, long=True):
    """gets all area lights in the scene from the given renderer
    returns a list of light shape nodes
    keeps long names if long=True

    :param renderer: nice name of the renderer "Redshift", "Arnold" etc
    :type renderer: str
    :return lightsShapeList: a list of area light shape nodes in the scene
    :rtype lightsShapeList: list
    """
    lightType = RENDERERAREALIGHTS[rendererNiceName]
    if isinstance(lightType, list):  # if it's a list then take the first renderman light
        lightType = lightType[0]
    lightsShapeList = list()
    if lightType == RENDERERAREALIGHTS[REDSHIFT]:  # "RedshiftPhysicalLight"
        redshiftPhysicalList = cmds.ls(type=RENDERERAREALIGHTS[REDSHIFT], long=True)
        for lightShape in redshiftPhysicalList:
            if cmds.getAttr("{}.lightType".format(lightShape)) == 0:  # then yes is an area light
                lightsShapeList.append(lightShape)
    elif lightType == RENDERERAREALIGHTS[ARNOLD]:  # aiAreaLight
        lightsShapeList = cmds.ls(type=RENDERERAREALIGHTS[ARNOLD], long=True)
    else:
        found = False
        for lightType in RENDERERAREALIGHTS[RENDERMAN]:  # Could be three lights
            if lightType == lightType:
                found = True
                lightsShapeList = rendermanlights.getAllRendermanAreaLightsInScene()
        if not found:
            om2.MGlobal.displayWarning("Light Type Not Supported Or Found `{}`".format(lightType))
    if not long:  # make names short/unique
        lightsShapeList = namehandling.getUniqueShortNameList(lightsShapeList)
    return lightsShapeList


def getAllAreaLightsInScene(rendererNiceName, long=True):
    """gets all the area light transforms and shapes in the scene for the current renderer
    returns lightsTransformList and lightsShapeList

    :param renderer: nice name of the renderer "Redshift", "Arnold" etc
    :type renderer: str
    :param long: return long names
    :type long: bool
    :return areaLightTransformList: list of names of the light transform nodes
    :rtype areaLightTransformList: list
    :return areaLightShapeList: list of names of the light shape nodes
    :rtype areaLightShapeList: list
    """
    areaLightShapeList = getAreaLightShapesInScene(rendererNiceName, long=True)
    if not areaLightShapeList:  # no shapes found so return empty lists
        return list(), list()
    areaLightTransformList = list()
    for lightShape in areaLightShapeList:  # find the transform names version of the light list
        areaLightTransformList.append(cmds.listRelatives(lightShape, parent=True, fullPath=True)[0])
        if not long:
            areaLightTransformList = namehandling.getUniqueShortNameList(areaLightTransformList)
    return areaLightTransformList, areaLightShapeList


def getSelectedAreaLights(rendererNiceName, message=True, prioritizeName=""):
    """Returns only the selected area lights of the given renderer, also supports shape nodes

    :param rendererNiceName: nice name of the renderer "Redshift", "Arnold" etc
    :type rendererNiceName: str
    :param message: Show the warning messages to the user
    :type message: bool
    :param prioritizeName: tries to select this light as a priority from the GUI, will also include other lights
    :type prioritizeName: bool
    :return lightTransformList: list of filtered light transforms given the renderer and selection
    :rtype lightTransformList: list
    :return lightShapeList: list of filtered light shape nodes given the renderer and selection
    :rtype lightShapeList: list
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs and not prioritizeName:  # nothing selected and no fallback name
        if message:
            om2.MGlobal.displayWarning("No Valid {} Area Lights Selected.".format(rendererNiceName))
        return list(), list()
    elif not cmds.objExists(prioritizeName) and not selObjs:  # no match for fallback name so return
        if message:
            om2.MGlobal.displayWarning("AA No Area Lights Named {} found in the scene, "
                                       "or other selected area lights.".format(prioritizeName))
        return list(), list()
    allAreaTransforms, allAreaShapes = getAllAreaLightsInScene(rendererNiceName)
    if not allAreaTransforms:  # no lights in the scene must return none
        if message:
            om2.MGlobal.displayWarning(
                "No Area Lights Found In Scene For {}. Please Create A New Light".format(rendererNiceName))
        return list(), list()
    if prioritizeName:
        if cmds.objExists(prioritizeName):
            selObjs.append(prioritizeName)  # area light was found so add it to lists
            allAreaTransforms.append(prioritizeName)
    # combine all lights
    filteredTransforms = list(set(allAreaTransforms) & set(selObjs))
    filteredShapeNodes = list(set(allAreaShapes) & set(selObjs))
    if not filteredTransforms and not filteredShapeNodes:
        if message and prioritizeName:
            om2.MGlobal.displayWarning("BB No Area Lights Named {} found in the scene, "
                                       "or other selected area lights.".format(prioritizeName))
        elif message:
            om2.MGlobal.displayWarning(
                "No Area Lights Found In Selection For {}.  Please Select An Area Light".format(rendererNiceName))
        return list(), list()
    if filteredShapeNodes:
        for lightShape in filteredShapeNodes:  # append the transforms of the shape nodes but could be duplicated
            filteredTransforms.append(cmds.listRelatives(lightShape, parent=True, type="transform", fullPath=True)[0])
    filteredTransforms = list(set(filteredTransforms))  # could be duplicates after appending parents of shape nodes
    filteredShapeNodes = list()
    for lightTransform in filteredTransforms:  # get the shape nodes now we know the transforms
        filteredShapeNodes.append(cmds.listRelatives(lightTransform, shapes=True, fullPath=True)[0])
    return filteredTransforms, filteredShapeNodes


def findFirstIblLight(nodeList, prioritizeName=""):
    """Returns the first ibl light found in a list, for GUI displays.

    :param nodeList: list of Maya nodes, can be shapes or transforms, any nodes
    :type nodeList: list
    :return obj: will be one shape node that is an IBL light
    :rtype obj: str
    """
    if prioritizeName:
        if cmds.objExists(prioritizeName):
            nodeList.insert(0, prioritizeName)  # insert prioritizeName as the first entry
    obj = None
    for obj in nodeList:  # check to find the first directional light
        if cmds.objectType(obj) == "transform":  # transform so get the shape
            shape = getIblShape(obj)  # returns None if not
            if not shape:  # is not an ibl
                obj = None
        else:  # could be a shape node
            obj = checkDirectionalShape(obj)  # will be None if not a directional light node
        if obj:
            break
    return obj


def getIblFromSelectedOrScene(rendererNiceName, includeSelChildren=False, returnFirstObj=False, prioritizeName="",
                              findUnselected=True):
    """Finds an IBL Light from selected and if findUnselected=True then finds IBLs from the scene

    TODO: note this function is depreciated and should use getIblLightSelected() see that function for docs

    Only returns the shape list, not transforms
    """
    return getIblLightSelected(rendererNiceName, includeSelChildren=includeSelChildren, prioritizeName=prioritizeName,
                               returnFirstObj=returnFirstObj, findUnselected=findUnselected)[1]


def getIblLightSelected(rendererNiceName, includeSelChildren=False, prioritizeName="", returnFirstObj=True,
                        findUnselected=True):
    """Smart function which intelligently returns an iblTransform list and iblShapes list from the selection with
    a number of options:

        prioritizeName: will include this obj name even if it's not selected (usually from a GUI)
        findUnselected: will return a light if none found and only one light exists in the scene
        returnFirstObj: will return the first obj found (usually for GUI)
        includeSelChildren: will search the children of the selected objs

    :param rendererNiceName: the renderer nicename "Arnold" etc
    :type rendererNiceName: str
    :param includeSelChildren: will include all children in the hierarchy of the selected objs
    :type includeSelChildren: str
    :param prioritizeName: tries to select this light as a priority from the GUI
    :type prioritizeName: str
    :param returnFirstObj: will only return the first object found
    :type returnFirstObj: bool
    :param findUnselected: will return the the only light in the scene if none found and only one light exists
    :type findUnselected: bool
    :return iblTransformList: list of IBL transform nodes
    :rtype iblTransformList: list
    :return iblShapeList: list of IBL shape nodes
    :rtype iblShapeList: list
    """
    if returnFirstObj:
        iblShape = findFirstIblLight(cmds.ls(selection=True, long=True), prioritizeName=prioritizeName)
        if iblShape:
            iblTransform = cmds.listRelatives(iblShape, parent=True, fullPath=True)[0]
            return [iblTransform], [iblShape]
    if not includeSelChildren:
        selObjs = cmds.ls(selection=True, long=True)
    else:
        selObjs = objhandling.returnSelectLists(selectFlag="hierarchy")[0]
    if prioritizeName:
        if cmds.objExists(prioritizeName):
            selObjs.insert(0, prioritizeName)  # insert prioritizeName as the first entry
            selObjs = list(set(selObjs))  # remove potential duplicates
    # if here then there are objs in selObjs, so test to see if they are ibl lights
    iblTransformList = list()
    iblShapeList = list()
    lightType = RENDERERSKYDOMELIGHTS[rendererNiceName]
    for obj in selObjs:
        if cmds.objectType(obj) == "transform":  # turn the obj into it's shape node so it can be checked
            objShape = cmds.listRelatives(obj, shapes=True, fullPath=True)
            if objShape:
                obj = objShape[0]
        if cmds.objectType(obj) == lightType:
            iblShapeList.append(obj)
            iblTransformList.append(cmds.listRelatives(obj, parent=True, fullPath=True)[0])
    if not iblTransformList:
        if findUnselected:  # try to find a single ibl light in the scene, if only one then return it
            iblTransforms, iblShapes = getAllIblSkydomeLightsInScene(rendererNiceName)
            if len(iblTransforms) == 1:
                return iblTransforms, iblShapes
        else:
            return list(), list()
    return iblTransformList, iblShapeList


def getIBLLightsInScene(rendererNiceName, long=True):
    """returns all ibl lights as shape nodes in the scene given the renderer nice name

    :param rendererNiceName: the renderer nice name "Redshift", "Arnold", "Renderman"
    :type rendererNiceName: str
    :return iblShapeList: list of ibl shapes for the renderer
    :rtype iblShapeList: list
    """
    iblShapeList = cmds.ls(type=RENDERERSKYDOMELIGHTS[rendererNiceName], long=True)
    if not long:
        iblShapeList = namehandling.getUniqueShortNameList(iblShapeList)
    return iblShapeList


def getAllIblSkydomeLightsInScene(rendererNiceName, long=True):
    """Gets all IBL skydome lights in the scene from the given renderer
    Returns both shape and transform node lists

    :param renderer: nice name of the renderer "Redshift", "Arnold" etc
    :type renderer: str
    :return iblSkydomeTransformList: list of names of the IBL light transform nodes
    :rtype iblSkydomeTransformList: list
    :return iblSkydomeShapeList: list of names of the IBL light shape nodes
    :rtype iblSkydomeShapeList: list
    """
    iblSkydomeShapeList = getIBLLightsInScene(rendererNiceName)
    if not iblSkydomeShapeList:  # no shapes found so return empty lists
        return list(), list()
    iblSkydomeTransformList = list()
    for lightShape in iblSkydomeShapeList:  # find the transform names version of the light list
        iblSkydomeTransformList.append(cmds.listRelatives(lightShape, parent=True, fullPath=True)[0])
        if not long:
            iblSkydomeTransformList = namehandling.getUniqueShortNameList(iblSkydomeTransformList)
    return iblSkydomeTransformList, iblSkydomeShapeList


def getAllDirectionalShapesInScene(rendererNiceName, long=True):
    """gets all directional lights in the scene from the given renderer
    returns a list of light shape nodes
    keeps long names if not unique

    :param rendererNiceName: nice name of the renderer "Redshift", "Arnold" etc
    :type rendererNiceName: str
    :return lightsShapeList: a list of directional light shape nodes in the scene
    :rtype lightsShapeList: list
    """
    lightType = RENDERERDIRECTIONALLIGHTS[rendererNiceName]
    lightsShapeList = list()
    if lightType == RENDERERAREALIGHTS[REDSHIFT]:  # "RedshiftPhysicalLight"
        redshiftPhysicalList = cmds.ls(type=RENDERERDIRECTIONALLIGHTS[REDSHIFT], long=True)
        for lightShape in redshiftPhysicalList:
            if cmds.getAttr("{}.lightType".format(lightShape)) == 3:  # then yes its a directional light
                lightsShapeList.append(lightShape)
    elif lightType == RENDERERDIRECTIONALLIGHTS[ARNOLD]:  # directionalLight  NOTE tricky because it's just a Maya light
        lightsShapeList = cmds.ls(type=RENDERERDIRECTIONALLIGHTS[ARNOLD], long=True)
    elif lightType == RENDERERDIRECTIONALLIGHTS[RENDERMAN]:
        lightsShapeList = cmds.ls(type=RENDERERDIRECTIONALLIGHTS[RENDERMAN], long=True)
    else:
        om2.MGlobal.displayWarning("Light Type Not Supported Or Found `{}`".format(lightType))
    if not long:
        lightsShapeList = namehandling.getUniqueShortNameList(lightsShapeList)
    return lightsShapeList


def getAllDirectionalLightsInScene(rendererNiceName, forceUniqueNames=False):
    """gets all directional lights in the scene from the given renderer
    returns a list of light shape nodes
    force unique names, will rename lights to be unique
    otherwise keeps long names if not unique

    :param rendererNiceName: nice name of the renderer "Redshift", "Arnold" etc
    :type rendererNiceName: str
    :param forceUniqueNames: names will be returned as long, if this is on, names will be renamed to unique
    :type forceUniqueNames: bool
    :return lightsShapeList: a list of area light shape nodes in the scene
    :rtype lightsShapeList: list
    """
    directionalLightTransformList = list()
    directionalLightShapeList = getAllDirectionalShapesInScene(rendererNiceName)
    if not directionalLightShapeList:  # no shapes found so return empty lists
        return list(), list()
    for lightShape in directionalLightShapeList:  # find the transform names version of the light list
        directionalLightTransformList.append(cmds.listRelatives(lightShape, parent=True, fullPath=True)[0])
    if forceUniqueNames:  # everything is long names should not need this
        namehandling.forceUniqueShortNameList(directionalLightShapeList, ignoreShape=False)
        namehandling.forceUniqueShortNameList(directionalLightTransformList, ignoreShape=True)
    return directionalLightTransformList, directionalLightShapeList


def getSelectedDirectionalLights(rendererNiceName, message=True, returnIfOneDirectional=True,
                                 includeSelChildren=False, prioritizeName="", returnFirstLight=False):
    """Returns only the selected directional lights of the given renderer, also supports shape nodes

    :param rendererNiceName: nice name of the renderer "Redshift", "Arnold" etc
    :type rendererNiceName: str
    :param message: Show the warning messages to the user
    :type message: bool
    :param returnIfOneDirectional: if None selected and only 1 directional light in the scene return it
    :type returnIfOneDirectional: bool
    :param includeSelChildren: if True will search the hierarchy of the selected objects too
    :type includeSelChildren: bool
    :param prioritizeName: tries to select this light as a priority from the GUI, will also include other lights
    :type prioritizeName: bool
    :param returnFirstLight: returns only the attr dict from the first light selected
    :type returnFirstLight: bool
    :return lightTransformList: list of filtered light transforms given the renderer and selection
    :rtype lightTransformList: list
    :return lightShapeList: list of filtered light shape nodes given the renderer and selection
    :rtype lightShapeList: list
    """
    allDirectionalTransforms, allDirectionalShapes = getAllDirectionalLightsInScene(rendererNiceName,
                                                                                    forceUniqueNames=False)
    if not includeSelChildren:
        selObjs = cmds.ls(selection=True, long=True)
    else:
        selObjs = objhandling.returnSelectLists(selectFlag="hierarchy", long=True)[0]
    if selObjs and returnFirstLight:  # find the first directional light
        firstDirectionalLight = findFirstDirectionalLight(selObjs)
        selObjs = [firstDirectionalLight]
    if prioritizeName and not cmds.objExists(prioritizeName):  # it doesn't exist so delete
        prioritizeName = ""
    if not selObjs and not prioritizeName:  # return the only light in the scene
        if returnIfOneDirectional:
            if len(allDirectionalTransforms) == 1:
                return allDirectionalTransforms, allDirectionalShapes
        if message and allDirectionalTransforms:
            om2.MGlobal.displayWarning("No Lights Found In Selection, And Multiple {} Directional "
                                       "Lights Found In Scene, Please Select One".format(rendererNiceName))
        if message and not allDirectionalTransforms:
            om2.MGlobal.displayWarning("No Lights Found In Selection, "
                                       "And No Directional Lights In Scene For {}. "
                                       "Please Create Light".format(rendererNiceName))
        return list(), list()
    if not selObjs and prioritizeName:  # return the prioritizeName and it's shape node
        shapeNode = cmds.listRelatives(prioritizeName, shapes=True, fullPath=True)[0]
        return [prioritizeName], [shapeNode]
    filteredTransforms = list(set(allDirectionalTransforms) & set(selObjs))  # return only matches
    filteredShapeNodes = list(set(allDirectionalShapes) & set(selObjs))
    if not filteredTransforms and not filteredShapeNodes:  # no object found while comparing the lists
        if prioritizeName:
            shapeNode = cmds.listRelatives(prioritizeName, shapes=True, fullPath=True)[0]
            return [prioritizeName], [shapeNode]
        # else return
        if message:
            om2.MGlobal.displayWarning("No Directional Lights For {} Found In Selection".format(rendererNiceName))
        return list(), list()
    if filteredShapeNodes:
        if prioritizeName:
            filteredTransforms.append(prioritizeName)
        for lightShape in filteredShapeNodes:  # append the transforms of the shape nodes
            filteredTransforms.append(cmds.listRelatives(cmds.listRelatives(lightShape, parent=True, fullPath=True)[0]))
    filteredShapeNodes = list()  # reset
    for lightTransform in filteredTransforms:  # get the shape nodes
        filteredShapeNodes.append(cmds.listRelatives(lightTransform, shapes=True, fullPath=True)[0])
    return filteredTransforms, filteredShapeNodes


def getAllLightsInScene(rendererNiceName):
    """Retrieves all lights of type
        area
        directional
        IBL skydome
    Given the renderer in the current scene

    :param renderer: nice name of the renderer "Redshift", "Arnold" etc
    :type renderer: str
    :return areaLightTransformList: List of area light transforms in the scene
    :rtype areaLightTransformList: list
    :return areaLightShapeList: List of area light shapes in the scene
    :rtype areaLightShapeList: list
    :return directionalLightTransformList: List of directional light transforms in the scene
    :rtype directionalLightTransformList: list
    :return directionalLightShapeList: List of directional light shapes in the scene
    :rtype directionalLightShapeList: list
    :return skyDomeTransformList: List of skyDome light Transforms in the scene
    :rtype skyDomeTransformList: list
    :return skydomeShapeList: List of skyDome light Shapes in the scene
    :rtype skydomeShapeList: list
    """
    areaLightTransformList, areaLightShapeList = getAllAreaLightsInScene(rendererNiceName, long=True)
    directionalLightTransformList, directionalLightShapeList = getAllDirectionalLightsInScene(rendererNiceName)
    skyDomeTransformList, skydomeShapeList = getAllIblSkydomeLightsInScene(rendererNiceName)
    return areaLightTransformList, areaLightShapeList, directionalLightTransformList, directionalLightShapeList, \
           skyDomeTransformList, skydomeShapeList


def getAllLightShapesInScene(rendererNiceName, forceUniqueName=False):
    """Retrieves all lights of type given the renderer in the current scene:

        Area
        Directional
        IBL Skydome

    Will auto-rename non unique names
    returns light shapes only

    :param renderer: nice name of the renderer "Redshift", "Arnold" etc
    :type renderer: str
    :return directionalLightShapeList: List of directional light shapes in the scene
    :rtype directionalLightShapeList: list
    :return skyDomeTransformList: List of skyDome light Transforms in the scene
    :rtype skyDomeTransformList: list
    :return skydomeShapeList: List of skyDome light Shapes in the scene
    :rtype skydomeShapeList: list
    """
    areaLightTransformList, areaLightShapeList, directionalLightTransformList, directionalLightShapeList, \
    skyDomeTransformList, skydomeShapeList = getAllLightsInScene(rendererNiceName)
    if forceUniqueName:
        if areaLightShapeList:
            areaLightShapeList = namehandling.forceUniqueShortNameList(areaLightShapeList, ignoreShape=True)
        if directionalLightShapeList:
            directionalLightShapeList = namehandling.forceUniqueShortNameList(directionalLightShapeList,
                                                                              ignoreShape=True)
        if skydomeShapeList:
            skydomeShapeList = namehandling.forceUniqueShortNameList(skydomeShapeList, ignoreShape=True)
        if areaLightTransformList:
            areaLightTransformList = namehandling.forceUniqueShortNameList(areaLightTransformList, ignoreShape=True)
        if directionalLightTransformList:
            directionalLightTransformList = namehandling.forceUniqueShortNameList(directionalLightTransformList,
                                                                                  ignoreShape=True)
        if skyDomeTransformList:
            skyDomeTransformList = namehandling.forceUniqueShortNameList(skyDomeTransformList, ignoreShape=True)
    areaLightShapeList, directionalLightShapeList, \
    skydomeShapeList = mergeLightShapesTransforms(areaLightTransformList, areaLightShapeList,
                                                  directionalLightTransformList, directionalLightShapeList,
                                                  skyDomeTransformList, skydomeShapeList)
    return areaLightShapeList, directionalLightShapeList, skydomeShapeList


def filterAllLightTypesFromSelection(rendererNiceName, message=True):
    """From the current selection return all light types from the given renderer
    Will force rename of non unique names
    return shapes and transforms

    :param rendererNiceName: nice name of the renderer "Redshift", "Arnold" etc
    :type rendererNiceName: str
    :param message: report the message to the user?
    :type message: bool
    :return areaLightTransformList: List of area light transforms filtered from selection
    :rtype areaLightTransformList: list
    :return areaLightShapeList: List of area light shapes filtered from selection
    :rtype areaLightShapeList: list
    :return directionalLightTransformList: List of directional light transforms filtered from selection
    :rtype directionalLightTransformList: list
    :return directionalLightShapeList: List of directional light shapes filtered from selection
    :rtype directionalLightShapeList: list
    :return skyDomeTransformList: List of skyDome light Transforms filtered from selection
    :rtype skyDomeTransformList: list
    :return skydomeShapeList: List of skyDome light Shapes filtered from selection
    :rtype skydomeShapeList: list
    """
    # TODO check this works now with longnames
    selObj = cmds.ls(selection=True, long=True)
    if not selObj:
        if message:
            om2.MGlobal.displayWarning("Please Select Light/s. No Lights Selected")
        return None, None, None, None, None, None
    areaLightTransformList, areaLightShapeList, directionalLightTransformList, directionalLightShapeList, \
    skyDomeTransformList, skydomeShapeList = getAllLightsInScene(rendererNiceName)
    # filter
    if areaLightTransformList:
        areaLightTransformList = list(set(areaLightTransformList) & set(selObj))
        areaLightTransformList = namehandling.forceUniqueShortNameList(areaLightTransformList)
    if areaLightShapeList:
        areaLightShapeList = list(set(areaLightShapeList) & set(selObj))
        areaLightShapeList = namehandling.forceUniqueShortNameList(areaLightShapeList)
    if directionalLightTransformList:
        directionalLightTransformList = list(set(directionalLightTransformList) & set(selObj))
        directionalLightTransformList = namehandling.forceUniqueShortNameList(directionalLightTransformList)
    if directionalLightShapeList:
        directionalLightShapeList = list(set(directionalLightShapeList) & set(selObj))
        directionalLightShapeList = namehandling.forceUniqueShortNameList(directionalLightShapeList)
    if skyDomeTransformList:
        skyDomeTransformList = list(set(skyDomeTransformList) & set(selObj))
        skyDomeTransformList = namehandling.forceUniqueShortNameList(skyDomeTransformList)
    if skydomeShapeList:
        skydomeShapeList = list(set(skydomeShapeList) & set(selObj))
        skydomeShapeList = namehandling.forceUniqueShortNameList(skydomeShapeList)
    return areaLightTransformList, areaLightShapeList, directionalLightTransformList, directionalLightShapeList, \
           skyDomeTransformList, skydomeShapeList


def filterAllLightShapesFromSelection(rendererNiceName, message=True):
    """From the current selection return all light shapes from the given renderer

    :param rendererNiceName: nice name of the renderer "Redshift", "Arnold" etc
    :type rendererNiceName: str
    :param message: report the message to the user?
    :type message: bool
    :return areaLightShapeList: List of area light shapes in the scene
    :rtype areaLightShapeList: list
    :return directionalLightShapeList: List of directional light shapes in the scene
    :rtype directionalLightShapeList: list
    :return skydomeShapeList: List of skyDome light Shapes in the scene
    :rtype skydomeShapeList: list
    """
    areaLightTransformList, areaLightShapeList, directionalLightTransformList, directionalLightShapeList, \
    skyDomeTransformList, skydomeShapeList = filterAllLightTypesFromSelection(rendererNiceName, message=message)
    # merge shapes and transforms
    areaLightShapeList, directionalLightShapeList, \
    skydomeShapeList = mergeLightShapesTransforms(areaLightTransformList, areaLightShapeList,
                                                  directionalLightTransformList, directionalLightShapeList,
                                                  skyDomeTransformList, skydomeShapeList)
    return areaLightShapeList, directionalLightShapeList, skydomeShapeList


"""
ROTATE LIGHTS
"""


def rotIblLight(iblShape, rotOffset):
    """Rotates an IBL light in the scene from it's shape node

    :param iblShape: The single IBL light to rotate, must be the shape node name only
    :type iblShape: str
    :param rotOffset: The amount to rotate the IBL light by in degrees
    :type rotOffset: float
    """
    attrValDict = getIblAttr(iblShape, getIntensity=False, getExposure=False,
                             getColor=False, getLightVisible=False, getIblTexture=False, getTranslation=False,
                             getRotation=True, getScale=False)
    rotY = attrValDict[ROTATE][1] + rotOffset
    attrValDict[ROTATE] = (attrValDict[ROTATE][0], rotY, attrValDict[ROTATE][2])
    setIblAttr(iblShape, attrValDict)


def rotIblLightSelectedScene(rendererNiceName, rotOffset):
    """Rotates selected IBL lights in the scene by the rotOffset

    :param rendererNiceName: The nice name of the renderer ie "Arnold" or "Redshift" etc
    :type rendererNiceName: str
    :param rotOffset: the amount to rotate the IBL light by in degrees
    :type rotOffset: float
    """
    iblShapeList = getIblLightSelected(rendererNiceName, includeSelChildren=False, prioritizeName="",
                                       returnFirstObj=False, findUnselected=True)[1]

    if not iblShapeList:
        om2.MGlobal.displayWarning("No {} IBL Found".format(rendererNiceName))
        return
    if len(iblShapeList) > 1:
        om2.MGlobal.displayWarning("More than one {} IBL Found, "
                                   "Please Select One IBL Light".format(rendererNiceName))
        return
    rotIblLight(iblShapeList[0], rotOffset)
    om2.MGlobal.displayInfo("{} IBL Skydome Light Rotated".format(rendererNiceName))


def rotLightGrp(rendererNiceName, rot, setExactRotation=False):
    """Rotates the light group, usually named "ArnoldLights_grp" or similar in the current scene

    Looks for the name depending on the renderer, otherwise isn't very intelligent

    :param rendererNiceName: The nice name of the renderer ie "Arnold" or "Redshift" etc
    :type rendererNiceName: str
    :param rot: the amount to rotate offset from current value unless the setExactRotation flag is on
    :type rot: float
    :param setExactRotation: will not offset the rotation, will set rotation to the exact value
    :type setExactRotation: float
    """
    lightGrp = "".join([rendererNiceName, LIGHTGRPNAME])
    if not cmds.objExists(lightGrp):
        om2.MGlobal.displayWarning("No Group Named {} Found In Scene".format(lightGrp))
        return
    if setExactRotation:
        rotY = rot
    else:  # offset from the current value
        rotY = cmds.getAttr("{}.rotateY".format(lightGrp))
        rotY += rot
    cmds.setAttr("{}.rotateY".format(lightGrp), rotY)
    om2.MGlobal.displayInfo("{} Rotated".format(lightGrp))


"""
NORMALIZE LIGHTS
"""


def getLightNormalizeValue(lightShapeNode):
    attrValDict = getLightAttr(lightShapeNode, getIntensity=False, getExposure=False, getColor=False,
                               getTemperature=False,
                               getTempOnOff=False, getShape=False, getNormalize=True, getLightVisible=False,
                               getScale=False)
    return attrValDict[NORMALIZE]


def convertNormalizeRenderer(newNormalizeVal, intensity, exposure, shapeInt, scale, rendererNiceName,
                             convertAsIntensity=False, account2xScale=True):
    """Function for calculating the convert normalization of lights by the renderer, usually for the UI values

    uses generic light data
    returns the converted intensity and exposure values

    :param newNormalizeVal: is normalize being changed to on or off?
    :type newNormalizeVal: bool
    :param intensity: intensity value of the area light
    :type intensity: float
    :param exposure: exposure value of the area light
    :type exposure: float
    :param shapeInt: the shape of the area light as a generic value int
    :type shapeInt: int
    :param scale: the scale of the area light
    :type scale: tuple(float)
    :param rendererNiceName: The nicename of the renderer "Arnold" or "Redshift" etc
    :type rendererNiceName: str
    :param convertAsIntensity: Converts the light value as intensity and not exposure
    :type convertAsIntensity: bool
    :param account4xScale: generic lights are scaled four times the area at a value of 1, True multiplies intensity by 4
    :type account4xScale: bool
    :return intensity: the returned intensity value will be 1
    :rtype intensity: float
    :return exposure: the returned exposure value now normalized
    :rtype exposure: float
    """
    shape = SHAPE_ATTR_ENUM_LIST_NICE[shapeInt]  # ["rectangle", "disc", "sphere", "cylinder"]
    if rendererNiceName == "Arnold" and shapeInt == 2:  # if Arnold and sphere
        shape = SHAPE_ATTR_ENUM_LIST_NICE[0]  # doesn't exist so set to rectangle
    if rendererNiceName == "Renderman" and shapeInt == 3:  # if Renderman and cylinder
        shape = SHAPE_ATTR_ENUM_LIST_NICE[0]  # doesn't exist so set to rectangle
    if account2xScale:  # Generic lights are 2* the scale of 1cm lights (2cm x 2cm x 2cm)
        scaleX = scale[0] * 2
        scaleY = scale[1] * 2
        scaleZ = scale[2] * 2
        scale = (scaleX, scaleY, scaleZ)
    if not convertAsIntensity:  # convert as exposure
        if not newNormalizeVal:  # convert to not normalized exposure
            return lightingutils.convertToNonNormalizedExposure(intensity, exposure, scale[0], scale[1],
                                                                scale[2], shape=shape)
        else:  # convert to normalized exposure
            return lightingutils.convertToNormalizedExposure(intensity, exposure, scale[0], scale[1],
                                                             scale[2], shape=shape)
    else:  # convert as intensity
        if not newNormalizeVal:  # convert to not normalized intensity
            return lightingutils.convertToNonNormalizedIntensity(intensity, exposure, scale[0], scale[1],
                                                                 scale[2],
                                                                 shape=shape)
        else:  # convert to normalized intensity
            return lightingutils.convertToNormalizedIntensity(intensity, exposure, scale[0], scale[1],
                                                              scale[2], shape=shape)


def convertNormalize(lightTransform, newNormalizeVal, applyAsIntensity=True, renderer=""):
    """Converts the normalization of a single area light for multiple renderers.

    Calculates the surface area of the current light shape and the raw light scale in the world (not local)

    Scale is calculated by xform world space, lights should not be parented or reparented

    :param lightTransform:  The light transform name
    :type lightTransform: str
    :param newNormalizeVal: is normalize being changed to on or off?
    :type newNormalizeVal: bool
    :param applyAsIntensity: Applies the light value as intensity and not exposure
    :type applyAsIntensity: bool
    :param renderer: The renderer nice name, is optional and can be left out, matters for "Renderman" only
    :type renderer: str
    :return success: Did the light get coverted?
    :rtype: bool
    """
    # Get lightShape
    lightShape = getLightShape(lightTransform)
    # Get normalize value
    attrValDict = getLightAttr(lightShape, getIntensity=False, getExposure=False, getColor=False, getTemperature=False,
                               getTempOnOff=False, getShape=False, getNormalize=True, getLightVisible=False,
                               getScale=False)
    if attrValDict[NORMALIZE] == newNormalizeVal:
        om2.MGlobal.displayWarning("Light Is Already Set to Normalize `{}`".format(newNormalizeVal))
        return False
    scaleValue = cmds.xform(lightTransform, query=True, scale=True, worldSpace=True)  # get global scale value
    # Get intensity, exposure and shape
    attrValDict = getLightAttr(lightShape, getIntensity=True, getExposure=True, getColor=False, getTemperature=False,
                               getTempOnOff=False, getShape=True, getNormalize=False, getLightVisible=False,
                               getScale=False)
    # -----------------
    # do the conversion
    # -----------------
    if renderer != RENDERMAN:  # renderer can also be empty string ""
        sclX = scaleValue[0] * 2  # default light scales are doubled for normalization, defaults are 2 x 1 maya unit
        sclY = scaleValue[1] * 2
        sclZ = scaleValue[2] * 2
    else:  # leave renderman lights
        sclX = scaleValue[0]
        sclY = scaleValue[1]
        sclZ = scaleValue[2]
    intensity = attrValDict[INTENSITY]
    exposure = attrValDict[EXPOSURE]
    shapeInt = attrValDict[SHAPE]
    shape = SHAPE_ATTR_ENUM_LIST_NICE[shapeInt]  # get the nicename "Rectangle" "Disc" etc
    if newNormalizeVal:  # convert to normalized
        # get the new exposure, intensity
        if applyAsIntensity:
            intensity, exposure = lightingutils.convertToNormalizedIntensity(intensity, exposure, sclX, sclY, sclZ,
                                                                             shape=shape)
        else:
            intensity, exposure = lightingutils.convertToNormalizedExposure(intensity, exposure, sclX, sclY, sclZ,
                                                                            shape=shape)
    else:  # convert to non-normalized
        if applyAsIntensity:
            intensity, exposure = lightingutils.convertToNonNormalizedIntensity(intensity, exposure, sclX, sclY, sclZ,
                                                                                shape=shape)
        else:
            intensity, exposure = lightingutils.convertToNonNormalizedExposure(intensity, exposure, sclX, sclY, sclZ,
                                                                               shape=shape)
    # -----------------
    # set the attributes for exposure and intensity
    # -----------------
    attrValDict[INTENSITY] = intensity
    attrValDict[EXPOSURE] = exposure
    attrValDict[NORMALIZE] = newNormalizeVal
    setLightAttr(lightShape, attrValDict, ignoreIntensity=False)
    return True


def convertNormalizeList(lightTransformList, newNormalizeVal, applyAsIntensity=True, renderer=""):
    """Converts the normalization of an area light list for any renderers.

    This is achieved by unparenting the light into world, and recording the scale values of the light before reparenting
    back under the original parent.

    :param lightTransformList: list of light transform node names
    :type lightTransformList: list
    :param newNormalizeVal: is normalize being changed to on or off?
    :type newNormalizeVal: bool
    :param applyAsIntensity: Applies the light value as intensity and not exposure
    :type applyAsIntensity: bool
    :param renderer: The renderer nice name, is optional and can be left out, matters for "Renderman" only
    :type renderer: str
    :return success: Did the light get converted?
    :rtype: bool
    """
    convertedList = list()
    for lightTransform in lightTransformList:
        convertedList.append(convertNormalize(lightTransform,
                                              newNormalizeVal,
                                              applyAsIntensity=applyAsIntensity,
                                              renderer=renderer))
    return convertedList


def convertToNormalizeSelected(newNormalizeVal, applyAsIntensity=True, renderer=""):
    """Converts the normalization of selected area light/s for multiple renderers.

    :param newNormalizeVal: is normalize being changed to on or off?
    :type newNormalizeVal: bool
    :param applyAsIntensity: Applies the light value as intensity and not exposure
    :type applyAsIntensity: bool
    :return success: Did the light get coverted?
    :rtype: bool
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        om2.MGlobal.displayWarning("No Lights Selected, Please Select")
        return
    for obj in selObjs:
        if cmds.objectType(obj) != "transform":  # if not a transform node, it could be a shape node so try the parent
            obj = cmds.listRelatives(obj, parent=True, fullPath=True)
        lightShape = getLightShape(obj)
        if checkValidLightType(lightShape):
            convertNormalize(obj, newNormalizeVal, applyAsIntensity=applyAsIntensity, renderer=renderer)


"""
CREATE LIGHTS
"""


def createAreaLightFromDict(attrDictGenericValues, rendererNiceName, lightName="areaLight", replaceLight=False,
                            cleanup=True):
    """builds an area light from the a dictionary, makes the fixes given the renderer type

    :param lightName: the lights name to be created
    :type lightName: str
    :param attrDictGenericValues: generic light dictionary of attributes and values
    :type attrDictGenericValues: dict
    :param translateRotScale: set the attributes for translateRotScale, only set if they are included (import)
    :type translateRotScale: bool
    :return lightTransform: the light transform node
    :rtype lightTransform: str
    :return lightShape: the light shape node
    :rtype lightShape: str
    """
    # create light
    lightTransform, lightShape, warningState = createLightRenderer(lightName, rendererNiceName, warningState=False,
                                                                   addSuffix=True, replaceLight=replaceLight)
    if "rotateX" in attrDictGenericValues:  # if exists then apply rotation scale translate
        if rendererNiceName == RENDERMAN:  # then scale by 2
            attrDictGenericValues["scaleX"] = attrDictGenericValues["scaleX"] * 2
            attrDictGenericValues["scaleY"] = attrDictGenericValues["scaleY"] * 2
            attrDictGenericValues["scaleZ"] = attrDictGenericValues["scaleZ"] * 2
        attrDictGenericValues = setLightTransformDict(lightTransform, attrDictGenericValues)
    setLightAttr(lightShape, attrDictGenericValues, ignoreIntensity=False)  # apply dictionary to shape node
    if cleanup:
        lightsTransformList = [lightTransform]  # cleanup
        cleanupLights(rendererNiceName, lightsTransformList, selectLights=False)
    return lightTransform, lightShape


def createDirectionalLightRenderer(name, renderer, warningState=False, forceGimbalZXY=True):
    """Creates a directional light for the given renderer

    :param renderer: the renderer nice name "Redshift", "Arnold", "Renderman"
    :type renderer: str
    :return lightTransformName: the name of the light (transform node)
    :rtype lightTransformName: str
    :return shapeNodeName: the name of the shape node
    :rtype shapeNodeName: str
    """
    lightTransformName = ""
    shapeNodeName = ""
    if renderer == REDSHIFT:  # "RedshiftPhysicalLight"
        lightTransformName, shapeNodeName = redshiftlights.createRedshiftDirectionalLight(name=name)
    elif renderer == ARNOLD:
        lightTransformName, shapeNodeName = arnoldlights.createArnoldDirectionalLight(name=name)
        # add attribute to tag as Arnold
        cmds.addAttr(shapeNodeName, longName=RENDERERTAGATTRIBUTE, dataType="string")
        cmds.setAttr(".".join([shapeNodeName, RENDERERTAGATTRIBUTE]), ARNOLD, type="string")
    elif renderer == RENDERMAN:
        lightTransformName, shapeNodeName = rendermanlights.createRendermanDirectionalLight(name=name)
    else:
        om2.MGlobal.displayWarning("Light Type Not Supported Or Found For Renderer `{}`".format(renderer))
        warningState = True
    if forceGimbalZXY:  # set gimbal rot order to zxy
        cmds.setAttr("{}.rotateOrder".format(lightTransformName), 2)
    # get longNames
    lightTransformName = namehandling.getLongNameFromShort(lightTransformName)
    shapeNodeName = namehandling.getLongNameFromShort(shapeNodeName)
    return lightTransformName, shapeNodeName, warningState


def createLightRenderer(name, renderer, warningState=False, addSuffix=False, replaceLight=False):
    """Creates a physical area light for the given renderer

    :param name: the  name of the light that will be created
    :type name: str
    :param renderer: the renderer nice name "Redshift", "Arnold", "Renderman"
    :type renderer: str
    :param warningState: mark warning bool on if issues have already been encountered
    :type warningState: str
    :param addSuffix: add the suffix for the light usually as per the renderer
    :type addSuffix: bool
    :param replaceLight: replace the light if one already exists with the same name
    :type replaceLight: bool
    :return lightTransformName: the name of the light (transform node)
    :rtype lightTransformName: str
    :return shapeNodeName: the name of the shape node
    :rtype shapeNodeName: str
    :return warningState: display a warning bool on if issues encountered
    :rtype warningState: bool
    """

    lightTransformName = ""
    shapeNodeName = ""
    if addSuffix:
        suffix = RENDERER_SUFFIX[renderer]
        name = "_".join([name, suffix])
    if replaceLight:
        if cmds.objExists(name):
            cmds.delete(name)
            uniqueName = namehandling.getUniqueShortName(name)
            om2.MGlobal.displayWarning("Light {} deleted and recreated".format(uniqueName))
            warningState = True
    if renderer == REDSHIFT:  # "RedshiftPhysicalLight"
        lightTransformName, shapeNodeName = redshiftlights.createRedshiftPhysicalLight(name=name)
    elif renderer == ARNOLD:
        lightTransformName, shapeNodeName = arnoldlights.createArnoldPhysicalLight(name=name)
    elif renderer == RENDERMAN:
        lightTransformName, shapeNodeName = rendermanlights.createRendermanPxrRectLight(name=name)
    else:
        om2.MGlobal.displayWarning("Light Type Not Supported Or Found For Renderer `{}`".format(renderer))
        warningState = True
    return lightTransformName, shapeNodeName, warningState


def createAreaLightMatchPos(name, renderer, warningState=False, addSuffix=False, replaceLight=False, position="world"):
    """Creates a physical area light for the given renderer and place it with options

    Position can be:

        "world" create at the world center
        "selected" create at the same position as the selected object
        "camera" drop from the camera position

    :param name: the  name of the light that will be created
    :type name: str
    :param renderer: the renderer nice name "Redshift", "Arnold", "Renderman"
    :type renderer: str
    :param warningState: mark warning bool on if issues have already been encountered
    :type warningState: str
    :param addSuffix: add the suffix for the light usually as per the renderer
    :type addSuffix: bool
    :param replaceLight: replace the light if one already exists with the same name
    :type replaceLight: bool
    :param position: "world" world center, "selected" selected object pos/rot, "camera" drop at camera position
    :type position: str
    :return lightTransformName: the name of the light (transform node)
    :rtype lightTransformName: str
    :return shapeNodeName: the name of the shape node
    :rtype shapeNodeName: str
    :return warningState: display a warning bool on if issues encountered
    :rtype warningState: bool
    """
    selobjs = cmds.ls(selection=True, transforms=True, long=True)
    lightTransformName, shapeNodeName, warningState = createLightRenderer(name, renderer, warningState=warningState,
                                                                          addSuffix=addSuffix,
                                                                          replaceLight=replaceLight)
    if not lightTransformName:
        return None, None, warningState
    if position == "world":  # do nothing
        return lightTransformName, shapeNodeName
    if position == "selected":  # create by matching to the first selected object
        if selobjs:
            matching.matchZooAlSimpErrConstrain(selobjs[0], lightTransformName)
    elif position == "camera":  # create by dropping the light at the camera position and rotation
        cam = cameras.getFocusCamera()
        if cam:
            matching.matchZooAlSimpErrConstrain(cam, lightTransformName)
        else:
            om2.MGlobal.displayWarning("No camera found. Must have a Maya window 'with focus' and a camera view.  "
                                       "Light created at world center")
    return lightTransformName, shapeNodeName, warningState


def createLightFromLoc(locator, rendererNiceName, replaceLight=True, cleanup=True):
    """Will build an area light in the renderer type from a given generic locator
    Locator must have the light information attributes

    :param locator: the generic locator name, locator must have with light information
    :type locator: str
    :param rendererNiceName: the renderer nice name "Redshift", "Arnold", "Renderman"
    :type rendererNiceName: str
    :param replaceLight: Replace existing lights if true, otherwise will build with a new name
    :type replaceLight: bool
    :param cleanup: grp the lights into the renderer group?
    :type cleanup: bool
    :return lightTransform: The lights transform node name
    :rtype lightTransform: str
    :return lightShape: The lights shape node name
    :rtype lightShape: str
    """
    lightName = namehandling.stripSuffixExact(locator, RENDERER_SUFFIX["Generic"])  # remove suffix
    attrDictGenericValues = getLocatorAttr(locator)  # pull the values in a generic dict
    lightTransform, lightShape = createAreaLightFromDict(attrDictGenericValues, rendererNiceName, lightName=lightName,
                                                         replaceLight=replaceLight, cleanup=cleanup)
    matchLights(rendererNiceName, lightTransform, locator, locatorMode=True)
    return lightTransform, lightShape


def createLightFromLocList(locatorList, rendererNiceName, replaceLight=True, cleanup=True):
    """Builds a list of area light in the renderer type from a given generic locator list
    Locators must have the light information attributes

    :param locatorList: the generic locator name, locator must have with light information
    :type locator: list
    :param rendererNiceName: the renderer nice name "Redshift", "Arnold", "Renderman"
    :type rendererNiceName: str
    :param replaceLight: Replace existing lights if true, otherwise will build with a new name
    :type replaceLight: bool
    :param cleanup: grp the lights into the renderer group?
    :type cleanup: bool
    :return lightTransformList: The lights transform node name
    :rtype lightTransformList: str
    :return lightShapeList: The lights shape node name
    :rtype lightShapeList: str
    """
    lightTransformList = list()
    lightShapeList = list()
    for locator in locatorList:
        lightTransform, lightShape = createLightFromLoc(locator, rendererNiceName, replaceLight=replaceLight,
                                                        cleanup=cleanup)
        lightTransformList.append(lightTransform)
        lightShapeList.append(lightShape)
    return lightTransformList, lightShapeList


def createAreaLightsFromAllLocs(rendererNiceName):
    """finds all the generic area light locators in the scene and builds lights with the current renderer type

    :param rendererNiceName: the renderer nice name "Redshift", "Arnold", "Renderman"
    :type rendererNiceName: str
    :return lightTransformList: The lights transform node name
    :rtype lightTransformList: str
    :return lightShapeList: The lights shape node name
    :rtype lightShapeList: str
    """
    selObjs = cmds.ls(selection=True, long=True)  # needs the selection so can return later
    locatorList = getAllLocsInScene()  # returns self.lightLocatorList
    if not locatorList:
        om2.MGlobal.displayWarning("No Locators With Suffix `_LgtLc` found in scene.  "
                                   "No lights created.")
        return list(), list()
    # create the lights
    lightsTransformList, lightsShapeList = createLightFromLocList(locatorList, rendererNiceName, replaceLight=True,
                                                                  cleanup=True)
    cmds.select(selObjs, replace=True)  # reselect objects from original selection
    transformListUnique = namehandling.getUniqueShortNameList(lightsTransformList)
    om2.MGlobal.displayInfo("Success: Lights Created And Matched {}".format(transformListUnique))
    return lightsTransformList, lightsShapeList


def createDirectionalDictRenderer(attrGenericDict, lightName, rendererNiceName, warningState=False,
                                  cleanup=False, setZXY=True, suffix=True):
    """Creates a directional light for the given renderer from a attribute dict

    :param name: the name of the light to be created
    :type name: str
    :param renderer: the renderer nice name "Redshift", "Arnold", "Renderman"
    :type renderer: str
    :param warningState: if warnings have happened report them
    :type warningState: bool
    :param cleanup: will put the lights into an appropriate group named by the renderer name
    :type cleanup: bool
    :param setZXY: will create the IBL with a default rotation order of ZXY which is generally better
    :type setZXY: bool
    :return lightTransformName: the name of the light (transform node)
    :rtype lightTransformName: str
    :return shapeNodeName: the name of the shape node
    :rtype shapeNodeName: str
    :return warningState: has the warning state been activated?
    :rtype warningState: bool
    """
    directionalTransform, \
    directionalShape, \
    warningState = createDirectionalLightRenderer("tempXXXXdirlight", rendererNiceName, warningState=False,
                                                  forceGimbalZXY=True)
    setDirectionalAttr(directionalShape, rendererNiceName, attrGenericDict)
    directionalTransform, directionalShape = renameLight(directionalTransform, lightName, addSuffix=suffix,
                                                         renderer=rendererNiceName, lightFamily=DIRECTIONALS)
    if cleanup:
        cleanupLights(rendererNiceName, [directionalTransform], selectLights=True)
    return directionalTransform, directionalShape, warningState


def createDirectionalLightMatchPos(attrGenericDict, lightName, rendererNiceName, warningState=False,
                                   cleanup=False, setZXY=True, suffix=True, position="world"):
    """Creates a directional light for the given renderer and place it with options

    Position can be:

        "world" create at the world center
        "selected" create at the same position as the selected object
        "camera" drop from the camera position

    :param name: the name of the light to be created
    :type name: str
    :param renderer: the renderer nice name "Redshift", "Arnold", "Renderman"
    :type renderer: str
    :param warningState: if warnings have happened report them
    :type warningState: bool
    :param cleanup: will put the lights into an appropriate group named by the renderer name
    :type cleanup: bool
    :param setZXY: will create the IBL with a default rotation order of ZXY which is generally better
    :type setZXY: bool
    :param position: "world" world center, "selected" selected object pos/rot, "camera" drop at camera position
    :type position: str
    :return lightTransformName: the name of the light (transform node)
    :rtype lightTransformName: str
    :return shapeNodeName: the name of the shape node
    :rtype shapeNodeName: str
    :return warningState: has the warning state been activated?
    :rtype warningState: bool
    """
    selobjs = cmds.ls(selection=True, transforms=True, long=True)
    lightTransformName, shapeNodeName, warningState = createDirectionalDictRenderer(attrGenericDict,
                                                                                    lightName,
                                                                                    rendererNiceName,
                                                                                    warningState=warningState,
                                                                                    suffix=suffix,
                                                                                    setZXY=setZXY,
                                                                                    cleanup=cleanup)
    if not lightTransformName:
        return None, None, warningState
    if position == "world":  # do nothing
        return lightTransformName, shapeNodeName
    if position == "selected":  # create by matching to the first selected object
        if selobjs:
            matching.matchZooAlSimpErrConstrain(selobjs[0], lightTransformName)
    elif position == "camera":  # create by droping the light at the camera position and rotation
        cam = cameras.getFocusCamera()
        if cam:
            matching.matchZooAlSimpErrConstrain(cam, lightTransformName)
        else:
            om2.MGlobal.displayWarning("No camera found. Must have a Maya window 'with focus' and a camera view. "
                                       "Light created at world center")
    return lightTransformName, shapeNodeName, warningState


def createSkydomeLightRenderer(name, renderer, warningState=False, cleanup=False, setZXY=True):
    """Creates a skydome light for the given renderer

    :param name: the name of the light to be created
    :type name: str
    :param renderer: the renderer nice name "Redshift", "Arnold", "Renderman"
    :type renderer: str
    :param warningState: if warnings have happened report them
    :type warningState: bool
    :param cleanup: will put the lights into an appropriate group named by the renderer name
    :type cleanup: bool
    :param setZXY: will create the IBL with a default rotation order of ZXY which is generally better
    :type setZXY: bool
    :return lightTransformName: the name of the light (transform node)
    :rtype lightTransformName: str
    :return shapeNodeName: the name of the shape node
    :rtype shapeNodeName: str
    :return warningState: has the warning state been activated?
    :rtype warningState: bool
    """
    lightTransformName = ""
    shapeNodeName = ""
    if renderer == REDSHIFT:  # "RedshiftPhysicalLight"
        lightTransformName, shapeNodeName = redshiftlights.createRedshiftSkydomeLight(name=name)
        # add attribute to tag as Arnold
        cmds.addAttr(shapeNodeName, longName=RENDERERTAGATTRIBUTE, dataType="string")
        cmds.setAttr(".".join([shapeNodeName, RENDERERTAGATTRIBUTE]), REDSHIFT, type="string")
    elif renderer == ARNOLD:
        lightTransformName, shapeNodeName = arnoldlights.createArnoldSkydomeLight(name=name)
        # add attribute to tag as Arnold
        cmds.addAttr(shapeNodeName, longName=RENDERERTAGATTRIBUTE, dataType="string")
        cmds.setAttr(".".join([shapeNodeName, RENDERERTAGATTRIBUTE]), ARNOLD, type="string")
    elif renderer == RENDERMAN:
        lightTransformName, shapeNodeName = rendermanlights.createRendermanSkydomeLight(name=name)
    else:
        om2.MGlobal.displayWarning("Light Type Not Supported Or Found For Renderer `{}`".format(renderer))
        warningState = True
    if cleanup:
        cleanupLights(renderer, [lightTransformName], selectLights=True)
    if setZXY:
        cmds.setAttr("{}.rotateOrder".format(lightTransformName), 2)
    return lightTransformName, shapeNodeName, warningState


def createSkydomeLightDictRenderer(attrValDict, name, rendererNiceName, warningState=False, cleanup=True):
    """Creates a Skydome IBL HDR light for the given renderer

    :param attrValDict: the attribute values to create the light with
    :type attrValDict: dict
    :param name: The name of the light to be created
    :type name: str
    :param rendererNiceName: the nice name of the renderer the light will be created "Redshift", "Arnold", "Renderman"
    :type rendererNiceName: str
    :param warningState: Are there reported warnings?
    :type warningState: bool
    :param cleanup: cleanup the lights into a tidy Maya group with the renderer name?
    :type cleanup: bool
    :return lightTransformName: The name of the new transform node
    :rtype lightTransformName: str
    :return shapeNodeName: The name of the new shape node
    :rtype shapeNodeName: str
    """
    uniqueName = namehandling.nonUniqueNameNumber(name, shortNewName=True)
    lightTransformName, shapeNodeName, warningState = createSkydomeLightRenderer(uniqueName, rendererNiceName,
                                                                                 warningState=warningState)
    # set attributes
    setIblAttr(shapeNodeName, attrValDict)
    # rename with suffix
    lightTransformName, shapeNodeName = renameLight(lightTransformName, name, addSuffix=True, renderer=rendererNiceName,
                                                    lightFamily=IBLSKYDOMES)
    if cleanup:
        cleanupLights(rendererNiceName, [lightTransformName])
    return lightTransformName, shapeNodeName


def createAttributesLocator(locator):
    """creates attributes on a single locator, assumes none exist

    :param locator: name of a locator transform node
    :type locator: str
    """
    for keyAttribute in sorted(GENERICLIGHTATTRDICT):
        if SRGBSUFFIX in keyAttribute:  # if the keyAttribute has _srgb in the name
            # create this attribute as a color attribute
            attributes.createColorAttribute(locator, attrName=GENERICLIGHTATTRDICT[keyAttribute],
                                            keyable=True)  # attrName is most probably "color"
        elif "_shape" in keyAttribute:  # this is the light shape which is a dropdown/combo enum list
            attributes.createEnumAttributeFromList(SHAPE_ATTR_ENUM_LIST, locator,
                                                   GENERICLIGHTATTRDICT[keyAttribute], keyable=True)
        else:  # attribute is a float just create normally
            cmds.addAttr(locator, shortName=GENERICLIGHTATTRDICT[keyAttribute],
                         longName=GENERICLIGHTATTRDICT[keyAttribute], keyable=True)


def createMatchAttributesLocatorSingle(locator, lightTransform, rendererNiceName):
    """creates a single locator, adds the new attributes, sets the values of the attrs and matches trans rot scale

    :param locator: name of a locator transform node
    :type locator: str
    """
    matchLights(rendererNiceName, locator, lightTransform, locatorMode=True)
    lightShape = getLightShape(lightTransform)
    attrDictGenericValues = getLightAttr(lightShape, getIntensity=True, getExposure=True, getColor=True,
                                         getTemperature=True, getTempOnOff=True, getShape=True, getNormalize=True,
                                         getLightVisible=True, getScale=False)
    for genericAttr, value in attrDictGenericValues.items():  # genericAttr is loc attr
        if value is not None:
            attributes.setAttrAutoType(locator, GENERICLIGHTATTRDICT[genericAttr], value, message=False)


def uniqueLightNamesList(lightTransformList, rendererNiceName, renameDuplicates=True, message=True):
    """Convenience function that fixes non unique names for lights, usually used while creating light locators

    :param lightTransformList: List of light transform names
    :type lightTransformList: list(str)
    :param rendererNiceName: The nice name of the renderer
    :type rendererNiceName: str
    :param renameDuplicates: if True this function will rename
    :type renameDuplicates: bool
    :param message:  Report the message to the user
    :type message: bool
    :return lightTransformList: A list of light transforms now potentially renamed if not unique
    :rtype lightTransformList: list(str)
    :return warning: The warning type if there was one, "" if no warnings, can also be "noLights", or "duplicate"
    :rtype warning:
    """
    warning = ""
    shortNameTransformList = namehandling.getShortNameList(lightTransformList)
    if not lightTransformList:  # if no lights bail
        warning = "noLights"
        return None, warning
    if len(shortNameTransformList) != len(set(shortNameTransformList)):  # if duplicate names in list
        if renameDuplicates:  # rename the lights without asking user
            lightTransformList = namehandling.forceUniqueShortNameList(shortNameTransformList)
            if message:
                om2.MGlobal.displayWarning("Some lights have been renamed to be unique")
        else:
            warning = "duplicate"
            if message:
                om2.MGlobal.displayWarning("Lights found that have duplicated names, "
                                           "light names must be unique, please rename")
    if warning:
        if message:
            om2.MGlobal.displayInfo("Success: {} *locator light info objects updated. With warnings "
                                    "*some locators already existed so were deleted and rebuilt. "
                                    "See script editor.".format(rendererNiceName))
        return None, warning
    return lightTransformList, warning


def createLocatorForLight(lightTransform, rendererNiceName):
    """Creates a light-locator for a single area light given the renderer

    :param lightTransform: the lights transform node name
    :type lightTransform: str
    :param rendererNiceName: the light's shape node name
    :type rendererNiceName: str
    :return lightLocator: the locator transform node name
    :rtype lightLocator: str
    """
    shortLightName = namehandling.getShortName(lightTransform)
    shortLightName = shortLightName.replace("_{}".format(RENDERER_SUFFIX[rendererNiceName]), "")  # remove other parts
    locName = "_".join([shortLightName, RENDERER_SUFFIX["Generic"]])
    if cmds.objExists(locName):  # if exists delete
        cmds.delete(locName)
        om2.MGlobal.displayWarning("Existing locator already exists, deleting {}".format(locName))
    locator = cmds.spaceLocator(name=locName)[0]  # create locator
    createAttributesLocator(locator)  # create the attributes
    createMatchAttributesLocatorSingle(locator, lightTransform, rendererNiceName)  # match the attributes
    return locator


def createLocatorForAreaLightList(lightTransformList, rendererNiceName):
    """Creates a light-locator for a single area light given the renderer

    :param lightTransformList: a list of light transform node names
    :type lightTransformList: list(str)
    :param rendererNiceName: the nice name of the renderer the light will be created "Redshift", "Arnold", "Renderman"
    :type rendererNiceName: str
    :return lightLocatorList: a list of generic light locator transform node names
    :rtype lightLocatorList: str
    """
    lightTransformList, warning = uniqueLightNamesList(lightTransformList, rendererNiceName)  # force unique names
    lightLocatorList = list()
    if not lightTransformList:
        return lightLocatorList
    for lightTransform in lightTransformList:
        locator = createLocatorForLight(lightTransform, rendererNiceName)
        lightLocatorList.append(locator)
    return lightLocatorList, warning


def createLocatorLightScene(rendererNiceName, message=True, renameDuplicates=True):
    """Creates a locator for each area light of a given renderer for the scene
    returns the locator list if it was made (None if not) and a warning
    Warnings are
    "noLights" = Couldn't find any lights of this renderer
    "duplicate" = Found duplicate light names

    :param rendererNiceName: the nice name of the renderer the light will be created "Redshift", "Arnold", "Renderman"
    :type rendererNiceName: str
    :param message: report a warning message to the user
    :type message: bool
    :return lightLocatorList: a list of generic light locator transform node names
    :rtype lightLocatorList: list
    :return warning: A warning message if the operation was cancelled
    :rtype warning: str
    """
    lightTransformList, lightsShapeList = getAllAreaLightsInScene(rendererNiceName)
    selObjs = cmds.ls(selection=True, long=True)  # Needs the selection so can return later
    if not lightTransformList:  # no lights to save
        return list(), None
    lightLocatorList, warning = createLocatorForAreaLightList(lightTransformList, rendererNiceName)
    if message:
        om2.MGlobal.displayInfo("Success: {} locator light info objects created".format(rendererNiceName))
    cmds.select(selObjs, replace=True)  # return original selection
    return lightLocatorList, warning


"""
Delete Remove
"""


def deleteAllLightsInScene(renderer, message=True):
    """deletes all lights of the given renderer

    :param renderer: nice name of the renderer "Redshift", "Arnold" etc
    :type renderer: str
    :param message: report the message?
    :type message: bool
    :return lightsDeleted: list of deleted light names
    :rtype lightsDeleted: list
    """
    lightsDeleted = list()
    if renderer == REDSHIFT:
        lightsDeleted = redshiftlights.deleteAllLights()
    elif renderer == ARNOLD:
        lightsDeleted = arnoldlights.deleteAllLights()
    elif renderer == RENDERMAN:
        lightsDeleted = rendermanlights.deleteAllLights()
    # delete grps too
    grp = "".join([renderer, LIGHTGRPNAME])
    if cmds.objExists(grp):
        cmds.delete(grp)
        lightsDeleted.append(grp)
    if message:
        if lightsDeleted:
            transformListUnique = namehandling.getUniqueShortNameList(lightsDeleted)
            om2.MGlobal.displayInfo("{} Lights Deleted `{}`".format(renderer, transformListUnique))
        else:
            om2.MGlobal.displayWarning("No Lights Found")
    return lightsDeleted


def deleteAllLightLocsInScene(message=False):
    """Delete all locators suffixed to "_LgtLc"
    Light Locators that match the lights to export light data
    will delete nameespace names too

    :param message: report the message to the user?
    :type message: bool
    :return lightLocList: light locators deleted
    :rtype lightLocList: list
    """
    lightLocList = cmds.ls("*{}*".format(RENDERER_SUFFIX["Generic"]), long=True)  # no namespaces
    lightLocWithNSList = cmds.ls("*:*{}*".format(RENDERER_SUFFIX["Generic"]), long=True)  # namespaces
    lightLocList += lightLocWithNSList
    if not lightLocList:
        if message:
            om2.MGlobal.displayWarning("No Locator Or Locator Groups Found")
        return lightLocList
    cmds.delete(lightLocList)
    if message:
        transformListUnique = namehandling.getUniqueShortNameList(lightLocList)
        om2.MGlobal.displayInfo("Success: Lights Deleted: {}".format(transformListUnique))
    return lightLocList


"""
Attr Light Dictionaries
"""


def getDirectionalLightAttrDictList(directionalLightTransformList, directionalLightShapeList, rendererNiceName):
    """gets a ibl dict with attributes given a ibl transform and shape list for the current renderer

    :param directionalLightTransformList: list of directional light transform nodes
    :type directionalLightTransformList: list
    :param directionalLightShapeList: list of directional shape nodes
    :type directionalLightShapeList: list
    :param rendererNiceName: the renderer nice name "Arnold" etc
    :type rendererNiceName: str
    :return directionalLightAttrDict: dictionary with the dir light transform names as keys with attribute data
    :rtype directionalLightAttrDict: dict
    """
    directionalLightAttrDict = dict()
    for i, lightShape in enumerate(directionalLightShapeList):
        transformName = directionalLightTransformList[i]
        transformNameNoSuffix = transformName.replace("_{}".format(RENDERER_SUFFIX[rendererNiceName]), "")
        transformNameNoSuffix = namehandling.getShortName(transformNameNoSuffix)
        attrValDict = getDirectionalAttr(lightShape, getIntensity=True, getColor=True, getTemperature=True,
                                         getTempOnOff=True, getAngleSoft=True, getRotation=True)
        directionalLightAttrDict[transformNameNoSuffix] = attrValDict
    return directionalLightAttrDict


def getDirectionalLightDictOfScene(rendererNiceName):
    """For all directional lights in a scene return a dictionary of generic attributes.
    The dictionary keys are the lightname (transform node) with the light suffix removed

    :param rendererNiceName: nice name of the renderer "Redshift", "Arnold" etc
    :type rendererNiceName: str
    :return directionalLightAttrDict: Dictionary of lights with their attributes in a generic dict
    :rtype directionalLightAttrDict: dict
    """
    directionalLightTransformList, directionalLightShapeList = getAllDirectionalLightsInScene(rendererNiceName)
    if not directionalLightShapeList:
        return dict()
    # get the attribute dicts
    return getDirectionalLightAttrDictList(directionalLightTransformList, directionalLightShapeList, rendererNiceName)


def getDirectionalDictSelected(rendererNiceName, includeSelChildren=False):
    """gets a directional dictionary with attributes for the current renderer from selection

    :param rendererNiceName: the renderer nicename "Arnold" etc
    :type rendererNiceName: str
    :return directionalLightAttrDict: the directional dictionary with lights as keys and attribute data
    :rtype directionalLightAttrDict dict
    """
    directionalLightTransformList, \
    directionalLightShapeList = getSelectedDirectionalLights(rendererNiceName, message=False,
                                                             returnIfOneDirectional=False,
                                                             includeSelChildren=includeSelChildren)
    if not directionalLightTransformList:
        return dict()
    return getDirectionalLightAttrDictList(directionalLightTransformList, directionalLightShapeList, rendererNiceName)


def getIBLAttrDictList(iblTransformList, iblShapeList, rendererNiceName):
    """gets a ibl dict with attributes given a ibl transform and shape list for the current renderer

    :param iblTransformList: list of IBL transform nodes
    :type iblTransformList: list
    :param iblShapeList: list of IBL shape nodes
    :type iblShapeList: list
    :param rendererNiceName: the renderer nice name "Arnold" etc
    :type rendererNiceName: str
    :return iblSkyDomeAttributeDict: dictionary with the ibl names as keys with attribute data
    :rtype iblSkyDomeAttributeDict:
    """
    iblSkyDomeAttributeDict = dict()
    for i, lightShape in enumerate(iblShapeList):
        transformName = namehandling.getShortName(iblTransformList[i])
        transformNameNoSuffix = transformName.replace("_{}".format(RENDERER_SUFFIX[rendererNiceName]), "")
        attrValDict = getIblAttr(lightShape, getIntensity=True, getExposure=True, getColor=True, getLightVisible=True,
                                 getIblTexture=True, getTranslation=True, getRotation=True, getScale=True)
        iblSkyDomeAttributeDict[transformNameNoSuffix] = attrValDict
    return iblSkyDomeAttributeDict


def getIblDictSelected(rendererNiceName, includeSelChildren=False):
    """gets a ibl dict with attributes for the current renderer from selection

    :param rendererNiceName: the renderer nicename "Arnold" etc
    :type rendererNiceName: str
    :return iblSkyDomeAttributeDict: the ibl dict with lights as keys and attribute data
    :rtype iblSkyDomeAttributeDict dict
    """
    iblTransformList, iblShapeList = getIblLightSelected(rendererNiceName, includeSelChildren=includeSelChildren)
    if not iblTransformList:
        return dict()
    return getIBLAttrDictList(iblTransformList, iblShapeList, rendererNiceName)


def getIblSkydomeDictOfScene(rendererNiceName):
    """For all the IBL skydomes in a scene return a dictionary of generic attributes.
    The dictionary keys are the lightname (transform node) with the light suffix removed

    :param renderer: nice name of the renderer "Redshift", "Arnold" etc
    :type renderer: str
    :return iblSkyDomeAttributeDict: Dictionary of lights with their attributes in a generic dict
    :rtype iblSkyDomeAttributeDict: dict
    """
    iblTransformList, iblShapeList = getAllIblSkydomeLightsInScene(rendererNiceName)
    # get the attribute dicts
    if not iblShapeList:
        return dict()
    return getIBLAttrDictList(iblTransformList, iblShapeList, rendererNiceName)


def cleanupLights(rendererNiceName, lightsTransformList, selectLights=False):
    """Given the list of lights group them, parent them into the appropriate group if it already exists
    Groups are called something like "RedshiftLights_grp"

    :param rendererNiceName: nice name of the renderer "Redshift", "Arnold" etc
    :type rendererNiceName: str
    :param lightsTransformList: the list of light names of the light transform nodes
    :type lightsTransformList: list
    :param selectLights: select the lights after grouping?
    :type selectLights: bool
    """
    grpName = "|{}{}".format(rendererNiceName, LIGHTGRPNAME)
    if cmds.objExists(grpName):  # group already exists
        for i, light in enumerate(lightsTransformList):
            if cmds.listRelatives(light, parent=True, fullPath=True):  # isn't parented to world
                checkGrpName = cmds.listRelatives(light, parent=True, fullPath=True)[0]
                if namehandling.getShortName(checkGrpName) != grpName:  # parent is not grpName
                    lightsTransformList[i] = cmds.parent(light, grpName)[0]
            else:  # will be parented to world and should be parented to existing grp
                lightsTransformList[i] = cmds.parent(light, grpName)[0]
    else:  # create group as doesn't exist so create it
        grpName = cmds.group(name=grpName, empty=True)  # build so pivot is centered
        for i, light in enumerate(lightsTransformList):
            if cmds.listRelatives(light, parent=True, fullPath=True):  # isn't parented to world
                checkGrpName = cmds.listRelatives(light, parent=True, fullPath=True)[0]
                if namehandling.getShortName(checkGrpName) != grpName:  # parent is not grpName
                    lightsTransformList[i] = cmds.parent(light, grpName)[0]
            else:  # will be parented to world and should be parented to existing grp
                lightsTransformList[i] = cmds.parent(light, grpName)[0]
    if selectLights:
        cmds.select(lightsTransformList, replace=True)
    return lightsTransformList, getLightShapeList(lightsTransformList)


def forceUniqueLightNamesScene(rendererNiceName):
    """Finds all lights in the scene of a Renderer and make sure they are all uniquely named for short names

    If non unique names are found it will rename the lights automatically as per the settings in:

        namehandling.forceUniqueShortNameList(nameList)

    :param rendererNiceName: The renderer nice name eg "Redshift"
    :type rendererNiceName: str
    """
    areaLightTransforms = getAllAreaLightsInScene(rendererNiceName)[0]
    dirLightTransforms = getAllDirectionalLightsInScene(rendererNiceName)[0]
    iblLightTransforms = getAllIblSkydomeLightsInScene(rendererNiceName)[0]
    allLights = areaLightTransforms + dirLightTransforms + iblLightTransforms
    allLightsShort = namehandling.getShortNameList(allLights)
    if len(allLightsShort) != len(set(allLightsShort)):  # Make lights unique
        namehandling.forceUniqueShortNameList(allLights)


def getAllLightsGenericDict(rendererNiceName, getSelected=False, includeSelChildren=False):
    """Retrieves all the area and ibl lights in a scene,
    selected returns selected area lights

    :param rendererNiceName: nice name of the renderer "Redshift", "Arnold" etc
    :type rendererNiceName: str
    :param getSelected: get the selected lights (True) or all lights (False), NOTE** IBLs are always on right now
    :type getSelected: bool
    :param getSelected: when getSelected is True then include the hierarchy of objects selected too.
    :type getSelected: bool
    :return multiLightDict: area lights and ibls {AREALIGHTS: areaAttrDict, IBLSKYDOMES: iblAttrList}
    :rtype multiLightDict: dict
    """
    # Check if light names are non unique
    forceUniqueLightNamesScene(rendererNiceName)
    # Now get the dictionary
    if getSelected:
        areaAttrDict = getLightAttrFromLightSelected(rendererNiceName, includeSelChildren=includeSelChildren)
        iblAttrList = getIblDictSelected(rendererNiceName, includeSelChildren=includeSelChildren)
        dirAttrDict = getDirectionalDictSelected(rendererNiceName, includeSelChildren=includeSelChildren)
    else:
        areaAttrDict = getLightAttrFromLocatorScene(rendererNiceName, message=False)
        dirAttrDict = getDirectionalLightDictOfScene(rendererNiceName)
        iblAttrList = getIblSkydomeDictOfScene(rendererNiceName)
    # Check no clashing names as all names of all lights must be unique
    multiLightDict = {AREALIGHTS: areaAttrDict,
                      IBLSKYDOMES: iblAttrList,
                      DIRECTIONALS: dirAttrDict}

    return multiLightDict


"""
Save Import .json
"""


def saveJsonFile(dictionary, fullFilePath):
    """Saves a json file to disk

    :param dictionary: the dictionary to save as .json
    :type dictionary: dict
    :param fullFilePath: the full file path to save
    :type fullFilePath: str
    """
    jsonFilePath = os.path.join(fullFilePath)
    with open(jsonFilePath, 'w') as outfile:
        json.dump(dictionary, outfile, sort_keys=True, indent=4, ensure_ascii=False)


def saveLightsGenericJson(fullFilePath, rendererNiceName, saveSelect=False):
    """Saves as a .json file the selected or all lights in a scene from the given renderer
    Saves as the generic light dict
    **This function should be depreciated by the exportAbcShaderLights module

    :param fullFilePath: the full file path to save
    :type fullFilePath: str
    :param rendererNiceName: nice name of the renderer "Redshift", "Arnold" etc
    :type rendererNiceName: str
    :param saveSelect: save the selected lights (True) or all lights (False)
    :type saveSelect: bool
    """
    multiLightDict = getAllLightsGenericDict(rendererNiceName, getSelected=False)
    if not multiLightDict[AREALIGHTS] and multiLightDict[IBLSKYDOMES]:
        om2.MGlobal.displayWarning("No Lights Found To Export For {}".format(rendererNiceName))
        return
    saveJsonFile(multiLightDict, fullFilePath)
    om2.MGlobal.displayInfo("Success Generic Lights Saved From {} Lights. "
                            "File Saved {} ".format(rendererNiceName, fullFilePath))


def importLightsGenericDict(multiLightDict, rendererNiceName, selectLights=True, message=True, replaceLights=True):
    """imports (creates the lights) from a multiLightDict, a nested dict file that contains light data

    currently supports directionals, area lights, and IBLs
    Will apply as in the format of the rendererNiceName

    :param fullPathName: the full file path to open
    :type fullPathName: str
    :param rendererNiceName: nice name of the renderer "Redshift", "Arnold" etc
    :type rendererNiceName: str
    :param selectLights: will select all the lights after import
    :type selectLights: bool
    :return allLightTransforms: All the light transforms created
    :rtype allLightTransforms: list
    :return allLightShapes: All the light shape nodes created
    :rtype allLightShapes: list
    """
    lightTransformList = list()
    lightShapeList = list()
    directionalTransformList = list()
    directionalShapeList = list()
    iblTransformList = list()
    iblShapeList = list()
    # create the lights
    if replaceLights:
        deleteAllLightsInScene(rendererNiceName, message=False)
    if multiLightDict[AREALIGHTS]:  # area light import
        for lightName, attrGenericDict in multiLightDict[AREALIGHTS].items():
            lightTransform, lightShape = createAreaLightFromDict(attrGenericDict, rendererNiceName,
                                                                 lightName=lightName,
                                                                 replaceLight=True, cleanup=True)
            lightTransformList.append(lightTransform)
            lightShapeList.append(lightShape)
    if multiLightDict[IBLSKYDOMES]:  # ibl skydome light import
        for lightName, attrGenericDict in multiLightDict[IBLSKYDOMES].items():
            lightTransform, lightShape = createSkydomeLightDictRenderer(attrGenericDict, lightName, rendererNiceName,
                                                                        warningState=False)
            iblTransformList.append(lightTransform)
            iblShapeList.append(lightShape)
    if DIRECTIONALS in multiLightDict:  # if older file format then the key "DIRECTIONALS" may no exist
        if multiLightDict[DIRECTIONALS]:  # then import the directional lights
            for lightName, attrGenericDict in multiLightDict[DIRECTIONALS].items():
                directionalTransform, \
                directionalShape, \
                warningState = createDirectionalDictRenderer(attrGenericDict, lightName, rendererNiceName,
                                                             warningState=False, cleanup=True, suffix=True)
                directionalTransformList.append(directionalTransform)
                directionalShapeList.append(directionalShape)
    allLightTransforms = lightTransformList + iblTransformList + directionalTransformList
    allLightShapes = lightShapeList + iblShapeList + directionalShapeList
    if message:
        transformListUnique = namehandling.getUniqueShortNameList(allLightTransforms)
        om2.MGlobal.displayInfo("Success: {} Lights Created {}".format(rendererNiceName, transformListUnique))
    if selectLights == True:
        cmds.select(allLightTransforms, replace=True)
    return allLightTransforms, allLightShapes


"""
CONVERT LIGHTS RENDERER
"""


def convertLights(fromRenderer, toRenderer):
    """Converts all lights in a scene from the fromRenderer to the to renderer
    Currently supports area lights and IBLs only

    :param fromRenderer: the rendererNiceName to convert from
    :type fromRenderer: str
    :param toRenderer: the rendererNiceName to convert to
    :type toRenderer: str
    """
    areaLightsBuilt = False
    skydomeIblBuilt = False
    deleteAllLightLocsInScene()
    lightLocatorlist, warning = createLocatorLightScene(fromRenderer)
    if not warning:  # the locs were created so convert
        createAreaLightsFromAllLocs(toRenderer)
        areaLightsBuilt = True
        deleteAllLightLocsInScene()
    # create IBL Skydomes
    iblSkyDomeAttributeList = getIblSkydomeDictOfScene(fromRenderer)  # get all IBLS and create dictionary
    if iblSkyDomeAttributeList:  # skydomes found
        for lightName, attrGenericDict in iblSkyDomeAttributeList.items():
            createSkydomeLightDictRenderer(attrGenericDict, lightName, toRenderer, warningState=False)
        skydomeIblBuilt = True
    if not skydomeIblBuilt and not areaLightsBuilt:
        om2.MGlobal.displayWarning("No valid lights not found to convert from the `{}` renderer".format(fromRenderer))
        return
    om2.MGlobal.displayInfo("Success: {} Lights Built from the `{}` renderer".format(toRenderer, fromRenderer))
