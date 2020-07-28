from maya import cmds
import maya.api.OpenMaya as om2

from zoo.libs.maya.cmds.lighting import arnoldlights, rendermanlights, redshiftlights
from zoo.libs.maya.cmds.cameras import cameras

GEO_SX = 'geo'
JOINT_SX = 'jnt'
CONTROLLER_SX = 'ctrl'
GROUP_SX = 'grp'
SRT_SX = 'srt'
LEFT_SX = 'L'
LEFT2_SX = 'lft'
RIGHT_SX = 'R'
RIGHT2_SX = 'rgt'
CENTER_SX = 'M'
CENTER2_SX = 'cntr'
CENTER3_SX = 'mid'
LOW = 'low'
HIGH = 'high'
LORES = 'lores'
HIRES = 'hires'
CURVE_SX = 'crv'
CLUSTER_SX = 'cstr'
FOLLICLE_SX = 'foli'
NURBS_SX = 'geo'
IMAGEPLANE_SX = 'imgp'
LOCATOR_SX = 'loc'
LIGHT_SX = 'lgt'
SHADER_SX = 'shdr'
SHADINGGROUP_SX = 'shdg'
CAMERA_SX = 'cam'

SUFFIXLIST = ["Select...",
              "Mesh: '{}'".format(GEO_SX),
              "Joint: '{}'".format(JOINT_SX),
              "Control: '{}'".format(CONTROLLER_SX),
              "Group: '{}'".format(GROUP_SX),
              "Rot Trans Scl: '{}'".format(SRT_SX),
              "Left: '{}'".format(LEFT_SX),
              "Left: '{}'".format(LEFT2_SX),
              "Right: '{}'".format(RIGHT_SX),
              "Right: '{}'".format(RIGHT2_SX),
              "Center: '{}'".format(CENTER_SX),
              "Center: '{}'".format(CENTER2_SX),
              "Center: '{}'".format(CENTER3_SX),
              "Low: '{}'".format(LOW),
              "High: '{}'".format(HIGH),
              "Lores: '{}'".format(LORES),
              "Hires: '{}'".format(HIRES),
              "Camera: '{}'".format(CAMERA_SX),
              "Curve: '{}'".format(CURVE_SX),
              "Cluster: '{}'".format(CLUSTER_SX),
              "Follicle: '{}'".format(FOLLICLE_SX),
              "Nurbs: '{}'".format(NURBS_SX),
              "Image Planes: '{}'".format(IMAGEPLANE_SX),
              "Locators: '{}'".format(LOCATOR_SX),
              "Shader: '{}'".format(SHADER_SX),
              "Lights: '{}'".format(LIGHT_SX),
              "Shading Group: '{}'".format(SHADINGGROUP_SX)]

AUTO_SUFFIX_DICT = {"mesh": GEO_SX,
                    "joint": JOINT_SX,
                    "nurbsCurve": CURVE_SX,
                    "group": GROUP_SX,
                    "follicle": FOLLICLE_SX,
                    "nurbsSurface": GEO_SX,
                    "imagePlane": IMAGEPLANE_SX,
                    "aiAreaLight": LIGHT_SX,
                    "rsPhysicalLight": LIGHT_SX,
                    "PxrRectLight": LIGHT_SX,
                    "PxrSphereLight": LIGHT_SX,
                    "PxrDiskLight": LIGHT_SX,
                    "PxrDistantLight": LIGHT_SX,
                    "PxrDomeLight": LIGHT_SX,
                    "locator": LOCATOR_SX,
                    "light": LIGHT_SX,
                    "lambert": SHADER_SX,
                    "blinn": SHADER_SX,
                    "phong": SHADER_SX,
                    "rampShader": SHADER_SX,
                    "phongE": SHADER_SX,
                    "surfaceShader": SHADER_SX,
                    "useBackground": SHADER_SX,
                    "shadingGroup": SHADINGGROUP_SX,
                    "aiStandardSurface": SHADER_SX,
                    "RedshiftMaterial": SHADER_SX,
                    "PxrSurface": SHADER_SX,
                    "controller": CONTROLLER_SX,
                    "camera": CAMERA_SX,
                    "clusterHandle": CLUSTER_SX}

