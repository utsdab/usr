import maya.mel as mel
import maya.api.OpenMaya as om2
from maya import cmds as cmds

from zoo.libs.maya.cmds.shaders import createshadernetwork
from zoo.libs.maya.cmds.objutils import namewildcards, namehandling, filtertypes, selection
from zoo.libs.maya.cmds.renderer.rendererconstants import RENDERER_SUFFIX_DICT

SGKEY = "ShadingGroup"
ASSIGNKEY = "assigned"


def getShaderFromSG(shadingGroup):
    """Returns the main shader from a shading group, this assumes only one shader is related to the shadering group
    This will have to ignore extra shaders deeper in the node network if there are many nested/layered shaders

    :param shadingGroup: The name of the shading group
    :type shadingGroup: str
    :return shader: the shader name
    :rtype shader: str
    """
    connections = cmds.listConnections(shadingGroup, source=True, destination=False)
    shaders = cmds.ls(connections, materials=True)
    if shaders:
        return shaders[0]
    return ""


def getShadersFromSGList(shadingGroupSet):
    """Returns a list of shaders from a set of shading groups

    :param shadingGroupSet: set of shading group names
    :type shadingGroupSet: set
    :return shaderList:
    :rtype shaderList:
    """
    shaderList = list()
    for shadingGroup in shadingGroupSet:
        shaderList.append(getShaderFromSG(shadingGroup))
    return shaderList


def getShadingGroupFromShader(shader):
    """Returns the Shading Group from a shader

    :param shader: the shader name
    :type shader: string
    :return shadingGroup: the shading group node (can easily be None if not assigned)
    :rtype shadingGroup: str
    """
    connectedNodes = cmds.listConnections(shader, source=False, destination=True)
    for node in connectedNodes:
        if cmds.ls(node, type="shadingEngine"):
            if node == "initialParticleSE":  # hardcoded for lambert1 which has two shading groups, ignore particlesSG
                return "initialShadingGroup"
            return node
    return ""


def getShadingGroupFromShaderList(shaderList):
    shadingGroupList = list()
    for shader in shaderList:
        shadingGroupList.append(getShadingGroupFromShader(shader))
    return shadingGroupList


def getShadingGroupsFromObj(mayaObj):
    """Returns all the Shading Groups related to a mesh or nurbsSurface object

    :param mayaObj: A transform or shape node that is or has a "mesh" or "nurbsSurface" node
    :type mayaObj: str
    :return shadingGroupList: list of shading group names
    :rtype shadingGroupList: list
    """
    # if mesh transform or shape ------------------------------
    meshList = filtertypes.filterTypeReturnTransforms([mayaObj], shapeType="mesh")
    if meshList or cmds.objectType(mayaObj) == "mesh":
        # must search on faces, shape nodes is not enough
        faces = cmds.polyListComponentConversion(mayaObj, tf=True)
        if not faces:
            return None
        return cmds.listSets(object=faces[0], type=1)
    # if nurbsSurface transform or shape ------------------------------
    nurbsSurfaceList = filtertypes.filterTypeReturnTransforms([mayaObj], shapeType="nurbsSurface")
    if nurbsSurfaceList or cmds.objectType(mayaObj) == "nurbsSurface":
        if cmds.objectType(mayaObj) == "transform":  # get it's nurbs shape node
            nurbsShape = cmds.listRelatives(mayaObj, shapes=True, fullPath=True, type="nurbsSurface")[0]
        else:
            nurbsShape = mayaObj
        return cmds.listSets(object=nurbsShape, type=1)  # returns the shading group as a list


def getShadingGroupsObjList(objList):
    """Returns all the Shading Groups related to an object list

    :param objList: list of Maya Object names
    :type objList: list
    :return shadingGroupList: list of shading group names
    :rtype shadingGroupList: list
    """
    shadingGroupList = list()
    for obj in objList:
        newShadingGroupList = getShadingGroupsFromObj(obj)
        if newShadingGroupList:
            shadingGroupList += newShadingGroupList
    list(set(shadingGroupList))  # make unique list
    return shadingGroupList


