"""Functions for skin binding

Examples
# bindskin hierarchy (closest distance)
from zoo.libs.maya.cmds.skin import bindSkin
bindSkin.bindSkinSelected(toSelectedBones=False, maximumInfluences=5, maxEditLimit=5, bindMethod=0, displayMessage=True)

# bindskin selected (closest distance)
from zoo.libs.maya.cmds.skin import bindSkin
bindSkin.bindSkinSelected(toSelectedBones=True, maximumInfluences=5, maxEditLimit=5, bindMethod=0, displayMessage=True)

# bindskin selected rigid bind (closest distance)
from zoo.libs.maya.cmds.skin import bindSkin
bindSkin.bindSkinSelected(toSelectedBones=True, maximumInfluences=0, maxEditLimit=5, bindMethod=0, displayMessage=True)

# bind skin heat map
from zoo.libs.maya.cmds.skin import bindSkin
bindSkin.bindSkinSelected(bindMethod=2)

#bind skin geodesic
from zoo.libs.maya.cmds.skin import bindSkin
bindSkin.bindSkinSelected(bindMethod=3)

# mirror x to -x
from zoo.libs.maya.cmds.skin import bindSkin
bindSkin.mirrorSkinSelection(mirrorMode='YZ', mirrorInverse=False)

# mirror -x to x
from zoo.libs.maya.cmds.skin import bindSkin
bindSkin.mirrorSkinSelection(mirrorMode='YZ', mirrorInverse=True)

# remove influence
from zoo.libs.maya.cmds.skin import bindSkin
bindSkin.removeInfluenceSelected()

# transfer skin weights zoo
from zoo.libs.maya.cmds.skin import bindSkin
bindSkin.transferSkinWeightsSelected()

# add joints to skin cluster
from zoo.libs.maya.cmds.skin import bindSkin
bindSkin.addJointsToSkinnedSelected()

# unbind skin
from zoo.libs.maya.cmds.skin import bindSkin
bindSkin.unbindSkinSelected()

# duplicate mesh before bind - orig shape duplicate
from zoo.libs.maya.cmds.skin import bindSkin
bindSkin.duplicateSelectedBeforeBind()

# change skin method to weight belnded (dual quat)
from zoo.libs.maya.cmds.skin import bindSkin
bindSkin.skinClusterMethodSwitch(skinningMethod=2, displayMessage=True)
"""

import maya.cmds as cmds
import maya.api.OpenMaya as om2
import maya.mel as mel

from zoo.libs.maya.cmds.objutils import shapenodes, namehandling, attributes
from zoo.libs.utils import zlogging
from zoo.libs.maya.cmds.shaders import shaderutils

logger = zlogging.getLogger(__name__)


def getAllSkinClusters(displayMessage=False):
    """Returns all valid skin clusters in a scene

    :param displayMessage:  Report the message inside of maya?
    :type displayMessage: bool
    :return skinClusterList: List of the skin cluster node names
    :rtype skinClusterList: list
    """
    skinClusterList = cmds.ls(type='skinCluster')  # get all skin clusters in scene
    if not skinClusterList:
        if displayMessage:
            om2.MGlobal.displayWarning("No skinClusters Exist In The Scene")
        return
    return skinClusterList


