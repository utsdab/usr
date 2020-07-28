"""
Example code:

    from zoo.libs.maya.cmds.rig import splinebuilder
    rigName = "rigX"
    jointList = ["joint1", "joint2","joint3", "joint4", "joint5", "joint6", "joint7", "joint8", "joint9"]
    splinebuilder.buildSpine(rigName, jointList, controlCount=5, scale=1.0)

"""

import maya.cmds as cmds
import maya.api.OpenMaya as om2

from zoo.libs.maya.cmds.objutils import joints
from zoo.libs.maya.cmds.rig import splines, deformers
from zoo.libs.maya.utils import general


class splineBuilder(object):
    """Main class that builds the spline rig with multiple control types and various switching functionality
    """

    def __init__(self, rigName, jointList, controlCount=5, scale=1.0, fk=True, revFk=True, flt=True, spine=True,
                 stretchy=True, cogUpAxis="+y", message=True):
        """The variables required for the spline rig builder

        :param rigName: the name of the rig part, this is the suffix so could be "spine", "ponyTail2" or "tail"
        :type rigName: str
        :param jointList: names of the joints
        :type jointList: list
        :param controlCount: the amount of controls you wish to build. Must be 5 for the spine controls
        :type controlCount: int
        :param scale: the overall scale of the rig as a multiplier, will scale controls etc
        :type scale: float
        :param fk: do you want to build the fk controls?
        :type fk: bool
        :param revFk:  do you want to build the revFk controls?
        :type revFk: bool
        :param flt: do you want to build the flt controls?
        :type flt: bool
        :param spine: do you want to build the spine controls?
        :type spine: bool
        :param cogUpAxis: Which direction to orient the COG control?  Up axis "+y" or "-z" etc
        :type cogUpAxis: str

        :param message: report the message to the user?
        :type message: bool
        """
        self.rigName = rigName
        self.jointList = jointList
        self.controlCount = controlCount
        self.scale = scale
        self.fk = fk
        self.revFk = revFk
        self.flt = flt
        self.spine = spine
        self.stretchy = stretchy
        self.cogUpAxis = cogUpAxis
        self.buildAll(message=message)

    def _buildControls(self):
        """Builds the control curves
        """
        self.cogControl, self.cogGroup = splines.buildSplineCogControl(self.rigName, self.clusterList,
                                                                       scale=self.scale, upAxis=self.cogUpAxis)
        self.fkControlList = list()
        self.fkGroupList = list()
        if self.fk:  # fk controls
            self.fkControlList, \
            self.fkGroupList = splines.buildControlsSplineFk(self.rigName, self.clusterList, scale=self.scale,
                                                             orientGlobalVectorObj=self.cogControl)
        self.revfkControlList = list()
        self.revfkGroupList = list()
        if self.revFk:  # revFk controls
            self.revfkControlList, \
            self.revfkGroupList = splines.buildControlsSplineRevfk(self.rigName, self.clusterList, scale=self.scale,
                                                                   orientGlobalVectorObj=self.cogControl)
        self.floatControlList = list()
        self.floatGroupList = list()
        if self.flt:  # float controls
            self.floatControlList, \
            self.floatGroupList = splines.buildControlsSplineFloat(self.rigName, self.clusterList, scale=self.scale,
                                                                   orientGlobalVectorObj=self.cogControl)
        self.spineControlList = list()
        self.spineGroupList = list()
        self.spineOtherConstraintList = list()
        self.spineRotControl = ""
        if self.spine:  # spine controls
            self.spineControlList, \
            self.spineGroupList, \
            self.spineOtherConstraintList, \
            self.spineRotControl = splines.buildControlsSplineSpine(self.rigName, self.clusterList, scale=self.scale,
                                                                    orientGlobalVectorObj=self.cogControl)

    def _buildStretchy(self):
        """Builds the squash and stretch setup
        """
        self.curveInfo, \
        self.splineMultiplyNode, \
        self.splineMultiplyNode2, \
        self.splineStretchBlendTwoAttr, \
        self.splineSquashBlendTwoAttr, \
        self.multiplyStretchNodes = splines.createStretchy(self.splineIkList[2], self.jointList)
        # create and connect attributes
        splines.stretchyConnectCntrlAttributes(self.splineStretchBlendTwoAttr, self.splineSquashBlendTwoAttr,
                                               self.cogControl)
        # Hookup scale to world size so the rig can be scaled
        self.scaleGroup, \
        self.scaleMultiplyNode, \
        self.scaleGroupConstraint = splines.stretchyWorldScaleMod(self.cogControl,
                                                                  self.splineMultiplyNode2,
                                                                  self.rigName)

    def _buildAdvancedTwist(self):
        """Builds the spline ik advanced twist
        """
        splines.advancedSplineIkTwist(self.splineIkList[0], (self.clusterList[0])[1], (self.clusterList[-1])[1])

    def _constrainToControls(self):
        pureClusterList = list()  # filter the clusters because they are in little lists? why?
        for i, clusterPack in enumerate(self.clusterList):
            pureClusterList.append((self.clusterList[i])[1])
        spineControl = ""
        if self.spineRotControl:  # spine exists
            spineControl = self.spineRotControl[0]
        self.controlEnumList, \
        self.driverAttr, \
        self.hchySwitchCondPnts, \
        self.hchySwitchCondVis, \
        self.objConstraintList = splines.constrainToControls(self.fkControlList, self.fkGroupList,
                                                             self.revfkControlList, self.revfkGroupList,
                                                             self.floatControlList, self.floatGroupList,
                                                             self.spineControlList, self.spineGroupList,
                                                             pureClusterList, self.cogControl, self.rigName,
                                                             spineControl)

    def _createRigMessageNode(self):
        self.messageNodeManager = cmds.createNode("network", n="{}_messageNodeManager".format(self.rigName))
        # connect with message node
        cmds.addAttr(self.cogControl, longName="messageNodeManager", attributeType='message')
        cmds.connectAttr('{}.message'.format(self.messageNodeManager),
                         '.'.join([self.cogControl, "messageNodeManager"]))
        spineControl = ""
        if self.spineRotControl:  # spine exists
            spineControl = self.spineRotControl[0]
        splines.createMessageNodeSetupSpline(self.messageNodeManager, self.fkControlList, self.revfkControlList,
                                             self.floatControlList, self.spineControlList, spineControl)

    def _cleanupRig(self):
        self.rigGrp = splines.cleanupSplineRig(self.fkGroupList, self.revfkGroupList, self.floatGroupList,
                                               self.spineGroupList, self.clusterList, self.rigName, self.splineIkList,
                                               self.splineSolver, self.jointList, self.spineRotControl, self.cogControl,
                                               self.cogGroup, self.scaleGroup)

    def returnAllNodes(self):
        """Returns all rig nodes after creation
        """
        return self.splineIkList, self.splineSolver, self.clusterList, self.fkControlList, self.fkGroupList, \
               self.revfkControlList, self.revfkGroupList, self.floatControlList, self.floatGroupList, \
               self.spineControlList, self.spineRotControl, self.spineOtherConstraintList, self.spineRotControl, \
               self.cogControl, self.cogGroup, self.scaleGroup, self.scaleMultiplyNode, self.scaleGroupConstraint, \
               self.rigGrp

    def buildAll(self, message=True):
        """Builds the spline rig
        """
        # spline ik
        self.splineIkList, self.splineSolver = splines.createSplineIk(self.rigName, self.jointList,
                                                                      curveSpans=self.controlCount - 3)
        self.clusterList = deformers.createClustersOnCurve(self.rigName, self.splineIkList[2])  # clusters
        self._buildControls()  # Controls
        if self.stretchy:  # Stretchy
            self._buildStretchy()
        self._buildAdvancedTwist()  # Advanced twist
        self._constrainToControls()  # The constraint setup to the controls
        self._createRigMessageNode()  # Create the message node to track the objects
        self._cleanupRig()  # cleanup the outliner
        if message:
            om2.MGlobal.displayInfo("Success: Spline rig built")


