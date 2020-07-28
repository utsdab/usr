"""
TO DO
---------
Exporting lights should use long names?

"""

import glob, os, tempfile

import maya.cmds as cmds
import maya.api.OpenMaya as om2
from zoo.libs.maya.cmds.shaders.shadermultirenderer import OBJECTSFACES

from zoo.libs.utils import filesystem
from zoo.libs.maya.utils import files

from zoo.libs.maya.cmds.objutils import namehandling, objhandling, attributes, meshhandling

from zoo.libs.maya.cmds.shaders import shadermultirenderer, shaderutils
from zoo.libs.maya.cmds.lighting import renderertransferlights, presets
from zoo.libs.maya.cmds.renderer.exportglobals import GENERICVERSIONNO, VERSIONKEY, LIGHTS, MESHOBJECTS, AREALIGHTS, \
    IBLSKYDOMES, DIRECTIONALS, SHADERS, NAMESPACELIST, ZOOSCENESUFFIX, ZOOABC_MESH, ZOOABC_LIGHT, LIGHTGRPNAME, \
    ZOOABC_CAM, ZOOABC_LOC, ZOOABC_CURVE, ZOOABC_PREFIX, RENDERERAREALIGHTS, RENDERERDIRECTIONALLIGHTS, \
    RENDERERSKYDOMELIGHTS
from zoo.libs.zooscene import constants, zooscenefiles
from zoo.libs.zooscene.zooscenefiles import setSudbDDict, loadGenericShaderLightFiles, getExportedNamespaces


def tagTransformsZooABCAttr(nodeType, attrName):
    """Tags transform nodes of shape nodes of the given type
    Will tag by creating a float attribute named attrName
    message nodes cannot be exported by alembic

    :param nodeType: the maya node type eg "mesh", or "nurbsCurve"
    :type nodeType: str
    :param attrName: the name of the attribute to be created
    :type attrName: str
    """
    shapeNodes = cmds.ls(exactType=nodeType, long=True)  # find all meshes
    if not shapeNodes:
        return  # nothing found
    for node in shapeNodes:  # find their parent (the transform)
        transform = cmds.listRelatives(node, parent=True)[0]
        if not cmds.attributeQuery(attrName, node=transform, exists=True):  # tag create custom attr
            cmds.addAttr(transform, longName=attrName, attributeType='float')


def tagZooABCAttributes(meshes=False, lights=True, cameras=False, locators=False, curves=False):
    """Tags all nodes (transforms) in the scene with a message attribute with the prefix "zooABC"
    eg. zooABC_light
    The attribute tags can be exported with alembic
    These tags enable us to control what's in the scene on ABC import by deleting or managing unwanted types
    This is really only handy for lights which often need to be deleted but can't be found via querying the object type
    as they are usually empty transform nodes

    :param meshes: tag mesh transform node types with an attribute identifier
    :type meshes: bool
    :param lights: tag lights transform node types with an attribute identifier
    :type lights: bool
    :param cameras: tag camera transform node types with an attribute identifier
    :type cameras: bool
    :param locators: tag locators transform node types with an attribute identifier
    :type locators: bool
    :param curves: tag curves transform node types with an attribute identifier
    :type curves: bool
    """
    if meshes:
        tagTransformsZooABCAttr("mesh", ZOOABC_MESH)
    if lights:  # lights can be many node types, cycle through them from the export globals, current VP2 not supported
        for renderer in RENDERERAREALIGHTS:
            if not isinstance(RENDERERAREALIGHTS[renderer], tuple):
                tagTransformsZooABCAttr(RENDERERAREALIGHTS[renderer], ZOOABC_LIGHT)
            else:
                for nodeType in RENDERERAREALIGHTS[renderer]:  # will be renderman lights grr
                    tagTransformsZooABCAttr(nodeType, ZOOABC_LIGHT)
        for renderer in RENDERERDIRECTIONALLIGHTS:
            tagTransformsZooABCAttr(RENDERERDIRECTIONALLIGHTS[renderer], ZOOABC_LIGHT)
        for renderer in RENDERERSKYDOMELIGHTS:
            tagTransformsZooABCAttr(RENDERERSKYDOMELIGHTS[renderer], ZOOABC_LIGHT)
    if cameras:
        tagTransformsZooABCAttr("camera", ZOOABC_CAM)
    if locators:
        tagTransformsZooABCAttr("locator", ZOOABC_LOC)
    if curves:
        tagTransformsZooABCAttr("nurbsCurve", ZOOABC_CURVE)


