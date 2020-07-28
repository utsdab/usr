from maya import cmds
import maya.api.OpenMaya as om2
import maya.mel as mel

from zoo.libs.maya import zapi
from zoo.libs.utils import zlogging

logger = zlogging.getLogger(__name__)


def matchObjTransRot(alignObj, srcObj, message=True):
    """Matches an alignObj to srcObj. Tries:

        1. Try 2017 and above new match
        2. Maya Constraint and delete constraint method

    :param alignObj: The object to affect/align, the object moved
    :type alignObj: str
    :param srcObj: The object to match to, this object doesn't move
    :type srcObj: str
    :param message: report the success message to the user?
    :type message: bool
    """
    try:  # 2017 and above match
        cmds.matchTransform([alignObj, srcObj], pos=1, rot=1, scl=0, piv=0)
        if message:
            om2.MGlobal.displayInfo('Object `{}` matched to `{}`'.format(alignObj, srcObj))
    except:  # will fail if not 2017+:
        cmds.delete(cmds.parentConstraint(srcObj, alignObj))
        if message:
            om2.MGlobal.displayInfo('note: `{}` object zoo simple align failed, '
                                    'using constraint instead'.format(srcObj))
        logger.debug('note: `{}` object zoo simple align failed, using constraint instead'.format(srcObj))


def matchObjTransRotSelection():
    """ Match Align based on selection (rotation and translation) Tries:

        1. Try 2017 and above new match
        2. Maya Constraint and delete constraint method

    Matches to the first selected object, all other objects are matched to the first in the selection
    """
    selobjs = cmds.ls(sl=True, type='transform') or []
    if not selobjs or len(selobjs) == 1:
        om2.MGlobal.displayWarning("At least two objects should be selected. Source, then target/s")
    if selobjs:
        srcObj = selobjs[0]
        for alignObj in selobjs[1:]:
            matchObjTransRot(alignObj, srcObj, message=False)
        om2.MGlobal.displayInfo("Objects matched to {}: {}".format(selobjs[0], selobjs[1:]))


def matchObjTransRotLists(alignObjList, srcObjList, message=False):
    """Matches an alignObj list to srcObj list, tries new match 2017+ if fail use Maya del parent constraint method

        1. Try 2017 new match
        2. Maya Constraint and delete constraint method

    :param alignObj: The object to affect/align
    :type alignObj: str
    :param srcObj: The object to match to, this object doesn't move
    :type srcObj: str
    :param message: report the success message to the user?
    :type message: bool
    """
    for i, alignObj in enumerate(alignObjList):
        matchObjTransRot(alignObj, srcObjList[i], message=message)


def matchObjRot(alignObj, srcObj):
    """Matches the rotation of a single obj to a srcObj.

    Tries new match 2017+ if fail use Maya del parent constraint method
    Will break if values objToAlign are already managed, connected/constrained

    :param alignObj: The object to align
    :type alignObj: str
    :param srcObj: The master object that the obj will align to
    :type srcObj: str
    """
    try:  # 2017 and above match
        cmds.matchTransform([alignObj, srcObj], pos=0, rot=1, scl=0, piv=0)
    except ValueError:
        cmds.delete(cmds.orientConstraint(srcObj, alignObj))


def matchObjTrans(alignObj, srcObj):
    """Matches the translation of a single obj to a srcObj.

    Tries new match 2017+ if fail use Maya del parent constraint method
    Will break if values objToAlign are already managed, connected/constrained

    :param alignObj: string The object to align
    :param src: string the master object that the obj will align to
    """
    try:  # 2017 and above match
        cmds.matchTransform([alignObj, srcObj], pos=1, rot=0, scl=0, piv=0)
    except ValueError:
        cmds.delete(cmds.pointConstraint(srcObj, alignObj))


def matchObjScale(alignObj, srcObj):
    """Matches the scale of a single obj to a srcObj.

    Tries new match 2017+ if fail use Maya del parent constraint method
    Will break if values objToAlign are already managed, connected/constrained

    :param objToAlign: string The object to align
    :param srcObj: string the master object that the obj will align to
    """
    try:  # 2017 and above match
        cmds.matchTransform([alignObj, srcObj], pos=0, rot=0, scl=1, piv=0)
    except ValueError:
        cmds.delete(cmds.scaleConstraint(srcObj, alignObj))


def matchObjPivot(alignObj, srcObj):
    """ Matches the pivot of the alignObj to the srcObj, Only compatible 2017+

    :param alignObj: The object to align (moved obj)
    :type alignObj: str
    :param srcObj: The object to match, this object doesn't move
    :type srcObj: str
    """
    try:  # 2017 and above match
        cmds.matchTransform([alignObj, srcObj], pos=0, rot=0, scl=0, piv=1)
    except ValueError:
        om2.MGlobal.displayWarning('This command is only valid in maya 2017 and above')


