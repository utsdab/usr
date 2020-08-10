"""
---------------
Rig Spine Build
---------------
Builds a Spline rig with various options
Trying object orientation and class inheritance in rigging

Also handles spline matching too

TO DO
------
- do cleanup
- figure auto build of right click menus
- need ordered dicts for controls, since they'll be called later... maybe can work of the part?
- fix cluster curve function
- move options onto a new control for the spine (will be on proxy in the future)
- add proxy attributes in 2017
- think about scale and keeping the controls nice for size

SHORT TERM
- add pure fk and distributed fk
- take out joint list as needed by rig generic
- Add Ingo Twist node
- add dual hybrid IK/FK tentacle setup

LATER
------
- Add complex offsets twists

LATER STILL
------
- Ribbon Setup

OPTIONAL
- take out lock attribute from controls zoo
- add group option to zoo control
"""

import maya.api.OpenMaya as om2
import maya.cmds as cmds

from zoo.libs.maya.utils import align_utils
from zoo.libs.maya.cmds.objutils import joints
from zoo.libs.maya.cmds.objutils import mesh
from zoo.libs.maya.cmds.objutils import namehandling
from zoo.libs.maya.cmds.objutils import attributes
from zoo.libs.maya.cmds.rig import nodes
from zoo.libs.maya.cmds.rig import parentfk
from zoo.libs.maya.cmds.rig import controls
from zoo.libs.maya.cmds.rig import splines
from zoo.libs.utils import zlogging

logger = zlogging.getLogger(__name__)


def createMessageNodeSetupSpline(splineDict):
    messageManager = splineDict["messageNodeManager"]
    # create/connect fk control attributes
    if splineDict["mainControls"]["fk"]:
        for i, control in enumerate(splineDict["mainControls"]["fk"]):
            cmds.addAttr(messageManager, longName="fkCtrl_{}".format(i), attributeType='message')
            cmds.connectAttr('{}.message'.format(control), '.'.join([messageManager, "fkCtrl_{}".format(i)]))
    # create/connect float attributes
    if splineDict["mainControls"]["float"]:
        for i, control in enumerate(splineDict["mainControls"]["float"]):
            cmds.addAttr(messageManager, longName="floatCtrl_{}".format(i), attributeType='message')
            cmds.connectAttr('{}.message'.format(control), '.'.join([messageManager, "floatCtrl_{}".format(i)]))
    # create/connect revFk attributes
    if splineDict["mainControls"]["revFk"]:
        for i, control in enumerate(splineDict["mainControls"]["revFk"]):
            cmds.addAttr(messageManager, longName="revFkCtrl_{}".format(i), attributeType='message')
            cmds.connectAttr('{}.message'.format(control), '.'.join([messageManager, "revFkCtrl_{}".format(i)]))
    # create connect spine attributes
    if splineDict["mainControls"]["spine"]:
        for i, control in enumerate(splineDict["mainControls"]["spine"]):
            cmds.addAttr(messageManager, longName="spineCtrl_{}".format(i), attributeType='message')
            cmds.connectAttr('{}.message'.format(control), '.'.join([messageManager, "spineCtrl_{}".format(i)]))
        # create/connect spine midRot control attribute
        cmds.addAttr(messageManager, longName="spineMidCtrl", attributeType='message')
        cmds.connectAttr('{}.message'.format(splineDict["spineRotControl"][1]),
                         '.'.join([messageManager, "spineMidCtrl"]))
    # lock messageNodeManager
    cmds.lockNode(messageManager, l=True)


class rigGeneric(object):
    def __init__(self, rigName, jointList=[], root='root_ctrl'):
        """
        Genric rig class, mostly used for controls, could be just functions. Might change later.
        Should take out joint list requirement too.
        """
        self.rigName = rigName
        self.jointList = jointList
        self.root = root