def deleteZooABCAttrObjs(rendererNiceName="", meshes=False, lights=True, cameras=False, locators=False, curves=False,
                         message=False, lightGrps=True, checkNodes="", skipLightGrps=False):
    """Deletes objects with attribute tags by type, usually used for lights from ABC as they aren't imported as
    light types and so can't be tracked or deleted.

    :param rendererNiceName: the renderer name "Arnold" "Redshift" etc, needs to be specified for deleting light groups
    :type rendererNiceName: bool
    :param meshes: delete objects with mesh tags
    :type meshes: bool
    :param lights: delete objects with light tags
    :type lights: bool
    :param cameras: delete objects with camera tags
    :type cameras: bool
    :param locators: delete objects with locator tags
    :type locators: bool
    :param curves: delete objects with curves tags
    :type curves: bool
    :param message: report the message to message user
    :type message: bool
    :param checkNodes: only check these nodes, otherwise the whole scene
    :type checkNodes: list
    :param skipLightGrps: skips the deletion of the light grp of the current renderer
    :type skipLightGrps: bool
    :return deletedNodes: all the deleted nodes
    :rtype deletedNodes: list
    """
    if checkNodes:
        transformNodes = cmds.ls(checkNodes, type="transform")  # tags are on the transform nodes, filter checkNodes
    else:
        transformNodes = cmds.ls(type="transform")  # all tags are on the transform nodes, select all in scene
    deletedNodes = list()
    if meshes:
        deletedNodes += attributes.deleteNodesWithAttributeList(transformNodes, ZOOABC_MESH)
    if lights:
        deletedNodes += attributes.deleteNodesWithAttributeList(transformNodes, ZOOABC_LIGHT)
        if not skipLightGrps:
            if lightGrps and rendererNiceName:
                baseLightGrp = "|{}{}".format(rendererNiceName, LIGHTGRPNAME)
                if cmds.objExists(baseLightGrp):
                    cmds.delete(baseLightGrp)
                    deletedNodes.append(baseLightGrp)
    if cameras:
        deletedNodes += attributes.deleteNodesWithAttributeList(transformNodes, ZOOABC_CAM)
    if locators:
        deletedNodes += attributes.deleteNodesWithAttributeList(transformNodes, ZOOABC_LOC)
    if curves:
        deletedNodes += attributes.deleteNodesWithAttributeList(transformNodes, ZOOABC_CURVE)
    if message:
        om2.MGlobal.displayInfo("Nodes Deleted: {}".format(deletedNodes))


def getShaderLightDict(rendererNiceName, getShader=True, getLight=True, exportSelected=False, includeSelChildren=False):
    """get the information from the scene to build the shader/light dictionaries given the options passed in

    :param rendererNiceName: name of the renderer nicename "Arnold"
    :type rendererNiceName: str
    :param getShader: get shader information
    :type getShader: bool
    :param getLight: get the lighting information
    :type getLight: bool
    :param exportSelected:  export only the selected objects (and their children/grandchildren)
    :type exportSelected: bool
    :return zooSceneDict: the lightShader dictionary with version number
    :rtype zooSceneDict: dict
    """
    lightMultDict = dict()
    shadMultDict = dict()
    if getShader:  # export the shaders as generic .zooScene format for the zooSceneDict
        if exportSelected:
            shadMultDict = shadermultirenderer.getMultiShaderObjAssignDictSelected(removeSuffix=True)
        else:
            shadMultDict = shadermultirenderer.getMultiShaderObjAssignDictScene(removeSuffix=True)
    if getLight:
        lightMultDict = renderertransferlights.getAllLightsGenericDict(rendererNiceName, getSelected=exportSelected,
                                                                       includeSelChildren=includeSelChildren)
    return shadMultDict, lightMultDict


def removeNamespaceZooScene(zooSceneDict, shaderMultiDict, lightMultiDict):
    """Depreciated function, might not be needed anymore since Alembic supports namespaces
    removes all namespaces from the zooSceneDict, might be handy for strip namespaces to match that flag for alembic

    Could be done better as a flag while collecting the dict info, maybe will do later
    Ugly dict and string handling :/

    Deletes namespaces in the
        zooSceneDict[MESHOBJECTS] = the keys  (long names)
        zooSceneDict[LIGHTS][AREALIGHTS] = the area light keys (short names)
        zooSceneDict[LIGHTS][IBLSKYDOMES] = the ibl keys (short names)
        zooSceneDict[SHADERDICT][OBJECTFACES] = then go through each list  (short names)

    :param zooSceneDict: the lighting/shader/subd dict the .zooscene
    :type zooSceneDict: dict
    :return zooSceneDict: the lighting/shader/subd dict the .zooscene, now with namespaces removed
    :rtype zooSceneDict: dict
    """
    if MESHOBJECTS in zooSceneDict:  # remove on subD settings
        for mesh in zooSceneDict[MESHOBJECTS]:  # objects are stored as longnames
            newKeyMesh = namehandling.removeNamespaceLongnames(mesh)  # long name
            if newKeyMesh != mesh:  # if namespace has been removed update the key
                zooSceneDict[MESHOBJECTS][newKeyMesh] = zooSceneDict[MESHOBJECTS][mesh]
                del zooSceneDict[MESHOBJECTS][mesh]
    if LIGHTS in zooSceneDict:  # remove on light settings
        if AREALIGHTS in lightMultiDict:
            for areaLight in lightMultiDict[AREALIGHTS]:
                newKeyAreaLight = namehandling.removeNamespaceShortName(areaLight)  # short name
                if newKeyAreaLight != areaLight:  # if namespace has been removed update the key
                    lightMultiDict[AREALIGHTS][newKeyAreaLight] = lightMultiDict[AREALIGHTS][areaLight]
                    del lightMultiDict[AREALIGHTS][areaLight]
        if IBLSKYDOMES in lightMultiDict:
            for areaLight in lightMultiDict[IBLSKYDOMES]:
                newKeyAreaLight = namehandling.removeNamespaceShortName(areaLight)  # short name
                if newKeyAreaLight != areaLight:  # if namespace has been removed update the key
                    lightMultiDict[IBLSKYDOMES][newKeyAreaLight] = zooSceneDict[LIGHTS][IBLSKYDOMES][areaLight]
                    del lightMultiDict[IBLSKYDOMES][areaLight]
    # remove on shader assignment
    if not shaderMultiDict:  # no shader data so return
        return zooSceneDict
    for shaderDictKey in shaderMultiDict:  # shaderDictKey[OBJECTSFACES] shortname list object/face assigns
        # check OBJECTFACES in dict, will be in all shaderDictKey or none, if none return
        if OBJECTSFACES not in shaderMultiDict[shaderDictKey]:
            return zooSceneDict
        newNamesList = namehandling.removeNamespaceShortNameList(shaderMultiDict[shaderDictKey][OBJECTSFACES],
                                                                 checkFaceAssign=True)
        shaderMultiDict[shaderDictKey][OBJECTSFACES] = newNamesList
    return zooSceneDict, shaderMultiDict, lightMultiDict


