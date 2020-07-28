import os

import maya.api.OpenMaya as om2
import maya.cmds as cmds
import maya.mel as mel

from zoo.libs.utils import filesystem
from zoo.libs.maya.utils import files
from zoo.libs.maya.cmds.objutils import filtertypes, namehandling, selection
from zoo.libs.maya.cmds.modeling import subdivisions, components

try:
    from zoo.libs.buliarcacristian import lockNormals_toHS
except:
    pass

OLD_GEO_SUFFIX = "oldGeo"


def nonManifold(objList=list(), select=True, message=True):
    """Selects Non-Manifold Vertices on selected meshes or those given with objList

    :param objList: Optional list of Maya objects if empty will use the current selection.
    :type objList: list(str)
    :param select: Select the verts?
    :type select: bool
    :param message: Report message to the user?
    :type message: bool

    :return verts: Non manifold selection if found otherwise an empty list
    :rtype verts: list(str)
    """
    origSelection = cmds.ls(selection=True)
    if objList:
        selMeshTransforms = filtertypes.filterTypeReturnTransforms(objList, children=False, shapeType="mesh")
    else:
        selMeshTransforms = filtertypes.filterTypeReturnTransforms(origSelection, children=False, shapeType="mesh")
    if not selMeshTransforms:
        if message:
            om2.MGlobal.displayWarning("Please select a polygon object")
        return list()
    verts = cmds.polyInfo(selMeshTransforms, nonManifoldVertices=True)
    if verts:
        if select:
            selObjs = selection.componentsToObjectList(verts)
            cmds.select(selObjs, replace=True)
            cmds.selectMode(component=True)
            cmds.selectType(vertex=True)
            cmds.select(verts, replace=True)
        if message:
            om2.MGlobal.displayWarning("Non-Manifold Vertices Found: {}".format(verts))
        return verts
    if message:
        om2.MGlobal.displayInfo("No Non-Manifold Vertices Found.")
    return list()


def interiorVertex(objList=list(), includeBoundary=False, select=True, message=True):
    """Selects Interior-Vertex Vertices on selected meshes

    :param objList: Optional list of Maya objects if empty will use the current selection.
    :type objList: list(str)
    :param includeBoundary: If True interior vertices can be on a border edge
    :type includeBoundary: bool
    :param select: Select the verts?
    :type select: bool
    :param message: Report message to the user?
    :type message: bool

    :return interiorVerts: Interior Vert selection if found otherwise an empty list
    :rtype interiorVerts: list(str)
    """
    if objList:
        origSel = objList
        cmds.select(objList, replace=True)
        selMeshTransforms = filtertypes.filterTypeReturnTransforms(objList, children=False, shapeType="mesh")
    else:
        origSel = cmds.ls(selection=True)
        selMeshTransforms = filtertypes.filterTypeReturnTransforms(origSel, children=False, shapeType="mesh")
    if not selMeshTransforms:
        if message:
            om2.MGlobal.displayWarning("Please select a polygon object")
        return list()
    # Find the interior verts, will included perimeter vertices -------------------
    mel.eval("resetPolySelectConstraint")
    cmds.polySelectConstraint(mode=3, type=1, order=True, orderbound=(0, 2))  # interior vertex including boundary
    mel.eval("resetPolySelectConstraint")
    interiorVerts = cmds.ls(selection=True)
    # Report the messages -----------------------------------------------
    if not interiorVerts:
        if message:
            om2.MGlobal.displayInfo("No Interior Vertices Found")
        if selMeshTransforms and select:
            cmds.select(selMeshTransforms, replace=True)
        else:
            cmds.select(origSel)
        return list()
    if "vtx" in interiorVerts[0]:  # Interior Verts Found ----------------------------------------------------
        if not includeBoundary:  # Then remove any perimeter vertices
            cmds.select(selMeshTransforms, replace=True)
            mel.eval("ConvertSelectionToVertexPerimeter")
            perimeterVerts = cmds.ls(selection=True)
            cmds.select(interiorVerts, replace=True)
            cmds.select(perimeterVerts, deselect=True)
            interiorVerts = cmds.ls(selection=True)
        # Return/select the verts ----------------------
        if interiorVerts:
            if select:
                selObjs = selection.componentsToObjectList(interiorVerts)
                cmds.select(selObjs, replace=True)
                cmds.selectMode(component=True)
                cmds.selectType(vertex=True)
                cmds.select(interiorVerts, replace=True)
            else:
                cmds.select(origSel)
            if message:
                om2.MGlobal.displayWarning("Interior Vertices Found: {}".format(interiorVerts))
            return interiorVerts
    # Else will be the shape node of the object
    if select:
        cmds.select(selMeshTransforms, replace=True)
    else:
        cmds.select(origSel)
    om2.MGlobal.displayInfo("No Interior Vertices Found")
    return list()


