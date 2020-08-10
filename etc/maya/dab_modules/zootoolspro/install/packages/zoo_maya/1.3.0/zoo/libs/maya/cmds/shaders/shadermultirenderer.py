import json
import os

import maya.api.OpenMaya as om2
import maya.cmds as cmds
from zoo.libs.maya.cmds.objutils import attributes, namehandling, objhandling, namewildcards
from zoo.libs.maya.cmds.renderer.rendererconstants import RENDERMAN, REDSHIFT, ARNOLD, RENDERER_SUFFIX
from zoo.libs.maya.cmds.shaders import arnoldshaders, redshiftshaders, rendermanshaders, redshiftaovs, rendermanaovs, \
    arnoldaovs, shaderutils
from zoo.libs.utils import colour

# default keys for the generic shader dicts
DIFFUSE = 'gDiffuseColor_srgb'
DIFFUSEWEIGHT = 'gDiffuseWeight'
SPECWEIGHT = 'gSpecWeight'
SPECCOLOR = 'gSpecColor_srgb'
SPECROUGHNESS = 'gSpecRoughness'
SPECIOR = 'gSpecIor'
COATCOLOR = 'gCoatColor_srgb'
COATWEIGHT = 'gCoatWeight'
COATROUGHNESS = 'gCoatRoughness'
COATIOR = 'gCoatIor'

GEN_KEY_LIST = [DIFFUSE, DIFFUSEWEIGHT,
                SPECWEIGHT, SPECCOLOR, SPECROUGHNESS, SPECIOR,
                COATCOLOR, COATWEIGHT, COATROUGHNESS, COATIOR]

# Default keys for simple textures
TEXTURE_NODE = "textureNode"  # The name of the node connected to the shader
TEXTURE_SOURCE_ATTRIBUTE = "textureSourceAttr"  # The source attribute of the texture connecting to the shader
TEXTURE_DESTINATION_GEN_KEY = "textureDestinationGenKey"

# Shader types
REDSHIFTMATERIAL = "RedshiftMaterial"
PXRSURFACE = "PxrSurface"
PXRLAYEREDSURFACE = "PxrLayeredSurface"
AISTANDARDSURFACE = "aiStandardSurface"

RENDERERSHADERS = {REDSHIFT: [REDSHIFTMATERIAL],
                   RENDERMAN: [PXRSURFACE],
                   ARNOLD: [AISTANDARDSURFACE]}

SHADERMATCHPREFIX = "duplctS"

SHADERNAME = "shaderName"
OBJECTSFACES = "objectFaces"
ATTRSHADERDICT = "attributesShaderDict"

RENDERER_SHADERS_DICT = {REDSHIFT: ["RedshiftMaterial"],
                         RENDERMAN: ["PxrSurface",
                                     "PxrLayeredSurface"],
                         ARNOLD: ["aiStandardSurface"]}

def getShadersSceneRenderer(rendererNiceName):
    """Returns all shaders in a scene of the renderer, only supported shaders as per RENDERERSHADERS

    :param rendererNiceName: the nice name of the renderer
    :type rendererNiceName: str
    :return shaderList:  A list of shaders of the renderer type
    :rtype shaderList: list(str)
    """
    return cmds.ls(type=RENDERERSHADERS[rendererNiceName][0])


def getRendererFromShaderType(shaderType):
    """given an Shader Type return the nice name of the renderer

    :param shaderType: the type of the shader eg "PxrSurface"
    :type shaderType: str
    :return renderer: Nice name of the supported renderer
    :rtype renderer: str
    """
    for renderer, shadTypeList in RENDERERSHADERS.items():
        for shadType in shadTypeList:
            if shaderType == shadType:
                return renderer
    return ""  # if none found then return null


def listCompatibleShaders():
    """returns a list of all the compatible shader types, "RedshiftMaterial", "PxrSurface" etc

    :return compatibleShaderList: shader node type names
    :rtype compatibleShaderList: list
    """
    compatibleShaderList = list()
    for renderer in RENDERER_SHADERS_DICT:
        for shader in RENDERER_SHADERS_DICT[renderer]:
            compatibleShaderList.append(shader)
    return compatibleShaderList


def getAllSupportedRenderers():
    """returns all supported renderers in order from the RENDERERSHADERS dict
    """
    allRenderersList = list()
    for renderer, shaderList in RENDERERSHADERS.items():
        allRenderersList.append(renderer)
    allRenderersList.sort()
    return allRenderersList


def getAllSupportedShaders():
    """returns all the supported shaders in order from the RENDERERSHADERS dict
    """
    allShadersList = list()
    for renderer, shaderList in RENDERERSHADERS.items():
        for shader in shaderList:
            allShadersList.append(shader)
    allShadersList.sort()
    return allShadersList


def testIfSupportedShader(shader):
    """Tests to see if the shader is supported

    :param shader: a shader name
    :type shader: str
    :return isSupported: The node type of the shader if it's supported, None if not supported
    :rtype isSupported: bool
    """
    if not shader:  # Can be no connected shader
        return None
    nodeType = cmds.nodeType(shader)
    supportedShaderList = getAllSupportedShaders()
    if nodeType in supportedShaderList:
        return nodeType
    return None


def autoTypeShader(rendererNiceName):
    """Returns the most common uber shader from a given renderer nice name

    :param rendererNiceName: the nice name of the renderer
    :type rendererNiceName: str
    :return shaderType: the type of the shader node
    :rtype shaderType: str
    """
    if REDSHIFT == rendererNiceName:
        return RENDERERSHADERS[REDSHIFT][0]
    if ARNOLD == rendererNiceName:
        return RENDERERSHADERS[ARNOLD][0]
    if RENDERMAN == rendererNiceName:
        return RENDERERSHADERS[RENDERMAN][0]