def createShaderLightDict(rendererNiceName, shadMultDict, lightMultDict, setShaders=True, setLights=True,
                          addSuffix=True,
                          replaceShaders=True, replaceLights=True, includeLights=True):
    """Given the renderer and zooSceneDict, build the lights and shaders in the scene,

    :param rendererNiceName: name of the renderer nicename "Arnold"
    :type rendererNiceName: str
    :param zooSceneDict: the lightShader dictionary with light and shader info
    :type zooSceneDict: dict
    :param setShaders: apply/import the shaders?
    :type setShaders: bool
    :param setLights: import the lights?
    :type setLights: bool
    :param addSuffix: add suffixes to the shaders and lights?
    :type addSuffix: bool
    :param replaceShaders: replace the existing shaders? if off will add shaders but with new names 001 002 etc
    :type replaceShaders: bool
    :param includeLights: if False then skip the importing of lights, override
    :type includeLights: bool
    :return allNodes: all shader and light nodes created
    :rtype allNodes: list
    """
    allLightTransforms = list()
    allLightShapes = list()
    shaderList = list()
    shadingGroupList = list()
    if setShaders:  # if True import shaders in generic format
        shaderDict = shadMultDict
        if shaderDict:
            shaderList = shadermultirenderer.applyMultiShaderDictObjAssign(shaderDict, rendererNiceName,
                                                                           addSuffix=addSuffix,
                                                                           overwrite=replaceShaders)
            if shaderList:  # get shaderGroups to return
                shadingGroupList = shaderutils.getShadingGroupFromShaderList(shaderList)
    if setLights and lightMultDict and includeLights:  # if True import lights in generic format
        if lightMultDict[AREALIGHTS] or lightMultDict[IBLSKYDOMES] or lightMultDict[DIRECTIONALS]:
            allLightTransforms, \
            allLightShapes = renderertransferlights.importLightsGenericDict(lightMultDict,
                                                                            rendererNiceName,
                                                                            message=False,
                                                                            replaceLights=replaceLights)
    return allLightTransforms, allLightShapes, shaderList, shadingGroupList


def getTexturedAttributes(shaderList, renderer):
    """Builds the nested dictionary from shader connections so it can be rebuilt later with transferRenderer():

        {"shaderName": {"gDiffuseColor_srgb": "fileTexture01.outColor",
                          "gSpecRoughness": "fileTexture02.outAlpha"}}

    If no textures the dicts will be empty.

        {"shaderName": {}}

    See reconnectTextures() for rebuilding the connections after Renderer convert

    :param shaderList: A list of shader names to find source connections
    :type shaderList: list(str)
    :param renderer: The renderer of the shader names
    :type renderer: str
    :return texturedShaderDict: A nested dictionary, shader keys and then generic key (attrs), values are node.attr
    :rtype texturedShaderDict:  dict(dict(str))
    """
    texturedShaderDict = dict()
    for shader in shaderList:
        textureDict = shadermultirenderer.getTexturedInfo(shader, renderer)
        texturedShaderDict[shader] = textureDict
    return texturedShaderDict


def reconnectTextures(texturedShaderDict, fromRenderer, toRenderer, addSuffix):
    """Reconnects textures while converting transferRenderer().  Uses a nested dict texturedShaderDict:

        {"oldShaderName": {"gDiffuseColor_srgb": "fileTexture01.outColor",
                          "gSpecRoughness": "fileTexture02.outAlpha"}}

    :param texturedShaderDict: A nested dictionary, shader keys and then generic key (attrs), values are node.attr
    :type texturedShaderDict: dict(dict(str))
    :param fromRenderer: The renderer converting from
    :type fromRenderer: str
    :param toRenderer: The renderer converting to
    :type toRenderer: str
    :param addSuffix: Adding suffix's to the new renderer? Recommended to be true
    :type addSuffix: bool
    """
    if not texturedShaderDict:  # empty
        return
    for oldShader in texturedShaderDict:  # shader names are the keys
        if not texturedShaderDict[oldShader]:  # empty
            continue
        # Get the new shader name TODO Possible issues while there's no addSuffix, name clashes
        newShader = shaderutils.removeShaderSuffix(oldShader)
        newShader = shadermultirenderer.buildNameWithSuffix(newShader, addSuffix, renderer=toRenderer)
        if cmds.objExists(newShader):
            # Loop over the generic keys
            for genKey in texturedShaderDict[oldShader]:
                # Figure the new attribute to connect to
                attrDict = shadermultirenderer.getShaderAttributesDict(shadermultirenderer.autoTypeShader(toRenderer))
                destinationAttr = attrDict[genKey]
                # connect attributes, texturedShaderDict[oldShader][genKey] is shader.attribute
                cmds.connectAttr(texturedShaderDict[oldShader][genKey], '.'.join([newShader, destinationAttr]))