class rigSpline(rigGeneric):
    """
    The base class for building spline rigs.
    buildControls() Currently defaults to an ik spline with clusters to floating controls.
    Sub classes modify the control setups to be fk, reverse fk or spline.
    These different part types can be combined in various ways via functions.
    Can later add other functionality like dual fk ik, ribbon support etc.
    """

    def __init__(self, *args, **kwargs):
        super(rigSpline, self).__init__(*args, **kwargs)

    def clusterCurve(self, curveName):
        """
        Creates clusters on the CVs of a given curve
        :param curveName: string
        :param clusterName: string
        :return: list of clusters
        """
        clusterName = ('{}_cluster'.format(self.rigName))
        returnCV = []
        cmds.select('{}.cv[*]'.format(curveName), r=1)
        cvs = cmds.ls(selection=True)
        rf = cvs[0].rfind(':')
        lenCVs = len(cvs[0])
        number = int(cvs[0][(rf + 1):(lenCVs - 1)])
        cvName = cvs[0][0:rf - 2]
        clusterList = []
        for i in range(0, number + 1, 1):
            returnCV.append(str(cvName) + '[' + str(i) + ']')
            c = cmds.cluster(str(curveName) + '.cv[' + str(i) + ']')
            nn = cmds.rename(c[1], clusterName + str(i + 1))
            clusterList.append(nn)
        return clusterList

    def createSplineIkClusters(self, curveSpans=2, longName=False):
        '''
        Creates spline ik with given curve spans and puts clusters on the curve
        :param jointlist:
        :param globalSpineName:
        :param curveSpans:
        :return: SplineIk List and clusterList
        '''
        # create spline ik
        name = namehandling.nonUniqueNameNumber("{}_splineIkhandle".format(self.rigName))
        splineIkList = cmds.ikHandle(name=name, sj=self.jointList[0], ee=self.jointList[-1], solver='ikSplineSolver',
                                     numSpans=curveSpans)
        splineSolver = cmds.ikHandle(splineIkList[0], q=True, sol=True)
        # name curve
        name = namehandling.nonUniqueNameNumber("{}_ikSplineCurve".format(self.rigName))
        splineIkList[2] = cmds.rename(splineIkList[2], name)
        # name effector
        name = namehandling.nonUniqueNameNumber("{}_splineIkEffector".format(self.rigName))
        splineIkList[1] = cmds.rename(splineIkList[1], name)
        # create clusters
        clusterList = self.clusterCurve(splineIkList[2])
        # build fk controls
        if longName:  # return the long name of all DAG nodes
            splineIkList = cmds.ls(splineIkList, long=True)
            clusterList = cmds.ls(clusterList, long=True)
        return splineIkList, clusterList, splineSolver

    def buildControls(self, splineDict, partname="fk", scale=1.0, curveScale=1.0, curveColor="orange",
                      controlType='sphere'):
        """
        Builds controls for the clusters.  Default is floating and controls aren't parented,
        see child classes for other options like spine setup and fk and rev fk.
        """
        controlList = []
        groupList = []
        for i, cluster in enumerate(splineDict["clusters"]):
            clusterNo = str(i + 1)
            # create control curves
            control, group = self.controlCurveBuild('_'.join([self.rigName, partname, 'ctrl', clusterNo]),
                                                    cluster, group=True, curveScale=(scale * curveScale),
                                                    controlType=controlType, curveColor=curveColor)
            controlList.append(control)
            groupList.append(group)
        # parent
        controlList, groupList = self.parentControls(controlList, groupList)  # this overrides in each class
        # and add the list to an ordered dict
        if partname == "floatSecondary":  # this is special if the type is the floating
            splineDict["secondarySrts"] = groupList
            splineDict["secondaryCntrls"] = controlList
        else:  # otherwise normal controls
            splineDict["mainControlSrts"][partname] = groupList
            splineDict["mainControls"][partname] = controlList
        return (splineDict)

    def parentControls(self, controlList, groupList):
        """
        pass by design for floating style (the default) controls, see child classes for other options
        """
        return controlList, groupList

    def cleanupControls(self, objList, parentObj, longName=True):
        """
        takes each group and if in world parent to the given group
        """
        pass  # depricated

    def createSplineBase(self, controls=5, longName=False):
        """
        creates the spline base, the spline, spline ik and clusters, also cleanup grps
        """
        if 4 <= controls <= 9:  # maya can't build other default curves/cvs, unless you rebuild the curve
            curveSpans = controls - 3  # maya creates extra cvs so -3
            # build spline and clusters
            splineIkList, clusterList, splineSolver = self.createSplineIkClusters(curveSpans=curveSpans)
            # Create Cleanup Groups
            name = namehandling.nonUniqueNameNumber("{}_rig_grp".format(self.rigName))
            rigGrp = cmds.group(em=True, n=name)
            name = namehandling.nonUniqueNameNumber("{}_spline_grp".format(self.rigName))
            splineGrp = cmds.group(em=True, p=rigGrp, n=name)
            name = namehandling.nonUniqueNameNumber("{}_controls_grp".format(self.rigName))
            controlsGrp = cmds.group(em=True, p=rigGrp, n=name)
            name = namehandling.nonUniqueNameNumber("{}_cluster_grp".format(self.rigName))
            clusterGrp = cmds.group(em=True, p=rigGrp, n=name)
            cmds.setAttr('{}.visibility'.format(splineGrp), 0, lock=1)
            cmds.setAttr('{}.inheritsTransform'.format(splineGrp), 0)
            # Parent Spline and Clusters
            for i, obj in enumerate(splineIkList):
                if i != 1:  # filter the effector
                    splineIkList[i] = (cmds.parent(obj, splineGrp))[0]
            clusterList = (cmds.parent(clusterList, splineGrp))
            if longName:
                rigGrp = (cmds.ls(rigGrp, long=True))[0]
                splineGrp = (cmds.ls(splineGrp, long=True))[0]
                controlsGrp = (cmds.ls(controlsGrp, long=True))[0]
                clusterGrp = (cmds.ls(clusterGrp, long=True))[0]
                splineIkList = cmds.ls(splineIkList, long=True)
                clusterList = cmds.ls(clusterList, long=True)
            return splineIkList, splineSolver, clusterList, rigGrp, splineGrp, controlsGrp, clusterGrp
        else:
            # should add in rebuild curve options here
            om2.MGlobal.displayError('Maya Spline IK only takes between 4 and 9 controls')


class rigSplineFKPart(rigSpline):
    """
    overrides the spline parentControls() method so the controls build fk.
    """

    def __init__(self, *args, **kwargs):
        super(rigSplineFKPart, self).__init__(*args, **kwargs)

    def parentControls(self, controlList, groupList):
        controlList, groupList = parentfk.parentGroupControls(controlList, groupList)
        return controlList, groupList


class rigSplineRevFKPart(rigSpline):
    """
    overrides the spline parentControls() method so the controls build reverse fk.
    """

    def __init__(self, *args, **kwargs):
        super(rigSplineRevFKPart, self).__init__(*args, **kwargs)

    def parentControls(self, controlList, groupList):
        controlList, groupList = parentfk.parentGroupControls(controlList, groupList, reverse=True)
        controlList.reverse()
        groupList.reverse()
        return controlList, groupList


