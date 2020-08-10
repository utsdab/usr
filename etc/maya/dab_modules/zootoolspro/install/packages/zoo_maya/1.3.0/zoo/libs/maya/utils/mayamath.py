import math

from maya.api import OpenMaya as om2
from maya import OpenMaya as om1
from zoo.libs.utils import zoomath


def aimToNode(source, target, aimVector=None,
              upVector=None):
    """Function to aim one node at another using quaternions

    :param source: node to aim towards the target node
    :type source: om2.MObject
    :param target: the node which the source will aim at
    :type target: om2.MObject
    :param aimVector: the om2.MVector for the aim axis defaults to om2.MVector(1.0,0.0,0.0)
    :type aimVector: om2.MVector
    :param upVector: the om2.MVector for the upVector axis defaults to om2.MVector(0.0,1.0,0.0)
    :type upVector: om2.MVector
    """
    eyeAim = aimVector or om2.MVector(1.0, 0.0, 0.0)
    eyeUp = upVector or om2.MVector(0.0, 1.0, 0.0)

    targetDag = om2.MDagPath.getAPathTo(target)
    eyeDag = om2.MDagPath.getAPathTo(source)
    transformFn = om2.MFnTransform(eyeDag)
    eyePivotPos = transformFn.rotatePivot(om2.MSpace.kWorld)

    transformFn = om2.MFnTransform(targetDag)
    targetPivotPos = transformFn.rotatePivot(om2.MSpace.kWorld)

    aimVector = targetPivotPos - eyePivotPos
    eyeU = aimVector.normal()
    worldUp = om1.MGlobal.upAxis()
    eyeW = (eyeU ^ om2.MVector(worldUp.x, worldUp.y, worldUp.z)).normal()
    eyeV = eyeW ^ eyeU
    quatU = om2.MQuaternion(eyeAim, eyeU)

    upRotated = eyeUp.rotateBy(quatU)
    # try:
    try:
        angle = math.acos(upRotated * eyeV)

    except (ZeroDivisionError, ValueError):
        return  # if already aligned then we just return

    quatV = om2.MQuaternion(angle, eyeU)

    if not eyeV.isEquivalent(upRotated.rotateBy(quatV), 1.0e-5):
        angle = (2 * math.pi) - angle
        quatV = om2.MQuaternion(angle, eyeU)

    quatU *= quatV
    # align the aim
    transformFn.setObject(eyeDag)
    transformFn.setRotation(quatU, om2.MSpace.kWorld)


def quaterionDot(qa, qb):
    return qa.w * qb.w + qa.x * qb.x + qa.y * qb.y + qa.z * qb.z


def slerp(qa, qb, weight):
    qc = om2.MQuaternion()
    dot = quaterionDot(qa, qb)
    if abs(dot >= 1.0):
        qc.w = qa.w
        qc.x = qa.x
        qc.y = qa.y
        qc.z = qa.z
        return qc
    halfTheta = math.acos(dot)
    sinhalfTheta = math.sqrt(1.0 - dot * dot)
    if zoomath.almostEqual(math.fabs(sinhalfTheta), 0.0, 2):
        qc.w = (qa.w * 0.5 + qb.w * 0.5)
        qc.x = (qa.x * 0.5 + qb.x * 0.5)
        qc.y = (qa.y * 0.5 + qb.y * 0.5)
        qc.z = (qa.z * 0.5 + qb.z * 0.5)
        return qc

    ratioA = math.sin((1.0 - weight) * halfTheta) / sinhalfTheta
    ratioB = math.sin(weight * halfTheta) / sinhalfTheta

    qc.w = (qa.w * ratioA + qb.w * ratioB)
    qc.x = (qa.x * ratioA + qb.x * ratioB)
    qc.y = (qa.y * ratioA + qb.y * ratioB)
    qc.z = (qa.z * ratioA + qb.z * ratioB)
    return qc


def toEulerXYZ(rotMatrix, degrees=False):
    rotXZ = rotMatrix[2]
    if zoomath.almostEqual(rotXZ, 1.0, 2):
        z = math.pi
        y = -math.pi * 0.5
        x = -z + math.atan2(-rotMatrix[4], -rotMatrix[7])
    elif zoomath.almostEqual(rotXZ, -1.0, 2):
        z = math.pi
        y = math.pi * 0.5
        x = z + math.atan2(rotMatrix[4], rotMatrix[7])
    else:
        y = -math.asin(rotXZ)
        cosY = math.cos(y)
        x = math.atan2(rotMatrix[6] * cosY, rotMatrix[10] * cosY)
        z = math.atan2(rotMatrix[1] * cosY, rotMatrix[0] * cosY)
    angles = x, y, z
    if degrees:
        return map(math.degrees, angles)
    return om2.MEulerRotation(angles)