def transferRenderer(fromRenderer, toRenderer, transferShader=True, transferLights=True, transferSelected=False,
                     addSuffix=True, replaceShaders=True, deleteOld=False):
    """Transfers a scene (transferSelected=False) or selection to a new renderer using the generic shader dicts
    Many options
    Currently will always delete lights while rebuilding

    Texture Note:
        Textures that are connected to supported generic attributes ie. shadermultirenderer.GEN_KEY_LIST will be \
        reconnected. However they will not be converted, so it'll only work with native Maya nodes such as ramps \
        and native file textures and or math nodes etc that are supported by the both renderers.

    TODO: Add support attributes such as metalness, normals, bump, displacement etc.

    :param fromRenderer: The renderer converting from "Arnold"
    :type fromRenderer: str
    :param toRenderer: The renderer converting to "Redshift"
    :type toRenderer: str
    :param transferShader: transfer the shaders?
    :type transferShader: bool
    :param transferLights: transfer the lights?
    :type transferLights: bool
    :param transferSelected: transfer only selected objects? If false will export scene, shaders are assigned to objs
    :type transferSelected: bool
    :param addSuffix: add a suffix to the shader names while creating
    :type addSuffix: bool
    :param replaceShaders: replace shaders with the same names
    :type replaceShaders: bool
    :param deleteOld: delete the old lights and shaders (if they are being transferred) Shaders use suffix's
    :type deleteOld: bool
    :return wasConverted: if converted True if not False
    :rtype wasConverted: bool
    """
    # Get the info fromRenderer
    shadMultDict, lightMultDict = getShaderLightDict(fromRenderer, getShader=transferShader, getLight=transferLights,
                                                     exportSelected=transferSelected)
    if not shadMultDict and not lightMultDict:
        om2.MGlobal.displayWarning("No supported shaders or lights found for the renderer `{}`".format(fromRenderer))
        return
    # Monitor shader connections (textures) and track
    if shadMultDict:
        originalShaderList = shadermultirenderer.getShadersSceneRenderer(fromRenderer)
        texturedShaderDict = getTexturedAttributes(originalShaderList, fromRenderer)
    # Assign
    allLightTransforms, allLightShapes, shaderList, shadingGroupList = createShaderLightDict(toRenderer,
                                                                                             shadMultDict,
                                                                                             lightMultDict,
                                                                                             setShaders=transferShader,
                                                                                             setLights=transferLights,
                                                                                             addSuffix=addSuffix,
                                                                                             replaceShaders=True)
    if shadMultDict:  # Reconnect textures
        reconnectTextures(texturedShaderDict, fromRenderer, toRenderer, addSuffix)
    if deleteOld:  # delete from renderer lights and shaders, will delete all lights in scene for now
        if transferLights:  # deletes all lights even if selected is on
            renderertransferlights.deleteAllLightsInScene(fromRenderer)
        if transferShader and shadMultDict:  # deletes shaders with a fromRenderer suffix, can fail
            shadermultirenderer.deleteShadersDict(fromRenderer, shadMultDict, deleteNetwork=False)
    om2.MGlobal.displayInfo("Success: Transferred from `{}` to `{}`".format(fromRenderer, toRenderer))
    return True


def exportAbcWithDictInfo(filePathAlembic, zooSceneDict=None, exportSelected=False, noMayaDefaultCams=True,
                          exportGeo=False, exportCams=False, exportAll=True, dataFormat="ogawa", frameRange="",
                          visibility=True, creases=True, uvSets=True, exportSubD=True):
    """Exports the .abc data with a generic zooSceneDict .zooScene file
     has a number of filter options, including exporting hierarchies containing geo or cams.
     Can exclude Maya default cams, persp front bottom back
     Can export SubD attribute info to the .zooScene file
     Other regular .abc export flags too.

    :param filePathAlembic: the full filepath to the .abc file to save
    :type filePathAlembic: str
    :param zooSceneDict: the exported dict usually for .zooScene writing, if None it will be created
    :type zooSceneDict: dict
    :param exportSelected: export selected, will override other filters like noMayaDefaultCams
    :type exportSelected: bool
    :param noMayaDefaultCams: omit the Maya default cams, 'front' 'left' 'bottom' 'back' 'persp' etc
    :type noMayaDefaultCams: bool
    :param exportGeo: export the geometry?  Note, child nodes of all objects root parent will still be included
    :type exportGeo: bool
    :param exportCams: export the cameras?  Note, child nodes of all cameras root parent will still be included
    :type exportCams: bool
    :param exportAll: will export everything, maya default cams are still potentially filtered
    :type exportAll: bool
    :param visibility: will export visibility state of every object
    :type visibility: bool
    :param creases: will export creases on objects, currently broken
    :type creases: bool
    :param uvSets: will export poly objects with uv sets
    :type uvSets: bool
    :param dataFormat: abc format type, "ogawa" is small and fast, "hdf" supports backwards compatibility
    :type dataFormat: str
    :param frameRange: frame to and from as a string eg "0 10".  If left empty will default to current frame.
    :type frameRange: str
    :param exportSubD: export the subD settings into the .zooScene file
    :type exportSubD: bool
    :return zooSceneDict: the exported dict usually for .zooScene writing extra data uch as subD and objExist info
    :rtype zooSceneDict: dict
    """
    if not zooSceneDict:
        zooSceneDict = dict()
    if exportSelected:  # exports only selected hierarchies
        filePathAlembic, objectRootList = files.exportAbcSelected(filePathAlembic,
                                                                  frameRange=frameRange,
                                                                  visibility=visibility,
                                                                  creases=creases,
                                                                  uvSets=uvSets,
                                                                  dataFormat=dataFormat,
                                                                  userAttrPrefix=ZOOABC_PREFIX)
    else:  # export whole scene
        filePathAlembic, objectRootList = files.exportAbcSceneFilters(filePathAlembic,
                                                                      frameRange=frameRange,
                                                                      visibility=visibility,
                                                                      creases=creases,
                                                                      uvSets=uvSets,
                                                                      dataFormat=dataFormat,
                                                                      noMayaDefaultCams=noMayaDefaultCams,
                                                                      exportGeo=exportGeo,
                                                                      exportCams=exportCams,
                                                                      exportAll=exportAll,
                                                                      userAttrPrefix=ZOOABC_PREFIX)
    # export .zooScene dict for mesh name and subD info
    if objectRootList:
        meshTransformList = objhandling.getTypeTransformsHierarchy(objectRootList, type="mesh")
    if exportSubD and objectRootList:
        meshTransformList = objhandling.getTypeTransformsHierarchy(objectRootList, type="mesh")
        if meshTransformList:  # then save the subD settings
            # nested dict, attrs will be zooSceneDict[MESHOBJECTS]["sphere1"]["attr"]
            zooSceneDict[MESHOBJECTS] = meshhandling.getMeshSubDSettingsList(meshTransformList,
                                                                             longName=True)
        else:
            zooSceneDict[MESHOBJECTS] = dict()  # no mesh objects to export
    elif objectRootList:
        if meshTransformList:
            for mesh in meshTransformList:
                zooSceneDict[MESHOBJECTS][mesh] = list()  # write mesh objects as keys with empty lists
        else:
            zooSceneDict[MESHOBJECTS] = dict()
    else:
        zooSceneDict[MESHOBJECTS] = dict()  # no mesh objects to export
    return zooSceneDict, objectRootList


