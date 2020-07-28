"""
Zoo Asset Code

To Do
- list assets in the scene just print is ok for starters
- Add asset list to "manage asset in scene", should be a selectable list
- Delete ibl textures
- lights won't delete hdri textures for arnold and deleting shaders won't delete any textures assigned should fix in
light manager then return the nodes here for the assets

"""

import json
import glob, os

import maya.cmds as cmds
import maya.api.OpenMaya as om2
from zoo.libs.zooscene import constants

from zoo.libs.zooscene import zooscenefiles
from zoo.libs.maya.cmds.renderer import exportabcshaderlights
from zoo.libs.maya.cmds.rig import nodes, connections
from zoo.libs.maya.cmds.objutils import objhandling, namehandling
from zoo.libs.maya.cmds.cameras import cameras
from zoo.libs.maya.cmds.animation import keyframes
from zoo.libs.maya.cmds.shaders import shaderutils

PRESETSUFFIX = ["zooScene"]  # the file type recognised as an package (asset)
ASSETFILEPATHPRESETS = "assetspresets.json"  # the file that the asset preset quick directory is stored
FILEQUICKDIRKEY = "fileQuickDir"  # the key for the ASSETFILEPATHPRESETS dict for retrieving the file path
ZOOSCENEGRPNAME = "zooPackage_grp"  # the name of the grp for importing assets
ASSETSUFFIX = "zooAssetNetwork"
ASSETATTR = "assetConnections"  # the attribute on the network node that identifies all asset nodes
ASSETROOTATTR = "assetRootGrp"  # the attribute on the network node that identifies the root grp
ASSETTYPEATTR = "assetType"  # the attribute on the network node that identifies the asset type as a string
ASSETGRP = "package_grp"
INFOASSET = constants.INFOASSET  # the key for asset types in the infoDict
ASSETTYPES = constants.ASSETTYPES

# txt for asset info/tags
TAGCREATORPLACEHOLD = "3d Model: Your Name \n2d Concept: Artist Name"
TAGWEBSITEPLACEHOLD = "www.yourwebsite.com \nwww.conceptartist.com"
TAGPLACEHOLD = "tagOne, tag two, three"
TAGDESCRIPTIONPLACEHOLD = "Full description goes here."


def getPluginAbcLoaded():
    """Returns the state of the two plugins, AbcImport and AbcExport

    :return abcImportLoaded: the state, True/False of the abcImport plugin
    :rtype abcImportLoaded: bool
    :return abcExportLoaded: the state, True/False of the abcExport plugin
    :rtype abcExportLoaded: bool
    """
    abcImportLoaded = cmds.pluginInfo("AbcImport", query=True, loaded=True)
    abcExportLoaded = cmds.pluginInfo("AbcExport", query=True, loaded=True)
    return abcImportLoaded, abcExportLoaded


def loadAbcPlugin(message=True):
    """Loads the AbcImport and AbcExport plugins

    :param message:  return the message to the user
    :type message: bool
    """
    if getPluginAbcLoaded()[0] and getPluginAbcLoaded()[1]:  # both abc import and export loaded
        if message:
            om2.MGlobal.displayWarning("Abc Alembic Import/Export Plugins Already Loaded")
    if not getPluginAbcLoaded()[0]:
        cmds.loadPlugin("AbcImport")
    if not getPluginAbcLoaded()[1]:
        cmds.loadPlugin("AbcExport")
    if message:
        om2.MGlobal.displayInfo("Abc Alembic Import/Export Plugins Now Loaded")


def getAssetNode(objList):
    """returns a list of asset nodes from the given objects
    for each object find if it has a asset node attached


    :param objList: list of maya object names
    :type objList: str
    :return assetNodes: list of unique asset nodes connected to the objects
    :rtype assetNodes: list
    """
    assetNodes = list()
    for obj in objList:
        if cmds.attributeQuery(ASSETATTR, node=obj, exists=True):  # if attribute exists
            connectedNodes = cmds.listConnections('.'.join([obj, ASSETATTR]))
            if connectedNodes:  # must check as fails on first in list
                assetNodes.append(connectedNodes[0])
    if not assetNodes:
        return assetNodes
    assetNodes = list(set(assetNodes))  # make unique
    assetNodes = namehandling.getLongNameList(assetNodes)  # force long names
    return assetNodes


def getAssetFromSelection():
    """returns a list of asset nodes from the selected objects

    :return assetNodes: list of unique asset nodes connected to the objects
    :rtype assetNodes: list
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        om2.MGlobal.displayWarning("No Objects Selected. Please Select An Object/s")
        return list()
    return getAssetNode(selObjs)


def getAssetFromSelectionOrUI(uiSelectedName="", message=True):
    """returns a list of asset nodes from the selected objects
    If none found then tries to find based off a UI selection name
    For each object find if it has a asset node attached

    :param uiSelectedName: the name of the package asset usually selected in the UI
    :type uiSelectedName: str
    :param message: report the message to the user?
    :type message: bool
    :return assetNodes: list of unique asset nodes connected to the objects
    :rtype assetNodes: list
    """
    assetGrps = findAssetGrpsSelectedOrUI(uiSelectedName=uiSelectedName, message=message)
    if not assetGrps:
        return
    return getAssetNode(assetGrps)


def removeAssetNodeSelected():
    """deletes asset nodes from assets, these network nodes are what tracks the characters

    :return assetNodes: The asset nodes (Network Nodes) in the scene that were deleted
    :rtype assetNodes:
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        om2.MGlobal.displayWarning("No Objects Selected. Please Select An Object/s")
        return list()
    assetNodes = getAssetNode(selObjs)
    if not assetNodes:
        om2.MGlobal.displayWarning("Couldn't find asset node, this object/s may not be an asset")
        return list()
    for assetNode in assetNodes:
        cmds.delete(assetNode)
    om2.MGlobal.displayInfo("Asset Nodes Are Disconnected. Nodes Deleted: {}".format(assetNodes))
    return assetNodes