def checkValidOrigShape(mesh, deleteDeadShapes=False, displayMessage=False):
    """Checks for valid orig shape nodes, by checking if multiple orig shapes are present
    or that the object isn't skinned or has no orig shape nodes
    returns the the orig shape node name or None on fail

    :param mesh: the object name to check
    :type mesh: str
    :param displayMessage: Report the message inside of maya?
    :type displayMessage: bool
    :return originalShape: The original shape node returned
    :rtype: str
    """
    mshShortName = namehandling.getUniqueShortName(mesh)
    originalShapeList = shapenodes.getOrigShapeNodes(mesh, fullPath=True)
    if not originalShapeList:
        if not getSkinCluster(mesh):
            om2.MGlobal.displayWarning("There's no skin cluster on this object `{}`, must have "
                                       "skinning/deformation".format(mshShortName))
            return
        om2.MGlobal.displayWarning("This object `{}` is missing an original shape node it should have one,"
                                   " best to rebuild the skinning".format(mshShortName))
        return
    for i, shape in reversed(list(enumerate(originalShapeList))):  # tests for legit nodes from outgoing connections
        outputs = cmds.listConnections(shape, destination=True, source=False)
        if not outputs:
            if deleteDeadShapes:  # do Maya delete on this as it's most likely a dead origShape and worthless
                cmds.delete(originalShapeList[i])
                if displayMessage:
                    currentOriginalShape = namehandling.getUniqueShortName(originalShapeList[i])
                    om2.MGlobal.displayInfo("Dead Original Mesh Deleted: {}".format(currentOriginalShape))
            # remove from list
            del originalShapeList[i]
    if len(originalShapeList) > 1:  # Rare cases more than one live intermediate object is found, like a UvProjection
        for orig in originalShapeList:  # Remove the end numbers and search if endsWith "Orig"
            origNumberlessEnd = ''.join([i for i in orig if not i.isdigit()])  # strip all numbers
            if origNumberlessEnd.endswith("Orig"):
                originalShapeList = [orig]  # Name found so break
                break
    if len(originalShapeList) < 1:  # This test shouldn't occur, if so very rare
        om2.MGlobal.displayWarning("There's more than one legitimate Original Shape Node on object `{}`. A fix is to "
                                   "save skin weights, unbind the skin and obj clean the object, re import"
                                   " skin. Can also be planarProjection or another issue.".format(mshShortName))
        return originalShapeList[0]
    # else tests passed
    return originalShapeList[0]


def checkValidOrigShapeList(meshList, deleteDeadShapes=False, displayMessage=False):
    """List version of the function checkValidOrigShape

    :param meshList: list of mesh objects
    :type meshlist: list
    :param deleteDeadShapes: delete any dead original nodes while checking?
    :type deleteDeadShapes: bool
    :param displayMessage: Report the message inside of maya?
    :type displayMessage: bool
    :return origShapeList: list of original shape nodes (intermediate objects)
    :rtype origShapeList: list
    """
    origShapeList = list()
    for mesh in meshList:
        origShapeList.append(
            checkValidOrigShape(mesh, deleteDeadShapes=deleteDeadShapes, displayMessage=displayMessage))
    return origShapeList


def cleanDeadOrigShapesSelected(displayMessage=True):
    """Cleans the unused original shape nodes from selected mesh
    Nodes are likely intermediate objects with no output connections, usually left over and unused nodes

    :param displayMessage: Report the message inside of maya?
    :type displayMessage: bool
    """
    selObj = cmds.ls(selection=True, long=True)
    checkValidOrigShapeList(selObj, deleteDeadShapes=True, displayMessage=displayMessage)
    if displayMessage:
        selObjUniqueShortNames = namehandling.getUniqueShortNameList(selObj)
        om2.MGlobal.displayInfo("Meshes Cleaned {}, see script editor for details".format(selObjUniqueShortNames))


