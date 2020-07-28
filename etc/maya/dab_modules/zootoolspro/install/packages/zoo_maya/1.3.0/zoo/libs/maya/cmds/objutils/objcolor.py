"""
OBJ COLOR .py
Various functions for setting, retrieving and offsetting object colors, usually control curves for animation/rigging

This file handles the coloring of objects in Maya, most commonly for animator NURBS Controls also the wireframes
shape node or NURBS curves.  Transform nodes can be colored though this script affects shape nodes as a default.
Colors default to linear as per the Maya's viewport.
While using a UI or coming from a program like photoshop colors may be switched to srgb
Colors are not shader related.

Colors can be two types, Index (both numbers or strings), or RGB/HSV (color values)
RGB is in 0-1 range (0.5, 0.5, 0.5) defaults to linear color space
HSV is in 0-360 for hue, 0-1 for values and saturation (180.0, 0.5, 0.5) defaults to linear color space
"""

import maya.cmds as cmds
import maya.api.OpenMaya as om2

from zoo.libs.utils import colour
from zoo.libs.maya.utils.mayacolors import MAYA_COLOR_SRGB, MAYA_COLOR_LINEAR_RGB, MAYA_COLOR_NICENAMES
from zoo.libs.maya.cmds.objutils import shapenodes
from zoo.libs.utils import zlogging
from zoovendor.six import string_types


logger = zlogging.getLogger(__name__)


def convertColorMayaStringToInt(colorString):
    """Given a color nice name as string, return the Maya index number. 0 -30 ish
    Names are at the top of this file as global variable MAYA_COLOR_NICENAMES (list)

    :param colorString: Color as nice name
    :type colorString: str
    :return colorIndex: Maya's color as int (number)
    :type colorIndex: int
    """
    try:
        colorIndex = MAYA_COLOR_NICENAMES.index(colorString)
    except ValueError:
        return None
    return colorIndex


def convertColorMayaIntToRGB(colorIndex, linear=True):
    """Given a Maya Color Index Number return the RGB value

    :param colorIndex: Maya's index color
    :type colorIndex: int
    :param linear: If true return the color in linear space, matches the viewport
    :type linear: bool
    :return rgb: rgb values as a tuple of floats, all values in 0-1 range
    :rtype rgb: tuple
    """
    if linear:
        linRgb = MAYA_COLOR_LINEAR_RGB[colorIndex]
        return linRgb
    srgb = MAYA_COLOR_SRGB[colorIndex]
    return srgb


def convertColorMayaStringToRGB(colorString, linear=True):
    """Given a Maya Color string (nice name) return the RGB value

    :param colorString: Color as nice name
    :type colorString: str
    :param linear: If true return the color in linear space, matches the viewport
    :type linear: bool
    :return rgb: rgb values as a tuple of floats, all values in 0-1 range
    :rtype rgb: tuple
    """
    colorIndex = convertColorMayaStringToInt(colorString)
    if colorIndex:
        return convertColorMayaIntToRGB(colorIndex)
    else:
        return None


def getRgbColor(shape, hsv=False, linear=True, limitDecimalPlaces=False):
    """Returns the color of a shape node in rgb or hsv
    Nodes are usually shapes, can be transforms
    Can return rgb or hsv values, defaults rgb.  If RGB mode isn't on interprets the Maya Index color as RGB
    rgb = [.5, .5, .5]
    hsv = [180, .5, .5]
    Will return an empty list [] if .overrideRGBColors is off

    :param shape: the name of the node, usually a shape node, should be long names
    :type shape: str
    :param hsv: return the `hue saturation value` values rather than rgb which is the default
    :type hsv: bool
    :param linear: If true return the color in linear space, matches the viewport
    :type linear: bool
    :param limitDecimalPlaces: If true limits the decimal places to max of 3 ie .098
    :type limitDecimalPlaces: bool
    :return color: a list either hsv or rgb [float, float, float]
    :rtype: list
    """
    # check if in index color mode
    if not cmds.getAttr('{}.overrideEnabled'.format(shape)):  # override isn't on most likely maya default blue
        if linear:
            rgb = MAYA_COLOR_LINEAR_RGB[0]
        else:
            rgb = MAYA_COLOR_SRGB[0]
    elif not cmds.getAttr('{}.overrideRGBColors'.format(shape)):  # then index Maya mode, should convert
        mayaColor = cmds.getAttr('{}.overrideColor'.format(shape))
        if linear:
            rgb = MAYA_COLOR_LINEAR_RGB[mayaColor]
        else:
            rgb = MAYA_COLOR_SRGB[mayaColor]
    else:  # control is in rgb mode
        rgb = tuple([cmds.getAttr('{}.overrideColorR'.format(shape)),
                    cmds.getAttr('{}.overrideColorG'.format(shape)),
                    cmds.getAttr('{}.overrideColorB'.format(shape))])
        if not linear:
            rgb = colour.convertColorLinearToSrgb(rgb)
    if hsv:
        hsv = colour.convertRgbToHsv(rgb)
        return hsv
    if limitDecimalPlaces:  # then limit the decimal places
        rgb = list(rgb)
        for i, value in enumerate(rgb):
            rgb[i] = float("{0:.3f}".format(value))
        return tuple(rgb)
    return rgb