def getShadingGroupsSelected(reportMessage=True):
    """From selection return all related shading groups as a list

    This function only works on meshes, not all nodes, see later function
    *** Should be cleaned up at some stage ****
    *** Doubled up confusing functionality ****

    :param reportMessage: report the message back to the user?
    :type reportMessage: bool
    :return shadingGroupList: list of shading group names
    :rtype shadingGroupList: list
    """
    objList = cmds.ls(selection=True, long=True)
    if not objList:
        om2.MGlobal.displayWarning('No Objects Select, Please Select')
        return list()
    shadingGroupList = getShadingGroupsObjList(objList)
    if not shadingGroupList:
        om2.MGlobal.displayWarning('No Shading Groups Found From Selection')
        return list()
    return shadingGroupList


def getShadersObjList(objList):
    """Gets a list of shader names related to a object list

    :param objList: List of Maya Objects as strings
    :type objList: list
    :return shaderList:
    :rtype shaderList: list
    """
    shadingGroupList = getShadingGroupsObjList(objList)
    return getShadersFromSGList(shadingGroupList)


def getShadersSelected(reportMessage=True):
    """From selection return all related shaders as a list

    :param reportMessage: report the message back to the user?
    :type reportMessage: bool
    :return shaderList: A list of shader names
    :rtype shaderList: list
    """
    objList = cmds.ls(selection=True, long=True)
    if not objList:
        if reportMessage:
            om2.MGlobal.displayWarning('No objects selected, please select and object, shader or shading group')
        return
    shadingGroupList = getShadingGroupsObjList(objList)
    if not shadingGroupList:
        if reportMessage:
            om2.MGlobal.displayWarning('No shaders found in the current selection')
        return
    return list(set(getShadersFromSGList(shadingGroupList)))  # remove duplicates


def getShaderWildcard(wildcardName):
    """Finds all shaders in a scene with the given suffix

    :param wildcardName: The suffix name
    :type wildcardName: str
    :return shaderList: the shaders
    :rtype shaderList: list
    """
    shaderList = namewildcards.getWildcardObjs(wildcardName)  # find all nodes with suffix
    return cmds.ls(shaderList, materials=True)  # check legitimate shaders filtering out other nodes


def getShadersShadeNode(shapeNode):
    """Get the related shaders connected to the given shapeNode

    :param shapeNode: name of the shape node
    :type shapeNode: str
    :return shaderList: the shader names
    :rtype shaderList: list
    """
    if not shapeNode:
        return list()
    shadingGrps = cmds.listConnections(shapeNode, type='shadingEngine')
    if not shadingGrps:
        return list()
    shaderList = cmds.ls(cmds.listConnections(shadingGrps), materials=1)
    return shaderList


def getShadersShapeNodeList(shapeNodeList):
    """Returns the shaders attached to a list of shape nodes

    :param shapeNodeList: list of shape node names
    :type shapeNodeList: str
    :return shaderList: the shader names
    :rtype shaderList: list
    """
    shaderList = list()
    for shapeNode in shapeNodeList:
        shaderList += getShadersShadeNode(shapeNode)
    return shaderList


def shaderAndAssignmentsFromObj(objTransform, message=True):
    """Returns a shader list and a selection list from the selected mesh object, can included face selection.

    Assumes the transform only has one mesh shape node.
    Used in transferShaderTopology()

    Example 1 return:
        ["redShadingGroup"]
        [["|pSphere3"]]

    Example 2 return:
        ["redShadingGroup", "blueShadingGroup]
        [["|pSphere3.f[0:47]", "|pSphere3.f[101:222]"], ["|pSphere3.f[48:100]", "|pSphere3.f[223:228]"]]

    :param objTransform: Maya transform node name should have a mesh shape nodes as children (ie a mesh object)
    :type objTransform: str
    :param message: Return messages to the user om2.MGlobal
    :type message: bool
    :return shadingGroupList: List of shading groups assigned to the object, can be multiple if face assigned
    :rtype shadingGroupList: list(str)
    :return objectsFacesList: List of shader assignments to this object, can be face assigned, see function description
    :rtype objectsFacesList: list(list(str))
    """
    objTransformDot = "{}.".format(objTransform)  # add a fullstop for use later
    objTransformShape = cmds.listRelatives(shapes=True, fullPath=True, type="mesh")  # get shape for use later
    if not objTransformShape:
        if message:
            om2.MGlobal.displayWarning('The object `{}` does not have a mesh shape node'.format(objTransform))
        return
    objTransformShape = objTransformShape[0]  # the shape node
    objectsFacesList = list()
    shadingGroupList = getShadingGroupsFromObj(objTransform)
    if not shadingGroupList:
        if message:
            om2.MGlobal.displayWarning('The object `{}` does not have any shading groups assigned'.format(objTransform))
        return
    for i, shadingGroup in enumerate(shadingGroupList):
        assignList = getObjectsFacesAssignedToSG(shadingGroup, longName=True)  # will return all objs face in scene
        objAssignment = list()
        for assignment in assignList:  # restrict the objs and faces to the objTransform
            # if the assignment contains the name of the target object then keep it, lose all others
            if objTransformDot in assignment:  # if face assignment will match to name with fullstop "|pCube."
                objAssignment.append(assignment)
            elif objTransformShape == assignment:  # if not face assign assignment then will match to shape node name
                objAssignment.append(assignment)
                break  # if this has been triggered, no face assignments, only one will be in the list
        objectsFacesList.append(objAssignment)
    return shadingGroupList, objectsFacesList