def findLaminaFaces(objList=list(), delete=False, select=True, message=True):
    """Selects or deletes Lamina Faces on selected meshes

    :param objList: Optional list of Maya objects if empty will use the current selection.
    :type objList: list(str)
    :param delete: Deletes the faces if any are found, otherwise select
    :type delete: bool
    :param select: Select the faces?
    :type select: bool
    :param message: Report message to the user?
    :type message: bool

    :return laminaFaces: laminaFace selection if found otherwise an empty list
    :rtype laminaFaces: list(str)
    """
    if not objList:
        faces = cmds.polyInfo(laminaFaces=True)
    else:
        faces = cmds.polyInfo(objList, laminaFaces=True)
    if not faces:
        if message:
            om2.MGlobal.displayInfo("No Lamina Faces Found")
        return list()
    if select and not delete:
        selObjs = selection.componentsToObjectList(faces)
        cmds.select(selObjs, replace=True)
        cmds.selectMode(component=True)
        cmds.selectType(polymeshFace=True)
        cmds.select(faces, replace=True)
    if delete:
        cmds.delete(faces)
        if message:
            om2.MGlobal.displayInfo("Lamina Faces Deleted: {}".format(faces))
        return faces
    if message:
        om2.MGlobal.displayWarning("Lamina Faces Found: {}".format(faces))
    return faces


def zeroFace(objList, select=True, message=True):
    """Finds faces with zero area and selects them as vertices so they are easy to see.

    :param objList: the objects to check for zero face issues.
    :type objList: bool
    :param select: Select the faces as vertices?  False will ignore the selection
    :type select: bool
    :param message: Report message to the user?
    :type message: bool

    :return zeroFaces: Zero Face selection if found otherwise an empty list
    :rtype zeroFaces: list(str)
    """
    origSel = cmds.ls(selection=True)
    cmds.select(objList, replace=True)
    zeroFacesAsVerts = calcZeroFace(objList, select=select, message=select)
    if zeroFacesAsVerts:
        return zeroFacesAsVerts  # already selected and messages
    cmds.select(origSel, replace=True)  # return to the original selection
    return list()


def zeroFaceSelected(select=True, message=True):
    """From the selection finds faces with zero area and optionally selects them as vertices so they are easy to see.

    :param select: Select the faces as vertices?  False will ignore the selection
    :type select: bool
    :param message: Report message to the user?
    :type message: bool

    :return zeroFaces: Zero Face selection if found otherwise an empty list
    :rtype zeroFaces: list(str)
    """
    origSel = cmds.ls(selection=True)
    if not origSel:
        if message:
            om2.MGlobal.displayWarning("Please select a polygon object")
        return list()
    return calcZeroFace(origSel, select=select, message=select)