def getHsvColor(shape, linear=True):
    """Returns the color of the node if the attribute on the Maya node .overrideRGBColors is on
    Nodes are usually shapes, can be transforms
    Returns hsv values
    hsv = [180, .5, .5]
    Will return an empty list [] if .overrideRGBColors is off

    :param shape: the name of the node, usually a shape node
    :type shape: str
    :param linear: If true return the color in linear space, matches the viewport
    :type linear: bool
    :return hsv: a list either hsv or rgb [float, float, float]
    :rtype: list
    """
    return getRgbColor(shape, hsv=True, linear=linear)


def getIndexColor(shape):
    """Returns the shape's Index color value, blue if not enabled, None if rgb is on

    :param shape: name of the shape node
    :type shape: str
    :return mayaIndexColorInt: the color as a Maya number, if -1 the number is not applicable as is in rgb mode
    :rtype mayaIndexColorInt: int
    """
    if not cmds.getAttr('{}.overrideEnabled'.format(shape)):  # override isn't on most likely maya default blue
        return 0
    elif not cmds.getAttr('{}.overrideRGBColors'.format(shape)):  # then old style maya, should convert
        return cmds.getAttr('{}.overrideColor'.format(shape))
    else:  # shape is already in rgb so color doesn't apply
        return -1


def setColorShapeRgb(node, rgb, linear=True):
    """Colors a shape node with rgb values
    Override color in RGB values from Maya 2016+
    Switches override to on and to rgb colors

    :param node: The name of a single shape node
    :type node: str
    :param rgb: set/list of rgb values eg (.5, .5, .5)
    :type rgb: set/list
    :param linear: If true the rgb color is in linear space, matching the viewport, else convert it
    :type linear: bool
    """
    if not linear:
        rgb = colour.convertColorLinearToSrgb(rgb)
    cmds.setAttr('{}.overrideEnabled'.format(node), 1)
    cmds.setAttr('{}.overrideRGBColors'.format(node), 1)
    cmds.setAttr('{}.overrideColorR'.format(node), rgb[0])
    cmds.setAttr('{}.overrideColorG'.format(node), rgb[1])
    cmds.setAttr('{}.overrideColorB'.format(node), rgb[2])


def setColorShapeHsv(shape, hsv, linear=True):
    """Colors a shape node with hsv values

    :param shape: The name of a single shape node
    :type shape: str
    :param hsv: tuple of hsv values eg (180, .5, .5)
    :type hsv: list
    """
    rgb = colour.convertHsvToRgb(hsv)
    setColorShapeRgb(shape, rgb, linear=linear)


def setColorShapeIndex(shape, mayaColor):
    """Sets the color on a shape node in Index Maya Colors

    :param shape: Maya node, usually shape, can be transform node.
    :type shape: str
    :param mayaColor: The Index color that the object will change to, can be int or str
    :type mayaColor: str or int
    :return shape: Maya node, usually shape, could also be transform node.
    :rtype shape: str
    """
    if isinstance(mayaColor, string_types):  # if string, converts nice name string to Maya int
        mayaColor = convertColorMayaStringToInt(mayaColor)
    if mayaColor:
        try:  # sets rgb mode off, this could fail in older versions of Maya
            cmds.setAttr('{}.overrideRGBColors'.format(shape), 0)
        except:
            pass
        cmds.setAttr("{}.overrideEnabled".format(shape), 1)
        cmds.setAttr("{}.overrideColor".format(shape), mayaColor)
    return mayaColor


def setColorShapeIndexToRgb(shape, mayaColor, linear=True):
    """Given the color as an index (int) or Maya nice name (str) set the color of the shape in rgb mode

    :param shape: Maya node, usually shape, can be transform node.
    :type shape: str
    :param mayaColor: the color can be a string (nicename) or int/float
    :type mayaColor: str/int/float
    """
    if isinstance(mayaColor, string_types):  # converts nice name string to Maya int
        mayaColor = convertColorMayaStringToInt(mayaColor)
    rgb = convertColorMayaIntToRGB(mayaColor, linear=linear)
    setColorShapeRgb(shape, rgb=rgb)


