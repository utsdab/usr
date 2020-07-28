import maya.cmds as cmds
import maya.api.OpenMaya as om2

from zoo.libs.maya.cmds.renderer import exportglobals

DISPLAYSMOOTHMESH = exportglobals.DISPLAYSMOOTHMESH   # SubD attribute and dict key
SMOOTHLEVEL = exportglobals.SMOOTHLEVEL  # SubD attribute and dict key
USESMOOTHPREVIEWFORRENDERER = exportglobals.USESMOOTHPREVIEWFORRENDERER  # SubD attribute and dict key
RENDERSMOOTHLEVEL = exportglobals.RENDERSMOOTHLEVEL  # SubD attribute and dict key
MESHOBJECTS = exportglobals.MESHOBJECTS  # dict key for the generic mesh objects that contain subD info


def getMeshSubDSettings(meshTransform, longName=True):
    """Returns four SubD mode attribute settings as a dict with these keys...

        DISPLAYSMOOTHMESH: if the object has subd mode on (2) or hull (1) or none (0)
        SMOOTHLEVEL: the divisions level setting as an int
        USESMOOTHPREVIEWFORRENDERER: if renderer override is on (True False)
        RENDERSMOOTHLEVEL: the renderer override level as int

    :param meshTransform: a single transform name with mesh shape node/s
    :type meshTransform: str
    :param longName: query as longnames
    :type longName: bool
    :return subDDict: dictionary of subD attribute values
    :rtype subDDict:
    """
    subDDict = dict()
    meshShapes = cmds.listRelatives(meshTransform, shapes=True, fullPath=longName, type="mesh")
    subDDict[DISPLAYSMOOTHMESH] = cmds.getAttr(".".join([meshShapes[0], DISPLAYSMOOTHMESH]))
    subDDict[SMOOTHLEVEL] = cmds.getAttr(".".join([meshShapes[0], SMOOTHLEVEL]))
    subDDict[USESMOOTHPREVIEWFORRENDERER] = cmds.getAttr(".".join([meshShapes[0], USESMOOTHPREVIEWFORRENDERER]))
    subDDict[RENDERSMOOTHLEVEL] = cmds.getAttr(".".join([meshShapes[0], RENDERSMOOTHLEVEL]))
    return subDDict


def getMeshSubDSettingsList(meshTransformList, longName=True):
    """Returns a nested dict of the 4 SubD mode settings given a meshTransformNode as a dict
    The nested dicts keys are meshTransform names
    The subD attribute dict has four keys

        DISPLAYSMOOTHMESH: if the object has subd mode on (2) or hull (1) or none (0)
        SMOOTHLEVEL: the divisions level setting as an int
        USESMOOTHPREVIEWFORRENDERER: if renderer override is on (True False)
        RENDERSMOOTHLEVEL: the renderer override level as int

    :param meshTransformList: a list of maya transform nodes with mesh shape nodes attached
    :type meshTransformList: list
    :param longName: query as longnames
    :type longName: bool
    :return subDMeshDict: a nested dictionary meshes as keys and subD dict of attribute values
    :rtype subDMeshDict: dict
    """
    subDMeshDict = dict()
    for meshTransform in meshTransformList:
        subDMeshDict[meshTransform] = getMeshSubDSettings(meshTransform, longName=longName)
    return subDMeshDict


def setMeshSubDSettings(meshTransform, subDDict, longName=True):
    """for a meshTransform apply the settings of a subDDict, with the following attributes being set...

        DISPLAYSMOOTHMESH: if the object has subd mode on (2) or hull (1) or none (0)
        SMOOTHLEVEL: the divisions level setting as an int
        USESMOOTHPREVIEWFORRENDERER: if renderer override is on (True False)
        RENDERSMOOTHLEVEL: the renderer override level as int

    :param meshTransform: a single transform name with mesh shape node/s
    :type meshTransform: str
    :param longName: query as longnames
    :type longName: bool
    :param subDDict: a subD dictionary of the subD attributes
    :type subDDict: dict
    """
    meshShapes = cmds.listRelatives(meshTransform, shapes=True, fullPath=longName, type="mesh")
    for meshShape in meshShapes:
        cmds.setAttr("{}.displaySmoothMesh".format(meshShape), subDDict[DISPLAYSMOOTHMESH])
        cmds.setAttr("{}.smoothLevel".format(meshShape), subDDict[SMOOTHLEVEL])
        cmds.setAttr("{}.useSmoothPreviewForRender".format(meshShape), subDDict[USESMOOTHPREVIEWFORRENDERER])
        cmds.setAttr("{}.renderSmoothLevel".format(meshShape), subDDict[RENDERSMOOTHLEVEL])


def setMeshSubDSettingsList(meshTransformList, subDDict, longName=True):
    """for a meshTransformList apply the settings of a single subDDict

        DISPLAYSMOOTHMESH: if the object has subd mode on (2) or hull (1) or none (0)
        SMOOTHLEVEL: the divisions level setting as an int
        USESMOOTHPREVIEWFORRENDERER: if renderer override is on (True False)
        RENDERSMOOTHLEVEL: the renderer override level as int

    :param meshTransformList: a list of maya transform nodes with mesh shape nodes attached
    :type meshTransformList: list
    :param longName: query as longnames
    :type longName: bool
    :param subDDict: a subD dictionary of the subD attributes
    :type subDDict: dict
    """
    for meshTransform in meshTransformList:
        setMeshSubDSettings(meshTransform, subDDict, longName=True)


def setMeshSubDSettingsSelected(subDDict, longName=True):
    """For the selected objects apply the settings of a single subDDict

            DISPLAYSMOOTHMESH: if the object has subd mode on (2) or hull (1) or none (0)
            SMOOTHLEVEL: the divisions level setting as an int
            USESMOOTHPREVIEWFORRENDERER: if renderer override is on (True False)
            RENDERSMOOTHLEVEL: the renderer override level as int

    :param longName: query as longnames
    :type longName: bool
    :param subDDict: a subD dictionary of the subD attributes
    :type subDDict: dict
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        om2.MGlobal.displayWarning('No Objects Selected, Please Select'.format())
        return
    setMeshSubDSettingsList(selObjs, subDDict, longName=True)