def getAssetGroup(assetNodes):
    """returns an asset group list given the asset node list

    :param assetNodes: list of unique asset nodes
    :type assetNodes: list
    :return assetGrps: list of unique asset group names connected to the given assetNodes
    :rtype assetGrps: list
    """
    assetGrps = list()
    for assetNode in assetNodes:
        # assets may not have a group and if so are considered dead and should be cleaned
        if cmds.connectionInfo('.'.join([assetNode, ASSETROOTATTR]), isSource=True):  # if node is connected
            assetGrps.append(cmds.listConnections('.'.join([assetNode, ASSETROOTATTR]))[0])
        else:  # the asset node is not connected to a grp so it's considered dead.  Delete the asset node
            cmds.delete(assetNode)
    if not assetGrps:
        return assetGrps
    assetGrps = list(set(assetGrps))
    assetGrps = namehandling.getLongNameList(assetGrps)  # long names
    return assetGrps


def getAssetGrpsSelected():
    """returns an asset group list from selected objs

    :return assetGrps: list of unique asset group names connected to the given selected objs
    :rtype assetGrps: list
    """
    assetNodes = getAssetFromSelection()
    return getAssetGroup(assetNodes)


def findAssetGrpsSelectedOrUI(uiSelectedName="", message=True):
    """Finds assets grps with priority to the selected objects (getAssetGrpsSelected())
    If none are selected or found then try from the uiSelectedName which is usually the name of the
    package selected in the browser UI

    :param uiSelectedName: the name of the package asset usually selected in the UI
    :type uiSelectedName: str
    :param message: report the message to the user
    :type message: bool
    :return assetGrps: list of maya objects, usually grp transform names
    :rtype assetGrps: list
    """
    selObjs = cmds.ls(selection=True)
    assetGrpsUI = list()
    assetGrps = list()
    if uiSelectedName:  # do a wildcard search on the name joined with the assetgrp name
        wildcardSearch = "{}_{}*".format(uiSelectedName, ASSETGRP)
        assetGrpsUI = cmds.ls(wildcardSearch)  # will be an empty list if not found
    if not selObjs and not assetGrpsUI:
        if message:
            om2.MGlobal.displayWarning("No Objects Selected or found from UI Selection. Please Select An Object/s")
        return
    if selObjs:  # then objects selected so search from selection
        assetGrps = getAssetGrpsSelected()
    if not assetGrps:  # nothing connected to selected
        if not assetGrpsUI:  # nothing found from the ui name
            if message:
                om2.MGlobal.displayWarning("No Asset Groups Found That Are Connected To Selected Objects "
                                           "Or UI Selection".format(assetGrps))
            return
        return assetGrpsUI
    return assetGrps


def createAssetGrps(assetName):
    """creates the asset groups, one scene asset grp if it doesn't exist and the other custom named asset grp

    :param assetName: the prefix of the asset group name
    :type assetName: str
    :return assetGrpLongName: the long name of the asset group, no need to pass the other group as its ZOOSCENEGRPNAME
    :rtype assetGrpLongName: str
    """
    assetGrpName = '_'.join([assetName, ASSETGRP])
    assetGrpName = namehandling.nonUniqueNameNumber(assetGrpName, shortNewName=True)
    if not cmds.objExists(ZOOSCENEGRPNAME):  # create the scene grp
        cmds.group(em=True, name=ZOOSCENEGRPNAME)
    assetGrpName = cmds.group(em=True, name=assetGrpName)
    assetGrpName = cmds.parent(assetGrpName, ZOOSCENEGRPNAME)
    assetGrpLongName = cmds.ls(assetGrpName, long=True)[0]
    return assetGrpLongName