def convertShaderDictToLinearColor(shaderDict):
    """Converts a shader dict (not nested) to linear color
    by finding attributes with suffixes "_srgb" and converting those

    :param shaderDict: a dict of shader attributes with generic shader attributes as keys, not a nested dict
    :type shaderDict: dict
    :param shaderDict: shader attributes now with srgb colors converted to linear
    :type shaderDict: dict
    """
    for attr, value in shaderDict.items():
        if "_srgb" in attr:  # convert attributes with suffix _srgb to linear color values for Maya
            shaderDict[attr] = colour.convertColorSrgbToLinear(value)
    return shaderDict


def convertPresetShadersDictToLinear(presetShadersDict):
    """Converts a presetShaderDict (generic preset shader info) to be in linear color
    by finding attributes with suffixes "_srgb" and converting those

    :param presetShadersDict: nested dictionary of preset generic shader info (maya attr)
    :type presetShadersDict: dict
    :return presetShadersDict: preset generic shader info now in linear color
    :rtype presetShadersDict: dict
    """
    for presetName, presetDict in presetShadersDict.items():
        for attr, value in presetDict.items():
            if "_srgb" in attr:  # convert attributes with suffix _srgb to linear color values for Maya
                presetShadersDict[presetName][attr] = colour.convertColorSrgbToLinear(value)
    return presetShadersDict


def getShaderDict(filename='shaderpresets_ior.json', convertSrgbToLinear=True):
    """Loads the .json file of the shader presets

    :param filename: the name of the json file, filename only, should be in same directory as this file
    :type filename: str
    :return presetShaderDict: The .json file as a python dict
    :rtype presetShaderDict: dict
    """
    jsonShaderFilePath = os.path.join(os.path.dirname(__file__), filename)
    with open(jsonShaderFilePath) as data_file:
        presetShadersDict = json.load(data_file)
    if convertSrgbToLinear:  # iterate through keys and convert the colors to linear based off the suffix convention
        convertPresetShadersDictToLinear(presetShadersDict)
    return presetShadersDict


def getShaderPresetNamesList(presetShadersDict, firstInList="Matte Grey"):
    """retrieves the Preset Shader names in alphabetical order
    ["Copper", "Car Paint Blue", "Car Paint Red"]
    First in list must exist in the list or it will fail

    :param presetShadersDict: nested dictionary of preset generic shader info (maya attr)
    :type presetShadersDict: dict
    :param firstInList: if exists chooses this value at the top of the list, if empty or none no changes will be made
    :type firstInList: bool
    :return presetShadersList: list of shaders in alphabetical order
    :rtype presetShadersList: list
    """
    presetShadersList = sorted(presetShadersDict.keys())
    if firstInList:
        presetShadersList.insert(0, presetShadersList.pop(presetShadersList.index(firstInList)))
    return presetShadersList


def redshiftMaterialAttributes():
    """attribute conversion names for RedshiftMaterial Shader

    :return shaderDict: redshiftMaterialAttributes dictionary
    :rtype shaderDict: dict
    """
    return {DIFFUSE: "diffuse_color",
            DIFFUSEWEIGHT: "diffuse_weight",
            SPECWEIGHT: "refl_weight",
            SPECCOLOR: "refl_color",
            SPECROUGHNESS: "refl_roughness",
            SPECIOR: "refl_ior",
            COATCOLOR: "coat_color",
            COATWEIGHT: "coat_weight",
            COATROUGHNESS: "coat_roughness",
            COATIOR: "coat_ior"}


def aiStandardSurfaceAttributes():
    """attribute conversion names for aiStandardSurface Shader

    :return shaderDict: aiStandardSurface dictionary
    :rtype shaderDict: dict
    """
    return {DIFFUSE: "baseColor",
            DIFFUSEWEIGHT: "base",
            SPECWEIGHT: "specular",
            SPECCOLOR: "specularColor",
            SPECROUGHNESS: "specularRoughness",
            SPECIOR: "specularIOR",
            COATCOLOR: "coatColor",
            COATWEIGHT: "coat",
            COATROUGHNESS: "coatRoughness",
            COATIOR: "coatIOR"}


def pxrSurfaceAttributes():
    """attribute conversion names for PxrSurface Shader

    :return shaderDict: PxrSurface dictionary
    :rtype shaderDict: dict
    """
    return {DIFFUSE: "diffuseColor",
            DIFFUSEWEIGHT: "diffuseGain",
            SPECWEIGHT: SPECWEIGHT,  # doesn't exist!!
            SPECCOLOR: "specularEdgeColor",
            SPECROUGHNESS: "specularRoughness",
            SPECIOR: "specularIor",
            COATCOLOR: "clearcoatEdgeColor",
            COATWEIGHT: COATWEIGHT,  # doesn't exist!!
            COATROUGHNESS: "clearcoatRoughness",
            COATIOR: "clearcoatIor"}


