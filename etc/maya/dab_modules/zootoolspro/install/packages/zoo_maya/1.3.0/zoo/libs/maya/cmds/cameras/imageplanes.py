from maya import cmds
from maya.api import OpenMaya as om2

from zoo.libs.maya.cmds.cameras import cameras
from zoo.libs.maya.cmds.objutils import namehandling, attributes

IMAGE_PLANE_LYR = "imagePlanes_lyr"

IP_FLOAT_ATTRS = ["depth", "offsetX", "offsetY", "sizeX", "sizeY", "alphaGain", "rotate"]

ORTH_ROT_OFFSET_DICT = {"frontShape": (0.0, 0.0, 0.0),
                        "backShape": (0.0, 180.0, 0.0),
                        "sideShape": (0.0, 90.0, 0.0),
                        "leftShape": (0.0, -90.0, 0.0),
                        "topShape": (-90.0, 0.0, 0.0),
                        "bottomShape": (90.0, 0.0, 0.0)}  # rotate offset to match orthographic cameras

def findLayer(layerName, matchAnyPartOfName=True):
    """Returns a list of layer names that match layerName

    If matchAnyPartOfName the search will look for *layerName*

    :param layerName: The name of the layer to return, if found in the scene
    :type layerName: str
    :param matchAnyPartOfName: if True the search will look for *layerName*
    :type matchAnyPartOfName: bool
    :return layers: A list of layers found, or epty list if not found
    :rtype layers: list
    """
    if not layerName:  # will set all layers
        layers = cmds.ls(long=True, type='displayLayer')
    elif matchAnyPartOfName:
        layers = cmds.ls("*{}*".format(layerName), long=True, type='displayLayer')
    else:
        layers = cmds.ls("{}".format(layerName), long=True, type='displayLayer')
    return layers


def setLayerVisibility(layerName, value, matchAnyPartOfName=True):
    """Sets the visibility value of the given layer

    :param layerName: The name of the Maya layer
    :type layerName: str
    :param value: True the layer is visible False is hidden
    :type value: bool
    :param matchAnyPartOfName: if True the search will look for *layerName*
    :type matchAnyPartOfName: bool
    """
    layers = findLayer(layerName, matchAnyPartOfName=True)
    if not layers:
        return
    for l in layers:
        cmds.setAttr("{}.visibility".format(l), value)


def toggleLayerVis(layerName, matchAnyPartOfName=True, message=True):
    """Toggles the visibility of a Maya Layer

    :param layerName: The name of the Maya layer
    :type layerName: str
    :param matchAnyPartOfName: if True the search will look for *layerName*
    :param message: Report the message to the user?
    :type message: bool
    :return layers: A list of layers found, or epty list if not found
    :rtype layers: list
    """
    layers = findLayer(layerName, matchAnyPartOfName=True)
    if not layers:
        return list()
    visState = cmds.getAttr("{}.visibility".format(layers[0]))
    for l in layers:
        cmds.setAttr("{}.visibility".format(l), not visState)
    if message:
        om2.MGlobal.displayInfo("Visibility set to '{}' Layers '{}' ".format(not visState, layers))
    return layers


def toggleLayerReference(layerName, matchAnyPartOfName=True, message=True):
    """Toggles the Reference state of a Maya Layer

    :param layerName: The name of the Maya layer
    :type layerName: str
    :param matchAnyPartOfName: if True the search will look for *layerName*
    :type matchAnyPartOfName: bool
    :param message: Report the message to the user?
    :type message: bool
    :return layers: A list of layers found, or epty list if not found
    :rtype layers: list
    """
    layers = findLayer(layerName, matchAnyPartOfName=True)
    if not layers:
        return list()
    displayType = cmds.getAttr("{}.displayType".format(layers[0]))
    if displayType == 0:
        for l in layers:
            cmds.setAttr("{}.displayType".format(l), 2)
        if message:
            om2.MGlobal.displayInfo("Display set to `Referenced Not Selectable` Layers '{}' ".format(layers))
    else:
        for l in layers:
            cmds.setAttr("{}.displayType".format(l), 0)
        if message:
            om2.MGlobal.displayInfo("Display set to `Regular Selectablity` Layers '{}' ".format(layers))
    return layers