class rigSpinePart(rigSpline):
    """
    overrides the spline buildControls() method so the controls build as per a spine setup
    overrides the spline parentControls() method for the spine build
    """

    def __init__(self, *args, **kwargs):
        super(rigSpinePart, self).__init__(*args, **kwargs)

    def buildControls(self, splineDict, partname="fk", scale=1.0, curveScale=1.0,
                      curveColor="orange", controlType='sphere', parentControls=True, longName=True):
        """
        Overides the spline base class, alters the controls to be different shapes and sizes, names vary too.
        Returns the same dictionary
        """
        spineControlList = []
        spineGroupList = []
        controlStartEnd = 'cube'
        controlMid = 'cube'
        controlRotMid = 'sphere'
        # start 0
        name = "{}_start_ctrl".format(self.rigName)
        cntrlScale = scale * curveScale * 2.0
        cntrl, grp = controls.controlBuildGrouped(name, splineDict["clusters"][0], curveScale=cntrlScale,
                                            controlType=controlStartEnd, curveColor=curveColor, group=True)
        spineControlList.append(cntrl)
        spineGroupList.append(grp)
        # cluster bottom 1
        name = "{}_clusterBot_ctrl".format(self.rigName)
        cntrlScale = scale * curveScale / 3.0
        cntrl, grp = controls.controlBuildGrouped(name, splineDict["clusters"][1], curveScale=cntrlScale,
                                            controlType=controlType, curveColor=curveColor, group=True)
        spineControlList.append(cntrl)
        spineGroupList.append(grp)
        # mid 2
        name = "{}_mid_ctrl".format(self.rigName)
        cntrlScale = scale * curveScale
        cntrl, grp = controls.controlBuildGrouped(name, splineDict["clusters"][2], curveScale=cntrlScale,
                                            controlType=controlMid, curveColor=curveColor, group=True)
        spineControlList.append(cntrl)
        spineGroupList.append(grp)
        # cluster top 3
        name = "{}_clusterTop_ctrl".format(self.rigName)
        cntrlScale = scale * curveScale / 3.0
        cntrl, grp = controls.controlBuildGrouped(name, splineDict["clusters"][3], curveScale=cntrlScale,
                                            controlType=controlType, curveColor=curveColor, group=True)
        spineControlList.append(cntrl)
        spineGroupList.append(grp)
        # end 4
        name = "{}_end_ctrl".format(self.rigName)
        cntrlScale = scale * curveScale * 2.0
        cntrl, grp = controls.controlBuildGrouped(name, splineDict["clusters"][-1], curveScale=cntrlScale,
                                            controlType=controlStartEnd, curveColor=curveColor, group=True)
        spineControlList.append(cntrl)
        spineGroupList.append(grp)
        # parent controls
        spineControlList, spineGroupList = self.parentControls(spineControlList, spineGroupList)

        # build extra controls setup, constraints extra controls etc
        # build mid constraint
        endControl = spineControlList[4]
        startControl = spineControlList[0]
        midControlGrp = spineGroupList[2]
        constraintList = [startControl, endControl, midControlGrp]
        otherConstraintList = list()
        otherConstraintList.append((cmds.parentConstraint(constraintList, maintainOffset=1))[0])

        # build rotMid control
        name = "{}_rotMid_ctrl".format(self.rigName)
        cntrlScale = scale * curveScale * 1.0
        cntrl, grp = self.controlCurveBuild(name, spineControlList[2], curveScale=cntrlScale,
                                            controlType=controlRotMid, curveColor=curveColor, group=True)
        extraSpineControl = [grp, cntrl]

        # parent midControlGrp to extraSpineControl
        cmds.parent(midControlGrp, extraSpineControl[1])

        # constrain the startControlGrp to extraSpineControl
        constraintList = [extraSpineControl[1], spineGroupList[0]]
        otherConstraintList.append((cmds.parentConstraint(constraintList, maintainOffset=1))[0])

        # save controls and grps to dictionary
        splineDict["mainControls"]["spine"] = spineControlList
        splineDict["mainControlSrts"]["spine"] = spineGroupList
        splineDict["spineExtraConstraints"] = otherConstraintList
        splineDict["spineRotControl"] = extraSpineControl
        return (splineDict)

    def parentControls(self, controlList, groupList, longName=False):
        """
        overrides the spline method so the controls build as per the spine variation
        """
        for i, control in enumerate(controlList):
            if i == 1:
                groupList[i] = (cmds.parent(groupList[i], controlList[0]))[0]
            elif i == (len(controlList) - 2):
                groupList[i] = (cmds.parent(groupList[i], controlList[len(controlList) - 1]))[0]
        if longName:
            controlList = cmds.ls(controlList, long=True)
            groupList = cmds.ls(groupList, long=True)
        return controlList, groupList


def jointStretchMultiplySetup(joints, curveInfo, splineCurve):
    """Sets up the "stretch" part of a squash/stretch component for a regular spline ik chain
    Returns a blend node (and multiplyDivideA) which can blend between the stretch and the non stretch modes
    The blend node attribute should later be hooked up to the controls

    """
    # create multiplyDivide math node with settings
    name = namehandling.nonUniqueNameNumber('{}_multiplyDivideA'.format(splineCurve))  # unique name
    splineMultiplyNode = cmds.createNode('multiplyDivide', n=name)
    cmds.setAttr('{}.input2X'.format(splineMultiplyNode), len(joints) - 1)  # divide by number of joints
    cmds.setAttr('{}.operation'.format(splineMultiplyNode), 2)  # set to divide
    cmds.connectAttr('{}.arcLength'.format(curveInfo), '{}.input1X'.format(splineMultiplyNode))
    # The no scale initial value for no stretch (curve length / joint count)
    cmds.setAttr('{}.input1Z'.format(str(splineMultiplyNode)),
                 cmds.getAttr('{}.arcLength'.format(str(curveInfo))) / len(joints))
    # stretch blend setup
    name = namehandling.nonUniqueNameNumber('{}_stretchBlendTwoAttr'.format(splineCurve))  # unique name
    splineStretchBlendTwoAttr = cmds.createNode('blendTwoAttr', n=name)
    cmds.connectAttr('{}.outputX'.format(splineMultiplyNode),
                     '{}.input[1]'.format(splineStretchBlendTwoAttr))  # stretch
    cmds.connectAttr('{}.input1Z'.format(splineMultiplyNode),
                     '{}.input[0]'.format(splineStretchBlendTwoAttr))  # no stretch
    cmds.setAttr('{}.attributesBlender'.format(splineStretchBlendTwoAttr), 1)
    for jnt in joints:  # connect blend to all joints on trans x
        cmds.connectAttr('{}.output'.format(splineStretchBlendTwoAttr), '{}.translateX'.format(jnt))
    return splineMultiplyNode, splineStretchBlendTwoAttr