def exportAbcGenericShaderLights(zooSceneFullPath, rendererNiceName="Arnold", exportSelected=False, exportShaders=True,
                                 exportLights=True, exportAbc=True, noMayaDefaultCams=True, exportGeo=False,
                                 exportCams=False, exportAll=True, dataFormat="ogawa", frameRange="", visibility=True,
                                 creases=True, uvSets=True, exportSubD=True, exportNamespaces=True,
                                 tagInfoDict=dict(), includeSelChildren=False, keepThumbnailOverride=False):
    """Saves files

        1. .zooScene file with misc info
        2. The shader file with generic shader info
        3. The lights file with generic light info
        4. An alembic file with the same name in the same location
        5. The zooInfo file with information meta data about the file

    While saving lights or shaders only it's worth saving this same filetype, and the remaining category will be an
    empty dict.

    The related importer will only import the dictionaries it finds with legit data.
    Please note that the 'exportGeo' and 'exportCams' will save the root node of each of those object types,
    the alembic will export all viable nodes parented into that hierarchy.

    :param zooSceneFullPath: the full filepath to the json file to save
    :type zooSceneFullPath: str
    :param rendererNiceName: which rendererNice name should the lights be saved from?  Saving shaders only = not needed
    :type rendererNiceName: str
    :param exportSelected: export selected, will override other filters like noMayaDefaultCams
    :type exportSelected: bool
    :param exportShaders: export all meshes (poly only) in the scene and all related shaders
    :type exportShaders: bool
    :param exportLights: will export supported light types, the lights in generic (not alembic) format as .zooScene
    :type exportLights: bool
    :param exportAbc: will export an alembic files with the same name as the .zooScene
    :type exportAbc: bool
    :param noMayaDefaultCams: omit the Maya default cams, 'front' 'left' 'bottom' 'back' 'persp' etc
    :type noMayaDefaultCams: bool
    :param exportGeo: export the geometry?  Note, child nodes of all objects root parent will still be included
    :type exportGeo: bool
    :param exportCams: export the cameras?  Note, child nodes of all cameras root parent will still be included
    :type exportCams: bool
    :param exportAll: will export everything, maya default cams are still potentially filtered
    :type exportAll: bool
    :param visibility: will export visibility state of every object
    :type visibility: bool
    :param creases: will export creases on objects, currently broken
    :type creases: bool
    :param uvSets: will export poly objects with uv sets
    :type uvSets: bool
    :param dataFormat: abc format type,  "ogawa" is small and fast, "hdf" supports backwards compatibility
    :type dataFormat: str
    :param frameRange: frame to and from as a string eg "0 10".  If left empty will default to current frame.
    :type frameRange: str
    :param exportSubD: export the subD settings into the .zooScene file
    :type exportSubD: bool
    :param exportNamespaces: exports namespaces to the .zooscene folder, bug in .abc means it must created before import
    :type exportNamespaces: bool
    :param exportNamespaces: exports namespaces to the .zooscene folder, bug in .abc means it must created before import
    :type exportNamespaces: bool
    :param keepThumbnailOverride: keeps the existing thumbnail image if over righting, usually for delete when renaming
    :type keepThumbnailOverride: bool
    :return tagInfoDict: tag info dictionary that is saved as a .zooInfo, if empty and will be created as empty
    :rtype tagInfoDict: dict
    :return includeSelChildren: include whole hierarchy of selected, will override to auto on if alembic and exportsel
    :rtype includeSelChildren: dict
    :return zooSceneFullPath: file path of the alembic file saved
    :rtype filePathAlembic: str
    """
    animationInfo = frameRange
    objectRootList = list()
    filePathAlembic = None
    gShaderExists = False
    gLightExists = False
    # create the directory for the info file
    dependencyDir, fileNameNoExt = zooscenefiles.getDependencyFolder(zooSceneFullPath)
    # checks if existing dependency folder with files in them, if so delete them
    if os.listdir(dependencyDir) != []:  # if contains files
        deletedFiles = zooscenefiles.deleteZooDependencies(zooSceneFullPath, message=True,
                                                           keepThumbnailOverride=keepThumbnailOverride)
        if not deletedFiles:  # a file is locked and in use
            return
    if not frameRange:  # if no frame range set to current time
        animationInfo = None
        curTime = cmds.currentTime(query=True)
        frameRange = "{0} {0}".format(curTime)
    # always include children if exporting alembic
    if exportAbc and exportSelected:
        includeSelChildren = True
    # get version, light and shader info,
    gShaderDict, gLightDict = getShaderLightDict(rendererNiceName, getShader=exportShaders, getLight=exportLights,
                                                 exportSelected=exportSelected, includeSelChildren=includeSelChildren)
    if gShaderDict:  # there are incoming generic shaders
        gShaderExists = True
    if gLightDict:
        if gLightDict[IBLSKYDOMES] or gLightDict[AREALIGHTS] or gLightDict[DIRECTIONALS]:  # then incoming gLights
            gLightExists = True
        else:  # no lights found
            gLightDict = dict()
    zooSceneDict = {VERSIONKEY: GENERICVERSIONNO,
                    SHADERS: gShaderExists,
                    LIGHTS: gLightExists}
    if exportAbc:  # export alembic files
        tagZooABCAttributes(meshes=False, lights=True, cameras=False, locators=False, curves=False)  # attr tag lights
        alembicFileNameOnly = ".".join([fileNameNoExt, "abc"])
        filePathAlembic = os.path.join(dependencyDir, alembicFileNameOnly)
        zooSceneDict, objectRootList = exportAbcWithDictInfo(filePathAlembic,
                                                             zooSceneDict,
                                                             exportSelected=exportSelected,
                                                             noMayaDefaultCams=noMayaDefaultCams,
                                                             exportGeo=exportGeo,
                                                             exportCams=exportCams,
                                                             exportAll=exportAll,
                                                             dataFormat=dataFormat,
                                                             frameRange=frameRange,
                                                             visibility=visibility,
                                                             creases=creases,
                                                             uvSets=uvSets,
                                                             exportSubD=exportSubD)
    # If export selected and .abc then need to fix all the long name paths of the shader assignment for objectRootList
    # this is because the exported objects remove the hierarchies below the exported roots, so all long name objects
    # need to be potentially adjusted
    if exportNamespaces:
        namespaceList = getExportedNamespaces(objectRootList, gShaderDict)
        zooSceneDict[NAMESPACELIST] = namespaceList
    else:
        zooSceneDict[NAMESPACELIST] = list()
    if exportSelected and exportAbc and exportSubD:  # adjust the names of the dict to match the alembic export, roots
        zooSceneDict, gShaderDict = zooscenefiles.selectedZooSceneObjDictFix(zooSceneDict, gShaderDict, objectRootList)
    # write the .zooInfo
    zooInfoPath, fileInfoSaved = zooscenefiles.writeExportZooInfo(zooSceneFullPath, zooSceneDict, gShaderDict,
                                                                  gLightDict,
                                                                  objectRootList, tagInfoDict, animationInfo)
    if gShaderDict:  # save the generic shader info
        gShaderFullPath = zooscenefiles.writeZooGShaders(gShaderDict, zooSceneFullPath)
    if gLightDict:  # save the generic light info
        gLightsFullPath = zooscenefiles.writeZooGLights(gLightDict, zooSceneFullPath)
    # do the .zooscene save
    zooSceneDict[constants.INFOSAVE] = fileInfoSaved
    filesystem.saveJson(zooSceneDict, zooSceneFullPath, indent=4, separators=(",", ":"))
    om2.MGlobal.displayInfo("Success: Save Info {}, From `{}`"
                            "Written To: , `{}`".format(fileInfoSaved, rendererNiceName, zooSceneFullPath))
    return zooSceneFullPath, filePathAlembic


