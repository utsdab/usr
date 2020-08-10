"""
Functions for handling wildcard matching of objects in Maya.  Wildcards are usually suffix or prefix names
Used in matching controls, proxies and triggers etc
Wildcard should be given without a "_" underscore
"""

import maya.cmds as cmds
import maya.api.OpenMaya as om2

from zoo.libs.maya.cmds.objutils import namehandling

def renameWithUniquePrefix(prefixName, nodeName):
    """Renames the node with a suffix and checks that the suffix is unique

    :param prefixName: the prefix name, will be added with a unique name to the nodeName
    :type prefixName: str
    :param nodeName: the Maya node name
    :type nodeName: str
    :return nodeName: new name now with unique suffix added that won't clash with other objects in scene
    :rtype nodeName: str
    """
    uniquePrefixName = prefixName
    potentialClashSuffixList = list()
    if nodeName.startswith(prefixName):  # check if the suffix already exists in the incoming nodeName
        # if it does remove the prefix (assumes it has a "_" underscore separator eg suffix01_object)
        if "_" in nodeName:
            tempPrefix = nodeName.split("_")[0]  # could have a number after it before the "_"
            nodeName = nodeName.replace("{}_".format(tempPrefix), "")
    potentialClashesInScene = cmds.ls("*{}".format(nodeName))   # find all objects which could clash with new node name
    if potentialClashesInScene:
        for potentialClash in potentialClashesInScene:
            if "_".format(nodeName) in potentialClash:  # remove the node name leaving the potentially clashing prefix
                potentialClashSuffixList.append(potentialClash.replace("_{}".format(nodeName), ""))
        if potentialClashSuffixList:  # test that the prefix is unique, if not unique it
            potentialClashSuffixList = list(set(potentialClashSuffixList))  # take away duplicates
            uniquePrefixName = namehandling.uniqueNameFromList(prefixName, potentialClashSuffixList)
    return "_".join([uniquePrefixName, nodeName])  # rename with the new suffix



def filterNonMatchingObjs(nodeList, wildcardName):
    """Given a list of nodes return the matching nodes with the wildcard name removed
    Also return the wildcard objects with successful matches

    :param objectList:
    :type objectList:
    :param wildcardName:
    :type wildcardName:
    :return:
    :rtype:
    """
    matchObjs = list()
    wildcardObjs = list()
    for node in nodeList:
        matchTemp = node.replace(wildcardName, '')
        if cmds.objExists(matchTemp):
            wildcardObjs.append(node)
            matchObjs.append(matchTemp)
    return (wildcardObjs, matchObjs)


def getWildcardObjs(wildcardName, suffix="suffix", reportMessage=False):
    """Returns objects specified by wildcardName suffix string

    :param wildcardName:
    :type wildcardName:
    :param suffix: Can be any of three strings "suffix", "prefix", "both"
    :type suffix: string
    :param reportMessage:
    :type reportMessage:
    :return:
    :rtype:
    """
    if not cmds.objExists("*{}*".format(wildcardName)):
        if reportMessage:
            om2.MGlobal.displayWarning("No Objects Found With Name '{}'".format(wildcardName))
        return
    if suffix == "suffix":
        return cmds.ls("*_{}".format(wildcardName))
    elif suffix == "prefix":
        return cmds.ls("{}_*".format(wildcardName))
    else:
        return cmds.ls("*{}*".format(wildcardName))


def renameWildcardTwoObj(objList, wildcard, reverse=False, suffix="suffix"):
    """Renames the first object [0] to the name of the second [1] adding the suffix to the tail of the name
    if `reverse` then reverse the named object to be the second [1]

    :param objList: list of Maya objects by name
    :type objList: list
    :param wildcard: the wildcard name as a string, should have no "_"
    :type wildcard: str
    :param reverse: Do you want to reverse the order?  This will rename the second object
    :type reverse: bool
    :param suffix: Can affect the suffix or prefix naming, "suffix" or "prefix"
    :type suffix:
    :return originalObject:
    :rtype: str
    :return newRenamedObj:
    :rtype: str
    """
    if reverse:
        temp = objList[1]
        objList[1] = objList[0]
        objList[0] = temp
    if suffix == "suffix":
        newRenamedObj = "_".join([objList[1], wildcard])
    else:
        newRenamedObj = "_".join([wildcard, objList[1]])
    cmds.rename(objList[0], (newRenamedObj))
    return objList[0], newRenamedObj


def renameWildcardTwoObjSelected(wildcard, reverse=False, suffix="suffix"):
    """Renames the first selected object to the name of the second now adding the suffix to the tail of the name
    if `reverse` then reverse the named object to be the second

    :param wildcard: the wildcard name as a string, should have no "_"
    :type wildcard: str
    :param reverse: Do you want to reverse the order?  This will rename the second object
    :type reverse: bool
    :param suffix: Can affect the suffix or prefix naming, "suffix" or "prefix"
    :type suffix:
    """
    objList = cmds.ls(selection=True)
    if not objList:
        om2.MGlobal.displayWarning('No Objects Select, Please Select')
        return
    if len(objList) != 2:  # only accept 2 objects given
        om2.MGlobal.displayWarning('Two objects need to be selected.  Currently {} objects'
                                   ' selected'.format(str(len(objList))))
        return
    origObj, newRenamedObj = renameWildcardTwoObj(objList, wildcard, reverse=reverse, suffix=suffix)
    om2.MGlobal.displayInfo("`{}` renamed to `{}`".format(origObj, newRenamedObj))


def removeWildcardNameObjsList(objList, wildcardName):
    """changes a list so that the wildcard name is taken out of every item

    :param objList: list of Maya object names
    :type objList: list
    :param wildcardName: the name of the wildcard to be removed
    :type wildcardName: str
    :return wildcardRemovedList: A list of the given objects now with the wildcard removed from each name
    :rtype wildcardRemovedList: list
    """
    wildcardRemovedList = []
    for obj in objList:
        wildcardRemovedList.append(obj.replace(wildcardName, ''))
    return wildcardRemovedList

