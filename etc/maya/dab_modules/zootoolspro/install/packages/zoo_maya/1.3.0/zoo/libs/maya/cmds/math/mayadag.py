from math import pow, sqrt

import maya.cmds as cmds
import maya.api.OpenMaya as om2

from zoo.libs.maya.cmds.objutils import moveorient

def findDistanceTwoPoints(startPosition, endPosition):
    """Finds the distance between two positions in 3d space

    :param startPosition: Start postition to measure
    :type startPosition: tuple
    :param endPosition: End position to measure
    :type endPosition: tuple
    :return distance:
    :rtype distance:
    """
    return (om2.MVector(endPosition) - om2.MVector(startPosition)).length()


def straightLineSpacing(startPosition, endPosition, sectionCount, neg1=True):
    """given the count of sections, return the length of each space between two points

    :param startPosition: The start position to be measured xyz
    :type startPosition: tuple
    :param endPosition: The end position to be measured xyz
    :type endPosition: tuple
    :param sectionCount: The amount of divisions/sections in the straight line
    :type sectionCount: int
    :param neg1: for joints etc where the last object should be built at the end point
    :type neg1: bool
    :return spacingLength: The length of each section
    :rtype spacingLength: float
    """
    spineDistance = findDistanceTwoPoints(startPosition, endPosition)
    if sectionCount:
        spacingLength = spineDistance / (float(sectionCount) - neg1)
        return spacingLength
    om2.MGlobal.displayError("Section Count Can't be zero")
    return None


def distanceTwoObjs(startObj, endObj):
    """Finds the distance between two maya objects

    :param startObj: The first object to be measured
    :type startObj: str
    :param endObj: The second object to be measured
    :type endObj: str
    :return distance: the distance between the two objects
    :rtype distance: float
    """
    startPosition = cmds.xform(startObj, q=1, ws=1, translation=1)
    endPosition = cmds.xform(endObj, q=1, ws=1, translation=1)
    distance = findDistanceTwoPoints(startPosition, endPosition)
    return distance


def straightLineSpacingObjs(startObj, endObj, sectionCount):
    """Given two objects and a section count, find how long each section is

    :param startObj: The first object to be measured
    :type startObj: str
    :param endObj: The second object to be measured
    :type endObj: str
    :param sectionCount: The amount of divisions/sections in the straight line
    :type sectionCount: int
    :return spacingLength: The length of each section
    :rtype spacingLength: float
    """
    startPosition = cmds.xform(startObj, q=1, ws=1, translation=1)
    endPosition = cmds.xform(endObj, q=1, ws=1, translation=1)
    spacingLength = straightLineSpacing(startPosition, endPosition, sectionCount)
    return spacingLength


def getAimTwoPositions(startPosition, endPosition, worldUpVector=[0, 1, 0]):
    """get the orientation and position of an aim between two positions in 3d space
    Position will match start position
    Orientation will aim towards end position given the upVector
    Returns as (pos, Rot, Roo)

    :param startPosition:
    :type startPosition:
    :param endPosition:
    :type endPosition:
    :param worldUpVector:
    :type worldUpVector:
    :return:
    :rtype:
    """
    # build aim for orientation, should be math
    startNull = cmds.spaceLocator()
    endNull = cmds.spaceLocator()
    cmds.move(startPosition[0], startPosition[1], startPosition[2], startNull)
    cmds.move(endPosition[0], endPosition[1], endPosition[2], endNull)
    aimConstraint = (cmds.aimConstraint(endNull, startNull, worldUpVector=worldUpVector))
    # record pos and orientation in a matrix
    posRotRoo = moveorient.getPosRotRoo(startNull)
    # cleanup
    cmds.delete(aimConstraint, startNull, endNull)  # delete null objects
    return posRotRoo