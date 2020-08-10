import maya.api.OpenMaya as om2
import maya.cmds as cmds
from zoo.libs.maya import zapi

from zoo.libs.maya.cmds.objutils import objhandling
from zoo.libs.maya.cmds.display import viewportmodes
from zoo.libs.utils import colour

OTHERCAMDEFAULTS = ["bottom", "left", "back"]

CAM_TYPE_ALL = "all"
CAM_TYPE_PERSP = "perspective"
CAM_TYPE_ORTHOGRAPHIC = "orthographic"

CAM_FIT_RES_FILL = 0
CAM_FIT_RES_HORIZONTAL = 1
CAM_FIT_RES_VERTICAL = 2
CAM_FIT_RES_OVERSCAN = 3

ZOO_APERTURE_INCH_WIDTH_ATTR = "zooApertureWidthI"
ZOO_APERTURE_INCH_HEIGHT_ATTR = "zooApertureHeightI"
ZOO_APERTURE_BOOL = "zooApertureBool"
ZOO_APERTURE_PREVIOUS_FIT = "zooPreviousFit"
ZOO_FIT_LIST = "Fill:Horizontal:Vertical:Overscan"


def inchesToMm(inchesValue):
    """Converts inches (as a float) to mm

    :param inchesValue: value in inches
    :type inchesValue: float

    :return: mmValue: value in mm
    :rtype: mmValue: float
    """
    return inchesValue * 25.4


def mmToInches(mmValue):
    """mm to inches (as a float)

    :param mmValue: value in mm
    :type mmValue: float

    :return inchesValue: value in inches
    :rtype inchesValue: float
    """
    return mmValue / 25.4


def cameraShape(cameraTransform):
    """Returns the camera shape node given the camera transform

    :param cameraTransform: Name of the maya camera transform node
    :type cameraTransform: str

    :return: Name of the maya camera shape node
    :rtype: str
    """
    return cmds.listRelatives(cameraTransform, shapes=True, allDescendents=False, fullPath=True, type="camera")[0]


def cameraTransform(cameraShape):
    """Returns the camera transform node given the camera shape

    :param cameraShape: Name of the maya camera shape node
    :type cameraShape: str

    :return cameraTransform: Name of the maya camera transform node
    :rtype cameraTransform: str
    """
    return cmds.listRelatives(cameraShape, parent=True, fullPath=True)[0]


def cameraShapeList(cameraTransformList):
    """Returns the camera shape node list given a camera transform node list

    :param cameraTransformList: List of maya camera transform node names
    :type cameraTransformList: list(str)
    :return camShapeList: List of many camera shape node names
    :rtype camShapeList: list(str)
    """
    camShapeList = list()
    for cam in cameraTransformList:
        camShape = cameraShape(cam)
        if camShape:
            camShapeList.append(camShape)
    return camShapeList


def cameraTransformList(cameraShapeList):
    """Returns the camera transform node list given a camera shape node list

    :param cameraShapeList: List of many camera shape node names
    :type cameraShapeList: list(str)
    :return cameraTransformList: List of maya camera transform node names
    :rtype cameraTransformList: list(str)
    """
    return cmds.listRelatives(cameraShapeList, parent=True, fullPath=True)


def duplicateCamera(camera):
    """ Duplicate Camera

    :param camera:
    :type camera:
    :return: Returns long string
    :rtype:
    """
    return cmds.duplicate(camera)


def createCameraZxy(camName="", message=True):
    """Creates a new Maya camera with the default rotation order set to zxy rather than xyz

    :param message: Report the message to the user?
    :type message: bool
    :return cameraName: The name of the camera created [cameraTransform, cameraShape]
    :rtype cameraName: [str, str]
    """
    # todo maybe return zapi objects instead
    if camName:
        cameraName = cmds.camera(name=camName)
    else:
        cameraName = cmds.camera()
    cmds.setAttr(cameraName[0] + ".rotateOrder", 2)
    if message:
        om2.MGlobal.displayInfo("Success: Camera created with `zxy` gimbal rotation order")
    return cameraName


def createCameraNodesZxy(camName="", message=True):
    """Creates a new Maya camera with the default rotation order set to zxy rather than xyz

    :param message: Report the message to the user?
    :type message: bool
    :return cameraName: The dag nodes of the camera and the cameraShape
    :rtype cameraName: [, str]
    """
    if camName:
        cameraName = cmds.camera(name=camName)
    else:
        cameraName = cmds.camera()
    cmds.setAttr(cameraName[0] + ".rotateOrder", 2)
    if message:
        om2.MGlobal.displayInfo("Success: Camera created with `zxy` gimbal rotation order")
    return zapi.nodesByNames(cameraName)


def lookThrough(cameraTransform):
    """Look through this camera, helper function, use the straight cmds one liner

    :param cameraTransform: A camera transform name
    :type cameraTransform: str
    """
    cmds.lookThru(cameraTransform)


def getFocusCamera(prioritizeUnderCursor=True, message=True):
    """returns the camera that is under the cursor, or if error return the camera in the active window (with focus)

    :param message: report a potential fail message to the user?
    :type message: bool
    :return camera: The name of the Maya camera transform under the current panel
    :rtype camera: str
    """
    mayaPanel = viewportmodes.panelUnderPointerOrFocus(viewport3d=True, prioritizeUnderCursor=prioritizeUnderCursor,
                                                       message=False)  # underPointer or if none then withFocus
    if not mayaPanel:  # viewport isn't 3d
        if message:
            om2.MGlobal.displayWarning("No camera found under the cursor or in the currently active viewport,"
                                       "move the mouse over, or activate a viewport.")
        return ""
    camera = cmds.modelPanel(mayaPanel, query=True, camera=True)  #  Can be a transform or shape node
    if camera:
        if cmds.objectType(camera) == "camera":  # Then is a shape node, return the transform
            camera = cmds.listRelatives(camera, parent=True, type="transform")[0]
    return camera