@general.undoDecorator
def buildSpine(rigName, jointList=[], startJoint="", endJoint="", controlCount=5, scale=1.0, buildFk=True,
               buildRevFk=True, buildSpine=True, buildFloat=True, cogUpAxis="+y"):
    """Builds the spine rig

    :param rigName: The name of the rig
    :type rigName: str
    :param jointList: list of joints to add to the spline
    :type jointList: list(str)
    :param controlCount: The amount of controls to build, will be 5 if a spine
    :type controlCount: int
    :param scale: The scale of the rig, affects the controls
    :type scale: float
    :param buildFk: Builds the Fk controls part of the rig
    :type buildFk: bool
    :param buildRevFk: Builds the Reverse Fk controls part of the rig
    :type buildRevFk: bool
    :param buildSpine: Builds the Spine controls part of the rig
    :type buildSpine: bool
    :param buildFloat: Builds the Floating controls part of the rig
    :type buildFloat: bool
    :return splineInstance: The instance of the spline class
    :rtype splineInstance: object
    :return allNodes: See splineBuilder.returnAllNodes() for all nodes
    :rtype splineInstance: list()
    """
    # Error checking ------------------------------------------------------------------
    if not buildFk and not buildRevFk and not buildSpine and not buildFloat:
        om2.MGlobal.displayWarning("A rig type must be selected to build.  Please check a Control Rig.")
        return None, None
    if not jointList:
        if not cmds.objExists(startJoint):
            om2.MGlobal.displayWarning("The start joint `{}` does not exist".format(startJoint))
            return
        if endJoint:
            if not cmds.objExists(endJoint):
                om2.MGlobal.displayWarning("The end joint `{}` does not exist".format(endJoint))
                return
        if not startJoint:
            om2.MGlobal.displayWarning("Please specify a starting joint.")
            return
        # Check the start joint is a joint
        if cmds.nodeType(startJoint) != "joint":
            om2.MGlobal.displayWarning("`{}` is not a joint.  Please specify a joint name.".format(startJoint))
            return
        if endJoint and cmds.nodeType(endJoint) != "joint":
            om2.MGlobal.displayWarning("`{}` is not a joint.  Please specify a joint name.".format(endJoint))
            return
        jointList = joints.getJointChain(startJoint, endJoint)  # Extrapolates the joint chain
        if not jointList:  # Can happen if the end joint is not a child of the start joint.
            om2.MGlobal.displayWarning("The specified joints do not form a legitimate joint chain, "
                                       "try reversing the start/end entries, or check your scene.")
            return
    # Checks passed so build the rig  ------------------------------------------------------------------
    splineInstance = splineBuilder(rigName, jointList, controlCount=controlCount, scale=scale, fk=buildFk,
                                   revFk=buildRevFk, spine=buildSpine, flt=buildFloat, cogUpAxis=cogUpAxis)
    return splineInstance, splineInstance.returnAllNodes()


if __name__ == "__main__":
    rigName = "rigX"
    jointList = ["joint1", "joint2", "joint3", "joint4", "joint5", "joint6", "joint7", "joint8", "joint9"]
    buildSpine(rigName, jointList, controlCount=5, scale=1.0)
