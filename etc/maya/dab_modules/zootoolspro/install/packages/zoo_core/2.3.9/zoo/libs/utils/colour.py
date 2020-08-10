"""Colors

This module contains functions related to color but not specific to any particular softawre
"""

import colorsys
from math import radians, sqrt, cos, sin, log, pow
from zoo.libs.utils import zoomath


def convertHsvToRgb(hsv):
    """Converts hsv values to rgb
    rgb is in 0-1 range srgbFloat, hsv is in (0-360, 0-1, 0-1) ranges

    :param hsv: Hue Saturation Value Hue is in 0-360 range, Sat/Value 0-1 range
    :type hsv: list
    :return rgb: Red Green Blue values 0-1 srgbFloat
    :rtype rgb: list
    """
    rgb = list(colorsys.hsv_to_rgb((hsv[0] / 360.0), hsv[1], hsv[2]))  # convert HSV to RGB
    return rgb


def convertRgbToHsv(rgb):
    """ Converts rgb values to hsv
    rgb is in 0-1 range, hsv is in (0-360, 0-1, 0-1) ranges

    :param rgb: Hue Saturation Value Hue is in 0-360 range, Sat/Value 0-1 range
    :type rgb: list or tuple
    :return hsv: Red Green Blue values 0-1
    :rtype hsv: list
    """
    hsv = list(colorsys.rgb_to_hsv((rgb[0]), rgb[1], rgb[2]))
    hsv[0] *= 360.0
    return hsv


def convertSingleSrgbToLinear(colorValue):
    """Changes a single rgb color (so say red only) to linear space.

    :param colorValue: a single color value, expects a value from 0-1
    :type colorValue: float
    :return Linear: the new color converted to linear
    :rtype Linear: float
    """
    a = 0.055
    if colorValue <= 0.04045:
        return colorValue * (1.0 / 12.92)
    return pow((colorValue + a) * (1.0 / (1 + a)), 2.4)


def convertSingleLinearToSrgb(colorValue):
    """Changes a single rgb color (so say red only) in linear so the resulting color is displayed
    in srgb color space.

    :param colorValue: a single color value, expects a value from 0-1
    :type colorValue: float
    :return Srgb: the new color converted to srgb
    :rtype Srgb: float
    """
    a = 0.055
    if colorValue <= 0.0031308:
        return colorValue * 12.92
    return (1 + a) * pow(colorValue, 1 / 2.4) - a


def convertColorSrgbToLinear(srgbColor):
    """Changes a srgb color to linear color

    :param srgbColor: a SRGB float color list/tuple, expects values from 0-1
    :type srgbColor: list of floats
    :return linearRgb: the new color gamma converted to linear
    :rtype linearRgb: float
    """
    return (convertSingleSrgbToLinear(srgbColor[0]),
            convertSingleSrgbToLinear(srgbColor[1]),
            convertSingleSrgbToLinear(srgbColor[2]))


def convertColorLinearToSrgb(linearRgb):
    """Changes a linear color to srgb color

    :param linearRgb: a rgb color list/tuple, expects values from 0-1
    :type linearRgb: list of floats
    :return: the new color gamma converted to srgb
    :rtype: tuple(float)
    """
    return (convertSingleLinearToSrgb(linearRgb[0]),
            convertSingleLinearToSrgb(linearRgb[1]),
            convertSingleLinearToSrgb(linearRgb[2]))


def convertSrgbListToLinear(srgbList, roundNumber=True):
    """Converts a list to linear, optional round to 4 decimal places

    :param srgbList: list of srgb colors range 0-1 eg (0.0, 1.0, 0.0)
    :type srgbList: list
    :param roundNumber: do you want to round to 4 decimal places?
    :type roundNumber: bool
    :return linearRgbList: The list of colors converted to linear color
    :rtype linearRgbList: list
    """
    linearRgbList = list()
    for col in srgbList:
        linColorLong = convertColorSrgbToLinear(col)
        if roundNumber:
            linCol = list()
            for longNumber in linColorLong:
                roundedNumber = round(longNumber, 4)
                linCol.append(roundedNumber)
            linearRgbList.append(linCol)
        else:
            linearRgbList.append(linColorLong)
    return linearRgbList