def transferShaderTopology(sourceObject, targetObject, ignoreTopologyMismatch=True, message=True):
    """Transfers shader/s from one object to another with matching topology, handles face assignment

    Copies the shaders from the source object and copies them onto the target object

    Objects must be transforms and can have "mesh" or "nurbsSurface" shapes
    TODO: Nurbs does not support multiple shaders yet

    :param sourceObject: The source object name to copy the shader info from, should be a long name
    :type sourceObject: str
    :param targetObject: The target object name to copy the shader info onto, should be a long name
    :type targetObject: str
    :param ignoreTopologyMismatch: Ignores the topology difference and copies the first shader found
    :type ignoreTopologyMismatch: bool
    :param message: Return messages to the user om2.MGlobal
    :type message: bool
    :return success: True if the transfer succeeded via matching topology False if not
    :rtype success: bool
    """
    # Mesh --------------------------------------------------
    meshObjs = filtertypes.filterTypeReturnTransforms([sourceObject, targetObject], shapeType="mesh")
    if len(meshObjs) == 2:
        if cmds.polyCompare(sourceObject, targetObject, faceDesc=True):  # returns 0 if the faces are a topology match
            if message:
                om2.MGlobal.displayWarning('The topology of both objects does not match')
                # topology has probably changed so assign the first shader found from the skinned mesh
            if ignoreTopologyMismatch:  # assign the first shader found
                shadingGroups = getShadingGroupsFromObj(sourceObject)
                if shadingGroups:
                    assignShadingGroup([targetObject], shadingGroups[0])
                if message:
                    om2.MGlobal.displayInfo("The topology has probably changed between the skinned and orig. "
                                            "Transferring first shader found")
            return False
        # is a match so continue
        shadingGroupList, objectsFacesList = shaderAndAssignmentsFromObj(sourceObject)
        if len(shadingGroupList) == 1:  # maya weirdness, if no face assign replace the shape node names not transform
            sourceObject = cmds.listRelatives(sourceObject, shapes=True, fullPath=True, type="mesh")[0]
        for i, assignmentList in enumerate(objectsFacesList):
            for x, assignment in enumerate(assignmentList):
                objectsFacesList[i][x] = assignment.replace(sourceObject, targetObject)  # swap the assignment to target
        for i, shadingGroup in enumerate(shadingGroupList):  # do the shader assign
            assignShadingGroup(objectsFacesList[i], shadingGroup)
        return True
    # NurbsSurface --------------------------------------------------
    nurbsObjs = filtertypes.filterTypeReturnTransforms([sourceObject, targetObject], shapeType="nurbsSurface")
    if len(nurbsObjs) == 2:
        # TODO currently only supports one shader assignment
        shadingGroup = getShadingGroupsFromObj(sourceObject)[0]  # only one shader on nurbsSurfaces
        for targetObj in nurbsObjs:  # do the transfer
            nurbsShapeList = cmds.listRelatives(targetObj, shapes=True, fullPath=True, type="nurbsSurface")
            assignShadingGroup(nurbsShapeList, shadingGroup)
        return True
    # Other ------------------------------------------------------------------
    if message:
        om2.MGlobal.displayWarning('The objects are not both "nurbsSurfaces" or both "polygon meshes"')
    return False


