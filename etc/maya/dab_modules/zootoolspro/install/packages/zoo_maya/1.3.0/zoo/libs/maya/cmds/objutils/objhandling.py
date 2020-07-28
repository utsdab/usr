"""functions for handling objects in Maya.

"""
import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as om2
import maya.OpenMaya as om1


def getAllParents(obj, long=True):
    """Returns all parents of the current obj.  Long will return long names

    :param obj: A Maya DAG object name
    :type obj: str
    :param long: Return long names?
    :type long: bool
    :return parents: List of the parents of this object
    :rtype parents: list(str)
    """
    parents = cmds.ls(obj, long=True)[0].split("|")[1:-1]
    if long:  # Get long names
        parents = ["|".join(parents[:i]) for i in range(1, 1 + len(parents))]
        for i, obj in enumerate(parents):  # must add "|" to the beginning of each name
            parents[i] = "|{}".format(obj)
    return parents


def getRootObjectsFromList(objsLongList):
    """Returns only the bottom hierarchy objects (roots) in an object list

    Compares longnames and filters by the start of each string o get the lowest unique name
    eg. |group1 will filter out |group1|mesh1 and |group1|mesh1|locator2

    :param objsLongList: list of maya object names, as long (full) names with "|"
    :type objsLongList: list
    :return rootObjs: only the bottom objects of the hierarchy, no children included
    :rtype rootObjs:
    """
    removeList = list()
    for i, checkObj in enumerate(objsLongList):
        for obj in objsLongList:
            if checkObj == obj:
                continue
            if checkObj.startswith("{}|".format(obj)):  # True then it's a child
                removeList.append(checkObj)
                break
    rootObjs = list(set(objsLongList) - set(removeList))
    return rootObjs