def desaturate(col, level=1.0):
    """ Returns a desaturated color

    :param col: int color tuple eg (128, 128, 255, 255)
    :type col: tuple
    :param level: Level of desaturation from 0 to 1.0. 1.0 is desaturated, 0 is the same saturation
    :type level: float
    :return: Tuple with desaturated color
    :rtype: tuple
    """
    saturation = convertRgbToHsv(rgbIntToFloat(col))[1]
    if saturation:
        saturationOffset = int((saturation * level) * -255.0)
    else:
        saturationOffset = 0.0
    desaturated = hslColourOffsetInt(col, lightnessOffset=-40, saturationOffset=saturationOffset)

    return desaturated


def offsetHueColor(hsv, offset):
    """Offsets the hue value (0-360) by the given `offset` amount
    keeps in range 0-360 by looping
    Max offset is 360, min is -360

    :param hsv: The hue sat val color list [180, .5, .5]
    :type hsv: list
    :param offset: How much to offset the hue component, can go past 360 or less than 0. 0-360 color wheel
    :type offset: float
    :return hsv: The new hsv list eg [200, .5, .5]
    :rtype hsv: list
    """
    if offset > 360:
        offset = 360
    elif offset < -360:
        offset = -360
    hsv[0] += offset
    # reset value so it lies within the 0-360 range
    if hsv[0] > 360:
        hsv[0] -= 360
    elif hsv[0] < 0:
        hsv[0] += 360
    return hsv


def offsetSaturation(hsv, offset):
    """Offsets the "saturation" value (0-1) by the given `offset` amount
    keeps in range 0-1 by looping

    :param hsv: a 3 value list or tuple representing a the hue saturation and value color [180, .5, .5]
    :type hsv: list
    :param offset: the offset value to offset the color
    :type offset: float
    :return hsv: the hue saturation value color eg [200, .5, .5]
    :rtype: list
    """
    hsv[1] += offset
    # reset value so it lies within the 0-360 range
    if hsv[1] > 1:
        hsv[1] = 1
    elif hsv[1] < 0:
        hsv[1] = 0
    return hsv


def offsetColor(col, offset=0):
    """Returns a color with the offset in tuple form.

    :param col: Color in form of tuple with 3 ints. eg tuple(255,255,255)
    :type col: tuple(int,int,int)
    :param offset: The int to offset the color
    :return: tuple (int,int,int)
    """
    return tuple([zoomath.clamp((c + offset), 0, 255) for c in col])


def offsetValue(hsv, offset):
    """Offsets the "value" (brightness/darkness) value (0-1) by the given `offset` amount
    keeps in range 0-1 by looping

    :param hsv: a 3 value list or tuple representing a the hue saturation and value color [180, .5, .5]
    :type hsv: list
    :param offset: the offset value to offset the color
    :type offset: float
    :return hsv: the hue saturation value color eg [200, .5, .5]
    :rtype: list
    """
    hsv[2] += offset
    # reset value so it lies within the 0-360 range
    if hsv[2] > 1:
        hsv[2] = 1
    elif hsv[2] < 0:
        hsv[2] = 0
    return hsv


def hueShift(col, shift):
    """Shifts the hue of the given colour

    :param col: Colour to shift
    :type col: tuple(int,int,int)
    :param shift: The distance and direction of the colour to shift
    :type shift: int
    :return: the colour with the shifted hue
    :rtype: tuple(int,int,int)
    """
    rgbRotator = RGBRotate()
    rgbRotator.set_hue_rotation(shift)
    return rgbRotator.apply(*col)


def hexToRGBA(hexstr):
    """ Converts hexidecimal number to RGBA tuple

    Allows folowing formats:

    "RRGGBB" eg 2F2F2F
    "AARRGGBB" eg 882F2F2F
    "RGB" eg CCC

    :param hex: String hex eg "2F2F2F"
    :return: Returns in format tuple(R, G, B, A)
    :rtype: tuple
    """
    if len(hexstr) == 8:
        return int(hexstr[2:4], 16), int(hexstr[4:6], 16), int(hexstr[6:8], 16), int(hexstr[0:2], 16)
    elif len(hexstr) == 6:
        return int(hexstr[0:2], 16), int(hexstr[2:4], 16), int(hexstr[4:6], 16), 255
    elif len(hexstr) == 3:
        return int(hexstr[0:1]*2, 16), int(hexstr[1:2]*2, 16), int(hexstr[2:3]*2, 16), 255
    else:
        raise Exception("Invalid hex length: {}".format(hexstr))