def matchAllSelection(translate=False, rotate=False, scale=False, pivot=False, message=True):
    """Match all selection, works for 2017 and above only

    :param translate: Match translate?
    :type translate: bool
    :param rotate: Match rotate?
    :type rotate: bool
    :param scale: Match scale?
    :type scale: bool
    :param pivot: Match pivot?
    :type pivot: bool
    :param message: report message to the user?
    :type message: bool
    """
    objList = cmds.ls(selection=True)
    if not objList:
        if message:
            om2.MGlobal.displayWarning("Please select objects")
        return
    cmds.matchTransform(objList, pos=translate, rot=rotate, scl=scale, piv=pivot)
    if message:
        om2.MGlobal.displayInfo("Objects matched `{}`".format(objList))


def findLowestVert(objLongName, worldSpace=True):
    """Finds the lowest point in world or local space, useful for snapping.  Can be mesh curve or nurbs

    :param objLongName: maya mesh long name as a string
    :type objLongName: str
    :param worldSpace: return the lowset point in world space True or local space False?
    :type worldSpace: bool

    :return index: the index of the current vertex
    :rtype index: int
    :return min: The y value, will be in local or world space depending on the worldSpace kwarg
    :rtype min: float
    """
    dagPath = zapi.nodeByName(objLongName).dagPath()
    # todo: can move to api package, as is api code
    dagPath.extendToShape()
    space = om2.MSpace.kObject
    if worldSpace:
        space = om2.MSpace.kWorld
    node = dagPath.node()
    if node.hasFn(om2.MFn.kMesh):
        mfn = om2.MFnMesh(dagPath)
        points = mfn.getPoints(space=space)
    elif node.hasFn(om2.MFn.kNurbsSurface):
        mfn = om2.MFnNurbsSurface(dagPath)
        points = mfn.cvPositions(space=space)
    elif node.hasFn(om2.MFn.kCurve):
        mfn = om2.MFnNurbsCurve(dagPath)
        points = mfn.cvPositions(space=space)

    min = None
    index = None
    for i in xrange(0, len(points)):
        if min is None:
            min = points[i].y
            index = i
        elif min > points[i].y:
            min = points[i].y
            index = i
    return index, min


def placeObjectOnGround(obj):
    """Places an object on the ground.

    The code builds a plane then matches the object to a plane, then deletes the plane

    :param obj: A maya transform object name
    :type obj: str
    """
    shapeList = cmds.listRelatives(obj, shapes=True, fullPath=True)
    if shapeList:  # check if mesh nurbs or curve
        nodeType = cmds.objectType(shapeList[0])
        if nodeType == "mesh" or nodeType == "nurbsSurface" or nodeType == "nurbsCurve":  # find lowest point
            vertIndex, yValue = findLowestVert(obj, worldSpace=True)  # find lowest vert/cv value in world space
            cmds.move(0.0, -yValue, 0.0, obj, relative=True, worldSpace=True)  # move
            return
    # else work off bounding box with cmds.align code
    planeObj = cmds.polyPlane(name="tempZooXXX_planeMatch")[0]
    cmds.align([obj, planeObj], alignToLead=True, yAxis="Min")
    cmds.delete(planeObj)


def placeObjectOnGroundList(objList):
    """Places a list of objects on the ground.

    :param objList: A list of maya transform object names
    :type objList: list
    """
    for obj in objList:
        placeObjectOnGround(obj)


def placeObjectOnGroundSel(message=True):
    """Places selected objects on the ground.

    :param message: Report the message to the user?
    :type message: bool
    """
    objList = cmds.ls(selection=True)
    if not objList:
        if message:
            om2.MGlobal.displayWarning("Please select an object")
        return
    # Check selection is a list of transform nodes.
    transformList = cmds.ls(objList, type="transform")
    if not transformList:
        if message:
            om2.MGlobal.displayWarning("Selected objects must be transform nodes, please select geo etc")
        return
    placeObjectOnGroundList(transformList)
    if message:
        om2.MGlobal.displayInfo("Objects placed on ground zero Y, `{}`".format(transformList))


def mayaAlignTool():
    """Enter Maya's Align Tool mode
    """
    mel.eval('setToolTo alignToolCtx')


def mayaSnapTogetherTool():
    """Enter Maya's Snap Together Tool mode
    """
    mel.eval('setToolTo snapTogetherToolCtx')


def snapPointToPoint():
    """Snap align 2 points to 2 points"""
    mel.eval('SnapPointToPoint;')


def snap2PointsTo2Points():
    """Snap align point to point"""
    mel.eval('Snap2PointsTo2Points;')


def snap3PointsTo3Points():
    """Snap align 3 points to 3 points"""
    mel.eval('Snap3PointsTo3Points;')