def pxrSurfaceFixAttrValues(shaderDict):
    """this function fixes the pxrSurface attributes while applying as it is missing the spec and coat weights,
    and the default mode is in artistic not physical for spec and coat
    Some math has to be done in srgb color, incoming is in linear and outgoing too

    :param shaderDict: a dict of shader attributes with generic shader attributes as keys, not a nested dict
    :type shaderDict: dict
    :param shaderDict: a dict of shader attributes with generic shader attributes as keys, not a nested dict
    :type shaderDict: dict
    """
    for key, value in shaderDict.items():
        if key == "specularIor" or key == "clearcoatIor":  # convert to a color
            shaderDict[key] = (value, value, value)
    # add new attributes to change the specularFresnelMode
    shaderDict["specularFresnelMode"] = 1
    shaderDict["clearcoatFresnelMode"] = 1
    # convert color to srgb for the math
    shaderDict["specularEdgeColor"] = colour.convertColorLinearToSrgb(shaderDict["specularEdgeColor"])
    shaderDict["clearcoatEdgeColor"] = colour.convertColorLinearToSrgb(shaderDict["clearcoatEdgeColor"])
    # multiply the value of the spec weight and coat weight by the spec coat colors, since there's no spec weight
    shaderDict["specularEdgeColor"] = ((shaderDict["specularEdgeColor"][0] * shaderDict[SPECWEIGHT]),
                                       (shaderDict["specularEdgeColor"][1] * shaderDict[SPECWEIGHT]),
                                       (shaderDict["specularEdgeColor"][2] * shaderDict[SPECWEIGHT]))
    shaderDict["clearcoatEdgeColor"] = ((shaderDict["clearcoatEdgeColor"][0] * shaderDict[COATWEIGHT]),
                                        (shaderDict["clearcoatEdgeColor"][1] * shaderDict[COATWEIGHT]),
                                        (shaderDict["clearcoatEdgeColor"][2] * shaderDict[COATWEIGHT]))
    # convert the colors back to linear
    shaderDict["specularEdgeColor"] = colour.convertColorSrgbToLinear(shaderDict["specularEdgeColor"])
    shaderDict["clearcoatEdgeColor"] = colour.convertColorSrgbToLinear(shaderDict["clearcoatEdgeColor"])
    # specWeight and coatWeight aren't supported so make None
    shaderDict[SPECWEIGHT] = None
    shaderDict[COATWEIGHT] = None
    return shaderDict


def aiSurfaceStandardFixAttrValues(shaderDict):
    """Fixes the aiSurfaceStandard as the color is always white, no matter so should be used on the weight

    Newer versions of Arnold are no better, tried using the if and else on Arnold version but it's still wrong.

    legacy code:

        mtoaMajorVersion = arnoldshaders.mtoaVersionNumber()[0]
            if mtoaMajorVersion < 4:
                convert color to hsv

    :param shaderDict: a dict of shader attributes with generic shader attributes as keys, not a nested dict
    :type shaderDict: dict
    :param shaderDict: a dict of shader attributes with generic shader attributes as keys, not a nested dict
    :type shaderDict: dict
    """
    hsvColor = colour.convertRgbToHsv(shaderDict["coatColor"])
    # weight = color value times weight
    shaderDict["coat"] = hsvColor[2] * shaderDict["coat"]
    if shaderDict["coat"] > 1.0:  # need to clamp as easy to go 1.0045
        shaderDict["coat"] = 1.0
    # color value = pure brightness
    hsvColor = (hsvColor[0], hsvColor[1], 1)
    shaderDict["coatColor"] = colour.convertHsvToRgb(hsvColor)
    return shaderDict


def getShadersSelectedRenderer(renderer, reportSelError=False):
    """Returns all shaders associated with the selection and then filters them by the given Renderer

    :param renderer: "Arnold", "Redshift" or "Renderman"
    :type renderer: str
    :param reportSelError: Give a message if there are issues to the user
    :type reportSelError: bool
    :return shaderList: Shaders related to selected object of the rendertype from RENDERERSHADERS dict
    :rtype shaderList: list(str)
    """
    shaderList = list()
    allShaderList = shaderutils.getShadersFromSelectedNodes(reportSelError=reportSelError)
    for shader in allShaderList:
        nodeType = RENDERERSHADERS[renderer][0]
        if cmds.nodeType(shader) == nodeType:
            shaderList.append(shader)
    return shaderList


def getFirstSupportedShaderSelected(reportSelError=False, message=True):
    """Find a the first supported shader from selected

    :param reportSelError: Report selection issues to the user
    :type reportSelError: bool
    :param message: report messages to the user?
    :type message: bool
    :return shaderName: the name of the first found shader
    :rtype shaderName: str
    :return shaderType: the Maya type of the first found shader
    :rtype shaderType: str
    """
    shaderName = ""
    shaderType = ""
    shaderList = shaderutils.getShadersFromSelectedNodes(reportSelError=reportSelError)  # grab the first shader name
    if not shaderList:
        if reportSelError and message:
            om2.MGlobal.displayWarning("No shaders or objects with this shader type selected")
        return shaderName, shaderType  # will be empty
    for shader in shaderList:  # iterate through shaders to find a supported type, pass on the first found
        shaderType = testIfSupportedShader(shader)
        if shaderType:
            shaderName = shader
            return shaderName, shaderType
    if not shaderName:  # no legit shaders found
        if message:
            compatibleShaderList = listCompatibleShaders()
            om2.MGlobal.displayWarning("The active shader is not supported. "
                                       "Shader must not be a lambert, blinn etc, "
                                       "supported types {}".format(compatibleShaderList))
        return shaderName, shaderType  # shaderName will be empty


def buildNameWithSuffix(shaderName, suffix, renderer):
    """Returns the shader name given the name without a suffix, the suffix bool (checkbox) and the renderer

    :param shaderName: The name of the shader without it's suffix
    :type shaderName: str
    :param suffix: Is there a suffix or not?
    :type suffix: bool
    :param renderer: The nice name of the renderer
    :type renderer: str
    :return fullShaderName: The full shader name with suffix if the suffix = True
    :rtype fullShaderName: str
    """
    if not suffix:
        return shaderName
    newSuffix = RENDERER_SUFFIX[renderer]
    return "_".join([shaderName, newSuffix])


def supportedShaderType(shader, message=True):
    """Get the supported shader type, None if it is not supported.

    :param shader: The name of a shader that exists in Maya
    :type shader: str
    :param message: report messages to the user
    :type message: bool
    :return shaderType: The node type of the shader if supported, None if not supported.
    :rtype shaderType: str
    """
    shaderType = testIfSupportedShader(shader)  # get shaderType
    if not shaderType:
        if message:
            om2.MGlobal.displayWarning("The shader type is not supported for shader `{}`. "
                                       "The shader must not be blinn lambert etc".format(shader))
        return None
    return shaderType