def toggleVisImagePlaneLayer(matchAnyPartOfName=True, message=True):
    """Auto function that toggles the layer named IMAGE_PLANE_LYR, see toggleLayerVis() for documentation"""
    return toggleLayerVis(IMAGE_PLANE_LYR, matchAnyPartOfName=True, message=message)


def toggleRefImagePlaneLayer(matchAnyPartOfName=True, message=True):
    """Auto function that toggles the layer named IMAGE_PLANE_LYR, see toggleLayerReference() for documentation"""
    return toggleLayerReference(IMAGE_PLANE_LYR, matchAnyPartOfName=True, message=message)


# -----------------------------
# TRANSFORM & SHAPE
# -----------------------------


def getImagePlaneTransform(imagePlaneShape):
    """Returns the transform of an image plane

    :param imagePlaneShape: Name of an image plane shape node
    :type imagePlaneShape: str
    :return imagePlaneTransform: Name of the image plane's transform node
    :rtype imagePlaneTransform: str
    """
    imagePlaneParent = cmds.listRelatives(imagePlaneShape, parent=True, fullPath=True)[0]
    return imagePlaneParent


def getImagePlaneShape(imagePlaneTransform):
    """Returns the shape of an image plane

    :param imagePlaneTransform: Name of a image plane transform node
    :type imagePlaneTransform: str
    :return imagePlaneShape: Name of the image plane's shape node
    :rtype imagePlaneShape: str
    """
    imagePlaneShape = cmds.listRelatives(imagePlaneTransform, shapes=True, fullPath=True, type="imagePlane")[0]
    return imagePlaneShape


# -----------------------------
# ATTRIBUTES
# -----------------------------


def getImagePlaneAttrs(imagePlaneShape):
    """Returns a dictionary of all the image place major attribute values as found in IP_FLOAT_ATTRS and "imageName"

    :param imagePlaneShape: Name of the image plane shape node
    :type imagePlaneShape: str
    :return imagePlaneAttrDict: A dictionary containing the attribute names as keys and their value
    :rtype imagePlaneAttrDict: dict
    """
    imagePlaneAttrDict = dict()
    attrList = IP_FLOAT_ATTRS + ["imageName"]  # add the string attribute
    for attr in attrList:
        imagePlaneAttrDict[attr] = cmds.getAttr(".".join([imagePlaneShape, attr]))
    return imagePlaneAttrDict


def getImagePlaneAttrsAuto():
    """returns the image plane dictionary of attributes as keys:

        IP_FLOAT_ATTRS + ["imageName"]

    :return imagePlaneAttrDict: A dictionary containing the attribute names as keys and their value
    :rtype imagePlaneAttrDict: dict
    """
    iPShape, iPTransform, camShape = autoImagePlaneInfo()
    if not iPShape:
        return dict()
    return getImagePlaneAttrs(iPShape)


def getImagePlaneAttrsWithScaleAuto(message=True):
    """returns the image plane dictionary of attributes as keys:

        IP_FLOAT_ATTRS + ["imageName"] + ["scale"]

    The attribute "scale" does not exist on image planes so we do some math to figure it's value.

    :return imagePlaneAttrDict: A dictionary containing the attribute names as keys and their value
    :rtype imagePlaneAttrDict: dict
    """
    iPShape, iPTransform, camShape = autoImagePlaneInfo(message=message)
    if not iPShape:
        return dict()
    imagePlaneAttrDict = getImagePlaneAttrs(iPShape)
    imagePlaneAttrDict["scale"] = calculateCurrentSingleScale(iPShape)  # Gets the ratio
    return imagePlaneAttrDict


def setImagePlaneAttrs(iPShape, iPShapeAttrDict):
    """Sets the main attributes of an image plane from a imagePlaneAttrDict.

    Attribute names are found in  IP_FLOAT_ATTRS and the attribute "imageName"

    :param iPShape: Name of the image plane shape node
    :type iPShape: str
    :param iPShapeAttrDict: A dictionary containing the attribute names as keys and their value
    :type iPShapeAttrDict: dict
    """
    for attr in IP_FLOAT_ATTRS:
        cmds.setAttr(".".join([iPShape, attr]), iPShapeAttrDict[attr])
    cmds.setAttr(".".join([iPShape, "imageName"]), iPShapeAttrDict["imageName"], type="string")


