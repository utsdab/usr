import maya.cmds as cmds


def getPosRotRoo(mayaObj):
    """gets the position and orientation of an object including the rotate order in world space

    :param mayaObj: the object to record the pos and orient rot order
    :type mayaObj: str
    :return PosRotRoo: list of tuples in this order pos, rot, roo
    :rtype PosRotRoo: list
    """
    xformPos = cmds.xform(mayaObj, query=True, worldSpace=True, translation=True)
    xformRot = cmds.xform(mayaObj, query=True, worldSpace=True, rotation=True)
    xformRotOrder = cmds.xform(mayaObj, query=True, worldSpace=True, rotateOrder=True)
    return (xformPos, xformRot, xformRotOrder)


def setPosRotRoo(mayaObj, posRotRoo):
    """sets the position and orientation give the posRotRoo which is a list in world space
    ((posX, posY, posz), (rotX, rotY, rotZ), xyz)

    :param mayaObj:
    :type mayaObj:
    :param xformData:
    :type xformData:
    :return:
    :rtype:
    """
    cmds.xform(mayaObj, worldSpace=True, translation=posRotRoo[0])
    cmds.xform(mayaObj, worldSpace=True, rotation=posRotRoo[1])
    cmds.xform(mayaObj, worldSpace=True, rotateOrder=posRotRoo[2])