def jointSquashMultiplySetup(joints, splineCurve, curveInfo, splineMultiplyNode):
    """Sets up the stretch part of a squash/stretch component for a regular spline ik chain
    Returns a blend node (and multiplyDivideB) which can blend between the stretch and the non stretch modes
    also builds and returns the curve info node for measuring the length of the spline curve
    The blend node attribute should later be hooked up to the controls

    """
    cmds.connectAttr('{}.arcLength'.format(curveInfo), '{}.input1Y'.format(splineMultiplyNode))
    cmds.setAttr('{}.input2Y'.format(splineMultiplyNode), cmds.getAttr('{}.arcLength'.format(curveInfo)))
    name = namehandling.nonUniqueNameNumber('{}_multiplyDivideB'.format(splineCurve))  # unique name
    splineMultiplyNode2 = cmds.createNode('multiplyDivide', n=name)
    cmds.connectAttr('{}.outputY'.format(splineMultiplyNode), '{}.input2Y'.format(splineMultiplyNode2))
    cmds.setAttr('{}.input1Y'.format(splineMultiplyNode2), 1)
    cmds.setAttr('{}.operation'.format(splineMultiplyNode2), 2)  # set to divide
    # no scale value
    cmds.setAttr('{}.input1Z'.format(splineMultiplyNode2), 1)
    # squash blend setup
    name = namehandling.nonUniqueNameNumber('{}_squashBlendTwoAttr'.format(splineCurve))
    splineSquashBlendTwoAttr = cmds.createNode('blendTwoAttr', n=name)
    cmds.connectAttr('{}.outputY'.format(splineMultiplyNode2), '{}.input[1]'.format(splineSquashBlendTwoAttr))  # squash
    cmds.connectAttr('{}.input1Z'.format(splineMultiplyNode2),
                     '{}.input[0]'.format(splineSquashBlendTwoAttr))  # no squash
    cmds.setAttr('{}.attributesBlender'.format(splineSquashBlendTwoAttr), 1)
    for jnt in joints:
        cmds.connectAttr('{}.output'.format(splineSquashBlendTwoAttr), '{}.scaleY'.format(jnt))
        cmds.connectAttr('{}.output'.format(splineSquashBlendTwoAttr), '{}.scaleZ'.format(jnt))
    return splineSquashBlendTwoAttr, splineMultiplyNode2


def createStretchy(splineCurve, joints):
    """Builds the squash and stretch setup for regular spline ik
    Returns the  splineDict with new entries...
    :sqshStrchMults, :squashBlendTwo, :stretchBlendTwo, :curveInfo
    The blend nodes are needed for later setup when assigning attributes to the controls (.attributesBlender attrs)
    Squash and Stretch can be mixed/multiplied independently
    Returned nodes
    curveInfo: node to measure the length of a curve
    splineMultiplyNode: multiplies to find the offset for x (length joints)
    TO DO
    - Add compatiblity for only squash or only stretch
    - Add compatibility for joint changes with non uniform lengths. Right now joint
    chains must have even translate x values

    :param splineCurve:
    :type splineCurve:
    :param joints:
    :type joints:
    :return nodeTuple: tuple of nodes returned in the building of the squash and stretch
    :rtype nodeTuple: tuple
    """
    # create curve info node for measuring length of curve
    curveInfo = cmds.arclen(splineCurve, ch=True)
    # stretch setup
    splineMultiplyNode, splineStretchBlendTwoAttr = jointStretchMultiplySetup(joints, curveInfo, splineCurve)
    # squash setup
    splineSquashBlendTwoAttr, splineMultiplyNode2 = jointSquashMultiplySetup(joints, splineCurve, curveInfo,
                                                                             splineMultiplyNode)
    return (curveInfo, splineMultiplyNode, splineMultiplyNode2, splineStretchBlendTwoAttr, splineSquashBlendTwoAttr)


def stretchyConnectCntrlAttributes(stretchBlend, squashBlend, controlObj):
    cmds.addAttr(controlObj, longName='squash', attributeType='float',
                 keyable=1, defaultValue=1)
    cmds.addAttr(controlObj, longName='stretch', attributeType='float',
                 keyable=1, defaultValue=1)
    cmds.connectAttr('{}.squash'.format(controlObj), '{}.attributesBlender'.format(squashBlend))
    cmds.connectAttr('{}.stretch'.format(controlObj), '{}.attributesBlender'.format(stretchBlend))


def createStretchyDict(splineDict):
    """Same function as createStretchy(), only compatible with the splineDict dictionary

    :param splineDict: main dict used in the spline rig
    :type splineDict: dict
    :return splineDict: Dictionary now updated with the 5 nodes created by createStretchy()
    :rtype splineDict: dict
    """
    # get spline curve and jointList
    splineCurve = (splineDict["splineIkParts"])[-1]
    joints = splineDict["joints"]
    # do stretchy
    curveInfo, splineMultiplyNode, splineMultiplyNode2, splineStretchBlendTwoAttr, splineSquashBlendTwoAttr = createStretchy(
        splineCurve, joints)
    # save values to dict
    splineDict["squashBlendTwo"] = splineSquashBlendTwoAttr
    splineDict["stretchBlendTwo"] = splineStretchBlendTwoAttr
    splineDict["sqshStrchMults"] = [splineMultiplyNode, splineMultiplyNode2]
    splineDict["curveInfo"] = curveInfo
    return splineDict


def splineDictSetup():
    """
    Creates an empty dict with potential objects (dag nodes) of the spine.
    Main controls and their sorts are in nested dicts.
    Keys can be strings, lists, or dicts. Keys could be added later but here it's easier to track

    :return splineDict: The dictionary with empty keys
    :type splineDict: dict
    """
    splineDict = dict.fromkeys(['mainGrp', 'splineIkGrp', 'splineIkParts', 'clusters', 'clusterCnsts', 'joints',
                                'clusterGrp', 'controlsGrp', 'mainControls', 'mainControlSrts', 'secondaryCntrls',
                                'secondarySrts', 'secondaryCnsts', 'squashBlendTwo', 'stretchBlendTwo',
                                'sqshStrchMults', 'curveInfo', 'splineSolver', 'hchySwitchCondVis', 'jointSpacing',
                                'hchySwitchCondPnts', 'spineExtraConstraints', 'spineRotControl', 'messageNodeManager'])
    splineDict['mainControls'] = dict.fromkeys(['fk', 'spine', 'revFk', 'float'])  # nested dict
    splineDict['mainControlSrts'] = dict.fromkeys(['fk', 'spine', 'revFk', 'float'])  # nested dict
    return splineDict