def setImagePlaneAttrsAuto(iPShapeAttrDict):
    """Runs setImagePlaneAttrs() while automatically finding the current image plane, if None found then returns None.

    :param iPShapeAttrDict: A dictionary containing the attribute names as keys and their value
    :type iPShapeAttrDict: dict
    """
    iPShape, iPTransform, camShape = autoImagePlaneInfo(message=True)
    if iPShape:
        setImagePlaneAttrs(iPShape, iPShapeAttrDict)

    
# -----------------------------
# GET IMAGE PLANE SHAPES
# -----------------------------


def returnSelectedImagePlane(message=True):
    """Returns the image plane shape node name from a selected image plane shape or transform node

    :param message: Report the message to the user?
    :type message: bool
    :return imagePlane: image plane shape node name
    :rtype imagePlane: str
    """
    warningMessage = "Please Select an Image Plane"
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        if message:
            om2.MGlobal.displayWarning(warningMessage)
        return ""
    imagePlane = selObjs[0]
    if not cmds.objectType(imagePlane, isType="imagePlane"):  # then check the shape for an imagePlane node
        objList = cmds.listRelatives(imagePlane, shapes=True, fullPath=True, type="imagePlane")
        if not objList:
            if message:
                om2.MGlobal.displayWarning(warningMessage)
            return ""
        imagePlane = objList[0]  # will be an image plane
    return imagePlane


def imagePlanesConnectedToCamera(camShape):
    """Returns a list of image planes connected to a camera shape node, will be an empty list if None.

    :param camShape: maya camera shape node name
    :type camShape: str
    :return imagePlaneList: list of image planes connected to the camera
    :rtype imagePlaneList: list
    """
    imagePlaneStringList = cmds.listConnections(camShape, type="imagePlane") or []
    if not imagePlaneStringList:
        return imagePlaneStringList
    validIpList = list()
    shortNameCam = namehandling.getShortName(camShape)
    for imagePlane in imagePlaneStringList:
        if shortNameCam in imagePlane:  # then the image planes are attached to this camera
            validIpList.append(imagePlane)
    if not validIpList:  # no valid image planes found connected to the camera although others are in the scene
        return validIpList
    imagePlaneList = list()
    for i, ip in enumerate(imagePlaneStringList):
        imagePlaneList.append(ip.split('>')[+1])
    return imagePlaneList


def autoImagePlaneInfo(message=True):
    """Automatically gets the image plan either:

        1. From the selected image plane (either transform or shape node selection)
        2. From the camera with focus and the first connected image plane

    Returns: iPShape, iPTransform, camShape
    Returns: "", "", "" if nothing found

    :param message: Report the message to the user
    :type message: bool
    :return iPShape: The name of the image plane shape node
    :rtype iPShape: str
    :return iPTransform: The name of the image plane transform node
    :rtype iPTransform: str
    :return camShape: The name of the camera shape node with focus
    :rtype camShape: str
    """
    iPShape = returnSelectedImagePlane(message=False)
    camShape = cameras.getFocusCameraShape(prioritizeUnderCursor=False)
    if not iPShape:  # try getting one from the active camera
        if not camShape:
            if message:
                om2.MGlobal.displayWarning(
                    "Please make a 3d viewport active or select an image plane.  Image planes will "
                    "be created in the active viewport.")
            return "", "", ""
        imagePlaneList = imagePlanesConnectedToCamera(camShape)
        if not imagePlaneList:
            if message:
                om2.MGlobal.displayWarning(
                    "Please make a 3d viewport active or select an image plane.  Image planes will "
                    "be created in the active viewport.")
            return "", "", camShape
        iPTransform = imagePlaneList[0]
        iPShape = getImagePlaneShape(iPTransform)
    else:
        iPTransform = getImagePlaneTransform(iPShape)
        if not camShape:
            camShape = cmds.imagePlane(iPShape, query=True, camera=True)[0]
    return iPShape, iPTransform, camShape


# -----------------------------
# ASPECT RATIO
# -----------------------------

