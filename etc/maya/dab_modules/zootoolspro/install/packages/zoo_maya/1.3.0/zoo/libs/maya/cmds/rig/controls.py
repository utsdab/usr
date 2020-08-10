import os

import maya.cmds as cmds
import maya.api.OpenMaya as om2

from zoo.libs.zooscene.constants import DEPENDENCY_FOLDER

from zoo.libs.utils import colour
from zoo.libs.maya.cmds.objutils import shapenodes, namehandling, objcolor, joints, alignutils, filtertypes, \
    scaleutils, attributes, objhandling
from zoo.libs.maya.cmds.rig import nodes as nodeCreate
from zoo.libs.maya import shapelib
from zoo.libs.maya.api import nodes
from zoo.libs.command import executor
from zoo.libs.maya.utils import general

NEW_CONTROL = "newControl"
CONTROLS_GRP_SUFFIX = "controls_grp"
ZOO_TRANSLATE_TRACK_ATTR = "zooTranslateTrack"
ZOO_TRANSLATE_DEFAULT_ATTR = "zooTranslateDefault"
ZOO_ROTATE_TRACK_ATTR = "zooRotateTrack"
ZOO_ROTATE_DEFAULT_ATTR = "zooRotateDefault"
ZOO_SCALE_TRACK_ATTR = "zooScaleTrack"
ZOO_SCALE_DEFAULT_ATTR = "zooScaleDefault"
ZOO_COLOR_TRACK_ATTR = "zooColorTrack"
ZOO_COLOR_DEFAULT_ATTR = "zooColorDefault"
ZOO_SHAPE_TRACK_ATTR = "zooShapeTrack"
ZOO_SHAPE_DEFAULT_ATTR = "zooShapeDefault"
XYZ_LIST = ["x", "y", "z"]
RGB_LIST = ["r", "g", "b"]
CONTROL_BUILD_TYPE_LIST = ["Joint, Shape Parent Ctrl", "Match Selection Only", "Constrain Obj, Cnstn Ctrl",
                           "Constrain Obj, Parent Ctrl", "Constrain Obj, Float Ctrl"]

ZOO_CONTROLTRACK_VECTOR_LIST = [ZOO_TRANSLATE_TRACK_ATTR, ZOO_TRANSLATE_DEFAULT_ATTR,
                                ZOO_ROTATE_TRACK_ATTR, ZOO_ROTATE_DEFAULT_ATTR,
                                ZOO_SCALE_TRACK_ATTR, ZOO_SCALE_DEFAULT_ATTR]
ZOO_CONTROLTRACK_RGB_LIST = [ZOO_COLOR_TRACK_ATTR, ZOO_COLOR_DEFAULT_ATTR]
ZOO_CONTROLTRACK_STRING_LIST = [ZOO_SHAPE_TRACK_ATTR, ZOO_SHAPE_DEFAULT_ATTR]

ZOO_TEMPBREAK_NETWORK = "breakTrack_network"
ZOO_TEMPBREAK_CTRL_ATTR = "zoo_ctrl_tempBreakTrack"
ZOO_TEMPBREAK_GRP_ATTR = "zoo_grp_tempBreakTrack"
ZOO_TEMPBREAK_MASTER_ATTR = "zoo_mstr_tempBreakTrack"

# Set rot up axis based on lists
X_UP = 0
X_DOWN = 1
Y_UP = 2
Y_DOWN = 3
Z_UP = 4
Z_DOWN = 5

# Set rot axis based on strings
ROT_AXIS_DICT = {"+x": (0.0, -90.0, 90.0),
                 "-x": (0.0, 90.0, 90.0),
                 "+y": (0.0, 0.0, 0.0),
                 "-y": (0.0, 180.0, 0.0),
                 "+z": (90.0, 0.0, 0.0),
                 "-z": (-90.0, 0.0, 0.0)}


# ---------------------------
# M-OBJECT (SHOULD MOVE)
# ---------------------------


def convertMObjsHandlesToStringList(mObjectList):
    """Converts MObjects Handles to a list of strings

    :return selection: object names as strings
    :rtype selection: list(str)
    """
    # TODO needs to be moved or switched to daves code
    objList = list()
    for i in mObjectList:
        mHandle = om2.MObjectHandle(i)
        if not mHandle.isValid() or not mHandle.isAlive():
            continue
        objList.append(nodes.nameFromMObject(mHandle.object()))
    return objList


def mObjectFromString(objName):
    """Returns an mObject from a Maya string object name, preferably a long name.

    :param objName: the string name of a Maya object or node
    :type objName: str
    :return: The maya node as an MObject
    :rtype: MObject
    """
    # TODO needs to be moved or switched to daves code
    mSel = om2.MSelectionList().add(objName)
    return mSel.getDependNode(0)


def renameMobject(MObjectNode, newname):
    """Renames an MObject dependency node

    :param MObjectNode: A maya dependency node as an MObject
    :type MObjectNode: MObject
    """
    dagMod = om2.MDagModifier()
    dagMod.renameNode(MObjectNode, newname)
    dagMod.doIt()


# ---------------------------
# COPY CONTROL CLASS FOR GLOBAL ACCESS
# ---------------------------


class ControlClipboard:
    def __init__(self):
        """This small class is used to store the copied control information"""
        self.copyCtrl = ""
        self.copyTranslate = None
        self.copyRotate = None
        self.copyScale = None
        self.copyColor = None
        self.copyShape = None

    def pasteControl(self):
        """Pastes controls from the function pasteControl(), handles error checking and restoring the copied data

        :return self.copyCtrl: The copied control object
        :rtype self.copyCtrl: str
        :return pasteObjs: The objects that have been pasted, if none will be an empty list
        :rtype pasteObjs: list(str)
        """
        if not self.copyTranslate:
            om2.MGlobal.displayWarning("No controls found in clipboard, please copy")
            return self.copyCtrl, list()
        if not cmds.objExists(self.copyCtrl):
            om2.MGlobal.displayWarning("The copied control must exist in the scene, please copy another control")
            return self.copyCtrl, list()
        pasteObjs = cmds.ls(selection=True, type="transform", long=True)
        pasteControl(pasteObjs, self.copyCtrl, self.copyTranslate, self.copyRotate, self.copyScale,
                     self.copyColor, self.copyShape)
        om2.MGlobal.displayInfo("Success: Control pasted from "
                                "`{}`, to the controls `{}`".format(namehandling.getShortName(self.copyCtrl),
                                                                    namehandling.getShortNameList(pasteObjs)))
        return self.copyCtrl, pasteObjs

    def copyControl(self):
        """Copies the selected controls from the function copyControl(), stores the data inside the class
        """
        selObjs = cmds.ls(selection=True, type="transform", long=True)
        if selObjs:  # filter only the transforms with curves
            selObjs = filtertypes.filterTypeReturnTransforms(selObjs, children=False, shapeType="nurbsCurve")
        if not selObjs:
            om2.MGlobal.displayWarning("No curves found to copy. Please select a curve control.")
            return
        self.copyCtrl = selObjs[0]
        self.copyTranslate, self.copyRotate, self.copyScale, self.copyColor, self.copyShape = copyControl(self.copyCtrl)
        om2.MGlobal.displayInfo("Control information copied `{}`".format(namehandling.getShortName(self.copyCtrl)))


CNTRL_CLIPBOARD_INSTANCE = ControlClipboard()  # for global Maya access copy/paste controls


# ---------------------------
# CURVE LINE THICKNESS
# ---------------------------


def curveLinethickness(curveTransform):
    """Returns the line thickness (attribute lineWidth) of the first curve shape found under the obj curveTransform

    :param curveTransform: A transform object with a nurbsCurve shape node
    :type curveTransform: str
    :return lineWidth: The width of the curve's line
    :rtype lineWidth: int
    """

    curveShapes = filtertypes.shapeTypeFromTransformOrShape([curveTransform], shapeType="nurbsCurve")
    if not curveShapes:
        return 0
    return cmds.getAttr("{}.lineWidth".format(curveShapes[0]))


def setCurveLineThickness(nodeList, lineWidth=-1):
    """Changes the lineWidth attribute of a curve (control) making the lines thicker or thinner.

    -1 is the default line width and used the global lineWidth setting in Maya's preferences, other values override.

    :param nodeList: Maya node list of any type, will only affect transforms with or "nurbsCurve" shapes
    :type nodeList: list(str)
    :param lineWidth: The width of the curve's lines in pixels, -1 is default and will use global pref settings
    :type lineWidth: int
    """
    curveShapes = filtertypes.shapeTypeFromTransformOrShape(nodeList, shapeType="nurbsCurve")
    for curve in curveShapes:
        cmds.setAttr("{}.lineWidth".format(curve), lineWidth)


# ---------------------------
# SAVE CONTROLS
# ---------------------------


def saveControlSelected(controlNewName, directory, dependenciesFolder=True, message=True):
    """Saves the first selected curve (transform node) with shapelib.saveToDirectory()

    Creates an empty dependencies folder if dependenciesFolder=True

    :param controlNewName: The name of the new control
    :type controlNewName: str
    :param directory: The path of the directory to save into
    :type directory: str
    :param dependenciesFolder: True will create an empty dependencies folder
    :type dependenciesFolder: bool
    :param message: Report the messages to the user?
    :type message: bool
    :return: The file path to the newly created shape file
    :rtype: str
    """
    curveTransformList = filtertypes.filterByNiceTypeKeepOrder(filtertypes.CURVE,
                                                               searchHierarchy=False,
                                                               selectionOnly=True,
                                                               dag=False,
                                                               removeMayaDefaults=False,
                                                               transformsOnly=True,
                                                               message=True)
    if not curveTransformList:
        if message:
            om2.MGlobal.displayWarning("Please select a curve object (transform)")
        return
    # requires an MObject of the shape node
    data, path = shapelib.saveToDirectory(nodes.asMObject(curveTransformList[0]), controlNewName, directory)
    if dependenciesFolder:
        dependenciesDirPath = os.path.join(directory, "_".join([controlNewName, DEPENDENCY_FOLDER]))
        os.mkdir(dependenciesDirPath)
    if data and message:
        om2.MGlobal.displayInfo("Success: Curve `{}` saved to `{}`".format(controlNewName, path))
    return data, path


# ---------------------------
# CREATE CONTROLS
# ---------------------------


def createControlCurve(folderpath="", ctrlName="control", curveScale=(1.0, 1.0, 1.0), designName='circle',
                       addSuffix=True, shapeParent=None, rotateOffset=(0.0, 0.0, 0.0), trackScale=True, lineWidth=-1,
                       rgbColor=None):
    """Creates the control curve, using a curve shape/design from the shape library shapelib.loadAndCreateFromLib()

    Also sizes and rotates 90 degrees down X+ if rotateOffset is True

    :param ctrlName: The name of the control to create (or shapeNodes shapeParent), if addSuffix also adds _ctrl
    :type ctrlName: str
    :param curveScale: The scale of each control in Maya units.  Is measured in radius, not width.
    :type curveScale: list(float)
    :param designName: The shape/look/design of the control, for list see shapelib.shapeNames() from the shapes dir
    :type designName: str
    :param addSuffix: Adds an underscore and suffix from filterTypes.CONTROLLER_SX usually "ctrl"
    :type addSuffix: bool
    :param shapeParent: If specified will shape parent the new curve to an existing object, long Name required.
    :type shapeParent: str
    :param rotateOffset: rotate offset of the control, is a CV rotation offset not object
    :type rotateOffset: list(float)
    :param trackScale: Add tracking attributes for tracking the scale of the control, will not appear in channel box
    :type trackScale: bool
    :param lineWidth: The width of the curve's lines in pixels, -1 is default and will use global pref settings
    :type lineWidth: int
    :param rgbColor: rgb color as a linear float [0.1, 0.3, 1.0] If None the color setting will be ignored
    :type rgbColor: list(float)
    :return curveLongNameList: If shapeParent returns a list of shape nodes, otherwise returns a list of one transform
    :rtype curveLongNameList: list(str)
    """
    if addSuffix:
        ctrlName = '_'.join([ctrlName, filtertypes.CONTROLLER_SX])
    if shapeParent:
        ctrlName = '_'.join([ctrlName, "Shape"])
    placementMobj = None
    if shapeParent:  # parent needs to be converted to an mObject
        placementMobj = nodes.asMObject(shapeParent)
    exe = executor.Executor()
    if folderpath:  # use the folder path
        parentMObject, curveMObjects = exe.execute("zoo.maya.curves.createFromFilePath",
                                                   designName=designName,
                                                   folderpath=folderpath,
                                                   parent=placementMobj)
    else:  # use the library paths
        parentMObject, curveMObjects = exe.execute("zoo.maya.curves.createFromLib",
                                                   libraryName=designName,
                                                   parent=placementMobj)
    if shapeParent:  # will be shape nodes
        for shape in curveMObjects:
            renameMobject(shape, ctrlName)
        curveLongNameList = convertMObjsHandlesToStringList(curveMObjects)
    else:  # will be a single transform node
        renameMobject(curveMObjects[0], ctrlName)
        curveLongName = convertMObjsHandlesToStringList(curveMObjects)[0]
        curveLongNameList = [curveLongName]
    if rotateOffset != (0, 0, 0):
        shapenodes.rotateObjListCVs(curveLongNameList, rotateOffset)
    if curveScale != (1.0, 1.0, 1.0):
        shapenodes.scaleObjListCVs(curveLongNameList, curveScale)
    if lineWidth != -1:
        setCurveLineThickness(curveLongNameList, lineWidth=lineWidth)
    if rgbColor:
        objcolor.setColorListRgb(curveLongNameList, rgbColor, displayMessage=False, linear=True)
    if trackScale:  # add the attribute that tracks the control's cv scale
        if not shapeParent:  # then assign the new transform node as shapeParent
            shapeParent = curveLongNameList[0]
        addTrackAttrs(shapeParent, curveScale, designName=designName, color=rgbColor)
    return curveLongNameList  # curve as a longname string


def createControlCurveList(jointList, folderpath="", curveScale=(1.0, 1.0, 1.0), rotateOffset=(0.0, 0.0, 0.0),
                           designName='circle', trackScale=True, lineWidth=-1, rgbColor=None):
    """Creates multiple control curves from a joint list, will shape parent the curves

    :param jointList: the joints to build controls on
    :type jointList: str
    :param curveScale: The size of the curve in Maya units
    :type curveScale: float
    :param rotateOffset: rotate offset of the control, is a CV rotation offset not object
    :type rotateOffset: list(float)
    :param designName: The shape/look/design of the control, control names can be found in skeleton builder's folder
    :type designName: str
    :param trackScale: Add tracking attributes for tracking the scale of the control, will not appear in channel box
    :type trackScale: bool
    :param lineWidth: The width of the curve's lines in pixels, -1 is default and will use global pref settings
    :type lineWidth: int
    :param rgbColor: rgb color as a linear float [0.1, 0.3, 1.0] If None the color setting will be ignored
    :type rgbColor: list(float)
    :return controlCrv: Each control returns a list of shape nodes, so will be a list(list(shape nodes))
    :rtype controlCrv: list(list(str))
    """
    controlCurveShapes = list()
    for i, jnt in enumerate(jointList):
        jntPureName = namehandling.mayaNamePartTypes(jnt)[2]
        controlCrvList = createControlCurve(folderpath=folderpath,
                                            ctrlName=jntPureName,
                                            curveScale=curveScale,
                                            designName=designName,
                                            shapeParent=jnt,
                                            rotateOffset=rotateOffset,
                                            addSuffix=False,
                                            trackScale=trackScale,
                                            lineWidth=lineWidth,
                                            rgbColor=rgbColor)
        controlCurveShapes.append(controlCrvList)
    return controlCurveShapes


def groupInPlace(objName, objUuid=None, grpSwapSuffix=False, includeScale=False):
    """Groups an object, with the grp matching the object's pivot

    :param objName: Object name to be grouped, usually a joint, should be a unique or longname
    :type objName: str
    :param objUuid: Optional uuid of the object to be grouped, usually a joints uuid.  Will ignore the name.
    :type objUuid: str
    :param grpSwapSuffix: Will swap the suffix, ie jnt "joint1_jnt" grp is named "joint1_grp" not "joint1_jnt_grp"
    :type grpSwapSuffix: str
    :return grp: The new group name
    :rtype grp: str
    :return objName: The object name, now modified if a long name
    :rtype objName: list
    :return grpUuid: Optional grp uuid, useful if multiple re-parenting withing a single hierarchy, can return as None
    :rtype grpUuid: list
    :return objUuid: Optional obj uuid, useful if multiple re-parenting withing a single hierarchy, can return as None
    :rtype objUuid: list
    """
    grpUuid = None
    if objUuid:  # if uuid then use the most current long name
        objName = cmds.ls(objUuid, long=True)[0]
    pureName = namehandling.mayaNamePartTypes(objName)[2]
    grp = "_".join([pureName, filtertypes.GROUP_SX])
    parentObj = cmds.listRelatives(objName, parent=True, fullPath=True)
    grp = cmds.group(name=grp, empty=True)
    if grpSwapSuffix:  # grp will already be named "joint1_jnt_grp", so remove index -2
        grp = namehandling.editIndexItem(grp, -2, mode=namehandling.EDIT_INDEX_REMOVE)
    if objUuid:  # then also return the grp uuid
        grpUuid = cmds.ls(grp, uuid=True)[0]
    if parentObj is not None:  # parent excluding None which is world
        grp = cmds.parent(grp, parentObj)[0]
    cmds.matchTransform([grp, objName], pos=1, rot=1, scl=includeScale, piv=0)
    objName = cmds.parent(objName, grp)[0]
    return grp, objName, grpUuid, objUuid