EXTRA_PROTECTED_NODES = ["layerManager", "renderLayerManager", "poseInterpolatorManager", "defaultRenderLayer",
                         "defaultLayer", "lightLinker1", "shapeEditorManager"]

ALL = "All Node Types"
GROUP = "Group"
GEOMETRY = "Geometry"
POLYGON = "Polygon"
NURBS = "Nurbs"
JOINT = "Joint"
CURVE = "Curve"
LOCATOR = "Locator"
LIGHT = "Light"
CAMERA = "Camera"
CLUSTER = "Cluster"
FOLLICLE = "Follicle"
DEFORMER = "Deformer"
TRANSFORM = "Transform"
CONTROLLERS = "Controllers"

DEFORMER_TYPE_LIST = ["clusterHandle", "baseLattice", "lattice", "softMod", "deformBend", "sculpt", "deformTwist",
                      "deformWave", "deformFlare"]
LIGHT_TYPE_LIST = ["light"]
# TODO light type list will only work while checking if Renderman or Arnold or Redshift is loaded
LIGHT_PLUGIN_TYPE_LIST = rendermanlights.ALLLIGHTTYPES + arnoldlights.ALLLIGHTTYPES + redshiftlights.ALLLIGHTTYPES
ALL_SPECIAL = "ALL"
GROUP_SPECIAL = "GROUP"

# list of nice names for real values see relative TYPE_FILTER_DICT
TYPE_FILTER_LIST = [ALL, POLYGON, NURBS, GEOMETRY, JOINT, CURVE, CONTROLLERS, GROUP, LOCATOR, LIGHT, CAMERA, CLUSTER,
                    FOLLICLE, DEFORMER]

# lookup for filtering, finds the nice name and returns the object type or other special type
TYPE_FILTER_DICT = {ALL: [ALL_SPECIAL],
                    POLYGON: ["mesh"],
                    NURBS: ["nurbsSurface"],
                    GEOMETRY: ["mesh", "nurbsSurface"],
                    JOINT: ["joint"],
                    CURVE: ["nurbsCurve"],
                    GROUP: [GROUP_SPECIAL],
                    LOCATOR: ["locator"],
                    LIGHT: ["light"],
                    CAMERA: ["camera"],
                    CLUSTER: ["cluster"],
                    FOLLICLE: ["follicle"],
                    DEFORMER: DEFORMER_TYPE_LIST,
                    TRANSFORM: ["transform"]}


# ---------------------------
# FILTER SHAPE BY TYPE
# ---------------------------


def filterExactTypeList(nodeList, type="transform"):
    """Returns a list filtered to be only the type of node

    Easy to forget this one liner, best not to use, here for reference"""
    return cmds.ls(nodeList, type=type)


def filterTypeReturnTransforms(objList, children=False, shapeType="nurbsCurve"):
    """From a transform list filters the objects which have shape nodes of the given type, returns a transform list.

    Joints are also included as transforms and can be passed in and returned

    :param objList: Maya obj list
    :type objList: list
    :return curveObjList: list of curve transforms now filtered
    :rtype curveObjList: list
    """
    curveObjList = list()
    fullObjList = list(objList)
    if children:
        joints = cmds.listRelatives(objList, children=True, allDescendents=True, fullPath=True, type="joint")
        if joints:
            fullObjList += joints
        transforms = cmds.listRelatives(objList, children=True, allDescendents=True, fullPath=True, type="transform")
        if transforms:
            fullObjList += transforms
        fullObjList = list(set(fullObjList))  # remove duplicates
    for obj in fullObjList:
        shapes = cmds.listRelatives(obj, shapes=True, fullPath=True, type=shapeType)
        if shapes:
            curveObjList.append(obj)
    return curveObjList


def filterTypeReturnShapes(objList, children=False, shapeType="nurbsCurve"):
    """From a transform list filters the objects which have shape nodes of the given type, returns a shape list.

    Joints are also included as transforms and can be passed in

    :param objList: Maya transform obj list
    :type objList: list
    :return curveObjList: list of curve shapes now filtered
    :rtype curveObjList: list
    """
    curveShapeList = list()
    for obj in objList:
        shapes = cmds.listRelatives(obj, shapes=True, allDescendents=children, fullPath=True, type=shapeType)
        if shapes:
            curveShapeList += shapes
    return curveShapeList