def displaySplineParts(splineDict):
    """
    Displays the dicts splineDict and splineDict to return readable list of returns
    """
    om2.MGlobal.displayInfo('*******' * 8)
    om2.MGlobal.displayInfo('DAG NODES')
    om2.MGlobal.displayInfo('*******' * 8)
    om2.MGlobal.displayInfo(' '.join(['mainGrp:', str(splineDict['mainGrp'])]))
    om2.MGlobal.displayInfo(' '.join(['splineIkGrp:', str(splineDict['splineIkGrp'])]))
    om2.MGlobal.displayInfo(' '.join(['splineIkParts:', str(splineDict['splineIkParts'])]))
    om2.MGlobal.displayInfo(' '.join(['clusters:', str(splineDict['clusters'])]))
    om2.MGlobal.displayInfo(' '.join(['clusterCnsts:', str(splineDict['clusterCnsts'])]))
    om2.MGlobal.displayInfo(' '.join(['clusterGrp:', str(splineDict['clusterGrp'])]))
    om2.MGlobal.displayInfo(' '.join(['controlsGrp:', str(splineDict['controlsGrp'])]))
    om2.MGlobal.displayInfo(' '.join(['secondaryCntrls:', str(splineDict['secondaryCntrls'])]))
    om2.MGlobal.displayInfo(' '.join(['secondarySrts:', str(splineDict['secondarySrts'])]))
    om2.MGlobal.displayInfo(' '.join(['secondaryCnsts:', str(splineDict['secondaryCnsts'])]))
    om2.MGlobal.displayInfo('*******' * 8)
    om2.MGlobal.displayInfo(' '.join(['mainControls fk:', str(splineDict['mainControls']['fk'])]))
    om2.MGlobal.displayInfo(' '.join(['mainControls spine:', str(splineDict['mainControls']['spine'])]))
    om2.MGlobal.displayInfo(' '.join(['mainControls revFk:', str(splineDict['mainControls']['revFk'])]))
    om2.MGlobal.displayInfo(' '.join(['mainControls float:', str(splineDict['mainControls']['float'])]))
    om2.MGlobal.displayInfo('*******' * 8)
    om2.MGlobal.displayInfo(' '.join(['mainControlSrts fk:', str(splineDict['mainControlSrts']['fk'])]))
    om2.MGlobal.displayInfo(' '.join(['mainControlSrts spine:', str(splineDict['mainControlSrts']['spine'])]))
    om2.MGlobal.displayInfo(' '.join(['mainControlSrts revFk:', str(splineDict['mainControlSrts']['revFk'])]))
    om2.MGlobal.displayInfo(' '.join(['mainControlSrts float:', str(splineDict['mainControlSrts']['float'])]))
    om2.MGlobal.displayInfo(' '.join(['spineRotControl:', str(splineDict['spineRotControl'])]))
    om2.MGlobal.displayInfo(' '.join(['spineExtraConstraints:', str(splineDict['spineExtraConstraints'])]))
    om2.MGlobal.displayInfo('*******' * 8)
    om2.MGlobal.displayInfo('OTHER NODES')
    om2.MGlobal.displayInfo('*******' * 8)
    om2.MGlobal.displayInfo(' '.join(['jointSpacing:', str(splineDict['jointSpacing'])]))
    om2.MGlobal.displayInfo(' '.join(['squashBlendTwo:', str(splineDict['squashBlendTwo'])]))
    om2.MGlobal.displayInfo(' '.join(['stretchBlendTwo:', str(splineDict['stretchBlendTwo'])]))
    om2.MGlobal.displayInfo(' '.join(['sqshStrchMults:', str(splineDict['sqshStrchMults'])]))
    om2.MGlobal.displayInfo(' '.join(['curveInfo:', str(splineDict['curveInfo'])]))
    om2.MGlobal.displayInfo(' '.join(['splineSolver:', str(splineDict['splineSolver'])]))
    om2.MGlobal.displayInfo(' '.join(['hchySwitchCondVis:', str(splineDict['hchySwitchCondVis'])]))
    om2.MGlobal.displayInfo(' '.join(['hchySwitchCondPnts:', str(splineDict['hchySwitchCondPnts'])]))
    om2.MGlobal.displayInfo(' '.join(['messageNodeManager:', str(splineDict['messageNodeManager'])]))