def groupInPlaceList(objList, grpSwapSuffix=False):
    """Groups each object from an object list, with each new group matching the object's pivot and rotation.

    Objects will be automatically zeroed in most cases. Handles longnames with uuids.  Returns new longnames.

    :param objList: A list of object list to group individually
    :type objList: list
    :param grpSwapSuffix: Will remove the suffix, ie jnt "joint1_jnt" grp is named "joint1_grp" not "joint1_jnt_grp"
    :type grpSwapSuffix: str
    :return grpList: The new groups listed as their long names
    :rtype grpList: list(str)
    :return objList: The object list of long names, if long have now probably been modified
    :rtype objList: list(str)
    """
    grpList = list()
    grpUuidList = list()
    objUuidList = list()
    uuidList = cmds.ls(objList, uuid=True)
    for i, obj in enumerate(objList):  # Grouping will mess with long-names so use uuids
        grp, obj, grpUuid, objUuid = groupInPlace(obj, objUuid=uuidList[i], grpSwapSuffix=grpSwapSuffix)
        grpList.append(grp)
        grpUuidList.append(grpUuid)
        objUuidList.append(objUuid)
    if grpUuidList:  # Update new long-names from uuids
        if grpUuidList[0]:
            grpList = cmds.ls(grpUuidList, long=True)
            objList = cmds.ls(objUuidList, long=True)
    return grpList, objList


# ---------------------------
# CREATE CONTROLS ON JOINTS (SHAPE PARENT)
# ---------------------------


def createControlsOnJoints(jntList, folderpath="", curveScale=(1.0, 1.0, 1.0), rotateOffset=(0, -90, 90), grpJnts=True,
                           designName='circle', freezeJnts=True, children=False, message=True, rgbColor=(0, 0, 1),
                           suffixControls=True, trackScale=True, lineWidth=-1):
    """Creates controls from a given list of joints.

    Can group each joint and can freeze transform them too

    Control styles can be selected and sized, uses control shape/designs from the shapelib module.

    :param jntList: The list of joints to be grouped
    :type jntList: list
    :param folderpath: Optional folder path of the .shape file. If empty "" then search within the Zoo internal library
    :type folderpath: str
    :param curveScale: The scale of each control in Maya units.  Is measured in radius, not width.
    :type curveScale: list(float)
    :param rotateOffset: rotate offset of the control, is a CV rotation offset not object
    :type rotateOffset: list(float)
    :param grpJnts: Group the joints, if frozen will cause each joint to be zeroed.
    :type grpJnts: bool
    :param designName: The shape/look/design of the control, control names can be found in skeleton builder's folder
    :type designName: str
    :param freezeJnts: Freeze the joints to be sure they're good?
    :type freezeJnts: bool
    :param children: Will create controls for all child joints
    :type children: bool
    :param message: Report the messages to the user?
    :type message: bool
    :param rgbColor: The color of the control in rgb color (color values should be in linear color)
    :type rgbColor: bool
    :param suffixControls: Suffix the controls with an underscore and filterTypes.CONTROLLER_SX, usually "ctrl"
    :type suffixControls: bool
    :param trackScale: Add tracking attributes for tracking the scale of the control, will not appear in channel box
    :type trackScale: bool
    :param lineWidth: The width of the curve's lines in pixels, -1 is default and will use global pref settings
    :type lineWidth: int
    :return controlList: The control list of names
    :rtype controlList: list
    :return grpList: The group list of names
    :rtype grpList: list
    """
    doFreezeGrp = not attributes.checkAllAttrsZeroedList(jntList)  # Only True if a jnt has not zeroed attrs
    grpList = list()
    if children:
        jntList = joints.filterChildJointList(jntList)
    if freezeJnts and doFreezeGrp:  # Skip if already all zeroed attrs
        cmds.makeIdentity(jntList, apply=True, scale=True, rotate=True, translate=True)
    if suffixControls:  # then rename first
        jntList = namehandling.addPrefixSuffixList(jntList, filtertypes.CONTROLLER_SX, addUnderscore=True)
    # create controls
    controlShapeList = createControlCurveList(jntList, folderpath=folderpath, curveScale=curveScale,
                                              rotateOffset=rotateOffset, designName=designName, trackScale=trackScale,
                                              lineWidth=lineWidth, rgbColor=rgbColor)
    if grpJnts and suffixControls and doFreezeGrp:  # grp the joints and replace the ctrl suffix with grp for the groups
        grpList, jntList = groupInPlaceList(jntList, grpSwapSuffix=True)
    elif grpJnts and doFreezeGrp:
        grpList, jntList = groupInPlaceList(jntList)
    for jnt in jntList:  # set selection child highlighting to 0
        cmds.setAttr('{}.selectionChildHighlighting'.format(jnt), 0)
    if message:
        om2.MGlobal.displayInfo('Success: Controls Built')
    return controlShapeList, grpList, jntList


def createControlsOnSelected(curveScale=(1.0, 1.0, 1.0), folderpath="", rotateOffset=(0, -90, 90), designName='circle',
                             grpJnts=True, children=False, rgbColor=(0, 0, 1), freezeJnts=True, postSelectControls=True,
                             suffixControls=True, trackScale=True, lineWidth=-1):
    """Creates curve controls from selected joint/s. Will shape node parent the nurbsCurve shapes to the joints.

    Control styles can be selected and sized, uses control shape/designs from the shapelib module.
    Can auto affect all children so all joints in the chain below the selected joint.

    :param curveScale: The scale of each control in Maya units.  Is measured in radius, not width.
    :type curveScale: list(float)
    :param designName: The shape/look/design of the control, control names can be found in skeleton builder's folder
    :type designName: str
    :param children: Will create controls for all child joints
    :type children: bool
    :param rgbColor: The color of the control in rgb color (color values should be in linear color)
    :type rgbColor: bool
    :param freezeJnts: Freeze the joints to be sure they're good?
    :type freezeJnts: bool
    :param postSelectControls: If True will select the controls at the end of the function
    :type postSelectControls: bool
    :param suffixControls: Suffix the controls with an underscore and filterTypes.CONTROLLER_SX, usually "ctrl"
    :type suffixControls: bool
    :param trackScale: Suffix the controls with an underscore and filterTypes.CONTROLLER_SX, usually "ctrl"
    :type trackScale: bool
    :param lineWidth: The width of the curve's lines in pixels, -1 is default and will use global pref settings
    :type lineWidth: int
    :return jntList: The list of joints that the controls have been added, if longNames and grps, now with new names.
    :rtype jntList: list(str)
    :return controlShapeList: A list of list(curve shape nodes), not the transforms as they are the joints
    :rtype controlShapeList: list(list(str))
    :return grpList: If grpJnts is a list of all the new groups
    :rtype grpList: list(str)
    """
    jntList = cmds.ls(selection=True, exactType="joint", long=True)
    if not jntList:  # Nothing selected build control at world center
        newControl, grpName = createControlsMatch(folderpath=folderpath, matchObj="", newName=NEW_CONTROL,
                                                  curveScale=curveScale, rotateOffset=rotateOffset,
                                                  designName=designName, grp=True, rgbColor=rgbColor,
                                                  lineWidth=lineWidth)
        return list(), [newControl], [grpName]
    if children:
        jntList = joints.filterChildJointList(jntList)
    controlShapeList, grpList, jntList = createControlsOnJoints(jntList, folderpath=folderpath, curveScale=curveScale,
                                                                rotateOffset=rotateOffset, grpJnts=grpJnts,
                                                                designName=designName, children=children,
                                                                rgbColor=rgbColor, freezeJnts=freezeJnts,
                                                                suffixControls=suffixControls, trackScale=trackScale,
                                                                lineWidth=lineWidth)
    if postSelectControls:
        cmds.select(jntList, replace=True)
    return jntList, controlShapeList, grpList


# ---------------------------
# CONSTRAIN BUILD CONTROLS
# ---------------------------


def constrainControlsObjList(objList, folderpath="", curveScale=(1.0, 1.0, 1.0), rotateOffset=(0, -90, 90),
                             designName='circle',
                             rgbColor=(0, 0, 1), constrainControls=False, createMasterGrp=True,
                             postSelectControls=True, suffixControls=True, trackScale=True, lineWidth=-1,
                             scaleConstraint=True, float=False, message=True):
    """Creates curve controls from an object list. Will be created in order. Only one chain can be created and no forks.

    Uses parent constrain to link the curves into a hierarchy, with many options.

    Control styles can be selected and sized, uses control shape/designs uses the shapelib module.

    :param objList: The object list to create the controls on
    :type objList: list(str)
    :param folderpath: Optional folder path of the .shape file. If empty "" then search within the Zoo internal library
    :type folderpath: str
    :param curveScale: The scale of each control in Maya units.  Is measured in radius, not width.
    :type curveScale: list(float)
    :param designName: The shape/look/design of the control, control names can be found in skeleton builder's folder
    :type designName: str
    :param rgbColor: The color of the control in rgb color (color values should be in linear color)
    :type rgbColor: bool
    :param constrainControls: Controls can either be constrained (True) to each other or parented (False)
    :type constrainControls: bool
    :param createMasterGrp: Will create a master root ground to tidy up the controls
    :type createMasterGrp: bool
    :param postSelectControls: If True will select the controls at the end of the function
    :type postSelectControls: bool
    :param suffixControls: Suffix the controls with an underscore and filterTypes.CONTROLLER_SX, usually "ctrl"
    :type suffixControls: bool
    :param trackScale: Suffix the controls with an underscore and filterTypes.CONTROLLER_SX, usually "ctrl"
    :type trackScale: bool
    :param lineWidth: The width of the curve's lines in pixels, -1 is default and will use global pref settings
    :type lineWidth: int
    :param float: Override where the controls will not be parented to one another, they will be floating
    :type float: bool
    :param message: report messages to the user?
    :type message: bool
    :return objList: The list of the objects now constrained
    :rtype objList: list(str)
    :return controlList: A list of newly created control transform nodes
    :rtype controlList: list(str)
    :return groupList: A list of all the new groups for each control
    :rtype groupList: list(str)
    :return objConstraintList: A list of the constraints created in order for the selected objects
    :rtype objConstraintList: list(str)
    :return cntrlConstraintList: An optional list of the constraints for the control groups. Empty if not used
    :rtype cntrlConstraintList: list(str)
    :return objScaleConstraintList: An optional list of scale constraints for the objects. Empty if not used
    :rtype objScaleConstraintList: list(str)
    :return cntrlScaleConstraintList: An optional list of scale constraints for the control groups. Empty if not used
    :rtype cntrlScaleConstraintList: list(str)
    :return masterGrpName: An optional name of the main group root that all controls are parented into
    :rtype masterGrpName: str
    """
    objConstraintList = list()
    cntrlConstraintList = list()
    objScaleConstraintList = list()
    cntrlScaleConstraintList = list()
    masterGrpName = ""
    # Create the master group root -------------------------------------------------------------------
    if createMasterGrp:
        firstObjName = namehandling.getShortName(objList[0])
        masterGrpName = "_".join([firstObjName, CONTROLS_GRP_SUFFIX])
    # Create controls and the groups -----------------------------------------------------------------
    controlList, groupList = createControlsMatchList(objList, folderpath=folderpath, curveScale=curveScale,
                                                     rotateOffset=rotateOffset,
                                                     designName=designName, grp=True, rgbColor=rgbColor,
                                                     lineWidth=lineWidth)
    # Parent the grp to the preceding control -------------------------------------------------------
    if not constrainControls and not float:
        controlUuids = cmds.ls(controlList, uuid=True)  # uuid to keep track of names
        groupUuids = cmds.ls(groupList, uuid=True)  # uuid to keep track of names
        for i, grp in enumerate(groupList):
            if i == 0:
                continue
            grp = cmds.ls(groupUuids[i], long=True)[0]
            control = cmds.ls(controlUuids[i - 1], long=True)[0]
            cmds.parent(grp, control)  # do the parent group to previous control
        if createMasterGrp:
            masterGrpName = cmds.group(cmds.ls(groupUuids[0], long=True)[0], name=masterGrpName)[0]
        controlList = cmds.ls(controlUuids, long=True)  # convert back to long names
        groupList = cmds.ls(groupUuids, long=True)
    # Parent constrain the groups to their preceding control ------------------------------------------
    else:
        if createMasterGrp:
            controlUuids = cmds.ls(controlList, uuid=True)  # uuid to keep track of names
            groupUuids = cmds.ls(groupList, uuid=True)
            masterGrpName = cmds.group(cmds.ls(groupUuids, long=True), name=masterGrpName)[0]
            controlList = cmds.ls(controlUuids, long=True)  # convert back to long names
            groupList = cmds.ls(groupUuids, long=True)
        if not float:  # then parent controls together
            for i, grp in enumerate(groupList):
                if i == 0:
                    continue
                # Do the group constraints to previous control
                cntrlConstraintList.append(cmds.parentConstraint(controlList[i - 1], groupList[i],
                                                                 maintainOffset=True)[0])
                if scaleConstraint:
                    cntrlScaleConstraintList.append(
                        cmds.scaleConstraint(controlList[i - 1], groupList[i], maintainOffset=True)[0])
    # Constrain objects to the controls ---------------------------------------------------------------
    for i, obj in enumerate(objList):
        objConstraintList.append(cmds.parentConstraint(controlList[i], obj, maintainOffset=True)[0])
        objScaleConstraintList.append(cmds.scaleConstraint(controlList[i], obj, maintainOffset=True)[0])
    # Set selection child highlighting to 0 -----------------------------------------------------------
    for control in controlList:
        cmds.setAttr('{}.selectionChildHighlighting'.format(control), 0)
    if postSelectControls:
        cmds.select(controlList, replace=True)
    return objList, controlList, groupList, objConstraintList, cntrlConstraintList, objScaleConstraintList, \
           cntrlScaleConstraintList, masterGrpName