def setColorListRgb(nodeList, rgb, colorShapes=True, displayMessage=True, linear=True):
    """sets the color of all object list's shape nodes to rgb color

    :param nodeList: list of Maya objects
    :type nodeList: list
    :param rgb: Red Green Blue, tuple of three numbers, float values 0-1
    :type rgb: list
    :param colorShapes: if True set the shapeNodes, otherwise set the exact list, often transforms
    :type colorShapes: bool
    :param displayMessage: display the message to the user?
    :type displayMessage: bool
    :param linear: If true the rgb color is in linear space, matching the viewport, else convert it
    :type linear: bool
    """
    if colorShapes:
        nodeList = shapenodes.filterShapesInList(nodeList)
    if not nodeList:
        if displayMessage:
            om2.MGlobal.displayWarning('Warning: No Valid Shape List Detected XX')
        return
    for shape in nodeList:
        setColorShapeRgb(shape, rgb, linear=linear)
    if displayMessage:
        om2.MGlobal.displayInfo("Success: Colors have been changed")


def setColorListHsv(nodeList, hsv, colorShapes=True, displayMessage=True, linear=True):
    """Sets the color for a list of objects in hsv values. 3 tuple of 0-1 floats

    :param nodeList: List of Maya Objects
    :type nodeList: list
    :param hsv: Hue Saturation Value, tuple of floats hue is 0-360 sat and value is 0-1
    :type hsv: list
    :param colorShapes: if True set the shapeNodes, otherwise set the exact list, often transforms
    :type colorShapes: bool
    :param displayMessage: Displays the success message
    :type displayMessage: bool
    :param linear: If true the rgb color is in linear space, matching the viewport, else convert it
    :type linear: bool
    """
    if colorShapes:
        nodeList = shapenodes.filterShapesInList(nodeList)
    if not nodeList:
        if displayMessage:
            om2.MGlobal.displayWarning('Warning: No Valid Shape List Detected')
        return
    rgb = colour.convertHsvToRgb(hsv)  # convert HSV to RGB
    for shape in nodeList:
        setColorShapeRgb(shape, rgb, linear=linear)
    if displayMessage:
        om2.MGlobal.displayInfo("Success: Colors have been changed")


def setColorListIndex(nodeList, mayaColor, colorShapes=True, displayMessage=True):
    """Sets the color of shape nodes, given an object list
    Color can be Maya Index (int) or Maya Nice Name (str)

    :param nodeList: List of Maya Objects
    :type nodeList: list
    :param mayaColor: Color can be Maya Index (int) or Maya Nice Name (str)
    :type mayaColor: int or str
    :param colorShapes: if True set the shapeNodes, otherwise set the exact list, often transforms
    :type colorShapes: bool
    :param displayMessage: Displays the success message
    :type displayMessage: bool
    """
    if colorShapes:
        nodeList = shapenodes.filterShapesInList(nodeList)
    if not nodeList:
        txt = 'Warning: No Valid Shape List Detected'
        om2.MGlobal.displayWarning(txt)
        logger.debug(txt)
        return
    for shape in nodeList:
        mayaColor = setColorShapeIndex(shape, mayaColor)  # main function

    if not mayaColor:
        txt = 'Color Not Found!'
        logger.debug(txt)
        if displayMessage:
            om2.MGlobal.displayError(txt)
        return
    elif not isinstance(mayaColor, string_types):  # or if int
        mayaColor = MAYA_COLOR_NICENAMES[mayaColor]
    txt = 'Success: Shape Nodes Colored `{}`'.format(mayaColor)
    logger.debug(txt)
    if displayMessage:
        om2.MGlobal.displayInfo(txt)


def setColorSelectedRgb(rgb, colorShapes=True, displayMessage=True, linear=True):
    """Sets the selected object's shape nodes to be a color in rgb

    :param rgb: Red Green Blue, tuple of three numbers, float values 0-1
    :type rgb: list
    :param colorShapes: if True set the shapeNodes, otherwise set the exact list, often transforms
    :type colorShapes: bool
    :param displayMessage: If true display the message to the user
    :type displayMessage: bool
    :param linear: If true the rgb color is in linear space, matching the viewport, else convert it
    :type linear: bool
    """
    selobjs = cmds.ls(selection=True)
    if not selobjs:
        txt = 'No Objects Selected, Please Select An Object'
        logger.debug(txt)
        om2.MGlobal.displayWarning(txt)
        return
    setColorListRgb(selobjs, rgb, colorShapes=True, displayMessage=displayMessage, linear=linear)


def setColorSelectedHsv(hsv, displayMessage=True, linear=True):
    """Sets the selected object's shape nodes to be the rgb color

    :param hsv: Hue Saturation Value, tuple of floats hue is 0-360 sat and value is 0-1
    :type hsv: list
    :param displayMessage: If true display the message to the user
    :type displayMessage: bool
    :param linear: If true the rgb color is in linear space, matching the viewport, else convert it
    :type linear: bool
    """
    selobjs = cmds.ls(selection=True)
    if not selobjs:
        txt = 'No Objects Selected, Please Select An Object'
        logger.debug(txt)
        om2.MGlobal.displayWarning(txt)
        return
    setColorListHsv(selobjs, hsv, displayMessage=displayMessage, linear=linear)


