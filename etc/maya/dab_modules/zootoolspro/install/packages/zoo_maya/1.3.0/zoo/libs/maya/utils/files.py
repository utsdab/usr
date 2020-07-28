import contextlib
import os

from maya import cmds, mel
from maya.api import OpenMaya as om2
from zoovendor.six import string_types
from zoo.libs.maya.utils import general
from zoo.libs.maya.api import nodes
from zoo.libs.maya.api import plugs
from zoo.libs.maya.cmds.objutils import objhandling
from zoo.libs.maya.cmds.cameras import cameras
from zoo.libs.utils import filesystem, zlogging, profiling

logger = zlogging.getLogger(__name__)


@contextlib.contextmanager
def exportContext(rootNode):
    changed = []
    for i in nodes.iterChildren(rootNode, recursive=True):
        dp = om2.MFnDependencyNode(i)
        plug = dp.findPlug("visibility", False)
        with plugs.setLockedContext(plug):
            if plug.asFloat() != 1.0:
                plugs.setPlugValue(plug, 1.0)
                changed.append(dp)
    yield
    for i in iter(changed):
        plug = i.findPlug("visibility", False)
        with plugs.setLockedContext(plug):
            plugs.setPlugValue(plug, 0.0)


@contextlib.contextmanager
def exportMultiContext(nodes):
    try:
        changed = []
        for i in nodes:
            dp = om2.MFnDependencyNode(i)
            plug = dp.findPlug("visibility", False)
            with plugs.setLockedContext(plug):
                if plug.asFloat() != 1.0:
                    plugs.setPlugValue(plug, 1.0)
                    changed.append(dp)
        yield
        for i in iter(changed):
            plug = i.findPlug("visibility", False)
            with plugs.setLockedContext(plug):
                plugs.setPlugValue(plug, 0.0)
    except RuntimeError:
        logger.error("Unknown Error Occurred during export",
                     exc_info=True)


@profiling.fnTimer
def saveScene(path, removeUnknownPlugins=False):
    logger.info("Saving new work File {}".format(path))
    maya_file_type = "mayaAscii"
    filesystem.ensure_folder_exists(os.path.dirname(path))
    if removeUnknownPlugins:
        logger.debug("Cleaning unknownPlugins from scene if any")
        general.removeUnknownPlugins()
    cmds.file(rename=path)
    cmds.file(save=True, force=True, type=maya_file_type)
    logger.info("Finished saving work file")


@profiling.fnTimer
def openFile(path, selectivePreload=False, force=True, modified=False):
    """ Opens the maya file.

    :param path: The absolute path to the maya file
    :type path: str
    :param selectivePreload: If True the preload reference dialog will be shown if there's references
    :type selectivePreload: bool
    :param force: Force's a new scene
    :type force: bool
    :param modified: If True then the scene state will be set to True, this is the same \
    as cmds.file(modified=True)
    :type modified: bool
    """
    path = path.replace("\\", "/")
    logger.debug("Starting a new maya session")
    cmds.file(new=True, force=force)
    if selectivePreload:
        cmds.file(path, buildLoadSettings=True, open=True)
        # query the reference count in the file, result of 1 means no references so don't show the preload dialog
        if cmds.selLoadSettings(numSettings=True, q=True) > 1:
            cmds.optionVar(stringValue=('preloadRefEdTopLevelFile', path))
            cmds.PreloadReferenceEditor()
            return
    logger.debug("Starting a opening maya scene: {}".format(path))
    cmds.file(path, open=True, force=True, ignoreVersion=True)
    cmds.file(modified=modified)
    logger.debug("completed opening maya scene: {}".format(path))


@profiling.fnTimer
def exportSceneAsFbx(filePath, skeletonDefinition=False, constraints=False):
    filePath = filePath.replace("/", "\\")
    mel.eval("FBXExportSmoothingGroups -v true;")
    mel.eval("FBXExportHardEdges -v false;")
    mel.eval("FBXExportTangents -v true;")
    mel.eval("FBXExportSmoothMesh -v false;")
    mel.eval("FBXExportInstances -v true;")
    # Animation
    mel.eval("FBXExportCacheFile -v false;")
    mel.eval("FBXExportBakeComplexAnimation -v false;")
    mel.eval("FBXExportApplyConstantKeyReducer -v true;")
    mel.eval("FBXExportUseSceneName -v false;")
    mel.eval("FBXExportQuaternion -v euler;")
    mel.eval("FBXExportShapes -v true;")
    mel.eval("FBXExportSkins -v true;")
    mel.eval("FBXExportConstraints -v {};".format("false" if not constraints else "true"))
    mel.eval("FBXExportSkeletonDefinitions -v {};".format("false" if not skeletonDefinition else "true"))
    mel.eval("FBXExportCameras -v true;")
    mel.eval("FBXExportLights -v true;")
    mel.eval("FBXExportEmbeddedTextures -v false;")
    mel.eval("FBXExportInputConnections -v true;")
    mel.eval("FBXExportUpAxis {};".format(general.upAxis()))
    mel.eval('FBXExport -f "{}";'.format(filePath.replace("\\", "/")))  # this maya is retarded
    return filePath


