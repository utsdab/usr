from zoo.libs.utils import colour

# color palettes are stored in SRGB float

PASTEL_PALETTE = [(0.933, 0.376, 0.333), (0.458, 0.858, 0.803), (0.925, 0.891, 0.799), (0.795, 0.788, 0.85),
                  (0.745, 0.933, 0.384), (0.738, 0.285, 0.249), (0.0, 0.706, 0.644), (0.79, 0.712, 0.434),
                  (0.536, 0.499, 0.762), (0.605, 0.8, 0.0)]

NEON_PALETTE = [(0.535, 0.743, 0.996), (0.506, 0.945, 0.83), (0.778, 0.584, 1.0), (1.0, 0.537, 0.649),
                (1.0, 0.772, 0.57), (0.004, 0.627, 0.996), (0.0, 0.945, 0.787), (0.674, 0.248, 1.0),
                (1.0, 0.248, 0.499), (1.0, 0.668, 0.204)]

CAMPFIRE_PALETTE = [(0.314, 0.636, 0.492), (0.995, 0.919, 0.463), (0.995, 0.651, 0.246), (0.903, 0.303, 0.22),
                    (0.71, 0.165, 0.343), (0.345, 0.549, 0.451), (0.949, 0.89, 0.58), (0.949, 0.682, 0.447),
                    (0.851, 0.392, 0.349), (0.674, 0.26, 0.373)]

CONTRAD_PALETTE = [(0.955, 0.881, 0.572), (0.955, 0.941, 0.512), (1.0, 0.582, 0.511), (0.881, 0.214, 0.553),
                   (0.633, 0.227, 0.877), (0.8, 0.773, 0.11), (1.0, 0.917, 0.424), (0.941, 0.353, 0.157),
                   (0.725, 0.0, 0.431), (0.442, 0.139, 0.621)]

LRXD_PALETTE = [(0.996, 0.671, 0.422), (0.8, 0.333, 0.481), (0.624, 0.352, 0.842), (0.456, 0.714, 0.945),
                (0.413, 0.718, 0.652), (0.996, 0.588, 0.0), (0.8, 0.19, 0.422), (0.574, 0.0, 0.842),
                (0.0, 0.639, 0.945), (0.0, 0.718, 0.622)]

PRIMARIES_PALETTE = [(1.0, 0.424, 0.424), (1.0, 0.507, 0.424), (1.0, 1.0, 0.424), (0.424, 1.0, 0.424),
                     (0.424, 0.424, 1.0), (1.0, 0.0, 0.0), (1.0, 0.32, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0),
                     (0.0, 0.0, 1.0)]


def generateHueOffsetPalette(startHsvColor, colorNumber=20, hueRange=280.0):
    """Generates a color palette by offsetting the hue value from a start hsv color (0-360.0, 0-1.0, 0-1.0)

    :param startHsvColor: The first color in the palette in hsv color (0-360.0, 0-1.0, 0-1.0)
    :type startHsvColor: tuple[float]
    :param colorNumber: The total number of colors in the palette
    :type colorNumber: int
    :param hueRange: The full spectrum range of the entire color palette in the hue range (360.0 is a full circle)
    :type hueRange: float
    :return colorListSrgb: A color list in rgb float [0-1.0, 0-1.0, 0-1.0]
    :rtype colorListSrgb: tuple
    """
    colorListSrgb = list()
    hueOffset = hueRange / float(colorNumber)
    for i in range(colorNumber):
        hsvColor = list(startHsvColor)
        hsvColor[0] += (i * hueOffset)  # adds the offset each loop to hue
        srgbFloat = colour.convertHsvToRgb(hsvColor)  # Maya uses linear float color (0.1, 1.0, 0.4)
        colorListSrgb.append(srgbFloat)
    return tuple(colorListSrgb)


SATURATED_PALETTE = generateHueOffsetPalette((0.0, 1.0, 1.0), colorNumber=20, hueRange=280)
MIDDLE_PALETTE = generateHueOffsetPalette((0.0, 0.7, 1.0), colorNumber=20, hueRange=280)
FADED_PALETTE = generateHueOffsetPalette((0.0, 0.4, 1.0), colorNumber=20, hueRange=280)
SATURATED_FULL_PALETTE = generateHueOffsetPalette((0.0, 1.0, 1.0), colorNumber=20, hueRange=360)
MIDDLE_FULL_PALETTE = generateHueOffsetPalette((0.0, 0.7, 1.0), colorNumber=20, hueRange=360)
FADED_FULL_PALETTE = generateHueOffsetPalette((0.0, 0.4, 1.0), colorNumber=20, hueRange=360)
DARK_PALETTE = generateHueOffsetPalette((0.0, 1.0, 0.3), colorNumber=20, hueRange=280)
