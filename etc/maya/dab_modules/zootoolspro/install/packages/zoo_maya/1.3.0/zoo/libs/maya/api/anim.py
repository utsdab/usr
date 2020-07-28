import contextlib

from maya.api import OpenMayaAnim as om2Anim
from maya.api import OpenMaya as om2
from zoo.libs.utils import general

FRAME_TO_UNIT = {25: om2.MTime.k25FPS,
                 30: om2.MTime.k30FPS,
                 48: om2.MTime.k48FPS,
                 2: om2.MTime.k2FPS,
                 3: om2.MTime.k3FPS,
                 4: om2.MTime.k4FPS,
                 5: om2.MTime.k5FPS,
                 6: om2.MTime.k6FPS,
                 8: om2.MTime.k8FPS,
                 10: om2.MTime.k10FPS,
                 12: om2.MTime.k12FPS,
                 15: om2.MTime.k15FPS,
                 16: om2.MTime.k16FPS,
                 20: om2.MTime.k20FPS,
                 23.976: om2.MTime.k23_976FPS,
                 24: om2.MTime.k24FPS,
                 29.9: om2.MTime.k29_97DF,
                 29.97: om2.MTime.k29_97FPS,
                 40: om2.MTime.k40FPS,
                 47.952: om2.MTime.k47_952FPS,
                 50: om2.MTime.k50FPS,
                 59.94: om2.MTime.k59_94FPS,
                 60: om2.MTime.k60FPS,
                 75: om2.MTime.k75FPS,
                 80: om2.MTime.k80FPS,
                 100: om2.MTime.k100FPS,
                 120: om2.MTime.k120FPS,
                 125: om2.MTime.k125FPS,
                 150: om2.MTime.k150FPS,
                 200: om2.MTime.k200FPS,
                 240: om2.MTime.k240FPS,
                 250: om2.MTime.k250FPS,
                 300: om2.MTime.k300FPS,
                 375: om2.MTime.k375FPS,
                 400: om2.MTime.k400FPS,
                 500: om2.MTime.k500FPS,
                 600: om2.MTime.k600FPS,
                 750: om2.MTime.k750FPS,
                 1200: om2.MTime.k1200FPS,
                 1500: om2.MTime.k1500FPS,
                 2000: om2.MTime.k2000FPS,
                 3000: om2.MTime.k3000FPS,
                 6000: om2.MTime.k6000FPS,
                 44100: om2.MTime.k44100FPS,
                 48000: om2.MTime.k48000FPS}

UNIT_TO_FRAME = {om2.MTime.k25FPS: 25,
                 om2.MTime.k30FPS: 30,
                 om2.MTime.k48FPS: 48,
                 om2.MTime.k2FPS: 2,
                 om2.MTime.k3FPS: 3,
                 om2.MTime.k4FPS: 4,
                 om2.MTime.k5FPS: 5,
                 om2.MTime.k6FPS: 6,
                 om2.MTime.k8FPS: 8,
                 om2.MTime.k10FPS: 10,
                 om2.MTime.k12FPS: 12,
                 om2.MTime.k15FPS: 15,
                 om2.MTime.k16FPS: 16,
                 om2.MTime.k20FPS: 20,
                 om2.MTime.k23_976FPS: 23.976,
                 om2.MTime.k24FPS: 24,
                 om2.MTime.k29_97DF: 29.9,
                 om2.MTime.k29_97FPS: 29.97,
                 om2.MTime.k40FPS: 40,
                 om2.MTime.k47_952FPS: 47.952,
                 om2.MTime.k50FPS: 50,
                 om2.MTime.k59_94FPS: 59.94,
                 om2.MTime.k60FPS: 60,
                 om2.MTime.k75FPS: 75,
                 om2.MTime.k80FPS: 80,
                 om2.MTime.k100FPS: 100,
                 om2.MTime.k120FPS: 120,
                 om2.MTime.k125FPS: 125,
                 om2.MTime.k150FPS: 150,
                 om2.MTime.k200FPS: 200,
                 om2.MTime.k240FPS: 240,
                 om2.MTime.k250FPS: 250,
                 om2.MTime.k300FPS: 300,
                 om2.MTime.k375FPS: 375,
                 om2.MTime.k400FPS: 400,
                 om2.MTime.k500FPS: 500,
                 om2.MTime.k600FPS: 600,
                 om2.MTime.k750FPS: 750,
                 om2.MTime.k1200FPS: 1200,
                 om2.MTime.k1500FPS: 1500,
                 om2.MTime.k2000FPS: 2000,
                 om2.MTime.k3000FPS: 3000,
                 om2.MTime.k6000FPS: 6000,
                 om2.MTime.k44100FPS: 44100,
                 om2.MTime.k48000FPS: 48000}