def constrainControlsHierarchyList(rootObjList, objList, folderpath="", curveScale=(1.0, 1.0, 1.0),
                                   rotateOffset=(0, -90, 90),
                                   designName='circle', rgbColor=(0, 0, 1), constrainControls=False,
                                   createMasterGrp=True, children=False, postSelectControls=True, suffixControls=True,
                                   trackScale=True, lineWidth=-1, scaleConstraint=True, float=False, message=True):
    """Creates curve controls from a rootObjList list and objList. Will be created as per the object hierarchy.

    Uses parent constrain to link the curves into a hierarchy, with many options.

    Control styles can be selected and sized, uses control shape/designs uses the shapelib module.

    :param objList: The object list to create the controls on
    :type objList: list(str)
    :param curveScale: The scale of each control in Maya units.  Is measured in radius, not width.
    :type curveScale: list(float)
    :param folderpath: Optional folder path of the .shape file. If empty "" then search within the Zoo internal library
    :type folderpath: str
    :param designName: The shape/look/design of the control, control names can be found in skeleton builder's folder
    :type designName: str
    :param rgbColor: The color of the control in rgb color (color values should be in linear color)
    :type rgbColor: list(float)
    :param constrainControls: Controls can either be constrained (True) to each other or parented (False)
    :type constrainControls: bool
    :param createMasterGrp: Will create a master root ground to tidy up the controls
    :type createMasterGrp: bool
    :param children: Parent constrains as per the original hierarchy, all objects must be passed in
    :type children: bool
    :param postSelectControls: If True will select the controls at the end of the function
    :type postSelectControls: bool
    :param suffixControls: Suffix the controls with an underscore and filterTypes.CONTROLLER_SX, usually "ctrl"
    :type suffixControls: bool
    :param trackScale: Suffix the controls with an underscore and filterTypes.CONTROLLER_SX, usually "ctrl"
    :type trackScale: bool
    :param lineWidth: The width of the curve's lines in pixels, -1 is default and will use global pref settings
    :type lineWidth: int
    :param float: Override where the controls will not be parented to one another, they will be floating
    :type float: bool
    :param message: report messages to the user?
    :type message: bool
    :return objList: The list of the objects now constrained
    :rtype objList: list(str)
    :return controlList: A list of newly created control transform nodes
    :rtype controlList: list(str)
    :return groupList: A list of all the new groups for each control
    :rtype groupList: list(str)
    :return objConstraintList: A list of the constraints created in order for the selected objects
    :rtype objConstraintList: list(str)
    :return cntrlConstraintList: An optional list of the constraints for the control groups. Empty if not used
    :rtype cntrlConstraintList: list(str)
    :return objScaleConstraintList: An optional list of scale constraints for the objects. Empty if not used
    :rtype objScaleConstraintList: list(str)
    :return cntrlScaleConstraintList: An optional list of scale constraints for the control groups. Empty if not used
    :rtype cntrlScaleConstraintList: list(str)
    :return masterGrpName: An optional name of the main group root that all controls are parented into
    :rtype masterGrpName: str
    """
    objConstraintList = list()
    cntrlConstraintList = list()
    objScaleConstraintList = list()
    cntrlScaleConstraintList = list()
    rootControlGrpList = list()
    masterGrpName = ""
    # Create the master group root -------------------------------------------------------------------
    if createMasterGrp:
        firstObjName = namehandling.getShortName(rootObjList[0])
        masterGrpName = "_".join([firstObjName, CONTROLS_GRP_SUFFIX])
    # Create controls and the groups -----------------------------------------------------------------
    controlList, groupList = createControlsMatchList(objList, folderpath=folderpath, curveScale=curveScale,
                                                     rotateOffset=rotateOffset,
                                                     designName=designName, grp=True, rgbColor=rgbColor,
                                                     lineWidth=lineWidth)
    # Parent the groups to their control relative to objList -----------------------------------------
    if not constrainControls and not float:
        controlUuids = cmds.ls(controlList, uuid=True)  # uuid to keep track of names
        groupUuids = cmds.ls(groupList, uuid=True)  # uuid to keep track of names
        for i, obj in enumerate(objList):  # parents the grp to it's relative parent in objList
            if obj in rootObjList:  # then skip as it's control doesn't need to be parented
                rootControlGrpList.append(groupList[i])
                continue
            grp = cmds.ls(groupUuids[i], long=True)[0]
            parentObj = cmds.listRelatives(obj, parent=True, fullPath=True)[0]  # parent must exist as is not a root
            parentIndex = objList.index(parentObj)  # there must be a match in objList
            parentCntrlUuid = controlUuids[parentIndex]  # there must be an equivalent index in controlList
            parentCntrl = cmds.ls(parentCntrlUuid, long=True)[0]
            cmds.parent(grp, parentCntrl)  # parent the group to it's objList relative control
        if createMasterGrp:
            masterGrpName = cmds.group(rootControlGrpList, name=masterGrpName)[0]
        controlList = cmds.ls(controlUuids, long=True)  # convert back to long names
        groupList = cmds.ls(groupUuids, long=True)
    # Parent constrain the groups to their control relative to objList --------------------------------
    else:
        if createMasterGrp:
            controlUuids = cmds.ls(controlList, uuid=True)  # uuid to keep track of names
            groupUuids = cmds.ls(groupList, uuid=True)
            masterGrpName = cmds.group(groupList, name=masterGrpName)[0]
            controlList = cmds.ls(controlUuids, long=True)  # convert back to long names
            groupList = cmds.ls(groupUuids, long=True)
        if not float:  # parent constrain the controls to each other
            for i, obj in enumerate(objList):
                if obj in rootObjList:  # then skip as it's control doesn't need to be parented
                    continue
                # Do the group constraints relative to the object list's hierarchy
                group = groupList[i]
                parentObj = cmds.listRelatives(obj, parent=True, fullPath=True)[0]  # parent must exist as is not a root
                parentIndex = objList.index(parentObj)  # there must be a match in objList
                parentCntrl = controlList[parentIndex]  # there must be an equivalent index in controlList
                cntrlConstraintList.append(cmds.parentConstraint(parentCntrl, group, maintainOffset=True)[0])
                if scaleConstraint:
                    cntrlScaleConstraintList.append(
                        cmds.scaleConstraint(parentCntrl, group, maintainOffset=True)[0])
    # Constrain objects to the controls ---------------------------------------------------------------
    for i, obj in enumerate(objList):
        objConstraintList.append(cmds.parentConstraint(controlList[i], obj, maintainOffset=True)[0])
        objScaleConstraintList.append(cmds.scaleConstraint(controlList[i], obj, maintainOffset=True)[0])
    # Set selection child highlighting to 0 -----------------------------------------------------------
    for control in controlList:
        cmds.setAttr('{}.selectionChildHighlighting'.format(control), 0)
    if postSelectControls:
        cmds.select(controlList, replace=True)
    return objList, controlList, groupList, objConstraintList, cntrlConstraintList, objScaleConstraintList, \
           cntrlScaleConstraintList, masterGrpName


def constrainControlsOnSelected(folderpath="", curveScale=(1.0, 1.0, 1.0), rotateOffset=(0, -90, 90),
                                designName='circle',
                                children=False, rgbColor=(0, 0, 1), constrainControls=False, createMasterGrp=True,
                                postSelectControls=True, suffixControls=True, trackScale=True, lineWidth=-1,
                                scaleConstraint=True, float=False, message=True):
    """Creates curve controls from selected objects. Uses parent constrain to link the curves into a hierarchy.
    Currently only builds one straight chain, no forking.

    If children is False will build a parent constrain in the order of selection as per FK
    If children is True will build a parent constrain in order of the hierarchy as per FK

    Control styles can be selected and sized, uses control shape/designs from the shapelib module.

    TODO: Support hierarchy
    TODO: Support multiple chains in hierarchy mode

    :param folderpath: Optional folder path of the .shape file. If empty "" then search within the Zoo internal library
    :type curveScale: str
    :param curveScale: The scale of each control in Maya units.  Is measured in radius, not width.
    :type curveScale: list(float)
    :param designName: The shape/look/design of the control, control names can be found in skeleton builder's folder
    :type designName: str
    :param children: Will create controls for all child joints
    :type children: bool
    :param rgbColor: The color of the control in rgb color (color values should be in linear color)
    :type rgbColor: bool
    :param constrainControls: Controls can either be constrained (True) to each other or parented (False)
    :type constrainControls: bool
    :param postSelectControls: If True will select the controls at the end of the function
    :type postSelectControls: bool
    :param suffixControls: Suffix the controls with an underscore and filterTypes.CONTROLLER_SX, usually "ctrl"
    :type suffixControls: bool
    :param trackScale: Suffix the controls with an underscore and filterTypes.CONTROLLER_SX, usually "ctrl"
    :type trackScale: bool
    :param lineWidth: The width of the curve's lines in pixels, -1 is default and will use global pref settings
    :type lineWidth: int
    :param float: Override where the controls will not be parented to one another, they will be floating
    :type float: bool
    :param message: report messages to the user?
    :type message: bool
    :return objList: The list of the objects now constrained
    :rtype objList: list(str)
    :return controlList: A list of newly created control transform nodes
    :rtype controlList: list(str)
    :return groupList: A list of all the new groups for each control
    :rtype groupList: list(str)
    :return objConstraintList: A list of the constraints created in order for the selected objects
    :rtype objConstraintList: list(str)
    :return cntrlConstraintList: An optional list of the constraints for the control groups. Empty if not used
    :rtype cntrlConstraintList: list(str)
    :return objScaleConstraintList: An optional list of scale constraints for the objects. Empty if not used
    :rtype objScaleConstraintList: list(str)
    :return cntrlScaleConstraintList: An optional list of scale constraints for the control groups. Empty if not used
    :rtype cntrlScaleConstraintList: list(str)
    :return masterGrpName: An optional name of the main group root that all controls are parented into
    :rtype masterGrpName: str
    """
    objList = cmds.ls(selection=True, type="transform", long=True)
    rootObjList = list()
    # Basic selection check --------------------------------------------------------------------------
    if not objList:  # Nothing selected build control at world center
        newControl, grpName = createControlsMatch(folderpath=folderpath, matchObj="", newName=NEW_CONTROL,
                                                  curveScale=curveScale, rotateOffset=rotateOffset,
                                                  designName=designName, grp=True,
                                                  rgbColor=rgbColor, lineWidth=lineWidth)
        return [newControl], [grpName], list(), list(), list(), ""
    # Hierarchy figure the object list ---------------------------------------------------------------
    if children:  # parent by matching the hierarchy, can only be one chain
        rootObjList = objhandling.getRootObjectsFromList(objList)
        objList = cmds.listRelatives(rootObjList, allDescendents=True, type="transform", fullPath=True)
        objList = list(set(objList + rootObjList))  # doesn't matter the order as we are tracking the roots
    # Check translation/rot/scale channels are free, return warning if can't perform action ----------
    attrCheckList = attributes.MAYA_ROTATE_ATTRS + attributes.MAYA_TRANSLATE_ATTRS
    if scaleConstraint:
        attrCheckList += attributes.MAYA_SCALE_ATTRS
    lockedNodes, lockedAttrList = attributes.getLockedConnectedAttrsList(objList, attrList=attrCheckList)
    if lockedNodes:
        if message:
            om2.MGlobal.displayWarning("Selected nodes cannot be constrained as they have connections "
                                       "or are locked: {}".format(lockedNodes))
        return list(), list(), list(), list(), list(), ""
    # Do the create controls and constraints ----------------------------------------------------------
    if children:
        return constrainControlsHierarchyList(rootObjList, objList, folderpath=folderpath, curveScale=curveScale,
                                              rotateOffset=rotateOffset, designName=designName, rgbColor=rgbColor,
                                              constrainControls=constrainControls, createMasterGrp=createMasterGrp,
                                              children=children, postSelectControls=postSelectControls,
                                              suffixControls=suffixControls, trackScale=trackScale, lineWidth=lineWidth,
                                              scaleConstraint=scaleConstraint, float=float, message=message)
    return constrainControlsObjList(objList, folderpath=folderpath, curveScale=curveScale, rotateOffset=rotateOffset,
                                    designName=designName, rgbColor=rgbColor, constrainControls=constrainControls,
                                    createMasterGrp=createMasterGrp, postSelectControls=postSelectControls,
                                    suffixControls=suffixControls, trackScale=trackScale, lineWidth=-1,
                                    scaleConstraint=scaleConstraint, float=float, message=True)


# ---------------------------
# BUILD MATCH GRP CONTROLS
# ---------------------------


def createControlsMatch(folderpath="", matchObj="", newName=NEW_CONTROL, curveScale=(1.0, 1.0, 1.0),
                        rotateOffset=(0, 0, 0), designName='circle', grp=True, rgbColor=(0, 0, 1), lineWidth=-1):
    """Creates a control matching the rot and pos of an object does not parent.

    If the matchObj is an empty str will create the control at the world center and the new name will be "newControl"

    :param folderpath: Optional folder path of the .shape file. If empty "" then search within the Zoo internal library
    :type folderpath: str
    :param matchObj: The object to match the control/group to.  If empty string will remain at the center of the world
    :type matchObj: str
    :param newName: The new name of the control and group if grp=True
    :type newName: str
    :param curveScale: The scale of each control in Maya units.  Is measured in radius, not width.
    :type curveScale: list(float)
    :param rotateOffset: rotate offset of the control, is a CV rotation offset not object
    :type rotateOffset: list(float)
    :param designName: The shape/look/design of the control, control names can be found in skeleton builder's folder
    :type designName: str
    :param grp: Will group the curve transforms cause the curve transforms to be zeroed
    :type grp: str
    :param rgbColor: The color of the control in rgb color (color values should be in linear color)
    :type rgbColor: bool
    :param lineWidth: The width of the curve's lines in pixels, -1 is default and will use global pref settings
    :type lineWidth: int
    :return newControl: the curve transform name
    :rtype newControl: str
    :return grpList: the grp if it exists
    :rtype grpList: str
    """
    grpName = ""
    newControl = \
        createControlCurve(folderpath=folderpath, ctrlName=newName, curveScale=curveScale, rotateOffset=rotateOffset,
                           designName=designName, shapeParent="", lineWidth=lineWidth, rgbColor=rgbColor)[0]
    if grp:  # Then group and match the group
        grpName = "_".join([newName, filtertypes.GROUP_SX])
        grpName = cmds.group(name=grpName, em=True)
        newControl = cmds.parent(newControl, grpName)[0]
        if matchObj:
            cmds.matchTransform([grpName, matchObj], pos=1, rot=1, scl=0, piv=0)
        grpName = namehandling.getLongNameFromShort(grpName)  # make long name
    elif matchObj:  # Don't create a group just match the control
        cmds.matchTransform([newControl, matchObj], pos=1, rot=1, scl=0, piv=0)
    newControl = namehandling.getLongNameFromShort(newControl)  # make long name
    return newControl, grpName


def createControlsMatchList(objList, overrideName="", folderpath="", curveScale=(1.0, 1.0, 1.0), rotateOffset=(0, 0, 0),
                            designName='circle', grp=True, rgbColor=(0, 0, 1), lineWidth=-1):
    """Creates control/s from an object list, will match pos and orient but does not parent.

    :param objList: The scale of each control
    :type objList: float
    :param folderpath: Optional folder path of the .shape file. If empty "" then search within the Zoo internal library
    :type folderpath: str
    :param curveScale: The scale of each control in Maya units.  Is measured in radius, not width.
    :type curveScale: list(float)
    :param rotateOffset: rotate offset of the control, is a CV rotation offset not object
    :type rotateOffset: list(float)
    :param rotateOffset: rotate offset of the control, is a CV rotation offset not object
    :type rotateOffset: list(float)
    :param designName: The shape/look/design of the control, control names can be found in skeleton builder's folder
    :type designName: str
    :param grp: Will group the curve transforms cause the curve transforms to be zeroed
    :type grp: bool
    :param rgbColor: The color of the control in rgb color (color values should be in linear color)
    :type rgbColor: tuple
    :param lineWidth: The width of the curve's lines in pixels, -1 is default and will use global pref settings
    :type lineWidth: int
    :return controlList: A list of all the curve transforms
    :rtype controlList: list(str)
    :return grpList: a list of all the grps if they exist
    :rtype grpList: list(str)
    """
    groupList = list()
    controlList = list()
    for i, obj in enumerate(objList):
        if overrideName:
            newPadding = str(i).zfill(2)  # force 2 padding
            pureName = "{}_{}".format(overrideName, newPadding)
        else:
            pureName = namehandling.mayaNamePartTypes(obj)[2]
        newControl, grpName = createControlsMatch(folderpath=folderpath, matchObj=obj, newName=pureName,
                                                  curveScale=curveScale, rotateOffset=rotateOffset,
                                                  designName=designName, grp=grp,
                                                  rgbColor=rgbColor, lineWidth=lineWidth)
        groupList.append(grpName)
        controlList.append(newControl)
    return controlList, groupList


def createControlsMatchSelected(folderpath="", curveScale=(1.0, 1.0, 1.0), rotateOffset=(0, 0, 0), designName='circle',
                                grp=True, children=False, rgbColor=(0, 0, 1), lineWidth=-1):
    """Creates control/s, if nothing is selected will build the control at world zero.  Does not parent.

    If an object is selected will build at that objects pivot position.
    Multiple objects are supported as are children which will build a control on every object in the hierarchy.

    :param folderpath: Optional folder path of the .shape file. If empty "" then search within the Zoo internal library
    :type folderpath: str
    :param curveScale: The scale of each control in Maya units.  Is measured in radius, not width.
    :type curveScale: list(float)
    :param rotateOffset: rotate offset of the control, is a CV rotation offset not object
    :type rotateOffset: list(float)
    :param designName: The shape/look/design of the control, control names can be found in skeleton builder's folder
    :type designName: str
    :param grp: Will group the curve transforms cause the curve transforms to be zeroed
    :type grp: bool
    :param children: Will create controls for all child joints
    :type children: bool
    :param rgbColor: The color of the control in rgb color (color values should be in linear color)
    :type rgbColor: tuple
    :param lineWidth: The width of the curve's lines in pixels, -1 is default and will use global pref settings
    :type lineWidth: int
    :return controlList: A list of all the curve transforms
    :rtype controlList: list(str)
    :return grpList: a list of all the grps if they exist
    :rtype grpList: list(str)
    """
    selObjs = cmds.ls(selection=True, long=True, type="transform", dagObjects=children)
    if not selObjs:  # Build control at world center
        newControl, grpName = createControlsMatch(folderpath=folderpath, matchObj="", newName=NEW_CONTROL,
                                                  curveScale=curveScale, rotateOffset=rotateOffset,
                                                  designName=designName, grp=grp,
                                                  rgbColor=rgbColor, lineWidth=lineWidth)
        controlList = [newControl]
        groupList = [grpName]
    else:  # Build and match for the selection list
        controlList, groupList = createControlsMatchList(selObjs, folderpath=folderpath, curveScale=curveScale,
                                                         rotateOffset=rotateOffset, designName=designName,
                                                         grp=grp, rgbColor=rgbColor, lineWidth=lineWidth)
    cmds.select(deselect=True)
    return controlList, groupList


# ---------------------------
# TRACK CONTROLS
# ---------------------------