def renameShaderUniqueSuffix(oldName, newName, message=True):
    """renames a shader and auto adds the appropriate suffix

    :param oldName: the old/current shader name
    :type oldName: str
    :param newName: the new name without a suffix
    :type newName: str
    :param message: shows the result message to the user
    :type message: bool
    :return shaderNewName: the shader's new name, shader has been renamed to this
    :rtype shaderNewName: str
    """
    shaderType = testIfSupportedShader(oldName)  # get shaderType
    if not shaderType:
        om2.MGlobal.displayWarning("There are no supported shaders connected to the selected objects")
        return None
    renderer = getRendererFromShaderType(shaderType)
    newSuffix = RENDERER_SUFFIX[renderer]
    if "_".join([newName, newSuffix]) == oldName:  # if name is already the same
        return oldName
    shaderNewName = namehandling.getUniqueNameSuffix(newName, newSuffix)  # get unique name
    shaderNewName = cmds.rename(oldName, shaderNewName)  # rename
    if message:
        om2.MGlobal.displayInfo("Success: Shader `{}` renamed to `{}`".format(oldName, shaderNewName))
    return shaderNewName


def getShaderAttributesDict(shaderType):
    """Returns the shader attributes of a given shader type.  Shader type will be important when multi shader support.

    :param shaderType:  The type of shader `redshiftMaterial`, `PxrSurface` etc
    :type shaderType: str
    :return attrDict: the attributes with conversions types as a dictionary
    :rtype attrDict: dict
    """
    if shaderType == REDSHIFTMATERIAL:
        return redshiftMaterialAttributes()  # using a function as dict gets overridden with messy code
    elif shaderType == AISTANDARDSURFACE:
        return aiStandardSurfaceAttributes()  # using a function as dict gets overridden with messy code
    elif shaderType == PXRSURFACE:
        return pxrSurfaceAttributes()  # using a function as dict gets overridden with messy code
    else:
        attrDict = {}
        om2.MGlobal.displayWarning('Shader Type Not Found {}'.format(shaderType))
        return attrDict


def getShaderPresetShaders(shaderType, convertSrgbToLinear=True):
    """Given a shader type will return the shaderDict (from .json file)
    now with all the attributes renamed to suit the current shader type
    ie. RedshiftMaterial `diffuseColor` attribute becomes, `diffuse_color`

    :param shaderType:  The type of shader `RedshiftMaterial`, `PxrSurface` etc
    :type shaderType: str
    :return: the shaderDict now with new attribute keys to match the current shader
    :rtype: dict
    """
    presetShadersDict = getShaderDict(convertSrgbToLinear=convertSrgbToLinear)
    attrDict = getShaderAttributesDict(shaderType)  # get the conversion dict for this shader
    if not attrDict:  # if shader convert failed
        return {}
    for key, presetDict in presetShadersDict.items():  # converts the attributes in dict to this shader naming
        newPresetDict = {}  # creates a new dict with the new attributes from the given shader
        for attr, value in presetDict.items():
            newPresetDict[attrDict[attr]] = presetDict[attr]  # assign the old attribute value while creating new key
        presetShadersDict[key] = newPresetDict  # replace the new dict for the old
    return presetShadersDict


def setPresetShaderAttrs(shaderName, presetShaderName, shaderType):
    """Will set the maya shader's attributes to the preset type
    shader type must be given and attributes will be converted
    "shader1", "Gold", "PxrSurface"

    :param shaderName: The maya name of the shader, could be any user defined name
    :type shaderName: str
    :param presetShaderName: the key name of the shader preset `Gold` `Matte Grey`
    :type presetShaderName: str
    :param shaderType: the type of shader, `RedshiftMaterial` `PxrSurface` `alStandardSurface` etc
    :type shaderType: str
    """
    presetShadersDict = getShaderPresetShaders(shaderType)  # get the preset shaders dict and convert to shader type
    shaderDict = presetShadersDict[presetShaderName]  # get the individual shader dict
    attributes.setAttrributesFromDict(shaderName, shaderDict, message=False)  # set the attributes on the shader


def setShaderAttrs(shaderName, shaderType, shaderDict, convertSrgbToLinear=True, reportMessage=True):
    """Will set the maya shader's attributes to the preset type,
    this is from a single shader input not presets

    :param shaderName: The maya name of the shader, could be any user defined name
    :type shaderName: str
    :param shaderType: the type of shader, `RedshiftMaterial` `pxrSurface` `alStandardSurface` etc
    :type shaderType: str
    :param shaderDict: a dict of shader attributes with generic shader attributes as keys, not a nested dict
    :type shaderDict: dict
    :param reportMessage: report the success message or hid it?
    :type reportMessage: bool
    """
    if convertSrgbToLinear:
        shaderDict = convertShaderDictToLinearColor(shaderDict)  # convert linear color applicable attrs
    attrDict = getShaderAttributesDict(shaderType)  # get the shaderTypeConversion dict
    convertedShaderDict = {}
    for attr in shaderDict:  # transfer the values of the shader dict to the converted dict
        if attrDict[attr] is not None:
            convertedShaderDict[attrDict[attr]] = shaderDict[attr]
    if shaderType == PXRSURFACE:  # fix the PxrShader as there are a number of issues with it
        convertedShaderDict = pxrSurfaceFixAttrValues(convertedShaderDict)
    if shaderType == AISTANDARDSURFACE:  # aiSurfaceStandard clear coat color can only be white and use value as weight
        convertedShaderDict = aiSurfaceStandardFixAttrValues(convertedShaderDict)
    # Check attributes have no incoming connections like textures
    for attr in convertedShaderDict:
        if convertedShaderDict[attr] is not None:
            if cmds.listConnections(".".join([shaderName, attr]), destination=False, source=True):
                convertedShaderDict[attr] = None
    # Set the attributes
    attributes.setAttrributesFromDict(shaderName, convertedShaderDict, message=False)
    if reportMessage:
        om2.MGlobal.displayInfo('Success: Shader Attributes Set On {}'.format(shaderName))