def getFocusCameraShape(prioritizeUnderCursor=True, message=True):
    """returns the camera shape under the cursor, or if error return the camera in the active window (with focus)

    :param message: report a potential fail message to the user?
    :type message: bool
    :return cameraShape: The name of the Maya camera shape under the current panel
    :rtype cameraShape: str
    """
    cameraTransform = getFocusCamera(prioritizeUnderCursor=prioritizeUnderCursor, message=message)
    if cameraTransform:
        return cameraShape(cameraTransform)
    return ""


def selectCamInView(message=True):
    """Selects the camera under the pointer or if an error, get the camera in active panel, if error return message

    Use this on a hotkey

    :return camera: camera transform name that was selected, empty string if None
    :rtype camera: str
    """
    camera = getFocusCamera()
    if not camera:
        if message:
            om2.MGlobal.displayInfo("No Active Camera Found")
        return ""
    cmds.select(camera, replace=True)
    if message:
        om2.MGlobal.displayInfo("Camera Selected: {}".format(camera))
    return camera


def filterCameraType(camShapeList, camType=CAM_TYPE_ALL):
    """from a camera shape list filter out the cameras by type:

        CAM_TYPE_ALL = "all"
        CAM_TYPE_PERSP = "perspective"
        CAM_TYPE_ORTHOGRAPHIC = "orthographic"

    All will return the whole list.

    :param camShapeList: A list of camera shape nodes
    :type camShapeList: list(str)
    :param camType: Which type to filter, "all", "perspective" or "orthographic"
    :type camType: str

    :return: A list of camera shape nodes now filtered
    :rtype: list(str)
    """
    camFilterList = list()
    if camType == CAM_TYPE_ALL:  # if "all" then skip the filter
        return camShapeList
    for camShape in camShapeList:
        if cmds.getAttr("{}.orthographic".format(camShape)):  # is orthographic
            if camType == CAM_TYPE_ORTHOGRAPHIC:
                camFilterList.append(camShape)
        else:  # is persp
            if camType == CAM_TYPE_PERSP:
                camFilterList.append(camShape)
    return camFilterList


def cameraTransformsSelected(longName=True):
    """From the selection only return the camera transform nodes as a list, will be an empty list if none.

    :param longName: Forces long names rather than unique names if False
    :type longName: bool

    :return camTransformList: camera transform nodes as a list of names, will be empty list if None in selection
    :rtype camTransformList: list(str)
    """
    camTransformList = list()
    selObjs = cmds.ls(selection=True, long=longName)
    if not selObjs:
        return camTransformList
    for obj in selObjs:
        shapes = cmds.listRelatives(obj, shapes=True, fullPath=True, type="camera")
        if shapes:
            camTransformList.append(obj)
    return camTransformList


def cameraShapesSelected(longName=True):
    """From the selection only return the camera shape nodes as a list, will be an empty list if none.

    :param longName: Forces long names rather than unique names if False
    :type longName: bool

    :return camShapeList: camera shape nodes as a list of names, will be empty list if None in selection
    :rtype camShapeList: list(str)
    """
    camShapeList = list()
    camTransformList = cameraTransformsSelected(longName=longName)
    if not camTransformList:
        return camShapeList
    for cam in camTransformList:
        camShapeList.append(cameraShape(cam))
    return camShapeList


def cameraShapesAll(longName=True):
    """Returns all camera shapes in the whole scene

    :param longName: Forces long names rather than unique names if False
    :type longName: bool

    :return camShapeList: all camera shape names in the scene
    :rtype camShapeList: list
    """
    return cmds.ls(type='camera', long=longName)


def cameraTransformsAll(camType=CAM_TYPE_ALL, longname=True):
    """ Returns all camera transforms in the whole scene:

        CAM_TYPE_ALL = "all" returns all
        CAM_TYPE_PERSP = "perspective"
        CAM_TYPE_ORTHOGRAPHIC = "orthographic"

    :param camType: Which type to filter, "all", "perspective" or "orthographic"
    :type camType: str
    :return camTransformList: all camera transform names in the scene
    :rtype camTransformList: list[str]
    """
    allCamShapes = cameraShapesAll()
    if not allCamShapes:
        return list()
    camShapeList = filterCameraType(allCamShapes, camType=camType)
    return objhandling.getListTransforms(camShapeList, longName=longname)


def allCamTransformsDag(camType=CAM_TYPE_ALL):
    """ Returns all camera transforms in the whole scene

    Same as AllCamTransforms except it returns the dag node

    :param camType:
    :type camType:
    :return:
    :rtype: list[zoo.libs.maya.zapi.DagNode]
    """
    return list(zapi.nodesByNames(cameraTransformsAll(camType=camType)))


def getStartupCamShapes(includeLeftBot=True):
    """Returns all the startup cameras in the scene as shape node name list
    ["perspShape", "topShape", "sideShape", "frontShape", "leftShape", "bottomShape"]

    :return startupCamShapeList: list of default maya camera shape nodes
    :rtype startupCamShapeList: list
    returns long names
    """
    camShapeList = cameraShapesAll()
    startupCamShapeList = list()
    for camShape in camShapeList:
        if cmds.camera(cmds.listRelatives(camShape, parent=True)[0], startupCamera=True, q=True):
            startupCamShapeList.append(camShape)
    if not includeLeftBot:
        return startupCamShapeList
    for cam in OTHERCAMDEFAULTS:
        camShape = "{}Shape".format(cam)
        if cmds.objExists(camShape):
            startupCamShapeList.append(camShape)
    return startupCamShapeList