def duplicateMeshBeforeBind(mesh, fullPath=True, suffix="_duplicate", message=True, deleteDeadShapes=False,
                            transferShader=True):
    """Given a mesh will duplicate it ignoring the skinning, does this via the original shape node.
    Will fail if mesh isn't skinned or no orig node

    :param mesh: The mesh name to be duplicated
    :type mesh: str
    :param fullPath: return full path names not short
    :type fullPath: bool
    :param suffix: The suffix to add to the duplicated mesh
    :type suffix: str
    :param message: Report the message inside of maya?
    :type message: bool
    :param transferShader: Transfer the shader from the skinned mesh so that the new duplicate matches?
    :type transferShader: bool
    :return duplicateMesh: the name of the duplicated mesh
    :rtype: str
    """
    mshShortUniqueName = namehandling.getUniqueShortName(mesh)
    longPrefix, namespace, mshShortUniqueName = namehandling.mayaNamePartTypes(mshShortUniqueName)
    # get orig shape
    originalShapeNode = checkValidOrigShape(mesh, deleteDeadShapes=deleteDeadShapes, displayMessage=message)
    if not originalShapeNode:
        return
    tempDuplicateMesh = cmds.duplicate(originalShapeNode, name="".join([mshShortUniqueName, "_tempDup"]),
                                       returnRootsOnly=True)
    tDupShapesList = shapenodes.filterNotOrigNodes(tempDuplicateMesh, fullPath=fullPath)  # get shape of the new mesh
    # get origShape of the new mesh
    tDupShapesOrigList = shapenodes.getOrigShapeNodes(tempDuplicateMesh, fullPath=fullPath)
    # connect outMesh to inMesh
    cmds.connectAttr('{}.outMesh'.format(tDupShapesOrigList[0]), '{}.inMesh'.format(tDupShapesList[0]))
    # duplicate again to lock in shape
    duplicateMesh = (cmds.duplicate(tempDuplicateMesh, name="".join([mshShortUniqueName, suffix]),
                                    returnRootsOnly=True))[0]
    dupShapesOrigList = shapenodes.getOrigShapeNodes(duplicateMesh, fullPath=fullPath)
    for origShape in dupShapesOrigList:
        cmds.delete(origShape)
    cmds.delete(tempDuplicateMesh)
    attributes.unlockAll(duplicateMesh)  # unlock attributes on duplicate
    if transferShader:  # transfer shader by topology and if not then find the first shader and use it
        shaderutils.transferShaderTopology(mesh, duplicateMesh, ignoreTopologyMismatch=True, message=True)
    if message:
        om2.MGlobal.displayInfo("Success: The object `{}` has been duplicated to "
                                "object `{}".format(mshShortUniqueName, duplicateMesh))
    return duplicateMesh


def duplicateSelectedBeforeBind(fullPath=True, suffix="_duplicate", message=True, selectDuplicate=True,
                                transferShader=True):
    """Duplicates selected mesh/es before a skin cluster has been added, pre bind.
    Will fail if no skinning is present.
    Works by finding the original shape node and duplicating it

    :param fullPath: return full path names not short
    :type fullPath: bool
    :param suffix: The suffix to add to the duplicated mesh
    :type suffix: str
    :param message: Report the message inside of maya?
    :type message: bool
    :param transferShader: Transfer the shader from the skinned mesh so that the new duplicate matches?
    :type transferShader: bool
    :return duplicatedMeshes: a list of the duplicated mesh names
    :rtype: list
    """
    selObjList = cmds.ls(selection=True, long=True)
    if not selObjList:
        om2.MGlobal.displayWarning("No Mesh Selected, Please Select A Skinned or Deformed Mesh")
    duplicatedMeshes = list()
    for obj in selObjList:
        duplicatedMeshes.append(duplicateMeshBeforeBind(obj, fullPath=fullPath, suffix=suffix,
                                                        message=message, transferShader=transferShader))
        duplicatedMeshes = filter(None, duplicatedMeshes)
    if selectDuplicate:
        cmds.select(duplicatedMeshes, replace=True)
    return duplicatedMeshes


def getSkinCluster(obj):
    """Checks if the given object has a skin cluster using mel, (doesn't have a python equivalent).
    Long or short names must be converted to unique names, see namehandling.getUniqueShortName() documentation
    Returns empty string if no skin cluster found on object

    :param obj: Maya obj name, usually a transform node, best if a long or unique name
    :type obj: str
    :return skinCluster: The name of the skin cluster, or if not found/skinned will be an empty string ""
    :rtype skinned: str
    """
    objUniqueName = namehandling.getUniqueShortName(obj)
    return mel.eval('findRelatedSkinCluster {}'.format(objUniqueName))


def getSkinClusterList(objList):
    """Returns a list of skin clusters from an objList

    :param objList: Maya obj name list
    :type objList: list
    :return skinClusterList: list of skin clusters
    :rtype skinClusterList: list
    """
    skinClusterList = list()
    for obj in objList:
        skinCluster = getSkinCluster(obj)
        if skinCluster:
            skinClusterList.append(skinCluster)
    return skinClusterList