def setColorSelectedIndex(mayaColor, displayMessage=True):
    """Sets the selected object's shape nodes to be the Maya Index (int) color, or the nice name (str) color

    :param mayaColor: the color as per Maya numbers, Index (int) color, or the nice name (str) color
    :type mayaColor: str or int
    :param displayMessage: If true display the message to the user
    :type displayMessage: bool
    """
    selobjs = cmds.ls(selection=True)
    if not selobjs:
        txt = 'No Objects Selected, Please Select An Object'
        logger.debug(txt)
        om2.MGlobal.displayWarning(txt)
        return
    setColorListIndex(selobjs, mayaColor, displayMessage=displayMessage)


def convertShapeColorIndexToRGB(shape, linear=True):
    """Given a shape node, and assuming that it's in index color mode (.overrideRGBColors = 0)
    find the color and set the object to that rgb color

    :param shape: The shape's node name to get the color
    :type shape: str
    :param linear: If true the rgb color is in linear space, matching the viewport, else convert it
    :type linear: bool
    :return rgb: The r g b value as a list
    :rtype rgb: tuple
    """
    rgb = getRgbColor(shape, linear=linear)
    setColorShapeRgb(shape, rgb, linear=linear)
    return rgb


def convertObjIndexToRGB(mayaObj, linear=True):
    """Find if any shapes of the object are in index color and convert all shape nodes to RGB
    Given an object, (joint/transform etc)

    :param objectTransform: The name of the object (usually joint or transform)
    :type objectTransform: str
    :param linear: If true the rgb color is in linear space, matching the viewport, else convert it
    :type linear: bool
    """
    controlShapeNodeList = shapenodes.filterShapesInList([mayaObj])
    for shape in controlShapeNodeList:
        if not cmds.getAttr('{}.overrideRGBColors'.format(shape)):
            convertShapeColorIndexToRGB(shape, linear=linear)


def convertListIndexToRGB(mayaObjList, linear=True):
    """Find if any list of objects are in index color and convert all shape nodes to RGB
    Given an object, (joint/transform etc)

    :param objectTransform: The name of the object (usually joint or transform)
    :type objectTransform: str
    :param linear: If true the rgb color is in linear space, matching the viewport, else convert it
    :type linear: bool
    """
    for mayaObj in mayaObjList:
        convertObjIndexToRGB(mayaObj, linear=linear)


def offsetObjHsv(mayaNode, offset, colorShapes=True, hsvType="hue", displayMessage=True, linear=True):
    """Recolors shape nodes related to a Maya object in RGB values
    Offsets the hue by the offset amount (0-360) Can go past 360 or less than 0
    Saturation and Value range is 0-1

    :param mayaObj: The Maya object
    :type mayaObj: str
    :param offset: the offset value to offset the color, 0-1 or if hue is 0-360
    :type offset: float
    :param colorShapes: if True set the shapeNodes, otherwise set the exact list, often transforms
    :type colorShapes: bool
    :param hsvType: the type to offset, "hue", "saturation" or "value"
    :type hsvType: str
    :param displayMessage: If true display the message to the user
    :type displayMessage: bool
    :param linear: If true the rgb color is in linear space, matching the viewport, else convert it
    :type linear: bool
    """
    nodeList = [mayaNode]
    if colorShapes:
        nodeList = shapenodes.filterShapesInList(nodeList)
    if nodeList:
        hsv = getHsvColor(nodeList[0], linear=True)
        if hsvType == "hue":
            hsv = colour.offsetHueColor(hsv, offset)
        if hsvType == "saturation":
            hsv = colour.offsetSaturation(hsv, offset)
        if hsvType == "value":
            hsv = colour.offsetValue(hsv, offset)
        setColorListHsv(nodeList, hsv, colorShapes=colorShapes, linear=linear, displayMessage=displayMessage)


def offsetListHsv(nodeList, offset, colorShapes=True, hsvType="hue", displayMessage=True, linear=True):
    """Recolors the overrideRGBColors for all shape nodes in an object list
    Offsets the hue by the offset amount (0-360)
    Can go past 360 or less than 0

    :param nodeList: list of obj names, usually transforms/joints
    :type nodeList: list
    :param offset: How much to offset the hue component, can go past 360 or less than 0. 0-360 color wheel
    :type offset: float
    :param colorShapes: if True set the shapeNodes, otherwise set the exact list, often transforms
    :type colorShapes: bool
    :param hsvType: the type to offset, "hue", "saturation" or "value"
    :type hsvType: str
    :param displayMessage: If true display the message to the user
    :type displayMessage: bool
    :param linear: If true the rgb color is in linear space, matching the viewport, else convert it
    :type linear: bool
    """
    for node in nodeList:
        offsetObjHsv(node, offset, colorShapes=colorShapes, hsvType=hsvType, displayMessage=displayMessage,
                     linear=linear)


