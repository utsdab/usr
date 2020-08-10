import sys
import math
from zoovendor.six.moves import range


AXIS = {"x": 0,
        "y": 1,
        "z": 2}


def lerp(current, goal, weight=0.5):
    return (goal * weight) + ((1.0 - weight) * current)


def remap(value, oldMin, oldMax, newMin, newMax):
    return (((value - oldMin) * (newMax - newMin)) / (oldMax - oldMin)) + newMin


def almostEqual(x, y, tailCount):
    return math.fabs(x - y) < sys.float_info.epsilon * math.fabs(x + y) * tailCount or math.fabs(
        x - y) < sys.float_info.min


def threePointParabola(a, b, c, iterations):
    positions = []
    for t in range(1, int(iterations)):
        x = t / iterations
        q = b + (b - a) * x
        r = c + (c - b) * x
        p = r + (r - q) * x
        positions.append(p)
    return positions


def clamp(value, minValue=0.0, maxValue=1.0):
    """Clamps a value withing a max and min range

    :param value: value/number
    :type value: float
    :param minValue: clamp/stop any value below this value
    :type minValue: float
    :param maxValue: clamp/stop any value above this value
    :type maxValue: float
    :return clampedValue: clamped value as a float
    :rtype clampedValue: float
    """
    return max(minValue, min(value, maxValue))