def addTrackAttrs(transformName, scale=(1.0, 1.0, 1.0), color=None, rotate=(0.0, 0.0, 0.0),
                  translate=(0.0, 0.0, 0.0), designName="circle"):
    """Adds a tracker attributes and sets the scale/color value that can tracked/changed
    ZOO_SCALE_DEFAULT_ATTR "zooScaleDefault" sets the default scale that generally will not change unless frozen (reset)

    :param transformName: The name of the transform/joint node, this transform is a control ie has curve shapes
    :type transformName: str
    :param scale: The initial scale size [scaleX, scaleY, scaleZ]
    :type scale: list(float)
    :param color: The initial color as a linear float [colorR, colorG, colorB]
    :type color: list(float)
    :param rotate: The initial rotation values [rotateX, rotateY, rotateZ]
    :type rotate: list(float)
    :param translate: The initial translation values [translateX, translateY, translateZ]
    :type translate: list(float)
    :param designName: A str Maya attribute value which records the text name eg "circle"
    :type designName: str
    """
    if not cmds.attributeQuery(ZOO_SCALE_TRACK_ATTR, node=transformName, exists=True):
        # trans rot and scale
        for i, attr in enumerate(ZOO_CONTROLTRACK_VECTOR_LIST):  # add a vector attribute for each trakcer attr
            cmds.addAttr(transformName, longName=attr, attributeType="double3")
            for letter in XYZ_LIST:  # add the "attrName_x" "attrName_y" and "attrName_z"
                cmds.addAttr(transformName, longName="{}_{}".format(attr, letter),
                             attributeType="double", parent=attr)
        # color
        for i, attr in enumerate(ZOO_CONTROLTRACK_RGB_LIST):  # add a vector attribute for each tracker attr
            cmds.addAttr(transformName, longName=attr, attributeType="double3")
            for letter in RGB_LIST:  # add the "attrName_x" "attrName_y" and "attrName_z"
                cmds.addAttr(transformName, longName="{}_{}".format(attr, letter),
                             attributeType="double", parent=attr)
        # designName "circle"
        cmds.addAttr(transformName, longName=ZOO_SHAPE_TRACK_ATTR, dataType="string")
        cmds.addAttr(transformName, longName=ZOO_SHAPE_DEFAULT_ATTR, dataType="string")
    # set the attributes
    cmds.setAttr(".".join([transformName, ZOO_SCALE_TRACK_ATTR]), scale[0], scale[1], scale[2])
    cmds.setAttr(".".join([transformName, ZOO_SCALE_DEFAULT_ATTR]), scale[0], scale[1], scale[2])
    cmds.setAttr(".".join([transformName, ZOO_ROTATE_TRACK_ATTR]), rotate[0], rotate[1], rotate[2])
    cmds.setAttr(".".join([transformName, ZOO_ROTATE_DEFAULT_ATTR]), rotate[0], rotate[1], rotate[2])
    cmds.setAttr(".".join([transformName, ZOO_TRANSLATE_TRACK_ATTR]), translate[0], translate[1], translate[2])
    cmds.setAttr(".".join([transformName, ZOO_TRANSLATE_DEFAULT_ATTR]), translate[0], translate[1], translate[2])
    if color:  # might be None
        cmds.setAttr(".".join([transformName, ZOO_COLOR_TRACK_ATTR]), color[0], color[1], color[2])
        cmds.setAttr(".".join([transformName, ZOO_COLOR_DEFAULT_ATTR]), color[0], color[1], color[2])
    else:  # No color given, try to get it from the shape node
        shapes = cmds.listRelatives(transformName, shapes=True, type="nurbsCurve", fullPath=True)
        if shapes:
            color = objcolor.getRgbColor(shapes[0], hsv=False, linear=True)
            cmds.setAttr(".".join([transformName, ZOO_COLOR_TRACK_ATTR]), color[0], color[1], color[2])
            cmds.setAttr(".".join([transformName, ZOO_COLOR_DEFAULT_ATTR]), color[0], color[1], color[2])
    cmds.setAttr(".".join([transformName, ZOO_SHAPE_TRACK_ATTR]), designName, type="string")
    cmds.setAttr(".".join([transformName, ZOO_SHAPE_DEFAULT_ATTR]), designName, type="string")


def freezeScaleTracker(controlCurve):
    """Freezes the scale tracker attributes setting them to a scale of 1.0 no matter the current scale

    :param controlCurve: A control curve with the tracker attributes
    :type controlCurve: str
    :return success: True if successful
    :rtype success: bool
    """
    if not cmds.attributeQuery(ZOO_SCALE_TRACK_ATTR, node=controlCurve, exists=True):  # tracker attr exists
        return False
    scaleXYZ = cmds.getAttr(".".join([controlCurve, ZOO_SCALE_TRACK_ATTR]))[0]
    cmds.setAttr(".".join([controlCurve, ZOO_SCALE_DEFAULT_ATTR]), scaleXYZ[0], scaleXYZ[1], scaleXYZ[2])
    return True


def freezeScaleTrackerList(controlCurveList, message=True):
    """Freezes the scale tracker attributes on a curve list setting them to a scale of 1.0 no matter the current scale

    :param controlCurveList: A list of control curves with the tracker attributes
    :type controlCurveList: list(str)
    """
    ctrlFrozenList = list()
    for ctrl in controlCurveList:
        result = freezeScaleTracker(ctrl)
        if result:
            ctrlFrozenList.append(ctrl)
    if not ctrlFrozenList:
        if message:
            om2.MGlobal.displayWarning("No controls found to be frozen")
        return
    if message:
        ctrlFrozenShortList = namehandling.getShortNameList(ctrlFrozenList)
        om2.MGlobal.displayInfo("Controls Frozen: {}".format(ctrlFrozenShortList))


def deleteTrackAttrs(controlTransform):
    """Removes the tracking custom attributes on a single control

    Attributes are found in:

        ZOO_CONTROLTRACK_VECTOR_LIST
        ZOO_CONTROLTRACK_RGB_LIST
        ZOO_CONTROLTRACK_STRING_LIST

    :param controlTransform: The transform node that may contain the tracking attributes
    :type controlTransform: str
    """
    attrList = ZOO_CONTROLTRACK_VECTOR_LIST + ZOO_CONTROLTRACK_RGB_LIST + ZOO_CONTROLTRACK_STRING_LIST
    for attr in attrList:
        attributes.checkRemoveAttr(controlTransform, attr)


def deleteTrackAttrsList(controlTransformList):
    """Removes the tracking custom attributes on a control list

    Attributes are found in:

        ZOO_CONTROLTRACK_VECTOR_LIST
        ZOO_CONTROLTRACK_RGB_LIST
        ZOO_CONTROLTRACK_STRING_LIST

    :param controlTransformList: List of control transforms that may contain the tracking attributes
    :type controlTransformList: list(str)
    """
    for control in controlTransformList:
        deleteTrackAttrs(control)


# ---------------------------
# COLOR CONTROLS
# ---------------------------


def colorUpdateTracker(cntrl, color):
    """Sets the color tracker attributes for a ctrl, if the tracker doesn't exist then it doesn't set anything

    :param cntrl: The Maya control name, joint or transform node.
    :type cntrl: str
    :param color: The color as a linear float [colorR, colorG, colorB], set these values
    :type color: list(float)
    """
    if cmds.attributeQuery(ZOO_COLOR_TRACK_ATTR, node=cntrl, exists=True):  # then update
        cmds.setAttr(".".join([cntrl, ZOO_COLOR_TRACK_ATTR]), color[0], color[1], color[2])


def colorUpdateTrackerList(cntrlList, color):
    """Sets the color tracker attributes for a control list, if the tracker doesn't exist then it doesn't set anything

    :param cntrlList: The list of Maya control names, joints or transform nodes.
    :type cntrlList: list(str)
    :param color: The color as a linear float [colorR, colorG, colorB], set these values
    :type color: list(float)
    """
    for ctrl in cntrlList:
        colorUpdateTracker(ctrl, color)


def colorControl(cntrl, color, linear=True):
    """Changes the color of a control. Takes linear float color by default. [0.1, 1.0, 0.33]

    :param cntrl: The Maya control name, joint or transform node.
    :type cntrl: str
    :param color: The color as float [colorR, colorG, colorB], set these values
    :type color: list(float)
    :param linear: If linear the color passed in should also be linear (default).  If False the color will be SRGB
    :type linear: bool
    """
    shapes = cmds.listRelatives(cntrl, shapes=True, type="nurbsCurve", fullPath=True)
    if not shapes:
        return False
    for shape in shapes:
        objcolor.setColorShapeRgb(shape, color, linear=linear)
    colorUpdateTracker(cntrl, color)
    return True


def colorControlsList(cntrlList, color, linear=True):
    """Changes the color of a list of controls. Takes linear float color by default. [0.1, 1.0, 0.33]

    :param cntrlList: The list of Maya control names, joints or transform nodes.
    :type cntrlList: list(str)
    :param color: The color as float [colorR, colorG, colorB], set these values
    :type color: list(float)
    :param linear: If linear the color passed in should also be linear (default).  If False the color will be SRGB
    :type linear: bool
    """
    coloredList = list()
    for ctrl in cntrlList:
        colored = colorControl(ctrl, color, linear=linear)
        if colored:
            coloredList.append(ctrl)
    return coloredList


def offsetHSVControl(cntrl, offset, hsvType="hue", linear=True):
    """Colors a control curve transform node name with HSV offsets.

    If hue the offset amount (0-360) Can go past 360 or less than 0
    Else if saturation or value (brightness) the range is 0-1

    :param cntrl: The Maya transform name of the selected control
    :type cntrl: str
    :param offset: the offset value to offset the color, 0-1 or if hue is 0-360
    :type offset: float
    :param hsvType: the type to offset, "hue", "saturation" or "value"
    :type hsvType: str
    :param linear: If linear the color passed in should also be linear (default).  If False the color will be SRGB
    :type linear: bool
    """
    shapes = cmds.listRelatives(cntrl, shapes=True, type="nurbsCurve", fullPath=True)
    if not shapes:
        return
    hsv = objcolor.getHsvColor(shapes[0], linear=True)
    if hsvType == "hue":
        hsv = colour.offsetHueColor(hsv, offset)
    if hsvType == "saturation":
        hsv = colour.offsetSaturation(hsv, offset)
    if hsvType == "value":
        hsv = colour.offsetValue(hsv, offset)
    objcolor.setColorListHsv(shapes, hsv, colorShapes=False, linear=linear, displayMessage=False)
    # Then update the color tracker attr
    if cmds.attributeQuery(ZOO_COLOR_TRACK_ATTR, node=cntrl, exists=True):
        color = colour.convertHsvToRgb(hsv)
        cmds.setAttr(".".join([cntrl, ZOO_COLOR_TRACK_ATTR]), color[0], color[1], color[2])


def offsetHSVControlList(cntrlList, offset, hsvType="hue", linear=True):
    """Colors a control curve list of transform node names with HSV offsets.

    If hue the offset amount (0-360) Can go past 360 or less than 0
    Else if saturation or value (brightness) the range is 0-1

    :param cntrlList: The list of Maya control names, joints or transform nodes.
    :type cntrlList: list(str)
    :param offset: the offset value to offset the color, 0-1 or if hue is 0-360
    :type offset: float
    :param hsvType: the type to offset, "hue", "saturation" or "value"
    :type hsvType: str
    :param linear: If linear the color passed in should also be linear (default).  If False the color will be SRGB
    :type linear: bool
    """
    for cntrl in cntrlList:
        offsetHSVControl(cntrl, offset, hsvType=hsvType, linear=linear)


def getColorControlTransform(controlName):
    """Returns the color of the current control, looks for the color of the first shape node

    :param controlName: The name of the control
    :type controlName: str
    :return rgbColor: color in float linear values (1.0, 0.5, 0.1)
    :rtype rgbColor: list(float)
    """
    shapes = filtertypes.filterTypeReturnShapes([controlName], shapeType="nurbsCurve")
    if not shapes:
        return (0.0, 0.0, 1.0)  # just return blue
    return objcolor.getRgbColor(shapes[0], hsv=False, linear=True)


# ---------------------------
# CV SCALE CONTROLS (ALSO SEE MODIFY BREAK/RECONNECT CONTROLS)
# ---------------------------


def scaleValuesFromCurrent(currentScaleXYZ, newScaleXYZ):
    """1 / (current scale / new scale) returns the value that the current scale must be multiplied by

    Note: These functions are CV scales, for break-off functions see see scaleBreakConnectCtrl()

    :param currentScaleXYZ: The current scale xyz [2.0, 2.0, 2.0]
    :type currentScaleXYZ: list(float)
    :param newScaleXYZ: The desired new scale xyz [8.0, 8.0, 8.0]
    :type newScaleXYZ: list(float)
    :return multiplyScale: The scale to multiply by the current to match the new scale xyz [4.0, 4.0, 4.0]
    :rtype multiplyScale: list(float)
    """
    multiplyScale = [1.0 / (currentScaleXYZ[0] / newScaleXYZ[0]),
                     1.0 / (currentScaleXYZ[1] / newScaleXYZ[1]),
                     1.0 / (currentScaleXYZ[2] / newScaleXYZ[2])]  #
    return multiplyScale


def resetScale(controlCurve):
    """Will reset the control scale back to it's initial value/s, only if the scale tracking attributes have been added

    Note: These functions are CV scales, for break-off functions see see scaleResetBrkCnctCtrl()

    :param controlCurve: the name of the control curve to affect
    :type controlCurve: str
    """
    if not cmds.attributeQuery(ZOO_SCALE_TRACK_ATTR, node=controlCurve, exists=True):  # tracker attr exists
        return
    currentScale = cmds.getAttr(".".join([controlCurve, ZOO_SCALE_TRACK_ATTR]))[0]
    dfltScale = cmds.getAttr(".".join([controlCurve, ZOO_SCALE_DEFAULT_ATTR]))[0]
    cmds.setAttr(".".join([controlCurve, ZOO_SCALE_TRACK_ATTR]), dfltScale[0], dfltScale[1], dfltScale[2])
    multiplyScale = scaleValuesFromCurrent(currentScale, dfltScale)
    shapenodes.scaleObjListCVs([controlCurve], multiplyScale)


def resetScaleList(controlList):
    """For a objList resets ctrl scale back to initial value/s, if the scale tracking attributes have been added

    Note: These functions are CV scales, for break-off functions see scaleResetBrkCnctCtrlList()

    :param controlList: list of control curve objects
    :type controlList: list(str)
    """
    for ctrl in controlList:
        resetScale(ctrl)


def resetScaleSelection():
    """From selection resets the ctrl scale back to initial value/s, if the scale tracking attributes have been added

    Note: These functions are CV scales, for break-off functions see scaleResetBrkCnctCtrlList()
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        return
    resetScaleList(selObjs)


def setTrackerScaleAbs(controlCurve, scaleXYZ):
    """While absolute scaling controls through the GUI, this function updates the scale track attr ZOO_SCALE_TRACK_ATTR

    This is an absolute scale and not an offset

    Note: These functions are CV scales, for break-off functions see see scaleBreakConnectCtrl()

    :param controlCurve: the name of the control curve to affect (transform)
    :type controlCurve: str
    :param scaleXYZ: The new scale value of the control xyz
    :type scaleXYZ: list(float)
    """
    if cmds.attributeQuery(ZOO_SCALE_TRACK_ATTR, node=controlCurve, exists=True):  # tracker attr exists
        cmds.setAttr(".".join([controlCurve, ZOO_SCALE_TRACK_ATTR]), scaleXYZ[0], scaleXYZ[1], scaleXYZ[2])
    else:  # doesn't exist so measure the size of the control and create the tracker attributes
        longestEdge = scaleutils.getLongestEdgeObj(controlCurve)
        # double the scale as control scale is the radius not width
        addTrackAttrs(controlCurve, [longestEdge * 2, longestEdge * 2, longestEdge * 2])


def setTrackerScaleOffset(controlCurve, scaleXYZ):
    """While offset scaling controls through the UI, this function updates the scale track attr ZOO_SCALE_TRACK_ATTR

    This is a relative scale, not absolute

    Note: These functions are CV scales, for break-off functions see see scaleBreakConnectCtrl()

    :param controlCurve: the name of the control curve to affect (transform)
    :type controlCurve: str
    :param scaleXYZ: The amount the control curve has been CV scaled
    :type scaleXYZ: list(float)
    """
    trackerScale = getCreateControlScale(controlCurve)  #
    trackerScale = [scaleXYZ[0] * trackerScale[0],
                    scaleXYZ[1] * trackerScale[1],
                    scaleXYZ[2] * trackerScale[2]]
    cmds.setAttr(".".join([controlCurve, ZOO_SCALE_TRACK_ATTR]), trackerScale[0], trackerScale[1], trackerScale[2])


def scaleAndTrackControlList(controlList, scaleXYZ):
    """While offset scaling controls through the UI, this function updates the scale track attr ZOO_SCALE_TRACK_ATTR

    This function works on an object list

    Note: These functions are CV scales, for break-off functions see see scaleBreakConnectCtrl() etc

    :param controlList: list of control curve objects
    :type controlList: list(str)
    :param scaleXYZ: The amount the control curve has been CV scaled, this is an offset value, relative not absolute
    :type scaleXYZ: list(float)
    """
    for obj in controlList:
        getCreateControlScale(obj)  # be sure has the tracker attributes
    shapenodes.scaleObjListCVs(controlList, scaleXYZ)  # do the CV scale
    for obj in controlList:  # set the tracker attributes
        setTrackerScaleOffset(obj, scaleXYZ)


def scaleAndTrackControlSelected(scaleXYZ):
    """While CV scaling control curves through the UI, this function updates the scale track attr ZOO_SCALE_TRACK_ATTR

    This function works on selected objects

    Note: These functions are CV scales, for break-off functions see see scaleBreakConnectCtrl() etc

    :param scaleXYZ: The amount the control curve has been CV scaled
    :type scaleXYZ: list(float)
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        return
    scaleAndTrackControlList(selObjs, scaleXYZ)