def calcZeroFace(selObjs, select=True, message=True):
    """Finds any zero faces and returns and optionally selects them

    :param selobjs: The selected objects
    :type selobjs: list(str)
    :param select: Select the faces as vertices?  False will ignore the selection
    :type select: bool
    :param message: Report message to the user?
    :type message: bool

    :return zeroFaces: Zero Face selection if found otherwise an empty list
    :rtype zeroFaces: list(str)
    """
    mel.eval('polyCleanupArgList 4 {"0", "2", "1", "0", "0", "0", "0", "0", "1", "1e-05", "0", "1e-05", "0", "1e-05", '
             '"0", "-1", "0", "0"}')
    zeroFaceSelection = cmds.ls(selection=True)
    if not zeroFaceSelection:
        cmds.select(selObjs, replace=True)
        if message:
            om2.MGlobal.displayInfo("No faces with zero area found.")
        return list()
    mel.eval("ConvertSelectionToVertices")
    selection.convertSelection(type="vertices")  # convert face to vert selection
    zeroFacesAsVerts = cmds.ls(selection=True)
    if select:
        selObjs = selection.componentsToObjectList(zeroFacesAsVerts)  # filter the objects so they can be selected
        cmds.select(selObjs, replace=True)
        cmds.selectMode(component=True)
        cmds.selectType(vertex=True)
        cmds.select(zeroFacesAsVerts, replace=True)
    else:
        cmds.select(selObjs, replace=True)
    if message:
        om2.MGlobal.displayWarning("Zero faces found: {}".format(zeroFaceSelection))
    return zeroFacesAsVerts


def deleteHistory():
    """Delete History on selected objects"""
    cmds.delete(constructionHistory=True)
    om2.MGlobal.displayInfo("History Deleted for: {}".format(cmds.ls(selection=True)))


def freezeTransforms():
    """Maya default Freeze Transforms on selected"""
    mel.eval('performFreezeTransformations(0)')
    om2.MGlobal.displayInfo("Frozen Transforms: {}".format(cmds.ls(selection=True)))


def unlockVertexNormalsObj(obj, keepSoftHard=False):
    """Unlocks vertex normals on an object.

    WARNING:  keepSoftHard takes a lot of time on dense meshes 20sec per 3k faces. Slow function

    :param obj: A maya mesh object
    :type obj: str
    :param keepSoftHard: Keeps the soft and hard edges but does slow down the function
    :type keepSoftHard: bool
    """
    try:
        reload(lockNormals_toHS)
        lockNormals_toHS.run([obj])
        return
    except:
        om2.MGlobal.displayWarning("Could not maintain smoothing with Community Script: "
                                   "zoo.libs.buliarcacristian.lockNormals_toHS")
    cmds.polyNormalPerVertex([obj], unFreezeNormal=True)


def unlockVertexNormalsList(objList=list(), keepSoftHard=False, message=True):
    """Unlocks vertex normals on the currently selected object or the given object list.

    If no objectList is give works on current selection.

    WARNING:  keepSoftHard takes a lot of time on dense meshes 20sec per 3k faces. Slow function

    :param objList: A list of Maya objects
    :type objList: list(str)
    :param keepSoftHard: Keeps the soft and hard edges but does slow down the function
    :type keepSoftHard: bool
    :param message: Report the message to the user?
    :type message: bool
    """
    if not objList:
        objList = checkMeshSelection()
        if not objList:  # reports error if non found
            return
    for obj in objList:
        unlockVertexNormalsObj(obj, keepSoftHard=False)
    if message:
        om2.MGlobal.displayInfo("Unlocked Normals: {}".format(cmds.ls(selection=True)))


def averageVertexNormals():
    mel.eval('performPolyAverageNormal 0')
    om2.MGlobal.displayInfo("Normals Averaged: {}".format(cmds.ls(selection=True)))


def conformNormals():
    """Maya's Mesh Display > Conform Command, all normals conform to face the same direction"""
    mel.eval('performPolyNormal 0 2 0')
    om2.MGlobal.displayInfo("Normals Conformed: {}".format(cmds.ls(selection=True)))


def reverseFaceNormals():
    """Maya's Mesh Display > Reverse Command, flips normal direction"""
    mel.eval('performPolyNormal 0 -1 0')
    om2.MGlobal.displayInfo("Normals Reversed: {}".format(cmds.ls(selection=True)))


def mergeIdenticalVertices():
    """Merge Vertices with extremely low distance tolerance"""
    cmds.polyMergeVertex(distance=0.0001)
    om2.MGlobal.displayInfo("Merge Vertices Node Added: {}".format(cmds.ls(selection=True)))