def transferShaderTopologySelected(message=True):
    """Transfers shader/s from one object to another with matching topology, handles face assignment

    The first object in the selection's shader/s are copied to all other selected objects

    Objects must be transforms and can have "mesh" or "nurbsSurface" shapes
    TODO: Nurbs does not support multiple shaders yet

    :param message: Return messages to the user om2.MGlobal
    :type message: bool
    """
    selObjs = cmds.ls(selection=True, long=True, type="transform")
    if len(selObjs) < 2:
        if message:
            om2.MGlobal.displayWarning("Please select two or more mesh, or nurbsSurface objects.")
    sourceObj = selObjs.pop(0)  # the source obj is the first selected object and remove from selObj list
    for targetObj in selObjs:  # do the transfer
        transferShaderTopology(sourceObj, targetObj, message=message)


def getAllShadersAndObjectFaceAssigns(filterOnlyUsed=False, filterShaderType=None):
    """Gets all shaders, shading groups and their face assignments in the scene
    if filterOnlyUsed then return only those with scene assignments, ie not unused shaders

    :param filterOnlyUsed: only return used shaders, shaders that contain assignments, obj or face etc
    :type filterOnlyUsed: bool
    :return shaderList: list of shader names
    :rtype shaderList: list
    :return shadingGroupList: list of shading group names
    :rtype shadingGroupList: list
    :return objFaceList: list of face/obj assignements
    :rtype objFaceList: list
    """
    shadersAllList = getAllShaders()
    shaderAssignmentDict = dict()
    deleteShaderList = list()
    for shader in shadersAllList:
        shaderAssignmentDict[shader] = dict()
        if shader == "particleCloud1":  # ignore the primary particleCloud1
            shaderAssignmentDict[shader][SGKEY] = "initialParticleSE"
            shaderAssignmentDict[shader][ASSIGNKEY] = getObjectsFacesAssignedToSG("initialParticleSE")
            continue
        shadingGroup = getShadingGroupFromShader(shader)
        shaderAssignmentDict[shader][SGKEY] = shadingGroup
        shaderAssignmentDict[shader][ASSIGNKEY] = getObjectsFacesAssignedToSG(shadingGroup)
    if filterOnlyUsed:
        for shaderName in shaderAssignmentDict:
            if shaderAssignmentDict[shaderName][ASSIGNKEY] is None:  # record index to remove
                deleteShaderList.append(shaderName)  # shader to delete from dict
    if filterShaderType:
        for shaderName in shaderAssignmentDict:
            nodeType = cmds.objectType(shaderName)
            if filterShaderType != nodeType:
                deleteShaderList.append(shaderName)  # shader to delete from
    deleteShaderList = list(set(deleteShaderList))  # no duplicates
    for shader in deleteShaderList:
        shaderAssignmentDict.pop(shader, None)
    return shaderAssignmentDict


def getAllShaders():
    """return all shaders types that could be created in a scene

    :return shaderList: list of shader names
    :rtype shaderList: list
    """
    return cmds.ls(materials=True)


def getObjectsFacesAssignedToSG(shadingGroup, longName=True):
    """gets objects and faces of the given shading group

    :param shadingGroup: the shading group name
    :type shadingGroup: str
    :param longName: return all longnames, will return only clashing nodes as long if false
    :type longName: str
    :return objectFaceList: list of objects and faces as names with [1:233]
    :rtype objectFaceList: list
    """
    objectFaceList = cmds.sets(shadingGroup, query=True)
    if longName and objectFaceList:
        objectFaceList = namehandling.getLongNameList(objectFaceList)
    return objectFaceList


def getObjectsFacesAssignedToShader(shader, longName=True):
    """gets objects and faces of the given shader

    :param shader: the shader name
    :type shader: str
    :return objectFaceList: list of objects and faces as names with [1:233]
    :rtype objectFaceList: list
    """
    shadingGroup = getShadingGroupFromShader(shader)
    objectFaceList = getObjectsFacesAssignedToSG(shadingGroup, longName=True)
    return objectFaceList


def assignShadingGroup(objFaceList, shadingGroup):
    """Assigns the shader to an object/face list

    :param objFaceList: list of objects and faces for the assignment
    :type objFaceList: list
    :param shadingGroup: the shading group name to assign
    :type shadingGroup: str
    :return shadingGroup: the shading group name assigned
    :rtype shadingGroup: str
    """
    for objFace in objFaceList:
        cmds.sets(objFace, e=True, forceElement=shadingGroup)
    return shadingGroup