def toEulerXZY(rotMatrix, degrees=False):
    rotYY = rotMatrix[1]
    z = math.asin(rotYY)
    cosZ = math.cos(z)

    x = math.atan2(-rotMatrix[9] * cosZ, rotMatrix[5] * cosZ)
    y = math.atan2(-rotMatrix[2] * cosZ, rotMatrix[0] * cosZ)

    angles = x, y, z

    if degrees:
        return map(math.degrees, angles)

    return om2.MEulerRotation(angles)


def toEulerYXZ(rotMatrix, degrees=False):
    rotZ = rotMatrix[6]
    x = math.asin(rotZ)
    cosX = math.cos(x)

    y = math.atan2(-rotMatrix[2] * cosX, rotMatrix[10] * cosX)
    z = math.atan2(-rotMatrix[4] * cosX, rotMatrix[5] * cosX)

    angles = x, y, z

    if degrees:
        return map(math.degrees, angles)

    return om2.MEulerRotation(angles)


def toEulerYZX(rotMatrix, degrees=False):
    rotYX = rotMatrix[4]
    z = -math.asin(rotYX)
    cosZ = math.cos(z)

    x = math.atan2(rotMatrix[6] * cosZ, rotMatrix[5] * cosZ)
    y = math.atan2(rotMatrix[8] * cosZ, rotMatrix[0] * cosZ)

    angles = x, y, z

    if degrees:
        return map(math.degrees, angles)

    return om2.MEulerRotation(angles)


def toEulerZXY(rotMatrix, degrees=False):
    rotZY = rotMatrix[9]
    x = -math.asin(rotZY)
    cosX = math.cos(x)

    z = math.atan2(rotMatrix[1] * cosX, rotMatrix[5] * cosX)
    y = math.atan2(rotMatrix[8] * cosX, rotMatrix[10] * cosX)

    angles = x, y, z

    if degrees:
        return map(math.degrees, angles)

    return om2.MEulerRotation(angles)


def toEulerZYX(rotMatrix, degrees=False):
    rotZX = rotMatrix[8]
    y = math.asin(rotZX)
    cosY = math.cos(y)

    x = math.atan2(-rotMatrix[9] * cosY, rotMatrix[10] * cosY)
    z = math.atan2(-rotMatrix[4] * cosY, rotMatrix[0] * cosY)

    angles = x, y, z

    if degrees:
        return map(math.degrees, angles)

    return om2.MEulerRotation(angles)


def toEulerFactory(rotMatrix, rotateOrder, degrees=False):
    if rotateOrder == om2.MTransformationMatrix.kXYZ:
        return toEulerXYZ(rotMatrix, degrees)
    elif rotateOrder == om2.MTransformationMatrix.kXZY:
        return toEulerXZY(rotMatrix, degrees)
    elif rotateOrder == om2.MTransformationMatrix.kYXZ:
        return toEulerYXZ(rotMatrix, degrees)
    elif rotateOrder == om2.MTransformationMatrix.kYZX:
        return toEulerYZX(rotMatrix, degrees)
    elif rotateOrder == om2.MTransformationMatrix.kZXY:
        return toEulerZXY(rotMatrix, degrees)
    return toEulerZYX(rotMatrix, degrees)


def mirrorXY(rotationMatrix):
    rotMat = om2.MMatrix(rotationMatrix)
    rotMat[0] *= -1
    rotMat[1] *= -1
    rotMat[4] *= -1
    rotMat[5] *= -1
    rotMat[8] *= -1
    rotMat[9] *= -1
    return rotMat


def mirrorYZ(rotationMatrix):
    rotMat = om2.MMatrix(rotationMatrix)
    rotMat[1] *= -1
    rotMat[2] *= -1
    rotMat[5] *= -1
    rotMat[6] *= -1
    rotMat[9] *= -1
    rotMat[10] *= -1
    return rotMat


def mirrorXZ(rotationMatrix):
    rotMat = om2.MMatrix(rotationMatrix)
    rotMat[0] *= -1
    rotMat[2] *= -1
    rotMat[4] *= -1
    rotMat[6] *= -1
    rotMat[8] *= -1
    rotMat[10] *= -1
    return rotMat