def selectVerts(vertSelection, origSel):
    """Helper function for GUI while selecting vertices

    :param vertSelection: A maya list of vertices
    :type vertSelection: list(str)
    :param origSel: A list of maya objects usually containing the faces
    :type origSel: list()
    """
    cmds.select(vertSelection, replace=True)
    cmds.select(origSel, add=True)
    cmds.selectMode(component=True)
    cmds.selectType(vertex=True)


def selectFaces(faceSelection, origSel, selObject=True):
    """Helper function for GUI while selecting faces

    :param faceSelection: A maya list of faces
    :type faceSelection: list(str)
    :param origSel: A list of maya objects usually containing the faces
    :type origSel: list()
    """
    cmds.select(faceSelection, replace=True)
    if selObject:
        cmds.select(origSel, add=True)
        cmds.selectMode(component=True)
        cmds.selectType(polymeshFace=True)


def checkMeshSelection():
    """Checks for selected meshes, used by GUIs

    :return selMeshTransforms: Selected mesh transforms will be an empty list if none
    :rtype selMeshTransforms: list(str)
    """
    selMeshTransforms = filtertypes.filterTypeReturnTransforms(cmds.ls(selection=True),
                                                               children=False,
                                                               shapeType="mesh")
    if not selMeshTransforms:
        om2.MGlobal.displayWarning("Please select a polygon object")
        return list()
    return selMeshTransforms


def checkMeshIssues(objList=list(), select=True, message=True):
    """Checks meshes for issues:

        - Non-Manifold
        - Interior-Vertex
        - Zero-Face Area
        - Lamina-Faces

    Returns each type as a list, lists are empty if no issues.

    :param message: Report the message to the user?
    :type message: bool

    :return selMeshTransforms: The meshes in the selection, empty list if no issues
    :rtype selMeshTransforms: list(str)
    :return nonManifoldVerts: A list of vertices matching non-manifold issues, empty list if no issues
    :rtype nonManifoldVerts: list(str)
    :return interiorVerts: A list of vertices matching interior-vertex issues, empty list if no issues
    :rtype interiorVerts: list(str)
    :return zeroFacesAsVerts: A list of vertices matching zero-face issues, empty list if no issues
    :rtype zeroFacesAsVerts: list(str)
    :return laminaFaces:  A list of lamina faces, empty list if no issues
    :rtype laminaFaces: list(str)
    """
    if objList:
        origSel = objList
    else:
        origSel = cmds.ls(selection=True)
    selMeshTransforms = filtertypes.filterTypeReturnTransforms(origSel, children=False, shapeType="mesh")
    if not selMeshTransforms:
        if message:
            om2.MGlobal.displayWarning("Please select a polygon object")
        return list(), list(), list(), list(), list()
    issueText = ""
    if not objList:
        nonManifoldVerts = nonManifold(select=False, message=False)
        interiorVerts = interiorVertex(select=False, message=False)
        zeroFacesAsVerts = zeroFaceSelected(select=False, message=False)
        laminaFaces = findLaminaFaces(delete=False, select=False, message=False)
    else:
        nonManifoldVerts = nonManifold(objList=objList, select=False, message=False)
        interiorVerts = interiorVertex(objList=objList, select=False, message=False)
        zeroFacesAsVerts = zeroFace(objList, select=False, message=False)
        laminaFaces = findLaminaFaces(objList=objList, delete=False, select=False, message=False)
    if select:
        components = nonManifoldVerts + interiorVerts + zeroFacesAsVerts + laminaFaces
        if components:
            selObjs = selection.componentsToObjectList(components)
            cmds.select(selObjs, replace=True)
            cmds.selectMode(component=True)
            if laminaFaces:
                cmds.selectType(polymeshFace=True)
            else:
                cmds.selectType(vertex=True)
            cmds.select(components, replace=True)
    if message:
        if nonManifoldVerts:
            issueText = "{} Non-Manifold".format(issueText)
        if interiorVerts:
            issueText = "{} Interior-Vertices".format(issueText)
        if zeroFacesAsVerts:
            issueText = "{} Zero-Faces".format(issueText)
        if laminaFaces:
            issueText = "{} Lamina-Faces".format(issueText)
        if issueText:
            om2.MGlobal.displayWarning("Mesh Issues Found: {}".format(issueText))
        else:
            om2.MGlobal.displayInfo("Meshes are clean: {}".format(selMeshTransforms))
    return selMeshTransforms, nonManifoldVerts, interiorVerts, zeroFacesAsVerts, laminaFaces