def camFromCamShape(camShape):
    """ Get the camera transform from the camShape

    :param camShape:
    :type camShape:
    :return:
    :rtype:
    """
    # feels like there should be a better way to doing this
    return cmds.listRelatives(camShape, parent=True)[0]


def getStartupCamTransforms():
    """Returns all the startup cameras in the scene as transform node name list
    ["persp", "top", "side", "front", "left", "bottom"]
    returns long names

    :return startupCamTransforms: list of startup (maya default) camera transform names
    :rtype startupCamTransforms: list
    """
    startupCamShapes = getStartupCamShapes()
    if startupCamShapes:
        return objhandling.getListTransforms(startupCamShapes)


def getUserCamShapes():
    """Returns all the camera shape nodes in the scene while filtering out the maya default cams
    returns long names

    :return userCamShapes: list of camera shape node names that aren't Maya default
    :rtype userCamShapes: list
    """
    camShapeList = cameraShapesAll()
    startupCamShapeList = getStartupCamShapes()
    return list(set(camShapeList) - set(startupCamShapeList))


def getUserCamTransforms(camType=CAM_TYPE_ALL):
    """Returns all the camera transform nodes in the scene while filtering out the maya default cams
    returns long names:

        CAM_TYPE_ALL = "all" returns all
        CAM_TYPE_PERSP = "perspective"
        CAM_TYPE_ORTHOGRAPHIC = "orthographic"

    :param camType: Which type to filter, "all", "perspective" or "orthographic"
    :type camType: str
    :return cameraTransformList: All the camera transforms that aren't maya default cams
    :rtype cameraTransformList: list
    """
    userCamShapes = getUserCamShapes()
    if not userCamShapes:
        return list()
    camShapeList = filterCameraType(userCamShapes, camType=camType)
    return objhandling.getListTransforms(camShapeList)


# -------------------
# Toggles
# -------------------


def toggleCamResGate(camShape=None, resGateOnly=True):
    """Toggles the resolution gate On/Off on a cameraShape of if None then auto find the current camera.

    If filmgateOnly is False will:

        Sets the filmFit to "Overscan"
        Sets the res gate overscan of 1.05
        Sets film gate to match resolution gate
        Opacity is set to 50 percent grey

    :param camShape: The cameraShape node to toggle
    :type camShape: str
    :param resGateOnly: Will only toggle the film gate
    :type resGateOnly: bool
    :return: Returns if it was turned on or off
    """
    if camShape is None:
        camera = getFocusCamera()
        if not camera:
            return  # Message already reported
        camShape = cameraShape(camera)
    resGate = resolutionGate(camShape)

    # toggle the resGate and the filmFit
    newState = not resGate  # toggle
    setCamResGate(camShape, newState, resGateOnly)
    return newState


def resolutionGate(camShape):
    """ Gets the resolution gate of the camera shape and returns it as a boolean

    :param camShape:
    :type camShape:
    :return:
    :rtype:
    """
    return bool(cmds.getAttr('{}.displayResolution'.format(camShape)))


def filmGate(camShape):
    """Shows the film gate display True or False (1 or 0)

    :param camShape: A maya camShape node
    :type camShape: str
    :return value: Shows the film gate display True or False (1 or 0)
    :rtype value: bool
    """
    return cmds.getAttr('{}.displayFilmGate'.format(camShape))


def gateMask(camShape):
    """Gets the gate display

    :param camShape: A maya camShape node
    :type camShape: str
    :return gateMaskValue: Shows the gate display True or False (1 or 0)
    :rtype gateMaskValue: bool
    """
    return cmds.getAttr('{}.displayGateMask'.format(camShape))


def setCamResGate(camShape, on=True, resGateOnly=True, message=True):
    """ Sets camera resolution gate visibility

    :param camShape: A maya camera shape node
    :type camShape: str
    :param on: True sets the resolution gate on
    :type on: bool
    :param resGateOnly: Only sets the resGate, does not set the Zoo defaults
    :type resGateOnly: bool
    :param message: Report a message to the user?
    :type message: bool
    """
    if on:
        out = "On"
    else:
        out = "Off"

    if resGateOnly:  # Only toggle the resGate, skip Zoo settings
        setCamResolutionGate(camShape, int(on))
        if message:
            om2.MGlobal.displayInfo('Success: `{}` resolution gate {}'.format(camShape, out))
        return

    setZooResolutionGate(camShape, resolutionGate=on)
    setCamFitResGate(camShape, fitResolutionGate=CAM_FIT_RES_OVERSCAN)
    if message:
        om2.MGlobal.displayInfo('Success: `{}` resolution gate {}, film gate matched'.format(camShape, out))


def toggleOverscan():
    """Toggles the camera `overscan` attribute of the camera between 1 and 1.05
    """
    camShape = getFocusCameraShape()
    if not camShape:
        return  # Message already reported
    overscan = cmds.getAttr('{}.overscan'.format(camShape))
    if overscan == 1:
        overscan = 1.05
        setCamOverscan(camShape, overscan)
    else:
        overscan = 1.0
        setCamOverscan(camShape, overscan)
    om2.MGlobal.displayInfo('Success: `{}` Overscan set to {}'.format(camShape, str(overscan)))


# -------------------
# Set Current Camera
# -------------------


def setCurrCamClipPlanes(nearClip, farClip):
    """Sets the Near and Far clip planes on the current camera

    :param nearClip: The near clip plane for the camera
    :type nearClip: float
    :param farClip: The far clip plane for the camera
    :type farClip: float
    """
    camera = getFocusCamera()
    if not camera:
        return  # Message already reported
    camShape = cameraShape(camera)
    setCamClipPlanes(camShape, nearClip, farClip)
    om2.MGlobal.displayInfo("Success: `{}` clipping planes set to "
                            "Near `{}` and Far `{}`".format(camera, nearClip, farClip))