def getSkinClustersSelected():
    """Find all the skin clusters related to selected objects (transforms)
    Works off the first shape node and selected must be the transform/s
    """
    objList = cmds.ls(selection=True, long=True)
    skinClusterList = getSkinClusterList(objList)
    return skinClusterList


def getJnts(objList):
    """returns only joints from an object list

    :param objList: list of object names
    :type objList: list
    :return jntList: List of joint names
    :rtype jntList: list
    """
    jntList = list()
    for obj in objList:
        if cmds.objectType(obj, isType='joint'):
            jntList.append(obj)
    return jntList


def filterSkinnedMeshes(objList):
    """Returns meshes that are skinned from a list

    :param objList: list of Maya object names
    :type objList: list
    :return skinnedMeshes: list of skinned meshes
    :rtype skinnedMeshes: list
    """
    skinnedMeshes = list()
    for obj in objList:
        if getSkinCluster(obj):
            skinnedMeshes.append(obj)
    return skinnedMeshes


def filterObjsForSkin(objList):
    """Returns meshes/surfaces and joints that are ready for skinning from the list of objects

    Tests for issues and reports errors

    :return jointList: List of joint names
    :rtype jointList: list
    :return meshList: list of mesh names
    :rtype meshList: list
    """
    meshes = list()
    joints = list()
    for obj in objList:
        if cmds.objectType(obj, isType='joint'):
            joints.append(obj)  # add because joint
        shapes = cmds.listRelatives(obj, shapes=True, fullPath=True)
        if shapes:
            for shape in shapes:
                if cmds.objectType(shape, isType='mesh') or cmds.objectType(shape, isType='nurbsSurface'):
                    if not getSkinCluster(obj):
                        meshes.append(obj)
                        break
    return joints, meshes


def skinClusterMethodSwitch(skinningMethod=2, displayMessage=True):
    """Switches the attribute .skinningMethod for all skinClusters on selected objects

    :param skinningMethod: 0 = classic linear, 1 = dual quaternion, 2 = weight blended
    :type skinningMethod: int
    :param displayMessage: Report the message inside of maya?
    :type displayMessage: bool
    """
    skinClusterList = getSkinClustersSelected()
    if not skinClusterList:
        om2.MGlobal.displayWarning("No skin clusters found on selected")
        return
    for skinCluster in skinClusterList:
        cmds.setAttr("{}.skinningMethod".format(skinCluster), skinningMethod)
    if skinningMethod == 0:
        skinMethodName = "Classic Linear"
    elif skinningMethod == 1:
        skinMethodName = "Dual Quaternion"
    else:
        skinMethodName = "Weight Blended"
    if displayMessage:
        skinClusterNames = ", ".join(skinClusterList)
        om2.MGlobal.displayInfo("Skin Clusters Changed to '{}': {}".format(skinMethodName, skinClusterNames))


def unbindSkinObjs(objList):
    """Python version of Maya's unbind skin, this function is for an object list
    """
    for obj in objList:
        skinCluster = getSkinCluster(obj)
        if skinCluster:  # then mesh is skinned
            cmds.skinCluster(skinCluster, edit=True, unbind=True)
            om2.MGlobal.displayInfo("Skin Cluster `{}` Deleted".format(skinCluster))


def unbindSkinSelected():
    """python version of unbind skin on selected
    """
    selObj = cmds.ls(selection=True, long=True)
    if not selObj:
        om2.MGlobal.displayInfo("No Objects Selected:  Please Selected Skinned Objects")
    unbindSkinObjs(selObj)