def hexToRGB(hexstr):
    """  Converts hexidecimal number to RGBA tuple

    :param hex: String hex eg "2F2F2F"
    :return: Returns in format tuple(R, G, B)
    :rtype: tuple
    """
    return hexToRGBA(hexstr)[0:3]


def RGBToHex(rgb):
    """ Converts rgb tuple to hex string

    (62, 104, 173) ==> '3E68AD'
    (168, 20, 86, 255) ==> 'FF3E68AD'

    :param rgb: rgb tuple
    :return: Hex string eg '44FF33'
    """
    ret = ''.join([hex(h)[2:].upper().zfill(2) for h in rgb])
    if len(ret) == 8:
        return ret[-2:] + ret[:-2]  # Move the last two characters to the beginning

    return ret


def rgbIntToFloat(color):
    """ Turns int color (255,255,255,255) to (1.0, 1.0, 1.0, 1.0)

    :param color: int color tuple eg (128, 128, 255, 255)
    :return: Float color eg (0.5, 0.5, 1.0, 1.0)
    """

    return tuple([c/255.0 for c in color])


def rgbFloatToInt(color):
    """ Turns float color to int color  eg (1.0, 1.0, 1.0, 1.0) to (255,255,255,255)

    :param color: float color tuple eg (0.5, 0.5, 1.0, 1.0)
    :return: int color eg (128, 128, 255, 255)
    """
    return tuple([int(round(255*float(c))) for c in color])


def rgbIntRound(color):
    """Rounds all values of 255 color

    example:
        (244.9, 100, 10.33) is returned as (255, 100, 10)

    :param color: int color tuple eg (255.0, 0.001, 0.0)
    :type: tuple
    :return: int color converted eg (255, 0, 0)
    :rtype: tuple
    """
    return tuple([int(round(c)) for c in color])


class RGBRotate(object):
    """Hue Rotation, using the matrix rotation method. From here

    https://stackoverflow.com/questions/8507885/shift-hue-of-an-rgb-color
    """
    def __init__(self):
        self.matrix = [[1,0,0],[0,1,0],[0,0,1]]

    def set_hue_rotation(self, degrees):
        cosA = cos(radians(degrees))
        sinA = sin(radians(degrees))
        self.matrix[0][0] = cosA + (1.0 - cosA) / 3.0
        self.matrix[0][1] = 1./3. * (1.0 - cosA) - sqrt(1./3.) * sinA
        self.matrix[0][2] = 1./3. * (1.0 - cosA) + sqrt(1./3.) * sinA
        self.matrix[1][0] = 1./3. * (1.0 - cosA) + sqrt(1./3.) * sinA
        self.matrix[1][1] = cosA + 1./3.*(1.0 - cosA)
        self.matrix[1][2] = 1./3. * (1.0 - cosA) - sqrt(1./3.) * sinA
        self.matrix[2][0] = 1./3. * (1.0 - cosA) - sqrt(1./3.) * sinA
        self.matrix[2][1] = 1./3. * (1.0 - cosA) + sqrt(1./3.) * sinA
        self.matrix[2][2] = cosA + 1./3. * (1.0 - cosA)

    def apply(self, r, g, b):
        rx = r * self.matrix[0][0] + g * self.matrix[0][1] + b * self.matrix[0][2]
        gx = r * self.matrix[1][0] + g * self.matrix[1][1] + b * self.matrix[1][2]
        bx = r * self.matrix[2][0] + g * self.matrix[2][1] + b * self.matrix[2][2]
        return zoomath.clamp(rx, 0, 255), zoomath.clamp(gx, 0, 255), zoomath.clamp(bx, 0, 255)