# -------------------
# Set Camera Attributes
# -------------------


def createZooApertureAttrs(camShape):
    """Adds the custom attributes "zooApertureWidthInches" and "zooApertureHeightInches" and set their values from the \
    Maya camera settings.

    The attrs are used to store and measure the film gate size (camera sensor size) by zoo tools which will override \
    Maya's settings.

    :param camShape: The name of the camera's shape node
    :type camShape: str

    :return: inchesWidth: value in inches
    :rtype: inchesWidth: float
    :return: inchesHeight: value in inches
    :rtype: inchesHeight: float
    """
    inchesWidth = cmds.getAttr("{}.horizontalFilmAperture".format(camShape))
    inchesHeight = cmds.getAttr("{}.verticalFilmAperture".format(camShape))

    if not cmds.attributeQuery(ZOO_APERTURE_INCH_HEIGHT_ATTR, node=camShape, exists=True):  # may exist earlier version
        cmds.addAttr(camShape, longName=ZOO_APERTURE_INCH_WIDTH_ATTR, attributeType='float')
        cmds.addAttr(camShape, longName=ZOO_APERTURE_INCH_HEIGHT_ATTR, attributeType='float')
        cmds.setAttr("{}.{}".format(camShape, ZOO_APERTURE_INCH_WIDTH_ATTR), inchesWidth)
        cmds.setAttr("{}.{}".format(camShape, ZOO_APERTURE_INCH_HEIGHT_ATTR), inchesHeight)
    # add the boolean and the remember combo
    cmds.addAttr(camShape, longName=ZOO_APERTURE_BOOL, attributeType='bool')
    cmds.setAttr("{}.{}".format(camShape, ZOO_APERTURE_BOOL), False)
    cmds.addAttr(camShape, longName=ZOO_APERTURE_PREVIOUS_FIT, attributeType='enum', enumName=ZOO_FIT_LIST)
    return inchesWidth, inchesHeight


def matchResolutionFilmGate(camShape, fitResGate=CAM_FIT_RES_OVERSCAN, getZooGate=True, matchGates=True):
    """Automatically sets the aspect ratio of the camera to the render globals by doing the math on \
    verticalFilmAperture and horizontalFilmAperture.

    :param camShape: The name of the camera's shape node
    :type camShape: str
    :param fitResGate: Sets the Fit Resolution Gate setting, usually to "overscan"
    :type fitResGate: int
    """
    gateWidth, gateHeight, gateRatio = sensorSizeInches(camShape, getZooGate=getZooGate)
    resolutionWidth, resolutionHeight, resRatio = renderGlobalsWidthHeight()
    matchResolutionInsideFilmGate(camShape, resolutionWidth, resolutionHeight, resRatio, gateWidth, gateHeight,
                                  gateRatio)
    if matchGates:
        setCamFitResGate(camShape, fitResolutionGate=fitResGate)  # change to film Gate fit to overscan


def setZooResolutionGate(camShape, resolutionGate=True, overscan=1.05, matchResGateRatios=True,
                         gateMaskOpacity=0.5, affectGateMask=True, fitResGate=CAM_FIT_RES_OVERSCAN):
    """Sets resolution gate with default Zoo settings:

        - overscan
        - gateMaskOpacity
        - matchResGateRatios
        - gateMaskOpacity
        - fitResGate

    :param camShape: A maya camShape node
    :type camShape: str
    :param resolutionGate: Show the resolution in the window or not
    :type resolutionGate: bool
    :param overscan: Space between the resolution gate and the window.
    :type overscan: float
    :param matchResGateRatios: Automatically sets the camera's film back to match the resolution
    :type matchResGateRatios:
    :param gateMaskOpacity: The opacity of the mask around the camera if a mask is on
    :type gateMaskOpacity: float
    :param affectGateMask: If True set the gateMaskOpacity
    :type affectGateMask: float
    """
    setCamResolutionGate(camShape, resolutionGate)
    setCamOverscan(camShape, overscan)
    if affectGateMask:
        setCamGateMaskOpacity(camShape, gateMaskOpacity)
    if matchResGateRatios:
        matchResolutionFilmGate(camShape, fitResGate=fitResGate)
        # setCamFitResGate(camShape, fitResolutionGate=fitResGate)


def matchResolutionInsideFilmGate(camShape, resolutionWidth, resolutionHeight, resRatio, gateWidth, gateHeight,
                                  gateRatio):
    """Takes into consideration the camera's sensor (film gate) settings in mm and automatically fits the resolution \
    to fit inside of the sensor aspect ratio

    :param camShape: The camera shape name
    :type camShape: str
    :param resolutionWidth: The scene resolution width
    :type resolutionWidth: float
    :param resolutionHeight: The scene resolution height
    :type resolutionHeight: float
    :param resRatio: The aspect ratio width/height of the resolution Eg. 1.7777
    :type resRatio: float
    :param gateWidth: The current film gate width
    :type gateWidth: float
    :param gateHeight: The current film gate height
    :type gateHeight: float
    :param gateRatio: The aspect ratio width/height of the film gate Eg. 1.7777
    :type gateRatio: float
    """
    if gateRatio > resRatio:  # fit vertical
        matchCamFilmBackRatio(camShape, resRatio, keepVerticalSensorSize=True)
    else:  # fit horizontal
        matchCamFilmBackRatio(camShape, resRatio, keepVerticalSensorSize=False)