def bindSkin(joints, meshes, toSelectedBones=True, maximumInfluences=5, maxEditLimit=5, bindMethod=0,
             displayMessage=True):
    """Skins meshes to joints based with skin variables

    :param toSelectedBones: on binds to selected off binds to hierarchy
    :type toSelectedBones: bool
    :param maxInfluences: 5 is default, 1 is a rigid bind, limits the amount of joint influences
    :type maxInfluences: int
    :param: maxEditLimit is after the weights have been assigned so influences can be set differently for skin editing
    :type maxEditLimit: int
    :param: bindMethod = closest distance = 0, hierarchy = 1, heat = 2 and geodesic = 3
    :type bindMethod: int
    :param displayMessage: Report the message inside of maya?
    :type displayMessage: bool
    """
    geodesic = False
    if bindMethod == 3:  # is geodesic with unique options, must be bound then switched with cmds.geomBind
        bindMethod = 0
        geodesic = True
    for mesh in meshes:
        skinCluster = (cmds.skinCluster(joints, mesh, toSelectedBones=toSelectedBones,
                                        maximumInfluences=maximumInfluences, bindMethod=bindMethod))[0]
    if geodesic:  # if geodesic bind this is needed
        cmds.geomBind(skinCluster, bindMethod=3, falloff=0.2, maxInfluences=maximumInfluences,
                      geodesicVoxelParams=(256, True))
    cmds.setAttr("{}.maintainMaxInfluences".format(skinCluster), 1)
    cmds.setAttr("{}.maxInfluences".format(skinCluster), maxEditLimit)
    if displayMessage:
        meshes = namehandling.getUniqueShortNameList(meshes)
        joints = namehandling.getUniqueShortNameList(joints)
        meshesStr = ", ".join(meshes)
        jointsStr = ", ".join(joints)
        hierarchyMessage = ""
        if not toSelectedBones:
            hierarchyMessage = "And It's Hierarchy"
        om2.MGlobal.displayInfo("Success: Mesh `{}` Bound To Joints: {} {}".format(meshesStr, jointsStr,
                                                                                   hierarchyMessage))


def bindSkinSelected(toSelectedBones=True, maximumInfluences=5, maxEditLimit=5, bindMethod=0, displayMessage=True):
    """Binds skin to mesh or meshes based off selection similar to the regular Maya behaviour.  No in built cmds version

    :param toSelectedBones: on binds to selected off binds to hierarchy
    :type toSelectedBones: bool
    :param maxInfluences: 5 is default, 1 is a rigid bind, limits the amount of joint influences
    :type maxInfluences: int
    :param: maxEditLimit is after the weights have been assigned so influences can be set differently for skin editing
    :type maxEditLimit: int
    :param: bindMethod = distance = 1, hierarchy = 2, heat = 3 and geodesic = 4
    :type bindMethod: int
    :param displayMessage: Report the message inside of maya?
    :type displayMessage: bool
    """
    selObjs = cmds.ls(selection=True, long=True)
    joints, meshes = filterObjsForSkin(selObjs)
    if not meshes or not joints:
        om2.MGlobal.displayWarning("The selection does not contain both joints and unskinned meshes/surfaces, "
                                   "please select and try again")
        return
    bindSkin(joints, meshes, toSelectedBones=toSelectedBones, maximumInfluences=maximumInfluences,
             maxEditLimit=maxEditLimit, bindMethod=bindMethod, displayMessage=displayMessage)


def setMaxInfluencesOnSkinCluster(skinCluster, maxInfluences=4):
    """for a skin cluster set the max influences and turn maintain on

    :param skinCluster: skin cluster name
    :type skinCluster: str
    :param maxInfluences: the max influences
    :type maxInfluences: bool
    """
    cmds.setAttr("{}.maintainMaxInfluences".format(skinCluster), 1)
    cmds.setAttr("{}.maxInfluences".format(skinCluster), maxInfluences)


def setMaxInfluencesOnSkinClusterList(skinClusterList, maxInfluences=4):
    for skinCluster in skinClusterList:
        setMaxInfluencesOnSkinCluster(skinCluster, maxInfluences=maxInfluences)


def setMaxInfluencesOnSkinSelected(maxInfluences=4):
    selObjs = cmds.ls(selection=True, long=True)
    skinClusterList = getSkinClusterList(selObjs)
    if not skinClusterList:
        om2.MGlobal.displayWarning("The selection does not contain objects with skin clusters, "
                                   "please select and try again")
        return
    setMaxInfluencesOnSkinClusterList(skinClusterList, maxInfluences=maxInfluences)
    om2.MGlobal.displayInfo("Success: Max Influences Set To '{}' on {}".format(maxInfluences, skinClusterList))