def scaleControlAbsoluteList(newScaleXYZ, controlList, message=False):
    """Scales the controls to be exactly a certain value.  A little tricky due to the vert scale being tracked

    Note: These functions are CV scales, for break-off functions see see scaleBreakConnectCtrl() etc

    :param newScaleXYZ: The new scale XYZ of the control  (2.0, 2.0, 2.0)
    :type newScaleXYZ: list(float)
    :param controlList: list of control names
    :type controlList: list(str)
    """
    scaleList = getControlScaleList(controlList)
    if not scaleList:
        if message:
            om2.MGlobal.displayWarning("No controls found")
        return
    for i, scale in enumerate(scaleList):
        scaleList[i] = scaleValuesFromCurrent(list(scale), list(newScaleXYZ))  # get the new scale multiplier
    for i, control in enumerate(controlList):
        shapenodes.scaleObjListCVs([control], scaleList[i])
    for i, obj in enumerate(controlList):
        setTrackerScaleAbs(obj, newScaleXYZ)


# ---------------------------
# SCALE TRACK AND HELPER FUNCTIONS (ALSO SEE MODIFY BREAK/RECONNECT CONTROLS)
# ---------------------------


def getCreateControlScale(controlCurve):
    """Returns the ZOO_SCALE_TRACK_ATTR attribute scale if it exists otherwise returns the size of the control \
    measured from the longest edge / 2.  Will also create all tracker attrs with defaults if they do not exist.

    Control scale is measured in radius not width.

    Note: Used while creating controls and setting up the tracker info see getAllTrackerInfo() and addTrackAttrs()

    :param controlCurve: the name of the control curve to retrieve the scale tracker values
    :type controlCurve: str
    """
    if cmds.attributeQuery(ZOO_SCALE_TRACK_ATTR, node=controlCurve, exists=True):  # tracker attr exists
        trackerScale = cmds.getAttr(".".join([controlCurve, ZOO_SCALE_TRACK_ATTR]))[0]
        return trackerScale
    else:  # doesn't exist so measure the size of the control and create the tracker attributes
        # get the longest edge
        longestEdge = scaleutils.getLongestEdgeObj(controlCurve, worldSpace=True, ignoreChildren=True)
        # halve the scale as control scale is the radius not width
        trackerScale = [longestEdge / 2, longestEdge / 2, longestEdge / 2]
        addTrackAttrs(controlCurve, trackerScale)
    return trackerScale


def getControlScaleList(controlCurveList):
    """Returns the ZOO_SCALE_TRACK_ATTR attribute scale if it exists for objList otherwise returns the size of the \
    control measured from the longest edge / 2.  Will also create all tracker attrs with defaults if they do not exist.

    Control scale is measured in radius not width.

    :param controlCurveList: list of control names
    :type controlCurveList: list(str)
    """
    scaleList = list()
    for control in controlCurveList:
        scaleList.append(getCreateControlScale(control))
    return scaleList


def getAllTrackerInfo(controlCurve):
    """Returns the zoo tracker attributes, if they don't exist it will create them with default values.

    Scale: Will be automatically created if it doesn't exist by measuring the bounding box as radius, longest edge / 2
    Shape: Will be "circle" if it doesn't already exist
    Rotate, Translate: Will be [0.0, 0.0, 0.0] if they don't exist
    Color: Will be automatically found from the first shape node's color

    :param controlCurve: the name of the control curve to retrieve the attr tracker values
    :type controlCurve: str
    """
    scale = getCreateControlScale(controlCurve)
    rotate = cmds.getAttr(".".join([controlCurve, ZOO_ROTATE_TRACK_ATTR]))[0]
    translate = cmds.getAttr(".".join([controlCurve, ZOO_TRANSLATE_TRACK_ATTR]))[0]
    shape = cmds.getAttr(".".join([controlCurve, ZOO_SHAPE_TRACK_ATTR]))
    # get color properly
    shapes = cmds.listRelatives(controlCurve, shapes=True, fullPath=True, type="nurbsCurve")
    if shapes:
        color = objcolor.getRgbColor(shapes[0], hsv=False, linear=True)
    else:
        color = cmds.getAttr(".".join([controlCurve, ZOO_COLOR_TRACK_ATTR]))[0]
    return translate, rotate, scale, color, shape


def getControlDefaultScale(controlCurve):
    """Returns the ZOO_SCALE_DEFAULT_ATTR attribute scale if it exists otherwise returns [1.0, 1.0, 1.0]

    :param controlCurve: The name of the control curve to retrieve the scale tracker values
    :type controlCurve: str
    """
    if cmds.attributeQuery(ZOO_SCALE_DEFAULT_ATTR, node=controlCurve, exists=True):  # tracker attr exists
        trackerScale = cmds.getAttr(".".join([controlCurve, ZOO_SCALE_DEFAULT_ATTR]))[0]
        return trackerScale
    return [1.0, 1.0, 1.0]


# ---------------------------
# ROTATE CONTROLS
# ---------------------------


def convertRotateUpList(rotateUpInt):
    """Converts the list CONTROL_UP_LIST into euler rotation offset

    :param rotateUpInt: Int position of the list CONTROL_UP_LIST "+y" is 0 "+x" is 2 etc
    :type rotateUpInt: int
    :return rotationOffset: The rotation offset assuming +y is (0, 0, 0)
    :rtype rotationOffset: list(float)
    """
    if rotateUpInt == Y_UP:  # 0
        return [0, 0, 0]
    elif rotateUpInt == Y_DOWN:  # 1
        return [0, 180, 0]
    elif rotateUpInt == X_UP:  # 2
        return [0, -90, 90]
    elif rotateUpInt == X_DOWN:  # 3
        return [0, 90, 90]
    elif rotateUpInt == Z_UP:  # 4
        return [90, 0, 0]
    elif rotateUpInt == Z_DOWN:  # 5
        return [-90, 0, 0]


# ---------------------------
# REPLACE CONTROLS WITH SHAPE/DESIGN
# ---------------------------


def replaceWithShapeDesign(controlName, folderpath="", designName="circle", autoScale=True,
                           rotateOffset=(0, 0, 0), message=True,
                           maintainLineWidth=True):
    """Replaces the controlName with a new shape design as per designName.  Will delete the existing curve shape nodes.

    :param controlName: The control shape design transform to replace it's curve
    :type controlName: str
    :param folderpath: Optional folder path of the .shape file. If empty "" then search within the Zoo internal library
    :type folderpath: str
    :param designName: The shape/look/design of the control, control names can be found in skeleton builder's folder
    :type designName: str
    :param autoScale: Try to automatically scale the size of the designName replacing the current control?
    :type autoScale: bool
    :param rotateOffset: rotate offset of the control, is a CV rotation offset not object
    :type rotateOffset: list(float)
    :param message: Report the messages to the user?
    :type message: bool
    :param maintainLineWidth: If True will keep the line thickness of the previous control (default)
    :type maintainLineWidth: bool
    """
    lineWidth = -1
    # get scale of current control
    scale = (1.0, 1.0, 1.0)
    if autoScale:
        scale = getCreateControlScale(controlName)
    if maintainLineWidth:
        lineWidth = curveLinethickness(controlName)
    # get current color
    rgbColor = getColorControlTransform(controlName)
    # create new control and match position
    newControl = createControlCurve(folderpath=folderpath, ctrlName=NEW_CONTROL, curveScale=scale,
                                    designName=designName, addSuffix=True, lineWidth=lineWidth,
                                    shapeParent="", rotateOffset=rotateOffset, trackScale=True)[0]
    cmds.matchTransform([newControl, controlName], pos=1, rot=1, scl=0, piv=0)
    # shape node replace
    shapenodes.shapeNodeParentList([newControl, controlName], deleteOriginal=True, reportSuccess=False,
                                   delShapeType="nurbsCurve")
    # set color
    objcolor.setColorListRgb([controlName], rgbColor, displayMessage=False, linear=True)
    if maintainLineWidth:
        setCurveLineThickness([controlName], lineWidth=lineWidth)
    cmds.setAttr(".".join([controlName, ZOO_SHAPE_TRACK_ATTR]), designName, type="string")
    if message:
        om2.MGlobal.displayInfo("Success: Control `{}` has been replaced with the design shape "
                                "`{}`".format(controlName, designName))


def replaceWithShapeDesignList(controlList, folderpath="", designName="circle", rotateOffset=(0, 0, 0), autoScale=True,
                               message=True):
    """Replaces the controlList with a new shape design as per "designName".  Will delete existing curve shape nodes.

    :param controlList: The control shape design transform, will replace it's curve.
    :type controlList: list(str)
    :param folderpath: Optional folder path of the .shape file. If empty "" then search within the Zoo internal library
    :type folderpath: str
    :param designName: The shape/look/design of the control, control names can be found in skeleton builder's folder
    :type designName: str
    :param rotateOffset: rotate offset of the control, is a CV rotation offset not object
    :type rotateOffset: list(float)
    :param autoScale: Try to automatically scale the size of the designName replacing the current control?
    :type autoScale: bool
    :param message: Report the messages to the user?
    :type message: bool
    """
    rememberSel = cmds.ls(selection=True, long=True)  # must remember selection as will select
    for controlName in controlList:
        replaceWithShapeDesign(controlName, folderpath=folderpath, designName=designName, rotateOffset=rotateOffset,
                               autoScale=autoScale, message=False)
    if message:
        om2.MGlobal.displayInfo("Success: Controls have been replaced with the design shape `{}`".format(designName))
    cmds.select(rememberSel, replace=True)


def replaceWithShapeDesignSelection(folderpath="", designName="circle", rotateOffset=(0, 0, 0), autoScale=True,
                                    message=True, keepSelection=True):
    """Replaces the selection with a new shape design as per "designName".  Will delete existing curve shape nodes.

    :param folderpath: Optional folder path of the .shape file. If empty "" then search within the Zoo internal library
    :type folderpath: str
    :param designName: The shape/look/design of the control, control names can be found in skeleton builder's folder
    :type designName: str
    :param rotateOffset: rotate offset of the control, is a CV rotation offset not object
    :type rotateOffset: list(float)
    :param autoScale: Try to automatically scale the size of the designName replacing the current control?
    :type autoScale: bool
    :param message: Report the messages to the user?
    :type message: bool
    :param keepSelection: Maintain the current selection? True is recommended
    :type keepSelection: bool
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        if message:
            om2.MGlobal.displayWarning("Please select control curves")
        return
    replaceWithShapeDesignList(selObjs, folderpath=folderpath, designName=designName, rotateOffset=rotateOffset,
                               autoScale=autoScale,
                               message=message)
    if keepSelection:
        cmds.select(selObjs, replace=True)


def replaceDesignBrkCnctCtrl(cntrl, folderpath="", designName="circle", autoScale=True, rotateOffset=(0, 0, 0),
                             maintainLineWidth=True, message=True):
    """Replaces a control with a new shape design as per "designName" with break-off functionality.
    Deletes existing curve shape nodes.

    Break-off functionality maintains the ctrl's offset picot and scale information by using the zoo tracker attrs. \
    For example the replace will maintain any offsets of the control.

    :param cntrl: The control shape design transform, will replace it's curve.
    :type cntrl: str
    :param folderpath: Optional folder path of the .shape file. If empty "" then search within the Zoo internal library
    :type folderpath: str
    :param designName: The shape/look/design of the control, control names can be found in skeleton builder's folder
    :type designName: str
    :param autoScale: Try to automatically scale the size of the designName replacing the current control?
    :type autoScale: bool
    :param rotateOffset: rotate offset of the control, is a CV rotation offset not object
    :type rotateOffset: list(float)
    :param message: Report the messages to the user?
    :type message: bool
    :param maintainLineWidth: If True will keep the line thickness of the previous control (default)
    :type maintainLineWidth: bool
    """
    skipReconnect = False
    brokenOffCtrl, replaceGrp, networkNode = breakTrackControl(cntrl, applyTempColor=False, createNetwork=False)
    if not brokenOffCtrl:  # already broken off, just straight replace
        brokenOffCtrl = cntrl
        skipReconnect = True
    # do the scale
    replaceWithShapeDesign(brokenOffCtrl, folderpath=folderpath, designName=designName, autoScale=autoScale,
                           rotateOffset=rotateOffset, message=message, maintainLineWidth=maintainLineWidth)
    if not skipReconnect:  # if not a breakoff ctrl
        reconnectBreakControl(brokenOffCtrl, cntrl, replaceGrp)


def replaceDesignBrkCnctCtrlList(cntrlList, folderpath="", designName="circle", autoScale=True, rotateOffset=(0, 0, 0),
                                 message=True, maintainLineWidth=True):
    """Replaces a list of controls with a new shape design as per "designName" with break-off functionality.
    Deletes existing curve shape nodes.

    Break-off functionality maintains the ctrl's offset picot and scale information by using the zoo tracker attrs. \
    For example the replace will maintain any offsets of the control.

    :param cntrlList: A control transform list of names, will replace their curves.
    :type cntrlList: list(str)
    :param designName: The shape/look/design of the control, control names can be found in skeleton builder's folder
    :type designName: str
    :param autoScale: Try to automatically scale the size of the designName replacing the current control?
    :type autoScale: bool
    :param rotateOffset: rotate offset of the control, is a CV rotation offset not object
    :type rotateOffset: list(float)
    :param message: Report the messages to the user?
    :type message: bool
    :param maintainLineWidth: If True will keep the line thickness of the previous control (default)
    :type maintainLineWidth: bool
    """
    for ctrl in cntrlList:
        replaceDesignBrkCnctCtrl(ctrl, folderpath=folderpath, designName=designName, autoScale=autoScale,
                                 rotateOffset=rotateOffset, message=message, maintainLineWidth=maintainLineWidth)


# ---------------------------
# DUPLICATE CONTROLS
# ---------------------------


def duplicateControl(controlName, useSelectedName=False, copyScaleTracker=True, deleteNodeShapes=False):
    """Duplicates the object (usually a curve) to it's own new transform parented to the world, joints become transforms

    Useful for breaking off control curves

    :param controlName: The control name to duplicate
    :type controlName: str
    :param useSelectedName: Use the name of the control with a suffix to name the new control?
    :type useSelectedName: bool
    :param copyScaleTracker: Copies the scaleTrackerAttributes if they exist on the controlName?
    :type copyScaleTracker: bool
    :return duplicatedCtrl: The new duplicated transform node name
    :rtype duplicatedCtrl: str
    """
    zooScaleTrack = list()
    zooScaleDefault = [1.0, 1.0, 1.0]
    duplicatedCtrl = shapenodes.duplicateWithoutChildren(controlName, name='zoo_tempControlXX',
                                                         deleteNodeShapes=deleteNodeShapes)
    if cmds.listRelatives(duplicatedCtrl, parent=True, fullPath=True):  # None if already parented to world
        duplicatedCtrl = cmds.parent(duplicatedCtrl, world=True, absolute=True)[0]
    if cmds.nodeType(duplicatedCtrl) == "joint":  # is a joint so transfer shape to a transform node
        if copyScaleTracker:  # get the attribute values as they won't be duplicated
            zooScaleTrack = getCreateControlScale(controlName)
            zooScaleDefault = getControlDefaultScale(controlName)
        dupGrp = cmds.group(empty=True, name='zoo_tempMirror_GrpXX')
        cmds.matchTransform([dupGrp, controlName], pos=1, rot=1, scl=0, piv=0)
        # Swap onto the new grp, will delete the old dupCtrl (previously a joint)
        duplicatedCtrl = shapenodes.shapeNodeParentList([duplicatedCtrl, dupGrp], deleteOriginal=True,
                                                        reportSuccess=False)
        if copyScaleTracker:  # add the scale tracker attributes
            addTrackAttrs(duplicatedCtrl, zooScaleTrack)
            cmds.setAttr(".".join([duplicatedCtrl, ZOO_SCALE_DEFAULT_ATTR]), zooScaleDefault[0], zooScaleDefault[1],
                         zooScaleDefault[2])
    if useSelectedName:  # use the controlName to name the object
        lonNamePrefix, namespace, shortName = namehandling.mayaNamePartTypes(controlName)
        if namespace:
            shortName = ":".join([namespace, shortName])
        if "_newControl" not in shortName:
            duplicatedCtrl = cmds.rename(duplicatedCtrl, "{}_newControl".format(shortName))
        else:
            duplicatedCtrl = cmds.rename(duplicatedCtrl, shortName)  # maya will increment
    return duplicatedCtrl


def duplicateControlList(controlList, selectNewCtrls=True, useSelectedName=True, copyScaleTracker=True):
    """Duplicates an obj list with shape nodes to it's own new transform parented to the world, joints become transforms

    :param controlList: The control names to break off
    :type controlList: list(str)
    :param selectNewCtrls: after duplicating select the new controls?
    :type selectNewCtrls: bool
    :param useSelectedName: Use the name of the control with a suffix to name the new control?
    :type useSelectedName: bool
    :param copyScaleTracker: Copies the scaleTrackerAttributes if they exist on the controlName?
    :type copyScaleTracker: bool
    :return duplicatedCtrlList: The new duplicated transform node list of names
    :rtype duplicatedCtrlList: list(str)
    """
    duplicatedCtrlList = list()
    for ctrl in controlList:
        duplicatedCtrlList.append(duplicateControl(ctrl, useSelectedName=useSelectedName,
                                                   copyScaleTracker=copyScaleTracker))
    if selectNewCtrls:
        cmds.select(duplicatedCtrlList, replace=True)
    return duplicatedCtrlList


def breakoffControlSelected(selectNewCtrls=True, children=False, useSelectedName=True, copyScaleTracker=True,
                            message=True):
    """Duplicates a curve selection to it's own new list of transforms, parented to the world, joints become transforms

    :param selectNewCtrls: after duplicating select the new controls?
    :type selectNewCtrls: bool
    :param children: Include all children in the hierarchy?
    :type children: bool
    :param useSelectedName: Use the name of the control with a suffix to name the new control?
    :type useSelectedName: bool
    :param copyScaleTracker: Copies the scaleTrackerAttributes if they exist on the controlName?
    :type copyScaleTracker: bool
    :param message: Return the message to the user?
    :type message: bool
    :return duplicatedCtrlList: The new duplicated transform node list of names
    :rtype duplicatedCtrlList: list(str)
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        if message:
            om2.MGlobal.displayWarning("No controls selected, please select controls.")
        return
    cntrlList = filtertypes.filterTypeReturnTransforms(selObjs, children=children, shapeType="nurbsCurve")
    if not cntrlList:
        if message:
            om2.MGlobal.displayWarning("No controls selected, please select controls.")
        return
    return duplicateControlList(cntrlList, selectNewCtrls=selectNewCtrls, useSelectedName=useSelectedName,
                                copyScaleTracker=copyScaleTracker)