def currentTimeInfo():
    """Returns a dict of all the current timeline settings
    
    :rtype: dict

    .. code-block:: python

        currentTimeInfo()
        # result {"currentTime": om2.MTime,
                "start": 0,
                "end": 1,
                "unit": 12,
                "fps": 25}

    """
    current = om2Anim.MAnimControl.currentTime()
    return {"currentTime": current,
            "start": om2Anim.MAnimControl.minTime(),
            "end": om2Anim.MAnimControl.maxTime(),
            "unit": current.uiUnit(),
            "fps": UNIT_TO_FRAME[current.uiUnit()]}


def setCurrentRange(start, end, newCurrentFrame):
    """Set's maya's frame range and the current time number.

    :param start: The start of the frame range to set
    :type start: int
    :param end: The end of the frame range to set
    :type end: int
    :param newCurrentFrame: The frame number to set maya's current time to.
    :type newCurrentFrame: ints
    """
    currentUnit = om2Anim.MAnimControl.currentTime().unit
    start = om2.MTime(start, currentUnit)
    end = om2.MTime(end, currentUnit)
    newTime = om2.MTime(newCurrentFrame, currentUnit)
    om2Anim.MAnimControl.setMinMaxTime(start, end)
    om2Anim.MAnimControl.setAnimationStartEndTime(start, end)
    om2Anim.MAnimControl.setCurrentTime(newTime)


def formatFrameRange():
    """Return's mayas current frame range as a format string.

    :return: "0:100"  startframe:endFrame
    :rtype: str
    """
    info = currentTimeInfo()
    start, end = int(info["start"].value), int(info["end"].value)
    return ":".join([str(start), str(end)]) + "({})".format(end - start)


def formatFrame():
    """Returns the current frame rate as a formatted string.
    
    :return: "0:100(30 FPS)" startFrame:endFrame(FPS)
    :rtype: str
    """
    info = currentTimeInfo()
    start, end = int(info["start"].value), int(info["end"].value)
    return ":".join([str(start), str(end)]) + "({} FPS)".format(info["fps"])


def formatCurrentTime():
    currentTime = om2Anim.MAnimControl.currentTime()
    minTime = om2Anim.MAnimControl.minTime()
    return general.formatFrameToTime(minTime.value, currentTime.value, UNIT_TO_FRAME[currentTime.uiUnit()])


@contextlib.contextmanager
def maintainTime():
    """Context manager for preserving (resetting) the time after the context"""
    currentTime = om2Anim.MAnimControl.currentTime()
    try:
        yield
    finally:
        om2Anim.MAnimControl.setCurrentTime(currentTime)


def iterFrameRangeDGContext(start, end):
    """Generator function to iterate over a time range returning a MDGContext for the current frame.

    :param start: the start frame
     :type start: int
    :param end: the end frame
    :type end: int
    :return: Returns a generator function with each element being a MDGContext with the current frame applied
    :rtype: Generator(om2.MDGContext)
    """
    currentTime = om2Anim.MAnimControl.currentTime()
    perFrame = om2.MTime(start, currentTime.unit)
    for frame in range(start, end + 1):
        context = om2.MDGContext(perFrame)
        yield context
        perFrame += 1