def connectMultipleSplineParts(splineDict, rigName, switchAttrObject, switchAttrName='hierarchySwitch',
                               secondaryVisAttrName='secondaryVis', primaryVisAttrName='primaryVis', stretchy=True):
    """
    Connects all the spline controls together sets up the switch attributes and constraints depending on the settings
    Also vis switch for hiding the primary and secondary controls
    """
    if splineDict['secondarySrts']:  # constrain to the floatSecondary controls
        splineDict["clusterCnsts"] = list()
        # ----------------------------
        # Sets up the clusters to follow the secondary float controls
        # ----------------------------
        constrainToList = splineDict['secondarySrts']  # float secondary control groups
        secondaryControlList = splineDict['secondaryCntrls']  # controls
        for i, cluster in enumerate(splineDict["clusters"]):  # constrain clusters
            constraints = [secondaryControlList[i], cluster]
            name = namehandling.nonUniqueNameNumber('_ClusterConstraint_'.join([rigName, cluster]))
            constraintNm = (cmds.parentConstraint(constraints, maintainOffset=True, name=name))[0]
            splineDict["clusterCnsts"].append(constraintNm)
    else:
        # ----------------------------
        # clusters constrain to the main controls, constraints setup later
        # ----------------------------
        constrainToList = splineDict["clusters"]
    # constraint list and conditional node dicts
    objConstraintList = list()
    controlEnumList = list()
    # get list of the keys in mainControls for the drop down name list "controlEnumList"
    for key in splineDict["mainControls"].keys():
        if splineDict["mainControls"][key]:
            controlEnumList.append(key)
    if len(controlEnumList) > 1:  # create switch attribute as enum list
        driverAttr = attributes.createEnumAttributeFromList(controlEnumList, switchAttrObject, switchAttrName)
        driverAttr = driverAttr.split("|")[-1]
    # ----------------------------
    # create the constraints
    # ----------------------------
    # note:  The constraints will either constrain the clusters or the secondary controls
    # this depends whether the secondary controls have been built and is already factored in constrainToList
    for i, cnstrObj in enumerate(constrainToList):  # constrain to objects and create lists for the switching
        constraintObjList = list()
        for part in controlEnumList:  # part is fk, spine, float, rev etc
            # get existing controls for this cluster
            constraintObjList.append(splineDict["mainControls"][part][i])
        constraintObjList.append(cnstrObj)  # last to append is the target object with the constraint
        # constrain to object
        name = namehandling.nonUniqueNameNumber('{}_PointConstraint_{}'.format(rigName, str(i + 1)))
        constraintNm = (cmds.parentConstraint(constraintObjList, maintainOffset=True,
                                              name=name))[0]
        objConstraintList.append(constraintNm)
    if len(controlEnumList) != 1:  # if more than 1 set of controls do switching
        # ----------------------------
        # setup condition node switching for constraints and vis
        # ----------------------------
        splineDict["hchySwitchCondPnts"] = list()
        splineDict["hchySwitchCondVis"] = list()
        for x, part in enumerate(controlEnumList):
            constraintList = list()
            visAttrList = list()
            for i, control in enumerate(splineDict["mainControls"][part]):  # loop through controls
                controlGrpName = splineDict["mainControlSrts"][part][i]
                constraintList.append(''.join([(objConstraintList[i]), '.', str(control), 'W', str(x)]))
                visAttrList.append('{}.visibility'.format(controlGrpName))
            splineDict["hchySwitchCondPnts"].append(nodes.conditionMulti(driverAttr, constraintList, x, suffix=rigName))
            splineDict["hchySwitchCondVis"].append(nodes.conditionMulti(driverAttr, visAttrList, x, suffix=rigName))
    # ----------------------------
    # visibility of main and secondary controls
    # ----------------------------
    cmds.addAttr(switchAttrObject, longName=primaryVisAttrName, attributeType='bool', keyable=0, defaultValue=1)
    cmds.setAttr('.'.join([str(switchAttrObject), str(primaryVisAttrName)]), channelBox=1)
    # hookup attributes to vis of the primary and secondary controls
    for i, part in enumerate(controlEnumList):
        # primary controls vis connect
        for control in splineDict["mainControls"][part]:  # loop through controls
            cmds.connectAttr('.'.join([str(switchAttrObject), str(primaryVisAttrName)]),
                             '{}.visibility'.format(control))
            cmds.setAttr('{}.visibility'.format(control), keyable=False)
    if splineDict["secondaryCntrls"]:
        # secondary controls vis connect
        cmds.addAttr(switchAttrObject, longName=secondaryVisAttrName, attributeType='bool',
                     keyable=0, defaultValue=0)
        cmds.setAttr('.'.join([str(switchAttrObject), str(secondaryVisAttrName)]), channelBox=1)
        for control in splineDict["secondaryCntrls"]:
            cmds.connectAttr('.'.join([str(switchAttrObject), str(secondaryVisAttrName)]),
                             '{}.visibility'.format(control))
            cmds.setAttr('{}.visibility'.format(control), keyable=False)
        splineDict["secondaryCnsts"] = objConstraintList
    else:
        splineDict["clusterCnsts"] = objConstraintList
    # ----------------------------
    # setup squash and stretch attributes on the switchAttrObject
    # ----------------------------
    if stretchy:
        stretchyConnectCntrlAttributes(splineDict["stretchBlendTwo"], splineDict["squashBlendTwo"], switchAttrObject)
    # ----------------------------
    # create messageNodeManager node
    # ----------------------------
    messageNodeManager = cmds.createNode("network", n="{}_messageNodeManager".format(rigName))
    # connect with message node
    cmds.addAttr(switchAttrObject, longName="messageNodeManager", attributeType='message')
    cmds.connectAttr('{}.message'.format(messageNodeManager), '.'.join([switchAttrObject, "messageNodeManager"]))
    splineDict["messageNodeManager"] = messageNodeManager
    return splineDict


def advancedSplineIkTwist(splineIk, objStart, objectEnd, startVector=(0, 0, -1), endVector=(0, 0, -1)):
    """
    Sets up advanced ik twist on existing splineIK handle
    Currently obj rot up start and end

    :param splineIk: splineIk handle
    :param objStart: first obj for twist
    :param objectEnd: second obj for twist
    :param startVector: (0,0,1) start up vector
    :param endVector: (0,0,1) end up vector
    """
    cmds.setAttr("{}.dTwistControlEnable".format(splineIk), 1)  # advanced on
    cmds.setAttr("{}.dWorldUpType".format(splineIk), 4)  # obj rot up start/end
    # start/end objects
    cmds.connectAttr("{}.xformMatrix".format(objStart), "{}.dWorldUpMatrix".format(splineIk), force=True)
    cmds.connectAttr("{}.xformMatrix".format(objectEnd), "{}.dWorldUpMatrixEnd".format(splineIk), force=True)
    # start/end vectors
    cmds.setAttr("{}.dWorldUpVectorX".format(splineIk), startVector[0])
    cmds.setAttr("{}.dWorldUpVectorY".format(splineIk), startVector[1])
    cmds.setAttr("{}.dWorldUpVectorZ".format(splineIk), startVector[2])
    cmds.setAttr("{}.dWorldUpVectorEndX".format(splineIk), endVector[0])
    cmds.setAttr("{}.dWorldUpVectorEndY".format(splineIk), endVector[1])
    cmds.setAttr("{}.dWorldUpVectorEndZ".format(splineIk), endVector[2])


def buildTestSkeleton(jointCount=20, buildRefCubes=True, worldUpVector=[0, 0, 1], suffixName="spine", jntName="joint"):
    """Builds a test skeleton for the spine 20 units high

    :param jointCount: The number of joints
    :type jointCount: int
    :param buildRefCubes: Build cubes on the joints for testing?
    :type buildRefCubes: bool
    :param worldUpVector: The up vector for the joints
    :type worldUpVector: tuple
    :param suffixName: name of the suffix on all joints and cubes
    :type suffixName: str
    :param jntName: the name of the joint part of the name
    :type jntName: str
    :return jointList: The joints names in a list
    :rtype jointList: list
    :return cubeList: the mesh cubes names in a list
    :rtype cubeList: list
    """
    startPosition = [0, 0, 0]
    endPosition = [0, 20, 0]
    jointList, jointSpacing = joints.buildJointTwoPoints(startPosition, endPosition, jointCount=jointCount,
                                                         worldUpVector=worldUpVector, suffixName=suffixName,
                                                         jntName=jntName)
    if buildRefCubes:  # this is for testing
        cubeList = mesh.createPrimitiveFromList(jointList, type="cube", message=False, scale=1.0)
        return jointList, cubeList, jointSpacing
    return jointList, None, jointSpacing