@profiling.fnTimer
def exportAbc(filePath, objectRootList=None, frameRange="1 1", visibility=True, creases=True, uvSets=True,
              autoSubd=True, dataFormat="ogawa", userAttr=None, userAttrPrefix=None, stripNamespaces=False,
              selection=False):
    """Exports and alembic file from multiple objects/transform nodes, could be multiple selected hierarchies for
     example objectRootList is the list of bojs who's hierarchy is to be exported

     *Note: since the cmds.AbcExport does not support spaces in filepaths, this function saves in temp and then moves
     the file to the correct location.

    :param filePath: the full file path to save to
    :type filePath: str
    :param objectRootList: a list of objects that are the root object, under each transform gets exported, None is scene
    :type objectRootList: list
    :param frameRange: frame range (to and from) separated by a space
    :type frameRange: str
    :param visibility: export visibility state?
    :type visibility: bool
    :param creases: export creases?  autoSubd needs to be on
    :type creases: bool
    :param uvSets: export with uv sets?
    :type uvSets: bool
    :param creases: export creases?  autoSubd needs to be on
    :type creases: bool
    :param autoSubd: Must be on for crease edges, crease vertices or holes, mesh is written out as an OSubD
    :type autoSubd: str
    :param userAttr: will export including Maya attributes with these custom strings in a list
    :type userAttr: tuple
    :param userAttrPrefix: will export including Maya attributes with these prefix's, custom strings in a list
    :type userAttrPrefix: tuple
    :param stripNamespaces: will strip the namespaces on export, if duplicated names it will fail
    :type stripNamespaces: bool
    :param selection: will export selected nodes only, given they are under the root list
    :type selection: bool
    """
    filePath = filePath.replace("/", "\\")
    fileName = os.path.split(filePath)[-1]
    tempDir = filesystem.getTempDir()  # needs temp dir as filepaths with spaces aren't supported
    tempPath = os.path.join(tempDir, fileName)
    command = "-frameRange {} -dataFormat {}".format(frameRange, dataFormat)
    if visibility:
        command += " -writeVisibility"
    if creases:
        command += " -writeCreases"
    if uvSets:
        command += " -writeUVSets"
    if objectRootList:
        for node in objectRootList:
            command += " -root {}".format(node)
    if autoSubd:
        command += " -autoSubd"
    if userAttr:
        for userAttrSingle in userAttr:
            command += " -userAttr {}".format(userAttrSingle)
    if userAttrPrefix:
        for userAttrPSingle in userAttrPrefix:
            command += " -userAttrPrefix {}".format(userAttrPSingle)
    if selection:
        command += " -selection"
    if stripNamespaces:
        command += " -stripNamespaces"
    command += ' -file {}'.format(tempPath)
    cmds.AbcExport(j=command)  # this will write to the temp directory
    fileNameFrom = os.path.join(tempDir, fileName)  # move from temp to actual path
    filesystem.moveFile(fileNameFrom, filePath)
    om2.MGlobal.displayInfo("Success Alembic Written: `{}`".format(filePath))
    return filePath


def getCamGeoRootsFromScene(exportGeo=True, exportCams=True, returnWorldRoots=True):
    """Returns the root objects of ge and cams (so that objects can't be doubled) top most node/s
    in a scene.  This is for .abc exporting where the root nodes need to be given and not doubled

    :param exportGeo: find roots of all geo in the scene?
    :type exportGeo: bool
    :param exportCams: find roots of all cameras in the scene?
    :type exportCams: bool
    :param returnWorldRoots: instead of returning the object roots, return the full scene roots, bottom of hierarchy
    :type returnWorldRoots: bool
    :return objectRootList: all root object names (objects can't be doubled) of the scene with cams or geo
    :rtype objectRootList: list
    """
    allCameraTransforms = list()
    allGeoTransforms = list()
    worldRootList = list()
    if exportGeo:  # get all geo
        allGeoShapes = cmds.ls(type='mesh', long=True)
        allGeoTransforms = objhandling.getListTransforms(allGeoShapes)
    if exportCams:  # get all cams
        allCameraTransforms = cameras.cameraTransformsAll()
    allTransforms = allCameraTransforms + allGeoTransforms
    objectRootList = objhandling.getRootObjectsFromList(allTransforms)
    if returnWorldRoots:
        for obj in objectRootList:
            worldRootList.append(objhandling.getTheWorldParentOfObj(obj))
        objectRootList = list(set(worldRootList))
    return objectRootList