def shapeTypeFromTransformOrShape(nodeList, shapeType="nurbsCurve"):
    """Returns a list of shapes of the given type from a node list that can include transforms and shape nodes.

    Joints are also included as transforms

    :param nodeList: Maya node list of any type
    :type nodeList: list(str)
    :param shapeType: The type name of the node, eg "nurbsCurve" or "camera"
    :type shapeType: str
    :return returnShapes: A list of shape nodes from the children of the transforms or the actual matching nodes.
    :rtype returnShapes: list(str)
    """
    returnShapes = list()
    for node in nodeList:
        if cmds.objectType(node, isType="transform") or cmds.objectType(node, isType="joint"):
            returnShapes += filterTypeReturnShapes([node], shapeType=shapeType)
        elif cmds.objectType(node, isType=shapeType):
            returnShapes.append(node)
    return returnShapes


# ---------------------------
# FILTER GEOMETRY
# ---------------------------


def filterGeoOnly(objList, nurbs=True, polygons=True):
    """Filters a node list for both shapes and transforms and returns geometry, nurbs or polygons

    Note:  cmds.ls(objList, geometry=True)  #  will only return if shapes are selected

    :param objList: A list of Maya objects, shapes or other nodes
    :type objList: list(str)
    :param nurbs: if True return NurbsSurfaces
    :type nurbs: bool
    :param polygons: if True return Meshes
    :type polygons: bool
    :return geoList:  A list of geometry, can be mixed transforms and shapes
    :rtype geoList: list(str)
    """
    geoList = list()
    transformList = cmds.ls(objList, type="transform")
    if polygons:
        geoList += cmds.ls(objList, type="mesh")
    if nurbs:
        geoList += cmds.ls(objList, type="nurbsSurface")
    if transformList:
        for transform in transformList:
            shapes = cmds.listRelatives(transform, shapes=True)
            if not shapes:
                continue
            for shape in shapes:
                if cmds.ls(shape, type="nurbsSurface") and nurbs:
                    geoList.append(shape)
                if cmds.ls(shape, type="mesh") and polygons:
                    geoList.append(shape)
    return geoList


# ---------------------------
# FILTER DEFORMERS
# ---------------------------


def deformerHistoryOnObj(objTransform, ignoreTweak=True):
    """Returns all deformers on object including skinning, can ignore the tweak node.

    :param objTransform: Maya obj transform name
    :type objTransform: str
    :param ignoreTweak: Ignore returning the tweak node if True, False will return it if it exists
    :type ignoreTweak: bool
    :return deformHistoryFiltered: A list of deformer nodes attached to the object
    :rtype deformHistoryFiltered: list(str)
    """
    deformHistoryFiltered = list()
    history = cmds.listHistory(objTransform) or []
    deformHistory = cmds.ls(history, type="geometryFilter", long=True)
    if not deformHistory:
        return list()
    if ignoreTweak:  # include the tweak node?  Then return
        return deformHistory
    for deformer in deformHistory:  # remove the tweak node, can do this better
        if not cmds.objectType(deformer) == "tweak":
            deformHistoryFiltered.append(deformer)
    return deformHistoryFiltered


# ---------------------------
# SELECTION AND SCENE FILTERING
# ---------------------------


def filterTypeObjList(objTypeList, objList=(), searchHierarchy=False, searchScene=False, dag=False):
    """Returns a list of objects/nodes in Maya that match the filter criteria, usually by node type:

        Can filter by a list of nodeTypes
        Can limit the filter to an object list or over ride to search the whole scene
        Can search the hierarchy of the objList

    :param objTypeList: A list of node types, usually from a key in TYPE_FILTER_DICT.  DEFORMER_TYPE_LIST for example
    :type objTypeList: list(str)
    :param objList: A list of maya nodes/object names
    :type objList: list(str)
    :param searchHierarchy: Also try to search the hierarchy below the objectList?  False will only filter objList
    :type searchHierarchy: bool
    :param searchScene: If True will ignore the objList and search the whole scene instead
    :type searchScene: bool
    :param dag: return only dag nodes?  Ie nodes that can be viewed in the outliner hierarchy tree? Includes children
    :type dag: bool
    :return filteredNodes: Returns a list of objects/nodes in Maya that match the filter criteria
    :rtype filteredNodes: list(str)
    """
    filteredObjs = list()
    if searchScene:
        for objType in objTypeList:
            filteredObjs += cmds.ls(type=objType, long=True, dagObjects=searchHierarchy, dag=dag)
    else:
        for objType in objTypeList:
            filteredObjs += cmds.ls(objList, type=objType, long=True, dagObjects=searchHierarchy, dag=dag)
    return list(set(filteredObjs))