def assignShader(objFaceList, shader):
    """Assigns the shader to an object/face list

    :param objFaceList: list of objects and faces for the assignment
    :type objFaceList: list
    :param shader: the shader name to assign
    :type shader: str
    :return shadingGroup: the shading group name assigned
    :rtype shadingGroup: str
    """
    shadingGroup = getShadingGroupFromShader(shader)
    if not shadingGroup:  # create one
        shadingGroup = createshadernetwork.createSGOnShader(shader)
    return assignShadingGroup(objFaceList, shadingGroup)


def assignShaderCheck(objFaceList, shader):
    """Assigns the shader to an object/face list, checks to see if the object exists before assigning

    :param objFaceList: list of objects and faces for the assignment
    :type objFaceList: list
    :param shader: the shader name to assign
    :type shader: str
    """
    shadingGroup = getShadingGroupFromShader(shader)
    if not shadingGroup:  # create one
        shadingGroup = createshadernetwork.createSGOnShader(shader)
    for objFace in objFaceList:  # gets the shader assignment list
        if ".f" in objFace:  # could be a face selection so split to get object
            object = objFace.split(".f")[0]
        else:
            object = objFace
        if cmds.objExists(object):  # assign the shader
            cmds.sets(objFace, e=True, forceElement=shadingGroup)


def assignShaderSelected(shader):
    """Assigns the given shader to current selection

    :param shader: The shader name
    :type shader: str
    """
    cmds.hyperShade(assign=shader)


def getShadingGroupsFromNodes(nodeList):
    """Finds shaders assigned to current node list,
    Includes shape nodes, transforms, shaders and shadingGroups (will return themselves)

    :param nodeList: list of maya node names, can be any nodes
    :type nodeList: list
    :return shadingGroupList: List of shading group names associated with the given nodes
    :rtype shadingGroupList: list
    """
    shadingGroupList = list()
    meshShadingGroups = list()
    # check if nodes are shading groups themselves
    for node in nodeList:
        if "." not in node:  # could be a component, if "." then skip
            if cmds.objectType(node) == "shadingEngine":
                shadingGroupList.append(node)
    # check shaders and shapes for connecting Shading Groups and add to main list
    shadingGroupShaderList = cmds.listConnections(nodeList, type='shadingEngine')
    if shadingGroupShaderList:
        shadingGroupList = list(set(shadingGroupList + shadingGroupShaderList))
    # check for shaders on shape or transform nodes, this also checks faces too, add to main list
    for node in nodeList:
        shaderList = getShadingGroupsFromObj(node)
        if shaderList:
            meshShadingGroups += shaderList
    if meshShadingGroups:
        shadingGroupList = list(set(shadingGroupList + meshShadingGroups))
    return shadingGroupList


def getShadingGroupsFromSelectedNodes():
    """finds shaders assigned to current selection of nodes
    This includes shape nodes, transforms, shaders and shadingGroups (will return themselves)

    :return shadingGroupList: List of shading group names associated with the given nodes
    :rtype shadingGroupList: list
    """
    selObj = cmds.ls(selection=True, long=True)
    return getShadingGroupsFromNodes(selObj)


def getShadersFromNodes(nodeList):
    """Will return a shader list from given nodes,
    This includes shape nodes, transforms, shaders (will return themselves) and shadingGroups

    :param nodeList: list of maya node names, can be any nodes
    :type nodeList: list
    :return shaderList: List of Shader Names associated with the nodeList
    :rtype shaderList: list
    """
    shadingGroupList = getShadingGroupsFromNodes(nodeList)
    shaderList = getShadersFromSGList(set(shadingGroupList))
    return shaderList


def getShadersFromSelectedNodes(allDescendents=False, reportSelError=False):
    """Will return a shader list from given selection of nodes,
    This includes shape nodes, transforms, shaders (will return themselves) and shadingGroups
    Also can retrieve shaders on all descendents of the selected objects

    :param allDescendents: will include allDescendants of the selection, children and grandchildren etc
    :type allDescendents: bool
    :param reportSelError: Report selection issues to the user
    :type reportSelError: bool
    :return shaderList: List of Shader Names associated with the selected nodeList
    :rtype shaderList: list
    """
    allChildren = list()
    shaderRetrieveObjs = cmds.ls(selection=True, long=True)
    if not shaderRetrieveObjs:
        if reportSelError:
            om2.MGlobal.displayWarning('Nothing Selected Please Select Node/s')
        return
    if allDescendents:
        for obj in shaderRetrieveObjs:
            allChildren += cmds.listRelatives(obj, allDescendents=True, shapes=False, fullPath=True)
        shaderRetrieveObjs = list(set(shaderRetrieveObjs + allChildren))
    shaderList = getShadersFromNodes(shaderRetrieveObjs)
    return shaderList