def offsetOutlinerColorHsv(node, offset, hsvType="hue", displayMessage=True):
    """Offsets a Maya nodes affecting the outliner color by hue or, saturation, or value

    Hue is 0-360, saturation and value are 0-1 ranges (srgbFloat)

    :param node: A maya node
    :type node: str
    :param offset: the offset value to offset the color, 0-1 or if hue is 0-360
    :type offset: float
    :param hsvType: the type to offset, "hue", "saturation" or "value"
    :type hsvType: str
    :param displayMessage: If true display the message to the user
    :type displayMessage: bool
    :param linear: If true the rgb color is in linear space, matching the viewport, else convert it
    :type linear: bool
    """
    srgbFloat = getOutlinerColors(node)
    hsv = colour.convertRgbToHsv(srgbFloat)
    if hsvType == "hue":
        hsv = colour.offsetHueColor(hsv, offset)
    if hsvType == "saturation":
        hsv = colour.offsetSaturation(hsv, offset)
    if hsvType == "value":
        hsv = colour.offsetValue(hsv, offset)
    srgbFloat = colour.convertHsvToRgb(hsv)
    setOutlinerColor(node, srgbFloat)


def offsetOutlinerColorListHsv(nodeList, offset, hsvType="hue", displayMessage=True):
    """Offsets a list of Maya nodes affecting the outliner colors by hue or, saturation, or value

    Hue is 0-360, saturation and value are 0-1 ranges

    :param nodeList: A list of Maya node names
    :type nodeList: list(str)
    :param offset: the offset value to offset the color, 0-1 or if hue is 0-360
    :type offset: float
    :param hsvType: the type to offset, "hue", "saturation" or "value"
    :type hsvType: str
    :param displayMessage: If true display the message to the user
    :type displayMessage: bool
    :param linear: If true the rgb color is in linear space, matching the viewport, else convert it
    :type linear: bool
    """
    for node in nodeList:
        offsetOutlinerColorHsv(node, offset, hsvType=hsvType, displayMessage=displayMessage)

def convertHsvOffsetTuple(offsetTuple):
    """Receives a hsv offset as a tuple and converts to a single float and string
    Offsets the hue by the offset amount (0-360), value and saturation are 0-1

    Hue is 0-360, saturation and value are 0-1 ranges

    :param offsetTuple: The hsv offset as a tuple eg (45.1, 0.0, 0.0)
    :type offsetTuple: tuple
    :return offset: The offset now as a single float
    :rtype offset: float
    :param hsvType: hsv type to modify, can be "hue", "saturation" or "value"
    :rtype hsvType: str
    """
    if offsetTuple[0]:
        return offsetTuple[0], "hue"
    elif offsetTuple[1]:
        return offsetTuple[1], "saturation"
    else:
        return offsetTuple[2], "value"


def offsetSelectedHsv(offset, hsvType="hue", linear=True, message=True):
    """Recolors the overrideRGBColors for shape nodes under selected objects (usually jnts/transforms)
    Offsets the hue by the offset amount (0-360), value and saturation are 0-1
    Can go past 360 or less than 0

    :param offset: How much to offset the hue component, 0-1 or neg 360-360 for hue
    :type offset: float
    :param hsvType: hsv type to modify, can be "hue", "saturation" or "value"
    :type hsvType: str
    :param linear: If true the rgb color is in linear space, matching the viewport, else convert it
    :type linear: bool
    :param message: report the message to the user?
    :type message: bool
    """
    selobjs = cmds.ls(selection=True, long=True)
    if not selobjs:
        txt = 'No Objects Selected, Please Select An Object'
        logger.debug(txt)
        if message:
            om2.MGlobal.displayWarning(txt)
        return
    offsetListHsv(selobjs, offset=offset, hsvType=hsvType, linear=linear)


