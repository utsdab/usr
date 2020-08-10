import maya.cmds as cmds
import maya.api.OpenMaya as om2

from zoo.libs.maya.cmds.objutils import namehandling, shapenodes


def createClustersOnCurve(partPrefixName, splineCurve, relative=False, showHandles=False, padding=2):
    """Creates clusters on a curve automatically adding the clusters to each cv in order

    :param partPrefixName:  The prefix, name of the rig/part, optional, can be an empty string (auto), is a shortname
    :type partPrefixName: str
    :param splineCurve: can be a nurbsCurve shape node or transform with nurbsCurve shape, longname preferred
    :type splineCurve: str
    :param relative:  If True only the transformations directly above the cluster are used by the cluster.
    :type relative: bool
    :param showHandles:  If True show the Maya handles display mode, little crosses on each handle
    :type showHandles: bool
    :param padding:  The numerical padding
    :type padding: bool
    :return clusterList: The created cluster names
    :rtype clusterList: list
    """
    rememberObjs = cmds.ls(selection=True, long=True)
    clusterList = list()
    numSpans = cmds.getAttr("{}.spans".format(splineCurve))
    degree = cmds.getAttr("{}.degree".format(splineCurve))
    form = cmds.getAttr("{}.form".format(splineCurve))
    numCVs = numSpans + degree
    if form == 2:
        numCVs -= degree
    nameSuffix = "cluster"
    if partPrefixName:  # then add it to the beginning of the name
        nameSuffix = "{}_cluster".format(partPrefixName)
    for i in range(numCVs):
        clusterName = "{}_{}_".format(nameSuffix, str(i).zfill(padding))
        clusterList.append(cmds.cluster("{}.cv[{}]".format(splineCurve, i), name=clusterName, relative=relative))
    cmds.select(rememberObjs, replace=True)  # as clusters are created they're selected, so return to orig
    if showHandles:
        for clusterPair in clusterList:  # cluster pair is a list, [clusterNode, transformNode]
            cmds.setAttr("{}.displayHandle".format(clusterPair[1]), True)
    return clusterList


def createClustersOnCurveSelection(partPrefixName="", relative=False, showHandles=False):
    """Creates a cluster on each CV of a nurbsCurve of the first selected object.

    If a transform selection will check shapes for the first nurbsCurve shape node

    :param showHandles:  if not an empty string overrides the default cluster name which uses the spline name as prefix
    :type showHandles: bool
    :param showHandles:  If True show the Maya handles display mode, little crosses on each handle
    :type showHandles: bool
    :param padding:  The numerical padding
    :type padding: bool
    :return clusterList: The created cluster names,
    :rtype clusterList: list(list(str))
    """
    # TODO support lists not only first selected obj
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        om2.MGlobal.displayWarning("Nothing selected. Please select a curve")
        return list()
    splineShape = shapenodes.transformHasShapeOfType(selObjs[0], "nurbsCurve")
    if not splineShape:
        om2.MGlobal.displayWarning("Please select a curve.")
        return list()
    # Curve found so build
    if partPrefixName:  # use the partPrefixName as the prefix for each cluster
        return createClustersOnCurve(partPrefixName, splineShape, relative=relative, showHandles=showHandles)
    firstObjShortName = namehandling.mayaNamePartTypes(selObjs[0])[2]  # short name and no namespace
    # firstObj as prefix for each cluster
    return createClustersOnCurve(firstObjShortName, splineShape, relative=relative, showHandles=showHandles)