def matchCamFilmBackRatio(camShape, ratio, keepVerticalSensorSize=False, useZooGate=True):
    """Matches the aspect ratio of the film gate to the scene resolution ratio

    Sets horizontalFilmAperture or verticalFilmAperture (width height)

    If useZooGate:

        Will use the Zoo Tools stored attributes instead of Maya's default to do all the calculations
        Zoo messes with Maya's sensor size, so it needs to stores and query it separately

    :param camShape: A maya camShape node
    :type camShape: str
    :param ratio: The aspect ratio width/height of the camera Eg. 1.7777
    :type ratio: float
    :param keepVerticalSensorSize: The vertical height sensor size of the camera is kept, otherwise horizontal
    :type keepVerticalSensorSize: float
    :param useZooGate: The vertical height sensor size of the camera is kept, otherwise horizontal
    :type useZooGate: float
    """
    # If querying the zoo attributes and they don't exist then create them
    if useZooGate and not cmds.attributeQuery(ZOO_APERTURE_BOOL, node=camShape, exists=True):
        createZooApertureAttrs(camShape)

    # Set the film aperture in width or height inches
    if keepVerticalSensorSize:  # Adjust the vertical film aperture to match the resolution ratio
        if useZooGate:  # Use Zoo's stored settings
            verticalFilmAperture = cmds.getAttr("{}.{}".format(camShape, ZOO_APERTURE_INCH_HEIGHT_ATTR))
            cmds.setAttr('{}.verticalFilmAperture'.format(camShape), verticalFilmAperture)
        else:  # Use maya's settings
            verticalFilmAperture = cmds.getAttr('{}.verticalFilmAperture'.format(camShape))
        cmds.setAttr('{}.horizontalFilmAperture'.format(camShape), verticalFilmAperture * ratio)
    else:  # Adjust the horizontal film aperture to match the resolution ratio
        if useZooGate:  # Use Zoo's stored settings
            horizontalFilmAperture = cmds.getAttr("{}.{}".format(camShape, ZOO_APERTURE_INCH_WIDTH_ATTR))
            cmds.setAttr('{}.horizontalFilmAperture'.format(camShape), horizontalFilmAperture)
        else:  # Use maya's settings
            horizontalFilmAperture = cmds.getAttr('{}.horizontalFilmAperture'.format(camShape))
        cmds.setAttr('{}.verticalFilmAperture'.format(camShape), horizontalFilmAperture * (1 / ratio))
    if useZooGate:  # set tracker Attr to True
        cmds.setAttr('.'.join([camShape, ZOO_APERTURE_BOOL]), True)
        cmds.setAttr('.'.join([camShape, ZOO_APERTURE_PREVIOUS_FIT]), cmds.getAttr('{}.filmFit'.format(camShape)))


def unmatchCamFilmBackRatio(camShape):
    """Unmatches the film gate only after it has been set by zoo tools. Requires Zoo custom attrs on cameras.

    :param camShape: A maya camShape node
    :type camShape: str
    """
    if not cmds.attributeQuery(ZOO_APERTURE_BOOL, node=camShape, exists=True):
        createZooApertureAttrs(camShape)
        return
    horizontalFilmAperture = cmds.getAttr("{}.{}".format(camShape, ZOO_APERTURE_INCH_WIDTH_ATTR))
    verticalFilmAperture = cmds.getAttr("{}.{}".format(camShape, ZOO_APERTURE_INCH_HEIGHT_ATTR))
    cmds.setAttr('{}.verticalFilmAperture'.format(camShape), verticalFilmAperture)
    cmds.setAttr('{}.horizontalFilmAperture'.format(camShape), horizontalFilmAperture)
    cmds.setAttr('{}.{}'.format(camShape, ZOO_APERTURE_BOOL), False)  # Set tracker Attr to False
    cmds.setAttr('{}.filmFit'.format(camShape), cmds.getAttr('.'.join([camShape, ZOO_APERTURE_PREVIOUS_FIT])))


def zooMatchGateBoolValue(camShape):
    """Returns the value of the Zoo Aperture Boolean, a custom attribute that tracks the Match Gate state.

    :param camShape: A maya camShape node
    :type camShape: str
    :return zooMatchBoolValue: True if the cams are currently matched, False if not.
    :rtype zooMatchBoolValue: bool
    """
    if not cmds.attributeQuery(ZOO_APERTURE_BOOL, node=camShape, exists=True):
        try:  # not sure may error?
            createZooApertureAttrs(camShape)
        except:
            pass
        return False
    return cmds.getAttr('{}.{}'.format(camShape, ZOO_APERTURE_BOOL))

# -------------------
# Set Camera Attributes
# -------------------


def setSensorSizeInches(camShape, width, height, setZooGate=True):
    """Sets the sensor size (film gate) aperture width and height settings,

    If setZooGate True:

        Checks for the zoo custom attribute ZOO_APERTURE_BOOL if on then sets with
        matchResolutionFilmGate(camShape)

    :param camShape: A maya camShape node
    :type camShape: str
    :param width: The width of the sensor size (film gate) in inches
    :type width: float
    :param height: The height of the sensor size (film gate) in inches
    :type height: float
    :param setZooGate: If True will set with the Match Gate Zoo custom attributes
    :type setZooGate: bool
    """
    if setZooGate:
        if not cmds.attributeQuery(ZOO_APERTURE_BOOL, node=camShape, exists=True):
            createZooApertureAttrs(camShape)
        cmds.setAttr("{}.{}".format(camShape, ZOO_APERTURE_INCH_WIDTH_ATTR), width)
        cmds.setAttr("{}.{}".format(camShape, ZOO_APERTURE_INCH_HEIGHT_ATTR), height)
        if cmds.getAttr('{}.{}'.format(camShape, ZOO_APERTURE_BOOL)):  # if boolean is True
            # Now set the Maya settings
            matchResolutionFilmGate(camShape, matchGates=False)
            return
        # else continue
    cmds.setAttr("{}.horizontalFilmAperture".format(camShape), width)
    cmds.setAttr("{}.verticalFilmAperture".format(camShape), height)