def recordedObjColor(RECORDCOLORBOBJS):
    """This function is for UIs where it's handy to keep track of objects after they're deselected
    This is because it's hard/impossible to see curves while they're being adjusted
    uses the global variable RECORDCOLORBOBJS, which must be set and returned when the script is run.

    :param RECORDCOLORBOBJS: global list of objects used so objects can be changes without selection
    :type RECORDCOLORBOBJS: list
    :return RECORDCOLORBOBJS: global list of objects used so objects can be changes without selection
    :rtype RECORDCOLORBOBJS: list
    """
    selobjs = cmds.ls(selection=True)
    if selobjs:  # set new recorded objs
        RECORDCOLORBOBJS = selobjs  # record the obj list to the global variable
        cmds.select(d=1)
        return RECORDCOLORBOBJS
    if RECORDCOLORBOBJS:  # nothing selected so read the class variable to see if it exists
        testedObjs = list()
        for obj in RECORDCOLORBOBJS:
            if cmds.objExists(obj):  # in case of new scene or delete
                testedObjs.append(obj)
        if testedObjs:  # objects do exist
            RECORDCOLORBOBJS = testedObjs
            return RECORDCOLORBOBJS
    txt = 'No Objects Selected, Please Select An Object'
    logger.debug(txt)
    om2.MGlobal.displayWarning(txt)
    return RECORDCOLORBOBJS


def getColorList(objList, hsv=False, linear=False, limitDecimalPlaces=False):
    """From an object list returns each first shape node's color as either:

        hsv or rgb
        linear or srgb

    :param objList: List of Maya objects (transforms)
    :type objList: list(str)
    :param hsv: Return the color as hsv?
    :type hsv: bool
    :param linear: Return the color as linear (True) or srgb (False)
    :type linear: bool
    :param limitDecimalPlaces: If true limits the decimal places to max of 3 ie .098
    :type limitDecimalPlaces: bool
    :return colorList: A list of colors
    :rtype colorList: list(tuple(float))
    """
    colorList = list()
    for obj in objList:
        shapeNodeList = cmds.listRelatives(obj, shapes=True, fullPath=True)
        if shapeNodeList:
            colorList.append(getRgbColor(shapeNodeList[0], hsv=hsv, linear=linear,
                                         limitDecimalPlaces=limitDecimalPlaces))
    return colorList


def getColorListSelection(hsv=False, linear=False, limitDecimalPlaces=False):
    """From a selection return each first shape node's color as either:

        hsv or rgb
        linear or srgb

    :param hsv: Return the color as hsv?
    :type hsv: bool
    :param linear: Return the color as linear (True) or srgb (False)
    :type linear: bool
    :return colorList: A list of colors
    :rtype colorList: list(tuple(float))
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        return
    return getColorList(selObjs, hsv=hsv, linear=linear, limitDecimalPlaces=limitDecimalPlaces)


def getDictOfRGBColors(objectList, linear=True):
    """Creates a dictionary of given objects with the color of each object's first shape node

    :param objectList: list of Maya objects
    :type objectList: list
    :return objRGBDict: The obj[color] dict, colors are always in rgb
    :rtype objRGBDict: dict
    :param linear: If true the rgb color is in linear space, matching the viewport, else convert it
    :type linear: bool
    """
    objRGBDict = dict()
    for obj in objectList:
        shapeList = shapenodes.filterShapesInList([obj])
        if shapeList:
            rgb = getRgbColor(shapeList[0])
            if not linear:
                rgb = colour.convertColorLinearToSrgb(rgb)
            objRGBDict[obj] = rgb
    return objRGBDict


def getDictOfRGBColorsSel(fullPath=False, linear=True):
    """Creates a dictionary of selected objects with the color of each object's first shape node

    :param fullPath: record the full path names?
    :type fullPath: bool
    :param linear: If true the rgb color is in linear space, matching the viewport, else convert it
    :type linear: bool
    :return objRGBDict: The obj[color] dict, colors are always in rgb
    :rtype objRGBDict: dict
    """
    objList = cmds.ls(selection=True, long=fullPath)
    if not objList:
        txt = 'No Objects Selected, Please Select An Object'
        logger.debug(txt)
        om2.MGlobal.displayWarning(txt)
        return
    return getDictOfRGBColors(objList, linear=linear)


def setDictOfRGBColors(dictObjRGB, linear=True, displayMessage=False):
    """Reads a dictionary and sets colors for all shape nodes of the given Maya objects

    :param dictObjRGB: The dictionary keys are object names (str) and values are rgb tuples, three floats 0-1
    :type dictObjRGB: dict
    :param linear: If true the rgb color is in linear space, matching the viewport, else convert it
    :type linear: bool
    :param displayMessage: If true display the message to the user
    :type displayMessage: bool
    """
    for keyObj, rgb in dictObjRGB.items():
        shapeList = shapenodes.filterShapesInList([keyObj])
        if shapeList:
            setColorListRgb(shapeList, rgb, displayMessage=displayMessage, linear=linear)


def setDictOfRGBColorsExistCheck(dictObjRGB, linear=True, displayMessage=False):
    """Reads a dictionary and sets colors for all shape nodes of the given Maya objects
    This function checks if obj exists as they may not if the rig is dynamic

    :param dictObjRGB: The dictionary keys are object names (str) and values are rgb tuples, three floats 0-1
    :type dictObjRGB: dict
    :param linear: If true the rgb color is in linear space, matching the viewport, else convert it
    :type linear: bool
    :param displayMessage: If true display the message to the user
    :type displayMessage: bool
    """
    for keyObj, rgb in dictObjRGB.items():
        # check if obj exists
        if not cmds.objExists(keyObj):
            dictObjRGB.pop(keyObj, None)
    setDictOfRGBColors(dictObjRGB, linear=linear, displayMessage=displayMessage)


# -------------------------------
# Reset Override Obj Colors
# -------------------------------


def resetOverrideObjColor(node):
    """Resets the color of a node to Maya default, does not reset the rgb color

    :param node: Maya node name, should be a dag object
    :type node: str
    """
    cmds.setAttr('{}.overrideEnabled'.format(node), 0)


def resetOverrideObjColorList(nodeList, colorShapes=True):
    """Resets the color of a node list to Maya default, does not reset the rgb color

    :param nodeList: Maya node names, should be dag objects
    :type nodeList: list(str)
    :param colorShapes: if True set the shapeNodes, otherwise set the exact list, often transforms
    :type colorShapes: bool
    """
    if colorShapes:
        nodeList = shapenodes.filterShapesInList(nodeList)
    for node in nodeList:
        resetOverrideObjColor(node)


def resetOverrideObjColorSelection(colorShapes=True):
    """Resets the color of the current selection to Maya default, does not reset the rgb color

    TODO should fiter objects as some may not be supported

    :param colorShapes: if True set the shapeNodes, otherwise set the exact list, often transforms
    :type colorShapes: bool
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        return
    resetOverrideObjColorList(selObjs, colorShapes=colorShapes)