def createShaderTypeObjList(shaderType, objList=None, shaderName="shader", specWeight=0.0, message=True,
                            rgbColor=(.5, .5, .5)):
    """Creates a shader give the type, supports main monolithic shaders in Redshift, Arnold and Renderman
    Assigns to an object list if it exists

    :param shaderType: the type of shader, `RedshiftMaterial` `PxrSurface` `alStandardSurface` etc
    :type shaderType: str
    :param objList: list to assign the shader to, can be None
    :type objList: list()
    :param shaderName: The maya name of the shader, could be any user defined name
    :type shaderName: str
    :param specWeight: the default specular weight
    :type specWeight: float
    :param message: return the messages to the user
    :type message: bool
    :param rgbColor: the diffuse color of the shader
    :type rgbColor: tuple
    :return shaderName: the shader name created
    :rtype shaderName: str
    """
    if shaderType == REDSHIFTMATERIAL:
        shaderName = redshiftshaders.assignNewRedshiftMaterial(objList, shaderName=shaderName, specWeight=specWeight,
                                                               message=message, rgbColor=rgbColor)
    elif shaderType == AISTANDARDSURFACE:
        shaderName = arnoldshaders.assignNewAiStandardSurface(objList, shaderName=shaderName, specWeight=specWeight,
                                                              message=message, rgbColor=rgbColor)
    elif shaderType == PXRSURFACE:
        shaderName = rendermanshaders.assignNewPxrSurface(objList, shaderName=shaderName, specWeight=specWeight,
                                                          message=message, rgbColor=rgbColor)
    else:
        om2.MGlobal.displayWarning('Shader Type Not Found, Or Not Supported `{}`'.format(shaderType))
    return shaderName


def createShaderTypeSelected(shaderType, shaderName="shader", specWeight=0.0, message=True, rgbColor=(.5, .5, .5)):
    """Creates a shader give the type, supports main monolithic shaders in Redshift, Arnold and Renderman

    :param shaderType: the type of shader, `RedshiftMaterial` `PxrSurface` `alStandardSurface` etc
    :type shaderType: str
    :param shaderName: The maya name of the shader, could be any user defined name
    :type shaderName: str
    :param specWeight: the default specular weight
    :type specWeight: float
    :param message: return the messages to the user
    :type message: bool
    :param rgbColor: the diffuse color of the shader
    :type rgbColor: tuple
    :return shaderName: the shader name created
    :rtype shaderName: str
    """
    objList = cmds.ls(selection=True)
    return createShaderTypeObjList(shaderType, objList=objList, shaderName=shaderName, specWeight=specWeight,
                                   message=True,
                                   rgbColor=rgbColor)


def createShaderType(shaderType, shaderName="shader", specWeight=0.0, message=True, rgbColor=(.5, .5, .5)):
    """Creates a shader of the given type

    :param shaderType: the type of shader, `RedshiftMaterial` `PxrSurface` `alStandardSurface` etc
    :type shaderType: str
    :param shaderName: The maya name of the shader, could be any user defined name
    :type shaderName: str
    :param specWeight: the default specular weight
    :type specWeight: float
    :param message: return the messages to the user
    :type message: bool
    :param rgbColor: the diffuse color of the shader
    :type rgbColor: tuple
    :return shaderName: The maya name of the shader, could be any user defined name
    :rtype shaderName: str
    """
    if shaderType == REDSHIFTMATERIAL:
        shaderName = redshiftshaders.createRedshiftMaterial(shaderName=shaderName, specWeight=specWeight,
                                                            message=message, rgbColor=rgbColor)
    elif shaderType == AISTANDARDSURFACE:
        shaderName = arnoldshaders.createAiStandardSurface(shaderName=shaderName, specWeight=specWeight,
                                                           message=message, rgbColor=rgbColor)
    elif shaderType == PXRSURFACE:

        shaderName = rendermanshaders.createPxrSurface(shaderName=shaderName, specWeight=specWeight,
                                                       message=message, rgbColor=rgbColor)
    return shaderName


def checkShaderRendererMatch(shader, renderer):
    """checks the shader type and current renderer match, returns True if match, False if not a match

    Used in UIs to check is correct

    :param shader: shader name
    :type shader: str
    :param renderer: renderer name
    :type renderer: str
    :return: Match, True if the shader is of the renderer type
    :rtype: bool
    """
    if not cmds.objExists(shader):
        return False
    shaderType = cmds.objectType(shader)
    for type in RENDERERSHADERS[renderer]:
        if shaderType == type:
            return True
    return False


def getShaderTexturedAttrs(shader, renderer):
    """Returns a list of attributes that have incoming source connections, usually textures.

    Attributes are generic attributes and not the shader's attributes

    :param shader: The shader node name
    :type shader: str
    :return genericKeyList: A list of generic attributes that have incoming source connections
    :rtype genericKeyList: list(str)
    """
    genericKeyList = list()
    nodeType = RENDERERSHADERS[renderer][0]
    attributesDict = getShaderAttributesDict(nodeType)  # gets the current shader type and returns the attributes
    # Convert attributes back to generic attributes
    for genKey, attr in attributesDict.items():
        if genKey != attr:  # If the keyAttr and Attr match then the attribute is null and doesn't exist
            if cmds.listConnections(".".join([shader, attr]), destination=False, source=True):
                genericKeyList.append(genKey)  # Appends the generic attribute name
    return genericKeyList