def createAssetFromSelection(newAssetName, message=True):
    """Creates a new asset from selection, creates a new asset grp from the name given and
    copies it to the ZOOSCENEGRPNAME
    creates a network node that connects to all the children and grandchildren of selected and shaders

    :param newAssetName: the name of the new asset, may be in use and will be unique
    :type newAssetName: str
    :param message: Would you like the user to see the message in Maya
    :type message: True
    :return allObjects: all nodes connected to the networkNodeName
    :rtype allObjects: list
    :return networkNodeName: the network asset node name that connects to all asset objects and nodes
    :rtype networkNodeName: str
    """
    # get the obj roots
    selectedRootObjs = objhandling.getRootObjectsFromSelection()
    # get all nodes hierarchies
    relatives = cmds.listRelatives(allDescendents=True)
    allObjects = selectedRootObjs + relatives
    # get all related shaders and shader nodes
    allShadingGroups = shaderutils.getShadingGroupsObjList(allObjects)
    allShaders = shaderutils.getShadersFromSGList(allShadingGroups)
    allObjects = allObjects + allShadingGroups + allShaders
    # check all nodes are not already connected to an asset
    assetNodes = getAssetNode(allObjects)
    if assetNodes:
        if message:
            om2.MGlobal.displayWarning("Some nodes related to this selection (children/shaders) are already "
                                       "connected to {}".format(assetNodes))
        return list()
    # create the folder/s
    assetGrpLongName = createAssetGrps(newAssetName)
    networkNodeName = '_'.join([newAssetName, ASSETSUFFIX])
    allObjects = list(set(allObjects))
    # create the network node and make connections
    networkNodeName = nodes.createNetworkNodeWithConnections(networkNodeName, ASSETATTR, allObjects)
    # finally connect the new asset group
    connections.createMessageConnection(networkNodeName, assetGrpLongName, ASSETATTR)
    connections.createMessageConnection(networkNodeName, assetGrpLongName, ASSETROOTATTR)
    allObjects.append(assetGrpLongName)
    for rootObj in selectedRootObjs:  # parent to the group
        cmds.parent(rootObj, assetGrpLongName)
    # now everything has been parented, get the names of all objects from the connections
    allObjects = cmds.listConnections('.'.join([networkNodeName, ASSETATTR]))
    if message:
        om2.MGlobal.displayInfo("Success: Asset node created: {}".format(networkNodeName))
    return allObjects, networkNodeName