def hslColourOffsetFloat(rgb, hueOffset=0, saturationOffset=0, lightnessOffset=0):
    """Offset color with hue, saturation and lightness (brighten/darken) values

    Colour is expected as rgb  in 0.0-1.0 float range eg (0.1, 0.34, 1.0)
    Offsets are in...
        hue: 0-360,
        saturation: 0.0-1.0,
        value (lightness): 0.0-1.0
    Returned colour is rgb in in 0-1.0 range eg (0.1, 0.34, 1.0)

    :param rgb: the rgb color in 0.0-0.1 range eg (0.1, 0.34, 1.0)
    :type rgb: tuple
    :param hueOffset: the hue offset in 0-360 range
    :type hueOffset: float
    :param saturationOffset: the saturation offset in 0-255 range
    :type saturationOffset: float
    :param lightnessOffset: the lightness value offset, lighten (0.2) or darken (-0.3), 0-0.1 range as an offset
    :type lightnessOffset: float
    :return rgb: the changed rgb color in 0.0-0.1 range eg (0.1, 0.34, 1.0)
    :rtype: rgb: tuple
    """
    if hueOffset:
        hsv = convertRgbToHsv(list(rgb))
        newHue = hsv[0] + hueOffset
        if newHue > 360.0:
            newHue -= 360.0
        elif newHue < 360.0:
            newHue += 360.0
        hsv = (newHue, hsv[1], hsv[2])
        rgb = convertHsvToRgb(list(hsv))
    if saturationOffset:
        hsv = convertRgbToHsv(rgb)
        saturationOffset = saturationOffset
        hsv = (hsv[0], zoomath.clamp(hsv[1] + saturationOffset), hsv[2])
        rgb = convertHsvToRgb(list(hsv))
    if lightnessOffset:
        rgb = (zoomath.clamp(rgb[0] + lightnessOffset),
               zoomath.clamp(rgb[1] + lightnessOffset),
               zoomath.clamp(rgb[2] + lightnessOffset))
    return rgb


def hslColourOffsetInt(rgb, hueOffset=0, saturationOffset=0, lightnessOffset=0):
    """Offset color with hue, saturation and lightness (brighten/darken) values
    Colour is expected as rgb  in 0-255 range eg (255, 123, 23)
    Offsets are in...
        hue: 0-360,
        saturation: 0-255,
        value (lightness): 0-255
    Returned colour is rgb in in 0-255 range eg (255, 123, 23)

    :param rgb: the rgb color in 0-255 range eg (255, 123, 23)
    :type rgb: tuple
    :param hueOffset: the hue offset in 0-360 range
    :type hueOffset: int
    :param saturationOffset: the saturation offset in 0-255 range
    :type saturationOffset: int
    :param lightnessOffset: the lightness value offset, lighten (30) or darken (-30), 0-255 range as an offset
    :type lightnessOffset: int
    :return rgb: the changed rgb color in 0-255 range eg (255, 123, 23)
    :rtype: rgb: tuple
    """
    rgb = rgbIntToFloat(rgb)
    lightnessOffset = float(lightnessOffset) / 255.0
    saturationOffset = float(saturationOffset) / 255.0
    rgb = hslColourOffsetFloat(rgb, hueOffset=hueOffset, saturationOffset=saturationOffset,
                               lightnessOffset=lightnessOffset)
    return rgbFloatToInt(rgb)


def convertKelvinToRGB(colour_temperature):
    """ Converts from K to RGB, algorithm courtesy of
    http://www.tannerhelland.com/4435/convert-temperature-rgb-algorithm-code/

    :param colour_temperature: the color in degrees kelvin
    :type colour_temperature: float
    :return srgb: srgb color in int 255 format
    :rtype srgb: tuple(int)
    """
    # range check
    if colour_temperature < 1000:
        colour_temperature = 1000
    elif colour_temperature > 40000:
        colour_temperature = 40000

    tmp_internal = colour_temperature / 100.0

    # red
    if tmp_internal <= 66:
        red = 255
    else:
        tmp_red = 329.698727446 * pow(tmp_internal - 60, -0.1332047592)
        if tmp_red < 0:
            red = 0
        elif tmp_red > 255:
            red = 255
        else:
            red = tmp_red

    # green
    if tmp_internal <= 66:
        tmp_green = 99.4708025861 * log(tmp_internal) - 161.1195681661
        if tmp_green < 0:
            green = 0
        elif tmp_green > 255:
            green = 255
        else:
            green = tmp_green
    else:
        tmp_green = 288.1221695283 * pow(tmp_internal - 60, -0.0755148492)
        if tmp_green < 0:
            green = 0
        elif tmp_green > 255:
            green = 255
        else:
            green = tmp_green

    # blue
    if tmp_internal >= 66:
        blue = 255
    elif tmp_internal <= 19:
        blue = 0
    else:
        tmp_blue = 138.5177312231 * log(tmp_internal - 10) - 305.0447927307
        if tmp_blue < 0:
            blue = 0
        elif tmp_blue > 255:
            blue = 255
        else:
            blue = tmp_blue

    return (red, green, blue)