def softenEdge(objComponentList):
    """Softens the selected edges or objects (all edges) as per mesh display > soften edge
    From the given objComponentList, a maya selection list

    :param objComponentList: list of edges or objects
    :type objComponentList: list(str)
    """
    origSel = cmds.ls(selection=True)
    cmds.select(objComponentList, replace=True)
    softenEdgeSelection()
    cmds.select(origSel, replace=True)

def softenEdgeSelection():
    """Softens the selected edges or objects (all edges) as per mesh display > soften edge
    """
    mel.eval("SoftPolyEdgeElements 1; toggleSelMode; toggleSelMode;")


def hardenEdgeSelection():
    """Hardens the selected edges or objects (all edges) as per mesh display > harden edge
    """
    mel.eval("SoftPolyEdgeElements 0; toggleSelMode; toggleSelMode;")


def removeInstances():
    pass


def checkSymmetry():
    pass


def loadObjPlugin():
    """Check if the plugin objExport is loaded, if not load it.
    """
    if not cmds.pluginInfo("objExport", query=True, loaded=True):
        cmds.loadPlugin("objExport")


def objCleanSingle(obj, filePath, objOptions="groups=0;ptgroups=0;materials=0;smoothing=0;normals=1",
                   keepShaders=True, keepSubDs=True, unlockNormals=True, type="obj"):
    """Cleans a single object with OBJ import/export

    Handles:

        - Shader reassignment assignment, supports any shader
        - Vertex normals
        - Naming
        - SubD settings

    :param obj: The mesh objects transform name, must have a mesh shape node.
    :type obj: str
    :param filePath: The full file path to save (file will be immediately deleted)
    :type filePath: string
    :param objOptions: Options for the save of the obj file, see Maya's cmds.file command with options kwarg
    :type objOptions: str
    :param keepShaders: Keeps current shaders by transferring the shaders onto the newly imported objects
    :type keepShaders: bool
    :param keepSubDs: Keeps current subD settings, note issues regarding getting the state of a subD (on off)
    :type keepSubDs: bool

    :return oldObj: The old object now potentially renamed, long name
    :rtype oldObj: str
    :return newObj: The new object's long name
    :rtype newObj: str
    """
    allMeshesBefore = cmds.ls(type="mesh", long=True)
    cmds.select(obj, replace=True)
    if type == "obj":
        # OBJ export/save ---------------------------------------------------------
        filePath = cmds.file(filePath, exportSelected=True, options=objOptions, type="OBJexport", force=True)
        cmds.file(filePath, i=True, type="OBJexport")  # import
    if type == "fbx":  # not tested
        filePath = files.exportFbx(filePath, [obj])
        files.importFbx(filePath)
    os.remove(filePath)  # delete saved file
    allMeshesAfter = cmds.ls(type="mesh", long=True)
    newMeshes = [x for x in allMeshesAfter if x not in allMeshesBefore]  # find new mesh
    # Rename the objects ------------------------------------------------------
    if not newMeshes:
        return obj, None
    newTransformName = cmds.listRelatives(newMeshes[0], parent=True)[0]
    origShortName = namehandling.getShortName(obj)
    # Shader Transfer ---------------------------------------------------------
    if keepShaders:
        cmds.transferShadingSets(obj, newTransformName, sampleSpace=2, searchMethod=1)  # topology transfer
        cmds.delete(newTransformName, constructionHistory=True)  # Delete history
    # SubD Settings ----------------------------------------------------------
    if keepSubDs:
        oldMeshShape = cmds.listRelatives(obj, shapes=True)[0]
        vpDiv, renderDiv, useForRender, showSubDs = subdivisions.subDSettingsShape(oldMeshShape)
        newMeshShape = cmds.listRelatives(newTransformName, shapes=True)[0]
        subdivisions.setSubDSettingsShape(newMeshShape,
                                          previewDivisions=vpDiv,
                                          rendererDivisions=renderDiv,
                                          usePreview=useForRender,
                                          displaySubs=showSubDs)
        # set 1 2 or 3 for the Smooth Mesh Preview mode, only works if user has hit the 3 key in the current session...
        subDMode = cmds.displaySmoothness(oldMeshShape, polygonObject=2, query=True)  # queries the 1, 2 or 3 hotkey
        cmds.displaySmoothness(newMeshShape, polygonObject=subDMode[0])
    # Unlock normals  ------------------------------------------------------------------
    if unlockNormals:
        unlockVertexNormalsObj(newTransformName, keepSoftHard=True)
        cmds.delete(newTransformName, constructionHistory=True)  # Delete history
    # Rename ------------------------------------------------------------------
    suffix = obj.split("_")[-1]
    if suffix == OLD_GEO_SUFFIX:  # old name already has this suffix
        oldObj = str(obj)
        newObj = obj.replace("_{}".format(OLD_GEO_SUFFIX), "")
        newObj = namehandling.nonUniqueNameNumber(namehandling.getShortName(newObj))
        newObj = namehandling.safeRename(newTransformName, newObj)
    else:  # rename old name
        uniqueOldName = namehandling.getUniqueNameSuffix(origShortName, OLD_GEO_SUFFIX)
        oldObj = namehandling.safeRename(obj, uniqueOldName)
        newName = namehandling.nonUniqueNameNumber(origShortName)
        newObj = namehandling.safeRename(newTransformName, newName)
    return oldObj, newObj