# ---------------------------
# BREAK OFF CONTROLS
# ---------------------------


def breakTrackControl(ctrlName, applyTempColor=True, tempColor=(1.0, 0.0, 1.0), createNetwork=True):
    """Breaks off a control turning it pink (optional) with a group.  Transformations/pivot use the tracker info. \
    A network node (optional) tracks the nodes so they can be easily reconnected back to the original transform or \
    joint.

    :param ctrlName: The control transform name to break off.
    :type ctrlName: str
    :param applyTempColor: If True turns the control pink or the given tempColor
    :type applyTempColor: bool
    :param tempColor: The color of the break off control's color if applyTempColor is on.  Linear float color.
    :type tempColor: bool
    :param createNetwork: Create a network node to track the reconnect.  Not needed if only using temporarily.
    :type createNetwork: bool
    :return newControlTransform: The name of the broken off control, empty string if already a broken off control
    :rtype newControlTransform: str
    :return grp: The name of the broken off control's group, empty string if already a broken off control
    :rtype grp: str
    :return networkName: The name of the network node used for reconnecting the control back to it's original node
    :rtype networkName: str
    """
    if cmds.attributeQuery(ZOO_TEMPBREAK_CTRL_ATTR, node=ctrlName, exists=True):
        return "", "", ""
    networkName = ""
    # get attributes, scale, rot, trans information, create the attributes on the new newControlTransform
    translate, rotate, scale, color, shape = getAllTrackerInfo(ctrlName)  # get the scale rot pos
    curveShapes = cmds.listRelatives(ctrlName, shapes=True, type="nurbsCurve", fullPath=True)
    # Get line width
    lineWidth = curveLinethickness(ctrlName)
    # Break off the control removes the curve shapes from the original
    brokenOffCtrl = shapenodes.duplicateWithoutChildren(ctrlName, name='{}_break'.format(ctrlName),
                                                        deleteNodeShapes=False, duplicateShapeType="nurbsCurve")
    # delete curve shapes from the original control
    cmds.delete(curveShapes)  # there must be curve shapes
    # Group the new control and rename it to a temp name
    grp, brokenOffCtrl, grpUuid, objUuid = groupInPlace(brokenOffCtrl, includeScale=True)
    newControlTransform = str(brokenOffCtrl)
    brokenOffCtrl = cmds.rename(brokenOffCtrl, "{}_tempDelMeXX".format(brokenOffCtrl))
    # Create the new transform that the curve shapes will be moved onto
    newControlTransform = cmds.group(name=newControlTransform, empty=True)  # create the group that will be the control
    newControlTransform = cmds.parent(newControlTransform, grp)[0]
    # set attributes, scale, rot, trans information, create the attributes on the new newControlTransform
    cmds.setAttr("{}.translate".format(newControlTransform), translate[0], translate[1], translate[2])
    cmds.setAttr("{}.rotate".format(newControlTransform), rotate[0], rotate[1], rotate[2])
    cmds.setAttr("{}.scale".format(newControlTransform), scale[0], scale[1], scale[2])
    addTrackAttrs(newControlTransform, scale=scale, rotate=rotate, translate=translate, color=color,
                  designName=shape)
    # Shape parent the brokenOffCtrl to newControlTransform
    newControlTransform = shapenodes.shapeNodeParentList([brokenOffCtrl, newControlTransform], deleteOriginal=True,
                                                         reportSuccess=False, renameShapes=True)
    # set line width
    setCurveLineThickness([newControlTransform], lineWidth)
    # Color the control the temp color
    if applyTempColor:
        shapeList = cmds.listRelatives(newControlTransform, shapes=True, type="nurbsCurve", fullPath=True)
        if shapeList:
            for shape in shapeList:
                objcolor.setColorShapeRgb(shape, tempColor, linear=True)
    # Create the network message node tracker and attributes
    if createNetwork:
        networkName = "_".join([newControlTransform, ZOO_TEMPBREAK_NETWORK])
        networkName = nodeCreate.messageNodeObjs(networkName, [newControlTransform], ZOO_TEMPBREAK_CTRL_ATTR)
        nodeCreate.messageNodeObjs(networkName, [grp], ZOO_TEMPBREAK_GRP_ATTR, createNetworkNode=False)
        if cmds.attributeQuery(ZOO_TEMPBREAK_MASTER_ATTR, node=ctrlName, exists=True):  # can already exist
            cmds.deleteAttr(ctrlName, attribute=ZOO_TEMPBREAK_MASTER_ATTR)
        nodeCreate.messageNodeObjs(networkName, [ctrlName], ZOO_TEMPBREAK_MASTER_ATTR, createNetworkNode=False)
    return newControlTransform, grp, networkName


def breakTrackControlList(ctrlNameList, applyTempColor=True, tempColor=(1.0, 0.0, 1.0), createNetwork=True):
    """Breaks off a list of controls turning them pink (optional) and grouped.  Transformations/pivot use the tracker \
    info. A network node (optional) tracks the nodes so they can be easily reconnected back to the original transform \
    or joint.

    :param ctrlNameList: The list of control transform names to break off.
    :type ctrlNameList: list(str)
    :param applyTempColor: If True turns the control pink or the given tempColor
    :type applyTempColor: bool
    :param tempColor: The color of the break off control's color if applyTempColor is on.  Linear float color.
    :type tempColor: bool
    :param createNetwork: Create a network node to track the reconnect.  Not needed if only using temporarily.
    :type createNetwork: bool
    :return newControlList: The names of the broken off controls, empty strings if already broken off
    :rtype newControlList: list(str)
    :return newGrpList: The names of the broken off control groups, empty string/s if already a broken off
    :rtype newGrpList: list(str)
    """
    newControlList = list()
    newGrpList = list()
    for ctrl in ctrlNameList:
        newCtrl, newGrp, networkNode = breakTrackControl(ctrl, applyTempColor=applyTempColor, tempColor=tempColor,
                                                         createNetwork=createNetwork)
        if newCtrl:
            newControlList.append(newCtrl)
            newGrpList.append(newGrp)
    return newControlList, newGrpList


def breakOffControlSelected(applyTempColor=True, tempColor=(1.0, 0.0, 1.0), createNetwork=True, selectControls=True):
    """Breaks off selected of controls turning them pink (optional) and grouped.  Transformations/pivot use the tracker \
    info. A network node (optional) tracks the nodes so they can be easily reconnected back to the original transform \
    or joint.

    :param applyTempColor: If True turns the control pink or the given tempColor
    :type applyTempColor: bool
    :param tempColor: The color of the break off control's color if applyTempColor is on.  Linear float color.
    :type tempColor: bool
    :param createNetwork: Create a network node to track the reconnect.  Not needed if only using temporarily.
    :type createNetwork: bool
    :return newControlList: The names of the broken off controls, empty strings if already broken off
    :rtype newControlList: list(str)
    :return newGrpList: The names of the broken off control groups, empty string/s if already a broken off
    :rtype newGrpList: list(str)
    """
    selObjs = cmds.ls(selection=True, long=True)
    curveTransforms = filtertypes.filterTypeReturnTransforms(selObjs,
                                                             children=False,
                                                             shapeType="nurbsCurve")
    if not curveTransforms:  # then no shapes as nurbsCurves
        return
    newControlList, newGrpList = breakTrackControlList(curveTransforms, applyTempColor=applyTempColor,
                                                       tempColor=tempColor,
                                                       createNetwork=createNetwork)
    if selectControls:
        cmds.select(newControlList, replace=True)
    return newControlList, newGrpList


# ---------------------------
# RECONNECT CONTROLS
# ---------------------------


def reconnectBreakControl(breakCntrl, masterCntrl, replaceGrp, ignoreScale=False):
    """Reconnects a break-off control back to it's master transform or joint node. Will return the control to \
    it's original color now with the new scale, rot, translation info.

    :param breakCntrl: The break-off control transform name.
    :type breakCntrl: str
    :param masterCntrl: Master control that will remain, this is the joint or transform node used in scene
    :type masterCntrl: str
    :param replaceGrp: The group of the breakCntrl, will be deleted once finished
    :type replaceGrp: str
    :param ignoreScale: Can ignore the scale while reconnecting which is only used while flip-mirroring
    :type ignoreScale: bool
    """
    # Get the attribute info, (trans, rot, scale, shape and color)
    translate = cmds.getAttr("{}.translate".format(breakCntrl))[0]
    rotate = cmds.getAttr("{}.rotate".format(breakCntrl))[0]
    scale = cmds.getAttr("{}.scale".format(breakCntrl))[0]
    designName = cmds.getAttr(".".join([breakCntrl, ZOO_SHAPE_TRACK_ATTR]))
    color = cmds.getAttr(".".join([breakCntrl, ZOO_COLOR_TRACK_ATTR]))[0]
    # Shape parent the tempCurve to the master
    masterCntrl = shapenodes.shapeNodeParentList([breakCntrl, masterCntrl], deleteOriginal=True, reportSuccess=False,
                                                 renameShapes=True, delShapeType="nurbsCurve")
    # Set the attribute on the master
    cmds.setAttr(".".join([masterCntrl, ZOO_TRANSLATE_TRACK_ATTR]), translate[0], translate[1], translate[2])
    cmds.setAttr(".".join([masterCntrl, ZOO_ROTATE_TRACK_ATTR]), rotate[0], rotate[1], rotate[2])
    if not ignoreScale:  # set scale as always positive for flipping
        cmds.setAttr(".".join([masterCntrl, ZOO_SCALE_TRACK_ATTR]), scale[0], scale[1], scale[2])
    cmds.setAttr(".".join([masterCntrl, ZOO_COLOR_TRACK_ATTR]), color[0], color[1], color[2])
    cmds.setAttr(".".join([masterCntrl, ZOO_SHAPE_TRACK_ATTR]), designName, type="string")
    # Set the color
    shapeList = cmds.listRelatives(masterCntrl, shapes=True, type="nurbsCurve", fullPath=True)
    if shapeList:
        for shape in shapeList:
            objcolor.setColorShapeRgb(shape, color, linear=True)
    # Cleanup the remaining empty group and network node, and remove the network attr on the master control
    cmds.delete(replaceGrp)


def reconnectBreakControlList(breakCntrlList, masterCntrlList, replaceGrpList):
    """Reconnects a list of break-off controls back to their master transforms or joint nodes. Will return the controls\
     to their original color now with the new scale, rot, translation info.

    :param breakCntrlList: The break-off control transform names.
    :type breakCntrlList: list(str)
    :param masterCntrlList: Master controls that will remain, these are the joints or transform nodes used in scene
    :type masterCntrlList: list(str)
    :param replaceGrpList: The groups of the breakCntrl, will be deleted once finished
    :type replaceGrpList: list(str)
    """
    for i, breakCtrl in enumerate(breakCntrlList):
        reconnectBreakControl(breakCtrl, masterCntrlList[i], replaceGrpList[i])


def reconnectBreakTempControlNetwork(breakCntrl):
    """Reconnects a break-off control back to it's master transform/joint node. Uses the network node to find the \
    master. Will return the control to it's original color with the new scale, rot, translation info.  Removes the \
    left over nodes.

    :param breakCntrl: The break-off control transform name.
    :type breakCntrl: str
    """
    # Get the grp, breakCntrl and the masterCtrl
    networkNode = nodeCreate.getNodeAttrConnections([breakCntrl], ZOO_TEMPBREAK_CTRL_ATTR)[0]
    masterCntrl = nodeCreate.getNodeAttrConnections([networkNode], ZOO_TEMPBREAK_MASTER_ATTR)[0]
    replaceGrp = nodeCreate.getNodeAttrConnections([networkNode], ZOO_TEMPBREAK_GRP_ATTR)[0]
    # break off the control
    reconnectBreakControl(breakCntrl, masterCntrl, replaceGrp)
    # Cleanup the remaining empty group and network node, and remove the network attr on the master control
    cmds.delete(networkNode)
    cmds.deleteAttr(masterCntrl, attribute=ZOO_TEMPBREAK_MASTER_ATTR)


def reconnectBreakTempControlNetwork(breakCntrlList):
    """Reconnects a list of break-off controls back to their master transform/joint nodes. Uses network nodes to find \
    the masters. Will return the controls to their original colors with the new scale, rot, translation info. \
     Removes the left over nodes.

    :param breakCntrlList: A list of break-off control transform names.
    :type breakCntrlList: list(str)
    """
    for breakCntrl in breakCntrlList:
        reconnectBreakTempControlNetwork(breakCntrl)


def reconnectAllBreakCtrls(message=True):
    """Reconnects all break-off controls in the scene back to their master transform/joint nodes. Uses network nodes \
    to find all the controls to reconnect. Returns the controls to their original colors with the new scale, rot, \
    translation information. Removes the left over nodes.

    :param message: Report the message to the user?
    :type message: bool
    :return masterCtrlList: A list of master controls that were reconnected
    :rtype masterCtrlList: list(str)
    """
    breakCtrlList = list()
    breakGrpList = list()
    masterCtrlList = list()
    # Find all the network nodes in the scene
    allNetworkNodes = cmds.ls(exactType="network")
    networkNodeList = [s for s in allNetworkNodes if ZOO_TEMPBREAK_NETWORK in s]  # returns all with break name matches
    if not networkNodeList:
        if message:
            om2.MGlobal.displayWarning("No break off controls found connected to network nodes "
                                       "containing the name `{}`".format(ZOO_TEMPBREAK_NETWORK))
        return
    for network in networkNodeList:  # Loop over the network nodes
        # Get the grp, masterCtrl and brokenCtrl add to lists
        breakCtrlTestList = nodeCreate.getNodeAttrConnections([network], ZOO_TEMPBREAK_CTRL_ATTR)
        if not breakCtrlTestList:  # the network node is dead and disconnected
            if message:
                om2.MGlobal.displayWarning("Node `{}` has no connections and has been deleted".format(network))
            continue
        breakCtrl = breakCtrlTestList[0]
        masterCntrl = nodeCreate.getNodeAttrConnections([network], ZOO_TEMPBREAK_MASTER_ATTR)[0]
        replaceGrp = nodeCreate.getNodeAttrConnections([network], ZOO_TEMPBREAK_GRP_ATTR)[0]
        breakCtrlList.append(breakCtrl)
        breakGrpList.append(replaceGrp)
        masterCtrlList.append(masterCntrl)
    reconnectBreakControlList(breakCtrlList, masterCtrlList, breakGrpList)
    cmds.delete(networkNodeList)
    cmds.select(deselect=True)
    if not masterCtrlList:
        if message:
            om2.MGlobal.displayWarning("No break off controls found in the scene connected to network "
                                       "nodes named".format(ZOO_TEMPBREAK_NETWORK))
        return
    if message:
        om2.MGlobal.displayInfo("Success: Controls reconnected `{}`".format(masterCtrlList))
    return masterCtrlList