@profiling.fnTimer
def exportAbcSceneFilters(filePath, frameRange="1 1", visibility=True, creases=True, uvSets=True,
                          dataFormat="ogawa", noMayaDefaultCams=True, exportGeo=True, exportCams=True,
                          exportAll=True, userAttr=None, userAttrPrefix=None):
    """Export alembic whole scene settings

    :param filePath: the full file path to save to
    :type filePath: str
    :param frameRange: frame range (to and from) separated by a space
    :type frameRange: str
    :param visibility: export visibility state?
    :type visibility: bool
    :param creases: export creases?  autoSubd needs to be on
    :type creases: bool
    :param uvSets: export with uv sets?
    :type uvSets: bool
    :param dataFormat: Alembic can save is a variety of formats, most commonly "ogawa"
    :type dataFormat: str
    :param noMayaDefaultCams: If True don't export Maya's default cams such as persp, top, side, front etc
    :type noMayaDefaultCams: bool
    :param exportGeo: Export geometry?
    :type exportGeo: bool
    :param exportCams: Export cameras?
    :type exportCams: bool
    :param exportAll: exports everything in the scene
    :type exportAll: bool
    :param userAttr: will export including Maya attributes with these custom strings in a list
    :type userAttr: tuple
    :param userAttrPrefix: will export including Maya attributes with these prefix's, custom strings in a list
    :type userAttrPrefix: tuple
    :return filePath:  the full file path to save the alembic
    :rtype filePath: str
    :return objectRootList: list of the root object to export, alembic requires root objects/transforms to export
    :rtype objectRootList: list(str)
    """
    if not exportGeo and not exportCams and not exportAll:
        om2.MGlobal.displayWarning("Alembic Nothing To Export")
        return "", list()
    if exportAll:  # get all roots in scene as still want to filter the default cameras maybe
        objectRootList = objhandling.getAllTansformsInWorld()
    else:  # get all roots of cam/geo if needed/wanted
        objectRootList = getCamGeoRootsFromScene(exportGeo=exportGeo, exportCams=exportCams)
    if noMayaDefaultCams:  # remove maya default cameras, front side etc
        mayaStartupCams = cameras.getStartupCamTransforms()
        objectRootList = [x for x in objectRootList if x not in mayaStartupCams]  # removes the maya cams from rootList
    # export the alembic
    if not objectRootList:
        om2.MGlobal.displayWarning("Alembic Nothing To Export")
        return "", list()
    filePath = exportAbc(filePath, objectRootList=objectRootList, frameRange=frameRange, visibility=visibility,
                         creases=creases, uvSets=uvSets, dataFormat=dataFormat, userAttr=userAttr,
                         userAttrPrefix=userAttrPrefix)
    return filePath, objectRootList


@profiling.fnTimer
def exportAbcSelected(filePath, frameRange="1 1", visibility=True, creases=True, uvSets=True,
                      dataFormat="ogawa", userAttr=None, userAttrPrefix=None):
    """Exports selected objects as alembic filetype .abc
    Alembics export from the root, so filter the root of each selection hierarchy

    :param filePath: the full file path to save to
    :type filePath: str
    :param frameRange: frame range (to and from) separated by a space
    :type frameRange: str
    :param visibility: export visibility state?
    :type visibility: bool
    :param creases: export creases?
    :type creases: bool
    :param uvSets: export with uv sets?
    :type uvSets:
    :param dataFormat: abc format type, usually "ogawa"
    :type dataFormat: str
    :return filePath:  the full file path to saved
    :rtype filePath: str
    """
    objectRootList = objhandling.getRootObjectsFromSelection()
    if not objectRootList:  # will have already reported the error
        return
    filePath = exportAbc(filePath, objectRootList, frameRange=frameRange, visibility=visibility, creases=creases,
                         uvSets=uvSets, dataFormat=dataFormat, userAttr=userAttr, userAttrPrefix=userAttrPrefix)
    return filePath, objectRootList


@profiling.fnTimer
def exportObj(filePath, sceneNode):
    filePath = filePath.replace("/", "\\")
    cmds.select(sceneNode)
    cmds.file(filePath, force=True, options="groups=0;ptgroups=0;materials=0;smoothing=1;normals=1", typ="OBJexport",
              pr=True,
              es=True)
    cmds.select(cl=True)
    return filePath


@profiling.fnTimer
def importAlembic(filePath):
    cmds.AbcImport(filePath, mode="import")
    return filePath


@profiling.fnTimer
def importObj(filePath):
    cmds.file(filePath, i=True, type="OBJ", ignoreVersion=True, mergeNamespacesOnClash=False, options="mo=1;lo=0")
    return filePath