def loopAbcMeshSelection(cycleInt=1):
    """from the current selection set the alembic cache/s to the cycle type

    :param cycleInt: the integer of the attribute cycleType 0 Hold 1 is Loop 2 is Reverse 3 is Bounce
    :type cycleInt: int
    :return alembicNodeList: the alembic nodes changed
    :rtype alembicNodeList: list
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        om2.MGlobal.displayWarning("No Objects Selected. Please Select An Object/s")
        return list()
    meshShapeList = list()
    alembicNodeList = list()
    for obj in selObjs:
        meshShapes = cmds.listRelatives(obj, shapes=True, type="mesh")
        if meshShapes:
            meshShapeList += meshShapes
    for meshShape in meshShapeList:
        inMeshList = cmds.listConnections('.'.join([meshShape, "inMesh"]))
        for inMesh in inMeshList:
            if cmds.objectType(inMesh) == "AlembicNode":
                alembicNodeList.append(inMesh)
    alembicNodeList = list(set(alembicNodeList))
    for alembicNode in alembicNodeList:
        cmds.setAttr("{}.cycleType".format(alembicNode), cycleInt)  # set the alembic node to "Loop"
    return alembicNodeList


def loopAbcSelectedAsset(cycleInt=1, uiSelectedName="", message=True):
    """Loops a selected alembic node from the asset nodes, or the given cycle type

    :param cycleInt: the integer of the attribute cycleType 0 Hold 1 is Loop 2 is Reverse 3 is Bounce
    :type cycleInt: int
    :param uiSelectedName: the name of the package asset usually selected in the UI
    :type uiSelectedName: str
    :param message: report the message to the user?
    :type message: bool
    :return alembicNodeList: the alembic nodes changed
    :rtype alembicNodeList: list
    """
    assetNodes = getAssetFromSelectionOrUI(uiSelectedName=uiSelectedName, message=True)
    if not assetNodes:
        return list()
    connectedNodes = cmds.listConnections('.'.join([assetNodes[0], ASSETATTR]))
    alembicNodes = cmds.ls(connectedNodes, type="AlembicNode")
    if alembicNodes:
        for alembicNode in alembicNodes:
            cmds.setAttr("{}.cycleType".format(alembicNode), cycleInt)  # set the alembic node to "Loop"
    return alembicNodes


def scaleRotateAssetSelected(scaleValue, rotYValue, uiSelectedName="", message=True):
    """Scales the selected package asset's grp to the scale and rotY value

    :param scaleValue: the scale value of the asset package grp on x y and z
    :type scaleValue: float
    :param rotYValue: the rot y value of the asset package grp
    :type rotYValue: float
    :param uiSelectedName: the name of the asset grp to try if the selection method fails
    :type uiSelectedName: str
    :param message: show the success message to the user?
    :type message: bool
    """
    assetGrps = findAssetGrpsSelectedOrUI(uiSelectedName=uiSelectedName, message=message)
    if not assetGrps:
        return
    for assetGrp in assetGrps:
        cmds.setAttr("{}.scaleX".format(assetGrp), scaleValue)
        cmds.setAttr("{}.scaleY".format(assetGrp), scaleValue)
        cmds.setAttr("{}.scaleZ".format(assetGrp), scaleValue)
        cmds.setAttr("{}.rotateY".format(assetGrp), rotYValue)
    if message:
        om2.MGlobal.displayInfo("Success: Package Grps Changed {}".format(assetGrps))


def createTurntableAssetSelected(startFrame=0, endFrame=200, angleOffset=0, setTimerange=True, uiSelectedName="",
                                 reverse=False, message=True):
    """Creates a turntable on an asset from object selection, auto finds the asset group and animates it

    :param startFrame: the start frame of the turntable
    :type startFrame: float
    :param endFrame: the end frame of the turntable
    :type endFrame: float
    :param angleOffset: the angle offset of the keyframes in degrees, will change the start rotation of the asset
    :type angleOffset: float
    :param setTimerange: will change mayas timerange to match to the start and end frames
    :type setTimerange: bool
    :param uiSelectedName: the name of the asset grp to try if the selection method fails
    :type uiSelectedName: str
    :param reverse: reverses the spin direction
    :type reverse: bool
    :param message: report the messages to the user in Maya?
    :type message: bool
    :return assetGrps: the group/s now with animation
    :rtype assetGrps: list
    """
    assetGrps = findAssetGrpsSelectedOrUI(uiSelectedName=uiSelectedName, message=message)
    if not assetGrps:
        return
    for assetGrp in assetGrps:
        keyframes.createTurntable(assetGrp, start=startFrame, end=endFrame, angleOffset=angleOffset,
                                  setTimerange=setTimerange, reverse=reverse)
    if message:
        om2.MGlobal.displayInfo("Turntable Create on:  {}".format(assetGrps))
    return assetGrps


def deleteTurntableAssetSelected(attr="rotateY", message=True, returnToZeroRot=True, uiSelectedName=""):
    """Deletes a turntable anim of an asset. auto finds the asset group and deletes the anim on rot y

    :param attr: the attribute to delete all keys
    :type attr: str
    :param message: report the messages to the user in Maya?
    :type message: bool
    :param returnToZeroRot: return the object to default zero?
    :type returnToZeroRot: bool
    :param uiSelectedName: the name of the asset grp to try if the selection method fails
    :type uiSelectedName: str
    :return assetGrps: the group/s now with animation
    :rtype assetGrps: list
    """
    assetGrps = findAssetGrpsSelectedOrUI(uiSelectedName=uiSelectedName, message=message)
    if not assetGrps:
        return
    for assetGrp in assetGrps:
        cmds.cutKey(assetGrp, time=(-1000, 100000), attribute=attr)  # delete all keys rotY
        if returnToZeroRot:
            cmds.setAttr(".".join([assetGrp, attr]), 0)
    if message:
        om2.MGlobal.displayInfo("Turntable Keyframes deleted on:  {}".format(assetGrps))
    return assetGrps


def deleteAssetNodeList(zooAssetNodeList):
    """For the Maya scene deletes multiple package asset nodes and their connections

    :param zooAssetNodeList: a list of asset nodes who's connections need to be deleted
    :type zooAssetNodeList:
    """
    for assetNode in zooAssetNodeList:
        if cmds.objExists(assetNode):  # are occasions where it has already been deleted
            cmds.select(assetNode)
            # delete root grp
            if cmds.connectionInfo('.'.join([assetNode, ASSETROOTATTR]), isSource=True):  # if node is connected
                assetGrp = cmds.listConnections('.'.join([assetNode, ASSETROOTATTR]))[0]
                cmds.delete(assetGrp)  # will delete the root grp but other nodes may exist, faster to delete this first
            if not cmds.objExists(assetNode):  # the asset node can already be deleted if not shaders
                continue  # asset has been deleted
            # Continue to delete all connected nodes shaders etc
            cmds.select(assetNode)
            if cmds.connectionInfo('.'.join([assetNode, ASSETATTR]), isSource=True):  # if node is connected
                connectedNodes = cmds.listConnections('.'.join([assetNode, ASSETATTR]))
                for node in connectedNodes:  # left over nodes
                    if cmds.objExists(node):
                        cmds.delete(node)
            if cmds.objExists(assetNode):
                cmds.delete(assetNode)  # remove the asset node itself
    if cmds.objExists("|{}".format(ZOOSCENEGRPNAME)):  # "|zooAsset_grp"
        if not cmds.listRelatives("|{}".format(ZOOSCENEGRPNAME), children=True):  # no children so delete it too
            cmds.delete("|{}".format(ZOOSCENEGRPNAME))


def deleteZooAssetObjList(objList):
    """Deletes (in the Maya scene) package assets that are connected to the asset nodes of the objList

    :param objList: list of Maya objects
    :type objList: list
    :return assetNodes: list of asset nodes  (all their connections will be deleted)
    :rtype assetNodes: list
    """
    assetNodes = getAssetNode(objList)
    if not assetNodes:
        return list()
    deleteAssetNodeList(assetNodes)
    return assetNodes


def selectZooAssetGrps(message=True, uiSelectedName=""):
    """Selects all package asset grps from selected, if none found then tries from the UI selection

    :param message: report the message to the user?
    :type message: bool
    :param uiSelectedName: the name of the package asset usually selected in the UI
    :type uiSelectedName: str
    :return assetGrps: The asset grps selected
    :rtype assetGrps:
    """
    assetGrps = findAssetGrpsSelectedOrUI(uiSelectedName=uiSelectedName, message=message)
    if not assetGrps:
        return
    cmds.select(assetGrps, replace=True)


def deleteZooAssetSelected(uiSelectedName="", message=True):
    """Deletes (in the Maya scene) package assets that are connected to the asset nodes of the selected objects/UI
    First it tries to find asset grps from selected, then tries from the wildcard uiSelectedName_package_grp*
    If finds the grps then deletes everything in all the connected package assets

    :param message: report the message to the user?
    :type message: bool
    :param uiSelectedName: the name of the package asset usually selected in the UI
    :type uiSelectedName: str
    :return assetNodes: list of asset nodes  (all their connections will be deleted)
    :rtype assetNodes: list
    """
    assetGrps = findAssetGrpsSelectedOrUI(uiSelectedName=uiSelectedName, message=message)
    if not assetGrps:
        return
    assetNodes = deleteZooAssetObjList(assetGrps)
    if not assetNodes:
        if message:
            om2.MGlobal.displayWarning("No Asset Nodes Found That Are Connected To Selected Objects "
                                       "Or Selected In The UI")
            return
    if message:
        om2.MGlobal.displayInfo("Success: Asset/s Deleted {}".format(assetNodes))
    return assetNodes


def deleteZooAssets(onlyInAssetsGrp=False):
    """Deletes all package asset nodes and their connections in a scene
    Or if onlyInAssetsGrp then delete only assets in that grp

    :param onlyInAssetsGrp:  keep assets outside of the main asset grp
    :type onlyInAssetsGrp: bool
    :return deleteAssetNodeList:  list of asset nodes who's connections have been deleted
    :rtype deleteAssetNodeList: list
    """
    zooAssetNodeList = cmds.ls("*_{}".format(ASSETSUFFIX))
    if not zooAssetNodeList:
        return
    parentAssetNodeList = list()
    if onlyInAssetsGrp:
        for assetNode in zooAssetNodeList:
            assetGrp = cmds.listConnections('.'.join([assetNode, ASSETROOTATTR]))[0]
            if cmds.listRelatives(assetGrp, parent=True) != ASSETGRP:
                parentAssetNodeList.append(assetNode)
        zooAssetNodeList = parentAssetNodeList
    deleteAssetNodeList(zooAssetNodeList)
    return zooAssetNodeList


def tagAssetAsType(assetNode, assetType):
    """tags an asset node and sets the assetType attibute with a string

    :param assetNode: the network asset node that connects to assets in the scene
    :type assetNode: str
    :param assetType: The type of asset as per the list ASSETTYPES... "Not Specified", "Hero Model", "Prop Model" etc
    :type assetType: str
    """
    if not cmds.attributeQuery(ASSETTYPEATTR, node=assetNode, exists=True):  # if attribute exists
        cmds.addAttr(assetNode, longName=ASSETTYPEATTR, dataType="string")
    cmds.setAttr(".".join([assetNode, ASSETTYPEATTR]), assetType, type="string")


def tagAssetAsTypeObjectList(objectList, assetType):
    """tags the asset nodes of an object list to the assetType

    :param objectList: the maya object name list
    :type objectList: list
    :param assetType: The type of asset as per the list ASSETTYPES... "Not Specified", "Hero Model", "Prop Model" etc
    :type assetType: str
    :return assetNodes: the assetNodes now tagged
    :rtype assetNodes: list
    """
    assetNodes = getAssetNode(objectList)
    if not assetNodes:
        return
    for assetNode in assetNodes:
        tagAssetAsType(assetNode, assetType)
    return assetNodes


def tagAssetAsTypeSelection(assetType, message=True):
    """tags the asset nodes of selected objects and sets them to the assetType

    :param assetType: The type of asset as per the list ASSETTYPES... "Not Specified", "Hero Model", "Prop Model" etc
    :type assetType: str
    :param message: report the message to the user?
    :type message: bool
    :return assetNodes: the assetNodes now tagged
    :rtype assetNodes: list
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        if message:
            om2.MGlobal.displayWarning("No Objects Selected. Please Select An Object/s")
        return list()
    assetNodes = tagAssetAsTypeObjectList(selObjs, assetType)
    if not assetNodes:
        om2.MGlobal.displayWarning("No asset nodes are connected To the current selection")
        return list()
    om2.MGlobal.displayInfo("Success: Asset nodes tagged as `{}`: {}".format(assetType, assetNodes))
    return assetNodes