def imagePlaneScaleData(iPShape):
    cameraShape = cmds.imagePlane(iPShape, query=True, camera=True)[0]
    if not cameraShape:
        cameraShape = cameras.getFocusCameraShape()
        if not cameraShape:
            om2.MGlobal.displayWarning("Image Plane is not connected to a camera, please activate a view pane")
            return
    cameraApertureHorizontal = cmds.getAttr("{}.horizontalFilmAperture".format(cameraShape))
    cameraApertureVertical = cmds.getAttr("{}.verticalFilmAperture".format(cameraShape))
    imageWidth, imageHeight = cmds.imagePlane(iPShape, query=True, imageSize=True)
    imageWidth = float(imageWidth)
    imageHeight = float(imageHeight)
    cameraRatio = cameraApertureHorizontal / cameraApertureVertical
    if imageWidth:  # image width and height can be zero
        imageRatio = imageWidth / imageHeight
    else:
        imageRatio = 1
    return cameraApertureHorizontal, cameraApertureVertical, imageWidth, imageHeight, cameraRatio, imageRatio


def calculateDefaultImagePlaneScale(iPShape):
    """Gets the scale values when set to 1.0 will fill the camera.

    This function calculates the imagePlaneShape.sizeX and imagePlaneShape.sizeY values returning the
    imagePlaneShape.scaleX and imagePlaneShape.scaleY values which need to be calculated manually.

    The cameraAperture attributes are the camera canvas .horizontalFilmAperture x .verticalFilmAperture
    Then the image width x height
    With the both ratios of cameraAperture and imageSizes you can figure the longest image edge that fits the camera. \
    The max image edge will use the corresponding aperture value as it's default. Then the opposite dimension can be \
    calculated.

    Auto calculates the near and far clip planes from the attached camera

    :param iPShape: The name of a maya image plane shape node
    :type iPShape: str
    :return scaleX: The value of imagePlaneShape.scaleX if it fits 100%
    :rtype scaleX: float
    :return scaleY: The value of imagePlaneShape.scaleY if it fits 100%
    :rtype scaleY: float
    """
    cameraApertureHorizontal, cameraApertureVertical, imageWidth, imageHeight, \
    cameraRatio, imageRatio = imagePlaneScaleData(iPShape)
    if imageRatio < cameraRatio:  # Then image height is the max
        scaleY = cameraApertureVertical
        scaleX = cameraApertureVertical * (imageWidth / imageHeight)
    else:  # Then image width is the max
        scaleX = cameraApertureHorizontal
        scaleY = cameraApertureHorizontal * (imageHeight / imageWidth)
    return scaleX, scaleY


def calculateCurrentSingleScale(iPShape):
    """Gets the scale values when set to 1.0 will fill the camera."""
    cameraApertureHorizontal, cameraApertureVertical, imageWidth, imageHeight, \
    cameraRatio, imageRatio = imagePlaneScaleData(iPShape)
    sizeX = cmds.getAttr("{}.sizeX".format(iPShape))
    sizeY = cmds.getAttr("{}.sizeY".format(iPShape))
    if imageRatio < cameraRatio:  # Then image height is the max
        return sizeY/cameraApertureVertical
    # else image width is the max
    return sizeX/cameraApertureHorizontal


# -----------------------------
# ATTRIBUTES setting moving rot scale etc
# -----------------------------


def moveScaleImagePlane(iPShape, scale, offsetX, offsetY):
    """Moves/scales an image plane

    Scale is relative to the longest edge

    :param iPShape: Name of the image plane shape node
    :type iPShape: str
    :param scale: Scale is relative to the longest edge 0.0 - 1.0
    :type scale: float
    :param offsetX: The offset in X units
    :type offsetX: float
    :param offsetY: The offset in Y units
    :type offsetY: float
    """
    sizeX, sizeY = calculateDefaultImagePlaneScale(iPShape)
    cmds.setAttr("{}.sizeX".format(iPShape), sizeX * scale)
    cmds.setAttr("{}.sizeY".format(iPShape), sizeY * scale)
    cmds.setAttr("{}.offsetX".format(iPShape), offsetX)
    cmds.setAttr("{}.offsetY".format(iPShape), offsetY)