# -------------------------------
# Select Objects by Color
# -------------------------------


def compareColorsTolerance(firstColor, secondColor, tolerance):
    """Compares two colors usually rgb floats, but could be other types within a tolerance level

    Colors often aren't precise especially when converting back n forth between linear, srgb or rgb and hsv

    Tolerance is the margin for error.

    :param firstColor: The first color to compare (0.0, 0.5, 1.0)
    :type firstColor: tuple(float)
    :param secondColor: The second color to compare (0.0, 0.5, 1.0)
    :type secondColor: tuple(float)
    :param tolerance: The range in which the colors can vary
    :type tolerance: float
    :return match: True if matches withing the tolerance.
    :rtype match: bool
    """
    for i, value in enumerate(firstColor):
        if not abs(value - secondColor[i]) <= tolerance:
            return False
    return True


def objsByColor(nodeList, color, tolerance=0.05, queryShapes=True):
    """Returns objects by shape color, given a filtered list

    Will match by finding the rgbColor of the first shape node of the transform, if color is a match it will return

    Tolerance is the margin for error.  Colors often aren't precise especially when converting back n forth between \
    linear, srgb or rgb and hsv

    :param nodeList: list of objects (transforms), usually filtered by curve, but can be other types
    :type nodeList: list(str)
    :param color: The color to match to the obj list
    :type color: tuple(float)
    :param tolerance: The range in which the colors can vary
    :type tolerance: float
    :param queryShapes: Will query the first shape node for the matching color value
    :type queryShapes: bool
    :return coloredTransforms:  Transform objs where the first shape matches the color
    :rtype coloredTransforms: list(str)
    """
    coloredTransforms = list()
    for i, node in enumerate(nodeList):
        nodesToCheck = [nodeList[i]]
        if queryShapes:
            nodesToCheck = shapenodes.filterShapesInList([node])
        if nodesToCheck:  # compare colors within a tolerance level
            if compareColorsTolerance(getRgbColor(nodesToCheck[0]), color, tolerance):
                coloredTransforms.append(node)
    return coloredTransforms


def selectObjsByColor(nodeList, color, queryShapes=True, message=True, selectObjs=True):
    """Selects objects by shape color, given a filtered list

    :param nodeList: list of objects (transforms), usually filtered, ready to find any color matches
    :type nodeList: list(str)
    :param color: The color to match to the obj list
    :type color: tuple(float)
    :param queryShapes: Will query the first shape node for the matching color value
    :type queryShapes: bool
    :param selectObjs: If False will just return the objects and not select them
    :type selectObjs: bool
    :param message: Report the message to the user?
    :type message: bool
    """
    matchObjs = objsByColor(nodeList, tuple(color), queryShapes=queryShapes)
    if not matchObjs:
        if message:
            om2.MGlobal.displayWarning("No objects found matching the color `{}`".format(color))
        return matchObjs
    cmds.select(matchObjs, replace=True)
    if message:
        om2.MGlobal.displayInfo("Success: Objs matching color `{}` found.".format(color))
    return matchObjs


# -------------------------------
# Set Outliner Colors
# -------------------------------