# ---------------------------
# MODIFY BREAK/RECONNECT CONTROLS
# ---------------------------


def scaleBreakConnectCtrl(cntrl, scaleXYZ, relative=True):
    """Scales a control by breakTrackControl(); does the scale in the shapes object space and then reconnects.
    Break-off uses the zoo tracker information to build the object space.

    Use relative=True for offsets and relative=False for setting the absolute scale.

    :param cntrl: The control transform name to scale.
    :type cntrl: str
    :param scaleXYZ: The scale in [scaleX, scaleY, scaleZ], use relative True to offset or False to set absolutely
    :type scaleXYZ: list(float)
    :param relative: True for offsetting the current scale and relative=False for setting the absolute scale.
    :type relative: bool
    """
    brokenOffCtrl, replaceGrp, networkNode = breakTrackControl(cntrl, applyTempColor=False, createNetwork=False)
    # do the scale
    cmds.scale(scaleXYZ[0], scaleXYZ[1], scaleXYZ[2], brokenOffCtrl, relative=relative)
    reconnectBreakControl(brokenOffCtrl, cntrl, replaceGrp)


def scaleBreakConnectCtrlList(cntrlList, scaleXYZ, relative=True):
    """Scales a control by breakTrackControl(); does the scale in the shapes object space and then reconnects.
    Break-off uses the zoo tracker information to build the object space.

    Use relative=True for offsets and relative=False for setting the absolute scale.

    :param cntrlList: The list of control transform names to scale.
    :type cntrlList: list(str)
    :param scaleXYZ: The scale in [scaleX, scaleY, scaleZ], use relative True to offset or False to set absolutely
    :type scaleXYZ: list(float)
    :param relative: True for offsetting the current scale and relative=False for setting the absolute scale.
    :type relative: bool
    """
    for ctrl in cntrlList:
        if not cmds.attributeQuery(ZOO_TEMPBREAK_CTRL_ATTR, node=ctrl, exists=True):  # Regular control
            scaleBreakConnectCtrl(ctrl, scaleXYZ, relative=relative)
        else:  # Has already been broken off
            cmds.scale(scaleXYZ[0], scaleXYZ[1], scaleXYZ[2], ctrl, relative=relative)


def flipBreakConnectCtrl(cntrl, flipAxis="X"):
    """Flip-mirrors (mirror for a single control) with breakTrackControl();  does the flip in the shape's object space \
    and then reconnects.
    Break-off uses the zoo tracker information to build the object space.

    The flipAxis can be "X", "Y", or "Z".  Will flip relative to the local space of the break control not the master \
    control.

    :param cntrl: The control transform name to scale.
    :type cntrl: str
    :param flipAxis: The local axis to the break-control not the master to flip, can be "X", "Y", or "Z".
    :type flipAxis: str
    """
    brokenOffCtrl, replaceGrp, networkNode = breakTrackControl(cntrl, applyTempColor=False, createNetwork=False)
    scaleXYZ = cmds.getAttr("{}.scale".format(brokenOffCtrl))[0]
    # flip the scale
    if flipAxis == "X":
        scaleXYZ = (scaleXYZ[0] * -1, scaleXYZ[1], scaleXYZ[2])
    elif flipAxis == "Y":
        scaleXYZ = (scaleXYZ[0], scaleXYZ[1] * -1, scaleXYZ[2])
    else:
        scaleXYZ = (scaleXYZ[0], scaleXYZ[1], scaleXYZ[2] * -1)
    cmds.scale(scaleXYZ[0], scaleXYZ[1], scaleXYZ[2], brokenOffCtrl, relative=False)
    reconnectBreakControl(brokenOffCtrl, cntrl, replaceGrp, ignoreScale=True)  # Ignore setting scale for flip mirror


def flipBreakConnectCtrlList(cntrlList, flipAxis="X"):
    """Flip-mirrors (mirror for a single control) a list of controls with breakTrackControl(); does the flip then \
    reconnects.
    Break-off uses the zoo tracker information to build the object space.

    The flipAxis can be "X", "Y", or "Z".  Will flip relative to the local space of the break control not the master \
    control.

    :param cntrlList: The list of control transform names to scale.
    :type cntrlList: list(str)
    :param flipAxis: The local axis to the break-control not the master to flip, can be "X", "Y", or "Z".
    :type flipAxis: str
    """
    for ctrl in cntrlList:
        flipBreakConnectCtrl(ctrl, flipAxis=flipAxis)


def rotateBreakConnectCtrl(cntrl, rotateXYZ, relative=True):
    """Rotates a control by breakTrackControl(); does the rotate in the shape's object space and then reconnects.
    Break-off uses the zoo tracker information to build the object space.

    Use relative=True for offsets and relative=False for setting the absolute rotation.  Relative is object space.

    :param cntrl: The control transform name to scale.
    :type cntrl: str
    :param rotateXYZ: The rotate in [rotateX, rotateY, rotateZ], use relative True to offset or False to set absolutely.
    :type rotateXYZ: list(float)
    :param relative: True for offsetting the current rotation and relative=False for setting the absolute rotation.
    :type relative: bool
    """
    brokenOffCtrl, replaceGrp, networkNode = breakTrackControl(cntrl, applyTempColor=False, createNetwork=False)
    # do the scale
    cmds.rotate(rotateXYZ[0], rotateXYZ[1], rotateXYZ[2], brokenOffCtrl, objectSpace=True, relative=relative)
    reconnectBreakControl(brokenOffCtrl, cntrl, replaceGrp)


def rotateBreakConnectCtrlList(cntrlList, rotateXYZ, relative=True):
    """Rotates a list of controls with breakTrackControl(); does the rotate in the shape's object space and then \
    reconnects. Break-off uses the zoo tracker information to build the object space.

    Use relative=True for offsets and relative=False for setting the absolute rotation.  Relative is object space.

    :param cntrlList: The list of control transform names to scale.
    :type cntrlList: list(str)
    :param rotateXYZ: The rotate in [rotateX, rotateY, rotateZ], use relative True to offset or False to set absolutely.
    :type rotateXYZ: list(float)
    :param relative: True for offsetting the current rotation and relative=False for setting the absolute rotation.
    :type relative: bool
    """
    for ctrl in cntrlList:
        if not cmds.attributeQuery(ZOO_TEMPBREAK_CTRL_ATTR, node=ctrl, exists=True):  # not already broken off
            rotateBreakConnectCtrl(ctrl, rotateXYZ, relative=relative)
        else:
            cmds.rotate(rotateXYZ[0], rotateXYZ[1], rotateXYZ[2], ctrl, objectSpace=True, relative=relative)


def scaleResetBrkCnctCtrl(cntrl):
    """Resets a control scales with breakTrackControl(); as per the zoo tracker stored default scale attribute. \
    Performs the scale in the shape's object space and then reconnects.  Break-off uses the zoo tracker information to \
    build the object space.

    :param cntrl: The control transform name to scale.
    :type cntrl: str
    """
    brokenOffCtrl, replaceGrp, networkNode = breakTrackControl(cntrl, applyTempColor=False, createNetwork=False)
    # do the scale
    dfltScale = cmds.getAttr(".".join([cntrl, ZOO_SCALE_DEFAULT_ATTR]))[0]
    cmds.scale(dfltScale[0], dfltScale[1], dfltScale[2], brokenOffCtrl, relative=False, absolute=True)
    reconnectBreakControl(brokenOffCtrl, cntrl, replaceGrp)


def scaleResetBrkCnctCtrlList(cntrlList):
    """Resets a list of controls with breakTrackControl(); as per the zoo tracker stored default scale attribute. \
    Performs the scale in the shape's object space and then reconnects.  Break-off uses the zoo tracker information to \
    build the object space.

    :param cntrlList: The list of control transform names to scale.
    :type cntrlList: list(str)
    """
    for ctrl in cntrlList:
        if not cmds.attributeQuery(ZOO_TEMPBREAK_CTRL_ATTR, node=ctrl, exists=True):  # Regular control
            scaleResetBrkCnctCtrl(ctrl)
        else:  # Already broken off
            dfltScale = cmds.getAttr(".".join([ctrl, ZOO_SCALE_DEFAULT_ATTR]))[0]
            cmds.scale(dfltScale[0], dfltScale[1], dfltScale[2], ctrl, relative=False, absolute=True)


def rotateResetBrkCnctCtrl(cntrl):
    """Resets a control with breakTrackControl(); as per the zoo tracker stored default rotate attribute. \
    Performs the rotate in the shape's object space and then reconnects.  Break-off uses the zoo tracker information to \
    build the object space.

    :param cntrl: The control transform name to rotate.
    :type cntrl: str
    """
    brokenOffCtrl, replaceGrp, networkNode = breakTrackControl(cntrl, applyTempColor=False, createNetwork=False)
    # do the scale
    dfltRotate = cmds.getAttr(".".join([cntrl, ZOO_ROTATE_DEFAULT_ATTR]))[0]
    cmds.rotate(dfltRotate[0], dfltRotate[1], dfltRotate[2], brokenOffCtrl, objectSpace=True, relative=False)
    reconnectBreakControl(brokenOffCtrl, cntrl, replaceGrp)


def rotateResetBrkCnctCtrlList(cntrlList):
    """Resets a list of controls with breakTrackControl(); as per the zoo tracker stored default rotate attribute. \
    Performs the rotate in the shape's object space and then reconnects.  Break-off uses the zoo tracker information to \
    build the object space.

    :param cntrlList: The list of control transform names to scale.
    :type cntrlList: list(str)
    """
    for ctrl in cntrlList:
        if not cmds.attributeQuery(ZOO_TEMPBREAK_CTRL_ATTR, node=ctrl, exists=True):  # Regular control
            rotateResetBrkCnctCtrl(ctrl)
        else:
            dfltRotate = cmds.getAttr(".".join([ctrl, ZOO_ROTATE_DEFAULT_ATTR]))[0]
            cmds.rotate(dfltRotate[0], dfltRotate[1], dfltRotate[2], ctrl, objectSpace=True, relative=False)


# ---------------------------
# MIRROR CONTROLS
# ---------------------------


def mirrorControl(currentCntrl, destinationCntrl, mirrorAxis="X", keepColor=True):
    """Mirrors a ctrl curve from the current control to the destination control.

    :param currentCntrl: The control (curve) name to mirror
    :type currentCntrl: str
    :param destinationCntrl: The control (curve) name to recieve the mirrored shapes
    :type destinationCntrl:str
    :param mirrorAxis: The axis to mirror across "X', "Y" or "Z"
    :type mirrorAxis: str
    :param keepColor: Keep the existing control color if it exists?
    :type keepColor: bool
    :return updatedCtrl:  The destination control now with updated shape nodes.
    :rtype updatedCtrl: str
    """
    rememberSelection = cmds.ls(selection=True, long=True)
    if keepColor:  # record the existing control color, will be blue if None
        destinationCtrlColor = getColorControlTransform(destinationCntrl)
    # Duplicate the current control, just the transform/joint and shapes, parent to world -----------------------
    dupCtrl = duplicateControl(currentCntrl)
    # Mirror with the mirrorPivotGrp with negative scale -------------------------------------------------------
    mirrorPivotGrp = cmds.group(empty=True, name='zoo_tempMirrorPivotXX')
    dupCtrl = cmds.parent(dupCtrl, mirrorPivotGrp)[0]
    if mirrorAxis == "X":
        cmds.setAttr("{}.scaleX".format(mirrorPivotGrp), -1)
    elif mirrorAxis == "Y":
        cmds.setAttr("{}.scaleY".format(mirrorPivotGrp), -1)
    else:
        cmds.setAttr("{}.scaleZ".format(mirrorPivotGrp), -1)
    # Swap curves onto the destination ctrl and remove the old dupCtrl and mirrorPivotGrp ----------------------
    updatedCtrl = shapenodes.shapeNodeParentSafe([dupCtrl, destinationCntrl], deleteOriginal=True, reportSuccess=False)
    cmds.delete(mirrorPivotGrp)
    if keepColor:  # Color destination control with original color ---------------------------------------------
        objcolor.setColorListRgb([updatedCtrl], destinationCtrlColor, displayMessage=False, linear=True)
    cmds.select(rememberSelection, replace=True)
    return updatedCtrl


def checkValidMirrorObj(search, replace, pureName, namespace):
    """Checks if the current control "namespace + pureName" has a mirror with the suffix L R names.

    Only used internally in mirrorControlAutoName()

    Search "_L" and replace "_R", name "obj_L_ctrl", will search for "obj_R_ctrl" and return if found + unique.

    Returns:
        - mirrorName: If it was found, will be an empty str if nothing found.
        - unique: True if the mirror control found is unique, False if not unique

    :param search: The existing suffix or search text eg. "_L", note does not have to be a suffix eg "control1_L_ctrl"
    :type search: str
    :param replace: The new suffix or replace text eg. "_R", note does not have to be a suffix eg "control1_R_ctrl"
    :type replace: str
    :param pureName: The existing controls Maya pure name without long or namespace
    :type pureName: str
    :param namespace: The namespace if it exists, will include in the search.  Can be empty ie ""
    :type namespace: str
    :return mirrorCtrl: The name of the mirrorCtrl, will be empty str if not found ""
    :rtype mirrorCtrl: str
    :return unique: True only if found and the name is unique in the scene, only one obj found
    :rtype unique: bool
    """
    mirrorCtrl = pureName.replace(search, replace)
    if namespace:
        currentName = str(":".join([namespace, pureName]))
    else:  # no namespace
        currentName = str(pureName)
    if cmds.objExists(mirrorCtrl) and mirrorCtrl != currentName:  # may be multiples so check is unique
        if len(cmds.ls(mirrorCtrl)) == 1:  # Exists and is unique
            return mirrorCtrl, True
        else:  # Mirror name exists but is not unique
            return mirrorCtrl, False
    # None found
    return "", False


def mirrorReturnExists(mirrorName, unique, currentCntrl, keepColor, mirrorAxis, message=True):
    """Performs the mirror only if the mirrorName is unique in the scene.

    For kwarg docs see mirrorControlAutoName(), only used internally in mirrorControlAutoName()

    :return mirrorName: The name of the mirror object, will be empty string "" if duplicates
    :rtype mirrorName: str
    :return unique: True if the found object `mirrorName` is unique in the scene? False if duplicates
    :rtype unique: bool
    """
    if unique:  # All good so perform the mirror
        mirrorControl(currentCntrl=currentCntrl, destinationCntrl=mirrorName, mirrorAxis=mirrorAxis,
                      keepColor=keepColor)
        return mirrorName, unique
    if message:  # Not unique so skip mirror and message
        om2.MGlobal.displayWarning("The object named `{}` is not unique and cannot be mirrored.".format(mirrorName))
    return mirrorName, unique


def mirrorControlAutoName(currentCntrl, searchTags=(("_L", "_R"), ("_lft", "rgt")), mirrorAxis="X", keepColor=True):
    """Mirrors a single control and tries to automatically find the opposite control if it exists with the searchTags.

    If the mirrorObject is found and is also unique then perform the mirror. If not, it won't mirror.

    Returns:
        - mirrorName: If it was found, will be an empty str if nothing found.
        - unique: If True the obj was mirrored, the found mirror ctrl is unique, False if not unique and or not found

    :param currentCntrl: The control (curve) name to mirror
    :type currentCntrl: str
    :param searchTags: A tuple of tuples, each tuple contains the search and replace text for left and right.
    :type searchTags: tuple(tuple(str))
    :param mirrorAxis: The axis to mirror across "X', "Y" or "Z"
    :type mirrorAxis: str
    :param keepColor: Keep the existing control color if it exists?
    :type keepColor: bool
    :return mirrorName:  The destination control name, the object that has been mirrored if also unique
    :rtype mirrorName: str
    :return unique:  True if the mirror object was found and it is unique
    :rtype unique: bool
    """
    # Search scene to see if opposite name exists
    longPrefix, namespace, pureName = namehandling.mayaNamePartTypes(currentCntrl)
    for searchList in searchTags:
        # Check R matches
        mirrorName, unique = checkValidMirrorObj(searchList[0], searchList[1], pureName, namespace)
        if mirrorName:  # return, may not be unique
            return mirrorReturnExists(mirrorName, unique, currentCntrl, keepColor, mirrorAxis)
        # Check inverse, so L matches
        mirrorName, unique = checkValidMirrorObj(searchList[1], searchList[0], pureName, namespace)
        if mirrorName:  # Return, may not be unique
            return mirrorReturnExists(mirrorName, unique, currentCntrl, keepColor, mirrorAxis)
    # Nothing found
    return mirrorName, unique