def filterShapesFromList(objList, allowJoints=True, allowDG=True):
    """If a shape node is in objList replace with it's transform parent. Otherwise will leave the node in the list.

    Options:

        Can include joints as transforms
        Can allow DG nodes (can't have transform node parents)

    :param objList: A list of maya nodes/object names
    :type objList: list(str)
    :param allowJoints: If True include joints in the returned list, treat them as transform nodes
    :type allowJoints: list(str)
    :param allowDG: If True allow DG nodes to be returned.  DG nodes cannot have transform parents eg shaders
    :type allowDG: list(str)
    :return objList: objList now with the shape nodes replaced to be their transform nodes
    :rtype objList: list(str)
    """
    transformList = list()
    for obj in objList:
        if cmds.objectType(obj, isType="transform"):
            transformList.append(obj)
        elif cmds.objectType(obj, isType="joint") and allowJoints:
            transformList.append(obj)
        else:  # see if it has a transform as a parent
            if 'dagNode' in cmds.nodeType(obj, inherited=True):  # check if a dag node return parent if so
                transformList.append(cmds.listRelatives(obj, parent=True, fullPath=True)[0])
            elif allowDG:  # is not a dag node, will not have a transform parent
                transformList.append(obj)
    return list(set(transformList))


def filterDagObjTransforms(objTypeList, searchHierarchy=False, selectionOnly=True, message=True, dag=False,
                           transformsOnly=True):
    """Returns a list of objects/nodes in Maya that match the filter criteria, usually by node type, will filter further
    by returning only the transform parents of shape nodes. Also can filter based on selection

        Can filter by a list of nodeTypes
        Can limit the filter to an object list or over ride to search the whole scene
        Can search the hierarchy of the objList
        Can limit the returned list to transforms that will replace any shape nodes
        Can limit the returned objects to the current selection

    :param objTypeList: A list of node types, usually from a key in TYPE_FILTER_DICT.  DEFORMER_TYPE_LIST for example
    :type objTypeList: list(str)
    :param searchHierarchy: Also try to search the hierarchy below the objectList?  False will only filter objList
    :type searchHierarchy: bool
    :param selectionOnly: If True search the selected objects not the whole scene
    :type selectionOnly: bool
    :param message: Return the message to the user?
    :type message: bool
    :param dag: return only dag nodes?  Ie nodes that can be viewed in the outliner hierarchy tree? Includes children
    :type dag: bool
    :param transformsOnly: If True will not further filter the transforms with the function filterShapesFromList()
    :type transformsOnly: bool
    :return filteredNodes: Returns a list of objects/nodes in Maya that match the filter criteria
    :rtype filteredNodes: list(str)
    """
    if selectionOnly:
        selObjs = cmds.ls(selection=True, long=True)
        if not selObjs:
            if message:
                om2.MGlobal.displayWarning("No objects selected. Please select an object")
            return list()
        shapesList = cmds.listRelatives(selObjs, shapes=True, fullPath=True)
        if shapesList:
            selObjs += shapesList  # add the shapes of the current selection
        filteredShapes = filterTypeObjList(objTypeList, objList=selObjs, searchHierarchy=searchHierarchy, dag=dag)
    else:
        filteredShapes = filterTypeObjList(objTypeList, searchHierarchy=False, searchScene=True, dag=dag)
    if not transformsOnly:
        return filteredShapes
    return filterShapesFromList(filteredShapes)