def setOutlinerColor(node, rgb, incomingIsLinear=False):
    """Colors the Outliner color for a node

    :param node: The name of a single shape node
    :type node: str
    :param rgb: Set/list of rgb values eg (0.5, 0.5, 0.5), if srgb color then set linear to be False
    :type rgb: Set/list
    :param incomingIsLinear: Set to True if the incoming color is linear. Outliner colors are in SRCB only
    :type incomingIsLinear: bool
    """
    if incomingIsLinear:
        rgb = colour.convertColorLinearToSrgb(rgb)
    cmds.setAttr('{}.useOutlinerColor'.format(node), 1)
    cmds.setAttr('{}.outlinerColorR'.format(node), rgb[0])
    cmds.setAttr('{}.outlinerColorG'.format(node), rgb[1])
    cmds.setAttr('{}.outlinerColorB'.format(node), rgb[2])


def setOutlinerColorList(nodeList, rgb, incomingIsLinear=False):
    """Colors the outliner color for a nodeList

    :param nodeList: The name of a single shape node
    :type nodeList: str
    :param rgb: set/list of rgb values eg (0.5, 0.5, 0.5), if srgb color then set linear to be False
    :type rgb: set/list
    :param incomingIsLinear: Set to True if the incoming color is linear. Outliner colors are in SRCB only
    :type incomingIsLinear: bool
    """
    for node in nodeList:
        setOutlinerColor(node, rgb, incomingIsLinear=incomingIsLinear)


def setOutlinerColorSelection(rgb, incomingIsLinear=False):
    """Colors the Outliner color for the current selection

    :param rgb: set/list of rgb values eg (0.5, 0.5, 0.5), if srgb color then set linear to be False
    :type rgb: set/list
    :param incomingIsLinear: Set to True if the incoming color is linear. Outliner colors are in SRCB only
    :type incomingIsLinear: bool
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        return
    setOutlinerColorList(selObjs, rgb, incomingIsLinear=incomingIsLinear)


# -------------------------------
# Get Outliner Colors
# -------------------------------


def getOutlinerColors(node, returnLinear=False):
    """Gets the outliner color of a node

    :param node: Maya node name, should be a dag object
    :type node: str
    :return color: The color in srgb float, if returnLinear is on then will be in linear float
    :rtype color: list(float)
    """
    if not cmds.attributeQuery('useOutlinerColor', node=node, exists=True):
        return None
    if not cmds.getAttr('{}.useOutlinerColor'.format(node)):
        srgbColor = [0.8, 0.8, 0.8]
    else:
        srgbColor = list(cmds.getAttr('{}.outlinerColor'.format(node))[0])
    if returnLinear:  # then return the colour as linear float
        return colour.convertColorSrgbToLinear(srgbColor)
    return srgbColor


# -------------------------------
# Reset Outliner Colors
# -------------------------------


def resetOutlinerColor(node):
    """Resets the Outliner color of a node to Maya default

    :param node: Maya node name, should be a dag object
    :type node: str
    """
    cmds.setAttr('{}.useOutlinerColor'.format(node), False)


def resetOutlinerColorList(nodeList):
    """Resets the OUtliner color of a node list to Maya default

    :param nodeList: Maya node names, should be dag objects
    :type nodeList: list(str)
    """
    for node in nodeList:
        resetOutlinerColor(node)


def resetOutlinerColorSelection():
    """Resets the Outliner color of the current selection to Maya default

    TODO should fiter objects as some may not be supported
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        return
    resetOutlinerColorList(selObjs)


# -------------------------------
# Select By Outliner Colors
# -------------------------------


def selectObjsByOutlinerColor(objList, matchColor, tolerance=0.05, incomingLinear=False, selectObjs=True):
    """Matches objects by Outliner colour.  Colour is in srgb float. If passing linear in use incomingLinear=True.

    :param objList: A Maya object list of nodes
    :type objList: list(str)
    :param matchColor: The color to match to the obj list
    :type matchColor: list(float)
    :param tolerance: The range in which the colors can vary
    :type tolerance: float
    :param incomingLinear: If the incoming color is in linear float color, set this to True, otherwise leave as False.
    :type incomingLinear: bool
    :param selectObjs: Mark as True if you want to select the objects
    :type selectObjs: bool
    :return: If the incoming matchColor is in linear space, set this to True
    :rtype:
    """
    matchList = list()
    if incomingLinear:
        matchColor = colour.convertColorLinearToSrgb(matchColor)
    for obj in objList:
        srgbColor = getOutlinerColors(obj, returnLinear=False)
        if not srgbColor:
            continue
        if compareColorsTolerance(srgbColor, matchColor, tolerance=tolerance):
            matchList.append(obj)
    if selectObjs and matchList:
        cmds.select(matchList, replace=True)
    return matchList