def buildSpineRig(jointList, jointSpacing, spine=True, fk=True, revFk=True, float=True,
                  floatSecondary=True, controls=5,
                  rigName='spine', stretchy=True, report=True):
    """
    Main function that builds the spline calling the other functions and classes

    :param jointList:
    :param spine:
    :param fk:
    :param revFk:
    :param float:
    :param floatSecondary:
    :param controls:
    :param rigName:
    :param stretchy:
    :return:
    """
    splineDict = splineDictSetup()
    rigSplinePartInstance = rigSpline(rigName, jointList=jointList)
    # ------------------
    # create base spline base, splines and clusters, cleanup groups
    # ------------------
    splineIkList, splineSolver, clusterList, rigGrp, splineGrp, controlsGrp, clusterGrp = rigSplinePartInstance.createSplineBase(
        controls=controls)
    # ------------------
    # setup dictionaries for keeping track of objects
    # ------------------
    splineDict['joints'] = jointList
    splineDict['jointSpacing'] = jointSpacing
    splineDict['splineIkParts'] = splineIkList
    splineDict['splineSolver'] = splineSolver
    splineDict['clusters'] = clusterList
    splineDict['mainGrp'] = rigGrp
    splineDict['splineIkGrp'] = splineGrp
    splineDict['clusterGrp'] = clusterGrp
    splineDict['controlsGrp'] = controlsGrp
    # ------------------
    # build stretchy setup
    # ------------------
    if stretchy:  # create stretchy
        splineDict = createStretchyDict(splineDict)
    # ------------------
    # setup the spline twist
    # ------------------
    # attributes to send are: splineIk, objStart, objectEnd
    advancedSplineIkTwist(splineDict["splineIkParts"][0], splineDict["clusters"][0], splineDict["clusters"][-1])
    # ------------------
    # build control setups, various parts of the spline rig
    # ------------------
    if spine:  # build
        spineRigPartInstance = rigSpinePart(rigName, jointList=jointList)
        splineDict = spineRigPartInstance.buildControls(splineDict, partname="spine", curveColor="green")
    if fk:  # build
        rigSplineFKPartInstance = rigSplineFKPart(rigName, jointList=jointList)
        splineDict = rigSplineFKPartInstance.buildControls(splineDict, partname="fk", curveColor="blue",
                                                           curveScale=1.2)
    if float:  # build
        splineDict = rigSplinePartInstance.buildControls(splineDict, partname="float")
    if revFk:  # build
        rigSplineRevFKPartInstance = rigSplineRevFKPart(rigName, jointList=jointList)
        splineDict = rigSplineRevFKPartInstance.buildControls(splineDict, partname="revFk", curveColor="orange",
                                                              curveScale=.8)
    # ------------------
    # build float secondary a special floating style that follows main controls
    # ------------------
    if floatSecondary:  # build
        splineDict = rigSplinePartInstance.buildControls(splineDict, curveScale=0.2, partname="floatSecondary",
                                                         curveColor="peach")
    # ------------------
    # connect up all the spline parts with switching, stretchy, vis attributes, control cleanup
    # ------------------
    splineDict = connectMultipleSplineParts(splineDict, rigName, rootControl, stretchy=stretchy)
    # ------------------
    # create the dict attributes for obj tracking and switching
    # ------------------
    # createMessageConnectionsFromDict(rootControl, splineDict, 'controlDict')
    createMessageNodeSetupSpline(splineDict)
    # createMessageConFromDictFlat(rootControl, splineDict)

    # ------------------
    # success message
    # ------------------
    if report:
        displaySplineParts(splineDict)
    om2.MGlobal.displayInfo('Success: Spline rig built')


def buildNew(spine=True, fk=True, revFk=True, float=True, floatSecondary=True, controls=5, buildRefCubes=True,
             jointChainCount=20, stretchy=True):
    """
    Main Spline Build function run from UI or maya button
    """
    # build skeleton
    jointList, cubeList, jointSpacing = buildTestSkeleton()
    # build new spline rig
    if controls != 5 and spine == True:
        # error check if building the spine component which must have 5 controls
        om2.MGlobal.displayWarning('The spine component of the spline rig may only be built with 5 controls')
        return
    buildSpineRig(jointList, jointSpacing, spine=spine, fk=fk, revFk=revFk, float=float,
                  floatSecondary=floatSecondary,
                  controls=controls, stretchy=stretchy)
    return jointList, cubeList, jointSpacing


def retrieveSpineControlList(switchObj="root_ctrl"):
    """
    Gets the current spline mode (spine, fk, float or revFk) and retrieves all controls names if they exist
    This function is for spline switching not building

    :param switchObj: the main control with the switch attribute
    :type switchObj: str
    :return spineList: the spine control list
    :type spineList: list
    :return fkList: the fk control list
    :type fkList: list
    :return floatList: the float control list
    :type floatList: list
    :return revFkList: the revFk control list
    :type revFkList: list
    :return currentMode: The current spline mode, what controls are we currently seeing?
    :type currentMode: str
    """
    controlTypesList = list()
    # get the messageManager
    messageNodeManager = cmds.listConnections('{}.messageNodeManager'.format(switchObj))[0]
    # get the current mode
    currentMode = cmds.getAttr("{}.hierarchySwitch".format(switchObj))
    # list attributes on messageNodeManager and filter the one's we want
    fkList = cmds.listAttr(messageNodeManager, userDefined=True, string='fkCtrl_*')
    floatList = cmds.listAttr(messageNodeManager, userDefined=True, string='floatCtrl_*')
    revFkList = cmds.listAttr(messageNodeManager, userDefined=True, string='revFkCtrl_*')
    spineList = cmds.listAttr(messageNodeManager, userDefined=True, string='spineCtrl_*')
    # get actual objects
    if spineList:
        controlTypesList.append('spine')
        for i, attr in enumerate(spineList):
            spineList[i] = cmds.listConnections('.'.join([messageNodeManager, attr]))[0]
        spineMidRot = cmds.listConnections('{}.spineMidCtrl'.format(messageNodeManager))[0]
    if floatList:
        controlTypesList.append('float')
        for i, attr in enumerate(floatList):
            floatList[i] = cmds.listConnections('.'.join([messageNodeManager, attr]))[0]
    if fkList:
        controlTypesList.append('fk')
        for i, attr in enumerate(fkList):
            fkList[i] = cmds.listConnections('.'.join([messageNodeManager, attr]))[0]
    if revFkList:
        controlTypesList.append('revFk')
        for i, attr in enumerate(revFkList):
            revFkList[i] = cmds.listConnections('.'.join([messageNodeManager, attr]))[0]
    currentMode = controlTypesList[currentMode]
    return spineList, fkList, floatList, revFkList, spineMidRot, currentMode, controlTypesList