def getAssetTypeFile(filePathZooScene):
    """gets the asset type from a zooScene file, will auto find the .zooInfo file

    :param filePathZooScene:  full path to the zooscene file
    :type filePathZooScene: str
    :return assetType: The type of asset as per the list ASSETTYPES... "Not Specified", "Hero Model", "Prop Model" etc
    :rtype assetType: str
    """
    infoDict, fileFound = zooscenefiles.getZooInfoFromFile(filePathZooScene, message=False)
    if infoDict:
        return infoDict[INFOASSET]  # get asset type


def getAllAssetNamesInTheScene():
    """gets all the asset names in the scene by finding the network asset nodes and getting their grp and removing
    the suffix

    :return zooAssetNames: current asset names in the scene
    :rtype zooAssetNames: list
    """
    zooAssetNames = list()
    zooAssetNodeList = cmds.ls("*_{}".format(ASSETSUFFIX))
    if not zooAssetNodeList:
        return zooAssetNames
    assetGrpList = getAssetGroup(zooAssetNodeList)
    if not assetGrpList:
        return zooAssetNames
    for assetGrp in assetGrpList:
        if assetGrp.endswith(ASSETGRP):
            assetName = assetGrp[:-len(ASSETGRP) - 1]  # remove "_asset_grp"
            zooAssetNames.append(namehandling.getShortName(assetName))
    return zooAssetNames