def selectMeshFaceFromShaderName(shaderName):
    """Selects objects and faces assigned from a shader

    :param shaderName: The name of a Maya shader
    :type shaderName: list
    """
    if not cmds.objExists(shaderName):
        return
    cmds.select(shaderName)
    cmds.hyperShade(shaderName, objects="")  # Select function


def getMeshFaceFromShaderNodes(nodeList, selectMesh=True, objectsOnly=False):
    """Will return a mesh shape node list from given nodeList,
    This includes shape nodes, transforms, shaders (will return themselves) and shadingGroups

    :param nodeList: list of maya node names, can be any nodes
    :type nodeList: list
    :param selectMesh: Select the returned meshes and potential faces?
    :type selectMesh: bool
    :param objectsOnly: Only return (and potentially select) meshes, not faces
    :type objectsOnly: bool
    :return meshList: List of mesh node names, not transforms
    :rtype meshList: list
    """
    if not selectMesh:
        selObj = cmds.ls(selection=True, long=True)
    # get all related shaders from node selection
    shaderList = getShadersFromNodes(nodeList)
    objFaceList = list()
    if shaderList:
        for shader in shaderList:
            cmds.select(shader, replace=True)
            cmds.hyperShade(shader, objects="")
            objFaceList += cmds.ls(selection=True, long=True)
    om2.MGlobal.displayInfo('selected: '.format(objFaceList))
    if objectsOnly:  # return only shape nodes and not potential face selection
        for i, objFace in enumerate(objFaceList):
            if ".f[" in objFace:  # save only the object names not face list
                objFaceList[i] = objFace.split('.f[')[0]
    objFaceList = list(set(objFaceList))  # make unique list
    if not selectMesh:
        cmds.select(selObj, replace=True)
    else:
        cmds.select(objFaceList, replace=True)
    return objFaceList


def getMeshFaceFromShaderSelection(selectMesh=True, objectsOnly=False):
    """Will return a mesh (shape) node list from given selection of nodes,
    This includes shape nodes, transforms, shaders (will return themselves) and shadingGroups

    :param selectMesh: Select the returned meshes and potential faces?
    :type selectMesh: bool
    :param objectsOnly: Only return and potentially select meshes, not faces
    :type objectsOnly: bool
    :return meshFaceList: List of mesh node names, and potentially face names, not transforms
    :rtype meshFaceList: list
    """
    selObj = cmds.ls(selection=True, long=True)
    if not selObj:
        om2.MGlobal.displayWarning('Nothing Selected Please Select Node/s')
        return
    objFaceList = getMeshFaceFromShaderNodes(selObj, selectMesh=selectMesh, objectsOnly=objectsOnly)
    return objFaceList


def transferAssign(objFaceList):
    """from a list take the first objects shader (it can be a shader or shading group too) and assign it to the
    remaining list objects

    :param objFaceList: list of maya objects and or face selection
    :type objFaceList: list
    """
    # get first selection, and remove it from the list
    fromObj = objFaceList[0]
    del objFaceList[0]
    fromObjList = [fromObj]
    fromShader = (getShadersFromNodes(fromObjList))[0]  # get fromShader, this is the first shader it finds
    assignShader(objFaceList, fromShader)  # assign shader to remaining selection