def importAbcDict(filePathAlembic, zooSceneDict, shadMultDict, lightMultDict, rendererNiceName, replaceRoots=False,
                  importSubDInfo=True, returnNodes=True, createNamespaces=True, deleteAbcLightNulls=True,
                  importLights=True, replaceLights=True):
    """Imports an alembic file and uses zooSceneDict to potentially replace existing roots

    :param filePathAlembic: the full filepath to the .abc file to save
    :type filePathAlembic: str
    :param zooSceneDict: the nested exported dict which contains subD information
    :type zooSceneDict: dict
    :param replaceRoots: Will delete an existing hierarchy root to make way for the imported hierarchy
    :type replaceRoots: bool
    :param createNamespaces: needs to create empty namespaces in the scene for namespaces to be imported correctly
    :type createNamespaces: bool
    :param deleteAbcLightNulls: deletes nulls that were once lights, and so avoids clashes with maya/generic lights
    :type deleteAbcLightNulls: bool
    :param importLights: this is for the generic light importer, if off don't delete the existing scene lights
    :type importLights: bool
    :param replaceLights: if True then we need to delete the renderer lights grp here for returning all abc nodes
    :type replaceLights: bool
    :return filePathAlembic: the full filepath to the .abc file to save
    :rtype filePathAlembic: str
    """
    allNodesBefore = list()
    if createNamespaces:
        if NAMESPACELIST in zooSceneDict:
            if zooSceneDict[NAMESPACELIST]:
                for namespace in zooSceneDict[NAMESPACELIST]:
                    if not cmds.namespace(exists=namespace):
                        cmds.namespace(add=namespace)
    if replaceRoots:  # delete any mesh roots if they already exist
        # could be a problem if there are no meshes but other types, not sure
        if MESHOBJECTS in zooSceneDict:  # if the key exists if not there are no meshes recorded
            meshList = list(zooSceneDict[MESHOBJECTS].keys())
            worldRootObjs = objhandling.getTheWorldParentOfObjList(meshList)
            for rootObj in worldRootObjs:
                if cmds.objExists(rootObj):
                    cmds.delete(rootObj)
    if returnNodes:
        allNodesBefore = cmds.ls(dependencyNodes=True, long=True)
    if os.path.isfile(filePathAlembic):  # import the alembic file
        files.importAlembic(filePathAlembic)
        if deleteAbcLightNulls and lightMultDict:
            for lightKey in lightMultDict:  # only delete lights if they are incoming, area type and ibl
                if lightMultDict[lightKey]:  # this is the light type incoming
                    # must delete lights here,  otherwise the returned abc nodes is wrong when lights deleted later
                    if replaceLights and importLights:
                        grp = "|{}{}*".format(rendererNiceName, LIGHTGRPNAME)  # delete renderer light group if at root
                        if cmds.objExists(grp):
                            cmds.delete(grp)
                    allNodesAndNew = cmds.ls(dependencyNodes=True, long=True)
                    checkNodes = [x for x in allNodesAndNew if x not in allNodesBefore]  # only check new
                    deleteZooABCAttrObjs(rendererNiceName=rendererNiceName, meshes=False, lights=True, cameras=False,
                                         locators=False, curves=False, message=True, checkNodes=checkNodes,
                                         skipLightGrps=True)
                    break
    if importSubDInfo:  # if True then apply subD settings to the imported objects
        setSudbDDict(zooSceneDict)
    if returnNodes:
        allNodesAndNew = cmds.ls(dependencyNodes=True, long=True)
        newNodes = [x for x in allNodesAndNew if x not in allNodesBefore]  # take allNodesBefore from allNodesAndNew
        return newNodes