def getAllAssetsInSceneOfType(assetType):
    """Gets all asset network nodes in the scene of this assetType, get this from an attribute on the node
    Some assets may have no attribute and are therefor the type  "Not Specified"

    :param assetType: The type of asset as per the list ASSETTYPES... "Not Specified", "Hero Model", "Prop Model" etc
    :type assetType: str
    :return assetNodeOfTypeList: list of network nodes that are of the given type
    :rtype assetNodeOfTypeList: list
    """
    assetNodeOfTypeList = list()
    # get all asset nodes in scene
    zooAssetNodeList = cmds.ls("*_{}".format(ASSETSUFFIX))
    if not zooAssetNodeList:
        return
    # find the type attribute
    for assetNode in zooAssetNodeList:
        if cmds.attributeQuery(ASSETTYPEATTR, node=assetNode, exists=True):  # if attribute exists
            if cmds.getAttr(".".join([assetNode, ASSETTYPEATTR])) == assetType:
                assetNodeOfTypeList.append(assetNode)
        else:
            if assetType == ASSETTYPES[0]:  # if not specified
                assetNodeOfTypeList.append(assetNode)
    return assetNodeOfTypeList


def importZooSceneNoParent(filePathZooScene, rendererNiceName, assetName, importShaders=True, importLights=True,
                           importAbc=True, replaceShaders=True, addShaderSuffix=True, importSubDInfo=True,
                           replaceRoots=False):
    """Imports the asset without parenting to the asset group

    :param filePathZooScene:  full path to the zooscene file
    :type filePathZooScene: str
    :param rendererNiceName: the renderer nice name "Arnold"
    :type rendererNiceName: str
    :param assetName: the name of the asset for the network node name
    :type assetName: str
    :param importShaders: import shaders into the scene?
    :type importShaders: bool
    :param importLights: import lights into the scene?
    :type importLights: bool
    :param importAbc: import alembic into the scene?
    :type importAbc: bool
    :param replaceShaders: replace/overwrite existing shaders?
    :type replaceShaders: bool
    :param addShaderSuffix: add a shader suffix to the end of each shader and light to match the renderer?
    :type addShaderSuffix: bool
    :param importSubDInfo: import the subd settings which isn't contained in the alembic and auto apply after import
    :type importSubDInfo: bool?
    :param replaceRoots: replace the root/base hierarchy objects in maya, will delete and remake the root objects.
    :type replaceRoots: bool
    :return allNodes: all nodes built, not the network node
    :rtype: list
    :return networkNodeName:  the node network name created
    :rtype: str
    """
    allNodes = exportabcshaderlights.importAbcGenericShaderLights(filePathZooScene,
                                                                  rendererNiceName=rendererNiceName,
                                                                  importShaders=importShaders,
                                                                  importLights=importLights,
                                                                  importAbc=importAbc,
                                                                  replaceShaders=replaceShaders,
                                                                  addShaderSuffix=addShaderSuffix,
                                                                  importSubDInfo=importSubDInfo,
                                                                  replaceRoots=replaceRoots,
                                                                  returnNodes=True)
    networkNodeName = '_'.join([assetName, ASSETSUFFIX])
    # create network node and add the network node itself
    networkNodeName = nodes.createNetworkNodeWithConnections(networkNodeName, ASSETATTR, allNodes)
    allNodes.append(networkNodeName)
    return allNodes, networkNodeName