@profiling.fnTimer
def importFbx(filepath, cameras=False, lights=False, skeletonDefinition=True, constraints=True):
    filepath = filepath.replace("/", "\\")
    mel.eval("FBXImportMode -v add;")
    mel.eval("FBXImportMergeAnimationLayers -v false;")
    mel.eval("FBXImportProtectDrivenKeys -v false;")
    mel.eval("FBXImportConvertDeformingNullsToJoint -v false;")
    mel.eval("FBXImportMergeBackNullPivots -v false;")
    mel.eval("FBXImportSetLockedAttribute -v true;")
    mel.eval("FBXExportConstraints -v {};".format("false" if not constraints else "true"))
    mel.eval("FBXExportSkeletonDefinitions -v {};".format("false" if not skeletonDefinition else "true"))
    mel.eval("FBXImportLights -v {};".format(str(lights).lower()))
    mel.eval("FBXImportCameras -v {};".format(str(cameras).lower()))
    mel.eval("FBXImportHardEdges -v true;")
    mel.eval("FBXImportShapes -v true;")
    mel.eval("FBXImportUnlockNormals -v true;")
    mel.eval('FBXImport -f "{}";'.format(filepath.replace("\\", "/")))  # stupid autodesk and there mel crap
    return True


@profiling.fnTimer
def exportFbx(filePath, exportNodes, skeletonDefinition=False, constraints=False, **kwargs):
    """
    :param filePath: The absolute file path
    :type filePath: str
    :param exportNodes:
    :type exportNodes: list or str
    :param skeletonDefinition:
    :type skeletonDefinition: bool
    :param constraints:
    :type constraints: bool
    :param kwargs:
    :type kwargs: dict
    :return:
    :rtype:
    """
    general.loadPlugin("fbxmaya")
    if isinstance(exportNodes, string_types):
        exportNodes = [exportNodes]
    upAxis = kwargs.get("FBXExportUpAxis", general.upAxis())
    # If baking required over a specific frame range, for subframes for example, then set them in kwargs.
    startFrame = kwargs.get("startFrame")
    endFrame = kwargs.get("endFrame")
    with exportMultiContext(map(nodes.asMObject, exportNodes)):
        mel.eval("FBXResetExport;")
        mel.eval("FBXExportSmoothingGroups -v {};".format(kwargs.get("smoothingGroups", "true")))
        mel.eval("FBXExportHardEdges -v {};".format(kwargs.get("hardEdges", "false")))
        mel.eval("FBXExportTangents -v true;")
        mel.eval("FBXExportSmoothMesh -v false;")
        mel.eval("FBXExportInstances -v true;")
        # Animation
        mel.eval("FBXExportCacheFile -v false;")
        mel.eval("FBXExportApplyConstantKeyReducer -v false;")
        mel.eval("FBXExportUseSceneName -v false;")
        mel.eval("FBXExportQuaternion -v resample;")
        mel.eval("FBXExportShapes -v {};".format("false" if not kwargs.get("shapes") else "true"))
        mel.eval("FBXExportSkins -v {};".format("false" if not kwargs.get("skins") else "true"))
        mel.eval("FBXExportConstraints -v {};".format("false" if not constraints else "true"))
        mel.eval("FBXExportSkeletonDefinitions -v {};".format("false" if not skeletonDefinition else "true"))
        mel.eval("FBXExportCameras -v {};".format("false" if not kwargs.get("cameras") else "true"))
        mel.eval("FBXExportLights -v {};".format("false" if not kwargs.get("lights") else "true"))
        mel.eval("FBXExportEmbeddedTextures -v false;")
        mel.eval("FBXExportInputConnections -v {};".format("false" if not kwargs.get("inputConnections") else "true"))
        mel.eval("FBXExportUpAxis {};".format(upAxis))
        mel.eval("FBXExportBakeComplexAnimation -v {};".format("false" if not kwargs.get("animation") else "true"))
        mel.eval("FBXExportBakeResampleAnimation -v {};".format("false" if not kwargs.get("resample") else "true"))
        mel.eval("FBXExportBakeComplexStep -v {:f};".format(kwargs.get("step", 1.0)))
        mel.eval("FBXExportIncludeChildren -v {}".format("false" if not kwargs.get("includeChildren") else "true"))
        if startFrame is not None:
            mel.eval("FBXExportBakeComplexStart -v {:d};".format(startFrame))
        if endFrame is not None:
            mel.eval("FBXExportBakeComplexEnd -v {:d};".format(endFrame))
        mel.eval("FBXExportGenerateLog -v true")
        if kwargs.get("version"):
            mel.eval("FBXExportFileVersion -v {}".format(kwargs.get("version")))
        cmds.select(exportNodes)
        mel.eval('FBXExport -f "{}" -s;'.format(filePath.replace("\\", "/")))  # this maya is retarded
        cmds.select(cl=True)

    return filePath