def moveScaleImagePlaneAuto(scale, offsetX, offsetY):
    """Moves/scales an image plane via selection or the camera with focus

    Scale is relative to the longest edge

    :param scale: Scale is relative to the longest edge 0.0 - 1.0
    :type scale: float
    :param offsetX: The offset in X units
    :type offsetX: float
    :param offsetY: The offset in Y units
    :type offsetY: float
    """
    iPShape, iPTransform, camShape = autoImagePlaneInfo(message=True)
    if iPShape:
        moveScaleImagePlane(iPShape, scale, offsetX, offsetY)


def rotImagePlaneAuto(rotate):
    """Rotates an image plane by automatically finding it via selection or from the focused camera

    :param rotate: Rotation absolute value in degrees
    :type rotate: float
    """
    iPShape, iPTransform, camShape = autoImagePlaneInfo(message=True)
    if iPShape:
        cmds.setAttr("{}.rotate".format(iPShape), rotate)


def scaleImagePlaneAuto(scale, message=True):
    """scales the image plane found automatically via the selection or from the camera with focus

    Scale is calculated where 1.0 fits the camera fully.

    :param scale: Scale is calculated where 1.0 fits the camera fully.  Absolute value
    :type scale: float
    :param message: return the message to the user?
    :type message: bool
    """
    iPShape, iPTransform, camShape = autoImagePlaneInfo(message=True)
    if iPShape:
        sizeX, sizeY = calculateDefaultImagePlaneScale(iPShape)
        cmds.setAttr("{}.sizeX".format(iPShape), sizeX * scale)
        cmds.setAttr("{}.sizeY".format(iPShape), sizeY * scale)


def opacityImagePlaneAuto(alphaGain, message=True):
    """Sets the alphaGain attr of the image plane found automatically via the selection or from the camera with focus

    :param alphaGain: The opacity (inverse transparency) of the image plane. 1.0 is opaque, 0.0 is transparent
    :type alphaGain: float
    :param message: return the message to the user?
    :type message: bool
    """
    iPShape, iPTransform, camShape = autoImagePlaneInfo(message=message)
    if iPShape:
        cmds.setAttr("{}.alphaGain".format(iPShape), alphaGain)


def offsetXImagePlaneAuto(offsetX, message=True):
    """Sets the alphaGain attr of the image plane found automatically via the selection or from the camera with focus

    :param offsetX: The offsetX attr value of the image plane. -.5 is left and +.5 is right
    :type offsetX: float
    :param message: return the message to the user?
    :type message: bool
    """
    iPShape, iPTransform, camShape = autoImagePlaneInfo(message=message)
    if iPShape:
        cmds.setAttr("{}.offsetX".format(iPShape), offsetX)


def offsetYImagePlaneAuto(offsetY, message=True):
    """Sets the alphaGain attr of the image plane found automatically via the selection or from the camera with focus

    :param offsetY: The offsetY attr value of the image plane. -0.5 is down and +0.5 is up
    :type offsetY: float
    :param message: return the message to the user?
    :type message: bool
    """
    iPShape, iPTransform, camShape = autoImagePlaneInfo(message=message)
    if iPShape:
        cmds.setAttr("{}.offsetY".format(iPShape), offsetY)


def placeInFrontAuto(message=True, divideDistance=5000):
    """Sets the image plane depth automatically based on the camera, moves it to the front with:

        nearDepth + (farDepth / divideDistance)

    :param divideDistance: return
    :type divideDistance:
    :param message: report the message to the user
    :type message: bool
    """
    iPShape, iPTransform, camShape = autoImagePlaneInfo(message=message)
    if iPShape:
        nearDepth = cmds.getAttr("{}.nearClipPlane".format(camShape))
        farDepth = cmds.getAttr("{}.farClipPlane".format(camShape))
        cmds.setAttr("{}.depth".format(iPShape), nearDepth + (farDepth / divideDistance))


def placeBehindAuto(message=True, divideDistance=100):
    """Sets the image plane depth automatically based on the camera, moves it to the far distance with:

        farDepth - (farDepth / divideDistance)

    :param divideDistance: return
    :type divideDistance:
    :param message: report the message to the user
    :type message: bool
    """
    iPShape, iPTransform, camShape = autoImagePlaneInfo(message=message)
    if iPShape:
        farDepth = cmds.getAttr("{}.farClipPlane".format(camShape))
        cmds.setAttr("{}.depth".format(iPShape), farDepth - (farDepth / divideDistance))