def importZooSceneAsAsset(filePathZooScene, rendererNiceName, replaceAssets=True, importAbc=True, importShaders=True,
                          importLights=False, replaceShaders=True, addShaderSuffix=True, importSubDInfo=True,
                          replaceRoots=True, turnStart=0, turnEnd=0, turnOffset=0, loopAbc=False, replaceByType=False,
                          scaleOffset=1.0, rotYOffset=0.0):
    """Imports a .zoo scene with checks and replace options, and auto group creation for zooAssets.


    :param filePathZooScene:  full path to the zooscene file
    :type filePathZooScene: str
    :param rendererNiceName: the renderer nice name "Arnold"
    :type rendererNiceName: str
    :param replaceAssets:
    :type replaceAssets:
    :param importShaders: import shaders into the scene?
    :type importShaders: bool
    :param importLights: import lights into the scene?
    :type importLights: bool
    :param importAbc: import alembic into the scene?
    :type importAbc: bool
    :param replaceShaders: replace/overwrite existing shaders?
    :type replaceShaders: bool
    :param addShaderSuffix: add a shader suffix to the end of each shader and light to match the renderer?
    :type addShaderSuffix: bool
    :param importSubDInfo: import the subd settings which isn't contained in the alembic and auto apply after import
    :type importSubDInfo: bool?
    :param replaceRoots: replace the root/base hierarchy objects in maya, will delete and remake the root objects.
    :type replaceRoots: bool
    :param turnStart: The start frame for a spinning animated turntable
    :type turnStart: int
    :param turnEnd: The end frame for a spinning animated turntable
    :type turnEnd: int
    :param turnOffset: The angle offset for the start of the turntable in degrees
    :type turnOffset: float
    :param replaceByType: deletes existing assets which match the type stored in the info file
    :type replaceByType: bool
    :param scaleOffset: the scale value of the asset package grp on x y and z
    :type scaleOffset: float
    :param rotYOffset: the rot y value of the asset package grp
    :type rotYOffset: float
    :return allNodes: all nodes built, including the network node
    :rtype: list
    """
    assetType = getAssetTypeFile(filePathZooScene)
    if replaceByType:
        assetNodesWithSameType = getAllAssetsInSceneOfType(assetType)
        if assetNodesWithSameType:
            deleteAssetNodeList(assetNodesWithSameType)
    elif replaceAssets:  # delete existing assets
        deleteZooAssets(onlyInAssetsGrp=False)
    fileName = os.path.basename(filePathZooScene)
    assetName = os.path.splitext(fileName)[0]
    # check if asset is already in scene by searching through the existing network asset nodes which record this info
    currentAssetNames = getAllAssetNamesInTheScene()
    if assetName in currentAssetNames:  # it already exists so find a unique name
        assetName = namehandling.uniqueNameFromList(assetName, currentAssetNames)
    assetGrpName = '_'.join([assetName, ASSETGRP])
    assetGrpLong = "|{}|{}".format(ZOOSCENEGRPNAME, assetGrpName)
    if not cmds.objExists(ZOOSCENEGRPNAME):  # create the assets grp
        cmds.group(em=True, name=ZOOSCENEGRPNAME)
    if not cmds.objExists(assetGrpLong):  # create the asset grp
        assetGrpNameNew = cmds.group(em=True, name=ZOOSCENEGRPNAME)
        assetGrpNameNew = cmds.parent(assetGrpNameNew, ZOOSCENEGRPNAME)
        if assetGrpNameNew != assetGrpName:
            assetGrpLong = cmds.rename(assetGrpNameNew, assetGrpName)
    allNodes, networkNodeName = importZooSceneNoParent(filePathZooScene, rendererNiceName, assetName,
                                                       importShaders=importShaders, importLights=importLights,
                                                       replaceShaders=replaceShaders, addShaderSuffix=addShaderSuffix,
                                                       importSubDInfo=importSubDInfo, replaceRoots=replaceRoots)
    # now get all root objects
    dagObjects = cmds.ls(allNodes, dag=True, long=True, shapes=False)
    rootObjects = objhandling.getTheWorldParentOfObjList(dagObjects)
    if rootObjects:  # rare case no root objects can occur, importing lights but they aren't checked as on
        cmds.parent(rootObjects, assetGrpLong)
    # tag networkNode as assetType
    tagAssetAsType(networkNodeName, assetType)
    # network connect the remaining root
    connections.createMessageConnection(networkNodeName, assetGrpLong, ASSETATTR)
    connections.createMessageConnection(networkNodeName, assetGrpLong, ASSETROOTATTR)
    cmds.select(deselect=True)
    assetGrp = cmds.listConnections('.'.join([networkNodeName, ASSETROOTATTR]))[0]
    if turnStart != turnEnd:
        assetGrp = cmds.listConnections('.'.join([networkNodeName, ASSETROOTATTR]))[0]
        keyframes.createTurntable(assetGrp, setTimerange=True, angleOffset=turnOffset)
    else:
        cmds.setAttr("{}.rotateY".format(assetGrp), rotYOffset)
    if loopAbc:
        alembicNodes = cmds.ls(allNodes, type="AlembicNode")
        if alembicNodes:  # should be just one node
            cmds.setAttr("{}.cycleType".format(alembicNodes[0]), 1)  # set the alembic node to "Loop"
        else:
            om2.MGlobal.displayWarning("No Alembic Node Found")
    cmds.setAttr("{}.scaleX".format(assetGrp), scaleOffset)
    cmds.setAttr("{}.scaleY".format(assetGrp), scaleOffset)
    cmds.setAttr("{}.scaleZ".format(assetGrp), scaleOffset)
    return allNodes


def getAssetRoots():
    """gets all the asset groups in a scene and return them as a long name list.

    :return assetRootList: a list of asset root objects, zooAsset_grp and *_asset_grp with long names
    :rtype assetRootList: list
    """
    assetRootList = list()
    if cmds.objExists(ZOOSCENEGRPNAME):
        assetRootList.append(ZOOSCENEGRPNAME)
    zooAssetNodeList = cmds.ls("*_{}".format(ASSETSUFFIX))
    if not zooAssetNodeList:
        return assetRootList
    for zooAssetNode in zooAssetNodeList:
        assetGrp = cmds.listConnections('.'.join([zooAssetNode, ASSETROOTATTR]))
        if assetGrp:  # could be empty
            assetRootList.append(assetGrp[0])
    assetRootList = namehandling.getLongNameList(assetRootList)
    return assetRootList