def setSensorSizeMm(camShape, width, height, setZooGate=True):
    """Sets the sensor size (film gate) aperture width and height settings,

    If setZooGate True:

        Checks for the zoo custom attribute ZOO_APERTURE_BOOL if on then sets with
        matchResolutionFilmGate(camShape)

    :param camShape: A maya camShape node
    :type camShape: str
    :param width: The width of the sensor size (film gate) in mm
    :type width: float
    :param height: The height of the sensor size (film gate) in mm
    :type height: float
    :param setZooGate: If True will set with the Match Gate Zoo custom attributes
    :type setZooGate: bool
    """
    setSensorSizeInches(camShape, mmToInches(width), mmToInches(height), setZooGate=setZooGate)


def setCamResolutionGate(camShape, resolutionGate):
    """Sets the "resolutionGate" attribute on a camera shape.  Show the resolution in the window or not

    :param camShape: A maya camShape node
    :type camShape: str
    :param resolutionGate: Show the resolution in the window or not
    :type resolutionGate: bool
    """
    cmds.setAttr('{}.displayResolution'.format(camShape), resolutionGate)


def setCamFilmGate(camShape, value):
    """Shows the film gate display True or False (1 or 0)

    :param camShape: A maya camShape node
    :type camShape: str
    :param value: Shows the film gate display True or False (1 or 0)
    :type value: bool
    """
    cmds.setAttr('{}.displayFilmGate'.format(camShape), value)


def setGateMask(camShape, value):
    """Shows the gate display True or False (1 or 0)

    :param camShape: A maya camShape node
    :type camShape: str
    :param value: Shows the gate display True or False (1 or 0)
    :type value: bool
    """
    cmds.setAttr('{}.displayGateMask'.format(camShape), value)


def setCamGateMaskOpacity(camShape, gateMaskOpacity):
    """Sets the "gateMaskOpacity" attribute on a camera shape.  The opacity of the mask around the camera if on.

    :param camShape: A maya cameraShape node
    :type camShape: str
    :param gateMaskOpacity: The opacity of the mask around the camera if a mask is on
    :type gateMaskOpacity: float
    """
    cmds.setAttr('{}.displayGateMaskOpacity'.format(camShape), float(gateMaskOpacity))


def setCamOverscan(camShape, overscan=1.05):
    """Sets the "Overscan" attribute on a camera shape. Space between the resolution gate and the window.

    :param camShape: A maya cameraShape node
    :type camShape: str
    :param overscan: Space between the resolution gate and the window.
    :type overscan: float
    """
    cmds.setAttr('{}.overscan'.format(camShape), float(overscan))


def setCamFitResGate(camShape, fitResolutionGate=CAM_FIT_RES_OVERSCAN):
    """Sets the "Fit Resolution Gate" setting on a camera shape:

        CAM_FIT_RES_FILL = 0
        CAM_FIT_RES_HORIZONTAL = 1
        CAM_FIT_RES_VERTICAL = 2
        CAM_FIT_RES_OVERSCAN = 3

    :param camShape: A maya cameraShape node
    :type camShape: str
    :param fitResolutionGate: Integer of the setting to set 0 - 3
    :type fitResolutionGate: int
    """
    cmds.setAttr('{}.filmFit'.format(camShape), fitResolutionGate)


def setCamClipPlanes(camShape, nearClip, farClip):
    """Sets the Near and Far clip planes on a camera shape node

    :param camShape: A maya cameraShape node
    :type camShape: str
    :param nearClip: The near clip plane for the camera
    :type nearClip: float
    :param farClip: The far clip plane for the camera
    :type farClip: float
    """
    cmds.setAttr('{}.nearClipPlane'.format(camShape), float(nearClip))
    cmds.setAttr('{}.farClipPlane'.format(camShape), float(farClip))


def setCamMaskColor(camShape, srgbFloat=(0.5, 0.5, 0.5)):
    """Sets the camera gate mask color in SRGB Float range

    Color passed in as SRG and is applied as linear color (Maya takes linear)

    :param camShape: A maya camera shape node name
    :type camShape: str
    :param srgbFloat: A SRGB float color in 0 - 1.0 range eg (0.5, 0.5, 0.5)
    :type srgbFloat: tuple(float)
    """
    linearFloat = colour.convertColorSrgbToLinear(srgbFloat)
    cmds.setAttr('{}.displayGateMaskColor'.format(camShape), *linearFloat, type="double3")


def setPespectiveMode(camShape, perspMode):
    """

    :param camShape:
    :type camShape: basestring
    :param perspMode:
    :type perspMode: bool
    :return:
    :rtype:
    """
    cmds.setAttr('{}.orthographic'.format(camShape), int(not perspMode))


def setFocalLength(camShape, focalLength):
    cmds.setAttr("{}.focalLength".format(camShape), float(focalLength))


# -------------------
# Get Camera Attributes
# -------------------


def sensorSizeInches(camShape, getZooGate=True):
    """Returns the camera shape setting "Camera Aperture (mm)" height and width

    If getZooGate:

        Use zooTools custom attributes to query the camera's sensor size (film back), and does not use Maya's
        Also creates the custom attributes if they don't exist

    :param camShape: The name of the camera shape node
    :type camShape: str
    :param getZooGate: If the Zoo Tools custom attributes exist will use those values, if not will create/set attrs
    :type getZooGate: str

    :return widthInches: Height in mm value
    :rtype widthInches: float
    :return heightInches: Width in mm value
    :rtype heightInches: float
    """
    if getZooGate:
        if not cmds.attributeQuery(ZOO_APERTURE_BOOL, node=camShape, exists=True):
            createZooApertureAttrs(camShape)
        if cmds.getAttr('{}.{}'.format(camShape, ZOO_APERTURE_BOOL)):  # if boolean is True
            inchesWidth = cmds.getAttr("{}.{}".format(camShape, ZOO_APERTURE_INCH_WIDTH_ATTR))
            inchesHeight = cmds.getAttr("{}.{}".format(camShape, ZOO_APERTURE_INCH_HEIGHT_ATTR))
        else:  # If boolean is False, go with the Maya settings
            inchesWidth = cmds.getAttr("{}.horizontalFilmAperture".format(camShape))
            inchesHeight = cmds.getAttr("{}.verticalFilmAperture".format(camShape))
    else:  # No Zoo check go with defaults
        inchesWidth = cmds.getAttr("{}.horizontalFilmAperture".format(camShape))
        inchesHeight = cmds.getAttr("{}.verticalFilmAperture".format(camShape))
    ratio = inchesWidth / inchesHeight
    return inchesWidth, inchesHeight, ratio