# -----------------------------
# ANIMATE (NOT SEQUENCE)
# -----------------------------


def animateImagePlane(fadeLength=6, minScale=0.4, offsetX=-0.45, offsetY=0.3, message=True):
    """Sets up an animated image plane ready for modelling or sculpting. This is not an image plane sequence

    Keys 7 frames:

        Frame 1: Image plane is small and top left in frame
        Frame 2: Image plane is far back, behind the model
        Frames will then fade from transparent to opaque base on `Frame Fades` value, default over 6 frames

    :param fadeLength: the amount of frames to fade the opacity of the image up from frame 3 to + fadeLength
    :type fadeLength: float
    :param minScale: The size of the image plane scaled from the max fit size
    :type minScale: float
    :param offsetX: The pos X offset of the image in x coords when up in the left corn of screen
    :type offsetX: float
    :param offsetY: The pos Y offset of the image in x coords when up in the left corn of screen
    :type offsetY: float
    :param message: Report the message to the user?
    :type message: bool
    """

    def keyImagePlane(time, imagePlane, sizeX, sizeY, depth, offsetX, offsetY, alpha, parentWarning):
        """Function for setting attributes and keyframes on the image plane
        """
        cmds.currentTime(time)
        if not parentWarning:  # camera is parented so adjust the offsets and depth
            cmds.setAttr("{}.sizeX".format(imagePlane), sizeX)
            cmds.setAttr("{}.sizeY".format(imagePlane), sizeY)
            cmds.setAttr("{}.depth".format(imagePlane), depth)
            cmds.setAttr("{}.offsetX".format(imagePlane), offsetX)
            cmds.setAttr("{}.offsetY".format(imagePlane), offsetY)
        cmds.setAttr("{}.alphaGain".format(imagePlane), alpha)
        cmds.setKeyframe()  # TODO should specify the node and attrs directly
    # Start
    parentWarning = False
    imagePlane = returnSelectedImagePlane()
    if not imagePlane:  # no image plane found
        return
    # image plane found, get near and far clip planes
    cameraShape = cmds.imagePlane(imagePlane, query=True, camera=True)[0]
    # Warnings --------------------------------
    if not cameraShape:
        cameraShape = cameras.getFocusCameraShape()
        parentWarning = True  # image plane is not parented to a camera
        if not cameraShape:
            om2.MGlobal.displayWarning("An image plane is not connected to a camera, "
                                       "activate a view pane image plane, or select an image plane")
            return
    if cmds.getAttr("{}.orthographic".format(cameraShape)):  # orthographic camera then disconnect
        om2.MGlobal.displayWarning("This camera `{}` is an orthographic camera, animated image planes is only "
                                   "compatible with perspective cameras".format(cameraShape))
        return
    if not cmds.imagePlane(imagePlane, query=True, camera=True)[0]:  # see if no camera attached
        om2.MGlobal.displayWarning("This image plane is not connected to a perspective camera")
        return
    # Animate --------------------------------
    nearDepth = cmds.getAttr("{}.nearClipPlane".format(cameraShape))
    farDepth = cmds.getAttr("{}.farClipPlane".format(cameraShape))
    nearDepth += farDepth / 5000
    farDepth -= farDepth / 100
    # other
    cmds.select(imagePlane, replace=True)  # could replace this am using selection for keyframes
    sizeX, sizeY = calculateDefaultImagePlaneScale(imagePlane)
    # Do the animation, frame 1 - 6
    keyImagePlane(1, imagePlane, sizeX * minScale, sizeY * minScale, nearDepth, offsetX, offsetY, 1.0, parentWarning)
    keyImagePlane(2, imagePlane, sizeX, sizeY, farDepth, 0, 0, 1.0, parentWarning)
    for i in range(3, int(fadeLength + 3.0)):
        alpha = (i - 2) / fadeLength
        keyImagePlane(i, imagePlane, sizeX, sizeY, nearDepth, 0, 0, alpha, parentWarning)
    cmds.currentTime(1)  # back to 1
    if message:  # success message
        if not parentWarning:
            om2.MGlobal.displayInfo("Success: Image Plane Animated `{}`".format(imagePlane))
        else:
            om2.MGlobal.displayWarning("Success: Image Plane Animated `{}`.  Note: image plane is not connected "
                                       "to a camera so will not move or scale".format(imagePlane))