def getRootObjectsFromSelection():
    """Returns only the bottom hierarchy objects in a selection,
    Compares longnames and filters byt the start
    eg. |group1 will filter out |group1|mesh1 and |group1|mesh1|locator2

    :param objsLongList: list of maya object names, as long (full) names with "|"
    :type objsLongList: list
    :return rootObjs: only the bottom objects of the hierarchy, no children included
    :rtype rootObjs: list
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        om2.MGlobal.displayWarning('No Objects Selected, Please Select'.format())
        return
    return getRootObjectsFromList(selObjs)





def getListTransforms(mayaShapeList, longName=True):
    """From a list of Maya shape nodes return their transforms

    :param mayaShapeList: list of maya shape node names
    :type mayaShapeList: list
    :return transformList: list of transform names related to the node list
    :rtype transformList: list
    """
    transformList = list()
    for node in mayaShapeList:
        parent = cmds.listRelatives(node, parent=True, fullPath=longName)[0]
        if cmds.objectType(parent, isType='transform'):
            transformList.append(parent)
    return list(set(transformList))


# -----------------------------
# INSTANCING
# -----------------------------


def getInstances():
    """Returns all instanced nodes in a scene

    :return instances: all instance names in a scene
    :type instances: list
    """
    instances = []
    iterDag = om1.MItDag(om1.MItDag.kBreadthFirst)
    while not iterDag.isDone():
        instanced = om1.MItDag.isInstanced(iterDag)
        if instanced:
            instances.append(iterDag.fullPathName())
        iterDag.next()
    return instances


def isInstanced(longName):
    """Returns if an object is instanced?

    :param longName: The fullpath of a maya DAG object "|grpX|cube1"
    :type longName: str
    :return isInstanced: Is the object an instance or not?
    :rtype isInstanced: bool
    """
    if not cmds.objExists(longName):
        return None
    else:
        selectionList = om1.MSelectionList()
        selectionList.add(longName)
        dagPath = om1.MDagPath()
        selectionList.getDagPath(0, dagPath)
        return dagPath.isInstanced()


def uninstanceObjs(objs):
    """Uninstances all given objects uses mel eval of `convertInstanceToObject;`

    Objects do not need to be an instance, will accept non instanced geo
    """
    rememberSelection = cmds.ls(selection=True)
    cmds.select(objs, replace=True)
    uninstanceSelected()
    cmds.select(rememberSelection, replace=True)


def uninstanceSelected():
    """Uninstance the selected in the scene"""
    mel.eval('convertInstanceToObject;')


def uninstanceAllDepretiated():
    """Uninstances all objects in a scene. mel eval of `convertInstanceToObject;`
    """
    rememberSelection = cmds.ls(selection=True)
    instances = getInstances()
    cmds.select(instances, replace=True)
    uninstanceSelected()
    cmds.select(rememberSelection, replace=True)


def uninstanceAll():
    """Uninstances all objects in a scene.  Works by duplicating the instance and deletes it while maintaining names.
    This avoids the mel eval of `convertInstanceToObject;` which will delete the instanced object

    :return parentInstanceList: The Instanced Parents in the scene that were uninstanced
    :rtype parentInstanceList: list
    """
    instances = getInstances()
    parentInstanceList = []
    while len(instances):
        parent = cmds.listRelatives(instances[0], parent=True, fullPath=True)[0]
        newName = str((cmds.duplicate(parent))[0])  # duplicate to avoid mel eval
        newName = (newName.split('|'))[-1]
        cmds.delete(parent)
        cmds.rename(newName, parent)
        parentInstanceList.append(parent)
        instances = getInstances()
    om2.MGlobal.displayInfo('Success: Instance Objects Removed: {}'.format(parentInstanceList))
    return parentInstanceList


# -----------------------------
# CONNECTIONS
# -----------------------------


def cleanConnections(objName, keyframes=True):
    """Cleans an object of all connections, keys/connections constraints
    currently only works for keys

    :param objName: name of the obj to clean
    :type objName: str
    :param keyframes: do you want to clean keyframes?
    :type keyframes: bool
    :return:
    """
    if keyframes:
        cmds.cutKey(objName, s=True)  # delete key command


# -----------------------------
# GET BY TYPE
# -----------------------------


def getTypeTransformsHierarchy(objList, type="mesh"):
    """Returns the nodes of a certain type under the current hierarchy (maya list)

    :param objList: list of maya objects
    :type objList: list
    :param type: the type of node to filter
    :type type: str
    :return filteredNodes: a list of maya node names, the nodes now filtered
    :rtype filteredNodes: list
    """
    meshShapes = cmds.listRelatives(objList, allDescendents=True, fullPath=True, type=type)
    selMeshShapes = cmds.listRelatives(objList, shapes=True, fullPath=True, type=type)
    if selMeshShapes:  # if the selection has shapes of type
        return cmds.listRelatives((meshShapes + selMeshShapes), parent=True, fullPath=True)
    return cmds.listRelatives(meshShapes, parent=True, fullPath=True)


def selectTypeUnderHierarchy(type="mesh"):
    """Select objects of a given type as a child of the selected objects

    :param type:
    :type type:
    :return:
    :rtype:
    """
    objList = cmds.ls(selection=True)
    typeTransformList = getTypeTransformsHierarchy(objList, type=type)
    cmds.select(typeTransformList, replace=True)


def returnSelectLists(selectFlag="all", long=False):
    """Based on a selectFlag will return nodes of three types:

        1. "all" : All in scene
        2. "selected" : only selected
        3. "hierarchy" : search selected hierarchy

    TODO: Selected should include shape nodes

    :param selectFlag: "all", "selected", "hierarchy".
    :type str:
    :return returnNodeList: the nodes to be processed
    :type list:
    :return selectionWarning: True if nothing is selected and needs to be
    :type bool:
    """
    nodeList = []
    selectionWarning = False
    if selectFlag == "all":
        nodeList = cmds.ls(dag=True, long=long)  # allDagNodes
    elif selectFlag == "selected":  # selected only
        nodeList = cmds.ls(sl=True, long=long)
        if not nodeList:
            selectionWarning = True
    elif selectFlag == "hierarchy":  # all descendents children
        nodeList = cmds.ls(sl=True, long=long)
        if nodeList:
            nodeList = nodeList + cmds.listRelatives(nodeList, allDescendents=True, fullPath=True)
        else:
            selectionWarning = True
    return nodeList, selectionWarning


def selectHierarchyFilterType(nodeType='transform'):
    """Filters the select hierarchy command by a node type, usually transform type so it doesn't select the shape nodes

    :param nodeType: type of object or nde to be filtered in the selection
    :type str: any maya node type
    :return: filterList: the objs to be selected
    :type list:
    """
    cmds.select(hi=True)
    objs = cmds.ls(sl=True)
    filterList = cmds.ls(objs, type=nodeType)
    cmds.select(filterList, r=True)
    return filterList


def findParentObjList(objectList):
    """Find the parent from list world is a none type, check for it and add as None
    * no idea what this does anymore, leaving it as hotkeys may reference, old code

    :param objectList:
    :type objectList:
    :return:
    :rtype:
    """
    matchObjsParent = []
    for obj in objectList:
        matchParent = cmds.listRelatives(obj, p=1)
        if matchParent is None:
            matchObjsParent.append(None)
        else:
            matchObjsParent.append(matchParent[-1])
    return (matchObjsParent)


def getAllTansformsInWorld(long=True):
    """Returns all transforms in world, are not parented to anything

    :return rootTransforms: transform node names that are in world
    :rtype rootTransforms: list
    """
    return cmds.ls(assemblies=True, long=long)


def getTheWorldParentOfObj(objLongName):
    """Returns the bottom most object of a hierarchy given the object as a child.  (assembly)
    Will return the same object if in world

    :param objLongName: maya object dag node name, must be long name
    :type objLongName: str
    :return worldParent: the
    :rtype worldParent:
    """
    worldParent = objLongName.split('|')[1]  # take the 1 element is the first root obj
    worldParent = "|{}".format(worldParent)  # worldParent as long name
    return worldParent


def getTheWorldParentOfObjList(objLongNameList):
    worldParentList = list()
    for obj in objLongNameList:
        worldParentList.append(getTheWorldParentOfObj(obj))
    return list(set(worldParentList))


def getAllMeshTransformsInScene(longName=True):
    """Returns all meshes (poly geo) in a scene as a list

    :param longName: names will be in long format
    :type longName: bool
    :return allMeshTransforms: list of all the mesh transform names in the scene
    :rtype allMeshTransforms: list
    """
    meshShapes = cmds.ls(type='mesh')
    if meshShapes:
        return getListTransforms(meshShapes, longName=longName)


def getTransformListFromShapeNodes(shapeList, fullPath=True):
    """Given a lit of shapes find their parents (transforms)

    :param shapeList: list of shape nodes by name
    :type shapeList: list
    :param fullPath: do you want to return the fullpath name?
    :type fullPath: bool
    :return transformList: a list of transform names
    :rtype transformList: list
    """
    transformList = list()
    for shape in shapeList:
        try:
            transformList.append(cmds.listRelatives(shape, parent=True, fullPath=fullPath)[0])
        except:
            pass
    return transformList


def templateObject(obj):
    """Sets an object to be templated

    :param obj: maya object
    :type obj: str
    """
    cmds.setAttr(('{}.overrideEnabled'.format(obj)), 1)
    cmds.setAttr(('{}.overrideDisplayType'.format(obj)), 1)
    # find shapes and turn enable override off
    shapesList = cmds.listRelatives(obj, shapes=True)
    om2.MGlobal.displayInfo('Shape nodes: {}'.format(shapesList))
    for shapeNode in shapesList:
        cmds.setAttr(('{}.overrideDisplayType'.format(shapeNode)), 1)


def getParentHierachyOfObjList(sceneRootsLongName):
    """Returns the parentHierarchy of an object list (long names)
    will filter out world or empty "" returns

    :param sceneRootsLongName: a list of long names in Maya ["|group1|object", "|group1|object2"]
    :type sceneRootsLongName: list
    :return parentHierarchy: the parent hierarchy as a long name list
    :rtype parentHierarchyList: list
    """
    parentHierarchyList = list()
    for obj in sceneRootsLongName:
        hierarchyList = obj.split("|")
        del hierarchyList[-1]
        parent = "|".join(hierarchyList)
        if parent:
            parentHierarchyList.append("|".join(hierarchyList))
    return parentHierarchyList


def removePrefixLists(parentHierarchy, objectLongName):
    """From a single object and single parent hierarchy remove it if there's a prefix match

    :param parentHierarchy: the potential parent hierarchy
    :type parentHierarchy: str
    :param objectLongName: the maya object long name
    :type objectLongName: str
    :return objectLongName: the maya object long name now with the parent removed if there's a match
    :rtype objectLongName: str
    """
    if objectLongName.startswith(parentHierarchy):
        return objectLongName[len(parentHierarchy):]  # the shortened name
    return objectLongName  # name didn't change


def removeParentHierarchyObj(objectLongName, parentHierarchyList):
    """For an objectLongName remove possible parent hierarchies from the name in parentHierarchyList

    :param objectLongName: the maya object long name
    :type objectLongName: str
    :param parentHierarchy: the potential parent hierarchy
    :type parentHierarchy: str
    :return:
    :rtype:
    """
    for parentHierarchy in parentHierarchyList:
        objectLongName = removePrefixLists(parentHierarchy, objectLongName)
    return objectLongName


def removeRootParentListObj(objectLongName, sceneRootsLongName):
    """For an objectLongName remove possible parent hierarchies of sceneRootsLongName list

    :param objectLongName: the maya object long name
    :type objectLongName: str
    :param parentHierarchy: the potential parent hierarchy
    :type parentHierarchy: str
    :return:
    :rtype:
    """
    parentHierarchyList = getParentHierachyOfObjList(sceneRootsLongName)
    for parentHierarchy in parentHierarchyList:
        objectLongName = removePrefixLists(parentHierarchy, objectLongName)
    return objectLongName


def removeRootParentListObjList(objectListLongName, sceneRootsLongName):
    """Function that is useful for exporting alembic selected which export from the selected top root node
    when exported recorded objects will have incorrect long names so this will fix that and remove the
    parent hierarchies from the longnames

    :param objectList: a list of maya object long names ["|group1|object|objC", "|group1|object2|objA"]
    :type objectList: list
    :param rootsObjects: root object list long names ["|group1|object", "|group1|object2"]
    :type rootsObjects: list
    :return objectListLongName: the fixed names with roots hierarchies eliminated
    :rtype objectListLongName: list
    """
    fixObjectListLongName = objectListLongName
    parentHierarchyList = getParentHierachyOfObjList(sceneRootsLongName)
    for i, objectLongName in enumerate(objectListLongName):
        fixObjectListLongName[i] = removeParentHierarchyObj(objectLongName, parentHierarchyList)
    return fixObjectListLongName