def getTexturedInfo(shader, renderer):
    """Creates a dictionary with texture information. Used by convert renderer to rehook textures

    Example:

        {"gDiffuseColor_srgb": "fileTexture01.outColor",
        "gSpecRoughness": "fileTexture02.outAlpha"}

    No textures will be an empty dict.

    :param shader: A maya shader node
    :type shader: str
    :param renderer: Renderer name
    :type renderer: str
    :return shaderTextureDict: Dictionary with generic attributes as keys and "node.attribute" as values
    :rtype shaderTextureDict:
    """
    shaderTextureDict = dict()  # keys will be generic attributes
    nodeType = RENDERERSHADERS[renderer][0]
    attributesDict = getShaderAttributesDict(nodeType)  # gets the current shader type and returns the attributes
    # Convert attributes back to generic attributes
    for genKey, attr in attributesDict.items():  # genKey is generic key and attr is the actual shader attribute
        if genKey != attr:  # if the keyAttr and Attr match then the attribute is null and doesn't exist
            sourceConnectionList = cmds.listConnections(".".join([shader, attr]),
                                                        destination=False,
                                                        source=True,
                                                        plugs=True)
            if sourceConnectionList:
                shaderTextureDict[genKey] = sourceConnectionList[0]  # node.attribute of the texture or first node
    return shaderTextureDict


def getShaderAttributes(shader):
    """Pulls shader attributes from the given shader and enters them into a generic attributes dict

    Note: Querying textured attributes returns either black or zero, may have to handle later

    :param shader: The shader name
    :type shader: str
    :return attributesDict: dictionary of generic shader attributes correctly converted
    :rtype attributesDict: dict()
    """
    if not shader:  # can be no shader assigned
        return dict()
    nodeType = cmds.nodeType(shader)
    attributesDict = getShaderAttributesDict(nodeType)  # gets the current shader type and returns the attributes
    if not attributesDict:  # empty dict so return early as the nodetype isn't supported
        return attributesDict
    # convert attributes back to generic attributes
    for keyAttr, attr in attributesDict.items():
        if keyAttr != attr:  # if the keyAttr and Attr match then the attribute is null and doesn't exist
            attributesDict[keyAttr] = cmds.getAttr(".".join([shader, attr]))  # assign the value of the attr to the key
            if type(attributesDict[keyAttr]) is list:  # maya embeds the tuples in lists so unembed
                attributesDict[keyAttr] = attributesDict[keyAttr][0]
            if "_srgb" in keyAttr:  # the color pulled from Maya is linear so convert to srgb
                attributesDict[keyAttr] = colour.convertColorLinearToSrgb(attributesDict[keyAttr])
    # Do renderman PxrSurface conversion which doesn't support spec weight or coat weight
    if nodeType == PXRSURFACE:
        if SPECWEIGHT == attributesDict[SPECWEIGHT]:  # spec weight isn't supported by all renderers
            attributesDict[SPECWEIGHT] = 1.0
        if COATWEIGHT == attributesDict[COATWEIGHT]:  # coat weight isn't supported by all renderers
            attributesDict[COATWEIGHT] = 1.0
        if type(attributesDict[SPECIOR]) is tuple:  # if spec ior is a tuple then it's a color take the first value
            attributesDict[SPECIOR] = attributesDict[SPECIOR][0]
        if type(attributesDict[COATIOR]) is tuple:  # if coat ior is a tuple then it's a color take the first value
            attributesDict[COATIOR] = attributesDict[COATIOR][0]
    # return as a dict in generic format
    return attributesDict


def getShaderSelected(reportNoneFoundError=False, shaderName=""):
    """Pulls shader attributes from the given selection and enters them into a generic attributes dict
    will cycle through a list returning one shader, the first legitimate type found

    :param reportNoneFoundError: Report none found to the user
    :type reportNoneFoundError: bool
    :param shaderName: Return this if it's in the scene and nothing else was found
    :type shaderName: bool

    :return attributesDict: dictionary of generic shader attributes correctly converted
    :rtype attributesDict: dict
    """
    nameMatch = False
    shaderList = shaderutils.getShadersFromSelectedNodes()
    attributesDict = dict()
    if not shaderList:
        if shaderName:
            if not cmds.objExists(shaderName):
                if reportNoneFoundError:
                    om2.MGlobal.displayWarning('No shaders found. Please select nodes linked to a shader')
                return attributesDict, nameMatch
        else:
            if reportNoneFoundError:
                om2.MGlobal.displayWarning('No shaders found. Please select nodes linked to a shader')
            return attributesDict, nameMatch
        nameMatch = True
        shaderList = [shaderName]
    for shader in shaderList:
        if getShaderAttributes(shader):  # if the shader is legitimate and can be processed
            attributesDict = getShaderAttributes(shader)
            return attributesDict, nameMatch
    compatibleShaderList = listCompatibleShaders()
    if not shaderList[0]:
        if reportNoneFoundError:
            om2.MGlobal.displayWarning('No shaders found. Please select nodes linked to a shader')
        return attributesDict, False
    om2.MGlobal.displayWarning("The active shader is not supported. "
                               "Shader must not be a blinn or lambert etc. "
                               "Must be one of these types {}".format(compatibleShaderList))
    return attributesDict, nameMatch


def getShaderList(shaderList):
    """From a shader list pull the shader attributes into a dictionary of attributes
    Returns a nested dict with each key the shader name

    :param shaderList: a list of shader names, should be in scen no error checking
    :type shaderList: list
    :return shaderListAttributesDict: a nested dictionary of the shader name, then the dict of generic attribute values
    :rtype shaderListAttributesDict: dict
    """
    shaderListAttributesDict = dict()
    for shader in shaderList:
        attributesDict = getShaderAttributes(shader)
        shaderListAttributesDict[shader] = attributesDict
    return shaderListAttributesDict


def getShaderObjectAssignDict(shader, removeSuffix=True):
    """Pulls nested dict with the shader information as a generic dict, shadername, and object/face assignements

    :param shader: Maya shader name
    :type shader: str
    :return shaderObjAssignDict: dict containing shader info such as the attributesDict, shader name and obj assignments
    :rtype shaderObjAssignDict:
    """
    attributesDict = getShaderAttributes(shader)  # the generic attributes of the shader
    objectsFaces = shaderutils.getObjectsFacesAssignedToShader(shader)
    if removeSuffix:
        shader = shaderutils.removeShaderSuffix(shader)
    shaderObjAssignDict = {SHADERNAME: shader,
                           OBJECTSFACES: objectsFaces,
                           ATTRSHADERDICT: attributesDict}
    return shaderObjAssignDict