# -----------------------
# CREATE & REBUILD
# -----------------------


def createImagePlane(camShape="", iPName="", matchToFilmGate=True):
    """Builds an image plane on a cameraShape

    camShape can be "" in which imagePlane will not be attached to a camera

    :param camShape: The name of the camera shape node, if "" will not be attached to a camera
    :type camShape: str
    :param iPName: The name of the image plane node to create, if "" then auto build name with Maya defaults
    :type iPName: str

    :return iPTransform: The name of the image plane transform node created
    :rtype iPTransform: str
    :return iPShape: The name of the image plane shape node created
    :rtype iPShape: str
    """
    if iPName:  # name the new image plane
        if not camShape:  # "" given don't assign
            iPTransform, iPShape = cmds.imagePlane(name=iPName)
        else:
            iPTransform, iPShape = cmds.imagePlane(camera=camShape, name=iPName)
    else:  # use default name while creating
        if not camShape:
            iPTransform, iPShape = cmds.imagePlane()
        else:
            iPTransform, iPShape = cmds.imagePlane(camera=camShape)
    return iPTransform, iPShape


def finalizeImagePlaneCreation(addToLayer, iPShape, camShape, moveToFarClip, detachOrthographic):
    """Used in createImagePlaneAuto() and rebuildImagePlane() to finish the image plane build or change:

        - if addToLayer: adds to a layer
        - if detachOrthographic: and camShape is an orthographic camera then disconnect it
        - if moveToFarClip the image plane to the far clip plane

    See documentation in createImagePlaneAuto()
    """
    if addToLayer:  # add image plane to a maya layer
        if not cmds.objExists(addToLayer):
            cmds.createDisplayLayer(name=addToLayer)
        cmds.editDisplayLayerMembers(addToLayer, iPShape)
    if moveToFarClip and camShape:  # move to just inside the far clip plane
        farDepth = cmds.getAttr("{}.farClipPlane".format(camShape))
        farDepth -= farDepth / 100
        cmds.setAttr("{}.depth".format(iPShape), farDepth)
    if detachOrthographic and camShape:  # Default Orthographic cameras don't have the image plane attached
        if cmds.getAttr("{}.orthographic".format(camShape)):  # orthographic camera
            camShapeShort = namehandling.getShortName(camShape)
            if camShapeShort in ORTH_ROT_OFFSET_DICT:  # is a Maya orthographic default camera so disconnect
                cmds.imagePlane(iPShape, edit=True, detach=True)
                # Must calculate the width and height manually
                imageWidth, imageHeight = cmds.imagePlane(iPShape, query=True, imageSize=True)
                width = 10 * (float(imageWidth) / float(imageHeight))
                cmds.setAttr("{}.width".format(iPShape), width)
                # orient offset for front, top, bottom, left, right, back
                iPTransform = cmds.listRelatives(iPShape, parent=True)[0]
                cmds.setAttr("{}.rotate".format(iPTransform),
                             ORTH_ROT_OFFSET_DICT[camShapeShort][0],
                             ORTH_ROT_OFFSET_DICT[camShapeShort][1],
                             ORTH_ROT_OFFSET_DICT[camShapeShort][2])