def importAbcGenericShaderLights(zooSceneFullPath, rendererNiceName="Arnold", importShaders=True, importLights=True,
                                 importAbc=True, replaceShaders=True, addShaderSuffix=True, importSubDInfo=True,
                                 replaceRoots=False, returnNodes=True, replaceLights=True):
    """Imports the generic .zooScene file (shaders, shader assignment and lighting)
    with alembic data supported and various flags for importing.

    :param zooSceneFullPath: the full path of the .zooScene file to be saved
    :type zooSceneFullPath: str
    :param rendererNiceName: The renderer nice name used to import generic shaders eg. "Redshift" "Arnold"
    :type rendererNiceName: str
    :param importShaders: will import shaders in generic format
    :type importShaders: bool
    :param importLights: will import lights in generic format
    :type importLights: bool
    :param importAbc: imports the accompanying .abc alembic file
    :type importAbc: bool
    :param replaceShaders: will delete existing shaders before importing those of the same name
    :type replaceShaders: bool
    :param addShaderSuffix: Adds renderer suffixes to shader imports eg _RS, _ARN, _PXR
    :type addShaderSuffix:  bool
    :param importSubDInfo: Imports the subD info, includes maya subd info data like renderer level etc.
    :type importSubDInfo:  bool
    :param replaceRoots: Will delete an existing hierarchy root to make way for the imported hierarchy
    :type replaceRoots: bool
    :param newNodes: returns the new nodes created if returnNodes=True, otherwise returns None
    :type newNodes: bool
    :param replaceLights: if lights are imported will delete lights with the incoming/clashing names
    :type replaceLights: bool
    :return newNodes: returns the new nodes created if returnNodes=True, otherwise returns None
    :rtype newNodes: list
    """
    zooSceneDict = filesystem.loadJson(zooSceneFullPath)
    shadMultDict, lightMultDict = loadGenericShaderLightFiles(zooSceneFullPath)  # get the dicts
    if importAbc:  # if True import alembic file, replace meshes is an option
        filePathAlembic = zooscenefiles.getSingleFileFromZooScene(zooSceneFullPath, "abc")
        abcNodes = importAbcDict(filePathAlembic, zooSceneDict, shadMultDict, lightMultDict, rendererNiceName,
                                 replaceRoots=replaceRoots, importSubDInfo=importSubDInfo, returnNodes=returnNodes,
                                 importLights=importLights, replaceLights=replaceLights)
    # create and assign shaders and lights
    allLightTransforms, allLightShapes, shaderList, shadingGroupList = createShaderLightDict(rendererNiceName,
                                                                                             shadMultDict,
                                                                                             lightMultDict,
                                                                                             setShaders=importShaders,
                                                                                             setLights=importLights,
                                                                                             addSuffix=addShaderSuffix,
                                                                                             replaceShaders=replaceShaders,
                                                                                             replaceLights=replaceLights,
                                                                                             includeLights=importLights)
    shaderLightNodes = allLightTransforms + allLightShapes + shaderList + shadingGroupList
    om2.MGlobal.displayInfo("Success File Imported: `{}` and related files.".format(zooSceneFullPath))
    if returnNodes:
        if importAbc:
            allNodes = shaderLightNodes + abcNodes
        else:
            allNodes = shaderLightNodes
        return allNodes


def saveLightsZooScene(zooSceneFullPath, renderer, exportAll=True):
    """Simple function that exports lights with hardcoded export options

    :param zooSceneFullPath: fullpath to the .zooscene
    :type zooSceneFullPath: str
    :param renderer: the renderNiceName  "Arnold"
    :type renderer: str
    :param exportAll: export all (True) or selected (False)
    :type exportAll: bool
    :return zooSceneFullPath: the path to the zooScene saved
    :rtype zooSceneFullPath: str
    """
    zooSceneFullPath, filePathAlembic = exportAbcGenericShaderLights(zooSceneFullPath,
                                                                     rendererNiceName=renderer,
                                                                     exportSelected=False,
                                                                     exportShaders=False,
                                                                     exportLights=True,
                                                                     exportAbc=False,
                                                                     noMayaDefaultCams=False,
                                                                     exportGeo=False,
                                                                     exportCams=False,
                                                                     exportAll=True,
                                                                     dataFormat="ogawa",
                                                                     frameRange="",
                                                                     visibility=True,
                                                                     creases=True,
                                                                     uvSets=True,
                                                                     exportSubD=False)
    return zooSceneFullPath