def getMultiShaderObjAssignDict(shaderList, removeSuffix=True):
    """Returns a multi shader dict, keys are the shader names, contents are nested dicts with
    attribute, name and object/face assignment details

    :param shaderList: a list of Maya shader names
    :type shaderList: list
    :return multiShaderGenericDict: keys are the shader names, with  attribute, name and object/face assignment details
    :rtype multiShaderGenericDict: dict
    """
    multiShaderGenericDict = dict()
    for shader in shaderList:
        shaderObjAssignDict = getShaderObjectAssignDict(shader, removeSuffix=removeSuffix)
        if removeSuffix:
            shader = shaderutils.removeShaderSuffix(shader)
        multiShaderGenericDict[shader] = shaderObjAssignDict
    return multiShaderGenericDict


def getMultiShaderObjAssignDictSelected(removeSuffix=True):
    """Returns a multi shader dict, from selected objects/shaders
    keys are the shader names, contents are nested dicts with
    attribute, name and object/face assignment details

    :return multiShaderGenericDict: keys are the shader names, with  attribute, name and object/face assignment details
    :rtype multiShaderGenericDict: dict
    """
    shaderList = shaderutils.getShadersFromSelectedNodes(allDescendents=True)
    multiShaderGenericDict = getMultiShaderObjAssignDict(shaderList, removeSuffix=removeSuffix)
    return multiShaderGenericDict


def getMultiShaderObjAssignDictScene(removeSuffix=True, checkNonUnique=False):
    """Returns a multi shader dict, from scene, currently mesh objects only
    keys are the shader names, contents are nested dicts with
    attribute, name and object/face assignment details

    :return multiShaderGenericDict: keys are the shader names, with  attribute, name and object/face assignment details
    :rtype multiShaderGenericDict: dict
    """
    meshTransformLongNameList = objhandling.getAllMeshTransformsInScene(longName=True)
    if not meshTransformLongNameList:
        om2.MGlobal.displayWarning("No polygon objects found in the scene")
        return
    shaderList = shaderutils.getShadersFromNodes(meshTransformLongNameList)
    if not shaderList:
        om2.MGlobal.displayWarning("No supported shaders found in the scene that are assigned to polygon objects")
    multiShaderGenericDict = getMultiShaderObjAssignDict(shaderList, removeSuffix=removeSuffix)
    return multiShaderGenericDict


def createApplyShaderWithDict(shaderName, genericShaderDict, rendererNiceName, addSuffix=True, overwrite=True):
    """Creates shaders if they don't already exist
    If shader exists and overwrite is on delete the old shader, if overwite is off then add a suffix to the new shader
    so there are no conflicts

    :param shaderName: The name of the shader, usually without a suffix
    :type shaderName: str
    :param genericShaderDict: generic shader dictionary with attribute settings only
    :type genericShaderDict: dict
    :param rendererNiceName: the nice name of the renderer
    :type rendererNiceName: str
    :param addSuffix: add a suffix to the shader name or the renderer type
    :type addSuffix: bool
    :param overwrite: delete the shader if it exists or keep it and apply the attribute settings?
    :type overwrite: bool
    :return shaderName: the name of the shader
    :rtype shaderName: str
    """
    shaderType = autoTypeShader(rendererNiceName)
    if addSuffix:
        shaderName = "_".join([shaderName, RENDERER_SUFFIX[rendererNiceName]])
    if cmds.objExists(shaderName):
        if overwrite:
            cmds.delete(shaderName)
        else:  # rename existing shader with a suffix to avoid clashes *could be referenced is not checked
            newName = namewildcards.renameWithUniquePrefix(SHADERMATCHPREFIX, shaderName)
            shaderName = newName
        # shader name will build correctly now
        shaderName = createShaderType(shaderType, shaderName=shaderName, specWeight=0.0, message=False,
                                      rgbColor=(.5, .5, .5))
    else:  # no clashes so all cool
        shaderName = createShaderType(shaderType, shaderName=shaderName, specWeight=0.0, message=False,
                                      rgbColor=(.5, .5, .5))
    # assign attribute values to the shader
    setShaderAttrs(shaderName, shaderType, genericShaderDict, convertSrgbToLinear=True, reportMessage=False)
    return shaderName


def createShaderApplyToObjFace(shaderName, genericShaderDict, objFace, rendererNiceName, addSuffix=True,
                               overwrite=True):
    """Creates a shader and applies it to an object/face list
    will overwite existing shaders if overwite is on, if off will use existing shaders
    can add suffix of the renderer type

    :param shaderName: The name of the shader, usually without a suffix
    :type shaderName: str
    :param genericShaderDict: generic shader dictionary with attribute settings only
    :type genericShaderDict: dict
    :param objFace: a list of polygon objects and faces in Maya format that it uses to make selections
    :type objFace: list
    :param rendererNiceName:  renderer nice name "Arnold", "Renderman", "Redshift"
    :type rendererNiceName: str
    :param addSuffix: add a suffix to the shader name or the renderer type
    :type addSuffix: bool
    :param overwrite: delete the shader if it exists or keep it and apply the attribute settings?
    :type overwrite: bool
    """
    shaderName = createApplyShaderWithDict(shaderName, genericShaderDict, rendererNiceName, addSuffix=addSuffix,
                                           overwrite=overwrite)
    shaderutils.assignShader(objFace, shaderName)  # assign to objects and or faces