def createImagePlaneAuto(iPName="", iPPath="", forceCreate=False, message=True, addToLayer=IMAGE_PLANE_LYR,
                         moveToFarClip=True, detachOrthographic=True):
    """Creates an image plane if one is not already selected or attached to the current active viewport

    forceCreate = True will create a new image plane even if one already exists.

    Image planes are created on the current active perspective camera, or if orthographic are disconnected

    :param iPName: The name of the image plane node to create, if "" then auto build name with Maya fdefaults
    :type iPName: str
    :param iPPath: full path to an image to be assigned or changed on the image plane
    :type iPPath: str
    :param forceCreate: Always create a new image plane, if False will attempt to find existing image plane fist
    :type forceCreate: bool
    :param message: Report the message to the user?
    :type message: bool
    :return imagePlane: An image plane shape node name
    :rtype imagePlane: str
    """
    imagePlaneCreated = False
    # Get image plane details automatically from the selected or camera in focus -----------------------------------
    iPShape, iPTransform, camShape = autoImagePlaneInfo()  # returns selected IP or cam in focus first image plane
    # Create if needed or error with warning  --------------------------------
    if not iPShape and not iPTransform and not camShape:
        return "", imagePlaneCreated  # message already given
    elif not iPShape and camShape:  # there is a camera and no image plane so create it
        iPTransform, iPShape = createImagePlane(camShape, iPName="")
        imagePlaneCreated = True
    elif forceCreate and camShape:  # create a new image plane even if one already exists
        iPTransform, iPShape = createImagePlane(camShape, iPName="")
    elif iPShape and not camShape:  # then return the camera
        camShape = cmds.imagePlane(iPShape, query=True, camera=True)[0]
    # Change image  -----------------------------------
    if iPPath:
        moveToFarClip = False  # Changing so don't change the depth
        # If 2020.0 then is buggy so we need to rebuild, hopefully will be fixed in 2020.1
        if float(cmds.about(version=True)) == 2020.0 and not imagePlaneCreated and not forceCreate:
            return rebuildImagePlane(iPShape, iPTransform, iPPath, forceCreate, message, addToLayer,
                                     moveToFarClip, detachOrthographic, iPPath), imagePlaneCreated
        else:  # Or set the new image plane image if not 2020.0 (will check if this gets fixed in 2020.1)
            cmds.setAttr("{}.imageName".format(iPShape), iPPath, type="string")
        if message:
            om2.MGlobal.displayInfo("Success: Image set on set image plane `{}` "
                                    "image `{}`".format(iPShape, iPPath))
    else:  # All good so success
        if imagePlaneCreated:
            om2.MGlobal.displayInfo("Success: Image plane created `{}`".format(iPShape))
    # Add to layer, move to far clip plane, and if orthographic disconnect
    finalizeImagePlaneCreation(addToLayer, iPShape, camShape, moveToFarClip, detachOrthographic)
    return iPShape, imagePlaneCreated


def rebuildImagePlane(iPShape, iPTransform, imagePath, forceCreate, message, addToLayer, moveToFarClip,
                      detachOrthographic, iPPath):
    """Rebuilds an image plane while keeping the main settings,

    To fix bug in 2020.0 only :/ used in createImagePlaneAuto()

    See createImagePlaneAuto() for documentation
    """
    # Copy image plane attributes
    camShape = cmds.imagePlane(iPShape, query=True, camera=True)
    if camShape:
        camShape = camShape[0]
    else:
        camShape = ""  # not connected
    imagePlaneDict = getImagePlaneAttrs(iPShape)
    # Copy Transform attributes if orthographic
    if not camShape:
        srtAttrDict = attributes.srtAttrsDict(iPTransform)
    cmds.delete(iPTransform)  # should take the shape with it
    # Now rebuild the image plane as it needs to be rebuilt in 2020
    shortName = namehandling.getShortName(iPTransform)
    iPTransform, iPShape = createImagePlane(camShape, iPName=shortName)
    # Set attributes from copied image plane, and new path
    setImagePlaneAttrs(iPShape, imagePlaneDict)
    cmds.setAttr("{}.imageName".format(iPShape), imagePath, type="string")
    if not camShape:  # is most likely an orthographic, so will have no camera
        attributes.setFloatAttrsDict(iPTransform, srtAttrDict)
        # Must calculate the width and height manually
        imageWidth, imageHeight = cmds.imagePlane(iPShape, query=True, imageSize=True)
        width = 10 * (float(imageWidth) / float(imageHeight))
        cmds.setAttr("{}.width".format(iPShape), width)
    # Add to layer, move to far clip plane, and if orthographic disconnect
    finalizeImagePlaneCreation(addToLayer, iPShape, camShape, moveToFarClip, detachOrthographic)
    if message:
        om2.MGlobal.displayInfo("Success: Image set on set image plane `{}` "
                                "image `{}`".format(iPShape, iPPath))
    return iPShape