def checkInfluenceObj(obj, skinCluster):
    """Checks if an object is an influece of a skin cluster

    :param obj: Maya obj name
    :type obj: str
    :param skinCluster: skin cluster name
    :type skinCluster: str
    :return influence: True if the object is an influence
    :rtype influence: bool
    """
    skinInfluences = cmds.skinCluster(skinCluster, query=True, influence=True)
    obj = namehandling.getUniqueShortName(obj)
    for influenceObj in skinInfluences:
        if obj == influenceObj:
            return True


def removeInfluence(objList, skinCluster):
    """Removes Influence Objects from a Skin Cluster
    Checks if influences are valid
    Returns object list of influences removed


    :param objList: the list of influence objects to be removed
    :type objList:
    :param skinCluster: The skin luster name
    :type skinCluster: str
    :return removedInfluenceList: list of influence objects removed
    :rtype: list
    """
    removedInfluenceList = list()
    for obj in objList:
        if checkInfluenceObj(obj, skinCluster):
            cmds.skinCluster(skinCluster, removeInfluence=obj, edit=True)
            removedInfluenceList.append(obj)
    return removedInfluenceList


def removeInfluenceSelected():
    """Removes influence objects from a skinned mesh.
    Last selected object should be the skinned mesh, other objects are the influences
    Will check for user error
    """
    objList = cmds.ls(selection=True, long=True)
    # get obj and joint list
    lastObj = objList[-1]
    del objList[-1]
    skinCluster = getSkinCluster(lastObj)
    if not skinCluster:
        lastObj = namehandling.getUniqueShortName(lastObj)
        om2.MGlobal.displayWarning(
            "Last obj in selection `{}` is not a skinned mesh. Please select in order.".format(lastObj))
        return
    removedInfluenceList = removeInfluence(objList, skinCluster)
    if not removedInfluenceList:
        om2.MGlobal.displayWarning("No Influence Objects found of Skin Cluster `{}`".format(skinCluster))
        return
    removedInfluenceList = namehandling.getUniqueShortNameList(removedInfluenceList)
    om2.MGlobal.displayInfo("Success: Influences removed `{}`".format(removedInfluenceList))


def addJointsToSkinned(jointList, skinClusterList):
    """Adds joints as new influences to a skin cluster
    Select the mesh/es with skin cluster and the joints to assign
    jnts are assigned with zero weighting and do not affect existing weights

    should check this no need for try
    """
    for skinCluster in skinClusterList:
        try:
            cmds.skinCluster(skinCluster, edit=True, addInfluence=jointList, weight=0, lockWeights=1)
        except RuntimeError:
            om2.MGlobal.displayWarning("Influence object `{}` is already attached".format(skinCluster))
        for jnt in jointList:  # unlock weights that were previously locked to be safe while adding
            cmds.skinCluster(skinCluster, influence=jnt, edit=True, lockWeights=0)


def addJointsToSkinnedSelected(displayMessage=True):
    """Adds joints to a skinned mesh, keeps the joints with a zero influence value

    :param displayMessage: Report the message inside of maya?
    :type displayMessage: bool
    """
    objList = cmds.ls(selection=True, long=True)
    jointList = getJnts(objList)
    skinClusterList = getSkinClusterList(objList)
    if not skinClusterList or not jointList:  # error
        om2.MGlobal.displayError("The selection does not contain both joints and meshes/surfaces with skinClusters, "
                                 "please select and try again")
        return
    addJointsToSkinned(jointList, skinClusterList)
    if displayMessage:
        skinClustersStr = ", ".join(skinClusterList)
        om2.MGlobal.displayInfo("Success: Selected joints are now bound to "
                                "SkinCluster/s: '{}' ".format(skinClustersStr))