def importLightPreset(zooSceneFullPath, rendererNiceName, overideDeleteLights):
    """Imports the lights only from a .zooScene and the dependency file .zooGShad

    :param zooSceneFullPath: the full path to the .zooScene file
    :type zooSceneFullPath: str
    :param rendererNiceName: nice name of the renderer "Arnold"
    :type rendererNiceName: str
    :param overideDeleteLights: delete current lights while importing, deletes the current renderer lights
    :type overideDeleteLights: bool
    :return allLightShapes: all light shapes and I think transforms created
    :rtypeallLightShapes: list
    """
    lightMultDict = loadGenericShaderLightFiles(zooSceneFullPath)[1]  # get the dicts
    allLightShapes = renderertransferlights.importLightsGenericDict(lightMultDict, rendererNiceName,
                                                                    replaceLights=overideDeleteLights)
    return allLightShapes


def updateIBLPaths(zooSceneDir, oldIblPath="D:/3dtrainingResources/HDRImages/_neatHDRIcollection",
                   newIblPath=""):
    """temp functexportglobalsion to fix bad ibl paths for .zooScene directories.  Useful for upgrading or batch fixing

    Note: is likely depreciated, nothing is using this function

    :param zooSceneDir: the directory to rename made up of .zooScene files and their dependencies
    :type zooSceneDir: str
    :param oldIblPath: the old ibl path to replace
    :type oldIblPath: str
    :param newIblPath: the new iblPath, if "" then will use the default location of the IBL dir from lighting.presets
    :type newIblPath: str
    :return lightFilesRenamedList:  a list of fileNames full path that have been renamed
    :rtype lightFilesRenamedList: list
    """
    lightFilesRenamedList = list()
    zooSceneList = list()
    if not newIblPath:
        newIblPath = presets.listIblQuickDirImages()[1]
    # get list of .zoo scenes
    os.chdir(zooSceneDir)
    for fileName in glob.glob("*.{}".format(ZOOSCENESUFFIX)):
        zooSceneList.append(fileName)
    # return os.chdir to the temp dir as it gets in the way with file permissions for later renames!
    os.chdir(tempfile.gettempdir())
    for zooScene in zooSceneList:
        # get path of gLight file and check if it exists
        zooSceneFullPath = os.path.join(zooSceneDir, zooScene)
        fullDirPath, fileNameNoExt = zooscenefiles.getDependencyFolder(zooSceneFullPath)
        zooLightsFileName = ".".join([fileNameNoExt, constants.ZOO_LIGHT_EXT])
        lightFile = os.path.join(fullDirPath, zooLightsFileName)
        if not os.path.exists(lightFile):  # there is no file so skip
            continue
        lightText = filesystem.loadFileTxt(lightFile)  # load text
        lightText = lightText.replace(oldIblPath, newIblPath)  # do the rename
        filesystem.saveFileTxt(lightText, lightFile)  # save text file
        lightFilesRenamedList.append(lightFile)
    om2.MGlobal.displayInfo("Files Renamed: {}".format(lightFilesRenamedList))
    return lightFilesRenamedList


def setShaderAttrsZooScene(zooScenePath, shaderName, shaderType, renameToZooName=False, message=True):
    """Sets a shader's attributes from a .zooScene file

    Will find the first shader in the file, and then it's attributes

    Can rename the shader to the .zooScene name, useful for creating from a preset or thumb browser

    :param shaderName: The maya name of the shader, could be any user defined name
    :type shaderName: str
    :param shaderType: the type of shader, `RedshiftMaterial` `pxrSurface` `alStandardSurface` etc
    :type shaderType: str
    :param renameToZooName: Rename the existing shader to the shader name in the .zooScene
    :type renameToZooName: str
    :param message: report the success message to the user?
    :type message: bool
    :return shaderName:  The name of the shader set
    :rtype shaderName: str
    """
    shadersDict = loadGenericShaderLightFiles(zooScenePath)[0]  # get the shader dict
    firstKey = next(iter(shadersDict))
    shaderDict = shadersDict[firstKey]["attributesShaderDict"]
    shadermultirenderer.setShaderAttrs(shaderName, shaderType, shaderDict, reportMessage=message)
    if renameToZooName:
        zooSceneName = shadersDict[firstKey]["shaderName"]
        return cmds.rename(shaderName, zooSceneName)
    return shaderName


def saveShaderPresetZooScene(zooSceneFullPath, shaderInScene, shaderName):
    """Saves a Shader Preset as a .zooScene file with the generic shader JSON file (.zooGShad). No other data is saved.

    :param zooSceneFullPath:  The full path including the filename
    :type zooSceneFullPath: str
    :param shaderInScene: The shader name that will be read from the scene, it's data will be saved
    :type shaderInScene: str
    :param shaderName: The name of the shader that will be saved in the shader JSON file, can differ from shaderInScene
    :type shaderName: str
    :return zooSceneFullPath: The full path of the .zooScene file saved
    :rtype zooSceneFullPath: str
    :return gShaderFullPath: The full path of the shader JSON file saved (.zooGShad)
    :rtype gShaderFullPath: str
    """
    # Get the shader attrs
    shaderAttributes, nameMatch = shadermultirenderer.getShaderSelected(shaderName=shaderInScene)
    gShaderDict = {"nullObj": {"attributesShaderDict": shaderAttributes,
                               "shaderName": shaderName,
                               "objectFaces": []}
                   }
    # Save Shader info
    if gShaderDict:  # save the generic shader info
        gShaderFullPath = zooscenefiles.writeZooGShaders(gShaderDict, zooSceneFullPath)
    # Build the .zooScene dict
    zooSceneDict = {VERSIONKEY: GENERICVERSIONNO,
                    SHADERS: True,
                    LIGHTS: False,
                    constants.INFOSAVE: False}
    filesystem.saveJson(zooSceneDict, zooSceneFullPath, indent=4, separators=(",", ":"))
    om2.MGlobal.displayInfo("Success: Shader saved. ZooScene: `{}`".format(zooSceneFullPath))
    return zooSceneFullPath, gShaderFullPath