def removeAssetRootsFromAlembicRoots(alembicRoots):
    """*Probably should be a while loop but lazy
    Removes the asset nodes the organising groups from being exported automatically.
    The groups are the zooAssets grp and each asset grp
    Finds the asset nodes in the scene and if they are scene roots find legitimate children to export instead.

    :param alembicRoots: roots of the alembic export as specified by the user
    :type alembicRoots: list
    :return alembicRoots: roots of the alembic export actually exported ignoring asset folders
    :rtype alembicRoots: list
    """
    childrenList = list()
    grandChildrenList = list()
    removeRootList = list()
    legitNewRootList = list()
    assetRootList = getAssetRoots()
    for assetRoot in assetRootList:
        if assetRoot in alembicRoots:
            removeRootList.append(assetRoot)
            # return it's children
            children = cmds.listRelatives(assetRoot, children=True, shapes=False, fullPath=True)
            if children:
                childrenList = childrenList + children
    if childrenList:
        for child in childrenList:
            if child in assetRootList:
                removeRootList.append(child)
                grandChildren = cmds.listRelatives(child, children=True, shapes=False, fullPath=True)
                if grandChildren:
                    grandChildrenList = grandChildren + grandChildrenList
            else:
                legitNewRootList.append(child)
    legitNewRootList = legitNewRootList + grandChildrenList
    alembicRoots = legitNewRootList + alembicRoots
    # take asset root list from
    alembicRoots = [x for x in alembicRoots if x not in assetRootList]
    return alembicRoots


def saveAsset(fullFilePath, rendererNiceName, exportSelected=False, exportShaders=True,
              exportLights=True, exportAbc=True, noMayaDefaultCams=True,
              exportGeo=True, exportCams=True, exportAll=False, dataFormat="ogawa",
              frameRange="", visibility=True, creases=True, uvSets=True, exportSubD=True):
    """same as exportAbcGenericShaderLights only this function checks for asset node grps and tries to auto filter
    them out.
    """
    selectedObjs = cmds.ls(selection=True)
    if not exportSelected:
        # since this is an asset export we don't want to include asset grps
        # ignore these grps by selecting the appropriate nodes under the asset grps and export selected
        # roots, dodgy but will work for now
        alembicRoots = objhandling.getAllTansformsInWorld()
        rootsNoAssetGrps = removeAssetRootsFromAlembicRoots(alembicRoots)
        mayaStartupCams = cameras.getStartupCamTransforms()
        rootsNoAssetGrps = [x for x in rootsNoAssetGrps if x not in mayaStartupCams]  # remove default cams
        cmds.select(rootsNoAssetGrps, replace=True)
    exportSelected = True
    zooSceneFullPath, filePathAlembic = exportabcshaderlights.exportAbcGenericShaderLights(fullFilePath,
                                                                                           rendererNiceName=rendererNiceName,
                                                                                           exportSelected=exportSelected,
                                                                                           exportShaders=exportShaders,
                                                                                           exportLights=exportLights,
                                                                                           exportAbc=exportAbc,
                                                                                           noMayaDefaultCams=noMayaDefaultCams,
                                                                                           exportGeo=exportGeo,
                                                                                           exportCams=exportCams,
                                                                                           exportAll=exportAll,
                                                                                           dataFormat=dataFormat,
                                                                                           frameRange=frameRange,
                                                                                           visibility=visibility,
                                                                                           creases=creases,
                                                                                           uvSets=uvSets,
                                                                                           exportSubD=exportSubD)
    cmds.select(selectedObjs, replace=True)
    return zooSceneFullPath, filePathAlembic


def getAssetPresetDict(filename=ASSETFILEPATHPRESETS):
    """Retrieves the .zooScene preset dictionary from the .json file
    The preset dictionary only contains the file paths of the .zooScene assets

    :param filename: the name of the assetsPreset.json file
    :type filename: str
    :return presetAssetFilePathDict: The asset preset dictionary, contains mostly the file path info of files
    :rtype presetAssetFilePathDict: dict
    """
    jsonShaderFilePath = os.path.join(os.path.dirname(__file__), filename)
    with open(jsonShaderFilePath) as data_file:
        presetAssetFilePathDict = json.load(data_file)
    return presetAssetFilePathDict


def writeAssetPresetDict(presetAssetFilePathDict):
    """Writes the selected asset to a zooScene .zooScene file and also Alembic .abc

    :param presetAssetFilePathDict: The incoming .json dictionary with file path info, directories etc
    :type presetAssetFilePathDict: dict
    """
    jsonFilePath = os.path.join(os.path.dirname(__file__), ASSETFILEPATHPRESETS)
    with open(jsonFilePath, 'w') as outfile:
        json.dump(presetAssetFilePathDict, outfile, sort_keys=True, indent=4, ensure_ascii=False)


def listFileQuickDir():
    """Lists all the json files inside of the "fileQuickDir"

    :return fileList: List of the assets inside of the assetQuickDir
    :rtype fileList: list
    :return fileQuickDir: The file path of the asset directory
    :rtype fileQuickDir: str
    """
    presetLightDict = getAssetPresetDict()
    fileList = list()
    if not presetLightDict[FILEQUICKDIRKEY]:
        return fileList, presetLightDict[FILEQUICKDIRKEY]  # emptyList
    if not os.path.isdir(presetLightDict[FILEQUICKDIRKEY]):  # check if directory actually exists
        return fileList, ""
    os.chdir(presetLightDict[FILEQUICKDIRKEY])
    for ext in PRESETSUFFIX:  # find presets in directory
        for file in glob.glob("*.{}".format(ext)):
            fileList.append(file)
    return fileList, presetLightDict[FILEQUICKDIRKEY]


def deleteQuickDirZooScene(filePath):
    """Deletes a zooscene file

    :return filesFullPathDeleted: a list of the files deleted full file path
    :rtype filesFullPathDeleted: list
    """
    return zooscenefiles.deleteZooSceneFiles(filePath)