def disableAllSkinClusters(skinClusterList, displayMessage=True):
    """Disables all skin clusters in scene by turning the node state to hasNoEffect (1)

    :param skinClusterList: List of the skin cluster node names
    :type skinClusterList: list
    :param displayMessage: Report the message inside of maya?
    :type displayMessage: bool
    """
    for skinClstr in skinClusterList:  # disable all skin clusters
        cmds.setAttr(skinClstr + '.nodeState', 1)
    if displayMessage:
        om2.MGlobal.displayInfo("All Skin Clusters Disabled")


def renableAllSkinClusters(skinCLusterList, displayMessage=True, keepSelection=True):
    """Re enables all skin clusters in a scene that have previously had their nodestate set to hasNoEffect (1)
    It does this while rebinding at the current pose, this needs to be done in .mel and is a Maya skin trick

    :param skinClusterList: List of the skin cluster node names
    :type skinClusterList: list
    :param displayMessage: Report the message inside of maya?
    :type displayMessage: bool
    :param keepSelection: Keep the selection?  Needed as te .mel eval requires selection
    :type keepSelection: bool
    """
    if keepSelection:
        selobjs = cmds.ls(selection=True, long=True)
    for skinClstr in skinCLusterList:  # rebind all skin clusters
        jointsBound = cmds.skinCluster(skinClstr, query=True, inf=True)
        geometryBound = cmds.skinCluster(skinClstr, query=True, g=True)
        cmds.select(jointsBound, geometryBound,
                    replace=True)  # needs to select as need to run the mel eval, only works in mel
        mel.eval('SmoothBindSkin')
    if displayMessage:
        om2.MGlobal.displayInfo("All Skin Clusters Enabled")
    if keepSelection:
        cmds.select(selobjs, replace=True)


def toggleAllSkinClusters(displayMessage=True):
    """Toggles all skin clusters in a scene
    Handy for quick move pivots on joints
    Uses the `nodeState` attribute on the cluster

    1. Switching the nodestate to 1 (hasNoEffect) disables the skin cluster like a temp skin unbind without data loss
    2. Maya trick by selecting any joint and the mesh of the existing skin cluster and > `bind skin`
    3. Will return the cluster on skinning essentially skinning it at the current mesh/joint position
    """
    skinClusterList = getAllSkinClusters(displayMessage=False)
    if not skinClusterList:
        if displayMessage:
            om2.MGlobal.displayWarning("No skinClusters Exist In The Scene")
        return
    if cmds.getAttr(skinClusterList[0] + '.nodeState') == 1:  # re enable clusters
        renableAllSkinClusters(skinClusterList, displayMessage=displayMessage, keepSelection=True)
    else:
        disableAllSkinClusters(skinClusterList, displayMessage=displayMessage)  # disable


def transferSkinning(sourceMesh, targetMesh):
    """Transfers skin weights from the source mesh to the target,
    if the target already has a skin cluster will use the current

    :param sourceMesh: the mesh that already has the skin weights
    :type sourceMesh: str
    :param targetMesh: the mesh that will have the skin weights copied onto it
    :type targetMesh: str
    :return targetSkinCluster: the skinCluster created or transferred onto
    :rtype targetSkinCluster: str
    """
    sourceSkinCluster = getSkinCluster(sourceMesh)
    if not sourceSkinCluster:
        om2.MGlobal.displayWarning("Cannot find a skin cluster on `{}`".format(sourceMesh))
    # if there isn't a skin cluster already, create one
    targetSkinCluster = getSkinCluster(targetMesh)
    if not targetSkinCluster:
        influences = cmds.skinCluster(sourceSkinCluster, q=True, inf=True)
        targetSkinCluster = cmds.skinCluster(targetMesh, influences, toSelectedBones=True)[0]
    cmds.copySkinWeights(sourceSkin=sourceSkinCluster,
                         destinationSkin=targetSkinCluster,
                         noMirror=True,
                         surfaceAssociation='closestPoint',
                         smooth=True)
    return targetSkinCluster


