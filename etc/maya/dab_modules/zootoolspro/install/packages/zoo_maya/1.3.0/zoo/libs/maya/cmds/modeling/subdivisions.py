from maya import cmds
import maya.api.OpenMaya as om2

from zoo.libs.maya.cmds.objutils import filtertypes


def subDSettingsShape(meshShape):
    """Returns the subdivision settings of the meshShape node

    :param meshShape: The mesh shape node name
    :type meshShape: str

    :return vpDiv: Gets the Preview Division Levels attribute on the mesh shape
    :rtype vpDiv: int
    :return renderDiv: Gets the Render Division Levels attribute on the mesh shape
    :rtype renderDiv: int
    :return useForRender: Gets the Use Preview Level For Rendering check box on the mesh shape
    :rtype useForRender: bool
    :return showSubDs: Gets the Display Subdivisions check box on the mesh shape
    :rtype showSubDs: bool
    """
    showSubDs = cmds.getAttr("{}.displaySubdComps".format(meshShape))
    vpDiv = cmds.getAttr("{}.smoothLevel".format(meshShape))
    useForRender = cmds.getAttr("{}.useSmoothPreviewForRender".format(meshShape))
    renderDiv = cmds.getAttr("{}.renderSmoothLevel".format(meshShape))
    return vpDiv, renderDiv, useForRender, showSubDs


def subDSettingsSelected(message=False):
    """Returns the subdivision settings of the last selected mesh transform

    :param message: return the message to the user?
    :type message: bool

    :return vpDiv: Gets the Preview Division Levels attribute on the mesh shape
    :rtype vpDiv: int
    :return renderDiv: Gets the Render Division Levels attribute on the mesh shape
    :rtype renderDiv: int
    :return useForRender: Gets the Use Preview Level For Rendering check box on the mesh shape
    :rtype useForRender: bool
    :return showSubDs: Gets the Display Subdivisions check box on the mesh shape
    :rtype showSubDs: bool
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        return None, None, None, None
    meshList = filtertypes.filterTypeReturnTransforms(selObjs, children=False, shapeType="mesh")
    if not meshList:
        return None, None, None, None
    return subDSettingsShape(meshList[0])


def setSubDSettingsShape(meshShape, previewDivisions=2, rendererDivisions=2, usePreview=True, displaySubs=False):
    """Sets the subd mesh settings on the mesh shape node for polygon object Maya.

    :param meshShape: The mesh shape node name
    :type meshShape: str
    :param previewDivisions: Sets the Preview Division Levels attribute on the mesh shape
    :type previewDivisions: int
    :param rendererDivisions: Sets the Render Division Levels attribute on the mesh shape
    :type rendererDivisions: int
    :param usePreview: Sets the Use Preview Level For Rendering check box on the mesh shape
    :type usePreview: bool
    :param displaySubs: Sets the Display Subdivisions check box on the mesh shape
    :type displaySubs: bool
    """
    cmds.setAttr("{}.displaySubdComps".format(meshShape), displaySubs)
    cmds.setAttr("{}.smoothLevel".format(meshShape), previewDivisions)
    cmds.setAttr("{}.useSmoothPreviewForRender".format(meshShape), usePreview)
    cmds.setAttr("{}.renderSmoothLevel".format(meshShape), rendererDivisions)


def setSubDSettingsTransform(obj, previewDivisions=2, rendererDivisions=2, usePreview=True, displaySubs=False):
    """Sets the subd mesh settings on a transform polygon node.

    :param obj: The transform node name
    :type obj: str
    :param previewDivisions: Sets the Preview Division Levels attribute on the mesh shape
    :type previewDivisions: int
    :param rendererDivisions: Sets the Render Division Levels attribute on the mesh shape
    :type rendererDivisions: int
    :param usePreview: Sets the Use Preview Level For Rendering check box on the mesh shape
    :type usePreview: bool
    :param displaySubs: Sets the Display Subdivisions check box on the mesh shape
    :type displaySubs: bool
    """
    meshShapes = cmds.listRelatives(obj, shapes=True, fullPath=True, type="mesh")
    if not meshShapes:
        return
    for meshShape in meshShapes:
        setSubDSettingsShape(meshShape, previewDivisions=previewDivisions, rendererDivisions=rendererDivisions,
                             usePreview=usePreview, displaySubs=displaySubs)


def setSubDSettingsList(objList, previewDivisions=2, rendererDivisions=2, usePreview=True, displaySubs=False):
    """Sets the subd mesh settings on a transform polygon node list.

    :param objList: A list of transform node names with mesh shapes
    :type objList: list(str)
    :param previewDivisions: Sets the Preview Division Levels attribute on the mesh shape
    :type previewDivisions: int
    :param rendererDivisions: Sets the Render Division Levels attribute on the mesh shape
    :type rendererDivisions: int
    :param usePreview: Sets the Use Preview Level For Rendering check box on the mesh shape
    :type usePreview: bool
    :param displaySubs: Sets the Display Subdivisions check box on the mesh shape
    :type displaySubs: bool
    """
    for obj in objList:
        setSubDSettingsTransform(obj, previewDivisions=previewDivisions, rendererDivisions=rendererDivisions,
                                 usePreview=usePreview, displaySubs=displaySubs)


def setSubDSettingsList(previewDivisions=2, rendererDivisions=2, usePreview=True, displaySubs=False, message=True):
    """Sets the subD mesh settings on the current selection

    :param previewDivisions: Sets the Preview Division Levels attribute on the mesh shape
    :type previewDivisions: int
    :param rendererDivisions: Sets the Render Division Levels attribute on the mesh shape
    :type rendererDivisions: int
    :param usePreview: Sets the Use Preview Level For Rendering check box on the mesh shape
    :type usePreview: bool
    :param displaySubs: Sets the Display Subdivisions check box on the mesh shape
    :type displaySubs: bool
    :param message: Report the message to the user?
    :type message: bool
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        if message:
            om2.MGlobal.displayWarning("No objects selected.  Please select mesh object/s")
        return
    meshList = filtertypes.filterTypeReturnTransforms(selObjs, children=False, shapeType="mesh")
    if not meshList:
        if message:
            om2.MGlobal.displayWarning("Please select mesh object/s.  No polygon mesh objects found")
        return
    for obj in meshList:
        setSubDSettingsTransform(obj, previewDivisions=previewDivisions, rendererDivisions=rendererDivisions,
                                 usePreview=usePreview, displaySubs=displaySubs)