def objClean(deleteOldObj=False, keepNormals=True, keepShaders=True, keepSubDs=True, type="obj", message=True):
    """Cleans an object by exporting it as an OBJ to the temp directory and importing it again. Parents the object in \
    world coords.

    Option to delete the old object.

    Handles:

        - Shader reassignment assignment, supports any shader
        - Vertex normals
        - Naming
        - SubD settings

    :param deleteOldObj: Will remove the existing object now replaced with the new.
    :type deleteOldObj: bool
    :param keepNormals: Keeps the normals on the export so they import with the new model
    :type keepNormals: bool
    :param keepShaders: Keeps current shaders by transferring the shaders onto the newly imported objects
    :type keepShaders: bool
    :param keepSubDs: Keeps current shaders by transferring the shaders onto the newly imported objects
    :type keepSubDs: bool
    :param message: Reports the message to the user
    :type message: bool

    :return newObjectList: A list of new objects that have been created
    :rtype newObjectList: list(str)
    :return oldObjectList: A list of the old objects now potentially renamed
    :rtype oldObjectList: list(str)
    """
    newObjectList = list()
    oldObjectList = list()
    selObjs = cmds.ls(selection=True)
    selMeshTransforms = filtertypes.filterTypeReturnTransforms(selObjs, children=False, shapeType="mesh")
    if not selMeshTransforms:
        om2.MGlobal.displayWarning("Please select polygon object/s")
        return list(), list()
    # Start -------------------------------------------------------------
    loadObjPlugin()
    tempDir = filesystem.getTempDir()  # needs temp dir as filepaths with spaces aren't supported
    objFilePath = os.path.join(tempDir, "temp.{}".format(type))
    if keepNormals:
        normals = "1"
        unlockNormals = True
    else:
        normals = "0"
        unlockNormals = False
    objOptions = "groups=0;ptgroups=0;materials=0;smoothing=0;normals={}".format(normals)
    # save and import each mesh in the selection ------------------------------------
    for obj in selMeshTransforms:
        oldObj, newObj = objCleanSingle(obj, objFilePath, objOptions=objOptions, keepShaders=keepShaders,
                                        keepSubDs=keepSubDs, unlockNormals=unlockNormals, type=type)
        newObjectList.append(newObj)
        oldObjectList.append(oldObj)
    if deleteOldObj:
        cmds.delete(oldObjectList)
        oldObjectList = list()
    cmds.select(newObjectList, replace=True)  # Otherwise errors if the Attribute Editor is open
    if message:
        om2.MGlobal.displayInfo(
            "Success: Meshes OBJ import/exported: {}".format(namehandling.getShortNameList(newObjectList)))
    return newObjectList, oldObjectList