def switchToSplineMode(switchMode, spineList, fkList, floatList, revFkList, spineMidRot, currentMode,
                       controlTypesList, selObjs=None, switchObj="root_ctrl", selectControls=True):
    """
    Does the switching for the spline to a given mode 'spine', 'fk', 'float', 'revFk'

    :param switchMode: The spline mode to switch to, 'spine', 'fk', 'float', 'revFk'
    :type str:
    :param spineList: The spline list of controls
    :type list:
    :param fkList: The fk list of controls
    :type list:
    :param floatList: The floating list of controls
    :type list:
    :param revFkList: The fk list of controls
    :type list
    :param currentMode: What mode is the spline in now?
    :type str:
    :param controlTypesList: is a list of the type of controls that exist on the spline rig, fk, spine, revFk etc
    :type list:
    :param selObjs: The selected objects
    :type list:
    :param switchObj: The object that controls the spline
    :type string:
    :param selectControls: Should we select the matching control on the new set and deselect the old?
    :type bool:
    :return:
    """
    if currentMode == switchMode:  # bail if no change needed
        om2.MGlobal.displayInfo("Already in {} mode".format(switchMode))
        return

    # get current control list
    if currentMode == "spine":
        currentControlList = spineList
    elif currentMode == "fk":
        currentControlList = fkList
    elif currentMode == "float":
        currentControlList = floatList
    elif currentMode == "revFk":
        currentControlList = revFkList

    # get the match/switch to list
    if switchMode == "spine":
        switchControlList = spineList
    elif switchMode == "fk":
        switchControlList = fkList
    elif switchMode == "float":
        switchControlList = floatList
    elif switchMode == "revFk":
        switchControlList = revFkList
    else:
        om2.MGlobal.displayError("The switch mode %s isn't valid" % switchMode)
        return

    # create temp null (transforms) setup for orient aim info
    orientedNullList = switchOrientNulls(currentControlList, switchObj, currentMode, switchMode)

    # re order if needed otherwise match fails for switching to revFk and spine modes
    if switchMode == "revFk":  # if switching to reversFk then reverse the order
        switchControlList.reverse()
        orientedNullList.reverse()
        currentControlList.reverse()
    if switchMode == "spine":  # if switching to spine then items need shuffling for match due to parent order in spine
        newOrder = [0, 1, 4, 3, 2]
        currentControlList = [currentControlList[i] for i in newOrder]
        switchControlList = [switchControlList[i] for i in newOrder]
        orientedNullList = [orientedNullList[i] for i in newOrder]

    # do the match
    for i, null in enumerate(orientedNullList):
        align_utils.matchObjTransRot(switchControlList[i], null)  # match objs
    cmds.delete(orientedNullList)
    # get switch mode as number and switch to the new mode
    switchIndex = controlTypesList.index(switchMode)
    cmds.setAttr("{}.hierarchySwitch".format(switchObj), switchIndex)

    if selectControls:  # tgl the controls of the new switch set, and tgl off old
        selectedSwitch = set(selObjs).intersection(currentControlList)
        selectedSwitchList = list(selectedSwitch)
        # match get the indices of the original list
        selIndices = list()
        for i, obj in enumerate(selectedSwitchList):
            selIndices.append(currentControlList.index(obj))
        newObjSelection = [switchControlList[i] for i in selIndices]
        cmds.select(selectedSwitchList, tgl=1)
        cmds.select(newObjSelection, add=1)
    om2.MGlobal.displayInfo("Success: Spine swap matched {} to {}".format(currentMode, switchMode))


def switchOrientNulls(objList, switchObj, currentMode, switchMode):
    # create nulls
    nullList = list()
    for i, obj in enumerate(objList):
        nullList.append(cmds.group(name="tempNull_{}".format(i), empty=1, world=1))
        # match
        align_utils.matchObjTransRot(nullList[i], obj, skipZoo=True)
    # get the vector of the switchObj
    switchObjMatrix = cmds.xform(switchObj, worldSpace=True, matrix=True, query=True)
    # switchXVector = switchObjMatrix[:3]
    # switchYVector = switchObjMatrix[4:7]
    switchZVector = switchObjMatrix[8:11]
    # aim nulls at each other
    direction = 1.0
    for i, null in enumerate(nullList):
        if i + 1 == len(nullList):
            cmds.aimConstraint([nullList[i - 1], null], worldUpVector=switchZVector, upVector=(0.0, 0.0, 1.0),
                               aimVector=(0.0, direction * -1.0, 0.0), maintainOffset=False)
            continue
        # cmds.delete(cmds.aimConstraint()
        cmds.aimConstraint([nullList[i + 1], null], worldUpVector=switchZVector, upVector=(0.0, 0.0, 1.0),
                           aimVector=(0.0, direction, 0.0), maintainOffset=False)
    return nullList


def switchMatchSplineMode(switchMode, switchObj="root_ctrl", selectControls=True):
    """
    Main function for spline space switching.  Switch the spline to a mode can be...
    'spine', 'fk', 'float', 'revFk'

    :param switchMode: The spline mode to switch to, 'spine', 'fk', 'float', 'revFk'
    :type str:
    :param switchObj: The object that controls the spine
    :type str:
    :param selectControls: Do you want to select the equivalent spine controls after the switch?
    :type bool:
    :return:
    """
    selObjs = cmds.ls(sl=1)  # will select equivalent controls of new mode if selectControls=True
    # get obj lists and state info
    spineList, fkList, floatList, revFkList, \
    spineMidCtrl, currentMode, controlTypesList = retrieveSpineControlList(switchObj=switchObj)
    # switch and match
    switchToSplineMode(switchMode, spineList, fkList, floatList, revFkList, spineMidCtrl, currentMode, controlTypesList,
                       selObjs=selObjs, switchObj=switchObj, selectControls=selectControls)


if __name__ == "__main__":
    # builds the spine
    buildNew(spine=True, fk=True, revFk=True, float=True, floatSecondary=True, controls=5,
             buildRefCubes=True, jointChainCount=20, stretchy=True)