def mirrorControlAutoNameList(cntrlList, searchTags=(("_L", "_R"), ("_lft", "_rgt")), mirrorAxis="X", keepColor=True,
                              message=False):
    """Mirrors a control list and tries to automatically find the opposite control if it exists with the searchTags.

    If a mirrorObject is found and is also unique then perform the mirror. If not, it won't mirror.

    Returns a list of lists, each list contains:
        - mirrorName: If found returns the name of the mirror object, if not found returns an empty str
        - unique: If True the obj was mirrored, the found mirror ctrl is unique, False if not unique and or not found

    :param cntrlList: The control list (curve list) names to mirror
    :type cntrlList: list(str)
    :param searchTags: A tuple of tuples, each tuple contains the search and replace text for left and right.
    :type searchTags: tuple(tuple(str))
    :param mirrorAxis: The axis to mirror across "X', "Y" or "Z"
    :type mirrorAxis: str
    :param keepColor: Keep the existing control color if it exists?
    :type keepColor: bool
    :param message: Report the message to the user?
    :type message: bool
    :return mirrorInfoList: A list of lists, each list contains the mirrorObj (empty if not found) and if it is unique
    :rtype mirrorInfoList: list(list(str))
    """
    mirrorInfoList = list()
    for ctrl in cntrlList:
        mirrorInfoList.append(mirrorControlAutoName(ctrl, searchTags=searchTags, mirrorAxis=mirrorAxis,
                                                    keepColor=keepColor))
    if not message:
        return mirrorInfoList
    # Report user messages if message ---------------------------------------------------------------------------
    objMirrored = list()
    objExistNotMirrored = list()
    objNotFound = list()
    for result in mirrorInfoList:
        if result[0] and result[1]:  # success so append to objMirrored
            objMirrored.append(result[0])
        elif result[0] and not result[1]:
            objExistNotMirrored.append(result[0])
        else:
            objNotFound.append(result[0])
    if objMirrored and not objExistNotMirrored and not objNotFound:
        om2.MGlobal.displayInfo("Success: All curve objects mirrored: {}".format(objMirrored))
    elif not objMirrored and not objExistNotMirrored:
        om2.MGlobal.displayWarning("No objects found by names `{}` to be mirrored".format(searchTags))
    elif objMirrored and objExistNotMirrored and not objNotFound:
        om2.MGlobal.displayWarning(
            "Controls Mirrored with warnings: Curves could not be mirrored as not unique {}, "
            "Curves mirrored are {}".format(objMirrored, objExistNotMirrored))
    elif objMirrored and not objExistNotMirrored and objNotFound:
        om2.MGlobal.displayWarning("Controls Mirrored with warnings: Some curves were not mirrored, "
                                   "Curves mirrored are {}".format(objMirrored, objExistNotMirrored))
    elif not objMirrored and objExistNotMirrored and objNotFound:
        om2.MGlobal.displayWarning("No Curves were mirrored, curves found but not unique are "
                                   "{}".format(objExistNotMirrored))
    elif objMirrored and objExistNotMirrored and objNotFound:
        om2.MGlobal.displayWarning("Controls Mirrored with warnings: Curves could not be mirrored as not unique {},"
                                   " Curves mirrored are {}".format(objMirrored, objExistNotMirrored))
    elif not objMirrored and objExistNotMirrored and not objNotFound:
        om2.MGlobal.displayWarning("Controls Not Mirrored: Curves could not be mirrored as "
                                   "not unique {}".format(objExistNotMirrored))
    return mirrorInfoList


def mirrorControlAutoNameSelected(searchTags=(("_L", "_R"), ("_lft", "rgt")), mirrorAxis="X", keepColor=True,
                                  children=False, message=True):
    """Mirrors a control selection, tries to automatically find the opposite control if it exists with the searchTags.

    If a mirrorObject is found and is also unique then perform the mirror. If not, it won't mirror.

    Returns a list of lists, each list contains:
        - mirrorName: If found returns the name of the mirror object, if not found returns an empty str
        - unique: If True the obj was mirrored and the mirror ctrl is unique, False if not unique and or not found

    Detailed user messages from mirrorControlAutoNameList() if messages=True

    :param searchTags: A tuple of tuples, each tuple contains the search and replace text for left and right.
    :type searchTags: tuple(tuple(str))
    :param mirrorAxis: The axis to mirror across "X', "Y" or "Z"
    :type mirrorAxis: str
    :param keepColor: Keep the existing control color if it exists?
    :type keepColor: bool
    :param children: Include all children in the hierarchy?
    :type children: bool
    :param message: Report the message to the user?
    :type message: bool
    :return mirrorInfoList: A list of lists, each list contains the mirrorObj (empty if not found) and if it is unique
    :rtype mirrorInfoList: list(list(str))
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        if message:
            om2.MGlobal.displayWarning("No controls selected, please select controls.")
        return
    cntrlList = filtertypes.filterTypeReturnTransforms(selObjs, children=children, shapeType="nurbsCurve")
    if not cntrlList:
        if message:
            om2.MGlobal.displayWarning("No controls selected, please select controls.")
        return
    return mirrorControlAutoNameList(cntrlList, searchTags=searchTags, mirrorAxis=mirrorAxis, keepColor=keepColor,
                                     message=message)


# ---------------------------
# COPY PASTE CONTROLS
# ---------------------------


def copyControl(ctrl):
    """Copies the zoo tracker information from a control. Returns:

        Translate
        Rotate
        Scale
        Color
        Shape

    While pasting this info is needed in conjunction with the paste control name to paste from.

    :param ctrl: The transform name of the control
    :type ctrl: str
    :return translate: The zoo tracker translation value as [X, Y, Z]
    :rtype translate: list(float)
    :return rotate: The zoo tracker rotation value as [X, Y, Z]
    :rtype rotate: list(float)
    :return scale: The zoo tracker scale value as [X, Y, Z]
    :rtype scale: list(float)
    :return color: The zoo tracker color value as [R, G, B], color is linear float 0-1
    :rtype color: list(float)
    :return shape: The name of the zoo tracker design shape of the control ie "circle"
    :rtype shape: str
    """
    return getAllTrackerInfo(ctrl)


def pasteControl(ctrlList, pasteCtrl, translate, rotate, scale, color, shape):
    """Pastes the curve shape nodes and zoo tracker information onto a list of controls.

    :param ctrlList: The list of control transform names to paste the control shapes onto.
    :type ctrlList: list(str)
    :param pasteCtrl: The control transform name to paste the curve shapes from
    :type pasteCtrl: str
    :param translate: The zoo tracker translation value as [X, Y, Z]
    :type translate: list(float)
    :param rotate: The zoo tracker rotation value as [X, Y, Z]
    :type rotate: list(float)
    :param scale: The zoo tracker scale value as [X, Y, Z]
    :type scale: list(float)
    :param color: The zoo tracker color value as [R, G, B], color is linear float 0-1
    :type color: list(float)
    :param shape: The name of the zoo tracker design shape of the control ie "circle"
    :type shape: str
    """
    dupCtrlList = list()
    dupCtrlList.append(duplicateControl(pasteCtrl, useSelectedName=True, copyScaleTracker=False,
                                        deleteNodeShapes=False))
    ctrlNumber = len(ctrlList)
    for i in range(ctrlNumber - 1):
        dupCtrlList.append(cmds.duplicate(dupCtrlList[0])[0])
    # match and replace controls
    for i, ctrl in enumerate(dupCtrlList):
        cmds.matchTransform([ctrl, ctrlList[i]], pos=1, rot=1, scl=1, piv=0)
        ctrlList[i] = shapenodes.shapeNodeParentList([ctrl, ctrlList[i]], deleteOriginal=True, reportSuccess=False,
                                                     delShapeType="nurbsCurve")
        addTrackAttrs(ctrlList[i], scale=scale, color=color, rotate=rotate, translate=translate, designName=shape)
    cmds.select(ctrlList, replace=True)


# ---------------------------
# TEMPLATE REFERENCE
# ---------------------------


def templateRefToggle(ctrl, template=True, message=False):
    """Toggles the template or reference attributes of a control.

    :param ctrl: The transform name of the control
    :type ctrl: str
    :param template: True will template, False will reference toggle
    :type template: bool
    :param message: Report the message to the user?
    :type message: bool
    """
    shapes = cmds.listRelatives(ctrl, shapes=True, type="nurbsCurve", fullPath=True)
    if not shapes:
        return
    if not cmds.getAttr("{}.overrideDisplayType".format(shapes[0])):  # Template
        shapenodes.templateRefShapeNodes(ctrl, template=True, message=False, unTemplateRef=False)
    else:  # Un-template
        shapenodes.templateRefShapeNodes(ctrl, template=True, message=False, unTemplateRef=True)


def templateRefToggleList(ctrlList, template=True, message=False, unTemplateRef=False):
    """Toggles the template or reference attributes of a list of controls.

    :param ctrlList: The list of control transform names to template or reference toggle
    :type ctrlList: list(str)
    :param template: True will template, False will reference toggle
    :type template: bool
    :param message: Report the message to the user?
    :type message: bool
    """
    for ctrl in ctrlList:
        templateRefToggle(ctrl, template=template, message=message)


# ---------------------------
# SPINE BUILDER
# ---------------------------


def orientAimControlsNulls(objList, globalOrientObj):
    """Creates nulls (grps) for orient matching via aims.  Also gives global up vectors relative to a globalOrientObj
    this is a messy function, could be done more cleanly with math instead of using aims, but it works
    Currently aims controls on y

    :param objList: objects for locator positions
    :type objList: list
    :param globalOrientObj: The object name that dictates the overall up vector
    :type globalOrientObj: list
    :return nullList: the created locators
    :rtype nullList: list
    """
    nullList = list()
    for i, obj in enumerate(objList):
        nullList.append(cmds.group(name="tempNull_{}".format(i), empty=1, world=1))
        alignutils.matchObjTransRot(nullList[i], obj, message=False)  # match
    # get the vector of the globalOrientObj
    globalObjMatrix = cmds.xform(globalOrientObj, worldSpace=True, matrix=True, query=True)
    globalZVector = globalObjMatrix[8:11]  # switchYVector = switchObjMatrix[4:7]  # switchXVector = switchObjMatrix[:3]
    # aim nulls at each other
    direction = 1.0
    for i, null in enumerate(nullList):
        if i + 1 == len(nullList):
            cmds.aimConstraint([nullList[i - 1], null], worldUpVector=globalZVector, upVector=(0.0, 0.0, 1.0),
                               aimVector=(0.0, direction * -1.0, 0.0), maintainOffset=False)
            continue
        cmds.aimConstraint([nullList[i + 1], null], worldUpVector=globalZVector, upVector=(0.0, 0.0, 1.0),
                           aimVector=(0.0, direction, 0.0), maintainOffset=False)
    return nullList


def orientControlsAims(controlList, orientGlobalVectorObj=""):
    """Orients a control list so that the controls aim toward each other, useful for splines possibly other
    The orientGlobalVectorObj gives an overall object up for the scene
    Aims controls +y and globalObject up is -z

    :param controlList: the control names
    :type controlList: list
    :param orientGlobalVectorObj: the object for the world up on aims, uses obj -z (ie spine), if "" will be 1st ctrl
    :type orientGlobalVectorObj: str
    """
    if not orientGlobalVectorObj:  # then use the first control
        orientGlobalVectorObj = controlList[0]
    orientedNullList = orientAimControlsNulls(controlList, orientGlobalVectorObj)
    alignutils.matchObjTransRotLists(controlList, orientedNullList, message=False)
    cmds.delete(orientedNullList)


# ---------------------------
# GUI FUNCTIONS WITH UNDO
# ---------------------------


@general.undoDecorator
def buildControlsGUI(buildType=CONTROL_BUILD_TYPE_LIST[1],
                     folderpath="",
                     designName="circle",
                     rotateOffset=(0, -90, 0),
                     scale=(1.0, 1.0, 1.0),
                     children=False,
                     rgbColor=(0, 0, 1),
                     postSelectControls=True,
                     trackScale=True,
                     lineWidth=-1,
                     grp=True,
                     freezeJnts=True):
    """Builds controls usually based on the GUI value from the list CONTROL_BUILD_TYPE_LIST:

        "Joint, Shape Parent Ctrl"
        "Match Selection Only"
        "Constrain Obj, Cnstn Ctrl"
        "Constrain Obj, Parent Ctrl"
        "Constrain Obj, Float Ctrl"

    :param buildType: The type to build
    :type buildType: str
    :param folderpath: Optional folder path of the .shape file. If empty "" then search within the Zoo internal library
    :type folderpath: str
    :param designName: The shape/look/design of the control, control names can be found in skeleton builder's folder
    :type designName: str
    :param rotateOffset: rotate offset of the control, is a CV rotation offset not object
    :type rotateOffset: list(float)
    :param scale: The scale of each control in Maya units.  Is measured in radius, not width.
    :type scale: list(float)
    :param children: Will create controls for all children
    :type children: bool
    :param rgbColor: The color of the control in rgb color (color values should be in linear color)
    :type rgbColor: tuple
    :param postSelectControls: If True will select the controls at the end of the function
    :type postSelectControls: bool
    :param trackScale: Suffix the controls with an underscore and filterTypes.CONTROLLER_SX, usually "ctrl"
    :type trackScale: bool
    :param lineWidth: The width of the curve's lines in pixels, -1 is default and will use global pref settings
    :type lineWidth: int
    :param grp: Group the controls where possible
    :type grp: bool
    :param freezeJnts: Freeze the joints to be sure they're good?
    :type freezeJnts: bool
    """
    if buildType == CONTROL_BUILD_TYPE_LIST[0]:  # Joint Shape Parent
        return createControlsOnSelected(curveScale=scale,
                                        folderpath=folderpath,
                                        rotateOffset=rotateOffset,
                                        designName=designName,
                                        grpJnts=grp,
                                        children=children,
                                        rgbColor=rgbColor,
                                        freezeJnts=freezeJnts,
                                        postSelectControls=postSelectControls,
                                        trackScale=trackScale,
                                        lineWidth=lineWidth)[0]

    elif buildType == CONTROL_BUILD_TYPE_LIST[1]:  # Match Selected Only
        return createControlsMatchSelected(folderpath=folderpath,
                                           curveScale=scale,
                                           rotateOffset=rotateOffset,
                                           designName=designName,
                                           grp=grp,
                                           children=children,
                                           rgbColor=rgbColor,
                                           lineWidth=lineWidth)[0]

    elif buildType == CONTROL_BUILD_TYPE_LIST[2]:  # Constrain Objects Constrain Controls
        return constrainControlsOnSelected(folderpath=folderpath,
                                           curveScale=scale,
                                           rotateOffset=rotateOffset,
                                           constrainControls=True,
                                           float=False,
                                           designName=designName,
                                           children=children,
                                           rgbColor=rgbColor,
                                           postSelectControls=postSelectControls,
                                           trackScale=trackScale,
                                           lineWidth=lineWidth)[1]

    elif buildType == CONTROL_BUILD_TYPE_LIST[3]:  # Constrain Objects Parent Controls
        return constrainControlsOnSelected(folderpath=folderpath,
                                           curveScale=scale,
                                           rotateOffset=rotateOffset,
                                           constrainControls=False,
                                           float=False,
                                           designName=designName,
                                           children=children,
                                           rgbColor=rgbColor,
                                           postSelectControls=postSelectControls,
                                           trackScale=trackScale,
                                           lineWidth=lineWidth)[1]

    elif buildType == CONTROL_BUILD_TYPE_LIST[4]:  # Constrain Objects Float Controls
        return constrainControlsOnSelected(folderpath=folderpath,
                                           curveScale=scale,
                                           rotateOffset=rotateOffset,
                                           constrainControls=False,
                                           float=True,
                                           designName=designName,
                                           children=children,
                                           rgbColor=rgbColor,
                                           postSelectControls=postSelectControls,
                                           trackScale=trackScale,
                                           lineWidth=lineWidth)[1]


@general.undoDecorator
def replaceControlCuves(cntrlList,
                        folderpath="",
                        designName="circle",
                        autoScale=True,
                        rotateOffset=(0, 0, 0),
                        message=True,
                        maintainLineWidth=True,
                        deselect=True):
    """Replace Control Curves function usually called by GUI as it supports undo

    Replaces a list of controls with a new shape design as per "designName" with break-off functionality.
    Deletes existing curve shape nodes.

    Break-off functionality maintains the ctrl's offset picot and scale information by using the zoo tracker attrs. \
    For example the replace will maintain any offsets of the control.

    :param cntrlList: A control transform list of names, will replace their curves.
    :type cntrlList: list(str)
    :param folderpath: Optional folder path of the .shape file. If empty "" then search within the Zoo internal library
    :type folderpath: list(str)
    :param designName: The shape/look/design of the control, control names can be found in skeleton builder's folder
    :type designName: str
    :param autoScale: Try to automatically scale the size of the designName replacing the current control?
    :type autoScale: bool
    :param rotateOffset: rotate offset of the control, is a CV rotation offset not object
    :type rotateOffset: list(float)
    :param message: Report the messages to the user?
    :type message: bool
    :param maintainLineWidth: If True will keep the line thickness of the previous control (default)
    :type maintainLineWidth: bool
    :param deselect: Will deselect the object after completing
    :type deselect: bool
    """
    replaceDesignBrkCnctCtrlList(cntrlList,
                                 folderpath=folderpath,
                                 designName=designName,
                                 autoScale=autoScale,
                                 rotateOffset=rotateOffset,
                                 message=message,
                                 maintainLineWidth=True)
    if deselect:
        cmds.select(deselect=True)