def filterAllNodeTypes(selectionOnly=True, searchHierarchy=False, dag=False, transformsOnly=False,
                       removeMayaDefaults=True, message=True):
    """Function used while filtering with no restrictions on node types, ie All node types.

    Does not use the function filterShapesFromList()

        Can limit the returned objects to the current selection, or False whole scene
        Can search the hierarchy of the objList
        Can limit the returned list to transforms that will replace any shape nodes
        Can ignore Maya default nodes such as lambert1 and persp front cams etc

    :param selectionOnly: If True search the selected objects not the whole scene
    :type selectionOnly: bool
    :param searchHierarchy: Also try to search the hierarchy below the objectList?  False will only filter objList
    :type searchHierarchy: bool
    :param dag: return only dag nodes?  Ie nodes that can be viewed in the outliner hierarchy tree? Includes children
    :type dag: bool
    :param transformsOnly: If True will not further filter the transforms with the function filterShapesFromList()
    :type transformsOnly: bool
    :param removeMayaDefaults: While filtering the whole scene don't include default nodes such as lambert1/persp etc
    :type removeMayaDefaults: bool
    :return filteredNodes: Returns a list of objects/nodes in Maya that match the filter criteria
    :rtype filteredNodes: list(str)
    """
    if not selectionOnly:  # return the scene (except Maya default cams and lambert)
        allObjs = cmds.ls(long=True, dagObjects=searchHierarchy, dag=dag)
        if not removeMayaDefaults:  # return as much as possible, can't rename protected nodes
            protected = cmds.ls(defaultNodes=True) + EXTRA_PROTECTED_NODES
            sceneFiltered = list(set(allObjs) - set(protected))
            if not transformsOnly:
                return sceneFiltered
            else:
                return filterShapesFromList(sceneFiltered)
        # TODO could make this more comprehensive time etc
        # take the defaults out of all dag objects
        mayaDefaults = cameras.getStartupCamTransforms() + cameras.getStartupCamShapes() \
                       + cmds.ls(defaultNodes=True) + EXTRA_PROTECTED_NODES
        sceneFiltered = list(set(allObjs) - set(mayaDefaults))
        if not transformsOnly:
            return sceneFiltered
        else:
            return filterShapesFromList(sceneFiltered)
    # if all types and selected
    allSelectedObjs = cmds.ls(selection=True, long=True, dagObjects=searchHierarchy, dag=dag)
    if not allSelectedObjs:
        if message:
            om2.MGlobal.displayWarning("No objects selected, please select an object")
            return list()
    if transformsOnly:
        return filterShapesFromList(allSelectedObjs)  # return only
    else:
        return allSelectedObjs


def filterByGroup(selectionOnly, searchHierarchy, dag, message=True):
    """Return nodes that are "groups".  Groups are empty transform nodes with no shapes nodes

    :param selectionOnly: If True search the selected objects not the whole scene
    :type selectionOnly: bool
    :param searchHierarchy: Also try to search the hierarchy below the objectList?  False will only filter objList
    :type searchHierarchy: bool
    :param dag: return only dag nodes?  Ie nodes that can be viewed in the outliner hierarchy tree? Includes children
    :type dag: bool
    :param message: Return the message to the user?
    :type message: bool
    :return filteredNodes: Returns a list of objects/nodes in Maya that match the filter criteria
    :rtype filteredNodes: list(str)
    """
    objList = list()
    groupList = list()
    searchScene = not selectionOnly
    if selectionOnly:
        objList = cmds.ls(selection=True, long=True)
        if not objList:
            if message:
                om2.MGlobal.displayWarning("Nothing is selected, please select objects")
            return list()
    objTransforms = filterTypeObjList([TYPE_FILTER_DICT[TRANSFORM]],
                                      objList=objList,
                                      searchHierarchy=searchHierarchy,
                                      searchScene=searchScene, dag=dag)
    if not objTransforms:
        if message:
            om2.MGlobal.displayWarning("No groups were found")
        return list()
    for obj in objTransforms:  # may still be a joint or have shape nodes (not a group)
        if not cmds.listRelatives(obj, shapes=True) and cmds.objectType(obj, isType="transform"):
            groupList.append(obj)
    return groupList