def sensorSizeMm(camShape, getZooGate=True):
    """See documentation for sensorSizeInches() only returns in mm instead of inches
    """
    inchesWidth, inchesHeight, ratio = sensorSizeInches(camShape, getZooGate=True)
    return inchesToMm(inchesWidth), inchesToMm(inchesHeight), ratio


def calculateResSize(resolutionWidth, resolutionHeight, sensorWidth, sensorHeight, fitWidth=True):
    """

    :param resolutionWidth:
    :type resolutionWidth:
    :param resolutionHeight:
    :type resolutionHeight:
    :param sensorWidth:
    :type sensorWidth:
    :param sensorHeight:
    :type sensorHeight:
    :param fitWidth:
    :type fitWidth:
    :return:
    :rtype:
    """
    if fitWidth:
        width = sensorWidth
        height = width / (float(resolutionWidth) / float(resolutionHeight))
    else:
        height = sensorHeight
        width = height * (float(resolutionWidth) / float(resolutionHeight))
    return width, height


def resolutionSizeInches(camShape, getZooGate=True):
    """Calculates the cropped sensor size, or the actual resolution (rendered) sensor size in inches.

    This is only a read/get function there is no set equivalent.

    :param camShape: The name of the camera shape node
    :type camShape: str
    :param getZooGate: If the Zoo Tools custom attributes exist will use those values, if not will create/set attrs
    :type getZooGate: str

    :return width: The resolution width in inches
    :rtype width: float
    :return height: The resolution height in inches
    :rtype height: float
    """
    fitInt = camFitResGate(camShape)
    resolutionWidth, resolutionHeight, resRatio = renderGlobalsWidthHeight()
    sensorWidth, sensorHeight, sensorRatio = sensorSizeInches(camShape, getZooGate=False)
    if fitInt == CAM_FIT_RES_FILL:
        if resRatio > sensorRatio:  # Width
            return calculateResSize(resolutionWidth, resolutionHeight, sensorWidth, sensorHeight, fitWidth=True)
        else:  # Height
            return calculateResSize(resolutionWidth, resolutionHeight, sensorWidth, sensorHeight, fitWidth=False)
    elif fitInt == CAM_FIT_RES_HORIZONTAL:  # Width
        return calculateResSize(resolutionWidth, resolutionHeight, sensorWidth, sensorHeight, fitWidth=True)
    elif fitInt == CAM_FIT_RES_VERTICAL:  # Height
        return calculateResSize(resolutionWidth, resolutionHeight, sensorWidth, sensorHeight, fitWidth=False)
    else:  # Over scan
        if resRatio > sensorRatio:  # Height
            return calculateResSize(resolutionWidth, resolutionHeight, sensorWidth, sensorHeight, fitWidth=False)
        else:  # Width
            return calculateResSize(resolutionWidth, resolutionHeight, sensorWidth, sensorHeight, fitWidth=True)


def resolutionSizeMm(camShape, getZooGate=True):
    """See documentation for resolutionSizeInches() only returns in mm instead of inches
    """
    widthInches, heightInches = resolutionSizeInches(camShape, getZooGate=True)
    return inchesToMm(widthInches), inchesToMm(heightInches)


def camClipPlanes(camShape):
    """ Get the camClipPlanes and

    :param camShape: Cam shape as long name
    :type camShape: basestring
    :return camClipPlanes: The near and far clip planes as floats
    :rtype camClipPlanes: tuple [float, float]
    """
    near = cmds.getAttr("{}.nearClipPlane".format(camShape))
    far = cmds.getAttr("{}.farClipPlane".format(camShape))

    return (near, far)


def camFitResGate(camShape):
    """Get the fit resolution attribute value as an index

    :param camShape: Cam shape as long name
    :type camShape: basestring
    :return filmFitValue: The value of the Fit Resolution Gate combo box in the attr editor
    :rtype filmFitValue: int
    """
    return cmds.getAttr('{}.filmFit'.format(camShape))


def focalLength(camShape):
    """ Get the focal length of the camShape

    :param camShape: Cam shape as long name
    :type camShape: basestring
    :return focalLength: The focal length of the current camera
    :rtype focalLength: float
    """
    return cmds.getAttr("{}.focalLength".format(camShape))


def isPerspective(camShape):
    """ Returns if camShape is perspective or orthographic. Perspective if true, false if ortho

    :param camShape: Cam shape as long name
    :type camShape: basestring
    :return isPerspective: True if the cmaera is a perspective cam, False if Orthographic
    :rtype isPerspective: bool
    """
    return not bool(cmds.getAttr("{}.orthographic".format(camShape)))


def maskOpacity(camShape):
    """ Get the mask opacity from the cam shape

    :param camShape: Cam shape as long name
    :type camShape: basestring
    :return maskOpacity: The opacity of the mask
    :rtype maskOpacity: float
    """
    return cmds.getAttr("{}.displayGateMaskOpacity".format(camShape))