def createShaderApplyToObjFaceCheck(shaderName, genericShaderDict, objFace, rendererNiceName, addSuffix=True,
                                    overwrite=True):
    """Creates a shader and check if obj exists and if so applies it the object/face list
    will overwite existing shaders if overwite is on, if off will use existing shaders
    can add suffix of the renderer type

    :param shaderName: The name of the shader, usually without a suffix
    :type shaderName: str
    :param genericShaderDict: generic shader dictionary with attribute settings only
    :type genericShaderDict: dict
    :param objFace: a list of polygon objects and faces in Maya format that it uses to make selections
    :type objFace: list
    :param rendererNiceName:  renderer nice name "Arnold", "Renderman", "Redshift"
    :type rendererNiceName: str
    :param addSuffix: add a suffix to the shader name or the renderer type
    :type addSuffix: bool
    :param overwrite: delete the shader if it exists or keep it and apply the attribute settings?
    :type overwrite: bool
    """
    shaderName = createApplyShaderWithDict(shaderName, genericShaderDict, rendererNiceName, addSuffix=addSuffix,
                                           overwrite=overwrite)
    shaderutils.assignShaderCheck(objFace, shaderName)  # assign to objects and or faces with check
    return shaderName


def applyMultiShaderDictObjAssign(multiShaderGenericDict, rendererNiceName, addSuffix=True, overwrite=True):
    """Apples a multiShaderGenericDict, by creating the shader if it doesn't exist and assigning to the objects/faces
    will overwite existing shaders if overwite is on, if off will rename the incoming shaders to have a unique prefix
    can add suffix of the renderer type

    :param multiShaderGenericDict: keys are the shader names, with  attribute, name and object/face assignment details
    :type multiShaderGenericDict: dict
    :param rendererNiceName:  renderer nice name "Arnold", "Renderman", "Redshift"
    :type rendererNiceName: str
    :param addSuffix: add a suffix to the shader name or the renderer type
    :type addSuffix: bool
    :param overwrite: delete the shader if it exists or keep it and apply the attribute settings?
    :type overwrite: bool
    :return shaderList: list of shaders
    :rtype shaderList: list
    """
    shaderList = list()
    for shader in multiShaderGenericDict:  # loop through keys which are shader names
        if multiShaderGenericDict[shader][ATTRSHADERDICT]:  # check could be non supported shader
            shaderCreated = createShaderApplyToObjFaceCheck(shader,
                                                            multiShaderGenericDict[shader][ATTRSHADERDICT],
                                                            multiShaderGenericDict[shader][OBJECTSFACES],
                                                            rendererNiceName,
                                                            addSuffix=addSuffix,
                                                            overwrite=overwrite)
            shaderList.append(shaderCreated)
    return shaderList


def deleteShader(shaderName, checkValid=True, deleteShaderNetwork=True, message=False):
    """Deletes a compatible shader from the Maya scene

    :param shaderName: The name of a Maya supported shader
    :type shaderName: str
    :param shaderName: The name of a Maya supported shader
    :type shaderName: str
    :param shaderName: The name of a Maya supported shader
    :type shaderName: str
    :param deleteShaderNetwork: Delete all texture nodes etc connected to the shader
    :type deleteShaderNetwork: bool

    """
    # Check if a valid shader
    if not cmds.objExists(shaderName):
        om2.MGlobal.displayWarning("The shader `{}` does not exist in the current scene".format(shaderName))
        return
    if not testIfSupportedShader(shaderName) and checkValid:
        om2.MGlobal.displayWarning("The shader's type is not supported should be an "
                                   "Arnold, Renderman, or Redshift shader type")
        return
    if deleteShaderNetwork:
        shaderutils.deleteShaderNetwork(shaderName)
    else:
        cmds.delete(shaderName)
    om2.MGlobal.displayInfo("Shader deleted `{}`".format(shaderName))


def deleteShadersDict(rendererNiceName, shaderDict, deleteNetwork=True):
    """Deletes all shaders and shading groups from a shader dict, can also delete the entire network (default True)

    :param rendererNiceName: the name of the renderer to delete from  "Arnold"
    :type rendererNiceName: str
    :param shaderDict: The shader dictionary with shader names as keys
    :type shaderDict: dict
    :param deleteNetwork: Delete the entire shading network? Or just the shader and shading group?
    :type deleteNetwork: dict
    """
    for shader in shaderDict:
        # add the suffix
        suffix = RENDERER_SUFFIX[rendererNiceName]
        shaderName = "_".join([shader, suffix])
        if cmds.objExists(shaderName):
            if deleteNetwork:  # Delete the entire network
                shaderutils.deleteShaderNetwork(shaderName)
            else:  # Just delete the shader and shading group
                shadingGroup = shaderutils.getShadingGroupFromShader(shaderName)
                cmds.delete([shadingGroup, shaderName])


def createMatteAOVRenderer(rendererNiceName, matteColor, imageNumber):
    """Given a renderer nice name, create an AOV rgb matte
    supports "Arnold", "Renderman", "Redshift"

    :param renderer:  renderer nice name "Arnold", "Renderman", "Redshift"
    :type renderer: str
    :param matteColor: color of the matte, certain renderers only do pure r g b. In 0-1 values (0.0, 0.0, 1.0)
    :type matteColor: tuple
    :param imageNumber: the image number, each rgb only has 3 spots per image.  Image numbering usually starts at 0
    :type imageNumber: int
    :return rendererFound: was the renderer nice name in the list
    :rtype rendererFound: bool
    """
    if rendererNiceName == ARNOLD:
        arnoldaovs.createRGBMatteAOVSelected(matteColor, imageNumber)
        return True
    elif rendererNiceName == REDSHIFT:
        redshiftaovs.setMatteSelected(matteColor, imageNumber)
        return True
    elif rendererNiceName == RENDERMAN:
        rendermanaovs.connectPxrMatteIDSelected(imageNumber, matteColor)
        return True
    else:
        om2.MGlobal.displayError("Renderer Not Found")
        return False