def filterByNiceType(niceNameType, searchHierarchy=False, selectionOnly=True, dag=False,
                     removeMayaDefaults=True, transformsOnly=True, message=True):
    """Returns a list of objects/nodes in Maya that match the filter criteria, usually by node type.

    This is the main function as used by GUIs:

        Can filter by a list of nodeTypes
        Can filter by special node types such as "group" which does not have a node type name
        Can limit the filter to an object list or over ride to search the whole scene (selectionOnly=False)
        Can include the hierarchy of the objList in the search
        Can limit the returned list to transforms that will replace any shape nodes
        Can ignore Maya default nodes such as lambert1 and persp front cams etc

    The nice names include types that aren't maya object types such as "Groups" and "All Types", some types are
    multiple object types, "Light" for example will find many node types.

    TYPE_FILTER_LIST globals include:

        ALL = "All Types"
        POLYGON = "Polygon"
        NURBS = "Nurbs"
        GEOMETRY = "Geometry"
        JOINT = "Joint"
        CURVE = "Curve"
        GROUP = "Group"
        LOCATOR = "Locator"
        LIGHT = "Light"
        CAMERA = "Camera"
        CLUSTER = "Cluster"
        FOLLICLE = "Follicle"
        DEFORMER = "Deformer"
        TRANSFORM = "Transform"

    :param niceNameType: A single string from the list TYPE_FILTER_LIST, describes a type of node/s in Maya
    :type niceNameType: str
    :param selectionOnly: If True search the selected objects not the whole scene
    :type selectionOnly: bool
    :param searchHierarchy: Also try to search the hierarchy below the objectList?  False will only filter objList
    :type searchHierarchy: bool
    :param dag: return only dag nodes?  Ie nodes that can be viewed in the outliner hierarchy tree? Includes children
    :type dag: bool
    :param transformsOnly: If True will not further filter the transforms with the function filterShapesFromList()
    :type transformsOnly: bool
    :param removeMayaDefaults: While filtering the whole scene don't include default nodes such as lambert1/persp etc
    :type removeMayaDefaults: bool
    :param message: Return the message to the user?
    :type message: bool
    :return filteredNodes: Returns a list of objects/nodes in Maya that match the filter criteria
    :rtype filteredNodes: list(str)
    """
    if not selectionOnly:  # disable search hierarchy is searching all
        searchHierarchy = False
    objTypeList = TYPE_FILTER_DICT[niceNameType]
    if objTypeList[0] == ALL_SPECIAL:  # ALL return all node types
        return filterAllNodeTypes(selectionOnly,
                                  searchHierarchy=searchHierarchy,
                                  dag=dag,
                                  transformsOnly=transformsOnly,
                                  removeMayaDefaults=removeMayaDefaults,
                                  message=message)
    elif objTypeList[0] == GROUP_SPECIAL:  # GROUPS return transforms without shape nodes and not joints
        return filterByGroup(selectionOnly,
                             searchHierarchy,
                             dag,
                             message=message)
    else:  # OBJECT TYPE LIST the type list should be legitimate so just search it
        return filterDagObjTransforms(objTypeList,
                                      searchHierarchy=searchHierarchy,
                                      selectionOnly=selectionOnly,
                                      dag=dag, message=message)


def filterByNiceTypeKeepOrder(niceNameType, searchHierarchy=False, selectionOnly=True, dag=False,
                              removeMayaDefaults=True, transformsOnly=True, message=True):
    """Same as filterByNiceType() but keeps the order of selection and hierarchy with more work

    TODO: May be possible to keep the order in the original function, mostly has to do with sets losing the order.

    See filterByNiceType() for documentation
    """
    if selectionOnly:
        selObjs = cmds.ls(selection=True, long=True, dagObjects=searchHierarchy)  # dagObjects is hierarchy children
        filteredResult = filterByNiceType(niceNameType, searchHierarchy, selectionOnly, dag,
                                          removeMayaDefaults, transformsOnly, message)
        removeResult = [x for x in selObjs if x not in filteredResult]  # selObjs - filteredResult
        return [x for x in selObjs if x not in removeResult]  # selObjs - removeResult
    else:  # returns whole scene so don't worry about order
        return filterByNiceType(niceNameType, searchHierarchy, selectionOnly, dag,
                                removeMayaDefaults, transformsOnly, message)