def overscan(camShape):
    """ Get overscan of cam shape

    :param camShape: Cam shape as long name
    :type camShape: basestring
    :return overscan: The amount of mask overscan on the camera
    :rtype overscan: float
    """
    return cmds.getAttr("{}.overscan".format(camShape))


def camMaskColor(camShape):
    """ Get Mask Color from cam shape

    :param camShape: Cam shape as long name
    :type camShape: basestring
    :return camMaskColor:  The color of the mask in linear float (0.3, 1.0, 0.0) etc
    :rtype camMaskColor: list(float)
    """
    return cmds.getAttr("{}.displayGateMaskColor".format(camShape))


# -------------------
# Render Globals
# -------------------


def renderGlobalsWidthHeight():
    """Returns the width and height of the render globals

    :return width: The height of the render settings in pixels
    :rtype: int
    :return height: The width of the render settings in pixels
    :rtype: int
    :return ratio: The ratio of the camera width/height Eg. 1.77
    :rtype: float
    """
    width = cmds.getAttr('defaultResolution.width')
    height = cmds.getAttr('defaultResolution.height')
    ratio = float(width) / float(height)
    return (width, height, ratio)


# -------------------
# Tear Off Cameras
# -------------------


def setGlobalsWidthHeight(width, height, matchCurrentCam=False, fitResGate=CAM_FIT_RES_OVERSCAN,
                          updateAllMatchedCams=True, message=True):
    """Sets the width and height of the render globals

    Optional sets the aspect ratio of the camera film back of the current camera

    :return width: The height of the render settings in pixels
    :rtype: int
    :return height: The width of the render settings in pixels
    :rtype: int
    :param matchCurrentCam: Change the ratio of the current camera?
    :type matchCurrentCam: bool
    :param message: Report the message to the user?
    :type message: bool
    """
    ratioMessage = ""
    ratio = float(width) / float(height)
    # Set Maya globals
    cmds.setAttr('defaultResolution.width', int(width))
    cmds.setAttr('defaultResolution.height', int(height))
    cmds.setAttr('defaultResolution.deviceAspectRatio', ratio)
    if updateAllMatchedCams:
        allCamShapes = cameraShapesAll()
        for camShape in allCamShapes:
            if zooMatchGateBoolValue(camShape):
                matchResolutionFilmGate(camShape)
    if matchCurrentCam:  # Set the focus camera's film gate to match
        camera = getFocusCamera()
        if not camera:
            return
        camShape = cameraShape(camera)
        setZooResolutionGate(camShape,
                             resolutionGate=True,
                             overscan=1.05,
                             matchResGateRatios=True,
                             affectGateMask=False,
                             fitResGate=fitResGate)
        ratioMessage = '"{}" film gate matched to {} aspect ratio of the ' \
                       'resolution gate'.format(camera, round(ratio, 3))
    if message:
        om2.MGlobal.displayInfo('Success: Render globals set to {} x {}. {}'.format(width, height, ratioMessage))


# -------------------
# Tear Off Cameras
# -------------------


def openTearOffCam(camera='persp', width=450, height=400):
    """Opens a tear off window looking through the designated camera.  Checks the scene to see if the camera exists.

    :param camera: The name of the camera transform node
    :type camera: str
    :param width: The width of the window to open in pixels
    :type width: int
    :param height: The height of the window to open in pixels
    :type height: int
    """
    if not cmds.objExists(camera):
        om2.MGlobal.displayWarning("Camera not found `{}`".format(camera))
        return
    shortName = camera.split("|")[-1]
    uiWindow = cmds.window(shortName)
    cmds.paneLayout()
    panel = cmds.modelPanel(camera=camera)
    cmds.showWindow(uiWindow)
    uiWindow = cmds.window(uiWindow, edit=True, widthHeight=(width, height))
    cmds.modelEditor(panel, edit=True, displayAppearance="smoothShaded")
    return uiWindow


def setDefaultDisplayAndCameras(focalLength=80, antiAlias=True, ambientOcclusion=True, adjustAspect=-True,
                                nearClip=0.9, farClip=5000):
    """Sets all perspective cameras to 80mm lens and matches the aspect ration of the camera filmback, also adjusts \
    clipping planes to medium values and turns on AO and antialiasing on in the viewport.

    :param focalLength: Set the focal length to all persp cameras to this value, if zero or None will skip
    :type focalLength: float
    :param antiAlias: Turns anti aliasing on or off
    :type antiAlias: bool
    :param ambientOcclusion: Turns viewport ambient occlusion on or off
    :type ambientOcclusion: bool
    :param adjustAspect: Automatically sets the aspect ratio of the camera to the render globals.
    :type adjustAspect: bool
    :param nearClip: The near clip plane of all perspective cams, if zero or None will skip setting the clip planes
    :type nearClip: float
    :param farClip: The far clip plane of all perspective cams, if zero or None will skip setting the clip planes
    :type farClip: float
    """
    if antiAlias:
        viewportmodes.enableAntiAliasMutliSample(enable=True)
    if ambientOcclusion:
        viewportmodes.setDisplayOcclusion(enable=True)
    camShapeList = cameraShapesAll()
    perpsCamShapeList = filterCameraType(camShapeList, camType=CAM_TYPE_PERSP)
    for perspShape in perpsCamShapeList:
        if adjustAspect:
            matchResolutionFilmGate(perspShape)
        if focalLength:
            cmds.setAttr("{}.focalLength".format(perspShape), focalLength)
        if nearClip and farClip:
            setCamClipPlanes(perspShape, nearClip, farClip)
    om2.MGlobal.displayInfo("Cameras changed lens/clip planes and aspect ratio for {}, "
                            "viewport anti alias and AO on".format(perpsCamShapeList))


def nodeLocked(name):
    defaultCams = ["persp", "top", "front", "side"]

    return name in defaultCams or cmds.lockNode(name, q=1)[0]