def transferAssignSelection(message=True):
    """from a selection take the first object's shader (it can be a shader or shading group itself too) and assign it
    to the remaining list objects, this is like copy shader from an object to objects

    :param message: report warnings to the user
    :type message: bool
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        return False
    geoFaceList = selection.convertGeometryFaces(selObjs, individualFaces=True)
    if len(geoFaceList) < 2:
        om2.MGlobal.displayWarning("Transfer requires at least two geometry or polygon faces selected")
        return False
    transferAssign(geoFaceList)
    return True


def removeShaderSuffix(shaderName):
    """Removes the shader suffix from a shader name, will remove all shader suffix names for any renderer

    Will remove suffix for all renderers

    :param shaderName: the Maya shader name
    :type shaderName: str
    :return shaderName:  the Maya shader name now with suffix removed
    :rtype shaderName: str
    """
    suffix = shaderName.split('_')[-1]
    for key in RENDERER_SUFFIX_DICT:
        if RENDERER_SUFFIX_DICT[key] == suffix:
            shaderName = shaderName.replace("_{}".format(suffix), "")
    return shaderName


def removeShaderSuffixRenderer(shaderName, renderer):
    """Removes the shader suffix from a shader name, will remove all shader suffix names for any renderer

    Will remove on for the given renderer.

    :param shaderName: A Maya shader name
    :type shaderName: str
    :return shaderName:  the Maya shader name now with suffix removed
    :rtype shaderName: str
    """
    suffix = shaderName.split('_')[-1]
    if RENDERER_SUFFIX_DICT[renderer] == suffix:
        shaderName = shaderName.replace("_{}".format(suffix), "")
    return shaderName


def removeShaderSuffixList(shaderNameList, renderer):
    """

    :param shaderNameList: List of shader names
    :type shaderNameList: list(str)
    :param renderer: A renderer nicename
    :type renderer: str
    :return shaderRenamedList: Shader list now renamed
    :rtype shaderRenamedList:
    """
    shaderRenamedList = list()
    for shader in shaderNameList:
        shaderRenamedList.append(removeShaderSuffix(shader, renderer))
    return shaderRenamedList


def getShaderNameFromNode(node, removeSuffix=False):
    """from the given node return the shader name that's attached to it
    can remove the suffix if it's in the dict rendererManage.ALLRENDERERSUFFIX

    :param node: any maya node, should be shader related but is ok if not, will just fail to find a shader
    :type node: str
    :param removeSuffix: removes the suffix name if it's in the rendererManage.ALLRENDERERSUFFIX dict
    :type removeSuffix: bool
    :return shaderName: the shader name
    :rtype shaderName: str
    """
    shaderName = getShadersFromNodes([node])[0]
    if removeSuffix:
        shaderName = removeShaderSuffix(shaderName)
    return shaderName


def getShaderNameFromNodeSelected(removeSuffix=False):
    """from the first selected object return the shader name that's attached to it
    can remove the suffix if it's in the dict rendererManage.ALLRENDERERSUFFIX

    :param removeSuffix: removes the suffix name if it's in the rendererManage.ALLRENDERERSUFFIX dict
    :type removeSuffix: bool
    :return shaderName: the shader name
    :rtype shaderName: str
    """
    selbObj = cmds.ls(selection=True, long=True)[0]
    shaderName = getShaderNameFromNode(selbObj, removeSuffix=removeSuffix)
    return shaderName


def connectSurfaceShaderToViewportShader(surfaceShader, viewportShadingGroup, renderer, connectedCount=0):
    """Connects the surface shader (usually the renderer shader) to the viewport shaders shading group
    Usually via the surface attribute.
    Useful while rendering in an engine whilst having the shaders looking nice in the viewport.
    This is a single shader setup

    :param surfaceShader:  the renderers shader to be connected to the viewport shaders shading group
    :type surfaceShader: str
    :param viewportShadingGroup: the viewport shaders shading group name
    :type viewportShadingGroup: str
    :param connectedCount: useful for looping and messaging, usually used by another function for counting connections
    :type connectedCount: int
    :param renderer: which renderer are you using "redshift", "arnold", "vray", mentalRay", "renderman".  Only Redshift is supported
    :type renderer: str
    :return connectedCount:  Was the connection made, if so return this number as a +1
    :rtype connectedCount: int
    """
    if renderer == "redshift":
        try:
            cmds.connectAttr("{}.outColor".format(surfaceShader), "{}.rsSurfaceShader".format(viewportShadingGroup))
            connectedCount += 1
        except RuntimeError:
            om2.MGlobal.displayWarning(
                'The Shading Group `{}` is probably already connected. Skipping.'.format(viewportShadingGroup))
    elif renderer == "arnold":
        try:
            cmds.connectAttr("{}.outColor".format(surfaceShader), "{}.aiSurfaceShader".format(viewportShadingGroup))
            connectedCount += 1
        except RuntimeError:
            om2.MGlobal.displayWarning(
                'The Shading Group `{}` is probably already connected. Skipping.'.format(viewportShadingGroup))
    elif renderer == "mentalRay":
        pass
    elif renderer == "vRay":
        pass
    elif renderer == "renderman":
        pass
    return connectedCount


def assignSurfaceShaderWildcard(surfaceSuffix="RS", viewportSuffix="VP2", renderer="redshift"):
    """Connects the surface shader (usually the renderer shader) to the viewport shader via the surface attribute.
    Useful while rendering in an engine whilst having the shaders looking nice in the viewport.
    works off matching suffix shader names eg skin_RS => skin_VP2's shading group
    To Do
    1. checks if the shader is already connected, if not disconnects the current connection and reconnects
    2. disconnect

    :param surfaceSuffix: The user defined suffix of the renderer shader
    :type surfaceSuffix: str
    :param viewportSuffix: The user defined suffix of the viewport shader
    :type viewportSuffix: str
    :param renderer: which renderer are you using "redshift", "arnold", "vray", mentalRay", "renderman".  Only Redshift is supported
    :type renderer: str
    """
    connectedCount = 0
    surfaceShaderList = getShaderWildcard(surfaceSuffix)  # find all potential surface shaders
    if not surfaceShaderList:
        om2.MGlobal.displayWarning('No Surface Shaders Found With Suffix `{}`'.format(surfaceSuffix))
        return
    for surfaceShader in surfaceShaderList:
        viewportShader = surfaceShader.replace(surfaceSuffix, viewportSuffix)
        if cmds.objExists(viewportShader):  # do the connection
            viewportShadingGroup = getShadingGroupFromShader(viewportShader)  # get the shading group
            if not viewportShadingGroup:
                om2.MGlobal.displayWarning('The Shader `{}` has no Shading Group Skipping'.format(viewportShader))
            # Main function
            connectedCount = connectSurfaceShaderToViewportShader(surfaceShader, viewportShadingGroup, renderer,
                                                                  connectedCount=connectedCount)
    if not connectedCount:
        om2.MGlobal.displayWarning('No Shaders Connected')
        return
    om2.MGlobal.displayInfo('Success: {} Shaders Connected'.format(connectedCount))


def deleteShaderNetwork(shaderName):
    """deletes the shader network of a shader

    :param shaderName: the name of the shader
    :type shaderName: str
    :return shaderNodes: all nodes deleted
    :rtype shaderNodes: list
    """
    shaderNodes = cmds.hyperShade(listUpstreamNodes=shaderName)
    shadingGroup = getShadingGroupFromShader(shaderName)
    shaderNodes = shaderNodes + [shaderName, shadingGroup]
    for node in shaderNodes:
        if cmds.objExists(node):
            cmds.delete(node)
    return shaderNodes


def deleteShaderNetworkList(shaderList):
    """Deletes the shading network of a shading node

    :param shaderList: a list of maya shader names
    :type shaderList: list
    :return shaderNodeDeletedList:
    :rtype shaderNodeDeletedList:
    """
    shaderNodeDeletedList = list()
    for shader in shaderList:
        shaderNodesDeleted = deleteShaderNetwork(shader)
        shaderNodeDeletedList += shaderNodesDeleted
    return shaderNodeDeletedList


"""
SELECTION MACROS
"""


def selectNodeOrShaderAttrEditor():
    """This script selects the shader or the selected nodes:

        1. Selects the node if selected in the channel box and opens the attribute editor
        2. Or if a transform node is selected, select the shaders of the current selection and open attr editor

    :return selectedReturn: A list of the currently selected objects
    :rtype selectedReturn: list
    """
    selectedObjs = cmds.ls(selection=True, long=True)
    if not selectedObjs:
        return
    firstObj = selectedObjs[0]
    if cmds.objectType(firstObj, isType='transform'):  # then select the shader of this object
        shaderList = getShadersSelected()
        if shaderList:
            cmds.select(shaderList, replace=True)
            mel.eval('openAEWindow')  # attribute editor
            return shaderList
    else:  # select the current node and open attr editor
        cmds.select(firstObj, replace=True)
        mel.eval('openAEWindow')
        selectedReturn = [firstObj]
        return selectedReturn
    return selectedObjs