def transferSkinWeightsSelected():
    """Transfers skin weights from the first selected object to other objects
    iterates through a list so the transfer is from the first object selected to all other objects
    """
    objList = cmds.ls(selection=True, long=True)
    if not getSkinCluster(objList[0]):
        objectZero = namehandling.getUniqueShortName(objList[0])
        om2.MGlobal.displayWarning("No SkinClusters Exist On Object `{}`".format(objectZero))
        return
    for obj in objList[1:]:
        transferSkinning(objList[0], obj)


def mirrorSkinClusterList(skinClusterList, surfaceAssociation="closestPoint", influenceAssociation="closestJoint",
                          mirrorMode='YZ',
                          mirrorInverse=False):
    """Mirrors Skin Clusters

    :param surfaceAssociation: which surface style to mirror, "closestPoint", "rayCast", or "closestComponent"
    :type surfaceAssociation: str
    :param influenceAssociation: choose joint style to mirror "closestJoint", "closestBone", "label", "name", "oneToOne"
    :type influenceAssociation: str
    :param mirrorMode: which plane to mirror over, XY, YZ, or XZ
    :type mirrorMode: str
    :param mirrorInverse: Reverse the direction of the mirror. if true - to +
    :type mirrorInverse: bool
    """
    for skinCluster in skinClusterList:
        cmds.copySkinWeights(sourceSkin=skinCluster, destinationSkin=skinCluster, mirrorMode=mirrorMode,
                             mirrorInverse=mirrorInverse, influenceAssociation=influenceAssociation,
                             surfaceAssociation=surfaceAssociation)


def mirrorSkinMeshList(objList, surfaceAssociation="closestPoint", influenceAssociation="closestJoint", mirrorMode='YZ',
                       mirrorInverse=False):
    """Mirrors Skin Weights from skin clusters connected to the objects in the objList

    :param objList: List of Maya Object Names
    :type objList: list
    :param surfaceAssociation: which surface style to mirror, "closestPoint", "rayCast", or "closestComponent"
    :type surfaceAssociation: str
    :param influenceAssociation: choose joint style to mirror "closestJoint", "closestBone", "label", "name", "oneToOne"
    :type influenceAssociation: str
    :param mirrorMode: which plane to mirror over, XY, YZ, or XZ
    :type mirrorMode: str
    :param mirrorInverse: Reverse the direction of the mirror. if true - to +
    :type mirrorInverse: bool
    :return skinClusterList: list of the skin clusters mirrored
    :rtype skinClusterList: list
    """
    skinClusterList = getSkinClusterList(objList)
    if not skinClusterList:
        return
    mirrorSkinClusterList(skinClusterList, surfaceAssociation=surfaceAssociation,
                          influenceAssociation=influenceAssociation,
                          mirrorMode=mirrorMode, mirrorInverse=mirrorInverse)
    return skinClusterList


def mirrorSkinSelection(surfaceAssociation="closestPoint", influenceAssociation="closestJoint", mirrorMode='YZ',
                        mirrorInverse=False):
    """Mirrors Skin Weights from skin clusters assigned to the current meshes or joints
    Selections as object transforms

    :param surfaceAssociation: which surface style to mirror, "closestPoint", "rayCast", or "closestComponent"
    :type surfaceAssociation: str
    :param influenceAssociation: choose joint style to mirror "closestJoint", "closestBone", "label", "name", "oneToOne"
    :type influenceAssociation: str
    :param mirrorMode: which plane to mirror over, XY, YZ, or XZ
    :type mirrorMode: str
    :param mirrorInverse: Reverse the direction of the mirror. if true - to +
    :type mirrorInverse: bool
    """
    objList = cmds.ls(selection=True, long=True)
    skinClusterList = mirrorSkinMeshList(objList, surfaceAssociation=surfaceAssociation,
                                         influenceAssociation=influenceAssociation, mirrorMode=mirrorMode,
                                         mirrorInverse=mirrorInverse)
    if not skinClusterList:
        om2.MGlobal.displayWarning("No skin clusters found on selected")
        return
    skinClusterNames = ", ".join(skinClusterList)
    om2.MGlobal.displayInfo("Skin Clusters Mirrored: '{}'".format(skinClusterNames))
